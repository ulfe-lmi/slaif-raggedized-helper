import os

import pytest

from slaif_raggedized_helper import raw_snapshot_directory as directory


def test_invalid_configuration_and_nonexception(monkeypatch):
    for root, ident in [
        ("/", "sha256:" + "a" * 64),
        ("/tmp/../x", "sha256:" + "a" * 64),
        ("/tmp/x", "sha256:" + "A" * 64),
    ]:
        with pytest.raises(directory.DirectoryError):
            directory.load_directory(None, None, root, ident)
    marker = KeyboardInterrupt()

    def stop(*args):
        raise marker

    monkeypatch.setattr(directory, "_load", stop)
    with pytest.raises(KeyboardInterrupt) as caught:
        directory.load_directory(None, None, "/tmp/x", "sha256:" + "a" * 64)
    assert caught.value is marker


def test_closed_then_raises_never_retried(tmp_path, monkeypatch):
    owner = directory._Owner()
    fd = owner.open(str(tmp_path), directory._DIR)
    real_close = os.close
    calls = []

    def fail(number):
        calls.append(number)
        real_close(number)
        raise OSError("injected close uncertainty")

    with monkeypatch.context() as patch:
        patch.setattr(os, "close", fail)
        with pytest.raises(OSError):
            owner.close(fd)
    replacement = os.open(str(tmp_path), directory._DIR)
    try:
        assert replacement == fd
        assert owner.cleanup() is None
        os.fstat(replacement)
        assert calls == [fd] and fd in owner.unknown and owner in directory._pending
    finally:
        real_close(replacement)
