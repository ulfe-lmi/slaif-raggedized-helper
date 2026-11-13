# Observed-path embedding parity capture

`qualification.embedding_capture.capture` composes the existing source loader, CPU and GPU
producers, typed batch store, entered resident query encoder, and supplied-vector analyzer.
Its caller supplies an original store, derived store, bundle ID and ordered chunk IDs; manifest,
artifact and definition inputs; native and CPU runtimes; GPU launch inputs and an already-owned
reservation; distinct private journal roots; an entered query encoder; and an explicit trusted
authorization provider. The full call signature is in `embedding_capture.py`.

The caller must establish processing rights for the source and query text before calling. The
provider receives actual producer plan bytes and their original boundaries, and content-free query
identities at query boundaries. It must return the same lowercase 64-hex authorization epoch for
all boundaries. A changed epoch or a cooperative deadline expiry refuses further work. The deadline
is not a hard interruption mechanism. One attempt is made per producer; an error can leave an
already-published artifact or a journal in its producer-defined state. Original producer interrupts
and pending cleanup owners must be handled under those producer APIs. The caller retains its stores,
reservation and query encoder and is responsible for closing them.

The request admits one to eight unique ordered chunk IDs and one to eight `(id, text, relevant_ids)`
tuples. Gold IDs must refer to selected chunks. The wrapper reloads producer outputs from the typed
store and runs the original analyzer against these matrices and actual query vectors. The returned
`Capture` holds canonical bytes, their SHA-256, and the analyzer result. The wrapper labels its origin
`OBSERVED_LOCAL_SOFTWARE_PATHS_UNQUALIFIED` and qualification `NOT_QUALIFIED`; the analyzer retains
`SUPPLIED_UNVERIFIED` and `NOT_QUALIFIED`. Reused producer outputs are historical verified data, not
new forward executions. Evidence is bounded to 1 MiB and excludes raw text and vector payloads.

These labels do not establish a neural model, actual FP16 arithmetic, physical GPU execution, model
quality, license status, security, or hardware qualification. Synthetic fixture results cannot close
those gates. A wrapper hash identifies bytes; it does not authorize processing or prove origin.
