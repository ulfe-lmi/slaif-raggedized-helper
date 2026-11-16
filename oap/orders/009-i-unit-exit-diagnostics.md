# OAP Work Order — 009-i

Status: FINAL
Identifier: 009-i
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 71172016968615365a59cf0341c699e105d38012
PR number: 11
Expected active: 009-h
Provenance: H standing full-MVP development; E fresh CI43949914814 Python3.12 unit step exit137 without localization; I Root exact graph/report/normal/all78steps/log review; A honest unfiltered verification
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Produce diagnostic evidence for the unexplained Python3.12 unit-process exit, preserving the complete suite. This is same numeric009/PR11, not a speculative product repair or acceptance. Root resolved009h FAILED in audit/009-h-resolution.json. Its immutable report-only SELF7117201, implementation d8a43fb, transcript b1aafae and earlier base857355ab are reviewed. Normal verified20:42:59.547803Z; old sole response wrapper3937128 is absent and coder30 is quiescent with its bounded goal achieved. Reconcile current state before work. No010, merge or release.

## Dependencies and current state

Fresh run43949914814/run131 is terminalFAILURE at this head: four jobsSUCCESS, oneFAILURE;78requiredsteps=71success/1failure/6skipped. AllthreeOAPjobs and the entire product3.14job succeeded, including integration. Product3.12job133589340533 ends unit step with exit137 after90%progress plus52dots, without a failed-node traceback or completed summary; six downstream steps skipped. Precise cause UNPROVEN: no OOM, sender, culprit node or constructor-recurrence claim. Product3.14job133589341005 fullunit/integration progress reaches100%; existing multithreaded-fork DeprecationWarning is retained, not a failed gate or full OS certificate. No old run retry. Root104focused units remain attributed earlier bounded evidence, not a replacement for fullCI.

## Allowed paths and scope

Only THREE implementation paths: .github/workflows/oap.yml, docs/evaluation.md, STATUS.md. Workflow preimage14095B SHA256a26bda03a81323ed1213b87965c8ec7200da596fb9d5194f1c0b3739522ca1f8. Change ONLY the Product test suite run block from its unique `run: uv run pytest tests/unit -q` to:

```yaml
      - name: Product test suite
        run: |
          test -x /usr/bin/time
          /usr/bin/time -v uv run pytest tests/unit -o addopts= -vv
```

Expected exact workflow postimage14169B SHA256556fa14da027d7bb489679c4e4774a5ae3079a539fafc30f80ca30d596946951. Every other workflow byte remains exact. Five jobs, Python matrices, dependencies/setup,20-minute product job limit, permissions/triggers, every default test node, full unit order/set and all downstream integration/OAP/governance/help/doctor gates remain unchanged. Clearing quiet addopts changes reporting only; no selector/filter/skip/xfail or splitting. GNU time reports command resources/termination and adds an external parent: record that observation boundary, not identical process ancestry, measured allocation, additive/delta high-water, complete live-tree/cgroup accounting or proof of OOM. A last printed node is localization, not proof that it caused a kill. Missing /usr/bin/time fails loudly; no install, shell pipeline, background process or status-masking wrapper.

The two current docs add a short precise009i record of the previous failure and diagnostic-only behavior. New-head CI remains PENDING at publication. Preserve real baseline NOT_RUN and all currentprincipal/policy/qualifiedencoder/data/rights/operator/parser/publisher/nativeOS/20k/hardware/visual/security/license/mergedICA/MVP/release gates. No product/test/config/dependency/law changes. Program84aceffc, runnerd9f1 and programunit59f093b4 remain byte-exact. Do not modify other lanes, create a worktree/branch/PR, reset/clean/stash/switch or adopt unrelated dirties.

First commit FOUR transcript paths, sole parent exact base7117201: unchanged FINAL order at oap/orders/009-i-unit-exit-diagnostics.md; active009-i plus oneLF; exact Root resolution at oap/reviews/009-i-prior-resolution.json; exact Root index at oap/reviews/009-i-root-records.json. Index source audit/009-i-root-records-FINAL.json is447B SHA2569e5c58e43a210f022f350cf4986fbb91deddd6aca8fc0f8c05b1990a035036b1; its ONE record3286B SHA25681afc95bb9b5320463da5a281720ca0861dce3c18175266f9012e86603b00973. Copy source/targets as specified and verify both. No raw logs or other private lane files in Git. One three-path implementation commit sole parent transcript, then one immutable report-only SELF sole parent implementation: EIGHT round paths total. No intermediate push, force-push or historical report rewrite; preserve unpublished review checkpoints if needed.

## Non-goals

No product fix based on an unproven cause, capacity/resource-limit change, workflow weakening, test rewrite, feature, native/source/model/fixture journey, local fullsuite, new environment, real corpus/credential/service/GPU access, baseline qualification or numeric010 advance. No rerun of oldCI.

## Acceptance criteria

1. Exact current PR/base/normal/order/Root bytes; four-path transcript, three-path implementation, report-only graph, clean unrelated state and immutable historical reports.
2. Exact workflow postimage above; full five-job/matrix/step/test set preserved. Only the two docs change beyond that one run block.
3. STATIC Git/hash/text verification suffices locally. Before implementation commit, place a regular-file request under strategic audit/009-i-check/ containing exact three-path diff and proposed hashes, then await Root independent review. No product invocation is authorized. Root may approve completion from source inspection; do not invent a local YAML/parser check or import older check permission.
4. Concise docs/report accurately distinguish old failedCI, Root104unit evidence and future new-head diagnostics; no current or future green certificate, cause claim, baseline or fullMVP acceptance.
5. After Root exact diff review, finish implementation/report, push ONLY the report head, invoke original normal helper once. Root independently reviews new-head fullCI, every required job/step, diagnostic output and reviews/threads before remediation or acceptance. Missing/skipped/pending/cancelled/failed is not green.

## Verification and negative evidence

Static source preparation only: exact bytes/unique text replacement, allowed-path diff, unchanged source/test/dependency/workflow remainder, transcript/report graph and remote identities. No local format/lint/test/import/collect/setup/native/model/probe. No need to rerun focused104units for a diagnostic-only workflow change. Root owns the pre-implementation regular-file diff gate and later actual current-head CI review. Unexpected dirties, input mismatch or helper failure means preserve evidence and report a regular blocker; never reset or silently retry a signal. No nested agents.

## Documentation

Keep current docs short, without duplicating historical reports. Semantic coding allowance256KiB includes repeated/helper/own verification reads; read only task-relevant sections, record estimates/unknowns honestly. Source hash/stat bytes are separate from model-visible source or dynamic/OS closure. Do not reload whole books/history. Root authors exact order/records; coding owns implementation/Git.

## Runtime and protected resources

No local product execution or setup. Ordinary new-head GitHub-hosted fullCI only after reviewed publication; no new runtime scope beyond the single diagnostic run-block edit. Preserve human Qwen3.8-27B/A100 Q8/xhigh profile/auth and other panes/worktrees. Use qualified ordinary fresh-context startup, then one bounded static goal after actual initial tool reads. Existing helpers own sole readers; no FIFO read/replay/second consumer.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Result PARTIAL whole009. Aim3000–4500B; soft6000B/hard8192B. State exact source/implementation/SELF/PR identities, static actions, previous failed evidence, read-ledger limitations, DHA and remaining gates. No bespoke post-publication receipt or duplicate verification loop: the unmodified respond helper verifies remote report topology/bytes and persists response-send receipt itself. After one report-head push, invoke ONCE `python3 oap/bin/oap.py respond --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --role CODING --identifier 009-i`. An existing response-send receipt means reconcile without replay. ChatOK is not wire delivery. Remain quiescent afterward; no merge/release/deploy.

Strongest counterargument: another fullCI run with logging only consumes time and changes an external parent without fixing the cause. The present log supplies no failed node or traceback; minimal honest localization and command-resource output is a more defensible next step than speculative patches or raised limits. Diagnose the new evidence without equating temporal proximity, exit137 or a successful rerun with causal proof.
