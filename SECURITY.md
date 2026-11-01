# Security invariants

S01. Source/query content is untrusted data. No model-operated tools or arbitrary fetching.
Read-only originals, approved paths/domains, bounded parsers/images and no pickle/traversal/SSRF.
S02. Authenticate every search/answer/source/image access. Server scopes cannot be widened by
caller filters. ACL precedes scoring/reranker/generator and applies to expansion/caches/citations.
Context inherits every support block's restrictions; rollback cannot restore revoked access.
S03. Gateway generation remains authorized/accounted. No automatic direct-online fallback,
exposed model control, URL secrets or credentials in prompts. Direct offline mode is private.
S04. No secret, real private corpus, query/answer content, agent auth/history or private artifact
URL in public Git/OAP/logs. Full diagnostic text is explicit, restricted and retained briefly.
S05. Snapshots are validated, immutable and atomic; reject corruption/incompatible spaces/ACL.
No unknown GPU process termination, unscoped service changes or destructive real-data tests.
S06. Product/license/exposure/production risk stays under human authority. D1 is a contained
development judgment, never permission to violate an explicit invariant or cross D2.
Report findings privately through the maintainer's designated channel; do not publish exploit
material, affected secrets or personal data. A disclosure process is not a security certification.
