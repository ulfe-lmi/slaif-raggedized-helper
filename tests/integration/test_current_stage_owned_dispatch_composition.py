"""Owned private stage-owned source dispatch composition proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The
test reuses the already real structured-text stage/ranking support
fixture (``make_owned_support`` over the real ``make_sources``) and
the attributed selected-policy installation and scenario builder of
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
expensive fixture setup and the unguarded comparison setup that
precede its dispatch, and the already grounded actual hybrid trace is
built by the real legacy hybrid search in that unguarded setup,
supplied to both routes as the existing typed supplied input.

Counting wrappers attribute the real catalog, directory, bundle,
derived, original-store verified read, owner-load, association and
reader calls to pin, catalog and pass windows at the intended
boundaries, record the exact ``owner.op.end`` at every full directory
start and at every real association, and record the exact
``owner.op.end`` after each delegated borrowed span returns; counts
run from the private dispatch after fixture acquisition, and the
separate real legacy stage path keeps its own measured counters.  The per-phase formulas follow the
exact source: each full pin directory performs M+2*P actual
bundle/original ingests (and M+6*P derived) and each complete catalog
performs 2*M+B+2*G+4*P ingests, so the expected route performs
eleven full directories - five independent pin revalidations, the one
direct stage catalog (two load_directory trees) and the two retained
ranking catalogs (two trees each) - while the two Gold passes each
load the K declared bundles and the two selected ranking passes each
load the J eligible unique bundles (not chunk IDs when grouped).
Derived shapes are asserted, never treated as proof of per-original
current authorization.
No local native execution: only the configured hosted CI executes the
real fixture; the three default hosted cases are collect-only here.
"""
import json
import struct
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import ingestion_store  # noqa: E402
from slaif_raggedized_helper import private_policy_capture as capture  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import raw_hybrid_search as hybrid  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_catalog  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_directory  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_rows  # noqa: E402
from slaif_raggedized_helper import source_bound_ranking as ranking  # noqa: E402
from slaif_raggedized_helper import source_bound_stage_loss as stage_loss  # noqa: E402
from slaif_raggedized_helper import text_evaluation_gold_binding as gold  # noqa: E402
import test_current_ranking_dispatch_composition as ranking_composition  # noqa: E402

CREDENTIAL = ranking_composition.CREDENTIAL


def _dispatch(admission, owner, dataset, case_id, result, payload, ids, bundle_ids):
    return stage_loss.bind_stage_owned_dispatch(
        admission, owner, dataset, case_id, result, payload,
        query_space_id=ids["query_space_id"],
        query_definition_fingerprint=ids["query_definition_fingerprint"],
        query_policy_id=ids["query_policy_id"],
        query_execution_fingerprint=ids["query_execution_fingerprint"],
        gold_bundle_ids=bundle_ids,
    )


def _comparison_setup(ctx, dataset):
    """Unguarded comparison setup: the already grounded actual hybrid
    trace supplied to both routes, derived from the exact h2 case
    question and the catalog's own declared identity fields, with no
    witness and no admission."""
    data = json.loads(dataset)
    case = next(c for c in data["cases"] if c["case_id"] == "h2")
    question = case["question"]
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
    result = hybrid.search(
        ctx.originals,
        ctx.derived,
        ctx.root,
        ctx.snapshot_id,
        question,
        payload,
        **ids,
        grants=ctx.grants,
        dense_k=60,
        lexical_k=60,
        partition_cap=60,
        k=60,
        trace=True,
    )
    return question, ids, payload, result


def _counts():
    return {
        "catalog": 0,
        "catalog_done": 0,
        "directory": [],
        "directory_done": [],
        "directory_ends": [],
        "bundle_pin": 0,
        "bundle_catalog": 0,
        "bundle_pass": 0,
        "derived_pin": 0,
        "derived_catalog": 0,
        "derived_pass": 0,
        "original_pin": 0,
        "original_catalog": 0,
        "original_pass": 0,
        "pin_load": 0,
        "read": 0,
        "association": 0,
        "association_ends": [],
        "read_changed_at": None,
        "spans": [],
    }


def _assert_zero(holder):
    assert holder["counts"] == _counts()


def _install_witness(monkeypatch, ctx, owner, reader, holder, *,
                     change_after_catalog=None, change_at_read=None,
                     change=None, interrupt_at_association=None):
    # Counting wrappers that delegate the real functions at the
    # intended boundaries, attributed to pin, catalog and pass windows
    # by the owner._load, load_catalog and load_directory depth.
    # ``change_after_catalog`` is the attributed same-wire generation
    # change fired once after the first completed trusted stage
    # catalog returns, before the next guarded pin work;
    # ``change_at_read`` is the exact one-based reader call index at
    # which the separate ``change`` callable fires once, immediately
    # before the real read at that index; ``interrupt_at_association``
    # is the exact one-based association index at which
    # ``holder["interrupt_marker"]`` (a non-Exception interruption
    # object) is raised.  No production hook is added.
    state = {"in_catalog": 0, "in_pin": 0, "catalog_changed": False,
             "read_changed": False}
    real_catalog = raw_snapshot_catalog.load_catalog
    real_directory = raw_snapshot_directory.load_directory
    real_bundle = ingestion_store.load
    real_derived = ctx.derived.load
    real_original = ctx.originals.read_verified
    real_pin_load = owner._load
    real_association = owner._association
    real_read = capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader))

    def phase():
        if state["in_pin"]:
            return "pin"
        if state["in_catalog"]:
            return "catalog"
        return "pass"

    def counting_catalog(*args, **kwargs):
        holder["counts"]["catalog"] += 1
        state["in_catalog"] += 1
        try:
            result = real_catalog(*args, **kwargs)
        finally:
            state["in_catalog"] -= 1
        # Record the actual successful catalog completion after the
        # real delegate returns, alongside the start counted above.
        holder["counts"]["catalog_done"] += 1
        return result

    def counting_directory(*args, **kwargs):
        holder["counts"]["directory"].append(phase())
        # The exact operation end while this full directory runs is
        # the delegate's clipped absolute end.
        holder["counts"]["directory_ends"].append(owner.op.end)
        result = real_directory(*args, **kwargs)
        # A full directory completed only after the real delegate
        # returned successfully.
        holder["counts"]["directory_done"].append(phase())
        return result

    def counting_bundle(*args, **kwargs):
        holder["counts"]["bundle_" + phase()] += 1
        return real_bundle(*args, **kwargs)

    def counting_derived(*args, **kwargs):
        holder["counts"]["derived_" + phase()] += 1
        return real_derived(*args, **kwargs)

    def counting_original(*args, **kwargs):
        holder["counts"]["original_" + phase()] += 1
        return real_original(*args, **kwargs)

    def counting_pin_load(*args, **kwargs):
        holder["counts"]["pin_load"] += 1
        state["in_pin"] += 1
        try:
            return real_pin_load(*args, **kwargs)
        finally:
            state["in_pin"] -= 1

    def counting_association(*args, **kwargs):
        holder["counts"]["association"] += 1
        # The exact operation end held while this association runs.
        holder["counts"]["association_ends"].append(owner.op.end)
        if (interrupt_at_association is not None
                and holder["counts"]["association"] == interrupt_at_association):
            raise holder["interrupt_marker"]
        return real_association(*args, **kwargs)

    def counting_read(*args, **kwargs):
        holder["counts"]["read"] += 1
        if (change is not None and change_at_read is not None
                and holder["counts"]["read"] == change_at_read
                and not state["read_changed"]):
            state["read_changed"] = True
            holder["counts"]["read_changed_at"] = holder["counts"]["read"]
            change()
        return real_read(*args, **kwargs)

    monkeypatch.setattr(raw_snapshot_catalog, "load_catalog", counting_catalog)
    monkeypatch.setattr(raw_snapshot_directory, "load_directory", counting_directory)
    monkeypatch.setattr(ingestion_store, "load", counting_bundle)
    monkeypatch.setattr(ctx.derived, "load", counting_derived)
    monkeypatch.setattr(ctx.originals, "read_verified", counting_original)
    monkeypatch.setattr(owner, "_load", counting_pin_load)
    monkeypatch.setattr(owner, "_association", counting_association)
    monkeypatch.setattr(reader, "read_selection", counting_read)
    # Delegate spies: the exact prior owner end must be preserved
    # after each actual borrowed span returns.
    real_revalidate = pin_eligibility.revalidate_current_pin_case
    real_catalog_entry = stage_loss.bind_stage_catalog
    real_gold = gold.bind_pinned
    real_ranking = ranking.bind_pinned

    def spy_revalidate(*args, **kwargs):
        result = real_revalidate(*args, **kwargs)
        holder["counts"]["spans"].append(("revalidate", owner.op.end))
        return result

    def spy_catalog(*args, **kwargs):
        result = real_catalog_entry(*args, **kwargs)
        holder["counts"]["spans"].append(("catalog", owner.op.end))
        # The same-wire change fires once the first completed trusted
        # stage catalog has returned, before the next guarded pin work.
        if change_after_catalog is not None and not state["catalog_changed"]:
            state["catalog_changed"] = True
            change_after_catalog()
        return result

    def spy_gold(*args, **kwargs):
        result = real_gold(*args, **kwargs)
        holder["counts"]["spans"].append(("gold", owner.op.end))
        return result

    def spy_ranking(*args, **kwargs):
        result = real_ranking(*args, **kwargs)
        holder["counts"]["spans"].append(("ranking", owner.op.end))
        return result

    monkeypatch.setattr(pin_eligibility, "revalidate_current_pin_case",
                        spy_revalidate)
    monkeypatch.setattr(stage_loss, "bind_stage_catalog", spy_catalog)
    monkeypatch.setattr(gold, "bind_pinned", spy_gold)
    monkeypatch.setattr(ranking, "bind_pinned", spy_ranking)


def _change_generation(owner, policy_root):
    # The synthetic selected generation changes while the wire payload
    # stays identical: the same audited raw capture.
    documents = ranking_composition._documents_from_membership(owner)
    ranking_composition._publish_selection(
        policy_root, 2,
        ranking_composition._encode_policy(
            [ranking_composition.PRINCIPAL], documents))


def test_owned_h2_matches_legacy_stage(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, _chunks) = (
        ranking_composition._scenario(tmp_path))
    try:
        assert len(bundle_ids) == 3
        bundles, groups, members, triples = ranking_composition._shapes(owner)
        assert (members, triples) == (3, 3)
        per_bundle, per_derived, per_original = ranking_composition._per_catalog(
            bundles, groups, members, triples)
        pin_shape = (members + 2 * triples, members + 6 * triples,
                     members + 2 * triples)
        # Unguarded comparison setup before the fresh admission
        # begins its request lifetime.
        _question, ids, payload, result = _comparison_setup(ctx, dataset)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        common_end = admission._end
        # A still-live pin whose prior acquisition end is already
        # expired: every borrowed span must use the common admission
        # end and restore this exact prior value.
        stale_end = time.monotonic() - 60.0
        owner.op.end = stale_end
        holder = {"counts": _counts()}
        _install_witness(monkeypatch, ctx, owner, reader, holder)
        diagnosis = _dispatch(admission, owner, dataset, "h2", result, payload,
                              ids, tuple(bundle_ids))
        counts = holder["counts"]
        # Eleven full directories: five independent pin revalidations,
        # the one direct stage catalog (two load_directory trees) and
        # the two retained ranking catalogs (two trees each).
        assert counts["pin_load"] == 5
        assert counts["catalog"] == 3 and counts["catalog_done"] == 3
        assert counts["directory"] == (
            ["pin", "catalog", "catalog", "pin", "pin",
             "catalog", "catalog", "catalog", "catalog", "pin", "pin"])
        assert counts["directory_done"] == counts["directory"]
        # The exact common operation end: every full directory started
        # under the same recorded admission end.
        assert counts["directory_ends"] == [common_end] * 11
        # Preservation of the exact prior owner end on each actual
        # borrowed span: five revalidations, the one catalog, one Gold
        # and one ranking.
        assert [name for name, _end in counts["spans"]] == (
            ["revalidate", "catalog", "revalidate", "gold", "revalidate",
             "ranking", "revalidate", "revalidate"])
        assert [end for _name, end in counts["spans"]] == [stale_end] * 8
        # The exact operation end held at every association, including
        # the actual final stage result cutoff's fifteenth association,
        # with the prior owner end restored after it.
        assert counts["association_ends"] == [common_end] * 15
        # Per-phase physical work: M+2*P per pin directory,
        # 2*M+B+2*G+4*P per complete catalog, the two Gold passes each
        # loading the K declared bundles and the two selected ranking
        # passes each loading the J eligible unique bundles.
        rows = raw_snapshot_rows.parse(owner.value.data.row_map.map_bytes).rows
        k = len(bundle_ids)
        j = len({row.bundle_container_id for row in rows})
        assert (counts["bundle_pin"], counts["derived_pin"],
                counts["original_pin"]) == tuple(5 * side for side in pin_shape)
        assert (counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == tuple(
                    3 * side for side in (per_bundle, per_derived, per_original))
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (2 * k + 2 * j, 2 * k + 2 * j,
                                             2 * k + 2 * j)
        # Real selected reads: two per revalidation, two for the
        # direct catalog, one before each Gold bundle load in both
        # passes, one before each ranking catalog dispatch and
        # selected bundle load in both passes, and one at the actual
        # final stage result cutoff.
        assert counts["read"] == 2 * 5 + 2 + 2 * k + (2 + 2 * j) + 1
        assert admission._invalid is False
        assert owner.state == "ACTIVE"
        assert owner.op.end == stale_end
        assert not owner.guard.locked()
        # The stable h2 and complete real all-atom Gold fixture matches
        # the legacy stage identities and diagnosis; the separate real
        # legacy path keeps its own measured counters.
        monkeypatch.undo()
        legacy_holder = {"counts": _counts()}
        _install_witness(monkeypatch, ctx, owner, reader, legacy_holder)
        legacy = stage_loss.bind_stages(
            ctx.originals, ctx.derived, ctx.root, owner, dataset, "h2",
            tuple(bundle_ids), result, payload, **ids, grants=ctx.grants)
        legacy_counts = legacy_holder["counts"]
        assert legacy_counts["pin_load"] == 5
        assert legacy_counts["catalog"] == 3
        assert legacy_counts["directory"] == (
            ["pin", "catalog", "catalog", "pin", "pin",
             "catalog", "catalog", "catalog", "catalog", "pin", "pin"])
        assert (legacy_counts["bundle_pin"], legacy_counts["derived_pin"],
                legacy_counts["original_pin"]) == tuple(
                    5 * side for side in pin_shape)
        assert (legacy_counts["bundle_catalog"],
                legacy_counts["derived_catalog"],
                legacy_counts["original_catalog"]) == tuple(
                    3 * side for side in (per_bundle, per_derived, per_original))
        assert (legacy_counts["bundle_pass"], legacy_counts["derived_pass"],
                legacy_counts["original_pass"]) == (2 * k + 2 * j, 2 * k + 2 * j,
                                                    2 * k + 2 * j)
        assert legacy_counts["read"] == 0
        assert legacy_counts["spans"] == []
        assert diagnosis == legacy
        assert diagnosis.invocation_id == legacy.invocation_id
    finally:
        ranking_composition._close_owned(ctx, owner)


def test_owned_change_after_catalog_denies_next_pin(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, _chunks) = (
        ranking_composition._scenario(tmp_path))
    try:
        bundles, groups, members, triples = ranking_composition._shapes(owner)
        per_bundle, per_derived, per_original = ranking_composition._per_catalog(
            bundles, groups, members, triples)
        pin_shape = (members + 2 * triples, members + 6 * triples,
                     members + 2 * triples)
        _question, ids, payload, result = _comparison_setup(ctx, dataset)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        common_end = admission._end

        def change_generation():
            _change_generation(owner, policy_root)

        stale_end = time.monotonic() - 60.0
        owner.op.end = stale_end
        holder = {"counts": _counts()}
        _install_witness(monkeypatch, ctx, owner, reader, holder,
                         change_after_catalog=change_generation)
        held_before = owner.value
        with pytest.raises(stage_loss.StageBindingError,
                           match="^owned stage diagnosis refused$") as err:
            _dispatch(admission, owner, dataset, "h2", result, payload, ids,
                      tuple(bundle_ids))
        assert err.value.__cause__ is None and err.value.__suppress_context__
        counts = holder["counts"]
        # Positive prior physical work up to the exact mutation cut:
        # one completed pin revalidation and one complete direct
        # catalog (two full directories) with their real selected
        # reads.
        assert counts["pin_load"] == 1
        assert counts["catalog"] == 1 and counts["catalog_done"] == 1
        assert counts["directory"] == ["pin", "catalog", "catalog"]
        assert counts["directory_ends"] == [common_end] * 3
        assert (counts["bundle_pin"], counts["derived_pin"],
                counts["original_pin"]) == pin_shape
        assert (counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == (per_bundle, per_derived,
                                                per_original)
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (0, 0, 0)
        # Two revalidation reads and two catalog reads, then the one
        # genuine pre-load recheck that observes the real selected
        # generation change.
        assert counts["read"] == 2 + 2 + 1
        # The real current denial latches the admission and refuses
        # the next physical pin start before any directory or source
        # load: zero later guarded stages and no diagnosis.
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 5
        assert counts["spans"] == [("revalidate", stale_end),
                                   ("catalog", stale_end)]
        # The same exact raw held value and pointer, the restored
        # guard and the exact prior owner end.
        assert owner.state == "ACTIVE"
        assert owner.value is held_before
        assert owner.op.end == stale_end
        assert not owner.guard.locked()
    finally:
        ranking_composition._close_owned(ctx, owner)


def test_owned_final_cutoff_denies_assembled_result(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, _chunks) = (
        ranking_composition._scenario(tmp_path))
    try:
        bundles, groups, members, triples = ranking_composition._shapes(owner)
        per_bundle, per_derived, per_original = ranking_composition._per_catalog(
            bundles, groups, members, triples)
        pin_shape = (members + 2 * triples, members + 6 * triples,
                     members + 2 * triples)
        rows = raw_snapshot_rows.parse(owner.value.data.row_map.map_bytes).rows
        k = len(bundle_ids)
        j = len({row.bundle_container_id for row in rows})
        # The actual final stage observation is the last real reader
        # call of the complete route: one read after every completed
        # revalidation, catalog, Gold and ranking observation.
        final_read = 2 * 5 + 2 + 2 * k + (2 + 2 * j) + 1
        _question, ids, payload, result = _comparison_setup(ctx, dataset)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        common_end = admission._end

        def change_generation():
            _change_generation(owner, policy_root)

        stale_end = time.monotonic() - 60.0
        owner.op.end = stale_end

        # Arm the same-wire change immediately before the real read at
        # the exact one-based final reader index.
        holder = {"counts": _counts()}
        _install_witness(monkeypatch, ctx, owner, reader, holder,
                         change_at_read=final_read, change=change_generation)
        held_before = owner.value
        with pytest.raises(stage_loss.StageBindingError,
                           match="^owned stage diagnosis refused$") as err:
            _dispatch(admission, owner, dataset, "h2", result, payload, ids,
                      tuple(bundle_ids))
        assert err.value.__cause__ is None and err.value.__suppress_context__
        counts = holder["counts"]
        # The actually completed final pin revalidation and the whole
        # assembled route: five full pin revalidations, the one direct
        # stage catalog and the two retained ranking catalogs, with no
        # extra full source load.
        assert counts["pin_load"] == 5
        assert counts["catalog"] == 3 and counts["catalog_done"] == 3
        assert counts["directory"] == (
            ["pin", "catalog", "catalog", "pin", "pin",
             "catalog", "catalog", "catalog", "catalog", "pin", "pin"])
        assert counts["directory_ends"] == [common_end] * 11
        assert (counts["bundle_pin"], counts["derived_pin"],
                counts["original_pin"]) == tuple(5 * side for side in pin_shape)
        assert (counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == tuple(
                    3 * side for side in (per_bundle, per_derived, per_original))
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (2 * k + 2 * j, 2 * k + 2 * j,
                                             2 * k + 2 * j)
        # Every prior genuine observation completed; the one actual
        # final stage observation read the changed selection and
        # refused the assembled result with that same pin.
        assert counts["read"] == final_read
        assert counts["read_changed_at"] == final_read
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == final_read
        assert counts["spans"] == [
            ("revalidate", stale_end), ("catalog", stale_end),
            ("revalidate", stale_end), ("gold", stale_end),
            ("revalidate", stale_end), ("ranking", stale_end),
            ("revalidate", stale_end), ("revalidate", stale_end),
        ]
        assert owner.state == "ACTIVE"
        assert owner.value is held_before
        assert owner.op.end == stale_end
        assert not owner.guard.locked()
        # (a) Bounded interruption evidence on the existing node: a
        # non-Exception interruption raised at the final stage result
        # cutoff propagates by identity with the exact owner custody
        # preserved and no usable diagnosis, on a fresh admitted
        # request created before its own counting witness.
        class _Interrupted(BaseException):
            pass

        marker = _Interrupted()
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert fresh.selection.generation == 2
        fresh_end = fresh._end
        monkeypatch.undo()
        int_holder = {"counts": _counts(), "interrupt_marker": marker}
        _install_witness(monkeypatch, ctx, owner, reader, int_holder,
                         interrupt_at_association=15)
        with pytest.raises(_Interrupted) as excinfo:
            _dispatch(fresh, owner, dataset, "h2", result, payload, ids,
                      tuple(bundle_ids))
        # The captured object is the exact marker instance, propagated
        # by identity through the final cutoff's short exclusive
        # acquisition, at the route's fifteenth and final association.
        assert excinfo.value is marker
        int_counts = int_holder["counts"]
        assert int_counts["pin_load"] == 5
        assert int_counts["catalog"] == 3
        assert int_counts["directory"] == (
            ["pin", "catalog", "catalog", "pin", "pin",
             "catalog", "catalog", "catalog", "catalog", "pin", "pin"])
        assert int_counts["association"] == 15
        # Every association ran under the exact clipped end of its
        # actual operation, the final cutoff's included, and the prior
        # owner end was restored after the interrupted final association.
        assert int_counts["association_ends"] == [fresh_end] * 15
        assert int_counts["read"] == final_read - 1
        assert fresh._invalid is False
        assert owner.state == "ACTIVE"
        assert owner.value is held_before
        assert owner.op.end == stale_end
        assert not owner.guard.locked()
    finally:
        ranking_composition._close_owned(ctx, owner)
