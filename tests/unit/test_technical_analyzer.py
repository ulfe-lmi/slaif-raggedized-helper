from dataclasses import replace
import builtins
import importlib
import pydoc
import socket
import unicodedata

import pytest

from slaif_raggedized_helper import technical_analyzer as a


def test_technical_terms_and_exact_spans():
    text = ('WARNING WARNING --no-cache /opt/a.conf C:\\Temp\\ERR_CODE42 '
            'foo.bar_name E123 -12.5 +3V v1.2.3 L/s ne not never '
            'Živjo e\u0301 😀\r\n"https://example.invalid/a" malformed\\tail')
    result = a.analyze(text)
    terms = [t.text for t in result.terms]
    for term in ('--no-cache', 'no', 'cache', '/opt/a.conf', 'C:\\Temp\\ERR_CODE42',
                 'ERR', 'CODE42', 'foo.bar_name', 'name', 'E123', '-12.5', '+3V',
                 'v1.2.3', 'L/s', 'ne', 'not', 'never', 'Živjo', 'živjo', '😀',
                 'https://example.invalid/a', 'tail'):
        assert term in terms
    assert terms.count('WARNING') == 2
    for t in result.terms:
        original = text[t.start:t.end]
        if t.derivation in ('literal', 'component'):
            assert t.text == original
        else:
            assert t.text == unicodedata.normalize('NFKC', original).casefold()
    assert a.analyze(text) == result
    assert a.analyze('').terms == () and a.analyze(' \r\n').terms == ()
    assert a.analyzer_id() != a.analyzer_id(replace(a.Policy(), max_terms=99))


def test_fixed_errors_limits_and_deadline(monkeypatch):
    for text in (None, b'canary', 'private-canary\ud800'):
        with pytest.raises(a.AnalyzerError, match='^analysis refused$'):
            a.analyze(text)
    for val in (True, 0, -1, float('inf'), float('nan'), '1', 10**20):
        with pytest.raises(a.AnalyzerError, match='^analysis refused$'):
            a.analyze('private-canary', replace(a.Policy(), max_chars=val))
    for policy, text in ((a.Policy(max_bytes=1), 'Ž'), (a.Policy(max_chars=1), 'ab'),
                         (a.Policy(max_token_chars=2), 'abc'),
                         (a.Policy(max_terms=1), 'two words'),
                         (a.Policy(max_components=1), 'a.b.c'),
                         (a.Policy(max_work=1), 'abc')):
        with pytest.raises(a.AnalyzerError, match='^analysis refused$'):
            a.analyze(text, policy)
    ticks = iter((0, 10))
    monkeypatch.setattr(a.time, 'monotonic', lambda: next(ticks, 10))
    with pytest.raises(a.AnalyzerError, match='^analysis refused$'):
        a.analyze('private-canary')


def test_no_io_on_import_or_analysis(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('unexpected I/O')
    monkeypatch.setattr(builtins, 'open', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    importlib.reload(a)
    assert a.analyze('/private/path https://example.invalid --no-cache').terms
    assert 'half-open codepoint' in pydoc.render_doc(a.analyze)
