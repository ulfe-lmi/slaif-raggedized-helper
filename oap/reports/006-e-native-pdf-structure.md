# OAP Coding Report — 006-e

Identifier: 006-e
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 8
Branch: oap/006-native-extraction-and-chunking
Base branch: main
Base commit: 391c8331d43365b048c9c7903637637b5f459601 (exact 006-e round base; PR base main 4977186d3ddbd2259f78590b29c0364fe26eb1fb)
Implementation head SHA: 6168099c3171d4b18fac8e39674cc7596c37ce4d
Report publication commit: SELF

## Work and scope

Order 006-e (FINAL, DHA NONE) on PR 8. Round-start b2b4f100dea96ba2bf0326d59f51f14730c30261 committed the strategic bytes unchanged (order f67837f1, active 006-e, 006-d root review e9a97999, index 23629b4f, re-verified). ONE exact local --no-ff merge 6582845378a57995039ba278d3cf02d024ddcf38 (parents b2b4f10 + 275335a068e9f62723d344288240b6571f9d4f8e, implementation b39317a838f7d6d7500be4efb84a586af5b45205, tip report 784a002f, lane review a33f20c3) forecast clean with git merge-tree against the actual round-start parent; merged tree 3c2edff8e678fdb6311a6f38656c17ea567f2703 equals the forecast; all 17 index source blobs verified (two changed PDF modules, new pdf_structure.py, worker 652fcf66 unchanged). Implementation 6168099: docs/governance only (README, STATUS, TESTING, UNCERTAINTIES, docs/ingestion.md, benchmarks/ingestion-count-storage.md, CONTEXT-BUDGET 49705/50000, MANIFEST re-hashes). No src/, .github/, dependency or model/profile change; no app patch beyond the reviewed merge.

## Acceptance evidence

1. Merge/index/root bytes/worker verified as above. Policy v4 binds classifier pdf-literal-structure-v3; kind-bound block fingerprint v2 is SHARED by producer and stored validator; policy v3 / classifier v2 records are immutable and incompatible — explicit re-extraction, never a silent upgrade; text/order/page/bbox/source hash/rights and native count identity unchanged.
2. Actual post-merge owned fixtures (reduced-policy small 20-row and closing, default-policy 300-row, fitting warning 14/20/12): EVERY row chunk retains the original header fragments; complete interval-union coverage, tail, units, anchors; warning + procedure together, unrelated prefix separate; closing rule/blank/EOF preserves the last row; a next table starts only on complete header + rule + two consistent rows, same page, compatible offsets; one-character offset and ambiguous/incomplete next-prefix limits documented (compatible incomplete prefix stays in the current run; other ambiguous material stays text).
3. Focused actual runs on the MERGED module (approved DEV backends): 88 passed 36.52s (classifier unit, four actual PDF structure cases, PDF extraction composition incl. the original owned loopback isolation negative, record guards incl. coherent-wrong-kind/legacy, typed PDF publish-close-fresh-load); 25 passed 37.64s (installed chunk/inspect T15); ruff/compileall/OAP scaffold/check_state/diff --check exit 0 (ACTIVE 006-e 49705/50000); console: --help 0, doctor example 1 (MODEL_UNQUALIFIED x3, SECRET_ABSENT). Unchanged witnesses pass on the merged source: root terminator (24 blocks, 21 chunks, all 20 row chunks header, last row table_row, trailing blank text), root admission (huge geometry REFUSED 0.049s, long spaces BOUNDED_TEXT 0.058s), peer C boundary. No deselection or skip.
4. At EXACT implementation 6168099 CI run 43094014711 ALL FIVE jobs SUCCESS (OAP 3.12/3.13/3.14 checks 130778083814/130778083931/130778083895; Product 3.12/3.14 130778083874/130778083315). This report's future CI is not claimed.
5. Docs current v4/classifier 3/kind ID 2/grammar/IDs/re-extraction/limits; closed structural failures recorded with Root/peer evidence; failed broad STRUCTURE-A operational references removed (superseded as current repair); wording fixed: structured text re-derives the bounded source; PDF stored validation = original hash/catalog plus producer-record consistency (shared classifier re-run, kind-bound IDs) WITHOUT fresh PDF parse/fidelity attestation; complete semantic unit = validator + publisher + fresh loader; metadata approval is not current auth.
6. Context 49705/50000 UTF-8; exact model tokens UNMEASURED; contrary native capacity timings and 019 OPEN preserved.

## Verification

Commands: uv run --isolated --locked --offline --python 3.14 pytest -o addopts='' -q (88 and 25 cases); witnesses via uv run --isolated --locked --offline --python 3.12 python /tmp/raggedized-root-pdf-classifier-admission.py, /tmp/raggedized-root-pdf-table-terminator.py, /tmp/audit-pdf-c-witness.py under approved SLAIF_NATIVE_TEST_*/PDF_TEST_* DEV backends (root cpython-3.12.15; /tmp/raggedized-root-native-setup-b-6cd8bebe0a, /tmp/raggedized-root-pdf-setup-20ca62cd48); all exit 0. Mock/live: synthetic owned fixtures; native route REAL local tokenization of toy artifacts; PDF route the real 006-a worker parse; live/model/GPU/corpus authorization NONE. No claim about this report's future push/CI.

## Documentation impact

README/STATUS 006-e entries; TESTING T13 006-e extension; UNCERTAINTIES 006-e block; docs/ingestion.md (classifier, kind-bound IDs, policy v4 re-extraction, 006-e section, slice status); benchmarks T13/T14a/T15 wording plus 006-e notes; CONTEXT-BUDGET 49705/50000 plus MANIFEST re-hashes. Historical reports untouched.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. Preserved: strategic round-start bytes unchanged; candidate histories intact (no reset/clean/stash/pick); all other MANIFEST-listed files byte-identical. No merge performed: PR 8 OPEN, base main, no auto-merge, no tag/release/deploy.

## Limitations and remaining work

- The bounded literal grammar cannot infer arbitrary PDF layout/fidelity; incomplete/ambiguous material stays text or in the current run — documented, not claimed.
- Whole-006 acceptance owned by Root after this report (independent review; code queue/green CI alone are not acceptance); pilot/model/fidelity/current auth/visual/license/ICA gates OPEN; all real qualification NOT RUN; no numeric 007, no self-assigned next work.
