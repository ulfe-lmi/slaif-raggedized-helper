import pytest

from slaif_raggedized_helper import derived_store, ingestion_store
from slaif_raggedized_helper.source_admission import OriginalStore


def test_admission_and_closed_stores(tmp_path):
    originals = OriginalStore(tmp_path)
    derived = derived_store.Store(tmp_path)
    for args in [(object(), derived, '0' * 64), (originals, object(), '0' * 64),
                 (originals, derived, b'0' * 64), (originals, derived, '0' * 63)]:
        with pytest.raises(ingestion_store.IngestionStoreError, match='^ingestion store refused$'):
            ingestion_store.load(*args)
    derived.close()
    with pytest.raises(ingestion_store.IngestionStoreError):
        ingestion_store.load(originals, derived, '0' * 64)
    originals.close()
