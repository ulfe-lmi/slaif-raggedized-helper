# Watchdog process observation

A process can disappear between discovery and a `/proc` read. Linux may report
ENOENT or ESRCH at that boundary. The test treats only those read errors as
disappearance; permission and I/O errors propagate, and successful contents
still undergo the original parsing and worker identity checks. Deterministic
injected reads cover both disappearance errors, a live result, and EACCES,
EPERM and EIO. The original paused-parent test retains its worker ownership,
watchdog deadline and cleanup assertions.

The actual watchdog proof uses one synthetic CPU worker and the existing
sandbox runtime. It exercises observed ownership and watchdog cleanup, not a
reproduction of every possible operating-system race or a production watchdog
change. The injected cases establish the error classification independently.
