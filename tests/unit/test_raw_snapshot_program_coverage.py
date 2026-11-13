"""Source-free checks of coverage admission and failure boundaries."""

import json
from dataclasses import FrozenInstanceError

import pytest

from slaif_raggedized_helper import raw_snapshot_program_coverage as coverage
from slaif_raggedized_helper import derived_store
from slaif_raggedized_helper.source_admission import OriginalStore


def wire(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("ascii")


def locator():
    return dict(
        schema=1,
        kind="slaif-raw-program-output-selection-v1",
        source_program_id="sha256:" + "a" * 64,
        outputs=[
            dict(batch_index=i, container_id=str(i + 1) * 64, metadata_sha256="f" * 64)
            for i in range(2)
        ],
    )


def test_locator_strict():
    obj = locator()
    assert coverage._locator(wire(obj), obj["source_program_id"], 2) == obj["outputs"]
    for mutate in (
        lambda x: x.update(schema=True),
        lambda x: x.update(extra=1),
        lambda x: x["outputs"][0].update(batch_index=False),
        lambda x: x["outputs"].reverse(),
        lambda x: x["outputs"].pop(),
        lambda x: x["outputs"][1].update(container_id=x["outputs"][0]["container_id"]),
        lambda x: x["outputs"][0].update(metadata_sha256="A" * 64),
        lambda x: x["outputs"][0].update(extra=1),
    ):
        bad = locator()
        mutate(bad)
        with pytest.raises(ValueError):
            coverage._locator(wire(bad), obj["source_program_id"], 2)
    for data in (wire(obj) + b" ", b'{"schema":1,"schema":1}', b"x" * 65537):
        with pytest.raises((ValueError, UnicodeError)):
            coverage._locator(data, obj["source_program_id"], 2)


def test_public_refusal_and_base_exception(monkeypatch):
    originals = object.__new__(OriginalStore)
    derived = object.__new__(derived_store.Store)
    for deadline in (True, 0, 120001, 1.0):
        with pytest.raises(coverage.CoverageError, match="^program coverage refused$"):
            coverage.build(originals, derived, b"{}", b"{}", b"{}", deadline_ms=deadline)

    class Stop(BaseException):
        pass

    def stop(_):
        raise Stop

    monkeypatch.setattr(coverage.program, "_parse", stop)
    with pytest.raises(Stop):
        coverage.build(originals, derived, b"{}", b"{}", b"{}")


def test_result_is_frozen_and_honest():
    result = coverage.CoveredRowMap("id", b"map", "hash", ("bundle",), 1, 1, 1)
    assert (result.coverage, result.execution_origin, result.qualification) == (
        "COMPLETE_SELECTED_PROGRAM",
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
    )
    with pytest.raises(FrozenInstanceError):
        result.row_count = 2


def test_program_policies_and_bounds_before_source_io(monkeypatch):
    from dataclasses import asdict
    from types import SimpleNamespace

    from slaif_raggedized_helper import retrieval_representation as rr

    originals = object.__new__(OriginalStore)
    derived = object.__new__(derived_store.Store)
    ident = "sha256:" + "a" * 64
    descriptor = SimpleNamespace(source_program_id=ident, row_count=1, batch_count=1)
    doc = {
        "representation_policy": asdict(rr.Policy()),
        "batch_policy": asdict(rr.BatchPolicy()),
        "program_policy": {"max_rows": 1, "max_batches": 1},
        "sources": [{}],
    }
    completion = wire(
        dict(
            schema=1,
            kind="slaif-raw-program-output-selection-v1",
            source_program_id=ident,
            outputs=[dict(batch_index=0, container_id="1" * 64, metadata_sha256="f" * 64)],
        )
    )
    monkeypatch.setattr(coverage.program, "_parse", lambda _: (descriptor, doc))

    class ReachedSource(BaseException):
        pass

    def reached(*_args):
        raise ReachedSource

    monkeypatch.setattr(coverage.program, "validate", reached)
    with pytest.raises(ReachedSource):
        coverage.build(originals, derived, b"valid", b"declaration", completion)
    for field, value in (("row_count", 4097), ("batch_count", 129)):
        original = getattr(descriptor, field)
        setattr(descriptor, field, value)
        with pytest.raises(coverage.CoverageError):
            coverage.build(originals, derived, b"valid", b"declaration", completion)
        setattr(descriptor, field, original)
    doc["sources"] = [{}] * 129
    with pytest.raises(coverage.CoverageError):
        coverage.build(originals, derived, b"valid", b"declaration", completion)
    doc["sources"] = [{}]
    for key in ("representation_policy", "batch_policy"):
        saved = doc[key]
        doc[key] = dict(saved, version="unsupported")
        with pytest.raises(coverage.CoverageError):
            coverage.build(originals, derived, b"valid", b"declaration", completion)
        doc[key] = saved
    with pytest.raises(coverage.CoverageError):
        coverage.build(originals, derived, b"x" * (16777216 + 1), b"declaration", completion)


def test_deadline_is_captured_before_parse(monkeypatch):
    originals = object.__new__(OriginalStore)
    derived = object.__new__(derived_store.Store)
    times = iter((10.0, 10.001))
    monkeypatch.setattr(coverage.time, "monotonic", lambda: next(times))
    with pytest.raises(coverage.CoverageError):
        coverage.build(originals, derived, b"{}", b"{}", b"{}", deadline_ms=1)


def test_valid_smaller_program_policy_reaches_fresh_validation(monkeypatch):
    from dataclasses import asdict

    from slaif_raggedized_helper import corpus_embedding_program as program
    from slaif_raggedized_helper import retrieval_representation as rr

    source = dict(
        bundle_id="1" * 64,
        bundle_metadata_sha256="2" * 64,
        revision_id="sha256:" + "3" * 64,
        extraction_id="sha256:" + "4" * 64,
        source_scope_sha256="5" * 64,
        first_ordinal=0,
        row_count=1,
    )
    row = dict(
        ordinal=0,
        source_index=0,
        chunk_id="sha256:" + "6" * 64,
        rendered_sha256="7" * 64,
        codepoints=1,
        native_request_bytes=1,
    )
    batch = dict(
        batch_index=0,
        source_index=0,
        first_ordinal=0,
        row_count=1,
        total_codepoints=1,
        total_native_request_bytes=1,
    )
    doc = dict(
        schema=1,
        kind="embedding-source-program-v1",
        token_eligibility="NOT_RUN",
        representation_policy=asdict(rr.Policy()),
        batch_policy=asdict(rr.BatchPolicy()),
        program_policy=asdict(program.ProgramPolicy(max_rows=1, max_batches=1, max_bundles=1)),
        sources=[source],
        rows=[row],
        batches=[batch],
    )
    data = wire(doc)
    parsed = program.parse(data)
    completion = wire(
        dict(
            schema=1,
            kind="slaif-raw-program-output-selection-v1",
            source_program_id=parsed.source_program_id,
            outputs=[dict(batch_index=0, container_id="8" * 64, metadata_sha256="9" * 64)],
        )
    )

    class ReachedSource(BaseException):
        pass

    def reached(*_args):
        raise ReachedSource

    monkeypatch.setattr(program, "validate", reached)
    with pytest.raises(ReachedSource):
        coverage.build(
            object.__new__(OriginalStore),
            object.__new__(derived_store.Store),
            data,
            b"{}",
            completion,
        )


def test_factored_representation_render_matches_original_body():
    from slaif_raggedized_helper import retrieval_representation as rr

    def original(title, headings, body, remaining):
        components = [title, *headings, body]
        if any(x is not None and type(x) is not str for x in components):
            raise ValueError
        components = [x for x in components[:-1] if x] + [components[-1]]
        length = sum(len(x) for x in components) + 2 * (len(components) - 1)
        if length > 100000 or length > remaining:
            raise ValueError
        text = "\n\n".join(components)
        request = (
            json.dumps(
                dict(text=text, pair=None, nonce="0" * 32, role="bge_representation", artifact=0),
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode()
            + b"\n"
        )
        if len(request) > 200000:
            raise ValueError
        return text, len(request)

    for title, headings, body in (
        (None, (), ""),
        ("Title", ("", "Heading"), "text"),
        ("Ž😀", ("段",), '\\"\n'),
        (None, (), "x" * 100000),
    ):
        assert rr._format_raw(title, headings, body, rr.Policy()) == original(
            title, headings, body, 100000
        )
    for args in (("title", (), "body", 2), (None, (), "x" * 100001, 100001)):
        with pytest.raises(ValueError):
            original(*args)
        with pytest.raises(ValueError):
            rr._format_raw(*args[:3], rr.Policy(), args[3])


def test_locator_rejects_foreign_program_and_noncanonical_values():
    obj = locator()
    ident = obj["source_program_id"]
    cases = []
    bad = locator()
    bad["source_program_id"] = "sha256:" + "b" * 64
    cases.append(wire(bad))
    bad = locator()
    bad["outputs"][0]["batch_index"] = 0.0
    cases.append(wire(bad))
    bad = locator()
    bad["outputs"][0]["container_id"] = "z" * 64
    cases.append(wire(bad))
    bad = locator()
    bad["outputs"] = {}
    cases.append(wire(bad))
    cases.extend((wire(obj).replace(b'"schema":1', b'"schema":1,"schema":1'), b"\xff"))
    for data in cases:
        with pytest.raises((ValueError, UnicodeError)):
            coverage._locator(data, ident, 2)


def test_original_error_is_content_free_and_base_exception_identity(monkeypatch):
    originals = object.__new__(OriginalStore)
    derived = object.__new__(derived_store.Store)

    def leak(_):
        raise RuntimeError("sensitive content")

    monkeypatch.setattr(coverage.program, "_parse", leak)
    with pytest.raises(coverage.CoverageError) as exc:
        coverage.build(originals, derived, b"{}", b"{}", b"{}")
    assert str(exc.value) == "program coverage refused"
    assert exc.value.__cause__ is None
    marker = KeyboardInterrupt("marker")

    def interrupt(_):
        raise marker

    monkeypatch.setattr(coverage.program, "_parse", interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        coverage.build(originals, derived, b"{}", b"{}", b"{}")
    assert caught.value is marker
