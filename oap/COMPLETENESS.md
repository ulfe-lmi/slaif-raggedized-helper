# Architecture coverage, not queue completion

Architecture revision 2.0 explains the product in component, data, interface, lifecycle and
qualification sections. A01–A40 remain stable references in its Appendix A. The machine-readable
matrix is `audit/requirements.json`; section references below locate the actual design.
Classification remains UNPROVEN: this rewrite is not an independent product audit. Full original
source specifications remain audit scope, even where an objective list omitted a requirement.

| Requirement | Obligation | Architecture sections | Planned objectives | Classification |
|---|---|---|---|---|
| [A01](../ARCHITECTURE.md#a01) | Local documentation retrieval/answering product and explicit non-goals | [1](../ARCHITECTURE.md#product), [3](../ARCHITECTURE.md#workflows) | 002, 014, 019, 020, 021 | UNPROVEN |
| [A02](../ARCHITECTURE.md#a02) | Corrected online/offline CPU/GPU topology and preserved long-context profiles | [2](../ARCHITECTURE.md#decisions), [5](../ARCHITECTURE.md#deployment), [19](../ARCHITECTURE.md#gpu-lifecycle) | 001, 004, 015, 020 | UNPROVEN |
| [A03](../ARCHITECTURE.md#a03) | Small service composition and explicit component ownership | [4](../ARCHITECTURE.md#context), [5](../ARCHITECTURE.md#deployment), [6](../ARCHITECTURE.md#modules), [20](../ARCHITECTURE.md#configuration) | 002, 018, 020 | UNPROVEN |
| [A04](../ARCHITECTURE.md#a04) | License policy, exact model/runtime provenance and transitive audit | [24](../ARCHITECTURE.md#licensing) | 001, 002, 016, 018, 020 | UNPROVEN |
| [A05](../ARCHITECTURE.md#a05) | Source identities, rights, access metadata and representative inventory | [3](../ARCHITECTURE.md#workflows), [7](../ARCHITECTURE.md#domain), [9](../ARCHITECTURE.md#ingestion) | 005, 020 | UNPROVEN |
| [A06](../ARCHITECTURE.md#a06) | Structure-preserving native extraction | [9](../ARCHITECTURE.md#ingestion), [18](../ARCHITECTURE.md#vision) | 006, 016, 020 | UNPROVEN |
| [A07](../ARCHITECTURE.md#a07) | Blocks/chunks with exact original evidence and separate context | [7](../ARCHITECTURE.md#domain), [15](../ARCHITECTURE.md#answers) | 005, 006, 013, 020 | UNPROVEN |
| [A08](../ARCHITECTURE.md#a08) | Independent generator/embedding/reranker/lexical accounting | [9](../ARCHITECTURE.md#ingestion), [11](../ARCHITECTURE.md#indexes), [14](../ARCHITECTURE.md#retrieval), [15](../ARCHITECTURE.md#answers) | 002, 006, 007, 013, 020 | UNPROVEN |
| [A09](../ARCHITECTURE.md#a09) | Structural chunk/enrichment budgets without silent truncation | [9](../ARCHITECTURE.md#ingestion), [10](../ARCHITECTURE.md#contextualization) | 006, 020 | UNPROVEN |
| [A10](../ARCHITECTURE.md#a10) | Parent-aware contextual retrieval and long-document adaptation | [10](../ARCHITECTURE.md#contextualization) | 010, 020 | UNPROVEN |
| [A11](../ARCHITECTURE.md#a11) | Context validation, rejection and restrictive support permissions | [7](../ARCHITECTURE.md#domain), [10](../ARCHITECTURE.md#contextualization), [13](../ARCHITECTURE.md#authorization) | 010, 011, 020 | UNPROVEN |
| [A12](../ARCHITECTURE.md#a12) | Durable job fingerprints, resume and dependency invalidation | [8](../ARCHITECTURE.md#storage), [10](../ARCHITECTURE.md#contextualization), [21](../ARCHITECTURE.md#recovery) | 005, 007, 010, 015, 020 | UNPROVEN |
| [A13](../ARCHITECTURE.md#a13) | Semantic generator interface and honest available metrics | [6](../ARCHITECTURE.md#modules), [17](../ARCHITECTURE.md#generators) | 002, 003, 010, 020 | UNPROVEN |
| [A14](../ARCHITECTURE.md#a14) | Qualified gateway Responses online contract | [16](../ARCHITECTURE.md#api), [17](../ARCHITECTURE.md#generators), [23](../ARCHITECTURE.md#qualification) | 001, 003, 014, 020 | UNPROVEN |
| [A15](../ARCHITECTURE.md#a15) | Private direct offline adapter and measured prefix-cache correctness | [10](../ARCHITECTURE.md#contextualization), [17](../ARCHITECTURE.md#generators), [23](../ARCHITECTURE.md#qualification) | 001, 003, 004, 010, 020 | UNPROVEN |
| [A16](../ARCHITECTURE.md#a16) | One qualified embedding space across CPU/GPU precision paths | [8](../ARCHITECTURE.md#storage), [11](../ARCHITECTURE.md#indexes), [23](../ARCHITECTURE.md#qualification) | 004, 007, 011, 020 | UNPROVEN |
| [A17](../ARCHITECTURE.md#a17) | Independent technical BM25 and exact dense retrieval | [11](../ARCHITECTURE.md#indexes), [14](../ARCHITECTURE.md#retrieval) | 008, 011, 020 | UNPROVEN |
| [A18](../ARCHITECTURE.md#a18) | Validated immutable snapshots and atomic reader-consistent publication | [12](../ARCHITECTURE.md#snapshots), [21](../ARCHITECTURE.md#recovery) | 008, 011, 017, 020 | UNPROVEN |
| [A19](../ARCHITECTURE.md#a19) | Rank fusion, bounded candidates and recall-loss accounting | [14](../ARCHITECTURE.md#retrieval), [23](../ARCHITECTURE.md#qualification) | 008, 020 | UNPROVEN |
| [A20](../ARCHITECTURE.md#a20) | Private GPU FP16 reranker with bounded validated work | [5](../ARCHITECTURE.md#deployment), [14](../ARCHITECTURE.md#retrieval), [16](../ARCHITECTURE.md#api) | 004, 012, 020 | UNPROVEN |
| [A21](../ARCHITECTURE.md#a21) | Original supporting evidence and complete generator budgeting | [15](../ARCHITECTURE.md#answers) | 013, 020 | UNPROVEN |
| [A22](../ARCHITECTURE.md#a22) | Grounded multilingual answers, bounded conversation and honest failure | [15](../ARCHITECTURE.md#answers), [16](../ARCHITECTURE.md#api) | 003, 013, 014, 020 | UNPROVEN |
| [A23](../ARCHITECTURE.md#a23) | Authenticated reader API and private operator boundary | [13](../ARCHITECTURE.md#authorization), [16](../ARCHITECTURE.md#api), [20](../ARCHITECTURE.md#configuration) | 014, 020 | UNPROVEN |
| [A24](../ARCHITECTURE.md#a24) | Authorization before exposure, source rechecks and cache isolation | [13](../ARCHITECTURE.md#authorization), [14](../ARCHITECTURE.md#retrieval), [22](../ARCHITECTURE.md#security) | 005, 008, 013, 014, 017, 020 | UNPROVEN |
| [A25](../ARCHITECTURE.md#a25) | Untrusted source/model isolation and bounded extraction | [9](../ARCHITECTURE.md#ingestion), [17](../ARCHITECTURE.md#generators), [22](../ARCHITECTURE.md#security) | 005, 006, 014, 016, 017, 020 | UNPROVEN |
| [A26](../ARCHITECTURE.md#a26) | Privacy, safe logs and stage-specific observability | [22](../ARCHITECTURE.md#security) | 014, 017, 018, 020 | UNPROVEN |
| [A27](../ARCHITECTURE.md#a27) | Physical-GPU ownership, safe transitions and recovery | [19](../ARCHITECTURE.md#gpu-lifecycle), [21](../ARCHITECTURE.md#recovery) | 004, 007, 015, 020 | UNPROVEN |
| [A28](../ARCHITECTURE.md#a28) | Readiness, finite admission, cancellation and explicit degradation | [14](../ARCHITECTURE.md#retrieval), [16](../ARCHITECTURE.md#api), [19](../ARCHITECTURE.md#gpu-lifecycle) | 012, 014, 015, 018, 020 | UNPROVEN |
| [A29](../ARCHITECTURE.md#a29) | Actual memory/latency/concurrency qualification and fallback choice | [23](../ARCHITECTURE.md#qualification) | 001, 004, 012, 019, 020 | UNPROVEN |
| [A30](../ARCHITECTURE.md#a30) | Audited targeted visual extraction with original provenance | [18](../ARCHITECTURE.md#vision), [24](../ARCHITECTURE.md#licensing) | 016, 020 | UNPROVEN |
| [A31](../ARCHITECTURE.md#a31) | Text-first visual retrieval and original-image answers | [18](../ARCHITECTURE.md#vision), [23](../ARCHITECTURE.md#qualification) | 016, 020 | UNPROVEN |
| [A32](../ARCHITECTURE.md#a32) | Human-authored representative evaluation and held-out discipline | [23](../ARCHITECTURE.md#qualification) | 009, 019, 020 | UNPROVEN |
| [A33](../ARCHITECTURE.md#a33) | Controlled ablations and retrieval/support/performance metrics | [23](../ARCHITECTURE.md#qualification) | 009, 011, 019, 020 | UNPROVEN |
| [A34](../ARCHITECTURE.md#a34) | Update/delete/revocation propagation, backup and rollback | [8](../ARCHITECTURE.md#storage), [13](../ARCHITECTURE.md#authorization), [21](../ARCHITECTURE.md#recovery) | 005, 017, 020 | UNPROVEN |
| [A35](../ARCHITECTURE.md#a35) | Explicit profiles, operator CLI and qualified deployment settings | [5](../ARCHITECTURE.md#deployment), [20](../ARCHITECTURE.md#configuration) | 002, 015, 018, 020 | UNPROVEN |
| [A36](../ARCHITECTURE.md#a36) | Early environment/feasibility gates and named live experiments | [23](../ARCHITECTURE.md#qualification), [25](../ARCHITECTURE.md#delivery) | 001, 002, 003, 004, 019, 020 | UNPROVEN |
| [A37](../ARCHITECTURE.md#a37) | Meaningful layered tests and honest evidence classification | [23](../ARCHITECTURE.md#qualification), [25](../ARCHITECTURE.md#delivery) | 002, 009, 017, 018, 019, 020 | UNPROVEN |
| [A38](../ARCHITECTURE.md#a38) | Separate human/strategic/coding authority and provenance-backed work | [4](../ARCHITECTURE.md#context), [25](../ARCHITECTURE.md#delivery) | 000, 020 | UNPROVEN |
| [A39](../ARCHITECTURE.md#a39) | Readiness distinctions, deferred judgment and independent closure audit | [25](../ARCHITECTURE.md#delivery) | 000, 020, 021 | UNPROVEN |
| [A40](../ARCHITECTURE.md#a40) | Protected resources and non-delegable deployment/service boundaries | [19](../ARCHITECTURE.md#gpu-lifecycle), [20](../ARCHITECTURE.md#configuration), [22](../ARCHITECTURE.md#security) | 000, 001, 020, 021 | UNPROVEN |
