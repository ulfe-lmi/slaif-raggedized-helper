# OAP Coding Report — 009-ab

Identifier: 009-ab
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: d4fc8d12562880bf3843b44c9eb708fa671543ea
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-ab-private-pinned-hybrid-dispatch.md` (FINAL;
AMEND existing PR 11; Decision: NONE; order file SHA-256
`ff53578831be4665251fb35d0570ab97ad009dc4733a3d4137910f564baff4c5`)
at round base `ebbce25705c41c1db9e8f2ec1c4d3a0b833d476f` (the
accepted 009-aa report-only head whose required hosted run
44781112453 attempt 1 passed all five jobs and every step, both
Products at 3,370 ordered units and the separate 951-case
integration; main `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`
exact). Objective: add the first private held-pin route through the
one real hybrid search, binding the admitted current policy,
effective scope, active owner and request deadline to the existing
hybrid engines, with a genuine observed policy change after dense
before actual lexical dispatch; this proof-sized route takes an
already provided synthetic query payload and does not attach the
evaluator, encoder, source grounding or serving path.

History published in this round (one regular push to the same PR
branch, no force push, no merge, one PR):

1. `1d36945d834e7227dcff9065a10aafd9199636a2` (parent: round base
   `ebbce257`) — exact Root transcript, four paths: `oap/active`
   (`009-ab` + LF, 6 bytes),
   `oap/orders/009-ab-private-pinned-hybrid-dispatch.md` (the FINAL
   order above, 11,591 B, SHA-256
   `ff53578831be4665251fb35d0570ab97ad009dc4733a3d4137910f564baff4c5`),
   `oap/reviews/009-ab-pinned-hybrid-source-inputs.json` (byte-exact
   copy by basename, SHA-256
   `7233946e4435825b1cdedf87b7ee8c550b69f28cf7fb55c432b82cf203d14e31`)
   and `oap/reviews/009-ab-prior-resolution.json` (byte-exact copy by
   basename, SHA-256
   `325535e330705a7421f069ce689d4a797f0db67e5d1594244119c91e4eaee2b8`),
   each re-verified at its indexed SHA-256 after copy.
2. `d4fc8d12562880bf3843b44c9eb708fa671543ea` (parent: 1) —
   implementation, exactly the five ordered paths:
   `src/slaif_raggedized_helper/raw_hybrid_search.py` (new fixed
   private entry `search_pinned`/`_search_pinned` plus the O2/O3/final
   owned validation cuts in the shared `_search` body),
   `src/slaif_raggedized_helper/private_policy_pin_eligibility.py`
   (behavior-preserving extraction of the genuinely shared
   already-held operations `_borrowed_owner` and `_held_capture`),
   `tests/integration/test_private_pinned_hybrid_composition.py`
   (new, six default hosted nodes), `STATUS.md` (current-slice lead
   009-aa -> 009-ab plus 009-ab slice entry) and
   `docs/evaluation.md` (new 009-ab section). `PinOwner`, the
   selection operations, all engines, the legacy tests, the unit
   inventory, the configured workflow, the fixtures and the measured
   bridge sources are byte-exact; no other product path or output
   envelope changes.

Behavior added by the implementation:

- The new fixed private entry takes an exact
  `PolicyRequestAdmission`, an exact active `PinOwner` and the
  existing bounded query parameters. It derives the stores, store
  root, snapshot identity and admitted grants only from the actual
  owners and verified selected material: the stores from the owner,
  the root from the actual association's validated root string
  (never the held root file descriptor), the snapshot from the
  verified held `PinData` and the grants from the admission's bound
  principal with restrictions `None`, so the principal's exact
  admitted scope is used with no additional caller restriction. The
  caller supplies no root, stores, snapshot ID, grants, provider,
  callable, alternate clock or credential. The public `search`
  signature, its normal 1..120,000 ms deadline and outcomes and every
  original caller path stay exact; this route's deadline is bounded
  to the accepted 1..30,000 ms reader range.
- One real nonblocking owner guard is held through the one existing
  hybrid body; the span never calls `PinOwner.check` or re-enters the
  borrowed preparation guard, and the private operation does not
  acquire, close or return ownership of the input pin. One original
  absolute operation deadline is clipped to the current request
  lifetime (the request end is never reset or extended) and anchors
  the actual `op.end` only while held; its original exact value is
  restored in a finally before guard release on success, ordinary
  refusal and interruption.
- Four genuine current observations run at the precisely named cuts:
  O1 after pure admission, nonblocking owner custody and in-memory
  capture verification, before captured scope use, with no
  association, catalog or source I/O; the genuine isolated policy and
  captured membership scope rules then refuse an unavailable or
  unusable scope before any catalog I/O; O2 inside the shared body
  after verified scope, actual association and all earlier body
  validation, before the first real catalog call; O3 after the real
  dense output completes and before any real lexical call, where a
  detected change refuses with zero new lexical and fusion calls (an
  already-started earlier operation cannot be undone); O4 after the
  final actual pin association/full revalidation and its post-load
  association, with the final exact authority check and the true
  remaining deadline, before usable return. The final full
  revalidation compares the fresh full load against the exact
  originally held `PinData` bound before the body, not a newly read
  alias. Scope drift, expired budget and late usable results refuse
  throughout; a fixed content-free ordinary refusal is exposed and a
  non-Exception interruption is preserved by identity.
- The eligibility refactor extracts only the genuinely shared
  already-held operations (the nonblocking borrowed custody and the
  held capture verification); the 53-case eligibility suite stays
  behavior-exact.

## Acceptance evidence

Criterion 1 (one fixed private entry, derived bindings, exact public
path): `search_pinned` admits only the exact `PolicyRequestAdmission`
and `PinOwner` types and one bounded 1..30,000 ms deadline; stores,
the validated root string, the held snapshot identity and the bound
principal grants (restrictions `None`) all derive from the actual
owners and verified selected material; no caller root, stores,
snapshot ID, grants, provider, callable, alternate clock or
credential is accepted. The public `search` signature, normal
deadline and outcomes and every original caller path are unchanged
(the public path is behavior-proven by the unchanged 15-case
`test_raw_hybrid_search.py` focus and by the legacy-equivalence
assertion in the new positive node).

Criterion 2 (one real nonblocking guard through the body, exact
owner/deadline semantics): `_borrowed_owner` (creator-PID check plus
the owner's own nonblocking guard) is the single custody entrance and
is held through the entire span; the span never calls
`PinOwner.check` and never re-enters the borrowed preparation guard;
`op.end` is anchored to the one absolute operation deadline clipped
to the request lifetime only while held and restored to its original
exact value in a finally before guard release on success, ordinary
refusal and interruption (witnessed by the expired-prior-acquisition
end returning in node 1 and by custody assertions in every node); the
private operation does not acquire, close or return ownership of the
input pin.

Criterion 3 (four genuine current observations at precisely named
cuts, exact scope, refuse throughout): O1, the scope refusal and O2
run before the first real catalog call (O1 after pure admission and
custody with no association/catalog/source I/O, then the genuine
isolated policy and captured membership scope rules, then O2 inside
the shared body after all earlier body validation); O3 runs after the
real dense output and before any real lexical call; O4 runs after the
final actual pin association/full revalidation and its post-load
association, before usable return, with the final exact authority
check (`_bound_grants` agreement) and the true remaining deadline. A
detected post-dense change means zero new lexical and fusion calls
(witnessed in node 2); the final comparison is against the
originally held `PinData`; expired budget and late usable results
refuse throughout (witnessed in node 6, part 2, at the genuine
late-completion cut of the delegated recheck).

Criterion 4 (one reuse of the actual engines, honest vocabulary, held
owner through association, fixed refusal and identity-preserving
interruption): the actual catalog, dense, lexical and fusion path is
reused once (node 1 witnesses eight catalog calls, sixteen full
directory validations plus the one distinct final full owner
validation, and result equality with the public legacy call on the
same supplied arguments); the legacy trace and output vocabulary are
unchanged; the owner is held through live root/store/content
association including the final full re-admission compared with the
exact held value; owner closure, creator mismatch, busy custody,
unavailable membership and pathname/capture drift are detected at the
relevant cuts (node 5 sub-cases); the fixed content-free
`HybridSearchError('hybrid search refused')` is the only ordinary
outward refusal and a non-Exception interruption object propagates by
identity (node 6, part 1).

Criterion 5 (exactly six default hosted integration nodes, existing
951 preserved, 3,370 + 957): the new file contributes exactly six
default nodes (capped collect-only witnesses 6/6 locally); no
existing integration file, fixture or workflow changed, so the 951
inherited cases and both Products' ordered A 1,440 / B 1,930 = 3,370
units run unchanged, with the integration total 957 at the report
head. All five required jobs and every existing step at the exact new
report head are Root's acceptance gate (pending; see Verification).

## Verification

Local (actual, this round; local hosted native test environment
absent, not installed and not simulated):

- One bounded unit focus of the four ordered files
  (`test_raw_hybrid_search.py` 15,
  `test_private_policy_pin_eligibility.py` 53,
  `test_private_policy_request.py` 45, `test_raw_snapshot_pin.py` 8):
  121/121 passed, exit 0 in 1.76 s.
- One capped collect-only of
  `tests/integration/test_private_pinned_hybrid_composition.py`:
  six nodes, exit 0.
- One targeted Ruff on the three changed Python paths on one
  process-local core: exit 0.
- One capped physical import-origin check: both product modules
  resolve to the canonical repository `src` with working-tree
  SHA-256 `7ba08bbd5b32df62c1270a29e30ca3e9e9c3784eedead0b883e4656d35e09309`
  (`raw_hybrid_search.py`) and
  `7dc89e5277032d2f3bb24143e3f878e6a5a85ccc46d514b35c37b418214daf3b`
  (`private_policy_pin_eligibility.py`).
- Every process proof used `timeout -k 5 120 prlimit --cpu=60
  --as=1073741824`, `OPENBLAS_NUM_THREADS=1`,
  `PYTHONDONTWRITEBYTECODE=1`, a fresh private 0700 directory
  directly under sticky `/tmp` with a private pytest basetemp
  subdirectory, `-o addopts= -p no:cacheprovider` where applicable,
  and captured the actual command exit without pipeline masking.

Hosted (expected, pending at report authoring): the six real
integration outcomes (positive journey with exact authority,
semantic identities and legacy-equivalent engine counts; post-dense
change latching before real lexical/fusion; revocation before
dispatch; change during the final owner validation; the five held-pin
refusals before engine work; interruption identity plus the actual
late-deadline cut) run only in the configured hosted jobs. Expected
at the exact report head: group A 1,440 and group B 1,930 unchanged
(3,370 units each Product), the separate 957-case integration (951
inherited plus the six new default nodes), and all five required jobs
(the two Product legs and the three OAP legs) with every existing
step. This report does not certify its own future push, checks or CI;
the round base's required hosted run 44781112453 attempt 1 passed
all five jobs and every step, and the fresh full hosted CI at the
exact report head is PENDING at report authoring, with Root owning
the fresh CI and terminal review. A separate post-publication
receipt verifies the remote publication facts.

## Documentation impact

`STATUS.md`: current-slice lead advanced 009-aa -> 009-ab (one
indent deeper, after the 009-aa line) plus a cumulative 009-ab slice
entry (exact source and integration scope, the four actual checks,
owner/deadline and dispatch semantics, local and pending hosted
evidence, open gates). `docs/evaluation.md`: new section
`## The 009-ab private pinned hybrid dispatch (same 009 continuation)`
with the same cumulative content. No other documentation changed.

## DHA and boundaries

Decision: NONE; no critical entry was appended or changed and the
register was not loaded. No merge was performed, no auto-merge
enabled, no release/tag/deployment, no order/active byte change
beyond the ordered activation, no duplicate PR (PR 11 amended), no
force push/reset/clean/stash; all unrelated files, private config and
worktrees preserved. No live network beyond the existing private
GitHub push and configured tests on this PR only; no protected data,
real corpus, credential, model or worker invocation; no outside
installation.

## Limitations and remaining work

- The six real integration outcomes are hosted-only and PENDING at
  report authoring; only the configured hosted jobs establish them.
- The lexical-to-fusion current-policy check remains an explicit open
  cut for this first synthetic seam (fusion's existing data scope
  checks still run).
- No evaluator, encoder, source grounding, serving, grade,
  publication, writer qualification or recovery entry is attached;
  the test-local atomic selector fixture provides no writer
  qualification.
- The representative baseline remains NOT_RUN; the governed operator,
  current durable writer, request execution, source rights, model and
  hardware gates remain open; whole 009 stays PARTIAL.
