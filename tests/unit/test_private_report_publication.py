"""Synthetic DTO and owned-directory checks; no producer or rights attestation.

unnamed staging protocol (Root amendment unnamed-v2): no destructive namespace
operation is exercised or permitted; controlled fixtures are simulations, not
adversarial scheduler proofs; no skip/xfail/fallback.
"""

import ast
import hashlib
import os
import stat

import pytest

from slaif_raggedized_helper import private_report_publication as publisher
from slaif_raggedized_helper.evaluation_program import Report
from slaif_raggedized_helper.source_cohort_runner import CohortReport


SENTINEL_EXIT = 73


def _never_touch(counter):
    # Unswallowed BaseException sentinel: a controlled SystemExit cannot be
    # caught or sanitized by the product (non-Exception failures are
    # re-raised with identity); the zero-call counter is asserted outside
    # the expected exception capture.
    def forbidden(*args, **kwargs):
        counter.append(1)
        raise SystemExit(SENTINEL_EXIT)

    return forbidden


def _report(payload=b"opaque\x00payload", graded=False):
    domain = (
        b"slaif-graded-evaluation-program-v1\n" if graded else b"slaif-source-cohort-runner-v1\n"
    )
    identity = "sha256:" + hashlib.sha256(domain + payload).hexdigest()
    if graded:
        return Report(payload, identity, "sha256:" + "0" * 64, 0, 0)
    return CohortReport(payload, identity, 0, 0)


def _assert_loaded_origins(checkout_root):
    # Actual-loaded origin guard: iterates every currently loaded module;
    # each matching product package module must be a nonmissing real file
    # under the assigned resolved src, and each loaded test_ module a
    # nonmissing real file under the assigned tests/unit.  Resolved real
    # files only; no source-size sum, no sys.path/sys.modules rewriting.
    import sys

    def origin(module):
        file = getattr(module, "__file__", None)
        if file is None:
            return None
        return os.path.realpath(os.path.abspath(file))

    src_root = os.path.join(checkout_root, "src")
    tests_unit = os.path.join(checkout_root, "tests", "unit")
    matched = 0
    for name, module in tuple(sys.modules.items()):
        if module is None:
            continue
        if name == "slaif_raggedized_helper" or name.startswith("slaif_raggedized_helper."):
            file = origin(module)
            assert file is not None and os.path.isfile(file)
            assert file.startswith(src_root + os.sep)
            matched += 1
        elif name.startswith("test_"):
            file = origin(module)
            assert file is not None and os.path.isfile(file)
            assert file.startswith(tests_unit + os.sep)
            matched += 1
    assert matched


def test_imported_module_is_assigned_worktree_source():
    # Closed-environment origin guard: the venv's editable .pth adds another
    # lane's source path, so every currently loaded product/test module must
    # be a real file under the worktree that contains this test, selected by
    # the assigned PYTHONPATH entry.  The final restored-state guard is the
    # separate test_final_state_loaded_origins_restored at module end.
    test_path = os.path.realpath(os.path.abspath(__file__))
    checkout_root = os.path.realpath(os.path.join(os.path.dirname(test_path), "..", ".."))
    _assert_loaded_origins(checkout_root)
    expected_module = os.path.join(
        checkout_root, "src", "slaif_raggedized_helper", "private_report_publication.py"
    )
    assert os.path.isfile(expected_module)
    assert os.path.realpath(os.path.abspath(publisher.__file__)) == expected_module
    assert test_path.startswith(checkout_root + os.sep + "tests" + os.sep + "unit" + os.sep)


@pytest.mark.parametrize("graded", [False, True])
def test_publish_exact_opaque_and_existing(tmp_path, graded):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report(graded=graded)
    first = publisher.publish(report, directory=str(root))
    second = publisher.publish(report, directory=str(root))
    assert first.outcome is publisher.Outcome.PUBLISHED
    assert second.outcome is publisher.Outcome.EXISTING
    names = list(root.iterdir())
    assert len(names) == 1
    assert names[0].read_bytes() == report.identity_payload
    assert names[0].stat().st_mode & 0o777 == 0o400


@pytest.mark.parametrize("directory", ["/", "relative", "/tmp/../x", "/tmp//x", "/tmp/\x00"])
def test_bad_path_before_open(monkeypatch, directory):
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=directory)
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert calls == []


def test_wrong_identity_before_open(monkeypatch):
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    report = CohortReport(b"data", "sha256:" + "0" * 64, 0, 0)
    with pytest.raises(publisher.PublicationError):
        publisher.publish(report, directory="/tmp/private")
    assert calls == []


def test_existing_conflict_is_never_overwritten(tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    target = root / ("source-" + report.identity[7:] + ".json")
    target.write_bytes(b"foreign")
    target.chmod(0o400)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.CONFLICT
    assert target.read_bytes() == b"foreign"


@pytest.mark.parametrize("bad", [True, -1, 134217729])
def test_bad_work_before_open(monkeypatch, bad):
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    report = _report()
    report = CohortReport(report.identity_payload, report.identity, bad, 0)
    with pytest.raises(publisher.PublicationError):
        publisher.publish(report, directory="/tmp/private")
    assert calls == []


@pytest.mark.parametrize("bad", [True, 0, 30001, 1.5])
def test_bad_deadline_before_open(monkeypatch, bad):
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    with pytest.raises(publisher.PublicationError):
        publisher.publish(_report(), directory="/tmp/private", deadline_ms=bad)
    assert calls == []


@pytest.mark.parametrize("kind", ["fifo", "directory", "hardlink"])
def test_unsafe_existing_final_conflicts(tmp_path, kind):
    # The symlink kind runs in a fresh bounded owned exec child (see
    # test_symlink_final_conflicts_in_fresh_process): a nofollow open
    # refusal is an unresolved acquisition that permanently counts a
    # token in this process.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    target = root / ("source-" + report.identity[7:] + ".json")
    if kind == "fifo":
        os.mkfifo(target, 0o400)
    elif kind == "directory":
        target.mkdir()
    else:
        foreign = root / "foreign"
        foreign.write_bytes(report.identity_payload)
        foreign.chmod(0o400)
        os.link(foreign, target)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.CONFLICT
    assert os.path.lexists(target)


def test_short_writes_preserve_bytes(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    real_write = os.write

    def short(fd, data):
        return real_write(fd, data[: max(1, min(7, len(data)))])

    monkeypatch.setattr(os, "write", short)
    report = _report(b"x" * 137)
    assert publisher.publish(report, directory=str(root)).outcome is publisher.Outcome.PUBLISHED
    assert next(root.iterdir()).read_bytes() == report.identity_payload


def test_link_interruption_is_uncertain_and_no_partial_final(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)

    def interrupted(*args, **kwargs):
        raise OSError("controlled fault")

    monkeypatch.setattr(os, "link", interrupted)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    assert list(root.iterdir()) == []
    assert str(caught.value) == "private report publication refused"


def test_cancellation_keeps_identity_and_reclaims_staging(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    cancel = KeyboardInterrupt()

    def interrupted(*args, **kwargs):
        raise cancel

    monkeypatch.setattr(os, "write", interrupted)
    with pytest.raises(KeyboardInterrupt) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value is cancel
    assert list(root.iterdir()) == []


@pytest.mark.parametrize("operation", ["write", "fchmod", "fsync"])
def test_staging_fault_does_not_publish(tmp_path, monkeypatch, operation):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)

    def fail(*args, **kwargs):
        raise OSError("controlled fault")

    monkeypatch.setattr(os, operation, fail)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert list(root.iterdir()) == []


def test_directory_fsync_failure_keeps_complete_final(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    real_fsync = os.fsync
    count = 0

    def fail_second(fd):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("controlled directory fsync fault")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fail_second)
    report = _report()
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    assert next(root.iterdir()).read_bytes() == report.identity_payload


def test_omptfile_absent_refuses_without_staging(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    monkeypatch.setattr(os, "O_TMPFILE", None)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert caught.value.cleanup is publisher.Cleanup.CLEAN
    assert list(root.iterdir()) == []


def test_stage_foreign_link_detected_before_link(tmp_path, monkeypatch):
    # Controlled fstat fixture (simulated, not an adversarial scheduler proof):
    # the first fstat of the new regular nlink-0 fd records the stage fd; every
    # later fstat of it reports a foreign link, so the post-fsync nlink-0 check
    # must refuse before any publication link.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    real_fstat = os.fstat
    stage = []

    def foreign_link(fd):
        st = real_fstat(fd)
        if not stage and st.st_nlink == 0 and stat.S_ISREG(st.st_mode):
            stage.append(fd)
        values = list(st)
        if stage and fd == stage[0] and st.st_nlink == 0:
            values[3] = 1
        return os.stat_result(values)

    monkeypatch.setattr(os, "fstat", foreign_link)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert list(root.iterdir()) == []


def test_final_nlink_foreign_link_is_uncertain(tmp_path, monkeypatch):
    # Controlled entry-stat fixture (simulated): the final entry is observed
    # with nlink 2 (a foreign name on the same inode); the exact-nlink-1 final
    # check must degrade to uncertainty, never to PUBLISHED, without rollback.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    final_name = "source-" + report.identity[7:] + ".json"
    real_stat = os.stat

    def foreign_entry(name, dir_fd=None, follow_symlinks=True):
        st = real_stat(name, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        values = list(st)
        if name == final_name:
            values[3] = 2
        return os.stat_result(values)

    monkeypatch.setattr(os, "stat", foreign_entry)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    assert next(root.iterdir()).read_bytes() == report.identity_payload


_BANNED_CALLS = {"unlink", "remove", "rename", "replace", "rmtree"}


def _is_self_fds(node):
    # Exactly the attribute chain self.fds, nothing else.
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "fds"
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def _slot_fds_proven_builtin_set(tree):
    # Exemption provenance: _Slot.__init__ assigns self.fds = set() (the
    # builtin set, no arguments or keywords) and the module performs no
    # other self.fds assignment or in-place rebinding anywhere.
    init_assign = None
    for cls in ast.walk(tree):
        if not (isinstance(cls, ast.ClassDef) and cls.name == "_Slot"):
            continue
        for func in cls.body:
            if not (isinstance(func, ast.FunctionDef) and func.name == "__init__"):
                continue
            for node in ast.walk(func):
                if (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and _is_self_fds(node.targets[0])
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "set"
                    and not node.value.args
                    and not node.value.keywords
                ):
                    if init_assign is not None:
                        return False
                    init_assign = node
    if init_assign is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and node is not init_assign:
            for target in node.targets:
                if _is_self_fds(target):
                    return False
        if isinstance(node, ast.AugAssign) and _is_self_fds(node.target):
            return False
    return True


def _iter_calls_with_scope(node, class_name, function_name):
    if isinstance(node, ast.ClassDef):
        class_name = node.name
    elif isinstance(node, ast.FunctionDef):
        function_name = node.name
    if isinstance(node, ast.Call):
        yield node, class_name, function_name
    for child in ast.iter_child_nodes(node):
        yield from _iter_calls_with_scope(child, class_name, function_name)


def _scan_destructive_calls(source):
    # Receiver/context-aware destructive-namespace scan.  Unqualified
    # banned names and every call through any other receiver are rejected
    # conservatively; the single justified exemption is _Slot.close's
    # self.fds.remove(fd) bookkeeping on a member proven to be a builtin
    # set() with no other reassignment in the module.
    tree = ast.parse(source)
    proven = _slot_fds_proven_builtin_set(tree)
    found = []
    for call, class_name, function_name in _iter_calls_with_scope(tree, None, None):
        func = call.func
        if isinstance(func, ast.Name):
            if func.id in _BANNED_CALLS:
                found.append((call.lineno, func.id, "unqualified"))
        elif isinstance(func, ast.Attribute) and func.attr in _BANNED_CALLS:
            if (
                func.attr == "remove"
                and class_name == "_Slot"
                and function_name == "close"
                and _is_self_fds(func.value)
                and proven
            ):
                continue
            found.append((call.lineno, func.attr, "receiver"))
    return found


def test_no_destructive_namespace_calls_on_fault_branches(tmp_path, monkeypatch):
    calls = []

    def ban(name):
        def caller(*args, **kwargs):
            calls.append(name)
            raise SystemExit(SENTINEL_EXIT)

        return caller

    for name in sorted(_BANNED_CALLS):
        monkeypatch.setattr(os, name, ban(name), raising=False)
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    # Staging fault.
    with monkeypatch.context() as patch:
        patch.setattr(
            os, "write", lambda *a, **k: (_ for _ in ()).throw(OSError("controlled write fault"))
        )
        with pytest.raises(publisher.PublicationError):
            publisher.publish(report, directory=str(root))
    # Publication link fault.
    with monkeypatch.context() as patch:
        patch.setattr(
            os, "link", lambda *a, **k: (_ for _ in ()).throw(OSError("controlled link fault"))
        )
        with pytest.raises(publisher.PublicationError):
            publisher.publish(report, directory=str(root))
    assert calls == []
    assert list(root.iterdir()) == []


def test_module_source_has_no_destructive_calls():
    # Receiver/context-aware: unqualified and unknown-receiver destructive
    # calls are rejected; the only exemption is _Slot.close's self.fds.remove
    # bookkeeping, proven to target a builtin set() member.
    source_path = os.path.abspath(publisher.__file__)
    with open(source_path, "r", encoding="utf-8") as handle:
        source = handle.read()
    assert _scan_destructive_calls(source) == []


def test_destructive_ast_scan_non_vacuity_controls():
    # Pure-AST non-vacuity controls over source strings (never executed):
    # every banned namespace call, every unqualified form and every unknown
    # receiver must be detected; only the proven _Slot.close self.fds.remove
    # bookkeeping is distinguished, and missing or broken provenance must
    # not earn the exemption.
    detected = [
        "import os\nos.unlink('/x')\n",
        "import os\nos.remove('/x')\n",
        "import os\nos.rename('/x', '/y')\n",
        "import os\nos.replace('/x', '/y')\n",
        "import shutil\nshutil.rmtree('/x')\n",
        "def f():\n    unlink('/x')\n",
        "def f():\n    remove('/x')\n",
        "def f():\n    rename('/x', '/y')\n",
        "def f():\n    replace('/x', '/y')\n",
        "def f():\n    rmtree('/x')\n",
        "def f():\n    thing.remove('/x')\n",
        "def close(fd):\n    self.fds.remove(fd)\n",
        "class Other:\n    def close(self, fd):\n        self.fds.remove(fd)\n",
    ]
    for snippet in detected:
        assert _scan_destructive_calls(snippet), snippet
    valid = (
        "class _Slot:\n"
        "    def __init__(self):\n"
        "        self.fds = set()\n"
        "    def close(self, fd):\n"
        "        self.fds.remove(fd)\n"
    )
    assert _scan_destructive_calls(valid) == []
    unproven = (
        "class _Slot:\n"
        "    def __init__(self):\n"
        "        self.fds = {}\n"
        "    def close(self, fd):\n"
        "        self.fds.remove(fd)\n"
    )
    reassigned = (
        "class _Slot:\n"
        "    def __init__(self):\n"
        "        self.fds = set()\n"
        "    def swap(self):\n"
        "        self.fds = list()\n"
        "    def close(self, fd):\n"
        "        self.fds.remove(fd)\n"
    )
    assert _scan_destructive_calls(unproven), unproven
    assert _scan_destructive_calls(reassigned), reassigned


def test_tracking_protocol_ast_controls():
    # Pure-AST protocol controls over the actual source (never
    # executed): one close protocol with CLOSING before the close call
    # and numeric clear before FREE, failure counted as UNKNOWN; PRE
    # reserved before open with the fd bound directly; the bounded
    # no-acquisition probe precedes the attempted final open.
    source_path = os.path.abspath(publisher.__file__)
    with open(source_path, "r", encoding="utf-8") as handle:
        source = handle.read()
    assert "self.fds" not in source
    tree = ast.parse(source)
    close_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "close"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
    ]
    assert len(close_calls) == 1
    functions = {
        func.name: func
        for cls in ast.walk(tree)
        if isinstance(cls, ast.ClassDef) and cls.name == "_Slot"
        for func in cls.body
        if isinstance(func, ast.FunctionDef)
    }
    close_cell = functions["_close_cell"]
    first = close_cell.body[0]
    assert isinstance(first, ast.Assign)
    target = first.targets[0]
    assert isinstance(target, ast.Subscript) and isinstance(target.value, ast.Attribute)
    assert target.value.attr == "st" and isinstance(target.value.value, ast.Name)
    assert target.value.value.id == "self"
    assert isinstance(first.value, ast.Name) and first.value.id == "_CLOSING"
    try_stmt = close_cell.body[1]
    assert isinstance(try_stmt, ast.Try)
    body = try_stmt.body
    assert len(body) == 3
    assert isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Call)
    call = body[0].value
    assert isinstance(call.func, ast.Attribute) and call.func.attr == "close"
    assert isinstance(call.func.value, ast.Name) and call.func.value.id == "os"
    assert isinstance(body[1], ast.Assign)
    target1 = body[1].targets[0]
    assert isinstance(target1, ast.Subscript) and isinstance(target1.value, ast.Attribute)
    assert target1.value.attr == "fdn"
    assert isinstance(body[1].value, ast.UnaryOp) and isinstance(body[1].value.op, ast.USub)
    assert isinstance(body[1].value.operand, ast.Constant) and body[1].value.operand.value == 1
    assert isinstance(body[2], ast.Assign)
    target2 = body[2].targets[0]
    assert isinstance(target2, ast.Subscript) and isinstance(target2.value, ast.Attribute)
    assert target2.value.attr == "st"
    assert isinstance(body[2].value, ast.Name) and body[2].value.id == "_FREE"
    handler = try_stmt.handlers[0]
    assert isinstance(handler, ast.ExceptHandler) and handler.type is not None
    assert isinstance(handler.type, ast.Name) and handler.type.id == "BaseException"
    assert len(handler.body) == 2
    h_target = handler.body[0].targets[0]
    assert isinstance(h_target, ast.Subscript) and isinstance(h_target.value, ast.Attribute)
    assert h_target.value.attr == "st"
    assert isinstance(handler.body[0].value, ast.Name) and handler.body[0].value.id == "_UNKNOWN"
    assert isinstance(handler.body[1], ast.Raise)
    opened = functions["opened"]
    pre_assign = None
    direct_store = None
    for node in ast.walk(opened):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Attribute)
            and isinstance(target.value.value, ast.Name)
            and target.value.value.id == "self"
        ):
            continue
        if (
            target.value.attr == "st"
            and isinstance(node.value, ast.Name)
            and node.value.id == "_PRE"
        ):
            pre_assign = node
        if (
            target.value.attr == "fdn"
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "open"
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "os"
        ):
            direct_store = node
    assert pre_assign is not None
    assert direct_store is not None
    assert pre_assign.lineno < direct_store.lineno
    verify = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_verify":
            verify = node
    assert verify is not None
    stat_calls = []
    opened_calls = []
    for node in ast.walk(verify):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if not isinstance(func.value, ast.Name):
            continue
        if (
            func.attr == "stat"
            and func.value.id == "os"
            and any(
                kw.arg == "follow_symlinks"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is False
                for kw in node.keywords
            )
        ):
            stat_calls.append(node)
        if func.attr == "opened" and func.value.id == "slot":
            opened_calls.append(node)
    assert stat_calls
    assert opened_calls
    assert stat_calls[0].lineno < opened_calls[0].lineno


def test_bad_root_mode_refuses(tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    root.chmod(0o750)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert list(root.iterdir()) == []


def test_symlink_root_refuses_in_fresh_process(tmp_path):
    # A nofollow walk refusal on a symlink root is an unresolved
    # acquisition under the token model and permanently counts a cell,
    # so the refusal is witnessed in a fresh bounded owned exec child.
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _SYMLINK_ROOT_CHILD,
            str(root),
            str(tmp_path / "alias"),
        ],
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr
    assert list(root.iterdir()) == []


def test_symlink_final_conflicts_in_fresh_process(tmp_path):
    # A nofollow open refusal on an unsafe existing final is an
    # unresolved acquisition under the token model and permanently
    # counts a cell, so the conflict is witnessed in a fresh bounded
    # owned exec child; the unsafe final must remain untouched.
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    completed = subprocess.run(
        [sys.executable, "-c", _SYMLINK_FINAL_CHILD, str(root)],
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr


def _sixteen_slot_fixture(monkeypatch, start_fault=None, started=None, on_reserve=None):
    # Shared 16-slot refusal harness: every successfully started worker
    # is owned until it has terminated.  start_fault is a narrow
    # optional seam invoked before each real Thread.start; when a start
    # fails (seam or platform), the unreachable barrier is aborted,
    # waiting workers are signalled, the started workers are
    # bounded-joined and the exact initiating exception is re-raised
    # unchanged so pytest reports it.
    # on_reserve is a narrow optional observer of the real _reserve()
    # return value, invoked in the reserving worker before the barrier.
    import threading

    barrier = threading.Barrier(17, timeout=8)
    release = threading.Event()
    failures = []

    def own_slot():
        slot = None
        try:
            slot = publisher._reserve()
            if on_reserve is not None:
                on_reserve(slot)
            barrier.wait()
            assert release.wait(8)
        except BaseException as exc:
            failures.append(exc)
        finally:
            if slot is not None:
                publisher._release(slot)
                slot.guard.release()

    threads = [threading.Thread(target=own_slot) for _ in range(16)]
    owned = []
    try:
        for thread in threads:
            if start_fault is not None:
                start_fault()
            thread.start()
            owned.append(thread)
            if started is not None:
                started.append(thread)
    except BaseException:
        # Partial startup: the 17-party barrier can never trip, so
        # abort it to release waiting workers, signal the release
        # gate, own the started workers to bounded termination and
        # preserve the exact initiating failure.
        barrier.abort()
        release.set()
        for thread in owned:
            thread.join(timeout=8)
        raise
    try:
        barrier.wait()
        calls = []
        monkeypatch.setattr(os, "open", _never_touch(calls))
        with pytest.raises(publisher.PublicationError) as caught:
            publisher.publish(_report(), directory="/tmp/private")
        assert caught.value.cleanup is publisher.Cleanup.PENDING
        assert calls == []
    finally:
        release.set()
        for thread in threads:
            thread.join(timeout=8)
    assert not failures
    assert all(not thread.is_alive() for thread in threads)


def test_sixteen_slots_refuse_seventeenth_without_open(monkeypatch):
    _sixteen_slot_fixture(monkeypatch)


def test_partial_startup_preserves_failure_and_terminates_workers(monkeypatch):
    # Controlled ordinary failure at the third start, after two genuine
    # workers are already running and each holds a real reservation:
    # the exact initiating exception must escape, both acquired slot
    # identities must be observed present in the real broker before the
    # fault, the started workers must terminate through the production
    # release path, and the registry's exact identities and order must
    # be restored afterwards.  No fake start success, no fake
    # allocator, no pool reset, no registry clearing, no sleep
    # oracles; a synchronization timeout is a test failure.
    import threading

    initiating = RuntimeError("controlled partial startup failure")
    attempts = []
    started = []
    reserved = []
    both_reserved = threading.Event()

    def on_reserve(slot):
        reserved.append(slot)
        if len(reserved) == 2:
            both_reserved.set()

    def flaky_start():
        attempts.append(1)
        if len(attempts) >= 3:
            if not both_reserved.wait(8):
                raise AssertionError("synchronization timeout before fault")
            assert reserved[0] is not reserved[1]
            for slot in reserved:
                assert any(current is slot for current in publisher._SLOTS)
            raise initiating

    initial_registry = list(publisher._SLOTS)
    with pytest.raises(RuntimeError) as caught:
        _sixteen_slot_fixture(
            monkeypatch, start_fault=flaky_start, started=started, on_reserve=on_reserve
        )
    assert caught.value is initiating
    assert len(attempts) == 3
    assert len(started) == 2
    assert all(not thread.is_alive() for thread in started)
    for slot in reserved:
        assert not any(current is slot for current in publisher._SLOTS)
    assert list(publisher._SLOTS) == initial_registry


def _child_limits():
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16777216, 16777216))


def _child_environment():
    environment = {"PYTHONPATH": os.path.abspath("src"), "PYTHONDONTWRITEBYTECODE": "1"}
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        environment[name] = "1"
    return environment


_CHILD = r"""
import hashlib, resource, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper.source_cohort_runner import CohortReport
from slaif_raggedized_helper.private_report_publication import publish
payload = sys.argv[2].encode("ascii")
identity = "sha256:" + hashlib.sha256(b"slaif-source-cohort-runner-v1\n" + payload).hexdigest()
result = publish(CohortReport(payload, identity, 0, 0), directory=sys.argv[1], deadline_ms=8000)
print(result.outcome.value)
"""


@pytest.mark.parametrize("same", [True, False])
def test_fresh_processes_serialize_publication(tmp_path, same):
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    children = []
    try:
        for value in ("first", "first" if same else "second"):
            children.append(
                subprocess.Popen(
                    [sys.executable, "-c", _CHILD, str(root), value],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=environment,
                    preexec_fn=_child_limits,
                )
            )
        outputs = []
        for child in children:
            out, err = child.communicate(timeout=10)
            assert child.returncode == 0, err
            outputs.append(out.strip())
        assert sorted(outputs) == (
            ["EXISTING", "PUBLISHED"] if same else ["PUBLISHED", "PUBLISHED"]
        )
        assert len(list(root.iterdir())) == (1 if same else 2)
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)


_TOMBSTONE_CHILD = r"""
import hashlib, os, resource, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper.source_cohort_runner import CohortReport
from slaif_raggedized_helper import private_report_publication as p
payload = b"synthetic"
identity = "sha256:" + hashlib.sha256(b"slaif-source-cohort-runner-v1\n" + payload).hexdigest()
original_cleanup = p._cleanup
original_close = os.close
seen = []
def cleanup(slot, end):
    root = slot.root
    def close(fd):
        if fd == root:
            seen.append(fd)
            raise OSError("simulated ambiguous close")
        return original_close(fd)
    os.close = close
    try:
        return original_cleanup(slot, end)
    finally:
        os.close = original_close
p._cleanup = cleanup
try:
    p.publish(CohortReport(payload, identity, 0, 0), directory=sys.argv[1])
except p.PublicationError as exc:
    assert exc.publication is p.Publication.DURABLE
    assert exc.cleanup is p.Cleanup.PENDING
else:
    raise AssertionError("missing refusal")
assert len(seen) == 1
receipt = p.retry_cleanup()
assert receipt.remaining == 1 and receipt.status is p.Cleanup.PENDING
assert len(seen) == 1
"""


_CANCEL_TOMBSTONE_CHILD = r"""
import hashlib, os, resource, stat, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper.source_cohort_runner import CohortReport
from slaif_raggedized_helper import private_report_publication as p
payload = b"synthetic"
identity = "sha256:" + hashlib.sha256(b"slaif-source-cohort-runner-v1\n" + payload).hexdigest()
root = sys.argv[1]
original_cleanup = p._cleanup
original_close = os.close
original_fstat = os.fstat
cancel = KeyboardInterrupt("controlled cancellation")
def cleanup(slot, end):
    def close(fd):
        try:
            st = original_fstat(fd)
        except OSError:
            raise cancel
        if stat.S_ISREG(st.st_mode):
            raise cancel
        return original_close(fd)
    os.close = close
    try:
        return original_cleanup(slot, end)
    finally:
        os.close = original_close
p._cleanup = cleanup
def bad_write(fd, data):
    raise OSError("controlled write fault")
os.write = bad_write
try:
    p.publish(CohortReport(payload, identity, 0, 0), directory=root)
except p.PublicationError:
    raise AssertionError("cancellation must keep its BaseException identity")
except BaseException as exc:
    assert type(exc) is KeyboardInterrupt
    assert exc is cancel
else:
    raise AssertionError("missing cancellation")
assert os.listdir(root) == []
receipt = p.retry_cleanup()
assert receipt.status is p.Cleanup.PENDING
assert receipt.remaining >= 1
pending = [s for s in p._SLOTS if s is not None and s.pending]
assert len(pending) == 1
assert sum(1 for s in pending[0].st if s in (p._CLOSING, p._UNKNOWN)) >= 1
"""

_PENDING_FOREIGN_CHILD = r"""
import hashlib, os, resource, stat, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper.source_cohort_runner import CohortReport
from slaif_raggedized_helper import private_report_publication as p
payload = b"synthetic"
identity = "sha256:" + hashlib.sha256(b"slaif-source-cohort-runner-v1\n" + payload).hexdigest()
root = sys.argv[1]
real_fstat = os.fstat
real_close = os.close
real_write = os.write
def bad_write(fd, data):
    raise OSError("controlled write fault")
def fault_close(fd):
    try:
        st = real_fstat(fd)
    except OSError:
        raise OSError("controlled close fault")
    if stat.S_ISREG(st.st_mode):
        raise OSError("controlled close fault")
    return real_close(fd)
os.write = bad_write
os.close = fault_close
try:
    p.publish(CohortReport(payload, identity, 0, 0), directory=root)
except p.PublicationError as exc:
    assert exc.publication is p.Publication.NOT_PUBLISHED
    assert exc.cleanup is p.Cleanup.PENDING
else:
    raise AssertionError("missing refusal")
os.write = real_write
os.close = real_close
foreign = os.path.join(root, "foreign-owned")
with open(foreign, "wb") as handle:
    handle.write(b"foreign synthetic")
receipt = p.retry_cleanup()
assert receipt.status is p.Cleanup.PENDING
assert receipt.remaining >= 1
with open(foreign, "rb") as handle:
    assert handle.read() == b"foreign synthetic"
assert sorted(os.listdir(root)) == ["foreign-owned"]
pending = [s for s in p._SLOTS if s is not None and s.pending]
assert len(pending) == 1
assert sum(1 for s in pending[0].st if s in (p._CLOSING, p._UNKNOWN)) >= 1
"""


_TRACKING_FAULT_CHILD = r"""
import os, resource, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper import private_report_publication as p
root = sys.argv[1]
owned = os.path.join(root, "owned")
with open(owned, "wb") as handle:
    handle.write(b"x")
real_open = os.open
real_close = os.close
seen = []
close_calls = []
def unresolved_open(*args, **kwargs):
    fd = real_open(*args, **kwargs)
    seen.append(fd)
    raise OSError("controlled unresolved acquisition")
os.open = unresolved_open
slot = p._reserve()
try:
    slot.opened(owned, os.O_RDONLY | os.O_CLOEXEC)
except OSError as exc:
    assert type(exc) is OSError
    assert "unresolved acquisition" in str(exc)
else:
    raise AssertionError("missing unresolved acquisition fault")
assert len(seen) == 1
unknown = [k for k in range(6) if slot.st[k] == p._UNKNOWN]
assert len(unknown) == 1
assert slot.fdn[unknown[0]] == -1
assert slot._occupied() == 1
assert len([s for s in p._SLOTS if s is not None and s is slot]) == 1
slot.pending = True
slot.guard.release()
def counting_close(fd):
    close_calls.append(fd)
    return real_close(fd)
os.close = counting_close
receipt = p.retry_cleanup()
assert receipt.attempted == 1
assert receipt.status is p.Cleanup.PENDING
assert receipt.remaining == 1
assert close_calls == []
pending = [s for s in p._SLOTS if s is not None and s.pending]
assert len(pending) == 1
assert pending[0] is slot
assert len([k for k in range(6) if slot.st[k] == p._UNKNOWN]) == 1
# Fault B: close-return-then-raise on a definitely stored token keeps the
# number counted, and the retired number is never closed again.
os.open = real_open
fd = slot.opened(owned, os.O_RDONLY | os.O_CLOEXEC)
k = slot._find(fd)
assert slot.st[k] == p._OWNED and slot.fdn[k] == fd
def failing_close(fd2):
    close_calls.append(fd2)
    raise OSError("controlled close fault")
os.close = failing_close
try:
    slot.close(fd)
except OSError as exc:
    assert "close fault" in str(exc)
else:
    raise AssertionError("missing close fault")
assert slot.st[k] == p._UNKNOWN and slot.fdn[k] == fd
assert close_calls == [fd]
receipt = p.retry_cleanup()
assert receipt.attempted == 1
assert receipt.status is p.Cleanup.PENDING
assert receipt.remaining == 1
assert close_calls == [fd]
os.close = real_close
# Fault C: post-store bookkeeping fault model with a real owned private
# FD: the acquisition wrapper really opens, the store commits (kernel
# acquisition + product cell), then the precreated primary raises from
# the wrapper and the cleanup close raises the precreated cleanup.  The
# three priority combinations are covered in this SAME child (no new
# launches): ordinary primary + ordinary cleanup -> primary from
# cleanup; non-Exception + non-Exception -> the same primary wins;
# ordinary primary + non-Exception -> the same cleanup wins.  Every cell
# stays UNKNOWN (counted, number retained, never retried); each own fd
# is closed exactly once by the independently tracking test.  Controlled
# model - not actual OOM or signal.
prim_a = OSError("controlled post-store primary a")
clean_a = OSError("controlled cleanup a")
prim_b = KeyboardInterrupt("controlled non-exception primary b")
clean_b = GeneratorExit("controlled non-exception cleanup b")
prim_c = OSError("controlled post-store primary c")
clean_c = SystemExit("controlled non-exception cleanup c")
stored_cells = []
def make_fault_pair(primary, cleanup):
    def fault_open(*args, **kwargs):
        fdx = real_open(*args, **kwargs)
        reserved = [
            kk for kk in range(6)
            if slot.st[kk] == p._PRE and slot.fdn[kk] == -1
        ]
        assert len(reserved) == 1
        slot.fdn[reserved[0]] = fdx
        slot.st[reserved[0]] = p._OWNED
        stored_cells.append((reserved[0], fdx))
        raise primary
    def fault_close(fd2):
        close_calls.append(fd2)
        raise cleanup
    return fault_open, fault_close
def run_fault(primary, cleanup):
    fault_open, fault_close = make_fault_pair(primary, cleanup)
    os.open = fault_open
    os.close = fault_close
    close_calls.clear()
    caught = None
    try:
        slot.opened(owned, os.O_RDONLY | os.O_CLOEXEC)
    except BaseException as exc:
        caught = exc
    return caught
caught_a = run_fault(prim_a, clean_a)
assert caught_a is prim_a
assert caught_a.__cause__ is clean_a
caught_b = run_fault(prim_b, clean_b)
assert caught_b is prim_b
assert caught_b.__cause__ is clean_b
caught_c = run_fault(prim_c, clean_c)
assert caught_c is clean_c
assert caught_c.__context__ is prim_c
assert caught_c.__cause__ is None
assert len(stored_cells) == 3
for kc, fd3 in stored_cells:
    assert slot.st[kc] == p._UNKNOWN and slot.fdn[kc] == fd3
assert slot._occupied() == 5
# Restore both acquisition hooks before the genuine new-token branch:
# the fresh reopen must be a real ordinary acquisition, not another
# controlled fault; the temporary own close hooks end at this boundary.
os.open = real_open
os.close = real_close
os.close = counting_close
close_calls.clear()
receipt = p.retry_cleanup()
assert receipt.attempted == 1
assert receipt.status is p.Cleanup.PENDING
assert receipt.remaining == 1
assert close_calls == []
os.close = real_close
# Close only the B/C known-retired fixture fds before the reopen; their
# numbers remain in counted UNKNOWN cells.  A's unresolved fd stays
# open, so the allocator cannot return an unseen lower integer and the
# fresh open must reuse B's known retired number.
retired = [fd] + [fd3 for _, fd3 in stored_cells]
for fdx in retired:
    real_close(fdx)
# A fresh genuine open reusing the known retired number is a NEW token.
close_calls.clear()
fd2 = slot.opened(owned, os.O_RDONLY | os.O_CLOEXEC)
assert fd2 == fd
k2 = slot._find(fd2)
assert k2 != k
assert slot.st[k2] == p._OWNED and slot.fdn[k2] == fd2
os.close = counting_close
slot.close(fd2)
assert close_calls == [fd2]
assert slot.st[k2] == p._FREE and slot.fdn[k2] == -1
# The retired cell stays counted with its retained number; only the new
# token was closed, exactly once.
assert slot.st[k] == p._UNKNOWN and slot.fdn[k] == fd
# Now close A's unresolved fd exactly once via independent tracking.
real_close(seen[0])
with open(owned, "rb") as handle:
    assert handle.read() == b"x"
"""

_SYMLINK_ROOT_CHILD = r"""
import hashlib, os, resource, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper.source_cohort_runner import CohortReport
from slaif_raggedized_helper import private_report_publication as p
payload = b"synthetic"
identity = "sha256:" + hashlib.sha256(b"slaif-source-cohort-runner-v1\n" + payload).hexdigest()
root, alias = sys.argv[1], sys.argv[2]
os.symlink(root, alias, target_is_directory=True)
try:
    p.publish(CohortReport(payload, identity, 0, 0), directory=alias)
except p.PublicationError:
    pass
else:
    raise AssertionError("symlink root must refuse")
"""

_SYMLINK_FINAL_CHILD = r"""
import hashlib, os, resource, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper.source_cohort_runner import CohortReport
from slaif_raggedized_helper import private_report_publication as p
payload = b"synthetic"
identity = "sha256:" + hashlib.sha256(b"slaif-source-cohort-runner-v1\n" + payload).hexdigest()
root = sys.argv[1]
final = os.path.join(root, "source-" + identity[7:] + ".json")
os.symlink("absent", final)
try:
    p.publish(CohortReport(payload, identity, 0, 0), directory=root)
except p.PublicationError as exc:
    assert exc.publication is p.Publication.CONFLICT
else:
    raise AssertionError("symlink final must conflict")
assert os.path.lexists(final)
"""

_CANCEL_PRIORITY_CHILD = r"""
import hashlib, os, resource, stat, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper.source_cohort_runner import CohortReport
from slaif_raggedized_helper import private_report_publication as p
root = sys.argv[1]
payload = b"synthetic"
identity = "sha256:" + hashlib.sha256(b"slaif-source-cohort-runner-v1\n" + payload).hexdigest()
def report():
    return CohortReport(payload, identity, 0, 0)
real_write = os.write
real_close = os.close
real_fstat = os.fstat
# Scenario 1: a latched non-Exception primary survives a second, distinct
# cancellation raised by bounded cleanup; the propagated object must be the
# SAME latched primary, and the guard must be released.
sentinel = SystemExit(73)
second = KeyboardInterrupt("second controlled cancellation")
def write_primary(fd, data):
    raise sentinel
os.write = write_primary
def close_second(fd):
    try:
        st = real_fstat(fd)
    except OSError:
        return real_close(fd)
    if stat.S_ISREG(st.st_mode):
        raise second
    return real_close(fd)
os.close = close_second
try:
    p.publish(report(), directory=root)
except BaseException as exc:
    assert exc is sentinel, type(exc)
else:
    raise AssertionError("missing latched primary cancellation")
os.write = real_write
os.close = real_close
slots = [s for s in p._SLOTS if s is not None]
assert len(slots) == 1
first = slots[0]
assert first.pending
assert sum(1 for s in first.st if s in (p._CLOSING, p._UNKNOWN)) >= 1
assert first.guard.acquire(blocking=False)
first.guard.release()
# Scenario 2 (G1): a non-close cleanup failure must propagate, keep the
# slot pending and visible, release the guard, and leave the owned cells
# closeable by retry_cleanup.
original_cleanup = p._cleanup
exit74 = SystemExit(74)
def cleanup_failure(slot, end):
    raise exit74
p._cleanup = cleanup_failure
seen = []
def write_fault(fd, data):
    seen.append(fd)
    raise OSError("controlled write fault")
os.write = write_fault
try:
    p.publish(report(), directory=root)
except BaseException as exc:
    assert exc is exit74, type(exc)
else:
    raise AssertionError("missing cleanup failure")
os.write = real_write
p._cleanup = original_cleanup
slots = [s for s in p._SLOTS if s is not None]
assert len(slots) == 2
owned = [s for s in slots if any(c == p._OWNED for c in s.st)]
assert len(owned) == 1
second_slot = owned[0]
assert second_slot.pending
assert second_slot.guard.acquire(blocking=False)
second_slot.guard.release()
receipt = p.retry_cleanup()
assert receipt.attempted == 2
assert receipt.remaining == 1
assert receipt.status is p.Cleanup.PENDING
try:
    os.fstat(seen[0])
except OSError:
    pass
else:
    raise AssertionError("owned cell must be closed by retry_cleanup")
# Scenario order 3, 5, 4, 6: both write-fault scenarios need the
# genuinely fresh path (no final exists yet), so the durable-creating
# scenario runs after them; the durable original final is preserved,
# never deleted to force a path.
# Scenario 3 (F17): an ordinary latched primary plus a non-close
# ordinary cleanup failure must surface as the content-free
# PublicationError NOT_PUBLISHED/PENDING, with no raw internal error,
# cause or context on the fresh controlled call path.
ordinary_primary3 = OSError("controlled ordinary write fault 3")
ordinary_cleanup3 = OSError("controlled non-close cleanup fault 3")
def current_slots():
    return [s for s in p._SLOTS if s is not None]
def new_slot(before):
    added = [s for s in current_slots() if all(s is not b for b in before)]
    assert len(added) == 1
    return added[0]
original_cleanup = p._cleanup
def cleanup_ordinary3(slot, end):
    raise ordinary_cleanup3
p._cleanup = cleanup_ordinary3
def write_fault3(fd, data):
    raise ordinary_primary3
os.write = write_fault3
before3 = current_slots()
try:
    p.publish(report(), directory=root)
except p.PublicationError as exc:
    assert type(exc) is p.PublicationError
    assert str(exc) == "private report publication refused"
    assert exc.publication is p.Publication.NOT_PUBLISHED
    assert exc.cleanup is p.Cleanup.PENDING
    assert exc.__cause__ is None and exc.__context__ is None
else:
    raise AssertionError("missing ordinary cleanup refusal")
os.write = real_write
p._cleanup = original_cleanup
slot3 = new_slot(before3)
assert slot3.pending and any(c == p._OWNED for c in slot3.st)
assert slot3.guard.acquire(blocking=False)
slot3.guard.release()
# S3's replaced _cleanup never closed its known owned handles (stage
# and root), so its directory flock would block the next same-root
# publish; reclaim them through the PUBLIC bounded retry now, keeping
# the earlier UNKNOWN tombstone counted.
mid_receipt = p.retry_cleanup()
assert mid_receipt.attempted == 2
assert mid_receipt.remaining == 1
assert mid_receipt.status is p.Cleanup.PENDING
final_name = "source-" + identity[7:] + ".json"
final_path = os.path.join(root, final_name)
# Scenario 5 (F18): a latched non-Exception primary keeps its SAME
# object when retirement raises a second, distinct cancellation; the
# write fault is reached non-vacuously on the genuinely fresh path.
assert not os.path.lexists(final_path)
sentinel5 = SystemExit(75)
retire_cancel5 = SystemExit(76)
write_reached5 = []
def write_primary5(fd, data):
    write_reached5.append(fd)
    raise sentinel5
os.write = write_primary5
original_release = p._release
def release_cancel5(slot):
    raise retire_cancel5
p._release = release_cancel5
before5 = current_slots()
try:
    p.publish(report(), directory=root)
except BaseException as exc:
    assert exc is sentinel5, type(exc)
else:
    raise AssertionError("missing latched primary over retirement")
os.write = real_write
p._release = original_release
assert len(write_reached5) == 1
slot5 = new_slot(before5)
assert slot5.pending and slot5._all_free()
assert slot5.guard.acquire(blocking=False)
slot5.guard.release()
# Scenario 4 (F17/F18): the first completed DURABLE publish creates
# the final; a bounded cleanup that raises an ordinary error after
# the real close work must surface as the content-free DURABLE/PENDING
# refusal with the final preserved and the slot retry-visible.
ordinary_durable4 = OSError("controlled post-durable cleanup fault 4")
original_cleanup = p._cleanup
def cleanup_after_durable4(slot, end):
    original_cleanup(slot, end)
    raise ordinary_durable4
p._cleanup = cleanup_after_durable4
before4 = current_slots()
try:
    p.publish(report(), directory=root)
except p.PublicationError as exc:
    assert str(exc) == "private report publication refused"
    assert exc.publication is p.Publication.DURABLE
    assert exc.cleanup is p.Cleanup.PENDING
    assert exc.__cause__ is None and exc.__context__ is None
else:
    raise AssertionError("missing post-durable cleanup refusal")
p._cleanup = original_cleanup
final_bytes = open(final_path, "rb").read()
assert final_bytes == b"synthetic"
slot4 = new_slot(before4)
assert slot4.pending and slot4._all_free()
assert slot4.guard.acquire(blocking=False)
slot4.guard.release()
# Scenario 6 (F18): an ordinary retirement error is sanitized to the
# content-free DURABLE/PENDING refusal; the second publish verifies
# the preserved final byte-exact (pre-attempt EXISTING -> DURABLE)
# and never replaces or deletes it.
ordinary_retire6 = OSError("controlled retirement fault 6")
def release_ordinary6(slot):
    raise ordinary_retire6
p._release = release_ordinary6
before6 = current_slots()
try:
    p.publish(report(), directory=root)
except p.PublicationError as exc:
    assert str(exc) == "private report publication refused"
    assert exc.publication is p.Publication.DURABLE
    assert exc.cleanup is p.Cleanup.PENDING
    assert exc.__cause__ is None and exc.__context__ is None
else:
    raise AssertionError("missing retirement refusal")
p._release = original_release
assert open(final_path, "rb").read() == final_bytes
slot6 = new_slot(before6)
assert slot6.pending and slot6._all_free()
# Scenario 7 (F19 witness): the guard-release fault, before and after
# its effect, is reached in the real publish path: the preserved final
# selects the pre-attempt EXISTING path and the controlled root fsync
# fault is the ordinary primary.  The release is attempted exactly
# once, never retried blindly, and the registry stays accurate.
real_fsync = os.fsync
fsyncfault7 = OSError("controlled root fsync fault 7")
def fsync_rootfault7(fd):
    try:
        st = real_fstat(fd)
    except OSError:
        return real_fsync(fd)
    if stat.S_ISREG(st.st_mode):
        return real_fsync(fd)
    raise fsyncfault7
shims7a = []
class shim_class7a:
    def __init__(self, real):
        self.real = real
        self.releases = 0
    def acquire(self, blocking=True):
        return self.real.acquire(blocking=blocking)
    def release(self):
        self.releases += 1
        raise OSError("controlled guard release fault 7a")
original_reserve = p._reserve
def reserve7a():
    slot = original_reserve()
    shim = shim_class7a(slot.guard)
    shims7a.append(shim)
    slot.guard = shim
    return slot
p._reserve = reserve7a
os.fsync = fsync_rootfault7
before7a = current_slots()
try:
    p.publish(report(), directory=root)
except p.PublicationError as exc:
    assert str(exc) == "private report publication refused"
    assert exc.publication is p.Publication.NOT_PUBLISHED
    assert exc.cleanup is p.Cleanup.PENDING
    assert exc.__cause__ is None and exc.__context__ is None
else:
    raise AssertionError("missing guard fault refusal")
os.fsync = real_fsync
p._reserve = original_reserve
g7a = shims7a[0]
assert g7a.releases == 1
assert not g7a.real.acquire(blocking=False)
g7a.real.release()
assert current_slots() == before7a
sentinel7b = SystemExit(77)
shims7b = []
class shim_class7b:
    def __init__(self, real):
        self.real = real
        self.releases = 0
    def acquire(self, blocking=True):
        return self.real.acquire(blocking=blocking)
    def release(self):
        self.releases += 1
        self.real.release()
        raise sentinel7b
def reserve7b():
    slot = original_reserve()
    shim = shim_class7b(slot.guard)
    shims7b.append(shim)
    slot.guard = shim
    return slot
p._reserve = reserve7b
os.fsync = fsync_rootfault7
before7b = current_slots()
try:
    p.publish(report(), directory=root)
except BaseException as exc:
    assert exc is sentinel7b
    assert exc.__cause__ is None and exc.__context__ is None
else:
    raise AssertionError("missing guard cancellation")
os.fsync = real_fsync
p._reserve = original_reserve
g7b = shims7b[0]
assert g7b.releases == 1
assert g7b.real.acquire(blocking=False)
g7b.real.release()
assert current_slots() == before7b
# Final retry: honest owned accounting derived from actual retention
# (one mid-retry already retired S3's slot); only the first slot,
# with its counted UNKNOWN cell, remains pending; final is intact.
receipt = p.retry_cleanup()
assert receipt.attempted == 4
assert receipt.remaining == 1
assert receipt.status is p.Cleanup.PENDING
slots = current_slots()
assert len(slots) == 1
left = slots[0]
assert sum(1 for c in left.st if c in (p._CLOSING, p._UNKNOWN)) >= 1
assert open(final_path, "rb").read() == final_bytes
assert sorted(e.name for e in os.scandir(root)) == [final_name]
"""

_EXHAUSTION_CHILD = r"""
import os, resource, sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from slaif_raggedized_helper import private_report_publication as p
root = sys.argv[1]
owned = os.path.join(root, "owned")
with open(owned, "wb") as handle:
    handle.write(b"x")
slot = p._Slot()
for k in range(6):
    slot.st[k] = p._UNKNOWN
    slot.fdn[k] = -1
opens = []
real_open = os.open
def counting_open(*args, **kwargs):
    opens.append(1)
    return real_open(*args, **kwargs)
os.open = counting_open
try:
    slot.opened(owned, os.O_RDONLY | os.O_CLOEXEC)
except p._Failure:
    pass
else:
    raise AssertionError("unknown exhaustion must refuse before open")
assert opens == []
os.open = real_open
try:
    p._release(slot)
except p._Failure:
    pass
else:
    raise AssertionError("counted unknown must not unregister")
slot2 = p._Slot()
for k in range(5):
    slot2.st[k] = p._UNKNOWN
    slot2.fdn[k] = -1
fd = slot2.opened(owned, os.O_RDONLY | os.O_CLOEXEC)
k = slot2._find(fd)
assert slot2.st[k] == p._OWNED
try:
    slot2.opened(owned, os.O_RDONLY | os.O_CLOEXEC)
except p._Failure:
    pass
else:
    raise AssertionError("occupied sixth cell must refuse the next open")
slot2.close(fd)
assert not slot2._all_free()
fd2 = slot2.opened(owned, os.O_RDONLY | os.O_CLOEXEC)
slot2.close(fd2)
with open(owned, "rb") as handle:
    assert handle.read() == b"x"
"""


def test_durable_ambiguous_close_in_fresh_process(tmp_path):
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    completed = subprocess.run(
        [sys.executable, "-c", _TOMBSTONE_CHILD, str(root)],
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr
    assert len(list(root.iterdir())) == 1


def test_fork_child_refuses_before_inherited_lock():
    import select
    import signal
    import time

    read_fd, write_fd = os.pipe()
    publisher._REGISTRY_LOCK.acquire()
    try:
        pid = os.fork()
    except BaseException:
        publisher._REGISTRY_LOCK.release()
        os.close(read_fd)
        os.close(write_fd)
        raise
    if pid == 0:
        os.close(read_fd)
        try:
            _child_limits()
            checks = []
            for operation in (
                publisher.retry_cleanup,
                lambda: publisher.publish(None, directory="/tmp/private"),
            ):
                try:
                    operation()
                except publisher.PublicationError as exc:
                    checks.append(exc.cleanup is publisher.Cleanup.PENDING)
                else:
                    checks.append(False)
            os.write(write_fd, b"1" if checks == [True, True] else b"0")
        finally:
            os._exit(0)
    os.close(write_fd)
    try:
        readable, _, _ = select.select([read_fd], [], [], 5)
        assert readable and os.read(read_fd, 1) == b"1"
        end = time.monotonic() + 3
        while True:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited:
                pid = None
                break
            if time.monotonic() >= end:
                raise AssertionError("owned child did not exit")
            time.sleep(0.01)
        assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    finally:
        publisher._REGISTRY_LOCK.release()
        os.close(read_fd)
        if pid is not None:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)


@pytest.mark.parametrize("graded,limit", [(False, 1642496), (True, 12582912)])
def test_oversized_payload_refused_before_open(monkeypatch, graded, limit):
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    payload = b"x" * (limit + 1)
    identity = "sha256:" + "0" * 64
    report = (
        Report(payload, identity, identity, 0, 0)
        if graded
        else CohortReport(payload, identity, 0, 0)
    )
    with pytest.raises(publisher.PublicationError):
        publisher.publish(report, directory="/tmp/private")
    assert calls == []


def test_extra_fields_and_subclasses_refused_before_open(monkeypatch):
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    original = _report()
    object.__setattr__(original, "extra", "private")

    class Derived(CohortReport):
        pass

    derived = Derived(b"x", "sha256:" + "0" * 64, 0, 0)
    for report in (original, derived, object()):
        with pytest.raises(publisher.PublicationError) as caught:
            publisher.publish(report, directory="/tmp/private")
        assert str(caught.value) == "private report publication refused"
    assert calls == []


def test_root_replacement_is_refused_before_link(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    moved = tmp_path / "moved"
    real_namespace = publisher._namespace
    calls = 0

    def replace(slot, parts, end):
        nonlocal calls
        calls += 1
        if calls == 2:
            root.rename(moved)
            root.mkdir(mode=0o700)
        return real_namespace(slot, parts, end)

    monkeypatch.setattr(publisher, "_namespace", replace)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert list(root.iterdir()) == []
    assert list(moved.iterdir()) == []


def test_prelink_stage_recheck_refuses_before_link(tmp_path, monkeypatch):
    # Prelink boundary: after staging and the namespace recheck, a mutated
    # retained staged inode (foreign link) is refused by the normative
    # prelink recheck - no link call, exact NOT_PUBLISHED/CLEAN, no entries.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    real_fstat = os.fstat
    stage_fd = []
    counts = {"n": 0}

    def foreign_after_fsync(fd):
        st = real_fstat(fd)
        if not stage_fd and st.st_nlink == 0 and stat.S_ISREG(st.st_mode):
            stage_fd.append(fd)
        if stage_fd and fd == stage_fd[0]:
            counts["n"] += 1
            if counts["n"] >= 3:
                values = list(st)
                values[3] = 1
                return os.stat_result(values)
        return st

    monkeypatch.setattr(os, "fstat", foreign_after_fsync)
    link_calls = []
    real_link = os.link

    def no_link(*args, **kwargs):
        link_calls.append(1)
        return real_link(*args, **kwargs)

    monkeypatch.setattr(os, "link", no_link)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert caught.value.cleanup is publisher.Cleanup.CLEAN
    assert link_calls == []
    assert list(root.iterdir()) == []


def test_deadline_after_prelink_metadata_blocks_link(tmp_path, monkeypatch):
    # Next-boundary deadline check: a controlled clock that expires only
    # after the prelink staged-inode metadata observation must stop the
    # operation before POSSIBLY_PUBLISHED - no link call, honest
    # NOT_PUBLISHED, and the actual bounded product cleanup (never forced
    # CLEAN); exactly one transient jump proves the post-metadata tick.
    import time

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    real_monotonic = time.monotonic
    base = real_monotonic()
    pending_jump = {"n": 0}
    consumed = []

    def fake_monotonic():
        if pending_jump["n"] > 0:
            pending_jump["n"] -= 1
            consumed.append(1)
            return base + 3600.0
        return base

    real_fstat = os.fstat
    stage_fd = []
    counts = {"n": 0}

    def jump_after_stage_recheck(fd):
        st = real_fstat(fd)
        if not stage_fd and st.st_nlink == 0 and stat.S_ISREG(st.st_mode):
            stage_fd.append(fd)
        if stage_fd and fd == stage_fd[0]:
            counts["n"] += 1
            if counts["n"] >= 3:
                pending_jump["n"] = 1
        return st

    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    monkeypatch.setattr(os, "fstat", jump_after_stage_recheck)
    link_calls = []
    real_link = os.link

    def no_link(*args, **kwargs):
        link_calls.append(1)
        return real_link(*args, **kwargs)

    monkeypatch.setattr(os, "link", no_link)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root), deadline_ms=30000)
    assert consumed == [1]
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert caught.value.cleanup is publisher.Cleanup.CLEAN
    assert link_calls == []
    assert list(root.iterdir()) == []


def test_cleanup_cancellation_keeps_identity_and_tombstone(tmp_path):
    # Permanent-uncertainty scenario in a fresh bounded owned exec child:
    # primary KeyboardInterrupt identity and the retained tombstone are
    # asserted inside the child; the direct child teardown is verified, so
    # the main pytest process registry stays clean.
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    completed = subprocess.run(
        [sys.executable, "-c", _CANCEL_TOMBSTONE_CHILD, str(root)],
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr
    assert list(root.iterdir()) == []


def test_pending_slot_never_touches_foreign_entry(tmp_path):
    # Permanent-uncertainty scenario in a fresh bounded owned exec child;
    # the pending slot must never touch the foreign entry, and the retained
    # tombstone stays in the child, not the main process.
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    completed = subprocess.run(
        [sys.executable, "-c", _PENDING_FOREIGN_CHILD, str(root)],
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr
    foreign = root / "foreign-owned"
    assert foreign.read_bytes() == b"foreign synthetic"
    assert sorted(entry.name for entry in root.iterdir()) == ["foreign-owned"]


def test_cancel_priority_and_cleanup_guard_in_fresh_process(tmp_path):
    # Cancellation-priority, non-close cleanup-failure and
    # cleanup/retirement-boundary accounting in a fresh bounded owned
    # exec child: the latched non-Exception primary keeps its exact
    # identity over second cleanup/retirement cancellations, ordinary
    # boundary faults stay content-free, a non-close cleanup failure
    # leaves the slot pending, visible, guard-released with owned
    # cells closeable by retry_cleanup, the guard-release fault is
    # witnessed before and after its effect with exactly one release
    # attempt, and the preserved durable final is inspected exactly,
    # never deleted.
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    completed = subprocess.run(
        [sys.executable, "-c", _CANCEL_PRIORITY_CHILD, str(root)],
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
        preexec_fn=_child_limits,
    )

    assert completed.returncode == 0, completed.stderr
    # The child's durable scenario preserves its final: inspect the
    # exact preserved artifact (64-hex basename, exact synthetic
    # bytes, regular 0400 file), never delete it or erase unknowns.
    identity = "sha256:" + hashlib.sha256(b"slaif-source-cohort-runner-v1\nsynthetic").hexdigest()
    expected_final = "source-" + identity[7:] + ".json"
    entries = sorted(entry.name for entry in root.iterdir())
    assert entries == [expected_final]
    preserved = root / expected_final
    assert preserved.read_bytes() == b"synthetic"
    pst = preserved.stat()
    assert stat.S_ISREG(pst.st_mode)
    assert stat.S_IMODE(pst.st_mode) == 0o400


def test_unknown_exhaustion_refuses_before_further_open(tmp_path):
    # Counted UNKNOWN cells occupy the slot: a fully unknown slot must
    # refuse further opens before any os.open and must not unregister;
    # a slot with one owned cell among unknowns refuses until the owned
    # cell is closed.
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    completed = subprocess.run(
        [sys.executable, "-c", _EXHAUSTION_CHILD, str(root)],
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr
    assert sorted(entry.name for entry in root.iterdir()) == ["owned"]


def test_retry_cleanup_closes_definitely_owned_handles(tmp_path):
    # Quiescent pending slot: the non-reentrant guard is released before the
    # retry, so retry_cleanup genuinely owns the slot it retries; the
    # genuinely owned fd must be closed exactly once by that retry.  No
    # registry-clearing fallback: an unexpected failure stays a failure with
    # truthful ownership.
    owned = tmp_path / "owned"
    owned.write_bytes(b"x")
    slot = publisher._reserve()
    try:
        fd = slot.opened(str(owned), os.O_RDONLY | os.O_CLOEXEC)
    except BaseException:
        slot.guard.release()
        raise
    slot.pending = True
    slot.guard.release()
    receipt = publisher.retry_cleanup()
    assert receipt.attempted == 1
    assert receipt.remaining == 0
    assert receipt.status is publisher.Cleanup.CLEAN
    with pytest.raises(OSError):
        os.fstat(fd)


def test_cleanup_first_interrupt_survives_later_helper_fault(monkeypatch):
    # F20: the first caught per-close cancellation is not lost to a
    # later next-iteration clock fault inside _cleanup: the SAME first
    # object propagates, chained from the later fault; the finite
    # six-cell protocol is unchanged (cell 0 UNKNOWN and counted with
    # its number retained, cell 1 untouched), no retry, and no
    # exception object is stored in the retained slot state.
    import time

    fd_a, fd_b = os.pipe()
    slot = publisher._Slot()
    real_close = os.close
    real_monotonic = time.monotonic
    sentinel = SystemExit(81)
    close_calls = []

    def close_fault(fd):
        close_calls.append(fd)
        if len(close_calls) == 1:
            raise sentinel
        return real_close(fd)

    stage = {"armed": False, "calls": 0}

    def faulting_clock():
        if not stage["armed"]:
            return real_monotonic()
        stage["calls"] += 1
        if stage["calls"] == 2:
            raise RuntimeError(82)
        return real_monotonic()

    try:
        slot.st[0] = publisher._OWNED
        slot.fdn[0] = fd_a
        slot.st[1] = publisher._OWNED
        slot.fdn[1] = fd_b
        monkeypatch.setattr(os, "close", close_fault)
        monkeypatch.setattr(time, "monotonic", faulting_clock)
        end = real_monotonic() + 30
        stage["armed"] = True
        with pytest.raises(SystemExit) as excinfo:
            publisher._cleanup(slot, end)
        stage["armed"] = False
        assert excinfo.value is sentinel
        assert type(excinfo.value.__cause__) is RuntimeError
        assert slot.st[0] == publisher._UNKNOWN and slot.fdn[0] == fd_a
        assert slot.st[1] == publisher._OWNED and slot.fdn[1] == fd_b
        assert close_calls == [fd_a]
        assert not any(isinstance(v, BaseException) for v in vars(slot).values())
    finally:
        for fd in (fd_a, fd_b):
            real_close(fd)


def test_retry_release_faults_keep_conservative_status(monkeypatch):
    # F22: a _release fault is never assumed to have had no effect:
    # before its effect the slot genuinely remains registered, after
    # its effect it is genuinely unregistered; either way the real
    # observed count is preserved with conservative status, exactly
    # one release attempt per pending slot, no reinsertion and no raw
    # ordinary escape; a non-Exception release fault propagates as the
    # SAME caught object with the guard released.
    real_release = publisher._release
    calls = []
    slot_a = slot_b = slot_c = None
    try:

        def release_fault_before(slot_):
            calls.append("before")
            raise OSError("controlled pre-effect release fault")

        monkeypatch.setattr(publisher, "_release", release_fault_before)
        slot_a = publisher._reserve()
        slot_a.guard.release()
        receipt = publisher.retry_cleanup()
        assert receipt.attempted == 1
        assert receipt.remaining == 1
        assert receipt.status is publisher.Cleanup.PENDING
        assert calls == ["before"]
        assert any(current is slot_a for current in publisher._SLOTS)
        assert slot_a.pending
        real_release(slot_a)

        def release_fault_after(slot_):
            calls.append("after")
            real_release(slot_)
            raise OSError("controlled post-effect release fault")

        monkeypatch.setattr(publisher, "_release", release_fault_after)
        slot_b = publisher._reserve()
        slot_b.guard.release()
        receipt = publisher.retry_cleanup()
        assert receipt.attempted == 1
        assert receipt.remaining == 0
        assert receipt.status is publisher.Cleanup.PENDING
        assert calls == ["before", "after"]
        assert not any(current is slot_b for current in publisher._SLOTS)
        cancel = SystemExit(78)

        def release_cancel(slot_):
            calls.append("cancel")
            raise cancel

        monkeypatch.setattr(publisher, "_release", release_cancel)
        slot_c = publisher._reserve()
        slot_c.guard.release()
        with pytest.raises(SystemExit) as excinfo:
            publisher.retry_cleanup()
        assert excinfo.value is cancel
        assert calls == ["before", "after", "cancel"]
        assert any(current is slot_c for current in publisher._SLOTS)
        assert slot_c.pending
        assert slot_c.guard.acquire(blocking=False)
        slot_c.guard.release()
    finally:
        for slot_ in (slot_a, slot_b, slot_c):
            if slot_ is not None and any(current is slot_ for current in publisher._SLOTS):
                real_release(slot_)


def test_slot_enforces_six_descriptor_tokens(tmp_path, monkeypatch):
    owned = tmp_path / "owned"
    owned.write_bytes(b"x")
    slot = publisher._Slot()
    opened = []
    try:
        for _ in range(6):
            opened.append(slot.opened(str(owned), os.O_RDONLY | os.O_CLOEXEC))
        calls = []
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", _never_touch(calls))
            with pytest.raises(publisher._Failure):
                slot.opened(str(owned), os.O_RDONLY)
        assert calls == []
    finally:
        for fd in opened:
            slot.close(fd)
    assert slot._all_free()


def test_opened_tracking_failure_closes_returned_fd(tmp_path, monkeypatch):
    # Close-protocol boundary, witnessed in-process: a definitely stored
    # returned descriptor is marked CLOSING before the close call, and a
    # known successful close clears the numeric cell before FREE.  The
    # unresolved-acquisition and close-uncertain cases run in a fresh
    # bounded owned exec child on the registered production slot path,
    # where the accurate unknown/pending state, the retained global slot
    # and the never-re-closed numeric fd are asserted; the child is owned
    # and reaped directly.
    owned = tmp_path / "owned"
    owned.write_bytes(b"x")
    slot = publisher._Slot()
    fd = slot.opened(str(owned), os.O_RDONLY | os.O_CLOEXEC)
    k = slot._find(fd)
    assert k >= 0 and slot.st[k] == publisher._OWNED and slot.fdn[k] == fd
    real_close = os.close
    order = []

    def witnessing_close(close_fd):
        order.append((close_fd, slot.st[k]))
        return real_close(close_fd)

    with monkeypatch.context() as patch:
        patch.setattr(os, "close", witnessing_close)
        slot.close(fd)
    assert len(order) == 1
    assert order[0] == (fd, publisher._CLOSING)
    assert slot.st[k] == publisher._FREE and slot.fdn[k] == -1

    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    environment = _child_environment()
    completed = subprocess.run(
        [sys.executable, "-c", _TRACKING_FAULT_CHILD, str(root)],
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr
    assert sorted(entry.name for entry in root.iterdir()) == ["owned"]


def test_graded_identity_requires_graded_domain(monkeypatch):
    source = _report()
    graded = Report(source.identity_payload, source.identity, "sha256:" + "0" * 64, 0, 0)
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    with pytest.raises(publisher.PublicationError):
        publisher.publish(graded, directory="/tmp/private")
    assert calls == []


def test_invalid_plan_identity_and_payload_counter(monkeypatch):
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    valid = _report(graded=True)
    for report in (
        Report(valid.identity_payload, valid.identity, "sha256:" + "A" * 64, 0, 0),
        Report(valid.identity_payload, valid.identity, valid.plan_identity, 0, True),
        Report(valid.identity_payload, valid.identity, valid.plan_identity, 0, 268435457),
    ):
        with pytest.raises(publisher.PublicationError):
            publisher.publish(report, directory="/tmp/private")
    assert calls == []


@pytest.mark.parametrize("identical", [True, False])
def test_no_replace_collision_checks_once_and_keeps_final(tmp_path, monkeypatch, identical):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    target = root / ("source-" + report.identity[7:] + ".json")
    attempts = []

    def collision(*args, **kwargs):
        attempts.append(1)
        target.write_bytes(report.identity_payload if identical else b"foreign")
        target.chmod(0o400)
        raise FileExistsError()

    monkeypatch.setattr(os, "link", collision)
    if identical:
        assert publisher.publish(report, directory=str(root)).outcome is publisher.Outcome.EXISTING
    else:
        # Post-attempt incompatible recovery final: the observed
        # FileExistsError is not proof of no effect, so the state
        # retains uncertainty rather than downgrading to CONFLICT.
        with pytest.raises(publisher.PublicationError) as caught:
            publisher.publish(report, directory=str(root))
        assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    assert len(attempts) == 1
    assert list(root.iterdir()) == [target]
    assert target.read_bytes() == (report.identity_payload if identical else b"foreign")


@pytest.mark.parametrize("refuse", ["deadline", "verification"])
def test_real_link_then_fileexists_retains_uncertainty(tmp_path, monkeypatch, refuse):
    # A genuine no-replace link succeeds, then a controlled in-process
    # FileExistsError is raised after the successful call: the observed
    # exception alone does not prove that the link had no effect.  When
    # the deadline or the recovery verification then refuses, the state
    # must remain POSSIBLY_PUBLISHED (no actual signal is involved).
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    real_link = os.link
    real_tick = publisher._tick
    real_verify = publisher._verify
    state = {"linked": False, "verify_calls": 0}

    def collide(*args, **kwargs):
        real_link(*args, **kwargs)
        state["linked"] = True
        raise FileExistsError()

    def guarded_tick(end):
        if state["linked"] and refuse == "deadline":
            raise publisher._Failure()
        return real_tick(end)

    def guarded_verify(slot, name, data, end, **kwargs):
        state["verify_calls"] += 1
        if state["linked"] and state["verify_calls"] >= 2 and refuse == "verification":
            raise publisher._Failure()
        return real_verify(slot, name, data, end, **kwargs)

    monkeypatch.setattr(os, "link", collide)
    monkeypatch.setattr(publisher, "_tick", guarded_tick)
    monkeypatch.setattr(publisher, "_verify", guarded_verify)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert state["linked"]
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    # The genuine link left a complete final: no false-absence claim.
    target = root / ("source-" + report.identity[7:] + ".json")
    assert target.read_bytes() == report.identity_payload


def test_post_attempt_absent_final_retains_uncertainty(tmp_path, monkeypatch):
    # Controlled no-replace fault: the link raises FileExistsError without
    # any entry appearing (final absent before and after).  The post-
    # attempt state retains uncertainty: an observed exception is not
    # proof that no visible entry was ever created.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)

    def collision(*args, **kwargs):
        raise FileExistsError()

    monkeypatch.setattr(os, "link", collision)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    assert list(root.iterdir()) == []


def test_post_attempt_incompatible_final_retains_uncertainty(tmp_path, monkeypatch):
    # A foreign incompatible final appears between the pre-attempt check
    # and the link (controlled same-UID fixture, not an adversarial proof):
    # recovery verification refuses it, and the post-attempt state retains
    # uncertainty rather than CONFLICT or NOT_PUBLISHED.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    target = root / ("source-" + report.identity[7:] + ".json")

    def racing_collision(*args, **kwargs):
        target.write_bytes(b"foreign")
        target.chmod(0o400)
        raise FileExistsError()

    monkeypatch.setattr(os, "link", racing_collision)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    assert target.read_bytes() == b"foreign"


def test_own_publication_identity_mismatch_refuses_before_durable(tmp_path, monkeypatch):
    # Clean own publication: the genuine stage inode is linked under an
    # alias (so the stage nlink-1 precheck passes) while the final name is
    # held by a DIFFERENT inode with exactly the admitted bytes.  Byte
    # equality alone is insufficient: the held final descriptor must be
    # exactly the retained fsynced staging inode, so the call refuses
    # before DURABLE and retains uncertainty.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    final_name = "source-" + report.identity[7:] + ".json"
    alias_name = final_name + ".alias"
    real_link = os.link

    def alias_only(src, dst, **kwargs):
        real_link(src, alias_name, **kwargs)
        (root / final_name).write_bytes(report.identity_payload)
        (root / final_name).chmod(0o400)

    monkeypatch.setattr(os, "link", alias_only)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    assert (root / final_name).read_bytes() == report.identity_payload
    # No DURABLE: the final entry is not the stage inode (alias is).
    assert os.lstat(str(root / final_name)).st_ino != os.lstat(str(root / alias_name)).st_ino


@pytest.mark.parametrize("branch", ["pre_attempt", "recovery"])
def test_generic_identical_existing_different_inode_succeeds(tmp_path, monkeypatch, branch):
    # A different valid inode holds exactly the admitted bytes: generic
    # existing/recovery verification deliberately accepts it (it must not
    # require every existing artifact to be this call's stage), performs
    # the held-file flush, and returns EXISTING with DURABLE.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    target = root / ("source-" + report.identity[7:] + ".json")
    if branch == "pre_attempt":
        target.write_bytes(report.identity_payload)
        target.chmod(0o400)
    else:

        def collision(*args, **kwargs):
            target.write_bytes(report.identity_payload)
            target.chmod(0o400)
            raise FileExistsError()

        monkeypatch.setattr(os, "link", collision)
    receipt = publisher.publish(report, directory=str(root))
    assert receipt.outcome is publisher.Outcome.EXISTING
    assert receipt.durability is publisher.Publication.DURABLE
    assert receipt.cleanup is publisher.Cleanup.CLEAN
    assert target.read_bytes() == report.identity_payload


@pytest.mark.parametrize("branch", ["pre_attempt", "recovery"])
def test_existing_file_fsync_refusal_stops_before_durable(tmp_path, monkeypatch, branch):
    # The NEW verified-file flush (distinct from the stage flush and the
    # directory flush) fails: the refusal must happen before any DURABLE
    # latch, with the final untouched.  Pre-attempt the state is
    # NOT_PUBLISHED; after an attempt it retains uncertainty.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    target = root / ("source-" + report.identity[7:] + ".json")
    final_identity = {}
    if branch == "pre_attempt":
        target.write_bytes(report.identity_payload)
        target.chmod(0o400)
        st = target.stat()
        final_identity["id"] = (st.st_dev, st.st_ino)
    else:

        def collision(*args, **kwargs):
            target.write_bytes(report.identity_payload)
            target.chmod(0o400)
            st = target.stat()
            final_identity["id"] = (st.st_dev, st.st_ino)
            raise FileExistsError()

        monkeypatch.setattr(os, "link", collision)
    real_fsync = os.fsync
    witness = {"target": False, "other": 0}

    def fail_file_flush(fd):
        # Target only the verified final descriptor; the genuine stage
        # flush passes through the real original and is counted.  No
        # directory flush occurs before the refusal.
        st = os.fstat(fd)
        if final_identity and (st.st_dev, st.st_ino) == final_identity["id"]:
            witness["target"] = True
            raise OSError("controlled file fsync fault")
        witness["other"] += 1
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fail_file_flush)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    expected = (
        publisher.Publication.NOT_PUBLISHED
        if branch == "pre_attempt"
        else publisher.Publication.POSSIBLY_PUBLISHED
    )
    assert caught.value.publication is expected
    # Explicit target-flush-attempt witness: the refusal fired on the
    # verified final descriptor itself, not on another flush.
    assert witness["target"] is True
    # Stage flush passed before the attempt (recovery branch only).
    assert witness["other"] == (0 if branch == "pre_attempt" else 1)
    assert target.read_bytes() == report.identity_payload


@pytest.mark.parametrize(
    ("branch", "kind"),
    [
        ("pre_attempt", "stability"),
        ("pre_attempt", "deadline"),
        ("recovery", "stability"),
        ("recovery", "deadline"),
    ],
)
def test_post_flush_failure_after_verified_file_flush(tmp_path, monkeypatch, branch, kind):
    # A controlled own-file timestamp mutation (stability kind: real
    # os.utime ns= on the owned fixture, performed exactly after the
    # observed verified-file fsync succeeds) or a deadline expiry
    # (deadline kind: tick guard armed only after that successful
    # flush) then refuses before DURABLE.  Pre-attempt
    # stability is CONFLICT and pre-attempt deadline is NOT_PUBLISHED;
    # any post-attempt refusal retains uncertainty.  The reached markers
    # prove the refusal happened AFTER the target flush, so no earlier
    # refusal can satisfy this test.  Controlled model, not actual
    # scheduler or power-loss behavior.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    target = root / ("source-" + report.identity[7:] + ".json")
    final_identity = {}
    if branch == "pre_attempt":
        target.write_bytes(report.identity_payload)
        target.chmod(0o400)
        st = target.stat()
        final_identity["id"] = (st.st_dev, st.st_ino)
    else:

        def collision(*args, **kwargs):
            target.write_bytes(report.identity_payload)
            target.chmod(0o400)
            st = target.stat()
            final_identity["id"] = (st.st_dev, st.st_ino)
            raise FileExistsError()

        monkeypatch.setattr(os, "link", collision)
    real_fstat = os.fstat
    real_fsync = os.fsync
    real_tick = publisher._tick
    state = {
        "flushed": False,
        "mutated": False,
        "late_raised": False,
        "meta_before": None,
        "meta_after": None,
    }

    def watch_fsync(fd):
        st = real_fstat(fd)
        if final_identity and (st.st_dev, st.st_ino) == final_identity["id"]:
            result = real_fsync(fd)
            state["flushed"] = True
            if kind == "stability" and not state["mutated"]:
                # Controlled own-file timestamp mutation, ordered after
                # the successful observed target flush: real os.utime
                # ns= moves mtime +1 s (mtime_ns +1e9); a real utime
                # also updates ctime, so no ctime claim is made.
                before = real_fstat(fd)
                os.utime(
                    str(target),
                    ns=(before.st_atime_ns, before.st_mtime_ns + 1000000000),
                )
                state["meta_before"] = before
                state["meta_after"] = real_fstat(fd)
                state["mutated"] = True
            return result
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", watch_fsync)
    if kind == "deadline":

        def late_tick(end):
            if state["flushed"]:
                state["late_raised"] = True
                raise publisher._Failure()
            return real_tick(end)

        monkeypatch.setattr(publisher, "_tick", late_tick)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    if branch == "pre_attempt":
        expected = (
            publisher.Publication.CONFLICT
            if kind == "stability"
            else publisher.Publication.NOT_PUBLISHED
        )
    else:
        expected = publisher.Publication.POSSIBLY_PUBLISHED
    assert caught.value.publication is expected
    # The verified-file flush was reached before the refusal.
    assert state["flushed"] is True
    if kind == "stability":
        assert state["mutated"] is True
        mb, ma = state["meta_before"], state["meta_after"]
        assert mb.st_dev == ma.st_dev and mb.st_ino == ma.st_ino
        assert ma.st_mtime_ns == mb.st_mtime_ns + 1000000000
        assert ma.st_atime_ns == mb.st_atime_ns
    else:
        assert state["late_raised"] is True


def test_fsync_census_stage_directory_and_existing_file(tmp_path, monkeypatch):
    # Distinguishing census: a fresh publication performs exactly one
    # stage-file flush and one directory flush; a second identical call
    # performs the NEW existing-file flush plus one directory flush and no
    # stage flush.  No zero-total-fsync claim is made for either call.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    real_fsync = os.fsync
    kinds = []

    def count(fd):
        st = os.fstat(fd)
        kinds.append("reg" if stat.S_ISREG(st.st_mode) else "dir")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", count)
    first_receipt = publisher.publish(report, directory=str(root))
    assert first_receipt.outcome is publisher.Outcome.PUBLISHED
    first = list(kinds)
    kinds.clear()
    second_receipt = publisher.publish(report, directory=str(root))
    assert second_receipt.outcome is publisher.Outcome.EXISTING
    second = list(kinds)
    assert first == ["reg", "dir"]
    assert second == ["reg", "dir"]


def test_public_receipt_and_error_hide_private_content(tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report(b"sensitive synthetic marker")
    result = publisher.publish(report, directory=str(root))
    assert report.identity not in repr(result)
    assert "sensitive synthetic marker" not in repr(result)
    with pytest.raises((AttributeError, TypeError)):
        result.cleanup = publisher.Cleanup.PENDING
    with pytest.raises(AttributeError):
        object.__setattr__(result, "extra", "private")
    error = publisher.PublicationError(publisher.Publication.CONFLICT, publisher.Cleanup.CLEAN)
    assert str(error) == "private report publication refused"
    with pytest.raises(AttributeError):
        error.publication = publisher.Publication.DURABLE


def test_wrong_root_owner_is_controlled_metadata_refusal(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    root_identity = (root.stat().st_dev, root.stat().st_ino)
    real_fstat = os.fstat

    def wrong_owner(fd):
        original = real_fstat(fd)
        if (original.st_dev, original.st_ino) == root_identity:
            values = list(original)
            values[4] = os.geteuid() + 12345
            return os.stat_result(values)
        return original

    monkeypatch.setattr(os, "fstat", wrong_owner)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory=str(root))
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert list(root.iterdir()) == []


def test_link_succeeds_then_raises_keeps_complete_final(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    report = _report()
    real_link = os.link

    def uncertain(*args, **kwargs):
        real_link(*args, **kwargs)
        raise OSError("controlled post-link fault")

    monkeypatch.setattr(os, "link", uncertain)
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    files = list(root.iterdir())
    assert len(files) == 1
    assert files[0].read_bytes() == report.identity_payload


def test_failed_final_verification_stays_uncertain(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    real_verify = publisher._verify
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise publisher._Conflict()
        return real_verify(*args, **kwargs)

    monkeypatch.setattr(publisher, "_verify", fail_second)
    report = _report()
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.POSSIBLY_PUBLISHED
    assert next(root.iterdir()).read_bytes() == report.identity_payload


def test_surrogate_path_error_has_no_raw_context():
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory="/tmp/\ud800")
    assert caught.value.__context__ is None
    assert str(caught.value) == "private report publication refused"


def test_untrusted_writable_ancestor_refuses(tmp_path):
    ancestor = tmp_path / "writable"
    ancestor.mkdir(mode=0o700)
    root = ancestor / "private"
    root.mkdir(mode=0o700)
    ancestor.chmod(0o777)
    try:
        with pytest.raises(publisher.PublicationError) as caught:
            publisher.publish(_report(), directory=str(root))
        assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
        assert list(root.iterdir()) == []
    finally:
        ancestor.chmod(0o700)


def test_late_deadline_after_durable_is_not_false_absence(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    real_tick = publisher._tick

    def late(end):
        if any(
            slot is not None and slot.state is publisher.Publication.DURABLE
            for slot in publisher._SLOTS
        ):
            raise publisher._Failure()
        real_tick(end)

    monkeypatch.setattr(publisher, "_tick", late)
    report = _report()
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(report, directory=str(root))
    assert caught.value.publication is publisher.Publication.DURABLE
    assert caught.value.cleanup is publisher.Cleanup.CLEAN
    assert next(root.iterdir()).read_bytes() == report.identity_payload


@pytest.mark.parametrize("graded,limit", [(False, 1642496), (True, 12582912)])
def test_exact_payload_cap_is_admitted(tmp_path, graded, limit):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    payload = b"x" * limit
    domain = (
        b"slaif-graded-evaluation-program-v1\n" if graded else b"slaif-source-cohort-runner-v1\n"
    )
    digest = hashlib.sha256(domain)
    digest.update(payload)
    identity = "sha256:" + digest.hexdigest()
    report = (
        Report(payload, identity, "sha256:" + "0" * 64, 0, 0)
        if graded
        else CohortReport(payload, identity, 0, 0)
    )
    receipt = publisher.publish(report, directory=str(root))
    assert receipt.outcome is publisher.Outcome.PUBLISHED
    target = next(root.iterdir())
    assert target.stat().st_size == limit


def test_deadline_expires_before_filesystem_access(monkeypatch):
    clock = iter((0.0, 1.0))
    monkeypatch.setattr(publisher.time, "monotonic", lambda: next(clock))
    calls = []
    monkeypatch.setattr(os, "open", _never_touch(calls))
    with pytest.raises(publisher.PublicationError) as caught:
        publisher.publish(_report(), directory="/tmp/private", deadline_ms=1)
    assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert calls == []


def test_global_ninety_six_descriptor_bound(tmp_path, monkeypatch):
    owned = tmp_path / "owned"
    owned.write_bytes(b"x")
    slots = []
    try:
        for _ in range(16):
            slot = publisher._reserve()
            slots.append(slot)
            for _ in range(6):
                slot.opened(str(owned), os.O_RDONLY | os.O_CLOEXEC)
        assert sum(slot._occupied() for slot in slots) == 96
        calls = []
        with monkeypatch.context() as patch:
            patch.setattr(os, "open", _never_touch(calls))
            with pytest.raises(publisher.PublicationError):
                publisher.publish(_report(), directory="/tmp/private")
        assert calls == []
    finally:
        for slot in slots:
            for k in range(6):
                if slot.st[k] in (publisher._PRE, publisher._OWNED) and slot.fdn[k] >= 0:
                    slot.close(slot.fdn[k])
            publisher._release(slot)
            slot.guard.release()


def test_seventeen_fresh_publications_release_pool(tmp_path):
    # Repeated ordinary publication must not consume permanent unknown
    # slots: seventeen fresh publications in ONE process, each
    # unregistering its slot when every token is definitely FREE.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    for index in range(17):
        report = _report(b"payload-%02d" % index)
        assert publisher.publish(report, directory=str(root)).outcome is publisher.Outcome.PUBLISHED
    assert all(slot is None for slot in publisher._SLOTS)
    receipt = publisher.retry_cleanup()
    assert receipt.attempted == 0
    assert receipt.remaining == 0
    assert receipt.status is publisher.Cleanup.CLEAN
    assert len(list(root.iterdir())) == 17


def test_final_state_loaded_origins_restored():
    # Final restored-state origin guard: default-collected at module end, so
    # it runs last after every fault case; the actual loaded product/test
    # origins must still be real files under the assigned worktree - no
    # sys.path/sys.modules drift is tolerated.
    test_path = os.path.realpath(os.path.abspath(__file__))
    checkout_root = os.path.realpath(os.path.join(os.path.dirname(test_path), "..", ".."))
    _assert_loaded_origins(checkout_root)
