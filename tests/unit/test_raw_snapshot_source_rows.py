import dataclasses

import pytest

from slaif_raggedized_helper import derived_store, raw_snapshot_source_rows as source
from slaif_raggedized_helper.source_admission import OriginalStore


def test_input_refusals_and_non_exception_propagation(tmp_path, monkeypatch):
    originals = OriginalStore(tmp_path / 'private')
    with derived_store.Store(tmp_path / 'private') as derived:
        try:
            for value in (None, 'a' * 64, b'{}'):
                with pytest.raises(source.SourceRowsError, match='^source rows refused$'):
                    source.load_group(originals, derived, value, 'bad', 'a' * 64)
            class Stop(BaseException):
                pass
            def stop(_):
                raise Stop()
            monkeypatch.setattr(source.raw_snapshot_rows, 'parse', stop)
            with pytest.raises(Stop):
                source.load_group(originals, derived, b'{}', 'a' * 64, 'b' * 64)
        finally:
            originals.close()


def test_return_records_are_frozen():
    row = source.BoundRow(None, b'c', b's', b'p', 'text')
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.rendered_text = 'changed'
