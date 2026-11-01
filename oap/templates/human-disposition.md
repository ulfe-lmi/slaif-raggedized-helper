# Human disposition template — not an approval

An agent may prepare facts; only the human makes and authenticates the disposition. Allowed
decisions: ACCEPTED, REJECTED, CHANGE REQUIRED, DEFERRED. Latest attributable ACCEPTED applies
only to its exact entry/gate. Merely writing a human name in Markdown is not authentication.

For mechanical verification, an external human signing key signs a JSON statement containing
repository, critical_id, entry_sha256, gate, decision, authority, recorded_at, conditions and
evidence. Use SSH detached signatures with namespace `slaif-oap-dha`. The trusted signer file
is configured by the human outside the repository; agents cannot self-enroll keys or sign.
`verify_human_disposition.py` verifies and stores evidence under oap/adjudications; no private
signing material belongs in either workspace. Without configured trusted human signers, gate
state is UNVERIFIED/BLOCKING. Direct human instructions remain authoritative; their actual
recorded source and scope must never be fabricated by an agent.
