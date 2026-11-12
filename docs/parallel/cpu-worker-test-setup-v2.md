# Disposable CPU v2 synthetic fixture

This fixture exercises the accepted CPU-v2 lock's 38 distribution names using six actual lightweight distributions and 32 metadata-only records. The real packages are annotated-types, pydantic, pydantic-core, tokenizers 0.23.1, typing-extensions and typing-inspection. The other distributions have only a `METADATA` file, with no fake importable ML modules. This is not a neural environment, BGE execution, installed-package attestation, or evidence of framework compatibility, security, licenses, ABI, quality, rights or ICA. The separate native tokenizers 0.21.4 capsule and its semantics are unchanged.

On Linux x86-64, with the existing standalone CPython 3.12 root, `uv`, `bwrap`, `prlimit` and `timeout` installed, run from the repository root:

```sh
python3 tests/support/prepare_cpu_worker_test_backend_v2.py \
  --runtime-dir "$TRUSTED_STANDALONE_CPYTHON312_ROOT" \
  --target /tmp/NEW-PRIVATE-FIXTURE-NAME
```

Choose a nonexistent direct child of `/tmp`. The helper prints distinct `SLAIF_CPU_V2_TEST_ROOT` and `SLAIF_CPU_V2_TEST_PACKAGES` values; set them explicitly for tests without sourcing printed output. It rejects existing targets and preserves a partial target and receipt on failure for inspection; choose a new name after diagnosing failure. Never delete a path unless its ownership is established independently.

The fixed lock and requirements are checked before target creation or network access. Installation uses six pinned binary wheels with hashes, no dependencies and a sanitized environment. The helper checks real installed metadata and runs Pydantic validation and an owned tiny WordLevel tokenizers smoke before creating synthetic records. Receipt labels real and synthetic records separately. Downloads are limited to the six wheels whose lock sizes total under 16 MiB; transfer bytes are unknown. Metadata created is bounded to 2 MiB. Resource limits are 1 GiB address space and 30 CPU seconds per process, 120 seconds wall time, 32 MiB per file, single download/install/thread, and sampled target size aborting above 96 MiB with 128 MiB intended headroom. Sampling is not an atomic filesystem quota and process rlimits are not aggregate accounting. Owned child process groups are killed and reaped on completion/failure; unreaped handles are retained in the helper process when cleanup cannot confirm reaping.

The operator must explicitly supply a trusted standalone runtime root; version checks do not establish trust. The root must be an absolute canonical path, with an executable CPython 3.12 interpreter whose base prefix is that root. CI can pass its provisioned `PDF_TEST_RUNTIME` explicitly. Choose a direct child of `/tmp`, not an arbitrary `RUNNER_TEMP` path. Set the output values explicitly, for example:

```sh
export SLAIF_CPU_V2_TEST_ROOT="$TRUSTED_STANDALONE_CPYTHON312_ROOT"
export SLAIF_CPU_V2_TEST_PACKAGES=/tmp/NEW-PRIVATE-FIXTURE-NAME/packages
```

Keep the legacy CPU fixture variables and native 0.21 capsule variables pointed at their separate fixtures. The receipt records the resolved runtime and version for new runs.
