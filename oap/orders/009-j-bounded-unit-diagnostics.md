# OAP Work Order — 009-j

Status: FINAL
Identifier: 009-j
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: a7ad70b5e96995122afeae937ce8dd49d569131b
PR number: 11
Expected active: 009-i
Provenance: H standing full-MVP development; E CI43962945486 both product jobs cancelled by annotated20m limit with unavailable logs; I Root exact report/normal/remote/required-step/annotation review; A honest complete verification
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Make the current unit diagnostic step terminate and produce useful stack/status evidence before the enclosing job limit. Same numeric009/PR11; no speculative product repair or acceptance. Root resolved009i CANCELLED/NOT_ACCEPTED in audit/009-i-resolution.json. Its report-only SELF a7ad70b, implementation200fe4c and transcript0cdd00e were reviewed; normal21:44:06.301648Z, old response wrapper3997297 absent. Pane30 is independently verified quiescent with its prior goal achieved and human Qwen settings preserved. Reconcile current head/branch/base/order/normal/dirty state before acting. No010 or merge.

## Dependencies and current state

Run43962945486/run132/attempt1 completed CANCELLED22:08:29Z. Three OAP jobsSUCCESS; product3.12job133634863960 and product3.14job133634863970 CANCELLED. Both check-run annotations explicitly say the job exceeded20m0s. The raw terminal API returns76steps:60completedSUCCESS,2unitsteps still labelledin_progress,14downstreampending; the usual two Complete job steps are absent. Preserve this inconsistency rather than calling any missing gate green. Connector job summaries remained stale; Root retrieved actual terminal metadata/annotations through gh. Connector logs returned404BlobNotFound for both; gh312 --log returned0 with0bytes, not proof of unit execution/success. Exact underlying blocked node/reason remainsUNPROVEN. Earlier009h312exit137cause alsoUNPROVEN. Root104priorfocused units are separate evidence, not fullCI substitution. All raw terminal evidence stays in strategic audit/009-i-ci-terminal/; do not copy logs into Git or rerun oldCI.

## Allowed paths and scope

Only THREE implementation paths: .github/workflows/oap.yml, docs/evaluation.md, STATUS.md. Workflow preimage14169B SHA256556fa14da027d7bb489679c4e4774a5ae3079a539fafc30f80ca30d596946951. Change ONLY the unique Product test suite run block to:

```yaml
      - name: Product test suite
        run: |
          test -x /usr/bin/time
          test -x /usr/bin/timeout
          PYTHONUNBUFFERED=1 /usr/bin/time -v /usr/bin/timeout --signal=TERM --kill-after=10s 180s \
            uv run pytest tests/unit -o addopts= -vv -o faulthandler_timeout=60
```

Exact workflow postimage14317B SHA256fc1ba2cd062ae5d314dc480bb2f2270834a7c22b9a2937fa9afc4b430101655d. Independently reviewed reference audit/009-j-reviewed-workflow.yml; derive the one replacement, do not copy unrelated whole files. Every other workflow byte remains identical. Five jobs, matrices, setup/dependencies, permissions/triggers, full default unit set/order and all downstream integration/OAP/governance/help/doctor gates remain exact. The20-minute product job cap is unchanged. No selectors, skips, xfails, test splitting, dependency/action addition, status masking, shell pipeline/background process, continue-on-error or retry.

This explicitly LOWERED180-second unit command diagnostic deadline sends TERM, with KILL after10seconds if necessary. Timeout/nonzero must fail the step, never become success. Missing tools fail loudly; no install. Builtin pytest faulthandler_timeout60 requests a stack dump during a long test, not test cancellation, proof of cause or an OS containment guarantee. Unbuffered Python output reduces lost progress. External time/timeout change ancestry and resource observation boundaries; neither establishes aggregate/live-tree accounting, descendant adoption/reap, escaped-child containment, exact allocation or OOM cause. A printed stack/last node is localization only. A command exceeding180s may be a legitimate slow case; preserve it and replan from evidence instead of raising the cap or filtering the suite. This is a diagnostic D0 choice, not qualification.

Update only concise current009j paragraphs in the two docs: prior annotated cancellation, narrowed command bound and future new-head CI PENDING. Preserve old records, baselineNOT_RUN and currentprincipal/policy/encoder/data/rights/operator/parser/publisher/OS/20k/hardware/visual/security/license/mergedICA/MVP/release gates. Production program84aceffc, runnerd9f1 and existing unit59f093b4 unchanged. No product/test/config/dependency/law edit, other lane mutation, new worktree/branch/PR or reset/clean/stash/switch.

First commit FOUR transcript paths on exact basea7ad: unchanged FINAL order at oap/orders/009-j-bounded-unit-diagnostics.md; oap/active009-j plus oneLF; exact resolution source at oap/reviews/009-j-prior-resolution.json; exact index at oap/reviews/009-j-root-records.json. Index source audit/009-j-root-records-FINAL.json447B SHA256749c6d45a758e38fd04e3fff98cc9491d61c87b2353fa169144fab64e43cf53d; its ONE resolution3293B SHA256f79d684f5825b834ae4b66909b86d1ca29096b8548942aad7ae87756f7b720a6. One three-path implementation commit sole parent transcript, then immutable report-only SELF sole parent implementation: EIGHT round paths. Preserve every historical report/checkpoint. No intermediate push/force-push or custom post-publication receipt.

## Non-goals

No speculative product/test fix, cap increase, suite filtering, local runtime, environment setup, real data/model/GPU/credentials/service action, old CI retry, new numeric objective, merge, release or deployment. No whole-MVP acceptance from component progress.

## Acceptance criteria

1. Exact current uniquePR11/head/base/branch, normal and Root bytes, four-path transcript/three-path implementation/report-only graph, no unrelated dirties or historical rewrites.
2. Exact workflow postimage; every suite node/order, matrix and other gate preserved; only two current docs beyond that run block.
3. Before implementation commit, prepare audit/009-j-check/review-request.json and implementation.diff with exact proposed three-path hashes. Root independently reviews actual bytes. This is a regular-file gate, not a FIFO signal. No local product execution is authorized; static Git/hash/text inspection suffices. Do not invent YAML/lint/pytest/import/collect/setup/probe checks or inherit old permission.
4. Docs/report distinguish observed20m cancellation from unknown underlying node/cause, prior Root104 evidence and future CI. No green, baseline or full-MVP certificate.
5. After Root exact diff approval, finish implementation/report, push only report head and invoke original respond helper ONCE. Root independently reviews fresh-head fullCI, all required jobs/steps, output and reviews/threads; missing/skipped/pending/cancelled/blocked/failed is not green. No old run retry.

## Verification and negative evidence

Static exact bytes, unique replacement, path diff, unchanged workflow remainder/product/tests/dependencies, transcript/report ancestry and remote identities. No local test/format/lint/import/collect/native/model/fixture/OS journey or setup. Root inspected actual installed pytest builtin faulthandler option source and timeout help as metadata; this does not certify remote versions or runtime behavior. GitHub-hosted new-head CI is the first actual invocation for the revised command. Any dirty mismatch, missing dependency or helper refusal: retain evidence and regular blocker; no reset or silent signal retry. No nested agents.

## Documentation

Keep current docs/report short. Prospective semantic allowance192KiB includes repeated/helper/own verification reads; use relevant ranges, not whole large docs/books/strategic handoff. No broad strategic/worktree search. Source/hash/stat bytes are not model-visible read bytes or dynamic/OS closure; retain estimates and unknowns honestly, no retrospective hard-bound claim. Root owns exact order/records; coding owns implementation/Git.

## Runtime and protected resources

No local product invocation or environment changes. Ordinary fresh-head fullCI after reviewed publication only; explicit decreased unit diagnostic cap above, no higher job/host allowance. Preserve human Qwen3.8-27B/A100Q8/xhigh profile/auth, other panes and existing checkout. Qualified ordinary fresh-context startup, then bounded static goal after actual initial tool reads. Helpers retain sole FIFO readers; no FIFO read/replay/second consumer. Independently scoped parser/publisher software reviews continue under their existing orders, never as whole009 acceptance.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Whole009 resultPARTIAL. Aim3000–4500B, soft6000/hard8192B. Exact implementation/SELF/PR/source identities, static actions, previous cancellation, read-ledger limitations, DHA and remaining gates. After one report-head push invoke ONCE `python3 oap/bin/oap.py respond --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --role CODING --identifier 009-j`. Existing response-send receipt means reconcile without replay; helper verifies remote report and writes its own receipt. ChatOK is not wire delivery. Remain quiescent afterward; no merge/release/deploy.

Strongest counterargument: added timeout can cut off a valid slow suite and the extra wrapper may alter behavior. Prior diagnostic jobs exhausted20minutes without usable logs, so a disclosed smaller failure deadline plus stack output is a reversible evidence step. Any timeout remains a failure to investigate, never an accepted workaround or authority to weaken gates.
