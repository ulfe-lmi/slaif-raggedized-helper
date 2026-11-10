import hashlib

import pytest
from pydantic import ValidationError

from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper.schema import fingerprint
from slaif_raggedized_helper.source_admission import Revision, Source


def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()


def revision(**changes):
    data = dict(
        logical_id="doc",
        relative_path="a",
        display_uri="urn:x",
        corpus="c",
        access_labels=("private",),
        processing_approved=True,
        redistribution_rights="prohibited",
        media_type="text/plain",
        size=1,
        sha256="a" * 64,
        version="v1",
    )
    data.update(changes)
    source = Source(**data)
    return Revision(
        schema_version=1,
        revision_id=fingerprint(
            {"version": 1, "kind": "source-revision", "source": source.model_dump()}
        ),
        source=source,
        blob=source.sha256,
    )


def fixture():
    rev = revision()
    dep = p.Dependency(
        schema_version=1,
        revision_id=rev.revision_id,
        extraction_id=p.extraction_id("synthetic"),
        definition="synthetic",
    )
    text = "H😀e\u0301\nř"
    block = p.Block(
        schema_version=1,
        block_id="b",
        revision_id=rev.revision_id,
        extraction_id=dep.extraction_id,
        order=0,
        kind="table_header",
        anchor="page 1",
        text=text,
        text_sha256=digest(text),
        origin="native",
    )
    registry = p.Registry((rev,), (dep,), (block,))
    fragment = p.SourceFragment(
        schema_version=1, kind="source", block_id="b", start=1, end=5, copied_text=text[1:5]
    )
    chunk = p.Chunk(
        schema_version=1,
        chunk_id="temporary",
        revision_id=rev.revision_id,
        extraction_id=dep.extraction_id,
        policy_id=p.policy_id("fixture"),
        fragments=(fragment, p.Separator(schema_version=1, kind="separator", text="|"), fragment),
        text=text[1:5] + "|" + text[1:5],
        text_sha256=digest(text[1:5] + "|" + text[1:5]),
        counts=(
            p.TokenCount(
                schema_version=1, availability="unavailable", count=None, provenance="not measured"
            ),
        ),
    )
    chunk = chunk.model_copy(update={"chunk_id": p.chunk_id(chunk)})
    return rev, dep, block, registry, chunk


def test_exact_unicode_and_repeated_header():
    rev, dep, block, registry, chunk = fixture()
    assert registry.bind_chunk(chunk).labels == ("private",)
    assert chunk.text == "😀e\u0301\n|😀e\u0301\n"
    assert registry.bind_chunk(chunk).revision_id == rev.revision_id


@pytest.mark.parametrize(
    "changes",
    [
        dict(start=True),
        dict(start=-1),
        dict(end=100),
        dict(start=2, end=2),
        dict(copied_text="wrong"),
        dict(block_id="missing"),
    ],
)
def test_bad_fragments_fail_without_input(changes):
    _, _, _, registry, chunk = fixture()
    fragment = chunk.fragments[0].model_copy(update=changes)
    bad = chunk.model_copy(update={"fragments": (fragment,)})
    with pytest.raises(p.ProvenanceError, match="^invalid chunk binding$"):
        registry.bind_chunk(bad)


def test_corrupt_references_and_forged_models():
    rev, dep, block, _, chunk = fixture()
    for bad in (
        rev.model_copy(update={"blob": "b" * 64}),
        rev.model_copy(update={"source": rev.source.model_copy(update={"access_labels": None})}),
        rev.model_copy(update={"revision_id": "sha256:" + "0" * 64}),
    ):
        with pytest.raises(p.ProvenanceError):
            p.catalog((bad,))
    for bad in (
        block.model_copy(update={"text": "changed"}),
        block.model_copy(update={"extraction_id": "unknown"}),
    ):
        with pytest.raises(p.ProvenanceError):
            p.Registry((rev,), (dep,), (bad,))
    with pytest.raises(p.ProvenanceError):
        p.Registry((rev,), (dep,), (block, block))
    with pytest.raises(p.ProvenanceError):
        p.Registry((rev,), (dep.model_copy(update={"definition": "changed"}),), (block,))
    with pytest.raises(p.ProvenanceError):
        fixture()[3].bind_chunk(chunk.model_copy(update={"text_sha256": "wrong"}))


def test_counts_and_visual_requirements():
    with pytest.raises(ValidationError):
        p.TokenCount(schema_version=1, availability="available", count=None, provenance="fixture")
    with pytest.raises(ValidationError):
        p.TokenCount(schema_version=1, availability="unavailable", count=0, provenance="fixture")
    rev, dep, block, registry, _ = fixture()
    visual = block.model_copy(update={"origin": "visual_transcription"})
    with pytest.raises(p.ProvenanceError):
        p.Registry((rev,), (dep,), (visual,))
    visual = visual.model_copy(update={"page_ref": "page", "uncertainty": "unreadable"})
    p.Registry((rev,), (dep,), (visual,))
    derived = p.Derived(
        schema_version=1,
        artifact_id="d",
        origin="interpretation",
        target_revision=rev.revision_id,
        support_blocks=("b",),
        text="description",
        page_ref="page",
        uncertainty="uncertain",
    )
    assert registry.bind_derived(derived).labels == ("private",)
    with pytest.raises(p.ProvenanceError):
        registry.bind_derived(derived.model_copy(update={"page_ref": None}))


def test_reader_intersection():
    rev, _, _, registry, chunk = fixture()
    scope = registry.bind_chunk(chunk)
    grant = p.Grants(schema_version=1, corpora=("c",), versions=("v1",), labels=("private",))
    assert p.reader_allows(scope, grant)
    assert not p.reader_allows(scope, None)
    assert not p.reader_allows(scope, grant.model_copy(update={"labels": ()}))
    assert not p.reader_allows(scope, grant, p.Restrictions(schema_version=1, corpora=("other",)))
    assert not p.reader_allows(scope, grant.model_copy(update={"versions": ()}))
