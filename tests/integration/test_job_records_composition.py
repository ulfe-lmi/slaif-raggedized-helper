import hashlib

from slaif_raggedized_helper.job_records import JobSpec, admit
from slaif_raggedized_helper.source_admission import OriginalStore, Source


def test_identical_originals_keep_source_rights_and_job_identity(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a").write_bytes(b"synthetic")
    digest = hashlib.sha256(b"synthetic").hexdigest()
    base = dict(
        logical_id="doc",
        relative_path="a",
        display_uri="inert",
        corpus="one",
        access_labels=("private",),
        processing_approved=True,
        redistribution_rights="prohibited",
        media_type="text/plain",
        size=9,
        sha256=digest,
    )
    store = OriginalStore(tmp_path / "store")
    try:
        first = store.admit(root, Source(**base))
        second = store.admit(
            root,
            Source(
                **{
                    **base,
                    "corpus": "two",
                    "access_labels": ("public",),
                    "redistribution_rights": "unknown",
                }
            ),
        )
        assert first.blob == second.blob and first.revision_id != second.revision_id
        assert store.inspect(first.revision_id).source.redistribution_rights == "prohibited"
        assert store.inspect(second.revision_id).source.corpus == "two"
        d = "sha256:" + "1" * 64

        def job(revision):
            return admit(
                JobSpec,
                {
                    "version": 1,
                    "kind": "extraction",
                    "purpose": "prepare",
                    "inputs": [
                        {
                            "kind": "source_revision",
                            "ref": revision.revision_id,
                            "fingerprint": "sha256:" + revision.blob,
                        }
                    ],
                    "configuration": dict(policy=d, model=d, prompt=d, encoder=d, runtime=None),
                },
            )

        assert job(first).job_id != job(second).job_id
    finally:
        store.close()
