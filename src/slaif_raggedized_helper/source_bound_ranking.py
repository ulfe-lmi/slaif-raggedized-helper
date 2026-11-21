"""Private, ephemeral original-source bindings for a supplied ranking."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
import time
import unicodedata

from . import derived_store, ingestion_store, provenance_records as p
from . import private_policy_pin_eligibility as pin_eligibility
from . import raw_snapshot_catalog, raw_snapshot_membership, raw_snapshot_rows
from . import source_bound_stage_loss as stage_loss
from . import supplied_policy_eligibility, text_evaluation_dataset
from .private_policy_request import PolicyRequestAdmission
from .raw_snapshot_pin import PinOwner
from .source_admission import OriginalStore, Revision


class SourceBindingError(Exception):
    """Content-free refusal of a source binding."""


@dataclass(frozen=True, slots=True, repr=False)
class BoundFragment:
    block_id: str
    start: int
    end: int
    text_sha256: str


@dataclass(frozen=True, slots=True, repr=False)
class BoundRow:
    ordinal: int
    partition_id: str
    chunk_id: str
    revision_id: str
    extraction_id: str
    representation_id: str
    bundle_container_id: str
    batch_container_id: str
    scope_sha256: str
    fragments: tuple[BoundFragment, ...]


@dataclass(frozen=True, slots=True, repr=False)
class BoundRanking:
    binding_id: str
    snapshot_id: str
    catalog_id: str
    authority_sha256: str
    rows: tuple[BoundRow, ...]
    row_count: int
    fragment_count: int
    source_binding_status: str
    input_origin: str = field(default="SUPPLIED_RANKING_UNVERIFIED", init=False)
    authorization_status: str = field(default="SUPPLIED_SCOPE_CHECKS_ONLY", init=False)
    execution_status: str = field(default="NOT_ATTESTED", init=False)
    qualification: str = field(default="NOT_QUALIFIED", init=False)


def _check(value):
    if not value:
        raise ValueError


def _json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _timed_hash(data, check):
    check()
    result = _hash(data)
    check()
    return result


def _authority(value, cls, fields, optional, budget, check):
    check()
    if value is None:
        return None
    _check(
        type(value) is cls
        and type(value.__dict__) is dict
        and len(value.__dict__) == len(fields) + 1
        and "schema_version" in value.__dict__
        and all(name in value.__dict__ for name in fields)
        and not value.__pydantic_extra__
        and type(value.schema_version) is int
        and value.schema_version == 1
    )
    for name in fields:
        check()
        items = value.__dict__[name]
        if items is None:
            _check(optional)
            continue
        _check(type(items) is tuple and len(items) <= 128)
        for item in items:
            check()
            _check(type(item) is str)
            budget[0] += len(item)
            _check(budget[0] <= 65536)
            item.encode("utf-8")
    clone = p._snapshot(value, cls)
    check()
    return clone


class _PassBudget:
    """Count selected occurrences, including repeated content, for one pass."""

    __slots__ = ("blocks", "bundle_bytes", "fragments", "copied_bytes", "block_id_bytes")

    def __init__(self):
        self.blocks = self.bundle_bytes = self.fragments = self.copied_bytes = 0
        self.block_id_bytes = 0

    def bundle(self, blocks, size):
        self.blocks += blocks
        self.bundle_bytes += size
        _check(self.blocks <= 4096 and self.bundle_bytes <= 100663296)

    def member(self, size):
        self.bundle_bytes += size
        _check(self.bundle_bytes <= 100663296)

    def fragment(self, copied, block_id):
        self.fragments += 1
        self.copied_bytes += copied
        self.block_id_bytes += block_id
        _check(
            self.fragments <= 65536
            and self.copied_bytes <= 16777216
            and self.block_id_bytes <= 2097152
        )


def _binding_hash(obj, check, limit=16777216):
    digest = hashlib.sha256(b"slaif-source-bound-supplied-ranking-v1\n")
    size = 0
    encoder = json.JSONEncoder(
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )
    for piece in encoder.iterencode(obj):
        check()
        data = piece.encode("ascii")
        size += len(data)
        _check(size <= limit)
        digest.update(data)
        check()
    return "sha256:" + digest.hexdigest()


def _pass(catalog, originals, derived, ids, grants, restrictions, check,
          *, observe=None, pinned=None):
    # ``observe`` runs one genuine selected observation before every
    # actual selected bundle load; ``pinned`` ties each observed bundle
    # to the exact held pin after load.  Both are inert when omitted.
    check()
    mapping = raw_snapshot_rows.parse(catalog.row_map_bytes)
    check()
    _check(len(mapping.rows) == len(catalog.rows))
    lookup = {}
    for i, (declaration, row) in enumerate(zip(mapping.rows, catalog.rows)):
        check()
        _check(
            declaration.ordinal == i
            and row.declaration_bytes == _json(asdict(declaration))
            and row.representation_id == declaration.representation_id
            and declaration.chunk_id not in lookup
        )
        lookup[declaration.chunk_id] = (declaration, row)
    for ident in ids:
        check()
        _check(ident in lookup)
    groups = {}
    for ident in ids:
        check()
        declaration, row = lookup[ident]
        groups.setdefault(declaration.bundle_container_id, []).append((declaration, row))
    _check(len(groups) <= 128)
    if not ids:
        return (), ()
    check()

    def admit_all(values, fn):
        result = []
        for value in values:
            check()
            result.append(fn(value))
            check()
        return tuple(result)

    revisions = admit_all(catalog.revisions, Revision.model_validate_json)
    dependencies = admit_all(catalog.dependencies, lambda x: p.admit_record("Dependency", x))
    blocks = admit_all(catalog.blocks, lambda x: p.admit_record("Block", x))
    check()
    registry = p.Registry(revisions, dependencies, blocks)
    check()
    revision_bytes, dependency_bytes, block_bytes = (
        set(catalog.revisions),
        set(catalog.dependencies),
        set(catalog.blocks),
    )
    output, observations = {}, []
    budget = _PassBudget()
    for bundle_id in sorted(groups):
        check()
        if observe is not None:
            # One genuine selected observation before this actual
            # selected bundle load in this pass.
            observe()
        bundle = ingestion_store.load(originals, derived, bundle_id)
        check()
        budget.bundle(len(bundle.blocks), len(bundle.metadata_json))
        members = []
        for name, data in bundle.members:
            check()
            budget.member(len(data))
            members.append((name, len(data), _timed_hash(data, check)))
            check()
        metadata_hash = _timed_hash(bundle.metadata_json, check)
        if pinned is not None:
            # Genuine post-load pin tie within the pass: the observed
            # revision, extraction and bundle metadata hash, plus the
            # bound admitted scope (retained as the exact admitted
            # Scope, so the tie never depends on two canonical JSON
            # dialects), agree with the exact held pin before any
            # subsequent work.
            for decl, row in groups[bundle_id]:
                check()
                bound = pinned[decl.chunk_id]
                _check(
                    bundle.revision.revision_id == bound[2]
                    and bundle.dependency.extraction_id == bound[3]
                    and metadata_hash == bound[6]
                    and type(bundle.scope) is type(bound[7])
                    and bundle.scope == bound[7]
                )
        observations.append(
            (
                bundle_id,
                bundle.adapter,
                bundle.status,
                bundle.coverage_kind,
                len(bundle.metadata_json),
                metadata_hash,
                tuple(members),
            )
        )
        _check(
            (bundle.adapter, bundle.status, bundle.coverage_kind)
            == ("structured_text", "complete_text", "unicode_codepoints")
            and bundle.revision.source.media_type in ("text/plain", "text/markdown")
            and _json(bundle.revision.model_dump(mode="json")) in revision_bytes
            and _json(bundle.dependency.model_dump(mode="json")) in dependency_bytes
        )
        block_map = {}
        for block in bundle.blocks:
            check()
            _check(
                block.kind != "visual"
                and block.origin == "native"
                and _json(block.model_dump(mode="json")) in block_bytes
                and block.block_id not in block_map
            )
            block_map[block.block_id] = block
        chunks = {}
        for chunk in bundle.chunks:
            check()
            _check(chunk.chunk_id not in chunks)
            chunks[chunk.chunk_id] = chunk
        for decl, row in groups[bundle_id]:
            check()
            _check(
                decl.bundle_metadata_sha256 == metadata_hash
                and decl.revision_id == bundle.revision.revision_id
                and decl.extraction_id == bundle.dependency.extraction_id
            )
            chunk = chunks[decl.chunk_id]
            _check(
                chunk.revision_id == decl.revision_id
                and chunk.extraction_id == decl.extraction_id
                and _json(chunk.model_dump(mode="json")) == row.chunk_bytes
                and _json(bundle.revision.source.model_dump(mode="json")) == row.source_bytes
            )
            check()
            scope = registry.bind_chunk(chunk)
            check()
            _check(
                scope == bundle.scope and _json(scope.model_dump(mode="json")) == row.scope_bytes
            )
            _check(p.reader_allows(scope, grants, restrictions))
            check()
            fragments = []
            for fragment in chunk.fragments:
                check()
                if type(fragment) is p.Separator:
                    continue
                _check(type(fragment) is p.SourceFragment)
                block = block_map[fragment.block_id]
                _check(
                    0 <= fragment.start < fragment.end <= len(block.text) <= 200000
                    and block.text[fragment.start : fragment.end] == fragment.copied_text
                )
                data = fragment.copied_text.encode("utf-8")
                budget.fragment(len(data), len(fragment.block_id.encode("utf-8")))
                fragments.append(
                    BoundFragment(
                        fragment.block_id, fragment.start, fragment.end, _timed_hash(data, check)
                    )
                )
                check()
            _check(fragments)
            output[decl.chunk_id] = BoundRow(
                decl.ordinal,
                decl.partition_id,
                decl.chunk_id,
                decl.revision_id,
                decl.extraction_id,
                decl.representation_id,
                decl.bundle_container_id,
                decl.batch_container_id,
                _timed_hash(row.scope_bytes, check),
                tuple(fragments),
            )
            check()
        del bundle, chunks, block_map, members, data, chunk, block, fragment, scope
    return tuple(output[x] for x in ids), tuple(observations)


def bind(
    originals,
    derived,
    store_root,
    snapshot_id,
    expected_catalog_id,
    chunk_ids,
    *,
    grants,
    restrictions=None,
    deadline_ms=30000,
):
    """Bind ordered supplied IDs to revalidated originals, without attesting a query."""
    try:
        start = time.monotonic()
        _check(type(deadline_ms) is int and 1 <= deadline_ms <= 30000)
        end = start + deadline_ms / 1000

        def check():
            _check(time.monotonic() < end)

        def remaining():
            check()
            value = int((end - time.monotonic()) * 1000)
            _check(value >= 1)
            return value

        check()
        _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
        _check(
            type(store_root) is str
            and store_root.startswith("/")
            and store_root != "/"
            and len(store_root.encode("utf-8")) <= 4096
            and all(unicodedata.category(c) != "Cc" for c in store_root)
            and all(x not in ("", ".", "..") for x in store_root[1:].split("/"))
        )
        for ident in (snapshot_id, expected_catalog_id):
            _check(type(ident) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", ident))
        _check(type(chunk_ids) is tuple and len(chunk_ids) <= 4096)
        seen = set()
        for ident in chunk_ids:
            check()
            _check(
                type(ident) is str
                and re.fullmatch(r"sha256:[0-9a-f]{64}", ident)
                and ident not in seen
            )
            seen.add(ident)
        budget = [0]
        grants = _authority(
            grants, p.Grants, ("corpora", "versions", "labels"), False, budget, check
        )
        restrictions = _authority(
            restrictions, p.Restrictions, ("corpora", "versions"), True, budget, check
        )
        pair = [
            x.model_dump(mode="json") if x is not None else None for x in (grants, restrictions)
        ]
        encoded = _json(pair)
        _check(len(encoded) <= 262144)
        authority_hash = _timed_hash(encoded, check)
        check()
        rows = _body(
            originals,
            derived,
            store_root,
            snapshot_id,
            expected_catalog_id,
            chunk_ids,
            grants,
            restrictions,
            check,
            remaining,
        )
        return _finalize(rows, snapshot_id, expected_catalog_id, authority_hash, check)
    except Exception:
        raise SourceBindingError("source bound ranking refused") from None


def _body(
    originals,
    derived,
    store_root,
    snapshot_id,
    expected_catalog_id,
    chunk_ids,
    grants,
    restrictions,
    check,
    remaining,
    *,
    observe=None,
    pinned=None,
):
    """The single inherited ranking body over both observation passes.

    Two retained catalog rebuilds (broader trusted integrity I/O) and
    the two identical observation passes over the retained rows;
    ``observe`` runs one genuine selected observation before every
    actual catalog dispatch and every selected bundle load, and
    ``pinned`` ties each observed bundle to the exact held pin after
    load.  Legacy callers omit both hooks and are unchanged.
    """
    if observe is not None:
        # One genuine selected observation before this retained actual
        # catalog dispatch.
        observe()
        check()
    first = raw_snapshot_catalog.load_catalog(
        originals, derived, store_root, snapshot_id, deadline_ms=remaining()
    )
    check()
    _check(first.snapshot_id == snapshot_id and first.catalog_id == expected_catalog_id)
    rows, observations = _pass(
        first,
        originals,
        derived,
        chunk_ids,
        grants,
        restrictions,
        check,
        observe=observe,
        pinned=pinned,
    )
    check()
    if observe is not None:
        # One genuine selected observation before the second retained
        # actual catalog dispatch.
        observe()
        check()
    second = raw_snapshot_catalog.load_catalog(
        originals, derived, store_root, snapshot_id, deadline_ms=remaining()
    )
    check()
    _check(
        first == second
        and second.snapshot_id == snapshot_id
        and second.catalog_id == expected_catalog_id
    )
    rows2, observations2 = _pass(
        second,
        originals,
        derived,
        chunk_ids,
        grants,
        restrictions,
        check,
        observe=observe,
        pinned=pinned,
    )
    _check(rows == rows2 and observations == observations2)
    check()
    return rows


def _finalize(rows, snapshot_id, expected_catalog_id, authority_hash, check):
    """One canonical bound result over the retained rows."""
    count = 0
    serial_rows = []
    for row in rows:
        check()
        count += len(row.fragments)
        serial_rows.append(asdict(row))
        check()
    status = "ORIGINALS_REVALIDATED_AT_BIND_TIME" if rows else "NO_SELECTED_SOURCE_VALIDATED"
    obj = dict(
        schema=1,
        kind="slaif-source-bound-supplied-ranking-v1",
        snapshot_id=snapshot_id,
        catalog_id=expected_catalog_id,
        authority_sha256=authority_hash,
        rows=serial_rows,
        row_count=len(rows),
        fragment_count=count,
        source_binding_status=status,
    )
    binding_id = _binding_hash(obj, check)
    check()
    result = BoundRanking(
        binding_id,
        snapshot_id,
        expected_catalog_id,
        authority_hash,
        rows,
        len(rows),
        count,
        status,
    )
    check()
    return result


def _gate(core, row_map_bytes, membership_bytes, policy_snapshot, grants,
          dataset_bytes, case_id, chunk_ids, end):
    """Refuse the complete selected chunk batch before any new source I/O.

    Pure: no store access, no catalog or bundle load.  The exact held
    core, row map and membership are bound to their real manifest
    descriptors with the actual pure row and membership binds only, and
    the ordered chunk IDs are bound to their held row, entry and scope
    declarations under the effective case scope before any protected
    dispatch.  Unknown, malformed, unreadable or unavailable selected
    entries refuse the whole batch; an unselected unavailable bundle
    never refuses by itself.
    """

    def check():
        if time.monotonic() >= end:
            raise ValueError

    meter = stage_loss._Meter()
    meter.check = check
    check()
    mapping = raw_snapshot_rows.bind(core, row_map_bytes)
    check()
    bound = raw_snapshot_membership.bind(core, row_map_bytes, membership_bytes)
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
    _original, effective, _restricted = stage_loss._admit_authority(
        grants, None, case.scope, meter, check
    )
    check()
    unavailable = set(
        supplied_policy_eligibility.unavailable_partitions(policy_snapshot, bound)
    )
    check()
    by_chunk, by_revision = _bound_indexes(mapping, bound, meter, check)
    return effective, _admit_selected_chunks(
        chunk_ids, by_chunk, by_revision, unavailable, effective, meter, check
    )


def _bound_indexes(mapping, bound, meter, check):
    """The bounded chunk/revision indexes with duplicate refusal."""
    by_chunk = {}
    for row in mapping.rows:
        meter.reserve(1)
        if row.chunk_id in by_chunk:
            raise ValueError
        by_chunk[row.chunk_id] = row
    by_revision = {}
    for entry in bound.entries:
        meter.reserve(1)
        if entry.revision_id in by_revision:
            raise ValueError
        by_revision[entry.revision_id] = entry
    return by_chunk, by_revision


def _admit_selected_chunks(chunk_ids, by_chunk, by_revision, unavailable,
                           effective, meter, check):
    """The pure rank kernel over one ordered selected chunk batch.

    Each selected chunk is bound to its held row, entry and scope
    declarations under the effective case scope before any new source
    I/O: unknown, malformed, unreadable or genuinely unavailable
    selected entries refuse the whole batch, while an unselected
    unavailable bundle never refuses by itself.
    """
    pinned = {}
    for ident in chunk_ids:
        check()
        row = by_chunk.get(ident)
        if row is None:
            # Unknown selected chunk: refuse the full batch before I/O.
            raise ValueError
        entry = by_revision.get(row.revision_id)
        # Exact held linkage: ordinal, scope, revision, extraction,
        # bundle and metadata, sealed by the pure binds and re-asserted
        # for the selected set only.
        if (
            entry is None
            or row.ordinal not in entry.ordinals
            or row.bundle_container_id != entry.bundle_container_id
            or row.bundle_metadata_sha256 != entry.bundle_metadata_sha256
            or row.extraction_id != entry.extraction_id
            or row.source_scope_sha256 != entry.source_scope_sha256
            or row.partition_id != entry.partition_id
        ):
            raise ValueError
        if entry.partition_id in unavailable:
            # A genuinely unavailable selected partition refuses.
            raise ValueError
        scope = p.admit_record("Scope", entry.scope_bytes)
        if not p.reader_allows(scope, effective):
            # An unreadable selected chunk refuses the full batch.
            raise ValueError
        pinned[ident] = (
            row.ordinal,
            row.partition_id,
            row.revision_id,
            row.extraction_id,
            row.bundle_container_id,
            row.batch_container_id,
            row.bundle_metadata_sha256,
            scope,
        )
        check()
    return pinned


def _bind_pinned(admission, owner, dataset_bytes, case_id, expected_catalog_id,
                 chunk_ids, deadline_ms):
    # Fixed private ranking entry: the exact admitted current
    # selected-policy request and the exact active operator-owned pin
    # only.  The stores and snapshot come from the actual owner, and the
    # effective case scope from the exact admitted principal intersected
    # with the genuine case declaration.  No caller scope token, grants,
    # path, snapshot, supplied Catalog, provider, callback or clock is
    # accepted.
    if (
        type(admission) is not PolicyRequestAdmission
        or type(owner) is not PinOwner
        or type(dataset_bytes) is not bytes
        or not 1 <= len(dataset_bytes) <= 16777216
        or type(case_id) is not str
        or not 1 <= len(case_id) <= 128
        or type(expected_catalog_id) is not str
        or re.fullmatch(r"sha256:[0-9a-f]{64}", expected_catalog_id) is None
        or type(chunk_ids) is not tuple
        or len(chunk_ids) > 4096
        or not pin_eligibility._deadline_accepted(deadline_ms)
    ):
        raise ValueError
    # One bounded 1..30000 ms cooperative deadline clipped to the current
    # request lifetime; the single absolute end is established after the
    # nominal envelope validation and before the per-chunk term loop, is
    # never reset or extended, and is kept through that loop, the gate,
    # the shared body and the owner.
    end = min(time.monotonic() + deadline_ms / 1000, admission._end)
    pin_eligibility._still_within(end)

    def check():
        if time.monotonic() >= end:
            raise ValueError

    def remaining():
        check()
        value = int((end - time.monotonic()) * 1000)
        if value < 1:
            raise ValueError
        return value

    check()
    seen = set()
    for ident in chunk_ids:
        check()
        if (
            type(ident) is not str
            or re.fullmatch(r"sha256:[0-9a-f]{64}", ident) is None
            or ident in seen
        ):
            raise ValueError
        seen.add(ident)
    check()
    # Pure admission before any owner custody: the isolated
    # selected-policy snapshot and the admitted principal's exact bound
    # grants (verified scope); the full principal anchor is preserved
    # separately for the final detached admission agreement check.
    policy_snapshot = pin_eligibility._isolated_policy_snapshot(admission)
    pin_eligibility._still_within(end)
    anchor = pin_eligibility._bounded_admission(
        pin_eligibility._admitted_principal_grants(policy_snapshot, admission.principal_id)
    )
    grants = pin_eligibility._bound_grants(admission, anchor)
    pin_eligibility._still_within(end)
    # One real nonblocking owner guard, held through the entire span.
    pin_eligibility._borrowed_owner(owner)
    original_end = None
    try:
        if owner.op is None or owner.state != "ACTIVE":
            raise ValueError
        _check(
            type(owner.originals) is OriginalStore
            and type(owner.derived) is derived_store.Store
        )
        original_end = owner.op.end
        # Clip one end to the request lifetime and the accepted 1..30000
        # ms; anchor the real owner operation end for exact restore.
        owner.op.end = end
        check()
        # In-memory held capture verification only, no I/O: the exact
        # held core, row map and membership bound to their real manifest
        # are the only scope material this span evaluates.
        pointer, core, membership, membership_bytes = pin_eligibility._held_capture(owner)
        pin_eligibility._still_within(end)
        # Pre-dispatch gate: the complete ordered selected chunk batch is
        # bound to the held manifest-bound declarations under the
        # effective case scope before any new catalog or bundle load,
        # without any store lookup.
        effective, pinned = _gate(
            core,
            owner.value.data.row_map.map_bytes,
            membership_bytes,
            policy_snapshot,
            grants,
            dataset_bytes,
            case_id,
            chunk_ids,
            end,
        )
        pin_eligibility._still_within(end)
        # Live namespace and genuine metadata-only association under the
        # held guard; no nested owner.check, no duplicate guard and no
        # extra independent full owner/source reload.
        owner._association()
        check()
        if remaining() < 1:
            raise ValueError

        def observe():
            # One genuine selected observation at each protected cut,
            # with the remaining time checked before the real dispatch.
            pin_eligibility._genuine_recheck(admission, end)
            check()

        # The actual case authority for result binding and source
        # eligibility; the first proof carries no restrictions.
        authority_hash = _timed_hash(
            _json([effective.model_dump(mode="json"), None]), check
        )
        check()
        rows = _body(
            owner.originals,
            owner.derived,
            owner.op.path,
            pointer.snapshot_id,
            expected_catalog_id,
            chunk_ids,
            effective,
            None,
            check,
            remaining,
            observe=observe,
            pinned=pinned,
        )
        result = _finalize(rows, pointer.snapshot_id, expected_catalog_id,
                           authority_hash, check)
        # The full policy-derived anchor, preserved separately from the
        # effective case grants, is re-verified against the detached
        # admission through the existing bound grants before the
        # constructed result is returned: a pure check that adds no
        # selected disk read or delivery attestation.
        if pin_eligibility._bound_grants(admission, anchor) != grants:
            raise ValueError
        # No late usable bound result after the final cut.
        pin_eligibility._still_within(end)
        return result
    finally:
        if original_end is not None:
            owner.op.end = original_end
        owner.guard.release()


def bind_pinned(admission, owner, dataset_bytes, case_id, expected_catalog_id,
                chunk_ids, *, deadline_ms=30000):
    """Bind one admitted case's ordered selected chunks under one held pin.

    Binds the exact admitted current selected-policy request
    (``private_policy_request.PolicyRequestAdmission``) and the exact
    active operator-owned pin (``raw_snapshot_pin.PinOwner``) to the
    single inherited ranking body: the stores and snapshot come only
    from the actual owner, the effective case scope from the exact
    admitted principal intersected with the genuine case declaration
    through the genuine shared-binder authority admission, and one real
    nonblocking owner guard is held across the pure pre-dispatch gate,
    the shared body and the pin tie, restoring the owner operation's
    exact prior deadline before release on every exit.  Before any new
    catalog or bundle load, the complete ordered selected chunk batch is
    bound to the exact held core, row map and membership sealed to their
    real manifest through the actual pure row and membership binds,
    which verify the selected ordinal, scope, exact revision, extraction,
    bundle and metadata linkage; unknown, malformed, unreadable or
    unavailable selected entries refuse the full batch before any new
    source I/O, while an unselected unavailable bundle never refuses by
    itself.  One genuine selected observation precedes each retained
    actual catalog dispatch and each actual selected bundle load in both
    observation passes under the one clipped absolute end, with the
    remaining time checked after every genuine reread and after the
    nested dispatches, so every protected start stops upon denial and no
    late usable bound result is returned; the observed bundle revision,
    extraction, metadata hash and admitted scope are compared to the exact
    held pin in both passes at the post-load validation.  The two
    retained catalog rebuilds still perform broader trusted integrity
    I/O, including original and derived work to unrequested bundles; this
    cut does not reauthorize each nested original, does not preempt an
    in-flight operation, and earlier program and grade source activity
    and later delivery remain open.  The caller supplies no scope token,
    grants, path, snapshot, supplied Catalog, provider, callback or
    clock.  Every ordinary failure is one fixed content-free
    :class:`SourceBindingError`; a non-Exception interruption object
    propagates by identity, preserving interruption and cleanup
    semantics.
    """
    try:
        return _bind_pinned(
            admission, owner, dataset_bytes, case_id, expected_catalog_id,
            chunk_ids, deadline_ms
        )
    except Exception:
        raise SourceBindingError("source bound ranking refused") from None
