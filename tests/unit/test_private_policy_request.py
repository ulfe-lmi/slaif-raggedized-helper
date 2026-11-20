"""Private current-view request admission and freshness evidence.

Offline and fully synthetic: every root is a private temporary directory
owned by the test and every byte is generated here; no real protected path,
credential, network route, model or service is touched.  The test-side wire
emitter is an independent re-derivation of the typed component grammar, so
the composed route is never its own oracle.  One absolute request deadline
is witnessed with a controlled monotone clock where exact phase boundaries
are needed, and with the real monotonic clock where actual remaining-clock
lateness is the point; pointer swaps are trusted-writer fixture operations
between genuine reader boundaries; concurrency is synchronized with
deterministic events, never sleeps; no real wall behavior is described as
a hard guarantee.  Counting wrappers delegate to the real reader, decoder
and matcher at the intended boundaries.
"""

import dataclasses
import hashlib
import inspect
import json
import os
import sys
import threading
import time
from pathlib import Path

import pytest

from slaif_raggedized_helper import policy_selection as selection
from slaif_raggedized_helper import private_policy_capture as capture
from slaif_raggedized_helper import private_policy_request as ppr
from slaif_raggedized_helper import provenance_records as provenance
from slaif_raggedized_helper import supplied_policy as sp
from slaif_raggedized_helper import supplied_policy_wire as spw
from slaif_raggedized_helper.provenance_records import admit_record

_KIND = "slaif-current-policy-selection-v1"
_SELECTION = "current-policy.json"
_MAGIC = b"slaif-supplied-policy-view-v1\n"
CREDENTIAL = b"synthetic-credential-" + b"a" * 22  # exactly 43
CREDENTIAL_OTHER = b"synthetic-credential-" + b"b" * 22  # exactly 43
PRINCIPAL_ID = "alpha-1"
VERIFIER = hashlib.sha256(CREDENTIAL).digest()
OPERATIONS = ("search", "sources:read")
CORPORA = ("corpus-a",)
LABELS = ("label-a",)
DOC_ID = "doc-1"
REVISION_ID = "sha256:" + "0" * 64
SCOPE_DIGEST = "f" * 64


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
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(str(path), mode)


def _make_root(
    directory,
    generation,
    payload,
    *,
    selection_bytes=None,
    write_payload=True,
    write_selection=True,
):
    directory = Path(directory)
    directory.mkdir(mode=0o700)
    os.chmod(str(directory), 0o700)
    digest = _digest(payload)
    if write_selection:
        if selection_bytes is None:
            selection_bytes = _render_selection(generation, len(payload), digest)
        _write_private(directory / _SELECTION, selection_bytes)
    if write_payload:
        _write_private(directory / (digest + ".bin"), payload)
    return directory


def _replace_selection(root, generation, payload):
    # Trusted-writer fixture role: publish a new selected record.
    repl = Path(root).parent / ("swap-" + str(generation) + ".json")
    _write_private(repl, _render_selection(generation, len(payload), _digest(payload)))
    os.replace(str(repl), str(Path(root) / _SELECTION))


def _restore_selection(root, data):
    repl = Path(root).parent / "restore.json"
    _write_private(repl, data)
    os.replace(str(repl), str(Path(root) / _SELECTION))


def _u32(value):
    return value.to_bytes(4, "big")


def _s(text):
    raw = text.encode("utf-8")
    return _u32(len(raw)) + raw


def encode_principal(principal_id, verifier, operations, corpora=(), versions=(), labels=()):
    parts = [_s(principal_id), _u32(32) + verifier, _u32(len(operations))]
    for operation in operations:
        parts.append(_s(operation))
    parts.append(_u32(1))
    for values in (corpora, versions, labels):
        parts.append(_u32(len(values)))
        for value in values:
            parts.append(_s(value))
    return b"".join(parts)


def encode_policy(principals, documents):
    """Independent test-side wire framing per the typed component grammar."""
    parts = [_MAGIC, _u32(1), _u32(len(principals))]
    for principal in principals:
        parts.append(encode_principal(*principal))
    parts.append(_u32(len(documents)))
    for document_id, pairs in documents:
        parts.append(_s(document_id))
        parts.append(_u32(len(pairs)))
        for revision_id, scope_digest in pairs:
            parts.append(_s(revision_id))
            parts.append(_s(scope_digest))
    return b"".join(parts)


def _payload(
    operations=OPERATIONS,
    principal_id=PRINCIPAL_ID,
    verifier=VERIFIER,
    corpora=CORPORA,
    versions=(),
    labels=LABELS,
    doc_id=DOC_ID,
    revision_id=REVISION_ID,
    scope_digest=SCOPE_DIGEST,
):
    principals = [(principal_id, verifier, operations, corpora, versions, labels)]
    documents = [(doc_id, [(revision_id, scope_digest)])]
    return encode_policy(principals, documents)


def _grants(corpora=CORPORA, versions=(), labels=LABELS):
    return admit_record(
        "Grants",
        {"schema_version": 1, "corpora": corpora, "versions": versions, "labels": labels},
    )


def _expected_policy(
    operations=OPERATIONS,
    principal_id=PRINCIPAL_ID,
    verifier=VERIFIER,
    corpora=CORPORA,
    versions=(),
    labels=LABELS,
    doc_id=DOC_ID,
    revision_id=REVISION_ID,
    scope_digest=SCOPE_DIGEST,
):
    principal = sp.PrincipalSpec(
        principal_id, verifier, operations, _grants(corpora, versions, labels)
    )
    document = sp.DocumentRule(doc_id, ((revision_id, scope_digest),))
    return sp.admit_policy((principal,), (document,))


def _reader(root):
    return capture.PolicyCaptureReader(str(root))


def _counts():
    return {"capture": 0, "read_selection": 0, "admit": 0, "match": 0, "match_operations": []}


def _install_counting(
    monkeypatch, reader, counts, *, capture_delay_s=0.0, after_admit=None, after_match=None
):
    # Counting wrappers that delegate the real functions at the intended
    # boundaries; the real bound methods are always taken from the class,
    # so reinstalls never wrap a prior wrapper.  No production hook is
    # added.
    real_capture = capture.PolicyCaptureReader.capture.__get__(reader, type(reader))
    real_read_selection = capture.PolicyCaptureReader.read_selection.__get__(reader, type(reader))
    real_admit = spw.admit_policy_bytes
    real_match = sp.match_supplied

    def counting_capture(*args, **kwargs):
        counts["capture"] += 1
        result = real_capture(*args, **kwargs)
        if capture_delay_s:
            time.sleep(capture_delay_s)
        return result

    def counting_read_selection(*args, **kwargs):
        counts["read_selection"] += 1
        return real_read_selection(*args, **kwargs)

    def counting_admit(data):
        counts["admit"] += 1
        result = real_admit(data)
        if after_admit is not None:
            after_admit(result)
        return result

    def counting_match(policy, credential, operations):
        counts["match"] += 1
        counts["match_operations"].append(tuple(operations))
        result = real_match(policy, credential, operations)
        if after_match is not None:
            after_match(result)
        return result

    monkeypatch.setattr(reader, "capture", counting_capture)
    monkeypatch.setattr(reader, "read_selection", counting_read_selection)
    monkeypatch.setattr(ppr, "admit_policy_bytes", counting_admit)
    monkeypatch.setattr(ppr, "match_supplied", counting_match)


# ---------------------------------------------------------------- origins/API


def test_module_origin_is_assigned_worktree():
    # Derived from this test file's resolved physical location
    # (tests/unit/test_private_policy_request.py -> worktree root / src), so
    # a canonical transfer or CI keeps the same fail-closed origin check.
    src = Path(__file__).resolve().parents[2] / "src"
    for module in (ppr, capture, selection, sp, spw, provenance):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(src), "module origin outside assigned worktree"


def test_public_api_surface():
    assert ppr.__all__ == ["PolicyRequestAdmission", "PolicyRequestError", "request_current_view"]
    parameters = list(inspect.signature(ppr.request_current_view).parameters.items())
    assert [name for name, _ in parameters] == ["reader", "credential", "deadline_ms"]
    assert parameters[0][1].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[1][1].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[2][1].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters[2][1].default is inspect.Parameter.empty
    assert ppr._REQUIRED_OPERATIONS == ("search", "sources:read")


def test_error_is_fixed_input_free_value_error(tmp_path):
    with pytest.raises(ppr.PolicyRequestError) as excinfo:
        ppr.request_current_view(None, CREDENTIAL, deadline_ms=30000)
    error = excinfo.value
    assert isinstance(error, ValueError)
    assert error.args == ("private policy request refused",)
    assert error.__cause__ is None and error.__context__ is None
    # A refusal after a genuine internal fault also carries no context.
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload, selection_bytes=b'{"generation":')
    with pytest.raises(ppr.PolicyRequestError) as excinfo:
        ppr.request_current_view(_reader(root), CREDENTIAL, deadline_ms=30000)
    error = excinfo.value
    assert error.args == ("private policy request refused",)
    assert error.__cause__ is None and error.__context__ is None


def test_admission_constructor_refused_and_frozen(tmp_path):
    with pytest.raises(ppr.PolicyRequestError):
        ppr.PolicyRequestAdmission()
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    with pytest.raises(dataclasses.FrozenInstanceError):
        admission.principal_id = "other"
    assert repr(admission) == "PolicyRequestAdmission(<redacted>)"
    assert admission._reader is reader
    assert admission._owner_pid == os.getpid()
    assert admission._expected_selection_bytes == _render_selection(
        1, len(payload), _digest(payload)
    )


# ------------------------------------------------------------------ positive


def test_real_reader_decoder_matcher_positive_proof(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    expected_policy = _expected_policy()
    assert admission.principal_id == PRINCIPAL_ID
    assert admission.policy_id == expected_policy.policy_id
    assert admission.authorization_status == "SUPPLIED_POLICY_MATCH_ONLY"
    assert admission.operations == ("search", "sources:read")
    assert type(admission.grants) is provenance.Grants
    assert admission.grants.corpora == CORPORA and admission.grants.labels == LABELS
    assert admission.selection.generation == 1
    assert admission.selection.wire_bytes == len(payload)
    assert admission.selection.wire_sha256 == _digest(payload)
    assert admission.selection.selection_bytes == _render_selection(
        1, len(payload), _digest(payload)
    )
    assert admission.policy.policy_id == expected_policy.policy_id
    assert admission._reader is reader
    assert counts["capture"] == 1 and counts["admit"] == 1
    assert counts["match"] == 1
    assert counts["match_operations"] == [("search", "sources:read")]
    assert counts["read_selection"] == 1  # one bounded final selection reread
    assert reader._latched is False and reader._retained_slot is None
    # The raw credential is not retained in the admission record.
    values = [getattr(admission, field.name) for field in dataclasses.fields(admission)]
    assert not any(type(v) is bytes and CREDENTIAL in v for v in values)


def test_repeated_stable_selection_counts_only_bounded_rereads(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert admission.recheck(deadline_ms=30000) is True
    assert admission.recheck(deadline_ms=30000) is True
    # One full wire admission per successful request; later checks reopen
    # only the bounded selector and never re-admit the full wire bytes.
    assert counts["capture"] == 1 and counts["admit"] == 1
    assert counts["match"] == 1 and counts["read_selection"] == 3
    assert reader._latched is False


# ------------------------------------------------------------- negative wire


def test_unknown_credential_refused_before_final_reread(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL_OTHER, deadline_ms=30000)
    assert counts["capture"] == 1 and counts["admit"] == 1
    assert counts["match"] == 1 and counts["match_operations"] == [("search", "sources:read")]
    assert counts["read_selection"] == 0  # no final reread after a match refusal
    assert reader._latched is False
    # A separate new request on the clean owner admits the same view.
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert admission.recheck(deadline_ms=30000) is True


def test_missing_required_operation_refused(tmp_path, monkeypatch):
    payload = _payload(operations=("search",))
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 1 and counts["admit"] == 1
    assert counts["match"] == 1 and counts["read_selection"] == 0
    assert reader._latched is False
    # A separate new request on a clean owner admits the full view.
    full_payload = _payload()
    admission = ppr.request_current_view(
        _reader(_make_root(tmp_path / "root-2", 1, full_payload)),
        CREDENTIAL,
        deadline_ms=30000,
    )
    assert admission.recheck(deadline_ms=30000) is True


@pytest.mark.parametrize(
    "selection_bytes",
    [
        b'{"generation":',
        b"not-json",
        b'{"generation":1,"kind":"slaif-current-policy-selection-v1","schema":1,'
        b'"wire_bytes":42,"wire_sha256":"zz"}',
    ],
)
def test_malformed_selection_refused(tmp_path, monkeypatch, selection_bytes):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload, selection_bytes=selection_bytes)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 1 and counts["admit"] == 0
    assert counts["match"] == 0 and counts["read_selection"] == 0
    assert reader._latched is False


def test_missing_selection_refused(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload, write_selection=False)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 1 and counts["admit"] == 0
    assert reader._latched is False


# ------------------------------------------------- pointer and freshness


def test_same_semantic_view_at_new_publication_recheck_refused(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    # The exact same policy bytes published at a new selection generation:
    # the principal permissions would remain the same, yet the selected
    # identity changed, so the retained view refuses.
    _replace_selection(root, 2, payload)
    assert admission.recheck(deadline_ms=30000) is False
    assert admission.recheck(deadline_ms=30000) is False
    assert counts["read_selection"] == 2  # the latched refusal calls no reader
    assert reader._latched is False  # the latch is per-admission, not per-owner


def test_observed_denial_then_restoration_permanent_refusal(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["read_selection"] == 1
    _replace_selection(root, 2, payload)
    assert admission.recheck(deadline_ms=30000) is False
    assert counts["read_selection"] == 2
    _restore_selection(root, _render_selection(1, len(payload), _digest(payload)))
    # The observed denial is permanent even though the record is restored.
    assert admission.recheck(deadline_ms=30000) is False
    assert counts["read_selection"] == 2
    # A separate new request captures and admits the restored fresh view.
    fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 2 and counts["admit"] == 2
    assert fresh.recheck(deadline_ms=30000) is True


def test_pointer_changed_during_decode_refuses_request(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    swapped = []

    def swap_after_admit(_policy):
        if not swapped:
            swapped.append(1)
            _replace_selection(root, 2, payload)

    _install_counting(monkeypatch, reader, counts, after_admit=swap_after_admit)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 1 and counts["admit"] == 1
    assert counts["match"] == 1 and counts["read_selection"] == 1
    assert reader._latched is False
    _restore_selection(root, _render_selection(1, len(payload), _digest(payload)))
    # A separate new request on the restored view admits generation 1.
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert admission.selection.generation == 1
    assert counts["capture"] == 2 and counts["admit"] == 2


def test_pointer_changed_between_match_and_final_reread(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()

    def swap_after_match(_match):
        _replace_selection(root, 2, payload)

    _install_counting(monkeypatch, reader, counts, after_match=swap_after_match)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 1 and counts["admit"] == 1
    assert counts["match"] == 1 and counts["read_selection"] == 1
    assert reader._latched is False


# ---------------------------------------------------------- deadline budget


def test_real_remaining_clock_lateness_refuses_late_usable_success(tmp_path, monkeypatch):
    # Actual remaining-clock lateness: the genuine capture succeeds inside
    # its call cap, then the bounded request budget is spent before the
    # post-capture check, so the late usable success is refused.
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts, capture_delay_s=0.1)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=50)
    assert counts["capture"] == 1
    assert counts["admit"] == 0 and counts["match"] == 0 and counts["read_selection"] == 0
    assert reader._latched is False and reader._retained_slot is None
    # A separate new request on the clean owner admits the fresh view.
    counts2 = _counts()
    _install_counting(monkeypatch, reader, counts2)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts2["capture"] == 1 and counts2["admit"] == 1
    assert admission.recheck(deadline_ms=30000) is True


def test_controlled_clock_late_usable_success_refused_after_capture(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    _install_counting(monkeypatch, reader, counts)
    counting_capture = reader.capture  # the installed counting wrapper

    def late_capture(*args, **kwargs):
        result = counting_capture(*args, **kwargs)  # the real capture, counted
        clock["now"] = 1000.020  # past the 10 ms request end (1000.010)
        return result

    monkeypatch.setattr(reader, "capture", late_capture)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=10)
    assert counts["capture"] == 1
    assert counts["admit"] == 0 and counts["match"] == 0 and counts["read_selection"] == 0
    assert reader._latched is False and reader._retained_slot is None
    # A separate new request on the clean owner admits the fresh view.
    clock["now"] = 1000.0
    _install_counting(monkeypatch, reader, counts)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 2 and counts["admit"] == 1
    assert admission.recheck(deadline_ms=30000) is True


def test_controlled_clock_expiry_after_match_refuses_before_final_reread(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])

    def late_after_match(_match):
        clock["now"] = 1000.02  # past the 10 ms request end (1000.010)

    _install_counting(monkeypatch, reader, counts, after_match=late_after_match)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=10)
    assert counts["capture"] == 1 and counts["admit"] == 1 and counts["match"] == 1
    assert counts["read_selection"] == 0  # refused before the final reread
    assert reader._latched is False


def test_exhausted_original_budget_refuses_without_reader_call(tmp_path, monkeypatch):
    # The one absolute deadline established on entry is carried through
    # every recheck; an exhausted budget refuses without any reader call
    # despite a fresh-looking per-check timeout.
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    reads = []
    real_read_selection = capture.PolicyCaptureReader.read_selection.__get__(reader, type(reader))

    def counting_read(*args, **kwargs):
        result = real_read_selection(*args, **kwargs)
        reads.append(result)
        return result

    monkeypatch.setattr(reader, "read_selection", counting_read)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=100)
    assert len(reads) == 1  # the entry's one bounded final selection reread
    clock["now"] = 1000.200  # the 100 ms request end (1000.100) is exhausted
    assert admission.recheck(deadline_ms=30000) is False
    assert len(reads) == 1  # no reader call despite the fresh per-check timeout
    assert admission.recheck(deadline_ms=30000) is False
    assert len(reads) == 1  # still no reader call
    # The reader itself is unaffected.
    selection = real_read_selection(deadline_ms=30000)
    assert selection.generation == 1


@pytest.mark.parametrize("bad_deadline", [True, 0, 30001, "30000", 30000.5, -1])
def test_non_nominal_deadline_refused(tmp_path, bad_deadline):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(_reader(root), CREDENTIAL, deadline_ms=bad_deadline)


@pytest.mark.parametrize("bad_reader", [None, "/private/root", object()])
def test_non_nominal_reader_refused(tmp_path, bad_reader):
    with pytest.raises(ppr.PolicyRequestError) as excinfo:
        ppr.request_current_view(bad_reader, CREDENTIAL, deadline_ms=30000)
    assert excinfo.value.__cause__ is None and excinfo.value.__context__ is None


# --------------------------------------------------------------- ownership


def test_concurrent_operation_refused_while_owner_holds_guard(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    # Deterministic event synchronization: the first real read inside the
    # guarded operation signals, then waits; the owner provably holds the
    # guard while the concurrent call is attempted.
    real_read = os.read
    inside_guard = threading.Event()
    release = threading.Event()

    def spy_read(fd, size, *args, **kwargs):
        if not inside_guard.is_set():
            inside_guard.set()
            release.wait(timeout=30)
        return real_read(fd, size, *args, **kwargs)

    monkeypatch.setattr(os, "read", spy_read)
    result = {}

    def run_request():
        try:
            result["admission"] = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        except BaseException as exc:
            result["error"] = exc

    worker = threading.Thread(target=run_request)
    worker.start()
    try:
        assert inside_guard.wait(timeout=30)
        # The concurrent acquisition is refused with zero observations.
        with pytest.raises(capture.PolicyCaptureError):
            reader.read_selection(deadline_ms=30000)
    finally:
        release.set()
        worker.join(timeout=30)
    assert "admission" in result
    admission = result["admission"]
    assert counts["capture"] == 1
    # One zero-observation refused attempt plus one successful final reread.
    assert counts["read_selection"] == 2
    assert admission.recheck(deadline_ms=30000) is True
    assert reader._latched is False


def test_latched_reader_remains_invalid_under_concurrent_use(tmp_path):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    # White-box state setup: the owner is latched closed.
    reader._latched = True
    refusals = []

    def worker():
        for _ in range(3):
            try:
                reader.read_selection(deadline_ms=30000)
            except BaseException as exc:
                refusals.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(refusals) == 6
    assert all(isinstance(exc, capture.PolicyCaptureError) for exc in refusals)
    assert reader._latched is True
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)


def test_recheck_foreign_pid_refused_before_lock(tmp_path, monkeypatch):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    reads = []
    real_read_selection = capture.PolicyCaptureReader.read_selection.__get__(reader, type(reader))

    def counting_read(*args, **kwargs):
        result = real_read_selection(*args, **kwargs)
        reads.append(result)
        return result

    monkeypatch.setattr(reader, "read_selection", counting_read)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert len(reads) == 1
    real_getpid = os.getpid
    real_pid = real_getpid()
    monkeypatch.setattr(ppr.os, "getpid", lambda: real_pid + 1)
    assert admission.recheck(deadline_ms=30000) is False
    assert len(reads) == 1  # refused before attempting the lock or a reader call
    monkeypatch.setattr(ppr.os, "getpid", real_getpid)
    assert admission.recheck(deadline_ms=30000) is True
    assert len(reads) == 2


def test_serialized_recheck_span_real_request_state(tmp_path, monkeypatch):
    # Deterministic event-based witness: a recheck pauses on the return of
    # its real stable read while still holding its ownership span.  A
    # concurrent recheck is refused nonblocking with zero observations and
    # does not latch; the paused call decides inside its span on its stable
    # observation, before any invalidation; the next recheck observes the
    # new publication, latches, and every later recheck refuses with no
    # further reader call.
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["read_selection"] == 1
    real_read_selection = capture.PolicyCaptureReader.read_selection.__get__(reader, type(reader))
    paused = threading.Event()
    release = threading.Event()

    def pause_on_return(*args, **kwargs):
        counts["read_selection"] += 1
        result = real_read_selection(*args, **kwargs)  # the real stable read
        if not paused.is_set():
            paused.set()
            release.wait(timeout=30)
        return result

    monkeypatch.setattr(reader, "read_selection", pause_on_return)
    results = {}

    def first_recheck():
        results["first"] = admission.recheck(deadline_ms=30000)

    worker = threading.Thread(target=first_recheck)
    worker.start()
    try:
        assert paused.wait(timeout=30)  # the span is held, stable bytes read
        assert counts["read_selection"] == 2  # the first recheck's real read
        # The concurrent recheck: zero-observation contention, no latch.
        assert admission.recheck(deadline_ms=30000) is False
        assert counts["read_selection"] == 2  # the concurrent call read nothing
        # The trusted writer publishes a new selected publication.
        _replace_selection(root, 2, payload)
    finally:
        release.set()
        worker.join(timeout=30)
    # The paused stable read decided True inside its span, before the
    # invalidation: its observation matched at the time it was taken.
    assert results["first"] is True
    # The next recheck observes the mismatch, latches, and refuses.
    assert admission.recheck(deadline_ms=30000) is False
    assert counts["read_selection"] == 3
    # A permanent refusal never requalifies and calls no reader.
    assert admission.recheck(deadline_ms=30000) is False
    assert counts["read_selection"] == 3


# ----------------------------------------------------------------- reuse


def test_refused_request_leaves_no_admission_and_latches_per_admission(tmp_path):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    with pytest.raises(ppr.PolicyRequestError):
        ppr.request_current_view(reader, CREDENTIAL_OTHER, deadline_ms=30000)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert admission.recheck(deadline_ms=30000) is True
    _replace_selection(root, 2, payload)
    assert admission.recheck(deadline_ms=30000) is False
    assert admission.recheck(deadline_ms=30000) is False  # never requalifies
    _restore_selection(root, _render_selection(1, len(payload), _digest(payload)))
    fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert fresh.recheck(deadline_ms=30000) is True
    assert admission.recheck(deadline_ms=30000) is False


def test_stable_and_refusal_paths_compare(tmp_path):
    # Stable path: the admitted view keeps qualifying.
    payload = _payload()
    root_a = _make_root(tmp_path / "root-a", 1, payload)
    reader_a = _reader(root_a)
    admission_a = ppr.request_current_view(reader_a, CREDENTIAL, deadline_ms=30000)
    assert [admission_a.recheck(deadline_ms=30000) for _ in range(3)] == [True, True, True]
    # Refusal path: an observed denial latches; a permanent refusal cannot
    # qualify, while the stable path still qualifies independently.
    root_b = _make_root(tmp_path / "root-b", 1, payload)
    reader_b = _reader(root_b)
    admission_b = ppr.request_current_view(reader_b, CREDENTIAL, deadline_ms=30000)
    _replace_selection(root_b, 2, payload)
    assert [admission_b.recheck(deadline_ms=30000) for _ in range(3)] == [False] * 3
    assert admission_a.recheck(deadline_ms=30000) is True


@pytest.mark.parametrize("bad_deadline", [True, 0, 30001, "30000"])
def test_recheck_deadline_refused(tmp_path, bad_deadline):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    admission = ppr.request_current_view(_reader(root), CREDENTIAL, deadline_ms=30000)
    with pytest.raises(ppr.PolicyRequestError):
        admission.recheck(deadline_ms=bad_deadline)
    assert admission.recheck(deadline_ms=30000) is True


@pytest.mark.parametrize("boundary_deadline", [1, 30000])
def test_recheck_boundary_deadlines_accepted(tmp_path, monkeypatch, boundary_deadline):
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    # Request and rechecks share one controlled clock so the absolute
    # request end (1030.0) is independent of the host uptime.
    admission = ppr.request_current_view(_reader(root), CREDENTIAL, deadline_ms=30000)
    assert admission.recheck(deadline_ms=boundary_deadline) is True


# --------------------------------- permanent invalidation (actual reader)


def test_missing_selection_recheck_latches_permanently_real_reader(tmp_path, monkeypatch):
    # Actual reader: the selection is absent, the recheck enters its real
    # read and is refused; the exact restoration does not requalify the
    # same admission (zero further reads), while a separate newly admitted
    # request succeeds.  The shared reader itself is never latched by the
    # request latch.
    payload = _payload()
    root = _make_root(tmp_path / "missing", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    selected = root / _SELECTION
    original = selected.read_bytes()
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert admission.recheck(deadline_ms=30000) is True  # stable before loss
    assert counts["read_selection"] == 2
    selected.unlink()  # trusted-writer fixture role: the selection is absent
    assert admission.recheck(deadline_ms=30000) is False  # refused during loss
    assert counts["read_selection"] == 3  # it entered its real read once
    _restore_selection(root, original)  # exact restoration
    assert admission.recheck(deadline_ms=30000) is False  # permanently latched
    assert counts["read_selection"] == 3  # zero reads on old reuse
    fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 2 and counts["admit"] == 2
    assert fresh.recheck(deadline_ms=30000) is True  # a separate new request
    assert reader._latched is False  # the latch is per-admission, not per-owner


def test_malformed_selection_recheck_latches_permanently_real_reader(tmp_path, monkeypatch):
    # Actual reader: a malformed selector makes the recheck enter its real
    # read and be refused; the exact restoration does not requalify the
    # same admission (zero further reads), while a separate newly admitted
    # request succeeds.
    payload = _payload()
    root = _make_root(tmp_path / "malformed", 1, payload)
    reader = _reader(root)
    counts = _counts()
    _install_counting(monkeypatch, reader, counts)
    original = (root / _SELECTION).read_bytes()
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert admission.recheck(deadline_ms=30000) is True  # stable before loss
    assert counts["read_selection"] == 2
    _restore_selection(root, b"{invalid synthetic selector}")
    assert admission.recheck(deadline_ms=30000) is False  # refused while malformed
    assert counts["read_selection"] == 3  # it entered its real read once
    _restore_selection(root, original)  # exact restoration
    assert admission.recheck(deadline_ms=30000) is False  # permanently latched
    assert counts["read_selection"] == 3  # zero reads on old reuse
    fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert counts["capture"] == 2 and counts["admit"] == 2
    assert fresh.recheck(deadline_ms=30000) is True  # a separate new request
    assert reader._latched is False  # the latch is per-admission, not per-owner


def test_recheck_operation_cutoff_after_observation_controlled_clock(tmp_path, monkeypatch):
    # Controlled-clock witness for the caller's tightened recheck cutoff:
    # the fixed local observation end is taken before the real call from
    # the monotonic time and the capped call duration, clipped to the
    # fixed original request end, and is checked after the observation
    # and the exact comparison under the request lock.  The controlled
    # monotonic clock advances only after the actual delegated read.
    # Early, within the 50 ms operation end while the original 30 s end
    # is demonstrably live, the stable observation qualifies; late, past
    # the operation end while the original end still has ~29.9 s
    # remaining, the operation refuses and latches with zero subsequent
    # reads by the refused admission.
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    real_read_selection = capture.PolicyCaptureReader.read_selection.__get__(reader, type(reader))
    reads = []

    def stable_read(*args, **kwargs):
        result = real_read_selection(*args, **kwargs)  # the actual delegated read
        reads.append(result)
        return result

    monkeypatch.setattr(reader, "read_selection", stable_read)
    admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    assert admission._end == 1030.0  # the one absolute request end, never reset
    assert len(reads) == 1  # the entry's one bounded final selection reread

    # Early outcome: the clock advances only after the actual delegated
    # read, staying within the 50 ms operation end.
    def early_read(*args, **kwargs):
        result = real_read_selection(*args, **kwargs)  # the actual delegated read
        reads.append(result)
        clock["now"] += 0.010  # 10 ms after the read; within the 50 ms end
        return result

    monkeypatch.setattr(reader, "read_selection", early_read)
    assert admission.recheck(deadline_ms=50) is True
    assert 1000.0 < clock["now"] < 1000.050  # advanced, within the operation end
    assert clock["now"] < admission._end  # the original end is still live

    # Late outcome: the clock advances 65 ms after the successful
    # delegated read, past the 50 ms operation end, while the original
    # 30 s end remains demonstrably live.
    def late_read(*args, **kwargs):
        result = real_read_selection(*args, **kwargs)  # the actual delegated read
        reads.append(result)
        clock["now"] += 0.065  # 65 ms after the read; past the 50 ms end
        return result

    monkeypatch.setattr(reader, "read_selection", late_read)
    assert admission.recheck(deadline_ms=50) is False  # refused at the cutoff
    assert clock["now"] < admission._end  # the original end is still live
    assert len(reads) == 3  # the late delegated read itself was real
    # The late completion latched: zero subsequent reads by the refused
    # admission, even under fresh-looking per-check timeouts.
    assert admission.recheck(deadline_ms=30000) is False
    assert admission.recheck(deadline_ms=30000) is False
    assert len(reads) == 3
    # The shared reader itself is unaffected by the request latch.
    selection = real_read_selection(deadline_ms=30000)
    assert selection.generation == 1


# ------------------------------------------------- credential frame hygiene


def test_ordinary_credential_refusal_clears_entry_frame_credential(tmp_path):
    # Focused ordinary refusal witness: the retained request entry frame
    # of the fixed credential refusal no longer holds the raw synthetic
    # credential as a local, while the existing caller frame keeps its own
    # local.  No credential value is printed or compared by text.
    payload = _payload()
    root = _make_root(tmp_path / "root", 1, payload)
    reader = _reader(root)
    caller_frame = sys._getframe(0)
    credential = CREDENTIAL_OTHER  # this test frame's own local ownership
    with pytest.raises(ppr.PolicyRequestError) as excinfo:
        ppr.request_current_view(reader, credential, deadline_ms=30000)
    entry_frame = None
    trace = excinfo.value.__traceback__
    while trace is not None:
        if trace.tb_frame.f_code is ppr.request_current_view.__code__:
            entry_frame = trace.tb_frame
        trace = trace.tb_next
    assert entry_frame is not None  # the request entry frame is retained
    assert entry_frame.f_locals.get("credential") is None
    # The existing caller's frame ownership is distinct and unchanged.
    assert caller_frame.f_locals["credential"] is credential
