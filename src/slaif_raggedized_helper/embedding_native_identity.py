"""Bounded selected-file identity; this is not a runtime execution receipt."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from pathlib import Path

from . import embedding_tokenizer, native_tokenizers

DOMAIN = b'slaif-bge-native-runtime-identity-v1\n'
SCOPE = ('binds selected Python executable, complete selected tokenizers package/distribution '
         'file bytes, fixed native policy and these application source files; excludes Python '
         'stdlib, system libraries, launch binaries, actual ABI/loading/runtime execution, '
         'publisher/authenticity, current authorization and model/hardware/security/license '
         'qualification.')
DIST = 'tokenizers-0.21.4.dist-info'
SOURCES = ('embedding_native_identity.py', 'native_tokenizers.py', 'embedding_tokenizer.py',
           'embedding_tokenizer_worker.py')
MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_PYTHON = 128 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}\Z')
_uncertain = ContextVar('native_identity_uncertain', default=None)
_uncertain_closes = 0


class IdentityRefused(ValueError):
    """A content-free identity refusal."""


@dataclass(frozen=True)
class NativeRuntimeIdentity:
    record_bytes: bytes
    fingerprint: str


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'),
                      allow_nan=False).encode('ascii')


def _fingerprint(raw):
    return 'sha256:' + hashlib.sha256(DOMAIN + raw).hexdigest()


def _path(value):
    if type(value) not in (str, Path) and not isinstance(value, Path):
        raise ValueError
    s = str(value)
    if (not s.startswith('/') or len(os.fsencode(s)) > 4096 or s != os.path.normpath(s)
            or s == '/' or '\x00' in s):
        raise ValueError
    return s


def _relative(path):
    if type(path) is not str or not 1 <= len(path) <= 512 or not path.isascii():
        raise ValueError
    parts = path.split('/')
    if (len(parts) > 9 or any(not p or p in ('.', '..') for p in parts)
            or any(ord(c) < 32 or ord(c) == 127 or c == '\\' for c in path)):
        raise ValueError
    return parts


def _sha(value):
    if type(value) is not str or not HEX.fullmatch(value):
        raise ValueError


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError


def _keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError


def _policy():
    return asdict(embedding_tokenizer.Policy())


def _validate(raw):
    if type(raw) is not bytes or len(raw) > 131072:
        raise ValueError

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    obj = json.loads(raw.decode('ascii'), object_pairs_hook=unique,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    if _canonical(obj) != raw:
        raise ValueError
    _keys(obj, ('schema', 'contract', 'python', 'package', 'policy', 'sources',
                'runtime_integrity_scope', 'qualification'))
    if (type(obj['schema']) is not int or obj['schema'] != 1
            or obj['contract'] != 'bge-native-tokenizer-runtime-v1'
            or obj['runtime_integrity_scope'] != SCOPE or obj['qualification'] != 'unknown'):
        raise ValueError
    python = obj['python']
    _keys(python, ('name', 'bytes', 'sha256'))
    if python['name'] != 'python3.12':
        raise ValueError
    _integer(python['bytes'], 1, MAX_PYTHON)
    _sha(python['sha256'])
    package = obj['package']
    _keys(package, ('name', 'version', 'files', 'fingerprint'))
    if package['name'] != 'tokenizers' or package['version'] != '0.21.4':
        raise ValueError
    files = package['files']
    if type(files) is not list or not 1 <= len(files) <= 512:
        raise ValueError
    paths = []
    total = 0
    for item in files:
        _keys(item, ('path', 'bytes', 'sha256'))
        parts = _relative(item['path'])
        if len(parts) < 2 or parts[0] not in ('tokenizers', DIST):
            raise ValueError
        paths.append(item['path'])
        _integer(item['bytes'], 0, MAX_FILE)
        total += item['bytes']
        _sha(item['sha256'])
    if (paths != sorted(set(paths)) or total > MAX_TOTAL
            or not {'tokenizers/__init__.py', DIST + '/METADATA'} <= set(paths)
            or package['fingerprint'] != hashlib.sha256(_canonical(files)).hexdigest()):
        raise ValueError
    policy = obj['policy']
    expected = _policy()
    _keys(policy, expected)
    if any(type(policy[k]) is not type(v) or policy[k] != v for k, v in expected.items()):
        raise ValueError
    embedding_tokenizer.Policy(**policy)
    _keys(obj['sources'], SOURCES)
    for digest in obj['sources'].values():
        _sha(digest)
    return _fingerprint(raw)


def validate_record(raw):
    """Validate a persisted declaration without filesystem or process access."""
    try:
        return _validate(raw)
    except Exception:
        raise IdentityRefused('native runtime identity refused') from None


def _signature(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_size,
            st.st_mtime_ns, st.st_ctime_ns)


def _close(fd):
    pending = sys.exception()
    try:
        os.close(fd)
    except BaseException as cleanup:
        global _uncertain_closes
        _uncertain_closes += 1
        state = _uncertain.get()
        if state is not None:
            state[0] = True
        selected = pending
        if pending is None or (isinstance(pending, Exception)
                               and not isinstance(cleanup, Exception)):
            selected = cleanup
        try:
            selected.add_note('native identity descriptor cleanup uncertain')
        except BaseException:
            pass
        if selected is cleanup:
            raise


def _directory(path):
    """Open each lexical component without following links."""
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in _path(path).split('/')[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=fd)
            old, fd = fd, child
            _close(old)
        return fd
    except BaseException:
        _close(fd)
        raise


def _read(dirfd, name, limit, executable=False):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                 dir_fd=dirfd)
    try:
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or before.st_size > limit or (executable and not before.st_mode & 0o111)):
            raise ValueError
        digest = hashlib.sha256()
        data = bytearray() if name == 'METADATA' else None
        size = 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise ValueError
            digest.update(chunk)
            if data is not None:
                data.extend(chunk)
        if size != before.st_size or _signature(before) != _signature(os.fstat(fd)):
            raise ValueError
        if _signature(before) != _signature(os.stat(name, dir_fd=dirfd, follow_symlinks=False)):
            raise ValueError
        return (size, digest.hexdigest(), bytes(data) if data is not None else None,
                _signature(before))
    finally:
        _close(fd)


def _names(fd, counter):
    names = []
    with os.scandir(fd) as entries:
        for entry in entries:
            names.append(entry.name)
            counter[0] += 1
            if len(names) > 512 or counter[0] > 1024:
                raise ValueError
    return sorted(names)


def _scan(packages):
    counter = [0]
    files = []
    seen = set()
    metadata = None
    witness = []
    total = 0

    def walk(fd, prefix, depth):
        nonlocal metadata, total
        before = _signature(os.fstat(fd))
        witness.append((prefix, before))
        inode = before[:2]
        if inode in seen:
            raise ValueError
        seen.add(inode)
        names = _names(fd, counter)
        for name in names:
            path = prefix + '/' + name
            _relative(path)
            st = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISDIR(st.st_mode):
                if depth >= 8:
                    raise ValueError
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                                dir_fd=fd)
                try:
                    if _signature(st) != _signature(os.fstat(child)):
                        raise ValueError
                    walk(child, path, depth + 1)
                    if _signature(st) != _signature(os.stat(name, dir_fd=fd,
                                                             follow_symlinks=False)):
                        raise ValueError
                finally:
                    _close(child)
            else:
                size, digest, raw, signature = _read(fd, name, MAX_FILE)
                if signature != _signature(st):
                    raise ValueError
                witness.append((path, signature))
                total += size
                files.append({'path': path, 'bytes': size, 'sha256': digest})
                if len(files) > 512 or total > MAX_TOTAL:
                    raise ValueError
                if path == DIST + '/METADATA':
                    metadata = raw
        if before != _signature(os.fstat(fd)):
            raise ValueError

    before = _signature(os.fstat(packages))
    names = _names(packages, counter)
    if set(names) not in ({'tokenizers', DIST}, {'tokenizers', DIST, '.lock'}):
        raise ValueError
    if '.lock' in names:
        size, _, _, signature = _read(packages, '.lock', 0)
        witness.append(('.lock', signature))
        if size:
            raise ValueError
    for name in ('tokenizers', DIST):
        child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                        dir_fd=packages)
        try:
            st = _signature(os.fstat(child))
            walk(child, name, 1)
            if st != _signature(os.stat(name, dir_fd=packages, follow_symlinks=False)):
                raise ValueError
        finally:
            _close(child)
    if before != _signature(os.fstat(packages)):
        raise ValueError
    if metadata is None:
        raise ValueError
    headers = []
    for line in metadata.splitlines():
        if not line:
            break
        if line.lower().startswith((b'name:', b'version:')):
            headers.append(line.split(b':', 1))
    names = [v.strip() for k, v in headers if k.lower() == b'name']
    versions = [v.strip() for k, v in headers if k.lower() == b'version']
    if (len(names) != 1 or re.sub(rb'[-_]+', b'-', names[0].lower()) != b'tokenizers'
            or versions != [b'0.21.4']):
        raise ValueError
    return sorted(files, key=lambda x: x['path']), witness


def _sources():
    fd = _directory(Path(__file__).absolute().parent)
    try:
        return {name: _read(fd, name, 1024 * 1024) for name in SOURCES}
    finally:
        _close(fd)


def predict(runtime):
    """Inspect selected files and return a detached declaration, not execution authority."""
    state = [False]
    token = _uncertain.set(state)
    try:
        if type(runtime) is not native_tokenizers.Runtime or runtime.python != 'python3.12':
            raise ValueError
        root = _directory(runtime.root)
        try:
            binary = os.open('bin', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                             dir_fd=root)
            try:
                packages = _directory(runtime.packages)
                try:
                    python_file = _read(binary, 'python3.12', MAX_PYTHON, True)
                    size, digest = python_file[:2]
                    files, witness = _scan(packages)
                    sources = _sources()
                    root_check = _directory(runtime.root)
                    try:
                        packages_check = _directory(runtime.packages)
                        try:
                            if (_signature(os.fstat(root_check)) != _signature(os.fstat(root))
                                    or _signature(os.fstat(packages_check)) !=
                                    _signature(os.fstat(packages))
                                    or _signature(os.stat('bin', dir_fd=root,
                                                          follow_symlinks=False)) !=
                                    _signature(os.fstat(binary))):
                                raise ValueError
                        finally:
                            _close(packages_check)
                    finally:
                        _close(root_check)
                    if (python_file != _read(binary, 'python3.12', MAX_PYTHON, True)
                            or (files, witness) != _scan(packages) or sources != _sources()):
                        raise ValueError
                finally:
                    _close(packages)
            finally:
                _close(binary)
        finally:
            _close(root)
        if state[0]:
            raise ValueError
        record = {'schema': 1, 'contract': 'bge-native-tokenizer-runtime-v1',
                  'python': {'name': 'python3.12', 'bytes': size, 'sha256': digest},
                  'package': {'name': 'tokenizers', 'version': '0.21.4', 'files': files,
                              'fingerprint': hashlib.sha256(_canonical(files)).hexdigest()},
                  'policy': _policy(), 'sources': {k: v[1] for k, v in sources.items()},
                  'runtime_integrity_scope': SCOPE,
                  'qualification': 'unknown'}
        raw = _canonical(record)
        return NativeRuntimeIdentity(raw, _validate(raw))
    except Exception:
        refusal = IdentityRefused('native runtime identity refused')
        if state[0]:
            try:
                refusal.add_note('native identity descriptor cleanup uncertain')
            except BaseException:
                pass
        raise refusal from None
    finally:
        _uncertain.reset(token)
