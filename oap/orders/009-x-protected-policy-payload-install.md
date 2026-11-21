# OAP Work Order — 009-x

Status: FINAL
Identifier: 009-x
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: ed48ca58934b21003ba57d057be1a9921d666e1c
PR number: 11
Expected active: 009-w
Provenance: H activated MVP, A ARCH 13.3–13.4, E protected policy selection requires durable digest-named content, I accepted selection/capture and private publisher evidence
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Add the private operator-side storage prerequisite for future policy
selection. Install genuinely admitted wire bytes at their immutable
digest name in an operator-owned root, preserving the current selector.
Reuse the accepted private report publisher's protected storage
transaction. The current-view and encoder candidate lanes have separate
dependencies and reviews. Their provisional code is outside this order.

## Dependencies and current state

Unique open non-draft PR 11 on main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. Exact 009-w report at the
base above. Run 44737907992 attempt 1 passed both Products with 3,134
ordered unit cases and 951 integration cases each, and all five jobs and
steps. `audit/009-w-check/Root-terminal-review.json` SHA-256
`16bb1da7354be855eddafe84f6db687aa8ef49f1ec1d1d608c59fe896804628e`.

`workorders/009-x-prior-resolution.json` SHA-256
`933434844869eaafa7f2228b0ae1f1f98527a34680d1781c3643d5323505bc8d`
binds the exact prior report, consumed regular receipt, terminal review
and base source/test objects. Verify all indexed hashes. The bulk test
files are indexed for identity and execution. Read their named existing
witnesses and relevant fixtures as needed. Review the publisher body,
the reader path grammar and file format, and the public exact wire decoder
boundary. Source hash verification does not require reading the full
history or test bodies into working context.

## Allowed paths and scope

Canonical CODING pane `%30`. Commit three byte-exact Root transcript paths
first: `oap/active` with `009-x` plus LF, the existing exact order at
`oap/orders/009-x-protected-policy-payload-install.md`, and the prior
resolution at `oap/reviews/009-x-prior-resolution.json`. Subsequent
implementation changes only these paths:

- `src/slaif_raggedized_helper/private_policy_payload.py`
- `src/slaif_raggedized_helper/private_report_publication.py`
- `tests/unit/test_private_policy_payload.py`
- `STATUS.md`
- `docs/evaluation.md`

Use trusted operator-side synthetic roots and exact bytes. The candidate
covers immutable content installation.

## Non-goals

The current selector has no writer in this order. Scope excludes changes
to capture/wire/selection, existing
test files, configuration, workflow, dependencies, CLI, policy generation,
pre-encode or dispatch integration, real corpus/credentials/use, pruning,
model or GPU access, new PR, merge, release and deployment.

## Acceptance criteria

1. Add one private payload installation entry. Take exact wire bytes,
   trusted private directory and one bounded monotonic admission deadline.
   Use the production `admit_policy_bytes` for the entire candidate with
   the established wire envelope. Reject invalid inputs before any
   protected namespace work. Derive the sole final name from the SHA-256
   of the exact bytes, in `<64 lowercase hex>.bin` form, in bounded chunks.
   Reuse the capture root's exact path grammar. The input supplies no
   explicit name, digest, generation, parsed DTO, callback or selector.
   Use one absolute deadline, with cooperative checks after actual
   admission, hashing, storage and before a receipt can return.
2. Extract at most the existing publisher's generic admitted-content
   storage operation into a private core. Keep the public report entry's
   existing signature, admission order, path and report identity,
   transaction, exception/cleanup precedence, resource bounds and tests.
   Reuse the exact existing fixed process-wide slot pool, directory-inode
   writer lock, no-follow namespace traversal, existing unnamed stage,
   immutable mode and no-overwrite link, byte and inode verification,
   both fsync boundaries, conservative state and cleanup. This authorizes
   the same pool to bound writes from both trusted entries if called in
   the same process. The admitted capture reader's owner is independent.
   The new entry requires the same supported synthetic filesystem as the
   existing publisher. Preserve its existing cleanup retry interface.
3. Receipt or fixed content-free refusal reports file-installation state
   and cleanup state only, plus exact byte length and wire digest when
   installed. Distinguish existing exact content from a new installation.
   Reject byte/mode/identity conflicts without clobbering or changing
   links. On a failure after possible installation, preserve conservative
   publication state, never unlink or roll back the final object, and
   preserve pending ownership for the actual authorized retry. Keep
   selected `BaseException` identity and existing publisher behavior.
   The receipt establishes content storage only. It confers no authority
   to select a policy or use protected data. The existing selector's bytes
   and linked inode remain unchanged during this operation.
4. Show a stable real reader capture of selected synthetic policy A before
   and after installing different valid B. A separately attributed test
   fixture may then atomically select B and prove the real capture and
   wire decoder admit exact B. This demonstrates interoperability with the
   reader; the fixture supplies no writer-authority evidence. Include
   exact reuse, malformed/oversize or non-nominal input, collision,
   substitution and deadline/fault witnesses. Prove that invalid wire
   reaches zero namespace operations and a post-install interruption or
   flush fault never removes the old selector or final payload. Compare
   positive, refusal, cleanup and retry outcomes and actual operation order.
5. Reconcile the canonical base and pinned inputs; preserve existing tests
   and unchanged Product workflow. Run one focused pytest of the new module
   plus the complete `test_private_report_publication.py` and
   `test_private_policy_capture.py`, targeted Ruff on the three changed
   Python paths and one bounded physical product import origin check.
   Record exact result, exits and raw output. The full hosted inventory
   expects the unchanged A 1,440 and B 1,694 plus the actual new test nodes
   in B, the separate 951-case integration suite, both
   Products and all OAP jobs and every existing step. The hosted result
   is pending until measured at the exact new report head.

## Verification and negative evidence

Preserve the inherited publisher and reader suites exactly. Use counted
real I/O witnesses for the initializer, existing-object conflict, stable
selected-reader interoperability and storage fault cuts in criteria 3–4.
Every added default test remains in the ordinary hosted Product suite.

## Documentation

In STATUS and evaluation notes, document actual proof and fixed existing
limits, immutable payload versus independent selector, shared writer pool
and conservative errors, and separate future selector, recovery and
operator integration. Preserve history and honest mode/authority claims.
Representative baseline NOT_RUN. Whole 009 PARTIAL.

## Runtime and protected resources

Use the pre-existing canonical `.venv` binaries, physical canonical
`src`, a fresh 0700 disposable directory directly beneath sticky `/tmp`,
private pytest basetemp, disabled cacheprovider, `PYTHONDONTWRITEBYTECODE=1`,
`OPENBLAS_NUM_THREADS=1` and `timeout -k 5 120 prlimit --cpu=60
--as=1073741824` for each authorized local proof. One process-local
allowed-core Ruff invocation may use affinity under the same limits.
Use `-o addopts=` to retain the pytest summary. Keep actual failures
and commands. Synthetic ephemeral files only. Report setup faults and
stop an invalid proof before proceeding. No setup installs, uncapped
development runs, full local suite or unchanged retry. The standard
GitHub publication and fresh CI described below are authorized.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Use the existing CODING control and response components. Publish one
immutable `oap/reports/009-x-protected-policy-payload-install.md` report
as a report-only SELF child of the implementation. Include actual test
counts and evidence, exact source/read scope and preimages, Git and CI
identities, bounded operational deviations if any, and pending fresh
hosted review. Use one regular push to the same PR and the established
`send-response.sh --identifier 009-x --timeout 10` once, then quiesce.
Use no direct FIFO reader or signal relay. Root owns exact fresh CI and
acceptance. DHA NONE.
