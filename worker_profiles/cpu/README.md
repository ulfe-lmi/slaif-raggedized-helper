# Optional CPU worker dependency profile

This standalone CPython 3.12 Linux x86_64 profile is separate from the application environment (the application pins NumPy 2.5.4; this worker pins 2.2.6). The official PyTorch CPU index is explicit and applies only to torch; all other packages resolve from PyPI. The lock records distribution URLs and SHA256 hashes. The selected CPU wheel matches the observed official index hash. GHSA-63cw-57p8-fm3p establishes a patched torch floor of 2.10.0; that is not a general security clearance.

For reproduction, create a new private mode 0700 capsule and use an existing CPython 3.12 interpreter, with no ambient index configuration or credentials. From the repository root, substitute your capsule path in the following commands. Limit total network artifacts to 600 MiB and capsule disk usage to 3 GiB; monitor those totals externally. The original network byte count was not captured.

```sh
ulimit -v 2097152 -t 120 -f 629145600
CAPSULE=/tmp/your-private-capsule
PYTHON=/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12
UV=/home/janezp/.local/bin/uv
timeout 600 env -i PATH=/usr/local/bin:/usr/bin:/bin UV_CACHE_DIR="$CAPSULE/cache" UV_NO_CONFIG=1 "$UV" lock --check --project worker_profiles/cpu --python "$PYTHON" --no-python-downloads
timeout 600 env -i PATH=/usr/local/bin:/usr/bin:/bin UV_CACHE_DIR="$CAPSULE/cache" UV_PROJECT_ENVIRONMENT="$CAPSULE/venv" UV_NO_CONFIG=1 UV_CONCURRENT_DOWNLOADS=1 UV_CONCURRENT_INSTALLS=1 UV_CONCURRENT_BUILDS=1 TOKIO_WORKER_THREADS=1 RAYON_NUM_THREADS=1 "$UV" sync --project worker_profiles/cpu --locked --no-build --python "$PYTHON" --no-python-downloads
env -i PATH=/usr/bin:/bin UV_NO_CONFIG=1 "$UV" pip check --python "$CAPSULE/venv/bin/python"
```

The original successful installation used the serialized download and install settings and thread limits shown; the additional build concurrency setting is defensive because builds are disabled. Never point this at the application environment.

For metadata inspection, invoke the standalone interpreter with `-I -S`; use `importlib.metadata.distributions(path=[private_site_packages])` with the explicit private site-packages path. Do not add the directory to `sys.path` or import the installed packages. The evidence records installed metadata and local reproduction location, not provenance or license permission. License fields may be truncated to 300 characters; consult installed metadata for full declarations. License audit 018, transitive and native security, actual framework loading, physical CPU and V100 qualification, parity and quality remain open. No model assets, inference, deployment, ICA or MVP qualification were performed. Objective 007 remains partial.
