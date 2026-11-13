"""Private synthetic composition of actual retrieval and source-bound support."""

# This provider establishes the normal test helper path before other test imports.
import test_retrieval_representation_composition as representation_fixture

import hashlib
import json
from pathlib import Path
import struct
import sys
import time
from types import SimpleNamespace

import pytest

from slaif_raggedized_helper import ingestion_store, raw_snapshot_catalog, tokenizer_session
from slaif_raggedized_helper import raw_text_stage_support as stage
import test_native_tokenizers
import test_raw_hybrid_search_composition as source_fixture
import test_source_bound_support_ci_composition as fixture
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401


class CeilingExceeded(BaseException):
    """Stop before a delegated call exceeds the predeclared envelope."""


def test_raw_text_stage_support_composition(tmp_path, monkeypatch):
    checkout = Path(__file__).resolve().parents[2]
    for module in (representation_fixture, test_native_tokenizers, source_fixture, fixture, stage):
        assert Path(module.__file__).resolve().is_relative_to(checkout)

    counts = dict(
        generator=0,
        session_init=0,
        session_count=0,
        session_close=0,
        catalog=0,
        bundle=0,
        hybrid=0,
        dense=0,
        lexical=0,
        fusion=0,
        support=0,
    )
    ceilings = dict(
        generator=1,
        session_init=6,
        session_count=98304,
        session_close=64,
        catalog=160,
        bundle=5000,
        hybrid=7,
        dense=7,
        lexical=7,
        fusion=7,
        support=14,
    )
    observed = {"hybrid": [], "support": [], "authority": []}
    expired = [False]
    clock = time.monotonic

    def instrument(obj, name, key):
        actual = getattr(obj, name)

        def guarded(*args, **kwargs):
            counts[key] += 1
            if counts[key] > ceilings[key]:
                raise CeilingExceeded(key)
            if key in ("dense", "lexical"):
                authority = kwargs["grants"]
                assert set(authority.corpora) <= {"one"}
                assert set(authority.versions) <= {"v1"} and not authority.labels
                observed["authority"].append((key, authority))
            result = actual(*args, **kwargs)
            if key in ("hybrid", "support"):
                observed[key].append((args, kwargs, result))
            if key == "hybrid" and expired[0]:
                expired[0] = "returned"
            return result

        monkeypatch.setattr(obj, name, guarded)

    for obj, name, key in (
        (test_native_tokenizers, "make_native", "generator"),
        (tokenizer_session.Session, "__init__", "session_init"),
        (tokenizer_session.Session, "count", "session_count"),
        (tokenizer_session.Session, "close", "session_close"),
        (raw_snapshot_catalog, "load_catalog", "catalog"),
        (ingestion_store, "load", "bundle"),
        (stage.hybrid, "search", "hybrid"),
        (stage.dense, "search", "dense"),
        (stage.lexical, "search", "lexical"),
        (stage.fusion, "fuse", "fusion"),
        (stage.support, "score_case", "support"),
    ):
        instrument(obj, name, key)

    ctx = None
    initial = None
    withdrawal = None
    progress = {"attempted": 0, "completed": 0}
    owner = stage.pin.PinOwner()
    try:
        ctx = fixture.make_owned_support(tmp_path)
        original = json.loads(ctx.dataset)
        original["cases"][0]["question"] = "DistinctiveZephyr"
        dataset = fixture.wire(original)
        admitted = stage.datasets.admit(dataset)
        assert len(admitted.cases) == 2
        assert tuple(len(c.requirements) for c in admitted.cases) == (2, 1)
        core = json.loads(
            (Path(ctx.root) / "snapshots" / ctx.snapshot_id[7:] / ".core.json").read_bytes()
        )
        embedding = core["embedding"]
        payload = struct.pack("<1024f", 0.6, 0.0, 0.8, *([0.0] * 1021))
        first = stage.selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, None
        )
        captured = owner.acquire_selected_data(ctx.originals, ctx.derived, ctx.root)
        second = stage.selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, first.pointer.pointer_bytes
        )
        assert captured.pointer == first.pointer and owner.check() == captured
        assert second.pointer.snapshot_id == captured.pointer.snapshot_id == ctx.snapshot_id
        assert second.pointer.generation == captured.pointer.generation + 1
        assert second.pointer.pointer_bytes != captured.pointer.pointer_bytes
        assert (
            stage.selection.read_selected_data(ctx.originals, ctx.derived, ctx.root).pointer
            == second.pointer
        )

        kwargs = dict(
            query_space_id=embedding["space_id"],
            query_definition_fingerprint=embedding["definition_fingerprint"],
            query_policy_id=embedding["query_policy_fingerprint"],
            query_execution_fingerprint=embedding["query_execution_fingerprint"],
            grants=ctx.grants,
        )
        expected_a, expected_c, denied_b = ctx.chunk_ids
        assert len(set(ctx.chunk_ids)) == 3
        c_bundles = tuple(
            ident
            for ident in ctx.gold_bundle_ids
            if ingestion_store.load(ctx.originals, ctx.derived, ident).revision.source.logical_id
            == "c"
        )
        assert len(c_bundles) == 1
        effective = ctx.denied_grants
        initial = dict(counts)
        # Expected deltas before each call: successful a/b/c/f=(1,1,1,1,3);
        # d=(1,1,1,1,1); e may fail before or during the producer or its first
        # source binding; g=(1,1,1,1,0); h=(0,0,0,0,0).
        keys = ("hybrid", "dense", "lexical", "fusion", "support")

        def attempt(data, expected, *, refusal=False, bundles=None):
            progress["attempted"] += 1
            before = dict(counts)
            before_h = len(observed["hybrid"])
            before_s = len(observed["support"])
            args = (
                ctx.originals,
                ctx.derived,
                ctx.root,
                owner,
                data,
                ctx.case_id,
                ctx.gold_bundle_ids if bundles is None else bundles,
                payload,
            )
            if refusal:
                with pytest.raises(
                    stage.StageSupportError, match="^raw text stage support refused$"
                ) as err:
                    stage.evaluate_case(*args, **kwargs)
                assert err.value.__cause__ is None and err.value.__suppress_context__
                value = None
            else:
                value = stage.evaluate_case(*args, **kwargs)
            delta = tuple(counts[k] - before[k] for k in keys)
            if expected is not None:
                assert delta == expected
            else:
                # Withdrawn source can be detected by pin, producer, or first support.
                assert delta[0] in (0, 1) and all(x in (0, 1) for x in delta[1:])
                assert delta[4] <= delta[0] and delta[3] <= delta[0]
            progress["completed"] += 1
            return value, delta, observed["hybrid"][before_h:], observed["support"][before_s:]

        def positive(value, hybrid_calls, support_calls):
            assert len(hybrid_calls) == 1 and len(support_calls) == 3
            hargs, hkw, result = hybrid_calls[0]
            assert hargs[3:6] == (ctx.snapshot_id, "DistinctiveZephyr", payload)
            assert hkw["grants"] == effective
            assert [h.chunk_id for h in result.dense.hits] == [expected_c, expected_a]
            assert [h.chunk_id for h in result.lexical.hits] == [expected_c]
            assert [h.chunk_id for h in result.fusion.hits] == [expected_c, expected_a]
            assert denied_b not in {h.chunk_id for h in result.dense.hits + result.lexical.hits}
            assert tuple(v.name for v in value.variants) == ("dense", "lexical", "fusion")
            for v, (args, skw, item), ids, fraction in zip(
                value.variants,
                support_calls,
                ((expected_c, expected_a), (expected_c,), (expected_c, expected_a)),
                (1.0, 0.5, 1.0),
                strict=True,
            ):
                assert args[8] == ids and skw["grants"] == effective and v.support is item
                assert item.ranking_count == len(ids)
                assert (
                    item.case_requirement_count,
                    item.global_gold_atom_occurrences,
                    item.global_distinct_gold_atoms,
                ) == (2, 3, 3)
                assert tuple(x.k for x in item.at_k) == (20, 60)
                assert all(x.requirement_fraction == fraction for x in item.at_k)
                assert item.snapshot_id == value.snapshot_id and item.catalog_id == value.catalog_id
                assert item.authority_sha256 == value.effective_authority_sha256
            assert value.snapshot_id == ctx.snapshot_id and value.catalog_id == ctx.catalog_id
            assert (
                value.pointer_sha256 == hashlib.sha256(captured.pointer.pointer_bytes).hexdigest()
            )
            assert value.generation == captured.pointer.generation
            assert value.question_sha256 == hashlib.sha256(b"DistinctiveZephyr").hexdigest()
            assert value.query_payload_sha256 == hashlib.sha256(payload).hexdigest()
            assert value.hybrid_query_id == result.query_id
            assert value.original_authority_sha256 == stage.lexical._authority_hash(
                ctx.grants, None
            )
            assert value.effective_authority_sha256 == stage.lexical._authority_hash(
                effective, None
            )
            assert value.qualification == "NOT_QUALIFIED"

        ok = (1, 1, 1, 1, 3)
        a, _, ah, ass = attempt(dataset, ok)
        positive(a, ah, ass)
        empty = json.loads(dataset)
        empty["cases"][0]["scope"]["corpora"] = []
        b, _, bh, bs = attempt(fixture.wire(empty), ok)
        assert all(not x.hits for x in (bh[0][2].dense, bh[0][2].lexical, bh[0][2].fusion))
        assert all(args[8] == () for args, _, _ in bs)
        assert all(
            v.support.case_requirement_count == 2
            and all(x.requirement_fraction == 0 for x in v.support.at_k)
            for v in b.variants
        )
        no_gold = json.loads(dataset)
        no_gold["cases"][0]["requirements"] = []
        no_gold["cases"][0]["answerability"] = "unanswerable"
        no_gold["cases"][0]["acceptable_facts"] = []
        c, _, _, _ = attempt(fixture.wire(no_gold), ok, bundles=c_bundles)
        assert all(
            v.support.case_requirement_count == 0
            and v.support.global_gold_atom_occurrences == 1
            and all(
                x.requirement_fraction is None and x.undefined_reason == "NO_GOLD_REQUIREMENTS"
                for x in v.support.at_k
            )
            for v in c.variants
        )
        bad = json.loads(dataset)
        bad["cases"][1]["requirements"][0]["alternatives"][0][0]["text_sha256"] = "0" * 64
        _, _, dh, ds = attempt(fixture.wire(bad), (1, 1, 1, 1, 1), refusal=True)
        assert len(dh) == 1 and not ds
        blob_hash = hashlib.sha256((tmp_path / "source" / "c").read_bytes()).hexdigest()
        blob = ctx.originals.root / "blobs" / blob_hash
        hidden = blob.with_name("withdrawn-" + blob_hash)
        assert blob.is_file() and not hidden.exists()
        blob.rename(hidden)
        try:
            _, withdrawal, _, _ = attempt(dataset, None, refusal=True)
        finally:
            hidden.rename(blob)
        f, _, fh, fs = attempt(dataset, ok)
        positive(f, fh, fs)
        assert owner.check() == captured
        expired[0] = True
        with monkeypatch.context() as patch:
            patch.setattr(
                stage,
                "time",
                SimpleNamespace(
                    monotonic=lambda: clock() + (121 if expired[0] == "returned" else 0)
                ),
            )
            _, _, gh, gs = attempt(dataset, (1, 1, 1, 1, 0), refusal=True)
        assert expired[0] == "returned" and len(gh) == 1 and not gs
        owner.close()
        attempt(dataset, (0, 0, 0, 0, 0), refusal=True)
        assert counts["generator"] == 1 and counts["session_init"] == 6
    finally:
        body_failure = sys.exception()
        cleanup_failure = None
        try:
            if owner.state == "ACTIVE":
                owner.close()
        except BaseException as exc:
            cleanup_failure = exc
            if body_failure is not None:
                try:
                    BaseException.add_note(
                        body_failure, "Pin close failed; cleanup may be incomplete."
                    )
                except BaseException:
                    pass
        try:
            if ctx is not None:
                source_fixture.close_owned_stores(
                    ctx.derived, ctx.originals,
                    body_failure if body_failure is not None else cleanup_failure,
                )
        except BaseException as exc:
            if cleanup_failure is None:
                cleanup_failure = exc
        finally:
            try:
                print(
                    "COMPOSITION_PRIVATE_COUNTS",
                    json.dumps(
                        {
                            "counts": counts,
                            "ceilings": ceilings,
                            "progress": progress,
                            "withdrawal_delta": withdrawal,
                            "setup_counts": initial,
                            "pin_state": owner.state,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
            except BaseException as exc:
                if body_failure is None and cleanup_failure is None:
                    cleanup_failure = exc
        if body_failure is None and cleanup_failure is not None:
            raise cleanup_failure
