"""Build and exercise the actual wheel in an isolated private prefix."""

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

ROOT = Path(__file__).resolve().parents[2]
ENV = dict(
    os.environ,
    UV_NO_CONFIG="1",
    UV_PYTHON_DOWNLOADS="never",
    UV_CONCURRENT_BUILDS="1",
    UV_CONCURRENT_INSTALLS="1",
    UV_CONCURRENT_DOWNLOADS="1",
    TOKIO_WORKER_THREADS="1",
    RAYON_NUM_THREADS="1",
    MALLOC_ARENA_MAX="1",
    UV_LINK_MODE="copy",
    OPENBLAS_NUM_THREADS="1",
    OMP_NUM_THREADS="1",
    MKL_NUM_THREADS="1",
    NUMEXPR_NUM_THREADS="1",
    PYTHONDONTWRITEBYTECODE="1",
)


def run(args, cwd, env=ENV):
    return subprocess.run(
        ["timeout", "120", "prlimit", "--as=1073741824", "--cpu=30", "--", *map(str, args)],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_wheel_profile_and_contract(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("pyproject.toml", "LICENSE", "README.md"):
        shutil.copy2(ROOT / name, source / name)
    shutil.copytree(
        ROOT / "src/slaif_raggedized_helper",
        source / "src/slaif_raggedized_helper",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    for name in ("cpu-v2", "cpu", "gpu"):
        target = source / "worker_profiles" / name
        target.mkdir(parents=True)
        shutil.copy2(ROOT / "worker_profiles" / name / "uv.lock", target / "uv.lock")
    assert sum(p.stat().st_size for p in source.rglob("*") if p.is_file()) < 256 * 1024**2
    run(["uv", "build", "--wheel", "--offline", "--out-dir", tmp_path / "dist"], source)
    (wheel,) = (tmp_path / "dist").glob("*.whl")
    assert wheel.stat().st_size < 64 * 1024**2
    with zipfile.ZipFile(wheel) as z:
        assert sum(i.file_size for i in z.infolist()) < 64 * 1024**2
        for name in ("cpu-v2", "cpu", "gpu"):
            assert (
                z.read(f"slaif_raggedized_helper/_worker_profiles/{name}/uv.lock")
                == (ROOT / "worker_profiles" / name / "uv.lock").read_bytes()
            )
        (record,) = [n for n in z.namelist() if n.endswith(".dist-info/RECORD")]
        rows = list(csv.reader(io.StringIO(z.read(record).decode())))
        assert {r[0] for r in rows} == set(z.namelist())
        for name, digest, size in rows:
            if name == record:
                assert not digest and not size
            else:
                data = z.read(name)
                assert digest == "sha256=" + base64.urlsafe_b64encode(
                    hashlib.sha256(data).digest()
                ).decode().rstrip("=")
                assert int(size) == len(data)
        for name in (
            "cpu_embedding_worker.py",
            "cpu_embedding_worker_main.py",
            "cpu_embedding_backend.py",
            "cpu_execution_contract.py",
        ):
            assert f"slaif_raggedized_helper/{name}" in z.namelist()
        print(
            "wheel",
            wheel.stat().st_size,
            "expanded",
            sum(i.file_size for i in z.infolist()),
            "entries",
            len(z.infolist()),
            "sha256",
            hashlib.sha256(wheel.read_bytes()).hexdigest(),
        )
        assert any(n.endswith(".dist-info/entry_points.txt") for n in z.namelist())
        assert any(n.endswith("/licenses/LICENSE") for n in z.namelist())
    prefix = tmp_path / "prefix"
    run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            "--no-index",
            "--no-deps",
            "--target",
            prefix,
            wheel,
        ],
        tmp_path,
    )
    probe = r"""
import hashlib, json, os, shutil, sys
from dataclasses import replace
from pathlib import Path
from slaif_raggedized_helper import cpu_embedding_worker as w, cpu_execution_contract as c
from slaif_raggedized_helper import embedding_artifacts as a, native_tokenizers as n
from test_cpu_embedding_backend import make_tree
from test_native_tokenizers import make_native
prefix, tmp, checkout = map(Path, sys.argv[1:])
assert Path(w.__file__).is_relative_to(prefix)
lock = w._profile_path()
assert lock.is_relative_to(prefix / 'slaif_raggedized_helper')
assert len(w._lock(lock)) == 38
packages = Path(os.environ['SLAIF_CPU_V2_TEST_PACKAGES'])
profile = w._profile(lock, packages)
paths, runtime, _ = make_native(tmp)
root = tmp / 'model'
manifest, _, _, definition, token = make_tree(root)
data = paths[0].read_bytes()
(root / 'tokenizer.json').write_bytes(data)
entry = next(x for x in manifest['files'] if x['role'] == 'tokenizer')
entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
raw = json.dumps(manifest).encode()
inv = a.verify_artifacts(raw, root)
token = replace(token, sha256=entry['sha256'])
cpu_runtime = n.Runtime(Path(os.environ['SLAIF_CPU_V2_TEST_ROOT']), packages, 'python3.12')
planned = c.prepare(raw, root, definition, token, inv.inventory_id, runtime, cpu_runtime)
record = json.loads(planned.record_bytes)
assert record['worker']['profile'] == profile and record['worker']['code'] == w._code_identity()
assert record['space'] == planned.space_id and record['hardware_qualification'] == 'unknown'
original = lock.read_bytes()
ambient = prefix.parent / 'worker_profiles/cpu-v2/uv.lock'
ambient.parent.mkdir(parents=True)
ambient.write_bytes(original)
def refused():
    try: w._lock(w._profile_path())
    except (ValueError, OSError): pass
    else: raise AssertionError('bad asset accepted')
    try: c.prepare(raw, root, definition, token, inv.inventory_id, runtime, cpu_runtime)
    except c.ContractError: pass
    else: raise AssertionError('bad contract accepted')
lock.unlink(); refused()
lock.write_bytes(b'bad'); refused()
lock.unlink(); lock.symlink_to(checkout); refused()
lock.unlink(); lock.write_bytes(original)
assert w._profile(w._profile_path(), packages) == profile
assert c.prepare(raw, root, definition, token, inv.inventory_id, runtime, cpu_runtime) == planned
shutil.rmtree(lock.parents[1])
refused()
lock.parent.mkdir(parents=True)
lock.write_bytes(original)
assert w._profile(w._profile_path(), packages) == profile
assert c.prepare(raw, root, definition, token, inv.inventory_id, runtime, cpu_runtime) == planned
assert not any(x in sys.modules for x in ('torch', 'transformers', 'safetensors'))
print('installed profile, contract and controls passed',
      hashlib.sha256(original).hexdigest(), planned.fingerprint)
"""
    env = dict(ENV, PYTHONPATH=os.pathsep.join((str(prefix), str(ROOT / "tests/unit"))))
    result = run(
        [sys.executable, "-c", probe, prefix, tmp_path, ROOT / "worker_profiles/cpu-v2/uv.lock"],
        tmp_path,
        env,
    )
    assert "installed profile, contract and controls passed" in result.stdout
    print(result.stdout.strip())
    # A real wheel installed into a source-looking prefix must never fall back.
    src_parent = tmp_path / "source-looking"
    src_parent.mkdir()
    shutil.copy2(ROOT / "pyproject.toml", src_parent / "pyproject.toml")
    src_prefix = src_parent / "src"
    run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            "--no-index",
            "--no-deps",
            "--target",
            src_prefix,
            wheel,
        ],
        tmp_path,
    )
    env = dict(ENV, PYTHONPATH=os.pathsep.join((str(src_prefix), str(ROOT / "tests/unit"))))
    result = run(
        [
            sys.executable,
            "-c",
            probe,
            src_prefix,
            src_parent,
            ROOT / "worker_profiles/cpu-v2/uv.lock",
        ],
        tmp_path,
        env,
    )
    assert "installed profile, contract and controls passed" in result.stdout
    print("src prefix:", result.stdout.strip())
    print("private bytes", sum(p.stat().st_size for p in tmp_path.rglob("*") if p.is_file()))
