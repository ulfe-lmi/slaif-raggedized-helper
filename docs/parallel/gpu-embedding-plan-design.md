# Pre-model GPU execution and fresh source batch plan — strategic D0 contract

Status: FINAL DESIGN, INERT pending finalized order/live state and bridge4554 affected review.
H activated MVP/parallel; A8.4/11.1/11.2/19 source-bound resumable exclusive GPU corpus batches;
I actual source plan, CPU reference plan/journal, GPU PreparedLaunch/worker identity and
isolated_gpu_embedding4554; E no source-derived journal job currently binds the complete
predicted GPU/native execution before model startup. DHA NONE. Whole007 remains partial.

This bounded leaf provides gpu_embedding_plan.py, new unit/actual composition tests and API/
exact design/order only. No modification to CPU paths, bridge, launch, source plan, journal,
stores, policy/locks, profiles or CI. It counts source text with the existing independent
native tokenizer but starts NO GPU parent, GPU model, CPU model or framework, publishes no
vectors/journal events and does not own/close the borrowed launch/reservation/original store.
Native source-count workers are existing bounded owned helpers; failures preserve their
original non-Exception/cleanup ownership behavior. No arbitrary callback replaces planning.

## Public API

build(original_store, bundle_metadata_bytes, bundle_members, chunk_ids, manifest_bytes,
artifact_root, embedding_definition, tokenizer_definition, expected_inventory_id, runtime,
prepared_launch, *, purpose='prepare', representation_policy=None, batch_policy=None)
returns a frozen Prepared containing plan_bytes, spec, texts, predicted_record,
native_runtime_record, execution_fingerprint, intended_execution_fingerprint and space_id.
Exact immutable bytes/strings/tuple texts only, existing immutable journal spec; do not return
mutable dict aliases or store/launch handles. Ordinary errors are content-free PlanError;
original non-Exception propagates unchanged. Never trust a caller-created Prepared as fresh
source admission, current authorization, actual observed execution or permission to launch.

Inputs/policies follow actual embedding_batch_plan.build and its bounded preflight (unique
ordered1..128 chunk IDs, strict original store, exact metadata/five members, model manifest,
root, definition/tokenizer/runtime, purpose prepare/evaluate, raw separator/limits). Perform
the existing scalar preflight before filesystem work/native counting, then require actual
PreparedLaunch and revalidate through the existing GPU prediction mechanism. Its runtime
roots/artifacts/reservation are trusted operator inputs, not caller HTTP parameters.
Also enforce selected GPU wire policy batch/items/shape/UTF8 input limits available from its
startup frame before source text could reach a future parent: actual policy.max_rows limits
selected chunk count, source-counted token counts remain2..1024, and the existing bridge's
fixed text/codepoint/serialized-native-request ceilings remain applicable. Prediction cannot
know a future live parent's counters, remaining wall time, observed vocabulary or accumulated
pipe bytes. Its actual bridge must still apply _budget at dispatch; do not claim this plan
reserves or certifies those dynamic budgets. Do not grant inference here.

## Predict, independently derive source, then bind

1. Call actual isolated_gpu_embedding.predict(prepared_launch, runtime); freshly validate its
   execution and detached native runtime record with validate_record. Strictly compare all
   predicted fields/fingerprints to the bytes, rather than trusting the frozen DTO type.
   Execution fingerprint here is BARE64hex SHA256(execution_record). This differs from the
   CPU reference contract's prefixed schema fingerprint. Do not blindly strip seven bytes
   or decorate a legacy intended fingerprint to pretend the contracts are interchangeable.
   Intended GPU FP16 execution remains its distinct exact schema.EmbeddingExecution identity.
2. Parse actual prepared_launch.startup with the existing wire codec; compare its manifest
   UTF8 bytes EXACTLY to manifest_bytes, definition to the supplied strict definition,
   inventory to expected_inventory_id, space to predicted space, and tokenizer hash/backend/
   role/revision/preprocessing to the supplied tokenizer definition. An identical tokenizer
   artifact may be reached through the pinned /proc descriptor; filesystem path equality is
   not its semantic identity. Existing preparation revalidation independently verifies its
   actual pinned artifact files and reservation. No DTO-only pretend preparation path.
3. Build the complete source plan through actual embedding_batch_plan.build with the admitted
   source/policies. That API's historic execution field is intended CPU FP32: require the
   exact expected legacy value, then explicitly REPLACE ONLY that dependency with the
   complete predicted GPU execution fingerprint. Do not call the CPU execution-contract
   planner or CPU model, modify source-plan implementation, or treat intended CPU as GPU proof.
4. Compare independently derived source dependencies to GPU prediction/startup: exact space,
   inventory, definition fingerprint with deliberate existing prefix conversion, tokenizer
   artifact, normalization policy and source policy. Compare runtime/native declaration
   fields to the supplied definition and tokenizer; validate detached record hash/identity.
   Preserve every original row, row order, source scope, token count, rendered/input/
   representation hash, purpose, codec policy and all other dependency bytes/values.
5. Recheck actual prediction/prepared startup after source planning and require exact same
   stable execution record, native record and all IDs. This catches changed selected runtime
   files/source/artifact/preparation while counting; no stale cached declaration is accepted.
   The full record describes software with hardware_qualification unknown. No stable identity
   may acquire ephemeral PID/FD/nonce/plan_id/root from this wrapper.
6. Emit existing embedding-job-plan-v1 canonical sorted compact ensure_ascii=False UTF8,
   no NaN/LF, <=131072 bytes, with ONLY the execution dependency changed as above. Freshly call
   actual embedding_job_journal.make_spec on these bytes; derive the job ID from that actual
   specification, not a manually synthesized CPU/GPU ID. Return actual source texts in the
   same exact order, predicted execution/detached native bytes and distinct intended identity.

Do not start a GPU parent merely to predict its stable record or use a fake full-contract
provider. Existing source counting verifies original source/representation integrity and
historic processing classification; caller must establish current permission before using
this operator planning API. This component does not implement a principal/current-policy
store, rights/license clearance or complete GPU producer. A later producer must freshly
rebuild the plan, obtain current rights at each boundary, own journal/device/model resources,
compare actual observed execution before content dispatch, persist verified output before
COMPLETE and revalidate COMPLETE reuse without model startup. Prediction alone grants none.

## Finite proof and limits

Use actual private original/bundle fixtures, actual pinned PreparedLaunch with existing null
device/fake GPU profile metadata, and actual independent synthetic native0.21 counting.
Positive plan: no GPU parent/model/framework/Popen beyond explicitly identified native count
worker, no store/journal publication; actual job spec matches canonical bytes and rows/texts
match independent generic source plan. Legacy source API still reports intended CPU unchanged;
new plan uses bare complete GPU fingerprint and distinct intended GPU identity. Deterministic
same-input planning, different source row/execution/policy changes appropriate job identity,
source order retained, detached native identity strict, returned immutable objects.

Negatives: malformed input/purpose/policy/ref before IO; real original corruption, wrong
manifest/inventory/definition/tokenizer/space between prepared launch and source inputs;
changed actual prepared artifact or selected native file only in OWN copied private fixture;
changed prediction across actual native counting; unsupported batch shape/budget; no partial
result. Borrowed reservation/prepared/original stores remain usable and caller closes them.
No modification of shared runtime, packages, fixture roots or another process's resources.

One original narrow prediction-to-source comparison control using actual admitted fixtures
and only ONE relevant equality removed in owned temporary in-memory source demonstrates a
specific cross-binding guard. It must not substitute the whole source/predictor/registry or
forge a launch as proof. Report source/control hashes, commands/results, any setup failures,
transitive read set and strongest counterargument. This proves consistency at a software
planning boundary, not observed model execution, physical exclusivity, FP16/parity or current
authorization. Fresh affected peer and exact canonical integration/CI remain separate gates.

Run new focused unit/actual compositions, relevant source-plan/journal/prediction/bridge
pure tests and unchanged source-plan actual tests as proportionate groups. No gratuitous
full predecessor/OS suite, overlapping-count inflation, cap relaxation or large aggregate
retry. Per invocation timeout120/AS1GiB/CPU30/five thread budgets1/no bytecode; existing cached
app/native/GPUfake setup only. No install/download/network/framework/Tensor/model/GPU/driver/
service/credential/real-corpus operations, mainmerge/release/deployment or canonical008 jump.
