# OAP parallel work order — PAR-009-SELECT-INSTALLED-POLICY-A

Status: FINAL — isolated local development candidate.
Lane: select-installed-policy. Pane: %32.
Base: 0b337eca746eea97b1e56e71f5a8a06176565a59.
Branch: oap/parallel-009-select-installed-policy.
Transport: isolated local worktree.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a.
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922.
Source inputs SHA256: 34b8419b4209bb8a79b27091b4d9cd327e7d0a8d0237af73bd3a42a4f3b94665.
DHA: NONE.

Provenance H activated MVP, A ARCH 13.3–13.4, E verified payload
installation leaves current selection untouched, I finalized independent
writer-seam resolution and accepted 009-y host gate preserving the exact
009-x installer. The active canonical PR remains independent. Exact
selected writer evidence is future scope for canonical transfer.

## Exact target and paths

Build on the exact accepted 009-y report, with the frozen source
identities and no preparation merge. The existing payload, publisher,
capture, selection parser, wire and all existing tests stay byte-exact.
Only add `src/slaif_raggedized_helper/private_policy_selection.py`,
`tests/unit/test_private_policy_selection.py` and the unchanged Root
order under `oap/parallel/orders/`. Stop on a concrete dependency mismatch.

## Contract and acceptance

1. Add one private `select_installed_policy(wire_bytes, *, directory,
   deadline_ms=30000)` update. Admit exact bytes with the genuine closed
   wire decoder and derive the canonical digest name under one cooperative
   monotonic deadline, using the existing envelope and 1–30,000 ms cap.
   Use no caller record, digest, generation, callback, credential or
   candidate path. Invalid payloads fail before protected namespace work.
   Adopt the existing private writer root admission and cwd-independent
   path rules. All use is synthetic and operator-owned.
2. Use the existing bounded private descriptor-slot, no-follow walk,
   namespace identity and same-root cooperating flock discipline. One
   bounded transaction and lock hold. Never call the payload installer
   or take a second directory lock inside selection. Read and parse the
   exact canonical current record under the lock. Absent, malformed or
   exhausted records refuse. The next generation is the observed current
   generation plus one, including same-wire reselection and A–B–A.
   Derive the new canonical record and pass it through the real parser.
3. Verify the already installed digest-named payload under that lock
   against exact admitted bytes and stable linked owner/mode/size/link
   identity. Reuse the publisher's held-fd verification where it fits,
   including the file flush. Require a verified root-directory flush
   before making the new selector visible. Apply this even to admissible
   existing bytes that do not carry a prior installer receipt. Lost or
   conflicting payloads refuse with the old selector intact. Avoid
   redundant full reads where the accepted bounded verifier suffices.
4. Reserve exactly one fixed staging name `.current-policy.stage` per
   root across all processes and restarts. A preexisting entry of any
   identity or type causes content-free refusal before creating or
   changing any namespace entry. Use exclusive no-follow create under
   the held lock, tracked before acquisition, actual 0600 owned regular
   file and one-link checks, bounded writes, seal to 0400, flush, verify
   exact record bytes and bound inode, and recheck namespace and prior
   selection before one fd-relative `os.replace`. After that attempt
   check linked new selector with exact bytes and staging identity,
   flush the directory and confirm the same namespace and selected
   record. No success after the one deadline. Preserve consumed policy
   and original payload objects, no automatic selector restoration.
5. Expose fixed content-free ordinary errors, separating selection
   before possible effect, possible effect, and verified durable outcome
   from descriptor cleanup and an observed absent/present/unresolved
   reserved stage. An attempted replace may act and then raise. A later
   flush, readback, deadline or cleanup fault never proves rollback.
   Before the attempt, automatically unlink only a proven still-owned
   staging inode under the same verified lock. After the attempt, use
   bounded observation of the reserved name without automatic unlink.
   An uncertain observation must remain unresolved even if an earlier
   state looked known. Do not conflate an absence proof with a selector
   outcome. A retained reserved name blocks new selection even after
   restart. The existing publisher descriptor cleanup must not claim to
   unlink names. Preserve actual first non-Exception interruption by
   identity, bounded creator-process descriptor handling and truthful
   incomplete custody. Preserve the old selected name in failures
   before the replace attempt. Report exact strongest availability
   limitation and distinguish power-loss behavior and protected recovery.

## Required synthetic evidence

- Use the genuine installer and capture reader. A named test fixture
  initializes a synthetic existing selector. Observe A, B and A at
  generations 1, 2, 3 and a further same-wire generation. Match exact
  decoded bytes and immutable payload inode and show no selector writes
  from content installation. No actual initialization entry.
- Verify ordered real file and directory operations and every visibility
  and durability cut, including the payload directory flush before
  replacement and selection directory flush and readback after it.
  Count calls. Use two fresh owned writer processes (independent
  interpreters) running against one actual root and the same lock,
  with deterministic synchronization. Demonstrate bounded contention
  or ordered success and no reused published generation.
- Show a real missing/tampered/link or mode-conflicting payload,
  missing/malformed/exhausted selector, foreign reserved file or link,
  initial and late deadlines, and held-slot/custody refusal. Include
  faults before the replacement call, a replace that acts then raises,
  a replace that raises without acting after invocation, a post-replace
  durability or readback fault and retained reserved-stage restart
  refusal without mutation. Test known stage absence separately from
  unresolved observation. Test interruption/cleanup owner behavior
  at supported fault cuts and preserve fixed public diagnostics.
- Run one bounded four-module focused proof: the full new unit suite,
  existing `test_private_policy_payload.py`,
  `test_private_policy_capture.py` and
  `test_private_report_publication.py`. Include physical import-origin
  evidence and one targeted Ruff on the new Python paths. Use the
  existing canonical `.venv` executables, exact isolated `src`,
  fresh mode-0700 scratch directly under sticky `/tmp`, private
  basetemp, `-p no:cacheprovider -o addopts=`,
  `PYTHONDONTWRITEBYTECODE=1`, `OPENBLAS_NUM_THREADS=1` and
  `timeout -k 5 120 prlimit --cpu=60 --as=1073741824` for every
  execution, including Ruff, any collection or import origins. One
  allowed process-local core for Ruff. Preserve commands, raw streams,
  exits and first faults. No alternate fixture setup or uncapped
  execution. Stop on any genuine product or contract fault and report.

## Publication and limits

Use the owned exact `implementation_cycle.py request` foreground
helper with early tool yield. Wait for FIX or REPORT. After REPORT,
make one immutable report-only SELF child and existing local response
once. Report actual witness limits, bounds, proof hashes and excluded
execution precisely. No direct FIFO access, external writes, real roots
or protected data, runtime/rights claim, old-selection rollback,
root initialization/recovery, GitHub push, PR change, integration,
release or merge. DHA NONE and whole 009 PARTIAL.
