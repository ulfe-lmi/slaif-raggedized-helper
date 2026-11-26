# OAP Work Order — 009-t

Status: FINAL
Identifier: 009-t
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: d731dea7f5aad7f55b96386c869795ddba913fe9
PR number: 11
Expected active: 009-s
Provenance: H activated MVP development, A ARCH 13.2–13.4 and 23/A23/A24, E missing canonical supplied-view and pinned membership eligibility primitives, I exact four isolated acceptances and complete canonical CI run 44711903559
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Transfer the exact accepted typed supplied-policy declaration, canonical
wire reader, selected-view record and pinned-membership eligibility
components. Retain their reviewed unit contracts and immutable provenance
on the current evaluation PR. The transferred primitives admit explicit
supplied policy data for later operator composition.

## Dependencies and current state

One open non-draft PR 11, base branch main at
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. Round base is the verified
009-s report-only head identified above. CI run 44711903559 attempt 1
passed all five jobs and all steps. Both Product legs passed the ordered
2,731 units (1,421 in A and 1,310 in B) and independent full integration.
Earlier SIGKILL cause remains unproven. Direct evidence is in strategic
`audit/009-s-check/Root-terminal-review.json` SHA256
`d8a362ce58f53bc2febbcfff6c636e712295599db73b1bd2da8fcf7703d1af9f`.

Use exactly the following strategic sources from the shared workspace.

- `workorders/009-t-transfer-index.json` SHA256
  `9f8a3e9a3245d213a158004bb9aa64f1dd2fc3d546d9d31438a69dc14ea52460`.
  The index lists 16 payload paths, four archive destinations, original
  implementation/report commits, receipt identities and three inherited
  dependency blobs. Read only those indexed objects and scoped evidence.
- `workorders/009-t-prior-resolution.json` SHA256
  `43c7a09aecaf56054c93fc1988d893b9f15819783ba06914f78a8b3dffb57689`.
  The prior owned 009-s terminal response is reconciled. Use the regular
  receipt and prior resolution for provenance without re-opening it.

## Allowed paths and scope

Canonical CODING pane %30. The sole-parent transcript contains only
`oap/active` with exact LF, this order under `oap/orders/`, and the two
strategic files above copied verbatim to `oap/reviews/` by basename.
The implementation, its sole child, contains only the 16 indexed payload
paths (four product modules, four unit modules, four component docs and
four original orders), four indexed archival report destinations,
`STATUS.md` and `docs/evaluation.md`. Source report `SELF` denotes its
original indexed local report commit. The new report-only SELF child uses
`oap/reports/009-t-pure-policy-component-transfer.md`.

## Non-goals

Preserve existing product source, tests, workflow, 009-s CI supervisor,
lock/environment, package metadata, earlier reports, governance and
the critical register. Policy capture, authenticated operator policy,
actual pin/catalog, decisions about model access or source rights,
retrieval, dispatch, delivery and release remain outside this slice.
No branch history import, cherry-pick, new PR, force push or merge.

## Acceptance criteria

1. Verify the actual clean canonical content at the round base, unique
   PR+branch, live main, exact unchanged inherited dependency bytes
   and the exact active/order, prior resolution and transfer-index
   files. The Root activation contributes only the known active/order
   working-tree changes. Stop on extra changes, unknown targets, a
   missing source object or divergence without mutating existing work.
2. Verify every indexed source path's mode, size, SHA256 and Git blob
   OID from its exact commit. Verify each receipt and the original
   sole-parent implementation and report-only SELF child. Each of
   the 16 new source paths and four archive paths is absent at the
   round base. Copy the exact object bytes without replacing the
   historical `SELF` marker, and verify mode, size, hash and blob at the
   receiving path before commit and at the actual implementation head.
3. Run one actual targeted Ruff check on the eight copied Python files
   and one selected pytest invocation on all four new default unit
   modules. Check the imported modules' exact canonical source origin.
   Compare the combined result with 284 expected cases (124 typed,
   95 wire, 47 selection, 18 eligibility). Preserve any failure and
   stop or report an evidence-based gap. The indexed artifact bytes are
   immutable for this transfer. A proposed fix requires a separately
   reviewed order or scoped recovery before further tests/push.
4. Independently verifiable Git scope is four exact Root transcript
   paths, implementation-only scope above, then one new report-only
   commit naming its sole implementation parent. Preserve prior
   report bytes, ordered unit process shape and no old test changes.
   On exact publication, Root verifies fresh full CI against the new
   report head. Expected on each Product leg after this addition is
   Group A 1,421, Group B 1,594, total 3,015, plus separate integration
   and all unchanged required jobs/steps. Report counts as expected
   until measured, and leave 009 PARTIAL with baseline NOT_RUN.

## Verification and negative evidence

Use only canonical installed locked `.venv` under fresh private 0700
scratch with `PYTHONDONTWRITEBYTECODE=1` and scoped Product
`OPENBLAS_NUM_THREADS=1`. Bound each proof invocation with
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824`. Use one selected pytest
invocation with private `--basetemp` and disabled cacheprovider. A
bounded local origin check may occur with the existing interpreter
under the same limits. Preserve commands, origins, scope, actual exits
and raw streams. No test body outside the four indexed files, local
full suite, unchanged retry or increased limits. Local source and
fixture evidence remains bounded and synthetic.

## Documentation

Add a short cumulative STATUS and evaluation entry identifying the four
component scopes, 009-s exact integrated CI evidence, preserved original
SELF provenance, actual local 009-t proof and pending exact-head CI.
Describe the supplied-policy limit, without implying that protected
policy service, live credentials, model dispatch or real representative
held-out qualification exists. Preserve cumulative historical sections.

## Runtime and protected resources

Private local copies and synthetic tests, normal same-PR private hosted
CI, no package installation, product service, real user/corpus data,
protected policy, credentials, models or GPU operations. No external
write beyond the one ordinary existing branch push after local proof.
Use the pre-existing canonical OAP helpers. No direct FIFO access,
extra reader, activation replay or report replay.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Same PR 11, one ordinary push after exact staged-byte and Git checks.
Report path `oap/reports/009-t-pure-policy-component-transfer.md` in its
own immutable SELF child on the implementation. Report original source
and archival identities, actual command outcomes including failures and
pending current-head CI. Verify remote current head, then use only the
one supported `send-response.sh --identifier 009-t --timeout 10` from
the strategic helper path and quiesce. Root owns terminal review.
