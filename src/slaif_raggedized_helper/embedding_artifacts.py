"""Bounded, local-only verification of a caller-selected BGE-M3 artifact tree."""

import hashlib
import json
import math
import os
import re
import stat
import time
from dataclasses import dataclass


class ArtifactRefused(ValueError):
    """Input or filesystem did not satisfy the artifact contract (no input echoed)."""


_FIXED = {
    "config": "config.json",
    "tokenizer": "tokenizer.json",
    "tokenizer_config": "tokenizer_config.json",
    "special_tokens_map": "special_tokens_map.json",
    "modules": "modules.json",
    "pooling": "1_Pooling/config.json",
    "sentence_bert_config": "sentence_bert_config.json",
    "sentence_transformers_config": "config_sentence_transformers.json",
}
_HEX = re.compile(r"^[0-9a-f]+$")


@dataclass(frozen=True)
class VerifiedFile:
    role: str
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class VerifiedInventory:
    model_name: str
    model_revision: str
    files: tuple[VerifiedFile, ...]
    inventory_id: str
    schema: int = 1
    checkpoint_format: str = "safetensors"


def _fail():
    raise ArtifactRefused("artifact verification refused")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def _json(data):
    try:
        value = json.loads(
            data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=lambda _: _fail()
        )
        _unicode(value)
        return value
    except (ValueError, UnicodeError, RecursionError):
        _fail()


def _unicode(value):
    if isinstance(value, str):
        value.encode("utf-8")
    elif isinstance(value, dict):
        for key, item in value.items():
            _unicode(key)
            _unicode(item)
    elif isinstance(value, list):
        for item in value:
            _unicode(item)


def _safe_json(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "auto_map":
                _fail()
            _safe_json(v)
    elif isinstance(value, list):
        for v in value:
            _safe_json(v)
    elif isinstance(value, float) and not math.isfinite(value):
        _fail()


def _digest(value, length):
    return isinstance(value, str) and len(value) == length and bool(_HEX.fullmatch(value))


def _path(value):
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 4096:
        _fail()
    if "\x00" in value or "\\" in value or ":" in value or value.startswith("/"):
        _fail()
    parts = value.split("/")
    if any(p in ("", ".", "..") or len(p.encode("utf-8")) > 255 for p in parts):
        _fail()
    return parts


def _admit(data):
    if not isinstance(data, bytes) or len(data) > 256 * 1024:
        _fail()
    manifest = _json(data)
    if not isinstance(manifest, dict):
        _fail()
    schema = manifest.get("schema")
    if type(schema) is not int or schema not in (1, 2):
        _fail()
    expected = {
        "schema",
        "model_name",
        "model_revision",
        "files",
    }
    if schema == 2:
        expected.add("checkpoint_format")
    if set(manifest) != expected:
        _fail()
    fmt = manifest.get("checkpoint_format", "safetensors")
    if fmt not in ("safetensors", "pytorch-state-dict"):
        _fail()
    if manifest["model_name"] != "BAAI/bge-m3" or not _digest(manifest["model_revision"], 40):
        _fail()
    files = manifest["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= 32:
        _fail()
    result, roles, paths, total = [], set(), set(), 0
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"role", "path", "sha256", "size"}:
            _fail()
        role, path, digest, size = (entry[k] for k in ("role", "path", "sha256", "size"))
        _path(path)
        if not isinstance(role, str) or role not in (*_FIXED, "weights"):
            _fail()
        if (role != "weights" and (role in roles or path != _FIXED[role])) or path in paths:
            _fail()
        if role == "weights":
            if schema == 1 and not path.endswith(".safetensors"):
                _fail()
            if schema == 2 and (role in roles or path != {"safetensors": "model.safetensors", "pytorch-state-dict": "pytorch_model.bin"}[fmt]):
                _fail()
        if not _digest(digest, 64) or type(size) is not int or not 0 <= size <= 4 * 1024**3:
            _fail()
        if role == "tokenizer" and size > 32 * 1024**2:
            _fail()
        if role not in ("tokenizer", "weights") and size > 65536:
            _fail()
        total += size
        if total > 8 * 1024**3:
            _fail()
        roles.add(role)
        paths.add(path)
        result.append(VerifiedFile(role, path, digest, size))
    if roles != set(_FIXED) | {"weights"}:
        _fail()
    return manifest["model_revision"], tuple(sorted(result, key=lambda f: f.path)), schema, fmt


def _secure(st, directory):
    if (
        not (stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode))
        or st.st_mode & 0o022
        or st.st_uid not in (0, os.geteuid())
    ):
        _fail()


def _signature(st):
    return (
        st.st_dev,
        st.st_ino,
        st.st_mode,
        st.st_uid,
        st.st_gid,
        st.st_size,
        st.st_mtime_ns,
        st.st_ctime_ns,
    )


def _root(path):
    # Open each component without following links, including in caller-selected root.
    path = os.path.abspath(os.fspath(path))
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in path.split("/")[1:]:
            if component:
                nxt = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = nxt
        _secure(os.fstat(fd), True)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open_file(root, path):
    parts = _path(path)
    fd = os.dup(root)
    try:
        for part in parts[:-1]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
            _secure(os.fstat(fd), True)
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            _secure(os.fstat(file_fd), False)
        except BaseException:
            os.close(file_fd)
            raise
        return file_fd
    finally:
        os.close(fd)


def _semantics(config):
    for obj in config.values():
        _safe_json(obj)
    c, t, p, s = (
        config[k] for k in ("config", "tokenizer_config", "pooling", "sentence_bert_config")
    )
    if not all(isinstance(x, dict) for x in (c, t, p, s)):
        _fail()
    if (
        c.get("model_type") != "xlm-roberta"
        or type(c.get("hidden_size")) is not int
        or c["hidden_size"] != 1024
        or type(t.get("model_max_length")) is not int
        or t["model_max_length"] != 8192
        or type(s.get("max_seq_length")) is not int
        or s["max_seq_length"] != 8192
        or s.get("do_lower_case") is not False
        or type(p.get("word_embedding_dimension")) is not int
        or p["word_embedding_dimension"] != 1024
        or p.get("pooling_mode_cls_token") is not True
    ):
        _fail()
    if any(
        v is not False
        for k, v in p.items()
        if k.startswith("pooling_mode_") and k != "pooling_mode_cls_token"
    ):
        _fail()
    expected = [
        {"idx": 0, "name": "0", "path": "", "type": "sentence_transformers.models.Transformer"},
        {
            "idx": 1,
            "name": "1",
            "path": "1_Pooling",
            "type": "sentence_transformers.models.Pooling",
        },
        {
            "idx": 2,
            "name": "2",
            "path": "2_Normalize",
            "type": "sentence_transformers.models.Normalize",
        },
    ]
    if (
        config["modules"] != expected
        or not isinstance(config["modules"], list)
        or any(type(x.get("idx")) is not int for x in config["modules"] if isinstance(x, dict))
    ):
        _fail()
    if c.get("architectures", ["XLMRobertaModel"]) != ["XLMRobertaModel"] or t.get(
        "tokenizer_class", "XLMRobertaTokenizer"
    ) not in ("XLMRobertaTokenizer", "XLMRobertaTokenizerFast"):
        _fail()
    if not isinstance(config["special_tokens_map"], dict) or not isinstance(
        config["sentence_transformers_config"], dict
    ):
        _fail()


def _verify_artifacts(
    manifest_bytes: bytes, artifact_root, *, timeout: float = 30
) -> VerifiedInventory:
    """Verify bytes and semantics beneath a trusted root; raise ArtifactRefused on failure."""
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 30:
        _fail()
    deadline = time.monotonic() + timeout
    revision, files, schema, fmt = _admit(manifest_bytes)

    def check_time():
        if time.monotonic() >= deadline:
            _fail()

    root = None
    try:
        check_time()
        root = _root(artifact_root)
        root_signature = _signature(os.fstat(root))
        signatures, configs = {}, {}
        for item in files:
            check_time()
            fd = _open_file(root, item.path)
            try:
                before = os.fstat(fd)
                if before.st_size != item.size:
                    _fail()
                digest, count, chunks = hashlib.sha256(), 0, []
                while True:
                    check_time()
                    chunk = os.read(fd, 65536)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > item.size:
                        _fail()
                    digest.update(chunk)
                    if item.role not in ("weights", "tokenizer"):
                        chunks.append(chunk)
                if (
                    count != item.size
                    or digest.hexdigest() != item.sha256
                    or _signature(os.fstat(fd)) != _signature(before)
                ):
                    _fail()
                signatures[item.path] = _signature(before)
                if chunks or item.role not in ("weights", "tokenizer"):
                    configs[item.role] = _json(b"".join(chunks))
            finally:
                os.close(fd)
        _semantics(configs)
        # Reopen root and every named file to detect replacement after its read.
        check_time()
        again = _root(artifact_root)
        try:
            if _signature(os.fstat(again)) != root_signature:
                _fail()
            for item in files:
                check_time()
                fd = _open_file(again, item.path)
                try:
                    if _signature(os.fstat(fd)) != signatures[item.path]:
                        _fail()
                finally:
                    os.close(fd)
        finally:
            os.close(again)
        canonical = {
            "schema": 1,
            "model_name": "BAAI/bge-m3",
            "model_revision": revision,
            "files": [vars(f) for f in files],
        }
        if schema == 2:
            canonical["schema"] = 2
            canonical["checkpoint_format"] = fmt
        fingerprint = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        ).hexdigest()
        return VerifiedInventory("BAAI/bge-m3", revision, files, fingerprint, schema, fmt)
    except ArtifactRefused:
        raise
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        _fail()
    finally:
        if root is not None:
            os.close(root)


def verify_artifacts(
    manifest_bytes: bytes, artifact_root, *, timeout: float = 30
) -> VerifiedInventory:
    """Verify a local inventory, refusing invalid input without exposing it."""
    try:
        return _verify_artifacts(manifest_bytes, artifact_root, timeout=timeout)
    except Exception:
        raise ArtifactRefused("artifact verification refused") from None
