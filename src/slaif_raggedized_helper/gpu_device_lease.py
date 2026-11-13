"""Cooperative local GPU-device leases; no hardware access or authorization."""

import os
import re
import weakref

from . import embedding_job_ownership as ownership
from .schema import fingerprint


class DeviceLeaseRefused(ValueError):
    """A device lease could not be established or verified."""


# Retain uncertain owners: a failed close may already have released the lock, and
# its descriptor numbers must not be closed again after they may have been reused.
_live = {}
_pending = {}
_closed = weakref.WeakKeyDictionary()
_HOST = re.compile(r'[0-9a-f]{64}\Z')
_UUID = re.compile(r'GPU-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z')


def _refuse():
    raise DeviceLeaseRefused('device lease refused') from None


def _validate(root, host_id, device_uuid):
    # Bound raw strings before encoding, normalization, hashing, or I/O.
    if (type(root) is not str or not 2 <= len(root) <= 4096
            or type(host_id) is not str or len(host_id) != 64
            or type(device_uuid) is not str or len(device_uuid) != 40):
        _refuse()
    if (not root.startswith('/') or '\x00' in root or root.endswith('/')
            or any(part in ('', '.', '..') for part in root[1:].split('/'))
            or _HOST.fullmatch(host_id) is None or _UUID.fullmatch(device_uuid) is None):
        _refuse()
    try:
        if len(root.encode('utf-8')) > 4096:
            _refuse()
    except UnicodeError:
        _refuse()


def _key(host_id, device_uuid):
    return fingerprint({'kind': 'gpu-device-lease-v1', 'host_id': host_id,
                        'device_uuid': device_uuid})


class DeviceLease:
    __slots__ = ('_root', '_host_id', '_device_uuid', '_key', '_owner', '_pid', '_state',
                 '__weakref__')

    def __init__(self, *args):
        _refuse()

    @property
    def key(self):
        return self._key

    @property
    def owner_id(self):
        return self._owner.owner_id

    @property
    def owner_pid(self):
        return self._owner.owner_pid

    @property
    def cleanup_owner(self):
        record = _live.get(id(self))
        return record[5] if record is not None and record[8][0] == 'pending' else None

    def assert_owned(self):
        try:
            record = _live.get(id(self))
            if (record is None or record[0] is not self or record[8][0] != 'live'
                    or type(self._state) is not str or self._state != 'live'):
                _refuse()
            _, root, host, device, key, owner, pid, owner_id, _ = record
            _validate(self._root, self._host_id, self._device_uuid)
            if (self._root != root or self._host_id != host or self._device_uuid != device
                    or type(self._key) is not str or self._key != key
                    or self._owner is not owner or type(self._pid) is not int or self._pid != pid
                    or os.getpid() != pid or owner.owner_pid != pid
                    or type(owner.owner_id) is not str or owner.owner_id != owner_id
                    or type(owner.job_id) is not str or owner.job_id != key
                    or _key(host, device) != key):
                _refuse()
            owner.assert_owned()
        except Exception:
            _refuse()

    def close(self):
        record = _live.get(id(self))
        if record is None or record[0] is not self:
            if (self in _closed and _closed[self] == os.getpid()
                    and type(self._state) is str and self._state == 'closed'):
                return
            _refuse()
        if record[8][0] == 'pending':
            error = DeviceLeaseRefused('device lease cleanup pending or unknown')
            error.cleanup_owner = record[5]
            raise error
        if (record[8][0] != 'live' or type(self._state) is not str or self._state != 'live'
                or os.getpid() != record[6]):
            _refuse()
        # Use the captured owner even if public-facing fields were changed.
        record[8][0] = self._state = 'pending'
        try:
            record[5].close()
        except BaseException as exc:
            _pending[(record[1], record[4])] = record[5]
            if isinstance(exc, Exception):
                error = DeviceLeaseRefused('device lease cleanup pending or unknown')
                error.cleanup_owner = record[5]
                raise error from None
            exc.cleanup_owner = record[5]
            raise
        record[8][0] = self._state = 'closed'
        _closed[self] = record[6]
        del _live[id(self)]

    def __enter__(self):
        try:
            self.assert_owned()
        except BaseException as exc:
            try:
                self.close()
            except BaseException as cleanup:
                exc.cleanup_owner = self.cleanup_owner
                exc.add_note('device lease cleanup is pending or unknown')
                if isinstance(exc, Exception) and not isinstance(cleanup, Exception):
                    raise
            raise
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.close()
        except BaseException as cleanup:
            if exc is None:
                raise
            exc.cleanup_owner = self.cleanup_owner
            exc.add_note('device lease cleanup is pending or unknown')
            if not isinstance(cleanup, Exception) and isinstance(exc, Exception):
                raise
        return False


def acquire(root, host_id, device_uuid):
    """Claim the device key under the shared trusted local root."""
    _validate(root, host_id, device_uuid)
    key = _key(host_id, device_uuid)
    if (root, key) in _pending:
        error = DeviceLeaseRefused('device lease cleanup pending or unknown')
        error.cleanup_owner = _pending[(root, key)]
        raise error
    try:
        owner = ownership.claim(root, key)
    except BaseException as exc:
        cleanup_owner = getattr(exc, 'cleanup_owner', None)
        if cleanup_owner is not None:
            _pending[(root, key)] = cleanup_owner
        if isinstance(exc, Exception):
            error = DeviceLeaseRefused('device lease refused')
            if cleanup_owner is not None:
                error.cleanup_owner = cleanup_owner
            raise error from None
        raise
    try:
        lease = object.__new__(DeviceLease)
        lease._root, lease._host_id, lease._device_uuid = root, host_id, device_uuid
        lease._key, lease._owner, lease._pid, lease._state = key, owner, os.getpid(), 'live'
        _live[id(lease)] = (lease, root, host_id, device_uuid, key, owner, lease._pid,
                            owner.owner_id, ['live'])
        return lease
    except BaseException as exc:
        try:
            owner.close()
        except BaseException as cleanup:
            _pending[(root, key)] = owner
            exc.cleanup_owner = owner
            exc.add_note('device lease cleanup is pending or unknown')
            if isinstance(exc, Exception) and not isinstance(cleanup, Exception):
                cleanup.cleanup_owner = owner
                raise
        raise
