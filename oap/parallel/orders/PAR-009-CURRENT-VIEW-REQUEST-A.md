# OAP parallel work order — PAR-009-CURRENT-VIEW-REQUEST-A

Status: FINAL — isolated local development candidate.
Lane: current-view-request. Pane: %33.
Base: 6e8922c6a35de57ed19a70ed3a5aca59e4b7a68a.
Branch: oap/parallel-009-current-view-request.
Transport: isolated worktree, no remote push or PR.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922
Source inputs SHA256: 891ecb6390171455dc57b6c791974c578ae90cfc08c1f2804c5bf9ee19ec63bc.
DHA: NONE.

Provenance H activated MVP, A ARCH 13.1–13.4/A23/A24, E admitted
capture and exact matcher have no shared request entry, I finalized
read-boundary audit and Root local capture/wire acceptances. Canonical
objective 009 remains active in PR #11. This isolated development
slice uses only the exact audited component implementations.

## Exact candidate scope

Use candidate base `6e8922c6a35de57ed19a70ed3a5aca59e4b7a68a`, the
accepted capture implementation, with one native exact clean preparation
merge of `899465220ac2108388845d6926209448f41fdadb`, the accepted wire
implementation including the accepted typed dependency. Preview tree
`01c91d3d8f2440c378f2050a2255f4547c09d050` verified the exact
capture, selection, publisher, typed and wire source bytes. The exact source index above controls. Verify clean native merge and
first/second parents before code. Report the full commit under
preparation_heads. No manual merge resolution.

Candidate implementation paths are a new private
`src/slaif_raggedized_helper/private_policy_request.py`, a new focused
`tests/unit/test_private_policy_request.py`, and the original final
parallel order copy. Exact existing dependencies and public supplied
policy behavior are preserved. The new private entry performs only
selected-view admission, credential match and freshness observation.

## Acceptance outline

1. Use an exactly admitted `PolicyCaptureReader` owned by trusted
   operator initialization. Creator-process ownership and serialization
   protect freshness/refusal state. Acquisition or owner conflict refuses
   that call. A latched mismatch remains invalid under concurrent use. No root path, arbitrary selector, caller
   callback, view bytes or match DTO accepted in the request entry.
   Use its real `capture()`, `admit_policy_bytes()` and `match_supplied()`
   with exact required operations `("search", "sources:read")`.
   Bind an internal request record to the same reader, exact selected
   record bytes, independent semantic identity and admitted principal
   match. Avoid retaining the raw credential after matching. Any
   externally visible failure is fixed and content-free. Preserve
   system interruption and owned reader cleanup semantics.
2. Use one bounded monotonic request deadline. Cap calls by current
   remaining time and the accepted reader caps, check after capture,
   decode, match and final reread, and refuse late usable success.
   A fresh actual `read_selection()` after decode/match compares exact
   publication identity before the entry can yield private admission.
   Recheck only via that same genuine bounded reader and same exact
   selector. A changed generation, changed bytes, malformed or absent
   selection, or an expired operation refuses the entire request and
   prevents later reuse of that admission even if a record is restored.
   A separate request may capture a new view. A retained match is
   evidence from the earlier verified immutable selected identity.
   This scope measures observations, with a trusted monotonic-generation
   writer protocol still required to rule out undetected reversal.
3. Positive proof with an actual synthetic private root must invoke
   the real reader, wire decoder and matcher, retain expected identity
   and observe repeated stable selection. Count one full wire admission
   per successful request and only bounded selection rereads later.
   Negative witnesses include unknown credential and missing operation,
   exact bytes with a different selection generation, same semantic view
   at a new selected publication, changed pointer during decode,
   observed denial then restoration, a separate successful new request,
   missing/malformed selection, actual remaining-clock lateness,
   non-nominal owner/view inputs and invalid request reuse.
   Use counted wrappers that delegate real functions at the intended
   boundary. Compare stable and refusal paths so a permanent refusal
   cannot qualify. Keep timing, cleanup ownership and caller-visible
   errors precise, including unusable admission when the final reread fails. Check nominal state and origin under the actual
   test location. Protect all nonsynthetic credentials, roots and data.
4. Use one targeted Ruff and one focused pytest command, exact selected
   physical worktree imports, existing locked venv, fresh private
   scratch, CPU 60 s, AS 1 GiB, wall 120 s plus 5 s kill grace,
   scoped one-thread Product setting. Keep commands, actual statuses
   and raw outputs. Use the exact implementation checkpoint with the sole owned
   implementation_cycle.py helper. Await consumed FIX or REPORT. After
   REPORT, one immutable report-only SELF child and the established
   owned lane response. Report actual setup failures and exits. No
   extra runner, network, GitHub write, push, PR or integration.

Actual evaluation orchestration, pinned membership eligibility and policy
writer, current authorization at model/engine/source or publisher
dispatch, real credential use, broad runtime qualification, deployment
and acceptance remain outside this proposed implementation.
