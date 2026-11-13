import dataclasses
import json

import pytest

from slaif_raggedized_helper import derived_store
from slaif_raggedized_helper import raw_snapshot_file_builder as builder
from slaif_raggedized_helper.source_admission import OriginalStore
from test_raw_snapshot_rows import enc, mapping


def context(m):
    return enc(
        dict(
            schema=1,
            kind="slaif-raw-snapshot-query-context-v1",
            space_id=m["space_id"],
            definition_fingerprint=m["definition_fingerprint"],
            query_policy_fingerprint="b" * 64,
            query_execution_fingerprint="c" * 64,
            precision_qualification_ref=None,
        )
    )


def test_empty_and_admission(tmp_path, monkeypatch):
    originals = OriginalStore(tmp_path / "store")
    with derived_store.Store(tmp_path / "store") as derived:
        try:
            m = mapping()
            data, query = enc(m), context(m)
            result = builder.build(originals, derived, data, (), (), query)
            assert [p for p, _ in result.files] == ["map", "members"]
            assert result.row_count == result.partition_count == result.member_count == 0
            assert result.qualification == "NOT_QUALIFIED"
            assert (
                json.loads(result.core_bytes)["validation"]["validator_fingerprint"]
                == builder.VALIDATION_POLICY_FINGERPRINT
            )
            with pytest.raises(dataclasses.FrozenInstanceError):
                result.row_count = 1

            def forbidden(*args):
                raise AssertionError("source I/O before admission")

            monkeypatch.setattr(builder.raw_snapshot_membership, "build", forbidden)
            for args in (
                (data, (), (), query + b" "),
                (data, ("bad",), (), query),
                (data, (), (), b"{}"),
                (data + b" ", (), (), query),
            ):
                with pytest.raises(builder.SnapshotBuildError):
                    builder.build(originals, derived, *args)
            with pytest.raises(builder.SnapshotBuildError):
                builder.build(originals, derived, data, (), (), query, deadline_ms=True)
        finally:
            originals.close()


def test_non_exception_propagates(tmp_path, monkeypatch):
    originals = OriginalStore(tmp_path / "store")
    with derived_store.Store(tmp_path / "store") as derived:
        try:

            class Stop(BaseException):
                pass

            def stop(_):
                raise Stop()

            monkeypatch.setattr(builder.raw_snapshot_rows, "parse", stop)
            m = mapping()
            with pytest.raises(Stop):
                builder.build(originals, derived, enc(m), (), (), context(m))
        finally:
            originals.close()


def test_strict_context_ids_and_final_deadline(tmp_path, monkeypatch):
    originals = OriginalStore(tmp_path / "store")
    with derived_store.Store(tmp_path / "store") as derived:
        try:
            m = mapping()
            data = enc(m)
            q = json.loads(context(m))
            invalid = []
            for field, value in (
                ("schema", True),
                ("space_id", "f" * 64),
                ("definition_fingerprint", "a" * 64),
                ("query_policy_fingerprint", "A" * 64),
                ("precision_qualification_ref", "f" * 64),
            ):
                altered = dict(q)
                altered[field] = value
                invalid.append(enc(altered))
            invalid += [b'{"schema":1,"schema":1}', context(m) + b"\n"]
            for query in invalid:
                with pytest.raises(builder.SnapshotBuildError):
                    builder.build(originals, derived, data, (), (), query)
            for ids in (("b" * 64, "a" * 64), ("a" * 64, "a" * 64), ["a" * 64]):
                with pytest.raises(builder.SnapshotBuildError):
                    builder.build(originals, derived, data, ids, (), context(m))
            clock = [0.0]
            monkeypatch.setattr(builder.time, "monotonic", lambda: clock[0])
            validate = builder.raw_snapshot_files.validate_files

            def late(*args):
                result = validate(*args)
                clock[0] = 1.0
                return result

            monkeypatch.setattr(builder.raw_snapshot_files, "validate_files", late)
            with pytest.raises(builder.SnapshotBuildError):
                builder.build(originals, derived, data, (), (), context(m), deadline_ms=1000)
        finally:
            originals.close()
