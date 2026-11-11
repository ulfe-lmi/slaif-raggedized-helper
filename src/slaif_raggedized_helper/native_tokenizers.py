"""Explicit, isolated native tokenizer counts; model equivalence is unqualified."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import selectors
import stat
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


class TokenizerError(ValueError):
    """Input-free refusal; never includes source content or filesystem paths."""


class TokenizerPrerequisiteError(TokenizerError):
    """The explicitly configured isolation or backend is unavailable."""


@dataclass(frozen=True)
class Runtime:
    root: Path
    packages: Path
    python: str = 'python3.14'


@dataclass(frozen=True)
class Policy:
    max_artifact_bytes: int = 32_000_000
    max_request_bytes: int = 200_000
    max_chars: int = 100_000
    max_count: int = 200_000
    max_output: int = 4096
    wall_seconds: float = 5.0

    def __post_init__(self):
        for value, maximum in ((self.max_artifact_bytes, 32_000_000),
                               (self.max_request_bytes, 200_000), (self.max_chars, 100_000),
                               (self.max_count, 200_000), (self.max_output, 4096)):
            if type(value) is not int or not 1 <= value <= maximum:
                raise TokenizerError('invalid policy')
        if (type(self.wall_seconds) not in (int, float) or not math.isfinite(self.wall_seconds)
                or not 0 < self.wall_seconds <= 5):
            raise TokenizerError('invalid policy')


@dataclass(frozen=True)
class Definition:
    artifact: Path
    sha256: str
    backend_version: str
    role: str
    model_revision: str
    preprocessing: str


@dataclass(frozen=True)
class Count:
    count: int
    artifact_sha256: str
    backend_version: str
    role: str
    model_revision: str
    preprocessing: str
    input_sha256: str
    mode: str
    serialization: str = 'utf8-json-v1;no-truncation;no-padding;special-tokens'


def _read_artifact(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError
        raw = bytearray()
        while len(raw) <= limit:
            part = os.read(fd, min(65536, limit + 1 - len(raw)))
            if not part:
                break
            raw.extend(part)
        after = os.fstat(fd)
        if (len(raw) > limit or len(raw) != before.st_size or
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
                 before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size,
                                         after.st_mtime_ns, after.st_ctime_ns)):
            raise ValueError
        return bytes(raw)
    finally:
        os.close(fd)


def _run(argv, cap, deadline):
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, close_fds=True)
    except OSError:
        raise TokenizerPrerequisiteError('tokenizer isolation unavailable') from None
    selector = None
    try:
        selector = selectors.DefaultSelector()
        assert child.stdout is not None
        selector.register(child.stdout, selectors.EVENT_READ)
        data = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not selector.select(remaining):
                raise TokenizerError('tokenizer worker timeout')
            part = os.read(child.stdout.fileno(), min(65536, cap + 1 - len(data)))
            if not part:
                break
            data.extend(part)
            if len(data) > cap:
                raise TokenizerError('tokenizer output limit')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TokenizerError('tokenizer worker timeout')
        try:
            code = child.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            raise TokenizerError('tokenizer worker timeout') from None
        if code:
            raise TokenizerError('tokenizer worker refused')
        return bytes(data)
    finally:
        if selector is not None:
            selector.close()
        if child.stdout is not None:
            child.stdout.close()
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
                child.wait(timeout=0.5)


def _argv(runtime, artifact, request):
    try:
        root = Path(runtime.root).resolve(strict=True)
        packages = Path(runtime.packages).resolve(strict=True)
        worker = Path(__file__).with_name('tokenizer_worker.py').resolve(strict=True)
        if (not re.fullmatch(r'python3\.(12|14)', runtime.python)
                or not (root / 'bin' / runtime.python).is_file()
                or not (packages / 'tokenizers' / '__init__.py').is_file()
                or not Path('/usr/bin/bwrap').is_file() or not Path('/usr/bin/prlimit').is_file()):
            raise ValueError
        return ['/usr/bin/prlimit', '--as=536870912', '--cpu=3', '--nofile=32', '--fsize=4096',
                '/usr/bin/bwrap', '--unshare-user', '--unshare-pid', '--unshare-net',
                '--unshare-ipc', '--unshare-uts', '--die-with-parent', '--new-session',
                '--clearenv', '--setenv', 'PYTHONPATH', '/packages', '--setenv',
                'PYTHONDONTWRITEBYTECODE', '1', '--setenv', 'TOKENIZERS_PARALLELISM', 'false',
                '--setenv', 'HOME', '/tmp', '--ro-bind', str(root), '/runtime', '--ro-bind',
                str(packages), '/packages', '--ro-bind', str(artifact), '/artifact.json',
                '--ro-bind', str(request), '/request.json', '--ro-bind', str(worker), '/worker.py',
                '--ro-bind', '/usr/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu',
                '--ro-bind', '/usr/lib64', '/usr/lib64', '--symlink', 'usr/lib', '/lib',
                '--symlink', 'usr/lib64', '/lib64', '--proc', '/proc', '--dev', '/dev',
                '--tmpfs', '/tmp', '--chdir', '/tmp', '/runtime/bin/' + runtime.python,
                '/worker.py']
    except (OSError, TypeError, ValueError):
        raise TokenizerPrerequisiteError('tokenizer isolation unavailable') from None


def count(definition: Definition, runtime: Runtime, text: str, pair: str | None = None,
          policy: Policy | None = None) -> Count:
    """Count exact already-preprocessed strings. Pair is mandatory for reranker role."""
    try:
        if type(definition) is not Definition or type(runtime) is not Runtime:
            raise ValueError
        if policy is not None and type(policy) is not Policy:
            raise ValueError
        policy = Policy() if policy is None else Policy(**policy.__dict__)
        if (type(definition.sha256) is not str or
                not re.fullmatch(r'[0-9a-f]{64}', definition.sha256) or
                definition.backend_version != '0.21.4' or
                definition.role not in ('bge_body', 'bge_representation', 'reranker_pair') or
                any(type(x) is not str or not 1 <= len(x) <= 256 for x in
                    (definition.model_revision, definition.preprocessing)) or
                type(text) is not str or (pair is not None and type(pair) is not str) or
                (definition.role == 'reranker_pair') != (pair is not None)):
            raise ValueError
        deadline = time.monotonic() + policy.wall_seconds
        raw = _read_artifact(definition.artifact, policy.max_artifact_bytes)
        digest = hashlib.sha256(raw).hexdigest()
        if digest != definition.sha256:
            raise ValueError
        if len(text) + (len(pair) if pair is not None else 0) > policy.max_chars:
            raise ValueError
        inputs = json.dumps([text, pair], ensure_ascii=True, separators=(',', ':')).encode('utf-8')
        if len(inputs) > policy.max_request_bytes:
            raise ValueError
        input_digest = hashlib.sha256(inputs).hexdigest()
        nonce = uuid.uuid4().hex
        request = json.dumps({'text': text, 'pair': pair, 'nonce': nonce,
                              'version': definition.backend_version}, ensure_ascii=True,
                             separators=(',', ':')).encode('utf-8')
        if len(request) > policy.max_request_bytes:
            raise ValueError
        with tempfile.TemporaryDirectory(prefix='tokenizer-worker-') as directory:
            artifact = Path(directory) / 'artifact.json'
            req = Path(directory) / 'request.json'
            artifact.write_bytes(raw)
            req.write_bytes(request)
            output = _run(_argv(runtime, artifact, req), policy.max_output, deadline)
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError
                result[key] = value
            return result
        obj = json.loads(output.decode('utf-8', errors='strict'), object_pairs_hook=unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if (type(obj) is not dict or set(obj) != {'nonce', 'count', 'version'} or
                obj['nonce'] != nonce or obj['version'] != definition.backend_version or
                type(obj['count']) is not int or not 0 <= obj['count'] <= policy.max_count or
                time.monotonic() >= deadline):
            raise ValueError
        return Count(obj['count'], digest, definition.backend_version, definition.role,
                     definition.model_revision, definition.preprocessing, input_digest,
                     'pair' if pair is not None else 'single')
    except TokenizerError:
        raise
    except Exception:
        raise TokenizerError('tokenizer count refused') from None
