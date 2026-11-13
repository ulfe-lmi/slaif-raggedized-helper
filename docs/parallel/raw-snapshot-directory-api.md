# Private snapshot directory DATA reader

`load_directory(originals, derived, store_root, snapshot_id)` reads the fixed private
`snapshots/<digest>/.core.json` layout and returns detached `BoundSnapshotData` after
fresh complete source validation. Inputs are internal operator configuration. Ordinary
refusals raise content-free `DirectoryError`; borrowed stores are neither closed nor written.

This establishes software directory DATA correspondence only. Pathnames, IDs and inode
identities do not establish permission or filesystem immutability. Deployment filesystem,
current rights, query compatibility, retrieval, publication, retention, neural precision,
security, licensing, independent audit and MVP qualification remain open. The cooperative
bounds do not preempt blocked operating-system calls. Close interruptions can leave an
uncertain descriptor state; such descriptor numbers are not retried.
