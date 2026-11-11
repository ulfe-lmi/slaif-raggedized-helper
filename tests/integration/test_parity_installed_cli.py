import hashlib
import json
import os
import resource
import shutil
import signal
import subprocess
import sys

import pytest


D = "a" * 64


def fixture(kind):
    if kind == "embedding":
        definition = {
            "model_name": "ž😀", "checkpoint_revision": "r", "checkpoint_sha256": D,
            "tokenizer_revision": "t", "pooling": "cls", "normalize": True, "dimensions": 2,
        }
        row = {"id": "p", "input_digest": D, "representation_digest": D, "vector": [1, 0]}
        return {
            "version": 1,
            "reference": {"definition": definition, "device": "cpu", "dtype": "fp32"},
            "candidate": {"definition": definition, "device": "gpu", "dtype": "fp16"},
            "queries": [dict(row, id="q")], "reference_corpus": [row],
            "candidate_corpus": [row], "k": 1, "cosine_tolerance": 0, "score_tolerance": 0,
        }
    side = {
        "definition": {"model": "ž😀", "checkpoint": "c", "tokenizer": "t", "pair_budget": 2},
        "execution": {"device": "cpu", "precision": "fp32", "provenance": "SUPPLIED_UNVERIFIED"},
        "pairs": [{"pair_id": "p", "query_id": "q", "passage_id": "p",
                   "query_digest": D, "passage_digest": D, "score": 1}],
    }
    return {"version": 1, "reference": side, "candidate": side,
            "criteria": {"top_k": 1, "max_absolute_delta": 0, "min_top_k_overlap": 1}}


def invoke(*args, preexec_fn=None):
    executable = shutil.which("raggedized")
    assert executable is not None
    return subprocess.run([executable, *map(str, args)], capture_output=True,
                          timeout=10, preexec_fn=preexec_fn)


@pytest.mark.parametrize("kind", ["embedding", "rerank"])
def test_installed_parity_success_and_refusal(tmp_path, kind):
    data = fixture(kind)
    raw = json.dumps(data, ensure_ascii=False, indent=1).encode()
    source, output = tmp_path / "private-canary", tmp_path / "out"
    source.write_bytes(raw)
    result = invoke("parity", kind, "--input", source, "--output", output)
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert json.loads(output.read_bytes()) == doc
    assert doc["input_sha256"] == hashlib.sha256(raw).hexdigest()
    assert doc["input_bytes"] == len(raw) and doc["real_qualification"] == "NOT_RUN"
    analysis = doc["analysis"]
    assert analysis["evidence" if kind == "embedding" else "provenance"] == "SUPPLIED_UNVERIFIED"
    assert analysis["input_fingerprint" if kind == "embedding" else "input_binding"]
    if kind == "embedding":
        assert analysis["paired_vectors"][0]["cosine"] == 1.0
    else:
        assert analysis["pairs"][0]["absolute_delta"] == 0.0
    for extra in ("--allow-supplied-input", "--PRIVATE_CANARY"):
        bad = invoke("parity", kind, "--input", source, "--output", output, extra)
        assert bad.returncode == 2 and b"PRIVATE_CANARY" not in bad.stderr
    for incomplete in (("--input", source), ("--output", output)):
        bad = invoke("parity", kind, *incomplete)
        assert bad.returncode == 2 and b"private-canary" not in bad.stderr
    bad = invoke("parity", kind, "--input", tmp_path / "missing-input", "--output", output)
    assert bad.returncode == 2 and str(tmp_path).encode() not in bad.stderr
    bad = invoke("parity", kind, "--input", source, "--output", tmp_path / "missing" / "out")
    assert bad.returncode == 2 and str(tmp_path).encode() not in bad.stderr
    source.write_bytes(b'{"version":true}')
    bad = invoke("parity", kind, "--input", source, "--output", output)
    assert bad.returncode == 2 and b"private-canary" not in bad.stderr


@pytest.mark.parametrize("kind", ["embedding", "rerank"])
def test_post_work_export_failure_retains_evidence(tmp_path, kind):
    source, output = tmp_path / "input", tmp_path / "output"
    raw = json.dumps(fixture(kind)).encode()
    source.write_bytes(raw)

    def limit():
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))

    result = invoke("parity", kind, "--input", source, "--output", output, preexec_fn=limit)
    assert result.returncode == 3
    evidence = json.loads(result.stdout)["evidence"]
    assert evidence["input_sha256"] == hashlib.sha256(raw).hexdigest()
    assert evidence["input_bytes"] == len(raw) and evidence["real_qualification"] == "NOT_RUN"
    assert evidence["analysis"]["evidence" if kind == "embedding" else "provenance"] == \
        "SUPPLIED_UNVERIFIED"


def test_help_and_import_have_no_network_model_or_telemetry():
    for args in (("--help",), ("parity", "--help"), ("parity", "embedding", "--help"),
                 ("probe", "--help"), ("qualification", "--help"), ("resource", "--help")):
        assert invoke(*args).returncode == 0
    code = '''
import builtins, resource, socket, subprocess, sys
original = builtins.__import__
def guard(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'sentence_transformers'):
        raise AssertionError('model import')
    return original(name, *args, **kwargs)
def forbidden(*args, **kwargs):
    raise AssertionError('unexpected work')
builtins.__import__ = guard
socket.socket.connect = forbidden
socket.create_connection = forbidden
subprocess.Popen = forbidden
resource.getrusage = forbidden
from slaif_raggedized_helper import cli
try:
    cli.main(['parity', '--help'])
except SystemExit as exc:
    assert exc.code == 0
else:
    raise AssertionError('help did not exit')
'''
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=10,
                            env=os.environ.copy())
    assert result.returncode == 0, result.stderr
