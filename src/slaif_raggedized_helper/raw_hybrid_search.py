"""Private source-backed hybrid DATA composition, without serving qualification."""
from dataclasses import asdict, dataclass
import hashlib
import importlib.metadata
import json
import math
import re
import time
import unicodedata

from . import derived_store, private_policy_pin_eligibility as pin_eligibility
from . import raw_dense_search as dense, raw_lexical_search as lexical
from . import raw_rank_fusion as fusion, raw_snapshot_catalog as catalog
from . import provenance_records
from . import source_bound_stage_loss as stage_loss
from . import text_evaluation_dataset as evaluation_dataset
from .private_policy_request import PolicyRequestAdmission
from .raw_snapshot_pin import PinOwner
from .source_admission import OriginalStore


class HybridSearchError(ValueError):
    """Content-free refusal of the complete request."""


@dataclass(frozen=True, slots=True)
class HybridResult:
    snapshot_id: str
    catalog_id: str
    query_id: str
    query_text_sha256: str
    query_payload_sha256: str
    authority_sha256: str
    query_origin: str
    qualification: str
    dense: dense.DenseResult
    lexical: lexical.LexicalResult
    fusion: fusion.FusionResult


def _check(condition):
    if not condition:
        raise ValueError


def _wire(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _ranking(modality, snapshot, catalog_id, query_id, hits):
    entries = tuple(fusion.Entry(h.ordinal, h.partition_id, h.chunk_id, h.revision_id,
                                 h.representation_id, h.rank) for h in hits)
    return fusion.Ranking(modality, 'COMPLETE', snapshot, catalog_id, query_id, entries)


def _trace_link(result, engine, expected, k, cap, remaining):
    """Admit bounded producer DTOs, then verify their old identity and linkage."""
    is_dense = engine is dense
    trace = result.trace
    trace_type = dense.DenseTrace if is_dense else lexical.LexicalTrace
    row_type = dense.DenseTraceRow if is_dense else lexical.LexicalTraceRow
    part_type = dense.DensePartitionTrace if is_dense else lexical.LexicalPartitionTrace
    _check(type(trace) is trace_type)

    def string(value, prefixed=False):
        _check(type(value) is str and len(value) <= 128)
        _check(re.fullmatch(('sha256:' if prefixed else '') + r'[0-9a-f]{64}', value))

    for name in ('trace_id', 'snapshot_id', 'catalog_id'):
        string(getattr(trace, name), True)
    for name, value in expected.items():
        actual = getattr(trace, name)
        _check(type(actual) is str and len(actual) <= 128)
        if name not in ('backend', 'method'):
            string(actual, name in ('snapshot_id', 'catalog_id', 'query_definition_fingerprint'))
        _check(actual == value)
    _check(type(trace.k) is int and trace.k == k and type(trace.partition_cap) is int
           and trace.partition_cap == cap)
    for name, value in (('input_origin', 'SUPPLIED_UNVERIFIED'),
                        ('qualification', 'NOT_QUALIFIED'),
                        ('authorization_status', 'SUPPLIED_SCOPE_CHECKS_ONLY'),
                        ('execution_status', 'NOT_ATTESTED')):
        actual = getattr(trace, name)
        _check(type(actual) is str and len(actual) <= 128 and actual == value)
    rows, parts = trace.rows, trace.partitions
    _check(type(rows) is tuple and len(rows) <= 4096 and type(parts) is tuple
           and len(parts) <= 128)
    sequences = [trace.selected_ordinals, trace.returned_ordinals]
    _check(type(sequences[0]) is tuple and len(sequences[0]) <= 4096
           and type(sequences[1]) is tuple and len(sequences[1]) <= k)
    total = sum(map(len, sequences))
    for part in parts:
        remaining()
        _check(type(part) is part_type)
        string(part.partition_id, True)
        for name in ('eligible_ordinals', 'ranked_ordinals', 'selected_ordinals',
                     'returned_ordinals'):
            seq = getattr(part, name)
            _check(type(seq) is tuple and len(seq) <= (k if name == 'returned_ordinals' else 4096))
            total += len(seq)
            _check(total <= 16504)
            sequences.append(seq)
    for row in rows:
        remaining()
        _check(type(row) is row_type and type(row.ordinal) is int and 0 <= row.ordinal < 4096)
        for name in ('partition_id', 'chunk_id', 'revision_id'):
            string(getattr(row, name), True)
        string(row.representation_id)
    for seq in sequences:
        remaining()
        for ordinal in seq:
            _check(type(ordinal) is int and 0 <= ordinal < 4096)
        remaining()
    counts = result.allowed_partition_counts if is_dense else result.partitions
    hit_type = dense.Hit if is_dense else lexical.Hit
    count_type = dense.PartitionCount if is_dense else lexical.PartitionCount
    _check(type(result.hits) is tuple and len(result.hits) <= k and
           type(counts) is tuple and len(counts) <= 128)
    count_names = ('eligible', 'selected', 'returned') if is_dense else (
        'eligible', 'matching', 'selected', 'returned')
    for count in counts:
        remaining()
        _check(type(count) is count_type)
        string(count.partition_id, True)
        for name in count_names:
            n = getattr(count, name)
            _check(type(n) is int and 0 <= n <= 4096)
    for name in count_names:
        n = getattr(result, name)
        _check(type(n) is int and 0 <= n <= 4096 and
               n == sum(getattr(count, name) for count in counts))
    _check(result.eligible == len(rows) and result.selected == len(trace.selected_ordinals)
           and result.returned == len(trace.returned_ordinals) == len(result.hits))
    before = result.eligible if is_dense else result.matching
    _check(type(result.partition_cap_applied) is bool and
           result.partition_cap_applied == (before > result.selected) and
           type(result.global_cap_applied) is bool and
           result.global_cap_applied == (result.selected > result.returned))
    remaining()
    if is_dense:
        engine._validate_trace(rows, parts, trace.selected_ordinals, trace.returned_ordinals,
                               counts, cap, k)
    else:
        engine._validate_trace(rows, parts, trace.selected_ordinals, trace.returned_ordinals,
                               counts, cap, k, remaining)
    remaining()
    by_ordinal = {row.ordinal: row for row in rows}
    for rank, hit in enumerate(result.hits, 1):
        remaining()
        _check(type(hit) is hit_type and type(hit.ordinal) is int and 0 <= hit.ordinal < 4096
               and type(hit.rank) is int and hit.rank == rank and type(hit.score) is float
               and math.isfinite(hit.score) and type(hit.scope_bytes) is bytes and
               type(hit.original_chunk_bytes if is_dense else hit.chunk_bytes) is bytes)
        for name in ('partition_id', 'chunk_id', 'revision_id'):
            string(getattr(hit, name), True)
        string(hit.representation_id)
        row = by_ordinal.get(hit.ordinal)
        _check(row is not None and all(getattr(hit, name) == getattr(row, name) for name in
               ('partition_id', 'chunk_id', 'revision_id', 'representation_id')))
    _check(tuple(hit.ordinal for hit in result.hits) == trace.returned_ordinals)
    header = {name: getattr(trace, name) for name in expected}
    obj = dict(schema=1, kind=('slaif-raw-dense-authorized-trace-v1' if is_dense else
                               'slaif-raw-lexical-authorized-trace-v1'),
               **header, k=k, partition_cap=cap, rows=[asdict(row) for row in rows],
               partitions=[asdict(part) for part in parts],
               selected_ordinals=trace.selected_ordinals, returned_ordinals=trace.returned_ordinals)
    remaining()
    _check(engine._trace_hash(obj, remaining) == trace.trace_id)
    remaining()


def search(originals, derived, store_root, snapshot_id, text, query_payload, *, query_space_id,
           query_definition_fingerprint, query_policy_id, query_execution_fingerprint, grants,
           restrictions=None, dense_k=60, lexical_k=60, partition_cap=60, k=60,
           deadline_ms=120000, trace=False):
    """Compose actual engines under one cooperative deadline and captured authority."""
    try:
        _check(type(trace) is bool)
        return _search(originals, derived, store_root, snapshot_id, text, query_payload,
                       query_space_id, query_definition_fingerprint, query_policy_id,
                       query_execution_fingerprint, grants, restrictions, dense_k, lexical_k,
                       partition_cap, k, deadline_ms, trace)
    except Exception:
        raise HybridSearchError('hybrid search refused') from None


def _search(originals, derived, root, snapshot, text, payload, space, definition, policy,
            execution, grants, restrictions, dense_k, lexical_k, cap, k, deadline_ms, trace,
            *, owner=None, admission=None, end=None, held=None):
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = time.monotonic() + deadline_ms / 1000 if end is None else end

    def remaining():
        ms = math.floor((end - time.monotonic()) * 1000)
        _check(ms > 0)
        return ms

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(type(root) is str and len(root) <= 4096 and root.startswith('/') and root != '/')
    _check(len(root.encode('utf-8')) <= 4096 and
           all(unicodedata.category(c) != 'Cc' for c in root) and
           all(part not in ('', '.', '..') for part in root[1:].split('/')))
    _check(type(snapshot) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', snapshot))
    for value, prefix in ((space, ''), (definition, 'sha256:'), (policy, ''), (execution, '')):
        _check(type(value) is str and re.fullmatch(re.escape(prefix) + r'[0-9a-f]{64}', value))
    _check(all(type(value) is int and 1 <= value <= 60 for value in (dense_k, lexical_k, cap, k)))
    _check(type(text) is str and len(text) <= 8192)
    text_bytes = text.encode('utf-8')
    _check(len(text_bytes) <= 32768 and type(payload) is bytes and len(payload) == 4096)
    grants, restrictions = lexical._authority(grants, restrictions)
    _check(grants is not None)
    authority_pair = [grants.model_dump(mode='json'),
                      None if restrictions is None else restrictions.model_dump(mode='json')]
    authority_sha = _sha(_wire(authority_pair))
    remaining()
    for package, version in (('numpy', '2.5.4'), ('bm25s', '0.2.14'), ('scipy', '1.18.1')):
        _check(importlib.metadata.version(package) == version)
    import numpy as np
    import bm25s  # noqa: F401
    import scipy  # noqa: F401

    _check(np.__version__ == '2.5.4')
    query = np.frombuffer(payload, dtype='<f4')
    _check(bool(np.isfinite(query).all()) and abs(float(np.linalg.norm(query)) - 1) <= 1e-4)
    text_sha, payload_sha = _sha(text_bytes), _sha(payload)
    if owner is not None:
        # O2: the second genuine current observation, after verified
        # scope and actual association, after all earlier shared-body
        # validation and before the first real catalog call.
        pin_eligibility._genuine_recheck(admission, end)
        remaining()
    source = catalog.load_catalog(originals, derived, root, snapshot, deadline_ms=remaining())
    remaining()
    _check(type(source) is catalog.Catalog and source.snapshot_id == snapshot)
    analyzer_id = json.loads(source.core_bytes)['analyzer']['fingerprint']
    query_id = _sha(_wire(dict(kind='raw-hybrid-query/v1', snapshot_id=snapshot,
                               catalog_id=source.catalog_id, query_text_sha256=text_sha,
                               query_payload_sha256=payload_sha, query_space_id=space,
                               query_definition_fingerprint=definition, query_policy_id=policy,
                               query_execution_fingerprint=execution,
                               authority_sha256=authority_sha,
                               dense_k=dense_k, lexical_k=lexical_k, partition_cap=cap, k=k)))
    dr = dense.search(originals, derived, root, snapshot, payload, query_space_id=space,
                      query_definition_fingerprint=definition, query_policy_id=policy,
                      query_execution_fingerprint=execution, grants=grants,
                      restrictions=restrictions,
                      k=dense_k, partition_cap=cap, deadline_ms=remaining(), trace=trace)
    remaining()
    _check(type(dr) is dense.DenseResult and
           (dr.snapshot_id, dr.catalog_id, dr.query_payload_sha256, dr.query_origin,
            dr.qualification) == (snapshot, source.catalog_id, payload_sha,
                                  'SUPPLIED_UNVERIFIED', 'NOT_QUALIFIED'))
    if owner is not None:
        # O3: the third genuine current observation, after the real
        # dense output completes and before any real lexical call; a
        # detected change refuses here with zero new lexical and
        # fusion calls - an already-started earlier operation cannot
        # be undone.
        pin_eligibility._genuine_recheck(admission, end)
        remaining()
    lr = lexical.search(originals, derived, root, snapshot, text, grants=grants,
                        restrictions=restrictions, k=lexical_k, partition_cap=cap,
                        deadline_ms=remaining(), trace=trace)
    remaining()
    _check(type(lr) is lexical.LexicalResult and
           (lr.snapshot_id, lr.catalog_id, lr.query_text_sha256, lr.analyzer_fingerprint,
            lr.backend, lr.method) ==
           (snapshot, source.catalog_id, text_sha, analyzer_id,
            'bm25s-lucene/0.2.14/2.5.4/1.18.1', 'lucene'))
    if trace:
        common = dict(snapshot_id=snapshot, catalog_id=source.catalog_id,
                      authority_sha256=authority_sha)
        _trace_link(dr, dense, dict(**common, query_payload_sha256=payload_sha,
                    query_space_id=space, query_definition_fingerprint=definition,
                    query_policy_id=policy, query_execution_fingerprint=execution),
                    dense_k, cap, remaining)
        _trace_link(lr, lexical, dict(**common, query_text_sha256=text_sha,
                    analyzer_fingerprint=analyzer_id,
                    backend='bm25s-lucene/0.2.14/2.5.4/1.18.1', method='lucene'),
                    lexical_k, cap, remaining)
    else:
        _check(dr.trace is None and lr.trace is None)
    if owner is not None:
        # O4: the fourth genuine current observation, after the real
        # lexical response validation and optional trace links and
        # before the first real fusion call; a detected change refuses
        # here with zero new fusion, catalog or directory calls - an
        # already-started earlier operation cannot be undone.
        pin_eligibility._genuine_recheck(admission, end)
        remaining()
    fr = fusion.fuse(originals, derived, root, snapshot, query_id,
                     dense=_ranking('dense', snapshot, source.catalog_id, query_id, dr.hits),
                     lexical=_ranking('lexical', snapshot, source.catalog_id, query_id, lr.hits),
                     grants=grants, restrictions=restrictions, k=k, deadline_ms=remaining())
    remaining()
    _check(type(fr) is fusion.FusionResult and
           (fr.snapshot_id, fr.catalog_id, fr.query_id, fr.ranking_origin, fr.qualification,
            fr.dense_status, fr.lexical_status, fr.degraded) ==
           (snapshot, source.catalog_id, query_id, 'SUPPLIED_UNVERIFIED', 'NOT_QUALIFIED',
            'COMPLETE', 'COMPLETE', False))
    fresh = catalog.load_catalog(originals, derived, root, snapshot, deadline_ms=remaining())
    remaining()
    _check(fresh == source and fresh.catalog_id == source.catalog_id)
    if owner is not None:
        # Final owned validation under the single held guard: the
        # actual owner sequence with the association before and after
        # the one distinct last full reload, compared with the exact
        # originally held PinData bound before the body, not a newly
        # read alias.
        owner._association()
        loaded = owner._load(snapshot)
        owner._association()
        _check(loaded == held.data)
        remaining()
    result = HybridResult(snapshot, source.catalog_id, query_id, text_sha, payload_sha,
                          authority_sha, 'SUPPLIED_UNVERIFIED', 'NOT_QUALIFIED', dr, lr, fr)
    remaining()
    return result


def search_pinned(admission, owner, text, query_payload, *, query_space_id,
                  query_definition_fingerprint, query_policy_id,
                  query_execution_fingerprint, dense_k=60, lexical_k=60,
                  partition_cap=60, k=60, deadline_ms=30000, trace=False):
    """One fixed private held-pin route through the real hybrid search.

    Binds the exact admitted current selected-policy request
    (``private_policy_request.PolicyRequestAdmission``) and the exact
    active operator-owned pin (``raw_snapshot_pin.PinOwner``) to the
    existing hybrid engines: the stores, store root, snapshot identity
    and admitted grants come only from the actual owner and verified
    selected material; the principal's exact admitted scope is used
    with no additional caller restriction.  The caller supplies no
    root, stores, snapshot ID, grants, provider, callable, alternate
    clock or credential.  One real nonblocking owner guard is held
    through the one existing hybrid body; the span never calls
    ``PinOwner.check`` or re-enters the borrowed preparation guard,
    and the private operation does not acquire, close or return
    ownership of the input pin.  One original absolute operation
    deadline, bounded to the accepted 1..30000 ms reader range, is
    clipped to the current request lifetime and anchors
    the owner operation's ``op.end`` only while held, restoring its
    original exact value in a finally before guard release on
    success, ordinary refusal and interruption.  Five genuine current
    observations run at the precisely named cuts: O1 after pure
    admission and nonblocking owner custody, with no association,
    catalog or source I/O; O2 after verified scope and actual
    association, before the first real catalog call in the shared
    body; O3 after real dense output completes, before any real
    lexical call, where a detected change refuses with zero new
    lexical and fusion calls; O4 after real lexical output completes
    and is validated, with its optional trace links, before the first
    real fusion call, where a detected change refuses with zero new
    fusion, catalog or directory calls; O5 after the final actual
    pin association/full revalidation and its post-load association,
    with the final exact authority check and the true remaining
    deadline, before usable return.  Scope drift, expired budget and
    late usable results refuse throughout.  The public :func:`search`
    signature, normal deadline and outcomes and every original caller
    path stay exact; this route exposes one fixed content-free
    ordinary refusal and preserves a non-Exception interruption
    object by identity.
    """
    try:
        _check(type(trace) is bool)
        return _search_pinned(admission, owner, text, query_payload, query_space_id,
                              query_definition_fingerprint, query_policy_id,
                              query_execution_fingerprint, dense_k, lexical_k,
                              partition_cap, k, deadline_ms, trace)
    except Exception:
        raise HybridSearchError('hybrid search refused') from None


def _case_bound_scope(full_grants, case_scope, end):
    # The genuine existing case-scope intersection: the narrower
    # effective case value derived from the exact full principal
    # anchor and the admitted case declaration, with no additional
    # restriction; bounded meter work under the clipped deadline.
    def check():
        pin_eligibility._still_within(end)

    meter = stage_loss._Meter()
    meter.check = check
    try:
        _, effective, restricted = stage_loss._admit_authority(
            full_grants, None, case_scope, meter, check)
    except Exception:
        raise pin_eligibility._Refused() from None
    if restricted is not None or type(effective) is not provenance_records.Grants:
        raise pin_eligibility._Refused()
    return effective


def _search_pinned(admission, owner, text, payload, space, definition, policy,
                   execution, dense_k, lexical_k, cap, k, deadline_ms, trace,
                   *, case_bytes=None, case_id=None):
    # Fixed private entry: exact admission and exact owner only; the
    # new public case entry selects the fixed internal case path,
    # which admits the bounded canonical dataset and derives the case
    # question and effective grants before guard custody.
    if type(admission) is not PolicyRequestAdmission or type(owner) is not PinOwner:
        raise pin_eligibility._Refused()
    if not pin_eligibility._deadline_accepted(deadline_ms):
        raise pin_eligibility._Refused()
    case_bound = case_bytes is not None
    if case_bound:
        if type(case_bytes) is not bytes or not 1 <= len(case_bytes) <= 16777216:
            raise pin_eligibility._Refused()
        if type(case_id) is not str or not 1 <= len(case_id) <= 128:
            raise pin_eligibility._Refused()
    # One bounded 1..30000 ms operation deadline clipped to the current
    # request lifetime; the request end is never reset or extended.
    end = min(time.monotonic() + deadline_ms / 1000.0, admission._end)
    pin_eligibility._still_within(end)
    # Pure admission: the isolated selected-policy snapshot and the
    # admitted principal's exact full bound grants (verified scope),
    # before any owner custody or I/O.
    policy_snapshot = pin_eligibility._isolated_policy_snapshot(admission)
    pin_eligibility._still_within(end)
    anchor = pin_eligibility._bounded_admission(
        pin_eligibility._admitted_principal_grants(
            policy_snapshot, admission.principal_id))
    full_grants = pin_eligibility._bound_grants(admission, anchor)
    pin_eligibility._still_within(end)
    if case_bound:
        # Fixed internal case path: the bounded canonical dataset is
        # admitted under the genuine parser through the same clipped
        # absolute budget; the exact admitted case question and the
        # narrower effective case value come only from the admitted
        # dataset and the genuine existing case-scope intersection
        # over the exact full anchor, with no additional restriction,
        # before guard custody; a missing or invalid case refuses
        # without widening, and the full anchor stays carried for the
        # final detached authority comparison.
        remaining_ms = int((end - time.monotonic()) * 1000)
        if remaining_ms < 1:
            raise pin_eligibility._Refused()
        try:
            dataset = evaluation_dataset.admit(
                case_bytes, deadline_ms=min(remaining_ms, 30000))
        except Exception:
            raise pin_eligibility._Refused() from None
        pin_eligibility._still_within(end)
        case = next((c for c in dataset.cases if c.case_id == case_id), None)
        if case is None:
            raise pin_eligibility._Refused()
        pin_eligibility._still_within(end)
        text = case.question
        grants = _case_bound_scope(full_grants, case.scope, end)
        pin_eligibility._still_within(end)
    else:
        # Legacy path: the principal's exact admitted scope, unchanged.
        grants = full_grants
    # One real nonblocking owner guard, held through the entire span.
    pin_eligibility._borrowed_owner(owner)
    original_end = None
    try:
        if owner.op is None or owner.state != 'ACTIVE':
            raise pin_eligibility._Refused()
        original_end = owner.op.end
        owner.op.end = end
        # In-memory held capture verification only, no I/O; the
        # captured membership is the only scope material this span
        # evaluates.
        _, _, membership, _ = pin_eligibility._held_capture(owner)
        # The originally held PinData bound before the body; the final
        # full revalidation compares against it, not a newly read alias.
        held = owner.value
        pin_eligibility._still_within(end)
        # O1: the first genuine current observation, after pure
        # admission, nonblocking owner custody and in-memory capture
        # verification, before captured scope use, with no
        # association, catalog or source I/O.
        pin_eligibility._genuine_recheck(admission, end)
        pin_eligibility._still_within(end)
        # The genuine isolated policy and captured membership scope
        # rules: an unavailable or unusable scope refuses before any
        # catalog or source I/O.
        if pin_eligibility._scope_refused(policy_snapshot, membership, grants, None):
            raise pin_eligibility._Refused()
        pin_eligibility._still_within(end)
        # Live namespace and pin association before the shared body;
        # the root is the actual association's validated root string,
        # not the held root file descriptor.
        owner._association()
        pin_eligibility._still_within(end)
        result = _search(owner.originals, owner.derived, owner.op.path,
                         held.data.snapshot_id, text, payload, space, definition,
                         policy, execution, grants, None, dense_k, lexical_k, cap, k,
                         deadline_ms, trace, owner=owner, admission=admission, end=end,
                         held=held)
        # O5: after the final actual pin association/full revalidation
        # and its post-load association, with the final exact authority
        # check and the true remaining deadline, before usable return.
        pin_eligibility._genuine_recheck(admission, end)
        if pin_eligibility._bound_grants(admission, full_grants) != full_grants:
            raise pin_eligibility._Refused()
        pin_eligibility._still_within(end)
        return result
    finally:
        if original_end is not None:
            owner.op.end = original_end
        owner.guard.release()


def search_pinned_case(admission, owner, dataset_bytes, case_id, query_payload, *,
                       query_space_id, query_definition_fingerprint, query_policy_id,
                       query_execution_fingerprint, dense_k=60, lexical_k=60,
                       partition_cap=60, k=60, deadline_ms=30000, trace=False):
    """One fixed private case-bound held-pin route through the real hybrid search.

    Selects the fixed internal case path of the one shared
    :func:`search_pinned` body: the exact admitted current
    selected-policy request (``private_policy_request.
    PolicyRequestAdmission``), the exact active operator-owned pin
    (``raw_snapshot_pin.PinOwner``), bounded canonical
    text-evaluation dataset bytes and one exact case ID.  The case
    question and the narrowed effective scope come only from the
    genuinely admitted dataset and its case declaration; the caller
    supplies no text, grants, restrictions, stores, root, snapshot
    ID, provider, callable, alternate clock or credential.  The
    dataset input is validated as exact canonical dataset bytes at
    the entry: a None dataset or any other non-bytes value receives
    this entry's fixed content-free refusal before the shared body,
    before owner custody, before the first genuine observation,
    before any live namespace association and before any protected
    dispatch.  The
    dataset is admitted through the genuine canonical parser under
    the same clipped absolute budget, and the narrower effective
    case value is derived through the genuine existing case-scope
    intersection from the exact full principal anchor with no
    additional restriction, before guard custody.  The full
    principal immutable policy-derived value is carried separately
    for the detached current authority comparisons, while the
    effective value serves the actual eligibility and the engines,
    including the authority hash bound to the result.  A missing or
    invalid case, or an unavailable partition inside the actual
    effective readable scope, refuses before the first catalog; an
    unavailable partition outside that scope does not block the
    unaffected scope, and the scope is never widened.  The same
    private preparation, one real nonblocking owner guard held
    through the one existing hybrid body, live association and
    ownership span, and the five genuine current observations at the
    precisely named cuts O1 through O5 are reused unchanged; the
    span never calls ``PinOwner.check`` or re-enters the borrowed
    preparation guard, and the private operation does not acquire,
    close or return ownership of the input pin.  One original
    absolute operation deadline, bounded to the accepted 1..30000 ms
    reader range, is clipped to the current request lifetime and
    anchors the owner operation's ``op.end`` only while held,
    restoring its original exact value in a finally before guard
    release on success, ordinary refusal and interruption.  Scope
    drift, expired budget and late usable results refuse throughout;
    no second retrieval or duplicate engine loop happens.  The
    public :func:`search` and :func:`search_pinned` signatures,
    normal deadlines, the legacy call shape and every original
    caller path stay exact; this route exposes one fixed content-free
    ordinary refusal and preserves a non-Exception interruption
    object by identity.
    """
    try:
        _check(type(trace) is bool)
        # Exact nominal case input: the bounded canonical dataset
        # must already be exact dataset bytes.  A None dataset (the
        # legacy sentinel of the shared body) or any other non-bytes
        # value is refused here, before the shared body can interpret
        # the sentinel, before owner custody, before the first
        # genuine observation and before any live namespace
        # association or protected dispatch.
        _check(type(dataset_bytes) is bytes)
        return _search_pinned(admission, owner, None, query_payload, query_space_id,
                              query_definition_fingerprint, query_policy_id,
                              query_execution_fingerprint, dense_k, lexical_k,
                              partition_cap, k, deadline_ms, trace,
                              case_bytes=dataset_bytes, case_id=case_id)
    except Exception:
        raise HybridSearchError('hybrid search refused') from None
