# Root amendment 2 to active007-l — correct causal-check expectation

Status: FINAL, same context/goal/PR9/007-l/sole wrapper. DHA NONE.
Preserve amendment1 and all historical bytes. This overrides ONLY its sentence asking a
single size-predicate bypass to permit the same reported-oversize fixture through the full
predictor. All production source/limits/other22files/CI and scope boundaries remain EXACT.

Root instruction was overconstrained: identity._read compares actual bytes read with the
same before.st_size AFTER the initial before.st_size > limit guard. With a narrow fstat seam
reporting an oversized size for an actual small owned file, removing ONLY the first guard
still correctly fails the later size-consistency check. No production/test guard may be
removed or globally mocked to force a positive control. This is Root instruction error,
not an implementation defect, permission problem or reason to redesign the size guard.

Required meaningful evidence: actual public predictor refuses the designated own small file
whose exact fstat device/inode boundary reports MAX_FILE+1, BEFORE any read of that file.
Record/spy os.read only for this actual descriptor, delegating all operations to originals.
Unmodified fixture with actual fstat must still predict successfully. The optional owned
temporary one-guard-omission control should demonstrate that the actual file IS read once
that initial guard is omitted, THEN still refuses at the intact consistency guard. It must
NOT claim full admission of inconsistent stat data. This precisely tests early rejection.
The ordinary corrected unit need not carry a large redundant source-mutation control if
an isolated retained witness documents that distinction. No oversized actual file creation,
raised/reset resource cap, skip/xfail, whole-reader fake or product modification.

Commit both exact Root amendments and original failure record under corresponding
oap/reviews filenames before the test correction. If amendment1 record commit already
exists, append amendment2 in a new record commit; never rewrite pushed history. Existing
original order/index/transcript remain preserved. Corrected file hash/size and explicit
unit-only exception in final docs/report; all required new implementation/report CI gates
and independent Root review remain unchanged. No FIFO read/replay/new reader/client reset.
