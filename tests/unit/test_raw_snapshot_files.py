import pytest
from slaif_raggedized_helper import raw_snapshot_files as files


def test_types_and_non_exception(monkeypatch):
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(None, None, b"", ())
    marker = KeyboardInterrupt()

    def stop(*args):
        raise marker

    monkeypatch.setattr(files, "_validate", stop)
    with pytest.raises(KeyboardInterrupt) as caught:
        files.validate_files(None, None, b"", ())
    assert caught.value is marker
