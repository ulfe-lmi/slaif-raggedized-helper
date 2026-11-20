"""Default-discovered stdlib-only unittest for
oap/bin/ci_unit_resources.py (order 009-r, bounded own-cgroup
numeric observation).

Fixed census specified BEFORE execution (not adjusted afterwards):

* 10 test methods in one single-threaded module (unittest main
  thread only; no extra threads, no fork anywhere);
* 0 owned children (pure parser/renderer logic over owned synthetic
  fixture files in a private 0700 temp root; no real cgroup mutation,
  no privilege, no /proc or /sys write, no path output, no shell);
* every cgroup input is an owned synthetic fixture: a fake
  /proc/self/cgroup text file plus a fake cgroup2 directory tree
  under the temp root, passed through the documented private
  proc_path/mount_root seams; the only real reads are the test
  process's own RLIMIT_CPU and the read-only zero-size procfs
  pseudofile /proc/self/cgroup (bounded, read-only, no mutation);
* no network, no keys, no GPU, no model download, no product
  import, no uv.
"""
import os
import resource
import stat
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE / "oap" / "bin"))
import ci_unit_resources as cur  # noqa: E402


class CiUnitResourcesTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ci-unit-res-test-")
        self.assertEqual(stat.S_IMODE(os.lstat(self.root).st_mode),
                         0o700)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)

    def _cgroup_tree(self, components, memory=None, pids=None):
        """Build an owned synthetic cgroup2 tree below a fake trusted
        mount; returns (mount, target). Event file contents are the
        exact bytes given (str or bytes); None omits the file. Each
        call gets its own mount so several trees may coexist."""
        self._tree_n = getattr(self, "_tree_n", 0) + 1
        mount = os.path.join(self.root, "cg%d" % self._tree_n)
        target = os.path.join(mount, *components)
        os.makedirs(target)
        if memory is not None:
            with open(os.path.join(target,
                                   cur.MEMORY_EVENTS), "wb") as f:
                f.write(memory if isinstance(memory, bytes)
                        else memory.encode("utf-8"))
        if pids is not None:
            with open(os.path.join(target, cur.PIDS_EVENTS), "wb") as f:
                f.write(pids if isinstance(pids, bytes)
                        else pids.encode("utf-8"))
        return mount, target

    def _proc_file(self, text):
        proc = os.path.join(self.root, "self-cgroup")
        with open(proc, "wb") as f:
            f.write(text if isinstance(text, bytes)
                    else text.encode("utf-8"))
        return proc

    def test_01_unified_row_parsing(self):
        # Exactly one unified row is the requirement; v1 rows are
        # ignored; zero or multiple unified rows are refused.
        self.assertEqual(cur.parse_unified_cgroup_path("0::/\n"), [])
        self.assertEqual(
            cur.parse_unified_cgroup_path(
                "12:cpu:/x\n0::/system.slice/ci.scope\n1:name:unknown:/\n"),
            ["system.slice", "ci.scope"])
        self.assertIsNone(cur.parse_unified_cgroup_path("12:cpu:/x\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path("0::/a\n0::/b\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path("0::\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path("1::/a\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path(""))
        self.assertIsNone(cur.parse_unified_cgroup_path("0:/a\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path("0:1:/a\n"))
        # Colons are canonical cgroup-name characters (accepted).
        self.assertEqual(cur.parse_unified_cgroup_path("0::/a:1/b\n"),
                         ["a:1", "b"])

    def test_02_component_validation(self):
        # Canonical absolute components only: bounded count/length,
        # no dots, no empty segments, conservative ASCII set.
        self.assertIsNone(cur.parse_unified_cgroup_path("0::relative\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path("0::/a/../b\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path("0::/./a\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path("0:://a\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path(
            "0::/" + "x" * (cur.PATH_COMPONENT_LEN_MAX + 1) + "\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path(
            "0::/" + "/".join("d%d" % i
                              for i in range(cur.PATH_DEPTH_MAX + 1))
            + "\n"))
        self.assertIsNone(cur.parse_unified_cgroup_path(
            "0::/\u00e9caf\u00e9\n"))
        self.assertEqual(
            cur.parse_unified_cgroup_path(
                "0::/system.slice/user-1000.slice/session-3.scope\n"),
            ["system.slice", "user-1000.slice", "session-3.scope"])

    def test_03_event_file_parsing(self):
        # A complete normal kernel memory.events.local: the kernel
        # documents low/high plus oom_group_kill/sock_throttled
        # alongside the selected fields; untracked valid keys are
        # parsed and ignored, tracked values are exact.
        d = cur.parse_events(
            b"low 0\nhigh 0\nmax 5\noom 0\n"
            b"oom_kill 0\n"
            b"oom_group_kill 0\n"
            b"sock_throttled 0\n")
        self.assertEqual(d, {"low": 0, "high": 0, "max": 5, "oom": 0,
                             "oom_kill": 0, "oom_group_kill": 0,
                             "sock_throttled": 0})
        self.assertEqual(d["max"], 5)
        self.assertEqual(d["oom"], 0)
        self.assertEqual(d["oom_kill"], 0)
        # Untracked keys in a pids-style file are ignored too.
        self.assertEqual(cur.parse_events(b"anything 7\nmax 3\n"),
                         {"anything": 7, "max": 3})
        self.assertEqual(cur.parse_events(b""), {})
        self.assertEqual(cur.parse_events(b"\n"), {})
        # Malformed lines refuse the whole file without raising.
        self.assertIsNone(cur.parse_events(b"max 3 extra\n"))
        self.assertIsNone(cur.parse_events(b"max -1\n"))
        self.assertIsNone(cur.parse_events(b"max +1\n"))
        self.assertIsNone(cur.parse_events(b"max 1x\n"))
        self.assertIsNone(cur.parse_events(b"max\n"))
        self.assertIsNone(cur.parse_events(b"max  5\n"))
        self.assertIsNone(cur.parse_events(b"=max 5\n"))
        self.assertIsNone(cur.parse_events(b"max 9223372036854775808\n"))
        self.assertIsNone(cur.parse_events(b"max 5\nmax 6\n"))
        self.assertIsNone(cur.parse_events(b"low 5\nlow 6\n"))
        self.assertIsNone(cur.parse_events(b"\xff\xfe\n"))
        # Non-ASCII numeric text (a Unicode digit) cannot bypass the
        # bounded ASCII value grammar.
        self.assertIsNone(cur.parse_events("max \u0665\n".encode("utf-8")))
        self.assertIsNone(cur.parse_events(
            "m\u00e1x 1\n".encode("utf-8")))
        self.assertEqual(cur.parse_events(b"max 9223372036854775807\n")
                         ["max"], cur.COUNTER_MAX - 1)

    def test_04_oversize_and_malformed_refused(self):
        # Bounded line count, bounded file size (at the read seam).
        self.assertIsNone(
            cur.parse_events(b"max 5\n" * (cur.EVENT_LINE_MAX + 1)))
        mount, target = self._cgroup_tree(
            ["s"], memory="max 1\n", pids="max 1\n")
        with open(os.path.join(target, cur.MEMORY_EVENTS), "wb") as f:
            f.write(b"max 1\n" + b"x" * (cur.FILE_MAX_BYTES + 1))
        proc = self._proc_file("0::/s\n")
        snap = cur.snapshot(proc_path=proc, mount_root=mount)
        self.assertIsNotNone(snap["identity"])
        self.assertIsNone(snap["memory_max"])
        self.assertEqual(snap["pids_max"], 1)
        # An event file that is a symlink is refused, not followed.
        real = os.path.join(self.root, "real-events")
        with open(real, "wb") as f:
            f.write(b"max 9\n")
        os.unlink(os.path.join(target, cur.PIDS_EVENTS))
        os.symlink(real, os.path.join(target, cur.PIDS_EVENTS))
        snap2 = cur.snapshot(proc_path=proc, mount_root=mount)
        self.assertIsNone(snap2["pids_max"])

    def test_05_snapshot_stable_positive(self):
        mount, target = self._cgroup_tree(
            ["system.slice", "ci.scope"],
            memory="high 0\nmax 1\noom 0\noom_kill 0\n",
            pids="max 3\n")
        proc = self._proc_file("0::/system.slice/ci.scope\n")
        snap = cur.snapshot(proc_path=proc, mount_root=mount)
        st = os.lstat(target)
        self.assertEqual(snap["identity"], (st.st_dev, st.st_ino))
        self.assertEqual(snap["memory_max"], 1)
        self.assertEqual(snap["memory_oom"], 0)
        self.assertEqual(snap["memory_oom_kill"], 0)
        self.assertEqual(snap["pids_max"], 3)
        # Root cgroup ("0::/") maps to the trusted mount itself.
        mount2, target2 = self._cgroup_tree(
            [], memory="max 0\n", pids="max 1\n")
        proc2 = self._proc_file("0::/\n")
        snap2 = cur.snapshot(proc_path=proc2, mount_root=mount2)
        st2 = os.lstat(target2)
        self.assertEqual(snap2["identity"], (st2.st_dev, st2.st_ino))
        self.assertEqual(snap2["pids_max"], 1)

    def test_06_snapshot_unavailable_boundaries(self):
        # Missing/malformed inputs report unavailable, never a guess.
        empty = {"identity": None, "memory_max": None,
                 "memory_oom": None, "memory_oom_kill": None,
                 "pids_max": None}
        self.assertEqual(cur.snapshot(
            proc_path=os.path.join(self.root, "absent"),
            mount_root=self.root), empty)
        mount, target = self._cgroup_tree(
            ["s"], memory="max 1\n", pids="max 1\n")
        proc = self._proc_file("12:cpu:/s\n")  # no unified row
        self.assertEqual(cur.snapshot(proc_path=proc,
                                      mount_root=mount), empty)
        proc = self._proc_file("0::/s\n0::/t\n")  # two unified rows
        self.assertEqual(cur.snapshot(proc_path=proc,
                                      mount_root=mount), empty)
        proc = self._proc_file("0::/a/../s\n")  # traversal component
        self.assertEqual(cur.snapshot(proc_path=proc,
                                      mount_root=mount), empty)
        # No exact mount mapping: the unified path is not below the
        # trusted mount.
        proc = self._proc_file("0::/other\n")
        self.assertEqual(cur.snapshot(proc_path=proc,
                                      mount_root=mount), empty)
        # A symlink directory in the chain is refused.
        linkmount = os.path.join(self.root, "lm")
        os.makedirs(os.path.join(linkmount, "target-dir"))
        os.symlink(os.path.join(linkmount, "target-dir"),
                   os.path.join(linkmount, "s"))
        proc = self._proc_file("0::/s\n")
        self.assertEqual(cur.snapshot(proc_path=proc,
                                      mount_root=linkmount), empty)
        # Missing event file: only the affected counters unavailable.
        mount2, target2 = self._cgroup_tree(
            ["s"], pids="max 2\n")
        proc2 = self._proc_file("0::/s\n")
        snap2 = cur.snapshot(proc_path=proc2, mount_root=mount2)
        self.assertIsNotNone(snap2["identity"])
        self.assertIsNone(snap2["memory_max"])
        self.assertIsNone(snap2["memory_oom"])
        self.assertIsNone(snap2["memory_oom_kill"])
        self.assertEqual(snap2["pids_max"], 2)
        # Malformed event line: that file's counters unavailable.
        mount3, target3 = self._cgroup_tree(
            ["s"], memory="max 1\nbogus\n", pids="max 2\n")
        proc3 = self._proc_file("0::/s\n")
        snap3 = cur.snapshot(proc_path=proc3, mount_root=mount3)
        self.assertIsNone(snap3["memory_max"])
        self.assertEqual(snap3["pids_max"], 2)

    def test_07_render_deltas_reset_and_identity(self):
        before = {"identity": (1, 2), "memory_max": 1, "memory_oom": 0,
                  "memory_oom_kill": 0, "pids_max": 3}
        after = {"identity": (1, 2), "memory_max": 2, "memory_oom": 0,
                 "memory_oom_kill": 0, "pids_max": 3}
        frag = cur.render(("unlimited", "unlimited"), before, after)
        self.assertEqual(
            frag,
            "rlimit_cpu=unlimited:unlimited "
            "cgroup=mem_max+1:oom+0:oom_kill+0:pids_max+0")
        # Counter reset: only the affected observation unavailable.
        after2 = dict(after, memory_max=0)
        frag2 = cur.render(None, before, after2)
        self.assertEqual(
            frag2,
            "rlimit_cpu=unavailable:unavailable "
            "cgroup=mem_max=unavailable:oom+0:oom_kill+0:pids_max+0")
        # Identity change (unstable cgroup): whole observation
        # unavailable; no per-counter attribution.
        after3 = dict(after, identity=(1, 3))
        frag3 = cur.render(("5", "unlimited"), before, after3)
        self.assertEqual(frag3,
                         "rlimit_cpu=5:unlimited cgroup=unavailable")
        # Missing snapshots / missing identity: unavailable.
        frag4 = cur.render(("unlimited", "unlimited"), None, None)
        self.assertEqual(frag4,
                         "rlimit_cpu=unlimited:unlimited "
                         "cgroup=unavailable")
        before_no_id = dict(before, identity=None)
        frag5 = cur.render(("unlimited", "unlimited"), before_no_id,
                           after)
        self.assertEqual(frag5,
                         "rlimit_cpu=unlimited:unlimited "
                         "cgroup=unavailable")
        # One-side unavailable counter: that observation unavailable.
        after6 = dict(after, pids_max=None)
        frag6 = cur.render(("unlimited", "unlimited"), before, after6)
        self.assertEqual(
            frag6,
            "rlimit_cpu=unlimited:unlimited "
            "cgroup=mem_max+1:oom+0:oom_kill+0:pids_max=unavailable")
        # No path output anywhere.
        for f in (frag, frag2, frag3, frag4, frag5, frag6):
            self.assertNotIn("/", f)
            self.assertNotIn(self.root, f)

    def test_08_rlimit_cpu_grammar(self):
        # The one real read: this process's own inherited RLIMIT_CPU,
        # described with the bounded decimal/unlimited/unavailable
        # grammar and consistent with resource.getrlimit.
        soft, hard = cur.rlimit_cpu()
        for desc in (soft, hard):
            self.assertRegex(desc,
                             r"^(unlimited|unavailable|[0-9]{1,12})$")
        actual = resource.getrlimit(resource.RLIMIT_CPU)

        def expected(value):
            if value == -1:
                return "unlimited"
            if (isinstance(value, int) and not isinstance(value, bool)
                    and 0 <= value < cur.RLIMIT_DECIMAL_MAX):
                return str(value)
            return "unavailable"

        self.assertEqual(soft, expected(actual[0]))
        self.assertEqual(hard, expected(actual[1]))

    def test_09_render_bounded_length(self):
        # The summary fragment stays a fixed small numeric string
        # even at the counter bound.
        before = {"identity": (1, 2), "memory_max": 2 ** 62,
                  "memory_oom": 2 ** 62, "memory_oom_kill": 2 ** 62,
                  "pids_max": 2 ** 62}
        after = {"identity": (1, 2), "memory_max": 2 ** 62 + 1,
                 "memory_oom": 2 ** 62 + 1,
                 "memory_oom_kill": 2 ** 62 + 1,
                 "pids_max": 2 ** 62 + 1}
        frag = cur.render(("unlimited", "unlimited"), before, after)
        self.assertEqual(
            frag,
            "rlimit_cpu=unlimited:unlimited "
            "cgroup=mem_max+1:oom+1:oom_kill+1:pids_max+1")
        self.assertLess(len(frag), 160)

    def test_10_procfs_zero_size_pseudofile_real_read(self):
        # The observed real defect class: /proc/self/cgroup is a
        # procfs regular file whose stat size (0) does not describe
        # the generated text; the bounded read must run to EOF under
        # the strict cap-plus-one and return the real bytes.
        # Read-only, no mutation, no privilege.
        proc = cur.PROC_CGROUP
        st = os.lstat(proc)
        self.assertTrue(stat.S_ISREG(st.st_mode))
        self.assertEqual(st.st_size, 0)
        data = cur._bounded_read(proc)
        self.assertIsNotNone(data, "zero-size pseudofile must still read")
        self.assertGreater(len(data), 0)
        self.assertLessEqual(len(data), cur.FILE_MAX_BYTES)
        lines = data.decode("utf-8").split("\n")
        self.assertTrue(any(ln for ln in lines))


if __name__ == "__main__":
    unittest.main()
