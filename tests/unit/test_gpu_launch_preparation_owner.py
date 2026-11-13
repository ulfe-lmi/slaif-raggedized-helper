import os
import shutil

import pytest

from slaif_raggedized_helper import gpu_worker_launch as launch
from test_gpu_worker_launch import _prepared_fixture


def test_success_handoff_and_one_use(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    try:
        prepared = launch.prepare(**args, preparation_owner=capture)
        try:
            assert capture.pending
            assert capture.prepared is prepared
            assert prepared._owner is launch.PreparationOwner._record(capture)[1]
            prepared.revalidate()
            with pytest.raises(launch.LaunchRefused):
                capture.close()
            with pytest.raises(launch.LaunchRefused):
                launch.prepare(**args, preparation_owner=capture)
            reservation.assert_owned()
        finally:
            prepared.close()
        assert not capture.pending
        capture.close()
        reservation.assert_owned()
    finally:
        reservation.close()


def _fail_with_capsule(args, capture, monkeypatch, error):
    original_revalidate = launch.PreparedLaunch.revalidate
    original_rmtree = shutil.rmtree
    def fail_revalidate(self):
        raise error
    def fail_rmtree(path, *a, **kw):
        raise OSError('controlled cleanup failure')
    with monkeypatch.context() as m:
        m.setattr(launch.PreparedLaunch, 'revalidate', fail_revalidate)
        m.setattr(shutil, 'rmtree', fail_rmtree)
        with pytest.raises(type(error)) as caught:
            launch.prepare(**args, preparation_owner=capture)
        if not isinstance(error, Exception):
            assert caught.value is error
    assert launch.PreparedLaunch.revalidate is original_revalidate
    assert shutil.rmtree is original_rmtree
    assert capture.pending
    assert capture.prepared is None
    owner = launch.PreparationOwner._record(capture)[1]
    assert owner.directory is not None and os.path.isdir(owner.directory)
    return owner


def test_interleaved_actual_failure_association(tmp_path, monkeypatch):
    a, b = tmp_path / 'a', tmp_path / 'b'
    a.mkdir()
    b.mkdir()
    args_a, reservation_a = _prepared_fixture(a, monkeypatch)
    args_b, reservation_b = _prepared_fixture(b, monkeypatch)
    capture_a, capture_b = launch.PreparationOwner(), launch.PreparationOwner()
    try:
        owner_a = _fail_with_capsule(args_a, capture_a, monkeypatch, ValueError())
        owner_b = _fail_with_capsule(args_b, capture_b, monkeypatch, ValueError())
        path_a, path_b = owner_a.directory, owner_b.directory
        assert owner_a is not owner_b
        capture_a.close()
        assert not os.path.exists(path_a) and os.path.isdir(path_b) and capture_b.pending
        capture_b.close()
        assert not os.path.exists(path_b) and not capture_b.pending
    finally:
        reservation_a.close()
        reservation_b.close()


def test_hostile_interruption_retains_association(tmp_path, monkeypatch):
    class Hostile(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError('no attributes')
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    try:
        _fail_with_capsule(args, capture, monkeypatch, Hostile())
        capture.close()
        assert not capture.pending
    finally:
        reservation.close()


def test_cleanup_interrupt_priority(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    class Interrupt(BaseException):
        pass
    interrupt = Interrupt()
    try:
        with monkeypatch.context() as m:
            m.setattr(launch.PreparedLaunch, 'revalidate',
                      lambda self: (_ for _ in ()).throw(ValueError()))
            m.setattr(shutil, 'rmtree', lambda *a, **k: (_ for _ in ()).throw(interrupt))
            with pytest.raises(Interrupt) as caught:
                launch.prepare(**args, preparation_owner=capture)
            assert caught.value is interrupt
        assert capture.pending
        capture.close()
    finally:
        reservation.close()


def test_forged_closed_busy_and_fork_refusal(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    forged = object.__new__(launch.PreparationOwner)
    try:
        for invalid in (forged, object()):
            with pytest.raises(launch.LaunchRefused):
                launch.prepare(**args, preparation_owner=invalid)
            with pytest.raises(launch.LaunchRefused):
                launch.PreparationOwner.close(invalid)
        record = launch.PreparationOwner._record(capture)
        assert record[3].acquire(False)
        try:
            with pytest.raises(launch.LaunchRefused):
                capture.close()
            with pytest.raises(launch.LaunchRefused):
                _ = capture.prepared
            with pytest.raises(launch.LaunchRefused):
                launch.prepare(**args, preparation_owner=capture)
        finally:
            record[3].release()
        launch._preparation_records_lock.acquire()
        pid = os.fork()
        if pid == 0:
            try:
                _ = capture.prepared
            except launch.LaunchRefused:
                os._exit(0)
            os._exit(1)
        launch._preparation_records_lock.release()
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        capture.close()
        with pytest.raises(launch.LaunchRefused):
            launch.prepare(**args, preparation_owner=capture)
    finally:
        reservation.close()


def test_uncertain_fd_never_retried(monkeypatch):
    capture = launch.PreparationOwner()
    owner = launch.PreparationOwner._record(capture)[1]
    fd = owner.add(os.open('/dev/null', os.O_RDONLY))
    real_close = os.close
    def close_then_raise(number):
        real_close(number)
        if number == fd:
            raise OSError('uncertain')
    with monkeypatch.context() as m:
        m.setattr(os, 'close', close_then_raise)
        with pytest.raises(launch.LaunchRefused):
            capture.close()
    reused = os.open('/dev/null', os.O_RDONLY)
    try:
        assert reused == fd
        with pytest.raises(launch.LaunchRefused):
            capture.close()
        os.fstat(reused)
        assert capture.pending and owner.unknown_fd
    finally:
        real_close(reused)


def test_actual_one_use_guard_control(tmp_path, monkeypatch):
    import ast
    import inspect

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    capture.close()
    try:
        with pytest.raises(launch.LaunchRefused):
            launch.prepare(**args, preparation_owner=capture)
        tree = ast.parse(inspect.getsource(launch.prepare))
        function = tree.body[0]
        outer = next(node for node in function.body if isinstance(node, ast.If))
        guard = next(node for node in outer.body if isinstance(node, ast.If)
                     and "record[2] != 'unused'" in ast.unparse(node.test))
        outer.body.remove(guard)
        ast.fix_missing_locations(tree)
        namespace = dict(launch.__dict__)
        exec(compile(tree, '<one-use-control>', 'exec'), namespace)
        prepared = namespace['prepare'](**args, preparation_owner=capture)
        try:
            assert prepared._owner is launch.PreparationOwner._record(capture)[1]
        finally:
            prepared.close()
    finally:
        reservation.close()


def test_original_interruption_outranks_cleanup_interrupt(tmp_path, monkeypatch):
    class Interrupt(BaseException):
        pass
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    original, cleanup = Interrupt(), Interrupt()
    try:
        with monkeypatch.context() as m:
            m.setattr(launch.PreparedLaunch, 'revalidate',
                      lambda self: (_ for _ in ()).throw(original))
            m.setattr(shutil, 'rmtree', lambda *a, **k: (_ for _ in ()).throw(cleanup))
            with pytest.raises(Interrupt) as caught:
                launch.prepare(**args, preparation_owner=capture)
            assert caught.value is original
        capture.close()
    finally:
        reservation.close()


def test_capture_cannot_be_reinitialized_or_mutated():
    capture = launch.PreparationOwner()
    with pytest.raises(launch.LaunchRefused):
        capture.__init__()
    with pytest.raises(AttributeError):
        capture.owner = object()
    capture.close()


def test_return_interruption_recovers_actual_handoff(tmp_path, monkeypatch):
    import inspect
    import sys

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    lines, start = inspect.getsourcelines(launch.prepare)
    targets = [start + i for i, line in enumerate(lines) if line.strip() == 'return result']
    assert len(targets) == 1

    class Interrupt(BaseException):
        pass

    marker = Interrupt()

    def stop(frame, event, arg):
        if (frame.f_code is launch.prepare.__code__ and event == 'line'
                and frame.f_lineno == targets[0]):
            raise marker
        return stop

    try:
        assert capture.prepared is None
        sys.settrace(stop)
        try:
            with pytest.raises(Interrupt) as caught:
                launch.prepare(**args, preparation_owner=capture)
            assert caught.value is marker
        finally:
            sys.settrace(None)
        prepared = capture.prepared
        assert type(prepared) is launch.PreparedLaunch
        assert prepared._owner is launch.PreparationOwner._record(capture)[1]
        assert capture.pending
        with pytest.raises(launch.LaunchRefused):
            capture.close()
        prepared.close()
        assert not capture.pending
        reservation.assert_owned()
    finally:
        sys.settrace(None)
        reservation.close()
