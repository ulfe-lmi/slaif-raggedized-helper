# OAP Coding Report — 006-a

Identifier: 006-a
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 8
Branch: oap/006-native-extraction-and-chunking
Base branch: main
Base commit: 4977186d3ddbd2259f78590b29c0364fe26eb1fb
Implementation head SHA: e57820e13993860f86d026531dd0ef6d223f0f60
Report publication commit: SELF

## Work and scope

Order oap/orders/006-a-native-extraction.md (Status FINAL, Decision NONE) on
the accepted 005 record/store foundation (PR 7 merged to main as 4977186).
Branch oap/006-native-extraction-and-chunking created from verified main
4977186d3ddbd2259f78590b29c0364fe26eb1fb (remote ref independently checked;
PR 7 merge commit 4977186 at 2026-11-11T15:05:18Z; no other open objective
PR). Commits pushed before this report:

- 32ab979e (round start): strategic bytes byte-for-byte unchanged — order
  006-a, active 006-a, oap/reviews/005-b-review.json (SHA256
  1aae55206bd1d8c786037bb7db5022a48d5bbcecb2bc008fb5824f8014b73219) and
  oap/reviews/005-resolution.json (SHA256
  3ffbac86344d2ee47422cda69c4659716d8eeace7d7a53fcc2b9147fa1fba754).
- 51046a8: local --no-ff merge of the accepted PDF-test-setup candidate tip
  be40286eeafe810071961789aa7d80d2fac847d5 (corrected PDF-D tip
  eb80a7bc84fbf74f46882030a3ce277852e18bf2; parser/worker blobs
  01d18381895ad539051e9fe6f98119c31623f3f1 and
  652fcf664cb6de017a9ed4d13353b0a365031be0, both present in the merged tree;
  plus implementation 33d77b6841bc22448095c791fdd9e8b9a37fa3ed reproducible
  development PDF test setup). Forecast with git merge-tree against the
  actual parent: clean, forecast tree a57cec62b76b0e246030dc7f2b091cd9cd249f4e
  equals the actual merged tree.
- Literal line merge step (ordered tip e84469f78b82fc5cd41110289bfa7446793ca034):
  `git merge --no-ff` reported "Already up to date" (exit 0) and created no
  new commits because e84469f is a strict ancestor of the first merged tip
  be40286; its complete history (implementation d56515044bb581915b20fbe661291d5a635a11d2,
  report e84469f, provenance merge 73635fd) is retained byte-for-byte in this
  branch. No reset/clean/stash/cherry-pick; provenance preserved.
- e0d7774: local --no-ff merge of the accepted structured text candidate tip
  7a0caf1a3c51427de33fa7140ec01bc24ca81d13 (implementation
  2951eeee9a617bfe6a938adf7fb55fcf68b7f080; merge base b9d5cf6, the old
  PDF-A ancestor that is not accepted PDF code — the corrected PDF-D graph
  from be40286 remains authoritative). Forecast clean; forecast tree
  570faf556e35318e9db47e13ac320998317f163d equals the actual merged tree.
- 667778d: implementation — new combined integration test, CI wiring,
  docs/ingestion.md, README/STATUS/UNCERTAINTIES/TESTING (T13), governance
  measurements (routine context 44046 -> 46521/50000; MANIFEST re-hashed for
  TESTING.md and CONTEXT-BUDGET.md). No candidate code change was required:
  the three accepted tips passed the combined journey as-is.
- e57820e: CI qualification repair (see acceptance 4) — literal
  NAME=value GITHUB_ENV binding for PDF_TEST_PACKAGES and pipefail for the
  helper invocation.

Allowed paths only: one new integration test, .github/workflows/oap.yml
(solely the required reproducible native PDF development tests),
docs/ingestion.md, README/STATUS/UNCERTAINTIES/TESTING and affected
context/manifest measurements. No dependency/lock/runtime-model graph or
architecture/law/helper/prompt change; every other MANIFEST-listed file is
byte-identical (check_state verify_governance passes).

## Acceptance evidence

1. Combined manifest -> OriginalStore -> native line/structure/PDF adapters
   -> provenance.Registry: tests/integration/test_extraction_combined.py —
   two logical documents sharing bytes with distinct corpus/labels/
   redistribution_rights/version produce distinct revisions over one
   verified 0600 blob with distinct Scope bindings; a metadata correction
   publishes a new revision reusing the blob with the prior revision intact;
   literal line blocks concatenate to the exact decoded original with
   line:N anchors; structural blocks tile the decoded original with
   contiguous half-open code-point coverage (CRLF, astral U+10348 and
   combining U+0301 preserved); headings, paragraphs, list procedures,
   fenced code and pipe table header+rows are recognized per the documented
   bounded subset with explicit uncertainty; the mixed native/raster PDF
   yields native blocks with actual geometry plus visual_needed page
   status and partial_visual_needed result; all three extraction
   dependencies bind into one Registry and chunks from each adapter bind to
   their scopes while a cross-extraction forged fragment is refused.
   No full CommonMark, OCR, rasterization or semantic reconstruction claim
   is made (docs/ingestion.md).
2. Fixed trusted isolated PDF worker (merged as-is from the corrected PDF-D
   tip): bounded verified original read before the parser (max_bytes cap
   before any blob read), read-only configured runtime/packages, no
   network/home/GPU/credentials (canary witness test), bounded CPU/memory/
   pipe/time (prlimit 256 MiB/1 CPU s/32 fds/2 MiB; parent 2 s cooperative
   deadline; output cap+1 byte) and owned-child cleanup; nested forms keep
   native text with actual character boxes without duplication; raster and
   vector material, including mixed pages and nested forms, explicitly
   require visual work and cannot report complete-looking extraction;
   object-count/blocks/geometry correlations and forged worker identity are
   refused (merged suites, unmodified).
3. Combined tests with shared-byte distinct rights/ACL/version, metadata
   revision, native literal and structural coverage, source immutability
   (0600 verified blob, exact byte round-trip, corrupted-blob refusal) and
   malformed/oversized/wrong-hash/unsupported-media refusal (new file); all
   existing parser/source/record/qualification regressions retained
   unchanged — collection-only counts grew 588+354 -> 614 unit / 383
   integration with zero removed tests. The source byte-integrity pass, the
   parse limits and the cooperative parent/worker deadlines are separate
   mechanisms and none is claimed as a hard filesystem-interrupt guarantee.
4. Required PDF tests fail missing/incompatible backend or isolation
   instead of skipping: locally without PDF_TEST_RUNTIME/PDF_TEST_PACKAGES
   the suite exits 1 with 2 fixture errors and zero skips (verified).
   Product CI (both Python 3.12/3.14 legs) now: installs and verifies
   bubblewrap + prlimit on the disposable GitHub-hosted runner, runs an
   unprivileged namespace smoke mirroring the worker unshare set, stubs
   /usr/lib64 when the merged-usr host lacks it, provisions the standalone
   CPython 3.12 worker runtime (uv-managed base) and a NEW private pinned
   SHA-256-verified backend via the reviewed helper, and binds
   PDF_TEST_RUNTIME/PDF_TEST_PACKAGES as literal GITHUB_ENV entries (never
   sourcing or evaling helper output; helper exit preserved through tee
   with pipefail). Actual CI qualification: first run 43052087816 (head
   667778d) failed exactly as the defective wiring predicted — backend
   provisioned on both legs but PDF_TEST_PACKAGES unset because the helper's
   shell-oriented `export NAME=value` lines are not valid GITHUB_ENV
   entries; both product legs failed at the integration step with the
   explicit fixture RuntimeError (job logs 130631661952/130631662533; no
   skip, no unsandboxed fallback). After the e57820e repair, run
   43053529368 executed the full unchanged required suites on the actual
   provisioned backend: product legs 130636794584 (3.12) and
   130636795345 (3.14) show 383 integration tests, all passed, zero
   skipped, with both PDF_TEST_* entries present in every step environment.
   No continue-on-error, exclusions or weakened assertions.
5. Whole combined unit and integration runs separately; OAP/lint/
   governance/installed-source/qualification routes pass: locally at the
   implementation head — uv sync --locked ok; pytest tests/unit exit 0
   (614); pytest tests/integration exit 0 (383, real isolated worker);
   unittest tests/oap "Ran 41 tests OK"; check_state exit 0 (state ACTIVE
   006-a; declared 46521/50000; critical {}); ruff check src tests/unit
   tests/integration "All checks passed!"; compileall clean. Real process
   exits recorded; counts collection-only. Actual CI run 43053529368 on
   implementation head e57820e: all five required jobs SUCCESS — OAP tests
   3.12/3.13/3.14 (130636795308/130636795144/130636795077) and Product
   tests 3.12/3.14 (130636794584/130636795345), observed 2026-11-11
   16:04-16:05Z. Routine governance 46521/50000 bytes; detailed historical
   qualification-testing.md preserved verbatim; exact model tokens
   UNMEASURED; no model-token or quality claim.

## Verification

Commands (implementation head e57820e, devhost Ubuntu 26.04, uv 0.12.5,
local worker runtime CPython 3.12.15, parent pytest 3.14):

- git fetch origin; rev-parse origin/main == 4977186d3ddbd2259f78590b29c0364fe26eb1fb;
  gh pr list: PR 7 MERGED, no other open objective PR.
- git merge-tree --write-tree (per merge, actual parent): clean forecasts
  a57cec62 / 570faf55; actual merged trees equal.
- git rev-parse HEAD:src/slaif_raggedized_helper/pdf_extraction.py ==
  01d18381895ad539051e9fe6f98119c31623f3f1; pdf_worker.py ==
  652fcf664cb6de017a9ed4d13353b0a365031be0.
- uv sync --locked; uv run pytest tests/unit -q (exit 0); uv run pytest
  tests/integration -q with provisioned backend (exit 0); same suite
  without backend (exit 1, 2 errors, 0 skips — required failure).
- python3 tests/support/prepare_pdf_test_backend.py --runtime-dir
  .../cpython-3.12.15-linux-x86_64-gnu --target <new private dir>: exit 0,
  exact pins printed (pdfminer.six 20260107, charset-normalizer 3.5.2,
  cryptography 50.0.2, cffi 2.0.0, pycparser 3.12; SHA-256 verified).
- python3 -m unittest discover -s tests/oap (OK, 41); python3
  oap/bin/check_state.py --repo-root . (exit 0); uv run ruff check src
  tests/unit tests/integration (clean); python3 -m compileall -q oap tests
  (clean).

Mock/live distinction: all inputs are synthetic owned fixtures (text and
PDFs built in-test). The PDF route is REAL native parsing: the actual
pdfminer.six 20260107 worker executes in a real bwrap/prlimit namespace on
both the devhost and both CI legs (real route, not a mock replacing native
parsing); gateway/qualification routes are unchanged synthetic loopback
suites. Live target/model/GPU/private corpus authorization: NONE. No model
download, no network beyond the pinned wheel fetch inside the reviewed
helper, no real corpus, no GPU. CI evidence above was already observed at
the implementation head; this report makes no claim about this report's own
future push or CI — a separate post-publication receipt and strategic
review record those facts.

## Documentation impact

New docs/ingestion.md: exact supported formats/structural subset,
source-to-block coverage/anchors, native versus visual-needed/partial
semantics, parser resource and trusted-runtime/filesystem limits, required
local/CI setup and exact DEV-only pins, and explicit separation of the
remaining 006 chunk/tokenizer integration and all physical/model/domain/
license/ICA gates. TESTING.md T13 added (historical T01-T12 unchanged).
README/STATUS/UNCERTAINTIES updated (U06/U07 narrowed in software only).
CONTEXT-BUDGET.md 46521/50000 and MANIFEST.json re-hashed (TESTING.md
c158be64..., CONTEXT-BUDGET.md b7fe4989...); after this round's authorized
measurement update, check_state reports
activation_matches_current_governance=false against the order's
ead5815a... activation digest (expected; 005-b precedent; the immutable
order bytes are not rewritten).

## DHA and boundaries

Decision: NONE; no critical append ordered or made; CRITICAL.md untouched
(critical {}). Preserved resources: every MANIFEST-listed source/role/
helper/prompt/startup/governance-law file byte-identical; candidate
histories retained without reset/clean/stash/cherry-pick; no secrets or
private data in Git. No merge performed: PR 8 remains OPEN, no auto-merge,
no tag/release/deploy, no GitHub/default-main merge by coding.

## Limitations and remaining work

- This first slice does NOT close 006: the ordered same-PR continuation
  still integrates the reviewed structural chunking/native tokenizer
  sessions with exact 512/768/1024 body/representation budgets, 64 overlap,
  table neighbor references and no-tail-loss mapping, and must prove actual
  bounded composition before whole-006 acceptance.
- The PDF worker is a trusted isolated development worker, not a hardened
  hostile-PDF sandbox (no seccomp); the cooperative deadlines cannot
  interrupt blocked filesystem calls; the request nonce correlates but does
  not authenticate a compromised worker.
- cffi MIT-0 and remaining transitive/native/platform/model license
  questions stay release/redistribution gates; the DEV backend grants no
  license exception or allowlist expansion.
- The literal-line merge step recorded no new commit (topology no-op; see
  Work and scope). Whole-006 acceptance, contextualization, embeddings,
  snapshots, retrieval, API, GPU/vision, ICA and all real qualification
  remain open / NOT RUN; this report certifies execution of 006-a only, not
  acceptance or release readiness.
