"""Wire-level evidence for precedence of a latched role failure."""
import hashlib
import inspect
import json
import textwrap
import time

import pytest

from conftest import sse_data_only
from test_gateway_generator import make_config, make_generator, make_request, valid_stream_frames
from slaif_raggedized_helper.config import RouteCapabilities
from slaif_raggedized_helper.model_clients import gateway, transport
from slaif_raggedized_helper.schema import CompletionOutcome


def run_wire(server, bad, *, timeout=False):
    frames = valid_stream_frames()
    if bad:
        item = json.loads(frames[5].split(b"data: ", 1)[1])
        item["item"]["role"] = "user"
        frames[5] = sse_data_only(item)

    def scenario(handler, request):
        handler._send_headers_only()
        for frame in frames[:6]:
            handler._write_stream(frame)
        if timeout:
            time.sleep(0.6)

    srv = server(scenario)
    config = make_config(f"{srv.url}/v1", RouteCapabilities(streaming=True),
                         timeout_seconds=0.2 if timeout else 2, max_retries=2)
    result = make_generator(config).generate(make_request(stream=True))
    assert len(srv.requests) == 1
    assert result.attempts == 1
    print(f"wire bad={bad} timeout={timeout} outcome={result.outcome} "
          f"text={result.text!r} error={result.error!r} calls={len(srv.requests)}")
    return result


def failed(result):
    assert result.outcome is CompletionOutcome.FAILED
    assert result.text is None
    assert result.error == "invalid message role"


def unknown(result):
    assert result.outcome is CompletionOutcome.UNKNOWN_COMPLETION
    assert result.text == "Hello world"


def test_actual_timeout_and_original_guard_control(server, monkeypatch):
    original = gateway.GatewayGenerator._run_stream
    source = textwrap.dedent(inspect.getsource(original))
    guard = ("    except TransportTimeoutError as exc:\n"
             "        if acc.state.error is not None:\n"
             "            return _finish_stream(acc, request, eof_incomplete=False,\n"
             "                                  backend_fingerprint=backend_fingerprint)\n")
    assert source.count(guard) == 1
    control = source.replace(guard, "    except TransportTimeoutError as exc:\n", 1)
    print("original source sha256", hashlib.sha256(source.encode()).hexdigest())
    print("control source sha256", hashlib.sha256(control.encode()).hexdigest())
    failed(run_wire(server, True, timeout=True))
    namespace = dict(gateway.__dict__)
    exec(compile(control, "<timeout-guard-control>", "exec"), namespace)
    with monkeypatch.context() as patch:
        patch.setattr(gateway.GatewayGenerator, "_run_stream", namespace["_run_stream"])
        unknown(run_wire(server, True, timeout=True))
    failed(run_wire(server, True, timeout=True))
    unknown(run_wire(server, False, timeout=True))


def test_generic_fault_after_real_frames(server, monkeypatch):
    original = transport._AsyncStreamHandle.frames

    def frames_with_fault(handle):
        real = original(handle)

        def iterator():
            for frame in real:
                yield frame
            raise transport.TransportError("controlled generic fault", dispatched=True)

        return iterator()

    monkeypatch.setattr(transport._AsyncStreamHandle, "frames", frames_with_fault)
    failed(run_wire(server, True))
    unknown(run_wire(server, False))


@pytest.mark.parametrize("error_type", [transport.TransportProtocolError,
                                      transport.TransportRefusedError])
def test_controlled_close_fault_after_real_drain(server, monkeypatch, error_type):
    original = transport._AsyncStreamHandle.__exit__
    closes = []

    def exit_with_fault(handle, *args):
        original(handle, *args)
        closes.append(1)
        raise error_type("controlled late close fault")

    monkeypatch.setattr(transport._AsyncStreamHandle, "__exit__", exit_with_fault)
    failed(run_wire(server, True))
    assert closes == [1]
