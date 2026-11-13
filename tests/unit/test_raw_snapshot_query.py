"""Pure typed mocks for the private pinned-query boundary; no native execution."""

from dataclasses import replace
from types import SimpleNamespace as NS

import pytest
from slaif_raggedized_helper import raw_snapshot_query as q
from slaif_raggedized_helper import raw_snapshot_membership as membership

CORE = (
    b'{"embedding":{"definition_fingerprint":"sha256:2222222222222222222222222222222222222222222222222222222222222222",'
    b'"query_execution_fingerprint":"4444444444444444444444444444444444444444444444444444444444444444",'
    b'"query_policy_fingerprint":"3333333333333333333333333333333333333333333333333333333333333333",'
    b'"space_id":"1111111111111111111111111111111111111111111111111111111111111111"}}'
)
SHA = "4e6dc50f7677623ca9f2e581dced9be9d59d7c766354544b57d572f368744fa6"
PAYLOAD_SHA = "ad7facb2586fc6e966c004d7d1d16b024f5805ff7cb47c7a85dabd8b48892ca7"
QUESTION_SHA = "1f5087db919ced5c123c7f507d3fcce818cb0cf6e77c2f95a8a35e951e03fdb9"
PART = "sha256:" + "a" * 64


@pytest.fixture
def context(monkeypatch):
    originals = object.__new__(q.OriginalStore)
    derived = object.__new__(q.derived_store.Store)
    owner = q.pin.PinOwner()
    owner.state, owner.op, owner.originals, owner.derived = (
        "ACTIVE",
        NS(path="/owned"),
        originals,
        derived,
    )
    encoder = object.__new__(q.query_embedding.ResidentQueryEncoder)
    encoder._state = "open"
    scope = q.records.Scope(
        schema_version=1,
        document_id="doc",
        revision_id="rev",
        corpus="c",
        version="v",
        labels=(),
        processing_approved=True,
        redistribution_rights="allowed",
    )
    entry = membership.Entry(
        "rev",
        "extract",
        "bundle",
        "b" * 64,
        "c" * 64,
        "d" * 64,
        PART,
        scope.model_dump_json().encode(),
        (0,),
    )
    pointer = q.selection.Pointer(b"old", 1, "sha256:" + SHA, SHA)
    members = membership.Membership(b"", "0" * 64, "0" * 64, 1, (entry,), ())
    data = q.files.BoundSnapshotData(pointer.snapshot_id, CORE, None, members, ())
    captured = q.pin.PinData(pointer, data)
    monkeypatch.setattr(q.pin.PinOwner, "check", lambda self, **kw: captured)
    monkeypatch.setattr(q.manifest, "parse", lambda value: NS(snapshot_id=pointer.snapshot_id))
    embedding = q.query_embedding.QueryEmbedding(
        bytes(4096),
        PAYLOAD_SHA,
        "1" * 64,
        "sha256:" + "2" * 64,
        "sha256:" + "9" * 64,
        b"unused",
        "sha256:" + "4" * 64,
        "3" * 64,
    )
    grants = q.records.Grants(schema_version=1, corpora=("c",), versions=("v",), labels=())
    authority = q.QueryAuthority("e" * 64, grants, None, ())
    calls = []

    def encode(self, text):
        calls.append(("encode", text))
        return embedding

    monkeypatch.setattr(q.query_embedding.ResidentQueryEncoder, "encode_query", encode)
    auth_hash = "717afe57679c385c90f2f4782801d9326f4eb8594d6de9831fca3a1ec8547d2e"

    def search(*args, **kwargs):
        calls.append(("search", args, kwargs))
        return q.hybrid.HybridResult(
            pointer.snapshot_id,
            "catalog",
            "query",
            QUESTION_SHA,
            PAYLOAD_SHA,
            auth_hash,
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
            NS(trace=None),
            NS(trace=None),
            NS(),
        )

    monkeypatch.setattr(q.hybrid, "search", search)

    def provider(boundary, admission):
        calls.append((boundary, admission))
        return authority

    return NS(
        args=(originals, derived, "/owned", owner, encoder, "question", provider),
        owner=owner,
        encoder=encoder,
        authority=authority,
        embedding=embedding,
        calls=calls,
        captured=captured,
        monkeypatch=monkeypatch,
    )


def test_healthy_borrowed_old_pin(context):
    c = context
    result = q.search_pinned_data(*c.args)
    assert [x[0] for x in c.calls] == [
        "before_encode",
        "encode",
        "before_retrieval",
        "search",
        "before_return",
    ]
    assert c.calls[0][1] is c.calls[2][1] is c.calls[4][1]
    assert c.calls[3][1][3:6] == ("sha256:" + SHA, "question", bytes(4096))
    assert c.calls[3][2]["query_execution_fingerprint"] == "4" * 64
    assert (result.snapshot_id, result.pointer_bytes, result.question_sha256) == (
        "sha256:" + SHA,
        b"old",
        QUESTION_SHA,
    )
    assert c.owner.state == "ACTIVE" and c.encoder._state == "open"


@pytest.mark.parametrize(
    "field,value",
    [
        ("payload_sha256", "0" * 64),
        ("payload", b""),
        ("execution_fingerprint", "4" * 64),
        ("execution_fingerprint", "sha256:" + "9" * 64),
        ("space_id", "0" * 64),
        ("definition_fingerprint", "sha256:" + "0" * 64),
        ("query_policy_id", "0" * 64),
    ],
)
def test_bad_embedding_before_search(context, field, value):
    c = context
    bad = replace(c.embedding, **{field: value})
    c.monkeypatch.setattr(q.query_embedding.ResidentQueryEncoder, "encode_query", lambda *a: bad)
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args)
    assert not any(x[0] == "search" for x in c.calls)


@pytest.mark.parametrize("boundary", ["before_retrieval", "before_return"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("epoch", "f" * 64),
        ("unavailable_partitions", (PART,)),
        ("grants", q.records.Grants(schema_version=1, corpora=(), versions=(), labels=())),
        ("restrictions", q.records.Restrictions(schema_version=1, corpora=(), versions=None)),
    ],
)
def test_changed_policy_refuses(context, boundary, field, value):
    c = context

    def provider(stage, admission):
        return replace(c.authority, **{field: value}) if stage == boundary else c.authority

    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args[:-1], provider)


def test_affected_readable_partition_before_encode(context):
    c = context
    with pytest.raises(q.ScopeUnavailableError, match="query scope unavailable"):
        q.search_pinned_data(
            *c.args[:-1], lambda *a: replace(c.authority, unavailable_partitions=(PART,))
        )
    assert not c.calls


def test_unknown_partition_and_provider_refusal(context):
    c = context
    for provider in (
        lambda *a: replace(c.authority, unavailable_partitions=("sha256:" + "b" * 64,)),
        lambda *a: None,
    ):
        with pytest.raises(q.PinnedQueryError, match="pinned query refused"):
            q.search_pinned_data(*c.args[:-1], provider)
    assert not c.calls


@pytest.mark.parametrize(
    "kwargs", [dict(trace=1), dict(k=True), dict(k=61), dict(deadline_ms=0), dict(dense_k=0)]
)
def test_cheap_admission(context, kwargs):
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*context.args, **kwargs)
    assert not context.calls


def test_nonexception_propagates(context):
    def stop(*args):
        raise SystemExit(7)

    with pytest.raises(SystemExit):
        q.search_pinned_data(*context.args[:-1], stop)


def test_denied_affected_partition_does_not_disclose(context):
    c = context
    denied = q.records.Grants(schema_version=1, corpora=(), versions=(), labels=())
    authority = replace(c.authority, grants=denied, unavailable_partitions=(PART,))

    # The hybrid producer's literal authority identity corresponds to the denied grants.
    def search(*args, **kwargs):
        c.calls.append(("search", args, kwargs))
        return q.hybrid.HybridResult(
            "sha256:" + SHA,
            "catalog",
            "query",
            QUESTION_SHA,
            PAYLOAD_SHA,
            "0bb2b22c9c2d57d4162d8d5ad387cdb366b82bb2f11a79b70732d9810d54487d",
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
            NS(trace=None),
            NS(trace=None),
            NS(),
        )

    c.monkeypatch.setattr(q.hybrid, "search", search)
    result = q.search_pinned_data(*c.args[:-1], lambda *a: authority)
    assert result.snapshot_id == "sha256:" + SHA
    assert [x[0] for x in c.calls] == ["encode", "search"]


def test_encoder_changes_policy_before_retrieval(context):
    c = context
    state = [c.authority]

    def encode(self, text):
        state[0] = replace(c.authority, epoch="f" * 64)
        return c.embedding

    c.monkeypatch.setattr(q.query_embedding.ResidentQueryEncoder, "encode_query", encode)
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args[:-1], lambda *a: state[0])
    assert not any(x[0] == "search" for x in c.calls)


def test_result_constructor_must_finish_before_deadline(context):
    c = context
    now = [0.0]
    c.monkeypatch.setattr(q.time, "monotonic", lambda: now[0])
    constructor = q.PinnedQueryResult

    def late(*args, **kwargs):
        result = constructor(*args, **kwargs)
        now[0] = 121.0
        return result

    c.monkeypatch.setattr(q, "PinnedQueryResult", late)
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args)
    assert [x[0] for x in c.calls][-1] == "before_return"


@pytest.mark.parametrize("stage", ["before_encode", "before_retrieval", "before_return"])
def test_late_provider_return_refuses(context, stage):
    c = context
    now = [0.0]
    c.monkeypatch.setattr(q.time, "monotonic", lambda: now[0])

    def provider(boundary, admission):
        if boundary == stage:
            now[0] = 121.0
        return c.authority

    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args[:-1], provider)
    if stage == "before_encode":
        assert not c.calls


def test_foreign_store_and_wrong_root_are_refused(context):
    c = context
    args = list(c.args)
    args[2] = "/other"
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*args)
    args = list(c.args)
    args[0] = object.__new__(q.OriginalStore)
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*args)
    assert not c.calls


def test_hybrid_identity_mismatch_refuses_whole_query(context):
    c = context

    def wrong(*args, **kwargs):
        return q.hybrid.HybridResult(
            "sha256:" + SHA,
            "catalog",
            "query",
            QUESTION_SHA,
            "0" * 64,
            "717afe57679c385c90f2f4782801d9326f4eb8594d6de9831fca3a1ec8547d2e",
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
            NS(trace=None),
            NS(trace=None),
            NS(),
        )

    c.monkeypatch.setattr(q.hybrid, "search", wrong)
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args)
    assert not any(x[0] == "before_return" for x in c.calls)


def test_trace_required_when_requested(context):
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*context.args, trace=True)
    assert not any(x[0] == "before_return" for x in context.calls)


def test_borrowed_pin_change_refuses_before_search(context):
    c = context
    checks = [0]

    def changed(self, **kw):
        checks[0] += 1
        if checks[0] == 3:
            return q.pin.PinData(replace(c.captured.pointer, generation=2), c.captured.data)
        return c.captured

    c.monkeypatch.setattr(q.pin.PinOwner, "check", changed)
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args)
    assert checks == [3] and not any(x[0] == "search" for x in c.calls)


@pytest.mark.parametrize("text", ["", "   ", "x" * 8193, "\ud800", 1])
def test_bad_question_before_policy(context, text):
    args = list(context.args)
    args[5] = text
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*args)
    assert not context.calls


@pytest.mark.parametrize("phase", ["pin", "encoder", "hybrid"])
def test_nested_call_late_success_refused(context, phase):
    c = context
    now = [0.0]
    c.monkeypatch.setattr(q.time, "monotonic", lambda: now[0])
    if phase == "pin":

        def late_pin(self, **kw):
            now[0] = 121.0
            return c.captured

        c.monkeypatch.setattr(q.pin.PinOwner, "check", late_pin)
    elif phase == "encoder":

        def late_encoder(self, text):
            now[0] = 121.0
            return c.embedding

        c.monkeypatch.setattr(q.query_embedding.ResidentQueryEncoder, "encode_query", late_encoder)
    else:
        original = q.hybrid.search

        def late_hybrid(*args, **kwargs):
            result = original(*args, **kwargs)
            now[0] = 121.0
            return result

        c.monkeypatch.setattr(q.hybrid, "search", late_hybrid)
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args)
    assert c.owner.state == "ACTIVE" and c.encoder._state == "open"


def test_policy_changes_during_hybrid_refuse(context):
    c = context
    state = [c.authority]
    original = q.hybrid.search

    def search(*args, **kwargs):
        result = original(*args, **kwargs)
        state[0] = replace(
            c.authority,
            restrictions=q.records.Restrictions(schema_version=1, corpora=(), versions=None),
        )
        return result

    c.monkeypatch.setattr(q.hybrid, "search", search)
    with pytest.raises(q.PinnedQueryError):
        q.search_pinned_data(*c.args[:-1], lambda *a: state[0])
    assert sum(x[0] == "search" for x in c.calls) == 1


def test_hybrid_exception_is_content_free_and_owners_retained(context):
    c = context

    def fail(*args, **kwargs):
        raise ValueError("private detail")

    c.monkeypatch.setattr(q.hybrid, "search", fail)
    with pytest.raises(q.PinnedQueryError, match="^pinned query refused$"):
        q.search_pinned_data(*c.args)
    assert c.owner.state == "ACTIVE" and c.encoder._state == "open"
