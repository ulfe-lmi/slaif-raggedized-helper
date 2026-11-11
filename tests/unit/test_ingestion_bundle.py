import pytest

from slaif_raggedized_helper import ingestion_bundle as b
from slaif_raggedized_helper.source_admission import OriginalStore


@pytest.mark.parametrize('metadata,members', [
    (b'{}', ()), (b'{}', []), (b'x' * (b.METADATA_BYTES + 1), ()),
    (b'{}', tuple((name, bytearray()) for name in b.NAMES)),
    (b'{}', tuple((name, b'') for name in reversed(b.NAMES))),
])
def test_raw_refusal_precedes_parse(monkeypatch, metadata, members):
    # The exact trusted class check is exercised without invoking its initializer.
    store = object.__new__(OriginalStore)
    def forbidden(*args):
        raise AssertionError('parser called')
    monkeypatch.setattr(b.native, '_parse', forbidden)
    with pytest.raises(b.BundleError, match='^ingestion bundle refused$'):
        b.validate(store, metadata, members)
