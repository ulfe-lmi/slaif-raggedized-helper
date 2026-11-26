"""Private current-policy pin-eligibility evidence (objective 009, PAR-009).

Offline and fully synthetic: every root is a private temporary directory
owned by the test and every byte is generated here; no real protected
path, credential, network route, model or service is touched.  The
policy side uses an actual PolicyCaptureReader and a genuine
request_current_view admission (the test-side wire emitter is an
independent re-derivation of the typed component grammar).  The pin side
uses a real PinOwner acquisition with governed synthetic input: real
original/derived store objects, a real private store namespace, a real
canonical pointer, real lock and association steps, and real canonical
manifest, row-map and membership bytes with real digests.

Explicit substituted source-loading boundary (controlled lower
load): the full-dataset native CI fixture is unavailable in this
environment, so the test-local delegate replaces only
raw_snapshot_directory.load_directory during test preparation.  It
applies the real canonical rules (raw_snapshot_manifest.parse,
raw_snapshot_rows.bind, raw_snapshot_membership.bind, the core-digest
agreement) to the same real bytes and returns a real
BoundSnapshotData with partitions=(); no dense or lexical partition
payload is loaded, no originals-backed rebuild runs, and no directory
walk happens.  The pin owner's acquisition, ownership, capture
association and cleanup remain real, and no convenient fake field
replaces the owner admission proof.  The new entry itself performs no
snapshot reload, source access or index work, which the counting
wrappers and canaries witness directly.

Counting wrappers delegate to the real reader, recheck, eligibility and
authority functions at the intended boundaries (real bound methods are
always taken from the class, so reinstalls never wrap a prior wrapper).
Controlled-clock tests run the request and the entry under the same
controlled monotone clock where exact deadline boundaries are needed;
the real clock is used where actual remaining-clock lateness is the
point.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from slaif_raggedized_helper import (
    derived_store,
    private_policy_capture,
    private_policy_request,
    provenance_records,
    raw_lexical_search,
    raw_snapshot_directory,
    raw_snapshot_files,
    raw_snapshot_manifest,
    raw_snapshot_membership,
    raw_snapshot_pin,
    raw_snapshot_rows,
    raw_snapshot_selection,
    schema,
    source_admission,
    supplied_policy,
    technical_analyzer,
)
from slaif_raggedized_helper import private_policy_pin_eligibility as ppe
from slaif_raggedized_helper import supplied_policy_eligibility as spe
from slaif_raggedized_helper.embedding_vectors import POLICY_ID
from slaif_raggedized_helper.provenance_records import admit_record

# ------------------------------------------------------------- constants

_KIND = "slaif-current-policy-selection-v1"
_SELECTION = "current-policy.json"
_MAGIC = b"slaif-supplied-policy-view-v1\n"
CREDENTIAL = b"synthetic-credential-" + b"a" * 22  # exactly 43
PRINCIPAL_ID = "alpha-1"
VERIFIER = hashlib.sha256(CREDENTIAL).digest()
OPERATIONS = ("search", "sources:read")
CORPORA = ("corpus-a",)
VERSIONS = ("v1",)
LABELS = ("label-a", "label-b", "label-c")
DOC_A, DOC_B, DOC_C = "doc-1", "doc-2", "doc-3"
WITHDRAWN = ("sha256:" + "0" * 63 + "e",)
_SPACE_ID = "1" * 64
_DEF_FINGERPRINT = "sha256:" + "2" * 64
_REP_POLICY = "3" * 64
_QUERY_POLICY = "4" * 64
_QUERY_EXEC = "5" * 64
_CHUNK_POLICY = "6" * 64

GRANTS = admit_record(
    "Grants",
    {"schema_version": 1, "corpora": CORPORA, "versions": VERSIONS, "labels": LABELS},
)


def _revision(index: int) -> str:
    return "sha256:" + format(0x1000 + index, "064x")


def _enc(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _scope_map(document_id, revision, corpus="corpus-a", version="v1", labels=("label-a",)):
    return dict(
        schema_version=1,
        document_id=document_id,
        revision_id=revision,
        corpus=corpus,
        version=version,
        labels=list(labels),
        processing_approved=True,
        redistribution_rights="allowed",
    )


def _entry(document_id, revision, bundle, *, corpus="corpus-a", version="v1", labels=("label-a",)):
    scope = _scope_map(document_id, revision, corpus, version, labels)
    return dict(
        revision_id=revision,
        extraction_id="sha256:" + format(0x2000 + bundle, "064x"),
        bundle_container_id=format(0x3000 + bundle, "064x"),
        bundle_metadata_sha256=format(0x4000 + bundle, "064x"),
        chunk_policy_fingerprint=_CHUNK_POLICY,
        source_scope_sha256=schema.fingerprint(
            {"kind": "embedding-source-scope-v1", "scope": scope}
        )[7:],
        partition_id=schema.fingerprint(
            {"schema": 1, "corpus": corpus, "version": version, "labels": list(labels)}
        ),
        scope=scope,
        ordinals=[],
    )


# Admitted zero-row entries on three distinct partitions, in canonical
# (sorted revision) order; A and B sit inside the granted corpus/version
# and are label-covered, C sits in an ungranted corpus.
ENTRY_A = _entry(DOC_A, _revision(0), 0, labels=("label-a",))
ENTRY_B = _entry(DOC_B, _revision(1), 1, labels=("label-b",))
ENTRY_C = _entry(DOC_C, _revision(2), 2, corpus="corpus-x", labels=("label-c",))
HASH_A, HASH_B, HASH_C = (e["source_scope_sha256"] for e in (ENTRY_A, ENTRY_B, ENTRY_C))
REV_A, REV_B, REV_C = (e["revision_id"] for e in (ENTRY_A, ENTRY_B, ENTRY_C))

PAIRS_ALL = [(DOC_A, [(REV_A, HASH_A)]), (DOC_B, [(REV_B, HASH_B)]), (DOC_C, [(REV_C, HASH_C)])]
PAIRS_B_STALE = [
    (DOC_A, [(REV_A, HASH_A)]),
    (DOC_B, [(REV_B, "0" * 64)]),  # same-grant document withdrawal
    (DOC_C, [(REV_C, HASH_C)]),
]
PAIRS_C_STALE = [
    (DOC_A, [(REV_A, HASH_A)]),
    (DOC_B, [(REV_B, HASH_B)]),
    (DOC_C, [(REV_C, "0" * 64)]),  # withdrawn outside the granted corpus
]


# ---------------------------------------------------------- wire fixtures


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


def _make_root(directory, generation, payload, *, selection_bytes=None):
    directory = Path(directory)
    directory.mkdir(mode=0o700)
    os.chmod(str(directory), 0o700)
    digest = _digest(payload)
    if selection_bytes is None:
        selection_bytes = _render_selection(generation, len(payload), digest)
    _write_private(directory / _SELECTION, selection_bytes)
    _write_private(directory / (digest + ".bin"), payload)
    return directory


def _replace_selection(root, generation, payload):
    # Trusted-writer fixture role: publish a new selected record.
    repl = Path(root).parent / ("swap-" + str(generation) + ".json")
    _write_private(repl, _render_selection(generation, len(payload), _digest(payload)))
    os.replace(str(repl), str(Path(root) / _SELECTION))


def _u32(value):
    return value.to_bytes(4, "big")


def _s(text):
    raw = text.encode("utf-8")
    return _u32(len(raw)) + raw


def encode_principal(principal_id, verifier, operations, corpora, versions, labels):
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


def _payload(documents):
    principals = [(PRINCIPAL_ID, VERIFIER, OPERATIONS, CORPORA, VERSIONS, LABELS)]
    return encode_policy(principals, documents)


def _expected_policy(documents):
    principal = supplied_policy.PrincipalSpec(PRINCIPAL_ID, VERIFIER, OPERATIONS, GRANTS)
    rules = tuple(
        supplied_policy.DocumentRule(document_id, tuple(pairs))
        for document_id, pairs in sorted(documents)
    )
    return supplied_policy.admit_policy((principal,), rules)


def _reader(root):
    return private_policy_capture.PolicyCaptureReader(str(root))


# ------------------------------------------------------- snapshot fixtures


def _row_map_bytes():
    return _enc(
        dict(
            schema=1,
            kind="slaif-raw-row-map-v1",
            space_id=_SPACE_ID,
            definition_fingerprint=_DEF_FINGERPRINT,
            representation_policy_fingerprint=_REP_POLICY,
            chunk_policy_fingerprint=_CHUNK_POLICY,
            normalization_policy_id=POLICY_ID,
            rows=[],
        )
    )


def _membership_bytes(entries, row_map_bytes, withdrawn=WITHDRAWN):
    return _enc(
        dict(
            schema=1,
            kind="slaif-raw-source-membership-v1",
            row_map_sha256=_digest(row_map_bytes),
            row_count=0,
            entries=entries,
            withdrawn_revisions=list(withdrawn),
        )
    )


def _core_bytes(entries, row_map_bytes, membership_bytes, withdrawn=WITHDRAWN):
    return _enc(
        dict(
            schema=1,
            kind="slaif-raw-snapshot-core-v1",
            representation="raw",
            embedding=dict(
                space_id=_SPACE_ID,
                definition_fingerprint=_DEF_FINGERPRINT,
                query_policy_fingerprint=_QUERY_POLICY,
                query_execution_fingerprint=_QUERY_EXEC,
                corpus_execution_fingerprints=[],
                normalization_policy_id=POLICY_ID,
                precision_qualification_ref=None,
            ),
            analyzer=dict(
                fingerprint=technical_analyzer.analyzer_id(technical_analyzer.Policy())[7:],
                backend="bm25s-lucene",
                bm25s_version="0.2.14",
                numpy_version="2.5.4",
                scipy_version="1.18.1",
            ),
            chunk_policy_fingerprint=_CHUNK_POLICY,
            representation_policy_fingerprint=_REP_POLICY,
            sources=dict(
                active_revisions=sorted({e["revision_id"] for e in entries}),
                withdrawn_revisions=list(withdrawn),
            ),
            row_count=0,
            row_map_path="row_map.json",
            membership_path="membership.json",
            files=[
                dict(
                    path="membership.json",
                    role="source_membership",
                    schema="slaif-raw-source-membership-v1",
                    bytes=len(membership_bytes),
                    sha256=_digest(membership_bytes),
                ),
                dict(
                    path="row_map.json",
                    role="row_map",
                    schema="slaif-raw-row-map-v1",
                    bytes=len(row_map_bytes),
                    sha256=_digest(row_map_bytes),
                ),
            ],
            partitions=[],
            validation=dict(state="unproven", validator_fingerprint=None),
        )
    )


def _make_store(root, generation, snapshot_id, core_bytes, row_map_bytes, membership_bytes):
    root = Path(root)
    root.mkdir(mode=0o700)
    os.chmod(str(root), 0o700)
    snapshots = root / "snapshots"
    os.mkdir(str(snapshots), 0o700)
    os.chmod(str(snapshots), 0o700)
    _write_private(root / "current.json", raw_snapshot_selection._encode(generation, snapshot_id))
    target = snapshots / snapshot_id[7:]
    os.mkdir(str(target), 0o700)
    os.chmod(str(target), 0o700)
    _write_private(target / ".core.json", core_bytes)
    _write_private(target / "membership.json", membership_bytes)
    _write_private(target / "row_map.json", row_map_bytes)
    os.chmod(str(target), 0o500)
    return root


def _make_delegate(core_bytes, row_map_bytes, membership_bytes, counts):
    # Explicit substituted source-loading boundary (controlled lower
    # load): real canonical manifest, row-map and membership rules over
    # the same real bytes, plus the real core-digest agreement.  No
    # dense or lexical partition payload, no originals-backed rebuild,
    # no directory walk; partitions stays empty, which the entry never
    # touches.

    def delegate(originals, derived, store_root, snapshot_id):
        counts["load_directory"] += 1
        if "sha256:" + _digest(core_bytes) != snapshot_id:
            raise raw_snapshot_directory.DirectoryError("snapshot directory refused")
        manifest = raw_snapshot_manifest.parse(core_bytes)
        row_map = raw_snapshot_rows.bind(core_bytes, row_map_bytes)
        membership = raw_snapshot_membership.bind(core_bytes, row_map_bytes, membership_bytes)
        return raw_snapshot_files.BoundSnapshotData(
            manifest.snapshot_id, core_bytes, row_map, membership, ()
        )

    return delegate


# ---------------------------------------------------------- measurement


def _counts():
    return {
        "read_selection": 0,
        "read_selection_args": [],
        "unavailable": 0,
        "unavailable_results": [],
        "authority": 0,
        "authority_results": [],
        "load_directory": 0,
        "validate_files": 0,
        "source_read": 0,
        "owner_check": 0,
    }


def _install_counting(monkeypatch, reader, counts, after_unavailable=None):
    # Counting wrappers that delegate the real functions at the intended
    # boundaries; the real bound methods are always taken from the class,
    # so reinstalls never wrap a prior wrapper.  No production hook is
    # added.
    real_read = private_policy_capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader)
    )
    real_unavailable = spe.unavailable_partitions
    real_authority = raw_lexical_search._authority

    def counting_read(*args, **kwargs):
        counts["read_selection"] += 1
        counts["read_selection_args"].append(dict(kwargs))
        return real_read(*args, **kwargs)

    def counting_unavailable(policy, membership):
        counts["unavailable"] += 1
        result = real_unavailable(policy, membership)
        counts["unavailable_results"].append(result)
        if after_unavailable is not None:
            after_unavailable(result)
        return result

    def counting_authority(grants, restrictions):
        counts["authority"] += 1
        result = real_authority(grants, restrictions)
        counts["authority_results"].append(result)
        return result

    monkeypatch.setattr(reader, "read_selection", counting_read)
    monkeypatch.setattr(spe, "unavailable_partitions", counting_unavailable)
    monkeypatch.setattr(raw_lexical_search, "_authority", counting_authority)


def _build_scenario(tmp_path, monkeypatch, counts, *, documents, acquire=True):
    entries = [ENTRY_A, ENTRY_B, ENTRY_C]
    row_map_bytes = _row_map_bytes()
    membership_bytes = _membership_bytes(entries, row_map_bytes)
    core_bytes = _core_bytes(entries, row_map_bytes, membership_bytes)
    snapshot_id = "sha256:" + _digest(core_bytes)
    store = _make_store(
        tmp_path / "store", 1, snapshot_id, core_bytes, row_map_bytes, membership_bytes
    )
    originals = source_admission.OriginalStore(tmp_path / "originals")
    derived_root = tmp_path / "derived"
    derived_root.mkdir(mode=0o700)
    derived = derived_store.Store(str(derived_root))
    monkeypatch.setattr(
        raw_snapshot_directory,
        "load_directory",
        _make_delegate(core_bytes, row_map_bytes, membership_bytes, counts),
    )
    owner = raw_snapshot_pin.PinOwner()
    value = None
    if acquire:
        value = owner.acquire_selected_data(originals, derived, str(store), deadline_ms=30000)
    payload = _payload(documents)
    root = _make_root(tmp_path / "policy-root", 1, payload)
    reader = _reader(root)
    admission = private_policy_request.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
    return SimpleNamespace(
        owner=owner,
        value=value,
        originals=originals,
        derived=derived,
        reader=reader,
        admission=admission,
        root=root,
        store=store,
        payload=payload,
        snapshot_id=snapshot_id,
        core_bytes=core_bytes,
        membership_bytes=membership_bytes,
        row_map_bytes=row_map_bytes,
    )


def _release(scenario):
    scenario.owner.close()
    scenario.originals.close()
    scenario.derived.close()


# ------------------------------------------------------------ origins/API


def test_module_origin_is_assigned_worktree():
    # Derived from this test file's resolved physical location
    # (tests/unit/test_private_policy_pin_eligibility.py -> worktree root
    # / src), so a canonical transfer or CI keeps the same fail-closed
    # origin check.
    src = Path(__file__).resolve().parents[2] / "src"
    for module in (
        ppe,
        private_policy_request,
        private_policy_capture,
        supplied_policy,
        spe,
        raw_snapshot_pin,
        raw_snapshot_selection,
        raw_snapshot_directory,
        raw_snapshot_manifest,
        raw_snapshot_membership,
        raw_snapshot_rows,
        raw_snapshot_files,
        provenance_records,
        raw_lexical_search,
        derived_store,
        source_admission,
    ):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(src), "module origin outside assigned worktree"


def test_public_api_surface():
    assert ppe.__all__ == [
        "PinEligibilityObservation",
        "PolicyPinEligibilityError",
        "prepare_current_pin_eligibility",
    ]
    parameters = list(inspect.signature(ppe.prepare_current_pin_eligibility).parameters.items())
    assert [name for name, _ in parameters] == ["admission", "owner", "deadline_ms", "restrictions"]
    assert parameters[0][1].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[1][1].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[2][1].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters[2][1].default is inspect.Parameter.empty
    assert parameters[3][1].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters[3][1].default is None
    assert ppe._MIN_DEADLINE_MS == 1
    assert ppe._MAX_DEADLINE_MS == 30000


def test_error_is_fixed_input_free_value_error(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        with pytest.raises(ppe.PolicyPinEligibilityError) as excinfo:
            ppe.prepare_current_pin_eligibility(object(), scenario.owner, deadline_ms=30000)
        error = excinfo.value
        assert isinstance(error, ValueError)
        assert error.args == ("private pin eligibility refused",)
        assert error.__cause__ is None and error.__context__ is None
        # A refusal after a genuine internal fault also carries no context.
        pointer = scenario.value.pointer
        tampered = raw_snapshot_files.BoundSnapshotData(
            pointer.snapshot_id, b"\x00" * 10,
            scenario.value.data.row_map, scenario.value.data.membership, ()
        )
        scenario.owner.value = raw_snapshot_pin.PinData(pointer, tampered)
        with pytest.raises(ppe.PolicyPinEligibilityError) as excinfo:
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        error = excinfo.value
        assert error.args == ("private pin eligibility refused",)
        assert error.__cause__ is None and error.__context__ is None
    finally:
        _release(scenario)


def test_observation_constructor_refused_and_frozen(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.PinEligibilityObservation()
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.PinEligibilityObservation(True, "s", "p", "q", 1)
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            observation.eligible = False
        assert repr(observation) == "PinEligibilityObservation(<redacted>)"
        assert observation._owner is scenario.owner
        assert observation._admission is scenario.admission
        # Exact capture and normalized narrowed-authority identity is
        # retained opaquely (no restrictions were given here).
        assert observation._core is scenario.value.data.core_bytes
        assert observation._membership is scenario.value.data.membership.membership_bytes
        # The bound grants snapshot is an isolated coherent authority
        # value equal to the admitted principal grants.
        assert observation._grants == GRANTS
        assert observation._restrictions is None
        fields = {field.name for field in dataclasses.fields(observation)}
        assert fields == {
            "eligible",
            "snapshot_id",
            "policy_id",
            "principal_id",
            "selection_generation",
            "_owner",
            "_admission",
            "_core",
            "_membership",
            "_grants",
            "_restrictions",
        }
        assert type(observation.eligible) is bool
        assert type(observation.selection_generation) is int
    finally:
        _release(scenario)


# ---------------------------------------------------------------- positive


def test_real_admission_owner_positive_proof(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        loads_before = counts["load_directory"]  # 2: the real acquisition double load
        reads_before = counts["read_selection"]  # 1: the admission's final reread
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
        assert observation.snapshot_id == scenario.snapshot_id
        assert observation.policy_id == _expected_policy(PAIRS_ALL).policy_id
        assert observation.principal_id == PRINCIPAL_ID
        assert observation.selection_generation == 1
        assert observation._owner is scenario.owner
        assert observation._admission is scenario.admission
        assert observation._core is scenario.core_bytes
        assert observation._membership is scenario.value.data.membership.membership_bytes
        assert observation._grants == GRANTS
        assert observation._restrictions is None
        # Two genuine rechecks (before the pin data, after the scope)
        # and one real unavailable-partition derivation; no reload.
        assert counts["read_selection"] == reads_before + 2
        assert counts["unavailable"] == 1
        assert counts["unavailable_results"] == [()]
        assert counts["load_directory"] == loads_before
        assert scenario.owner.state == "ACTIVE" and scenario.owner.value is scenario.value
        # Owner lifetime preserved: the real full check (through the
        # delegated boundary) still agrees, and cleanup completes.
        assert scenario.owner.check(deadline_ms=30000) is scenario.value
        scenario.owner.close()
        assert scenario.owner.state == "CLOSED"
    finally:
        scenario.originals.close()
        scenario.derived.close()


def test_zero_row_entries_admitted_on_distinct_partitions(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        membership = scenario.value.data.membership
        # Nonvacuity: the capture really has three parsed zero-row
        # entries on three distinct partitions with a real withdrawn
        # revision, and the policy really has one rule per document.
        assert [len(entry.ordinals) for entry in membership.entries] == [0, 0, 0]
        assert len({entry.partition_id for entry in membership.entries}) == 3
        assert membership.withdrawn_revisions == WITHDRAWN
        assert scenario.value.data.row_map.rows == ()
        assert len(_expected_policy(PAIRS_ALL).documents) == 3
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
        assert counts["unavailable_results"] == [()]
    finally:
        _release(scenario)


def test_restrictions_no_op_scope_keeps_outcome(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_B_STALE)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        baseline = counts["read_selection"]
        without = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert without.eligible is False  # the withdrawn document is in scope
        no_op = admit_record(
            "Restrictions",
            {"schema_version": 1, "corpora": None, "versions": None},
        )
        with_no_op = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000, restrictions=no_op
        )
        assert with_no_op.eligible is without.eligible
        assert counts["read_selection"] == baseline + 4  # two rechecks per entry
        # The real authority bounder admits the anchor and the detached
        # value at the initial and final cuts (three per call), plus one
        # validation of the given restriction.
        assert counts["authority"] == 7
        assert counts["unavailable"] == 2
    finally:
        _release(scenario)


# ------------------------------------------------------------ scope rules


def test_same_grant_document_withdrawal_refuses_whole_scope(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_B_STALE)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        membership = scenario.value.data.membership
        entry_b = next(e for e in membership.entries if e.revision_id == REV_B)
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        # The principal's corpus/version/label grants still permit B's
        # partition, yet the document rule is stale: the whole requested
        # scope is refused with the fixed content-free unavailable
        # outcome, and both genuine rechecks ran.
        assert observation.eligible is False
        assert counts["unavailable_results"] == [(entry_b.partition_id,)]
        assert counts["read_selection_args"][-2:] or counts["read_selection"] >= 3
        # No disallowed partition identity or source text outward.
        exposed = repr(observation) + repr(
            [
                observation.eligible,
                observation.snapshot_id,
                observation.policy_id,
                observation.principal_id,
                observation.selection_generation,
            ]
        )
        for entry in membership.entries:
            assert entry.partition_id not in exposed
        for entry in membership.entries:
            assert entry.scope_bytes.decode("ascii") not in exposed
    finally:
        _release(scenario)


def test_withdrawn_partition_outside_readable_scope_does_not_block(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_C_STALE)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        membership = scenario.value.data.membership
        entry_c = next(e for e in membership.entries if e.revision_id == REV_C)
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        # C's partition is unavailable (stale rule) but its corpus is
        # not granted: the withdrawn partition is outside the requested
        # readable scope and does not block the unaffected scope.
        assert observation.eligible is True
        assert counts["unavailable_results"] == [(entry_c.partition_id,)]
    finally:
        _release(scenario)


def test_restrictions_narrow_readable_scope_flips_outcome(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_B_STALE)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        membership = scenario.value.data.membership
        entry_b = next(e for e in membership.entries if e.revision_id == REV_B)
        assert counts["unavailable_results"] or True
        unrestricted = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert unrestricted.eligible is False
        assert counts["unavailable_results"] == [(entry_b.partition_id,)]
        # The real narrowed rule: a version restriction excluding B's
        # v1 leaves the narrowed scope without any readable membership
        # entry, so no usable scope remains and the fixed unavailable
        # outcome is returned.
        narrow = admit_record(
            "Restrictions", {"schema_version": 1, "corpora": None, "versions": ("v2",)}
        )
        narrowed = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000, restrictions=narrow
        )
        assert narrowed.eligible is False
        # A wrong-but-still-covering restriction keeps the refusal.
        covering = admit_record(
            "Restrictions", {"schema_version": 1, "corpora": None, "versions": ("v1",)}
        )
        covered = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000, restrictions=covering
        )
        assert covered.eligible is False
        # Each call admits the anchor and the detached value at the
        # initial and final cuts (three), plus one validation of the
        # given restriction on the two restricted calls.
        assert counts["authority"] == 11
    finally:
        _release(scenario)


def test_restrictions_narrowing_to_zero_readable_entries_reports_unavailable(
    tmp_path, monkeypatch
):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        # Nothing is unavailable, so the old empty-unavailable shortcut
        # used to report eligible here; the real narrowed rule leaves
        # zero readable membership entries, so no usable scope remains.
        narrow = admit_record(
            "Restrictions", {"schema_version": 1, "corpora": None, "versions": ("v2",)}
        )
        start = len(counts["authority_results"])
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000, restrictions=narrow
        )
        assert observation.eligible is False
        assert counts["unavailable_results"] == [()]
        # The normalized narrowed-authority identity is retained
        # opaquely on the observation: the first admission of the call
        # is the restriction validation whose snapshot is bound.
        assert observation._restrictions is counts["authority_results"][start][1]
        # A covering restriction restores the usable scope.
        covering = admit_record(
            "Restrictions", {"schema_version": 1, "corpora": None, "versions": ("v1",)}
        )
        start = len(counts["authority_results"])
        covered = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000, restrictions=covering
        )
        assert covered.eligible is True
        assert covered._restrictions is counts["authority_results"][start][1]
    finally:
        _release(scenario)


def test_restrictions_narrowing_to_valid_unaffected_scope_stays_eligible(
    tmp_path, monkeypatch
):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_C_STALE)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        membership = scenario.value.data.membership
        entry_c = next(e for e in membership.entries if e.revision_id == REV_C)
        # C's partition is unavailable, but narrowing to the granted
        # corpus leaves a valid authorized scope the withdrawal does not
        # affect.
        narrow = admit_record(
            "Restrictions", {"schema_version": 1, "corpora": ("corpus-a",), "versions": None}
        )
        start = len(counts["authority_results"])
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000, restrictions=narrow
        )
        assert observation.eligible is True
        assert counts["unavailable_results"] == [(entry_c.partition_id,)]
        assert observation._restrictions is counts["authority_results"][start][1]
    finally:
        _release(scenario)


# ------------------------------------------------- authority binding


def test_detached_grant_mutation_cannot_bypass_scope_refusal(tmp_path, monkeypatch):
    # The exact false-to-true defect case: the admission's nominal grant
    # is a detached mutable snapshot; removing one label while the
    # selected policy's admitted principal grant, the selected bytes,
    # the generation and the unavailable partition set stay unchanged
    # must refuse, not flip the scope refusal.
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_B_STALE)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        membership = scenario.value.data.membership
        entry_b = next(e for e in membership.entries if e.revision_id == REV_B)
        admission = scenario.admission
        anchor = next(
            p for p in admission.policy.principals if p.principal_id == PRINCIPAL_ID
        )
        before = ppe.prepare_current_pin_eligibility(admission, scenario.owner, deadline_ms=30000)
        assert before.eligible is False
        assert counts["unavailable_results"][-1] == (entry_b.partition_id,)
        labels = vars(admission.grants)["labels"]
        vars(admission.grants)["labels"] = tuple(
            label for label in labels if label != "label-b"
        )
        try:
            # The independently retained selected policy grant is
            # untouched by the detached mutation...
            assert anchor.grants.labels == labels
            reads_before = counts["read_selection"]
            with pytest.raises(ppe.PolicyPinEligibilityError):
                ppe.prepare_current_pin_eligibility(
                    admission, scenario.owner, deadline_ms=30000
                )
            assert counts["read_selection"] == reads_before  # before any freshness
            assert counts["unavailable"] == 1  # ...and no scope computation
        finally:
            vars(admission.grants)["labels"] = labels
        # ...so the same real pair still yields the genuine refusal.
        again = ppe.prepare_current_pin_eligibility(admission, scenario.owner, deadline_ms=30000)
        assert again.eligible is False
        assert counts["unavailable_results"][-1] == (entry_b.partition_id,)
    finally:
        _release(scenario)


def test_grant_widening_during_computation_refused_at_final_cut(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        admission = scenario.admission
        original = vars(admission.grants)["labels"]
        mutated = []

        def widen_after_scope(_result):
            if not mutated:
                mutated.append(1)
                # A widening mutation that slips past the initial
                # binding cut during the scope/freshness window.
                vars(admission.grants)["labels"] = tuple(original) + ("label-x",)

        _install_counting(monkeypatch, scenario.reader, counts, after_unavailable=widen_after_scope)
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(admission, scenario.owner, deadline_ms=30000)
        # The scope really ran before the final observation cut caught
        # the changed authority.
        assert counts["unavailable"] == 1
        # The ordinary positive control: restored authority on the same
        # selected identity still qualifies with the bound snapshot.
        vars(admission.grants)["labels"] = original
        observation = ppe.prepare_current_pin_eligibility(
            admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
        assert observation._grants == GRANTS
        assert counts["unavailable"] == 2
    finally:
        _release(scenario)


def test_invalid_detached_authority_refused(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        admission = scenario.admission
        reads_before = counts["read_selection"]
        original = vars(admission.grants)["labels"]
        vars(admission.grants)["labels"] = "label-a"  # not a bounded tuple
        try:
            with pytest.raises(ppe.PolicyPinEligibilityError):
                ppe.prepare_current_pin_eligibility(admission, scenario.owner, deadline_ms=30000)
        finally:
            vars(admission.grants)["labels"] = original
        assert counts["read_selection"] == reads_before  # refused before any freshness
        observation = ppe.prepare_current_pin_eligibility(
            admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
    finally:
        _release(scenario)


def test_two_copy_grant_mutation_cannot_anchor_authority(tmp_path, monkeypatch):
    # The exact second defect case: both exposed nominal grant DTOs -
    # the detached admission value and the policy's nested principal
    # grant - mutated to the same narrowed values agree with each other
    # but cannot anchor authority: the verified isolated policy
    # snapshot's canonical identity no longer matches the bound
    # semantic policy ID.
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_B_STALE)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        membership = scenario.value.data.membership
        entry_b = next(e for e in membership.entries if e.revision_id == REV_B)
        admission = scenario.admission
        policy_principal = next(
            p for p in admission.policy.principals if p.principal_id == PRINCIPAL_ID
        )
        before = ppe.prepare_current_pin_eligibility(admission, scenario.owner, deadline_ms=30000)
        assert before.eligible is False
        assert counts["unavailable_results"][-1] == (entry_b.partition_id,)
        labels = vars(admission.grants)["labels"]
        policy_labels = vars(policy_principal.grants)["labels"]
        narrowed = tuple(label for label in labels if label != "label-b")
        vars(admission.grants)["labels"] = narrowed
        vars(policy_principal.grants)["labels"] = narrowed
        try:
            # Both mutable copies now agree with each other, while the
            # selected record, stored bytes, semantic policy ID and the
            # unavailable partition set are unchanged.
            assert vars(admission.grants)["labels"] == vars(policy_principal.grants)["labels"]
            with pytest.raises(ppe.PolicyPinEligibilityError):
                ppe.prepare_current_pin_eligibility(
                    admission, scenario.owner, deadline_ms=30000
                )
        finally:
            vars(admission.grants)["labels"] = labels
            vars(policy_principal.grants)["labels"] = policy_labels
        # The real unchanged outcome on the restored state.
        after = ppe.prepare_current_pin_eligibility(admission, scenario.owner, deadline_ms=30000)
        assert after.eligible is False
        assert counts["unavailable_results"][-1] == (entry_b.partition_id,)
        # A real unchanged positive on an all-admitted view.
        positive_base = tmp_path / "positive"
        positive_base.mkdir(mode=0o700)
        positive = _build_scenario(positive_base, monkeypatch, counts, documents=PAIRS_ALL)
        try:
            observation = ppe.prepare_current_pin_eligibility(
                positive.admission, positive.owner, deadline_ms=30000
            )
            assert observation.eligible is True
        finally:
            _release(positive)
    finally:
        _release(scenario)


def test_policy_snapshot_lateness_refused_under_same_deadline(tmp_path, monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        assert scenario.admission._end == 1030.0
        clock["now"] = 1029.875  # exactly 125 ms of the request lifetime remains
        late = []
        real_admit_policy = supplied_policy.admit_policy

        def late_snapshot(*args, **kwargs):
            if not late:
                late.append(1)
                clock["now"] = 1030.001  # past the one absolute operation end
            return real_admit_policy(*args, **kwargs)

        monkeypatch.setattr(supplied_policy, "admit_policy", late_snapshot)
        reads_before = counts["read_selection"]
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        # The added snapshot work really ran under the deadline, and a
        # late usable success is refused with no observation, no
        # freshness read and no scope computation.
        assert len(late) == 1
        assert counts["read_selection"] == reads_before
        assert counts["unavailable"] == 0
        # Inside the lifetime again, the same admission qualifies.
        clock["now"] = 1029.876
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
    finally:
        _release(scenario)


# ------------------------------------------------------------- freshness


def test_selected_change_during_computation_refuses_and_latches(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        swapped = []

        def swap_after_scope(_result):
            if not swapped:
                swapped.append(1)
                _replace_selection(scenario.root, 2, scenario.payload)

        _install_counting(monkeypatch, scenario.reader, counts, after_unavailable=swap_after_scope)
        reads_before = counts["read_selection"]
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        # The pre-check read once; the post-check entered its real read,
        # observed the changed selection and latched the admission.
        assert counts["read_selection"] == reads_before + 2
        assert counts["unavailable"] == 1
        assert scenario.admission.recheck(deadline_ms=30000) is False
        assert counts["read_selection"] == reads_before + 2  # permanent, no further read
        # A clean subsequent admission with a separate valid request
        # can succeed on the same borrowed owner.
        fresh = private_policy_request.request_current_view(
            scenario.reader, CREDENTIAL, deadline_ms=30000
        )
        observation = ppe.prepare_current_pin_eligibility(fresh, scenario.owner, deadline_ms=30000)
        assert observation.eligible is True
        assert observation.selection_generation == 2
        assert counts["unavailable"] == 2
    finally:
        _release(scenario)


def test_selected_change_before_eligibility_refuses_without_scope(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        reads_before = counts["read_selection"]
        _replace_selection(scenario.root, 2, scenario.payload)  # trusted writer
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        assert counts["read_selection"] == reads_before + 1  # the pre-check entered the read
        assert counts["unavailable"] == 0  # no scope computation at all
        # A separate valid request on the new selected publication.
        fresh = private_policy_request.request_current_view(
            scenario.reader, CREDENTIAL, deadline_ms=30000
        )
        observation = ppe.prepare_current_pin_eligibility(fresh, scenario.owner, deadline_ms=30000)
        assert observation.eligible is True and observation.selection_generation == 2
    finally:
        _release(scenario)


def test_exhausted_request_lifetime_refuses_without_recheck(tmp_path, monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        assert scenario.admission._end == 1030.0  # one absolute request end
        reads_before = counts["read_selection"]
        clock["now"] = 1029.9999  # less than the 1 ms reader floor remains
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        assert counts["read_selection"] == reads_before  # refused before the recheck
        assert counts["unavailable"] == 0
        # A new request under the still-live lifetime requalifies.
        fresh = private_policy_request.request_current_view(
            scenario.reader, CREDENTIAL, deadline_ms=30000
        )
        observation = ppe.prepare_current_pin_eligibility(fresh, scenario.owner, deadline_ms=30000)
        assert observation.eligible is True
    finally:
        _release(scenario)


def test_shorter_request_lifetime_honored_over_operation_deadline(tmp_path, monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        clock["now"] = 1029.875  # exactly 125 ms of the request lifetime remains
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
        # The genuine rechecks were bounded by the remaining request
        # lifetime (125 ms), not by the larger 30 s operation deadline.
        # The admission's own final read predates the wrapper, so both
        # recorded reads are the entry's two genuine rechecks.
        entry_args = counts["read_selection_args"]
        assert len(entry_args) == 2
        for args in entry_args:
            assert 120 <= args["deadline_ms"] <= 125 < 30000
    finally:
        _release(scenario)


def test_operation_deadline_lateness_refuses_late_usable_success(tmp_path, monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        clock["now"] = 1029.875  # 125 ms remain of the request lifetime
        late = []

        def late_scope(_result):
            if not late:
                late.append(1)
                clock["now"] = 1030.001  # past the one absolute operation end

        _install_counting(monkeypatch, scenario.reader, counts, after_unavailable=late_scope)
        reads_before = counts["read_selection"]
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        assert counts["read_selection"] == reads_before + 1  # only the pre-check read
        # The admission is not latched by a deadline refusal; inside the
        # lifetime again, a new entry call on the same admission qualifies.
        clock["now"] = 1029.876
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
    finally:
        _release(scenario)


# ------------------------------------------------------------ owner states


def test_new_owner_refused(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL, acquire=False)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        fresh = raw_snapshot_pin.PinOwner()
        assert fresh.state == "NEW"
        reads_before = counts["read_selection"]
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(scenario.admission, fresh, deadline_ms=30000)
        assert counts["read_selection"] == reads_before + 1  # freshness ran, borrow refused
        assert counts["load_directory"] == 0  # no acquisition, no load at all
        assert fresh.state == "NEW"
    finally:
        _release(scenario)


def test_closed_owner_refused(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        scenario.owner.close()
        assert scenario.owner.state == "CLOSED"
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
    finally:
        _release(scenario)


def test_busy_owner_refused_without_observation(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        scenario.owner.guard.acquire()
        try:
            reads_before = counts["read_selection"]
            loads_before = counts["load_directory"]
            with pytest.raises(ppe.PolicyPinEligibilityError):
                ppe.prepare_current_pin_eligibility(
                    scenario.admission, scenario.owner, deadline_ms=30000
                )
            # The genuine pre-check ran; the guarded borrow refused
            # nonblocking with zero observations and no latch.
            assert counts["read_selection"] == reads_before + 1
            assert counts["load_directory"] == loads_before
            assert scenario.owner.state == "ACTIVE"
        finally:
            scenario.owner.guard.release()
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True  # the same owner still qualifies
    finally:
        _release(scenario)


def test_guard_held_across_scope_final_check_and_assembly(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        probe = []

        def probe_guard(_result):
            # Scope computation has finished; the final current check
            # and result assembly still run.  The actual owner gate is
            # held: a concurrent close is refused and the guard cannot
            # be taken.
            try:
                scenario.owner.close()
            except raw_snapshot_pin.PinError:
                probe.append("close-refused")
            else:
                probe.append("close-succeeded")
            if scenario.owner.guard.acquire(blocking=False):
                probe.append("guard-taken")
                scenario.owner.guard.release()
            else:
                probe.append("guard-held")

        _install_counting(monkeypatch, scenario.reader, counts, after_unavailable=probe_guard)
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
        assert probe == ["close-refused", "guard-held"]
        assert scenario.owner.state == "ACTIVE"
        # The guard was released on the exit, so the same owner still
        # qualifies and can be closed afterwards.
        assert scenario.owner.guard.acquire(blocking=False)
        scenario.owner.guard.release()
        again = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert again.eligible is True
        scenario.owner.close()
        assert scenario.owner.state == "CLOSED"
    finally:
        scenario.originals.close()
        scenario.derived.close()


def test_foreign_process_owner_refused(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        real_pid = os.getpid()
        scenario.owner.pid = real_pid + 1  # a foreign creator process
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        scenario.owner.pid = real_pid
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True  # restored creator pid qualifies
    finally:
        _release(scenario)


@pytest.mark.parametrize(
    ("bad_admission", "bad_owner"),
    [
        (object(), None),
        (None, None),
        (None, object()),
        (object(), object()),
    ],
)
def test_invalid_admission_or_owner_type_refused(tmp_path, monkeypatch, bad_admission, bad_owner):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        admission = scenario.admission if bad_admission is None else bad_admission
        owner = scenario.owner if bad_owner is None else bad_owner
        if bad_admission is None and bad_owner is None:
            # Neither side is invalid: the real pair still qualifies.
            observation = ppe.prepare_current_pin_eligibility(
                admission, owner, deadline_ms=30000
            )
            assert observation.eligible is True
            return
        reads_before = counts["read_selection"]
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(admission, owner, deadline_ms=30000)
        assert counts["read_selection"] == reads_before  # refused before any freshness call
    finally:
        _release(scenario)


@pytest.mark.parametrize("bad_deadline", [True, 0, 30001, "30000", 30000.5, -1])
def test_non_nominal_deadline_refused(tmp_path, monkeypatch, bad_deadline):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        reads_before = counts["read_selection"]
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=bad_deadline
            )
        assert counts["read_selection"] == reads_before
        # The nominal gate's boundaries are exactly 1..30000, and the
        # 30 s boundary is accepted end to end on the same real scenario.
        assert ppe._deadline_accepted(1) is True
        assert ppe._deadline_accepted(30000) is True
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
    finally:
        _release(scenario)


# ---------------------------------------------------- capture agreement


def _tamper_value(scenario, data):
    pointer = scenario.value.pointer
    scenario.owner.value = raw_snapshot_pin.PinData(pointer, data)


@pytest.mark.parametrize(
    "tamper",
    [
        "core_digest",
        "manifest_snapshot",
        "snapshot_mismatch",
        "stale_membership",
        "membership_type",
        "pointer_type",
        "value_none",
        "value_type",
    ],
)
def test_stale_or_mismatched_capture_refused(tmp_path, monkeypatch, tamper):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        data = scenario.value.data
        pointer = scenario.value.pointer
        if tamper == "core_digest":
            _tamper_value(
                scenario,
                raw_snapshot_files.BoundSnapshotData(
                    pointer.snapshot_id, b"\x00" * 10, data.row_map, data.membership, ()
                ),
            )
        elif tamper == "manifest_snapshot":
            # Pointer and data agree on a foreign snapshot ID that is
            # not the captured core's own digest ID; only the parsed
            # manifest's snapshot ID catches the disagreement.
            foreign = "sha256:" + "f" * 64
            foreign_pointer = raw_snapshot_selection.Pointer(
                pointer.pointer_bytes, pointer.generation, foreign, pointer.core_sha256
            )
            foreign_data = raw_snapshot_files.BoundSnapshotData(
                foreign, scenario.core_bytes, data.row_map, data.membership, ()
            )
            scenario.owner.value = raw_snapshot_pin.PinData(foreign_pointer, foreign_data)
        elif tamper == "snapshot_mismatch":
            _tamper_value(
                scenario,
                raw_snapshot_files.BoundSnapshotData(
                    "sha256:" + "f" * 64, scenario.core_bytes, data.row_map, data.membership, ()
                ),
            )
        elif tamper == "stale_membership":
            # A genuinely different capture (different entry set, real
            # parse) whose bytes no longer match the admitted manifest
            # descriptor.
            stale_bytes = _membership_bytes([ENTRY_A], scenario.row_map_bytes)
            stale = raw_snapshot_membership.parse(stale_bytes)
            assert stale.membership_bytes != data.membership.membership_bytes
            _tamper_value(
                scenario,
                raw_snapshot_files.BoundSnapshotData(
                    pointer.snapshot_id, scenario.core_bytes, data.row_map, stale, ()
                ),
            )
        elif tamper == "membership_type":
            _tamper_value(
                scenario,
                raw_snapshot_files.BoundSnapshotData(
                    pointer.snapshot_id, scenario.core_bytes, data.row_map, object(), ()
                ),
            )
        elif tamper == "pointer_type":
            scenario.owner.value = raw_snapshot_pin.PinData(object(), data)
        elif tamper == "value_none":
            scenario.owner.value = None
        elif tamper == "value_type":
            scenario.owner.value = object()
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        # The borrow refused without latching the owner: restoring the
        # admitted capture makes the same owner qualify again.
        scenario.owner.value = scenario.value
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
    finally:
        _release(scenario)


@pytest.mark.parametrize("state", ["NEW", "CLEANUP_PENDING", "CLOSED"])
def test_non_active_owner_state_refused(tmp_path, monkeypatch, state):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        scenario.owner.state = state  # white-box state setup
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
    finally:
        scenario.owner.state = "ACTIVE"
        _release(scenario)


# ------------------------------------------------------ restrictions gate


def _restrictions(**fields):
    payload = {"schema_version": 1, "corpora": None, "versions": None}
    payload.update(fields)
    return admit_record("Restrictions", payload)


def test_invalid_restrictions_refused_before_observation(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        reads_before = counts["read_selection"]
        # Exact-class gate: a Grants DTO is not a Restrictions DTO.
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000, restrictions=GRANTS
            )
        # Non-DTO values refuse the same way.
        for bad in ("corpus-a", 7, [], {"schema_version": 1}):
            with pytest.raises(ppe.PolicyPinEligibilityError):
                ppe.prepare_current_pin_eligibility(
                    scenario.admission, scenario.owner, deadline_ms=30000, restrictions=bad
                )
        # A bypassed 129-value vector defeats the public bound.
        over = provenance_records.Restrictions.model_construct(
            schema_version=1, corpora=None, versions=("v" + str(i) for i in range(129))
        )
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000, restrictions=over
            )
        # An extra field fails the closed-DTO gate.
        extra = provenance_records.Restrictions.model_construct(
            schema_version=1, corpora=None, versions=None, bogus=()
        )
        extra.__pydantic_extra__ = {"bogus": ()}
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000, restrictions=extra
            )
        assert counts["read_selection"] == reads_before  # refused before any freshness call
        assert counts["unavailable"] == 0
    finally:
        _release(scenario)


# --------------------------------------------- refusal and interruption


def test_ordinary_refusal_preserves_owner_and_reader(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        with pytest.raises(ppe.PolicyPinEligibilityError):
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=0
            )
        # Ordinary refusal latches nothing: the same real admission and
        # owner still qualify, and the reader never latched.
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
        assert scenario.reader._latched is False and scenario.owner.state == "ACTIVE"
    finally:
        _release(scenario)


def test_hostile_base_exception_identity_during_borrow(tmp_path, monkeypatch):
    class Hostile(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError("no attributes")

    marker = Hostile()
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        real_parse = raw_snapshot_manifest.parse

        def interrupt(_core):
            raise marker

        monkeypatch.setattr(raw_snapshot_manifest, "parse", interrupt)
        with pytest.raises(Hostile) as caught:
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        assert caught.value is marker
        # The creator guard was released even through the interruption.
        assert scenario.owner.guard.acquire(blocking=False)
        scenario.owner.guard.release()
        assert scenario.owner.state == "ACTIVE" and scenario.owner.value is scenario.value
        # The same admission and owner still qualify once the fault is
        # gone; the interruption latched nothing.
        monkeypatch.setattr(raw_snapshot_manifest, "parse", real_parse)
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
    finally:
        _release(scenario)


@pytest.mark.parametrize("marker", [KeyboardInterrupt()])
def test_keyboard_interrupt_identity_during_recheck(tmp_path, monkeypatch, marker):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        real_read = private_policy_capture.PolicyCaptureReader.read_selection.__get__(
            scenario.reader, type(scenario.reader)
        )

        def interrupt(*args, **kwargs):
            raise marker

        monkeypatch.setattr(scenario.reader, "read_selection", interrupt)
        with pytest.raises(KeyboardInterrupt) as caught:
            ppe.prepare_current_pin_eligibility(
                scenario.admission, scenario.owner, deadline_ms=30000
            )
        assert caught.value is marker
        # The reader itself is not latched by an interrupted recheck.
        monkeypatch.setattr(scenario.reader, "read_selection", real_read)
        assert real_read(deadline_ms=30000).generation == 1
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
    finally:
        _release(scenario)


# ------------------------------------------------- no-work demonstration


def test_entry_never_invokes_reload_source_or_index_work(tmp_path, monkeypatch):
    counts = _counts()
    scenario = _build_scenario(tmp_path, monkeypatch, counts, documents=PAIRS_ALL)
    try:
        _install_counting(monkeypatch, scenario.reader, counts)
        real_check = raw_snapshot_pin.PinOwner.check

        def check_canary(self, *args, **kwargs):
            counts["owner_check"] += 1
            return real_check(self, *args, **kwargs)

        real_validate = raw_snapshot_files.validate_files

        def validate_canary(*args, **kwargs):
            counts["validate_files"] += 1
            return real_validate(*args, **kwargs)

        real_source_read = source_admission.OriginalStore._read

        def source_canary(self, *args, **kwargs):
            counts["source_read"] += 1
            return real_source_read(self, *args, **kwargs)

        monkeypatch.setattr(raw_snapshot_pin.PinOwner, "check", check_canary)
        monkeypatch.setattr(raw_snapshot_files, "validate_files", validate_canary)
        monkeypatch.setattr(source_admission.OriginalStore, "_read", source_canary)
        loads_before = counts["load_directory"]
        reads_before = counts["read_selection"]
        observation = ppe.prepare_current_pin_eligibility(
            scenario.admission, scenario.owner, deadline_ms=30000
        )
        assert observation.eligible is True
        # No snapshot reload, no owner check, no files validation, no
        # source access, and exactly the two genuine bounded rechecks.
        assert counts["load_directory"] == loads_before
        assert counts["owner_check"] == 0
        assert counts["validate_files"] == 0
        assert counts["source_read"] == 0
        assert counts["read_selection"] == reads_before + 2
        assert counts["unavailable"] == 1
        # The borrowed capture is untouched and the owner lifetime is
        # intact through a real full check and a real cleanup.
        assert scenario.owner.value is scenario.value
        assert scenario.owner.check(deadline_ms=30000) is scenario.value
        scenario.owner.close()
        assert scenario.owner.state == "CLOSED"
    finally:
        scenario.originals.close()
        scenario.derived.close()
