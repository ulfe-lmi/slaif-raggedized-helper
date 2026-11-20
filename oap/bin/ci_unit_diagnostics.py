#!/usr/bin/env python3
"""Owned CI unit-diagnostics supervisor (order 009-k; private, stdlib only).

Makes the whole-unit CI run observable without giving test children the
GitHub runner output pipe:

* the direct child (the fixed production command) writes stdout/stderr to
  an exclusive 0600 regular diagnostic log inside a private 0700 directory
  under RUNNER_TEMP; stdin is DEVNULL; close_fds and a new session; no
  PIPE and no inherited runner output stream. The parent reads the same
  file through its OWN read descriptor (independent offset), so the
  private log always retains the raw child bytes;
* the parent alone forwards finite regular-file reads: bounded 64 KiB
  chunks, at most one chunk per monitor iteration with a bounded number
  of labeled pieces and a deadline check between pieces; the display is
  escaped (every '#' percent-escaped so no legacy action-command
  introducer survives anywhere in a line, CR folded to LF so no emitted
  line can start from raw child bytes, C0/DEL controls escaped, stateful
  incremental UTF-8 decode with replacement so partial multi-byte
  sequences across chunk boundaries cannot corrupt job output); 4 MiB
  total forward cap and 4,096-byte piece payloads; the job-stdout channel
  is written through a finite wall/byte backpressure writer (select +
  os.write with per-write and total wall budgets; no open-file-flag
  mutation of the shared channel); on channel refusal the forwarding
  offset is recorded and the run fails honestly as OBSERVER_FAILURE;
  there is no whole-file read, no output-EOF wait and no unbounded line
  accumulation;
* the parent enforces a monotonic 180 s child deadline. On EVERY
  post-launch exit (normal, nonzero, deadline, oversize, observer,
  interrupt, supervisor error) the bounded owned teardown runs FIRST and
  finishes all group-signal/escalation decisions while the unreaped
  leader holds its identity: identity-verified TERM to the owned initial
  group, the 10 s grace, then the bounded KILL sweep (survivor state is
  unobservable without a forbidden host scan, so the sweep is issued and
  labeled, not claimed), ONE shared absolute 5 s post-KILL observation
  budget, and only then the single bounded reap. A recycled PID/PGID is
  never signalled; a child that re-sessions itself fails closed as
  GROUP_UNPROVEN. The raw log and its private 0700 directory are
  PRESERVED (never deleted by this utility), and a best-effort separate
  private status record (0600, same directory) holds the full result
  including any incomplete-forwarding offset;
* after the bounded teardown, the remaining log bytes get a finite
  SEPARATE post-drain budget (5 s) through the same backpressured
  channel;
* the actual child exit status (including pytest 5) is preserved exactly
  (named CLD_EXITED decoding); a signalled child is reported via a
  separate child-signal field, never by adding 128 to a normal exit;
  only a complete zero command with proven supervisor teardown returns
  0; a finite own status summary is emitted even when test output is
  unavailable;
* production ``main`` installs scoped NONRAISING latched SIGTERM/SIGINT
  handlers only while the run is active (no import-time mutation; no
  locks, I/O or teardown in the handlers); the monitor observes the
  latch, the owned teardown completes, the run returns
  OBSERVER_FAILURE (terminated_by="interrupted") and the previous
  handlers are restored. This is not SIGKILL/crash/OS-blocking immunity;
  private caller BaseException paths still perform owned teardown.

Order 009-r (main only): the fixed production command is now the
repository's own installed pytest console entrypoint
(``<root>/.venv/bin/pytest``) with the unchanged trailing suite args,
supervised directly - the uv wrapper is no longer invoked. The
prelaunch projection (direct_launch_projection) requires the fixed
installed console (real regular executable file), an interpreter
shebang inside that same local venv bin, a real local venv
(pyvenv.cfg) and a real bin directory; any absence fails closed with
EXIT_PREREQUISITE before any child exists. The child environment is
the inherited environment plus the repo .venv VIRTUAL_ENV and its bin
as the first PATH entry; no new uv operation, shell, argv override or
fallback. run_child receives this explicit argv and environment and
keeps every resource execution/ownership behavior unchanged. A
bounded optional own-cgroup observation (oap/bin/ci_unit_resources.py)
snapshots the supervisor's own cgroup event counters immediately
before launch and after the owned teardown, and records the
inherited prelaunch RLIMIT_CPU soft/hard; only a fixed-length numeric
fragment is appended to the existing bounded final summary, and
observation availability or any delta never determines child status,
acceptance, or which member failed.

Exit codes: 0 (child zero + proven teardown), the child's exact nonzero
exit code (preserved), 124 TIMEOUT, 125 CLEANUP_UNPROVEN, 126
OBSERVER_FAILURE, 127 LOG_FAILURE, 128 OVERSIZE, 129 PREREQUISITE, 130
LAUNCH_FAILURE, 131 CHILD_SIGNALED, 132 GROUP_UNPROVEN. (A child that
itself exits with a code in 124-132 on a clean completion is passed
through unchanged and is indistinguishable from the same supervisor
code; documented accepted ambiguity.)

No shell command construction, no public arbitrary-command CLI, no
environment dump, no new dependency, no rlimit change, no artifact
upload, no network.

Honest limits: this is not proof of the historical CI cancellation cause
(output ownership is a hypothesis only), not a write-rate/host-disk
certificate, not OOM/allocation accounting and not universal descendant
containment - a descendant that creates its own session escapes the
owned group and is neither signalled nor reaped here. Group signal scope
is direct-reap plus issued group TERM/KILL: the owned leader's death is
proven when cleanup=PROVEN; initial-group survivor death is NOT claimed
(no host scan, no adoption, no emptiness theorem). A persistently
blocking job-stdout channel is handled by bounded backpressure plus
honest OBSERVER_FAILURE; kernel I/O inside a single os.write call is not
universally parent-bounded, and no hard parent/host guarantee is
claimed.

The private ``run_child`` function accepts explicit synthetic argv and
short synthetic bounds (for its own unittest cases only, via
log_path/read_hook/extra_fds/sink/interrupt_check/budget seams); the
production defaults and the exclusive 0700/0600 generated log path
cannot be changed by caller environment or CLI - ``main`` always uses
the generated exclusive log and the fixed production command.
"""
from __future__ import annotations

import codecs
import json
import os
import select
import signal
import stat
import subprocess
import sys
import tempfile
import time

try:
    # Optional bounded own-cgroup observation (order 009-r),
    # co-shipped in this same directory; its absence degrades the
    # summary fragment to unavailable, never the run.
    import ci_unit_resources as _ci_unit_resources
except ImportError:
    _ci_unit_resources = None

# Order 009-r: main supervises the repo's own installed pytest console
# entrypoint directly (absolute fixed path <root>/.venv/bin/pytest,
# validated by direct_launch_projection before any child exists); the
# trailing suite args are unchanged from the 009-k uv wrapper, and the
# uv wrapper itself is no longer invoked.
TEST_SUITE_ARGS = (
    "tests/unit", "-o", "addopts=", "-vv",
    "-o", "faulthandler_timeout=60",
)
VENV_RELPATH = ".venv"
BIN_RELPATH = "bin"
CONSOLE_RELPATH = "pytest"
SHEBANG_READ_BYTES = 4096
PRODUCTION_DEADLINE_S = 180.0
PRODUCTION_KILL_GRACE_S = 10.0
POST_KILL_OBSERVE_S = 5.0
POST_DRAIN_S = 5.0
FORWARD_TOTAL_BYTES = 4 * 1024 * 1024
FORWARD_CHUNK_BYTES = 64 * 1024
FORWARD_LINE_CHARS = 4096
LOG_LIMIT_BYTES = 16 * 1024 * 1024
POLL_S = 0.05
WRITE_POLL_S = 0.5
WRITE_BUDGET_S = 2.0
FORWARD_WALL_BUDGET_S = 10.0
WRITE_STEP_BYTES = 4096
TIME_BINARY = "/usr/bin/time"
LABEL = b"ci-unit-output| "
TOTAL_CAP_MARK = (
    b"\nci-unit-output| [forward total cap reached; remainder held in "
    b"private log only]\n"
)
GROUP_SCOPE_LABEL = (
    "direct-reap + identity-verified group TERM/KILL sweep; leader death "
    "proven when cleanup=PROVEN; initial-group survivor death not "
    "claimed (no host scan, no adoption)"
)

STATUS_OK = "OK"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_OVERSIZE = "OVERSIZE"
STATUS_OBSERVER_FAILURE = "OBSERVER_FAILURE"
STATUS_CLEANUP_UNPROVEN = "CLEANUP_UNPROVEN"
STATUS_LOG_FAILURE = "LOG_FAILURE"
STATUS_LAUNCH_FAILURE = "LAUNCH_FAILURE"
STATUS_PREREQUISITE = "PREREQUISITE"
STATUS_CHILD_SIGNALED = "CHILD_SIGNALED"
STATUS_GROUP_UNPROVEN = "GROUP_UNPROVEN"

EXIT_TIMEOUT = 124
EXIT_CLEANUP_UNPROVEN = 125
EXIT_OBSERVER_FAILURE = 126
EXIT_LOG_FAILURE = 127
EXIT_OVERSIZE = 128
EXIT_PREREQUISITE = 129
EXIT_LAUNCH_FAILURE = 130
EXIT_CHILD_SIGNALED = 131
EXIT_GROUP_UNPROVEN = 132

_EXIT_BY_STATUS = {
    STATUS_TIMEOUT: EXIT_TIMEOUT,
    STATUS_CLEANUP_UNPROVEN: EXIT_CLEANUP_UNPROVEN,
    STATUS_OBSERVER_FAILURE: EXIT_OBSERVER_FAILURE,
    STATUS_LOG_FAILURE: EXIT_LOG_FAILURE,
    STATUS_OVERSIZE: EXIT_OVERSIZE,
    STATUS_PREREQUISITE: EXIT_PREREQUISITE,
    STATUS_LAUNCH_FAILURE: EXIT_LAUNCH_FAILURE,
    STATUS_CHILD_SIGNALED: EXIT_CHILD_SIGNALED,
    STATUS_GROUP_UNPROVEN: EXIT_GROUP_UNPROVEN,
}


class _LogFailure(Exception):
    """Owned diagnostic log cannot be opened/created/verified safely."""


class _SinkRefused(Exception):
    """Backpressured display channel did not drain within its budgets
    (or the channel errored); forwarding stops and the run fails
    honestly."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _new_result(forward_total, forward_line_chars):
    return {
        "status": STATUS_OK,
        "child_exit": None,
        "child_signal": None,
        "direct_pid": None,
        "terminated_by": None,
        "elapsed": None,
        "forwarded_bytes": 0,
        "forward_truncated": False,
        "forward_refused": False,
        "forward_refusal_reason": None,
        "forward_stopped_at_log_offset": None,
        "drain_truncated": False,
        "drain_refused": False,
        "log_bytes": None,
        "log_path": None,
        "owned_dir": None,
        "status_record_path": None,
        "status_record_bytes": None,
        "summary_display": None,
        "summary_record_path": None,
        "summary_record_bytes": None,
        "popen_returncode": None,
        "cleanup": "NOT_APPLICABLE",
        "group_state": "not-started",
        "group_term_issued": False,
        "group_kill_issued": False,
        "group_scope": GROUP_SCOPE_LABEL,
        "cap": forward_total,
        "line_chars": forward_line_chars,
        "_teardown_done": False,
    }


def _backpressured_writer(fd, write_poll_s=WRITE_POLL_S,
                          write_budget_s=WRITE_BUDGET_S,
                          wall_budget_s=FORWARD_WALL_BUDGET_S):
    """Finite wall/byte/chunk backpressure on the actual channel fd.

    select() + os.write() only, in bounded steps: the fd's open-file
    flags are never mutated (no shared-stdout flag leak) and nothing is
    dup'd or closed here. Raises _SinkRefused when the channel does not
    drain within the per-write wall budget, the total forwarding wall
    budget, or on channel error. One in-flight os.write of a bounded
    step is the only kernel I/O; it is not universally parent-bounded
    (documented honest limit)."""
    state = {"wall": 0.0}

    def writer(chunk):
        if not chunk:
            return
        if state["wall"] >= wall_budget_s:
            raise _SinkRefused("forward-wall-budget")
        data = bytes(chunk)
        write_deadline = time.monotonic() + write_budget_s
        while data:
            if time.monotonic() >= write_deadline:
                raise _SinkRefused("write-budget")
            if state["wall"] >= wall_budget_s:
                raise _SinkRefused("forward-wall-budget")
            started = time.monotonic()
            try:
                _, writable, _ = select.select([], [fd], [], write_poll_s)
            except OSError:
                raise _SinkRefused("select-failed")
            written = 0
            if writable:
                step = data[:WRITE_STEP_BYTES]
                try:
                    written = os.write(fd, step)
                except (BlockingIOError, InterruptedError):
                    written = 0
                except OSError:
                    raise _SinkRefused("write-failed")
            state["wall"] += time.monotonic() - started
            data = data[written:]

    return writer


def _escape_display_text(text):
    """Escape display text: '#' -> %23 (neutralizes legacy
    action-command introducers anywhere in a line), C0 controls (except
    LF and TAB) and DEL -> \\xNN. Newlines are handled by the caller.
    Emitted display lines always start with the fixed LABEL, so the
    new-style (line-leading) introducer can never arise from raw child
    bytes, including CR-folded line starts."""
    out = []
    for ch in text:
        o = ord(ch)
        if ch == "\n" or ch == "\t":
            out.append(ch)
        elif ch == "#":
            out.append("%23")
        elif o < 0x20 or o == 0x7F:
            out.append("\\x%02x" % o)
        else:
            out.append(ch)
    return "".join(out)


class _Forwarder:
    """Stateful bounded display forwarder.

    raw log bytes -> stateful incremental UTF-8 decode (errors=replace;
    partial multi-byte sequences held across chunk boundaries) -> CR
    fold (CRLF/CR -> LF; a trailing CR held across the boundary) ->
    escape/control-normalize -> labeled pieces of <= seg_bytes payload.
    Decoder state, pending CR, residual line and piece queue persist
    across chunk and segment boundaries. The raw log is untouched."""

    def __init__(self, cap, seg_bytes):
        self.cap = cap
        self.seg_bytes = seg_bytes
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._pending_cr = False
        self._line = []
        self._line_bytes = 0
        self._pieces = []
        self.forwarded = 0
        self.truncated = False
        self.refused = False
        self.stop_offset = None
        self.offer_offset = 0
        self._finished = False

    def offer(self, raw):
        if self.truncated or self.refused:
            return
        self.offer_offset += len(raw)
        text = self.decoder.decode(raw)
        text = self._cr_fold(text)
        for ch in _escape_display_text(text):
            self._append(ch)

    def _cr_fold(self, text):
        if self._pending_cr:
            if text.startswith("\n"):
                # Split CRLF across chunks: the held CR plus this LF
                # is ONE line break; emit it exactly once.
                text = "\n" + text[1:]
            else:
                text = "\n" + text
            self._pending_cr = False
        trailing = text.endswith("\r")
        body = text[:-1] if trailing else text
        out = []
        i = 0
        while i < len(body):
            c = body[i]
            if c == "\r":
                out.append("\n")
                i += 1
                if i < len(body) and body[i] == "\n":
                    i += 1
            else:
                out.append(c)
                i += 1
        if trailing:
            self._pending_cr = True
        return "".join(out)

    def _append(self, ch):
        if ch == "\n":
            self._emit_line("".join(self._line))
            self._line = []
            self._line_bytes = 0
            return
        self._line.append(ch)
        self._line_bytes += len(ch.encode("utf-8"))
        if self._line_bytes > self.seg_bytes:
            self._emit_line("".join(self._line))
            self._line = []
            self._line_bytes = 0

    def _emit_line(self, payload):
        """Emit one child line (without its terminating LF) as labeled
        pieces of at most seg_bytes encoded payload each."""
        n = len(payload)
        if n == 0:
            self._push_piece(LABEL + b"\n")
            return
        i = 0
        while i < n:
            j = i
            b = 0
            while j < n:
                cb = len(payload[j].encode("utf-8"))
                if b + cb > self.seg_bytes:
                    break
                b += cb
                j += 1
            if j == i:
                j = i + 1
            self._push_piece(LABEL + payload[i:j].encode("utf-8") + b"\n")
            i = j

    def _push_piece(self, piece):
        if self.truncated or self.refused:
            return
        if self.forwarded + len(piece) > self.cap:
            self.truncated = True
            self.stop_offset = self.offer_offset
            if self.forwarded + len(TOTAL_CAP_MARK) <= self.cap:
                self._pieces.append(TOTAL_CAP_MARK)
                self.forwarded += len(TOTAL_CAP_MARK)
            return
        self._pieces.append(piece)
        self.forwarded += len(piece)

    def take_piece(self):
        if not self._pieces:
            return None
        return self._pieces.pop(0)

    def has_piece(self):
        return bool(self._pieces)

    def finish(self):
        """Flush decoder residual, pending CR and residual line into
        bounded pieces (called once, after the child is torn down)."""
        if self._finished or self.truncated or self.refused:
            return
        self._finished = True
        text = self.decoder.decode(b"", True)
        text = self._cr_fold(text)
        for ch in _escape_display_text(text):
            self._append(ch)
        if self._pending_cr:
            self._pending_cr = False
            self._emit_line("")
        if self._line:
            self._emit_line("".join(self._line))
            self._line = []
            self._line_bytes = 0


def _temp_root_ok(temp_root):
    """Fail loudly (None) on a missing/unsafe owned temp prerequisite."""
    try:
        st = os.lstat(temp_root)
    except (OSError, TypeError):
        return None
    if not stat.S_ISDIR(st.st_mode):
        return None
    if not os.access(temp_root, os.W_OK):
        return None
    return st


def _open_owned_log(temp_root, explicit_path):
    """Return (write_fd, path, owned_dir); no fd may leak on failure.

    Generated (production) path: private 0700 directory (mkdtemp),
    exclusive O_EXCL 0600 regular log; the HELD descriptor is fchmod'ed
    and fstat-verified (S_ISREG). Explicit path (private test seam
    only): O_NOFOLLOW open plus fstat verification of the held
    descriptor; never a symlink, never non-regular. A construction
    failure before any child exists leaves at most an empty private
    directory (runner-reclaimed); nothing is deleted after a child has
    been launched (raw evidence is preserved).
    """
    if explicit_path is not None:
        fd = os.open(explicit_path, os.O_WRONLY | os.O_NOFOLLOW)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise _LogFailure("explicit log not a regular file")
            os.fchmod(fd, 0o600)
        except BaseException:
            os.close(fd)
            raise
        return fd, explicit_path, None
    owned_dir = tempfile.mkdtemp(prefix="ci-unit-diag-", dir=temp_root)
    path = os.path.join(owned_dir, "unit-diagnostic.log")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600)
    try:
        os.fchmod(fd, 0o600)
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise _LogFailure("generated log not a regular file")
    except BaseException:
        os.close(fd)
        raise
    return fd, path, owned_dir


def _decode_termination(status):
    """Return (exit_code, signal_number) from an observed waitid status.
    A normal exit keeps its EXACT code (0/7/5) via the named
    os.CLD_EXITED; a signalled termination is represented separately -
    never by 128-addition to a normal exit."""
    if status is None:
        return None, None
    if status.si_code == os.CLD_EXITED:
        return status.si_status, None
    if status.si_code in (os.CLD_KILLED, os.CLD_DUMPED):
        return None, status.si_status
    return None, None


def _wait_exited_until(pid, end):
    """Observe direct-child termination via waitid(WNOWAIT) until the
    given absolute deadline; never reaps and never reuses the numeric
    identity."""
    while True:
        try:
            st = os.waitid(os.P_PID, pid,
                           os.WEXITED | os.WNOHANG | os.WNOWAIT)
        except ChildProcessError:
            return None
        if st is not None:
            return st
        if time.monotonic() >= end:
            return None
        time.sleep(POLL_S)


def _reap(pid):
    """Single ownership-safe reap, only after all group-signal decisions
    have finished and termination was observed."""
    try:
        return os.waitid(os.P_PID, pid, os.WEXITED)
    except ChildProcessError:
        return None


def _group_identity_ok(pid):
    try:
        return (os.getpgid(pid) == pid and os.getsid(pid) == pid)
    except OSError:
        return False


def _group_signal(pid, sig):
    """One explicit signal decision to the identity-verified owned
    initial group; each return is an issued/failed observation, never
    an all-descendant certificate. 'issued': killpg accepted for the
    PGID. 'resolved': killpg observed no process in that PGID at this
    instant - a point observation of the initial group only: a member
    that re-sessioned, or any process outside the group, is outside
    this observation's scope, and nothing is certified about
    descendants beyond it. 'unproven': identity lost / unexpected
    error - fail closed; a recycled PID/PGID is never signalled."""
    if not _group_identity_ok(pid):
        return "unproven"
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        return "resolved"
    except OSError:
        return "unproven"
    return "issued"


def _teardown_owned(child, result, terminal, kill_grace_s, post_kill_s):
    """Owned teardown on ALL post-launch exits (idempotent, never
    raises, never deletes the raw log). The group-signal/escalation
    decisions are finished while the unreaped leader holds its identity;
    the single bounded reap is last. Survivor state is unobservable
    without a forbidden host scan, so the bounded KILL sweep is issued
    on every path and labeled (GROUP_SCOPE_LABEL), not claimed. The
    post-KILL observation uses ONE shared absolute budget."""
    if child is None or result.get("_teardown_done"):
        return
    if result.get("_teardown_attempted"):
        # Single-attempt semantics: the first pass owns the group
        # decisions, its absolute grace/post-KILL windows and the
        # single bounded reap. A reentry on a later error path must
        # not reissue signals or start fresh budgets; the first
        # pass's UNPROVEN record (if any) is preserved as-is and
        # never re-graded into success.
        return
    result["_teardown_attempted"] = True
    pid = child.pid
    result["cleanup"] = "UNPROVEN"
    try:
        group = _group_signal(pid, signal.SIGTERM)
        result["group_state"] = group
        result["group_term_issued"] = group == "issued"
        if terminal is None:
            terminal = _wait_exited_until(
                pid, time.monotonic() + kill_grace_s)
        else:
            # Terminal leader: the grace window still bounds the group
            # sweep decision before the identity is released.
            time.sleep(kill_grace_s)
        escalation = _group_signal(pid, signal.SIGKILL)
        if escalation == "issued":
            result["group_kill_issued"] = True
            if result["group_state"] != "unproven":
                result["group_state"] = "kill-issued"
        elif escalation == "resolved":
            if result["group_state"] != "unproven":
                result["group_state"] = "resolved"
        else:
            result["group_state"] = "unproven"
        if terminal is None:
            terminal = _wait_exited_until(
                pid, time.monotonic() + post_kill_s)
        if terminal is None:
            return  # unresolved termination: stays UNPROVEN, no reap
        final = _reap(pid)
        if final is None:
            return  # failed reap: stays UNPROVEN, honest
        result["cleanup"] = "PROVEN"
        result["child_exit"], result["child_signal"] = \
            _decode_termination(final)
        # K17: reconcile the owned Popen object with the ACTUAL
        # observed manual-reap result (stdlib convention: exit N ->
        # N, signal N -> -N) so the stdlib destructor/internal_poll
        # performs no further numeric waitpid after identity release.
        # Unknown si_code or unproven paths never set it (no invented
        # 0/success; those stay honest via the nonzero statuses).
        if result["child_exit"] is not None:
            child.returncode = result["child_exit"]
        elif result["child_signal"] is not None:
            child.returncode = -result["child_signal"]
        result["popen_returncode"] = child.returncode
        result["_teardown_done"] = True
    except BaseException:
        result["cleanup"] = "UNPROVEN"
        if result["group_state"] == "not-started":
            result["group_state"] = "unproven"


def _final_status(result, break_reason):
    """Fixed precedence: group uncertainty and cleanup refusal stay
    nonzero; a later break_reason mapping can never convert an unproven
    cleanup into ordinary child success."""
    if result["group_state"] == "unproven":
        return STATUS_GROUP_UNPROVEN
    if result["cleanup"] != "PROVEN":
        return STATUS_CLEANUP_UNPROVEN
    if break_reason == "deadline":
        return STATUS_TIMEOUT
    if break_reason == "oversize":
        return STATUS_OVERSIZE
    if break_reason in ("observer", "interrupted"):
        return STATUS_OBSERVER_FAILURE
    if result.get("drain_refused"):
        # Post-teardown drain refused the remaining output: an honest
        # observer failure - distinct from intentional cap truncation
        # (forward_truncated/drain_truncated), which stays benign.
        return STATUS_OBSERVER_FAILURE
    if result["child_exit"] is None and result["child_signal"] is None:
        return STATUS_OBSERVER_FAILURE
    if result["child_exit"] is None:
        return STATUS_CHILD_SIGNALED
    return STATUS_OK


def exit_code_for(result):
    status = result["status"]
    if status == STATUS_OK:
        if result["child_exit"] is None:
            return EXIT_CLEANUP_UNPROVEN
        return result["child_exit"]
    return _EXIT_BY_STATUS[status]


def _write_status_record(owned_dir, result):
    """Best-effort separate private status record (0600, same 0700
    directory). No retry; a write failure is recorded, never fatal."""
    if owned_dir is None:
        return
    path = os.path.join(owned_dir, "diagnostic-status.json")
    fd = None
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW, 0o600)
        os.fchmod(fd, 0o600)
        payload = (json.dumps(
            {k: v for k, v in result.items() if not k.startswith("_")},
            sort_keys=True, default=str) + "\n").encode("utf-8")
        off = 0
        while off < len(payload):
            n = os.write(fd, payload[off:])
            if n <= 0:
                # Zero progress: refuse; one best-effort record, no
                # hidden retry loop.
                break
            off += n
        result["status_record_bytes"] = off
        result["status_record_path"] = (
            path if off == len(payload) else None)
    except OSError:
        result["status_record_path"] = None
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def _summary(result, deadline_s):
    exit_desc = ("none" if result["child_exit"] is None
                 else str(result["child_exit"]))
    sig_desc = ("none" if result["child_signal"] is None
                else str(result["child_signal"]))
    log_desc = ("unknown" if result["log_bytes"] is None
                else "%dB" % result["log_bytes"])
    stop_desc = ("none" if result["forward_stopped_at_log_offset"] is None
                 else "%dB" % result["forward_stopped_at_log_offset"])
    by_desc = ("none" if result["terminated_by"] is None
               else str(result["terminated_by"]))
    summary = ("ci-unit-diagnostics status=%s child_exit=%s child_signal=%s "
            "deadline=%.1fs elapsed=%.2fs forwarded=%dB/%dB truncated=%s "
            "refused=%s stop_offset=%s log_bytes=%s raw_log=exact "
            "display_decode=utf8-replace group=%s group_term=%s "
            "group_kill=%s cleanup=%s terminated_by=%s"
            % (result["status"], exit_desc, sig_desc, deadline_s,
               result["elapsed"] if result["elapsed"] is not None else 0.0,
               result["forwarded_bytes"], result["cap"],
               "yes" if result["forward_truncated"] else "no",
               "yes" if result["forward_refused"] else "no",
               stop_desc, log_desc, result["group_state"],
               "yes" if result["group_term_issued"] else "no",
               "yes" if result["group_kill_issued"] else "no",
               result["cleanup"], by_desc))
    # Order 009-r: the bounded optional own-cgroup fragment is wired
    # into THIS fixed final summary only; its availability or any
    # delta never changes the status/exit computed above.
    resource_display = result.get("resource_display")
    if resource_display:
        summary = summary + " " + resource_display
    return summary


def _write_summary_record(owned_dir, result, exit_code):
    """K18 phase-2 record: a DISTINCT fixed exclusive private record
    for the main summary phase (refusal/unavailable only). The
    run-phase record was already persisted by run_child before
    return, so this record never overwrites it and reports the run
    record's actual path/byte metadata truthfully. O_EXCL, 0600,
    bounded single write (zero-progress refuses; no retry)."""
    if owned_dir is None:
        return
    path = os.path.join(owned_dir, "diagnostic-final-summary.json")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW, 0o600)
    except OSError:
        result["summary_record_path"] = None
        return
    try:
        os.fchmod(fd, 0o600)
        summary_status = result.get("summary_display")
        payload = (json.dumps(
            {"phase": "final-summary",
             "summary_display": summary_status,
             "run_status": result.get("status"),
             "summary_status": summary_status,
             "exit_code": exit_code,
             "run_record_path": result.get("status_record_path"),
             "run_record_bytes": result.get("status_record_bytes")},
            sort_keys=True, default=str) + "\n").encode("utf-8")
        off = 0
        while off < len(payload):
            n = os.write(fd, payload[off:])
            if n <= 0:
                break
            off += n
        result["summary_record_bytes"] = off
        result["summary_record_path"] = (
            path if off == len(payload) else None)
    except OSError:
        result["summary_record_path"] = None
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def _summary_phase(result, writer):
    """K18 phase 2 (main only): bounded display of the final summary
    through the reviewed production display path. Returns None when
    forwarded; on refusal/unavailable persists the distinct
    final-summary record (exact nonzero outcome, truthful run-record
    metadata) and returns that exact nonzero exit."""
    summary = (_summary(result, PRODUCTION_DEADLINE_S) + "\n")
    try:
        writer(summary.encode("utf-8"))
    except _SinkRefused:
        result["summary_display"] = "refused"
    except (AttributeError, TypeError, OSError, ValueError):
        # Includes a None writer (channel unavailable pre-construction).
        result["summary_display"] = "unavailable"
    else:
        result["summary_display"] = "forwarded"
        return None
    _write_summary_record(result.get("owned_dir"), result,
                          EXIT_OBSERVER_FAILURE)
    return EXIT_OBSERVER_FAILURE


def run_child(argv, *, deadline_s=PRODUCTION_DEADLINE_S,
              kill_grace_s=PRODUCTION_KILL_GRACE_S,
              post_kill_s=POST_KILL_OBSERVE_S,
              post_drain_s=POST_DRAIN_S,
              forward_total=FORWARD_TOTAL_BYTES,
              forward_line_chars=FORWARD_LINE_CHARS,
              log_limit=LOG_LIMIT_BYTES,
              temp_root=None, log_path=None, read_hook=None,
              extra_fds=(), environment=None, cwd=None, sink=None,
              interrupt_check=None, post_popen_hook=None,
              write_poll_s=WRITE_POLL_S,
              write_budget_s=WRITE_BUDGET_S,
              forward_wall_s=FORWARD_WALL_BUDGET_S):
    """Run one owned child under the bounded supervisor; returns a
    result dict. Private testable entry: explicit synthetic argv and
    short synthetic bounds for its own unittest cases only. Never shells
    out; never signals or reaps anything but the owned direct child and
    its identity-verified owned initial process group."""
    started = time.monotonic()
    deadline_end = started + deadline_s
    result = _new_result(forward_total, forward_line_chars)
    reader = read_hook if read_hook is not None else os.read
    if sink is None:
        try:
            sink = _backpressured_writer(sys.stdout.fileno(),
                                         write_poll_s, write_budget_s,
                                         forward_wall_s)
        except (AttributeError, OSError, ValueError):
            result["status"] = STATUS_PREREQUISITE
            result["terminated_by"] = "sink-unavailable"
            result["elapsed"] = time.monotonic() - started
            # K21 conditional diagnostic gap: the stdout fileno is
            # unavailable BUT a safe RUNNER_TEMP (and generated owned
            # path) is available -> bounded private evidence
            # preparation (owned 0700 dir + 0600 record, best effort)
            # before the refusal return so the failure is observable
            # privately. No child is launched here; a missing/unsafe
            # temp stays honest nonzero with no artifact. Not an
            # fsync/power-loss/OS immunity promise.
            if _temp_root_ok(temp_root) is not None \
                    and log_path is None:
                try:
                    evidence_fd, evidence_log, evidence_dir = \
                        _open_owned_log(temp_root, log_path)
                except (_LogFailure, OSError):
                    evidence_fd = None
                    evidence_dir = None
                else:
                    try:
                        os.close(evidence_fd)
                    except OSError:
                        pass
                if evidence_dir is not None:
                    result["log_path"] = evidence_log
                    result["owned_dir"] = evidence_dir
                    _write_status_record(evidence_dir, result)
            return result
    forwarder = _Forwarder(forward_total, forward_line_chars)
    write_fd = None
    read_fd = None
    owned_dir = None
    log_path_resolved = None
    child = None
    break_reason = None
    terminal = None
    try:
        if _temp_root_ok(temp_root) is None:
            result["status"] = STATUS_PREREQUISITE
            result["terminated_by"] = "prerequisite"
            result["elapsed"] = time.monotonic() - started
            return result
        try:
            write_fd, log_path_resolved, owned_dir = _open_owned_log(
                temp_root, log_path)
        except (_LogFailure, OSError):
            result["status"] = STATUS_LOG_FAILURE
            result["terminated_by"] = "log-construction"
            result["elapsed"] = time.monotonic() - started
            return result
        result["log_path"] = log_path_resolved
        result["owned_dir"] = owned_dir
        env = dict(os.environ if environment is None else environment)
        env["PYTHONUNBUFFERED"] = "1"
        try:
            child = subprocess.Popen(
                list(argv), cwd=cwd, env=env,
                stdin=subprocess.DEVNULL, stdout=write_fd,
                stderr=subprocess.STDOUT, close_fds=True,
                start_new_session=True,
                pass_fds=tuple(extra_fds) if extra_fds else (),
            )
        except (OSError, ValueError):
            # The constructor did not return a PID: no ownership is
            # invented for it.
            child = None
            result["status"] = STATUS_LAUNCH_FAILURE
            result["terminated_by"] = "launch"
            result["elapsed"] = time.monotonic() - started
            return result
        # Post-launch owned-supervision region: from the successful
        # Popen assignment onward the child is KNOWN and owned; EVERY
        # post-Popen operation - direct_pid bookkeeping, owned log
        # write-fd close, monitor start - runs inside this single
        # owned cleanup boundary, so a BaseException/cancellation at
        # any point here still routes through the bounded owned
        # teardown. A constructor failure never reaches the boundary
        # (no invented PID).
        try:
            result["direct_pid"] = child.pid
            try:
                os.close(write_fd)
            except OSError:
                pass
            write_fd = None
            if post_popen_hook is not None:
                post_popen_hook(child)
            try:
                read_fd = os.open(log_path_resolved,
                                  os.O_RDONLY | os.O_NOFOLLOW)
            except OSError:
                read_fd = None
                break_reason = "observer"
            if read_fd is not None:
                while break_reason is None:
                    if interrupt_check is not None and interrupt_check():
                        break_reason = "interrupted"
                        break
                    if time.monotonic() >= deadline_end:
                        break_reason = "deadline"
                        break
                    try:
                        status = os.waitid(
                            os.P_PID, child.pid,
                            os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    except ChildProcessError:
                        break_reason = "observer"
                        break
                    if status is not None:
                        if status.si_pid == child.pid:
                            terminal = status
                        else:
                            break_reason = "observer"
                        break
                    # Bounded per-iteration forward: one chunk read,
                    # then queued pieces with a deadline check between
                    # pieces (finite per-iteration handling).
                    try:
                        chunk = reader(read_fd, FORWARD_CHUNK_BYTES)
                        if chunk:
                            forwarder.offer(chunk)
                    except Exception:
                        break_reason = "observer"
                        break
                    while forwarder.has_piece() and break_reason is None:
                        if interrupt_check is not None \
                                and interrupt_check():
                            break_reason = "interrupted"
                            break
                        if time.monotonic() >= deadline_end:
                            break_reason = "deadline"
                            break
                        piece = forwarder.take_piece()
                        try:
                            sink(piece)
                        except _SinkRefused as exc:
                            result["forward_refused"] = True
                            result["forward_refusal_reason"] = exc.reason
                            result["forward_stopped_at_log_offset"] = \
                                forwarder.offer_offset
                            break_reason = "observer"
                            break
                        except Exception:
                            break_reason = "observer"
                            break
                        result["forwarded_bytes"] = forwarder.forwarded
                    if break_reason is not None:
                        break
                    try:
                        result["log_bytes"] = os.fstat(read_fd).st_size
                    except OSError:
                        break_reason = "observer"
                        break
                    if result["log_bytes"] > log_limit:
                        break_reason = "oversize"
                        break
                    time.sleep(POLL_S)
            # R4: bounded owned teardown FIRST on every post-launch
            # exit; the remaining log bytes get a finite SEPARATE
            # post-drain budget through the same backpressured channel.
            _teardown_owned(child, result, terminal,
                            kill_grace_s, post_kill_s)
            if (break_reason is None and interrupt_check is not None
                    and interrupt_check()):
                break_reason = "interrupted"
            if read_fd is not None:
                drain_end = time.monotonic() + post_drain_s
                try:
                    while True:
                        if time.monotonic() >= drain_end:
                            result["drain_truncated"] = True
                            break
                        if forwarder.has_piece():
                            try:
                                sink(forwarder.take_piece())
                            except _SinkRefused as exc:
                                if not result["forward_refused"]:
                                    result["forward_refused"] = True
                                    result["forward_refusal_reason"] = \
                                        exc.reason
                                    result["forward_stopped_at_log_offset"] = \
                                        forwarder.offer_offset
                                result["drain_refused"] = True
                                break
                            except Exception:
                                # Non-refusal sink failure in the
                                # drain: a channel error, recorded.
                                result["drain_refused"] = True
                                break
                            result["forwarded_bytes"] = forwarder.forwarded
                            continue
                        try:
                            chunk = reader(read_fd, FORWARD_CHUNK_BYTES)
                        except Exception:
                            # Post-teardown read failure: a channel
                            # error, recorded for the final status.
                            result["drain_refused"] = True
                            break
                        if not chunk:
                            break
                        forwarder.offer(chunk)
                    forwarder.finish()
                    while forwarder.has_piece():
                        if time.monotonic() >= drain_end:
                            result["drain_truncated"] = True
                            break
                        try:
                            sink(forwarder.take_piece())
                        except _SinkRefused as exc:
                            if not result["forward_refused"]:
                                result["forward_refused"] = True
                                result["forward_refusal_reason"] = exc.reason
                                result["forward_stopped_at_log_offset"] = \
                                    forwarder.offer_offset
                            result["drain_refused"] = True
                            break
                        except Exception:
                            # Non-refusal sink failure in the drain:
                            # a channel error, recorded.
                            result["drain_refused"] = True
                            break
                        result["forwarded_bytes"] = forwarder.forwarded
                except Exception:
                    # Post-teardown drain is bounded and best-effort;
                    # an unexpected failure here is a channel error,
                    # recorded for the final status (not a cap).
                    result["drain_refused"] = True
                try:
                    result["log_bytes"] = os.fstat(read_fd).st_size
                except OSError:
                    pass
                try:
                    os.close(read_fd)
                except OSError:
                    pass
                read_fd = None
            result["forward_truncated"] = forwarder.truncated
            result["forwarded_bytes"] = forwarder.forwarded
            result["status"] = _final_status(result, break_reason)
            result["terminated_by"] = break_reason
            _write_status_record(owned_dir, result)
        except Exception:
            _teardown_owned(child, result, terminal,
                            kill_grace_s, post_kill_s)
            if read_fd is not None:
                try:
                    os.close(read_fd)
                except OSError:
                    pass
                read_fd = None
            result["forward_truncated"] = forwarder.truncated
            result["forwarded_bytes"] = forwarder.forwarded
            result["status"] = _final_status(result,
                                             break_reason or "observer")
            if result["status"] == STATUS_OK:
                result["status"] = STATUS_OBSERVER_FAILURE
            if result["terminated_by"] is None:
                result["terminated_by"] = "supervisor-error"
            _write_status_record(owned_dir, result)
        except BaseException:
            _teardown_owned(child, result, terminal,
                            kill_grace_s, post_kill_s)
            if read_fd is not None:
                try:
                    os.close(read_fd)
                except OSError:
                    pass
                read_fd = None
            result["forward_truncated"] = forwarder.truncated
            result["forwarded_bytes"] = forwarder.forwarded
            # K20: finalize a truthful non-OK status/terminated_by
            # BEFORE the abort record persists: _final_status keeps
            # any stronger group/cleanup uncertainty, and a
            # supervisor abort must never be recorded as ordinary
            # child success. The same primary re-raises unchanged;
            # a record attempt must not mask it.
            status = _final_status(result, break_reason or "observer")
            if status == STATUS_OK:
                status = STATUS_OBSERVER_FAILURE
            result["status"] = status
            if result["terminated_by"] is None:
                result["terminated_by"] = "supervisor-error"
            try:
                _write_status_record(owned_dir, result)
            except BaseException:
                pass
            raise
    finally:
        result["elapsed"] = time.monotonic() - started
        if write_fd is not None:
            try:
                os.close(write_fd)
            except OSError:
                pass
        if read_fd is not None:
            try:
                os.close(read_fd)
            except OSError:
                pass
        # No deletion: the raw diagnostic log and its private 0700
        # directory are preserved (owned process cleanup only); the
        # runner reclaims RUNNER_TEMP per job.
    return result


def _repo_root():
    """oap/bin/ci_unit_diagnostics.py -> two levels up is the
    repository root, independent of the caller's working directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def direct_launch_projection(root):
    """Fixed direct pytest-console launch projection (main only).

    Returns (argv, env) for the repo's own installed console with the
    unchanged trailing suite args, or None to fail closed before any
    child exists. Every component is a bounded check of fixed local
    paths (no path scan, no caller-selected input, no shell, no uv,
    no fallback, no output framing change):

    * <root>/.venv and <root>/.venv/bin are real directories (lstat:
      a symlinked venv is refused);
    * <root>/.venv/pyvenv.cfg is a real regular file (local venv);
    * <root>/.venv/bin/pytest is a real regular executable file (the
      fixed installed console);
    * its shebang names an existing executable interpreter inside
      that same local bin directory (the console runs the local venv
      python, not an arbitrary external interpreter);
    * the child environment is the inherited environment plus
      VIRTUAL_ENV=<root>/.venv and <root>/.venv/bin as the first PATH
      entry (the reviewed local launch projection).
    """
    venv = os.path.join(root, VENV_RELPATH)
    bin_dir = os.path.join(venv, BIN_RELPATH)
    console = os.path.join(bin_dir, CONSOLE_RELPATH)
    try:
        venv_st = os.lstat(venv)
        bin_st = os.lstat(bin_dir)
        cfg_st = os.lstat(os.path.join(venv, "pyvenv.cfg"))
        console_st = os.lstat(console)
        interp_st = os.lstat(os.path.join(bin_dir, "python"))
    except (OSError, TypeError):
        return None
    if not (stat.S_ISDIR(venv_st.st_mode)
            and stat.S_ISDIR(bin_st.st_mode)
            and stat.S_ISREG(cfg_st.st_mode)
            and stat.S_ISREG(console_st.st_mode)
            and (stat.S_ISREG(interp_st.st_mode)
                 or stat.S_ISLNK(interp_st.st_mode))):
        return None
    if not (os.access(console, os.X_OK) and os.access(
            os.path.join(bin_dir, "python"), os.X_OK)):
        return None
    # Bounded shebang read: the first line of the fixed console must
    # name an interpreter inside the same local bin directory.
    try:
        fd = os.open(console, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return None
    try:
        head = os.read(fd, SHEBANG_READ_BYTES)
    except OSError:
        head = None
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    if head is None:
        return None
    line = head.split(b"\n", 1)[0]
    if not line.startswith(b"#!"):
        return None
    interpreter = line[2:].strip()
    if (not interpreter.startswith(b"/") or b" " in interpreter
            or b"\x00" in interpreter):
        return None
    try:
        interp_text = interpreter.decode("ascii")
    except UnicodeDecodeError:
        return None
    if os.path.dirname(interp_text) != bin_dir:
        return None
    env = dict(os.environ)
    env["VIRTUAL_ENV"] = venv
    inherited_path = env.get("PATH", "")
    env["PATH"] = (bin_dir + os.pathsep + inherited_path
                   if inherited_path else bin_dir)
    argv = [console] + list(TEST_SUITE_ARGS)
    return argv, env


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if args:
        sys.stderr.write(
            "ci-unit-diagnostics: no arguments accepted "
            "(fixed production command)\n")
        return EXIT_PREREQUISITE
    if not os.path.isfile(TIME_BINARY) \
            or not os.access(TIME_BINARY, os.X_OK):
        sys.stderr.write(
            "ci-unit-diagnostics: prerequisite missing: "
            "/usr/bin/time not executable\n")
        return EXIT_PREREQUISITE
    root = _repo_root()
    if not os.path.isdir(os.path.join(root, "tests", "unit")):
        sys.stderr.write(
            "ci-unit-diagnostics: prerequisite missing: tests/unit under "
            + root + "\n")
        return EXIT_PREREQUISITE
    projection = direct_launch_projection(root)
    if projection is None:
        sys.stderr.write(
            "ci-unit-diagnostics: prerequisite missing: fixed installed "
            "pytest console in the repo .venv\n")
        return EXIT_PREREQUISITE
    launch_argv, launch_env = projection
    runner_temp = os.environ.get("RUNNER_TEMP")
    latched = {"flag": False}

    def _latch(signum, frame):
        # Minimal NONRAISING latch: no locks, no I/O, no teardown here.
        latched["flag"] = True

    previous = {}
    for signum in (signal.SIGTERM, signal.SIGINT):
        try:
            previous[signum] = signal.signal(signum, _latch)
        except (ValueError, OSError):
            pass
    # Order 009-r: bounded optional own-cgroup observation. The
    # prelaunch snapshot and the inherited prelaunch RLIMIT_CPU are
    # captured BEFORE any child exists; the post-teardown snapshot is
    # taken only after run_child's bounded owned teardown completed.
    # Observation availability or any delta never determines child
    # status, acceptance, or which member failed.
    res_before = None
    res_rlimit = None
    if _ci_unit_resources is not None:
        try:
            res_before = _ci_unit_resources.snapshot()
            res_rlimit = _ci_unit_resources.rlimit_cpu()
        except Exception:
            res_before = None
            res_rlimit = None
    try:
        result = run_child(
            launch_argv, temp_root=runner_temp, cwd=root,
            environment=launch_env,
            interrupt_check=lambda: latched["flag"])
    finally:
        for signum, handler in previous.items():
            try:
                signal.signal(signum, handler)
            except (ValueError, OSError):
                pass
    res_after = None
    if _ci_unit_resources is not None:
        try:
            res_after = _ci_unit_resources.snapshot()
        except Exception:
            res_after = None
    if _ci_unit_resources is not None:
        result["resource_display"] = (
            _ci_unit_resources.render(res_rlimit, res_before, res_after))
    # K12/K18: the final summary uses the same bounded production
    # display path as forwarding (finite wall/byte/chunk budgets on
    # the real channel fd; no shared-fd flag mutation, no threads, no
    # helper child). A channel refusal is not success: the distinct
    # bounded phase-2 record persists the exact nonzero outcome and
    # truthful run-record metadata, then an honest nonzero returns.
    writer = None
    try:
        writer = _backpressured_writer(
            sys.stdout.fileno(), WRITE_POLL_S, WRITE_BUDGET_S,
            FORWARD_WALL_BUDGET_S)
    except (AttributeError, OSError, ValueError):
        pass
    phase_exit = _summary_phase(result, writer)
    if phase_exit is not None:
        return phase_exit
    return exit_code_for(result)


if __name__ == "__main__":
    raise SystemExit(main())
