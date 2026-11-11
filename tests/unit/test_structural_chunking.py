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


def test_all_policy_fields_reject_nonintegers_and_unbounded_values():
    for field in c.Policy.__dataclass_fields__:
        for value in (True, 1.5, -1, 0, float('nan'), float('inf'), 10**30):
            with pytest.raises(c.ChunkingError, match='^invalid policy$'):
                c.Policy(**{field: value})


def test_deadline_policy_boundaries():
    assert c.Policy().deadline_ms == 5000
    assert c.Policy(deadline_ms=1).deadline_ms == 1
    assert c.Policy(deadline_ms=15000).deadline_ms == 15000
    with pytest.raises(c.ChunkingError):
        c.Policy(deadline_ms=15001)
