"""Private source-bound stage diagnostics for supplied raw traces."""

from dataclasses import dataclass, field as dc_field


class StageBindingError(ValueError):
    """Content-free refusal of a source-bound diagnosis."""


class _Meter:
    """Cumulative logical work and payload reservations, not OS resources."""

    __slots__ = ("work", "payload", "work_limit", "payload_limit", "check", "categories")

    def __init__(self, work_limit=134217728, payload_limit=268435456):
        if (
            type(work_limit) is not int
            or type(payload_limit) is not int
            or work_limit < 0
            or payload_limit < 0
        ):
            raise ValueError
        self.work = 0
        self.payload = 0
        self.work_limit = work_limit
        self.payload_limit = payload_limit
        self.check = None
        self.categories = {
            "local": [0, 0],
            "string_compare": [0, 0],
            "json_emit": [0, 0],
            "pure_delegate": [0, 0],
        }

    def reserve(self, work, payload=0, *, category="local"):
        if self.check is not None:
            self.check()
        if (
            type(work) is not int
            or type(payload) is not int
            or work < 0
            or payload < 0
            or work > self.work_limit - self.work
            or payload > self.payload_limit - self.payload
            or category not in self.categories
        ):
            raise ValueError
        self.work += work
        self.payload += payload
        self.categories[category][0] += work
        self.categories[category][1] += payload

    def compare_strings(self, left, right):
        if type(left) is not str or type(right) is not str:
            raise ValueError
        charge = len(left) + len(right) + 1
        self.reserve(charge, category="string_compare")
        if left < right:
            return -1
        self.reserve(charge, category="string_compare")
        if left > right:
            return 1
        return 0


def _sort_unique_terms(terms, meter):
    """Sort bounded terms without a string-keyed hash table or builtin sort."""
    if type(terms) is not tuple or len(terms) > 200000:
        raise ValueError
    for term in terms:
        meter.reserve(1)
        if type(term) is not str or not 1 <= len(term) <= 4096:
            raise ValueError
    meter.reserve(len(terms), 128 * len(terms))
    current = []
    for term in terms:
        meter.reserve(len(term) + 2)
        current.append(term)
    width = 1
    count = len(current)
    while width < count:
        meter.reserve(count, 128 * count)
        out = []
        for start in range(0, count, 2 * width):
            left, right = start, min(start + width, count)
            mid, end = right, min(start + 2 * width, count)
            while left < mid and right < end:
                if meter.compare_strings(current[left], current[right]) <= 0:
                    out.append(current[left])
                    left += 1
                else:
                    out.append(current[right])
                    right += 1
            while left < mid:
                out.append(current[left])
                left += 1
            while right < end:
                out.append(current[right])
                right += 1
        current = out
        width *= 2
    meter.reserve(count, 128 * count)
    unique = []
    for term in current:
        meter.reserve(1)
        if not unique or meter.compare_strings(unique[-1], term) != 0:
            unique.append(term)
    meter.reserve(len(unique), 128 * len(unique))
    return tuple(unique)


def _canonical_hash(value, domain, meter, check, *, ensure_ascii=True, limit=4194304):
    """Hash a bounded canonical JSON value in pieces, charging before emission."""
    import hashlib
    import json
    import math

    if type(domain) is not bytes or len(domain) > 128:
        raise ValueError
    meter.reserve(len(domain) + 1, len(domain))
    digest = hashlib.sha256()
    check()
    digest.update(domain)
    check()
    size = 0

    def emit(data):
        nonlocal size
        if type(data) is not bytes or size + len(data) > limit:
            raise ValueError
        size += len(data)
        for offset in range(0, len(data), 49152):
            piece_size = min(49152, len(data) - offset)
            meter.reserve(piece_size, piece_size, category="json_emit")
            piece = data[offset : offset + piece_size]
            check()
            digest.update(piece)
            check()

    def visit(item, depth):
        if depth > 16:
            raise ValueError
        meter.reserve(1)
        if type(item) is str:
            if len(item) > 4096:
                raise ValueError
            # ASCII JSON can use twelve bytes per non-BMP character, plus quotes.
            meter.reserve(len(item) + 1, 128 + 2 * (12 * len(item) + 2))
            token = (
                json.encoder.encode_basestring_ascii(item)
                if ensure_ascii
                else json.encoder.encode_basestring(item)
            )
            emit(token.encode("ascii" if ensure_ascii else "utf-8"))
        elif item is None:
            meter.reserve(1, 128)
            emit(b"null")
        elif type(item) is bool:
            meter.reserve(1, 128)
            emit(b"true" if item else b"false")
        elif type(item) is int:
            if not -(2**63) <= item < 2**63:
                raise ValueError
            meter.reserve(1, 128 + 2 * 20)
            token = str(item)
            emit(token.encode("ascii"))
        elif type(item) is float:
            if not math.isfinite(item):
                raise ValueError
            meter.reserve(1, 128 + 2 * 32)
            token = json.dumps(item, allow_nan=False)
            emit(token.encode("ascii"))
        elif type(item) in (tuple, list):
            if len(item) > 200000:
                raise ValueError
            meter.reserve(len(item), 128 * len(item))
            emit(b"[")
            for index, child in enumerate(item):
                if index:
                    emit(b",")
                visit(child, depth + 1)
            emit(b"]")
        elif type(item) is dict:
            if len(item) > 128:
                raise ValueError
            meter.reserve(len(item), 128 * len(item))
            keys = list(item)
            for key in keys:
                if type(key) is not str or len(key) > 128:
                    raise ValueError
                meter.reserve(len(key) + 1)
            # Fixed-schema keys only; no source terms enter this map.
            for index in range(1, len(keys)):
                position = index
                while position and meter.compare_strings(keys[position - 1], keys[position]) > 0:
                    keys[position - 1], keys[position] = keys[position], keys[position - 1]
                    position -= 1
            emit(b"{")
            for index, key in enumerate(keys):
                if index:
                    emit(b",")
                visit(key, depth + 1)
                emit(b":")
                visit(item[key], depth + 1)
            emit(b"}")
        else:
            raise ValueError

    visit(value, 0)
    meter.reserve(65, 128 + 64)
    check()
    result = digest.hexdigest()
    check()
    return result


def _terms_intersect(left, right, meter):
    """Compare previously sorted unique exact terms without hashing them."""
    if type(left) is not tuple or type(right) is not tuple:
        raise ValueError
    i = j = 0
    while i < len(left) and j < len(right):
        meter.reserve(2)
        order = meter.compare_strings(left[i], right[j])
        if order == 0:
            return True
        if order < 0:
            i += 1
        else:
            j += 1
    return False


_SOURCE_INGESTION_LOADS = 5888
_SOURCE_BATCH_LOADS = 6400
_SOURCE_LOADS = 12288
_SOURCE_LOGICAL_BYTES = 4986555627809


def _source_envelope():
    """Check the fixed, trace-independent source accounting envelope."""
    generic = 4 * (524288 + 100663296 + 17)
    original = 2000000 + 16384 + 2
    directory = 262144 + 100663296 + 259
    total = 11 * directory + _SOURCE_LOADS * generic + _SOURCE_INGESTION_LOADS * original
    if (
        _SOURCE_INGESTION_LOADS + _SOURCE_BATCH_LOADS != _SOURCE_LOADS
        or total != _SOURCE_LOGICAL_BYTES
        or total > 6 * 1024**4
    ):
        raise ValueError
    return (_SOURCE_INGESTION_LOADS, _SOURCE_BATCH_LOADS, _SOURCE_LOADS, total)


class _Deadline:
    __slots__ = ("end",)

    def __init__(self, start, deadline_ms):
        if type(deadline_ms) is not int or not 1 <= deadline_ms <= 120000:
            raise ValueError
        self.end = start + deadline_ms / 1000

    def check(self):
        import time

        if time.monotonic() >= self.end:
            raise ValueError

    def remaining(self, cap):
        import time

        self.check()
        remaining = int((self.end - time.monotonic()) * 1000)
        if remaining < 1:
            raise ValueError
        return min(remaining, cap)


def _preflight_result(result, meter):
    """Bound every supplied DTO before any source observation or serialization."""
    import re

    from . import raw_dense_search as dense
    from . import raw_hybrid_search as hybrid
    from . import raw_lexical_search as lexical
    from . import raw_rank_fusion as fusion

    def obj(value, cls):
        meter.reserve(1)
        if type(value) is not cls:
            raise ValueError

    def string(value, *, identifier=False, prefixed=False):
        meter.reserve(1)
        if type(value) is not str or len(value) > 128:
            raise ValueError
        meter.reserve(len(value) + 1)
        if identifier and not re.fullmatch(
            ("sha256:" if prefixed else "") + r"[0-9a-f]{64}", value
        ):
            raise ValueError

    def literal(value, expected):
        string(value)
        if meter.compare_strings(value, expected):
            raise ValueError

    def integer(value, upper=4095):
        meter.reserve(1)
        if type(value) is not int or not 0 <= value <= upper:
            raise ValueError

    def boolean(value):
        meter.reserve(1)
        if type(value) is not bool:
            raise ValueError

    def sequence(value, maximum):
        meter.reserve(1)
        if type(value) is not tuple or len(value) > maximum:
            raise ValueError

    def ordinals(value, maximum):
        sequence(value, maximum)
        for ordinal in value:
            integer(ordinal)

    def identifiers(value, fields):
        for name in fields:
            meter.reserve(1)
            string(
                getattr(value, name),
                identifier=True,
                prefixed=name
                in (
                    "trace_id",
                    "snapshot_id",
                    "catalog_id",
                    "query_definition_fingerprint",
                    "partition_id",
                    "chunk_id",
                    "revision_id",
                ),
            )

    def counters(value, fields):
        for name in fields:
            meter.reserve(1)
            integer(getattr(value, name), 4096)

    obj(result, hybrid.HybridResult)
    identifiers(
        result,
        (
            "snapshot_id",
            "catalog_id",
            "query_id",
            "query_text_sha256",
            "query_payload_sha256",
            "authority_sha256",
        ),
    )
    literal(result.query_origin, "SUPPLIED_UNVERIFIED")
    literal(result.qualification, "NOT_QUALIFIED")
    total_bytes = 0
    for result_part, module, is_dense in (
        (result.dense, dense, True),
        (result.lexical, lexical, False),
    ):
        obj(result_part, module.DenseResult if is_dense else module.LexicalResult)
        identifiers(
            result_part,
            ("snapshot_id", "catalog_id", "query_payload_sha256")
            if is_dense
            else ("snapshot_id", "catalog_id", "query_text_sha256", "analyzer_fingerprint"),
        )
        if is_dense:
            literal(result_part.query_origin, "SUPPLIED_UNVERIFIED")
            literal(result_part.qualification, "NOT_QUALIFIED")
            counts = result_part.allowed_partition_counts
        else:
            literal(result_part.backend, "bm25s-lucene/0.2.14/2.5.4/1.18.1")
            literal(result_part.method, "lucene")
            counts = result_part.partitions
        counters(
            result_part,
            ("eligible", "selected", "returned")
            if is_dense
            else ("eligible", "matching", "selected", "returned"),
        )
        boolean(result_part.partition_cap_applied)
        boolean(result_part.global_cap_applied)
        sequence(counts, 128)
        for count in counts:
            obj(count, module.PartitionCount)
            identifiers(count, ("partition_id",))
            counters(
                count,
                ("eligible", "selected", "returned")
                if is_dense
                else ("eligible", "matching", "selected", "returned"),
            )
        trace = result_part.trace
        obj(trace, module.DenseTrace if is_dense else module.LexicalTrace)
        ids = ("trace_id", "snapshot_id", "catalog_id", "authority_sha256")
        ids += (
            (
                "query_payload_sha256",
                "query_space_id",
                "query_definition_fingerprint",
                "query_policy_id",
                "query_execution_fingerprint",
            )
            if is_dense
            else ("query_text_sha256", "analyzer_fingerprint")
        )
        identifiers(trace, ids)
        if not is_dense:
            literal(trace.backend, "bm25s-lucene/0.2.14/2.5.4/1.18.1")
            literal(trace.method, "lucene")
        for name, expected in (("input_origin", "SUPPLIED_UNVERIFIED"),
                               ("qualification", "NOT_QUALIFIED"),
                               ("authorization_status", "SUPPLIED_SCOPE_CHECKS_ONLY"),
                               ("execution_status", "NOT_ATTESTED")):
            literal(getattr(trace, name), expected)
        integer(trace.k, 60)
        integer(trace.partition_cap, 60)
        if trace.k != 60 or trace.partition_cap != 60:
            raise ValueError
        sequence(trace.rows, 512)
        for row in trace.rows:
            obj(row, module.DenseTraceRow if is_dense else module.LexicalTraceRow)
            integer(row.ordinal)
            identifiers(row, ("partition_id", "chunk_id", "revision_id", "representation_id"))
        sequence(trace.partitions, 128)
        ordinals(trace.selected_ordinals, 512)
        ordinals(trace.returned_ordinals, 60)
        ordinal_count = len(trace.selected_ordinals) + len(trace.returned_ordinals)
        for part in trace.partitions:
            obj(part, module.DensePartitionTrace if is_dense else module.LexicalPartitionTrace)
            identifiers(part, ("partition_id",))
            for name in (
                "eligible_ordinals",
                "ranked_ordinals",
                "selected_ordinals",
                "returned_ordinals",
            ):
                values = getattr(part, name)
                ordinals(values, 60 if name == "returned_ordinals" else 512)
                ordinal_count += len(values)
                if ordinal_count > 2176:
                    raise ValueError
        sequence(result_part.hits, 60)
        for hit in result_part.hits:
            obj(hit, module.Hit)
            total_bytes += _preflight_hit(hit, meter, fusion_hit=False, dense_hit=is_dense)
            if total_bytes > 16777216:
                raise ValueError
    fr = result.fusion
    obj(fr, fusion.FusionResult)
    identifiers(fr, ("snapshot_id", "catalog_id", "query_id"))
    for name, expected in (("ranking_origin", "SUPPLIED_UNVERIFIED"),
                           ("qualification", "NOT_QUALIFIED"),
                           ("dense_status", "COMPLETE"), ("lexical_status", "COMPLETE")):
        literal(getattr(fr, name), expected)
    boolean(fr.degraded)
    if fr.degraded is not False:
        raise ValueError
    boolean(fr.global_cap_applied)
    counters(
        fr,
        (
            "dense_input_rows",
            "lexical_input_rows",
            "unique_candidates",
            "overlap_candidates",
            "returned",
        ),
    )
    sequence(fr.hits, 60)
    for hit in fr.hits:
        obj(hit, fusion.Hit)
        total_bytes += _preflight_hit(hit, meter, fusion_hit=True, dense_hit=False)
        if total_bytes > 16777216:
            raise ValueError


def _preflight_hit(hit, meter, *, fusion_hit, dense_hit):
    import math
    import re

    meter.reserve(8)
    if type(hit.ordinal) is not int or not 0 <= hit.ordinal < 4096:
        raise ValueError
    for name in ("partition_id", "chunk_id", "revision_id", "representation_id"):
        value = getattr(hit, name)
        if type(value) is not str or len(value) > 128:
            raise ValueError
        meter.reserve(len(value) + 1)
        prefix = "" if name == "representation_id" else "sha256:"
        if not re.fullmatch(prefix + r"[0-9a-f]{64}", value):
            raise ValueError
    chunk = hit.original_chunk_bytes if dense_hit or fusion_hit else hit.chunk_bytes
    if (
        type(hit.scope_bytes) is not bytes
        or len(hit.scope_bytes) > 262144
        or type(chunk) is not bytes
        or len(chunk) > 16777216
        or type(hit.rank) is not int
        or not 1 <= hit.rank <= 60
        or type(hit.score) is not float
        or not math.isfinite(hit.score)
    ):
        raise ValueError
    if fusion_hit:
        for rank in (hit.dense_rank, hit.lexical_rank):
            meter.reserve(1)
            if rank is not None and (type(rank) is not int or not 1 <= rank <= 60):
                raise ValueError
    return len(hit.scope_bytes) + len(chunk)


def _preflight_inputs(
    root, dataset_bytes, case_id, gold_bundle_ids, query_payload, identifiers, deadline_ms, meter
):
    import math
    import re
    import struct
    import unicodedata

    if (
        type(root) is not str
        or not 1 <= len(root) <= 4096
        or type(dataset_bytes) is not bytes
        or not 1 <= len(dataset_bytes) <= 1048576
        or type(case_id) is not str
        or not 1 <= len(case_id) <= 128
        or type(gold_bundle_ids) is not tuple
        or len(gold_bundle_ids) > 128
        or type(query_payload) is not bytes
        or len(query_payload) != 4096
        or type(deadline_ms) is not int
        or not 1 <= deadline_ms <= 120000
        or type(identifiers) is not tuple
        or len(identifiers) != 4
    ):
        raise ValueError
    meter.reserve(len(root) + 1, 4 * len(root))
    root_bytes = root.encode("utf-8")
    if (
        len(root_bytes) > 4096
        or not root.startswith("/")
        or root == "/"
        or any(unicodedata.category(char) == "Cc" for char in root)
    ):
        raise ValueError
    meter.reserve(len(root) + 1)
    if root.count("/") > 64:
        raise ValueError
    meter.reserve(len(root) + 1, 128 * 64 + 4 * len(root))
    components = root[1:].split("/")
    if len(components) > 64 or any(part in ("", ".", "..") for part in components):
        raise ValueError
    meter.reserve(len(case_id) + 1)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", case_id):
        raise ValueError
    previous = None
    for ident in gold_bundle_ids:
        meter.reserve(1)
        if type(ident) is not str or len(ident) != 64:
            raise ValueError
        meter.reserve(len(ident) + 1)
        if not re.fullmatch(r"[0-9a-f]{64}", ident):
            raise ValueError
        if previous is not None and meter.compare_strings(previous, ident) >= 0:
            raise ValueError
        previous = ident
    for index, ident in enumerate(identifiers):
        meter.reserve(1)
        expected_length = 71 if index == 1 else 64
        if type(ident) is not str or len(ident) != expected_length:
            raise ValueError
        meter.reserve(len(ident) + 1)
        prefix = "sha256:" if index == 1 else ""
        if not re.fullmatch(prefix + r"[0-9a-f]{64}", ident):
            raise ValueError
    meter.reserve(len(query_payload) + 1 + 4 * 1024, len(query_payload) + 128 * 1024)
    vector = struct.unpack("<1024f", query_payload)
    norm_squared = 0.0
    for value in vector:
        if not math.isfinite(value):
            raise ValueError
        norm_squared += value * value
    if abs(math.sqrt(norm_squared) - 1.0) > 1e-4:
        raise ValueError


def _validate_trace_relations(result, eligible_rows, matching, meter, *, dense):
    """Validate bounded producer relations against independently observed rows.

    ``matching`` is a 4096-entry boolean table derived from catalog terms. The
    caller has already preflighted the producer DTOs and admitted source rows.
    """
    trace = result.trace
    if type(eligible_rows) is not tuple or len(eligible_rows) > 512:
        raise ValueError
    if type(matching) is not list or len(matching) != 4096:
        raise ValueError
    meter.reserve(4096 * 4, 128 * 4096 * 4)
    by_ordinal = [None] * 4096
    selected = [False] * 4096
    observed_selected = [False] * 4096
    ranked = [False] * 4096
    previous_ordinal = -1
    if len(trace.rows) != len(eligible_rows):
        raise ValueError
    for source, row in zip(eligible_rows, trace.rows, strict=True):
        meter.reserve(3)
        ordinal = source.ordinal
        if type(ordinal) is not int or not previous_ordinal < ordinal < 4096:
            raise ValueError
        previous_ordinal = ordinal
        if row.ordinal != ordinal:
            raise ValueError
        for field in ("partition_id", "chunk_id", "revision_id", "representation_id"):
            meter.reserve(2)
            if meter.compare_strings(getattr(source, field), getattr(row, field)):
                raise ValueError
        by_ordinal[ordinal] = source
    # A fixed ordinal array avoids hashing arbitrary source identifiers. Duplicate
    # chunk and representation IDs are checked by charged comparisons.
    for index, row in enumerate(trace.rows):
        for previous_index in range(index):
            meter.reserve(3)
            previous = trace.rows[previous_index]
            if (
                meter.compare_strings(row.chunk_id, previous.chunk_id) == 0
                or meter.compare_strings(row.representation_id, previous.representation_id) == 0
            ):
                raise ValueError
    counts = result.allowed_partition_counts if dense else result.partitions
    if len(trace.partitions) != len(counts):
        raise ValueError
    previous_partition = None
    eligible_total = ranked_total = selected_total = returned_total = 0
    for part, count in zip(trace.partitions, counts, strict=True):
        meter.reserve(2)
        if (
            previous_partition is not None
            and meter.compare_strings(previous_partition, part.partition_id) >= 0
        ):
            raise ValueError
        previous_partition = part.partition_id
        if meter.compare_strings(part.partition_id, count.partition_id):
            raise ValueError
        # Build the expected partition in catalog ordinal order.
        meter.reserve(len(eligible_rows), 128 * len(eligible_rows))
        expected = []
        for source in eligible_rows:
            meter.reserve(1)
            if meter.compare_strings(source.partition_id, part.partition_id) == 0:
                expected.append(source.ordinal)
        if not expected or len(part.eligible_ordinals) != len(expected):
            raise ValueError
        for actual, wanted in zip(part.eligible_ordinals, expected, strict=True):
            meter.reserve(1)
            if actual != wanted:
                raise ValueError
        expected_rank_count = 0
        for ordinal in expected:
            meter.reserve(1)
            if dense or matching[ordinal] is True:
                expected_rank_count += 1
            elif matching[ordinal] is not False:
                raise ValueError
        if len(part.ranked_ordinals) != expected_rank_count:
            raise ValueError
        for ordinal in part.ranked_ordinals:
            meter.reserve(3)
            source = by_ordinal[ordinal]
            if (
                source is None
                or ranked[ordinal]
                or meter.compare_strings(source.partition_id, part.partition_id)
                or (not dense and matching[ordinal] is not True)
            ):
                raise ValueError
            ranked[ordinal] = True
        if len(part.selected_ordinals) != min(60, len(part.ranked_ordinals)):
            raise ValueError
        for index, ordinal in enumerate(part.selected_ordinals):
            meter.reserve(2)
            if ordinal != part.ranked_ordinals[index] or selected[ordinal]:
                raise ValueError
            selected[ordinal] = True
        position = 0
        for ordinal in trace.returned_ordinals:
            meter.reserve(2)
            source = by_ordinal[ordinal]
            if source is None:
                raise ValueError
            if meter.compare_strings(source.partition_id, part.partition_id) == 0:
                if (
                    position >= len(part.returned_ordinals)
                    or part.returned_ordinals[position] != ordinal
                ):
                    raise ValueError
                position += 1
        if position != len(part.returned_ordinals):
            raise ValueError
        eligible_total += len(expected)
        ranked_total += expected_rank_count
        selected_total += len(part.selected_ordinals)
        returned_total += len(part.returned_ordinals)
        if (
            count.eligible != len(expected)
            or count.selected != len(part.selected_ordinals)
            or count.returned != len(part.returned_ordinals)
            or (not dense and count.matching != expected_rank_count)
        ):
            raise ValueError
    if eligible_total != len(eligible_rows) or len(trace.selected_ordinals) != selected_total:
        raise ValueError
    for ordinal in trace.selected_ordinals:
        meter.reserve(2)
        if not selected[ordinal] or observed_selected[ordinal]:
            raise ValueError
        observed_selected[ordinal] = True
    if len(trace.returned_ordinals) != min(60, selected_total):
        raise ValueError
    for index, ordinal in enumerate(trace.returned_ordinals):
        meter.reserve(1)
        if ordinal != trace.selected_ordinals[index]:
            raise ValueError
    if (
        result.eligible != eligible_total
        or result.selected != selected_total
        or result.returned != returned_total
        or returned_total != len(trace.returned_ordinals)
        or result.partition_cap_applied != (ranked_total > selected_total)
        or result.global_cap_applied != (selected_total > returned_total)
        or (not dense and result.matching != ranked_total)
    ):
        raise ValueError
    if len(result.hits) != returned_total:
        raise ValueError
    for index, hit in enumerate(result.hits):
        meter.reserve(2)
        if hit.rank != index + 1 or hit.ordinal != trace.returned_ordinals[index]:
            raise ValueError
        source = by_ordinal[hit.ordinal]
        for field in ("partition_id", "chunk_id", "revision_id", "representation_id"):
            meter.reserve(2)
            if meter.compare_strings(getattr(hit, field), getattr(source, field)):
                raise ValueError


def _validate_trace_hash(trace, expected_header, meter, check, *, dense):
    """Reproduce the producer's versioned canonical trace wire format."""
    if type(expected_header) is not dict:
        raise ValueError
    common = ("snapshot_id", "catalog_id", "authority_sha256")
    specific = (
        (
            "query_payload_sha256",
            "query_space_id",
            "query_definition_fingerprint",
            "query_policy_id",
            "query_execution_fingerprint",
        )
        if dense
        else ("query_text_sha256", "analyzer_fingerprint", "backend", "method")
    )
    names = common + specific
    if len(expected_header) != len(names):
        raise ValueError
    meter.reserve(12 + len(names), 128 * (12 + len(names)))
    wire = {
        "schema": 1,
        "kind": (
            "slaif-raw-dense-authorized-trace-v1"
            if dense
            else "slaif-raw-lexical-authorized-trace-v1"
        ),
        "k": 60,
        "partition_cap": 60,
    }
    for name in names:
        meter.reserve(2, 128)
        if name not in expected_header or meter.compare_strings(
            getattr(trace, name), expected_header[name]
        ):
            raise ValueError
        wire[name] = getattr(trace, name)
    for name, expected in (
        ("input_origin", "SUPPLIED_UNVERIFIED"),
        ("qualification", "NOT_QUALIFIED"),
        ("authorization_status", "SUPPLIED_SCOPE_CHECKS_ONLY"),
        ("execution_status", "NOT_ATTESTED"),
    ):
        meter.reserve(1)
        if meter.compare_strings(getattr(trace, name), expected):
            raise ValueError
    if trace.k != 60 or trace.partition_cap != 60:
        raise ValueError
    meter.reserve(
        len(trace.rows) + len(trace.partitions), 128 * (len(trace.rows) + len(trace.partitions))
    )
    rows = []
    for row in trace.rows:
        meter.reserve(5, 128 * 5)
        rows.append(
            {
                "ordinal": row.ordinal,
                "partition_id": row.partition_id,
                "chunk_id": row.chunk_id,
                "revision_id": row.revision_id,
                "representation_id": row.representation_id,
            }
        )
    parts = []
    for part in trace.partitions:
        meter.reserve(5, 128 * 5)
        parts.append(
            {
                "partition_id": part.partition_id,
                "eligible_ordinals": part.eligible_ordinals,
                "ranked_ordinals": part.ranked_ordinals,
                "selected_ordinals": part.selected_ordinals,
                "returned_ordinals": part.returned_ordinals,
            }
        )
    wire["rows"] = rows
    wire["partitions"] = parts
    wire["selected_ordinals"] = trace.selected_ordinals
    wire["returned_ordinals"] = trace.returned_ordinals
    domain = (
        b"slaif-raw-dense-authorized-trace-v1\n"
        if dense
        else b"slaif-raw-lexical-authorized-trace-v1\n"
    )
    actual = "sha256:" + _canonical_hash(wire, domain, meter, check)
    if meter.compare_strings(actual, trace.trace_id):
        raise ValueError


def _validate_fusion(
    result, catalog_rows, expected_snapshot, expected_catalog, expected_query, meter
):
    """Validate RRF over supplied modality order, without executing either search."""
    fusion = result.fusion
    for name, expected in (
        ("snapshot_id", expected_snapshot),
        ("catalog_id", expected_catalog),
        ("query_id", expected_query),
        ("ranking_origin", "SUPPLIED_UNVERIFIED"),
        ("qualification", "NOT_QUALIFIED"),
        ("dense_status", "COMPLETE"),
        ("lexical_status", "COMPLETE"),
    ):
        meter.reserve(1)
        if meter.compare_strings(getattr(fusion, name), expected):
            raise ValueError
    if fusion.degraded is not False:
        raise ValueError
    meter.reserve(4096 * 3, 128 * 4096 * 3)
    dense_ranks = [None] * 4096
    lexical_ranks = [None] * 4096
    entries = [None] * 4096
    count = overlap = 0
    for hits, ranks in ((result.dense.hits, dense_ranks), (result.lexical.hits, lexical_ranks)):
        for index, hit in enumerate(hits):
            meter.reserve(5)
            ordinal = hit.ordinal
            if ranks[ordinal] is not None or hit.rank != index + 1:
                raise ValueError
            ranks[ordinal] = hit.rank
            if entries[ordinal] is None:
                entries[ordinal] = hit
                count += 1
            else:
                previous = entries[ordinal]
                for field in ("partition_id", "chunk_id", "revision_id", "representation_id"):
                    if meter.compare_strings(getattr(previous, field), getattr(hit, field)):
                        raise ValueError
                overlap += 1
    if (
        fusion.dense_input_rows != len(result.dense.hits)
        or fusion.lexical_input_rows != len(result.lexical.hits)
        or fusion.unique_candidates != count
        or fusion.overlap_candidates != overlap
        or fusion.returned != min(count, 60)
        or len(fusion.hits) != min(count, 60)
        or fusion.global_cap_applied is not (count > 60)
    ):
        raise ValueError
    meter.reserve(count * 5, count * 5 * 128)
    candidates = []
    for ordinal in range(4096):
        meter.reserve(1)
        entry = entries[ordinal]
        if entry is None:
            continue
        dr, lr = dense_ranks[ordinal], lexical_ranks[ordinal]
        score = 0.0
        if dr is not None:
            meter.reserve(3)
            score += 1.0 / (60 + dr)
        if lr is not None:
            meter.reserve(3)
            score += 1.0 / (60 + lr)
        candidates.append((entry, dr, lr, score))

    def before(left, right):
        meter.reserve(1)
        if left[3] != right[3]:
            return left[3] > right[3]
        for field in ("chunk_id", "revision_id", "representation_id"):
            comparison = meter.compare_strings(getattr(left[0], field), getattr(right[0], field))
            if comparison:
                return comparison < 0
        return True

    width = 1
    while width < count:
        meter.reserve(count, 128 * count)
        out = []
        for start in range(0, count, 2 * width):
            middle = min(start + width, count)
            end = min(start + 2 * width, count)
            left, right = start, middle
            while left < middle and right < end:
                if before(candidates[left], candidates[right]):
                    out.append(candidates[left])
                    left += 1
                else:
                    out.append(candidates[right])
                    right += 1
            while left < middle:
                out.append(candidates[left])
                left += 1
            while right < end:
                out.append(candidates[right])
                right += 1
        candidates = out
        width *= 2
    for index, hit in enumerate(fusion.hits):
        meter.reserve(7)
        entry, dr, lr, score = candidates[index]
        if (
            hit.ordinal != entry.ordinal
            or hit.rank != index + 1
            or hit.dense_rank != dr
            or hit.lexical_rank != lr
            or hit.score != score
        ):
            raise ValueError
        for field in ("partition_id", "chunk_id", "revision_id", "representation_id"):
            if meter.compare_strings(getattr(hit, field), getattr(entry, field)):
                raise ValueError
        if hit.ordinal >= len(catalog_rows):
            raise ValueError
        source = catalog_rows[hit.ordinal]
        for actual, expected in (
            (hit.scope_bytes, source.scope_bytes),
            (hit.original_chunk_bytes, source.chunk_bytes),
        ):
            meter.reserve(len(actual) + len(expected) + 1)
            if actual != expected:
                raise ValueError
    meter.reserve(count, 128 * count)
    union = []
    for ordinal in range(4096):
        meter.reserve(1)
        if entries[ordinal] is not None:
            union.append(ordinal)
    meter.reserve(len(union), 128 * len(union))
    return tuple(union)


def _matching_universe(question, analyzer_fingerprint, catalog_rows, eligible_rows, meter, check):
    """Derive lexical membership from analyzed question and eligible catalog terms."""
    from . import technical_analyzer

    if type(question) is not str or len(question) > 8192:
        raise ValueError
    meter.reserve(2000000, 4 * len(question))
    check()
    analysis = technical_analyzer.analyze(question)
    check()
    meter.reserve(72, 128 + 71)
    expected_analyzer_id = "sha256:" + analyzer_fingerprint
    if (
        type(analysis) is not technical_analyzer.Analysis
        or type(analysis.terms) is not tuple
        or len(analysis.terms) > 2048
        or meter.compare_strings(analysis.analyzer_id, expected_analyzer_id)
    ):
        raise ValueError
    total_chars = 0
    for term in analysis.terms:
        meter.reserve(1)
        if (
            type(term) is not technical_analyzer.Term
            or type(term.text) is not str
            or not 1 <= len(term.text) <= 4096
        ):
            raise ValueError
        total_chars += len(term.text)
    meter.reserve(len(analysis.terms), 128 * len(analysis.terms) + 4 * total_chars)
    query_terms = []
    for term in analysis.terms:
        meter.reserve(1)
        query_terms.append(term.text)
    meter.reserve(len(query_terms), 128 * len(query_terms))
    query_terms = _sort_unique_terms(tuple(query_terms), meter)
    if len(query_terms) * len(eligible_rows) > 4000000:
        raise ValueError
    meter.reserve(4096, 128 * 4096)
    matching = [False] * 4096
    total_terms = 0
    all_terms = []
    for declaration in eligible_rows:
        meter.reserve(1)
        row = catalog_rows[declaration.ordinal]
        terms = row.terms
        if type(terms) is not tuple or len(terms) > 200000 - total_terms:
            raise ValueError
        total_terms += len(terms)
        meter.reserve(len(terms), 128 * len(terms))
        text_terms = []
        for term in terms:
            meter.reserve(1)
            if type(term) is not tuple or len(term) != 4:
                raise ValueError
            text = term[0]
            if type(text) is not str or not 1 <= len(text) <= 4096:
                raise ValueError
            meter.reserve(1, 128)
            text_terms.append(text)
            all_terms.append(text)
        meter.reserve(len(text_terms), 128 * len(text_terms))
        sorted_terms = _sort_unique_terms(tuple(text_terms), meter)
        matching[declaration.ordinal] = _terms_intersect(query_terms, sorted_terms, meter)
    meter.reserve(len(all_terms), 128 * len(all_terms))
    if len(_sort_unique_terms(tuple(all_terms), meter)) > 100000:
        raise ValueError
    return matching


def _admit_authority(grants, restrictions, case_scope, meter, check):
    """Snapshot bounded caller authority, then intersect grants with case scope."""
    from . import provenance_records as provenance
    from . import text_evaluation_dataset as dataset

    if type(case_scope) is not dataset.DeclaredScope:
        raise ValueError
    total = 0
    snapshots = []
    for value, cls, fields, optional in (
        (grants, provenance.Grants, ("corpora", "versions", "labels"), False),
        (restrictions, provenance.Restrictions, ("corpora", "versions"), True),
    ):
        meter.reserve(1)
        if value is None:
            if not optional:
                raise ValueError
            snapshots.append(None)
            continue
        if (
            type(value) is not cls
            or type(value.__dict__) is not dict
            or len(value.__dict__) != len(fields) + 1
            or value.__dict__.get("schema_version") != 1
            or type(value.__dict__.get("schema_version")) is not int
            or value.__pydantic_extra__ is not None
        ):
            raise ValueError
        for field in fields:
            meter.reserve(1)
            if field not in value.__dict__:
                raise ValueError
            entries = value.__dict__[field]
            if optional and entries is None:
                continue
            if type(entries) is not tuple or len(entries) > 128:
                raise ValueError
            for entry in entries:
                meter.reserve(1)
                if type(entry) is not str:
                    raise ValueError
                total += len(entry)
                if total > 65536:
                    raise ValueError
                meter.reserve(len(entry) + 1, 4 * len(entry))
                entry.encode("utf-8")
        meter.reserve(1, 128 * (len(fields) + 1))
        check()
        snapshots.append(provenance._snapshot(value, cls))
        check()
    original, restriction_snapshot = snapshots
    values = []
    for field in ("corpora", "versions", "labels"):
        source = getattr(original, field)
        allowed = getattr(case_scope, field)
        if type(allowed) is not tuple or len(allowed) > 128:
            raise ValueError
        meter.reserve(len(source), 128 * len(source))
        retained = []
        for item in source:
            for candidate in allowed:
                meter.reserve(1)
                if type(candidate) is not str or len(candidate) > 4096:
                    raise ValueError
                if meter.compare_strings(item, candidate) == 0:
                    retained.append(item)
                    break
        values.append(tuple(retained))
    meter.reserve(4, 128 * 4)
    check()
    effective = provenance.Grants(
        schema_version=1, corpora=values[0], versions=values[1], labels=values[2]
    )
    check()
    return original, effective, restriction_snapshot



def _declaration_bytes(text):
    """Encode one already bounded declaration JSON string."""
    return text.encode("utf-8")


def _check_declaration_wire(obj, expected, meter, check):
    """Reserve a conservative complete wire envelope before serialization."""
    import json

    if type(obj) is not dict or len(obj) > 32 or type(expected) is not bytes:
        raise ValueError
    if len(expected) > 262144:
        raise ValueError
    bound = 2
    for key, value in obj.items():
        meter.reserve(2)
        if type(key) is not str or len(key) > 128:
            raise ValueError
        meter.reserve(len(key) + 1)
        if type(value) is str:
            if len(value) > 128:
                raise ValueError
            meter.reserve(len(value) + 1)
            value_bound = 12 * len(value) + 2
        elif type(value) is int and -(2**63) <= value < 2**63:
            meter.reserve(1)
            value_bound = 20
        else:
            raise ValueError
        bound += 2 + 12 * len(key) + 2 + value_bound
    if bound > 262144:
        raise ValueError
    # Charge the JSON text temporary, UTF-8 copy, emitted bytes and comparison
    # against the admitted declaration before either encoder or copy runs.
    meter.reserve(3 * bound + len(expected) + 1, 3 * bound)
    check()
    text = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False)
    check()
    wire = _declaration_bytes(text)
    check()
    if len(wire) > bound or wire != expected:
        raise ValueError

def _catalog_eligible(catalog, captured, grants, restrictions, meter, check):
    """Admit all catalog declarations and scopes before selecting eligible rows."""
    from . import provenance_records as provenance
    from . import raw_snapshot_catalog
    from . import raw_snapshot_rows

    if (
        type(catalog) is not raw_snapshot_catalog.Catalog
        or type(catalog.rows) is not tuple
        or len(catalog.rows) > 512
        or type(catalog.core_bytes) is not bytes
        or len(catalog.core_bytes) > 262144
        or type(catalog.row_map_bytes) is not bytes
        or len(catalog.row_map_bytes) > 16777216
        or type(catalog.snapshot_id) is not str
        or type(catalog.catalog_id) is not str
    ):
        raise ValueError
    meter.reserve(len(catalog.core_bytes) + len(catalog.row_map_bytes) + 2)
    if (
        catalog.snapshot_id != captured.pointer.snapshot_id
        or catalog.core_bytes != captured.data.core_bytes
        or catalog.row_map_bytes != captured.data.row_map.map_bytes
    ):
        raise ValueError
    for data in (catalog.core_bytes, catalog.row_map_bytes):
        meter.reserve(len(data) + 1, len(data))
    check()
    mapping = raw_snapshot_rows.bind(catalog.core_bytes, catalog.row_map_bytes)
    check()
    if type(mapping) is not raw_snapshot_rows.RawRowMap or len(mapping.rows) != len(catalog.rows):
        raise ValueError
    row_fields = tuple(raw_snapshot_rows.Row.__dataclass_fields__)
    meter.reserve(len(mapping.rows), 128 * len(mapping.rows))
    eligible = []
    bundles = []
    groups = []
    for ordinal, (declaration, row) in enumerate(zip(mapping.rows, catalog.rows, strict=True)):
        meter.reserve(2)
        if (
            type(declaration) is not raw_snapshot_rows.Row
            or type(row) is not raw_snapshot_catalog.CatalogRow
            or declaration.ordinal != ordinal
            or row.representation_id != declaration.representation_id
            or type(row.declaration_bytes) is not bytes
            or len(row.declaration_bytes) > 262144
            or type(row.scope_bytes) is not bytes
            or len(row.scope_bytes) > 262144
            or type(row.chunk_bytes) is not bytes
            or len(row.chunk_bytes) > 16777216
        ):
            raise ValueError
        bundle_found = False
        group_found = False
        for bundle in bundles:
            if meter.compare_strings(declaration.bundle_container_id, bundle) == 0:
                bundle_found = True
                break
        for bundle, batch in groups:
            if (
                meter.compare_strings(declaration.bundle_container_id, bundle) == 0
                and meter.compare_strings(declaration.batch_container_id, batch) == 0
            ):
                group_found = True
                break
        if not bundle_found:
            meter.reserve(1, 128)
            bundles.append(declaration.bundle_container_id)
            if len(bundles) > 128:
                raise ValueError
        if not group_found:
            meter.reserve(2, 256)
            groups.append((declaration.bundle_container_id, declaration.batch_container_id))
            if len(groups) > 128:
                raise ValueError
        meter.reserve(len(row_fields), 128 * len(row_fields))
        obj = {}
        for field in row_fields:
            meter.reserve(1, 128)
            value = getattr(declaration, field)
            if type(value) is str:
                meter.reserve(len(value) + 1, 12 * len(value))
            elif type(value) is not int:
                raise ValueError
            obj[field] = value
        _check_declaration_wire(obj, row.declaration_bytes, meter, check)
        for data in (row.scope_bytes, row.chunk_bytes):
            meter.reserve(len(data) + 1, len(data))
        check()
        scope = provenance.admit_record("Scope", row.scope_bytes)
        check()
        chunk = provenance.admit_record("Chunk", row.chunk_bytes)
        check()
        meter.reserve(8, 8 * 128 + len(row.scope_bytes))
        check()
        scope_object = scope.model_dump(mode="json")
        check()
        scope_identity = _canonical_hash(
            {"kind": "embedding-source-scope-v1", "scope": scope_object},
            b"slaif-fingerprint-v1\n", meter, check,
        )
        partition_identity = "sha256:" + _canonical_hash(
            {"schema": 1, "corpus": scope.corpus, "version": scope.version,
             "labels": scope.labels}, b"slaif-fingerprint-v1\n", meter, check,
        )
        meter.reserve(7)
        if (
            meter.compare_strings(scope_identity, declaration.source_scope_sha256)
            or meter.compare_strings(partition_identity, declaration.partition_id)
            or meter.compare_strings(chunk.policy_id, "sha256:" + mapping.chunk_policy_fingerprint)
            or scope.revision_id != declaration.revision_id
            or chunk.chunk_id != declaration.chunk_id
            or chunk.revision_id != declaration.revision_id
            or chunk.extraction_id != declaration.extraction_id
        ):
            raise ValueError
        check()
        allowed = provenance.reader_allows(scope, grants, restrictions)
        check()
        if type(allowed) is not bool:
            raise ValueError
        if allowed:
            eligible.append(declaration)
    meter.reserve(len(eligible), 128 * len(eligible))
    return tuple(eligible)


def _geometry_inputs(
    binding,
    eligible,
    catalog_rows,
    result,
    fusion_union,
    dataset,
    data,
    snapshot_id,
    catalog_id,
    authority_sha256,
    meter,
    check,
):
    """Validate the owned ranking and build pure geometry plus its exact ledger."""
    import hashlib
    import re

    from . import source_bound_ranking as ranking

    if (
        type(binding) is not ranking.BoundRanking
        or type(binding.rows) is not tuple
        or len(binding.rows) != len(eligible)
        or binding.row_count != len(eligible)
    ):
        raise ValueError
    for name, expected in (
        ("snapshot_id", snapshot_id),
        ("catalog_id", catalog_id),
        ("authority_sha256", authority_sha256),
        (
            "source_binding_status",
            "ORIGINALS_REVALIDATED_AT_BIND_TIME" if eligible else "NO_SELECTED_SOURCE_VALIDATED",
        ),
        ("input_origin", "SUPPLIED_RANKING_UNVERIFIED"),
        ("authorization_status", "SUPPLIED_SCOPE_CHECKS_ONLY"),
        ("execution_status", "NOT_ATTESTED"),
        ("qualification", "NOT_QUALIFIED"),
    ):
        meter.reserve(1)
        if meter.compare_strings(getattr(binding, name), expected):
            raise ValueError
    meter.reserve(4096 + len(eligible), 128 * (4096 + len(eligible)))
    local = [-1] * 4096
    rows = []
    fragment_count = block_chars = 0
    serial_rows = []
    meter.reserve(len(eligible), 128 * len(eligible))
    for index, (source, bound) in enumerate(zip(eligible, binding.rows, strict=True)):
        meter.reserve(2)
        if type(bound) is not ranking.BoundRow or bound.ordinal != source.ordinal:
            raise ValueError
        for field in (
            "partition_id",
            "chunk_id",
            "revision_id",
            "extraction_id",
            "representation_id",
            "bundle_container_id",
            "batch_container_id",
        ):
            meter.reserve(1)
            if meter.compare_strings(getattr(bound, field), getattr(source, field)):
                raise ValueError
        scope_bytes = catalog_rows[source.ordinal].scope_bytes
        meter.reserve(len(scope_bytes) + 66, 192)
        check()
        scope_hash = hashlib.sha256(scope_bytes).hexdigest()
        check()
        if meter.compare_strings(bound.scope_sha256, scope_hash):
            raise ValueError
        if type(bound.fragments) is not tuple or not 1 <= len(bound.fragments) <= 256:
            raise ValueError
        fragment_count += len(bound.fragments)
        if fragment_count > 8192:
            raise ValueError
        meter.reserve(len(bound.fragments) * 4, 128 * len(bound.fragments) * 4)
        fragments = []
        serialized_fragments = []
        for fragment in bound.fragments:
            meter.reserve(4)
            if (
                type(fragment) is not ranking.BoundFragment
                or type(fragment.block_id) is not str
                or not 1 <= len(fragment.block_id) <= 256
                or type(fragment.start) is not int
                or type(fragment.end) is not int
                or not 0 <= fragment.start < fragment.end <= 200000
                or type(fragment.text_sha256) is not str
                or len(fragment.text_sha256) != 64
            ):
                raise ValueError
            meter.reserve(
                len(fragment.block_id) + len(fragment.text_sha256) + 2, 4 * len(fragment.block_id)
            )
            if len(fragment.block_id.encode("utf-8")) > 1024 or not re.fullmatch(
                r"[0-9a-f]{64}", fragment.text_sha256
            ):
                raise ValueError
            block_chars += len(fragment.block_id)
            if block_chars > 65536:
                raise ValueError
            fragments.append((fragment.block_id, fragment.start, fragment.end))
            serialized_fragments.append(
                {
                    "block_id": fragment.block_id,
                    "start": fragment.start,
                    "end": fragment.end,
                    "text_sha256": fragment.text_sha256,
                }
            )
        meter.reserve(13, 128 * 13)
        rows.append((bound.chunk_id, bound.revision_id, bound.extraction_id, tuple(fragments)))
        serial_rows.append(
            {
                "ordinal": bound.ordinal,
                "partition_id": bound.partition_id,
                "chunk_id": bound.chunk_id,
                "revision_id": bound.revision_id,
                "extraction_id": bound.extraction_id,
                "representation_id": bound.representation_id,
                "bundle_container_id": bound.bundle_container_id,
                "batch_container_id": bound.batch_container_id,
                "scope_sha256": bound.scope_sha256,
                "fragments": serialized_fragments,
            }
        )
        local[source.ordinal] = index
    if type(binding.fragment_count) is not int or binding.fragment_count != fragment_count:
        raise ValueError
    meter.reserve(9, 128 * 9)
    wire = {
        "schema": 1,
        "kind": "slaif-source-bound-supplied-ranking-v1",
        "snapshot_id": snapshot_id,
        "catalog_id": catalog_id,
        "authority_sha256": authority_sha256,
        "rows": serial_rows,
        "row_count": len(rows),
        "fragment_count": fragment_count,
        "source_binding_status": binding.source_binding_status,
    }
    binding_hash = "sha256:" + _canonical_hash(
        wire, b"slaif-source-bound-supplied-ranking-v1\n", meter, check
    )
    if meter.compare_strings(binding_hash, binding.binding_id):
        raise ValueError

    def convert(ordinals):
        meter.reserve(len(ordinals), 128 * len(ordinals))
        output = []
        for ordinal in ordinals:
            meter.reserve(1)
            index = local[ordinal]
            if index < 0:
                raise ValueError
            output.append(index)
        meter.reserve(len(output), 128 * len(output))
        return tuple(output)

    def flatten(trace, field):
        size = 0
        for part in trace.partitions:
            meter.reserve(1)
            size += len(getattr(part, field))
        meter.reserve(size, 128 * size)
        output = []
        for part in trace.partitions:
            for ordinal in getattr(part, field):
                meter.reserve(1)
                output.append(ordinal)
        meter.reserve(len(output), 128 * len(output))
        return tuple(output)

    dense, lexical = result.dense.trace, result.lexical.trace
    meter.reserve(len(result.fusion.hits), 128 * len(result.fusion.hits))
    fused_ordinals = []
    for hit in result.fusion.hits:
        meter.reserve(1)
        fused_ordinals.append(hit.ordinal)
    meter.reserve(20, 128 * 20)
    stages = (
        ("dense.eligible", convert(flatten(dense, "eligible_ordinals"))),
        ("dense.ranked", convert(flatten(dense, "ranked_ordinals"))),
        ("dense.selected", convert(dense.selected_ordinals)),
        ("dense.returned", convert(dense.returned_ordinals)),
        ("lexical.eligible", convert(flatten(lexical, "eligible_ordinals"))),
        ("lexical.ranked", convert(flatten(lexical, "ranked_ordinals"))),
        ("lexical.selected", convert(lexical.selected_ordinals)),
        ("lexical.returned", convert(lexical.returned_ordinals)),
        ("fusion.input", convert(fusion_union)),
        ("fusion.returned", convert(tuple(fused_ordinals))),
    )
    indices = 0
    for stage in stages:
        meter.reserve(1)
        indices += len(stage[1])
    n, g, c, d = len(rows), dataset.gold_atom_count, dataset.case_count, len(data)
    j = max(1, (fragment_count + 1).bit_length())
    work = 42 * d + 29 * (fragment_count + g + 1) * (j + 6) + 64 * (n + indices + c + g + 1)
    budget = 56 * d + 29 * (4 * block_chars + 96 * fragment_count + 256 * n + 128 * g) + 4194304
    if work > 67108864 or budget > 134217728 or indices > 5120:
        raise ValueError
    return tuple(rows), stages, work, budget


def _pin_check(owner, originals, derived, root, prior, meter, clock):
    """Check one borrowed pin observation without consulting current selection."""
    import hashlib

    from . import raw_snapshot_files, raw_snapshot_pin, raw_snapshot_rows, raw_snapshot_selection

    if (
        type(owner) is not raw_snapshot_pin.PinOwner
        or owner.state != "ACTIVE"
        or owner.originals is not originals
        or owner.derived is not derived
        or owner.op is None
        or owner.op.path != root
    ):
        raise ValueError
    meter.reserve(1)
    clock.check()
    captured = owner.check(deadline_ms=clock.remaining(120000))
    clock.check()
    if (
        type(captured) is not raw_snapshot_pin.PinData
        or type(captured.pointer) is not raw_snapshot_selection.Pointer
        or type(captured.data) is not raw_snapshot_files.BoundSnapshotData
        or type(captured.data.row_map) is not raw_snapshot_rows.RawRowMap
        or captured is not owner.value
        or (prior is not None and captured is not prior)
    ):
        raise ValueError
    pointer = captured.pointer
    if type(pointer.pointer_bytes) is not bytes or len(pointer.pointer_bytes) > 512:
        raise ValueError
    meter.reserve(len(pointer.pointer_bytes) + 1, len(pointer.pointer_bytes))
    clock.check()
    parsed = raw_snapshot_selection.parse_pointer(pointer.pointer_bytes)
    clock.check()
    if parsed != pointer or captured.data.snapshot_id != pointer.snapshot_id:
        raise ValueError
    core = captured.data.core_bytes
    if type(core) is not bytes or len(core) > 262144:
        raise ValueError
    meter.reserve(len(core) + 66, 192)
    clock.check()
    digest = hashlib.sha256(core).hexdigest()
    clock.check()
    if meter.compare_strings(digest, pointer.core_sha256):
        raise ValueError
    return captured


def _validate_gold(gold, dataset, data, bundle_ids, meter, check):
    """Match the full admitted dataset's atoms to a complete owned Gold binding."""
    import hashlib
    import re

    from . import text_evaluation_gold_binding as gold_module

    if (
        type(gold) is not gold_module.BoundGold
        or type(gold.bindings) is not tuple
        or type(gold.observations) is not tuple
        or len(gold.bindings) > 512
        or len(gold.observations) != len(bundle_ids)
    ):
        raise ValueError
    meter.reserve(len(data) + 66, 192)
    check()
    data_hash = hashlib.sha256(data).hexdigest()
    check()
    for name, expected in (
        ("dataset_id", dataset.dataset_id),
        ("split_id", dataset.split_id),
        ("dataset_sha256", data_hash),
        ("qualification", "NOT_QUALIFIED"),
        ("authorship_status", "DECLARED_UNVERIFIED"),
        ("rights_status", "DECLARED_UNVERIFIED"),
        ("split_status", "STRUCTURAL_ONLY"),
    ):
        meter.reserve(1)
        if meter.compare_strings(getattr(gold, name), expected):
            raise ValueError
    if (
        type(gold.case_count) is not int
        or gold.case_count != dataset.case_count
        or type(gold.gold_atom_occurrences) is not int
        or gold.gold_atom_occurrences != dataset.gold_atom_count
        or type(gold.distinct_atom_count) is not int
        or gold.distinct_atom_count != len(gold.bindings)
    ):
        raise ValueError
    status = "ORIGINALS_REVALIDATED_AT_BIND_TIME" if gold.bindings else "NO_GOLD_SOURCE_VALIDATED"
    if meter.compare_strings(gold.source_binding_status, status):
        raise ValueError
    if bool(gold.bindings) != bool(bundle_ids):
        raise ValueError
    meter.reserve(len(gold.bindings), 128 * len(gold.bindings))
    seen = [False] * len(gold.bindings)
    for binding in gold.bindings:
        meter.reserve(7)
        if (type(binding) is not gold_module.GoldBinding or type(binding.start) is not int
                or type(binding.end) is not int or not 0 <= binding.start < binding.end <= 200000
                or type(binding.block_id) is not str or not 1 <= len(binding.block_id) <= 256):
            raise ValueError
        meter.reserve(len(binding.block_id) + 1, 4 * len(binding.block_id))
        if len(binding.block_id.encode("utf-8")) > 1024:
            raise ValueError
        for name, prefix in (("revision_id", "sha256:"), ("extraction_id", "sha256:"),
                             ("text_sha256", "")):
            value = getattr(binding, name)
            if type(value) is not str or len(value) != 64 + len(prefix):
                raise ValueError
            meter.reserve(len(value) + 1)
            if not re.fullmatch(prefix + r"[0-9a-f]{64}", value):
                raise ValueError
    occurrences = 0
    for case in dataset.cases:
        meter.reserve(1)
        for requirement in case.requirements:
            meter.reserve(1)
            for alternative in requirement.alternatives:
                meter.reserve(1)
                for atom in alternative:
                    meter.reserve(1)
                    occurrences += 1
                    found = -1
                    for index, binding in enumerate(gold.bindings):
                        meter.reserve(1)
                        if type(binding) is not gold_module.GoldBinding:
                            raise ValueError
                        equal = True
                        for name in ("revision_id", "extraction_id", "block_id", "text_sha256"):
                            if meter.compare_strings(getattr(atom, name), getattr(binding, name)):
                                equal = False
                                break
                        meter.reserve(2)
                        if equal and atom.start == binding.start and atom.end == binding.end:
                            if found >= 0:
                                raise ValueError
                            found = index
                    if found < 0:
                        raise ValueError
                    seen[found] = True
    if occurrences != dataset.gold_atom_count:
        raise ValueError
    serial_bindings = []
    meter.reserve(len(gold.observations), 128 * len(gold.observations))
    referenced_observations = [False] * len(gold.observations)
    meter.reserve(len(gold.bindings), 128 * len(gold.bindings))
    previous_binding = None
    for index, binding in enumerate(gold.bindings):
        meter.reserve(8, 128 * 8)
        if previous_binding is not None:
            order = 0
            for name in ("revision_id", "extraction_id", "block_id", "start", "end", "text_sha256"):
                left, right = getattr(previous_binding, name), getattr(binding, name)
                if type(left) is str and type(right) is str:
                    order = meter.compare_strings(left, right)
                elif type(left) is int and type(right) is int:
                    meter.reserve(1)
                    order = (left > right) - (left < right)
                else:
                    raise ValueError
                if order:
                    break
            if order >= 0:
                raise ValueError
        previous_binding = binding
        if not seen[index] or type(binding.bundle_ids) is not tuple or not binding.bundle_ids:
            raise ValueError
        previous = None
        for ident in binding.bundle_ids:
            meter.reserve(1)
            if type(ident) is not str or len(ident) != 64:
                raise ValueError
            if previous is not None and meter.compare_strings(previous, ident) >= 0:
                raise ValueError
            previous = ident
            member = False
            for observation_index, supplied in enumerate(bundle_ids):
                if meter.compare_strings(ident, supplied) == 0:
                    observation = gold.observations[observation_index]
                    if (
                        type(observation) is not gold_module.BundleObservation
                        or meter.compare_strings(observation.revision_id, binding.revision_id)
                        or meter.compare_strings(observation.extraction_id, binding.extraction_id)
                    ):
                        raise ValueError
                    referenced_observations[observation_index] = True
                    member = True
                    break
            if not member:
                raise ValueError
        serial_bindings.append(
            {
                "revision_id": binding.revision_id,
                "extraction_id": binding.extraction_id,
                "block_id": binding.block_id,
                "start": binding.start,
                "end": binding.end,
                "text_sha256": binding.text_sha256,
                "bundle_ids": binding.bundle_ids,
            }
        )
    meter.reserve(len(gold.observations), 128 * len(gold.observations))
    observations = []
    total_blocks = total_member_bytes = 0
    for index, (ident, observation) in enumerate(zip(bundle_ids, gold.observations, strict=True)):
        meter.reserve(6, 128 * 6)
        if not referenced_observations[index]:
            raise ValueError
        if (
            type(observation) is not gold_module.BundleObservation
            or meter.compare_strings(ident, observation.bundle_id)
            or type(observation.block_count) is not int
            or not 0 <= observation.block_count <= 4096
            or type(observation.member_bytes) is not int
            or not 0 <= observation.member_bytes <= 100663296
        ):
            raise ValueError
        for name, prefix in (("metadata_sha256", ""), ("revision_id", "sha256:"),
                             ("extraction_id", "sha256:")):
            value = getattr(observation, name)
            if type(value) is not str or len(value) != 64 + len(prefix):
                raise ValueError
            meter.reserve(len(value) + 1)
            if not re.fullmatch(prefix + r"[0-9a-f]{64}", value):
                raise ValueError
        total_blocks += observation.block_count
        total_member_bytes += observation.member_bytes
        if total_blocks > 4096 or total_member_bytes > 100663296:
            raise ValueError
        observations.append(
            {
                "bundle_id": observation.bundle_id,
                "metadata_sha256": observation.metadata_sha256,
                "revision_id": observation.revision_id,
                "extraction_id": observation.extraction_id,
                "block_count": observation.block_count,
                "member_bytes": observation.member_bytes,
            }
        )
    meter.reserve(9, 128 * 9)
    wire = {
        "dataset_id": dataset.dataset_id,
        "split_id": dataset.split_id,
        "dataset_sha256": data_hash,
        "observations": observations,
        "bindings": serial_bindings,
        "case_count": dataset.case_count,
        "gold_atom_occurrences": occurrences,
        "distinct_atom_count": len(gold.bindings),
        "source_binding_status": status,
    }
    identity = "sha256:" + _canonical_hash(
        wire, b"slaif-text-evaluation-gold-binding-v1\n", meter, check
    )
    if meter.compare_strings(identity, gold.binding_id):
        raise ValueError


def _catalog_identity(catalog, meter, check):
    """Reconstruct the catalog identity from all returned source observations."""
    import hashlib

    from . import raw_snapshot_catalog

    def digest(data, limit):
        if type(data) is not bytes or len(data) > limit:
            raise ValueError
        meter.reserve(len(data) + 66, 192)
        check()
        value = hashlib.sha256(data).hexdigest()
        check()
        return value

    def sequence(values, limit):
        if type(values) is not tuple or len(values) > limit:
            raise ValueError
        meter.reserve(len(values), 128 * len(values))
        result = []
        for value in values:
            meter.reserve(1, 128)
            result.append(digest(value, 16777216))
        return result

    if (
        type(catalog) is not raw_snapshot_catalog.Catalog
        or type(catalog.rows) is not tuple
        or len(catalog.rows) > 512
    ):
        raise ValueError
    # Validate all returned term shapes before retaining or processing any term content.
    for row in catalog.rows:
        meter.reserve(1)
        if (type(row) is not raw_snapshot_catalog.CatalogRow or type(row.terms) is not tuple
                or len(row.terms) > 200000):
            raise ValueError
        for term in row.terms:
            meter.reserve(4)
            if (type(term) is not tuple or len(term) != 4 or type(term[0]) is not str
                    or not 1 <= len(term[0]) <= 4096 or type(term[1]) is not int
                    or type(term[2]) is not int or not 0 <= term[1] < term[2] <= 100000
                    or type(term[3]) is not str or len(term[3]) > 128):
                raise ValueError
    meter.reserve(len(catalog.rows), 128 * len(catalog.rows))
    rows = []
    for row in catalog.rows:
        meter.reserve(8, 128 * 8)
        if (type(row.representation_id) is not str or len(row.representation_id) != 64
                or type(row.vector_bytes) is not bytes or len(row.vector_bytes) != 4096):
            raise ValueError
        for term in row.terms:
            meter.reserve(len(term[0]) + len(term[3]) + 2, 4 * len(term[0]))
            if (len(term[0].encode("utf-8")) > 16384
                    or term[3] not in ("literal", "nfkc-casefold", "component",
                                       "component-nfkc-casefold")):
                raise ValueError
        rows.append(
            [
                digest(row.declaration_bytes, 262144),
                digest(row.chunk_bytes, 16777216),
                digest(row.source_bytes, 262144),
                digest(row.scope_bytes, 262144),
                digest(row.rendered_bytes, 16777216),
                row.representation_id,
                digest(row.vector_bytes, 4096),
                row.terms,
            ]
        )
    meter.reserve(8, 128 * 8)
    identity = {
        "version": 1,
        "snapshot_id": catalog.snapshot_id,
        "core": digest(catalog.core_bytes, 262144),
        "row_map": digest(catalog.row_map_bytes, 16777216),
        "revisions": sequence(catalog.revisions, 128),
        "dependencies": sequence(catalog.dependencies, 128),
        "blocks": sequence(catalog.blocks, 4096),
        "rows": rows,
    }
    actual = "sha256:" + _canonical_hash(identity, b"", meter, check, ensure_ascii=False)
    if meter.compare_strings(actual, catalog.catalog_id):
        raise ValueError


def _query_identity(
    catalog, question, payload, identifiers, grants, restrictions, result, meter, check
):
    import hashlib
    import json

    from . import technical_analyzer

    def byte_hash(data):
        meter.reserve(len(data) + 66, 192)
        check()
        value = hashlib.sha256(data).hexdigest()
        check()
        return value

    meter.reserve(len(catalog.core_bytes) + 1, len(catalog.core_bytes))
    check()
    core = json.loads(catalog.core_bytes)
    check()
    embedding, analyzer = core["embedding"], core["analyzer"]
    for name, expected in zip(
        (
            "space_id",
            "definition_fingerprint",
            "query_policy_fingerprint",
            "query_execution_fingerprint",
        ),
        identifiers,
        strict=True,
    ):
        meter.reserve(1)
        if meter.compare_strings(embedding[name], expected):
            raise ValueError
    if (
        analyzer["backend"] != "bm25s-lucene"
        or analyzer["bm25s_version"] != "0.2.14"
        or analyzer["numpy_version"] != "2.5.4"
        or analyzer["scipy_version"] != "1.18.1"
    ):
        raise ValueError
    meter.reserve(1)
    check()
    analyzer_id = technical_analyzer.analyzer_id()
    check()
    meter.reserve(72, 128 + 71)
    expected_analyzer_id = "sha256:" + analyzer["fingerprint"]
    if meter.compare_strings(expected_analyzer_id, analyzer_id):
        raise ValueError
    if type(question) is not str or len(question) > 8192:
        raise ValueError
    meter.reserve(len(question) + 1, 4 * len(question))
    question_bytes = question.encode("utf-8")
    if len(question_bytes) > 32768:
        raise ValueError
    question_hash, payload_hash = byte_hash(question_bytes), byte_hash(payload)
    # The snapshots are already bounded; account for both serialized authority objects.
    meter.reserve(8, 8 * 128 + 262144)
    check()
    authority = [
        grants.model_dump(mode="json"),
        None if restrictions is None else restrictions.model_dump(mode="json"),
    ]
    check()
    authority_hash = _canonical_hash(authority, b"", meter, check, ensure_ascii=False, limit=262144)
    meter.reserve(14, 14 * 128)
    query_wire = {
        "kind": "raw-hybrid-query/v1",
        "snapshot_id": catalog.snapshot_id,
        "catalog_id": catalog.catalog_id,
        "query_text_sha256": question_hash,
        "query_payload_sha256": payload_hash,
        "query_space_id": identifiers[0],
        "query_definition_fingerprint": identifiers[1],
        "query_policy_id": identifiers[2],
        "query_execution_fingerprint": identifiers[3],
        "authority_sha256": authority_hash,
        "dense_k": 60,
        "lexical_k": 60,
        "partition_cap": 60,
        "k": 60,
    }
    query_id = _canonical_hash(query_wire, b"", meter, check, ensure_ascii=False)
    for name, expected in (
        ("snapshot_id", catalog.snapshot_id),
        ("catalog_id", catalog.catalog_id),
        ("query_id", query_id),
        ("query_text_sha256", question_hash),
        ("query_payload_sha256", payload_hash),
        ("authority_sha256", authority_hash),
        ("query_origin", "SUPPLIED_UNVERIFIED"),
        ("qualification", "NOT_QUALIFIED"),
    ):
        meter.reserve(1)
        if meter.compare_strings(getattr(result, name), expected):
            raise ValueError
    return question_hash, payload_hash, authority_hash, query_id, analyzer["fingerprint"]


def _validate_modality_headers(
    result,
    snapshot,
    catalog_id,
    text_sha,
    payload_sha,
    authority_sha,
    identifiers,
    analyzer,
    rows,
    meter,
    check,
):
    meter.reserve(24, 24 * 128)
    common = {"snapshot_id": snapshot, "catalog_id": catalog_id, "authority_sha256": authority_sha}
    dense_header = dict(
        common,
        query_payload_sha256=payload_sha,
        query_space_id=identifiers[0],
        query_definition_fingerprint=identifiers[1],
        query_policy_id=identifiers[2],
        query_execution_fingerprint=identifiers[3],
    )
    lexical_header = dict(
        common,
        query_text_sha256=text_sha,
        analyzer_fingerprint=analyzer,
        backend="bm25s-lucene/0.2.14/2.5.4/1.18.1",
        method="lucene",
    )
    for result_part, header, dense in (
        (result.dense, dense_header, True),
        (result.lexical, lexical_header, False),
    ):
        for name, expected in header.items():
            if hasattr(result_part, name):
                meter.reserve(1)
                if meter.compare_strings(getattr(result_part, name), expected):
                    raise ValueError
        if dense:
            if (
                result_part.query_origin != "SUPPLIED_UNVERIFIED"
                or result_part.qualification != "NOT_QUALIFIED"
            ):
                raise ValueError
        _validate_trace_hash(result_part.trace, header, meter, check, dense=dense)
        for hit in result_part.hits:
            meter.reserve(1)
            if hit.ordinal >= len(rows):
                raise ValueError
            row = rows[hit.ordinal]
            chunk = hit.original_chunk_bytes if dense else hit.chunk_bytes
            for actual, expected in ((hit.scope_bytes, row.scope_bytes), (chunk, row.chunk_bytes)):
                meter.reserve(len(actual) + len(expected) + 1)
                if actual != expected:
                    raise ValueError


@dataclass(frozen=True, repr=False)
class _Diagnosis:
    invocation_id: str
    dataset_id: str
    split_id: str
    case_id: str
    question_sha256: str
    payload_sha256: str
    authority_sha256: str
    original_authority_sha256: str
    filter_id: str
    pointer_sha256: str
    generation: int
    snapshot_id: str
    catalog_id: str
    query_id: str
    gold_binding_id: str
    ranking_binding_id: str
    dense_trace_id: str
    lexical_trace_id: str
    partition_summary_id: str
    dataset_case_count: int
    dataset_atom_occurrences: int
    chosen_atom_occurrences: int
    eligible_row_count: int
    geometry: object
    source_envelope: tuple
    pre_final_work: int
    pre_final_payload: int
    final_work: int
    final_payload: int
    checkpoint_categories: tuple
    final_categories: tuple
    source_status: str = dc_field(default="OWNED_BINDING_CALLS_ONLY", init=False)
    authorization: str = dc_field(default="SUPPLIED_SCOPE_CHECKS_ONLY", init=False)
    score_order: str = dc_field(default="SUPPLIED_SCORE_ORDER_NOT_REEXECUTED", init=False)
    execution: str = dc_field(default="NOT_ATTESTED", init=False)
    temporal: str = dc_field(default="SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC", init=False)
    gold_eligibility: str = dc_field(default="NOT_CHECKED", init=False)
    held_out: str = dc_field(default="NOT_CHECKED", init=False)
    origin: str = dc_field(default="SUPPLIED_UNVERIFIED", init=False)
    current_rights: str = dc_field(default="NOT_CHECKED", init=False)
    scale: str = dc_field(default="NOT_QUALIFIED", init=False)
    model: str = dc_field(default="NOT_QUALIFIED", init=False)
    quality: str = dc_field(default="NOT_QUALIFIED", init=False)
    visual: str = dc_field(default="NOT_QUALIFIED", init=False)
    license: str = dc_field(default="NOT_CHECKED", init=False)
    independent_audit: str = dc_field(default="NOT_CHECKED", init=False)
    mvp: str = dc_field(default="NOT_QUALIFIED", init=False)
    qualification: str = dc_field(default="NOT_QUALIFIED", init=False)
    accounting: str = dc_field(default="FINAL_TOTALS_NOT_IN_INVOCATION_ID", init=False)


def bind_stages(
    originals,
    derived,
    root,
    pin_owner,
    dataset_bytes,
    case_id,
    gold_bundle_ids,
    hybrid_result,
    query_payload,
    *,
    query_space_id,
    query_definition_fingerprint,
    query_policy_id,
    query_execution_fingerprint,
    grants,
    restrictions=None,
    deadline_ms=120000,
):
    """Bind supplied trace metadata to sequential owned source observations."""
    import time

    try:
        start = time.monotonic()
        return _bind_stages(
            originals,
            derived,
            root,
            pin_owner,
            dataset_bytes,
            case_id,
            gold_bundle_ids,
            hybrid_result,
            query_payload,
            query_space_id,
            query_definition_fingerprint,
            query_policy_id,
            query_execution_fingerprint,
            grants,
            restrictions,
            deadline_ms,
            start,
        )
    except Exception:
        raise StageBindingError("source-bound stage diagnosis refused") from None


def _bind_stages(
    originals,
    derived,
    root,
    owner,
    data,
    case_id,
    gold_ids,
    result,
    payload,
    space,
    definition,
    policy,
    execution,
    grants,
    restrictions,
    deadline_ms,
    start,
):
    from . import declared_stage_geometry, derived_store, raw_snapshot_catalog
    from . import source_bound_ranking, text_evaluation_dataset, text_evaluation_gold_binding
    from .source_admission import OriginalStore

    meter = _Meter()
    clock = _Deadline(start, deadline_ms)
    meter.check = clock.check
    clock.check()
    ids = (space, definition, policy, execution)
    _preflight_inputs(root, data, case_id, gold_ids, payload, ids, deadline_ms, meter)
    if type(originals) is not OriginalStore or type(derived) is not derived_store.Store:
        raise ValueError
    _preflight_result(result, meter)
    meter.reserve(len(data) + 1, len(data))
    clock.check()
    dataset = text_evaluation_dataset.admit(data, deadline_ms=clock.remaining(5000))
    clock.check()
    if (
        type(dataset) is not text_evaluation_dataset.Dataset
        or dataset.case_count > 256
        or dataset.gold_atom_count > 512
        or type(dataset.cases) is not tuple
        or dataset.case_count != len(dataset.cases)
    ):
        raise ValueError
    case = None
    for candidate in dataset.cases:
        meter.reserve(1)
        if type(candidate) is not text_evaluation_dataset.Case:
            raise ValueError
        if meter.compare_strings(candidate.case_id, case_id) == 0:
            if case is not None:
                raise ValueError
            case = candidate
    if case is None:
        raise ValueError
    chosen_occurrences = 0
    for requirement in case.requirements:
        meter.reserve(1)
        for alternative in requirement.alternatives:
            meter.reserve(1)
            chosen_occurrences += len(alternative)
    if chosen_occurrences > dataset.gold_atom_count:
        raise ValueError
    original_grants, effective, restricted = _admit_authority(
        grants, restrictions, case.scope, meter, clock.check
    )
    meter.reserve(8, 8 * 128 + 262144)
    original_authority = [
        original_grants.model_dump(mode="json"),
        None if restricted is None else restricted.model_dump(mode="json"),
    ]
    original_authority_sha = _canonical_hash(
        original_authority, b"", meter, clock.check, ensure_ascii=False, limit=262144
    )
    meter.reserve(4, 4 * 128)
    filter_id = "sha256:" + _canonical_hash(
        {
            "original_authority": original_authority_sha,
            "case_id": case_id,
            "policy": "case-scope-intersection-v1",
        },
        b"slaif-stage-filter-v1\n",
        meter,
        clock.check,
    )
    envelope = _source_envelope()
    captured = _pin_check(owner, originals, derived, root, None, meter, clock)
    meter.reserve(1)
    clock.check()
    catalog = raw_snapshot_catalog.load_catalog(
        originals, derived, root, captured.pointer.snapshot_id, deadline_ms=clock.remaining(120000)
    )
    clock.check()
    _pin_check(owner, originals, derived, root, captured, meter, clock)
    _catalog_identity(catalog, meter, clock.check)
    eligible = _catalog_eligible(catalog, captured, effective, restricted, meter, clock.check)
    text_sha, payload_sha, authority_sha, query_id, analyzer = _query_identity(
        catalog, case.question, payload, ids, effective, restricted, result, meter, clock.check
    )
    matching = _matching_universe(
        case.question, analyzer, catalog.rows, eligible, meter, clock.check
    )
    _validate_modality_headers(
        result,
        catalog.snapshot_id,
        catalog.catalog_id,
        text_sha,
        payload_sha,
        authority_sha,
        ids,
        analyzer,
        catalog.rows,
        meter,
        clock.check,
    )
    _validate_trace_relations(result.dense, eligible, matching, meter, dense=True)
    _validate_trace_relations(result.lexical, eligible, matching, meter, dense=False)
    fusion_union = _validate_fusion(
        result, catalog.rows, catalog.snapshot_id, catalog.catalog_id, query_id, meter
    )
    meter.reserve(1)
    clock.check()
    gold = text_evaluation_gold_binding.bind(
        originals, derived, data, gold_ids, deadline_ms=clock.remaining(30000)
    )
    clock.check()
    _pin_check(owner, originals, derived, root, captured, meter, clock)
    _validate_gold(gold, dataset, data, gold_ids, meter, clock.check)
    meter.reserve(len(eligible), 128 * len(eligible))
    chunk_ids = []
    for row in eligible:
        meter.reserve(1)
        chunk_ids.append(row.chunk_id)
    meter.reserve(1)
    clock.check()
    binding = source_bound_ranking.bind(
        originals,
        derived,
        root,
        catalog.snapshot_id,
        catalog.catalog_id,
        tuple(chunk_ids),
        grants=effective,
        restrictions=restricted,
        deadline_ms=clock.remaining(30000),
    )
    clock.check()
    _pin_check(owner, originals, derived, root, captured, meter, clock)
    rows, stages, pure_work, pure_budget = _geometry_inputs(
        binding,
        eligible,
        catalog.rows,
        result,
        fusion_union,
        dataset,
        data,
        catalog.snapshot_id,
        catalog.catalog_id,
        authority_sha,
        meter,
        clock.check,
    )
    meter.reserve(1 + pure_work, pure_budget, category="pure_delegate")
    clock.check()
    geometry = declared_stage_geometry.diagnose(
        data, case_id, rows, stages, deadline_ms=clock.remaining(10000)
    )
    clock.check()
    if (
        type(geometry) is not declared_stage_geometry.Diagnosis
        or geometry.work != pure_work
        or geometry.serialization_budget != pure_budget
        or geometry.source_binding != "UNVERIFIED"
        or geometry.qualification != "NOT_QUALIFIED"
    ):
        raise ValueError
    _pin_check(owner, originals, derived, root, captured, meter, clock)
    import hashlib

    pointer_bytes = captured.pointer.pointer_bytes
    meter.reserve(len(pointer_bytes) + 66, 192)
    clock.check()
    pointer_sha = hashlib.sha256(pointer_bytes).hexdigest()
    clock.check()
    partition_count = len(result.dense.allowed_partition_counts) + len(result.lexical.partitions)
    meter.reserve(partition_count, 128 * partition_count)
    partition_summary = []
    for modality, counts in (("dense", result.dense.allowed_partition_counts),
                             ("lexical", result.lexical.partitions)):
        for count in counts:
            meter.reserve(6, 6 * 128)
            partition_summary.append((modality, count.partition_id, count.eligible,
                                      count.selected, count.returned,
                                      None if modality == "dense" else count.matching))
    partition_summary_id = "sha256:" + _canonical_hash(
        partition_summary, b"slaif-stage-partition-summary-v1\n", meter, clock.check)
    meter.reserve(8, 8 * 128)
    checkpoint_work, checkpoint_payload = meter.work, meter.payload
    checkpoint_categories = tuple(
        (name, values[0], values[1]) for name, values in meter.categories.items()
    )
    meter.reserve(32, 32 * 128)
    identity = {
        "policy": "source-bound-raw-stage-loss-v1",
        "dataset": dataset.dataset_id,
        "split": dataset.split_id,
        "case": case_id,
        "question": text_sha,
        "payload": payload_sha,
        "authority": authority_sha,
        "original_authority": original_authority_sha,
        "filter_id": filter_id,
        "pointer_sha256": pointer_sha,
        "generation": captured.pointer.generation,
        "snapshot": catalog.snapshot_id,
        "catalog": catalog.catalog_id,
        "query": query_id,
        "gold": gold.binding_id,
        "ranking": binding.binding_id,
        "geometry": geometry.invocation_id,
        "dense_trace": result.dense.trace.trace_id,
        "lexical_trace": result.lexical.trace.trace_id,
        "partition_summary": partition_summary_id,
        "dataset_cases": dataset.case_count,
        "dataset_atoms": dataset.gold_atom_count,
        "chosen_atoms": chosen_occurrences,
        "eligible_rows": len(eligible),
        "statuses": ("OWNED_BINDING_CALLS_ONLY", "SUPPLIED_SCOPE_CHECKS_ONLY",
                     "SUPPLIED_SCORE_ORDER_NOT_REEXECUTED", "NOT_ATTESTED",
                     "SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC", "NOT_QUALIFIED"),
        "checkpoint": "PRE_FINAL_IDENTITY_CHECKPOINT",
        "work": checkpoint_work,
        "payload_charge": checkpoint_payload,
        "categories": checkpoint_categories,
        "source_envelope": envelope,
    }
    invocation = "sha256:" + _canonical_hash(
        identity, b"slaif-source-bound-stage-loss-v1\n", meter, clock.check
    )
    meter.reserve(64, 64 * 128)
    final_categories = tuple(
        (name, values[0], values[1]) for name, values in meter.categories.items()
    )
    clock.check()
    output = _Diagnosis(
        invocation,
        dataset.dataset_id,
        dataset.split_id,
        case_id,
        text_sha,
        payload_sha,
        authority_sha,
        original_authority_sha,
        filter_id,
        pointer_sha,
        captured.pointer.generation,
        catalog.snapshot_id,
        catalog.catalog_id,
        query_id,
        gold.binding_id,
        binding.binding_id,
        result.dense.trace.trace_id,
        result.lexical.trace.trace_id,
        partition_summary_id,
        dataset.case_count,
        dataset.gold_atom_count,
        chosen_occurrences,
        len(eligible),
        geometry,
        envelope,
        checkpoint_work,
        checkpoint_payload,
        meter.work,
        meter.payload,
        checkpoint_categories,
        final_categories,
    )
    clock.check()
    return output
