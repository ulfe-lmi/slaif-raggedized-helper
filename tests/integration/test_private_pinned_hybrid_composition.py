"""Owned private held-pin hybrid dispatch composition proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The real
source-backed hosted fixture (``make_sources`` from
``test_raw_hybrid_search_composition``), the real raw snapshot selector
and the actual ``PinOwner.acquire_selected_data`` build the pinned data;
the exact synthetic policy wire bytes are installed through the existing
payload installer, and a clearly attributed test-local atomic selector
fixture (re-derived from the 009-z current-view lane fixture in
``tests/unit/test_private_policy_request.py``) publishes the selected
record for the actual capture/decoder/request methods - it provides no
writer qualification.  The supported request lifetime begins after the
expensive fixture setup.  Counting wrappers delegate the real catalog,
directory, engine, owner-load and reader functions at the intended
boundaries; counts run from the private dispatch after fixture
acquisition.  The actual
late-deadline cut is crossed during the operation, after a genuinely
delegated policy read, under a bounded real wait on the real monotonic
clock, never a caller-selectable clock.
"""
import hashlib
import json
import os
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from slaif_raggedized_helper import private_policy_capture as capture
from slaif_raggedized_helper import private_policy_payload as payload_install
from slaif_raggedized_helper import private_policy_request as ppr
from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import raw_hybrid_search as hybrid
from slaif_raggedized_helper import raw_snapshot_catalog as catalog
from slaif_raggedized_helper import raw_snapshot_directory as directory
from slaif_raggedized_helper import raw_snapshot_selection as selection
from slaif_raggedized_helper.raw_snapshot_pin import PinData, PinOwner
from test_raw_hybrid_search_composition import make_sources
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401

# Attributed test-local wire emitter: an independent re-derivation of the
# typed component grammar (009-z current-view lane fixture,
# tests/unit/test_private_policy_request.py).
_MAGIC = b"slaif-supplied-policy-view-v1\n"
_KIND = "slaif-current-policy-selection-v1"
_SELECTION = "current-policy.json"
CREDENTIAL = b"synthetic-credential-" + b"a" * 22  # exactly 43
PRINCIPAL_ID = "alpha-1"
VERIFIER = hashlib.sha256(CREDENTIAL).digest()
OPERATIONS = ("search", "sources:read")
CORPORA = ("one", "two")
VERSIONS = ("v1",)
LABELS = ("secret",)
PRINCIPAL = (PRINCIPAL_ID, VERIFIER, OPERATIONS, CORPORA, VERSIONS, LABELS)
TEXT = "DistinctiveZephyr"
VECTOR = np.zeros(1024, dtype="<f4")
VECTOR[:3] = [0.6, 0, 0.8]
GRANTS = p.Grants(schema_version=1, corpora=CORPORA, versions=VERSIONS,
                  labels=LABELS)


def _u32(value):
    return value.to_bytes(4, "big")


def _s(text):
    raw = text.encode("utf-8")
    return _u32(len(raw)) + raw


def _encode_principal(principal_id, verifier, operations, corpora, versions, labels):
    parts = [_s(principal_id), _u32(32) + verifier, _u32(len(operations))]
    for operation in operations:
        parts.append(_s(operation))
    parts.append(_u32(1))
    for values in (corpora, versions, labels):
        parts.append(_u32(len(values)))
        for value in values:
            parts.append(_s(value))
    return b"".join(parts)


def _encode_policy(principals, documents):
    parts = [_MAGIC, _u32(1), _u32(len(principals))]
    for principal in principals:
        parts.append(_encode_principal(*principal))
    parts.append(_u32(len(documents)))
    for document_id, pairs in documents:
        parts.append(_s(document_id))
        parts.append(_u32(len(pairs)))
        for revision_id, scope_digest in pairs:
            parts.append(_s(revision_id))
            parts.append(_s(scope_digest))
    return b"".join(parts)


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


def _publish_selection(root, generation, payload):
    # Trusted-writer fixture role: one atomic selected-record publication.
    root = Path(root)
    repl = root.parent / ("swap-" + str(generation) + ".json")
    fd = os.open(str(repl), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(
            fd,
            _render_selection(
                generation, len(payload), hashlib.sha256(payload).hexdigest()
            ),
        )
    finally:
        os.close(fd)
    os.chmod(str(repl), 0o400)
    os.replace(str(repl), str(root / _SELECTION))


def _documents_from_membership(owner, withhold_two=False):
    # Policy documents derived from the real captured membership: per
    # entry, the admitted scope's document ID owns the exact
    # (revision_id, source_scope_sha256) pair.  Document IDs and pairs
    # are strictly ascending, as the genuine policy admission requires.
    docs = {}
    corpus = {}
    for entry in owner.value.data.membership.entries:
        scope = p.admit_record("Scope", entry.scope_bytes)
        docs.setdefault(scope.document_id, []).append(
            (entry.revision_id, entry.source_scope_sha256)
        )
        corpus[scope.document_id] = scope.corpus
    documents = []
    for doc_id in sorted(docs):
        pairs = tuple(sorted(docs[doc_id]))
        if withhold_two and corpus[doc_id] == "two":
            pairs = ()
        documents.append((doc_id, pairs))
    return tuple(documents)


def _install_policy(tmp_base, name, documents):
    payload = _encode_policy([PRINCIPAL], documents)
    policy_root = Path(tmp_base) / name
    policy_root.mkdir(mode=0o700)
    os.chmod(str(policy_root), 0o700)
    receipt = payload_install.install_policy_payload(
        payload, directory=str(policy_root), deadline_ms=30000
    )
    assert receipt.outcome is payload_install.PayloadInstallOutcome.INSTALLED
    _publish_selection(policy_root, 1, payload)
    return policy_root, payload


def _close_owned(originals, derived, owner):
    for owned in (owner, derived, originals):
        owned.close()


def _scenario(tmp_path, *, withhold_two=False):
    """One real scenario: hosted fixture, real selector, real pin, genuine
    policy admission; the request lifetime begins after fixture setup."""
    originals = derived = owner = None
    try:
        originals, derived, root, ident = make_sources(tmp_path)
        core = json.loads(
            (root / "snapshots" / ident[7:] / ".core.json").read_bytes()
        )
        embedding = core["embedding"]
        selection.compare_and_select_data(originals, derived, str(root), ident, None)
        owner = PinOwner()
        owner.acquire_selected_data(originals, derived, str(root), deadline_ms=30000)
        documents = _documents_from_membership(owner, withhold_two=withhold_two)
        policy_root, payload = _install_policy(tmp_path, "policy", documents)
        reader = capture.PolicyCaptureReader(str(policy_root))
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        return (
            originals, derived, root, ident, embedding, owner, policy_root,
            reader, admission,
        )
    except BaseException:
        for owned in (owner, derived, originals):
            if owned is not None:
                try:
                    owned.close()
                except BaseException:
                    pass
        raise


def _counts():
    return {"catalog": 0, "directory": 0, "dense": 0, "lexical": 0, "fuse": 0,
            "read": 0}


def _engine_counts(counts):
    return (counts["catalog"], counts["directory"], counts["dense"],
            counts["lexical"], counts["fuse"])


def _install_witness(monkeypatch, reader, counts, *, after_dense=None,
                     interrupt_at_read=None, interrupt_marker=None):
    # Counting wrappers that delegate the real functions at the intended
    # boundaries; counts run from the private dispatch after fixture
    # acquisition.  ``interrupt_at_read`` is the exact one-based read index
    # to match separately; ``interrupt_marker`` is the exact non-Exception
    # object raised there by identity.  No production hook is added.
    real_catalog = catalog.load_catalog
    real_directory = directory.load_directory
    real_dense = hybrid.dense.search
    real_lexical = hybrid.lexical.search
    real_fuse = hybrid.fusion.fuse
    real_read = capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader)
    )

    def counting_catalog(*args, **kwargs):
        counts["catalog"] += 1
        return real_catalog(*args, **kwargs)

    def counting_directory(*args, **kwargs):
        counts["directory"] += 1
        return real_directory(*args, **kwargs)

    def counting_dense(*args, **kwargs):
        counts["dense"] += 1
        result = real_dense(*args, **kwargs)
        if after_dense is not None:
            after_dense()
        return result

    def counting_lexical(*args, **kwargs):
        counts["lexical"] += 1
        return real_lexical(*args, **kwargs)

    def counting_fuse(*args, **kwargs):
        counts["fuse"] += 1
        return real_fuse(*args, **kwargs)

    def counting_read(*args, **kwargs):
        counts["read"] += 1
        if (interrupt_at_read is not None
                and counts["read"] == interrupt_at_read):
            raise interrupt_marker
        return real_read(*args, **kwargs)

    monkeypatch.setattr(catalog, "load_catalog", counting_catalog)
    monkeypatch.setattr(directory, "load_directory", counting_directory)
    monkeypatch.setattr(hybrid.dense, "search", counting_dense)
    monkeypatch.setattr(hybrid.lexical, "search", counting_lexical)
    monkeypatch.setattr(hybrid.fusion, "fuse", counting_fuse)
    monkeypatch.setattr(reader, "read_selection", counting_read)


def _install_reader_counts(monkeypatch, reader, counts):
    real_read = capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader)
    )

    def counting_read(*args, **kwargs):
        counts["read"] += 1
        return real_read(*args, **kwargs)

    monkeypatch.setattr(reader, "read_selection", counting_read)


def _dispatch(admission, owner, embedding, *, deadline_ms=30000):
    return hybrid.search_pinned(
        admission,
        owner,
        TEXT,
        VECTOR.tobytes(),
        query_space_id=embedding["space_id"],
        query_definition_fingerprint=embedding["definition_fingerprint"],
        query_policy_id=embedding["query_policy_fingerprint"],
        query_execution_fingerprint=embedding["query_execution_fingerprint"],
        dense_k=3,
        lexical_k=3,
        partition_cap=3,
        k=3,
        deadline_ms=deadline_ms,
    )


def test_pinned_positive_journey_matches_legacy(tmp_path, monkeypatch):
    (originals, derived, root, ident, embedding, owner, policy_root, reader,
     admission) = _scenario(tmp_path)
    try:
        # A still-live pin whose prior acquisition end is already expired:
        # the new bounded request must succeed and that old value returns.
        stale_end = time.monotonic() - 60.0
        owner.op.end = stale_end
        counts = _counts()
        _install_witness(monkeypatch, reader, counts)
        result = _dispatch(admission, owner, embedding)
        assert _engine_counts(counts) == (8, 17, 1, 1, 1)
        assert counts["read"] == 4
        assert owner.op.end == stale_end
        assert not owner.guard.locked()
        assert (result.dense.eligible, result.dense.returned) == (3, 3)
        assert (result.lexical.eligible, result.lexical.matching,
                result.lexical.returned) == (3, 1, 1)
        assert (result.fusion.dense_input_rows, result.fusion.lexical_input_rows,
                result.fusion.unique_candidates, result.fusion.overlap_candidates) \
            == (3, 1, 3, 1)
        assert [h.score for h in result.dense.hits] == pytest.approx(
            [0.8, 0.6, 0.0])
        assert result.fusion.hits[0].score == pytest.approx(2 / 61)
        assert result.snapshot_id == ident
        assert result.query_origin == "SUPPLIED_UNVERIFIED"
        assert result.qualification == "NOT_QUALIFIED"
        # Independent authority binding: the admitted grants with no
        # additional caller restriction.
        expected_authority = hashlib.sha256(
            json.dumps([GRANTS.model_dump(mode="json"), None], sort_keys=True,
                       ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert result.authority_sha256 == expected_authority
        # The one real hybrid body is unchanged: the same supplied
        # arguments through the public legacy entry yield the same result.
        legacy = hybrid.search(
            originals, derived, str(root), ident, TEXT, VECTOR.tobytes(),
            query_space_id=embedding["space_id"],
            query_definition_fingerprint=embedding["definition_fingerprint"],
            query_policy_id=embedding["query_policy_fingerprint"],
            query_execution_fingerprint=embedding["query_execution_fingerprint"],
            grants=GRANTS, dense_k=3, lexical_k=3, partition_cap=3, k=3)
        assert result == legacy
    finally:
        _close_owned(originals, derived, owner)


def test_post_dense_change_latches_before_lexical(tmp_path, monkeypatch):
    (originals, derived, root, ident, embedding, owner, policy_root, reader,
     admission) = _scenario(tmp_path)
    try:
        counts = _counts()

        def change_generation():
            # The synthetic selected generation changes while the wire
            # payload stays identical.
            documents = _documents_from_membership(owner)
            _publish_selection(policy_root, 2, _encode_policy([PRINCIPAL],
                                                              documents))

        original_end = owner.op.end
        _install_witness(monkeypatch, reader, counts, after_dense=change_generation)
        with pytest.raises(hybrid.HybridSearchError):
            _dispatch(admission, owner, embedding)
        assert _engine_counts(counts) == (3, 6, 1, 0, 0)
        assert counts["read"] == 3
        assert admission._invalid is True
        # The latched recheck refuses with zero further reader calls.
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 3
        # The shared reader is never latched: a fresh admission succeeds
        # only through the actual reader/matcher on the new generation.
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert fresh.policy_id == admission.policy_id
        assert fresh.selection.generation == 2
        assert owner.op.end == original_end
        assert not owner.guard.locked()
    finally:
        _close_owned(originals, derived, owner)


def test_revocation_before_dispatch_refuses_at_o1(tmp_path, monkeypatch):
    (originals, derived, root, ident, embedding, owner, policy_root, reader,
     admission) = _scenario(tmp_path)
    try:
        counts = _counts()
        _install_witness(monkeypatch, reader, counts)
        # Real principal revocation after admission and before dispatch:
        # the search operation is withdrawn from the new selected policy.
        revoked = (PRINCIPAL_ID, VERIFIER, ("sources:read",), CORPORA, VERSIONS,
                   LABELS)
        documents = _documents_from_membership(owner)
        payload = _encode_policy([revoked], documents)
        receipt = payload_install.install_policy_payload(
            payload, directory=str(policy_root), deadline_ms=30000)
        assert receipt.outcome is payload_install.PayloadInstallOutcome.INSTALLED
        _publish_selection(policy_root, 2, payload)
        original_end = owner.op.end
        with pytest.raises(hybrid.HybridSearchError):
            _dispatch(admission, owner, embedding)
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 1
        assert admission._invalid is True
        # Fresh admission of the revoked synthetic credential also refuses:
        # the bounded match of the required operations runs before any
        # further selected-record read, so no new reader call is made.
        with pytest.raises(ppr.PolicyRequestError):
            ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert counts["read"] == 1
        assert owner.op.end == original_end
        assert not owner.guard.locked()
    finally:
        _close_owned(originals, derived, owner)


def test_final_owner_validation_change_refuses_usable_return(tmp_path, monkeypatch):
    (originals, derived, root, ident, embedding, owner, policy_root, reader,
     admission) = _scenario(tmp_path)
    try:
        counts = _counts()
        owner_loads = []
        real_load = owner._load

        def load_then_change(snapshot_id):
            owner_loads.append(snapshot_id)
            result = real_load(snapshot_id)
            # The selected record changes during the real final owner
            # validation; the wire payload stays identical.
            documents = _documents_from_membership(owner)
            _publish_selection(policy_root, 2, _encode_policy([PRINCIPAL],
                                                              documents))
            return result

        monkeypatch.setattr(owner, "_load", load_then_change)
        original_end = owner.op.end
        _install_witness(monkeypatch, reader, counts)
        with pytest.raises(hybrid.HybridSearchError):
            _dispatch(admission, owner, embedding)
        # The complete real body ran, including the one distinct final
        # full owner validation; the last actual read after the load and
        # association refuses the usable return.
        assert owner_loads == [ident]
        assert _engine_counts(counts) == (8, 17, 1, 1, 1)
        assert counts["read"] == 4
        assert admission._invalid is True
        assert owner.op.end == original_end
        assert not owner.guard.locked()
    finally:
        _close_owned(originals, derived, owner)


def test_held_pin_refusals_before_engine_work(tmp_path, monkeypatch):
    (originals, derived, root, ident, embedding, owner, policy_root, reader,
     admission) = _scenario(tmp_path)
    try:
        # The closed-ownership fixture is built before the witness so its
        # genuine acquisition I/O never counts as dispatch.
        other = PinOwner()
        other.acquire_selected_data(originals, derived, str(root),
                                    deadline_ms=30000)
        other.close()
        assert other.state == "CLOSED"
        # The captured-membership scope scenario is a second exact owned
        # fixture, built before the witness so fixture acquisition never
        # counts as dispatch.
        second = tmp_path / "second"
        second.mkdir(mode=0o700)
        (originals2, derived2, root2, ident2, embedding2, owner2,
         policy_root2, reader2, admission2) = _scenario(second,
                                                        withhold_two=True)
        counts = _counts()
        _install_witness(monkeypatch, reader, counts)
        _install_reader_counts(monkeypatch, reader2, counts)
        original_end = owner.op.end
        held = owner.value

        # (a) malformed held capture: core digest drift.
        mutated = replace(held.data, core_bytes=held.data.core_bytes + b"drift")
        owner.value = PinData(held.pointer, mutated)
        try:
            with pytest.raises(hybrid.HybridSearchError):
                _dispatch(admission, owner, embedding)
        finally:
            owner.value = held
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 0

        # (b) busy custody.
        assert owner.guard.acquire(blocking=False)
        try:
            with pytest.raises(hybrid.HybridSearchError):
                _dispatch(admission, owner, embedding)
        finally:
            owner.guard.release()
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 0

        # (c) foreign creator PID.
        owner.pid = -1
        try:
            with pytest.raises(hybrid.HybridSearchError):
                _dispatch(admission, owner, embedding)
        finally:
            owner.pid = os.getpid()
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 0

        # (d) closed ownership.
        with pytest.raises(hybrid.HybridSearchError):
            _dispatch(admission, other, embedding)
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 0

        # (e) genuine isolated policy over the captured membership: the
        # withheld corpus-two pairs make that partition unavailable
        # inside the admitted readable scope; the refusal runs before
        # any catalog or source I/O.
        with pytest.raises(hybrid.HybridSearchError):
            _dispatch(admission2, owner2, embedding2)
        assert _engine_counts(counts) == (0, 0, 0, 0, 0)
        assert counts["read"] == 1
        assert admission2._invalid is False

        # The owner and reader state is stable across every refusal.
        assert owner.value is held
        assert owner.state == "ACTIVE"
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        assert owner2.state == "ACTIVE"
        assert not owner2.guard.locked()
        _close_owned(originals2, derived2, owner2)
    finally:
        _close_owned(originals, derived, owner)


def test_interruption_identity_and_late_deadline(tmp_path, monkeypatch):
    (originals, derived, root, ident, embedding, owner, policy_root, reader,
     admission) = _scenario(tmp_path)
    try:
        counts = _counts()

        class _Interrupted(BaseException):
            pass

        marker = _Interrupted()
        original_end = owner.op.end
        _install_witness(monkeypatch, reader, counts, interrupt_at_read=3,
                         interrupt_marker=marker)
        # (1) A controlled non-Exception interruption at the third real
        # read (the O3 boundary, after the genuine dense output).
        with pytest.raises(_Interrupted) as excinfo:
            _dispatch(admission, owner, embedding)
        assert excinfo.value is marker
        assert _engine_counts(counts) == (3, 6, 1, 0, 0)
        assert counts["read"] == 3
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        # No later protected dispatch follows: the recorded dispatch and
        # reader state stay at the interruption boundary.
        assert _engine_counts(counts) == (3, 6, 1, 0, 0)
        assert counts["read"] == 3
        # (2) An actual late-deadline cut under the real monotonic clock:
        # a legitimately admitted request with a short real lifetime.  The
        # private operation's actual deadline, clipped to that lifetime, is
        # crossed during the operation, after the one genuinely delegated
        # policy read, by a bounded real wait; no caller-selectable clock
        # is used.
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=1000)
        real_read = capture.PolicyCaptureReader.read_selection.__get__(
            reader, type(reader)
        )

        def delayed_read(*args, **kwargs):
            counts["read"] += 1
            result = real_read(*args, **kwargs)
            time.sleep(1.5)
            return result

        monkeypatch.setattr(reader, "read_selection", delayed_read)
        before = dict(counts)
        with pytest.raises(hybrid.HybridSearchError):
            _dispatch(fresh, owner, embedding)
        # The operation started and ran the one genuine delegated policy
        # read; the late completion refused at that cut with no further
        # protected stage, latching the admission, and custody is restored.
        for key in ("catalog", "directory", "dense", "lexical", "fuse"):
            assert counts[key] == before[key]
        assert counts["read"] == before["read"] + 1
        assert fresh._invalid is True
        assert owner.op.end == original_end
        assert not owner.guard.locked()
    finally:
        _close_owned(originals, derived, owner)
