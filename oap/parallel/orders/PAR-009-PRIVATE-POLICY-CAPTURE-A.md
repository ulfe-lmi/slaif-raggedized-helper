# Parallel OAP work order — private policy wire capture

Status: FINAL for separately verified isolated activation.
Provenance H full MVP, ARCH 13.3–13.4/A23/A24, E actual protected
policy capture absent, I scoped read-boundary review 7b6a4961 and
selection implementation b0bd2821.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922
DHA: NONE.

## Goal and scope

Capture opaque policy wire bytes and observe the current selection from
one explicit trusted operator-owned root, under synthetic tests only.
CODING %33, exact isolated base
b0bd2821872e2ee82c98a85d9df509e616c8c642. No canonical or remote mutation.
This is one private offline evaluation invocation owner, without a
serving-process concurrency contract, writer, cache, wire decoding,
semantic ID, principal verification or delivery integration.

Module `src/slaif_raggedized_helper/private_policy_capture.py`.
`PolicyCaptureReader(root: str)` retains a validated absolute path,
creator PID and one operation lock. `read_selection(*, deadline_ms=30000)`
returns the decoded PolicySelection current at its successful observation.
`capture(*, deadline_ms=30000)` returns an immutable
`CapturedPolicyBytes(selection: PolicySelection, wire_bytes: bytes)`
only after successful stable capture and cleanup. One fixed input-free
`PolicyCaptureError(ValueError)`. No logging or partial result.
Use exact existing selection grammar. Selection is fixed
`current-policy.json`; payload is `<wire_sha256>.bin` in the same
root. Payload filename is derived from the admitted digest only, with
no caller entry path. Root comes from this trusted private constructor,
never from a query, caller-supplied selection, or data snapshot.

## Required implementation boundaries

1. Reuse current exact publisher descriptor cell and verified namespace
   helpers where they fit (`_Slot`, `_walk`, `_namespace`, `_file_ok`,
   `_file_signature`, `_cleanup`), through a reader-owned slot, without
   reserve/release in its publication pool. Fixed six cells per owner.
   An operation checks creator PID before entering the lock. Serialize
   one active operation per owner through nonblocking lock entrance.
   An uncertain open/close or failed cleanup latches the owner closed
   and retains its counted slot. It must not acquire more later, never
   retry numeric closes, and never evict an unresolved slot. Close
   all definitely owned cells on exit, including after deadline, with
   at most six cleanup closes, and preserve first interruption identity.
   No program-wide descriptor or service/parallel ownership claim.
2. Validate path through existing absolute path checks. Walk fd-relative
   with no-follow, verified entries and effective UID convention. Root
   must be 0700, selected files 0400 effective UID, regular and nlink=1.
   Pre-probe linked entries to refuse special files before attempting
   open and recheck descriptor and current link type/identity. Use
   no-follow, close-on-exec and nonblocking read flags. The trust model
   is a configured root and a trusted immutable writer, with no hostile
   same-UID, special-device race or guaranteed kernel I/O timeout claim.
3. Use bounded reads of selection <=512 and payload exact declared
   42..64 MiB, requiring captured size, read exact EOF, stable fstat and
   lstat signatures, and digest match. Capture reads selection before
   and after the payload and fails if exact bytes or observed selection
   signature differ. Verify root namespace re-walk and stable required
   entries before return. No persisted dev/inode in the record. The
   reader makes only boundary observations and records no rollback or
   durability guarantee. Preserve ordinary error hygiene after catches.
   Deadline integer 1..30000 ms and monotone cooperative checkpoints
   before/after bounded reads/identity checks; cleanup certainty is
   required for a successful return.
4. Independent custody from publisher: no write, delete, link, rename,
   fsync, lock file, creating files in product source, separate broker
   mutation or changes to the existing shared primitives. No actual
   current auth invocation. Future writer must publish immutable bytes
   before atomic selection and own its writer-side generation contract.

## Verification and publication

Default tests `tests/unit/test_private_policy_capture.py` on private
owned synthetic temporary roots using real data descriptors. Cover
valid current observation and capture, independent root, byte/length/
hash mismatch, noncanonical selection, refusal of mode or symlink/
hard link/special file, growth and pointer replacement around capture,
and owner cleanup/no-new-open after injected uncertain close. Use
actual fd ownership and test-local narrowly delegated fault witnesses.
Source-origin check comes from the physical test path. Cap cooperation
measured by controlled clock/fault hooks; never describe real wall
behavior as a hard guarantee. No real protected path or credentials.

Use existing canonical venv with exact candidate src. Targeted Ruff
(with RAYON_NUM_THREADS=1 if needed) and one publisher-independent
focused selection of new capture test plus inherited selection test,
CPU60s AS1GiB wall120s + KILL5 and private fresh temporary directory.
Preserve full output/exit. One changed-byte correction for a real
failed assertion allowed, with actual setup issues reported separately.

Only the new module, test and exact order copy at
`oap/parallel/orders/PAR-009-PRIVATE-POLICY-CAPTURE-A.md` in a clean
sole-parent implementation. Request exact checkpoint; wait for FIX
or REPORT. Only then one local report-only SELF child and original
response. No old/canonical FIFO, nested agent, remote/real resources.
