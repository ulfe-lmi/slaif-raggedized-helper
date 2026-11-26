# OAP Coding Report — 009-ae

Identifier: 009-ae
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 6388882361dc9ce10c030152ab5030f6406948d0
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-ae-private-case-bound-hybrid.md` (FINAL;
AMEND_EXISTING_PR 11; Decision: NONE; order file SHA-256
`425f57f1ce19d7e2cd304f0597a8725f128a00c83b80fe4e6228a41aeee78c7e`,
byte-identical to the strategic workorders copy) at round base
`df480130695d524b23346d002860c96ff71d80e5` (the accepted 009-ad
report-only head whose required hosted run 44810977091 attempt 1
passed all five jobs and every step, each Product at 3,438 ordered
units and the separate 958-case integration; main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b` exact). Objective: add a
bounded private case-bound entry to the same held-pin hybrid
operation, deriving the case question and effective scope through
genuine canonical dataset admission and the actual cohort's case
intersection, keeping the full selected principal authority anchor
distinct, and exercising a genuine narrowed success and a refusal for
an unavailable readable partition without attaching the evaluator or
a model.

History published in this round (one normal push to the same PR branch,
no force push, no merge, one PR):

1. `e523fc170357510a10d05cb43f4506e9c1d1b775` (parent: round base
   `df480130`) — exact Root transcript, four paths: `oap/active`
   (`009-ae` + LF, 7 bytes, SHA-256
   `9255a790519b2ce9223b7c967a1958187b0f6a36dcc484da491e0c2a18809705`),
   `oap/orders/009-ae-private-case-bound-hybrid.md` (the FINAL order
   above, 8,390 B, SHA-256
   `425f57f1ce19d7e2cd304f0597a8725f128a00c83b80fe4e6228a41aeee78c7e`)
   and the two indexed JSON control files copied byte-exact by
   basename: `oap/reviews/009-ae-case-bound-source-inputs.json`
   (10,287 B, SHA-256
   `5df8e00528c88216cf2776ba9e815d654cb897a03ec43be4c77b3112fe1e7b08`)
   and `oap/reviews/009-ae-prior-resolution.json` (1,285 B, SHA-256
   `21dcfab02a302b5c4bbfea8e7f3f9563399aa80e9005b6e44157dbc7168ed9e9`),
   each re-verified at its indexed SHA-256 after copy.
2. `6388882361dc9ce10c030152ab5030f6406948d0` (parent: 1) —
   implementation, exactly the four ordered paths:
   `src/slaif_raggedized_helper/raw_hybrid_search.py` (30,026 B,
   SHA-256
   `6908c3764e7b047347a33df9e6c23a4fecc210023da9b8a5c96aff2a07603575`),
   the new
   `tests/integration/test_private_case_bound_hybrid_composition.py`
   (10,744 B, 219 lines, SHA-256
   `8c944ad946ada150b454aedff92c56bfe76ac235484c86faf5802b668ff3e364`),
   `STATUS.md` and `docs/evaluation.md` (short cumulative notes).
   Everything else — the public `search` and `search_pinned` bodies
   and signatures, the legacy call shape, the one real `_search`
   body, all lower engines, existing callers, the pin and policy
   libraries, the publisher, evaluator, native encoder, existing
   tests, the workflow and the CI partition — stays byte-exact; no
   relabeling of prior immutable evidence.

## Implementation

One fixed private case-bound public entry
`search_pinned_case(admission, owner, dataset_bytes, case_id,
query_payload, *, query_space_id, query_definition_fingerprint,
query_policy_id, query_execution_fingerprint, dense_k=60,
lexical_k=60, partition_cap=60, k=60, deadline_ms=30000, trace=False)`
binds the exact current `PolicyRequestAdmission`, the exact active
operator-owned `PinOwner`, bounded canonical text-evaluation dataset
bytes and one exact case ID; it takes no caller text, grants,
restrictions, stores, root, snapshot, credential, callback or clock.
It selects the fixed internal case path of the ONE shared
`_search_pinned` body (no duplicate preparation, guard, held checks,
O1, live association, O5 or restoration in a second body; one real
`_search` algorithm runs exactly once per dispatch). On that path the
bounded canonical dataset is admitted under the genuine parser
(`text_evaluation_dataset.admit`) through the same clipped absolute
budget (remaining ms of the one clipped operation deadline, capped at
the accepted 30,000 ms), the exact admitted case question and the
narrower effective case value are derived BEFORE guard custody
through the genuine existing case-scope intersection
(`source_bound_stage_loss._admit_authority`) over the exact full
principal anchor with no additional restriction, and a missing or
invalid case refuses without widening. The full principal immutable
policy-derived value stays carried separately for the detached
current authority comparisons: the final O5 check re-derives and
compares against the full anchor (never the narrowed value), while
the effective grants serve the actual eligibility
(`_scope_refused`), the engines and the authority hash bound to the
result (the shared body's `authority_sha` is computed from the
passed grants). The legacy path is byte-identical in behavior and
shape (`grants = full_grants`), and the public `search` /
`search_pinned` signatures, normal deadline, outcomes and every
original caller path are unchanged. The same private preparation,
one real nonblocking owner guard held through the ownership span,
live association, one shared hybrid body and the five genuine
current observations at the precisely named cuts O1-O5 are reused
unchanged; the fixed ordinary content-free refusal, the exact
original interruption identity, owner restoration (the original
exact `op.end` restored in a finally before guard release) and no
post-deadline usable result are preserved, with no duplicate engine
loop and no per-operator additional restriction in this first
private proof.

The new integration file holds exactly two default actual hosted
nodes over the real `make_owned_support` owned-source fixture (three
real sources a, b, c over corpora one/two with the secret label on
b), the real `dataset_and_bundles` cohort dataset (actual owned
source atoms and the h1/h2 case declarations), the real raw snapshot
selector and the actual `PinOwner.acquire_selected_data`, reusing the
existing reviewed synthetic wire/selector fixtures from
`test_private_pinned_hybrid_composition` byte-exact (synthetic
principal, credential, attributed wire emitter, payload installer and
atomic selected-record publication). Counters start after real setup,
selection and pin; the request lifetime begins after fixture
acquisition. The actual positive witness (h1) genuinely narrows to
(one, v1, no secret): the real policy withholds b in corpus two,
which is outside the effective readable scope and does not block it,
so only a/c contribute; it attests the engine/owner proof
(8 catalogs, 17 directory loads including the distinct final owner
load, 1 dense, 1 lexical, 1 fusion), five reads (O1-O5), the restored
`op.end` and released guard, dense (2,2,2) with scores [0.8, 0.6],
lexical (2,1,1), fusion (2,1,2,1) with the leading score 2/61, the
exact narrowed effective authority hash, and equality of the result
with the genuine legacy body explicitly run with those effective
grants (legacy counted separately at 8 catalogs / 16 directory loads
with no owner load and no further reader call). The actual negative
witness (h2) under the same admitted synthetic policy reads (one,
two, v1, secret): the withheld b is now inside the readable scope
and the dispatch refuses through the actual policy admission and case
declaration before any new catalog, directory, dense, lexical or
fusion call (0,0,0,0,0 with one read, O1 only), the admission not
latched and custody restored; the same node attests the absent case
and the tampered dataset byte refusal before custody at zero engine
work and zero new reads, the fixed content-free ordinary refusal, the
restored owner guard/deadline, and no fixture rejection as passing
evidence. The existing seven private integration nodes and the 958
total prior integrations stay exact.

## Acceptance evidence

1. Exact clean canonical and unique remote PR base, regular prior
   response and terminal proof, every indexed base dependency and
   exact transcript bytes: local HEAD equals the ordered round base
   `df480130` and the exact remote branch head; live main is
   `5a7b41cc` exact; PR 11 is the unique open non-draft PR, base
   `main` `5a7b41cc`, head `oap/009-evaluation-baseline`
   `df480130`, no auto-merge, mergeable state clean; the round-base
   required hosted run 44810977091 attempt 1 is
   completed/success on that exact head (all five jobs and every
   step, 3,438 ordered units and 958 integration each Product); all
   four indexed strategic files match their ordered SHA-256s
   (`5df8e005…`, `21dcfab0…`, `334b25e0…`, `da6bedbe…`); all 35
   indexed base dependency objects were verified exact at the round
   base (mode 100644, blob OID, byte count and SHA-256 per the source
   inputs) and all four indexed proof input/inventory files match
   their digests at the strategic location; `oap/active` is exactly
   `009-ae` + LF (7 bytes) and the order file is byte-identical to
   the strategic workorders copy. The new integration destination
   was absent at the base (git ls-tree empty) and exists only as the
   ordered new path. No concrete drift; reconciliation stopped
   nothing.
2. One fixed private case-bound entry with the shared preparation,
   guard, live association, one shared body and five real cut
   positions: see Implementation above; the final committed bytes
   contain exactly one `_search_pinned` body and one real `_search`,
   the fixed case path is chosen internally by the new public entry,
   the dataset is admitted under the same clipped absolute budget,
   the case question and effective grants are derived before guard
   custody, the full anchor is carried separately for O5 and the
   effective grants for scope/hash/engines, and the public
   `search`/`search_pinned` signatures, legacy call shape and all
   five real cut positions O1-O5 are preserved byte-exact from the
   base.
3. Full anchor vs effective case value separation: the final O5
   authority check compares the re-derived bound grants against the
   exact full anchor (`full_grants`), never against the narrowed
   value; the effective case value is derived only from that exact
   full anchor and the admitted case declaration with no additional
   restriction; the result keeps the exact case authority (authority
   hash computed from the effective grants); a missing or invalid
   case refuses without widening; an unavailable partition outside
   the effective readable scope does not block the unaffected scope
   (h1), while unavailability inside the readable scope refuses
   before the first catalog (h2); no claims about prior trusted
   internal snapshot integrity reads or additional rights are made.
4. Two new default actual hosted cases with real fixtures and
   counters after setup/selection/pin: see Implementation above;
   h1 positive witness (exact narrowed effective authority and exact
   real case question matching the genuine legacy body run with those
   effective grants, five real observations, real positive
   engine/owner proof, legacy counted separately) and h2 negative
   witness (actual policy admission and case declaration refusal
   before any new catalog/directory/dense/lexical/fusion call, plus
   absent/invalid case in the same node), with the existing seven
   private integration nodes and 958 total prior integrations
   unchanged. Expected exact report-head gate: ordered hosted
   Product units unchanged at 3,438 each (A 1,440 and B 1,998),
   separate 960 default integrations each (958 prior + 2 new), both
   Products, all three OAP jobs and every prior required step
   passing.
5. The exact report-head hosted gate is owned by Root and is PENDING
   at report authoring (item 4 counts); pending jobs are pending at
   report authoring — this report does not certify its future push or
   checks, and no expected test result is claimed as having run
   locally.

## Verification

Local (actual, this round, on the final corrected working-tree
bytes; all process proofs under `timeout -k 5 120 prlimit --cpu=60
--as=1073741824`, canonical `.venv`, physical canonical `src` via
`PYTHONPATH`, `OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`,
fresh mode-0700 scratch `/tmp/oap-009ae-proof.JOvhJ1` directly under
sticky `/tmp`, private pytest basetemp subdirectory, raw logs outside
the basetemp, `-o addopts= -p no:cacheprovider`, actual exits
captured without pipeline masking; command record `commands.txt`
SHA-256
`623c6677fba243bcca73d3d5bb87526f5dd09c4c299bab94cd0936750de28546`,
probe `origins-probe.py` SHA-256
`d98d57a679d2500230f4f5480b65bc8caf498b3e51153b02c75fc99a791b8ce4`):

- RUN1 one bounded inherited focus of the four ordered unit files
  under `tests/unit/` (`test_raw_hybrid_search.py` 15,
  `test_private_policy_pin_eligibility.py` 53,
  `test_private_policy_request.py` 45, `test_raw_snapshot_pin.py` 8):
  121/121 passed, exit 0 in 1.75 s; raw stream `run1.log` 180 B
  SHA-256
  `099353b415b5cab4a67770a6472809500995673d9a0ba117a420c2d27171674a`.
- RUN2 one capped collect-only of the two new integration nodes in
  `tests/integration/test_private_case_bound_hybrid_composition.py`:
  2 tests collected, exit 0; raw stream `run2.log` 258 B SHA-256
  `105d8df2fdea856ffcbd9c187398e21124b13c7712b4f2115216cb81e406ddd8`.
- RUN3 one targeted two-file Ruff on the two changed Python paths on
  one local core (`taskset -c 0`): exit 0, "All checks passed!" (raw
  `run3.log` 19 B SHA-256
  `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`,
  byte-identical to the prior rounds' Ruff digest).
- RUN4 one bounded physical product import-origin probe: the changed
  module `slaif_raggedized_helper.raw_hybrid_search` and the three
  modules it newly uses (`provenance_records`,
  `source_bound_stage_loss`, `text_evaluation_dataset`) all resolve
  to the canonical repository physical `src`; the changed file's
  working-tree SHA-256 is
  `6908c3764e7b047347a33df9e6c23a4fecc210023da9b8a5c96aff2a07603575`
  and the three newly used modules match their indexed preimage
  digests (`88d3edfc…`, `caf22819…`, `923d34d2…`); ORIGINS_OK, exit
  0; raw stream `run4.log` 609 B SHA-256
  `87e74a7c61ca27fec295b7d5744e0977d596fd1b238e37de27f8d872138c6580`.

No full local suite, no repeated unchanged proofs, no native proof
execution, no substitute, no install or other setup ran locally (the
actual native fixture is hosted-only; the local native test
environment is absent, was not installed and was not simulated). No
first failure occurred on the final bytes, so nothing was preserved
beyond the recorded raw streams. The earlier pre-correction scratch
proofs (against the superseded draft bytes) are not evidence for this
report and were re-run fresh on the final bytes as listed above.

Hosted (expected, pending at report authoring): the two real
integration outcomes in the new file run only in the configured
hosted jobs; the exact report-head gate requires ordered hosted
Product units unchanged at 3,438 each (A 1,440 and B 1,998) plus the
separate 960 default integrations each, with the other three OAP
jobs, both Products and every prior required step; Root owns that
fresh hosted review. The round base's required hosted run
44810977091 attempt 1 passed all five jobs and every step. This
report cannot certify its future push or checks; a separate
post-publication receipt verifies the remote publication facts.

Mock/live distinction: all fixtures and roots are synthetic and
operator-owned; no live model request, network, real policy root,
credential, GPU or hardware was used, and no actual current
authorization invocation happens outside the synthetic
wire/selector fixtures.

## Documentation impact

`STATUS.md` current-slice lead 009-ad -> 009-ae plus the 009-ae slice
entry, and `docs/evaluation.md` new "The 009-ae private case-bound
hybrid (same 009 continuation)" section before the preserved
input-contracts section: the exact case-scope authority (one shared
body and one real `_search`, fixed internal case path, dataset
admission under the same clipped budget, case question and effective
grants derived before guard custody, full anchor carried separately
for the detached authority comparisons, effective grants for
scope/hash/engines), the actual positive (h1) and negative (h2, plus
absent/invalid) witnesses with their exact counts, the actual local
proof on the final bytes, the pending hosted gate and expected
counts (3,438 each, 960 integrations each), and the open gates.
Evaluation/source/grade/delivery, rights, the governed live operator,
the encoder and the representative baseline stay open; whole 009
PARTIAL and baseline NOT_RUN are recorded. All historical sections
preserved.

## DHA and boundaries

Order Decision: NONE; no `append_critical.py` invocation, no CRIT
entry added or touched, no consequential D1 candidate reported this
round. Preserved: the prior report archive and transcript objects,
all 35 indexed base dependencies byte-exact, the unrelated worktrees
and branches, the workflow and CI partition, the existing
Qwen/gateway services, and the canonical worktree's synthetic
temporary fixtures only. No merge, no auto-merge, no force push, no
new PR, no release/tag/deploy, no branch merge/cherry-pick, no direct
FIFO access, no credentials, no real data, service or hardware use,
no outside setup, no model/profile change, and no nested/helper
agents; the sole external control wrapper's consumed notification
was not re-read.

## Limitations and remaining work

No actual first failure occurred on the final bytes in this
round's ordered proofs. Deviation from the as-planned first draft:
the pre-proof draft duplicated the existing `_search_pinned`
preparation, guard, held checks, O1, live association, O5 and
restoration in a separate `_search_pinned_case` body; the human
pre-proof source correction (authoritative) required one shared
`_search_pinned` body and one real `_search`, a fixed case path
chosen internally by the new entry, dataset admission under the
shared clipped end, case question plus effective grants derived
before guard custody, the full anchor carried separately for O5 and
effective grants for scope/hash/engines, preservation of the old
public signatures, legacy call shape, all five real cut positions
and the current proof caps; the final committed bytes implement
exactly that, and the ordered local proofs above were re-run fresh
on the final bytes (the superseded pre-correction scratch proofs are
not cited as evidence). Two initially unused imports in the new test
file were removed before commit; the final file is Ruff-clean. The
two real integration outcomes, including their exact counts (h1
(8,17,1,1,1) with five reads and legacy (8,16,1,1,1); h2
(0,0,0,0,0) with one read), are hosted-only and unproven until the
exact report-head hosted run passes; this report attests collection
and the bounded local checks only. The case-bound entry is synthetic
in this first private proof: it does not attach the evaluator or a
model, does not qualify real selection roots, guarded encoding,
fusion/current delivery, evaluation source cuts or the
representative baseline, and makes no per-operator additional
restriction. The observation cuts remain cooperative deadline checks
between steps — they cannot preempt a running operation. No merge;
baseline NOT_RUN; whole 009 PARTIAL; DHA NONE.
