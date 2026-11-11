from dataclasses import replace
from pathlib import Path

from slaif_raggedized_helper import native_chunking as nc, native_tokenizers as n


def test_definition_identity_binds_all_declarations():
    d = n.Definition(Path('/unused'), '0' * 64, '0.21.4', 'bge_body', 'rev', 'identity')
    baseline = nc._identity(d)
    for changed in (replace(d, sha256='1' * 64), replace(d, backend_version='other'),
                    replace(d, role='bge_representation'), replace(d, model_revision='r2'),
                    replace(d, preprocessing='other')):
        assert nc._identity(changed) != baseline
    assert nc._input_digest('a', None) != nc._input_digest('a', '')
    assert nc._input_digest('é', None) != nc._input_digest('e', None)


def test_receipt_output_ceiling_and_safe_error(monkeypatch):
    import pytest
    monkeypatch.setattr(nc, '_json', lambda value: b'x' * 8_000_001)
    with pytest.raises(nc.NativeChunkingError, match='^native chunk construction refused$'):
        nc.Result((), (), ()).receipts_json()
