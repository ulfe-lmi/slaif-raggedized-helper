# Cooperative GPU device lease

`acquire(root, host_id, device_uuid)` returns a live context manager with `key`,
`owner_id`, `owner_pid`, `assert_owned()` and `close()`. The root is an absolute,
normalized string naming a private 0700 directory. All cooperating controllers
must use the same trusted local root and protected ancestry on a local flock
filesystem. Different roots do not coordinate. Host identity is exactly 64
lowercase hexadecimal characters; device identity is a canonical lowercase
`GPU-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` string. Both are claimed operator
configuration, not hardware discovery or authenticated input.

The key is `schema.fingerprint` of the structured object with kind
`gpu-device-lease-v1`, host_id and device_uuid. It does not include jobs or
modes. The existing ownership module supplies actual kernel exclusion and owner
identity; serialized metadata alone proves nothing. Forked children cannot use
the parent's lease. Filesystem and PID namespaces must be configured so all
cooperators share the intended local lock and process identity semantics.

A close failure is sticky and ownership becomes unknown: the inner close may
already have unlocked, and descriptors are not blindly closed again. Pre-return acquisition failures attempt each acquired descriptor once and expose a
retained cleanup owner if an attempt is uncertain. Do not automatically reclaim after uncertainty.
Future controllers must drain owned workers before release and independently
validate device, runtime and authorization before CUDA. This module does not
manage GPU or model lifetime, grant inference, maintenance or service-stop
permission, or exclude noncooperating GPU users.

Ordinary acquisition refusals use `DeviceLeaseRefused`. Errors during
uncertain cleanup expose `cleanup_owner`, and the same root and device key are
refused for further acquisition in this process while uncertainty is retained.
This memory does not coordinate other roots, other processes or restarts; it
cannot establish continued kernel or physical ownership. A future controller
must independently validate and reconcile the physical owner and runtime.
Cleanly closed wrappers do not remain strongly retained by the registry.
