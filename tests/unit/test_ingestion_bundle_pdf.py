import pytest

from slaif_raggedized_helper import ingestion_bundle as bundle
from slaif_raggedized_helper.source_admission import OriginalStore


def test_unknown_dispatch_refused_before_source(monkeypatch):
    store = object.__new__(OriginalStore)
    monkeypatch.setattr(bundle.source, 'validate', lambda *a: pytest.fail('text dispatch'))
    monkeypatch.setattr(bundle.pdf, 'validate', lambda *a: pytest.fail('pdf dispatch'))
    metadata = {'schema_version': 1, 'kind': 'native-ingestion-bundle', 'revision_id': 'x',
                'extraction': {'adapter': 'unknown'}, 'chunking': {},
                'counts': {'blocks': 1, 'chunks': 1, 'neighbors': 1, 'receipts': 3}}
    with pytest.raises(bundle.BundleError):
        bundle.validate(store, bundle._json(metadata), tuple((n, b'') for n in bundle.NAMES))
