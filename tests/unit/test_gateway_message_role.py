"""Role admission through the real collector and stream accumulator."""
import json

import pytest

from slaif_raggedized_helper.model_clients.gateway import _GatewayAccumulator, _collect_output
from slaif_raggedized_helper.model_clients.transport import SSEFrame


def item(role="assistant", status="completed"):
    return {"id": "m", "type": "message", "role": role, "status": status,
            "content": [{"type": "output_text", "text": "ok"}]}


@pytest.mark.parametrize("role", [None, False, 1, [], {}, "user", "system", "developer",
                                   "tool", "Assistant", "assistant ", "ROLE-CANARY"])
def test_collector_rejects_roles_without_reflection(role):
    obj = item(role)
    texts, refusal, error = _collect_output([obj])
    assert texts == [] and refusal is None and error == "invalid message role"
    del obj["role"]
    assert _collect_output([obj])[2] == "invalid message role"


def test_collector_reasoning_and_refusal():
    reasoning = {"id": "r", "type": "reasoning", "status": "completed"}
    assert _collect_output([reasoning, item()]) == (["ok"], None, None)
    refusal = item(status="refusal")
    refusal["content"] = [{"type": "refusal", "refusal": "content_filter"}]
    assert _collect_output([refusal])[1] == "content_filter"
    refusal["role"] = "user"
    assert _collect_output([refusal])[2] == "invalid message role"


@pytest.mark.parametrize("boundary", ["added", "done"])
def test_stream_latches_bad_role(boundary):
    acc = _GatewayAccumulator()
    added = {"type": "response.output_item.added", "output_index": 0,
             "item": {"id": "m", "type": "message", "role": "assistant"}}
    done = {"type": "response.output_item.done", "output_index": 0, "item": item()}
    (added if boundary == "added" else done)["item"]["role"] = {"canary": "secret"}
    for payload in (added, done):
        acc.handle(SSEFrame(event="message", data=json.dumps(payload)))
    assert acc.state.error == "invalid message role"
