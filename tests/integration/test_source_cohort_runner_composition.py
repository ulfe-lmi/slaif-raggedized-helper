"""Work in progress: actual source execution requires a separate Root decision."""

import test_retrieval_representation_composition as representation_fixture

import hashlib
import json
from dataclasses import replace
from pathlib import Path
import struct
import subprocess
import sys

import pytest
from slaif_raggedized_helper import ingestion_store, raw_snapshot_catalog, raw_snapshot_rows
from slaif_raggedized_helper import raw_snapshot_pin as pin, raw_snapshot_selection as selection
from slaif_raggedized_helper import provenance_records, source_cohort_runner as runner
from slaif_raggedized_helper import tokenizer_session
import test_native_tokenizers
import test_raw_hybrid_search_composition as source_fixture
import test_source_bound_support_ci_composition as fixture
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
        "ascii"
    )


def check_local_origins(checkout):
    """Reject local product or test helpers loaded from a different checkout."""
    for name, module in tuple(sys.modules.items()):
        if (
            name == "slaif_raggedized_helper"
            or name.startswith("slaif_raggedized_helper.")
            or name.startswith("test_")
        ):
            origin = getattr(module, "__file__", None)
            assert origin is not None and Path(origin).resolve().is_relative_to(checkout)


def dataset_and_bundles(ctx):
    """Use actual owned source IDs, independent of runner, producer and binder outputs."""
    catalog = raw_snapshot_catalog.load_catalog(
        ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id
    )
    rows = raw_snapshot_rows.parse(catalog.row_map_bytes).rows
    atoms, bundle_ids = {}, set()
    for row in rows:
        bundle = ingestion_store.load(ctx.originals, ctx.derived, row.bundle_container_id)
        bundle_ids.add(row.bundle_container_id)
        chunk = next(c for c in bundle.chunks if c.chunk_id == row.chunk_id)
        blocks = {b.block_id: b for b in bundle.blocks}
        fragment = next(f for f in chunk.fragments if "alpha beta" in getattr(f, "copied_text", ""))
        block = blocks[fragment.block_id]
        start = block.text.index("alpha beta", fragment.start, fragment.end)
        atoms[bundle.revision.source.logical_id] = dict(
            revision_id=row.revision_id,
            extraction_id=row.extraction_id,
            block_id=block.block_id,
            start=start,
            end=start + 10,
            text_sha256=hashlib.sha256(b"alpha beta").hexdigest(),
        )
    assert set(atoms) == {"a", "b", "c"} and len(bundle_ids) == 3
    base = json.loads(ctx.dataset)
    common = base["cases"][0]

    def req(name, alternatives):
        return dict(
            requirement_id=name,
            grade=1,
            alternatives=sorted(([atoms[x]] for x in alternatives), key=canonical),
        )

    def case(case_id, split, question, requirements, corpora, labels=()):
        return dict(
            common,
            case_id=case_id,
            family_id="family-" + case_id,
            split=split,
            question=question,
            scope=dict(corpora=corpora, versions=["v1"], labels=list(labels)),
            answerability="answerable" if requirements else "unanswerable",
            acceptable_facts=["Synthetic alpha beta."] if requirements else [],
            requirements=requirements,
        )

    base["cases"] = [
        case("h1", "held_out", "DistinctiveZephyr one?", [req("one", "a")], ["one"]),
        case(
            "h2",
            "held_out",
            "DistinctiveZephyr three?",
            [req("all", "a"), req("bee", "b"), req("cee", "c")],
            ["one", "two"],
            ("secret",),
        ),
        case("h3", "held_out", "DistinctiveZephyr either?", [req("either", "ac")], ["one"]),
        case("h4", "held_out", "DistinctiveZephyr none?", [], ["one"]),
        case("t1", "tuning", "Unrelated tuning question?", [req("tune", "c")], ["one"]),
    ]
    return canonical(base), tuple(sorted(bundle_ids))


def different_space_id(value):
    """Valid shape, guaranteed changed; used only after frozen ABI inspection."""
    assert len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    return ("1" if value[0] == "0" else "0") + value[1:]


def observe_runner(
    monkeypatch,
    events,
    outer,
    data,
    bundles,
    grants,
    restrictions,
    ctx,
    captured,
    query_state,
    observed,
):
    """Validate at the delegate boundary; retain scalar evidence and one pending result."""
    declared = {case["case_id"]: case for case in json.loads(data)["cases"]}
    case_ids = ("h1", "h2", "h3", "h4")
    scopes = (("one",), ("one", "two"), ("one",), ("one",))
    labels = ((), ("secret",), (), ())
    for name in ("_owner_check", "_produce", "_bind", "_aggregate"):
        delegate = getattr(runner, name)

        def measured(*args, _name=name, _delegate=delegate, **kwargs):
            attempt = len(outer)
            prior = [event for event in events if event["attempt"] == attempt]
            index = sum(event["name"] == _name for event in prior)
            state = observed.setdefault(attempt, {"pending": None, "cases": [], "geometries": []})
            if _name == "_produce":
                query = query_state["queries"][index]
                assert state["pending"] is None and query.case_id == case_ids[index]
                assert args[:4] == (
                    ctx.originals,
                    ctx.derived,
                    ctx.root,
                    captured.pointer.snapshot_id,
                )
                assert args[4] == declared[query.case_id]["question"] and args[5] == query.payload
                assert tuple(
                    kwargs[key]
                    for key in (
                        "query_space_id",
                        "query_definition_fingerprint",
                        "query_policy_id",
                        "query_execution_fingerprint",
                    )
                ) == (
                    query.space_id,
                    query.definition_fingerprint,
                    query.policy_id,
                    query.execution_fingerprint,
                )
                assert kwargs["grants"] == provenance_records.Grants(
                    schema_version=1, corpora=scopes[index], versions=("v1",), labels=labels[index]
                )
                assert kwargs["restrictions"] == restrictions
                assert tuple(
                    kwargs[key] for key in ("dense_k", "lexical_k", "partition_cap", "k", "trace")
                ) == (60, 60, 60, 60, True)
                effective_hash = hashlib.sha256(
                    canonical(
                        [
                            kwargs["grants"].model_dump(mode="json"),
                            restrictions.model_dump(mode="json"),
                        ]
                    )
                ).hexdigest()
            elif _name == "_bind":
                pending = state["pending"]
                state["pending"] = None
                assert pending is not None and args[7] is pending
                del pending
                assert args[:4] == (ctx.originals, ctx.derived, ctx.root, query_state["owner"])
                assert args[4:7] == (data, case_ids[index], bundles)
                query = query_state["queries"][index]
                assert args[8] == query.payload
                assert tuple(
                    kwargs[key]
                    for key in (
                        "query_space_id",
                        "query_definition_fingerprint",
                        "query_policy_id",
                        "query_execution_fingerprint",
                    )
                ) == (
                    query.space_id,
                    query.definition_fingerprint,
                    query.policy_id,
                    query.execution_fingerprint,
                )
                assert kwargs["grants"] == grants and kwargs["restrictions"] == restrictions
            elif _name == "_aggregate":
                assert state["pending"] is None and len(state["cases"]) == 4
                assert tuple(case_id for case_id, _ in args[0]) == case_ids
                assert tuple(id(geometry) for _, geometry in args[0]) == tuple(state["geometries"])
            event = {"attempt": attempt, "name": _name, "state": "attempted"}
            events.append(event)
            try:
                value = _delegate(*args, **kwargs)
                if _name == "_produce":
                    query_input = dict(
                        kind="raw-hybrid-query/v1",
                        snapshot_id=captured.pointer.snapshot_id,
                        catalog_id=value.catalog_id,
                        query_text_sha256=hashlib.sha256(args[4].encode("utf-8")).hexdigest(),
                        query_payload_sha256=hashlib.sha256(args[5]).hexdigest(),
                        query_space_id=query.space_id,
                        query_definition_fingerprint=query.definition_fingerprint,
                        query_policy_id=query.policy_id,
                        query_execution_fingerprint=query.execution_fingerprint,
                        authority_sha256=effective_hash,
                        dense_k=60,
                        lexical_k=60,
                        partition_cap=60,
                        k=60,
                    )
                    assert value.query_id == hashlib.sha256(canonical(query_input)).hexdigest()
                    state["pending"] = value
                    state["cases"].append(
                        {
                            "case_id": query.case_id,
                            "query_id": value.query_id,
                            "effective_authority_sha256": effective_hash,
                        }
                    )
                elif _name == "_bind":
                    original_hash = hashlib.sha256(
                        canonical(
                            [grants.model_dump(mode="json"), restrictions.model_dump(mode="json")]
                        )
                    ).hexdigest()
                    state["cases"][index].update(
                        original_authority_sha256=original_hash,
                        binder_invocation_id=value.invocation_id,
                        geometry_invocation_id=value.geometry.invocation_id,
                    )
                    state["geometries"].append(id(value.geometry))
            except BaseException:
                event["state"] = "refused"
                state["pending"] = None
                raise
            event["state"] = "completed"
            return value

        monkeypatch.setattr(runner, name, measured)


def observe_fixture_lifecycle(monkeypatch):
    """Capture owned session handles while preserving the real worker lifecycle."""
    events = []
    original_init = tokenizer_session.Session.__init__
    original_close = tokenizer_session.Session.close
    original_generator = test_native_tokenizers.make_native
    attempts = {"generator": 0, "session": 0}
    generators = []

    def generator(*args, **kwargs):
        attempts["generator"] += 1
        if attempts["generator"] > 1:
            raise RuntimeError("fixture generator ceiling exceeded")
        original_popen_init = subprocess.Popen.__init__

        def init_generator(child, *popen_args, **popen_kwargs):
            if generators:
                raise RuntimeError("fixture generator subprocess ceiling exceeded")
            event = {"spawn_state": "init_attempted_birth_unknown"}
            generators.append(event)
            original_popen_init(child, *popen_args, **popen_kwargs)
            event.update(child=child, pid=child.pid, spawn_state="initialized")

        try:
            with monkeypatch.context() as generator_patch:
                generator_patch.setattr(subprocess.Popen, "__init__", init_generator)
                return original_generator(*args, **kwargs)
        finally:
            for event in generators:
                if "child" not in event:
                    continue
                try:
                    event["returncode"] = event["child"].poll()
                except BaseException:
                    event["returncode"] = None
                    event["poll_failed"] = True

    def init(session, *args, **kwargs):
        attempts["session"] += 1
        if attempts["session"] > 6:
            raise RuntimeError("fixture session ceiling exceeded")
        try:
            return original_init(session, *args, **kwargs)
        finally:
            child = getattr(session, "_child", None)
            if child is not None and not any(event["child"] is child for event in events):
                events.append({"child": child, "pid": child.pid, "close_returned": False})

    def close(session, *args, **kwargs):
        child = getattr(session, "_child", None)
        event = next((item for item in events if item["child"] is child), None)
        if child is not None and event is None:
            event = {"child": child, "pid": child.pid, "close_returned": False}
            events.append(event)
        result = original_close(session, *args, **kwargs)
        if event is not None:
            event["close_returned"] = True
            try:
                event["returncode"] = child.poll()
            except BaseException:
                # An observation failure is not allowed to alter the real close.
                event["returncode"] = None
                event["poll_failed"] = True
        return result

    monkeypatch.setattr(test_native_tokenizers, "make_native", generator)
    monkeypatch.setattr(tokenizer_session.Session, "__init__", init)
    monkeypatch.setattr(tokenizer_session.Session, "close", close)
    return attempts, generators, events


def check_private_report(report, captured, data, cohort, observed_cases):
    """Check identities and structural status without emitting linkable values."""
    assert type(report) is runner.CohortReport
    assert (
        report.identity
        == "sha256:"
        + hashlib.sha256(b"slaif-source-cohort-runner-v1\n" + report.identity_payload).hexdigest()
    )
    result = json.loads(report.identity_payload)
    assert result["schema"] == "slaif-source-cohort-runner-v1"
    assert result["split"] == "held_out" and result["selection_kind"] == "FULL_ADMITTED_SPLIT"
    assert (
        result["dataset_case_count"],
        result["dataset_gold_occurrences"],
        result["selected_count"],
    ) == (5, 7, 4)
    assert (result["synthetic_count"], result["human_declared_count"]) == (5, 0)
    assert result["progress"] == dict(intended=4, attempted=4, completed=4, refused=0, pending=0)
    assert result["pointer_sha256"] == hashlib.sha256(captured.pointer.pointer_bytes).hexdigest()
    assert result["generation"] == captured.pointer.generation
    assert result["snapshot_id"] == captured.pointer.snapshot_id
    assert result["statuses"] == dict(
        split="STRUCTURAL_ONLY",
        authorship="DECLARED_UNVERIFIED",
        rights="DECLARED_UNVERIFIED",
        producer="COMPLETED",
        current_rights="NOT_CHECKED",
        policy="NOT_CHECKED",
        encoder="NOT_QUALIFIED",
        model="NOT_QUALIFIED",
        baseline="NOT_RUN",
        source="SEQUENTIAL_NOT_ATOMIC",
    )
    assert result["ledger"]["direct_own_observed"] == dict(
        dataset=1, pin=5, producer=4, binder=4, aggregate=1
    )
    assert result["ledger"]["dataset_internal"] == "UNMEASURED_BY_RUNNER"
    assert result["ledger"]["binder_geometry"] == "OVERLAPPING_NOT_ADDITIVE"
    assert [case["case_id"] for case in result["cases"]] == list(cohort.case_ids)
    assert [case["chosen_atom_occurrences"] for case in result["cases"]] == [1, 3, 2, 0]
    for case, evidence in zip(result["cases"], observed_cases, strict=True):
        assert (case["dataset_case_count"], case["dataset_atom_occurrences"]) == (5, 7)
        for key in (
            "case_id",
            "query_id",
            "original_authority_sha256",
            "effective_authority_sha256",
            "binder_invocation_id",
            "geometry_invocation_id",
        ):
            assert case[key] == evidence[key]
    pure = result["pure"]
    encoded = json.dumps(pure["identity_payload"], ensure_ascii=True, separators=(",", ":")).encode(
        "ascii"
    )
    assert (
        pure["identity"]
        == "sha256:" + hashlib.sha256(b"slaif-declared-cohort-metrics-v1\n" + encoded).hexdigest()
    )
    assert data == canonical(json.loads(data))


def load_final_oracle():
    """Load independent expected records before fixture or source creation."""
    oracle_path = (
        Path(__file__).resolve().parents[2] / "docs/parallel/source-cohort-runner-tiny-oracle.json"
    )
    oracle = json.loads(oracle_path.read_bytes())
    expected = oracle["api_expectations"]
    assert set(expected) == {"prefixes", "transitions"}
    assert len(expected["prefixes"]) == 6 and len(expected["transitions"]) == 7
    return expected


def check_final_oracle(report, expected):
    """Compare complete API summaries to independently supplied expected records."""
    payload = json.loads(report.identity_payload)["pure"]["identity_payload"]
    assert payload[11] == expected["prefixes"]
    assert payload[12] == expected["transitions"]


def cohort_budget():
    """Reserve the four-case logical envelope, not physical source I/O."""
    directories, ingestion, batches = 69, 38784, 43520
    source_bytes = (
        directories * 100925699
        + (ingestion + batches) * 404750404
        + ingestion * 2016386
        + 4 * 4986555627809
    )
    return runner.Budget(
        source_directories=113,
        source_ingestion_loads=ingestion + 4 * 5888,
        source_derived_batch_loads=batches + 4 * 6400,
        source_bytes=source_bytes,
        pin_calls=25,
        producer_calls=4,
        binder_calls=4,
        catalog_calls=44,
        gold_calls=4,
        ranking_calls=4,
        geometry_calls=4,
        aggregate_calls=1,
        local_work=134217728,
        local_payload=268435456,
        binder_work=4 * 134217728,
        binder_payload=4 * 268435456,
        geometry_work=4 * 67108864,
        geometry_payload=4 * 134217728,
        aggregate_work=134217728,
        aggregate_payload=268435456,
    )


def adapt_frozen_runner_and_observers(
    ctx, owner, captured, data, bundles, payload, ids, monkeypatch, expected, events, outer
):
    """Bind the four attempts to the published private runner ABI."""
    cohort = runner.Cohort("held_out", ("h1", "h2", "h3", "h4"))
    queries = tuple(runner.Query(case_id, payload, *ids) for case_id in cohort.case_ids)
    restrictions = provenance_records.Restrictions(schema_version=1, corpora=None, versions=None)
    assert ctx.grants == provenance_records.Grants(
        schema_version=1, corpora=("one", "two"), versions=("v1",), labels=("secret",)
    )
    options = dict(
        grants=ctx.grants,
        restrictions=restrictions,
        config=runner.Config("synthetic-cohort", "structural-only"),
        budget=cohort_budget(),
        deadline_ms=1200000,
    )
    observed = {}
    query_state = {"queries": queries, "owner": owner}
    observe_runner(
        monkeypatch,
        events,
        outer,
        data,
        bundles,
        ctx.grants,
        restrictions,
        ctx,
        captured,
        query_state,
        observed,
    )

    def invoke(selected_queries):
        query_state["queries"] = selected_queries
        record = {"attempt": len(outer) + 1, "state": "attempted"}
        outer.append(record)
        try:
            result = runner.run_cohort(
                ctx.originals,
                ctx.derived,
                ctx.root,
                owner,
                data,
                cohort,
                selected_queries,
                bundles,
                **options,
            )
        except runner.CohortRunnerError as exc:
            record["state"] = "refused"
            if exc.progress is not None:
                record["progress"] = {
                    key: getattr(exc.progress, key)
                    for key in ("phase", "intended", "attempted", "completed", "refused", "pending")
                }
            raise
        record["state"] = "completed"
        return result

    def counts(start):
        return tuple(
            sum(event["name"] == name for event in events[start:])
            for name in ("_owner_check", "_produce", "_bind", "_aggregate")
        )

    report = invoke(queries)
    assert counts(0) == (5, 4, 4, 1)
    assert events[-1]["name"] == "_aggregate" and events[-1]["state"] == "completed"
    assert observed[1]["pending"] is None and len(observed[1]["cases"]) == 4
    check_private_report(report, captured, data, cohort, observed[1]["cases"])
    check_final_oracle(report, expected)
    del report
    del observed[1]

    start = len(events)
    with pytest.raises(runner.CohortRunnerError) as missing:
        invoke(queries[:-1])
    assert missing.value.progress is None and counts(start) == (0, 0, 0, 0)
    assert missing.value.args == ("cohort runner refused",) and missing.value.__suppress_context__
    del missing

    start = len(events)
    altered = (*queries[:2], replace(queries[2], space_id=different_space_id(ids[0])), queries[3])
    with pytest.raises(runner.CohortRunnerError) as changed:
        invoke(altered)
    assert changed.value.progress == runner.FailurePrefix("PRODUCER", 4, 3, 2, 1, 1)
    assert counts(start) == (4, 3, 2, 0)
    assert [event["state"] for event in events[start:] if event["name"] == "_produce"] == [
        "completed",
        "completed",
        "refused",
    ]
    assert all(
        event["state"] == "completed"
        for event in events[start:]
        if event["name"] in ("_owner_check", "_bind")
    )
    assert changed.value.args == ("cohort runner refused",) and changed.value.__suppress_context__
    del changed

    owner.close()
    start = len(events)
    with pytest.raises(runner.CohortRunnerError) as closed:
        invoke(queries)
    assert closed.value.progress == runner.FailurePrefix("PREFLIGHT", 4, 0, 0, 0, 4)
    assert counts(start) == (0, 0, 0, 0)
    assert closed.value.args == ("cohort runner refused",) and closed.value.__suppress_context__
    del closed


def safe_cleanup_note(target, message):
    """Never let annotation replace the body or cleanup exception."""
    try:
        BaseException.add_note(target, message)
    except BaseException:
        pass


def cleanup_owned(body, close_pin, close_stores, write_log):
    """Attempt all owned cleanup, preserving the body or first cleanup exception."""
    first = None
    failures = []
    for label, operation in (("pin", close_pin), ("stores", close_stores)):
        try:
            operation()
        except BaseException as exc:
            failures.append({"operation": label, "type": type(exc).__name__})
            if first is None:
                first = exc
            target = body if body is not None else first
            safe_cleanup_note(target, "Owned " + label + " cleanup failed")
    try:
        write_log(failures)
    except BaseException as exc:
        failures.append({"operation": "lifecycle_log", "type": type(exc).__name__})
        if first is None:
            first = exc
        target = body if body is not None else first
        safe_cleanup_note(target, "Private lifecycle record failed")
    return first


def test_source_cohort_runner_composition(tmp_path, monkeypatch):
    checkout = Path(__file__).resolve().parents[2]
    for module in (representation_fixture, test_native_tokenizers, source_fixture, fixture):
        assert Path(module.__file__).resolve().is_relative_to(checkout)
    check_local_origins(checkout)
    expected = load_final_oracle()
    owner = None
    ctx = None
    attempts = generators = workers = None
    events, outer = [], []
    try:
        with monkeypatch.context() as fixture_patch:
            attempts, generators, workers = observe_fixture_lifecycle(fixture_patch)
            ctx = fixture.make_owned_support(tmp_path)
        assert attempts == {"generator": 1, "session": 6}
        assert len(generators) == 1 and generators[0].get("spawn_state") == "initialized"
        assert generators[0].get("returncode") == 0
        assert len(workers) == 6
        assert all(
            worker["close_returned"] and worker["returncode"] is not None for worker in workers
        )
        data, bundles = dataset_and_bundles(ctx)
        core = json.loads(
            (Path(ctx.root) / "snapshots" / ctx.snapshot_id[7:] / ".core.json").read_bytes()
        )
        e = core["embedding"]
        ids = (
            e["space_id"],
            e["definition_fingerprint"],
            e["query_policy_fingerprint"],
            e["query_execution_fingerprint"],
        )
        payload = struct.pack("<1024f", 0.6, 0, 0.8, *([0.0] * 1021))
        first = selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, None
        )
        owner = pin.PinOwner()
        captured = owner.acquire_selected_data(ctx.originals, ctx.derived, ctx.root)
        second = selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, first.pointer.pointer_bytes
        )
        assert captured.pointer == first.pointer and owner.check() is captured
        assert second.pointer.generation == captured.pointer.generation + 1
        adapt_frozen_runner_and_observers(
            ctx, owner, captured, data, bundles, payload, ids, monkeypatch, expected, events, outer
        )
        check_local_origins(checkout)
    finally:
        body = sys.exception()

        def close_pin():
            if owner is not None and owner.state != "CLOSED":
                owner.close()

        def close_stores():
            if ctx is not None:
                # Passing None lets this existing helper attempt both stores and
                # raise its first failure, which our outer cleanup records.
                source_fixture.close_owned_stores(ctx.derived, ctx.originals, None)

        def write_log(failures):
            lifecycle = {
                "attempts": attempts,
                "outer_attempts": outer,
                "cleanup_failures": failures,
                "generators": [
                    {
                        key: event.get(key)
                        for key in ("pid", "spawn_state", "returncode", "poll_failed")
                    }
                    for event in (generators if generators is not None else ())
                ],
                "runner_calls": [
                    {"attempt": event["attempt"], "name": event["name"], "state": event["state"]}
                    for event in events
                ],
                "workers": [
                    {
                        key: worker.get(key)
                        for key in ("pid", "close_returned", "returncode", "poll_failed")
                    }
                    for worker in (workers if workers is not None else ())
                ],
            }
            (tmp_path / "fixture-lifecycle.json").write_text(json.dumps(lifecycle, sort_keys=True))

        cleanup = cleanup_owned(body, close_pin, close_stores, write_log)
        if body is None and cleanup is not None:
            raise cleanup
