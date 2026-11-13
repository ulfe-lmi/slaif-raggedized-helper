# Root amendment 1 to active007-l — oversized-file unit fixture under inherited cap

Status: FINAL, same active007-l/PR9/context/sole wrapper. DHA NONE, ordinary D0 correction.
Original order, component index, source commits, transcript and failed c82e implementation
remain immutable history. No new active/control/response signal, /new or operational goal.

Observed GitHub CI43209043099 at c82e6085eace075846327d1fc4dcf36dee10db89:
all three OAP jobs succeeded; both Product test suite steps failed at the SAME
test_embedding_native_identity.py::test_limits_and_path_guards, line149,
output.truncate(identity.MAX_FILE+1): OSError27 File too large. Root independently read logs,
current test and identity._read; MAX_FILE is32MiB. Earlier unit
test_cpu_worker_backend_setup_v2.py::test_runtime_facts_refused_before_install calls the
actual fixture helper main which lowers the enclosing test process's hard RLIMIT_FSIZE
to32MiB (plus other limits). This explains the concrete oversized-fixture conflict; do not
attribute unrelated archived host-full-unit failures to this observation without proof.

Scope exception ONLY tests/unit/test_embedding_native_identity.py may differ from its frozen
d770 source/index hash. All other22 indexed files and ALL production code remain byte-exact,
especially embedding_native_identity.py and its limits/policy/size guard, native acquisition,
parent and source identities. Existing current-doc/budget/manifest permissions remain.
No helper/previous setup test/CI/workflow/pin/runtime/limit/law/ARCH/source book modification.

FIRST commit exact Root amendment and audit/007-l-CI-size-fixture-failure.json unchanged
under oap/reviews/007-l-ci-size-fixture-addendum-1.md and
oap/reviews/007-l-CI-size-fixture-failure.json. Preserve original order/active/index/transcript;
new source correction commit(s), never amend/rewrite already-pushed c82e. Final report names
original23file250571B transfer AND this explicit test-only exception/current test hash/size.

Repair the oversized-file negative fixture without creating a file beyond inherited FSIZE,
raising/resetting resource limits, skip/xfail/deselection, catching OSError to pass, weakening
the production MAX_FILE guard or replacing the whole predictor/reader. A narrow controlled
os.fstat boundary for ONE owned real small regular file is authorized: report st_size as
MAX_FILE+1 only for its exact actual device/inode; delegate EVERY other descriptor to the
real original fstat. Keep production limit unchanged. Ensure the real size guard refuses
BEFORE reading that file. Keep directory/path/symlink/other existing assertions meaningful.
Equivalent small owned-fixture test seam is acceptable only with equally narrow evidence.
Disclose reported-size simulation as a unit guard test, not an actual oversized file claim.

Prove the causal negative at the actual public predictor and that removing only the relevant
size predicate in owned temporary in-memory source permits the same otherwise-valid real
fixture. Do not leave altered source/global functions installed or change unrelated guards.
An additional finite isolated subprocess with inherited RLIMIT_FSIZE32MiB should run the
corrected focused test under existing AS1GiB/CPU30/wall120/five thread1 caps; never lower
Root/coding TUI process limits. Relevant focused native24/TokenID58 plus predecessor setup
tests in an isolated finite test invocation if needed to prove ordering cause. No full local
suite merely to repeat CI, no relaxed caps. Preserve exact error/setup history and source hash.

Current Root112units/native8/parent1/identity1 successes remain finite subset evidence, not
green CI. Both new implementation and sole-parent SELF report must have all5jobs/all78steps
SUCCESS, none skipped/missing/pending/cancelled. Root independently reviews the actual test
delta/source/doc/report/currentCI before resolution. No whole007/MVP/mainmerge/model/GPU/
license/release/deploy authority, no report publication or normal response before gates.

The ongoing parallel bridge and membership work remains independent. Do not read/replay any
FIFO or create duplicate wrapper/PR. Same current007-l goal continues through this correction.
