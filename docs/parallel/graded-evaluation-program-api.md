# Private graded evaluation program

Status: controlled checks passed; Root review and genuine source composition remain outstanding.
This describes a private ABI, not serving, rights, human relevance, or quality qualification.

`run_evaluation(originals, derived, root, pin_owner, dataset_bytes, cohort, queries,
gold_bundle_ids, *, grants, restrictions, config, budget, plan, grade_budget, deadline_ms)`
borrows its inputs and returns `Report(identity_payload, identity, plan_identity, final_work,
final_payload)` or raises the content-free `EvaluationError`. `Judgments(case_id, gold)`,
`Plan(plan_id, dataset_id, split_id, snapshot_id, generation, catalog_id, protocol_id,
unknown_policy, overlap_policy, cutoffs, judgments)` and the 13-field `GradeBudget` are frozen
private records. The adjacent Root contract and binding specify their semantics and ceilings.
Both identity domains end in one LF. The original source JSON is embedded once unchanged.
Identifiers and hashes are private linkable information; no source text or ranking/grade lists
are returned.

The original source budget remains separate. For N cases, the grade source reserve is
D=6N+4, T=3328N+1920, U=3584N+2304, bytes=D*100925699+(T+U)*404750404+T*2016386,
and owner observations 2+2N. Each of three variants reserves E=sum(g+60) entries and
W=sum((g+60)*C+g*max(1,(max(1,g)-1).bit_length())) logical work. Nested source and geometry
ledgers overlap and are not additive physical observations. These are logical worst-case
reservations, not measured I/O or permission to perform it.

## Grade local meter and preflight envelope

Work and cumulative payload are independent counters. `reserve` increments both before its
operation, checks deadline and fails rather than refunding. A preflight inequality checks future
headroom; it is not itself a consumed reservation. Let G=sum(g), C=cutoff count, and
R=65536+2048N+1642496+3*(4096+512C+N*(1024+448C)). Before pin, the implementation checks
remaining work >= 4,000,000+220,000N+8,000G+16R and payload >=
12,000,000+220,000N+12,000G+16R after plan admission/identity charges. After catalog and the
first grade pin, it additionally checks `(2N+1)` remaining grade pins at
work `pointer_bytes+core_bytes+2*map_bytes+2*rows+1095` and payload
`pointer_bytes+map_bytes+192` each. These checks do not raise any binding ceiling.

The following table describes the actual meter precharges. K is the total number of already
admitted authority strings in one original/effective and restriction pair, S their character
count, H the sum of actual metric gold and rank entries, and V the bound for one variant
`4096+512C+N*(1024+448C)`. JSON hashes of fixed schema objects use the lower canonical walker,
whose own per-node, string, emitted-byte and key-comparison charges are cumulative.

| Operation | Work / payload charged before allocation or walk |
| --- | --- |
| Closed plan and bounds | 4096/4096 fixed; 512/128 per case; 256/128 per judgment; 129 per plan/protocol ID, 72 per hash ID, one per cutoff. These are consumed before the future-headroom inequality. |
| Question, payload, authority, expected query IDs | Question `len+1 / 4*len`, then `question_UTF8+payload+132 / 384`; each authority pair `2048/2048`, `K+1/0`, then `S+K+1 / (4096+16S+128K)` before `model_dump`. Canonical authority and query hashing charge the lower walk separately. Duplicate-set entry costs 256/512. All are consumed before the second headroom check. |
| Plan graph and identity | `4096+256N+128(G+60N)` work and `4096+512N+256(G+60N)` payload before graph construction; canonical walker charges every node/string/key sort/emitted byte and caps the ASCII plan at 8 MiB. Consumed before the second headroom check. |
| Each extra pin | Actual runner charges pointer `p+1/p`, core `c+66/192`, digest comparison at most 258/0, map twice `(m+r+1)/m` then `(m+r+1)/0`, plus 1/0. The formula above adds slack and covers the remaining `2N+1` observations after the catalog pin. |
| Grade case | 2048/2048 per case; judged IDs `g+1 / 128g`; each bound row 1024/256; each of up to 180 rank IDs 256/128; retained case 1024/2048. The canonical judgment fingerprint charges its own bounded walk. Fragment contents remain in the binder and are not copied; row tuple lengths are summed. |
| Three triples and results | Sort reserves `3*(1024N+1)/1536N`. Each metric input hash precharges `4B/4B`, `B=512+128*cases+96*entries+8C`, before JSON encoding and hashing. Across three aggregate plus N query hashes per variant, using 60 rank IDs per query, this is at most `6144+147456N+96C(N+1)+2304G` in each counter. Result validation separately charges fixed 4096 per variant, 256N for counting, `512+g+rank_count / 512` per query and 128/128 per cutoff record. |
| Variant, case, header and final report | `asdict` costs `4V/4V` before traversal; encoding reserves `4V/4V` and then actual emitted bytes <=V. Each case dict reserves 512/2048 and encoding reserves `8192/8192` plus <=2048 emitted bytes. The fixed header dict reserves 65536/65536 before construction; each header value is bounded and independently charged `4*65536` plus actual bytes. List/variant joins reserve their upper lengths. Final outer join precharges `4*size+1` in each counter; the hash precharges `size+64` and updates the digest without concatenating domain and payload. Source payload validation precharges its length+64 before its domain concatenation. |

For the remaining non-pin work, the metric hashes charge at most
`6144+(147456+96C)N+96C+2304G`; rank validation charges at most 46083N work and 23040N
payload; sorting charges 3072N+3 work and 1536N payload; metric-result checks charge at most
`12288+(2484+384C)N+384C+3G` work and `12288+(2304+384C)N+384C` payload. Each case adds
3072/4096, each judged row/ID adds at most 1025/384, and the judgment canonical walk is
bounded by 512N+512G+constant work and 512N+3000G+constant payload: a grade ID is 71 ASCII
characters, a grade is one digit, and each pair contributes a two-element tuple. At C<=16
these terms fit 220,000N+8,000G work and 220,000N+12,000G payload; the 4,000,000/12,000,000
fixed margins cover the remaining fixed-key and call overhead. The `16R`
term covers three variant `9V` charges, up to `5R` outer joins/copies and hash, bounded case
encoding, source payload hashing, fixed header-value encodings, and the extra header/graph
allocations. R already includes the 1,642,496-byte source and 2048N case components, whose
remaining slack covers the fixed header encodings. Actual operations are still charged as they
occur. A larger judgment count, cutoff count or captured map can legitimately exceed the
independent caps and be refused; no later partial report is returned. The 256-case, zero-grade,
two-cutoff case has R=3,722,240 and future headroom 119,875,840 work / 127,875,840 payload,
before already-consumed admission and pin-map charges. It is included in proposed controlled
tests; that controlled test passed under the approved process.

Original 009 remains open. Controlled units are not genuine source composition. Separate
source requalification, private plan/report publication, CLI, CPU query/current-policy/data
integration and an authorized real baseline remain gates. The 512 joined-row and 4096
catalog-row ceilings are software limits; 20k support is not established. Encoder, model,
hardware, current rights, human-held-out relevance, license, visual MVP, merged-SHA independent
audit and release remain unqualified. One Root-authorized bounded sequence passed: AST-equivalent
format, Ruff and 98 controlled units, including all 54 unchanged old source-runner units and the
three pre-implementation legacy identity/payload/counter/call-sequence scenarios. The new units
use controlled source delegates and genuine pure metrics; they do not prove actual source
composition. No actual source proof has run. DHA NONE.
