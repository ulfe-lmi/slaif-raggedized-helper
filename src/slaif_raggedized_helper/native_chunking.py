"""Bind isolated local native counts to structural chunks and immutable receipts."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import chunking, native_tokenizers as native, provenance_records as p
from .tokenizer_session import Session


class NativeChunkingError(ValueError):
    """Input-free refusal; no partial result is returned."""


_SERIALIZATION = 'utf8-json-v1;no-truncation;no-padding;special-tokens'
_ROLES = ('bge_body', 'bge_representation', 'reranker_pair')


def _json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _input_digest(text, pair):
    # This is the exact Session serialization, whose array order is significant.
    return _digest(json.dumps([text, pair], ensure_ascii=True, separators=(',', ':')).encode())


def _identity(d):
    return _digest(_json({'version': 1, 'artifact_sha256': d.sha256,
                          'backend_version': d.backend_version, 'role': d.role,
                          'model_revision': d.model_revision, 'preprocessing': d.preprocessing,
                          'mode': 'pair' if d.role == 'reranker_pair' else 'single',
                          'serialization': _SERIALIZATION}))


@dataclass(frozen=True)
class Receipt:
    chunk_id: str
    definition_fingerprint: str
    count: native.Count


@dataclass(frozen=True)
class Result:
    chunks: tuple[p.Chunk, ...]
    neighbors: tuple[p.Neighbors, ...]
    receipts: tuple[Receipt, ...]

    def receipts_json(self) -> bytes:
        """Versioned bounded UTF-8 JSON; contains digests, never input text."""
        data = _json({'version': 1, 'receipts': [
            {'chunk_id': r.chunk_id, 'definition_fingerprint': r.definition_fingerprint,
             'count': r.count.__dict__} for r in self.receipts]})
        if len(data) > 8_000_000:
            raise NativeChunkingError('native chunk construction refused')
        return data


def build(registry: p.Registry, blocks: tuple[p.Block, ...], body: native.Definition,
          representation: native.Definition, pair: native.Definition, runtime: native.Runtime,
          query: str, policy: chunking.Policy | None = None) -> Result:
    """Count exact inputs in an owned fixed session, and bind observed-count chunks."""
    try:
        definitions = (body, representation, pair)
        # Bound every declaration before encoding or serializing any of them.
        for d, role in zip(definitions, _ROLES):
            if (type(d) is not native.Definition or type(d.role) is not str or
                    d.role != role or type(d.backend_version) is not str or
                    d.backend_version != '0.21.4' or type(d.sha256) is not str or
                    len(d.sha256) != 64 or not re.fullmatch('[0-9a-f]{64}', d.sha256) or
                    any(type(value) is not str or not 1 <= len(value) <= 256
                        for value in (d.model_revision, d.preprocessing))):
                raise ValueError
        for d in definitions:
            d.model_revision.encode('utf-8', errors='strict')
            d.preprocessing.encode('utf-8', errors='strict')
        if type(query) is not str or len(query) > 10000:
            raise ValueError
        query.encode('utf-8')
        if policy is None:
            policy = chunking.Policy(pair_max=1280)
        elif type(policy) is chunking.Policy:
            policy = chunking.Policy(**policy.__dict__)
        else:
            raise ValueError
        identities = tuple(_identity(d) for d in definitions)
        cache = {}
        with Session(definitions, runtime) as session:
            def observe(index, text, second=None):
                d = definitions[index]
                result = session.count(d.role, text, second)
                expected = (d.sha256, d.backend_version, d.role, d.model_revision,
                            d.preprocessing, _input_digest(text, second),
                            'pair' if second is not None else 'single', _SERIALIZATION)
                if (type(result) is not native.Count or type(result.count) is not int
                        or not 0 <= result.count <= 200000 or
                        (result.artifact_sha256, result.backend_version, result.role,
                         result.model_revision, result.preprocessing, result.input_sha256,
                         result.mode, result.serialization) != expected):
                    raise ValueError
                key = (index, text, second)
                if key in cache and cache[key] != result:
                    raise ValueError
                cache[key] = result
                return result.count

            counters = chunking.Counters(*identities, lambda t: observe(0, t),
                                         lambda t: observe(1, t),
                                         lambda q, t: observe(2, q, t))
            raw = chunking.build(registry, blocks, counters, query, policy)
            policy_definition = _json({'version': 1, 'kind': 'observed-local-native',
                                       'policy': policy.__dict__, 'definitions': identities,
                                       'query_input_sha256': _input_digest(query, None),
                                       'serialization': _SERIALIZATION}).decode()
            pid = p.policy_id(policy_definition)
            chunks = []
            receipts = []
            for original in raw.chunks:
                rep = ''.join(original.heading_path) + original.text
                keys = ((0, original.text, None), (1, rep, None), (2, query, rep))
                observed = tuple(cache[k] for k in keys)
                if tuple(c.count for c in observed) != tuple(c.count for c in original.counts):
                    raise ValueError
                counts = tuple(p.TokenCount(schema_version=1, availability='available',
                               count=c.count,
                               provenance='OBSERVED_LOCAL_NATIVE_TOKENIZATION:' + ident)
                               for c, ident in zip(observed, identities))
                chunk = original.model_copy(update={'policy_id': pid, 'counts': counts})
                chunk = chunk.model_copy(update={'chunk_id': p.chunk_id(chunk)})
                registry.bind_chunk(chunk)
                chunks.append(chunk)
                receipts.extend(Receipt(chunk.chunk_id, ident, count)
                                for ident, count in zip(identities, observed))
            chunks = tuple(chunks)
            links = tuple(p.Neighbors(schema_version=1, chunk_id=c.chunk_id,
                          previous_chunk_id=chunks[i - 1].chunk_id if i else None,
                          next_chunk_id=chunks[i + 1].chunk_id if i + 1 < len(chunks) else None)
                          for i, c in enumerate(chunks))
            registry.bind_neighbors(chunks, links)
            result = Result(chunks, links, tuple(receipts))
            result.receipts_json()
            return result
    except Exception:
        raise NativeChunkingError('native chunk construction refused') from None
