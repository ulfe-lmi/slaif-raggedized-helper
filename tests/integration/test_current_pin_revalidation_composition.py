"""Owned private case-bound pin revalidation composition proof.

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
dispatch, and the counts run from the revalidation after fixture
acquisition, with the legacy ``PinOwner.check`` comparison counted
separately.  No local native execution: only the configured hosted CI
executes the real fixture.
"""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility
from slaif_raggedized_helper import private_policy_request as ppr
from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import source_bound_stage_loss as stage_loss
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility
from slaif_raggedized_helper import text_evaluation_dataset
from slaif_raggedized_helper.raw_snapshot_pin import PinOwner
import test_current_gold_dispatch_composition as gold_fixture


def _revalidate(admission, owner, dataset, case_id, *, deadline_ms=30000):
    return pin_eligibility.revalidate_current_pin_case(
        admission, owner, dataset, case_id, deadline_ms=deadline_ms
    )


def _full_directory_shape(owner):
    """The real full-directory work shape over the actual fixture:
    M membership ingestions plus 2P per-partition dense and lexical
    source groups (P unique partition/bundle/batch triples), with the
    structured-text fixture reading the original once per ingestion and
    each source group loading its bundle and both of its stored derived
    snapshots; derived purely from the held pin data the fixture already
    captured (its membership and row map), with no additional catalog or
    source work."""
    data = owner.value.data
    m = len(data.membership.entries)
    triples = {(r.partition_id, r.bundle_container_id, r.batch_container_id)
               for r in data.row_map.rows}
    group_count = len(triples)
    return (
        (m + 2 * group_count, m + 3 * (2 * group_count), m + 2 * group_count),
        m,
        group_count,
    )


def _change_generation(owner, policy_root):
    # The synthetic selected generation changes while the wire payload
    # stays identical (same raw pin).
    documents = gold_fixture._documents_from_membership(owner)
    gold_fixture._publish_selection(
        policy_root, 2, gold_fixture._encode_policy([gold_fixture.PRINCIPAL], documents)
    )


def test_case_bound_h2_matches_legacy_check(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = gold_fixture._scenario(tmp_path)
    try:
        # The measured full-directory shape is derived purely from the
        # held pin data before the current admission begins its request
        # lifetime.
        shape, m, p_groups = _full_directory_shape(owner)
        assert (m, p_groups) == (3, 3)
        admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                             deadline_ms=30000)
        # A still-live pin whose prior acquisition end is already
        # expired: the guarded variant must use its own clipped
        # cooperative end and restore this exact prior value.
        prior_end = time.monotonic() - 60.0
        owner.op.end = prior_end
        counts = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
        result = _revalidate(admission, owner, dataset, "h2")
        # One actual full directory and two genuine selection
        # observations in the measured span.
        assert counts["pin_load"] == 1
        assert counts["read"] == 2
        assert (counts["bundle"], counts["derived"], counts["original"]) == shape
        # Exact retained capture and prior end restoration.
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
        assert admission._invalid is False
        # The same validated held PinData, equal to the legacy owned
        # observation, which is counted separately.
        assert result is owner.value
        monkeypatch.undo()
        legacy_counts = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, legacy_counts)
        legacy = owner.check(deadline_ms=30000)
        assert legacy_counts["pin_load"] == 1
        assert legacy_counts["read"] == 0
        assert (legacy_counts["bundle"], legacy_counts["derived"],
                legacy_counts["original"]) == shape
        assert result == legacy
    finally:
        gold_fixture._close_owned(ctx, owner)


def test_case_bound_gate_denies_unavailable_scope_before_protected_work(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = gold_fixture._scenario(
        tmp_path, withhold_two=True)
    try:
        # The measured full-directory shape is derived purely from the
        # held pin data before the current admission begins its request
        # lifetime.
        shape, _m, _p_groups = _full_directory_shape(owner)
        admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                             deadline_ms=30000)
        prior_end = time.monotonic() - 60.0
        owner.op.end = prior_end
        # b is genuinely unavailable under the actual selected policy.
        def _member_corpus(ident):
            entry = next(e for e in owner.value.data.membership.entries
                         if e.bundle_container_id == ident)
            return p.admit_record("Scope", entry.scope_bytes).corpus

        unavailable = set(policy_eligibility.unavailable_partitions(
            pin_eligibility._isolated_policy_snapshot(admission),
            owner.value.data.membership))
        b_id = next(ident for ident in bundle_ids
                    if _member_corpus(ident) == "two")
        member_b = next(e for e in owner.value.data.membership.entries
                        if e.bundle_container_id == b_id)
        assert member_b.partition_id in unavailable
        # (a) Pure h2 refusal for genuinely unavailable b: the scoped
        # permission is verified before any protected work in the
        # denied path, with zero new directory/source work.
        counts1 = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts1)
        with pytest.raises(pin_eligibility.PolicyPinEligibilityError):
            _revalidate(admission, owner, dataset, "h2")
        gold_fixture._assert_zero(counts1)
        assert admission._invalid is False
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
        # (b) The distinct h1 request accepts after the actual case
        # narrows to unaffected scope: the case-bound effective grants
        # exclude b and retain the unaffected member.
        declared = text_evaluation_dataset.admit(dataset)
        case_h1 = next(c for c in declared.cases if c.case_id == "h1")
        _original, effective_h1, _restricted = stage_loss._admit_authority(
            admission.grants, None, case_h1.scope, stage_loss._Meter(), lambda: None
        )
        b_scope = p.admit_record("Scope", member_b.scope_bytes)
        assert not p.reader_allows(b_scope, effective_h1, None)
        member_a = next(e for e in owner.value.data.membership.entries
                        if e.bundle_container_id != b_id
                        and p.admit_record("Scope", e.scope_bytes).corpus == "one")
        assert p.reader_allows(p.admit_record("Scope", member_a.scope_bytes),
                               effective_h1, None)
        # The trusted full directory rebuild still reaches b outside
        # the effective case scope: the accepted case runs the complete
        # one-full-directory work shape over every membership entry and
        # partition source group, and the actual verified original
        # reads are recorded by a wrapper that delegates the existing
        # counting witness.
        monkeypatch.undo()
        counts2 = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts2)
        witnessed_original = ctx.originals.read_verified
        revisions = []

        def recording_original(*args, **kwargs):
            revisions.append(args[0])
            return witnessed_original(*args, **kwargs)

        monkeypatch.setattr(ctx.originals, "read_verified", recording_original)
        result = _revalidate(admission, owner, dataset, "h1")
        # The withheld member b is outside the effective case scope, yet
        # the trusted full read reaches its actual verified revision.
        assert member_b.revision_id in revisions
        assert counts2["pin_load"] == 1
        assert counts2["read"] == 2
        assert (counts2["bundle"], counts2["derived"], counts2["original"]) == shape
        assert result is owner.value
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
        assert admission._invalid is False
    finally:
        gold_fixture._close_owned(ctx, owner)


def test_case_bound_first_selection_denial_before_full_directory(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = gold_fixture._scenario(tmp_path)
    try:
        admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                             deadline_ms=30000)
        prior_end = time.monotonic() - 60.0
        owner.op.end = prior_end
        counts = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
        # Change the actual selected generation with the same raw pin
        # immediately after the real metadata association and before
        # the first full directory: the first delegated selection read
        # is the genuine pre-load recheck read.
        real_read = reader.read_selection
        state = {"changed": False}

        def change_on_first_read(*args, **kwargs):
            if not state["changed"]:
                state["changed"] = True
                _change_generation(owner, policy_root)
            return real_read(*args, **kwargs)

        monkeypatch.setattr(reader, "read_selection", change_on_first_read)
        with pytest.raises(pin_eligibility.PolicyPinEligibilityError):
            _revalidate(admission, owner, dataset, "h2")
        # The real first selection denial: one genuine delegated read
        # observed the changed generation, with zero full directory
        # starts or source reads.
        assert state["changed"] is True
        assert counts["read"] == 1
        assert counts["pin_load"] == 0
        assert (counts["bundle"], counts["derived"], counts["original"]) == (0, 0, 0)
        # Latch and saved custody.
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 1
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
    finally:
        gold_fixture._close_owned(ctx, owner)


def test_case_bound_final_observation_denial_after_full_reload(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = gold_fixture._scenario(tmp_path)
    try:
        # The closed-ownership fixture is built before the admission
        # and the witness so its genuine acquisition I/O never counts
        # as revalidation work and the request lifetime begins after
        # it.
        other = PinOwner()
        other.acquire_selected_data(ctx.originals, ctx.derived, ctx.root,
                                    deadline_ms=30000)
        other.close()
        assert other.state == "CLOSED"
        # The measured full-directory shape is derived purely from the
        # held pin data before the current admission begins its request
        # lifetime.
        shape, _m, _p_groups = _full_directory_shape(owner)
        admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                             deadline_ms=30000)
        prior_end = time.monotonic() - 60.0
        owner.op.end = prior_end
        counts = gold_fixture._counts()
        gold_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
        # Change the actual selection after completion of the real
        # full reload: the first delegated read is the genuine pre-load
        # recheck before the full directory, the second delegated read
        # is the genuine final selection observation.
        real_read = reader.read_selection

        def change_after_full_reload(*args, **kwargs):
            if counts["read"] == 1:
                _change_generation(owner, policy_root)
            return real_read(*args, **kwargs)

        monkeypatch.setattr(reader, "read_selection", change_after_full_reload)
        with pytest.raises(pin_eligibility.PolicyPinEligibilityError):
            _revalidate(admission, owner, dataset, "h2")
        # One completed directory, two genuine selection observations,
        # no usable PinData, the latch and exact restored custody.
        assert counts["pin_load"] == 1
        assert counts["read"] == 2
        assert (counts["bundle"], counts["derived"], counts["original"]) == shape
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 2
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
        # (a) Bounded owner subcases: a closed owner and a busy
        # nonreentrant guard each refuse at custody with zero protected
        # work, on a fresh non-latched admission.
        custody = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                           deadline_ms=30000)
        after_a = dict(counts)
        with pytest.raises(pin_eligibility.PolicyPinEligibilityError):
            _revalidate(custody, other, dataset, "h2")
        assert counts == after_a
        assert custody._invalid is False
        assert owner.guard.acquire(blocking=False)
        try:
            with pytest.raises(pin_eligibility.PolicyPinEligibilityError):
                _revalidate(custody, owner, dataset, "h2")
        finally:
            owner.guard.release()
        assert counts == after_a
        assert custody._invalid is False
        # (b) Deadline subcase under the real monotonic clock: an
        # admitted request whose own 1000 ms lifetime is exhausted
        # refuses before any protected work, without latching.
        late = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                        deadline_ms=1000)
        before_late = dict(counts)
        time.sleep(1.1)
        with pytest.raises(pin_eligibility.PolicyPinEligibilityError):
            _revalidate(late, owner, dataset, "h2")
        assert counts == before_late
        assert late._invalid is False
        # (c) Interruption subcase: a non-Exception BaseException
        # propagates by identity, with the prior owner custody
        # restored and no full directory start or source read.
        class _Interrupted(BaseException):
            pass

        marker = _Interrupted()

        def interrupting_load(snapshot_id):
            raise marker

        monkeypatch.setattr(owner, "_load", interrupting_load)
        interrupted = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                               deadline_ms=30000)
        before_int = dict(counts)
        with pytest.raises(_Interrupted) as excinfo:
            _revalidate(interrupted, owner, dataset, "h2")
        # The captured object is the exact marker instance that was
        # raised, propagated by identity.
        assert excinfo.value is marker
        assert counts["pin_load"] == before_int["pin_load"]
        assert (counts["bundle"], counts["derived"], counts["original"]) == (
            before_int["bundle"], before_int["derived"], before_int["original"])
        # The genuine pre-load recheck completed before the
        # interruption; nothing else ran.
        assert counts["read"] == before_int["read"] + 1
        assert interrupted._invalid is False
        assert owner.state == "ACTIVE"
        assert owner.op.end == prior_end
        assert not owner.guard.locked()
    finally:
        gold_fixture._close_owned(ctx, owner)
