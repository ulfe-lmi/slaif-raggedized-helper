"""Genuine graded program composition; actual execution requires Root approval."""

import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys

import pytest

from slaif_raggedized_helper import evaluation_program as program
from slaif_raggedized_helper import ingestion_store, native_tokenizers, provenance_records
from slaif_raggedized_helper import raw_snapshot_catalog, raw_snapshot_rows
from slaif_raggedized_helper import raw_snapshot_pin as pin, raw_snapshot_selection as selection
from slaif_raggedized_helper import source_bound_ranking, source_cohort_runner as runner
from slaif_raggedized_helper import supplied_rank_metrics as metrics, text_evaluation_dataset
from slaif_raggedized_helper import tokenizer_session
import test_source_cohort_runner_composition as cohort
import test_native_tokenizers
import test_raw_hybrid_search_composition as source_fixture
import test_source_bound_support_ci_composition as fixture
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401

# Collection verifies imported project and test helper origins without running the test body.
cohort.check_local_origins(Path(__file__).resolve().parents[2])

# Data-only seeds from the previously reviewed genuine tokenizer fixture.
SEEDS = (
    (
        b'{\n  "version": "1.0",\n  "truncat'
        b'ion": {\n    "direction": "Right"'
        b',\n    "max_length": 5,\n    "stra'
        b'tegy": "LongestFirst",\n    "stri'
        b'de": 0\n  },\n  "padding": {\n    "'
        b'strategy": {\n      "Fixed": 20\n '
        b'   },\n    "direction": "Right",\n'
        b'    "pad_to_multiple_of": null,\n'
        b'    "pad_id": 0,\n    "pad_type_i'
        b'd": 0,\n    "pad_token": "[UNK]"\n'
        b'  },\n  "added_tokens": [],\n  "no'
        b'rmalizer": null,\n  "pre_tokenize'
        b'r": {\n    "type": "Whitespace"\n '
        b' },\n  "post_processor": {\n    "t'
        b'ype": "TemplateProcessing",\n    '
        b'"single": [\n      {\n        "Spe'
        b'cialToken": {\n          "id": "['
        b'CLS]",\n          "type_id": 0\n  '
        b"      }\n      },\n      {\n       "
        b' "Sequence": {\n          "id": "'
        b'A",\n          "type_id": 0\n     '
        b'   }\n      },\n      {\n        "S'
        b'pecialToken": {\n          "id": '
        b'"[SEP]",\n          "type_id": 0\n'
        b'        }\n      }\n    ],\n    "pa'
        b'ir": [\n      {\n        "SpecialT'
        b'oken": {\n          "id": "[CLS]"'
        b',\n          "type_id": 0\n       '
        b' }\n      },\n      {\n        "Seq'
        b'uence": {\n          "id": "A",\n '
        b'         "type_id": 0\n        }\n'
        b'      },\n      {\n        "Specia'
        b'lToken": {\n          "id": "[SEP'
        b']",\n          "type_id": 0\n     '
        b'   }\n      },\n      {\n        "S'
        b'equence": {\n          "id": "B",'
        b'\n          "type_id": 1\n        '
        b'}\n      },\n      {\n        "Spec'
        b'ialToken": {\n          "id": "[S'
        b'EP]",\n          "type_id": 1\n   '
        b'     }\n      }\n    ],\n    "speci'
        b'al_tokens": {\n      "[CLS]": {\n '
        b'       "id": "[CLS]",\n        "i'
        b'ds": [\n          1\n        ],\n  '
        b'      "tokens": [\n          "[CL'
        b'S]"\n        ]\n      },\n      "[S'
        b'EP]": {\n        "id": "[SEP]",\n '
        b'       "ids": [\n          2\n    '
        b'    ],\n        "tokens": [\n     '
        b'     "[SEP]"\n        ]\n      }\n '
        b'   }\n  },\n  "decoder": null,\n  "'
        b'model": {\n    "type": "WordLevel'
        b'",\n    "vocab": {\n      "[UNK]":'
        b' 0,\n      "[CLS]": 1,\n      "[SE'
        b'P]": 2,\n      "hello": 3,\n      '
        b'"caf\xc3\xa9": 4,\n      "\xe4\xb8\x96\xe7\x95\x8c": 5\n  '
        b'  },\n    "unk_token": "[UNK]"\n  '
        b"}\n}"
    ),
    (
        b'{\n  "version": "1.0",\n  "truncat'
        b'ion": {\n    "direction": "Right"'
        b',\n    "max_length": 5,\n    "stra'
        b'tegy": "LongestFirst",\n    "stri'
        b'de": 0\n  },\n  "padding": {\n    "'
        b'strategy": {\n      "Fixed": 20\n '
        b'   },\n    "direction": "Right",\n'
        b'    "pad_to_multiple_of": null,\n'
        b'    "pad_id": 0,\n    "pad_type_i'
        b'd": 0,\n    "pad_token": "<unk>"\n'
        b'  },\n  "added_tokens": [],\n  "no'
        b'rmalizer": null,\n  "pre_tokenize'
        b'r": {\n    "type": "Whitespace"\n '
        b' },\n  "post_processor": {\n    "t'
        b'ype": "TemplateProcessing",\n    '
        b'"single": [\n      {\n        "Spe'
        b'cialToken": {\n          "id": "<'
        b's>",\n          "type_id": 0\n    '
        b'    }\n      },\n      {\n        "'
        b'Sequence": {\n          "id": "A"'
        b',\n          "type_id": 0\n       '
        b' }\n      },\n      {\n        "Spe'
        b'cialToken": {\n          "id": "<'
        b'/s>",\n          "type_id": 0\n   '
        b'     }\n      }\n    ],\n    "pair"'
        b': [\n      {\n        "SpecialToke'
        b'n": {\n          "id": "<s>",\n   '
        b'       "type_id": 0\n        }\n  '
        b'    },\n      {\n        "Sequence'
        b'": {\n          "id": "A",\n      '
        b'    "type_id": 0\n        }\n     '
        b' },\n      {\n        "SpecialToke'
        b'n": {\n          "id": "</s>",\n  '
        b'        "type_id": 0\n        }\n '
        b'     },\n      {\n        "Special'
        b'Token": {\n          "id": "</s>"'
        b',\n          "type_id": 0\n       '
        b' }\n      },\n      {\n        "Seq'
        b'uence": {\n          "id": "B",\n '
        b'         "type_id": 1\n        }\n'
        b'      },\n      {\n        "Specia'
        b'lToken": {\n          "id": "</s>'
        b'",\n          "type_id": 1\n      '
        b'  }\n      }\n    ],\n    "special_'
        b'tokens": {\n      "</s>": {\n     '
        b'   "id": "</s>",\n        "ids": '
        b"[\n          2\n        ],\n       "
        b' "tokens": [\n          "</s>"\n  '
        b'      ]\n      },\n      "<s>": {\n'
        b'        "id": "<s>",\n        "id'
        b's": [\n          1\n        ],\n   '
        b'     "tokens": [\n          "<s>"'
        b"\n        ]\n      }\n    }\n  },\n  "
        b'"decoder": null,\n  "model": {\n  '
        b'  "type": "WordLevel",\n    "voca'
        b'b": {\n      "<unk>": 0,\n      "<'
        b's>": 1,\n      "</s>": 2,\n      "'
        b'hello": 3,\n      "caf\xc3\xa9": 4\n    '
        b'},\n    "unk_token": "<unk>"\n  }\n'
        b"}"
    ),
)

SEED_HASHES = (
    "1432b17ab7e9e4214568327a62acb0004515b6d23d920c3c8ed1150041f2ee32",
    "36583090527cd1a96fb0e9e576053ebece1a8621a7d788fdef6cb380a7e66153",
)
CUTOFFS = (1, 2, 20, 60)
VARIANTS = ("dense", "lexical", "fusion")


def cached_factory(tmp_path):
    root = os.environ["SLAIF_NATIVE_TEST_ROOT"]
    packages = os.environ["SLAIF_NATIVE_TEST_PACKAGES"]
    python = os.environ["SLAIF_NATIVE_TEST_PYTHON"]
    paths = []
    for name, data, digest in zip(("a.json", "b.json"), SEEDS, SEED_HASHES, strict=True):
        assert hashlib.sha256(data).hexdigest() == digest
        path = tmp_path / name
        path.write_bytes(data)
        paths.append(path)

    def definition(path, role="bge_body"):
        return native_tokenizers.Definition(
            path,
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "0.21.4",
            role,
            "synthetic-revision",
            "identity",
        )

    return paths, native_tokenizers.Runtime(Path(root), Path(packages), python), definition


class ObservationFailure(BaseException):
    """Observer assertions must not become an expected product refusal."""


def observe(validation, *args):
    try:
        return validation(*args)
    except Exception as exc:
        raise ObservationFailure("private observer assertion failed") from exc


def observe_workers(patch):
    """Record only subprocesses born inside this fixture and its Session closes."""
    births, sessions = [], []
    popen_init = subprocess.Popen.__init__
    session_init, session_close = (
        tokenizer_session.Session.__init__,
        tokenizer_session.Session.close,
    )

    def init_process(child, *args, **kwargs):
        event = {"state": "init_attempted", "child": child, "pid": None}
        births.append(event)
        try:
            popen_init(child, *args, **kwargs)
        finally:
            # Inspect only this exact object, even if Popen initialization failed.
            try:
                fields = vars(child)
                pid = fields.get("pid")
                created = fields.get("_child_created")
                event["pid"] = pid if type(pid) is int and pid > 0 else None
                event["created"] = created is True
                if created is True and event["pid"] is not None:
                    event["state"] = "initialized_handle"
                else:
                    event["state"] = "uncertain_partial_birth"
            except BaseException:
                # Observation must never replace the original Popen outcome.
                event["state"] = "uncertain_partial_birth"

    def init_session(session, *args, **kwargs):
        event = {"session": session, "close_returned": False}
        sessions.append(event)
        return session_init(session, *args, **kwargs)

    def close_session(session, *args, **kwargs):
        event = next((item for item in sessions if item["session"] is session), None)
        child = getattr(session, "_child", None)
        result = session_close(session, *args, **kwargs)
        if event is not None:
            event.update(close_returned=True, child=child)
        return result

    patch.setattr(subprocess.Popen, "__init__", init_process)
    patch.setattr(tokenizer_session.Session, "__init__", init_session)
    patch.setattr(tokenizer_session.Session, "close", close_session)
    return births, sessions


def reap_owned(births):
    """Reap only captured wrapper handles, with bounded termination on uncertainty."""
    first = None
    for event in births or ():
        child = event.get("child")
        if event.get("state") != "initialized_handle":
            first = prefer_cleanup_error(first, RuntimeError("owned subprocess birth uncertain"))
            continue
        try:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=0.4)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=0.4)
            event["returncode"] = child.wait(timeout=0.4)
        except BaseException as exc:
            event["reap_failed"] = True
            first = prefer_cleanup_error(first, exc)
    if first is not None:
        raise first


def prefer_cleanup_error(first, later):
    """Do not lose a non-Exception cleanup interruption behind an ordinary error."""
    if first is None:
        return later
    if isinstance(first, Exception) and not isinstance(later, Exception):
        cohort.safe_cleanup_note(later, "Earlier owned cleanup also failed")
        return later
    cohort.safe_cleanup_note(first, "Additional owned cleanup failed")
    return first


def test_evaluation_program_composition(tmp_path, monkeypatch):
    checkout = Path(__file__).resolve().parents[2]
    cohort.check_local_origins(checkout)
    expected = json.loads(
        (checkout / "docs/parallel/graded-evaluation-program-proof-oracle.json").read_bytes()
    )
    assert expected["totals"]["owner_check"] == 19
    owner = ctx = births = sessions = None
    factory_calls = []
    calls = []
    outer = []
    call_rows = []
    observed = []
    score_observations = {"nested": 0, "direct": 0}
    try:
        with monkeypatch.context() as patch:

            def factory(path):
                factory_calls.append(1)
                return cached_factory(path)

            patch.setattr(test_native_tokenizers, "make_native", factory)
            births, sessions = observe_workers(patch)
            ctx = fixture.make_owned_support(tmp_path)
        assert len(factory_calls) == 1
        assert len(births) == len(sessions) == 6
        assert all(item["state"] == "initialized_handle" for item in births)
        assert all(item["close_returned"] for item in sessions)
        assert {id(item["child"]) for item in sessions} == {id(item["child"]) for item in births}
        assert all(item["child"].poll() is not None for item in births)
        data, bundles = cohort.dataset_and_bundles(ctx)
        dataset = text_evaluation_dataset.admit(data)
        assert (dataset.case_count, dataset.gold_atom_count, len(bundles)) == (5, 7, 3)
        catalog = raw_snapshot_catalog.load_catalog(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id
        )
        rows = raw_snapshot_rows.parse(catalog.row_map_bytes).rows
        by_source = {}
        for row in rows:
            bundle = ingestion_store.load(ctx.originals, ctx.derived, row.bundle_container_id)
            by_source[bundle.revision.source.logical_id] = (row, bundle.scope)
        assert set(by_source) == {"a", "b", "c"}
        a, b, c = (by_source[name][0].chunk_id for name in ("a", "b", "c"))
        assert (a, c, b) == ctx.chunk_ids and len({a, b, c}) == 3
        restrictions = provenance_records.Restrictions(
            schema_version=1, corpora=None, versions=None
        )
        assert ctx.grants == provenance_records.Grants(
            schema_version=1, corpora=("one", "two"), versions=("v1",), labels=("secret",)
        )
        effective = ctx.denied_grants
        assert effective == provenance_records.Grants(
            schema_version=1, corpora=("one",), versions=("v1",), labels=()
        )
        assert all(
            provenance_records.reader_allows(by_source[x][1], effective, restrictions)
            for x in ("a", "c")
        )
        assert not provenance_records.reader_allows(by_source["b"][1], effective, restrictions)
        core = json.loads(
            (Path(ctx.root) / "snapshots" / ctx.snapshot_id[7:] / ".core.json").read_bytes()
        )
        embedding = core["embedding"]
        ids = tuple(
            embedding[key]
            for key in (
                "space_id",
                "definition_fingerprint",
                "query_policy_fingerprint",
                "query_execution_fingerprint",
            )
        )
        payload = struct.pack("<1024f", 0.6, 0, 0.8, *([0.0] * 1021))
        selected = selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, None
        )
        owner = pin.PinOwner()
        captured = owner.acquire_selected_data(ctx.originals, ctx.derived, ctx.root)
        assert captured.pointer == selected.pointer and owner.check() is captured
        chosen = runner.Cohort("held_out", ("h1", "h4"))
        queries = tuple(runner.Query(case, payload, *ids) for case in chosen.case_ids)
        args = (ctx.originals, ctx.derived, ctx.root, owner, data, chosen, queries, bundles)
        options = dict(
            grants=ctx.grants,
            restrictions=restrictions,
            config=runner.Config("synthetic-cohort", "structural-only"),
            budget=cohort.cohort_budget(),
            deadline_ms=1200000,
        )
        plan = program.Plan(
            "plan",
            dataset.dataset_id,
            dataset.split_id,
            ctx.snapshot_id,
            captured.pointer.generation,
            catalog.catalog_id,
            "protocol",
            "UNJUDGED_AS_ZERO_DIAGNOSTIC",
            "EXPLICIT_CHUNK_IDS_ONLY",
            CUTOFFS,
            (program.Judgments("h1", ((a, 3),)), program.Judgments("h4", ())),
        )
        grade_budget = program.GradeBudget(*program._MAX_BUDGET)
        # Observations execute outside delegates and cannot be swallowed as refusals.
        case_questions = {item["case_id"]: item["question"] for item in json.loads(data)["cases"]}

        def verify_runner(name, values, kwargs, result):
            if name == "_owner_check":
                assert values[0] is owner and result is captured
            elif name == "_produce":
                index = calls.count("_produce") - 1
                case_id = chosen.case_ids[index]
                assert values[:4] == (ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id)
                assert values[4] == case_questions[case_id] and values[5] == payload
                assert kwargs["grants"] == effective and kwargs["restrictions"] == restrictions
                assert (
                    tuple(
                        kwargs[key]
                        for key in (
                            "query_space_id",
                            "query_definition_fingerprint",
                            "query_policy_id",
                            "query_execution_fingerprint",
                        )
                    )
                    == ids
                )
                assert tuple(
                    kwargs[key] for key in ("dense_k", "lexical_k", "partition_cap", "k", "trace")
                ) == (60, 60, 60, 60, True)
                assert (result.snapshot_id, result.catalog_id) == (
                    ctx.snapshot_id,
                    catalog.catalog_id,
                )
                assert result.query_text_sha256 == hashlib.sha256(values[4].encode()).hexdigest()
                assert result.query_payload_sha256 == hashlib.sha256(payload).hexdigest()
                assert (
                    result.authority_sha256
                    == hashlib.sha256(
                        cohort.canonical(
                            [
                                effective.model_dump(mode="json"),
                                restrictions.model_dump(mode="json"),
                            ]
                        )
                    ).hexdigest()
                )
                query_wire = dict(
                    kind="raw-hybrid-query/v1",
                    snapshot_id=ctx.snapshot_id,
                    catalog_id=catalog.catalog_id,
                    query_text_sha256=result.query_text_sha256,
                    query_payload_sha256=result.query_payload_sha256,
                    query_space_id=ids[0],
                    query_definition_fingerprint=ids[1],
                    query_policy_id=ids[2],
                    query_execution_fingerprint=ids[3],
                    authority_sha256=result.authority_sha256,
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
                assert tuple(hit.chunk_id for hit in result.dense.hits) == (c, a)
                assert tuple(hit.chunk_id for hit in result.lexical.hits) == (c,)
                assert tuple(hit.chunk_id for hit in result.fusion.hits) == (c, a)
                observed.append((case_id, result.query_id))
            elif name == "_bind":
                assert values[:4] == (ctx.originals, ctx.derived, ctx.root, owner)
                assert values[4] == data and values[6] == bundles and values[8] == payload
                assert kwargs["grants"] == ctx.grants and kwargs["restrictions"] == restrictions
                assert result.geometry.chunk_metric_reason == "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING"
                assert result.geometry.stage_origin == "SUPPLIED_STAGE_RELATIONS_ONLY"
                assert result.qualification == "NOT_QUALIFIED"

        for name in ("_owner_check", "_produce", "_bind", "_aggregate"):
            delegate = getattr(runner, name)

            def measured(*values, _name=name, _delegate=delegate, **kwargs):
                calls.append(_name)
                result = _delegate(*values, **kwargs)
                observe(verify_runner, _name, values, kwargs, result)
                return result

            monkeypatch.setattr(runner, name, measured)
        original_catalog = program._catalog
        original_load_catalog = raw_snapshot_catalog.load_catalog
        original_bind = source_bound_ranking.bind
        original_case = program._case
        original_aggregate = metrics.aggregate
        original_score = metrics.score_query
        grading, in_aggregate, in_catalog = [False], [False], [False]
        aggregates = []

        def counted_catalog(*values, **kwargs):
            in_catalog[0] = True
            try:
                return original_catalog(*values, **kwargs)
            finally:
                in_catalog[0] = False

        def counted_load_catalog(*values, **kwargs):
            if in_catalog[0]:
                calls.append("catalog")
            return original_load_catalog(*values, **kwargs)

        def counted_case(*values, **kwargs):
            grading[0] = True
            try:
                return original_case(*values, **kwargs)
            finally:
                grading[0] = False

        def verify_bind_input(values, kwargs):
            assert values[:5] == (
                ctx.originals,
                ctx.derived,
                ctx.root,
                ctx.snapshot_id,
                catalog.catalog_id,
            )
            assert values[5] in ((a,), (), (b,))
            assert kwargs["grants"] == effective and kwargs["restrictions"] == restrictions

        def verify_bind_output(values, result):
            assert (result.snapshot_id, result.catalog_id) == (ctx.snapshot_id, catalog.catalog_id)
            assert tuple(row.chunk_id for row in result.rows) == values[5]
            assert (
                result.authority_sha256
                == hashlib.sha256(
                    cohort.canonical(
                        [effective.model_dump(mode="json"), restrictions.model_dump(mode="json")]
                    )
                ).hexdigest()
            )
            for row in result.rows:
                expected_row = by_source["a"][0] if row.chunk_id == a else by_source["b"][0]
                assert (
                    row.revision_id,
                    row.extraction_id,
                    row.representation_id,
                    row.bundle_container_id,
                ) == (
                    expected_row.revision_id,
                    expected_row.extraction_id,
                    expected_row.representation_id,
                    expected_row.bundle_container_id,
                )
                assert row.fragments

        def counted_bind(*values, **kwargs):
            if grading[0]:
                calls.append("grade_bind")
                observe(verify_bind_input, values, kwargs)
            result = original_bind(*values, **kwargs)
            if grading[0]:
                observe(verify_bind_output, values, result)
            return result

        def counted_aggregate(*values, **kwargs):
            calls.append("metrics")
            in_aggregate[0] = True
            try:
                result = original_aggregate(*values, **kwargs)
            finally:
                in_aggregate[0] = False
            aggregates.append(result)
            return result

        def counted_score(*values, **kwargs):
            key = "nested" if in_aggregate[0] else "direct"
            score_observations[key] += 1
            if key == "direct":
                raise ObservationFailure("unexpected direct score")
            return original_score(*values, **kwargs)

        monkeypatch.setattr(program, "_catalog", counted_catalog)
        monkeypatch.setattr(raw_snapshot_catalog, "load_catalog", counted_load_catalog)
        monkeypatch.setattr(program, "_case", counted_case)
        monkeypatch.setattr(source_bound_ranking, "bind", counted_bind)
        monkeypatch.setattr(metrics, "aggregate", counted_aggregate)
        monkeypatch.setattr(metrics, "score_query", counted_score)

        def count():
            names = (
                "_owner_check",
                "_produce",
                "_bind",
                "_aggregate",
                "catalog",
                "grade_bind",
                "metrics",
            )
            return tuple(calls.count(name) for name in names)

        def record(expected_counts):
            actual = count()
            assert actual == expected_counts
            call_rows.append(actual)

        def graded(chosen_plan):
            return program.run_evaluation(
                *args, **options, plan=chosen_plan, grade_budget=grade_budget
            )

        legacy = runner.run_cohort(*args, **options)
        outer.append("legacy")
        record((3, 2, 2, 1, 0, 0, 0))
        calls.clear()
        observed.clear()
        report = graded(plan)
        outer.append("graded")
        record((9, 2, 2, 1, 1, 2, 3))
        assert len(aggregates) == 3
        wire = json.loads(report.identity_payload)
        assert report.plan_identity == wire["plan_identity"]
        assert (wire["plan_id"], wire["protocol_id"]) == (plan.plan_id, plan.protocol_id)
        assert all(
            status in ("NOT_RUN", "DECLARED_UNVERIFIED", "NOT_CHECKED", "NOT_QUALIFIED")
            for status in wire["statuses"].values()
        )
        assert all(
            question.encode() not in report.identity_payload for question in case_questions.values()
        )
        assert (
            report.identity
            == "sha256:"
            + hashlib.sha256(
                b"slaif-graded-evaluation-program-v1\n" + report.identity_payload
            ).hexdigest()
        )
        assert report.identity_payload.count(b'"source_payload":') == 1
        assert b'"source_payload":' + legacy.identity_payload + b"," in report.identity_payload
        assert (
            wire["source_identity"],
            wire["source_final_work"],
            wire["source_final_payload"],
        ) == (legacy.identity, legacy.final_work, legacy.final_payload)
        assert (
            wire["dataset_id"],
            wire["split_id"],
            wire["snapshot_id"],
            wire["generation"],
            wire["catalog_id"],
        ) == (
            dataset.dataset_id,
            dataset.split_id,
            captured.pointer.snapshot_id,
            captured.pointer.generation,
            catalog.catalog_id,
        )
        assert [item["query_id"] for item in wire["cases"]] == [item[1] for item in observed]
        original_hash = hashlib.sha256(
            cohort.canonical(
                [ctx.grants.model_dump(mode="json"), restrictions.model_dump(mode="json")]
            )
        ).hexdigest()
        effective_hash = hashlib.sha256(
            cohort.canonical(
                [effective.model_dump(mode="json"), restrictions.model_dump(mode="json")]
            )
        ).hexdigest()
        assert all(
            item["original_authority_sha256"] == original_hash
            and item["effective_authority_sha256"] == effective_hash
            for item in wire["cases"]
        )
        assert wire["selection"] == "DECLARED_SUBSET" and wire["selected_case_count"] == 2
        source_wire = json.loads(legacy.identity_payload)
        assert source_wire["selection_kind"] == "DECLARED_SUBSET"
        assert (
            source_wire["dataset_case_count"],
            source_wire["dataset_gold_occurrences"],
            source_wire["selected_count"],
        ) == (5, 7, 2)
        assert source_wire["statuses"]["encoder"] == "NOT_QUALIFIED"
        assert wire["unknown_policy"] == "UNJUDGED_AS_ZERO_DIAGNOSTIC"
        assert wire["overlap_policy"] == "EXPLICIT_CHUNK_IDS_ONLY"
        for variant, aggregate in zip(VARIANTS, aggregates, strict=True):
            assert (
                aggregate.total_queries,
                aggregate.defined_queries,
                aggregate.undefined_empty_gold_queries,
            ) == (2, 1, 1)
            by_query = {result.query_id: result for result in aggregate.query_results}
            for case_id, query_id in observed:
                gold = ((a, 3),) if case_id == "h1" else ()
                ranking = (c,) if variant == "lexical" else (c, a)
                from test_source_graded_rank_composition import check_query

                check_query(by_query[query_id], variant, query_id, gold, ranking)
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
        calls.clear()
        invalid = dataclasses.replace(
            plan, judgments=(plan.judgments[0], program.Judgments("h4", ((b, True),)))
        )
        with pytest.raises(program.EvaluationError) as error:
            graded(invalid)
        outer.append("invalid")
        assert type(error.value) is program.EvaluationError and error.value.args == (
            "evaluation program refused",
        )
        assert error.value.progress is None and error.value.__context__ is None
        record((0,) * 7)
        calls.clear()
        ineligible = dataclasses.replace(
            plan, judgments=(plan.judgments[0], program.Judgments("h4", ((b, 0),)))
        )
        with pytest.raises(program.EvaluationError) as error:
            graded(ineligible)
        outer.append("ineligible")
        assert type(error.value) is program.EvaluationError and error.value.args == (
            "evaluation program refused",
        )
        assert error.value.__context__ is None
        assert error.value.progress == program.FailurePrefix("GRADE_BIND", 2, 2, 1, 1, 0)
        record((7, 2, 2, 0, 1, 2, 0))
        owner.close()
        calls.clear()
        with pytest.raises(program.EvaluationError) as error:
            graded(plan)
        outer.append("closed")
        assert type(error.value) is program.EvaluationError and error.value.args == (
            "evaluation program refused",
        )
        assert error.value.__context__ is None
        assert error.value.progress == program.FailurePrefix("CATALOG", 2, 0, 0, 0, 2)
        record((0,) * 7)
        assert tuple(map(sum, zip(*call_rows, strict=True))) == (19, 6, 6, 2, 2, 4, 3)
        assert outer == ["legacy", "graded", "invalid", "ineligible", "closed"]
        assert score_observations["direct"] == 0
        cohort.check_local_origins(checkout)
    finally:
        body = sys.exception()

        def close_pin():
            if owner is not None and owner.state != "CLOSED":
                owner.close()

        def close_stores():
            if ctx is not None:
                source_fixture.close_owned_stores(ctx.derived, ctx.originals, None)

        def close_and_reap():
            first = None
            try:
                close_stores()
            except BaseException as exc:
                first = exc
            for session in sessions or ():
                if not session["close_returned"]:
                    try:
                        session["session"].close()
                        session["close_returned"] = True
                    except BaseException as exc:
                        first = prefer_cleanup_error(first, exc)
            try:
                reap_owned(births)
            except BaseException as exc:
                first = prefer_cleanup_error(first, exc)
            if first is not None:
                raise first

        def write_log(failures):
            lifecycle = {
                "factory_calls": len(factory_calls),
                "session_calls": len(sessions or ()),
                "births": [
                    {key: item.get(key) for key in ("state", "pid", "returncode", "reap_failed")}
                    for item in (births or ())
                ],
                "session_closes": [item["close_returned"] for item in (sessions or ())],
                "outer": outer,
                "direct_call_rows": call_rows,
                "direct_score_calls": score_observations["direct"],
                "cleanup_failures": failures,
            }
            (tmp_path / "fixture-lifecycle.json").write_text(json.dumps(lifecycle, sort_keys=True))

        cleanup = None
        failures = []
        for label, operation in (("pin", close_pin), ("stores_and_wrappers", close_and_reap)):
            try:
                operation()
            except BaseException as exc:
                failures.append({"operation": label, "type": type(exc).__name__})
                cleanup = prefer_cleanup_error(cleanup, exc)
                if body is not None:
                    cohort.safe_cleanup_note(body, "Owned " + label + " cleanup failed")
        try:
            write_log(failures)
        except BaseException as exc:
            cleanup = prefer_cleanup_error(cleanup, exc)
            if body is not None:
                cohort.safe_cleanup_note(body, "Private lifecycle record failed")
        if body is None and cleanup is not None:
            raise cleanup
