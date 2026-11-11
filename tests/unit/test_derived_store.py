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
