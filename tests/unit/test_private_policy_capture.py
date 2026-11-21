"""Private offline policy wire capture evidence.

Offline and fully synthetic: every root is a private temporary directory
owned by the test and every byte is generated here; no real protected
path, credential, network route, model or service is touched.  The
test-side canonical emitter is an independent re-derivation, so the
reader is never its own oracle.  Descriptor faults and deadline
cooperation are measured through test-local narrowly delegated fault
witnesses on the real descriptor primitives and a controlled monotone
clock; no real wall behavior is described as a hard guarantee.
"""

import dataclasses
import inspect
import hashlib
import json
import os
import time
import threading
from pathlib import Path

import pytest

from slaif_raggedized_helper import policy_selection as selection
from slaif_raggedized_helper import private_policy_capture as capture
from slaif_raggedized_helper import private_report_publication as publication

_KIND = "slaif-current-policy-selection-v1"
_SELECTION = "current-policy.json"
_PAYLOAD = b"slaif-private-policy-wire-" * 4  # 104 synthetic bytes
_MAX_PAYLOAD = 67108864


class _Interrupt(BaseException):
    """Test-side non-Exception interrupt sentinel."""


def _render_selection(generation, wire_bytes, wire_sha256):
    return json.dumps(
        {
            "generation": generation,
            "kind": _KIND,
            "schema": 1,
            "wire_bytes": wire_bytes,
            "wire_sha256": wire_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _write_private(path, data, mode=0o400):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(str(path), mode)


def _make_root(directory, generation, payload, *, selection_bytes=None,
               payload_name=None, payload_content=None, write_payload=True):
    directory = Path(directory)
    directory.mkdir(mode=0o700)
    os.chmod(str(directory), 0o700)
    digest = hashlib.sha256(payload).hexdigest()
    if selection_bytes is None:
        selection_bytes = _render_selection(generation, len(payload), digest)
    _write_private(directory / _SELECTION, selection_bytes)
    if write_payload:
        _write_private(
            directory / (payload_name or digest + ".bin"),
            payload if payload_content is None else payload_content,
        )
    return directory


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _install(monkeypatch, name, action=None, match=None):
    """Test-local narrowly delegated fault witness: records every call,
    runs an optional bounded fixture action at matched calls, and always
    delegates to the real descriptor primitive."""
    real = getattr(os, name)
    state = {"calls": []}

    def witness(*args, **kwargs):
        state["calls"].append((args, kwargs))
        if action is not None and (match is None or match(args, kwargs)):
            action(*args, **kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(os, name, witness)
    return state


def _is_fd_of(fd, dev_ino):
    try:
        st = os.fstat(fd)
    except OSError:
        return False
    return (st.st_dev, st.st_ino) == dev_ino


def test_module_origin_is_assigned_worktree():
    # Portable guard derived from the resolved physical test path: both
    # modules originate from real files under the assigned worktree.
    root = Path(__file__).resolve().parents[2]
    assert Path(__file__).resolve() == root / "tests/unit/test_private_policy_capture.py"
    assert (
        Path(capture.__file__).resolve()
        == root / "src/slaif_raggedized_helper/private_policy_capture.py"
    )


def test_public_api_surface():
    assert capture.__all__ == [
        "CapturedPolicyBytes",
        "PolicyCaptureError",
        "PolicyCaptureReader",
    ]
    # No path, selection or snapshot entry in either operation signature:
    # the root comes from the trusted private constructor only.
    for operation in ("read_selection", "capture"):
        params = inspect.signature(
            getattr(capture.PolicyCaptureReader, operation)
        ).parameters
        assert tuple(params) == ("self", "deadline_ms")
        assert params["deadline_ms"].kind is inspect.Parameter.KEYWORD_ONLY
        assert params["deadline_ms"].default == 30000


def test_error_is_fixed_input_free_value_error():
    err = capture.PolicyCaptureError()
    assert type(err) is capture.PolicyCaptureError
    assert isinstance(err, ValueError)
    assert str(err) == "private policy capture refused"
    assert err.args == ("private policy capture refused",)
    assert err.__cause__ is None and err.__context__ is None
    # No partial result or input echo escapes the boundary.
    for name in ("root", "path", "selection", "wire_bytes", "data", "bytes", "fd"):
        assert not hasattr(err, name)
    assert b"current-policy" not in repr(err).encode("ascii", "replace")


def test_captured_record_is_frozen_nominal(tmp_path):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    cap = capture.PolicyCaptureReader(str(root)).capture()
    assert type(cap) is capture.CapturedPolicyBytes
    assert dataclasses.is_dataclass(cap) and cap.__dataclass_params__.frozen is True
    assert [field.name for field in dataclasses.fields(cap)] == [
        "selection",
        "wire_bytes",
    ]
    assert isinstance(cap.selection, selection.PolicySelection)
    assert type(cap.wire_bytes) is bytes
    with pytest.raises(dataclasses.FrozenInstanceError):
        cap.selection = cap.selection
    with pytest.raises(dataclasses.FrozenInstanceError):
        cap.wire_bytes = b""
    # No persisted dev/inode or other descriptor state in the record.
    for name in ("st_dev", "st_ino", "dev", "ino", "mode", "nlink", "size"):
        assert not hasattr(cap, name)


@pytest.mark.parametrize(
    ("root", "case"),
    [
        ("relative/root", "relative"),
        ("/", "root"),
        ("", "empty"),
        ("/a/b/", "trailing-slash"),
        ("/a/./b", "dot-component"),
        ("/a/../b", "dotdot-component"),
        ("/a\x01b", "control"),
        (b"/a/b", "bytes"),
        (None, "none"),
        (123, "int"),
        ("/" + "a" * 4096, "over-long"),
        ("/" + "/".join("a" * 65), "65-components"),
        ("/" + "\u00e9" * 200, "wide-component"),
        ("/\ud800", "malformed-utf8"),
        ("/\ud800" + "a" * 5000, "long-malformed"),
    ],
    ids=["relative", "root", "empty", "trailing-slash", "dot-component",
         "dotdot-component", "control", "bytes", "none", "int", "over-long",
         "65-components", "wide-component", "malformed-utf8",
         "long-malformed"],
)
def test_constructor_refuses_invalid_roots(root, case):
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(root)


def test_malformed_utf8_root_refused_without_context():
    with pytest.raises(capture.PolicyCaptureError) as exc:
        capture.PolicyCaptureReader("/\ud800")
    assert exc.value.__cause__ is None and exc.value.__context__ is None
    assert "surrogate" not in repr(exc.value).lower()


def test_constructor_accepts_boundary_length_root():
    root = "/" + "/".join("a" * 255 for _ in range(16))
    assert len(root.encode("utf-8")) == 4096  # exactly the 4096-byte limit
    reader = capture.PolicyCaptureReader(root)
    assert reader._root == root


def test_valid_current_observation_and_capture(tmp_path):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    sel = reader.read_selection()
    assert type(sel) is selection.PolicySelection
    assert sel.selection_bytes == _render_selection(1, len(_PAYLOAD), _digest(_PAYLOAD))
    assert (sel.generation, sel.wire_bytes, sel.wire_sha256) == (
        1,
        len(_PAYLOAD),
        _digest(_PAYLOAD),
    )
    cap = reader.capture()
    assert cap.selection.selection_bytes == sel.selection_bytes
    assert cap.selection.generation == 1
    assert cap.wire_bytes == _PAYLOAD
    # The same reader remains available for later operations.
    assert reader.read_selection().generation == 1


def test_real_descriptor_ownership(tmp_path, monkeypatch):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    opened = {}
    closed = []
    real_open = os.open
    real_close = os.close

    def spy_open(*args, **kwargs):
        fd = real_open(*args, **kwargs)
        if args and args[0] == _SELECTION:
            opened["selection"] = fd
        return fd

    def spy_close(fd, *args, **kwargs):
        closed.append(fd)
        return real_close(fd, *args, **kwargs)

    monkeypatch.setattr(os, "open", spy_open)
    monkeypatch.setattr(os, "close", spy_close)
    reader = capture.PolicyCaptureReader(str(root))
    assert reader.read_selection().generation == 1
    # Real fd ownership: the reader opened the entry through the slot and
    # the close protocol retired exactly that descriptor.
    assert "selection" in opened
    assert opened["selection"] in closed
    assert all(fd >= 0 for fd in closed)


def test_reader_bound_to_own_root(tmp_path):
    payload_a = b"slaif-root-a-wire-bytes-" * 4
    payload_b = b"slaif-root-b-wire-bytes-" * 4
    root_a = _make_root(tmp_path / "a", 1, payload_a)
    root_b = _make_root(tmp_path / "b", 2, payload_b)
    cap_a = capture.PolicyCaptureReader(str(root_a)).capture()
    cap_b = capture.PolicyCaptureReader(str(root_b)).capture()
    assert cap_a.wire_bytes == payload_a
    assert cap_a.selection.wire_sha256 == _digest(payload_a)
    assert cap_b.wire_bytes == payload_b
    assert cap_b.selection.wire_sha256 == _digest(payload_b)
    # A root advertising another root's digest must not cross into it:
    # selection-only observation still works, capture cannot.
    root_c = _make_root(
        tmp_path / "c",
        3,
        payload_a,
        write_payload=False,
        selection_bytes=_render_selection(3, len(payload_a), _digest(payload_a)),
    )
    reader_c = capture.PolicyCaptureReader(str(root_c))
    assert reader_c.read_selection().wire_sha256 == _digest(payload_a)
    with pytest.raises(capture.PolicyCaptureError):
        reader_c.capture()


def test_payload_byte_mismatch_refused(tmp_path):
    declared = "f" * 64
    root = _make_root(
        tmp_path / "root",
        1,
        _PAYLOAD,
        selection_bytes=_render_selection(1, len(_PAYLOAD), declared),
        payload_name=declared + ".bin",
    )
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).capture()


@pytest.mark.parametrize("short", [True, False], ids=["short", "long"])
def test_payload_length_mismatch_refused(tmp_path, short):
    content = _PAYLOAD[:-1] if short else _PAYLOAD + b"x"
    digest = _digest(_PAYLOAD)  # name derived from the admitted digest only
    root = _make_root(
        tmp_path / "root",
        1,
        _PAYLOAD,
        selection_bytes=_render_selection(1, len(_PAYLOAD), digest),
        payload_name=digest + ".bin",
        payload_content=content,
    )
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).capture()


def _canonical_bytes():
    return _render_selection(1, len(_PAYLOAD), _digest(_PAYLOAD))


@pytest.mark.parametrize(
    ("make_raw", "case"),
    [
        (lambda c: c + b"\n", "trailing-lf"),
        (lambda c: c + b" ", "trailing-space"),
        (
            lambda c: json.dumps(
                {
                    "wire_sha256": _digest(_PAYLOAD),
                    "kind": _KIND,
                    "schema": 1,
                    "generation": 1,
                    "wire_bytes": len(_PAYLOAD),
                },
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("ascii"),
            "shuffled-keys",
        ),
        (lambda c: c.replace(b":", b": ", 1), "noncanonical-whitespace"),
        (
            lambda c: json.dumps(
                {
                    "generation": 1,
                    "kind": "slaif-current-policy-selection-v2",
                    "schema": 1,
                    "wire_bytes": len(_PAYLOAD),
                    "wire_sha256": _digest(_PAYLOAD),
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("ascii"),
            "wrong-kind",
        ),
        (lambda c: c[:-1] + b',"extra":1}', "extra-key"),
    ],
    ids=["trailing-lf", "trailing-space", "shuffled-keys",
         "noncanonical-whitespace", "wrong-kind", "extra-key"],
)
def test_noncanonical_selection_refused(tmp_path, make_raw, case):
    root = _make_root(
        tmp_path / "root",
        1,
        _PAYLOAD,
        selection_bytes=make_raw(_canonical_bytes()),
    )
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).read_selection()


@pytest.mark.parametrize("mode", [0o755, 0o777, 0o750], ids=["0755", "0777", "0750"])
def test_root_mode_refused(tmp_path, mode):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    os.chmod(str(root), mode)
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).read_selection()


def test_selection_mode_refused(tmp_path):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    os.chmod(str(root / _SELECTION), 0o600)
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).read_selection()


def test_payload_mode_refused(tmp_path):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    os.chmod(str(root / (_digest(_PAYLOAD) + ".bin")), 0o600)
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).capture()


@pytest.mark.parametrize("entry", ["selection", "payload"], ids=["selection", "payload"])
def test_symlink_entry_refused_before_open(tmp_path, entry, monkeypatch):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    os.chmod(str(outside), 0o700)
    digest = _digest(_PAYLOAD)
    if entry == "selection":
        _write_private(outside / "real-selection", _canonical_bytes())
        os.unlink(str(root / _SELECTION))
        os.symlink(str(outside / "real-selection"), str(root / _SELECTION))
        name = _SELECTION
    else:
        _write_private(outside / "real-payload", _PAYLOAD)
        os.unlink(str(root / (digest + ".bin")))
        os.symlink(str(outside / "real-payload"), str(root / (digest + ".bin")))
        name = digest + ".bin"
    state = _install(monkeypatch, "open",
                     match=lambda a, k: bool(a) and a[0] == name)
    with pytest.raises(capture.PolicyCaptureError):
        if entry == "selection":
            capture.PolicyCaptureReader(str(root)).read_selection()
        else:
            capture.PolicyCaptureReader(str(root)).capture()
    # Refused by the linked-entry pre-probe before any open attempt.
    assert all(not (a and a[0] == name) for a, k in state["calls"])


def test_symlinked_intermediate_directory_refused(tmp_path):
    real = _make_root(tmp_path / "real", 1, _PAYLOAD)
    link = tmp_path / "link"
    os.symlink(str(real), str(link))
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(link)).read_selection()


@pytest.mark.parametrize("entry", ["selection", "payload"], ids=["selection", "payload"])
def test_hard_link_refused(tmp_path, entry):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    if entry == "selection":
        os.link(str(root / _SELECTION), str(root / "selection-link"))
        with pytest.raises(capture.PolicyCaptureError):
            capture.PolicyCaptureReader(str(root)).read_selection()
    else:
        os.link(str(root / (_digest(_PAYLOAD) + ".bin")), str(root / "payload-link"))
        with pytest.raises(capture.PolicyCaptureError):
            capture.PolicyCaptureReader(str(root)).capture()


@pytest.mark.parametrize("entry", ["selection", "payload"], ids=["selection", "payload"])
def test_special_file_refused_before_open(tmp_path, entry, monkeypatch):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    digest = _digest(_PAYLOAD)
    if entry == "selection":
        os.unlink(str(root / _SELECTION))
        name = _SELECTION
    else:
        os.unlink(str(root / (digest + ".bin")))
        name = digest + ".bin"
    os.mkfifo(str(root / name), 0o600)
    os.chmod(str(root / name), 0o400)
    state = _install(monkeypatch, "open",
                     match=lambda a, k: bool(a) and a[0] == name)
    with pytest.raises(capture.PolicyCaptureError):
        if entry == "selection":
            capture.PolicyCaptureReader(str(root)).read_selection()
        else:
            capture.PolicyCaptureReader(str(root)).capture()
    # The special file is refused before attempting open.
    assert all(not (a and a[0] == name) for a, k in state["calls"])


def test_missing_selection_refused(tmp_path):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    os.unlink(str(root / _SELECTION))
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).read_selection()


def test_missing_payload_selection_only(tmp_path):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD, write_payload=False)
    reader = capture.PolicyCaptureReader(str(root))
    # Boundary observation: the selection alone is still observable.
    assert reader.read_selection().generation == 1
    with pytest.raises(capture.PolicyCaptureError):
        reader.capture()


def test_payload_growth_during_capture(tmp_path, monkeypatch):
    digest = _digest(_PAYLOAD)
    root = _make_root(tmp_path / "root", 1, _PAYLOAD, write_payload=False)
    # The fixture owns a retained write descriptor (trusted-writer role)
    # opened before the 0400 mode so the witness can grow mid-capture.
    pay_path = str(root / (digest + ".bin"))
    pay_fd = os.open(pay_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                     | os.O_APPEND, 0o600)
    os.write(pay_fd, _PAYLOAD)
    os.chmod(pay_path, 0o400)
    st = os.fstat(pay_fd)
    pay_ino = (st.st_dev, st.st_ino)
    triggered = []

    def grow_on_first_payload_read(fd, *args, **kwargs):
        if not triggered and _is_fd_of(fd, pay_ino):
            triggered.append(1)
            os.write(pay_fd, b"g")

    _install(monkeypatch, "read", action=grow_on_first_payload_read)
    try:
        with pytest.raises(capture.PolicyCaptureError):
            capture.PolicyCaptureReader(str(root)).capture()
    finally:
        os.close(pay_fd)
    assert triggered == [1]


def test_payload_pointer_replacement_during_capture(tmp_path, monkeypatch):
    digest = _digest(_PAYLOAD)
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    repl = tmp_path / "replacement.bin"
    _write_private(repl, _PAYLOAD)
    st = os.lstat(str(root / (digest + ".bin")))
    old_ino = (st.st_dev, st.st_ino)
    triggered = []

    def replace_on_first_payload_read(fd, *args, **kwargs):
        if not triggered and _is_fd_of(fd, old_ino):
            triggered.append(1)
            os.rename(str(repl), str(root / (digest + ".bin")))

    _install(monkeypatch, "read", action=replace_on_first_payload_read)
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).capture()
    assert triggered == [1]
    # The entry now points at a different inode than the observed fd.
    after = os.lstat(str(root / (digest + ".bin")))
    assert (after.st_dev, after.st_ino) != old_ino


def test_selection_replaced_between_observations(tmp_path, monkeypatch):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    alt = _render_selection(2, len(_PAYLOAD), _digest(_PAYLOAD))
    repl = tmp_path / "alt-selection.json"
    _write_private(repl, alt)
    count = []
    real_open = os.open

    def spy_open(*args, **kwargs):
        if args and args[0] == _SELECTION:
            count.append(1)
            if len(count) == 2:
                os.rename(str(repl), str(root / _SELECTION))
        return real_open(*args, **kwargs)

    monkeypatch.setattr(os, "open", spy_open)
    with pytest.raises(capture.PolicyCaptureError):
        capture.PolicyCaptureReader(str(root)).capture()
    assert count == [1, 1]


def test_selection_growth_measured_read_requests(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir(mode=0o700)
    os.chmod(str(root), 0o700)
    canonical = _canonical_bytes()
    sel_path = str(root / _SELECTION)
    # Retained writer descriptor opened before the 0400 mode.
    sel_fd = os.open(sel_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                     | os.O_APPEND, 0o600)
    os.write(sel_fd, canonical)
    os.chmod(sel_path, 0o400)
    st = os.fstat(sel_fd)
    sel_ino = (st.st_dev, st.st_ino)
    triggered = []
    read_requests = []
    real_read = os.read

    def spy_read(fd, count, *args, **kwargs):
        if _is_fd_of(fd, sel_ino):
            read_requests.append(count)
            if not triggered:
                triggered.append(1)
                os.write(sel_fd, b"g")
        return real_read(fd, count, *args, **kwargs)

    monkeypatch.setattr(os, "read", spy_read)
    try:
        with pytest.raises(capture.PolicyCaptureError):
            capture.PolicyCaptureReader(str(root)).read_selection()
    finally:
        os.close(sel_fd)
    assert triggered == [1]
    # The data read request is bounded by the captured (observed) size,
    # not a larger envelope; the trailing probe is exactly one byte.
    assert read_requests[0] == len(canonical)
    assert read_requests[-1] == 1


@pytest.mark.parametrize(
    "op",
    ["capture", "read_selection"],
    ids=["capture", "read_selection"],
)
def test_selection_replaced_around_final_namespace_check(
    tmp_path, monkeypatch, op
):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    alt = _render_selection(2, len(_PAYLOAD), _digest(_PAYLOAD))
    repl = tmp_path / "alt-selection.json"
    _write_private(repl, alt)
    st = os.lstat(str(root / _SELECTION))
    sel_ino = (st.st_dev, st.st_ino)
    triggered = []
    root_opens = []
    real_open = os.open

    def spy_open(*args, **kwargs):
        if args and args[0] == "/":
            root_opens.append(1)
            if len(root_opens) == 2 and not triggered:
                # Replace while the final root re-walk is underway, after
                # the selection observation(s) completed: the final
                # linked-entry check is the detector.
                triggered.append(1)
                os.rename(str(repl), str(root / _SELECTION))
        return real_open(*args, **kwargs)

    monkeypatch.setattr(os, "open", spy_open)
    with pytest.raises(capture.PolicyCaptureError):
        getattr(capture.PolicyCaptureReader(str(root)), op)()
    assert triggered == [1]
    # The entry now points at a different inode than the observed one.
    after = os.lstat(str(root / _SELECTION))
    assert (after.st_dev, after.st_ino) != sel_ino


@pytest.mark.parametrize(
    "value",
    [0, -1, 30001, 1.0, 30000.0, "30000", None, True, [30000]],
    ids=["zero", "negative", "over", "float", "float-max", "str", "none", "bool",
         "list"],
)
def test_deadline_admission(tmp_path, value):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    with pytest.raises(capture.PolicyCaptureError):
        reader.read_selection(deadline_ms=value)
    with pytest.raises(capture.PolicyCaptureError):
        reader.capture(deadline_ms=value)
    # Admission is validated before any acquisition or latch.
    assert not reader._latched and reader._retained_slot is None


def test_deadline_boundaries_accepted(tmp_path):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    assert reader.read_selection(deadline_ms=1).generation == 1
    assert reader.capture(deadline_ms=30000).wire_bytes == _PAYLOAD


def test_cooperative_checkpoint_clean_expiry_reuse(tmp_path, monkeypatch):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    parts = str(root)[1:].split("/")
    part1 = parts[0]  # first path component, e.g. "tmp"
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    expired = []
    opened = []
    real_open = os.open

    def spy_open(*args, **kwargs):
        if args and isinstance(args[0], str) and (
            args[0] == "/" or args[0] in parts
        ):
            opened.append(args[0])
            if len(opened) == 2 and not expired:
                # Expire at the second walk open: the root and the first
                # component are both definitely owned at this point.
                expired.append(1)
                clock["now"] = 1000.0 + 30.001  # past the 30000 ms deadline
        return real_open(*args, **kwargs)

    monkeypatch.setattr(os, "open", spy_open)
    slash_ino = (os.stat("/").st_dev, os.stat("/").st_ino)
    part1_ino = (os.stat("/" + part1).st_dev, os.stat("/" + part1).st_ino)
    closed = []
    real_close = os.close

    def spy_close(fd, *args, **kwargs):
        if _is_fd_of(fd, slash_ino):
            closed.append("slash")
            # Advance the controlled clock further, past the original
            # 30000 ms budget, immediately after the first fixture-owned
            # cleanup close: a finite replacement deadline must not cut
            # the teardown, so the second real close must still happen.
            clock["now"] = 1000.0 + 60.002
        elif _is_fd_of(fd, part1_ino):
            closed.append("part1")
        return real_close(fd, *args, **kwargs)

    monkeypatch.setattr(os, "close", spy_close)
    with pytest.raises(capture.PolicyCaptureError):
        reader.capture(deadline_ms=30000)
    # The expiry fired once, at the second walk open; the clock then
    # advanced further, past the original budget, after the first
    # fixture-owned cleanup close, and the finite teardown still
    # performed the second real close without a time cut-off.
    assert expired == [1]
    assert opened == ["/", part1]
    assert closed == ["slash", "part1"]
    # A clean teardown does not latch: no partial result is delivered and
    # the same owner is reusable after a clean expiry.
    assert reader._latched is False
    assert reader._retained_slot is None
    clock["now"] += 60.0
    assert reader.read_selection().generation == 1


def test_successful_observation_final_checkpoint_expiry_reuse(
    tmp_path, monkeypatch
):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    expired = []
    st = os.stat(str(root))
    root_ino = (st.st_dev, st.st_ino)
    root_closes = []
    real_close = os.close

    def spy_close(fd, *args, **kwargs):
        if _is_fd_of(fd, root_ino):
            root_closes.append(fd)
            if len(root_closes) == 2:
                # The final real private-root close: advance the
                # controlled clock past the deadline only here, after
                # the successful observation and namespace re-walk.
                expired.append(1)
                clock["now"] = 1000.0 + 30.001
        return real_close(fd, *args, **kwargs)

    monkeypatch.setattr(os, "close", spy_close)
    with pytest.raises(capture.PolicyCaptureError):
        reader.read_selection(deadline_ms=30000)
    # The expiry happened only at the final root close; the successful
    # observation was refused at the final checkpoint before returning
    # success, without latching the clean owner.
    assert expired == [1]
    assert len(root_closes) == 2
    assert reader._latched is False
    assert reader._retained_slot is None
    # The same clean owner remains reusable: no latch, no retained slot.
    clock["now"] += 60.0
    assert reader.read_selection().generation == 1


def test_injected_uncertain_close_latches_owner(tmp_path, monkeypatch):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    real_close = os.close
    seen = []
    faulted = []
    fault_index = []
    # The root inode is closed exactly twice: by the namespace re-walk and
    # by the body's final root close; the second one is the last close of
    # the operation.  Delegate the real close first so no test descriptor
    # leaks, then fault the reported outcome so the cell stays counted.
    st = os.stat(str(root))
    root_ino = (st.st_dev, st.st_ino)
    root_closes = []

    def spying_close(fd, *args, **kwargs):
        seen.append(fd)
        if _is_fd_of(fd, root_ino):
            root_closes.append(fd)
            if len(root_closes) == 2:
                real_close(fd, *args, **kwargs)
                faulted.append(fd)
                fault_index.append(len(seen) - 1)
                raise OSError(5, "injected uncertain close")
        return real_close(fd, *args, **kwargs)

    monkeypatch.setattr(os, "close", spying_close)
    with pytest.raises(capture.PolicyCaptureError):
        reader.read_selection()
    assert len(faulted) == 1
    assert len(root_closes) == 2 and root_closes[1] == faulted[0]
    # No numeric close retry: the uncertain close was the last close the
    # protocol attempted; nothing was closed after it (fd numbers reused
    # earlier in the walk do not count).
    assert fault_index[0] == len(seen) - 1
    assert reader._latched is True
    slot = reader._retained_slot
    assert slot is not None
    assert sum(1 for s in slot.st if s != publication._FREE) == 1
    # No new open after the latch.
    os_real_open = os.open
    opened_after = []

    def spying_open(*args, **kwargs):
        opened_after.append(args)
        return os_real_open(*args, **kwargs)

    monkeypatch.setattr(os, "open", spying_open)
    with pytest.raises(capture.PolicyCaptureError):
        reader.read_selection()
    with pytest.raises(capture.PolicyCaptureError):
        reader.capture()
    assert opened_after == []


def test_injected_interrupt_close_preserves_identity(tmp_path, monkeypatch):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    sentinel = _Interrupt()
    real_close = os.close
    seen = []
    st = os.stat(str(root))
    root_ino = (st.st_dev, st.st_ino)
    root_closes = []

    def spying_close(fd, *args, **kwargs):
        seen.append(fd)
        if _is_fd_of(fd, root_ino):
            root_closes.append(fd)
            if len(root_closes) == 2:
                # Delegate the real close first (no leaked test
                # descriptor), then interrupt.
                real_close(fd, *args, **kwargs)
                raise sentinel
        return real_close(fd, *args, **kwargs)

    monkeypatch.setattr(os, "close", spying_close)
    with pytest.raises(_Interrupt) as exc:
        reader.read_selection()
    # First interruption identity is preserved, not wrapped.
    assert exc.value is sentinel
    assert reader._latched is True
    assert sum(1 for s in reader._retained_slot.st
               if s != publication._FREE) == 1


def test_lock_admission_interleaving_no_new_open(tmp_path, monkeypatch):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    real_guard = reader._guard
    attempts = []
    b2 = {}
    b2_started = []

    class _GuardWitness:
        def acquire(self, blocking=False):
            ok = real_guard.acquire(blocking=blocking)
            attempts.append((threading.get_ident(), blocking, ok))
            return ok

        def release(self):
            real_guard.release()
            if b2_started:
                return

            def attempt_b2():
                b2["thread"] = threading.get_ident()
                try:
                    reader.capture()
                    b2["result"] = "no-error"
                except BaseException as exc:
                    b2["result"] = exc

            # Release window: the closed latch was published under the
            # guard before this release, so a B2 admitted immediately
            # after it must be refused at the poison check.
            b2_started.append(1)
            worker = threading.Thread(target=attempt_b2)
            worker.start()
            worker.join()

    reader._guard = _GuardWitness()
    real_open = os.open
    opened_threads = []

    def spy_open(*args, **kwargs):
        opened_threads.append(threading.get_ident())
        return real_open(*args, **kwargs)

    monkeypatch.setattr(os, "open", spy_open)
    st = os.stat(str(root))
    root_ino = (st.st_dev, st.st_ino)
    root_closes = []
    interleaved = {}
    real_close = os.close

    def spy_close(fd, *args, **kwargs):
        if _is_fd_of(fd, root_ino):
            root_closes.append(fd)
            if len(root_closes) == 2:
                # Delegate the real close first (no leaked test
                # descriptor), then run B1 while A still holds the
                # guard, and fault the reported outcome.

                def attempt_b1():
                    interleaved["thread"] = threading.get_ident()
                    try:
                        reader.capture()
                        interleaved["result"] = "no-error"
                    except BaseException as exc:
                        interleaved["result"] = exc

                worker = threading.Thread(target=attempt_b1)
                worker.start()
                worker.join()
                real_close(fd, *args, **kwargs)
                raise OSError(5, "injected uncertain close")
        return real_close(fd, *args, **kwargs)

    monkeypatch.setattr(os, "close", spy_close)
    with pytest.raises(capture.PolicyCaptureError):
        reader.capture()
    # B1's admission attempt was a non-blocking entrance refused under
    # the held guard, and B1 performed no open of its own.
    b1_thread = interleaved["thread"]
    assert any(tid == b1_thread and blocking is False and ok is False
               for tid, blocking, ok in attempts)
    assert b1_thread not in opened_threads
    assert type(interleaved["result"]) is capture.PolicyCaptureError
    # B2 was admitted in the release window: its non-blocking acquisition
    # succeeded, and it was refused at the poison check because the closed
    # latch was published under the guard before the release.  B2 also
    # performed no open.
    b2_thread = b2["thread"]
    assert any(tid == b2_thread and blocking is False and ok is True
               for tid, blocking, ok in attempts)
    assert b2_thread not in opened_threads
    assert type(b2["result"]) is capture.PolicyCaptureError
    # A's genuine unknown close latches the owner and retains the slot.
    assert reader._latched is True
    assert sum(1 for s in reader._retained_slot.st
               if s != publication._FREE) == 1


def test_creator_pid_checked_before_lock(tmp_path):
    root = _make_root(tmp_path / "root", 1, _PAYLOAD)
    reader = capture.PolicyCaptureReader(str(root))
    reader._creator = os.getpid() + 1  # test-local forged creator binding
    with pytest.raises(capture.PolicyCaptureError):
        reader.read_selection()
    with pytest.raises(capture.PolicyCaptureError):
        reader.capture()
    assert not reader._latched  # the check refuses before any acquisition


def test_declared_payload_boundaries(tmp_path):
    minimum = b"slaif-min-wire-" + b"\x00" * 27
    assert len(minimum) == 42
    root_min = _make_root(tmp_path / "min", 1, minimum)
    cap = capture.PolicyCaptureReader(str(root_min)).capture()
    assert cap.wire_bytes == minimum and cap.selection.wire_bytes == 42
    maximum = (b"slaif-max-wire-" * ((_MAX_PAYLOAD // 15) + 1))[:_MAX_PAYLOAD]
    assert len(maximum) == _MAX_PAYLOAD
    root_max = _make_root(tmp_path / "max", 2, maximum)
    cap = capture.PolicyCaptureReader(str(root_max)).capture()
    assert cap.wire_bytes == maximum and cap.selection.wire_bytes == _MAX_PAYLOAD


def test_clean_failure_does_not_latch(tmp_path):
    digest = _digest(_PAYLOAD)
    root = _make_root(tmp_path / "root", 1, _PAYLOAD, write_payload=False)
    # Retained writer descriptor so the fixture can correct the root after
    # the clean refusal; the payload starts one byte short.
    pay_path = str(root / (digest + ".bin"))
    pay_fd = os.open(pay_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                     | os.O_APPEND, 0o600)
    os.write(pay_fd, _PAYLOAD[:-1])
    os.chmod(pay_path, 0o400)
    reader = capture.PolicyCaptureReader(str(root))
    with pytest.raises(capture.PolicyCaptureError):
        reader.capture()  # length mismatch, but every close was clean
    assert reader._latched is False
    assert reader._retained_slot is None
    # The same reader succeeds once the trusted writer completes the bytes.
    os.write(pay_fd, _PAYLOAD[-1:])
    os.close(pay_fd)
    assert reader.capture().wire_bytes == _PAYLOAD
