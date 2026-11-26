"""Owned private current-cohort encoder-to-producer composition proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The real
hosted source fixture (``make_owned_support`` from
``test_source_bound_support_ci_composition`` over the real
``make_sources``, with its bounded opt-in one fixture query identity
tuple at actual creation), the canonical five-case dataset and actual
bundle IDs (``dataset_and_bundles`` from
``test_source_cohort_runner_composition``), the actual raw snapshot
selector and the real ``PinOwner.acquire_selected_data`` build the
pinned data; the exact synthetic policy wire bytes are installed
through the existing payload installer and the attributed atomic
selection publication of ``test_current_gold_dispatch_composition``
publishes the selected record - it provides no writer qualification,
and the actual selected generation changes use the same-wire
generation change through that attributed fixture.  The actual guarded
encoder transport fixture of
``test_guarded_encoder_transport_composition`` and its visible
synthetic worker policy/identity provide the exact open
``ResidentQueryEncoder``; its space and definition are bound to the
real synthetic corpus batches and rows and its query policy and
execution are assigned to the core before materialization, while the
corpus vectors stay synthetic with their independently declared corpus
execution provenance.  Each fresh current admission is created only
after the expensive fixture setup that precedes its dispatch, with its
own initial selected read excluded from the counted span; the fixture
start, the inherited synthetic source authorship, the background
startup/renewal and the actual measured T1/T2/producer phases are kept
separate, and the counts run from the entry dispatch after fixture
acquisition.  Counting wrappers delegate the real bundle, derived,
original-store verified read, owner-load, delegated raw directory,
catalog and reader functions at the intended boundaries; the real T1
text and T2 token-ID transport writes are matched by live child pipe
identity against actual delegated kernel bytes.  No local native
witness execution: only the configured hosted CI executes the three
real hosted nodes, and local proof of this module is collection only.
"""
import hashlib
import json
import os
import struct
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import cpu_embedding_worker as cpu  # noqa: E402
from slaif_raggedized_helper import embedding_tokenizer  # noqa: E402
from slaif_raggedized_helper import ingestion_store  # noqa: E402
from slaif_raggedized_helper import private_policy_capture as capture  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import raw_hybrid_search as hybrid  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_catalog as catalog  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_directory  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_selection as selection  # noqa: E402
from slaif_raggedized_helper import source_bound_stage_loss as stage_loss  # noqa: E402
from slaif_raggedized_helper import source_cohort_runner as runner  # noqa: E402
from slaif_raggedized_helper import text_evaluation_dataset  # noqa: E402
from slaif_raggedized_helper.raw_snapshot_pin import PinOwner  # noqa: E402
import test_current_gold_dispatch_composition as gold_fixture  # noqa: E402
import test_guarded_encoder_transport_composition as transport  # noqa: E402
import test_source_bound_support_ci_composition as support_fixture  # noqa: E402
import test_source_cohort_runner_composition as cohort_fixture  # noqa: E402
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: E402,F401

# The selected held-out case of the canonical five-case fixture.  Its
# genuine FAKE-framework token IDs are observed at the real
# tokenizer/forward boundary, never assumed here, and through genuine
# normalization the expected one-row payload is 1024 copies of
# 0.03125 (float32).
QUESTION = "DistinctiveZephyr one?"
PAYLOAD = struct.pack("<1024f", *([1.0 / 32.0] * 1024))


def _identifiers(case_ids):
    # Well-shaped declared encoder identifier tuples under the exact
    # grammar the genuine declaration admission enforces (64 hex,
    # sha256-prefixed 64 hex, 64 hex, 64 hex), derived deterministically
    # per case ID: grammar-valid but distinct from the open resident's
    # actual identities and the concordant synthetic core by design.
    declared = []
    for case_id in case_ids:
        base = hashlib.sha256(("slaif-cep-ident:" + case_id).encode("ascii")).hexdigest()
        declared.append((
            hashlib.sha256((base + ":space").encode("ascii")).hexdigest(),
            "sha256:" + hashlib.sha256((base + ":definition").encode("ascii")).hexdigest(),
            hashlib.sha256((base + ":policy").encode("ascii")).hexdigest(),
            hashlib.sha256((base + ":execution").encode("ascii")).hexdigest(),
        ))
    return tuple(declared)


def _change_generation(policy_root, generation, payload):
    # The synthetic selected generation changes while the originally
    # installed policy payload bytes stay identical (same wire, same
    # raw pin), through the attributed fixture.
    gold_fixture._publish_selection(
        policy_root, generation, payload,
    )


def _scenario(tmp_path, monkeypatch, query_identity, *, withhold_two=True):
    """One real scenario: the real hosted source fixture with the
    bounded opt-in query identity, the canonical five-case dataset and
    actual bundle IDs, the actual raw snapshot selector, the real
    ``PinOwner.acquire_selected_data``, the exact synthetic policy wire
    and the actual capture reader; no admission yet, so each fresh
    current admission begins its lifetime only after the expensive
    fixture setup that precedes its dispatch.  The source fixture and
    its synthetic policy are isolated in their own separately created
    private directories under the test root, apart from the inherited
    resident synthetic assets and policy."""
    ctx = owner = None
    try:
        source_root = tmp_path / "source"
        source_root.mkdir(mode=0o700)
        ctx = support_fixture.make_owned_support(source_root,
                                                 query_identity=query_identity)
        dataset, bundle_ids = cohort_fixture.dataset_and_bundles(ctx)
        selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, None
        )
        owner = PinOwner()
        owner.acquire_selected_data(ctx.originals, ctx.derived, ctx.root,
                                    deadline_ms=30000)
        documents = gold_fixture._documents_from_membership(
            owner, withhold_two=withhold_two)
        policy_root, payload = gold_fixture._install_policy(
            source_root, "policy", documents)
        reader = capture.PolicyCaptureReader(str(policy_root))
        return ctx, dataset, bundle_ids, owner, policy_root, reader, payload
    except BaseException:
        if owner is not None:
            try:
                owner.close()
            except BaseException:
                pass
        if ctx is not None:
            for owned in (ctx.derived, ctx.originals):
                try:
                    owned.close()
                except BaseException:
                    pass
        raise


def _counts():
    return {"bundle": 0, "derived": 0, "original": 0, "pin_load": 0, "read": []}


def _zero(counts):
    return counts == {"bundle": 0, "derived": 0, "original": 0, "pin_load": 0,
                      "read": []}


def _install_counting(monkeypatch, ctx, owner, reader, counts, *,
                      change_after_read=None, change=None):
    """Counting wrappers that delegate the real functions at the
    intended boundaries; counts run from the entry dispatch after
    fixture acquisition.  ``change_after_read`` is the exact one-based
    genuine selected read index after whose successful completion
    ``change`` fires (the attributed same-wire generation change),
    kept separate from every other count.  No production hook is
    added.  Returns the restore closure for the genuine boundaries."""
    real_bundle = ingestion_store.load
    real_derived = ctx.derived.load
    real_original = ctx.originals.read_verified
    real_pin_load = owner._load
    real_read = capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader))

    def counting_bundle(*args, **kwargs):
        counts["bundle"] += 1
        return real_bundle(*args, **kwargs)

    def counting_derived(container_id):
        counts["derived"] += 1
        return real_derived(container_id)

    def counting_original(*args, **kwargs):
        counts["original"] += 1
        return real_original(*args, **kwargs)

    def counting_pin_load(snapshot_id):
        counts["pin_load"] += 1
        return real_pin_load(snapshot_id)

    def counting_read(*args, **kwargs):
        result = real_read(*args, **kwargs)
        counts["read"].append(1)
        if (change_after_read is not None and change is not None
                and len(counts["read"]) == change_after_read):
            change()
        return result

    monkeypatch.setattr(ingestion_store, "load", counting_bundle)
    monkeypatch.setattr(ctx.derived, "load", counting_derived)
    monkeypatch.setattr(ctx.originals, "read_verified", counting_original)
    monkeypatch.setattr(owner, "_load", counting_pin_load)
    monkeypatch.setattr(reader, "read_selection", counting_read)

    def restore():
        monkeypatch.setattr(ingestion_store, "load", real_bundle)
        monkeypatch.setattr(ctx.derived, "load", real_derived)
        monkeypatch.setattr(ctx.originals, "read_verified", real_original)
        monkeypatch.setattr(owner, "_load", real_pin_load)
        monkeypatch.setattr(reader, "read_selection", real_read)

    return restore


def _directory_counts(monkeypatch):
    """The actual delegated raw directory load starts and successful
    completions for the measured span, kept separate from the fixture
    baseline that ran before the witnesses."""
    counts = {"start": 0, "done": 0}
    real = raw_snapshot_directory.load_directory

    def counting(*args, **kwargs):
        counts["start"] += 1
        result = real(*args, **kwargs)
        counts["done"] += 1
        return result

    monkeypatch.setattr(raw_snapshot_directory, "load_directory", counting)
    return counts


def _catalog_counts(monkeypatch):
    """Real catalog loads classified by their direct caller module: the
    hybrid body's direct loads versus the engines' nested loads."""
    counts = {"direct": 0, "nested": 0}
    actual = catalog.load_catalog

    def counted(*args, **kwargs):
        module = sys._getframe(1).f_globals.get("__name__", "")
        if module == "slaif_raggedized_helper.raw_hybrid_search":
            counts["direct"] += 1
        else:
            counts["nested"] += 1
        return actual(*args, **kwargs)

    monkeypatch.setattr(catalog, "load_catalog", counted)
    return counts


def _shapes(owner):
    """Exact fixture shapes from the actual held pin data the fixture
    already captured, with no additional catalog or source work: M
    membership entries, B unique row-map bundles, G unique
    (bundle, batch) groups and P unique (partition, bundle, batch)
    triples."""
    data = owner.value.data
    m = len(data.membership.entries)
    rows = data.row_map.rows
    bundles = {r.bundle_container_id for r in rows}
    groups = {(r.bundle_container_id, r.batch_container_id) for r in rows}
    triples = {(r.partition_id, r.bundle_container_id, r.batch_container_id)
               for r in rows}
    return m, len(bundles), len(groups), len(triples)


def _per_directory(m, _b, _g, p):
    """The real full-directory work shape: M + 2*P ingestions
    (membership revalidation plus the dense and lexical partition
    rebuilds), every structured-text ingestion verifying one original
    and every source group loading its bundle and both of its stored
    derived snapshots."""
    ingestions = m + 2 * p
    return (ingestions, ingestions + 4 * p, ingestions)


def _per_catalog(m, b, g, p):
    """The exact source-derived per-catalog-load counts: both
    load_directory trees revalidate the whole declared membership and
    rebuild every partition through one real load_group, plus the two
    direct loops over every unique row-map bundle and every unique
    (bundle, batch) group, each through one real load_group; every
    real structured-text ingestion verifies one original."""
    loads = 2 * m + b + 2 * g + 4 * p
    return (loads, loads + 2 * (g + 4 * p), loads)


def _producer(admission, owner, dataset, bundle_ids, case_ids, identifiers,
              encoder, case_id):
    cohort = runner.Cohort("held_out", tuple(case_ids))
    return runner._current_cohort_encoder_producer(
        admission, owner, dataset, cohort, identifiers, bundle_ids,
        runner.Config("cep-cfg", "cep-declaration"),
        runner.Budget(*runner._MAX_BUDGET), encoder, case_id,
    )


def _refusal_prefix(progress):
    return (progress.phase, progress.intended, progress.attempted,
            progress.completed, progress.refused, progress.pending)


def _install_producer_counter(patched, calls):
    actual = hybrid.search_pinned_case

    def counting(*args, **kwargs):
        calls.append(kwargs.get("query_payload", args[4]))
        return actual(*args, **kwargs)

    patched.setattr(hybrid, "search_pinned_case", counting)


def test_encoder_producer_positive_binds_resident_and_matches_unguarded(
        tmp_path, monkeypatch):
    real_argv = cpu._argv
    encoder_root = tmp_path / "encoder"
    encoder_root.mkdir(mode=0o700)
    sc = transport._scenario(encoder_root, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    ctx = owner = None
    try:
        session = sc["encoder"].cleanup_owner
        worker_child = session._worker._child
        token_child = session._tokenizer._child
        expected = transport._expected_tuple(session)
        events = []
        encode_guarded, forward_guarded, receipt_check = transport._observe(
            session, events)
        monkeypatch.setattr(session._tokenizer, "_encode_guarded",
                            encode_guarded)
        monkeypatch.setattr(session._worker, "_forward_guarded",
                            forward_guarded)
        monkeypatch.setattr(session, "_receipt", receipt_check)
        (ctx, dataset, _bundle_ids, owner, _policy_root, reader, _payload) = (
            _scenario(tmp_path, monkeypatch, expected))
        try:
            m, b, g, p = _shapes(owner)
            directory = _per_directory(m, b, g, p)
            catalog_shape = _per_catalog(m, b, g, p)
            expected_source = tuple(
                2 * directory[i] + 8 * catalog_shape[i] for i in range(3))
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            # The fresh admission after the expensive fixture setup; its
            # own entry reads precede the cut counters.
            admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            real_read_bound = capture.PolicyCaptureReader.read_selection.__get__(
                reader, type(reader))
            counts = _counts()
            restore = _install_counting(monkeypatch, ctx, owner, reader, counts)
            dir_counts = _directory_counts(monkeypatch)
            with monkeypatch.context() as patched:
                catalog_counts = _catalog_counts(patched)
                producer_calls = []
                _install_producer_counter(patched, producer_calls)
                token_pipe = session._tokenizer._child.stdin
                worker_pipe = session._worker._child.stdin
                writes = []
                real_write = os.write
                os.write = transport._write_counter(
                    [token_pipe, worker_pipe], writes)
                try:
                    held = owner.value
                    held_op = owner.op
                    held_guard = owner.guard
                    held_end = owner.op.end
                    (case_id, query, result) = _producer(
                        admission, owner, dataset, _bundle_ids, ("h1", "h4"),
                        (expected, expected), sc["encoder"], "h1")
                finally:
                    os.write = real_write
                # One genuine encoder-to-producer selected case result,
                # with the internal HybridResult status fields.
                assert case_id == "h1"
                assert type(query) is runner.Query
                assert type(result) is hybrid.HybridResult
                assert (result.query_origin, result.qualification) == (
                    "SUPPLIED_UNVERIFIED", "NOT_QUALIFIED")
                # One actual full initial reload in the shared body
                # plus one final distinct full owner reload in the
                # producer, and the eight actual catalog loads at two
                # full directories each: eighteen stable actual raw
                # directory starts and successful completions, with the
                # bundle, derived and original counts computed by their
                # actual delegated phases including the catalogs.
                assert counts["pin_load"] == 2
                assert dir_counts == {"start": 18, "done": 18}
                assert (counts["bundle"], counts["derived"],
                        counts["original"]) == expected_source
                # The two initial source selected observations, the
                # genuine T1 and T2 and the real O1 through O5: nine
                # genuine selected observations in order.
                assert counts["read"] == [1, 1, 1, 1, 1, 1, 1, 1, 1]
                # Positive real T1 text and T2 token-ID payload writes
                # as actual delegated kernel bytes matched by live pipe
                # identity, with one real T1 and one real T2 each; the
                # T2 frame length is derived from the actual observed
                # token IDs, never an assumed frame.
                assert sum(actual for pipe, _req, actual in writes
                           if pipe == id(token_pipe)) == transport._frame_len(QUESTION)
                receipts = [r for kind, r in events if kind == "receipt"]
                assert len(receipts) == 1
                receipt = receipts[0]
                assert type(receipt) is embedding_tokenizer.TokenIDReceipt
                # The exact canonical text tie: the same digest the
                # real session receipt validation computes for the
                # question.
                assert receipt.input_sha256 == hashlib.sha256(
                    json.dumps([QUESTION, None], ensure_ascii=True,
                               separators=(",", ":")).encode()
                ).hexdigest()
                forwards = [rows for kind, rows in events if kind == "forward"]
                assert forwards == [[receipt.ids]]
                assert sum(actual for pipe, _req, actual in writes
                           if pipe == id(worker_pipe)) == (
                               transport._forward_frame_len(forwards[0]))
                assert session._tokenizer._calls == 1
                assert session._worker._calls == 1
                # One actual QueryEmbedding whose exact payload reaches
                # the real producer once.
                assert len(producer_calls) == 1
                assert producer_calls[0] == query.payload
                assert query.payload == PAYLOAD
                assert result.query_payload_sha256 == hashlib.sha256(
                    query.payload).hexdigest()
                # Two direct plus six nested catalog calls in the one
                # producer dispatch.
                assert catalog_counts == {"direct": 2, "nested": 6}
                # Exact identity and custody: the locally captured
                # actual association operation, held PinData, guard and
                # end survive both short borrows - the same operation
                # marker and guard object, the restored exact prior
                # end, the released guard, the live admission and the
                # still-open resident.
                assert owner.value is held
                assert owner.op is held_op
                assert owner.guard is held_guard
                assert owner.state == "ACTIVE"
                assert owner.op.end == held_end == prior_end
                assert not owner.guard.locked()
                assert admission._invalid is False
                assert sc["encoder"]._state == "open"
                # The custody recheck uses the genuine reader (not a
                # guarded cut), so the real reader is restored first.
                monkeypatch.setattr(reader, "read_selection", real_read_bound)
                assert admission.recheck(deadline_ms=30000) is True
            # The stable producer query ID matches the existing unguarded
            # route with the same good payload in its separately measured
            # phase, on the exact effective case grants derived through
            # the genuine existing case-scope intersection.
            restore()
            policy_snapshot = pin_eligibility._isolated_policy_snapshot(admission)
            anchor = pin_eligibility._bounded_admission(
                pin_eligibility._admitted_principal_grants(
                    policy_snapshot, admission.principal_id))
            full_grants = pin_eligibility._bound_grants(admission, anchor)
            declared = text_evaluation_dataset.admit(dataset)
            case_h1 = next(c for c in declared.cases if c.case_id == "h1")
            (_original, effective, _restricted) = stage_loss._admit_authority(
                full_grants, None, case_h1.scope, stage_loss._Meter(),
                lambda: None)
            with monkeypatch.context() as phase_patch:
                phase_catalog = _catalog_counts(phase_patch)
                phase_dirs = _directory_counts(phase_patch)
                legacy = hybrid.search(
                    ctx.originals, ctx.derived, str(owner.op.path),
                    held.data.snapshot_id, QUESTION, query.payload,
                    query_space_id=query.space_id,
                    query_definition_fingerprint=query.definition_fingerprint,
                    query_policy_id=query.policy_id,
                    query_execution_fingerprint=query.execution_fingerprint,
                    grants=effective, dense_k=60, lexical_k=60,
                    partition_cap=60, k=60, deadline_ms=120000, trace=True)
                assert phase_catalog == {"direct": 2, "nested": 6}
            assert legacy.query_id == result.query_id
            # The independent actual started/completed directory work of
            # the legacy phase: eight real catalogs at two full
            # directories each.
            assert phase_dirs == {"start": 16, "done": 16}
            # The full actual eligible/ranked dense, lexical and fusion
            # results match the actual unguarded legacy dispatch over
            # the same effective scope, question and payload: ranking
            # IDs and scores, qualification, no degradation and the
            # correct scope.
            assert result.dense == legacy.dense
            assert result.lexical == legacy.lexical
            assert result.fusion == legacy.fusion
        finally:
            gold_fixture._close_owned(ctx, owner)
    finally:
        sc["encoder"].close()
    # Reaping evidence: the real cleanup reaped both real children.
    assert worker_child.poll() is not None and token_child.poll() is not None


def test_encoder_producer_all_case_and_incompatible_declaration_denials(
        tmp_path, monkeypatch):
    real_argv = cpu._argv
    encoder_root = tmp_path / "encoder"
    encoder_root.mkdir(mode=0o700)
    sc = transport._scenario(encoder_root, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    ctx = owner = None
    try:
        session = sc["encoder"].cleanup_owner
        expected = transport._expected_tuple(session)
        (ctx, dataset, bundle_ids, owner, _policy_root, reader, _payload) = (
            _scenario(tmp_path, monkeypatch, expected))
        try:
            m, b, g, p = _shapes(owner)
            directory = _per_directory(m, b, g, p)
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            # The separately successful earlier pin, counted on its own
            # witnesses, before the later denials.
            admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            counts0 = _counts()
            restore0 = _install_counting(monkeypatch, ctx, owner, reader, counts0)
            dir0 = _directory_counts(monkeypatch)
            captured0 = runner._current_cohort_initial_pin(
                admission, owner, dataset, runner.Cohort("held_out", ("h1", "h4")),
                _identifiers(("h1", "h4")), bundle_ids,
                runner.Config("cep-cfg", "cep-declaration"),
                runner.Budget(*runner._MAX_BUDGET), deadline_ms=30000)
            assert captured0 is owner.value
            assert counts0["pin_load"] == 1
            assert dir0 == {"start": 1, "done": 1}
            assert (counts0["bundle"], counts0["derived"],
                    counts0["original"]) == directory
            restore0()
            # (b) The later unavailable selected case at zero reload:
            # the pure all-case scope admission of the exact ordered
            # cohort refuses before any new pin, directory, ingestion,
            # original or selected work.
            fresh = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                             deadline_ms=30000)
            counts = _counts()
            restore = _install_counting(monkeypatch, ctx, owner, reader, counts)
            dir_counts = _directory_counts(monkeypatch)
            with monkeypatch.context() as patched:
                producer_calls = []
                _install_producer_counter(patched, producer_calls)
                writes = []
                real_write = os.write
                os.write = transport._write_counter(
                    [session._tokenizer._child.stdin,
                     session._worker._child.stdin], writes)
                try:
                    with pytest.raises(runner.CohortRunnerError) as exc:
                        _producer(fresh, owner, dataset, bundle_ids,
                                  ("h1", "h2"), (expected, expected),
                                  sc["encoder"], "h2")
                finally:
                    os.write = real_write
            restore()
            assert _refusal_prefix(exc.value.progress) == ("PREFLIGHT", 2, 0, 0, 0, 2)
            assert _zero(counts)
            assert dir_counts == {"start": 0, "done": 0}
            assert writes == []
            assert producer_calls == []
            # No selected observation ran, so the admission is not
            # latched, and the guard and prior end are retained.
            assert fresh._invalid is False
            assert owner.state == "ACTIVE"
            assert owner.op.end == prior_end
            assert not owner.guard.locked()
            # (c) The well-shaped incompatible later declaration at zero
            # protected byte writes: the one actual cohort pin reload of
            # the shared body completes, then the pre-T1 verification of
            # the declared tuples against the held core refuses before
            # any encoder transport write or producer dispatch.
            fresh2 = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                              deadline_ms=30000)
            counts2 = _counts()
            restore2 = _install_counting(monkeypatch, ctx, owner, reader, counts2)
            dir2 = _directory_counts(monkeypatch)
            with monkeypatch.context() as patched2:
                producer_calls2 = []
                _install_producer_counter(patched2, producer_calls2)
                writes2 = []
                real_write = os.write
                os.write = transport._write_counter(
                    [session._tokenizer._child.stdin,
                     session._worker._child.stdin], writes2)
                try:
                    with pytest.raises(runner.CohortRunnerError) as exc2:
                        _producer(fresh2, owner, dataset, bundle_ids,
                                  ("h1", "h4"),
                                  _identifiers(("h1", "h4")),
                                  sc["encoder"], "h1")
                finally:
                    os.write = real_write
            restore2()
            # The tuple refusal retains the PREFLIGHT phase with the
            # actual intended count: the actual encoder attempt is
            # charged only immediately before encoder dispatch, which
            # never starts.
            assert _refusal_prefix(exc2.value.progress) == (
                "PREFLIGHT", 2, 0, 0, 0, 2)
            assert counts2["pin_load"] == 1
            assert dir2 == {"start": 1, "done": 1}
            assert (counts2["bundle"], counts2["derived"],
                    counts2["original"]) == directory
            # The two genuine body observations only; no T1 cut read
            # and no protected work beyond the one actual reload.
            assert counts2["read"] == [1, 1]
            assert writes2 == []
            assert producer_calls2 == []
            assert fresh2._invalid is False
            assert owner.state == "ACTIVE"
            assert owner.op.end == prior_end
            assert not owner.guard.locked()
            # No encode was attempted, so the resident stays open.
            assert sc["encoder"]._state == "open"
            # (d) The pure unknown nomination at zero reload: the exact
            # selected case index is resolved from the one genuine
            # declaration before the actual initial reload, so an
            # unknown case ID refuses at zero pin, directory,
            # ingestion, original, selected or protected work.
            fresh3 = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                              deadline_ms=30000)
            counts3 = _counts()
            restore3 = _install_counting(monkeypatch, ctx, owner, reader, counts3)
            dir3 = _directory_counts(monkeypatch)
            with monkeypatch.context() as patched3:
                producer_calls3 = []
                _install_producer_counter(patched3, producer_calls3)
                writes3 = []
                real_write = os.write
                os.write = transport._write_counter(
                    [session._tokenizer._child.stdin,
                     session._worker._child.stdin], writes3)
                try:
                    with pytest.raises(runner.CohortRunnerError) as exc3:
                        _producer(fresh3, owner, dataset, bundle_ids,
                                  ("h1", "h4"), (expected, expected),
                                  sc["encoder"], "h9")
                finally:
                    os.write = real_write
            restore3()
            assert _refusal_prefix(exc3.value.progress) == (
                "PREFLIGHT", 2, 0, 0, 0, 2)
            assert _zero(counts3)
            assert dir3 == {"start": 0, "done": 0}
            assert writes3 == []
            assert producer_calls3 == []
            assert fresh3._invalid is False
            assert owner.state == "ACTIVE"
            assert owner.op.end == prior_end
            assert not owner.guard.locked()
        finally:
            gold_fixture._close_owned(ctx, owner)
    finally:
        sc["encoder"].close()


def test_encoder_producer_generation_change_denials(tmp_path, monkeypatch):
    real_argv = cpu._argv
    encoder_root = tmp_path / "encoder"
    encoder_root.mkdir(mode=0o700)
    sc = transport._scenario(encoder_root, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    ctx = owner = None
    try:
        session = sc["encoder"].cleanup_owner
        expected = transport._expected_tuple(session)
        (ctx, dataset, bundle_ids, owner, policy_root, reader, payload) = (
            _scenario(tmp_path, monkeypatch, expected))
        try:
            m, b, g, p = _shapes(owner)
            directory = _per_directory(m, b, g, p)
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            # (c1) The real selected generation changes before T1 under
            # the same raw pin: the exact pre-dispatch held value and
            # raw pointer are retained across the change.
            held = owner.value
            raw_pointer = owner.value.pointer
            admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            counts = _counts()
            state = {"changed": False}

            def change_before_t1():
                state["changed"] = True
                _change_generation(policy_root, 2, payload)

            restore = _install_counting(
                monkeypatch, ctx, owner, reader, counts,
                change_after_read=2, change=change_before_t1)
            dir_counts = _directory_counts(monkeypatch)
            with monkeypatch.context() as patched:
                producer_calls = []
                _install_producer_counter(patched, producer_calls)
                writes = []
                real_write = os.write
                os.write = transport._write_counter(
                    [session._tokenizer._child.stdin,
                     session._worker._child.stdin], writes)
                try:
                    with pytest.raises(runner.CohortRunnerError) as exc:
                        _producer(admission, owner, dataset, bundle_ids,
                                  ("h1", "h4"), (expected, expected),
                                  sc["encoder"], "h1")
                finally:
                    os.write = real_write
            assert state["changed"] is True
            assert _refusal_prefix(exc.value.progress) == ("T1", 2, 1, 0, 1, 1)
            # One actual full initial reload completed in the body, the
            # genuine T1 observation refused, no usable result, no
            # protected byte write and no producer dispatch.
            assert counts["pin_load"] == 1
            assert dir_counts == {"start": 1, "done": 1}
            assert (counts["bundle"], counts["derived"],
                    counts["original"]) == directory
            # The initial two source selected observations and the
            # refused T1 cut read.
            assert counts["read"] == [1, 1, 1]
            assert writes == []
            assert producer_calls == []
            # Latch and exact restored custody, with the same raw pin
            # across the change.
            assert admission._invalid is True
            assert admission.recheck(deadline_ms=1000) is False
            assert counts["read"] == [1, 1, 1]
            assert owner.value is held
            assert owner.value.pointer is raw_pointer
            assert owner.state == "ACTIVE"
            assert owner.op.end == prior_end
            assert not owner.guard.locked()
            # The refused encode left the resident in its fixed refused
            # state, never a usable result.
            assert sc["encoder"]._state == "refused"
            restore()
            # (c2) The fresh separate subcase: the old refused resident
            # is retired and a fresh separate scenario reopens the same
            # synthetic assets and context with independently open
            # custody, rechecking the exact tuple of the verified same
            # fixture immutable identity.  Real T1 and T2 complete, the
            # actual O1 succeeds, the selection advances before O2, and
            # zero new producer catalog starts result.
            fresh_encoder_root = tmp_path / "encoder2"
            fresh_encoder_root.mkdir(mode=0o700)
            fresh_sc = transport._scenario(fresh_encoder_root, monkeypatch,
                                           real_argv)
            fresh_sc["encoder"].__enter__()
            try:
                fresh_session = fresh_sc["encoder"].cleanup_owner
                fresh_expected = transport._expected_tuple(fresh_session)
                assert fresh_expected == expected
                events2 = []
                encode_guarded2, forward_guarded2, receipt_check2 = (
                    transport._observe(fresh_session, events2))
                monkeypatch.setattr(fresh_session._tokenizer,
                                    "_encode_guarded", encode_guarded2)
                monkeypatch.setattr(fresh_session._worker,
                                    "_forward_guarded", forward_guarded2)
                monkeypatch.setattr(fresh_session, "_receipt",
                                    receipt_check2)
                fresh2 = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                                  deadline_ms=30000)
                counts2 = _counts()
                state2 = {"changed": False}

                def change_before_o2():
                    state2["changed"] = True
                    _change_generation(policy_root, 3, payload)

                restore2 = _install_counting(
                    monkeypatch, ctx, owner, reader, counts2,
                    change_after_read=5, change=change_before_o2)
                dir2 = _directory_counts(monkeypatch)
                with monkeypatch.context() as patched2:
                    catalog_counts2 = _catalog_counts(patched2)
                    producer_calls2 = []
                    _install_producer_counter(patched2, producer_calls2)
                    token_pipe = fresh_session._tokenizer._child.stdin
                    worker_pipe = fresh_session._worker._child.stdin
                    writes2 = []
                    real_write = os.write
                    os.write = transport._write_counter(
                        [token_pipe, worker_pipe], writes2)
                    try:
                        with pytest.raises(runner.CohortRunnerError) as exc2:
                            _producer(fresh2, owner, dataset, bundle_ids,
                                      ("h1", "h4"),
                                      (fresh_expected, fresh_expected),
                                      fresh_sc["encoder"], "h1")
                    finally:
                        os.write = real_write
                restore2()
                assert state2["changed"] is True
                # The producer dispatch is reported separately from the
                # encoder's own T1 and T2 as its own PRODUCER phase.
                assert _refusal_prefix(exc2.value.progress) == (
                    "PRODUCER", 2, 1, 0, 1, 1)
                # One actual full initial reload completed in the body;
                # the producer dispatch started no new full reload.
                assert counts2["pin_load"] == 1
                assert dir2 == {"start": 1, "done": 1}
                assert (counts2["bundle"], counts2["derived"],
                        counts2["original"]) == directory
                # The initial two source selected observations, the
                # actual T1 and T2 and the actual O1, then the refusing
                # O2: six genuine selected observations in order.
                assert counts2["read"] == [1, 1, 1, 1, 1, 1]
                # Actual T1 and T2 completed before the published
                # change: one real tokenizer text write and one real
                # forward token-ID payload write as actual delegated
                # kernel bytes on the new live pipes, the T2 frame
                # length derived from the actual observed token IDs.
                assert sum(actual for pipe, _req, actual in writes2
                           if pipe == id(token_pipe)) == transport._frame_len(QUESTION)
                receipts2 = [r for kind, r in events2 if kind == "receipt"]
                assert len(receipts2) == 1
                receipt2 = receipts2[0]
                assert type(receipt2) is embedding_tokenizer.TokenIDReceipt
                assert receipt2.input_sha256 == hashlib.sha256(
                    json.dumps([QUESTION, None], ensure_ascii=True,
                               separators=(",", ":")).encode()
                ).hexdigest()
                forwards2 = [rows for kind, rows in events2
                             if kind == "forward"]
                assert forwards2 == [[receipt2.ids]]
                assert sum(actual for pipe, _req, actual in writes2
                           if pipe == id(worker_pipe)) == (
                               transport._forward_frame_len(forwards2[0]))
                assert fresh_session._tokenizer._calls == 1
                assert fresh_session._worker._calls == 1
                # The actual O1 - the producer dispatch's first
                # genuine selected read, read #5 - completed with the
                # producer dispatched exactly once, and only after it
                # did the same-wire published change fire, detected by
                # O2, with zero new producer catalog starts.
                assert len(producer_calls2) == 1
                assert catalog_counts2 == {"direct": 0, "nested": 0}
                assert fresh2._invalid is True
                assert owner.value is held
                assert owner.value.pointer is raw_pointer
                assert owner.state == "ACTIVE"
                assert owner.op.end == prior_end
                assert not owner.guard.locked()
            finally:
                fresh_sc["encoder"].close()
        finally:
            gold_fixture._close_owned(ctx, owner)
    finally:
        sc["encoder"].close()
