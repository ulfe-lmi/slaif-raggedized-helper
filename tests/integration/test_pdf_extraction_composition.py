import hashlib
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import pdf_extraction as pdf, provenance_records as p
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest

RUNTIME = Path('/home/janezp/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu')
PACKAGES = Path('/tmp/raggedized-pdf-dependency-pin-312/lib/python3.12/site-packages')


def tiny_pdf(pages=1, text=True):
    stream = (b'BT /F1 12 Tf 50 700 Td (Owned warning.) Tj ET\n' if text else b'')
    kids = ' '.join(f'{3 + i} 0 R' for i in range(pages))
    font = 3 + pages
    content = font + 1
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               f'<< /Type /Pages /Kids [{kids}] /Count {pages} >>'.encode()]
    for _ in range(pages):
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
                       f'/Resources << /Font << /F1 {font} 0 R >> >> '
                       f'/Contents {content} 0 R >>'.encode())
    objects.extend([b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
                    b'<< /Length %d >>\nstream\n' % len(stream) + stream + b'endstream'])
    data = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n')
    xref = len(data)
    data.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        data.extend(f'{offset:010d} 00000 n \n'.encode())
    data.extend(f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n'
                f'startxref\n{xref}\n%%EOF\n'.encode())
    return bytes(data)


def make_store(tmp_path, data):
    root = tmp_path / 'root'
    root.mkdir()
    (root / 'pdf').write_bytes(data)
    obj = dict(logical_id='owned', relative_path='pdf', display_uri='urn:owned', corpus='private',
               access_labels=['label'], processing_approved=True,
               redistribution_rights='prohibited', media_type='application/pdf',
               size=len(data), sha256=hashlib.sha256(data).hexdigest())
    source = parse_manifest(json.dumps(dict(schema_version=1, sources=[obj])).encode()).sources[0]
    store = OriginalStore(tmp_path / 'store')
    return store, store.admit(root, source)


@pytest.fixture
def runtime():
    if not RUNTIME.is_dir() or not PACKAGES.is_dir():
        pytest.skip('isolated development pdfminer runtime not installed')
    return pdf.PdfRuntime(RUNTIME, PACKAGES)


def test_native_pdf_to_registry(tmp_path, runtime):
    store, rev = make_store(tmp_path, tiny_pdf())
    try:
        result = pdf.extract(store, rev.revision_id, runtime)
        assert result.status == 'native_text' and result.pages == ((1, 'native_text'),)
        assert result.scope.labels == ('label',)
        assert result.scope.redistribution_rights == 'prohibited'
        assert ''.join(x.text for x in result.blocks) == 'Owned warning.\n'
        block = result.blocks[0]
        assert block.page_ref == 'page:1' and block.geometry is not None
        assert block.geometry[0] == 50.0 and block.origin == 'native'
        assert pdf.extract(store, rev.revision_id, runtime).blocks == result.blocks
        changed = pdf.extract(store, rev.revision_id, runtime, pdf.PdfPolicy(max_pages=1))
        assert changed.dependency.extraction_id != result.dependency.extraction_id
        assert changed.blocks[0].block_id != block.block_id
        registry = p.Registry((rev,), (result.dependency,), result.blocks)
        fragment = p.SourceFragment(schema_version=1, kind='source', block_id=block.block_id,
                                    start=0, end=len(block.text), copied_text=block.text)
        chunk = p.Chunk(schema_version=1, chunk_id='tmp', revision_id=rev.revision_id,
                        extraction_id=result.dependency.extraction_id,
                        policy_id=p.policy_id('owned'),
                        fragments=(fragment,), text=block.text, text_sha256=block.text_sha256)
        chunk = chunk.model_copy(update={'chunk_id': p.chunk_id(chunk)})
        assert registry.bind_chunk(chunk) == result.scope
    finally:
        store.close()


def test_pdf_limits_and_visual_page(tmp_path, runtime):
    for name, data, policy, expected in (
        ('pages', tiny_pdf(2), pdf.PdfPolicy(max_pages=1), 'refused'),
        ('objects', tiny_pdf(), pdf.PdfPolicy(max_objects=1), 'refused'),
        ('text', tiny_pdf(), pdf.PdfPolicy(max_chars=1), 'refused'),
        ('output', tiny_pdf(), pdf.PdfPolicy(max_output=50), 'refused'),
        ('bytes', tiny_pdf(), pdf.PdfPolicy(max_bytes=10), 'refused'),
        ('malformed', b'not a PDF', pdf.PdfPolicy(), 'refused'),
        ('visual', tiny_pdf(text=False), pdf.PdfPolicy(), 'partial_visual_needed'),
    ):
        sub = tmp_path / name
        sub.mkdir()
        store, rev = make_store(sub, data)
        try:
            if expected == 'refused':
                with pytest.raises(pdf.PdfError):
                    pdf.extract(store, rev.revision_id, runtime, policy)
            else:
                result = pdf.extract(store, rev.revision_id, runtime, policy)
                assert result.status == expected and result.pages == ((1, 'visual_needed'),)
                assert result.blocks == ()
        finally:
            store.close()


def test_cap_before_blob_read_and_corruption(tmp_path, runtime, monkeypatch):
    import os

    data = tiny_pdf()
    store, rev = make_store(tmp_path, data)
    blob = tmp_path / 'store' / 'blobs' / rev.blob
    actual = os.read
    reads = []

    def track(fd, size):
        result = actual(fd, size)
        if os.fstat(fd).st_ino == blob.stat().st_ino:
            reads.append(len(result))
        return result

    monkeypatch.setattr(os, 'read', track)
    try:
        with pytest.raises(pdf.PdfError):
            pdf.extract(store, rev.revision_id, runtime, pdf.PdfPolicy(max_bytes=10))
        assert reads == []
        blob.write_bytes(b'x' * len(data))
        with pytest.raises(pdf.PdfError, match='pdf extraction refused'):
            pdf.extract(store, rev.revision_id, runtime)
        assert sum(reads) == len(data)
    finally:
        store.close()


def test_wrong_worker_identity_refused(tmp_path, runtime, monkeypatch):
    store, rev = make_store(tmp_path, tiny_pdf())
    try:
        forged = {'revision': rev.revision_id, 'policy': 'wrong', 'request': 'wrong',
                  'pages': [{'page': 1, 'status': 'visual_needed'}], 'blocks': [], 'objects': 0}
        monkeypatch.setattr(pdf, '_run', lambda *_: json.dumps(forged).encode())
        with pytest.raises(pdf.PdfError, match='pdf extraction refused'):
            pdf.extract(store, rev.revision_id, runtime)
    finally:
        store.close()


def test_isolation_denies_owned_external_canary_network_and_inherited_fd(tmp_path, runtime):
    import os
    import socket
    import time

    canary = tmp_path / 'outside-canary'
    canary.write_bytes(b'owned')
    source = tmp_path / 'input'
    source.write_bytes(tiny_pdf())
    probe = tmp_path / 'probe.py'
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen()
    fd = os.open(canary, os.O_RDONLY)
    os.set_inheritable(fd, True)
    probe.write_text('import os,socket,json\n'
                     f'canary={str(canary)!r}\n'
                     f'fd={fd}\n'
                     'try:\n os.fstat(fd); inherited=True\nexcept OSError:\n inherited=False\n'
                     'try:\n open("/input.pdf","ab"); writable=True\n'
                     'except OSError:\n writable=False\n'
                     's=socket.socket();s.settimeout(.3)\n'
                     f'network=s.connect_ex(("127.0.0.1",{listener.getsockname()[1]}))\n'
                     'print(json.dumps(dict(outside=os.path.exists(canary),'
                     'home=os.path.exists("/home"),gpu=os.path.exists("/dev/nvidia0"),'
                     'inherited=inherited,writable=writable,network=network)))\n')
    try:
        argv = pdf._argv(runtime, source, [])
        worker = str(Path(pdf.__file__).with_name('pdf_worker.py').resolve())
        argv[argv.index(worker)] = str(probe)
        result = json.loads(pdf._run(argv, 4096, time.monotonic() + 2.0))
        assert result == {'outside': False, 'home': False, 'gpu': False,
                          'inherited': False, 'writable': False, 'network': 111}
    finally:
        os.close(fd)
        listener.close()


def test_encrypted_pdf_refused(tmp_path, runtime):
    data = tiny_pdf().replace(
        b'/Root 1 0 R >>',
        b'/Root 1 0 R /ID [<30313233343536373839616263646566>'
        b'<30313233343536373839616263646566>] '
        b'/Encrypt << /Filter /Standard /V 1 /R 2 /P -4 '
        b'/O <0000000000000000000000000000000000000000000000000000000000000000> '
        b'/U <0000000000000000000000000000000000000000000000000000000000000000> >> >>')
    store, rev = make_store(tmp_path, data)
    try:
        with pytest.raises(pdf.PdfError, match='pdf worker refused input'):
            pdf.extract(store, rev.revision_id, runtime)
    finally:
        store.close()


def test_source_mutation_during_verified_read_refused(tmp_path, runtime, monkeypatch):
    import os

    data = tiny_pdf()
    store, rev = make_store(tmp_path, data)
    blob = tmp_path / 'store' / 'blobs' / rev.blob
    actual = os.read
    changed = []

    def mutate(fd, size):
        result = actual(fd, size)
        if result and not changed and os.fstat(fd).st_ino == blob.stat().st_ino:
            changed.append(True)
            blob.write_bytes(b'x' * len(data))
        return result

    monkeypatch.setattr(os, 'read', mutate)
    try:
        with pytest.raises(pdf.PdfError, match='pdf extraction refused'):
            pdf.extract(store, rev.revision_id, runtime)
        assert changed == [True]
    finally:
        store.close()


def test_non_pdf_media_refused_without_worker(tmp_path, runtime, monkeypatch):
    root = tmp_path / 'root'
    root.mkdir()
    (root / 'doc').write_bytes(b'owned')
    data = dict(logical_id='owned', relative_path='doc', display_uri='urn:owned', corpus='c',
                access_labels=[], processing_approved=True, redistribution_rights='unknown',
                media_type='text/plain', size=5, sha256=hashlib.sha256(b'owned').hexdigest())
    source = parse_manifest(json.dumps(dict(schema_version=1, sources=[data])).encode()).sources[0]
    store = OriginalStore(tmp_path / 'store')
    try:
        rev = store.admit(root, source)
        monkeypatch.setattr(pdf, '_run', lambda *_: (_ for _ in ()).throw(AssertionError()))
        with pytest.raises(pdf.PdfError, match='pdf extraction refused'):
            pdf.extract(store, rev.revision_id, runtime)
    finally:
        store.close()


def test_missing_backend_import_is_explicit_prerequisite(tmp_path, runtime):
    packages = tmp_path / 'packages'
    (packages / 'pdfminer').mkdir(parents=True)
    (packages / 'pdfminer' / '__init__.py').write_text('')
    dist = packages / 'pdfminer_six-20260107.dist-info'
    dist.mkdir()
    (dist / 'METADATA').write_text('Metadata-Version: 2.1\nName: pdfminer.six\nVersion: 20260107\n')
    store, rev = make_store(tmp_path, tiny_pdf())
    try:
        with pytest.raises(pdf.PdfPrerequisiteError, match='pdf isolation or backend unavailable'):
            pdf.extract(store, rev.revision_id, pdf.PdfRuntime(runtime.runtime_dir, packages))
    finally:
        store.close()


def nested_form_pdf():
    outer = b'BT /F1 12 Tf 50 700 Td (Visible normal) Tj ET\n/Fm1 Do\n'
    form = b'BT /F1 12 Tf 50 600 Td (Hidden warning) Tj ET\n/Fm2 Do\n'
    inner = b'BT /F1 12 Tf 50 500 Td (Nested warning) Tj ET\n'
    def stream(data):
        return b' /Length %d >>\nstream\n' % len(data) + data + b'endstream'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources '
               b'<< /Font << /F1 4 0 R >> /XObject << /Fm1 6 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<<' + stream(outer),
               b'<< /Type /XObject /Subtype /Form /BBox [0 0 612 792] /Resources '
               b'<< /Font << /F1 4 0 R >> /XObject << /Fm2 7 0 R >> >>' + stream(form),
               b'<< /Type /XObject /Subtype /Form /BBox [0 0 612 792] /Resources '
               b'<< /Font << /F1 4 0 R >> >>' + stream(inner)]
    data = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n')
    xref = len(data)
    data.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:
        data.extend(f'{offset:010d} 00000 n \n'.encode())
    data.extend(
        f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    return bytes(data)


def test_nested_forms_keep_text_once_with_geometry_and_limits(tmp_path, runtime):
    store, rev = make_store(tmp_path, nested_form_pdf())
    try:
        result = pdf.extract(store, rev.revision_id, runtime)
        text = ''.join(block.text for block in result.blocks)
        assert text == 'Visible normal\nHidden warningNested warning'
        assert result.pages == ((1, 'native_text'),)
        assert all(block.geometry is not None for block in result.blocks)
        assert (next(b for b in result.blocks if b.text == 'H').geometry[1]
            > next(b for b in result.blocks if b.text == 'N').geometry[1])
        assert pdf.extract(store, rev.revision_id, runtime).blocks == result.blocks
        for policy in (pdf.PdfPolicy(max_objects=10), pdf.PdfPolicy(max_chars=20)):
            with pytest.raises(pdf.PdfError):
                pdf.extract(store, rev.revision_id, runtime, policy)
    finally:
        store.close()


def test_matching_child_object_counts_and_mixed_status(tmp_path, runtime, monkeypatch):
    store, rev = make_store(tmp_path, tiny_pdf())
    state = {'objects': 0, 'status': 'native_text',
             'blocks': [{'page': 1, 'text': 'x', 'bbox': [0, 0, 1, 1]}]}
    def forged(argv, cap, deadline):
        rid, policy, nonce = argv[-6:-3]
        return json.dumps(dict(revision=rid, policy=policy, request=nonce,
                               pages=[dict(page=1, status=state['status'])],
                               blocks=state['blocks'], objects=state['objects'])).encode()
    monkeypatch.setattr(pdf, '_run', forged)
    try:
        with pytest.raises(pdf.PdfError):
            pdf.extract(store, rev.revision_id, runtime)
        state['objects'] = 1
        assert pdf.extract(store, rev.revision_id, runtime).status == 'native_text'
        state['status'] = 'visual_needed'
        assert pdf.extract(store, rev.revision_id, runtime).status == 'partial_visual_needed'
        state['blocks'] = []
        state['status'] = 'native_text'
        with pytest.raises(pdf.PdfError):
            pdf.extract(store, rev.revision_id, runtime)
    finally:
        store.close()
