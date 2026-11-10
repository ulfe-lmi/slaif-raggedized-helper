# Governance projection map — architecture revision 2.0

Canonical full source: ARCHITECTURE.md, SHA-256 `4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a`.
The human requested this direct strategic rewrite. Source PLAN/UPDATE bytes remain unchanged;
UPDATE precedence and stable A01–A40 meanings are preserved. The compact projection carries
both original requirement groups and concrete implementation contracts V2-01–V2-08.

| Obligation | Full architecture sections | Compact original group | Semantic coverage and new detail |
|---|---|---|---|
| A01: Local documentation retrieval/answering product and explicit non-goals | 1, 3 | A01–A04 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A02: Corrected online/offline CPU/GPU topology and preserved long-context profiles | 2, 5, 19 | A01–A04 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A03: Small service composition and explicit component ownership | 4, 5, 6, 20 | A01–A04 | Concrete process/module/interface ownership added; V2-01 carries the selected implementation baseline. |
| A04: License policy, exact model/runtime provenance and transitive audit | 24 | A01–A04 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A05: Source identities, rights, access metadata and representative inventory | 3, 7, 9 | A05–A12 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A06: Structure-preserving native extraction | 9, 18 | A05–A12 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A07: Blocks/chunks with exact original evidence and separate context | 7, 15 | A05–A12 | Exact code-point span semantics, copied fragments and separate derived records are retained in V2-02. |
| A08: Independent generator/embedding/reranker/lexical accounting | 9, 11, 14, 15 | A05–A12 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A09: Structural chunk/enrichment budgets without silent truncation | 9, 10 | A05–A12 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A10: Parent-aware contextual retrieval and long-document adaptation | 10 | A05–A12 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A11: Context validation, rejection and restrictive support permissions | 7, 10, 13 | A05–A12 | Pre-generation parent-access compatibility and cross-boundary rejection are explicit in V2-04. |
| A12: Durable job fingerprints, resume and dependency invalidation | 8, 10, 21 | A05–A12 | Artifact-before-completion ordering, fingerprints and ambiguous-call recovery are explicit in V2-02/V2-03. |
| A13: Semantic generator interface and honest available metrics | 6, 17 | A13–A18 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A14: Qualified gateway Responses online contract | 16, 17, 23 | A13–A18 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A15: Private direct offline adapter and measured prefix-cache correctness | 10, 17, 23 | A13–A18 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A16: One qualified embedding space across CPU/GPU precision paths | 8, 11, 23 | A13–A18 | Shared encoder identity is separated from CPU/GPU execution precision; qualified pairing retained in V2-02. |
| A17: Independent technical BM25 and exact dense retrieval | 11, 14 | A13–A18 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A18: Validated immutable snapshots and atomic reader-consistent publication | 12, 21 | A13–A18 | Validated directory publication, pointer generation and request-pinned snapshots are explicit in V2-03. |
| A19: Rank fusion, bounded candidates and recall-loss accounting | 14, 23 | A19–A26 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A20: Private GPU FP16 reranker with bounded validated work | 5, 14, 16 | A19–A26 | Private IPC, exact bounded pair IDs, finite scores and independent worker validation are explicit in V2-01/V2-06. |
| A21: Original supporting evidence and complete generator budgeting | 15 | A19–A26 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A22: Grounded multilingual answers, bounded conversation and honest failure | 15, 16 | A19–A26 | Bounded history/retrieval, final validated answer and upstream-versus-public streaming distinction retained in V2-06. |
| A23: Authenticated reader API and private operator boundary | 13, 16, 20 | A19–A26 | Concrete authenticated routes, private operator boundary and high-entropy token verification are explicit in V2-05/V2-06. |
| A24: Authorization before exposure, source rechecks and cache isolation | 13, 14, 22 | A19–A26 | All-label partitions, policy epochs, conservative restriction during rebuild and source/output rechecks are explicit in V2-04. |
| A25: Untrusted source/model isolation and bounded extraction | 9, 17, 22 | A19–A26 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A26: Privacy, safe logs and stage-specific observability | 22 | A19–A26 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A27: Physical-GPU ownership, safe transitions and recovery | 19, 21 | A27–A31 | Physical ownership, cooperative-lock limit and exact controlled supervisor transitions retained in V2-01/V2-07. |
| A28: Readiness, finite admission, cancellation and explicit degradation | 14, 16, 19 | A27–A31 | Single-pipeline baseline, queues/cancellation/degradation and non-inference readiness polling retained in V2-01/V2-06/V2-07. |
| A29: Actual memory/latency/concurrency qualification and fallback choice | 23 | A27–A31 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A30: Audited targeted visual extraction with original provenance | 18, 24 | A27–A31 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A31: Text-first visual retrieval and original-image answers | 18, 23 | A27–A31 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A32: Human-authored representative evaluation and held-out discipline | 23 | A32–A40 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A33: Controlled ablations and retrieval/support/performance metrics | 23 | A32–A40 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A34: Update/delete/revocation propagation, backup and rollback | 8, 13, 21 | A32–A40 | Withdrawal/rebuild, pinned references, restore/GC and authorization independent of rollback retained in V2-03/V2-04. |
| A35: Explicit profiles, operator CLI and qualified deployment settings | 5, 20 | A32–A40 | Concrete configuration/CLI/process boundary retained; exact implementation excerpts are order-scoped. |
| A36: Early environment/feasibility gates and named live experiments | 23, 25 | A32–A40 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A37: Meaningful layered tests and honest evidence classification | 23, 25 | A32–A40 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |
| A38: Separate human/strategic/coding authority and provenance-backed work | 4, 25 | A32–A40 | Product/development separation retained; full strategic decision/merge law stays in its constitution. |
| A39: Readiness distinctions, deferred judgment and independent closure audit | 25 | A32–A40 | No rewrite-as-implementation claim; ICA and human target gates remain separate from scaffold CI. |
| A40: Protected resources and non-delegable deployment/service boundaries | 19, 20, 22 | A32–A40 | Original obligation and its conditions/refusals retained in the compact group; detailed implementation explanation stays in the full source. |

## Operational law projection

| Full strategic/operational source | Coding obligation |
|---|---|
| Strategic S01/S10 | C01 source/projection discipline; current source digest and bounded excerpt correction |
| Strategic S03/S07 and decision policy | C02/C03/C05; no self-authored D1, no human-gate acceptance or D2 crossing |
| Strategic S04/S05 and communication | C02/C06; exact active selector, immutable order, same PR and no self-assignment |
| Strategic S06 | C04/C06 evidence and immutable report duties; coding never merges |
| Strategic S08 | C07/communication recovery without replay, competing readers or human-quit resurrection |
| Strategic S09 | C04/C07 honest scope/readiness; independent milestone assessment remains outside coding acceptance authority |
| SECURITY S01–S06 | Always-loaded security boundaries plus compact product enforcement points |
| TESTING T01–T06 | Always-loaded synthetic/live distinction, negative behavior, exact evidence rules, and the controlled loopback HTTP/SSE real-route test boundary |

## Semantic self-review and limits

Reviewed by the strategic author against both supplied specifications: corrected hardware and
adapter defaults; original-versus-derived evidence; tokenization/budget boundaries; source rights
and ACL before model exposure; state/fingerprint invalidation; restore/cancellation behavior;
license and held-out evaluation gates. The new process/data/API decisions are implementation
elaborations identified as such in SOURCE-MAP, not fabricated installed capabilities.

The author inspected the component, lifecycle, interface and rationale treatment in local
Agent-Site, Asset Reservation, Local Coding and Slovenian Repair architectures. No coding agent
or delegated writer prepared this revision. This is self-review, not independent review or ICA.
Mechanical hashes, link checks and tests establish consistency only; product behavior and real
hardware remain unqualified. A future work order must request relevant bounded full-source
sections where detailed schema/wire implementation exceeds the routine compact projection.
