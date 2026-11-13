# Raw GPU worker identity

`predict(prepared)` revalidates a current-process `PreparedLaunch` and returns immutable canonical record bytes and a domain-separated fingerprint. It does not launch a process or take ownership of the launch, artifacts, or reservation. `validate_record` checks persisted canonical structure and returns its fingerprint; it does not establish live ownership or observed readiness. A record is not an authorization or capability.

The schema identifies the raw FP16 CLS worker, its admitted semantic space and inventory, policy, device configuration, explicit driver bytes, pinned Python, profile metadata, and relevant code. Instance values such as nonce, PID, inode, descriptor, capsule path and plan ID are excluded. A private null-device fixture records null for the observed NVIDIA rdev; it is not a hardware observation. The profile binds selected lock and package name/version metadata, not all package bytes, launcher or system libraries. Hardware qualification remains unknown.

`observe(worker)` depends on the private parent registry and layout, including its retained lock and immutable ready snapshot. It returns a distinct immutable observed value with canonical ready-binding bytes after validating the actual registered live owner and independently derived ready binding. Observation describes only that boundary, not future liveness or a completed forward. Neither prediction nor a serialized record substitutes for observation at the relevant boundary.

Native-text receipts, normalization, durable jobs and controller, current rights, parity, hardware, security and license evaluation, and full merged-SHA independent audit remain separate gates. This is not a complete GPU execution contract.
