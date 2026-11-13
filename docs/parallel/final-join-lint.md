# Final join static preparation

Canonical CI 43377547440 failed both product legs on E501 at the adapted trace fixture docstring; later full tests were skipped. The current canonical fixture input was copied from 50a85ac8ad41856cc9e81292db8d50d39477b42b and only its docstring was shortened. The inherited fixture difference in the base includes the earlier portability adaptation. Eight incoming Python files were formatted. The Root literal addendum SHA256 76ff14cf9a9e59958f3affb4c12db7c19f5699975d0a8f24e3d27916a37353cf authorized adjacent byte literal splits for PROGRAM and EXPECTED; both values were compared exactly. All nine Python non-docstring ASTs match their indexed inputs; the other eight indexed files remain byte-identical.

One Ruff format passed; the first check found two E501 literal lines; the second check passed. Private preflight, raw outputs, timings and exit codes are preserved under /tmp/final-join-lint-1129-recovery. The initial preparation failure and Root recovery are retained separately. No application, tests, model, native or store runtime was executed. The V6 Toy proof used the prior unformatted wrapper and the V2 constructor proof preceded formatting; those historical component results do not prove execution of these new bytes or combined composition. Full normal hosted CI on both versions remains required at the future canonical head. This branch contains 009 extras; only the 17 indexed components and Root records/current docs are candidates for selective copying, not a whole-branch merge.

Input and output SHA256 (input → output):

- `src/slaif_raggedized_helper/raw_snapshot_completion_locator.py`: `34cea660631a488ad08ed19c3bb95c4dc2638e294b165647a807bcf05d6d20c7` → `6ca8ec375aa6595c615f11b6ea208dcfe16e5eb06271eb90630f1366640ce7d0`
- `tests/unit/test_raw_snapshot_completion_locator.py`: `0bec942bea0b67d9f743fc764fd25bb3d95b9281707b730dd95414cd5797f621` → `a2b088a0d66948f76287bdf1da511b7eadc66d9368d0b5f414dc42d463d3a784`
- `docs/parallel/completion-locator-api.md`: `f1f43243293331369d4ecf3d83c8de0e603cc0a5452f949b0068c0c1f9465dbe` → `f1f43243293331369d4ecf3d83c8de0e603cc0a5452f949b0068c0c1f9465dbe`
- `docs/parallel/completion-locator-contract.md`: `dd93b0996d1bb165d8f13ae503213264fe3d64b883cb5188df942e80c53ca130` → `dd93b0996d1bb165d8f13ae503213264fe3d64b883cb5188df942e80c53ca130`
- `docs/parallel/completion-locator-oracle.json`: `dd1caa4216f809a7435fb4bf290baacecd3874b28df8346b7ba9eaed6ba29dde` → `dd1caa4216f809a7435fb4bf290baacecd3874b28df8346b7ba9eaed6ba29dde`
- `src/slaif_raggedized_helper/raw_snapshot_construction.py`: `107673d5bedf22fbe629fd4d5ec41c33d0fad70bbed99db8522c2d46ee7ff9d6` → `4a01e150f46633dca856f6bfcac05007b06930839c21c7b13c1431672c54f7a3`
- `tests/unit/test_raw_snapshot_construction.py`: `c7093fd2a0775d7e364be65ae8b65069d62ce5f7082daa4d83f1d4af83129660` → `a43d7c99780c9fdb7c58ca5e18c58936caa5f23aef2e3cc3b92ccafafcc50de0`
- `tests/integration/test_raw_snapshot_construction_composition.py`: `c45d9d961d147d00e3a6a26d7e5c28e8a339da45470cf0860ebec1283ed749ee` → `7ffd3f0d6c64b72bde4b8957d27397b370cb7d936cb8fe09526bb5f1dafe16d6`
- `docs/parallel/snapshot-construction-api.md`: `cfd67f4ea4d8494730b6f7e5db8fb1dd24998a8191d85cb870738d922786b992` → `cfd67f4ea4d8494730b6f7e5db8fb1dd24998a8191d85cb870738d922786b992`
- `docs/parallel/snapshot-construction-contract.md`: `07df618fc26d3ca1fb0318ad6903fd93556aeeccd6246a4dc7a4a82d114aa942` → `07df618fc26d3ca1fb0318ad6903fd93556aeeccd6246a4dc7a4a82d114aa942`
- `src/slaif_raggedized_helper/raw_snapshot_query.py`: `7cf010637cbee6378155aa921297b8fa4c072e27b5eb37d4770953f5fb88f6a5` → `aced05dea7dc3019390676d8fc509e65c672accff4090a87acbaaf24ac292541`
- `tests/unit/test_raw_snapshot_query.py`: `b54cf7335153d3b0cbfc0807165c22034f1da2d6210b8766c3bc065792ac03bf` → `cd7c959d7b067756dce7c8a04b09f8111e261d32821d65509e65936c045f3e08`
- `docs/parallel/pinned-query-api.md`: `1ef76d5723a0f9552999fc4403105481e4c426ae2664b75dabb22c01fdddd6e5` → `1ef76d5723a0f9552999fc4403105481e4c426ae2664b75dabb22c01fdddd6e5`
- `docs/parallel/pinned-query-contract.md`: `89066153ec7d66fedfec33aa4000a6b67e5c621546a4f4c8d0b9a5c0a5cad2fd` → `89066153ec7d66fedfec33aa4000a6b67e5c621546a4f4c8d0b9a5c0a5cad2fd`
- `tests/integration/test_raw_snapshot_query_ci_composition.py`: `f04570f2b9d9f85e719fa2d30947d69c11cd73a78218f4c9a379823fa95ed311` → `a5442419d9a3865e2a9eefbd8181964cccc1d0db896f1b6161befc8d08d4f893`
- `docs/parallel/pinned-query-ci-preparation.md`: `304def8842e8d27e0dbee88347006a3bb85d80bf06c95e413145e2d4db84e08e` → `304def8842e8d27e0dbee88347006a3bb85d80bf06c95e413145e2d4db84e08e`
- `tests/integration/test_raw_hybrid_trace_composition.py`: `3759df10d25748e41f9988bc853c04e7e8799e32e3cc2b86150182b9aacb7057` → `3a12ea8d574a5a3d40b3de52190f862a79172c8486109ef5234374268326fa5d`
