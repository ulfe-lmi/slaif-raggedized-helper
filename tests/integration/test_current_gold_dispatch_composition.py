"""Owned private held-pin Gold bundle dispatch composition proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  The real
hosted source fixture (``make_owned_support`` from
``test_source_bound_support_ci_composition`` over the real
``make_sources``), the canonical five-case dataset and actual bundle IDs
(``dataset_and_bundles`` from
``test_source_cohort_runner_composition``), the actual raw snapshot
selector and the real ``PinOwner.acquire_selected_data`` build the
pinned data; the exact synthetic policy wire bytes are installed through
the existing payload installer, and a clearly attributed test-local
atomic selector fixture (re-derived from the 009-z current-view lane
fixture in ``tests/unit/test_private_policy_request.py``) publishes the
selected record for the actual capture/decoder/request methods - it
provides no writer qualification, and the actual selected changes use
the same-wire generation change through that attributed fixture.  Each
fresh current admission is created only after the expensive fixture
setup that precedes its dispatch.  Counting wrappers delegate the real
bundle, derived, original-store verified read, owner-load and reader
functions at the intended boundaries; counts run from the private
dispatch after fixture acquisition, and the legacy comparison is
counted separately.  No local native execution: only the configured
hosted CI executes the real fixture.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import ingestion_store  # noqa: E402
from slaif_raggedized_helper import private_policy_capture as capture  # noqa: E402
from slaif_raggedized_helper import private_policy_payload as payload_install  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import provenance_records as p  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_selection as selection  # noqa: E402
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility  # noqa: E402
from slaif_raggedized_helper import text_evaluation_gold_binding as gold  # noqa: E402
from slaif_raggedized_helper.raw_snapshot_pin import PinOwner  # noqa: E402
from slaif_raggedized_helper.source_admission import parse_manifest  # noqa: E402
import test_native_tokenizers  # noqa: E402
import test_source_bound_support_ci_composition as support_fixture  # noqa: E402
import test_source_cohort_runner_composition as cohort_fixture  # noqa: E402
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: E402,F401
from test_retrieval_representation_composition import make_bundle  # noqa: E402

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


def _close_owned(ctx, owner):
    for owned in (owner, ctx.derived, ctx.originals):
        owned.close()


def _scenario(tmp_path, *, withhold_two=False):
    """One real scenario: hosted fixture, real selector, real pin, genuine
    policy wire and reader; no admission yet, so each fresh current
    admission begins its lifetime only after the expensive fixture setup
    that precedes its dispatch."""
    ctx = owner = None
    try:
        ctx = support_fixture.make_owned_support(tmp_path)
        dataset, bundle_ids = cohort_fixture.dataset_and_bundles(ctx)
        selection.compare_and_select_data(
            ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id, None
        )
        owner = PinOwner()
        owner.acquire_selected_data(ctx.originals, ctx.derived, ctx.root,
                                    deadline_ms=30000)
        documents = _documents_from_membership(owner, withhold_two=withhold_two)
        policy_root, payload = _install_policy(tmp_path, "policy", documents)
        reader = capture.PolicyCaptureReader(str(policy_root))
        return ctx, dataset, bundle_ids, owner, policy_root, reader
    except BaseException:
        if owner is not None:
            try:
                owner.close()
            except BaseException:
                pass
        if ctx is not None:
            for owned in (ctx.derived, ctx.originals):
                try:
                    owned.close()
                except BaseException:
                    pass
        raise


def _counts():
    return {"bundle": 0, "derived": 0, "original": 0, "read": 0, "pin_load": 0}


def _assert_zero(counts):
    assert counts == {"bundle": 0, "derived": 0, "original": 0, "read": 0,
                      "pin_load": 0}


def _install_witness(monkeypatch, ctx, owner, reader, counts, *,
                     change_at_load=None, change_generation=None):
    # Counting wrappers that delegate the real functions at the intended
    # boundaries; counts run from the private dispatch after fixture
    # acquisition.  ``change_at_load`` is the exact one-based bundle load
    # index; ``change_generation`` is the attributed same-wire generation
    # change callback, kept separate from that index.  No production
    # hook is added.
    real_bundle = ingestion_store.load
    real_derived = ctx.derived.load
    # The actual OriginalStore verified read: the high-level
    # structured_text.extract begins before that real store read, so
    # the counted boundary is the bound store method itself, delegated
    # with its exact original args and kwargs.
    real_original = ctx.originals.read_verified
    real_pin_load = owner._load
    real_read = capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader)
    )

    def counting_bundle(*args, **kwargs):
        counts["bundle"] += 1
        result = real_bundle(*args, **kwargs)
        if (change_at_load is not None and counts["bundle"] == change_at_load
                and change_generation is not None):
            change_generation()
        return result

    def counting_derived(container_id):
        counts["derived"] += 1
        return real_derived(container_id)

    def counting_original(*args, **kwargs):
        counts["original"] += 1
        return real_original(*args, **kwargs)

    def counting_pin_load(snapshot_id):
        counts["pin_load"] += 1
        return real_pin_load(snapshot_id)

    def counting_read(*args, **kwargs):
        counts["read"] += 1
        return real_read(*args, **kwargs)

    monkeypatch.setattr(ingestion_store, "load", counting_bundle)
    monkeypatch.setattr(ctx.derived, "load", counting_derived)
    monkeypatch.setattr(ctx.originals, "read_verified", counting_original)
    monkeypatch.setattr(owner, "_load", counting_pin_load)
    monkeypatch.setattr(reader, "read_selection", counting_read)


def _dispatch(admission, owner, dataset, case_id, bundle_ids, *, deadline_ms=30000):
    return gold.bind_pinned(admission, owner, dataset, case_id, bundle_ids,
                            deadline_ms=deadline_ms)


def test_pinned_positive_h2_matches_legacy(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = _scenario(tmp_path)
    try:
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        # A still-live pin whose prior acquisition end is already expired:
        # the new bounded dispatch must succeed and that old value returns.
        stale_end = time.monotonic() - 60.0
        owner.op.end = stale_end
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        result = _dispatch(admission, owner, dataset, "h2", bundle_ids)
        # Exactly six Gold bundle/derived/original dispatches (3 per
        # pass) and six genuinely delegated selected rereads, with no
        # new pin/source reload in the measured span.
        assert (counts["bundle"], counts["derived"], counts["original"]) == (6, 6, 6)
        assert counts["read"] == 6
        assert counts["pin_load"] == 0
        assert owner.op.end == stale_end
        assert not owner.guard.locked()
        assert result.source_binding_status == "ORIGINALS_REVALIDATED_AT_BIND_TIME"
        assert result.case_count == 5
        assert len(result.observations) == 3
        # The one real Gold body is unchanged: the same admitted inputs
        # through the public legacy entry yield the same result, with the
        # legacy pass counters kept separate.
        monkeypatch.undo()
        legacy_counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, legacy_counts)
        legacy = gold.bind(ctx.originals, ctx.derived, dataset, bundle_ids,
                           deadline_ms=30000)
        assert (legacy_counts["bundle"], legacy_counts["derived"],
                legacy_counts["original"]) == (6, 6, 6)
        assert legacy_counts["read"] == 0
        assert legacy_counts["pin_load"] == 0
        assert result == legacy
        assert result.binding_id == legacy.binding_id
    finally:
        _close_owned(ctx, owner)


def test_genuine_scope_narrowing_and_unavailable_refuse(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = _scenario(tmp_path)
    try:
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        original_end = owner.op.end
        # (a) The genuine h1 case excludes b under the actual effective
        # intersection on the same full dataset and bundle set: zero Gold
        # starts.
        counts1 = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts1)
        with pytest.raises(gold.GoldBindingError):
            _dispatch(admission, owner, dataset, "h1", bundle_ids)
        _assert_zero(counts1)
        # The scope refusal does not latch the admission: one genuine
        # delegated reread still agrees on the unchanged selection.
        assert admission._invalid is False
        assert admission.recheck(deadline_ms=1000) is True
        assert counts1["read"] == 1
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        # (b) The independent second fixture, instrumented separately:
        # the withheld corpus-two document pairs make b genuinely
        # unavailable under the selected semantic policy, refusing the h2
        # case before Gold source work.
        monkeypatch.undo()
        second = tmp_path / "second"
        second.mkdir(mode=0o700)
        (ctx2, dataset2, bundle_ids2, owner2, policy_root2, reader2) = (
            _scenario(second, withhold_two=True))
        try:
            admission2 = ppr.request_current_view(
                reader2, CREDENTIAL, deadline_ms=30000)
            original_end2 = owner2.op.end
            counts2 = _counts()
            _install_witness(monkeypatch, ctx2, owner2, reader2, counts2)
            with pytest.raises(gold.GoldBindingError):
                _dispatch(admission2, owner2, dataset2, "h2", bundle_ids2)
            _assert_zero(counts2)
            assert admission2._invalid is False
            assert owner2.state == "ACTIVE"
            assert owner2.op.end == original_end2
            assert not owner2.guard.locked()
            # (c) Regression for the declared-only gate: the whole
            # membership is authenticated by the genuine unavailable
            # partitions, but readability and availability are checked
            # only for declared bundles, preserving the undeclared
            # member's unaffected scope.  b is the corpus-two bundle:
            # its partition is genuinely unavailable under this
            # selected policy while the same real pin still holds it,
            # so the declared a/c dispatch on a distinct canonical
            # dataset whose atoms all live in a and c must not be
            # refused by the extra pin member.
            def _member_corpus(ident):
                entry = next(e for e in owner2.value.data.membership.entries
                             if e.bundle_container_id == ident)
                return p.admit_record("Scope", entry.scope_bytes).corpus

            b_id = next(ident for ident in bundle_ids2
                        if _member_corpus(ident) == "two")
            member_b = next(e for e in owner2.value.data.membership.entries
                            if e.bundle_container_id == b_id)
            unavailable2 = set(policy_eligibility.unavailable_partitions(
                pin_eligibility._isolated_policy_snapshot(admission2),
                owner2.value.data.membership))
            assert member_b.partition_id in unavailable2
            # An explicitly distinct canonical dataset: the same
            # canonical JSON with every b span removed, pruning the
            # resulting empty requirement, so only a/c atoms remain.
            base2 = json.loads(dataset2)
            dropped = {(member_b.revision_id, member_b.extraction_id)}
            for case in base2["cases"]:
                requirements = []
                for requirement in case["requirements"]:
                    alternatives = []
                    for alternative in requirement["alternatives"]:
                        spans = [span for span in alternative
                                 if (span["revision_id"],
                                     span["extraction_id"]) not in dropped]
                        if spans:
                            alternatives.append(spans)
                    if alternatives:
                        requirements.append(requirement)
                case["requirements"] = requirements
            dataset2_ac = cohort_fixture.canonical(base2)
            declared_ac = tuple(ident for ident in bundle_ids2 if ident != b_id)
            monkeypatch.undo()
            counts3 = _counts()
            _install_witness(monkeypatch, ctx2, owner2, reader2, counts3)
            result2 = _dispatch(admission2, owner2, dataset2_ac, "h1",
                                declared_ac)
            assert (result2.source_binding_status
                    == "ORIGINALS_REVALIDATED_AT_BIND_TIME")
            assert len(result2.observations) == 2
            assert (counts3["bundle"], counts3["derived"],
                    counts3["original"]) == (4, 4, 4)
            assert counts3["read"] == 4
            assert counts3["pin_load"] == 0
            assert admission2._invalid is False
            assert owner2.op.end == original_end2
            assert not owner2.guard.locked()
        finally:
            _close_owned(ctx2, owner2)
    finally:
        _close_owned(ctx, owner)


def test_unknown_declared_id_refuses_without_derived_lookup(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = _scenario(tmp_path)
    try:
        # A real fourth source and bundle published into the owned
        # derived store: its container ID exists in the synthetic store
        # but is absent from the actual pin.  Fixture work, before the
        # witness, so it never counts as dispatch.
        paths, runtime, make = test_native_tokenizers.make_native(tmp_path)
        defs = (make(paths[0], "bge_body"), make(paths[0], "bge_representation"),
                make(paths[1], "reranker_pair"))
        source_root = tmp_path / "source"
        raw = ("# Heading\n\nalpha beta gamma. " * 20).encode()
        raw_d = raw + b"\n\nFourthSource"
        (source_root / "d").write_bytes(raw_d)
        base = dict(logical_id="d", relative_path="d", display_uri="urn:owned",
                    corpus="one", version="v1", title="uniquetitle",
                    access_labels=[], processing_approved=True,
                    redistribution_rights="allowed", media_type="text/markdown",
                    size=len(raw_d), sha256=hashlib.sha256(raw_d).hexdigest())
        sources = parse_manifest(
            json.dumps(dict(schema_version=1, sources=[base])).encode())
        revision = ctx.originals.admit(source_root, sources.sources[0])
        metadata, members, _, _ = make_bundle(ctx.originals, revision, defs, runtime)
        extra = ingestion_store.publish(ctx.originals, ctx.derived, metadata, members)
        # Prove the outside-pin ID really exists in the owned synthetic
        # store before starting counters.
        proven = ingestion_store.load(ctx.originals, ctx.derived, extra)
        assert proven.revision.source.logical_id == "d"
        declared = tuple(sorted(bundle_ids + (extra,)))
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        original_end = owner.op.end
        with pytest.raises(gold.GoldBindingError):
            _dispatch(admission, owner, dataset, "h2", declared)
        # The complete batch refuses with zero new bundle/derived/original
        # lookup, even though the ID exists in the owned synthetic store.
        _assert_zero(counts)
        assert admission._invalid is False
        assert owner.op.end == original_end
        assert not owner.guard.locked()
    finally:
        _close_owned(ctx, owner)


def test_change_after_three_first_pass_loads_denies_pass_two(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = _scenario(tmp_path)
    try:
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)

        def change_generation():
            # The synthetic selected generation changes while the wire
            # payload stays identical.
            documents = _documents_from_membership(owner)
            _publish_selection(policy_root, 2, _encode_policy([PRINCIPAL],
                                                              documents))

        original_end = owner.op.end
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts,
                         change_at_load=3, change_generation=change_generation)
        with pytest.raises(gold.GoldBindingError):
            _dispatch(admission, owner, dataset, "h2", bundle_ids)
        # Three allowed first-pass loads; the fourth selected read denies
        # the first load of pass two, with zero new dispatch after denial
        # and no usable result.
        assert (counts["bundle"], counts["derived"], counts["original"]) == (3, 3, 3)
        assert counts["read"] == 4
        assert counts["pin_load"] == 0
        assert admission._invalid is True
        # The latched recheck refuses with zero further reader calls.
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 4
        # The shared reader is never latched: a fresh admission succeeds
        # only through the actual reader on the new generation.
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert fresh.policy_id == admission.policy_id
        assert fresh.selection.generation == 2
        assert owner.op.end == original_end
        assert not owner.guard.locked()
    finally:
        _close_owned(ctx, owner)


def test_change_after_first_load_and_custody_refusals(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader) = _scenario(tmp_path)
    try:
        # The closed-ownership fixture is built before the admission and
        # the witness so its genuine acquisition I/O never counts as
        # dispatch and the request lifetime begins after it.
        other = PinOwner()
        other.acquire_selected_data(ctx.originals, ctx.derived, ctx.root,
                                    deadline_ms=30000)
        other.close()
        assert other.state == "CLOSED"
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)

        def change_generation():
            # The synthetic selected generation changes while the wire
            # payload stays identical.
            documents = _documents_from_membership(owner)
            _publish_selection(policy_root, 2, _encode_policy([PRINCIPAL],
                                                              documents))

        original_end = owner.op.end
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts,
                         change_at_load=1, change_generation=change_generation)
        with pytest.raises(gold.GoldBindingError):
            _dispatch(admission, owner, dataset, "h2", bundle_ids)
        # Exactly one allowed load, then zero additional Gold work.
        assert (counts["bundle"], counts["derived"], counts["original"]) == (1, 1, 1)
        assert counts["read"] == 2
        assert counts["pin_load"] == 0
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 2
        # (a) Pre-first refusal: a fresh request captures generation 2;
        # generation 3 is published before dispatch, so the one genuine
        # delegated read before the first load denies it.
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert fresh.selection.generation == 2
        _publish_selection(policy_root, 3, _encode_policy(
            [PRINCIPAL], _documents_from_membership(owner)))
        before = dict(counts)
        with pytest.raises(gold.GoldBindingError):
            _dispatch(fresh, owner, dataset, "h2", bundle_ids)
        assert (counts["bundle"], counts["derived"], counts["original"]) == (1, 1, 1)
        assert counts["read"] == before["read"] + 1
        assert fresh._invalid is True
        # A fresh non-latched admission proves the custody boundaries
        # below: each refusal happens at its named boundary without any
        # protected work, read or policy-state change.
        custody = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        after_a = dict(counts)
        # (b) Busy nonreentrant custody refuses at the guard.
        assert owner.guard.acquire(blocking=False)
        try:
            with pytest.raises(gold.GoldBindingError):
                _dispatch(custody, owner, dataset, "h2", bundle_ids)
        finally:
            owner.guard.release()
        assert counts == after_a
        assert custody._invalid is False
        # (c) Closed ownership refuses at the state boundary.
        with pytest.raises(gold.GoldBindingError):
            _dispatch(custody, other, dataset, "h2", bundle_ids)
        assert counts == after_a
        assert custody._invalid is False
        # (d) Foreign creator PID refuses before custody.
        owner.pid = -1
        try:
            with pytest.raises(gold.GoldBindingError):
                _dispatch(custody, owner, dataset, "h2", bundle_ids)
        finally:
            owner.pid = os.getpid()
        assert counts == after_a
        assert custody._invalid is False
        # (e) An actual late-deadline cut under the real monotonic clock:
        # a legitimately admitted request with a short real lifetime; the
        # genuine delegated policy read completes late against the fixed
        # local observation end, latching the admission with no further
        # protected stage.  No caller-selectable clock is used.
        late = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=1000)
        before_late = dict(counts)
        real_read = capture.PolicyCaptureReader.read_selection.__get__(
            reader, type(reader)
        )

        def delayed_read(*args, **kwargs):
            counts["read"] += 1
            result = real_read(*args, **kwargs)
            time.sleep(1.5)
            return result

        monkeypatch.setattr(reader, "read_selection", delayed_read)
        with pytest.raises(gold.GoldBindingError):
            _dispatch(late, owner, dataset, "h2", bundle_ids)
        assert (counts["bundle"], counts["derived"], counts["original"]) == (1, 1, 1)
        assert counts["read"] == before_late["read"] + 1
        assert late._invalid is True
        assert owner.op.end == original_end
        assert owner.state == "ACTIVE"
        assert not owner.guard.locked()
    finally:
        _close_owned(ctx, owner)
