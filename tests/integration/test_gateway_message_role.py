"""Owned HTTP/SSE proof of role enforcement and its causal control."""
import json

import pytest

from conftest import sse_data_only
from test_gateway_generator import (completed_json, make_config, make_generator,
                                    make_request, message_item, reasoning_item,
                                    stream_scenario, valid_stream_frames)
from slaif_raggedized_helper.config import RouteCapabilities
from slaif_raggedized_helper.model_clients import gateway
from slaif_raggedized_helper.schema import CompletionOutcome

CANARY = "ROLE-PRIVATE-CANARY"
MISSING = object()


def set_role(item, role):
    if role is MISSING:
        item.pop("role", None)
    else:
        item["role"] = role


def check(result, outcome):
    assert result.outcome is outcome
    assert CANARY not in str(result)
    if outcome is CompletionOutcome.FAILED:
        assert result.text is None
        assert result.error == "invalid message role"


def send_json(server, output):
    srv = server(lambda h, r: h._send_json(200, completed_json(output)))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert len(srv.requests) == 1
    assert json.loads(srv.requests[0].body)["input"][0]["role"] == "user"
    return result


def send_stream(server, frames):
    srv = server(stream_scenario(frames))
    config = make_config(f"{srv.url}/v1", RouteCapabilities(streaming=True))
    result = make_generator(config).generate(make_request(stream=True))
    assert len(srv.requests) == 1
    return result


@pytest.mark.parametrize("role", [MISSING, None, False, 5, [], {}, "user", CANARY])
def test_json_bad_role(server, role):
    msg = message_item("m", "answer")
    set_role(msg, role)
    check(send_json(server, [msg]), CompletionOutcome.FAILED)


def test_json_compatibility(server):
    check(send_json(server, [reasoning_item("r"), message_item("a", "alpha"),
                             message_item("b", "beta")]), CompletionOutcome.TERMINAL)
    refusal = message_item("m", "", status="refusal")
    check(send_json(server, [refusal]), CompletionOutcome.REFUSAL)
    refusal["role"] = "user"
    check(send_json(server, [refusal]), CompletionOutcome.FAILED)


@pytest.mark.parametrize("boundary", ["added", "done", "final", "final-only"])
def test_stream_boundaries_cannot_salvage(server, boundary):
    frames = valid_stream_frames()
    if boundary == "final-only":
        frames = [frames[0], frames[-1]]
        index = 1
    else:
        index = {"added": 1, "done": 5, "final": 6}[boundary]
    payload = json.loads(frames[index].split(b"data: ", 1)[1])
    target = payload["response"]["output"][0] if boundary.startswith("final") else payload["item"]
    set_role(target, CANARY if boundary == "added" else "user")
    frames[index] = sse_data_only(payload)
    check(send_stream(server, frames), CompletionOutcome.FAILED)


def test_stream_assistant_baseline(server):
    result = send_stream(server, valid_stream_frames())
    check(result, CompletionOutcome.TERMINAL)
    assert result.text == "Hello world"


def test_original_guard_causal_control(server, monkeypatch):
    bad = message_item("m", "answer", role="user")
    good = message_item("m", "answer")
    check(send_json(server, [good]), CompletionOutcome.TERMINAL)
    check(send_json(server, [bad]), CompletionOutcome.FAILED)
    with monkeypatch.context() as patch:
        patch.setattr(gateway, "_valid_message_role", lambda item: True)
        admitted = send_json(server, [bad])
        check(admitted, CompletionOutcome.TERMINAL)
        assert admitted.text == "answer"
    check(send_json(server, [bad]), CompletionOutcome.FAILED)
    check(send_json(server, [good]), CompletionOutcome.TERMINAL)
