# Parallel OAP work order — supplied raw membership eligibility

Status: FINAL for separately verified isolated activation.
Provenance H full MVP, ARCH 13.2–13.4/A23/A24, E partition eligibility
under a supplied policy is absent, I reviewed typed checkpoint and
current-policy read-boundary evidence.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922
DHA: NONE.

## Goal and scope

Implement a pure function to derive unavailable raw partition IDs under
a genuine supplied policy and an admitted supplied raw Membership.
CODING %32 only. Exact typed base
191139254f327dd9d987f60db4102f2916e55611, with actual unchanged raw
membership/provenance/query inputs per index, local isolated manifest.
No canonical or remote mutation. PR 11 and 009-q remain separate.

Module `src/slaif_raggedized_helper/supplied_policy_eligibility.py`.
API `unavailable_partitions(policy: SuppliedPolicy, membership: Membership)
-> tuple[str, ...]`, fixed empty-input-free `PolicyEligibilityError(ValueError)`.
Require exact factory-owned policy with existing typed marker. Membership
is a constructible nominal DTO. Use its exact class and genuine bounded
admission, without assuming a nominal constructor authenticates a capture.
For this pure slice, re-admit its exact canonical `membership_bytes`
through existing `raw_snapshot_membership.parse` and require full type/
field agreement before use. Use established `qualification.parity_io._depth_check`
on strict ASCII text decoded only after the existing 8 MiB byte bound, before
that parser, so
arbitrary deep bytes cannot go through unguarded JSON decoding. A future
trusted operator may avoid repeating whole membership admission on real
bound pin evidence, scoped separately. Never call filesystem or verify a
current policy here.

For each entry in admitted membership, use the real
`provenance_records.admit_record("Scope", entry.scope_bytes)` to obtain
document_id. Entry carries no direct document_id. The existing membership
parser binds scope hash, revision and partition. Match the policy's exact
document rule and its (entry.revision_id, entry.source_scope_sha256) pair.
A missing rule/pair or empty rule makes the complete entry partition
unavailable. Include admitted zero-row entries under this conservative
membership rule. Derive only partitions in this captured membership;
return a unique sorted tuple. Do not use old snapshot withdrawal state
or a later different Membership as a substitute for this mapping.

Bound lookup on the already canonical sorted policy documents using
binary search (stdlib bisect or equivalent); no copy/reparse/rebuild
of the complete policy, no principal traversals or credential
handling. Pair count <=64 per rule, entries <=128. Use a fixed
ordinary error with no own caught cause/context; let interruption
identity propagate.

## Acceptance and verification

1. Verify exact lane and base, index sources and previous receipt. Read
   bounded exact inputs. Existing membership/provenance/policy types,
   source files, tests and error contracts remain unchanged.
2. Default tests `tests/unit/test_supplied_policy_eligibility.py` build
   real synthetic membership with canonical source hashes and genuine
   parse, and genuine typed policy via factory. Cover exact positive,
   scope-hash change, missing and emptied rules, mixed-partition denial,
   unaffected scope, clean same-partition replacement, old data again
   under unchanged policy, nominal inconsistent input and error hygiene.
   Show return is derived from actual parsed entries, no handwritten
   partition suppression. Include positive boundary context and
   nonvacuity; show portability via exact worktree source origin.
3. Existing venv/read-only with candidate PYTHONPATH. Focused Ruff and
   one selected module run, CPU 30s AS 1GiB wall60s + KILL5, private
   fresh basetemp. Use RAYON_NUM_THREADS=1 for bounded Ruff if needed.
   Correct a real changed-byte failing case once. Preserve full
   outcomes; request review on remaining failures.
4. One exact implementation commit containing only the module, its
   test and order copied to
   `oap/parallel/orders/PAR-009-SUPPLIED-MEMBERSHIP-ELIGIBILITY-A.md`.
   Document scope in module and immutable report. Request one exact
   implementation checkpoint. Only after REPORT make local report-only
   SELF commit then send original lane response once. No old/canonical
   FIFO and no remote publication.

## Protected resources

Pure synthetic supplied raw data with existing tooling and unchanged
profile/auth. No protected I/O, actual authority, writer, data/model/GPU,
service, installation, real rights or runtime qualification. Later
raw eligibility must be composed from real current policy and a real
pin before actual encode/score/ground/delivery. No enriched/visual or
full-MVP claim follows from this component.
