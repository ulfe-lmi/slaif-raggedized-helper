import pytest

from slaif_raggedized_helper import retrieval_representation as rr


def test_invalid_inputs_refuse_without_disclosure():
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build(None, b'secret', (), 'secret', None, None)
    with pytest.raises(rr.RepresentationError):
        rr.build(None, b'', (), '', None, None, rr.Policy(max_tokens=1025))
