"""Borrowed GPU parent and independent native tokenizer composition.

Identity declarations describe software inputs; they are not execution authority.
"""

import dataclasses
import hashlib
import json
import os
import re
import weakref
from pathlib import Path

from . import embedding_native_identity as native_identity
from . import embedding_vectors, gpu_worker_identity, gpu_worker_protocol as wire
from . import native_tokenizers
from .schema import EmbeddingDefinition, EmbeddingExecution, FINGERPRINT_VERSION, fingerprint

DOMAIN = b"slaif-isolated-gpu-fp16-cls-execution-v1\n"
SCOPE = (
    "Native selected Python/package/source FILE identity plus raw GPU worker pinned "
    "Python/driver/source/profile and package metadata; excludes stdlib/system/launcher "
    "libraries, GPU package contents, actual ABI/runtime execution, publisher/authenticity, "
    "current authorization and model/hardware/security/license qualification."
)
SOURCES = (
    "isolated_gpu_embedding.py",
    "gpu_worker_identity.py",
    "embedding_native_identity.py",
    "embedding_tokenizer.py",
    "embedding_tokenizer_worker.py",
    "native_tokenizers.py",
    "embedding_vectors.py",
    "schema.py",
)
HEX = re.compile(r"[0-9a-f]{64}\Z")


class SessionRefused(ValueError):
    """Content-free refusal; no declaration confers execution authority."""


@dataclasses.dataclass(frozen=True)
class PlannedContract:
    execution_record: bytes
    execution_fingerprint: str
    native_runtime_record: bytes
    space_id: str
    definition_fingerprint: str
    intended_execution_fingerprint: str


def _json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _digest(raw):
    return "sha256:" + hashlib.sha256(DOMAIN + raw).hexdigest()


def _hex(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError


def _intended(definition):
    return fingerprint(
        {
            "version": FINGERPRINT_VERSION,
            "kind": "embedding-execution",
            "space": definition,
            "device": "gpu",
            "dtype": "fp16",
        }
    )


def _bridge():
    root = Path(__file__).parent
    return {
        name: hashlib.sha256(native_tokenizers._read_artifact(root / name, 1024 * 1024)).hexdigest()
        for name in SOURCES
    }


def validate_record(execution_record, native_runtime_record):
    """Validate canonical persisted declarations; do not infer live ownership."""
    try:
        if type(execution_record) is not bytes or len(execution_record) > 32768:
            raise ValueError
        obj = wire.parse(execution_record)
        if _json(obj) != execution_record:
            raise ValueError
        _keys(
            obj,
            (
                "schema",
                "contract",
                "space_id",
                "definition_fingerprint",
                "intended_execution_fingerprint",
                "worker",
                "native",
                "normalization_policy_id",
                "bridge",
                "hardware_qualification",
                "runtime_integrity_scope",
            ),
        )
        if (
            type(obj["schema"]) is not int
            or obj["schema"] != 1
            or obj["contract"] != "isolated-gpu-fp16-cls-v1"
            or obj["hardware_qualification"] != "unknown"
            or obj["runtime_integrity_scope"] != SCOPE
            or obj["normalization_policy_id"] != embedding_vectors.POLICY_ID
            or not _hex(obj["space_id"])
        ):
            raise ValueError
        definition = obj["definition_fingerprint"]
        if (
            type(definition) is not str
            or not definition.startswith("sha256:")
            or not _hex(definition[7:])
            or obj["intended_execution_fingerprint"] != _intended(definition)
        ):
            raise ValueError
        worker = obj["worker"]
        _keys(worker, ("record", "fingerprint"))
        worker_raw = _json(worker["record"])
        if (
            gpu_worker_identity.validate_record(worker_raw) != worker["fingerprint"]
            or worker["record"]["space_id"] != obj["space_id"]
            or worker["record"]["definition_fingerprint"] != definition
        ):
            raise ValueError
        native = obj["native"]
        _keys(
            native,
            (
                "artifact_sha256",
                "backend_version",
                "role",
                "model_revision",
                "preprocessing",
                "runtime_fingerprint",
                "runtime_record_sha256",
            ),
        )
        if (
            not _hex(native["artifact_sha256"])
            or native["backend_version"] != "0.21.4"
            or native["role"] != "bge_representation"
            or native["preprocessing"] != "identity"
            or type(native["model_revision"]) is not str
            or re.fullmatch(r"[0-9a-f]{40}", native["model_revision"]) is None
            or native_identity.validate_record(native_runtime_record)
            != native["runtime_fingerprint"]
            or hashlib.sha256(native_runtime_record).hexdigest() != native["runtime_record_sha256"]
        ):
            raise ValueError
        _keys(obj["bridge"], SOURCES)
        if any(not _hex(value) for value in obj["bridge"].values()):
            raise ValueError
        detached = json.loads(native_runtime_record)
        if any(
            detached["sources"][name] != obj["bridge"][name] for name in native_identity.SOURCES
        ):
            raise ValueError
        return _digest(execution_record)
    except Exception:
        raise SessionRefused("embedding session refused") from None


def _prepared_token(prepared):
    prepared.revalidate()
    start = wire.parse(prepared.startup)
    definition = EmbeddingDefinition.model_validate(start["definition"], strict=True)
    token = start["tokenizer"]
    _keys(token, ("sha256", "backend_version", "role", "model_revision", "preprocessing"))
    if (
        not _hex(token["sha256"])
        or token["backend_version"] != "0.21.4"
        or token["role"] != "bge_representation"
        or token["preprocessing"] != "identity"
        or type(token["model_revision"]) is not str
        or re.fullmatch(r"[0-9a-f]{40}", token["model_revision"]) is None
        or definition.checkpoint_revision != token["model_revision"]
        or definition.tokenizer_revision != token["model_revision"]
    ):
        raise ValueError
    path = Path("/proc/self/fd") / str(prepared._descriptors["artifacts"]) / "tokenizer.json"
    if (
        hashlib.sha256(native_tokenizers._read_artifact(path, 32_000_000)).hexdigest()
        != token["sha256"]
    ):
        raise ValueError
    prepared.revalidate()
    return definition, native_tokenizers.Definition(path, **token)


def predict(prepared, tokenizer_runtime):
    """Revalidate prepared inputs without launching a worker."""
    try:
        worker = gpu_worker_identity.predict(prepared)
        definition, token = _prepared_token(prepared)
        native = native_identity.predict(tokenizer_runtime)
        bridge = _bridge()
        worker_record = wire.parse(worker.record_bytes)
        intended = EmbeddingExecution(
            definition=definition, device="gpu", dtype="fp16"
        ).fingerprint()
        obj = {
            "schema": 1,
            "contract": "isolated-gpu-fp16-cls-v1",
            "space_id": worker_record["space_id"],
            "definition_fingerprint": definition.fingerprint(),
            "intended_execution_fingerprint": intended,
            "worker": {"record": worker_record, "fingerprint": worker.fingerprint},
            "native": {
                "artifact_sha256": token.sha256,
                "backend_version": token.backend_version,
                "role": token.role,
                "model_revision": token.model_revision,
                "preprocessing": token.preprocessing,
                "runtime_fingerprint": native.fingerprint,
                "runtime_record_sha256": hashlib.sha256(native.record_bytes).hexdigest(),
            },
            "normalization_policy_id": embedding_vectors.POLICY_ID,
            "bridge": bridge,
            "hardware_qualification": "unknown",
            "runtime_integrity_scope": SCOPE,
        }
        raw = _json(obj)
        result = PlannedContract(
            raw,
            validate_record(raw, native.record_bytes),
            native.record_bytes,
            obj["space_id"],
            definition.fingerprint(),
            intended,
        )
        if gpu_worker_identity.predict(prepared) != worker or _bridge() != bridge:
            raise ValueError
        _prepared_token(prepared)
        return result
    except Exception:
        raise SessionRefused("embedding session refused") from None


def _raw_rows(result, ready, count):
    from . import gpu_embedding_worker

    if (
        type(result) is not gpu_embedding_worker.RawCLSResult
        or type(result.binding) is not tuple
        or result.binding != tuple(sorted(wire.parse(ready).items()))
    ):
        raise ValueError
    wire.output_ok(result.rows, count)
    return result.rows


@dataclasses.dataclass(frozen=True)
class EncodedBatch:
    vectors: embedding_vectors.NormalizedVectors
    receipts: tuple
    space_id: str
    definition_fingerprint: str
    intended_execution_fingerprint: str
    execution_record: bytes
    execution_fingerprint: str
    native_runtime_record: bytes


# Strong references retain cleanup owners even if a caller loses its session.
_owners = {}
_closed = weakref.WeakKeyDictionary()


def _note(error, owner):
    try:
        error.add_note("embedding session cleanup pending")
    except BaseException:
        pass
    try:
        error.cleanup_owner = owner
    except BaseException:
        pass


class GPUTextEmbeddingSession:
    """Own only a native tokenizer; borrow the caller's registered GPU parent."""

    def __new__(cls, *args, **kwargs):
        import threading

        if cls is not GPUTextEmbeddingSession:
            raise SessionRefused("embedding session refused")
        obj = super().__new__(cls)
        obj._creator = os.getpid()
        obj._initialized = False
        obj._lock = threading.Lock()
        _owners[id(obj)] = [
            obj,
            obj._creator,
            obj._lock,
            None,
            None,
            None,
            None,
            None,
            set(),
            False,
        ]
        return obj

    def __init__(self, worker, tokenizer_runtime):
        from . import embedding_tokenizer

        record = self._acquire()
        if record[9] or self._initialized:
            record[2].release()
            raise SessionRefused("embedding session refused")
        record[9] = True
        self._initialized = True
        self._state = "initializing"
        try:
            observed = gpu_worker_identity.observe(worker)
            self._worker = worker
            self._prepared = worker._prepared
            self._runtime = tokenizer_runtime
            self._plan = predict(self._prepared, tokenizer_runtime)
            if (
                observed.record_bytes
                != _json(json.loads(self._plan.execution_record)["worker"]["record"])
                or observed.fingerprint
                != json.loads(self._plan.execution_record)["worker"]["fingerprint"]
            ):
                raise ValueError
            self._ready = observed.ready_binding_bytes
            self._vocab = worker._vocab
            self._max_rows = worker._policy.max_rows
            _, self._definition = _prepared_token(self._prepared)
            self._native = embedding_tokenizer.TokenIDSession.__new__(
                embedding_tokenizer.TokenIDSession
            )
            record[3] = self._native
            embedding_tokenizer.TokenIDSession.__init__(
                self._native, self._definition, self._runtime
            )
            record[5] = (
                self._native._child,
                self._native._tmp,
                self._native._deadline,
                self._native._tmp.name,
            )
            record[6] = dataclasses.astuple(self._plan)
            record[7] = (dataclasses.astuple(self._runtime), dataclasses.astuple(self._definition))
            record[4] = (
                worker,
                self._prepared,
                tokenizer_runtime,
                self._plan,
                self._ready,
                self._vocab,
                self._max_rows,
                self._definition,
                self._guards(),
            )
            self._state = "open"
            self._check()
        except BaseException as error:
            self._fail(error)
        finally:
            record[2].release()

    def _admit(self):
        record = _owners.get(id(self))
        if record is None:
            record = _closed.get(self)
        if (
            record is None
            or (
                record[0] is not self
                and (not isinstance(record[0], weakref.ReferenceType) or record[0]() is not self)
            )
            or record[1] != os.getpid()
            or self._creator != record[1]
            or self._lock is not record[2]
            or self._initialized is not record[9]
        ):
            raise SessionRefused("embedding session refused")
        return record

    def _acquire(self):
        record = self._admit()
        if not record[2].acquire(blocking=False):
            raise SessionRefused("embedding session refused")
        return record

    @staticmethod
    def _guards():
        from . import embedding_tokenizer

        cls = GPUTextEmbeddingSession
        return (
            predict,
            validate_record,
            _prepared_token,
            _bridge,
            _raw_rows,
            gpu_worker_identity.observe,
            native_identity.predict,
            embedding_vectors.normalize_rows,
            cls._check,
            cls.encode,
            cls.close,
            cls._renew,
            cls._receipt,
            cls._drain,
            cls._preflight,
            cls._budget,
            cls.__init__,
            cls.__enter__,
            cls.__exit__,
            cls._admit,
            cls._acquire,
            cls._fail,
            cls._guards,
            embedding_tokenizer.TokenIDSession.__init__,
            embedding_tokenizer.TokenIDSession.encode,
            embedding_tokenizer.TokenIDSession.close,
        )

    def _check(self):
        record = self._admit()
        if (
            record[4]
            != (
                self._worker,
                self._prepared,
                self._runtime,
                self._plan,
                self._ready,
                self._vocab,
                self._max_rows,
                self._definition,
                self._guards(),
            )
            or self._state != "open"
            or record[3] is not self._native
            or self._worker._prepared is not self._prepared
        ):
            raise ValueError
        if (
            dataclasses.astuple(self._plan) != record[6]
            or (dataclasses.astuple(self._runtime), dataclasses.astuple(self._definition))
            != record[7]
            or validate_record(self._plan.execution_record, self._plan.native_runtime_record)
            != self._plan.execution_fingerprint
        ):
            raise ValueError
        observed = gpu_worker_identity.observe(self._worker)
        planned = json.loads(self._plan.execution_record)
        current_native = native_identity.predict(self._runtime)
        if (
            observed.ready_binding_bytes != self._ready
            or current_native.record_bytes != self._plan.native_runtime_record
            or current_native.fingerprint != planned["native"]["runtime_fingerprint"]
            or _bridge() != planned["bridge"]
            or observed.record_bytes
            != _json(json.loads(self._plan.execution_record)["worker"]["record"])
            or observed.fingerprint
            != json.loads(self._plan.execution_record)["worker"]["fingerprint"]
            or self._worker._vocab != self._vocab
            or self._worker._policy.max_rows != self._max_rows
        ):
            raise ValueError
        from . import embedding_tokenizer

        policy = dataclasses.asdict(self._native._policy)
        expected_policy = dataclasses.asdict(embedding_tokenizer.Policy())
        if (
            type(self._native._policy) is not embedding_tokenizer.Policy
            or any(
                type(policy[name]) is not type(value) or policy[name] != value
                for name, value in expected_policy.items()
            )
            or self._native not in embedding_tokenizer._OWNERS
            or self._native._creator_pid != os.getpid()
            or not self._native._initialized
            or record[5]
            != (
                self._native._child,
                self._native._tmp,
                self._native._deadline,
                self._native._tmp.name,
            )
            or self._native._child is None
            or self._native._child.poll() is not None
            or hashlib.sha256(
                native_tokenizers._read_artifact(Path(record[5][3]) / "artifact.json", 32_000_000)
            ).hexdigest()
            != self._definition.sha256
            or self._native._definition != self._definition
            or _prepared_token(self._prepared)[1] != self._definition
        ):
            raise ValueError

    def _drain(self):
        record = self._admit()
        native = record[3]
        if native is not None:
            native.close()
            if native._child is not None or native._tmp is not None:
                raise SessionRefused("embedding session refused")
            record[3] = None
            record[5] = None
        self._state = "closed"
        if _owners.get(id(self)) is record:
            closed = [
                weakref.ref(self),
                record[1],
                record[2],
                None,
                None,
                None,
                None,
                None,
                None,
                record[9],
            ]
            _closed[self] = closed
            del _owners[id(self)]

    def _fail(self, error):
        cleanup = None
        try:
            self._drain()
        except BaseException as caught:
            cleanup = caught
        pending = self._admit()[3] is not None
        if not isinstance(error, Exception):
            selected = error
        elif cleanup is not None and not isinstance(cleanup, Exception):
            selected = cleanup
        else:
            selected = SessionRefused("embedding session refused")
            if pending:
                _note(selected, self)
        if pending:
            _note(selected, self)
        raise selected from None

    def close(self):
        record = self._acquire()
        try:
            record[9] = True
            self._initialized = True
            self._drain()
        finally:
            record[2].release()

    def __enter__(self):
        self._admit()
        if self._state != "open":
            raise SessionRefused("embedding session refused")
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.close()
        except BaseException as cleanup:
            if exc is None or (isinstance(exc, Exception) and not isinstance(cleanup, Exception)):
                raise
            _note(exc, self)
        return False

    def _preflight(self, texts):
        if type(texts) not in (list, tuple) or not 1 <= len(texts) <= min(128, self._max_rows):
            raise ValueError
        texts = tuple(texts)
        if (
            any(type(t) is not str or len(t) > 100000 for t in texts)
            or sum(map(len, texts)) > 1000000
        ):
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
        return texts, sizes

    def _budget(self, count):
        """Refuse before text exposure if the borrowed parent lacks worst-case room."""
        import time

        worker = self._worker
        pump = worker._pump
        policy = worker._policy
        worst_rows = [[self._vocab - 1] * 1024 for _ in range(count)]
        request = wire.encode({"nonce": "0" * 32, "digest": "0" * 64, "rows": worst_rows})
        response = len(self._ready) + count * 32770 + 512
        if (
            worker._calls + 1 >= policy.calls
            or len(request) + 1 > policy.request_bytes
            or response > policy.response_bytes
            or pump.written + len(request) + 1 > policy.total_input_bytes
            or pump.read + response > policy.total_output_bytes
            or pump.read + response > pump.resource.output_bytes
            or pump.deadline <= time.monotonic()
        ):
            raise ValueError

    def _renew(self, sizes):
        import time
        from . import embedding_tokenizer

        old = self._native
        policy = old._policy

        def insufficient(owner):
            return (
                owner._deadline - time.monotonic() <= 5 + 2 * len(sizes)
                or owner._calls + len(sizes) > policy.max_calls
                or owner._input + sum(sizes) > policy.max_input_bytes
                or owner._output + len(sizes) * (policy.max_response_bytes + 1)
                > policy.max_output_bytes
            )

        if insufficient(old):
            old.close()
            if old._child is not None or old._tmp is not None:
                raise ValueError
            record = self._admit()
            record[3] = None
            fresh = embedding_tokenizer.TokenIDSession.__new__(embedding_tokenizer.TokenIDSession)
            self._native = fresh
            record[3] = fresh
            embedding_tokenizer.TokenIDSession.__init__(fresh, self._definition, self._runtime)
            record[5] = (fresh._child, fresh._tmp, fresh._deadline, fresh._tmp.name)
            if insufficient(fresh):
                raise ValueError
            return True
        return False

    def _receipt(self, receipt, text):
        from . import embedding_tokenizer

        digest = hashlib.sha256(
            json.dumps([text, None], ensure_ascii=True, separators=(",", ":")).encode()
        ).hexdigest()
        d = self._definition
        if (
            type(receipt) is not embedding_tokenizer.TokenIDReceipt
            or type(receipt.ids) is not tuple
            or type(receipt.count) is not int
            or receipt.count != len(receipt.ids)
            or not 2 <= receipt.count <= 1024
            or any(type(i) is not int or not 0 <= i < self._vocab for i in receipt.ids)
            or (
                receipt.artifact_sha256,
                receipt.backend_version,
                receipt.role,
                receipt.model_revision,
                receipt.preprocessing,
            )
            != (d.sha256, d.backend_version, d.role, d.model_revision, d.preprocessing)
            or receipt.input_sha256 != digest
            or type(receipt.nonce) is not str
            or re.fullmatch(r"[0-9a-f]{32}", receipt.nonce) is None
            or receipt.serialization != "utf8-json-v1;no-truncation;no-padding;special-tokens"
        ):
            raise ValueError

    def encode(self, texts):
        from . import embedding_tokenizer, gpu_embedding_worker

        record = self._acquire()
        try:
            try:
                texts, sizes = self._preflight(texts)
                self._check()
                self._budget(len(texts))
                renewed = self._renew(sizes)
                receipts = []
                for text in texts:
                    if receipts or renewed:
                        self._check()
                        renewed = False
                    receipt = embedding_tokenizer.TokenIDSession.encode(record[3], text)
                    self._receipt(receipt, text)
                    if receipt.nonce in record[8]:
                        raise ValueError
                    record[8].add(receipt.nonce)
                    receipts.append(receipt)
                self._check()
                result = gpu_embedding_worker.GPUEmbeddingWorker.forward_cls(
                    record[4][0], [list(r.ids) for r in receipts]
                )
                rows = _raw_rows(result, self._ready, len(texts))
                self._check()
                vectors = embedding_vectors.normalize_rows(rows)
                self._check()
                if len(vectors.rows) != len(texts):
                    raise ValueError
                plan = self._plan
                return EncodedBatch(
                    vectors,
                    tuple(receipts),
                    plan.space_id,
                    plan.definition_fingerprint,
                    plan.intended_execution_fingerprint,
                    plan.execution_record,
                    plan.execution_fingerprint,
                    plan.native_runtime_record,
                )
            except BaseException as error:
                self._fail(error)
        finally:
            record[2].release()
