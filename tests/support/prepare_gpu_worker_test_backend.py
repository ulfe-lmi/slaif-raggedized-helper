"""Prepare a disposable synthetic GPU distribution metadata fixture."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import shlex
import shutil
import signal
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parents[2]
LOCK_HASH = "d3f47d3d2943759967a95694017f32e20b8a29ee7de4df790465a402bc17c334"
WHEELS = {
    "annotated-types": (
        "0.8.0",
        "annotated_types-0.8.0-py3-none-any.whl",
        "f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0",
        13427,
    ),
    "pydantic": (
        "2.14.3",
        "pydantic-2.14.3-py3-none-any.whl",
        "3f7b347782ab7e4cf4c798496ae3a82787d9f21ec12676a9c564355eeef8daa8",
        494071,
    ),
    "pydantic-core": (
        "2.50.4",
        "pydantic_core-2.50.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl",
        "c81d98e27d9d9261909dcccab1ba5d6ea1c98b0bb9470e368604614fd1d36ddd",
        2261727,
    ),
    "tokenizers": (
        "0.23.1",
        "tokenizers-0.23.1-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
        "5075b405006415ea148a992d093699c66eb01952bf59f4d5727089a98bda45a4",
        3346235,
    ),
    "typing-extensions": (
        "4.16.0",
        "typing_extensions-4.16.0-py3-none-any.whl",
        "481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8",
        45571,
    ),
    "typing-inspection": (
        "0.4.5",
        "typing_inspection-0.4.5-py3-none-any.whl",
        "bc210535442b39e1bf2805e0c7a17dfd6a4ace760c84c7f7d16245d23a6b1c39",
        14874,
    ),
}
# Load only the fixed sibling support module; do not change its on-disk or shared state.
_spec = importlib.util.spec_from_file_location(
    "_cpu_v2_bounded_support", Path(__file__).with_name("prepare_cpu_worker_test_backend.py")
)
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)
_support.DISK_LIMIT = 96 * 1024**2


def fixed_inputs(lock, requirements):
    raw = lock.read_bytes()
    if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != LOCK_HASH:
        raise ValueError("lock mismatch")
    req = requirements.read_bytes()
    expected = "".join(
        f"{n}=={v} --hash=sha256:{h}\n" for n, (v, _, h, _) in WHEELS.items()
    ).encode()
    if req != expected:
        raise ValueError("requirements mismatch")
    entries = [p for p in tomllib.loads(raw.decode())["package"] if "registry" in p["source"]]
    pins = {p["name"]: p["version"] for p in entries}
    if len(entries) != 57 or len(pins) != 57 or len(WHEELS) != 6:
        raise ValueError("inventory mismatch")
    if sum(w[3] for w in WHEELS.values()) > 16 * 1024**2:
        raise ValueError("wheel budget exceeded")
    for name, (version, filename, digest, size) in WHEELS.items():
        matches = [p for p in entries if p["name"] == name and p["version"] == version]
        wheels = [w for p in matches for w in p["wheels"] if w["url"].endswith("/" + filename)]
        if (
            len(matches) != 1
            or len(wheels) != 1
            or wheels[0]["hash"] != "sha256:" + digest
            or wheels[0]["size"] != size
        ):
            raise ValueError("wheel mismatch")
    for package in entries:
        for dependency in package.get("dependencies", []):
            if dependency["name"] not in pins:
                raise ValueError("dependency graph mismatch")
    if len(set(pins) - set(WHEELS)) != 51:
        raise ValueError("synthetic inventory mismatch")
    return pins, hashlib.sha256(req).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "worker_profiles/gpu/uv.lock"
    req = Path(__file__).with_name("cpu-worker-test-v2-requirements.txt")
    pins, req_hash = fixed_inputs(lock, req)
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise ValueError("Linux x86_64 required")
    runtime = args.runtime_dir
    if (
        not runtime.is_absolute()
        or str(runtime) != str(runtime.resolve(strict=True))
        or len(str(runtime)) > 4096
        or not runtime.is_dir()
    ):
        raise ValueError("runtime must be canonical absolute directory")
    python = runtime / "bin/python3.12"
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError("runtime executable unavailable")
    target = args.target
    if (
        not target.is_absolute()
        or str(target) != "/tmp/" + target.name
        or target.name in ("", ".", "..")
        or len(target.name) > 200
    ):
        raise ValueError("target must be a new direct child of /tmp")
    if os.path.lexists(target):
        raise ValueError("target already exists")
    uv = shutil.which("uv")
    if not uv or any(
        not os.access(p, os.X_OK)
        for p in ("/usr/bin/bwrap", "/usr/bin/prlimit", "/usr/bin/timeout")
    ):
        raise ValueError("tools unavailable")

    def timed_out(_signum, _frame):
        raise TimeoutError("wall limit")

    signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(120)
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "UV_NO_CONFIG": "1",
        "UV_PYTHON_DOWNLOADS": "never",
        "RAYON_NUM_THREADS": "1",
        "UV_CONCURRENT_INSTALLS": "1",
        "UV_CONCURRENT_DOWNLOADS": "1",
    }
    facts = _support.run(
        [
            str(python),
            "-I",
            "-S",
            "-c",
            "import sys; print(sys.implementation.name); "
            "print('.'.join(map(str, sys.version_info[:3]))); print(sys.base_prefix)",
        ],
        env,
        10,
    ).splitlines()
    if (
        len(facts) != 3
        or facts[0] != "cpython"
        or not facts[1].startswith("3.12.")
        or facts[2] != str(runtime)
    ):
        raise ValueError("runtime facts mismatch")
    _support.run(
        [
            "/usr/bin/prlimit",
            "--as=536870912",
            "--cpu=3",
            "/usr/bin/timeout",
            "5",
            "/usr/bin/bwrap",
            "--unshare-user",
            "--unshare-pid",
            "--unshare-net",
            "--ro-bind",
            "/",
            "/",
            "/bin/true",
        ],
        env,
        10,
    )
    target.mkdir(mode=0o700)
    receipt = target / "setup-evidence.json"
    receipt.write_text('{"state":"partial","cleanup":"UNKNOWN; inspect owned processes"}\n')
    packages = target / "packages"
    packages.mkdir(mode=0o700)
    env.update({"HOME": str(target), "TMPDIR": str(target)})
    install = [
        str(Path(uv).resolve()),
        "--no-config",
        "pip",
        "install",
        "--target",
        str(packages),
        "--python",
        str(python),
        "--index-url",
        "https://pypi.org/simple",
        "--no-cache",
        "--no-deps",
        "--only-binary",
        ":all:",
        "--require-hashes",
        "-r",
        str(req),
    ]
    started = time.monotonic()
    _support.run(install, env, 100, target)
    actual = json.loads(
        _support.run([str(python), "-I", "-c", _support.PROBE, str(packages)], env, 10, target)
    )
    _support.WHEELS = WHEELS
    expected = _support.validate_actual(actual)
    synthetic = {n: v for n, v in pins.items() if n not in expected}
    metadata_bytes = 0
    for name, version in synthetic.items():
        info = packages / (name.replace("-", "_") + "-" + version + ".dist-info")
        info.mkdir(mode=0o700)
        data = f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
        metadata_bytes += len(data.encode())
        if metadata_bytes > 2 * 1024**2:
            raise RuntimeError("metadata limit")
        (info / "METADATA").write_text(data)
    probe = (
        "import json,sys; from importlib.metadata import distributions; "
        "d=list(distributions(path=[sys.argv[1]])); "
        'p={x.metadata["Name"].lower().replace("_","-"):x.version for x in d}; '
        "assert len(p)==len(d); print(json.dumps(p,sort_keys=True))"
    )
    if (
        json.loads(_support.run([str(python), "-I", "-c", probe, str(packages)], env, 10, target))
        != pins
    ):
        raise RuntimeError("metadata mismatch")
    _support.disk_size(target)
    if _support.UNREAPED:
        raise RuntimeError("unreaped child; retain partial target")
    evidence = {
        "state": "complete",
        "fixturekind": "synthetic-gpu-worker-test",
        "runtime": str(runtime),
        "runtime_version": facts[1],
        "unreaped_handles": len(_support.UNREAPED),
        "lock_sha256": LOCK_HASH,
        "requirements_sha256": req_hash,
        "actual_installed": actual,
        "synthetic_metadata_only": synthetic,
        "wheels": WHEELS,
        "network_bytes": "UNKNOWN",
        "sampled_peak_disk_bytes": _support.PEAK_DISK,
        "elapsed_seconds": time.monotonic() - started,
        "limits": "per-process rlimits; sampled disk is not atomic quota",
    }
    data = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if len(data.encode()) > 32768:
        raise RuntimeError("receipt limit")
    receipt.write_text(data)
    print(f"export SLAIF_GPU_TEST_ROOT={shlex.quote(str(runtime))}")
    print(f"export SLAIF_GPU_TEST_PACKAGES={shlex.quote(str(packages))}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, TimeoutError):
        print("GPU fixture setup failed; preserve any partial target.", file=sys.stderr)
        sys.exit(1)
