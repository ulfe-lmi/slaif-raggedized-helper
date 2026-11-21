"""Owned private current graded cohort composition proof.

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
graded execution entry over the actual accepted donor fixture: the
positive two selected held-out cases h1 and h4 with the withheld
out-of-scope corpus two and the actual declared whole-batch a/c
projection - the corpus-two bundle b derived from the actual held
membership, every b revision/extraction span removed from the
test-local synthetic declaration with the resulting empty
requirement pruned, and b omitted from the declared Gold IDs only,
while the actual raw pin and the real selected b-withholding stay
intact - one initial physical pin, the guarded genuine current
direct grade catalog with its two genuine selected observations,
the distinct guarded post-catalog pin, two actual source
CASE_PIN reloads, two true T1/T2 encoder uses and two full
same-payload hybrid spans each followed by a completed real stage
diagnosis and the shared grading-owned GRADE_PIN / GRADE_BIND /
GRADE_PIN dispatch (h1 nonempty grade 3 on the a chunk, h4 empty),
the shared source aggregate and serialization, the one canonical
plan identity and the distinct full guarded grade FINAL_PIN
minting the private immutable owner-bound owning result only
after the final genuine selected reread, measured against the
exact legacy counts and per-case metadata in a
separately measured legacy phase; the two negative cases h1 and h2
with the corpus withheld on the original declaration, refusing the
whole declaration without a new physical reload or protected model
touch; and the mutation publishing one actual same-wire
selected-policy generation after the genuine final full raw reload
and before the final genuine selected reread, proving exact
FINAL_PIN progress, the same raw pointer, the restored owner/guard/
end, the latched admission and no usable report or storage.  No
local native witness execution: only the configured hosted CI
executes the three real hosted nodes, and local proof of this module
is collection only.
"""
import hashlib
import json
import os
import sys
import time
from dataclasses import FrozenInstanceError, asdict, fields
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import cpu_embedding_worker as cpu  # noqa: E402
from slaif_raggedized_helper import embedding_tokenizer  # noqa: E402
from slaif_raggedized_helper import evaluation_program as program  # noqa: E402
from slaif_raggedized_helper import private_policy_capture as capture  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import provenance_records as p  # noqa: E402
from slaif_raggedized_helper import raw_hybrid_search as hybrid  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_catalog as catalog  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_pin  # noqa: E402
from slaif_raggedized_helper import source_bound_stage_loss as stage_loss  # noqa: E402
from slaif_raggedized_helper import source_cohort_runner as runner  # noqa: E402
from slaif_raggedized_helper import supplied_rank_metrics as metrics  # noqa: E402
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility  # noqa: E402
from slaif_raggedized_helper import text_evaluation_dataset  # noqa: E402
import test_current_cohort_encoder_producer_composition as producer_fixture  # noqa: E402
import test_current_gold_dispatch_composition as gold_fixture  # noqa: E402
import test_current_grade_catalog_composition as grade_fixture  # noqa: E402
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


def _member_corpus(owner, ident):
    """The actual held membership entry's scope corpus for one bundle."""
    entry = next(e for e in owner.value.data.membership.entries
                 if e.bundle_container_id == ident)
    return p.admit_record("Scope", entry.scope_bytes).corpus


def _projected_declaration(owner, dataset, bundle_ids):
    """The actual declared whole-batch a/c projection.

    b is the corpus-two bundle derived from the actual held
    membership; every b revision/extraction span is removed from the
    test-local synthetic declaration, pruning the resulting empty
    requirement, so only a/c atoms remain.  b is omitted from the
    declared Gold IDs only; the actual raw pin and its selected
    withholding are left intact.  Returns the projected canonical
    dataset bytes and the declared a/c Gold ID tuple.
    """
    b_id = next(ident for ident in bundle_ids
                if _member_corpus(owner, ident) == "two")
    member_b = next(e for e in owner.value.data.membership.entries
                    if e.bundle_container_id == b_id)
    base = json.loads(dataset)
    dropped = {(member_b.revision_id, member_b.extraction_id)}
    for case in base["cases"]:
        requirements = []
        for requirement in case["requirements"]:
            alternatives = []
            for alternative in requirement["alternatives"]:
                spans = [span for span in alternative
                         if (span["revision_id"],
                             span["extraction_id"]) not in dropped]
                if spans:
                    alternatives.append(spans)
            if alternatives:
                requirements.append(requirement)
        case["requirements"] = requirements
    declared = tuple(ident for ident in bundle_ids if ident != b_id)
    return cohort_fixture.canonical(base), declared, member_b


def _authority_hash(authority, meter, check):
    return stage_loss._canonical_hash(
        [authority.model_dump(mode="json"), None], b"", meter, check,
        ensure_ascii=False, limit=262144)


def _query_identity(snapshot_id, catalog_id, question, payload, original,
                    effective, query_tuple):
    """The shared single-query expected identity, recomputed in its
    own domain from the known case authority and actual payload."""
    meter = stage_loss._Meter()
    question_hash = hashlib.sha256(question.encode()).hexdigest()
    payload_hash = hashlib.sha256(payload).hexdigest()
    original_hash = _authority_hash(original, meter, lambda: None)
    effective_hash = _authority_hash(effective, meter, lambda: None)
    query_id = stage_loss._canonical_hash(
        {
            "kind": "raw-hybrid-query/v1",
            "snapshot_id": snapshot_id,
            "catalog_id": catalog_id,
            "query_text_sha256": question_hash,
            "query_payload_sha256": payload_hash,
            "query_space_id": query_tuple[0],
            "query_definition_fingerprint": query_tuple[1],
            "query_policy_id": query_tuple[2],
            "query_execution_fingerprint": query_tuple[3],
            "authority_sha256": effective_hash,
            "dense_k": 60,
            "lexical_k": 60,
            "partition_cap": 60,
            "k": 60,
        },
        b"", meter, lambda: None, ensure_ascii=False)
    return (query_id, question_hash, payload_hash, original_hash,
            effective_hash)


def _plan_query_record(case_id, expected, query_tuple):
    return {
        "case_id": case_id,
        "query_id": expected[0],
        "question_sha256": expected[1],
        "payload_sha256": expected[2],
        "original_authority_sha256": expected[3],
        "effective_authority_sha256": expected[4],
        "space_id": query_tuple[0],
        "definition_fingerprint": query_tuple[1],
        "policy_id": query_tuple[2],
        "execution_fingerprint": query_tuple[3],
    }


def _graded_cohort(admission, owner, dataset, plan_wire, case_ids,
                   identifiers, bundle_ids, encoder):
    return runner._current_graded_cohort(
        admission, owner, dataset, plan_wire,
        runner.Cohort("held_out", tuple(case_ids)), identifiers,
        bundle_ids,
        runner.Config("cgc-cfg", "cgc-declaration"),
        runner.Budget(*runner._MAX_BUDGET),
        program.GradeBudget(*program._MAX_BUDGET),
        encoder,
    )


def test_graded_cohort_positive_two_cases_match_legacy_dispatch(
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
            a, c, _b = ctx.chunk_ids
            chunks = {"a": a, "c": c, "b": _b}
            # The actual declared whole-batch a/c projection before
            # the positive span: the corpus-two bundle is derived from
            # the actual held membership, its revision/extraction
            # spans are pruned from the synthetic declaration and it
            # is omitted from the declared Gold IDs only.
            dataset_ac, declared, member_b = _projected_declaration(
                owner, dataset, bundle_ids)
            admitted_ac = text_evaluation_dataset.admit(dataset_ac)
            assert admitted_ac.case_count == 5
            assert admitted_ac.gold_atom_count == 6
            assert len(declared) == 2
            ctx.pointer_generation = owner.value.pointer.generation
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            # The fresh admission after the expensive fixture setup;
            # its own entry reads precede the cut counters.
            admission = ppr.request_current_view(reader,
                                                 gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            policy_snapshot = pin_eligibility._isolated_policy_snapshot(
                admission)
            anchor = pin_eligibility._bounded_admission(
                pin_eligibility._admitted_principal_grants(
                    policy_snapshot, admission.principal_id))
            full_grants = pin_eligibility._bound_grants(admission, anchor)
            # The corpus-two partition is genuinely unavailable under
            # the selected policy while the same real pin still holds
            # it.
            unavailable = set(policy_eligibility.unavailable_partitions(
                policy_snapshot, owner.value.data.membership))
            assert member_b.partition_id in unavailable
            rows1, u1, _case1, original1, effective1, _restricted1 = (
                _eligible(ctx, owner, dataset_ac, "h1", full_grants))
            rows4, u4, _case4, original4, effective4, _restricted4 = (
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
                    mints = []
                    real_mint = program._mint_owning_grade_report

                    def mint_spy(*args, **kwargs):
                        result = real_mint(*args, **kwargs)
                        mints.append(result)
                        return result

                    monkeypatch.setattr(
                        program, "_mint_owning_grade_report", mint_spy)
                    wire = grade_fixture._plan_wire(
                        ctx, admitted_ac, ctx.catalog_id,
                        (("h1", ((chunks["a"], 3),)), ("h4", ())),
                    )
                    report = _graded_cohort(
                        admission, owner, dataset_ac, wire,
                        ("h1", "h4"), (expected, expected), declared,
                        sc["encoder"])
                finally:
                    os.write = real_write
                # One genuine shared source cohort and grade result,
                # the private immutable owner-bound owning result.
                assert type(report) is program._OwningGradeReport
                grade_doc = json.loads(report.identity_payload)
                assert grade_doc["schema"] == \
                    "slaif-graded-evaluation-program-v1"
                assert grade_doc["plan_id"] == "plan"
                assert grade_doc["protocol_id"] == "protocol"
                assert grade_doc["unit"] == "FROZEN_SNAPSHOT_CHUNK_ID"
                assert grade_doc["dataset_id"] == admitted_ac.dataset_id
                assert grade_doc["split_id"] == admitted_ac.split_id
                assert grade_doc["split"] == "held_out"
                assert grade_doc["selection"] == "DECLARED_SUBSET"
                assert grade_doc["dataset_case_count"] == 5
                assert grade_doc["selected_case_count"] == 2
                assert grade_doc["snapshot_id"] == held.data.snapshot_id
                assert grade_doc["generation"] == held.pointer.generation
                assert grade_doc["catalog_id"] == ctx.catalog_id
                assert grade_doc["config_id"] == "cgc-cfg"
                assert report.identity == "sha256:" + hashlib.sha256(
                    b"slaif-graded-evaluation-program-v1\n"
                    + report.identity_payload).hexdigest()
                # The exact named work and payload caps of the real
                # source Budget and grade GradeBudget: the source
                # ordinals 10 and 11 are the geometry and aggregate
                # call limits, while the source work bounds are the
                # named local work and payload fields.
                budget_caps = runner.Budget(*runner._MAX_BUDGET)
                grade_caps = program.GradeBudget(*program._MAX_BUDGET)
                assert 0 < report.final_work <= grade_caps.local_work
                assert (0 < report.final_payload
                        <= grade_caps.local_payload)
                # The original source payload embedded as an exact
                # JSON value, once; the outer source identity is the
                # domain digest of those exact bytes, re-derived
                # through the canonical round trip.
                source_doc = grade_doc["source_payload"]
                source_payload = json.dumps(
                    source_doc, ensure_ascii=True,
                    separators=(",", ":")).encode("ascii")
                assert grade_doc["source_identity"] == "sha256:" + \
                    hashlib.sha256(
                        b"slaif-source-cohort-runner-v1\n"
                        + source_payload).hexdigest()
                assert (0 < grade_doc["source_final_work"]
                        <= budget_caps.local_work)
                assert (0 < grade_doc["source_final_payload"]
                        <= budget_caps.local_payload)
                assert grade_doc["grade_budget"] == {
                    item.name: cap for item, cap in zip(
                        fields(program.GradeBudget), program._MAX_BUDGET)}
                assert grade_doc["statuses"] == {
                    "baseline": "NOT_RUN",
                    "authorship": "DECLARED_UNVERIFIED",
                    "rights": "DECLARED_UNVERIFIED",
                    "current_policy": "CHECKED",
                    "encoder": "NOT_QUALIFIED",
                    "model": "NOT_QUALIFIED",
                    "scale": "NOT_QUALIFIED",
                    "quality": "NOT_QUALIFIED",
                    "visual": "NOT_QUALIFIED",
                    "mvp": "NOT_QUALIFIED",
                }
                assert set(grade_doc["variants"]) == {
                    "dense", "lexical", "fusion"}
                # The embedded source report is the genuine shared
                # source result over the same completed cases.
                assert source_doc["schema"] == "slaif-source-cohort-runner-v1"
                assert source_doc["split"] == "held_out"
                assert source_doc["selection_kind"] == "DECLARED_SUBSET"
                assert source_doc["selected_count"] == 2
                assert source_doc["dataset_case_count"] == 5
                assert source_doc["dataset_gold_occurrences"] == 6
                assert source_doc["progress"] == {
                    "intended": 2, "attempted": 2, "completed": 2,
                    "refused": 0, "pending": 0}
                assert source_doc["pointer_sha256"] == hashlib.sha256(
                    held.pointer.pointer_bytes).hexdigest()
                assert source_doc["generation"] == held.pointer.generation
                assert source_doc["snapshot_id"] == held.data.snapshot_id
                assert source_doc["statuses"]["producer"] == "COMPLETED"
                assert source_doc["statuses"]["baseline"] == "NOT_RUN"
                assert source_doc["statuses"]["policy"] == "CHECKED"
                assert source_doc["statuses"]["current_rights"] == \
                    "NOT_QUALIFIED"
                sources = runner._source_reservation(2)
                extra = runner._current_owned_extra_reservation(2)
                ledger = source_doc["ledger"]
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
                assert source_doc["caps"] == dict(zip(
                    (item.name for item in fields(runner.Budget)),
                    runner._MAX_BUDGET))
                pure = source_doc["pure"]
                encoded = json.dumps(
                    pure["identity_payload"], ensure_ascii=True,
                    separators=(",", ":")).encode("ascii")
                assert pure["identity"] == "sha256:" + hashlib.sha256(
                    b"slaif-declared-cohort-metrics-v1\n"
                    + encoded).hexdigest()
                assert 0 < pure["final_work"] <= budget_caps.aggregate_work
                assert (0 < pure["final_payload"]
                        <= budget_caps.aggregate_payload)
                # The one canonical graded plan identity over the
                # complete ordered actual query metadata.
                expected_h1 = _query_identity(
                    ctx.snapshot_id, ctx.catalog_id, QUESTION_H1,
                    producer_calls[0], original1, effective1, expected)
                expected_h4 = _query_identity(
                    ctx.snapshot_id, ctx.catalog_id, QUESTION_H4,
                    producer_calls[1], original4, effective4, expected)
                identity = {
                    "schema": "slaif-graded-evaluation-plan-v1",
                    "plan": {
                        "plan_id": "plan",
                        "dataset_id": admitted_ac.dataset_id,
                        "split_id": admitted_ac.split_id,
                        "snapshot_id": ctx.snapshot_id,
                        "generation": ctx.pointer_generation,
                        "catalog_id": ctx.catalog_id,
                        "protocol_id": "protocol",
                        "unknown_policy": "UNJUDGED_AS_ZERO_DIAGNOSTIC",
                        "overlap_policy": "EXPLICIT_CHUNK_IDS_ONLY",
                        "cutoffs": (20, 60),
                    },
                    "judgments": (
                        ("h1", ((chunks["a"], 3),)), ("h4", ())),
                    "dataset_id": admitted_ac.dataset_id,
                    "split_id": admitted_ac.split_id,
                    "cohort": ("held_out", ("h1", "h4")),
                    "selection": "DECLARED_SUBSET",
                    "config": ("cgc-cfg", "cgc-declaration"),
                    "queries": (
                        _plan_query_record("h1", expected_h1, expected),
                        _plan_query_record("h4", expected_h4, expected),
                    ),
                    "gold_bundle_ids": declared,
                    "source_budget": runner._MAX_BUDGET,
                    "grade_budget": program._MAX_BUDGET,
                }
                meter = stage_loss._Meter()
                assert grade_doc["plan_identity"] == "sha256:" + \
                    stage_loss._canonical_hash(
                        identity, b"slaif-graded-evaluation-plan-v1\n",
                        meter, lambda: None, limit=8388608)
                # The graded case records: h1 nonempty grade 3 on the
                # a chunk, h4 empty, both under the exact shared
                # binder output gate.
                cases_doc = grade_doc["cases"]
                assert [c["case_id"] for c in cases_doc] == ["h1", "h4"]
                assert cases_doc[0]["query_id"] == expected_h1[0]
                assert cases_doc[0]["original_authority_sha256"] == \
                    expected_h1[3]
                assert cases_doc[0]["effective_authority_sha256"] == \
                    expected_h1[4]
                assert cases_doc[0]["row_count"] == 1
                assert cases_doc[0]["fragment_count"] > 0
                assert cases_doc[0]["source_binding_status"] == \
                    "ORIGINALS_REVALIDATED_AT_BIND_TIME"
                assert cases_doc[0]["judgment_fingerprint"] == \
                    "sha256:" + stage_loss._canonical_hash(
                        ((chunks["a"], 3),),
                        b"slaif-graded-judgments-v1\n",
                        stage_loss._Meter(), lambda: None, limit=1048576)
                assert cases_doc[1]["query_id"] == expected_h4[0]
                assert cases_doc[1]["row_count"] == 0
                assert cases_doc[1]["fragment_count"] == 0
                assert cases_doc[1]["source_binding_status"] == \
                    "NO_SELECTED_SOURCE_VALIDATED"
                # The embedded source cases match the actual shared
                # per-case result checks.
                source_cases = source_doc["cases"]
                assert [c["case_id"] for c in source_cases] == ["h1", "h4"]
                assert source_cases[0]["question_sha256"] == \
                    hashlib.sha256(QUESTION_H1.encode()).hexdigest()
                assert source_cases[1]["question_sha256"] == \
                    hashlib.sha256(QUESTION_H4.encode()).hexdigest()
                assert source_cases[0]["payload_sha256"] == \
                    hashlib.sha256(producer_calls[0]).hexdigest()
                assert source_cases[1]["payload_sha256"] == \
                    hashlib.sha256(producer_calls[1]).hexdigest()
                assert source_cases[0]["chosen_atom_occurrences"] == 1
                assert source_cases[1]["chosen_atom_occurrences"] == 0
                assert source_cases[0]["eligible_row_count"] == rows1
                assert source_cases[1]["eligible_row_count"] == rows4
                assert source_cases[0]["dataset_atom_occurrences"] == 6
                assert source_cases[1]["dataset_atom_occurrences"] == 6
                # Twenty-one actual full pin loads: three direct
                # source runner pins (one initial plus one CASE_PIN
                # per case), twelve completed delegate source
                # observations, one distinct guarded post-catalog
                # grade pin, two grade revalidations per case and the
                # distinct full guarded grade final pin.
                assert counts["pin_load"] == 21
                # Seventy-five actual raw directory starts and
                # successful completions: fifty-nine source (one
                # initial plus twenty-nine per case) plus sixteen
                # grade (two direct catalog, one post-catalog pin,
                # six per case and one final pin), the exact
                # independently sourced n=2 forecast.
                assert dir_counts == {"start": 75, "done": 75}
                # The delegated bundle, derived and original loads of
                # the initial pin, the two actual source cases under
                # the two declared bundles, and the grade pin,
                # catalog and rank loads.
                case1 = _bundle_work(directory, catalog_shape, u1, 2)
                case4 = _bundle_work(directory, catalog_shape, u4, 2)
                grade_pins = tuple(6 * directory[i] for i in range(3))
                grade_catalogs = tuple(5 * catalog_shape[i]
                                       for i in range(3))
                rank_tail = (2, 2, 2)
                assert (counts["bundle"], counts["derived"],
                        counts["original"]) == tuple(
                            directory[i] + case1[i] + case4[i]
                            + grade_pins[i] + grade_catalogs[i]
                            + rank_tail[i]
                            for i in range(3))
                # The initial two observations, the two genuine
                # selected observations of the guarded direct
                # catalog, the two genuine selected observations of
                # the guarded post-catalog pin, the two full
                # case-scoped source observation spans in declaration
                # order with the shared grading-owned dispatch reads
                # (two revalidations and the delegated pinned rank
                # binding) after each, and the distinct full guarded
                # grade final pin's two genuine selected
                # observations.
                assert counts["read"] == [1, 1] + [1, 1] + [1, 1] \
                    + [1] * _case_reads(u1, 2) + [1] * 8 \
                    + [1] * _case_reads(u4, 2) + [1] * 6 + [1, 1]
                # Four direct hybrid catalog loads and twenty-three
                # nested: nine per source case plus the one direct
                # grade catalog and four delegated grade rank
                # catalog rebuilds.
                assert catalog_counts == {"direct": 4, "nested": 23}
                # Two actual T1 text and T2 token-ID spans, one per
                # case, as actual delegated kernel bytes matched by
                # live pipe identity.
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
                # prepared pin, the direct catalog, the post-catalog
                # pin, the two CASE_PIN reloads, the two producer
                # spans, the two stage dispatches, the two grade
                # dispatches and the distinct full guarded final pin
                # - the restored exact prior end, the released guard,
                # the live admission and the still-open resident.
                assert owner.value is held
                assert owner.state == "ACTIVE"
                assert owner.op.end == prior_end
                assert not owner.guard.locked()
                assert admission._invalid is False
                assert sc["encoder"]._state == "open"
                # The private immutable owner-bound owning result,
                # minted exactly once: the exact admission with its
                # captured selected publication bytes and admitted
                # operations, the detached original grants, anchor and
                # operation, the absolute clipped deadline, the exact
                # original custody, the retained capture and the
                # immutable snapshot and generation, with the grade
                # report digest independently re-derived above.
                assert len(mints) == 1
                assert mints[0] is report
                assert report.owner is owner
                assert report.admission is admission
                assert report.selected_bytes == (
                    admission._expected_selection_bytes)
                assert report.operations == admission.operations
                assert report.grants == full_grants
                assert report.anchor == anchor
                assert report.original_op is owner.op
                assert report.originals is owner.originals
                assert report.derived is owner.derived
                assert report.root == str(owner.op.path)
                assert report.capture is held
                assert type(report.end) is float
                assert 0 < report.end <= admission._end
                assert report.snapshot_id == held.data.snapshot_id
                assert report.generation == held.pointer.generation
                # The bound result is immutable through normal Python
                # use: ordinary mutation and deletion of
                # representative bound fields and the original
                # type's ordinary construction are all refused; no
                # defense against deliberate Python introspection is
                # claimed.
                with pytest.raises(FrozenInstanceError):
                    report.owner = None
                with pytest.raises(FrozenInstanceError):
                    del report.generation
                with pytest.raises(ValueError):
                    program._OwningGradeReport()
                # The custody recheck uses the genuine reader (not a
                # guarded cut), so the real reader is restored first.
                real_read_bound = (
                    capture.PolicyCaptureReader.read_selection.__get__(
                        reader, type(reader)))
                monkeypatch.setattr(reader, "read_selection",
                                    real_read_bound)
                assert admission.recheck(deadline_ms=30000) is True
            # The stable per-case metadata of the current guarded
            # dispatches matches the exact legacy unguarded route with
            # the same good payloads in its separately measured phase,
            # on the exact case-bound grants derived through the
            # genuine existing case-scope intersection.
            restore()
            items = {c["case_id"]: c for c in source_cases}
            for case_id, question, payload, (rows, u, case, original,
                                             effective, _restricted) in (
                ("h1", QUESTION_H1, producer_calls[0],
                 (rows1, u1, _case1, original1, effective1,
                  _restricted1)),
                ("h4", QUESTION_H4, producer_calls[1],
                 (rows4, u4, _case4, original4, effective4,
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
                        owner, dataset_ac, case.case_id, declared, legacy,
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
                grade_case = cases_doc[0 if case_id == "h1" else 1]
                assert grade_case["query_id"] == legacy.query_id
                # The actual dense, lexical and fusion rankings of
                # the same legacy search verify the reported metric
                # query result for this exact query ID through the
                # product's own serializer round trip: the h1
                # grade-3 declared gold unit retrieved with the
                # dense and fusion improvement and the lexical zero,
                # and the h4 empty-gold cutoff rows undefined.
                rankings = {
                    "dense": tuple(h.chunk_id for h in legacy.dense.hits),
                    "lexical": tuple(h.chunk_id
                                     for h in legacy.lexical.hits),
                    "fusion": tuple(h.chunk_id for h in legacy.fusion.hits),
                }
                gold = ((chunks["a"], 3),) if case_id == "h1" else ()
                for name, ranking in rankings.items():
                    variant = json.loads(grade_doc["variants"][name])
                    reported = next(
                        item for item in variant["query_results"]
                        if item["query_id"] == legacy.query_id)
                    recomputed = json.loads(json.dumps(asdict(
                        metrics.score_query(
                            legacy.query_id, gold, ranking,
                            cutoffs=(20, 60), deadline_ms=5000))))
                    assert reported == recomputed
                    if case_id == "h1":
                        assert reported["positive_gold_count"] == 1
                        retrieved = name != "lexical"
                        for value in reported["at_k"]:
                            assert (value["relevant_returned"],
                                    value["recall"]) == (
                                        1 if retrieved else 0,
                                        1.0 if retrieved else 0.0)
                    else:
                        assert reported["positive_gold_count"] == 0
                        for value in reported["at_k"]:
                            assert (value["relevant_returned"],
                                    value["recall"],
                                    value["reciprocal_rank"],
                                    value["ndcg"]) == (0, None, None, None)
                            assert value["undefined_reason"] == (
                                "UNDEFINED_EMPTY_POSITIVE_GOLD")
        finally:
            gold_fixture._close_owned(ctx, owner)
    finally:
        sc["encoder"].close()
    # Reaping evidence: the real cleanup reaped both real children.
    assert worker_child.poll() is not None and token_child.poll() is not None


def test_graded_cohort_unavailable_declaration_refuses_without_work(
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
            a, _c, _b = ctx.chunk_ids
            ctx.pointer_generation = owner.value.pointer.generation
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            # The pure all-case scope admission of the exact ordered
            # cohort with the withheld corpus two refuses before any
            # new pin, directory, ingestion, original, selected or
            # protected work.
            admission = ppr.request_current_view(reader,
                                                 gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            admitted = text_evaluation_dataset.admit(dataset)
            wire = grade_fixture._plan_wire(
                ctx, admitted, ctx.catalog_id,
                (("h1", ((_c, 3),)), ("h2", ())),
            )
            # The real helper encodes exactly the singleton h1
            # judgment pair and the empty h2 judgment.
            assert json.loads(wire.decode("ascii"))["judgments"] == [
                {"case_id": "h1", "gold": [[_c, 3]]},
                {"case_id": "h2", "gold": []},
            ]
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
                    with pytest.raises(program.EvaluationError) as exc:
                        _graded_cohort(admission, owner, dataset, wire,
                                       ("h1", "h2"), (expected, expected),
                                       bundle_ids, sc["encoder"])
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


def test_graded_cohort_generation_change_after_final_pin(
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
            a, c, _b = ctx.chunk_ids
            chunks = {"a": a, "c": c, "b": _b}
            dataset_ac, declared, _member_b = _projected_declaration(
                owner, dataset, bundle_ids)
            admitted_ac = text_evaluation_dataset.admit(dataset_ac)
            assert admitted_ac.case_count == 5
            assert admitted_ac.gold_atom_count == 6
            ctx.pointer_generation = owner.value.pointer.generation
            held = owner.value
            raw_pointer = owner.value.pointer
            prior_end = time.monotonic() - 60.0
            owner.op.end = prior_end
            admission = ppr.request_current_view(reader,
                                                 gold_fixture.CREDENTIAL,
                                                 deadline_ms=30000)
            policy_snapshot = pin_eligibility._isolated_policy_snapshot(
                admission)
            anchor = pin_eligibility._bounded_admission(
                pin_eligibility._admitted_principal_grants(
                    policy_snapshot, admission.principal_id))
            full_grants = pin_eligibility._bound_grants(admission, anchor)
            rows1, u1, _case1, original1, effective1, _restricted1 = (
                _eligible(ctx, owner, dataset_ac, "h1", full_grants))
            rows4, u4, _case4, original4, effective4, _restricted4 = (
                _eligible(ctx, owner, dataset_ac, "h4", full_grants))
            counts = producer_fixture._counts()
            changed = {"flag": False}
            completed = []
            # A test-local spy around the genuine held revalidation
            # publishes the real same-wire generation after the
            # genuine final full raw reload - by which point both
            # ordered cases have genuinely completed - before the
            # final genuine selected reread; the actual case
            # completion is observed through a test-local wrapper
            # around the genuine record step, so no numerical read
            # index decides when the change is published.
            real_case_record = runner._case_record

            def record_after_real(*args, **kwargs):
                real_case_record(*args, **kwargs)
                completed.append(args[-1])
            monkeypatch.setattr(runner, "_case_record", record_after_real)
            real_held_revalidation = raw_snapshot_pin.PinOwner._held_revalidation

            def final_pin_change(self, *args, **kwargs):
                result = real_held_revalidation(self, *args, **kwargs)
                if not changed["flag"] and completed == ["h1", "h4"]:
                    changed["flag"] = True
                    producer_fixture._change_generation(
                        policy_root, 2, payload)
                return result
            monkeypatch.setattr(
                raw_snapshot_pin.PinOwner, "_held_revalidation",
                final_pin_change)
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
                mints = []
                real_mint = program._mint_owning_grade_report

                def mint_spy(*args, **kwargs):
                    result = real_mint(*args, **kwargs)
                    mints.append(result)
                    return result

                monkeypatch.setattr(
                    program, "_mint_owning_grade_report", mint_spy)
                try:
                    wire = grade_fixture._plan_wire(
                        ctx, admitted_ac, ctx.catalog_id,
                        (("h1", ((chunks["a"], 3),)), ("h4", ())),
                    )
                    with pytest.raises(program.EvaluationError) as exc:
                        _graded_cohort(admission, owner, dataset_ac, wire,
                                       ("h1", "h4"), (expected, expected),
                                       declared, sc["encoder"])
                finally:
                    os.write = real_write
            restore()
            assert changed["flag"] is True
            # Both intended cases complete before the cut, and the
            # final genuine selected reread observes the published
            # same-wire generation change after the genuine final
            # full raw reload, refusing before any usable report.
            assert producer_fixture._refusal_prefix(
                exc.value.progress) == ("FINAL_PIN", 2, 2, 2, 0, 0)
            # The full span completes: twenty-one actual full pin
            # loads including the final full raw reload, seventy-five
            # actual directory starts and completions, and the
            # complete delegated load and observation trace.
            assert counts["pin_load"] == 21
            assert dir_counts == {"start": 75, "done": 75}
            case1 = _bundle_work(directory, catalog_shape, u1, 2)
            case4 = _bundle_work(directory, catalog_shape, u4, 2)
            grade_pins = tuple(6 * directory[i] for i in range(3))
            grade_catalogs = tuple(5 * catalog_shape[i]
                                   for i in range(3))
            rank_tail = (2, 2, 2)
            assert (counts["bundle"], counts["derived"],
                    counts["original"]) == tuple(
                        directory[i] + case1[i] + case4[i]
                        + grade_pins[i] + grade_catalogs[i]
                        + rank_tail[i]
                        for i in range(3))
            assert counts["read"] == [1, 1] + [1, 1] + [1, 1] \
                + [1] * _case_reads(u1, 2) + [1] * 8 \
                + [1] * _case_reads(u4, 2) + [1] * 6 + [1, 1]
            assert catalog_counts == {"direct": 4, "nested": 23}
            # Both actual T1 and T2 spans and the two same-payload
            # producer dispatches completed before the cut.
            assert sum(actual for pipe, _req, actual in writes
                       if pipe == id(token_pipe)) == (
                           transport._frame_len(QUESTION_H1)
                           + transport._frame_len(QUESTION_H4))
            receipts = [r for kind, r in events if kind == "receipt"]
            assert len(receipts) == 2
            forwards = [rows for kind, rows in events
                        if kind == "forward"]
            assert forwards == [
                [receipts[0].ids], [receipts[1].ids]]
            assert session._tokenizer._calls == 2
            assert session._worker._calls == 2
            assert len(producer_calls) == 2
            assert producer_calls[0] == producer_fixture.PAYLOAD
            assert len(producer_calls[1]) == 4096
            # No usable result was minted on the exact final denial:
            # the private owning result exists only after the final
            # genuine selected reread.
            assert mints == []
            # The genuine admission latches on the observed change,
            # and the exact raw pointer and owner survive it with the
            # restored exact prior end and released guard; no usable
            # report or storage exists.
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
