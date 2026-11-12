"""Owned, isolated sessions producing exact native embedding tokenizer IDs."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import selectors
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from . import native_tokenizers as native


@dataclass(frozen=True)
class Policy:
    max_artifact_bytes: int = 32_000_000
    max_request_bytes: int = 200_000
    max_chars: int = 100_000
    max_response_bytes: int = 16_384
    max_ids: int = 1024
    max_calls: int = 1024
    max_input_bytes: int = 32_000_000
    max_output_bytes: int = 16_000_000
    lifetime_seconds: float = 300
    startup_seconds: float = 5
    request_seconds: float = 2

    def __post_init__(self):
        for value, maximum in ((self.max_artifact_bytes, 32_000_000),
                               (self.max_request_bytes, 200_000), (self.max_chars, 100_000),
                               (self.max_response_bytes, 16_384), (self.max_ids, 1024),
                               (self.max_calls, 1024), (self.max_input_bytes, 32_000_000),
                               (self.max_output_bytes, 16_000_000)):
            if type(value) is not int or not 1 <= value <= maximum:
                raise native.TokenizerError('invalid tokenizer policy')
        for value, maximum in ((self.lifetime_seconds, 300), (self.startup_seconds, 5),
                               (self.request_seconds, 2)):
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or not 0 < value <= maximum):
                raise native.TokenizerError('invalid tokenizer policy')


@dataclass(frozen=True)
class TokenIDReceipt:
    ids: tuple[int, ...]
    count: int
    artifact_sha256: str
    backend_version: str
    role: str
    model_revision: str
    preprocessing: str
    input_sha256: str
    nonce: str
    serialization: str = 'utf8-json-v1;no-truncation;no-padding;special-tokens'


class TokenIDSession:
    """Own a fixed native worker and its private artifact for a bounded lifetime."""

    def __init__(self, definition, runtime, policy=None):
        self._child = None
        self._tmp = None
        self._buffer = bytearray()
        self._calls = self._input = self._output = 0
        started = time.monotonic()
        try:
            if policy is not None and type(policy) is not Policy:
                raise ValueError
            self._policy = Policy() if policy is None else Policy(**policy.__dict__)
            self._deadline = started + self._policy.lifetime_seconds
            d = definition
            if (type(d) is not native.Definition or type(runtime) is not native.Runtime
                    or type(d.sha256) is not str or not re.fullmatch('[0-9a-f]{64}', d.sha256)
                    or d.backend_version != '0.21.4' or type(d.backend_version) is not str
                    or d.role != 'bge_representation' or type(d.role) is not str
                    or type(d.model_revision) is not str
                    or not re.fullmatch('[0-9a-f]{40}', d.model_revision)
                    or type(d.preprocessing) is not str or d.preprocessing != 'identity'):
                raise ValueError
            self._definition = d
            raw = native._read_artifact(d.artifact, self._policy.max_artifact_bytes)
            if hashlib.sha256(raw).hexdigest() != d.sha256:
                raise ValueError
            self._tmp = tempfile.TemporaryDirectory(prefix='embedding-tokenizer-')
            artifact = Path(self._tmp.name) / 'artifact.json'
            artifact.write_bytes(raw)
            del raw
            argv = native._argv(runtime, artifact, artifact)
            i = argv.index('--ro-bind', argv.index('/artifact.json') + 1)
            del argv[i:i + 3]
            i = argv.index('/worker.py')
            argv[i - 1] = str(Path(__file__).with_name('embedding_tokenizer_worker.py')
                              .resolve(strict=True))
            argv[1:3] = ['--as=1073741824', '--cpu=30']
            argv = ['/usr/bin/timeout', '--signal=KILL',
                    str(self._policy.lifetime_seconds) + 's'] + argv
            argv.append('/artifact.json')
            self._child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.DEVNULL, close_fds=True)
            os.set_blocking(self._child.stdin.fileno(), False)
            os.set_blocking(self._child.stdout.fileno(), False)
            startup_deadline = min(self._deadline, started + self._policy.startup_seconds)
            if (self._parse(self._read(startup_deadline)) != {'ready': '0.21.4'}
                    or time.monotonic() >= startup_deadline):
                raise ValueError
        except BaseException as error:
            self._refuse(error)

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
                    if rest or len(line) > self._policy.max_response_bytes:
                        raise ValueError
                    return bytes(line)
                if len(self._buffer) > self._policy.max_response_bytes:
                    raise ValueError
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not sel.select(remaining):
                    raise ValueError
                data = os.read(self._child.stdout.fileno(),
                               self._policy.max_response_bytes + 1 - len(self._buffer))
                if not data:
                    raise ValueError
                self._buffer.extend(data)
                self._output += len(data)
                if self._output > self._policy.max_output_bytes:
                    raise ValueError

    def encode(self, text):
        try:
            if (self._child is None or self._child.poll() is not None or type(text) is not str
                    or len(text) > self._policy.max_chars):
                raise ValueError
            text.encode('utf-8', 'strict')
            inputs = json.dumps([text, None], ensure_ascii=True, separators=(',', ':')).encode()
            digest = hashlib.sha256(inputs).hexdigest()
            nonce = uuid.uuid4().hex
            wire = json.dumps({'text': text, 'nonce': nonce}, ensure_ascii=True,
                              separators=(',', ':')).encode() + b'\n'
            self._calls += 1
            self._input += len(wire)
            if (len(wire) > self._policy.max_request_bytes or self._calls > self._policy.max_calls
                    or self._input > self._policy.max_input_bytes):
                raise ValueError
            deadline = min(self._deadline, time.monotonic() + self._policy.request_seconds)
            with selectors.DefaultSelector() as sel:
                sel.register(self._child.stdin, selectors.EVENT_WRITE)
                sent = 0
                while sent < len(wire):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not sel.select(remaining):
                        raise ValueError
                    sent += os.write(self._child.stdin.fileno(), wire[sent:])
            result = self._parse(self._read(deadline))
            with selectors.DefaultSelector() as sel:
                sel.register(self._child.stdout, selectors.EVENT_READ)
                if sel.select(0):
                    raise ValueError
            if (type(result) is not dict or set(result) !=
                    {'nonce', 'count', 'ids', 'digest', 'version'}
                    or result['nonce'] != nonce or result['digest'] != digest
                    or result['version'] != '0.21.4' or type(result['ids']) is not list
                    or type(result['count']) is not int or result['count'] != len(result['ids'])
                    or not 2 <= result['count'] <= self._policy.max_ids
                    or any(type(x) is not int or not 0 <= x <= 2**31 - 1 for x in result['ids'])
                    or time.monotonic() >= deadline):
                raise ValueError
            d = self._definition
            return TokenIDReceipt(tuple(result['ids']), result['count'], d.sha256,
                                  d.backend_version, d.role, d.model_revision, d.preprocessing,
                                  digest, nonce)
        except BaseException as error:
            self._refuse(error)

    def _refuse(self, error):
        cleanup_error = None
        try:
            self.close()
        except BaseException as caught:
            cleanup_error = caught
            error.add_note('tokenizer cleanup pending or interrupted')
        pending = self._child is not None or self._tmp is not None
        if not isinstance(error, Exception):
            if pending:
                error.cleanup_owner = self
            raise error
        if cleanup_error is not None and not isinstance(cleanup_error, Exception):
            if pending:
                cleanup_error.cleanup_owner = self
            raise cleanup_error
        refused = native.TokenizerError('tokenizer session refused')
        if pending:
            refused.owner = self
        raise refused from None

    def close(self):
        child = self._child
        first = None

        def remember(error):
            nonlocal first
            if first is None or (isinstance(first, Exception) and
                                 not isinstance(error, Exception)):
                first = error

        def attempt(fn):
            nonlocal first
            try:
                return fn()
            except ProcessLookupError:
                return None
            except BaseException as error:
                remember(error)
                return None

        if child is not None:
            if child.stdin is not None:
                attempt(child.stdin.close)
            # Keep the exact handle until wait confirms the child was reaped.
            attempt(child.terminate)
            reaped = False
            try:
                child.wait(timeout=0.4)
                reaped = True
            except BaseException as error:
                if not isinstance(error, subprocess.TimeoutExpired):
                    remember(error)
                attempt(child.kill)
                try:
                    child.wait(timeout=0.4)
                    reaped = True
                except BaseException as later:
                    remember(later)
            if child.stdout is not None:
                attempt(child.stdout.close)
            if reaped and first is None:
                self._child = None
        if self._child is None and self._tmp is not None:
            tmp = self._tmp
            try:
                tmp.cleanup()
                self._tmp = None
            except BaseException as error:
                remember(error)
        if first is not None:
            raise first

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
