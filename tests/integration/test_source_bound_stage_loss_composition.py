"""Source-bound stage composition with owned synthetic data; no model execution."""

# This fixture establishes the normal unit-helper path before other helper imports.
import test_retrieval_representation_composition as representation_fixture

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

import pytest

from slaif_raggedized_helper import declared_stage_geometry as geometry
from slaif_raggedized_helper import derived_store, embedding_batch_store, ingestion_store
from slaif_raggedized_helper import raw_hybrid_search as hybrid
from slaif_raggedized_helper.source_admission import OriginalStore
from slaif_raggedized_helper import raw_snapshot_catalog, raw_snapshot_directory
from slaif_raggedized_helper import raw_snapshot_source_rows
from slaif_raggedized_helper import raw_snapshot_pin as pin
from slaif_raggedized_helper import raw_snapshot_selection as selection
from slaif_raggedized_helper import source_bound_ranking as rank
from slaif_raggedized_helper import source_bound_stage_loss as binder
from slaif_raggedized_helper import text_evaluation_gold_binding as gold
from slaif_raggedized_helper import tokenizer_session
import test_native_tokenizers
import test_raw_hybrid_search_composition as source_fixture
import test_source_bound_support_ci_composition as fixture
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401


class CeilingExceeded(BaseException):
    """Do not delegate beyond an approved, derived ceiling."""


def trace_hash(trace, kind):
    names = ("snapshot_id", "catalog_id") + (
        (
            "query_payload_sha256",
            "query_space_id",
            "query_definition_fingerprint",
            "query_policy_id",
            "query_execution_fingerprint",
            "authority_sha256",
        )
        if kind == "dense"
        else ("query_text_sha256", "analyzer_fingerprint", "backend", "method", "authority_sha256")
    )
    domain = "slaif-raw-" + kind + "-authorized-trace-v1"
    obj = dict(
        schema=1,
        kind=domain,
        **{n: getattr(trace, n) for n in names},
        k=trace.k,
        partition_cap=trace.partition_cap,
        rows=[asdict(row) for row in trace.rows],
        partitions=[asdict(part) for part in trace.partitions],
        selected_ordinals=trace.selected_ordinals,
        returned_ordinals=trace.returned_ordinals,
    )
    data = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return "sha256:" + hashlib.sha256(domain.encode() + b"\n" + data).hexdigest()


def project(modality, kind, *, drop_eligible=(), drop_ranked=()):
    """Rebuild a self-consistent supplied modality without consulting a source or producer."""
    old = modality.trace
    rows = tuple(r for r in old.rows if r.ordinal not in drop_eligible)
    eligible = {r.ordinal for r in rows}
    parts = []
    for p in old.partitions:
        e = tuple(x for x in p.eligible_ordinals if x in eligible)
        if not e:
            continue
        ranked = tuple(x for x in p.ranked_ordinals if x in eligible and x not in drop_ranked)
        selected = ranked[: old.partition_cap]
        parts.append(
            replace(
                p,
                eligible_ordinals=e,
                ranked_ordinals=ranked,
                selected_ordinals=selected,
                returned_ordinals=(),
            )
        )
    selected_set = {x for p in parts for x in p.selected_ordinals}
    selected = tuple(x for x in old.selected_ordinals if x in selected_set)
    returned = selected[: old.k]
    parts = tuple(
        replace(p, returned_ordinals=tuple(x for x in returned if x in p.eligible_ordinals))
        for p in parts
    )
    trace = replace(
        old, rows=rows, partitions=parts, selected_ordinals=selected, returned_ordinals=returned
    )
    trace = replace(trace, trace_id=trace_hash(trace, kind))
    hits_by_ordinal = {h.ordinal: h for h in modality.hits}
    hits = tuple(replace(hits_by_ordinal[x], rank=i) for i, x in enumerate(returned, 1))
    counts = []
    for part in parts:
        orig = next(
            c
            for c in (modality.allowed_partition_counts if kind == "dense" else modality.partitions)
            if c.partition_id == part.partition_id
        )
        changes = dict(
            eligible=len(part.eligible_ordinals),
            selected=len(part.selected_ordinals),
            returned=len(part.returned_ordinals),
        )
        if kind == "lexical":
            changes["matching"] = len(part.ranked_ordinals)
        counts.append(replace(orig, **changes))
    changes = dict(
        trace=trace,
        hits=hits,
        eligible=len(rows),
        selected=len(selected),
        returned=len(returned),
        partition_cap_applied=False,
        global_cap_applied=False,
    )
    if kind == "dense":
        changes["allowed_partition_counts"] = tuple(counts)
    else:
        changes.update(
            partitions=tuple(counts), matching=sum(len(p.ranked_ordinals) for p in parts)
        )
    return replace(modality, **changes)


def assert_relations(modality, kind):
    trace = modality.trace
    assert trace.trace_id == trace_hash(trace, kind)
    assert trace.k == trace.partition_cap == 60
    assert tuple(r.ordinal for r in trace.rows) == tuple(sorted(r.ordinal for r in trace.rows))
    assert tuple(p.partition_id for p in trace.partitions) == tuple(
        sorted(p.partition_id for p in trace.partitions)
    )
    assert len({r.ordinal for r in trace.rows}) == len(trace.rows) == modality.eligible
    assert set(trace.selected_ordinals) == {
        o for p in trace.partitions for o in p.selected_ordinals
    }
    assert trace.returned_ordinals == trace.selected_ordinals[:60]
    assert tuple(h.ordinal for h in modality.hits) == trace.returned_ordinals
    assert tuple(h.rank for h in modality.hits) == tuple(range(1, len(modality.hits) + 1))
    counts = modality.allowed_partition_counts if kind == "dense" else modality.partitions
    assert len(counts) == len(trace.partitions)
    for part, count in zip(trace.partitions, counts, strict=True):
        assert part.partition_id == count.partition_id
        assert part.eligible_ordinals == tuple(
            r.ordinal for r in trace.rows if r.partition_id == part.partition_id
        )
        assert set(part.ranked_ordinals) <= set(part.eligible_ordinals)
        if kind == "dense":
            assert set(part.ranked_ordinals) == set(part.eligible_ordinals)
        else:
            assert count.matching == len(part.ranked_ordinals)
        assert part.selected_ordinals == part.ranked_ordinals[:60]
        assert part.returned_ordinals == tuple(
            o for o in trace.returned_ordinals if o in part.eligible_ordinals
        )
        assert (count.eligible, count.selected, count.returned) == (
            len(part.eligible_ordinals),
            len(part.selected_ordinals),
            len(part.returned_ordinals),
        )
    assert (modality.selected, modality.returned) == (
        len(trace.selected_ordinals),
        len(trace.returned_ordinals),
    )
    assert not modality.partition_cap_applied and not modality.global_cap_applied


def altered_results(result, a, c):
    d, lexical_result, f = result.dense, result.lexical, result.fusion
    a_ord = next(h.ordinal for h in d.hits if h.chunk_id == a)
    c_ord = next(h.ordinal for h in d.hits if h.chunk_id == c)
    assert [h.chunk_id for h in d.hits] == [c, a]
    assert [h.chunk_id for h in lexical_result.hits] == [c]
    assert [h.chunk_id for h in f.hits] == [c, a]
    # Only the complete eligible universe differs from source in the first mutation.
    nd = project(d, "dense", drop_eligible=(a_ord,))
    nl = project(lexical_result, "lexical", drop_eligible=(a_ord,))
    only_c = replace(f.hits[0], dense_rank=1, lexical_rank=1, score=1 / 61 + 1 / 61, rank=1)
    nf = replace(
        f,
        hits=(only_c,),
        dense_input_rows=1,
        lexical_input_rows=1,
        unique_candidates=1,
        overlap_candidates=1,
        returned=1,
        global_cap_applied=False,
    )
    omitted = replace(result, dense=nd, lexical=nl, fusion=nf)
    # Preserve both eligible universes and every dense byte; lexical matching alone differs.
    ml = project(lexical_result, "lexical", drop_ranked=(c_ord,))
    mh = tuple(
        replace(h, lexical_rank=None, score=1 / (60 + h.dense_rank), rank=i)
        for i, h in enumerate(f.hits, 1)
    )
    mf = replace(
        f,
        hits=mh,
        dense_input_rows=2,
        lexical_input_rows=0,
        unique_candidates=2,
        overlap_candidates=0,
        returned=2,
        global_cap_applied=False,
    )
    matching = replace(result, lexical=ml, fusion=mf)
    score = replace(
        result,
        fusion=replace(f, hits=(replace(f.hits[0], score=f.hits[0].score + 0.01), f.hits[1])),
    )
    modalities = (
        (d, "dense"),
        (lexical_result, "lexical"),
        (nd, "dense"),
        (nl, "lexical"),
        (ml, "lexical"),
    )
    for mod, kind in modalities:
        assert_relations(mod, kind)
    assert nd.trace.trace_id == trace_hash(nd.trace, "dense")
    assert nl.trace.trace_id == trace_hash(nl.trace, "lexical")
    assert ml.trace.trace_id == trace_hash(ml.trace, "lexical")
    assert {r.ordinal for r in nd.trace.rows} == {c_ord} == {r.ordinal for r in nl.trace.rows}
    assert matching.dense is d and ml.trace.rows == lexical_result.trace.rows
    assert all(
        not p.ranked_ordinals and not p.selected_ordinals and not p.returned_ordinals
        for p in ml.trace.partitions
    )
    assert (ml.eligible, ml.matching, ml.selected, ml.returned) == (2, 0, 0, 0)
    assert (
        nd.eligible,
        nd.selected,
        nd.returned,
        nl.eligible,
        nl.matching,
        nl.selected,
        nl.returned,
    ) == (1, 1, 1, 1, 1, 1, 1)
    assert (
        nf.dense_input_rows,
        nf.lexical_input_rows,
        nf.unique_candidates,
        nf.overlap_candidates,
        nf.returned,
    ) == (1, 1, 1, 1, 1)
    assert [h.score for h in nf.hits] == [1 / 61 + 1 / 61]
    assert [h.score for h in mh] == [1 / 61, 1 / 62]
    assert (
        score.dense is d
        and score.lexical is lexical_result
        and score.fusion.hits[1] == f.hits[1]
    )
    return omitted, matching, score


def assert_positive(value, result, ctx, captured, payload):
    assert (
        value.dataset_case_count,
        value.dataset_atom_occurrences,
        value.chosen_atom_occurrences,
        value.eligible_row_count,
    ) == (2, 3, 2, 2)
    assert (value.snapshot_id, value.catalog_id, value.generation) == (
        ctx.snapshot_id,
        ctx.catalog_id,
        captured.pointer.generation,
    )
    assert value.pointer_sha256 == hashlib.sha256(captured.pointer.pointer_bytes).hexdigest()
    assert value.question_sha256 == hashlib.sha256(b"DistinctiveZephyr").hexdigest()
    assert value.payload_sha256 == hashlib.sha256(payload).hexdigest()
    assert value.query_id == result.query_id
    assert value.dense_trace_id == result.dense.trace.trace_id
    assert value.lexical_trace_id == result.lexical.trace.trace_id
    assert value.source_status == "OWNED_BINDING_CALLS_ONLY"
    assert value.qualification == "NOT_QUALIFIED"
    g = value.geometry
    names = (
        "dense.eligible",
        "dense.ranked",
        "dense.selected",
        "dense.returned",
        "lexical.eligible",
        "lexical.ranked",
        "lexical.selected",
        "lexical.returned",
        "fusion.input",
        "fusion.returned",
    )
    assert tuple(s.name for s in g.stages) == names
    expected = (("first", "second"),) * 5 + (("second",),) * 3 + (("first", "second"),) * 2
    for stage, ids in zip(g.stages, expected, strict=True):
        assert stage.coverage.covered_requirement_ids == ids
        assert stage.coverage.requirement_fraction == len(ids) / 2
        assert stage.completion.recall == len(ids) / 2
    assert tuple((s.name, s.cutoff) for s in g.prefixes) == tuple(
        (name, k)
        for name in ("dense.returned", "lexical.returned", "fusion.returned")
        for k in (20, 60)
    )
    assert tuple(s.coverage.requirement_fraction for s in g.prefixes) == (1, 1, 0.5, 0.5, 1, 1)
    assert len(g.transitions) == 7
    for i, transition in enumerate(g.transitions):
        assert transition.lost_requirements == (("first",) if i == 3 else ())
        assert transition.lost_alternatives == ((("first", 0),) if i == 3 else ())
        assert transition.gained_requirements == transition.gained_alternatives == ()
    assert (
        g.source_binding,
        g.eligibility,
        g.execution,
        g.qualification,
        g.chunk_metric_reason,
    ) == (
        "UNVERIFIED",
        "NOT_CHECKED",
        "NOT_ATTESTED",
        "NOT_QUALIFIED",
        "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING",
    )


def test_source_bound_stage_loss_composition(tmp_path, monkeypatch):
    checkout = Path(__file__).resolve().parents[2]
    for module in (
        representation_fixture,
        test_native_tokenizers,
        source_fixture,
        fixture,
        binder,
        geometry,
        hybrid,
        gold,
        rank,
    ):
        assert Path(module.__file__).resolve().is_relative_to(checkout)
    # Conservative envelopes are derived in the lane accounting, not measurements.
    limits = dict(
        fixture=1,
        sources=1,
        generator=1,
        catalog=33,
        hybrid=1,
        dense=1,
        lexical=1,
        fusion=1,
        bind=8,
        gold=8,
        rank=8,
        pure=8,
        lower=104,
        session_init=6,
        session_count=49158,
        session_close=7,
        bundle=1402,
        source_load=1411,
        verified_original=1414,
        batch_load=792,
        pin_check=41,
        pin_setup=1,
        selection=2,
        store_init=2,
        store_close=2,
        pin_close=2,
        derived_load=2983,
        group=789,
        pin_init=1,
        directory=114,
        original_admit=3,
    )
    counts = {key: 0 for key in limits}
    completed = {key: 0 for key in limits}
    failed = {key: 0 for key in limits}
    close_overages = set()
    close_over_budget = {key: 0 for key in ("session_close", "store_close", "pin_close")}
    owned_children = []
    worker_cleanup = dict(attempted=0, reaped=0, failed=0)
    close_keys = {"session_close", "store_close", "pin_close"}
    progress = dict(attempted=0, completed=0)

    def guard(obj, name, key):
        actual = getattr(obj, name)

        def call(*args, **kwargs):
            counts[key] += 1
            if counts[key] > limits[key]:
                if key not in close_keys:
                    failed[key] += 1
                    raise CeilingExceeded(key)
                close_overages.add(key)
                close_over_budget[key] += 1
            if key == "session_close":
                child = getattr(args[0], "_child", None)
                if child is not None and all(child is not old for old in owned_children):
                    owned_children.append(child)
            succeeded = False
            try:
                result = actual(*args, **kwargs)
                succeeded = True
                return result
            finally:
                if succeeded:
                    completed[key] += 1
                else:
                    failed[key] += 1

        monkeypatch.setattr(obj, name, call)

    for obj, name, key in (
        (fixture, "make_owned_support", "fixture"),
        (source_fixture, "make_sources", "sources"),
        (test_native_tokenizers, "make_native", "generator"),
        (pin.PinOwner, "__init__", "pin_init"),
        (raw_snapshot_source_rows, "load_group", "group"),
        (tokenizer_session.Session, "__init__", "session_init"),
        (tokenizer_session.Session, "count", "session_count"),
        (tokenizer_session.Session, "close", "session_close"),
        (raw_snapshot_catalog, "load_catalog", "catalog"),
        (raw_snapshot_directory, "load_directory", "directory"),
        (OriginalStore, "admit", "original_admit"),
        (ingestion_store, "load", "bundle"),
        (embedding_batch_store, "load", "batch_load"),
        (OriginalStore, "read_verified", "source_load"),
        (OriginalStore, "_verified_original", "verified_original"),
        (derived_store.Store, "load", "derived_load"),
        (OriginalStore, "__init__", "store_init"),
        (derived_store.Store, "__init__", "store_init"),
        (OriginalStore, "close", "store_close"),
        (derived_store.Store, "close", "store_close"),
        (pin.PinOwner, "close", "pin_close"),
        (hybrid, "search", "hybrid"),
        (hybrid.dense, "search", "dense"),
        (hybrid.lexical, "search", "lexical"),
        (hybrid.fusion, "fuse", "fusion"),
        (binder, "bind_stages", "bind"),
        (gold, "bind", "gold"),
        (rank, "bind", "rank"),
        (geometry, "diagnose", "pure"),
        (geometry.declared_span_support, "score_case", "lower"),
        (pin.PinOwner, "check", "pin_check"),
        (pin.PinOwner, "acquire_selected_data", "pin_setup"),
        (selection, "compare_and_select_data", "selection"),
    ):
        guard(obj, name, key)
    owner = None
    ctx = None
    try:
        owner = pin.PinOwner()
        ctx = fixture.make_owned_support(tmp_path)
        data = json.loads(ctx.dataset)
        data["cases"][0]["question"] = "DistinctiveZephyr"
        data = fixture.wire(data)
        core_path = Path(ctx.root) / "snapshots" / ctx.snapshot_id[7:] / ".core.json"
        core = json.loads(core_path.read_bytes())
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
        captured = owner.acquire_selected_data(ctx.originals, ctx.derived, ctx.root)
        second = selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, first.pointer.pointer_bytes
        )
        assert captured.pointer == first.pointer and owner.check() == captured
        assert second.pointer.snapshot_id == captured.pointer.snapshot_id == ctx.snapshot_id
        assert second.pointer.generation == captured.pointer.generation + 1
        assert second.pointer.pointer_bytes != captured.pointer.pointer_bytes
        result = hybrid.search(
            ctx.originals,
            ctx.derived,
            ctx.root,
            ctx.snapshot_id,
            "DistinctiveZephyr",
            payload,
            **ids,
            grants=ctx.denied_grants,
            dense_k=60,
            lexical_k=60,
            partition_cap=60,
            k=60,
            trace=True,
        )
        a, c, b = ctx.chunk_ids
        assert b not in {h.chunk_id for h in result.dense.hits + result.lexical.hits}
        assert (result.dense.eligible, result.lexical.eligible, result.lexical.matching) == (
            2,
            2,
            1,
        )
        assert (
            result.fusion.dense_input_rows,
            result.fusion.lexical_input_rows,
            result.fusion.unique_candidates,
            result.fusion.overlap_candidates,
            result.fusion.returned,
        ) == (2, 1, 2, 1, 2)
        assert [h.score for h in result.fusion.hits] == [1 / 61 + 1 / 61, 1 / 62]
        assert (
            all(
                not x.partition_cap_applied and not x.global_cap_applied
                for x in (result.dense, result.lexical)
            )
            and not result.fusion.global_cap_applied
        )
        omitted, matching, score = altered_results(result, a, c)
        args = (
            ctx.originals,
            ctx.derived,
            ctx.root,
            owner,
            data,
            ctx.case_id,
            ctx.gold_bundle_ids,
            result,
            payload,
        )

        def attempt(supplied=result, refusal=False, validate=None):
            progress["attempted"] += 1
            call_args = (*args[:7], supplied, args[8])
            if refusal:
                with pytest.raises(
                    binder.StageBindingError, match="^source-bound stage diagnosis refused$"
                ) as err:
                    binder.bind_stages(*call_args, **ids, grants=ctx.grants)
                assert err.value.__cause__ is None and err.value.__suppress_context__
                value = None
            else:
                value = binder.bind_stages(*call_args, **ids, grants=ctx.grants)
                assert_positive(value, result, ctx, captured, payload)
            if validate is not None:
                validate()
            progress["completed"] += 1
            return value

        attempt()
        for mutation in (omitted, matching, score):
            before = counts["gold"]

            def before_gold():
                assert counts["gold"] == before

            attempt(mutation, refusal=True, validate=before_gold)
        blob_hash = hashlib.sha256((tmp_path / "source" / "c").read_bytes()).hexdigest()
        blob = ctx.originals.root / "blobs" / blob_hash
        hidden = blob.with_name("withdrawn-" + blob_hash)
        assert blob.is_file() and not hidden.exists()
        with monkeypatch.context() as patch:
            original_gold = gold.bind
            returned_gold = []
            rank_before, pure_before = counts["rank"], counts["pure"]

            def withdraw(*a, **kw):
                result_gold = original_gold(*a, **kw)
                returned_gold.append(result_gold)
                blob.rename(hidden)
                return result_gold

            def withdrawal_validated():
                assert len(returned_gold) == 1
                assert hidden.is_file() and not blob.exists()
                assert counts["rank"] == rank_before and counts["pure"] == pure_before

            patch.setattr(gold, "bind", withdraw)
            try:
                attempt(refusal=True, validate=withdrawal_validated)
            finally:
                body = sys.exception()
                try:
                    if hidden.exists():
                        hidden.rename(blob)
                except BaseException:
                    if body is None:
                        raise
                    body.add_note("Owned blob restoration failed.")
        attempt()
        with monkeypatch.context() as patch:
            original_init, original_rank = binder._Deadline.__init__, rank.bind
            captured_clock = []

            def clock_init(instance, *a, **kw):
                original_init(instance, *a, **kw)
                captured_clock.append(instance)

            def expire_after_rank(*a, **kw):
                result_rank = original_rank(*a, **kw)
                assert len(captured_clock) == 1
                captured_clock[0].end = 0
                return result_rank

            patch.setattr(binder._Deadline, "__init__", clock_init)
            patch.setattr(rank, "bind", expire_after_rank)
            pure_before = counts["pure"]

            def no_pure():
                assert len(captured_clock) == 1 and captured_clock[0].end == 0
                assert counts["pure"] == pure_before

            attempt(refusal=True, validate=no_pure)
        owner.close()
        attempt(refusal=True)
        assert progress == dict(attempted=8, completed=8)
    finally:
        body = sys.exception()
        cleanup = None
        try:
            if owner is not None and owner.state != "CLOSED":
                owner.close()
        except BaseException as exc:
            cleanup = exc
            if body is not None:
                body.add_note("Pin close failed; cleanup may be incomplete.")
        try:
            if ctx is not None:
                source_fixture.close_owned_stores(ctx.derived, ctx.originals, body or cleanup)
        except BaseException as exc:
            if cleanup is None:
                cleanup = exc
        for child in owned_children:
            worker_cleanup["attempted"] += 1
            try:
                errors = []
                reaped = False
                if child.poll() is None:
                    try:
                        child.terminate()
                    except ProcessLookupError:
                        pass
                    except BaseException as exc:
                        errors.append(exc)
                    try:
                        child.wait(timeout=0.4)
                        reaped = True
                    except BaseException as first_wait:
                        if not isinstance(first_wait, subprocess.TimeoutExpired):
                            errors.append(first_wait)
                        try:
                            child.kill()
                        except ProcessLookupError:
                            pass
                        except BaseException as exc:
                            errors.append(exc)
                        try:
                            child.wait(timeout=0.4)
                            reaped = True
                        except BaseException as exc:
                            if errors:
                                errors[0].add_note(
                                    "Second owned worker wait failed: " + type(exc).__name__
                                )
                            else:
                                errors.append(exc)
                else:
                    child.wait(timeout=0.4)
                    reaped = True
                if reaped:
                    worker_cleanup["reaped"] += 1
                if errors:
                    raise errors[0]
            except BaseException as exc:
                worker_cleanup["failed"] += 1
                if body is not None:
                    body.add_note("Owned native worker cleanup failed: " + type(exc).__name__)
                elif cleanup is None:
                    cleanup = exc
                else:
                    cleanup.add_note("Owned native worker cleanup also failed.")
        if len(owned_children) > limits["session_init"]:
            close_overages.add("owned_children")
        if close_overages:
            message = "Cleanup ceiling exceeded: " + ", ".join(sorted(close_overages))
            if body is not None:
                body.add_note(message)
            elif cleanup is not None:
                cleanup.add_note(message)
            else:
                cleanup = CeilingExceeded(message)
        try:
            print(
                "PRIVATE_STAGE_COUNTS",
                json.dumps(
                    dict(
                        attempted=counts,
                        completed=completed,
                        failed=failed,
                        limits=limits,
                        progress=progress,
                        close_overages=sorted(close_overages),
                        close_over_budget=close_over_budget,
                        worker_cleanup=worker_cleanup,
                    ),
                    sort_keys=True,
                ),
                flush=True,
            )
        except BaseException as exc:
            if body is not None:
                body.add_note("Private progress reporting failed.")
            elif cleanup is None:
                cleanup = exc
        if body is None and cleanup is not None:
            raise cleanup
