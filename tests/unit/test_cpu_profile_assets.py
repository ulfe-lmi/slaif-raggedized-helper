"""Profile selection refuses bad bundled assets instead of falling back."""

from pathlib import Path

import pytest

from slaif_raggedized_helper import cpu_embedding_worker as cpu


def test_source_and_bundle_selection(tmp_path, monkeypatch):
    source = tmp_path / "src/slaif_raggedized_helper"
    source.mkdir(parents=True)
    monkeypatch.setattr(cpu, "__file__", str(source / "cpu_embedding_worker.py"))
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "slaif-raggedized-helper"\n')
    source_lock = tmp_path / "worker_profiles/cpu-v2/uv.lock"
    source_lock.parent.mkdir(parents=True)
    source_lock.write_bytes(
        (Path(__file__).resolve().parents[2] / "worker_profiles/cpu-v2/uv.lock").read_bytes()
    )
    assert cpu._profile_path() == source_lock
    assert len(cpu._lock(cpu._profile_path())) == 38
    assets = source / "_worker_profiles/cpu-v2"
    assets.mkdir(parents=True)
    path = assets / "uv.lock"
    assert cpu._profile_path() == path
    with pytest.raises((OSError, ValueError)):
        cpu._lock(cpu._profile_path())
    path.write_text("bad")
    with pytest.raises(ValueError):
        cpu._lock(cpu._profile_path())
    path.unlink()
    path.symlink_to(Path(__file__).resolve().parents[2] / "worker_profiles/cpu-v2/uv.lock")
    with pytest.raises((OSError, ValueError)):
        cpu._lock(cpu._profile_path())
    path.unlink()
    assets.rmdir()
    assets.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        cpu._profile_path()


def test_source_named_install_refuses_ambient(tmp_path, monkeypatch):
    source = tmp_path / "src/slaif_raggedized_helper"
    source.mkdir(parents=True)
    monkeypatch.setattr(cpu, "__file__", str(source / "cpu_embedding_worker.py"))
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "slaif-raggedized-helper"\n')
    (source.parent / "slaif_raggedized_helper-0.1.0.dist-info").mkdir()
    with pytest.raises(ValueError):
        cpu._profile_path()
