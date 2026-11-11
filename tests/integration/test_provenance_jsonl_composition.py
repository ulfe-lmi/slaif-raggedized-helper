import hashlib

from slaif_raggedized_helper import provenance_jsonl as j
from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper.source_admission import OriginalStore, Source


def test_owned_store_to_jsonl_and_registry(tmp_path):
    text = "A😀e\u0301\r\nB\u2028C\u2029"
    raw = text.encode()
    root = tmp_path / "input"
    root.mkdir()
    for name in ("a", "b"):
        (root / name).write_bytes(raw)
    common = dict(
        display_uri="urn:fixture",
        processing_approved=True,
        media_type="text/plain",
        size=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
        version="1",
    )
    store = OriginalStore(tmp_path / "store")
    try:
        revisions = tuple(
            store.admit(
                root,
                Source(
                    logical_id=name,
                    relative_path=name,
                    corpus=name,
                    access_labels=(),
                    redistribution_rights="allowed",
                    **common,
                ),
            )
            for name in ("a", "b")
        )
        assert revisions[0].blob == revisions[1].blob
        assert revisions[0].revision_id != revisions[1].revision_id
        assert all(store.read_original(r.revision_id) == raw for r in revisions)
        deps = tuple(
            p.Dependency(
                schema_version=1,
                revision_id=r.revision_id,
                extraction_id=p.extraction_id("fixture"),
                definition="fixture",
            )
            for r in revisions
        )
        blocks = tuple(
            p.Block(
                schema_version=1,
                block_id=str(i),
                revision_id=r.revision_id,
                extraction_id=deps[i].extraction_id,
                order=0,
                kind="text",
                anchor="a",
                text=text,
                text_sha256=hashlib.sha256(raw).hexdigest(),
                origin="native",
            )
            for i, r in enumerate(revisions)
        )
        fragments = (
            p.SourceFragment(
                schema_version=1, kind="source", block_id="0", start=0, end=5, copied_text=text[:5]
            ),
            p.Separator(schema_version=1, kind="separator", text="\r\n"),
            p.SourceFragment(
                schema_version=1,
                kind="source",
                block_id="0",
                start=5,
                end=len(text),
                copied_text=text[5:],
            ),
        )
        assembled = text[:5] + "\r\n" + text[5:]
        chunk = p.Chunk(
            schema_version=1,
            chunk_id="temp",
            revision_id=revisions[0].revision_id,
            extraction_id=deps[0].extraction_id,
            policy_id=p.policy_id("fixture"),
            fragments=fragments,
            text=assembled,
            text_sha256=hashlib.sha256(assembled.encode()).hexdigest(),
            counts=(
                p.TokenCount(
                    schema_version=1, availability="available", count=0, provenance="fixture"
                ),
                p.TokenCount(
                    schema_version=1, availability="unavailable", count=None, provenance="fixture"
                ),
            ),
        )
        chunk = chunk.model_copy(update={"chunk_id": p.chunk_id(chunk)})
        links = (
            p.Neighbors(
                schema_version=1,
                chunk_id=chunk.chunk_id,
                previous_chunk_id=None,
                next_chunk_id=None,
            ),
        )

        def roundtrip(kind, records):
            data = j.encode(kind, tuple(r.model_dump_json().encode() for r in records))
            result = j.decode(kind, data, hashlib.sha256(data).hexdigest(), len(records))
            assert result == records
            return result

        deps = roundtrip("Dependency", deps)
        blocks = roundtrip("Block", blocks)
        chunks = roundtrip("Chunk", (chunk,))
        links = roundtrip("Neighbors", links)
        registry = p.Registry(revisions, deps, blocks)
        assert registry.bind_chunk(chunks[0]) == p.catalog(revisions)[0]
        assert registry.bind_neighbors(chunks, links) == links
    finally:
        store.close()
