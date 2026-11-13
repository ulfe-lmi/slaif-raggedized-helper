# Synthetic GPU worker metadata fixture

This disposable test fixture supplies six real lightweight distributions (Pydantic and its four dependencies, plus tokenizers 0.23.1) and 51 DATA_ONLY distribution metadata records matching the fixed GPU lock. The latter are not installed framework packages. The backend gate test uses trusted neural framework facades held only in memory and never constructs a model, tensor, or device. It proves metadata and protocol gate wiring only; it does not qualify real frameworks, a GPU, isolation, licensing, security, or model parity.

Supply a trusted standalone CPython 3.12 Linux x86-64 root and a new direct child of `/tmp`:

```sh
python3 tests/support/prepare_gpu_worker_test_backend.py --runtime-dir /absolute/canonical/runtime --target /tmp/new-private-fixture
export SLAIF_GPU_TEST_ROOT=/absolute/canonical/runtime
export SLAIF_GPU_TEST_PACKAGES=/tmp/new-private-fixture/packages
pytest tests/unit/test_gpu_worker_backend_setup.py
```

The target is private and must not already exist. A partial target and receipt are preserved on failure. The helper obtains only the six pinned wheels from PyPI using hash-required binary-only, no-dependency installation; transfer bytes are unknown. Its per-process limits are 1 GiB address space, 30 CPU seconds, 120 seconds wall time and 32 MiB per file. It samples the target against 96 MiB, with 128 MiB headroom; sampling is not an atomic quota and process resource limits are not aggregate accounting. The runtime and fixture must be provisioned explicitly by any future worker integration; no CI setup is implied.
