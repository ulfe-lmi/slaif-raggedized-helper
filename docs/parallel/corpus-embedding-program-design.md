# Complete selected-source embedding program — strategic D0 contract

Status: FINAL DESIGN; finalized order/live reconciliation required before activation.
H full-MVP/parallel; A original007.3/A08/A12/A16/A27 and ARCH11.2/12; I remaining-software
inventory4d71 at frozenb0ca; E current one-batch APIs do not prove coverage of an entire
selected corpus or stable batch boundaries. DHA NONE. First proof-sized part of corpus
orchestration, independent of the unfinished GPU producer; not a competing batch/job format.
Execution/resume/operator command follow separately after producer admission. No numeric jump.

## Scope and API

Add corpus_embedding_program.py, new unit/actual composition/API/design/order. A SMALL change
to existing retrieval_representation.py may factor ONLY its pure raw formatting and message-
size preflight so the real existing build_many and this planner share one implementation.
Preserve all public APIs, accepted input semantics, default policy/fingerprints/representation
IDs/text/receipt behavior, native source/count admission, error/privacy/resource bounds. No
native worker, ingestion, source store, GPU/CPU producer, job/journal, CLI, snapshot, dependency,
sourcebook/law/CI modification. Do not implement source rendering independently a second time.

build(originals,derived,bundle_ids,*,policy=None,batch_policy=None,program_policy=None)
returns immutable SourceProgram DATA. Borrow actual existing OriginalStore and derived Store;
never close/write them. bundle_ids is an exact tuple of1..128 sorted unique bare64lowerhex
actual ingestion container IDs. Each selected bundle contributes ALL actual validated chunks,
never just a prefix or caller-supplied claimed row list. Reject duplicate original revision
selections (including two extraction bundles for the same revision) and global duplicate chunk
IDs. Distinct selected document versions remain permitted if actual revision IDs differ.
This describes completeness of the explicitly supplied selection, not discovery/authorization
or completeness of an external repository/catalog.

parse(program_bytes) returns immutable DATA after strict canonical structure/integrity checks,
without stores. validate(originals,derived,program_bytes) freshly rebuilds from the actual
selected containers and declared supported policies and requires byte-identical whole program;
it returns the fresh actual build. Parsed/frozen/caller-created objects and IDs are never source
proof, current rights, native count, execution, completion or readiness authority. The future
executor must fresh-validate and use actual producer/job/output/current-policy checks.

SourceProgram exposes source_program_id (sha256: plus64hex), program_bytes, row_count,
batch_count and immutable batches of BatchSelection. Each BatchSelection exposes batch_index,
bundle_id, first_ordinal and tuple chunk_ids. Pure parsed views are DATA; do not trust object
construction/mutation as authority. The ID hashes canonical bytes under fixed domain
b'slaif-embedding-source-program-v1\n'; no circular ID in its own manifest. Source-program
identity is distinct from model space, execution fingerprint and existing per-batch job ID.
Changing model/runtime still invalidates actual execution/job reuse even if source data did
not change. No full execution records or model provenance are fabricated by this planner.

## Source and shared formatting

For each actual ID call REAL ingestion_store.load(originals,derived,id). It revalidates current
original-backed bundle bytes; retain the actual validated metadata/chunks only while working
on that source. Read actual metadata JSON hash, revision/extraction and scope from this result,
not a supplied DTO/callback or integrity hash alone. Use canonical source order (input sorted
bundle IDs), then chunks sorted by actual chunk_id. Record this ordering; do not change text,
case, punctuation, Unicode, source version or heading order.

Factor one appropriately named PRIVATE pure formatting helper in retrieval_representation.
It must be used by actual build_many AND this actual planner. Preserve original title + each
nonempty heading + original body, two LF separator, original Unicode, no prefix/truncation/
padding, original type/strict encoding/100000codepoint/200000request-byte admission. Message
size is EXACT existing native-count request JSON with text,pair=None,nonce='0'*32,
role='bge_representation',artifact=0, ensure_ascii=True/compact separators and finalLF. The
helper may return text and its exact wire-byte count; it grants no validation/permission and
starts no session. Keep native Session/count/receipt/ID computation inside existing build_many
with its prior guards and actual source validation. No callback supplies formatting or proof.

Planner computes rendered SHA256 and size facts from this SAME actual helper, without native
count/model/session/process work. Source-program token eligibility is NOT_RUN; actual native
count and GPU frame/resource compatibility remain required at execution. Respect the existing
representation Policy and BatchPolicy ceilings; snapshot/copy/revalidate exact dataclass
values (including frozen-object bypasses), not unchecked caller attributes. No increased old
limits or policy-version change to fit input. Program grouping never claims hardware fit.

## Deterministic bounded grouping and closed canonical data

Greedily pack each source's ordered chunks into nonempty batches satisfying ALL exact
BatchPolicy.max_items, max_total_codepoints and max_total_request_bytes. Never cross a source
bundle in one batch (the existing producer accepts one source bundle). Close a batch before
adding a row that would exceed any cap. A single row that cannot fit refuses the entire
program, never truncates/skips it. Every selected chunk occurs exactly once; batch ranges are
contiguous, disjoint and cover all rows, including final partial batches. Unchanged sources/
policies give identical bytes and boundaries. A changed selection may conservatively form a
new program; cross-program arbitrary regrouping or per-row salvage is NOT a new requirement.
The future executor chooses a compatible batch policy or explicitly replans before execution;
it cannot silently repartition a frozen program to conceal GPU frame/row incompatibility.

Canonical ASCII JSON, sort_keys/compact separators/no floats/duplicates/nonfinite/unknown
keys/whitespace aliases/trailing content. Top-level exact fields:
 schema=1, kind='embedding-source-program-v1', token_eligibility='NOT_RUN',
 representation_policy, batch_policy, program_policy, sources, rows, batches.
Policies contain exactly their supported dataclass fields. Source records exactly:
 bundle_id, bundle_metadata_sha256, revision_id, extraction_id, source_scope_sha256,
 first_ordinal, row_count.
Rows exactly: ordinal, source_index, chunk_id, rendered_sha256, codepoints,
 native_request_bytes.
Batches exactly: batch_index, source_index, first_ordinal, row_count,
 total_codepoints, total_native_request_bytes.
All digests are bare64hex except existing revision/extraction/chunk IDs, whose actual
canonical hash forms must follow existing source helpers (do not invent replacements).
source_scope_sha256 uses existing canonical embedding-source-scope-v1 fingerprint convention.
No original title/body/headings/path/URL/private text in output or diagnostics. Per-source
metadata digest pins its policies and provenance; heterogeneous source policies are not
silently relabeled compatible with a later snapshot. This is source DATA only.

parse admits strict types (bool is not int), policy ceilings, exact count/size/work bounds,
source uniqueness/canonical ordering/contiguous ranges, global row uniqueness, per-source
sorted IDs, source-row partitioning and exact batch coverage/sums/caps. It cannot verify that
an internally consistent omitted row corresponds to an actual selected source; validate must
fresh-rebuild and compare. No store/model execution inside parse. Actual source/model checks
are never bypassed because a manifest is canonical or an ID matches.

New frozen ProgramPolicy has fixed version='embedding-source-program-policy-v1' and positive
integer ceilings max_bundles<=128 (default128), max_rows<=65536(default65536),
max_batches<=65536(default65536), max_program_bytes<=16777216(default16777216),
deadline_ms<=120000(default120000). May lower, never raise. Bounds apply before additional
retention/work whenever facts are available: reject next source before loading if no capacity
remains; once actual bundle count is known reject whole over-budget source before rendering
its rows. Stop on first observed count/work/output overflow, no unbounded flatten/sort/copies.
Retain bounded IDs/digests/counts, not all rendered texts or all validated source bundles.
Maintain incremental output/accounting bounds before retaining later rows; one final giant
serialization followed by size rejection is insufficient. Conservative exact/lower-bound
budget admission may reject explicitly but must not silently skip source input. Serialize
once final within bounds; report any bounded temporary encoding honestly. Cooperative checks
around sources/rows/rendering/parsing/serialization; no hard I/O/preemption/RAM guarantee or
new hard worker cap. >128 rows and illustrative20000 are supported selections within explicit
policy bounds, not measured throughput promises. Over-ceiling input refuses wholly, not a
new hidden lower corpus cap. Public ordinary ProgramError is content-free; preserve original
non-Exception and attempt no borrowed-resource cleanup.

## Finite evidence

1. Actual original/derived stores, real existing synthetic native ingestion fixture construction
   BEFORE planner calls. Multiple actual selected bundles, actual source/current rendering,
   >128 total actual chunks and final partial batches. No native/process/model/start/storewrite
   during build/parse/validate. Every actual selected chunk exactly once, deterministic reorder
   rejection/stable repeated bytes, all counters/ranges/sums/caps match, borrowed stores usable.
   If an existing fixture cannot produce129 legitimate chunks within bounds, build a smaller
   valid-chunk policy via actual native pipeline; no fabricated complete bundle/validator.
2. Original/corrupt source/bundle/metadata changes, missing/duplicate sources/revisions/chunks,
   wrong version/policies/frozen mutation, boolean/unknown/oversized input, one unfit row, exact
   count/size boundaries/early next-source refusal, Unicode/escaped request size and changed
   headings/body/scope must refuse or explicitly produce changed program, not stale equality.
3. Compare existing build_many output BEFORE and AFTER pure factoring with actual same source
   and native tokenizer: text, rendered/input/representation IDs, count/metadata semantics
   identical. Original source may be loaded as isolated witness; no product restore/switch.
   Existing focused representation/batch-plan tests and actual source composition as relevant,
   not repeated whole suites. Preserve baseline APIs and all model/native safety guards.
4. One original actual completeness guard control: valid actual program, internally consistent
   candidate omits a selected source chunk with adjusted counts/ranges; parse may admit DATA,
   fresh validate refuses. Temporary isolated module omits ONLY final actual rebuild equality,
   actual source reconstruction still runs and returns fresh COMPLETE correct program while
   accepting the wrong candidate; original refuses again. State exact effect (not forged
   output). Or equally meaningful specific actual source-completeness guard control; never
   require one omission defeat independent later guards or substitute fake authority.
5. Record exact source/readset/commands/counts/logs/hash/limits/failures and strongest argument
   against admission. No fabricated20000-source integration test: a large purely structural
   codec case is labeled DATA only; actual>128 proves composition. No completion/resume/model/
   current-policy/efficient-bulk/hardware/parity/license/Ready/ICA/MVP claim. Fresh affected
   opposite review and later canonical integration/currentCI required.

Allowed SEVEN paths ONLY: src/slaif_raggedized_helper/retrieval_representation.py (purefactor);
NEW src/slaif_raggedized_helper/corpus_embedding_program.py;
NEW tests/unit/test_corpus_embedding_program.py;
NEW tests/integration/test_corpus_embedding_program_composition.py;
NEW docs/parallel/corpus-embedding-program-api.md;
NEW docs/parallel/corpus-embedding-program-design.md (EXACT this contract);
NEW order path finalized by Root. No producer/journal/worker/CLI/sourcebook/law/dependency/CI
changes. Per test invocation120wall/AS1GiB/CPU30/five threads1/no bytecode/private basetemp,
cached app and existing actual synthetic native0.21 fixtures only. No GPUfake/model/framework/
Tensor/driver/service/install/download/network/credentials/real corpus/sharedfixture edit,
unknown process/otherpane/nestedagent/profileauth change/push/merge/release/deploy/FIFO replay.
Ruff120wall/thread1 allocator exception disclosed, not pytest cap change. Root checkpoints
FIX/REPORT before immutableSELFreport and ONE normal response; no premature partial handback.
