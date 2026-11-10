"""Shared owned loopback HTTP fixtures for integration tests (OAP 003-b).

Every fixture binds 127.0.0.1 on an ephemeral port, records every received
request (exact path, headers, body, arrival order) and never touches external
networks, product services, real keys or corpora. The recording server does
NOT accept every endpoint silently: every path is recorded and the tests
assert the exact expected wire path, so a wrong-endpoint regression fails.

Synthetic API key canaries are unique to this suite and are never real
credentials.
"""

from __future__ import annotations

import json
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

SYNTHETIC_API_KEY = "sk-synthetic-003b-canary"


@dataclass
class RecordedRequest:
    path: str
    headers: dict[str, str]
    body: bytes
    received_at: float


class _BaseHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # silence request logging
        pass

    # -- plumbing ---------------------------------------------------------
    @property
    def _server_state(self) -> "ServerState":
        return self.server.state  # type: ignore[attr-defined]

    def _read_body(self) -> bytes:
        length = int(self.headers.get("content-length") or 0)
        return self.rfile.read(length) if length else b""

    def _record(self) -> RecordedRequest:
        record = RecordedRequest(
            path=self.path,
            headers={k.lower(): v for k, v in self.headers.items()},
            body=self._read_body(),
            received_at=time.monotonic(),
        )
        with self._server_state.lock:
            self._server_state.requests.append(record)
        return record

    def _send_json(self, status: int, doc: object) -> None:
        body = json.dumps(doc).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _send_raw(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _send_headers_only(self, status: int = 200) -> None:
        """Stream response: no Content-Length; terminated by close."""
        self.send_response(status)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()

    def _write_stream(self, data: bytes) -> None:
        self.wfile.write(data)
        self.wfile.flush()

    def _close_with_reset(self) -> None:
        """Close the accepted connection with RST after the body was read."""
        self.connection.setsockopt(
            socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        self.connection.close()
        self.close_connection = True

    def _accept_then_close(self) -> None:
        """Close before any response headers.

        The POST body was already read and recorded by the shared do_POST
        wrapper, so the accepted request is visible in the recording.
        """
        self.connection.close()
        self.close_connection = True


@dataclass
class ServerState:
    requests: list[RecordedRequest] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def paths(self) -> list[str]:
        return [r.path for r in self.requests]

    def count(self, path: str) -> int:
        return sum(1 for r in self.requests if r.path == path)


def sse_frame(event: str, payload: object) -> bytes:
    """Build one literal SSE frame (LF endings) from an event name + JSON payload."""
    return sse_data_frame(event, json.dumps(payload, separators=(",", ":"),
                                            ensure_ascii=True))


def sse_data_frame(event: str, data: str) -> bytes:
    """Build one literal SSE frame (LF endings) from an event name + raw data text.

    The data text is placed on the wire verbatim (no re-serialization), so
    multibyte UTF-8 stays real bytes for split-chunk tests.
    """
    return f"event: {event}\ndata: {data}\n\n".encode("utf-8")


def sse_data_only(payload: object) -> bytes:
    """Build one pinned-dialect data-only SSE frame (no ``event:`` line).

    The pinned gateway (f2df0e82) emits ``data: {json}\\n\\n`` frames; the
    event discriminator is the JSON ``type`` field, never an SSE event name.
    """
    return ("data: "
            + json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
            + "\n\n").encode("utf-8")


class RecordingServer:
    """One owned loopback HTTP server with a per-test scenario."""

    def __init__(self, scenario) -> None:
        self.state = ServerState()

        class ScenarioHandler(_BaseHandler):
            def do_POST(self) -> None:
                record = self._record()
                scenario(self, record)

        handler = ScenarioHandler
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._httpd.daemon_threads = True
        self._httpd.state = self.state  # type: ignore[attr-defined]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    # Forwarding helpers so tests can use the server object directly.
    @property
    def paths(self) -> list[str]:
        return self.state.paths

    def count(self, path: str) -> int:
        return self.state.count(path)

    def shutdown(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=5)


@pytest.fixture()
def server():
    """Factory fixture: start one owned loopback server per scenario."""

    started: list[RecordingServer] = []

    def _start(scenario) -> RecordingServer:
        srv = RecordingServer(scenario)
        started.append(srv)
        return srv

    yield _start

    for srv in started:
        srv.shutdown()


@pytest.fixture()
def closed_port():
    """An owned port that refuses connections (bind then release)."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port
