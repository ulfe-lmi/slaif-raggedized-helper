"""Bounded HTTP transport and SSE parsing for generator adapters (OAP 003-a).

Safety rules enforced here (architecture A13/A18/A20, V2-06, SECURITY S03/S04):

- only ``http``/``https`` destinations without embedded credentials;
- redirects are never followed (no implicit destination switches);
- one total deadline spans connect, write, headers and every body read:
  the exchange runs inside an async cancellation scope, so a stalled read
  late in the budget (or a slow trickle of bytes) still refuses at the
  absolute deadline and owned I/O is closed on expiry/cancellation;
  per-operation httpx timeouts stay finite as a secondary bound;
- ambient HTTP proxy environment is never inherited (``trust_env=False``);
- error messages carry status classes and safe type names only; provider
  response bodies are never echoed through exceptions or results.
"""

from __future__ import annotations

import asyncio
import codecs
import contextlib
import math
import queue
import threading
import time
from dataclasses import dataclass
from typing import Iterator
from urllib.parse import urlsplit

import httpx

DEFAULT_MAX_RESPONSE_BYTES = 2_000_000
DEFAULT_MAX_SSE_EVENT_BYTES = 262_144
DEFAULT_MAX_STREAM_BYTES = 16_000_000
_WORKER_JOIN_TIMEOUT = 2.0
_QUEUE_PUT_TIMEOUT = 0.2


class TransportError(Exception):
    """Safe transport failure; the message never contains provider body bytes."""

    retryable = False


class TransportConfigError(TransportError):
    """Local configuration/destination refusal (pre-dispatch, never retried)."""


class TransportRefusedError(TransportError):
    """The destination refused the request (HTTP 4xx, redirect, malformed wire)."""


class TransportConnectError(TransportError):
    """Pre-dispatch network failure before any response bytes (retryable)."""

    retryable = True


class TransportTimeoutError(TransportError):
    """A finite deadline or timeout expired; pre-dispatch timeouts are retryable."""

    def __init__(self, message: str, *, dispatched: bool) -> None:
        super().__init__(message)
        self.retryable = not dispatched


class TransportTruncatedError(TransportError):
    """A bounded size limit was exceeded (response body or single SSE event)."""


class TransportProtocolError(TransportError):
    """Wire-protocol violation (oversized line/event, invalid UTF-8).

    The stream is not a valid success; it is never retried and never
    treated as an ambiguous completion.
    """


def validate_destination_url(base_url: str) -> str:
    """Refuse destinations that embed credentials or are not plain http/https."""
    parts = urlsplit(base_url)
    if parts.scheme not in ("http", "https"):
        raise TransportConfigError("destination must use http or https")
    if parts.username is not None or parts.password is not None:
        raise TransportConfigError("credentials in the destination URL are forbidden (no userinfo)")
    if parts.query or parts.fragment:
        raise TransportConfigError("query/fragment strings in the destination URL are forbidden")
    if not parts.hostname:
        raise TransportConfigError("destination must contain a hostname")
    return base_url


def _map_httpx(exc: httpx.HTTPError, *, dispatched: bool) -> TransportError:
    if isinstance(exc, httpx.ConnectTimeout):
        return TransportTimeoutError("connect timeout before dispatch", dispatched=False)
    if isinstance(exc, httpx.ConnectError):
        return TransportConnectError("connection failed before dispatch")
    if isinstance(exc, httpx.TimeoutException):
        return TransportTimeoutError("deadline timeout", dispatched=dispatched)
    return TransportError(f"transport failure: {type(exc).__name__}")


@dataclass(frozen=True)
class SSEFrame:
    """One decoded server-sent-events frame (event name + joined data)."""

    event: str
    data: str


class SSEStream:
    """Incremental SSE parser over a bounded byte iterator.

    Handles split and coalesced frames, CRLF/LF line endings, multi-line
    ``data`` fields (joined with LF), comment lines and inert ``id``/``retry``
    fields. UTF-8 sequences split across chunk boundaries are reassembled.
    Unknown event names are delivered to the caller (the adapter decides they
    are never terminals). Raises on per-line/per-event/aggregate byte
    overflow, invalid UTF-8 or overall deadline exhaustion; an unterminated
    trailing frame or line at clean EOF is reported via
    :attr:`incomplete_trailing` without being emitted.
    """

    def __init__(
        self,
        chunks: Iterator[bytes],
        *,
        max_event_bytes: int,
        max_stream_bytes: int,
        deadline: float | None = None,
    ) -> None:
        if max_event_bytes <= 0 or max_stream_bytes <= 0:
            raise TransportConfigError("SSE byte bounds must be positive")
        self._chunks = chunks
        self._max_event_bytes = int(max_event_bytes)
        self._max_stream_bytes = int(max_stream_bytes)
        self._deadline = deadline
        self.incomplete_trailing = False

    def _next_chunk(self) -> bytes | None:
        if self._deadline is not None and time.monotonic() >= self._deadline:
            raise TransportTimeoutError("overall stream deadline exhausted", dispatched=True)
        try:
            chunk = next(self._chunks)
        except StopIteration:
            return None
        except TransportError:
            raise
        except Exception as exc:  # map any provider/stack error to a safe failure
            raise TransportError(f"stream read failure: {type(exc).__name__}") from exc
        if self._deadline is not None and time.monotonic() >= self._deadline:
            raise TransportTimeoutError("overall stream deadline exhausted", dispatched=True)
        return chunk

    def __iter__(self) -> Iterator[SSEFrame]:
        decoder = codecs.getincrementaldecoder("utf-8")()
        line_buffer = ""
        pending_event: str | None = None
        pending_data: list[str] = []
        pending_bytes = 0
        stream_bytes = 0
        max_line_bytes = self._max_event_bytes  # no valid line may exceed the event bound

        while True:
            chunk = self._next_chunk()
            eof = chunk is None
            try:
                if chunk is not None:
                    text = decoder.decode(chunk, eof)
                else:
                    text = decoder.decode(b"", True)
            except UnicodeDecodeError:
                raise TransportProtocolError("SSE stream is not valid UTF-8") from None
            if chunk is not None:
                stream_bytes += len(chunk)
                if stream_bytes > self._max_stream_bytes:
                    raise TransportTruncatedError("SSE stream exceeds aggregate byte bound")
            line_buffer += text
            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                if line.endswith("\"):
                    line = line[:-1]
                if len(line.encode("utf-8")) > max_line_bytes:
                    raise TransportTruncatedError("SSE line exceeds byte bound")
                if line == "":
                    if pending_data:
                        yield SSEFrame(
                            event=pending_event or "message",
                            data="\n".join(pending_data),
                        )
                    pending_event = None
                    pending_data = []
                    pending_bytes = 0
                    continue
                if line.startswith(":"):
                    continue  # comment (still line-bounded above)
                if ":" in line:
                    field, _, value = line.partition(":")
                    if value.startswith(" "):
                        value = value[1:]
                else:
                    field, value = line, ""
                if field == "event":
                    pending_event = value
                elif field == "data":
                    pending_data.append(value)
                    pending_bytes += len(value.encode("utf-8")) + 1
                    if pending_bytes > self._max_event_bytes:
                        raise TransportTruncatedError("SSE event exceeds byte bound")
                # "id", "retry" and unknown fields are inert for this contract.
            if len(line_buffer.encode("utf-8")) > max_line_bytes:
                raise TransportTruncatedError("SSE line exceeds byte bound")
            if eof:
                if line_buffer != "" or pending_data or pending_event is not None:
                    self.incomplete_trailing = True
                return


def _deadline_remaining(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return deadline - time.monotonic()


class _AsyncStreamHandle:
    """Bounded streaming POST owned by one worker thread and event loop.

    The exchange runs as an asyncio task; the total deadline is enforced by
    bounded queue reads on the consumer side plus task cancellation, which
    closes the owned connection. Pre-dispatch failures surface
    synchronously from ``start()``; post-dispatch conditions surface while
    iterating :meth:`frames`.
    """

    def __init__(
        self,
        base_url: str,
        path: str,
        body: bytes,
        *,
        timeout_seconds: float,
        api_key: str | None,
        max_sse_event_bytes: int,
        max_stream_bytes: int,
        deadline: float | None,
    ) -> None:
        self._base_url = base_url
        self._path = path
        self._body = body
        self._timeout_seconds = timeout_seconds
        self._api_key = api_key
        self._max_sse_event_bytes = int(max_sse_event_bytes)
        self._max_stream_bytes = int(max_stream_bytes)
        self._deadline = deadline
        self._queue: "queue.Queue[tuple[str, object]]" = queue.Queue(maxsize=32)
        self._cancel = threading.Event()
        self._lock = threading.Lock()
        self._dispatched = False
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None
        self.status_code: int | None = None
        self._closed = False

    # -- worker -----------------------------------------------------------
    def _worker(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        task = loop.create_task(self._exchange())
        self._task = task
        try:
            loop.run_until_complete(task)
        except BaseException:
            pass  # failures are reported through the queue
        finally:
            with contextlib.suppress(BaseException):
                loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            self._put(("closed", None))

    async def _exchange(self) -> None:
        headers = {"accept": "text/event-stream"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout_seconds, connect=self._timeout_seconds),
                follow_redirects=False,
                limits=httpx.Limits(max_connections=2, max_keepalive_connections=0),
                trust_env=False,
            ) as client:
                request = client.build_request(
                    "POST",
                    self._path,
                    content=self._body,
                    headers={"content-type": "application/json", **headers},
                )
                try:
                    response = await client.send(request, stream=True)
                except httpx.HTTPError as exc:
                    self._put(("error", self._map(exc, dispatched=False)))
                    return
                with self._lock:
                    self._dispatched = True
                try:
                    status = response.status_code
                    if 300 <= status < 400:
                        with contextlib.suppress(BaseException):
                            await response.aclose()
                        self._put(("error", TransportRefusedError(
                            f"redirect refused (HTTP {status})")))
                        return
                    if status >= 400:
                        # No raw error body is needed for a safe status class.
                        with contextlib.suppress(BaseException):
                            await response.aclose()
                        self._put(("error", TransportRefusedError(
                            f"request refused (HTTP {status})")))
                        return
                    self.status_code = status
                    self._put(("started", status))
                    raw = response.aiter_raw()
                    while True:
                        try:
                            chunk = await anext(raw)
                        except StopAsyncIteration:
                            break
                        if self._cancel.is_set():
                            raise TransportTimeoutError("overall deadline exhausted",
                                                        dispatched=True)
                        self._put_bounded(("chunk", chunk))
                except httpx.HTTPError as exc:
                    self._put(("error", self._map(exc, dispatched=True)))
                    return
                except TransportError as exc:
                    self._put(("error", exc))
                    return
                finally:
                    with contextlib.suppress(BaseException):
                        await response.aclose()
                self._put(("eof", None))
        except TransportError as exc:
            self._put(("error", exc))
        except httpx.HTTPError as exc:
            self._put(("error", self._map(exc, dispatched=True)))
        except Exception as exc:  # defensive: never crash the worker silently
            self._put(("error", TransportError(f"stream transport failure: {type(exc).__name__}")))

    @staticmethod
    def _map(exc: httpx.HTTPError, *, dispatched: bool) -> TransportError:
        return _map_httpx(exc, dispatched=dispatched)

    def _put(self, item: tuple[str, object]) -> None:
        with contextlib.suppress(queue.Full):
            self._queue.put_nowait(item)

    def _put_bounded(self, item: tuple[str, object]) -> None:
        # Backpressure with cancellation awareness: a stalled consumer must
        # not grow unbounded buffers, and cancellation must win the wait.
        while True:
            if self._cancel.is_set():
                raise TransportTimeoutError("overall deadline exhausted", dispatched=True)
            try:
                self._queue.put(item, timeout=_QUEUE_PUT_TIMEOUT)
                return
            except queue.Full:
                continue

    # -- lifecycle ----------------------------------------------------------
    def start(self) -> None:
        if self._deadline is not None and time.monotonic() >= self._deadline:
            raise TransportTimeoutError("deadline already expired before dispatch",
                                        dispatched=False)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        remaining = _deadline_remaining(self._deadline)
        try:
            kind, value = self._queue.get(
                timeout=remaining if remaining is not None and remaining > 0 else None
            )
        except queue.Empty:
            self._cancel_worker()
            with self._lock:
                dispatched = self._dispatched
            raise TransportTimeoutError(
                "overall deadline exhausted while waiting for response headers",
                dispatched=dispatched,
            ) from None
        if kind == "error":
            self._cancel_worker()
            assert isinstance(value, TransportError)
            raise value
        if kind != "started":
            self._cancel_worker()
            raise TransportError("stream worker reported an unexpected startup state")

    def _iter_chunks(self) -> Iterator[bytes]:
        while True:
            if self._cancel.is_set():
                raise TransportTimeoutError("overall deadline exhausted", dispatched=True)
            remaining = _deadline_remaining(self._deadline)
            if remaining is not None and remaining <= 0:
                self._cancel_worker()
                raise TransportTimeoutError("overall deadline exhausted", dispatched=True)
            try:
                kind, value = self._queue.get(
                    timeout=remaining if remaining is not None else None
                )
            except queue.Empty:
                self._cancel_worker()
                raise TransportTimeoutError("overall deadline exhausted", dispatched=True) from None
            if kind == "eof" or kind == "closed":
                return
            if kind == "error":
                assert isinstance(value, TransportError)
                raise value
            yield value  # kind == "chunk"
            if self._cancel.is_set():
                raise TransportTimeoutError("overall deadline exhausted", dispatched=True)

    def frames(self) -> SSEStream:
        return SSEStream(
            self._iter_chunks(),
            max_event_bytes=self._max_sse_event_bytes,
            max_stream_bytes=self._max_stream_bytes,
            deadline=self._deadline,
        )

    def _cancel_worker(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._cancel.set()
        loop, task = self._loop, self._task
        if loop is not None and task is not None and not task.done():
            with contextlib.suppress(BaseException):
                loop.call_soon_threadsafe(task.cancel)
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=_WORKER_JOIN_TIMEOUT)

    def close(self) -> None:
        self._cancel_worker()

    def __enter__(self) -> "_AsyncStreamHandle":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class GatewayTransport:
    """Bounded single-purpose HTTP transport for one configured base URL.

    Every request is one bounded POST under one total deadline. No
    redirects, no cookie jar, no connection reuse across calls, no ambient
    proxy inheritance.
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float,
        api_key: str | None = None,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        max_sse_event_bytes: int = DEFAULT_MAX_SSE_EVENT_BYTES,
        max_stream_bytes: int = DEFAULT_MAX_STREAM_BYTES,
    ) -> None:
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise TransportConfigError("timeout_seconds must be finite and positive")
        if max_response_bytes <= 0 or max_sse_event_bytes <= 0 or max_stream_bytes <= 0:
            raise TransportConfigError("response/stream byte bounds must be positive")
        self.base_url = validate_destination_url(base_url.rstrip("/"))
        self.timeout_seconds = float(timeout_seconds)
        self.api_key = api_key
        self.max_response_bytes = int(max_response_bytes)
        self.max_sse_event_bytes = int(max_sse_event_bytes)
        self.max_stream_bytes = int(max_stream_bytes)

    # -- non-streaming ------------------------------------------------------
    def post_json(
        self, path: str, body: bytes, *, deadline: float | None = None
    ) -> tuple[int, bytes]:
        """POST bounded JSON to ``path`` under one overall deadline.

        Returns ``(status, body)`` for any non-redirect status; the caller
        classifies 4xx/5xx. The total deadline spans connect, write,
        headers and every body read (enforced by an async cancellation
        scope); an already-expired deadline refuses before dispatch. The
        provider body is never included in an error message.
        """
        if deadline is not None and time.monotonic() >= deadline:
            raise TransportTimeoutError("deadline already expired before dispatch",
                                        dispatched=False)
        state = {"dispatched": False}
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["authorization"] = f"Bearer {self.api_key}"

        async def _exchange() -> tuple[int, bytes]:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout_seconds, connect=self.timeout_seconds),
                follow_redirects=False,
                headers=headers,
                limits=httpx.Limits(max_connections=2, max_keepalive_connections=0),
                trust_env=False,
            ) as client:
                async with client.stream(
                    "POST", path, content=body,
                    headers={"content-type": "application/json"},
                ) as response:
                    state["dispatched"] = True
                    status = response.status_code
                    if 300 <= status < 400:
                        raise TransportRefusedError(f"redirect refused (HTTP {status})")
                    payload = bytearray()
                    async for chunk in response.aiter_raw():
                        payload.extend(chunk)
                        if len(payload) > self.max_response_bytes:
                            raise TransportTruncatedError("response exceeds byte bound")
                    return status, bytes(payload)

        try:
            return _run_async(_exchange(), _deadline_remaining(deadline))
        except asyncio.TimeoutError:
            raise TransportTimeoutError("overall deadline exhausted",
                                        dispatched=state["dispatched"]) from None

    # -- streaming ----------------------------------------------------------
    def open_stream(
        self, path: str, body: bytes, *, deadline: float | None = None
    ) -> _AsyncStreamHandle:
        """Open one bounded streaming POST; the handle must be closed.

        Pre-dispatch failures (and an already-expired deadline) raise here;
        header/body failures surface while iterating the frames.
        """
        handle = _AsyncStreamHandle(
            self.base_url,
            path,
            body,
            timeout_seconds=self.timeout_seconds,
            api_key=self.api_key,
            max_sse_event_bytes=self.max_sse_event_bytes,
            max_stream_bytes=self.max_stream_bytes,
            deadline=deadline,
        )
        handle.start()
        return handle


def _run_async(coro, remaining: float | None):
    """Run one bounded async exchange on a fresh loop under a total deadline."""

    async def _bounded():
        if remaining is None:
            return await coro
        return await asyncio.wait_for(coro, timeout=remaining)

    return asyncio.run(_bounded())
