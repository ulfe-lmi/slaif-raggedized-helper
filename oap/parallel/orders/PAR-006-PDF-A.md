# Native PDF software candidate — PAR-006-PDF-A

Status: FINAL
Role: CODING WORKER
Worktree: /home/janezp/codex-work/slaif-raggedized-helper-parallel-pdf-adapter
Base: e84469f78b82fc5cd41110289bfa7446793ca034
Decision: NONE

Human authorized parallel Terra medium coding. Use isolated worktree for every tool; preserve model/profile/auth and live main/PR/canonical FIFOs. Local preparatory006 only, not canonical activation/acceptance. Read compact coding/security, architecture7.1–7.4/9.2/22.1–22.2, actual source/provenance APIs and exact regular reports parallel/pdf-spike/report.json, pdf-dependency-pin/report.json, pdf-isolation/report.json. No helper/history scans or wildcard lane reads.

## License and dependency boundary

The planned backend is EXACT pdfminer.six, tested20260107, not another parser. Its current development graph has unresolved MIT-0/native notice questions. Human MIT-0 policy question is pending. This order permits SOFTWARE DEVELOPMENT and owned-fixture tests using the already isolated development environments ONLY. NO project pyproject/lock/runtime dependency changes, vendoring, distribution, legal exception or LICENSE-01 clearance. Lazy backend availability/prerequisites must be explicit in the API. Actual packaging waits for policy/audit. No models/fonts/tokenizer/CUDA downloads.

## Actual bounded implementation

1. Implement parent pdf_extraction.py and fixed worker pdf_worker.py. Compose verified approved original bytes and existing source/provenance types; processing approval/source revision/ACL/corpus/rights retained. Only application/pdf here. If necessary add a backward-compatible PUBLIC bounded verified-read option to source_admission.py so parser max input bytes is checked before reading an oversized blob and on actual descriptor reads, rather than only after full capture. Preserve all source corruption/path/race/immutability regressions. No raw original bytes in routine errors.
2. Use actual pdfminer native page/layout APIs in a separate OWN worker process. Fixed trusted operator runtime/config and argv only, never module/executable/path from PDF or JSON. Use actual qualified bwrap/unshare/prlimit isolation from the spike: selected trusted Python/runtime/packages/code/input read-only, empty writable temp, clean environment, closed inherited FDs, no agent homes/credentials/real stores/host root/network/GPU. If required isolation/backend is unavailable, fail closed with exact prerequisite, no silent unsandboxed fallback. OS resource isolation is not a Python monkeypatch.
3. Finite practical documented byte/page/layout-object/text/output/memory/CPU/wall limits. Parent enforces actual pipe bytes while produced, deadline and exact-child terminate/kill/reap within explicit finite cleanup; no unbounded capture_output or detached work. Page bound uses admitted limit+1/overflow refusal rather than silent truncation. Child output strictly decoded/validated with identity bindings to source/policy/request and safe fixed errors. No arbitrary pickle/object/loader chosen by source. Trusted packaged CMap/runtime resources remain read-only and document assumptions. Only exact owned fixtures controlled.
4. Preserve exact extractor-produced native text (pdfminer may synthesize spaces/newlines; don't pretend raw PDF text-byte equivalence), deterministic blocks/dependency/policy fingerprints, source page/section anchors and ACTUAL supplied layout geometry in explicit PDF point coordinate system. Reading order/layout heuristic uncertainty and textless/unreadable/visual-needed pages explicit; no apparently complete empty result, no invented geometry, no deleting repeated warnings/version/headers. No OCR, rendering, vision model, token-aware chunking or actual hardware qualification. Partial results/status must never masquerade as complete extraction.
5. Actual owned tiny PDF text/page/geometry -> sourceStore -> provenance Registry composition; malformed/encrypted/unsupported input, extra pages, object/text/output exhaustion, child crash/timeout, source corruption/read race, wrong child identity, safe canary errors, cancellation with surviving caller and child cleanup. Test OS denial with synthetic outside canary/network-owned listener, no real secrets. Fixture children<=2s timeout+<=1s cleanup; production-library limits may be larger finite choices. Preserve current text/source/provenance tests, no broad reruns for counts. Module import/help no parser/model/network/telemetry.

Document actual APIs/defaults/MAX/isolation/dependency prerequisites, scope and deployment-host qualification requirements. This is a software candidate; small fixtures don't qualify hostile PDFs, full006/vision/ICA/MVP/licenses. No shared CLI/schema/gates/governance edits.

## Lane protocol

Consume only fresh control once:
python3 /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/lane_signal.py wait-control pdf-adapter
Allowed paths: src/slaif_raggedized_helper/pdf_extraction.py, src/slaif_raggedized_helper/pdf_worker.py, src/slaif_raggedized_helper/source_admission.py, docs/parallel/pdf-extraction-api.md, tests/unit/test_pdf_extraction.py, tests/integration/test_pdf_extraction_composition.py, oap/parallel/orders/PAR-006-PDF-A.md
Copied order: oap/parallel/orders/PAR-006-PDF-A.md
One implementation commit(parent=base), then report-only JSONoap/parallel/reports/PAR-006-PDF-A.json(parent=implementation). Report lane_id/result/full implementation_head/report_publication_commit SELF/summary/API/tests/limits. Clean tree then respond once and idle:
python3 /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/lane_signal.py respond pdf-adapter
No push, PR/default-main merge, release, nextwork or integration-gate writes. Working tested implementation required, not only a plan/report.
