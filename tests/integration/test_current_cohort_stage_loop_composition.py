"""Owned private current-cohort shared source and stage loop proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The
real hosted source fixture and the canonical five-case dataset with
actual bundle IDs come from the reviewed composition fixtures of the
encoder producer proof, which this module imports as helpers
(``_scenario``, its counting wrappers and shapes); the actual raw
snapshot selector and the real ``PinOwner.acquire_selected_data``
build the pinned data, and each fresh current admission is created
only after the expensive fixture setup that precedes its dispatch,
with its own initial selected read excluded from the counted span.
The three real hosted witnesses run the one fixed private current
source execution entry over the actual accepted donor fixture: the
positive two selected held-out cases h1 and h4 with the withheld
out-of-scope corpus, one initial physical pin, two actual source
CASE_PIN reloads, two true T1/T2 encoder uses and two full
same-payload hybrid spans each followed by a completed real stage
diagnosis, the shared source aggregate and serialization, and the
final same-admission selected cut's one genuine delegate
observation, measured against the exact legacy counts and per-case
metadata in a separately measured legacy phase; the negative two
cases h1 and h2 with the corpus withheld, refusing the whole
declaration without a new physical reload or protected model touch;
and the mutation publishing one actual same-wire selected-policy
generation after one actually completed case scope and before the
second real CASE_PIN reread, proving zero second encoder/catalog/
stage starts, one completed case, the exact prefix, the genuine
admission latch and the retained exact raw pointer and owner.  The
stable h1/h4 and mutation witnesses project the owned fixture's
declared Gold to the genuinely admissible a/c batch, because the
existing whole-declared-Gold-batch gate refuses the complete
declaration whenever the genuinely withheld corpus-two member b is
declared while unavailable under the selected policy; the h1/h2
witness keeps the exact original full declaration.  No local native
witness execution: only the configured hosted CI
executes the three real hosted nodes, and local proof of this module
is collection only.
"""
import hashlib
import json
import os
import sys
import time
from dataclasses import fields
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import cpu_embedding_worker as cpu  # noqa: E402
from slaif_raggedized_helper import embedding_tokenizer  # noqa: E402
from slaif_raggedized_helper import private_policy_capture as capture  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import provenance_records as p  # noqa: E402
from slaif_raggedized_helper import raw_hybrid_search as hybrid  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_catalog as catalog  # noqa: E402
from slaif_raggedized_helper import source_bound_stage_loss as stage_loss  # noqa: E402
from slaif_raggedized_helper import source_cohort_runner as runner  # noqa: E402
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility  # noqa: E402
from slaif_raggedized_helper import text_evaluation_dataset  # noqa: E402
import test_current_cohort_encoder_producer_composition as producer_fixture  # noqa: E402
import test_current_gold_dispatch_composition as gold_fixture  # noqa: E402
import test_guarded_encoder_transport_composition as transport  # noqa: E402
import test_source_cohort_runner_composition as cohort_fixture  # noqa: E402

QUESTION_H1 = "DistinctiveZephyr one?"
QUESTION_H4 = "DistinctiveZephyr none?"


def _case_reads(u_rank, bundle_count):
    """Genuine selected observations of one complete ordered case:
    the CASE_PIN revalidation's two, the real T1 and T2, the real O1
    through O5, the five stage pin revalidations' two each, the stage
    catalog's two, the Gold body's two per declared bundle, the
    ranking's two catalogs plus two per selected bundle, and the
    stage operation's one actual final same-admission selected cut
    distinct from the outer cohort's terminal read."""
    return 2 + 1 + 1 + 5 + 10 + 2 + 2 * bundle_count + 2 + 2 * u_rank + 1


def _bundle_work(directory, catalog_shape, u_rank, bundle_count):
    """The per-case (bundle, derived, original) delegated loads: the
    CASE_PIN directory, the hybrid span's one final full reload and
    eight catalog loads, the stage span's five pin directories, one
    stage catalog load and two ranking catalog rebuilds, the Gold
    body's two loads per declared bundle and the ranking's two loads
    per selected bundle, each load delegating one real bundle,
    derived and original load."""
    extra = 2 * bundle_count + 2 * u_rank
    return tuple(7 * directory[i] + 11 * catalog_shape[i] + extra
                 for i in range(3))


def _eligible(ctx, owner, dataset, case_id, full_grants):
    """The actual eligible rows, distinct selected bundles, case
    record and case-bound authority of one case, computed as an
    unmeasured fixture baseline with one real catalog load through
    the same pure eligibility the stage dispatch uses, before the
    counted span installs its wrappers."""
    meter = stage_loss._Meter()
    declared = text_evaluation_dataset.admit(dataset)
    case = next(c for c in declared.cases if c.case_id == case_id)
    original, effective, restricted = stage_loss._admit_authority(
        full_grants, None, case.scope, meter, lambda: None)
    loaded = catalog.load_catalog(
        ctx.originals, ctx.derived, str(owner.op.path),
        owner.value.data.snapshot_id, deadline_ms=120000)
    eligible = stage_loss._catalog_eligible(
        loaded, owner.value, effective, restricted, stage_loss._Meter(),
        lambda: None)
    return (len(eligible),
            len({d.bundle_container_id for d in eligible}),
            case, original, effective, restricted)


def _admissible_gold_batch(owner, dataset, bundle_ids, admission):
    """The one test-local projection of the full native fixture to
    the genuinely admissible synthetic Gold batch, following the
    already proven Gold witness.  The existing whole-declared-
    Gold-batch gate authenticates the whole membership by the
    genuine unavailable partitions but refuses the declared batch
    whenever a declared entry's partition is unavailable under the
    effective case scope; with the complete native declaration the
    genuinely withheld corpus-two member b is declared and refused
    while the same actual raw original pin still holds it.  The
    projection resolves b from the actually retained membership and
    its corpus scope, excludes its bundle ID from the declared
    Gold, and projects every one of its revision/extraction spans
    out of the entire declared five-case dataset, pruning only the
    resulting emptied alternatives and requirements, reassembled
    with the exact existing canonical JSON and source fixture.  The
    h1/h4 case scopes and questions, the five dataset cases, the
    six projected Gold atom occurrences and a/c as the two declared
    Gold bundles are preserved, and b stays present in the pin and
    genuinely unavailable under the selected policy.  Returns the
    projected dataset bytes and the declared bundle ID tuple."""
    entries = owner.value.data.membership.entries

    def corpus_of(ident):
        entry = next(e for e in entries
                     if e.bundle_container_id == ident)
        return p.admit_record("Scope", entry.scope_bytes).corpus

    withheld_id = next(ident for ident in bundle_ids
                       if corpus_of(ident) == "two")
    withheld = next(e for e in entries
                    if e.bundle_container_id == withheld_id)
    unavailable = set(policy_eligibility.unavailable_partitions(
        pin_eligibility._isolated_policy_snapshot(admission),
        owner.value.data.membership))
    assert withheld.partition_id in unavailable
    dropped = {(entry.revision_id, entry.extraction_id)
               for entry in entries
               if entry.bundle_container_id == withheld_id}
    base = json.loads(dataset)
    for case in base["cases"]:
        requirements = []
        for requirement in case["requirements"]:
            alternatives = []
            for alternative in requirement["alternatives"]:
                spans = [span for span in alternative
                         if (span["revision_id"], span["extraction_id"])
                         not in dropped]
                if spans:
                    alternatives.append(spans)
            if alternatives:
                requirements.append(requirement)
        case["requirements"] = requirements
    projected = cohort_fixture.canonical(base)
    declared = tuple(ident for ident in bundle_ids
                     if ident != withheld_id)
    admitted = text_evaluation_dataset.admit(projected)
    assert admitted.case_count == 5
    assert admitted.gold_atom_count == 6
    assert len(declared) == 2
    return projected, declared


def _unexpected_refusal(error, shapes):
    """Bounded test-local diagnostic for an unexpected refusal: the
    existing content-free progress prefix and the fixture aggregate
    counts (membership entries, row-map bundles, source groups,
    partition triples) only - no content, identity, path or byte
    material."""
    return AssertionError(
        "unexpected stage-loop refusal progress=%s fixture=%s"
        % (producer_fixture._refusal_prefix(error.progress), shapes))


def _stage_loop(admission, owner, dataset, bundle_ids, case_ids,
                identifiers, encoder):
    cohort = runner.Cohort("held_out", tuple(case_ids))
    return runner._current_cohort_stage_loop(
        admission, owner, dataset, cohort, identifiers, bundle_ids,
        runner.Config("csl-cfg", "csl-declaration"),
        runner.Budget(*runner._MAX_BUDGET), encoder,
    )


def test_stage_loop_positive_two_cases_match_legacy_dispatch(
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
        (ctx, dataset, bundle_ids, owner, _policy_root, reader, _payload) = (
            producer_fixture._scenario(tmp_path, monkeypatch, expected))
        try:
            m, b, g, p = producer_fixture._shapes(owner)
            directory = producer_fixture._per_directory(m, b, g, p)
            catalog_shape = producer_fixture._per_catalog(m, b, g, p)
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            # The fresh admission after the expensive fixture setup;
            # its own entry reads precede the cut counters.
            admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            policy_snapshot = pin_eligibility._isolated_policy_snapshot(
                admission)
            anchor = pin_eligibility._bounded_admission(
                pin_eligibility._admitted_principal_grants(
                    policy_snapshot, admission.principal_id))
            full_grants = pin_eligibility._bound_grants(admission, anchor)
            # The complete native declaration is refused by the
            # existing whole-declared-Gold-batch gate because the
            # genuinely withheld corpus-two b is declared and
            # unavailable; the stable witness uses the one test-local
            # projection to the genuinely admissible a/c batch over
            # the same actual raw original pin.
            dataset_ac, declared_ac = _admissible_gold_batch(
                owner, dataset, bundle_ids, admission)
            rows1, u1, _case1, _original1, _effective1, _restricted1 = (
                _eligible(ctx, owner, dataset_ac, "h1", full_grants))
            rows4, u4, _case4, _original4, _effective4, _restricted4 = (
                _eligible(ctx, owner, dataset_ac, "h4", full_grants))
            counts = producer_fixture._counts()
            restore = producer_fixture._install_counting(
                monkeypatch, ctx, owner, reader, counts)
            dir_counts = producer_fixture._directory_counts(monkeypatch)
            with monkeypatch.context() as patched:
                catalog_counts = producer_fixture._catalog_counts(patched)
                producer_calls = []
                producer_fixture._install_producer_counter(
                    patched, producer_calls)
                token_pipe = session._tokenizer._child.stdin
                worker_pipe = session._worker._child.stdin
                writes = []
                real_write = os.write
                os.write = transport._write_counter(
                    [token_pipe, worker_pipe], writes)
                try:
                    held = owner.value
                    try:
                        report = _stage_loop(
                            admission, owner, dataset_ac, declared_ac,
                            ("h1", "h4"), (expected, expected),
                            sc["encoder"])
                    except runner.CohortRunnerError as error:
                        raise _unexpected_refusal(error, (m, b, g, p))
                finally:
                    os.write = real_write
                # One genuine shared source cohort and stage result,
                # the private identity-embedded CohortReport.
                assert type(report) is runner.CohortReport
                document = json.loads(report.identity_payload)
                assert document["schema"] == "slaif-source-cohort-runner-v1"
                assert document["split"] == "held_out"
                assert document["selection_kind"] == "DECLARED_SUBSET"
                assert document["selected_count"] == 2
                assert document["dataset_case_count"] == 5
                assert document["dataset_gold_occurrences"] == 6
                assert document["progress"] == {
                    "intended": 2, "attempted": 2, "completed": 2,
                    "refused": 0, "pending": 0}
                assert document["pointer_sha256"] == hashlib.sha256(
                    held.pointer.pointer_bytes).hexdigest()
                assert document["generation"] == held.pointer.generation
                assert document["snapshot_id"] == held.data.snapshot_id
                assert document["statuses"]["producer"] == "COMPLETED"
                assert document["statuses"]["baseline"] == "NOT_RUN"
                assert document["statuses"]["policy"] == "CHECKED"
                assert document["statuses"]["current_rights"] == "NOT_QUALIFIED"
                sources = runner._source_reservation(2)
                extra = runner._current_owned_extra_reservation(2)
                ledger = document["ledger"]
                # Direct source runner pins only: one initial plus the
                # genuine per-case CASE_PIN revalidation; the
                # completed delegate pin loads are a separate current
                # quantity below.
                assert ledger["direct_own_observed"] == {
                    "dataset": 1, "pin": 3, "producer": 2, "binder": 2,
                    "aggregate": 1}
                reserved = ledger["static_worstcase_reserved"]
                assert reserved["directories"] == sources[0]
                assert reserved["ingestion_loads"] == sources[1]
                assert reserved["derived_batch_loads"] == sources[2]
                assert reserved["bytes"] == sources[3]
                assert reserved["transitive_pin"] == 10
                assert reserved["catalog"] == 22
                assert reserved["gold"] == 2
                assert reserved["ranking"] == 2
                assert reserved["geometry"] == 2
                assert ledger["current_owned_extra_reserved"] == {
                    "directories": extra[0],
                    "ingestion_loads": extra[1],
                    "derived_batch_loads": extra[2],
                    "bytes": extra[3]}
                # One hybrid final revalidation plus five stage pin
                # loads per completed case, required by the completed
                # exact delegates and distinct from the three direct
                # pins and the legacy static reservation.
                assert ledger["delegate_pin_observations"] == 12
                assert document["caps"] == dict(zip(
                    (item.name for item in fields(runner.Budget)),
                    runner._MAX_BUDGET))
                pure = document["pure"]
                # The pure metrics and the outer report are computed
                # and metered in distinct domains: rederive each
                # digest with its own domain separator and verify
                # each counter in its actual scope, as the legacy
                # reference does.
                budget_caps = runner.Budget(*runner._MAX_BUDGET)
                encoded = json.dumps(
                    pure["identity_payload"], ensure_ascii=True,
                    separators=(",", ":")).encode("ascii")
                assert pure["identity"] == "sha256:" + hashlib.sha256(
                    b"slaif-declared-cohort-metrics-v1\n"
                    + encoded).hexdigest()
                assert 0 < pure["final_work"] <= budget_caps.aggregate_work
                assert (0 < pure["final_payload"]
                        <= budget_caps.aggregate_payload)
                assert report.identity == "sha256:" + hashlib.sha256(
                    b"slaif-source-cohort-runner-v1\n"
                    + report.identity_payload).hexdigest()
                assert 0 < report.final_work <= budget_caps.local_work
                assert (0 < report.final_payload
                        <= budget_caps.local_payload)
                cases_doc = document["cases"]
                assert [c["case_id"] for c in cases_doc] == ["h1", "h4"]
                assert cases_doc[0]["question_sha256"] == hashlib.sha256(
                    QUESTION_H1.encode()).hexdigest()
                assert cases_doc[1]["question_sha256"] == hashlib.sha256(
                    QUESTION_H4.encode()).hexdigest()
                assert cases_doc[0]["payload_sha256"] == hashlib.sha256(
                    producer_calls[0]).hexdigest()
                assert cases_doc[1]["payload_sha256"] == hashlib.sha256(
                    producer_calls[1]).hexdigest()
                assert cases_doc[0]["chosen_atom_occurrences"] == 1
                assert cases_doc[1]["chosen_atom_occurrences"] == 0
                assert cases_doc[0]["eligible_row_count"] == rows1
                assert cases_doc[1]["eligible_row_count"] == rows4
                # Fifteen actual full pin loads: three direct source
                # runner pins (one initial plus one CASE_PIN per case)
                # plus twelve completed delegate observations (one
                # hybrid final revalidation plus five stage pins per
                # case), and one initial plus twenty-nine actual raw
                # directory starts and successful completions per
                # case: fifty-nine in total.
                assert counts["pin_load"] == 15
                assert dir_counts == {"start": 59, "done": 59}
                # The delegated bundle, derived and original loads of
                # the initial pin plus the two actual cases.
                case1 = _bundle_work(directory, catalog_shape, u1, 2)
                case4 = _bundle_work(directory, catalog_shape, u4, 2)
                assert (counts["bundle"], counts["derived"],
                        counts["original"]) == tuple(
                            directory[i] + case1[i] + case4[i]
                            for i in range(3))
                # The initial two observations, the two full case-
                # scoped observation spans in declaration order, and
                # the one genuine delegate observation of the final
                # same-admission cut after the shared result work.
                assert counts["read"] == [1, 1] + [1] * _case_reads(u1, 2) \
                    + [1] * _case_reads(u4, 2) + [1]
                # Two direct plus nine nested catalog loads per case.
                assert catalog_counts == {"direct": 4, "nested": 18}
                # Two actual T1 text and T2 token-ID spans, one per
                # case, as actual delegated kernel bytes matched by
                # live pipe identity; the T2 frame lengths are derived
                # from the actual observed token IDs.
                assert sum(actual for pipe, _req, actual in writes
                           if pipe == id(token_pipe)) == (
                               transport._frame_len(QUESTION_H1)
                               + transport._frame_len(QUESTION_H4))
                receipts = [r for kind, r in events if kind == "receipt"]
                assert len(receipts) == 2
                assert all(type(r) is embedding_tokenizer.TokenIDReceipt
                           for r in receipts)
                for receipt, question in zip(
                        receipts, (QUESTION_H1, QUESTION_H4)):
                    assert receipt.input_sha256 == hashlib.sha256(
                        json.dumps([question, None], ensure_ascii=True,
                                   separators=(",", ":")).encode()
                    ).hexdigest()
                forwards = [rows for kind, rows in events
                            if kind == "forward"]
                assert len(forwards) == 2
                assert forwards[0] == [receipts[0].ids]
                assert forwards[1] == [receipts[1].ids]
                assert sum(actual for pipe, _req, actual in writes
                           if pipe == id(worker_pipe)) == (
                               transport._forward_frame_len(forwards[0])
                               + transport._forward_frame_len(forwards[1]))
                assert session._tokenizer._calls == 2
                assert session._worker._calls == 2
                # The two actual same-payload producer dispatches in
                # declaration order, the first with the exact one-row
                # payload of the reviewed producer proof.
                assert len(producer_calls) == 2
                assert producer_calls[0] == producer_fixture.PAYLOAD
                assert len(producer_calls[1]) == 4096
                # Exact custody: the held PinData survives the shared
                # prepared pin, the two CASE_PIN reloads, the two
                # producer spans, the two stage dispatches and the
                # final same-admission selected cut - the restored
                # exact prior end, the released guard, the live
                # admission and the still-open resident.
                assert owner.value is held
                assert owner.state == "ACTIVE"
                assert owner.op.end == prior_end
                assert not owner.guard.locked()
                assert admission._invalid is False
                assert sc["encoder"]._state == "open"
                # The custody recheck uses the genuine reader (not a
                # guarded cut), so the real reader is restored first.
                real_read_bound = (
                    capture.PolicyCaptureReader.read_selection.__get__(
                        reader, type(reader)))
                monkeypatch.setattr(reader, "read_selection", real_read_bound)
                assert admission.recheck(deadline_ms=30000) is True
            # The stable per-case metadata of the current guarded
            # dispatches matches the exact legacy unguarded route with
            # the same good payloads in its separately measured phase,
            # on the exact case-bound grants derived through the
            # genuine existing case-scope intersection, without
            # requiring exact current-versus-legacy report identity
            # after the different truthful meters.
            restore()
            items = {c["case_id"]: c for c in cases_doc}
            for case_id, question, payload, (rows, u, case, original,
                                             effective, _restricted) in (
                ("h1", QUESTION_H1, producer_calls[0],
                 (rows1, u1, _case1, _original1, _effective1, _restricted1)),
                ("h4", QUESTION_H4, producer_calls[1],
                 (rows4, u4, _case4, _original4, _effective4,
                  _restricted4)),
            ):
                assert case.case_id == case_id
                with monkeypatch.context() as phase_patch:
                    phase_catalog = producer_fixture._catalog_counts(
                        phase_patch)
                    phase_dirs = producer_fixture._directory_counts(
                        phase_patch)
                    legacy = hybrid.search(
                        ctx.originals, ctx.derived, str(owner.op.path),
                        held.data.snapshot_id, question, payload,
                        query_space_id=expected[0],
                        query_definition_fingerprint=expected[1],
                        query_policy_id=expected[2],
                        query_execution_fingerprint=expected[3],
                        grants=effective, dense_k=60, lexical_k=60,
                        partition_cap=60, k=60, deadline_ms=120000,
                        trace=True)
                    assert phase_catalog == {"direct": 2, "nested": 6}
                    assert phase_dirs == {"start": 16, "done": 16}
                with monkeypatch.context() as bind_patch:
                    bind_catalog = producer_fixture._catalog_counts(
                        bind_patch)
                    bind_dirs = producer_fixture._directory_counts(
                        bind_patch)
                    legacy_diag = stage_loss.bind_stages(
                        ctx.originals, ctx.derived, str(owner.op.path),
                        owner, dataset_ac, case.case_id, declared_ac, legacy,
                        payload, query_space_id=expected[0],
                        query_definition_fingerprint=expected[1],
                        query_policy_id=expected[2],
                        query_execution_fingerprint=expected[3],
                        grants=original, restrictions=None,
                        deadline_ms=120000)
                    assert bind_catalog == {"direct": 0, "nested": 3}
                    assert bind_dirs == {"start": 11, "done": 11}
                item = items[case_id]
                assert item["catalog_id"] == legacy.catalog_id
                assert item["query_id"] == legacy.query_id
                assert item["gold_binding_id"] == legacy_diag.gold_binding_id
                assert item["ranking_binding_id"] == (
                    legacy_diag.ranking_binding_id)
                assert item["binder_invocation_id"] == (
                    legacy_diag.invocation_id)
                assert item["geometry_invocation_id"] == (
                    legacy_diag.geometry.invocation_id)
                assert item["eligible_row_count"] == (
                    legacy_diag.eligible_row_count)
                assert item["chosen_atom_occurrences"] == (
                    legacy_diag.chosen_atom_occurrences)
        finally:
            gold_fixture._close_owned(ctx, owner)
    finally:
        sc["encoder"].close()
    # Reaping evidence: the real cleanup reaped both real children.
    assert worker_child.poll() is not None and token_child.poll() is not None


def test_stage_loop_unavailable_declaration_refuses_without_work(
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
            producer_fixture._scenario(tmp_path, monkeypatch, expected))
        try:
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            # The pure all-case scope admission of the exact ordered
            # cohort with the withheld corpus refuses before any new
            # pin, directory, ingestion, original, selected or
            # protected work.
            admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            counts = producer_fixture._counts()
            restore = producer_fixture._install_counting(
                monkeypatch, ctx, owner, reader, counts)
            dir_counts = producer_fixture._directory_counts(monkeypatch)
            with monkeypatch.context() as patched:
                producer_calls = []
                producer_fixture._install_producer_counter(
                    patched, producer_calls)
                writes = []
                real_write = os.write
                os.write = transport._write_counter(
                    [session._tokenizer._child.stdin,
                     session._worker._child.stdin], writes)
                try:
                    with pytest.raises(runner.CohortRunnerError) as exc:
                        _stage_loop(admission, owner, dataset, bundle_ids,
                                    ("h1", "h2"), (expected, expected),
                                    sc["encoder"])
                finally:
                    os.write = real_write
            restore()
            assert producer_fixture._refusal_prefix(
                exc.value.progress) == ("PREFLIGHT", 2, 0, 0, 0, 2)
            assert producer_fixture._zero(counts)
            assert dir_counts == {"start": 0, "done": 0}
            assert writes == []
            assert producer_calls == []
            # No selected observation ran, so the admission is not
            # latched, the resident stays open, and the guard and
            # prior end are retained.
            assert admission._invalid is False
            assert owner.state == "ACTIVE"
            assert owner.op.end == prior_end
            assert not owner.guard.locked()
            assert sc["encoder"]._state == "open"
        finally:
            gold_fixture._close_owned(ctx, owner)
    finally:
        sc["encoder"].close()


def test_stage_loop_generation_change_after_first_case(tmp_path,
                                                       monkeypatch):
    real_argv = cpu._argv
    encoder_root = tmp_path / "encoder"
    encoder_root.mkdir(mode=0o700)
    sc = transport._scenario(encoder_root, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    ctx = owner = None
    try:
        session = sc["encoder"].cleanup_owner
        expected = transport._expected_tuple(session)
        events = []
        encode_guarded, forward_guarded, receipt_check = transport._observe(
            session, events)
        monkeypatch.setattr(session._tokenizer, "_encode_guarded",
                            encode_guarded)
        monkeypatch.setattr(session._worker, "_forward_guarded",
                            forward_guarded)
        monkeypatch.setattr(session, "_receipt", receipt_check)
        (ctx, dataset, bundle_ids, owner, policy_root, reader, payload) = (
            producer_fixture._scenario(tmp_path, monkeypatch, expected))
        try:
            m, b, g, p = producer_fixture._shapes(owner)
            directory = producer_fixture._per_directory(m, b, g, p)
            catalog_shape = producer_fixture._per_catalog(m, b, g, p)
            held = owner.value
            raw_pointer = owner.value.pointer
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            policy_snapshot = pin_eligibility._isolated_policy_snapshot(
                admission)
            anchor = pin_eligibility._bounded_admission(
                pin_eligibility._admitted_principal_grants(
                    policy_snapshot, admission.principal_id))
            full_grants = pin_eligibility._bound_grants(admission, anchor)
            # The mutation witness uses the same one test-local
            # projection to the genuinely admissible a/c batch over
            # the same actual raw original pin with the withheld b
            # still present and genuinely unavailable.
            dataset_ac, declared_ac = _admissible_gold_batch(
                owner, dataset, bundle_ids, admission)
            rows1, u1, _case1, _original1, _effective1, _restricted1 = (
                _eligible(ctx, owner, dataset_ac, "h1", full_grants))
            counts = producer_fixture._counts()
            changed = {"flag": False}
            completed = []
            # A test-local spy around the genuine revalidation publishes
            # the real same-wire generation at the first h4 delegate
            # call - by which point the ordered h1 case has genuinely
            # completed - before forwarding to the genuine
            # revalidation; the actual first-case completion is
            # observed through a test-local wrapper around the genuine
            # record step, so no numerical read index decides when the
            # change is published.
            real_revalidate = pin_eligibility.revalidate_current_pin_case

            def revalidate_at_h4(*args, **kwargs):
                if (not changed["flag"] and args[3] == "h4"
                        and completed == ["h1"]):
                    changed["flag"] = True
                    producer_fixture._change_generation(
                        policy_root, 2, payload)
                return real_revalidate(*args, **kwargs)
            monkeypatch.setattr(
                pin_eligibility, "revalidate_current_pin_case",
                revalidate_at_h4)
            real_case_record = runner._case_record

            def record_after_real(*args, **kwargs):
                real_case_record(*args, **kwargs)
                completed.append(args[-1])
            monkeypatch.setattr(runner, "_case_record", record_after_real)
            restore = producer_fixture._install_counting(
                monkeypatch, ctx, owner, reader, counts)
            dir_counts = producer_fixture._directory_counts(monkeypatch)
            with monkeypatch.context() as patched:
                catalog_counts = producer_fixture._catalog_counts(patched)
                producer_calls = []
                producer_fixture._install_producer_counter(
                    patched, producer_calls)
                token_pipe = session._tokenizer._child.stdin
                worker_pipe = session._worker._child.stdin
                writes = []
                real_write = os.write
                os.write = transport._write_counter(
                    [token_pipe, worker_pipe], writes)
                try:
                    with pytest.raises(runner.CohortRunnerError) as exc:
                        _stage_loop(admission, owner, dataset_ac, declared_ac,
                                    ("h1", "h4"), (expected, expected),
                                    sc["encoder"])
                finally:
                    os.write = real_write
            restore()
            assert changed["flag"] is True
            # The first case completes, and the second case's real
            # CASE_PIN reread observes the published same-wire
            # generation change and refuses the remainder before any
            # new second encoder, catalog, stage or full reload work.
            # Any other refusal point is unexpected; the bounded
            # content-free progress and fixture aggregate counts are
            # the only diagnostic material.
            if (producer_fixture._refusal_prefix(exc.value.progress)
                    != ("CASE_PIN", 2, 2, 1, 1, 0)):
                raise _unexpected_refusal(exc.value, (m, b, g, p))
            assert producer_fixture._refusal_prefix(
                exc.value.progress) == ("CASE_PIN", 2, 2, 1, 1, 0)
            # One initial plus the seven actual case-one pin loads;
            # the second case's CASE_PIN refuses before any new full
            # load, directory, ingestion, original or catalog work.
            assert counts["pin_load"] == 8
            assert dir_counts == {"start": 30, "done": 30}
            case1 = _bundle_work(directory, catalog_shape, u1, 2)
            assert (counts["bundle"], counts["derived"],
                    counts["original"]) == tuple(
                        directory[i] + case1[i] for i in range(3))
            # The initial two observations, the whole case-one span,
            # then the single refusing second CASE_PIN observation.
            assert counts["read"] == [1] * (2 + _case_reads(u1, 2) + 1)
            assert catalog_counts == {"direct": 2, "nested": 9}
            # One actual T1 and T2 span, the case-one producer
            # dispatch once with the exact one-row payload, and zero
            # second encoder or producer starts.
            assert sum(actual for pipe, _req, actual in writes
                       if pipe == id(token_pipe)) == (
                           transport._frame_len(QUESTION_H1))
            receipts = [r for kind, r in events if kind == "receipt"]
            assert len(receipts) == 1
            assert type(receipts[0]) is embedding_tokenizer.TokenIDReceipt
            assert receipts[0].input_sha256 == hashlib.sha256(
                json.dumps([QUESTION_H1, None], ensure_ascii=True,
                           separators=(",", ":")).encode()
            ).hexdigest()
            forwards = [rows for kind, rows in events if kind == "forward"]
            assert forwards == [[receipts[0].ids]]
            assert sum(actual for pipe, _req, actual in writes
                       if pipe == id(worker_pipe)) == (
                           transport._forward_frame_len(forwards[0]))
            assert session._tokenizer._calls == 1
            assert session._worker._calls == 1
            assert len(producer_calls) == 1
            assert producer_calls[0] == producer_fixture.PAYLOAD
            # The genuine admission latches on the observed change,
            # and the exact raw pointer and owner survive it with the
            # restored exact prior end and released guard.
            assert admission._invalid is True
            assert admission.recheck(deadline_ms=1000) is False
            assert owner.value is held
            assert owner.value.pointer is raw_pointer
            assert owner.state == "ACTIVE"
            assert owner.op.end == prior_end
            assert not owner.guard.locked()
            # The completed encode left the resident usable and open.
            assert sc["encoder"]._state == "open"
        finally:
            gold_fixture._close_owned(ctx, owner)
    finally:
        sc["encoder"].close()
