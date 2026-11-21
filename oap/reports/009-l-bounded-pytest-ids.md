# OAP Coding Report — 009-l

Identifier: 009-l
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Round base commit: 3f8b4eb08c4213b2ea11561e722263c40fa75c1e
Transcript commit: 3af18f85273ffc7a61bef081f6694c232e9813ad
Implementation head SHA: d12a696a4dce12441963b457b981a32bdd42eb2e
Report publication commit: SELF
Order SHA256: 3b6096ae7aa7a04311cc022c0797fbdadd79f165e821809a017ba50b95a31861
Postimage manifest SHA256: 8addafb5ba0ed519f7f799f1e43d3a7e4958ceafaf721fced4a5ecb452618a24
Publication authorization: Root-publication-decision-v2.json (2026-11-17T05:11:27Z)

## Scope

009-l (FINAL) at base 3f8b4eb (the 009-k report head = remote PR head):
bounded pytest case-ID metadata repair. Metadata-only: the exact fifteen
named pytest.mark.parametrize calls gain ONE explicit ids= literal tuple
of short lowercase ASCII case labels (90 total; each 1..48 chars, unique
within its call, descriptive, content-free). No product behavior fix, no
suite narrowing, no limit increase, no completion claim.

## Change

Transcript 3af18f8 (sole parent 3f8b4eb): the four exact
Root paths (order, active, root-records, prior-resolution),
byte-verified. Implementation d12a696 (sole parent
transcript): fifteen test files + docs/evaluation.md + STATUS.md (17
files; all 21 postimage blobs equal the Root-approved v2 manifest).
Display-only effect: -vv node IDs use the bounded labels instead of
auto-derived serialized scalar payloads, so verbose diagnostics no
longer embed large fixture bytes in test names.

## Evidence (static; no local execution)

- Coding-side: all 15 preimage SHA256s equal the frozen Root index;
static AST differential removing exactly the new ids keywords yields
the exact preimage AST for 15/15 files; 15 calls / 15 files / 90
labels; case census per call unchanged; no import/body/name/argument/
order changes.
- Root independent: 15 files / 15 calls / 90 cases AST invariant PASS
(exact source proof, static; not product test/collection evidence and
not current authority).
- Ruff deviation disclosure (author attestation; no retained logs;
not Root-qualified; no reruns): three unauthorized invocations -
(A) 15 changed files, repo pyproject config, ruff 0.17.4, exit 0
"All checks passed!"; (B) /tmp preimage copies under ruff DEFAULT
config, no evidentiary value claimed; (C) tests/unit/ directory, repo
config, exit 0. Details: audit/009-l-check/ruff-evidence-v2.json.
- Preserved current failure (immutable): run 44017736685 at 009-k head
3f8b4eb: 3 OAP SUCCESS; both Product jobs FAILURE - 2455 collected per
whole-unit run; verbose auto-derived parameter IDs serialized large
scalar fixtures (first 65,537 B header) into node names; supervisor
raw 16,843,391 B crossed 16 MiB; OVERSIZE 128 after 5.62/5.97 s. The
earlier 20-minute cancellation (cc51b9a run 43978029330) and 009-h
3.12 exit-137 causes remain UNPROVEN.
- Fresh head CI is PENDING: the first actual whole-unit run of this
metadata change; expected collection is the same 2455 unit cases
(expectation, not a new measurement). No product/native/pytest
collection run was made or claimed locally.

## Acceptance evidence

1. PR 11 unique open/non-draft/unmerged; remote head 3f8b4eb = round
base; main 5a7b41cc; no auto-merge; only authorized dirties.
2. Transcript/implementation sole-parent chain and exact path sets
verified by ordinary Git/hash only; 21/21 postimage hashes equal the
v2 manifest (machine-verified pre-push).
3. Precommit v1 (5,979 B), Root return v1 corrections, and v2 request
(2,987 B) / manifest (4,926 B) / ruff evidence (1,817 B) reviewed;
publication authorized by the exact decision above.
4. This report is the sole new path of the SELF commit; one
fast-forward report-head push; no intermediate push/force/merge/tag/
deploy; respond 009-l once after remote verification.

## Limitations and gates

Whole 009 PARTIAL. Fresh head CI pending (the actual whole-unit run;
no green/cause/baseline/whole-MVP certificate follows). Real
representative baseline NOT_RUN. Current principal/policy, qualified
real encoder, held-out data + rights, operator/CLI, parser/publisher
joins, raw 4096-row ceiling, hardware/visual/security/license/
merged-ICA/full-MVP/release gates remain OPEN. The three Ruff
deviations are recorded, not retroactively authorized. DHA NONE. No
merge.
