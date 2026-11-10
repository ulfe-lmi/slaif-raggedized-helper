"""Bounded local original admission; see docs/parallel/source-admission-api.md."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Callable, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    ValidationError,
    field_validator,
)

from .schema import fingerprint

MAX_MANIFEST = 256_000
MAX_ENTRIES = 128
MAX_ORIGINAL = 64 * 1024 * 1024
MAX_RECORD = 16_384
HEX = re.compile(r"^[0-9a-f]{64}$")


class AdmissionError(ValueError):
    """A deliberately input-free admission failure."""


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Source(StrictRecord):
    logical_id: str = Field(min_length=1, max_length=256)
    relative_path: str = Field(min_length=1, max_length=1024)
    display_uri: str = Field(min_length=1, max_length=1024)
    corpus: str = Field(min_length=1, max_length=256)
    access_labels: tuple[str, ...] = Field(max_length=64)
    processing_approved: StrictBool
    redistribution_rights: Literal["allowed", "prohibited", "unknown"]
    media_type: Literal["text/plain", "text/markdown", "application/pdf"]
    size: StrictInt = Field(ge=0, le=MAX_ORIGINAL)
    sha256: str
    title: str | None = Field(default=None, max_length=256)
    language: str | None = Field(default=None, max_length=64)
    product: str | None = Field(default=None, max_length=256)
    version: str | None = Field(default=None, max_length=256)
    date: str | None = Field(default=None, max_length=64)
    authority: str | None = Field(default=None, max_length=256)

    @field_validator("sha256")
    @classmethod
    def digest_valid(cls, value: str) -> str:
        if not HEX.fullmatch(value):
            raise ValueError("invalid digest")
        return value

    @field_validator("relative_path")
    @classmethod
    def path_valid(cls, value: str) -> str:
        if (
            value.startswith("/")
            or any(x in ("", ".", "..") for x in value.split("/"))
            or "\x00" in value
        ):
            raise ValueError("invalid relative path")
        return value

    @field_validator("access_labels", mode="before")
    @classmethod
    def labels_tuple(cls, value: object) -> object:
        return tuple(value) if type(value) is list else value

    @field_validator("access_labels")
    @classmethod
    def labels_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not label or len(label) > 256 for label in value) or len(set(value)) != len(value):
            raise ValueError("invalid labels")
        return tuple(sorted(value))


class Manifest(StrictRecord):
    @field_validator("schema_version", mode="before", check_fields=False)
    @classmethod
    def version_is_integer(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("invalid schema version")
        return value

    schema_version: Literal[1]
    sources: list[Source] = Field(min_length=1, max_length=MAX_ENTRIES)


class Revision(StrictRecord):
    @field_validator("schema_version", mode="before", check_fields=False)
    @classmethod
    def version_is_integer(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("invalid schema version")
        return value

    schema_version: Literal[1]
    revision_id: str
    source: Source
    blob: str


def parse_manifest(data: bytes) -> Manifest:
    try:
        if len(data) > MAX_MANIFEST:
            raise ValueError
        if type(data) is not bytes:
            raise ValueError
        obj = json.loads(
            data.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_invalid_constant
        )
        _valid_unicode(obj)
        return Manifest.model_validate(obj)
    except (ValueError, TypeError, ValidationError, UnicodeError, RecursionError):
        raise AdmissionError("invalid manifest") from None


def _invalid_constant(value: str) -> None:
    raise ValueError("invalid JSON number")


def _valid_unicode(value: object) -> None:
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            item.encode("utf-8")
        elif isinstance(item, dict):
            stack.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _identity(source: Source) -> str:
    return fingerprint({"version": 1, "kind": "source-revision", "source": source.model_dump()})


def _open_source(
    root_fd: int, path: str, hook: Callable[[str], None]
) -> tuple[int, list[int], list[tuple[int, str, int]]]:
    # Independently enforce the boundary even if a caller bypasses model validation.
    try:
        Source.path_valid(path)
    except (ValueError, AttributeError, TypeError):
        raise AdmissionError("invalid source") from None
    dirs = [os.dup(root_fd)]
    links: list[tuple[int, str, int]] = []
    try:
        parts = path.split("/")
        for part in parts[:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dirs[-1])
            links.append((dirs[-1], part, fd))
            dirs.append(fd)
            hook("directory_opened")
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dirs[-1])
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise AdmissionError("source unavailable")
        return fd, dirs, links
    except BaseException:
        for fd in dirs:
            os.close(fd)
        raise


def _check_links(links: list[tuple[int, str, int]]) -> None:
    for parent, name, fd in links:
        actual = os.stat(name, dir_fd=parent, follow_symlinks=False)
        opened = os.fstat(fd)
        if not stat.S_ISDIR(actual.st_mode) or (actual.st_dev, actual.st_ino) != (
            opened.st_dev,
            opened.st_ino,
        ):
            raise AdmissionError("source changed")


def _changed(before: os.stat_result, after: os.stat_result) -> bool:
    # Reading may update atime; identity, mode, size and nanosecond change times matter.
    return any(
        getattr(before, field) != getattr(after, field)
        for field in ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
    )


class OriginalStore:
    """A store in a private, operator-controlled local POSIX directory."""

    def __init__(self, root: Path, *, fault: Callable[[str], None] | None = None):
        self.root = Path(root)
        self.fault = fault or (lambda _: None)
        self._fd = -1
        try:
            self.root.mkdir(mode=0o700, parents=False, exist_ok=True)
            self._fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            for name in ("blobs", "revisions"):
                try:
                    os.mkdir(name, 0o700, dir_fd=self._fd)
                    os.fsync(self._fd)
                except FileExistsError:
                    pass
                fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self._fd)
                os.close(fd)
        except OSError:
            if self._fd >= 0:
                os.close(self._fd)
            raise AdmissionError("store unavailable") from None

    def close(self) -> None:
        os.close(self._fd)

    def _dir(self, name: str) -> int:
        return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self._fd)

    def _read(self, directory: str, name: str, limit: int) -> bytes:
        d = self._dir(directory)
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=d)
            try:
                st = os.fstat(fd)
                if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
                    raise AdmissionError("invalid stored object")
                result = bytearray()
                while len(result) <= limit:
                    chunk = os.read(fd, min(65536, limit + 1 - len(result)))
                    if not chunk:
                        break
                    result.extend(chunk)
                if len(result) > limit or len(result) != st.st_size or _changed(st, os.fstat(fd)):
                    raise AdmissionError("invalid stored object")
                return bytes(result)
            finally:
                os.close(fd)
        finally:
            os.close(d)

    def _publish(self, directory: str, name: str, data: bytes) -> None:
        d = self._dir(directory)
        temp = None
        try:
            # The root is private; random staging names are never source-controlled.
            fd, temp_path = tempfile.mkstemp(prefix=".stage-", dir=self.root / directory)
            temp = os.path.basename(temp_path)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                self.fault("before_" + directory + "_publish")
                try:
                    os.link(temp, name, src_dir_fd=d, dst_dir_fd=d, follow_symlinks=False)
                    os.fsync(d)
                except FileExistsError:
                    if self._read(directory, name, len(data)) != data:
                        raise AdmissionError("immutable object conflict")
            finally:
                if temp is not None:
                    os.unlink(temp, dir_fd=d)
                    os.fsync(d)
        finally:
            os.close(d)

    def admit(self, approved_root: Path, source: Source) -> Revision:
        try:
            # Pydantic model_copy/model_construct can bypass validators. Bind a fresh,
            # validated primitive snapshot before opening even the approved root.
            if type(source) is not Source:
                raise AdmissionError("invalid source")
            source = Source.model_validate(
                {name: getattr(source, name) for name in Source.model_fields}
            )
            if not source.processing_approved:
                raise AdmissionError("processing not approved")
            root = os.open(approved_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                fd, dirs, links = _open_source(root, source.relative_path, self.fault)
                try:
                    before = os.fstat(fd)
                    if before.st_size != source.size:
                        raise AdmissionError("source size mismatch")
                    data = bytearray()
                    while len(data) <= source.size:
                        self.fault("before_read")
                        chunk = os.read(fd, min(65536, source.size + 1 - len(data)))
                        if not chunk:
                            break
                        data.extend(chunk)
                    _check_links(links)
                    after = os.fstat(fd)
                    if (
                        _changed(before, after)
                        or len(data) != source.size
                        or hashlib.sha256(data).hexdigest() != source.sha256
                    ):
                        raise AdmissionError("source changed or digest mismatch")
                finally:
                    os.close(fd)
                    for directory in dirs:
                        os.close(directory)
            finally:
                os.close(root)
            revision = Revision(
                schema_version=1, revision_id=_identity(source), source=source, blob=source.sha256
            )
            self._publish("blobs", source.sha256, bytes(data))
            self.fault("after_blob_publish")
            encoded = json.dumps(
                revision.model_dump(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
            ).encode()
            if len(encoded) > MAX_RECORD:
                raise AdmissionError("record too large")
            self._publish("revisions", revision.revision_id.removeprefix("sha256:"), encoded)
            return self.inspect(revision.revision_id)
        except AdmissionError:
            raise
        except (OSError, ValueError, TypeError, AttributeError, ValidationError):
            raise AdmissionError("admission failed") from None

    def inspect(self, revision_id: str) -> Revision:
        return self._verified_original(revision_id)[0]

    def read_original(self, revision_id: str) -> bytes:
        """Return bytes verified against the controlled revision and blob descriptors."""
        return self._verified_original(revision_id)[1]

    def read_verified(self, revision_id: str, *, max_bytes: int) -> tuple[Revision, bytes]:
        """Read a revision and its verified bytes within a caller-selected cap."""
        if type(max_bytes) is not int or not 0 <= max_bytes <= MAX_ORIGINAL:
            raise AdmissionError("invalid read limit")
        return self._verified_original(revision_id, max_bytes=max_bytes)

    def _verified_original(
        self, revision_id: str, *, max_bytes: int = MAX_ORIGINAL
    ) -> tuple[Revision, bytes]:
        try:
            if not revision_id.startswith("sha256:") or not HEX.fullmatch(revision_id[7:]):
                raise ValueError
            raw = self._read("revisions", revision_id[7:], MAX_RECORD)
            record = Revision.model_validate(json.loads(raw, object_pairs_hook=_unique))
            if (
                record.revision_id != revision_id
                or _identity(record.source) != revision_id
                or record.blob != record.source.sha256
            ):
                raise ValueError
            if record.source.size > max_bytes:
                raise ValueError
            blob = self._read("blobs", record.blob, max_bytes)
            if len(blob) != record.source.size or hashlib.sha256(blob).hexdigest() != record.blob:
                raise ValueError
            return record, blob
        except (
            OSError,
            ValueError,
            TypeError,
            AttributeError,
            ValidationError,
            UnicodeError,
            RecursionError,
        ):
            raise AdmissionError("invalid stored revision") from None
