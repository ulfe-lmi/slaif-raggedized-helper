"""ONE actual combined 005 journey: store -> provenance records -> job/attempt DTOs.

Objective 005-b (order: oap/orders/005-b-canonical-provenance-and-jobs.md).
Synthetic and offline: owned disposable root/store, no extraction, no model,
no network, no GPU. Supplied extraction text and token counts are assertions,
not executed parsers or qualified tokenizer measurements.
"""

import hashlib

import pytest

from slaif_raggedized_helper import job_records as j
from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper.source_admission import OriginalStore, Source

# Shared bytes: astral (U+1F600), combining mark (U+0301), CRLF, LF and
# non-ASCII letters. Offsets below are Unicode code points, never bytes.
SHARED = "Řídká hlavička\r\nH😀e\u0301\nposlední".encode("utf-8")
TEXT = SHARED.decode("utf-8")
HEADER = TEXT[:14]  # "Řídká hlavička"
BODY = TEXT[14:]  # "\r\nH😀e\u0301\nposlední"


def digest(name):
    """Inert fixture digest; explicitly not an observed model/encoder identity."""
    return "sha256:" + hashlib.sha256(name.encode()).hexdigest()


def source_a(**changes):
    data = dict(
        display_uri="urn:fixture",
        corpus="public",
        access_labels=(),
        processing_approved=True,
        redistribution_rights="allowed",
        media_type="text/plain",
        size=len(SHARED),
        sha256=hashlib.sha256(SHARED).hexdigest(),
        version="1",
    )
    data.update(changes)
    return Source(logical_id="doc-a", relative_path="a", **data)


def build_store(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a").write_bytes(SHARED)
    (root / "b").write_bytes(SHARED)
    store = OriginalStore(tmp_path / "store")
    b = Source(
        logical_id="doc-b",
        relative_path="b",
        display_uri="urn:fixture-b",
        corpus="private",
        access_labels=("confidential", "internal"),
        processing_approved=True,
        redistribution_rights="prohibited",
        media_type="text/plain",
        size=len(SHARED),
        sha256=hashlib.sha256(SHARED).hexdigest(),
        version=None,  # unknown declared version stays fail-closed
    )
    a1 = store.admit(root, source_a())
    b1 = store.admit(root, b)
    a2 = store.admit(root, source_a(title="corrected", date="2026-11-11"))
    return store, root, a1, b1, a2


def build_registry(a1, b1, a2):
    revisions = (a1, b1, a2)
    defs = ("fixture extraction a", "fixture extraction b", "fixture extraction a")
    deps = tuple(
        p.Dependency(
            schema_version=1,
            revision_id=rev.revision_id,
            extraction_id=p.extraction_id(definition),
            definition=definition,
        )
        for rev, definition in zip(revisions, defs)
    )

    def block(bid, rev, dep, kind, order, text):
        return p.Block(
            schema_version=1,
            block_id=bid,
            revision_id=rev.revision_id,
            extraction_id=dep.extraction_id,
            order=order,
            kind=kind,
            anchor=f"fixture {bid}",
            text=text,
            text_sha256=hashlib.sha256(text.encode()).hexdigest(),
            origin="native",
        )

    blocks = (
        block("h-a1", a1, deps[0], "table_header", 0, HEADER),
        block("t-a1", a1, deps[0], "text", 1, BODY),
        block("t-b1", b1, deps[1], "text", 0, TEXT),
        block("h-a2", a2, deps[2], "table_header", 0, HEADER),
        block("t-a2", a2, deps[2], "text", 1, BODY),
    )
    refs = {"h-a1": HEADER, "t-a1": BODY, "t-b1": TEXT, "h-a2": HEADER, "t-a2": BODY}
    return revisions, deps, blocks, p.Registry(revisions, deps, blocks), refs


def make_chunk(refs, rev, dep, policy, fragments, counts=()):
    text = "".join(f.copied_text if f.kind == "source" else f.text for f in fragments)
    chunk = p.Chunk(
        schema_version=1,
        chunk_id="temporary",
        revision_id=rev.revision_id,
        extraction_id=dep.extraction_id,
        policy_id=policy,
        fragments=fragments,
        text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        counts=counts,
    )
    return chunk.model_copy(update={"chunk_id": p.chunk_id(chunk)})


def src(refs, block_id, start, end):
    return p.SourceFragment(
        schema_version=1,
        kind="source",
        block_id=block_id,
        start=start,
        end=end,
        copied_text=refs[block_id][start:end],
    )


def test_combined_store_provenance_job_journey(tmp_path):
    store, root, a1, b1, a2 = build_store(tmp_path)
    try:
        # One verified shared blob under three distinct metadata revisions.
        assert len(list((tmp_path / "store" / "blobs").iterdir())) == 1
        assert len({a1.revision_id, b1.revision_id, a2.revision_id}) == 3
        assert a1.blob == b1.blob == a2.blob
        for rev in (a1, b1, a2):
            assert store.read_original(rev.revision_id) == SHARED
        assert store.inspect(a2.revision_id).source.title == "corrected"

        revisions, deps, blocks, registry, refs = build_registry(a1, b1, a2)
        scopes = p.catalog(revisions)
        assert scopes[0].labels == () and scopes[1].labels == ("confidential", "internal")
        assert scopes[2].labels == () and scopes[1].version is None
        assert (
            scopes[0].redistribution_rights == "allowed"
            and scopes[1].redistribution_rights == "prohibited"
        )

        policy = p.policy_id("fixture chunk policy v0")
        # Multi-span chunks with explicit separators; the original table header
        # reference is repeated inside the first chunk.
        c1 = make_chunk(
            refs,
            a1,
            deps[0],
            policy,
            (
                src(refs, "h-a1", 0, 14),
                p.Separator(schema_version=1, kind="separator", text="\n"),
                src(refs, "t-a1", 2, 6),
                p.Separator(schema_version=1, kind="separator", text="…"),
                src(refs, "h-a1", 0, 14),
            ),
            counts=(
                p.TokenCount(
                    schema_version=1,
                    availability="available",
                    count=0,
                    provenance="supplied fixture count, not a qualified tokenizer",
                ),
            ),
        )
        c2 = make_chunk(refs, a1, deps[0], policy, (src(refs, "t-a1", 2, 15),))
        c3 = make_chunk(
            refs,
            b1,
            deps[1],
            policy,
            (
                src(refs, "t-b1", 0, 6),
                p.Separator(schema_version=1, kind="separator", text="\r\n"),
                src(refs, "t-b1", 6, 14),
            ),
        )
        assert c1.text == "Řídká hlavička\nH😀e\u0301…Řídká hlavička"
        assert c2.text == "H😀e\u0301\nposlední"
        assert c3.text == "Řídká \r\nhlavička"
        assert c1.counts[0].count == 0 and c1.counts[0].availability == "available"
        assert registry.bind_chunk(c1) == scopes[0]
        assert registry.bind_chunk(c2) == scopes[0]
        assert registry.bind_chunk(c3) == scopes[1]

        # Reciprocal neighbors within the compatible (same revision/policy) set;
        # nulls stay unknown and are never inferred as document ends.
        l1 = p.Neighbors(
            schema_version=1,
            chunk_id=c1.chunk_id,
            previous_chunk_id=None,
            next_chunk_id=c2.chunk_id,
        )
        l2 = p.Neighbors(
            schema_version=1,
            chunk_id=c2.chunk_id,
            previous_chunk_id=c1.chunk_id,
            next_chunk_id=None,
        )
        assert registry.bind_neighbors((c1, c2, c3), (l1, l2)) == (l1, l2)
        conflicting = l2.model_copy(update={"previous_chunk_id": c3.chunk_id})
        with pytest.raises(p.ProvenanceError, match="^invalid neighbor binding$"):
            registry.bind_neighbors((c1, c2, c3), (l1, conflicting))

        # Same-source derived support keeps the revision classification; the
        # label union cannot cross the document/revision boundary.
        derived = p.Derived(
            schema_version=1,
            artifact_id="ctx-a1",
            origin="context",
            target_revision=a1.revision_id,
            support_blocks=("h-a1", "t-a1"),
            text="fixture context, not source evidence",
        )
        assert registry.bind_derived(derived).labels == scopes[0].labels
        for support in ("t-b1", "h-a2"):
            with pytest.raises(p.ProvenanceError):
                registry.bind_derived(derived.model_copy(update={"support_blocks": (support,)}))

        # Pure reader-scope intersection: all-label grants, unknown version and
        # missing label all deny; restrictions only narrow.
        grant_a = p.Grants(schema_version=1, corpora=("public",), versions=("1",), labels=())
        assert p.reader_allows(scopes[0], grant_a)
        assert not p.reader_allows(scopes[1], grant_a)  # corpus/labels deny
        # Unknown declared version fails closed even with corpus and all labels.
        assert not p.reader_allows(scopes[1], p.Grants(
            schema_version=1,
            corpora=("private",),
            versions=("*",),
            labels=("confidential", "internal"),
        ))
        assert not p.reader_allows(scopes[0], None)
        assert not p.reader_allows(
            scopes[0], grant_a, p.Restrictions(schema_version=1, corpora=("other",))
        )
        assert not p.reader_allows(scopes[1], p.Grants(
            schema_version=1,
            corpora=("private",),
            versions=("2",),
            labels=("internal",),  # one required label missing
        ))

        # Job identities bind the real revision fingerprints; shared bytes keep
        # distinct source inputs and job IDs.

        def job_spec(*revisions):
            return j.admit(
                j.JobSpec,
                {
                    "version": 1,
                    "kind": "extraction",
                    "purpose": "prepare",
                    "inputs": [
                        {
                            "kind": "source_revision",
                            "ref": r.revision_id,
                            "fingerprint": "sha256:" + r.blob,
                        }
                        for r in revisions
                    ],
                    "configuration": {
                        "policy": policy,
                        "model": digest("model-not-applicable"),
                        "prompt": digest("prompt-not-applicable"),
                        "encoder": digest("encoder-not-applicable"),
                        "runtime": None,
                    },
                },
            )

        spec_a = job_spec(a1, a2)
        assert spec_a.job_id.startswith("sha256:")
        assert j.admit(j.JobSpec, j.serialize(spec_a)) == spec_a
        assert job_spec(b1).job_id != spec_a.job_id
        assert job_spec(a2, a1).job_id != spec_a.job_id  # input order is meaningful

        def state(job_id, status, attempt=None, owner=None, output=None, time=1):
            return j.admit(
                j.JobState,
                {
                    "version": 1,
                    "job_id": job_id,
                    "status": status,
                    "attempt_id": attempt,
                    "owner_id": owner,
                    "updated_ms": time,
                    "output": output,
                },
            )

        def attempt(job_id, ident, outcome, time, output=None):
            return j.admit(
                j.Attempt,
                {
                    "version": 1,
                    "job_id": job_id,
                    "attempt_id": ident,
                    "request_id": "req-005b-1",
                    "outcome": outcome,
                    "started_ms": time - 1,
                    "ended_ms": time,
                    "input_tokens": 0,
                    "output_tokens": None,
                    "diagnostic_code": None,
                    "output": output,
                },
            )

        # Full transition roundtrip with a verified output REFERENCE: the output
        # is a supplied assertion, not proof an artifact exists.
        out = {
            "ref": digest("artifact-a1"),
            "fingerprint": digest("artifact-a1-bytes"),
            "availability": "verified",
        }
        pending = state(spec_a.job_id, "PENDING")
        claimed = state(spec_a.job_id, "CLAIMED", "att-005b-1", "owner-005b", time=2)
        running = state(spec_a.job_id, "RUNNING", "att-005b-1", "owner-005b", time=3)
        complete = state(spec_a.job_id, "COMPLETE", "att-005b-1", output=out, time=4)
        done_attempt = attempt(spec_a.job_id, "att-005b-1", "COMPLETE", 4, out)
        assert j.transition(pending, claimed) == claimed
        assert j.transition(claimed, running) == running
        assert j.transition(running, complete, done_attempt) == complete
        with pytest.raises(j.RecordError):
            j.transition(running, complete)  # terminal state requires an attempt

        # UNKNOWN_COMPLETION: preserved correlation, no automatic retry path.
        unknown = state(spec_a.job_id, "UNKNOWN_COMPLETION", "att-005b-1", time=4)
        j.transition(
            running, unknown, attempt(spec_a.job_id, "att-005b-1", "UNKNOWN_COMPLETION", 4)
        )
        for target in (
            state(spec_a.job_id, "PENDING"),
            state(spec_a.job_id, "RETRYABLE_FAILED", "att-005b-1"),
        ):
            with pytest.raises(j.RecordError):
                j.transition(unknown, target)

        # Bounded retry: RETRYABLE_FAILED -> PENDING keeps the attempt identity;
        # the next claim must use a different attempt ID.
        job_b = job_spec(b1)
        failed = state(job_b.job_id, "RETRYABLE_FAILED", "att-005b-2", time=4)
        j.transition(
            state(job_b.job_id, "RUNNING", "att-005b-2", "owner-b", time=3),
            failed,
            attempt(job_b.job_id, "att-005b-2", "RETRYABLE_FAILED", 4),
        )
        retry = j.transition(failed, state(job_b.job_id, "PENDING", "att-005b-2", time=5))
        with pytest.raises(j.RecordError):
            j.transition(retry, state(job_b.job_id, "CLAIMED", "att-005b-2", "owner-b", time=6))
        reclaimed = j.transition(
            retry, state(job_b.job_id, "CLAIMED", "att-005b-3", "owner-b", time=6)
        )
        assert reclaimed.attempt_id == "att-005b-3"
    finally:
        store.close()


def test_forged_records_and_wrong_bindings_are_rejected(tmp_path):
    store, root, a1, b1, a2 = build_store(tmp_path)
    try:
        revisions, deps, blocks, registry, refs = build_registry(a1, b1, a2)
        policy = p.policy_id("fixture chunk policy v0")
        good = make_chunk(refs, a1, deps[0], policy, (src(refs, "h-a1", 0, 14),))
        assert registry.bind_chunk(good) is not None
        # Copied text conflicting with the exact block span.
        forged = src(refs, "h-a1", 0, 14).model_copy(update={"copied_text": "forged"})
        with pytest.raises(p.ProvenanceError, match="^invalid chunk binding$"):
            registry.bind_chunk(good.model_copy(update={"fragments": (forged,)}))
        # Out-of-range and boolean offsets; empty span; unknown block.
        for changes in (
            dict(start=0, end=15),
            dict(start=True, end=5),
            dict(start=3, end=3),
            dict(block_id="missing"),
        ):
            fragment = src(refs, "h-a1", 0, 14).model_copy(update=changes)
            with pytest.raises(p.ProvenanceError):
                registry.bind_chunk(good.model_copy(update={"fragments": (fragment,)}))
        # Chunk claiming the wrong revision for its blocks.
        wrong_rev = make_chunk(
            refs,
            b1,
            deps[1],
            policy,
            (src(refs, "h-a1", 0, 2),),
        )
        with pytest.raises(p.ProvenanceError):
            registry.bind_chunk(wrong_rev)
        # Wrong dependency definition and wrong block hash are refused at the registry.
        bad_dep = deps[0].model_copy(update={"definition": "changed"})
        with pytest.raises(p.ProvenanceError):
            p.Registry(revisions, (bad_dep, *deps[1:]), blocks)
        bad_block = blocks[0].model_copy(update={"text_sha256": "0" * 64})
        with pytest.raises(p.ProvenanceError):
            p.Registry(revisions, deps, (bad_block, *blocks[1:]))
    finally:
        store.close()
