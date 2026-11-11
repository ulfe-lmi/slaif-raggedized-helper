import hashlib
import json
import os

import pytest

from slaif_raggedized_helper.derived_store import Member, Store, StoreError


def test_roundtrip_dedup_and_reopen(tmp_path):
    members = (Member("first", b"same"), Member("second", b"same"), Member("empty", b""))
    with Store(tmp_path) as store:
        ident = store.publish(b'{"z":[1,true],"a":"text"}', members)
        assert store.publish(b'{"a":"text", "z":[1,true]}', members) == ident
    with Store(tmp_path) as store:
        snapshot = store.load(ident)
        assert snapshot.members == members
        assert snapshot.metadata["z"] == (1, True)
        assert hashlib.sha256(snapshot.manifest).hexdigest() == ident
        with pytest.raises(TypeError):
            snapshot.metadata["a"] = 1
    assert len(list((tmp_path / "derived/v1/objects").iterdir())) == 2


@pytest.mark.parametrize(
    "metadata,members",
    [
        (b'{"a":1,"a":2}', ()),
        (b"[]", ()),
        (b'{"x":NaN}', ()),
        (b'{"x":"\\ud800"}', ()),
        (b"\xff", ()),
        (b"{}", (Member("../x", b"x"),)),
        (b"{}", (Member("x", b"a"), Member("x", b"b"))),
        (b"{}", [Member("x", b"x")]),
        (b"{}", (Member("x", bytearray(b"x")),)),
        (b"{}", tuple(Member("x", b"") for _ in range(17))),
    ],
)
def test_bad_inputs(tmp_path, metadata, members):
    with Store(tmp_path) as store, pytest.raises(StoreError):
        store.publish(metadata, members)


def test_tamper_and_symlink(tmp_path):
    with Store(tmp_path) as store:
        ident = store.publish(b"{}", (Member("x", b"abc"),))
        obj = tmp_path / "derived/v1/objects" / hashlib.sha256(b"abc").hexdigest()
        obj.write_bytes(b"bad")
        with pytest.raises(StoreError):
            store.load(ident)
        with pytest.raises(StoreError):
            store.publish(b"{}", (Member("x", b"abc"),))
        obj.unlink()
        obj.symlink_to("/dev/null")
        with pytest.raises(StoreError):
            store.load(ident)


def test_bad_manifest_and_fifo(tmp_path):
    with Store(tmp_path) as store:
        manifest = json.dumps(
            {"format": "slaif-derived-container-v1", "metadata": {}, "members": [], "extra": 1},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        ident = hashlib.sha256(manifest).hexdigest()
        path = tmp_path / "derived/v1/manifests" / ident
        path.write_bytes(manifest)
        path.chmod(0o600)
        with pytest.raises(StoreError):
            store.load(ident)
        path.unlink()
        os.mkfifo(path, 0o600)
        with pytest.raises(StoreError):
            store.load(ident)


def test_failure_before_manifest_leaves_no_manifest(tmp_path, monkeypatch):
    with Store(tmp_path) as store:
        original = store._put

        def fail(directory, digest, data, end):
            if directory == store._manifests:
                raise OSError
            original(directory, digest, data, end)

        monkeypatch.setattr(store, "_put", fail)
        with pytest.raises(StoreError):
            store.publish(b"{}", (Member("x", b"abc"),))
        assert list((tmp_path / "derived/v1/manifests").iterdir()) == []


def test_concurrent_publication(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    def publish(_):
        with Store(tmp_path) as store:
            return store.publish(b"{}", (Member("x", b"concurrent"),))

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(publish, range(8)))
    assert len(set(ids)) == 1
    with Store(tmp_path) as store:
        assert store.load(ids[0]).members == (Member("x", b"concurrent"),)


def test_insecure_directory_and_object(tmp_path):
    with Store(tmp_path) as store:
        ident = store.publish(b"{}", (Member("x", b"abc"),))
        obj = tmp_path / "derived/v1/objects" / hashlib.sha256(b"abc").hexdigest()
        obj.chmod(0o644)
        with pytest.raises(StoreError):
            store.load(ident)
    (tmp_path / "derived/v1/objects").chmod(0o755)
    with pytest.raises(StoreError):
        Store(tmp_path)


def test_closed_store_cannot_use_recycled_descriptors(tmp_path):
    aroot, broot = tmp_path / "a", tmp_path / "b"
    aroot.mkdir(mode=0o700)
    broot.mkdir(mode=0o700)
    a = Store(aroot)
    a.close()
    a.close()
    with Store(broot) as b:
        ident = b.publish(b"{}", ())
        with pytest.raises(StoreError):
            a.publish(b"{}", ())
        with pytest.raises(StoreError):
            a.load(ident)
        assert b.load(ident).members == ()


def test_deadline_after_final_fsync_and_empty_load(tmp_path, monkeypatch):
    import slaif_raggedized_helper.derived_store as ds

    now = [0.0]
    monkeypatch.setattr(ds.time, "monotonic", lambda: now[0])
    with Store(tmp_path) as store:
        original = ds.os.fsync

        def late(fd):
            original(fd)
            if fd == store._manifests:
                now[0] = 31.0

        monkeypatch.setattr(ds.os, "fsync", late)
        with pytest.raises(StoreError):
            store.publish(b"{}", ())
        monkeypatch.setattr(ds.os, "fsync", original)
        now[0] = 0
        ident = store.publish(b"{}", ())
        original_freeze = ds._freeze

        def late_freeze(value):
            result = original_freeze(value)
            now[0] = 31
            return result

        monkeypatch.setattr(ds, "_freeze", late_freeze)
        with pytest.raises(StoreError):
            store.load(ident)


@pytest.mark.parametrize(
    "change",
    [
        lambda x: x.update(format="wrong"),
        lambda x: x.update(metadata=[]),
        lambda x: x.update(members={}),
        lambda x: x.update(extra=1),
        lambda x: x.update(members=[{"name": "../x", "sha256": "0" * 64, "bytes": 0}]),
        lambda x: x.update(members=[{"name": "x", "sha256": "G" * 64, "bytes": 0}]),
        lambda x: x.update(members=[{"name": "x", "sha256": "0" * 64, "bytes": True}]),
        lambda x: x.update(members=[{"name": "x", "sha256": "0" * 64, "bytes": 2**30}]),
        lambda x: x.update(members=[{"name": "x", "sha256": "0" * 64, "bytes": 0}] * 17),
        lambda x: x.update(members=[{"name": "0", "sha256": "0" * 64, "bytes": 0}]),
    ],
)
def test_manifest_rejected_before_member_open(tmp_path, monkeypatch, change):
    import slaif_raggedized_helper.derived_store as ds

    obj = {"format": ds.FORMAT, "metadata": {}, "members": []}
    change(obj)
    raw = ds._encode(obj)
    ident = hashlib.sha256(raw).hexdigest()
    with Store(tmp_path) as store:
        path = tmp_path / "derived/v1/manifests" / ident
        path.write_bytes(raw)
        path.chmod(0o600)
        read = store._read

        def guarded(directory, *args):
            assert directory != store._objects
            return read(directory, *args)

        monkeypatch.setattr(store, "_read", guarded)
        with pytest.raises(StoreError):
            store.load(ident)


@pytest.mark.parametrize(
    "primitive,stage",
    [
        ("write", "object"),
        ("link", "object"),
        ("fsync", "object"),
        ("write", "manifest"),
        ("link", "manifest"),
        ("fsync", "manifest"),
    ],
)
def test_injected_publication_failures(tmp_path, monkeypatch, primitive, stage):
    import slaif_raggedized_helper.derived_store as ds

    with Store(tmp_path) as store:
        original = getattr(ds.os, primitive)
        active = [False]
        put = store._put

        def wrapped(directory, *args):
            active[0] = directory == (store._objects if stage == "object" else store._manifests)
            try:
                return put(directory, *args)
            finally:
                active[0] = False

        monkeypatch.setattr(store, "_put", wrapped)
        failed = [False]

        def fail_once(*args, **kwargs):
            if active[0] and not failed[0]:
                failed[0] = True
                raise OSError("injected")
            return original(*args, **kwargs)

        monkeypatch.setattr(ds.os, primitive, fail_once)
        with pytest.raises(StoreError):
            store.publish(b"{}", (Member("x", b"abc"),))
        assert failed[0]
        assert not list((tmp_path / "derived/v1/objects").glob(".stage-*"))
        assert not list((tmp_path / "derived/v1/manifests").glob(".stage-*"))
        ident = store.publish(b"{}", (Member("x", b"abc"),))
        assert store.load(ident).members == (Member("x", b"abc"),)


def test_descriptor_mutation_is_refused(tmp_path, monkeypatch):
    import slaif_raggedized_helper.derived_store as ds

    with Store(tmp_path) as store:
        ident = store.publish(b"{}", (Member("x", b"abc"),))
        original = ds.os.read
        changed = [False]

        def mutate(fd, count):
            data = original(fd, count)
            if data and not changed[0]:
                changed[0] = True
                os.fchmod(fd, 0o644)
            return data

        monkeypatch.setattr(ds.os, "read", mutate)
        with pytest.raises(StoreError):
            store.load(ident)


def test_metadata_and_member_limits_without_large_allocations(tmp_path, monkeypatch):
    import slaif_raggedized_helper.derived_store as ds

    with Store(tmp_path) as store:
        monkeypatch.setattr(ds, "MAX_MEMBER", 2)
        monkeypatch.setattr(ds, "MAX_TOTAL", 3)
        for members in [(Member("x", b"abc"),), (Member("x", b"ab"), Member("y", b"ab"))]:
            with pytest.raises(StoreError):
                store.publish(b"{}", members)
        monkeypatch.setattr(ds, "MAX_METADATA", 5)
        with pytest.raises(StoreError):
            store.publish(b'{"a":1}', ())


@pytest.mark.parametrize(
    "metadata",
    [
        b'{"x":' + b"[" * 33 + b"0" + b"]" * 33 + b"}",
        b'{"x":[' + b"0," * 20000 + b"0]}",
        b'{"x":' + str(1 << 431).encode() + b"}",
        b'{"x":"\\udfff"}',
    ],
)
def test_json_complexity_and_unicode_limits(tmp_path, metadata):
    with Store(tmp_path) as store, pytest.raises(StoreError):
        store.publish(metadata, ())


def test_aggregate_manifest_limit_before_member_open(tmp_path, monkeypatch):
    import slaif_raggedized_helper.derived_store as ds

    obj = {
        "format": ds.FORMAT,
        "metadata": {},
        "members": [
            {"name": "a", "sha256": "0" * 64, "bytes": ds.MAX_MEMBER},
            {"name": "b", "sha256": "0" * 64, "bytes": ds.MAX_MEMBER},
        ],
    }
    raw = ds._encode(obj)
    ident = hashlib.sha256(raw).hexdigest()
    with Store(tmp_path) as store:
        path = tmp_path / "derived/v1/manifests" / ident
        path.write_bytes(raw)
        path.chmod(0o600)
        read = store._read

        def guarded(directory, *args):
            assert directory != store._objects
            return read(directory, *args)

        monkeypatch.setattr(store, "_read", guarded)
        with pytest.raises(StoreError):
            store.load(ident)


def test_final_directory_fsync_failure_may_commit(tmp_path, monkeypatch):
    import slaif_raggedized_helper.derived_store as ds

    with Store(tmp_path) as store:
        original = ds.os.fsync
        failed = [False]

        def fail(fd):
            if fd == store._manifests and not failed[0]:
                failed[0] = True
                raise OSError("after link")
            return original(fd)

        monkeypatch.setattr(ds.os, "fsync", fail)
        with pytest.raises(StoreError):
            store.publish(b"{}", ())
        manifests = list((tmp_path / "derived/v1/manifests").iterdir())
        assert len(manifests) == 1
        assert store.load(manifests[0].name).members == ()
        assert store.publish(b"{}", ()) == manifests[0].name


def test_hash_chunks_check_deadline(tmp_path, monkeypatch):

    with Store(tmp_path) as store:
        calls = [0]

        def deadline(_):
            calls[0] += 1
            if calls[0] == 2:
                raise ValueError

        monkeypatch.setattr(store, "_deadline", deadline)
        with pytest.raises(ValueError):
            store._hash(b"x" * 131073, 0)
        assert calls[0] == 2


def test_unrelated_stage_survives_and_missing_member_never_loads(tmp_path):
    with Store(tmp_path) as store:
        unrelated = tmp_path / "derived/v1/objects/.stage-unrelated"
        unrelated.write_bytes(b"keep")
        unrelated.chmod(0o600)
        members = (Member("a", b"a"), Member("b", b"b"))
        ident = store.publish(b"{}", members)
        (tmp_path / "derived/v1/objects" / hashlib.sha256(b"b").hexdigest()).unlink()
        with pytest.raises(StoreError):
            store.load(ident)
        assert unrelated.read_bytes() == b"keep"


def test_manifest_hash_and_truncation_refused(tmp_path):
    with Store(tmp_path) as store:
        ident = store.publish(b"{}", ())
        path = tmp_path / "derived/v1/manifests" / ident
        path.write_bytes(b"{}")
        with pytest.raises(StoreError):
            store.load(ident)
