# Optional CPU framework candidate

This inert candidate targets CPython >=3.12,<3.13 on Linux x86_64. It pins torch 2.14.0+cpu, transformers 5.22.2, tokenizers 0.23.1, safetensors 0.8.0, huggingface-hub 1.31.0, pydantic 2.14.3 and numpy 2.5.4. Torch alone uses the explicit official PyTorch CPU index; the remaining graph uses PyPI. The lock contains 38 registry packages and the virtual project. It records wheel URLs and hashes; the PyTorch index did not provide a wheel size to uv, so its lock entry lacks a size. An independent HTTP HEAD on 2026-11-12 at 02:26:24 UTC returned HTTP 200 and Content-Length 196253793 for https://download-r2.pytorch.org/whl/cpu/torch-2.14.0%2Bcpu-cp312-cp312-manylinux_2_28_x86_64.whl, with zero payload bytes read. This is an observed header, not a measurement or digest verification of downloaded wheel bytes. Future acquisition requires separately bounded download and actual byte-count and digest verification. The lock is not evidence of installed files. No current runtime has switched: the existing CPU profile remains unqualified.

Reproduce metadata resolution in a private cache with the existing CPython 3.12 interpreter and uv, with python downloads disabled, a 16 MiB file limit, 1 GiB address space, 30 CPU seconds, 120 seconds wall time, one download/thread, and a monitored 64 MiB cache ceiling. Run `uv lock --project worker_profiles/cpu-v2 --python <existing-python>` and `uv lock --check --offline --project worker_profiles/cpu-v2 --python <existing-python>`. Do not install or execute packages for this preparation.

The independent native tokenizer capsule, engine 0.21.4, definition and semantic space remain unchanged; framework tokenizers 0.23.1 is separate. A later reviewed cutover must update the framework inventory and version validation in `cpu_embedding_backend.py`, the lock path and inventory checks in `cpu_embedding_worker.py`, synthetic metadata fixtures and `tests/unit/test_cpu_worker_backend_setup.py`, and the pinned inventories in `tests/support/real_cpu_toy_worker.py`, `real_cpu_toy_probe.py`, and `prepare_cpu_worker_test_backend.py` as applicable. Preserve the independent native 0.21.4 checks and definitions. Update affected tests and evidence rather than treating this lock as installed metadata.

Actual framework class loading, owned toy and real BGE execution, FP16 parity, host and ABI qualification, security and transitive license audit, and independent completeness audit remain gates. Empty direct advisories or newer versions do not constitute security approval. No hardware, quality, resource, or MVP qualification is claimed.

The published Transformers 5.22.2 metadata requires huggingface-hub >=1.31.0,<3.0, tokenizers >=0.23.1,<0.24.0, safetensors >=0.8.0 and numpy >=1.17; the ordered pins satisfy these constraints. Resolution is metadata evidence, not runtime compatibility or a security clearance.

## Current selection (order 007-g, 2026-11-12)

Order 007-g selects this exact candidate lock/graph as the current
CPUv2 source selection on the 007 branch (PR 9): the CPU source gates
now target this graph (Torch 2.14.0+cpu / Transformers 5.22.2 /
framework tokenizers 0.23.1), and the required CI step provisions the
portable synthetic fixture from this lock (six exact wheels plus 32
explicitly DATA-ONLY metadata distributions). The historical
preparation evidence above is preserved unchanged. This selection is
source and synthetic-fixture integration only: no full 38-package
installation has completed (the latest actual attempt is the recorded
PARTIAL uv allocation abort under the fixed 2 GiB address space), no
neural import, and the actual BGE model/checkpoint/hardware remains
UNRUN/UNQUALIFIED. The legacy CPU profile (Torch 2.10.0+cpu /
Transformers 4.51.3) and the native 0.21.4 capsule remain intact and
independent.
