# Private report publication API

Status: implementation and tests adapted to the Root unnamed staging
amendment (unnamed-v2) and to the FINAL descriptor tracking repair addendum
(retained unchanged at oap/parallel/orders/): preallocated closed builtin
state/number cells per slot, one CLOSING-before-close protocol, counted
unresolved acquisition and CLOSING/UNKNOWN tombstones, recovery-visible
pending, one bounded no-acquisition no-follow probe before the final open,
and same caught cancellation identity. The prior 67-case 66/1 failure and
corrected 68-case PASS are narrow evidence about the old code and do not
certify the repaired failure paths; no checks are authorized or executed
against the repaired source yet. Runtime feasibility of the O_TMPFILE/procfs
publication path is environment-specific and UNPROVEN until the separately
authorized probe and checks pass. This interface stores opaque supplied
bytes. It does not attest execution, rights, current policy, data quality, or
evaluation results.

## Protocol (unnamed staging)

`publish(report, *, directory, deadline_ms=30000)` accepts exactly a
`source_cohort_runner.CohortReport` or `evaluation_program.Report`, with precisely
their declared instance fields. Both carry `identity_payload` (exact bytes),
`identity` (lowercase `sha256:` plus 64 hex digits), `final_work` (exact integer
0..134217728) and `final_payload` (exact integer 0..268435456). Graded reports
also carry `plan_identity` in the same hash syntax. Booleans are not integers for
this interface. Payload limits are 1..1642496 source bytes and 1..12582912
graded bytes. The identity is SHA-256 of the fixed nominal domain followed by the
exact payload, streamed in at most 65536-byte chunks. The domains are
`slaif-source-cohort-runner-v1\n` and `slaif-graded-evaluation-program-v1\n`,
where `\n` means a single LF byte. Payloads are never parsed or re-encoded.

The directory must already exist, be an exact normalized absolute string, not
`/`, at most 4096 UTF-8 bytes and at most 64 components of 255 UTF-8 bytes each.
Its owner is the effective UID and its mode is 0700; ancestors must be trusted
and writable ancestors must be root-owned sticky directories. The deadline is an
exact integer 1..30000 milliseconds. Checks are cooperative: kernel calls can
exceed the deadline, and this is not a host-wide resource quota.

Publication stages the bytes in an unnamed O_TMPFILE inode held by an owned
descriptor (requested mode 0600; the observed mode must be exactly 0600,
regular, current owner, nlink 0 before writing), writes them once in bounded
chunks, fchmods 0400, fsyncs, rechecks size/owner/mode/inode/nlink 0, re-derives
the namespace, rechecks the same owned staged inode (regular, current owner,
mode 0400, nlink 0, exact size, retained device/inode identity, same device as
the held root), and rechecks the deadline immediately before any link is
attempted, and then creates exactly one no-replace hardlink of that same inode
under the fixed
basename `source-` or `graded-` plus digest plus `.json`, using the owned procfs
magic-link source with the held root as destination dirfd. An existing final
is first observed by one bounded no-acquisition no-follow metadata probe: if
absent, the normal staging/link path proceeds without a final open on the
common fresh path; if present (or on a probe error, which is not a decision),
the real open with all regular/owner/mode/nlink/content/EOF checks, a file
fsync of the verified descriptor while held, then post-fstat and
linked-entry stability and namespace checks, verifies it without
replacement (EXISTING); a mismatched or unsafe existing final is refused
(CONFLICT) and never modified. The probe is not an atomic lease or
security substitute. After a successful link the module requires the same
retained staging inode at nlink 1, binds the held final descriptor's
device/inode exactly to the retained fsynced staging device/inode, checks
exact final 0400/nlink1/bytes/stable signatures, directory fsync and
namespace recheck before latching DURABLE; the stage's already-successful
file fsync is reused for the clean own publication instead of a second
payload flush.

The module performs no destructive namespace operation (unlink/remove/rename/
replace/rmtree or equivalent) in any publication, cleanup, cancellation, fault
or retry branch. Cleanup closes only definitely-owned descriptors. A crashed or
failed operation leaves no named staging entry: an unnamed inode is reclaimed by
the kernel at its last close. Closing a descriptor never changes a link count.

Environmental assumptions (stated, not proven by this document): trusted Linux
kernel and genuine kernel procfs at `/proc/self/fd` in the process namespace.
Unsupported kernel/filesystem/procfs semantics fail closed with a content-free
refusal; there is no named fallback and no cooperating-writer-only weakening.
The advisory directory flock coordinates cooperating publishers; it is not a
safety dependency. This API does not defend process-memory tampering, kernel
compromise, or later owner mutation of a published final; metadata validations
are sequential observations, not an atomic lease. The file and directory
fsyncs are observed protocol operations under these assumptions, not actual
power-loss qualification or a hard blocking-time guarantee.

## States and receipts

A successful frozen, repr-disabled `Receipt` has `outcome` PUBLISHED or
EXISTING, `durability` DURABLE and `cleanup` CLEAN, returned only after the
protocol AND owned cleanup succeed. Publication state describes this call's
effect and verified durability, not a namespace lease: before any link
attempt, NOT_PUBLISHED means no own new final link was attempted by this
call; it asserts no namespace absence, because a pre-attempt existing-file
fsync refusal can end NOT_PUBLISHED with the existing final present; a known
incompatible existing object is CONFLICT. Once a link is
attempted, every unresolved link, verification, deadline, fsync or namespace
failure retains POSSIBLY_PUBLISHED, including a FileExistsError and a later
incompatible or absent final: an exception type or errno alone does not prove
that the link had no effect, and an unresolved post-attempt state is never
downgraded to NOT_PUBLISHED or CONFLICT. The complete final may remain
visible after error and is never rolled back. EXISTING means a matching
complete artifact was verified through the full held-fd path, including its
file fsync; it is not historical proof that this call never created a visible
entry and attests no creation, rights or computation. A durable result
followed by failed or late cleanup raises PublicationError with durability
DURABLE and cleanup PENDING; DURABLE once latched survives later
cleanup/deadline errors.

A content-free `PublicationError` exposes `publication` as NOT_PUBLISHED,
CONFLICT, POSSIBLY_PUBLISHED or DURABLE and `cleanup` as CLEAN or PENDING; its
message is exactly `private report publication refused`. Cancellation retains
the original BaseException identity after bounded safe cleanup and is never
replaced by a cleanup error; the first caught cancellation is re-raised as
the SAME object. No general immunity to repeated external interruption or
kernel death is promised: only a second interruption actually caught by the
bounded cleanup or failure-propagation logic yields the latched priority, and
an interruption reaching uncaught bytecode is not universally suppressed.

`retry_cleanup(*, deadline_ms=30000)` returns a repr-disabled
`CleanupReceipt(attempted, remaining, status)` with exact counts 0..16 and
status CLEAN only when no pending slot remains. It visits at most 16 pending
slots once per call and closes only definitely-owned handles; it never unlinks
any entry. The registry reserves 16 slots, each with six preallocated closed
builtin state/number cells allocated before any acquisition: FREE always with
a cleared number; PRE/-1 reserved and unresolved; PRE/fd and OWNED/fd
definitely stored and closeable; CLOSING/fd|-1 and UNKNOWN/fd|-1 counted,
never retried and retained until process restart. One close protocol marks
CLOSING before the first os.close and, after known success, clears the number
cell before FREE; a close that returns then raises or is interrupted before
bookkeeping remains counted, including a cleared-number unknown. A raising
open or interrupted handler does not prove the kernel acquired no descriptor,
so an unresolved acquisition stays counted. A fresh genuine open reusing the
same integer is a new token, never a retry of the retired one. A slot is
pending before it is handed out, and a failure outside the per-fd close try
leaves the slot pending and visible to retry_cleanup; the guard release is
attempted once on every exit of the covered bounded cleanup and retirement
paths and is never retried blindly: an ordinary release fault is never
raised raw but degrades the conservative status, while a non-Exception
release cancellation is intentionally propagated as the SAME caught object
under the existing latched priority; unregister happens only when every
cell is definitely FREE.
Pending slots retain cleanup metadata, not report
bytes. A fork
child refuses inherited operations before locking; a newly exec'd process is a
fresh owner. Process crash leftovers need separately authorized operator
inspection; this API neither scans directories nor deletes foreign entries.

## Work bounds

For each operation the input is hashed once, staged at most once, and verified
at most once (existing or post-link/EEXIST branch) with at most payload length
plus one EOF byte read. File flushes per call: at most one stage-file fsync,
at most one verified existing/recovery-file fsync and one directory fsync
before latching DURABLE. Scratch is bounded by 128 KiB plus bounded metadata and
the caller-owned payload; no whole-payload copy or JSON re-encoding. Descriptor
lifetimes: at most six counted cells per slot, at most 96 counted (open or
unknown) overall, preallocated before any acquisition; CLOSING and UNKNOWN
cells occupy their slot until restart. These claims remain unverified until Root
authorizes and reviews the probe and the proposed checks. Original 009, real
program/CLI composition, policy, rights, real data, hardware, security,
license, full-MVP and release gates remain open.
