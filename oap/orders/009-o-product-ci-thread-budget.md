# OAP Work Order — 009-o

Status: FINAL
Identifier: 009-o
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 21341795babef15de2913fd50c4f66d20abca2b1
PR number: 11
Expected active: 009-n
Provenance: H activated MVP development; A ARCH23/A24 private reporting and honest proof; E exact head CI44656541114 Product failures; I independent terminal and controlled-local evidence review
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Apply the locally validated single-thread OpenBLAS setting to the existing
Product test suite step for both Python matrices. Exercise the complete
hosted suite at the new report head. Preserve the existing 16 real
concurrent publication reservations and all test assertions.

## Dependencies and current state

PR 11 is the only open objective PR, against main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b. Clean base 21341795 is the report-only
child of 09f1633b36b05fec7bea2cb24e33a60fdaef4434. Its original response
was consumed once; do not read/replay that FIFO. Prior resolution
`workorders/009-o-prior-resolution.json` SHA256
6f2c280ec82161b51f4b1d6d535252568da95cbfbe5c9e35c28a17e24d07ca49
records no development acceptance. Read also
`audit/009-n-ci-terminal/Root-terminal-review.json` SHA256
536460ebcdb16a92de5e130a099938c375bbe4b70f52f0f4e75bb044123a6643 and
`audit/009-n-check/Root-p3-p4-review.json` SHA256
4ee4f838c49d758bc0b262dccb7cf1d500be0d760bfdb8c82ca92afac86ef801 under
strategic home. These concise records replace rereads of large historical logs.

In hosted run 44656541114 at 21341795, both Product legs collected 2731,
passed 2730, failed the 16-slot publisher test, ended with an ordinary
pytest summary and exit 1. Both hit RuntimeError "can't start new thread"
inside the fixture's Thread.start. The cleanup regression, reader cases,
and four other previously failing publisher cases passed. The three OAP
jobs succeeded. Mandatory downstream steps in the two Product jobs were
skipped. The previous fatal exits 139/137 did not recur. Cause of the OS
thread refusal on hosted runners is unproven.

Local p2–p4 used the same original publisher case after ordinary unit
collection at a 2 GiB address-space cap. Changing only
OPENBLAS_NUM_THREADS to 1 reduced collection from 40 OS threads to one,
VmSize from 1,838,972 to 241,244 KiB, and let that case pass. The
subsequent publisher-only selection with the same setting passed all 88
cases. These controlled results justify the narrowly scoped comparison
on CI. They do not establish the underlying hosted cause.

## Allowed paths and scope

CODING pane %30 in the canonical checkout. First commit exactly these
three transcript paths, sole parent 21341795:

- `oap/orders/009-o-product-ci-thread-budget.md` copied by Root helper
- `oap/active` exactly 009-o plus LF, copied by Root helper
- `oap/reviews/009-o-prior-resolution.json` exact Root resolution bytes

Implementation commit after transcript may touch only
`.github/workflows/oap.yml`, `STATUS.md`, and `docs/evaluation.md`. Workflow
preimage SHA256 29a44dd6f5d36d6035478c469d8b3c666fed8c25fe6c2b36ae2ac4e57c887bc4.
Add these exact two lines after the unique Product test suite name and
before its run key, retaining indentation and LF:

      - name: Product test suite
        env:
          OPENBLAS_NUM_THREADS: '1'
        run: |

Only the env block is added. Test supervisor preimage SHA256
3e15bf1c2e3707de12365ffb6ec73fd24b180c9e7ea023b0817d853c04ab3681.
Verify main's run_child call inherits its env through Popen without an
explicit override. The patch needs no other workflow or tool edits.

## Non-goals

No product or test edits, fixture weakening, test selection, job/deadline
or limit changes, other thread settings, dependency/setup changes,
governance/DHA edits, workflow trigger/credential/deploy changes, retry
of the red run, or unrelated policy integration. No checkout reset,
clean, stash, switch or parallel worker action.

## Acceptance criteria

1. Verify local clean tracked base except the exact active/order bytes,
   current unique remote PR and branch head, active ID and prior resolution
   digest. Commit the transcript, checking its exact three paths.
2. Independently verify additional env lines occur exactly once, under
   Product test suite only, and removing them restores the whole workflow
   byte-for-byte. Verify unchanged supervisor byte hash and the relevant
   literal env inheritance. Run git diff --check on both commits.
3. Add short factual 009-o paragraphs per Documentation. Verify
   implementation diff is exactly the three scoped paths and its sole
   parent is the transcript. No locally executing product tests needed for
   this env-only comparison; tests are already required at the new head.
4. Author one immutable report-only sole child of the implementation.
   Reconcile exact branch/PR and remote head before one ordinary push.
   Verify remote head and report bytes, then respond exactly once using
   normal canonical response helper. Scope result PARTIAL for 009. Report
   CI as awaiting fresh required checks at report-authoring time. Preserve
   historical run evidence and commit identities.
5. Strategic gate after publication is actual fresh full Product matrix
   and all OAP checks/steps green at the exact report head. Report
   uncertainty if still pending; missing or skipped checks block merge.
   A CI failure goes to Root for bounded next diagnosis, never auto-retry.

## Verification and negative evidence

Use existing tools, simple static checks, and Git/GitHub readback.
Keep a concise private log of exact preimage/postimage hashes, commit
graph and command exits under strategic `audit/009-o-check/`. No new
tests or package install. Fresh hosted CI may still fail if a different
resource or ordering constraint causes thread refusal there. Confirm it
with the hosted actual result. Preserve all commands, step selection and
time/byte limits. All prior full qualification gates remain open.

## Documentation

Advance current STATUS heading/lead to 009-o and add a short current
continuation note. Add a short 009-o section to docs/evaluation.md near
the 009-n section, preserving prior evidence. Record exact 009-n head,
CI run and 2730/1 per Product leg, reproduced local comparison and its
limit, Product step setting, and pending actual outcome on new head.
Do not rewrite original 009-n report. STATUS.md preimage SHA256
76ad8496c0c7a560762adfde0371b060980c139c9880e924746eefdfb28954cf.
docs/evaluation.md preimage SHA256
3d36b870e9741f78c5b54bf489013b4eb24b867f3cf8c89e6244fc3863746cb0.

## Runtime and protected resources

Use the current Qwen client, canonical OAP helpers and existing GitHub
development authority. Read only named evidence, affected workflow
range, supervisor call/fallback and required OAP startup sources. No
GPU, model, services, protected data, secrets, hardware qualification,
release or deployment. Independent lanes continue separately.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Same PR 11; no extra PR. Report path
`oap/reports/009-o-product-ci-thread-budget.md`. Include order SHA256 of
this actual order, prior resolution digest, transcript/implementation
SHA, exact reports schema metadata with SELF, verification and
negative-evidence scope. Use canonical respond only once after remote
proof. Scope and publish under standing development authority.
