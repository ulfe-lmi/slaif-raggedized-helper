"""Admission and empty DATA checks without integration helpers."""

from dataclasses import asdict
import json

import pytest

from slaif_raggedized_helper import (
    derived_store,
    embedding_vectors,
    retrieval_representation,
    schema,
)
from slaif_raggedized_helper import raw_snapshot_row_builder as builder
from slaif_raggedized_helper.source_admission import OriginalStore


def declaration(**changes):
    policy = schema.fingerprint(
        dict(
            kind="embedding-representation-policy-v1",
            policy=asdict(retrieval_representation.Policy()),
            batch_policy=asdict(retrieval_representation.BatchPolicy()),
        )
    )[7:]
    obj = dict(
        schema=1,
        kind="slaif-raw-row-map-build-declaration-v1",
        space_id="a" * 64,
        definition_fingerprint="sha256:" + "b" * 64,
        representation_policy_fingerprint=policy,
        chunk_policy_fingerprint="c" * 64,
        normalization_policy_id=embedding_vectors.POLICY_ID,
    )
    obj.update(changes)
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("ascii")


def stores():
    return object.__new__(OriginalStore), object.__new__(derived_store.Store)


def test_empty_is_deterministic_and_unqualified(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("store access")

    monkeypatch.setattr(derived_store.Store, "load", forbidden)
    a = builder.build(*stores(), declaration(), ())
    assert a == builder.build(*stores(), declaration(), ())
    assert (a.row_count, a.group_count, a.execution_origin, a.qualification) == (
        0,
        0,
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
    )


@pytest.mark.parametrize(
    "groups",
    [
        [],
        (("a" * 64, "b" * 64), ("a" * 64, "b" * 64)),
        (("b" * 64, "c" * 64), ("a" * 64, "d" * 64)),
        (("a" * 64, "b" * 64), ("c" * 64, "b" * 64)),
        (("A" * 64, "b" * 64),),
        (("a" * 64, "b" * 64, "c" * 64),),
        (("a" * 64, "b" * 64),) * 129,
    ],
)
def test_group_admission(groups):
    with pytest.raises(builder.BuildError):
        builder.build(*stores(), declaration(), groups)


@pytest.mark.parametrize(
    "data",
    [
        b"{}",
        b'{"schema":1,"schema":1}',
        declaration(schema=True),
        declaration(representation_policy_fingerprint="f" * 64),
        declaration(definition_fingerprint="b" * 64),
        declaration() + b" ",
    ],
)
def test_declaration_admission(data):
    with pytest.raises(builder.BuildError):
        builder.build(*stores(), data, ())


@pytest.mark.parametrize("deadline", [True, 0, 120001, 1.0])
def test_deadline_admission(deadline):
    with pytest.raises(builder.BuildError):
        builder.build(*stores(), declaration(), (), deadline_ms=deadline)


def test_deadline_after_result_hash(monkeypatch):
    ticks = iter([0, 0, 0, 0, 2])
    monkeypatch.setattr(builder.time, "monotonic", lambda: next(ticks))
    with pytest.raises(builder.BuildError):
        builder.build(*stores(), declaration(), (), deadline_ms=1000)
