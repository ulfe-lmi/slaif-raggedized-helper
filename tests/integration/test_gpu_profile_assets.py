"""Offline wheel and model-free installed GPU profile evidence."""
import base64
import csv
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENV = dict(os.environ, UV_NO_CONFIG='1', UV_PYTHON_DOWNLOADS='never',
           UV_CONCURRENT_BUILDS='1', UV_CONCURRENT_INSTALLS='1',
           UV_CONCURRENT_DOWNLOADS='1', TOKIO_WORKER_THREADS='1', RAYON_NUM_THREADS='1',
           MALLOC_ARENA_MAX='1', UV_LINK_MODE='copy', PYTHONDONTWRITEBYTECODE='1',
           OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
           NUMEXPR_NUM_THREADS='1')


def run(args, cwd):
    return subprocess.run(['timeout', '120', 'prlimit', '--as=1073741824', '--cpu=30',
                           '--', *map(str, args)], cwd=cwd, env=ENV, check=True,
                          capture_output=True, text=True)


@pytest.fixture(scope='module')
def wheel(tmp_path_factory):
    base = tmp_path_factory.mktemp('gpu-wheel')
    source = base / 'source'
    source.mkdir()
    for name in ('pyproject.toml', 'LICENSE', 'README.md'):
        shutil.copy2(ROOT / name, source / name)
    shutil.copytree(ROOT / 'src/slaif_raggedized_helper', source / 'src/slaif_raggedized_helper',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('cpu', 'cpu-v2', 'gpu'):
        target = source / 'worker_profiles' / name
        target.mkdir(parents=True)
        shutil.copy2(ROOT / 'worker_profiles' / name / 'uv.lock', target / 'uv.lock')
    assert sum(p.stat().st_size for p in source.rglob('*') if p.is_file()) < 256 * 1024**2
    run(['uv', 'build', '--wheel', '--offline', '--out-dir', base / 'dist'], source)
    (wheel_path,) = (base / 'dist').glob('*.whl')
    assert wheel_path.stat().st_size < 64 * 1024**2
    with zipfile.ZipFile(wheel_path) as z:
        assert sum(i.file_size for i in z.infolist()) < 64 * 1024**2
        for name in ('cpu', 'cpu-v2', 'gpu'):
            assert z.read(f'slaif_raggedized_helper/_worker_profiles/{name}/uv.lock') == (
                ROOT / 'worker_profiles' / name / 'uv.lock').read_bytes()
        (record,) = [n for n in z.namelist() if n.endswith('.dist-info/RECORD')]
        rows = list(csv.reader(io.StringIO(z.read(record).decode())))
        assert {r[0] for r in rows} == set(z.namelist())
        for name, digest, size in rows:
            if name == record:
                assert not digest and not size
            else:
                data = z.read(name)
                assert digest == 'sha256=' + base64.urlsafe_b64encode(
                    hashlib.sha256(data).digest()).decode().rstrip('=')
                assert int(size) == len(data)
        assert any(n.endswith('/licenses/LICENSE') for n in z.namelist())
        assert any(n.endswith('.dist-info/entry_points.txt') for n in z.namelist())
        from slaif_raggedized_helper import gpu_worker_protocol as wire
        for name in wire.CODE_FILES:
            assert z.read('slaif_raggedized_helper/' + name) == (
                ROOT / 'src/slaif_raggedized_helper' / name).read_bytes()
    print('wheel_sha256', hashlib.sha256(wheel_path.read_bytes()).hexdigest())
    return wheel_path


def install(wheel, prefix, cwd):
    run(['uv', 'pip', 'install', '--python', sys.executable, '--no-index', '--no-deps',
         '--target', prefix, wheel], cwd)


PROBE = r'''
import hashlib, importlib, os, shutil, sys
from pathlib import Path
prefix, packages, root = map(Path, sys.argv[1:4])
src_named = sys.argv[4] == "1"
sys.path[:0] = [str(prefix), str(packages)]
from slaif_raggedized_helper import gpu_embedding_backend as backend, gpu_worker_protocol as wire
assert Path(backend.__file__).is_relative_to(prefix)
assert Path(wire.__file__).is_relative_to(prefix)
lock = prefix / 'slaif_raggedized_helper/_worker_profiles/gpu/uv.lock'
original = lock.read_bytes()
ambient = root / 'worker_profiles/gpu/uv.lock'
ambient.parent.mkdir(parents=True, exist_ok=True)
ambient.write_bytes(original)
class Sentinel(Exception): pass
old_import = importlib.import_module
def intercept(name, *args, **kwargs):
    if name == 'torch': raise Sentinel('first torch')
    return old_import(name, *args, **kwargs)
importlib.import_module = intercept
def valid():
    try: backend._framework()
    except Sentinel as e: assert str(e) == 'first torch'
    else: raise AssertionError('sentinel not reached')
def refused():
    try: backend._framework()
    except (ValueError, OSError): pass
    else: raise AssertionError('bad asset accepted')
valid()
lock.unlink(); refused()
lock.write_bytes(b'bad'); refused()
lock.unlink(); lock.symlink_to(ambient); refused()
lock.unlink(); lock.write_bytes(original); valid()
shutil.rmtree(lock.parents[1]); refused()
# Hide only the installed distribution entry from the selector's bounded scan.
# The actual selector and backend still run on the same module and filesystem.
if src_named:
    scandir = wire.os.scandir
    class FilteredScan:
        def __init__(self, path): self.scan = scandir(path)
        def __enter__(self):
            return (entry for entry in self.scan.__enter__()
                    if not entry.name.lower().startswith('slaif_raggedized_helper-'))
        def __exit__(self, *args): return self.scan.__exit__(*args)
    def bypass(path):
        return FilteredScan(path) if Path(path) == prefix else scandir(path)
    wire.os.scandir = bypass
    try: valid()
    finally: wire.os.scandir = scandir
    refused()
lock.parent.mkdir(parents=True); lock.write_bytes(original); valid()
assert wire.profile(lock, packages)
assert not any(x in sys.modules for x in ('torch', 'transformers', 'safetensors'))
print('preflight-sentinel-and-causal-control', hashlib.sha256(original).hexdigest())
'''


@pytest.mark.parametrize('src_named', [False, True])
def test_installed_preframework(wheel, tmp_path, src_named):
    root = tmp_path / 'project'
    root.mkdir()
    shutil.copy2(ROOT / 'pyproject.toml', root / 'pyproject.toml')
    prefix = root / ('src' if src_named else 'prefix')
    install(wheel, prefix, tmp_path)
    python = Path(os.environ['SLAIF_GPU_TEST_ROOT']) / 'bin/python3.12'
    packages = os.environ['SLAIF_GPU_TEST_PACKAGES']
    result = run([python, '-I', '-S', '-c', PROBE, prefix, packages, root,
                  '1' if src_named else '0'], tmp_path)
    assert 'preflight-sentinel-and-causal-control' in result.stdout
    print(result.stdout.strip())


def test_installed_real_namespace(wheel, tmp_path, monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location('gpu_launch_composition',
        ROOT / 'tests/integration/test_gpu_worker_launch.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    prefix = tmp_path / 'installed'
    install(wheel, prefix, tmp_path)
    original = module._prepared_fixture
    original_frame = module._frame
    expected_profile = {}

    def checked_frame(stream):
        value = original_frame(stream)
        if value.get('ready') is True:
            assert value['profile'] == expected_profile['profile']
        return value

    def installed_fixture(path, patch):
        args, reservation = original(path, patch)
        args['source_root'] = str(prefix / 'slaif_raggedized_helper')
        from slaif_raggedized_helper import gpu_worker_protocol as wire
        expected_profile['profile'] = wire.profile(
            prefix / 'slaif_raggedized_helper/_worker_profiles/gpu/uv.lock',
            Path(args['packages_root']))
        return args, reservation

    monkeypatch.setattr(module, '_frame', checked_frame)
    monkeypatch.setattr(module, '_prepared_fixture', installed_fixture)
    module.test_real_child_namespace_lease_and_protocol(tmp_path, monkeypatch)


@pytest.mark.parametrize('mutation', ['source', 'lock', 'missing', 'symlink', 'capsule_extra'])
def test_installed_revalidation(wheel, tmp_path, monkeypatch, mutation):
    import importlib.util

    from slaif_raggedized_helper import gpu_worker_launch as launch
    spec = importlib.util.spec_from_file_location('gpu_launch_unit_installed',
        ROOT / 'tests/unit/test_gpu_worker_launch.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    prefix = tmp_path / 'installed'
    install(wheel, prefix, tmp_path)
    args, reservation = module._prepared_fixture(tmp_path, monkeypatch)
    package = prefix / 'slaif_raggedized_helper'
    args['source_root'] = str(package)
    prepared = launch.prepare(**args)
    try:
        prepared.launch_arguments()
        if mutation == 'source':
            path = package / 'schema.py'
            path.write_bytes(path.read_bytes() + b'\n')
        elif mutation == 'lock':
            (package / '_worker_profiles/gpu/uv.lock').write_bytes(b'bad')
        elif mutation == 'missing':
            (package / '_worker_profiles/gpu/uv.lock').unlink()
        elif mutation == 'symlink':
            path = package / '_worker_profiles/gpu/uv.lock'
            path.unlink()
            path.symlink_to(ROOT / 'worker_profiles/gpu/uv.lock')
        else:
            (Path(prepared._owner.directory) / 'app/extra').write_bytes(b'x')
        with pytest.raises((launch.LaunchRefused, ValueError, OSError)):
            prepared.launch_arguments()
    finally:
        prepared.close()
        reservation.assert_owned()
        reservation.close()
