# OAP Coding Report — 009-ac

Identifier: 009-ac
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 6650e725e6e5889ae171fcf1e9dff5fbcfa73d5b
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-ac-selected-installed-policy-transfer.md` (FINAL;
AMEND existing PR 11; Decision: NONE; order file SHA-256
`0a29116b36fb4c72ac76c6d38b6b836035927230327883852c6554e6966b985b`,
byte-identical to the strategic workorders copy) at round base
`8f1ba9aa38f38cffc3d8a9adc66ea1a7bbfa1459` (the accepted 009-ab
report-only head whose required hosted run 44796492067 attempt 1
passed all five jobs and every required step, each Product at 3,370
ordered units and the separate 957-case integration; main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b` exact). Objective: transfer
the independently reviewed private installed-policy selector and its
synthetic regression suite byte-exact — a bounded synthetic selection
component that updates an existing selector using already installed
admissible bytes under the one shared root writer lock, preserving the
separate immutable payload installer.

History published in this round (one normal push to the same PR branch,
no force push, no merge, one PR):

1. `2dbac3f236954919c36cf0913deecffe8f105b9a` (parent: round base
   `8f1ba9aa`) — exact Root transcript, four paths: `oap/active`
   (`009-ac` + LF, 7 bytes),
   `oap/orders/009-ac-selected-installed-policy-transfer.md` (the FINAL
   order above, 6,489 B, SHA-256
   `0a29116b36fb4c72ac76c6d38b6b836035927230327883852c6554e6966b985b`),
   `oap/reviews/009-ac-selected-installed-policy-transfer-index.json`
   (byte-exact copy by basename, SHA-256
   `711bf2b8851b81e889e3837c0941c0e06e8479a2e0800c4468f3e8781257e2dc`)
   and `oap/reviews/009-ac-prior-resolution.json` (byte-exact copy by
   basename, SHA-256
   `d6448b4fa86a6e1355fbffc20281752c41277895f67b2812f72a0cd1ebb426ba`),
   each re-verified at its indexed SHA-256 after copy.
2. `6650e725e6e5889ae171fcf1e9dff5fbcfa73d5b` (parent: 1) —
   implementation, exactly the six ordered paths: the four transferred
   artifacts `src/slaif_raggedized_helper/private_policy_selection.py`
   (26,825 B, SHA-256
   `e929ccc1b4ecc9c7637c6d958022e5c97eae7f9172bbe5012c7bc05b8e3b33c1`),
   `tests/unit/test_private_policy_selection.py` (68 synthetic cases,
   74,745 B, SHA-256
   `22c9b9a349acaf3fa30bc568f5d77cf256a5acbee2029d21267cbae885a63f00`),
   the original lane order
   `oap/parallel/orders/PAR-009-SELECT-INSTALLED-POLICY-A.md` (7,982 B,
   SHA-256 `69545b67ae9b84a8366822381fef83103d41a5b3d6117740fdc534e7b3ac3862`)
   and the original immutable SELF report archived at
   `oap/provenance/009-ac/PAR-009-SELECT-INSTALLED-POLICY-A.original.json`
   (8,488 B, SHA-256
   `6a02bf7846d96543ba940ec1ea388c996659e630c2f17e4f8fc7519ddf9b9f92`),
   plus `STATUS.md` (current-slice lead 009-ab -> 009-ac plus 009-ac
   slice entry) and `docs/evaluation.md` (new 009-ac section). The nine
   frozen dependency objects, the workflow, the CI partition, the prior
   hybrid code and tests and the fixtures are byte-exact; no other
   product path or output envelope changes. The committed implementation
   head is a Root-directed pre-publication doc-only amendment of the
   first implementation commit `7fa456db048e85d22984d69b3d64766847ec9117`
   (same sole parent, unpublished when amended): the amendment changes
   only `STATUS.md` and `docs/evaluation.md` and corrects three factual
   descriptions — (a) the registry mutex is short-lived while one held
   slot guard and the root-directory (directory-inode) writer flock
   cover the transaction; (b) after the sealed staged-name verify the
   final pre-replace checks are the namespace and the prior-selector
   full stable metadata signature (metadata only, no second read), while
   the actual linked new record readback occurs after the replace and
   again after the verified directory flush and namespace recheck; and
   (c) when re-association fails the requested path is probed by the
   real no-follow walk, which is what detects the mismatch, while the
   replacement root's stage is neither observed nor mutated and no
   selector rollback is claimed. `git diff 7fa456db 6650e725 --stat`
   shows only the two document paths, the four transferred blobs are
   re-verified byte-exact at the amended head, and every product byte is
   therefore identical to the proof-time tree below.

## Acceptance evidence

1. Terminal prior report and regular receipt, exact remote head and
   main, unique PR, clean source lane, one implementation parent and
   sole report-only SELF child: the 009-ab report commit `8f1ba9aa`
   equals the exact remote branch head and the ordered base; the
   regular prior receipt `.oap-state/response-consumed-009-ab.json`
   (347 B, SHA-256
   `a1ab94c7d6cb785ebce660376b9363ec5a3a2d00a0f4e0b85269d6dbb9cdbbe9`)
   and the prior exact terminal review (SHA-256
   `7b69c35334dae037691b1b119212cf660813ac715af8e204d983dafbd2a8aed5`)
   match the prior resolution; live main is `5a7b41cc` exact; PR 11 is
   the unique open non-draft PR, base `main`, head `8f1ba9aa`,
   MERGEABLE/CLEAN, no auto-merge, no review threads; the source lane
   worktree is clean at HEAD `54848699469d74e1e5187a13c399113c787144cb`
   (sole report-only child, single-file report diff of 26 insertions)
   over implementation `319ac7db7c2e854d5663016a63022bd626aaa243` with
   sole parent `0b337eca746eea97b1e56e71f5a8a06176565a59` (the indexed
   candidate base). All four indexed source objects were verified at
   their exact source commits (mode 100644, blob OID, byte count and
   SHA-256 per the transfer index), all 18 indexed receiver preimages
   were verified exact at the round base (mode 100644, blob OID, byte
   count and SHA-256), the four owned destinations were confirmed
   absent in-tree and on disk, and the three preview-inventory files
   (added-B/expected-A/expected-B nodes) hash-exact. No mismatch;
   reconciliation stopped nothing.
2. Four exact blobs copied byte-exact (SHA-256 re-verified after copy
   at the implementation head; modes 100644). The nine frozen
   dependencies, the publisher, the payload installer, the prior hybrid
   code/tests and the workflow/CI partition are unchanged; the source
   report was not regenerated or edited. Citing Root's raw
   reconciliation for the omitted Ruff line and the inaccurate repeated
   origins line in the immutable original SELF report: "The immutable
   SELF report repeats RUN3 with two incorrect origin digests and omits
   RUN2. Direct raw command/exit files and the output hashes above
   identify all three capped final successes. Root independently
   confirmed them. Original report retained unchanged." The retained
   raw files identify the actual three capped final successes (290-case
   focus exit 0; Ruff exit 0 with digest
   `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`,
   byte-identical to this round's Ruff output; six-module origins exit
   0), and Root's independent capped proof at the identical tree
   confirmed all three (witness
   `/tmp/oap-root-selected-writer-319ac7d.0sty7CIw`). Historical bounded
   and excluded failure evidence preserved at its prior inputs: the
   pre-recovery combined run 267 passed / 21 failed exit 1 (raw
   `pytest.out` 148,194 B SHA-256
   `a860e91efeac278be58e56a8994f6e48e0779883b2423c006dd38f9e9ec6ed10`
   in `/tmp/selproof.x99iLS`), the transient F841 targeted-Ruff exit 1
   at the intermediate bytes 7b0a5c1/c1f871b (raw `ruff.out` 683 B
   SHA-256 `5d71ac739dea3b763d140592e5f2f0e1802e5bc7303f716f9cf534ab0893fc55`
   in `/tmp/selproof.HsQ90p`) whose intermediate commit summary had
   falsely asserted Ruff success, the invalid `-B` harness deviation
   (usage error exit 4, raw stderr overwritten per the original report),
   the disclosed uncapped dev runs, and both review FIX rounds
   (implementation `2ba9c7be8695ad4cad06fbf90c83afa60f1ae2ab`,
   independent root witness SHA-256
   `127eac996f3dede7cae073d592f7b235a6b5630df1e74dc78e6280915e86be72`;
   implementation `360e0b33df2d308e0e86d55d1268570a30a632ae`,
   independent root witness SHA-256
   `db81f2d12f283070b06a2d42b1338a36e147bcb94b55e4b1e437d6c39c406af0`).
3. One scoped canonical local proof ran at the implementation bytes
   (see Verification); real exits, exact inputs, commands and raw proof
   locators are recorded below; no first failure occurred this round,
   so nothing was preserved beyond the recorded raw streams. Separate
   stage, descriptor and observed publication states under ambiguity
   and root association loss are retained by the transferred 68-case
   suite (UNRESOLVED stage semantics, PENDING custody with first
   interrupt identity, the two genuine root-relocation cuts in fresh
   bounded owned exec children, and the held-root custody separation
   from any reported observation of the requested root).
4. The exact report-head hosted gate is owned by Root and is PENDING at
   report authoring: group A 1,440 and group B 1,998 (3,438 ordered
   units per Product, 68 new B cases) plus the separate 957-case
   integration each, with the other three OAP jobs, both Products and
   every previous required step. Pending jobs are pending at report
   authoring; this report does not certify its future push or checks.

## Verification

Local (actual, this round; all process proofs under `timeout -k 5 120
prlimit --cpu=60 --as=1073741824`, canonical `.venv` (Python 3.14.4),
physical canonical `src` via `PYTHONPATH`, `OPENBLAS_NUM_THREADS=1
PYTHONDONTWRITEBYTECODE=1`, fresh mode-0700 scratch
`/tmp/selproof-ac.IV23F5` directly under sticky `/tmp`, private pytest
basetemp subdirectory, raw logs outside the basetemp, `-o addopts= -p
no:cacheprovider`, actual exits captured without pipeline masking;
command record `commands.txt` SHA-256
`a540d4a26292c69ac62ab5d2d3e8429ab08da09ecefb2baf851cae7e2ce5224d`,
probe `origins-probe.py` SHA-256
`26eedd058bd298483c652bc5d752448fb9d3874508fc26cf5ebe19d480157c4a`):

- RUN1 one bounded four-module focused unit proof of the exact ordered
  paths under `tests/unit/` (`test_private_policy_selection.py` 68,
  `test_private_policy_payload.py` 62,
  `test_private_policy_capture.py` 71,
  `test_private_report_publication.py` 89): 290/290 passed, exit 0 in
  6.20 s; raw streams `pytest.out` 40,178 B SHA-256
  `18a8525bfccef2cb5363e5f8cd99738733f224386494a6372acb62ed2a92a488`,
  `pytest.err` empty.
- RUN2 one targeted Ruff on the two copied Python files on one allowed
  local core (`taskset -c 0`): exit 0, "All checks passed!" (raw
  `ruff.out` 19 B SHA-256
  `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` —
  byte-identical to the Root lane Ruff digest; `ruff.err` empty).
- RUN3 one bounded physical import-origin probe for
  `private_policy_selection`, `private_policy_payload`,
  `private_policy_capture`, `private_report_publication`,
  `policy_selection` and `supplied_policy_wire`: all six resolve to the
  canonical repository physical `src`, ORIGINS_OK, exit 0 (raw
  `origins.out` 919 B SHA-256
  `c4fe4f001e8b4096ae9d6e0b901bd89c62ad6811fbc06dde052a7f5003f977f9`;
  `origins.err` empty).

No full local suite, no repeated unchanged proofs, no native setup and
no live baseline ran this round (the local native test environment is
absent, was not installed and was not simulated; the new cases are unit
only). The proof ran at the pre-amendment implementation bytes
`7fa456db`; the Root-directed doc-only amendment to `6650e725` touches
only the two documents, so every product byte proven above is identical
at the committed implementation head (four transferred blobs
re-verified byte-exact; nine frozen dependencies unchanged from their
round-base preimages).

Hosted (expected, pending at report authoring): the exact report-head
gate requires group A 1,440 and group B 1,998 (3,438 ordered units per
Product, 68 new B cases) plus the separate 957-case integration each,
with the other three OAP jobs, both Products and every previous
required step; Root owns that fresh review. The round base's required
hosted run 44796492067 attempt 1 passed all five jobs and every step.
This report cannot certify its future push or checks; a separate
post-publication receipt verifies the remote publication facts.
Mock/live distinction: all fixtures and roots are synthetic and
operator-owned; no live model request, network, real policy root,
credential, GPU or hardware was used, and no actual current
authorization invocation happens in this module.

## Documentation impact

`STATUS.md` current-slice lead 009-ab -> 009-ac plus the 009-ac slice
entry, and `docs/evaluation.md` new "The 009-ac selected installed
policy transfer" section: isolated artifact identities (bytes and
SHA-256 of all four transferred objects), the operating cuts (admission
before any protected namespace work, the single lock-hold transaction
under the short-lived registry mutex with one slot guard and the
root-directory flock, the pre-replace namespace plus prior-selector
metadata signature rechecks, and the post-replace then post-flush
linked record readbacks), no automatic rollback or stale-stage
recovery, and the reserved-stage availability limitation across
restart: the fixed reserved staging path `.current-policy.stage` can
remain occupied after an uncertain attempt or restart, blocking a new
selection pending separate operator-authorized recovery. Runtime/model,
rights, real operator initialization and recovery, guarded encoding and
protected delivery, and representative evaluation gates stay open;
whole 009 PARTIAL and baseline NOT_RUN are recorded.

## DHA and boundaries

Order Decision: NONE; no `append_critical.py` invocation, no CRIT entry
added or touched. Preserved: the prior report archive and all four
transferred blobs byte-exact, the candidate lane and its scratch
evidence, the unrelated worktrees and branches, the workflow and CI
partition, and the existing Qwen/gateway services. No merge, no
auto-merge, no force push, no new PR, no release/tag/deploy, no branch
merge/cherry-pick, no direct FIFO access and no change of model or
profile; the sole external control wrapper's consumed notification was
not re-read.

## Limitations and remaining work

No actual first failure occurred in this round's proof. The strongest
availability limitation transfers with the component: the fixed
reserved staging path can remain occupied after an uncertain attempt or
restart, blocking any later update pending separate recovery (no
inferred rollback, no automatic stale recovery). Power loss is proven
only by the final verified readback (DURABLE); an attempted replace may
have acted before a crash, leaving the new record in the selector
(POSSIBLY_PUBLISHED) with no automatic restoration claim, and the stage
may be retained. No power-loss test, no actual initialization entry
(generation-1 initialization is separate scope), no actual current
authorization invocation, no runtime or rights claim, no real roots, no
credentials, no network. Caller-facing policy admission, payload
installation, private retrieval, evaluation and publication behavior,
real root initialization, protected recovery, source rights, guarded
encoding and protected delivery, and representative evaluation remain
separate gates. Baseline NOT_RUN; whole 009 PARTIAL; the fresh hosted
gate at the exact report head is PENDING with Root owning it and the
terminal review. DHA NONE.
