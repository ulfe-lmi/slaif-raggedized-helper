"""Fixed private GPU child entry; importing does not load a framework."""

import dataclasses
import hashlib
import json
import os
import re
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path[:0] = ["/packages", "/app/src"]

from slaif_raggedized_helper import (embedding_artifacts, embedding_space, gpu_device_lease,
                                     gpu_embedding_backend, gpu_worker_protocol as wire,
                                     native_tokenizers)
from slaif_raggedized_helper.cpu_embedding_backend import _closed_tree
from slaif_raggedized_helper.schema import EmbeddingDefinition


def _hex(value, length):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def _runtime_ok():
    return sys.version_info[:2] == (3, 12) and sys.implementation.name == "cpython"


def _run(pipe):
    if not _runtime_ok():
        raise ValueError
    selected_profile = wire.profile(Path("/profile.lock"), Path("/packages"))
    backend_lock = wire._profile_path(Path(gpu_embedding_backend.__file__).resolve().parent)
    if wire.profile(backend_lock, Path("/packages")) != selected_profile:
        raise ValueError
    start = pipe.read(2 * 1024**2, 32 * 1024**2, 120)
    fields = {"schema", "api", "startup_nonce", "manifest", "definition", "tokenizer",
              "inventory", "space", "profile", "policy", "policy_id", "code_id",
              "host", "device_uuid"}
    if (type(start) is not dict or set(start) != fields or start["schema"] != wire.SCHEMA
            or type(start["schema"]) is not int or start["api"] != wire.API
            or not _hex(start["startup_nonce"], 32) or not _hex(start["host"], 64)
            or type(start["device_uuid"]) is not str
            or gpu_device_lease._UUID.fullmatch(start["device_uuid"]) is None
            or os.environ.get("CUDA_VISIBLE_DEVICES") != start["device_uuid"]):
        raise ValueError
    if (type(start["policy"]) is not dict
            or set(start["policy"]) != set(wire.Policy.__dataclass_fields__)):
        raise ValueError
    policy = wire.Policy(**start["policy"])
    code, policy_id = wire.code_id(), wire.policy_id(policy)
    if (pipe.input > policy.total_input_bytes or pipe.input > policy.request_bytes
            or selected_profile != start["profile"] or code != start["code_id"]
            or policy_id != start["policy_id"] or type(start["manifest"]) is not str):
        raise ValueError
    d = EmbeddingDefinition.model_validate(start["definition"], strict=True)
    t = native_tokenizers.Definition(
        artifact=Path("/artifacts/tokenizer.json"), **start["tokenizer"])
    manifest = start["manifest"].encode("utf-8")
    space = embedding_space.admit(manifest, Path("/artifacts"), d, t, start["inventory"])
    if space.space_id != start["space"]:
        raise ValueError
    inv = embedding_artifacts.verify_artifacts(manifest, Path("/artifacts"))
    weight = next(item for item in inv.files if item.role == "weights")
    if weight.path != ("model.safetensors" if inv.checkpoint_format == "safetensors"
                       else "pytorch_model.bin"):
        raise ValueError
    _closed_tree(Path("/artifacts"), inv.files)
    root_fd = embedding_artifacts._root(Path("/artifacts"))
    try:
        config_fd = embedding_artifacts._open_file(root_fd, "config.json")
        with os.fdopen(config_fd, "rb") as stream:
            config = json.load(stream)
    finally:
        os.close(root_fd)
    vocab, pad = config.get("vocab_size"), config.get("pad_token_id")
    if (type(vocab) is not int or not 1 <= vocab <= 10000000 or type(pad) is not int
            or not 0 <= pad < vocab):
        raise ValueError
    lease = gpu_device_lease.acquire("/lease", start["host"], start["device_uuid"])
    lease.assert_owned()
    definition_snapshot = wire.encode(start["definition"])
    tokenizer_snapshot = dataclasses.astuple(t)

    def stable():
        if (wire.encode(d.model_dump(mode="json")) != definition_snapshot
                or dataclasses.astuple(t) != tokenizer_snapshot
                or wire.policy_id(policy) != policy_id
                or wire.code_id() != code):
            raise ValueError
        lease.assert_owned()

    backend = None
    error = None
    retained_before = {id(owner) for owner in gpu_embedding_backend._retained}
    try:
        backend = gpu_embedding_backend.GPUEmbeddingBackend(
            manifest, Path("/artifacts"), d, t, start["inventory"], lease, start["device_uuid"])
        if backend.space != space or backend._vocab != vocab:
            raise ValueError
        stable()
        binding = {"schema": wire.SCHEMA, "api": wire.API,
                   "startup_nonce": start["startup_nonce"], "space": space.space_id,
                   "definition": space.definition_fingerprint, "profile": selected_profile,
                   "code_id": code, "policy_id": policy_id, "device_uuid": start["device_uuid"],
                   "device_key": lease.key}
        pipe.write({**binding, "ready": True, "vocab": vocab, "contract": "gpu-fp16-cls"},
                   policy.response_bytes, policy.total_output_bytes, policy.io_seconds)
        seen = set()
        for _ in range(policy.calls):
            request = pipe.read(policy.request_bytes, policy.total_input_bytes, policy.io_seconds)
            if type(request) is not dict or set(request) != {"nonce", "digest", "rows"}:
                raise ValueError
            nonce, digest, rows = request["nonce"], request["digest"], request["rows"]
            if not _hex(nonce, 32) or nonce in seen or not _hex(digest, 64):
                raise ValueError
            wire.rows_ok(rows, vocab, policy.max_rows)
            if hashlib.sha256(wire.encode(rows)).hexdigest() != digest:
                raise ValueError
            seen.add(nonce)
            stable()
            result = backend.forward_cls(rows)
            stable()
            wire.output_ok(result, len(rows))
            pipe.write({**binding, "nonce": nonce, "digest": digest, "rows": result},
                       policy.response_bytes, policy.total_output_bytes, policy.io_seconds)
    except BaseException as exc:
        error = exc
        if backend is None:
            # Constructor failures can retain an owner internally; never close a foreign owner.
            record = gpu_device_lease._live.get(id(lease))
            candidates = [
                owner for owner in gpu_embedding_backend._retained
                if id(owner) not in retained_before
                and type(owner) is gpu_embedding_backend.GPUEmbeddingBackend
                and record is not None and record[0] is lease and record[6] == os.getpid()
                and record[8][0] == "live" and lease._state == "live"
                and getattr(owner, "_lease", None) is lease
                and getattr(owner, "_lease_identity", None) == record[:8]
                and getattr(owner, "_pid", None) == os.getpid()
            ]
            if len(candidates) == 1:
                backend = candidates[0]
    if backend is not None:
        try:
            backend.close()
        except BaseException as cleanup:
            if (error is None
                    or (isinstance(error, Exception) and not isinstance(cleanup, Exception))):
                error = cleanup
    # The live registry holds the actual lease through process termination.
    if error is not None:
        raise error


def main():
    try:
        _run(wire.Pipe(0, 1))
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
