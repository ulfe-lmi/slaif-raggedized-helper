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


def test_independent_processes_converge(tmp_path):
    code = (
        "from slaif_raggedized_helper.derived_store import Store, Member; "
        f"s=Store({str(tmp_path)!r}); "
        "print(s.publish(b'{}', (Member('x', b'concurrent'),))); s.close()"
    )
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        for _ in range(4)
    ]
    results = [p.communicate(timeout=30) for p in processes]
    assert all(p.returncode == 0 for p in processes), results
    assert len({out.strip() for out, _ in results}) == 1
    with Store(tmp_path) as store:
        assert store.load(results[0][0].strip()).members == (Member("x", b"concurrent"),)
