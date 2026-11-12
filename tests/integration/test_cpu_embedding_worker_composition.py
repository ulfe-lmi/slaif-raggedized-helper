"""Real OS protocol with a test-only fake provider, never real neural loading."""

import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests/unit")]

from slaif_raggedized_helper import cpu_embedding_worker as worker, native_tokenizers  # noqa: E402
from test_cpu_embedding_backend import make_tree  # noqa: E402

PACKAGES = Path(os.environ["SLAIF_CPU_V2_TEST_PACKAGES"])
RUNTIME = Path(os.environ["SLAIF_CPU_V2_TEST_ROOT"])

FAKE = """
import sys
sys.path[:0] = ['/packages', '/app']
from types import SimpleNamespace
from slaif_raggedized_helper import cpu_embedding_backend as b
from slaif_raggedized_helper import cpu_embedding_worker_main as m
class Tensor:
    def __init__(self, data=None, dtype='fp32', shape=None):
        self.data, self.dtype, self.shape = data, dtype, shape
        self.device = SimpleNamespace(type='cpu')
    def is_floating_point(self): return self.dtype == 'fp32'
    def __getitem__(self, key): return Tensor([row[0] for row in self.data])
    def tolist(self): return self.data
class Context:
    def __enter__(self): return self
    def __exit__(self, *args): pass
class Torch:
    __version__ = '2.14.0+cpu'
    float32 = 'fp32'
    long = 'long'
    def tensor(self, data, **kw): return Tensor(data, kw['dtype'])
    def inference_mode(self): return Context()
    def autocast(self, **kw): return Context()
class Model:
    def __init__(self):
        self.training = True
        self.config = SimpleNamespace(vocab_size=20, pad_token_id=1)
    def to(self, **kw): return self
    def eval(self): self.training = False
    def parameters(self): return iter([Tensor()])
    def buffers(self): return iter([])
    def __call__(self, **kw):
        ids = kw['input_ids'].data
        return SimpleNamespace(last_hidden_state=Tensor(
            [[[float(x)] * 1024 for x in row] for row in ids],
            shape=(len(ids), len(ids[0]), 1024)))
class Factory:
    calls = 0
    @classmethod
    def from_pretrained(cls, *args, **kw):
        cls.calls += 1
        assert cls.calls == 1
        assert kw == dict(local_files_only=True, trust_remote_code=False, token=False,
                          weights_only=True, use_safetensors=True,
                          torch_dtype='fp32', device_map=None)
        return Model()
sys.modules['torch'] = Torch()
sys.modules['transformers'] = SimpleNamespace(__version__='5.22.2', XLMRobertaModel=Factory)
sys.exit(m.main())
"""


def test_actual_sandbox_protocol(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    _, raw, inv, definition, tokenizer = make_tree(root)
    script = tmp_path / "fake.py"
    canary = tmp_path / "host-canary"
    canary.write_text("synthetic")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    checks = f"""
import os, socket
assert not os.path.exists({str(canary)!r})
assert not os.path.exists('/home/janezp')
assert not any(os.path.exists(p) for p in ('/dev/nvidia0', '/dev/nvidiactl', '/dev/dri'))
s = socket.socket()
s.settimeout(1)
assert s.connect_ex(('127.0.0.1', {port})) != 0
s.close()
"""
    script.write_text(checks + FAKE)
    original = worker._argv

    def intercept(*args):
        argv = original(*args)
        argv[argv.index("/worker.py") - 1] = str(script)
        return argv

    monkeypatch.setattr(worker, "_argv", intercept)
    policy = worker.Policy(address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=120)
    runtime = native_tokenizers.Runtime(RUNTIME, PACKAGES, "python3.12")
    before = dict(os.environ)
    with worker.CPUEmbeddingWorker(
        raw, root, definition, tokenizer, inv.inventory_id, runtime, policy
    ) as obj:
        assert obj.vocab_size == 20
        assert obj.forward_cls([[3, 4], [5, 6]]) == ((3.0,) * 1024, (5.0,) * 1024)
        assert obj.forward_cls([[7, 8]]) == ((7.0,) * 1024,)
        child = obj._child
    assert child.poll() is not None
    listener.close()
    assert root.exists() and dict(os.environ) == before


def test_idle_lifetime_reaps_child(tmp_path, monkeypatch):
    import time

    root = tmp_path / "tree"
    _, raw, inv, definition, tokenizer = make_tree(root)
    script = tmp_path / "fake.py"
    script.write_text(FAKE)
    original = worker._argv

    def intercept(*args):
        argv = original(*args)
        argv[argv.index("/worker.py") - 1] = str(script)
        return argv

    monkeypatch.setattr(worker, "_argv", intercept)
    policy = worker.Policy(address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=2)
    runtime = native_tokenizers.Runtime(RUNTIME, PACKAGES, "python3.12")
    obj = worker.CPUEmbeddingWorker(
        raw, root, definition, tokenizer, inv.inventory_id, runtime, policy
    )
    child = obj._child
    deadline = time.monotonic() + 4
    while child.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    assert child.poll() is not None
    obj.close()


def test_startup_timeout_reaps_child(tmp_path, monkeypatch):
    import pytest

    root = tmp_path / "tree"
    _, raw, inv, definition, tokenizer = make_tree(root)
    script = tmp_path / "hang.py"
    script.write_text("import time; time.sleep(20)")
    original = worker._argv
    children = []
    popen = worker.subprocess.Popen

    def intercept(*args):
        argv = original(*args)
        argv[argv.index("/worker.py") - 1] = str(script)
        return argv

    def capture(*args, **kwargs):
        child = popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(worker, "_argv", intercept)
    monkeypatch.setattr(worker.subprocess, "Popen", capture)
    policy = worker.Policy(
        address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=5, startup_seconds=1
    )
    runtime = native_tokenizers.Runtime(RUNTIME, PACKAGES, "python3.12")
    with pytest.raises(worker.WorkerRefused):
        worker.CPUEmbeddingWorker(
            raw, root, definition, tokenizer, inv.inventory_id, runtime, policy
        )
    assert len(children) == 1 and children[0].poll() is not None
    assert root.exists()


def test_watchdog_expires_while_owned_parent_paused(tmp_path):
    import select
    import signal
    import subprocess
    import time

    root = tmp_path / "artifacts"
    root.mkdir()
    fake = tmp_path / "sleep.py"
    fake.write_text("import time; print('ready', flush=True); time.sleep(30)")
    script = """
import os,subprocess,sys,time
from pathlib import Path
from slaif_raggedized_helper import cpu_embedding_worker as w,native_tokenizers as n
root,packages,artifacts,lock,fake = sys.argv[1:]
argv=w._argv(n.Runtime(Path(root),Path(packages),'python3.12'),Path(artifacts),Path(lock),
             w.Policy(address_bytes=1024**3,cpu_seconds=30,lifetime_seconds=5))
argv[argv.index('/worker.py')-1]=fake
p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
assert p.stdout.readline() == b'ready\\n'
print(p.pid,flush=True)
p.wait(timeout=10)
"""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    parent = subprocess.Popen(
        [
            "/usr/bin/prlimit",
            "--as=1073741824",
            "--cpu=30",
            sys.executable,
            "-c",
            script,
            str(RUNTIME),
            str(PACKAGES),
            str(root),
            str(ROOT / "worker_profiles/cpu-v2/uv.lock"),
            str(fake),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env=env,
    )
    pid = None
    try:
        fd = parent.stdout.fileno()
        os.set_blocking(fd, False)
        deadline = time.monotonic() + 4
        data = bytearray()
        while b"\n" not in data:
            remaining = deadline - time.monotonic()
            assert remaining > 0 and select.select([fd], [], [], remaining)[0], (
                "synthetic parent did not become ready"
            )
            part = os.read(fd, 32 - len(data))
            assert part and len(data) + len(part) <= 31
            data.extend(part)
        assert data.endswith(b"\n") and data.count(b"\n") == 1
        pid = int(data[:-1])

        def descendants(ancestor):
            seen, queue = set(), [ancestor]
            while queue:
                current = queue.pop()
                try:
                    children = Path(f"/proc/{current}/task/{current}/children").read_text().split()
                except FileNotFoundError:
                    continue
                for value in children:
                    child = int(value)
                    if child not in seen:
                        seen.add(child)
                        queue.append(child)
            return seen

        owned = descendants(pid)
        assert owned, "no sandbox descendants observed"
        worker_pids = []
        for process in owned:
            try:
                command = Path(f"/proc/{process}/cmdline").read_bytes()
                executable = os.readlink(f"/proc/{process}/exe")
            except FileNotFoundError:
                continue
            if b"/worker.py" in command and Path(executable).name.startswith("python3.12"):
                worker_pids.append(process)
        assert worker_pids, "owned sandbox worker was not observed"
        os.kill(parent.pid, signal.SIGSTOP)
        deadline = time.monotonic() + 8
        pending = owned | {pid}
        while pending and time.monotonic() < deadline:
            for process in tuple(pending):
                try:
                    state = Path(f"/proc/{process}/stat").read_text().split()[2]
                except FileNotFoundError:
                    state = "gone"
                if state in ("Z", "gone"):
                    pending.remove(process)
            time.sleep(0.05)
        assert not pending, f"owned sandbox processes remained: {pending}"
    finally:
        if parent.poll() is None:
            os.kill(parent.pid, signal.SIGCONT)
        try:
            parent.wait(timeout=8)
        except subprocess.TimeoutExpired:
            parent.kill()
            parent.wait(timeout=2)
        parent.stdout.close()
