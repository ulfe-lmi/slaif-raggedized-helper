# OAP Work Order — 009-au

Status: FINAL
Identifier: 009-au
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
PR number: 11
Expected active: 009-at
Base commit: a6daecf947447eb393722f2a8e818a1b172824e1
Provenance: H activated MVP, A ARCH 13.3–13.4 and 23.4–23.5, E exact native stable grade metric fixture fault, I independent exact serializer/pure source proof
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Repair the stable grade metric witness using the actual decoded
report variant and exact legacy observed ranking. Preserve both
passing refusal witnesses. Whole 009 PARTIAL, baseline NOT_RUN,
DHA NONE.

## Dependencies and current state

Exact prior run 44909856462 attempt 1 on PR 11 passed all three
OAP jobs and both Product ordered unit steps (1,440 + 1,998).
Both Products ran 1,003 integrations, 1,002 passing with the
same sole stable metric fixture failure on line 766. Early denial
and final generation mutation passed on both.

Root terminal review `audit/009-at-check/Root-terminal-review.json` SHA256 `63aa21cd999ef3069b563c0ca841d79c22971530d13cfa4d13d7a298c9dec00a`.
Prior resolution `workorders/009-au-prior-resolution.json` SHA256 `fe4cd8a2fd2e2c43bde8a7d506fc68d902280042d1b427a551d44de2051a2545`.
Bounded pure verifier `audit/009-au-check/check-pure-metric.py` SHA256 `a7a439f28f4cf2ee712dc73a6b8da8c0a093beeb3f59af1b27e2e3e5a3b945e9`.

Base remains this exact failed report and main remains
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`.

The exact witness source preimage SHA256 is
`9cfa43d9b039e144706370099e3b5991df3308f145c91aae516d67942f0c7b0e`.
The actual shared grade serializer inserts each variant's encoded
JSON object as a value. Parsing the report sets each value to a dict.
The exact bounded source-only proof at
`audit/009-at-check/Root-pure-variant-shape.log` reproduced the
erroneous second decode with the actual serializer assembly.

## Allowed paths and scope

The sole transcript has the exact order, active with one LF and
byte-exact `oap/reviews/009-au-prior-resolution.json` from the
strategic prior-resolution file. The next sole-parent implementation
changes only `tests/integration/test_current_graded_cohort_composition.py`,
and only the existing stable metric assertion block. Preserve both
other test functions verbatim, all three node names, the canonical
stage fixture and every other source/test/doc byte. One report-only
child. No shared tooling edits.

## Non-goals

No product, budget, workflow, runtime, grade/delegated I/O count
change, native local run, new pytest node, publisher or CLI transfer,
baseline run, merge, deployment or release.

## Acceptance criteria

1. Read each report variant directly from the already decoded
   `grade_doc["variants"][name]` dict. Preserve the exact query ID
   matching, score recomputation from genuine legacy dense, lexical
   and fusion rankings, and full equality of parsed metric rows.
   In h1, derive retrieved status at each cutoff from membership
   of the declared grade-3 chunk in the actual ranking prefix. Check
   the single positive's ideal gain of 7 and the expected relevant
   count and recall. Do not encode an assumed modality outcome.
   Retain the existing h4 undefined empty-gold checks.
2. Pass the exact bounded pure check
   `audit/009-au-check/check-pure-metric.py` with the assigned
   physical source root as its argument and that root's `src` on
   PYTHONPATH. It extracts the existing stable `for name, ranking
   in rankings.items()` loop and exercises it against decoded
   variants built by the actual serializer and actual metrics. It
   uses h1 where lexical retrieves and dense misses, plus a rank-2
   hit and h4 empty gold. Preserve that loop shape so the check
   exercises the source being published. This is a pure check.
3. Verify transcript, single test-only implementation, report-only
   child, unchanged product and other witnesses, and exact three
   names. Local proof requires 361 focused units, exact three
   integration nodes collected only, scoped one-core Ruff and two
   fresh physical imports. Exact remote report gate requires all five
   jobs and every step green, ordered 1,440 + 1,998 units and 1,003
   integrations in each Product.

## Verification and negative evidence

Existing boxed venv, actual physical source, private 0700
`/dev/shm` TMPDIR and independent pytest basetemps. CPU60, AS1GiB,
wall120 and KILL5. Use `OPENBLAS_NUM_THREADS=1`,
`PYTHONDONTWRITEBYTECODE=1`, pytest `-o addopts= -p no:cacheprovider`,
and one allowed Ruff CPU with one Rayon thread. Record actual exits,
log digests, exact scopes and physical origins. Native proof is
hosted only. Preserve the failed 009-at head and run evidence.

## Documentation

Record the exact fixture fault and new pure proof in the immutable
report. Preserve all earlier report and repository documentation.

## Runtime and protected resources

Existing bounded synthetic test resources only. No live data, model,
GPU, credential, service access, dependency setup or release action.
Preserve the human-selected execution settings.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Use existing PR 11. Push the exact transcript, test-only implementation
and report-only child once. Verify the remote report, then use the
single owned response wrapper outside the bounded local proof
envelope. Record CI pending in the report.
