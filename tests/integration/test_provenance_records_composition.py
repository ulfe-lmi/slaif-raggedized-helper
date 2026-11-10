import hashlib
import json

import pytest

from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest


def test_real_store_to_provenance(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    data = "H😀e\u0301\nvrstica".encode()
    (root / "a").write_bytes(data)
    (root / "b").write_bytes(data)
    common = dict(
        display_uri="urn:fixture",
        processing_approved=True,
        media_type="text/plain",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        version="1",
    )
    a = dict(
        common,
        logical_id="a",
        relative_path="a",
        corpus="public",
        access_labels=[],
        redistribution_rights="allowed",
    )
    b = dict(
        common,
        logical_id="b",
        relative_path="b",
        corpus="private",
        access_labels=["secret"],
        redistribution_rights="prohibited",
    )

    def parse(values):
        return parse_manifest(json.dumps(dict(schema_version=1, sources=values)).encode()).sources

    store = OriginalStore(tmp_path / "store")
    try:
        first, second = (store.admit(root, s) for s in parse([a, b]))
        third = store.admit(root, parse([dict(a, title="new")])[0])
        assert len(list((tmp_path / "store" / "blobs").iterdir())) == 1
        assert len({first.revision_id, second.revision_id, third.revision_id}) == 3
        revisions = tuple(store.inspect(r.revision_id) for r in (first, second, third))
        scopes = p.catalog(revisions)
        assert scopes[0].labels == () and scopes[1].labels == ("secret",)
        assert (
            scopes[0].redistribution_rights == "allowed"
            and scopes[1].redistribution_rights == "prohibited"
        )
        deps = tuple(
            p.Dependency(
                schema_version=1,
                revision_id=r.revision_id,
                extraction_id=p.extraction_id("fixture"),
                definition="fixture",
            )
            for r in revisions
        )
        text = data.decode()
        blocks = tuple(
            p.Block(
                schema_version=1,
                block_id=f"b{i}",
                revision_id=r.revision_id,
                extraction_id=deps[i].extraction_id,
                order=0,
                kind="table_header",
                anchor="1",
                text=text,
                text_sha256=hashlib.sha256(data).hexdigest(),
                origin="native",
            )
            for i, r in enumerate(revisions)
        )
        registry = p.Registry(revisions, deps, blocks)
        fragments = (
            p.SourceFragment(
                schema_version=1, kind="source", block_id="b0", start=0, end=4, copied_text=text[:4]
            ),
            p.Separator(schema_version=1, kind="separator", text="\n"),
            p.SourceFragment(
                schema_version=1,
                kind="source",
                block_id="b0",
                start=5,
                end=len(text),
                copied_text=text[5:],
            ),
        )
        reconstructed = text[:4] + "\n" + text[5:]
        chunk = p.Chunk(
            schema_version=1,
            chunk_id="temp",
            revision_id=first.revision_id,
            extraction_id=deps[0].extraction_id,
            policy_id=p.policy_id("fixture"),
            fragments=fragments,
            text=reconstructed,
            text_sha256=hashlib.sha256(reconstructed.encode()).hexdigest(),
        )
        chunk = chunk.model_copy(update={"chunk_id": p.chunk_id(chunk)})
        chunk = p.admit_record("Chunk", chunk.model_dump_json().encode())
        assert registry.bind_chunk(chunk) == scopes[0]
        tail_fragment = p.SourceFragment(
            schema_version=1,
            kind="source",
            block_id="b0",
            start=5,
            end=len(text),
            copied_text=text[5:],
        )
        tail = chunk.model_copy(
            update={
                "fragments": (tail_fragment,),
                "text": text[5:],
                "text_sha256": hashlib.sha256(text[5:].encode()).hexdigest(),
            }
        )
        tail = tail.model_copy(update={"chunk_id": p.chunk_id(tail)})
        links = p.admit_record(
            "Neighbors",
            {
                "schema_version": 1,
                "chunk_id": chunk.chunk_id,
                "previous_chunk_id": None,
                "next_chunk_id": tail.chunk_id,
            },
        )
        assert registry.bind_neighbors((chunk, tail), (links,)) == (links,)
        grant = p.Grants(schema_version=1, corpora=("public",), versions=("1",), labels=())
        assert p.reader_allows(scopes[0], grant) and not p.reader_allows(scopes[1], grant)
        derived = p.Derived(
            schema_version=1,
            artifact_id="context",
            origin="context",
            target_revision=first.revision_id,
            support_blocks=("b0",),
            text="fixture",
        )
        assert registry.bind_derived(derived) == scopes[0]
        for support in ("b1", "b2", "missing"):
            with pytest.raises(p.ProvenanceError):
                registry.bind_derived(derived.model_copy(update={"support_blocks": (support,)}))
    finally:
        store.close()
