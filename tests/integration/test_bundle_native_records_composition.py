import json
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
from test_native_tokenizers import make_native  # noqa: E402
from test_structured_text_composition import create_store  # noqa: E402
from slaif_raggedized_helper import bundle_native_records as b, chunking  # noqa: E402
from slaif_raggedized_helper import native_chunking as nc, provenance_jsonl as jl  # noqa: E402
from slaif_raggedized_helper import provenance_records as p, structured_text as s  # noqa: E402


def test_actual_native_roundtrip_and_mutations(tmp_path, monkeypatch):
    paths, runtime, make = make_native(tmp_path)
    defs = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    text = "# Guide Ž😀\r\n\r\nhello café 世界\r\n\r\nWARNING: check units.\r\n"
    store, revisions = create_store(tmp_path, text)
    try:
        item = s.extract(store, revisions[0].revision_id)
        registry = p.Registry((revisions[0],), (item.dependency,), item.blocks)
        policy = chunking.Policy(pair_max=1280)
        query = "hello"
        result = nc.build(registry, item.blocks, *defs, runtime, query, policy)
        declarations = [
            dict(
                role=d.role,
                artifact_sha256=d.sha256,
                backend_version=d.backend_version,
                model_revision=d.model_revision,
                preprocessing=d.preprocessing,
            )
            for d in defs
        ]
        definition = nc._json(
            dict(
                version=1,
                kind="observed-local-native",
                policy=asdict(policy),
                definitions=[nc._identity(d) for d in defs],
                query_input_sha256=nc._input_digest(query, None),
                serialization=nc._SERIALIZATION,
            )
        ).decode()
        header = dict(
            policy=asdict(policy),
            query=query,
            definitions=declarations,
            policy_definition=definition,
            policy_id=p.policy_id(definition),
        )
        raw_header = nc._json(header)
        raw_chunks = jl.encode("Chunk", tuple(c.model_dump_json().encode() for c in result.chunks))
        raw_receipts = result.receipts_json()
        valid = b.validate(raw_header, raw_chunks, raw_receipts, len(result.chunks))
        assert valid.chunks == result.chunks
        with monkeypatch.context() as patch:
            ticks = iter((0, 31))
            patch.setattr(b.time, "monotonic", lambda: next(ticks))
            with pytest.raises(b.BundleRecordsError):
                b.validate(raw_header, raw_chunks, raw_receipts, len(result.chunks))
        assert (
            b.validate(
                valid.header_json, valid.chunks_jsonl, valid.receipts_json, len(result.chunks)
            )
            == valid
        )
        assert (tmp_path / "root" / "a").read_bytes() == text.encode()
        for field, value in (
            ("chunk_id", "sha256:" + "0" * 64),
            ("text_sha256", "0" * 64),
            ("text", "forged"),
            ("policy_id", "sha256:" + "0" * 64),
            ("counts", []),
        ):
            obj = json.loads(result.chunks[0].model_dump_json())
            obj[field] = value
            altered = (
                nc._json(obj)
                + b"\n"
                + b"".join(
                    nc._json(json.loads(c.model_dump_json())) + b"\n" for c in result.chunks[1:]
                )
            )
            with pytest.raises(b.BundleRecordsError):
                b.validate(raw_header, altered, raw_receipts, len(result.chunks))
        for mutate in ("query", "policy", "definition", "receipt", "count", "order", "sha"):
            h = json.loads(raw_header)
            r = json.loads(raw_receipts)
            if mutate == "query":
                h["query"] += "!"
            if mutate == "policy":
                h["policy"]["target"] = True
            if mutate == "definition":
                h["definitions"][0]["role"] = "reranker_pair"
            if mutate == "receipt":
                r["receipts"].pop()
            if mutate == "count":
                r["receipts"][0]["count"]["count"] = True
            if mutate == "order":
                r["receipts"][0], r["receipts"][1] = r["receipts"][1], r["receipts"][0]
            if mutate == "sha":
                r["receipts"][0]["count"]["input_sha256"] = "0" * 64
            with pytest.raises(b.BundleRecordsError):
                b.validate(nc._json(h), raw_chunks, nc._json(r), len(result.chunks))
    finally:
        store.close()
