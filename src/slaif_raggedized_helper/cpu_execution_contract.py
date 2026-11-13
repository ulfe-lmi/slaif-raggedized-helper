"""Predict and construct the versioned isolated CPU execution contract.

The prediction is metadata, not evidence of execution or hardware qualification.
"""

import dataclasses
import hashlib
import json
from pathlib import Path
import re

from . import cpu_embedding_worker as cpu
from . import embedding_space, embedding_tokenizer, embedding_vectors, native_tokenizers
from .schema import fingerprint


class ContractError(ValueError):
    """A content-free contract refusal."""


@dataclasses.dataclass(frozen=True)
class PlannedContract:
    record_bytes: bytes
    fingerprint: str
    intended_execution_fingerprint: str
    space_id: str


def _bridge():
    directory = Path(__file__).resolve().parent
    return {
        name: hashlib.sha256(native_tokenizers._read_artifact(directory / name, 131072)).hexdigest()
        for name in (
            "isolated_cpu_embedding.py",
            "cpu_execution_contract.py",
            "embedding_tokenizer.py",
            "embedding_vectors.py",
        )
    }


def _validate(data):
    """Refuse noncanonical or non-closed schema-2 records, including duplicate keys."""
    from . import isolated_cpu_embedding as isolated

    if type(data) is not bytes or not 1 <= len(data) <= 16384:
        raise ValueError
    obj = cpu._parse(data)
    if (
        type(obj) is not dict
        or set(obj)
        != {
            "schema",
            "contract",
            "space",
            "definition",
            "worker",
            "normalization",
            "native",
            "bridge",
            "hardware_qualification",
        }
        or type(obj["schema"]) is not int
        or obj["schema"] != 2
        or obj["contract"] != "cpu-fp32-cls"
        or obj["normalization"] != embedding_vectors.POLICY_ID
        or obj["hardware_qualification"] != "unknown"
    ):
        raise ValueError

    def hexdigest(value, size):
        return type(value) is str and re.fullmatch(r"[0-9a-f]{%d}" % size, value) is not None

    worker, native, bridge = obj["worker"], obj["native"], obj["bridge"]
    if (
        not hexdigest(obj["space"], 64)
        or type(obj["definition"]) is not str
        or re.fullmatch(r"sha256:[0-9a-f]{64}", obj["definition"]) is None
        or type(worker) is not dict
        or set(worker) != {"space", "definition", "profile", "code", "policy"}
        or any(not hexdigest(worker[k], 64) for k in ("space", "profile", "code", "policy"))
        or worker["space"] != obj["space"]
        or worker["definition"] != obj["definition"]
        or type(native) is not dict
        or set(native)
        != {
            "artifact_sha256",
            "backend",
            "role",
            "revision",
            "preprocessing",
            "policy",
            "worker_sha256",
        }
        or not hexdigest(native["artifact_sha256"], 64)
        or not hexdigest(native["worker_sha256"], 64)
        or not hexdigest(native["revision"], 40)
        or native["backend"] != "0.21.4"
        or native["role"] != "bge_representation"
        or native["preprocessing"] != "identity"
        or type(bridge) is not dict
        or set(bridge)
        != {
            "isolated_cpu_embedding.py",
            "cpu_execution_contract.py",
            "embedding_tokenizer.py",
            "embedding_vectors.py",
        }
        or any(not hexdigest(v, 64) for v in bridge.values())
    ):
        raise ValueError
    p = native["policy"]
    if type(p) is not dict or set(p) != set(isolated._NATIVE_INTS + isolated._NATIVE_TIMES):
        raise ValueError
    if isolated._native_values(embedding_tokenizer.Policy(**p)) != isolated._native_values(
        embedding_tokenizer.Policy()
    ):
        raise ValueError
    canonical = json.dumps(
        obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    if canonical != data:
        raise ValueError
    return obj


def _record(space, definition, token, worker, native_policy):
    # Inputs come from the admitted session or freshly admitted prediction, never a caller DTO.
    from . import isolated_cpu_embedding as isolated

    if type(space) is not embedding_space.AdmittedSpace:
        raise ValueError
    if type(worker) is not dict or set(worker) != {
        "space",
        "definition",
        "profile",
        "code",
        "policy",
    }:
        raise ValueError
    for key in ("space", "profile", "code", "policy"):
        if type(worker[key]) is not str or re.fullmatch(r"[0-9a-f]{64}", worker[key]) is None:
            raise ValueError
    if (
        worker["space"] != space.space_id
        or worker["definition"] != definition.fingerprint()
        or worker["definition"] != space.definition_fingerprint
    ):
        raise ValueError
    policy_values = isolated._native_values(native_policy)
    record = {
        "schema": 2,
        "contract": "cpu-fp32-cls",
        "space": space.space_id,
        "definition": definition.fingerprint(),
        "worker": worker,
        "normalization": embedding_vectors.POLICY_ID,
        "native": {
            "artifact_sha256": token.sha256,
            "backend": token.backend_version,
            "role": token.role,
            "revision": token.model_revision,
            "preprocessing": token.preprocessing,
            "policy": dict(
                zip(isolated._NATIVE_INTS + isolated._NATIVE_TIMES, policy_values, strict=True)
            ),
            "worker_sha256": hashlib.sha256(
                native_tokenizers._read_artifact(
                    Path(__file__).with_name("embedding_tokenizer_worker.py"), 131072
                )
            ).hexdigest(),
        },
        "bridge": _bridge(),
        "hardware_qualification": "unknown",
    }
    data = json.dumps(
        record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    if len(data) > 16384:
        raise ValueError
    _validate(data)
    return data, fingerprint({"kind": "isolated-cpu-embedding-execution-v2", **record})


def prepare(
    manifest_bytes,
    artifact_root,
    definition,
    tokenizer_definition,
    expected_inventory_id,
    tokenizer_runtime,
    cpu_runtime,
    *,
    worker_policy=None,
):
    """Admit current inputs and predict identity without starting model or native workers."""
    from . import isolated_cpu_embedding as isolated

    try:
        session = isolated.IsolatedCPUEmbeddingSession(
            manifest_bytes,
            artifact_root,
            definition,
            tokenizer_definition,
            expected_inventory_id,
            tokenizer_runtime,
            cpu_runtime,
            worker_policy=worker_policy,
        )
        session._validate_state()
        space = embedding_space.admit(
            manifest_bytes, artifact_root, definition, tokenizer_definition, expected_inventory_id
        )
        lock = cpu._profile_path()
        worker = {
            "space": space.space_id,
            "definition": space.definition_fingerprint,
            "profile": cpu._profile(lock, cpu_runtime.packages),
            "code": cpu._code_identity(),
            "policy": cpu._policy_identity(session._policy),
        }
        data, fp = _record(
            space, definition, tokenizer_definition, worker, embedding_tokenizer.Policy()
        )
        return PlannedContract(data, fp, session.intended_execution_fingerprint, space.space_id)
    except Exception:
        raise ContractError("CPU execution contract refused") from None
