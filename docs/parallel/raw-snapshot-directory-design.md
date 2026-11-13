# Private raw snapshot directory reader — strategic D0 contract

Status: FINAL DESIGN; activation requires finalized order/live reconciliation.
H full-MVP/parallel; A11.5/12.1/12.3/12.4; I file-set1131/report84fb, membership892/peer0d82,
payload peer6aad and filesystem facts e03a; E complete byte-set correspondence exists but
there is no bounded real directory reader anchoring those bytes to a private snapshot ID.
DHA NONE. Local future008 implementation; no canonical number jump or Ready authority.

Add only raw_snapshot_directory.py and new tests/API/design/order. No predecessor edits,
new dependencies, writer, current pointer, retention/GC, query/retrieval or service operation.
The caller supplies trusted INTERNAL operator configuration, never an HTTP/model path.

## API and physical layout

load_directory(originals,derived,store_root,snapshot_id) returns the actual frozen
raw_snapshot_files.BoundSnapshotData after real bounded reads and actual validate_files.
Borrow exact existing OriginalStore/derived Store; never close/write them. snapshot_id is
exact sha256: plus64lowerhex. store_root is an exact canonical absolute UTF8 string, nonroot,
<=4096 bytes, no NUL/control/path-normalization aliases. No arbitrary resolver/provider/
parsed DTO/file handle. Ordinary content-free DirectoryError; original non-Exception stays.

Fixed path: store_root/snapshots/<bare64snapshotid>/.core.json plus the core's declared data
files. Hidden .core.json is reserved metadata; core descriptor paths cannot begin with dot,
so there is no collision or circular selfhash. Never derive snapshot ID from a directory
timestamp or trust the directory name alone. Actual core SHA must equal requested ID.

Configured root and snapshots directory: current user owner, mode0700. Snapshot directory
and all nested data directories: current user owner, mode0500. Core and data files: current
user owner, mode0400, regular and one hard link. These are supported private layout rules,
not OS immutability against that owner/admin. Tests build their OWN fixture writable, then
set these final modes; no change to existing stores or real corpus.

Resolve each absolute/relative component with actual directory FDs and O_DIRECTORY,
O_NOFOLLOW,O_CLOEXEC (and nonblocking where relevant), no symlink traversal, chdir or realpath
follow fallback. Ancestors must be actual directories, owned by root or current UID and not
group/world writable; root-owned sticky /tmp is allowed. Do not accidentally reject that
explicit safe test ancestor. Configured/data directory modes above remain stricter.

Capture actual directory/entry identities. Reconcile root/snapshots/target directory linkage
before and after loading, including a fresh no-follow resolution of configured root at end.
A pinned FD is not proof the current pathname still selects it. Keep only bounded active FDs
(target at most16); close intermediate ancestry/relative components rather than keeping one
FD for every file. Do not inspect or alter unrelated snapshot IDs in the global store.

## Bounded reads, closed physical tree and fresh data validation

1. Read .core.json as bounded regular bytes <=262144 with exact allowed metadata and stable
   dev/inode/mode/owner/link-count/size/mtime_ns/ctime_ns before/after read. O_NONBLOCK and
   fstat precede any content read; refuse nonregular objects without reading them. No FIFO
   test objects or FIFO read at all. Confirm its current directory entry still names that
   inode, not just the opened FD. Compare requested SHA and freshly parse actual core.
2. Derive the expected data-file and necessary ancestor-directory sets from actual closed
   core paths; reject file/directory prefix collisions (e.g a and a/b). Data-only codecs may
   represent such names; this filesystem layout cannot. No core-format rewrite is needed.
3. Verify the target physical tree contains EXACTLY .core.json, declared files and their
   necessary directories. Walk with pinned no-follow directory FDs; check types/modes/owner,
   bounded inventory and linkage. At most1033 relative nodes from258files*4components+core;
   stop on the first over-limit observation, not an unbounded list/sort. Reject unexpected
   files/directories, symlinks and hard-linked data files. Do not recurse into other snapshots.
4. Read each declared file using its known size/role/total bound and exact SHA. Open no-follow
   nonblocking regular FD, admit before reading, detect over/under-length/trailing bytes,
   verify before/after metadata and current entry identity. Total actual data bytes <=96MiB,
   core additional; lower file-set/payload bounds still apply. Avoid retaining redundant full
   buffer copies or unbounded directory inventories. No content-addressed filename is proof
   without reading/hash validation. An EOF read is normal, not an unexpected data read.
5. Pass canonical sorted exact (relative_path,bytes) tuples and actual core to REAL
   raw_snapshot_files.validate_files(originals,derived,...). It must fresh-check the complete
   original-backed membership/dense/lexical source relation and current analyzer; no fallback
   to parse or caller validation callback. Reconcile physical tree/directory identities and
   stable admitted file observations again before returning the fresh immutable data.

Use cooperative60s around phases/files/helpers; no hard IO/preemption/RAM guarantee or raised
lower helper bound. No source/model/authorization process starts; source fixture construction
may use existing synthetic native workers BEFORE this API is called. The returned bytes/data
are detached, not a retained physical reader handle and not evidence the filesystem cannot
change after return. A later request/publisher must use its appropriate fresh boundary.

## Owned descriptors and failure behavior

Only close actual descriptors acquired in this operation; preserve creating PID/identity and
finite cleanup bookkeeping. On success all own FDs drain before returning. On interruption,
ordinary refusal or close failure, attempt safe independent own cleanup; preserve original
non-Exception, later cleanup interruption outranks an ordinary error. Ordinary error remains
content-free. Retain an actual reachable cleanup owner for unknown/pending descriptor state.
Record an attempted close before it can raise; never retry an uncertain numeric FD, close a
reused foreign FD or claim a retained uncertainty object proves a lock/FD is still held. A
forked borrower cannot drain its creator's retained owner. No GC-as-proof or global FD scan.

Use an appropriately small operation-local owner plus retained pending/unknown state rather
than copying whole GPU supervision or modifying existing stores. A Python wrapper is not
atomic protection from every kernel interruption; report finite behavior/limits honestly.
No model, driver, namespace process, GPU lock or publication lock is owned by this reader.

## Finite proof

Actual valid fixture materializes the existing real complete-file-set synthetic source data
into OWN private root/snapshots/id layout, applies modes and loads it. Result equals actual
byte-set validator result, ID/content/row/term/vector correspondence exact; no Popen, writes,
publication or borrowed close during reader calls. Empty/tombstone or active zero-selected-row
case remains meaningful; unknown snapshot and wrong ID refuse without partial accepted data.

Actual negatives: unsafe configured root/ancestor/symlink component, wrong owner/mode where
safe to simulate only designated own metadata, unexpected tree member, hard link, directory
at file position, prefix collision, wrong/trailing/oversized core/data, swapped correct-shape
dense bytes with updated outer hashes reaching fresh semantic validation, source corruption,
actual path replacement while FD pinned. No special FIFO/socket/device test objects needed.
Use owned fixtures, restore only their bytes/modes. Verify independent stores remain usable.

One narrow ORIGINAL guard control may hard-link an actual valid snapshot data file to an OWN
alias OUTSIDE the snapshot tree: original refuses the link-count policy; a temporary in-memory
module removes ONLY the central nlink==1 predicate, actual bounded directory/data/source
validation still succeeds; original refuses again. Other stability checks stay intact. This
proves hardlink admission policy, not general security/immutable bytes/current rights. Do not
require removal of one early guard to defeat independent later guards; state the exact effect.

Meaningful cleanup fault: a controlled close of ONE actual owned reader FD closes it then
raises; retain sticky unknown, allocate a new own FD reusing that number if feasible, and
confirm retry does not close/retry the uncertain number. Keep borrowed store FDs untouched.
No fake complete owner/registry or unknown process signal. Context/interrupt priority and
actual no-follow/path replacement behavior are finite cases, not exhaustive kernel proofs.

Focused new unit/actual cases plus relevant complete-file-set/core/parser checks; reuse exact
unchanged predecessor proof where new composition already exercises it. Unique logs/hashes,
source/read-set/actual commands/results/failures/counterargument; fresh affected peer before
canonical integration and current required CI. Per invocation120wall/30CPU/1GiB/five threads1/
no bytecode/cached app and existing synthetic native fixture only. No install/download/network/
framework/Tensor/model/GPU/driver/service/credentials/real corpus/source/law/CI mutation,
mainmerge/release/deploy/FIFO replay. This is SOFTWARE DIRECTORY DATA correspondence only;
deployment filesystem qualification, current ACL/withdrawal, actual query compatibility,
retrieval smoke, publication/CAS/retention, neural/precision/security/license/ICA/MVP stay open.
