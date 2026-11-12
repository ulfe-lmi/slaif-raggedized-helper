# Local embedding job ownership

`claim(root, job_id)` immediately acquires an exclusive POSIX lock or raises
`OwnershipRefused`. Use `with claim(root, job_id) as lease:` and call
`lease.assert_owned()` at ownership boundaries. `close()` is idempotent. The
identifier must be `sha256:` followed by 64 lowercase hex characters. The
absolute root must already exist, belong to the effective user, and be mode
0700. The root and its ancestry must be protected from untrusted writers;
there is no atomicity guarantee against hostile privileged or same-UID writers.
The lock directory and stable files remain after release. Each lease owns its
file and directory descriptors; this is per-job ownership only.

A forked child cannot assert ownership, and closing its inherited lease does
not unlock its parent. An unmanaged fork retaining a descriptor may prolong
the lock until it closes or exits. Use spawned or exec workers with close_fds.
This API does not provide GPU ownership, ACL enforcement, durable job state,
retry policy, model execution, or hardware qualification.
