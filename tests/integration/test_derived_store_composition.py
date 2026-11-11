import os
import subprocess
import sys

from slaif_raggedized_helper.derived_store import Member, Store
from slaif_raggedized_helper.source_admission import OriginalStore


def test_original_store_and_new_process(tmp_path):
    with_original = OriginalStore(tmp_path)
    with Store(tmp_path) as store:
        ident = store.publish(b'{"source":"opaque"}', (Member("part", b"data"),))
    with_original.close()
    code = (
        "from slaif_raggedized_helper.derived_store import Store; "
        f"s=Store({str(tmp_path)!r}); x=s.load({ident!r}); "
        'assert x.members[0].data == b"data"; s.close()'
    )
    subprocess.run([sys.executable, "-c", code], check=True, env=os.environ.copy())
    assert (tmp_path / "blobs").is_dir() and (tmp_path / "revisions").is_dir()
