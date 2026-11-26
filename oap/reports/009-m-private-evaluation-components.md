# OAP Coding Report — 009-m

Identifier: 009-m
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Round base commit: 494a1908b3f0719c0eb78becdcbcb6c5c3ac0d74
Transcript commit: 7db62b9cd29e5f2622e7c3141cc9ecee9eded9e4
Implementation head SHA: 1169f3a5dce301e0b7ba089eee4914a8812f9fe3
Report publication commit: SELF
Order SHA256: 0160a8b3150027e6ed60f1bb96a3e93efb77d68b28ecb74599b301a85772eb92
Root index SHA256: 7b4f4ec00392180aae2c89adec90a63d94dbb9da265c57607231e74a7c6ee563
Publication authorization: Root-publication-decision.json (a3eec1d0…)

## Scope

009-m (FINAL) at base 494a1908 (009-l report head): byte-exact transfer of
the two reviewed private evaluation components into canonical 009. Code
presence only: no evaluate CLI, current-principal provider, real data,
models, encoder or baseline; no refactoring/behavioral patching; no
candidate-branch merge/cherry-pick (preparation bases e3bf5b84/45bcb729 not canonical ancestors).

## Change

Transcript 7db62b9 (sole parent 494a1908): four exact Root paths (order,
active, root-records, prior-resolution), byte-verified. Implementation
1169f3a5 (sole parent transcript): exactly 18 paths = 16 Root-indexed
blobs + 2 current docs. Parser (implementation ceef2888, original report
head 82923f0): plan-wire API/v1 docs, PAR-009-PLAN-WIRE-A order,
evaluation_plan_wire.py, test_evaluation_plan_wire.py (186 cases) +
byte-identical archival original report
oap/provenance/009-m/PAR-009-PLAN-WIRE-A.original.json. Publisher
(implementation 70bf21fc, original report head 6196ef2): three
publication docs, four PAR-009-REPORT-PUBLICATION-A order files,
private_report_publication.py, test_private_report_publication.py (88
cases) + oap/provenance/009-m/PAR-009-REPORT-PUBLICATION-A.original.json.
Each archival SELF resolves the original report head, never the later
archival-copy commit; source-graph mapping in
oap/reviews/009-m-root-records.json. Docs: current 009-m factual sections
in docs/evaluation.md (+3238 B) and STATUS.md (+2747 B; slice pointer
009-l -> 009-m), combined delta 5985 B.

## Verification (static + one authorized lint)

- 16/16: source Git-object OID = destination OID; absent at 494a;
noclobber create; post sha256 + size + git blob OID +
mode (0644 regular, nlink 1, no hardlinks) match the Root index (manifest
10141 B, be1bfe53…).
- Core unchanged vs index: evaluation_program.py 84aceffc,
source_cohort_runner.py d9f1b0e8, pyproject.toml a4c6c55e.
- One authorized static Ruff check of exactly the four new Python files
(repo pyproject, no flags/retry): exit 0, "All checks passed!" (19 B
output retained); static lint only, no tests/imports/collection/product/
native/model execution; malformed initial record retained as v1,
corrected v2 valid, no rerun.
- CI run 44022614755 at 494a1908 SUCCESS (5/5 jobs, 78 steps); the
3f8b4eb run 44017736685 OVERSIZE128 failure preserved with its established cause (auto parameter IDs/oversized step output); only the
older 20-minute/exit-137 underlying causes remain UNPROVEN.
- Fresh report-head full CI PENDING as the first canonical combined run;
expected 2729 unit cases = 2455 current + 186 parser + 88 publisher
(expectation only - mismatch is a stop, not a silent adjustment); every
new case must actually run, not be skipped. Inherited scoped source
evidence (284 parser PASS = 186+44+54; 88 publisher PASS) is historical
on the exact source, not a fresh combined claim.

## Acceptance evidence

1. GitHub reconciled at round start: PR 11 unique OPEN at head = base
494a1908, main 5a7b41cc, no auto-merge; only Root order/active dirtied
the tree.
2. Transcript sole-parent 494a with four exact Root bytes; implementation
sole-parent transcript, exact 18 path set (machine-verified
pre-push); postimages 18/18 equal the Root exact postimage review
(c97fc030…).
3. Checkpoint v2 request (4031 B) + transfer manifest approved by the
exact decision (a3eec1d0…) before publication.
4. One fast-forward report-head push; no intermediate push/force/merge/
tag/deploy; respond 009-m once after remote verification.

## Documentation impact

New 009-m section in docs/evaluation.md plus STATUS.md slice pointer +
paragraph: components now present on this unmerged branch,
code/data/identity limits, inherited source evidence vs fresh canonical
CI pending, all open gates and prior failures. No history rewrite.

## DHA and boundaries

DHA NONE; no CRITICAL change. Preserved: candidate branches/worktrees
(untouched; no merge/cherry-pick/reset/clean/stash/switch), original
local source reports/branches, Qwen profile/auth, other worktrees/repos,
original FIFO readers (none started). No merge; PR 11 remains
open and unmerged.

## Limitations and remaining work

Whole 009 PARTIAL; no deployment readiness implied. Fresh report-head CI
pending (no green/cause/baseline/whole-MVP certificate follows). Real
representative baseline NOT_RUN. no-auth/no-current-policy/
no-real-producer/no-model-qualification labels hold: parser admission is
a private 8 MiB closed wire to real Plan objects, not current
auth/grades truth; publisher private unnamed-stage/no-replace/
durability/cleanup contracts remain exact, no new target/hardware
qualification from import; pure policy primitives remain separately
INERT design work (pure-policy implementation is separate external local
work, not in this canonical transfer). The source workload illustration
is 20k CHUNKS, not 20k documents; the raw 4096-row ceiling stays open.
Existing local real-resource evidence is neither erased as globally
unproven nor universalized. Rights/privacy/visual/security/license/
hardware/merged-ICA/MVP/release gates remain OPEN. Record-correction
disclosure: the initial 7388 B checkpoint request was overwritten during
compression before v1 preservation (original bytes unavailable);
preserved request v1 is 5168 B, corrected v2 is 4031 B, no reconstruction. No green certificate, no 010, no merge; DHA NONE.
