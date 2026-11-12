"""Owned, isolated CPU embedding worker with a bounded JSON protocol."""

import dataclasses
import hashlib
import email.parser
import re
import stat
import json
import math
import os
import selectors
import struct
import subprocess
import threading
import time
import tomllib
import uuid
from pathlib import Path

from . import cpu_embedding_backend, embedding_artifacts, embedding_space, native_tokenizers
from .schema import EmbeddingDefinition


class WorkerRefused(ValueError):
    """A worker operation was refused without disclosing input."""


@dataclasses.dataclass(frozen=True)
class Policy:
    max_rows: int = 8
    request_bytes: int = 2 * 1024 * 1024
    response_bytes: int = 8 * 1024 * 1024
    startup_seconds: int = 120
    forward_seconds: int = 30
    lifetime_seconds: int = 3600
    cpu_seconds: int = 600
    address_bytes: int = 16 * 1024**3
    calls: int = 1024
    total_input_bytes: int = 32 * 1024**2
    total_output_bytes: int = 256 * 1024**2

    def __post_init__(self):
        ceilings = (
            128,
            2 * 1024**2,
            8 * 1024**2,
            120,
            120,
            3600,
            600,
            16 * 1024**3,
            1024,
            32 * 1024**2,
            256 * 1024**2,
        )
        if any(
            type(v) is not int or not 1 <= v <= cap
            for v, cap in zip(dataclasses.astuple(self), ceilings, strict=True)
        ):
            raise WorkerRefused("invalid policy")


def _json(value):
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _parse(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def bad(_):
        raise ValueError

    return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=unique, parse_constant=bad)


def _lock(path):
    raw = native_tokenizers._read_artifact(path, 65536)
    if (
        hashlib.sha256(raw).hexdigest()
        != "7cf4c88943cc2b519ad18c0c28cbc2281f159a98704db172e1696ec5ae20b287"
    ):
        raise ValueError
    packages = tomllib.loads(raw.decode())["package"]
    pins = {p["name"]: p["version"] for p in packages if "registry" in p["source"]}
    if len(pins) != 38 or any(pins.get(k) != v for k, v in cpu_embedding_backend._PINS.items()):
        raise ValueError
    return pins


def _profile(lock, packages):
    pins = _lock(lock)
    found = {}
    count = 0
    with os.scandir(packages) as entries:
        for entry in entries:
            count += 1
            if count > 4096:
                raise ValueError
            name = entry.name.lower()
            if name.endswith(".egg-info"):
                raise ValueError
            if not name.endswith(".dist-info"):
                continue
            if not stat.S_ISDIR(entry.stat(follow_symlinks=False).st_mode):
                raise ValueError
            raw = native_tokenizers._read_artifact(Path(entry.path) / "METADATA", 262144)
            message = email.parser.BytesParser().parsebytes(raw, headersonly=True)
            names, versions = message.get_all("Name", []), message.get_all("Version", [])
            if len(names) != 1 or len(versions) != 1:
                raise ValueError
            name = re.sub(r"[-_.]+", "-", names[0].lower())
            if name not in pins or name in found or len(found) >= len(pins):
                raise ValueError
            found[name] = versions[0]
    if found != pins:
        raise ValueError
    return hashlib.sha256(_json(pins)).hexdigest()


_CODE_FILES = (
    "cpu_embedding_worker.py",
    "cpu_embedding_worker_main.py",
    "cpu_embedding_backend.py",
    "embedding_artifacts.py",
    "embedding_space.py",
    "native_tokenizers.py",
    "schema.py",
    "_constraints.py",
)


def _code_identity():
    directory = Path(__file__).resolve().parent
    hashes = {
        name: hashlib.sha256(native_tokenizers._read_artifact(directory / name, 131072)).hexdigest()
        for name in _CODE_FILES
    }
    return hashlib.sha256(_json({"schema": 1, "api": "cpu-worker-v1", "files": hashes})).hexdigest()


def _policy_identity(policy):
    return hashlib.sha256(
        _json({"schema": 1, "api": "cpu-worker-v1", "policy": dataclasses.asdict(policy)})
    ).hexdigest()


def _rows(rows, vocab, limit):
    if type(rows) not in (tuple, list) or not 1 <= len(rows) <= limit:
        raise ValueError
    if any(type(row) not in (tuple, list) or not 2 <= len(row) <= 1024 for row in rows):
        raise ValueError
    if sum(map(len, rows)) > 131072 or any(
        type(x) is not int or not 0 <= x < vocab for row in rows for x in row
    ):
        raise ValueError


def _output(rows, count):
    if type(rows) is not list or len(rows) != count:
        raise ValueError
    for row in rows:
        if type(row) is not list or len(row) != 1024:
            raise ValueError
        for x in row:
            if type(x) is not float or not math.isfinite(x):
                raise ValueError
            try:
                if struct.unpack("!f", struct.pack("!f", x))[0] != x:
                    raise ValueError
            except OverflowError:
                raise ValueError from None
    return tuple(tuple(row) for row in rows)


def _argv(runtime, root, lock, policy):
    if type(runtime) is not native_tokenizers.Runtime or runtime.python != "python3.12":
        raise ValueError
    # Reuse the accepted runtime validation and isolation scaffold.
    args = native_tokenizers._argv(runtime, root, lock)
    args[1] = f"--as={policy.address_bytes}"
    args[2] = f"--cpu={policy.cpu_seconds}"
    args[4] = "--fsize=8388608"
    for old, new in (("/artifact.json", "/artifacts"), ("/request.json", "/profile.lock")):
        args[args.index(old)] = new
    worker = Path(__file__).with_name("cpu_embedding_worker_main.py").resolve(strict=True)
    args[args.index("/worker.py") - 1] = str(worker)
    pos = args.index("--chdir")
    app = Path(__file__).resolve().parent.parent
    extra = ["--ro-bind", str(app), "/app"]
    for name, value in {
        "LOGNAME": "raggedized-worker",
        "USER": "raggedized-worker",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "RAYON_NUM_THREADS": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
    }.items():
        extra += ["--setenv", name, value]
    args[pos:pos] = extra
    args[-1:] = ["-I", "-S", "/worker.py"]
    return ["/usr/bin/timeout", "--signal=KILL", f"{policy.lifetime_seconds}s"] + args


class CPUEmbeddingWorker:
    """Own one process, borrowing the caller's protected artifact tree until close."""

    def __init__(
        self,
        manifest_bytes,
        private_artifact_root,
        definition,
        tokenizer_definition,
        expected_inventory_id,
        runtime,
        policy=None,
    ):
        self._child = None
        self._guard = threading.Lock()
        self._close_guard = threading.Lock()
        self._timer = None
        self._input = self._output = self._calls = 0
        self._buffer = bytearray()
        try:
            if policy is not None and type(policy) is not Policy:
                raise ValueError
            self.policy = (
                Policy()
                if policy is None
                else Policy(
                    **{
                        field.name: getattr(policy, field.name)
                        for field in dataclasses.fields(Policy)
                    }
                )
            )
            if (
                type(self.policy) is not Policy
                or type(manifest_bytes) is not bytes
                or len(manifest_bytes) > 2 * 1024**2
            ):
                raise ValueError
            if (
                type(definition) is not EmbeddingDefinition
                or type(tokenizer_definition) is not native_tokenizers.Definition
                or type(expected_inventory_id) is not str
                or len(expected_inventory_id) != 64
                or not isinstance(private_artifact_root, (str, Path))
                or type(runtime) is not native_tokenizers.Runtime
                or runtime.python != "python3.12"
                or any(
                    not isinstance(p, (str, Path))
                    or not 1 <= len(str(p)) <= 4096
                    or not os.path.isabs(p)
                    or os.path.normpath(str(p)) != str(p)
                    for p in (private_artifact_root, runtime.root, runtime.packages)
                )
                or not isinstance(tokenizer_definition.artifact, Path)
                or len(str(tokenizer_definition.artifact)) > 4096
                or (
                    definition.query_prefix is not None
                    and (
                        type(definition.query_prefix) is not str
                        or len(definition.query_prefix) > 128
                    )
                )
            ):
                raise ValueError
            metadata_strings = (
                definition.model_name,
                definition.checkpoint_revision,
                definition.checkpoint_sha256,
                definition.tokenizer_revision,
                definition.pooling,
                tokenizer_definition.sha256,
                tokenizer_definition.backend_version,
                tokenizer_definition.role,
                tokenizer_definition.model_revision,
                tokenizer_definition.preprocessing,
            )
            if any(type(value) is not str or len(value) > 256 for value in metadata_strings):
                raise ValueError
            if (
                definition.model_name != "BAAI/bge-m3"
                or definition.pooling != "cls"
                or definition.normalize is not True
                or definition.query_prefix is not None
                or type(definition.dimensions) is not int
                or definition.dimensions != 1024
                or not re.fullmatch(r"[0-9a-f]{40}", definition.checkpoint_revision)
                or definition.tokenizer_revision != definition.checkpoint_revision
                or not re.fullmatch(r"[0-9a-f]{64}", definition.checkpoint_sha256)
                or not re.fullmatch(r"[0-9a-f]{64}", expected_inventory_id)
                or not re.fullmatch(r"[0-9a-f]{64}", tokenizer_definition.sha256)
                or tokenizer_definition.backend_version != "0.21.4"
                or tokenizer_definition.role != "bge_representation"
                or tokenizer_definition.model_revision != definition.checkpoint_revision
                or tokenizer_definition.preprocessing != "identity"
            ):
                raise ValueError
            # Bound serializable metadata before filesystem admission or process startup.
            if (
                len(
                    _json(
                        {
                            "definition": definition.model_dump(),
                            "tokenizer": dataclasses.asdict(tokenizer_definition)
                            | {"artifact": ""},
                            "inventory": expected_inventory_id,
                        }
                    )
                )
                > 65536
            ):
                raise ValueError
            root = Path(private_artifact_root)
            lock = Path(__file__).resolve().parents[2] / "worker_profiles/cpu-v2/uv.lock"
            if type(runtime) is not native_tokenizers.Runtime or runtime.python != "python3.12":
                raise ValueError
            self.profile = _profile(lock, runtime.packages)
            self.code_fingerprint = _code_identity()
            self.policy_fingerprint = _policy_identity(self.policy)
            self.space = embedding_space.admit(
                manifest_bytes, root, definition, tokenizer_definition, expected_inventory_id
            )
            inv = embedding_artifacts.verify_artifacts(manifest_bytes, root)
            cpu_embedding_backend._closed_tree(root, inv.files)
            config = _parse(native_tokenizers._read_artifact(root / "config.json", 1048576))
            vocab = config.get("vocab_size") if type(config) is dict else None
            if type(vocab) is not int or not 1 <= vocab <= 10000000:
                raise ValueError
            startup = {
                "manifest": manifest_bytes.decode("utf-8"),
                "definition": definition.model_dump(),
                "tokenizer": {
                    k: v
                    for k, v in dataclasses.asdict(tokenizer_definition).items()
                    if k != "artifact"
                },
                "inventory": expected_inventory_id,
                "space": self.space.space_id,
                "profile": self.profile,
                "policy": dataclasses.asdict(self.policy),
                "policy_id": self.policy_fingerprint,
                "code_id": self.code_fingerprint,
            }
            argv = _argv(runtime, root, lock, self.policy)
            self._deadline = time.monotonic() + self.policy.lifetime_seconds
            self._child = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            self._timer = threading.Timer(self.policy.lifetime_seconds, self._shutdown)
            self._timer.daemon = True
            self._timer.start()
            os.set_blocking(self._child.stdin.fileno(), False)
            os.set_blocking(self._child.stdout.fileno(), False)
            reply = self._exchange(startup, self.policy.startup_seconds)
            if (
                type(reply) is not dict
                or set(reply)
                != {
                    "ready",
                    "space",
                    "definition",
                    "profile",
                    "vocab",
                    "contract",
                    "policy_id",
                    "code_id",
                }
                or reply["ready"] is not True
                or reply["space"] != self.space.space_id
                or reply["definition"] != self.space.definition_fingerprint
                or reply["profile"] != self.profile
                or reply["policy_id"] != self.policy_fingerprint
                or reply["code_id"] != self.code_fingerprint
                or reply["contract"] != "cpu-fp32-cls"
                or type(reply["vocab"]) is not int
                or reply["vocab"] != vocab
            ):
                raise ValueError
            self.vocab_size = reply["vocab"]
        except BaseException as error:
            try:
                self._shutdown()
            except BaseException as cleanup_error:
                if not isinstance(error, Exception):
                    error.add_note("worker cleanup refused")
                elif not isinstance(cleanup_error, Exception):
                    raise
            if not isinstance(error, Exception):
                raise
            raise WorkerRefused("worker refused") from None

    def _exchange(self, value, timeout):
        wire = _json(value) + b"\n"
        if (
            len(wire) > self.policy.request_bytes
            or self._input + len(wire) > self.policy.total_input_bytes
        ):
            raise ValueError
        deadline = min(self._deadline, time.monotonic() + timeout)
        child = self._child
        sent = 0
        with selectors.DefaultSelector() as sel:
            sel.register(child.stdin, selectors.EVENT_WRITE)
            sel.register(child.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError
                events = sel.select(remaining)
                if not events:
                    raise ValueError
                for key, _ in events:
                    if key.fileobj is child.stdin:
                        sent += os.write(child.stdin.fileno(), wire[sent:])
                        if sent == len(wire):
                            sel.unregister(child.stdin)
                            self._input += sent
                    else:
                        part = os.read(
                            child.stdout.fileno(),
                            min(65536, self.policy.response_bytes + 1 - len(self._buffer)),
                        )
                        if not part:
                            raise ValueError
                        self._buffer.extend(part)
                        self._output += len(part)
                        if (
                            len(self._buffer) > self.policy.response_bytes
                            or self._output > self.policy.total_output_bytes
                        ):
                            raise ValueError
                        if b"\n" in self._buffer:
                            if (
                                sent != len(wire)
                                or self._buffer.count(b"\n") != 1
                                or not self._buffer.endswith(b"\n")
                            ):
                                raise ValueError
                            data = bytes(self._buffer[:-1])
                            self._buffer.clear()
                            result = _parse(data)
                            if time.monotonic() >= deadline:
                                raise ValueError
                            return result

    def forward_cls(self, sequences):
        if not self._guard.acquire(blocking=False):
            raise WorkerRefused("worker busy")
        try:
            if self._child is None or self._calls >= self.policy.calls:
                raise ValueError
            _rows(sequences, self.vocab_size, self.policy.max_rows)
            batch = [list(row) for row in sequences]
            digest = hashlib.sha256(_json(batch)).hexdigest()
            nonce = uuid.uuid4().hex
            operation_deadline = min(self._deadline, time.monotonic() + self.policy.forward_seconds)
            reply = self._exchange(
                {"nonce": nonce, "digest": digest, "rows": batch}, self.policy.forward_seconds
            )
            if (
                type(reply) is not dict
                or set(reply) != {"nonce", "digest", "space", "profile", "rows"}
                or reply["nonce"] != nonce
                or reply["digest"] != digest
                or reply["space"] != self.space.space_id
                or reply["profile"] != self.profile
            ):
                raise ValueError
            result = _output(reply["rows"], len(batch))
            if time.monotonic() >= operation_deadline:
                raise ValueError
            self._calls += 1
            return result
        except BaseException as error:
            try:
                self._shutdown()
            except BaseException as cleanup_error:
                if not isinstance(error, Exception):
                    error.add_note("worker cleanup refused")
                elif not isinstance(cleanup_error, Exception):
                    raise
            if not isinstance(error, Exception):
                raise
            raise WorkerRefused("worker refused") from None
        finally:
            self._guard.release()

    def _shutdown(self):
        with self._close_guard:
            child = self._child
            timer, self._timer = self._timer, None
            first_interrupt = None
            failed = False

            def record(error):
                nonlocal first_interrupt, failed
                failed = True
                if not isinstance(error, Exception) and first_interrupt is None:
                    first_interrupt = error

            if timer is not None:
                try:
                    timer.cancel()
                except BaseException as error:
                    record(error)
            if child is not None:
                streams_closed = True
                for stream in (child.stdin, child.stdout):
                    if stream is None:
                        continue
                    for _ in range(2):
                        try:
                            if not getattr(stream, "closed", False):
                                stream.close()
                            break
                        except BaseException as error:
                            record(error)
                    else:
                        streams_closed = False
                reaped = False
                try:
                    reaped = child.poll() is not None
                except BaseException as error:
                    record(error)
                if not reaped:
                    try:
                        child.terminate()
                    except ProcessLookupError:
                        pass
                    except BaseException as error:
                        record(error)
                    try:
                        child.wait(timeout=0.4)
                        reaped = True
                    except subprocess.TimeoutExpired:
                        pass
                    except BaseException as error:
                        record(error)
                    if not reaped:
                        try:
                            child.kill()
                        except ProcessLookupError:
                            pass
                        except BaseException as error:
                            record(error)
                        for _ in range(2):
                            try:
                                child.wait(timeout=0.5)
                                reaped = True
                                break
                            except BaseException as error:
                                record(error)
                if reaped and streams_closed:
                    self._child = None
                else:
                    failed = True
            if first_interrupt is not None:
                if child is not None and (not reaped or not streams_closed):
                    first_interrupt.add_note("worker cleanup refused")
                raise first_interrupt
            if failed:
                raise WorkerRefused("worker cleanup refused") from None

    def close(self):
        if not self._guard.acquire(blocking=False):
            raise WorkerRefused("worker busy")
        try:
            self._shutdown()
        except BaseException as error:
            if not isinstance(error, Exception):
                raise
            raise WorkerRefused("worker cleanup refused") from None
        finally:
            self._guard.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.close()
        except BaseException as error:
            if exc is None:
                if not isinstance(error, Exception):
                    raise
                raise WorkerRefused("worker cleanup refused") from None
            exc.add_note("worker cleanup refused")
        return False
