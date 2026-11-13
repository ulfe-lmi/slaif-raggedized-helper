"""Tests for bounded GPU worker protocol primitives without neural frameworks."""

import dataclasses
import hashlib
import os

import pytest

from slaif_raggedized_helper import gpu_worker_protocol as wire


def test_policy_and_identity():
    assert wire.policy_id(wire.Policy()) == wire.policy_id(wire.Policy())
    assert wire.policy_id(wire.Policy(calls=1)) != wire.policy_id(wire.Policy())
    for kwargs in ({"calls": True}, {"max_rows": 129}, {"io_seconds": 0},
                   {"request_bytes": 2 * 1024**2 + 1}):
        with pytest.raises(ValueError):
            wire.Policy(**kwargs)


def test_canonical_json_and_rows():
    value = {"nonce": "a" * 32, "rows": [[1, 2]]}
    assert wire.parse(wire.encode(value)) == value
    for raw in (b'{"a":1,"a":2}', b'{ "a":1}', b'{"a":NaN}', b'"\xff"', b'{'):
        with pytest.raises((ValueError, UnicodeError)):
            wire.parse(raw)
    wire.rows_ok(value["rows"], 3, 8)
    for rows in ([[True, 1]], [[1]], [[1, 3]], [[1, 2]] * 9):
        with pytest.raises(ValueError):
            wire.rows_ok(rows, 3, 8)
    assert len(hashlib.sha256(wire.encode(value["rows"])).hexdigest()) == 64


def test_output_requires_finite_exact_fp32():
    wire.output_ok([[0.5] * 1024], 1)
    for row in ([True] * 1024, [float("inf")] * 1024, [1e40] * 1024,
                [0.1] * 1024, [0.0] * 1023):
        with pytest.raises(ValueError):
            wire.output_ok([row], 1)
    with pytest.raises(ValueError):
        wire.output_ok([[0.0] * 1024], 2)


def test_pipe_frames_caps_and_truncation():
    r, w = os.pipe()
    out_r, out_w = os.pipe()
    try:
        pipe = wire.Pipe(r, out_w)
        os.write(w, b'{"a":1}\n')
        assert pipe.read(8, 8, 1) == {"a": 1}
        pipe.write({"x": 1}, 8, 8, 1)
        assert os.read(out_r, 8) == b'{"x":1}\n'
        os.write(w, b'123456789')
        with pytest.raises(ValueError):
            pipe.read(8, 100, 1)
    finally:
        for fd in (r, w, out_r, out_w):
            os.close(fd)


def test_pipe_deadline_and_cumulative_limit():
    r, w = os.pipe()
    out_r, out_w = os.pipe()
    try:
        pipe = wire.Pipe(r, out_w)
        os.write(w, b'1\n2\n')
        assert pipe.read(4, 3, 1) == 1
        with pytest.raises(ValueError):
            pipe.read(4, 3, 1)
        pipe.write(1, 4, 3, 1)
        with pytest.raises(ValueError):
            pipe.write(2, 4, 3, 1)
        os.close(w)
        w = -1
        with pytest.raises(ValueError):
            pipe.read(4, 20, 1)
    finally:
        for fd in (r, w, out_r, out_w):
            if fd >= 0:
                os.close(fd)


@pytest.mark.parametrize("mode", ["ok", "main_ok", "main_init_failure", "main_close_failure",
                                  "replay", "bad_digest", "init_failure",
                                  "close_failure", "interrupt_cleanup", "interrupt_body",
                                  "body_cleanup_interrupt",
                                  "init_captured", "bad_nonce", "bad_rows", "bad_output",
                                  "bad_profile", "bad_code", "bad_policy", "bad_device",
                                  "bad_definition", "bad_space", "bad_artifact", "bad_runtime",
                                  "new_foreign", "other_lease_owner"])
def test_child_owns_lease_across_return_and_forward(tmp_path, monkeypatch, mode):
    from pathlib import Path

    from slaif_raggedized_helper import embedding_space, gpu_device_lease
    from slaif_raggedized_helper import gpu_embedding_worker_main as child
    from test_gpu_embedding_backend import DEVICE, HOST, make_tree

    root = tmp_path / "artifacts"
    raw, inv, definition, tokenizer = make_tree(root)
    admitted = embedding_space.admit(raw, root, definition, tokenizer, inv.inventory_id)
    lease_root = tmp_path / "lease"
    lease_root.mkdir(mode=0o700)
    policy = wire.Policy(calls=2 if mode == "replay" else 1)
    profile = wire.profile(Path(__file__).resolve().parents[2] / "worker_profiles/gpu/uv.lock",
                           Path(os.environ["SLAIF_GPU_TEST_PACKAGES"]))
    start = {"schema": 1, "api": wire.API, "startup_nonce": "1" * 32,
             "manifest": raw.decode(), "definition": definition.model_dump(mode="json"),
             "tokenizer": {"sha256": tokenizer.sha256, "backend_version": tokenizer.backend_version,
                           "role": tokenizer.role, "model_revision": tokenizer.model_revision,
                           "preprocessing": tokenizer.preprocessing},
             "inventory": inv.inventory_id, "space": admitted.space_id, "profile": profile,
             "policy": __import__("dataclasses").asdict(policy),
             "policy_id": wire.policy_id(policy),
             "code_id": wire.code_id(), "host": HOST, "device_uuid": DEVICE}
    rows = [[3, 4]]
    req = {"nonce": "2" * 32, "digest": hashlib.sha256(wire.encode(rows)).hexdigest(), "rows": rows}
    if mode in ("bad_digest", "body_cleanup_interrupt"):
        req["digest"] = "0" * 64
    if mode == "bad_nonce":
        req["nonce"] = "z" * 32
    if mode == "bad_rows":
        req["rows"] = [[True, 2]]
        req["digest"] = hashlib.sha256(wire.encode(req["rows"])).hexdigest()
    if mode in ("bad_profile", "bad_code", "bad_policy", "bad_space"):
        key = {"bad_profile": "profile", "bad_code": "code_id",
               "bad_policy": "policy_id", "bad_space": "space"}[mode]
        start[key] = "f" * 64
    if mode == "bad_device":
        start["device_uuid"] = DEVICE[:-1] + "d"
    if mode == "bad_definition":
        start["definition"]["model_name"] = "other"
    if mode == "bad_artifact":
        (root / "tokenizer.json").write_bytes(b"changed")
    calls = []
    leases = []

    class Interrupt(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError("immutable exception")

    body_interrupt, cleanup_interrupt = Interrupt(), Interrupt()
    class Foreign:
        def close(self):
            calls.append("foreign close")

    foreign = Foreign()
    new_foreign = Foreign()
    foreign_added = []
    child.gpu_embedding_backend._retained.append(foreign)
    acquire = gpu_device_lease.acquire
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", DEVICE)
    monkeypatch.setattr(child, "_runtime_ok", lambda: mode != "bad_runtime")
    monkeypatch.setattr(child.wire, "profile", lambda *args: profile)
    admit = child.embedding_space.admit
    verify = child.embedding_artifacts.verify_artifacts
    closed_tree = child._closed_tree
    open_root = child.embedding_artifacts._root
    monkeypatch.setattr(child.embedding_space, "admit",
                        lambda raw, _, d, t, inventory: admit(
                            raw, root, d, dataclasses.replace(t, artifact=root / "tokenizer.json"),
                            inventory))
    monkeypatch.setattr(child.embedding_artifacts, "verify_artifacts",
                        lambda raw, _, **kwargs: verify(raw, root, **kwargs))
    monkeypatch.setattr(child, "_closed_tree", lambda _, files: closed_tree(root, files))
    monkeypatch.setattr(child.embedding_artifacts, "_root", lambda _: open_root(root))

    def own(_root, host, device):
        lease = acquire(str(lease_root), host, device)
        leases.append(lease)
        return lease

    monkeypatch.setattr(child.gpu_device_lease, "acquire", own)

    class Facade:
        def __init__(self, *args):
            args[-2].assert_owned()
            self.space, self._vocab = admitted, 20
            self._lease = args[-2]
            self._lease_identity = gpu_device_lease._live[id(self._lease)][:8]
            self._pid = os.getpid()
            calls.append("construct")
            if mode in ("init_failure", "main_init_failure"):
                raise ValueError("private")
            if mode == "init_captured":
                child.gpu_embedding_backend._retained.append(self)
                raise ValueError("private")
            if mode == "new_foreign":
                child.gpu_embedding_backend._retained.append(new_foreign)
                raise ValueError("private")
            if mode == "other_lease_owner":
                other = acquire(str(lease_root), HOST, DEVICE[:-1] + "d")
                leases.append(other)
                owner = object.__new__(Facade)
                owner._lease = other
                owner._lease_identity = gpu_device_lease._live[id(other)][:8]
                owner._pid = os.getpid()
                foreign_added.append(owner)
                child.gpu_embedding_backend._retained.append(owner)
                raise ValueError("private")

        def forward_cls(self, batch):
            leases[0].assert_owned()
            calls.append(batch)
            if mode == "interrupt_body":
                raise body_interrupt
            if mode == "bad_output":
                return ((float("inf"),) * 1024,)
            return ((3.0,) * 1024,)

        def close(self):
            leases[0].assert_owned()
            calls.append("close")
            if mode in ("close_failure", "main_close_failure", "interrupt_body"):
                raise ValueError("cleanup")
            if mode in ("interrupt_cleanup", "body_cleanup_interrupt"):
                raise cleanup_interrupt
            if mode == "init_captured":
                child.gpu_embedding_backend._retained.remove(self)

    monkeypatch.setattr(child.gpu_embedding_backend, "GPUEmbeddingBackend", Facade)

    class Frames:
        input = 0
        sent = []

        def read(self, *args):
            value = start if not self.sent else req
            self.input += len(wire.encode(value)) + 1
            return value

        def write(self, value, *args):
            self.sent.append(value)

    pipe = Frames()
    try:
        if mode.startswith("main_"):
            monkeypatch.setattr(child.wire, "Pipe", lambda *args: pipe)
            assert child.main() == (0 if mode == "main_ok" else 1)
        elif mode == "ok":
            child._run(pipe)
            assert calls == ["construct", rows, "close"]
            assert pipe.sent[0]["ready"] and pipe.sent[1]["digest"] == req["digest"]
        else:
            expected = (Interrupt if mode in ("interrupt_body", "interrupt_cleanup",
                                               "body_cleanup_interrupt") else ValueError)
            with pytest.raises(expected) as caught:
                child._run(pipe)
            if mode == "interrupt_body":
                assert caught.value is body_interrupt
            if mode in ("interrupt_cleanup", "body_cleanup_interrupt"):
                assert caught.value is cleanup_interrupt
            if mode == "replay":
                assert calls == ["construct", rows, "close"]
            if mode in ("bad_digest", "body_cleanup_interrupt"):
                assert calls == ["construct", "close"]
        if mode in ("bad_profile", "bad_code", "bad_policy", "bad_device",
                    "bad_definition", "bad_space", "bad_artifact", "bad_runtime"):
            assert not calls and not leases
            return
        leases[0].assert_owned()
        with pytest.raises(gpu_device_lease.DeviceLeaseRefused):
            acquire(str(lease_root), HOST, DEVICE)
        if mode != "other_lease_owner":
            other = acquire(str(lease_root), HOST, DEVICE[:-1] + "d")
            other.close()
        if mode in ("new_foreign", "other_lease_owner"):
            assert calls == ["construct"]
            assert (new_foreign if mode == "new_foreign" else foreign_added[0]) in (
                child.gpu_embedding_backend._retained)
    finally:
        assert foreign in child.gpu_embedding_backend._retained
        child.gpu_embedding_backend._retained.remove(foreign)
        for owner in [new_foreign, *foreign_added]:
            if owner in child.gpu_embedding_backend._retained:
                child.gpu_embedding_backend._retained.remove(owner)
        for lease in leases:
            lease.close()


def test_exact_gpu_profile_rejects_mutation(tmp_path):
    from pathlib import Path

    packages = Path(os.environ["SLAIF_GPU_TEST_PACKAGES"])
    lock = Path(__file__).resolve().parents[2] / "worker_profiles/gpu/uv.lock"
    expected = wire.profile(lock, packages)
    assert len(expected) == 64
    copied = tmp_path / "packages"
    copied.mkdir()
    for entry in packages.iterdir():
        if entry.name.endswith(".dist-info"):
            target = copied / entry.name
            target.mkdir()
            (target / "METADATA").write_bytes((entry / "METADATA").read_bytes())
    assert wire.profile(lock, copied) == expected
    target = next(copied.iterdir()) / "METADATA"
    target.write_bytes(target.read_bytes().replace(b"\nVersion:", b"\nVersion: invalid-", 1))
    with pytest.raises(ValueError):
        wire.profile(lock, copied)
    bad_lock = tmp_path / "profile.lock"
    bad_lock.write_bytes(lock.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        wire.profile(bad_lock, packages)


def test_code_identity_binds_actual_sources(tmp_path, monkeypatch):
    from pathlib import Path

    source = Path(wire.__file__).parent
    for name in wire.CODE_FILES:
        (tmp_path / name).write_bytes((source / name).read_bytes())
    monkeypatch.setattr(wire, "__file__", str(tmp_path / "gpu_worker_protocol.py"))
    first = wire.code_id()
    target = tmp_path / "gpu_embedding_backend.py"
    target.write_bytes(target.read_bytes() + b"\n")
    assert wire.code_id() != first


def test_pipe_read_deadline_expires():
    import time

    r, w = os.pipe()
    out_r, out_w = os.pipe()
    try:
        pipe = wire.Pipe(r, out_w)
        started = time.monotonic()
        with pytest.raises(ValueError):
            pipe.read(10, 10, 1)
        assert 0.8 <= time.monotonic() - started < 3
    finally:
        for fd in (r, w, out_r, out_w):
            os.close(fd)
