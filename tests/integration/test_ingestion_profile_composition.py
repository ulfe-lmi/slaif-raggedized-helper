import dataclasses
import json

from slaif_raggedized_helper import chunking, ingestion_profile


def test_operator_file_roundtrip(tmp_path):
    record = {'artifact': '/toy/artifact', 'sha256': '0' * 64, 'backend_version': '0.21.4',
              'model_revision': 'toy-revision', 'preprocessing': 'toy-preprocessing'}
    document = {'schema_version': 1, 'native_runtime': {'root': '/toy/root',
                'packages': '/toy/packages', 'python': 'python3.14'}, 'bge': record,
                'reranker': record.copy(), 'pdf_runtime': None,
                'chunk_policy': dataclasses.asdict(chunking.Policy())}
    path = tmp_path / 'operator.json'
    raw = json.dumps(document).encode()
    path.write_bytes(raw)
    profile = ingestion_profile.load_profile(path)
    assert profile == ingestion_profile.parse_profile(raw)
    assert profile.bge_body.role == 'bge_body'
    assert profile.bge_representation.role == 'bge_representation'
    assert profile.reranker_pair.role == 'reranker_pair'
