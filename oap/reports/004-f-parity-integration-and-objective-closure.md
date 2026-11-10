# OAP Coding Report — 004-f

Identifier: 004-f
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 6
Branch: oap/004-qualification-harness
Base branch: main
Implementation head SHA: d34e31b334848501c2ef0e60c165edae3d3c7fa6
Report publication commit: SELF

## Work and scope

Executed oap/orders/004-f-parity-integration-and-objective-closure.md
(Status FINAL, DHA Decision: NONE, live target authorization: NONE,
PR mode AMEND_EXISTING_PR, base commit
2bc320ff9e66c874f07da061218f2ff52e3420a9) on the existing PR 6,
integrating the independently reviewed parallel embedding/rerank
parity, shared safe file I/O, module/installed-CLI routing and the
full fourteen-gate prerequisite projection, and reconciling all
original 004 software criteria while preserving real qualification
NOT_RUN with exact later implementation/access prerequisites. No
hardware/model/quality/license pass.

Round start reconciled against GitHub: unique OPEN PR 6, head
oap/004-qualification-harness at the verified canonical 004-e
immutable report-only commit 6df26c82df26c1f946f2fd21792441d874b43acf
(sole implementation parent
651635c22e76fef11adbe3f440cf4c5593dfefb0, report SHA-256
7fb36653df1ce9b9bf571ed73edfe02226990f0d07e0f32bef6e08da2024bf6e),
base main 2bc320ff9e66c874f07da061218f2ff52e3420a9, local == remote,
no auto-merge, mergeable CLEAN. The sole control OK was consumed by
the sole external wrapper and was never reread or replayed. Root
review oap/parallel/parity-router/review.json SHA-256
740baea8ac1b05906175a631ca03efdaed262d6026081c450a2da22a02813a33
(ACCEPT_LOCAL_CANDIDATE_FOR_CANONICAL_INTEGRATION) and the parent
lane reviews (embedding-c 86916edc94b907e38a6689e02cb4da3f5e0e756b5eae6218b10d917dcc2476eb,
rerank-b 1c682f14a039568d2cac7d6ced2b322e9c12270592690f8808a78f6d159db42c,
parity-io-b 986e9536d7d6bb6dfe25adb36fd7f05adb2c65c81502799115b155840ea5da4d,
cli-gates-b dd0919e600c53ce910d227a4ba9b8e603cf2d62ffe506c925dae25b7b8dad8d0)
re-verified against disk; approved candidate tip
oap/parallel-004-parity-router at
956eed068475033cf479c845516ea8710cd2e752 re-verified; the root clean
automatic merge forecast (git merge-tree of canonical 6df26c8 with
the tip) reproduced exactly, tree
56aec4368644929d145eb3e8c18314a818a292d1, no conflicts.

Commits pushed on the branch before this report, in order:

1. 405b2a31364297c3f8c95f6dbac1409d2feeee95 (parent 6df26c8) — the
   strategic round-start bytes committed byte-for-byte unchanged:
   oap/orders/004-f-parity-integration-and-objective-closure.md,
   oap/reviews/004-e-review.json (SHA-256
   8da7c23a3f14aa8316c483b9fc77716c88fe728c6b3bbda6c34cf5fce06abcae,
   records ACCEPT_RESOURCE_CORRECTION_CONTINUE_SAME_PR_004_f) and
   oap/active exactly `004-f\n` from 004-e. Architecture
   4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
   and governance manifest 6f30a6b8d105de353905b2d6a4a1cb0b807a18e10af8565ab8289f278ccea1a9
   (the activation-time values recorded in the order) verified.

2. c73451de036c5009425f7578deaf520ed5942e89 (parents 405b2a3 and
   956eed0) — the ONE authorized local --no-ff integration merge of
   the root-reviewed candidate tip into the existing PR 6 branch
   under the human parallel mandate. Clean merge, no conflicts, no
   resolution edits: the merged tree equals the root clean automatic
   forecast tree 56aec4368644929d145eb3e8c18314a818a292d1 plus the
   three 004-f round-start files. Preserved: all original candidate
   lane histories and provenance (oap/parallel orders/reports for
   PAR-004-EMBED-A/-B/-C, PAR-004-PARITY-IO-A/-B, PAR-004-RERANK-A/-B,
   PAR-004-CLI-GATES-A/-B, PAR-004-ROUTER-A; docs/parallel/parity-
   cli-and-gates.md and parity-router.md), the accepted 004-e
   resource/ledger/cleanup/strict versions (resources.py, runner.py,
   cli.py resource paths, 004-e order, 004-d review and resource
   tests byte-identical to the canonical 004-e head), and the
   strategic order/active bytes. This is NOT a GitHub
   PR/default-main merge.

3. d34e31b334848501c2ef0e60c165edae3d3c7fa6 (parent c73451d) —
   canonical documentation reconciliation (see Documentation
   impact): actual fixed GPU reason vocabulary, final observation-
   window / CPU-endpoint / completion-wall semantics, conservative
   combined byte-pool reservations, current prerequisite references
   replacing obsolete 004-b references, the gate-projection
   available-analysis/partial-instrumentation distinction, compact
   TESTING T10, and measured context/manifest updates.

## Acceptance evidence

Numbered against the order's acceptance criteria 1-6.

1. Canonical expected head/branch/worktree and the exact Root-reviewed
   candidate tip were rechecked before any mutation (PR 6 OPEN at
   canonical 6df26c8; branch oap/004-qualification-harness; worktree
   clean apart from the strategic round-start bytes; tip
   956eed068475033cf479c845516ea8710cd2e752 on
   oap/parallel-004-parity-router). ONLY that tip was merged, with
   --no-ff, inside the existing PR branch; the merge was clean (no
   conflicts to resolve) and the merged tree equals the root
   forecast tree plus the round-start bytes. All approved source/
   report/order identities are preserved (candidate lane commits
   624b992b/baaea84c/d4f09834/a9bc1d1a/4978ca7b/956eed0 remain in PR
   history; the accepted 004-e resource/ledger/cleanup/strict
   versions are byte-identical to the canonical 004-e head); the
   strategic order/active/prior-review bytes are committed
   unchanged.

2. The installed `raggedized parity embedding|rerank` and the module
   `python -m slaif_raggedized_helper.qualification.parity_cli`
   commands execute the accepted bounded pure analyzers through the
   ONE shared safe I/O layer (parity_io read_document/preflight_
   output/run_export; the 12-line canonical cli.py routing diff
   delegates the `parity` prefix without touching resource handlers
   or the standard parser/main path). Raw file provenance (exact
   input SHA-256 and byte count) and normalized input bindings
   (embedding input_fingerprint; rerank input_binding) are preserved
   in the evidence; strict safe refusals use fixed input-free
   reasons; post-work export retains the analyzer result as
   evidence (exit 3) instead of dropping it. No repeated math/
   client/parser stack, no redundant approval flag (required
   --input/--output are the opt-in), no default model/network/I-O:
   help and import perform zero work, and no transport/model
   accounting is implied.

3. Embedding identity/execution separation (definition space
   fingerprint distinct from execution fingerprints; declared
   CPU-FP32 reference vs GPU-FP16 candidate; storage provenance
   unavailable for supplied vectors, FP32 storage a target not an
   observation), durable row alignment (corpus IDs and both
   digests must bind across corpora), raw stored-vector dot ranking
   (mixed CPU query vectors versus the supplied corpora;
   descending score then ascending durable ID deterministic ties)
   versus paired cosine with L2 norm deviations, explicit
   requested_k/effective_k, gold denominators over explicitly
   supplied relevant IDs and unavailable facts (null recall, null
   gold denominator), and the rerank exact pair/query/passage/
   digest binding with signed relative (candidate minus reference)
   scores all match the actual reviewed code; rerank scores remain
   SUPPLIED_UNVERIFIED supplied analysis, never executed evidence.
   Verified by reading the integrated modules against the lane
   reviews and by the parity unit suites (550 unit total) plus the
   direct end-to-end runs recorded under Verification.

4. All fourteen architecture section 23.2 gates carry the exact
   actual current entrypoint or precise missing implementation/
   access prerequisites (no obsolete 004-b references): GATEWAY-01/
   GATEWAY-03/DIRECT-01 name the bounded text trial entrypoint
   `raggedized qualification run` with authorization prerequisites;
   GATEWAY-02 016/qualified vision/authorized target; V100-MEM-01
   012+015/authorized GPU/model processes; V100-MEM-02 015/context
   controls/authorized GPU; RERANK-01 012/pair-batch controls/
   authorized GPU/measured experiments; EMBED-01 007/real serving
   CPU; EMBED-02 007/authorized CPU-GPU execution; ONLINE-01 014+
   019/authorized target; ONLINE-02 014/concurrency implementation;
   OPS-01 007/010+017; OPS-02 015/ownership journal; LICENSE-01 018
   (certifi MPL-2.0 exception not granted). Available analysis
   (`parity_cli embedding`/`rerank`, supplied values only) and
   partial local instrumentation (`resource diagnose`, own-process/
   devhost only) are separate projection fields and are distinct
   from full experiments, which neither executes. Every real status
   stays NOT_RUN; unsupported trial controls still refuse with the
   current named prerequisites (spec.py: seed-variation
   implementation, concurrency implementation for ONLINE-02, 007/012
   pipeline controls, context controls, 012 pair worker). The
   generated projection matches: `raggedized qualification gates`
   output is byte-equal to the committed
   docs/benchmarks/qualification-gates.json (SHA-256
   0619c277d36edd5a9aeb431b89677130ec7d523e31a9881b7e474435a143832d),
   and the unit test binding the committed bytes to the canonical
   rendering passes.

5. The canonical docs now match the final E semantics: the protocol
   describes the observation window (ResourceSeries.duration_
   seconds: start to admitted CPU endpoint, else report assembly,
   intersected with the work window; never cleanup elapsed), the
   CPU endpoint (cpu wall_seconds can exceed the window when the
   probe finishes after cutoff; the observation window when no
   endpoint is admitted), and the completion wall (collector
   wall_seconds through report assembly including cleanup/
   finalization, can exceed the work-window bound); the actual
   fixed unavailable/error vocabulary (tool_absent/no_devices/
   query_budget_exhausted and spawn_failed/timeout/stdout_oversize/
   stderr_oversize/query_failed/malformed_output/
   contradictory_values) replaces the E report's shorthand reason
   names in the current protocol/CLI docs; the conservative
   combined byte pool (own-process bytes_read plus device-pipe
   device_query_bytes_read; full status-read cap reserved per
   admitted sample; both pipe caps plus one lookahead byte per pipe
   reserved per device query; reservations never reported as actual
   reads) is documented. The immutable 004-e report is NOT
   rewritten. Source/model/hardware/vision/domain quality/license/
   019/ICA/full-MVP gates remain open in docs and projection.

6. Meaningful installed-CLI/owned-file end-to-end and the original
   trial/resource/input/ledger regression negatives ran on the
   combined source: 550 unit + 340 integration = 890 product tests
   (484 + 318 baseline preserved, zero removed; the parity
   integration suites include the installed-CLI exit-code matrix,
   post-work export failure retaining bounded evidence, and the
   shared-I/O crash/negative cases) plus 41 OAP scaffold tests, all
   pass locally; required product/OAP/lint/governance pass (ruff
   clean, compileall clean, check_state exit 0); implementation-head
   CI all five jobs SUCCESS. No skipped/missing/pending is claimed
   as success; suites were not rerun merely for counts. No real
   trial was executed: all real trial blockers are reported
   UNRUN/NOT_RUN (live target authorization NONE), never simulated
   passes. The whole original 004 software scope (runner, evidence
   contracts, bounded spec input, telemetry, parity, gates) is now
   integrated on the canonical branch, but terminal acceptance
   (real qualification) is strategy's, not this round's.

## Verification

Local evidence on Python 3.14 (uv run --isolated --locked --python
3.14) at implementation head
d34e31b334848501c2ef0e60c165edae3d3c7fa6:

- ruff check src tests/unit tests/integration: all checks passed.
- python -m compileall -q src tests/unit tests/integration: clean.
- pytest tests/unit -q: 550 passed (484 baseline + 66 new parity
  unit; zero removed).
- pytest tests/integration -q: 340 passed (318 baseline + 22 new
  parity integration; zero removed). Product total: 890.
- python3 -m unittest discover -s tests/oap: OK (41 scaffold).
- oap/bin/check_state.py --repo-root .: exit 0, active 004-f,
  declared context 49996/50000 UTF-8 bytes, critical {}.
- Direct installed-CLI end-to-end on owned disposable files
  (scratch /tmp, synthetic digests/vectors only):
  `raggedized parity embedding --input ... --output ...` exit 0
  (evidence: SUPPLIED_UNVERIFIED, NOT_QUALIFIED,
  INCOMPLETE_UNVERIFIED space identity, paired cosine/L2
  deviations, raw dot scores/ranks, requested_k/effective_k, gold
  denominator 1, input SHA-256/byte provenance, real_qualification
  NOT_RUN); `python -m
  slaif_raggedized_helper.qualification.parity_cli rerank ...`
  exit 0 (input_binding, signed deltas, requested/effective top_k,
  criteria_passed, gold_recall null, SUPPLIED_UNVERIFIED, NOT_RUN);
  refusal negatives exit 2 with the fixed safe message and no
  input echo (unknown field, missing input file, missing
  --output argument, output into nonexistent directory);
  `raggedized qualification gates` output byte-equal to the
  committed projection document.
- Implementation-head CI: run 42918833573 on
  d34e31b334848501c2ef0e60c165edae3d3c7fa6 — all five jobs SUCCESS
  (OAP tests Python 3.12/3.13/3.14; Product tests Python 3.12
  3m8s / Python 3.14 3m32s), observed before this report. No
  claim is made about this report's future push or CI; a separate
  post-publication receipt verifies those facts.
- Mock/live distinction: synthetic/offline only — owned disposable
  fixtures and scratch files, deterministic supplied values; no
  model loads, no network, no GPU, no corpus; devhost is
  nvidia-smi-less so GPU facts stay an honest unavailable; live
  target authorization NONE; all real trials NOT_RUN; no real
  host/device metadata or secrets in any committed file.

## Documentation impact

- d34e31b: docs/benchmarks/qualification-protocol.md (executed-
  software intro and 004 replan section updated to the actual slice
  history; spec table seed/concurrency prerequisites; actual fixed
  GPU reason vocabulary; observation-window / CPU-endpoint /
  completion-wall time-field semantics; conservative combined byte-
  pool reservations; gate-projection bullet with current
  prerequisites 007/010/012/014/015/016/017/018/019 and the
  available-analysis versus partial-instrumentation distinction;
  stale "(this slice)" claims removed); TESTING.md T10 compact
  parity entry; oap/governance/CONTEXT-BUDGET.md measured routine
  49996/50000 bytes (TESTING.md 17445); oap/governance/MANIFEST.json
  hashes updated for TESTING.md and CONTEXT-BUDGET.md with every
  other manifest entry re-verified against disk. Candidate-
  provenance docs (docs/parallel/parity-cli-and-gates.md,
  parity-router.md) and the generated projection arrived with the
  merge unchanged.

## DHA and boundaries

- DHA Decision: NONE (per the order). No CRITICAL append; the
  critical table is empty (check_state critical {} on the
  implementation head).
- Strategic round-start bytes preserved byte-for-byte: the order,
  oap/reviews/004-e-review.json (SHA-256 8da7c23a3f14aa8316c483b9fc77716c88fe728c6b3bbda6c34cf5fce06abcae,
  re-verified) and oap/active exactly `004-f\n`; the immutable
  004-e report commit 6df26c82df26c1f946f2fd21792441d874b43acf is
  unchanged and its review (ACCEPT_RESOURCE_CORRECTION_CONTINUE_
  SAME_PR_004_f) is the activation basis.
- Parallel mandate: the human-authorized, Root-reviewed LOCAL
  candidate integration only — parity-router review
  ACCEPT_LOCAL_CANDIDATE_FOR_CANONICAL_INTEGRATION (SHA-256
  740baea8ac1b05906175a631ca03efdaed262d6026081c450a2da22a02813a33,
  re-verified) with parent lane reviews re-verified, and ONLY the
  reviewed local tip 956eed068475033cf479c845516ea8710cd2e752
  merged with --no-ff inside the existing PR branch, preserving
  candidate implementation/report provenance. It is NOT a GitHub
  PR/default-main merge; no release or deployment.
- No merge of PR 6 to main performed (PR 6 remains OPEN, no
  auto-merge); no next work chosen; no live target/model/GPU/
  corpus work (live authorization NONE, all real trials NOT_RUN,
  LICENSE-01 open); no model/profile/auth/runtime-policy change;
  no secrets in Git.

## Limitations and remaining work

- The parity-router review records that an additional peer router
  review was still active at preparation; Root will reconcile any
  new concrete finding in this scope. Nothing here assumes that
  peer's PASS.
- This round is the software integration slice, not whole-004
  acceptance: no real gate pass, no model/hardware/quality/vision/
  license evidence; source/model/hardware/vision/domain quality/
  license/019/ICA/full-MVP gates remain open; all real trials
  NOT_RUN. Strategy owns the independent whole-004 review, report-
  head CI acceptance, any qualifying protected PR merge/main CI/
  terminal resolution, and canonical 005 activation. No 005/006
  candidate branch was merged.
- Supplied-value parity evidence binds supplied declarations only;
  it does not attest execution, model artifacts or source
  authenticity. Storage provenance for generic supplied vectors is
  unavailable. Export is neither atomic nor durable by design
  (documented).
- No merge performed; no early 005 activation; no post-response CI
  polling or readers.
