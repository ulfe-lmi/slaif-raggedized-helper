# Development decisions and deferred human adjudication

D0: reversible ordinary engineering within A01–A40; decide/test/document and continue.
Examples: local file schema versioning, CLI parser choice, bounded queue implementation.
D1: consequential choice remains unresolved after investigation but can be implemented safely
and reversibly in confined development. Decide, mitigate/test and record exact judgment debt.
D2: real protected service/GPU/profile changes, live inference without scoped allowance, private
corpus use, credential/authority changes, irreversible source purge, external exposure, license
exception, release/deploy or redefinition of human product intent. Stop before that boundary;
continue independent authorized preparation. An open D1 entry never waives an A24/A40 invariant.

Admit a CRIT entry only if ALL are true: (1) existing human/governance/evidence does not decide;
(2) investigation yields materially different credible alternatives requiring a choice;
(3) error materially affects security/privacy/authorization/integrity/trust/exposure/deployment/
release; (4) a provisional choice can be tested without D2; (5) a competent human might reject
or materially change it before its exact gate. TODOs, bugs, routine choices, unknown benchmark
numbers and speculative issues belong in ordinary work/evidence/uncertainty records.

Strategy assigns stable CRIT-NNNN and authors dilemma, decision, reasoning, alternatives,
strongest counterargument, assumptions, blast radius, evidence/mitigations, rollback, exact
safe continuation, human gate/question and five-condition attestation. It names an existing
introducing PR; otherwise create safe prerequisite PR and then finalize same-PR continuation.
Every final order declares NONE or exact APPEND. Coding appends exact bytes, never authors it.

Register history is append-only in spirit and byte-preserved by helpers. Evidence/mitigation
append is distinct from new D1 admission and cannot close gates. Only latest attributable
human ACCEPTED clears its registered scope; REJECTED, CHANGE REQUIRED and DEFERRED block.
No name/checksum alone proves a human action. Initial automatic gate clearing is disabled:
human signing trust is not configured. The runbook describes externally signed dispositions;
agents cannot manufacture human signatures. Explicit human instructions remain authoritative,
but any recorded disposition must preserve their actual evidence and scope without invention.
