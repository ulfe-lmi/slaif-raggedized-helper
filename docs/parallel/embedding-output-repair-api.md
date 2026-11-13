# Explicit output repair

`Journal(root).own(plan_bytes)` yields a live owned handle. `repair_running_output(metadata_bytes, container_id, expected_revision, expected_state_bytes, *, store, validate_current, deadline_ms=5000)` accepts an explicit immutable batch locator and exact canonical observed RUNNING state and revision. It requires an old owner different from the current live lease owner. It does not discover orphan outputs or reopen terminal jobs. The borrowed store and handle remain caller-owned.

The trusted local `validate_current(plan_bytes, stage)` provider must freshly validate original sources, exact configuration and current rights for the entire plan at both `before_repair_validation` and `before_repair_commit`, returning the same bare SHA-256 epoch. A caller-supplied epoch or persisted hashes alone do not provide authority. This repository does not supply an actual current-principal policy provider or operator/controller integration.

The existing typed store freshly validates the complete plan binding and batch data, then the journal commits one CAS transition to COMPLETE with the original attempt and `RECOVERED_VALID_OUTPUT`. This is data materialization evidence, not evidence of execution origin, billing, physical drain or model qualification. The result labels these unknown or unqualified. After an exception following commit, reread and use `verified_output`; do not blindly repeat repair. The deadline is cooperative, including callbacks.

Remaining work includes durable discovery, controller and real source-policy integration, worker/resource recovery, retry policy, neural execution and hardware qualification. The synthetic provider in tests is not an authorization implementation.

The implementation reads the full owned journal, its job records and transition rules, the typed batch and derived store contracts, and lease ownership checks. The copied design records the governing boundary; proof identities and exact commands reside in the lane evidence. The causal control omits only the complete-plan comparison in a private source copy. These tests establish no model, hardware, or physical-vacancy claim.

Readset at this candidate (SHA-256; semantic inspection covers the whole line range listed):

| File | Bytes | Lines | SHA-256 |
| --- | ---: | ---: | --- |
| embedding_job_journal.py | 25497 | 1–662 | `2dfd72c88537fee0f6d85b3448212906be0137cdbcac6ba1deb79283b3aec15d` |
| embedding_job_ownership.py | 7008 | 1–210 | `708731cd9a76e41df08c1c07e02b78748f90aca72da0bb6e12e5c7ee1977cafe` |
| job_records.py | 11211 | 1–343 | `7a74be6ae92e046ce35f372a02877a3e9042fc30f46995199cd6c2a43add9625` |
| embedding_batch_store.py | 5893 | 1–142 | `8e53be2d1a0acb8fc8d6932bdd9c1d5f5b8f9015108de79814fa2a07c6a9f429` |
| derived_store.py | 12215 | 1–363 | `80cb56fcee50aa18df1c291a58e4ea8a0b462fcd614aa480d36605e12916e761` |
| embedding_vectors.py | 2029 | 1–58 | `c69906f3cb4a1239241990d31eb2688fb14712525c5046e93ff07331724b3a67` |
| vector_codec.py | 5983 | 1–178 | `13a923892bba79089d1e1c7282d562eff1fd3fff2ec51c3c6df4a7f5dc52330c` |
| tests/unit/test_embedding_batch_store.py | 4063 | 1–107 | `8efee30c265604db3bf8b62f1262a512db28b5992cc5541050aa647c19c75cc9` |

The production files in the table are under `src/slaif_raggedized_helper/`. Full integration collection requires the existing CPU test environment variables even when no test executes. Collection with placeholder private paths checks import layout only; it does not validate the CPU runtime.

Synthetic proof includes a fresh one-row repair and reload, live child lease exclusion and repair after termination of that owned child, a different-plan causal control, missing/corrupt data, stale state and revision, changing or refusing provider, interruption before and after commit, callback-induced output and revision changes, non-RUNNING states, same owner, closed ownership and callback-entered deadline. These establish only the described local behaviors. Fixture source was formatted after earlier actual-store runs. Those earlier runs used journal SHA-256 `074928ccbc156ae1646bc4ca7bb1b6c4565ed286f5a5b372a0a8810b1a621651`; the later deadline correction uses the current journal identity above. Two additional bounded tests exercise delayed actual commit return and delayed actual final verification against the corrected source; earlier journeys were not rerun. Raw per-process plans, hashes, output, resource records, failed attempts and decisions are retained in the lane evidence. Full canonical CI is a later gate.
