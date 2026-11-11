"""Explicit operator-selected, declaration-only native ingestion profile."""

from dataclasses import dataclass, fields
import os
from pathlib import Path
import re
import stat
import time

from . import bundle_native_records as bounded
from . import chunking, native_tokenizers as native
from .pdf_extraction import PdfRuntime

MAX_BYTES = 65536
MAX_SECONDS = 5


class ProfileError(ValueError):
    """Fixed, input-free refusal of a complete profile."""


@dataclass(frozen=True)
class Profile:
    native_runtime: native.Runtime
    bge_body: native.Definition
    bge_representation: native.Definition
    reranker_pair: native.Definition
    pdf_runtime: PdfRuntime | None
    chunk_policy: chunking.Policy


def _check(deadline):
    if time.monotonic() >= deadline:
        raise ValueError


def _fields(value, names):
    if type(value) is not dict or set(value) != set(names):
        raise ValueError


def _string(value, maximum):
    if type(value) is not str or not 1 <= len(value) <= maximum or '\0' in value:
        raise ValueError
    value.encode('utf-8')
    return value


def _path(value):
    value = _string(value, 4096)
    if not value.startswith('/'):
        raise ValueError
    return Path(value)


def _definition(record, role):
    _fields(record, ('artifact', 'sha256', 'backend_version', 'model_revision', 'preprocessing'))
    artifact = _path(record['artifact'])
    digest = record['sha256']
    if (type(digest) is not str or re.fullmatch(r'[0-9a-f]{64}', digest) is None
            or record['backend_version'] != '0.21.4'):
        raise ValueError
    return native.Definition(artifact, digest, '0.21.4', role,
                             _string(record['model_revision'], 256),
                             _string(record['preprocessing'], 256))


def _parse(raw, deadline):
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError
    _check(deadline)
    value = bounded._parse(raw, 10000)
    _check(deadline)
    _fields(value, ('schema_version', 'native_runtime', 'bge', 'reranker', 'pdf_runtime',
                    'chunk_policy'))
    if type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ValueError
    runtime = value['native_runtime']
    _fields(runtime, ('root', 'packages', 'python'))
    if runtime['python'] not in ('python3.12', 'python3.14'):
        raise ValueError
    runtime = native.Runtime(_path(runtime['root']), _path(runtime['packages']), runtime['python'])
    body = _definition(value['bge'], 'bge_body')
    representation = _definition(value['bge'], 'bge_representation')
    pair = _definition(value['reranker'], 'reranker_pair')
    pdf = value['pdf_runtime']
    if pdf is not None:
        _fields(pdf, ('runtime_dir', 'packages_dir'))
        pdf = PdfRuntime(_path(pdf['runtime_dir']), _path(pdf['packages_dir']))
    policy = value['chunk_policy']
    _fields(policy, (f.name for f in fields(chunking.Policy)))
    policy = chunking.Policy(**policy)
    result = Profile(runtime, body, representation, pair, pdf, policy)
    _check(deadline)
    return result


def parse_profile(raw: bytes) -> Profile:
    """Parse immutable JSON bytes without filesystem access or runtime execution."""
    try:
        return _parse(raw, time.monotonic() + MAX_SECONDS)
    except Exception:
        raise ProfileError('ingestion profile refused') from None


def load_profile(path) -> Profile:
    """Read only the explicitly selected regular profile file, then parse it."""
    try:
        deadline = time.monotonic() + MAX_SECONDS
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            _check(deadline)
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= MAX_BYTES:
                raise ValueError
            raw = bytearray()
            while len(raw) <= MAX_BYTES:
                _check(deadline)
                part = os.read(fd, min(65536, MAX_BYTES + 1 - len(raw)))
                if not part:
                    break
                raw.extend(part)
            after = os.fstat(fd)
            def identity(s):
                return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

            if (len(raw) > MAX_BYTES or len(raw) != before.st_size
                    or identity(before) != identity(after)):
                raise ValueError
            _check(deadline)
            result = _parse(bytes(raw), deadline)
        finally:
            os.close(fd)
        _check(deadline)
        return result
    except Exception:
        raise ProfileError('ingestion profile refused') from None
