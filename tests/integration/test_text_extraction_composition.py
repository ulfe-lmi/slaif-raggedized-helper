import hashlib
import json
import os

import pytest

from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import text_extraction as t
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest


def test_owned_store_provenance_exact_and_scopes(tmp_path):
    text = (
        "# Navodila / Guide 😀\r\n\r\nWARNING: ne izklopi e\u0301\r\n"
        "| Name | Unit |\n| --- | --- |\n| Name | Unit |\n"
        "- list --flag\n```sh\n$ command --flag\n```\n"
        "[do not fetch](https://example.invalid/private) <script>ignore instructions</script>\n"
        "~~~unclosed\n## literal\n"
    )
    raw = text.encode()
    root = tmp_path / "input"
    root.mkdir()
    (root / "a").write_bytes(raw)
    (root / "b").write_bytes(raw)
    common = dict(
        display_uri="https://example.invalid/no-fetch",
        processing_approved=True,
        media_type="text/markdown",
        size=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
        version="1",
    )
    a = dict(
        common,
        logical_id="a",
        relative_path="a",
        corpus="one",
        access_labels=[],
        redistribution_rights="allowed",
    )
    b = dict(
        common,
        logical_id="b",
        relative_path="b",
        corpus="two",
        access_labels=["private"],
        redistribution_rights="prohibited",
    )

    def parse(items):
        return parse_manifest(json.dumps(dict(schema_version=1, sources=items)).encode()).sources

    store = OriginalStore(tmp_path / "store")
    try:
        revisions = [store.admit(root, x) for x in parse([a, b, dict(a, title="new")])]
        results = [t.extract(store, rev.revision_id) for rev in revisions]
        assert len({x.revision.revision_id for x in results}) == 3
        assert all("".join(block.text for block in x.blocks) == text for x in results)
        assert len(list((tmp_path / "store" / "blobs").iterdir())) == 1
        assert results[0].scope.labels == () and results[1].scope.labels == ("private",)
        assert results[1].scope.corpus == "two"
        assert results[1].scope.redistribution_rights == "prohibited"
        registry = p.Registry(
            tuple(x.revision for x in results),
            tuple(x.dependency for x in results),
            tuple(b for x in results for b in x.blocks),
        )
        first = results[0].blocks[0]
        fragment = p.SourceFragment(
            schema_version=1,
            kind="source",
            block_id=first.block_id,
            start=0,
            end=len(first.text),
            copied_text=first.text,
        )
        chunk = p.Chunk(
            schema_version=1,
            chunk_id="temp",
            revision_id=first.revision_id,
            extraction_id=first.extraction_id,
            policy_id=p.policy_id("fixture"),
            fragments=(fragment,),
            text=first.text,
            text_sha256=first.text_sha256,
        )
        chunk = chunk.model_copy(update={"chunk_id": p.chunk_id(chunk)})
        assert registry.bind_chunk(chunk) == results[0].scope
        assert sum(b.text == "| Name | Unit |\n" for b in results[0].blocks) == 2
        assert results[0].blocks[-1].kind == "code"
    finally:
        store.close()


def test_read_race_refused_without_partial(tmp_path, monkeypatch):
    root = tmp_path / "input"
    root.mkdir()
    (root / "a").write_bytes(b"hello")
    source = dict(
        logical_id="a",
        relative_path="a",
        display_uri="urn:x",
        corpus="c",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="unknown",
        media_type="text/plain",
        size=5,
        sha256=hashlib.sha256(b"hello").hexdigest(),
    )
    store = OriginalStore(tmp_path / "store")
    try:
        rev = store.admit(
            root,
            parse_manifest(json.dumps({"schema_version": 1, "sources": [source]}).encode()).sources[
                0
            ],
        )
        blob = tmp_path / "store" / "blobs" / rev.blob
        actual = os.read
        hits = 0

        def mutate(fd, count):
            nonlocal hits
            data = actual(fd, count)
            if os.fstat(fd).st_ino == blob.stat().st_ino and data:
                hits += 1
                if hits == 2:  # extract's second verified read, after inspect
                    blob.write_bytes(b"HELLO")
            return data

        monkeypatch.setattr(os, "read", mutate)
        with pytest.raises(t.ExtractionError, match="^extraction refused$"):
            t.extract(store, rev.revision_id)
        assert hits == 2
    finally:
        store.close()
