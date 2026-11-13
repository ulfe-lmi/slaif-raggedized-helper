"""Preflight and interruption behavior for the catalog boundary."""
import pytest

from slaif_raggedized_helper import raw_snapshot_catalog as catalog


def test_preflight_rejects_before_loader(monkeypatch):
    calls = []
    def forbidden(*args):
        calls.append(True)
        raise AssertionError('loader called')
    monkeypatch.setattr(catalog.raw_snapshot_directory, 'load_directory', forbidden)
    with pytest.raises(catalog.CatalogError, match='^catalog refused$'):
        catalog.load_catalog(None, None, '/private', 'sha256:' + '0' * 64)
    assert calls == []


def test_aggregate_and_duplicate_bounds():
    class Record:
        def __init__(self, value):
            self.value = value
        def model_dump(self, *, mode):
            assert mode == 'json'
            return {'value': self.value}

    budget = catalog._Budget()
    table = {}
    catalog._insert(table, 'a', Record('same'), 1, budget)
    total = budget.total
    catalog._insert(table, 'a', Record('same'), 1, budget)
    assert budget.total == total and len(table) == 1
    with pytest.raises(ValueError):
        catalog._insert(table, 'a', Record('different'), 1, budget)
    with pytest.raises(ValueError):
        catalog._insert(table, 'b', Record('same'), 1, budget)
    budget.total = 32 * 1048576 - 1
    budget.retain(b'x')
    with pytest.raises(ValueError):
        budget.retain(b'x')


def test_catalog_id_budget_boundary():
    budget = catalog._Budget()
    budget.total = 32 * 1048576 - 71
    budget.retain(b'sha256:' + b'0' * 64)
    assert budget.total == 32 * 1048576
    budget = catalog._Budget()
    budget.total = 32 * 1048576 - 70
    with pytest.raises(ValueError):
        budget.retain(b'sha256:' + b'0' * 64)
