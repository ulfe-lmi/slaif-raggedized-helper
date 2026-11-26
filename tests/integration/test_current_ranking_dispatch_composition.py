"""Owned private held-pin ranking source dispatch composition proof.

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
setup that precedes its dispatch.  Counting wrappers attribute the real
catalog, bundle, derived, original-store verified read, owner-load and
reader calls to catalog-nested versus direct _pass dispatch at the
intended boundaries; counts run from the private dispatch after fixture
acquisition, and the legacy comparison is counted separately.  The
catalog-nested count formulas are derived from the exact source: each
catalog load performs two load_directory trees, each revalidating the
whole declared membership (one ingestion load per entry) and rebuilding
every dense and lexical partition once per distinct (partition, bundle,
batch) triple through one real load_group, plus one ingestion load per
unique row-map bundle and one per unique (bundle, batch) group, each
through one real load_group; every load_group performs one ingestion
load plus two additional derived loads, and every ingestion load
performs one derived load and one verified original read.
No local native execution: only the configured hosted CI executes the
real fixture.
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
from slaif_raggedized_helper import raw_snapshot_catalog  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_rows  # noqa: E402
from slaif_raggedized_helper import raw_snapshot_selection as selection  # noqa: E402
from slaif_raggedized_helper import source_bound_ranking as ranking  # noqa: E402
from slaif_raggedized_helper import supplied_policy_eligibility as policy_eligibility  # noqa: E402
from slaif_raggedized_helper.raw_snapshot_pin import PinOwner  # noqa: E402
import test_source_bound_support_ci_composition as support_fixture  # noqa: E402
import test_source_cohort_runner_composition as cohort_fixture  # noqa: E402
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: E402,F401

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


def _chunk_by_source(ctx, owner):
    # Fixture-time chunk map from the actual held row map: each source's
    # selected chunk, bound through the real per-row bundle load.  The
    # witness is installed only after this, so none of it counts.
    mapping = raw_snapshot_rows.parse(owner.value.data.row_map.map_bytes)
    by_source = {}
    for row in mapping.rows:
        bundle = ingestion_store.load(ctx.originals, ctx.derived, row.bundle_container_id)
        by_source[bundle.revision.source.logical_id] = row.chunk_id
    assert set(by_source) == {"a", "b", "c"}
    return by_source


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
        chunks = _chunk_by_source(ctx, owner)
        return ctx, dataset, bundle_ids, owner, policy_root, reader, chunks
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


def _shapes(owner):
    # Exact fixture shape from the actual held capture bytes: the unique
    # row-map bundles, the unique (bundle, batch) groups, the unique
    # membership-entry bundles and the unique (partition, bundle, batch)
    # triples.
    rows = raw_snapshot_rows.parse(owner.value.data.row_map.map_bytes).rows
    bundles = {row.bundle_container_id for row in rows}
    groups = {(row.bundle_container_id, row.batch_container_id) for row in rows}
    members = {entry.bundle_container_id for entry in owner.value.data.membership.entries}
    triples = {
        (row.partition_id, row.bundle_container_id, row.batch_container_id)
        for row in rows
    }
    return len(bundles), len(groups), len(members), len(triples)


def _per_catalog(bundles, groups, members, triples):
    # Exact source-derived per-catalog-load counts: (bundle, derived,
    # original).  Both load_directory trees revalidate the whole declared
    # membership (one ingestion load per entry) and rebuild every dense
    # and lexical partition, each once per distinct (partition, bundle,
    # batch) triple through one real load_group; loop one loads every
    # unique row-map bundle; loop two loads every unique (bundle, batch)
    # group directly, each through one real load_group; each load_group
    # performs one ingestion load plus two additional derived loads;
    # every ingestion load performs one derived load and one verified
    # original read.
    loads = 2 * members + bundles + 2 * groups + 4 * triples
    return loads, loads + 2 * (groups + 4 * triples), loads


def _counts():
    return {
        "catalog": 0,
        "bundle_catalog": 0,
        "bundle_pass": 0,
        "derived_catalog": 0,
        "derived_pass": 0,
        "original_catalog": 0,
        "original_pass": 0,
        "read": 0,
        "pin_load": 0,
        "catalog_ids": [],
        "direct_ids": [],
    }


def _assert_zero(counts):
    assert counts == _counts()


def _install_witness(monkeypatch, ctx, owner, reader, counts, *,
                     change_at_load=None, change_generation=None,
                     change_after_catalog=None, interrupt_read=None):
    # Counting wrappers that delegate the real functions at the intended
    # boundaries, attributed to catalog-nested versus direct _pass
    # dispatch by the load_catalog depth.  ``change_at_load`` is the exact
    # one-based direct _pass bundle load index; ``change_after_catalog``
    # is the exact one-based completed catalog index; ``change_generation``
    # is the attributed same-wire generation change callback, kept separate
    # from both indices; ``interrupt_read`` is a non-Exception interruption
    # object raised after one genuine delegated read.  No production hook
    # is added.
    state = {"in_catalog": 0}
    real_catalog = raw_snapshot_catalog.load_catalog
    real_bundle = ingestion_store.load
    real_derived = ctx.derived.load
    real_original = ctx.originals.read_verified
    real_pin_load = owner._load
    real_read = capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader)
    )

    def counting_catalog(*args, **kwargs):
        counts["catalog"] += 1
        state["in_catalog"] += 1
        try:
            result = real_catalog(*args, **kwargs)
        finally:
            state["in_catalog"] -= 1
        if (change_after_catalog is not None
                and counts["catalog"] == change_after_catalog
                and change_generation is not None):
            change_generation()
        return result

    def counting_bundle(*args, **kwargs):
        container_id = args[2] if len(args) >= 3 else kwargs["container_id"]
        if state["in_catalog"]:
            counts["bundle_catalog"] += 1
            counts["catalog_ids"].append(container_id)
        else:
            counts["bundle_pass"] += 1
            counts["direct_ids"].append(container_id)
        result = real_bundle(*args, **kwargs)
        if (change_at_load is not None and counts["bundle_pass"] == change_at_load
                and change_generation is not None):
            change_generation()
        return result

    def counting_derived(*args, **kwargs):
        if state["in_catalog"]:
            counts["derived_catalog"] += 1
        else:
            counts["derived_pass"] += 1
        return real_derived(*args, **kwargs)

    def counting_original(*args, **kwargs):
        if state["in_catalog"]:
            counts["original_catalog"] += 1
        else:
            counts["original_pass"] += 1
        return real_original(*args, **kwargs)

    def counting_pin_load(*args, **kwargs):
        counts["pin_load"] += 1
        return real_pin_load(*args, **kwargs)

    def counting_read(*args, **kwargs):
        counts["read"] += 1
        result = real_read(*args, **kwargs)
        if interrupt_read is not None:
            raise interrupt_read
        return result

    monkeypatch.setattr(raw_snapshot_catalog, "load_catalog", counting_catalog)
    monkeypatch.setattr(ingestion_store, "load", counting_bundle)
    monkeypatch.setattr(ctx.derived, "load", counting_derived)
    monkeypatch.setattr(ctx.originals, "read_verified", counting_original)
    monkeypatch.setattr(owner, "_load", counting_pin_load)
    monkeypatch.setattr(reader, "read_selection", counting_read)


def _dispatch(admission, owner, dataset, case_id, catalog_id, chunk_ids,
              *, deadline_ms=30000):
    return ranking.bind_pinned(admission, owner, dataset, case_id, catalog_id,
                               chunk_ids, deadline_ms=deadline_ms)


def test_pinned_positive_h2_matches_legacy(tmp_path, monkeypatch):
    (ctx, dataset, bundle_ids, owner, policy_root, reader, chunks) = _scenario(tmp_path)
    try:
        assert len(bundle_ids) == 3
        bundles, groups, members, triples = _shapes(owner)
        per_bundle, per_derived, per_original = _per_catalog(
            bundles, groups, members, triples)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        # A still-live pin whose prior acquisition end is already expired:
        # the new bounded dispatch must succeed and that old value returns.
        stale_end = time.monotonic() - 60.0
        owner.op.end = stale_end
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        selected = (chunks["a"], chunks["b"], chunks["c"])
        result = _dispatch(admission, owner, dataset, "h2", ctx.catalog_id, selected)
        # Two catalogs, six directly selected bundle dispatches and eight
        # genuine selected observations (one before each catalog dispatch
        # and each selected bundle load in both passes), with no new
        # pin/source reload in the measured span.
        assert (counts["catalog"], counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (2, 6, 6, 6)
        assert (counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == (
                    2 * per_bundle, 2 * per_derived, 2 * per_original)
        assert counts["read"] == 8
        assert counts["pin_load"] == 0
        assert admission._invalid is False
        assert owner.op.end == stale_end
        assert not owner.guard.locked()
        assert result.source_binding_status == "ORIGINALS_REVALIDATED_AT_BIND_TIME"
        assert result.snapshot_id == ctx.snapshot_id
        assert result.catalog_id == ctx.catalog_id
        assert [row.chunk_id for row in result.rows] == [
            chunks["a"], chunks["b"], chunks["c"]]
        # The one inherited ranking body is unchanged: the same admitted
        # inputs through the public legacy entry yield the same canonical
        # result, with the legacy pass counters kept separate.
        monkeypatch.undo()
        legacy_counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, legacy_counts)
        legacy = ranking.bind(ctx.originals, ctx.derived, ctx.root, ctx.snapshot_id,
                              ctx.catalog_id, selected, grants=ctx.grants,
                              restrictions=None, deadline_ms=30000)
        assert (legacy_counts["catalog"], legacy_counts["bundle_pass"],
                legacy_counts["derived_pass"], legacy_counts["original_pass"]) == (2, 6, 6, 6)
        assert (legacy_counts["bundle_catalog"], legacy_counts["derived_catalog"],
                legacy_counts["original_catalog"]) == (
                    2 * per_bundle, 2 * per_derived, 2 * per_original)
        assert legacy_counts["read"] == 0
        assert legacy_counts["pin_load"] == 0
        assert result == legacy
        assert result.binding_id == legacy.binding_id
        assert result.authority_sha256 == legacy.authority_sha256
    finally:
        _close_owned(ctx, owner)


def test_unavailable_b_retained_and_ac_dispatch(tmp_path, monkeypatch):
    (ctx, dataset, _bundle_ids, owner, policy_root, reader, chunks) = (
        _scenario(tmp_path, withhold_two=True))
    try:
        bundles, groups, members, triples = _shapes(owner)
        per_bundle, per_derived, per_original = _per_catalog(
            bundles, groups, members, triples)
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        original_end = owner.op.end
        # Prove the genuine affected partition: the withheld corpus-two
        # document pairs make b's partition genuinely unavailable under
        # the selected policy while the real pin still retains it.
        rows = raw_snapshot_rows.parse(owner.value.data.row_map.map_bytes).rows
        row_b = next(row for row in rows if row.chunk_id == chunks["b"])
        member_b = next(
            entry for entry in owner.value.data.membership.entries
            if entry.revision_id == row_b.revision_id
        )
        unavailable = set(policy_eligibility.unavailable_partitions(
            pin_eligibility._isolated_policy_snapshot(admission),
            owner.value.data.membership))
        assert member_b.partition_id in unavailable
        # The unavailable b remains pinned but the h2 case requests only
        # the readable a/c; the complete batch gates before any new source
        # I/O and the retained catalogs still reach b as trusted integrity.
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        selected = (chunks["a"], chunks["c"])
        result = _dispatch(admission, owner, dataset, "h2", ctx.catalog_id, selected)
        assert result.source_binding_status == "ORIGINALS_REVALIDATED_AT_BIND_TIME"
        assert [row.chunk_id for row in result.rows] == [chunks["a"], chunks["c"]]
        assert (counts["catalog"], counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (2, 4, 4, 4)
        assert (counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == (
                    2 * per_bundle, 2 * per_derived, 2 * per_original)
        assert counts["read"] == 6
        assert counts["pin_load"] == 0
        assert member_b.bundle_container_id in counts["catalog_ids"]
        assert member_b.bundle_container_id not in counts["direct_ids"]
        assert admission._invalid is False
        assert owner.state == "ACTIVE"
        assert owner.op.end == original_end
        assert not owner.guard.locked()
    finally:
        _close_owned(ctx, owner)


def test_precheck_refusals_zero_source_io(tmp_path, monkeypatch):
    (ctx, dataset, _bundle_ids, owner, policy_root, reader, chunks) = _scenario(tmp_path)
    try:
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        original_end = owner.op.end
        # (a) An unknown but well-formed selected chunk refuses the full
        # batch before any new source I/O.
        forged = "sha256:" + "ab" * 32
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        with pytest.raises(ranking.SourceBindingError):
            _dispatch(admission, owner, dataset, "h2", ctx.catalog_id,
                      (chunks["a"], chunks["b"], forged))
        _assert_zero(counts)
        assert admission._invalid is False
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        monkeypatch.undo()
        # (a2) A malformed identifier refuses at the entry boundary.
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        with pytest.raises(ranking.SourceBindingError):
            _dispatch(admission, owner, dataset, "h2", ctx.catalog_id,
                      (chunks["a"], "not-a-chunk"))
        _assert_zero(counts)
        assert admission._invalid is False
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        monkeypatch.undo()
        # (b) The real h1 case excludes b under the actual effective
        # intersection (corpus one only): the selected unreadable chunk
        # refuses before any new source I/O.
        counts = _counts()
        _install_witness(monkeypatch, ctx, owner, reader, counts)
        with pytest.raises(ranking.SourceBindingError):
            _dispatch(admission, owner, dataset, "h1", ctx.catalog_id,
                      (chunks["a"], chunks["b"]))
        _assert_zero(counts)
        assert admission._invalid is False
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        monkeypatch.undo()
        # (c) The independent withheld fixture, instrumented separately:
        # a genuinely unavailable selected partition refuses before any
        # new source I/O, even though the chunk is readable under the
        # effective h2 scope.
        second = tmp_path / "second"
        second.mkdir(mode=0o700)
        (ctx2, dataset2, _bundle_ids2, owner2, policy_root2, reader2,
         chunks2) = _scenario(second, withhold_two=True)
        try:
            admission2 = ppr.request_current_view(
                reader2, CREDENTIAL, deadline_ms=30000)
            original_end2 = owner2.op.end
            counts2 = _counts()
            _install_witness(monkeypatch, ctx2, owner2, reader2, counts2)
            with pytest.raises(ranking.SourceBindingError):
                _dispatch(admission2, owner2, dataset2, "h2", ctx2.catalog_id,
                          (chunks2["a"], chunks2["b"]))
            _assert_zero(counts2)
            assert admission2._invalid is False
            assert owner2.state == "ACTIVE"
            assert owner2.op.end == original_end2
            assert not owner2.guard.locked()
        finally:
            _close_owned(ctx2, owner2)
    finally:
        _close_owned(ctx, owner)


def test_change_after_last_pass_one_load_denies_catalog_two(tmp_path, monkeypatch):
    (ctx, dataset, _bundle_ids, owner, policy_root, reader, chunks) = _scenario(tmp_path)
    try:
        bundles, groups, members, triples = _shapes(owner)
        per_bundle, per_derived, per_original = _per_catalog(
            bundles, groups, members, triples)
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
        with pytest.raises(ranking.SourceBindingError):
            _dispatch(admission, owner, dataset, "h2", ctx.catalog_id,
                      (chunks["a"], chunks["b"], chunks["c"]))
        # One catalog and three directly selected starts; the actual
        # same-pin generation change after the final pass-one load makes
        # the next selected cut deny entrance to catalog two, with zero
        # subsequent load and no usable bound result.
        assert counts["catalog"] == 1
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (3, 3, 3)
        assert (counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == (
                    per_bundle, per_derived, per_original)
        assert counts["read"] == 5
        assert counts["pin_load"] == 0
        assert admission._invalid is True
        # The latched recheck refuses with zero further reader calls.
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 5
        assert owner.op.end == original_end
        assert not owner.guard.locked()
    finally:
        _close_owned(ctx, owner)


def test_change_after_first_catalog_and_observational_bounds(tmp_path, monkeypatch):
    (ctx, dataset, _bundle_ids, owner, policy_root, reader, chunks) = _scenario(tmp_path)
    try:
        bundles, groups, members, triples = _shapes(owner)
        per_bundle, per_derived, per_original = _per_catalog(
            bundles, groups, members, triples)
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
                         change_after_catalog=1, change_generation=change_generation)
        with pytest.raises(ranking.SourceBindingError):
            _dispatch(admission, owner, dataset, "h2", ctx.catalog_id,
                      (chunks["a"], chunks["b"], chunks["c"]))
        # One actual catalog, zero direct _pass bundle work, two selected
        # reads including the denial, bounded cleanup.
        assert counts["catalog"] == 1
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (0, 0, 0)
        assert (counts["bundle_catalog"], counts["derived_catalog"],
                counts["original_catalog"]) == (
                    per_bundle, per_derived, per_original)
        assert counts["read"] == 2
        assert counts["pin_load"] == 0
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        assert counts["read"] == 2
        assert owner.op.end == original_end
        assert not owner.guard.locked()
        # Subcases prove the observation/custody boundary only: nested
        # loads keep their own bounded local clocks and are never
        # preempted.  A fresh non-latched admission proves each boundary
        # refuses without protected work, read or policy-state change.
        fresh = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        assert fresh.selection.generation == 2
        _publish_selection(policy_root, 3, _encode_policy(
            [PRINCIPAL], _documents_from_membership(owner)))
        before = dict(counts)
        with pytest.raises(ranking.SourceBindingError):
            _dispatch(fresh, owner, dataset, "h2", ctx.catalog_id,
                      (chunks["a"], chunks["b"], chunks["c"]))
        assert counts["catalog"] == 1
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (0, 0, 0)
        assert counts["read"] == before["read"] + 1
        assert fresh._invalid is True
        custody = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        after_a = dict(counts)
        # Busy nonreentrant custody refuses at the guard.
        assert owner.guard.acquire(blocking=False)
        try:
            with pytest.raises(ranking.SourceBindingError):
                _dispatch(custody, owner, dataset, "h2", ctx.catalog_id,
                          (chunks["a"], chunks["b"], chunks["c"]))
        finally:
            owner.guard.release()
        assert counts == after_a
        assert custody._invalid is False
        # Closed ownership refuses at the state boundary.
        with pytest.raises(ranking.SourceBindingError):
            _dispatch(custody, other, dataset, "h2", ctx.catalog_id,
                      (chunks["a"], chunks["b"], chunks["c"]))
        assert counts == after_a
        assert custody._invalid is False
        # Foreign creator PID refuses before custody.
        owner.pid = -1
        try:
            with pytest.raises(ranking.SourceBindingError):
                _dispatch(custody, owner, dataset, "h2", ctx.catalog_id,
                          (chunks["a"], chunks["b"], chunks["c"]))
        finally:
            owner.pid = os.getpid()
        assert counts == after_a
        assert custody._invalid is False
        # An actual late-deadline cut under the real monotonic clock: a
        # legitimately admitted request with a short real lifetime; the
        # genuine delegated policy read completes late against the fixed
        # local observation end, latching the admission with no protected
        # work.  No caller-selectable clock is used.
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
        with pytest.raises(ranking.SourceBindingError):
            _dispatch(late, owner, dataset, "h2", ctx.catalog_id,
                      (chunks["a"], chunks["b"], chunks["c"]))
        assert counts["catalog"] == 1
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (0, 0, 0)
        assert counts["read"] == before_late["read"] + 1
        assert late._invalid is True
        assert owner.op.end == original_end
        assert owner.state == "ACTIVE"
        assert not owner.guard.locked()
        # A non-Exception interruption object propagates by identity
        # through the first selected observation, with custody restored
        # and no admission latch (only ordinary observation failures
        # latch).
        monkeypatch.undo()
        interrupted = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        interrupt = KeyboardInterrupt("owned-interruption")
        _install_witness(monkeypatch, ctx, owner, reader, counts,
                         interrupt_read=interrupt)
        before_interrupt = dict(counts)
        with pytest.raises(BaseException) as excinfo:
            _dispatch(interrupted, owner, dataset, "h2", ctx.catalog_id,
                      (chunks["a"], chunks["b"], chunks["c"]))
        assert excinfo.value is interrupt
        assert counts["catalog"] == 1
        assert (counts["bundle_pass"], counts["derived_pass"],
                counts["original_pass"]) == (0, 0, 0)
        assert counts["read"] == before_interrupt["read"] + 1
        assert interrupted._invalid is False
        assert owner.op.end == original_end
        assert owner.state == "ACTIVE"
        assert not owner.guard.locked()
    finally:
        _close_owned(ctx, owner)
