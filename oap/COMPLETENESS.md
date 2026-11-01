# Architecture coverage, not queue completion

Initial matrix is UNPROVEN throughout: no product implementation or independent closure audit.
The detailed machine-readable matrix is `audit/requirements.json`. Full source specifications
remain audit scope even if a draft omitted a requirement. The auditor adds exact merged revision,
enforcing paths/runtime, positive/negative evidence, limitations and freshness for each row.

| Requirement | Architecture obligation | Planned objectives | Evidence classification |
|---|---|---|---|
| A01 | Product and boundaries (PLAN §§1,12; UPDATE §§1,12) | 020 | UNPROVEN |
| A02 | Corrected hardware topology (UPDATE §§1–4,6,8) | 001, 004, 015, 020 | UNPROVEN |
| A03 | Small service composition (PLAN §§3,12; UPDATE §8) | 002, 018, 020 | UNPROVEN |
| A04 | Licenses and model provenance (PLAN §§2–3; UPDATE §9 LICENSE-01) | 001, 002, 016, 018, 020 | UNPROVEN |
| A05 | Source identity, rights and inventory (PLAN §§5,6.1,10) | 005, 020 | UNPROVEN |
| A06 | Structural extraction (PLAN §6.2) | 006, 016, 020 | UNPROVEN |
| A07 | Blocks, chunks and original evidence (PLAN §5) | 005, 006, 013, 020 | UNPROVEN |
| A08 | Independent token accounting (PLAN §4; UPDATE §§3,6) | 002, 006, 007, 013, 020 | UNPROVEN |
| A09 | Structural chunk budgets (PLAN §6.3) | 006, 020 | UNPROVEN |
| A10 | Contextual retrieval algorithm (PLAN §§6.4–6.5) | 010, 020 | UNPROVEN |
| A11 | Annotation validation (PLAN §6.7) | 010, 011, 020 | UNPROVEN |
| A12 | Resumable jobs and invalidation (PLAN §§5,6.7; UPDATE §§3,9 OPS-01) | 005, 007, 010, 015, 020 | UNPROVEN |
| A13 | Generator boundary (UPDATE §5) | 002, 003, 010, 020 | UNPROVEN |
| A14 | Gateway online contract (UPDATE §§1,5.2; GATEWAY-01/02/03) | 001, 003, 014, 020 | UNPROVEN |
| A15 | Direct offline adapter and cache proof (PLAN §6.6; UPDATE §5.3–5.4) | 001, 003, 004, 010, 020 | UNPROVEN |
| A16 | Embedding-space contract (PLAN §§3,6.8; UPDATE §6.1 EMBED-01/02) | 004, 007, 011, 020 | UNPROVEN |
| A17 | Lexical and dense retrieval (PLAN §§4,6.8,7) | 008, 011, 020 | UNPROVEN |
| A18 | Immutable snapshots (PLAN §§5,6.8,10) | 008, 011, 017, 020 | UNPROVEN |
| A19 | Fusion and candidate accounting (PLAN §7) | 008, 020 | UNPROVEN |
| A20 | Reranker worker (UPDATE §§3,4,6.2; RERANK-01) | 004, 012, 020 | UNPROVEN |
| A21 | Evidence assembly (PLAN §7) | 013, 020 | UNPROVEN |
| A22 | Answering and conversation limits (PLAN §7; UPDATE §6.3) | 003, 013, 014, 020 | UNPROVEN |
| A23 | Authenticated API and source serving (PLAN §§10,12; UPDATE §5.2) | 014, 020 | UNPROVEN |
| A24 | Authorization and cache isolation (PLAN §10) | 005, 008, 013, 014, 017, 020 | UNPROVEN |
| A25 | Extraction/model isolation (PLAN §§6,10) | 005, 006, 014, 016, 017, 020 | UNPROVEN |
| A26 | Privacy and observability (PLAN §10; UPDATE §§5,6) | 014, 017, 018, 020 | UNPROVEN |
| A27 | GPU ownership and transitions (UPDATE §§3,8; OPS-02) | 004, 007, 015, 020 | UNPROVEN |
| A28 | Readiness, admission and concurrency (UPDATE §§4,6,8; ONLINE-02) | 012, 014, 015, 018, 020 | UNPROVEN |
| A29 | Memory/latency qualification (UPDATE §§4,6.4,9) | 001, 004, 012, 019, 020 | UNPROVEN |
| A30 | Optional visual ingestion (PLAN §6.2; UPDATE §§5,9 GATEWAY-02) | 016, 020 | UNPROVEN |
| A31 | Visual answers (PLAN §7; UPDATE §10 E) | 016, 020 | UNPROVEN |
| A32 | Evaluation data and held-out discipline (PLAN §§6.1,11) | 009, 019, 020 | UNPROVEN |
| A33 | Retrieval and answer ablations (PLAN §11; UPDATE §9) | 009, 011, 019, 020 | UNPROVEN |
| A34 | Corpus updates, deletion and recovery (PLAN §§5,10,12) | 005, 017, 020 | UNPROVEN |
| A35 | Configuration and operators (PLAN §12; UPDATE §§7–8) | 002, 015, 018, 020 | UNPROVEN |
| A36 | Early qualification gates (UPDATE §§9–10) | 001, 002, 003, 004, 019, 020 | UNPROVEN |
| A37 | Test and publication honesty (PLAN §11; UPDATE §11) | 002, 009, 017, 018, 019, 020 | UNPROVEN |
| A38 | Concentrated OAP authority and provenance | 000, 020 | UNPROVEN |
| A39 | Readiness, DHA and closure audit | 000, 020, 021 | UNPROVEN |
| A40 | Protected resources and non-delegable actions | 000, 001, 020, 021 | UNPROVEN |
