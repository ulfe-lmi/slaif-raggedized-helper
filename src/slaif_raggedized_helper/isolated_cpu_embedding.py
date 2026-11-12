"""Owned isolated CPU embedding composition; callers must establish content rights."""

import dataclasses
import hashlib
import json
import math
import os
import re
import threading
import time
from pathlib import Path

from . import cpu_embedding_worker as cpu
from . import cpu_execution_contract
from . import embedding_staging, embedding_tokenizer, embedding_vectors, native_tokenizers
from .schema import EmbeddingDefinition, EmbeddingExecution, fingerprint


class SessionRefused(ValueError):
    """Input-free refusal, optionally retaining the owner of pending cleanup."""

    def __init__(self, message="embedding session refused", *, owner=None):
        super().__init__(message)
        self.owner = owner
        self.pending = owner is not None


@dataclasses.dataclass(frozen=True)
class EncodedBatch:
    vectors: embedding_vectors.NormalizedVectors
    receipts: tuple
    space_id: str
    definition_fingerprint: str
    intended_execution_fingerprint: str
    execution_record: bytes
    execution_fingerprint: str


def _path(value):
    if type(value) not in (str, type(Path())):
        raise ValueError
    if type(value) is type(Path()):
        parts = value._raw_paths
        if (
            type(parts) is not list
            or len(parts) > 4096
            or any(type(part) is not str or len(part) > 4096 for part in parts)
            or sum(map(len, parts)) > 4096
        ):
            raise ValueError
    value = os.fspath(value)
    if (
        type(value) is not str
        or not 1 <= len(value) <= 4096
        or not os.path.isabs(value)
        or os.path.normpath(value) != value
        or len(os.fsencode(value)) > 4096
    ):
        raise ValueError

    return value


_CPU_FIELDS = (
    "max_rows",
    "request_bytes",
    "response_bytes",
    "startup_seconds",
    "forward_seconds",
    "lifetime_seconds",
    "cpu_seconds",
    "address_bytes",
    "calls",
    "total_input_bytes",
    "total_output_bytes",
)
_NATIVE_INTS = (
    "max_artifact_bytes",
    "max_request_bytes",
    "max_chars",
    "max_response_bytes",
    "max_ids",
    "max_calls",
    "max_input_bytes",
    "max_output_bytes",
)
_NATIVE_TIMES = ("lifetime_seconds", "startup_seconds", "request_seconds")


def _cpu_values(policy):
    if type(policy) is not cpu.Policy:
        raise ValueError
    values = tuple(getattr(policy, name) for name in _CPU_FIELDS)
    if any(type(value) is not int for value in values):
        raise ValueError
    cpu.Policy(**dict(zip(_CPU_FIELDS, values, strict=True)))
    return values


def _native_values(policy):
    if type(policy) is not embedding_tokenizer.Policy:
        raise ValueError
    values = tuple(getattr(policy, name) for name in _NATIVE_INTS + _NATIVE_TIMES)
    if any(type(value) is not int for value in values[: len(_NATIVE_INTS)]) or any(
        type(value) not in (int, float) or not math.isfinite(value)
        for value in values[len(_NATIVE_INTS) :]
    ):
        raise ValueError
    embedding_tokenizer.Policy(**dict(zip(_NATIVE_INTS + _NATIVE_TIMES, values, strict=True)))
    return values


def _runtime_values(runtime):
    if (
        type(runtime) is not native_tokenizers.Runtime
        or type(runtime.python) is not str
        or runtime.python != "python3.12"
    ):
        raise ValueError
    return (_path(runtime.root), _path(runtime.packages), runtime.python)


def _definition_values(d):
    if (
        type(d) is not EmbeddingDefinition
        or type(d.model_name) is not str
        or d.model_name != "BAAI/bge-m3"
        or type(d.pooling) is not str
        or d.pooling != "cls"
        or d.normalize is not True
        or d.query_prefix is not None
        or type(d.dimensions) is not int
        or d.dimensions != 1024
        or type(d.checkpoint_revision) is not str
        or not re.fullmatch(r"[0-9a-f]{40}", d.checkpoint_revision)
        or type(d.tokenizer_revision) is not str
        or d.tokenizer_revision != d.checkpoint_revision
        or type(d.checkpoint_sha256) is not str
        or not re.fullmatch(r"[0-9a-f]{64}", d.checkpoint_sha256)
    ):
        raise ValueError
    return (
        d.model_name,
        d.pooling,
        d.normalize,
        d.dimensions,
        d.checkpoint_revision,
        d.tokenizer_revision,
        d.checkpoint_sha256,
    )


def _token_values(t, revision):
    if (
        type(t) is not native_tokenizers.Definition
        or type(t.sha256) is not str
        or not re.fullmatch(r"[0-9a-f]{64}", t.sha256)
        or type(t.backend_version) is not str
        or t.backend_version != "0.21.4"
        or type(t.role) is not str
        or t.role != "bge_representation"
        or type(t.model_revision) is not str
        or t.model_revision != revision
        or type(t.preprocessing) is not str
        or t.preprocessing != "identity"
    ):
        raise ValueError
    return (
        _path(t.artifact),
        t.sha256,
        t.backend_version,
        t.role,
        t.model_revision,
        t.preprocessing,
    )


def _json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


class IsolatedCPUEmbeddingSession:
    """Own a stage, renewable tokenizer, and one resident CPU worker."""

    def __init__(
        self,
        manifest_bytes,
        artifact_root,
        definition,
        tokenizer_definition,
        expected_inventory_id,
        tokenizer_runtime,
        cpu_runtime,
        *,
        worker_policy=None,
        parent=None,
    ):
        try:
            if (
                type(manifest_bytes) is not bytes
                or not 1 <= len(manifest_bytes) <= 2 * 1024**2
                or type(definition) is not EmbeddingDefinition
                or type(tokenizer_definition) is not native_tokenizers.Definition
                or type(expected_inventory_id) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", expected_inventory_id)
                or type(tokenizer_runtime) is not native_tokenizers.Runtime
                or type(cpu_runtime) is not native_tokenizers.Runtime
                or type(tokenizer_runtime.python) is not str
                or type(cpu_runtime.python) is not str
                or tokenizer_runtime.python != "python3.12"
                or cpu_runtime.python != "python3.12"
                or (worker_policy is not None and type(worker_policy) is not cpu.Policy)
            ):
                raise ValueError
            policy_values = _cpu_values(cpu.Policy() if worker_policy is None else worker_policy)
            policy = cpu.Policy(**dict(zip(_CPU_FIELDS, policy_values, strict=True)))
            root_value = _path(artifact_root)
            if parent is not None:
                _path(parent)
            d, t = definition, tokenizer_definition
            definition_values = _definition_values(d)
            token_values = _token_values(t, d.checkpoint_revision)
            runtime_values = (_runtime_values(tokenizer_runtime), _runtime_values(cpu_runtime))
            if root_value == "/" or token_values[0] != root_value + "/tokenizer.json":
                raise ValueError
            self._args = (
                manifest_bytes,
                artifact_root,
                definition,
                tokenizer_definition,
                expected_inventory_id,
                parent,
            )
            self._native_runtime, self._cpu_runtime, self._policy = (
                tokenizer_runtime,
                cpu_runtime,
                policy,
            )
            self.definition = definition
            self._definition_snapshot = definition_values
            self._token_snapshot = token_values
            self._runtime_snapshot = runtime_values
            self._policy_snapshot = policy_values
            self.intended_execution_fingerprint = EmbeddingExecution(
                definition=definition, device="cpu", dtype="fp32"
            ).fingerprint()
        except Exception:
            raise SessionRefused() from None
        self._lock = threading.Lock()
        self._pid = os.getpid()
        self._state = "new"
        self._stage = self._tokenizer = self._worker = None
        self._stage_failed = False

    def _validate_state(self):
        if (
            _definition_values(self.definition) != self._definition_snapshot
            or _token_values(self._args[3], self.definition.checkpoint_revision)
            != self._token_snapshot
            or (_runtime_values(self._native_runtime), _runtime_values(self._cpu_runtime))
            != self._runtime_snapshot
            or _cpu_values(self._policy) != self._policy_snapshot
        ):
            raise ValueError

    def _acquire(self):
        if os.getpid() != self._pid:
            raise SessionRefused()
        if not self._lock.acquire(blocking=False):
            raise SessionRefused("embedding session busy")

    def _cleanup(self):
        self._state = "closed"
        failed = False
        self._cleanup_interrupt = None

        def remember(error):
            nonlocal failed
            failed = True
            if not isinstance(error, Exception) and self._cleanup_interrupt is None:
                self._cleanup_interrupt = error

        if self._tokenizer is not None:
            try:
                self._tokenizer.close()
                self._tokenizer = None
            except BaseException as error:
                remember(error)
        if self._worker is not None:
            try:
                self._worker.close()
            except BaseException as error:
                remember(error)
            if getattr(self._worker, "_child", None) is None:
                self._worker = None
        if (self._worker is None and self._tokenizer is None and self._stage is not None
                and not self._stage_failed):
            try:
                self._stage.__exit__(None, None, None)
                self._stage = None
            except BaseException as error:
                self._stage_failed = True
                remember(error)
        return (
            failed or self._worker is not None or self._tokenizer is not None or self._stage_failed
        )

    def _fail(self, error):
        pending = self._cleanup()
        if not isinstance(error, Exception):
            if pending:
                error.add_note("embedding session cleanup pending; owner retained")
                error.cleanup_owner = self
            raise error
        if self._cleanup_interrupt is not None:
            self._cleanup_interrupt.add_note("embedding session cleanup pending")
            self._cleanup_interrupt.cleanup_owner = self
            raise self._cleanup_interrupt
        raise SessionRefused(owner=self if pending else None) from None

    def __enter__(self):
        self._acquire()
        try:
            if self._state != "new":
                raise SessionRefused()
            try:
                self._validate_state()
                manifest, root, definition, token, inventory, parent = self._args
                self._stage = embedding_staging.stage(
                    manifest, root, definition, token, inventory, parent=parent
                )
                try:
                    staged = self._stage.__enter__()
                except BaseException as error:
                    if (
                        type(error) is embedding_staging.StagingRefused
                        and "staging cleanup failed" not in getattr(error, "__notes__", ())
                    ):
                        self._stage = None
                    else:
                        self._stage_failed = True
                    raise
                self._token_definition = dataclasses.replace(
                    token, artifact=staged.path / "tokenizer.json"
                )
                self._tokenizer = embedding_tokenizer.TokenIDSession.__new__(
                    embedding_tokenizer.TokenIDSession
                )
                embedding_tokenizer.TokenIDSession.__init__(
                    self._tokenizer, self._token_definition, self._native_runtime
                )
                self._worker = cpu.CPUEmbeddingWorker.__new__(cpu.CPUEmbeddingWorker)
                cpu.CPUEmbeddingWorker.__init__(
                    self._worker,
                    staged.manifest_bytes,
                    staged.path,
                    definition,
                    self._token_definition,
                    inventory,
                    self._cpu_runtime,
                    self._policy,
                )
                self.space = staged.space
                if (
                    self._worker.space != self.space
                    or self.space.definition_fingerprint != definition.fingerprint()
                ):
                    raise ValueError
                self._identity = self._worker_identity()
                self._native_policy_snapshot = _native_values(self._tokenizer._policy)
                self.execution_record, self.execution_fingerprint = cpu_execution_contract._record(
                    self.space, definition, token, self._identity, self._tokenizer._policy
                )
                self._record_snapshot = self.execution_record
                self._fingerprint_snapshot = self.execution_fingerprint
                self._state = "open"
                return self
            except BaseException as error:
                self._fail(error)
        finally:
            self._lock.release()

    def _worker_identity(self):
        w = self._worker
        identity = {
            "space": w.space.space_id,
            "definition": w.space.definition_fingerprint,
            "profile": w.profile,
            "code": w.code_fingerprint,
            "policy": w.policy_fingerprint,
        }
        if any(
            type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None
            for key, value in identity.items()
            if key in ("profile", "code", "policy", "space")
        ) or any(
            type(identity[key]) is not str
            or re.fullmatch(r"sha256:[0-9a-f]{64}", identity[key]) is None
            for key in ("definition",)
        ):
            raise ValueError
        return identity

    def close(self):
        self._acquire()
        try:
            pending = self._cleanup()
            if self._cleanup_interrupt is not None:
                self._cleanup_interrupt.add_note("embedding session cleanup pending")
                self._cleanup_interrupt.cleanup_owner = self
                raise self._cleanup_interrupt
            if pending:
                raise SessionRefused("embedding session cleanup pending", owner=self)
        finally:
            self._lock.release()

    def __exit__(self, exc_type, exc, tb):
        try:
            self.close()
        except BaseException as cleanup_error:
            if exc is None or (isinstance(exc, Exception)
                               and not isinstance(cleanup_error, Exception)):
                raise
            exc.add_note("embedding session cleanup pending")
            exc.cleanup_owner = self
        return False

    def _preflight(self, texts):
        if type(texts) not in (list, tuple) or not 1 <= len(texts) <= self._policy.max_rows:
            raise ValueError
        if any(type(text) is not str or len(text) > 100000 for text in texts):
            raise ValueError
        if sum(len(text) for text in texts) > 1000000:
            raise ValueError
        sizes = []
        for text in texts:
            text.encode("utf-8", "strict")
            sizes.append(
                len(
                    json.dumps(
                        {"text": text, "nonce": "0" * 32}, ensure_ascii=True, separators=(",", ":")
                    ).encode()
                )
                + 1
            )
        if any(size > 200000 for size in sizes) or sum(sizes) > 4000000:
            raise ValueError
        return sizes

    def _renew(self, sizes):
        worker = self._tokenizer
        p = worker._policy
        if (
            worker._deadline - time.monotonic() <= 5 + 2 * len(sizes)
            or worker._calls + len(sizes) > p.max_calls
            or worker._input + sum(sizes) > p.max_input_bytes
            or worker._output + len(sizes) * (p.max_response_bytes + 1) > p.max_output_bytes
        ):
            worker.close()
            self._tokenizer = None
            self._tokenizer = embedding_tokenizer.TokenIDSession.__new__(
                embedding_tokenizer.TokenIDSession
            )
            embedding_tokenizer.TokenIDSession.__init__(
                self._tokenizer, self._token_definition, self._native_runtime
            )

    def _receipt(self, receipt, text):
        d = self._token_definition
        digest = hashlib.sha256(
            json.dumps([text, None], ensure_ascii=True, separators=(",", ":")).encode()
        ).hexdigest()
        if (
            type(receipt) is not embedding_tokenizer.TokenIDReceipt
            or type(receipt.ids) is not tuple
            or type(receipt.count) is not int
            or receipt.count != len(receipt.ids)
            or not 2 <= receipt.count <= 1024
            or any(type(i) is not int or not 0 <= i < self._worker.vocab_size for i in receipt.ids)
            or receipt.artifact_sha256 != d.sha256
            or receipt.backend_version != d.backend_version
            or receipt.role != d.role
            or receipt.model_revision != d.model_revision
            or receipt.preprocessing != d.preprocessing
            or receipt.input_sha256 != digest
            or type(receipt.nonce) is not str
            or not re.fullmatch(r"[0-9a-f]{32}", receipt.nonce)
            or receipt.serialization != "utf8-json-v1;no-truncation;no-padding;special-tokens"
        ):
            raise ValueError

    def encode(self, texts):
        self._acquire()
        try:
            if self._state != "open":
                raise SessionRefused()
            try:
                self._validate_state()
                if _native_values(
                    self._tokenizer._policy
                ) != self._native_policy_snapshot or _token_values(
                    self._tokenizer._definition, self.definition.checkpoint_revision
                ) != _token_values(self._token_definition, self.definition.checkpoint_revision):
                    raise ValueError
                sizes = self._preflight(texts)
                texts = tuple(texts)
                self._renew(sizes)
                if _native_values(self._tokenizer._policy) != self._native_policy_snapshot:
                    raise ValueError
                receipts = tuple(self._tokenizer.encode(text) for text in texts)
                for receipt, text in zip(receipts, texts, strict=True):
                    self._receipt(receipt, text)
                rows = self._worker.forward_cls([receipt.ids for receipt in receipts])
                vectors = embedding_vectors.normalize_rows(rows)
                if (
                    len(vectors.rows) != len(texts)
                    or vectors.policy_id != embedding_vectors.POLICY_ID
                    or self._worker_identity() != self._identity
                    or self._worker.space != self.space
                    or self.space.definition_fingerprint != self.definition.fingerprint()
                    or self.intended_execution_fingerprint
                    != EmbeddingExecution(
                        definition=self.definition, device="cpu", dtype="fp32"
                    ).fingerprint()
                    or _cpu_values(self._policy) != self._policy_snapshot
                    or _native_values(self._tokenizer._policy) != self._native_policy_snapshot
                    or _token_values(
                        self._tokenizer._definition, self.definition.checkpoint_revision
                    )
                    != _token_values(self._token_definition, self.definition.checkpoint_revision)
                    or self._token_definition.sha256 != self._token_snapshot[1]
                    or _definition_values(self.definition) != self._definition_snapshot
                    or (_runtime_values(self._native_runtime), _runtime_values(self._cpu_runtime))
                    != self._runtime_snapshot
                    or hashlib.sha256(
                        native_tokenizers._read_artifact(
                            Path(__file__).with_name("embedding_tokenizer_worker.py"), 131072
                        )
                    ).hexdigest()
                    != json.loads(self._record_snapshot)["native"]["worker_sha256"]
                    or self.execution_record != self._record_snapshot
                    or self.execution_fingerprint != self._fingerprint_snapshot
                    or self.execution_fingerprint
                    != fingerprint(
                        {
                            "kind": "isolated-cpu-embedding-execution-v2",
                            **json.loads(self.execution_record),
                        }
                    )
                    or cpu._policy_identity(self._worker.policy) != self._identity["policy"]
                    or cpu_execution_contract._bridge()
                    != json.loads(self._record_snapshot)["bridge"]
                ):
                    raise ValueError
                return EncodedBatch(
                    vectors,
                    receipts,
                    self.space.space_id,
                    self.definition.fingerprint(),
                    self.intended_execution_fingerprint,
                    self.execution_record,
                    self.execution_fingerprint,
                )
            except BaseException as error:
                self._fail(error)
        finally:
            self._lock.release()

    def embed(self, texts):
        return [list(row) for row in self.encode(texts).vectors.rows]
