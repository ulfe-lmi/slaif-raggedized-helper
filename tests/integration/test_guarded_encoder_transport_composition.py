"""Actual guarded encoder transport composition (PAR-009, hosted gate).

Both children are real: the native tokenizer child runs the real
``embedding_tokenizer_worker`` protocol under the configured trusted
backend, and the CPU sandbox child runs the genuine
``cpu_embedding_worker_main`` entry, which independently re-verifies the
host-declared code handshake.  The model framework is the trusted
synthetic delegate reused from
``test_cpu_embedding_worker_composition`` (never real neural loading).
The synthetic policy wire, the payload installation and the attributed
atomic selection publication reuse the already reviewed fixture pattern
(009-z current-view lane fixture re-derived in
``tests/unit/test_private_policy_request.py`` and used by
``tests/integration/test_private_pinned_hybrid_composition.py``).

Hosted-environment fixture modules are imported inside test setup so
local collect-only remains available.  Local proof of these five
witnesses is collection only; the five real outcomes require the later
separate configured hosted gate.
"""
import hashlib
import json
import os
import struct
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests/unit")]

import pytest  # noqa: E402

from slaif_raggedized_helper import (  # noqa: E402
    cpu_embedding_worker as cpu,
    cpu_execution_contract,
    embedding_artifacts,
    native_tokenizers,
    private_policy_capture as capture,
    private_policy_payload as payload_install,
    private_policy_request as ppr,
    query_embedding as q,
)
from slaif_raggedized_helper.schema import fingerprint  # noqa: E402

# Attributed test-local wire emitter: an independent re-derivation of the
# typed component grammar (009-z current-view lane fixture,
# tests/unit/test_private_policy_request.py; used by
# tests/integration/test_private_pinned_hybrid_composition.py).
_MAGIC = b"slaif-supplied-policy-view-v1\n"
_SELECTION = "current-policy.json"
CREDENTIAL = b"synthetic-credential-" + b"a" * 22  # exactly 43 synthetic bytes
PRINCIPAL_ID = "alpha-1"
VERIFIER = hashlib.sha256(CREDENTIAL).digest()
OPERATIONS = ("search", "sources:read")
CORPORA = ("one", "two")
VERSIONS = ("v1",)
LABELS = ("secret",)
PRINCIPAL = (PRINCIPAL_ID, VERIFIER, OPERATIONS, CORPORA, VERSIONS, LABELS)
_DOCUMENTS = (
    (
        "doc-one",
        (
            (
                "sha256:" + hashlib.sha256(b"revision-one").hexdigest(),
                hashlib.sha256(b"scope-one").hexdigest(),
            ),
        ),
    ),
)
# Test-side reconstruction data (clearly labeled): exact historical
# SHA-256 digests of the eight worker code files and the four bridge
# files at the accepted base
# 00743eca3c351d57e45ec81004f52e519ebec00a.  This is reconstruction from
# the frozen code preimages, not a runtime observation.
_HISTORICAL_CODE_SHA256 = {
    "cpu_embedding_worker.py":
        "6c9703ca5eea837b588b55c63dde88a6ac5e35c4db3ea192f61e27c27b1127ae",
    "cpu_embedding_worker_main.py":
        "df25d670940a0a0d7dbeca5d3d4c42992feb1a801188494f69ef7f7a9236be26",
    "cpu_embedding_backend.py":
        "0e94b61abbc05556fbb60196080b17593e386b17d69cfbfc2da220d84fb03bf1",
    "embedding_artifacts.py":
        "f9f52ece4cea2f686d1765b3538ff1e1d52ac79bc55ab62c2f41f73ea0cb2892",
    "embedding_space.py":
        "2cf63b8dcc5bc081fee174582159c362e6d7f351ba0e0ac74885aee9654a1e2e",
    "native_tokenizers.py":
        "a17e7c7a18b33694a495f18c37dc51b50b2050837e01a16c47aa17e4d6e34ae2",
    "schema.py": "9fecd1043f6f62b263a78d5ff0726ce0dcb379ffcdaefa225b3c77dfaee736d2",
    "_constraints.py": "408286611df60ba2a6747a6375ca05931b7199eb78e86b4bfc143b34929df376",
}
_HISTORICAL_BRIDGE_SHA256 = {
    "isolated_cpu_embedding.py":
        "bae33448cf4d629b6b351031618bb959d0e2baf2b5a5a11977499ad21b1edbc8",
    "cpu_execution_contract.py":
        "e2e01b1c189036ad7eee036e90625b4aa14c4a33bfdb52d97c8c7d4cd4744c7f",
    "embedding_tokenizer.py":
        "1c1d0a3ebf6bb3d587cd89aa3dc2270ea6ec745823c990964f715ce8a5bf5094",
    "embedding_vectors.py":
        "c69906f3cb4a1239241990d31eb2688fb14712525c5046e93ff07331724b3a67",
}


def _u32(value):
    return value.to_bytes(4, "big")


def _s(text):
    raw = text.encode("utf-8")
    return _u32(len(raw)) + raw


def _encode_principal(principal_id, verifier, operations, corpora, versions, labels):
    parts = [_s(principal_id), _u32(32) + verifier, _u32(len(operations))]
    for operation in operations:
        parts.append(_s(operation))
    parts.append(_u32(1))
    for values in (corpora, versions, labels):
        parts.append(_u32(len(values)))
        for value in values:
            parts.append(_s(value))
    return b"".join(parts)


def _encode_policy(principals, documents):
    parts = [_MAGIC, _u32(1), _u32(len(principals))]
    for principal in principals:
        parts.append(_encode_principal(*principal))
    parts.append(_u32(len(documents)))
    for document_id, pairs in documents:
        parts.append(_s(document_id))
        parts.append(_u32(len(pairs)))
        for revision_id, scope_digest in pairs:
            parts.append(_s(revision_id))
            parts.append(_s(scope_digest))
    return b"".join(parts)


def _render_selection(generation, wire_bytes, wire_sha256):
    return json.dumps(
        {
            "generation": generation,
            "kind": "slaif-current-policy-selection-v1",
            "schema": 1,
            "wire_bytes": wire_bytes,
            "wire_sha256": wire_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _publish_selection(root, generation, payload):
    # Trusted-writer fixture role: one atomic selected-record publication.
    root = Path(root)
    repl = root.parent / ("swap-" + str(generation) + ".json")
    fd = os.open(str(repl), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(
            fd,
            _render_selection(
                generation, len(payload), hashlib.sha256(payload).hexdigest()
            ),
        )
    finally:
        os.close(fd)
    os.chmod(str(repl), 0o400)
    os.replace(str(repl), str(root / _SELECTION))


def _install_policy(tmp_base, name, documents):
    payload = _encode_policy([PRINCIPAL], documents)
    policy_root = Path(tmp_base) / name
    policy_root.mkdir(mode=0o700)
    os.chmod(str(policy_root), 0o700)
    receipt = payload_install.install_policy_payload(
        payload, directory=str(policy_root), deadline_ms=30000
    )
    assert receipt.outcome is payload_install.PayloadInstallOutcome.INSTALLED
    _publish_selection(policy_root, 1, payload)
    return policy_root, payload


def _frame_len(text):
    # Independent re-derivation of the exact tokenizer wire framing:
    # compact separators, ASCII, 32 hex nonce characters and one LF.  For
    # "hello" this named framing is exactly 60 bytes.  The session books
    # this length before the write, but a booked counter does not prove
    # kernel bytes were sent.
    return len(
        json.dumps(
            {"text": text, "nonce": "0" * 32}, ensure_ascii=True,
            separators=(",", ":"),
        ).encode()
    ) + 1


def _forward_frame_len(rows):
    # Independent re-derivation of the exact CPU forward wire framing:
    # sorted compact JSON (the worker's _json) plus one LF; the nonce is a
    # fixed 32 hex characters, so only its content varies.
    batch = [list(row) for row in rows]
    digest = hashlib.sha256(cpu._json(batch)).hexdigest()
    return len(
        json.dumps(
            {"digest": digest, "nonce": "0" * 32, "rows": batch},
            sort_keys=True, separators=(",", ":"),
        ).encode()
    ) + 1


def _hosted_fixtures():
    # Hosted-environment fixture modules: imported inside test setup so
    # local collect-only remains available.
    from test_cpu_embedding_backend import make_tree
    from test_cpu_embedding_worker_composition import FAKE
    from test_native_tokenizers import make_native

    return make_tree, FAKE, make_native


def _expected_tuple(session):
    return (
        session.space.space_id,
        session.definition.fingerprint(),
        q._POLICY_DIGEST,
        session.execution_fingerprint[7:],
    )


def _scenario(tmp_path, monkeypatch, real_argv):
    make_tree, fake, make_native = _hosted_fixtures()
    paths, runtime, _ = make_native(tmp_path)
    root = tmp_path / "tree"
    manifest, raw, inv, definition, token = make_tree(root)
    data = paths[0].read_bytes()
    (root / "tokenizer.json").write_bytes(data)
    entry = next(x for x in manifest["files"] if x["role"] == "tokenizer")
    entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    raw = json.dumps(manifest).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    token = replace(token, sha256=entry["sha256"])
    script = tmp_path / "fake.py"
    script.write_text(fake)
    # The real argv builder is captured once per test (passed in) so
    # repeated scenarios in one test never nest interceptors.
    def intercept(*args):
        argv = real_argv(*args)
        argv[argv.index("/worker.py") - 1] = str(script)
        return argv

    monkeypatch.setattr(cpu, "_argv", intercept)
    cpu_runtime = native_tokenizers.Runtime(
        Path(os.environ["SLAIF_CPU_V2_TEST_ROOT"]),
        Path(os.environ["SLAIF_CPU_V2_TEST_PACKAGES"]),
        "python3.12",
    )
    policy = cpu.Policy(address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=120)
    policy_root, _ = _install_policy(tmp_path, "policy", _DOCUMENTS)
    reader = capture.PolicyCaptureReader(str(policy_root))
    encoder = q.ResidentQueryEncoder(
        raw, root, definition, token, inv.inventory_id, runtime, cpu_runtime,
        worker_policy=policy,
    )
    return {
        "raw": raw,
        "root": root,
        "definition": definition,
        "token": token,
        "inv": inv,
        "runtime": runtime,
        "cpu_runtime": cpu_runtime,
        "policy": policy,
        "policy_root": policy_root,
        "reader": reader,
        "encoder": encoder,
    }


def _observe(session, events):
    # Measure the genuine guarded entry boundaries while delegating to the
    # real implementations; the legacy public signatures stay untouched.
    tokenizer = session._tokenizer
    worker = session._worker
    real_encode_guarded = tokenizer._encode_guarded
    real_forward_guarded = worker._forward_guarded
    real_receipt = session._receipt

    def encode_guarded(text, admission, op_end):
        receipt = real_encode_guarded(text, admission, op_end)
        events.append(("receipt", receipt))
        return receipt

    def forward_guarded(rows, admission, op_end):
        events.append(("forward", rows))
        return real_forward_guarded(rows, admission, op_end)

    def receipt_check(receipt, text):
        real_receipt(receipt, text)
        events.append(("checked", receipt))

    return encode_guarded, forward_guarded, receipt_check


def _read_counter(reader, counts):
    real_read = capture.PolicyCaptureReader.read_selection.__get__(
        reader, type(reader))

    def counting_read(*args, **kwargs):
        counts.append(1)
        return real_read(*args, **kwargs)

    return counting_read


def _write_counter(tracked_pipes, log):
    # Narrowly scoped real os.write delegation, matched to the active pipe
    # that owns the fd (live pipe identity, never a stale numeric fd).
    # Every call is delegated to the real os.write; only writes to a named
    # live child stdin pipe are recorded, keeping the requested length and
    # the actual delegated return value (kernel bytes) distinct so calls and
    # bytes stay separate.  A closed pipe is a stale identity and is skipped
    # so a reused descriptor is never attributed to it.  The live pipes held
    # by the test exclude descriptor reuse, and the wrapper is installed only
    # around the protected operation.
    real_write = os.write

    def counting_write(fd, data):
        for pipe in tracked_pipes:
            try:
                active_fd = pipe.fileno()
            except (OSError, ValueError):
                continue  # pipe closed: a stale identity, not this fd
            if active_fd == fd:
                actual = real_write(fd, data)
                log.append((id(pipe), len(data), actual))
                return actual
        return real_write(fd, data)

    return counting_write


def test_matched_new_positive_planned_actual_and_legacy(tmp_path, monkeypatch):
    real_argv = cpu._argv
    sc = _scenario(tmp_path, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    try:
        session = sc["encoder"].cleanup_owner
        expected = _expected_tuple(session)
        planned = cpu_execution_contract.prepare(
            sc["raw"], sc["root"], sc["definition"], sc["token"],
            sc["inv"].inventory_id, sc["runtime"], sc["cpu_runtime"],
            worker_policy=sc["policy"],
        )
        worker = session._worker
        tokenizer = session._tokenizer
        worker_child = worker._child
        token_child = tokenizer._child
        # Live child stdin pipe identities, captured while the children are
        # live, are the write-tracking identity (never a stale numeric fd).
        token_pipe = token_child.stdin
        worker_pipe = worker_child.stdin
        events = []
        encode_guarded, forward_guarded, receipt_check = _observe(session, events)
        monkeypatch.setattr(tokenizer, "_encode_guarded", encode_guarded)
        monkeypatch.setattr(worker, "_forward_guarded", forward_guarded)
        monkeypatch.setattr(session, "_receipt", receipt_check)
        # One real exact admission with a bounded cooperative deadline that
        # spans the protected operation only; its own entry reads happen
        # before the cut counters are installed below.
        admission = ppr.request_current_view(sc["reader"], CREDENTIAL,
                                             deadline_ms=30000)
        # Genuine selected-observation cut reads (installed after the
        # admission so its own entry reads are excluded) and narrow real
        # os.write delegation on the live child stdin pipe identities,
        # installed only around the protected operation.
        real_read_bound = capture.PolicyCaptureReader.read_selection.__get__(
            sc["reader"], type(sc["reader"]))
        reads = []
        monkeypatch.setattr(sc["reader"], "read_selection",
                            _read_counter(sc["reader"], reads))
        writes = []
        real_write = os.write
        os.write = _write_counter([token_pipe, worker_pipe], writes)
        try:
            result = sc["encoder"]._encode_expected_identity_admitted(
                "hello", expected, admission)
        finally:
            os.write = real_write
        # Both actual selected observation cuts read genuinely: the T1 cut
        # (tokenizer) and the T2 cut (forward) each made one real selected
        # read of the unchanged current view.
        assert reads == [1, 1]
        # Real dual transfers: the exact framed text and forward payloads
        # reached the genuine child stdin descriptors as actual delegated
        # kernel bytes matched by live pipe identity (booked counters alone
        # would not prove kernel bytes were sent).
        assert sum(actual for _pid, _req, actual in writes
                   if _pid == id(token_pipe)) == _frame_len("hello")
        assert sum(actual for _pid, _req, actual in writes
                   if _pid == id(worker_pipe)) == _forward_frame_len(
                       [[1, 3, 2]])
        # Genuine tokenizer receipt, real receipt validation and the real
        # forward entry, in that order; the resident validates the same
        # receipt again after the session returns, so the real order carries
        # a fourth checked event.
        assert [k for k, _ in events] == \
            ["receipt", "checked", "forward", "checked"]
        receipt = events[0][1]
        assert receipt.ids == (1, 3, 2) and receipt.count == 3
        assert events[2][1] == [(1, 3, 2)]
        # The admitted view is still current immediately after the positive;
        # this custody recheck uses the genuine reader (not a guarded cut),
        # so the real reader is restored before it runs.
        monkeypatch.setattr(sc["reader"], "read_selection", real_read_bound)
        assert admission._invalid is False
        assert admission.recheck(deadline_ms=30000) is True
        # Real FAKE child framework: the first token ID replicated across
        # 1024 components; through genuine normalization the expected
        # payload is 1024 copies of 0.03125 (float32), not one 1.0
        # followed by zeros.
        payload = struct.pack("<1024f", *([1.0 / 32.0] * 1024))
        assert result.payload == payload
        assert result.payload_sha256 == hashlib.sha256(payload).hexdigest()
        # Matched new: the planned (childless) and actual (genuine child
        # handshake) measured identities are byte-equal on the same
        # synthetic setup with unchanged inputs.
        assert planned.record_bytes == session.execution_record
        assert planned.fingerprint == session.execution_fingerprint
        assert planned.intended_execution_fingerprint == \
            session.intended_execution_fingerprint
        assert planned.space_id == session.space.space_id
        record = json.loads(session.execution_record)
        assert record["worker"] == session._worker_identity()
        assert record["bridge"] == cpu_execution_contract._bridge()
        assert session._worker.code_fingerprint == cpu._code_identity()
        # Same-runtime legacy result through the shared algorithm.
        legacy = sc["encoder"].encode_query("hello")
        assert (legacy.payload, legacy.execution_fingerprint,
                legacy.intended_execution_fingerprint, legacy.execution_record
                ) == (result.payload, result.execution_fingerprint,
                      result.intended_execution_fingerprint,
                      result.execution_record)
        # Observable counting boundaries: one successful call and one
        # successful forward per admitted and per legacy transfer.
        assert session._tokenizer._calls == 2
        assert session._worker._calls == 2
    finally:
        sc["encoder"].close()
    # Reaping evidence: both real children were reaped by the real cleanup.
    assert worker_child.poll() is not None and token_child.poll() is not None


def test_t1_selected_change_after_renewal_before_text_bytes(tmp_path, monkeypatch):
    real_argv = cpu._argv
    sc = _scenario(tmp_path, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    try:
        session = sc["encoder"].cleanup_owner
        expected = _expected_tuple(session)
        old_tokenizer = session._tokenizer
        old_child = old_tokenizer._child
        old_pipe = old_child.stdin
        worker = session._worker
        worker_child = worker._child
        worker_pipe = worker_child.stdin
        startup_input = worker._input
        startup_output = worker._output
        assert startup_input > 0 and startup_output > 0  # genuine startup
        real_renew = session._renew
        renewals = []
        renewed_entries = []
        # Live pipe identities (old tokenizer + worker) are the write
        # tracking identity; the renewed tokenizer's live pipe is captured
        # and added during genuine renewal.
        tracked_pipes = [old_pipe, worker_pipe]
        writes = []

        def renew_then_change(sizes):
            real_renew(sizes)
            new_tokenizer = session._tokenizer
            new_child = new_tokenizer._child
            # Capture the new pipe identity and fd while the renewed child is
            # live (its descriptor is closed by the later real cleanup);
            # retain both for post-cleanup identity checks and write tracking.
            new_pipe = new_child.stdin
            tracked_pipes.append(new_pipe)
            renewals.append((new_tokenizer, new_child,
                             new_pipe.fileno(), new_pipe))
            # Instrument the actual renewed guarded tokenizer: delegate to
            # its real method and record the actual entry (which yields zero
            # receipt result, refusing at the T1 cut).
            real_renewed_encode = new_tokenizer._encode_guarded

            def renewed_encode_guarded(text, admission_, op_end_):
                renewed_entries.append(1)
                return real_renewed_encode(text, admission_, op_end_)

            new_tokenizer._encode_guarded = renewed_encode_guarded
            # Rotate the actually installed synthetic selection with a
            # genuine same wire / new generation before any real text
            # bytes or receipt.
            _publish_selection(sc["policy_root"], 2,
                               _encode_policy([PRINCIPAL], _DOCUMENTS))

        # Drive the genuine renewal predicate: a bounded synthetic
        # test-only remaining lifetime below the existing 7-second
        # threshold, without changing policy identity, so the real
        # close-and-respawn runs before the guarded entry.
        session._tokenizer._deadline = time.monotonic() + 1
        monkeypatch.setattr(session, "_renew", renew_then_change)
        events = []
        encode_guarded, forward_guarded, receipt_check = _observe(session, events)
        # The old-tokenizer wrapper cannot observe an invocation on the newly
        # renewed tokenizer; it is installed only to prove no old-side call.
        monkeypatch.setattr(old_tokenizer, "_encode_guarded", encode_guarded)
        monkeypatch.setattr(worker, "_forward_guarded", forward_guarded)
        monkeypatch.setattr(session, "_receipt", receipt_check)
        # One real exact admission with a bounded cooperative deadline that
        # spans the protected operation only; its own entry reads happen
        # before the cut counter is installed below.
        admission = ppr.request_current_view(sc["reader"], CREDENTIAL,
                                             deadline_ms=30000)
        reads = []
        monkeypatch.setattr(sc["reader"], "read_selection",
                            _read_counter(sc["reader"], reads))
        writes = []
        real_write = os.write
        os.write = _write_counter(tracked_pipes, writes)
        try:
            with pytest.raises(q.QueryRefused, match="refused"):
                sc["encoder"]._encode_expected_identity_admitted(
                    "hello", expected, admission)
        finally:
            os.write = real_write
        # The one genuine denying selected read: the T1 cut read the rotated
        # (new generation) selection on the renewed tokenizer and observed
        # the mismatch that latched the admission.
        assert reads == [1]
        # Genuine renewal: the real close-and-respawn ran and the new child
        # is a different process from the renewed-away child; the retained
        # live fd and pipe identity captured during renewal are used after
        # the real cleanup closed that descriptor.
        assert len(renewals) == 1
        new_tokenizer, new_child, new_fd, new_pipe = renewals[0]
        assert type(new_fd) is int and new_fd >= 0  # captured live, renewal
        assert new_tokenizer is not old_tokenizer
        assert new_child.pid != old_child.pid
        assert old_child.poll() is not None
        assert new_child.poll() is not None
        # Refused T1: zero kernel text bytes and zero receipts, although
        # the existing attempt counters are booked before transport (a
        # booked counter does not prove kernel bytes were sent).
        assert events == []
        # The actual renewed guarded tokenizer entry was made (recorded by
        # the instrumented real method) with a zero receipt result (the T1
        # cut refused before any receipt).
        assert renewed_entries == [1]
        assert new_tokenizer._calls == 1
        assert new_tokenizer._input == _frame_len("hello")
        assert _frame_len("hello") == 60  # the exact named framed hello wire
        assert new_tokenizer._output == 0
        assert new_tokenizer._child is None  # reaped by the real cleanup
        # No kernel write reached either tokenizer stdin pipe identity (old
        # or renewed); the tokenizer child sends its ready line without a
        # host write, so there is no unrelated startup write on this side.
        assert [p for p, _req, _actual in writes
                if p in (id(old_pipe), id(new_pipe))] == []
        # No forward payload was ever written; the startup handshake is the
        # only real exchange traffic (distinguished: it predates the
        # protected operation and is never guarded).
        assert [p for p, _req, _actual in writes if p == id(worker_pipe)] == []
        assert worker._calls == 0
        assert worker._input == startup_input
        assert worker._output == startup_output
        # The observed mismatch latches the admission permanently; even a
        # further same-wire rotation cannot re-validate it.
        assert admission._invalid is True
        _publish_selection(sc["policy_root"], 3,
                           _encode_policy([PRINCIPAL], _DOCUMENTS))
        assert admission.recheck(deadline_ms=30000) is False
        # The shared reader is never latched: a fresh admission succeeds
        # only through the actual reader/matcher on the new generation.
        fresh = ppr.request_current_view(sc["reader"], CREDENTIAL,
                                         deadline_ms=30000)
        assert fresh.selection.generation == 3
        assert fresh.policy_id == admission.policy_id
        # Custody: the resident entry refuses and the real cleanup closed
        # the session (tokenizer, then worker, then stage).
        assert sc["encoder"]._state == "refused"
        assert sc["encoder"].cleanup_owner is session
        assert session._state == "closed"
        assert session._tokenizer is None and session._worker is None
        assert session._stage is None
    finally:
        sc["encoder"].close()


def test_t2_selected_change_after_receipt_before_forward_payload(tmp_path, monkeypatch):
    real_argv = cpu._argv
    sc = _scenario(tmp_path, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    try:
        session = sc["encoder"].cleanup_owner
        expected = _expected_tuple(session)
        worker = session._worker
        tokenizer = session._tokenizer
        worker_child = worker._child
        tokenizer_child = tokenizer._child
        worker_pipe = worker_child.stdin
        startup_input = worker._input
        startup_output = worker._output
        assert startup_input > 0 and startup_output > 0  # genuine startup
        events = []
        encode_guarded, _observed_forward, receipt_check = _observe(
            session, events)
        # The actual private guarded entry, captured before it is wrapped, so
        # the forward is recorded exactly once at true guarded entry.
        real_forward = worker._forward_guarded

        def forward_guarded(rows, admission_, op_end):
            events.append(("forward", rows))
            # Rotate the actually installed synthetic selection with a
            # genuine same wire / new generation after the real tokenizer
            # receipt and before any real CPU forward payload.
            _publish_selection(sc["policy_root"], 2,
                               _encode_policy([PRINCIPAL], _DOCUMENTS))
            return real_forward(rows, admission_, op_end)

        monkeypatch.setattr(tokenizer, "_encode_guarded", encode_guarded)
        monkeypatch.setattr(worker, "_forward_guarded", forward_guarded)
        monkeypatch.setattr(session, "_receipt", receipt_check)
        # One real exact admission with a bounded cooperative deadline that
        # spans the protected operation only; its own entry reads happen
        # before the cut counters are installed below.
        admission = ppr.request_current_view(sc["reader"], CREDENTIAL,
                                             deadline_ms=30000)
        reads = []
        monkeypatch.setattr(sc["reader"], "read_selection",
                            _read_counter(sc["reader"], reads))
        writes = []
        real_write = os.write
        os.write = _write_counter([worker_pipe], writes)
        try:
            with pytest.raises(q.QueryRefused, match="refused"):
                sc["encoder"]._encode_expected_identity_admitted(
                    "hello", expected, admission)
        finally:
            os.write = real_write
        # The genuine tokenizer receipt was produced and the real receipt
        # validation ran before the CPU entry, and the forward was actually
        # entered with the real receipt ids.
        assert [k for k, _ in events] == ["receipt", "checked", "forward"]
        receipt = events[0][1]
        assert receipt.ids == (1, 3, 2) and receipt.count == 3
        digest = hashlib.sha256(
            json.dumps(["hello", None], ensure_ascii=True,
                       separators=(",", ":")).encode()).hexdigest()
        assert receipt.input_sha256 == digest
        assert events[2][1] == [(1, 3, 2)]
        # Actual current selected read counts: the T1 cut read the
        # unchanged selection (one genuine read) and the T2 cut read the
        # rotated generation (the second genuine read, the observed
        # mismatch).
        assert reads == [1, 1]
        # Distinguished real writes: the startup handshake predates the
        # protected operation (booked, never guarded); zero forward kernel
        # bytes reached the actual worker stdin pipe identity.
        assert [p for p, _req, _actual in writes if p == id(worker_pipe)] == []
        assert worker._calls == 0
        assert worker._input == startup_input
        assert worker._output == startup_output
        # Reaping evidence: the real forward shutdown reaped the worker
        # child and the session cleanup reaped the tokenizer child.
        assert worker_child.poll() is not None
        assert tokenizer_child.poll() is not None
        # The observed mismatch latches the admission; custody preserved.
        assert admission._invalid is True
        assert sc["encoder"]._state == "refused"
        assert sc["encoder"].cleanup_owner is session
        assert session._state == "closed"
        # The latched admission refuses without a further reader call.
        assert admission.recheck(deadline_ms=30000) is False
        assert reads == [1, 1]
    finally:
        sc["encoder"].close()


def test_old_expected_binding_refuses_before_protected_payloads(tmp_path, monkeypatch):
    real_argv = cpu._argv
    sc = _scenario(tmp_path, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    try:
        session = sc["encoder"].cleanup_owner
        worker = session._worker
        tokenizer = session._tokenizer
        startup_input = worker._input
        record = json.loads(session.execution_record)
        # Test-side reconstruction (clearly labeled) of the exact
        # historical execution binding from the base preimages: same
        # synthetic fixture inputs and same policy; only the measured
        # worker code and bridge digests differ, exactly as the reviewed
        # edits require.
        old_code = hashlib.sha256(cpu._json(
            {"schema": 1, "api": "cpu-worker-v1",
             "files": _HISTORICAL_CODE_SHA256})).hexdigest()
        assert old_code != record["worker"]["code"]
        assert _HISTORICAL_BRIDGE_SHA256 != record["bridge"]
        record["worker"]["code"] = old_code
        record["bridge"] = _HISTORICAL_BRIDGE_SHA256
        old_fingerprint = fingerprint(
            {"kind": "isolated-cpu-embedding-execution-v2", **record})
        assert old_fingerprint != session.execution_fingerprint
        old_expected = (session.space.space_id,
                        session.definition.fingerprint(),
                        q._POLICY_DIGEST, old_fingerprint[7:])
        events = []
        encode_guarded, forward_guarded, receipt_check = _observe(session, events)
        monkeypatch.setattr(tokenizer, "_encode_guarded", encode_guarded)
        monkeypatch.setattr(worker, "_forward_guarded", forward_guarded)
        monkeypatch.setattr(session, "_receipt", receipt_check)
        # One real exact admission; the refusal must be the identity gate,
        # so the pristine current view stays un-latched.
        admission = ppr.request_current_view(sc["reader"], CREDENTIAL,
                                             deadline_ms=30000)
        # A new runtime with the verified old execution binding must refuse
        # before either protected payload, with a pristine current view and
        # actual valid input.
        with pytest.raises(q.QueryRefused, match="refused"):
            sc["encoder"]._encode_expected_identity_admitted(
                "hello", old_expected, admission)
        assert events == []
        assert tokenizer._calls == 0 and tokenizer._input == 0
        assert worker._calls == 0 and worker._input == startup_input
        # The refusal is the identity gate, not the admission: the
        # pristine current view still re-validates and the admission is
        # not latched.
        assert admission._invalid is False
        assert admission.recheck(deadline_ms=30000) is True
        assert sc["encoder"]._state == "refused"
        assert session._state == "closed"
    finally:
        sc["encoder"].close()


def test_late_observation_and_interruption_custody(tmp_path, monkeypatch):
    class _Interrupted(BaseException):
        pass

    marker = _Interrupted()
    real_argv = cpu._argv

    # Phase 1: a controlled non-Exception interruption at a real selected
    # read in the new node; identity and custody are preserved.
    first = _scenario(tmp_path, monkeypatch, real_argv)
    reader = first["reader"]
    encoder = first["encoder"]
    encoder.__enter__()
    try:
        session = encoder.cleanup_owner
        expected = _expected_tuple(session)
        events = []
        encode_guarded, forward_guarded, receipt_check = _observe(session, events)
        monkeypatch.setattr(session._tokenizer, "_encode_guarded", encode_guarded)
        monkeypatch.setattr(session._worker, "_forward_guarded", forward_guarded)
        monkeypatch.setattr(session, "_receipt", receipt_check)
        # One real exact admission; its own entry reads happen before the
        # interrupting read below is installed.
        admission = ppr.request_current_view(reader, CREDENTIAL, deadline_ms=30000)
        reads = []
        real_read = capture.PolicyCaptureReader.read_selection.__get__(
            reader, type(reader))

        def interrupting_read(*args, **kwargs):
            reads.append(1)
            # Delegate the actual read first, then raise the exact marker
            # after the selected read has been entered.
            real_read(*args, **kwargs)
            raise marker

        monkeypatch.setattr(reader, "read_selection", interrupting_read)
        with pytest.raises(_Interrupted) as excinfo:
            encoder._encode_expected_identity_admitted("hello", expected, admission)
        assert excinfo.value is marker
        assert reads == [1]
        assert events == []
        assert encoder._state == "refused" and encoder.cleanup_owner is session
        assert session._state == "closed"
    finally:
        encoder.close()

    # Phase 2: an actual late selected observation after real write
    # readiness, under a short legitimate deadline and a bounded real delay
    # on the real monotonic clock; no post-deadline forward bytes.
    second_dir = tmp_path / "second"
    second_dir.mkdir(mode=0o700)
    second = _scenario(second_dir, monkeypatch, real_argv)
    reader2 = second["reader"]
    encoder2 = second["encoder"]
    encoder2.__enter__()
    try:
        session2 = encoder2.cleanup_owner
        expected2 = _expected_tuple(session2)
        # A legitimately admitted request with a short real lifetime.
        admission2 = ppr.request_current_view(reader2, CREDENTIAL,
                                              deadline_ms=1000)
        events2 = []
        encode_guarded2, forward_guarded2, receipt_check2 = _observe(
            session2, events2)
        monkeypatch.setattr(session2._tokenizer, "_encode_guarded", encode_guarded2)
        monkeypatch.setattr(session2._worker, "_forward_guarded", forward_guarded2)
        monkeypatch.setattr(session2, "_receipt", receipt_check2)
        worker2 = session2._worker
        tokenizer2 = session2._tokenizer
        worker2_child = worker2._child
        worker2_pipe = worker2_child.stdin
        startup_input = worker2._input
        reads2 = []
        delays = []
        real_read2 = capture.PolicyCaptureReader.read_selection.__get__(
            reader2, type(reader2))

        def delayed_read(*args, **kwargs):
            reads2.append(1)
            result = real_read2(*args, **kwargs)
            if len(reads2) >= 2:
                # Bounded real delay on the real monotonic clock: the T2
                # cut's genuine read completes late against the clipped
                # absolute end.
                started = time.monotonic()
                time.sleep(1.5)
                delays.append(time.monotonic() - started)
            return result

        monkeypatch.setattr(reader2, "read_selection", delayed_read)
        writes2 = []
        real_write = os.write
        os.write = _write_counter([worker2_pipe], writes2)
        try:
            with pytest.raises(q.QueryRefused, match="refused"):
                encoder2._encode_expected_identity_admitted(
                    "hello", expected2, admission2)
        finally:
            os.write = real_write
        # The T1 cut read the unchanged selection fast (genuine); the T2
        # cut's read was genuine and then completed late against the
        # clipped absolute end.
        assert reads2 == [1, 1]
        assert delays and delays[0] >= 1.49
        assert admission2._invalid is True
        # The real text transfer completed (T1 admitted): one genuine
        # receipt, the real receipt validation and the real forward entry
        # with the real receipt ids.
        assert [k for k, _ in events2] == ["receipt", "checked", "forward"]
        assert events2[0][1].ids == (1, 3, 2)
        assert events2[0][1].count == 3
        assert events2[2][1] == [(1, 3, 2)]
        assert tokenizer2._calls == 1
        assert tokenizer2._input == _frame_len("hello")
        assert tokenizer2._output > 0  # the real response was received
        # No post-deadline forward bytes: the T2 cut refused before the
        # first forward write; booked counters alone do not prove kernel
        # bytes were sent, and none reached the actual worker stdin pipe
        # identity.
        assert [p for p, _req, _actual in writes2 if p == id(worker2_pipe)] == []
        assert worker2._calls == 0 and worker2._input == startup_input
        assert worker2_child.poll() is not None  # real forward shutdown
        # A latched admission refuses without a further reader call.
        assert admission2.recheck(deadline_ms=1000) is False
        assert reads2 == [1, 1]
        assert encoder2._state == "refused"
        assert session2._state == "closed"
    finally:
        encoder2.close()
