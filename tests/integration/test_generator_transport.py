"""Real loopback HTTP/SSE behavior tests for the bounded transport (003-b).

Acceptance coverage (oap/orders/003-b, criteria 1-4 at transport level):

- one total deadline spans connect/write/headers/body; already-expired
  deadlines refuse before dispatch; late-body drips cannot overrun the
  budget; valid slow calls inside the budget still succeed;
- only positively pre-dispatch connect failures are retryable: an accepted
  request with delayed/absent headers is non-retryable in BOTH the httpx
  read-timeout and the total-deadline forms, normal AND streaming;
- raw httpx/network exceptions never escape;
- SSE parser correctness on literal wire bytes (LF/CRLF, split multibyte
  UTF-8, coalesced frames, multiline data/comments, partial trailing);
- bounded queue backpressure: terminal/error/eof signals are never lost
  when the data queue is full; closing a consumer cancels its own request
  and stops its worker (no orphaned threads).

All servers are owned loopback fixtures with unique synthetic keys; no real
product service, network, GPU or model is involved.
"""

from __future__ import annotations

import json
import threading
import time

import pytest

from conftest import SYNTHETIC_API_KEY, sse_frame
from conftest import sse_data_frame, sse_data_only

from slaif_raggedized_helper.model_clients import transport as T
from slaif_raggedized_helper.model_clients.transport import (
    GatewayTransport,
    SSEFrame,
    SSEStream,
    TransportConnectError,
    TransportConfigError,
    TransportError,
    TransportProtocolError,
    TransportRefusedError,
    TransportTimeoutError,
    TransportTruncatedError,
)

_TOLERANCE = 0.35  # wall-clock scheduling tolerance for CI runners


def _frames(stream: SSEStream) -> list[SSEFrame]:
    return list(stream)


# ---------------------------------------------------------------------------
# post_json: positive/negative HTTP under one total deadline
# ---------------------------------------------------------------------------

def test_post_json_happy_path_records_exact_call(server):
    srv = server(lambda h, r: h._send_json(200, {"ok": True}))
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5, api_key=SYNTHETIC_API_KEY)
    status, body = client.post_json("/v1/responses", b'{"x":1}', deadline=time.monotonic() + 5)
    assert status == 200
    assert json.loads(body) == {"ok": True}
    assert srv.paths == ["/v1/responses"]
    req = srv.state.requests[0]
    assert req.headers["authorization"] == f"Bearer {SYNTHETIC_API_KEY}"
    assert req.headers["content-type"] == "application/json"
    assert req.body == b'{"x":1}'
    assert SYNTHETIC_API_KEY not in req.body.decode("utf-8")


def test_post_json_4xx_returns_status_and_body(server):
    srv = server(lambda h, r: h._send_json(400, {"error": "CANARY-BODY"}))
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    status, body = client.post_json("/v1/responses", b"{}", deadline=time.monotonic() + 5)
    assert status == 400
    assert b"CANARY-BODY" in body  # transport returns the body; classification is the caller's
    assert srv.count("/v1/responses") == 1


def test_redirect_refused_and_never_followed(server):
    sink = server(lambda h, r: h._send_json(200, {"ok": True}))
    srv = server(
        lambda h, r: (
            h.send_response(302),
            h.send_header("Location", f"{sink.url}/stolen"),
            h.send_header("Content-Length", "0"),
            h.send_header("Connection", "close"),
            h.end_headers(),
        )
    )
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    with pytest.raises(TransportRefusedError) as excinfo:
        client.post_json("/v1/responses", b"{}", deadline=time.monotonic() + 5)
    assert "redirect refused (HTTP 302)" in str(excinfo.value)
    assert srv.paths == ["/v1/responses"]
    assert sink.state.requests == []  # the Location was never contacted


def test_pre_connect_failure_is_retryable_class(closed_port):
    client = GatewayTransport(f"http://127.0.0.1:{closed_port}", timeout_seconds=0.5)
    with pytest.raises(TransportConnectError) as excinfo:
        client.post_json("/v1/responses", b"{}", deadline=time.monotonic() + 5)
    assert excinfo.value.retryable is True
    assert excinfo.value.dispatched is False


# ---------------------------------------------------------------------------
# accepted request / delayed or absent headers: UNKNOWN, never retried
# ---------------------------------------------------------------------------

def test_accepted_header_delay_httpx_read_timeout_not_retryable(server):
    def scenario(h, r):
        time.sleep(0.6)  # past the 0.15s per-operation timeout
        h._send_json(200, {"ok": True})

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=0.15)
    start = time.monotonic()
    with pytest.raises(TransportTimeoutError) as excinfo:
        client.post_json("/v1/responses", b"{}", deadline=time.monotonic() + 10)
    assert excinfo.value.retryable is False
    assert excinfo.value.dispatched is True
    assert srv.count("/v1/responses") == 1  # the server accepted the POST
    assert time.monotonic() - start < 10  # bounded by the per-operation timeout


def test_accepted_header_delay_total_deadline_not_retryable(server):
    def scenario(h, r):
        time.sleep(2.0)
        h._send_json(200, {"ok": True})

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=10)
    start = time.monotonic()
    deadline = start + 0.3
    with pytest.raises(TransportTimeoutError) as excinfo:
        client.post_json("/v1/responses", b"{}", deadline=deadline)
    assert excinfo.value.retryable is False
    assert excinfo.value.dispatched is True
    assert srv.count("/v1/responses") == 1
    assert time.monotonic() - start <= deadline - start + _TOLERANCE


def test_late_body_drip_cannot_overrun_total_budget(server):
    """Regression of /tmp/raggedized003-deadline-repro.py (kept in-suite)."""

    def scenario(h, r):
        h.send_response(200)
        h.send_header("Content-Length", "2")
        h.send_header("Connection", "close")
        h.end_headers()
        time.sleep(0.14)
        try:
            h.wfile.write(b"a")
            h.wfile.flush()
            time.sleep(0.7)
            h.wfile.write(b"b")
            h.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=0.2)
    start = time.monotonic()
    deadline = start + 0.2
    with pytest.raises(TransportTimeoutError) as excinfo:
        client.post_json("/v1/responses", b"{}", deadline=deadline)
    assert excinfo.value.dispatched is True
    assert excinfo.value.retryable is False
    assert time.monotonic() - start <= 0.27  # exact repro tolerance


def test_valid_slow_call_inside_budget_succeeds(server):
    def scenario(h, r):
        h.send_response(200)
        h.send_header("Content-Length", "2")
        h.send_header("Connection", "close")
        h.end_headers()
        h.wfile.write(b"a")
        h.wfile.flush()
        time.sleep(0.1)
        h.wfile.write(b"b")

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=1.0)
    status, body = client.post_json("/v1/responses", b"{}", deadline=time.monotonic() + 5)
    assert status == 200
    assert body == b"ab"
    assert srv.count("/v1/responses") == 1


def test_expired_deadline_refused_before_dispatch(server):
    srv = server(lambda h, r: h._send_json(200, {"ok": True}))
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    expired = time.monotonic() - 1
    with pytest.raises(TransportTimeoutError) as excinfo:
        client.post_json("/v1/responses", b"{}", deadline=expired)
    assert excinfo.value.dispatched is False
    with pytest.raises(TransportTimeoutError):
        client.open_stream("/v1/responses", b"{}", deadline=expired)
    assert srv.state.requests == []  # nothing was dispatched


def test_base_url_root_and_versioned_base_hit_same_endpoint(server):
    def scenario(h, r):
        h._send_json(200, {"ok": True})

    srv = server(scenario)
    root = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    versioned = GatewayTransport(f"{srv.url}/v1", timeout_seconds=5)
    assert root.post_json("/v1/responses", b"{}", deadline=time.monotonic() + 5)[0] == 200
    assert versioned.post_json("/v1/responses", b"{}", deadline=time.monotonic() + 5)[0] == 200
    assert srv.paths == ["/v1/responses", "/v1/responses"]  # never /v1/v1/responses


def test_base_url_with_unsupported_path_refused():
    with pytest.raises(TransportConfigError):
        GatewayTransport("http://127.0.0.1:9/api", timeout_seconds=5)
    with pytest.raises(TransportConfigError):
        GatewayTransport("http://127.0.0.1:9/v1/extra", timeout_seconds=5)
    with pytest.raises(TransportConfigError):
        GatewayTransport("http://127.0.0.1:9", timeout_seconds=-1)
    with pytest.raises(TransportConfigError):
        GatewayTransport("http://user:pass@127.0.0.1:9", timeout_seconds=5)


# ---------------------------------------------------------------------------
# streaming: header/body failures, backpressure, cancellation
# ---------------------------------------------------------------------------

def test_stream_accepted_header_delay_httpx_timeout_not_retryable(server):
    def scenario(h, r):
        time.sleep(0.6)
        h._send_headers_only()

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=0.15)
    with pytest.raises(TransportTimeoutError) as excinfo:
        with client.open_stream("/v1/responses", b"{}", deadline=time.monotonic() + 10):
            pass
    assert excinfo.value.retryable is False
    assert excinfo.value.dispatched is True
    assert srv.count("/v1/responses") == 1


def test_stream_accepted_header_delay_total_deadline_not_retryable(server):
    def scenario(h, r):
        time.sleep(2.0)
        h._send_headers_only()

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=10)
    start = time.monotonic()
    deadline = start + 0.3
    with pytest.raises(TransportTimeoutError) as excinfo:
        with client.open_stream("/v1/responses", b"{}", deadline=deadline):
            pass
    assert excinfo.value.retryable is False
    assert excinfo.value.dispatched is True
    assert srv.count("/v1/responses") == 1
    assert time.monotonic() - start <= deadline - start + _TOLERANCE


def test_stream_close_after_send_is_safe_non_retryable(server):
    def scenario(h, r):
        h._accept_then_close()  # accept the POST, close before any headers

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    with pytest.raises(TransportError) as excinfo:
        with client.open_stream("/v1/responses", b"{}", deadline=time.monotonic() + 10):
            pass
    assert excinfo.value.dispatched is True
    assert excinfo.value.retryable is False
    assert not isinstance(excinfo.value, (TransportTimeoutError, TransportConnectError))
    assert srv.count("/v1/responses") == 1
    assert "CANARY" not in str(excinfo.value)


def test_stream_5xx_header_failure_does_not_echo_body(server):
    srv = server(lambda h, r: h._send_raw(503, b"CANARY-BODY", "text/plain"))
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    with pytest.raises(TransportRefusedError) as excinfo:
        with client.open_stream("/v1/responses", b"{}", deadline=time.monotonic() + 10):
            pass
    assert "request refused (HTTP 503)" in str(excinfo.value)
    assert "CANARY" not in str(excinfo.value)
    assert srv.count("/v1/responses") == 1


def test_stream_happy_path_frames_clean_eof_worker_stops(server):
    def scenario(h, r):
        h._send_headers_only()
        h._write_stream(sse_frame("response.created", {"id": "r1"}))
        h._write_stream(sse_frame("response.completed", {"id": "r1", "status": "completed"}))

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    frames = []
    with client.open_stream("/v1/responses", b"{}", deadline=time.monotonic() + 5) as handle:
        for frame in handle.frames():
            frames.append(frame)
        worker = handle._thread
        deadline_stop = time.monotonic() + 3
        while worker.is_alive() and time.monotonic() < deadline_stop:
            time.sleep(0.01)
        assert not worker.is_alive()  # no orphaned worker after clean close
    assert [(f.event, f.data) for f in frames] == [
        ("response.created", '{"id":"r1"}'),
        ("response.completed", '{"id":"r1","status":"completed"}'),
    ]
    assert srv.count("/v1/responses") == 1


def test_stream_queue_saturation_delivers_all_frames_and_eof(server):
    n_frames = 200
    maxsize = 32  # _AsyncStreamHandle bounded data queue capacity

    def scenario(h, r):
        h._send_headers_only()
        for i in range(n_frames):
            h._write_stream(sse_frame("message", {"i": i, "pad": "x" * 480}))
            time.sleep(0.001)  # pace frames; individual chunks, no coalescing proof needed

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=15)
    seen = []
    with client.open_stream("/v1/responses", b"{}", deadline=time.monotonic() + 15) as handle:
        # Synchronize on the real condition: the bounded data queue must be
        # observed at EXACT full capacity before any consumption starts, so
        # the backpressure proof does not rely on TCP coalescing behavior.
        full_by = time.monotonic() + 10
        while handle._queue.qsize() < maxsize and time.monotonic() < full_by:
            time.sleep(0.005)
        assert handle._queue.qsize() == maxsize
        for frame in handle.frames():
            seen.append(frame.data)
            time.sleep(0.004)  # slow consumer: the paced producer outruns it
    assert len(seen) == n_frames
    assert [json.loads(d)["i"] for d in seen] == list(range(n_frames))
    assert srv.count("/v1/responses") == 1
    stopped = time.monotonic() + 4
    while handle._thread.is_alive() and time.monotonic() < stopped:
        time.sleep(0.01)
    assert not handle._thread.is_alive()  # owned worker stopped after clean EOF


def test_stream_error_after_full_queue_is_delivered(server):
    n_frames = 120
    maxsize = 32  # _AsyncStreamHandle bounded data queue capacity

    def scenario(h, r):
        h._send_headers_only()
        for i in range(n_frames):
            h._write_stream(sse_frame("message", {"i": i, "pad": "x" * 480}))
            time.sleep(0.001)  # pace frames: queue is full when the RST lands
        h._close_with_reset()  # RST: mid-stream network failure after all frames

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=15)
    seen = []
    with client.open_stream("/v1/responses", b"{}", deadline=time.monotonic() + 15) as handle:
        # Synchronize on the real condition: wait until the bounded data
        # queue is observed at EXACT full capacity before consumption starts.
        full_by = time.monotonic() + 10
        while handle._queue.qsize() < maxsize and time.monotonic() < full_by:
            time.sleep(0.005)
        assert handle._queue.qsize() == maxsize  # observed full, no sample consumed
        with pytest.raises(TransportError) as excinfo:
            for frame in handle.frames():
                seen.append(frame.data)
                time.sleep(0.004)  # slow consumer: stays far behind the producer
    # The terminal failure signal survived the full data queue.
    assert not isinstance(excinfo.value, TransportTimeoutError)
    assert excinfo.value.dispatched is True
    assert len(seen) >= 1
    assert srv.count("/v1/responses") == 1
    stopped = time.monotonic() + 4
    while handle._thread.is_alive() and time.monotonic() < stopped:
        time.sleep(0.01)
    assert not handle._thread.is_alive()  # owned worker stopped after the failure


def test_stream_early_close_stops_worker_no_orphans(server):
    def scenario(h, r):
        h._send_headers_only()
        for i in range(20):
            h._write_stream(sse_frame("message", {"i": i}))
            time.sleep(0.03)  # slow producer keeps the stream open

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=15)
    baseline = {t.name for t in threading.enumerate()}
    with client.open_stream("/v1/responses", b"{}", deadline=time.monotonic() + 15) as handle:
        frames = iter(handle.frames())
        for _ in range(2):
            next(frames)
        handle.close()  # consumer gives up early
    stopped = time.monotonic() + 4
    while handle._thread.is_alive() and time.monotonic() < stopped:
        time.sleep(0.01)
    assert not handle._thread.is_alive()  # owned worker/request cancelled and stopped
    time.sleep(0.1)
    leftovers = {t.name for t in threading.enumerate()} - baseline
    assert not leftovers, f"orphaned threads: {leftovers}"
    assert srv.count("/v1/responses") == 1


def test_stream_startup_deadline_race_no_late_dispatch(server, monkeypatch):
    """Controlled worker-start scheduling delay (003-b strategic probe):
    with a 25ms total budget and a 60ms delayed worker, start() must refuse
    pre-dispatch, the caller must return before the budget expires, and the
    already-cancelled worker must never dispatch a late POST."""
    original_worker = T._AsyncStreamHandle._worker

    def delayed_worker(self):
        time.sleep(0.06)  # controlled scheduling delay before the exchange
        original_worker(self)

    monkeypatch.setattr(T._AsyncStreamHandle, "_worker", delayed_worker)
    srv = server(lambda h, r: h._send_json(200, {"ok": True}))
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    start = time.monotonic()
    with pytest.raises(TransportTimeoutError) as excinfo:
        with client.open_stream("/v1/responses", b"{}", deadline=start + 0.025):
            pass
    # Pre-dispatch refusal (nothing was sent), retryable in principle but
    # the total budget is gone.
    assert excinfo.value.dispatched is False
    assert excinfo.value.retryable is True
    assert time.monotonic() - start <= 0.025 + _TOLERANCE
    # The delayed worker eventually wakes up: cancellation must beat its
    # dispatch boundary, so no request may have reached the server.
    time.sleep(0.15)
    assert srv.state.requests == []


def test_stream_slow_headers_within_budget_starts(server):
    """Valid slow call at the startup boundary: headers delayed well past
    thread-start scheduling but inside the budget must still succeed."""

    def scenario(h, r):
        time.sleep(0.15)
        h._send_headers_only()
        h._write_stream(sse_data_only({"type": "response.created",
                                       "response": {"id": "r1", "status": "in_progress"}}))
        h._write_stream(sse_data_only({"type": "response.completed",
                                       "response": {"id": "r1", "status": "completed"}}))

    srv = server(scenario)
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    frames = []
    start = time.monotonic()
    with client.open_stream("/v1/responses", b"{}", deadline=time.monotonic() + 5) as handle:
        for frame in handle.frames():
            frames.append(frame)
    assert [(f.data) for f in frames] == [
        '{"type":"response.created","response":{"id":"r1","status":"in_progress"}}',
        '{"type":"response.completed","response":{"id":"r1","status":"completed"}}',
    ]
    assert time.monotonic() - start <= 0.15 + _TOLERANCE
    assert srv.count("/v1/responses") == 1


def test_proxy_environment_is_not_inherited(server, monkeypatch):
    proxy_sink = server(lambda h, r: h._send_json(200, {"ok": True}))
    srv = server(lambda h, r: h._send_json(200, {"ok": True}))
    for var in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.setenv(var, f"{proxy_sink.url}")
    client = GatewayTransport(f"{srv.url}", timeout_seconds=5)
    status, _ = client.post_json("/v1/responses", b"{}", deadline=time.monotonic() + 5)
    assert status == 200
    assert srv.count("/v1/responses") == 1
    assert proxy_sink.state.requests == []  # no ambient proxy destination switch


# ---------------------------------------------------------------------------
# SSE parser: literal wire bytes, bounds, encodings
# ---------------------------------------------------------------------------

def test_sse_lf_crlf_and_coalesced_frames():
    lf = sse_frame("response.completed", {"a": 1})
    crlf = lf.replace(b"\n", b"\r\n")
    frames = _frames(SSEStream(iter([lf, crlf]), max_event_bytes=1024, max_stream_bytes=65536))
    assert [(f.event, f.data) for f in frames] == [
        ("response.completed", '{"a":1}'),
        ("response.completed", '{"a":1}'),
    ]


def test_sse_multiline_data_comments_and_inert_fields():
    wire = (
        b": leading comment\n"
        b"id: 42\n"
        b"retry: 5000\n"
        b"event: message\n"
        b"data: line one\n"
        b"data:line two\n"
        b": trailing comment\n"
        b"data: \n"
        b"\n"
    )
    frames = _frames(SSEStream(iter([wire]), max_event_bytes=1024, max_stream_bytes=65536))
    assert len(frames) == 1
    assert frames[0].event == "message"
    # SSE joins multiple data fields with LF; a "data: " with one space yields "".
    assert frames[0].data == "line one\nline two\n"


def test_sse_multibyte_utf8_split_across_chunks():
    # Real multibyte UTF-8 on the wire (no ASCII escaping): "č" is 2 bytes,
    # the rocket is 4. Split inside the "č" sequence AND inside the rocket.
    text = "\u010drni \U0001f680"
    wire = sse_data_frame("message", text)
    encoded = text.encode("utf-8")
    assert len(encoded) != len(text)  # sanity: the data really is multibyte

    for split_after in (wire.index(encoded[0]) + 1,  # inside "č"
                        wire.index(encoded[len("\u010drni ")]) + 2):  # inside rocket
        frames = _frames(SSEStream(
            iter([wire[:split_after], wire[split_after:]]),
            max_event_bytes=4096, max_stream_bytes=65536))
        assert [(f.event, f.data) for f in frames] == [("message", text)]


def test_sse_partial_trailing_frame_is_not_emitted():
    wire = b"event: message\ndata: incomplete\n"  # no terminating blank line
    stream = SSEStream(iter([wire]), max_event_bytes=1024, max_stream_bytes=65536)
    frames = _frames(stream)
    assert frames == []
    assert stream.incomplete_trailing is True


def test_sse_partial_trailing_line_is_not_emitted():
    stream = SSEStream(iter([b"data: cut"]), max_event_bytes=1024, max_stream_bytes=65536)
    assert _frames(stream) == []
    assert stream.incomplete_trailing is True


def test_sse_clean_eof_without_trailing_is_complete():
    wire = b"data: done\n\n"
    stream = SSEStream(iter([wire]), max_event_bytes=1024, max_stream_bytes=65536)
    frames = _frames(stream)
    assert [f.data for f in frames] == ["done"]
    assert stream.incomplete_trailing is False


def test_sse_malformed_utf8_refused_safely():
    stream = SSEStream(iter([b"data: ok\n\n", b"data: \xff\xfe\n\n"]),
                       max_event_bytes=1024, max_stream_bytes=65536)
    with pytest.raises(TransportProtocolError):
        _frames(stream)


def test_sse_line_bound_refused():
    wire = b"event: " + b"x" * 64 + b"\ndata: a\n\n"
    stream = SSEStream(iter([wire]), max_event_bytes=16, max_stream_bytes=65536)
    with pytest.raises(TransportTruncatedError):
        _frames(stream)


def test_sse_event_name_bound_refused():
    # A 100-byte event name with max_event_bytes=8 must be refused (003-a
    # audit probe): the per-line byte bound covers frame metadata.
    wire = b"event: " + b"y" * 100 + b"\ndata: a\n\n"
    stream = SSEStream(iter([wire]), max_event_bytes=8, max_stream_bytes=65536)
    with pytest.raises(TransportTruncatedError):
        _frames(stream)


def test_sse_event_data_bound_refused():
    wire = b"data: " + b"z" * 64 + b"\n\n"
    stream = SSEStream(iter([wire]), max_event_bytes=32, max_stream_bytes=65536)
    with pytest.raises(TransportTruncatedError):
        _frames(stream)


def test_sse_aggregate_stream_bound_refused():
    stream = SSEStream(
        iter([b"data: " + b"a" * 64 + b"\n\n"] * 4),
        max_event_bytes=1024,
        max_stream_bytes=150,
    )
    with pytest.raises(TransportTruncatedError):
        _frames(stream)
