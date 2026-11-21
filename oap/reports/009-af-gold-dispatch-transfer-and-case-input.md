# OAP Coding Report — 009-af

Identifier: 009-af
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 961f8deee9d8d6493c5dd795e4c8aca3c1a2eb4c
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-af-gold-dispatch-transfer-and-case-input.md`
(FINAL; AMEND_EXISTING_PR 11; Decision: NONE; order file SHA-256
`6dbc22b0c5b13fac7e7b8693b75bb0c7d2d5886890e10672d50ad944ed7d6871`,
byte-identical to the strategic workorders copy) at round base
`de62aebdf11e1983845a6a38464cc0cc645991e9` (the accepted 009-ae
report-only head whose required hosted run 44822395486 attempt 1
passed all five jobs and every required step, each Product at 3,438
ordered units (A 1,440, B 1,998) and the separate 960-case
integration; main `5a7b41cc512cf883b5b2cb92d87554b4d24e685b` exact
against the remote at round start). The unique open non-draft PR 11
targets main with head `oap/009-evaluation-baseline`; no second
objective PR exists.

Objective: transfer the independently reviewed standalone private
Gold bundle dispatch start boundary by exact blobs, close the
observed 009-ae None dataset edge at the existing private case-bound
hybrid entry before shared custody or policy observation, and keep
one existing binder and one existing hybrid body. Controlled
synthetic software evidence only; whole 009 remains PARTIAL.

History published in this round (one normal push to the same PR
branch, no force push, no merge, one PR):

1. `1244bf995113ba409e63e209cb45d312b32982fe` (parent: round base
   `de62aebd`) — exact Root transcript, four paths: `oap/active`
   (`009-af` + LF, 7 bytes, SHA-256
   `b78be1492ba80d2e9617ae01f0ca8a0c43782444f8f8dc6c51d37255d7200c33`),
   `oap/orders/009-af-gold-dispatch-transfer-and-case-input.md`
   (9,087 B, SHA-256
   `6dbc22b0c5b13fac7e7b8693b75bb0c7d2d5886890e10672d50ad944ed7d6871`)
   and the two indexed JSON control files copied byte-exact by
   basename: `oap/reviews/009-af-gold-dispatch-transfer-index.json`
   (15,117 B, SHA-256
   `87e37bce939161788d57b49b3479b25c29949c9fb8e9bc361a96e9078314bd38`)
   and `oap/reviews/009-af-prior-resolution.json` (858 B, SHA-256
   `3e2837ba48bc21ce43045431903abe5446872a9ec73c3896046b8ea995cb10e9`),
   each re-verified at its indexed SHA-256 after copy.
2. `961f8deee9d8d6493c5dd795e4c8aca3c1a2eb4c` (parent: 1; tree
   `8430389ba52b98e7d460a13e06ba3047288ae418`) — implementation,
   exactly the six ordered paths:
   `src/slaif_raggedized_helper/text_evaluation_gold_binding.py`
   (20,215 B, SHA-256
   `e712c9d579585c43b5790d83367d04415de5fe166fef39398b445f26be488494`,
   exact candidate tree blob `85cdcaded451501a900e552be6a5257eaef9949d`),
   the new
   `tests/integration/test_current_gold_dispatch_composition.py`
   (28,197 B, SHA-256
   `934537cf536e8934da1b80c1e38795b585ce626574ed8e9eaf57531955540083`,
   exact candidate tree blob `2bcfc506a91d0b60b2e61e6433aaaa8e3f25276f`),
   `src/slaif_raggedized_helper/raw_hybrid_search.py` (30,865 B,
   SHA-256
   `3b3ae6915e20e324e3d6eb10aa3f8d3f5b1af419be5083c1cfd1e28bf921c4ba`),
   `tests/integration/test_private_case_bound_hybrid_composition.py`
   (11,997 B, SHA-256
   `ed8aada83b633711b2db29f1ed2b32212d73ee613dcdc4a9b53d59d396347a6e`),
   `STATUS.md` (186,704 B) and `docs/evaluation.md` (184,313 B) with
   short cumulative notes. Everything else — the public `search` and
   `search_pinned` bodies and signatures, the legacy call shape, the
   one real `_search` body, all lower engines, existing callers, the
   pin and policy libraries, the publisher, evaluator, native
   encoder, existing tests, the workflow and the CI partition —
   stays byte-exact; no relabeling of prior immutable evidence.

## Implementation

Gold dispatch transfer (exact blobs): the two tree objects of the
independently reviewed standalone private Gold candidate
`51ffb8ce2b521a229a5b518869ab90b8e8132a8b` (sole child of
`00743eca3c351d57e45ec81004f52e519ebec00a`; its report-only SELF
`cc0e60a3520d6ad55a75b2e24e2c90e0e43506aa` report bytes SHA-256
`82ccd331b57c3b45470a2d5f9b10a4f00113d73bc7ac5a9b1fd2e6287570d552`)
are transferred by blob identity only, without cherry-picking the
candidate's committed history; the parallel branch and its report
stay immutable. The transferred boundary is the start of the private
guarded Gold bundle dispatch: one closed private entry
`bind_pinned` binding the exact admitted
`PolicyRequestAdmission` and exact active `PinOwner` to the single
existing Gold body (one binder, one hybrid body retained); stores
from the actual owner only; effective case grants from the exact
admitted principal intersected with the genuine case declaration
through the genuine `_admit_authority` under a bounded meter and the
span deadline check; one real nonblocking owner guard held across
the pure pre-dispatch gate, the shared body and the pin tie, with
`op.end` anchored under the guard and its exact prior value
restored on every exit; the actual precomputed clipped end passed
through as `op_end` so every real check/recheck/dispatch uses that
exact end (legacy standalone computation retained); the complete
already-admitted dataset atom set and only the actual declared
bundle IDs gated in their real declared order under the genuine
effective case authority, with unknown, ambiguous, unreadable,
unavailable or uncovered declared entries refusing before any
protected bundle load and undeclared pin members preserving their
unaffected scopes; and the genuine selected reread immediately
before each actual bundle load in BOTH observation passes with the
post-load checks retained, the observed bundle
metadata hash/revision/extraction compared to the exact pin at the
existing post-load validation in both passes, keeping actual
post-load pin identity, legacy compatibility and exception custody
with the exact first non-Exception identity preserved. No new
evaluator/operator attachment, real source rights or protected
delivery is added.

Case input gate (narrow): `search_pinned_case` now validates the
exact dataset bytes type at the nominal case-bound hybrid entry
before calling the shared method or interpreting the internal
sentinel. A None dataset (the legacy sentinel of the shared body)
or any non-bytes dataset receives the existing fixed content-free
refusal before owner custody, before O1, before any live namespace
association and before any protected dispatch. The legacy public
signatures and call shape, the five valid-case observation
positions O1-O5, the effective-authority-versus-full-anchor binding
and the entire rest of the module are unchanged (AST-verified:
module-without-function equal to base, function arguments
equal, only the function body changed). The one existing negative
hosted node
`test_case_bound_withheld_partition_refuses_before_catalog` carries
the added None subcase plus the non-bytes probe over its genuine
fixture and counters, proving the early cut: the fixed refusal at
zero engine/catalog work, no new observation (read count
unchanged), custody never acquired, stable owner and reader state;
the original absent-case, invalid-bytes, genuine h1 positive and
h2 refusal witnesses in the two existing nodes are preserved.

## Acceptance evidence

1. Active prior evidence, named exact remote base and unchanged
   dependency objects verified at round start: `oap/active` exactly
   `009-af` + LF; remote `refs/heads/oap/009-evaluation-baseline`
   exactly the base commit and `refs/heads/main` exactly
   `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`; PR 11 OPEN,
   non-draft, base main, head branch, unique open objective PR; all
   46 indexed receiving objects verified byte-exact at the base
   tree (mode/blob/bytes/SHA-256), the order file verified
   byte-identical to the strategic workorders copy and the five
   exact strategic files verified at their ordered SHA-256
   (index `87e37bce…`, prior resolution `3e2837ba…`,
   Root-terminal-review `07179bce…`, local resolution `f0370284…`,
   receiving preview `70c62dcd…`); candidate topology verified
   (sole child of the exact base; report-only SELF child of the
   implementation; report bytes at the indexed digest); the
   absent candidate test destination confirmed absent at the base
   tree. The four transcript paths were committed byte-exact
   (commit 1 above) before any product implementation.
2. The two selected Gold candidate objects were transferred
   exactly (git blob identity and SHA-256 at the implementation
   tree equal to the index: `85cdcaded451501a900e552be6a5257eaef9949d`
   and `2bcfc506a91d0b60b2e61e6433aaaa8e3f25276f`), without
   cherry-picking the candidate's committed history. The complete
   already-admitted dataset atom set and only the actual declared
   bundle IDs pass the genuine selected-policy eligibility gate
   under effective case authority; no unknown, ambiguous,
   unreadable, unavailable or uncovered declared entry starts a
   protected bundle load; the one real owner guard retains and
   restores its operation end; the single real binder uses the same
   absolute end and the genuine selected reread immediately before
   each actual bundle load in BOTH observation passes, keeping
   actual post-load pin identity, legacy compatibility and
   exception custody (carried by the exact reviewed candidate
   bytes, whose local resolution
   `ACCEPT_EXACT_LOCAL_CANDIDATE_FOR_LATER_HOSTED_RECEIVING_BOUNDARY`
   is committed in the transcript).
3. The exact dataset bytes type is validated at the nominal
   case-bound hybrid entry before the shared method is called or
   the internal sentinel interpreted; the legacy public signatures
   and call shape are preserved. A None dataset and any non-bytes
   dataset receive the existing fixed content-free refusal before
   owner custody, O1, live namespace association or any protected
   dispatch (in-process sanity: None/str/int/valid-bytes all yield
   the fixed `HybridSearchError('hybrid search refused')` with the
   dummy inputs, the gate firing first for the non-bytes forms).
   The None subcase was added to the existing negative hosted node
   using its genuine fixture and counters, with the narrow real
   custody/observation probe (guard never locked, no new read,
   zero engine/catalog work); the original absent-case, invalid
   bytes, genuine h1 positive and h2 refusal remain in the two
   existing nodes, and all five valid-case observation positions
   with effective authority versus full anchor are unchanged.
4. The five actual default Gold witnesses from the candidate are
   preserved by exact file (the byte-exact transferred suite): the
   real fixture exercises stable h2 and separate legacy matching,
   genuine h1 refusal, genuine policy-unavailable h2 refusal, the
   distinct a/c-only dataset and batch with an undeclared
   unavailable b still pinned, the existing-but-unpinned unknown
   bundle, changes after one and three real loads, restored custody
   and the actual late read, with genuine per-load witness counts
   of six/three/one bundle, derived and verified original calls
   across the positive, declared-only and change nodes. They count
   genuinely delegated selected, bundle, derived and verified
   original calls and do not claim preemption of an already
   in-flight read or separate authorization within its lower call.
5. Fresh receiving CI on the exact report-only head is required and
   PENDING at report authoring: all five required jobs and every
   required step, both Product jobs passing the unchanged ordered A
   1,440 and B 1,998 plus a separate full 965 integration (960
   prior + 5 new Gold; the two case-bound nodes are existing nodes,
   one carrying the added negative subcase). Local collection alone
   does not prove the hosted outcomes; Root independently reviews
   the exact report-head logs and receiving scope.

## Verification

Local (actual, this round, on the exact implementation commit
bytes with a clean worktree equal to the committed tree; all
process proofs under `timeout -k 5 120 prlimit --cpu=60
--as=1073741824`, pre-existing canonical `.venv` binaries used
directly with no uv run, no setup and no installs, physical
canonical `src` via `PYTHONPATH`, `OPENBLAS_NUM_THREADS=1
PYTHONDONTWRITEBYTECODE=1`, fresh mode-0700 scratch
`/tmp/oap-009af-proof.jONqQY` directly under sticky `/tmp`, private
pytest basetemp subdirectory, raw logs outside the basetemp, `-o
addopts= -p no:cacheprovider`, actual exits captured without
pipeline masking; command record `commands.txt` SHA-256
`aff6da0b5edbb9a417ae7bb6b3471fa94eadf065116c5acc84fee90a9cb7d8a6`,
probe `origins-probe.py` SHA-256
`27587a0242f7ea87a6a170a0b4cd216e0af4eea09a1c4e5432f0d2295cbe27e4`):

- RUN1 one capped inherited focus of 142 units across the five
  ordered unit files (`test_text_evaluation_gold_binding.py` 21,
  `test_raw_hybrid_search.py` 15,
  `test_private_policy_pin_eligibility.py` 53,
  `test_private_policy_request.py` 45, `test_raw_snapshot_pin.py`
  8): 142/142 passed, exit 0 in 1.80 s; raw stream `run1.log` 180 B
  SHA-256
  `ed177ffd9700e3047ac358db327e1c557deaa66619563e2276cff0b8ede70c5d`.
- RUN2 one capped collect-only of the five Gold and two case-bound
  hosted nodes: 7 tests collected (the five Gold nodes
  `test_pinned_positive_h2_matches_legacy`,
  `test_genuine_scope_narrowing_and_unavailable_refuse`,
  `test_unknown_declared_id_refuses_without_derived_lookup`,
  `test_change_after_three_first_pass_loads_denies_pass_two`,
  `test_change_after_first_load_and_custody_refusals`, and the two
  case-bound nodes), exit 0; raw stream `run2.log` 817 B SHA-256
  `a74a4c50c703c5a2d2809d82d754e5b0d37a698eee7243dd311b69c9dec220ed`.
- RUN3 one targeted four-file Ruff on the four changed Python paths
  on one allowed local core (`taskset -c 0`): exit 0, "All checks
  passed!" (raw `run3.log` 19 B SHA-256
  `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`,
  byte-identical to the prior rounds' Ruff digest).
- RUN4 one bounded physical product import-origin probe: the
  transferred module `text_evaluation_gold_binding`, the changed
  module `raw_hybrid_search` and the companion
  `text_evaluation_dataset` all resolve to the canonical repository
  physical `src`; the two transferred Gold files equal the exact
  indexed candidate blobs and the six companion focus/preimage
  files equal their indexed receiving digests; ORIGINS_OK, exit 0;
  raw stream `run4.log` 912 B SHA-256
  `f7f82118b0bacac12582061134ac2be37c3affc07b1f88a7fe827d1c590a3f78`.

Pre-proof correction disclosed: the first draft of the non-bytes
subcase called the case dispatcher with a missing positional
argument, which would have thrown TypeError before testing the
guarded entry. The human directed the exact correction
(`_dispatch_case(admission, owner, "not dataset", "h1",
embedding)`); it was applied before the implementation commit and
before any proof run, with the bounded-change AST re-verification
and byte-compilation repeated on the final bytes. No proof run
used the defective draft. No first failure occurred on the final
bytes, so nothing was preserved beyond the recorded raw streams.
No unchanged repeat, no extra download, no setup and no local
native execution ran (the actual native fixtures are hosted-only;
the local native test environment is absent, was not installed and
was not simulated).

## Documentation

`STATUS.md` and `docs/evaluation.md` carry short cumulative notes
recording the distinct original case input refusal, the exact
candidate blob transfer (blobs, sizes, SHA-256, candidate
topology), the real six/three/one per-load witness evidence and the
expected hosted scope. Real source rights, encoder transport,
subsequent ranking, grading, publisher, authenticated delivery,
governed full evaluation and the representative baseline remain
explicitly open; no implemented command, measured performance,
license clearance or readiness is claimed.

## DHA

Decision: NONE. No ordered append; no consequential candidate
reported; the register is unchanged.

## Limitations and open evidence

- The five Gold hosted nodes and the two case-bound node outcomes
  are hosted-only and PENDING at report authoring; this report
  attests collection and the local proofs only and does not claim
  the hosted results as run.
- Fresh receiving CI at the exact report-only head is required:
  all five required jobs and every required step, both Products at
  the unchanged ordered A 1,440 / B 1,998 plus the separate full
  965 integration; Root independently reviews the exact
  report-head logs and receiving scope.
- Whole 009 PARTIAL; representative baseline NOT_RUN; protected
  evaluator/operator/delivery, real rights and subsequent
  ranking/grading/publisher/delivery gates stay open.

## Publication and preservation

The transcript and implementation were pushed to the existing PR
11 branch in one normal push (no force push); the remote branch
`oap/009-evaluation-baseline` was verified at the implementation
head `961f8deee9d8d6493c5dd795e4c8aca3c1a2eb4c` immediately after
the push. No merge, no auto-merge, no tag/release/deploy; no model,
provider, profile or client-setting change; no nested or helper
agents. All 46 indexed receiving objects are preserved (41
re-verified byte-exact at the implementation tree; the 5 in-scope
objects are exactly the ordered changes), and the candidate's
parallel branch and report remain immutable. This report cannot
certify its own future push or checks; a separate receipt and the
strategic review record those facts.
