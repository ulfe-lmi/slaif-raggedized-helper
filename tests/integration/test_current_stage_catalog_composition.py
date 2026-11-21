"""Owned private current-policy stage-catalog commencement proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The test
reuses the already real structured-text stage/ranking support fixture
(``make_owned_support`` over the real ``make_sources``) and the
attributed selected-policy installation and scenario builder of
``test_current_ranking_dispatch_composition``, together with the
canonical five-case dataset and actual bundle IDs
(``dataset_and_bundles``).  The actual raw snapshot selector and the
real ``PinOwner.acquire_selected_data`` build the pinned data; the
exact synthetic policy wire bytes are installed through the existing
payload installer; the attributed test-local atomic selector fixture
publishes the selected record for the actual capture/decoder/request
methods and provides no writer qualification; the actual selected
changes use the same-wire generation change through that attributed
fixture.  Each fresh current admission is created only after the
expensive fixture setup that precedes its dispatch.

Counting wrappers attribute the real catalog, directory, bundle,
derived, original-store verified read, owner-load and reader calls to
catalog start/completion/direct loops versus direct work at the
intended boundaries; counts run from the private dispatch after fixture
acquisition, and the prior pin check and the separate real legacy
catalog path keep their own measured phases.  The bundle and original
catalog aggregates count the true total of the delegated catalog-phase
calls, and the start/completion/loop subcounters attribute each
delegated call within that total; the prior pin check and the distinct
denied window are measured from reset holder and directory attribution,
so each window is exact on its own; successful catalog and directory
completions are recorded after each real delegate returns alongside the
starts, and the per-catalog directory index resets at each measured
catalog so first/second attribution is exact.  The per-catalog formulas
follow the exact source: each full directory performs M + 2*P
ingestions and the two directories plus the direct loops yield
2*M+B+2*G+4*P for a complete catalog, every real structured-text
ingestion verifies one original, and each real load_group performs one
ingestion load plus two additional derived loads.
No local native execution: only the configured hosted CI executes the
real fixture; the three default hosted cases are collect-only here.
"""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import ingestion_store  # noqa: E402
from slaif_raggedized_helper import private_policy_capture as capture  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_catalog  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_directory  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_rows  # noqa: E402
from slaif_raggedized_helper import source_bound_stage_loss as stage_loss  # noqa: E402
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility  # noqa: E402
import test_current_ranking_dispatch_composition as ranking_composition  # noqa: E402

CREDENTIAL = ranking_composition.CREDENTIAL


def _dispatch(admission, owner, dataset, case_id, *, deadline_ms=30000):
    return stage_loss.bind_stage_catalog(admission, owner, dataset, case_id,
                                         deadline_ms=deadline_ms)


def _counts():
    return {
        "catalog": 0,
        "catalog_done": 0,
        "directory": [],
        "directory_done": [],
        "bundle_catalog": 0,
        "bundle_start": 0,
        "bundle_completion": 0,
        "bundle_loop": 0,
        "bundle_pass": 0,
        "derived_catalog": 0,
        "derived_pass": 0,
        "original_catalog": 0,
        "original_start": 0,
        "original_completion": 0,
        "original_loop": 0,
        "original_pass": 0,
        "originals_catalog": [],
        "originals_pass": [],
        "catalog_ids": [],
        "direct_ids": [],
        "read": 0,
        "pin_load": 0,
    }


def _assert_zero(holder):
    assert holder["counts"] == _counts()


def _install_witness(monkeypatch, ctx, owner, reader, holder, *,
                     change_after_association=None, change_after_catalog=None):
    # Counting wrappers that delegate the real functions at the intended
    # boundaries, attributed to catalog start/completion/direct loops
    # versus direct work by the load_catalog, load_directory and
    # owner._load depth.  ``change_after_association`` is the attributed
    # same-wire generation change fired once, armed by the caller
    # through the returned state, after the guarded route's real
    # metadata association; ``change_after_catalog`` is the same-wire
    # generation change fired once after the first completed catalog.
    # ``state["interrupt"]`` holds an optional non-Exception
    # interruption object raised after one genuine delegated read.  No
    # production hook is added.
    state = {"association_armed": False, "catalog_changed": False, "interrupt": None,
             "in_catalog": 0, "in_pin": 0, "dir_depth": 0, "dir_loads": 0}
    real_catalog = raw_snapshot_catalog.load_catalog
    real_directory = raw_snapshot_directory.load_directory
    real_bundle = ingestion_store.load
    real_derived = ctx.derived.load
    real_original = ctx.originals.read_verified
    real_pin_load = owner._load
    real_association = owner._association
    real_read = capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader)
    )

    def counting_catalog(*args, **kwargs):
        holder["counts"]["catalog"] += 1
        state["in_catalog"] += 1
        # Reset the per-catalog directory index so the first/second
        # directory attribution is exact for this measured catalog.
        state["dir_loads"] = 0
        try:
            result = real_catalog(*args, **kwargs)
        finally:
            state["in_catalog"] -= 1
        # Record the actual successful catalog completion after the
        # real delegate returns, alongside the start counted above.
        holder["counts"]["catalog_done"] += 1
        if (change_after_catalog is not None and not state["catalog_changed"]
                and holder["counts"]["catalog"] == 1):
            state["catalog_changed"] = True
            change_after_catalog()
        return result

    def counting_directory(*args, **kwargs):
        state["dir_depth"] += 1
        state["dir_loads"] += 1
        if state["in_catalog"]:
            phase = "catalog"
        elif state["in_pin"]:
            phase = "pin"
        else:
            phase = "direct"
        holder["counts"]["directory"].append(phase)
        try:
            result = real_directory(*args, **kwargs)
        finally:
            state["dir_depth"] -= 1
        # Record the actual successful directory completion after the
        # real delegate returns, alongside the start recorded above.
        holder["counts"]["directory_done"].append(phase)
        return result

    def bundle_phase():
        if state["in_catalog"]:
            if state["dir_depth"] > 0:
                return "start" if state["dir_loads"] == 1 else "completion"
            return "loop"
        return "pass"

    def counting_bundle(*args, **kwargs):
        container_id = args[2] if len(args) >= 3 else kwargs["container_id"]
        phase = bundle_phase()
        if phase == "pass":
            holder["counts"]["bundle_pass"] += 1
            holder["counts"]["direct_ids"].append(container_id)
        else:
            holder["counts"]["bundle_" + phase] += 1
            holder["counts"]["bundle_catalog"] += 1
            holder["counts"]["catalog_ids"].append(container_id)
        return real_bundle(*args, **kwargs)

    def counting_derived(*args, **kwargs):
        if bundle_phase() == "pass":
            holder["counts"]["derived_pass"] += 1
        else:
            holder["counts"]["derived_catalog"] += 1
        return real_derived(*args, **kwargs)

    def counting_original(*args, **kwargs):
        revision_id = args[0]
        phase = bundle_phase()
        if phase == "pass":
            holder["counts"]["original_pass"] += 1
            holder["counts"]["originals_pass"].append(revision_id)
        else:
            holder["counts"]["original_" + phase] += 1
            holder["counts"]["original_catalog"] += 1
            holder["counts"]["originals_catalog"].append(revision_id)
        return real_original(*args, **kwargs)

    def counting_pin_load(*args, **kwargs):
        holder["counts"]["pin_load"] += 1
        state["in_pin"] += 1
        try:
            return real_pin_load(*args, **kwargs)
        finally:
            state["in_pin"] -= 1

    def counting_association(*args, **kwargs):
        result = real_association(*args, **kwargs)
        if change_after_association is not None and state["association_armed"]:
            state["association_armed"] = False
            change_after_association()
        return result

    def counting_read(*args, **kwargs):
        holder["counts"]["read"] += 1
        result = real_read(*args, **kwargs)
        interrupt = state["interrupt"]
        if interrupt is not None:
            raise interrupt
        return result

    monkeypatch.setattr(raw_snapshot_catalog, "load_catalog", counting_catalog)
    monkeypatch.setattr(raw_snapshot_directory, "load_directory", counting_directory)
    monkeypatch.setattr(ingestion_store, "load", counting_bundle)
    monkeypatch.setattr(ctx.derived, "load", counting_derived)
    monkeypatch.setattr(ctx.originals, "read_verified", counting_original)
    monkeypatch.setattr(owner, "_load", counting_pin_load)
    monkeypatch.setattr(owner, "_association", counting_association)
    monkeypatch.setattr(reader, "read_selection", counting_read)
    return state


def _per_directory_shapes(members, bundles, groups, triples):
    # Exact source-derived per-catalog attribution: one full directory
    # performs M + 2*P ingestions (membership revalidation plus the
    # dense and lexical partition rebuilds) and the two directories plus
    # the direct loops yield 2*M+B+2*G+4*P for a complete catalog;
    # every real structured-text ingestion verifies one original.
    per_directory = members + 2 * triples
    return (per_directory, per_directory, bundles + 2 * groups)


def test_stage_catalog_h2_identity_and_restricted_h1(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_composition._scenario(tmp_path))
    try:
        assert len(bundle_ids) == 3
        bundles, groups, members, triples = ranking_composition._shapes(owner)
        per_bundle, per_derived, per_original = ranking_composition._per_catalog(
            bundles, groups, members, triples)
        assert per_original == per_bundle
        start, completion, loop = _per_directory_shapes(members, bundles, groups, triples)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        # (a) Stable synthetic h2 catalog identity/equality against the
        # separate real legacy path, one guarded catalog, two genuine
        # selected observations, exact pin/custody retained.
        stale_end = time.monotonic() - 60.0
        owner.op.end = stale_end
        holder = {"counts": _counts()}
        _install_witness(monkeypatch, ctx, owner, reader, holder)
        catalog = _dispatch(admission, owner, dataset, "h2")
        assert catalog.catalog_id == ctx.catalog_id
        assert catalog.snapshot_id == ctx.snapshot_id
        counts = holder["counts"]
        assert (counts["catalog"], counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == (1, per_bundle, per_derived, per_original)
        assert (counts["bundle_start"], counts["bundle_completion"],
                counts["bundle_loop"]) == (start, completion, loop)
        assert (counts["original_start"], counts["original_completion"],
                counts["original_loop"]) == (start, completion, loop)
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (0, 0, 0)
        # The real directory loads are exactly the catalog's start and
        # completion, separate from any direct or pin work; the
        # successful catalog and directory completions match the starts.
        assert counts["directory"] == ["catalog", "catalog"]
        assert counts["catalog_done"] == 1
        assert counts["directory_done"] == ["catalog", "catalog"]
        assert counts["read"] == 2
        assert counts["pin_load"] == 0
        # The separate real legacy path over the same stores/root/
        # snapshot yields the identical stable synthetic h2 catalog.
        legacy = raw_snapshot_catalog.load_catalog(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id)
        assert catalog == legacy
        assert admission._invalid is False
        assert owner.op.end == stale_end
        assert owner.state == "ACTIVE"
        assert not owner.guard.locked()
        monkeypatch.undo()
        # (a2) The same restricted (withheld corpus-two) policy: a pure
        # unknown-case refusal and an unavailable h2 refusal with zero
        # new catalog, directory or source work, and a narrower h1
        # acceptance whose real trusted catalog reaches the retained b
        # by original revision, the request selection scope and the
        # successful measured window kept separate.
        second = tmp_path / "second"
        second.mkdir(mode=0o700)
        (ctx2, dataset2, _bundle_ids2, owner2, policy_root2, reader2,
         chunks2) = ranking_composition._scenario(second, withhold_two=True)
        try:
            admission2 = ppr.request_current_view(reader2, CREDENTIAL, deadline_ms=30000)
            rows2 = raw_snapshot_rows.parse(owner2.value.data.row_map.map_bytes).rows
            row_b = next(row for row in rows2 if row.chunk_id == chunks2["b"])
            member_b = next(
                entry for entry in owner2.value.data.membership.entries
                if entry.revision_id == row_b.revision_id
            )
            # Prove the genuinely affected partition: the withheld
            # corpus-two document pairs make b's partition genuinely
            # unavailable under the selected policy while the real pin
            # still retains it.
            unavailable = set(policy_eligibility.unavailable_partitions(
                pin_eligibility._isolated_policy_snapshot(admission2),
                owner2.value.data.membership))
            assert member_b.partition_id in unavailable
            original_end2 = owner2.op.end
            holder2 = {"counts": _counts()}
            _install_witness(monkeypatch, ctx2, owner2, reader2, holder2)
            with pytest.raises(stage_loss.StageBindingError):
                _dispatch(admission2, owner2, dataset2, "missing")
            _assert_zero(holder2)
            assert admission2._invalid is False
            assert owner2.op.end == original_end2
            assert not owner2.guard.locked()
            monkeypatch.undo()
            holder2 = {"counts": _counts()}
            _install_witness(monkeypatch, ctx2, owner2, reader2, holder2)
            with pytest.raises(stage_loss.StageBindingError):
                _dispatch(admission2, owner2, dataset2, "h2")
            _assert_zero(holder2)
            assert admission2._invalid is False
            assert owner2.state == "ACTIVE"
            assert owner2.op.end == original_end2
            assert not owner2.guard.locked()
            monkeypatch.undo()
            holder2 = {"counts": _counts()}
            _install_witness(monkeypatch, ctx2, owner2, reader2, holder2)
            catalog2 = _dispatch(admission2, owner2, dataset2, "h1")
            assert catalog2.catalog_id == ctx2.catalog_id
            assert catalog2.snapshot_id == ctx2.snapshot_id
            counts2 = holder2["counts"]
            assert (counts2["catalog"], counts2["bundle_catalog"],
                    counts2["derived_catalog"], counts2["original_catalog"]) == (
                        1, per_bundle, per_derived, per_original)
            assert (counts2["bundle_start"], counts2["bundle_completion"],
                    counts2["bundle_loop"]) == (start, completion, loop)
            assert (counts2["original_start"], counts2["original_completion"],
                    counts2["original_loop"]) == (start, completion, loop)
            assert (counts2["bundle_pass"], counts2["derived_pass"],
                    counts2["original_pass"]) == (0, 0, 0)
            assert counts2["directory"] == ["catalog", "catalog"]
            assert counts2["catalog_done"] == 1
            assert counts2["directory_done"] == ["catalog", "catalog"]
            assert counts2["read"] == 2
            assert counts2["pin_load"] == 0
            # The request selection scope (corpus one) excludes b while
            # the successful measured window reaches the retained b by
            # original revision through the trusted nested catalog.
            assert member_b.bundle_container_id in counts2["catalog_ids"]
            assert member_b.bundle_container_id not in counts2["direct_ids"]
            assert row_b.revision_id in counts2["originals_catalog"]
            assert row_b.revision_id not in counts2["originals_pass"]
            assert admission2._invalid is False
            assert owner2.op.end == original_end2
            assert owner2.state == "ACTIVE"
            assert not owner2.guard.locked()
        finally:
            ranking_composition._close_owned(ctx2, owner2)
    finally:
        ranking_composition._close_owned(ctx, owner)


def test_stage_catalog_change_after_association_denies_before_catalog(tmp_path, monkeypatch):
    (ctx, dataset, _bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_composition._scenario(tmp_path))
    try:
        def change_generation():
            # The synthetic selected generation changes while the wire
            # payload stays identical: the same audited raw capture.
            documents = ranking_composition._documents_from_membership(owner)
            ranking_composition._publish_selection(
                policy_root, 2,
                ranking_composition._encode_policy(
                    [ranking_composition.PRINCIPAL], documents))

        _bundles, _groups, members, triples = ranking_composition._shapes(owner)
        holder = {"counts": _counts()}
        state = _install_witness(monkeypatch, ctx, owner, reader, holder,
                                 change_after_association=change_generation)
        # A real completed prior PinOwner.check from the same owner in
        # its own measured phase: one directory load, M+2*P actual
        # bundle and original ingests and M+6*P derived loads for this
        # fixture, with no catalog or selected-read work; it provides
        # synthetic setup evidence only and keeps its own window.
        checked = owner.check(deadline_ms=30000)
        assert checked is owner.value
        m2p = members + 2 * triples
        m6p = members + 6 * triples
        prior_snapshot = dict(holder["counts"])
        assert prior_snapshot["pin_load"] == 1
        assert prior_snapshot["directory"] == ["pin"]
        assert prior_snapshot["bundle_pass"] == m2p
        assert prior_snapshot["original_pass"] == m2p
        assert prior_snapshot["derived_pass"] == m6p
        assert (prior_snapshot["catalog"], prior_snapshot["bundle_catalog"],
                prior_snapshot["derived_catalog"],
                prior_snapshot["original_catalog"]) == (0, 0, 0, 0)
        assert (prior_snapshot["bundle_start"], prior_snapshot["bundle_completion"],
                prior_snapshot["bundle_loop"], prior_snapshot["original_start"],
                prior_snapshot["original_completion"],
                prior_snapshot["original_loop"]) == (0, 0, 0, 0, 0, 0)
        assert len(prior_snapshot["direct_ids"]) == m2p
        assert len(prior_snapshot["originals_pass"]) == m2p
        assert prior_snapshot["catalog_ids"] == []
        assert prior_snapshot["originals_catalog"] == []
        assert prior_snapshot["catalog_done"] == 0
        assert prior_snapshot["directory_done"] == ["pin"]
        assert prior_snapshot["read"] == 0
        assert owner.state == "ACTIVE"
        original_end = owner.op.end
        held_before = owner.value
        # The independent request establishment after the measured
        # prior pin window: its own initial read is excluded from the
        # denied proof window by the reset below.
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        # The distinct denied window starts from a reset holder and
        # directory attribution, so only its own work is measured.
        holder["counts"] = _counts()
        state["association_armed"] = True
        with pytest.raises(stage_loss.StageBindingError):
            _dispatch(admission, owner, dataset, "h2")
        # The actual selected generation advanced immediately after the
        # guarded route's real association, before the catalog call: the
        # real selected denial latches the admission, and only the
        # denied window has zero new catalog, directory, bundle or
        # store work and exactly one actual selected reread.
        counts = holder["counts"]
        denied_window = dict(counts)
        denied_window["read"] = 0
        assert denied_window == _counts()
        assert counts["read"] == 1
        assert admission._invalid is True
        # The latched recheck refuses with zero further reader calls.
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 1
        # The real selection change leaves the same exact raw held
        # value and pointer untouched.
        assert owner.value is held_before
        assert owner.value.pointer is held_before.pointer
        assert owner.op.end == original_end
        assert owner.state == "ACTIVE"
        assert not owner.guard.locked()
    finally:
        ranking_composition._close_owned(ctx, owner)


def test_stage_catalog_change_after_catalog_and_interruption(tmp_path, monkeypatch):
    (ctx, dataset, _bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_composition._scenario(tmp_path))
    try:
        bundles, groups, members, triples = ranking_composition._shapes(owner)
        per_bundle, per_derived, per_original = ranking_composition._per_catalog(
            bundles, groups, members, triples)
        assert per_original == per_bundle
        start, completion, loop = _per_directory_shapes(members, bundles, groups, triples)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)

        def change_generation():
            # The synthetic selected generation changes while the wire
            # payload stays identical: the same audited raw capture.
            documents = ranking_composition._documents_from_membership(owner)
            ranking_composition._publish_selection(
                policy_root, 2,
                ranking_composition._encode_policy(
                    [ranking_composition.PRINCIPAL], documents))

        original_end = owner.op.end
        held_before = owner.value
        holder = {"counts": _counts()}
        state = _install_witness(monkeypatch, ctx, owner, reader, holder,
                                 change_after_catalog=change_generation)
        with pytest.raises(stage_loss.StageBindingError):
            _dispatch(admission, owner, dataset, "h2")
        # The actual selection advanced after the real full catalog
        # returned: one genuine complete catalog and two live
        # observations, and the usable catalog output is denied.
        counts = holder["counts"]
        assert (counts["catalog"], counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == (1, per_bundle, per_derived, per_original)
        assert (counts["bundle_start"], counts["bundle_completion"],
                counts["bundle_loop"]) == (start, completion, loop)
        assert (counts["original_start"], counts["original_completion"],
                counts["original_loop"]) == (start, completion, loop)
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (0, 0, 0)
        assert counts["directory"] == ["catalog", "catalog"]
        assert counts["catalog_done"] == 1
        assert counts["directory_done"] == ["catalog", "catalog"]
        assert counts["read"] == 2
        assert counts["pin_load"] == 0
        assert admission._invalid is True
        # The latched recheck refuses with zero further reader calls.
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 2
        # The real selection change leaves the same exact raw held
        # value and pointer untouched.
        assert owner.value is held_before
        assert owner.value.pointer is held_before.pointer
        # Association and prior custody preserved.
        assert owner.op.end == original_end
        assert owner.state == "ACTIVE"
        assert not owner.guard.locked()
        checked = owner.check(deadline_ms=30000)
        assert checked is owner.value
        assert owner.state == "ACTIVE"
        custody_end = owner.op.end
        # A bounded interruption subcase on the existing node: the exact
        # marker object propagates by identity through the cleanup, with
        # custody restored and no admission latch (only ordinary
        # observation failures latch).
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert fresh.selection.generation == 2
        interrupt = KeyboardInterrupt("owned-interruption")
        holder["counts"] = _counts()
        state["interrupt"] = interrupt
        with pytest.raises(BaseException) as excinfo:
            _dispatch(fresh, owner, dataset, "h2")
        assert excinfo.value is interrupt
        counts = holder["counts"]
        assert (counts["catalog"], counts["catalog_done"],
                counts["bundle_catalog"], counts["bundle_pass"],
                counts["derived_catalog"], counts["derived_pass"],
                counts["original_catalog"], counts["original_pass"]) == (0, 0, 0, 0, 0, 0, 0, 0)
        assert counts["directory"] == []
        assert counts["directory_done"] == []
        assert counts["pin_load"] == 0
        assert counts["read"] == 1
        assert fresh._invalid is False
        assert owner.op.end == custody_end
        assert owner.state == "ACTIVE"
        assert not owner.guard.locked()
    finally:
        ranking_composition._close_owned(ctx, owner)
