# OAP Coding Report — 007-s

Identifier: 007-s
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: c1bcba4666d184689e6d8cdf47e42ceea3667db9
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: ade6291dca4c2e1a35d3e450bc2fbbccc6fbf9f8
Implementation head SHA: d39b3eae319296dba45b949460fdb40e2a1c5c38
Report publication commit: SELF

## Work and scope

Order 007-s (FINAL, DHA NONE, AMEND_EXISTING_PR) ran transcript-first. Transcript (sole parent = round base R SELF): exact final order (9,635 B, SHA-256 9fa98100f84b7830086f58e49e3f98ec30324333efcdc8a69e3aa293722f43b0), active 007-s+LF, the eighteen exact frozen Root records (69,274 source bytes per oap/reviews/007-s-root-records.json; index 4,895 B, SHA-256 4a7cbbf57386dafc00b0c2e192f7214aa1047ad6f077ee33a6afa689e2bad4a1) copied unchanged with per-file byte/size/SHA-256 identity checks; the format-recovery helper is archived TEXT ONLY and was never executed; no Root bytes edited. Implementation (sole parent = transcript): exactly THREE paths — (1) tests/integration/test_cpu_embedding_worker_composition.py 11,031 B SHA-256 79b98fb99f30751604b5a31640ab5d31a6dce4e7ebb34ed299a348fee9390c97; (2) new docs/parallel/watchdog-proc-disappearance-test.md 840 B SHA-256 3562e4da37e776d8024c58dffdcb8dd905f1b71dd1183f0d368b3d21f8c99d7b — both byte-exact copies from immutable SELF 8b0961736389c0bcd00827e2a48fb31439c99494 / implementation 87be2e8f8558e648790af33201de26536f9f633e per oap/reviews/007-s-watchdog-components.json (11,871 B); (3) ONLY the concise STATUS.md current-S/scoped-evidence paragraph. Behavior: _proc_read catches OSError only, returns None solely for errno ENOENT/ESRCH, every other error propagates; the children/cmdline/exe/stat consumers retain successful-content parsing and worker identity and treat only absent owned /proc reads as disappearance; no arbitrary exception swallow or unknown PID ownership. The paused-parent test keeps its worker ownership, nonempty descendants + worker PIDs, SIGSTOP parent, 5-second watchdog, 8-second pending window and final cleanup assertions. Bounded test-harness continuation only: no production watchdog/timeout/ownership/model/gateway/CI change, no R report rewrite or lenient parser, no manual OK, no replayed FIFO, no Root-only procedure.

## Acceptance evidence

1. TWO copied files byte-exact (size/SHA-256 above); ruff 0.17.4 on the changed test: All checks passed; AST vs round base: only _proc_read and test_proc_read_disappearance_and_errors added, the other three tests AST-identical, and the paused-parent function's sole deltas are the three _proc_read call sites preserving every assertion. Preservation: gateway.py 59,033 B SHA-256 f8a686590e0b91f0f367327733cb7c0b02131ed2fa650de6695e5a9e717ea5bd plus all seven other R component files, worker_profiles, locks, architecture, CRITICAL, TESTING 17,448 B b84fd5c6, governance 49,999/50,000 B, deps and CI byte-exact vs round base (zero protected-path diff).
2. ONE actual process, TWO named nodes; actual collected counts: 2 items, 2 passed in 5.88 s, zero failures/errors, exit 0; resources wall 6.49 s, user 1.21 s, sys 0.24 s, max RSS 140,672 kB. Exact command (repo root; cached .venv/bin/python3.14 = 3.14.4): prlimit --as=1073741824 --cpu=30 timeout 120 env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 SLAIF_CPU_V2_TEST_ROOT=/tmp/raggedized-root-cpython312-portability SLAIF_CPU_V2_TEST_PACKAGES=/tmp/raggedized-root-cpu-v2-portable-485fc687/packages .venv/bin/python3.14 -m pytest tests/integration/test_cpu_embedding_worker_composition.py::test_proc_read_disappearance_and_errors tests/integration/test_cpu_embedding_worker_composition.py::test_watchdog_expires_while_owned_parent_paused -v --basetemp=/tmp/raggedized-s-007-basetemp (private 0700 direct tmp; outer pytest parent CPU30/AS1073741824/wall120, the test's synthetic parent applies its own CPU30/AS1GiB prlimit; the native worker child keeps existing limits and the 5-second watchdog — not an aggregate hard CPU cap). Hash read set (module, doc, four imported src modules, tests/unit/test_cpu_embedding_backend.py, worker_profiles/cpu-v2/uv.lock) SHA-256 identical before/after; borrowed fixture roots: zero files modified in the run window; pre-plan (source/command/env/setup/caps) written before execution. No model imports/inference/downloads/extra fixtures/network; no blind retry, cap raise, skip or timeout/CI weakening; no broad predecessor/parity/native replay.
3. CURRENT sources at publication: implementation head d39b3eae319296dba45b949460fdb40e2a1c5c38, sole parent transcript ade6291dca4c2e1a35d3e450bc2fbbccc6fbf9f8, sole parent round base c1bcba4666d184689e6d8cdf47e42ceea3667db9; PR 9 OPEN/non-draft on oap/007-embedding-pipeline, auto-merge OFF, remote main 11badc7782bed326995d400f5532b63399b91fbd. R distinction preserved: the R report is REJECTED for report format (parenthetical implementation head SHA; Root records under oap/reviews/007-s-prior-*) while current R CI 43315535020 is all 5 jobs / 78 actual steps green.
4. This report validated on actual bytes pre-commit via imported oaplib.metadata and oaplib.commit_id: Implementation head SHA is the bare 40-hex implementation HEAD with no commentary, all commit-ID header fields bare 40-hex (parent/explanation only in body), Report publication commit SELF, at most 8192 B, identity/branch/PR/result correct, no duplicate fields, sole-parent report-only plan.
5. One push of this final report head, the original unmodified strict verify-report, CURRENT all-5-jobs/every-actual-step CI and ONE original normal response are recorded in the separate post-publication receipt; not certified here.

## Verification

Mock/live: the new node is a deterministic injected-read proof (ENOENT/ESRCH to None; EACCES/EPERM/EIO propagate) plus ONE owned synthetic-OS paused-parent proof (fake provider, cached CPUv2 fixture, real sandbox process tree; no real model, GPU, keys or network). Strongest counterargument: a finite synthetic-OS positive plus injected errors does not reproduce arbitrary GitHub /proc races or qualify the production watchdog, neural, hardware or current-rights behavior; actual failure 43311410951 (Product 3.12 integration step 17 ProcessLookupError) stays classified as an intermittent observation/test-harness race; Root/opposite archived proofs are context, not new execution. Current CI for this head: PENDING/UNOBSERVED at publication.

## Documentation impact

ONLY the concise STATUS.md current-S paragraph plus the exact copied API doc (docs/parallel/watchdog-proc-disappearance-test.md). No TESTING/law/governance/README edit; R failed-format vs current-green-CI distinction and the whole-007/BGE UNRUN/UNQUALIFIED gates preserved.

## DHA and boundaries

Order Decision: NONE; no CRIT append; no candidate. Preserved: human Qwen3.8/A100 profile/auth, runtime and helper bytes, all prior immutable orders/reports/Root records, borrowed fixture roots, reference gateway repo. No merge/reset/stash/clean/switch/rebase/cherry-pick/force-push; no nested agents, installs, downloads, credentials, SSH, gateway/model/GPU/service change or network exposure; no 008 advance, tag, deploy or release.

## Limitations and remaining work

PARTIAL: report-head CI PENDING/UNOBSERVED at publication (observed separately post-push); the repair is test-harness observation only, not production watchdog qualification; whole 007 and full MVP remain PARTIAL with actual BGE UNRUN/UNQUALIFIED; no real BGE execution, FP16 qualification, snapshot publication or license clearance; numeric 008, full-007 source coverage and ICA remain open.
