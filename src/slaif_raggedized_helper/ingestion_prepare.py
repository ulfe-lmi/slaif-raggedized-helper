"""Private operator preparation and verified publication of native bundles."""

from dataclasses import asdict
import time

from . import derived_store, ingestion_profile, ingestion_store, native_chunking as nc
from . import pdf_extraction, provenance_jsonl as jl, provenance_records as p, structured_text
from .source_admission import OriginalStore


class PrepareError(ValueError):
    """Input-free failure; a known published ID is retained when available."""

    def __init__(self, published_bundle_id=None):
        super().__init__('ingestion failed')
        self.published_bundle_id = published_bundle_id


def _check(end):
    if time.monotonic() >= end:
        raise ValueError


def _overview(value, ident):
    return dict(revision_id=value.revision.revision_id, bundle_id=ident,
                adapter=value.adapter, status=value.status, coverage_kind=value.coverage_kind,
                counts=dict(blocks=len(value.blocks), chunks=len(value.chunks),
                            neighbors=len(value.neighbors), receipts=len(value.receipts)))


def inspect(original_path, derived_path, ident, end=None):
    end = time.monotonic() + 180 if end is None else end
    original = derived = None
    try:
        _check(end)
        original = OriginalStore(original_path)
        derived = derived_store.Store(derived_path)
        value = ingestion_store.load(original, derived, ident)
        _check(end)
        return _overview(value, ident)
    except Exception:
        raise PrepareError() from None
    finally:
        if derived is not None:
            derived.close()
        if original is not None:
            original.close()


def prepare(original_path, derived_path, revision_id, adapter, profile, query='', end=None):
    end = time.monotonic() + 180 if end is None else end
    original = derived = None
    ident = None
    try:
        if (type(profile) is not ingestion_profile.Profile or adapter not in
                ('structured_text', 'pdf_extraction') or type(query) is not str
                or len(query) > 10000):
            raise ValueError
        query.encode('utf-8')
        _check(end)
        original = OriginalStore(original_path)
        if adapter == 'structured_text':
            item = structured_text.extract(original, revision_id)
            revision = item.revision
            status, kind = 'complete_text', 'unicode_codepoints'
            coverage = dict(schema_version=1, kind=kind, spans=[asdict(x) for x in item.coverage])
        else:
            if profile.pdf_runtime is None:
                raise ValueError
            item = pdf_extraction.extract(original, revision_id, profile.pdf_runtime)
            revision = item.revision
            status, kind = item.status, 'pdf_pages'
            coverage = dict(schema_version=1, kind=kind,
                            pages=[dict(page=n, status=s) for n, s in item.pages])
        _check(end)
        if not item.blocks:
            return dict(revision_id=revision_id, adapter=adapter, status='no_native_chunks',
                        coverage_kind=kind,
                        counts=dict(blocks=0, chunks=0, neighbors=0, receipts=0))
        definitions = (profile.bge_body, profile.bge_representation, profile.reranker_pair)
        result = nc.build(p.Registry((revision,), (item.dependency,), item.blocks), item.blocks,
                          *definitions, profile.native_runtime, query, profile.chunk_policy)
        _check(end)
        declarations = [dict(role=d.role, artifact_sha256=d.sha256,
                             backend_version=d.backend_version, model_revision=d.model_revision,
                             preprocessing=d.preprocessing) for d in definitions]
        definition = nc._json(dict(version=1, kind='observed-local-native',
                                   policy=asdict(profile.chunk_policy),
                                   definitions=[nc._identity(d) for d in definitions],
                                   query_input_sha256=nc._input_digest(query, None),
                                   serialization=nc._SERIALIZATION)).decode()
        metadata = dict(schema_version=1, kind='native-ingestion-bundle', revision_id=revision_id,
                        extraction=dict(dependency=item.dependency.model_dump(), adapter=adapter,
                                        status=status, coverage_kind=kind,
                                        uncertainty=item.uncertainty),
                        chunking=dict(policy=asdict(profile.chunk_policy), query=query,
                                      definitions=declarations, policy_definition=definition,
                                      policy_id=p.policy_id(definition)),
                        counts=dict(blocks=len(item.blocks), chunks=len(result.chunks),
                                    neighbors=len(result.chunks), receipts=3 * len(result.chunks)))
        def encode(kind, values):
            return jl.encode(kind, tuple(x.model_dump_json().encode() for x in values))
        members = (('blocks', encode('Block', item.blocks)), ('coverage', nc._json(coverage)),
                   ('chunks', encode('Chunk', result.chunks)),
                   ('neighbors', encode('Neighbors', result.neighbors)),
                   ('receipts', result.receipts_json()))
        derived = derived_store.Store(derived_path)
        ident = ingestion_store.publish(original, derived, nc._json(metadata), members)
        _check(end)
        derived.close()
        derived = None
        original.close()
        original = None
        try:
            return inspect(original_path, derived_path, ident, end)
        except PrepareError:
            raise PrepareError(ident) from None
    except PrepareError:
        raise
    except Exception:
        raise PrepareError(ident) from None
    finally:
        if derived is not None:
            derived.close()
        if original is not None:
            original.close()
