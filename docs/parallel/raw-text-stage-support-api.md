# Private raw text stage support

`evaluate_case` borrows exact original and derived stores and an ACTIVE same-root pin. It admits at most 16 MiB of canonical dataset bytes, a case ID of at most 128 characters, up to 128 sorted unique bundle hashes, a 4096-byte normalized little-endian float32 vector and four declared query identifiers. Its strict integer deadline is 1–120000 ms; one cooperative clock includes admission, every call and final construction. Admission is capped at 5000 ms and each support call at 30000 ms. No hard preemption is promised.

The case scope is an allowlist intersection with supplied grants, retaining restrictions unchanged. Empty corpus or version intersections deny all; empty labels allow only unlabeled sources. Original and effective authority and filter identities are distinct. These are supplied declarations, not current rights or Gold eligibility. The full dataset and chosen case requirements remain the support denominator.

One owned hybrid call and three sequential owned source-support calls use the held old snapshot. Private frozen results contain linkable IDs, counts, cap markers, and source-support coverage records. They omit question text, vector, source content, paths, hits, traces, caller resources and exceptions. Caller inputs remain caller-owned; traceback contexts and a hostile process are outside this privacy courtesy. Errors are content-free and no resource ownership transfers.

Coverage describes declared original-span geometry, not factual support or qualified retrieval quality. Query vector and Gold eligibility remain unverified; execution is NOT_ATTESTED and results NOT_QUALIFIED. MRR, nDCG and Gold candidate-loss are unavailable under UNSPECIFIED_RELEVANCE_UNIT_MAPPING. Original 009 still requires a typed mapping and independent oracles or a justified meaningfulness limitation, plus actual trace-row source binding.

This slice is source code plus pure unit doubles only. A separate portable actual composition fixture and Root-reviewed finite proof are required before component admission; independent review and canonical CI remain future gates.

Peer remediation: the adapter requires an exact `str` root of at most 4096 characters before the lower path checker can encode it; the existing byte and path checks still apply. Pure unit sentinels exercise oversized and subclass refusal before lower calls. Actual raw adapter source and native composition remain UNRUN; this is source and pure unit evidence only.
