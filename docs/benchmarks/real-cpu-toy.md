# Optional random CPU toy probe

This experiment is a synthetic, seeded, random, one-layer XLM-RoBERTa on CPU.
Its 40-character revision is generated locally and is **synthetic**, not an
upstream model revision. The model-name field is a contract label needed by the
existing artifact verifier; the contents are not BAAI weights. Neither a model
hub nor external model, data, credentials, GPU, or service is involved. The two
checkpoint formats contain the same locally generated state dictionary, but
have distinct inventory and embedding-space identities. Agreement on these
rows does not establish BGE behavior, retrieval quality, CPU/GPU parity,
performance, hardware qualification, or a deployed capability.

The execution path has not been run or reviewed. Phase one consists of
source, tests, documentation and an unpublished implementation checkpoint.
Only a subsequent explicit Root source decision and private permit may authorize
the exact reviewed command. The private permit is a procedural source gate,
not human deployment authority. No neural operation may be attempted before
that decision.

The intended permit is a bounded, unique-key JSON object with exactly `schema`,
`purpose`, `head`, `sources`, `runtime`, `packages`, `lock_sha256`,
`framework_pins`, and `limits`.
It binds the exact Git head, relevant source hashes, fixed runtime and package
paths, pinned lock and closed resource limits. It must be an owned private
regular file. The plan command is safe and imports no frameworks:

```sh
python3 tests/support/real_cpu_toy_probe.py --plan
```

After implementation and review, the intended invocation requires all explicit
paths, including a new private target:

```sh
python3 tests/support/real_cpu_toy_probe.py --permit /private/root-permit.json \
  --target /private/new-toy-target \
  --runtime-dir /home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu \
  --packages /tmp/raggedized-cpu-profile-root-repro-860o22xx/venv/lib/python3.12/site-packages
```

This example is not an execution permit. The six-real/22-metadata synthetic
test capsule is not the approved actual 28-package profile. The owned target
is intended to retain two separate generated artifact trees and evidence; an
existing target or symlink is refused and no foreign files are cleaned up.
The planned bounds distinguish per-process resource limits from observed
self-plus-reaped-child CPU and sampled disk; neither is a kernel-enforced
aggregate quota. Resource measurements not actually captured must be reported
as unknown. This experiment grants no license, security, model, independent
architecture review, MVP, release or production clearance.

The generation child uses a fixed seed, vocabulary of 20, hidden width 1024,
one encoder layer, 16 attention heads, intermediate width 32 and 8194 position
embeddings. It saves the same owned random state dictionary in the two formats.
The fixed input ID rows are `[0,4,5,2]` and `[0,5,2]`; the reference uses
padding ID 1 and an explicit attention mask. The local tokenizer session must
return those IDs and matching receipts. Each format gets one resident worker,
two forwards and the actual normalization routine. Raw rows must match the
reference within `1e-5`, and normalized FP32 payloads must have unit norm
within `1e-4`. The evidence includes identities, artifact hashes, shapes implied
by the fixed rows, error maxima, norms, source/profile identities, runtime
origins, measured generation intra-op and inter-op thread counts, observed CPU, elapsed time and sampled disk; unmeasured RSS is unknown.

The overall ceiling is 600 seconds wall and 120 seconds observed self plus
reaped-child CPU. Each generation child has 4 GiB address space, 30 CPU seconds,
120 seconds wall and 128 MiB file-size limits. Worker policy is 4 GiB, 20 CPU
seconds, 45 seconds startup, 10 seconds per forward, 90 seconds lifetime,
two rows and two calls. Tokenization retains its existing 1 GiB, 30 CPU second
and two-second request ceilings. Available memory must be at least 8 GiB before
generation and worker dispatch. Messages are bounded at 64 KiB, aggregate output
at 256 KiB and sampled owned output at 256 MiB. CPU limits apply per process;
observed CPU omits live descendants until reaped, and disk sampling is not a
filesystem quota. No package installation occurs in this probe.

Safe checks use the cached locked offline application environment and do not
import Torch or Transformers or invoke generation:

```sh
RAYON_NUM_THREADS=1 UV_CONCURRENT_BUILDS=1 UV_CONCURRENT_INSTALLS=1 \
  /usr/bin/prlimit --as=1073741824 --cpu=30 /usr/bin/timeout 120 \
  uv run --offline --locked pytest -q tests/unit/test_real_cpu_toy_probe.py
```

The generation child records its Torch thread counts. The fixed worker receives
thread-limit environment variables; its actual inter-op thread count is unmeasured.
