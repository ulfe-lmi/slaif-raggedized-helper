"""GPU resource selection rejects installed layout downgrade attempts."""
import shutil
from pathlib import Path

import pytest

from slaif_raggedized_helper import gpu_worker_protocol as wire

ROOT = Path(__file__).resolve().parents[2]


def test_source_and_installed_selection(tmp_path):
    project = tmp_path / 'project'
    package = project / 'src/slaif_raggedized_helper'
    package.mkdir(parents=True)
    shutil.copyfile(ROOT / 'pyproject.toml', project / 'pyproject.toml')
    lock = project / 'worker_profiles/gpu/uv.lock'
    lock.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'worker_profiles/gpu/uv.lock', lock)
    assert wire._profile_path(package) == lock
    (project / 'src/slaif_raggedized_helper-1.dist-info').mkdir()
    with pytest.raises(ValueError):
        wire._profile_path(package)
    asset = package / '_worker_profiles/gpu/uv.lock'
    asset.parent.mkdir(parents=True)
    shutil.copyfile(lock, asset)
    assert wire._profile_path(package) == asset
    asset.unlink()
    with pytest.raises((OSError, ValueError)):
        wire.profile(wire._profile_path(package), tmp_path)
    asset.parent.rmdir()
    asset.parent.symlink_to(lock.parent, target_is_directory=True)
    with pytest.raises(ValueError):
        wire._profile_path(package)


def test_fixed_capsule_is_exact():
    assert wire._profile_path(Path('/app/src/slaif_raggedized_helper')) == Path(
        '/app/worker_profiles/gpu/uv.lock')
    with pytest.raises((OSError, ValueError)):
        wire._profile_path(Path('/other/src/slaif_raggedized_helper'))
