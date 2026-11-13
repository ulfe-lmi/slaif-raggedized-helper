"""Convert a structural executor result into a coverage locator, not proof of execution."""

import json
import re
import time

from . import corpus_embedding_executor as executor
from . import corpus_embedding_program as program


class CompletionLocatorError(ValueError):
    """Content-free refusal of a completion locator."""


def _hex(value, prefix=""):
    return (
        type(value) is str
        and len(value) == len(prefix) + 64
        and re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is not None
    )


def encode(program_bytes, execution_result, *, deadline_ms=30000):
    """Return canonical locator bytes; fresh coverage validation remains mandatory."""
    try:
        if type(deadline_ms) is not int or not 1 <= deadline_ms <= 120000:
            raise ValueError
        deadline = time.monotonic() + deadline_ms / 1000

        def check():
            if time.monotonic() >= deadline:
                raise ValueError

        check()
        if (
            type(program_bytes) is not bytes
            or not 1 <= len(program_bytes) <= 16777216
            or type(execution_result) is not executor.CorpusResult
        ):
            raise ValueError
        source_id = execution_result.source_program_id
        row_count = execution_result.row_count
        completions = execution_result.completions
        if (
            not _hex(source_id, "sha256:")
            or type(row_count) is not int
            or not 1 <= row_count <= 4096
            or type(completions) is not tuple
            or not 1 <= len(completions) <= 128
        ):
            raise ValueError
        check()
        parsed = program.parse(program_bytes)
        check()
        if (
            parsed.source_program_id != source_id
            or parsed.row_count != row_count
            or not 1 <= parsed.batch_count <= 128
            or parsed.batch_count != len(completions)
            or len(parsed.batches) != len(completions)
        ):
            raise ValueError
        outputs = []
        seen = set()
        for index, completion in enumerate(completions):
            check()
            if type(completion) is not executor.BatchCompletion:
                raise ValueError
            batch_index = completion.batch_index
            output_ref = completion.output_ref
            metadata = completion.metadata_sha256
            if (
                type(batch_index) is not int
                or batch_index != index
                or parsed.batches[index].batch_index != index
                or not _hex(output_ref, "sha256:")
                or not _hex(metadata)
            ):
                raise ValueError
            container = output_ref[7:]
            if container in seen:
                raise ValueError
            seen.add(container)
            outputs.append(
                {"batch_index": batch_index, "container_id": container, "metadata_sha256": metadata}
            )
        check()
        payload = json.dumps(
            {
                "schema": 1,
                "kind": "slaif-raw-program-output-selection-v1",
                "source_program_id": source_id,
                "outputs": outputs,
            },
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
        check()
        if len(payload) > 65536:
            raise ValueError
        check()
        return payload
    except Exception:
        raise CompletionLocatorError("completion locator refused") from None
