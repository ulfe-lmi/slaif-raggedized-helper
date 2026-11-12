import hashlib
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
from test_embedding_artifacts import setup_tree, write_config  # noqa: E402
from test_native_tokenizers import make_native  # noqa: E402
from test_retrieval_representation_composition import make_bundle  # noqa: E402
from test_structured_text_composition import create_store  # noqa: E402
from slaif_raggedized_helper import embedding_artifacts, embedding_batch_plan as plan  # noqa: E402
from slaif_raggedized_helper import embedding_batch_store as batch, embedding_space as space  # noqa: E402
from slaif_raggedized_helper import embedding_vectors, ingestion_bundle, native_tokenizers as nt  # noqa: E402
from slaif_raggedized_helper import retrieval_representation as rr, schema  # noqa: E402


@pytest.fixture
def journey(tmp_path):
    paths, runtime, _ = make_native(tmp_path)
    root = tmp_path / "model"
    manifest = setup_tree(root)
    write_config(root, manifest, "tokenizer", paths[0].read_bytes())
    raw = json.dumps(manifest).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    files = {x.role: x for x in inv.files}
    d = schema.EmbeddingDefinition(
        model_name="BAAI/bge-m3",
        checkpoint_revision=inv.model_revision,
        checkpoint_sha256=files["weights"].sha256,
        tokenizer_revision=inv.model_revision,
        pooling="cls",
        dimensions=1024,
    )
    t = nt.Definition(
        root / "tokenizer.json",
        files["tokenizer"].sha256,
        "0.21.4",
        "bge_representation",
        inv.model_revision,
        "identity",
    )
    definitions = (
        replace(t, role="bge_body"),
        t,
        nt.Definition(
            paths[1],
            hashlib.sha256(paths[1].read_bytes()).hexdigest(),
            "0.21.4",
            "reranker_pair",
            inv.model_revision,
            "identity",
        ),
    )
    store, revisions = create_store(tmp_path, "# Heading\n\n" + "hello world. " * 650 + "\n")
    metadata, members, item, result = make_bundle(store, revisions[0], definitions, runtime)
    assert len(result.chunks) >= 2
    args = (
        store,
        metadata,
        members,
        [c.chunk_id for c in result.chunks[:2]],
        raw,
        root,
        d,
        t,
        inv.inventory_id,
        runtime,
    )
    yield args, revisions, definitions, item, result
    store.close()


def test_actual_composition_and_independent_identities(journey):
    args, revisions, definitions, item, result = journey
    store, metadata, members, ids, manifest, root, d, t, inventory, runtime = args
    valid = ingestion_bundle.validate(store, metadata, members)
    admitted = space.admit(manifest, root, d, t, inventory)
    with (
        patch.object(rr.ingestion_bundle, "validate", wraps=ingestion_bundle.validate) as val,
        patch.object(rr, "Session", wraps=rr.Session) as session,
        patch.object(plan.retrieval_representation, "build_many", wraps=rr.build_many) as build,
    ):
        prepared = plan.build(*args)
        assert val.call_count == session.call_count == build.call_count == 1
    assert prepared == plan.build(*args)
    obj = json.loads(prepared.plan_bytes)
    assert (
        prepared.plan_bytes
        == json.dumps(
            obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode()
    )
    policy, bp = rr.Policy(), rr.BatchPolicy()

    def strip(x):
        return x.removeprefix("sha256:")

    assert obj["dependencies"] == dict(
        space_id=admitted.space_id,
        inventory_id=inventory,
        definition_fingerprint=strip(d.fingerprint()),
        execution_fingerprint=strip(
            schema.EmbeddingExecution(definition=d, device="cpu", dtype="fp32").fingerprint()
        ),
        tokenizer_sha256=t.sha256,
        normalization_policy_id=embedding_vectors.POLICY_ID,
        representation_policy_fingerprint=strip(
            schema.fingerprint(
                dict(
                    kind="embedding-representation-policy-v1",
                    policy=asdict(policy),
                    batch_policy=asdict(bp),
                )
            )
        ),
    )
    assert obj["codec_policy_fingerprint"] == batch.POLICY.fingerprint()
    reps = rr.build_many(store, metadata, members, ids, t, runtime)
    for i, (row, rep, chunk) in enumerate(zip(obj["rows"], reps, result.chunks[:2], strict=True)):
        text = "\n\n".join(
            [x for x in [revisions[0].source.title, *chunk.heading_path] if x] + [chunk.text]
        )
        assert prepared.texts[i] == text == rep.text
        identity = dict(
            revision_id=chunk.revision_id,
            extraction_id=chunk.extraction_id,
            chunk_id=chunk.chunk_id,
            source=revisions[0].source.model_dump(mode="json"),
            scope=valid.scope.model_dump(mode="json"),
            variant="raw",
            policy=asdict(policy),
            rendered_sha256=hashlib.sha256(text.encode()).hexdigest(),
        )
        representation_id = hashlib.sha256(
            json.dumps(identity, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert row == dict(
            chunk_id=chunk.chunk_id,
            revision_id=chunk.revision_id,
            extraction_id=chunk.extraction_id,
            representation_id=representation_id,
            rendered_sha256=hashlib.sha256(text.encode()).hexdigest(),
            source_scope_sha256=strip(
                schema.fingerprint(
                    dict(
                        kind="embedding-source-scope-v1", scope=valid.scope.model_dump(mode="json")
                    )
                )
            ),
            input_sha256=hashlib.sha256(
                json.dumps([text, None], ensure_ascii=True, separators=(",", ":")).encode()
            ).hexdigest(),
            token_count=nt.count(t, runtime, text).count,
        )
    assert prepared.spec == plan.embedding_job_journal.make_spec(prepared.plan_bytes)
    spec = prepared.spec.model_dump(mode="json")
    assert spec["inputs"] == [
        dict(
            kind="artifact",
            ref="sha256:" + row["representation_id"],
            fingerprint=schema.fingerprint(dict(kind="embedding-job-row-v1", row=row)),
        )
        for row in obj["rows"]
    ]
    assert spec["configuration"] == dict(
        model="sha256:" + inventory,
        encoder="sha256:" + admitted.space_id,
        runtime="sha256:" + obj["dependencies"]["execution_fingerprint"],
        policy=schema.fingerprint(
            dict(
                kind="embedding-job-policy-v1",
                dependencies=obj["dependencies"],
                codec_policy_fingerprint=obj["codec_policy_fingerprint"],
            )
        ),
        prompt=schema.fingerprint(
            dict(kind="embedding-job-prompt-policy-v1", mode="no-generator-prompt")
        ),
    )
    assert spec["purpose"] == "prepare" and spec["kind"] == "embedding"
    assert prepared.spec.configuration.prompt == schema.fingerprint(
        {"kind": "embedding-job-prompt-policy-v1", "mode": "no-generator-prompt"}
    )
    reversed_plan = plan.build(*args[:3], ids[::-1], *args[4:])
    assert reversed_plan.texts == prepared.texts[::-1]
    assert reversed_plan.spec.job_id != prepared.spec.job_id
    changed = plan.build(*args, batch_policy=rr.BatchPolicy(max_items=127))
    assert changed.spec.job_id != prepared.spec.job_id
    assert plan.build(*args, purpose="evaluate").spec.job_id != prepared.spec.job_id
    assert not list(root.glob("*.vectors"))


def test_refusals_actual_source_and_inventory(journey):
    args, revisions, definitions, _, _ = journey
    store, metadata, members, ids, manifest, root, d, t, inventory, runtime = args
    variants = [
        (*args[:3], [], *args[4:]),
        (*args[:3], ids * 2, *args[4:]),
        (*args[:3], ["foreign"], *args[4:]),
        (None, *args[1:]),
        (store, metadata, members[::-1], *args[3:]),
        (*args[:4], b"bad", *args[5:]),
        (*args[:8], "0" * 64, runtime),
        (*args[:6], d.model_copy(update={"pooling": "mean"}), *args[7:]),
        (*args[:7], replace(t, sha256="0" * 64), *args[8:]),
    ]
    for candidate in variants:
        with pytest.raises(plan.PlanError, match="^embedding batch plan refused$"):
            plan.build(*candidate)
    for name in ("tokenizer.json", "config.json"):
        path = root / name
        original_file = path.read_bytes()
        path.write_bytes(b"tampered")
        try:
            with pytest.raises(plan.PlanError):
                plan.build(*args)
        finally:
            path.write_bytes(original_file)
        assert plan.build(*args).texts
    original = (root / "synthetic.safetensors").read_bytes()
    (root / "synthetic.safetensors").write_bytes(b"tampered")
    with pytest.raises(plan.PlanError):
        plan.build(*args)
    (root / "synthetic.safetensors").write_bytes(original)
    assert plan.build(*args).texts
    foreign_metadata, foreign_members, _, foreign = make_bundle(
        store, revisions[1], definitions, runtime
    )
    with pytest.raises(plan.PlanError):
        plan.build(store, foreign_metadata, foreign_members, ids, *args[4:])
    assert foreign.chunks[0].chunk_id not in ids


def test_late_bad_count_and_space_mismatch(journey, monkeypatch):
    args, _, _, _, _ = journey
    good = rr.build_many(args[0], args[1], args[2], args[3], args[7], args[9])
    assert plan.build(*args).texts

    def invalid_count(*unused):
        return (good[0], replace(good[1], count=replace(good[1].count, count=1)))

    monkeypatch.setattr(rr, "build_many", invalid_count)
    with pytest.raises(plan.PlanError):
        plan.build(*args)
    actual = space.admit(*args[4:9])
    monkeypatch.setattr(space, "admit", lambda *a: replace(actual, tokenizer_sha256="0" * 64))
    monkeypatch.setattr(rr, "build_many", lambda *a: good)
    with pytest.raises(plan.PlanError):
        plan.build(*args)


def test_source_scope_title_and_tamper(journey):
    args, revisions, definitions, _, _ = journey
    store, metadata, members, ids, *rest = args
    baseline = plan.build(*args)
    for revision in revisions[1:]:
        m, parts, _, result = make_bundle(store, revision, definitions, args[9])
        changed = plan.build(store, m, parts, [c.chunk_id for c in result.chunks[:2]], *rest)
        assert changed.spec.job_id != baseline.spec.job_id
        assert (
            json.loads(changed.plan_bytes)["rows"][0]["representation_id"]
            != json.loads(baseline.plan_bytes)["rows"][0]["representation_id"]
        )
    tampered = list(members)
    tampered[0] = (tampered[0][0], tampered[0][1] + b"x")
    with pytest.raises(plan.PlanError):
        plan.build(store, metadata, tuple(tampered), ids, *rest)
    blob = store.root / "blobs" / revisions[0].blob
    raw = blob.read_bytes()
    blob.write_bytes(b"tampered")
    try:
        with pytest.raises(plan.PlanError):
            plan.build(*args)
    finally:
        blob.write_bytes(raw)
    assert plan.build(*args) == baseline


def test_receipt_and_policy_changes_are_causal(journey, monkeypatch):
    args, _, _, _, _ = journey
    baseline = plan.build(*args)
    reps = rr.build_many(args[0], args[1], args[2], args[3], args[7], args[9])
    changed_count = replace(reps[1].count, count=reps[1].count.count - 1)
    assert changed_count.count >= 2
    monkeypatch.setattr(
        rr, "build_many", lambda *a: (reps[0], replace(reps[1], count=changed_count))
    )
    changed = plan.build(*args)
    assert changed.spec.job_id != baseline.spec.job_id
    assert json.loads(changed.plan_bytes)["rows"][1]["token_count"] == changed_count.count
    monkeypatch.setattr(rr, "build_many", lambda *a: (reps[1], reps[0]))
    with pytest.raises(plan.PlanError):
        plan.build(*args)
    monkeypatch.undo()
    exact = rr.Policy(max_tokens=max(x.count.count for x in reps))
    policy_plan = plan.build(*args, representation_policy=exact)
    assert policy_plan.spec.job_id != baseline.spec.job_id
    with pytest.raises(plan.PlanError):
        plan.build(*args, representation_policy=rr.Policy(max_tokens=exact.max_tokens - 1))
    with pytest.raises(plan.PlanError):
        plan.build(*args[:9], nt.Runtime(Path("/missing"), Path("/missing"), "python3.12"))


def test_valid_revision_rebinds_real_inventory_and_native(journey):
    args, revisions, definitions, _, _ = journey
    baseline = plan.build(*args)
    store, _, _, _, manifest, root, definition, tokenizer, _, runtime = args
    updated_manifest = json.loads(manifest)
    updated_manifest["model_revision"] = "b" * 40
    updated_raw = json.dumps(updated_manifest).encode()
    updated_inventory = embedding_artifacts.verify_artifacts(updated_raw, root)
    updated_definition = definition.model_copy(
        update={"checkpoint_revision": "b" * 40, "tokenizer_revision": "b" * 40}
    )
    updated_tokenizer = replace(tokenizer, model_revision="b" * 40)
    updated_defs = tuple(replace(item, model_revision="b" * 40) for item in definitions)
    metadata, members, _, chunks = make_bundle(store, revisions[0], updated_defs, runtime)
    ids = [c.chunk_id for c in chunks.chunks[:2]]
    admitted = space.admit(
        updated_raw, root, updated_definition, updated_tokenizer, updated_inventory.inventory_id
    )
    changed = plan.build(
        store,
        metadata,
        members,
        ids,
        updated_raw,
        root,
        updated_definition,
        updated_tokenizer,
        updated_inventory.inventory_id,
        runtime,
    )
    before = json.loads(baseline.plan_bytes)["dependencies"]
    after = json.loads(changed.plan_bytes)["dependencies"]
    assert after["inventory_id"] == admitted.inventory_id != before["inventory_id"]
    assert after["space_id"] == admitted.space_id != before["space_id"]
    assert after["definition_fingerprint"] == updated_definition.fingerprint()[7:]
    assert after["definition_fingerprint"] != before["definition_fingerprint"]
    assert after["execution_fingerprint"] != before["execution_fingerprint"]
    assert after["tokenizer_sha256"] == before["tokenizer_sha256"]
    assert changed.spec.job_id != baseline.spec.job_id
