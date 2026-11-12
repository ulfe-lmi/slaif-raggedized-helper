# Private owned GPU worker API

`GPUEmbeddingWorker` consumes one actual current-process `PreparedLaunch`. The caller keeps
the operation reservation and artifact tree alive until the worker has drained. The worker
retains the prepared owner and process resources, and a failed constructor can leave an owner
in the private retention registry if namespace drain cannot be proved. `close()` is explicit;
a refused close is not proof of cleanup or GPU vacancy. A forked process cannot close an
owner created in its parent.

`forward_cls(rows)` accepts bounded integer token-ID rows and returns an immutable
`RawCLSResult`, containing the observed binding and ordered raw finite FP32 CLS values. It
does not tokenize, add prefixes, normalize, authorize access, create durable jobs or establish
semantic parity. A worker is single-use with respect to its prepared startup and serializes
calls. Ordinary failures are content-free refusals.

This is a private software subset, not a service controller or a rights, native-ID,
bulk-journal, durable-transition or source-projection integration. Model, framework, driver,
physical GPU vacancy, parity, security, licensing, installed layout and operational readiness
are not established by the model-free tests. Future canonical integration requires fresh peer
review and current checks, including corrected shared dependencies.

The parent verifies bwrap's initial status against the namespace-init process and retains a
pidfd before it writes startup data. It signals that pidfd and waits for exit before reaping the
owned wrapper and closing the capsule. Status loss, descriptor ambiguity or incomplete drain
leaves the owner pending for explicit retry; an early shutdown can produce no bwrap exit record
and therefore remain pending even after process exit. No lock reacquisition alone proves drain.

The model-free composition witness replaces only the copied worker bind descriptor with a
private harness and uses the existing safe `/dev/null` device-pin fixture. It verifies two
requests, a single fake-backend construction, status-FD isolation, a lease-holding forked
descendant, lease exclusion and reacquisition, and a wrong-binding causal control. These tests
do not substitute installed framework modules or run a real model or driver.

Process acquisition pre-registers the actual `Popen` object before initialization can create
a child. If initialization is interrupted, cleanup reconciles the handles attached to that
object; incomplete or ambiguous acquisition remains pending with its owner and capsule held.
An acquisition witness consumes the real bwrap status before raising an immutable interrupt:
the corrected parent retains the actual process and capsule, while bypassing only process
pre-registration reproduces the earlier false-clean failure. The witness independently holds a
verified namespace pidfd and drains its own model-free process before releasing its reservation.
If the actual wrapper is already known reaped, the parent refuses a new numeric pidfd lookup
and any numeric group signal. An existing pidfd may still support namespace cleanup; otherwise
the owner remains pending. Tests independently verified the reaped case and exercise a narrow
guard bypass with the numeric lookup intercepted before it reaches the operating system.

## Bounded verification notes

The reaped-owner witness uses an actual owned `Popen` reaped with return code zero; a spy stops
`pidfd_open` before an OS lookup. The ordinary guard made zero lookup attempts, while bypassing
only that guard reached the spy. No PID reuse or foreign signal was demonstrated. A separate
model-free bwrap witness reaped during initialization and retained the owner with no new pidfd
lookup, preserving its original immutable interrupt.

With each invocation limited to 1 GiB address space, 30 CPU seconds and 120 wall seconds, the
parent unit suite passed 23 cases. The original 22 namespace cases passed in groups of 11, 7,
2 and 2, and the added reaped-initialization case passed separately. The 11-case group measured
18.82 user and 1.73 system CPU seconds; the seven-case group measured 9.15 user and 0.78 system
seconds. A combined namespace run terminated with signal 9 and exit 137 after 19 progress dots
at 27.92 user plus 2.51 system CPU seconds, 37.17 wall seconds and 62,584 KiB maximum RSS. Its
termination is consistent with the CPU limit, but the precise cause was not established; it is
not a pass. No limits were increased and no cases were skipped from the grouped verification.

The actual owner registry retains the creating process's lock independently of the
mutable parent attribute. The private `_owned_lock()` accessor checks the owner,
creating PID and lock identity before returning that retained lock. Close and
forward acquire and release that same reference without blocking. The existing
ready snapshot remains at its prior registry position.

The owned lock accessor returns a snapshot of the actual registered lock, not a
promise that the owner remains live. Operations acquire that lock without
blocking and revalidate ownership after acquisition; concurrent retirement is
refused.

Constructor admission is bound to the process that created the worker instance. Each
instance admits initialization once, including when that attempt fails; a live,
failed, or closed instance cannot be initialized again or revived. A forked process
cannot initialize a borrowed instance. Refusal occurs before changing existing
ownership or consuming the supplied prepared launch.

These model-free lifecycle checks do not qualify a model, GPU, or complete pipeline.
Independent completion audit and current canonical integration qualification remain
open.
