"""Private immutable content container; metadata semantics are deliberately opaque."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import stat
import time
import threading
from functools import wraps
from dataclasses import dataclass
from types import MappingProxyType

MAX_METADATA = 262144
MAX_MANIFEST = 524288
MAX_MEMBER = 64 * 1024 * 1024
MAX_TOTAL = 96 * 1024 * 1024
HEX = re.compile(r"[0-9a-f]{64}\Z")
NAME = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
FORMAT = "slaif-derived-container-v1"


class StoreError(ValueError):
    """Input-free failure of admission, integrity, or storage."""


@dataclass(frozen=True)
class Member:
    name: str
    data: bytes


@dataclass(frozen=True)
class Snapshot:
    manifest: bytes
    metadata: object
    members: tuple[Member, ...]


def _pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError
        result[k] = v
    return result


def _parse(data):
    obj = json.loads(
        data.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )
    stack = [(obj, 0)]
    nodes = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > 20000 or depth > 32:
            raise ValueError
        if type(value) is str:
            value.encode("utf-8")
        elif type(value) is int:
            if value.bit_length() > 430:
                raise ValueError
        elif type(value) is float:
            if not math.isfinite(value):
                raise ValueError
        elif type(value) is list:
            if nodes + len(stack) + len(value) > 20000:
                raise ValueError
            stack.extend((v, depth + 1) for v in value)
        elif type(value) is dict:
            if nodes + len(stack) + 2 * len(value) > 20000:
                raise ValueError
            stack.extend((v, depth + 1) for v in value.values())
            stack.extend((k, depth + 1) for k in value)
        elif value is not None and type(value) is not bool:
            raise ValueError
    return obj


def _encode(obj):
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _freeze(value):
    if type(value) is dict:
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if type(value) is list:
        return tuple(_freeze(v) for v in value)
    return value


def _changed(a, b):
    return any(
        getattr(a, x) != getattr(b, x)
        for x in ("st_dev", "st_ino", "st_mode", "st_uid", "st_size", "st_mtime_ns", "st_ctime_ns")
    )


def _secure(st, directory=False):
    return (
        st.st_uid == os.geteuid()
        and stat.S_IMODE(st.st_mode) == (0o700 if directory else 0o600)
        and (stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode))
    )


def _open_operation(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        with self._lock:
            if self._closed:
                raise StoreError("store unavailable")
            return method(self, *args, **kwargs)

    return guarded


class Store:
    def __init__(self, root):
        self._fds = []
        self._lock = threading.RLock()
        self._closed = True
        try:
            fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            self._fds.append(fd)
            if not _secure(os.fstat(fd), True):
                raise ValueError
            for name in ("derived", "v1"):
                fd = self._directory(fd, name)
            self._objects = self._directory(fd, "objects")
            self._manifests = self._directory(fd, "manifests")
            self._closed = False
        except (OSError, ValueError, TypeError):
            self.close()
            raise StoreError("store unavailable") from None

    def _directory(self, parent, name):
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
            os.fsync(parent)
        except FileExistsError:
            pass
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        self._fds.append(fd)
        if not _secure(os.fstat(fd), True):
            raise ValueError
        return fd

    def close(self):
        with self._lock:
            self._closed = True
            while self._fds:
                os.close(self._fds.pop())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @staticmethod
    def _deadline(end):
        if time.monotonic() > end:
            raise ValueError

    def _hash(self, data, end):
        digest = hashlib.sha256()
        view = memoryview(data)
        for offset in range(0, len(view), 65536):
            self._deadline(end)
            digest.update(view[offset : offset + 65536])
        self._deadline(end)
        return digest.hexdigest()

    def _read(self, directory, name, limit, end):
        # A competing publisher's stage unlink changes the final inode's ctime.
        # Discard any changed attempt completely; only a fresh, stable and secure
        # descriptor may supply bytes to the caller's size and digest checks.
        for _ in range(4):
            self._deadline(end)
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            try:
                before = os.fstat(fd)
                if not _secure(before) or before.st_size > limit:
                    raise ValueError
                chunks = []
                count = 0
                while True:
                    self._deadline(end)
                    chunk = os.read(fd, min(65536, limit + 1 - count))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    count += len(chunk)
                    if count > limit:
                        raise ValueError
                if count != before.st_size:
                    raise ValueError
                if not _changed(before, os.fstat(fd)):
                    return b"".join(chunks)
            finally:
                os.close(fd)
        raise ValueError

    def _put(self, directory, digest, data, end):
        stage = ".stage-" + secrets.token_hex(16)
        fd = os.open(
            stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
        )
        try:
            try:
                if not _secure(os.fstat(fd)):
                    raise ValueError
                view = memoryview(data)
                while view:
                    self._deadline(end)
                    count = os.write(fd, view[:65536])
                    if not count:
                        raise ValueError
                    view = view[count:]
                os.fsync(fd)
            finally:
                os.close(fd)
            self._deadline(end)
            try:
                os.link(
                    stage, digest, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False
                )
            except FileExistsError:
                existing = self._read(directory, digest, len(data), end)
                if len(existing) != len(data) or self._hash(existing, end) != digest:
                    raise ValueError
            os.fsync(directory)
        finally:
            os.unlink(stage, dir_fd=directory)
            os.fsync(directory)

    @_open_operation
    def publish(self, metadata_json_bytes, members):
        end = time.monotonic() + 30
        try:
            if type(metadata_json_bytes) is not bytes or len(metadata_json_bytes) > MAX_METADATA:
                raise ValueError
            if type(members) is not tuple or len(members) > 16:
                raise ValueError
            total = 0
            names = set()
            for member in members:
                if (
                    type(member) is not Member
                    or type(member.name) is not str
                    or type(member.data) is not bytes
                ):
                    raise ValueError
                if (
                    not NAME.fullmatch(member.name)
                    or member.name in names
                    or len(member.data) > MAX_MEMBER
                ):
                    raise ValueError
                names.add(member.name)
                total += len(member.data)
            if total > MAX_TOTAL:
                raise ValueError
            metadata = _parse(metadata_json_bytes)
            if type(metadata) is not dict or len(_encode(metadata)) > MAX_METADATA:
                raise ValueError
            records = []
            for member in members:
                self._deadline(end)
                digest = self._hash(member.data, end)
                records.append({"name": member.name, "sha256": digest, "bytes": len(member.data)})
            manifest = _encode({"format": FORMAT, "metadata": metadata, "members": records})
            if len(manifest) > MAX_MANIFEST:
                raise ValueError
            _parse(manifest)
            for member, record in zip(members, records, strict=True):
                self._put(self._objects, record["sha256"], member.data, end)
            digest = self._hash(manifest, end)
            self._put(self._manifests, digest, manifest, end)
            self._deadline(end)
            return digest
        except (
            OSError,
            ValueError,
            TypeError,
            AttributeError,
            UnicodeError,
            RecursionError,
            OverflowError,
        ):
            raise StoreError("publication failed") from None

    @_open_operation
    def load(self, container_id):
        end = time.monotonic() + 30
        try:
            if type(container_id) is not str or not HEX.fullmatch(container_id):
                raise ValueError
            raw = self._read(self._manifests, container_id, MAX_MANIFEST, end)
            if self._hash(raw, end) != container_id:
                raise ValueError
            obj = _parse(raw)
            if (
                type(obj) is not dict
                or set(obj) != {"format", "metadata", "members"}
                or obj["format"] != FORMAT
                or type(obj["metadata"]) is not dict
                or type(obj["members"]) is not list
                or len(obj["members"]) > 16
                or len(_encode(obj["metadata"])) > MAX_METADATA
                or _encode(obj) != raw
            ):
                raise ValueError
            total = 0
            names = set()
            for record in obj["members"]:
                if type(record) is not dict or set(record) != {"name", "sha256", "bytes"}:
                    raise ValueError
                name, digest, size = record["name"], record["sha256"], record["bytes"]
                if (
                    type(name) is not str
                    or not NAME.fullmatch(name)
                    or name in names
                    or type(digest) is not str
                    or not HEX.fullmatch(digest)
                    or type(size) is not int
                    or not 0 <= size <= MAX_MEMBER
                ):
                    raise ValueError
                names.add(name)
                total += size
            if total > MAX_TOTAL:
                raise ValueError
            members = []
            for record in obj["members"]:
                data = self._read(self._objects, record["sha256"], record["bytes"], end)
                if len(data) != record["bytes"] or self._hash(data, end) != record["sha256"]:
                    raise ValueError
                members.append(Member(record["name"], data))
            snapshot = Snapshot(raw, _freeze(obj["metadata"]), tuple(members))
            self._deadline(end)
            return snapshot
        except (
            OSError,
            ValueError,
            TypeError,
            AttributeError,
            UnicodeError,
            RecursionError,
            OverflowError,
        ):
            raise StoreError("invalid container") from None
