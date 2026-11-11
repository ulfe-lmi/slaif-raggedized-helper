"""Owned PDFs exercise structural grouping with the installed bounded backends."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))
from test_native_tokenizers import make_native  # noqa: E402
from test_pdf_extraction_composition import configured_runtime, make_store  # noqa: E402
from slaif_raggedized_helper import chunking, native_chunking as nc  # noqa: E402
from slaif_raggedized_helper import native_tokenizers as nt, pdf_extraction as pdf  # noqa: E402
from slaif_raggedized_helper import provenance_records as p  # noqa: E402


def owned_pdf(lines):
    stream = ''.join(
        f'BT /F1 12 Tf 50 {9740-i*25} Td ('
        + line.replace('(', r'\(').replace(')', r'\)') + ') Tj ET\n'
        for i, line in enumerate(lines)
    ).encode()
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 10000] '
               b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length %d >>\nstream\n' % len(stream) + stream + b'endstream']
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


@pytest.mark.parametrize('case', ['small', 'default', 'warning'])
def test_real_structural_chunks(tmp_path, case):
    if case == 'warning':
        lines = ['Other text.', 'WARNING isolate power before reset.',
                 '1. Do not energize.', 'TAILCANARY.']
    else:
        n = 20 if case == 'small' else 300
        width = 2 if case == 'small' else 3
        lines = ['Parameter       Value (kg)', '--------------------------'] + [
            f'Item{i:0{width}d}          {i} kg' for i in range(1, n + 1)
        ] + ['TAILCANARY 99 kg']
    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    store, rev = make_store(tmp_path, owned_pdf(lines))
    try:
        item = pdf.extract(store, rev.revision_id, configured_runtime())
        assert item.status == 'native_text'
        assert all(b.page_ref == 'page:1' and b.geometry is not None for b in item.blocks)
        policy = (chunking.Policy(pair_max=1280, deadline_ms=15000) if case == 'default'
                  else chunking.Policy(target=12, soft_max=20, representation_max=80,
                                       pair_max=100, query_reserve=8, deadline_ms=15000))
        result = nc.build(p.Registry((rev,), (item.dependency,), item.blocks), item.blocks,
                          *defs, runtime, 'query', policy)
        assert len(result.chunks) > 1
        for block in item.blocks:
            covered = set()
            for chunk in result.chunks:
                for fragment in chunk.fragments:
                    if (isinstance(fragment, p.SourceFragment)
                            and fragment.block_id == block.block_id):
                        assert 0 <= fragment.start < fragment.end <= len(block.text)
                        covered.update(range(fragment.start, fragment.end))
            assert covered == set(range(len(block.text)))
        texts = [c.text for c in result.chunks]
        assert any('TAILCANARY' in t for t in texts)
        if case == 'warning':
            combined = 'WARNING isolate power before reset.\n1. Do not energize.'
            counts = (nt.count(defs[0], runtime, combined).count,
                      nt.count(defs[1], runtime, combined).count,
                      nt.count(defs[2], runtime, 'query', combined).count)
            assert 12 < counts[0] <= 20 and counts[1] <= 80 and counts[2] + 8 <= 100
            assert any('WARNING' in t and 'Do not energize.' in t for t in texts)
            assert all('WARNING' not in t for t in texts if 'Other text.' in t)
        else:
            row_chunks = [c for c in result.chunks if 'Item' in c.text]
            assert row_chunks
            header = next(b for b in item.blocks if 'Parameter' in b.text)
            for chunk in row_chunks:
                assert 'Parameter' in chunk.text and 'Value (kg)' in chunk.text
                assert any(isinstance(f, p.SourceFragment) and f.block_id == header.block_id
                           for f in chunk.fragments)
    finally:
        store.close()
