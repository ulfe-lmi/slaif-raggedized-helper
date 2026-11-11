"""Provision a new private engine-only native tokenizer development capsule."""
import argparse
import os
from pathlib import Path
import platform
import shlex
import selectors
import shutil
import subprocess
import sys
import time


PIN = ('tokenizers==0.21.4 --hash=sha256:'
       '51b7eabb104f46c1c50b486520555715457ae833d5aee9ff6ae853d1130506ff')


OUTPUT_LIMIT = 8192


def run(argv, env, timeout=10, capture=True):
    if not capture:
        subprocess.run(argv, env=env, check=True, timeout=timeout,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ''
    child = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + timeout
    output = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise subprocess.TimeoutExpired(argv, timeout)
                chunk = os.read(child.stdout.fileno(), OUTPUT_LIMIT + 1 - len(output))
                if not chunk:
                    break
                output.extend(chunk)
                if len(output) > OUTPUT_LIMIT:
                    raise RuntimeError('probe output exceeds byte limit')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(argv, timeout)
        if child.wait(timeout=remaining):
            raise RuntimeError('probe exited unsuccessfully')
        return output.decode('utf-8', errors='strict')
    finally:
        child.stdout.close()
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=1)
        else:
            child.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path, required=True,
                        help='trusted standalone CPython 3.12 base runtime')
    parser.add_argument('--target', type=Path, required=True,
                        help='new private directory; must not already exist')
    args = parser.parse_args()
    if sys.platform != 'linux' or platform.machine() != 'x86_64':
        raise RuntimeError('requires Linux x86-64')
    uv = shutil.which('uv')
    if not uv:
        raise RuntimeError('uv executable is required on PATH')
    for tool in ('/usr/bin/bwrap', '/usr/bin/prlimit', '/usr/bin/timeout'):
        if not os.access(tool, os.X_OK):
            raise RuntimeError(f'required tool is missing or not executable: {tool}')
    runtime = args.runtime_dir.resolve(strict=True)
    python = runtime / 'bin/python3.12'
    # No caller configuration, Python paths, index credentials, home or cache are inherited.
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'UV_NO_CONFIG': '1',
           'UV_PYTHON_DOWNLOADS': 'never'}
    facts = run([str(python), '-I', '-S', '-c',
                 'import sys; print(sys.implementation.name); '
                 'print(".".join(map(str, sys.version_info[:3]))); print(sys.base_prefix)'],
                env).splitlines()
    if (len(facts) != 3 or facts[0] != 'cpython' or not facts[1].startswith('3.12.')
            or Path(facts[2]).resolve() != runtime):
        raise RuntimeError('runtime-dir must be the CPython 3.12 base runtime')
    requirements = Path(__file__).with_name('native-test-requirements.txt').resolve(strict=True)
    if requirements.read_text().strip() != PIN:
        raise RuntimeError('requirements do not match the fixed version and wheel hash')
    target = args.target.absolute()
    target.mkdir(mode=0o700)  # Atomic refusal of every existing target, including symlinks.
    target.chmod(0o700)
    packages = target / 'packages'
    packages.mkdir(mode=0o700)
    env['HOME'] = str(target)
    run([str(Path(uv).resolve()), '--no-config', 'pip', 'install', '--target', str(packages),
         '--python', str(python), '--index-url', 'https://pypi.org/simple', '--no-cache',
         '--no-deps', '--only-binary', ':all:', '--require-hashes', '-r', str(requirements)],
        env, timeout=120, capture=False)
    probe = ('import sys; sys.path.insert(0, sys.argv[1]); '
             'from importlib.metadata import distributions; '
             'from tokenizers import Tokenizer, models; '
             'items=sorted((d.metadata["Name"].lower(), d.version) '
             'for d in distributions(path=[sys.argv[1]])); '
             'print(repr(items)); print(Tokenizer(models.WordLevel({"[UNK]": 0}, '
             'unk_token="[UNK]")).encode("x").ids)')
    inventory = run([str(python), '-I', '-c', probe, str(packages)], env).splitlines()
    if inventory != ["[('tokenizers', '0.21.4')]", '[0]']:
        raise RuntimeError('installed engine inventory or API probe differs from the fixed capsule')
    print(f'Worker CPython {facts[1]}; engine tokenizers 0.21.4')
    print(f'Installer verified wheel: {PIN}')
    print(f'export SLAIF_NATIVE_TEST_ROOT={shlex.quote(str(runtime))}')
    print('export SLAIF_NATIVE_TEST_PYTHON=python3.12')
    print(f'export SLAIF_NATIVE_TEST_PACKAGES={shlex.quote(str(packages))}')
    print('Engine-only development capsule; not a complete dependency or license clearance.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.SubprocessError, RuntimeError, UnicodeError) as exc:
        print(f'Native development backend setup failed: {exc}', file=sys.stderr)
        sys.exit(1)
