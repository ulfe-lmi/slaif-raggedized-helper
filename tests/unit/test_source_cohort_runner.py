"""Controlled cohort runner tests: no source, native, worker or model calls."""

import dataclasses
import hashlib
import json
import struct
from pathlib import Path
from types import SimpleNamespace

import pytest

import test_declared_stage_geometry as oracle
import test_raw_snapshot_manifest as manifest_fixture
import test_raw_snapshot_rows as rows_fixture
from slaif_raggedized_helper import declared_cohort_metrics as pure
from slaif_raggedized_helper import declared_span_support as span
from slaif_raggedized_helper import declared_stage_geometry as geometry
from slaif_raggedized_helper import derived_store, provenance_records as provenance
from slaif_raggedized_helper import raw_dense_search as dense
from slaif_raggedized_helper import raw_hybrid_search as hybrid
from slaif_raggedized_helper import raw_lexical_search as lexical
from slaif_raggedized_helper import raw_rank_fusion as fusion
from slaif_raggedized_helper import raw_snapshot_files, raw_snapshot_pin, raw_snapshot_rows
from slaif_raggedized_helper import raw_snapshot_selection, source_bound_stage_loss as binder
from slaif_raggedized_helper import source_cohort_runner as runner
from slaif_raggedized_helper import text_evaluation_dataset as dataset_module
from slaif_raggedized_helper.source_admission import OriginalStore


def test_module_origins_are_assigned_worktree():
    root = Path(__file__).resolve().parents[2]
    for module, relative in (
        (runner, "src/slaif_raggedized_helper/source_cohort_runner.py"),
        (geometry, "src/slaif_raggedized_helper/declared_stage_geometry.py"),
        (pure, "src/slaif_raggedized_helper/declared_cohort_metrics.py"),
        (binder, "src/slaif_raggedized_helper/source_bound_stage_loss.py"),
        (oracle, "tests/unit/test_declared_stage_geometry.py"),
        (rows_fixture, "tests/unit/test_raw_snapshot_rows.py"),
        (manifest_fixture, "tests/unit/test_raw_snapshot_manifest.py"),
    ):
        assert Path(module.__file__).resolve() == root / relative


class ForbiddenBoundary(BaseException):
    pass


@pytest.fixture(autouse=True)
def forbid_uncontrolled_source_boundaries(monkeypatch):
    def forbidden(*args, **kwargs):
        raise ForbiddenBoundary()

    for name in ("_owner_check", "_produce", "_bind"):
        monkeypatch.setattr(runner, name, forbidden)


def wire(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def budget():
    return runner.Budget(*runner._MAX_BUDGET)


def make_data(count=1, gold=False):
    obj = json.loads(oracle.data())
    template = obj["cases"][0]
    obj["cases"] = []
    for i in range(count):
        case = json.loads(json.dumps(template))
        case["case_id"] = f"case{i:03}"
        case["family_id"] = f"family{i:03}"
        case["question"] = f"Synthetic question {i}?"
        if not gold:
            case["requirements"] = []
            case["answerability"] = "unknown"
            case["acceptable_facts"] = []
        obj["cases"].append(case)
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def controlled(monkeypatch, count=1, *, mixed=False):
    if mixed:
        obj = json.loads(make_data(3))
        for case in obj["cases"][:2]:
            case["split"] = "held_out"
        obj["cases"][2]["split"] = "tuning"
        for index, revisions in ((0, (10, 11)), (2, (20,))):
            case = obj["cases"][index]
            case["answerability"] = "answerable"
            case["acceptable_facts"] = ["Synthetic supported fact"]
            case["requirements"] = [{
                "requirement_id": "R1", "grade": 1,
                "alternatives": [[oracle.atom(rev, "A", 1) for rev in revisions]],
            }]
        data = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    else:
        data = make_data(count)
    dataset = dataset_module.admit(data)
    case = dataset.cases[0]
    effective = provenance.Grants(
        schema_version=1, corpora=case.scope.corpora,
        versions=case.scope.versions, labels=case.scope.labels,
    )
    grants = provenance.Grants(
        schema_version=1,
        corpora=tuple(sorted(set(effective.corpora + (("extra-corpus",) if mixed else ())))),
        versions=tuple(sorted(set(effective.versions + (("extra-version",) if mixed else ())))),
        labels=tuple(sorted(set(effective.labels + (("extra-label",) if mixed else ())))),
    )
    restrictions = (
        provenance.Restrictions(schema_version=1, corpora=None, versions=None) if mixed else None
    )
    gold_ids = ("a" * 64, "b" * 64) if mixed else ()
    mapping = rows_fixture.mapping()
    row_map = raw_snapshot_rows.parse(rows_fixture.enc(mapping))
    core = b"controlled core"
    snapshot = "sha256:" + digest(core)
    pointer = raw_snapshot_selection.parse_pointer(
        wire(
            {
                "schema": 1,
                "kind": "raw-snapshot-selection-data-v1",
                "generation": 1,
                "snapshot_id": snapshot,
                "core_sha256": snapshot[7:],
            }
        )
    )
    captured = raw_snapshot_pin.PinData(
        pointer, raw_snapshot_files.BoundSnapshotData(snapshot, core, row_map, None, ())
    )
    originals = object.__new__(OriginalStore)
    derived = object.__new__(derived_store.Store)
    owner = object.__new__(raw_snapshot_pin.PinOwner)
    owner.state, owner.originals, owner.derived = "ACTIVE", originals, derived
    owner.op, owner.value = SimpleNamespace(path="/fixture"), captured
    payload = struct.pack("<1024f", 1.0, *([0.0] * 1023))
    ids = ("a" * 64, "sha256:" + "a" * 64, "a" * 64, "a" * 64)
    selected_cases = tuple(c for c in dataset.cases if c.split == case.split)
    queries = tuple(runner.Query(c.case_id, payload, *ids) for c in selected_cases)
    selected = runner.Cohort(case.split, tuple(c.case_id for c in selected_cases))
    calls = []
    marker = "sha256:" + "b" * 64
    catalog_id = "sha256:" + "c" * 64

    # Genuine closed lower DTOs supplied without running a geometry scorer.
    def stage(name, cutoff):
        coverage = span.CoverageAtK(cutoff, 0, (), None, None, "NO_GOLD_REQUIREMENTS", ())
        completion = geometry.Completion((), (), (), (), None, "NO_GOLD_SOURCES")
        return geometry.Stage(name, cutoff, 0, coverage, completion, marker)

    stages = tuple(stage(name, 1) for name in geometry._NAMES)
    prefixes = tuple(
        stage(geometry._NAMES[i], k)
        for i, k in ((3, 20), (3, 60), (7, 20), (7, 60), (9, 20), (9, 60))
    )
    transitions = tuple(
        geometry.Transition(geometry._NAMES[a], geometry._NAMES[b], (), (), (), ())
        for a, b in ((0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (8, 9))
    )
    shape = geometry.Diagnosis(marker, stages, prefixes, transitions, 1, 1)
    if mixed:
        atoms = ("sha256:" + "1" * 64, "sha256:" + "2" * 64)
        revisions = (oracle.ident(10), oracle.ident(11))
        def gold_stage(name, cutoff):
            req = span.RequirementCoverage("R1", (True,), True)
            coverage = span.CoverageAtK(cutoff, 2, ("R1",), 1.0, True, None, (req,))
            completion = geometry.Completion(
                tuple((atom, True) for atom in atoms),
                (("R1", 0, 0, atoms[0]), ("R1", 0, 1, atoms[1])),
                revisions, revisions, 1.0, None)
            return geometry.Stage(name, cutoff, 2, coverage, completion, marker)
        gold_shape = geometry.Diagnosis(
            marker, tuple(gold_stage(name, 2) for name in geometry._NAMES),
            tuple(gold_stage(geometry._NAMES[i], k) for i, k in
                  ((3, 20), (3, 60), (7, 20), (7, 60), (9, 20), (9, 60))),
            transitions, 1, 1)

    def check_pin(value, **kwargs):
        calls.append("pin")
        assert value is owner
        return captured

    def produce(_originals, _derived, _root, snap, question, value, **kwargs):
        calls.append("producer")
        assert kwargs["trace"] is True and kwargs["grants"] == effective
        assert kwargs["restrictions"] == restrictions
        assert (kwargs["dense_k"], kwargs["lexical_k"], kwargs["partition_cap"], kwargs["k"]) == (
            60,
            60,
            60,
            60,
        )
        text_sha, payload_sha = digest(question.encode()), digest(value)
        restriction_data = None if restrictions is None else restrictions.model_dump(mode="json")
        authority = digest(wire([kwargs["grants"].model_dump(mode="json"), restriction_data]))
        query_id = digest(
            wire(
                dict(
                    kind="raw-hybrid-query/v1",
                    snapshot_id=snap,
                    catalog_id=catalog_id,
                    query_text_sha256=text_sha,
                    query_payload_sha256=payload_sha,
                    query_space_id=ids[0],
                    query_definition_fingerprint=ids[1],
                    query_policy_id=ids[2],
                    query_execution_fingerprint=ids[3],
                    authority_sha256=authority,
                    dense_k=60,
                    lexical_k=60,
                    partition_cap=60,
                    k=60,
                )
            )
        )
        dt = dense.DenseTrace(
            marker, snap, catalog_id, payload_sha, *ids, authority, 60, 60, (), (), (), ()
        )
        lt = lexical.LexicalTrace(
            marker,
            snap,
            catalog_id,
            text_sha,
            "a" * 64,
            "backend",
            "method",
            authority,
            60,
            60,
            (),
            (),
            (),
            (),
        )
        dr = dense.DenseResult(
            snap,
            catalog_id,
            payload_sha,
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
            (),
            (),
            0,
            0,
            0,
            False,
            False,
            dt,
        )
        lr = lexical.LexicalResult(
            snap,
            catalog_id,
            text_sha,
            "a" * 64,
            "backend",
            "method",
            (),
            (),
            0,
            0,
            0,
            0,
            False,
            False,
            lt,
        )
        fr = fusion.FusionResult(
            snap,
            catalog_id,
            query_id,
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
        return hybrid.HybridResult(
            snap,
            catalog_id,
            query_id,
            text_sha,
            payload_sha,
            authority,
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
            dr,
            lr,
            fr,
        )

    def bind(_originals, _derived, _root, pin, full_data, case_id, gold, result, value, **kwargs):
        calls.append("binder")
        assert pin is owner and full_data == data and gold == gold_ids
        assert kwargs["grants"] == grants
        assert kwargs["restrictions"] == restrictions
        restriction_data = None if restrictions is None else restrictions.model_dump(mode="json")
        original = digest(wire([grants.model_dump(mode="json"), restriction_data]))
        filter_id = "sha256:" + digest(
            b"slaif-stage-filter-v1\n"
            + wire(
                {
                    "original_authority": original,
                    "case_id": case_id,
                    "policy": "case-scope-intersection-v1",
                }
            )
        )
        return binder._Diagnosis(
            marker,
            dataset.dataset_id,
            dataset.split_id,
            case_id,
            result.query_text_sha256,
            result.query_payload_sha256,
            result.authority_sha256,
            original,
            filter_id,
            digest(pointer.pointer_bytes),
            1,
            snapshot,
            catalog_id,
            result.query_id,
            marker,
            marker,
            marker,
            marker,
            marker,
            dataset.case_count,
            dataset.gold_atom_count,
            2 if mixed and case_id == "case000" else 0,
            2 if mixed and case_id == "case000" else 0,
            gold_shape if mixed and case_id == "case000" else shape,
            (5888, 6400, 12288, 4986555627809),
            1,
            1,
            2,
            2,
            (),
            (),
        )

    monkeypatch.setattr(runner, "_owner_check", check_pin)
    monkeypatch.setattr(runner, "_produce", produce)
    monkeypatch.setattr(runner, "_bind", bind)
    args = (originals, derived, "/fixture", owner, data, selected, queries, gold_ids)
    kwargs = dict(
        grants=grants,
        restrictions=restrictions,
        config=runner.Config("cfg", "declaration"),
        budget=budget(),
        deadline_ms=120000,
    )
    return args, kwargs, calls, captured


def test_success_and_private_report(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch)
    report = runner.run_cohort(*args, **kwargs)
    assert calls == ["pin", "pin", "producer", "binder"]
    payload = json.loads(report.identity_payload)
    assert payload["selection_kind"] == "FULL_ADMITTED_SPLIT"
    assert payload["progress"] == dict(intended=1, attempted=1, completed=1, refused=0, pending=0)
    assert payload["ledger"]["dataset_internal"] == "UNMEASURED_BY_RUNNER"
    assert payload["ledger"]["binder_geometry"] == "OVERLAPPING_NOT_ADDITIVE"
    assert report.identity == "sha256:" + digest(
        b"slaif-source-cohort-runner-v1\n" + report.identity_payload
    )
    assert (
        b"Synthetic question" not in report.identity_payload
        and args[6][0].payload not in report.identity_payload
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.identity = "changed"


def test_source_reservation_hand_arithmetic():
    assert runner._source_reservation(1) == (29, 15872, 17664, 13608640472407)
    assert runner._source_reservation(256) == (7169, 3965312, 4391424, 3391111408059907)


def test_admission_failure_has_no_progress_and_no_source(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch)
    args = (*args[:6], (), args[7])
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    assert exc.value.progress is None and calls == []
    assert str(exc.value) == "cohort runner refused"


@pytest.mark.parametrize(
    "phase,which", [("CASE_PIN", "_owner_check"), ("PRODUCER", "_produce"), ("BINDER", "_bind")]
)
def test_failure_prefix_and_no_aggregate(monkeypatch, phase, which):
    args, kwargs, calls, _ = controlled(monkeypatch)
    delegate = getattr(runner, which)

    def fail(*a, **kw):
        if which != "_owner_check" or calls:
            raise ValueError("private input")
        return delegate(*a, **kw)

    monkeypatch.setattr(runner, which, fail)
    monkeypatch.setattr(runner, "_aggregate", lambda *a, **kw: pytest.fail("unexpected aggregate"))
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    p = exc.value.progress
    assert (p.phase, p.intended, p.attempted, p.completed, p.refused, p.pending) == (
        phase,
        1,
        1,
        0,
        1,
        0,
    )
    assert "private input" not in str(exc.value)


def test_baseexception_identity(monkeypatch):
    args, kwargs, _, _ = controlled(monkeypatch)
    error = KeyboardInterrupt()

    def interrupt(*args, **kwargs):
        raise error

    monkeypatch.setattr(runner, "_produce", interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        runner.run_cohort(*args, **kwargs)
    assert caught.value is error


def test_full_256_and_257_preflight(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch, 256)
    result = runner.run_cohort(*args, **kwargs)
    assert json.loads(result.identity_payload)["selected_count"] == 256
    assert calls.count("producer") == calls.count("binder") == 256
    args257 = (*args[:4], make_data(257), *args[5:])
    calls.clear()
    with pytest.raises(runner.CohortRunnerError):
        runner.run_cohort(*args257, **kwargs)
    assert not calls


def test_declared_subset_and_query_mismatch(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch, 3)
    subset = runner.Cohort(args[5].split, (args[5].case_ids[1],))
    one = (*args[:5], subset, (args[6][1],), args[7])
    result = runner.run_cohort(*one, **kwargs)
    assert json.loads(result.identity_payload)["selection_kind"] == "DECLARED_SUBSET"
    calls.clear()
    bad = (*one[:6], (args[6][0],), one[7])
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*bad, **kwargs)
    assert exc.value.progress is None and not calls


@pytest.mark.parametrize("index", [0, 1, 2])
def test_whole_cohort_fails_at_each_position(monkeypatch, index):
    args, kwargs, calls, _ = controlled(monkeypatch, 3)
    original = runner._produce
    seen = []

    def fail_at(*a, **kw):
        seen.append(1)
        if len(seen) == index + 1:
            raise ValueError
        return original(*a, **kw)

    monkeypatch.setattr(runner, "_produce", fail_at)
    monkeypatch.setattr(
        runner, "_aggregate", lambda *a, **kw: pytest.fail("aggregate after refusal")
    )
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    p = exc.value.progress
    assert (p.phase, p.attempted, p.completed, p.refused, p.pending) == (
        "PRODUCER",
        index + 1,
        index,
        1,
        2 - index,
    )
    assert calls.count("binder") == index


def test_pin_mismatch_is_preflight_refusal(monkeypatch):
    args, kwargs, calls, captured = controlled(monkeypatch)
    args[3].value = dataclasses.replace(captured)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    p = exc.value.progress
    assert (p.phase, p.attempted, p.refused, p.pending) == ("PREFLIGHT", 0, 0, 1)
    assert calls == ["pin"]


def test_precharge_refuses_before_dataset_and_source(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch)
    kwargs["budget"] = dataclasses.replace(kwargs["budget"], local_work=0)
    monkeypatch.setattr(
        runner, "_admit_dataset", lambda *a, **kw: pytest.fail("unreserved dataset")
    )
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    assert exc.value.progress is None and not calls


def test_aggregate_failure_has_completed_counts(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch, 2)

    def fail(*args, **kwargs):
        raise ValueError

    monkeypatch.setattr(runner, "_aggregate", fail)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    p = exc.value.progress
    assert (p.phase, p.attempted, p.completed, p.refused, p.pending) == ("AGGREGATE", 2, 2, 0, 0)
    assert calls.count("binder") == 2


def test_global_gold_limit_refuses_before_source(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch)
    data = make_data(171, gold=True)
    args = (*args[:4], data, *args[5:])
    with pytest.raises(runner.CohortRunnerError):
        runner.run_cohort(*args, **kwargs)
    assert not calls


def test_dataset_called_with_deadline_only(monkeypatch):
    args, kwargs, _, _ = controlled(monkeypatch)
    delegate = runner._admit_dataset
    seen = []

    def admit(value, **options):
        seen.append(options)
        return delegate(value, **options)

    monkeypatch.setattr(runner, "_admit_dataset", admit)
    runner.run_cohort(*args, **kwargs)
    assert len(seen) == 1 and set(seen[0]) == {"deadline_ms"}
    assert 1 <= seen[0]["deadline_ms"] <= 5000


def test_invalid_deadline_and_source_cap(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch)
    kwargs["deadline_ms"] = 0
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    assert exc.value.progress is None and not calls
    kwargs["deadline_ms"] = 120000
    kwargs["budget"] = dataclasses.replace(kwargs["budget"], source_directories=28)
    with pytest.raises(runner.CohortRunnerError):
        runner.run_cohort(*args, **kwargs)
    assert not calls


def test_nonnormalized_ratio_rejected(monkeypatch):
    from slaif_raggedized_helper import declared_cohort_metrics as pure

    args, kwargs, _, _ = controlled(monkeypatch)
    delegate = runner._aggregate

    def malformed(*args, **kwargs):
        report = delegate(*args, **kwargs)
        ratio = pure.Ratio(1, 1)
        object.__setattr__(ratio, "numerator", 2)
        object.__setattr__(ratio, "denominator", 2)
        prefix = dataclasses.replace(report.prefixes[0], source_macro=ratio)
        return dataclasses.replace(report, prefixes=(prefix, *report.prefixes[1:]))

    monkeypatch.setattr(runner, "_aggregate", malformed)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    assert exc.value.progress.phase == "SERIALIZE"


class CountSubclass(int):
    pass


@pytest.mark.parametrize(
    "field,malformed",
    [
        ("dataset_case_count", value) for value in (True, 1.0, CountSubclass(1), 257)
    ]
    + [
        (field, value)
        for field in ("dataset_atom_occurrences", "chosen_atom_occurrences")
        for value in (False, 0.0, CountSubclass(0), -1, 513)
    ],
)
def test_malformed_binder_count_refused_before_aggregate(monkeypatch, field, malformed):
    args, kwargs, calls, _ = controlled(monkeypatch)
    bind = runner._bind

    def corrupt(*a, **kw):
        diagnosis = bind(*a, **kw)
        assert type(diagnosis) is binder._Diagnosis
        return dataclasses.replace(diagnosis, **{field: malformed})

    def forbidden(*a, **kw):
        raise ForbiddenBoundary()

    monkeypatch.setattr(runner, "_bind", corrupt)
    monkeypatch.setattr(runner, "_aggregate", forbidden)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    p = exc.value.progress
    assert (p.phase, p.intended, p.attempted, p.completed, p.refused, p.pending) == (
        "BINDER", 1, 1, 0, 1, 0
    )
    assert str(exc.value) == "cohort runner refused"
    assert calls == ["pin", "pin", "producer", "binder"]


@pytest.mark.parametrize("malformed", [True, 1.0, CountSubclass(1), 0, 257])
def test_malformed_pure_case_count_refused_after_one_aggregate(monkeypatch, malformed):
    args, kwargs, calls, _ = controlled(monkeypatch)
    aggregate = runner._aggregate
    results = []

    def corrupt(*a, **kw):
        report = aggregate(*a, **kw)
        assert type(report) is pure.Report and report.case_count == 1
        results.append(report)
        return dataclasses.replace(report, case_count=malformed)

    monkeypatch.setattr(runner, "_aggregate", corrupt)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    p = exc.value.progress
    assert (p.phase, p.intended, p.attempted, p.completed, p.refused, p.pending) == (
        "SERIALIZE", 1, 1, 1, 0, 0
    )
    assert str(exc.value) == "cohort runner refused"
    assert len(results) == 1 and calls == ["pin", "pin", "producer", "binder"]


def test_wrong_split_and_extra_query_refuse(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch)
    other = "held_out" if args[5].split == "tuning" else "tuning"
    bad_split = (*args[:5], runner.Cohort(other, args[5].case_ids), *args[6:])
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*bad_split, **kwargs)
    assert exc.value.progress is None and calls == []
    extra = (*args[:6], args[6] + args[6], args[7])
    with pytest.raises(runner.CohortRunnerError):
        runner.run_cohort(*extra, **kwargs)
    assert calls == []


def test_bad_query_vector_and_extra_fields_refuse(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch)
    query = dataclasses.replace(args[6][0], payload=b"\0" * 4096)
    with pytest.raises(runner.CohortRunnerError):
        runner.run_cohort(*args[:6], (query,), args[7], **kwargs)
    assert calls == []
    query = dataclasses.replace(args[6][0])
    object.__setattr__(query, "unexpected", "private")
    with pytest.raises(runner.CohortRunnerError):
        runner.run_cohort(*args[:6], (query,), args[7], **kwargs)
    assert calls == []


def test_original_and_effective_authority_are_independent(monkeypatch):
    import time

    args, kwargs, _, _ = controlled(monkeypatch)
    original = kwargs["grants"]
    expanded = provenance.Grants(
        schema_version=1,
        corpora=tuple(sorted(set(original.corpora + ("extra-corpus",)))),
        versions=tuple(sorted(set(original.versions + ("extra-version",)))),
        labels=tuple(sorted(set(original.labels + ("extra-label",)))),
    )
    restrictions = provenance.Restrictions(
        schema_version=1, corpora=("extra-corpus",), versions=None
    )
    _, selected, _, _ = runner._input_admission(
        *args,
        expanded,
        restrictions,
        kwargs["config"],
        kwargs["budget"],
        runner._Deadline(time.monotonic(), 120000),
    )
    _, saved, effective, saved_restrictions = selected[0]
    assert saved == expanded and saved is not expanded
    assert effective == original and saved_restrictions == restrictions


def test_pin_core_and_map_substitution_refused(monkeypatch):
    args, kwargs, calls, captured = controlled(monkeypatch)
    broken = dataclasses.replace(
        captured, data=dataclasses.replace(captured.data, core_bytes=b"bad")
    )
    args[3].value = broken
    monkeypatch.setattr(runner, "_owner_check", lambda *a, **kw: broken)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    assert exc.value.progress.phase == "PREFLIGHT"
    assert "producer" not in calls


def test_malformed_pure_identity_refused(monkeypatch):
    args, kwargs, _, _ = controlled(monkeypatch)
    aggregate = runner._aggregate

    def corrupt(*a, **kw):
        return dataclasses.replace(aggregate(*a, **kw), identity="sha256:" + "0" * 64)

    monkeypatch.setattr(runner, "_aggregate", corrupt)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    assert exc.value.progress.phase == "SERIALIZE"


def test_empty_scope_stays_empty(monkeypatch):
    import time

    args, kwargs, _, _ = controlled(monkeypatch)
    obj = json.loads(args[4])
    obj["cases"][0]["scope"] = {"corpora": [], "versions": [], "labels": []}
    data = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    revised = (*args[:4], data, *args[5:])
    _, selected, _, _ = runner._input_admission(
        *revised,
        kwargs["grants"],
        None,
        kwargs["config"],
        kwargs["budget"],
        runner._Deadline(time.monotonic(), 120000),
    )
    assert selected[0][2].corpora == selected[0][2].versions == selected[0][2].labels == ()


@pytest.mark.parametrize("field", ["state", "originals", "derived", "op"])
def test_owner_association_refusal_precedes_delegation(monkeypatch, field):
    args, kwargs, calls, _ = controlled(monkeypatch)
    setattr(args[3], field, None)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    assert exc.value.progress.phase == "PREFLIGHT" and not calls


def test_wrong_pid_fails_before_source(monkeypatch):
    import threading

    args, kwargs, calls, _ = controlled(monkeypatch)
    owner = args[3]
    owner.pid = -1
    owner.guard = threading.Lock()
    monkeypatch.setattr(runner, "_owner_check", lambda value, **kw: value.check(**kw))
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args, **kwargs)
    assert exc.value.progress.phase == "PREFLIGHT" and not calls


def test_bad_row_map_and_generation_refuse(monkeypatch):
    args, kwargs, _, captured = controlled(monkeypatch)
    bad_map = dataclasses.replace(captured.data.row_map, map_bytes=b"{}")
    bad = dataclasses.replace(captured, data=dataclasses.replace(captured.data, row_map=bad_map))
    args[3].value = bad
    monkeypatch.setattr(runner, "_owner_check", lambda *a, **kw: bad)
    with pytest.raises(runner.CohortRunnerError):
        runner.run_cohort(*args, **kwargs)
    bad_pointer = dataclasses.replace(captured.pointer, generation=captured.pointer.generation + 1)
    bad = dataclasses.replace(captured, pointer=bad_pointer)
    args[3].value = bad
    with pytest.raises(runner.CohortRunnerError):
        runner.run_cohort(*args, **kwargs)


def test_mixed_full_gold_and_effective_authority_composition(monkeypatch):
    args, kwargs, calls, _ = controlled(monkeypatch, mixed=True)
    delegate = runner._aggregate
    aggregated = []

    def once(pairs, **options):
        aggregated.append(tuple(case_id for case_id, _ in pairs))
        return delegate(pairs, **options)

    monkeypatch.setattr(runner, "_aggregate", once)
    report = runner.run_cohort(*args, **kwargs)
    payload = json.loads(report.identity_payload)
    assert aggregated == [("case000", "case001")]
    assert calls.count("producer") == calls.count("binder") == 2
    assert payload["dataset_case_count"] == 3
    assert payload["dataset_gold_occurrences"] == 3
    assert [item["chosen_atom_occurrences"] for item in payload["cases"]] == [2, 0]
    assert all(item["original_authority_sha256"] != item["effective_authority_sha256"]
               for item in payload["cases"])
    core = payload["pure"]["identity_payload"]
    # One defined 2/2 source case and one undefined no-Gold case, fixed by this fixture.
    assert (core[11][0]["source_defined"], core[11][0]["source_undefined"]) == (1, 1)
    assert core[10][0]["prefixes"][0]["required_revisions"] == 2
    assert core[11][0]["source_macro"] == {"num": "1", "den": "1"}


def test_oversized_record_shape_refuses_before_set_allocation(monkeypatch):
    class UnexpectedAllocation(BaseException):
        pass

    def forbidden_set(*args, **kwargs):
        raise UnexpectedAllocation()

    cohort = runner.Cohort("tuning", ("case",))
    for number in range(128):
        cohort.__dict__[f"extra{number}"] = None
    # The old implementation resolves this global for set(value.__dict__).
    monkeypatch.setattr(runner, "set", forbidden_set, raising=False)
    assert runner._closed(cohort, runner.Cohort) is False


def test_final_serialization_refuses_before_copy_or_hash(monkeypatch):
    class CopyOrHashReached(BaseException):
        pass

    def forbidden(*args, **kwargs):
        raise CopyOrHashReached()

    monkeypatch.setattr(runner, "_hash_identity", forbidden)
    monkeypatch.setattr(runner, "_copy_payload", forbidden)
    monkeypatch.setattr(runner, "_join_payload", forbidden)
    clock = SimpleNamespace(check=lambda: None)
    for finish, args in (
        (runner._finish_pure, (bytearray(4096), "unused")),
        (runner._finish_outer, ((bytes(4096),), 4096)),
    ):
        # Enough for two 4096-byte passes, but not a third traversal.
        meter = runner._Meter(10000, 10000, clock.check)
        with pytest.raises(ValueError):
            finish(*args, meter, clock)
