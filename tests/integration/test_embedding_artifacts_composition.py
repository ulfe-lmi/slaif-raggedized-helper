import hashlib
import importlib.util
from pathlib import Path

from slaif_raggedized_helper.embedding_artifacts import verify_artifacts


spec = importlib.util.spec_from_file_location(
    "artifact_fixtures", Path(__file__).parents[1] / "unit" / "test_embedding_artifacts.py"
)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def test_inventory_binds_verified_bytes_and_is_root_independent(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    manifest = fixtures.setup_tree(one)
    fixtures.setup_tree(two)
    inventory = verify_artifacts(fixtures.encoded(manifest), one)
    assert verify_artifacts(fixtures.encoded(manifest), two).inventory_id == inventory.inventory_id
    data = b"another synthetic weight"
    (two / "synthetic.safetensors").write_bytes(data)
    descriptor = next(x for x in manifest["files"] if x["role"] == "weights")
    descriptor.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    assert verify_artifacts(fixtures.encoded(manifest), two).inventory_id != inventory.inventory_id
