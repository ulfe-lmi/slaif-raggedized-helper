# Private raw snapshot DATA selection

`parse_pointer` accepts only the closed canonical pointer. `read_selected_data` reads the current pointer and freshly validates its source-backed DATA under a shared snapshots-directory lock. `compare_and_select_data` validates the current and candidate DATA under the exclusive lock and compares the exact previously read pointer bytes. Pass `None` only for bootstrap. Every successful selection advances the generation, including selection of the same snapshot or rollback.

A `SelectionError` carries `selection_may_have_changed`; after an attempted replacement, read again to reconcile. A stale expectation must be refreshed explicitly. The APIs borrow their stores and return detached immutable DATA, not a retained request handle. They do not establish READY, authorization, current policy, query compatibility, retention or GC safety. Future GC must participate in the same lock domain. Cooperative deadlines do not preempt source operations. Atomic replacement does not establish power-loss durability on arbitrary filesystems or protection against arbitrary same-UID interference.

Root clarification SHA256: `7d9a9751c4b2d2f3666eebe6ea68d0a3f7c8b67bc16c2d1b3cd0e42ec1de07fc`

# Root clarification: cooperative DATA selection deadline

Status: FINAL D0 CLARIFICATION
Applies only to PAR-008-SELECTION-A and contracts/raw-snapshot-selection-v1.md.
E: actual unchanged raw_snapshot_directory.load_directory accepts no caller deadline and _load
has its own cooperative 60-second timer. Root inspected those exact functions. No predecessor
API/source change is needed or authorized.

The selection operation checks its one original absolute caller deadline immediately before
and immediately after every actual unchanged load_directory call, and throughout its own
lock waits and bounded pointer I/O. It never resets the caller deadline or returns successful
DATA after the caller deadline expires. This is cooperative accounting, not a hard or inherited
inner-call wall timeout. An in-progress loader can exceed the caller's smaller remaining budget
before returning/refusing, subject to its own existing cooperative 60-second checks; filesystem
calls are not preempted. State this limit plainly in API documentation and error/ambiguity
accounting. No signal/thread cancellation, private validator monkeypatch, fake loader, mode
reservation, extra native process or callback is an alternative authority/timeout mechanism.

Keep original Root design bytes/order unchanged. In the already allowed API document append
this exact clarification text and its SHA256 citation; no new committed path/scope snapshot or
reader replay. Add one meaningful actual-loader boundary test: real loader completes under
controlled wrapper timing, caller elapsed budget expires, selection refuses after real source
validation without a success or pointer mutation; do not replace validation with fake success.
Normal source/FS/CAS tests continue under original caps. Record the original ambiguity and
clarification in report; supersede unsupported BLOCKED state with actual same-lane progress.
DHA NONE. No READY/request deadline guarantee, serving API or current-policy/qualification grant.
