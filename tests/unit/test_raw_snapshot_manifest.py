import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest

from slaif_raggedized_helper.embedding_vectors import POLICY_ID
from slaif_raggedized_helper.raw_snapshot_manifest import ManifestError, parse

H = "a" * 64


def record():
    return {
        "schema": 1,
        "kind": "slaif-raw-snapshot-core-v1",
        "representation": "raw",
        "embedding": {
            "space_id": H,
            "definition_fingerprint": "sha256:" + H,
            "query_policy_fingerprint": H,
            "query_execution_fingerprint": H,
            "corpus_execution_fingerprints": [],
            "normalization_policy_id": POLICY_ID,
            "precision_qualification_ref": None,
        },
        "analyzer": {
            "fingerprint": H,
            "backend": "bm25s-lucene",
            "bm25s_version": "0.2.14",
            "numpy_version": "2.5.4",
            "scipy_version": "1.18.1",
        },
        "chunk_policy_fingerprint": H,
        "representation_policy_fingerprint": H,
        "sources": {"active_revisions": [], "withdrawn_revisions": []},
        "row_count": 0,
        "row_map_path": "map",
        "membership_path": "members",
        "files": [
            {
                "path": "map",
                "role": "row_map",
                "schema": "slaif-raw-row-map-v1",
                "bytes": 0,
                "sha256": H,
            },
            {
                "path": "members",
                "role": "source_membership",
                "schema": "slaif-raw-source-membership-v1",
                "bytes": 0,
                "sha256": H,
            },
        ],
        "partitions": [],
        "validation": {"state": "unproven", "validator_fingerprint": None},
    }


def encode(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":")).encode()


def test_empty_and_immutable():
    data = encode(record())
    result = parse(data)
    assert result.snapshot_id == "sha256:" + hashlib.sha256(data).hexdigest()
    with pytest.raises(FrozenInstanceError):
        result.files[0].path = "other"
    x = record()
    x["files"][0]["bytes"] = 1
    assert parse(encode(x)).snapshot_id != result.snapshot_id


def test_nonempty():
    x = record()
    x["row_count"] = 1
    x["embedding"]["corpus_execution_fingerprints"] = [H]
    x["files"].extend(
        [
            {
                "path": "z/dense",
                "role": "dense",
                "schema": "slaif-normalized-fp32le-d1024-npy-v1",
                "bytes": 4,
                "sha256": H,
            },
            {
                "path": "z/terms",
                "role": "lexical_terms",
                "schema": "slaif-raw-lexical-terms-v1",
                "bytes": 4,
                "sha256": H,
            },
        ]
    )
    x["partitions"] = [
        {
            "partition_id": "sha256:" + H,
            "row_count": 1,
            "row_map_sha256": H,
            "dense_path": "z/dense",
            "lexical_path": "z/terms",
        }
    ]
    assert len(parse(encode(x)).partitions) == 1
    x["partitions"][0]["lexical_path"] = "z/dense"
    with pytest.raises(ManifestError):
        parse(encode(x))


@pytest.mark.parametrize(
    "change",
    [
        lambda x: x.update(snapshot_id="x"),
        lambda x: x.update(row_count=True),
        lambda x: x.update(row_map_path="../x"),
        lambda x: x["files"][0].update(bytes=16777217),
        lambda x: x["sources"].update(
            active_revisions=["sha256:" + H], withdrawn_revisions=["sha256:" + H]
        ),
        lambda x: x["files"][0].update(role="dense"),
    ],
)
def test_rejections(change):
    x = record()
    change(x)
    with pytest.raises(ManifestError):
        parse(encode(x))


def test_noncanonical_and_duplicate():
    for data in (encode(record()) + b"\n", b'{"schema":1,"schema":1}', b"{}", b"x" * 262145):
        with pytest.raises(ManifestError):
            parse(data)
