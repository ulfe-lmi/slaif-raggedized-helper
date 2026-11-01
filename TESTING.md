# Verification contract

T01. Default product tests use synthetic owned fixtures and fake generator/embedding/reranker
interfaces; no key, network, GPU or model download. OAP tests use isolated temp repositories,
FIFOs and fake remote/tmux interfaces. Never exercise live project pipes during fixture tests.
T02. Run focused behavior/negative-path tests for the changed boundary. Add integration proof
for actual composition, filesystem crash/atomicity/concurrency, ACL, cancellations and retries.
Do not accept keyword/assertion-only checks as product behavior proof. Broad suites belong at
phase/release gates or when reproducing their failures, not repeated without a reason.
T03. Real route/model/GPU tests are opt-in and require exact authorized host/device/data/call
budgets, known profiles, fingerprints and safe rollback. Mock success is not real qualification.
Report PASSED/FAILED/SKIPPED/NOT RUN/BLOCKED/PENDING/MISSING exactly. No fake timing/usage/results.
T04. Keep final held-out evaluation separate from tuning and retain safe raw measurements.
Verify negative authorization, contradictory/insufficient evidence, source support, tokenizer
limits, FP16/FP32 parity, no direct fallback, corrupt snapshots, restart and mode contention.
T05. Current scaffold check: `python3 -m unittest discover -s tests/oap -v`.
`python3 oap/bin/check_state.py --repo-root .` checks installed governance and orchestration.
The GitHub Actions workflow `CI` (.github/workflows/oap.yml, see docs/CI.md) runs those same
OAP-scaffold checks on pull requests/pushes to main and manual dispatch (Python 3.12-3.14). It
covers the OAP scaffold only. Product test commands and CI do not exist until their ordered
implementation. Required final-head checks are read from live policy; zero checks never means
product verification has passed.
