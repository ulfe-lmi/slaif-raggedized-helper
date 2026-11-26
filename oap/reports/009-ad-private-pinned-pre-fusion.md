# OAP Coding Report — 009-ad

Identifier: 009-ad
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: f82a3a23ea6b2e4cddd52479bee0a61b4c53a4bf
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-ad-private-pinned-pre-fusion.md` (FINAL;
AMEND_EXISTING_PR 11; Decision: NONE; order file SHA-256
`7fd4e557cf5f711f5db4851bed460c5a54a9445a890bda8147c93d929eec8fdc`,
byte-identical to the strategic workorders copy) at round base
`00743eca3c351d57e45ec81004f52e519ebec00a` (the accepted 009-ac
report-only head whose required hosted run 44803828473 attempt 1
passed all five jobs and every step, each Product at 3,438 ordered
units and the separate 957-case integration; main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b` exact). Objective: add the
genuine current selected-policy observation at the existing private
pinned hybrid boundary after lexical and before fusion, using the same
current request, live borrowed owner guard and one absolute deadline
in the shared hybrid body, keeping the existing engine calculations
and final owner validation.

History published in this round (one normal push to the same PR branch,
no force push, no merge, one PR):

1. `2fadfc810cfc7cd8e72e01b9944a8beda0976c1c` (parent: round base
   `00743eca`) — exact Root transcript, four paths: `oap/active`
   (`009-ad` + LF, 7 bytes),
   `oap/orders/009-ad-private-pinned-pre-fusion.md` (the FINAL order
   above, 6,864 B, SHA-256
   `7fd4e557cf5f711f5db4851bed460c5a54a9445a890bda8147c93d929eec8fdc`)
   and the two indexed JSON control files copied byte-exact by
   basename: `oap/reviews/009-ad-pre-fusion-source-inputs.json`
   (7,654 B, SHA-256
   `f96c34ccf65dbb8fc2495b0e6c5c8e6a839d3dd2a2c994004d472b620763878e`)
   and `oap/reviews/009-ad-prior-resolution.json` (1,264 B, SHA-256
   `30bbdcc88205cb72e7db51ce3a7fc54b8edda980e29744f47086afb020a11b00`),
   each re-verified at its indexed SHA-256 after copy.
2. `f82a3a23ea6b2e4cddd52479bee0a61b4c53a4bf` (parent: 1) —
   implementation, exactly the four ordered paths:
   `src/slaif_raggedized_helper/raw_hybrid_search.py` (SHA-256
   `6fb2996429b1ec22bb0b324f9c6a4d05f62b3af58c8103b3324a61401b3ba098`),
   `tests/integration/test_private_pinned_hybrid_composition.py`
   (SHA-256
   `3177224a4fb2b200859a1e05afe06b42e313802202b4b912cfb99d0e53651581`),
   `STATUS.md` and `docs/evaluation.md` (short cumulative notes).
   Everything else — the engine and fusion APIs, the policy
   request/reader/installer/writer, the pin helpers, the earlier
   source and test files, the workflow, the CI partition and every
   caller-facing signature — stays byte-exact; no relabeling of prior
   immutable evidence and no other product path or output envelope
   changes.

## Implementation

Within the one shared `_search` body, after the actual lexical
response validation and the optional trace links and before the first
real `fusion.fuse`, the existing private owned path (`owner is not
None`) now performs a single genuine current observation — the fourth
ordered cut O4 — of the current selected policy through the existing
`pin_eligibility._genuine_recheck(admission, end)`: the same current
request, the live borrowed owner guard and the one anchored absolute
deadline clipped to the current request lifetime (never reset or
extended), with the remaining budget checked after it (`remaining()`).
The existing private refusal is used on a detected change, refusing
with zero new fusion, catalog or directory calls; no second retrieval
happens. The earlier three checks (O1 after pure admission,
nonblocking owner custody and in-memory capture verification; O2 after
verified scope and actual association before the first real catalog
call; O3 after real dense before any real lexical) are unchanged, and
the final check after the actual association/full owned reload and
detached authority and deadline is preserved, now documented as the
fifth ordered cut O5; the `search_pinned` docstring records the five
ordered cuts.

The integration file gains exactly one default hosted node,
`test_post_lexical_change_latches_before_fusion`: after the actual
lexical succeeds it publishes the same synthetic wire under a new
generation via the existing attributed test-local fixture
(`_publish_selection` generation 2 over identical payload bytes) and
attests four genuine selected observations (O1–O4, the last one
observing the change), one actual dense, one actual lexical, five real
catalogs and ten complete directory loads before refusal, zero new
fusion, zero final owned load (counted `owner._load` wrapper), no
usable result, the old admission latched invalid — a later latched
`recheck` refuses with zero further reader calls, without inferring
recall of prior reads — the original owner deadline restored and the
guard released. Only the minimal helper extension was made: the
existing `_install_witness` counting wrappers gained the
`after_lexical` hook mirroring `after_dense`. The six inherited nodes
and their phase checks are preserved; only the stable positive
(`test_pinned_positive_journey_matches_legacy`) and the actual
final-owner-change (`test_final_owner_validation_change_refuses_
usable_return`) read counts move from four to five, while the genuine
positive eight catalogs and seventeen directory loads (including the
distinct final owner load) and the legacy output equality stay exact.

## Acceptance evidence

1. Exact clean canonical and unique remote PR base, regular prior
   response and terminal proof, every indexed base dependency and
   exact transcript bytes: local HEAD equals the ordered round base
   `00743eca` and the exact remote branch head; live main is
   `5a7b41cc` exact; PR 11 is the unique open non-draft PR, base
   `main` `5a7b41cc`, head `oap/009-evaluation-baseline` `00743eca`,
   no auto-merge, no review threads; the round-base required hosted
   run 44803828473 is completed/success on that exact head (Root's
   terminal review verified all five jobs and every step, 3,438
   ordered units and 957 integration each); the regular prior receipt
   `.oap-state/response-consumed-009-ac.json` (347 B, SHA-256
   `06dc5c7cfb2a13cd2bae4b3d1948192a183a987b0cebccc3182fb27701ba0c92`)
   and all four indexed strategic files match their ordered SHA-256s
   (`f96c34cc…`, `30bbdcc8…`, `d46cf4e6…`, `8fce85ad…`); all 26
   indexed base dependency objects were verified exact at the round
   base (mode 100644, blob OID, byte count and SHA-256 per the source
   inputs); `oap/active` is exactly `009-ad` + LF (7 bytes) and the
   order file is byte-identical to the strategic workorders copy. No
   concrete drift; reconciliation stopped nothing.
2. One genuine current observation at the new pre-fusion cut, same
   request/guard/deadline, existing refusal, no second retrieval, five
   ordered cuts documented, earlier three checks and the final owned
   validation preserved: see Implementation above; the shared body's
   engine calculations and final owner validation are byte-identical
   except the inserted O4 block and the O4→O5 rename of the final
   check's comment, and the public `search`/`search_pinned`
   signatures, normal deadline and outcomes are unchanged.
3. Exactly one new default hosted node with the ordered causal
   mutation and counts, six inherited nodes and phase checks
   preserved, only the two ordered read counts moved: the diff adds
   one node plus the `after_lexical` witness hook and the two
   `counts["read"]` assertions 4→5; all other assertions are
   unchanged. Expected exact report-head gate: ordered hosted Product
   units unchanged at 3,438 each (A 1,440 and B 1,998), separate 958
   default integrations each, both Products, all three OAP jobs and
   every prior required step passing.
4. The exact report-head hosted gate is owned by Root and is PENDING
   at report authoring (item 3 counts); pending jobs are pending at
   report authoring — this report does not certify its future push or
   checks, and no expected test result is claimed as having run
   locally.

## Verification

Local (actual, this round; all process proofs under `timeout -k 5 120
prlimit --cpu=60 --as=1073741824`, canonical `.venv` (Python 3.14.4),
physical canonical `src` via `PYTHONPATH`,
`OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`, fresh mode-0700
scratch `/tmp/oap-009ad-proof.piHtyL` directly under sticky `/tmp`,
private pytest basetemp subdirectory, raw logs outside the basetemp,
`-o addopts= -p no:cacheprovider`, actual exits captured without
pipeline masking; command record `commands.txt` SHA-256
`bbd5e3f8059ead14e4fa771d3d649725fea60e537f10eff2ce8c5637902befb8`,
probe `origins-probe.py` SHA-256
`17dcfa9ebea55a1bdd65675b95307d916746e6e52df2656568635b858a67a743`):

- RUN1 one bounded inherited focus of the four ordered unit files
  under `tests/unit/` (`test_raw_hybrid_search.py` 15,
  `test_private_policy_pin_eligibility.py` 53,
  `test_private_policy_request.py` 45, `test_raw_snapshot_pin.py` 8):
  121/121 passed, exit 0 in 1.76 s; raw streams `pytest.out` 180 B
  SHA-256 `b2c2ae8e2de441ff814446a9e8b0bb974cd3a11851389870ac87950f6641740d`,
  `pytest.err` empty.
- RUN2 one capped collect-only of the seven hosted nodes in
  `tests/integration/test_private_pinned_hybrid_composition.py`:
  7 tests collected, exit 0; raw streams `collect.out` 782 B SHA-256
  `64d87cab42af2619d6db5934aabc6e8cbacb8b579306520a53a0215643e148b2`,
  `collect.err` empty.
- RUN3 one targeted Ruff on the two changed Python paths on one local
  core (`taskset -c 0`): exit 0, "All checks passed!" (raw `ruff.out`
  19 B SHA-256
  `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`,
  byte-identical to the prior rounds' Ruff digest; `ruff.err` empty).
- RUN4 one bounded physical product import-origin probe: the changed
  module `slaif_raggedized_helper.raw_hybrid_search` resolves to the
  canonical repository physical `src` with working-tree SHA-256
  `6fb2996429b1ec22bb0b324f9c6a4d05f62b3af58c8103b3324a61401b3ba098`,
  ORIGINS_OK, exit 0 (raw `origins.out` 223 B SHA-256
  `ef4f34fc532b954e98b7927581890ff3e3b95d9b099543d485bda884e437016d`;
  `origins.err` empty).

No full local suite, no repeated unchanged proofs, no native proof
execution, no substitute, no install or other setup ran locally (the
actual native fixture is hosted-only; the local native test
environment is absent, was not installed and was not simulated). No
first failure occurred this round, so nothing was preserved beyond
the recorded raw streams.

Hosted (expected, pending at report authoring): the seven real
integration outcomes in the touched file (inherited six plus the new
post-lexical pre-fusion negative node) run only in the configured
hosted jobs; the exact report-head gate requires ordered hosted
Product units unchanged at 3,438 each (A 1,440 and B 1,998) plus the
separate 958 default integrations each, with the other three OAP jobs,
both Products and every prior required step; Root owns that fresh
hosted review. The round base's required hosted run 44803828473
attempt 1 passed all five jobs and every step. This report cannot
certify its future push or checks; a separate post-publication
receipt verifies the remote publication facts.

Mock/live distinction: all fixtures and roots are synthetic and
operator-owned; no live model request, network, real policy root,
credential, GPU or hardware was used, and no actual current
authorization invocation happens outside the synthetic
wire/selector fixtures.

## Documentation impact

`STATUS.md` current-slice lead 009-ac -> 009-ad plus the 009-ad slice
entry, and `docs/evaluation.md` new "The 009-ad private pinned
pre-fusion cut (same 009 continuation)" section: the five ordered
cuts including the new pre-fusion O4 and the preserved final O5, the
actual negative cut (same synthetic wire under a new generation after
the real lexical, four genuine observations, five catalogs, ten
directory loads, zero fusion/final owned load before refusal), the
inherited positive controls (six preserved nodes, only the two ordered
read counts 4->5, positive 8 catalogs / 17 directory loads and legacy
equality unchanged), the exact local verification and the pending
hosted gate. Evaluation/source/grade/delivery, rights, the governed
live operator, the encoder and the representative baseline stay open;
whole 009 PARTIAL and baseline NOT_RUN are recorded.

## DHA and boundaries

Order Decision: NONE; no `append_critical.py` invocation, no CRIT
entry added or touched, no consequential D1 candidate reported this
round. Preserved: the prior report archive and transcript objects,
all 26 indexed base dependencies byte-exact, the unrelated worktrees
and branches, the workflow and CI partition, the existing
Qwen/gateway services, and the canonical worktree's synthetic
temporary fixtures only. No merge, no auto-merge, no force push, no
new PR, no release/tag/deploy, no branch merge/cherry-pick, no direct
FIFO access, no credentials, no real data, service or hardware use,
no outside setup, no model/profile change, and no nested/helper
agents; the sole external control wrapper's consumed notification was
not re-read.

## Limitations and remaining work

No actual first failure occurred in this round's proof. The seven
real integration outcomes, including the new node's exact counts
(five catalogs, ten directory loads, four reads before refusal), are
hosted-only and unproven until the exact report-head hosted run
passes; this report attests collection and the bounded local checks
only. The pre-fusion cut is synthetic: it does not qualify real
selection roots, guarded encoding, fusion/current delivery,
evaluation source cuts or the representative baseline. Strongest
residual limitation (unchanged from 009-ab/009-ac): the fixed
reserved staging path can remain occupied after an uncertain attempt
or restart, blocking a later selection pending separate
operator-authorized recovery, and the observation cuts are
cooperative deadline checks between steps — they cannot preempt a
running operation. No merge; baseline NOT_RUN; whole 009 PARTIAL.
