"""Pure unit tests for supplied_policy_eligibility
(PAR-009-SUPPLIED-MEMBERSHIP-ELIGIBILITY-A).

Synthetic fixed fixtures only: real synthetic membership captures with
canonical source hashes and genuine parse, and genuine typed policies via the
factory. No network, credentials, models, GPU, filesystem or source runtime.
Every expected result is derived from actual parsed entries and parsed
capture fields, never from handwritten partition suppression. The
20000/64/128 boundary witnesses are finite pure-unit evidence, never
source/snapshot capacity evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import (
    provenance_records,
    raw_snapshot_membership,
    schema,
    supplied_policy,
)
from slaif_raggedized_helper import supplied_policy_eligibility as spe
from slaif_raggedized_helper.qualification import parity_io

Membership = raw_snapshot_membership.Membership
Entry = raw_snapshot_membership.Entry


def _assert_module_origins() -> None:
    # Derived from this test file's resolved physical location
    # (tests/unit/test_supplied_policy_eligibility.py -> worktree root / src),
    # so a canonical transfer or CI keeps the same fail-closed origin check.
    src = Path(__file__).resolve().parents[2] / "src"
    for module in (spe, supplied_policy, raw_snapshot_membership, provenance_records, parity_io):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(src), "module origin outside assigned worktree"


_assert_module_origins()


# ---------------------------------------------------------------- fixtures


def _hex(value: int) -> str:
    return format(value, "064x")


def _revision(index: int) -> str:
    return "sha256:" + _hex(0x1000 + index)


def _enc(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
        "ascii"
    )


def _scope_map(document_id, revision, corpus="corpus", version="v1", labels=("a",)):
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


def _entry(
    document_id, revision, bundle, *, corpus="corpus", version="v1", labels=("a",), ordinals=()
):
    scope = _scope_map(document_id, revision, corpus, version, labels)
    return dict(
        revision_id=revision,
        extraction_id="sha256:" + _hex(0x2000 + bundle),
        bundle_container_id=_hex(0x3000 + bundle),
        bundle_metadata_sha256=_hex(0x4000 + bundle),
        chunk_policy_fingerprint=_hex(0x5000 + bundle),
        source_scope_sha256=schema.fingerprint(
            {"kind": "embedding-source-scope-v1", "scope": scope}
        )[7:],
        partition_id=schema.fingerprint(
            {"schema": 1, "corpus": corpus, "version": version, "labels": list(labels)}
        ),
        scope=scope,
        ordinals=list(ordinals),
    )


def _membership_bytes(entries, row_count, withdrawn=()):
    return _enc(
        dict(
            schema=1,
            kind="slaif-raw-source-membership-v1",
            row_map_sha256=_hex(0x6000),
            row_count=row_count,
            entries=entries,
            withdrawn_revisions=list(withdrawn),
        )
    )


def _parse(entries, row_count, withdrawn=()):
    return raw_snapshot_membership.parse(_membership_bytes(entries, row_count, withdrawn))


def _policy_from_pairs(rules):
    """Genuine factory policy; each rule is (document_id, pair, pair, ...)."""
    documents = tuple(
        supplied_policy.DocumentRule(document_id, tuple(sorted(pairs)))
        for document_id, *pairs in sorted(rules, key=lambda rule: rule[0])
    )
    return supplied_policy.admit_policy((), documents)


def _matching_policy(parsed):
    grouped = {}
    for entry in parsed.entries:
        document_id = provenance_records.admit_record("Scope", entry.scope_bytes).document_id
        grouped.setdefault(document_id, []).append((entry.revision_id, entry.source_scope_sha256))
    return _policy_from_pairs([(document_id, *pairs) for document_id, pairs in grouped.items()])


# ---------------------------------------------------------------- positive


def test_positive_exact_including_zero_row_entry():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0, 1))
    e1 = _entry("doc-b", _revision(1), 1, labels=("b",))
    e2 = _entry("doc-c", _revision(2), 2, labels=("c",))  # admitted zero-row entry
    parsed = _parse([e0, e1, e2], row_count=2)
    # Nonvacuity: the capture really has three parsed entries (one zero-row)
    # on three distinct partitions, and the policy really has one rule each.
    assert [len(entry.ordinals) for entry in parsed.entries] == [2, 0, 0]
    partitions = {entry.partition_id for entry in parsed.entries}
    assert len(partitions) == 3
    policy = _matching_policy(parsed)
    assert len(policy.documents) == 3
    assert all(len(rule.admitted) == 1 for rule in policy.documents)
    assert spe.unavailable_partitions(policy, parsed) == ()


def test_positive_boundary_sixty_four_pairs_in_one_rule():
    entries = [
        _entry("doc-a", _revision(index), index, ordinals=tuple(range(64)) if index == 0 else ())
        for index in range(64)
    ]
    parsed = _parse(entries, row_count=64)
    policy = _matching_policy(parsed)
    # Boundary context: the factory's exact per-document pair limit, positive.
    assert len(policy.documents) == 1 and len(policy.documents[0].admitted) == 64
    assert spe.unavailable_partitions(policy, parsed) == ()


# ---------------------------------------------------------------- denial


def test_scope_hash_change_denies_entry():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    e1 = _entry("doc-a", _revision(1), 1, labels=("b",))
    parsed = _parse([e0, e1], row_count=1)
    changed = "0" if parsed.entries[1].source_scope_sha256[0] != "0" else "1"
    changed_hash = changed + parsed.entries[1].source_scope_sha256[1:]
    assert changed_hash != parsed.entries[1].source_scope_sha256
    policy = _policy_from_pairs(
        [
            (
                "doc-a",
                (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256),
                (parsed.entries[1].revision_id, changed_hash),
            )
        ]
    )
    assert spe.unavailable_partitions(policy, parsed) == (parsed.entries[1].partition_id,)


def test_missing_rule_denies_partition():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    e1 = _entry("doc-z", _revision(1), 1, labels=("b",))
    parsed = _parse([e0, e1], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    assert spe.unavailable_partitions(policy, parsed) == (parsed.entries[1].partition_id,)


def test_emptied_rule_denies_partition():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = supplied_policy.admit_policy((), (supplied_policy.DocumentRule("doc-a", ()),))
    assert policy.documents[0].admitted == ()
    assert spe.unavailable_partitions(policy, parsed) == (parsed.entries[0].partition_id,)


def test_mixed_partition_denial_is_unique_and_sorted():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))  # P_a admitted
    e1 = _entry("doc-b", _revision(1), 1, labels=("b",))  # P_b admitted
    e2 = _entry("doc-a", _revision(2), 2, ordinals=(1,))  # P_a again, pair not admitted
    parsed = _parse([e0, e1, e2], row_count=2)
    assert parsed.entries[0].partition_id == parsed.entries[2].partition_id
    assert parsed.entries[1].partition_id != parsed.entries[0].partition_id
    policy = _policy_from_pairs(
        [
            ("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256)),
            ("doc-b", (parsed.entries[1].revision_id, parsed.entries[1].source_scope_sha256)),
        ]
    )
    denied = {parsed.entries[0].partition_id, parsed.entries[2].partition_id}
    result = spe.unavailable_partitions(policy, parsed)
    assert result == tuple(sorted(denied))
    assert len(result) == 1


def test_unaffected_scope_remains_available():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = _policy_from_pairs(
        [
            ("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256)),
            ("doc-z", (_revision(9), "f" * 64)),
        ]
    )
    assert spe.unavailable_partitions(policy, parsed) == ()


def test_clean_same_partition_replacement():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))  # P_a
    e1 = _entry("doc-a", _revision(1), 1, ordinals=(1,))  # same P_a, different scope hash
    parsed = _parse([e0, e1], row_count=2)
    assert parsed.entries[0].partition_id == parsed.entries[1].partition_id
    assert parsed.entries[0].source_scope_sha256 != parsed.entries[1].source_scope_sha256
    before = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    assert spe.unavailable_partitions(before, parsed) == (parsed.entries[0].partition_id,)
    after = _policy_from_pairs(
        [
            (
                "doc-a",
                (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256),
                (parsed.entries[1].revision_id, parsed.entries[1].source_scope_sha256),
            )
        ]
    )
    assert spe.unavailable_partitions(after, parsed) == ()


def test_old_data_again_under_unchanged_policy():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    e1 = _entry("doc-a", _revision(1), 1, labels=("b",))
    parsed = _parse([e0, e1], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    first = spe.unavailable_partitions(policy, parsed)
    second = spe.unavailable_partitions(policy, parsed)
    assert first == (parsed.entries[1].partition_id,)
    assert second == first


# ------------------------------------------------- nominal DTO and errors


def test_nominal_inconsistent_inputs():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )

    def reject(calling):
        with pytest.raises(spe.PolicyEligibilityError):
            calling()

    # DTO field inconsistent with its own re-admitted capture bytes.
    tampered_row_count = Membership(
        parsed.membership_bytes,
        parsed.sha256,
        parsed.row_map_sha256,
        parsed.row_count + 1,
        parsed.entries,
        parsed.withdrawn_revisions,
    )
    reject(lambda: spe.unavailable_partitions(policy, tampered_row_count))
    foreign = Entry(
        "sha256:" + "9" * 64,
        parsed.entries[0].extraction_id,
        parsed.entries[0].bundle_container_id,
        parsed.entries[0].bundle_metadata_sha256,
        parsed.entries[0].chunk_policy_fingerprint,
        parsed.entries[0].source_scope_sha256,
        parsed.entries[0].partition_id,
        parsed.entries[0].scope_bytes,
        parsed.entries[0].ordinals,
    )
    tampered_entries = Membership(
        parsed.membership_bytes,
        parsed.sha256,
        parsed.row_map_sha256,
        parsed.row_count,
        (foreign,),
        parsed.withdrawn_revisions,
    )
    reject(lambda: spe.unavailable_partitions(policy, tampered_entries))
    # Exact class: not a policy at all / not the exact membership class.
    reject(lambda: spe.unavailable_partitions(object(), parsed))
    reject(lambda: spe.unavailable_partitions(policy, object()))

    class NominalSubclass(Membership):
        pass

    subclass = NominalSubclass(
        parsed.membership_bytes,
        parsed.sha256,
        parsed.row_map_sha256,
        parsed.row_count,
        parsed.entries,
        parsed.withdrawn_revisions,
    )
    reject(lambda: spe.unavailable_partitions(policy, subclass))
    # membership_bytes of the wrong type passes the nominal constructor.
    not_bytes = Membership(
        "not-bytes",
        parsed.sha256,
        parsed.row_map_sha256,
        parsed.row_count,
        parsed.entries,
        parsed.withdrawn_revisions,
    )
    reject(lambda: spe.unavailable_partitions(policy, not_bytes))


def test_bool_row_count_rejected():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    # Genuine positive pair: the re-admitted int row count 1 is accepted.
    assert type(parsed.row_count) is int and parsed.row_count == 1
    assert spe.unavailable_partitions(policy, parsed) == ()
    # Malformed pair: True equals 1 under scalar equality and must not pass.
    bool_row_count = Membership(
        parsed.membership_bytes,
        parsed.sha256,
        parsed.row_map_sha256,
        True,
        parsed.entries,
        parsed.withdrawn_revisions,
    )
    with pytest.raises(spe.PolicyEligibilityError):
        spe.unavailable_partitions(policy, bool_row_count)


def test_bool_ordinal_rejected():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0, 1))
    parsed = _parse([e0], row_count=2)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    # Genuine positive pair: the re-admitted int ordinals are accepted.
    assert spe.unavailable_partitions(policy, parsed) == ()
    # Malformed pair: True equals 1 under natural dataclass equality and must
    # not pass the exact int ordinal contract.
    bool_ordinal = Entry(
        parsed.entries[0].revision_id,
        parsed.entries[0].extraction_id,
        parsed.entries[0].bundle_container_id,
        parsed.entries[0].bundle_metadata_sha256,
        parsed.entries[0].chunk_policy_fingerprint,
        parsed.entries[0].source_scope_sha256,
        parsed.entries[0].partition_id,
        parsed.entries[0].scope_bytes,
        (True, 1),
    )
    malformed = Membership(
        parsed.membership_bytes,
        parsed.sha256,
        parsed.row_map_sha256,
        parsed.row_count,
        (bool_ordinal,),
        parsed.withdrawn_revisions,
    )
    with pytest.raises(spe.PolicyEligibilityError):
        spe.unavailable_partitions(policy, malformed)


def test_foreign_field_equality_hook_never_invoked():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    calls = []

    class Sentinel:
        def __eq__(self, other):
            calls.append("eq")
            return True

    # DTO-level sentinel: the exact str contract must reject it before the
    # comparison that would reach the foreign equality hook.
    dto_sentinel = Membership(
        parsed.membership_bytes,
        Sentinel(),
        parsed.row_map_sha256,
        parsed.row_count,
        parsed.entries,
        parsed.withdrawn_revisions,
    )
    with pytest.raises(spe.PolicyEligibilityError):
        spe.unavailable_partitions(policy, dto_sentinel)
    assert calls == []
    # Entry-level sentinel: the exact str Entry-field contract must reject it
    # before any dataclass field comparison reaches the hook.
    entry_sentinel = Entry(
        parsed.entries[0].revision_id,
        parsed.entries[0].extraction_id,
        parsed.entries[0].bundle_container_id,
        parsed.entries[0].bundle_metadata_sha256,
        parsed.entries[0].chunk_policy_fingerprint,
        parsed.entries[0].source_scope_sha256,
        Sentinel(),
        parsed.entries[0].scope_bytes,
        parsed.entries[0].ordinals,
    )
    entry_malformed = Membership(
        parsed.membership_bytes,
        parsed.sha256,
        parsed.row_map_sha256,
        parsed.row_count,
        (entry_sentinel,),
        parsed.withdrawn_revisions,
    )
    with pytest.raises(spe.PolicyEligibilityError):
        spe.unavailable_partitions(policy, entry_malformed)
    assert calls == []


def test_error_hygiene_fixed_message_no_cause_no_context():
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    bad_inputs = (
        (object(), parsed),
        (policy, object()),
        (policy, Membership(b"[" * (parity_io.MAX_DEPTH + 1), "0" * 64, "0" * 64, 0, (), ())),
        (
            policy,
            Membership(b" " * (raw_snapshot_membership._LIMIT + 1), "0" * 64, "0" * 64, 0, (), ()),
        ),
        (policy, Membership(b"\xff", "0" * 64, "0" * 64, 0, (), ())),
    )
    for given_policy, given_membership in bad_inputs:
        with pytest.raises(spe.PolicyEligibilityError) as excinfo:
            spe.unavailable_partitions(given_policy, given_membership)
        error = excinfo.value
        assert isinstance(error, ValueError)
        assert error.args == (spe._POLICY_ELIGIBILITY_ERROR_MESSAGE,)
        assert error.__cause__ is None
        assert error.__context__ is None


def test_depth_guard_fires_before_membership_parser(monkeypatch):
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    calls = []
    real_parse = raw_snapshot_membership.parse

    def spy(*args, **kwargs):
        calls.append(args)
        return real_parse(*args, **kwargs)

    monkeypatch.setattr(raw_snapshot_membership, "parse", spy)
    deep = Membership(b"[" * (parity_io.MAX_DEPTH + 1), "0" * 64, "0" * 64, 0, (), ())
    with pytest.raises(spe.PolicyEligibilityError):
        spe.unavailable_partitions(policy, deep)
    assert not calls


def test_depth_check_boundary_witness():
    parity_io._depth_check("[" * parity_io.MAX_DEPTH)
    with pytest.raises(parity_io.Refusal):
        parity_io._depth_check("[" * (parity_io.MAX_DEPTH + 1))


def test_byte_bound_rejects_before_depth_and_parser(monkeypatch):
    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    calls = []
    real_parse = raw_snapshot_membership.parse

    def spy(*args, **kwargs):
        calls.append(args)
        return real_parse(*args, **kwargs)

    monkeypatch.setattr(raw_snapshot_membership, "parse", spy)
    over = Membership(b" " * (raw_snapshot_membership._LIMIT + 1), "0" * 64, "0" * 64, 0, (), ())
    with pytest.raises(spe.PolicyEligibilityError):
        spe.unavailable_partitions(policy, over)
    assert not calls


def test_interrupt_identity_propagates(monkeypatch):
    class Stop(BaseException):
        pass

    def interrupt(*args, **kwargs):
        raise Stop()

    e0 = _entry("doc-a", _revision(0), 0, ordinals=(0,))
    parsed = _parse([e0], row_count=1)
    policy = _policy_from_pairs(
        [("doc-a", (parsed.entries[0].revision_id, parsed.entries[0].source_scope_sha256))]
    )
    monkeypatch.setattr(raw_snapshot_membership, "parse", interrupt)
    with pytest.raises(Stop):
        spe.unavailable_partitions(policy, parsed)
