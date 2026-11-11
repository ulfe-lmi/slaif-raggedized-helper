import hashlib
import json
import subprocess
import sys

import numpy as np
import pytest

from slaif_raggedized_helper import derived_store, embedding_batch_store as batch
from slaif_raggedized_helper import (
    embedding_job_journal as journal,
    embedding_vectors,
    vector_codec,
)


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fixture():
    h = "a" * 64
    dep = dict.fromkeys(batch._DEPS, h)
    dep["normalization_policy_id"] = embedding_vectors.POLICY_ID
    row = {
        "chunk_id": "c",
        "revision_id": "r",
        "extraction_id": "e",
        "representation_id": "b" * 64,
        "rendered_sha256": h,
        "source_scope_sha256": h,
        "input_sha256": h,
        "token_count": 2,
    }
    p = {
        "format": "embedding-job-plan-v1",
        "purpose": "prepare",
        "dependencies": dep,
        "rows": [row],
        "codec_policy_fingerprint": batch.POLICY.fingerprint(),
    }
    vector = np.zeros((1, 1024), dtype="<f4")
    vector[0, 0] = 1
    encoded = vector_codec.encode(vector, batch.POLICY)
    meta = {
        "schema": 1,
        "kind": "embedding-batch-v1",
        "dependencies": dep,
        "rows": [row],
        "codec_policy_fingerprint": batch.POLICY.fingerprint(),
        "vector_container_sha256": encoded.container_sha256,
        "vector_payload_sha256": encoded.payload_sha256,
    }
    return p, meta, encoded


def test_real_output_and_reopen_process(tmp_path):
    tmp_path.chmod(0o700)
    p, meta, encoded = fixture()
    with derived_store.Store(tmp_path) as store, journal.Journal(tmp_path).own(wire(p)) as handle:
        job = handle.spec.job_id

        def state(status, owner, output=None):
            return {
                "version": 1,
                "job_id": job,
                "status": status,
                "attempt_id": "a1",
                "owner_id": owner,
                "updated_ms": 10000000000000,
                "output": output,
            }

        _, rev = handle.read()
        _, rev = handle.append(wire(state("CLAIMED", handle.owner_id)), None, rev)
        _, rev = handle.append(wire(state("RUNNING", handle.owner_id)), None, rev)
        identifier = batch.publish(store, wire(meta), encoded.container)
        output = {
            "ref": "sha256:" + identifier,
            "fingerprint": "sha256:" + hashlib.sha256(wire(meta)).hexdigest(),
            "availability": "verified",
        }
        attempt = {
            "version": 1,
            "job_id": job,
            "attempt_id": "a1",
            "request_id": None,
            "outcome": "COMPLETE",
            "started_ms": 9999999999999,
            "ended_ms": 10000000000000,
            "input_tokens": None,
            "output_tokens": None,
            "diagnostic_code": None,
            "output": output,
        }
        with pytest.raises(journal.JournalError):
            handle.append(wire(state("COMPLETE", None, output)), wire(attempt), rev)
        wrong_meta = dict(meta, rows=[dict(meta["rows"][0], token_count=3)])
        with pytest.raises(journal.JournalError):
            handle.append(
                wire(state("COMPLETE", None, output)),
                wire(attempt),
                rev,
                store=store,
                metadata_bytes=wire(wrong_meta),
            )
        _, rev = handle.append(
            wire(state("COMPLETE", None, output)),
            wire(attempt),
            rev,
            store=store,
            metadata_bytes=wire(meta),
        )
        assert handle.verified_output(store, wire(meta)).ref == output["ref"]
        changed = dict(meta, rows=[dict(meta["rows"][0], token_count=3)])
        with pytest.raises(journal.JournalError):
            handle.verified_output(store, wire(changed))
    pfile = tmp_path / "plan.json"
    pfile.write_bytes(wire(p))
    (tmp_path / "metadata.json").write_bytes(wire(meta))
    script = (
        "from pathlib import Path\n"
        "from slaif_raggedized_helper import embedding_job_journal as j\n"
        "import sys\np=Path(sys.argv[1])\n"
        "from slaif_raggedized_helper import derived_store\n"
        "with derived_store.Store(p) as store:\n"
        " with j.Journal(p).own((p/'plan.json').read_bytes()) as h:\n"
        "  o=h.verified_output(store, (p/'metadata.json').read_bytes())\n"
        "  print(len(h.read()[0]['events']), o.ref)\n"
    )
    run = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    assert run.stdout.strip() == "4 " + output["ref"]
    with derived_store.Store(tmp_path) as store, journal.Journal(tmp_path).own(wire(p)) as handle:
        assert handle.verified_output(store, wire(meta)).ref == output["ref"]
        (tmp_path / "derived" / "v1" / "objects" / encoded.container_sha256).write_bytes(b"corrupt")
        with pytest.raises(journal.JournalError):
            handle.verified_output(store, wire(meta))


def test_killed_holder_releases_real_lease(tmp_path):
    tmp_path.chmod(0o700)
    p, _, _ = fixture()
    (tmp_path / "plan.json").write_bytes(wire(p))
    script = (
        "from pathlib import Path\n"
        "from slaif_raggedized_helper import embedding_job_journal as j\n"
        "import sys,time\np=Path(sys.argv[1])\n"
        "with j.Journal(p).own((p/'plan.json').read_bytes()):\n"
        " print('owned', flush=True)\n time.sleep(60)\n"
    )
    child = subprocess.Popen(
        [sys.executable, "-u", "-c", script, str(tmp_path)], stdout=subprocess.PIPE, text=True
    )
    try:
        import select

        assert select.select([child.stdout], [], [], 5)[0]
        assert child.stdout.readline().strip() == "owned"
        with pytest.raises(journal.JournalError):
            with journal.Journal(tmp_path).own(wire(p)):
                pass
        child.kill()
        child.wait(timeout=5)
        with journal.Journal(tmp_path).own(wire(p)) as handle:
            assert len(handle.read()[0]["events"]) == 1
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        child.stdout.close()
