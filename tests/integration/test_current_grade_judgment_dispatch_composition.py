"""Owned private grade-owned judgment dispatch composition proof.

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
fixture in ``tests/unit/test_private_policy_request.py`` through the
009-ai ranking-dispatch test) publishes the selected record for the
actual capture/decoder/request methods - it provides no writer
qualification, and the actual selected changes use the same-wire
generation change through that attributed fixture.  Each fresh current
admission is created only after the expensive fixture setup that
precedes its dispatch.  Counting wrappers attribute the real catalog,
directory, bundle, derived, original-store verified read, owner-load,
owner-association and reader calls at the intended boundaries; counts
run from the private commencement after fixture acquisition, and the
baseline pin measurement is kept separate from the slice.  The per-catalog
and per-pin count formulas are derived from the exact source: each catalog
load performs two load_directory trees, each revalidating the whole
declared membership (one ingestion load per entry) and rebuilding every
dense and lexical partition once per distinct (partition, bundle, batch)
triple through one real load_group, plus one ingestion load per unique
row-map bundle and one per unique (bundle, batch) group, each through one
real load_group; every load_group performs one ingestion load plus two
additional derived loads, and every ingestion load performs one derived
load and one verified original read; each full pin directory validation
performs one load_directory tree with the same membership and partition
rebuild.  The test-local delegate wrappers publish the attributed
same-wire generation change only after an actual completed
revalidate_current_pin_case or bind_pinned return, record the exact
owner operation end at each inter-delegate boundary, and anchor the
pin -> bind -> pin sequence by the retained PinData identity, with the
raw held value and the independent actual read counter untouched.
The directory attribution measures the two independent pin directory
validations separately from the total physical directory work: two
actual catalog dispatches at two directory loads apiece complete six
directory starts on a successful span, five remain after the successful
rank before the second pin, and denials before ranking still have one.
No local native execution: only the configured hosted CI executes the
real fixture.
"""
import pytest  # noqa: E402

from slaif_raggedized_helper import evaluation_program as program  # noqa: E402
from slaif_raggedized_helper import private_evaluation_preflight as preflight  # noqa: E402
from slaif_raggedized_helper import private_policy_capture as capture  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import provenance_records as p  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_directory  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_rows  # noqa: E402
from slaif_raggedized_helper import source_bound_ranking as ranking  # noqa: E402
from slaif_raggedized_helper import source_cohort_runner as runner  # noqa: E402
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility  # noqa: E402
from slaif_raggedized_helper import text_evaluation_dataset  # noqa: E402
import test_current_grade_catalog_composition as grade_fixture  # noqa: E402
import test_current_ranking_dispatch_composition as ranking_fixture  # noqa: E402
import test_source_cohort_runner_composition as cohort_fixture  # noqa: E402

CREDENTIAL = ranking_fixture.CREDENTIAL
PRINCIPAL_ID = ranking_fixture.PRINCIPAL_ID
VERIFIER = ranking_fixture.VERIFIER
OPERATIONS = ranking_fixture.OPERATIONS
CORPORA = ranking_fixture.CORPORA
VERSIONS = ranking_fixture.VERSIONS
LABELS = ranking_fixture.LABELS
PRINCIPAL = ranking_fixture.PRINCIPAL


def _dispatch(admission, owner, plan_wire, dataset, case_ids, identifiers,
              bundle_ids, case_id):
    return program._commence_grade_judgment_dispatch(
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
        case_id,
    )


def _principal_grants():
    return p.Grants(
        schema_version=1,
        corpora=CORPORA,
        versions=VERSIONS,
        labels=LABELS,
    )


def _pin_source_counts(members, triples):
    # Exact source-derived full pin directory validation counts:
    # (bundle, derived, original) for one real load_directory tree.
    return (
        members + 2 * triples,
        members + 6 * triples,
        members + 2 * triples,
    )


def _install_delegate_witness(monkeypatch, policy_root, owner, start_generation,
                              change_after, boundaries):
    # Test-local wrappers over the actual delegated calls: the
    # attributed same-wire generation change publishes only after the
    # exact one-based completed delegate call (an actual
    # revalidate_current_pin_case or bind_pinned return); the raw held
    # value is never touched, the independent actual read counter stays
    # with the store witness, and each completed delegate records the
    # owner operation end at the inter-delegate boundary and the
    # returned PinData identity anchoring the sequence.  No production
    # hook is added.
    state = {"n": 0, "generation": start_generation, "sequence": []}

    def change():
        state["generation"] += 1
        ranking_fixture._publish_selection(
            policy_root,
            state["generation"],
            ranking_fixture._encode_policy(
                [PRINCIPAL], ranking_fixture._documents_from_membership(owner)),
        )

    real_revalidate = pin_eligibility.revalidate_current_pin_case
    real_bind = ranking.bind_pinned

    def completed(call_kind, result):
        boundaries.append(owner.op.end)
        state["sequence"].append(
            (call_kind, id(result) if call_kind == "pin" else None))
        state["n"] += 1
        if change_after is not None and state["n"] == change_after:
            change()
        return result

    def counting_revalidate(*args, **kwargs):
        return completed("pin", real_revalidate(*args, **kwargs))

    def counting_bind(*args, **kwargs):
        return completed("bind", real_bind(*args, **kwargs))

    monkeypatch.setattr(pin_eligibility, "revalidate_current_pin_case",
                        counting_revalidate)
    monkeypatch.setattr(ranking, "bind_pinned", counting_bind)
    return state


def test_judgment_dispatch_stable_nonempty_and_empty_judgments(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_fixture._scenario(tmp_path)
    )
    try:
        assert len(bundle_ids) == 3
        bundles, groups, members, triples = ranking_fixture._shapes(owner)
        per_bundle, per_derived, per_original = ranking_fixture._per_catalog(
            bundles, groups, members, triples
        )
        pin_bundle, pin_derived, pin_original = _pin_source_counts(members, triples)
        admitted = text_evaluation_dataset.admit(dataset)
        ctx.pointer_generation = owner.value.pointer.generation
        ident = grade_fixture._identifiers(ctx)
        a, c, b = ctx.chunk_ids
        assert (chunks["a"], chunks["c"], chunks["b"]) == (a, c, b)
        # The stable ordered multi-case plan includes the unaffected
        # empty judgment; the fresh current admission is established
        # only after the expensive fixture setup.
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        original_end = owner.op.end
        retained = owner.value
        counts = grade_fixture._counts()
        grade_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
        grade_fixture._forbid_slice_boundaries(monkeypatch)
        # Direct delegated witness of the one shared exact clock: the
        # real joint preparation and the shared grading-owned dispatch
        # under the fresh admission's clipped end, the actual saved
        # owner operation end observed at every real association,
        # directory and loader end, and the inter-delegate boundaries
        # plus retained PinData identity through the delegate wrappers.
        observed = {
            "prepare_end": None,
            "dispatch_end": None,
            "held_ends": [],
            "directory_ends": [],
            "pin_ends": [],
        }
        real_prepare = preflight._prepare_declaration_body
        real_dispatch = program._grade_judgment_dispatch

        def witness_prepare(*args, **kwargs):
            clock = kwargs["clock"] if "clock" in kwargs else args[-1]
            observed["prepare_end"] = clock.end
            return real_prepare(*args, **kwargs)

        def witness_dispatch(*args, **kwargs):
            clock = kwargs["clock"] if "clock" in kwargs else args[2]
            observed["dispatch_end"] = clock.end
            return real_dispatch(*args, **kwargs)

        real_association = owner._association

        def witness_association(*args, **kwargs):
            observed["held_ends"].append(owner.op.end)
            return real_association(*args, **kwargs)

        real_directory = raw_snapshot_directory.load_directory

        def witness_directory(*args, **kwargs):
            observed["directory_ends"].append(owner.op.end)
            return real_directory(*args, **kwargs)

        real_pin_load = owner._load

        def witness_pin_load(*args, **kwargs):
            observed["pin_ends"].append(owner.op.end)
            return real_pin_load(*args, **kwargs)

        monkeypatch.setattr(
            preflight, "_prepare_declaration_body", witness_prepare
        )
        monkeypatch.setattr(program, "_grade_judgment_dispatch", witness_dispatch)
        monkeypatch.setattr(owner, "_association", witness_association)
        monkeypatch.setattr(raw_snapshot_directory, "load_directory",
                            witness_directory)
        monkeypatch.setattr(owner, "_load", witness_pin_load)
        boundaries = []
        delegate = _install_delegate_witness(
            monkeypatch, policy_root, owner, start_generation=1,
            change_after=None, boundaries=boundaries)
        wire = grade_fixture._plan_wire(
            ctx,
            admitted,
            ctx.catalog_id,
            (("h1", ((chunks["a"], 3),)), ("h4", ())),
        )
        # The stable one actual nonempty judgment: two real pin
        # directories, two actual ranking catalogs and the genuine
        # selected observations attributed to the actual owner calls.
        bound = _dispatch(
            admission, owner, wire, dataset, ("h1", "h4"), (ident, ident),
            bundle_ids, "h1",
        )
        # Two independent pin directory validations, measured
        # separately from the total physical directory work: the two
        # actual catalog dispatches at two directory loads apiece
        # complete six actual directory starts and completions.
        assert counts["pin_load"] == 2
        assert (counts["directory"], counts["directory_done"]) == (6, 6)
        assert (counts["catalog"], counts["catalog_done"]) == (2, 2)
        assert (
            counts["bundle"],
            counts["derived"],
            counts["original"],
        ) == (
            2 * pin_bundle + 2 * per_bundle + 2,
            2 * pin_derived + 2 * per_derived + 2,
            2 * pin_original + 2 * per_original + 2,
        )
        # Two genuine selected observations per pin revalidation, one
        # before each catalog dispatch and each selected bundle load in
        # both ranking passes, and the final same-admission observation.
        assert counts["read"] == 9
        # The one shared exact clock: the original admission end at the
        # joint preparation, the shared dispatch and every real
        # association, directory and loader end.
        assert observed["prepare_end"] == admission._end
        assert observed["dispatch_end"] == admission._end
        # The exact real association count: one preparation-span
        # association, two per delegated pin revalidation (the guarded
        # association and the held revalidation body's post-load
        # association), one for the delegated pinned rank binding and
        # one final-span association.
        assert len(observed["held_ends"]) == 1 + 2 + 2 + 1 + 1
        assert all(value == admission._end for value in observed["held_ends"])
        # Two independent pin directory validations and two actual
        # catalog dispatches at two directory loads apiece.
        assert len(observed["directory_ends"]) == 2 + 2 * 2
        assert all(value == admission._end
                   for value in observed["directory_ends"])
        assert len(observed["pin_ends"]) == 2
        assert all(value == admission._end for value in observed["pin_ends"])
        # The internal bounded verified judgment binding with its
        # existing source, authorization and qualification categories.
        assert bound.source_binding_status == "ORIGINALS_REVALIDATED_AT_BIND_TIME"
        assert bound.input_origin == "SUPPLIED_RANKING_UNVERIFIED"
        assert bound.authorization_status == "SUPPLIED_SCOPE_CHECKS_ONLY"
        assert bound.execution_status == "NOT_ATTESTED"
        assert bound.qualification == "NOT_QUALIFIED"
        assert bound.snapshot_id == ctx.snapshot_id
        assert bound.catalog_id == ctx.catalog_id
        assert bound.row_count == 1
        assert [row.chunk_id for row in bound.rows] == [chunks["a"]]
        assert bound.fragment_count == len(bound.rows[0].fragments)
        # The same validated held pin through the whole delegated span,
        # the exact prior end restored at every inter-delegate boundary
        # as well as at the end, and the same retained PinData returned
        # by both guarded pins anchoring the pin -> bind -> pin
        # sequence.
        assert owner.value is retained
        assert boundaries == [original_end, original_end, original_end]
        assert delegate["sequence"] == [
            ("pin", id(retained)),
            ("bind", None),
            ("pin", id(retained)),
        ]
        assert admission._invalid is False
        grade_fixture._custody_intact(owner, original_end)
        # The actual legacy binding equality and shape: the same
        # admitted case scope through the public legacy entry yields
        # the same canonical bound result, counted separately.
        monkeypatch.undo()
        legacy_counts = grade_fixture._counts()
        grade_fixture._install_witness(monkeypatch, ctx, owner, reader, legacy_counts)
        case_h1 = next(item for item in admitted.cases if item.case_id == "h1")
        effective_h1 = grade_fixture._effective(_principal_grants(), case_h1)
        legacy = ranking.bind(
            ctx.originals,
            ctx.derived,
            ctx.root,
            ctx.snapshot_id,
            ctx.catalog_id,
            (chunks["a"],),
            grants=effective_h1,
            restrictions=None,
            deadline_ms=30000,
        )
        assert (legacy_counts["catalog"], legacy_counts["catalog_done"]) == (2, 2)
        assert legacy_counts["pin_load"] == 0
        assert bound == legacy
        assert bound.binding_id == legacy.binding_id
        assert bound.authority_sha256 == legacy.authority_sha256
        assert bound.rows == legacy.rows
        monkeypatch.undo()
        # The unaffected empty judgment in its own distinct phase under
        # a fresh admission: zero selected judgment reads and no
        # selected bundle dispatch, while the two real pin directories
        # and the two actual ranking catalogs still complete.
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        original_end2 = owner.op.end
        counts2 = grade_fixture._counts()
        grade_fixture._install_witness(monkeypatch, ctx, owner, reader, counts2)
        grade_fixture._forbid_slice_boundaries(monkeypatch)
        observed2 = {
            "prepare_end": None,
            "dispatch_end": None,
            "held_ends": [],
            "directory_ends": [],
            "pin_ends": [],
        }
        real_prepare2 = preflight._prepare_declaration_body
        real_dispatch2 = program._grade_judgment_dispatch

        def witness_prepare2(*args, **kwargs):
            clock = kwargs["clock"] if "clock" in kwargs else args[-1]
            observed2["prepare_end"] = clock.end
            return real_prepare2(*args, **kwargs)

        def witness_dispatch2(*args, **kwargs):
            clock = kwargs["clock"] if "clock" in kwargs else args[2]
            observed2["dispatch_end"] = clock.end
            return real_dispatch2(*args, **kwargs)

        real_association2 = owner._association

        def witness_association2(*args, **kwargs):
            observed2["held_ends"].append(owner.op.end)
            return real_association2(*args, **kwargs)

        real_directory2 = raw_snapshot_directory.load_directory

        def witness_directory2(*args, **kwargs):
            observed2["directory_ends"].append(owner.op.end)
            return real_directory2(*args, **kwargs)

        real_pin_load2 = owner._load

        def witness_pin_load2(*args, **kwargs):
            observed2["pin_ends"].append(owner.op.end)
            return real_pin_load2(*args, **kwargs)

        monkeypatch.setattr(preflight, "_prepare_declaration_body",
                            witness_prepare2)
        monkeypatch.setattr(program, "_grade_judgment_dispatch",
                            witness_dispatch2)
        monkeypatch.setattr(owner, "_association", witness_association2)
        monkeypatch.setattr(raw_snapshot_directory, "load_directory",
                            witness_directory2)
        monkeypatch.setattr(owner, "_load", witness_pin_load2)
        boundaries2 = []
        delegate2 = _install_delegate_witness(
            monkeypatch, policy_root, owner, start_generation=1,
            change_after=None, boundaries=boundaries2)
        bound2 = _dispatch(
            fresh, owner, wire, dataset, ("h1", "h4"), (ident, ident),
            bundle_ids, "h4",
        )
        # The unaffected empty judgment still reaches two real pin
        # directories and two actual catalog dispatches at two
        # directory loads apiece = six total directory starts, with
        # the independent pin count measured separately.
        assert counts2["pin_load"] == 2
        assert (counts2["directory"], counts2["directory_done"]) == (6, 6)
        assert (counts2["catalog"], counts2["catalog_done"]) == (2, 2)
        assert (
            counts2["bundle"],
            counts2["derived"],
            counts2["original"],
        ) == (
            2 * pin_bundle + 2 * per_bundle,
            2 * pin_derived + 2 * per_derived,
            2 * pin_original + 2 * per_original,
        )
        # Two genuine selected observations per pin revalidation and
        # one before each actual catalog dispatch; no selected bundle
        # load.
        assert counts2["read"] == 7
        # The one shared exact clock under the fresh admission: the
        # original admission end at the joint preparation, the shared
        # dispatch and every real association, directory and loader
        # end, with the exact real association count.
        assert observed2["prepare_end"] == fresh._end
        assert observed2["dispatch_end"] == fresh._end
        assert len(observed2["held_ends"]) == 1 + 2 + 2 + 1 + 1
        assert all(value == fresh._end for value in observed2["held_ends"])
        assert len(observed2["directory_ends"]) == 2 + 2 * 2
        assert all(value == fresh._end for value in observed2["directory_ends"])
        assert len(observed2["pin_ends"]) == 2
        assert all(value == fresh._end for value in observed2["pin_ends"])
        assert bound2.source_binding_status == "NO_SELECTED_SOURCE_VALIDATED"
        assert bound2.row_count == 0
        assert bound2.rows == ()
        assert bound2.fragment_count == 0
        assert bound2.snapshot_id == ctx.snapshot_id
        assert bound2.catalog_id == ctx.catalog_id
        assert boundaries2 == [original_end2, original_end2, original_end2]
        assert delegate2["sequence"] == [
            ("pin", id(retained)),
            ("bind", None),
            ("pin", id(retained)),
        ]
        assert fresh._invalid is False
        grade_fixture._custody_intact(owner, original_end2)
        monkeypatch.undo()
    finally:
        ranking_fixture._close_owned(ctx, owner)


def test_judgment_dispatch_pure_refusals_zero_new_reads(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_fixture._scenario(tmp_path)
    )
    ctx2 = owner2 = None
    try:
        admitted = text_evaluation_dataset.admit(dataset)
        ctx.pointer_generation = owner.value.pointer.generation
        ident = grade_fixture._identifiers(ctx)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        original_end = owner.op.end
        a, c, b = ctx.chunk_ids
        assert (chunks["a"], chunks["c"], chunks["b"]) == (a, c, b)

        def refused(case_ids, judgments, case_id, expected):
            counts = grade_fixture._counts()
            grade_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
            grade_fixture._forbid_slice_boundaries(monkeypatch)
            plan = grade_fixture._plan_wire(ctx, admitted, ctx.catalog_id, judgments)
            with pytest.raises(program.EvaluationError) as error:
                _dispatch(
                    admission, owner, plan, dataset, case_ids,
                    (ident,) * len(case_ids), bundle_ids, case_id,
                )
            assert type(error.value) is program.EvaluationError
            assert error.value.args == ("evaluation program refused",)
            assert error.value.__context__ is None
            assert error.value.progress == expected
            grade_fixture._assert_zero(counts)
            assert admission._invalid is False
            grade_fixture._custody_intact(owner, original_end)
            monkeypatch.undo()
            return error.value.progress

        # The actual PREFLIGHT phase for a pure refusal once admitted:
        # the intended count with no attempted delegated work.
        plan_level = program.FailurePrefix("PREFLIGHT", 1, 0, 0, 0, 1)
        # (a) A later ordered judgment selects an unknown well-formed
        # chunk: the exact genuine held declarations show it is not in
        # the held row map, and the whole plan refuses before any new
        # full directory, catalog or bundle work and zero genuine
        # selected reads.
        forged = "sha256:" + "ab" * 32
        held = raw_snapshot_rows.parse(owner.value.data.row_map.map_bytes)
        assert forged not in {row.chunk_id for row in held.rows}
        refused(
            ("h1", "h4"),
            (("h1", ((chunks["a"], 3),)), ("h4", ((forged, 1),))),
            "h1",
            plan_level,
        )
        # (b) The real h4 case excludes b under the actual effective
        # intersection (corpus one only): the exact held scope of the
        # selected b chunk is unreadable, so the plan refuses before
        # any new read.
        rows = held.rows
        row_b = next(row for row in rows if row.chunk_id == chunks["b"])
        member_b = next(
            entry
            for entry in owner.value.data.membership.entries
            if entry.revision_id == row_b.revision_id
        )
        scope_b = p.admit_record("Scope", member_b.scope_bytes)
        case_h4 = next(item for item in admitted.cases if item.case_id == "h4")
        effective_h4 = grade_fixture._effective(_principal_grants(), case_h4)
        assert not p.reader_allows(scope_b, effective_h4)
        refused(
            ("h1", "h4"),
            (("h1", ((chunks["a"], 3),)), ("h4", ((chunks["b"], 1),))),
            "h1",
            plan_level,
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
        ident2 = grade_fixture._identifiers(ctx2)
        admission2 = ppr.request_current_view(reader2, CREDENTIAL, deadline_ms=30000)
        original_end2 = owner2.op.end
        unavailable = set(policy_eligibility.unavailable_partitions(
            pin_eligibility._isolated_policy_snapshot(admission2),
            owner2.value.data.membership))
        rows2 = raw_snapshot_rows.parse(
            owner2.value.data.row_map.map_bytes).rows
        row_b2 = next(row for row in rows2 if row.chunk_id == chunks2["b"])
        member_b2 = next(
            entry for entry in owner2.value.data.membership.entries
            if entry.revision_id == row_b2.revision_id
        )
        assert member_b2.partition_id in unavailable
        case_h2 = next(item for item in admitted2.cases if item.case_id == "h2")
        effective_h2 = grade_fixture._effective(_principal_grants(), case_h2)
        scope_b2 = p.admit_record("Scope", member_b2.scope_bytes)
        assert p.reader_allows(scope_b2, effective_h2)

        def refused2(judgments, case_ids, case_id):
            counts2 = grade_fixture._counts()
            grade_fixture._install_witness(monkeypatch, ctx2, owner2, reader2, counts2)
            grade_fixture._forbid_slice_boundaries(monkeypatch)
            plan2 = grade_fixture._plan_wire(ctx2, admitted2, ctx2.catalog_id, judgments)
            with pytest.raises(program.EvaluationError) as error2:
                _dispatch(
                    admission2, owner2, plan2, dataset2, case_ids,
                    (ident2,) * len(case_ids), bundle_ids2, case_id,
                )
            assert error2.value.__context__ is None
            assert error2.value.progress == plan_level
            grade_fixture._assert_zero(counts2)
            assert admission2._invalid is False
            grade_fixture._custody_intact(owner2, original_end2)
            monkeypatch.undo()

        refused2(
            (("h1", ((chunks2["a"], 3),)), ("h2", ((chunks2["b"], 1),))),
            ("h1", "h2"),
            "h2",
        )
        # (d) The mixed narrow scope: b is readable under the exact
        # effective h2 scope and its partition is genuinely withheld,
        # so the whole plan refuses before any new read even though the
        # other readable membership stays available.
        refused2(
            (("h2", ((chunks2["b"], 1),)),),
            ("h2",),
            "h2",
        )
        # (e) An effective scope with no usable membership at all
        # refuses the same fixed way: the narrow policy withholds the
        # corpus that is the only readable membership under the
        # narrowed principal grants.
        narrow_principal = (
            PRINCIPAL_ID, VERIFIER, OPERATIONS, ("two",),
            ranking_fixture.VERSIONS, ranking_fixture.LABELS)
        narrow_root, _payload = grade_fixture._install_principal_policy(
            tmp_path, "narrow", narrow_principal,
            ranking_fixture._documents_from_membership(
                owner2, withhold_two=True))
        narrow_reader = capture.PolicyCaptureReader(str(narrow_root))
        admission3 = ppr.request_current_view(
            narrow_reader, CREDENTIAL, deadline_ms=30000)
        case_h1_2 = next(item for item in admitted2.cases if item.case_id == "h1")
        effective_h1_2 = grade_fixture._effective(
            p.Grants(
                schema_version=1,
                corpora=("two",),
                versions=ranking_fixture.VERSIONS,
                labels=ranking_fixture.LABELS,
            ),
            case_h1_2,
        )
        assert effective_h1_2.corpora == ()
        assert not any(
            p.reader_allows(
                p.admit_record("Scope", entry.scope_bytes), effective_h1_2)
            for entry in owner2.value.data.membership.entries
        )
        counts3 = grade_fixture._counts()
        grade_fixture._install_witness(monkeypatch, ctx2, owner2, narrow_reader, counts3)
        grade_fixture._forbid_slice_boundaries(monkeypatch)
        plan3 = grade_fixture._plan_wire(
            ctx2, admitted2, ctx2.catalog_id, (("h1", ((chunks2["a"], 3),)),))
        with pytest.raises(program.EvaluationError) as error3:
            _dispatch(
                admission3, owner2, plan3, dataset2, ("h1",),
                (ident2,), bundle_ids2, "h1",
            )
        assert error3.value.progress == plan_level
        grade_fixture._assert_zero(counts3)
        assert admission3._invalid is False
        grade_fixture._custody_intact(owner2, original_end2)
        monkeypatch.undo()
        # (f) An unknown well-formed case ID refuses before any new
        # read even though the plan itself is fully usable.
        refused(
            ("h1", "h4"),
            (("h1", ((chunks["a"], 3),)), ("h4", ())),
            "h9",
            plan_level,
        )
        # (g) A declared plan judgment with no ordered prepared
        # selection at the same position is a malformed plan for this
        # operation and refuses before any new read.
        refused(
            ("h1",),
            (("h1", ((chunks["a"], 3),)), ("h2", ((chunks["a"], 1),))),
            "h1",
            plan_level,
        )
    finally:
        if owner2 is not None:
            ranking_fixture._close_owned(ctx2, owner2)
        ranking_fixture._close_owned(ctx, owner)


def test_judgment_dispatch_same_pin_generation_changes(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, chunks) = (
        ranking_fixture._scenario(tmp_path)
    )
    try:
        bundles, groups, members, triples = ranking_fixture._shapes(owner)
        per_bundle, per_derived, per_original = ranking_fixture._per_catalog(
            bundles, groups, members, triples
        )
        pin_bundle, pin_derived, pin_original = _pin_source_counts(members, triples)
        admitted = text_evaluation_dataset.admit(dataset)
        ctx.pointer_generation = owner.value.pointer.generation
        ident = grade_fixture._identifiers(ctx)
        a, c, b = ctx.chunk_ids
        assert (chunks["a"], chunks["c"], chunks["b"]) == (a, c, b)
        wire = grade_fixture._plan_wire(
            ctx, admitted, ctx.catalog_id, (("h1", ((chunks["a"], 3),)),)
        )
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        original_end = owner.op.end
        # The exact raw pin and bytes retained across the mutation.
        retained = owner.value
        retained_pointer_bytes = retained.pointer.pointer_bytes
        retained_core_sha256 = retained.pointer.core_sha256
        retained_map_bytes = retained.data.row_map.map_bytes
        retained_membership_bytes = retained.data.membership.membership_bytes
        # (a) The actual same-pin generation change after the completed
        # actual first grade pin, before the first true ranking source
        # start: the delegated pinned rank binding's first selected
        # observation denies entrance to the first catalog, with zero
        # subsequent load and no usable judgment result.
        counts = grade_fixture._counts()
        grade_fixture._install_witness(monkeypatch, ctx, owner, reader, counts)
        grade_fixture._forbid_slice_boundaries(monkeypatch)
        boundaries = []
        state = _install_delegate_witness(
            monkeypatch, policy_root, owner, start_generation=1,
            change_after=1, boundaries=boundaries)
        with pytest.raises(program.EvaluationError) as error:
            _dispatch(
                admission, owner, wire, dataset, ("h1",), (ident,), bundle_ids,
                "h1",
            )
        assert type(error.value) is program.EvaluationError
        assert error.value.args == ("evaluation program refused",)
        assert error.value.__context__ is None
        # The real source phase at the delegated rank binding, the one
        # attempted case and no completed grade case.
        assert error.value.progress == program.FailurePrefix(
            "GRADE_BIND", 1, 1, 0, 1, 0
        )
        # One completed actual first grade pin directory, measured
        # separately from the total physical directory work: the
        # denials before ranking still have one directory start, with
        # the exact later ranking source starts refused at zero
        # catalog, bundle and selected work.
        assert counts["pin_load"] == 1
        assert (counts["directory"], counts["directory_done"]) == (1, 1)
        assert (counts["catalog"], counts["catalog_done"]) == (0, 0)
        assert (
            counts["bundle"],
            counts["derived"],
            counts["original"],
        ) == (pin_bundle, pin_derived, pin_original)
        # Two genuine observations of the first pin and the denying
        # third at the first true ranking source start.
        assert counts["read"] == 3
        # Only the completed first delegate is counted; the same
        # retained PinData it returned anchors the sequence and the
        # inter-delegate boundary restored the exact prior end.
        assert state["n"] == 1
        assert state["sequence"] == [("pin", id(retained))]
        assert boundaries == [original_end]
        # The admission latches with zero further reader calls.
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 3
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
        grade_fixture._custody_intact(owner, original_end)
        monkeypatch.undo()
        # (b) A fresh equivalent admission under the advanced
        # selection: the real grade bind completes with its two actual
        # ranking catalogs, then the actual same-pin generation change
        # before the second physical pin denies the delegated revalidation
        # at its first selected observation, distinguishing prior
        # completed work from the exact later pin start refused.
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert fresh.selection.generation == 2
        counts2 = grade_fixture._counts()
        grade_fixture._install_witness(monkeypatch, ctx, owner, reader, counts2)
        grade_fixture._forbid_slice_boundaries(monkeypatch)
        # The change publishes only after the completed real grade bind
        # return, before the second physical pin's first observation.
        boundaries2 = []
        state2 = _install_delegate_witness(
            monkeypatch, policy_root, owner, start_generation=2,
            change_after=2, boundaries=boundaries2)
        with pytest.raises(program.EvaluationError) as error2:
            _dispatch(
                fresh, owner, wire, dataset, ("h1",), (ident,), bundle_ids,
                "h1",
            )
        assert error2.value.__context__ is None
        # The real source phase at the second delegated pin
        # revalidation.
        assert error2.value.progress == program.FailurePrefix(
            "GRADE_PIN", 1, 1, 0, 1, 0
        )
        # Prior completed work: the first real pin directory and the
        # real grade bind with its two actual ranking catalogs at two
        # directory loads apiece = five total directory starts after
        # the successful rank, before the second pin, with the
        # independent pin count measured separately.
        assert counts2["pin_load"] == 1
        assert (counts2["directory"], counts2["directory_done"]) == (5, 5)
        assert (counts2["catalog"], counts2["catalog_done"]) == (2, 2)
        assert (
            counts2["bundle"],
            counts2["derived"],
            counts2["original"],
        ) == (
            pin_bundle + 2 * per_bundle + 2,
            pin_derived + 2 * per_derived + 2,
            pin_original + 2 * per_original + 2,
        )
        # The exact later pin start refused: the second physical pin
        # never loads, with the denying observation as its only read.
        assert counts2["read"] == 7
        # The completed first pin and bind are counted; the same
        # retained PinData anchors the sequence and both inter-delegate
        # boundaries restored the exact prior end.
        assert state2["n"] == 2
        assert state2["sequence"] == [
            ("pin", id(retained)),
            ("bind", None),
        ]
        assert boundaries2 == [original_end, original_end]
        assert fresh._invalid is True
        assert fresh.recheck(deadline_ms=1000) is False
        assert counts2["read"] == 7
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
        grade_fixture._custody_intact(owner, original_end)
    finally:
        ranking_fixture._close_owned(ctx, owner)
