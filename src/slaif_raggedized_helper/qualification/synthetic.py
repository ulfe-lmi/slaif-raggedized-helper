"""Owned deterministic loopback fixtures for the explicit ``--synthetic``
trial route (OAP objective 004-a).

The synthetic route is reachable ONLY through the explicit CLI opt-in
(``raggedized qualification run --synthetic``). It starts an owned,
disposable 127.0.0.1 loopback server with a deterministic scenario for
the pinned gateway (``/v1/responses``) or native (``/apply-template`` +
``/completion``) dialect, points the REAL adapters/transport at it and
shuts it down when the trial returns. Evidence from this route is
labeled ``evidence_class: MOCK`` and ``target_type:
synthetic-owned-fixture``; it is never a real target, hardware, model,
cache or quality proof.

A configured URL (loopback or not) is NEVER classified synthetic by a
boolean: only this explicit route, which actually starts the owned
fixture, carries synthetic provenance.

No external network, product services, real keys, GPU or model
downloads; the synthetic canary key is unique to this suite and is not a
credential.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SYNTHETIC_API_KEY = "sk-synthetic-trial-004a-canary"
FIXTURE_ENDPOINT_IDENTITY = "synthetic-owned-fixture"


class SyntheticTrialServer:
    """One owned deterministic loopback fixture server (per backend)."""

    def __init__(self, backend: str) -> None:
        if backend not in ("gateway", "direct"):
            raise ValueError("backend must be gateway or direct")
        self._backend = backend
        self._lock = threading.Lock()
        self._responses = 0
        self._completions = 0
        self.requests: list[str] = []

        def scenario(h: "_SyntheticHandler", record_path: str) -> None:
            body_len = int(h.headers.get("content-length") or 0)
            body = h.rfile.read(body_len) if body_len else b""
            with self._lock:
                self.requests.append(record_path)
                if record_path == "/v1/responses":
                    self._responses += 1
                    n = self._responses
                elif record_path == "/completion":
                    self._completions += 1
                    n = self._completions
                else:
                    n = 0
            if record_path == "/v1/responses":
                h._send_gateway_completed(n)
            elif record_path == "/apply-template":
                doc = json.loads(body.decode("utf-8"))
                messages = doc.get("messages") or []
                last_user = ""
                for message in messages:
                    if message.get("role") == "user":
                        last_user = str(message.get("content") or "")
                h._send_json(200, {"prompt": "synthetic-rendered::" + last_user})
            elif record_path == "/completion":
                h._send_native_completed(n)
            else:
                h._send_json(404, {"error": "unknown fixture path"})

        class _SyntheticHandler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args) -> None:  # silence request logging
                pass

            def _send_json(self, status: int, doc: object) -> None:
                payload = json.dumps(doc).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)

            def _send_gateway_completed(self, n: int) -> None:
                # Pinned gateway final-dialect completed shape (f2df0e82):
                # array-ordered message item, output_text part, bounded
                # deterministic usage. Deterministic by call index.
                doc = {
                    "id": "resp_synthetic_trial_1",
                    "object": "response",
                    "created_at": 123,
                    "status": "completed",
                    "model": "synthetic-trial",
                    "output": [
                        {
                            "id": "msg_synthetic_trial",
                            "type": "message",
                            "status": "completed",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": f"synthetic-trial-terminal-{n}",
                                    "annotations": [],
                                    "logprobs": None,
                                }
                            ],
                            "phase": None,
                        }
                    ],
                    "usage": {"input_tokens": 12, "output_tokens": 3},
                }
                self._send_json(200, doc)

            def _send_native_completed(self, n: int) -> None:
                # Pinned native final-dialect stopped terminal (eos) with
                # consistent dialect accounting (tokens_evaluated ==
                # prompt_n + cache_n) and deterministic reported timings.
                doc = {
                    "content": f"synthetic-trial-native-terminal-{n}",
                    "stop": True,
                    "truncated": False,
                    "stop_type": "eos",
                    "tokens_evaluated": 12,
                    "tokens_predicted": 3,
                    "timings": {
                        "prompt_ms": 12.0,
                        "predicted_ms": 24.0,
                        "prompt_n": 12,
                        "cache_n": 0,
                        "predicted_n": 3,
                    },
                }
                self._send_json(200, doc)

            def do_POST(self) -> None:  # noqa: N802 (http.server API)
                scenario(self, self.path)

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _SyntheticHandler)
        self._httpd.daemon_threads = True
        self._thread = threading.Thread(target=self._httpd.serve_forever,
                                        daemon=True)
        self._thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    @property
    def gateway_base_url(self) -> str:
        # The pinned v1-responses contract base is the root plus /v1.
        return self.url + "/v1"

    @property
    def native_base_url(self) -> str:
        return self.url

    def shutdown(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=5)
