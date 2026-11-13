"""Private resident query embedding; callers must establish rights before model exposure."""

import dataclasses
import hashlib
import math
import os
from pathlib import Path
import struct
import threading

from . import cpu_execution_contract, embedding_vectors, isolated_cpu_embedding, native_tokenizers
from .schema import EmbeddingExecution, fingerprint

_POLICY = (b'{"max_characters":8192,"max_utf8_bytes":32768,"normalization":'
           b'"cls-l2-f64-fp32le-d1024-eps1e-12-tol1e-4-v1","schema":1,'
           b'"text":"raw-unicode-identity-nonblank-no-prefix-no-truncation-no-padding"}')
POLICY_ID = hashlib.sha256(_POLICY).hexdigest()
_POLICY_DIGEST = POLICY_ID


class QueryRefused(ValueError):
    """Content-free refusal; the service retains any pending resources."""


@dataclasses.dataclass(frozen=True)
class QueryEmbedding:
    payload: bytes
    payload_sha256: str
    space_id: str
    definition_fingerprint: str
    intended_execution_fingerprint: str
    execution_record: bytes
    execution_fingerprint: str
    query_policy_id: str


def _source_hash():
    return hashlib.sha256(native_tokenizers._read_artifact(Path(__file__), 131072)).hexdigest()


def _query(text):
    if type(text) is not str or not text or len(text) > 8192 or text.isspace():
        raise ValueError
    if len(text.encode('utf-8', 'strict')) > 32768:
        raise ValueError


class ResidentQueryEncoder:
    """Own one admitted isolated CPU session; no cache or authorization is provided."""

    def __init__(self, manifest_bytes, artifact_root, definition, tokenizer_definition,
                 expected_inventory_id, tokenizer_runtime, cpu_runtime, *, worker_policy=None,
                 parent=None):
        self._lock = threading.Lock()
        self._pid = os.getpid()
        self._state = 'new'
        self._session = None
        self._source = _source_hash()
        try:
            self._session = isolated_cpu_embedding.IsolatedCPUEmbeddingSession(
                manifest_bytes, artifact_root, definition, tokenizer_definition,
                expected_inventory_id, tokenizer_runtime, cpu_runtime,
                worker_policy=worker_policy, parent=parent)
        except Exception:
            raise QueryRefused('query encoder refused') from None

    @property
    def cleanup_owner(self):
        """The actual session is retained for retrying pending cleanup."""
        return self._session

    def _acquire(self):
        if os.getpid() != self._pid or not self._lock.acquire(blocking=False):
            raise QueryRefused('query encoder busy or unavailable')

    def _check(self):
        if (hashlib.sha256(_POLICY).hexdigest() != _POLICY_DIGEST
                or POLICY_ID != _POLICY_DIGEST or _source_hash() != self._source):
            raise ValueError
        self._session._validate_state()

    def _failed(self, error):
        self._state = 'refused'
        # The current operation determines priority; the session retains pending owners.
        if not isinstance(error, Exception):
            raise error
        raise QueryRefused('query encoder refused') from None

    def __enter__(self):
        self._acquire()
        try:
            if self._state != 'new':
                raise QueryRefused('query encoder refused')
            try:
                self._check()
                self._session.__enter__()
                self._check()
                self._state = 'open'
                return self
            except BaseException as error:
                try:
                    self._session.close()
                except BaseException as cleanup:
                    if isinstance(error, Exception) and not isinstance(cleanup, Exception):
                        error = cleanup
                self._failed(error)
        finally:
            self._lock.release()

    def encode_query(self, text):
        self._acquire()
        try:
            if self._state != 'open':
                raise QueryRefused('query encoder refused')
            try:
                _query(text)
            except (ValueError, UnicodeError):
                raise QueryRefused('query encoder refused') from None
            s = self._session
            try:
                self._check()
                batch = s.encode([text])
                self._check()
                if type(batch) is not isolated_cpu_embedding.EncodedBatch:
                    raise ValueError
                v = batch.vectors
                if (type(v) is not embedding_vectors.NormalizedVectors
                        or type(v.rows) is not tuple or len(v.rows) != 1
                        or type(v.rows[0]) is not tuple or len(v.rows[0]) != 1024
                        or any(type(x) is not float or not math.isfinite(x) for x in v.rows[0])
                        or type(v.payload) is not bytes or len(v.payload) != 4096
                        or struct.pack('<1024f', *v.rows[0]) != v.payload
                        or struct.unpack('<1024f', v.payload) != v.rows[0]
                        or hashlib.sha256(v.payload).hexdigest() != v.sha256
                        or abs(math.sqrt(math.fsum(x*x for x in v.rows[0])) - 1) > 1e-4
                        or v.policy_id != embedding_vectors.POLICY_ID
                        or type(batch.receipts) is not tuple or len(batch.receipts) != 1
                        or batch.space_id != s.space.space_id
                        or batch.definition_fingerprint != s.definition.fingerprint()
                        or batch.definition_fingerprint != s.space.definition_fingerprint
                        or batch.intended_execution_fingerprint != EmbeddingExecution(
                            definition=s.definition, device='cpu', dtype='fp32').fingerprint()
                        or batch.intended_execution_fingerprint != s.intended_execution_fingerprint
                        or batch.execution_record != s.execution_record
                        or batch.execution_fingerprint != s.execution_fingerprint):
                    raise ValueError
                s._receipt(batch.receipts[0], text)
                record = cpu_execution_contract._validate(batch.execution_record)
                if (record['space'] != batch.space_id
                        or record['definition'] != batch.definition_fingerprint
                        or batch.execution_fingerprint != fingerprint(
                            {'kind': 'isolated-cpu-embedding-execution-v2', **record})
                        or s._worker_identity() != record['worker']):
                    raise ValueError
                return QueryEmbedding(v.payload, v.sha256, batch.space_id,
                                      batch.definition_fingerprint,
                                      batch.intended_execution_fingerprint,
                                      batch.execution_record, batch.execution_fingerprint,
                                      _POLICY_DIGEST)
            except BaseException as error:
                try:
                    s.close()
                except BaseException as cleanup:
                    if isinstance(error, Exception) and not isinstance(cleanup, Exception):
                        error = cleanup
                self._failed(error)
        finally:
            self._lock.release()

    def close(self):
        self._acquire()
        try:
            try:
                if self._session is not None:
                    self._session.close()
                self._state = 'closed'
            except BaseException as error:
                self._failed(error)
        finally:
            self._lock.release()

    def __exit__(self, exc_type, exc, tb):
        try:
            self.close()
        except BaseException as cleanup:
            if exc is None or (isinstance(exc, Exception) and not isinstance(cleanup, Exception)):
                raise
        return False
