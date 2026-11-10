# OAP Coding Report — 003-j

Identifier: 003-j
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: 16fcbcb34fb2075747df7007f3648eac4846916d
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-j-credential-header-and-output-preflight.md
(Status FINAL, Decision: NONE, live authorization: NONE, active 003-j,
PR mode AMEND_EXISTING_PR) on the existing unique 003 objective PR #5.
Round start reconciled against GitHub: remote head and local HEAD were
both 693bec103b2a45472ac9477a94817d58928ddb85 (published 003-i report
SELF, sole implementation parent
0a49ab978bcedf65ab9e44c2741a9038a20c7d9f), PR #5 the sole OPEN
MERGEABLE PR, base main 93b43177f4dcd0b28ef2c5ed33a049f83217f152, and
the worktree carried exactly the strategic round-start bytes: modified
oap/active (003-i -> 003-j), new
oap/orders/003-j-credential-header-and-output-preflight.md and new
oap/reviews/003-i-review.json. All three were committed
byte-for-byte unchanged inside the single implementation commit
16fcbcb34fb2075747df7007f3648eac4846916d (12 files, +458/-70).

## Changed behavior, by 003-j criterion

1. Credential-value admission now matches the ACTUAL locked HTTPX
   0.28.1 string-header serializer. The transport
   (model_clients/transport.py) builds the `Authorization` header as a
   Python str and supplies no encoding override; the locked
   httpx/_models.py::_normalize_header_value encodes str header values
   with `value.encode(encoding or "ascii")`. The previous guard
   admitted code points <= 0xFF per an abstract RFC 7230 Latin-1
   reading, so the whole 0x80-0xFF range was admitted but unserializable.
   In src/slaif_raggedized_helper/probes.py, `_header_value_unsafe_reason`
   now refuses any code point >= 0x80, applied to env AND file
   references; the fixed typed reason is `value_not_ascii` (constant
   SECRET_REASON_VALUE_NOT_ASCII), replacing the now-misnamed
   `value_not_latin1` (003-i's > 0xFF subset keeps the same fixed
   outcome). The admitted domain is exactly 0x20-0x7E. C0/DEL
   control refusal (`value_contains_control_character`), ASCII
   positives, supported file ending (one optional trailing newline),
   bounded regular-file/non-blocking/FIFO/UTF-8/size handling, the
   opaque credential-path digest and the (separate) reference-PATH NUL
   admission are unchanged. No raw binary/Unicode header support was
   introduced and no key is re-encoded or transliterated.
2. Output-stage fixes preserved as proved: the pre-dispatch owned-0400 /
   invalid-directory refusal (exit 2, zero HTTP) and the genuinely late
   post-work export failure (exit 3, full safe JSON on stdout, exact
   spent-attempt accounting, safe post-work stderr stage) are untouched
   code, and their unit and installed-CLI regressions still pass,
   including on the CI Python 3.12 product leg (the 0a49 exception-safe
   destination probe remains in effect; no regression).
3. Documentation corrected to the actual scope (no historical report or
   order edits):
   - docs/generator-contract.md: the probe module path corrected from
     the nonexistent `model_clients/probes.py` to the real
     `src/slaif_raggedized_helper/probes.py`; the credential rule now
     explains supported header values via the actual HTTPX string
     encoding (not an abstract HTTP field-character allowance) with the
     `value_not_ascii` reason; 8192 is stated as the ACCEPTED
     credential-file size cap (the bounded read uses at most one
     4096-byte chunk of lookahead past the cap to detect the overflow —
     the cap bounds admission, not the exact bytes read); the final
     paragraph no longer implies live trials must be completed in 003 /
     the same PR — per order 003-a Runtime (live authorization NONE,
     "accept callable adapters/probe tooling and synthetic HTTP
     evidence only"), 003 software acceptance is that tooling +
     synthetic HTTP, and live-target evidence belongs to the separate
     004/019/full-MVP qualification gates, which remain OPEN; the
     explicit real-qualification NOT RUN statement and the open certifi
     (MPL-2.0) dependency gate are preserved.
   - STATUS.md: same scope-fidelity correction in the closing bullet;
     the 003-e bullet's live-scope wording corrected; new 003-j
     round bullet.
   - README.md: exit 3 described as a POST-WORK evidence export
     failure (after the probe returned, whether or not any dispatch
     occurred, as its spent-attempt ledger states), not "post-dispatch".
   - TESTING.md T07: objectives now 003-h/003-i/003-j; credential
     refusal wording now names the non-ASCII domain including the
     0x80-0xFF range for file and env references with the fixed typed
     reason.
   - docs/UNCERTAINTIES.md: 003-j entry (U01/U05 unchanged in kind,
     boundary corrected; scope fidelity; live NOT RUN).
   - oap/governance/MANIFEST.json: TESTING.md hash refreshed to
     898ff5f6ad5817d008d13f10d446f555bd9b3e741ce125b418ea93c208be4a98
     (only governance hash affected); manifest is now
     8d495656ed65746b15bfe33b6c7d703a254737a200e9d3629de8b45c05ecc85f.
4. Prior-report increment fact correction (report left immutable): the
   003-i report's "+21 unit / +9 integration" for 419 -> 440 is
   arithmetic — it is +21 TOTAL = +12 unit (159 -> 171) + 9 integration
   (260 -> 269). This round: 440 -> 442 = +2 integration (the two new
   probe-composition tests), unit unchanged at 171.

## Acceptance evidence (numbered to order criteria)

All evidence is synthetic and offline: owned 127.0.0.1 loopback
servers, owned fixtures and synthetic canary values only; no external
network, product services, real keys, GPU, model or corpus (mock/synthetic
route, NOT live qualification).

1. Admission domain: unit boundaries (tests/unit/test_probes.py):
   file and env U+00E9 and U+211D -> ("invalid", "value_not_ascii"),
   control NUL/DEL -> "value_contains_control_character", 0x7E "~" and
   "a b" -> resolved (exactly the 0x20-0x7E serializer domain).
   Installed-CLI composition (tests/integration/test_probe_composition.py,
   new): owned file credential U+00E9 and U+211D, and env reference
   U+00E9, each refuse with exit 2 / CREDENTIAL_INVALID /
   value_not_ascii, `srv.state.requests == []` (zero HTTP), no
   `UnicodeEncodeError` in stderr, no value echo. The order's own
   witness /tmp/raggedized003-credential-latin1-review.py re-run
   against the final source (uv run --locked python, owned HTTP
   server, synthetic credentials) prints exactly:
   `{"case": "ascii_file_positive", "exit_code": 0, "status": "complete", "error": null, "reason": null, "posts": 2}`
   `{"case": "latin1_file_value", "exit_code": 2, "status": "error", "error": "CREDENTIAL_INVALID", "reason": "value_not_ascii", "posts": 0}`
   `{"case": "latin1_env_value", "exit_code": 2, "status": "error", "error": "CREDENTIAL_INVALID", "reason": "value_not_ascii", "posts": 0}`
2. Exact commands and results at the implementation head (local venv,
   Python 3.14, `uv run --locked`):
   - `pytest tests/unit -q` -> 171 passed
   - `pytest tests/integration -q` -> 271 passed (129 gateway + 83
     native + 33 transport + 26 probe composition)
   - `ruff check src tests/unit tests/integration` -> All checks passed
   - `python -m compileall -q oap tests` -> clean
   - `python3 -m unittest discover -s tests/oap -v` -> Ran 41 tests, OK
   - `python3 oap/bin/check_state.py --repo-root .` -> exit 0
     (governance manifest sha256 8d495656ed65746b15bfe33b6c7d703a254737a200e9d3629de8b45c05ecc85f,
     active 003-j)
   - `uv run --locked raggedized --help` -> exit 0
   - collection (order's method): `pytest tests/unit tests/integration
     --collect-only -q -o addopts=''` -> 442 tests collected
     (171 unit + 271 integration; OAP 41 separate)
   All prior adapter/probe/deadline/retry/FIFO/export oracles retained
   and passing (no oracle weakened; the 003-i unit boundary positives
   for 0x80-0xFF were the documented wrong-domain expectation and were
   corrected to the actual-serializer negatives per the 003-i review).
3. CI at the implementation head: run 42814721086 on
   16fcbcb34fb2075747df7007f3648eac4846916d — all 5 jobs SUCCESS
   (OAP tests Python 3.12/3.13/3.14; Product tests Python 3.12/3.14,
   including the product 3.12 leg that failed at 2258464 before the
   0a49 repair), run completed success, last update
   2026-11-10T12:21:45Z. Observed BEFORE this report commit; this
   report cannot certify its own future push or checks.
4. Reconciliation: with the guard aligned, the remaining 003-i
   criterion 1 defect is closed at this head; all other 003-i
   positives were already verified by strategy and are re-proved by
   the retained suites and the green CI. Any other unmet original
   requirement remains visible in the round reports and
   oap/reviews/003-i-review.json; strategy alone chooses protected
   development merge or another continuation.

## Limitations and deviations

- Live-target/runtime/cache-quality/license/distribution qualification
  remains NOT RUN (live authorization: NONE); nothing here claims
  acceptance, readiness, license clearance or release.
- The report was authored after observing the implementation-head CI
  success; remote checks on the report commit itself are for the
  separate receipt/strategic review.
- No deviation from the ordered scope: no dependency or transport/
  parser rewrite, no broader credential encoding support, no new PR,
  no source-original/architecture/schema change.

## Preserved resources and no-merge confirmation

Source originals, ARCHITECTURE/PLAN/CRITICAL, prior orders/reports
(including the immutable 003-i report), agent homes/settings/FIFOs,
unrelated services/GPUs and real credentials untouched. OAP FIFOs were
never used or read; no second waiter started. PR #5 amended in place;
no merge, auto-merge, tag, release or deployment performed; no next
work chosen; model/provider/profile unchanged.
