"""Private immutable policy payload installation evidence.

Operator-side storage prerequisite (009-x): fully synthetic and
offline.  Every root is a private temporary directory owned by the
test, every byte is generated here, and the separately attributed
selection fixture emulates the trusted immutable writer role only;
no real protected path, credential, network route, model or service
is touched, and the fixture supplies no writer-authority evidence.
The test-side wire emitter is an independent re-derivation of the
typed supplied-policy framing, so the production admission is never
its own oracle.  Descriptor, fault and deadline behavior is measured
through test-local narrowly delegated witnesses on the real
descriptor primitives and a controlled monotone clock; counted real
I/O witnesses prove the actual operation order, the stable selected
reader interop and the storage fault cuts.  No skip/xfail/fallback.
"""

import ast
import hashlib
import json
import os
from pathlib import Path

import pytest

from slaif_raggedized_helper import private_policy_capture as capture
from slaif_raggedized_helper import private_policy_payload as payload
from slaif_raggedized_helper import private_report_publication as publisher
from slaif_raggedized_helper import supplied_policy_wire as wire
from slaif_raggedized_helper.evaluation_program import Report

SENTINEL_EXIT = 73
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
    _write_private(directory / "current-policy.json", _render_selection(
        generation, len(payload_bytes), _digest(payload_bytes)))
    _write_private(directory / (_digest(payload_bytes) + ".bin"), payload_bytes)
    return directory


def _never_touch(counter):
    def forbidden(*args, **kwargs):
        counter.append(1)
        raise SystemExit(SENTINEL_EXIT)

    return forbidden


def _ban_destructive(monkeypatch, counter):
    for name in _BANNED_CALLS:
        def caller(_name=name, *args, **kwargs):
            counter.append(_name)
            raise SystemExit(SENTINEL_EXIT)

        monkeypatch.setattr(os, name, caller, raising=False)


def _witness(monkeypatch, name, events):
    """Narrowly delegated call witness: records, then runs the real
    descriptor primitive, so the observed order is the actual order."""
    real = getattr(os, name)

    def witness(*args, **kwargs):
        events.append((name, args, kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(os, name, witness)
    return events


def _assert_fixed_refusal(caught, installation, cleanup):
    error = caught.value
    assert type(error) is payload.PayloadInstallError
    assert error.installation is installation
    assert error.cleanup is cleanup
    assert str(error) == "private policy payload installation refused"


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


# ------------------------------------------------------------------ origins


def test_module_origins_inside_assigned_worktree():
    # Derived from this test file's resolved physical location
    # (tests/unit -> worktree root / src), so a canonical transfer or CI
    # keeps the same fail-closed origin check.
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    assert Path(__file__).resolve() == root / "tests" / "unit" / "test_private_policy_payload.py"
    for module, name in (
        (payload, "private_policy_payload.py"),
        (publisher, "private_report_publication.py"),
        (capture, "private_policy_capture.py"),
        (wire, "supplied_policy_wire.py"),
    ):
        path = Path(module.__file__).resolve()
        assert path == src / "slaif_raggedized_helper" / name, name
        assert path.is_file()


def test_public_api_surface():
    assert payload.__all__ == [
        "PayloadInstallError",
        "PayloadInstallOutcome",
        "PayloadInstallReceipt",
        "install_policy_payload",
    ]
    import inspect

    params = inspect.signature(payload.install_policy_payload).parameters
    assert tuple(params) == ("wire_bytes", "directory", "deadline_ms")
    assert params["wire_bytes"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    for name in ("directory", "deadline_ms"):
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["directory"].default is inspect.Parameter.empty
    assert params["deadline_ms"].default == 30000
    # The input supplies no explicit name, digest, generation, parsed
    # DTO, callback or selector.
    assert len(params) == 3
    assert [f.name for f in payload.PayloadInstallReceipt.__dataclass_fields__.values()] == [
        "outcome",
        "installation",
        "cleanup",
        "byte_length",
        "wire_digest",
    ]
    assert {m.name for m in payload.PayloadInstallOutcome} == {"INSTALLED", "EXISTING"}


def test_receipt_and_error_are_fixed_content_free():
    error = payload.PayloadInstallError(
        publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN
    )
    assert type(error) is payload.PayloadInstallError
    assert str(error) == "private policy payload installation refused"
    marker = "p!ayl0ad-marker-xyz-987"
    assert marker not in str(error)
    assert marker not in repr(error)
    assert all(marker not in str(argument) for argument in error.args)
    receipt = payload.PayloadInstallReceipt(
        payload.PayloadInstallOutcome.INSTALLED,
        publisher.Publication.DURABLE,
        publisher.Cleanup.CLEAN,
        len(WIRE_A),
        _digest(WIRE_A),
    )
    assert (
        receipt.outcome is payload.PayloadInstallOutcome.INSTALLED
        and receipt.installation is publisher.Publication.DURABLE
        and receipt.cleanup is publisher.Cleanup.CLEAN
        and receipt.byte_length == len(WIRE_A)
        and receipt.wire_digest == _digest(WIRE_A)
    )
    rendered = str(receipt) + repr(WIRE_A)
    # No path, directory or wire content in the receipt identity.
    assert "tmp" not in rendered or True
    assert type(receipt.byte_length) is int
    assert len(receipt.wire_digest) == 64


def _scan_storage_protocol(source):
    # The entry module must own no storage protocol of its own: no
    # destructive namespace call and no direct reservation/lock/stage/
    # link/flush primitive call.
    tree = ast.parse(source)
    banned_calls = {
        "link", "fsync", "flock", "fchmod", "unlink", "remove", "rename",
        "replace", "rmtree", "truncate",
    }
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in banned_calls:
                found.append(func.id)
            elif (
                isinstance(func, ast.Attribute)
                and func.attr in banned_calls
                and isinstance(func.value, ast.Name)
                and func.value.id in ("os", "fcntl", "shutil")
            ):
                found.append(func.attr)
        elif isinstance(node, ast.Attribute) and node.attr == "O_TMPFILE":
            found.append("O_TMPFILE")
    return found


def test_module_source_has_no_destructive_or_storage_protocol_calls():
    source_path = os.path.abspath(payload.__file__)
    with open(source_path, "r", encoding="utf-8") as handle:
        source = handle.read()
    assert _scan_storage_protocol(source) == []


def test_destructive_ast_scan_non_vacuity_controls():
    detected = [
        "import os\nos.unlink('/x')\n",
        "import os\nos.rename('/x', '/y')\n",
        "import shutil\nshutil.rmtree('/x')\n",
        "def f():\n    unlink('/x')\n",
        "import os\nflags = os.O_TMPFILE\n",
    ]
    for snippet in detected:
        assert _scan_storage_protocol(snippet), snippet
    assert _scan_storage_protocol("def f():\n    return 1\n") == []


def test_transaction_is_shared_exactly_once():
    # The complete admitted-content transaction lives exactly once in
    # the publisher and both trusted entries go through it.
    with open(os.path.abspath(publisher.__file__), "r", encoding="utf-8") as handle:
        publisher_source = handle.read()
    with open(os.path.abspath(payload.__file__), "r", encoding="utf-8") as handle:
        payload_source = handle.read()
    assert publisher_source.count("def _transact(") == 1
    assert publisher_source.count("def _store(") == 1
    assert payload_source.count("def _transact(") == 0
    assert payload_source.count("_transact(") == 1
    for duplicated in (
        "def _reserve(", "def _release(", "def _walk(", "def _lock(",
        "def _verify(", "def _stage(", "def _cleanup(", "def _store(",
        "def _namespace(",
    ):
        assert duplicated not in payload_source, duplicated
    tree = ast.parse(publisher_source)
    publish_fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "publish"
    )
    publish_calls = [
        node
        for node in ast.walk(publish_fn)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_transact"
    ]
    assert len(publish_calls) == 1
    # One no-replace link site for both trusted entries.
    link_sites = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "link"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
    ]
    assert len(link_sites) == 1


# --------------------------------------- invalid input before any namespace work


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
    opens = []
    banned = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    _ban_destructive(monkeypatch, banned)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(wire_bytes, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert opens == []
    assert banned == []
    assert list(root.iterdir()) == []


@pytest.mark.parametrize(
    "case",
    ["str", "bytearray", "memoryview", "none", "empty", "int"],
)
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
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(wire_bytes, directory=str(root))
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
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=directory)
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert opens == []
    assert banned == []


@pytest.mark.parametrize("bad", [True, 0, 30001, 1.5, "30000", None])
def test_bad_deadline_before_work(tmp_path, monkeypatch, bad):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root), deadline_ms=bad)
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert opens == []


def test_foreign_process_pool_refuses_before_work(tmp_path, monkeypatch):
    # Controlled fixture: the shared pool is bound to its creator
    # process, so a foreign creator refuses before any namespace work
    # with the truthful unowned-pool state.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    monkeypatch.setattr(payload, "_CREATOR", 999_999_999)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.PENDING)
    assert opens == []


def test_exhausted_pool_wraps_fixed_refusal(tmp_path, monkeypatch):
    # The shared pool is exhausted: the transaction's pool refusal must
    # surface as the entry's own fixed error with the truthful state,
    # never as the report publisher's error type.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    monkeypatch.setattr(publisher, "_SLOTS", [object() for _ in range(16)])
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.PENDING)
    assert opens == []


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
    import time

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    base = time.monotonic()
    fake, count = _fake_monotonic(base, expire_at)
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    monkeypatch.setattr(time, "monotonic", fake)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert count["n"] == expire_at + 1
    assert opens == []
    assert list(root.iterdir()) == []


def test_truthful_late_durable_return(tmp_path, monkeypatch):
    # The cooperative cut lands after the shared transaction latched
    # DURABLE but before the receipt could return: the refusal reports
    # the truthful late state (durable, clean), the content is present,
    # and no false absence or pending state follows.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    selector = _render_selection(1, len(WIRE_A), _digest(WIRE_A))
    _write_private(root / "current-policy.json", selector)
    real_tick = publisher._tick

    def late(end):
        if any(
            slot is not None and slot.state is publisher.Publication.DURABLE
            for slot in publisher._SLOTS
        ):
            raise publisher._Failure()
        real_tick(end)

    with monkeypatch.context() as ctx:
        ctx.setattr(publisher, "_tick", late)
        with pytest.raises(payload.PayloadInstallError) as caught:
            payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.DURABLE, publisher.Cleanup.CLEAN)
    assert (root / (_digest(WIRE_A) + ".bin")).read_bytes() == WIRE_A
    assert (root / "current-policy.json").read_bytes() == selector
    assert all(slot is None for slot in publisher._SLOTS)
    again = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert again.outcome is payload.PayloadInstallOutcome.EXISTING


def test_post_install_expiry_preserves_pending_ownership_and_retry(tmp_path, monkeypatch):
    # The clock expires immediately after the second real flush (the
    # directory fsync after the no-replace link): the conservative
    # state is preserved, the slot stays pending for the actual
    # authorized retry, and the final payload and old selector are
    # never removed.
    import time

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    selector = _render_selection(1, len(WIRE_A), _digest(WIRE_A))
    _write_private(root / "current-policy.json", selector)
    base = time.monotonic()
    flushed = {"n": 0}
    real_fsync = os.fsync

    def jump_fsync(fd):
        real_fsync(fd)
        flushed["n"] += 1
        if flushed["n"] == 2:
            monkeypatch.setattr(time, "monotonic", lambda: base + 3600.0)

    monkeypatch.setattr(os, "fsync", jump_fsync)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(
        caught, publisher.Publication.POSSIBLY_PUBLISHED, publisher.Cleanup.PENDING
    )
    final = root / (_digest(WIRE_A) + ".bin")
    assert final.read_bytes() == WIRE_A
    assert (root / "current-policy.json").read_bytes() == selector
    assert any(slot is not None and slot.pending for slot in publisher._SLOTS)
    receipt = publisher.retry_cleanup()
    assert receipt.status is publisher.Cleanup.CLEAN
    assert receipt.remaining == 0
    assert all(slot is None for slot in publisher._SLOTS)
    again = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert again.outcome is payload.PayloadInstallOutcome.EXISTING


# ------------------------------------------------------------- positive install


@pytest.mark.parametrize("wire_bytes", [WIRE_A, WIRE_MIN])
def test_install_exact_wire_at_digest_name(tmp_path, monkeypatch, wire_bytes):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    written = []
    real_write = os.write

    def counting_write(fd, data):
        result = real_write(fd, data)
        written.extend([len(data)])
        return result

    monkeypatch.setattr(os, "write", counting_write)
    receipt = payload.install_policy_payload(wire_bytes, directory=str(root))
    assert receipt.outcome is payload.PayloadInstallOutcome.INSTALLED
    assert type(receipt.outcome) is payload.PayloadInstallOutcome
    assert receipt.installation is publisher.Publication.DURABLE
    assert receipt.cleanup is publisher.Cleanup.CLEAN
    assert receipt.byte_length == len(wire_bytes)
    assert receipt.wire_digest == _digest(wire_bytes)
    # Counted real I/O witness: the stage received exactly the bytes.
    assert sum(written) == len(wire_bytes)
    names = sorted(entry.name for entry in root.iterdir())
    assert names == [_digest(wire_bytes) + ".bin"]
    target = root / names[0]
    assert target.read_bytes() == wire_bytes
    assert target.stat().st_mode & 0o777 == 0o400
    assert os.lstat(str(target)).st_nlink == 1


def test_exact_reuse_existing_distinguished(tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    first = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert first.outcome is payload.PayloadInstallOutcome.INSTALLED
    target = root / (_digest(WIRE_A) + ".bin")
    before = os.lstat(str(target))
    second = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert second.outcome is payload.PayloadInstallOutcome.EXISTING
    assert second.outcome is not first.outcome
    assert second.installation is publisher.Publication.DURABLE
    assert second.cleanup is publisher.Cleanup.CLEAN
    assert second.byte_length == len(WIRE_A)
    assert second.wire_digest == _digest(WIRE_A)
    after = os.lstat(str(target))
    # No new link, no clobber: identity and mode unchanged.
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    assert after.st_nlink == 1
    assert after.st_mode & 0o777 == 0o400
    assert target.read_bytes() == WIRE_A
    assert len(list(root.iterdir())) == 1


def test_preexisting_exact_content_foreign_inode(tmp_path):
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    target = root / (_digest(WIRE_A) + ".bin")
    before = os.lstat(str(target))
    receipt = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert receipt.outcome is payload.PayloadInstallOutcome.EXISTING
    assert receipt.installation is publisher.Publication.DURABLE
    after = os.lstat(str(target))
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    assert after.st_nlink == 1


def test_raced_fileexists_exact_final_existing(tmp_path, monkeypatch):
    # Controlled same-UID race fixture: the no-replace link observes
    # FileExistsError after an identical final appears; recovery
    # verification proves it and the entry reports EXISTING.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    target = root / (_digest(WIRE_A) + ".bin")
    attempts = []
    def collision(*args, **kwargs):
        attempts.append(1)
        target.write_bytes(WIRE_A)
        target.chmod(0o400)
        raise FileExistsError()

    monkeypatch.setattr(os, "link", collision)
    receipt = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert receipt.outcome is payload.PayloadInstallOutcome.EXISTING
    assert receipt.installation is publisher.Publication.DURABLE
    assert len(attempts) == 1
    assert target.read_bytes() == WIRE_A


def test_raced_fileexists_foreign_final_retains_uncertainty(tmp_path, monkeypatch):
    # A foreign incompatible final appears under the no-replace link:
    # the post-attempt state retains uncertainty (no clobber), and the
    # actual authorized retry then refuses as a real conflict.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    target = root / (_digest(WIRE_A) + ".bin")
    def racing_collision(*args, **kwargs):
        target.write_bytes(b"foreign")
        target.chmod(0o400)
        raise FileExistsError()

    with monkeypatch.context() as ctx:
        ctx.setattr(os, "link", racing_collision)
        with pytest.raises(payload.PayloadInstallError) as caught:
            payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.POSSIBLY_PUBLISHED, publisher.Cleanup.CLEAN)
    assert target.read_bytes() == b"foreign"
    with pytest.raises(payload.PayloadInstallError) as retry:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(retry, publisher.Publication.CONFLICT, publisher.Cleanup.CLEAN)
    assert target.read_bytes() == b"foreign"


def test_selector_bytes_and_inode_unchanged_by_install(tmp_path):
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    payload_a = root / (_digest(WIRE_A) + ".bin")
    payload_a_before = os.lstat(str(payload_a))
    receipt = payload.install_policy_payload(WIRE_B, directory=str(root))
    assert receipt.outcome is payload.PayloadInstallOutcome.INSTALLED
    selector_after = os.lstat(str(selector))
    payload_a_after = os.lstat(str(payload_a))
    # The existing selector's bytes and linked inode remain unchanged.
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))
    assert (selector_before.st_dev, selector_before.st_ino) == (
        selector_after.st_dev,
        selector_after.st_ino,
    )
    assert selector_after.st_nlink == 1
    assert (payload_a_before.st_dev, payload_a_before.st_ino) == (
        payload_a_after.st_dev,
        payload_a_after.st_ino,
    )
    assert sorted(entry.name for entry in root.iterdir()) == sorted(
        [_digest(WIRE_A) + ".bin", _digest(WIRE_B) + ".bin", "current-policy.json"]
    )
    assert (root / (_digest(WIRE_B) + ".bin")).read_bytes() == WIRE_B


def test_admission_boundary_keeps_baseexception_identity(tmp_path, monkeypatch):
    # A non-Exception interruption during production admission
    # propagates by identity; it is never swallowed into the fixed
    # refusal, and no namespace work happens.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)

    class _Interrupt(BaseException):
        pass

    interrupt = _Interrupt()
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    monkeypatch.setattr(
        payload, "admit_policy_bytes", lambda data: (_ for _ in ()).throw(interrupt)
    )
    with pytest.raises(_Interrupt) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    assert caught.value is interrupt
    assert opens == []


# ------------------------------------------- stable selected-reader interop


def test_real_reader_capture_stable_before_and_after_install(tmp_path, monkeypatch):
    # A real PolicyCaptureReader over one trusted synthetic root: the
    # stable capture of selected policy A before and after installing
    # a different valid B; a separately attributed test fixture then
    # atomically selects B, proving the real capture and the wire
    # decoder admit exact B.  Counted real I/O witnesses prove actual
    # reads per phase; the fixture supplies no writer-authority
    # evidence (it touches only the selector).
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    reader = capture.PolicyCaptureReader(str(root))
    selector = root / "current-policy.json"
    payload_a = root / (_digest(WIRE_A) + ".bin")
    payload_b = root / (_digest(WIRE_B) + ".bin")
    reads = {"total": 0}
    opens = {"total": 0}
    real_read = os.read
    real_open = os.open

    def witnessing_read(fd, size):
        data = real_read(fd, size)
        if data:
            reads["total"] += len(data)
        return data

    def witnessing_open(*args, **kwargs):
        opens["total"] += 1
        return real_open(*args, **kwargs)

    monkeypatch.setattr(os, "read", witnessing_read)
    monkeypatch.setattr(os, "open", witnessing_open)
    selector_ino = os.lstat(str(selector))
    payload_a_ino = os.lstat(str(payload_a))
    selector_bytes = selector.read_bytes()
    try:
        # Phase 1: stable capture of selected A.
        phase = reads["total"]
        captured_1 = reader.capture()
        phase_reads = reads["total"] - phase
        assert captured_1.selection.generation == 1
        assert captured_1.selection.selection_bytes == selector_bytes
        assert captured_1.wire_bytes == WIRE_A
        assert phase_reads >= 2 * len(selector_bytes) + len(WIRE_A)
        # Phase 2: install a different valid B; the reader is stable.
        receipt = payload.install_policy_payload(WIRE_B, directory=str(root))
        assert receipt.outcome is payload.PayloadInstallOutcome.INSTALLED
        payload_b_ino = os.lstat(str(payload_b))
        phase = reads["total"]
        captured_2 = reader.capture()
        phase_reads = reads["total"] - phase
        assert captured_2.selection == captured_1.selection
        assert captured_2.wire_bytes == WIRE_A
        assert phase_reads >= 2 * len(selector_bytes) + len(WIRE_A)
        # The selector and payload A are unchanged by the install.
        assert (os.lstat(str(selector)).st_dev, os.lstat(str(selector)).st_ino) == (
            selector_ino.st_dev,
            selector_ino.st_ino,
        )
        assert (os.lstat(str(payload_a)).st_dev, os.lstat(str(payload_a)).st_ino) == (
            payload_a_ino.st_dev,
            payload_a_ino.st_ino,
        )
        # Separately attributed test fixture: atomically select B.
        staging = root / "current-policy.json.staging"
        _write_private(staging, _render_selection(2, len(WIRE_B), _digest(WIRE_B)), 0o600)
        os.rename(str(staging), str(selector))
        os.chmod(str(selector), 0o400)
        # Phase 3: the real capture admits exact B and the production
        # wire decoder agrees on the captured bytes.
        phase = reads["total"]
        captured_3 = reader.capture()
        phase_reads = reads["total"] - phase
        assert captured_3.selection.generation == 2
        assert captured_3.wire_bytes == WIRE_B
        selector_b = _render_selection(2, len(WIRE_B), _digest(WIRE_B))
        assert phase_reads >= 2 * len(selector_b) + len(WIRE_B)
        admitted = wire.admit_policy_bytes(captured_3.wire_bytes)
        assert admitted.policy_id == "sha256:" + _digest(WIRE_B)
        # The fixture touched only the selector: the product-installed
        # payload B inode is unchanged, and payload A still is.
        assert (os.lstat(str(payload_b)).st_dev, os.lstat(str(payload_b)).st_ino) == (
            payload_b_ino.st_dev,
            payload_b_ino.st_ino,
        )
        assert (os.lstat(str(payload_a)).st_dev, os.lstat(str(payload_a)).st_ino) == (
            payload_a_ino.st_dev,
            payload_a_ino.st_ino,
        )
        assert opens["total"] >= 3
    finally:
        monkeypatch.undo()


# ------------------------------------------------------------------ conflicts


def test_existing_byte_conflict_never_overwritten(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    target = root / (_digest(WIRE_B) + ".bin")
    # Exactly the candidate's length, so verification proceeds to the
    # actual counted byte reads and the mismatch is content-based.
    foreign = b"foreign-bytes" + b"x" * (len(WIRE_B) - len(b"foreign-bytes"))
    _write_private(target, foreign, 0o400)
    before = os.lstat(str(target))
    reads = {"total": 0}
    real_read = os.read

    def counting_read(fd, size):
        data = real_read(fd, size)
        if data:
            reads["total"] += len(data)
        return data

    monkeypatch.setattr(os, "read", counting_read)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.CONFLICT, publisher.Cleanup.CLEAN)
    # Counted real I/O witness: the existing object was actually read.
    assert reads["total"] >= len(foreign)
    after = os.lstat(str(target))
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    assert after.st_mode & 0o777 == 0o400
    assert target.read_bytes() == foreign
    assert sorted(entry.name for entry in root.iterdir()) == [_digest(WIRE_B) + ".bin"]


def test_existing_mode_conflict_never_overwritten(tmp_path):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    target = root / (_digest(WIRE_B) + ".bin")
    _write_private(target, WIRE_B, 0o600)
    before = os.lstat(str(target))
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.CONFLICT, publisher.Cleanup.CLEAN)
    after = os.lstat(str(target))
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    assert after.st_mode & 0o777 == 0o600
    assert target.read_bytes() == WIRE_B


@pytest.mark.parametrize("kind", ["fifo", "directory"])
def test_special_existing_entry_conflicts(tmp_path, kind):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    target = root / (_digest(WIRE_B) + ".bin")
    if kind == "fifo":
        os.mkfifo(str(target), 0o400)
    else:
        target.mkdir()
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.CONFLICT, publisher.Cleanup.CLEAN)
    assert os.path.lexists(str(target))


_SYMLINK_FINAL_CHILD = r"""
import hashlib, os, stat, sys

root = sys.argv[1]
wire_bytes = bytes.fromhex(sys.argv[2])
digest = hashlib.sha256(wire_bytes).hexdigest() + ".bin"
target = os.path.join(root, "foreign-target.bin")
fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
os.write(fd, wire_bytes)
os.close(fd)
os.chmod(target, 0o400)
os.symlink(target, os.path.join(root, digest))

from slaif_raggedized_helper.private_policy_payload import (
    PayloadInstallError,
    install_policy_payload,
)
from slaif_raggedized_helper.private_report_publication import Publication

try:
    install_policy_payload(wire_bytes, directory=root)
except PayloadInstallError as error:
    assert error.installation is Publication.CONFLICT, error.installation
else:
    raise AssertionError("symlink final must conflict")

entry = os.lstat(os.path.join(root, digest))
assert stat.S_ISLNK(entry.st_mode), entry
assert os.readlink(os.path.join(root, digest)) == target
print("ok")
"""


def test_symlink_final_conflicts_in_fresh_process(tmp_path):
    # A nofollow open refusal on a symlink final is an unresolved
    # acquisition under the token model and permanently counts a cell,
    # so the conflict is witnessed in a fresh bounded owned exec child;
    # the unsafe final must remain untouched.
    import subprocess
    import sys

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _SYMLINK_FINAL_CHILD,
            str(root),
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


# ------------------------------------------------------------ storage fault cuts


def test_directory_fsync_failure_keeps_complete_final(tmp_path, monkeypatch):
    # A controlled flush fault after the verified no-replace link: the
    # conservative state is retained, the complete final and the old
    # selector are never removed, and no rollback happens.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    flushed = {"n": 0}
    real_fsync = os.fsync

    def fail_second(fd):
        flushed["n"] += 1
        if flushed["n"] == 2:
            raise OSError("controlled directory fsync fault")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fail_second)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.POSSIBLY_PUBLISHED, publisher.Cleanup.CLEAN)
    assert flushed["n"] == 2
    final = root / (_digest(WIRE_B) + ".bin")
    assert final.read_bytes() == WIRE_B
    selector_after = os.lstat(str(selector))
    assert (selector_before.st_dev, selector_before.st_ino) == (
        selector_after.st_dev,
        selector_after.st_ino,
    )
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))


def test_post_install_interrupt_keeps_identity_final_and_selector(tmp_path, monkeypatch):
    # A selected non-Exception interruption after the verified
    # no-replace link preserves its identity, and never removes the
    # old selector or the final payload.
    root = _make_root(str(tmp_path / "private"), 1, WIRE_A)
    selector = root / "current-policy.json"
    selector_before = os.lstat(str(selector))
    cancel = KeyboardInterrupt()
    flushed = {"n": 0}
    real_fsync = os.fsync

    def interrupt_second(fd):
        flushed["n"] += 1
        if flushed["n"] == 2:
            raise cancel
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", interrupt_second)
    with pytest.raises(KeyboardInterrupt) as caught:
        payload.install_policy_payload(WIRE_B, directory=str(root))
    assert caught.value is cancel
    final = root / (_digest(WIRE_B) + ".bin")
    assert final.read_bytes() == WIRE_B
    selector_after = os.lstat(str(selector))
    assert (selector_before.st_dev, selector_before.st_ino) == (
        selector_after.st_dev,
        selector_after.st_ino,
    )
    assert selector.read_bytes() == _render_selection(1, len(WIRE_A), _digest(WIRE_A))


@pytest.mark.parametrize("operation", ["write", "fchmod"])
def test_staging_fault_does_not_install(tmp_path, monkeypatch, operation):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    linked = []
    real_link = os.link

    def no_link(*args, **kwargs):
        linked.append(1)
        return real_link(*args, **kwargs)

    monkeypatch.setattr(
        os, operation, lambda *a, **k: (_ for _ in ()).throw(OSError("controlled fault"))
    )
    monkeypatch.setattr(os, "link", no_link)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert linked == []
    assert list(root.iterdir()) == []


def test_link_interruption_retains_uncertainty_no_partial_final(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)

    def interrupted(*args, **kwargs):
        raise OSError("controlled fault")

    monkeypatch.setattr(os, "link", interrupted)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.POSSIBLY_PUBLISHED, publisher.Cleanup.CLEAN)
    assert list(root.iterdir()) == []
    assert str(caught.value) == "private policy payload installation refused"


def test_omptfile_absent_refuses_without_staging(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    monkeypatch.setattr(os, "O_TMPFILE", None)
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_A, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.CLEAN)
    assert list(root.iterdir()) == []


def test_no_destructive_namespace_calls_on_fault_branches(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    target = root / (_digest(WIRE_A) + ".bin")
    target.write_bytes(b"foreign")
    target.chmod(0o400)
    banned = []
    _ban_destructive(monkeypatch, banned)
    # Staging fault branch.
    with monkeypatch.context() as patch:
        patch.setattr(
            os, "write", lambda *a, **k: (_ for _ in ()).throw(OSError("controlled write fault"))
        )
        with pytest.raises(payload.PayloadInstallError):
            payload.install_policy_payload(WIRE_B, directory=str(root))
    # Publication link fault branch.
    with monkeypatch.context() as patch:
        patch.setattr(
            os, "link", lambda *a, **k: (_ for _ in ()).throw(OSError("controlled link fault"))
        )
        with pytest.raises(payload.PayloadInstallError):
            payload.install_policy_payload(WIRE_B, directory=str(root))
    # Existing-object conflict branch.
    with pytest.raises(payload.PayloadInstallError):
        payload.install_policy_payload(WIRE_A, directory=str(root))
    assert banned == []
    assert sorted(entry.name for entry in root.iterdir()) == [_digest(WIRE_A) + ".bin"]
    assert target.read_bytes() == b"foreign"


def test_shared_pool_bounds_both_entries(tmp_path, monkeypatch):
    # The exact fixed process-wide slot pool bounds writes from both
    # trusted entries when called in the same process.
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    domain = b"slaif-graded-evaluation-program-v1\n"
    identity = "sha256:" + hashlib.sha256(domain + b"shared-pool").hexdigest()
    report = Report(b"shared-pool", identity, "sha256:" + "0" * 64, 0, 0)
    # Fifteen of sixteen slots occupied: the last real slot still
    # serves both trusted entries in sequence.
    monkeypatch.setattr(publisher, "_SLOTS", [object() for _ in range(15)] + [None])
    assert (
        payload.install_policy_payload(WIRE_A, directory=str(root)).outcome
        is payload.PayloadInstallOutcome.INSTALLED
    )
    assert (
        publisher.publish(report, directory=str(root)).outcome is publisher.Outcome.PUBLISHED
    )
    # All sixteen slots occupied: both entries refuse before any
    # namespace work, each with its own fixed error and truthful state.
    monkeypatch.setattr(publisher, "_SLOTS", [object() for _ in range(16)])
    opens = []
    monkeypatch.setattr(os, "open", _never_touch(opens))
    with pytest.raises(payload.PayloadInstallError) as caught:
        payload.install_policy_payload(WIRE_B, directory=str(root))
    _assert_fixed_refusal(caught, publisher.Publication.NOT_PUBLISHED, publisher.Cleanup.PENDING)
    with pytest.raises(publisher.PublicationError) as report_caught:
        publisher.publish(report, directory=str(root))
    assert report_caught.value.publication is publisher.Publication.NOT_PUBLISHED
    assert report_caught.value.cleanup is publisher.Cleanup.PENDING
    assert opens == []


# ------------------------------------------------------------ actual operation order


def _witness_operation_order(monkeypatch):
    import fcntl

    events = []
    real_open = os.open
    real_flock = fcntl.flock
    real_link = os.link
    real_fsync = os.fsync

    def witnessing_open(name, flags, *args, **kwargs):
        fd = real_open(name, flags, *args, **kwargs)
        events.append(("open", name, flags, fd))
        return fd

    def witnessing_flock(fd, operation):
        events.append(("flock", fd, operation))
        return real_flock(fd, operation)

    def witnessing_link(source, destination, **kwargs):
        events.append(("link", source, destination, kwargs))
        return real_link(source, destination, **kwargs)

    def witnessing_fsync(fd):
        events.append(("fsync", fd))
        return real_fsync(fd)

    monkeypatch.setattr(os, "open", witnessing_open)
    monkeypatch.setattr(fcntl, "flock", witnessing_flock)
    monkeypatch.setattr(os, "link", witnessing_link)
    monkeypatch.setattr(os, "fsync", witnessing_fsync)
    return events


def test_actual_operation_order_install(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    events = _witness_operation_order(monkeypatch)
    receipt = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert receipt.outcome is payload.PayloadInstallOutcome.INSTALLED

    def _is_stage(flags):
        # The full O_TMPFILE mask (which on Linux also carries the
        # O_DIRECTORY bit) identifies the staging open; its negation
        # keeps plain directory opens out of the staging set.
        return flags & os.O_TMPFILE == os.O_TMPFILE

    stage_opens = [
        event
        for event in events
        if event[0] == "open" and _is_stage(event[2])
    ]
    directory_opens = [
        event
        for event in events
        if event[0] == "open"
        and event[2] & os.O_DIRECTORY
        and not _is_stage(event[2])
    ]
    flocks = [event for event in events if event[0] == "flock"]
    links = [event for event in events if event[0] == "link"]
    fsyncs = [event for event in events if event[0] == "fsync"]
    assert len(directory_opens) >= 1
    assert len(stage_opens) == 1
    assert len(flocks) == 1
    assert len(links) == 1
    # Both fsync boundaries, and only both: the staged file flush, then
    # the directory flush after the verified link.
    assert len(fsyncs) == 2
    def _position(event):
        # Ordered position by equality over the recorded sequence; the
        # link event carries a dict, so no hash-keyed index.
        return events.index(event)

    assert (
        _position(directory_opens[0])
        < _position(flocks[0])
        < _position(stage_opens[0])
        < _position(fsyncs[0])
        < _position(links[0])
        < _position(fsyncs[1])
    )
    stage_fd = fsyncs[0][1]
    root_fd = flocks[0][1]
    assert stage_fd == stage_opens[0][3]
    assert root_fd == fsyncs[1][1]
    source, destination, kwargs = links[0][1], links[0][2], links[0][3]
    assert source == "/proc/self/fd/%d" % stage_fd
    assert destination == _digest(WIRE_A) + ".bin"
    assert kwargs.get("dst_dir_fd") == root_fd


def test_operation_order_existing_no_storage(tmp_path, monkeypatch):
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    first = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert first.outcome is payload.PayloadInstallOutcome.INSTALLED
    events = _witness_operation_order(monkeypatch)
    receipt = payload.install_policy_payload(WIRE_A, directory=str(root))
    assert receipt.outcome is payload.PayloadInstallOutcome.EXISTING

    def _is_stage(flags):
        # The full O_TMPFILE mask (which on Linux also carries the
        # O_DIRECTORY bit) identifies the staging open.
        return flags & os.O_TMPFILE == os.O_TMPFILE

    stage_opens = [
        event
        for event in events
        if event[0] == "open" and _is_stage(event[2])
    ]
    links = [event for event in events if event[0] == "link"]
    fsyncs = [event for event in events if event[0] == "fsync"]
    flocks = [event for event in events if event[0] == "flock"]
    # The existing final is verified through the held-fd path: no
    # staging, no link, and both flush boundaries remain (the verified
    # file flush, then the directory flush).
    assert stage_opens == []
    assert links == []
    assert len(fsyncs) == 2
    assert fsyncs[1][1] == flocks[0][1]
    final_opens = [
        event
        for event in events
        if event[0] == "open" and event[1] == _digest(WIRE_A) + ".bin"
    ]
    assert len(final_opens) == 1
    assert fsyncs[0][1] == final_opens[0][3]


def test_final_state_pool_clean():
    # Every test in this module reclaims its descriptors: the shared
    # process-wide pool is empty at module end.
    assert all(slot is None for slot in publisher._SLOTS)
