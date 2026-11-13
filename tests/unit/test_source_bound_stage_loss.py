"""Controlled logical accounting tests for the private stage binder."""

import pytest

from slaif_raggedized_helper import source_bound_stage_loss as binder


def test_meter_reserves_before_operation_and_never_refunds():
    meter = binder._Meter(work_limit=10, payload_limit=5)
    meter.reserve(3, 2)
    assert (meter.work, meter.payload) == (3, 2)
    with pytest.raises(ValueError):
        meter.reserve(8, 1)
    assert (meter.work, meter.payload) == (3, 2)
    with pytest.raises(ValueError):
        meter.reserve(-1)
    with pytest.raises(ValueError):
        meter.reserve(True)
    assert (meter.work, meter.payload) == (3, 2)


def test_sort_terms_handles_duplicates_and_long_common_prefixes():
    meter = binder._Meter()
    prefix = "x" * 4095
    assert binder._sort_unique_terms((prefix + "z", "a", prefix + "y", "a"), meter) == (
        "a",
        prefix + "y",
        prefix + "z",
    )
    assert meter.work > 8190


def test_sort_refuses_invalid_terms_and_insufficient_reservation():
    with pytest.raises(ValueError):
        binder._sort_unique_terms(("",), binder._Meter())
    with pytest.raises(ValueError):
        binder._sort_unique_terms(("a",), binder._Meter(payload_limit=127))
    assert binder._sort_unique_terms((), binder._Meter()) == ()


def test_canonical_hash_splits_quoted_non_bmp_token(monkeypatch):
    import hashlib
    import json

    value = {"text": "\U0001f600" * 4096}
    expected = hashlib.sha256(
        b"domain\n"
        + json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
            "ascii"
        )
    ).hexdigest()
    real_sha256 = hashlib.sha256
    pieces = []

    class Recorder:
        def __init__(self):
            self.inner = real_sha256()

        def update(self, data):
            pieces.append(len(data))
            self.inner.update(data)

        def hexdigest(self):
            return self.inner.hexdigest()

    monkeypatch.setattr(hashlib, "sha256", Recorder)
    meter = binder._Meter()
    assert binder._canonical_hash(value, b"domain\n", meter, lambda: None) == expected
    assert meter.payload >= 49154
    assert max(pieces) == 49152
    assert 2 in pieces


def test_canonical_hash_refuses_unbounded_values_before_encoding():
    with pytest.raises(ValueError):
        binder._canonical_hash("a" * 4097, b"", binder._Meter(), lambda: None)
    with pytest.raises(ValueError):
        binder._canonical_hash(float("nan"), b"", binder._Meter(), lambda: None)


def test_sorted_term_intersection_including_oov():
    meter = binder._Meter()
    query = binder._sort_unique_terms(("beta", "alpha", "alpha"), meter)
    assert binder._terms_intersect(query, binder._sort_unique_terms(("beta",), meter), meter)
    assert not binder._terms_intersect(query, binder._sort_unique_terms(("gamma",), meter), meter)
    assert not binder._terms_intersect(query, (), meter)


def test_fixed_source_envelope():
    assert binder._source_envelope() == (5888, 6400, 12288, 4986555627809)


def test_input_preflight_rejects_bad_types_and_nonfinite_payload():
    import struct

    ids = ("a" * 64, "sha256:" + "b" * 64, "c" * 64, "d" * 64)
    payload = struct.pack("<1024f", 1.0, *([0.0] * 1023))
    binder._preflight_inputs("/safe/root", b"{}", "case", (), payload, ids, 1, binder._Meter())
    with pytest.raises(ValueError):
        binder._preflight_inputs(
            "/safe/root", b"{}", "case", (), payload, ids, True, binder._Meter()
        )
    bad = struct.pack("<1024f", float("nan"), *([0.0] * 1023))
    with pytest.raises(ValueError):
        binder._preflight_inputs("/safe/root", b"{}", "case", (), bad, ids, 1, binder._Meter())
    with pytest.raises(ValueError):
        binder._preflight_inputs(
            "/safe/../root", b"{}", "case", (), payload, ids, 1, binder._Meter()
        )


def test_dense_trace_rejects_omitted_catalog_row():
    from types import SimpleNamespace

    from slaif_raggedized_helper import raw_dense_search as dense

    partition = "sha256:" + "a" * 64
    chunk = "sha256:" + "b" * 64
    revision = "sha256:" + "c" * 64
    representation = "d" * 64
    source = SimpleNamespace(
        ordinal=0,
        partition_id=partition,
        chunk_id=chunk,
        revision_id=revision,
        representation_id=representation,
    )
    row = dense.DenseTraceRow(0, partition, chunk, revision, representation)
    part = dense.DensePartitionTrace(partition, (0,), (0,), (0,), (0,))
    trace = SimpleNamespace(
        rows=(row,), partitions=(part,), selected_ordinals=(0,), returned_ordinals=(0,)
    )
    hit = dense.Hit(0, partition, chunk, revision, representation, b"s", b"c", 1, 1.0)
    result = SimpleNamespace(
        trace=trace,
        allowed_partition_counts=(dense.PartitionCount(partition, 1, 1, 1),),
        eligible=1,
        selected=1,
        returned=1,
        partition_cap_applied=False,
        global_cap_applied=False,
        hits=(hit,),
    )
    binder._validate_trace_relations(result, (source,), [False] * 4096, binder._Meter(), dense=True)
    with pytest.raises(ValueError):
        binder._validate_trace_relations(
            result, (source, source), [False] * 4096, binder._Meter(), dense=True
        )


def test_fusion_recomputes_dense_then_lexical_and_rejects_score_change():
    from dataclasses import replace
    from types import SimpleNamespace

    from slaif_raggedized_helper import raw_dense_search as dense
    from slaif_raggedized_helper import raw_lexical_search as lexical
    from slaif_raggedized_helper import raw_rank_fusion as fusion

    partition, chunk, revision = ("sha256:" + char * 64 for char in "abc")
    representation = "d" * 64
    dense_hit = dense.Hit(0, partition, chunk, revision, representation, b"s", b"c", 1, 0.5)
    lexical_hit = lexical.Hit(0, partition, chunk, revision, representation, b"s", b"c", 2.0, 1)
    score = 1.0 / 61 + 1.0 / 61
    hit = fusion.Hit(0, partition, chunk, revision, representation, b"s", b"c", 1, 1, score, 1)
    output = fusion.FusionResult(
        "snap",
        "catalog",
        "query",
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
        "COMPLETE",
        "COMPLETE",
        False,
        (hit,),
        1,
        1,
        1,
        1,
        1,
        False,
    )
    result = SimpleNamespace(
        dense=SimpleNamespace(hits=(dense_hit,)),
        lexical=SimpleNamespace(hits=(lexical_hit,)),
        fusion=output,
    )
    rows = (SimpleNamespace(scope_bytes=b"s", chunk_bytes=b"c"),)
    assert binder._validate_fusion(result, rows, "snap", "catalog", "query", binder._Meter()) == (
        0,
    )
    result.fusion = replace(output, hits=(replace(hit, score=0.1),))
    with pytest.raises(ValueError):
        binder._validate_fusion(result, rows, "snap", "catalog", "query", binder._Meter())


def test_authority_intersection_retains_restrictions():
    from slaif_raggedized_helper import provenance_records as provenance
    from slaif_raggedized_helper import text_evaluation_dataset as dataset

    grants = provenance.Grants(
        schema_version=1, corpora=("a", "b"), versions=("1", "2"), labels=("public", "private")
    )
    restrictions = provenance.Restrictions(schema_version=1, corpora=("a",), versions=None)
    scope = dataset.DeclaredScope(corpora=("a",), versions=("2",), labels=("public",))
    original, effective, preserved = binder._admit_authority(
        grants, restrictions, scope, binder._Meter(), lambda: None
    )
    assert original == grants
    assert (effective.corpora, effective.versions, effective.labels) == (
        ("a",),
        ("2",),
        ("public",),
    )
    assert preserved == restrictions


def _controlled_fixture(monkeypatch, *, flat=False, wide=False):
    """Supplied test DTOs only; source delegates never open a store."""
    import dataclasses
    import hashlib
    import json
    import struct
    from types import SimpleNamespace

    import test_declared_stage_geometry as oracle
    import test_raw_snapshot_rows as row_fixture
    from slaif_raggedized_helper import derived_store, provenance_records as p, schema
    from slaif_raggedized_helper import raw_dense_search as dense
    from slaif_raggedized_helper import raw_hybrid_search as hybrid
    from slaif_raggedized_helper import raw_lexical_search as lexical
    from slaif_raggedized_helper import raw_rank_fusion as fusion
    from slaif_raggedized_helper import raw_snapshot_catalog as catalog_module
    from slaif_raggedized_helper import raw_snapshot_files, raw_snapshot_pin, raw_snapshot_rows
    from slaif_raggedized_helper import raw_snapshot_selection, source_bound_ranking as ranking
    from slaif_raggedized_helper import technical_analyzer, text_evaluation_dataset as ds
    from slaif_raggedized_helper import text_evaluation_gold_binding as gold_module
    from slaif_raggedized_helper.source_admission import OriginalStore

    def wire(value, ascii=True):
        return json.dumps(
            value, sort_keys=True, ensure_ascii=ascii, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

    def sha(value):
        return hashlib.sha256(value).hexdigest()

    data = oracle.data(not (flat or wide))
    dataset = ds.admit(data)
    case = dataset.cases[0]
    grants = p.Grants(
        schema_version=1,
        corpora=case.scope.corpora,
        versions=case.scope.versions,
        labels=case.scope.labels,
    )
    authority = sha(wire([grants.model_dump(mode="json"), None], False))
    specs = oracle.rows()
    if flat:
        base = specs
        irrelevant = tuple(oracle.row(10 + i, 20 + i, "irrelevant", 0, 1) for i in range(18))
        raw_specs = (base[0], base[4], *irrelevant, base[1], base[2])
        specs = tuple(
            (oracle.ident(100 + i), rev, ext, fragments)
            for i, (_, rev, ext, fragments) in enumerate(raw_specs)
        )
    if wide:
        base = oracle.rows()
        irrelevant = tuple(oracle.row(10 + i, 20 + i, "irrelevant", 0, 1) for i in range(60))
        raw_specs = (*irrelevant, base[0], base[1], base[2], base[4])
        specs = tuple((oracle.ident(100 + i), rev, ext, fragments)
                      for i, (_, rev, ext, fragments) in enumerate(raw_specs))
    count = len(specs)
    label_choices = [(), (case.scope.labels[0],)] if wide else [()]
    label_choices.sort(key=lambda labels: schema.fingerprint(
        {"schema": 1, "corpus": case.scope.corpora[0], "version": case.scope.versions[0],
         "labels": list(labels)}))
    declarations = []
    scopes = []
    for index, (chunk_id, revision, extraction, _) in enumerate(specs):
        labels = label_choices[index // 32] if wide else ()
        scope = p.Scope(schema_version=1, document_id="doc", revision_id=revision,
                        corpus=case.scope.corpora[0], version=case.scope.versions[0], labels=labels,
                        processing_approved=True, redistribution_rights="unknown")
        scope_wire = scope.model_dump(mode="json")
        scope_id = schema.fingerprint(
            {"kind": "embedding-source-scope-v1", "scope": scope_wire}
        )[7:]
        partition_id = schema.fingerprint({"schema": 1, "corpus": scope.corpus,
                                           "version": scope.version, "labels": list(labels)})
        scopes.append(scope)
        declaration = row_fixture.row(index)
        declaration.update(
            chunk_id=chunk_id,
            revision_id=revision,
            extraction_id=extraction,
            bundle_container_id=format(1000 + int(revision[7:], 16), "064x"),
            source_scope_sha256=scope_id, partition_id=partition_id,
            partition_row=(index % 32 if wide else index),
        )
        declarations.append(declaration)
    mapping = row_fixture.mapping(declarations)
    map_bytes = row_fixture.enc(mapping)
    core = row_fixture.core_for(mapping)
    core["analyzer"]["fingerprint"] = technical_analyzer.analyzer_id()[7:]
    core_bytes = row_fixture.enc(core)
    snapshot = "sha256:" + sha(core_bytes)
    row_map = raw_snapshot_rows.bind(core_bytes, map_bytes)
    term = technical_analyzer.analyze(case.question).terms[0].text
    catalog_rows = []
    for index, (declaration, spec) in enumerate(zip(declarations, specs, strict=True)):
        chunk_id, revision, extraction, fragments = spec
        block, lo, hi = fragments[0]
        scope = scopes[index]
        chunk = p.Chunk(
            schema_version=1,
            chunk_id=chunk_id,
            revision_id=revision,
            extraction_id=extraction,
            policy_id="sha256:" + "a" * 64,
            fragments=(
                p.SourceFragment(
                    schema_version=1,
                    kind="source",
                    block_id=block,
                    start=lo,
                    end=hi,
                    copied_text="x" * (hi - lo),
                ),
            ),
            text="x" * (hi - lo),
            text_sha256="a" * 64,
        )
        terms = ((term if flat or wide or index != 3 else "UNMATCHED", 0, 1, "literal"),)
        catalog_rows.append(
            catalog_module.CatalogRow(
                wire(declaration, False),
                wire(chunk.model_dump(mode="json"), False),
                b"{}",
                wire(scope.model_dump(mode="json"), False),
                b"x",
                declaration["representation_id"],
                bytes(4096),
                terms,
            )
        )
    catalog_rows = tuple(catalog_rows)
    catalog_wire = {
        "version": 1,
        "snapshot_id": snapshot,
        "core": sha(core_bytes),
        "row_map": sha(map_bytes),
        "revisions": [],
        "dependencies": [],
        "blocks": [],
        "rows": [
            [
                sha(r.declaration_bytes),
                sha(r.chunk_bytes),
                sha(r.source_bytes),
                sha(r.scope_bytes),
                sha(r.rendered_bytes),
                r.representation_id,
                sha(r.vector_bytes),
                r.terms,
            ]
            for r in catalog_rows
        ],
    }
    catalog_id = "sha256:" + sha(wire(catalog_wire, False))
    catalog = catalog_module.Catalog(
        snapshot, core_bytes, map_bytes, (), (), (), catalog_rows, catalog_id
    )
    pointer_bytes = wire(
        {
            "schema": 1,
            "kind": "raw-snapshot-selection-data-v1",
            "generation": 1,
            "snapshot_id": snapshot,
            "core_sha256": snapshot[7:],
        }
    )
    pointer = raw_snapshot_selection.parse_pointer(pointer_bytes)
    captured = raw_snapshot_pin.PinData(
        pointer, raw_snapshot_files.BoundSnapshotData(snapshot, core_bytes, row_map, None, ())
    )
    originals, derived = object.__new__(OriginalStore), object.__new__(derived_store.Store)
    owner = object.__new__(raw_snapshot_pin.PinOwner)
    owner.state, owner.originals, owner.derived = "ACTIVE", originals, derived
    owner.op, owner.value = SimpleNamespace(path="/fixture"), captured
    calls = []
    monkeypatch.setattr(
        raw_snapshot_pin.PinOwner, "check", lambda self, **kw: calls.append("pin") or captured
    )
    monkeypatch.setattr(
        catalog_module, "load_catalog", lambda *a, **kw: calls.append("catalog") or catalog
    )
    payload = struct.pack("<1024f", 1.0, *([0.0] * 1023))
    identifiers = ("a" * 64, "sha256:" + "a" * 64, "a" * 64, "a" * 64)
    text_sha, payload_sha = sha(case.question.encode()), sha(payload)
    query = sha(
        wire(
            dict(
                kind="raw-hybrid-query/v1",
                snapshot_id=snapshot,
                catalog_id=catalog_id,
                query_text_sha256=text_sha,
                query_payload_sha256=payload_sha,
                query_space_id=identifiers[0],
                query_definition_fingerprint=identifiers[1],
                query_policy_id=identifiers[2],
                query_execution_fingerprint=identifiers[3],
                authority_sha256=authority,
                dense_k=60,
                lexical_k=60,
                partition_cap=60,
                k=60,
            ),
            False,
        )
    )
    dr = tuple(
        dense.DenseTraceRow(
            d["ordinal"], d["partition_id"], d["chunk_id"], d["revision_id"], d["representation_id"]
        )
        for d in declarations
    )
    lr = tuple(
        lexical.LexicalTraceRow(
            r.ordinal, r.partition_id, r.chunk_id, r.revision_id, r.representation_id
        )
        for r in dr
    )
    all_ids = tuple(range(count))
    matching = all_ids if flat or wide else (0, 1, 2, 4)
    selected_dense = all_ids
    returned_dense = selected_dense[:60]
    selected_lexical = matching
    returned_lexical = selected_lexical[:60]
    partition_ids = tuple(dict.fromkeys(d["partition_id"] for d in declarations))
    dense_parts, lexical_parts = [], []
    dense_counts, lexical_counts = [], []
    for ident in partition_ids:
        eligible = tuple(i for i in all_ids if declarations[i]["partition_id"] == ident)
        matched = tuple(i for i in matching if declarations[i]["partition_id"] == ident)
        d_returned = tuple(i for i in returned_dense if declarations[i]["partition_id"] == ident)
        l_returned = tuple(i for i in returned_lexical if declarations[i]["partition_id"] == ident)
        dense_parts.append(
            dense.DensePartitionTrace(ident, eligible, eligible, eligible[:60], d_returned)
        )
        lexical_parts.append(
            lexical.LexicalPartitionTrace(ident, eligible, matched, matched[:60], l_returned)
        )
        dense_counts.append(
            dense.PartitionCount(ident, len(eligible), len(eligible[:60]), len(d_returned))
        )
        lexical_counts.append(lexical.PartitionCount(
            ident, len(eligible), len(matched), len(matched[:60]), len(l_returned)
        ))
    dp, lp = tuple(dense_parts), tuple(lexical_parts)
    dense_header = dict(
        snapshot_id=snapshot,
        catalog_id=catalog_id,
        query_payload_sha256=payload_sha,
        query_space_id=identifiers[0],
        query_definition_fingerprint=identifiers[1],
        query_policy_id=identifiers[2],
        query_execution_fingerprint=identifiers[3],
        authority_sha256=authority,
    )
    lexical_header = dict(
        snapshot_id=snapshot,
        catalog_id=catalog_id,
        query_text_sha256=text_sha,
        analyzer_fingerprint=core["analyzer"]["fingerprint"],
        backend="bm25s-lucene/0.2.14/2.5.4/1.18.1",
        method="lucene",
        authority_sha256=authority,
    )

    def trace_id(kind, header, trace_rows, parts, selected, returned):
        obj = dict(
            schema=1,
            kind=kind,
            **header,
            k=60,
            partition_cap=60,
            rows=[dataclasses.asdict(r) for r in trace_rows],
            partitions=[dataclasses.asdict(part) for part in parts],
            selected_ordinals=selected,
            returned_ordinals=returned,
        )
        return "sha256:" + sha((kind + "\n").encode() + wire(obj))

    dt = dense.DenseTrace(
        trace_id("slaif-raw-dense-authorized-trace-v1", dense_header, dr, dp,
                 selected_dense, returned_dense),
        **dense_header,
        k=60,
        partition_cap=60,
        rows=dr,
        partitions=dp,
        selected_ordinals=selected_dense,
        returned_ordinals=returned_dense,
    )
    lt = lexical.LexicalTrace(
        trace_id("slaif-raw-lexical-authorized-trace-v1", lexical_header, lr, lp,
                 selected_lexical, returned_lexical),
        **lexical_header,
        k=60,
        partition_cap=60,
        rows=lr,
        partitions=lp,
        selected_ordinals=selected_lexical,
        returned_ordinals=returned_lexical,
    )
    dh = tuple(
        dense.Hit(
            r.ordinal,
            r.partition_id,
            r.chunk_id,
            r.revision_id,
            r.representation_id,
            catalog_rows[r.ordinal].scope_bytes,
            catalog_rows[r.ordinal].chunk_bytes,
            i + 1,
            1.0,
        )
        for i, r in enumerate(dr[:60])
    )
    lh = tuple(
        lexical.Hit(
            i,
            lr[i].partition_id,
            lr[i].chunk_id,
            lr[i].revision_id,
            lr[i].representation_id,
            catalog_rows[i].scope_bytes,
            catalog_rows[i].chunk_bytes,
            1.0,
            rank + 1,
        )
        for rank, i in enumerate(returned_lexical)
    )
    dense_result = dense.DenseResult(
        snapshot,
        catalog_id,
        payload_sha,
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
        dh,
        tuple(dense_counts),
        count,
        len(selected_dense),
        len(returned_dense),
        False,
        len(selected_dense) > len(returned_dense),
        dt,
    )
    lexical_result = lexical.LexicalResult(
        snapshot,
        catalog_id,
        text_sha,
        lexical_header["analyzer_fingerprint"],
        lexical_header["backend"],
        "lucene",
        lh,
        tuple(lexical_counts),
        count,
        len(matching),
        len(selected_lexical),
        len(returned_lexical),
        False,
        len(selected_lexical) > len(returned_lexical),
        lt,
    )
    scored = []
    for i in returned_dense:
        lexical_rank = returned_lexical.index(i) + 1 if i in returned_lexical else None
        score = 1.0 / (61 + i) + (1.0 / (60 + lexical_rank) if lexical_rank else 0.0)
        scored.append((score, i, lexical_rank))
    scored.sort(
        key=lambda value: (
            -value[0],
            dr[value[1]].chunk_id,
            dr[value[1]].revision_id,
            dr[value[1]].representation_id,
        )
    )
    fh = tuple(
        fusion.Hit(
            i,
            dr[i].partition_id,
            dr[i].chunk_id,
            dr[i].revision_id,
            dr[i].representation_id,
            catalog_rows[i].scope_bytes,
            catalog_rows[i].chunk_bytes,
            i + 1,
            lexrank,
            score,
            rank + 1,
        )
        for rank, (score, i, lexrank) in enumerate(scored)
    )
    fused = fusion.FusionResult(
        snapshot,
        catalog_id,
        query,
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
        "COMPLETE",
        "COMPLETE",
        False,
        fh,
        len(returned_dense),
        len(returned_lexical),
        len(returned_dense),
        len(returned_lexical),
        len(fh),
        False,
    )
    result = hybrid.HybridResult(
        snapshot,
        catalog_id,
        query,
        text_sha,
        payload_sha,
        authority,
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
        dense_result,
        lexical_result,
        fused,
    )
    atoms = sorted(
        {
            (a.revision_id, a.extraction_id, a.block_id, a.start, a.end, a.text_sha256)
            for c in dataset.cases
            for req in c.requirements
            for alt in req.alternatives
            for a in alt
        }
    )
    sources = sorted({(atom[0], atom[1]) for atom in atoms})
    bundle_ids = tuple(format(3000 + index, "064x") for index in range(len(sources)))
    source_ids = dict(zip(sources, bundle_ids, strict=True))
    bindings = tuple(
        gold_module.GoldBinding(*atom, (source_ids[(atom[0], atom[1])],)) for atom in atoms
    )
    observations = tuple(
        gold_module.BundleObservation(ident, "f" * 64, source[0], source[1], 5, 50)
        for source, ident in zip(sources, bundle_ids, strict=True)
    )
    gold_wire = dict(
        dataset_id=dataset.dataset_id,
        split_id=dataset.split_id,
        dataset_sha256=sha(data),
        observations=[dataclasses.asdict(item) for item in observations],
        bindings=[dataclasses.asdict(value) for value in bindings],
        case_count=dataset.case_count,
        gold_atom_occurrences=dataset.gold_atom_count,
        distinct_atom_count=len(bindings),
        source_binding_status="ORIGINALS_REVALIDATED_AT_BIND_TIME",
    )
    gold = gold_module.BoundGold(
        dataset.dataset_id,
        dataset.split_id,
        sha(data),
        "sha256:" + sha(b"slaif-text-evaluation-gold-binding-v1\n" + wire(gold_wire)),
        observations,
        bindings,
        dataset.case_count,
        dataset.gold_atom_count,
        len(bindings),
        "ORIGINALS_REVALIDATED_AT_BIND_TIME",
    )
    monkeypatch.setattr(gold_module, "bind", lambda *a, **kw: calls.append("gold") or gold)
    bound_rows = []
    for declaration, spec, catalog_row in zip(declarations, specs, catalog_rows, strict=True):
        fragments = tuple(
            ranking.BoundFragment(block, lo, hi, "a" * 64) for block, lo, hi in spec[3]
        )
        bound_rows.append(
            ranking.BoundRow(
                declaration["ordinal"],
                declaration["partition_id"],
                declaration["chunk_id"],
                declaration["revision_id"],
                declaration["extraction_id"],
                declaration["representation_id"],
                declaration["bundle_container_id"],
                declaration["batch_container_id"],
                sha(catalog_row.scope_bytes),
                fragments,
            )
        )
    binding_wire = dict(
        schema=1,
        kind="slaif-source-bound-supplied-ranking-v1",
        snapshot_id=snapshot,
        catalog_id=catalog_id,
        authority_sha256=authority,
        rows=[dataclasses.asdict(r) for r in bound_rows],
        row_count=count,
        fragment_count=count,
        source_binding_status="ORIGINALS_REVALIDATED_AT_BIND_TIME",
    )
    binding = ranking.BoundRanking(
        "sha256:" + sha(b"slaif-source-bound-supplied-ranking-v1\n" + wire(binding_wire)),
        snapshot,
        catalog_id,
        authority,
        tuple(bound_rows),
        count,
        count,
        "ORIGINALS_REVALIDATED_AT_BIND_TIME",
    )

    def bind_ranking(*args, **kwargs):
        calls.append("ranking")
        assert args[5] == tuple(d["chunk_id"] for d in declarations)
        assert kwargs["grants"] == grants
        return binding

    monkeypatch.setattr(ranking, "bind", bind_ranking)
    return originals, derived, owner, data, bundle_ids, result, payload, identifiers, grants, calls


def test_controlled_full_binder_real_geometry_and_thirteen_lower_calls(monkeypatch):
    from unittest.mock import patch
    from slaif_raggedized_helper import declared_stage_geometry

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    lower = declared_stage_geometry.declared_span_support.score_case
    with patch.object(
        declared_stage_geometry.declared_span_support, "score_case", wraps=lower
    ) as score:
        output = binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert calls == ["pin", "catalog", "pin", "gold", "pin", "ranking", "pin", "pin"]
    assert score.call_count == 13
    assert output.geometry.transitions[3].lost_alternatives == (("R1", 1),)
    assert output.geometry.transitions[3].lost_requirements == ()
    assert output.geometry.source_binding == "UNVERIFIED"
    assert output.chosen_atom_occurrences == 4
    assert output.dataset_atom_occurrences >= output.chosen_atom_occurrences
    assert output.eligible_row_count == 5
    assert "case1" not in repr(output)
    assert "Kako" not in repr(output)
    assert output.gold_eligibility == "NOT_CHECKED"
    assert output.source_status == "OWNED_BINDING_CALLS_ONLY"
    with pytest.raises((AttributeError, TypeError)):
        output.source_status = "QUALIFIED"


def test_controlled_preflight_refuses_before_source_and_preserves_baseexception(monkeypatch):
    from dataclasses import replace
    from slaif_raggedized_helper import raw_snapshot_pin

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    kwargs = dict(
        query_space_id=ids[0],
        query_definition_fingerprint=ids[1],
        query_policy_id=ids[2],
        query_execution_fingerprint=ids[3],
        grants=grants,
    )
    invalid = replace(result, dense=replace(result.dense, eligible=True))
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            invalid,
            payload,
            **kwargs,
        )
    assert calls == []
    sentinel = KeyboardInterrupt()

    def interrupted(*args, **kwargs):
        raise sentinel

    monkeypatch.setattr(raw_snapshot_pin.PinOwner, "check", interrupted)
    with pytest.raises(KeyboardInterrupt) as caught:
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            **kwargs,
        )
    assert caught.value is sentinel


@pytest.mark.parametrize(
    "mutation", ["score", "count", "cap", "header", "authority", "row", "return"]
)
def test_controlled_same_count_and_metadata_tampering_refused(monkeypatch, mutation):
    from dataclasses import replace

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    if mutation == "score":
        hit = replace(result.fusion.hits[0], score=result.fusion.hits[0].score + 0.01)
        result = replace(result, fusion=replace(result.fusion, hits=(hit, *result.fusion.hits[1:])))
    elif mutation == "count":
        result = replace(result, dense=replace(result.dense, eligible=4))
    elif mutation == "cap":
        result = replace(result, dense=replace(result.dense, global_cap_applied=True))
    elif mutation == "header":
        result = replace(result, query_id="0" * 64)
    elif mutation == "authority":
        result = replace(result, authority_sha256="0" * 64)
    elif mutation == "row":
        hit = replace(result.dense.hits[0], chunk_id=result.dense.hits[1].chunk_id)
        result = replace(result, dense=replace(result.dense, hits=(hit, *result.dense.hits[1:])))
    else:
        part = result.dense.trace.partitions[0]
        part = replace(part, returned_ordinals=tuple(reversed(part.returned_ordinals)))
        trace = replace(result.dense.trace, partitions=(part,))
        result = replace(result, dense=replace(result.dense, trace=trace))
    with pytest.raises(binder.StageBindingError, match="^source-bound stage diagnosis refused$"):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert "gold" not in calls


def test_rehashed_omitted_eligible_row_still_refused(monkeypatch):
    import dataclasses
    import hashlib
    import json

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    trace = result.dense.trace
    kept = (0, 1, 2, 3)
    part = dataclasses.replace(
        trace.partitions[0],
        eligible_ordinals=kept,
        ranked_ordinals=kept,
        selected_ordinals=kept,
        returned_ordinals=kept,
    )
    header_names = (
        "snapshot_id",
        "catalog_id",
        "query_payload_sha256",
        "query_space_id",
        "query_definition_fingerprint",
        "query_policy_id",
        "query_execution_fingerprint",
        "authority_sha256",
    )
    header = {name: getattr(trace, name) for name in header_names}
    obj = dict(
        schema=1,
        kind="slaif-raw-dense-authorized-trace-v1",
        **header,
        k=60,
        partition_cap=60,
        rows=[dataclasses.asdict(row) for row in trace.rows[:4]],
        partitions=[dataclasses.asdict(part)],
        selected_ordinals=kept,
        returned_ordinals=kept,
    )
    encoded = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    identity = (
        "sha256:" + hashlib.sha256(b"slaif-raw-dense-authorized-trace-v1\n" + encoded).hexdigest()
    )
    trace = dataclasses.replace(
        trace,
        trace_id=identity,
        rows=trace.rows[:4],
        partitions=(part,),
        selected_ordinals=kept,
        returned_ordinals=kept,
    )
    count = dataclasses.replace(
        result.dense.allowed_partition_counts[0], eligible=4, selected=4, returned=4
    )
    dense = dataclasses.replace(
        result.dense,
        trace=trace,
        hits=result.dense.hits[:4],
        allowed_partition_counts=(count,),
        eligible=4,
        selected=4,
        returned=4,
    )
    result = dataclasses.replace(result, dense=dense)
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert "gold" not in calls


def test_controlled_flat_denominator_and_rank_21(monkeypatch):
    from unittest.mock import patch
    from slaif_raggedized_helper import declared_stage_geometry

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch, flat=True)
    )
    lower = declared_stage_geometry.declared_span_support.score_case
    with patch.object(
        declared_stage_geometry.declared_span_support, "score_case", wraps=lower
    ) as score:
        output = binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    twenty, sixty = output.geometry.prefixes[:2]
    assert twenty.completion.recall == 1 / 3
    assert twenty.coverage.covered_requirement_ids == ("R2",)
    assert sixty.completion.recall == 1
    assert sixty.coverage.covered_requirement_ids == ("R1", "R2")
    assert score.call_count == 13
    assert calls == ["pin", "catalog", "pin", "gold", "pin", "ranking", "pin", "pin"]


def test_controlled_withdrawal_and_restoration_are_sequential(monkeypatch):
    from slaif_raggedized_helper import raw_snapshot_pin

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    captured = owner.value
    state = {"checks": 0, "withdrawn": True}

    def check(self, **kwargs):
        state["checks"] += 1
        if state["withdrawn"] and state["checks"] == 3:
            raise ValueError("controlled withdrawal")
        return captured

    monkeypatch.setattr(raw_snapshot_pin.PinOwner, "check", check)
    kwargs = dict(
        query_space_id=ids[0],
        query_definition_fingerprint=ids[1],
        query_policy_id=ids[2],
        query_execution_fingerprint=ids[3],
        grants=grants,
    )
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            **kwargs,
        )
    assert state["checks"] == 3
    state.update(checks=0, withdrawn=False)
    output = binder.bind_stages(
        originals, derived, "/fixture", owner, data, "case1", gold_ids, result, payload, **kwargs
    )
    assert state["checks"] == 5
    state["withdrawn"] = True  # No assertion about changes after the final observation.
    assert output.temporal == "SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC"


def test_rehashed_omitted_lexical_match_still_refused(monkeypatch):
    import dataclasses
    import hashlib
    import json

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    trace = result.lexical.trace
    kept = trace.selected_ordinals[:-1]
    part = dataclasses.replace(
        trace.partitions[0], ranked_ordinals=kept, selected_ordinals=kept, returned_ordinals=kept
    )
    names = (
        "snapshot_id",
        "catalog_id",
        "query_text_sha256",
        "analyzer_fingerprint",
        "backend",
        "method",
        "authority_sha256",
    )
    header = {name: getattr(trace, name) for name in names}
    obj = dict(
        schema=1,
        kind="slaif-raw-lexical-authorized-trace-v1",
        **header,
        k=60,
        partition_cap=60,
        rows=[dataclasses.asdict(row) for row in trace.rows],
        partitions=[dataclasses.asdict(part)],
        selected_ordinals=kept,
        returned_ordinals=kept,
    )
    encoded = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    identity = (
        "sha256:" + hashlib.sha256(b"slaif-raw-lexical-authorized-trace-v1\n" + encoded).hexdigest()
    )
    trace = dataclasses.replace(
        trace, trace_id=identity, partitions=(part,), selected_ordinals=kept, returned_ordinals=kept
    )
    count = dataclasses.replace(result.lexical.partitions[0], matching=3, selected=3, returned=3)
    lexical = dataclasses.replace(
        result.lexical,
        trace=trace,
        hits=result.lexical.hits[:3],
        partitions=(count,),
        matching=3,
        selected=3,
        returned=3,
    )
    result = dataclasses.replace(result, lexical=lexical)
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert "gold" not in calls


def test_old_active_pin_does_not_consult_current_selection(monkeypatch):
    from slaif_raggedized_helper import raw_snapshot_selection

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )

    def forbidden(*args, **kwargs):
        pytest.fail("current selection must not be read")

    monkeypatch.setattr(raw_snapshot_selection._Operation, "pointer", forbidden)
    output = binder.bind_stages(
        originals,
        derived,
        "/fixture",
        owner,
        data,
        "case1",
        gold_ids,
        result,
        payload,
        query_space_id=ids[0],
        query_definition_fingerprint=ids[1],
        query_policy_id=ids[2],
        query_execution_fingerprint=ids[3],
        grants=grants,
    )
    assert output.generation == 1
    assert calls.count("pin") == 5


def test_expiration_after_final_constructor_refuses(monkeypatch):
    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    constructor = binder._Diagnosis

    def construct_then_expire(*args, **kwargs):
        value = constructor(*args, **kwargs)

        def expired(self):
            raise ValueError

        monkeypatch.setattr(binder._Deadline, "check", expired)
        return value

    monkeypatch.setattr(binder, "_Diagnosis", construct_then_expire)
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert calls == ["pin", "catalog", "pin", "gold", "pin", "ranking", "pin", "pin"]


@pytest.mark.parametrize("change", ["count", "unrelated", "status"])
def test_controlled_gold_substitution_refused_before_ranking(monkeypatch, change):
    from dataclasses import replace

    from slaif_raggedized_helper import text_evaluation_gold_binding as gold_module

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    source_fake = gold_module.bind

    def substituted(*args, **kwargs):
        value = source_fake(*args, **kwargs)
        if change == "count":
            return replace(value, gold_atom_occurrences=value.gold_atom_occurrences - 1)
        if change == "status":
            return replace(value, source_binding_status="NO_GOLD_SOURCE_VALIDATED")
        atom = replace(value.bindings[-1], text_sha256="0" * 64)
        return replace(value, bindings=(*value.bindings[:-1], atom))

    monkeypatch.setattr(gold_module, "bind", substituted)
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert "gold" in calls
    assert "ranking" not in calls


def test_meter_string_comparison_hand_calculated():
    meter = binder._Meter(work_limit=20)
    assert meter.compare_strings("ab", "ac") == -1
    assert meter.work == 5
    assert meter.compare_strings("x", "x") == 0
    assert meter.work == 11
    with pytest.raises(ValueError):
        meter.compare_strings("long", "long")
    assert meter.work == 20
    assert meter.categories["string_compare"] == [20, 0]


def test_meter_exhaustion_precedes_any_controlled_source_call(monkeypatch):
    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    meter_type = binder._Meter
    monkeypatch.setattr(binder, "_Meter", lambda: meter_type(work_limit=1))
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert calls == []


def test_canonical_depth_exhaustion_is_bounded():
    value = 0
    for _ in range(18):
        value = [value]
    with pytest.raises(ValueError):
        binder._canonical_hash(value, b"", binder._Meter(), lambda: None)


def test_no_gold_binding_is_distinct_from_nonzero_gold():
    import hashlib
    import json

    import test_declared_stage_geometry as oracle
    from slaif_raggedized_helper import text_evaluation_dataset as dataset_module
    from slaif_raggedized_helper import text_evaluation_gold_binding as gold_module

    empty_object = json.loads(oracle.data(empty=True))
    for case in empty_object["cases"]:
        case["requirements"] = []
        case["answerability"] = "unknown"
    empty_data = json.dumps(
        empty_object, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")
    empty = dataset_module.admit(empty_data)
    assert empty.gold_atom_count == 0
    dataset_sha = hashlib.sha256(empty_data).hexdigest()
    body = {
        "dataset_id": empty.dataset_id,
        "split_id": empty.split_id,
        "dataset_sha256": dataset_sha,
        "observations": [],
        "bindings": [],
        "case_count": empty.case_count,
        "gold_atom_occurrences": 0,
        "distinct_atom_count": 0,
        "source_binding_status": "NO_GOLD_SOURCE_VALIDATED",
    }
    encoded = json.dumps(body, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    binding_id = "sha256:" + hashlib.sha256(
        b"slaif-text-evaluation-gold-binding-v1\n" + encoded
    ).hexdigest()
    gold = gold_module.BoundGold(
        empty.dataset_id,
        empty.split_id,
        dataset_sha,
        binding_id,
        (),
        (),
        empty.case_count,
        0,
        0,
        "NO_GOLD_SOURCE_VALIDATED",
    )
    binder._validate_gold(gold, empty, empty_data, (), binder._Meter(), lambda: None)
    nonzero_data = oracle.data()
    nonzero = dataset_module.admit(nonzero_data)
    with pytest.raises(ValueError):
        binder._validate_gold(gold, nonzero, nonzero_data, (), binder._Meter(), lambda: None)


def test_denied_scope_keeps_nonzero_gold_denominator(monkeypatch):
    import dataclasses
    import hashlib
    import json

    from slaif_raggedized_helper import provenance_records as p
    from slaif_raggedized_helper import source_bound_ranking as ranking

    originals, derived, owner, data, gold_ids, result, payload, ids, _, calls = (
        _controlled_fixture(monkeypatch)
    )

    def wire(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()

    def digest(value):
        return hashlib.sha256(value).hexdigest()

    grants = p.Grants(schema_version=1, corpora=(), versions=(), labels=())
    authority = digest(wire([grants.model_dump(mode="json"), None]))
    query_wire = {
        "kind": "raw-hybrid-query/v1", "snapshot_id": result.snapshot_id,
        "catalog_id": result.catalog_id, "query_text_sha256": result.query_text_sha256,
        "query_payload_sha256": result.query_payload_sha256, "query_space_id": ids[0],
        "query_definition_fingerprint": ids[1], "query_policy_id": ids[2],
        "query_execution_fingerprint": ids[3], "authority_sha256": authority,
        "dense_k": 60, "lexical_k": 60, "partition_cap": 60, "k": 60,
    }
    query = digest(wire(query_wire))

    def empty_trace(trace, dense):
        kind = (
            "slaif-raw-dense-authorized-trace-v1" if dense
            else "slaif-raw-lexical-authorized-trace-v1"
        )
        names = (("snapshot_id", "catalog_id", "query_payload_sha256", "query_space_id",
                  "query_definition_fingerprint", "query_policy_id", "query_execution_fingerprint")
                 if dense else ("snapshot_id", "catalog_id", "query_text_sha256",
                                "analyzer_fingerprint", "backend", "method"))
        obj = {name: getattr(trace, name) for name in names}
        obj.update(schema=1, kind=kind, authority_sha256=authority, k=60, partition_cap=60,
                   rows=[], partitions=[], selected_ordinals=[], returned_ordinals=[])
        identity = "sha256:" + digest((kind + "\n").encode() + wire(obj))
        return dataclasses.replace(
            trace, trace_id=identity, authority_sha256=authority, rows=(), partitions=(),
            selected_ordinals=(), returned_ordinals=(),
        )

    dense = dataclasses.replace(result.dense, hits=(), allowed_partition_counts=(), eligible=0,
                                selected=0, returned=0, trace=empty_trace(result.dense.trace, True))
    lexical = dataclasses.replace(
        result.lexical, hits=(), partitions=(), eligible=0, matching=0, selected=0, returned=0,
        trace=empty_trace(result.lexical.trace, False),
    )
    fusion = dataclasses.replace(result.fusion, query_id=query, hits=(), dense_input_rows=0,
                                 lexical_input_rows=0, unique_candidates=0, overlap_candidates=0,
                                 returned=0)
    result = dataclasses.replace(result, query_id=query, authority_sha256=authority,
                                 dense=dense, lexical=lexical, fusion=fusion)
    bound_wire = {"schema": 1, "kind": "slaif-source-bound-supplied-ranking-v1",
                  "snapshot_id": result.snapshot_id, "catalog_id": result.catalog_id,
                  "authority_sha256": authority, "rows": [], "row_count": 0,
                  "fragment_count": 0, "source_binding_status": "NO_SELECTED_SOURCE_VALIDATED"}
    binding_id = "sha256:" + digest(b"slaif-source-bound-supplied-ranking-v1\n" + wire(bound_wire))
    bound = ranking.BoundRanking(binding_id, result.snapshot_id, result.catalog_id, authority,
                                 (), 0, 0, "NO_SELECTED_SOURCE_VALIDATED")
    def empty_binding(*args, **kwargs):
        calls.append("ranking")
        assert args[5] == ()
        return bound
    monkeypatch.setattr(ranking, "bind", empty_binding)
    output = binder.bind_stages(
        originals, derived, "/fixture", owner, data, "case1", gold_ids, result, payload,
        query_space_id=ids[0], query_definition_fingerprint=ids[1], query_policy_id=ids[2],
        query_execution_fingerprint=ids[3], grants=grants,
    )
    assert "gold" in calls and "ranking" in calls
    assert output.geometry.stages[0].coverage.requirement_fraction == 0
    assert (output.geometry.stages[0].completion.undefined_reason
            == "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE")
    assert output.geometry.stages[0].completion.recall is None


def test_fusion_equal_scores_use_identifier_tie_order():
    from dataclasses import replace
    from types import SimpleNamespace

    from slaif_raggedized_helper import raw_dense_search as dense
    from slaif_raggedized_helper import raw_lexical_search as lexical
    from slaif_raggedized_helper import raw_rank_fusion as fusion

    partition = "sha256:" + "a" * 64
    revision = "sha256:" + "b" * 64
    chunks = ("sha256:" + "1" * 64, "sha256:" + "2" * 64)
    reps = ("3" * 64, "4" * 64)
    dense_hits = tuple(
        dense.Hit(i, partition, chunks[i], revision, reps[i], b"s", b"c", i + 1, 1.0)
        for i in range(2)
    )
    lexical_hits = tuple(
        lexical.Hit(i, partition, chunks[i], revision, reps[i], b"s", b"c", 1.0, rank)
        for rank, i in enumerate((1, 0), 1)
    )
    score = 1 / 61 + 1 / 62
    hits = (
        fusion.Hit(0, partition, chunks[0], revision, reps[0], b"s", b"c", 1, 2, score, 1),
        fusion.Hit(1, partition, chunks[1], revision, reps[1], b"s", b"c", 2, 1, score, 2),
    )
    output = fusion.FusionResult(
        "snap", "catalog", "query", "SUPPLIED_UNVERIFIED", "NOT_QUALIFIED",
        "COMPLETE", "COMPLETE", False, hits, 2, 2, 2, 2, 2, False,
    )
    result = SimpleNamespace(
        dense=SimpleNamespace(hits=dense_hits), lexical=SimpleNamespace(hits=lexical_hits),
        fusion=output,
    )
    rows = (SimpleNamespace(scope_bytes=b"s", chunk_bytes=b"c"),) * 2
    assert binder._validate_fusion(
        result, rows, "snap", "catalog", "query", binder._Meter()
    ) == (0, 1)
    result.fusion = replace(
        output, hits=(replace(hits[1], rank=1), replace(hits[0], rank=2))
    )
    with pytest.raises(ValueError):
        binder._validate_fusion(result, rows, "snap", "catalog", "query", binder._Meter())


def test_controlled_catalog_refuses_wrong_vector_length_before_identity(monkeypatch):
    from dataclasses import replace

    from slaif_raggedized_helper import raw_snapshot_catalog

    originals, derived, owner, _, _, result, _, _, _, _ = _controlled_fixture(monkeypatch)
    catalog = raw_snapshot_catalog.load_catalog(
        originals, derived, "/fixture", result.snapshot_id, deadline_ms=1
    )
    row = replace(catalog.rows[0], vector_bytes=bytes(4095))
    bad = replace(catalog, rows=(row, *catalog.rows[1:]))
    with pytest.raises(ValueError):
        binder._catalog_identity(bad, binder._Meter(), lambda: None)


def test_controlled_catalog_same_count_byte_substitution_refused(monkeypatch):
    from dataclasses import replace

    from slaif_raggedized_helper import raw_snapshot_catalog

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    source_fake = raw_snapshot_catalog.load_catalog

    def substituted(*args, **kwargs):
        catalog = source_fake(*args, **kwargs)
        row = replace(catalog.rows[0], rendered_bytes=b"y")
        return replace(catalog, rows=(row, *catalog.rows[1:]))

    monkeypatch.setattr(raw_snapshot_catalog, "load_catalog", substituted)
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert calls == ["pin", "catalog", "pin"]


def test_controlled_pin_capture_substitution_refused(monkeypatch):
    from dataclasses import replace

    from slaif_raggedized_helper import raw_snapshot_pin

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    captured = owner.value
    observations = []

    def substituted(self, **kwargs):
        observations.append(1)
        if len(observations) == 2:
            return replace(captured, pointer=replace(captured.pointer, generation=2))
        return captured

    monkeypatch.setattr(raw_snapshot_pin.PinOwner, "check", substituted)
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals,
            derived,
            "/fixture",
            owner,
            data,
            "case1",
            gold_ids,
            result,
            payload,
            query_space_id=ids[0],
            query_definition_fingerprint=ids[1],
            query_policy_id=ids[2],
            query_execution_fingerprint=ids[3],
            grants=grants,
        )
    assert len(observations) == 2
    assert "gold" not in calls


def test_term_preflight_checks_all_types_before_content_reservations():
    meter = binder._Meter()
    with pytest.raises(ValueError):
        binder._sort_unique_terms(("valid", None), meter)
    assert (meter.work, meter.payload) == (2, 0)


def test_scalar_encoding_refuses_before_encoder(monkeypatch):
    import json

    called = []
    monkeypatch.setattr(json, "dumps", lambda *args, **kwargs: called.append(True))
    with pytest.raises(ValueError):
        binder._canonical_hash(1.0, b"", binder._Meter(payload_limit=100), lambda: None)
    assert called == []


def test_digest_finalization_reservation_and_postcheck(monkeypatch):
    import hashlib

    finalized = []

    class Digest:
        def update(self, value):
            pass

        def hexdigest(self):
            finalized.append(True)
            return "0" * 64

    monkeypatch.setattr(hashlib, "sha256", lambda: Digest())

    class RefuseFinalization(binder._Meter):
        def reserve(self, work, payload=0, **kwargs):
            if work == 65 and payload == 192:
                raise ValueError
            return super().reserve(work, payload, **kwargs)

    with pytest.raises(ValueError):
        binder._canonical_hash(None, b"", RefuseFinalization(), lambda: None)
    assert finalized == []

    def check():
        if finalized:
            raise ValueError

    with pytest.raises(ValueError):
        binder._canonical_hash(None, b"", binder._Meter(), check)
    assert finalized == [True]


@pytest.mark.parametrize("bad_payload", [b"", bytes(4095), bytearray(4096), b"x" * 4097])
def test_payload_preflight_refuses_before_source(monkeypatch, bad_payload):
    originals, derived, owner, data, gold_ids, result, _, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    with pytest.raises(binder.StageBindingError) as caught:
        binder.bind_stages(
            originals, derived, "/fixture", owner, data, "case1", gold_ids, result, bad_payload,
            query_space_id=ids[0], query_definition_fingerprint=ids[1], query_policy_id=ids[2],
            query_execution_fingerprint=ids[3], grants=grants,
        )
    assert str(caught.value) == "source-bound stage diagnosis refused"
    assert caught.value.__suppress_context__
    assert calls == []


def test_small_sort_has_hand_calculated_logical_charge():
    meter = binder._Meter()
    assert binder._sort_unique_terms(("b", "a"), meter) == ("a", "b")
    assert meter.work == 27
    assert meter.payload == 1024
    assert meter.categories["string_compare"] == [9, 0]


def test_forged_fixed_marker_is_refused_before_source(monkeypatch):
    from dataclasses import replace

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    result = replace(result, fusion=replace(result.fusion, dense_status="UNAVAILABLE"))
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals, derived, "/fixture", owner, data, "case1", gold_ids, result, payload,
            query_space_id=ids[0], query_definition_fingerprint=ids[1], query_policy_id=ids[2],
            query_execution_fingerprint=ids[3], grants=grants,
        )
    assert calls == []


def test_catalog_declaration_reserves_before_encoder_and_copy(monkeypatch):
    import json

    calls = []
    with monkeypatch.context() as patch:
        patch.setattr(json, "dumps", lambda *a, **k: calls.append("encoder"))
        patch.setattr(binder, "_declaration_bytes", lambda text: calls.append("copy"))
        for meter in (binder._Meter(work_limit=111), binder._Meter(payload_limit=95)):
            with pytest.raises(ValueError):
                binder._check_declaration_wire({"x": "a"}, b'{"x":"a"}', meter, lambda: None)
        assert calls == []
    meter = binder._Meter()
    binder._check_declaration_wire({"x": "a"}, b'{"x":"a"}', meter, lambda: None)
    assert (meter.work, meter.payload) == (112, 96)


def test_controlled_two_partition_full_stages_exceed_return_cap(monkeypatch):
    from unittest.mock import patch

    from slaif_raggedized_helper import declared_stage_geometry

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch, wide=True)
    )
    assert len(result.dense.trace.partitions) == 2
    assert tuple(len(p.eligible_ordinals) for p in result.dense.trace.partitions) == (32, 32)
    assert result.dense.eligible == result.dense.selected == 64
    assert result.dense.returned == 60 and result.dense.global_cap_applied is True
    assert result.dense.partition_cap_applied is False
    lower = declared_stage_geometry.declared_span_support.score_case
    with patch.object(
        declared_stage_geometry.declared_span_support, "score_case", wraps=lower
    ) as score:
        output = binder.bind_stages(
            originals, derived, "/fixture", owner, data, "case1", gold_ids, result, payload,
            query_space_id=ids[0], query_definition_fingerprint=ids[1], query_policy_id=ids[2],
            query_execution_fingerprint=ids[3], grants=grants,
        )
    assert score.call_count == 13
    assert calls == ["pin", "catalog", "pin", "gold", "pin", "ranking", "pin", "pin"]
    assert tuple(stage.row_count for stage in output.geometry.stages) == (
        64, 64, 64, 60, 64, 64, 64, 60, 60, 60
    )
    assert output.geometry.stages[0].completion.recall == 1
    assert output.geometry.stages[0].coverage.covered_requirement_ids == ("R1", "R2")
    assert output.geometry.stages[3].completion.recall == 0
    assert output.geometry.prefixes[0].cutoff == 20
    assert output.geometry.prefixes[1].cutoff == 60
    assert output.geometry.prefixes[0].coverage.covered_requirement_ids == ()
    assert output.geometry.prefixes[1].coverage.covered_requirement_ids == ()


@pytest.mark.parametrize("mutation", ["cross_query", "unrelated_row"])
def test_coherent_rehashed_trace_substitution_refused(monkeypatch, mutation):
    import dataclasses
    import hashlib
    import json

    originals, derived, owner, data, gold_ids, result, payload, ids, grants, calls = (
        _controlled_fixture(monkeypatch)
    )
    trace = result.dense.trace
    dense = result.dense
    if mutation == "cross_query":
        trace = dataclasses.replace(trace, query_payload_sha256="0" * 64)
        dense = dataclasses.replace(dense, query_payload_sha256="0" * 64)
    else:
        unrelated = "sha256:" + "f" * 64
        row = dataclasses.replace(trace.rows[0], chunk_id=unrelated)
        hit = dataclasses.replace(dense.hits[0], chunk_id=unrelated)
        trace = dataclasses.replace(trace, rows=(row, *trace.rows[1:]))
        dense = dataclasses.replace(dense, hits=(hit, *dense.hits[1:]))
    names = ("snapshot_id", "catalog_id", "query_payload_sha256", "query_space_id",
             "query_definition_fingerprint", "query_policy_id", "query_execution_fingerprint",
             "authority_sha256")
    obj = {name: getattr(trace, name) for name in names}
    obj.update(schema=1, kind="slaif-raw-dense-authorized-trace-v1", k=60, partition_cap=60,
               rows=[dataclasses.asdict(row) for row in trace.rows],
               partitions=[dataclasses.asdict(part) for part in trace.partitions],
               selected_ordinals=trace.selected_ordinals, returned_ordinals=trace.returned_ordinals)
    wire = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    trace_id = "sha256:" + hashlib.sha256(
        b"slaif-raw-dense-authorized-trace-v1\n" + wire
    ).hexdigest()
    trace = dataclasses.replace(trace, trace_id=trace_id)
    result = dataclasses.replace(result, dense=dataclasses.replace(dense, trace=trace))
    with pytest.raises(binder.StageBindingError):
        binder.bind_stages(
            originals, derived, "/fixture", owner, data, "case1", gold_ids, result, payload,
            query_space_id=ids[0], query_definition_fingerprint=ids[1], query_policy_id=ids[2],
            query_execution_fingerprint=ids[3], grants=grants,
        )
    assert calls == ["pin", "catalog", "pin"]
