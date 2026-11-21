# Gold binding coverage follow-up

The peer audit identified missing focused unit coverage for an irrelevant extra bundle and for a missing gold atom. The unit test uses the real dataset parser and UTF-8 span hashes, with a stubbed lower load and typed stores. It checks the irrelevant bundle is loaded before refusal and a relevant-only control returns. Separately, a bundle matches one of two declared atoms before missing membership is refused; a two-bundle control returns. These stubs establish guard behavior only, not original-source evidence. Removing the corresponding guard would allow each negative input to return, as the controls and exact calls demonstrate.

The A original-source evidence remains as recorded in its report. PDF, current rights, quality, CI, independent acceptance and MVP qualification remain outside this unit evidence.
