import copy
import json
import os

import pytest

from slaif_raggedized_helper import embedding_batch_store as batch, embedding_vectors
from slaif_raggedized_helper import embedding_job_journal as journal


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def plan():
    h = "a" * 64
    dep = dict.fromkeys(batch._DEPS, h)
    dep["normalization_policy_id"] = embedding_vectors.POLICY_ID
    row = {
        "chunk_id": "c",
        "revision_id": "r",
        "extraction_id": "e",
        "representation_id": "b" * 64,
        "rendered_sha256": h,
        "source_scope_sha256": h,
        "input_sha256": h,
        "token_count": 2,
    }
    return {
        "format": "embedding-job-plan-v1",
        "purpose": "prepare",
        "dependencies": dep,
        "rows": [row],
        "codec_policy_fingerprint": batch.POLICY.fingerprint(),
    }


def state(job, status, owner=None, attempt="attempt1", timestamp=10000000000000, output=None):
    return wire(
        {
            "version": 1,
            "job_id": job,
            "status": status,
            "attempt_id": attempt,
            "owner_id": owner,
            "updated_ms": timestamp,
            "output": output,
        }
    )


def test_plan_identity_and_admission():
    original = plan()
    spec = journal.make_spec(wire(original))
    assert spec.kind == "embedding"
    for section, key, value in [
        ("rows", "source_scope_sha256", "c" * 64),
        ("rows", "token_count", 3),
        ("dependencies", "definition_fingerprint", "c" * 64),
        ("dependencies", "execution_fingerprint", "c" * 64),
    ]:
        changed = copy.deepcopy(original)
        (changed[section][0] if section == "rows" else changed[section])[key] = value
        assert journal.make_spec(wire(changed)).job_id != spec.job_id
    for raw in [
        b'{"format":1,"format":2}',
        b"\xff",
        wire({**original, "extra": 1}),
        wire({**original, "rows": original["rows"] * 2}),
        b" " * 131073,
    ]:
        with pytest.raises(journal.JournalError):
            journal.make_spec(raw)


def test_cas_owner_transitions_and_close(tmp_path):
    tmp_path.chmod(0o700)
    p = wire(plan())
    with journal.Journal(tmp_path).own(p) as handle:
        obj, rev = handle.read()
        assert obj["events"][0]["state"]["status"] == "PENDING"
        job = handle.spec.job_id
        with pytest.raises(journal.JournalError):
            handle.append(state(job, "CLAIMED", "wrong"), None, rev)
        _, rev2 = handle.append(state(job, "CLAIMED", handle.owner_id), None, rev)
        with pytest.raises(journal.JournalError):
            handle.append(state(job, "RUNNING", handle.owner_id), None, rev)
        with pytest.raises(journal.JournalError):
            handle.append(state(job, "RUNNING", handle.owner_id, "other"), None, rev2)
        handle.append(state(job, "RUNNING", handle.owner_id), None, rev2)
    with pytest.raises(journal.JournalError):
        handle.read()
    with journal.Journal(tmp_path).own(p) as reopened:
        assert len(reopened.read()[0]["events"]) == 3


def test_symlink_and_sentinel(tmp_path):
    tmp_path.chmod(0o700)
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"untouched")
    directory = tmp_path / "embedding_job_journals"
    directory.mkdir(mode=0o700)
    name = journal.make_spec(wire(plan())).job_id[7:]
    (directory / name).symlink_to(sentinel)
    with pytest.raises(journal.JournalError):
        with journal.Journal(tmp_path).own(wire(plan())):
            pass
    assert sentinel.read_bytes() == b"untouched"


def test_reject_forged_history_and_failure_atomicity(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    with journal.Journal(tmp_path).own(wire(plan())) as handle:
        obj, rev = handle.read()
        original_fsync = os.fsync

        def fail_file(fd):
            if fd != handle.dirfd:
                raise OSError("synthetic before file fsync")
            original_fsync(fd)

        monkeypatch.setattr(os, "fsync", fail_file)
        with pytest.raises(journal.JournalError):
            handle.append(state(handle.spec.job_id, "CLAIMED", handle.owner_id), None, rev)
        assert handle.read()[1] == rev
        monkeypatch.setattr(os, "fsync", original_fsync)
        original_replace = os.replace

        def fail(*args, **kwargs):
            raise OSError("synthetic before replace")

        monkeypatch.setattr(os, "replace", fail)
        with pytest.raises(journal.JournalError):
            handle.append(state(handle.spec.job_id, "CLAIMED", handle.owner_id), None, rev)
        assert handle.read()[1] == rev
        monkeypatch.setattr(os, "replace", original_replace)
        original_fsync = os.fsync

        def fail_directory(fd):
            if fd == handle.dirfd:
                raise OSError("synthetic after replace")
            original_fsync(fd)

        monkeypatch.setattr(os, "fsync", fail_directory)
        with pytest.raises(journal.JournalError):
            handle.append(state(handle.spec.job_id, "CLAIMED", handle.owner_id), None, rev)
        assert len(handle.read()[0]["events"]) == 2
        monkeypatch.setattr(os, "fsync", original_fsync)
        obj["events"].append(obj["events"][0])
        path = tmp_path / "embedding_job_journals" / handle.name
        path.write_bytes(wire(obj))
        with pytest.raises(journal.JournalError):
            handle.read()


def test_history_bounds_and_unchecked_input(tmp_path):
    tmp_path.chmod(0o700)
    with journal.Journal(tmp_path).own(wire(plan())) as handle:
        obj, rev = handle.read()
        job = handle.spec.job_id
        with pytest.raises(journal.JournalError):
            handle.append({"status": "CLAIMED"}, None, rev)
        with pytest.raises(journal.JournalError):
            handle.append(state("sha256:" + "f" * 64, "CLAIMED", handle.owner_id), None, rev)
        with pytest.raises(journal.JournalError):
            handle.append(state(job, "RUNNING", handle.owner_id), None, rev)
        path = tmp_path / "embedding_job_journals" / handle.name
        for events in ([obj["events"][0]] * 65, []):
            path.write_bytes(wire(dict(obj, events=events)))
            with pytest.raises(journal.JournalError):
                handle.read()
        path.write_bytes(b"x" * 524289)
        with pytest.raises(journal.JournalError):
            handle.read()


def test_private_errors_and_foreign_entries(tmp_path):
    import traceback

    tmp_path.chmod(0o700)
    marker = "private-marker-81726"
    foreign = tmp_path / marker
    foreign.write_text("keep")
    with journal.Journal(tmp_path).own(wire(plan())) as handle:
        _, rev = handle.read()
        try:
            handle.append(marker.encode(), None, rev)
        except journal.JournalError:
            assert marker not in traceback.format_exc()
        else:
            pytest.fail("invalid state admitted")
        assert foreign.read_text() == "keep"


def test_history_attempt_reuse_and_verified_label(tmp_path):
    tmp_path.chmod(0o700)
    with journal.Journal(tmp_path).own(wire(plan())) as handle:
        obj, _ = handle.read()
        job = handle.spec.job_id
        owner = handle.owner_id
        t = 10000000000000
        claimed = json.loads(state(job, "CLAIMED", owner, timestamp=t))
        running = json.loads(state(job, "RUNNING", owner, timestamp=t))
        failed = json.loads(state(job, "RETRYABLE_FAILED", None, timestamp=t))
        attempt = {
            "version": 1,
            "job_id": job,
            "attempt_id": "attempt1",
            "request_id": None,
            "outcome": "RETRYABLE_FAILED",
            "started_ms": t,
            "ended_ms": t,
            "input_tokens": None,
            "output_tokens": None,
            "diagnostic_code": None,
            "output": None,
        }
        pending = json.loads(state(job, "PENDING", None, timestamp=t))
        events = obj["events"] + [
            {"state": claimed, "attempt": None},
            {"state": running, "attempt": None},
            {"state": failed, "attempt": attempt},
            {"state": pending, "attempt": None},
            {"state": claimed, "attempt": None},
        ]
        path = tmp_path / "embedding_job_journals" / handle.name
        path.write_bytes(wire(dict(obj, events=events)))
        with pytest.raises(journal.JournalError):
            handle.read()
        complete = json.loads(state(job, "COMPLETE", None, timestamp=t))
        complete["output"] = {
            "ref": "sha256:" + "b" * 64,
            "fingerprint": "sha256:" + "c" * 64,
            "availability": "unverified",
        }
        attempt.update(outcome="COMPLETE", output=complete["output"])
        events = obj["events"] + [
            {"state": claimed, "attempt": None},
            {"state": running, "attempt": None},
            {"state": complete, "attempt": attempt},
        ]
        path.write_bytes(wire(dict(obj, events=events)))
        with pytest.raises(journal.JournalError):
            handle.read()


def test_fifo_and_foreign_stage_are_preserved(tmp_path):
    tmp_path.chmod(0o700)
    directory = tmp_path / "embedding_job_journals"
    directory.mkdir(mode=0o700)
    stage = directory / ".stage-foreign"
    stage.write_bytes(b"keep")
    name = journal.make_spec(wire(plan())).job_id[7:]
    os.mkfifo(directory / name, 0o600)
    with pytest.raises(journal.JournalError):
        with journal.Journal(tmp_path).own(wire(plan())):
            pass
    assert stage.read_bytes() == b"keep"


def test_parent_fsync_order_and_failure_unwinds(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    actual = os.fsync
    calls = []

    def trace(fd):
        st = os.fstat(fd)
        calls.append((st.st_dev, st.st_ino))
        actual(fd)

    monkeypatch.setattr(os, "fsync", trace)
    with journal.Journal(tmp_path).own(wire(plan())):
        pass
    parent = tmp_path.stat()
    directory = (tmp_path / "embedding_job_journals").stat()
    parent_id = (parent.st_dev, parent.st_ino)
    dir_id = (directory.st_dev, directory.st_ino)
    assert parent_id in calls and dir_id in calls
    assert calls.index(parent_id) < calls.index(dir_id)

    def fail_parent(fd):
        st = os.fstat(fd)
        if (st.st_dev, st.st_ino) == parent_id:
            raise OSError("synthetic")
        actual(fd)

    monkeypatch.setattr(os, "fsync", fail_parent)
    handle = journal.Journal(tmp_path).own(wire(plan()))
    with pytest.raises(journal.JournalError):
        handle.__enter__()
    assert handle.rootfd is None and handle.dirfd is None
    monkeypatch.setattr(os, "fsync", actual)
    with journal.Journal(tmp_path).own(wire(plan())):
        pass


def test_interrupted_and_private_cleanup(tmp_path, monkeypatch):
    import secrets
    import traceback

    tmp_path.chmod(0o700)
    handle = journal.Journal(tmp_path).own(wire(plan()))
    handle.__enter__()
    directory, root = handle.dirfd, handle.rootfd
    realclose = os.close
    hit = False

    def interrupt(fd):
        nonlocal hit
        if fd == directory and not hit:
            hit = True
            raise KeyboardInterrupt()
        realclose(fd)

    monkeypatch.setattr(os, "close", interrupt)
    with pytest.raises(KeyboardInterrupt):
        handle.__exit__(None, None, None)
    for fd in (directory, root):
        with pytest.raises(OSError):
            os.fstat(fd)
    monkeypatch.setattr(os, "close", realclose)
    with journal.Journal(tmp_path).own(wire(plan())):
        pass
    handle = journal.Journal(tmp_path).own(wire(plan()))
    handle.__enter__()
    directory = handle.dirfd
    secret = secrets.token_hex(16)

    def fail(fd):
        if fd == directory:
            raise OSError(secret)
        realclose(fd)

    monkeypatch.setattr(os, "close", fail)
    try:
        handle.__exit__(None, None, None)
    except journal.JournalError:
        assert secret not in traceback.format_exc()
    else:
        pytest.fail("expected cleanup refusal")
    assert handle.dirfd == directory
    monkeypatch.setattr(os, "close", realclose)
    handle._close()
    with pytest.raises(OSError):
        os.fstat(directory)
    with journal.Journal(tmp_path).own(wire(plan())):
        pass


def test_body_exception_survives_cleanup_failure(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    handle = journal.Journal(tmp_path).own(wire(plan()))
    realclose = os.close
    with pytest.raises(RuntimeError, match="body") as caught:
        with handle:
            directory = handle.dirfd

            def fail(fd):
                if fd == directory:
                    raise OSError("private")
                realclose(fd)

            monkeypatch.setattr(os, "close", fail)
            raise RuntimeError("body")
    assert caught.value.__notes__ == ["journal cleanup failed"]
    monkeypatch.setattr(os, "close", realclose)
    handle._close()


def test_valid_history_reaches_event_limit(tmp_path):
    tmp_path.chmod(0o700)
    with journal.Journal(tmp_path).own(wire(plan())) as handle:
        envelope, _ = handle.read()
        job, owner = handle.spec.job_id, handle.owner_id
        t = 10000000000000
        events = envelope["events"]
        for i in range(16):
            aid = f"a{i}"
            for status in ("CLAIMED", "RUNNING"):
                events.append(
                    {"state": json.loads(state(job, status, owner, aid, t)), "attempt": None}
                )
            failed = json.loads(state(job, "RETRYABLE_FAILED", None, aid, t))
            attempt = {
                "version": 1,
                "job_id": job,
                "attempt_id": aid,
                "request_id": None,
                "outcome": "RETRYABLE_FAILED",
                "started_ms": t,
                "ended_ms": t,
                "input_tokens": None,
                "output_tokens": None,
                "diagnostic_code": None,
                "output": None,
            }
            events.append({"state": failed, "attempt": attempt})
            if i < 15:
                events.append(
                    {"state": json.loads(state(job, "PENDING", None, aid, t)), "attempt": None}
                )
        assert len(events) == 64
        assert len(handle._validate(wire(envelope))["events"]) == 64
        events.append({"state": json.loads(state(job, "PENDING", None, "a15", t)), "attempt": None})
        # This 65th transition is valid on its own: only the event cap rejects it.
        from slaif_raggedized_helper import job_records

        previous = job_records.admit(job_records.JobState, events[-2]["state"])
        following = job_records.admit(job_records.JobState, events[-1]["state"])
        job_records.transition(previous, following)
        with pytest.raises(ValueError):
            handle._validate(wire(envelope))


def test_plan_limits_and_mapping():
    from slaif_raggedized_helper.schema import fingerprint

    p = plan()
    spec = journal.make_spec(wire(p))
    row = p["rows"][0]
    assert spec.inputs[0].ref == "sha256:" + row["representation_id"]
    assert spec.inputs[0].fingerprint == fingerprint({"kind": "embedding-job-row-v1", "row": row})
    assert spec.configuration.policy == fingerprint(
        {
            "kind": "embedding-job-policy-v1",
            "dependencies": p["dependencies"],
            "codec_policy_fingerprint": p["codec_policy_fingerprint"],
        }
    )
    for key in p["dependencies"]:
        if key == "normalization_policy_id":
            continue  # fixed by the accepted metadata contract
        changed = copy.deepcopy(p)
        changed["dependencies"][key] = "f" * 64
        assert journal.make_spec(wire(changed)).job_id != spec.job_id
    for key in row:
        changed = copy.deepcopy(p)
        changed["rows"][0][key] = (
            3
            if key == "token_count"
            else ("f" * 64 if key.endswith("sha256") or key == "representation_id" else "different")
        )
        assert journal.make_spec(wire(changed)).job_id != spec.job_id
    changed = copy.deepcopy(p)
    changed["rows"] = [
        dict(row, chunk_id=str(i), representation_id=f"{i:064x}") for i in range(129)
    ]
    with pytest.raises(journal.JournalError):
        journal.make_spec(wire(changed))
    changed["rows"] = changed["rows"][:2]
    forward = journal.make_spec(wire(changed))
    changed["rows"].reverse()
    assert journal.make_spec(wire(changed)).job_id != forward.job_id
    with pytest.raises(ValueError):
        journal._parse(("[" * 33 + "0" + "]" * 33).encode(), 131072)
    with pytest.raises(ValueError):
        journal._parse(wire([0] * 20000), 131072)


def test_directory_substitution_and_owner_privacy(tmp_path, monkeypatch):
    import secrets
    import traceback

    tmp_path.chmod(0o700)
    with journal.Journal(tmp_path).own(wire(plan())) as handle:
        directory = tmp_path / "embedding_job_journals"
        original = tmp_path / "preserved"
        directory.rename(original)
        directory.mkdir(mode=0o700)
        sentinel = directory / handle.name
        sentinel.write_bytes(b"sentinel")
        sentinel.chmod(0o600)
        with pytest.raises(journal.JournalError):
            handle.read()
        assert sentinel.read_bytes() == b"sentinel"
        directory.rename(tmp_path / "replacement")
        original.rename(directory)
        secret = secrets.token_hex(16)
        lease_type = type(handle.lease)
        original_assert = lease_type.assert_owned

        def fail(_self):
            raise OSError(secret)

        monkeypatch.setattr(lease_type, "assert_owned", fail)
        try:
            _ = handle.owner_id
        except journal.JournalError:
            assert secret not in traceback.format_exc()
        else:
            pytest.fail("expected refusal")
        monkeypatch.setattr(lease_type, "assert_owned", original_assert)
    assert (tmp_path / "replacement" / handle.name).read_bytes() == b"sentinel"


def test_forked_handle_refused(tmp_path):
    tmp_path.chmod(0o700)
    with journal.Journal(tmp_path).own(wire(plan())) as handle:
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            try:
                handle.read()
            except journal.JournalError:
                os.write(write_fd, b"refused")
            finally:
                os.close(write_fd)
                os._exit(0)
        os.close(write_fd)
        try:
            import select

            assert select.select([read_fd], [], [], 5)[0]
            assert os.read(read_fd, 64) == b"refused"
        finally:
            os.close(read_fd)
            _, status = os.waitpid(pid, 0)
            assert os.waitstatus_to_exitcode(status) == 0
        assert len(handle.read()[0]["events"]) == 1


def test_failed_entry_interrupted_close_preserves_interrupt(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    actual_fsync = os.fsync
    actual_close = os.close
    handle = journal.Journal(tmp_path).own(wire(plan()))
    fired = False

    def fail_sync(fd):
        if fd == handle.rootfd:
            raise KeyboardInterrupt()
        actual_fsync(fd)

    def fail_close(fd):
        nonlocal fired
        if fd == handle.dirfd and not fired:
            fired = True
            raise OSError("cleanup failure")
        actual_close(fd)

    monkeypatch.setattr(os, "fsync", fail_sync)
    monkeypatch.setattr(os, "close", fail_close)
    with pytest.raises(KeyboardInterrupt) as caught:
        handle.__enter__()
    assert caught.value.__notes__ == ["journal cleanup failed"]
    assert handle.rootfd is None and handle.dirfd is None
    monkeypatch.setattr(os, "fsync", actual_fsync)
    monkeypatch.setattr(os, "close", actual_close)
    with journal.Journal(tmp_path).own(wire(plan())):
        pass
