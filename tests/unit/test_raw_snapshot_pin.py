"""Owner admission and cleanup contracts, without integration fixture imports."""

import os

import pytest

from slaif_raggedized_helper import raw_snapshot_pin as pin
from slaif_raggedized_helper import raw_snapshot_selection as selection


def test_one_attempt_and_idempotent_close():
    owner = pin.PinOwner()
    with pytest.raises(pin.PinError):
        owner.acquire_selected_data(None, None, "/tmp")
    assert owner.state == "CLOSED"
    with pytest.raises(pin.PinError):
        owner.acquire_selected_data(None, None, "/tmp")
    owner.close()
    owner.close()


def test_busy_guard_and_fork_identity():
    owner = pin.PinOwner()
    owner.guard.acquire()
    try:
        with pytest.raises(pin.PinError):
            owner.close()
    finally:
        owner.guard.release()
    owner.pid = -1
    with pytest.raises(pin.PinError):
        owner.close()


def test_uncertain_close_is_not_retried(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    owner = pin.PinOwner()
    owner.op = selection._Operation(str(tmp_path), 30000)
    owner.op.guard.release()
    fd = owner.op.owner.open(str(tmp_path), os.O_RDONLY | os.O_DIRECTORY)
    owner.state = "ACTIVE"
    real_close = os.close
    calls = []

    def uncertain(number):
        calls.append(number)
        real_close(number)
        raise OSError("unknown result")

    monkeypatch.setattr(os, "close", uncertain)
    with pytest.raises(pin.PinError):
        owner.close()
    assert owner.state == "CLEANUP_PENDING" and calls == [fd]
    with pytest.raises(selection.CleanupPendingError):
        owner.close()
    assert calls == [fd]


def test_hostile_base_exception_identity(monkeypatch):
    class Hostile(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError("no attributes")

    marker = Hostile()
    owner = pin.PinOwner()

    def interrupt(*args):
        raise marker

    monkeypatch.setattr(pin, "_admit", interrupt)
    with pytest.raises(Hostile) as caught:
        owner.acquire_selected_data(None, None, "/tmp")
    assert caught.value is marker and owner.state == "CLOSED"


def test_cleanup_interrupt_takes_priority_over_ordinary_error(monkeypatch):
    class Interrupt(BaseException):
        pass

    marker = Interrupt()
    owner = pin.PinOwner()

    def failed_admission(*args):
        raise ValueError("ordinary")

    def interrupted_cleanup():
        raise marker

    monkeypatch.setattr(pin, "_admit", failed_admission)
    monkeypatch.setattr(owner, "_cleanup", interrupted_cleanup)
    with pytest.raises(Interrupt) as caught:
        owner.acquire_selected_data(None, None, "/tmp")
    assert caught.value is marker and owner.state == "CLEANUP_PENDING"


def test_second_acquire_does_not_close_live_owner(tmp_path):
    tmp_path.chmod(0o700)
    owner = pin.PinOwner()
    owner.op = selection._Operation(str(tmp_path), 30000)
    owner.op.guard.release()
    fd = owner.op.owner.open(str(tmp_path), os.O_RDONLY | os.O_DIRECTORY)
    owner.state = "ACTIVE"
    with pytest.raises(pin.PinError):
        owner.acquire_selected_data(None, None, "/tmp")
    assert owner.state == "ACTIVE" and os.fstat(fd)
    owner.close()


def test_interrupted_close_marks_pending(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    owner = pin.PinOwner()
    owner.op = selection._Operation(str(tmp_path), 30000)
    owner.op.guard.release()
    owner.state = "ACTIVE"
    marker = KeyboardInterrupt()

    def interrupt():
        raise marker

    monkeypatch.setattr(owner.op, "cleanup", interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        owner.close()
    assert caught.value is marker and owner.state == "CLEANUP_PENDING"


def test_owner_subclasses_refused():
    with pytest.raises(TypeError):

        class ReaderSubclass(pin.PinOwner):
            pass

    with pytest.raises(TypeError):

        class RetirementSubclass(pin.RetirementOwner):
            pass
