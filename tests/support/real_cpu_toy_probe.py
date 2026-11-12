"""Permit-gated, local-only random CPU toy probe (phase-one implementation)."""
import argparse
import email.parser
import hashlib
import json
import math
import os
import re
import resource
from pathlib import Path
import selectors
import signal
import stat
import struct
import subprocess
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path('/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu')
PACKAGES = Path('/tmp/raggedized-cpu-profile-root-repro-860o22xx/venv/lib/python3.12/site-packages')
LOCK = 'e0a2b1be5601e141b1dca46cd054c77850344d5123424ed05f176a9621a41299'
LIMITS = {'wall_seconds': 600, 'observed_cpu_seconds': 120, 'child_as_bytes': 4 * 1024**3,
          'child_cpu_seconds': 30, 'child_wall_seconds': 120, 'message_bytes': 65536,
          'output_bytes': 262144, 'output_disk_bytes': 256 * 1024**2,
          'generation_fsize_bytes': 128 * 1024**2, 'memory_available_bytes': 8 * 1024**3,
          'worker_cpu_seconds': 20, 'worker_startup_seconds': 45,
          'worker_forward_seconds': 10, 'worker_lifetime_seconds': 90,
          'worker_max_rows': 2, 'worker_calls': 2}
SOURCES = ('tests/support/real_cpu_toy_probe.py', 'tests/support/real_cpu_toy_worker.py',
           'worker_profiles/cpu/uv.lock',
           'src/slaif_raggedized_helper/__init__.py',
           'src/slaif_raggedized_helper/cpu_embedding_worker.py',
           'src/slaif_raggedized_helper/cpu_embedding_worker_main.py',
           'src/slaif_raggedized_helper/cpu_embedding_backend.py',
           'src/slaif_raggedized_helper/embedding_artifacts.py',
           'src/slaif_raggedized_helper/embedding_space.py',
           'src/slaif_raggedized_helper/embedding_vectors.py',
           'src/slaif_raggedized_helper/embedding_tokenizer.py',
           'src/slaif_raggedized_helper/embedding_tokenizer_worker.py',
           'src/slaif_raggedized_helper/native_tokenizers.py',
           'src/slaif_raggedized_helper/tokenizer_session.py',
           'src/slaif_raggedized_helper/tokenizer_session_worker.py',
           'src/slaif_raggedized_helper/schema.py',
           'src/slaif_raggedized_helper/_constraints.py')
UNREAPED = []
PENDING_GROUPS = []
PENDING_OWNERS = []


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def read_regular(path, limit, private=False):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError('invalid file')
        if private and (info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1):
            raise ValueError('permit must be private and owned')
        data = b''
        while len(data) <= limit:
            chunk = os.read(fd, limit + 1 - len(data))
            if not chunk:
                after = os.fstat(fd)
                def signature(st):
                    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid,
                            st.st_size, st.st_mtime_ns, st.st_ctime_ns)

                if signature(info) != signature(after):
                    raise ValueError('file changed during read')
                return data
            data += chunk
        raise ValueError('file too large')
    finally:
        os.close(fd)


def source_hashes():
    return {name: hashlib.sha256(read_regular(ROOT / name, 1024 * 1024)).hexdigest()
            for name in SOURCES}


def head():
    return subprocess.check_output(['/usr/bin/git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                                   text=True, timeout=5).strip()


def permit_check(path, runtime, packages):
    raw = read_regular(path, 16384, private=True)
    permit = json.loads(raw, object_pairs_hook=unique,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('constant')))
    expected = {'schema': 1, 'purpose': 'random-cpu-toy-only', 'head': head(),
                'sources': source_hashes(), 'runtime': str(RUNTIME), 'packages': str(PACKAGES),
                'lock_sha256': LOCK, 'framework_pins': PINS, 'limits': LIMITS}
    def encoded(obj):
        return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)

    if runtime != RUNTIME or packages != PACKAGES or encoded(permit) != encoded(expected):
        raise ValueError('permit mismatch')
    if expected['sources']['worker_profiles/cpu/uv.lock'] != LOCK:
        raise ValueError('lock mismatch')
    return permit




PINS = {'torch': '2.10.0+cpu', 'transformers': '4.51.3', 'tokenizers': '0.21.4',
        'safetensors': '0.5.3', 'huggingface-hub': '0.30.2', 'numpy': '2.2.6'}


def verify_profile(packages):
    """Verify metadata inventory; this alone does not attest installed module bytes."""
    raw = read_regular(ROOT / 'worker_profiles/cpu/uv.lock', 65536)
    if hashlib.sha256(raw).hexdigest() != LOCK:
        raise ValueError('lock mismatch')
    entries = tomllib.loads(raw.decode('utf-8'))['package']
    pins = {item['name']: item['version'] for item in entries if 'registry' in item['source']}
    if len(pins) != 28 or any(pins.get(name) != version for name, version in PINS.items()):
        raise ValueError('lock pin mismatch')
    found = {}
    with os.scandir(packages) as children:
        for index, entry in enumerate(children):
            if index >= 4096:
                raise ValueError('profile entry limit')
            lower = entry.name.lower()
            if lower.endswith('.egg-info'):
                raise ValueError('unexpected profile metadata')
            if not lower.endswith('.dist-info'):
                continue
            if not stat.S_ISDIR(entry.stat(follow_symlinks=False).st_mode):
                raise ValueError('invalid metadata directory')
            metadata = email.parser.BytesParser().parsebytes(
                read_regular(Path(entry.path) / 'METADATA', 262144), headersonly=True)
            names, versions = metadata.get_all('Name', []), metadata.get_all('Version', [])
            if len(names) != 1 or len(versions) != 1:
                raise ValueError('invalid metadata')
            name = re.sub(r'[-_.]+', '-', names[0].lower())
            if name not in pins or name in found:
                raise ValueError('unexpected profile metadata')
            found[name] = versions[0]
    if found != pins:
        raise ValueError('profile pin mismatch')
    canonical = json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(canonical).hexdigest()

def create_target(path):
    """Create one fresh private directory without following any path component."""
    if not path.is_absolute() or os.path.normpath(str(path)) != str(path) or path == Path('/'):
        raise ValueError('invalid target')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in path.parts[1:-1]:
            nxt = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        os.mkdir(path.name, 0o700, dir_fd=fd)
        owned = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            info = os.fstat(owned)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
                raise ValueError('invalid target mode')
        finally:
            os.close(owned)
    finally:
        os.close(fd)


def memory_available():
    data = read_regular('/proc/meminfo', 65536).decode('ascii')
    values = [line.split() for line in data.splitlines() if line.startswith('MemAvailable:')]
    if len(values) != 1 or len(values[0]) != 3 or values[0][2] != 'kB':
        raise ValueError('memory availability unavailable')
    value = int(values[0][1]) * 1024
    if value < LIMITS['memory_available_bytes']:
        raise ValueError('insufficient available memory')
    return value


def validate_reference(value):
    if type(value) is not dict or value.get('kind') != 'synthetic-random-toy':
        raise ValueError('bad generation result')
    if value.get('input_ids') != [[0, 4, 5, 2], [0, 5, 2]]:
        raise ValueError('bad input IDs')
    threads = value.get('generation_threads')
    if (threads != {'intra_op': 1, 'inter_op': 1} or
            any(type(count) is not int for count in threads.values())):
        raise ValueError('generation thread mismatch')
    if value.get('package_versions') != PINS:
        raise ValueError('framework pin mismatch')
    origins = value.get('package_origins')
    if (type(origins) is not dict or set(origins) != set(PINS) or
            any(type(path) is not str or not path.startswith('/packages/')
                for path in origins.values())):
        raise ValueError('framework origin mismatch')
    if (value.get('runtime_executable') != '/runtime/bin/python3.12' or
            value.get('runtime_prefix') != '/runtime'):
        raise ValueError('runtime origin mismatch')
    rows = value.get('reference')
    if (type(rows) is not list or len(rows) != 2 or
            any(type(row) is not list or len(row) != 1024 or
                any(type(x) is not float or not math.isfinite(x) for x in row) for row in rows)):
        raise ValueError('bad reference rows')
    inventories = value.get('inventories')
    if type(inventories) is not dict or set(inventories) != {'safetensors', 'pytorch-state-dict'}:
        raise ValueError('bad inventories')
    revision = hashlib.sha256(b'slaif-random-toy-seed-20261112-v1').hexdigest()[:40]
    if value.get('synthetic_revision') != revision:
        raise ValueError('bad synthetic revision')
    for fmt, inventory in inventories.items():
        if (type(inventory) is not dict or inventory.get('schema') != 2 or
                type(inventory.get('schema')) is not int or
                inventory.get('checkpoint_format') != fmt or
                inventory.get('model_revision') != revision or
                inventory.get('model_name') != 'BAAI/bge-m3'):
            raise ValueError('bad inventory identity')
    return rows




def compare_rows(reference, actual, tolerance=1e-5):
    """Check both ordered raw batches as binary32 and return the maximum error."""
    if (type(reference) not in (tuple, list) or type(actual) not in (tuple, list) or
            len(reference) != 2 or len(actual) != 2):
        raise ValueError('invalid batch')
    errors = []
    for expected, row in zip(reference, actual, strict=True):
        if len(expected) != 1024 or len(row) != 1024:
            raise ValueError('invalid dimensions')
        for a, b in zip(expected, row, strict=True):
            if (type(a) is not float or type(b) is not float or
                    not math.isfinite(a) or not math.isfinite(b) or
                    struct.unpack('<f', struct.pack('<f', b))[0] != b):
                raise ValueError('invalid FP32 result')
            errors.append(abs(a - b))
    maximum = max(errors)
    if maximum > tolerance:
        raise ValueError('reference mismatch')
    return maximum


def validate_normalized(payload):
    if type(payload) is not bytes or len(payload) != 2 * 1024 * 4:
        raise ValueError('invalid normalized payload')
    values = struct.unpack('<2048f', payload)
    norms = []
    for offset in (0, 1024):
        row = values[offset:offset + 1024]
        if not all(math.isfinite(x) for x in row):
            raise ValueError('invalid normalized payload')
        norm = math.sqrt(math.fsum(x * x for x in row))
        if abs(norm - 1.0) > 1e-4:
            raise ValueError('invalid normalized norm')
        norms.append(norm)
    return norms




def token_owner_class(base):
    """Keep the real child and temporary owner reachable until the child is reaped."""
    class OwnedTokenSession(base):
        def close(self):
            child = getattr(self, '_child', None)
            if child is not None and child.poll() is None:
                first = None
                try:
                    child.terminate()
                except ProcessLookupError:
                    pass
                except BaseException as exc:
                    first = exc
                try:
                    child.wait(timeout=0.4)
                except BaseException as exc:
                    if first is None and not isinstance(exc, subprocess.TimeoutExpired):
                        first = exc
                if child.poll() is None:
                    try:
                        child.kill()
                    except ProcessLookupError:
                        pass
                    except BaseException as exc:
                        if first is None:
                            first = exc
                    for _ in range(2):
                        try:
                            child.wait(timeout=0.5)
                            break
                        except BaseException as exc:
                            if first is None and not isinstance(exc, subprocess.TimeoutExpired):
                                first = exc
                if child.poll() is None:
                    raise RuntimeError('token child remains owned') from first
                if first is not None:
                    raise first
            return super().close()
    return OwnedTokenSession



def ensure_no_pending():
    if PENDING_OWNERS or UNREAPED or PENDING_GROUPS:
        raise RuntimeError('pending owned process')

class OwnedSession:
    """Register the exact instance before constructor entry and retain uncertain owners."""
    def __init__(self, factory, *args):
        ensure_no_pending()
        self.factory, self.args = factory, args
        self.owner = factory.__new__(factory)
        PENDING_OWNERS.append(self)

    def __enter__(self):
        try:
            self.factory.__init__(self.owner, *self.args)
            return self.owner
        except BaseException as original:
            try:
                self.close()
            except BaseException:
                original.add_note('session cleanup pending or refused')
            raise

    def close(self):
        error = None
        for _ in range(2):
            try:
                self.owner.close()
                break
            except BaseException as exc:
                if (error is None or
                        (not isinstance(exc, Exception) and isinstance(error, Exception))):
                    error = exc
        child = getattr(self.owner, '_child', None)
        pending = child is not None and child.poll() is None
        temporary = getattr(self.owner, '_tmp', None)
        if not pending and temporary is None:
            if self in PENDING_OWNERS:
                PENDING_OWNERS.remove(self)
        if pending or temporary is not None:
            raise RuntimeError('session ownership remains pending') from error
        if error is not None:
            raise error

    def __exit__(self, _type, original, _traceback):
        try:
            self.close()
        except BaseException:
            if original is None:
                raise
            original.add_note('session cleanup pending or refused')
        return False

def verify_token_ids(target, fmt, manifest, budget):
    sys.path.insert(0, str(ROOT / 'src'))
    from slaif_raggedized_helper import embedding_artifacts, embedding_tokenizer, native_tokenizers

    root = target / fmt
    raw = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    budget.reserve(cpu=30, wall=20, target=target)
    inv = embedding_artifacts.verify_artifacts(raw, root)
    token = next(item for item in inv.files if item.role == 'tokenizer')
    definition = native_tokenizers.Definition(root / 'tokenizer.json', token.sha256, '0.21.4',
                                               'bge_representation', inv.model_revision, 'identity')
    runtime = native_tokenizers.Runtime(RUNTIME, PACKAGES, 'python3.12')
    remaining = LIMITS['output_bytes'] - budget.output
    if remaining < 1024:
        raise ValueError('insufficient output budget')
    policy = embedding_tokenizer.Policy(max_calls=2, max_output_bytes=min(remaining, 32768),
                                        max_response_bytes=4096, lifetime_seconds=20)
    expected = [('hello world', (0, 4, 5, 2)), ('world', (0, 5, 2))]
    receipts = []
    with OwnedSession(token_owner_class(embedding_tokenizer.TokenIDSession),
                      definition, runtime, policy) as session:
        child = session._child
        observed = session._output
        budget.charge_size(observed)
        for text, ids in expected:
            budget.check(target)
            try:
                receipt = session.encode(text)
            finally:
                original = sys.exception()
                try:
                    budget.charge_size(session._output - observed)
                except Exception:
                    if original is None:
                        raise
                    original.add_note('token output accounting failed')
                observed = session._output
            digest = hashlib.sha256(json.dumps([text, None], ensure_ascii=True,
                                                separators=(',', ':')).encode()).hexdigest()
            if (receipt.ids != ids or receipt.count != len(ids) or
                    receipt.artifact_sha256 != token.sha256 or receipt.input_sha256 != digest or
                    receipt.backend_version != '0.21.4' or receipt.role != 'bge_representation' or
                    receipt.model_revision != inv.model_revision or
                    receipt.preprocessing != 'identity' or
                    re.fullmatch('[0-9a-f]{32}', receipt.nonce) is None or
                    receipt.serialization !=
                    'utf8-json-v1;no-truncation;no-padding;special-tokens'):
                raise ValueError('token receipt mismatch')
            receipts.append({'ids': list(receipt.ids), 'artifact_sha256': receipt.artifact_sha256,
                             'input_sha256': receipt.input_sha256, 'nonce': receipt.nonce,
                             'revision': receipt.model_revision})
            budget.check(target)
        if session._child is not child or session._calls != 2:
            raise ValueError('token session reuse mismatch')
    return receipts

def verify_worker_format(target, fmt, manifest, reference, budget, expected_profile):
    """Use the real local-only worker for two ordered forwards of one resident model."""
    sys.path.insert(0, str(ROOT / 'src'))
    from slaif_raggedized_helper import (cpu_embedding_worker, embedding_artifacts,
                                         embedding_vectors, native_tokenizers)
    from slaif_raggedized_helper.schema import EmbeddingDefinition

    if fmt not in ('safetensors', 'pytorch-state-dict'):
        raise ValueError('invalid format')
    root = target / fmt
    raw = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    budget.check(target)
    inv = embedding_artifacts.verify_artifacts(raw, root)
    if inv.schema != 2 or inv.checkpoint_format != fmt:
        raise ValueError('inventory mismatch')
    files = {item.role: item for item in inv.files}
    definition = EmbeddingDefinition(model_name='BAAI/bge-m3',
                                     checkpoint_revision=inv.model_revision,
                                     checkpoint_sha256=files['weights'].sha256,
                                     tokenizer_revision=inv.model_revision, pooling='cls',
                                     dimensions=1024)
    tokenizer = native_tokenizers.Definition(root / 'tokenizer.json', files['tokenizer'].sha256,
                                             '0.21.4', 'bge_representation', inv.model_revision,
                                             'identity')
    runtime = native_tokenizers.Runtime(RUNTIME, PACKAGES, 'python3.12')
    remaining = LIMITS['output_bytes'] - budget.output
    if remaining < 1024:
        raise ValueError('insufficient output budget')
    policy = cpu_embedding_worker.Policy(max_rows=2, request_bytes=65536,
                                          response_bytes=min(65536, remaining),
                                          startup_seconds=45, forward_seconds=10,
                                          lifetime_seconds=90, cpu_seconds=20,
                                          address_bytes=4 * 1024**3, calls=2,
                                          total_input_bytes=131072, total_output_bytes=remaining)
    ids = [[0, 4, 5, 2], [0, 5, 2]]
    errors, outputs = [], []
    budget.reserve(cpu=20, wall=90, target=target)
    memory_available()
    with OwnedSession(cpu_embedding_worker.CPUEmbeddingWorker, raw, root, definition, tokenizer,
                      inv.inventory_id, runtime, policy) as worker:
        child = worker._child
        observed_output = worker._output
        budget.charge_size(observed_output)
        if worker.profile != expected_profile or worker.space.inventory_id != inv.inventory_id:
            raise ValueError('worker identity mismatch')
        identity = {'inventory_id': inv.inventory_id, 'space_id': worker.space.space_id,
                    'profile': worker.profile, 'policy_id': worker.policy_fingerprint,
                    'code_id': worker.code_fingerprint}
        for _ in range(2):
            budget.check(target)
            try:
                rows = worker.forward_cls(ids)
            finally:
                original = sys.exception()
                try:
                    budget.charge_size(worker._output - observed_output)
                except Exception:
                    if original is None:
                        raise
                    original.add_note('worker output accounting failed')
                observed_output = worker._output
            errors.append(compare_rows(reference, rows))
            normalized = embedding_vectors.normalize_rows(rows)
            norms = validate_normalized(normalized.payload)
            if hashlib.sha256(normalized.payload).hexdigest() != normalized.sha256:
                raise ValueError('normalized receipt mismatch')
            outputs.append({'sha256': normalized.sha256, 'norms': norms,
                            'policy_id': normalized.policy_id})
            budget.check(target)
        if worker._child is not child or worker._calls != 2:
            raise ValueError('worker reuse mismatch')
    if outputs[0] != outputs[1]:
        raise ValueError('resident output changed')
    return {'identity': identity, 'max_abs_error': max(errors), 'forwards': 2,
            'normalized': outputs[0]}


def validate_format_identities(results, profile):
    """Require separate spaces and the verified shared runtime profile."""
    if type(results) is not dict or set(results) != {'safetensors', 'pytorch-state-dict'}:
        raise ValueError('format results missing')
    first = results['safetensors']
    second = results['pytorch-state-dict']
    for item in (first, second):
        if (type(item) is not dict or item.get('forwards') != 2 or
                type(item.get('forwards')) is not int or
                type(item.get('identity')) is not dict or
                item['identity'].get('profile') != profile):
            raise ValueError('worker result identity mismatch')
        for field in ('inventory_id', 'space_id', 'profile', 'policy_id', 'code_id'):
            digest = item['identity'].get(field)
            if type(digest) is not str or re.fullmatch('[0-9a-f]{64}', digest) is None:
                raise ValueError('worker result identity malformed')
    if (first['identity']['inventory_id'] == second['identity']['inventory_id'] or
            first['identity']['space_id'] == second['identity']['space_id']):
        raise ValueError('format identities must be distinct')


def install_parent_limits():
    """Apply per-process ceilings; the observed tree budget is tracked separately."""
    def cap(resource_id, ceiling):
        soft, hard = resource.getrlimit(resource_id)
        bounded_hard = ceiling if hard == resource.RLIM_INFINITY else min(hard, ceiling)
        bounded_soft = bounded_hard if soft == resource.RLIM_INFINITY else min(soft, bounded_hard)
        resource.setrlimit(resource_id, (bounded_soft, bounded_hard))

    def expired(_signal, _frame):
        raise TimeoutError('overall wall limit')

    cap(resource.RLIMIT_CPU, LIMITS['observed_cpu_seconds'])
    cap(resource.RLIMIT_FSIZE, LIMITS['generation_fsize_bytes'])
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(LIMITS['wall_seconds'])

class Budget:
    """Wall and observed CPU bounds; disk is sampled and not a filesystem quota."""
    def __init__(self, started=None):
        self.started = time.monotonic() if started is None else started
        self.cpu_start = self.cpu()
        self.peak_disk = 0
        self.output = 0

    @staticmethod
    def cpu():
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime

    def check(self, target=None):
        if time.monotonic() - self.started >= LIMITS['wall_seconds']:
            raise TimeoutError('overall wall limit')
        used = self.cpu() - self.cpu_start
        if used >= LIMITS['observed_cpu_seconds']:
            raise TimeoutError('observed CPU limit')
        if target is not None:
            total = 0
            for parent, dirs, files in os.walk(target, followlinks=False):
                for name in dirs + files:
                    info = os.lstat(Path(parent) / name)
                    if stat.S_ISLNK(info.st_mode):
                        raise ValueError('unexpected output symlink')
                    if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                        raise ValueError('unexpected output type')
                    total += info.st_size
                    if total > LIMITS['output_disk_bytes']:
                        raise ValueError('output disk limit')
            self.peak_disk = max(self.peak_disk, total)
        return used

    def reserve(self, cpu, wall, target=None):
        used = self.check(target)
        if used + cpu >= LIMITS['observed_cpu_seconds']:
            raise TimeoutError('insufficient observed CPU budget')
        if time.monotonic() - self.started + wall >= LIMITS['wall_seconds']:
            raise TimeoutError('insufficient wall budget')

    def charge_size(self, size):
        if type(size) is not int or size < 0:
            raise ValueError('invalid output accounting')
        self.output += size
        if self.output > LIMITS['output_bytes']:
            raise ValueError('aggregate output limit')

    def charge_output(self, data):
        self.charge_size(len(data))

def generation_argv(target):
    """Fixed isolated child operation; no caller-supplied command or code."""
    if not target.is_absolute() or os.path.normpath(str(target)) != str(target):
        raise ValueError('invalid target')
    child = ROOT / 'tests/support/real_cpu_toy_worker.py'
    return [
        '/usr/bin/timeout', '--signal=KILL', '120s',
        '/usr/bin/prlimit', '--as=4294967296', '--cpu=30', '--nofile=64',
        '--fsize=134217728', '/usr/bin/bwrap', '--unshare-user', '--unshare-pid',
        '--unshare-net', '--unshare-ipc', '--unshare-uts', '--die-with-parent',
        '--new-session', '--clearenv', '--setenv', 'HOME', '/tmp', '--setenv',
        'TMPDIR', '/tmp', '--setenv', 'USER', 'raggedized-toy', '--setenv',
        'LOGNAME', 'raggedized-toy', '--setenv', 'LANG', 'C.UTF-8', '--setenv',
        'OMP_NUM_THREADS', '1', '--setenv', 'OPENBLAS_NUM_THREADS', '1', '--setenv',
        'MKL_NUM_THREADS', '1', '--setenv', 'RAYON_NUM_THREADS', '1', '--setenv',
        'TOKENIZERS_PARALLELISM', 'false', '--setenv', 'HF_HUB_OFFLINE', '1',
        '--setenv', 'TRANSFORMERS_OFFLINE', '1', '--setenv', 'HF_HUB_DISABLE_TELEMETRY',
        '1', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1',
        '--ro-bind', str(RUNTIME), '/runtime', '--ro-bind', str(PACKAGES), '/packages',
        '--ro-bind', str(child), '/worker.py', '--bind', str(target), '/output',
        '--ro-bind', '/usr/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu',
        '--ro-bind', '/usr/lib64', '/usr/lib64', '--symlink', 'usr/lib', '/lib',
        '--symlink', 'usr/lib64', '/lib64', '--proc', '/proc', '--dev', '/dev',
        '--tmpfs', '/tmp', '--chdir', '/tmp', '/runtime/bin/python3.12', '-I', '-S',
        '/worker.py', '/output',
    ]


def generation_stage(permit, target, runtime, packages, budget):
    """Execute one fixed operation only after validating its procedural permit.

    Root source review and an explicit scoped permit precede any invocation.
    """
    ensure_no_pending()
    permit_check(permit, runtime, packages)
    profile_id = verify_profile(packages)
    budget.reserve(cpu=30, wall=120)
    available = memory_available()
    create_target(target)
    budget.check(target)
    wire = run_bounded(generation_argv(target), {}, 120, budget=budget, target=target)
    if not wire.endswith(b'\n') or wire.count(b'\n') != 1:
        raise ValueError('invalid generation message')
    result = json.loads(wire[:-1], object_pairs_hook=unique,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('constant')))
    validate_reference(result)
    budget.check(target)
    return result, {'profile_id': profile_id, 'memory_available_bytes': available,
                    'output_bytes': len(wire)}

def cleanup(child):
    """Attempt group kill even after an interrupt; retain the child if unreaped."""
    error = None

    def record(exc):
        nonlocal error
        if error is None or (isinstance(exc, (KeyboardInterrupt, SystemExit))
                             and isinstance(error, Exception)):
            error = exc

    group_killed = False
    for _ in range(2):
        try:
            os.killpg(child.pid, signal.SIGKILL)
            group_killed = True
            break
        except ProcessLookupError:
            group_killed = True
            break
        except BaseException as exc:
            record(exc)
    if not group_killed:
        PENDING_GROUPS.append(child.pid)
    for _ in range(2):
        try:
            child.stdout.close()
            break
        except BaseException as exc:
            record(exc)
    reaped = False
    for _ in range(2):
        try:
            child.wait(timeout=1)
            reaped = True
            break
        except BaseException as exc:
            record(exc)
    if not reaped:
        UNREAPED.append(child)
    return error


def run_bounded(argv, env, timeout, cap=65536, budget=None, target=None):
    ensure_no_pending()
    if budget is not None:
        budget.check(target)
    child = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=True)
    deadline = time.monotonic() + timeout
    output = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            while selector.get_map():
                if budget is not None:
                    budget.check(target)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('child deadline')
                for key, _ in selector.select(min(remaining, .1)):
                    chunk = os.read(key.fd, cap + 1 - len(output))
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        output.extend(chunk)
                        if budget is not None:
                            budget.charge_output(chunk)
                        if len(output) > cap:
                            raise ValueError('child output limit')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('child deadline')
        if child.wait(timeout=remaining):
            raise ValueError('child failed')
        if time.monotonic() >= deadline:
            raise TimeoutError('child deadline')
        if budget is not None:
            budget.check(target)
        return bytes(output)
    finally:
        original = sys.exception()
        error = cleanup(child)
        if error:
            if original:
                original.add_note('child cleanup failed; pending ownership retained')
            else:
                raise error


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--permit', type=Path)
    parser.add_argument('--target', type=Path)
    parser.add_argument('--runtime-dir', type=Path)
    parser.add_argument('--packages', type=Path)
    args = parser.parse_args()
    if args.plan:
        if any((args.permit, args.target, args.runtime_dir, args.packages)):
            parser.error('--plan takes no other options')
        print(json.dumps({'purpose': 'random-cpu-toy-only', 'limits': LIMITS,
                          'runtime': str(RUNTIME), 'packages': str(PACKAGES)}, sort_keys=True))
        return
    if not all((args.permit, args.target, args.runtime_dir, args.packages)):
        parser.error('permit, target, runtime and packages required')
    permit_check(args.permit, args.runtime_dir, args.packages)
    install_parent_limits()
    budget = Budget(started)
    result, generation = generation_stage(args.permit, args.target, args.runtime_dir,
                                          args.packages, budget)
    reference = validate_reference(result)
    formats = {}
    receipts = {}
    for fmt in ('safetensors', 'pytorch-state-dict'):
        manifest = result['inventories'][fmt]
        receipts[fmt] = verify_token_ids(args.target, fmt, manifest, budget)
        formats[fmt] = verify_worker_format(args.target, fmt, manifest, reference, budget,
                                            generation['profile_id'])
    validate_format_identities(formats, generation['profile_id'])
    budget.check(args.target)
    evidence = {'kind': result['kind'], 'synthetic_revision': result['synthetic_revision'],
                'input_ids': result['input_ids'], 'inventories': result['inventories'],
                'package_versions': result['package_versions'],
                'package_origins': result['package_origins'], 'python': result['python'],
                'generation_threads': result['generation_threads'],
                'worker_inter_op_threads': 'UNKNOWN',
                'runtime_executable': result['runtime_executable'],
                'runtime_prefix': result['runtime_prefix'], 'generation': generation,
                'receipts': receipts, 'formats': formats, 'elapsed_seconds':
                time.monotonic() - budget.started,
                'observed_cpu_seconds': budget.check(args.target),
                'sampled_peak_disk_before_evidence_bytes': budget.peak_disk,
                'output_bytes_before_evidence': budget.output,
                'rss_bytes': 'UNKNOWN', 'limits': LIMITS,
                'commands': [{'operation': 'fixed-generation', 'argv': generation_argv(args.target),
                              'exit': 0},
                             {'operation': 'TokenIDSession.encode', 'calls': 4},
                             {'operation': 'CPUEmbeddingWorker.forward_cls', 'calls': 4}],
                'accounting': 'self plus reaped children CPU; per-process rlimits; sampled disk'}
    data = json.dumps(evidence, allow_nan=False, sort_keys=True, indent=2).encode() + b'\n'
    if len(data) > 65536:
        raise ValueError('evidence too large')
    budget.charge_size(len(data))
    fd = os.open(args.target / 'evidence.json', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
    budget.check(args.target)
    print(data.decode(), end='')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print('probe refused: ' + str(exc), file=sys.stderr)
        sys.exit(1)
