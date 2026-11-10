import hashlib
import json
import resource
import signal
import subprocess
import sys

import pytest

MODULE = "slaif_raggedized_helper.qualification.parity_cli"
D = "a" * 64


def fixture(kind):
    if kind == "embedding":
        definition = {
            "model_name": "ž",
            "checkpoint_revision": "r",
            "checkpoint_sha256": D,
            "tokenizer_revision": "t",
            "pooling": "cls",
            "normalize": True,
            "dimensions": 2,
        }
        row = {"id": "p", "input_digest": D, "representation_digest": D, "vector": [1, 0]}
        return {
            "version": 1,
            "reference": {"definition": definition, "device": "cpu", "dtype": "fp32"},
            "candidate": {"definition": definition, "device": "gpu", "dtype": "fp16"},
            "queries": [dict(row, id="q")],
            "reference_corpus": [row],
            "candidate_corpus": [row],
            "k": 1,
            "cosine_tolerance": 0,
            "score_tolerance": 0,
        }
    side = {
        "definition": {"model": "ž", "checkpoint": "c", "tokenizer": "t", "pair_budget": 2},
        "execution": {"device": "cpu", "precision": "fp32", "provenance": "SUPPLIED_UNVERIFIED"},
        "pairs": [
            {
                "pair_id": "p",
                "query_id": "q",
                "passage_id": "p",
                "query_digest": D,
                "passage_digest": D,
                "score": 1,
            }
        ],
    }
    return {
        "version": 1,
        "reference": side,
        "candidate": side,
        "criteria": {"top_k": 1, "max_absolute_delta": 0, "min_top_k_overlap": 1},
    }


def invoke(kind, source, target, *extra, preexec_fn=None):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            MODULE,
            kind,
            "--input",
            str(source),
            "--output",
            str(target),
            *extra,
        ],
        capture_output=True,
        preexec_fn=preexec_fn,
    )


@pytest.mark.parametrize("kind", ["embedding", "rerank"])
def test_success_binding_and_opt_in(tmp_path, kind):
    source, target = tmp_path / "in", tmp_path / "out"
    raw = json.dumps(fixture(kind), ensure_ascii=False).encode()
    source.write_bytes(raw)
    result = invoke(kind, source, target)
    assert result.returncode == 0, result.stderr
    evidence = json.loads(result.stdout)
    assert evidence == json.loads(target.read_bytes())
    assert evidence["input_sha256"] == hashlib.sha256(raw).hexdigest()
    assert evidence["input_bytes"] == len(raw)
    assert evidence["real_qualification"] == "NOT_RUN"
    from slaif_raggedized_helper.qualification import embedding_parity, rerank_parity

    analyzer = (
        embedding_parity.analyze if kind == "embedding" else rerank_parity.analyze_rerank_parity
    )
    assert evidence["analysis"] == analyzer(json.loads(raw))
    assert (
        evidence["analysis"]["evidence" if kind == "embedding" else "provenance"]
        == "SUPPLIED_UNVERIFIED"
    )
    assert evidence["analysis"]["input_fingerprint" if kind == "embedding" else "input_binding"]


@pytest.mark.parametrize(
    "raw",
    [
        b'{"version":true}',
        b'{"version":NaN}',
        b'{"x":1,"x":2}',
        b'{"unknown":1}',
        b"{bad",
        b" " * (16 * 1024 * 1024 + 1),
    ],
    ids=["bool", "nonfinite", "duplicate", "unknown", "malformed", "oversize"],
)
def test_refusals(tmp_path, raw):
    source = tmp_path / "private-canary"
    source.write_bytes(raw)
    result = invoke("rerank", source, tmp_path / "out")
    assert result.returncode == 2 and b"private-canary" not in result.stderr
    assert not (tmp_path / "out").exists()


def test_invalid_destination_and_late_failure(tmp_path):
    source = tmp_path / "input"
    source.write_text(json.dumps(fixture("rerank")))
    assert invoke("rerank", source, tmp_path / "missing" / "out").returncode == 2

    def limit():
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))

    result = invoke("rerank", source, tmp_path / "out", preexec_fn=limit)
    assert result.returncode == 3
    evidence = json.loads(result.stdout)["evidence"]
    assert evidence["analysis"]["pair_count"] == 1
    assert evidence["input_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


def test_help_and_import():
    for command in (
        [sys.executable, "-m", MODULE, "--help"],
        [sys.executable, "-c", f"import {MODULE}"],
    ):
        assert subprocess.run(command, capture_output=True).returncode == 0


@pytest.mark.parametrize("kind", ["embedding", "rerank"])
def test_promotion_refused(tmp_path, kind):
    data = fixture(kind)
    data["evidence"] = "EXECUTED"
    source = tmp_path / "in"
    source.write_text(json.dumps(data))
    result = invoke(kind, source, tmp_path / "out")
    assert result.returncode == 2
    assert not (tmp_path / "out").exists()


def test_import_and_help_do_not_call_network_or_telemetry():
    code = """
import resource, socket, subprocess, sys

def forbidden(*args, **kwargs):
    raise AssertionError("unexpected I/O")
socket.socket.connect = forbidden
socket.create_connection = forbidden
subprocess.Popen = forbidden
resource.getrusage = forbidden
import slaif_raggedized_helper.qualification.parity_cli as cli
try:
    cli.main(["--help"])
except SystemExit as exc:
    assert exc.code == 0
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True)
    assert result.returncode == 0, result.stderr


def test_required_paths_and_removed_flag_are_refused(tmp_path):
    source = tmp_path / "in"
    source.write_text(json.dumps(fixture("rerank")))
    for args in (
        ["rerank", "--input", str(source)],
        ["rerank", "--output", str(tmp_path / "out")],
        [
            "rerank",
            "--input",
            str(source),
            "--output",
            str(tmp_path / "out"),
            "--allow-supplied-input",
        ],
    ):
        result = subprocess.run([sys.executable, "-m", MODULE, *args], capture_output=True)
        assert result.returncode == 2
        assert result.stderr == b'{"error":"input or configuration refused"}\n'
        assert not (tmp_path / "out").exists()
