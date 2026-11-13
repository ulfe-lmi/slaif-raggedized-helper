# Private source cohort runner

`source_cohort_runner.run_cohort` is a private composition of a borrowed snapshot pin,
traced raw hybrid search, source-bound stage binding and declared cohort aggregation.
The caller supplies a canonical dataset, an explicit sorted split selection, matching
query vectors and fingerprints, original grants/restrictions, configuration declaration,
independent budgets and one deadline. The runner does not acquire or close its borrowed
stores or pin. Every selected case must succeed before aggregation; an ordinary refusal
raises the content-free `CohortRunnerError`, whose progress is unavailable until admission
and thereafter contains only phase and counts. Interruptions remain interruptions.

A successful private report contains a canonical identity payload and domain-separated
identity plus final local logical counters. Its case and binding identifiers are linkable,
not anonymous. The declaration establishes structural scope only: authorship and rights
are unverified, current policy is not checked, the encoder and model are not qualified,
and no baseline has run. The source observations are sequential, not an atomic lease.
The initial dataset parser's internal work and copied bytes are unmeasured by the runner;
source envelopes are static logical reservations, not observed physical I/O. Binder work
includes geometry, so those ledgers overlap and must not be added together. The large
worst-case reservation is not authorization for physical resource consumption.

On the local pinned Python 3.14 environment, the focused Ruff check passed and the
entire controlled unit module passed (35 tests) at source SHA-256
`e69a446b6437cb25bd5549e734102fd594c180d059f44bc7ba52d83f5cba04ae` and test
SHA-256 `d88a6f97f81e716773aae1fac4e541c054b89794f38eb84a4b871a3bac78558e`.
The first unit attempt failed during collection because its editable package resolved to
another worktree; the approved retry used the assigned source path and retained that failure.
The controlled tests do not run actual stores, source, native components or a model.
Python 3.12 and current canonical CI were not run locally.

The malformed trusted-callee correction requires exact bounded integers for the
aggregate case count and the binder's dataset case, dataset atom occurrence and
chosen atom occurrence counts, before independently comparing them with admitted
counts. The pinned lower constructors normally produce integers; no normal-run
metrics error or privacy leak was observed. The guards add no data traversal.

For this correction, the focused `ruff check` of the runner and unit module passed,
then the entire `pytest --assert=plain tests/unit/test_source_cohort_runner.py`
module passed 54 controlled cases (the original 35 plus 19 scalar variants). The
new cases substitute one malformed scalar into otherwise coherent exact lower DTOs;
binder refusals precede aggregation and pure-report refusals follow one real
controlled aggregate. Existing integer and mixed Gold success cases remain. Source
SHA-256 was `96e6971435a3a2f639e7ba3d101248c8eb3fb6bc34b35fedbebdd40d673b4f29`
and unit SHA-256 was `4d01ca5c9d717e900364f0aed8a97eff07e9a742cbfab051826b50438934d87b`.
These differ from the prior 35-case evidence above. Both checks exited zero with
empty stderr, no timeout or cleanup, and identical pre/post 377-entry read sets
(4,389,643 repository bytes and 353,921 selected metadata bytes). The frozen
readset SHA-256 is `cc57eb37f25d6bdc9e23f9bbfa3af1e0f8a39333783b64b091749d3d8c84099e`;
the private helper SHA-256 is `ca43d49543b172a695e96d1c48ad1b9ebc6883893262e71ceb529f16c9837aab`.
Evidence, exact commands, environment and pre/post hashes are retained under
`/tmp/slaif-cohort-runner-b-proof-20261113`; Python resolved to `/usr/bin/python3.14`
(SHA-256 `52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41`)
and Ruff SHA-256 was `4ef33997b4bb7c5f141527e90b2da0abe918108362ca1b9825c4d13adce0e347`.
Each child used CPU 0 affinity and zero core-file limit; Ruff had CPU 5 s, address
space 512 MiB, file 16 MiB, wall 30 s limits, and pytest had CPU 30 s, address
space 1 GiB, file 32 MiB, wall 120 s limits. GNU time observed 0.01 s and
18,476 KiB peak RSS for Ruff, 3.29 s and 79,572 KiB for pytest; these are process
observations, not aggregate resource caps. The earlier wrong-origin collection
failure remains retained and was not a pass.

Actual source composition, a qualified baseline, rights, held-out review,
encoder/model/hardware qualification, 20k scale, visual and domain review, license review and independent audit require
separate evidence and authorization. Original objective 009 and the full MVP remain open.
