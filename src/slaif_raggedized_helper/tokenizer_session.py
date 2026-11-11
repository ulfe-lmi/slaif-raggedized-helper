"""Explicit bounded sessions for isolated native tokenizer counts."""
from __future__ import annotations

import hashlib
import json
import os
import re
import selectors
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from . import native_tokenizers as native


class Session:
    """Own one isolated worker; definitions and inputs are explicit and bounded."""

    def __init__(self, definitions, runtime):
        self._child = None
        self._tmp = None
        self._buffer = bytearray()
        self._calls = self._input = self._output = 0
        started = time.monotonic()
        self._deadline = started + 20
        try:
            if type(definitions) not in (list, tuple) or not 1 <= len(definitions) <= 3:
                raise ValueError
            if type(runtime) is not native.Runtime:
                raise ValueError
            self._definitions = {}
            artifacts = {}
            for d in definitions:
                if (type(d) is not native.Definition or d.role in self._definitions or
                        d.role not in ('bge_body', 'bge_representation', 'reranker_pair') or
                        d.backend_version != '0.21.4' or type(d.sha256) is not str or
                        not re.fullmatch('[0-9a-f]{64}', d.sha256) or
                        any(type(x) is not str or not 1 <= len(x) <= 256
                            for x in (d.model_revision, d.preprocessing))):
                    raise ValueError
                raw = native._read_artifact(d.artifact, 32_000_000)
                if hashlib.sha256(raw).hexdigest() != d.sha256:
                    raise ValueError
                if d.sha256 not in artifacts:
                    artifacts[d.sha256] = raw
                self._definitions[d.role] = d
            if len(artifacts) > 2:
                raise ValueError
            self._indices = {digest: i for i, digest in enumerate(artifacts)}
            self._tmp = tempfile.TemporaryDirectory(prefix='tokenizer-session-')
            paths = []
            for i, raw in enumerate(artifacts.values()):
                path = Path(self._tmp.name) / f'{i}.json'
                path.write_bytes(raw)
                paths.append(path)
            del artifacts, raw
            argv = native._argv(runtime, paths[0], paths[0])
            # Preserve the accepted runtime validation and isolation mounts, replacing
            # only the fixed worker and per-session artifact mounts.
            worker = Path(__file__).with_name('tokenizer_session_worker.py').resolve(strict=True)
            i = argv.index('--ro-bind', argv.index('/artifact.json') + 1)
            del argv[i:i + 3]  # request mount
            i = argv.index('/worker.py')
            argv[i - 1] = str(worker)
            end = argv.index('--ro-bind', argv.index('/worker.py') + 1)
            for index, path in enumerate(paths[1:], 1):
                argv[end:end] = ['--ro-bind', str(path), f'/artifact{index}.json']
                end += 3
            argv[1:3] = ['--as=1073741824', '--cpu=10']
            argv = ['/usr/bin/timeout', '--signal=KILL', '20s'] + argv
            argv.extend(['/artifact.json'] + [f'/artifact{i}.json'
                                              for i in range(1, len(paths))])
            self._child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.DEVNULL, close_fds=True)
            os.set_blocking(self._child.stdin.fileno(), False)
            os.set_blocking(self._child.stdout.fileno(), False)
            ready = self._read(min(self._deadline, started + 5))
            if self._parse(ready) != {'ready': '0.21.4'}:
                raise ValueError
        except BaseException as error:
            self.close()
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise native.TokenizerError('tokenizer session refused') from None

    @staticmethod
    def _parse(data):
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError
                result[key] = value
            return result
        return json.loads(data.decode('utf-8', 'strict'), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))

    def _read(self, deadline):
        with selectors.DefaultSelector() as sel:
            sel.register(self._child.stdout, selectors.EVENT_READ)
            while True:
                if b'\n' in self._buffer:
                    line, _, rest = self._buffer.partition(b'\n')
                    self._buffer = bytearray(rest)
                    if rest or len(line) > 4096:
                        raise ValueError
                    return bytes(line)
                if len(self._buffer) > 4096 or time.monotonic() >= deadline:
                    raise ValueError
                if not sel.select(deadline - time.monotonic()):
                    raise ValueError
                data = os.read(self._child.stdout.fileno(), 4097 - len(self._buffer))
                if not data:
                    raise ValueError
                self._buffer.extend(data)
                self._output += len(data)
                if self._output > 4_000_000:
                    raise ValueError

    def count(self, role, text, pair=None):
        try:
            if (self._child is None or self._child.poll() is not None or
                    type(role) is not str or role not in self._definitions or
                    type(text) is not str or (pair is not None and type(pair) is not str) or
                    (role == 'reranker_pair') != (pair is not None) or
                    len(text) + (len(pair) if pair is not None else 0) > 100_000):
                raise ValueError
            inputs = json.dumps([text, pair], ensure_ascii=True, separators=(',', ':')).encode()
            digest = hashlib.sha256(inputs).hexdigest()
            d = self._definitions[role]
            request = {'text': text, 'pair': pair, 'nonce': uuid.uuid4().hex, 'role': role,
                       'artifact': self._indices[d.sha256]}
            wire = json.dumps(request, ensure_ascii=True, separators=(',', ':')).encode() + b'\n'
            self._calls += 1
            self._input += len(wire)
            if len(wire) > 200_000 or self._calls > 8192 or self._input > 16_000_000:
                raise ValueError
            deadline = min(self._deadline, time.monotonic() + 2)
            with selectors.DefaultSelector() as sel:
                sel.register(self._child.stdin, selectors.EVENT_WRITE)
                sent = 0
                while sent < len(wire):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not sel.select(remaining):
                        raise ValueError
                    sent += os.write(self._child.stdin.fileno(), wire[sent:])
            result = self._parse(self._read(deadline))
            if (type(result) is not dict or set(result) !=
                    {'nonce', 'role', 'artifact', 'count', 'digest', 'version'} or
                    result['nonce'] != request['nonce'] or result['role'] != role or
                    type(result['artifact']) is not int or
                    result['artifact'] != request['artifact'] or
                    result['digest'] != digest or result['version'] != '0.21.4' or
                    type(result['count']) is not int or not 0 <= result['count'] <= 200_000 or
                    time.monotonic() >= deadline):
                raise ValueError
            return native.Count(result['count'], d.sha256, d.backend_version, role,
                                d.model_revision, d.preprocessing, digest,
                                'pair' if pair is not None else 'single')
        except BaseException as error:
            self.close()
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise native.TokenizerError('tokenizer session refused') from None

    def close(self):
        child, self._child = self._child, None
        if child is not None:
            if child.stdin:
                child.stdin.close()
            if child.poll() is None:
                try:
                    child.terminate()
                except ProcessLookupError:
                    pass
                try:
                    child.wait(timeout=0.4)
                except subprocess.TimeoutExpired:
                    try:
                        child.kill()
                    except ProcessLookupError:
                        pass
                    child.wait(timeout=0.4)
            if child.stdout:
                child.stdout.close()
        if self._tmp is not None:
            self._tmp.cleanup()
            self._tmp = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
