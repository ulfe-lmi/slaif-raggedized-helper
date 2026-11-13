"""Portable synthetic original-source support composition; no model execution."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import ingestion_store, provenance_records
from slaif_raggedized_helper import raw_snapshot_catalog, raw_snapshot_rows
from slaif_raggedized_helper import source_bound_ranking, source_bound_text_support
from slaif_raggedized_helper import text_evaluation_dataset, text_evaluation_gold_binding
from slaif_raggedized_helper import tokenizer_session
import test_retrieval_representation_composition as representation_fixture
import test_native_tokenizers  # noqa: E402
import test_raw_hybrid_search_composition as source_fixture
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401


def wire(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
        "ascii"
    )


@dataclass
class OwnedSupport:
    originals: object
    derived: object
    root: str
    snapshot_id: str
    catalog_id: str
    dataset: bytes
    case_id: str
    gold_bundle_ids: tuple
    chunk_ids: tuple
    grants: object
    denied_grants: object


def make_owned_support(tmp_path):
    """Return borrowed stores and source-derived IDs; caller must close both stores."""
    originals, derived, root, snapshot_id = source_fixture.make_sources(
        tmp_path, three=True, paired=False
    )
    try:
        catalog = raw_snapshot_catalog.load_catalog(originals, derived, str(root), snapshot_id)
        mapping = raw_snapshot_rows.parse(catalog.row_map_bytes)
        by_source = {}
        for row in mapping.rows:
            bundle = ingestion_store.load(originals, derived, row.bundle_container_id)
            chunk = next(c for c in bundle.chunks if c.chunk_id == row.chunk_id)
            blocks = {b.block_id: b for b in bundle.blocks}
            fragment = next(
                f for f in chunk.fragments if getattr(f, "copied_text", "").find("alpha beta") >= 0
            )
            block = blocks[fragment.block_id]
            start = block.text.index("alpha beta", fragment.start, fragment.end)
            end = start + len("alpha beta")
            assert block.text[start:end] == "alpha beta"
            assert fragment.start <= start < end <= fragment.end
            atom = dict(
                revision_id=row.revision_id,
                extraction_id=row.extraction_id,
                block_id=block.block_id,
                start=start,
                end=end,
                text_sha256=hashlib.sha256(block.text[start:end].encode("utf-8")).hexdigest(),
            )
            by_source[bundle.revision.source.logical_id] = (row, atom)
        assert set(by_source) == {"a", "b", "c"}
        a, b, c = (by_source[x] for x in ("a", "b", "c"))

        def requirement(name, atom):
            return dict(requirement_id=name, grade=1, alternatives=[[atom]])

        common = dict(
            split="tuning",
            origin="synthetic",
            authorship_ref="owned-synthetic",
            rights_ref="synthetic-no-real-data",
            split_review_ref="structural-only",
            language="en",
            modality="text",
            product="fixture",
            version="v1",
            scope=dict(corpora=["one"], versions=["v1"], labels=[]),
            answerability="answerable",
            acceptable_facts=["Synthetic alpha beta."],
            disallowed_claims=[],
        )
        case = dict(
            common,
            case_id="chosen",
            family_id="chosen",
            question="What is the synthetic text?",
            requirements=[requirement("first", a[1]), requirement("second", c[1])],
        )
        other_atom = dict(
            c[1], start=c[1]["start"] + 6, text_sha256=hashlib.sha256(b"beta").hexdigest()
        )
        assert other_atom["end"] - other_atom["start"] == 4
        other = dict(
            common,
            case_id="other",
            family_id="other",
            question="What is another synthetic text?",
            requirements=[requirement("third", other_atom)],
        )
        dataset = wire(
            dict(
                schema=1,
                kind="slaif-text-evaluation-dataset-v1",
                namespace="owned-support-ci",
                split_policy_ref="synthetic-only",
                cases=[case, other],
            )
        )
        text_evaluation_dataset.admit(dataset)
        grants = provenance_records.Grants(
            schema_version=1, corpora=("one", "two"), versions=("v1",), labels=("secret",)
        )
        denied = provenance_records.Grants(
            schema_version=1, corpora=("one",), versions=("v1",), labels=()
        )
        return OwnedSupport(
            originals,
            derived,
            str(root),
            snapshot_id,
            catalog.catalog_id,
            dataset,
            "chosen",
            tuple(sorted({a[0].bundle_container_id, c[0].bundle_container_id})),
            (a[0].chunk_id, c[0].chunk_id, b[0].chunk_id),
            grants,
            denied,
        )
    except BaseException as failure:
        source_fixture.close_owned_stores(derived, originals, failure)
        raise


class ResourceCeilingExceeded(BaseException):
    """Stop the proof before an over-budget delegated call."""


@pytest.fixture
def owned_support(tmp_path, monkeypatch):
    counts = {"generator": 0, "session_init": 0, "session_count": 0,
              "session_close": 0, "catalog": 0, "bundle_load": 0}

    ceilings = {"generator": 1, "session_init": 6, "session_count": 98304,
                "session_close": 64, "catalog": 32, "bundle_load": 512}

    def track(obj, attribute, key):
        actual = getattr(obj, attribute)

        def measured(*args, **kwargs):
            counts[key] += 1
            if counts[key] > ceilings[key]:
                raise ResourceCeilingExceeded(key)
            return actual(*args, **kwargs)

        monkeypatch.setattr(obj, attribute, measured)

    track(test_native_tokenizers, "make_native", "generator")
    track(tokenizer_session.Session, "__init__", "session_init")
    track(tokenizer_session.Session, "count", "session_count")
    track(tokenizer_session.Session, "close", "session_close")
    track(raw_snapshot_catalog, "load_catalog", "catalog")
    track(ingestion_store, "load", "bundle_load")
    context = None
    try:
        context = make_owned_support(tmp_path)
        yield context
    finally:
        import sys

        if context is not None:
            source_fixture.close_owned_stores(context.derived, context.originals, sys.exception())
        print(
            "SOURCE_SUPPORT_COUNTS",
            json.dumps({"calls": counts, "ceilings": ceilings}, sort_keys=True),
            flush=True,
        )


def test_source_support_composition(owned_support, monkeypatch):
    ctx = owned_support
    checkout = Path(__file__).resolve().parents[2]
    for module in (
        source_fixture,
        representation_fixture,
        test_native_tokenizers,
        source_bound_ranking,
        source_bound_text_support,
        text_evaluation_gold_binding,
        text_evaluation_dataset,
    ):
        assert Path(module.__file__).resolve().is_relative_to(checkout)
    calls = {"gold": 0, "rank": 0, "score": 0}
    for name, module in (("gold", text_evaluation_gold_binding), ("rank", source_bound_ranking)):
        actual = module.bind

        def counted(*args, _name=name, _actual=actual, **kwargs):
            calls[_name] += 1
            return _actual(*args, **kwargs)

        monkeypatch.setattr(module, "bind", counted)
    actual_score = source_bound_text_support.score_case

    def counted_score(*args, **kwargs):
        calls["score"] += 1
        return actual_score(*args, **kwargs)

    monkeypatch.setattr(source_bound_text_support, "score_case", counted_score)
    gold = text_evaluation_gold_binding.bind(
        ctx.originals, ctx.derived, ctx.dataset, ctx.gold_bundle_ids
    )
    assert (gold.gold_atom_occurrences, gold.distinct_atom_count) == (3, 3)
    assert gold.source_binding_status == "ORIGINALS_REVALIDATED_AT_BIND_TIME"

    def score(
        data=ctx.dataset,
        case=ctx.case_id,
        ids=ctx.chunk_ids[:1],
        grants=ctx.denied_grants,
        bundles=ctx.gold_bundle_ids,
    ):
        return source_bound_text_support.score_case(
            ctx.originals,
            ctx.derived,
            ctx.root,
            ctx.snapshot_id,
            ctx.catalog_id,
            data,
            case,
            bundles,
            ids,
            grants=grants,
        )

    bound = source_bound_ranking.bind(
        ctx.originals,
        ctx.derived,
        ctx.root,
        ctx.snapshot_id,
        ctx.catalog_id,
        ctx.chunk_ids[:2],
        grants=ctx.denied_grants,
    )
    assert tuple(row.chunk_id for row in bound.rows) == ctx.chunk_ids[:2]
    value = score()
    assert (
        value.case_requirement_count,
        value.case_gold_atom_occurrences,
        value.global_gold_atom_occurrences,
        value.global_distinct_gold_atoms,
    ) == (2, 2, 3, 3)
    assert value.global_gold_source_status == "ORIGINALS_REVALIDATED_AT_BIND_TIME"
    assert value.ranking_source_status == "ORIGINALS_REVALIDATED_AT_BIND_TIME"
    assert all(
        x.requirement_fraction == 0.5 and x.covered_requirement_ids == ("first",)
        for x in value.at_k
    )
    assert tuple(x.k for x in value.at_k) == (20, 60)
    full = score(ids=ctx.chunk_ids[:2])
    assert all(x.requirement_fraction == 1 and x.complete_requirements for x in full.at_k)
    empty = score(ids=())
    assert (
        empty.case_requirement_count == 2
        and empty.ranking_source_status == "NO_SELECTED_SOURCE_VALIDATED"
    )
    assert all(x.requirement_fraction == 0 and not x.complete_requirements for x in empty.at_k)
    with pytest.raises(source_bound_text_support.TextSupportError):
        score(ids=ctx.chunk_ids, grants=ctx.denied_grants)
    with pytest.raises(source_bound_text_support.TextSupportError):
        score(case="missing")
    changed = json.loads(ctx.dataset)
    changed["cases"][1]["requirements"][0]["alternatives"][0][0]["text_sha256"] = "0" * 64
    with pytest.raises(source_bound_text_support.TextSupportError):
        score(data=wire(changed))
    with pytest.raises(source_bound_text_support.TextSupportError):
        score(bundles=ctx.gold_bundle_ids[:1])
    assert score().at_k[0].requirement_fraction == 0.5
    assert calls == {"gold": 8, "rank": 6, "score": 8}
