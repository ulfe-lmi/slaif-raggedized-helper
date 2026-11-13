"""Structural bridge tests; no store, model, or execution qualification."""

import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from slaif_raggedized_helper import corpus_embedding_executor as executor
from slaif_raggedized_helper import raw_snapshot_completion_locator as locator

PROGRAM = (
    b'{"batch_policy":{"max_items":128,"max_total_codepoints":1000000,"max_tot'
    b'al_request_bytes":4000000,"version":"raw-batch-v1"},"batches":[{"batch_i'
    b'ndex":0,"first_ordinal":0,"row_count":1,"source_index":0,"total_codepoin'
    b'ts":3,"total_native_request_bytes":100},{"batch_index":1,"first_ordinal"'
    b':1,"row_count":1,"source_index":1,"total_codepoints":3,"total_native_req'
    b'uest_bytes":100}],"kind":"embedding-source-program-v1","program_policy":'
    b'{"deadline_ms":120000,"max_batches":65536,"max_bundles":128,"max_program'
    b'_bytes":16777216,"max_rows":65536,"version":"embedding-source-program-po'
    b'licy-v1"},"representation_policy":{"max_codepoints":100000,"max_request_'
    b'bytes":200000,"max_tokens":1024,"separator":"\\n\\n","version":"raw-v1"},"'
    b'rows":[{"chunk_id":"sha256:000000000000000000000000000000000000000000000'
    b'000000000000000000b","codepoints":3,"native_request_bytes":100,"ordinal"'
    b':0,"rendered_sha256":"00000000000000000000000000000000000000000000000000'
    b'0000000000000d","source_index":0},{"chunk_id":"sha256:000000000000000000'
    b'000000000000000000000000000000000000000000000c","codepoints":3,"native_r'
    b'equest_bytes":100,"ordinal":1,"rendered_sha256":"00000000000000000000000'
    b'0000000000000000000000000000000000000000e","source_index":1}],"schema":1'
    b',"sources":[{"bundle_id":"0000000000000000000000000000000000000000000000'
    b'000000000000000001","bundle_metadata_sha256":"00000000000000000000000000'
    b'00000000000000000000000000000000000003","extraction_id":"sha256:00000000'
    b'00000000000000000000000000000000000000000000000000000007","first_ordinal'
    b'":0,"revision_id":"sha256:0000000000000000000000000000000000000000000000'
    b'000000000000000005","row_count":1,"source_scope_sha256":"000000000000000'
    b'0000000000000000000000000000000000000000000000009"},{"bundle_id":"000000'
    b'0000000000000000000000000000000000000000000000000000000002","bundle_meta'
    b'data_sha256":"0000000000000000000000000000000000000000000000000000000000'
    b'000004","extraction_id":"sha256:0000000000000000000000000000000000000000'
    b'000000000000000000000008","first_ordinal":1,"revision_id":"sha256:000000'
    b'0000000000000000000000000000000000000000000000000000000006","row_count":'
    b'1,"source_scope_sha256":"00000000000000000000000000000000000000000000000'
    b'0000000000000000a"}],"token_eligibility":"NOT_RUN"}'
)
EXPECTED = (
    b'{"kind":"slaif-raw-program-output-selection-v1","outputs":[{"batch_index'
    b'":0,"container_id":"0000000000000000000000000000000000000000000000000000'
    b'000000000015","metadata_sha256":"000000000000000000000000000000000000000'
    b'000000000000000000000001f"},{"batch_index":1,"container_id":"00000000000'
    b'00000000000000000000000000000000000000000000000000016","metadata_sha256"'
    b':"0000000000000000000000000000000000000000000000000000000000000020"}],"s'
    b'chema":1,"source_program_id":"sha256:68b546b8fe02ba2b9f76847586f4358bf1a'
    b'd95386f8d4ac263d6d2db0f5e3c13"}'
)
SOURCE = "sha256:68b546b8fe02ba2b9f76847586f4358bf1ad95386f8d4ac263d6d2db0f5e3c13"


def result():
    return executor.CorpusResult(
        SOURCE,
        2,
        (
            executor.BatchCompletion(0, None, "sha256:" + "0" * 62 + "15", "0" * 62 + "1f", None),
            executor.BatchCompletion(1, None, "sha256:" + "0" * 62 + "16", "0" * 62 + "20", None),
        ),
        None,
        None,
        None,
    )


def test_literal_oracle():
    actual = locator.encode(PROGRAM, result())
    assert actual == EXPECTED
    assert (
        hashlib.sha256(actual).hexdigest()
        == "bfef9048a4dea946acb355e4d914efa71eacc765c05c5aa92600fdd09e838798"
    )


class Poison:
    def __getattribute__(self, name):
        raise SystemExit("unused metadata was traversed")


def test_unused_fields_are_not_touched():
    r = result()
    cs = tuple(replace(c, job_id=Poison(), reused=Poison()) for c in r.completions)
    assert (
        locator.encode(
            PROGRAM,
            replace(
                r,
                completions=cs,
                execution_record=Poison(),
                native_runtime_record=Poison(),
                execution_fingerprint=Poison(),
            ),
        )
        == EXPECTED
    )


def changed(index=0, **kwargs):
    r = result()
    cs = list(r.completions)
    cs[index] = replace(cs[index], **kwargs)
    return replace(r, completions=tuple(cs))


@pytest.mark.parametrize(
    "bad",
    [
        None,
        object(),
        replace(result(), row_count=True),
        replace(result(), row_count=0),
        replace(result(), row_count=4097),
        replace(result(), row_count=1),
        replace(result(), source_program_id="sha256:" + "A" * 64),
        replace(result(), source_program_id="0" * 64),
        replace(result(), source_program_id="sha256:" + "0" * 64),
        replace(result(), completions=[]),
        replace(result(), completions=()),
        replace(result(), completions=result().completions * 65),
        replace(result(), completions=(result().completions[0],)),
        replace(result(), completions=tuple(reversed(result().completions))),
        replace(result(), completions=(object(), result().completions[1])),
        changed(batch_index=True),
        changed(batch_index=1),
        changed(output_ref="sha256:" + "A" * 64),
        changed(output_ref="0" * 64),
        changed(output_ref="sha256:" + "0" * 65),
        changed(output_ref="sha256:" + "0" * 100000),
        changed(metadata_sha256="A" * 64),
        changed(metadata_sha256="0" * 63),
        changed(metadata_sha256="0" * 100000),
        changed(1, output_ref=result().completions[0].output_ref),
    ],
)
def test_invalid_results_refused(bad):
    with pytest.raises(locator.CompletionLocatorError, match="^completion locator refused$"):
        locator.encode(PROGRAM, bad)


class BytesSubclass(bytes):
    pass


class ResultSubclass(executor.CorpusResult):
    pass


@pytest.mark.parametrize(
    "bad",
    [b"", b"{}", PROGRAM + b"\n", bytearray(PROGRAM), BytesSubclass(PROGRAM), b"x" * 16777217],
    ids=[
        "empty",
        "malformed-json",
        "trailing-newline",
        "mutable-bytes",
        "bytes-subclass",
        "oversized-program",
    ],
)
def test_bad_program_refused(bad):
    with pytest.raises(locator.CompletionLocatorError, match="^completion locator refused$"):
        locator.encode(bad, result())


def test_result_subclass_refused():
    r = result()
    with pytest.raises(locator.CompletionLocatorError):
        locator.encode(PROGRAM, ResultSubclass(*r.__dict__.values()))


@pytest.mark.parametrize("budget", [True, 0, -1, 120001, 1.0, "1"])
def test_bad_budget(budget):
    with pytest.raises(locator.CompletionLocatorError):
        locator.encode(PROGRAM, result(), deadline_ms=budget)


def test_oversized_tuple_rejected_before_parser(monkeypatch):
    def forbidden(*args):
        raise SystemExit("parser called")

    monkeypatch.setattr(locator.program, "parse", forbidden)
    with pytest.raises(locator.CompletionLocatorError):
        locator.encode(PROGRAM, replace(result(), completions=result().completions * 65))


def test_non_exception_propagates(monkeypatch):
    def interrupt(*args):
        raise SystemExit("interrupt")

    monkeypatch.setattr(locator.program, "parse", interrupt)
    with pytest.raises(SystemExit, match="interrupt"):
        locator.encode(PROGRAM, result())


@pytest.mark.parametrize("failure_at", [3, 4, 5, 6, 7, 8])
def test_deadline_boundaries(monkeypatch, failure_at):
    parsed = locator.program.parse(PROGRAM)
    monkeypatch.setattr(locator.program, "parse", lambda _: parsed)
    calls = iter([0.0] * failure_at + [1000.0] * 20)
    monkeypatch.setattr(locator.time, "monotonic", lambda: next(calls))
    with pytest.raises(locator.CompletionLocatorError):
        locator.encode(PROGRAM, result())


@pytest.mark.parametrize(
    "rows,batches,valid", [(4096, 128, True), (4097, 128, False), (4096, 129, False)]
)
def test_snapshot_limits(monkeypatch, rows, batches, valid):
    cs = tuple(
        executor.BatchCompletion(i, None, "sha256:" + f"{i:064x}", f"{i:064x}", None)
        for i in range(batches)
    )
    parsed = SimpleNamespace(
        source_program_id=SOURCE,
        row_count=rows,
        batch_count=batches,
        batches=tuple(SimpleNamespace(batch_index=i) for i in range(batches)),
    )
    monkeypatch.setattr(locator.program, "parse", lambda _: parsed)
    r = executor.CorpusResult(SOURCE, rows, cs, None, None, None)
    if valid:
        assert len(json.loads(locator.encode(PROGRAM, r))["outputs"]) == batches
    else:
        with pytest.raises(locator.CompletionLocatorError):
            locator.encode(PROGRAM, r)
