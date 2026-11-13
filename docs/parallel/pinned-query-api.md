# Private pinned query composition

`raw_snapshot_query.search_pinned_data` borrows an already active `PinOwner`, its
matching original and derived stores, and an already entered `ResidentQueryEncoder`.
The caller must exclusively own these objects throughout the call and retain the
pin for subsequent evidence use. The adapter never enters, closes, restarts, or
reacquires them. Concurrent mutation or closure is unsupported. Cleanup ownership
remains with the caller even on failure.

A trusted application supplies `authorization_provider(boundary, admission)`.
It must freshly attest permission for both the search operation and dispatch of
the exact question to the configured CPU encoder at each of `before_encode`,
`before_retrieval`, and `before_return`, including when data grants are empty.
Its `QueryAuthority` must identify the current epoch, grants, restrictions, and
complete set of affected partitions for the captured snapshot. A readable
unavailable partition refuses the whole query before model exposure; unknown
partition IDs cause a generic refusal. Policy or availability changes refuse the
whole query. The existing restriction rules intersect grants, never widen them.

The adapter invokes the actual borrowed encoder once and hybrid search once,
checks the actual execution fingerprint against the captured snapshot core, and
keeps the captured pin even if current selection advances. Its deadline is one
cooperative budget: nested calls cannot be preempted and a late return is refused.
Errors are content-free; a readable affected scope raises `ScopeUnavailableError`,
other ordinary errors raise `PinnedQueryError`, and non-Exception interruptions
propagate. The result contains identity hashes and the hybrid result, not the raw
question or encoder record. Its policy label means only that a supplied provider
was consulted; it does not attest authentication or model qualification.

This private hook does not implement current principal mapping, real current
policy, monotonic epochs, authenticated dispatch, evidence and final delivery
rechecks, or per-request ownership enforcement. Those are independent service
pre-exposure gates. Real CPU/corpus precision qualification, held-out evaluation,
licenses, and full product readiness remain unproven. Provider callbacks and
mocked tests do not establish those claims.

The finite local synthetic journey exercised a denied question before encoder
use, retained an old pin after selection advanced, and then ran one real
resident CPU toy encoder forward through dense, BM25 and fusion. The corpus
vectors were supplied synthetic values rebound to the toy space; they are not
model-produced corpus evidence. All three source tokenizer roles shared one
cached synthetic tokenizer. This does not qualify a real model or precision
pair. The local driver relies on externally provisioned toy inputs and injected
proof counters; it is not a normal CI recipe. A separately reviewed CI case and
its full required checks remain necessary before canonical integration.
