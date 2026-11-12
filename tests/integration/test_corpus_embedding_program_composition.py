import json
import subprocess
import sys
import types
from pathlib import Path
from dataclasses import asdict
from unittest.mock import patch

import pytest

from test_native_tokenizers import make_native
from test_structured_text_composition import create_store
from test_retrieval_representation_composition import make_bundle
from slaif_raggedized_helper import corpus_embedding_program as cp, derived_store, ingestion_store
from slaif_raggedized_helper import native_chunking, retrieval_representation as rr
from slaif_raggedized_helper import chunking, native_chunking as nc, provenance_jsonl as jl
from slaif_raggedized_helper import provenance_records as p, structured_text as st


def test_actual_selected_sources(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    defs = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    originals, revisions = create_store(tmp_path, "# Guide Ž😀\n\n" + "alpha beta gamma. " * 600)
    path = tmp_path / "derived"
    path.mkdir(mode=0o700)
    derived = derived_store.Store(path)
    try:
        bundles = [make_bundle(originals, rev, defs, runtime) for rev in revisions[:2]]
        ids = tuple(
            sorted(ingestion_store.publish(originals, derived, b[0], b[1]) for b in bundles)
        )
        actual = [ingestion_store.load(originals, derived, i) for i in ids]
        with (
            patch.object(native_chunking, "build", side_effect=AssertionError),
            patch.object(rr, "Session", side_effect=AssertionError),
        ):
            value = cp.build(originals, derived, ids, batch_policy=rr.BatchPolicy(max_items=2))
            assert cp.parse(value.program_bytes) == value
            assert cp.validate(originals, derived, value.program_bytes) == value
            assert (
                cp.build(originals, derived, ids, batch_policy=rr.BatchPolicy(max_items=2)) == value
            )
        assert [x for b in value.batches for x in b.chunk_ids] == [
            c.chunk_id for source in actual for c in sorted(source.chunks, key=lambda c: c.chunk_id)
        ]
        assert all(len(b.chunk_ids) <= 2 for b in value.batches)
        assert originals.inspect(revisions[0].revision_id) == revisions[0]
        with pytest.raises(cp.ProgramError):
            cp.build(originals, derived, ids[::-1])
        with pytest.raises(cp.ProgramError):
            cp.build(originals, derived, ids + (ids[-1],))
        assert json.loads(value.program_bytes)["token_eligibility"] == "NOT_RUN"
        with pytest.raises(cp.ProgramError):
            cp.build(
                originals,
                derived,
                ids,
                program_policy=cp.ProgramPolicy(max_rows=value.row_count - 1),
            )
        with pytest.raises(cp.ProgramError):
            cp.build(originals, derived, ids, batch_policy=rr.BatchPolicy(max_total_codepoints=1))
        # The declared byte ceiling participates in the manifest; converge to its exact size.
        ceiling = len(value.program_bytes)
        for _ in range(4):
            sized = cp.build(
                originals,
                derived,
                ids,
                batch_policy=rr.BatchPolicy(max_items=2),
                program_policy=cp.ProgramPolicy(max_program_bytes=ceiling + 100),
            )
            new_ceiling = len(sized.program_bytes)
            if new_ceiling == ceiling:
                break
            ceiling = new_ceiling
        exact = cp.build(
            originals,
            derived,
            ids,
            batch_policy=rr.BatchPolicy(max_items=2),
            program_policy=cp.ProgramPolicy(max_program_bytes=ceiling),
        )
        assert len(exact.program_bytes) == ceiling
        with pytest.raises(cp.ProgramError):
            cp.build(
                originals,
                derived,
                ids,
                batch_policy=rr.BatchPolicy(max_items=2),
                program_policy=cp.ProgramPolicy(max_program_bytes=ceiling - 1),
            )
        with patch.object(ingestion_store, "load", wraps=ingestion_store.load) as load:
            first_count = len(actual[0].chunks)
            with pytest.raises(cp.ProgramError):
                cp.build(
                    originals, derived, ids, program_policy=cp.ProgramPolicy(max_rows=first_count)
                )
            assert load.call_count == 1
        with pytest.raises(cp.ProgramError):
            cp.build(originals, derived, ("f" * 64,))
        blob = tmp_path / "store" / "blobs" / revisions[0].blob
        original_bytes = blob.read_bytes()
        blob.write_bytes(original_bytes + b"corruption")
        try:
            with pytest.raises(cp.ProgramError):
                cp.validate(originals, derived, value.program_bytes)
        finally:
            blob.write_bytes(original_bytes)
        assert cp.validate(originals, derived, value.program_bytes) == value
        # An internally consistent omission remains DATA; fresh comparison must reject it.
        doc = json.loads(value.program_bytes)
        removed = doc["rows"].pop()
        doc["sources"][-1]["row_count"] -= 1
        last = doc["batches"][-1]
        last["row_count"] -= 1
        last["total_codepoints"] -= removed["codepoints"]
        last["total_native_request_bytes"] -= removed["native_request_bytes"]
        if not last["row_count"]:
            doc["batches"].pop()
        candidate = cp._encode(doc)
        assert cp.parse(candidate).row_count == value.row_count - 1
        with pytest.raises(cp.ProgramError):
            cp.validate(originals, derived, candidate)
        # Isolated mutation removes only the final comparison; it still rebuilds real sources.
        module = types.ModuleType("slaif_raggedized_helper._control_corpus")
        module.__package__ = "slaif_raggedized_helper"
        import sys

        sys.modules[module.__name__] = module
        try:
            source = Path(cp.__file__).read_text()
            needle = "if fresh.program_bytes != program_bytes:"
            assert source.count(needle) == 1
            exec(compile(source.replace(needle, "if False:"), cp.__file__, "exec"), module.__dict__)
            assert (
                module.validate(originals, derived, candidate).program_bytes == value.program_bytes
            )
        finally:
            del sys.modules[module.__name__]
        with pytest.raises(cp.ProgramError):
            cp.validate(originals, derived, candidate)
        # Compare the original module from the base with the factored live implementation.
        base = subprocess.check_output(
            [
                "git",
                "show",
                "b0ca5a68f8e55667ada5dd7523903b5585cbe0af:src/slaif_raggedized_helper/retrieval_representation.py",
            ]
        )
        old = types.ModuleType("slaif_raggedized_helper._old_representation")
        old.__package__ = "slaif_raggedized_helper"
        sys.modules[old.__name__] = old
        try:
            exec(compile(base, "<base representation>", "exec"), old.__dict__)
            metadata, members = bundles[0][:2]
            source = ingestion_store.load(
                originals, derived, ingestion_store.publish(originals, derived, metadata, members)
            )
            chunk_ids = tuple(c.chunk_id for c in source.chunks[:2])
            before = old.build_many(originals, metadata, members, chunk_ids, defs[1], runtime)
            after = rr.build_many(originals, metadata, members, chunk_ids, defs[1], runtime)
            for a, b in zip(before, after):
                assert (a.text, a.rendered_sha256, a.representation_id, a.count, a.scope) == (
                    b.text,
                    b.rendered_sha256,
                    b.representation_id,
                    b.count,
                    b.scope,
                )
        finally:
            del sys.modules[old.__name__]
    finally:
        derived.close()
        originals.close()


def make_large_bundle(store, revision, definitions, runtime):
    item = st.extract(store, revision.revision_id)
    registry = p.Registry((revision,), (item.dependency,), item.blocks)
    policy = chunking.Policy(target=8, soft_max=12, pair_max=1280, deadline_ms=15000)
    result = nc.build(registry, item.blocks, *definitions, runtime, "hello", policy)
    declarations = [
        dict(
            role=d.role,
            artifact_sha256=d.sha256,
            backend_version=d.backend_version,
            model_revision=d.model_revision,
            preprocessing=d.preprocessing,
        )
        for d in definitions
    ]
    definition = nc._json(
        dict(
            version=1,
            kind="observed-local-native",
            policy=asdict(policy),
            definitions=[nc._identity(d) for d in definitions],
            query_input_sha256=nc._input_digest("hello", None),
            serialization=nc._SERIALIZATION,
        )
    ).decode()
    metadata = dict(
        schema_version=1,
        kind="native-ingestion-bundle",
        revision_id=revision.revision_id,
        extraction=dict(
            dependency=item.dependency.model_dump(),
            adapter="structured_text",
            status="complete_text",
            coverage_kind="unicode_codepoints",
            uncertainty=item.uncertainty,
        ),
        chunking=dict(
            policy=asdict(policy),
            query="hello",
            definitions=declarations,
            policy_definition=definition,
            policy_id=p.policy_id(definition),
        ),
        counts=dict(
            blocks=len(item.blocks),
            chunks=len(result.chunks),
            neighbors=len(result.chunks),
            receipts=3 * len(result.chunks),
        ),
    )

    def encode(kind, values):
        return jl.encode(kind, tuple(x.model_dump_json().encode() for x in values))

    members = (
        ("blocks", encode("Block", item.blocks)),
        (
            "coverage",
            nc._json(
                dict(
                    schema_version=1,
                    kind="unicode_codepoints",
                    spans=[asdict(x) for x in item.coverage],
                )
            ),
        ),
        ("chunks", encode("Chunk", result.chunks)),
        ("neighbors", encode("Neighbors", result.neighbors)),
        ("receipts", result.receipts_json()),
    )
    return nc._json(metadata), members, item, result


def test_over_128_actual_chunks(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    defs = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    originals, revisions = create_store(
        tmp_path,
        "# Guide\n\n" + "".join(f"Paragraph {i} alpha beta gamma delta.\n\n" for i in range(160)),
    )
    path = tmp_path / "derived"
    path.mkdir(mode=0o700)
    derived = derived_store.Store(path)
    try:
        bundles = [make_large_bundle(originals, rev, defs, runtime) for rev in revisions[:2]]
        ids = tuple(
            sorted(ingestion_store.publish(originals, derived, b[0], b[1]) for b in bundles)
        )
        value = cp.build(originals, derived, ids, batch_policy=rr.BatchPolicy(max_items=50))
        assert value.row_count > 128
        print("actual rows/batches:", value.row_count, value.batch_count)
        assert any(len(b.chunk_ids) < 50 for b in value.batches)
        assert cp.validate(originals, derived, value.program_bytes) == value
        other = make_bundle(originals, revisions[0], defs, runtime)
        duplicate_revision = ingestion_store.publish(originals, derived, other[0], other[1])
        first_id = ingestion_store.publish(originals, derived, bundles[0][0], bundles[0][1])
        with pytest.raises(cp.ProgramError):
            cp.build(originals, derived, tuple(sorted((first_id, duplicate_revision))))
    finally:
        derived.close()
        originals.close()


@pytest.fixture
def boundary_selected(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    defs = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    originals, revisions = create_store(
        tmp_path, "# Actual heading\n\n" + "alpha beta gamma delta. " * 600
    )
    dest = tmp_path / "derived-private"
    dest.mkdir(mode=0o700)
    derived = derived_store.Store(dest)
    try:
        bundles = [make_bundle(originals, v, defs, runtime) for v in revisions[:2]]
        ids = tuple(
            sorted(ingestion_store.publish(originals, derived, b[0], b[1]) for b in bundles)
        )
        yield originals, derived, ids, defs, runtime
    finally:
        derived.close()
        originals.close()


def test_actual_remaining_char_preflight_matches_base(boundary_selected):
    originals, derived, ids, defs, runtime = boundary_selected
    value = ingestion_store.load(originals, derived, ids[0])
    chunks = value.chunks[:2]
    assert len(chunks) == 2
    wanted = tuple(c.chunk_id for c in chunks)
    first = rr._format_raw(
        value.revision.source.title, chunks[0].heading_path, chunks[0].text, rr.Policy()
    )[0]
    base = subprocess.check_output(
        [
            "git",
            "show",
            "b0ca5a68f8e55667ada5dd7523903b5585cbe0af:src/slaif_raggedized_helper/retrieval_representation.py",
        ]
    ).decode()
    module = types.ModuleType("slaif_raggedized_helper._root_before_factor")
    module.__package__ = rr.__package__
    sys.modules[module.__name__] = module
    exec(compile(base, "<root-old-representation>", "exec"), module.__dict__)
    try:
        oldline = next(
            i
            for i, t in enumerate(base.splitlines(), 1)
            if t.strip() == "text = policy.separator.join(components)"
        )
        newsource = Path(rr.__file__).read_text()
        newline = next(
            i
            for i, t in enumerate(newsource.splitlines(), 1)
            if t.strip() == "text = policy.separator.join(components)"
        )
        observed = []
        for api, code, line, bp in [
            (
                module,
                module.build_many.__code__,
                oldline,
                module.BatchPolicy(max_total_codepoints=len(first)),
            ),
            (rr, rr._format_raw.__code__, newline, rr.BatchPolicy(max_total_codepoints=len(first))),
        ]:
            joins = []

            def trace(frame, event, arg):
                if frame.f_code is code and event == "line" and frame.f_lineno == line:
                    joins.append(1)
                return trace

            sys.settrace(trace)
            try:
                with pytest.raises(api.RepresentationError):
                    api.build_many(
                        originals,
                        value.metadata_json,
                        value.members,
                        wanted,
                        defs[1],
                        runtime,
                        batch_policy=bp,
                    )
            finally:
                sys.settrace(None)
            observed.append(len(joins))
        assert observed == [1, 1]
        print("old and factored both join once before refusal")
    finally:
        del sys.modules[module.__name__]


def test_actual_byte_budget_refuses_before_next_source_load(boundary_selected, monkeypatch):
    originals, derived, ids, _, _ = boundary_selected
    bp = rr.BatchPolicy(max_items=2)
    cap = len(cp.build(originals, derived, ids[:1], batch_policy=bp).program_bytes) + 1
    for _ in range(10):
        first = cp.build(
            originals,
            derived,
            ids[:1],
            batch_policy=bp,
            program_policy=cp.ProgramPolicy(max_program_bytes=cap),
        )
        wanted = len(first.program_bytes) + 1
        if wanted == cap:
            break
        cap = wanted
    assert cap == len(first.program_bytes) + 1
    actual = ingestion_store.load
    calls = []

    def observe(*args):
        calls.append(args[2])
        return actual(*args)

    monkeypatch.setattr(ingestion_store, "load", observe)
    with pytest.raises(cp.ProgramError):
        cp.build(
            originals,
            derived,
            ids,
            batch_policy=bp,
            program_policy=cp.ProgramPolicy(max_program_bytes=cap),
        )
    assert calls == list(ids[:1])
    print("next source refused before load at byte boundary")
