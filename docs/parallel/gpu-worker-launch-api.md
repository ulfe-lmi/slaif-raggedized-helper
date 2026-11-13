# GPU worker launch preparation

`gpu_worker_launch.prepare` admits an explicit device plan, explicit driver files and finite
resource policy, verifies the locked 57-distribution profile and artifact space, creates a private
capsule, and returns a `PreparedLaunch`. It does not start a process. The caller must hold the
actual operation reservation and protect the artifact tree until a future process owner has
confirmed child drain and closed the prepared object. The reservation is borrowed and never closed
by this API. This API does not establish rights, transition intent, GPU vacancy or capacity.

The code capsule contains the 12 wire files, exact GPU lock, and a separate copy of the fixed
child entry; the bounded explicit driver copies occupy a separate directory. Source, capsule,
profile, runtime executable, mount descriptor identities, device plan and policy participate in
admission and plan identity. `launch_arguments()` revalidates and returns a fixed argument tuple
and the descriptor tuple to pass to the eventual process owner. Device nodes and runtime executable
are descriptor pinned. The caller must not close or replace these descriptors. The selected
runtime is `/python/bin/python3.12 -I -S`; the unchanged child retains its CPython 3.12 guard.
The serialized startup frame, including its newline, must fit the child frame limit and the
selected request and cumulative input limits before a plan is returned.

The command uses prlimit, timeout, and bubblewrap with private user, PID, network, IPC and UTS
namespaces, a synthetic `/dev`, private `/proc`, a cleared environment, offline/thread-one flags,
and only the explicit device mounts. The inherited native C-library mounts are
`/usr/lib/x86_64-linux-gnu` and `/usr/lib64`; this is not a fully hermetic driver graph. Output
and stderr caps are recorded in the plan and the regular-file size rlimit, but a future parent
must enforce pipe byte limits while concurrently draining them. No subprocess, protocol supervisor,
controller, model, rights service or deployment is implemented here.

`close()` rejects every call from a forked process, including retries on a closed owner.
`close()` performs finite cleanup and retains an owner for uncertain descriptors or capsule
cleanup. An uncertain descriptor number is not retried. Closing the prepared object, a wrapper
exit, and EOF are not proof that all descendants have drained or that a physical GPU is vacant.
The future owner must retain the object until its own drain procedure completes. Current cleanup
and dependency behavior still require independent review; this leaf does not waive prior issues.

The OS test substitutes `/dev/null` for both configured GPU device descriptors and replaces only
its private copied entry with an in-memory fake backend. It uses the actual copied child protocol,
artifact admission, Python 3.12, profile metadata, namespace setup, and device lease. It proves no
actual NVIDIA device, driver, framework, model, resource sizing, parity, rights, license or hardware
behavior. A fresh affected peer review and subsequent parent/controller integration remain open.

Read projection for this leaf: the 8,085-byte Root contract, 6,706-byte wire protocol,
7,637-byte child and 7,008-byte job ownership implementation were read in full. Relevant
sections were read from the 7,098-byte device lease, 14,696-byte backend, 8,029-byte CPU
backend, 10,153-byte tokenizer scaffold, 12,280-byte artifact verifier, 4,600-byte space
admission, 19,545-byte schema and 13,869-byte protocol tests. The 44,632-byte GPU lock is
validated by the existing profile reader. This projection is not an audit of those dependencies.
