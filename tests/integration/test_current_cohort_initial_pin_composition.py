"""Owned private initial cohort pin composition proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The real
hosted source fixture (``make_owned_support`` from
``test_source_bound_support_ci_composition`` over the real
``make_sources``), the canonical five-case dataset and actual bundle IDs
(``dataset_and_bundles`` from
``test_source_cohort_runner_composition``), the actual raw snapshot
selector and the real ``PinOwner.acquire_selected_data`` build the
pinned data; the exact synthetic policy wire bytes are installed
through the existing payload installer and the clearly attributed
test-local atomic selector fixture of
``test_current_gold_dispatch_composition`` publishes the selected
record - it provides no writer qualification, and the actual selected
generation changes use the same-wire generation change through that
attributed fixture, triggered by test-local wrappers that delegate the
real functions at the intended boundaries (no production hook is added
and no physical read is simulated).  Each fresh current admission is
created only after the expensive fixture setup that precedes its
dispatch, with its own initial selected read excluded from the counted
span, and the counts run from the initial cohort pin after fixture
acquisition, with the actual delegated raw directory load starts and
successful completions counted by their own wrappers kept separate from
the fixture baseline and the separately measured legacy
``_pin_observation`` comparison.  No local native execution: only the
configured hosted CI executes the real fixture.
"""
import hashlib
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility
from slaif_raggedized_helper import private_policy_request as ppr
from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import raw_snapshot_directory
from slaif_raggedized_helper import source_bound_stage_loss as stage_loss
from slaif_raggedized_helper import source_cohort_runner as runner
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility
from slaif_raggedized_helper import text_evaluation_dataset
import test_current_gold_dispatch_composition as gold_fixture


def _identifiers(case_ids):
    # Declared encoder identifier tuples under the exact grammar the
    # genuine declaration admission enforces (64 hex, sha256-prefixed
    # 64 hex, 64 hex, 64 hex), derived deterministically per case ID.
    declared = []
    for case_id in case_ids:
        base = hashlib.sha256(("slaif-cip-ident:" + case_id).encode("ascii")).hexdigest()
        declared.append((
            hashlib.sha256((base + ":space").encode("ascii")).hexdigest(),
            "sha256:" + hashlib.sha256((base + ":definition").encode("ascii")).hexdigest(),
            hashlib.sha256((base + ":policy").encode("ascii")).hexdigest(),
            hashlib.sha256((base + ":execution").encode("ascii")).hexdigest(),
        ))
    return tuple(declared)


def _initial_pin(admission, owner, dataset, case_ids, bundle_ids, *, deadline_ms=30000):
    cohort = runner.Cohort("held_out", tuple(case_ids))
    return runner._current_cohort_initial_pin(
        admission, owner, dataset, cohort, _identifiers(case_ids), bundle_ids,
        runner.Config("cip-cfg", "cip-declaration"), runner.Budget(*runner._MAX_BUDGET),
        deadline_ms=deadline_ms,
    )


def _change_generation(owner, policy_root, generation):
    # The synthetic selected generation changes while the wire payload
    # stays identical (same raw pin).
    documents = gold_fixture._documents_from_membership(owner)
    gold_fixture._publish_selection(
        policy_root, generation,
        gold_fixture._encode_policy([gold_fixture.PRINCIPAL], documents),
    )


def _full_directory_shape(owner):
    """The real full-directory work shape over the actual fixture:
    M membership ingestions plus 2P per-partition dense and lexical
    source groups (P unique partition/bundle/batch triples), with the
    structured-text fixture reading the original once per ingestion and
    each source group loading its bundle and both of its stored derived
    snapshots; derived purely from the held pin data the fixture already
    captured (its membership and row map), with no additional catalog
    or source work."""
    data = owner.value.data
    m = len(data.membership.entries)
    triples = {(r.partition_id, r.bundle_container_id, r.batch_container_id)
               for r in data.row_map.rows}
    p_groups = len(triples)
    return (m + 2 * p_groups, m + 6 * p_groups, m + 2 * p_groups), m, p_groups


def _refusal_prefix(progress):
    return (progress.phase, progress.intended, progress.attempted,
            progress.completed, progress.refused, progress.pending)


def test_initial_cohort_h1_h4_matches_legacy_observation(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = gold_fixture._scenario(
        tmp_path, withhold_two=True)
    try:
        # The measured full-directory shape is derived purely from the
        # held pin data before the current admission begins its request
        # lifetime.
        shape, m, p_groups = _full_directory_shape(owner)
        assert (m, p_groups) == (3, 3)
        admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                             deadline_ms=30000)
        # A still-live pin whose prior acquisition end is already
        # expired: the guarded entry must use its own clipped
        # cooperative end and restore this exact prior value.
        prior_end = time.monotonic() - 60.0
        owner.op.end = prior_end
        counts = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
        # The actual delegated raw directory load starts and successful
        # completions for the entry span, kept separate from the
        # fixture baseline that ran before the witnesses.
        dir_counts = {"start": 0, "done": 0}
        real_directory_load = raw_snapshot_directory.load_directory

        def counting_directory_load(*args, **kwargs):
            dir_counts["start"] += 1
            result = real_directory_load(*args, **kwargs)
            dir_counts["done"] += 1
            return result

        monkeypatch.setattr(raw_snapshot_directory, "load_directory",
                            counting_directory_load)
        # The withheld member b is outside the effective h1/h4 case
        # scope, yet the trusted rebuild really reaches its retained
        # revision: the actual verified original reads are recorded by
        # a wrapper that delegates the existing counting witness.
        member_b = next(e for e in owner.value.data.membership.entries
                        if p.admit_record("Scope", e.scope_bytes).corpus == "two")
        declared = text_evaluation_dataset.admit(dataset)
        case_h1 = next(c for c in declared.cases if c.case_id == "h1")
        _original, effective_h1, _restricted = stage_loss._admit_authority(
            admission.grants, None, case_h1.scope, stage_loss._Meter(), lambda: None)
        assert not p.reader_allows(p.admit_record("Scope", member_b.scope_bytes),
                                   effective_h1, None)
        # Both exact narrowed case scopes exclude the withheld member b.
        case_h4 = next(c for c in declared.cases if c.case_id == "h4")
        _original4, effective_h4, _restricted4 = stage_loss._admit_authority(
            admission.grants, None, case_h4.scope, stage_loss._Meter(),
            lambda: None)
        assert not p.reader_allows(p.admit_record("Scope", member_b.scope_bytes),
                                   effective_h4, None)
        # The actual installed withdrawal for b: the installed selected
        # policy retains b's document but withdraws b's exact revision
        # pair, so b's partition is genuinely unavailable under the
        # retained membership.
        policy_snapshot = pin_eligibility._isolated_policy_snapshot(admission)
        installed = {doc.document_id: doc.admitted
                     for doc in policy_snapshot.documents}
        b_scope = p.admit_record("Scope", member_b.scope_bytes)
        b_pair = (member_b.revision_id, member_b.source_scope_sha256)
        assert b_pair not in installed[b_scope.document_id]
        assert member_b.partition_id in set(
            policy_eligibility.unavailable_partitions(
                policy_snapshot, owner.value.data.membership))
        witnessed_original = ctx.originals.read_verified
        revisions = []

        def recording_original(*args, **kwargs):
            revisions.append(args[0])
            return witnessed_original(*args, **kwargs)

        monkeypatch.setattr(ctx.originals, "read_verified", recording_original)
        # The exact cooperative end observed at the actual association
        # and loader: one clipped value, set once before the first
        # association and restored only after the final observation.
        ends = {"association": [], "loader": []}
        real_association = owner._association
        counted_load = owner._load

        def watching_association():
            ends["association"].append(owner.op.end)
            return real_association()

        def watching_load(snapshot_id):
            ends["loader"].append(owner.op.end)
            return counted_load(snapshot_id)

        monkeypatch.setattr(owner, "_association", watching_association)
        monkeypatch.setattr(owner, "_load", watching_load)
        result = _initial_pin(admission, owner, dataset, ("h1", "h4"), bundle_ids)
        # One actual full directory and two genuine selection
        # observations in the measured span, with the exact M+2*P
        # bundle/original and M+6*P derived calls and one delegated
        # raw directory start that successfully completes.
        assert counts["pin_load"] == 1
        assert counts["read"] == 2
        assert (counts["bundle"], counts["derived"], counts["original"]) == shape
        assert dir_counts == {"start": 1, "done": 1}
        # The exact retained raw value, the true operation end observed
        # at the actual association and loader - the one clipped
        # cooperative end, equal to the fresh admission's own end - and
        # the retained custody.
        assert result is owner.value
        observed = ends["association"] + ends["loader"]
        assert len(observed) == 3 and len(set(observed)) == 1
        assert observed[0] == admission._end
        assert observed[0] != prior_end
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
        assert admission._invalid is False
        # The trusted full directory rebuild reaches the retained
        # withheld revision b outside the effective case scope.
        assert member_b.revision_id in revisions
        # The separately measured legacy _pin_observation: its own real
        # full directory and bounded checks, counted separately.
        monkeypatch.undo()
        legacy_counts = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, legacy_counts)
        # The legacy comparison's own delegated raw directory counts,
        # kept separate from the entry span.
        legacy_dir_counts = {"start": 0, "done": 0}

        def counting_legacy_directory_load(*args, **kwargs):
            legacy_dir_counts["start"] += 1
            result = real_directory_load(*args, **kwargs)
            legacy_dir_counts["done"] += 1
            return result

        monkeypatch.setattr(raw_snapshot_directory, "load_directory",
                            counting_legacy_directory_load)
        legacy = runner._pin_observation(
            owner, ctx.originals, ctx.derived, ctx.root, None,
            runner._Meter(runner._MAX_BUDGET[12], runner._MAX_BUDGET[13], lambda: None),
            runner._Deadline(time.monotonic(), 30000),
        )
        assert legacy_counts["pin_load"] == 1
        assert legacy_counts["read"] == 0
        assert (legacy_counts["bundle"], legacy_counts["derived"],
                legacy_counts["original"]) == shape
        assert legacy_dir_counts == {"start": 1, "done": 1}
        assert result == legacy
    finally:
        gold_fixture._close_owned(ctx, owner)


def test_initial_cohort_h2_denies_unavailable_scope_before_protected_work(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = gold_fixture._scenario(
        tmp_path, withhold_two=True)
    try:
        # The measured full-directory shape is derived purely from the
        # held pin data before the current admission begins its request
        # lifetime.
        _shape, _m, _p_groups = _full_directory_shape(owner)
        admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                             deadline_ms=30000)
        prior_end = time.monotonic() - 60.0
        owner.op.end = prior_end
        # Prove the policy and the exact effective scope from the owned
        # fixture: b is genuinely unavailable under the actual selected
        # policy, and readable under the later broad h2 case's exact
        # effective scope.
        policy_snapshot = pin_eligibility._isolated_policy_snapshot(admission)
        unavailable = set(policy_eligibility.unavailable_partitions(
            policy_snapshot, owner.value.data.membership))
        member_b = next(e for e in owner.value.data.membership.entries
                        if p.admit_record("Scope", e.scope_bytes).corpus == "two")
        assert member_b.partition_id in unavailable
        declared = text_evaluation_dataset.admit(dataset)
        case_h2 = next(c for c in declared.cases if c.case_id == "h2")
        _original, effective_h2, _restricted = stage_loss._admit_authority(
            admission.grants, None, case_h2.scope, stage_loss._Meter(), lambda: None)
        assert p.reader_allows(p.admit_record("Scope", member_b.scope_bytes),
                               effective_h2, None)
        # The later broad h2 case makes the exact ordered cohort fail
        # before any new pin/directory/ingestion/original or selected
        # check; incomplete attempts stay zero.
        counts = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
        # The actual delegated raw directory load starts and successful
        # completions for the entry span, kept separate from the
        # fixture baseline that ran before the witnesses.
        dir_counts = {"start": 0, "done": 0}
        real_directory_load = raw_snapshot_directory.load_directory

        def counting_directory_load(*args, **kwargs):
            dir_counts["start"] += 1
            result = real_directory_load(*args, **kwargs)
            dir_counts["done"] += 1
            return result

        monkeypatch.setattr(raw_snapshot_directory, "load_directory",
                            counting_directory_load)
        with pytest.raises(runner.CohortRunnerError) as exc:
            _initial_pin(admission, owner, dataset, ("h1", "h2"), bundle_ids)
        assert _refusal_prefix(exc.value.progress) == ("PREFLIGHT", 2, 0, 0, 0, 2)
        gold_fixture._assert_zero(counts)
        assert dir_counts == {"start": 0, "done": 0}
        # No selected observation ran, so the admission is not latched,
        # and the guard and prior end are retained.
        assert admission._invalid is False
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
    finally:
        gold_fixture._close_owned(ctx, owner)


def test_initial_cohort_generation_change_refuses_without_usable_pin(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = gold_fixture._scenario(tmp_path)
    try:
        # The closed-ownership fixture is built before the admission so
        # its genuine acquisition I/O never counts as initial pin work
        # and the request lifetime begins after it.
        shape, _m, _p_groups = _full_directory_shape(owner)
        # The fresh admission for the first change, created before the
        # witness so its own initial selected read is excluded from the
        # counted span.
        admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                             deadline_ms=30000)
        prior_end = time.monotonic() - 60.0
        owner.op.end = prior_end
        # The exact pre-dispatch held value and raw pointer for the
        # change proofs.
        held = owner.value
        raw_pointer = owner.value.pointer
        # (c1) The real selected generation changes under the same raw
        # pointer and owner immediately after the real metadata
        # association and before the actual reload: the first delegated
        # selection read is the genuine pre-load recheck read, and it
        # observes the change - one genuine selected refusal with zero
        # new directory or source reads (actual started/completed
        # directory and source work: 0 started, 0 completed).
        counts = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
        # The actual delegated raw directory load starts and successful
        # completions for this change, kept separate from the fixture
        # baseline that ran before the witnesses.
        dir_counts = {"start": 0, "done": 0}
        real_directory_load = raw_snapshot_directory.load_directory

        def counting_directory_load(*args, **kwargs):
            dir_counts["start"] += 1
            result = real_directory_load(*args, **kwargs)
            dir_counts["done"] += 1
            return result

        monkeypatch.setattr(raw_snapshot_directory, "load_directory",
                            counting_directory_load)
        real_read = reader.read_selection
        state = {"changed": False}

        def change_on_first_read(*args, **kwargs):
            if not state["changed"]:
                state["changed"] = True
                _change_generation(owner, policy_root, 2)
            return real_read(*args, **kwargs)

        monkeypatch.setattr(reader, "read_selection", change_on_first_read)
        with pytest.raises(runner.CohortRunnerError) as exc:
            _initial_pin(admission, owner, dataset, ("h1", "h4"), bundle_ids)
        assert state["changed"] is True
        assert _refusal_prefix(exc.value.progress) == ("PREFLIGHT", 2, 0, 0, 0, 2)
        assert counts["read"] == 1
        assert counts["pin_load"] == 0
        assert (counts["bundle"], counts["derived"], counts["original"]) == (0, 0, 0)
        assert dir_counts == {"start": 0, "done": 0}
        # Latch and saved custody.
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 1
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
        # The same raw pin across the change: the exact pre-dispatch
        # held value and raw pointer are retained.
        assert owner.value is held
        assert owner.value.pointer is raw_pointer
        # Reset between subcases before the next fresh admission and
        # fresh witness: the inherited Gold witness rewraps the current
        # bundle/derived/original/owner loads, so sequential
        # installation without a reset would nest old count wrappers.
        monkeypatch.undo()
        # (c2) Post-reload actual selection change with a separate fresh
        # admission in that same node: the first delegated read is the
        # genuine pre-load recheck, the change lands after completion of
        # the real full reload, and the second delegated read is the
        # genuine final selection observation - one complete reload
        # produces no usable pin (actual started/completed directory and
        # source work: 1 started, 1 completed).
        # The exact same pre-dispatch held value and raw pointer across
        # both genuine selected generation changes.
        assert owner.value is held
        assert owner.value.pointer is raw_pointer
        # The separate fresh admission for this change, created before
        # the witness so its own initial selected read is excluded from
        # the counted span.
        fresh = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                         deadline_ms=30000)
        counts2 = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts2)
        # The actual delegated raw directory load starts and successful
        # completions for this change, kept separate from the fixture
        # baseline and the first change.
        dir_counts2 = {"start": 0, "done": 0}

        def counting_directory_load2(*args, **kwargs):
            dir_counts2["start"] += 1
            result = real_directory_load(*args, **kwargs)
            dir_counts2["done"] += 1
            return result

        monkeypatch.setattr(raw_snapshot_directory, "load_directory",
                            counting_directory_load2)
        real_read2 = reader.read_selection

        def change_after_full_reload(*args, **kwargs):
            if counts2["read"] == 1:
                _change_generation(owner, policy_root, 3)
            return real_read2(*args, **kwargs)

        monkeypatch.setattr(reader, "read_selection", change_after_full_reload)
        with pytest.raises(runner.CohortRunnerError) as exc:
            _initial_pin(fresh, owner, dataset, ("h1", "h4"), bundle_ids)
        assert _refusal_prefix(exc.value.progress) == ("PREFLIGHT", 2, 0, 0, 0, 2)
        # One completed directory, two genuine selection observations,
        # no usable PinData, the latch and exact restored custody, with
        # the one delegated raw directory start successfully completing
        # and the exact pre-dispatch held value and raw pointer retained
        # across both changes.
        assert counts2["pin_load"] == 1
        assert counts2["read"] == 2
        assert (counts2["bundle"], counts2["derived"], counts2["original"]) == shape
        assert dir_counts2 == {"start": 1, "done": 1}
        assert fresh._invalid is True
        assert fresh.recheck(deadline_ms=1000) is False
        assert counts2["read"] == 2
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
        assert owner.value is held
        assert owner.value.pointer is raw_pointer
        # Reset between subcases before the next fresh admission and
        # fresh witness, keeping the separate positive and negative
        # evidence and their counters apart.
        monkeypatch.undo()
        # (c3) Bounded exact interruption: a non-Exception BaseException
        # propagates by identity at the loader boundary before any
        # directory work starts (actual started/completed directory and
        # source work: 0 started, 0 completed), with the prior owner
        # custody restored.
        class _Interrupted(BaseException):
            pass

        marker = _Interrupted()
        interrupted = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                               deadline_ms=30000)
        counts3 = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts3)
        # The actual delegated raw directory load starts and successful
        # completions for this interruption, kept separate from the
        # fixture baseline and the two changes.
        dir_counts3 = {"start": 0, "done": 0}

        def counting_directory_load3(*args, **kwargs):
            dir_counts3["start"] += 1
            result = real_directory_load(*args, **kwargs)
            dir_counts3["done"] += 1
            return result

        monkeypatch.setattr(raw_snapshot_directory, "load_directory",
                            counting_directory_load3)

        def interrupting_load(snapshot_id):
            raise marker

        monkeypatch.setattr(owner, "_load", interrupting_load)
        with pytest.raises(_Interrupted) as caught:
            _initial_pin(interrupted, owner, dataset, ("h1", "h4"), bundle_ids)
        # The captured object is the exact marker instance that was
        # raised, propagated by identity.
        assert caught.value is marker
        assert counts3["pin_load"] == 0
        assert (counts3["bundle"], counts3["derived"], counts3["original"]) == (0, 0, 0)
        assert dir_counts3 == {"start": 0, "done": 0}
        # The genuine pre-load recheck completed before the
        # interruption; nothing else ran, and nothing latched.
        assert counts3["read"] == 1
        assert interrupted._invalid is False
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
    finally:
        gold_fixture._close_owned(ctx, owner)
