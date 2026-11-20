"""Default-discovered stdlib-only unittest for
oap/bin/ci_unit_partition.py (order 009-s, bounded one-level flat
tests/unit partition).

Fixed census specified BEFORE execution (not adjusted afterwards):

* 12 test methods in one single-threaded module (unittest main
  thread only; no extra threads, no fork anywhere);
* 0 child processes (pure bounded filesystem checks on owned
  synthetic 0700 temp trees only);
* no network, no keys, no GPU, no model download, no product
  import, no uv; no skip/xfail/selector/fake module.

Coverage notes: the positive cases prove exact regular-path
admission of BOTH default patterns (test_*.py and *_test.py),
ordinary non-test files and generated/hidden entries not being test
entries, deterministic name-sorted order, disjoint complete
membership, absolute in-scope paths and a repeatable result. The
negative cases are actual owned filesystem layouts (nested
nonhidden directory, symlinked scope, symlinked test and non-test
entries, FIFO entry, vanishing-scope variants, absent cut file, cut
file sorting first, and the finite pre-materialization entry
ceiling on an oversized scope) refused with the exact bounded
reason token - never a partial or silently omitted membership.
"""
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE / "oap" / "bin"))
import ci_unit_partition as cup  # noqa: E402


def _mktest(root, name):
    path = os.path.join(root, name)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    return path


class CiUnitPartitionTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ci-unit-partition-test-")
        self.assertEqual(stat.S_IMODE(os.lstat(self.root).st_mode),
                         0o700)
        self.scope = os.path.join(self.root, "unit")
        os.makedirs(self.scope)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)

    def _refused_reason(self):
        with self.assertRaises(cup.PartitionRefusal) as ctx:
            cup.partition_unit_tests(self.scope)
        return ctx.exception.reason

    def _happy_layout(self):
        for name in ("test_a.py", "b_test.py", "test_mid.py",
                     "test_owned_gpu_worker.py", "test_z.py",
                     "z_test.py"):
            _mktest(self.scope, name)
        _mktest(self.scope, "conftest.py")
        _mktest(self.scope, "__init__.py")
        _mktest(self.scope, "helper.py")
        os.makedirs(os.path.join(self.scope, "__pycache__"))
        _mktest(os.path.join(self.scope, "__pycache__"),
                "test_hidden_in_pycache.py")

    def test_01_positive_both_patterns_ordered_disjoint(self):
        self._happy_layout()
        a, b = cup.partition_unit_tests(self.scope)
        self.assertEqual([os.path.basename(p) for p in a],
                         ["b_test.py", "test_a.py", "test_mid.py"])
        self.assertEqual([os.path.basename(p) for p in b],
                         ["test_owned_gpu_worker.py", "test_z.py",
                          "z_test.py"])
        # Group B begins exactly at the fixed cut file.
        self.assertEqual(os.path.basename(b[0]),
                         cup.GROUP_B_FIRST)
        # Disjoint, complete (no omission, no extra), in scope.
        self.assertEqual(len(a) + len(b), 6)
        self.assertEqual(set(a) & set(b), set())
        self.assertEqual(set(a) | set(b),
                         {os.path.join(self.scope, n)
                          for n in ("test_a.py", "b_test.py",
                                    "test_mid.py",
                                    "test_owned_gpu_worker.py",
                                    "test_z.py", "z_test.py")})

    def test_02_deterministic_repeat_absolute_paths(self):
        self._happy_layout()
        first = cup.partition_unit_tests(self.scope)
        second = cup.partition_unit_tests(self.scope)
        self.assertEqual(first, second)
        for group in first:
            for path in group:
                self.assertTrue(os.path.isabs(path), path)
                self.assertEqual(os.path.dirname(path), self.scope)
                self.assertTrue(os.path.isfile(path))

    def test_03_empty_scope_refused(self):
        self.assertEqual(self._refused_reason(), "no-test-entries")
        # Only generated hidden entries: still no test entries.
        os.makedirs(os.path.join(self.scope, "__pycache__"))
        _mktest(os.path.join(self.scope, "__pycache__"),
                "test_only_hidden.py")
        self.assertEqual(self._refused_reason(), "no-test-entries")

    def test_04_cut_file_missing_refused(self):
        _mktest(self.scope, "test_a.py")
        _mktest(self.scope, "test_b.py")
        self.assertEqual(self._refused_reason(), "cut-file-missing")

    def test_05_cut_file_first_group_a_empty_refused(self):
        # test_owned_gpu_worker.py sorts before both other names
        # ('.' < '2' and 't' < 'z'): group A would be empty.
        _mktest(self.scope, "test_owned_gpu_worker.py")
        _mktest(self.scope, "test_owned_gpu_worker2.py")
        _mktest(self.scope, "zzz_test.py")
        self.assertEqual(self._refused_reason(), "group-empty")

    def test_06_nested_nonhidden_directory_refused(self):
        _mktest(self.scope, "test_a.py")
        _mktest(self.scope, "test_owned_gpu_worker.py")
        _mktest(self.scope, "test_b.py")
        nested = os.path.join(self.scope, "sub")
        os.makedirs(nested)
        _mktest(nested, "test_nested.py")
        self.assertEqual(self._refused_reason(), "nested-directory")

    def test_07_symlinked_entries_refused(self):
        _mktest(self.scope, "test_owned_gpu_worker.py")
        _mktest(self.scope, "test_b.py")
        outside = os.path.join(self.root, "outside_test.py")
        _mktest(self.root, "outside_test.py")
        os.symlink(outside, os.path.join(self.scope,
                                         "test_symlinked.py"))
        self.assertEqual(self._refused_reason(), "symlinked-entry")
        # A symlinked NON-test entry is refused the same way.
        os.unlink(os.path.join(self.scope, "test_symlinked.py"))
        _mktest(self.root, "outside_helper.py")
        os.symlink(os.path.join(self.root, "outside_helper.py"),
                   os.path.join(self.scope, "helper_link.py"))
        self.assertEqual(self._refused_reason(), "symlinked-entry")

    def test_08_symlinked_scope_refused(self):
        real = self.scope + "-real"
        os.rename(self.scope, real)
        os.symlink(real, self.scope)
        self.assertEqual(self._refused_reason(), "scope-symlinked")

    def test_09_non_regular_entry_refused(self):
        _mktest(self.scope, "test_owned_gpu_worker.py")
        _mktest(self.scope, "test_b.py")
        os.mkfifo(os.path.join(self.scope, "pipe_data"))
        self.assertEqual(self._refused_reason(), "non-regular-entry")

    def test_10_missing_or_file_scope_refused(self):
        self.assertEqual(
            self._refused_missing("nope"), "scope-missing")
        file_scope = os.path.join(self.root, "file-scope")
        _mktest(self.root, "file-scope")
        self.assertEqual(
            self._refused_missing(file_scope), "scope-not-directory")

    def _refused_missing(self, path):
        with self.assertRaises(cup.PartitionRefusal) as ctx:
            cup.partition_unit_tests(path)
        return ctx.exception.reason

    def test_11_hidden_and_ordinary_entries_not_test_entries(self):
        self._happy_layout()
        # A hidden directory containing a test-named file is not
        # followed (one-level inventory) and not a test entry.
        hidden = os.path.join(self.scope, ".hidden")
        os.makedirs(hidden)
        _mktest(hidden, "test_hidden.py")
        a, b = cup.partition_unit_tests(self.scope)
        self.assertEqual(len(a) + len(b), 6)
        # The generated __pycache__ test-named file is never in any
        # group, and ordinary files are not test entries.
        for path in a + b:
            self.assertNotIn("__pycache__", path)
            self.assertNotIn(".hidden", path)
            self.assertTrue(os.path.basename(path)
                            .startswith("test_")
                            or os.path.basename(path)
                            .endswith("_test.py"))


    def test_12_entry_ceiling_refused(self):
        # The one-level inventory is itself bounded: the finite
        # pre-materialization entry ceiling refuses an oversized
        # scope (ceiling+1 entries) with the exact token, instead
        # of materializing an unbounded listing.
        for i in range(cup.MAX_SCOPE_ENTRIES + 1):
            _mktest(self.scope, "t%04d_test.py" % i)
        self.assertEqual(self._refused_reason(), "too-many-entries")


if __name__ == "__main__":
    unittest.main()
