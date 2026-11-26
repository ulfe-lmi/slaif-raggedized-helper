"""Synthetic serialization checks; these do not prove original source binding."""

import hashlib
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import source_bound_ranking as binder


def test_literal_root_vectors():
    oracle = json.loads(
        (Path(__file__).parents[2] / "docs/parallel/source-bound-ranking-oracle.json").read_text()
    )
    for vector in oracle["vectors"]:
        pair = json.dumps(
            vector["authority_pair"],
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        assert pair.decode() == vector["authority_utf8"]
        assert (
            hashlib.sha256(pair).hexdigest() == vector["expected_hash_object"]["authority_sha256"]
        )
        encoded = json.dumps(
            vector["expected_hash_object"],
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
        assert encoded.decode() == vector["canonical_ascii"]
        assert len(encoded) == vector["canonical_bytes"]
        assert (
            binder._binding_hash(vector["expected_hash_object"], lambda: None)
            == vector["expected_binding_id"]
        )


def test_stream_limit_positive_control():
    obj = {"value": "abc"}
    size = len(json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode())
    assert binder._binding_hash(obj, lambda: None, size).startswith("sha256:")
    with pytest.raises(ValueError):
        binder._binding_hash(obj, lambda: None, size - 1)


def test_refusal_and_base_exception_identity(monkeypatch):
    class Sentinel(BaseException):
        pass

    marker = Sentinel()

    def interrupt():
        raise marker

    monkeypatch.setattr(binder.time, "monotonic", interrupt)
    with pytest.raises(Sentinel) as raised:
        binder.bind(None, None, "/", None, None, (), grants=None)
    assert raised.value is marker


def test_empty_two_passes_and_late_refusals(monkeypatch):
    from types import SimpleNamespace

    originals = object.__new__(binder.OriginalStore)
    derived = object.__new__(binder.derived_store.Store)
    snapshot = "sha256:" + "1" * 64
    catalog_id = "sha256:" + "2" * 64
    catalog = SimpleNamespace(
        snapshot_id=snapshot, catalog_id=catalog_id, row_map_bytes=b"fake", rows=()
    )
    calls = []

    def load(*args, **kwargs):
        calls.append(kwargs["deadline_ms"])
        return catalog

    monkeypatch.setattr(binder.raw_snapshot_catalog, "load_catalog", load)
    monkeypatch.setattr(binder.raw_snapshot_rows, "parse", lambda _: SimpleNamespace(rows=()))

    def run():
        return binder.bind(originals, derived, "/tmp/owned", snapshot, catalog_id, (), grants=None)

    result = run()
    assert len(calls) == 2 and all(1 <= n <= 30000 for n in calls)
    assert result.source_binding_status == "NO_SELECTED_SOURCE_VALIDATED"
    calls.clear()

    def second_failure(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise ValueError("private")
        return catalog

    monkeypatch.setattr(binder.raw_snapshot_catalog, "load_catalog", second_failure)
    with pytest.raises(binder.SourceBindingError, match="^source bound ranking refused$"):
        run()
    assert len(calls) == 2
    monkeypatch.setattr(binder.raw_snapshot_catalog, "load_catalog", load)
    original_constructor = binder.BoundRanking
    ticks = [0.0]
    monkeypatch.setattr(binder.time, "monotonic", lambda: ticks[0])

    def late(*args):
        value = original_constructor(*args)
        ticks[0] = 31.0
        return value

    monkeypatch.setattr(binder, "BoundRanking", late)
    with pytest.raises(binder.SourceBindingError):
        run()
    assert len(calls) == 4


def test_authority_snapshot_and_preflight(monkeypatch):
    from slaif_raggedized_helper import provenance_records as p

    originals = object.__new__(binder.OriginalStore)
    derived = object.__new__(binder.derived_store.Store)
    ident = "sha256:" + "1" * 64
    good = p.Grants(schema_version=1, corpora=("one",), versions=("v1",), labels=())
    calls = []
    monkeypatch.setattr(
        binder.raw_snapshot_catalog, "load_catalog", lambda *a, **k: calls.append(1)
    )

    def invoke(ids, grants=good):
        return binder.bind(originals, derived, "/tmp/owned", ident, ident, ids, grants=grants)

    for invalid in (None, [], (ident, ident), ("foreign",)):
        with pytest.raises(binder.SourceBindingError):
            invoke(invalid)
    invalid_grants = good.model_copy(update={"corpora": ["one"]})
    with pytest.raises(binder.SourceBindingError):
        invoke((), invalid_grants)
    assert not calls
    clone = binder._authority(
        good, p.Grants, ("corpora", "versions", "labels"), False, [0], lambda: None
    )
    assert clone == good and clone is not good


def test_authority_bypassed_dictionary_shape_refused():
    from slaif_raggedized_helper import provenance_records as p

    good = p.Grants(schema_version=1, corpora=("one",), versions=("v1",), labels=())
    args = (p.Grants, ("corpora", "versions", "labels"), False, [0], lambda: None)
    assert binder._authority(good, *args) == good
    malformed = good.model_copy()
    malformed.__dict__["unexpected"] = "ignored"
    with pytest.raises(ValueError):
        binder._authority(malformed, *args)
    missing = good.model_copy()
    del missing.__dict__["labels"]
    missing.__dict__["unexpected"] = ()
    with pytest.raises(ValueError):
        binder._authority(missing, *args)


@pytest.mark.parametrize(
    ("attribute", "maximum", "operation"),
    [
        ("blocks", 4096, lambda b: b.bundle(1, 0)),
        ("bundle_bytes", 100663296, lambda b: b.member(1)),
        ("fragments", 65536, lambda b: b.fragment(1, 1)),
        ("copied_bytes", 16777216, lambda b: b.fragment(1, 1)),
        ("block_id_bytes", 2097152, lambda b: b.fragment(1, 1)),
    ],
)
def test_private_per_pass_count_guards(attribute, maximum, operation):
    # Set a prior counter directly: this is a guard unit, not a giant store journey.
    budget = binder._PassBudget()
    setattr(budget, attribute, maximum - 1)
    operation(budget)
    assert getattr(budget, attribute) == maximum
    with pytest.raises(ValueError):
        operation(budget)


def test_per_pass_bundle_counts_are_cumulative():
    budget = binder._PassBudget()
    budget.bundle(2048, 50000000)
    budget.member(331648)
    budget.bundle(2048, 50000000)
    assert budget.blocks == 4096 and budget.bundle_bytes == 100331648
    with pytest.raises(ValueError):
        budget.bundle(1, 0)


def test_preflight_maximum_unique_ids_is_not_rejected(monkeypatch):
    originals = object.__new__(binder.OriginalStore)
    derived = object.__new__(binder.derived_store.Store)
    ident = "sha256:" + "0" * 64
    ids = tuple("sha256:" + format(i, "064x") for i in range(4096))
    calls = []

    class Observed(BaseException):
        pass

    def catalog(*args, **kwargs):
        calls.append(1)
        raise Observed

    monkeypatch.setattr(binder.raw_snapshot_catalog, "load_catalog", catalog)
    with pytest.raises(Observed):
        binder.bind(originals, derived, "/tmp/owned", ident, ident, ids, grants=None)
    assert calls == [1]
    with pytest.raises(binder.SourceBindingError):
        binder.bind(
            originals,
            derived,
            "/tmp/owned",
            ident,
            ident,
            ids + ("sha256:" + "f" * 64,),
            grants=None,
        )
    assert calls == [1]


def test_late_hash_refusal_and_interrupt_with_valid_empty_calls(monkeypatch):
    from types import SimpleNamespace

    originals = object.__new__(binder.OriginalStore)
    derived = object.__new__(binder.derived_store.Store)
    snapshot = "sha256:" + "a" * 64
    catalog = SimpleNamespace(
        snapshot_id=snapshot, catalog_id=snapshot, row_map_bytes=b"x", rows=()
    )
    calls = []

    def load(*args, **kwargs):
        calls.append(1)
        return catalog

    monkeypatch.setattr(binder.raw_snapshot_catalog, "load_catalog", load)
    monkeypatch.setattr(binder.raw_snapshot_rows, "parse", lambda _: SimpleNamespace(rows=()))

    def run():
        return binder.bind(originals, derived, "/tmp/owned", snapshot, snapshot, (), grants=None)

    assert run().row_count == 0 and len(calls) == 2

    def fail_hash(*args):
        raise ValueError("private")

    monkeypatch.setattr(binder, "_binding_hash", fail_hash)
    with pytest.raises(binder.SourceBindingError, match="^source bound ranking refused$"):
        run()
    assert len(calls) == 4

    class Sentinel(BaseException):
        pass

    marker = Sentinel()

    def interrupt(*args):
        raise marker

    monkeypatch.setattr(binder, "_binding_hash", interrupt)
    with pytest.raises(Sentinel) as result:
        run()
    assert result.value is marker and len(calls) == 6


def test_authority_utf8_pair_budget_before_catalog(monkeypatch):
    from slaif_raggedized_helper import provenance_records as p

    originals = object.__new__(binder.OriginalStore)
    derived = object.__new__(binder.derived_store.Store)
    ident = "sha256:" + "1" * 64
    calls = []

    class Seen(BaseException):
        pass

    def catalog(*args, **kwargs):
        calls.append(1)
        raise Seen

    monkeypatch.setattr(binder.raw_snapshot_catalog, "load_catalog", catalog)

    def value(n):
        return p.Grants(schema_version=1, corpora=("😀" * n,), versions=(), labels=())

    def call(grant):
        return binder.bind(originals, derived, "/tmp/owned", ident, ident, (), grants=grant)

    with pytest.raises(Seen):
        call(value(65500))
    with pytest.raises(binder.SourceBindingError):
        call(value(65536))  # Within the codepoint budget, over the canonical UTF-8 pair budget.
    with pytest.raises(binder.SourceBindingError):
        call(value(65537))
    assert calls == [1]
