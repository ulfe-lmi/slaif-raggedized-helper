"""Controlled ownership failures; no native generator or filesystem store is used."""
from types import SimpleNamespace

import pytest

import test_source_bound_support_ci_composition as support
import test_raw_hybrid_search_composition as source
import test_native_tokenizers
from slaif_raggedized_helper import derived_store, schema, source_admission


class Sentinel(BaseException):
    pass


class FakePath:
    def __truediv__(self, other):
        return self

    def mkdir(self, *args, **kwargs):
        pass

    def write_bytes(self, value):
        pass


class Store:
    def __init__(self, events, name, close_failure=None, admit_failure=None, fail_at=0):
        self.events, self.name = events, name
        self.close_failure, self.admit_failure, self.fail_at = close_failure, admit_failure, fail_at
        self.admissions = 0

    def admit(self, *args):
        self.admissions += 1
        if self.admissions == self.fail_at:
            raise self.admit_failure
        return object()

    def close(self):
        self.events.append(self.name)
        if self.close_failure:
            raise self.close_failure


def setup_sources(monkeypatch, original, derived, constructor_failure=None):
    # The local import inside make_sources resolves this stub, never the generator.
    monkeypatch.setattr(test_native_tokenizers, 'make_native', lambda path: (
        [object(), object()], object(), lambda *args: SimpleNamespace(sha256='a' * 64)))
    monkeypatch.setattr(source_admission, 'parse_manifest', lambda data: SimpleNamespace(
        sources=[object(), object(), object()]))
    monkeypatch.setattr(source_admission, 'OriginalStore', lambda path: original)

    def construct(path):
        if constructor_failure:
            raise constructor_failure
        return derived

    monkeypatch.setattr(derived_store, 'Store', construct)


@pytest.mark.parametrize('fail_at', [1, 2])
def test_admission_failure_closes_original(monkeypatch, fail_at):
    events = []
    failure = Sentinel('admit')
    original = Store(events, 'original', admit_failure=failure, fail_at=fail_at)
    setup_sources(monkeypatch, original, None)
    with pytest.raises(Sentinel) as caught:
        source.make_sources(FakePath())
    assert caught.value is failure
    assert events == ['original']


def test_derived_constructor_failure(monkeypatch):
    events = []
    failure = Sentinel('construct')
    setup_sources(monkeypatch, Store(events, 'original'), None, failure)
    with pytest.raises(Sentinel) as caught:
        source.make_sources(FakePath())
    assert caught.value is failure
    assert events == ['original']


def test_body_failure_survives_close_failure(monkeypatch):
    events = []
    failure, close_failure = Sentinel('body'), Sentinel('close')
    setup_sources(monkeypatch, Store(events, 'original'), Store(events, 'derived', close_failure))

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(schema, 'fingerprint', fail)
    with pytest.raises(Sentinel) as caught:
        source.make_sources(FakePath())
    assert caught.value is failure
    assert events == ['derived', 'original']
    assert 'close' in failure.__notes__[0]


def test_wrapper_failure_preserves_body(monkeypatch):
    events = []
    failure, close_failure = Sentinel('body'), Sentinel('close')
    original, derived = Store(events, 'original'), Store(events, 'derived', close_failure)
    monkeypatch.setattr(source, 'make_sources', lambda *a, **k: (original, derived, 'root', 'id'))

    def fail(*args):
        raise failure

    monkeypatch.setattr(support.raw_snapshot_catalog, 'load_catalog', fail)
    with pytest.raises(Sentinel) as caught:
        support.make_owned_support(FakePath())
    assert caught.value is failure
    assert events == ['derived', 'original']
    assert 'close' in failure.__notes__[0]


@pytest.mark.parametrize('body_fails', [False, True])
def test_fixture_finalizer_attempts_both(monkeypatch, body_fails):
    events = []
    body, close_failure = Sentinel('body'), Sentinel('close')
    context = SimpleNamespace(originals=Store(events, 'original'),
                              derived=Store(events, 'derived', close_failure))
    monkeypatch.setattr(support, 'make_owned_support', lambda path: context)
    fixture = support.owned_support.__wrapped__(FakePath(), monkeypatch)
    assert next(fixture) is context
    with pytest.raises(Sentinel) as caught:
        if body_fails:
            fixture.throw(body)
        else:
            next(fixture)
    assert caught.value is (body if body_fails else close_failure)
    assert events == ['derived', 'original']
    if body_fails:
        assert 'close' in body.__notes__[0]


class HostileException(Sentinel):
    def __repr__(self):
        raise AssertionError("repr must not run")

    def add_note(self, note):
        raise AssertionError("overridden add_note must not run")


def test_hostile_body_and_close_exceptions(monkeypatch):
    events = []
    body, close_failure = HostileException('body'), HostileException('close')
    setup_sources(monkeypatch, Store(events, 'original'), Store(events, 'derived', close_failure))

    def fail(*args, **kwargs):
        raise body

    monkeypatch.setattr(schema, 'fingerprint', fail)
    with pytest.raises(HostileException) as caught:
        source.make_sources(FakePath())
    assert caught.value is body
    assert events == ['derived', 'original']
    assert body.__notes__ == ['Store close failed; cleanup may be incomplete.']


def test_hostile_close_failures_preserve_first():
    events = []
    first, second = HostileException('first'), HostileException('second')
    with pytest.raises(HostileException) as caught:
        source.close_owned_stores(
            Store(events, 'derived', first), Store(events, 'original', second))
    assert caught.value is first
    assert events == ['derived', 'original']
    assert first.__notes__ == ['Store close failed; cleanup may be incomplete.']
