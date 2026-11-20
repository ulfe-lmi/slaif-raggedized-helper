#!/usr/bin/env python3
"""Bounded one-level flat tests/unit partition (order 009-s; private,
stdlib only).

Derives two nonempty disjoint deterministic ordered groups of test
file paths for separate direct pytest invocations, from exactly one
level of the flat scope directory:

* admission is exact and regular-path only: each scope entry is
  lstat'ed (never followed); a test entry is a REGULAR file whose
  name matches one of the two default file patterns (test_*.py or
  *_test.py). Ordinary non-test files (conftest.py, __init__.py,
  helpers) are not test entries; the generated __pycache__
  directory and other hidden entries are not test entries (the
  locked pytest version likewise ignores dot-prefixed entries);
* refusal fails closed instead of silently omitting tests: a
  missing or non-directory scope, a symlinked scope, any nonhidden
  directory entry (unsupported nested layout), any symlinked scope
  entry, any nonhidden non-regular entry, an entry that vanishes
  under the bounded inventory, the absent fixed group-B first file,
  or an empty derived group; the one-level inventory is itself
  bounded by a finite pre-materialization entry ceiling (an
  oversized scope is refused, never materialized unboundedly);
* determinism: test entries are sorted by name (byte-wise; the
  current names are ASCII), the same order the locked pytest
  version uses when collecting a flat directory without an
  __init__.py;
* the cut is fixed by order 009-s: group B begins at
  test_owned_gpu_worker.py; group A is exactly the entries ordered
  before it. Both groups are returned as ordered absolute paths.

No recursion, no path scan beyond one level, no caller-selected
input, no argv, no network, no non-stdlib import, no output.
"""
from __future__ import annotations

import os
import stat

GROUP_B_FIRST = "test_owned_gpu_worker.py"

# Finite pre-materialization entry ceiling for the one-level
# inventory (order 009-s): the bounded scandir walk refuses past
# this many scope entries instead of materializing an unbounded
# listing. The current exact base scope holds 119 entries.
MAX_SCOPE_ENTRIES = 1024

_REASON_SCOPE_MISSING = "scope-missing"
_REASON_SCOPE_NOT_DIRECTORY = "scope-not-directory"
_REASON_SCOPE_SYMLINKED = "scope-symlinked"
_REASON_TOO_MANY_ENTRIES = "too-many-entries"
_REASON_ENTRY_UNSTABLE = "entry-unstable"
_REASON_SYMLINKED_ENTRY = "symlinked-entry"
_REASON_NESTED_DIRECTORY = "nested-directory"
_REASON_NON_REGULAR_ENTRY = "non-regular-entry"
_REASON_NO_TEST_ENTRIES = "no-test-entries"
_REASON_CUT_FILE_MISSING = "cut-file-missing"
_REASON_GROUP_EMPTY = "group-empty"


class PartitionRefusal(Exception):
    """The scope is not a supported flat test layout. ``reason`` is a
    bounded fixed token (no paths) identifying the refusal."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _is_test_name(name):
    """Exactly the two default file patterns: test_*.py or
    *_test.py (a regular .py file name only)."""
    if not name.endswith(".py"):
        return False
    return (name.startswith("test_") or name.endswith("_test.py"))


def partition_unit_tests(scope_dir):
    """Return (group_a, group_b): ordered absolute regular test
    paths, group B beginning at the fixed GROUP_B_FIRST file.

    Raises PartitionRefusal (bounded reason token) on any
    unsupported or unverifiable layout; never returns a partial or
    silently omitted membership."""
    try:
        root_st = os.lstat(scope_dir)
    except (OSError, TypeError):
        raise PartitionRefusal(_REASON_SCOPE_MISSING)
    if stat.S_ISLNK(root_st.st_mode):
        raise PartitionRefusal(_REASON_SCOPE_SYMLINKED)
    if not stat.S_ISDIR(root_st.st_mode):
        raise PartitionRefusal(_REASON_SCOPE_NOT_DIRECTORY)
    try:
        names = []
        it = os.scandir(scope_dir)
    except OSError:
        raise PartitionRefusal(_REASON_SCOPE_NOT_DIRECTORY)
    try:
        for entry in it:
            names.append(entry.name)
            if len(names) > MAX_SCOPE_ENTRIES:
                # Finite pre-materialization entry ceiling: refuse
                # an oversized scope before unbounded listing.
                raise PartitionRefusal(_REASON_TOO_MANY_ENTRIES)
    except OSError:
        raise PartitionRefusal(_REASON_SCOPE_NOT_DIRECTORY)
    finally:
        it.close()
    entries = []
    for name in sorted(names):
        if name.startswith("."):
            # Hidden entries (generated __pycache__ and the like)
            # are not test entries; the locked pytest version
            # ignores dot-prefixed entries as well.
            continue
        try:
            st = os.lstat(os.path.join(scope_dir, name))
        except OSError:
            # The entry vanished under the bounded inventory:
            # refuse rather than guess a membership.
            raise PartitionRefusal(_REASON_ENTRY_UNSTABLE)
        if stat.S_ISLNK(st.st_mode):
            # Symlinked scope entry (test or otherwise): refuse
            # instead of silently omitting a possibly real test.
            raise PartitionRefusal(_REASON_SYMLINKED_ENTRY)
        if stat.S_ISDIR(st.st_mode):
            if name == "__pycache__":
                # Generated bytecode cache: not a test entry
                # (order 009-s); never followed (one-level
                # inventory).
                continue
            # Any other nonhidden nested layout is unsupported
            # for this flat partition; refuse instead of
            # recursing or omitting.
            raise PartitionRefusal(_REASON_NESTED_DIRECTORY)
        if not stat.S_ISREG(st.st_mode):
            raise PartitionRefusal(_REASON_NON_REGULAR_ENTRY)
        if _is_test_name(name):
            entries.append(name)
    if not entries:
        raise PartitionRefusal(_REASON_NO_TEST_ENTRIES)
    if GROUP_B_FIRST not in entries:
        raise PartitionRefusal(_REASON_CUT_FILE_MISSING)
    cut = entries.index(GROUP_B_FIRST)
    group_a = entries[:cut]
    group_b = entries[cut:]
    if not group_a or not group_b:
        raise PartitionRefusal(_REASON_GROUP_EMPTY)
    return ([os.path.join(scope_dir, n) for n in group_a],
            [os.path.join(scope_dir, n) for n in group_b])


if __name__ == "__main__":
    # No public CLI: the module is imported by the supervisor only.
    raise SystemExit(2)
