# OAP parallel work order — PAR-009-ENCODER-DECLARATION-PREFLIGHT-A

Status: FINAL — isolated local development candidate.
Lane: encoder-declaration-preflight. Pane: %32.
Base: 416009c94a6759c9a42e9c19dab688c0f54d9650.
Branch: oap/parallel-009-encoder-declaration-preflight.
Transport: isolated worktree, no remote push or PR.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922
DHA: NONE.
Source inputs SHA256: 50f345dc340adbe9f108e7ec35c71a5f378f46070759b92634e9e7d558de04df.

Provenance H activated MVP; A ARCH 13/A23/A24; E old binder mixes
declaration and encoded queries; I AUDIT-009-ENCODER-PREFLIGHT-SEAM-A
draft SHA256 62d4552aab04327049f0dfaeb9d930f51a7625229ab63b42be6c9c246367eab6
and Root-review-62d4552a.json. Original source anchor
416009c94a6759c9a42e9c19dab688c0f54d9650. Root reverified the exact
audit and indexed bytes against the activation base.

## Objective

Extract only the binder's shared query-independent admission for the
real root, dataset envelope, case ID, Gold IDs, encoder declarations
and deadline. Provide a private entry that accepts these actual
declarations and the caller's meter without accepting a query or
payload. Preserve the existing binder entry and old caller behavior.
This slice is a prerequisite for all-case preparation, with later
source/grade preparation, encoder/current-policy checks and dispatch
outside scope.

## Implementation scope

New isolated local candidate, no push, and own implementation review
helper. Only src/slaif_raggedized_helper/source_bound_stage_loss.py,
tests/unit/test_source_bound_stage_loss_preflight.py, and the exact
ordered OAP order copy. Existing source-cohort runner, grade program,
tests, package exports, product docs and workflow unchanged. No
engine, auth integration, storage access, protected data or real
encoding. Synthetic declaration shapes and synthetic payloads for
legacy compatibility only.

## Acceptance

1. Keep the exact private legacy binder signature/callers. The existing
   mixed shape gate at 531–547 performs original checks before its
   first metered canonical validation. Preserve old left-to-right
   payload shape relative to root/data/case/Gold/deadline/IDs. A
   malformed old-path None must fail as before. An explicit private
   mode/sentinel may express omission internally if needed. Do not
   use an invented vector to express absence or accept a public
   mode. The private declaration entry has no payload argument.
2. Reuse the same root UTF-8/path limits and bounded grammar,
   case ID and exact increasing Gold ID sequence, and actual
   declared identifier shape/grammar. Preserve exact admission
   bounds, relative check/reserve order and use of the supplied
   meter. The declaration path stops before vector reservation,
   struct unpack, vector finite/norm checks or any dependency/source
   access. It establishes identifier grammar, not provenance or
   equality with real encoded outputs. Keep the real legacy check
   over 4096-byte finite unit-vector data and same reserve order.
3. Add concise synthetic tests using real meter or delegated spy
   primitives. Independently establish before/after equivalence
   using exact legacy source as reference for selected hard-coded
   event order and charges, without running a second copy of the
   algorithm in committed tests. A valid declaration yields the
   same metered prefix as the valid old caller. Independently test
   no vector work in the declaration path and actual metered vector
   work in the old path. Include None and foreign payload type,
   nonfinite or bad norm, bad path/Gold/identifier and a budget
   refusal before a guarded operation. Use observed meter/check
   boundaries and concrete exception points; shared public error
   text is insufficient evidence of preserved precedence. New
   tests' binder import must originate from the assigned worktree.
4. Targeted Ruff and one bounded selected run including the new
   test module plus exact existing
   tests/unit/test_source_bound_stage_loss.py::test_input_preflight_rejects_bad_types_and_nonfinite_payload.
   Existing canonical locked venv with candidate src as import
   origin. Private fresh temp, CPU60s AS1GiB wall120s + KILL5;
   keep true output/exit. One changed-byte correction for an
   actual assertion failure under the same bounds is authorized.
   No broad unit, integration or dynamic source fixture execution.
5. Sole-parent clean implementation on the confirmed base, initial
   proof and exact source hashes preserved. Request exact
   implementation review and wait for FIX or REPORT. Report-only
   immutable SELF child and one normal local response only after
   REPORT. No canonical FIFO or prior lane reader.

No claim about full pre-encode preparation or actual evaluation,
data access, held-out baseline, encoder/model, current authority,
hardware, source/release/production or ICA qualification.
