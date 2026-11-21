"""Private immutable policy payload installation; storage is not selection.

Operator-side storage prerequisite for future policy selection (ARCH
13.3-13.4, provenance H/E): install genuinely admitted wire bytes at
their immutable digest name in an operator-owned root, preserving the
current selector.  One trusted entry takes the exact wire bytes, the
trusted private directory and one bounded monotonic admission
deadline; it rejects invalid inputs before any protected namespace
work, admits the entire candidate through the production
``admit_policy_bytes`` with the established wire envelope, and derives
the sole final name from the SHA-256 of the exact bytes in bounded
chunks (`<64 lowercase hex>.bin`).  The input supplies no explicit
name, digest, generation, parsed DTO, callback or selector.

The storage is the shared generic admitted-content transaction of
the private report publisher, performed exactly once for both
trusted entries: the exact fixed process-wide slot pool, the
directory-inode writer lock, the no-follow namespace traversal, the
existing unnamed O_TMPFILE stage, the immutable mode, the one
no-overwrite link, the byte and inode verification, both fsync
boundaries, the conservative state and the existing cleanup retry
interface.  Called in the same process, the same pool bounds writes
from both entries.  The admitted capture reader's owner stays
independent.  The entry requires the same supported synthetic
filesystem as the existing publisher; unsupported environments
refuse.  The module performs no destructive namespace operation in
any branch and owns no reservation, lock, verification or
cleanup/retirement flow of its own: every ordinary admission,
deadline or slot failure is normalized to the fixed content-free
refusal with the truthful installation and cleanup state, while
selected non-Exception BaseException identity is preserved.  The
receipt establishes content storage only: it confers no authority to
select a policy or use protected data, and the existing selector's
bytes and linked inode remain unchanged during the operation.
Current-view and encoder candidate lanes have separate dependencies
and reviews; their provisional code is outside this scope.
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
import os
import time

from .private_policy_capture import _root_path_ok
from .private_report_publication import (
    _CHUNK,
    _CREATOR,
    _deadline,
    _tick,
    _transact,
    Cleanup,
    Outcome,
    Publication,
    PublicationError,
)
from .supplied_policy_wire import (
    _MAX_WIRE_BYTES,
    _MIN_WIRE_BYTES,
    admit_policy_bytes,
)

__all__ = [
    "PayloadInstallError",
    "PayloadInstallOutcome",
    "PayloadInstallReceipt",
    "install_policy_payload",
]


class PayloadInstallOutcome(Enum):
    INSTALLED = "INSTALLED"
    EXISTING = "EXISTING"


@dataclass(frozen=True, repr=False, slots=True)
class PayloadInstallReceipt:
    outcome: PayloadInstallOutcome
    installation: Publication
    cleanup: Cleanup
    byte_length: int
    wire_digest: str


class PayloadInstallError(Exception):
    __slots__ = ("_installation", "_cleanup")

    def __init__(self, installation, cleanup):
        super().__init__("private policy payload installation refused")
        self._installation = installation
        self._cleanup = cleanup

    @property
    def installation(self):
        return self._installation

    @property
    def cleanup(self):
        return self._cleanup


def _refuse():
    raise PayloadInstallError(Publication.NOT_PUBLISHED, Cleanup.CLEAN) from None


def _payload_error(installation, cleanup):
    return PayloadInstallError(installation, cleanup)


def install_policy_payload(wire_bytes, *, directory, deadline_ms=30000):
    """Install exact admitted policy wire bytes at their immutable digest name.

    Takes the exact wire bytes, the trusted private directory and one
    bounded monotonic admission deadline.  The entire candidate is
    admitted by the production ``admit_policy_bytes`` with the
    established wire envelope before any protected namespace work;
    the sole final name is derived from the SHA-256 of the exact
    bytes in bounded chunks.  Returns a receipt reporting the
    file-installation state and cleanup state, plus the exact byte
    length and wire digest; a fixed content-free refusal reports the
    same two states and nothing else.
    """
    # Invalid inputs are rejected before any protected namespace work.
    if type(deadline_ms) is not int or not 1 <= deadline_ms <= 30000:
        _refuse()
    end = _deadline(deadline_ms)
    if os.getpid() != _CREATOR:
        # Shared pool custody is process-bound; the truthful state is
        # the publisher's own for an unowned pool.
        raise PayloadInstallError(Publication.NOT_PUBLISHED, Cleanup.PENDING) from None
    if (
        type(wire_bytes) is not bytes
        or not _MIN_WIRE_BYTES <= len(wire_bytes) <= _MAX_WIRE_BYTES
    ):
        _refuse()
    if not _root_path_ok(directory):
        _refuse()
    try:
        _tick(end)
        # Production admission of the entire candidate, established
        # wire envelope; structural and domain admission stays in the
        # typed wire decoder.
        admit_policy_bytes(wire_bytes)
        _tick(end)
        # Derive the sole final name from the SHA-256 of the exact
        # bytes, in bounded chunks.
        digest = hashlib.sha256()
        view = memoryview(wire_bytes)
        for offset in range(0, len(wire_bytes), _CHUNK):
            _tick(end)
            digest.update(view[offset : offset + _CHUNK])
        _tick(end)
    except Exception:
        # Ordinary admission, deadline or hashing failure before any
        # protected namespace work: nothing was reserved or touched,
        # so the truthful state is not-published and clean.  Non-
        # Exception interruptions keep their identity.
        _refuse()
    wire_digest = digest.hexdigest()
    final = wire_digest + ".bin"
    parts = directory[1:].split("/")
    try:
        outcome = _transact(
            parts,
            final,
            wire_bytes,
            end,
            error=_payload_error,
            note="private policy payload installation cleanup pending",
        )
    except PublicationError as exc:
        # A shared pool refusal (creator or exhaustion) escapes the
        # transaction with the publisher's fixed error; the entry
        # normalizes it with the same truthful state.
        raise PayloadInstallError(exc.publication, exc.cleanup) from None
    # Explicit outcome mapping from the shared transaction vocabulary
    # to the entry's own: a new installation and an existing exact
    # final are distinct receipts.
    if outcome is Outcome.PUBLISHED:
        outcome = PayloadInstallOutcome.INSTALLED
    else:
        outcome = PayloadInstallOutcome.EXISTING
    # Final checkpoint before the receipt can return: no successful
    # result after a cooperative expiry.  The shared transaction only
    # returns on success after the complete verified durability, so
    # the truthful late state is durable and clean.
    if time.monotonic() >= end:
        raise PayloadInstallError(Publication.DURABLE, Cleanup.CLEAN) from None
    return PayloadInstallReceipt(
        outcome,
        Publication.DURABLE,
        Cleanup.CLEAN,
        len(wire_bytes),
        wire_digest,
    )
