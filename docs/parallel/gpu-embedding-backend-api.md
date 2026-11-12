# Private GPU raw CLS backend

`GPUEmbeddingBackend(manifest_bytes, artifact_root, definition, tokenizer_definition,
expected_inventory_id, lease, expected_device_uuid)` admits the existing BGE-M3 space and
local closed artifact tree. The caller supplies a live `DeviceLease` acquired under the common
trusted local lock root, the canonical physical GPU UUID, and current rights for the data and
model. The lease remains the caller's responsibility. This private in-process API grants no
rights and has no HTTP or CLI entrypoint. Artifact files and their ancestry must remain protected
from modification through loading and use.

The runtime requires the exact CPython 3.12 GPU profile lock and installed package versions,
including the critical framework module versions. `CUDA_VISIBLE_DEVICES` must already equal the
configured canonical UUID. The backend checks one visible CUDA device and the pinned Torch UUID
byte binding against that identity before loading. This is neither a physical occupancy check nor
a host, driver, kernel, or security qualification. It loads only the local XLM-R model in FP16,
checks its configuration and device, and does not invoke a tokenizer. IDs must be supplied by the
separate native 0.21.4 tokenizer contract; framework tokenizers 0.23.1 do not redefine the space.

`forward_cls` accepts 1–128 exact lists or tuples, each containing 2–1024 exact integer token IDs
within vocabulary bounds, with at most 131072 tokens total. It returns ordered finite raw CPU
FP32 rows of 1024 values. Normalization and storage are separate producer obligations. Calls are
nonreentrant and refusals are terminal; the caller must not retry the instance. A fork cannot use
it. `close()` drops its model reference, never releases the lease, and does not prove that kernels,
allocations, or the CUDA context have drained. If loading fails before `from_pretrained` returns, no local model may have been captured and
there may be no attached `backend_owner`; framework-internal partial allocations are unknown.
After model capture, failures retain the actual owner in a local registry. Ordinary refusals
attach that owner; an original interrupt may reject attribute attachment and remains primary.
The registry is independent of physical drain. Local close only drops owned references; it does
not release the caller's lease or prove allocation or context vacancy. A future owned process
lifecycle and controller-observed vacancy are required before device handoff. This limitation
does not authorize loading in an unowned process.

Tests use synthetic artifact bytes and controlled fake framework objects with an actual cooperative
kernel lease. They do not run CUDA or real model inference. FP16 parity, real artifacts, hardware,
driver, isolation, rights, license and security review, independent audit, and deployment remain
separate gates. A cooperative lock does not exclude noncooperating processes or coordinate other
roots.
