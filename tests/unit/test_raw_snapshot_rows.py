import builtins
import dataclasses
import hashlib
import json

import pytest

from slaif_raggedized_helper import raw_snapshot_rows as codec
from slaif_raggedized_helper.embedding_vectors import POLICY_ID
from test_raw_snapshot_manifest import record


def h(n):
    return f"{n:064x}"


def enc(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def row(n, part=1, batch=None):
    return dict(
        ordinal=n,
        partition_id="sha256:" + h(part),
        partition_row=n,
        chunk_id="sha256:" + h(n + 10),
        revision_id="sha256:" + h(30),
        extraction_id="sha256:" + h(31),
        representation_id=h(n + 40),
        rendered_sha256=h(50),
        source_scope_sha256=h(51),
        input_sha256=h(52),
        token_count=2,
        bundle_container_id=h(53),
        bundle_metadata_sha256=h(54),
        batch_container_id=h(batch or 55),
        batch_metadata_sha256=h(56),
        batch_row=n,
        execution_fingerprint=h(57),
    )


def mapping(rows=()):
    return dict(
        schema=1,
        kind="slaif-raw-row-map-v1",
        space_id="a" * 64,
        definition_fingerprint="sha256:" + "a" * 64,
        representation_policy_fingerprint="a" * 64,
        chunk_policy_fingerprint="a" * 64,
        normalization_policy_id=POLICY_ID,
        rows=list(rows),
    )


def fixture():
    r = [row(0), row(1, batch=58), row(2, part=2, batch=59)]
    r[2]["partition_row"] = 0
    return mapping(r)


def core_for(m):
    c = record()
    b = enc(m)
    parsed = codec.parse(b)
    c["row_count"] = len(m["rows"])
    c["files"][0].update(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    c["sources"]["active_revisions"] = sorted({r["revision_id"] for r in m["rows"]})
    c["embedding"]["corpus_execution_fingerprints"] = sorted(
        {r["execution_fingerprint"] for r in m["rows"]}
    )
    for i, (part, digest) in enumerate(parsed.partition_hashes):
        dense, terms = f"z/{i}dense", f"z/{i}terms"
        c["files"].extend(
            [
                dict(
                    path=dense,
                    role="dense",
                    schema="slaif-normalized-fp32le-d1024-npy-v1",
                    bytes=4,
                    sha256=h(1),
                ),
                dict(
                    path=terms,
                    role="lexical_terms",
                    schema="slaif-raw-lexical-terms-v1",
                    bytes=4,
                    sha256=h(2),
                ),
            ]
        )
        c["partitions"].append(
            dict(
                partition_id=part,
                row_count=sum(r["partition_id"] == part for r in m["rows"]),
                row_map_sha256=digest,
                dense_path=dense,
                lexical_path=terms,
            )
        )
    c["validation"] = dict(state="passed", validator_fingerprint=h(3))
    return c


@pytest.mark.parametrize("m", [mapping(), fixture()])
def test_bind_valid_and_immutable(m):
    data = enc(m)
    result = codec.bind(enc(core_for(m)), data)
    assert result.map_bytes == data and len(result.rows) == len(m["rows"])
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.space_id = "bad"
    if result.rows:
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.rows[0].batch_row = 7
        m["rows"][0]["batch_row"] = 7
        assert result.rows[0].batch_row == 0


def test_subset_correspondence_and_forgery():
    m = fixture()
    a = codec.parse(enc(m))
    part = m["rows"][0]["partition_id"]
    sub = codec.subset_bytes(a, part)
    assert hashlib.sha256(sub).hexdigest() == dict(a.partition_hashes)[part]
    decoded = json.loads(sub)
    assert decoded["rows"] == m["rows"][:2] and "snapshot_id" not in decoded
    m["rows"][0]["batch_row"] = 20
    b = codec.parse(enc(m))
    assert codec.subset_bytes(b, part) != sub
    m["rows"][0]["ordinal"], m["rows"][1]["ordinal"] = 1, 0
    with pytest.raises(codec.RowMapError):
        codec.parse(enc(m))
    with pytest.raises(codec.RowMapError):
        codec.subset_bytes(dataclasses.replace(a, rows=()), part)
    with pytest.raises(codec.RowMapError):
        codec.subset_bytes(a, "sha256:" + h(999))


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.update(snapshot_id="x"),
        lambda m: m.update(generation=1),
        lambda m: m.update(timestamp="x"),
        lambda m: m.update(schema=True),
        lambda m: m.update(space_id="A" * 64),
        lambda m: m.update(definition_fingerprint=h(1)),
        lambda m: m["rows"][0].update(ordinal=True),
        lambda m: m["rows"][0].update(token_count=1),
        lambda m: m["rows"][0].update(batch_row=128),
        lambda m: m["rows"][0].update(extra="x"),
        lambda m: m["rows"][0].update(representation_id="sha256:" + h(1)),
        lambda m: m["rows"][0].update(chunk_id="../../bad"),
        lambda m: m["rows"][1].update(partition_row=0),
        lambda m: m["rows"][1].update(chunk_id=m["rows"][0]["chunk_id"]),
        lambda m: m["rows"][1].update(representation_id=m["rows"][0]["representation_id"]),
        lambda m: m["rows"][1].update(
            batch_container_id=m["rows"][0]["batch_container_id"], batch_row=0
        ),
        lambda m: m["rows"][1].update(
            batch_container_id=m["rows"][0]["batch_container_id"], batch_metadata_sha256=h(99)
        ),
        lambda m: m["rows"][1].update(bundle_metadata_sha256=h(99)),
        lambda m: m["rows"][1].update(revision_id="sha256:" + h(99)),
        lambda m: m["rows"].reverse(),
    ],
)
def test_row_rejections(change):
    m = fixture()
    change(m)
    with pytest.raises(codec.RowMapError):
        codec.parse(enc(m))


def test_encoding_and_caps():
    for b in (
        enc(mapping()) + b"\n",
        b'{"schema":1,"schema":1}',
        b"{}",
        b"x" * (16 * 1048576 + 1),
        enc({**mapping(), "schema": 1.0}),
        enc({**mapping(), "rows": [None] * 4097}),
    ):
        with pytest.raises(codec.RowMapError):
            codec.parse(b)
    rows = [row(i, part=i + 1, batch=i + 100) for i in range(129)]
    for r in rows:
        r["partition_row"] = 0
        r["batch_row"] = 0
    with pytest.raises(codec.RowMapError):
        codec.parse(enc(mapping(rows)))


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c["files"][0].update(sha256=h(7)),
        lambda c: c["files"][0].update(bytes=c["files"][0]["bytes"] + 1),
        lambda c: c["embedding"].update(space_id=h(8)),
        lambda c: c["partitions"][0].update(row_map_sha256=h(9)),
        lambda c: c["sources"].update(active_revisions=[], withdrawn_revisions=["sha256:" + h(30)]),
        lambda c: c["sources"].update(active_revisions=[]),
        lambda c: c["embedding"].update(corpus_execution_fingerprints=[h(99)]),
        lambda c: c.update(row_count=2),
        lambda c: c["partitions"][0].update(partition_id="sha256:" + h(9)),
    ],
)
def test_bind_rejections(change):
    m = fixture()
    c = core_for(m)
    change(c)
    with pytest.raises(codec.RowMapError):
        codec.bind(enc(c), enc(m))


def test_query_execution_is_separate_and_no_io(monkeypatch):
    m = fixture()
    c = core_for(m)
    c["embedding"]["query_execution_fingerprint"] = h(999)

    def fail(*args, **kwargs):
        raise AssertionError("unexpected I/O")

    monkeypatch.setattr(builtins, "open", fail)
    assert codec.bind(enc(c), enc(m)).rows


def test_non_exception_propagates(monkeypatch):
    marker = KeyboardInterrupt()

    def stop(*args, **kwargs):
        raise marker

    monkeypatch.setattr(codec.json, "loads", stop)
    with pytest.raises(KeyboardInterrupt) as caught:
        codec.parse(enc(mapping()))
    assert caught.value is marker


def test_original_causal_control():
    # Compile an in-memory altered copy: remove only duplicate batch-row guard.
    import inspect
    import types

    source = inspect.getsource(codec)
    needle = "_check(br not in batch_rows)"
    assert source.count(needle) == 1
    mutant = types.ModuleType("slaif_raggedized_helper._row_control")
    mutant.__package__ = codec.__package__
    import sys

    sys.modules[mutant.__name__] = mutant
    try:
        exec(
            compile(source.replace(needle, "pass"), "<in-memory-control>", "exec"), mutant.__dict__
        )
        m = fixture()
        m["rows"][1]["batch_container_id"] = m["rows"][0]["batch_container_id"]
        m["rows"][1]["batch_row"] = 0
        with pytest.raises(codec.RowMapError):
            codec.parse(enc(m))
        assert len(mutant.parse(enc(m)).rows) == 3
    finally:
        del sys.modules[mutant.__name__]


def test_global_ordinal_is_part_of_subset_identity():
    m = fixture()
    original = codec.parse(enc(m))
    partition = m["rows"][2]["partition_id"]
    before = codec.subset_bytes(original, partition)
    m["rows"].pop(0)
    for index, item in enumerate(m["rows"]):
        item["ordinal"] = index
        if item["partition_id"] != partition:
            item["partition_row"] = 0
    after = codec.subset_bytes(codec.parse(enc(m)), partition)
    assert json.loads(before)["rows"][0]["ordinal"] == 2
    assert json.loads(after)["rows"][0]["ordinal"] == 1
    assert hashlib.sha256(before).digest() != hashlib.sha256(after).digest()


@pytest.mark.parametrize(
    "field,value",
    [
        ("execution_fingerprint", h(101)),
        ("extraction_id", "sha256:" + h(102)),
        ("source_scope_sha256", h(103)),
    ],
)
def test_shared_declaration_mismatch(field, value):
    m = fixture()
    if field == "execution_fingerprint":
        m["rows"][1]["batch_container_id"] = m["rows"][0]["batch_container_id"]
    m["rows"][1][field] = value
    with pytest.raises(codec.RowMapError):
        codec.parse(enc(m))


def test_bind_partition_count_mismatch_with_valid_core():
    m = fixture()
    c = core_for(m)
    c["partitions"][0]["row_count"] = 1
    c["partitions"][1]["row_count"] = 2
    with pytest.raises(codec.RowMapError):
        codec.bind(enc(c), enc(m))
