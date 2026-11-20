# OAP Coding Report — 009-x

Identifier: 009-x
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 2219a5b16d0d0b1f92a7184ae6aacaa1abb0834a
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-x-protected-policy-payload-install.md`
(final; AMEND existing PR 11; Decision: NONE) at round base
`ed48ca58934b21003ba57d057be1a9921d666e1c` (the verified 009-w
report-only head). Objective: add the one private policy payload
install entry - exact wire bytes, trusted private directory, one
bounded monotonic deadline - admitting the entire candidate through
the production `admit_policy_bytes` and installing it at its SHA-256
digest name, reusing the publisher's complete admitted-content
transaction exactly once with the legacy report publication code,
ordering and outputs and the original capture helpers exact; all
ordinary initial/deadline/slot failures normalize to the entry's
fixed content-free refusal with the truthful installation and
cleanup state, BaseException identity is preserved, and the shared
and new outcome vocabularies map explicitly.

History pushed in this round (no force push, no merge, one PR):

1. `91694b6641eeb7c19e5ebcf3b8c452581e637d30` (parent: round base)
   — exact Root transcript: `oap/active` (`009-x` + LF, 6 bytes),
   `oap/orders/009-x-protected-policy-payload-install.md` (byte-
   identical to the strategic workorder copy, SHA-256
   `32932442a4dac14e46c83cbc9741bae2a9543c400f3a40395b0698e1952a0b44`),
   `oap/reviews/009-x-prior-resolution.json` (SHA-256
   `933434844869eaafa7f2228b0ae1f1f98527a34680d1781c3643d5323505bc8d`).
2. `2219a5b16d0d0b1f92a7184ae6aacaa1abb0834a` (parent: 1) —
   implementation: `src/slaif_raggedized_helper/private_policy_payload.py`
   (new, 7,421 B), `src/slaif_raggedized_helper/private_report_publication.py`
   (changed, 29,405 B), `tests/unit/test_private_policy_payload.py`
   (new, 50,707 B), `STATUS.md`, `docs/evaluation.md` (5 paths total).
3. SELF — this report only; first parent is the implementation head.

## Acceptance evidence

1. Round-base and GitHub reconciliation. Local branch head and
   remote `oap/009-evaluation-baseline` were exactly
   `ed48ca58934b21003ba57d057be1a9921d666e1c`; live `main` was
   exactly `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. GitHub
   shows exactly one open non-draft PR: #11 on
   `oap/009-evaluation-baseline` → `main`, head
   `ed48ca58934b21003ba57d057be1a9921d666e1c`, state OPEN,
   MERGEABLE. The working tree before this round contained only the
   Root activation changes (`oap/active` modified to exactly
   `009-x` + LF, 6 bytes; the new order file untracked, byte-
   identical to the strategic workorder copy) plus the in-progress
   implementation. The prior 009-w report bytes at the round base
   (`oap/reports/009-w-evaluation-declarations-transfer.md`) match
   the prior resolution `report_sha256`
   (`40346291ab0d8f9faa3184fb2a732c785c917b689b24e57ffce252b9691bcc10`);
   the consumed 009-w regular response receipt matches
   `95d36818e2e1b69e9329bb2bdd808c0e63681f2d0d5ab6fc40525821b0f254a2`;
   the adopted hosted terminal review matches
   `16bb1da7354be855eddafe84f6db687aa8ef49f1ec1d1d608c59fe896804628e`.
   All nine prior-resolution input files were present at the round
   base with their exact indexed sizes and SHA-256 (9/9 match,
   including `private_report_publication.py` 28,170 B
   `43207d97f4c195966049cf53bf45c1b47543277dbf95b0bb7068a8a734378e34`,
   `private_policy_capture.py` 14,974 B
   `4d0c3b8002c6c4fabe3c3be3a08d851375249ad2fb807260f56e5fa9e3e7f0fc`,
   `test_private_report_publication.py` 106,921 B
   `1b8cb255ba2b31fe1cb2c197fd6c72d5123dee9c400108d1d2a2b7812e9ad55d`,
   `test_private_policy_capture.py` 37,256 B
   `bb1fccfeddf28c8ecba464fa4f392e6b830f2fc07291a44a65978b19b670f7b9`);
   the three additive payload paths were absent at the round base.
2. Design witnesses at the implementation head. The complete
   admitted-content transaction lives exactly once in the publisher
   (`def _store(` == 1, `def _transact(` == 1, one no-replace `os.link`
   site module-wide) and both trusted entries go through it:
   `publish` performs `_deadline` → `_creator` → `_admit` →
   `_transact(..., error=_publication_error, note="private report
   publication cleanup pending")` → `Receipt`; the payload entry
   performs its own input validation, production admission, chunked
   SHA-256 and then one `_transact(..., error=_payload_error, note=
   "private policy payload installation cleanup pending")` call. The
   payload module owns no reservation, lock, walk, stage, verify,
   cleanup or retirement flow of its own (AST-pinned by the new
   suite: no `_reserve/_release/_walk/_lock/_verify/_stage/_cleanup/
   _store/_namespace` definitions and no destructive or storage-
   protocol primitive call, including any `O_TMPFILE` reference).
   The legacy `publish` ordering, the conservative state, the
   cleanup/retirement and guard policy and the original capture
   helpers are byte-preserved in their semantics and are still
   governed by the two exact inherited suites (160 inherited nodes,
   all passing). The new entry maps the shared transaction outcomes
   explicitly (`PUBLISHED` → `INSTALLED`, `EXISTING` → `EXISTING`),
   wraps the publisher's `PublicationError` to the entry's own fixed
   `PayloadInstallError` with the same truthful state, normalizes
   every ordinary initial, deadline or slot failure to that fixed
   content-free refusal, and preserves non-Exception BaseException
   identity.
3. Local proofs (all synthetic, offline, locked .venv Python
   3.14.4 / pytest 8.4.2 / ruff 0.17.4, fresh private 0700 scratch
   under /tmp, `OPENBLAS_NUM_THREADS=1`,
   `PYTHONDONTWRITEBYTECODE=1`, private `--basetemp`,
   cacheprovider disabled; each invocation bounded by
   `timeout -k 5 120 prlimit --cpu=60 --as=1073741824`):
   - One targeted ruff check on the three changed Python files
     (`taskset -c 0` one-core affinity with `RAYON_NUM_THREADS=1`
     under the same cap): exit 0, "All checks passed!".
   - One combined focused pytest invocation of the new unit file
     plus the two exact inherited publisher and capture suites
     (addopts reset to preserve the summary, `--tb=long`):
     exit 0, `222 passed in 3.52s` — exactly 222 = 62 new +
     160 inherited nodes.
   - One bounded origin check (same bounds): exit 0 — all four
     imported product modules (`private_policy_payload`,
     `private_report_publication`, `private_policy_capture`,
     `supplied_policy_wire`) resolve to the canonical repository
     `src/`; the eight unchanged prior-resolution inputs match
     their exact indexed size/SHA-256; final changed/new bytes:
     `private_report_publication.py` 29,405 B
     `d7c5410280f158cb4cc7c258e06522bb3809aa2c836a79c8b2252b50575ece3e`,
     `private_policy_payload.py` 7,421 B
     `48bf5ec415e049f265c6e90a68caa08283495bf3c07dbace90495f57e041193d`,
     `test_private_policy_payload.py` 50,707 B
     `ac56eed16c5505b7f8c3afd2a7728fc6312367fd2713be1a7a4f77eeb831d814`.
   Preserved debug trail from the in-progress session (same capped
   command form; basetemps retained): the first capped preflight of
   the new suite (13:58, basetemp
   `/tmp/oap-009-x-preflight.2410655`) ended exit 1,
   `56 passed, 6 failed`; the inherited publisher and capture
   suites passed 160/160 under the refactored publisher (exit 0);
   exploratory capped re-runs during diagnosis (14:35
   `/tmp/oap-009-x-preflight-2426578`, 14:43
   `/tmp/oap-009-x-dbg-2430269`) tracked the same six fixture
   failures; the synthetic probe (14:49
   `/tmp/oap-009-x-solo-2432929`, 14:50
   `/tmp/oap-009-x-solo2-2433198`; scratch test
   `/tmp/oap-009-x-debug-test.py`) isolated the selector-ordering
   case in a standalone single-case run, which passed in isolation
   and confirmed by static diagnosis a test-fixture comparison bug
   (sorted actual listing against an unsorted expected list), not a
   product defect. The six fixture failures and their static
   diagnoses: (a) the deadline-expiry parametrization used a
   1-indexed reading of a 0-indexed fake clock (the monotonic reads
   are the deadline base, the pre-admission tick, the post-admission
   tick, the single bounded hash tick and the post-hash tick; the
   wire decoder performs no monotonic read), corrected to
   post-decode / post-hash cuts with the exact call count; (b) the
   byte-conflict fixture wrote 13 B foreign content, so the held-fd
   size gate refused before any read - corrected to exactly the
   candidate's 118 B so the counted read witness and content-based
   conflict fire; (c) the selector test compared the sorted actual
   listing to an unsorted expected list - corrected to compare
   sorted sets; (d) both operation-order tests classified directory
   opens: on Linux `O_TMPFILE` carries the `O_DIRECTORY` bit, so the
   staging filter now requires the full `O_TMPFILE` mask and the
   plain-directory filter its negation; the install order test
   additionally built a hash-keyed index over event tuples, one of
   which carries a link kwargs dict (unhashable) - replaced by
   ordered `events.index` positions over the recorded sequence.
   The exact actual I/O assertions (counted bytes written/read,
   both fsync boundaries, single flock/link, selector bytes and
   linked inode) were preserved unchanged. One origin-check script
   initially included the changed publisher file in the unchanged
   input set (script error, exit 1) and was corrected before the
   recorded run above (exit 0); no product behavior was involved.
4. Git scope. Exactly three Root transcript paths, the
   implementation-only five-path scope above, then this one
   report-only commit naming the implementation as its sole first
   parent. Prior report bytes, the ordered unit process shape and
   all earlier tests are unchanged (verified at the implementation
   head). Expected counts at the new report head (expected until
   measured): group A 1,440, group B 1,694 plus the 62 new unit
   nodes, the unchanged complete integration (951 cases) and every
   downstream step, with all OAP jobs; 009 stays PARTIAL with
   baseline NOT_RUN. No full transfer or qualification acceptance
   flows from publication alone.

## Verification

Commands and outcomes are the exact bounded invocations listed in
acceptance item 3 (raw streams preserved in the private 0700
scratch `/tmp/oap-009-x-proof.WVtaXJ`). All product test evidence
is synthetic/offline: the new suite and the two inherited suites
exercise owned temporary roots, generated bytes, narrowly
delegated descriptor and clock witnesses, fault-injected refusals
and one fresh bounded owned exec child for the symlink-final
conflict only; no network, keys, GPU, model download or live
route, no actual encoder, pin/catalog, publisher, delivery,
current-policy authentication or protected-runtime use. The fresh
full hosted comparison (both Product legs plus all OAP jobs) at
this exact report head is PENDING at report authoring; the adopted
prior hosted evidence is run 44737907992 attempt 1 (all five jobs
and all steps passed; both Product legs 3,134 units — 1,440 and
1,694 — plus the separate 951-case integration run). This report
does not certify its own push or that CI, and Root owns the fresh
CI and terminal review.

## Documentation impact

`STATUS.md`: current slice advanced 009-w → 009-x and one
cumulative 009-x entry added (entry scope, shared once-only
admitted-content transaction, normalization and mapping semantics,
receipt content and authority limits, adopted 009-w hosted
evidence, actual local proof, pending exact-head CI, expected
counts, open gates). `docs/evaluation.md`: new 009-x section
before the preserved input-contracts section with the same
content. Both preserve the representative baseline NOT_RUN and
whole 009 PARTIAL, and state that the open governed operator, the
real representative baseline, source rights and model gates remain
open. All historical sections preserved.

## DHA and boundaries

Decision: NONE. No critical entry appended or modified. Preserved:
the canonical locked .venv (no installation or upgrade), all prior
reports/reviews/orders bytes, unrelated branches and worktrees. No
merge, no new PR, no force push, no tag/release/deploy, no
model/provider/profile change, no next-work selection, no other
consumer started.

## Limitations and deviations

The ordered unit counts (A 1,440, B 1,694 plus the 62 new unit
nodes) are projections until the fresh hosted run measures them;
the prior wall-time variance remains unproven until observed. No
local full unit or integration suite was run, per the order. The
deviations from the as-planned test fixture bytes are the six
statically diagnosed fixture corrections listed in acceptance item
3 (deadline indexing, foreign-content length, sorted-set
comparison, full `O_TMPFILE` mask and negation, ordered event
positions); no product byte, assertion or I/O witness semantics
changed beyond them.

## No merge

No merge performed or requested; PR 11 remains open and
non-draft. Baseline NOT_RUN; whole 009 PARTIAL; DHA NONE.
