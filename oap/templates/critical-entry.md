# Exact payload template — NOT a live entry

Use the following heading/fields in an unfenced finalized order payload between
`<!-- OAP-CRITICAL-BEGIN -->` and `<!-- OAP-CRITICAL-END -->`. Hash the exact UTF-8
payload including its final LF. Include `Critical prior SHA256` and `Critical payload SHA256`
in order metadata. The helper validates structure, not substantive judgment or human approval.

```text
## CRIT-0001 — Specific consequential choice
- Status: OPEN — HUMAN ADJUDICATION REQUIRED
- Introduced by: PR #123 / OAP objective 001-b
- Category: security
- Severity: medium
- Decision confidence: medium
- Required human gate: before controlled pilot
- Affected components: exact components
### Dilemma
Unresolved consequential choice after investigation.
### Decision taken
Exact provisional choice.
### Reasoning
Why appropriate for this stage.
### Alternatives considered
Materially different credible alternatives.
### Strongest argument that this decision is wrong
Substantive counterargument.
### Assumptions
Required truths and evidence.
### Failure mode and blast radius
Concrete failure and affected assets.
### Mitigations and evidence
Implemented/ordered controls and proofs.
### Reversibility and rollback
How to change course and cost.
### Safe autonomous continuation
Exact safe work and blocked actions.
### Exact human gate
Precise exposure/data/deployment boundary.
### Exact question for the human adjudicator
Specific later judgment.
### Strategic attestation
ALL FIVE CRITICAL-ENTRY CONDITIONS SATISFIED
### Human disposition
PENDING — append separately.
### Resolution
PENDING — only latest attributable human ACCEPTED can clear the registered gate.
```
