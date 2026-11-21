"""Private installed-policy selection evidence.

Operator-side current-policy view update (009, selected writer seam):
fully synthetic and offline.  Every root is a private temporary
directory owned by the test, every byte is generated here, and the
separately attributed selection fixture emulates the trusted immutable
writer role only; no real protected path, credential, network route,
model or service is touched, and the fixture supplies no
writer-authority evidence.  The test-side wire emitter is an
independent re-derivation of the typed supplied-policy framing, so
the production admission is never its own oracle.  Descriptor, fault
and deadline behavior is measured through test-local narrowly
delegated witnesses on the real descriptor primitives and a
controlled monotone clock; counted real I/O witnesses prove the
actual operation order and every visibility and durability cut, the
genuine installer and capture reader stay the stable interop, and two
fresh independent-interpreter writer processes serialize on one real
root lock.  No skip/xfail/fallback.
"""

import ast
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

from slaif_raggedized_helper import private_policy_capture as capture
from slaif_raggedized_helper import private_policy_payload as payload
from slaif_raggedized_helper import private_policy_selection as selection
from slaif_raggedized_helper import private_report_publication as publisher
from slaif_raggedized_helper import supplied_policy_wire as wire

_BANNED_CALLS = ("unlink", "remove", "rename", "replace", "rmtree")
_MAX_WIRE_BYTES = 67_108_864


# ------------------------------------------------- independent wire emitter

_MAGIC = b"slaif-supplied-policy-view-v1\n"
_CREDENTIAL_A = b"synthetic-credential-" + b"a" * 22
_CREDENTIAL_B = b"synthetic-credential-" + b"b" * 22
_CREDENTIAL_C = b"synthetic-credential-" + b"c" * 22
_VERIFIER_A = hashlib.sha256(_CREDENTIAL_A).digest()
_VERIFIER_B = hashlib.sha256(_CREDENTIAL_B).digest()
_VERIFIER_C = hashlib.sha256(_CREDENTIAL_C).digest()
_REVISION_1 = "sha256:" + "ab" * 32
_REVISION_C = "sha256:" + "ef" * 32
_SCOPE_1 = "cd" * 32


def _u32(value):
    return value.to_bytes(4, "big")


def _s(text):
    raw = text.encode("utf-8")
    return _u32(len(raw)) + raw


def _encode_policy(principals, documents):
    """Independent test-side wire framing per the typed component grammar."""
    parts = [_MAGIC, _u32(1), _u32(len(principals))]
    for principal_id, verifier, operations, corpora, versions, labels in principals:
        parts.append(_s(principal_id))
        parts.append(_u32(32) + verifier)
        parts.append(_u32(len(operations)))
        for operation in operations:
            parts.append(_s(operation))
        parts.append(_u32(1))
        for values in (corpora, versions, labels):
            parts.append(_u32(len(values)))
            for value in values:
                parts.append(_s(value))
    parts.append(_u32(len(documents)))
    for document_id, pairs in documents:
        parts.append(_s(document_id))
        parts.append(_u32(len(pairs)))
        for revision_id, scope_digest in pairs:
            parts.append(_s(revision_id))
            parts.append(_s(scope_digest))
    return b"".join(parts)


WIRE_MIN = _MAGIC + _u32(1) + _u32(0) + _u32(0)  # exactly 42, empty policy
WIRE_A = _encode_policy(
    [
        ("alpha-1", _VERIFIER_A, ("answer", "sources:read"), ("alpha",), ("v1",), ("l1",)),
        ("beta-2", _VERIFIER_B, ("search",), (), (), ()),
    ],
    [("doc-1", ((_REVISION_1, _SCOPE_1),))],
)
WIRE_B = _encode_policy([("beta-2", _VERIFIER_B, ("search",), (), (), ())], [])
WIRE_C = _encode_policy(
    [("delta-4", _VERIFIER_C, ("search",), (), (), ())],
    [("doc-c", ((_REVISION_C, _SCOPE_1),))],
)
WIRE_DOMAIN_INVALID = _encode_policy(
    [("gamma-3", _VERIFIER_C, ("answer",), (), (), ())], []
)

_KIND = "slaif-current-policy-selection-v1"


def _digest(data):
    return hashlib.sha256(data).hexdigest()


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
    # Test-side trusted immutable writer fixture (separately
    # attributed; it is not product code and carries no
    # writer-authority evidence).
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(str(path), mode)


def _make_root(directory, generation, payload_bytes):
    directory = Path(directory)
    directory.mkdir(mode=0o700)
    os.chmod(str(directory), 0o700)
    _write_private(
        directory / "current-policy.json",
        _render_selection(generation, len(payload_bytes), _digest(payload_bytes)),
    )
    _write_private(directory / (_digest(payload_bytes) + ".bin"), payload_bytes)
    return directory


def _never_touch(counter):
    def forbidden(*args, **kwargs):
        counter.append(1)
        raise SystemExit(73)

    return forbidden


def _ban_destructive(monkeypatch, counter):
    for name in _BANNED_CALLS:
        def caller(_name=name, *args, **kwargs):
            counter.append(_name)
            raise SystemExit(73)

        monkeypatch.setattr(os, name, caller, raising=False)


def _assert_fixed_refusal(caught, selection_state, cleanup, stage=None):
    error = caught.value
    assert type(error) is selection.PolicySelectError
    assert error.selection is selection_state
    assert error.cleanup is cleanup
    if stage is not None:
        assert error.stage is stage
    assert str(error) == "private policy selection refused"


def _child_environment():
    environment = {
        "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        environment[name] = "1"
    return environment


def _child_limits():
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16777216, 16777216))


_TWO_WRITER_CHILD = r"""
import os
import resource
import sys
import time

resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

root, role, wire_hex, sync = sys.argv[1:5]
if role == "second":
    deadline = time.monotonic() + 30
    while not os.path.exists(sync):
        if time.monotonic() >= deadline:
            print("NOSYNC")
            raise SystemExit(1)
        time.sleep(0.01)
from slaif_raggedized_helper import private_policy_selection as s

wire = bytes.fromhex(wire_hex)
try:
    receipt = s.select_installed_policy(wire, directory=root, deadline_ms=20000)
except s.PolicySelectError as exc:
    print("REFUSED:%s:%s:%s" % (exc.selection.value, exc.cleanup.value, exc.stage.value))
    raise SystemExit(0)
print("SELECTED:%d" % receipt.generation)
if role == "first":
    # Ordered success: signal completion so the second writer starts
    # only after the first published generation is durable.
    fd = os.open(sync, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
"""

_RESTART_REFUSAL_CHILD = r"""
import resource
import sys

resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

root, wire_hex = sys.argv[1:3]
from slaif_raggedized_helper import private_policy_selection as s

wire = bytes.fromhex(wire_hex)
try:
    s.select_installed_policy(wire, directory=root, deadline_ms=20000)
except s.PolicySelectError as exc:
    print("REFUSED:%s:%s:%s" % (exc.selection.value, exc.cleanup.value, exc.stage.value))
    raise SystemExit(0)
print("UNEXPECTED_SUCCESS")
"""

_AMBIGUOUS_CLOSE_CHILD = r"""
import os
import resource
import stat
import sys

resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

root, wire_hex = sys.argv[1:3]
from slaif_raggedized_helper import private_report_publication as p
from slaif_raggedized_helper import private_policy_selection as s

wire = bytes.fromhex(wire_hex)
armed = {"value": False}
real_cleanup = p._cleanup


def flagged_cleanup(slot, end):
    armed["value"] = True
    return real_cleanup(slot, end)


real_close = os.close


def faulting_close(fd):
    if armed["value"]:
        try:
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("simulated ambiguous close")
        except OSError:
            raise OSError("simulated ambiguous close") from None
    return real_close(fd)


s._cleanup = flagged_cleanup
os.close = faulting_close
try:
    s.select_installed_policy(wire, directory=root, deadline_ms=20000)
except s.PolicySelectError as exc:
    pending = sum(1 for slot in p._SLOTS if slot is not None and slot.pending)
    print("REFUSED:%s:%s:%s" % (exc.selection.value, exc.cleanup.value, exc.stage.value))
    print("PENDING:%d" % pending)
    raise SystemExit(0)
print("UNEXPECTED_SUCCESS")
"""


def _witness_order(monkeypatch):
    # Narrowly delegated call witnesses: each records, then runs the
    # real descriptor primitive, so the observed order is the actual
    # order; every event carries a unique sequence position.
    import fcntl

    events = []
    real_open = os.open
    real_flock = fcntl.flock
    real_fsync = os.fsync
    real_replace = os.replace
    real_unlink = os.unlink
    real_write = os.write

    def _record(name, payload):
        events.append((name, payload, len(events)))

    def witnessing_open(name, flags, *args, **kwargs):
        fd = real_open(name, flags, *args, **kwargs)
        _record("open", (name, flags, fd))
        return fd

    def witnessing_flock(fd, operation):
        _record("flock", (fd, operation))
        return real_flock(fd, operation)

    def witnessing_fsync(fd):
        _record("fsync", (fd,))
        return real_fsync(fd)

    def witnessing_replace(source, destination, **kwargs):
        _record("replace", (source, destination, kwargs))
        return real_replace(source, destination, **kwargs)

    def witnessing_unlink(name, **kwargs):
        _record("unlink", (name, kwargs))
        return real_unlink(name, **kwargs)

    def witnessing_write(fd, data, *args, **kwargs):
        _record("write", (fd, len(data)))
        return real_write(fd, data, *args, **kwargs)

    monkeypatch.setattr(os, "open", witnessing_open)
    monkeypatch.setattr(fcntl, "flock", witnessing_flock)
    monkeypatch.setattr(os, "fsync", witnessing_fsync)
    monkeypatch.setattr(os, "replace", witnessing_replace)
    monkeypatch.setattr(os, "unlink", witnessing_unlink)
    monkeypatch.setattr(os, "write", witnessing_write)
    return events


# --------------------------------------------------------------- origins


def test_module_origins_inside_assigned_worktree():
    # Derived from this test file's resolved physical location
    # (tests/unit -> worktree root / src), so a canonical transfer or
    # CI keeps the same fail-closed origin check.
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    assert (
        Path(__file__).resolve()
        == root / "tests" / "unit" / "test_private_policy_selection.py"
    )
    for module, name in (
        (selection, "private_policy_selection.py"),
        (payload, "private_policy_payload.py"),
        (publisher, "private_report_publication.py"),
        (capture, "private_policy_capture.py"),
        (wire, "supplied_policy_wire.py"),
    ):
        path = Path(module.__file__).resolve()
        assert path == src / "slaif_raggedized_helper" / name, name
        assert path.is_file()


_FROZEN_OBJECTS = {
    "src/slaif_raggedized_helper/private_report_publication.py": (
        "7a70eaa65d99b2b43c018e6d0d4381299ca1da2bd1cc21ce702e302450170df4"
    ),
    "src/slaif_raggedized_helper/private_policy_payload.py": (
        "48bf5ec415e049f265c6e90a68caa08283495bf3c07dbace90495f57e041193d"
    ),
    "src/slaif_raggedized_helper/private_policy_capture.py": (
        "4d0c3b8002c6c4fabe3c3be3a08d851375249ad2fb807260f56e5fa9e3e7f0fc"
    ),
    "src/slaif_raggedized_helper/policy_selection.py": (
        "eda878a12af9f141b6f9cd48ccec5601932201f9b36baa31fa17fe28659bde87"
    ),
    "src/slaif_raggedized_helper/supplied_policy.py": (
        "7e59a94b98ee9b58af53bd4f350b992dbb0b91c547fd428b31b43b7009927195"
    ),
    "src/slaif_raggedized_helper/supplied_policy_wire.py": (
        "d18a93996baa36ea88b538f439994e9d658eb1fe4de32fb6daac15068ec4805a"
    ),
    "tests/unit/test_private_report_publication.py": (
        "1b8cb255ba2b31fe1cb2c197fd6c72d5123dee9c400108d1d2a2b7812e9ad55d"
    ),
    "tests/unit/test_private_policy_payload.py": (
        "ac56eed16c5505b7f8c3afd2a7728fc6312367fd2713be1a7a4f77eeb831d814"
    ),
    "tests/unit/test_private_policy_capture.py": (
        "bb1fccfeddf28c8ecba464fa4f392e6b830f2fc07291a44a65978b19b670f7b9"
    ),
}


def test_frozen_dependency_objects_byte_exact():
    # The frozen payload, publisher, capture, selection parser, wire
    # and all existing test objects stay byte-exact at these bytes.
    root = Path(__file__).resolve().parents[2]
    for relative, expected in sorted(_FROZEN_OBJECTS.items()):
        path = root / relative
        with open(path, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        assert actual == expected, relative


def test_public_api_surface():
    assert selection.__all__ == [
        "PolicySelectError",
        "PolicySelectOutcome",
        "PolicySelectReceipt",
        "Stage",
        "select_installed_policy",
    ]
    import inspect

    params = inspect.signature(selection.select_installed_policy).parameters
    assert tuple(params) == ("wire_bytes", "directory", "deadline_ms")
    assert params["wire_bytes"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    for name in ("directory", "deadline_ms"):
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["directory"].default is inspect.Parameter.empty
    assert params["deadline_ms"].default == 30000
    # The input supplies no explicit name, record, digest, generation,
    # parsed DTO, callback or selector.
    assert len(params) == 3
    assert [f.name for f in selection.PolicySelectReceipt.__dataclass_fields__.values()] == [
        "outcome",
        "selection",
        "cleanup",
        "generation",
        "wire_digest",
        "selection_bytes",
    ]
    assert {m.name for m in selection.PolicySelectOutcome} == {"SELECTED"}
    assert {m.name for m in selection.Stage} == {"ABSENT", "PRESENT", "UNRESOLVED"}


def test_receipt_and_error_are_fixed_content_free():
    error = selection.PolicySelectError(
        publisher.Publication.POSSIBLY_PUBLISHED,
        publisher.Cleanup.PENDING,
        selection.Stage.UNRESOLVED,
    )
    assert type(error) is selection.PolicySelectError
    assert str(error) == "private policy selection refused"
    assert error.selection is publisher.Publication.POSSIBLY_PUBLISHED
    assert error.cleanup is publisher.Cleanup.PENDING
    assert error.stage is selection.Stage.UNRESOLVED
    marker = "sel!ect-marker-xyz-987"
    assert marker not in str(error)
    assert marker not in repr(error)
    assert all(marker not in str(argument) for argument in error.args)
    receipt = selection.PolicySelectReceipt(
        selection.PolicySelectOutcome.SELECTED,
        publisher.Publication.DURABLE,
        publisher.Cleanup.CLEAN,
        7,
        "ab" * 32,
        b"{}",
    )
    assert receipt.outcome is selection.PolicySelectOutcome.SELECTED
    assert receipt.selection is publisher.Publication.DURABLE
    assert receipt.cleanup is publisher.Cleanup.CLEAN
    assert receipt.generation == 7
    assert type(receipt.generation) is int
    assert receipt.wire_digest == "ab" * 32
    assert receipt.selection_bytes == b"{}"


def test_module_source_has_no_installer_or_second_lock_or_forbidden_calls():
    # The entry must never call the payload installer, never take a
    # second directory lock and never own a storage protocol: exactly
    # one fd-relative replace site, at most one (pre-attempt) unlink
    # site, no unnamed staging and no destructive namespace call.
    with open(os.path.abspath(selection.__file__), "r", encoding="utf-8") as handle:
        source = handle.read()
    tree = ast.parse(source)
    replace_sites = 0
    unlink_sites = 0
    banned = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                owner, attr = func.value.id, func.attr
                if (owner, attr) == ("os", "replace"):
                    replace_sites += 1
                elif (owner, attr) == ("os", "unlink"):
                    unlink_sites += 1
                elif (owner, attr) in {
                    ("os", "link"),
                    ("os", "remove"),
                    ("os", "rename"),
                    ("os", "rmtree"),
                    ("os", "truncate"),
                    ("shutil", "rmtree"),
                    ("fcntl", "flock"),
                }:
                    banned.append(owner + "." + attr)
            elif isinstance(func, ast.Name) and func.id in (
                "install_policy_payload",
                "_transact",
                "flock",
            ):
                banned.append(func.id)
        elif isinstance(node, ast.Attribute) and node.attr == "O_TMPFILE":
            banned.append("O_TMPFILE")
    assert banned == []
    assert replace_sites == 1
    assert unlink_sites == 1


# ----------------------------------- invalid input before any namespace work


@pytest.mark.parametrize(
    "case",
    ["too-short", "truncated-magic", "trailing-bytes", "domain-invalid", "oversize"],
)
def test_invalid_wire_zero_namespace_ops(tmp_path, monkeypatch, case):
    if case == "too-short":
        wire_bytes = _MAGIC + _u32(1) + _u32(0)
    elif case == "truncated-magic":
        wire_bytes = _MAGIC[:-1] + b"X" + _u32(1) + _u32(0) + _u32(0)
    elif case == "trailing-bytes":
        wire_bytes = WIRE_A + b"\x00"
    elif case == "domain-invalid":
        wire_bytes = WIRE_DOMAIN_INVALID
    else:
        wire_bytes = b"\x00" * (_MAX_WIRE_BYTES + 1)
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    # A genuinely preexisting reserved stage: the early refusal must
    # not observe or claim it, and must leave it untouched.
    stage = root / ".current-policy.stage"
    _write_private(stage, b"retained reserved stage", 0o400)
    opens = []
    banned = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    _ban_destructive(monkeypatch, banned)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(wire_bytes, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert caught.value.stage is selection.Stage.UNRESOLVED
    assert opens == []
    assert banned == []
    assert stage.read_bytes() == b"retained reserved stage"
    assert [entry.name for entry in root.iterdir()] == [".current-policy.stage"]


@pytest.mark.parametrize("case", ["str", "bytearray", "memoryview", "none", "empty", "int"])
def test_non_bytes_wire_zero_namespace_ops(tmp_path, monkeypatch, case):
    wire_bytes = {
        "str": "abc",
        "bytearray": bytearray(WIRE_A),
        "memoryview": memoryview(WIRE_A),
        "none": None,
        "empty": b"",
        "int": 42,
    }[case]
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(wire_bytes, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert opens == []


@pytest.mark.parametrize(
    "directory",
    [
        "/",
        "relative",
        "/tmp/../x",
        "/tmp//x",
        "/tmp/\x00",
        "/a/b/./c",
        "/" + "x" * 4096,
        "/surrogate\ud800",
    ],
)
def test_invalid_directory_zero_namespace_ops(tmp_path, monkeypatch, directory):
    opens = []
    banned = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    _ban_destructive(monkeypatch, banned)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_A, directory=directory)
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert opens == []
    assert banned == []


@pytest.mark.parametrize("bad", [True, 0, 30001, 1.5, "30000", None])
def test_bad_deadline_before_work(tmp_path, monkeypatch, bad):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_A, directory=str(root), deadline_ms=bad)
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert opens == []


def test_foreign_process_pool_refuses_before_work(tmp_path, monkeypatch):
    # Controlled fixture: the shared pool is bound to its creator
    # process, so a foreign creator refuses before any namespace work
    # with the truthful unowned-pool state.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    monkeypatch.setattr(selection, "_CREATOR", 999_999_999)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.PENDING)
    assert opens == []


def test_exhausted_pool_refuses_before_work(tmp_path, monkeypatch):
    # The shared pool is exhausted: the pool refusal must surface as
    # the entry's own fixed error with the truthful state, never as
    # the report publisher's error type.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    monkeypatch.setattr(publisher, "_SLOTS", [object() for _ in range(16)])
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.PENDING)
    assert opens == []


def test_single_free_slot_still_serves(tmp_path, monkeypatch):
    # Fifteen of sixteen slots occupied: the last real slot still
    # serves the selection entry in the same process.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    monkeypatch.setattr(publisher, "_SLOTS", [object() for _ in range(15)] + [None])
    receipt = selection.select_installed_policy(WIRE_B, directory=str(root))
    assert receipt.outcome is selection.PolicySelectOutcome.SELECTED
    assert receipt.generation == 2


# ---------------------------------------------------- cooperative deadline cuts


def _fake_monotonic(base, expire_at):
    count = {"n": 0}

    def fake():
        n = count["n"]
        count["n"] += 1
        if n >= expire_at:
            return base + 3600.0
        return base

    return fake, count


@pytest.mark.parametrize("expire_at", [2, 4])
def test_deadline_expiry_after_admission_zero_namespace(tmp_path, monkeypatch, expire_at):
    # The controlled clock is 0-indexed over every monotonic read: the
    # deadline base, the pre-admission tick, the post-admission tick,
    # the single bounded hash tick and the post-hash tick.
    # expire_at 2: the tick immediately after production admission
    # (post-decode); expire_at 4: the tick after bounded hashing
    # (post-hash).  Both land before any slot reservation, so no
    # protected namespace work happens.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    # A genuinely preexisting reserved stage: the early refusal must
    # not observe or claim it, and must leave it untouched.
    stage = root / ".current-policy.stage"
    _write_private(stage, b"retained reserved stage", 0o400)
    base = time.monotonic()
    fake, count = _fake_monotonic(base, expire_at)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    monkeypatch.setattr(time, "monotonic", fake)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert caught.value.stage is selection.Stage.UNRESOLVED
    assert count["n"] == expire_at + 1
    assert opens == []
    assert sorted(entry.name for entry in root.iterdir()) == sorted(
        [".current-policy.stage", "current-policy.json", _digest(WIRE_A) + ".bin"]
    )
    assert stage.read_bytes() == b"retained reserved stage"


def test_truthful_late_durable_return(tmp_path, monkeypatch):
    # The cooperative cut lands after the transaction latched DURABLE
    # but before the receipt could return: the refusal reports the
    # truthful late state (durable, clean, stage absent), the new
    # record is present, and no false absence or pending state
    # follows.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    real_tick = publisher._tick

    def late(end):
        if any(
            slot is not None and slot.state is publisher.Publication.DURABLE
            for slot in publisher._SLOTS
        ):
            raise publisher._Failure()
        real_tick(end)

    with monkeypatch.context() as ctx:
        ctx.setattr(selection, "_tick", late)
        with pytest.raises(selection.PolicySelectError) as caught:
            selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.DURABLE, publisher.Cleanup.CLEAN)
    assert caught.value.stage is selection.Stage.ABSENT
    assert (
        (root / "current-policy.json").read_bytes()
        == _render_selection(2, len(WIRE_B), _digest(WIRE_B))
    )
    assert all(slot is None for slot in publisher._SLOTS)
    again = selection.select_installed_policy(WIRE_B, directory=str(root))
    assert again.generation == 3


def test_stage_flush_expiry_preserves_pending_custody_and_retry(tmp_path, monkeypatch):
    # The clock expires immediately after the stage file flush (the
    # third real flush): the pre-attempt fault resolves the proven
    # stage, the slot stays pending for the actual authorized retry,
    # and the old selector is never touched.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    base = time.monotonic()
    flushed = {"n": 0}
    real_fsync = os.fsync

    def jump_fsync(fd):
        real_fsync(fd)
        flushed["n"] += 1
        if flushed["n"] == 3:
            monkeypatch.setattr(time, "monotonic", lambda: base + 3600.0)

    monkeypatch.setattr(os, "fsync", jump_fsync)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.PENDING
    )
    assert caught.value.stage is selection.Stage.ABSENT
    assert flushed["n"] == 3
    after = os.lstat(str(selector))
    assert (selector_before.st_dev, selector_before.st_ino) == (
        after.st_dev,
        after.st_ino,
    )
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))
    assert not (root / ".current-policy.stage").exists()
    assert any(slot is not None and slot.pending for slot in publisher._SLOTS)
    receipt = publisher.retry_cleanup()
    assert receipt.status is publisher.Cleanup.CLEAN
    assert receipt.remaining == 0
    assert all(slot is None for slot in publisher._SLOTS)
    again = selection.select_installed_policy(WIRE_B, directory=str(root))
    assert again.generation == 2


# ------------------------------- genuine installer, reader and A-B-A evidence


def test_real_installer_reader_aba_generations_exact_bytes(tmp_path, monkeypatch):
    # A named fixture initializes a synthetic existing selector at
    # generation 1 for wire A.  The genuine installer stores payload
    # B; the real capture reader observes A, B and A at generations
    # 1, 2 and 3 plus a further same-wire generation 4, matching
    # exact decoded bytes; the immutable payload inodes stay
    # invariant and the content installation performs no selector
    # writes.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    reader = capture.PolicyCaptureReader(str(root))
    selector = root / "current-policy.json"
    payload_a = root / (_digest(WIRE_A) + ".bin")
    payload_b = root / (_digest(WIRE_B) + ".bin")
    payload_a_before = os.lstat(str(payload_a))
    selector_bytes_1 = selector.read_bytes()
    assert selector_bytes_1 == _render_selection(1, len(WIRE_A), _digest(WIRE_A))
    # No selector writes from the genuine content installation:
    # counted real opens and writes while the installer runs.
    selector_fds = set()
    selector_writes = []
    real_open = os.open
    real_write = os.write

    def tracking_open(name, flags, *args, **kwargs):
        fd = real_open(name, flags, *args, **kwargs)
        if name == "current-policy.json":
            selector_fds.add(fd)
        return fd

    def counting_write(fd, data, *args, **kwargs):
        if fd in selector_fds:
            selector_writes.append(len(data))
        return real_write(fd, data, *args, **kwargs)

    with monkeypatch.context() as ctx:
        ctx.setattr(os, "open", tracking_open)
        ctx.setattr(os, "write", counting_write)
        selector_before = os.lstat(str(selector))
        receipt = payload.install_policy_payload(WIRE_B, directory=str(root))
    assert receipt.outcome is payload.PayloadInstallOutcome.INSTALLED
    assert selector_writes == []
    assert (os.lstat(str(selector)).st_dev, os.lstat(str(selector)).st_ino) == (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    assert selector.read_bytes() == selector_bytes_1
    # The real reader observes generation 1 / wire A before selection.
    captured_1 = reader.capture()
    assert captured_1.selection.generation == 1
    assert captured_1.selection.selection_bytes == selector_bytes_1
    assert captured_1.wire_bytes == WIRE_A
    payload_b_ino = os.lstat(str(payload_b))
    # A, B and A at generations 2, 3 and 4 (further same-wire).
    receipt_2 = selection.select_installed_policy(WIRE_B, directory=str(root))
    assert receipt_2.outcome is selection.PolicySelectOutcome.SELECTED
    assert receipt_2.selection is publisher.Publication.DURABLE
    assert receipt_2.cleanup is publisher.Cleanup.CLEAN
    assert receipt_2.generation == 2
    assert receipt_2.wire_digest == _digest(WIRE_B)
    assert receipt_2.selection_bytes == _render_selection(2, len(WIRE_B), _digest(WIRE_B))
    captured_2 = reader.capture()
    assert captured_2.selection.generation == 2
    assert captured_2.selection.selection_bytes == receipt_2.selection_bytes
    assert captured_2.wire_bytes == WIRE_B
    # The production wire decoder admits the captured bytes.
    wire.admit_policy_bytes(captured_2.wire_bytes)
    receipt_3 = selection.select_installed_policy(WIRE_A, directory=str(root))
    assert receipt_3.generation == 3
    assert receipt_3.selection_bytes == _render_selection(3, len(WIRE_A), _digest(WIRE_A))
    captured_3 = reader.capture()
    assert captured_3.selection.generation == 3
    assert captured_3.wire_bytes == WIRE_A
    # A further same-wire generation: the same wire A, a new
    # canonical record identity.
    receipt_4 = selection.select_installed_policy(WIRE_A, directory=str(root))
    assert receipt_4.generation == 4
    assert receipt_4.selection_bytes == _render_selection(4, len(WIRE_A), _digest(WIRE_A))
    assert receipt_4.selection_bytes != receipt_3.selection_bytes
    captured_4 = reader.capture()
    assert captured_4.selection.generation == 4
    assert captured_4.selection.selection_bytes == receipt_4.selection_bytes
    assert captured_4.wire_bytes == WIRE_A
    # The immutable payload inodes are invariant across all selections.
    assert (os.lstat(str(payload_a)).st_dev, os.lstat(str(payload_a)).st_ino) == (
        payload_a_before.st_dev,
        payload_a_before.st_ino,
    )
    assert (os.lstat(str(payload_b)).st_dev, os.lstat(str(payload_b)).st_ino) == (
        payload_b_ino.st_dev,
        payload_b_ino.st_ino,
    )
    # No reserved stage residue; the namespace holds exactly the two
    # payloads and the selector.
    assert not (root / ".current-policy.stage").exists()
    assert sorted(entry.name for entry in root.iterdir()) == sorted(
        [_digest(WIRE_A) + ".bin", _digest(WIRE_B) + ".bin", "current-policy.json"]
    )


def test_actual_operation_order_select(tmp_path, monkeypatch):
    # Counted real I/O: the exact operation order and every
    # visibility and durability cut, including the payload directory
    # flush before replacement and the selection directory flush and
    # readback after it.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    events = _witness_order(monkeypatch)
    receipt = selection.select_installed_policy(WIRE_B, directory=str(root))
    assert receipt.generation == 2
    open_events = [e for e in events if e[0] == "open"]
    dir_opens = [e for e in open_events if e[1][1] & os.O_DIRECTORY]
    sel_opens = [e for e in open_events if e[1][0] == "current-policy.json"]
    payload_opens = [e for e in open_events if e[1][0] == _digest(WIRE_B) + ".bin"]
    stage_opens = [e for e in open_events if e[1][0] == ".current-policy.stage"]
    flocks = [e for e in events if e[0] == "flock"]
    fsyncs = [e for e in events if e[0] == "fsync"]
    replaces = [e for e in events if e[0] == "replace"]
    unlinks = [e for e in events if e[0] == "unlink"]
    writes = [e for e in events if e[0] == "write"]
    # One lock hold, one stage creation, one pre-attempt staged-name
    # verification open, one replace, no unlink on the success path.
    assert len(dir_opens) >= 1
    assert len(flocks) == 1
    assert len(sel_opens) == 3
    assert len(payload_opens) == 1
    assert len(stage_opens) == 2
    assert len(replaces) == 1
    assert unlinks == []
    # Exactly the four flush boundaries: the verified payload file
    # flush, the payload directory flush before the selector becomes
    # visible, the staged record file flush, the selection directory
    # flush after the replace.
    assert len(fsyncs) == 4
    root_fd = flocks[0][1][0]
    payload_fd = payload_opens[0][1][2]
    stage_fd = stage_opens[0][1][2]
    assert fsyncs[0][1][0] == payload_fd
    assert fsyncs[1][1][0] == root_fd
    assert fsyncs[2][1][0] == stage_fd
    assert fsyncs[3][1][0] == root_fd

    def _position(event):
        return event[2]

    assert (
        _position(dir_opens[0])
        < _position(flocks[0])
        < _position(sel_opens[0])
        < _position(payload_opens[0])
        < _position(fsyncs[0])
        < _position(fsyncs[1])
        < _position(stage_opens[0])
        < _position(replaces[0])
        < _position(sel_opens[1])
        < _position(fsyncs[3])
        < _position(sel_opens[2])
    )
    # The bounded record write lands on the created stage fd before
    # the seal flush; the staged-name verification open is after the
    # seal flush and before the one replace.
    stage_writes = [e for e in writes if e[1][0] == stage_fd]
    record = _render_selection(2, len(WIRE_B), _digest(WIRE_B))
    assert len(stage_writes) == 1
    assert stage_writes[0][1][1] == len(record)
    assert (
        _position(stage_opens[0])
        < _position(stage_writes[0])
        < _position(fsyncs[2])
        < _position(stage_opens[1])
        < _position(replaces[0])
    )
    # The final namespace and prior-selection rechecks run after the
    # complete staged-name verify and immediately before the one
    # replace: only the namespace re-walk opens anything in that
    # window, and the prior recheck itself opens no descriptor.
    lo = _position(stage_opens[1])
    hi = _position(replaces[0])
    late_opens = [e for e in open_events if lo < e[2] < hi]
    assert len(late_opens) >= 1
    assert all(e[1][1] & os.O_DIRECTORY for e in late_opens)
    # The replace is fd-relative within the locked root.
    source, destination, kwargs = replaces[0][1][0], replaces[0][1][1], replaces[0][1][2]
    assert source == ".current-policy.stage"
    assert destination == "current-policy.json"
    assert kwargs == {"src_dir_fd": root_fd, "dst_dir_fd": root_fd}


def test_two_fresh_writer_processes_serialize_on_one_root(tmp_path):
    # Two fresh owned writer processes (independent interpreters) run
    # against one actual root and the same lock, with deterministic
    # synchronization: ordered success through the cooperating lock,
    # consecutive generations, no reused published generation.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    assert (
        payload.install_policy_payload(WIRE_B, directory=str(root)).outcome
        is payload.PayloadInstallOutcome.INSTALLED
    )
    sync = tmp_path / "writer-first.started"
    environment = _child_environment()
    wire_hex = WIRE_B.hex()
    children = []
    try:
        for role in ("first", "second"):
            children.append(
                subprocess.Popen(
                    [sys.executable, "-c", _TWO_WRITER_CHILD, str(root), role, wire_hex, str(sync)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=environment,
                    preexec_fn=_child_limits,
                )
            )
        outputs = []
        for child in children:
            out, err = child.communicate(timeout=60)
            assert child.returncode == 0, err
            outputs.append(out.strip())
        # Ordered success: the first writer takes generation 2 under
        # the lock, the second blocks on the same lock, then reads the
        # actual current record and takes generation 3.
        assert sorted(outputs) == ["SELECTED:2", "SELECTED:3"]
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)
    assert (
        (root / "current-policy.json").read_bytes()
        == _render_selection(3, len(WIRE_B), _digest(WIRE_B))
    )
    assert not (root / ".current-policy.stage").exists()


def test_retained_stage_refuses_after_restart_without_mutation(tmp_path):
    # A fresh independent-interpreter writer over a root retaining a
    # reserved stage entry refuses before any mutation: the retained
    # entry, the selector and the payload are byte- and inode-exact.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    stage = root / ".current-policy.stage"
    stage_bytes = b"retained from a previous interrupted writer"
    _write_private(stage, stage_bytes, 0o600)
    selector_before = os.lstat(str(selector))
    stage_before = os.lstat(str(stage))
    payload_b_before = os.lstat(str(root / (_digest(WIRE_B) + ".bin")))
    child = subprocess.Popen(
        [sys.executable, "-c", _RESTART_REFUSAL_CHILD, str(root), WIRE_B.hex()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_child_environment(),
        preexec_fn=_child_limits,
    )
    try:
        out, err = child.communicate(timeout=60)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=5)
    assert child.returncode == 0, err
    assert out.strip() == "REFUSED:CONFLICT:CLEAN:PRESENT"
    stage_after = os.lstat(str(stage))
    assert (stage_before.st_dev, stage_before.st_ino) == (
        stage_after.st_dev,
        stage_after.st_ino,
    )
    assert stage.read_bytes() == stage_bytes
    assert (os.lstat(str(selector)).st_dev, os.lstat(str(selector)).st_ino) == (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))
    payload_b_after = os.lstat(str(root / (_digest(WIRE_B) + ".bin")))
    assert (payload_b_before.st_dev, payload_b_before.st_ino) == (
        payload_b_after.st_dev,
        payload_b_after.st_ino,
    )


# ------------------------------------------------------- payload conflicts


@pytest.mark.parametrize(
    "kind", ["missing", "tampered", "mode", "nlink", "wrong-digest"]
)
def test_payload_conflict_refuses_with_selector_intact(tmp_path, kind):
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    payload_b = root / (_digest(WIRE_B) + ".bin")
    if kind == "missing":
        os.unlink(str(payload_b))
        wire_bytes, expected = WIRE_B, publisher.Publication.NOT_PUBLISHED
    elif kind == "tampered":
        data = payload_b.read_bytes() + b"X"
        os.chmod(str(payload_b), 0o600)
        fd = os.open(str(payload_b), os.O_WRONLY)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
        os.chmod(str(payload_b), 0o400)
        wire_bytes, expected = WIRE_B, publisher.Publication.CONFLICT
    elif kind == "mode":
        os.chmod(str(payload_b), 0o644)
        wire_bytes, expected = WIRE_B, publisher.Publication.CONFLICT
    elif kind == "nlink":
        os.link(str(payload_b), str(root / "extra-link.bin"))
        wire_bytes, expected = WIRE_B, publisher.Publication.CONFLICT
    else:  # wrong-digest: an admissible wire with no installed payload
        wire_bytes, expected = WIRE_C, publisher.Publication.NOT_PUBLISHED
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(wire_bytes, directory=str(root))
    _assert_fixed_refusal(caught, expected, publisher.Cleanup.CLEAN)
    assert caught.value.stage is selection.Stage.ABSENT
    after = os.lstat(str(selector))
    assert (selector_before.st_dev, selector_before.st_ino) == (
        after.st_dev,
        after.st_ino,
    )
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))
    assert not (root / ".current-policy.stage").exists()


_PAYLOAD_SYMLINK_CHILD = r"""
import hashlib, json, os, stat, sys

root = sys.argv[1]
wire_a = bytes.fromhex(sys.argv[2])
wire_b = bytes.fromhex(sys.argv[3])

from slaif_raggedized_helper.policy_selection import _KIND
from slaif_raggedized_helper.private_policy_selection import (
    PolicySelectError,
    Stage,
    select_installed_policy,
)
from slaif_raggedized_helper.private_report_publication import (
    Cleanup,
    Publication,
)

def digest(wire):
    return hashlib.sha256(wire).hexdigest()

def record(generation, wire):
    return json.dumps(
        {
            "generation": generation,
            "kind": _KIND,
            "schema": 1,
            "wire_bytes": len(wire),
            "wire_sha256": digest(wire),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")

def seal(path, data, mode):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(path, mode)

seal(os.path.join(root, "current-policy.json"), record(1, wire_a), 0o400)
seal(os.path.join(root, digest(wire_b) + ".bin"), wire_b, 0o400)
target = os.path.join(root, "foreign-payload.bin")
seal(target, wire_b, 0o600)
os.unlink(os.path.join(root, digest(wire_b) + ".bin"))
os.symlink(target, os.path.join(root, digest(wire_b) + ".bin"))

try:
    select_installed_policy(wire_b, directory=root)
except PolicySelectError as error:
    assert error.selection is Publication.CONFLICT, error.selection
    # A no-follow open refusal on a symlink is an unresolved
    # acquisition: the counted cell keeps the truthful custody
    # pending, never clean.
    assert error.cleanup is Cleanup.PENDING, error.cleanup
    assert error.stage is Stage.ABSENT, error.stage
else:
    raise AssertionError("symlink payload must conflict")

assert open(os.path.join(root, "current-policy.json"), "rb").read() == record(1, wire_a)
entry = os.lstat(os.path.join(root, digest(wire_b) + ".bin"))
assert stat.S_ISLNK(entry.st_mode), entry
assert os.readlink(os.path.join(root, digest(wire_b) + ".bin")) == target
assert not os.path.lexists(os.path.join(root, ".current-policy.stage"))
print("ok")
"""


def test_payload_symlink_conflict_retains_pending_in_fresh_process(tmp_path):
    # A no-follow open refusal on a symlink payload final is an
    # unresolved acquisition under the shared token model: the counted
    # cell permanently keeps the slot pending, so the actual retained
    # PENDING custody is witnessed in one fresh bounded owned exec
    # child; the shared parent pool stays completely clean.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _PAYLOAD_SYMLINK_CHILD,
            str(root),
            WIRE_A.hex(),
            WIRE_B.hex(),
        ],
        capture_output=True,
        text=True,
        env=_child_environment(),
        timeout=10,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "ok"
    assert os.path.islink(str(root / (_digest(WIRE_B) + ".bin")))
    assert (root / "current-policy.json").read_bytes() == _render_selection(
        1, len(WIRE_A), _digest(WIRE_A)
    )
    assert all(slot is None for slot in publisher._SLOTS)


# ---------------------------------------------------- current record states


@pytest.mark.parametrize("kind", ["missing", "malformed", "exhausted"])
def test_current_record_states_refuse(tmp_path, kind):
    root = Path(str(tmp_path / "private"))
    root.mkdir(mode=0o700)
    os.chmod(str(root), 0o700)
    _write_private(root / (_digest(WIRE_B) + ".bin"), WIRE_B)
    if kind == "missing":
        expected = publisher.Publication.NOT_PUBLISHED
        entries = [_digest(WIRE_B) + ".bin"]
    elif kind == "malformed":
        _write_private(root / "current-policy.json", b"not a canonical record")
        expected = publisher.Publication.CONFLICT
        entries = [_digest(WIRE_B) + ".bin", "current-policy.json"]
    else:
        _write_private(
            root / "current-policy.json",
            _render_selection(2**63 - 1, len(WIRE_B), _digest(WIRE_B)),
        )
        expected = publisher.Publication.NOT_PUBLISHED
        entries = [_digest(WIRE_B) + ".bin", "current-policy.json"]
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, expected, publisher.Cleanup.CLEAN)
    # No namespace entry was created or changed.
    assert sorted(entry.name for entry in root.iterdir()) == sorted(entries)


# ------------------------------------------------------------ reserved stage


@pytest.mark.parametrize("kind", ["file", "symlink"])
def test_preexisting_reserved_stage_refuses_without_mutation(tmp_path, kind):
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    stage = root / ".current-policy.stage"
    if kind == "file":
        _write_private(stage, b"foreign retained stage", 0o600)
    else:
        target = tmp_path / "stage-target"
        _write_private(target, b"foreign retained target", 0o600)
        os.symlink(str(target), str(stage))
    stage_before = os.lstat(str(stage))
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.CONFLICT, publisher.Cleanup.CLEAN)
    assert caught.value.stage is selection.Stage.PRESENT
    # No mutation: the foreign entry is retained exactly and the
    # selector is intact.
    stage_after = os.lstat(str(stage))
    assert (stage_before.st_dev, stage_before.st_ino) == (
        stage_after.st_dev,
        stage_after.st_ino,
    )
    if kind == "file":
        assert stage.read_bytes() == b"foreign retained stage"
    assert (os.lstat(str(selector)).st_dev, os.lstat(str(selector)).st_ino) == (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))


# ---------------------------------------------------------- pre-replace faults


def _track_stage_fd(monkeypatch):
    stage_fd = {}
    real_open = os.open

    def stage_open(name, flags, *args, **kwargs):
        fd = real_open(name, flags, *args, **kwargs)
        if name == ".current-policy.stage":
            stage_fd["fd"] = fd
        return fd

    monkeypatch.setattr(os, "open", stage_open)
    return stage_fd


@pytest.mark.parametrize("operation", ["write", "fchmod", "fsync"])
def test_pre_replace_fault_keeps_selector_and_resolves_stage(tmp_path, monkeypatch, operation):
    # A controlled fault before the replace call: the old selected
    # name is preserved byte- and inode-exact, the proven stage is
    # resolved (known absence) and the truthful state is before
    # possible effect.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    stage_fd = _track_stage_fd(monkeypatch)
    if operation == "write":
        real_write = os.write

        def fault_write(fd, data, *args, **kwargs):
            if fd == stage_fd.get("fd"):
                raise OSError("controlled write fault")
            return real_write(fd, data, *args, **kwargs)

        monkeypatch.setattr(os, "write", fault_write)
    elif operation == "fchmod":
        real_fchmod = os.fchmod

        def fault_fchmod(fd, mode):
            if fd == stage_fd.get("fd"):
                raise OSError("controlled fchmod fault")
            return real_fchmod(fd, mode)

        monkeypatch.setattr(os, "fchmod", fault_fchmod)
    else:
        real_fsync = os.fsync

        def fault_fsync(fd):
            if fd == stage_fd.get("fd"):
                raise OSError("controlled fsync fault")
            return real_fsync(fd)

        monkeypatch.setattr(os, "fsync", fault_fsync)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert caught.value.stage is selection.Stage.ABSENT
    after = os.lstat(str(selector))
    assert (selector_before.st_dev, selector_before.st_ino) == (
        after.st_dev,
        after.st_ino,
    )
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))
    assert not (root / ".current-policy.stage").exists()


def test_uncertain_stage_observation_stays_unresolved(tmp_path, monkeypatch):
    # A controlled observation fault during the pre-attempt stage
    # resolution: the state stays unresolved even though an earlier
    # state looked known, the entry remains, and a later call refuses
    # on the retained name.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    stage_fd = _track_stage_fd(monkeypatch)
    faulted = {"value": False}
    real_write = os.write

    def fault_write(fd, data, *args, **kwargs):
        if fd == stage_fd.get("fd") and not faulted["value"]:
            faulted["value"] = True
            raise OSError("controlled write fault")
        return real_write(fd, data, *args, **kwargs)

    monkeypatch.setattr(os, "write", fault_write)
    real_stat = os.stat

    def fault_stage_stat(name, *args, **kwargs):
        if faulted["value"] and name == ".current-policy.stage":
            raise PermissionError("controlled observation fault")
        return real_stat(name, *args, **kwargs)

    monkeypatch.setattr(os, "stat", fault_stage_stat)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN
    )
    assert caught.value.stage is selection.Stage.UNRESOLVED
    stage = root / ".current-policy.stage"
    assert stage.exists()
    assert (os.lstat(str(selector)).st_dev, os.lstat(str(selector)).st_ino) == (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    # Restore the real observation; the retained name blocks the next
    # selection without mutation.
    monkeypatch.setattr(os, "stat", real_stat)
    with pytest.raises(selection.PolicySelectError) as caught2:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught2, publisher.Publication.CONFLICT, publisher.Cleanup.CLEAN
    )
    assert caught2.value.stage is selection.Stage.PRESENT


def test_interrupted_unlink_observed_present_not_retried(tmp_path, monkeypatch):
    # A controlled interrupted unlink during pre-attempt resolution:
    # never retried, and the state is established by one fresh bounded
    # observation (the retained entry is PRESENT), not invented.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    stage = root / ".current-policy.stage"
    stage_fd = _track_stage_fd(monkeypatch)
    real_write = os.write

    def fault_write(fd, data, *args, **kwargs):
        if fd == stage_fd.get("fd"):
            raise OSError("controlled write fault")
        return real_write(fd, data, *args, **kwargs)

    monkeypatch.setattr(os, "write", fault_write)
    unlinks = []
    def interrupted_unlink(name, **kwargs):
        unlinks.append(name)
        raise OSError("controlled interrupted unlink")

    monkeypatch.setattr(os, "unlink", interrupted_unlink)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN
    )
    assert caught.value.stage is selection.Stage.PRESENT
    # One unlink attempt, never retried; the fresh observation found
    # the retained entry.
    assert unlinks == [".current-policy.stage"]
    assert stage.exists()
    after = os.lstat(str(selector))
    assert (selector_before.st_dev, selector_before.st_ino) == (
        after.st_dev,
        after.st_ino,
    )
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))


# -------------------------------------------------------------- post-replace


def test_replace_acts_then_raises_never_proves_rollback(tmp_path, monkeypatch):
    # A controlled fault after the replace acted: the refusal reports
    # possible effect, the absence proof never conflates with the
    # selector outcome, no automatic restoration happens, and the
    # retry reads the actual current generation plus one.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    real_replace = os.replace

    def replace_then_fault(source, destination, **kwargs):
        real_replace(source, destination, **kwargs)
        raise OSError("controlled post-replace fault")

    monkeypatch.setattr(os, "replace", replace_then_fault)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught, publisher.Publication.POSSIBLY_PUBLISHED, publisher.Cleanup.CLEAN
    )
    assert caught.value.stage is selection.Stage.ABSENT
    # The replace acted: the linked new selector holds the exact new
    # record on a new inode.
    after = os.lstat(str(selector))
    assert (after.st_dev, after.st_ino) != (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    assert selector.read_bytes() == _render_selection(2, len(WIRE_B), _digest(WIRE_B))
    assert not (root / ".current-policy.stage").exists()
    monkeypatch.undo()
    # The retry reads the actual current generation and allocates +1.
    again = selection.select_installed_policy(WIRE_B, directory=str(root))
    assert again.generation == 3


def test_replace_raises_without_acting_retains_reserved_stage(tmp_path, monkeypatch):
    # A controlled fault from the replace without effect: possible
    # effect, no automatic unlink, the old selected name intact, the
    # retained reserved name blocks the next selection, and
    # separately attributed operator recovery unblocks the actual
    # current generation plus one.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    selector_bytes_before = selector.read_bytes()

    def replace_fault(source, destination, **kwargs):
        raise OSError("controlled pre-effect replace fault")

    monkeypatch.setattr(os, "replace", replace_fault)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught, publisher.Publication.POSSIBLY_PUBLISHED, publisher.Cleanup.CLEAN
    )
    assert caught.value.stage is selection.Stage.PRESENT
    assert (os.lstat(str(selector)).st_dev, os.lstat(str(selector)).st_ino) == (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    assert selector.read_bytes() == selector_bytes_before
    stage = root / ".current-policy.stage"
    assert stage.exists()
    monkeypatch.undo()
    # The retained reserved name blocks new selection without mutation.
    with pytest.raises(selection.PolicySelectError) as caught2:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught2, publisher.Publication.CONFLICT, publisher.Cleanup.CLEAN
    )
    assert caught2.value.stage is selection.Stage.PRESENT
    assert selector.read_bytes() == selector_bytes_before
    # Operator-authorized recovery (separately attributed fixture
    # role) unlinks the retained stage; the next selection succeeds at
    # the actual current generation plus one.
    os.unlink(str(stage))
    again = selection.select_installed_policy(WIRE_B, directory=str(root))
    assert again.generation == 2


def test_post_replace_directory_fsync_fault(tmp_path, monkeypatch):
    # A controlled durability fault on the selection directory flush
    # after the replace: possible effect, stage absent, the new record
    # present, and no rollback.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    replaced = {"value": False}
    real_replace = os.replace

    def witnessing_replace(source, destination, **kwargs):
        replaced["value"] = True
        return real_replace(source, destination, **kwargs)

    monkeypatch.setattr(os, "replace", witnessing_replace)
    real_fsync = os.fsync

    def fault_root_fsync(fd):
        if replaced["value"] and stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("controlled post-replace directory fault")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fault_root_fsync)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught, publisher.Publication.POSSIBLY_PUBLISHED, publisher.Cleanup.CLEAN
    )
    assert caught.value.stage is selection.Stage.ABSENT
    after = os.lstat(str(selector))
    assert (after.st_dev, after.st_ino) != (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    assert selector.read_bytes() == _render_selection(2, len(WIRE_B), _digest(WIRE_B))


def test_post_replace_final_readback_fault(tmp_path, monkeypatch):
    # A controlled readback fault on the final selector readback
    # (after the directory flush): possible effect, stage absent, the
    # new record present, and no rollback.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    replaced = {"value": False}
    real_replace = os.replace

    def witnessing_replace(source, destination, **kwargs):
        replaced["value"] = True
        return real_replace(source, destination, **kwargs)

    monkeypatch.setattr(os, "replace", witnessing_replace)
    selector_fds_after = []
    real_open = os.open

    def tracking_open(name, flags, *args, **kwargs):
        fd = real_open(name, flags, *args, **kwargs)
        if replaced["value"] and name == "current-policy.json":
            selector_fds_after.append(fd)
        return fd

    monkeypatch.setattr(os, "open", tracking_open)
    real_read = os.read

    def corrupt_second_readback(fd, size):
        if len(selector_fds_after) >= 2 and fd == selector_fds_after[1]:
            return b""
        return real_read(fd, size)

    monkeypatch.setattr(os, "read", corrupt_second_readback)
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    _assert_fixed_refusal(
        caught, publisher.Publication.POSSIBLY_PUBLISHED, publisher.Cleanup.CLEAN
    )
    assert caught.value.stage is selection.Stage.ABSENT
    after = os.lstat(str(selector))
    assert (after.st_dev, after.st_ino) != (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    assert selector.read_bytes() == _render_selection(2, len(WIRE_B), _digest(WIRE_B))


# --------------------------------------------------- interruption and custody


def test_stage_interrupt_preserves_identity_and_resolves_stage(tmp_path, monkeypatch):
    # A selected non-Exception interruption at the stage file flush
    # preserves its identity; the proven stage is resolved and
    # descriptor custody completes.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_bytes = selector.read_bytes()
    cancel = KeyboardInterrupt()
    flushed = {"n": 0}
    real_fsync = os.fsync

    def interrupt_third(fd):
        flushed["n"] += 1
        if flushed["n"] == 3:
            raise cancel
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", interrupt_third)
    with pytest.raises(KeyboardInterrupt) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    assert caught.value is cancel
    assert selector.read_bytes() == selector_bytes
    assert not (root / ".current-policy.stage").exists()
    assert all(slot is None for slot in publisher._SLOTS)


def test_stage_observation_interrupt_preserves_identity_and_custody(
    tmp_path, monkeypatch
):
    # A selected non-Exception interruption in the post-attempt stage
    # observation cannot bypass the pending latch, the descriptor
    # cleanup or the guard release, and keeps its identity with the
    # earlier ordinary fault as the cause.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    replace_fault = OSError("controlled pre-effect replace fault")
    faulted = {"value": False}

    def replace_fault_raiser(source, destination, **kwargs):
        faulted["value"] = True
        raise replace_fault

    monkeypatch.setattr(os, "replace", replace_fault_raiser)
    cancel = KeyboardInterrupt()
    real_stat = os.stat

    def observation_interrupt(name, *args, **kwargs):
        if faulted["value"] and name == ".current-policy.stage":
            raise cancel
        return real_stat(name, *args, **kwargs)

    monkeypatch.setattr(os, "stat", observation_interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    # The first non-Exception interruption keeps its identity; the
    # earlier ordinary fault is retained as the cause.
    assert caught.value is cancel
    assert caught.value.__cause__ is replace_fault
    # The descriptor cleanup and guard release ran: complete custody.
    assert all(slot is None for slot in publisher._SLOTS)
    assert (os.lstat(str(selector)).st_dev, os.lstat(str(selector)).st_ino) == (
        selector_before.st_dev,
        selector_before.st_ino,
    )
    assert (root / ".current-policy.stage").exists()


def test_ambiguous_close_keeps_pending_custody_in_fresh_process(tmp_path):
    # A simulated ambiguous close of the locked root descriptor during
    # cleanup (fresh independent interpreter): the fixed refusal keeps
    # the truthful durable-but-pending state, the retained counted
    # slot stays visible, and nothing is rolled back.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    child = subprocess.Popen(
        [sys.executable, "-c", _AMBIGUOUS_CLOSE_CHILD, str(root), WIRE_B.hex()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_child_environment(),
        preexec_fn=_child_limits,
    )
    try:
        out, err = child.communicate(timeout=60)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=5)
    assert child.returncode == 0, err
    lines = out.strip().splitlines()
    assert lines[0] == "REFUSED:DURABLE:PENDING:ABSENT"
    assert lines[1] == "PENDING:1"
    # The replace acted before the ambiguous close: the new selector
    # is present; nothing is rolled back.
    assert (
        (root / "current-policy.json").read_bytes()
        == _render_selection(2, len(WIRE_B), _digest(WIRE_B))
    )


_ROOT_RELOCATION_CHILD = r"""
import hashlib, json, os, sys

root = sys.argv[1]
cut = sys.argv[2]
wire_a = bytes.fromhex(sys.argv[3])
wire_b = bytes.fromhex(sys.argv[4])

from slaif_raggedized_helper.policy_selection import _KIND
from slaif_raggedized_helper.private_policy_selection import (
    PolicySelectError,
    Stage,
    select_installed_policy,
)
from slaif_raggedized_helper.private_report_publication import (
    Cleanup,
    Publication,
)

def digest(wire):
    return hashlib.sha256(wire).hexdigest()

def record(generation, wire):
    return json.dumps(
        {
            "generation": generation,
            "kind": _KIND,
            "schema": 1,
            "wire_bytes": len(wire),
            "wire_sha256": digest(wire),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")

def seal(path, data, mode):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(path, mode)

seal(os.path.join(root, "current-policy.json"), record(1, wire_a), 0o400)
seal(os.path.join(root, digest(wire_b) + ".bin"), wire_b, 0o400)

relocated = root + ".relocated"
marker = b"requested root retained stage"
moved = {"done": False}
count = {"n": 0}
real_fsync = os.fsync
target = 3 if cut == "pre" else 4

def relocate_after_fsync(fd):
    real_fsync(fd)
    count["n"] += 1
    if count["n"] == target and not moved["done"]:
        moved["done"] = True
        # The genuine relocation: the locked (held) root moves away
        # and an independently prepared root takes the requested
        # path with its own retained reserved stage.
        os.rename(root, relocated)
        os.mkdir(root, 0o700)
        seal(os.path.join(root, ".current-policy.stage"), marker, 0o400)

os.fsync = relocate_after_fsync

try:
    select_installed_policy(wire_b, directory=root, deadline_ms=20000)
except PolicySelectError as error:
    if cut == "pre":
        assert error.selection is Publication.NOT_PUBLISHED, error.selection
    else:
        assert error.selection is Publication.POSSIBLY_PUBLISHED, error.selection
    # The relocated requested root is never probed or mutated: its
    # stage was not observed, so the reported state is unresolved,
    # while the held root's positively owned stage is custody-cleaned.
    assert error.cleanup is Cleanup.CLEAN, error.cleanup
    assert error.stage is Stage.UNRESOLVED, error.stage
else:
    raise AssertionError("relocated root must refuse")

# Both selectors stay exactly as the held root left them; no
# rollback is claimed.
if cut == "pre":
    assert open(os.path.join(relocated, "current-policy.json"), "rb").read() == record(1, wire_a)
else:
    assert open(os.path.join(relocated, "current-policy.json"), "rb").read() == record(2, wire_b)
assert not os.path.lexists(os.path.join(relocated, ".current-policy.stage"))
assert open(os.path.join(root, ".current-policy.stage"), "rb").read() == marker
assert not os.path.lexists(os.path.join(root, "current-policy.json"))
print("ok")
"""


@pytest.mark.parametrize("cut", ["pre", "post"])
def test_root_relocation_keeps_unresolved_custody_in_fresh_process(tmp_path, cut):
    # A genuine controlled root relocation at the affected recheck
    # cuts (fresh bounded owned exec child): after the real staged
    # verification the locked root moves away and an independently
    # prepared root with its own retained stage takes the requested
    # path.  The real final namespace recheck detects the mismatch;
    # the API keeps the truthful publication phase with the stage
    # UNRESOLVED, the held root's positively owned stage is
    # custody-cleaned, both selectors stay exactly as left, and
    # nothing is probed, mutated or rolled back.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _ROOT_RELOCATION_CHILD,
            str(root),
            cut,
            WIRE_A.hex(),
            WIRE_B.hex(),
        ],
        capture_output=True,
        text=True,
        env=_child_environment(),
        timeout=60,
        preexec_fn=_child_limits,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "ok"
    relocated = tmp_path / "private.relocated"
    stage = root / ".current-policy.stage"
    selector = root / "current-policy.json"
    assert stage.read_bytes() == b"requested root retained stage"
    assert not selector.exists()
    old_selector = relocated / "current-policy.json"
    if cut == "pre":
        assert old_selector.read_bytes() == _render_selection(
            1, len(WIRE_A), _digest(WIRE_A)
        )
    else:
        assert old_selector.read_bytes() == _render_selection(
            2, len(WIRE_B), _digest(WIRE_B)
        )
    assert not (relocated / ".current-policy.stage").exists()
    assert all(slot is None for slot in publisher._SLOTS)


# -------------------------------------------------------- diagnostics and state


def test_fixed_refusal_diagnostics_on_real_fault(tmp_path):
    # The fixed public diagnostics on a real fault: the constant
    # content-free message and the truthful three states, with no
    # content, path or directory in the error identity.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    payload.install_policy_payload(WIRE_B, directory=str(root))
    os.chmod(str(root / (_digest(WIRE_B) + ".bin")), 0o644)
    marker = "sel!ect-marker-xyz-987"
    with pytest.raises(selection.PolicySelectError) as caught:
        selection.select_installed_policy(WIRE_B, directory=str(root))
    error = caught.value
    assert type(error) is selection.PolicySelectError
    assert str(error) == "private policy selection refused"
    assert error.selection is publisher.Publication.CONFLICT
    assert error.cleanup is publisher.Cleanup.CLEAN
    assert error.stage is selection.Stage.ABSENT
    assert marker not in str(error)
    assert marker not in repr(error)
    assert all(marker not in str(argument) for argument in error.args)


def test_final_state_pool_clean():
    # Every selection transaction, including all fault and
    # interruption witnesses above, left the shared pool completely
    # released at these bytes.
    assert all(slot is None for slot in publisher._SLOTS)
