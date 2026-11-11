import pytest

from slaif_raggedized_helper import retrieval_representation as rr


def test_invalid_inputs_refuse_without_disclosure():
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build(None, b'secret', (), 'secret', None, None)
    with pytest.raises(rr.RepresentationError):
        rr.build(None, b'', (), '', None, None, rr.Policy(max_tokens=1025))


@pytest.mark.parametrize('policy', [
    rr.Policy(max_codepoints=100000.0), rr.Policy(max_request_bytes=200000.0),
    rr.Policy(max_codepoints=True), rr.Policy(max_request_bytes=True),
    rr.Policy(max_tokens=True), rr.Policy(max_tokens=1.0),
    rr.Policy(version='other'), rr.Policy(separator='secret'),
])
def test_invalid_policy_refuses_before_validation(policy, monkeypatch):
    reached = []
    def forbidden(*args):
        reached.append(True)
        raise AssertionError('validation reached')
    monkeypatch.setattr(rr.ingestion_bundle, 'validate', forbidden)
    definition = rr.native_tokenizers.Definition(None, '0' * 64, '0.21.4',
                                                  'bge_representation', 'r', 'p')
    runtime = rr.native_tokenizers.Runtime(None, None)
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build(None, b'secret', (), 'secret', definition, runtime, policy)
    assert not reached
