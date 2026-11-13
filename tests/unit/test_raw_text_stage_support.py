"""Pure boundary doubles: these do not establish actual retrieval or authorization."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
from types import SimpleNamespace

import pytest

from slaif_raggedized_helper import raw_text_stage_support as s

H = "a" * 64
ID = "sha256:" + H
ORACLE = json.loads(
    (Path(__file__).parents[2] / "docs/parallel/source-bound-text-support-oracle.json").read_text()
)
DATA = ORACLE["concrete_input_vector"]["dataset_ascii"].encode("ascii")


@pytest.fixture
def context(monkeypatch):
    ds = s.datasets.admit(DATA)
    case = ds.cases[0]
    originals = object.__new__(s.OriginalStore)
    derived = object.__new__(s.derived_store.Store)
    owner = s.pin.PinOwner()
    owner.state, owner.op, owner.originals, owner.derived = (
        "ACTIVE",
        SimpleNamespace(path="/owned"),
        originals,
        derived,
    )
    core = json.dumps({"analyzer": {"fingerprint": H}}).encode()
    snap = "sha256:" + hashlib.sha256(core).hexdigest()
    pointer = s.selection.Pointer(b"private-pointer", 1, snap, hashlib.sha256(core).hexdigest())
    captured = s.pin.PinData(pointer, s.files.BoundSnapshotData(snap, core, None, None, ()))
    monkeypatch.setattr(s.selection, "parse_pointer", lambda x: pointer)
    monkeypatch.setattr(s.manifest, "parse", lambda x: SimpleNamespace(snapshot_id=snap))
    calls = []
    monkeypatch.setattr(
        s.pin.PinOwner, "check", lambda self, **kw: calls.append(("pin", kw)) or captured
    )
    grants = s.provenance_records.Grants(
        schema_version=1,
        corpora=case.scope.corpora,
        versions=case.scope.versions,
        labels=case.scope.labels,
    )
    payload = struct.pack("<1024f", 1.0, *([0.0] * 1023))
    kw = dict(
        query_space_id=H,
        query_definition_fingerprint=ID,
        query_policy_id=H,
        query_execution_fingerprint=H,
        grants=grants,
    )

    def search(*args, **kwargs):
        calls.append(("search", args, kwargs))
        authority = s.lexical._authority_hash(kwargs["grants"], kwargs["restrictions"])
        qh, ph = s._digest(case.question.encode()), s._digest(payload)
        qid = s.hybrid._sha(
            s.hybrid._wire(
                dict(
                    kind="raw-hybrid-query/v1",
                    snapshot_id=snap,
                    catalog_id=ID,
                    query_text_sha256=qh,
                    query_payload_sha256=ph,
                    query_space_id=H,
                    query_definition_fingerprint=ID,
                    query_policy_id=H,
                    query_execution_fingerprint=H,
                    authority_sha256=authority,
                    dense_k=60,
                    lexical_k=60,
                    partition_cap=60,
                    k=60,
                )
            )
        )
        common = dict(snapshot_id=snap, catalog_id=ID, authority_sha256=authority)
        dhead = dict(
            **common,
            query_payload_sha256=ph,
            query_space_id=H,
            query_definition_fingerprint=ID,
            query_policy_id=H,
            query_execution_fingerprint=H,
        )
        lhead = dict(
            **common,
            query_text_sha256=qh,
            analyzer_fingerprint=H,
            backend="bm25s-lucene/0.2.14/2.5.4/1.18.1",
            method="lucene",
        )

        def trace_id(head, kind, engine):
            obj = dict(
                schema=1,
                kind=kind,
                **head,
                k=60,
                partition_cap=60,
                rows=[],
                partitions=[],
                selected_ordinals=(),
                returned_ordinals=(),
            )
            return engine._trace_hash(obj, lambda: 1000)

        dt = s.dense.DenseTrace(
            trace_id(dhead, "slaif-raw-dense-authorized-trace-v1", s.dense),
            **dhead,
            k=60,
            partition_cap=60,
            rows=(),
            partitions=(),
            selected_ordinals=(),
            returned_ordinals=(),
        )
        lt = s.lexical.LexicalTrace(
            trace_id(lhead, "slaif-raw-lexical-authorized-trace-v1", s.lexical),
            **lhead,
            k=60,
            partition_cap=60,
            rows=(),
            partitions=(),
            selected_ordinals=(),
            returned_ordinals=(),
        )
        dr = s.dense.DenseResult(
            snap, ID, ph, "SUPPLIED_UNVERIFIED", "NOT_QUALIFIED", (), (), 0, 0, 0, False, False, dt
        )
        lr = s.lexical.LexicalResult(
            snap, ID, qh, H, lhead["backend"], "lucene", (), (), 0, 0, 0, 0, False, False, lt
        )
        fr = s.fusion.FusionResult(
            snap,
            ID,
            qid,
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
            "COMPLETE",
            "COMPLETE",
            False,
            (),
            0,
            0,
            0,
            0,
            0,
            False,
        )
        return s.hybrid.HybridResult(
            snap, ID, qid, qh, ph, authority, "SUPPLIED_UNVERIFIED", "NOT_QUALIFIED", dr, lr, fr
        )

    monkeypatch.setattr(s.hybrid, "search", search)

    def score(*args, **kwargs):
        calls.append(("support", args, kwargs))
        all_atoms = [
            s.support._atom(span)
            for c in ds.cases
            for r in c.requirements
            for alt in r.alternatives
            for span in alt
        ]
        selected = [
            s.support._atom(span)
            for r in case.requirements
            for alt in r.alternatives
            for span in alt
        ]
        records = []
        for k in (20, 60):
            rows = tuple(
                s.coverage.RequirementCoverage(
                    r.requirement_id, (False,) * len(r.alternatives), False
                )
                for r in case.requirements
            )
            records.append(
                s.coverage.CoverageAtK(
                    k,
                    0,
                    (),
                    0.0 if rows else None,
                    False if rows else None,
                    None if rows else "NO_GOLD_REQUIREMENTS",
                    rows,
                )
            )
        return s.support.TextSupport(
            ID,
            ds.dataset_id,
            ds.split_id,
            case.case_id,
            s._digest(DATA),
            ID,
            ID,
            snap,
            ID,
            s.lexical._authority_hash(kwargs["grants"], kwargs["restrictions"]),
            case.answerability,
            len(case.requirements),
            len(selected),
            len(set(selected)),
            len(all_atoms),
            len(set(all_atoms)),
            0,
            0,
            "ORIGINALS_REVALIDATED_AT_BIND_TIME" if all_atoms else "NO_GOLD_SOURCE_VALIDATED",
            "ORIGINAL_GOLD_SPANS_REVALIDATED_AT_CALL_TIME"
            if selected
            else "NO_CASE_GOLD_REQUIREMENTS",
            "NO_SELECTED_SOURCE_VALIDATED",
            ID,
            tuple(records),
        )

    monkeypatch.setattr(s.support, "score_case", score)
    return SimpleNamespace(
        args=(originals, derived, "/owned", owner, DATA, case.case_id, (), payload),
        kw=kw,
        calls=calls,
        case=case,
        monkeypatch=monkeypatch,
    )


def test_owned_calls_and_private_empty_result(context):
    c = context
    result = s.evaluate_case(*c.args, **c.kw)
    calls = [v for v in c.calls if v[0] != "pin"]
    assert [v[0] for v in calls] == ["search", "support", "support", "support"]
    assert calls[0][1][4] == c.case.question
    assert all(call[1][8] == () for call in calls[1:])
    assert all(call[2]["grants"] == calls[0][2]["grants"] for call in calls[1:])
    assert [v.name for v in result.variants] == ["dense", "lexical", "fusion"]
    assert c.case.question not in repr(result)
    assert result.relevance_metrics == "UNSPECIFIED_RELEVANCE_UNIT_MAPPING"
    assert c.args[3].state == "ACTIVE"


@pytest.mark.parametrize(
    "field,value",
    [
        ("deadline_ms", True),
        ("deadline_ms", 0),
        ("query_space_id", "bad"),
        ("query_execution_fingerprint", "sha256:" + H),
    ],
)
def test_preflight_refuses_without_lower_calls(context, field, value):
    context.kw[field] = value
    with pytest.raises(s.StageSupportError, match="^raw text stage support refused$"):
        s.evaluate_case(*context.args, **context.kw)
    assert context.calls == []


def test_base_exception_identity_and_no_retry(context):
    class Stop(BaseException):
        pass

    error = Stop()

    def stop(*args, **kwargs):
        raise error

    context.monkeypatch.setattr(s.hybrid, "search", stop)
    with pytest.raises(Stop) as caught:
        s.evaluate_case(*context.args, **context.kw)
    assert caught.value is error


def test_swapped_support_marker_refused(context):
    original = s.support.score_case
    context.monkeypatch.setattr(
        s.support,
        "score_case",
        lambda *a, **kw: replace(original(*a, **kw), catalog_id="sha256:" + "b" * 64),
    )
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)
    assert len([v for v in context.calls if v[0] == "support"]) == 1


def test_case_scope_narrows_broad_grants_and_preserves_restrictions(context):
    c = context
    c.kw['grants'] = s.provenance_records.Grants(
        schema_version=1, corpora=('demo', 'poison'), versions=('v1.2', 'v2'),
        labels=('private', 'test'))
    c.kw['restrictions'] = s.provenance_records.Restrictions(
        schema_version=1, corpora=(), versions=('v1.2',))
    result = s.evaluate_case(*c.args, **c.kw)
    calls = [v for v in c.calls if v[0] != 'pin']
    authority = calls[0][2]['grants']
    assert (authority.corpora, authority.versions, authority.labels) == (
        ('demo',), ('v1.2',), ('test',))
    assert all(v[2]['restrictions'].corpora == () for v in calls)
    assert result.original_authority_sha256 != result.effective_authority_sha256


def test_empty_intersection_is_not_wildcard(context):
    context.kw['grants'] = s.provenance_records.Grants(
        schema_version=1, corpora=('other',), versions=('other',), labels=())
    s.evaluate_case(*context.args, **context.kw)
    call = next(v for v in context.calls if v[0] == 'search')
    grants = call[2]['grants']
    assert (grants.corpora, grants.versions, grants.labels) == ((), (), ())


def test_distinct_geometry_and_binding_ids_allowed(context):
    original = s.support.score_case
    counter = iter('bcd')
    def score(*args, **kwargs):
        item = original(*args, **kwargs)
        ident = 'sha256:' + next(counter) * 64
        return replace(item, geometry_fingerprint=ident,
                       ranking_binding_id=ident, evaluation_id=ident)
    context.monkeypatch.setattr(s.support, 'score_case', score)
    result = s.evaluate_case(*context.args, **context.kw)
    assert len({v.support.geometry_fingerprint for v in result.variants}) == 3


@pytest.mark.parametrize('field,value', [
    ('gold_binding_id', 'sha256:' + 'b' * 64),
    ('case_requirement_count', 0),
    ('global_gold_atom_occurrences', 0),
    ('authority_sha256', 'b' * 64),
    ('ranking_count', 1),
])
def test_support_mismatch_refuses(context, field, value):
    original = s.support.score_case
    count = [0]
    def score(*args, **kwargs):
        count[0] += 1
        item = original(*args, **kwargs)
        return replace(item, **{field: value}) if count[0] == 2 else item
    context.monkeypatch.setattr(s.support, 'score_case', score)
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)
    assert count[0] == 2


@pytest.mark.parametrize('field,value', [
    ('query_id', 'b' * 64), ('query_text_sha256', 'b' * 64),
    ('catalog_id', 'sha256:' + 'b' * 64), ('authority_sha256', 'b' * 64),
    ('qualification', 'QUALIFIED'),
])
def test_producer_mismatch_refuses_before_support(context, field, value):
    original = s.hybrid.search
    def swapped(*args, **kwargs):
        return replace(original(*args, **kwargs), **{field: value})
    context.monkeypatch.setattr(s.hybrid, 'search', swapped)
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)
    assert not any(v[0] == 'support' for v in context.calls)


def test_late_producer_refuses_and_does_not_retry(context):
    now = [1.0]
    context.monkeypatch.setattr(s.time, 'monotonic', lambda: now[0])
    original = s.hybrid.search
    def late(*args, **kwargs):
        result = original(*args, **kwargs)
        now[0] += 2
        return result
    context.monkeypatch.setattr(s.hybrid, 'search', late)
    context.kw['deadline_ms'] = 1000
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)
    assert len([v for v in context.calls if v[0] == 'search']) == 1
    assert not any(v[0] == 'support' for v in context.calls)


def test_rank_identity_rejects_duplicate_and_noncontiguous_rank():
    hit = s.dense.Hit(0, ID, ID, ID, H, b'private', b'private', 1, 1.0)
    assert s._rank((hit,), s.dense.Hit, lambda: 1)[0][0] == 0
    with pytest.raises(ValueError):
        s._rank((hit, replace(hit, rank=2)), s.dense.Hit, lambda: 1)
    with pytest.raises(ValueError):
        s._rank((replace(hit, rank=2),), s.dense.Hit, lambda: 1)


def test_changed_pin_refuses_before_producer(context):
    original = s.pin.PinOwner.check
    count = [0]
    def changed(self, **kw):
        count[0] += 1
        captured = original(self, **kw)
        if count[0] == 1:
            return captured
        return replace(captured, pointer=replace(captured.pointer, generation=2))
    context.monkeypatch.setattr(s.pin.PinOwner, 'check', changed)
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)
    assert not any(v[0] == 'search' for v in context.calls)


def test_failure_is_content_free_without_retry(context):
    def fail(*args, **kwargs):
        raise ValueError('private content')
    context.monkeypatch.setattr(s.hybrid, 'search', fail)
    with pytest.raises(s.StageSupportError) as caught:
        s.evaluate_case(*context.args, **context.kw)
    assert str(caught.value) == 'raw text stage support refused'
    assert caught.value.__suppress_context__
    assert not any(v[0] == 'support' for v in context.calls)


def test_three_nonempty_owned_rankings_and_trace_linkage(context):
    """Boundary doubles supply distinct real-shaped rankings, never source truth."""
    from dataclasses import asdict

    original_search = s.hybrid.search
    original_score = s.support.score_case
    chunks = tuple('sha256:' + c * 64 for c in 'bcd')
    revisions = tuple('sha256:' + c * 64 for c in '123')
    reps = tuple(c * 64 for c in '123')
    partition = 'sha256:' + 'f' * 64

    def nonempty(*args, **kwargs):
        result = original_search(*args, **kwargs)
        dense_rows = tuple(s.dense.DenseTraceRow(i, partition, chunks[i], revisions[i], reps[i])
                           for i in range(3))
        lexical_rows = tuple(
            s.lexical.LexicalTraceRow(i, partition, chunks[i], revisions[i], reps[i])
            for i in range(3))

        def traced(old, engine, rows, ranked):
            part_cls = (s.dense.DensePartitionTrace if engine is s.dense
                        else s.lexical.LexicalPartitionTrace)
            part = part_cls(partition, (0, 1, 2), ranked, ranked, ranked)
            trace = replace(old, rows=rows, partitions=(part,), selected_ordinals=ranked,
                            returned_ordinals=ranked)
            excluded = {'trace_id', 'k', 'partition_cap', 'rows', 'partitions',
                        'selected_ordinals', 'returned_ordinals', 'input_origin',
                        'qualification', 'authorization_status', 'execution_status'}
            header = {k: v for k, v in asdict(trace).items() if k not in excluded}
            kind = ('slaif-raw-dense-authorized-trace-v1' if engine is s.dense
                    else 'slaif-raw-lexical-authorized-trace-v1')
            preimage = dict(schema=1, kind=kind, **header, k=60, partition_cap=60,
                            rows=[asdict(r) for r in rows], partitions=[asdict(part)],
                            selected_ordinals=ranked, returned_ordinals=ranked)
            return replace(trace, trace_id=engine._trace_hash(preimage, lambda: 1000))

        dense_hits = tuple(s.dense.Hit(i, partition, chunks[i], revisions[i], reps[i],
                                      b'private scope', b'private source', i + 1, 1.0)
                           for i in range(3))
        lexical_hits = tuple(s.lexical.Hit(i, partition, chunks[i], revisions[i], reps[i],
                                          b'private scope', b'private source', 1.0, rank)
                             for rank, i in enumerate((2, 1, 0), 1))
        dr = replace(result.dense, hits=dense_hits,
                     allowed_partition_counts=(s.dense.PartitionCount(partition, 3, 3, 3),),
                     eligible=3, selected=3, returned=3,
                     trace=traced(result.dense.trace, s.dense, dense_rows, (0, 1, 2)))
        lr = replace(result.lexical, hits=lexical_hits,
                     partitions=(s.lexical.PartitionCount(partition, 3, 3, 3, 3),),
                     eligible=3, matching=3, selected=3, returned=3,
                     trace=traced(result.lexical.trace, s.lexical, lexical_rows, (2, 1, 0)))
        fusion_order = (0, 2, 1)
        fused_hits = tuple(
            s.fusion.Hit(i, partition, chunks[i], revisions[i], reps[i], b'private scope',
                         b'private source', i + 1, 3 - i,
                         1 / (61 + i) + 1 / (63 - i), rank)
            for rank, i in enumerate(fusion_order, 1))
        fr = replace(result.fusion, hits=fused_hits, dense_input_rows=3, lexical_input_rows=3,
                     unique_candidates=3, overlap_candidates=3, returned=3)
        return replace(result, dense=dr, lexical=lr, fusion=fr)

    def score(*args, **kwargs):
        item = original_score(*args, **kwargs)
        records = tuple(replace(record, returned_count=3) for record in item.at_k)
        return replace(item, ranking_count=3,
                       ranking_source_status='ORIGINALS_REVALIDATED_AT_BIND_TIME', at_k=records)

    context.monkeypatch.setattr(s.hybrid, 'search', nonempty)
    context.monkeypatch.setattr(s.support, 'score_case', score)
    output = s.evaluate_case(*context.args, **context.kw)
    calls = [v for v in context.calls if v[0] == 'support']
    assert [v[1][8] for v in calls] == [chunks, chunks[::-1], (chunks[0], chunks[2], chunks[1])]
    assert len({v.ranking_hash for v in output.variants}) == 3
    assert all(v.returned == 3 for v in output.variants)
    assert 'private source' not in repr(output)


def test_trace_authority_poison_refused_before_support(context):
    original = s.hybrid.search
    def poisoned(*args, **kwargs):
        result = original(*args, **kwargs)
        trace = replace(result.dense.trace, authority_sha256='b' * 64)
        return replace(result, dense=replace(result.dense, trace=trace))
    context.monkeypatch.setattr(s.hybrid, 'search', poisoned)
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)
    assert not any(v[0] == 'support' for v in context.calls)


def test_no_gold_coverage_is_undefined(context):
    output = s.evaluate_case(*context.args, **context.kw)
    item = output.variants[0].support
    case = replace(context.case, requirements=())
    empty = tuple(s.coverage.CoverageAtK(k, 0, (), None, None, 'NO_GOLD_REQUIREMENTS', ())
                  for k in (20, 60))
    item = replace(item, case_requirement_count=0, case_gold_atom_occurrences=0,
                   case_distinct_gold_atoms=0, case_gold_source_status='NO_CASE_GOLD_REQUIREMENTS',
                   at_k=empty)
    dataset = s.datasets.admit(DATA)
    atoms = (0, 0, item.global_gold_atom_occurrences, item.global_distinct_gold_atoms)
    s._support_check(item, dataset, case, s._digest(DATA), item.snapshot_id, item.catalog_id,
                     item.authority_sha256, 0, atoms, lambda: 1)
    assert all(record.requirement_fraction is None for record in item.at_k)


def test_late_second_support_refuses_whole_invocation(context):
    now = [1.0]
    context.monkeypatch.setattr(s.time, 'monotonic', lambda: now[0])
    original = s.support.score_case
    count = [0]
    def late(*args, **kwargs):
        count[0] += 1
        item = original(*args, **kwargs)
        if count[0] == 2:
            now[0] += 2
        return item
    context.monkeypatch.setattr(s.support, 'score_case', late)
    context.kw['deadline_ms'] = 1000
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)
    assert count[0] == 2


@pytest.mark.parametrize('field,value', [
    ('ranking_count', False), ('case_requirement_count', True),
    ('case_gold_atom_occurrences', True), ('case_distinct_gold_atoms', False),
    ('global_gold_atom_occurrences', True), ('global_distinct_gold_atoms', False),
])
def test_support_count_types_are_exact(context, field, value):
    original = s.support.score_case
    def forged(*args, **kwargs):
        return replace(original(*args, **kwargs), **{field: value})
    context.monkeypatch.setattr(s.support, 'score_case', forged)
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)


@pytest.mark.parametrize('value', [False, 0, float('nan'), -0.1, 1.1])
def test_coverage_fraction_requires_bounded_float(context, value):
    original = s.support.score_case
    def forged(*args, **kwargs):
        item = original(*args, **kwargs)
        return replace(item, at_k=(replace(item.at_k[0], requirement_fraction=value), item.at_k[1]))
    context.monkeypatch.setattr(s.support, 'score_case', forged)
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)


def test_rank_identity_checked_before_hashing():
    class Poison:
        def __hash__(self):
            raise AssertionError('must not hash malformed identity')
    hit = s.dense.Hit(0, ID, Poison(), ID, H, b'', b'', 1, 1.0)
    with pytest.raises(ValueError):
        s._rank((hit,), s.dense.Hit, lambda: 1)
    assert not s._hex('a' * 100000)


def test_output_fields_do_not_expose_private_inputs(context):
    from dataclasses import asdict
    output = s.evaluate_case(*context.args, **context.kw)
    wire = json.dumps(asdict(output))
    for secret in (context.case.question, 'Synthetic expected fact.',
                   'Synthetic unsupported claim.', '/owned', 'private-pointer'):
        assert secret not in wire
    assert 'hits' not in wire and 'trace' not in asdict(output)
    assert output.execution_status == 'NOT_ATTESTED'
    assert output.qualification == 'NOT_QUALIFIED'


def test_support_instance_cannot_be_reused(context):
    original = s.support.score_case
    first = []
    def reused(*args, **kwargs):
        if not first:
            first.append(original(*args, **kwargs))
        return first[0]
    context.monkeypatch.setattr(s.support, 'score_case', reused)
    with pytest.raises(s.StageSupportError):
        s.evaluate_case(*context.args, **context.kw)


@pytest.mark.parametrize("root", ["/" + "a" * 4096, type("Root", (str,), {
    "encode": lambda self, *args, **kwargs: (_ for _ in ()).throw(SystemExit())
})("/owned")], ids=["oversized-root", "str-subclass"])
def test_root_guard_precedes_path_and_producers(context, root):
    def stop(*args, **kwargs):
        raise SystemExit("unexpected lower call")

    context.monkeypatch.setattr(s.publication, "_path_check", stop)
    context.monkeypatch.setattr(s.datasets, "admit", stop)
    context.monkeypatch.setattr(s, "_digest", stop)
    context.monkeypatch.setattr(s.hybrid, "search", stop)
    args = list(context.args)
    args[2] = root
    with pytest.raises(s.StageSupportError, match="^raw text stage support refused$"):
        s.evaluate_case(*args, **context.kw)
    assert context.calls == []
