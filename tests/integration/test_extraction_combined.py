"""Combined canonical 006 first-slice extraction journey (order 006-a).

Composes the actually merged adapters in ONE owned store: owned manifest ->
OriginalStore -> native literal line / structural text / isolated fixed PDF
worker -> provenance.Registry. Shared bytes retain distinct rights/ACL and
version; a metadata correction publishes a new revision over the same
verified blob. Coverage is exact in Unicode code points; PDF pages are
native or explicitly visual-needed with honest partial status. Source byte
integrity (store verification) is exercised separately from the parser
limits and the cooperative parent/worker deadlines; none of those is a hard
filesystem-interrupt guarantee. The PDF part requires the explicitly
configured development backend and isolation and fails instead of skipping
when they are absent.
"""

import hashlib
import json
import os
from pathlib import Path

import pytest

from slaif_raggedized_helper import pdf_extraction as pdf
from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import structured_text as st
from slaif_raggedized_helper import text_extraction as tx
from slaif_raggedized_helper.source_admission import AdmissionError, OriginalStore, parse_manifest

RUNTIME = Path(os.environ['PDF_TEST_RUNTIME']) if os.environ.get('PDF_TEST_RUNTIME') else None
PACKAGES = Path(os.environ['PDF_TEST_PACKAGES']) if os.environ.get('PDF_TEST_PACKAGES') else None

# CRLF endings, an astral code point and a combining sequence: exact
# code-point preservation is asserted through both text adapters and the
# verified byte round-trip.
MARKDOWN = (
    "# Title \U00010348\r\n"
    "Intro paragraph with combining e\u0301 and CRLF endings.\r\n"
    "\r\n"
    "| Unit | Value |\r\n"
    "|---|---|\r\n"
    "| m | 1 |\r\n"
    "\r\n"
    "- step one\r\n"
    "  continuation line\r\n"
    "\r\n"
    "```text\r\n"
    "code line\r\n"
    "```\r\n"
    "\r\n"
    "Final line.\r\n"
)


def source_for(logical_id, path, media, *, corpus, labels, version, rights):
    data = MARKDOWN.encode('utf-8')
    return dict(logical_id=logical_id, relative_path=path, display_uri='urn:owned',
                corpus=corpus, access_labels=labels, processing_approved=True,
                redistribution_rights=rights, media_type=media, size=len(data),
                sha256=hashlib.sha256(data).hexdigest(), version=version)


def admit_markdown(store, root, **kwargs):
    (root / kwargs['relative_path']).write_bytes(MARKDOWN.encode('utf-8'))
    obj = source_for(kwargs['logical_id'], kwargs['relative_path'], kwargs['media_type'],
                     **{k: kwargs[k] for k in ('corpus', 'labels', 'version', 'rights')})
    source = parse_manifest(json.dumps(dict(schema_version=1, sources=[obj])).encode()).sources[0]
    return store.admit(root, source)


def make_markdown_store(tmp_path):
    """Two logical documents sharing bytes with distinct rights/ACL/version."""
    root_a, root_b = tmp_path / 'root-a', tmp_path / 'root-b'
    root_a.mkdir()
    root_b.mkdir()
    store = OriginalStore(tmp_path / 'store')
    rev_a = admit_markdown(store, root_a, logical_id='doc-a', relative_path='a.md',
                           media_type='text/markdown', corpus='private-a', labels=['a-label'],
                           version='1.0', rights='prohibited')
    rev_b = admit_markdown(store, root_b, logical_id='doc-b', relative_path='b.txt',
                           media_type='text/plain', corpus='private-b',
                           labels=['b-label', 'b-label-2'], version='2.0', rights='allowed')
    return store, rev_a, rev_b


@pytest.fixture
def runtime():
    if RUNTIME is None or PACKAGES is None or not RUNTIME.is_dir() or not PACKAGES.is_dir():
        raise RuntimeError('Set PDF_TEST_RUNTIME and PDF_TEST_PACKAGES to trusted test paths')
    return pdf.PdfRuntime(RUNTIME, PACKAGES)


def test_shared_bytes_distinct_rights_and_metadata_revision(tmp_path):
    store, rev_a, rev_b = make_markdown_store(tmp_path)
    try:
        text = MARKDOWN.encode('utf-8')
        assert rev_a.revision_id != rev_b.revision_id
        assert rev_a.blob == rev_b.blob == hashlib.sha256(text).hexdigest()
        blob = store.root / 'blobs' / rev_a.blob
        assert blob.is_file() and os.stat(blob).st_mode & 0o777 == 0o600
        assert store.read_original(rev_a.revision_id) == text
        assert store.read_original(rev_b.revision_id) == text
        # Distinct scope/ACL binding over one verified blob.
        scopes = p.catalog((rev_a, rev_b))
        assert [s.corpus for s in scopes] == ['private-a', 'private-b']
        assert [s.labels for s in scopes] == [('a-label',), ('b-label', 'b-label-2')]
        assert [s.redistribution_rights for s in scopes] == ['prohibited', 'allowed']
        assert [s.version for s in scopes] == ['1.0', '2.0']
        # Metadata correction: new revision, same blob, prior revision intact.
        root_c = tmp_path / 'root-c'
        root_c.mkdir()
        rev_a2 = admit_markdown(store, root_c, logical_id='doc-a', relative_path='a.md',
                                media_type='text/markdown', corpus='private-a',
                                labels=['a-label'], version='1.1', rights='prohibited')
        assert rev_a2.revision_id not in (rev_a.revision_id, rev_b.revision_id)
        assert rev_a2.blob == rev_a.blob
        assert store.inspect(rev_a.revision_id).source.version == '1.0'
        assert store.read_original(rev_a2.revision_id) == text
    finally:
        store.close()


def test_native_literal_and_structural_coverage_exact_codepoints(tmp_path):
    store, rev_a, rev_b = make_markdown_store(tmp_path)
    try:
        text = MARKDOWN
        lines = tx.extract(store, rev_a.revision_id)
        assert ''.join(b.text for b in lines.blocks) == text
        expected_anchors = [f'line:{i}' for i in range(1, len(text.splitlines(keepends=True)) + 1)]
        assert [b.anchor for b in lines.blocks] == expected_anchors
        assert lines.blocks[0].kind == 'heading'
        assert lines.blocks[7].kind == 'list'
        assert lines.blocks[10].kind == 'code'
        assert lines.scope.corpus == 'private-a'

        structure = st.extract(store, rev_a.revision_id)
        assert ''.join(b.text for b in structure.blocks) == text
        coverage = structure.coverage
        assert coverage and coverage[0].start == 0 and coverage[-1].end == len(text)
        for earlier, later in zip(coverage, coverage[1:]):
            assert earlier.end == later.start
        for block, cover in zip(structure.blocks, coverage):
            assert text[cover.start:cover.end] == block.text
            assert cover.block_id == block.block_id
        kinds = [b.kind for b in structure.blocks]
        assert kinds == ['heading', 'text', 'text', 'table_header', 'table_row',
                         'text', 'list', 'text', 'code', 'text', 'text']
        header = structure.blocks[kinds.index('table_header')]
        assert header.text == '| Unit | Value |\r\n|---|---|\r\n'
        assert structure.uncertainty

        # Same bytes, plain-text metadata: literal classifier, distinct
        # block identity, no Markdown structure claims.
        plain = st.extract(store, rev_b.revision_id)
        assert ''.join(b.text for b in plain.blocks) == text
        assert plain.coverage[-1].end == len(text)
        assert 'table_header' not in [b.kind for b in plain.blocks]
        assert any(b.kind == 'list' for b in plain.blocks)
        structure_ids = {b.block_id for b in structure.blocks}
        assert plain.blocks and all(b.block_id not in structure_ids for b in plain.blocks)
    finally:
        store.close()


def mixed_pdf():
    """Page 1 native text; page 2 raster image only (visual needed)."""
    text_stream = b'BT /F1 12 Tf 50 700 Td (Owned warning.) Tj ET\n'
    draw_stream = b'q 40 0 0 40 100 100 cm /Im1 Do Q\n'

    def stream(data):
        return b' << /Length %d >>\nstream\n' % len(data) + data + b'endstream'

    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources '
        b'<< /Font << /F1 5 0 R >> >> /Contents 6 0 R >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources '
        b'<< /XObject << /Im1 7 0 R >> >> /Contents 8 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<<' + stream(text_stream),
        b'<< /Type /XObject /Subtype /Image /Width 8 /Height 8 /ColorSpace '
        b'/DeviceGray /BitsPerComponent 8' + stream(b'\x00' * 64),
        b'<<' + stream(draw_stream),
    ]
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


def make_pdf_store(tmp_path):
    data = mixed_pdf()
    root = tmp_path / 'root'
    root.mkdir(parents=True)
    (root / 'doc.pdf').write_bytes(data)
    obj = dict(logical_id='owned-pdf', relative_path='doc.pdf', display_uri='urn:owned',
               corpus='private-c', access_labels=['c-label'], processing_approved=True,
               redistribution_rights='unknown', media_type='application/pdf',
               size=len(data), sha256=hashlib.sha256(data).hexdigest())
    source = parse_manifest(json.dumps(dict(schema_version=1, sources=[obj])).encode()).sources[0]
    store = OriginalStore(tmp_path / 'store')
    return store, store.admit(root, source)


def test_pdf_mixed_pages_bind_into_registry(tmp_path, runtime):
    store, rev_a, _ = make_markdown_store(tmp_path)
    pdf_store, pdf_rev = make_pdf_store(tmp_path / 'pdf-home')
    try:
        result = pdf.extract(pdf_store, pdf_rev.revision_id, runtime)
        assert result.status == 'partial_visual_needed'
        assert result.pages == ((1, 'native_text'), (2, 'visual_needed'))
        assert len(result.blocks) == 1
        block = result.blocks[0]
        assert block.text == 'Owned warning.\n' and block.origin == 'native'
        assert block.page_ref == 'page:1' and block.geometry is not None
        assert pdf.extract(pdf_store, pdf_rev.revision_id, runtime).blocks == result.blocks

        structure = st.extract(store, rev_a.revision_id)
        lines = tx.extract(store, rev_a.revision_id)
        registry = p.Registry((rev_a, pdf_rev),
                              (lines.dependency, structure.dependency, result.dependency),
                              lines.blocks + structure.blocks + result.blocks)
        policy = p.policy_id('combined-owned')

        def chunk_of(dependency, blocks, index):
            target = blocks[index]
            fragment = p.SourceFragment(schema_version=1, kind='source',
                                        block_id=target.block_id, start=0,
                                        end=len(target.text), copied_text=target.text)
            return p.Chunk(schema_version=1, chunk_id='tmp', revision_id=target.revision_id,
                           extraction_id=dependency.extraction_id, policy_id=policy,
                           fragments=(fragment,), text=target.text,
                           text_sha256=target.text_sha256)

        for dependency, blocks, index, corpus in (
                (lines.dependency, lines.blocks, 1, 'private-a'),
                (structure.dependency, structure.blocks, 0, 'private-a'),
                (result.dependency, result.blocks, 0, 'private-c')):
            chunk = chunk_of(dependency, blocks, index)
            chunk = chunk.model_copy(update={'chunk_id': p.chunk_id(chunk)})
            scope = registry.bind_chunk(chunk)
            assert scope.corpus == corpus

        forged = chunk_of(result.dependency, result.blocks, 0)
        foreign = structure.blocks[0]
        forged = forged.model_copy(update={
            'fragments': (p.SourceFragment(schema_version=1, kind='source',
                                           block_id=foreign.block_id, start=0,
                                           end=len(foreign.text), copied_text=foreign.text),)})
        with pytest.raises(p.ProvenanceError):
            registry.bind_chunk(forged)
    finally:
        store.close()
        pdf_store.close()


def test_refusals_malformed_oversized_wrong_hash_unsupported(tmp_path, runtime):
    store, rev_a, _ = make_markdown_store(tmp_path)
    try:
        # Malformed UTF-8: both text adapters refuse without partial output.
        root = tmp_path / 'bad'
        root.mkdir()
        bad = b'# Title\n\xff\xfe not utf-8\n'
        (root / 'bad.md').write_bytes(bad)
        obj = dict(logical_id='bad', relative_path='bad.md', display_uri='urn:owned',
                   corpus='c', access_labels=[], processing_approved=True,
                   redistribution_rights='unknown', media_type='text/markdown',
                   size=len(bad), sha256=hashlib.sha256(bad).hexdigest())
        manifest = json.dumps(dict(schema_version=1, sources=[obj])).encode()
        bad_rev = store.admit(root, parse_manifest(manifest).sources[0])
        with pytest.raises(tx.ExtractionError):
            tx.extract(store, bad_rev.revision_id)
        with pytest.raises(st.StructureError):
            st.extract(store, bad_rev.revision_id)

        # Oversized: policy byte cap below the actual verified size.
        with pytest.raises(tx.ExtractionError):
            tx.extract(store, rev_a.revision_id, tx.ExtractionPolicy(max_bytes=10))
        with pytest.raises(st.StructureError):
            st.extract(store, rev_a.revision_id, st.StructurePolicy(max_bytes=10))

        # Unsupported media: text adapters refuse a PDF; PDF adapter refuses text.
        pdf_store, pdf_rev = make_pdf_store(tmp_path / 'pdf-home')
        try:
            with pytest.raises(tx.ExtractionError):
                tx.extract(pdf_store, pdf_rev.revision_id)
            with pytest.raises(st.StructureError):
                st.extract(pdf_store, pdf_rev.revision_id)
            with pytest.raises(pdf.PdfError):
                pdf.extract(store, rev_a.revision_id, runtime)
        finally:
            pdf_store.close()

        # Wrong hash: corrupting the verified blob defeats all adapters.
        blob = store.root / 'blobs' / rev_a.blob
        blob.write_bytes(b'x' * len(MARKDOWN.encode('utf-8')))
        with pytest.raises(tx.ExtractionError):
            tx.extract(store, rev_a.revision_id)
        with pytest.raises(st.StructureError):
            st.extract(store, rev_a.revision_id)
    finally:
        store.close()


def test_unapproved_source_never_admitted(tmp_path):
    root = tmp_path / 'root'
    root.mkdir()
    data = MARKDOWN.encode('utf-8')
    (root / 'doc.md').write_bytes(data)
    obj = source_for('unapproved', 'doc.md', 'text/markdown', corpus='c', labels=[],
                     version=None, rights='unknown')
    obj['processing_approved'] = False
    source = parse_manifest(json.dumps(dict(schema_version=1, sources=[obj])).encode()).sources[0]
    store = OriginalStore(tmp_path / 'store')
    try:
        with pytest.raises(AdmissionError):
            store.admit(root, source)
    finally:
        store.close()
