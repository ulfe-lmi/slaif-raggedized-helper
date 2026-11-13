"""Atomic primitive and path guard controls."""

import errno
import os

import pytest

from slaif_raggedized_helper import raw_snapshot_publication as publication


def test_actual_no_replace(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(OSError) as exc:
            publication._rename_noreplace(fd, "a", "b")
        assert exc.value.errno == errno.EEXIST
        assert (tmp_path / "a").is_dir() and (tmp_path / "b").is_dir()
        publication._rename_noreplace(fd, "a", "c")
        assert not (tmp_path / "a").exists() and (tmp_path / "c").is_dir()
    finally:
        os.close(fd)


@pytest.mark.parametrize("path", ["/", "relative", "/tmp/../private", "/tmp//private"])
def test_bad_root(path):
    with pytest.raises(ValueError):
        publication._path_check(path)


def test_missing_primitive_refuses(tmp_path, monkeypatch):
    class NoPrimitive:
        pass

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    monkeypatch.setattr(publication.ctypes, "CDLL", lambda *args, **kwargs: NoPrimitive())
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(OSError) as exc:
            publication._rename_noreplace(fd, "a", "b")
        assert exc.value.errno == errno.ENOSYS
        assert (tmp_path / "a").is_dir() and (tmp_path / "b").is_dir()
    finally:
        os.close(fd)
