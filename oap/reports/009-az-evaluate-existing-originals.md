# OAP Coding Report — 009-az

Identifier: 009-az
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 1731bcfc68b7211ad13f7b66af7189d0094e6be7
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-az (AMEND_EXISTING_PR
on PR 11, round base
d3243019f284b00f83e814972866180454ef0dcc, the
exact 009-ay report
head whose bound prior resolution (SHA-256
9d7c7c0071db24ecefcbfc26a2c4b303bfb89a11c5675c6e
62ffc91e12a8ab46)
recorded ACCEPT_EXACT_SCOPE_CONTINUATION_ONLY at
GitHub run
45529630089 attempt 1: all five required jobs
and every required
step successful at both Products, ordered 1,440
+ 1,998 units and
exactly 1,008 integrations each; remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).

GitHub reconciliation before any edit: PR 11 is
the unique open
non-draft PR with head branch
oap/009-evaluation-baseline at exactly the round
base (headRefOid
d3243019f284b00f83e814972866180454ef0dcc, base
main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
mergedAt null, state
OPEN, mergeStateStatus CLEAN), local HEAD
equaled the base, and the
working tree carried only the four frozen
governance paths plus the
Root activation (oap/active exactly 7 B "009-az"
+ LF, from
"009-ay"), plus the new untracked order byte-
identical to the
strategic workorders copy (SHA-256
5ed81028b81b2ae09c8a77ee83f6643eea4a089506fe3713
a59095a8804b10f1).
The bound review index was copied byte-exact to
oap/reviews/009-az-evaluate-existing-originals-
index.json (SHA-256
c5d422ee73bd318be4fe1c97f3208d6b76b5dd1d2a270bc0
87989affb4bda3ef)
and the prior resolution to
oap/reviews/009-az-prior-resolution.json
(SHA-256
9d7c7c0071db24ecefcbfc26a2c4b303bfb89a11c5675c6e
62ffc91e12a8ab46).

The Root decision
audit/009-az-check/Root-partial-governance-only-
decision.json
(SHA-256
50bb4b9a2c629468e032f29787cc5541a1cb05a03cb09b29
0c2d3bbf3bce018d)
narrowed this round to
PARTIAL_GOVERNANCE_ONLY_WITHHOLD_ORIGINALS. Its
bounded actual
synthetic setup test (check-original-setup-
mode.py, 1,166 B,
SHA-256 ed1d60aa6d657df9d9a8c8c29c4bd0a1af68c5b6
9997223adf9e778fb8f0b8b5;
result log 84 B, SHA-256
68ff093c27988a932ef23d09bdb6f60659dc496ffc66cf40
1c2b97bf2c354c64)
observed that revisions change from 0700 to 0750
during the final
absolute-root observation, that the exact
_open_existing returns a
reader, and that the final linked-descriptor
comparison omits the
repeated actual mode admission. The decision:
preserve the original
order and prior transcript; publish the four
exact indexed human
governance paths; keep the exact OriginalStore
product transfer
(source_admission.py plus the new original-store
composition test)
unfulfilled and held before publication; award
no exact product
acceptance.

Three linear commits: transcript-first four-path
commit
dd5e460c7a8648dabcfdd428845c84b5103073d2 (exact
order, oap/active
009-ay to 009-az, both byte-exact review
copies); implementation
four-path commit
1731bcfc68b7211ad13f7b66af7189d0094e6be7 (the
bound governance
bundle only); this report-only SELF child.

## Acceptance evidence

1. The four governance files are exactly the
human-updated sources
frozen by the index: oap/coding-
instructions/AGENTS.md (7,195 B, git
blob 361fcebc6230a43584d5b2e88715988582270d69,
SHA-256
b17e6133a8f1027cfb6172c728d6e023993ab84cbba4424d
0bf1e17189a2cb04)
and oap/strategic-instructions/AGENTS.md (10,473
B, git blob
b2a5e15a89e2bc1916e825a5fde4ce1c80c8fc04,
SHA-256
606a2f91ef4465f7812a99170ab51a6919b381d878e2ccbf
9451919d40f0d7a2),
the strategic installed copy (strategy home
AGENTS.md)
byte-identical to the canonical repository file
(same SHA-256
606a2f91ef...), plus oap/governance/CONTEXT-
BUDGET.md (1,360 B,
blob c3fccaac21b0d4eaa28d8b0d7cdc035d44c5ce48,
SHA-256
ae410e3239e0e31d2c0a3cdea7abdbb355945f9a760a7d77
d55755f836e43306)
and oap/governance/MANIFEST.json (8,683 B, blob
e278e894495b2f2c0c7be4d78349d09735d9c912,
SHA-256
c3c4e2e9d3919ff2e4fe0baf4e85b6b3f2a619e88d7589c0
44e64c048e857971).
Every mode/Git blob/SHA-256/byte count equals
the bound index and
each before_sha256 equals the exact base blob.
Both law diffs are
the latest human wording correction to the
evidence phrasing law
(nine replaced lines each:
"adversarial/negative ... first-person
attack procedures" retitled to "negative ...
first-person harmful
routines", the four paired test-voice examples,
and the rationale
sentence), no other law byte changed.
2. The four governance files agree with each
other and with the
harness: the six-file routine read set measures
exactly 51,614
UTF-8 bytes (AGENTS.md 772, coding law 7,195,
ARCHITECTURE-for-agents.md 19,814,
OAP-COMMUNICATION-coding-agent.md 4,949,
SECURITY.md 1,436,
TESTING.md 17,448) under the existing 52,000
ceiling, each
component ceiling still holds (772/2,048,
7,195/12,000,
19,814/20,000, 4,949/10,000), MANIFEST.json
rebinds the three
changed hashes and keeps coding_byte_ceiling
52,000 with
architecture_sha256 4b419053... unchanged, and
exact model tokens
remain UNMEASURED. The existing projection map
and governance
tests are preserved because the law coverage and
numerical
threshold still hold.
3. The product transfer is withheld exactly as
ordered:
src/slaif_raggedized_helper/source_admission.py
remains the exact
receiving preimage (14,533 B, blob
b665f55fabc7680bc8a8d9f05388adcbcfe36688,
SHA-256
d065fdf6787e73f89355ae9e578b53f8bb28d830306fd9dc
2a26b90700c93f54)
and tests/integration/test_evaluate_existing_ori
ginal_store_composition.py
is absent from the tree. The full 46-path
receiving preimage set
verifies with exactly the five intended deltas
(oap/active plus the
four governance paths), so the expected-pin
witnesses and every
009-ax/009-ay product path are preserved. No
donor ancestry is
introduced: donor implementation
a1cefbfc51aa2dd33b90a29a3b6fcae7e58f4086 and
report
2b7748c0ed582b7e180466c987ddccc67ef600a3 are not
ancestors of the
implementation head, and the donor parent
b0bed822c6f1724b702b962b3961a5f809baadf2 is only
pre-existing
branch history already reachable at the round
base (the 009-au
report commit).
4. Actual governance verification (python3
oap/bin/check_state.py
--repo-root .) exits 0: state ACTIVE, active
009-az, order resolved
and validated,
activation_matches_current_governance true,
manifest_sha256
c3c4e2e9d3919ff2e4fe0baf4e85b6b3f2a619e88d7589c0
44e64c048e857971,
declared_context_bytes 51614, exact model tokens
UNMEASURED, no
critical entries.
5. The OAP unittest inventory (python3 -m
unittest discover -s
tests/oap -v) exits 0: "Ran 92 tests in 64.421s
/ OK", zero
failures, zero errors, zero skips (29 ci-unit
diagnostics, 12
ci-unit partition, 10 ci-unit resources, 41
harness); raw log
unittest.log 14,304 B, SHA-256
18c4060d9cf86a4b8b3410902a082565149d8d56272f8622
042aa433aed46878.
6. The narrowed exact-scope verification ran
against the bound
index and the Root decision: the original six-
file checker
audit/009-az-check/check-exact-transfer.py
(SHA-256
64beebad4e51e53d84984cd1f5afea1f31652dfc44bca934
bfd61599a5d350f3)
describes the unfulfilled complete scope, so it
is not this
round's acceptance gate. The boxed narrowed
script exits 0: bind
OK (index/decision/base/donor identifiers), GOV4
OK, TRANSCRIPT OK
(order SHA-256 5ed81028..., active bytes exactly
"009-az" + LF,
both review copies byte-exact), PREIMAGES OK (41
unchanged, 5
intended deltas), PRODUCT WITHELD OK, no donor
ancestry
introduced, git diff --check clean over the
round range,
implementation scope exactly the four governance
files, transcript
scope exactly the four transcript paths; log 374
B, SHA-256
a6258ffbea1defe48a24edf367f1b0cdfa1e49468641e8ce
fb528a97a066fd24.
7. Report-only SELF child: sole parent =
implementation head
1731bcfc68b7211ad13f7b66af7189d0094e6be7, single
changed path =
this report, remote report bytes and ancestry
verified after push
by the report verifier and the post-publication
receipt. A report
cannot certify its own future push or checks.

## Verification

Ordered local proof in the fresh mode-0700
scratch
/dev/shm/009az-coding-GpJhqR, every proof
process taskset to one
core under timeout -k 5 120 prlimit --cpu=60
--as=1073741824 with
PYTHONDONTWRITEBYTECODE=1,
OPENBLAS_NUM_THREADS=1,
RAYON_NUM_THREADS=1 and a separate private 0700
TMPDIR:

1. RUN1 the narrowed exact-scope verification
(verify-four-file-scope.py over committed
implementation
1731bcfc68b7211ad13f7b66af7189d0094e6be7) - real
exit 0 (acceptance
6 above; log 374 B, SHA-256 a6258ffbea...).
2. RUN2 the actual governance verification
(python3 oap/bin/check_state.py --repo-root .) -
real exit 0
(acceptance 4 above).
3. RUN3 the OAP unittest inventory
(python3 -m unittest discover -s tests/oap -v) -
real exit 0
(acceptance 5 above; log 14,304 B, SHA-256
18c4060d...).

Live repository (working tree equal to the
implementation head):
the same governance verification exits 0 with
identical numbers;
git diff --check
d3243019f284b00f83e814972866180454ef0dcc..1731bc
fc68b7211ad13f7b66af7189d0094e6be7
is clean; git log shows the three linear single-
parent commits
(report -> 1731bcfc -> dd5e460c -> d3243019).
The two exact
hosted nodes (test_stable_existing_only_reader_s
erves_native_pin_load,
test_refusals_keep_descriptor_custody) remain
collected-only
evidence from the bound receiving preview
(record SHA-256
c8f0442f08c8c6a30a9bc662d29a4273a1f01938b4912727
e257d22aa3ddf957)
and were not re-executed locally. Mock/live
distinction: all local
checks are synthetic or disposable fixtures
(governance and
protocol tests only); GitHub reconciliation used
read-only
queries; no product behavior, model, service or
network resource
was exercised locally. No claim about this
report's future push
or CI; the separate post-publication receipt
verifies remote
publication and strategy records the report-head
CI facts.

## Documentation impact

Only bound governance documentation changed: the
two law files
(coding and strategic evidence phrasing law
wording correction),
CONTEXT-BUDGET.md (measured 51,614 B routine
read set, 52,000
ceiling, UNMEASURED tokens) and MANIFEST.json
(three rebinds,
coding_byte_ceiling 52,000). No product
documentation changed
because no product behavior changed.

## DHA and boundaries

Ordered DHA Decision: NONE; no critical append,
no candidate
reported, CRITICAL register untouched. Preserved
resources: every
unrelated file, worktree, private configuration
and prior
transcript byte; the bound review copies are the
only new
oap/reviews entries; the product preimages and
the expected-pin
witnesses are untouched. No merge performed, no
auto-merge
enabled, no release/tag/deployment, no runtime
setting, model,
provider or profile change, and no activity
against external
protected resources beyond read-only GitHub
reconciliation.

## Limitations and remaining work

Result PARTIAL by the Root decision: the exact
OriginalStore
product transfer is unfulfilled and held before
publication
(donor acceptance gap recorded in the decision
finding above); no
exact product acceptance is awarded. Report-head
CI is PENDING at
publication: recorded for the separate strategic
review of the
exact reviewed head, the expected gate is all
five required jobs
and every required step, with ordered 1,440 +
1,998 unit passes
and exactly 1,008 integration passes in each
Product (the 1,010
integration expectation applied only to the
withheld complete
six-file scope). Per the decision, a bounded
corrected
OriginalStore seam with hosted proof is awarded
in a later round
after this report and current head are
reconciled. Representative
baseline NOT_RUN. Whole 009 PARTIAL. Exact model
tokens
UNMEASURED. No scope deviation; scratch
artifacts preserved in
/dev/shm/009az-coding-GpJhqR.
