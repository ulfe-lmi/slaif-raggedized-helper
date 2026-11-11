"""Combined canonical 006 second-slice native counts journey (order 006-b).

Composes the actually merged components in ONE owned store: owned manifest ->
OriginalStore -> native literal line / structural text / isolated fixed PDF
worker -> provenance.Registry -> fixed owned tokenizer Session through
native_chunking.build. The native roles bind exact full body, heading+body and
query-pair inputs with observed artifact SHA, declared revision/preprocessing,
backend, role, mode, serialization and input digests (three receipts per
chunk). Shared bytes retain distinct rights/labels/version; a metadata
revision reuses the verified blob; same-byte chunks keep distinct IDs and
cross-source binding is denied. PDF mixed pages stay partial_visual_needed
with no invented visual coverage. Counts are OBSERVED local native
tokenization of locally generated toy tokenizer artifacts: no deployed-model
equivalence, inference preprocessing parity, serving, hardware, license or
quality claim.

Actual usability limit (observed 2026-11-11, reproducible): the owned Session
accepts at most 1024 count requests per build. A representative-scale
procedure source (7876 characters, 403 blocks) is refused at attempted call
1025 with no chunk/neighbor/receipt output; the refusal is asserted with the
exact observed call count. This limit is a precise observed bound, not a
capacity proof: larger representative documents require the separately
commissioned same-PR native efficiency correction before whole-006
acceptance. Both the native backend and the PDF backend are required here:
the tests fail — they do not skip — when either is absent or unavailable.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))

from test_extraction_combined import mixed_pdf  # noqa: E402
from test_native_tokenizers import make_native  # noqa: E402

from slaif_raggedized_helper import chunking  # noqa: E402
from slaif_raggedized_helper import native_chunking as nc  # noqa: E402
from slaif_raggedized_helper import pdf_extraction as pdf  # noqa: E402
from slaif_raggedized_helper import provenance_records as p  # noqa: E402
from slaif_raggedized_helper import structured_text as st  # noqa: E402
from slaif_raggedized_helper import text_extraction as tx  # noqa: E402
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest  # noqa: E402
from slaif_raggedized_helper.tokenizer_session import Session  # noqa: E402

PDF_RUNTIME = Path(os.environ['PDF_TEST_RUNTIME']) if os.environ.get('PDF_TEST_RUNTIME') else None
PDF_PACKAGES = (Path(os.environ['PDF_TEST_PACKAGES'])
           if os.environ.get('PDF_TEST_PACKAGES') else None)


def sentence(words, prefix):
    return ' '.join(f'{prefix}{j:04d}' for j in range(words)) + '.'


# Astral and combining code points, CRLF endings, a warning with its numbered
# procedure, a pipe table with header and unit, fenced code, a 150-word
# paragraph, then a 1000-word paragraph (one 300-word sentence, one 50-word,
# ten 60-word and one 50-word sentence) that forces sentence splits with
# observed word-boundary overlap (each overlap sentence is 60 tokens, within
# the 64 maximum), and an explicit tail. Every split flush happens with a
# 60-word previous sentence, so the overlap search stays bounded: the
# accepted bridge code searches word-boundary suffixes longest first and each
# candidate costs one body count plus a five-count measure.
LONG_PARA = (''.join(sentence(300, 'long00') + '\r\n')
             + sentence(50, 'long01') + '\r\n'
             + ''.join(sentence(60, f'long{i:02d}') + '\r\n' for i in range(2, 12))
             + sentence(50, 'long12') + '\r\n')
RICH = (
    '# Guide \u017d\u0142\U0001F600\r\n'
    'Intro paragraph with combining e\u0301 and caf\u00e9 \u4e16\u754c.\r\n'
    'WARNING: isolate power before service.\r\n'
    '1. Check 12 V.\r\n'
    '2. If hot, wait until safe.\r\n'
    '\r\n'
    '| Name | Unit |\r\n'
    '| --- | --- |\r\n'
    '| flow | L/s |\r\n'
    '\r\n'
    '```sh\r\n'
    'run --owned\r\n'
    '```\r\n'
    '\r\n'
    + sentence(150, 'intro') + '\r\n'
    + '\r\n'
    + LONG_PARA
    + '\r\n'
    'Tail warning remains.\r\n'
)

# One 700-word sentence: observed pair count 706 exceeds the legacy callback
# fixture default pair 512 and fits the native default full pair 1280.
BUDGET_DOC = '# Big\r\n' + sentence(700, 'bud') + '\r\n'

# Exact representative-scale fixture of the QUAL-006-BUNDLE-SIZES-A evidence:
# 7876 characters, 403 structural blocks, refused at attempted session call
# 1025 before any output.
PROCEDURE = ('# Procedure\n\n'
             + ''.join(f'WARNING {i}: isolate power before service.\n\n'
                       f'1. Check pressure {i} kPa.\n2. If hot, wait until safe.\n\n'
                       for i in range(80))
             + 'Tail: restore power only after inspection.\n')


def admit(store, root, logical_id, path, data, media, corpus, labels, version, rights):
    (root / path).write_bytes(data)
    obj = dict(logical_id=logical_id, relative_path=path, display_uri='urn:owned',
               corpus=corpus, access_labels=labels, processing_approved=True,
               redistribution_rights=rights, media_type=media, size=len(data),
               sha256=hashlib.sha256(data).hexdigest(), version=version)
    source = parse_manifest(json.dumps(dict(schema_version=1, sources=[obj])).encode()).sources[0]
    return store.admit(root, source)


def make_store(tmp_path):
    """One owned store: same-byte rich pair, budget doc and mixed PDF."""
    root = tmp_path / 'root'
    root.mkdir()
    store = OriginalStore(tmp_path / 'store')
    rich = RICH.encode('utf-8')
    rev_a = admit(store, root, 'doc-a', 'a.md', rich, 'text/markdown', 'private-a',
                  ['a-label'], '1.0', 'prohibited')
    rev_c = admit(store, root, 'doc-c', 'c.md', rich, 'text/markdown', 'private-b',
                  ['b-label', 'b-label-2'], '2.0', 'allowed')
    rev_b = admit(store, root, 'doc-budget', 'budget.md',
                  BUDGET_DOC.encode('utf-8'), 'text/markdown',
                  'private-d', ['d-label'], '3.0', 'allowed')
    rev_pdf = admit(store, root, 'doc-pdf', 'doc.pdf', mixed_pdf(), 'application/pdf',
                    'private-c', ['c-label'], '1.0', 'unknown')
    return store, root, (rev_a, rev_c, rev_b, rev_pdf)


@pytest.fixture
def pdf_runtime():
    if (PDF_RUNTIME is None or PDF_PACKAGES is None or not PDF_RUNTIME.is_dir()
            or not PDF_PACKAGES.is_dir()):
        raise RuntimeError('Set PDF_TEST_RUNTIME and PDF_TEST_PACKAGES to trusted test paths')
    return pdf.PdfRuntime(PDF_RUNTIME, PDF_PACKAGES)


@pytest.fixture
def native(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    return paths, runtime, definition


def definitions(paths, definition):
    return (definition(paths[0], 'bge_body'), definition(paths[0], 'bge_representation'),
            definition(paths[1], 'reranker_pair'))


def assert_receipt_bindings(result, defs, query, expected_chunks=None):
    assert len(result.receipts) == 3 * len(result.chunks)
    for chunk in result.chunks:
        rep = ''.join(chunk.heading_path) + chunk.text
        receipts = [r for r in result.receipts if r.chunk_id == chunk.chunk_id]
        assert [r.count.input_sha256 for r in receipts] == [
            nc._input_digest(chunk.text, None), nc._input_digest(rep, None),
            nc._input_digest(query, rep)]
        assert [r.count.count for r in receipts] == [c.count for c in chunk.counts]
        assert [r.count.role for r in receipts] == ['bge_body', 'bge_representation',
                                                    'reranker_pair']
        assert [r.count.mode for r in receipts] == ['single', 'single', 'pair']
        for receipt, definition in zip(receipts, defs):
            count = receipt.count
            assert count.artifact_sha256 == definition.sha256
            assert count.backend_version == '0.21.4'
            assert count.model_revision == definition.model_revision
            assert count.preprocessing == definition.preprocessing
            assert count.serialization == ('utf8-json-v1;no-truncation;no-padding;'
                                           'special-tokens')
            assert receipt.definition_fingerprint == nc._identity(definition)
        assert all(c.provenance.startswith('OBSERVED_LOCAL_NATIVE_TOKENIZATION:')
                   for c in chunk.counts)
    if expected_chunks is not None:
        assert [c.chunk_id for c in result.chunks] == expected_chunks


def assert_exact_block_coverage(item, chunks):
    for block in item.blocks:
        fragments = [f for c in chunks for f in c.fragments
                     if isinstance(f, p.SourceFragment) and f.block_id == block.block_id]
        end = 0
        for fragment in fragments:
            assert fragment.copied_text == block.text[fragment.start:fragment.end]
            end = max(end, fragment.end)
        assert end == len(block.text)


def test_combined_native_extraction_counts_and_chunks(tmp_path, native, pdf_runtime):
    paths, runtime, definition = native
    defs = definitions(paths, definition)
    store, root, (rev_a, rev_c, rev_b, rev_pdf) = make_store(tmp_path)
    try:
        struct_a = st.extract(store, rev_a.revision_id)
        struct_c = st.extract(store, rev_c.revision_id)
        struct_b = st.extract(store, rev_b.revision_id)
        lines_a = tx.extract(store, rev_a.revision_id)
        pdf_result = pdf.extract(store, rev_pdf.revision_id, pdf_runtime)
        assert ''.join(b.text for b in struct_a.blocks) == RICH
        assert ''.join(b.text for b in lines_a.blocks) == RICH
        assert rev_a.blob == rev_c.blob == hashlib.sha256(RICH.encode()).hexdigest()
        assert rev_a.revision_id != rev_c.revision_id

        # Mixed PDF: native text page plus raster page, honest partial status,
        # no visual block invented.
        assert pdf_result.status == 'partial_visual_needed'
        assert pdf_result.pages == ((1, 'native_text'), (2, 'visual_needed'))
        assert len(pdf_result.blocks) == 1
        assert pdf_result.blocks[0].text == 'Owned warning.\n'
        assert pdf_result.blocks[0].origin == 'native'
        assert all(b.origin != 'visual_transcription' for b in pdf_result.blocks)

        registry = p.Registry((rev_a, rev_c, rev_b, rev_pdf),
                              (struct_a.dependency, struct_c.dependency, struct_b.dependency,
                               lines_a.dependency, pdf_result.dependency),
                              struct_a.blocks + struct_c.blocks + struct_b.blocks
                              + lines_a.blocks + pdf_result.blocks)

        result = nc.build(registry, struct_a.blocks, *defs, runtime, 'hello')
        assert_receipt_bindings(result, defs, 'hello')
        assert result == nc.build(registry, struct_a.blocks, *defs, runtime, 'hello')
        assert_exact_block_coverage(struct_a, result.chunks)
        chunks = result.chunks

        # Exact original bytes: fragments reconstruct every block exactly, and
        # the original file is untouched after all native work.
        assert (root / 'a.md').read_bytes() == RICH.encode('utf-8')
        assert (root / 'budget.md').read_bytes() == BUDGET_DOC.encode('utf-8')

        # Structure: warning stays with its procedure; the table row chunk
        # repeats the exact original header with unit; the tail is present and
        # nothing is silently discarded.
        coherent = [c for c in chunks if 'WARNING: isolate power before service.' in c.text
                    and '1. Check 12 V.' in c.text and '2. If hot, wait until safe.' in c.text]
        assert coherent
        table = [c for c in chunks if c.text.startswith('| Name | Unit |\r\n| --- | --- |\r\n')
                 and '| flow | L/s |\r\n' in c.text]
        assert table
        assert chunks[-1].text.endswith('Tail warning remains.\r\n')
        assert all(c.heading_path == ('# Guide \u017d\u0142\U0001F600\r\n',) for c in chunks)
        intro = [c for c in chunks if '\u4e16\u754c' in c.text]
        assert intro and all('caf\u00e9' in c.text and 'e\u0301' in c.text for c in intro)

        # Observed overlap: two whole 60-word sentences (word-boundary ranges
        # strictly inside the long paragraph block) are repeated across chunks,
        # each within the 64-body-token maximum.
        long_block = [b for b in struct_a.blocks
                      if b.kind == 'text' and len(b.text.split()) > 700]
        assert len(long_block) == 1
        long_block = long_block[0]
        range_counts = {}
        for chunk in chunks:
            for f in chunk.fragments:
                if isinstance(f, p.SourceFragment) and f.block_id == long_block.block_id:
                    range_counts[(f.start, f.end)] = range_counts.get((f.start, f.end), 0) + 1
        overlaps = [(rng, n) for rng, n in range_counts.items()
                    if n >= 2 and rng[0] > 0 and rng[1] < len(long_block.text)]
        assert len(overlaps) == 2
        for (start, end), _ in overlaps:
            assert 0 < len(long_block.text[start:end].split()) <= 64

        # Deterministic reciprocal neighbors within the bound chunk set.
        for i, chunk in enumerate(chunks):
            link = result.neighbors[i]
            assert link.chunk_id == chunk.chunk_id
            assert link.previous_chunk_id == (chunks[i - 1].chunk_id if i else None)
            assert link.next_chunk_id == (chunks[i + 1].chunk_id if i + 1 < len(chunks) else None)
        assert registry.bind_neighbors(result.chunks, result.neighbors) == result.neighbors
        for chunk in chunks:
            assert registry.bind_chunk(chunk).corpus == 'private-a'
        assert len(json.loads(result.receipts_json())['receipts']) == 3 * len(chunks)

        # Same bytes, distinct rights/labels/version: distinct chunk identity
        # over the same verified blob, bound to the other scope.
        result_c = nc.build(registry, struct_c.blocks, *defs, runtime, 'hello')
        assert [c.text for c in result_c.chunks] == [c.text for c in chunks]
        assert [c.chunk_id for c in result_c.chunks] != [c.chunk_id for c in chunks]
        scope_c = registry.bind_chunk(result_c.chunks[0])
        assert (scope_c.corpus, scope_c.labels, scope_c.redistribution_rights, scope_c.version) \
            == ('private-b', ('b-label', 'b-label-2'), 'allowed', '2.0')
        forged = result.chunks[0].model_copy(update={'revision_id': rev_c.revision_id})
        forged = forged.model_copy(update={'chunk_id': p.chunk_id(forged)})
        with pytest.raises(p.ProvenanceError):
            registry.bind_chunk(forged)

        # Budget document: the observed full pair (heading+body+query) of 706
        # tokens exceeds the legacy fixture pair 512 and fits the native
        # default full pair 1280; an explicit smaller policy stays strict.
        result_b = nc.build(registry, struct_b.blocks, *defs, runtime, 'hello')
        assert len(result_b.chunks) == 2
        body_chunk = result_b.chunks[-1]
        assert body_chunk.heading_path == ('# Big\r\n',)
        assert body_chunk.text == BUDGET_DOC.split('\r\n', 1)[1]
        assert_receipt_bindings(result_b, defs, 'hello')
        rep_b = ''.join(body_chunk.heading_path) + body_chunk.text
        pair_count = body_chunk.counts[2].count
        assert pair_count > 512
        with Session((defs[2],), runtime) as session_pair:
            assert session_pair.count('reranker_pair', 'hello', rep_b).count == pair_count
        with pytest.raises(nc.NativeChunkingError):
            nc.build(registry, struct_b.blocks, *defs, runtime, 'hello',
                     chunking.Policy(pair_max=pair_count - 1))
        assert nc.build(registry, struct_b.blocks, *defs, runtime, 'hello',
                        chunking.Policy(pair_max=pair_count)).chunks

        # PDF native block through the same observed-count path.
        result_p = nc.build(registry, pdf_result.blocks, *defs, runtime, 'hello')
        assert len(result_p.chunks) == 1
        assert result_p.chunks[0].text == 'Owned warning.\n'
        assert result_p.chunks[0].heading_path == ()
        assert_receipt_bindings(result_p, defs, 'hello')
        assert registry.bind_chunk(result_p.chunks[0]).corpus == 'private-c'

        # Independent re-count of one exact input through a fresh owned
        # session: receipts match actual tokenizer output, not stored values.
        with Session(defs, runtime) as session:
            chunk = chunks[-1]
            rep = ''.join(chunk.heading_path) + chunk.text
            assert session.count('bge_body', chunk.text).count == chunk.counts[0].count
            assert session.count('bge_representation', rep).count == chunk.counts[1].count
            assert session.count('reranker_pair', 'hello', rep).count == chunk.counts[2].count
    finally:
        store.close()


def test_native_pair_special_tokens_independent_artifacts(tmp_path, native):
    paths, runtime, definition = native
    with Session((definition(paths[0], 'reranker_pair'),), runtime) as session_a, \
            Session((definition(paths[1], 'reranker_pair'),), runtime) as session_b:
        first_a = session_a.count('reranker_pair', 'hello', 'caf\u00e9 \u4e16\u754c')
        assert session_a.count('reranker_pair', 'hello', 'caf\u00e9 \u4e16\u754c') == first_a
        assert (first_a.count, session_b.count('reranker_pair', 'hello',
                                               'caf\u00e9 \u4e16\u754c').count) == (6, 7)
        assert (session_a.count('reranker_pair', 'hello', '').count,
                session_b.count('reranker_pair', 'hello', '').count) == (4, 5)
        assert (session_a.count('reranker_pair', '', '').count,
                session_b.count('reranker_pair', '', '').count) == (3, 4)
        assert first_a.input_sha256 == nc._input_digest('hello', 'caf\u00e9 \u4e16\u754c')
        assert first_a.mode == 'pair' and first_a.artifact_sha256 == definition(
            paths[0]).sha256


def test_legacy_callback_pair512_supplied_unverified(tmp_path):
    store, _, (rev_a, _, rev_b, _) = make_store(tmp_path)
    try:
        struct_a = st.extract(store, rev_a.revision_id)
        struct_b = st.extract(store, rev_b.revision_id)
        registry = p.Registry((rev_a, rev_b), (struct_a.dependency, struct_b.dependency),
                              struct_a.blocks + struct_b.blocks)
        counters = chunking.Counters('body-fixture', 'representation-fixture',
                                     'pair-fixture', lambda t: len(t.split()),
                                     lambda t: len(t.split()),
                                     lambda q, t: len(q.split()) + len(t.split()) + 3)
        assert counters.provenance == 'SUPPLIED_UNVERIFIED'
        legacy_rich = chunking.build(registry, struct_a.blocks, counters, 'hello')
        assert legacy_rich.chunks
        assert all(c.provenance.startswith('SUPPLIED_UNVERIFIED:')
                   for chunk in legacy_rich.chunks for c in chunk.counts)
        assert legacy_rich.chunks[-1].text.endswith('Tail warning remains.\r\n')
        with pytest.raises(chunking.ChunkingError, match='^chunk construction refused$'):
            chunking.build(registry, struct_b.blocks, counters, 'hello')
    finally:
        store.close()


def test_native_session_call_budget_refuses_before_output(tmp_path, native, monkeypatch):
    """Representative scale is refused at the exact 1024-call Session budget.

    The observed Session subclass only records counters; it changes no count,
    worker or limit. The refusal returns no chunk, neighbor or receipt output.
    """
    paths, runtime, definition = native
    stats = {}
    original = nc.Session

    class Observed(original):
        def count(self, *args):
            try:
                return super().count(*args)
            finally:
                stats.update(calls=self._calls, input_bytes=self._input,
                             output_bytes=self._output)

    monkeypatch.setattr(nc, 'Session', Observed)
    store, _, revisions = make_store(tmp_path)
    proc_root = tmp_path / 'proc'
    proc_root.mkdir()
    proc_rev = admit(store, proc_root, 'proc', 'p.md', PROCEDURE.encode('utf-8'),
                     'text/markdown', 'private-e', [], '1.0', 'unknown')
    try:
        assert len(PROCEDURE) == 7876
        item = st.extract(store, proc_rev.revision_id)
        assert len(item.blocks) == 403
        registry = p.Registry((proc_rev,), (item.dependency,), item.blocks)
        defs = definitions(paths, definition)
        start = time.monotonic()
        with pytest.raises(nc.NativeChunkingError, match='^native chunk construction refused$'):
            nc.build(registry, item.blocks, *defs, runtime, 'hello')
        assert time.monotonic() - start < 30
        assert stats['calls'] == 1025
        assert stats['input_bytes'] > 0 and stats['output_bytes'] > 0
    finally:
        store.close()
