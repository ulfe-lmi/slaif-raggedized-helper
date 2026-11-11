# OAP Coding Report — 005-a

Identifier: 005-a
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 7
Branch: oap/005-artifact-schema-and-source-scopes
Base branch: main
Base commit: bd8e454b23b09bb25967b2c496ace9c0719a96a0
Implementation head SHA: 08b65b9ffc4dc7ebde9651ea258a9cbe4eb37a79
Report publication commit: SELF

## Work and scope

Executed oap/orders/005-a-canonical-source-integration.md (Status FINAL,
Decision: NONE, PR mode CREATE_NEW_PR, live authorization: NONE). The exact
order, oap/active (exactly `005-a` + LF), oap/reviews/004-f-review.json
(SHA-256 5c5c431e5f6ace85472c123c0afb69d5c7dfcae76bf7e94f3909ac0aec0b7225,
matching the order) and oap/reviews/004-resolution.json (FINAL_VERIFIED_
COMPLETE, main CI run 43031375735 all five jobs SUCCESS, live-verified)
were committed byte-for-byte unchanged first:

- dab67f9a50206fb33ed5f163fd4f0053a37553a5 — strategic 005-a round-start
  bytes byte-for-byte unchanged
- 24d273a14fddc6268387a75fe84c802b7b942fae — the ONE authorized LOCAL
  --no-ff merge of exactly
  32a2b84d099f2641123d2569b01afe533064ac61 (branch
  oap/parallel-005-source-cli) into the new 005 branch from verified main
  bd8e454b23b09bb25967b2c496ace9c0719a96a0, preserving candidate
  order/report/implementation histories (no cherry-pick). The merged tree
  equals the order's forecast clean automatic tree
  8332b7bf6d967685d991ffdb7782ad639d6dbf88 plus exactly the four
  round-start files (git diff --stat against that tree shows only
  oap/active, the order, and the two 004-f review/resolution JSONs).
  This local integration is NOT a GitHub PR/default-main merge.
- 08b65b9ffc4dc7ebde9651ea258a9cbe4eb37a79 — implementation head:
  integration of the reviewed source modules with the thin installed route,
  focused installed-CLI tests, documentation and governance reconciliation.

Changed behavior/paths at the implementation head:

- src/slaif_raggedized_helper/cli.py — thin `source` prefix delegation:
  top-level help entry plus `raggedized source ...` delegated to the
  existing source_cli.main before normal parsing (accepted parity
  pattern; no argparse/logic duplication).
- tests/integration/test_source_installed_cli.py — new; five installed
  `raggedized source` route tests (see acceptance 6).
- src/slaif_raggedized_helper/source_admission.py, source_cli.py and the
  four candidate test files, two docs/parallel API docs and three
  PAR-005 local lane orders/reports — arrived byte-identical via the
  ordered merge (candidate receipts re-verified: admission-b report commit
  0837191198b2b1712445d5ba6ca268d358637866 blob SHA-256 1a46e4d7...
  822a and source-cli report commit 32a2b84... blob SHA-256 ae5773bc...
  e736, both matching the accepted root reviews; opposite-author
  audit-source-b report SHA-256 2b6d8958... b5017 matches the recorded
  peer hash, audit-source-cli targets 32a2b84 with ACCEPT_CANDIDATE and
  zero findings).
- docs/parallel/source-cli-api.md — documents the installed route and the
  module invocation as one implementation with identical exit codes.
- README.md — 004 recorded as merged (PR #6); first 005 slice described;
  installed source commands added; the public CLI list now lists
  doctor/probe/qualification/resource/parity/source.
- STATUS.md — current state moved to 005-a on the new 005 PR; 004 closure
  (merge bd8e454, final review and terminal resolution) recorded; 005-a
  historical entry appended.
- TESTING.md — T08/T09/T10 detailed verification notes moved verbatim to
  the new focused document docs/benchmarks/qualification-testing.md
  (all coverage/limitations preserved); concise sufficient summaries and
  pointers remain in TESTING.md; new T11 covers the source suite. No
  required check or law weakened; the 50,000 ceiling untouched.
- docs/UNCERTAINTIES.md — 005-a observation (U06 software-only narrowing,
  U07 unchanged, documented local trust assumptions).
- oap/governance/CONTEXT-BUDGET.md + oap/governance/MANIFEST.json —
  routine set re-measured at 42,370/50,000 UTF-8 bytes (TESTING.md
  17,445 -> 9,819); manifest hashes for TESTING.md and
  oap/governance/CONTEXT-BUDGET.md refreshed and EVERY manifest hash
  re-verified against disk (all OK). Exact model tokens remain
  UNMEASURED.

No provenance/jobs/text/PDF/006 content in this slice; no unrelated
qualification/resource/model-client changes.

## Acceptance evidence

1. Strict versioned manifest/records round-trip: tests/unit/
   test_source_admission.py (strict manifest: duplicate keys, NaN,
   unpaired surrogate, unknown fields, unsafe paths, unsupported types
   refused; schema version 1; immutable tuples) and tests/integration/
   test_source_admission_composition.py (admit -> inspect equality) pass.
   Real installed smoke: `raggedized source inspect` returned the full
   versioned revision (revision identity, corpus, explicit labels,
   independent rights, declared product/version fields all present with
   unknown facts null — title/language/product/version/date/authority
   null), and the stored record re-validated byte-identically. No
   extraction/model fingerprint is fabricated: revision identity binds
   source metadata only; extraction dependency stays 006/016.
2. Approved-root admission with bounded reads and explicit fields:
   parse_manifest enforces the 256,000-byte/128-entry manifest bounds;
   the CLI reads the manifest through O_NOFOLLOW|O_NONBLOCK with
   before/after identity/size/mode/change-time checks; admit() opens the
   approved root and every path component with O_NOFOLLOW directory
   bindings, requires a regular file, and bounds the stream at the
   declared size + 1; processing approval, corpus, rights and explicit
   access labels (absent labels invalid, empty set public) are required;
   no tool/shell/fetch path exists (guarded subprocess below). Installed
   refusal tests prove unapproved/missing-label/traversal manifests fail
   with typed errors and no store object published.
3. Descriptor-level traversal/symlink/race/special-file/growth
   negatives: tests/unit/test_source_admission.py
   test_open_boundaries, test_intermediate_replacement_and_growth,
   tests/unit/test_source_cli.py test_manifest_descriptor_bounds_and_
   special_files, test_manifest_growth_refused,
   test_verified_read_detects_mid_read_mutation, and the installed
   symlink/corrupt-store test all exercise actual opens/reads (not
   string checks); atime-only changes are excluded from the identity
   comparison while mtime/ctime/size/mode/device/inode are not.
4. Exact-bytes storage, dedup with distinct identities, metadata
   revisions, conflict refusal: the installed shared-byte test and the
   real smoke both show two logical documents (public/allowed vs
   private/prohibited, distinct corpora) over ONE digest-named blob, a
   title correction publishing a NEW immutable revision while the
   unchanged document and blob are reused (identical retry returned the
   same revision IDs); tests/unit/test_source_admission.py
   test_corruption_conflict_and_retry and test_unvalidated_copy_cannot_
   escape_or_publish prove corrupt/conflicting objects are refused
   (existing immutable artifacts never overwritten to force reuse) and
   that Pydantic unchecked copying cannot escape the root or publish.
5. Atomic bounded publication: _publish writes to an mkstemp staging
   file, flush+fsync, then hard-link publication with directory fsync
   in the destination directory (same filesystem); the fault-seam tests
   (before_blobs_publish/before_revisions_publish/after_blob_publish)
   show an interrupted operation leaves prior complete artifacts
   readable and retry reuses verified matching artifacts; an orphan
   complete blob without a revision is not a completed import (inspect
   refuses); all store reads are bounded, no-follow and checksum-
   verified (MAX_RECORD 16,384; MAX_ORIGINAL 64 MiB); no pickle/object
   execution anywhere in the slice.
6. Installed CLI behavior with two owned synthetic documents sharing
   bytes and differing rights/ACL plus a metadata revision: new
   tests/integration/test_source_installed_cli.py (5 tests) runs the
   INSTALLED `raggedized source` route in subprocesses: shared-byte
   import -> one blob + two distinct revisions, identical retry reuse,
   inspect with correct per-document corpus/labels/rights, verified
   read_original byte equality, metadata-revision new ID with unchanged
   document/blob reuse; safe preflight refusals (unapproved, missing
   labels, traversal, argument errors, unknown subcommand, FIFO
   manifest) with no private-path echo and no store creation; corrupt-
   blob/unknown-revision inspect refusals with fixed safe errors;
   guarded help + full import with model imports and socket creation
   blocked (zero network/model work). Real disposable smoke (owned
   /tmp root/store, 35-byte Slovenian/astral shared original): import
   exit 0 with two distinct revisions and one blob named
   6145cad7443c56adbb526631649bf13d96bcb757ac980f529c04079a0aa24cde;
   second import reused both revision IDs; inspect exit 0 with corpus
   two / labels ["private"] / rights prohibited and unknown facts null;
   corrupted blob inspection refused (stage inspect, no content/path
   echo). Routine errors/logs carry no source passages, private paths,
   raw exception text or credentials. Existing suites stayed green.

## Verification

Exact commands and results (devhost, owned fixtures only):

- uv sync --locked — clean locked environment.
- uv run pytest tests/unit/test_source_admission.py tests/unit/
  test_source_cli.py tests/integration/test_source_admission_
  composition.py tests/integration/test_source_module_cli.py
  tests/integration/test_source_installed_cli.py -q — 22 passed
  (17 candidate + 5 new installed-CLI).
- uv run pytest tests/unit -q — subprocess return code 0 (562 tests
  collected; zero failures). uv run pytest tests/integration -q —
  subprocess return code 0 (350 tests collected; zero failures).
  Note: with pyproject addopts=-q plus command -q pytest prints only the
  progress line, so the subprocess return code is the authoritative
  result; root independently collected the same 562/350 counts without
  execution (strategic audit/005-a-collection-counts.json,
  2026-11-11T14:06:23Z). One unused import in the new test file was
  caught by lint and fixed before the final runs.
- python3 -m unittest discover -s tests/oap — Ran 41 tests, OK.
- python3 oap/bin/check_state.py --repo-root . — exit 0; state ACTIVE,
  active 005-a, declared context 42,370/50,000.
- uv run ruff check src tests/unit tests/integration — All checks
  passed.
- uv run raggedized --help — lists the source route; real installed
  smoke as in acceptance 6 (exit codes 0/0/0; refusal exit 1 with safe
  JSON).
- Reconciliation before integration: origin/main =
  bd8e454b23b09bb25967b2c496ace9c0719a96a0; PR #6 MERGED (no other open
  objective PRs); main CI run 43031375735 all five jobs SUCCESS
  (matching the committed resolution); candidate tip =
  32a2b84d099f2641123d2569b01afe533064ac61 containing admission-b tip
  0837191198b2b1712445d5ba6ca268d358637866; git merge-tree forecast tree
  8332b7bf6d967685d991ffdb7782ad639d6dbf88 matched the order; both
  candidate report blobs match the accepted reviews' SHA-256 receipts.
- Implementation-head CI: run 43036091799 on
  08b65b9ffc4dc7ebde9651ea258a9cbe4eb37a79 — ALL 5 jobs SUCCESS
  (OAP tests Python 3.12/3.13/3.14; Product tests Python 3.12/3.14).
- PR #7 created from exact main: base bd8e454b23b09bb25967b2c496ace9c0719a96a0,
  head oap/005-artifact-schema-and-source-scopes, state open, no
  auto-merge.

Mock/live distinction: all evidence is synthetic/offline on owned
disposable local fixtures (loopback-free; no network source fetch, no
model, no GPU, no real corpus, no protected service). Live
authorization: NONE. All real qualification remains NOT RUN. No secret
or private data appears in this report.

This report cannot certify its own future push or report-head checks;
the separate post-publication receipt and strategic review record those
facts.

## Documentation impact

docs/parallel/source-cli-api.md now documents the installed
`raggedized source import|inspect` route and module invocation as one
implementation with identical exit codes; README, STATUS,
docs/UNCERTAINTIES and TESTING updated as in Work and scope; detailed
T08/T09/T10 notes preserved verbatim in
docs/benchmarks/qualification-testing.md; governance measurements
refreshed (routine 42,370/50,000; manifest hashes re-verified).

## DHA and boundaries

Order Decision: NONE; no D1 candidate reported; no CRITICAL append
performed. Preserved: strategic round-start bytes byte-for-byte
(004-f-review SHA-256 5c5c431e..., resolution FINAL_VERIFIED_COMPLETE,
active exactly `005-a`+LF); candidate order/report/implementation
histories via merge; accepted 004 source/tests and
architecture/source-original/role/helper/prompt bytes untouched. No
merge performed on GitHub (PR #7 open, auto-merge disabled); the only
merge was the ONE ordered LOCAL --no-ff integration. No model/
profile/auth change; Qwen3.8-27B/A100 Q8/xhigh/CLI 0.164.0 settings
preserved (no live work at all).

## Limitations and remaining work

This is the first 005 slice only: block/span/chunk, derived-scope and
job/attempt contracts remain REQUIRED same-PR continuations before
whole-005 acceptance; no 006 canonical activation, no partial 005
merge. No extraction/parsing (006/016), no provenance or jobs records,
no principal authentication/policy revocation/snapshots/worker
execution, no source-serving endpoint; operator approval is metadata,
not authentication or legal verification. Local POSIX assumptions
(private operator-controlled store, atomic hard links, directory fsync,
same filesystem) are documented, not qualified beyond owned fixtures.
All real qualification, 014/015/016/017/018/019/020 gates, license
questions and full MVP remain open/NOT RUN.
