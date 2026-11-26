# Parallel OAP work order — private supplied-policy wire

Status: FINAL for separately activated isolated implementation.
Provenance H full-MVP work program; ARCH §13/A23/A24; E absence of bounded
operator-byte admission; I scoped policy-wire design c9499b77 and typed
implementation peer 912237c1. DHA NONE.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Scope

Implement the FINAL supplied-policy-wire-v1 contract at SHA256
b737e5e33ff2ce753ea8a9c3e68eba2a250b8f56d2004e57c1b52c5478aa3158.
Exact typed base 191139254f327dd9d987f60db4102f2916e55611. Worktree and
new local branch oap/parallel-009-supplied-policy-wire identified in the
lane manifest. Candidate isolated mode. Canonical objective 009 and PR
#11 remain owned by the original coding/control path. No remote branch,
PR or canonical changes.

Allowed new implementation paths:

- src/slaif_raggedized_helper/supplied_policy_wire.py
- tests/unit/test_supplied_policy_wire.py
- docs/parallel/supplied-policy-wire-v1.md (exact strategic contract bytes)
- docs/parallel/supplied-policy-wire-api.md
- oap/parallel/orders/PAR-009-SUPPLIED-POLICY-WIRE-A.md (exact order bytes)

Use the exact lane source index. Read the bound typed implementation and
the existing public provenance record mapping path. Preserve typed API,
format, factory, source/tests, constraints and object identity.

## Acceptance

1. New additive private module with admit_policy_bytes and PolicyWireError.
   No filesystem/current-policy/operator/provider/runtime integration.
   Only exact immutable bytes, bounds-first structural checks, monotone
   cursor, strict field UTF-8, and no alternative encoding or schema
   dropping. Unsupported raw/canonical shape refuses with one fixed
   input-free ordinary failure, with no retained own cause/context. A
   controlled non-Exception BaseException propagates by identity.
2. Use real public Grants admission with a controlled mapping, then
   reconstruct exact DTO types and call real typed admit_policy. Preserve
   its checks and hash. No counterfeit type, current-authorization
   substitute, relaxed cap or implicit second implementation of factory
   semantics. Document actual work/bytes and formal accounting scope.
3. Default-collected pure tests with portable fail-closed origin checks
   derived from the resolved test-file parent. Use bounded, content-free
   parameter IDs. Include meaningful direct/bytes equality and independent
   golden identity, Unicode/control/empty cases, actual 20000 declarations,
   size/count/material/remaining/EOF and strict invalid UTF-8 refusals.
   Test both distinct schema locations and structurally valid inputs refused
   by the typed factory. Exercise genuinely returned Grants/output via
   real supplied matching and real provenance query predicates. Verify
   exceptional identity/ordinary hygiene. Keep actual transport-size and
   typed canonical semantics distinct from a heap or runtime claim.
4. Existing canonical venv read-only with explicit PYTHONPATH pointing to
   the isolated candidate's src and actual module-origin assertions.
   One focused Ruff check/format cycle of the two new Python files.
   Up to two bounded pure-unit executions with CPU120s / AS1GiB / wall180s
   plus 5s kill, no external installation. Run the normal default test
   entries for the two supplied-policy test modules (inherited typed and
   new wire), with no skips or unchanged-failure retry. A second process
   requires an actual changed-byte correction after a concrete failure.
   Stop on setup/resource/origin issues. Preserve owned regular full logs
   with the exact command, env safe scope, limits, case counts, actual
   exits, source hashes and measurements.
5. One clean implementation commit on the exact sole base, restricted to
   the five paths, with byte-exact contract and order. Write regular
   private evidence and use the existing implementation checkpoint helper
   once. Wait for the strategic FIX/REPORT decision. Any final report is
   solely local with report_publication_commit SELF and sole parent the
   accepted implementation. Response only through the original lane
   helper, exactly once after verified report, and then quiesce.

## Protected resources

Use one new isolated lane control via the designated helper. No prior or
canonical FIFO, duplicate reader, nested agent, provider/profile/auth
changes, models, native runtimes, credentials, protected corpus,
services, remote/lifecycle/release, or protected file loading. Pure inputs
are synthetic and explicitly supplied. Existing authority, source rights,
real baseline, hardware, and MVP prerequisites remain open. 320 KiB
cumulative semantic allowance including source, law and outputs. Record
an honest measured/estimated ledger with hash-only I/O separate.
