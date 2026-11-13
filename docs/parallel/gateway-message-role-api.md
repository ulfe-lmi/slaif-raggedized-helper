# Gateway output message role

Supported output items of type `message` require a string role exactly `assistant` in completed JSON output, the final completed SSE output, and streamed item-added and item-done boundaries. Missing, malformed, or different roles fail the request without answer text; the fixed error does not include the supplied role. A failure at an early boundary remains latched. This also applies to refusals. Reasoning items do not require a role, and request input roles remain unchanged.

This is a software protocol check for the pinned dialect. It does not establish qualification of a deployed gateway, model, license, security controls, hardware, or MVP. HTTP status, headers, and content type remain under existing policy and outside this correction.
