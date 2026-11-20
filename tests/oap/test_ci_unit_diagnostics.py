"""Default-discovered stdlib-only unittest for
oap/bin/ci_unit_diagnostics.py (order 009-k, owned unit-diagnostics
supervisor).

Fixed census specified BEFORE execution (not adjusted afterwards):

* 21 test methods in one single-threaded module (unittest main thread
  only; no extra threads, no fork anywhere);
* 15 returned/owned direct children TOTAL (test 1: 1, test 2: 2,
  tests 3-6: 1 each, test 10: 1, test 11: 1, test 13: 1, test 14: 1,
  test 15: 1, test 18: 1, test 20: 2; tests 8-9, 12, 16, 17, 19 and
  21: 0), every one reaped inside the supervised run's owned
  teardown; PLUS test 7's 1 FAILED Popen constructor/exec launch
  attempt (no returned child; low-level creation on a failed
  constructor is platform/stdlib dependent, so creation attempts are
  conservatively budgeted 16; the stdlib constructor owns its
  failed-exec reap; the utility invents no PID);
* 0 grandchildren (the retained-handle case holds the extra fd in the
  test parent itself - an honest model, no orphan experiment);
* max 1 concurrent owned process (sequential runs);
* children are short ``sys.executable -c`` stdlib scripts only: no
  network, no keys, no GPU, no model download, no product import, no
  uv, no fixture environment;
* short synthetic bounds for the cases (deadline 1-20 s, grace/post-
  kill/drain 1 s); per-case wall bound asserted (< 15 s each); whole-
  suite wall expectation < 60 s; no skip/xfail/selector/fake module.

Coverage notes: the forwarder regressions (test 12) are pure-byte (no
process): legacy introducers, CR/LF across chunk boundaries, partial
UTF-8, giant lines, control bytes, cap truncation. The backpressure
case (test 14) drives the production writer factory on a REAL pipe
with a stalled reader (the actual default-channel class), not only a
bytearray sink. The interrupt case (test 15) drives the latched
request seam that production ``main`` wires to its scoped non-raising
SIGTERM/SIGINT handlers. Every process case observes the actual owned
child termination (exit codes 0/7/5 preserved exactly; signalled
termination via the separate child-signal field, no 128 addition), the
group decision record and the proven/unproven cleanup state.
The post-launch cancellation case (test 13) injects a BaseException
through the controlled seam inside the owned post-Popen boundary
(bookkeeping done, monitor not started) and inspects the actual
private abort record for a truthful non-OK status/terminated_by with
the proven group/cleanup state preserved and the same primary
unmasked (no external signal immunity claim). The pure post-teardown
refusal mapping case (test 16) is process-free. The post-teardown-only
integration case (test 18) runs one real stdlib child to a clean exit,
lets the real bounded teardown complete, then refuses the drain's
first piece offer through the test's own sink (observational seam; no
fake process/thread/hostscan): break_reason stays None, drain_refused
maps to an honest nonzero, the child is reaped, raw log preserved. The
prelaunch sink-unavailable case (test 19) is process-free with zero
Popen attempts: a safe owned temp root yields the bounded private
evidence record (truthful PREREQUISITE/sink-unavailable); missing or
unsafe roots stay honest no-artifact (tests 8-9). The order 009-r
bounded synthetic OAP check (test 20) drives two real stdlib children
through the unchanged supervisor: a positive exit 137 (the hosted
wrapper exit code) and a real direct self-issued SIGKILL produce
DISTINCT owned wait results - exact normal exit 137 with child_signal
None (status OK, exit 137 preserved, reconciled Popen returncode)
versus the separate child-signal field with child_exit None (status
CHILD_SIGNALED, exit 131), never a 128-addition; the SIGKILL child
installs a SIGTERM marker handler before its self-kill and the marker
is never written, proving the identity-verified owned group sweep
signalled no live process outside the child's own self-kill (an
unowned process is never signalled). The main-only direct
pytest-console projection (test 21) is process-free (no child, no
launch): the exact projected argv (fixed installed console plus the
unchanged trailing suite args) and environment (inherited env plus
repo .venv VIRTUAL_ENV and its bin as the first PATH entry) over an
owned synthetic repo tree, plus the clean prelaunch refusal (None)
for a missing, non-executable, external-shebang, no-shebang,
non-ASCII-shebang, interpreter-less, pyvenv.cfg-less or
symlinked-venv console. Proven-reap cases
(1, 2, 3, 4) observe the reconciled Popen returncode bookkeeping
(0/7/5, -15, -9), so the stdlib destructor performs no numeric
waitpid after identity release. The process-free summary-phase case
(test 17) reaches the real phase-2 record serialization and the main
summary-refusal boundary via private seams only (distinct exclusive
record, exact persisted nonzero, truthful run-record path/byte
metadata, no overwrite).
Controlled models are not real kernel/OOM/signal qualification.
"""
import fcntl
import json
import os
import signal
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE / "oap" / "bin"))
import ci_unit_diagnostics as cud  # noqa: E402

CASE_WALL_S = 15.0


def _child(script):
    return [sys.executable, "-c", script]


def _run_case(argv, temp_root, **kwargs):
    """Run one supervised case with the short synthetic bounds; assert
    the per-case wall bound and return (result, forwarded_bytes).
    The byte-capturing sink is the DEFAULT only: a caller may supply
    sink= (e.g. the real production backpressure writer), in which
    case forwarded_bytes is None and the result record carries the
    forwarded byte count."""
    kwargs.setdefault("deadline_s", 10.0)
    kwargs.setdefault("kill_grace_s", 1.0)
    kwargs.setdefault("post_kill_s", 1.0)
    kwargs.setdefault("post_drain_s", 1.0)
    sink = None
    if "sink" not in kwargs:
        sink = bytearray()
        kwargs["sink"] = sink.extend
    result = cud.run_child(argv, temp_root=temp_root, **kwargs)
    assert result["elapsed"] is not None and result["elapsed"] < CASE_WALL_S, \
        result
    return result, (bytes(sink) if sink is not None else None)


def _pid_gone(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def _collect(f):
    out = []
    while f.has_piece():
        out.append(f.take_piece())
    return out


class CiUnitDiagnosticsTest(unittest.TestCase):
    def setUp(self):
        # mkdtemp's private semantics create the directory 0700 and
        # verify it; observe the mode genuinely (no unsupported kw).
        self.root = tempfile.mkdtemp(prefix="ci-unit-diag-test-")
        self.assertEqual(stat.S_IMODE(os.lstat(self.root).st_mode),
                         0o700)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)

    def _owned_log(self, name="unit.log"):
        path = os.path.join(self.root, name)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        return path

    def test_01_normal_zero_regular_file_stdio_and_stdin_eof(self):
        log = self._owned_log()
        st = os.lstat(log)
        script = (
            "import os, stat, sys\n"
            "one = os.fstat(1)\n"
            "two = os.fstat(2)\n"
            "assert stat.S_ISREG(one.st_mode), one\n"
            "assert stat.S_ISREG(two.st_mode), two\n"
            "assert one.st_ino == %d and one.st_dev == %d\n"
            "assert two.st_ino == %d and two.st_dev == %d\n"
            "got = sys.stdin.buffer.read()\n"
            "assert got == b'', 'stdin must be EOF (DEVNULL)'\n"
            "with open(%r, 'w') as fh:\n"
            "    fh.write(str(os.getpid()))\n"
            "sys.stdout.write('hello-stdout\\n')\n"
            "sys.stderr.write('hello-stderr\\n')\n"
            "sys.stdout.write('stdin-eof\\n')\n"
        ) % (st.st_ino, st.st_dev, st.st_ino, st.st_dev,
             os.path.join(self.root, "child-pid"))
        result, fwd = _run_case(_child(script), self.root, log_path=log)
        self.assertEqual(result["status"], cud.STATUS_OK, result)
        self.assertEqual(result["child_exit"], 0)
        self.assertIsNone(result["child_signal"])
        self.assertEqual(result["cleanup"], "PROVEN")
        # Uniform lifecycle: the bounded KILL sweep completes the group
        # escalation decision on the normal path too.
        self.assertTrue(result["group_term_issued"])
        self.assertTrue(result["group_kill_issued"])
        self.assertEqual(result["group_state"], "kill-issued")
        self.assertFalse(result["forward_truncated"])
        self.assertFalse(result["forward_refused"])
        pidfile = os.path.join(self.root, "child-pid")
        self.assertEqual(result["direct_pid"], int(open(pidfile).read()))
        raw = open(log, "rb").read()
        for marker in (b"hello-stdout\n", b"hello-stderr\n", b"stdin-eof\n"):
            # Raw private log keeps exact child bytes (no label) and is
            # preserved after the run (never deleted by the utility).
            self.assertIn(marker, raw)
            self.assertTrue(os.path.exists(log))
            # Forwarded stream carries the fixed per-line label.
            self.assertIn(cud.LABEL + marker, fwd)
        self.assertEqual(stat.S_IMODE(os.lstat(log).st_mode), 0o600)
        # K17: the observed manual reap reconciled the Popen
        # returncode (exact exit 0), so the stdlib destructor
        # performs no numeric waitpid after identity release.
        self.assertEqual(result["popen_returncode"], 0)
        self.assertTrue(_pid_gone(result["direct_pid"]))

    def test_02_nonzero_seven_and_pytest_style_five_preserved(self):
        result7, _ = _run_case(_child("import sys; sys.exit(7)"), self.root)
        self.assertEqual(result7["status"], cud.STATUS_OK, result7)
        self.assertEqual(result7["child_exit"], 7)
        self.assertIsNone(result7["child_signal"])
        self.assertEqual(cud.exit_code_for(result7), 7)
        self.assertEqual(result7["popen_returncode"], 7)
        self.assertEqual(result7["cleanup"], "PROVEN")
        # Generated private path privacy (production shape): 0700 dir,
        # 0600 exclusive regular log, both preserved, status record.
        d = result7["owned_dir"]
        self.assertIsNotNone(d, result7)
        self.assertEqual(stat.S_IMODE(os.lstat(d).st_mode), 0o700)
        self.assertEqual(
            stat.S_IMODE(os.lstat(result7["log_path"]).st_mode), 0o600)
        self.assertTrue(os.path.isfile(result7["log_path"]))
        self.assertTrue(os.path.isfile(result7["status_record_path"]))
        result5, _ = _run_case(_child("import sys; sys.exit(5)"), self.root)
        self.assertEqual(result5["status"], cud.STATUS_OK, result5)
        self.assertEqual(result5["child_exit"], 5)
        self.assertEqual(cud.exit_code_for(result5), 5)
        self.assertEqual(result5["popen_returncode"], 5)
        self.assertEqual(result5["cleanup"], "PROVEN")

    def test_03_deadline_term_path(self):
        result, _ = _run_case(
            _child("import time; time.sleep(30)"), self.root,
            deadline_s=1.0)
        self.assertEqual(result["status"], cud.STATUS_TIMEOUT, result)
        self.assertEqual(result["terminated_by"], "deadline")
        self.assertTrue(result["group_term_issued"])
        # The leader died from our TERM; the KILL sweep still completed
        # the group escalation decision (uniform lifecycle).
        self.assertTrue(result["group_kill_issued"])
        self.assertEqual(result["group_state"], "kill-issued")
        self.assertEqual(result["cleanup"], "PROVEN")
        self.assertEqual(result["child_signal"], signal.SIGTERM)
        # K17: observed reap reconciles the Popen returncode to the
        # stdlib signal convention (-SIGTERM).
        self.assertEqual(result["popen_returncode"], -signal.SIGTERM)
        self.assertIsNone(result["child_exit"])
        self.assertEqual(cud.exit_code_for(result), cud.EXIT_TIMEOUT)
        self.assertLess(result["elapsed"], CASE_WALL_S)
        self.assertTrue(_pid_gone(result["direct_pid"]))

    def test_04_deadline_kill_escalation_term_ignored(self):
        script = ("import signal, time\n"
                  "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                  "time.sleep(60)\n")
        result, _ = _run_case(_child(script), self.root, deadline_s=1.0)
        self.assertEqual(result["status"], cud.STATUS_TIMEOUT, result)
        self.assertEqual(result["terminated_by"], "deadline")
        self.assertTrue(result["group_term_issued"])
        # TERM was ignored: the bounded KILL escalation is required.
        self.assertTrue(result["group_kill_issued"])
        self.assertEqual(result["group_state"], "kill-issued")
        self.assertEqual(result["cleanup"], "PROVEN")
        self.assertEqual(result["child_signal"], signal.SIGKILL)
        # K17: observed reap reconciles the Popen returncode to the
        # stdlib signal convention (-SIGKILL).
        self.assertEqual(result["popen_returncode"], -signal.SIGKILL)
        self.assertIsNone(result["child_exit"])
        self.assertEqual(cud.exit_code_for(result), cud.EXIT_TIMEOUT)
        self.assertLess(result["elapsed"], CASE_WALL_S)
        self.assertTrue(_pid_gone(result["direct_pid"]))

    def test_05_observer_read_failure_cleans_up(self):
        calls = {"n": 0, "bytes": 0}

        def hook(fd, n):
            data = os.read(fd, n)  # delegate the genuine read
            if data:
                calls["n"] += 1
                calls["bytes"] += len(data)
            if calls["n"] >= 2:
                raise OSError("injected observer read failure")
            return data

        result, fwd = _run_case(
            _child("import sys, time\n"
                   "sys.stdout.write('observer-start\\n')\n"
                   "sys.stdout.flush()\n"
                   "time.sleep(0.3)\n"
                   "sys.stdout.write('observer-2\\n')\n"
                   "sys.stdout.flush()\n"
                   "time.sleep(30)\n"),
            self.root, deadline_s=20.0, read_hook=hook)
        self.assertEqual(result["status"], cud.STATUS_OBSERVER_FAILURE,
                         result)
        self.assertEqual(result["terminated_by"], "observer")
        self.assertGreaterEqual(calls["n"], 2)
        self.assertGreater(calls["bytes"], 0)
        self.assertEqual(result["cleanup"], "PROVEN")
        self.assertEqual(cud.exit_code_for(result),
                         cud.EXIT_OBSERVER_FAILURE)
        self.assertIn(cud.LABEL + b"observer-start\n", fwd)
        self.assertTrue(_pid_gone(result["direct_pid"]))

    def test_06_retained_extra_output_handle_no_eof_wait(self):
        # Honest model, no fork/orphan: the TEST PARENT holds an extra
        # fd on the owned log and passes one copy into the child. The
        # supervisor must complete on direct-child termination, never
        # waiting for any output handle to close.
        log = self._owned_log()
        held = os.open(log, os.O_RDONLY)
        try:
            result, fwd = _run_case(
                _child("import sys\n"
                       "sys.stdout.write('child-done\\n')\n"
                       "sys.stdout.flush()\n"),
                self.root, log_path=log, extra_fds=(held,))
        finally:
            os.close(held)
        self.assertEqual(result["status"], cud.STATUS_OK, result)
        self.assertEqual(result["child_exit"], 0)
        self.assertEqual(result["cleanup"], "PROVEN")
        self.assertLess(result["elapsed"], 5.0)
        self.assertIn(cud.LABEL + b"child-done\n", fwd)
        self.assertTrue(_pid_gone(result["direct_pid"]))

    def test_07_launch_failure_without_ownership(self):
        result, fwd = _run_case(
            ["/nonexistent/ci-unit-diag-missing-binary", "--flag"],
            self.root)
        self.assertEqual(result["status"], cud.STATUS_LAUNCH_FAILURE,
                         result)
        self.assertIsNone(result["direct_pid"])
        self.assertIsNone(result["child_exit"])
        self.assertEqual(cud.exit_code_for(result),
                         cud.EXIT_LAUNCH_FAILURE)
        self.assertEqual(fwd, b"")

    def test_08_missing_temp_root_fails_loudly(self):
        result, _ = _run_case(_child("import sys; sys.exit(0)"),
                              "/nonexistent/ci-unit-diag-root")
        self.assertEqual(result["status"], cud.STATUS_PREREQUISITE, result)
        self.assertEqual(result["terminated_by"], "prerequisite")
        self.assertIsNone(result["direct_pid"])
        self.assertEqual(cud.exit_code_for(result), cud.EXIT_PREREQUISITE)

    def test_09_unsafe_temp_root_fails_loudly(self):
        file_root = os.path.join(self.root, "not-a-dir")
        with open(file_root, "w") as fh:
            fh.write("x")
        result, _ = _run_case(_child("import sys; sys.exit(0)"), file_root)
        self.assertEqual(result["status"], cud.STATUS_PREREQUISITE, result)
        self.assertIsNone(result["direct_pid"])
        self.assertEqual(cud.exit_code_for(result), cud.EXIT_PREREQUISITE)

    def test_10_oversize_small_private_log_limit(self):
        log = self._owned_log()
        result, _ = _run_case(
            _child("import sys, time\n"
                   "sys.stdout.write('X' * 200)\n"
                   "sys.stdout.flush()\n"
                   "time.sleep(30)\n"),
            self.root, deadline_s=20.0, log_path=log, log_limit=100)
        self.assertEqual(result["status"], cud.STATUS_OVERSIZE, result)
        self.assertEqual(result["terminated_by"], "oversize")
        self.assertEqual(result["cleanup"], "PROVEN")
        self.assertEqual(cud.exit_code_for(result), cud.EXIT_OVERSIZE)
        self.assertTrue(_pid_gone(result["direct_pid"]))
        # Raw log evidence is preserved with the full child bytes.
        self.assertTrue(os.path.exists(log))
        self.assertEqual(os.lstat(log).st_size, 200)

    def test_11_forwarding_cap_honest_bounded_real_process(self):
        # Forward-total cap: two independent proofs. (1) A
        # deterministic process-free near-cap oracle on the real
        # forwarder proves the cap arithmetic and the reached marker
        # exactly. (2) A real fast regular-file child proves the
        # CONTRACT, not a schedule: near-full forwarding is NOT
        # guaranteed - the child can exit before the 4 MiB cap is
        # reached and the deliberately bounded post-drain budget can
        # expire first, so the old blanket forward_truncated
        # assertion was wrong (Root one-check failure). Asserted:
        # cap never exceeded; the reached marker is honest, and when
        # set sits within one labeled segment of the cap with the
        # first full segment in the stream; otherwise the forwardable
        # stream exceeded the cap, so a short stop is only honest as
        # a bounded-drain expiry; the full raw output stays
        # preserved. The actual per-case result is the assertion msg,
        # so a failure carries causal output (not UNPROVEN).
        # (1) Deterministic near-cap oracle (no process).
        oracle = cud._Forwarder(cud.FORWARD_TOTAL_BYTES,
                                cud.FORWARD_LINE_CHARS)
        oracle.offer(("B" * cud.FORWARD_LINE_CHARS + "\n")
                     .encode() * 1024)
        oracle.finish()
        self.assertTrue(oracle.truncated)
        self.assertLessEqual(oracle.forwarded, cud.FORWARD_TOTAL_BYTES)
        self.assertGreater(oracle.forwarded,
                           cud.FORWARD_TOTAL_BYTES - 4200)
        # (2) Real process: honest bounded outcome.
        log = self._owned_log()
        result, fwd = _run_case(
            _child("import sys\n"
                   "sys.stdout.write('A' * (5 * 1024 * 1024))\n"
                   "sys.stdout.flush()\n"),
            self.root, deadline_s=30.0, log_path=log)
        self.assertEqual(result["status"], cud.STATUS_OK, result)
        self.assertEqual(result["child_exit"], 0, result)
        self.assertEqual(result["cleanup"], "PROVEN", result)
        cap = cud.FORWARD_TOTAL_BYTES
        sent = result["forwarded_bytes"]
        self.assertLessEqual(sent, cap, result)
        if result["forward_truncated"]:
            # Cap arithmetic: the crossing labeled segment is
            # bounded, so the stop sits within one segment of cap.
            self.assertGreater(sent, cap - 4200, result)
            self.assertIn(cud.LABEL + b"A" * 4096 + b"\n", fwd)
        else:
            # The forwardable labeled segments strictly exceed the
            # cap, so EOF-before-cap is impossible here: a short
            # stop is honest only as a bounded-drain expiry.
            self.assertFalse(result["drain_refused"], result)
            self.assertTrue(result["drain_truncated"] or sent == cap,
                            result)
        # The full raw output is retained in the preserved private log.
        self.assertEqual(os.lstat(log).st_size, 5 * 1024 * 1024, result)

    def test_12_pure_byte_forwarder_regressions(self):
        # Legacy introducer anywhere in a line is neutralized.
        f = cud._Forwarder(cap=1 << 20, seg_bytes=4096)
        f.offer(b"xx ##[group] yy\n")
        pieces = _collect(f)
        joined = b"".join(pieces)
        self.assertNotIn(b"##[", joined)
        # Display escaping policy is '#' -> '%23' ONLY (no bracket
        # escape): '##[' becomes '%23%23['; the literal legacy marker
        # is absent from every forwarded byte.
        self.assertIn(b"%23%23[", joined)
        # Every emitted display line starts with the fixed LABEL, so a
        # new-style (line-leading) introducer cannot arise.
        for p in pieces:
            self.assertTrue(p.startswith(cud.LABEL), p)
        # CR/LF folding, including the chunk boundary (held CR).
        f2 = cud._Forwarder(cap=1 << 20, seg_bytes=4096)
        f2.offer(b"one\r")
        f2.offer(b"\ntwo\r\nthree\n")
        text2 = b"".join(_collect(f2))
        self.assertNotIn(b"\r", text2)
        self.assertIn(cud.LABEL + b"one\n", text2)
        self.assertIn(cud.LABEL + b"two\n", text2)
        self.assertIn(cud.LABEL + b"three\n", text2)
        # Partial UTF-8 across a chunk boundary decodes without loss.
        f3 = cud._Forwarder(cap=1 << 20, seg_bytes=4096)
        euro = "\u20ac".encode("utf-8")  # 3 bytes
        f3.offer(euro[:2])
        f3.offer(euro[2:] + b"\n")
        f3.finish()
        joined3 = b"".join(_collect(f3))
        self.assertIn(b"\xe2\x82\xac", joined3)
        self.assertNotIn("\ufffd".encode("utf-8"), joined3)
        # Giant line is segmented with bounded payloads; the payload
        # round-trips exactly (no unbounded accumulation).
        f4 = cud._Forwarder(cap=1 << 20, seg_bytes=16)
        f4.offer(b"B" * 1000 + b"\n")
        pieces4 = _collect(f4)
        payload4 = b"".join(p[len(cud.LABEL):-1] for p in pieces4)
        self.assertEqual(payload4, b"B" * 1000)
        for p in pieces4:
            self.assertLessEqual(len(p[len(cud.LABEL):-1]), 16)
        self.assertGreaterEqual(len(pieces4), 62)
        # Control bytes are escaped.
        f5 = cud._Forwarder(cap=1 << 20, seg_bytes=4096)
        f5.offer(b"ctl\x01\x7fend\n")
        joined5 = b"".join(_collect(f5))
        self.assertNotIn(b"\x01", joined5)
        self.assertNotIn(b"\x7f", joined5)
        self.assertIn(b"\\x01", joined5)
        self.assertIn(b"\\x7f", joined5)
        # Total cap truncation.
        f6 = cud._Forwarder(cap=len(cud.LABEL) + 20, seg_bytes=4096)
        f6.offer(b"C" * 100 + b"\n")
        self.assertTrue(f6.truncated)

    def test_13_postlaunch_cancellation_same_object_and_teardown(self):
        class _Probe(BaseException):
            pass

        probe = _Probe("probe")
        hooks = {"n": 0, "pid": None}

        def post_popen(child):
            # Controlled cancellation seam INSIDE the owned post-Popen
            # boundary: bookkeeping done, monitor not started yet.
            # Record the ACTUAL owned child.pid in the parent before
            # raising - no child-created file, no wait, no inference.
            hooks["n"] += 1
            self.assertEqual(hooks["n"], 1)
            hooks["pid"] = child.pid
            raise probe

        # Generated owned path (no explicit log_path) so the owned
        # directory exists and the abort record has a private home.
        script = ("import time\n"
                  "time.sleep(30)\n")
        try:
            cud.run_child(_child(script), temp_root=self.root,
                          deadline_s=20.0, kill_grace_s=1.0,
                          post_kill_s=1.0, post_drain_s=1.0,
                          post_popen_hook=post_popen)
        except BaseException as exc:
            self.assertIs(exc, probe, "same-object propagation")
        else:
            self.fail("probe BaseException must propagate to the caller")
        # The probe propagated only AFTER the owned teardown
        # completed inside run_child: the known child identity is
        # already gone - a single check, no wait, no poll inference.
        child_pid = hooks["pid"]
        self.assertIsInstance(child_pid, int)
        self.assertTrue(_pid_gone(child_pid), "child not torn down")
        # No zombie left to the test parent: the owned teardown reaped
        # the child (it is this process's direct child).
        with self.assertRaises(ChildProcessError):
            os.waitpid(child_pid, os.WNOHANG)
        # K20: the actual private abort record persisted by the
        # BaseException handler (observational inspection of the real
        # generated file - no fake fd/process/status) is truthful
        # non-OK, preserves the proven group/cleanup state, claims
        # the real child identity, and did not mask the same primary
        # asserted above. This seam proves no real external
        # SIGINT/OOM immunity.
        owned = [d for d in os.listdir(self.root)
                 if d.startswith("ci-unit-diag-")
                 and os.path.isdir(os.path.join(self.root, d))]
        self.assertEqual(len(owned), 1, os.listdir(self.root))
        rec = os.path.join(self.root, owned[0], "diagnostic-status.json")
        self.assertEqual(os.lstat(rec).st_mode & 0o777, 0o600)
        data = json.loads(open(rec).read())
        self.assertNotEqual(data["status"], cud.STATUS_OK)
        self.assertEqual(data["status"], cud.STATUS_OBSERVER_FAILURE)
        self.assertEqual(data["terminated_by"], "supervisor-error")
        self.assertEqual(data["cleanup"], "PROVEN")
        self.assertNotEqual(data["group_state"], "unproven")
        self.assertEqual(data["direct_pid"], child_pid)
        self.assertTrue(os.path.exists(
            os.path.join(self.root, owned[0], "unit-diagnostic.log")))
        self.assertEqual(hooks["n"], 1)

    def test_14_default_channel_backpressure_real_pipe(self):
        read_end, write_end = os.pipe()
        flags_before = fcntl.fcntl(write_end, fcntl.F_GETFL)
        try:
            writer = cud._backpressured_writer(
                write_end, write_poll_s=0.05, write_budget_s=0.3,
                wall_budget_s=0.6)
            # Stall the reader: the kernel pipe buffer fills and the
            # writer must refuse within its finite budgets.
            refused = None
            for _ in range(200):
                try:
                    writer(b"Z" * (64 * 1024))
                except cud._SinkRefused as exc:
                    refused = exc
                    break
            self.assertIsNotNone(refused, "backpressure never engaged")
            self.assertIn(refused.reason,
                          ("write-budget", "forward-wall-budget"))
            # No shared-channel open-file-flag leak.
            self.assertEqual(fcntl.fcntl(write_end, fcntl.F_GETFL),
                             flags_before)
            # Full supervised run on the stalled real channel: the owned
            # child is still torn down and the run fails honestly.
            result, _ = _run_case(
                _child("import sys, time\n"
                       "sys.stdout.write('bp\\n')\n"
                       "sys.stdout.flush()\n"
                       "time.sleep(30)\n"),
                self.root, deadline_s=2.0, sink=writer)
            self.assertEqual(result["status"],
                             cud.STATUS_OBSERVER_FAILURE, result)
            self.assertTrue(result["forward_refused"])
            self.assertIsInstance(result["forward_stopped_at_log_offset"],
                                  int)
            self.assertEqual(result["cleanup"], "PROVEN")
            self.assertEqual(cud.exit_code_for(result),
                             cud.EXIT_OBSERVER_FAILURE)
            self.assertTrue(_pid_gone(result["direct_pid"]))
        finally:
            os.close(read_end)
            os.close(write_end)

    def test_15_interrupt_latch_observed_after_owned_teardown(self):
        checks = {"n": 0}

        def latch():
            checks["n"] += 1
            return checks["n"] >= 2

        result, _ = _run_case(
            _child("import sys, time\n"
                   "sys.stdout.write('before-interrupt\\n')\n"
                   "sys.stdout.flush()\n"
                   "time.sleep(30)\n"),
            self.root, deadline_s=20.0, interrupt_check=latch)
        self.assertEqual(result["status"], cud.STATUS_OBSERVER_FAILURE,
                         result)
        self.assertEqual(result["terminated_by"], "interrupted")
        self.assertEqual(result["cleanup"], "PROVEN")
        self.assertEqual(cud.exit_code_for(result),
                         cud.EXIT_OBSERVER_FAILURE)
        self.assertTrue(_pid_gone(result["direct_pid"]))

    def test_16_pure_post_teardown_refusal_status_mapping(self):
        # Pure model (no process): a fast child completed PROVEN with
        # exact exit 0, then the post-teardown drain channel refused
        # the remaining output. Final status must be an honest
        # OBSERVER_FAILURE (126); intentional cap truncation stays
        # benign; stronger timeout/cleanup outcomes are preserved.
        base = {"cleanup": "PROVEN", "child_exit": 0,
                "group_state": "kill-issued"}
        refused = cud._new_result(
            cud.FORWARD_TOTAL_BYTES, cud.FORWARD_LINE_CHARS)
        refused.update(base, drain_refused=True)
        refused["status"] = cud._final_status(refused, None)
        self.assertEqual(refused["status"], cud.STATUS_OBSERVER_FAILURE)
        self.assertEqual(cud.exit_code_for(refused),
                         cud.EXIT_OBSERVER_FAILURE)
        capped = cud._new_result(
            cud.FORWARD_TOTAL_BYTES, cud.FORWARD_LINE_CHARS)
        capped.update(base, drain_truncated=True, forward_truncated=True)
        self.assertEqual(cud._final_status(capped, None), cud.STATUS_OK)
        deadline = cud._new_result(
            cud.FORWARD_TOTAL_BYTES, cud.FORWARD_LINE_CHARS)
        deadline.update(base, drain_refused=True)
        self.assertEqual(cud._final_status(deadline, "deadline"),
                         cud.STATUS_TIMEOUT)
        unproven = cud._new_result(
            cud.FORWARD_TOTAL_BYTES, cud.FORWARD_LINE_CHARS)
        unproven.update(base, cleanup="UNPROVEN", drain_refused=True)
        self.assertEqual(cud._final_status(unproven, None),
                         cud.STATUS_CLEANUP_UNPROVEN)

    def test_17_pure_summary_phase_record_and_refusal_boundary(self):
        # Process-free (no child, no pipe stall): reaches the real
        # phase-2 record serialization and the main summary-refusal
        # boundary through private seams only.
        owned = self.root

        def make_result():
            r = cud._new_result(
                cud.FORWARD_TOTAL_BYTES, cud.FORWARD_LINE_CHARS)
            r.update({"cleanup": "PROVEN", "child_exit": 0,
                      "group_state": "kill-issued",
                      "status": cud.STATUS_OK, "elapsed": 0.1,
                      "log_bytes": 10, "owned_dir": owned})
            return r

        # Run-phase record (as run_child persists before return).
        result = make_result()
        cud._write_status_record(owned, result)
        run_path = result["status_record_path"]
        self.assertTrue(os.path.isfile(run_path), result)
        self.assertEqual(result["status_record_bytes"],
                         os.lstat(run_path).st_size)
        # Forwarded summary phase: bounded display, no phase record.
        out = bytearray()
        self.assertIsNone(cud._summary_phase(result, out.extend))
        self.assertEqual(result["summary_display"], "forwarded")
        self.assertIn(b"ci-unit-diagnostics status=OK", bytes(out))
        # Refusal boundary: distinct exclusive record with the exact
        # persisted nonzero outcome and truthful run-record metadata.
        result["summary_display"] = None

        def stall(chunk):
            raise cud._SinkRefused("test-stall")

        self.assertEqual(cud._summary_phase(result, stall),
                         cud.EXIT_OBSERVER_FAILURE)
        self.assertEqual(result["summary_display"], "refused")
        phase_path = result["summary_record_path"]
        self.assertTrue(os.path.isfile(phase_path), result)
        data = json.loads(open(phase_path).read())
        self.assertEqual(data["summary_display"], "refused")
        self.assertEqual(data["exit_code"], cud.EXIT_OBSERVER_FAILURE)
        self.assertEqual(data["run_status"], cud.STATUS_OK)
        self.assertEqual(data["summary_status"], "refused")
        self.assertEqual(data["run_record_path"], run_path)
        self.assertEqual(data["run_record_bytes"],
                         os.lstat(run_path).st_size)
        # Exclusive fixed name: a second refusal must not overwrite
        # the phase record and must claim nothing new.
        self.assertEqual(cud._summary_phase(result, stall),
                         cud.EXIT_OBSERVER_FAILURE)
        self.assertIsNone(result["summary_record_path"])
        self.assertEqual(json.loads(open(phase_path).read())[
            "summary_display"], "refused")


    def test_18_post_teardown_only_sink_refusal_real_child(self):
        # K22 post-teardown-only integration: one real stdlib child
        # (short line, no terminating LF, so its single display piece
        # exists only after finish(), i.e. only in the drain), a real
        # bounded teardown, then the test's own sink refuses the
        # drain's first piece offer. break_reason stays None; the
        # honest outcome is drain_refused -> OBSERVER_FAILURE (126);
        # the child is reaped and the raw log preserved. No fake
        # process, no new thread, no hostscan: the refusal is the
        # test's own sink object (observational seam), not a fake fd
        # or mocked status.
        offered = {"n": 0}

        def refusing_sink(chunk):
            offered["n"] += 1
            raise cud._SinkRefused("post-teardown probe refusal")

        result, _ = _run_case(
            _child("import sys\n"
                   "sys.stdout.write('Z' * 16)\n"
                   "sys.stdout.flush()\n"),
            self.root, sink=refusing_sink)
        self.assertEqual(offered["n"], 1, result)
        self.assertEqual(result["status"],
                         cud.STATUS_OBSERVER_FAILURE, result)
        self.assertEqual(cud.exit_code_for(result),
                         cud.EXIT_OBSERVER_FAILURE, result)
        self.assertTrue(result["drain_refused"], result)
        # T24: the post-drain _SinkRefused handler intentionally
        # charges forward_refused as well (queued/attempted labeled
        # bytes, not delivered success); the exact refusal reason and
        # stop offset are the causal metadata. terminated_by None
        # (asserted below) is what proves break_reason None / no
        # monitor failure.
        self.assertTrue(result["forward_refused"], result)
        self.assertEqual(result["forward_refusal_reason"],
                         "post-teardown probe refusal", result)
        self.assertEqual(result["forward_stopped_at_log_offset"], 16,
                         result)
        self.assertEqual(result["cleanup"], "PROVEN", result)
        self.assertEqual(result["child_exit"], 0, result)
        self.assertIsNone(result["terminated_by"], result)
        self.assertEqual(result["forwarded_bytes"],
                         len(cud.LABEL) + 17, result)
        self.assertTrue(_pid_gone(result["direct_pid"]), result)
        self.assertEqual(os.lstat(result["log_path"]).st_size, 16,
                         result)

    def test_19_prelaunch_sink_unavailable_private_record_no_popen(self):
        # K21 conditional diagnostic gap (process-free, ZERO Popen
        # attempts): stdout fileno unavailable BUT a safe RUNNER_TEMP
        # is available -> bounded private evidence preparation before
        # the sink-refusal return: owned 0700 dir + 0600 status
        # record, truthful PREREQUISITE/sink-unavailable, no child.
        # The Popen guard proves no launch attempt. Missing/unsafe
        # temp stays honest no-artifact (tests 8-9). Not an fsync /
        # power-loss / OS immunity promise.
        real_stdout = sys.stdout
        real_popen = cud.subprocess.Popen
        guard = {"called": 0}

        class _NoFileno:
            def fileno(self):
                raise OSError("stdout fileno unavailable (probe)")

        def _guard(*args, **kwargs):
            guard["called"] += 1
            raise AssertionError("Popen attempted in prelaunch case")

        sys.stdout = _NoFileno()
        cud.subprocess.Popen = _guard
        try:
            result = cud.run_child(_child("import sys; sys.exit(0)"),
                                   temp_root=self.root, deadline_s=5.0,
                                   kill_grace_s=1.0, post_kill_s=1.0,
                                   post_drain_s=1.0)
        finally:
            sys.stdout = real_stdout
            cud.subprocess.Popen = real_popen
        self.assertEqual(guard["called"], 0,
                         "no Popen attempt is a prelaunch invariant")
        self.assertEqual(result["status"], cud.STATUS_PREREQUISITE,
                         result)
        self.assertEqual(result["terminated_by"], "sink-unavailable",
                         result)
        self.assertIsNone(result["direct_pid"], result)
        self.assertEqual(cud.exit_code_for(result),
                         cud.EXIT_PREREQUISITE)
        self.assertLess(result["elapsed"], 5.0)
        # The bounded private evidence record exists exactly once.
        owned = [d for d in os.listdir(self.root)
                 if d.startswith("ci-unit-diag-")
                 and os.path.isdir(os.path.join(self.root, d))]
        self.assertEqual(len(owned), 1, os.listdir(self.root))
        rec = os.path.join(self.root, owned[0], "diagnostic-status.json")
        self.assertEqual(os.lstat(rec).st_mode & 0o777, 0o600)
        data = json.loads(open(rec).read())
        self.assertEqual(data["status"], cud.STATUS_PREREQUISITE)
        self.assertEqual(data["terminated_by"], "sink-unavailable")
        self.assertIsNone(data["direct_pid"])
        self.assertEqual(result["status_record_path"], rec)
        self.assertEqual(result["status_record_bytes"],
                         os.lstat(rec).st_size)


    def test_20_exit_137_vs_direct_sigkill_wait_results(self):
        # Order 009-r bounded synthetic OAP check: a positive exit
        # 137 (the hosted wrapper exit code) and a real direct
        # SIGKILL have DISTINCT owned wait results - 137 stays an
        # exact normal exit (child_signal None, status OK, exit 137
        # preserved); the self-issued SIGKILL is the separate
        # child-signal field (child_exit None, status CHILD_SIGNALED,
        # exit 131), never a 128-addition. The SIGKILL child
        # installs a SIGTERM marker handler BEFORE its self-kill:
        # the marker is never written, proving the identity-verified
        # owned group sweep signalled no live process outside the
        # child's own self-kill (an unowned process is never
        # signalled).
        log137 = self._owned_log("exit137.log")
        result137, _ = _run_case(
            _child("import sys\n"
                   "sys.exit(137)\n"),
            self.root, log_path=log137)
        self.assertEqual(result137["status"], cud.STATUS_OK)
        self.assertEqual(result137["child_exit"], 137)
        self.assertIsNone(result137["child_signal"])
        self.assertEqual(cud.exit_code_for(result137), 137)
        self.assertEqual(result137["cleanup"], "PROVEN")
        self.assertEqual(result137["popen_returncode"], 137)
        log9 = self._owned_log("sigkill.log")
        marker = os.path.join(self.root, "term-marker")
        script = (
            "import os, signal, sys\n"
            "marker = sys.argv[1]\n"
            "def handler(signum, frame):\n"
            "    with open(marker, 'wb') as f:\n"
            "        f.write(b'term')\n"
            "signal.signal(signal.SIGTERM, handler)\n"
            "os.kill(os.getpid(), signal.SIGKILL)\n"
        )
        result9, _ = _run_case(
            [sys.executable, "-c", script, marker],
            self.root, log_path=log9)
        self.assertEqual(result9["status"], cud.STATUS_CHILD_SIGNALED)
        self.assertIsNone(result9["child_exit"])
        self.assertEqual(result9["child_signal"], signal.SIGKILL)
        self.assertEqual(cud.exit_code_for(result9),
                         cud.EXIT_CHILD_SIGNALED)
        self.assertEqual(result9["cleanup"], "PROVEN")
        self.assertEqual(result9["popen_returncode"], -signal.SIGKILL)
        self.assertFalse(os.path.exists(marker))
        # The two wait results are genuinely distinct.
        self.assertNotEqual(
            (result137["child_exit"], result137["child_signal"]),
            (result9["child_exit"], result9["child_signal"]))
        self.assertNotEqual((137, None), (None, signal.SIGKILL))

    def test_21_direct_launch_projection_and_clean_refusal(self):
        # Order 009-r main-only projection: the exact direct console
        # argv/env and the clean prelaunch refusal when the fixed
        # installed console (or its local environment) is missing.
        # Process-free (no child, no launch).
        root = os.path.join(self.root, "proj-root")
        venv = os.path.join(root, ".venv")
        bin_dir = os.path.join(venv, "bin")
        os.makedirs(bin_dir)
        with open(os.path.join(venv, "pyvenv.cfg"), "wb") as f:
            f.write(b"home = /usr/bin\nversion_info = 3.12.1\n")
        interpreter = os.path.join(bin_dir, "python")
        with open(interpreter, "wb") as f:
            f.write(b"")
        os.chmod(interpreter, 0o755)
        console = os.path.join(bin_dir, "pytest")

        def valid_console():
            with open(console, "wb") as f:
                f.write(b"#!" + interpreter.encode("ascii")
                        + b"\n"
                        + b"# -*- coding: utf-8 -*-\n")
            os.chmod(console, 0o755)

        valid_console()
        sentinel = "oap-projection-sentinel-009r"
        old_sentinel = os.environ.get(sentinel)
        os.environ[sentinel] = "kept"
        try:
            projection = cud.direct_launch_projection(root)
            self.assertIsNotNone(projection, "valid projection refused")
            argv, env = projection
            self.assertEqual(
                argv, [console, "tests/unit", "-o", "addopts=",
                       "-vv", "-o", "faulthandler_timeout=60"])
            self.assertEqual(env["VIRTUAL_ENV"], venv)
            inherited_path = os.environ.get("PATH", "")
            self.assertEqual(
                env["PATH"],
                (bin_dir + os.pathsep + inherited_path
                 if inherited_path else bin_dir))
            self.assertEqual(env[sentinel], "kept")
            # Inherited environment otherwise unchanged.
            for key, value in os.environ.items():
                if key in ("VIRTUAL_ENV", "PATH"):
                    continue
                self.assertEqual(env[key], value)
        finally:
            if old_sentinel is None:
                os.environ.pop(sentinel, None)
            else:
                os.environ[sentinel] = old_sentinel
        # Clean refusal: the fixed installed console missing...
        os.unlink(console)
        self.assertIsNone(cud.direct_launch_projection(root))
        # ...or non-executable...
        valid_console()
        os.chmod(console, 0o644)
        self.assertIsNone(cud.direct_launch_projection(root))
        # ...or an external shebang interpreter ("env python")...
        valid_console()
        with open(console, "wb") as f:
            f.write(b"#!/usr/bin/env python\n")
        os.chmod(console, 0o755)
        self.assertIsNone(cud.direct_launch_projection(root))
        # ...or an absolute shebang outside the local venv bin...
        with open(console, "wb") as f:
            f.write(b"#!/usr/bin/python3\n")
        os.chmod(console, 0o755)
        self.assertIsNone(cud.direct_launch_projection(root))
        # ...or no shebang at all...
        with open(console, "wb") as f:
            f.write(b"import sys\n")
        os.chmod(console, 0o755)
        self.assertIsNone(cud.direct_launch_projection(root))
        # ...or a non-ASCII shebang byte...
        with open(console, "wb") as f:
            f.write(b"#!" + interpreter.encode("ascii") + b"\xff\n")
        os.chmod(console, 0o755)
        self.assertIsNone(cud.direct_launch_projection(root))
        # ...or a missing interpreter...
        valid_console()
        os.unlink(interpreter)
        self.assertIsNone(cud.direct_launch_projection(root))
        # ...or a missing pyvenv.cfg...
        with open(interpreter, "wb") as f:
            f.write(b"")
        os.chmod(interpreter, 0o755)
        os.unlink(os.path.join(venv, "pyvenv.cfg"))
        self.assertIsNone(cud.direct_launch_projection(root))
        # ...or a symlinked (non-local) venv...
        with open(os.path.join(venv, "pyvenv.cfg"), "wb") as f:
            f.write(b"home = /usr/bin\n")
        os.rename(venv, venv + "-real")
        os.symlink(venv + "-real", venv)
        self.assertIsNone(cud.direct_launch_projection(root))
        os.unlink(venv)
        os.rename(venv + "-real", venv)

if __name__ == "__main__":
    unittest.main()
