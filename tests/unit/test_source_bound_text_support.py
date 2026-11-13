"""Root concrete vectors with controlled source-binding boundaries."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from slaif_raggedized_helper import source_bound_text_support as subject
from slaif_raggedized_helper import text_evaluation_dataset as dataset_module
from slaif_raggedized_helper.text_evaluation_gold_binding import GoldBinding
from slaif_raggedized_helper.source_bound_ranking import BoundFragment, BoundRow, BoundRanking

ORACLE = json.loads(
    (Path(__file__).parents[2] / "docs/parallel/source-bound-text-support-oracle.json").read_text()
)
VECTOR = ORACLE["concrete_input_vector"]
DATA = VECTOR["dataset_ascii"].encode("ascii")
ID = "sha256:" + "a" * 64
BUNDLE = "b" * 64


def fixtures():
    ds = dataset_module.admit(DATA)
    atoms = {
        subject._atom(a)
        for c in ds.cases
        for r in c.requirements
        for alt in r.alternatives
        for a in alt
    }
    gold = SimpleNamespace(
        dataset_id=ds.dataset_id,
        split_id=ds.split_id,
        dataset_sha256=hashlib.sha256(DATA).hexdigest(),
        case_count=ds.case_count,
        bindings=tuple(GoldBinding(*a, (BUNDLE,)) for a in sorted(atoms)),
        distinct_atom_count=len(atoms),
        gold_atom_occurrences=4,
        binding_id=ID,
        source_binding_status="ORIGINALS_REVALIDATED_AT_BIND_TIME",
    )
    rows = tuple(
        BoundRow(
            i,
            ID,
            chunk,
            rev,
            ext,
            ID,
            ID,
            ID,
            ID,
            tuple(BoundFragment(block, lo, hi, "f" * 64) for block, lo, hi in fragments),
        )
        for i, (chunk, rev, ext, fragments) in enumerate(VECTOR["geometry_ranking"])
    )
    rank = BoundRanking(
        ID,
        ID,
        ID,
        "c" * 64,
        rows,
        len(rows),
        sum(len(r.fragments) for r in rows),
        "ORIGINALS_REVALIDATED_AT_BIND_TIME",
    )
    return gold, rank


def call(case="case1", chunks=None, **kwargs):
    if chunks is None:
        chunks = tuple(row[0] for row in VECTOR["geometry_ranking"])
    return subject.score_case(
        None,
        None,
        "/private",
        ID,
        ID,
        DATA,
        case,
        (BUNDLE,),
        chunks,
        grants=None,
        cutoffs=(1, 2, 3, 4),
        **kwargs,
    )


def test_concrete_geometry_and_case_association():
    gold, rank = fixtures()
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold) as gb,
        patch.object(subject.source_bound_ranking, "bind", return_value=rank) as rb,
    ):
        result = call()
        assert json.loads(json.dumps([asdict(x) for x in result.at_k])) == VECTOR["expected_at_k"]
        assert (result.case_gold_atom_occurrences, result.case_distinct_gold_atoms) == (4, 4)
        assert result.qualification == "NOT_QUALIFIED"
        assert result.gold_eligibility == "NOT_CHECKED"
        assert gb.call_args.args[2] == DATA
        assert rb.call_args.args[5] == tuple(row[0] for row in VECTOR["geometry_ranking"])
        unknown = call("case2")
        unanswerable = call("case3")
        assert unknown.case_answerability != unanswerable.case_answerability
        assert all(
            x.requirement_fraction is None and x.undefined_reason == "NO_GOLD_REQUIREMENTS"
            for item in (unknown, unanswerable)
            for x in item.at_k
        )
        assert unknown.case_gold_source_status == "NO_CASE_GOLD_REQUIREMENTS"


def test_refusals_have_positive_counterpart():
    gold, rank = fixtures()
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold) as gb,
        patch.object(subject.source_bound_ranking, "bind", return_value=rank) as rb,
    ):
        assert call().at_k[-1].complete_requirements
        for invalid in [("duplicate",), ("missing",)]:
            if invalid[0] == "duplicate":
                chunks = (rank.rows[0].chunk_id,) * 2
                with pytest.raises(
                    subject.TextSupportError, match="^source bound text support refused$"
                ):
                    call(chunks=chunks)
            else:
                with pytest.raises(subject.TextSupportError):
                    call("absent")
        gold.bindings = gold.bindings[:-1]
        with pytest.raises(subject.TextSupportError):
            call()
        gold, _ = fixtures()
        gb.return_value = gold
        rb.side_effect = ValueError("secret path")
        with pytest.raises(subject.TextSupportError) as error:
            call()
        assert str(error.value) == "source bound text support refused"
        assert error.value.__cause__ is None


def test_empty_ranking_and_identity_preimage():
    gold, rank = fixtures()
    rank = BoundRanking(
        rank.binding_id,
        rank.snapshot_id,
        rank.catalog_id,
        rank.authority_sha256,
        (),
        0,
        0,
        "NO_SELECTED_SOURCE_VALIDATED",
    )
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold),
        patch.object(subject.source_bound_ranking, "bind", return_value=rank),
    ):
        result = call(chunks=())
    assert all(x.requirement_fraction == 0 and not x.complete_requirements for x in result.at_k)
    assert result.ranking_source_status == "NO_SELECTED_SOURCE_VALIDATED"
    fields = {name: getattr(result, name) for name in list(result.__dataclass_fields__)[1:23]}
    fields["at_k"] = [asdict(x) for x in result.at_k]
    fields.update(schema=1, kind="slaif-source-bound-text-support-v1", cutoffs=(1, 2, 3, 4))
    assert len(fields) == 25
    wire = json.dumps(
        fields, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )
    assert (
        result.evaluation_id
        == "sha256:"
        + hashlib.sha256(b"slaif-source-bound-text-support-v1\n" + wire.encode("ascii")).hexdigest()
    )
    vector = ORACLE["identity_vector"]
    assert len(vector["preimage_object"]) == 25
    assert (
        json.dumps(
            vector["preimage_object"],
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        == vector["canonical_ascii"]
    )
    assert (
        "sha256:"
        + hashlib.sha256(
            vector["domain_ascii"].encode() + vector["canonical_ascii"].encode()
        ).hexdigest()
        == vector["expected_evaluation_id"]
    )


def test_preflight_refuses_before_binders_and_sanitizes():
    gold, rank = fixtures()
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold) as gb,
        patch.object(subject.source_bound_ranking, "bind", return_value=rank) as rb,
    ):
        assert call().at_k[-1].complete_requirements
        gb.reset_mock()
        rb.reset_mock()
        for bad in (True, 0, 30001):
            with pytest.raises(subject.TextSupportError):
                call(deadline_ms=bad)
        with pytest.raises(subject.TextSupportError):
            call(chunks=(rank.rows[0].chunk_id, rank.rows[0].chunk_id))
        gb.assert_not_called()
        rb.assert_not_called()
        gb.side_effect = ValueError("private source content")
        with pytest.raises(subject.TextSupportError) as error:
            call()
        assert str(error.value) == "source bound text support refused"
        rb.assert_not_called()


def test_original_deadline_across_gold_hash_and_constructor():
    gold, rank = fixtures()
    clock = [10.0]
    real_hash = hashlib.sha256
    real_result = subject.TextSupport

    def overrun_gold(*args, **kwargs):
        clock[0] = 11.0
        return gold

    def overrun_hash(value=b""):
        digest = real_hash(value)
        if value != b"slaif-source-bound-text-support-v1\n":
            return digest

        class DelayedHash:
            def update(self, data):
                digest.update(data)

            def hexdigest(self):
                value = digest.hexdigest()
                clock[0] = 11.0
                return value

        return DelayedHash()

    def overrun_constructor(*args, **kwargs):
        result = real_result(*args, **kwargs)
        clock[0] = 11.0
        return result

    with (
        patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]),
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold) as gb,
        patch.object(subject.source_bound_ranking, "bind", return_value=rank) as rb,
    ):
        assert call(deadline_ms=500).at_k[-1].complete_requirements
        gb.side_effect = overrun_gold
        with pytest.raises(subject.TextSupportError):
            call(deadline_ms=500)
        assert rb.call_count == 1
        gb.side_effect = None
        clock[0] = 10.0
        with patch.object(subject.hashlib, "sha256", side_effect=overrun_hash):
            with pytest.raises(subject.TextSupportError):
                call(deadline_ms=500)
        clock[0] = 10.0
        with patch.object(subject, "TextSupport", side_effect=overrun_constructor):
            with pytest.raises(subject.TextSupportError):
                call(deadline_ms=500)


def test_six_field_join_and_gold_identity_refusals():
    from dataclasses import replace

    gold, rank = fixtures()
    original = gold.bindings[0]
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold),
        patch.object(subject.source_bound_ranking, "bind", return_value=rank) as rb,
    ):
        assert call().at_k[-1].complete_requirements
        rb.reset_mock()
        for replacement in (
            replace(original, text_sha256="0" * 64),
            replace(original, start=original.start + 1),
            replace(original, bundle_ids=()),
        ):
            gold.bindings = (replacement,) + gold.bindings[1:]
            with pytest.raises(subject.TextSupportError):
                call()
        gold.bindings = (original,) + gold.bindings[1:]
        gold.dataset_sha256 = "0" * 64
        with pytest.raises(subject.TextSupportError):
            call()
        rb.assert_not_called()


def test_shape_bounds_and_no_raw_values_in_result():
    gold, rank = fixtures()
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold) as gb,
        patch.object(subject.source_bound_ranking, "bind", return_value=rank),
    ):
        result = call()
        assert "Synthetic source support" not in repr(asdict(result))
        assert "/private" not in repr(asdict(result))
        gb.reset_mock()
        for path, cutoff, ids in (
            ("x" * 4097, (1,), ()),
            ("é" * 2049, (1,), ()),
            ("/private", (True,), ()),
            ("/private", (2, 2), ()),
            ("/private", (1,), ("sha256:" + "0" * 63,)),
        ):
            with pytest.raises(subject.TextSupportError):
                subject.score_case(
                    None,
                    None,
                    path,
                    ID,
                    ID,
                    DATA,
                    "case1",
                    (BUNDLE,),
                    ids,
                    grants=None,
                    cutoffs=cutoff,
                )
        gb.assert_not_called()


def test_no_gold_dataset_and_refused_gold_never_scores():
    from slaif_raggedized_helper.text_evaluation_gold_binding import BoundGold

    obj = json.loads(DATA)
    obj["cases"] = obj["cases"][1:]
    data = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    ds = dataset_module.admit(data)
    gold = BoundGold(
        ds.dataset_id,
        ds.split_id,
        hashlib.sha256(data).hexdigest(),
        ID,
        (),
        (),
        ds.case_count,
        0,
        0,
        "NO_GOLD_SOURCE_VALIDATED",
    )
    _, rank = fixtures()
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold) as gb,
        patch.object(subject.source_bound_ranking, "bind", return_value=rank) as rb,
    ):
        result = subject.score_case(
            None,
            None,
            "/private",
            ID,
            ID,
            data,
            "case2",
            (),
            tuple(row.chunk_id for row in rank.rows),
            grants=None,
        )
        assert result.global_gold_source_status == "NO_GOLD_SOURCE_VALIDATED"
        assert result.case_gold_source_status == "NO_CASE_GOLD_REQUIREMENTS"
        assert all(x.requirement_fraction is None for x in result.at_k)
        rb.reset_mock()
        for reason in ("missing bundle", "wrong hash", "invalid unrelated Gold"):
            gb.side_effect = ValueError(reason)
            with pytest.raises(subject.TextSupportError):
                subject.score_case(
                    None,
                    None,
                    "/private",
                    ID,
                    ID,
                    data,
                    "case2",
                    (),
                    tuple(row.chunk_id for row in rank.rows),
                    grants=None,
                )
        rb.assert_not_called()


def test_rank_binding_shape_guard_has_positive_counterpart():
    from dataclasses import replace

    gold, rank = fixtures()
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold),
        patch.object(subject.source_bound_ranking, "bind", return_value=rank) as rb,
    ):
        assert call().at_k[-1].complete_requirements
        for bad in (
            replace(rank, row_count=0),
            replace(rank, catalog_id="sha256:" + "0" * 64),
            replace(rank, fragment_count=rank.fragment_count + 1),
            replace(rank, rows=tuple(reversed(rank.rows))),
        ):
            rb.return_value = bad
            with pytest.raises(subject.TextSupportError):
                call()


def test_stream_limit_refuses_before_oversized_digest_update():
    gold, rank = fixtures()
    encoder = subject.json.JSONEncoder.iterencode
    sha256 = hashlib.sha256
    recorded = []

    def encode(self, obj, *args, **kwargs):
        if isinstance(obj, dict) and obj.get("kind") == "slaif-source-bound-text-support-v1":
            yield "x" * 1048577
        else:
            yield from encoder(self, obj, *args, **kwargs)

    def tracked(value=b""):
        digest = sha256(value)
        if value != b"slaif-source-bound-text-support-v1\n":
            return digest

        class Digest:
            def update(self, value):
                recorded.append(len(value))
                return digest.update(value)

            def hexdigest(self):
                return digest.hexdigest()

        return Digest()

    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold),
        patch.object(subject.source_bound_ranking, "bind", return_value=rank),
    ):
        assert call().at_k[-1].complete_requirements
        with (
            patch.object(subject.json.JSONEncoder, "iterencode", encode),
            patch.object(subject.hashlib, "sha256", side_effect=tracked),
        ):
            with pytest.raises(subject.TextSupportError):
                call()
        assert recorded == []


def test_fixed_markers_are_non_init_and_result_frozen():
    from dataclasses import FrozenInstanceError, fields, replace

    gold, rank = fixtures()
    with (
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold),
        patch.object(subject.source_bound_ranking, "bind", return_value=rank),
    ):
        value = call()
    markers = {f.name for f in fields(value) if not f.init}
    assert markers == {
        "input_origin",
        "source_binding",
        "gold_eligibility",
        "authorization_status",
        "execution_status",
        "temporal_consistency",
        "qualification",
        "formula_version",
    }
    with pytest.raises(FrozenInstanceError):
        value.qualification = "QUALIFIED"
    with pytest.raises((ValueError, TypeError)):
        replace(value, gold_eligibility="CHECKED")


def test_invalid_store_path_refuses_before_dataset_and_binders():
    gold, rank = fixtures()
    chunks = tuple(row.chunk_id for row in rank.rows)
    admission = subject.text_evaluation_dataset.admit
    with (
        patch.object(subject.text_evaluation_dataset, "admit", wraps=admission) as admit,
        patch.object(subject.text_evaluation_gold_binding, "bind", return_value=gold) as gb,
        patch.object(subject.source_bound_ranking, "bind", return_value=rank) as rb,
    ):
        valid = subject.score_case(
            None,
            None,
            "/private/owned",
            ID,
            ID,
            DATA,
            "case1",
            (BUNDLE,),
            chunks,
            grants=None,
            cutoffs=(1, 2, 3, 4),
        )
        assert valid.at_k[-1].complete_requirements
        admit.reset_mock()
        gb.reset_mock()
        rb.reset_mock()
        for invalid in (
            "relative",
            "/",
            "/a//b",
            "/a/./b",
            "/a/../b",
            "/a/",
            "/a/\n/b",
            "/a/\u0085/b",
        ):
            with pytest.raises(subject.TextSupportError):
                subject.score_case(
                    None,
                    None,
                    invalid,
                    ID,
                    ID,
                    DATA,
                    "case1",
                    (BUNDLE,),
                    chunks,
                    grants=None,
                    cutoffs=(1,),
                )
        admit.assert_not_called()
        gb.assert_not_called()
        rb.assert_not_called()
