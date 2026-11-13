"""Prepare the locked CPU v2 runtime in a new, private disposable directory.

This is a source candidate, not an authorization to download or execute it.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import resource
import selectors
import signal
import ssl
import stat
import subprocess
import sys
import time
import tomllib
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

from packaging.requirements import Requirement
from packaging.tags import compatible_tags, cpython_tags, platform_tags
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "worker_profiles/cpu-v2/uv.lock"
LOCK_HASH = "7cf4c88943cc2b519ad18c0c28cbc2281f159a98704db172e1696ec5ae20b287"
RUNTIME = Path("/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu")
UV = Path("/home/janezp/.local/bin/uv")
TORCH_HASH = "a09987c95ec4cffdb6df798d3d641558110a334cfccce22f2f046d83142bc260"
TORCH_URL = "https://download-r2.pytorch.org/whl/cpu/torch-2.14.0%2Bcpu-cp312-cp312-manylinux_2_28_x86_64.whl"
TORCH_SIZE = 196253793  # Independent zero-body HEAD, not uv-lock metadata.
PAYLOAD_LIMIT = 600 * 1024**2
DISK_ABORT = 5 * 1024**3 // 2
DISK_CEILING = 3 * 1024**3
OUTPUT_LIMIT = 65536
UNREAPED = []
PEAK_DISK = 0


def check_url(url, name):
    p = urlsplit(url)
    host = "download-r2.pytorch.org" if name == "torch" else "files.pythonhosted.org"
    if (
        p.scheme != "https"
        or p.netloc != host
        or p.query
        or p.fragment
        or not p.path.startswith("/")
        or not p.path.endswith(".whl")
    ):
        raise ValueError("unapproved wheel URL")
    return unquote(p.path.rsplit("/", 1)[-1])


def select(lock=LOCK):
    raw = lock.read_bytes()
    if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != LOCK_HASH:
        raise ValueError("lock mismatch")
    entries = tomllib.loads(raw.decode())["package"]
    registries = [p for p in entries if "registry" in p["source"]]
    if len(registries) != 38 or len({p["name"] for p in registries}) != 38:
        raise ValueError("inventory mismatch")
    platforms = list(platform_tags())
    tags = list(cpython_tags((3, 12), platforms=platforms)) + list(
        compatible_tags((3, 12), interpreter="cp312", platforms=platforms)
    )
    rank = {tag: i for i, tag in reversed(list(enumerate(tags)))}
    selected = []
    for p in registries:
        name, version = p["name"], p["version"]
        source = (
            "https://download.pytorch.org/whl/cpu" if name == "torch" else "https://pypi.org/simple"
        )
        if p["source"] != {"registry": source}:
            raise ValueError("registry mismatch")
        candidates = []
        for wheel in p.get("wheels", []):
            filename = check_url(wheel["url"], name)
            dist, ver, build, wheel_tags = parse_wheel_filename(filename)
            if str(dist) != canonicalize_name(name) or ver != Version(version) or build:
                raise ValueError("wheel identity mismatch")
            matches = [rank[t] for t in wheel_tags if t in rank]
            if matches:
                candidates.append((min(matches), wheel, filename))
        candidates.sort(key=lambda c: c[0])
        if not candidates or (len(candidates) > 1 and candidates[0][0] == candidates[1][0]):
            raise ValueError("missing or ambiguous wheel")
        _, w, filename = candidates[0]
        digest = w["hash"].removeprefix("sha256:")
        if w["hash"] != "sha256:" + digest or not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError("invalid digest")
        if name == "torch":
            if version != "2.14.0+cpu" or digest != TORCH_HASH or "size" in w:
                raise ValueError("torch pin mismatch")
            size = TORCH_SIZE
        else:
            size = w.get("size")
        if type(size) is not int or size <= 0 or size > PAYLOAD_LIMIT:
            raise ValueError("invalid size")
        selected.append(
            dict(
                name=name,
                version=version,
                filename=filename,
                url=w["url"],
                sha256=digest,
                size=size,
                size_source="independent HEAD" if name == "torch" else "uv lock",
            )
        )
    if sum(x["size"] for x in selected) > PAYLOAD_LIMIT:
        raise ValueError("payload budget")
    if len({x["filename"] for x in selected}) != 38:
        raise ValueError("duplicate filenames")
    return selected


def validate_target(target):
    # /tmp is the only permitted protected ancestry; avoid alias and symlink ambiguity.
    if not target.is_absolute() or target.parent != Path("/tmp") or target.name in ("", ".", ".."):
        raise ValueError("target must be a direct /tmp child")
    if Path("/tmp").resolve(strict=True) != Path("/tmp") or os.path.lexists(target):
        raise ValueError("target already exists or /tmp is an alias")
    st = Path("/tmp").stat()
    if st.st_uid != 0 or not st.st_mode & 0o1000:
        raise ValueError("unprotected /tmp")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect refused")


def missing_type_allowed(item):
    return (
        item["name"] == "torch"
        and item["version"] == "2.14.0+cpu"
        and item["url"] == TORCH_URL
        and item["sha256"] == TORCH_HASH
        and item["size"] == TORCH_SIZE
    )


def download(item, dest, total, deadline, opener, sample=None, observation=None):
    observation = observation if observation is not None else {}
    observation.clear()
    observation.update(stage="request", artifact=item["name"], error_code="request_failed")
    check_url(item["url"], item["name"])
    if time.monotonic() >= deadline:
        raise TimeoutError("download deadline")
    req = Request(
        item["url"], headers={"Accept-Encoding": "identity", "User-Agent": "cpu-v2-locked/1"}
    )
    with opener.open(req, timeout=min(20, deadline - time.monotonic())) as response:
        observation.update(stage="headers", error_code="headers_refused")
        if response.status != 200 or response.geturl() != item["url"]:
            raise ValueError("unexpected response")
        encodings = response.headers.get_all("Content-Encoding", [])
        if len(encodings) > 1 or (encodings and encodings[0].lower() != "identity"):
            raise ValueError("encoded response")
        types = response.headers.get_all("Content-Type", [])
        raw_type = types[0] if len(types) == 1 else None
        observation["content_type_raw"] = (
            raw_type if isinstance(raw_type, str) and len(raw_type) <= 256 else None
        )
        if not types and missing_type_allowed(item):
            observation["content_type_policy"] = "exact_torch_missing"
        elif (
            len(types) == 1
            and isinstance(raw_type, str)
            and len(raw_type) <= 256
            and re.fullmatch(
                r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+"
                r"(?:\s*;\s*[A-Za-z0-9!#$&^_.+-]+="
                r"(?:[A-Za-z0-9!#$&^_.+-]+|\"[A-Za-z0-9 !#$&^_.+-]*\"))*",
                raw_type,
            )
            and raw_type.split(";", 1)[0].lower()
            in ("application/octet-stream", "application/zip", "binary/octet-stream")
        ):
            observation["content_type_policy"] = "declared_allowed"
        else:
            observation["content_type_policy"] = "refused"
            raise ValueError("content type")
        lengths = response.headers.get_all("Content-Length", [])
        length = lengths[0] if len(lengths) == 1 else None
        if length is None or not length.isdecimal() or int(length) != item["size"]:
            raise ValueError("content length")
        observation.update(
            stage="body", error_code="body_verification_failed", declared_content_length=length
        )
        count = 0
        digest = hashlib.sha256()
        with dest.open("xb") as out:
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError("download deadline")
                chunk = response.read(65536)
                if not chunk:
                    break
                count += len(chunk)
                total[0] += len(chunk)  # Account response bytes before any write.
                if count > item["size"] or total[0] > PAYLOAD_LIMIT:
                    raise ValueError("payload limit")
                digest.update(chunk)
                out.write(chunk)
                if sample:
                    sample()
        if count != item["size"] or digest.hexdigest() != item["sha256"]:
            raise ValueError("wheel count or digest mismatch")
    observation.update(
        stage="verified", error_code=None, actual_bytes=count, actual_sha256=digest.hexdigest()
    )
    return count


def disk_size(root):
    global PEAK_DISK
    total = 0
    enumerated_dirs = set()

    def walk_error(error):
        if isinstance(error, FileNotFoundError) and error.filename in enumerated_dirs:
            return
        raise error

    for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        enumerated_dirs.update(os.fspath(Path(parent) / n) for n in dirs)
        for n in dirs + files:
            p = Path(parent) / n
            try:
                info = p.lstat()
            except FileNotFoundError:
                # Only an enumerated entry disappearing is tolerated.
                continue
            if stat.S_ISLNK(info.st_mode):
                continue
            if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                raise ValueError("unexpected sampled entry type")
            if type(info.st_size) is not int or info.st_size < 0:
                raise ValueError("invalid sampled size")
            total += info.st_size
            if total > DISK_ABORT:
                raise RuntimeError("sampled disk abort")
    PEAK_DISK = max(PEAK_DISK, total)
    return total


class ChildFailure(RuntimeError):
    """Known status and bounded decoded output from an owned child."""

    def __init__(self, code, output):
        super().__init__("child failed")
        self.code = code
        self.output = output


def prioritize(primary, later):
    """Keep the first failure except when a new interrupt supersedes an ordinary error."""
    if primary is None:
        return later
    if isinstance(primary, Exception) and not isinstance(later, Exception):
        return later
    return primary


def safe_note(error, note):
    try:
        error.add_note(note)
    except BaseException as exc:
        return exc
    return None


def run(argv, env, timeout, root=None):
    child = subprocess.Popen(
        argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True
    )
    deadline = time.monotonic() + timeout
    output = bytearray()
    original = None
    try:
        with selectors.DefaultSelector() as sel:
            sel.register(child.stdout, selectors.EVENT_READ)
            while sel.get_map():
                left = remaining(deadline)
                if root:
                    disk_size(root)
                for key, _ in sel.select(min(0.1, left)):
                    chunk = os.read(key.fd, OUTPUT_LIMIT + 1 - len(output))
                    if not chunk:
                        sel.unregister(key.fileobj)
                    else:
                        output.extend(chunk)
                        if len(output) > OUTPUT_LIMIT:
                            raise RuntimeError("child output limit")
        # Observe exit without reaping: the leader PID remains reserved while its
        # owned process group is cleaned, including descendants that closed stdout.
        while not os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT):
            time.sleep(min(0.05, remaining(deadline)))
    except BaseException as exc:
        original = exc
        raise
    finally:
        cleanup_error = None
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except BaseException as exc:
            cleanup_error = exc
        try:
            child.wait(timeout=2)
        except BaseException as exc:
            cleanup_error = prioritize(cleanup_error, exc)
            UNREAPED.append(child)
        try:
            child.stdout.close()
        except BaseException as exc:
            cleanup_error = prioritize(cleanup_error, exc)
        if cleanup_error is not None:
            if child not in UNREAPED:
                UNREAPED.append(child)
            chosen = prioritize(original, cleanup_error)
            if original is not None:
                diagnostic = safe_note(chosen, "owned child cleanup failed; handle retained")
                if diagnostic is not None:
                    chosen = prioritize(chosen, diagnostic)
            if chosen is not original:
                raise chosen
    decoded = output.decode("utf-8")
    if any(not (c.isprintable() or c in "\n\r\t") for c in decoded):
        raise ValueError("malformed child output")
    if child.returncode != 0:
        raise ChildFailure(child.returncode, decoded)
    return decoded


PROBE = """import json,sys
from importlib.metadata import distributions
items=[]
for d in distributions(path=[sys.argv[1]]):
    items.append([d.metadata['Name'],d.version,d.requires or []])
print(json.dumps(items))
"""


def validate_metadata(rows, selected):
    expected = {x["name"]: x["version"] for x in selected}
    actual = {}
    for name, version, _ in rows:
        name = canonicalize_name(name)
        if name in actual:
            raise ValueError("duplicate distribution")
        actual[name] = version
    if actual != expected:
        raise ValueError("distribution mismatch")
    for _, _, requirements in rows:
        for text in requirements:
            req = Requirement(text)
            if req.marker and not req.marker.evaluate(
                {
                    "extra": "",
                    "python_version": "3.12",
                    "python_full_version": "3.12.15",
                    "implementation_name": "cpython",
                    "platform_python_implementation": "CPython",
                    "sys_platform": "linux",
                    "platform_system": "Linux",
                    "platform_machine": "x86_64",
                    "os_name": "posix",
                }
            ):
                continue
            name = canonicalize_name(req.name)
            if name not in actual or Version(actual[name]) not in req.specifier:
                raise ValueError("dependency mismatch")
    return actual


def sanitized_env(target):
    return {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "HOME": str(target),
        "TMPDIR": str(target / "tmp"),
        "UV_CACHE_DIR": str(target / "cache"),
        "UV_NO_CONFIG": "1",
        "UV_PYTHON_DOWNLOADS": "never",
        "UV_OFFLINE": "1",
        "UV_CONCURRENT_DOWNLOADS": "1",
        "UV_CONCURRENT_INSTALLS": "1",
        "UV_CONCURRENT_BUILDS": "1",
        "RAYON_NUM_THREADS": "1",
        "TOKIO_WORKER_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MALLOC_ARENA_MAX": "1",
    }


def install_commands(target, selected):
    venv = target / "venv"
    python = RUNTIME / "bin/python3.12"
    create = [
        str(UV),
        "--no-config",
        "venv",
        "--offline",
        "--no-python-downloads",
        "--python",
        str(python),
        str(venv),
    ]
    install = [
        str(UV),
        "--no-config",
        "pip",
        "install",
        "--offline",
        "--no-index",
        "--no-deps",
        "--require-hashes",
        "--only-binary",
        ":all:",
        "--python",
        str(venv / "bin/python"),
        "--find-links",
        str(target / "wheels"),
        "-r",
        str(target / "requirements.txt"),
    ]
    return create, install


def run_setup(target, runtime_dir, *, opener=None, runner=run):
    started = time.monotonic()
    deadline = started + 600
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise ValueError("platform mismatch")
    if any(os.environ.get(n) for n in ("VIRTUAL_ENV", "CONDA_PREFIX", "PYTHONPATH")):
        raise ValueError("ambient application environment")
    if runtime_dir != RUNTIME or runtime_dir.resolve(strict=True) != RUNTIME:
        raise ValueError("runtime mismatch")
    validate_target(target)
    selected = select()
    python = RUNTIME / "bin/python3.12"
    if (
        hashlib.sha256(python.read_bytes()).hexdigest()
        != "708fefcd7df61b1327cb7b9740fafd42cb2f6cd1d387378892d4a28b7479fb78"
    ):
        raise ValueError("interpreter identity mismatch")
    if (
        hashlib.sha256(UV.read_bytes()).hexdigest()
        != "b65f23a420c4acc96427efb30e5ed9bc0f7e25d2d712000f6ede77c1a0de5f46"
    ):
        raise ValueError("uv identity mismatch")
    env = sanitized_env(target)
    facts_cmd = [
        str(python),
        "-I",
        "-S",
        "-c",
        "import sys; print(sys.implementation.name); "
        'print(".".join(map(str,sys.version_info[:3]))); print(sys.base_prefix)',
    ]
    facts = runner(facts_cmd, env, 10).splitlines()
    if facts != ["cpython", "3.12.15", str(RUNTIME)]:
        raise ValueError("interpreter facts mismatch")
    target.mkdir(mode=0o700)
    receipt = target / "setup-evidence.json"
    total = [0]
    evidence = {
        "state": "partial",
        "lock_sha256": LOCK_HASH,
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "interpreter": str(python),
        "interpreter_sha256": "708fefcd7df61b1327cb7b9740fafd42cb2f6cd1d387378892d4a28b7479fb78",
        "uv_sha256": "b65f23a420c4acc96427efb30e5ed9bc0f7e25d2d712000f6ede77c1a0de5f46",
        "selected": selected,
        "verified": [],
        "verification_details": [],
        "observation": {"stage": "setup", "artifact": None, "error_code": "setup_failed"},
        "commands": [{"argv": facts_cmd, "exit": 0}],
        "limits": {
            "payload_bytes": PAYLOAD_LIMIT,
            "as_bytes_per_process": 2 * 1024**3,
            "cpu_seconds_per_process": 120,
            "wall_seconds": 600,
            "sampled_disk_abort_bytes": DISK_ABORT,
            "disk_ceiling_bytes": DISK_CEILING,
        },
        "accounting": "Payload bytes exclude HTTP/TLS overhead; disk sampling is not a quota.",
        "target": str(target),
        "target_uid": os.getuid(),
    }

    save_failed = [False]

    def save():
        evidence["payload_bytes_observed"] = total[0]
        evidence["elapsed_seconds"] = time.monotonic() - started
        evidence["sampled_peak_disk_bytes"] = PEAK_DISK
        evidence["unresolved_children"] = [p.pid for p in UNREAPED]
        try:
            data = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
            pending = target / ".setup-evidence.pending"
            with pending.open("x") as stream:
                stream.write(data)
            os.replace(pending, receipt)
        except BaseException:
            save_failed[0] = True
            raise

    save()
    peak = [0]

    def sample():
        peak[0] = max(peak[0], disk_size(target))
        evidence["sampled_peak_disk_bytes"] = peak[0]

    try:
        for n in ("wheels", "tmp", "cache"):
            (target / n).mkdir(mode=0o700)
        opener = opener or build_opener(
            ProxyHandler({}),
            NoRedirect(),
            HTTPSHandler(
                context=ssl.create_default_context(cafile="/etc/ssl/certs/ca-certificates.crt")
            ),
        )
        for item in selected:
            download(
                item,
                target / "wheels" / item["filename"],
                total,
                deadline,
                opener,
                sample,
                evidence["observation"],
            )
            evidence["verification_details"].append(dict(evidence["observation"]))
            evidence["verified"].append(item["name"])
            sample()
            save()
        if len(evidence["verified"]) != 38:
            raise RuntimeError("incomplete verification")
        evidence["observation"] = dict(
            stage="requirements", artifact=None, error_code="requirements_failed"
        )
        (target / "requirements.txt").write_text(
            "".join(f"{x['name']}=={x['version']} --hash=sha256:{x['sha256']}\n" for x in selected)
        )
        for cmd in install_commands(target, selected):
            evidence["observation"].update(
                stage="install", artifact=None, error_code="install_failed"
            )
            record = {"argv": cmd, "exit": "unresolved"}
            evidence["commands"].append(record)
            save()
            runner(cmd, env, min(remaining(deadline), 300), target)
            record["exit"] = 0
            sample()
            save()
        evidence["observation"].update(
            stage="metadata", artifact=None, error_code="metadata_failed"
        )
        site = target / "venv/lib/python3.12/site-packages"
        probe = [str(python), "-I", "-S", "-c", PROBE, str(site)]
        record = {"argv": probe, "exit": "unresolved"}
        evidence["commands"].append(record)
        save()
        rows = json.loads(runner(probe, env, min(remaining(deadline), 30), target))
        record["exit"] = 0
        evidence["installed"] = validate_metadata(rows, selected)
        sample()
        if UNREAPED:
            raise RuntimeError("unresolved children")
        evidence["observation"].update(stage="complete", error_code=None)
        evidence["state"] = "complete"
    except BaseException as exc:
        # Do not stringify arbitrary exceptions or retry an uncertain receipt write.
        evidence["failure"] = "operation failed; details unavailable"
        if type(exc) is ChildFailure and evidence["commands"][-1]["exit"] == "unresolved":
            record = evidence["commands"][-1]
            record["exit"] = exc.code
            record["output"] = exc.output
            record["output_bytes"] = len(exc.output.encode("utf-8"))
            record["output_truncated"] = False
            evidence["failure"] = "owned child failed"
        if not save_failed[0]:
            try:
                save()
            except BaseException as save_error:
                chosen = prioritize(exc, save_error)
                diagnostic = safe_note(chosen, "partial receipt update failed")
                if diagnostic is not None:
                    chosen = prioritize(chosen, diagnostic)
                if chosen is not exc:
                    raise chosen
        raise
    save()
    return evidence


def remaining(deadline):
    value = deadline - time.monotonic()
    if value <= 0:
        raise TimeoutError("overall deadline")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args()

    def timeout(_sig, _frame):
        raise TimeoutError("overall deadline")

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(600)
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (DISK_CEILING, DISK_CEILING))
    run_setup(args.target, args.runtime_dir)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
        print(f"CPU v2 setup failed; preserve partial target: {exc}", file=sys.stderr)
        sys.exit(1)
