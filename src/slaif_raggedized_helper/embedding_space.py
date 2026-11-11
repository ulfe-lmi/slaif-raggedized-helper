"""Admission of a verified local artifact inventory into a versioned space."""

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path

from . import embedding_artifacts, native_tokenizers
from .schema import EmbeddingDefinition


class SpaceRefused(ValueError):
    """Admission failed without exposing caller input."""


@dataclass(frozen=True)
class AdmittedSpace:
    inventory_id: str
    definition_fingerprint: str
    tokenizer_sha256: str
    preprocessing: str
    dimensions: int
    pooling: str
    normalize: bool
    space_id: str


def admit(
    manifest_bytes,
    artifact_root,
    definition,
    tokenizer_definition,
    expected_inventory_id,
    *,
    timeout=30,
):
    """Verify actual files and bind them to the supported v1 identity policy."""
    try:
        start = time.monotonic()
        d, t = definition, tokenizer_definition

        def hex64(x):
            return type(x) is str and re.fullmatch(r"[0-9a-f]{64}", x) is not None

        if (
            type(d) is not EmbeddingDefinition
            or type(t) is not native_tokenizers.Definition
            or not hex64(expected_inventory_id)
            or not hex64(d.checkpoint_sha256)
            or type(d.checkpoint_revision) is not str
            or re.fullmatch(r"[0-9a-f]{40}", d.checkpoint_revision) is None
            or d.model_name != "BAAI/bge-m3"
            or d.pooling != "cls"
            or d.normalize is not True
            or type(d.dimensions) is not int
            or d.dimensions != 1024
            or d.query_prefix is not None
            or d.tokenizer_revision != d.checkpoint_revision
            or not hex64(t.sha256)
            or t.backend_version != "0.21.4"
            or t.role != "bge_representation"
            or t.model_revision != d.checkpoint_revision
            or t.preprocessing != "identity"
            or type(t.artifact) is not Path
            or type(timeout) not in (int, float)
            or not math.isfinite(timeout)
            or not 0 < timeout <= 30
        ):
            raise ValueError
        remaining = timeout - (time.monotonic() - start)
        inv = embedding_artifacts.verify_artifacts(manifest_bytes, artifact_root, timeout=remaining)
        weights = [x for x in inv.files if x.role == "weights"]
        tokenizer = next(x for x in inv.files if x.role == "tokenizer")
        if (
            inv.inventory_id != expected_inventory_id
            or inv.model_revision != d.checkpoint_revision
            or len(weights) != 1
            or weights[0].sha256 != d.checkpoint_sha256
            or tokenizer.sha256 != t.sha256
            or time.monotonic() - start >= timeout
        ):
            raise ValueError
        raw = native_tokenizers._read_artifact(t.artifact, 32_000_000)
        if (
            hashlib.sha256(raw).hexdigest() != tokenizer.sha256
            or time.monotonic() - start >= timeout
        ):
            raise ValueError
        fp = d.fingerprint()
        identity = {
            "version": 1,
            "inventory_id": inv.inventory_id,
            "definition_fingerprint": fp,
            "tokenizer_sha256": tokenizer.sha256,
            "preprocessing": "identity",
            "backend": "0.21.4",
            "role": "bge_representation",
        }
        space_id = hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return AdmittedSpace(
            inv.inventory_id, fp, tokenizer.sha256, "identity", 1024, "cls", True, space_id
        )
    except Exception:
        raise SpaceRefused("space admission refused") from None
