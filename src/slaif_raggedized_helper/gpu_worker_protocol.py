"""Private, bounded wire primitives for the owned GPU worker."""

import dataclasses
import email.parser
import hashlib
import json
import math
import os
import re
import select
import stat
import struct
import time
import tomllib
from pathlib import Path

from . import native_tokenizers

API = "gpu-owned-worker-v1"
SCHEMA = 1
PROFILE_HASH = "d3f47d3d2943759967a95694017f32e20b8a29ee7de4df790465a402bc17c334"
PINS = {"torch": "2.14.0+cu126", "transformers": "5.22.2", "tokenizers": "0.23.1",
        "safetensors": "0.8.0", "huggingface-hub": "1.31.0", "numpy": "2.5.4"}
CODE_FILES = ("__init__.py", "gpu_worker_protocol.py", "gpu_embedding_worker_main.py",
              "gpu_embedding_backend.py", "gpu_device_lease.py", "embedding_job_ownership.py",
              "cpu_embedding_backend.py", "embedding_artifacts.py", "embedding_space.py",
              "native_tokenizers.py", "schema.py", "_constraints.py")


@dataclasses.dataclass(frozen=True)
class Policy:
    max_rows: int = 8
    request_bytes: int = 2 * 1024**2
    response_bytes: int = 8 * 1024**2
    calls: int = 64
    total_input_bytes: int = 32 * 1024**2
    total_output_bytes: int = 256 * 1024**2
    io_seconds: int = 30

    def __post_init__(self):
        limits = (128, 2 * 1024**2, 8 * 1024**2, 1024, 32 * 1024**2,
                  256 * 1024**2, 120)
        if any(type(v) is not int or not 1 <= v <= cap
               for v, cap in zip(dataclasses.astuple(self), limits, strict=True)):
            raise ValueError("invalid policy")


def encode(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("ascii")


def parse(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def bad(_):
        raise ValueError

    value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs, parse_constant=bad)
    if encode(value) != raw:
        raise ValueError
    return value


def identity(value):
    return hashlib.sha256(encode(value)).hexdigest()


def policy_id(policy):
    return identity({"api": API, "schema": SCHEMA, "policy": dataclasses.asdict(policy)})


def code_id():
    root = Path(__file__).resolve().parent
    files = {name: hashlib.sha256(native_tokenizers._read_artifact(root / name, 131072)).hexdigest()
             for name in CODE_FILES}
    return identity({"api": API, "schema": SCHEMA, "files": files})


def _profile_path(directory):
    """Select only the package asset, fixed source tree, or fixed child capsule."""
    directory = Path(directory)
    assets = directory / "_worker_profiles"
    bundled = assets / "gpu" / "uv.lock"
    if os.path.lexists(assets) or directory.parent.name != "src":
        for component in (assets, assets / "gpu"):
            if os.path.islink(component):
                raise ValueError("symlinked profile directory")
        return bundled
    if directory == Path("/app/src/slaif_raggedized_helper"):
        return Path("/app/worker_profiles/gpu/uv.lock")
    with os.scandir(directory.parent) as entries:
        for count, entry in enumerate(entries, 1):
            if count > 4096:
                raise ValueError("source directory too large")
            if (entry.name.lower().startswith("slaif_raggedized_helper-")
                    and entry.name.lower().endswith(".dist-info")):
                raise ValueError("installed profile missing")
    project = directory.parent.parent
    config = tomllib.loads(native_tokenizers._read_artifact(
        project / "pyproject.toml", 65536).decode())
    if (directory.name != "slaif_raggedized_helper"
            or config.get("project", {}).get("name") != "slaif-raggedized-helper"):
        raise ValueError("unrecognized source layout")
    return project / "worker_profiles/gpu/uv.lock"


def profile(lock, packages):
    raw = native_tokenizers._read_artifact(lock, 65536)
    if hashlib.sha256(raw).hexdigest() != PROFILE_HASH:
        raise ValueError
    entries = tomllib.loads(raw.decode("utf-8"))["package"]
    pins = {p["name"]: p["version"] for p in entries if "registry" in p.get("source", {})}
    if len(pins) != 57 or any(pins.get(k) != v for k, v in PINS.items()):
        raise ValueError
    found = {}
    with os.scandir(packages) as entries:
        for count, entry in enumerate(entries, 1):
            if count > 4096 or entry.name.lower().endswith(".egg-info"):
                raise ValueError
            if not entry.name.lower().endswith(".dist-info"):
                continue
            if not stat.S_ISDIR(entry.stat(follow_symlinks=False).st_mode):
                raise ValueError
            raw = native_tokenizers._read_artifact(Path(entry.path) / "METADATA", 262144)
            metadata = email.parser.BytesParser().parsebytes(raw, headersonly=True)
            names, versions = metadata.get_all("Name", []), metadata.get_all("Version", [])
            if len(names) != 1 or len(versions) != 1:
                raise ValueError
            name = re.sub(r"[-_.]+", "-", names[0].lower())
            if name not in pins or name in found:
                raise ValueError
            found[name] = versions[0]
    if found != pins:
        raise ValueError
    return identity(pins)


def rows_ok(rows, vocab, limit):
    if type(rows) is not list or not 1 <= len(rows) <= limit:
        raise ValueError
    if any(type(row) is not list or not 2 <= len(row) <= 1024 for row in rows):
        raise ValueError
    if sum(map(len, rows)) > 131072 or any(
        type(token) is not int or not 0 <= token < vocab for row in rows for token in row
    ):
        raise ValueError


def output_ok(rows, count):
    if type(rows) not in (list, tuple) or len(rows) != count:
        raise ValueError
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 1024:
            raise ValueError
        for value in row:
            if type(value) is not float or not math.isfinite(value):
                raise ValueError
            try:
                if struct.unpack("!f", struct.pack("!f", value))[0] != value:
                    raise ValueError
            except OverflowError:
                raise ValueError from None


class Pipe:
    """Deadline-bound unbuffered pipe frames and cumulative byte accounting."""
    def __init__(self, read_fd, write_fd):
        self.r, self.w = read_fd, write_fd
        self.input = self.output = 0
        os.set_blocking(self.r, False)
        os.set_blocking(self.w, False)

    def read(self, cap, total, seconds):
        end = time.monotonic() + seconds
        data = bytearray()
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0 or not select.select([self.r], [], [], remaining)[0]:
                raise ValueError
            # One byte avoids consuming any part of the next frame.
            try:
                chunk = os.read(self.r, 1)
            except BlockingIOError:
                continue
            if not chunk:
                raise ValueError
            self.input += 1
            if self.input > total or len(data) + 1 > cap:
                raise ValueError
            if chunk == b"\n":
                return parse(bytes(data))
            data.extend(chunk)

    def write(self, value, cap, total, seconds):
        data = encode(value) + b"\n"
        if len(data) > cap or self.output + len(data) > total:
            raise ValueError
        end = time.monotonic() + seconds
        offset = 0
        while offset < len(data):
            remaining = end - time.monotonic()
            if remaining <= 0 or not select.select([], [self.w], [], remaining)[1]:
                raise ValueError
            try:
                n = os.write(self.w, data[offset:offset + 4096])
            except BlockingIOError:
                continue
            if n <= 0:
                raise ValueError
            offset += n
            self.output += n
