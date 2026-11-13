"""Owned staged CPU embedding composition with bounded native worker renewal."""

import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass, replace

from . import (
    cpu_embedding_backend, embedding_staging, embedding_tokenizer, embedding_vectors,
    native_tokenizers,
)
from .schema import EmbeddingExecution


class SessionRefused(ValueError):
    """A session operation was refused without exposing input or paths."""


@dataclass(frozen=True)
class EncodedBatch:
    vectors: embedding_vectors.NormalizedVectors
    receipts: tuple[embedding_tokenizer.TokenIDReceipt, ...]
    space_id: str
    definition_fingerprint: str
    execution_fingerprint: str
    policy_id: str


class CPUEmbeddingSession:
    """Own the stage, a resident CPU backend and a renewable native tokenizer."""

    def __init__(self, manifest_bytes, artifact_root, definition, tokenizer_definition,
                 expected_inventory_id, runtime, *, parent=None):
        self._lock = threading.Lock()
        self._stage = self._backend = self._tokenizer = None
        self._closed = False
        try:
            if type(runtime) is not native_tokenizers.Runtime:
                raise ValueError
            self.definition = definition
            self.execution = EmbeddingExecution(definition=definition, device="cpu", dtype="fp32")
            self._runtime = runtime
            stage = embedding_staging.stage(manifest_bytes, artifact_root, definition,
                                            tokenizer_definition, expected_inventory_id,
                                            parent=parent)
            staged = stage.__enter__()
            self._stage = stage
            self._staged = staged
            self._token_definition = replace(tokenizer_definition,
                                             artifact=staged.path / "tokenizer.json")
            self._tokenizer = embedding_tokenizer.TokenIDSession(self._token_definition, runtime)
            self._backend = cpu_embedding_backend.CPUEmbeddingBackend(
                staged.manifest_bytes, staged.path, definition, self._token_definition,
                expected_inventory_id)
            if (self._backend.space != staged.space
                    or staged.space.definition_fingerprint != definition.fingerprint()):
                raise ValueError
            self.space = staged.space
        except BaseException as error:
            try:
                self._cleanup()
            except Exception:
                pass
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            raise SessionRefused("embedding session refused") from None

    def _cleanup(self):
        self._closed = True
        try:
            if self._backend is not None:
                self._backend.close()
        finally:
            self._backend = None
            try:
                if self._tokenizer is not None:
                    self._tokenizer.close()
            finally:
                self._tokenizer = None
                if self._stage is not None:
                    stage, self._stage = self._stage, None
                    stage.__exit__(None, None, None)

    def close(self):
        if not self._lock.acquire(blocking=False):
            raise SessionRefused("embedding session busy")
        try:
            if not self._closed:
                try:
                    self._cleanup()
                except Exception:
                    raise SessionRefused("embedding session refused") from None
        finally:
            self._lock.release()

    def __enter__(self):
        if self._closed:
            raise SessionRefused("embedding session refused")
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            self.close()
        except SessionRefused:
            if exc is None:
                raise
            exc.add_note("embedding session cleanup failed")

    @staticmethod
    def _preflight(texts):
        if type(texts) not in (list, tuple) or not 1 <= len(texts) <= 128:
            raise ValueError
        sizes = []
        total_chars = 0
        for text in texts:
            if type(text) is not str or len(text) > 100_000:
                raise ValueError
            text.encode("utf-8", "strict")
            wire = json.dumps({"text": text, "nonce": "0" * 32}, ensure_ascii=True,
                              separators=(",", ":")).encode() + b"\n"
            if len(wire) > 200_000:
                raise ValueError
            sizes.append(len(wire))
            total_chars += len(text)
        if total_chars > 1_000_000 or sum(sizes) > 4_000_000:
            raise ValueError
        return sizes

    def _renew_if_needed(self, sizes):
        worker = self._tokenizer
        policy = worker._policy
        if (worker._deadline - time.monotonic() <= 5 + 2 * len(sizes)
                or worker._calls + len(sizes) > policy.max_calls
                or worker._input + sum(sizes) > policy.max_input_bytes):
            worker.close()
            self._tokenizer = None
            self._tokenizer = embedding_tokenizer.TokenIDSession(self._token_definition,
                                                                 self._runtime)

    def _receipt(self, receipt, text):
        d = self._token_definition
        digest = hashlib.sha256(json.dumps([text, None], ensure_ascii=True,
                                          separators=(",", ":")).encode()).hexdigest()
        if (type(receipt) is not embedding_tokenizer.TokenIDReceipt
                or type(receipt.ids) is not tuple or type(receipt.count) is not int
                or receipt.count != len(receipt.ids) or not 2 <= receipt.count <= 1024
                or any(type(i) is not int or not 0 <= i < self._backend._vocab
                       for i in receipt.ids)
                or receipt.artifact_sha256 != d.sha256
                or receipt.backend_version != d.backend_version
                or receipt.role != d.role or receipt.model_revision != d.model_revision
                or receipt.preprocessing != d.preprocessing or receipt.input_sha256 != digest
                or type(receipt.nonce) is not str
                or not re.fullmatch(r"[0-9a-f]{32}", receipt.nonce)
                or receipt.serialization != "utf8-json-v1;no-truncation;no-padding;special-tokens"):
            raise ValueError

    def encode(self, texts):
        if not self._lock.acquire(blocking=False):
            raise SessionRefused("embedding session busy")
        try:
            if self._closed:
                raise SessionRefused("embedding session refused")
            try:
                if type(texts) not in (list, tuple) or not 1 <= len(texts) <= 128:
                    raise ValueError
                texts = tuple(texts)
                sizes = self._preflight(texts)
                self._renew_if_needed(sizes)
                receipts = tuple(self._tokenizer.encode(text) for text in texts)
                for receipt, text in zip(receipts, texts, strict=True):
                    self._receipt(receipt, text)
                rows = self._backend.forward_cls([receipt.ids for receipt in receipts])
                vectors = embedding_vectors.normalize_rows(rows)
                if (len(vectors.rows) != len(texts)
                        or vectors.policy_id != embedding_vectors.POLICY_ID
                        or self._backend.space != self.space
                        or self.space.definition_fingerprint != self.definition.fingerprint()
                        or self.execution.fingerprint() != EmbeddingExecution(
                            definition=self.definition, device="cpu", dtype="fp32"
                        ).fingerprint()):
                    raise ValueError
                return EncodedBatch(vectors, receipts, self.space.space_id,
                                    self.definition.fingerprint(), self.execution.fingerprint(),
                                    vectors.policy_id)
            except BaseException as error:
                try:
                    self._cleanup()
                except Exception:
                    pass
                if isinstance(error, (KeyboardInterrupt, SystemExit)):
                    raise
                raise SessionRefused("embedding session refused") from None
        finally:
            self._lock.release()

    def embed(self, texts):
        return [list(row) for row in self.encode(texts).vectors.rows]
