"""Create a private synthetic metadata capsule for trusted-fake CPU worker tests."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import selectors
import shlex
import shutil
import signal
import subprocess
import sys
import time
import tomllib

LOCK_HASH = 'e0a2b1be5601e141b1dca46cd054c77850344d5123424ed05f176a9621a41299'
# Versions, wheel filenames, SHA256s and sizes are selected from the accepted lock.
WHEELS = {
    'annotated-types': ('0.8.0', 'annotated_types-0.8.0-py3-none-any.whl',
                        'f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0', 13427),
    'pydantic': ('2.14.3', 'pydantic-2.14.3-py3-none-any.whl',
                 '3f7b347782ab7e4cf4c798496ae3a82787d9f21ec12676a9c564355eeef8daa8', 494071),
    'pydantic-core': ('2.50.4',
                      'pydantic_core-2.50.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl',
                      'c81d98e27d9d9261909dcccab1ba5d6ea1c98b0bb9470e368604614fd1d36ddd', 2261727),
    'tokenizers': ('0.21.4',
                   'tokenizers-0.21.4-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl',
                   '51b7eabb104f46c1c50b486520555715457ae833d5aee9ff6ae853d1130506ff', 3115426),
    'typing-extensions': ('4.16.0', 'typing_extensions-4.16.0-py3-none-any.whl',
                         '481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8', 45571),
    'typing-inspection': ('0.4.5', 'typing_inspection-0.4.5-py3-none-any.whl',
                         'bc210535442b39e1bf2805e0c7a17dfd6a4ace760c84c7f7d16245d23a6b1c39', 14874),
}
LIMIT = 8192
DISK_LIMIT = 3 * 1024**3
ROOT = Path(__file__).resolve().parents[2]
UNREAPED = []
PEAK_DISK = 0


def fixed_inputs(lock, requirements):
    raw = lock.read_bytes()
    if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != LOCK_HASH:
        raise ValueError('lock mismatch')
    text = requirements.read_bytes()
    expected = ''.join(f'{name}=={v} --hash=sha256:{h}\n'
                       for name, (v, _, h, _) in WHEELS.items()).encode()
    if text != expected:
        raise ValueError('requirements mismatch')
    entries = tomllib.loads(raw.decode())['package']
    pins = {p['name']: p['version'] for p in entries if 'registry' in p['source']}
    if len(pins) != 28:
        raise ValueError('lock inventory mismatch')
    for name, (version, filename, digest, size) in WHEELS.items():
        matching = [p for p in entries if p['name'] == name and p['version'] == version]
        if len(matching) != 1 or pins.get(name) != version:
            raise ValueError('wheel package mismatch')
        wheels = [w for w in matching[0]['wheels'] if w['url'].endswith('/' + filename)]
        if len(wheels) != 1 or wheels[0]['hash'] != 'sha256:' + digest or wheels[0]['size'] != size:
            raise ValueError('wheel pin mismatch')
    return pins, hashlib.sha256(text).hexdigest()


def disk_size(root):
    global PEAK_DISK
    total = 0
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            try:
                if path.is_symlink():
                    continue
                total += path.stat().st_size
            except FileNotFoundError:
                continue
            if total > DISK_LIMIT:
                raise RuntimeError('disk limit exceeded')
    PEAK_DISK = max(PEAK_DISK, total)
    return total


def cleanup(child):
    """Bound cleanup, retain unreaped ownership, and return the first cleanup error."""
    error = None
    for _ in range(2):
        try:
            os.killpg(child.pid, signal.SIGKILL)
            break
        except ProcessLookupError:
            break
        except BaseException as exc:
            if error is None or (isinstance(exc, (KeyboardInterrupt, SystemExit))
                                 and isinstance(error, Exception)):
                error = exc
    try:
        child.stdout.close()
    except BaseException as exc:
        if error is None or (isinstance(exc, (KeyboardInterrupt, SystemExit))
                             and isinstance(error, Exception)):
            error = exc
    reaped = False
    for _ in range(2):
        try:
            child.wait(timeout=1)
            reaped = True
            break
        except BaseException as exc:
            if error is None or (isinstance(exc, (KeyboardInterrupt, SystemExit))
                                 and isinstance(error, Exception)):
                error = exc
    if not reaped:
        UNREAPED.append(child)
    return error


def run(argv, env, timeout, disk=None):
    """Capture at most LIMIT combined bytes; kill and reap the whole owned group on failure."""
    child = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             start_new_session=True)
    deadline = time.monotonic() + timeout
    output = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('child timeout')
                if disk:
                    disk_size(disk)
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fd, LIMIT + 1 - len(output))
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        output.extend(chunk)
                        if len(output) > LIMIT:
                            raise RuntimeError('child output exceeds limit')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('child timeout')
        if child.wait(timeout=remaining) != 0:
            raise RuntimeError('child failed')
        return output.decode('utf-8')
    finally:
        original = sys.exception()
        error = cleanup(child)
        if error is not None:
            if original is not None:
                original.add_note('bounded child cleanup encountered an error')
            else:
                raise error



PROBE = r'''
import json, sys
from importlib.metadata import distributions
sys.path.insert(0, sys.argv[1])
ds = list(distributions(path=[sys.argv[1]]))
items = {d.metadata['Name'].lower().replace('_', '-'): d.version for d in ds}
assert len(items) == len(ds)
requirements = {d.metadata['Name'].lower().replace('_', '-'): d.requires or [] for d in ds}
from pydantic import BaseModel, ValidationError
class M(BaseModel):
    x: int
assert M(x='12').x == 12
try:
    M(x='no')
except ValidationError:
    pass
else:
    raise AssertionError('validation did not reject')
from tokenizers import Tokenizer, models
assert Tokenizer(models.WordLevel({'[UNK]': 0}, unk_token='[UNK]')).encode('x').ids == [0]
assert not any(x in sys.modules for x in ('torch', 'transformers', 'numpy'))
print(json.dumps({'actual': items, 'requires': requirements}, sort_keys=True))
'''


def validate_actual(actual):
    expected = {name: item[0] for name, item in WHEELS.items()}
    if actual['actual'] != expected:
        raise RuntimeError('actual installed inventory mismatch')
    requires = actual['requires']
    for name, deps in {'pydantic': ('annotated-types', 'pydantic-core', 'typing-extensions',
                                     'typing-inspection'),
                       'pydantic-core': ('typing-extensions',),
                       'typing-inspection': ('typing-extensions',)}.items():
        if any(not any(req.lower().replace('_', '-').startswith(dep) for req in requires[name])
               for dep in deps):
            raise RuntimeError('actual dependency graph mismatch')
    return expected


def main():
    started = time.monotonic()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_start = usage.ru_utime + usage.ru_stime + children.ru_utime + children.ru_stime
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != 'linux' or platform.machine() != 'x86_64':
        raise RuntimeError('Linux x86-64 required')
    uv = shutil.which('uv')
    if not uv or any(not os.access(p, os.X_OK) for p in
                     ('/usr/bin/bwrap', '/usr/bin/prlimit', '/usr/bin/timeout')):
        raise RuntimeError('required tools unavailable')
    # These rlimits apply separately to each descendant, not to the process tree in aggregate.
    def wall_timeout(_signum, _frame):
        raise TimeoutError('setup wall limit')

    signal.signal(signal.SIGALRM, wall_timeout)
    signal.alarm(600)
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (DISK_LIMIT, DISK_LIMIT))
    runtime = args.runtime_dir.resolve(strict=True)
    python = runtime / 'bin/python3.12'
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'UV_NO_CONFIG': '1',
           'UV_PYTHON_DOWNLOADS': 'never', 'RAYON_NUM_THREADS': '2',
           'UV_CONCURRENT_INSTALLS': '1', 'UV_CONCURRENT_DOWNLOADS': '1'}
    tools_cmd = ['/usr/bin/prlimit', '--as=536870912', '--cpu=3',
                 '/usr/bin/timeout', '5', '/usr/bin/bwrap', '--unshare-user',
                 '--unshare-pid', '--unshare-net', '--ro-bind', '/', '/', '/bin/true']
    run(tools_cmd, env, 10)
    runtime_cmd = [str(python), '-I', '-S', '-c',
                   'import sys; print(sys.implementation.name); '
                   'print(".".join(map(str,sys.version_info[:3]))); print(sys.base_prefix)']
    facts = run(runtime_cmd, env, 10).splitlines()
    if (len(facts) != 3 or facts[0] != 'cpython' or not facts[1].startswith('3.12.')
            or Path(facts[2]).resolve() != runtime):
        raise RuntimeError('runtime must be standalone CPython 3.12')
    lock = ROOT / 'worker_profiles/cpu/uv.lock'
    requirements = Path(__file__).with_name('cpu-worker-test-requirements.txt')
    pins, req_hash = fixed_inputs(lock, requirements)
    target = args.target.absolute()
    target.mkdir(mode=0o700)  # Atomic: never reuse or remove an existing path.
    target.chmod(0o700)
    packages = target / 'packages'
    packages.mkdir(mode=0o700)
    env.update({'HOME': str(target), 'TMPDIR': str(target)})
    install = [str(Path(uv).resolve()), '--no-config', 'pip', 'install', '--target', str(packages),
               '--python', str(python), '--index-url', 'https://pypi.org/simple', '--no-cache',
               '--no-deps', '--only-binary', ':all:', '--require-hashes', '-r', str(requirements)]
    # Receipt exists even if installation fails; never delete an uncertain partial capsule.
    receipt = target / 'setup-evidence.json'
    receipt.write_text(json.dumps({'fixturekind': 'synthetic-cpu-worker-test-v1',
                                   'state': 'partial'}) + '\n')
    run(install, env, 120, target)
    probe_cmd = [str(python), '-I', '-c', PROBE, str(packages)]
    actual = json.loads(run(probe_cmd, env, 10, target))
    expected = validate_actual(actual)
    synthetic = {name: version for name, version in pins.items() if name not in expected}
    if len(synthetic) != 22:
        raise RuntimeError('synthetic inventory mismatch')
    for name, version in synthetic.items():
        info = packages / (name.replace('-', '_') + '-' + version + '.dist-info')
        info.mkdir(mode=0o700)
        (info / 'METADATA').write_text(f'Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n')
    metadata_probe = [str(python), '-I', '-c',
                      'import json,sys; from importlib.metadata import distributions; '
                      'd=list(distributions(path=[sys.argv[1]])); '
                      'p={x.metadata["Name"].lower().replace("_","-"):x.version for x in d}; '
                      'assert len(p)==len(d); print(json.dumps(p,sort_keys=True))', str(packages)]
    if json.loads(run(metadata_probe, env, 10, target)) != pins:
        raise RuntimeError('final metadata inventory mismatch')
    disk_size(target)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_used = usage.ru_utime + usage.ru_stime + children.ru_utime + children.ru_stime - cpu_start
    evidence = {'fixturekind': 'synthetic-cpu-worker-test-v1', 'state': 'complete',
                'runtime_version': facts[1], 'runtime': str(runtime), 'lock_sha256': LOCK_HASH,
                'requirements_sha256': req_hash,
                'wheels': {n: {'version': v, 'filename': f, 'sha256': h, 'size': s}
                           for n, (v, f, h, s) in WHEELS.items()},
                'actual_installed': actual, 'synthetic_metadata_only': synthetic,
                'commands': [{'argv': tools_cmd, 'exit': 0},
                             {'argv': runtime_cmd, 'exit': 0}, {'argv': install, 'exit': 0},
                             {'argv': probe_cmd, 'exit': 0},
                             {'argv': metadata_probe, 'exit': 0}],
                'network_bytes': 'UNMEASURED', 'sampled_peak_disk_bytes': PEAK_DISK,
                'elapsed_seconds': time.monotonic() - started, 'observed_cpu_seconds': cpu_used,
                'accounting_limits': 'per-process rlimits; sampled disk, not filesystem quota'}
    data = json.dumps(evidence, indent=2, sort_keys=True) + '\n'
    if len(data.encode()) > 32768:
        raise RuntimeError('evidence limit exceeded')
    receipt.write_text(data)
    print('SYNTHETIC METADATA: six actual packages, 22 metadata-only records; '
          'no real neural ML environment.')
    print(f'export SLAIF_CPU_WORKER_TEST_ROOT={shlex.quote(str(runtime))}')
    print(f'export SLAIF_CPU_WORKER_TEST_PACKAGES={shlex.quote(str(packages))}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError, TimeoutError):
        print('CPU worker synthetic setup failed; inspect prerequisites and partial receipt.',
              file=sys.stderr)
        sys.exit(1)
