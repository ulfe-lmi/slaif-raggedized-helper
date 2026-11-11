import os
import subprocess
import sys
import time

import pytest

from slaif_raggedized_helper import pdf_extraction as pdf


def test_policy_rejects_boolean_nonfinite_and_oversize():
    for params in ({'max_bytes': True}, {'max_pages': 33}, {'max_objects': 0},
                   {'max_chars': -1}, {'wall_seconds': float('nan')}, {'wall_seconds': 2.1}):
        with pytest.raises(pdf.PdfError):
            pdf.PdfPolicy(**params)


def test_missing_isolation_fails_closed(tmp_path):
    with pytest.raises(pdf.PdfPrerequisiteError):
        pdf._argv(pdf.PdfRuntime(tmp_path, tmp_path), tmp_path / 'in', [])


@pytest.mark.parametrize('body,expected', [
    ('import time; time.sleep(1)', 'timeout'),
    ('import os,time; os.write(1,b"x"*8192); time.sleep(1)', 'output limit'),
    ('import sys; sys.exit(7)', 'unavailable'),
])
def test_owned_child_timeout_flood_crash_cleanup(tmp_path, monkeypatch, body, expected):
    child_path = tmp_path / 'owned.py'
    child_path.write_text(body)
    actual = subprocess.Popen
    children = []

    def record(*args, **kwargs):
        child = actual(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(pdf.subprocess, 'Popen', record)
    started = time.monotonic()
    with pytest.raises(pdf.PdfError, match=expected):
        pdf._run([sys.executable, str(child_path)], 128, time.monotonic() + 0.15)
    assert time.monotonic() - started < 1.5
    assert len(children) == 1 and children[0].poll() is not None
    assert children[0].stdout.closed


def test_keyboard_interrupt_stops_exact_child_with_caller_alive(tmp_path, monkeypatch):
    script = tmp_path / 'owned.py'
    script.write_text('import time; time.sleep(1)')
    actual = subprocess.Popen
    children = []

    def record(*args, **kwargs):
        child = actual(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(pdf.subprocess, 'Popen', record)
    monkeypatch.setattr(pdf.selectors.DefaultSelector, 'select',
                        lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('original')))
    with pytest.raises(KeyboardInterrupt, match='original'):
        pdf._run([sys.executable, str(script)], 128, time.monotonic() + 1)
    assert children[0].poll() is not None and children[0].stdout.closed
    assert os.getpid() > 0


def test_import_does_not_start_parser_network_or_telemetry():
    code = '''
import builtins, resource, socket, subprocess, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in ('pdfminer', 'torch', 'transformers', 'sentence_transformers'):
        raise AssertionError('unexpected parser or model import')
    return original(name, *args, **kwargs)
def forbidden(*args, **kwargs):
    raise AssertionError('unexpected external work')
builtins.__import__ = guarded
socket.socket.connect = forbidden
subprocess.Popen = forbidden
resource.getrusage = forbidden
import slaif_raggedized_helper.pdf_extraction
'''
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, timeout=2)
    assert result.returncode == 0, result.stderr


def test_selector_startup_failure_reaps_child(tmp_path, monkeypatch):
    script = tmp_path / 'owned.py'
    script.write_text('import time; time.sleep(1)')
    original = subprocess.Popen
    children = []

    def record(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(pdf.subprocess, 'Popen', record)
    monkeypatch.setattr(pdf.selectors, 'DefaultSelector',
                        lambda: (_ for _ in ()).throw(OSError('fixture')))
    with pytest.raises(OSError, match='fixture'):
        pdf._run([sys.executable, str(script)], 128, time.monotonic() + 1)
    assert len(children) == 1 and children[0].poll() is not None
    assert children[0].stdout.closed


def test_worker_marks_unsupported_nested_text_on_mixed_page(monkeypatch, capsys):
    import json
    import types
    from slaif_raggedized_helper import pdf_worker as worker

    class Text:
        pass
    class Container:
        def __init__(self, children): self.children = children
        def __iter__(self): return iter(self.children)
    class TextContainer(Container, Text):
        bbox = (0, 0, 1, 1)
        def get_text(self): return 'outer\n'
    class Char(Text):
        bbox = (0, 0, 1, 1)
        def get_text(self): return 'x'
    class Unsupported(Text):
        pass
    page = [TextContainer([Char()]), Container([Unsupported()])]
    modules = {
        'pdfminer': types.ModuleType('pdfminer'),
        'pdfminer.high_level': types.SimpleNamespace(extract_pages=lambda *a, **k: [page]),
        'pdfminer.layout': types.SimpleNamespace(LTContainer=Container, LTText=Text,
                                                 LTTextContainer=TextContainer, LTChar=Char,
                                                 LTImage=type('Image', (), {}),
                                                 LTCurve=type('Curve', (), {})),
        'pdfminer.pdfdocument': types.SimpleNamespace(
            PDFDocument=lambda _: types.SimpleNamespace(encryption=None)),
        'pdfminer.pdfparser': types.SimpleNamespace(PDFParser=lambda _: None),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(worker, 'version', lambda _: '20260107')
    monkeypatch.setattr('builtins.open', lambda *a, **k: __import__('io').BytesIO())
    monkeypatch.setattr(sys, 'argv', ['worker', 'revision', 'policy', 'nonce', '1', '10', '100'])
    assert worker.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result['pages'] == [{'page': 1, 'status': 'visual_needed'}]
    assert [b['text'] for b in result['blocks']] == ['outer\n']
    assert result['objects'] == 4
