# Resource observer correction candidate

The observer admits baseline CPU, optional device query, each CPU/RSS sample,
and final CPU/lifetime-RSS observation as separate collection calls. It checks
one lifetime call allowance and the earlier of observer duration and trial
absolute deadline before each operation. Device startup timeout is clipped to
the remaining time; cleanup may follow expiry but no new measurement is admitted.
A final observation refused by time or budget leaves CPU delta and lifetime RSS
unavailable rather than inventing zero. Stop reasons preserve exhaustion.

`bytes_read` counts actual own-process status bytes; `device_query_bytes_read`
counts actual device pipe bytes, and their sum is the collector total. Before a
sample the full status-read cap is reserved; before a device query both pipe caps
and one lookahead byte per pipe are reserved. Reservations are not reported as
actual reads. This conservative admission may refuse a query or sample even when
its eventual actual output would have fit. Limits never reset across phases.

Standalone diagnostics stop and join the owned observer in a `finally` on
normal, error and interruption exits; only the exact owned collector child is
managed. Measurements describe the caller, not a remote model or GPU worker.
These synthetic checks do not establish hardware qualification, parity, all 14
gates, 019, ICA, MVP or license acceptance.

The series duration is the observation window: the interval from start to the
actual CPU endpoint when collected, otherwise to report assembly, intersected
with the observer-duration and optional trial-deadline work window. It does not
represent cleanup elapsed time. Collector `wall_seconds` is actual elapsed time
through report assembly, including cleanup and finalization, and can exceed the
work-window limit. CPU `wall_seconds` is the actual elapsed time to the CPU
endpoint when that observation was admitted; if the probe finishes after the
cutoff it can exceed the series window; the subsequent lifetime-RSS probe is
then omitted. Without a CPU endpoint, CPU values and
utilization remain unavailable and its wall is the observation window. Sample
offsets are preserved. No deadline or collection allowance is extended.
