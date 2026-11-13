# GPU profile resources and launch source

The GPU worker selects its pinned bundled lock from the package. A recognized source
checkout uses its fixed project lock, and the private child capsule uses its fixed
`/app/worker_profiles/gpu/uv.lock`. Missing or invalid assets refuse admission.
`prepare(source_root=...)` accepts a recognized project root or an installed package
directory and copies the same finite inventory into the existing capsule. Its source
files, profile, runtime, descriptors, device and reservation are revalidated.

The software tests use metadata fixtures and a model-free child. They do not establish
GPU, driver, model, security, licensing, rights, parity or hardware qualification.
