# Raw snapshot payload format map — Root D0

The frozen core descriptor schema names identify the verifier contract; a payload's internal kind may use a distinct fixed name. No frozen codec/report is renamed.

| Core file role | Core descriptor schema | Actual payload |
| --- | --- | --- |
| row_map | slaif-raw-row-map-v1 | canonical JSON kind slaif-raw-row-map-v1 |
| lexical_terms | slaif-raw-lexical-terms-v1 | canonical JSON kind slaif-raw-lexical-v1, verified by raw_snapshot_lexical |
| dense | slaif-normalized-fp32le-d1024-npy-v1 | non-pickle NPY v1, C order, little-endian FP32, 1024 columns |
| source_membership | slaif-raw-source-membership-v1 | Still requires a separate source membership format/loader contract. |

A future actual file binder must explicitly dispatch this closed map and compare descriptor bytes/hash, partition subset identity and fresh source-rebuilt payload. Matching a descriptor or parser alone is not source/current-rights/Ready proof. This map adds no filesystem/publisher/backend implementation or qualification authority. Original core/row/lexical/source bytes remain unchanged; H/A11.5/12 provenance, DHA NONE.
