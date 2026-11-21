# Private evaluation plan wire v1

`evaluation_plan_wire.admit` is a pure byte-admission boundary for private
evaluation plan wire v1. The module is under construction and exposes no
product interface: one public function `admit(raw: bytes)` returning the exact
existing `evaluation_program.Plan` with nested `evaluation_program.Judgments`
and tuples, plus `PlanWireError`. It performs no filesystem, clock, config,
artifact, pin, model, source I/O or resource acquisition. A parsed plan is a
declaration, never proof of current principal, rights, execution or relevance
meaningfulness, and it cannot manufacture qualified data or grades. The
governing specification is the final Root contract, copied byte-identical to
`docs/parallel/private-evaluation-plan-wire-v1.md`, under coding order
`oap/parallel/orders/PAR-009-PLAN-WIRE-A.md`; this document records the
implementation's reasoning, not new authority.

The accepted input is exactly one `bytes` object of length 1..8388608: no
bytes subclasses, no `str`, `bytearray`, `memoryview` or coercion of any
kind. The 8 MiB bound is a new
explicit wire-policy cap, distinct from the existing program's 8 MiB canonical
plan-identity encoding cap. It bounds wire representations, including
whitespace and escapes; it does not imply that every JSON spelling of an
admitted typed plan fits. Every existing maximum-semantic case/entry
configuration has a compact ASCII wire representation under this cap; the
unit evidence verifies the compact maximum-shape witness against the coarse
documented partition rather than asserting a tighter attained maximum.

Admission is exactly four layers. First, the exact type and length envelope.
Second, a single iterative pre-materialization scan over the admitted bytes:
nesting depth at most 6 (root depth 1, every nested value or container one
deeper), node count at most 196608 with every container, object key and scalar
counted exactly once and keys counted at the associated member-value depth,
quoted strings at most 770 raw bytes and 128 decoded codepoints, integer
tokens at most 20 bytes including an optional minus, ASCII-only raw bytes with
no BOM, DEL or non-ASCII byte, only the four JSON whitespace bytes outside
strings, strict token syntax with exact JSON escape recognition (an escaped
quote does not end the string; braces and brackets inside strings are not
structure), refusal of bool/null/float/exponent/nonfinite literal forms,
refusal of EOF inside a string, after a backslash or before four hex digits,
refusal of trailing commas, exactly one root object and no content after it
except allowed whitespace. The scan is iterative with a fixed frame stack
bounded by the depth cap; it uses no recursion proportional to attacker input,
no unbounded regex or backtracking, no whole token list, no decoded giant
integer and no nested Python container before the limits hold. Third, strict
`json.loads` with an object-pairs hook that refuses duplicate decoded keys;
its work is bounded by the lexical envelope already established, so the
decoder is a second check, not a substitute for the envelope. Fourth, final
exact schema validation against the twelve-key wire schema plus the existing
program entries and work admission arithmetic, with every case validated
before anything is returned.

The wire schema is the explicit top-level integer `schema` fixed to exactly 1
(bool excluded) plus the existing eleven Plan fields, exactly twelve keys;
unknown, missing or duplicate decoded keys refuse, with no last-key-wins and
no coercion. Escaped ASCII spellings decode and remain admitted within the
envelope, so a key spelled with a Unicode escape for an ASCII character is the
same decoded key and duplicates on decoded equality. The schema discriminator
is not a Plan field and does not enter the existing program identity; the
unit evidence checks this structurally and through real identity computation.
GradeBudget, source Budget and config, dataset bytes, bundle bindings,
path/store roots, principal/provider/grants/restrictions and
encoder/runtime/model/credentials/commands remain trusted runtime inputs
outside the wire; unknown-key rejection enforces that separation.

The finite allocation and copy argument is logical, not physical. The scan
touches the admitted bytes once, holds at most six stack frames and a few
counters, and constructs nothing; the later JSON construction and validation
allocate only what the admitted envelope permits, bounded by depth, node
count, string size, case count and gold-pair caps, and the returned
Plan/Judgments/tuple structure is bounded by the same caps. No tighter
attained wire maximum, zero-allocation property or hard RSS guarantee is
claimed anywhere in this module or its evidence.

Refusals raise `PlanWireError`, a `ValueError` subclass with `__slots__ = ()`,
whose message is exactly `private evaluation plan refused`; the refusal adds
no raw payload, key, path, hash, grade or other private attribute and no
partial result. Ordinary parser and schema exceptions are sanitized: the
refusal is raised after the routine-exception handler has left, with `from
None` suppression, so the boundary suppresses the caught internal exception
context instead of exposing it. This makes no traceback-memory guarantee:
normal Python traceback frames can retain locals, and no zeroization or
exposure claim about them is made, nor any no-caller-frame or ambient
caller-exception retention guarantee. `BaseException` object identity
propagates unchanged: `KeyboardInterrupt`, `SystemExit` and the controlled
test sentinels escape the broad `Exception` handling untouched. There is no
stdout, stderr or logging and no public identity on success or error.

Compatibility with the existing program is evidenced without making the
parser its own oracle: the unit module drives the actual
`evaluation_program._plan_admission` against a manually constructed exact Plan
and the wire-parsed Plan, and then a genuine controlled preflight/identity
path, using the real `source_cohort_runner._input_admission` over the
controlled fixture pin, data, queries and authority, then the real
`program._prepare` and `_State` computing the actual nonempty `plan_identity`
through the real `binder._canonical_hash`. That path mirrors the `run_cohort`
sequence up to, and excluding, any pin, source, native or model use; the
fixture's recorded lower delegates stay uninvoked, so the evidence is pure and
controlled, not actual-source qualification. Equivalent wire spellings of the
same decoded plan must yield the same identity, and a one-field semantic
change must move it, so the witness is not vacuous.

Construction-unreached regressions install a `BaseException` sentinel as
`json.loads` (a monkeypatched attribute of the real `json` module,
auto-restored, with no fake modules or `sys.modules` pollution): because the
sentinel escapes the implementation's broad `Exception` handling, any
over-envelope input that reached the general decoder would surface the
sentinel instead of `PlanWireError` and fail its test.

Status and limits. During the static coding stage no check, import,
collection or test invocation occurred in this lane. The first run was the
Root independent bounded check under a separate exact decision, executed by
Root's own operational parent; the lane's v1 parent was NEVER_RUN and is
preserved as history, so Root's execution is not coding's. That check
recorded ONE Ruff lint process (PASS, no source mutation) and ONE exact
frozen three-file pure unit process: 186 new parser plus 44 existing
evaluation plus 54 existing runner cases, 284 passed in 13.64 s, no skip,
xfail or xpass, all 84 frozen identities matched pre and post, and the
worktree remained exactly the five NEW paths at the e3bf base. The complete
31377-byte unit log SHA-256 is
`20f38c2b32961851684099d1fabafcf042c2e7722d2d6836242390cfcb42496b`.
Resource observations were waited-child CPU user 13.871513 and system
0.179967 seconds, wall 14.206 s and a waited-children RSS high-water of
122604 KiB (Linux high-water, not an additive, delta or aggregate allocation
cap); runtime and entrypoint identities are representative, and OS, stdlib,
third-party and native-loader closure was not measured. These pure controlled
offline results do not establish current policy or principal, the actual CLI
or operator, qualified data, a real encoder, a representative baseline or the
full MVP. The actual CLI and operator remain ABSENT; `search_pinned_data`
already encodes
and retrieves and returns no reusable vector and must not be chained as an
imagined vector-producing adapter before `run_evaluation`. No
partial or surviving-subset report and no fake successful baseline exist; a
dry run is not evaluate completion. Numeric009 remains OPEN, the baseline
NOT_RUN, and the current-policy, operator and qualification gates OPEN. DHA
NONE. This contract, document and code authorize no activation, acceptance or
invocation.
