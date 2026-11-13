"""Independent adapter guards and canonical vectors; no source-proof stubs."""
import hashlib
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import derived_store, text_evaluation_gold_binding as gold
from slaif_raggedized_helper.source_admission import OriginalStore


ORACLE = json.loads((Path(__file__).resolve().parents[2] / 'docs/parallel/'
                     'text-evaluation-gold-binding-oracle.json').read_text())
DATA = ORACLE['zero_dataset_ascii'].encode('ascii')


def stores():
    # Uninitialized typed instances prove the zero path performs no store IO.
    return object.__new__(OriginalStore), object.__new__(derived_store.Store)


def test_fixed_vectors():
    for vector in ORACLE['vectors']:
        canonical = json.dumps(vector['object'], sort_keys=True, ensure_ascii=True,
                               separators=(',', ':'), allow_nan=False)
        assert canonical == vector['canonical_ascii']
        assert gold._binding_id(vector['object'], lambda: None) == vector['binding_id']
    expected = ORACLE['vectors'][1]['object']['bindings'][0]['text_sha256']
    assert hashlib.sha256('😀'.encode()).hexdigest() == expected


def test_real_zero_no_io_and_private_markers(monkeypatch):
    monkeypatch.setattr(gold.ingestion_store, 'load', lambda *a: pytest.fail('load'))
    result = gold.bind(*stores(), DATA, ())
    assert result.binding_id == ORACLE['vectors'][0]['binding_id']
    assert result.observations == result.bindings == ()
    assert result.source_binding_status == 'NO_GOLD_SOURCE_VALIDATED'
    assert result.qualification == 'NOT_QUALIFIED'
    assert result.authorship_status == result.rights_status == 'DECLARED_UNVERIFIED'
    assert result.split_status == 'STRUCTURAL_ONLY'
    assert 'case1' not in repr(result)
    with pytest.raises(Exception):
        result.qualification = 'QUALIFIED'


@pytest.mark.parametrize('ids,deadline', [([], 1), (('A' * 64,), 1),
    (('0' * 64, '0' * 64), 1), ((), True), ((), 0), ((), 120001)])
def test_preflight_refuses(ids, deadline, monkeypatch):
    monkeypatch.setattr(gold.text_evaluation_dataset, 'admit',
                        lambda *a, **k: pytest.fail('parser'))
    with pytest.raises(gold.GoldBindingError, match='^text evaluation gold binding refused$'):
        gold.bind(*stores(), DATA, ids, deadline_ms=deadline)


def test_zero_with_bundle_refuses_before_load(monkeypatch):
    monkeypatch.setattr(gold.ingestion_store, 'load', lambda *a: pytest.fail('load'))
    with pytest.raises(gold.GoldBindingError):
        gold.bind(*stores(), DATA, ('0' * 64,))


def test_errors_and_base_exception_identity(monkeypatch):
    class Stop(BaseException):
        pass
    sentinel = Stop()
    def fail(*args, **kwargs):
        raise sentinel
    monkeypatch.setattr(gold.text_evaluation_dataset, 'admit', fail)
    with pytest.raises(Stop) as caught:
        gold.bind(*stores(), DATA, ())
    assert caught.value is sentinel
    monkeypatch.setattr(gold.text_evaluation_dataset, 'admit', lambda *a, **k: 1 / 0)
    with pytest.raises(gold.GoldBindingError) as caught:
        gold.bind(*stores(), DATA, ())
    assert str(caught.value) == 'text evaluation gold binding refused'
    assert caught.value.__suppress_context__


def test_final_deadline(monkeypatch):
    original = gold._binding_id
    def expire(obj, check):
        value = original(obj, check)
        monkeypatch.setattr(gold.time, 'monotonic', lambda: float('inf'))
        return value
    monkeypatch.setattr(gold, '_binding_id', expire)
    with pytest.raises(gold.GoldBindingError):
        gold.bind(*stores(), DATA, ())


def test_non_structured_adapter_refused_guard_only(monkeypatch):
    # Stubbed lower load exercises only the adapter guard, never source proof.
    from types import SimpleNamespace
    doc = json.loads(DATA)
    case = doc['cases'][0]
    case['answerability'] = 'answerable'
    case['acceptable_facts'] = ['fixture']
    atom = dict(revision_id='sha256:' + '1' * 64, extraction_id='sha256:' + '2' * 64,
                block_id='b', start=0, end=1, text_sha256='3' * 64)
    case['requirements'] = [dict(requirement_id='r', grade=1, alternatives=[[atom]])]
    raw = json.dumps(doc, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()
    value = SimpleNamespace(blocks=(), metadata_json=b'{}', members=(),
                            adapter='pdf_extraction')
    monkeypatch.setattr(gold.ingestion_store, 'load', lambda *args: value)
    with pytest.raises(gold.GoldBindingError):
        gold.bind(*stores(), raw, ('a' * 64,))


@pytest.mark.parametrize('value', [None, b'', bytearray(DATA), 'text'])
def test_reject_non_admitted_dataset(value):
    with pytest.raises(gold.GoldBindingError):
        gold.bind(*stores(), value, ())


def test_exact_store_types_and_inert_fabrication():
    originals, derived = stores()
    with pytest.raises(gold.GoldBindingError):
        gold.bind(object(), derived, DATA, ())
    with pytest.raises(gold.GoldBindingError):
        gold.bind(originals, object(), DATA, ())
    fabricated = gold.BoundGold('x', 'y', 'z', 'id', (), (), 0, 0, 0, 'invented')
    with pytest.raises(gold.GoldBindingError):
        gold.bind(originals, derived, fabricated, ())


def test_deadline_before_parser(monkeypatch):
    times = iter((1.0, 1.0, 1.0005))
    monkeypatch.setattr(gold.time, 'monotonic', lambda: next(times))
    monkeypatch.setattr(gold.text_evaluation_dataset, 'admit',
                        lambda *a, **k: pytest.fail('parser'))
    with pytest.raises(gold.GoldBindingError):
        gold.bind(*stores(), DATA, (), deadline_ms=1)


def positive_data(spans):
    """Canonical declarations only; these never serve as source proof."""
    doc = json.loads(DATA)
    case = doc['cases'][0]
    case['answerability'] = 'answerable'
    case['acceptable_facts'] = ['fixture']
    alternatives = [spans[i:i + 8] for i in range(0, len(spans), 8)]
    alternatives.sort(key=lambda value: json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode())
    case['requirements'] = [dict(requirement_id='r', grade=1, alternatives=alternatives)]
    return json.dumps(doc, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()


def test_positive_empty_and_span_budget_preload(monkeypatch):
    from slaif_raggedized_helper import text_evaluation_dataset
    spans = [dict(revision_id='sha256:' + '1' * 64, extraction_id='sha256:' + '2' * 64,
                  block_id=f'b{i:02}', start=0, end=200000, text_sha256='3' * 64)
             for i in range(21 + 1)]
    raw = positive_data(spans)
    assert text_evaluation_dataset.admit(raw).gold_atom_count == 22
    monkeypatch.setattr(gold.ingestion_store, 'load', lambda *a: pytest.fail('load'))
    for ids in ((), ('a' * 64,)):
        with pytest.raises(gold.GoldBindingError):
            gold.bind(*stores(), raw, ids)
    with pytest.raises(gold.GoldBindingError):
        gold.bind(*stores(), positive_data(spans[:1]), ())


def test_id_limit_and_sort_precede_parser(monkeypatch):
    monkeypatch.setattr(gold.text_evaluation_dataset, 'admit',
                        lambda *a, **k: pytest.fail('parser'))
    for ids in (tuple(f'{i:064x}' for i in range(129)), ('b' * 64, 'a' * 64),
                ('sha256:' + 'a' * 64,)):
        with pytest.raises(gold.GoldBindingError):
            gold.bind(*stores(), DATA, ids)


def test_unit_stub_bundle_and_membership_guards(monkeypatch):
    """Lower load is stubbed: these checks are not original-source evidence."""
    from types import SimpleNamespace as NS

    revision, extraction = 'sha256:' + '1' * 64, 'sha256:' + '2' * 64
    def atom(block_id, text):
        return dict(revision_id=revision, extraction_id=extraction, block_id=block_id,
                    start=0, end=len(text), text_sha256=hashlib.sha256(text.encode()).hexdigest())
    def bundle(block_id, text):
        block = NS(revision_id=revision, extraction_id=extraction, block_id=block_id,
                   origin='native', kind='text', text=text)
        return NS(blocks=(block,), metadata_json=b'{}', members=(),
                  adapter='structured_text', revision=NS(revision_id=revision),
                  dependency=NS(extraction_id=extraction))
    a, b = 'a' * 64, 'b' * 64
    values = {a: bundle('a', 'é'), b: bundle('b', 'x')}
    calls = []
    def load(originals, derived, ident):
        calls.append(ident)
        return values[ident]
    monkeypatch.setattr(gold.ingestion_store, 'load', load)
    one = positive_data([atom('a', 'é')])
    with pytest.raises(gold.GoldBindingError, match='^text evaluation gold binding refused$'):
        gold.bind(*stores(), one, (a, b))
    assert calls == [a, b]
    calls.clear()
    assert len(gold.bind(*stores(), one, (a,)).bindings) == 1
    assert calls == [a, a]
    calls.clear()
    two = positive_data([atom('a', 'é'), atom('b', 'x')])
    with pytest.raises(gold.GoldBindingError, match='^text evaluation gold binding refused$'):
        gold.bind(*stores(), two, (a,))
    assert calls == [a]
    calls.clear()
    assert len(gold.bind(*stores(), two, (a, b)).bindings) == 2
    assert calls == [a, b, a, b]
