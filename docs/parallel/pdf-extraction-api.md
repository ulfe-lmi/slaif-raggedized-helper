# Native PDF extraction candidate

`extract(store, revision_id, PdfRuntime(runtime_dir, packages_dir), policy=None)`
uses the caller-owned `OriginalStore.read_verified(..., max_bytes=...)` to
validate the revision and read only a bounded descriptor; no blob read is
started when the declared original size exceeds the cap. It requires an
approved `application/pdf` source and returns its source scope, dependency,
native blocks, and page statuses. The caller closes the store. The runtime
and package paths are trusted operator configuration, never supplied by PDF
or JSON. The fixed worker requires pdfminer.six exactly 20260107; missing
runtime, backend or Linux isolation raises the input-free
`PdfPrerequisiteError`. Other failures raise an input-free `PdfError`; no
partial extraction result is returned on a worker/validation failure.

Each page is `native_text` or `visual_needed`; a textless page or a page with an unsupported text leaf yields result status `partial_visual_needed`, even when other blocks are present. The worker traverses layout in deterministic preorder, emits text containers once without re-emitting their descendants, and emits uncovered character leaves individually with their actual bounding boxes. This retains native text in nested Form XObjects without inventing separators. Unsupported text leaves are not emitted and mark the page visual-needed. Even native-text pages can contain images or
unreadable material; visual completeness is not claimed. Each block preserves
pdfminer's text (which may synthesize whitespace), page anchor, actual layout
bbox in PDF points with the pdfminer bottom-left coordinate convention and
explicit heuristic reading-order uncertainty. No original byte equivalence,
OCR, table structure, layout ordering, token count or model claim is made.
The policy fingerprint binds backend version, extraction semantics version, point convention and limits. Parent validation requires at least one counted layout object per block; the request nonce correlates a response and does not authenticate a compromised worker.

Defaults and maximums are 2,000,000 input bytes, 32 pages, 20,000 layout
objects, 500,000 decoded text code points, 2,000,000 output bytes and a
2-second cooperative parent wall deadline. The policy can narrow these bounds.
The parent reads the pipe only up to the output cap plus one byte and stops,
kills and reaps only its exact child on error, timeout or caller cancellation;
cleanup may take up to 0.9 seconds. Page admission reads up to the limit plus
one page to detect overflow. Blocking filesystem calls cannot be interrupted
by the cooperative parent deadline. Worker limits are 256 MiB virtual address
space, 1 CPU second, 32 descriptors and 2 MiB file size. A PDF may fail before
these application limits under those OS bounds.

The fixed launcher requires Linux `/usr/bin/prlimit` and `/usr/bin/bwrap`,
working user/PID/network/IPC/UTS namespaces, the explicitly configured trusted
CPython 3.12 runtime and package graph, and system library mounts. It exposes
only those read-only mounts, the fixed worker, the input and minimal proc/dev,
plus a fresh tmpfs; environment is cleared and inherited descriptors closed.
The backend, interpreter, package tree and OS isolation must be qualified on
each deployment host. Namespace support alone is not a hardened sandbox or
hostile-PDF security proof; no seccomp policy is supplied. The parent retains
verified bytes and a temporary input copy for the duration of the operation.

The exact development graph and MIT-0/native/notice questions remain under
review. This candidate adds no project dependency, lock, license exception,
distribution authority or LICENSE-01 clearance. Synthetic fixtures do not
qualify full 006, vision, ICA, MVP or a production deployment.
