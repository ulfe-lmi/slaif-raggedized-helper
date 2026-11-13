# Optional CUDA framework profile candidate

This inactive standalone CPython 3.12 Linux x86_64 profile resolves Torch 2.14.0+cu126 only from the explicit official PyTorch cu126 index; other roots use PyPI. The lock contains 58 unique entries: one virtual project and 57 registry packages, including 15 NVIDIA packages. Torch's cp312 wheel SHA256 is e9922441cb2ed269742a46246840c53634ca963f8b0a38d30182c28b4e8388da, matching the saved official metadata witness. uv omitted its size. A zero-body HEAD to the official locked wheel URL returned HTTP 200 and Content-Length 869177930 on 2026-11-12 02:35:41 UTC; this is a server header, not a downloaded-artifact measurement or hash verification. Lock URLs and hashes describe published artifacts, not installed or verified files. The source build configuration's SM70 support does not establish wheel kernels, driver or hardware support. This 2.14 CUDA 12.6 profile is a candidate.

To reproduce metadata resolution in a fresh private directory with the existing approved interpreter, with no ambient configuration or credentials, substitute a private 0700 directory for CAPSULE. Enforce a 64 MiB total cache cap externally and stop on a large binary fallback; do not install or execute packages. The original unmonitored run occupied 12,046,695 bytes after resolution; its peak is unknown. A fresh resolution sampled cache size every 50 ms with an abort threshold of 50,331,648 bytes: sampled peak and final were each 12,046,695 bytes. Sampling is not an atomic quota. That run reproduced the lock byte-for-byte and passed the offline check. Network transfer bytes are UNKNOWN. The file size limit applies per file, not to total cache.

```sh
CAPSULE=/tmp/your-private-capsule
ulimit -v 1048576 -t 30 -f 16384
timeout 120 env -i PATH=/usr/bin:/bin UV_CACHE_DIR="$CAPSULE/cache" UV_NO_CONFIG=1 UV_PYTHON_DOWNLOADS=never UV_CONCURRENT_DOWNLOADS=1 TOKIO_WORKER_THREADS=1 RAYON_NUM_THREADS=1 /home/janezp/.local/bin/uv lock --project worker_profiles/gpu --python /home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12
env -i PATH=/usr/bin:/bin UV_CACHE_DIR="$CAPSULE/cache" UV_NO_CONFIG=1 UV_PYTHON_DOWNLOADS=never /home/janezp/.local/bin/uv lock --check --offline --project worker_profiles/gpu --python /home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12
```

Framework tokenizers 0.23.1 are independent of the native 0.21.4 capsule, definition and space. No native identity changes are implied. A later CUDA backend, worker, controller and exclusive device-lease integration are required before use. Gates remain for measured FP16/FP32 parity, real BGE, driver and SM70 binary compatibility, host resources, installed files and ABI, transitive security and license audit, current rights, and independent ICA. Metadata and empty direct advisory results are not clearance. No runtime, model or hardware qualification has occurred; objective 007 remains partial.

## Current selection (order 007-g, 2026-11-12)

Order 007-g selects this exact candidate as the current GPU profile
source on the 007 branch (PR 9), together with the corrected raw GPU
backend source (assigned exact synthetic device UUID byte guard before
local FP16 model loading, actual child/process-owned DeviceLease
assertion, bounded immutable native-ID input, no autocast, finite
ordered CPU FP32 raw CLS 1024 output, sticky close/owner retention and
original non-Exception identity across hostile backend_owner
attachment). The historical preparation evidence above is preserved
unchanged. This is finite inert source integration with controlled
fakes only: no full 57-package installation, no GPU/driver/device
operation, no model loading, and the future owned worker/controller
and physical drain remain absent.
