# Private GPU child protocol v1

The future owned sandbox supplies a fixed `/worker.py` entry and read-only `/app`,
`/packages`, `/profile.lock`, `/artifacts`, plus a shared private `/lease` directory.
`/app/src` contains the fixed package and `/app/worker_profiles/gpu/uv.lock` is
the same pinned lock as `/profile.lock`; the fixed entry imports the child module.
It supplies the configured physical UUID in `CUDA_VISIBLE_DEVICES`. There is no
caller-selected code, runtime, lease object, device index, or dynamic backend.
The launcher is responsible for these mounts and for its own process supervision.

Frames are canonical ASCII JSON terminated by LF. Startup contains exactly `schema`,
`api`, `startup_nonce`, `manifest`, `definition`, `tokenizer`, `inventory`, `space`,
`profile`, `policy`, `policy_id`, `code_id`, `host`, and `device_uuid`. Schema is 1,
API is `gpu-owned-worker-v1`; nonce is 32 lower-case hex characters, host and hash
identities are 64 lower-case hex characters. The definition and tokenizer are the
admitted BGE-M3 definitions; the tokenizer artifact is fixed at
`/artifacts/tokenizer.json`. The child verifies CPython 3.12, the pinned 57-package
metadata, source and policy identities, local artifact inventory and semantic space,
then obtains and asserts its own actual lease before backend construction. Ready
contains `ready`, `vocab`, `contract` (`gpu-fp16-cls`) and the common binding:
`schema`, `api`, `startup_nonce`, `space`, `definition`, `profile`, `code_id`,
`policy_id`, `device_uuid`, and `device_key`.

Each request contains exactly `nonce`, `digest`, and `rows`; nonce is unique 32 hex,
and digest is SHA-256 of canonical JSON of the ordered ID rows. Replies repeat the
common binding and request nonce and digest, with ordered raw FP32 CLS `rows` of
1024 values. Inputs contain 1–128 rows, 2–1024 integer tokens per row, at most
131072 tokens, all below admitted vocabulary. The default is eight rows and 64 calls;
maximum is 1024 calls. Startup and request frames are at most 2 MiB, replies 8 MiB,
and cumulative input and output at most 32 MiB and 256 MiB. The immutable policy
can reduce these limits and sets a finite pipe I/O deadline. The child validates
finite exactly representable FP32 output. Protocol failure terminates the session;
ordinary failures are sanitized.

The lease remains held by its actual process-local registry through process exit,
including after `main` returns and after backend close attempts. Constructor failure
can leave an unknown model owner; neither close nor process exit proves physical GPU
vacancy. Namespace-local PIDs are not host recovery authorities. The future controller
must own the supervisor, bound synchronous model calls and cancellation, retain the
mode reservation through uncertain cleanup, and verify actual occupancy before reuse.
Rights, normalization, publication, GPU mounting, physical qualification and parity
remain outside this child protocol.
