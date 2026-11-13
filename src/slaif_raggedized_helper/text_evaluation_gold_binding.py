"""Private structured-text original-source gold binding; not a qualification."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
import time

from . import derived_store, ingestion_store, text_evaluation_dataset
from .source_admission import OriginalStore


class GoldBindingError(ValueError):
    """Content-free refusal."""


@dataclass(frozen=True, repr=False)
class BundleObservation:
    bundle_id: str
    metadata_sha256: str
    revision_id: str
    extraction_id: str
    block_count: int
    member_bytes: int


@dataclass(frozen=True, repr=False)
class GoldBinding:
    revision_id: str
    extraction_id: str
    block_id: str
    start: int
    end: int
    text_sha256: str
    bundle_ids: tuple


@dataclass(frozen=True, repr=False)
class BoundGold:
    dataset_id: str
    split_id: str
    dataset_sha256: str
    binding_id: str
    observations: tuple
    bindings: tuple
    case_count: int
    gold_atom_occurrences: int
    distinct_atom_count: int
    source_binding_status: str
    qualification: str = field(default="NOT_QUALIFIED", init=False)
    authorship_status: str = field(default="DECLARED_UNVERIFIED", init=False)
    rights_status: str = field(default="DECLARED_UNVERIFIED", init=False)
    split_status: str = field(default="STRUCTURAL_ONLY", init=False)


def _binding_id(obj, check):
    digest = hashlib.sha256(b"slaif-text-evaluation-gold-binding-v1\n")
    size = 0
    for part in json.JSONEncoder(sort_keys=True, ensure_ascii=True, separators=(",", ":"),
                                 allow_nan=False).iterencode(obj):
        check()
        data = part.encode("ascii")
        size += len(data)
        if size > 16777216:
            raise ValueError
        digest.update(data)
        check()
    result = "sha256:" + digest.hexdigest()
    check()
    return result


def _bind(originals, derived, dataset_bytes, bundle_ids, deadline_ms, start):
    if (type(originals) is not OriginalStore or type(derived) is not derived_store.Store
            or type(dataset_bytes) is not bytes or type(bundle_ids) is not tuple
            or len(bundle_ids) > 128 or type(deadline_ms) is not int
            or not 1 <= deadline_ms <= 120000):
        raise ValueError
    end = start + deadline_ms / 1000

    def check():
        if time.monotonic() >= end:
            raise ValueError

    check()
    for ident in bundle_ids:
        check()
        if type(ident) is not str or not re.fullmatch(r"[0-9a-f]{64}", ident):
            raise ValueError
    if any(a >= b for a, b in zip(bundle_ids, bundle_ids[1:])):
        raise ValueError
    check()
    remaining = min(30000, int((end - time.monotonic()) * 1000))
    if remaining < 1:
        raise ValueError
    dataset = text_evaluation_dataset.admit(dataset_bytes, deadline_ms=remaining)
    check()
    atoms = set()
    occurrences = 0
    for case in dataset.cases:
        for req in case.requirements:
            for alternative in req.alternatives:
                for span in alternative:
                    check()
                    occurrences += 1
                    atoms.add((span.revision_id, span.extraction_id, span.block_id,
                               span.start, span.end, span.text_sha256))
    check()
    atoms = sorted(atoms)
    check()
    span_length = 0
    for atom in atoms:
        check()
        span_length += atom[4] - atom[3]
    if (occurrences > 4096 or len(atoms) > 4096
            or span_length > 4194304 or bool(atoms) != bool(bundle_ids)):
        raise ValueError
    check()

    def observe():
        observations = []
        membership = [[] for _ in atoms]
        blocks_total = bytes_total = matched_bytes = 0
        for ident in bundle_ids:
            check()
            value = ingestion_store.load(originals, derived, ident)
            check()
            block_count = len(value.blocks)
            member_bytes = len(value.metadata_json)
            for _, data in value.members:
                check()
                member_bytes += len(data)
            blocks_total += block_count
            bytes_total += member_bytes
            if blocks_total > 4096 or bytes_total > 100663296 or value.adapter != "structured_text":
                raise ValueError
            revision = value.revision.revision_id
            extraction = value.dependency.extraction_id
            metadata_hash = hashlib.sha256(value.metadata_json).hexdigest()
            check()
            observations.append(BundleObservation(ident, metadata_hash, revision, extraction,
                                                  block_count, member_bytes))
            matched = False
            lookup = {}
            for block in value.blocks:
                check()
                lookup[(block.revision_id, block.extraction_id, block.block_id)] = block
            for i, atom in enumerate(atoms):
                check()
                block = lookup.get(atom[:3])
                if block is None:
                    continue
                matched = True
                if (atom[0] != revision or atom[1] != extraction or block.origin != "native"
                        or block.kind == "visual" or not 0 <= atom[3] < atom[4] <= len(block.text)):
                    raise ValueError
                encoded = block.text[atom[3]:atom[4]].encode("utf-8")
                check()
                matched_bytes += len(encoded)
                if matched_bytes > 16777216:
                    raise ValueError
                if hashlib.sha256(encoded).hexdigest() != atom[5]:
                    raise ValueError
                check()
                membership[i].append(ident)
            if not matched:
                raise ValueError
            # Drop the final loop references as well as the bundle before the next load.
            block = None
            encoded = None
            data = None
            del value, lookup
        check()
        if any(not ids for ids in membership):
            raise ValueError
        return tuple(observations), tuple(tuple(ids) for ids in membership)

    if atoms:
        first = observe()
        check()
        second = observe()
        check()
        if first != second:
            raise ValueError
        observations, membership = first
        binding_list = []
        for atom, ids in zip(atoms, membership):
            check()
            binding_list.append(GoldBinding(*atom, ids))
        bindings = tuple(binding_list)
        status = "ORIGINALS_REVALIDATED_AT_BIND_TIME"
    else:
        observations, bindings = (), ()
        status = "NO_GOLD_SOURCE_VALIDATED"
    check()
    dataset_hash = hashlib.sha256(dataset_bytes).hexdigest()
    check()
    observed_dicts = []
    for value in observations:
        check()
        observed_dicts.append(asdict(value))
    binding_dicts = []
    for value in bindings:
        check()
        binding_dicts.append(asdict(value))
    obj = dict(dataset_id=dataset.dataset_id, split_id=dataset.split_id,
               dataset_sha256=dataset_hash, observations=observed_dicts,
               bindings=binding_dicts, case_count=dataset.case_count,
               gold_atom_occurrences=occurrences, distinct_atom_count=len(atoms),
               source_binding_status=status)
    check()
    ident = _binding_id(obj, check)
    result = BoundGold(dataset.dataset_id, dataset.split_id, dataset_hash, ident, observations,
                       bindings, dataset.case_count, occurrences, len(atoms), status)
    check()
    return result


def bind(originals, derived, dataset_bytes, bundle_ids, *, deadline_ms=30000):
    """Revalidate selected structured-text sources; stores remain borrowed."""
    try:
        start = time.monotonic()
        return _bind(originals, derived, dataset_bytes, bundle_ids, deadline_ms, start)
    except Exception:
        raise GoldBindingError("text evaluation gold binding refused") from None
