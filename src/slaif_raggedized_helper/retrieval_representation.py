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
    """Validate source and count the exact raw representation; refuse atomically."""
    try:
        policy = Policy() if policy is None else policy
        if (type(policy) is not Policy or type(policy.max_tokens) is not int
                or not 1 <= policy.max_tokens <= 1024 or policy.version != 'raw-v1'
                or type(policy.version) is not str or type(policy.separator) is not str
                or policy.separator != '\n\n' or type(policy.max_codepoints) is not int
                or policy.max_codepoints != 100000 or type(policy.max_request_bytes) is not int
                or policy.max_request_bytes != 200000 or type(chunk_id) is not str
                or type(definition) is not native_tokenizers.Definition
                or definition.role != 'bge_representation'
                or definition.backend_version != '0.21.4'
                or type(definition.sha256) is not str
                or not re.fullmatch('[0-9a-f]{64}', definition.sha256)
                or any(type(x) is not str or not 1 <= len(x) <= 256
                       for x in (definition.model_revision, definition.preprocessing))
                or type(runtime) is not native_tokenizers.Runtime):
            raise ValueError
        definition.model_revision.encode('utf-8', errors='strict')
        definition.preprocessing.encode('utf-8', errors='strict')
        validated = ingestion_bundle.validate(store, metadata_json_bytes, members)
        matches = [c for c in validated.chunks if c.chunk_id == chunk_id]
        if len(matches) != 1:
            raise ValueError
        chunk = matches[0]
        components = [validated.revision.source.title, *chunk.heading_path, chunk.text]
        if any(x is not None and type(x) is not str for x in components):
            raise ValueError
        components = [x for x in components[:-1] if x] + [components[-1]]
        if sum(len(x) for x in components) + 2 * (len(components) - 1) > 100000:
            raise ValueError
        text = policy.separator.join(components)
        wire = json.dumps({'text': text, 'pair': None, 'nonce': '0' * 32,
                           'role': definition.role, 'artifact': 0}, ensure_ascii=True,
                          separators=(',', ':')).encode() + b'\n'
        if len(wire) > 200000:
            raise ValueError
        digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        input_digest = hashlib.sha256(json.dumps([text, None], ensure_ascii=True,
                                      separators=(',', ':')).encode()).hexdigest()
        with Session((definition,), runtime) as session:
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
        return Representation(chunk.revision_id, chunk.extraction_id, chunk.chunk_id,
                              validated.scope, validated.revision.source, 'raw', policy,
                              digest, rid, text, count)
    except Exception:
        raise RepresentationError('retrieval representation refused') from None
