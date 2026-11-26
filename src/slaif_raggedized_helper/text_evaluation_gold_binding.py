"""Private structured-text original-source gold binding; not a qualification."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
import time

from . import derived_store, ingestion_store, private_policy_pin_eligibility as pin_eligibility
from . import provenance_records, source_bound_stage_loss as stage_loss
from . import supplied_policy_eligibility, text_evaluation_dataset
from .private_policy_request import PolicyRequestAdmission
from .raw_snapshot_pin import PinOwner
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


def _bind(originals, derived, dataset_bytes, bundle_ids, deadline_ms, start, *,
          admission=None, pinned=None, dataset=None, op_end=None):
    if (type(originals) is not OriginalStore or type(derived) is not derived_store.Store
            or type(dataset_bytes) is not bytes or type(bundle_ids) is not tuple
            or len(bundle_ids) > 128 or type(deadline_ms) is not int
            or not 1 <= deadline_ms <= 120000
            or (op_end is not None and type(op_end) is not float)):
        raise ValueError
    # The pinned dispatch passes its actual precomputed clipped end as
    # op_end and it is used as-is; only the legacy standalone entry
    # reconstructs the end from its own start clock read, so no second
    # deadline is ever reconstructed from a later clock read.
    end = start + deadline_ms / 1000 if op_end is None else op_end

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
    if dataset is None:
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
            if admission is not None:
                # Genuine selected recheck under the same absolute
                # deadline, checked again before the real nested load.
                pin_eligibility._genuine_recheck(admission, end)
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
            if pinned is not None:
                # Pin tie within the pass: the observed bundle metadata
                # hash, revision and extraction agree with the exact pin
                # before any subsequent work.
                if (revision, extraction, metadata_hash) != pinned.get(ident):
                    raise ValueError
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


def _gate(membership, policy_snapshot, grants, dataset_bytes, case_id, bundle_ids,
          end):
    """Refuse the complete declared batch before any Gold bundle opens.

    Pure: no derived-store lookup, no bundle open and no source I/O.  The
    exact held membership is already bound to its real manifest, and the
    selected case establishes only the effective scope - it cannot shrink
    the atoms whose source the shared body reads.  Under that effective
    case scope, every already admitted whole-dataset atom needs a
    participating admissible revision/extraction, and every declared
    bundle ID needs unambiguous pinned revision, extraction and metadata
    plus readable available partitions.  The whole membership is
    authenticated by the genuine unavailable partitions, but only the
    declared batch is grouped and read-checked, in its real declared
    order, so undeclared pin members preserve their unaffected scopes.
    Any unknown, malformed, ambiguous, unreadable, unavailable or
    uncovered declared entry refuses.
    """
    def check():
        if time.monotonic() >= end:
            raise ValueError

    meter = stage_loss._Meter()
    meter.check = check
    check()
    remaining = min(30000, int((end - time.monotonic()) * 1000))
    if remaining < 1:
        raise ValueError
    dataset = text_evaluation_dataset.admit(dataset_bytes, deadline_ms=remaining)
    check()
    case = None
    for candidate in dataset.cases:
        meter.reserve(1)
        if candidate.case_id == case_id:
            if case is not None:
                raise ValueError
            case = candidate
    if case is None:
        raise ValueError
    # The shared body observes the whole dataset: all admitted atoms, not
    # only the selected case's.
    atoms = set()
    for candidate in dataset.cases:
        for requirement in candidate.requirements:
            for alternative in requirement.alternatives:
                for span in alternative:
                    meter.reserve(1)
                    check()
                    atoms.add((span.revision_id, span.extraction_id))
    # Effective case grants: the genuine shared-binder authority admission
    # of the exact admitted principal intersected with the genuine case
    # declaration, under a bounded meter and the span deadline check.
    _original, effective, _restricted = stage_loss._admit_authority(
        grants, None, case.scope, meter, check)
    check()
    # Genuine unavailable partitions from the isolated verified policy
    # over the exact held membership.
    unavailable = set(
        supplied_policy_eligibility.unavailable_partitions(policy_snapshot, membership))
    check()
    # Only the declared batch is grouped, read-checked and
    # availability-checked; undeclared pin members keep their
    # unaffected scopes.
    declared = set(bundle_ids)
    by_bundle = {}
    for entry in membership.entries:
        meter.reserve(1)
        check()
        if entry.bundle_container_id in declared:
            by_bundle.setdefault(entry.bundle_container_id, []).append(entry)
    pinned = {}
    for ident in bundle_ids:
        check()
        entries = by_bundle.get(ident)
        if entries is None:
            # Unknown declared ID: refuses before any I/O.
            raise ValueError
        triple = (entries[0].revision_id, entries[0].extraction_id,
                  entries[0].bundle_metadata_sha256)
        for entry in entries[1:]:
            check()
            if ((entry.revision_id, entry.extraction_id,
                 entry.bundle_metadata_sha256) != triple):
                raise ValueError
        for entry in entries:
            check()
            if entry.partition_id in unavailable:
                raise ValueError
            scope = provenance_records.admit_record("Scope", entry.scope_bytes)
            if not provenance_records.reader_allows(scope, effective):
                raise ValueError
        pinned[ident] = triple
    # Covered revision/extraction pairs from the actually admitted
    # declared entries only, in the real declared order.
    covered = set()
    for ident in bundle_ids:
        for entry in by_bundle[ident]:
            check()
            covered.add((entry.revision_id, entry.extraction_id))
    if not atoms <= covered:
        raise ValueError
    check()
    return dataset, pinned


def _bind_pinned(admission, owner, dataset_bytes, case_id, bundle_ids, deadline_ms):
    # Fixed private entry: the exact admitted current selected-policy
    # request and the exact active operator-owned pin only; the stores
    # come from the actual owner and the effective case grants from the
    # exact admitted principal intersected with the genuine case
    # declaration.  No caller root, grants, opaque callback, credential,
    # clock, provider, discovery or alternate binder is accepted.
    if (type(admission) is not PolicyRequestAdmission or type(owner) is not PinOwner
            or type(dataset_bytes) is not bytes or type(case_id) is not str
            or type(bundle_ids) is not tuple or len(bundle_ids) > 128
            or not pin_eligibility._deadline_accepted(deadline_ms)):
        raise ValueError
    for ident in bundle_ids:
        if type(ident) is not str or not re.fullmatch(r"[0-9a-f]{64}", ident):
            raise ValueError
    if any(a >= b for a, b in zip(bundle_ids, bundle_ids[1:])):
        raise ValueError
    # One bounded 1..30000 ms operation deadline clipped to the current
    # request lifetime; the request end is never reset or extended, and
    # this actual clipped end is kept through the shared body and owner.
    end = min(time.monotonic() + deadline_ms / 1000, admission._end)
    pin_eligibility._still_within(end)
    # Pure admission: the isolated selected-policy snapshot and the
    # admitted principal's exact bound grants (verified scope), before
    # any owner custody.
    policy_snapshot = pin_eligibility._isolated_policy_snapshot(admission)
    pin_eligibility._still_within(end)
    anchor = pin_eligibility._bounded_admission(
        pin_eligibility._admitted_principal_grants(
            policy_snapshot, admission.principal_id))
    grants = pin_eligibility._bound_grants(admission, anchor)
    pin_eligibility._still_within(end)
    # One real nonblocking owner guard, held through the entire span.
    pin_eligibility._borrowed_owner(owner)
    original_end = None
    try:
        if owner.op is None or owner.state != "ACTIVE":
            raise ValueError
        original_end = owner.op.end
        owner.op.end = end
        # In-memory held capture verification only, no I/O: the exact
        # held membership bound to its real manifest is the only scope
        # material this span evaluates.
        _, _, membership, _ = pin_eligibility._held_capture(owner)
        pin_eligibility._still_within(end)
        # Pre-dispatch gate: the complete declared batch and the captured
        # manifest-bound membership are checked under the effective case
        # scope and exact identity before any bundle opens, without
        # looking it up in the derived store; the one dataset admission
        # is passed to the shared body, not repeated.
        dataset, pinned = _gate(membership, policy_snapshot, grants, dataset_bytes,
                                case_id, bundle_ids, end)
        pin_eligibility._still_within(end)
        # Live namespace and pin association before the shared Gold body.
        owner._association()
        remaining = min(30000, int((end - time.monotonic()) * 1000))
        if remaining < 1:
            raise ValueError
        # The single existing Gold body: the same type/preflight, model
        # and immutable semantic authority checks, both observation
        # passes, result bindings and legacy error behavior; the genuine
        # selected recheck precedes every actual nested bundle load and
        # the remaining time is checked after every observation and after
        # actual loads; the pin tie runs in both passes at the existing
        # post-load validation before subsequent work.  The actual
        # clipped end is passed through as op_end, so every real check,
        # recheck and dispatch inside the body uses that exact end,
        # never a reconstructed second deadline.
        result = _bind(owner.originals, owner.derived, dataset_bytes, bundle_ids,
                       remaining, time.monotonic(), admission=admission,
                       pinned=pinned, dataset=dataset, op_end=end)
        pin_eligibility._still_within(end)
        return result
    finally:
        if original_end is not None:
            owner.op.end = original_end
        owner.guard.release()


def bind_pinned(admission, owner, dataset_bytes, case_id, bundle_ids, *,
                deadline_ms=30000):
    """Revalidate one admitted case's declared bundles under one held pin.

    Binds the exact admitted current selected-policy request
    (``private_policy_request.PolicyRequestAdmission``) and the exact
    active operator-owned pin (``raw_snapshot_pin.PinOwner``) to the
    single existing Gold body: the stores come only from the actual
    owner, the effective case grants from the exact admitted principal
    intersected with the genuine case declaration through the genuine
    shared-binder authority admission, and one real nonblocking owner
    guard is held across the pre-dispatch gate, the shared body and the
    pin tie, restoring the owner operation's exact prior deadline before
    release on every exit.  Before any bundle opens, the complete
    declared batch is checked under the effective case scope, which
    cannot shrink the whole-dataset atoms the shared body reads; the
    whole captured manifest-bound membership is authenticated by the
    genuine unavailable partitions, and undeclared pin members preserve
    their unaffected scopes; a genuine
    selected recheck precedes every actual nested bundle load in both
    observation passes with the remaining time checked before the load
    and after it; and the observed bundle metadata hash, revision and
    extraction are compared to the exact pin in both passes at the
    existing post-load validation.  The caller supplies no root, grants,
    opaque callback, credential, clock, provider, discovery or alternate
    binder.  Every ordinary failure is one fixed content-free
    :class:`GoldBindingError`; a non-Exception interruption object
    propagates by identity, preserving interruption and cleanup
    semantics.  This cut does not separately reauthorize the nested
    original source or certify later delivery or rights.
    """
    try:
        return _bind_pinned(admission, owner, dataset_bytes, case_id, bundle_ids,
                            deadline_ms)
    except Exception:
        raise GoldBindingError("text evaluation gold binding refused") from None
