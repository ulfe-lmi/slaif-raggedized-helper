# OAP Coding Report — 009-z

Identifier: 009-z
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 1729e85fdc37cbdd0f4a1c4eb879f0ced40d2333
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-z-current-view-and-encoder-transfer.md` (FINAL;
AMEND existing PR 11; Decision: NONE; order file SHA-256
`1328c3336939f296840384a4a0f4abe4864cb2ed79acf8c6c22e763c424f043e`) at
round base `0b337eca746eea97b1e56e71f5a8a06176565a59` (the accepted
009-y report-only head). Objective: transfer the two exact
independently reviewed current-view request and guarded encoder
identity components into the canonical PR, preserving
selected-request observation and existing encoder behavior for their
respective callers, as prerequisites for later guarded evaluation
orchestration.

History published in this round (one regular push to the same PR
branch, no force push, no merge, one PR):

1. `4de04bbc845553d9344d491555caea998f52beed` (parent: round base
   `0b337eca`) — exact Root transcript, four paths: `oap/active`
   (`009-z` + LF, 6 bytes), `oap/orders/009-z-current-view-and-encoder-transfer.md`
   (the FINAL order above), `oap/reviews/009-z-current-view-and-encoder-transfer-index.json`
   (byte-exact copy, SHA-256
   `d6a249fbd1162cbdc831b3961ebc49602fc93fa9db24a0afe513ede56f39124f`,
   17,348 B) and `oap/reviews/009-z-prior-resolution.json` (byte-exact
   copy, SHA-256
   `9fabdabc8cdfff363ae796f059ab57d60550b536ff8a6fd5782b2ad420b46eb5`,
   1,968 B).
2. `1729e85fdc37cbdd0f4a1c4eb879f0ced40d2333` (parent: 1) —
   implementation: the eight transferred objects plus cumulative
   `STATUS.md` and `docs/evaluation.md` notes (10 paths total).
3. SELF — this report only; first parent is the implementation head.

## Reconciliation at activation

- GitHub: main exactly `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`;
  unique open non-draft PR 11, OPEN/MERGEABLE, head
  `oap/009-evaluation-baseline` at `0b337eca` on base main; local HEAD
  and round base equal. Required run 44768398812 attempt 1 at
  `0b337eca`: conclusion success, all five jobs and every step; the
  earlier failed 009-x run 44760385202 (head `53937d7e`) remains as
  recorded.
- The two control files were read at their exact strategic paths
  under `/home/janezp/codex-supervision/slaif-raggedized-helper` and
  matched the order's pinned SHA-256s; the terminal review
  `audit/009-y-check/Root-terminal-review.json` (SHA-256
  `71f0e4461d67e7547cf376264bd8989a94057fef7eb7f972f6017aceacf2f8f6`)
  and the ordered-node projection
  `audit/009-z-preview-inventory/Root-projection.json` (SHA-256
  `48f53f00644474782b174a79067962483b7c1eb82d62a55067beab9bde97f953`,
  whose 17 old encoder nodes match the receiving inventory) were
  verified at their pinned hashes. The consumed 009-y regular
  response `.oap-state/response-consumed-009-y.json` (346 B, SHA-256
  `0977fb5cd4a97bab97d45b365ad09f9d01ef301837527da66435d652524d76d0`)
  was verified. The two consumed lane receipts
  (`parallel/current-view-request/response-consumed.json` SHA-256
  `80c33fa1d05fda6a5064ee90ab65e909e044ce6971f89f5ab61afc58f75ff93d`;
  `parallel/encoder-runtime-identity/response-consumed.json` SHA-256
  `2c4ae6097129257b069b89d62a741102de60fcaa6127da9ef7d6f1b049ad2d0d`)
  and the two local Root resolutions
  (`audit/009-current-view-request-local-resolution.json` SHA-256
  `9d6addc460178bdc1607bd09b83a5392b12a06521f5536638c67c84424bfc3b8`;
  `audit/009-encoder-runtime-identity-local-resolution.json` SHA-256
  `15a46a067fd05046ad0786362186a87290f632b84d09f38b3da561d12c122c31`)
  were verified at their indexed hashes.
- At the round base the report path and all four transcript paths
  were absent; six of the eight destinations were absent and the two
  replaced files sat at their indexed preimage blobs
  (`query_embedding.py` blob `502c2e49`, `test_query_embedding.py`
  blob `9b212eef`).

## Transfer (eight objects, all mode 100644)

Lane 1, current-view-request — implementation
`4b798897dcc3b6194eeda960046d0bf040747dfe` on effective base
`c933223897514b525e0c976cfbb7bd1e87d3cc95` (preparation tree
`01c91d3d`, exact parents `6e8922c6` + `89946522`):

| destination | bytes | blob | SHA-256 |
|---|---|---|---|
| `src/slaif_raggedized_helper/private_policy_request.py` (new) | 14,885 | `7b2a24d3` | `1b52e832ca7f65925bf129958b80b99d3a1a4260dddaa29f06db371505979e44` |
| `tests/unit/test_private_policy_request.py` (new) | 42,773 | `a2bb6642` | `f8491635ce587f1bbf8a61811e9492a015f88d4ad921284a7025961b2f4a663d` |
| `oap/parallel/orders/PAR-009-CURRENT-VIEW-REQUEST-A.md` (verbatim) | 5,675 | `d424d4b8` | `61a9e2e7fb4a564d3ed65c5206953b83920286e79e8fa04bdfdeae11dafb4fb3` |
| `oap/provenance/009-z/PAR-009-CURRENT-VIEW-REQUEST-A.json` (immutable lane SELF report, publication `037e238a`) | 27,304 | `3ae2a8ed` | `e5d870507903bd6d18a6225daa349a940a2fc9dadf03c267f0af6fc01437e0f1` |

Lane 2, encoder-runtime-identity — implementation
`7ac6994cbdbefb9b2afc4b82b56227544d340935` on effective base
`416009c94a6759c9a42e9c19dab688c0f54d9650`:

| destination | bytes | blob | SHA-256 |
|---|---|---|---|
| `src/slaif_raggedized_helper/query_embedding.py` (replaces 7,907 B preimage) | 10,872 | `bf4dbd88` | `6a8277afa130fc3e8da02a454f5eabb2ba7eb36d36147e63bd4301bbf6e8e1d2` |
| `tests/unit/test_query_embedding.py` (replaces 8,731 B preimage) | 24,884 | `504e2147` | `3488f8ceb127241c9ad5da555733fe45467983e35ab0a6e75e5d4e300ec78cf0` |
| `oap/parallel/orders/PAR-009-ENCODER-RUNTIME-IDENTITY-A.md` (verbatim) | 5,006 | `a440edfa` | `c301906a1da6f2d1925b12a85fd449a86820c5dd171d1d569645543ad2fbeb66` |
| `oap/provenance/009-z/PAR-009-ENCODER-RUNTIME-IDENTITY-A.json` (immutable lane SELF report, publication `84b0a6f3`) | 13,264 | `3eb4d31c` | `026163cfda20254d7984ca8472b54bd6b03baeba04a8ecc3148e11a47aa8c794` |

Every row was verified at the exact source commits and at the
receiving working tree (and staged index) for Git mode, byte count,
SHA-256 and blob OID. No product code or test outside the indexed
copies changed.

## Preimage and bridge verification at the round base

- All 14 indexed receiving preimages verified byte-exact (mode, blob,
  size, SHA-256): lane 1 the reader `private_policy_capture.py`,
  `policy_selection.py`, the publisher, `supplied_policy.py`,
  `supplied_policy_wire.py`, `provenance_records.py`; lane 2 the old
  `query_embedding.py`, `isolated_cpu_embedding.py`,
  `cpu_execution_contract.py`, `cpu_embedding_worker.py`,
  `embedding_tokenizer.py`, `embedding_tokenizer_worker.py`,
  `embedding_vectors.py` and the old `test_query_embedding.py`.
- The current publisher `private_report_publication.py` full SHA-256
  `d7c5410280f158cb4cc7c258e06522bb3809aa2c836a79c8b2252b50575ece3e`
  (29,405 B, blob `3c54cb52`) and its exact 22,985-byte original
  capture dependency prefix (SHA-256
  `0e43bb1141d1e122c2f745433716a19a8c99b85d3b431bf0b8499d0f7e29899c`)
  verified unchanged through 009-x and 009-y, per the 009-x exact
  implementation objects review. The indexed measured bridge files
  `private_policy_payload.py` (7,421 B, `48bf5ec4`),
  `private_report_publication.py` and
  `test_private_policy_payload.py` (50,707 B, `ac56eed1`) were
  verified byte-exact at the receiving head; the cumulative
  `STATUS.md`/`docs/evaluation.md` bytes are the accepted 009-y ones
  (the 009-x object review pinned their 009-x-time bytes, which the
  accepted 009-y round updated).
- Legacy query test nodes: collect-only of the 7,907 B preimage
  module in a fresh scratch checkout of the round base collected 17
  nodes; collect-only of the transferred 51-node module in the
  implementation tree shows the 17 old nodes as an exact ordered
  prefix (34 nodes added). No drift, no test refusal.

## Actual local proof (implementation bytes)

Environment: existing canonical locked `.venv` (Python 3.14.4),
physical canonical `src`, fresh mode-0700 scratch directly under
sticky `/tmp`, `-o addopts= -p no:cacheprovider`,
`OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`, and
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824` for the focused
run.

1. One bounded combined focus of the five ordered modules
   (`test_private_policy_request.py` 45, `test_query_embedding.py`
   51, `test_private_policy_capture.py` 71,
   `test_supplied_policy_wire.py` 95, `test_private_policy_payload.py`
   62): **324 passed in 7.77 s, exit 0** — the expected 324. This
   includes the exact passing installed-payload interoperability
   tests (the 009-x 62-case payload suite) against the current
   reader.
2. One four-file Ruff check on
   `private_policy_request.py`, `query_embedding.py`,
   `test_private_policy_request.py`, `test_query_embedding.py`:
   "All checks passed!", exit 0.
3. One bounded import-origin check: both transferred product modules
   resolve to the canonical repository `src` with the exact indexed
   SHA-256s.
4. Node-prefix collect-only comparison as described above (old 17
   exact ordered prefix of new 51).

The 45 request witnesses exercise the real request and authentication
checks (actual `capture()`, `admit_policy_bytes()`,
`match_supplied()` with the exact required operations
`("search", "sources:read")`, the fresh actual `read_selection()`
reread, deadline latching and refusal behavior) under synthetic
installed policy and synthetic ephemeral roots only. The 34 encoder
witnesses exercise the actual resident `ResidentQueryEncoder`
wrapper and session boundary (identity validation and comparison
under the existing encoder lock before the existing session encode)
with synthetic controlled delegates only. Exact bytes and eligible
declarations remain separate from real runtime or authority
qualification.

## Fresh hosted gate (pending)

At the report head the ordered inventories are expected: group A
1,440 unchanged, group B 1,835 (all 79 new default nodes in B; the
17 inherited encoder nodes retain their order), 3,275 total units,
the separate complete 951-case integration, all three OAP jobs and
every existing step. The fresh full hosted CI at the exact report
head is PENDING at report authoring; Root owns the independent exact
fresh CI and terminal review. The report cannot certify its future
push or checks. The representative baseline stays NOT_RUN; whole 009
PARTIAL.

## Limitations

No joint declaration or pin transfer, no durable policy selector, no
source-authorization composition, no callback authority, no
protected model dispatch, no representative evaluation, no product
fixes beyond the indexed transfer, no CI changes, no dependency
installs, no full local suite, no new PR, no merge, no branch
history merge or cherry-pick of a development lane. The open
governed operator, actual authority, source rights, representative
evaluation and hardware gates remain open. DHA: NONE.
