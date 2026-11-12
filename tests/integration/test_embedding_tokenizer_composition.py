"""Standalone composition with an explicitly loaded trusted fixture generator."""
import importlib.util
from dataclasses import replace
from pathlib import Path

from slaif_raggedized_helper.embedding_tokenizer import TokenIDSession
from slaif_raggedized_helper.tokenizer_session import Session


def test_native_count_and_ids_compose(tmp_path):
    fixture = Path(__file__).resolve().parents[1] / 'unit' / 'test_native_tokenizers.py'
    spec = importlib.util.spec_from_file_location('trusted_native_fixture', fixture)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    paths, runtime, definition = module.make_native(tmp_path)
    d = replace(definition(paths[0]), role='bge_representation', model_revision='1' * 40,
                preprocessing='identity')
    with TokenIDSession(d, runtime) as ids, Session((d,), runtime) as counts:
        receipt = ids.encode('hello café 世界')
        count = counts.count(d.role, 'hello café 世界')
        assert receipt.ids == (1, 3, 4, 5, 2)
        assert receipt.count == count.count
        assert receipt.input_sha256 == count.input_sha256
        assert receipt.artifact_sha256 == count.artifact_sha256
