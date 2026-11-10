"""Bounded, in-memory provenance records. No extraction or authorization is performed."""

from __future__ import annotations

import hashlib
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError, model_validator

from .schema import fingerprint
from .source_admission import Revision, Source


class ProvenanceError(ValueError):
    """Input-free failure at the public binding boundary."""


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, hide_input_in_errors=True)
    schema_version: Literal[1]

    @model_validator(mode="before")
    @classmethod
    def validate_version(cls, value):
        if not isinstance(value, dict) or type(value.get("schema_version")) is not int:
            raise ValueError("invalid version")
        return value


class Scope(Record):
    document_id: str = Field(min_length=1, max_length=256)
    revision_id: str = Field(min_length=1, max_length=71)
    corpus: str = Field(min_length=1, max_length=256)
    version: str | None
    labels: tuple[str, ...] = Field(max_length=64)
    processing_approved: Literal[True]
    redistribution_rights: Literal["allowed", "prohibited", "unknown"]


class Dependency(Record):
    revision_id: str = Field(min_length=1, max_length=71)
    extraction_id: str = Field(min_length=1, max_length=71)
    # Caller-supplied description of extraction inputs; never execution evidence.
    definition: str = Field(min_length=1, max_length=4096)


class Block(Record):
    block_id: str = Field(min_length=1, max_length=256)
    revision_id: str = Field(min_length=1, max_length=71)
    extraction_id: str = Field(min_length=1, max_length=71)
    order: StrictInt = Field(ge=0, le=1000000)
    kind: Literal["text", "heading", "list", "code", "table_header", "table_row", "visual"]
    anchor: str = Field(min_length=1, max_length=512)
    text: str = Field(max_length=200000)
    text_sha256: str
    origin: Literal["native", "visual_transcription"]
    page_ref: str | None = Field(default=None, min_length=1, max_length=512)
    crop_ref: str | None = Field(default=None, min_length=1, max_length=512)
    uncertainty: str | None = Field(default=None, min_length=1, max_length=1024)
    geometry: tuple[float, float, float, float] | None = None


class SourceFragment(Record):
    kind: Literal["source"]
    block_id: str = Field(min_length=1, max_length=256)
    start: StrictInt = Field(ge=0)
    end: StrictInt = Field(ge=0)
    copied_text: str = Field(min_length=1, max_length=200000)


class Separator(Record):
    kind: Literal["separator"]
    text: str = Field(min_length=1, max_length=4096)


class TokenCount(Record):
    availability: Literal["available", "unavailable"]
    count: StrictInt | None = Field(ge=0, le=10000000)
    provenance: str = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def consistency(self):
        if (self.availability == "available") != (self.count is not None):
            raise ValueError("inconsistent count")
        return self


class Chunk(Record):
    chunk_id: str = Field(min_length=1, max_length=71)
    revision_id: str = Field(min_length=1, max_length=71)
    extraction_id: str = Field(min_length=1, max_length=71)
    policy_id: str = Field(min_length=1, max_length=71)
    fragments: tuple[SourceFragment | Separator, ...] = Field(min_length=1, max_length=256)
    text: str = Field(min_length=1, max_length=200000)
    text_sha256: str
    heading_path: tuple[str, ...] = Field(default=(), max_length=64)
    counts: tuple[TokenCount, ...] = Field(default=(), max_length=16)


class Derived(Record):
    artifact_id: str = Field(min_length=1, max_length=256)
    origin: Literal["interpretation", "context"]
    target_revision: str = Field(min_length=1, max_length=71)
    support_blocks: tuple[str, ...] = Field(min_length=1, max_length=256)
    text: str = Field(min_length=1, max_length=200000)
    page_ref: str | None = Field(default=None, min_length=1, max_length=512)
    crop_ref: str | None = Field(default=None, min_length=1, max_length=512)
    uncertainty: str | None = Field(default=None, min_length=1, max_length=1024)


class Grants(Record):
    corpora: tuple[str, ...] = Field(max_length=128)
    versions: tuple[str, ...] = Field(max_length=128)
    labels: tuple[str, ...] = Field(max_length=128)


class Restrictions(Record):
    corpora: tuple[str, ...] | None = Field(default=None, max_length=128)
    versions: tuple[str, ...] | None = Field(default=None, max_length=128)


def _snapshot(obj, cls):
    if type(obj) is not cls:
        raise ValueError
    # model_dump recurses into nested DTOs, including copies with bypassed validators.
    return cls.model_validate(obj.model_dump(warnings=False))


def _hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extraction_id(definition: str) -> str:
    if type(definition) is not str or not 1 <= len(definition) <= 4096:
        raise ProvenanceError("invalid dependency")
    return fingerprint({"version": 1, "kind": "extraction", "definition": definition})


def policy_id(definition: str) -> str:
    if type(definition) is not str or not 1 <= len(definition) <= 4096:
        raise ProvenanceError("invalid policy")
    return fingerprint({"version": 1, "kind": "chunk-policy", "definition": definition})


def chunk_id(chunk: Chunk) -> str:
    try:
        data = _snapshot(chunk, Chunk).model_dump(exclude={"chunk_id"})
        return fingerprint({"version": 1, "kind": "chunk", "record": data})
    except (ValueError, TypeError, AttributeError, ValidationError, UnicodeError):
        raise ProvenanceError("invalid chunk") from None


def catalog(revisions: tuple[Revision, ...]) -> tuple[Scope, ...]:
    try:
        if type(revisions) is not tuple or not 1 <= len(revisions) <= 128:
            raise ValueError
        scopes = []
        seen = set()
        for item in revisions:
            if type(item) is not Revision or type(item.source) is not Source:
                raise ValueError
            # Explicit field snapshots prevent model_copy/model_construct trust.
            source = Source.model_validate(
                {n: getattr(item.source, n) for n in Source.model_fields}
            )
            rev = Revision.model_validate(
                {
                    "schema_version": item.schema_version,
                    "revision_id": item.revision_id,
                    "source": source.model_dump(),
                    "blob": item.blob,
                }
            )
            expected = fingerprint(
                {"version": 1, "kind": "source-revision", "source": source.model_dump()}
            )
            if (
                rev.revision_id != expected
                or rev.blob != source.sha256
                or not source.processing_approved
                or rev.revision_id in seen
            ):
                raise ValueError
            seen.add(rev.revision_id)
            scopes.append(
                Scope(
                    schema_version=1,
                    document_id=source.logical_id,
                    revision_id=rev.revision_id,
                    corpus=source.corpus,
                    version=source.version,
                    labels=source.access_labels,
                    processing_approved=True,
                    redistribution_rights=source.redistribution_rights,
                )
            )
        return tuple(scopes)
    except (ValueError, TypeError, AttributeError, ValidationError, UnicodeError):
        raise ProvenanceError("invalid revision catalog") from None


class Registry:
    """Validate a complete immutable snapshot of dependencies and original blocks."""

    def __init__(
        self,
        revisions: tuple[Revision, ...],
        dependencies: tuple[Dependency, ...],
        blocks: tuple[Block, ...],
    ):
        try:
            scopes = catalog(revisions)
            if (
                type(dependencies) is not tuple
                or len(dependencies) > 128
                or type(blocks) is not tuple
                or len(blocks) > 4096
            ):
                raise ValueError
            self._scopes = {s.revision_id: s for s in scopes}
            self._dependencies = {}
            for raw in dependencies:
                dep = _snapshot(raw, Dependency)
                key = (dep.revision_id, dep.extraction_id)
                if (
                    dep.revision_id not in self._scopes
                    or dep.extraction_id != extraction_id(dep.definition)
                    or key in self._dependencies
                ):
                    raise ValueError
                self._dependencies[key] = dep
            self._blocks = {}
            orders = set()
            for raw in blocks:
                block = _snapshot(raw, Block)
                key = (block.revision_id, block.extraction_id)
                order = (*key, block.order)
                if (
                    key not in self._dependencies
                    or block.block_id in self._blocks
                    or order in orders
                    or _hash(block.text) != block.text_sha256
                ):
                    raise ValueError
                if block.origin == "visual_transcription" and (
                    not block.page_ref or not block.uncertainty
                ):
                    raise ValueError
                if block.geometry is not None:
                    import math

                    x1, y1, x2, y2 = block.geometry
                    if not all(math.isfinite(x) for x in block.geometry) or x1 > x2 or y1 > y2:
                        raise ValueError
                self._blocks[block.block_id] = block
                orders.add(order)
        except (
            ValueError,
            TypeError,
            AttributeError,
            ValidationError,
            UnicodeError,
            ProvenanceError,
        ):
            raise ProvenanceError("invalid provenance registry") from None

    def bind_chunk(self, raw: Chunk) -> Scope:
        try:
            chunk = _snapshot(raw, Chunk)
            if (
                chunk.revision_id,
                chunk.extraction_id,
            ) not in self._dependencies or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", chunk.policy_id
            ):
                raise ValueError
            parts = []
            source_count = 0
            for fragment in chunk.fragments:
                if isinstance(fragment, Separator):
                    parts.append(fragment.text)
                else:
                    block = self._blocks[fragment.block_id]
                    if (
                        (block.revision_id, block.extraction_id)
                        != (chunk.revision_id, chunk.extraction_id)
                        or not fragment.start < fragment.end <= len(block.text)
                        or block.text[fragment.start : fragment.end] != fragment.copied_text
                    ):
                        raise ValueError
                    parts.append(fragment.copied_text)
                    source_count += 1
            if (
                not source_count
                or "".join(parts) != chunk.text
                or _hash(chunk.text) != chunk.text_sha256
                or chunk.chunk_id != chunk_id(chunk)
            ):
                raise ValueError
            return self._scopes[chunk.revision_id]
        except (
            ValueError,
            TypeError,
            AttributeError,
            KeyError,
            ValidationError,
            UnicodeError,
            ProvenanceError,
        ):
            raise ProvenanceError("invalid chunk binding") from None

    def bind_derived(self, raw: Derived) -> Scope:
        try:
            derived = _snapshot(raw, Derived)
            target = self._scopes[derived.target_revision]
            if derived.origin == "interpretation" and (
                not derived.page_ref or not derived.uncertainty
            ):
                raise ValueError
            labels = set(target.labels)
            for block_id in derived.support_blocks:
                block = self._blocks[block_id]
                scope = self._scopes[block.revision_id]
                labels.update(scope.labels)
                if (
                    scope.revision_id != target.revision_id
                    or scope.document_id != target.document_id
                    or scope.corpus != target.corpus
                    or scope.labels != target.labels
                ):
                    raise ValueError
            return target.model_copy(update={"labels": tuple(sorted(labels))})
        except (ValueError, TypeError, AttributeError, KeyError, ValidationError):
            raise ProvenanceError("invalid derived binding") from None


def reader_allows(
    scope: Scope, grants: Grants | None, restrictions: Restrictions | None = None
) -> bool:
    try:
        scope = _snapshot(scope, Scope)
        if grants is None:
            return False
        grants = _snapshot(grants, Grants)
        restrictions = _snapshot(restrictions, Restrictions) if restrictions is not None else None
        return (
            scope.corpus in grants.corpora
            and scope.version is not None
            and scope.version in grants.versions
            and set(scope.labels) <= set(grants.labels)
            and (
                restrictions is None
                or restrictions.corpora is None
                or scope.corpus in restrictions.corpora
            )
            and (
                restrictions is None
                or restrictions.versions is None
                or scope.version in restrictions.versions
            )
        )
    except (ValueError, TypeError, AttributeError, ValidationError):
        raise ProvenanceError("invalid reader scope") from None
