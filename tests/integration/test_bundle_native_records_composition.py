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


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("bundle_matrix")
    paths, runtime, make = make_native(tmp_path)
    defs = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    text = "# Guide Ž😀\r\n\r\nhello café 世界\r\n\r\nWARNING: check units.\r\n"
    store, revisions = create_store(tmp_path, text)
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
    store.close()
    return raw_header, raw_chunks, raw_receipts, len(result.chunks)


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


@pytest.mark.parametrize(
    "case",
    [
        "header_missing",
        "header_extra",
        "header_type",
        "policy_missing",
        "policy_extra",
        "policy_type",
        "policy_bound",
        "query_type",
        "query_long",
        "query_surrogate",
        "role",
        "backend",
        "hash",
        "revision_empty",
        "revision_long",
        "preproc_empty",
        "preproc_long",
        "definition",
        "pid",
        "query_mismatch",
        "outer_version",
        "outer_type",
        "outer_missing",
        "outer_extra",
        "receipt_missing",
        "receipt_extra",
        "receipt_duplicate",
        "receipt_reordered",
        "receipt_field_missing",
        "receipt_field_extra",
    ]
    + [
        "count_" + x
        for x in (
            "count",
            "artifact_sha256",
            "backend_version",
            "role",
            "model_revision",
            "preprocessing",
            "input_sha256",
            "mode",
            "serialization",
        )
    ],
)
def test_malformed_matrix(bundle, case):
    header, chunks, receipts, size = bundle
    h, r = json.loads(header), json.loads(receipts)
    if case == "header_missing":
        del h["query"]
    elif case == "header_extra":
        h["extra"] = 1
    elif case == "header_type":
        h = []
    elif case == "policy_missing":
        h["policy"].pop(next(iter(h["policy"])))
    elif case == "policy_extra":
        h["policy"]["extra"] = 1
    elif case == "policy_type":
        h["policy"]["target"] = True
    elif case == "policy_bound":
        h["policy"]["target"] = -1
    elif case == "query_type":
        h["query"] = 1
    elif case == "query_long":
        h["query"] = "x" * 10001
    elif case == "query_surrogate":
        h["query"] = "\ud800"
    elif case == "role":
        h["definitions"][0]["role"] = "wrong"
    elif case == "backend":
        h["definitions"][0]["backend_version"] = "wrong"
    elif case == "hash":
        h["definitions"][0]["artifact_sha256"] = "A" * 64
    elif case.startswith("revision_"):
        h["definitions"][0]["model_revision"] = "" if case.endswith("empty") else "x" * 257
    elif case.startswith("preproc_"):
        h["definitions"][0]["preprocessing"] = "" if case.endswith("empty") else "x" * 257
    elif case == "definition":
        h["policy_definition"] += "x"
    elif case == "pid":
        h["policy_id"] += "x"
    elif case == "query_mismatch":
        h["query"] += "x"
    elif case == "outer_version":
        r["version"] = 2
    elif case == "outer_type":
        r["version"] = True
    elif case == "outer_missing":
        del r["receipts"]
    elif case == "outer_extra":
        r["extra"] = 1
    elif case == "receipt_missing":
        r["receipts"].pop()
    elif case == "receipt_extra":
        r["receipts"].append(r["receipts"][0])
    elif case == "receipt_duplicate":
        r["receipts"][1] = r["receipts"][0]
    elif case == "receipt_reordered":
        r["receipts"][0], r["receipts"][1] = r["receipts"][1], r["receipts"][0]
    elif case == "receipt_field_missing":
        del r["receipts"][0]["chunk_id"]
    elif case == "receipt_field_extra":
        r["receipts"][0]["extra"] = 1
    elif case.startswith("count_"):
        key = case[6:]
        r["receipts"][0]["count"][key] = True if key == "count" else 1
    with pytest.raises(b.BundleRecordsError, match="^native bundle records refused$"):
        b.validate(json.dumps(h, ensure_ascii=True).encode(), chunks, _encoded(r), size)


@pytest.mark.parametrize("count", [0, 4097, True])
def test_bad_expected_count_before_parse(bundle, monkeypatch, count):
    called = []
    monkeypatch.setattr(b, "_parse", lambda *args: called.append(True))
    with pytest.raises(b.BundleRecordsError):
        b.validate(*bundle[:3], count)
    assert not called


@pytest.mark.parametrize(
    "field,value",
    [
        ("chunk_id", "sha256:" + "0" * 64),
        ("text_sha256", "0" * 64),
        ("text", "forged"),
        ("policy_id", "sha256:" + "0" * 64),
        ("counts", []),
    ],
)
def test_chunk_rejection_matrix(bundle, field, value):
    header, chunks, receipts, size = bundle
    records = [json.loads(line) for line in chunks.splitlines()]
    records[0][field] = value
    altered = b"".join(_encoded(record) + b"\n" for record in records)
    with pytest.raises(b.BundleRecordsError, match="^native bundle records refused$"):
        b.validate(header, altered, receipts, size)


@pytest.mark.parametrize("field", ["header", "receipts", "chunks"])
def test_raw_caps_exact_and_over(bundle, monkeypatch, field):
    header, chunks, receipts, size = bundle
    valid = b.validate(header, chunks, receipts, size)
    # Canonical output must also fit the same instrumented cap.
    raw = {"header": header, "receipts": receipts, "chunks": chunks}[field]
    output = {
        "header": valid.header_json,
        "receipts": valid.receipts_json,
        "chunks": valid.chunks_jsonl,
    }[field]
    cap = max(len(raw), len(output))
    if field == "chunks":
        monkeypatch.setattr(b.jl, "MAX_BYTES", cap)
    else:
        monkeypatch.setattr(b, "HEADER_BYTES" if field == "header" else "RECEIPTS_BYTES", cap)
    b.validate(header, chunks, receipts, size)
    padded = raw + (b" " * (cap + 1 - len(raw)))
    args = {
        "header": [padded, chunks, receipts],
        "receipts": [header, chunks, padded],
        "chunks": [header, padded, receipts],
    }[field]
    with pytest.raises(b.BundleRecordsError):
        b.validate(*args, size)


def test_final_deadline(bundle, monkeypatch):
    from types import SimpleNamespace

    calls = []

    def clock():
        calls.append(1)
        return 0

    monkeypatch.setattr(b, "time", SimpleNamespace(monotonic=clock))
    b.validate(*bundle)
    total = len(calls)
    calls.clear()

    def deadline():
        calls.append(1)
        return 31 if len(calls) == total else 0

    monkeypatch.setattr(b, "time", SimpleNamespace(monotonic=deadline))
    with pytest.raises(b.BundleRecordsError):
        b.validate(*bundle)
    assert len(calls) == total


def test_aggregate_work_exact_and_over(bundle, monkeypatch):
    header, chunks, receipts, size = bundle
    valid = b.validate(*bundle)
    query = json.loads(header)["query"]
    pairs = []
    for chunk in valid.chunks:
        rep = "".join(chunk.heading_path) + chunk.text
        pairs.extend([(chunk.text, None), (rep, None), (query, rep)])
    chars = sum(len(a) + (len(z) if z is not None else 0) for a, z in pairs)
    serialized = sum(
        len(json.dumps([a, z], ensure_ascii=True, separators=(",", ":")).encode()) for a, z in pairs
    )
    # The same aggregate ceiling applies independently to both measures.
    limit = max(chars, serialized)
    monkeypatch.setattr(b, "MAX_WORK", limit)
    b.validate(header, chunks, receipts, size)
    monkeypatch.setattr(b, "MAX_WORK", limit - 1)
    with pytest.raises(b.BundleRecordsError):
        b.validate(header, chunks, receipts, size)


@pytest.mark.parametrize(
    "key",
    [
        "count",
        "artifact_sha256",
        "backend_version",
        "role",
        "model_revision",
        "preprocessing",
        "input_sha256",
        "mode",
        "serialization",
    ],
)
def test_count_wrong_values(bundle, key):
    header, chunks, receipts, size = bundle
    doc = json.loads(receipts)
    count = doc["receipts"][0]["count"]
    count[key] = count[key] + 1 if key == "count" else count[key] + "x"
    with pytest.raises(b.BundleRecordsError, match="^native bundle records refused$"):
        b.validate(header, chunks, _encoded(doc), size)


@pytest.mark.parametrize(
    "case", ["fragment_length", "fragment_concat", "provenance", "unavailable", "budget"]
)
def test_rebound_chunk_semantics(bundle, case):
    header, chunks, receipts, size = bundle
    records = [json.loads(line) for line in chunks.splitlines()]
    item = records[0]
    fragment = next(f for f in item["fragments"] if f["kind"] == "source")
    if case == "fragment_length":
        fragment["end"] += 1
    elif case == "fragment_concat":
        fragment["copied_text"] = "x" * len(fragment["copied_text"])
    elif case == "provenance":
        item["counts"][0]["provenance"] += "x"
    elif case == "unavailable":
        item["counts"][0].update(availability="unavailable", count=None)
    else:
        item["counts"][0]["count"] = json.loads(header)["policy"]["soft_max"] + 1
    item["chunk_id"] = p.chunk_id(p.admit_record("Chunk", _encoded(item)))
    doc = json.loads(receipts)
    for receipt in doc["receipts"][:3]:
        receipt["chunk_id"] = item["chunk_id"]
    if case == "budget":
        doc["receipts"][0]["count"]["count"] = item["counts"][0]["count"]
    altered = b"".join(_encoded(record) + b"\n" for record in records)
    with pytest.raises(b.BundleRecordsError, match="^native bundle records refused$"):
        b.validate(header, altered, _encoded(doc), size)
