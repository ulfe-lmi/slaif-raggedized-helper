# Gateway stream failure precedence

When the stream accumulator has established a structural protocol error, a subsequent transport exception resolves through the existing error-first stream terminal path. The client returns FAILED with no text and the original fixed structural error. This applies to connection, timeout, refusal, protocol/truncation, and generic transport exits. It does not retry a known structural error. Attempt and available usage accounting follow the existing terminal path.

Without a latched structural error, existing transport behavior remains: genuine pre-dispatch connection and timeout errors retain their retry policy; post-dispatch timeout and generic interruptions retain UNKNOWN_COMPLETION and valid partial text; provider refusal and transport protocol errors retain their existing failure classification.

FAILED means the client cannot return a trusted answer after a known protocol violation. It does not establish whether the provider ran, completed or cancelled the request, whether it billed the request, or whether any device is free. No quota authority is inferred.

The local evidence uses synthetic messages and an owned loopback HTTP/SSE server, with controlled injected exceptions explicitly distinguished from the actual read timeout. It does not qualify a live gateway, model, hardware, latency, deployment, privacy posture, or upstream accounting. Provider data and credentials are not used in this proof.
