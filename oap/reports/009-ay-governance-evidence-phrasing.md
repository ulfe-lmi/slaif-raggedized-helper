# OAP Coding Report — 009-ay

Identifier: 009-ay
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: c5fca03976d647a8050396dcb489c4af6c25ffc2
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-ay
(AMEND_EXISTING_PR on PR 11, round
base 17b33ae4074b3478797011d39ceb94e28b4c4cf4,
the exact 009-ax report head whose prior
resolution ACCEPT_EXACT_SCOPE_
CONTINUATION_ONLY recorded GitHub run
44932837127 attempt 1 all five required
jobs and every required step SUCCESS at
both Products, ordered 1,440 + 1,998
units and exactly 1,008 integrations
each; remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
GitHub reconciliation before any edit:
PR 11 is the unique open non-draft PR
with head branch
oap/009-evaluation-baseline at exactly
the round base (headRefOid
17b33ae4074b3478797011d39ceb94e28b4c4cf4,
base main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
autoMergeRequest null, state OPEN,
MERGEABLE), local HEAD equaled the base
and the working tree carried only the
strategy activation (oap/active exactly
7 B "009-ay" + LF, the new untracked
order byte-identical to the strategic
workorders copy, SHA-256
f39811f582b94c463e9b604842a3b7311729bc2909b0a2f6bb10c85c7146b0ef)
plus the six pre-prepared governance
files, each already equal to the bound
index by mode, Git blob, SHA-256 and
byte count. The bound review index was
copied byte-exact to
oap/reviews/009-ay-governance-evidence-
phrasing-index.json (2,786 B, SHA-256
6f83b784ac1e3787790445e2607a15fc5c20d7590c5bad013e4ca88190a5b652)
and the prior resolution to
oap/reviews/009-ay-prior-resolution.json
(1,990 B, SHA-256
2ad1621a826c54bea383000a82fb1e2e50d40d243feaba7fe6fa7084efb321e4).
Three linear commits: transcript-first
four-path commit
7ec5916ff04301fbdf08816ab69ef840152e899d
(exact order, oap/active 009-ax to
009-ay, both byte-exact review copies);
implementation six-path commit
c5fca03976d647a8050396dcb489c4af6c25ffc2
(the bound bundle only); this report-only
SELF child.

## Acceptance evidence

1. Both law files are exactly the
human-updated sources frozen by the
index: oap/coding-instructions/AGENTS.md
(7,188 B, git blob
b35ed37d41af2d531bbcb8fb04aecda3747b5bf0,
SHA-256
e60bb0d865f5c23edfd0dc22060afccce98bc972e48230c2885d30c7bbec033b)
and oap/strategic-instructions/AGENTS.md
(10,466 B, git blob
38fac3eee411e62dfd57bf4b88c8de36e0739f84,
SHA-256
dc2a30eb6d48b2ca8e4ef6d91a36cf8798bcb8bc059ca3a1a182f5f46b75083f).
The strategic installed copy (strategy
home AGENTS.md) equals the canonical
repository file byte-for-byte (same
SHA-256 dc2a30eb...). Both diffs are
pure additions of the evidence phrasing
law (27 lines each) that frames every
adversarial/negative observation as a
bounded test, keeps complete
measurements and technical facts, and
retires the old lane token for the
credential lifecycle vocabulary; no
other law byte changed (before-sha256
6ee5dae3... and 94516ab9... match the
exact base blobs).
2. The four dependent governance files
agree with each other and with the
harness: the six-file routine read set
measures exactly 51,607 UTF-8 bytes
(AGENTS.md 772, coding law 7,188,
ARCHITECTURE-for-agents.md 19,814,
OAP-COMMUNICATION-coding-agent.md 4,949,
SECURITY.md 1,436, TESTING.md 17,448),
each previous component ceiling holds
(772/2,048, 7,188/12,000, 19,814/20,000,
4,949/10,000), the bounded aggregate
ceiling is 52,000 in CONTEXT-BUDGET.md
and MANIFEST.json, and exact model
tokens remain UNMEASURED. The only
harness change is the one approved
ceiling literal, 50,000 to 52,000, in
the inactive context test (single-line
diff); the stale-hash, malformed-order
and oversized-context harness checks
are preserved and pass (92-node
inventory below).
3. Exact prior base 17b33ae... (PR 11
report 009-ax), the two commit scopes
(four transcript paths; six
implementation paths, staged and
committed with mode/blob/SHA-256/bytes
equal to the bound index) and the
report-only SELF child (sole parent =
implementation head, single changed
path = this report, verified after push
with the report verifier). The full
six-file set was compared against the
bound index in the working tree and in
the committed implementation (git
ls-tree of the implementation head: all
six entries 100644 with the exact
bound blobs). git diff --check over the
round range is clean.
4. Published on exact PR 11 (the unique
oap/009-* PR). Report-head CI is
PENDING at publication: a report cannot
certify its own future push or checks.
The recorded base evidence is run
44932837127 attempt 1 SUCCESS at
17b33ae... with ordered 1,440 + 1,998
units and 1,008 integrations per
Product; the report-head gate is the
same five required jobs, every required
step and the same ordered counts,
recorded here for the separate
strategic review of the exact reviewed
head.

## Verification

Ordered local proof in a fresh
mode-0700 /dev/shm scratch
/dev/shm/009ay-coding-1795571046 over
a pristine tree (git archive of
implementation
c5fca03976d647a8050396dcb489c4af6c25ffc2,
physically re-verified: all six bundle
files equal the bound index by SHA-256,
git blob and byte count, the four
transcript paths byte-exact, the
six-file read set exactly 51,607 B), a
scratch-local disposable git fixture
for the governance checker, and every
proof process under taskset to one core
with timeout -k 5 120 prlimit
--cpu=60 --as=1073741824,
PYTHONDONTWRITEBYTECODE=1,
OPENBLAS_NUM_THREADS=1,
RAYON_NUM_THREADS=1 and a separate
private 0700 TMPDIR:

1. RUN1 the bound-index comparison -
real exit 0: six files sha256/blob/
bytes all true, transcript active/order/
index-copy/prior-copy all true, read-set
total 51,607 under the 52,000 ceiling.
2. RUN2 the actual governance
verification
(python3 oap/bin/check_state.py
--repo-root .) - real exit 0: state
ACTIVE, active 009-ay, the order
resolved and validated,
activation_matches_current_governance
true, manifest_sha256
193effdb8e37b1e673ae7ac2c1ae21fec1d36454a012bd61b56fdd98fc3bce4a,
declared_context_bytes 51607, exact
model tokens UNMEASURED, no critical
entries.
3. RUN3 the OAP unittest inventory
(python3 -m unittest discover -s
tests/oap -v) - real exit 0: "Ran 92
tests in 62.303s / OK", zero failures,
zero errors, zero skips (29 ci-unit
diagnostics, 12 ci-unit partition, 10
ci-unit resources, 41 harness); raw log
unittest.log 14,250 B, SHA-256
f0360ee39fbf5192d133813da2ba22ddce24deac43115289444553c0cc18bbba.

Live repository (clean worktree equal
to the implementation head): the same
governance verification exits 0 with
identical numbers; git diff --check
17b33ae4074b3478797011d39ceb94e28b4c4cf4..HEAD
is clean; git log shows the three
linear commits with single parents
(report -> c5fca039... -> 7ec5916... ->
17b33ae...). Mock/live distinction: all
local checks are synthetic or
disposable fixtures (governance and
protocol tests only); GitHub
reconciliation used read-only queries;
no product behavior, model, service or
network resource was exercised locally.
No claim about this report's future
push/CI; the separate post-publication
receipt verifies remote publication and
strategy records the report-head CI
facts.

## Documentation impact

Only the index-bound governance
documentation changed:
CONTEXT-BUDGET.md (measured 51,607 B
routine read set, 52,000 ceiling,
UNMEASURED tokens) and DISTILLATION-MAP.md
(one S11 projection row), together with
the two law files, the MANIFEST.json
rebinding (five file hashes,
coding_byte_ceiling 52,000) and the one
harness ceiling literal. No product
documentation changed because no
product behavior changed.

## DHA and boundaries

Ordered DHA Decision: NONE; no critical
append, no candidate reported, CRITICAL
register untouched (no entries).
Preserved resources: every unrelated
file, worktree, private configuration
and prior transcript byte; the bound
review copies are the only new oap/
review entries. No merge performed, no
auto-merge enabled, no release/tag/
deployment, no runtime setting, model,
provider or profile change, and no
activity against external protected
resources beyond read-only GitHub
reconciliation.

## Limitations and remaining work

Report-head CI PENDING at publication
(recorded above for strategic review of
the exact reviewed head; expected gate
all five required jobs and steps at
ordered 1,440 + 1,998 units and 1,008
integrations per Product). Representative
baseline NOT_RUN. Whole 009 PARTIAL.
Exact model tokens UNMEASURED. No scope
deviation; scratch artifacts preserved
in /dev/shm/009ay-coding-1795571046.
