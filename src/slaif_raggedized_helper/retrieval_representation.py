"""Source-bound raw retrieval representations with isolated native counts."""
from dataclasses import asdict, dataclass
import hashlib
import json
import re

from . import ingestion_bundle, native_tokenizers
from .tokenizer_session import Session


class RepresentationError(ValueError):
    """Content-free refusal of a representation."""


@dataclass(frozen=True)
class Policy:
    max_tokens: int = 1024
    version: str = 'raw-v1'
    separator: str = '\n\n'
    max_codepoints: int = 100000
    max_request_bytes: int = 200000


@dataclass(frozen=True)
class Representation:
    revision_id: str
    extraction_id: str
    chunk_id: str
    scope: object
    source: object
    variant: str
    policy: Policy
    rendered_sha256: str
    representation_id: str
    text: str
    count: native_tokenizers.Count


def build(store, metadata_json_bytes, members, chunk_id, definition, runtime, policy=None):
    """Validate source and count the exact raw representation."""
    return build_many(store, metadata_json_bytes, members, (chunk_id,), definition,
                      runtime, policy)[0]


@dataclass(frozen=True)
class BatchPolicy:
    version: str = 'raw-batch-v1'
    max_items: int = 128
    max_total_codepoints: int = 1000000
    max_total_request_bytes: int = 4000000


def build_many(store, metadata_json_bytes, members, chunk_ids, definition, runtime,
               policy=None, batch_policy=None):
    """Build ordered representations with one source validation and native session."""
    try:
        bp = BatchPolicy() if batch_policy is None else batch_policy
        policy = Policy() if policy is None else policy
        if (type(bp) is not BatchPolicy or type(bp.version) is not str
                or bp.version != 'raw-batch-v1'
                or any(type(v) is not int or not 1 <= v <= limit for v, limit in (
                    (bp.max_items, 128), (bp.max_total_codepoints, 1000000),
                    (bp.max_total_request_bytes, 4000000)))
                or type(chunk_ids) not in (list, tuple) or not 1 <= len(chunk_ids) <= bp.max_items
                or any(type(x) is not str or not 1 <= len(x) <= 71 for x in chunk_ids)
                or len(set(chunk_ids)) != len(chunk_ids)
                or type(policy) is not Policy or type(policy.max_tokens) is not int
                or not 1 <= policy.max_tokens <= 1024 or type(policy.version) is not str
                or policy.version != 'raw-v1' or type(policy.separator) is not str
                or policy.separator != '\n\n' or type(policy.max_codepoints) is not int
                or policy.max_codepoints != 100000 or type(policy.max_request_bytes) is not int
                or policy.max_request_bytes != 200000
                or type(definition) is not native_tokenizers.Definition
                or definition.role != 'bge_representation' or definition.backend_version != '0.21.4'
                or type(definition.sha256) is not str
                or not re.fullmatch('[0-9a-f]{64}', definition.sha256)
                or any(type(x) is not str or not 1 <= len(x) <= 256
                       for x in (definition.model_revision, definition.preprocessing))
                or type(runtime) is not native_tokenizers.Runtime):
            raise ValueError
        definition.model_revision.encode('utf-8', errors='strict')
        definition.preprocessing.encode('utf-8', errors='strict')
        validated = ingestion_bundle.validate(store, metadata_json_bytes, members)
        selected = []
        total_chars = total_wire = 0
        for chunk_id in chunk_ids:
            matches = [c for c in validated.chunks if c.chunk_id == chunk_id]
            if len(matches) != 1:
                raise ValueError
            chunk = matches[0]
            components = [validated.revision.source.title, *chunk.heading_path, chunk.text]
            if any(x is not None and type(x) is not str for x in components):
                raise ValueError
            components = [x for x in components[:-1] if x] + [components[-1]]
            length = sum(len(x) for x in components) + 2 * (len(components) - 1)
            if length > 100000 or total_chars + length > bp.max_total_codepoints:
                raise ValueError
            text = policy.separator.join(components)
            wire = json.dumps({'text': text, 'pair': None, 'nonce': '0' * 32,
                               'role': definition.role, 'artifact': 0}, ensure_ascii=True,
                              separators=(',', ':')).encode() + b'\n'
            total_chars += length
            total_wire += len(wire)
            if (len(wire) > 200000 or total_chars > bp.max_total_codepoints
                    or total_wire > bp.max_total_request_bytes):
                raise ValueError
            selected.append((chunk, text))
        results = []
        with Session((definition,), runtime) as session:
            for chunk, text in selected:
                digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
                input_digest = hashlib.sha256(json.dumps([text, None], ensure_ascii=True,
                                              separators=(',', ':')).encode()).hexdigest()
                count = session.count('bge_representation', text)
                if (type(count) is not native_tokenizers.Count or type(count.count) is not int
                        or not 0 <= count.count <= policy.max_tokens
                        or count.artifact_sha256 != definition.sha256
                        or count.backend_version != definition.backend_version
                        or count.role != definition.role
                        or count.model_revision != definition.model_revision
                        or count.preprocessing != definition.preprocessing
                        or count.input_sha256 != input_digest
                        or count.mode != 'single' or count.serialization !=
                        'utf8-json-v1;no-truncation;no-padding;special-tokens'):
                    raise ValueError
                identity = dict(revision_id=validated.revision.revision_id,
                                extraction_id=chunk.extraction_id, chunk_id=chunk.chunk_id,
                                source=validated.revision.source.model_dump(mode='json'),
                                scope=validated.scope.model_dump(mode='json'), variant='raw',
                                policy=asdict(policy), rendered_sha256=digest)
                rid = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=True,
                                     separators=(',', ':')).encode()).hexdigest()
                results.append(Representation(chunk.revision_id, chunk.extraction_id,
                               chunk.chunk_id,
                               validated.scope, validated.revision.source, 'raw', policy,
                               digest, rid, text, count))
        return tuple(results)
    except Exception:
        raise RepresentationError('retrieval representation refused') from None
