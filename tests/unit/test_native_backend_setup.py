"""Bounded capture tests using real owned child processes."""
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    'native_setup', Path(__file__).parents[1] / 'support/prepare_native_test_backend.py')
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)
ENV = {'PATH': '/usr/bin:/bin'}


def test_exact_limit_and_one_over():
    code = 'import os,sys; os.write(1,b"x"*int(sys.argv[1]))'
    assert setup.run([sys.executable, '-c', code, '8192'], ENV) == 'x' * 8192
    with pytest.raises(RuntimeError, match='byte limit'):
        setup.run([sys.executable, '-c', code, '8193'], ENV)


@pytest.mark.parametrize(('code', 'error'), [
    ('import os,signal; signal.signal(signal.SIGTERM, signal.SIG_IGN); '
     'exec("while True: os.write(1, b\\"x\\"*4096)")', RuntimeError),
    ('import time; time.sleep(10)', subprocess.TimeoutExpired),
    ('import sys; sys.exit(3)', RuntimeError),
    ('import os; os.write(1, bytes([255]))', UnicodeDecodeError),
])
def test_failure_reaps_owned_child(monkeypatch, code, error):
    original = subprocess.Popen
    children = []

    def record(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(setup.subprocess, 'Popen', record)
    start = time.monotonic()
    with pytest.raises(error):
        setup.run([sys.executable, '-c', code], ENV, timeout=0.3)
    assert time.monotonic() - start < 3
    assert len(children) == 1
    assert children[0].poll() is not None
    assert children[0].stdout.closed
    with pytest.raises(ChildProcessError):
        import os
        os.waitpid(children[0].pid, os.WNOHANG)
