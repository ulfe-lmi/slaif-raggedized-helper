# Synthetic CPU worker test capsule

The setup helper creates a new private directory for the trusted-fake neural worker tests. It
installs six real distributions: the pinned Pydantic graph (five packages) and the pinned native
`tokenizers` engine required by the existing sandbox setup. It adds data-only metadata for the
other 22 locked distributions. These records satisfy profile selection only: they do not install,
attest, import, or license the associated code. This is not an actual 28-package CPU ML
installation, model execution, hardware qualification, or license clearance. The separate full
CPU profile qualification remains separate evidence.

Prerequisites are Linux x86-64, a trusted standalone CPython 3.12 base runtime, `uv` on PATH,
`/usr/bin/bwrap`, `/usr/bin/prlimit`, `/usr/bin/timeout`, and network access to public PyPI for
six hash-pinned wheels. Use a new target under a private, sufficiently provisioned filesystem;
the helper refuses existing paths including symlinks. It clears ambient installer/Python settings,
uses binary-only `--no-deps` installation without cache, and verifies the lock, wheel pins, actual
inventory, Pydantic validation, and an owned-generated WordLevel tokenizer smoke. The `tokenizers`
wheel declares `huggingface-hub`; it is intentionally not installed and hub functionality is not
part of this fixture. The helper leaves a partial receipt on failure and never purges a target.

```sh
python3 tests/support/prepare_cpu_worker_test_backend.py \
  --runtime-dir /path/to/trusted/cpython-3.12 \
  --target /path/to/new/private/cpu-worker-fixture
```

The command prints shell-quoted exports for interactive use. CI should use independently chosen,
known paths rather than sourcing or evaluating output, for example:

```sh
printf '%s\n' 'SLAIF_CPU_WORKER_TEST_ROOT=/known/cpython-3.12' >> "$GITHUB_ENV"
printf '%s\n' 'SLAIF_CPU_WORKER_TEST_PACKAGES=/known/new-fixture/packages' >> "$GITHUB_ENV"
```

`setup-evidence.json` is outside `packages`, and lists the six actual distributions, their wheel
hashes and 22 metadata-only records. The setup does not install Torch, Transformers, NumPy, model
weights, or corpus data. Existing worker integration tests use a trusted fake provider; they do not
prove real CPU model behavior, GPU capacity, security, parity, MVP completeness, or release readiness.
Network bytes are unmeasured unless separately recorded. Neither synthetic metadata nor a passing
test is an installed-file attestation or license audit.

Resource limits for address space and CPU apply per process, not to the process tree as an
aggregate. Disk accounting samples the owned directory and is not a filesystem quota. The receipt
records observed elapsed time, self plus reaped-children CPU time, and sampled peak disk bytes;
these observations describe the run and are not strict aggregate enforcement guarantees.
