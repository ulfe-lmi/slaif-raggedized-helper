"""Fixed child entry point. Importing this file does not load a model."""

import hashlib
import os
import sys
from pathlib import Path


def main():
    from slaif_raggedized_helper import cpu_embedding_backend, embedding_space, native_tokenizers
    from slaif_raggedized_helper.cpu_embedding_worker import (
        Policy,
        _code_identity,
        _json,
        _parse,
        _policy_identity,
        _profile,
        _rows,
    )
    from slaif_raggedized_helper.schema import EmbeddingDefinition

    backend = None
    try:
        if sys.version_info[:2] != (3, 12) or sys.implementation.name != "cpython":
            raise ValueError
        profile = _profile(Path("/profile.lock"), Path("/packages"))

        input_bytes = output_bytes = 0
        policy = None

        def read(cap):
            nonlocal input_bytes
            raw = sys.stdin.buffer.readline(cap + 1)
            if not raw or len(raw) > cap or not raw.endswith(b"\n"):
                raise ValueError
            input_bytes += len(raw)
            if policy is not None and input_bytes > policy.total_input_bytes:
                raise ValueError
            return _parse(raw[:-1])

        def write(value, cap):
            nonlocal output_bytes
            raw = _json(value) + b"\n"
            output_bytes += len(raw)
            if len(raw) > cap or output_bytes > policy.total_output_bytes:
                raise ValueError
            sys.stdout.buffer.write(raw)
            sys.stdout.buffer.flush()

        startup = read(2 * 1024**2)
        if type(startup) is not dict or set(startup) != {
            "manifest",
            "definition",
            "tokenizer",
            "inventory",
            "space",
            "profile",
            "policy",
            "policy_id",
            "code_id",
        }:
            raise ValueError
        policy = Policy(**startup["policy"])
        if (
            input_bytes > policy.total_input_bytes
            or input_bytes > policy.request_bytes
            or startup["profile"] != profile
            or startup["policy_id"] != _policy_identity(policy)
            or startup["code_id"] != _code_identity()
        ):
            raise ValueError
        d = EmbeddingDefinition.model_validate(startup["definition"], strict=True)
        t = native_tokenizers.Definition(
            artifact=Path("/artifacts/tokenizer.json"), **startup["tokenizer"]
        )
        space = embedding_space.admit(
            startup["manifest"].encode("utf-8"), Path("/artifacts"), d, t, startup["inventory"]
        )
        if space.space_id != startup["space"]:
            raise ValueError
        backend = cpu_embedding_backend.CPUEmbeddingBackend(
            startup["manifest"].encode("utf-8"), Path("/artifacts"), d, t, startup["inventory"]
        )
        if backend.space.space_id != startup["space"]:
            raise ValueError
        write(
            {
                "ready": True,
                "space": backend.space.space_id,
                "definition": backend.space.definition_fingerprint,
                "profile": profile,
                "policy_id": _policy_identity(policy),
                "code_id": _code_identity(),
                "vocab": backend._vocab,
                "contract": "cpu-fp32-cls",
            },
            policy.response_bytes,
        )
        for _ in range(policy.calls):
            request = read(policy.request_bytes)
            if type(request) is not dict or set(request) != {"nonce", "digest", "rows"}:
                raise ValueError
            nonce, digest, rows = request["nonce"], request["digest"], request["rows"]
            if (
                type(nonce) is not str
                or len(nonce) != 32
                or any(c not in "0123456789abcdef" for c in nonce)
            ):
                raise ValueError
            _rows(rows, backend._vocab, policy.max_rows)
            if type(digest) is not str or hashlib.sha256(_json(rows)).hexdigest() != digest:
                raise ValueError
            result = backend.forward_cls(rows)
            write(
                {
                    "nonce": nonce,
                    "digest": digest,
                    "space": backend.space.space_id,
                    "profile": profile,
                    "rows": result,
                },
                policy.response_bytes,
            )
    except Exception:
        return 1
    finally:
        if backend is not None:
            backend.close()
    return 0


if __name__ == "__main__":
    sys.path[:0] = ["/packages", "/app"]
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.exit(main())
