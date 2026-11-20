"""Owned private case-bound held-pin hybrid dispatch composition proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The real
``make_owned_support`` owned-source fixture (three real sources a, b, c
over corpora one/two with the secret label on b), the real
``dataset_and_bundles`` cohort dataset (actual owned source atoms and
the h1/h2 case declarations), the real raw snapshot selector and the
actual ``PinOwner.acquire_selected_data`` build the pinned data; the
existing reviewed synthetic policy wire/selector fixtures (synthetic
principal, credential, attributed wire emitter, payload installer and
atomic selected-record publication) are reused byte-exact from
``test_private_pinned_hybrid_composition`` and provide no writer
qualification.  The supported request lifetime begins after the
expensive fixture setup.  Counting wrappers delegate the real catalog,
directory, engine, owner-load and reader functions at the intended
boundaries; counts run from the private dispatch after fixture
acquisition, selection and pinning.  The actual positive and negative
witnesses are the entry's own fixed refusal and result; fixture
construction failure is never passing evidence.  The real native
fixtures are hosted-only; locally only collection is expected.
"""
import hashlib
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import private_policy_capture as capture
from slaif_raggedized_helper import private_policy_request as ppr
from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import raw_hybrid_search as hybrid
from slaif_raggedized_helper import raw_snapshot_selection as selection
from slaif_raggedized_helper import text_evaluation_dataset as evaluation
from slaif_raggedized_helper.raw_snapshot_pin import PinOwner
import test_source_bound_support_ci_composition as support_fixture
import test_source_cohort_runner_composition as cohort_fixture
from test_private_pinned_hybrid_composition import (  # noqa: F401
    CREDENTIAL,
    VECTOR,
    _close_owned,
    _counts,
    _documents_from_membership,
    _engine_counts,
    _install_policy,
    _install_witness,
)
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401


def _scenario(tmp_path, *, withhold_two=True):
    """One real scenario: owned support, real selector, real pin, genuine
    policy admission and the real cohort dataset; the request lifetime
    begins after fixture setup, selection and pin."""
    ctx = support_fixture.make_owned_support(tmp_path)
    owner = None
    try:
        originals, derived = ctx.originals, ctx.derived
        core = json.loads(
            (Path(ctx.root) / "snapshots" / ctx.snapshot_id[7:] /
             ".core.json").read_bytes()
        )
        embedding = core["embedding"]
        selection.compare_and_select_data(
            originals, derived, ctx.root, ctx.snapshot_id, None)
        owner = PinOwner()
        owner.acquire_selected_data(originals, derived, ctx.root,
                                    deadline_ms=30000)
        documents = _documents_from_membership(owner, withhold_two=withhold_two)
        policy_root, _payload = _install_policy(tmp_path, "policy", documents)
        reader = capture.PolicyCaptureReader(str(policy_root))
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        data, _bundles = cohort_fixture.dataset_and_bundles(ctx)
        return ctx, embedding, owner, policy_root, reader, admission, data
    except BaseException:
        if owner is not None:
            try:
                owner.close()
            except BaseException:
                pass
        raise


def _dispatch_case(admission, owner, data, case_id, embedding, *, deadline_ms=30000):
    return hybrid.search_pinned_case(
        admission,
        owner,
        data,
        case_id,
        VECTOR.tobytes(),
        query_space_id=embedding["space_id"],
        query_definition_fingerprint=embedding["definition_fingerprint"],
        query_policy_id=embedding["query_policy_fingerprint"],
        query_execution_fingerprint=embedding["query_execution_fingerprint"],
        dense_k=3,
        lexical_k=3,
        partition_cap=3,
        k=3,
        deadline_ms=deadline_ms,
    )


def test_case_bound_narrowed_positive_journey(tmp_path, monkeypatch):
    (ctx, embedding, owner, policy_root, reader, admission, data) = _scenario(tmp_path)
    try:
        # A still-live pin: the bounded case-bound request must succeed
        # and the original operation end must return.
        original_end = owner.op.end
        counts = _counts()
        _install_witness(monkeypatch, reader, counts)
        result = _dispatch_case(admission, owner, data, "h1", embedding)
        # Five genuine current observations and one real positive
        # engine/owner proof: the shared body ran once with the
        # effective grants, including the one distinct final owner
        # validation load.
        assert _engine_counts(counts) == (8, 17, 1, 1, 1)
        assert counts["read"] == 5
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        # The withheld corpus-two partition is outside the actual
        # effective readable scope and does not block it: only a and c
        # contribute.
        assert (result.dense.eligible, result.dense.selected,
                result.dense.returned) == (2, 2, 2)
        assert (result.lexical.eligible, result.lexical.matching,
                result.lexical.returned) == (2, 1, 1)
        assert (result.fusion.dense_input_rows, result.fusion.lexical_input_rows,
                result.fusion.unique_candidates, result.fusion.overlap_candidates) \
            == (2, 1, 2, 1)
        assert [h.score for h in result.dense.hits] == pytest.approx([0.8, 0.6])
        assert result.fusion.hits[0].score == pytest.approx(2 / 61)
        assert result.snapshot_id == ctx.snapshot_id
        assert result.query_origin == "SUPPLIED_UNVERIFIED"
        assert result.qualification == "NOT_QUALIFIED"
        # Independent authority binding: the exact narrowed effective
        # value derived from the full anchor and the case declaration,
        # with no additional caller restriction.
        effective = p.Grants(schema_version=1, corpora=("one",), versions=("v1",),
                             labels=())
        expected_authority = hashlib.sha256(
            json.dumps([effective.model_dump(mode="json"), None], sort_keys=True,
                       ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert result.authority_sha256 == expected_authority
        # The one real hybrid body is unchanged: the exact admitted case
        # question and the same supplied arguments through the public
        # legacy entry, explicitly run with those effective grants,
        # yield the same result.
        case = next(c for c in evaluation.admit(data).cases if c.case_id == "h1")
        dispatch_counts = _engine_counts(counts)
        legacy = hybrid.search(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, case.question,
            VECTOR.tobytes(),
            query_space_id=embedding["space_id"],
            query_definition_fingerprint=embedding["definition_fingerprint"],
            query_policy_id=embedding["query_policy_fingerprint"],
            query_execution_fingerprint=embedding["query_execution_fingerprint"],
            grants=effective, dense_k=3, lexical_k=3, partition_cap=3, k=3)
        assert result == legacy
        # Legacy is counted separately: the same real body re-runs the
        # engines once more without any owner validation load and with
        # no further reader call.
        assert _engine_counts(counts) == tuple(
            part + extra for part, extra in zip(dispatch_counts,
                                                (8, 16, 1, 1, 1)))
        assert counts["read"] == 5
    finally:
        _close_owned(ctx.originals, ctx.derived, owner)


def test_case_bound_withheld_partition_refuses_before_catalog(tmp_path, monkeypatch):
    (ctx, embedding, owner, policy_root, reader, admission, data) = _scenario(tmp_path)
    try:
        original_end = owner.op.end
        counts = _counts()
        _install_witness(monkeypatch, reader, counts)
        # (1) h2 under the same admitted synthetic policy reads
        # (one, two, v1, secret): the withheld corpus-two partition is
        # now inside the effective readable scope and refuses through
        # the real policy admission and case declaration before any new
        # catalog, directory, dense, lexical or fusion call, after the
        # one genuine first observation.
        with pytest.raises(hybrid.HybridSearchError, match="^hybrid search refused$"):
            _dispatch_case(admission, owner, data, "h2", embedding)
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 1
        # The refusal is the entry's own fixed content-free ordinary
        # refusal; the admission is not latched and custody is
        # restored.
        assert admission._invalid is False
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        # (2) Absent case: no admitted case carries this ID, so the
        # dispatch refuses before custody, before any observation and
        # without widening to any other case or the full scope.
        with pytest.raises(hybrid.HybridSearchError, match="^hybrid search refused$"):
            _dispatch_case(admission, owner, data, "h9", embedding)
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 1
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        # (3) Invalid case bytes: the tampered canonical dataset is
        # refused under the genuine parser before custody and before
        # any observation.
        bad = data[:-1] + b"z"
        with pytest.raises(hybrid.HybridSearchError, match="^hybrid search refused$"):
            _dispatch_case(admission, owner, bad, "h1", embedding)
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 1
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        # The owner and reader state is stable across every refusal.
        assert owner.value is not None
        assert owner.state == "ACTIVE"
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        assert admission._invalid is False
    finally:
        _close_owned(ctx.originals, ctx.derived, owner)
