"""Source-backed pinned query with a supplied encoder; no neural execution."""

import test_retrieval_representation_composition  # noqa: F401
import hashlib
import json
from pathlib import Path
import struct

import pytest
from slaif_raggedized_helper import raw_snapshot_query as q
from test_raw_hybrid_search_composition import make_sources
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401


def test_source_backed_old_pin(tmp_path, monkeypatch):
    checkout = Path(__file__).resolve().parents[2]
    assert Path(q.__file__).resolve().is_relative_to(checkout)
    assert Path(make_sources.__code__.co_filename).resolve().is_relative_to(checkout)
    originals, derived, source_root, ident = make_sources(tmp_path)
    owner = q.pin.PinOwner()
    try:
        source = source_root / "snapshots" / ident[7:]
        core = json.loads((source / ".core.json").read_bytes())
        core["embedding"]["query_policy_fingerprint"] = "3" * 64
        core["embedding"]["query_execution_fingerprint"] = "4" * 64
        payloads = tuple((d["path"], (source / d["path"]).read_bytes()) for d in core["files"])

        def wire(value):
            return json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
            ).encode("utf-8")

        root = tmp_path / "published"
        root.mkdir(mode=0o700)
        first = q.publication.publish_directory(originals, derived, str(root), wire(core), payloads)
        core["validation"]["validator_fingerprint"] = "f" * 64
        second = q.publication.publish_directory(
            originals, derived, str(root), wire(core), payloads
        )
        assert first.snapshot_id != second.snapshot_id
        selected = q.selection.compare_and_select_data(
            originals, derived, str(root), first.snapshot_id, None
        )
        captured = owner.acquire_selected_data(originals, derived, str(root))
        q.selection.compare_and_select_data(
            originals, derived, str(root), second.snapshot_id, selected.pointer.pointer_bytes
        )
        grants = q.records.Grants(schema_version=1, corpora=("one",), versions=("v1",), labels=())
        authority = q.QueryAuthority("e" * 64, grants, None, ())
        encoder = object.__new__(q.query_embedding.ResidentQueryEncoder)
        encoder._state = "open"
        payload = struct.pack("<1024f", 1.0, *([0.0] * 1023))
        embedding = q.query_embedding.QueryEmbedding(
            payload,
            hashlib.sha256(payload).hexdigest(),
            core["embedding"]["space_id"],
            core["embedding"]["definition_fingerprint"],
            "sha256:" + "9" * 64,
            b"synthetic",
            "sha256:" + "4" * 64,
            "3" * 64,
        )
        counts = dict(encode=0, hybrid=0, dense=0, index=0, lexical=0, fusion=0)

        def encode(self, text):
            counts["encode"] += 1
            return embedding

        monkeypatch.setattr(q.query_embedding.ResidentQueryEncoder, "encode_query", encode)
        for obj, name, key in (
            (q.hybrid, "search", "hybrid"),
            (q.dense, "_score", "dense"),
            (q.lexical, "_index", "index"),
            (q.lexical, "_score", "lexical"),
            (q.hybrid.fusion, "fuse", "fusion"),
        ):
            actual = getattr(obj, name)

            def counted(*args, _actual=actual, _key=key, **kwargs):
                counts[_key] += 1
                return _actual(*args, **kwargs)

            monkeypatch.setattr(obj, name, counted)
        args = (originals, derived, str(root), owner, encoder, "Heading alpha beta gamma")

        def deny(*_):
            raise ValueError("policy denied")

        with pytest.raises(q.PinnedQueryError):
            q.search_pinned_data(*args, deny, dense_k=3, lexical_k=3, partition_cap=3, k=3)
        assert all(value == 0 for value in counts.values())
        boundaries = []

        def provider(boundary, admission):
            boundaries.append(boundary)
            assert admission.snapshot_id == first.snapshot_id
            return authority

        result = q.search_pinned_data(
            *args, provider, dense_k=3, lexical_k=3, partition_cap=3, k=3, trace=True
        )
        assert counts == dict(encode=1, hybrid=1, dense=1, index=1, lexical=1, fusion=1)
        assert boundaries == ["before_encode", "before_retrieval", "before_return"]
        assert owner.check() == captured
        assert result.snapshot_id == first.snapshot_id != second.snapshot_id
        assert result.question_sha256 == hashlib.sha256(args[5].encode()).hexdigest()
        assert result.query_payload_sha256 == embedding.payload_sha256
        assert result.authority_sha256 == q.lexical._authority_hash(grants, None)
        assert result.hybrid.lexical.matching > 0
        assert (result.execution_origin, result.authorization_status, result.qualification) == (
            "SUPPLIED_UNVERIFIED",
            "SUPPLIED_POLICY_PROVIDER_ONLY",
            "NOT_QUALIFIED",
        )
    finally:
        if owner.state == "ACTIVE":
            owner.close()
        derived.close()
        originals.close()
