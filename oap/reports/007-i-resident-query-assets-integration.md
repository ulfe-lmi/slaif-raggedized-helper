# OAP Coding Report — 007-i

Identifier: 007-i
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: b982354e117588e5f7a8f8eba157d072ab5507ae
PR main base: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main)
Implementation head SHA: 77ea5b8a3aa9e10ee0c2dfa4cfb7aea9abaade4e
Report publication commit: SELF

## Work and scope

Order 007-i (FINAL, DHA NONE, AMEND_EXISTING_PR) executed exactly in ONE
commit 77ea5b8 (sole parent = round base b982354), 39 files (16 M, 23 A):
the exact Root FINAL order (SHA-256
fd1bcb9905484c47d4a3e0dba34e5dc625a55b97784074436b5157b5320974f5) and
active (`007-i\n`) unchanged; the FOURTEEN sanitized Root records plus the
exact index (oap/reviews/007-i-root-records.json), all SHA-256-verified
against audit/007-i-root-records.json at the strategic root; the FIFTEEN
frozen query/CPU-asset files byte-exact from the two exact report commits
(query 1bb40cc6, CPU assets d75baa51; oap/reviews/007-i-components.json,
170,026 B; every path verified at HEAD for blob + SHA-256 + size); and the
scoped current docs (README.md, STATUS.md, docs/embedding.md,
docs/UNCERTAINTIES.md; TESTING.md with ONLY T16 compressed, T1..T15
byte-unchanged; oap/governance/CONTEXT-BUDGET.md + MANIFEST.json measured
current-doc/hash updates, routine 49,995/50,000 B). No branch merge,
cherry-pick, rebase, reset, stash or clean; no workflow/CI-step/helper/
lock/requirements/worker-profile-README/law/architecture/CRITICAL change;
no copying or use of the private Root H adapter; H never retried or edited.

## Acceptance evidence

1. Exact first transcript + fifteen blobs 170,026 B: order/active bytes
   and all 14 records/index verified before commit; `git show
   77ea5b8:<path>` equals the indexed SHA-256/size for all fifteen files;
   docs changes scoped to the allowed current docs only.
2. Resident query: query_embedding.py (new) admits bounded raw
   Unicode/UTF-8 (<=8192 chars / 32768 strict bytes, nonblank) with no
   prefix/title/normalization/truncation/padding, independent native
   0.21.4 tokenizer IDs (1024 limit), one actually owned CPU worker
   reused across different queries (load-once), immutable normalized
   FP32 result with observed complete execution provenance, content-free
   refusal before exposure. Verified by the committed hostile-input and
   identity refusals plus the composed suite (fake framework; actual
   staged artifacts, native tokenizer and CPU protocol).
3. Shared diagnostic priority: add_note/owner-attribute failures can
   never replace the selected original non-Exception interruption; a new
   cleanup interruption outranks ordinary errors; pending owners retained
   independently of notes/attrs. Verified by the committed hostile-
   diagnostic regressions in the three shared modules' unit suites and
   the separate composition invocations; historical F1/F2 bad-secondary
   witnesses remain historical, not passing proof.
4. Offline CPU wheel: the actual wheel built and installed offline in a
   private bounded prefix contains the exact three unchanged locks under
   _worker_profiles with RECORD/license/entry/source identity; normal and
   src-named prefix imports use the installed CPU profile helper and
   refuse missing/corrupt/symlinked/whole-bundle assets even with a
   matching ambient project/lock (bounded dist-info downgrade guards);
   source-checkout support retained. pyproject adds only the three
   reviewed force-include mappings; dependencies and all locks exact.
5. Complete worker/bridge/execution identities change with the current
   code (source fingerprints re-derived at runtime; no hardcoded old
   fingerprints; no ephemeral plan promoted to durable ID); semantic
   space/definition/native/query policy unchanged; producer/journal
   compatibility re-verified in the full local sweeps.
6. Focused local checks (implementation head, observed): tests/unit full
   sweep 1466 collected all passed exit 0; SEPARATE invocations each in
   its own process, bounded 1 GiB AS/30 s CPU/120 s wall: query
   composition 3 passed, isolated composition 3 passed (1 retained fork
   deprecation warning), CPU worker composition 4 passed (CPUv2 vars),
   actual offline wheel 1 passed — all exit 0; full tests/integration
   637 cases exit 0; ruff check src tests/unit tests/integration "All
   checks passed" (host ruff aborts under RLIMIT_AS <= 2 GiB, so it ran
   wall-bounded without the AS cap; the canonical uncapped CI step
   succeeded); compileall exit 0; OAP scaffold 41 tests OK; check_state
   ACTIVE 007-i (activation-time governance snapshot expected to differ
   from the current manifest after the authorized measured doc updates);
   raggedized --help exit 0; doctor example exit 1 with honest
   MODEL_UNQUALIFIED + SECRET_ABSENT. GitHub CI 43184289399 at 77ea5b8:
   ALL 5 jobs / 78 steps SUCCESS (observed 2026-11-12 ~08:40 UTC).
7. Current docs state the canonical resident-query/CPU packaged resources
   as finite model-free software progress; actual BGE UNRUN/UNQUALIFIED;
   GPU child/plan/parent resources still parallel/unintegrated; H actual
   38 setup/class-import/license-fact truth and the archived random CPU
   toy distinction preserved; H-era host full-unit failure cause remains
   UNRESOLVED (no causality invented, no failure hidden; this round's
   local full unit sweep passed at this head); no security/license/
   current-rights/real-CPU-neural/V100/controller/parity/visual/
   held-out/ICA/full-MVP claim.

## Mock vs real and limitations

All query/isolated/CPU-worker proof substitutes a trusted in-memory fake
framework over actual staged artifacts, actual native tokenizer 0.21.4
and the actual CPU isolation protocol; the wheel test exercises the
ACTUAL offline wheel. No real BGE execution, latency, parity, model
memory or hardware was run; Result is PARTIAL because whole 007 remains
incomplete (actual-model CPU query execution, GPU child/plan/parent
integration, snapshot binding, qualification all still open). The Root
15-file composed review tree (oap/reviews/007-i15-composed-review-tree.
json: 246 focused unit + separate 3/3/4/1 PASS, with the initial Root
invocation errors retained and corrected) is forecast evidence, not
canonical CI/ICA. This report does not certify report-head CI or any
future check.

## Deferred human adjudication

Order Decision: NONE. No consequential candidate is reported; no CRIT
append performed.

## No-merge confirmation

PR 9 remains OPEN on main 11badc7, auto-merge off, no merge/auto-merge/
tag/deploy/release performed, no next objective chosen, no model/
profile/auth change, no new consumer started; whole 007 PARTIAL; Root
alone reviews/accepts/activates next.
