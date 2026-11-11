# Private native ingestion operator (candidate)

The installed `raggedized chunk` command accepts private original and derived store paths,
revision, adapter (`structured_text` or `pdf_extraction`), explicit profile, and optional query.
For example, with an already admitted revision and a private derived directory:

```sh
raggedized chunk --original-store /private/original --derived-store /private/derived \
  --revision sha256:REVISION --adapter structured_text --profile /private/profile.json
raggedized chunk inspect --original-store /private/original --derived-store /private/derived \
  --bundle BUNDLE_ID
```

Replace the placeholders with the actual revision and bundle IDs. Profile syntax and limits are
in [ingestion-profile-api.md](parallel/ingestion-profile-api.md). The runtime must be a standalone
CPython installation, and its separately supplied native package directory must contain the pinned
backend; PDF extraction also requires its explicitly configured isolated runtime and PDF backend.
Declarations are not evidence that artifacts or dependencies exist or that their hashes match.

The operator reports bounded JSON without source text or query. `inspect` verifies a published
bundle against the retained original and does not load a profile or run tokenizers or PDF parsing.
An empty native result returns status `no_native_chunks`, a `source_status` explaining whether
text was complete or visual work is needed, no bundle ID, and exit 1. PDF native output may be
partial; `partial_visual_needed` is not a completeness claim. Invalid input or ingestion failure
returns a fixed error. A reported `published_bundle_id` means publication occurred before a later
verification, deadline, or cleanup failure; the caller can inspect that ID. If publication fails
without a known ID, its commit state is unknown. No rollback is implied. Canonical retries can
converge to the same ID when the same verified inputs remain available.

The overall 180-second budget is cooperative and cannot interrupt a blocked filesystem or stdout
operation. Interruptions propagate and owned resources are cleaned up where possible. Use private,
trusted stores and profiles; this tool does not establish producer authenticity, authorization,
model equivalence, or license clearance. The candidate still requires the remaining operator proof
matrix before acceptance.
