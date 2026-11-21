"""Owned private grade-owned direct catalog composition proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The real
hosted source fixture (``make_owned_support`` from
``test_source_bound_support_ci_composition`` over the real
``make_sources``), the canonical five-case dataset and actual bundle IDs
(``dataset_and_bundles`` from
``test_source_cohort_runner_composition``), the actual raw snapshot
selector and the real ``PinOwner.acquire_selected_data`` build the
pinned data; the exact synthetic policy wire bytes are installed through
the existing payload installer, and the clearly attributed test-local
atomic selector fixture (re-derived from the 009-z current-view lane
fixture in ``tests/unit/test_private_policy_request.py``) publishes the
selected record for the actual capture/decoder/request methods - it
provides no writer qualification, and the actual selected changes use
the same-wire generation change through that attributed fixture.  Each
fresh current admission is created only after the expensive fixture
setup that precedes its dispatch.  Counting wrappers attribute the real
catalog, bundle, derived, original-store verified read, owner-load,
owner-association and reader calls at the intended boundaries; counts
run from the private commencement after fixture acquisition, and the
baseline measurements are kept separate from the slice.  The per-catalog
count formulas are derived from the exact source: each catalog load
performs two load_directory trees, each revalidating the whole declared
membership (one ingestion load per entry) and rebuilding every dense
and lexical partition once per distinct (partition, bundle, batch)
triple through one real load_group, plus one ingestion load per unique
row-map bundle and one per unique (bundle, batch) group, each through
one real load_group; every load_group performs one ingestion load plus
two additional derived loads, and every ingestion load performs one
derived load and one verified original read.  No local native
execution: only the configured hosted CI executes the real fixture.
"""
import json
import os
from pathlib import Path

import pytest

from slaif_raggedized_helper import ingestion_store  # noqa: E402
from slaif_raggedized_helper import evaluation_program as program  # noqa: E402
from slaif_raggedized_helper import private_policy_capture as capture  # noqa: E402
from slaif_raggedized_helper import private_policy_payload as payload_install  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import provenance_records as p  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_catalog  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_directory  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_rows  # noqa: E402
from slaif_raggedized_helper import source_bound_stage_loss as stage_loss  # noqa: E402
from slaif_raggedized_helper import source_cohort_runner as runner  # noqa: E402
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility  # noqa: E402
from slaif_raggedized_helper import supplied_rank_metrics as metrics  # noqa: E402
from slaif_raggedized_helper import text_evaluation_dataset  # noqa: E402
import test_current_ranking_dispatch_composition as ranking_fixture  # noqa: E402
import test_source_cohort_runner_composition as cohort_fixture  # noqa: E402

CREDENTIAL = ranking_fixture.CREDENTIAL
PRINCIPAL_ID = ranking_fixture.PRINCIPAL_ID
VERIFIER = ranking_fixture.VERIFIER
OPERATIONS = ranking_fixture.OPERATIONS


class _ForbiddenBoundary(BaseException):
    pass


def _counts():
    return {
        "catalog": 0,
        "catalog_done": 0,
        "directory": 0,
        "directory_done": 0,
        "bundle": 0,
        "derived": 0,
        "original": 0,
        "pin_load": 0,
        "read": 0,
    }


def _zero(counts):
    for key in counts:
        counts[key] = 0


def _forbid_slice_boundaries(monkeypatch):
    """No pin observation, producer, binder, scoring or report work escapes the slice."""

    def forbidden(*args, **kwargs):
        raise _ForbiddenBoundary()

    monkeypatch.setattr(runner, "_produce", forbidden)
    monkeypatch.setattr(runner, "_bind", forbidden)
    monkeypatch.setattr(runner, "_aggregate", forbidden)
    monkeypatch.setattr(runner, "_pin_observation", forbidden)
    monkeypatch.setattr(runner, "_owner_check", forbidden)
    monkeypatch.setattr(program, "_case", forbidden)
    monkeypatch.setattr(program, "_finish", forbidden)
    monkeypatch.setattr(metrics, "score_query", forbidden)
    monkeypatch.setattr(metrics, "aggregate", forbidden)


def _install_witness(monkeypatch, ctx, owner, reader, counts, *, change=None,
                     change_on_association=None):
    # Counting wrappers that delegate the real functions at the intended
    # boundaries; catalog and raw directory wrappers record both the
    # actual start and the successful completion of the real call.
    # ``change_on_association`` is the exact one-based
    # owner-association index after which ``change`` publishes the
    # selected-record generation change.  No production hook is added.
    state = {"association": 0}
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
        counts["catalog"] += 1
        result = real_catalog(*args, **kwargs)
        counts["catalog_done"] += 1
        return result

    def counting_directory(*args, **kwargs):
        counts["directory"] += 1
        result = real_directory(*args, **kwargs)
        counts["directory_done"] += 1
        return result

    def counting_bundle(*args, **kwargs):
        counts["bundle"] += 1
        return real_bundle(*args, **kwargs)

    def counting_derived(*args, **kwargs):
        counts["derived"] += 1
        return real_derived(*args, **kwargs)

    def counting_original(*args, **kwargs):
        counts["original"] += 1
        return real_original(*args, **kwargs)

    def counting_pin_load(*args, **kwargs):
        counts["pin_load"] += 1
        return real_pin_load(*args, **kwargs)

    def counting_association(*args, **kwargs):
        state["association"] += 1
        result = real_association(*args, **kwargs)
        if (
            change is not None
            and change_on_association is not None
            and state["association"] == change_on_association
        ):
            change()
        return result

    def counting_read(*args, **kwargs):
        counts["read"] += 1
        return real_read(*args, **kwargs)

    monkeypatch.setattr(raw_snapshot_catalog, "load_catalog", counting_catalog)
    monkeypatch.setattr(raw_snapshot_directory, "load_directory", counting_directory)
    monkeypatch.setattr(ingestion_store, "load", counting_bundle)
    monkeypatch.setattr(ctx.derived, "load", counting_derived)
    monkeypatch.setattr(ctx.originals, "read_verified", counting_original)
    monkeypatch.setattr(owner, "_load", counting_pin_load)
    monkeypatch.setattr(owner, "_association", counting_association)
    monkeypatch.setattr(reader, "read_selection", counting_read)


def _identifiers(ctx):
    # The exact declared per-case identifiers from the real held core
    # embedding declaration.
    core = json.loads(
        (Path(ctx.root) / "snapshots" / ctx.snapshot_id[7:] / ".core.json").read_bytes()
    )
    e = core["embedding"]
    return (
        e["space_id"],
        e["definition_fingerprint"],
        e["query_policy_fingerprint"],
        e["query_execution_fingerprint"],
    )


def _plan_wire(ctx, admitted, catalog_id, judgments):
    return json.dumps(
        {
            "schema": 1,
            "plan_id": "plan",
            "dataset_id": admitted.dataset_id,
            "split_id": admitted.split_id,
            "snapshot_id": ctx.snapshot_id,
            "generation": ctx.pointer_generation,
            "catalog_id": catalog_id,
            "protocol_id": "protocol",
            "unknown_policy": "UNJUDGED_AS_ZERO_DIAGNOSTIC",
            "overlap_policy": "EXPLICIT_CHUNK_IDS_ONLY",
            "cutoffs": [20, 60],
            "judgments": [
                {
                    "case_id": case_id,
                    "gold": [[ident, grade] for ident, grade in gold],
                }
                for case_id, gold in judgments
            ],
        },
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _commence(admission, owner, plan_wire, dataset, case_ids, identifiers,
              bundle_ids, deadline_ms=30000):
    return program._commence_grade_catalog(
        admission,
        owner,
        plan_wire,
        dataset,
        runner.Cohort("held_out", case_ids),
        identifiers,
        bundle_ids,
        runner.Config("synthetic-cohort", "structural-only"),
        cohort_fixture.cohort_budget(),
        program.GradeBudget(*program._MAX_BUDGET),
        deadline_ms=deadline_ms,
    )


def _custody_intact(owner, original_end):
    assert owner.state == "ACTIVE"
    assert owner.op.end == original_end
    assert not owner.guard.locked()


def _install_principal_policy(tmp_base, name, principal, documents):
    payload = ranking_fixture._encode_policy([principal], documents)
    policy_root = Path(tmp_base) / name
    policy_root.mkdir(mode=0o700)
    os.chmod(str(policy_root), 0o700)
    receipt = payload_install.install_policy_payload(
        payload, directory=str(policy_root), deadline_ms=30000
    )
    assert receipt.outcome is payload_install.PayloadInstallOutcome.INSTALLED
    ranking_fixture._publish_selection(policy_root, 1, payload)
    return policy_root, payload


def _effective(grants, case):
    # The genuine shared-binder effective case scope, no restrictions.
    meter = stage_loss._Meter()
    _original, effective, _restricted = stage_loss._admit_authority(
        grants, None, case.scope, meter, lambda: None
    )
    return effective


def test_grade_catalog_stable_plan_empty_judgment_completes(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_fixture._scenario(tmp_path)
    )
    try:
        assert len(bundle_ids) == 3
        bundles, groups, members, triples = ranking_fixture._shapes(owner)
        per_bundle, per_derived, per_original = ranking_fixture._per_catalog(
            bundles, groups, members, triples
        )
        admitted = text_evaluation_dataset.admit(dataset)
        ctx.pointer_generation = owner.value.pointer.generation
        ident = _identifiers(ctx)
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        _forbid_slice_boundaries(monkeypatch)
        # Separate baseline measurement: one genuine completed actual
        # source PinOwner.check through real directory/original work,
        # kept apart from the measured slice.
        captured = owner.check(deadline_ms=30000)
        assert captured is owner.value
        assert counts["pin_load"] == 1
        assert (
            counts["bundle"],
            counts["derived"],
            counts["original"],
        ) == (members + 2 * triples, members + 6 * triples, members + 2 * triples)
        assert (
            counts["catalog"],
            counts["catalog_done"],
            counts["directory"],
            counts["directory_done"],
            counts["read"],
        ) == (0, 0, 1, 1, 0)
        _zero(counts)
        # The fresh current admission is established only after the
        # independent prior pin measurement; the measured counts start
        # after its initial selection observation.
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        _zero(counts)
        original_end = owner.op.end
        # Direct delegated witness of the one shared exact clock: the
        # real joint preparation, the shared direct dispatch and both
        # metadata associations under the guard run on the fresh
        # admission's clipped end in the normal valid 30000 ms case.
        from slaif_raggedized_helper import (
            private_evaluation_preflight as preflight,
        )
        observed = {
            "prepare_end": None,
            "dispatch_end": None,
            "held_ends": [],
        }
        real_prepare = preflight._prepare_declaration_body
        real_dispatch = program._direct_catalog

        def witness_prepare(*args, **kwargs):
            clock = kwargs["clock"] if "clock" in kwargs else args[-1]
            observed["prepare_end"] = clock.end
            return real_prepare(*args, **kwargs)

        def witness_dispatch(*args, **kwargs):
            clock = kwargs["clock"] if "clock" in kwargs else args[-1]
            observed["dispatch_end"] = clock.end
            return real_dispatch(*args, **kwargs)

        real_association = owner._association

        def witness_association(*args, **kwargs):
            observed["held_ends"].append(owner.op.end)
            return real_association(*args, **kwargs)

        monkeypatch.setattr(
            preflight, "_prepare_declaration_body", witness_prepare
        )
        monkeypatch.setattr(program, "_direct_catalog", witness_dispatch)
        monkeypatch.setattr(owner, "_association", witness_association)
        # The stable ordered multi-case plan includes the empty judgment;
        # the selected chunk order is the exact ascending value order.
        a, c, b = ctx.chunk_ids
        assert (chunks["a"], chunks["c"], chunks["b"]) == (a, c, b)
        wire = _plan_wire(
            ctx,
            admitted,
            ctx.catalog_id,
            (("h1", ((chunks["a"], 3),)), ("h4", ())),
        )
        catalog_id = _commence(
            admission, owner, wire, dataset, ("h1", "h4"), (ident, ident), bundle_ids
        )
        # The legacy catalog identity at the shared direct cut: one
        # completed catalog and two genuine selected observations, real
        # source counts, with no new pin reload and no producer, scoring
        # or report work from the private slice.
        assert catalog_id == ctx.catalog_id
        assert (counts["catalog"], counts["catalog_done"]) == (1, 1)
        # Both real directory validations completed inside the one
        # actual catalog.
        assert (counts["directory"], counts["directory_done"]) == (2, 2)
        assert (
            counts["bundle"],
            counts["derived"],
            counts["original"],
        ) == (per_bundle, per_derived, per_original)
        assert counts["pin_load"] == 0
        assert counts["read"] == 2
        # The one shared exact clock: the real joint preparation and the
        # shared direct dispatch ran under the fresh admission's clipped
        # end, and the actual saved owner operation end while held,
        # observed at both metadata associations under the guard,
        # equals it.
        assert observed["prepare_end"] == admission._end
        assert observed["dispatch_end"] == admission._end
        assert observed["held_ends"] == [admission._end, admission._end]
        # The empty judgment authorizes zero selected judgment reads and
        # does not erase the catalog: the broad trusted catalog
        # operation still reaches every retained bundle.
        assert admission._invalid is False
        assert owner.value is captured
        _custody_intact(owner, original_end)
    finally:
        if owner is not None:
            try:
                owner.close()
            except BaseException:
                pass
        for owned in (ctx.derived, ctx.originals):
            try:
                owned.close()
            except BaseException:
                pass


def test_early_pure_refusals_zero_new_reads(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_fixture._scenario(tmp_path)
    )
    ctx2 = owner2 = None
    try:
        bundles, groups, members, triples = ranking_fixture._shapes(owner)
        per_bundle, per_derived, per_original = ranking_fixture._per_catalog(
            bundles, groups, members, triples
        )
        admitted = text_evaluation_dataset.admit(dataset)
        ctx.pointer_generation = owner.value.pointer.generation
        ident = _identifiers(ctx)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        original_end = owner.op.end
        a, c, b = ctx.chunk_ids
        assert (chunks["a"], chunks["c"], chunks["b"]) == (a, c, b)

        def refused(case_ids, judgments, expected_intended):
            counts = _counts()
            _install_witness(monkeypatch, ctx, owner, reader, counts)
            _forbid_slice_boundaries(monkeypatch)
            wire = _plan_wire(ctx, admitted, ctx.catalog_id, judgments)
            with pytest.raises(program.EvaluationError) as error:
                _commence(
                    admission, owner, wire, dataset, case_ids,
                    (ident,) * len(case_ids), bundle_ids,
                )
            assert type(error.value) is program.EvaluationError
            assert error.value.args == ("evaluation program refused",)
            assert error.value.__context__ is None
            assert error.value.progress == program.FailurePrefix(
                "CATALOG", expected_intended, 0, 0, 0, expected_intended
            )
            _assert_zero(counts)
            assert admission._invalid is False
            _custody_intact(owner, original_end)
            monkeypatch.undo()
            return error.value.progress

        # (a) A later ordered judgment selects an unknown well-formed
        # chunk: the exact genuine held declarations show it is not in
        # the held row map, and the whole plan refuses before any new
        # catalog, directory or original.
        forged = "sha256:" + "ab" * 32
        held = raw_snapshot_rows.parse(owner.value.data.row_map.map_bytes)
        assert forged not in {row.chunk_id for row in held.rows}
        refused(
            ("h1", "h4"),
            (("h1", ((chunks["a"], 3),)), ("h4", ((forged, 1),))),
            2,
        )
        # (b) The real h4 case excludes b under the actual effective
        # intersection (corpus one only): the exact held scope of the
        # selected b chunk is unreadable, so the plan refuses before any
        # new read.
        rows = held.rows
        row_b = next(row for row in rows if row.chunk_id == chunks["b"])
        member_b = next(
            entry
            for entry in owner.value.data.membership.entries
            if entry.revision_id == row_b.revision_id
        )
        scope_b = p.admit_record("Scope", member_b.scope_bytes)
        case_h4 = next(item for item in admitted.cases if item.case_id == "h4")
        principal_grants = p.Grants(
            schema_version=1,
            corpora=ranking_fixture.CORPORA,
            versions=ranking_fixture.VERSIONS,
            labels=ranking_fixture.LABELS,
        )
        effective_h4 = _effective(principal_grants, case_h4)
        assert not p.reader_allows(scope_b, effective_h4)
        refused(
            ("h1", "h4"),
            (("h1", ((chunks["a"], 3),)), ("h4", ((chunks["b"], 1),))),
            2,
        )
        # (c) The independent withheld fixture: a genuinely unavailable
        # selected partition refuses before any new read even though the
        # chunk is readable under the effective h2 scope.
        second = tmp_path / "second"
        second.mkdir(mode=0o700)
        (ctx2, dataset2, bundle_ids2, owner2, policy_root2, reader2,
         chunks2) = ranking_fixture._scenario(second, withhold_two=True)
        admitted2 = text_evaluation_dataset.admit(dataset2)
        ctx2.pointer_generation = owner2.value.pointer.generation
        ident2 = _identifiers(ctx2)
        admission2 = ppr.request_current_view(
            reader2, CREDENTIAL, deadline_ms=30000)
        original_end2 = owner2.op.end
        unavailable = set(policy_eligibility.unavailable_partitions(
            pin_eligibility._isolated_policy_snapshot(admission2),
            owner2.value.data.membership))
        rows2 = raw_snapshot_rows.parse(
            owner2.value.data.row_map.map_bytes).rows
        row_b2 = next(row for row in rows2 if row.chunk_id == chunks2["b"])
        member_b2 = next(
            entry
            for entry in owner2.value.data.membership.entries
            if entry.revision_id == row_b2.revision_id
        )
        assert member_b2.partition_id in unavailable
        counts2 = _counts()
        _install_witness(monkeypatch, ctx2, owner2, reader2, counts2)
        _forbid_slice_boundaries(monkeypatch)
        # The full selection in the wire's mandatory ascending
        # chunk-ID order, derived from the actual fixture IDs.
        h2_gold = tuple(sorted(
            ((chunks2["a"], 1), (chunks2["c"], 1), (chunks2["b"], 1)),
            key=lambda pair: pair[0],
        ))
        wire2 = _plan_wire(
            ctx2, admitted2, ctx2.catalog_id,
            (("h1", ((chunks2["a"], 3),)), ("h2", h2_gold)),
        )
        with pytest.raises(program.EvaluationError) as error2:
            _commence(
                admission2, owner2, wire2, dataset2, ("h1", "h2"),
                (ident2, ident2), bundle_ids2,
            )
        assert error2.value.progress == program.FailurePrefix(
            "CATALOG", 2, 0, 0, 0, 2)
        _assert_zero(counts2)
        assert admission2._invalid is False
        _custody_intact(owner2, original_end2)
        monkeypatch.undo()
        # (c2) The mixed h2 scope: b is readable under the exact
        # effective h2 scope and its partition is genuinely withheld,
        # so the whole plan refuses before any new read even though
        # the judgment is empty and the other readable membership stays
        # available.
        counts2b = _counts()
        _install_witness(monkeypatch, ctx2, owner2, reader2, counts2b)
        _forbid_slice_boundaries(monkeypatch)
        wire2b = _plan_wire(ctx2, admitted2, ctx2.catalog_id, (("h2", ()),))
        with pytest.raises(program.EvaluationError) as error2b:
            _commence(
                admission2, owner2, wire2b, dataset2, ("h2",),
                (ident2,), bundle_ids2,
            )
        assert error2b.value.progress == program.FailurePrefix(
            "CATALOG", 1, 0, 0, 0, 1)
        _assert_zero(counts2b)
        assert admission2._invalid is False
        _custody_intact(owner2, original_end2)
        monkeypatch.undo()
        # (c3) The unaffected narrow scope proceeds: h4 reads only the
        # corpus-one membership, which holds no withheld partition, so
        # its empty judgment still completes the catalog at the shared
        # direct cut.
        bundles2, groups2, members2, triples2 = ranking_fixture._shapes(owner2)
        per_bundle2, per_derived2, per_original2 = ranking_fixture._per_catalog(
            bundles2, groups2, members2, triples2
        )
        counts2c = _counts()
        _install_witness(monkeypatch, ctx2, owner2, reader2, counts2c)
        _forbid_slice_boundaries(monkeypatch)
        wire2c = _plan_wire(ctx2, admitted2, ctx2.catalog_id, (("h4", ()),))
        catalog_id2 = _commence(
            admission2, owner2, wire2c, dataset2, ("h4",), (ident2,), bundle_ids2
        )
        assert catalog_id2 == ctx2.catalog_id
        assert (counts2c["catalog"], counts2c["catalog_done"]) == (1, 1)
        assert (counts2c["directory"], counts2c["directory_done"]) == (2, 2)
        assert (
            counts2c["bundle"],
            counts2c["derived"],
            counts2c["original"],
        ) == (per_bundle2, per_derived2, per_original2)
        assert counts2c["pin_load"] == 0
        assert counts2c["read"] == 2
        assert admission2._invalid is False
        _custody_intact(owner2, original_end2)
        monkeypatch.undo()
        # (d) The empty-judgment distinction: a usable case scope with an
        # empty judgment authorizes zero selected judgment reads and the
        # catalog still completes at the shared direct cut.
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        _forbid_slice_boundaries(monkeypatch)
        wire = _plan_wire(
            ctx, admitted, ctx.catalog_id, (("h4", ()),)
        )
        catalog_id = _commence(
            admission, owner, wire, dataset, ("h4",), (ident,), bundle_ids
        )
        assert catalog_id == ctx.catalog_id
        assert (counts["catalog"], counts["catalog_done"]) == (1, 1)
        assert (counts["directory"], counts["directory_done"]) == (2, 2)
        assert (
            counts["bundle"],
            counts["derived"],
            counts["original"],
        ) == (per_bundle, per_derived, per_original)
        assert counts["pin_load"] == 0
        assert counts["read"] == 2
        assert admission._invalid is False
        _custody_intact(owner, original_end)
        monkeypatch.undo()
        # (e) The same empty judgment over an unavailable effective
        # scope refuses before any new read: the narrow policy withholds
        # the corpus that is the only readable membership under the
        # narrowed principal grants, and that partition is genuinely
        # unavailable under this admission's own private snapshot.
        narrow_principal = (
            PRINCIPAL_ID, VERIFIER, OPERATIONS, ("two",),
            ranking_fixture.VERSIONS, ranking_fixture.LABELS)
        narrow_root, _payload = _install_principal_policy(
            tmp_path, "narrow", narrow_principal,
            ranking_fixture._documents_from_membership(
                owner2, withhold_two=True))
        narrow_reader = capture.PolicyCaptureReader(str(narrow_root))
        admission3 = ppr.request_current_view(
            narrow_reader, CREDENTIAL, deadline_ms=30000)
        # The exact unavailable set under this admission's own private
        # snapshot and the actual held membership, recomputed for the
        # narrow policy rather than the earlier withheld scenario.
        unavailable3 = set(policy_eligibility.unavailable_partitions(
            pin_eligibility._isolated_policy_snapshot(admission3),
            owner2.value.data.membership))
        case_h2 = next(item for item in admitted2.cases if item.case_id == "h2")
        effective_h2 = _effective(
            p.Grants(
                schema_version=1,
                corpora=("two",),
                versions=ranking_fixture.VERSIONS,
                labels=ranking_fixture.LABELS,
            ),
            case_h2,
        )
        readable_h2 = [
            entry for entry in owner2.value.data.membership.entries
            if p.reader_allows(
                p.admit_record("Scope", entry.scope_bytes), effective_h2)
        ]
        assert [entry.revision_id for entry in readable_h2] == [row_b2.revision_id]
        assert member_b2.partition_id in unavailable3
        counts3 = _counts()
        _install_witness(monkeypatch, ctx2, owner2, narrow_reader, counts3)
        _forbid_slice_boundaries(monkeypatch)
        wire3 = _plan_wire(ctx2, admitted2, ctx2.catalog_id, (("h2", ()),))
        with pytest.raises(program.EvaluationError) as error3:
            _commence(
                admission3, owner2, wire3, dataset2, ("h2",),
                (ident2,), bundle_ids2,
            )
        assert error3.value.progress == program.FailurePrefix(
            "CATALOG", 1, 0, 0, 0, 1)
        _assert_zero(counts3)
        assert admission3._invalid is False
        _custody_intact(owner2, original_end2)
        monkeypatch.undo()
        # (f) An effective scope with no usable membership at all
        # refuses the same fixed way.
        case_h1 = next(item for item in admitted2.cases if item.case_id == "h1")
        effective_h1 = _effective(
            p.Grants(
                schema_version=1,
                corpora=("two",),
                versions=ranking_fixture.VERSIONS,
                labels=ranking_fixture.LABELS,
            ),
            case_h1,
        )
        assert effective_h1.corpora == ()
        assert not any(
            p.reader_allows(
                p.admit_record("Scope", entry.scope_bytes), effective_h1)
            for entry in owner2.value.data.membership.entries
        )
        counts4 = _counts()
        _install_witness(monkeypatch, ctx2, owner2, narrow_reader, counts4)
        _forbid_slice_boundaries(monkeypatch)
        wire4 = _plan_wire(ctx2, admitted2, ctx2.catalog_id, (("h1", ()),))
        with pytest.raises(program.EvaluationError) as error4:
            _commence(
                admission3, owner2, wire4, dataset2, ("h1",),
                (ident2,), bundle_ids2,
            )
        assert error4.value.progress == program.FailurePrefix(
            "CATALOG", 1, 0, 0, 0, 1)
        _assert_zero(counts4)
        assert admission3._invalid is False
        _custody_intact(owner2, original_end2)
    finally:
        if owner2 is not None:
            _close_owned(ctx2, owner2)
        _close_owned(ctx, owner)


def test_selection_change_denies_catalog_and_post_catalog_observation(
    tmp_path, monkeypatch
):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_fixture._scenario(tmp_path)
    )
    try:
        bundles, groups, members, triples = ranking_fixture._shapes(owner)
        per_bundle, per_derived, per_original = ranking_fixture._per_catalog(
            bundles, groups, members, triples
        )
        admitted = text_evaluation_dataset.admit(dataset)
        ctx.pointer_generation = owner.value.pointer.generation
        ident = _identifiers(ctx)
        a, c, b = ctx.chunk_ids
        assert (chunks["a"], chunks["c"], chunks["b"]) == (a, c, b)
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        _forbid_slice_boundaries(monkeypatch)
        # Separately measure the earlier completed actual source
        # PinOwner.check through real directory/original work.
        captured = owner.check(deadline_ms=30000)
        assert captured is owner.value
        assert counts["pin_load"] == 1
        assert (
            counts["bundle"],
            counts["derived"],
            counts["original"],
        ) == (members + 2 * triples, members + 6 * triples, members + 2 * triples)
        assert (
            counts["catalog"],
            counts["catalog_done"],
            counts["directory"],
            counts["directory_done"],
            counts["read"],
        ) == (0, 0, 1, 1, 0)
        _zero(counts)
        # The fresh current admission is established only after the
        # independent prior pin measurement; the measured counts start
        # after its initial selection observation.
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        _zero(counts)
        monkeypatch.undo()
        # Advance the actual installed selection after the grade
        # association with the same raw pin and pointer: the synthetic
        # selected generation changes while the wire payload stays
        # identical.

        def change_to_generation(generation):
            ranking_fixture._publish_selection(
                policy_root, generation,
                ranking_fixture._encode_policy(
                    [ranking_fixture.PRINCIPAL],
                    ranking_fixture._documents_from_membership(owner)))

        original_end = owner.op.end
        # The entry's one exact end is the actual admitted current end:
        # the fresh admission's lifetime ends after the prior op end, so
        # the clipped end used under the guard is the admission end
        # itself, restored afterward.
        assert admission._end > original_end
        # The exact raw pin and bytes retained across the mutation.
        retained = owner.value
        retained_pointer_bytes = retained.pointer.pointer_bytes
        retained_core_sha256 = retained.pointer.core_sha256
        retained_map_bytes = retained.data.row_map.map_bytes
        retained_membership_bytes = retained.data.membership.membership_bytes
        wire = _plan_wire(
            ctx, admitted, ctx.catalog_id, (("h1", ((chunks["a"], 3),)),)
        )
        _install_witness(
            monkeypatch, ctx, owner, reader, counts,
            change=lambda: change_to_generation(2),
            change_on_association=1,
        )
        _forbid_slice_boundaries(monkeypatch)
        with pytest.raises(program.EvaluationError) as error:
            _commence(
                admission, owner, wire, dataset, ("h1",), (ident,), bundle_ids
            )
        # The genuine selected denial at the last gate before the
        # actual direct owned catalog: zero new chosen catalog starts,
        # no usable result, CATALOG failure progress and restored
        # guard/end.
        assert error.value.progress == program.FailurePrefix(
            "CATALOG", 1, 0, 0, 0, 1)
        assert (
            counts["catalog"],
            counts["catalog_done"],
            counts["directory"],
            counts["directory_done"],
            counts["bundle"],
            counts["derived"],
            counts["original"],
        ) == (0, 0, 0, 0, 0, 0, 0)
        assert counts["pin_load"] == 0
        assert counts["read"] == 1
        # The exact same raw pin and bytes across the generation
        # mutation: only the selected record changed.
        assert owner.value is retained
        assert (
            owner.value.pointer.pointer_bytes,
            owner.value.pointer.core_sha256,
            owner.value.data.row_map.map_bytes,
            owner.value.data.membership.membership_bytes,
        ) == (
            retained_pointer_bytes,
            retained_core_sha256,
            retained_map_bytes,
            retained_membership_bytes,
        )
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 1
        _custody_intact(owner, original_end)
        monkeypatch.undo()
        # A fresh equivalent admission under the advanced selection: one
        # genuine completed catalog, then the post-catalog genuine
        # denial under the same ownership and counts.
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert fresh.selection.generation == 2
        _zero(counts)
        _install_witness(
            monkeypatch, ctx, owner, reader, counts,
            change=lambda: change_to_generation(3),
            change_on_association=2,
        )
        _forbid_slice_boundaries(monkeypatch)
        with pytest.raises(program.EvaluationError) as error2:
            _commence(
                fresh, owner, wire, dataset, ("h1",), (ident,), bundle_ids
            )
        assert error2.value.progress == program.FailurePrefix(
            "CATALOG", 1, 0, 0, 0, 1)
        # One genuine completed catalog with its two real directory
        # validations, then the post-catalog genuine denial.
        assert (counts["catalog"], counts["catalog_done"]) == (1, 1)
        assert (counts["directory"], counts["directory_done"]) == (2, 2)
        assert (
            counts["bundle"],
            counts["derived"],
            counts["original"],
        ) == (per_bundle, per_derived, per_original)
        assert counts["pin_load"] == 0
        # One pre-catalog observation and the post-catalog denial.
        assert counts["read"] == 2
        # The exact same raw pin and bytes across this mutation too.
        assert owner.value is retained
        assert (
            owner.value.pointer.pointer_bytes,
            owner.value.pointer.core_sha256,
            owner.value.data.row_map.map_bytes,
            owner.value.data.membership.membership_bytes,
        ) == (
            retained_pointer_bytes,
            retained_core_sha256,
            retained_map_bytes,
            retained_membership_bytes,
        )
        assert fresh._invalid is True
        assert fresh.recheck(deadline_ms=1000) is False
        assert counts["read"] == 2
        assert owner.value is captured
        _custody_intact(owner, original_end)
    finally:
        _close_owned(ctx, owner)


def _close_owned(ctx, owner):
    for owned in (owner, ctx.derived, ctx.originals):
        owned.close()


def _assert_zero(counts):
    assert counts == _counts()
