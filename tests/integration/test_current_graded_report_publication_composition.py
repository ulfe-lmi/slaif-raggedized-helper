"""Guarded current graded report publication composition proof.

Offline synthetic fixtures only: every root is a private temporary
directory owned by the test and every byte is generated here.  Each
node reuses the existing real successful h1/h4 a/c grade producer of
``test_current_graded_cohort_composition`` (the same physical raw pin
with b genuinely withheld, the exact synthetic policy wire, the fresh
current admission after the expensive fixture setup, and the private
immutable owner-bound owning result minted by the genuine grade final
cut) to build one exact genuine earlier current graded result, then
exercises the actual fixed private product entry
``private_report_publication._publish_current`` over a distinct trusted
private report destination.  The entry reuses the owned admitted-
content report transaction's actual unnamed O_TMPFILE staging, held
directory-inode writer lock, exact-existing verification, single
no-replace install, held-fd checks, flushing and cleanup with its two
genuine short live guarded cuts and the separate after-cleanup
release cut.  The report writer's actual slot is identified by the
verified root inode at the real writer-lock boundary, and only that
slot's genuine successful cleanup result and later pool retirement
mark the report transaction-completion evidence, so the nested
genuine selected-policy writer I/O (the same-wire generation
publication through the attributed fixture) is distinguished from
report I/O; report payload writes are attributed only while the
written fd is still the actual captured staging inode (a reused fd
number never counts) and report link attempts to the actual procfs
magic-link of the captured staging fd, verified live, into the report
destination identity; the genuine generation changes are published on
real product events - the actual pre-write cut with the genuinely
owned staging fd and zero prior payload bytes, the actual successful
prelink validation bound to the exact report stage and live inode, and
the actual retired-slot post-cleanup moment - with no ordinal read
count and no simulated authority return triggering a witness.  No
local native witness execution: only the configured hosted CI
executes the three real hosted nodes, and local proof of this module
is collection only.
"""
import os
import stat
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))

from slaif_raggedized_helper import cpu_embedding_worker as cpu  # noqa: E402
from slaif_raggedized_helper import evaluation_program as program  # noqa: E402
from slaif_raggedized_helper import private_policy_pin_eligibility as pin_eligibility  # noqa: E402
from slaif_raggedized_helper import private_policy_request as ppr  # noqa: E402
from slaif_raggedized_helper import private_report_publication as publisher  # noqa: E402
from slaif_raggedized_helper import text_evaluation_dataset  # noqa: E402
import test_current_cohort_encoder_producer_composition as producer_fixture  # noqa: E402
import test_current_gold_dispatch_composition as gold_fixture  # noqa: E402
import test_current_grade_catalog_composition as grade_fixture  # noqa: E402
import test_current_graded_cohort_composition as graded_test  # noqa: E402
import test_guarded_encoder_transport_composition as transport  # noqa: E402


def _close_acquired(ctx, owner, encoder, *, failure=None):
    # One small fixture-local teardown: attempts every actually
    # acquired owner in fixed order - the raw owner, the derived and
    # originals stores, then the encoder, latching the first
    # non-Exception (including a primary that was already
    # non-Exception) and the first ordinary close fault while
    # continuing through ALL close calls, then propagating the first
    # non-Exception if present, otherwise the primary failure,
    # otherwise the first ordinary close fault.  No exception context
    # is mutated manually: a non-Exception primary keeps its original
    # identity across every close attempt, an ordinary primary is
    # preserved over ordinary close faults, and a close interruption
    # after an ordinary failure keeps the cancellation priority.
    # Before the handoff has returned the raw custody, the only owner
    # this teardown has been passed is the entered encoder, so its
    # close is the single attempt.
    first_interrupt = None
    first_ordinary = None
    if failure is not None and not isinstance(failure, Exception):
        first_interrupt = failure
    if ctx is None or owner is None:
        closes = (encoder.close,)
    else:
        closes = (
            owner.close,
            ctx.derived.close,
            ctx.originals.close,
            encoder.close,
        )
    for close in closes:
        try:
            close()
        except BaseException as exc:
            if not isinstance(exc, Exception):
                if first_interrupt is None:
                    first_interrupt = exc
                continue
            if first_ordinary is None:
                first_ordinary = exc
    if first_interrupt is not None:
        raise first_interrupt
    if failure is not None:
        raise failure
    if first_ordinary is not None:
        raise first_ordinary


def _synthetic_teardown_check():
    # The pure synthetic close-method check of the exact fixture-local
    # teardown body, run as one separate local proof against the
    # exact module functions - no native resource, no I/O, no
    # monkeypatch, no module import-time execution and no hosted
    # node: with only synthetic closeables it proves that every
    # actually acquired owner is attempted exactly once in fixed
    # order and that the propagated identity is the first
    # non-Exception (an early close fault, a later close fault after
    # an early ordinary close, or an already-non-Exception primary),
    # otherwise the primary failure, otherwise the first ordinary
    # close fault; the all-clean path returns normally; and the
    # producer-handoff and returned-custody failure paths close the
    # entered encoder exactly once before the primary or the first
    # interruption propagates.
    class _closeable:
        def __init__(self, fault=None):
            self.calls = 0
            self.fault = fault

        def close(self):
            self.calls += 1
            if self.fault is not None:
                raise self.fault

    def _ctx(derived, originals):
        return type("ctx", (), {"derived": derived, "originals": originals})

    # 1) An early non-Exception close fault after a clean start.
    owner1 = _closeable(KeyboardInterrupt())
    derived1, originals1, encoder1 = _closeable(), _closeable(), _closeable()
    with pytest.raises(KeyboardInterrupt) as caught1:
        _close_acquired(_ctx(derived1, originals1), owner1, encoder1)
    assert caught1.value is owner1.fault
    for closeable in (owner1, derived1, originals1, encoder1):
        assert closeable.calls == 1
    # 2) An already-non-Exception primary plus a later ordinary close
    #    fault: the primary keeps its identity.
    primary2 = KeyboardInterrupt()
    owner2, originals2, encoder2 = _closeable(), _closeable(), _closeable()
    derived2 = _closeable(OSError("derived close fault"))
    with pytest.raises(KeyboardInterrupt) as caught2:
        _close_acquired(_ctx(derived2, originals2), owner2, encoder2,
                        failure=primary2)
    assert caught2.value is primary2
    for closeable in (owner2, derived2, originals2, encoder2):
        assert closeable.calls == 1
    # 3) An early ordinary close fault plus a later non-Exception
    #    close fault: the non-Exception keeps its priority.
    owner3 = _closeable(OSError("early ordinary close fault"))
    derived3, originals3 = _closeable(), _closeable()
    encoder3 = _closeable(GeneratorExit())
    with pytest.raises(GeneratorExit) as caught3:
        _close_acquired(_ctx(derived3, originals3), owner3, encoder3)
    assert caught3.value is encoder3.fault
    for closeable in (owner3, derived3, originals3, encoder3):
        assert closeable.calls == 1
    # 4) An ordinary primary plus ordinary close faults on every
    #    closeable: the primary is preserved.
    primary4 = AssertionError("primary")
    owner4 = _closeable(ValueError("owner close fault"))
    derived4 = _closeable(ValueError("derived close fault"))
    originals4 = _closeable()
    encoder4 = _closeable(ValueError("encoder close fault"))
    with pytest.raises(AssertionError) as caught4:
        _close_acquired(_ctx(derived4, originals4), owner4, encoder4,
                        failure=primary4)
    assert caught4.value is primary4
    for closeable in (owner4, derived4, originals4, encoder4):
        assert closeable.calls == 1
    # 5) Every closeable clean and no primary: the teardown returns
    #    normally after attempting every close exactly once.
    owner5, derived5, originals5, encoder5 = (_closeable(), _closeable(),
                                              _closeable(), _closeable())
    assert _close_acquired(_ctx(derived5, originals5), owner5,
                           encoder5) is None
    for closeable in (owner5, derived5, originals5, encoder5):
        assert closeable.calls == 1
    # 6) The producer-handoff failure path: the producer has not yet
    #    returned custody, so the only owner attempted is the
    #    entered encoder, closed exactly once before the primary
    #    propagates.
    primary6 = RuntimeError("producer-handoff primary")
    encoder6 = _closeable()
    with pytest.raises(RuntimeError) as caught6:
        _close_acquired(None, None, encoder6, failure=primary6)
    assert caught6.value is primary6
    assert encoder6.calls == 1
    # 7) The returned-custody failure path: every actually acquired
    #    owner is attempted exactly once and the primary propagates.
    primary7 = RuntimeError("returned-custody primary")
    owner7, derived7, originals7 = _closeable(), _closeable(), _closeable()
    encoder7 = _closeable()
    with pytest.raises(RuntimeError) as caught7:
        _close_acquired(_ctx(derived7, originals7), owner7, encoder7,
                        failure=primary7)
    assert caught7.value is primary7
    for closeable in (owner7, derived7, originals7, encoder7):
        assert closeable.calls == 1
    # 8) Pre-handoff: an ordinary encoder close fault after a
    #    non-Exception primary keeps the primary identity.
    primary8 = KeyboardInterrupt()
    encoder8 = _closeable(ValueError("ordinary encoder close fault"))
    with pytest.raises(KeyboardInterrupt) as caught8:
        _close_acquired(None, None, encoder8, failure=primary8)
    assert caught8.value is primary8
    assert encoder8.calls == 1
    # 9) Pre-handoff: a non-Exception encoder close fault after an
    #    ordinary primary keeps the first interruption.
    primary9 = RuntimeError("ordinary primary")
    encoder9 = _closeable(GeneratorExit())
    with pytest.raises(GeneratorExit) as caught9:
        _close_acquired(None, None, encoder9, failure=primary9)
    assert caught9.value is encoder9.fault
    assert encoder9.calls == 1


def _fixture(tmp_path, monkeypatch, sc, expected, ctx, dataset,
             bundle_ids, owner, policy_root, reader, payload):
    """The real hosted scenario of the shared producer: the actual raw
    snapshot selector and the real ``PinOwner.acquire_selected_data``
    build the pinned data over the same physical raw pin with b
    genuinely withheld; the exact synthetic policy wire is installed
    through the attributed fixture; the fresh current admission is
    created only after the expensive fixture setup; the owner's exact
    saved end is the controlled prior end retained for every custody
    assertion.  The raw custody is already owned by the single
    ``_scenario`` acquisition handoff, whose failure teardown is the
    only cleanup path for the objects it returned."""
    a, c, _b = ctx.chunk_ids
    chunks = {"a": a, "c": c, "b": _b}
    dataset_ac, declared, member_b = graded_test._projected_declaration(
        owner, dataset, bundle_ids)
    admitted_ac = text_evaluation_dataset.admit(dataset_ac)
    assert admitted_ac.case_count == 5
    assert admitted_ac.gold_atom_count == 6
    # The real b withholding on the same live capture: the declared
    # Gold IDs omit b, while the same physical raw pin held by the
    # owner still contains b's bundle and revision/extraction span.
    assert len(declared) == 2
    b_id = next(ident for ident in bundle_ids if ident not in declared)
    assert member_b.bundle_container_id == b_id
    held_rows = {
        (r.bundle_container_id, r.batch_container_id)
        for r in owner.value.data.row_map.rows}
    assert (b_id, member_b.batch_container_id) in held_rows
    assert member_b.revision_id
    ctx.pointer_generation = owner.value.pointer.generation
    held = owner.value
    prior_end = time.monotonic() - 60.0
    owner.op.end = prior_end
    admission = ppr.request_current_view(reader, gold_fixture.CREDENTIAL,
                                         deadline_ms=30000)
    policy_snapshot = pin_eligibility._isolated_policy_snapshot(admission)
    anchor = pin_eligibility._bounded_admission(
        pin_eligibility._admitted_principal_grants(
            policy_snapshot, admission.principal_id))
    full_grants = pin_eligibility._bound_grants(admission, anchor)
    wire = grade_fixture._plan_wire(ctx, admitted_ac, ctx.catalog_id,
                                    (("h1", ((chunks["a"], 3),)),
                                     ("h4", ())),)
    return {
        "ctx": ctx, "owner": owner, "reader": reader,
        "policy_root": policy_root, "payload": payload,
        "admission": admission, "anchor": anchor,
        "full_grants": full_grants,
        "wire": wire, "dataset_ac": dataset_ac, "declared": declared,
        "held": held, "prior_end": prior_end, "expected": expected,
        "encoder": sc["encoder"],
    }


def _owning_result(state, monkeypatch):
    """One real successful current graded production under the actual
    production counters: the exact same physical raw pin with b
    genuinely withheld, the h1/h4 a/c projection, and the private
    immutable owner-bound owning result minted by the genuine grade
    final cut, with the real trace (twenty-one actual full pin loads
    and seventy-five actual raw directory starts and completions)."""
    counts = producer_fixture._counts()
    restore = producer_fixture._install_counting(
        monkeypatch, state["ctx"], state["owner"], state["reader"], counts)
    dir_counts = producer_fixture._directory_counts(monkeypatch)
    try:
        report = graded_test._graded_cohort(
            state["admission"], state["owner"], state["dataset_ac"],
            state["wire"], ("h1", "h4"), (state["expected"],
                                          state["expected"]),
            state["declared"], state["encoder"])
    finally:
        restore()
    assert type(report) is program._OwningGradeReport
    assert report.owner is state["owner"]
    assert report.admission is state["admission"]
    assert report.capture is state["held"]
    assert report.original_op is state["owner"].op
    assert report.grants == state["full_grants"]
    assert report.anchor == state["anchor"]
    assert counts["pin_load"] == 21
    assert dir_counts == {"start": 75, "done": 75}
    return report


def _assert_restored(owner, held, prior_end, report):
    # The real ownership checks: the retained active owner, the exact
    # saved end restored on the original operation, the independently
    # released guard and the same raw capture.
    assert owner.state == "ACTIVE"
    assert owner.value is held
    assert owner.op is report.original_op
    assert owner.originals is report.originals
    assert owner.derived is report.derived
    assert owner.op.end == prior_end
    assert not owner.guard.locked()


class _io_witness:
    """Real I/O attribution by the actual held fd, live inode identity
    and report destination.

    The report writer's actual slot is identified by the verified root
    inode at the real writer-lock boundary; only that slot's genuine
    successful cleanup result and later pool retirement mark the
    report transaction-completion evidence, so a nested genuine
    selected-policy writer entering the same shared transaction can
    never be marked as the report transaction.  Report payload writes
    count only while the written fd is still the actual captured
    staging inode (dev/ino), so a reused fd number - including one the
    nested genuine selected-policy writer may take after the report
    fds close - never counts as report I/O; report link attempts are
    the actual procfs magic-link of the captured staging fd, verified
    live, into the report destination identity.  The per-attempt
    captured fds (the staging fd and the held final-verification fd)
    together with the identified-slot cleanup-complete and retired-slot
    events give the transaction-completion evidence for the separate
    after-cleanup release check, which the closed-stage predicate alone
    cannot provide for EXISTING (no stage)."""

    def __init__(self, report_root):
        st = os.stat(report_root)
        self.root_identity = (st.st_dev, st.st_ino)
        self.root_dev = st.st_dev
        self.stage_fd = None
        self.stage_identity = None
        self.stage_bytes = 0
        self.stage_write_attempts = 0
        self.other_writes = []
        self.link_attempts = 0
        self.report_slot = None
        self.attempt_fds = []
        self.cleanup_done = False
        self.retired = False
        self._real_open = os.open
        self._real_write = os.write
        self._real_link = os.link
        self._real_fstat = os.fstat
        self._real_lock = publisher._lock
        self._real_cleanup = publisher._cleanup
        self._real_release = publisher._release

    def new_attempt(self):
        # One publication attempt begins: the per-attempt captured
        # fds, the report-slot identification and the
        # transaction-completion evidence reset.
        self.report_slot = None
        self.attempt_fds = []
        self.cleanup_done = False
        self.retired = False
        self.stage_write_attempts = 0

    def _live(self, fd, identity):
        # The fd is still the captured inode, not a reused number.
        try:
            st = self._real_fstat(fd)
        except OSError:
            return False
        return (st.st_dev, st.st_ino) == identity

    def stage_open(self):
        if self.stage_fd is None or self.stage_identity is None:
            return False
        return self._live(self.stage_fd, self.stage_identity)

    def stage_precondition(self):
        # The genuine pre-write boundary: the actual staging fd is
        # owned, is the retained nlink-0 regular inode on the report
        # root's device, and holds zero prior payload bytes.
        if self.stage_fd is None or self.stage_identity is None:
            return None
        try:
            st = self._real_fstat(self.stage_fd)
        except OSError:
            return None
        if (
            not stat.S_ISREG(st.st_mode)
            or st.st_nlink != 0
            or st.st_size != 0
            or st.st_dev != self.root_dev
            or (st.st_dev, st.st_ino) != self.stage_identity
        ):
            return None
        return True

    def fds_closed(self):
        # Every fd captured for the current attempt is closed (or no
        # longer the captured inode): the owned cleanup finished.  A
        # vacuous closure without a real captured report fd is not
        # completion evidence.
        return bool(self.attempt_fds) and all(
            not self._live(fd, identity)
            for fd, identity in self.attempt_fds)

    def install(self, monkeypatch):
        witness = self
        o_tmpfile = getattr(os, "O_TMPFILE", 0)

        def spy_open(name, flags, mode=0o777, *, dir_fd=None):
            fd = witness._real_open(name, flags, mode, dir_fd=dir_fd)
            if dir_fd is None:
                return fd
            try:
                parent = witness._real_fstat(dir_fd)
            except OSError:
                return fd
            if (parent.st_dev, parent.st_ino) != witness.root_identity:
                return fd
            if o_tmpfile and flags & o_tmpfile:
                try:
                    st = witness._real_fstat(fd)
                except OSError:
                    return fd
                if stat.S_ISREG(st.st_mode) and st.st_nlink == 0:
                    witness.stage_fd = fd
                    witness.stage_identity = (st.st_dev, st.st_ino)
                    witness.attempt_fds.append((fd, (st.st_dev, st.st_ino)))
            elif (flags & os.O_ACCMODE) == os.O_RDONLY:
                # The held final-verification fd opened on the report
                # destination by the exact-existing or post-link
                # verification.
                try:
                    st = witness._real_fstat(fd)
                except OSError:
                    return fd
                if stat.S_ISREG(st.st_mode):
                    witness.attempt_fds.append((fd, (st.st_dev, st.st_ino)))
            return fd

        def spy_write(fd, data):
            # The count of attempted real report os.write calls at the
            # captured live stage fd/inode, recorded immediately before
            # delegation, independently of the returned bytes: a zero
            # or failed syscall still counts as an attempted write.
            stage_attempt = (
                witness.stage_fd is not None
                and witness.stage_identity is not None
                and fd == witness.stage_fd
                and witness._live(fd, witness.stage_identity)
            )
            if stage_attempt:
                witness.stage_write_attempts += 1
            count = witness._real_write(fd, data)
            if (
                witness.stage_fd is not None
                and witness.stage_identity is not None
                and fd == witness.stage_fd
                and witness._live(fd, witness.stage_identity)
            ):
                witness.stage_bytes += count
            else:
                witness.other_writes.append((fd, count))
            return count

        def spy_link(src, dst, *args, **kwargs):
            dst_dir_fd = kwargs.get("dst_dir_fd")
            if (
                dst_dir_fd is not None
                and witness.stage_fd is not None
                and witness.stage_identity is not None
                and src == "/proc/self/fd/%d" % witness.stage_fd
                and witness._live(witness.stage_fd, witness.stage_identity)
            ):
                try:
                    st = witness._real_fstat(dst_dir_fd)
                except OSError:
                    st = None
                if st is not None and (st.st_dev, st.st_ino) == witness.root_identity:
                    witness.link_attempts += 1
            return witness._real_link(src, dst, *args, **kwargs)

        def spy_lock(slot, end):
            # The real writer-lock boundary: the slot's root is the
            # verified opened report destination fd, identified by its
            # inode, so the report writer's actual slot - and only that
            # slot - is ever marked with the transaction-completion
            # evidence.
            try:
                st = witness._real_fstat(slot.root)
            except OSError:
                st = None
            if st is not None and (st.st_dev, st.st_ino) == witness.root_identity:
                witness.report_slot = slot
            return witness._real_lock(slot, end)

        def spy_cleanup(slot, end):
            result = witness._real_cleanup(slot, end)
            # Only the identified report slot, after its real
            # successful cleanup result, marks report cleanup.
            if slot is witness.report_slot and result[0]:
                witness.cleanup_done = True
            return result

        def spy_release(slot):
            witness._real_release(slot)
            # Only the identified report slot's real pool retirement
            # marks report retirement.
            if slot is witness.report_slot:
                witness.retired = True
            return None

        monkeypatch.setattr(os, "open", spy_open)
        monkeypatch.setattr(os, "write", spy_write)
        monkeypatch.setattr(os, "link", spy_link)
        monkeypatch.setattr(publisher, "_lock", spy_lock)
        monkeypatch.setattr(publisher, "_cleanup", spy_cleanup)
        monkeypatch.setattr(publisher, "_release", spy_release)


def _recheck_witness(monkeypatch, log, witness, admission, owner, report,
                     fire=None):
    # The genuine same-admission selected rereads of the guarded
    # writer, each logged with the actual staging-fd liveness, the
    # transaction-completion/retired-slot evidence, and the exact
    # original admission, held owner guard and the original operation's
    # temporarily attached end observed before the real call.
    # ``fire`` publishes the real same-wire generation on its actual
    # product event; it is never a read ordinal.
    real = pin_eligibility._genuine_recheck

    def counting(recheck_admission, recheck_end):
        evidence = {
            "stage_open": witness.stage_open(),
            "cleanup_done": witness.cleanup_done,
            "retired": witness.retired,
            "fds_closed": witness.fds_closed(),
            "admission_exact": recheck_admission is admission,
            "guard_held": owner.guard.locked(),
            "attached_end": report.original_op.end == report.end,
        }
        if fire is not None:
            fired = fire(evidence)
            if fired:
                evidence["fired"] = True
        log.append(evidence)
        return real(recheck_admission, recheck_end)

    monkeypatch.setattr(pin_eligibility, "_genuine_recheck", counting)


def _change_generation(state):
    producer_fixture._change_generation(state["policy_root"], 2, state["payload"])


def _scenario(tmp_path, monkeypatch):
    """The real encoder transport scenario plus the real successful
    h1/h4 a/c graded production, left open for the node body.  One
    clear acquisition handoff owns the failure teardown: the raw
    custody is initialized absent, the expected-identity lookup and
    the producer acquisition run inside this one try, and the pure
    fixture construction receives the already-returned custody, so a
    failure tears down the caller-owned objects exactly once through
    the one fixture-local teardown - only the entered encoder before
    the handoff has returned custody, every returned owner once it
    has - while the producer keeps its own not-yet-returned
    resources and an encoder failure before its successful entry
    follows the actual encoder self-cleanup contract."""
    real_argv = cpu._argv
    encoder_root = tmp_path / "encoder"
    encoder_root.mkdir(mode=0o700)
    sc = transport._scenario(encoder_root, monkeypatch, real_argv)
    sc["encoder"].__enter__()
    custody = None
    ctx = owner = None
    state = None
    try:
        expected = transport._expected_tuple(sc["encoder"].cleanup_owner)
        custody = producer_fixture._scenario(tmp_path, monkeypatch, expected)
        state = _fixture(tmp_path, monkeypatch, sc, expected, *custody)
        report = _owning_result(state, monkeypatch)
    except BaseException as exc:
        if custody is not None:
            (ctx, _dataset, _bundle_ids, owner,
             _policy_root, _reader, _payload) = custody
        _close_acquired(ctx, owner, sc["encoder"], failure=exc)
        raise
    return sc, state, report


def _published_report(tmp_path, monkeypatch):
    report_root = tmp_path / "report"
    report_root.mkdir(mode=0o700)
    witness = _io_witness(str(report_root))
    witness.install(monkeypatch)
    return report_root, witness


def test_current_graded_report_publication_stable_published_and_existing(
        tmp_path, monkeypatch):
    sc, state, report = _scenario(tmp_path, monkeypatch)
    owner, admission, held, prior_end = (
        state["owner"], state["admission"], state["held"], state["prior_end"])
    try:
        report_root, witness = _published_report(tmp_path, monkeypatch)
        target = report_root / ("graded-" + report.identity[7:] + ".json")
        # The fixed private input: the ordinary legacy Report with the
        # same exact bytes is refused at the current entry with zero
        # namespace work.
        slots_before = list(publisher._SLOTS)
        legacy = program.Report(
            identity_payload=report.identity_payload,
            identity=report.identity,
            plan_identity=report.plan_identity,
            final_work=report.final_work,
            final_payload=report.final_payload,
        )
        with pytest.raises(publisher.PublicationError) as caught:
            publisher._publish_current(legacy, directory=str(report_root))
        assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
        assert caught.value.cleanup is publisher.Cleanup.CLEAN
        assert str(caught.value) == "private report publication refused"
        assert publisher._SLOTS == slots_before
        assert list(report_root.iterdir()) == []
        # Real PUBLISHED: the exact bytes staged and linked through one
        # real no-replace link attempt, with the receipt delivered by
        # the separate short release cut only after the genuine
        # storage transaction's owned cleanup finished (retired slot
        # and closed captured fds).
        rechecks = []
        _recheck_witness(monkeypatch, rechecks, witness, admission, owner, report)
        witness.new_attempt()
        receipt = publisher._publish_current(report, directory=str(report_root))
        assert receipt.outcome is publisher.Outcome.PUBLISHED
        assert receipt.durability is publisher.Publication.DURABLE
        assert receipt.cleanup is publisher.Cleanup.CLEAN
        assert witness.stage_bytes == len(report.identity_payload)
        assert witness.link_attempts == 1
        assert target.is_file()
        assert target.stat().st_mode & 0o7777 == 0o400
        assert target.read_bytes() == report.identity_payload
        # Three genuine same-admission selected rereads for this
        # publish: the pre-write cut (the actual staging fd already
        # owned, zero payload bytes written yet), the post-prelink cut
        # (after the genuine prelink metadata verification), and the
        # separate release cut after the owned cleanup (cleanup
        # complete, slot retired, captured fds closed).
        assert len(rechecks) == 3
        assert rechecks[0]["stage_open"] is True
        assert rechecks[0]["retired"] is False
        assert rechecks[1]["stage_open"] is True
        assert rechecks[1]["retired"] is False
        assert rechecks[2]["stage_open"] is False
        assert rechecks[2]["cleanup_done"] is True
        assert rechecks[2]["retired"] is True
        assert rechecks[2]["fds_closed"] is True
        # Each genuine reread ran on the exact original admission with
        # the owner guard held and the original operation's
        # temporarily attached end equal to the owning report's end.
        for evidence in rechecks:
            assert evidence["admission_exact"] is True
            assert evidence["guard_held"] is True
            assert evidence["attached_end"] is True
        # The real report payload writes of this PUBLISHED attempt.
        published_attempts = witness.stage_write_attempts
        assert published_attempts > 0
        _assert_restored(owner, held, prior_end, report)
        assert admission._invalid is False
        # Identical EXISTING: the exact existing final is verified
        # without any first write or link attempt and without any
        # stage, and the receipt is again delivered by the separate
        # after-cleanup release cut with the real completion evidence.
        witness.new_attempt()
        receipt = publisher._publish_current(report, directory=str(report_root))
        assert receipt.outcome is publisher.Outcome.EXISTING
        assert receipt.durability is publisher.Publication.DURABLE
        assert receipt.cleanup is publisher.Cleanup.CLEAN
        assert target.read_bytes() == report.identity_payload
        assert witness.link_attempts == 1
        assert witness.stage_bytes == len(report.identity_payload)
        assert len(rechecks) == 4
        assert rechecks[3]["stage_open"] is False
        assert rechecks[3]["cleanup_done"] is True
        assert rechecks[3]["retired"] is True
        assert rechecks[3]["fds_closed"] is True
        assert rechecks[3]["admission_exact"] is True
        assert rechecks[3]["guard_held"] is True
        assert rechecks[3]["attached_end"] is True
        # EXISTING staged nothing: that per-attempt count is zero,
        # consistent with the positive PUBLISHED per-attempt count.
        assert witness.stage_write_attempts == 0
        _assert_restored(owner, held, prior_end, report)
        assert admission._invalid is False
        # The real post-cleanup selected generation change, fired by
        # the actual retired-slot moment after the third transaction's
        # owned cleanup genuinely finished and ahead of the genuine
        # release guard's reread: the durable bytes stay verified, the
        # release cut refuses, and both result and safe receipt are
        # suppressed with the observed storage and cleanup truth
        # retained.
        armed = {"n": 0}
        fired = {"n": 0}
        real_cut = publisher._current_cut

        def change_on_release_cut(report_arg, end_arg):
            if (
                armed["n"] == 1
                and fired["n"] == 0
                and witness.retired
                and witness.fds_closed()
            ):
                fired["n"] = 1
                _change_generation(state)
            return real_cut(report_arg, end_arg)

        monkeypatch.setattr(publisher, "_current_cut", change_on_release_cut)
        armed["n"] = 1
        witness.new_attempt()
        with pytest.raises(publisher.PublicationError) as caught:
            publisher._publish_current(report, directory=str(report_root))
        assert fired["n"] == 1
        assert caught.value.publication is publisher.Publication.DURABLE
        assert caught.value.cleanup is publisher.Cleanup.CLEAN
        assert str(caught.value) == "private report publication refused"
        assert report.identity not in str(caught.value)
        # The normalized ordinary denial carries no data-bearing
        # context from the underlying namespace/authority error.
        assert caught.value.__context__ is None
        assert target.read_bytes() == report.identity_payload
        assert list(report_root.iterdir()) == [target]
        assert witness.link_attempts == 1
        assert witness.stage_bytes == len(report.identity_payload)
        assert len(rechecks) == 5
        assert rechecks[4]["stage_open"] is False
        assert rechecks[4]["cleanup_done"] is True
        assert rechecks[4]["retired"] is True
        assert rechecks[4]["fds_closed"] is True
        assert rechecks[4]["admission_exact"] is True
        assert rechecks[4]["guard_held"] is True
        assert rechecks[4]["attached_end"] is True
        # The post-cleanup denial staged nothing: that per-attempt
        # count is zero, consistent with the positive PUBLISHED
        # per-attempt count.
        assert witness.stage_write_attempts == 0
        # The nested genuine selected-policy writer I/O is real and
        # attributed to its own fds, never to the report destination.
        assert sum(count for _fd, count in witness.other_writes) > 0
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        _assert_restored(owner, held, prior_end, report)
        assert sc["encoder"]._state == "open"
    finally:
        _close_acquired(
            state["ctx"], state["owner"], sc["encoder"],
            failure=sys.exc_info()[1])


def test_current_graded_report_publication_change_before_first_write(
        tmp_path, monkeypatch):
    sc, state, report = _scenario(tmp_path, monkeypatch)
    owner, admission, held, prior_end = (
        state["owner"], state["admission"], state["held"], state["prior_end"])
    try:
        report_root, witness = _published_report(tmp_path, monkeypatch)
        # The genuine same-wire selected generation publication fires
        # at the real fixed product cut: the actual pre-write guarded
        # cut with the genuinely owned staging fd and zero prior
        # payload bytes, published immediately before the genuine
        # selected reread that the cut performs.
        rechecks = []
        changed = {"n": 0}

        def fire_pre_write(evidence):
            if changed["n"] == 0 and witness.stage_precondition():
                changed["n"] = 1
                evidence["stage_precondition"] = True
                _change_generation(state)
                return True
            return False

        _recheck_witness(
            monkeypatch, rechecks, witness, admission, owner, report,
            fire_pre_write)
        witness.new_attempt()
        with pytest.raises(publisher.PublicationError) as caught:
            publisher._publish_current(report, directory=str(report_root))
        assert changed["n"] == 1
        # The first guarded cut refused on the genuine reread: the
        # stage was genuinely owned then, with zero attempted report
        # payload writes at the live stage fd, zero report link
        # attempts and no final report, and the confirmed CLEAN
        # cleanup closed the owned stage.
        assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
        assert caught.value.cleanup is publisher.Cleanup.CLEAN
        assert str(caught.value) == "private report publication refused"
        assert witness.stage_fd is not None
        assert not witness.stage_open()
        assert witness.stage_bytes == 0
        assert witness.stage_write_attempts == 0
        assert witness.link_attempts == 0
        assert list(report_root.iterdir()) == []
        assert sum(count for _fd, count in witness.other_writes) > 0
        assert len(rechecks) == 1
        assert rechecks[0]["stage_precondition"] is True
        assert rechecks[0]["retired"] is False
        assert rechecks[0]["fds_closed"] is False
        assert rechecks[0]["admission_exact"] is True
        assert rechecks[0]["guard_held"] is True
        assert rechecks[0]["attached_end"] is True
        # The exact report-transaction completion evidence: the
        # identified report slot genuinely cleaned up and retired,
        # with its real captured report fd closed.
        assert witness.report_slot is not None
        assert witness.cleanup_done is True
        assert witness.retired is True
        assert witness.fds_closed() is True
        assert len(witness.attempt_fds) == 1
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        _assert_restored(owner, held, prior_end, report)
        assert sc["encoder"]._state == "open"
    finally:
        _close_acquired(
            state["ctx"], state["owner"], sc["encoder"],
            failure=sys.exc_info()[1])


def test_current_graded_report_publication_change_before_post_prelink(
        tmp_path, monkeypatch):
    sc, state, report = _scenario(tmp_path, monkeypatch)
    owner, admission, held, prior_end = (
        state["owner"], state["admission"], state["held"], state["prior_end"])
    try:
        report_root, witness = _published_report(tmp_path, monkeypatch)
        # The genuine same-wire selected generation publication fires
        # on the real fixed stage seam: the genuine prelink metadata
        # validation (``_stage_ok``) is invoked first and its actual
        # successful result observed, bound to the identified report
        # slot, its exact report stage and live inode, and the change
        # is published just before the actual post-prelink guarded cut
        # - no guessed fstat ordinal and no simulated authority return
        # decide when the change is published.
        rechecks = []
        changed = {"n": 0}
        prelink = {"result": None}
        real_stage_ok = publisher._stage_ok

        def change_on_prelink(slot, size):
            result = real_stage_ok(slot, size)
            if (
                changed["n"] == 0
                and result
                and slot is witness.report_slot
                and witness.stage_fd is not None
                and slot.stage == witness.stage_fd
                and slot.stage_identity == witness.stage_identity
                and witness._live(witness.stage_fd, witness.stage_identity)
            ):
                changed["n"] = 1
                prelink["result"] = result
                _change_generation(state)
            return result

        monkeypatch.setattr(publisher, "_stage_ok", change_on_prelink)
        _recheck_witness(monkeypatch, rechecks, witness, admission, owner, report)
        witness.new_attempt()
        expected_size = len(report.identity_payload)
        with pytest.raises(publisher.PublicationError) as caught:
            publisher._publish_current(report, directory=str(report_root))
        assert changed["n"] == 1
        assert prelink["result"] is True
        assert caught.value.publication is publisher.Publication.NOT_PUBLISHED
        assert caught.value.cleanup is publisher.Cleanup.CLEAN
        assert str(caught.value) == "private report publication refused"
        # Real staged bytes and the real successful prelink check both
        # completed, but the post-prelink cut refused: zero report link
        # attempts and no final report, with confirmed CLEAN cleanup.
        assert witness.stage_bytes == expected_size
        assert witness.stage_write_attempts > 0
        assert witness.link_attempts == 0
        assert list(report_root.iterdir()) == []
        assert sum(count for _fd, count in witness.other_writes) > 0
        # Two genuine same-admission selected rereads: the pre-write
        # cut passed with the genuinely owned staging fd and the
        # post-prelink cut observed the change after the real staged
        # bytes were fully written.
        assert len(rechecks) == 2
        assert rechecks[0]["stage_open"] is True
        assert rechecks[1]["stage_open"] is True
        assert rechecks[1]["retired"] is False
        for evidence in rechecks:
            assert evidence["admission_exact"] is True
            assert evidence["guard_held"] is True
            assert evidence["attached_end"] is True
        # The exact report-transaction completion evidence: the
        # identified report slot genuinely cleaned up and retired,
        # with its real captured report fd closed.
        assert witness.report_slot is not None
        assert witness.cleanup_done is True
        assert witness.retired is True
        assert witness.fds_closed() is True
        assert len(witness.attempt_fds) == 1
        assert admission._invalid is True
        assert admission.recheck(deadline_ms=1000) is False
        _assert_restored(owner, held, prior_end, report)
        assert sc["encoder"]._state == "open"
    finally:
        _close_acquired(
            state["ctx"], state["owner"], sc["encoder"],
            failure=sys.exc_info()[1])
