"""Provision only a new private Linux x86-64 CPython 3.12 PDF test backend."""
import argparse
from pathlib import Path
import platform
import shlex
import subprocess
import sys


def run(argv, timeout):
    return subprocess.run(argv, check=True, text=True, timeout=timeout, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path, required=True,
                        help='trusted standalone CPython 3.12 runtime root')
    parser.add_argument('--target', type=Path, required=True,
                        help='new private directory; must not already exist')
    args = parser.parse_args()
    if sys.platform != 'linux' or platform.machine() != 'x86_64':
        parser.error('requires Linux x86-64 and compatible manylinux wheels')
    runtime = args.runtime_dir.resolve(strict=True)
    python = runtime / 'bin/python3.12'
    version = run([str(python), '-c',
                   'import sys; print(".".join(map(str,sys.version_info[:3]))); '
                   'print(sys.base_prefix)'], 2).splitlines()
    if not version[0].startswith('3.12.') or Path(version[1]).resolve() != runtime:
        parser.error('runtime-dir must be the standalone CPython 3.12 base runtime')
    target = args.target.absolute()
    target.mkdir(mode=0o700)  # Fail if anything already exists; never reuse an environment.
    requirements = Path(__file__).with_name('pdf-test-requirements.txt').resolve()
    run(['uv', 'venv', '--python', str(python), str(target)], 60)
    run(['uv', 'pip', 'install', '--python', str(target / 'bin/python'), '--only-binary', ':all:',
         '--require-hashes', '-r', str(requirements)], 120)
    inventory = run([str(target / 'bin/python'), '-c',
                     'from importlib.metadata import version; '
                     'names=("pdfminer.six","charset-normalizer","cryptography","cffi",'
                     '"pycparser"); '
                     'print("\\n".join(f"{n}=={version(n)}" for n in names))'], 2)
    expected = [line.split(' --hash=')[0] for line in requirements.read_text().splitlines()]
    if inventory.splitlines() != expected:
        raise RuntimeError('installed distribution inventory differs from pinned requirements')
    packages = target / 'lib/python3.12/site-packages'
    print(f'Worker CPython {version[0]} (runtime {runtime})')
    print('Installed versions and installer-verified wheel SHA-256:')
    print(requirements.read_text(), end='')
    print(f'export PDF_TEST_RUNTIME={shlex.quote(str(runtime))}')
    print(f'export PDF_TEST_PACKAGES={shlex.quote(str(packages))}')
    print('Development tests only: MIT-0/native/notice questions remain release and '
          'distribution blockers; no license exception or application graph clearance.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        print(f'PDF development backend setup failed: {exc}', file=sys.stderr)
        sys.exit(1)
