# Installed parity commands

`raggedized parity embedding --input FILE --output FILE` and
`raggedized parity rerank --input FILE --output FILE` route to the existing
operator-local parity module. The required paths are the explicit opt-in; no
additional consent flag is used. Input contains supplied vectors or scores,
not model execution. Evidence includes the exact input file SHA-256 and byte
count, analyzer input binding, `SUPPLIED_UNVERIFIED` and real qualification
`NOT_RUN`.

The delegated module returns 0 for success, 2 for safe pre-analysis refusal,
and 3 for post-analysis export failure, with computed evidence on stdout
when it can be serialized within the bound. Input and output default to 16 MiB,
with additional structural and analyzer limits. Export trusts operator-chosen
parents and hard links, and is neither atomic nor durable. These commands do
not qualify a model, GPU, target, corpus, license or production deployment.
