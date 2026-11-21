#!/usr/bin/env python3
"""Bounded own-cgroup numeric resource observation (order 009-r).

Companion of oap/bin/ci_unit_diagnostics.py: the supervisor takes one
snapshot immediately before launching its child and one after the
bounded owned teardown, then folds ONE fixed-length numeric fragment
into the supervisor's existing bounded final summary. This module:

* reads ONLY /proc/self/cgroup and the two fixed local event files
  (memory.events.local, pids.events.local) below the trusted fixed
  cgroup2 mount /sys/fs/cgroup for the process's OWN unified cgroup;
* requires exactly one unified (``0::``) row; the cgroup path's
  components are validated as absolute canonical names (bounded
  count/length, no dots, no empty segments, conservative ASCII set)
  and the directory chain is lstat-verified component by component -
  no path scan, no caller-selected input, no symlink traversal, and
  an exact mount mapping that is not available means unavailable;
* never reports paths: only the cgroup directory's (st_dev, st_ino)
  identity plus bounded nonnegative counter values;
* bounds every read (file byte cap, line cap, value cap 2**63): the
  read is EOF-driven under a strict cap-plus-one, because procfs and
  cgroupfs virtual files report a stat size that does not describe
  the generated text (/proc/self/cgroup reports zero); reports
  unavailable for missing, malformed, oversize, unstable (identity
  changed between the two snapshots) or counter-reset observations -
  a nonnegative delta is reported only when both readings exist, the
  identity is the same, and the counter did not decrease;
* parses the event files with a bounded ASCII key/value grammar:
  kernel event files carry untracked valid keys alongside the
  selected fields (low/high, oom_group_kill, sock_throttled per the
  cgroup v2 interface files) - untracked keys are parsed and ignored,
  while a malformed value (including non-ASCII numeric text) refuses
  the whole file without raising;
* records the inherited prelaunch RLIMIT_CPU soft/hard as bounded
  decimal / unlimited / unavailable.

The observation never determines child status, acceptance, or which
member failed; it is folded into the final summary display only. No
raw file content, no unrelated metadata, no network, no rlimit
change, no privilege, no new dependency.
"""
from __future__ import annotations

import os
import stat

PROC_CGROUP = "/proc/self/cgroup"
CGROUP_MOUNT = "/sys/fs/cgroup"
MEMORY_EVENTS = "memory.events.local"
PIDS_EVENTS = "pids.events.local"
UNIFIED_PREFIX = "0::"

COUNTER_MAX = 2 ** 63
COUNTER_DIGITS_MAX = 19
FILE_MAX_BYTES = 4096
EVENT_LINE_MAX = 64
EVENT_TEXT_MAX = 512
PATH_DEPTH_MAX = 16
PATH_COMPONENT_LEN_MAX = 255
RLIMIT_DECIMAL_MAX = 10 ** 12

# The selected tracked fields per fixed event file (the kernel
# documents additional valid keys in the same files; those are
# parsed and ignored, never tracked).
TRACKED_MEMORY_FIELDS = ("max", "oom", "oom_kill")
TRACKED_PIDS_FIELDS = ("max",)

# Conservative canonical cgroup name characters (systemd slice/scope
# style). Anything else fails closed to unavailable.
_COMPONENT_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "._-:@=+")
_KEY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789_")
_ASCII_DIGITS = frozenset("0123456789")


def parse_unified_cgroup_path(text):
    """Exactly one unified row -> canonical component list (or None).

    ``"0::/"`` (the root cgroup) yields the empty component list.
    v1 rows are ignored; a file with zero or multiple unified rows,
    malformed fields or non-canonical components yields None."""
    try:
        lines = text.split("\n")
    except AttributeError:
        return None
    unified = [ln for ln in lines if ln.startswith(UNIFIED_PREFIX)]
    if len(unified) != 1:
        return None
    fields = unified[0].split(":", 2)
    if len(fields) != 3 or fields[0] != "0" or fields[1] != "":
        return None
    path = fields[2]
    if not path.startswith("/"):
        return None
    if path == "/":
        return []
    components = path[1:].split("/")
    if len(components) > PATH_DEPTH_MAX:
        return None
    for comp in components:
        if (not comp or comp in (".", "..")
                or len(comp) > PATH_COMPONENT_LEN_MAX):
            return None
        for ch in comp:
            if ch not in _COMPONENT_CHARS:
                return None
    return components


def parse_events(raw):
    """Bounded key/value parser for ONE fixed cgroup event file.

    Returns {key: int} for every syntactically valid line or None
    when the file is malformed, oversize or non-ASCII. The kernel
    documents valid untracked keys alongside the selected fields
    (low/high, oom_group_kill, sock_throttled): untracked keys are
    parsed and returned but never used by the caller. A malformed
    line, a duplicate key or a noncanonical/oversize value refuses
    the whole file; the parser never raises."""
    if not isinstance(raw, (bytes, bytearray)):
        return None
    raw = bytes(raw)
    if len(raw) > EVENT_TEXT_MAX:
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not text.isascii():
        return None
    lines = text.split("\n")
    if len(lines) > EVENT_LINE_MAX + 1:
        return None
    values = {}
    for line in lines:
        if not line:
            continue
        parts = line.split(" ")
        if len(parts) != 2:
            return None
        key, digits = parts
        if (not key or key in values
                or any(c not in _KEY_CHARS for c in key)):
            return None
        if (not digits or len(digits) > COUNTER_DIGITS_MAX
                or any(c not in _ASCII_DIGITS for c in digits)):
            return None
        value = int(digits)
        if value >= COUNTER_MAX:
            return None
        values[key] = value
    return values


def _bounded_read(path):
    """Bounded read of ONE fixed regular file; None on any refusal.

    lstat-verified regular file (a symlink is refused, not followed),
    O_NOFOLLOW open with a same-identity fstat recheck, then an
    EOF-DRIVEN read under a strict cap-plus-one: procfs/cgroupfs
    virtual files report a stat size that does not describe the
    generated text (/proc/self/cgroup reports zero while returning
    data), so the read runs to EOF and refuses once more than
    FILE_MAX_BYTES bytes are available. No path is ever returned."""
    try:
        st = os.lstat(path)
    except (OSError, TypeError):
        return None
    if not stat.S_ISREG(st.st_mode) or st.st_size > FILE_MAX_BYTES:
        return None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return None
    try:
        fst = os.fstat(fd)
        if ((fst.st_dev, fst.st_ino) != (st.st_dev, st.st_ino)
                or not stat.S_ISREG(fst.st_mode)):
            return None
        chunks = []
        total = 0
        while total <= FILE_MAX_BYTES:
            chunk = os.read(fd, FILE_MAX_BYTES + 1 - total)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        if total > FILE_MAX_BYTES:
            return None
        return b"".join(chunks)
    except OSError:
        return None
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def _dir_identity(root, components):
    """lstat-verified component chain below the trusted fixed mount.

    Every step must be a real directory (lstat: a symlink component
    is refused, never traversed). Returns (st_dev, st_ino) of the
    final directory or None; no path is ever returned."""
    current = root
    try:
        st = os.lstat(current)
    except (OSError, TypeError):
        return None
    if not stat.S_ISDIR(st.st_mode):
        return None
    for comp in components:
        current = os.path.join(current, comp)
        try:
            st = os.lstat(current)
        except OSError:
            return None
        if not stat.S_ISDIR(st.st_mode):
            return None
    return (st.st_dev, st.st_ino)


def snapshot(proc_path=PROC_CGROUP, mount_root=CGROUP_MOUNT):
    """ONE bounded snapshot of the process's own unified cgroup.

    Returns a dict with "identity" (st_dev, st_ino of the own cgroup
    directory, or None) and the four tracked counters (nonnegative
    int or None = unavailable for that observation):
    memory_max/memory_oom/memory_oom_kill from memory.events.local
    and pids_max from pids.events.local. proc_path/mount_root are
    private test seams (owned synthetic fixtures only); production
    calls use the fixed defaults."""
    out = {
        "identity": None,
        "memory_max": None,
        "memory_oom": None,
        "memory_oom_kill": None,
        "pids_max": None,
    }
    proc_raw = _bounded_read(proc_path)
    if proc_raw is None:
        return out
    try:
        components = parse_unified_cgroup_path(
            proc_raw.decode("utf-8"))
    except UnicodeDecodeError:
        return out
    if components is None:
        return out
    identity = _dir_identity(mount_root, components)
    if identity is None:
        return out
    target = os.path.join(mount_root, *components)
    memory = parse_events(
        _bounded_read(os.path.join(target, MEMORY_EVENTS)))
    if memory is not None:
        out["memory_max"] = memory.get("max")
        out["memory_oom"] = memory.get("oom")
        out["memory_oom_kill"] = memory.get("oom_kill")
    pids = parse_events(
        _bounded_read(os.path.join(target, PIDS_EVENTS)))
    if pids is not None:
        out["pids_max"] = pids.get("max")
    out["identity"] = identity
    return out


def _rlimit_desc(value):
    if value == -1:
        return "unlimited"
    if (isinstance(value, int) and not isinstance(value, bool)
            and 0 <= value < RLIMIT_DECIMAL_MAX):
        return str(value)
    return "unavailable"


def rlimit_cpu():
    """The inherited RLIMIT_CPU soft/hard as bounded descriptions:
    decimal (bounded), "unlimited" or "unavailable" for each."""
    try:
        import resource
    except ImportError:
        return ("unavailable", "unavailable")
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    except Exception:
        return ("unavailable", "unavailable")
    return (_rlimit_desc(soft), _rlimit_desc(hard))


def render(rlimit, before, after):
    """The ONE fixed-length summary fragment for the supervisor's
    final summary (no paths, no raw file content).

    cgroup=unavailable when either snapshot is missing, the identity
    is missing, or the device/inode identity differs between the two
    snapshots (unstable). Per counter: unavailable when either
    reading is unavailable or the counter decreased (counter reset);
    otherwise the exact nonnegative delta."""
    if rlimit is None:
        rlim = "rlimit_cpu=unavailable:unavailable"
    else:
        rlim = "rlimit_cpu=%s:%s" % (rlimit[0], rlimit[1])
    if (before is None or after is None
            or before.get("identity") is None
            or after.get("identity") is None
            or before["identity"] != after["identity"]):
        return rlim + " cgroup=unavailable"
    parts = []
    for label, key in (("mem_max", "memory_max"),
                       ("oom", "memory_oom"),
                       ("oom_kill", "memory_oom_kill"),
                       ("pids_max", "pids_max")):
        b = before.get(key)
        a = after.get(key)
        if b is None or a is None or a < b:
            parts.append(label + "=unavailable")
        else:
            parts.append(label + "+%d" % (a - b))
    return rlim + " cgroup=" + ":".join(parts)
