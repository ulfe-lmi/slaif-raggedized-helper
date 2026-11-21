"""Synthetic source-to-graded diagnostic; execution requires Root authorization."""

import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import pytest

from slaif_raggedized_helper import ingestion_store, provenance_records
from slaif_raggedized_helper import raw_hybrid_search, raw_snapshot_catalog, raw_snapshot_rows
from slaif_raggedized_helper import raw_snapshot_pin as pin, raw_snapshot_selection as selection
from slaif_raggedized_helper import source_bound_ranking, source_bound_stage_loss
from slaif_raggedized_helper import supplied_rank_metrics as metrics, text_evaluation_dataset
import test_raw_hybrid_search_composition as source_fixture
import test_source_bound_support_ci_composition as fixture
import test_source_cohort_runner_composition as cohort
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401


CUTOFFS = (1, 2, 20, 60)
VARIANTS = ("dense", "lexical", "fusion")


def authority_hash(grants, restrictions):
    return hashlib.sha256(
        cohort.canonical([grants.model_dump(mode="json"), restrictions.model_dump(mode="json")])
    ).hexdigest()


def check_query(result, expected, query_id, gold, ranking):
    positive = bool(gold)
    assert result.query_id == query_id
    payload = dict(query_id=query_id, gold=gold, ranking=ranking, cutoffs=CUTOFFS)
    assert (
        result.input_fingerprint
        == "sha256:"
        + hashlib.sha256(b"slaif-supplied-rank-query-v1\n" + cohort.canonical(payload)).hexdigest()
    )
    assert result.formula_version == "supplied-rank-metrics-v1"
    assert (result.input_origin, result.qualification, result.relevance_unit) == (
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
        "SUPPLIED_UNIT_ID",
    )
    assert result.positive_gold_count == int(positive)
    assert result.ranking_count == len(ranking)
    assert tuple(value.k for value in result.at_k) == CUTOFFS
    for value in result.at_k:
        assert value.k in CUTOFFS and value.returned_at_k == min(value.k, len(ranking))
        if not positive:
            assert (value.recall, value.reciprocal_rank, value.ndcg) == (None, None, None)
            assert (value.dcg, value.idcg, value.relevant_returned, value.undefined_reason) == (
                0,
                0,
                0,
                "UNDEFINED_EMPTY_POSITIVE_GOLD",
            )
            continue
        found = expected != "lexical" and value.k >= 2
        assert value.undefined_reason is None and value.idcg == 7
        assert value.relevant_returned == int(found)
        assert value.recall == int(found) and value.reciprocal_rank == (0.5 if found else 0)
        assert math.isclose(
            value.dcg, 7 / math.log2(3) if found else 0, rel_tol=1e-12, abs_tol=1e-12
        )
        assert math.isclose(
            value.ndcg, 1 / math.log2(3) if found else 0, rel_tol=1e-12, abs_tol=1e-12
        )


def test_source_graded_rank_composition(tmp_path, monkeypatch):
    checkout = Path(__file__).resolve().parents[2]
    cohort.check_local_origins(checkout)
    oracle_path = checkout / "docs/parallel/source-graded-rank-oracle.json"
    oracle_bytes = oracle_path.read_bytes()
    assert (
        hashlib.sha256(oracle_bytes).hexdigest()
        == "cea83b46fa74ec2c31217fd3544ffd2f842e7480bb00142fb42f67460f90c856"
    )
    oracle = json.loads(oracle_bytes)
    assert tuple(oracle["cutoffs"]) == CUTOFFS
    assert oracle["cases"]["h1"]["explicit_judgments"] == {"a": 3}
    assert oracle["cases"]["h4"]["explicit_judgments"] == {}
    assert oracle["rankings_logical_names"] == {
        "dense": ["c", "a"],
        "lexical": ["c"],
        "fusion": ["c", "a"],
    }
    assert math.isclose(
        oracle["h1_at_k"]["2_20_60"]["dense_and_fusion"]["ndcg_decimal"],
        1 / math.log2(3),
        rel_tol=1e-12,
        abs_tol=1e-12,
    )
    assert oracle["direct_calls"] == dict(
        producer=2, stage_binder=3, external_judged_id_grounding=5, score_query=6, aggregate=3
    )
    owner = ctx = attempts = generators = workers = None
    calls = dict(
        producer=0, stage_binder=0, external_judged_id_grounding=0, score_query=0, aggregate=0
    )
    try:
        with monkeypatch.context() as patch:
            attempts, generators, workers = cohort.observe_fixture_lifecycle(patch)
            ctx = fixture.make_owned_support(tmp_path)
        assert attempts == {"generator": 1, "session": 6}
        assert len(generators) == 1 and generators[0].get("returncode") == 0
        assert len(workers) == 6 and all(
            w["close_returned"] and w["returncode"] is not None for w in workers
        )
        data, bundles = cohort.dataset_and_bundles(ctx)
        dataset = text_evaluation_dataset.admit(data)
        assert (dataset.case_count, dataset.gold_atom_count, dataset.held_out_count) == (5, 7, 4)
        cases = {case["case_id"]: case for case in json.loads(data)["cases"]}
        assert len(cases) == 5 and len(bundles) == 3
        assert (
            sum(len(req["alternatives"]) for case in cases.values() for req in case["requirements"])
            == 7
        )
        catalog = raw_snapshot_catalog.load_catalog(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id
        )
        by_source = {}
        source_scopes = {}
        for row in raw_snapshot_rows.parse(catalog.row_map_bytes).rows:
            bundle = ingestion_store.load(ctx.originals, ctx.derived, row.bundle_container_id)
            name = bundle.revision.source.logical_id
            assert name not in by_source
            by_source[name] = row
            source_scopes[name] = bundle.scope
        assert set(by_source) == {"a", "b", "c"}
        a, b, c = (by_source[name].chunk_id for name in ("a", "b", "c"))
        assert (a, c, b) == ctx.chunk_ids and len({a, b, c}) == 3
        effective = ctx.denied_grants
        restrictions = provenance_records.Restrictions(
            schema_version=1, corpora=None, versions=None
        )
        assert ctx.grants == provenance_records.Grants(
            schema_version=1, corpora=("one", "two"), versions=("v1",), labels=("secret",)
        )
        assert effective == provenance_records.Grants(
            schema_version=1, corpora=("one",), versions=("v1",), labels=()
        )
        assert all(
            provenance_records.reader_allows(source_scopes[name], effective, restrictions)
            for name in ("a", "c")
        )
        assert not provenance_records.reader_allows(source_scopes["b"], effective, restrictions)
        effective_hash = authority_hash(effective, restrictions)
        original_hash = authority_hash(ctx.grants, restrictions)
        core = json.loads(
            (Path(ctx.root) / "snapshots" / ctx.snapshot_id[7:] / ".core.json").read_bytes()
        )
        e = core["embedding"]
        ids = dict(
            query_space_id=e["space_id"],
            query_definition_fingerprint=e["definition_fingerprint"],
            query_policy_id=e["query_policy_fingerprint"],
            query_execution_fingerprint=e["query_execution_fingerprint"],
        )
        payload = struct.pack("<1024f", 0.6, 0, 0.8, *([0.0] * 1021))
        first = selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, None
        )
        owner = pin.PinOwner()
        captured = owner.acquire_selected_data(ctx.originals, ctx.derived, ctx.root)
        assert captured.pointer == first.pointer and owner.check() is captured
        entries = {name: [] for name in VARIANTS}
        results = {}
        for case_id in ("h1", "h4"):
            case = cases[case_id]
            assert case["split"] == "held_out" and case["scope"] == dict(
                corpora=["one"], versions=["v1"], labels=[]
            )
            assert owner.check() is captured
            calls["producer"] += 1
            result = raw_hybrid_search.search(
                ctx.originals,
                ctx.derived,
                ctx.root,
                ctx.snapshot_id,
                case["question"],
                payload,
                **ids,
                grants=effective,
                restrictions=restrictions,
                dense_k=60,
                lexical_k=60,
                partition_cap=60,
                k=60,
                trace=True,
            )
            results[case_id] = result
            assert owner.check() is captured
            assert (result.snapshot_id, result.catalog_id, result.authority_sha256) == (
                captured.pointer.snapshot_id,
                catalog.catalog_id,
                effective_hash,
            )
            assert result.query_text_sha256 == hashlib.sha256(case["question"].encode()).hexdigest()
            assert result.query_payload_sha256 == hashlib.sha256(payload).hexdigest()
            query_wire = dict(
                kind="raw-hybrid-query/v1",
                snapshot_id=ctx.snapshot_id,
                catalog_id=catalog.catalog_id,
                query_text_sha256=result.query_text_sha256,
                query_payload_sha256=result.query_payload_sha256,
                **ids,
                authority_sha256=effective_hash,
                dense_k=60,
                lexical_k=60,
                partition_cap=60,
                k=60,
            )
            assert result.query_id == hashlib.sha256(cohort.canonical(query_wire)).hexdigest()
            assert (result.query_origin, result.qualification) == (
                "SUPPLIED_UNVERIFIED",
                "NOT_QUALIFIED",
            )
            for trace in (result.dense.trace, result.lexical.trace):
                assert (trace.snapshot_id, trace.catalog_id, trace.authority_sha256) == (
                    ctx.snapshot_id,
                    catalog.catalog_id,
                    effective_hash,
                )
            for field, value in ids.items():
                assert getattr(result.dense.trace, field) == value
            assert (
                result.fusion.snapshot_id,
                result.fusion.catalog_id,
                result.fusion.query_id,
            ) == (ctx.snapshot_id, catalog.catalog_id, result.query_id)
            assert result.dense.eligible == result.lexical.eligible == 2
            calls["stage_binder"] += 1
            diagnosis = source_bound_stage_loss.bind_stages(
                ctx.originals,
                ctx.derived,
                ctx.root,
                owner,
                data,
                case_id,
                bundles,
                result,
                payload,
                **ids,
                grants=ctx.grants,
                restrictions=restrictions,
            )
            assert owner.check() is captured
            assert (diagnosis.dataset_id, diagnosis.split_id) == (
                dataset.dataset_id,
                dataset.split_id,
            )
            assert (
                diagnosis.case_id,
                diagnosis.snapshot_id,
                diagnosis.catalog_id,
                diagnosis.query_id,
            ) == (case_id, ctx.snapshot_id, catalog.catalog_id, result.query_id)
            assert (diagnosis.question_sha256, diagnosis.payload_sha256) == (
                result.query_text_sha256,
                result.query_payload_sha256,
            )
            assert (diagnosis.authority_sha256, diagnosis.original_authority_sha256) == (
                effective_hash,
                original_hash,
            )
            assert (
                diagnosis.dataset_case_count,
                diagnosis.dataset_atom_occurrences,
                diagnosis.chosen_atom_occurrences,
            ) == (5, 7, 1 if case_id == "h1" else 0)
            assert (diagnosis.dense_trace_id, diagnosis.lexical_trace_id) == (
                result.dense.trace.trace_id,
                result.lexical.trace.trace_id,
            )
            gold = ((a, 3),) if case_id == "h1" else ()
            calls["external_judged_id_grounding"] += 1
            bound = source_bound_ranking.bind(
                ctx.originals,
                ctx.derived,
                ctx.root,
                ctx.snapshot_id,
                catalog.catalog_id,
                tuple(x[0] for x in gold),
                grants=effective,
                restrictions=restrictions,
            )
            assert owner.check() is captured
            assert (bound.snapshot_id, bound.catalog_id, bound.authority_sha256) == (
                ctx.snapshot_id,
                catalog.catalog_id,
                effective_hash,
            )
            assert tuple(row.chunk_id for row in bound.rows) == tuple(x[0] for x in gold)
            assert all(
                row.fragments
                and (
                    row.revision_id,
                    row.extraction_id,
                    row.representation_id,
                    row.bundle_container_id,
                )
                == (
                    by_source["a"].revision_id,
                    by_source["a"].extraction_id,
                    by_source["a"].representation_id,
                    by_source["a"].bundle_container_id,
                )
                for row in bound.rows
            )
            for variant in VARIANTS:
                ranking = tuple(hit.chunk_id for hit in getattr(result, variant).hits)
                assert ranking == ((c,) if variant == "lexical" else (c, a))
                calls["score_query"] += 1
                score = metrics.score_query(result.query_id, gold, ranking, cutoffs=CUTOFFS)
                assert score.query_id == result.query_id
                check_query(score, variant, result.query_id, gold, ranking)
                entries[variant].append((result.query_id, gold, ranking))
        for variant in VARIANTS:
            cases_sorted = tuple(sorted(entries[variant], key=lambda item: item[0]))
            calls["aggregate"] += 1
            aggregate = metrics.aggregate(cases_sorted, cutoffs=CUTOFFS)
            assert (aggregate.input_origin, aggregate.qualification, aggregate.relevance_unit) == (
                "SUPPLIED_UNVERIFIED",
                "NOT_QUALIFIED",
                "SUPPLIED_UNIT_ID",
            )
            assert aggregate.formula_version == "supplied-rank-metrics-v1"
            assert (
                aggregate.input_fingerprint
                == "sha256:"
                + hashlib.sha256(
                    b"slaif-supplied-rank-aggregate-v1\n"
                    + cohort.canonical(dict(cases=cases_sorted, cutoffs=CUTOFFS))
                ).hexdigest()
            )
            assert (
                aggregate.total_queries,
                aggregate.defined_queries,
                aggregate.undefined_empty_gold_queries,
            ) == (2, 1, 1)
            assert tuple(q.query_id for q in aggregate.query_results) == tuple(
                item[0] for item in cases_sorted
            )
            for query, (query_id, gold, ranking) in zip(
                aggregate.query_results, cases_sorted, strict=True
            ):
                check_query(query, variant, query_id, gold, ranking)
            assert tuple(item.k for item in aggregate.at_k) == CUTOFFS
            for item in aggregate.at_k:
                found = variant != "lexical" and item.k >= 2
                assert (
                    item.total_queries,
                    item.defined_queries,
                    item.undefined_empty_gold_queries,
                ) == (2, 1, 1)
                assert item.mean_recall == int(found) and item.mrr == (0.5 if found else 0)
                assert math.isclose(
                    item.mean_ndcg, 1 / math.log2(3) if found else 0, rel_tol=1e-12, abs_tol=1e-12
                )

        class UnexpectedScore(BaseException):
            pass

        def forbidden_score(*args, **kwargs):
            raise UnexpectedScore("scorer reached after refused grounding")

        wrong_catalog = "sha256:" + cohort.different_space_id(catalog.catalog_id[7:])
        with monkeypatch.context() as negative_patch:
            negative_patch.setattr(metrics, "score_query", forbidden_score)
            for chunk_ids, expected_catalog in (
                ((b,), catalog.catalog_id),
                ((a, a), catalog.catalog_id),
                ((a,), wrong_catalog),
            ):
                calls["external_judged_id_grounding"] += 1
                with pytest.raises(
                    source_bound_ranking.SourceBindingError, match="^source bound ranking refused$"
                ) as error:
                    source_bound_ranking.bind(
                        ctx.originals,
                        ctx.derived,
                        ctx.root,
                        ctx.snapshot_id,
                        expected_catalog,
                        chunk_ids,
                        grants=effective,
                        restrictions=restrictions,
                    )
                    metrics.score_query(results["h1"].query_id, ((a, 3),), (c, a), cutoffs=CUTOFFS)
                assert error.value.__suppress_context__
                assert owner.check() is captured
            wrong_ids = dict(ids, query_space_id=cohort.different_space_id(ids["query_space_id"]))
            calls["stage_binder"] += 1
            with pytest.raises(
                source_bound_stage_loss.StageBindingError,
                match="^source-bound stage diagnosis refused$",
            ) as error:
                source_bound_stage_loss.bind_stages(
                    ctx.originals,
                    ctx.derived,
                    ctx.root,
                    owner,
                    data,
                    "h1",
                    bundles,
                    results["h1"],
                    payload,
                    **wrong_ids,
                    grants=ctx.grants,
                    restrictions=restrictions,
                )
                metrics.score_query(results["h1"].query_id, ((a, 3),), (c, a), cutoffs=CUTOFFS)
            assert error.value.__suppress_context__ and owner.check() is captured
        assert calls == oracle["direct_calls"]
        cohort.check_local_origins(checkout)
    finally:
        body = sys.exception()

        def close_pin():
            if owner is not None and owner.state != "CLOSED":
                owner.close()

        def close_stores():
            if ctx is not None:
                source_fixture.close_owned_stores(ctx.derived, ctx.originals, None)

        def write_log(failures):
            lifecycle = dict(
                attempts=attempts,
                calls=calls,
                cleanup_failures=failures,
                generators=[
                    {
                        key: event.get(key)
                        for key in ("pid", "spawn_state", "returncode", "poll_failed")
                    }
                    for event in (generators if generators is not None else ())
                ],
                workers=[
                    {
                        key: worker.get(key)
                        for key in ("pid", "close_returned", "returncode", "poll_failed")
                    }
                    for worker in (workers if workers is not None else ())
                ],
            )
            (tmp_path / "fixture-lifecycle.json").write_text(json.dumps(lifecycle, sort_keys=True))

        cleanup = cohort.cleanup_owned(body, close_pin, close_stores, write_log)
        if body is None and cleanup is not None:
            raise cleanup
