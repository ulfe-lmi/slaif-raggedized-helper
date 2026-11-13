"""SYNTHETIC geometry only; no source quality or authorization evidence."""

import dataclasses
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from slaif_raggedized_helper import declared_span_support as subject

ORACLE = json.loads(
    (Path(__file__).parents[2] / "docs/parallel/declared-span-support-oracle.json").read_text()
)
DATA = ORACLE["dataset_ascii"].encode("ascii")


def tuples(value):
    return tuple(tuples(x) for x in value) if isinstance(value, list) else value


class SupportTests(unittest.TestCase):
    def score(self, ranking=(), **kw):
        return subject.score_case(DATA, "case1", ranking, **kw)

    def test_fixed_oracle(self):
        self.assertEqual(len(ORACLE["vectors"]), 15)
        for vector in ORACLE["vectors"]:
            with self.subTest(vector=vector["name"]):
                result = subject.score_case(
                    DATA,
                    vector["case_id"],
                    tuples(vector["ranking"]),
                    cutoffs=tuple(vector["cutoffs"]),
                )
                self.assertEqual(
                    (result.dataset_id, result.split_id, result.case_id),
                    (ORACLE["dataset_id"], ORACLE["split_id"], vector["case_id"]),
                )
                self.assertEqual(result.input_fingerprint, vector["input_fingerprint"])
                self.assertEqual(
                    "sha256:"
                    + hashlib.sha256(
                        b"slaif-declared-span-support-v1\n"
                        + vector["input_canonical_ascii"].encode("ascii")
                    ).hexdigest(),
                    vector["input_fingerprint"],
                )
                self.assertEqual(
                    [dataclasses.asdict(x) for x in result.at_k],
                    [tuples_dict(x) for x in vector["expected_at_k"]],
                )
                self.assertEqual(
                    (
                        result.input_origin,
                        result.source_binding,
                        result.qualification,
                        result.formula_version,
                    ),
                    tuple(
                        ORACLE["markers"][x]
                        for x in (
                            "input_origin",
                            "source_binding",
                            "qualification",
                            "formula_version",
                        )
                    ),
                )
                self.assertEqual(result.ranking_count, len(vector["ranking"]))
                self.assertEqual(
                    result.requirement_count, len(vector["expected_at_k"][0]["requirements"])
                )

    def test_invalid_inputs_and_privacy(self):
        row = tuples(ORACLE["vectors"][0]["ranking"])[0]
        self.score((row,))
        bad = [
            None,
            [],
            iter(()),
            (row, row),
            ((True, *row[1:]),),
            ((row[0] + "x", *row[1:]),),
            ((row[0], row[1], row[2], (("\ud800", 0, 1),)),),
            ((row[0], row[1], row[2], (("A", True, 1),)),),
            ((row[0], row[1], row[2], (("A", 1, 1),)),),
        ]
        for value in bad:
            with self.subTest(value=type(value)):
                with self.assertRaisesRegex(
                    subject.SpanSupportError, "^declared span support refused$"
                ):
                    self.score(value)
        for cutoffs in ((True,), (2, 1), (1, 1), [], (0,)):
            with self.assertRaises(subject.SpanSupportError):
                self.score(cutoffs=cutoffs)
        for case in ("", "a" * 129, "é", "missing"):
            with self.assertRaises(subject.SpanSupportError):
                subject.score_case(DATA, case, ())
        with self.assertRaises(subject.SpanSupportError):
            subject.score_case(b"foreign", "case1", ())
        result = self.score()
        self.assertNotIn("case1", repr(result))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.case_id = "x"

    def test_limits_and_parser_floor(self):
        base = tuples(ORACLE["vectors"][0]["ranking"])[0]

        def rows(n, fragments):
            return tuple(
                ("sha256:" + format(i, "064x"), base[1], base[2], fragments) for i in range(n)
            )

        self.assertEqual(self.score(rows(1, (("😀" * 256, 0, 1),)), cutoffs=(1,)).ranking_count, 1)
        with self.assertRaises(subject.SpanSupportError):
            self.score(rows(1, (("x" * 257, 0, 1),)), cutoffs=(1,))
        self.assertEqual(
            self.score(
                rows(256, (("x", 0, 1),) * 256), cutoffs=(1,), deadline_ms=30000
            ).ranking_count,
            256,
        )
        with self.assertRaises(subject.SpanSupportError):
            self.score(rows(257, (("x", 0, 1),) * 256), cutoffs=(1,), deadline_ms=30000)
        # Valid F but work budget exceeds the cap even with one cutoff.
        with self.assertRaises(subject.SpanSupportError):
            self.score(rows(33, (("😀" * 256, 0, 1),) * 256), cutoffs=(1,), deadline_ms=30000)
        # Exceeds Uin and work caps; not an isolated causal Uin witness.
        with self.assertRaises(subject.SpanSupportError):
            self.score(rows(65, (("😀" * 256, 0, 1),) * 256), cutoffs=(1,), deadline_ms=30000)
        clock = [10.0]
        real = subject.text_evaluation_dataset.admit

        def admitted(data, *, deadline_ms):
            self.assertEqual(deadline_ms, 1500)
            return real(data, deadline_ms=deadline_ms)

        with (
            patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(subject.text_evaluation_dataset, "admit", side_effect=admitted),
        ):
            self.score(deadline_ms=1500)
        with patch.object(subject.time, "monotonic", side_effect=[0, 1]):
            with self.assertRaises(subject.SpanSupportError):
                self.score(deadline_ms=1)

    def test_hash_deadline_and_all_ranks(self):
        ranking = tuples(ORACLE["vectors"][0]["ranking"])
        first = self.score(ranking, cutoffs=(1,))
        altered = list(ranking)
        row = altered[-1]
        altered[-1] = (row[0], row[1], row[2], (("A", 7, 8),))
        second = self.score(tuple(altered), cutoffs=(1,))
        self.assertEqual(first.at_k, second.at_k)
        self.assertNotEqual(first.input_fingerprint, second.input_fingerprint)
        clock = [0]
        actual = subject.hashlib.sha256

        def hash_then_expire(*args):
            digest = actual(*args)

            class Wrapper:
                def update(self, chunk):
                    digest.update(chunk)
                    clock[0] = 10

                def hexdigest(self):
                    return digest.hexdigest()

            return Wrapper()

        # Patch only after parser admission, otherwise its own hash uses this wrapper.
        original = subject.text_evaluation_dataset.admit

        def admit_then_patch(*args, **kwargs):
            result = original(*args, **kwargs)
            patcher = patch.object(subject.hashlib, "sha256", side_effect=hash_then_expire)
            patcher.start()
            self.addCleanup(patcher.stop)
            return result

        with (
            patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(subject.text_evaluation_dataset, "admit", side_effect=admit_then_patch),
        ):
            with self.assertRaises(subject.SpanSupportError):
                self.score(deadline_ms=1000)

    def test_exact_types_and_case_id_boundary(self):
        class TupleSubclass(tuple):
            pass

        class IntSubclass(int):
            pass

        class StringSubclass(str):
            pass

        row = tuples(ORACLE["vectors"][0]["ranking"])[0]
        self.score((row,), cutoffs=(1,))
        for ranking in (
            TupleSubclass((row,)),
            (TupleSubclass(row),),
            ((StringSubclass(row[0]), *row[1:]),),
            ((row[0], row[1], row[2], (("A", IntSubclass(0), 1),)),),
        ):
            with self.assertRaises(subject.SpanSupportError):
                self.score(ranking)
        obj = json.loads(DATA)
        case = obj["cases"][0]
        case["case_id"] = "a" * 128
        obj["cases"].sort(key=lambda item: item["case_id"])
        data = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
        self.assertEqual(subject.score_case(data, "a" * 128, ()).case_id, "a" * 128)
        with self.assertRaises(subject.SpanSupportError):
            subject.score_case(data, "a" * 129, ())

    def test_serialized_guard_private_fixture(self):
        # Guard-only fixture: no assertion that admitted data can reach this ceiling.
        self.score()

        class Oversized(str):
            def __len__(self):
                return 67108865

        class Encoder:
            def iterencode(self, obj):
                yield Oversized("x")

        original = subject.text_evaluation_dataset.admit

        def admit_then_patch(*args, **kwargs):
            result = original(*args, **kwargs)
            patcher = patch.object(subject.json, "JSONEncoder", return_value=Encoder())
            patcher.start()
            self.addCleanup(patcher.stop)
            return result

        with patch.object(subject.text_evaluation_dataset, "admit", side_effect=admit_then_patch):
            with self.assertRaises(subject.SpanSupportError):
                self.score()

    def test_grade_identity(self):
        obj = json.loads(DATA)
        obj["cases"][0]["requirements"][0]["grade"] = 2
        changed = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
        ranking = tuples(ORACLE["vectors"][0]["ranking"])
        a = self.score(ranking)
        b = subject.score_case(changed, "case1", ranking)
        self.assertNotEqual(a.dataset_id, b.dataset_id)
        self.assertNotEqual(a.input_fingerprint, b.input_fingerprint)
        self.assertEqual(a.at_k, b.at_k)

    def test_bisect_late_interval(self):
        # SYNTHETIC high-offset gold, with a late containing interval and a gap control.
        obj = json.loads(DATA)
        atom = obj["cases"][0]["requirements"][0]["alternatives"][0][0]
        atom["start"], atom["end"] = 1000, 1004
        data = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
        base = tuples(ORACLE["vectors"][0]["ranking"])[0]
        fragments = tuple(("A", i, i + 1) for i in range(10, 200, 2)) + (("A", 1000, 1004),)
        calls = []
        real_bisect = subject.bisect_right

        def record(starts, start):
            result = real_bisect(starts, start)
            calls.append((starts, start, result))
            return result

        def run(items):
            row = (base[0], base[1], base[2], items)
            return subject.score_case(data, "case1", (row,), cutoffs=(1,))

        with patch.object(subject, "bisect_right", side_effect=record):
            result = run(fragments)
        self.assertTrue(result.at_k[0].requirements[0].alternative_covered[0])
        starts, start, index = next(c for c in calls if c[1] == 1000)
        self.assertGreater(len(starts), 90)
        self.assertEqual(index - 1, len(starts) - 1)
        self.assertEqual(starts[index - 1], start)
        gap = fragments[:-1] + (("A", 1000, 1002), ("A", 1003, 1004))
        self.assertFalse(run(gap).at_k[0].requirements[0].alternative_covered[0])

    def test_propagation_and_deadline(self):
        sentinel = KeyboardInterrupt()
        with patch.object(subject.text_evaluation_dataset, "admit", side_effect=sentinel):
            with self.assertRaises(KeyboardInterrupt) as cm:
                self.score()
        self.assertIs(cm.exception, sentinel)
        real = subject.CaseCoverage

        def late(*a, **kw):
            result = real(*a, **kw)
            clock[0] = 10
            return result

        clock = [0]
        with (
            patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(subject, "CaseCoverage", side_effect=late),
        ):
            with self.assertRaises(subject.SpanSupportError):
                self.score(deadline_ms=1000)


def tuples_dict(value):
    if isinstance(value, dict):
        return {k: tuples_dict(v) for k, v in value.items()}
    if isinstance(value, list):
        return tuple(tuples_dict(v) for v in value)
    return value


if __name__ == "__main__":
    unittest.main()
