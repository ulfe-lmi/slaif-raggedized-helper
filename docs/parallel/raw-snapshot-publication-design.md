# Private raw snapshot directory publication

Status: FINAL DESIGN; a finalized order and live reconciliation activate implementation.
Provenance: H full MVP and parallel development mandate; A immutable snapshots, original008,
ARCH11.4/11.5/12/19; I reviewed files1131/SELF84fb and directory591a/SELF6228436813498b493a704d5f27cff00659c82958, combined peer4326 and Root actual filesystem controls; E the source-bound file set and directory reader have no atomic publisher. DHA NONE.

This is independent software work while canonical007 remains active. It publishes detached
snapshot DATA to an owned private directory. It neither selects a current snapshot nor grants
rights, readiness, model qualification, production deployment or a new numeric OAP activation.

## API and exact scope

Add raw_snapshot_publication.py, unit tests, actual filesystem composition tests, API document,
exact design copy and order: SIX new paths. Base is exact directory SELF6228436813498b493a704d5f27cff00659c82958.
No predecessor, store, source, reader, manifest, payload, CLI, dependency, policy, CI or law edits.

publish_directory(originals,derived,store_root,core_bytes,files) returns frozen Publication
with snapshot_id, created (bool) and freshly loaded BoundSnapshotData in data. Inputs use the
same actual stores, exact core bytes and sorted tuple of exact (relative_path,bytes) pairs as
raw_snapshot_files.validate_files. Never accept a supplied BoundSnapshotData as source proof.
Borrow both stores; do not close or write them. Require the caller to establish processing
permission before source validation. Current principal policy is separate, with no default grant.

Run actual validate_files before destination mutation. Preserve its complete actual original,
bundle, row-map, membership, dense, lexical, policy and metadata checks. Parse the actual core,
use its content identity sha256:<64hex>, exact descriptors, bounds and safe paths. Reject known
layout conflicts with reserved .core.json, file/directory prefix collisions, unknown files,
wrong order, bytes or hashes before filesystem work. Preserve existing limits: core<=262144B,
member total<=96MiB, <=258 members, <=1033 tree nodes and existing per-role limits. These
components' row/partition limits remain explicit; this leaf does not claim a qualified20k
snapshot or quietly raise their bounds. A source-bound snapshot is still DATA, not neural proof.

## Private layout and publication

Final layout is the existing reader's store_root/snapshots/<bare_digest>/.core.json plus exact
payload files. Configured root is an existing canonical absolute private0700 directory under
trusted ancestors, with the same no-follow/ownership/path requirements as the actual reader.
Do not create or chmod configured ancestors. May create snapshots with0700 when absent; validate
existing snapshots owner/mode/type and stable link. If snapshots is created, fsync its pinned store_root parent before reporting success. Reject symlink, foreign owner, writable
ancestor, hard-linked regular file, path alias or unexpected destination type. Pin directory
FDs and operate relative to them. Revalidate the configured path and namespace before success;
writing safely to an old detached root cannot become successful configured-root publication.

Prepare a fresh random owned temporary directory under snapshots with0700. Never treat an
existing temporary name as yours, enumerate/delete other temporary trees or sweep old files.
Create exact payloads and .core.json with exclusive no-follow regular creation, bounded writes,
complete byte checks and mode0400. Create only required descendant directories, ending0500;
final snapshot directory0500. No symlinks or hard links. Verify known ownership, types, links,
sizes, hashes and closed exact tree; retain descriptors sufficiently to detect replacement.
Temporary writable modes are private to their0700 parent. No source content appears in errors.

Fsync written file data and final mode metadata, then descendant directories bottom up and
the temporary snapshot directory. Publish atomically with no replacement. On this Linux-only
project, use actual renameat2(RENAME_NOREPLACE) through an explicit bounded standard-library
binding, or an equivalently real tested atomic no-replace primitive. A prior exists check plus
ordinary overwriting rename is NOT equivalent. Missing primitive/support refuses explicitly,
never falls back to clobbering. No new dependency, shell command or external helper is needed.
Fsync the snapshots parent after successful rename. Preserve failures around fsync/rename as
uncertain outcomes; these calls are not universal power-loss or deployment filesystem proof.

An existing final digest, including an empty or invalid directory, is NEVER overwritten,
replaced, repaired, chmodded, removed or recursively cleaned. If it exists, use actual
raw_snapshot_directory.load_directory and exact expected core/identity correspondence;
return created=False only after full fresh validation succeeds. A concurrent same-ID winner
is handled the same way. Conflicting, corrupt or unsafe existing destinations refuse. No
check-then-rename race may silently replace one. Existing validated content is reused; do not
invent proof of its historical fsync or creator from its pathname/hash/mode.

After a new rename and parent fsync, use the actual directory reader against the configured
path to freshly validate complete on-disk bytes and source correspondence before returning
created=True. All private reader checks remain. A changed original or namespace after staging
may leave an immutable unreferenced directory and cause refusal; do not delete the final tree
to conceal the failure. Returning detached data does not keep an open handle or authorize use.

No current pointer, CAS, activation record, retention, deletion, withdrawal, publication to
network, cache, query worker or snapshot promotion. Those remain separately designed gates.
No object or directory becomes Ready from successful immutable DATA publication.

## Cleanup, concurrency and failure

Catch errors only for finite own cleanup and content-free refusal, preserving the original
non-Exception object and interruption priority. Allocate and retain actual operation ownership
before fallible filesystem work. Close known owned FDs once; attempted close with uncertain
outcome is not a safe numeric-FD retry. Keep any genuine uncertainty strongly reachable with
supported creator-owned cleanup semantics and disclose its limits. Do not invent atomicity
between a kernel return, Python assignment or asynchronous interruption. Forked or busy owner
cannot clean creator resources. Avoid a new global controller or arbitrary cleanup callbacks.

Clean only the exact temporary tree this operation created, using pinned actual directory
identity and safe relative operations. No cleanup through a replaced pathname, symlink,
unknown descriptor, borrowed store or final published tree. If supported cleanup is pending,
retain the real owner, not an exception-ID guess. Do not conceal cleanup or durability failure
as success, silently lose the original interruption, or claim a lock remains after uncertain
close. The operation needs no model process or mode reservation.

Set rename_attempted before the fallible atomic call. A throw may occur after publication;
report uncertainty honestly and leave any final tree alone. A safe content-free PublicationError
may expose the known candidate snapshot ID and publication_may_exist boolean, explicitly not
proof of publication. Preserve original non-Exceptions. Caller recovery uses fresh actual
load_directory; never delete/replay based on a guessed outcome. Resume/idempotence must not
mutate an already committed target. No public path or source text in diagnostics.

## Finite actual evidence

Use actual private original/derived stores and a complete valid core/files fixture from the
accepted directory tests. Actual validate, publisher writes, fresh directory reader and source
validation all run. Verify exact data, permissions, hashes, closed tree and borrowed stores;
success followed by same-ID reuse without target mutation. Test actual corrupt input before
writes, source change after staging, unsafe existing target/root/ancestor, extra or missing
member, file/dir collision, configured-root replacement, actual same-ID concurrent publishers,
and an existing empty/invalid target that remains byte/inode unchanged. Actual no-replace
primitive must be exercised, not mocked as proof. No sleeps as race proof: coordinate owned
child processes through bounded private test synchronization.

Exercise controlled pre-rename failure, parent fsync failure after rename, interruption after
actual rename before return and cleanup/close uncertainty. State actual result and whether an
unreferenced final directory may exist. Original interrupts and exact own cleanup survive;
only owned temporary resources are touched. One original narrow actual guard control with
original/control/restored effect; changing one guard need not defeat independent later guards.
Use temporary in-memory functions only; no product disk patch or whole-source validator fake.

Each ordinary invocation: CPU30, AS1GiB, wall120, OMP/OPENBLAS/MKL/RAYON/NUMEXPRthreads1,
no bytecode, private basetemp. Use cached app/NumPy and existing native fixtures only for valid
source construction. Split tests when necessary; no automatic cap raise, skip/xfail or broad
unchanged predecessor repetition. Ruff wall120 allocator exception is separate. No framework,
Tensor, model, GPU, driver, network, installs, service, credentials, real corpus, shared fixture
writes, other panes, nested agents, model/profile/auth changes, push, PR, merge, release or
canonical FIFO use/replay. Filesystem facts apply only to tested private local setup.

Record precise source/readset bytes, commands/counts/results, log/witness hashes, failures,
limits and strongest counterargument. Pre-report implementation checkpoint requires Root
FIX/REPORT before immutable SELF and ONE normal response. Actual current rights, query
compatibility, retrieval, pointer/CAS, retention, efficient scale, neural/FP16/hardware, security,
licenses, held-out evaluation, canonical integration/CI, milestone ICA and full MVP remain open.
