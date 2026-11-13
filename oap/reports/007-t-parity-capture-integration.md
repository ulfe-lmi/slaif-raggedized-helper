# OAP Coding Report — 007-t

Identifier: 007-t
Result: BLOCKED
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 1b38443f36ae170a4ee816d392e0294ce8fc4a5f
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 9403c45b2272c5d24fd0e8b3cc3d2e0d3677dcd7
Implementation head SHA: cf7479ee551e01803f7e2e6a8823bc61b3f1fe23
Report publication commit: SELF

## Work and scope

Order 007-t (FINAL, DHA NONE) ran transcript-first. Transcript (sole parent = round base): exact final order (12,623 B f98150a6e6fc...), active 007-t+LF, and the ELEVEN frozen Root records (110,669 source bytes per oap/reviews/007-t-root-records.json; index 3,008 B c47c90dc2363712ca00d5c795465a76e813be242c930728f353cfe742e422ebe) copied byte-exact with per-file byte/size/SHA-256 identity checks; no Root bytes edited. Implementation (sole parent = transcript): exactly SIX paths — five NEW files copied byte-exact from immutable SELF 29b06100ba00708687a427f4b1dbadfaeca9b97f per oap/reviews/007-t-capture-components.json (f1f554ea..., 69,098 B): src/slaif_raggedized_helper/qualification/embedding_capture.py 26,978 B b3ffad426d08e876a18bef0ac5faae7ea758ff9bead0aaa0207c863f6efb0019; tests/unit/test_embedding_capture.py 17,818 B a674177f7fdba1a08f08cc96300f3ae14b1f21440266eb473399cc61bd5359c4; tests/integration/test_embedding_capture_composition.py 12,294 B dfc9a8c37be11d2af966780f0c70ba98bb3e4cc8de3e8d5762b5a6ee36325425; docs/parallel/embedding-parity-capture-api.md 2,343 B a5df0bae83b720aa51384049ecb2922f1d147186984f0af9e64f2bb00abb776f; docs/parallel/embedding-parity-capture-design.md 9,665 B 2d4561400aeb9a53989d98cbdca3fb4d7c4ec5e085b13a915fe5f836db1289b4; plus ONLY the concise STATUS.md current-T paragraph. Added behavior: the same-source CPU/GPU/query execution DATA capture primitive and its SUPPLIED_UNVERIFIED/NOT_QUALIFIED analyzer adapter (contracts: the two copied design/API docs). Bounded software continuation: no production policy/gateway/CI/dependency change, no merge, no 008.

## Acceptance evidence

1. Five copied files byte-exact (sizes/SHA-256 above; re-verified against source blobs after copy); exactly six implementation paths. Transcript 14 paths byte-verified pre-commit. Preservation: model_clients/gateway.py 59,033 B f8a686590e0b91f0f367327733cb7c0b02131ed2fa650de6695e5a9e717ea5bd and all other R/S component files, worker_profiles, locks, architecture, CRITICAL, TESTING 17,448 B b84fd5c6..., governance manifest 24cec232... at 49,999/50,000 B, deps and CI byte-exact vs round base (base-vs-tree diff = the 14 ordered transcript paths only).
2. ONE local source-only pytest process (cached .venv/bin/python3.14 = 3.14.4; PYTHONPATH unset; PYTHONDONTWRITEBYTECODE=1; five thread caps 1; outer prlimit --as=1073741824 --cpu=30 timeout 120; fresh 0700 basetemp): tests/unit/test_embedding_capture.py collected 38 items (order forecast 38), 38 passed in 0.92 s, exit 0; wall 1.65 s, max RSS 164,672 kB. ONE separate cached synthetic process under the same caps with the order's exact seven SLAIF_* fixture env vars executed ONLY the two named nodes (full literal command/env in pre-plan): ::test_actual_bad_gpu_root_refuses_before_cpu_entry and ::test_actual_epoch_revocation_refuses_before_cpu_forward in tests/integration/test_embedding_capture_composition.py — collected 2: bad_gpu_root PASSED, epoch_revocation FAILED (1 failed, 1 passed in 3.93 s, exit 1) (wall 4.67 s, user 2.60 s, sys 0.33 s, max RSS 167,152 kB). Failure mode: gpu_embedding_producer.ProducerRefused (GPU domain) from the _build_plans catch-all (embedding_capture.py:368) before any CPU producer entry; the node expects cpu_embedding_producer.ProducerRefused at the CPU before_encode authorization; the wrapped base exception is masked by design (attribution: GPU launch _prepare startup, GPU plan build or _compare_plans refusal). Per order: raw failure preserved, STOP further actual processes, no blind retry, no cap raise.
3. Focused ruff 0.17.4 on the changed code/test paths: All checks passed; compileall clean; 5/5 exact-copy checks OK. Default collection with the CI-provided fixture env recognizes 38 unit + 4 integration items of the two new modules (without fixture env, collection fails transitively via a pre-existing base module reading SLAIF_CPU_V2_TEST_PACKAGES at import — pre-existing pattern, CI always provides the vars; no PYTHONPATH workaround). check_state ACTIVE 007-t exit 0 (manifest 24cec232..., 49,999 B); OAP scaffold 41 tests OK; raggedized --help exit 0.
4. This report validated on actual bytes pre-commit via imported oaplib.metadata and oaplib.commit_id: Implementation head SHA bare 40-hex with no commentary, all commit-ID header fields bare 40-hex except SELF, no duplicate fields, at most 8,192 B, identity/branch/PR/result correct, sole-parent report-only plan.
5. CURRENT sources at publication: implementation head cf7479ee551e01803f7e2e6a8823bc61b3f1fe23, sole parent transcript 9403c45b2272c5d24fd0e8b3cc3d2e0d3677dcd7, whose sole parent is round base 1b38443f36ae170a4ee816d392e0294ce8fc4a5f; PR 9 OPEN/non-draft, auto-merge OFF, remote main 11badc7782bed326995d400f5532b63399b91fbd. One push of this final report head; original strict verify-report, CURRENT report-head CI (required gate: both Product jobs normally collect/execute the entire combined driver) and ONE original normal response are recorded in the separate post-publication receipt, not certified here.

## Verification

Mock/live: all local evidence synthetic/offline — fake providers, cached fixture roots, isolated sandbox processes; no real Torch/model/GPU/device calls, installs/downloads/network. Strongest counterargument: static fit (77 modules) reports GPU-side production modules unchanged between candidate lineage and current base (only gateway R fix and CPU worker test differ; FAKE literal AST-identical); the borrowed GPU fixture lock matches current worker_profiles/gpu/uv.lock (d3f47d3d...); Root and the opposite peer passed this node on candidate base bac11bee with their own approved fixture pairs (7.329 s / 7.175 s proof wall); this round's GPU runtime root (uv cpython-3.12.15) differs from the portable 3.12 root used by prior local GPU runs — so the cause is a local fixture/runtime-environment difference or a current-base interaction invisible to static fit; only the current full report CI or a Root revised decision resolves it. Synthetic success cannot establish neural FP16, hardware or current-rights qualification. Current CI for this head: PENDING/UNOBSERVED at publication.

## Documentation impact

ONLY the concise STATUS.md current-T paragraph plus the five exact copied component files including API/design. No TESTING/law/governance/README edit; capture NOT_QUALIFIED and whole-007/BGE UNRUN/UNQUALIFIED gates preserved; R failed-format and S scoped-acceptance distinctions preserved.

## DHA and boundaries

Order Decision: NONE; no CRIT append; no candidate. Preserved: human Qwen3.8-27b/A100 profile/auth, runtime and helper bytes, prior immutable orders/reports/Root records, borrowed fixture roots (zero files modified in the run window), reference gateway repo. No merge/reset/stash/clean/switch/rebase/cherry-pick/force-push; no nested agents, installs, downloads, credentials, SSH, gateway/model/GPU/service change, network exposure, 008 advance, tag, deploy or release.

## Limitations and remaining work

BLOCKED on Root's revised decision for the failed scoped node: (a) epoch-revocation integration node failed locally as described (raw outputs and pre-plan preserved under /tmp/raggedized-t-007-*); (b) the required current full report CI (both Product jobs; entire combined driver including test_actual_synthetic_capture_and_reuse) is PENDING/UNOBSERVED at publication — terminal state recorded post-publication; terminal red preserves head/run/jobs/failed steps/logs with Root notification, no out-of-scope patch. Whole 007 and full MVP remain open; actual BGE UNRUN/UNQUALIFIED; no real model execution, FP16 qualification, snapshot publication or license clearance; 008 advance, full-007 source coverage and ICA remain open.
