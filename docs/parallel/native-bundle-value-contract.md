# Native ingestion bundle value contract v1

Status: FINAL DEVELOPMENT CONTRACT
Authority: Root strategic D0 within architecture8.1/8.2/9.3/9.4/20.2/25.2.
This contract defines the bounded value layer. It does not activate coding, accept any software,
prove execution, authorize target resources or close006. A finalized lane order supplies execution.

## Scope and split

One bundle fixes one admitted revision, one structured-text or native-PDF extraction, one
native chunk policy, exact query and ordered three tokenizer declarations. Keep typed value
admission/serialization separate from descriptor-safe member publication and installed CLI.
Prefer bytes-first entrypoints so untrusted model_copy DTOs cannot trigger recursive dumping
before resource admission. The later private operator pipeline creates these bytes from owned
actual extractor/native results; loading receives bounded immutable bytes from the memberstore.
A semantic validator may use OriginalStore.read_verified with the extraction2MB cap; it never
accepts a source path or executable from a document. No tokenizer/model invocation on load.

The initial value codec can return canonical metadata JSON bytes plus fixed named memberbytes,
or validated immutable records for a caller's Store.publish. The integrated loader must call
Store.load then validate every semantic member against the actual OriginalStore. Never let
successful opaque Store.load alone become a trusted native ingestion result. Keep errors typed
and input-free, successful result immutable, no partial publication/result from exhausted work.

## Metadata v1

Canonical UTF8 JSON object, strict schema/unique keys/finite numbers/valid Unicode and bounded
bytes/depth/nodes. Required metadata concepts (exact selected field schema below):
- schema_version: integer1; kind: native-ingestion-bundle.
- revision_id: exact sha256-prefixed Source revision ID, reverified from OriginalStore.
- extraction: full admitted Dependency, adapter enum structured_text/pdf_extraction, declared
  native/partial status and bounded uncertainty, coverage kind unicode_codepoints/pdf_pages.
- chunking: complete exact chunking.Policy fields, exact query<=10000codepoints, ordered
  tokenizer declarations for bge_body/bge_representation/reranker_pair, exact policy definition
  and policy_id. No artifact/runtime filesystem paths. Definitions retain artifactSHA/backend/
  declared model_revision/preprocessing and fixed mode/serialization; derive their fingerprints.
- counts: exact expected Block/Chunk/Neighbors/Receipt/coverage or page counts used to check
  all records; not hints allowing unparsed tails. All counts strict no-bool nonnegative integers
  within selected finite limits. Native successful bundles require nonempty chunks/blocks.

The outer derived-store manifest binds exact metadata and member name/order/size/SHA256. Do
not duplicate source Scope as an authority: derive it from the reverified actual revision.
Unknown source.version remains a legitimate ingestion value and denies later reader access;
this codec must not silently reinterpret unknown/empty source versions. Processing approval
is metadata, not authentication, redistribution permission or current serving authorization.

## Members

Fixed names and kinds, never user-provided paths:
- blocks: admitted Block JSONL in exact extractor order, each exact revision/extraction.
- coverage: versioned JSON with exact fields. Text: ordered block_id/start/end codepoint spans.
  PDF: sequential1-based page/status entries and bounded uncertainty. Do not confuse PDFpoints,
  codepoint offsets, bytes and native token indices.
- chunks: admitted Chunk JSONL in output order, no duplicates or ignored records.
- neighbors: admitted Neighbors JSONL, exactly one per chunk, exact reciprocal previous/next
  adjacency in that order and null at both ends, beyond Registry's compatibility-only checks.
- receipts: exact bridge-v1 JSON, exactly three Count receipts per chunk in role order, no
  additional, duplicate, absent or input-bearing fields. Its current8MB ceiling remains.

Reuse accepted provenance_jsonl API for existing types. Current1MiBrecord/16MiBstream/4096record
caps remain until measured valid required outputs justify a deliberate format/policy evolution.
If needed later, ordered chunks_00..chunks_03 shards may each use16MiB and aggregate4096chunks;
all shard counts/order/IDs and total member count/size must be checked, without silently pruning
source. Do not implement sharding merely from theoretical size guesses. The capacity study
completed only two small outputs and discovered a more immediate native-call bottleneck.
Storage64MiBmember/96MiBtotal admission ceilings do not prove this codec/native/RSS capacity.

## Required semantic validation

1. Admit raw byte kinds/counts/cumulative sizes BEFORE parsing/copy/UTF8 conversion/hash work;
   bound all decoded schema/tree/collection/scalar work and a measured cooperative deadline.
   Verify all stream hashes/framing/counts and no unknown members or trailing bytes. Exact
   boundary negative tests must intercept forbidden parsing/opening/materialization where useful.
2. Read verified actual source/revision within2MB, derive catalog, validate extraction fingerprint
   equals Dependency.definition, construct Registry for that revision/dependency/complete blocks.
   Unique contiguous block order and ID/text hashes, exact adapter origin/status/metadata shape.
3. For text, decode original strictly, coverage tiles all codepoints with no gap/reorder/truncation,
   every block.text equals its original source slice, concatenation equals entire original. Preserve
   CRLF/combining/astral/control characters and original unit/table/warning/anchor metadata.
   Recompute documented deterministic structural block IDs; no normalization or tail trimming.
4. For PDF, bind page records/native blocks/anchors/finite ordered geometry and explicit partial
   visual-needed status; raster/vector pages do not become complete. Recompute current native
   block IDs from their recorded inputs. Original integrity and record consistency do not prove
   faithful extraction afresh from the PDF. Trust the fixed approved producer path and document
   that trust; no nonce/hash masquerades as an attestation. Loading does not launch a parser.
5. Registry.bind_chunk on every chunk, exact revision/extraction/policy, unique output IDs, complete
   original fragment interval coverage for every extracted block, explicit separators and exact
   reconstructed text. Overlap may repeat coverage but gaps/tail loss must refuse. Preserve
   headings/table original headers/units and check recorded heading path belongs to source units.
6. Recompute ordered tokenizer-definition fingerprints exactly as the accepted bridge does:
   version/artifact_sha256/backend/role/model_revision/preprocessing/mode/serialization, canonical
   ensure_ascii JSON. Recompute policy definition with full policy, identities, query-input digest
   and serialization; policy_id must match all chunks. Do not improvise a near-equivalent hash.
7. For every chunk, require exactly3 available TokenCounts and matching receipts. Body input is
   chunk.text; representation is concatenated heading_path+body; pair is exact query+representation.
   Validate exact native input digests, role/mode/serialization/artifact/backend/declarations,
   count ranges and chunk count/provenance OBSERVED_LOCAL_NATIVE_TOKENIZATION:<fingerprint>.
   Check stored body/representation/fullpair count budgets. Special tokens are already included.
8. The three exported receipts do NOT contain the query-only or empty-query-passage counts used
   internally for query-reserve admission. That admission is a trusted producer execution
   invariant, not independently replayable from three receipts. Do not invent missing counts,
   fresh tokenizer observations, cryptographic execution proof or deployed inference equivalence.
   Revalidation checks mechanical consistency; the trusted producer must be the actual fixed
   native build, and later019/model preprocessing gates remain mandatory.

## Proof and closure

Positive owned OriginalStore -> actual structured and PDF extraction -> actual isolated native
counts/chunks -> value codec -> descriptor store -> newinstance/process load -> complete fresh
source/Registry/neighbor/receipt validation. Include distinct rights/version revisions sharing
bytes, real Unicode, procedure/warnings/table units/headers, conditional overlap and no-tail-loss.
Negative mutations: original/revision/ACL/extraction/coverage/chunk deletion/reorder/crosssource/
neighbor/policy/query/definition/role/count/input digest/provenance/status/corrupt bytes and every
finite resource boundary. Empty/textless PDF cannot fabricate a native-success chunk bundle;
retain original and explicit visual-needed/no-native-chunks failure/status until later016 path.

Only after storage/value/loader acceptance, add thin installed private chunk/inspect route with
fixed adapters, explicit trusted runtime/tokenizer configuration, bundleID/status safe JSON,
nonzero typed errors, help/retry/idempotency. No implicit download/inference/network/GPU or
source-defined paths/models/executables. Full006 requires that usable durable journey and all
original criteria, actual current-head CI and exact source coverage. Full architecture text+
visualMVP/hardware/domain/licensing/ICA gates remain open. A separate finalized order is required for each implementation/integration.

## Exact selected schema and API obligations

Use a bytes-first validate/canonicalize API taking trusted OriginalStore plus metadata bytes and
an immutable tuple of(name, bytes) pairs; return immutable validated records plus canonical bytes
suitable for the separate member store. No disk publication/CLI in this layer, and no direct
unvalidated native Result/Chunk/Count DTO admission. Clear helper names may follow local style.

Metadata has EXACT schema_version,kind,revision_id,extraction,chunking,counts fields:
- schema_version strictinteger1, kind native-ingestion-bundle.
- extraction EXACT dependency,adapter,status,coverage_kind,uncertainty. dependency is full
  admitted Dependency. adapter structured_text or pdf_extraction. Structured text status
  complete_text and coverage_kind unicode_codepoints; PDF native_text or partial_visual_needed
  with pdf_pages. uncertainty bounded nonempty<=1024characters, no false freshness claim.
- chunking EXACT policy,query,definitions,policy_definition,policy_id. policy contains all exact
  recognized fields of the trusted installed chunking.Policy; reject unknown/missing fields and
  instantiate that actual class. query is string0..10000characters. definitions is ordered3items,
  each EXACT role,artifact_sha256,backend_version,model_revision,preprocessing. Roles/body/rep/
  pair order fixed; artifactSHA raw64hex, backend0.21.4, revision/preprocessing1..256characters.
  Derive fixed mode and serialization and reproduce bridge definition fingerprints. Reproduce
  native policy definition version1/kind observed-local-native/policy/definitions/query_input_sha256/
  serialization, including every recognized policy field; no near-equivalent invented hashing.
- counts EXACT blocks,chunks,neighbors,receipts, strictintegers. Successful native bundles have
  1..4096blocks/chunks, neighbors=chunks, receipts=3*chunks<=12288.

Members EXACT fixed order blocks,coverage,chunks,neighbors,receipts; names are never paths.
Coverage JSON EXACT schema_version,kind and spans (codepoints) or pages (PDF). Each span
EXACT block_id,start,end; each PDF page EXACT page,status. No unknown keys or silently ignored
records. Dependency is metadata, not a separate stream. Receipts retain bridge-v1 exact fields.

Before parsing, input caps: metadata256KiB; each existing JSONLstream16MiB/perrecord1MiB/4096
records; coverage2MiB; receipts8000000bytes; at most16namedmembers and96MiBtotal. This v1
requires exactlyfive members and does not yet shard. Bound decoded nodes/depth/scalars and
aggregate work explicitly (including<=1048576sourcefragments, as allowed maximum4096*256,
with tighter actualstream/work checks), default30s cooperative deadline checked through final
successful return. Do not assert fixedRSS/hardblockedfilesystem interrupt. No policy enlargement
or dropping source for easytests. Future demonstrated needed overflow requires a separateorder.

The declared work-policy fieldset may evolve through separately reviewed native budget work.
Tests construct an explicit actual Policy and pass that same policy to actual native build and
metadata, avoiding hidden-default mismatches. Unknown historical schemas/policies refuse; this
pre-MVP value layer does not promise an unimplemented migration. New field values participate
in policy_id, thereby changing chunk IDs as required, while exact source/count semantics remain.
