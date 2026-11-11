import pytest

from slaif_raggedized_helper import chunking as c


def test_policy_strict():
    for values in ({'target': True}, {'target': 0}, {'target': 9, 'soft_max': 8},
                   {'pair_max': 2, 'query_reserve': 2}):
        with pytest.raises(c.ChunkingError):
            c.Policy(**values)


def test_fixed_error_on_untrusted_inputs():
    with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
        c.build(None, (), None, 'canary secret')
