import importlib.util
import json
import os
from pathlib import Path

import pytest

from slaif_raggedized_helper import derived_store, embedding_batch_store as batch
from slaif_raggedized_helper import embedding_job_journal as journal, job_records

# Load the exact existing synthetic fixture by path, without modifying import paths.
_spec = importlib.util.spec_from_file_location(
    "_repair_batch_fixture",
    Path(__file__).resolve().parents[1] / "unit" / "test_embedding_batch_store.py",
)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)
wire = _fixture.wire


def setup_case(root):
    root.chmod(0o700)
    metadata, vectors = _fixture.fixture(1)
    plan = {key: metadata[key] for key in ("dependencies", "rows", "codec_policy_fingerprint")}
    plan.update(format="embedding-job-plan-v1", purpose="prepare")
    store_dir = root / "store"
    store_dir.mkdir(mode=0o700)
    store = derived_store.Store(store_dir)
    locator = batch.publish(store, wire(metadata), vectors.container)
    return wire(plan), wire(metadata), locator, store


def running(root, plan):
    with journal.Journal(root).own(plan) as old:
        initial, rev = old.read()
        state = dict(
            version=1,
            job_id=old.spec.job_id,
            status="CLAIMED",
            attempt_id="attempt1",
            owner_id=old.owner_id,
            updated_ms=initial["events"][0]["state"]["updated_ms"],
            output=None,
        )
        _, rev = old.append(wire(state), None, rev)
        state["status"] = "RUNNING"
        envelope, rev = old.append(wire(state), None, rev)
        return envelope, rev, job_records.serialize(job_records.admit(job_records.JobState, state))


def provider(_plan, _stage):
    return "e" * 64  # synthetic provider; no real source or policy assertion


def test_positive(tmp_path):
    plan, metadata, locator, store = setup_case(tmp_path)
    try:
        before, rev, state = running(tmp_path, plan)
        with journal.Journal(tmp_path).own(plan) as new:
            result = new.repair_running_output(
                metadata, locator, rev, state, store=store, validate_current=provider
            )
            after, new_rev = new.read()
            assert after["events"][:-1] == before["events"]
            assert result.revision == new_rev and result.old_attempt_id == "attempt1"
            assert result.old_owner_id != result.repair_owner_id
            assert result.accounting == result.physical_drain == "UNKNOWN"
            assert after["events"][-1]["attempt"]["diagnostic_code"] == "RECOVERED_VALID_OUTPUT"
            assert new.verified_output(store, metadata) == result.output
            with pytest.raises(journal.JournalError):
                new.repair_running_output(
                    metadata, locator, rev, state, store=store, validate_current=provider
                )
    finally:
        store.close()


def test_process_lease(tmp_path):
    import signal
    import select

    tmp_path.chmod(0o700)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            plan, metadata, locator, store = setup_case(tmp_path)
            with journal.Journal(tmp_path).own(plan) as old:
                initial, rev = old.read()
                state = dict(
                    version=1,
                    job_id=old.spec.job_id,
                    status="CLAIMED",
                    attempt_id="child1",
                    owner_id=old.owner_id,
                    updated_ms=initial["events"][0]["state"]["updated_ms"],
                    output=None,
                )
                _, rev = old.append(wire(state), None, rev)
                state["status"] = "RUNNING"
                _, rev = old.append(wire(state), None, rev)
                payload = json.dumps(
                    [
                        plan.decode(),
                        metadata.decode(),
                        locator,
                        rev,
                        job_records.serialize(
                            job_records.admit(job_records.JobState, state)
                        ).decode(),
                    ]
                ).encode()
                os.write(write_fd, payload)
                while True:
                    signal.pause()
        finally:
            os._exit(0)
    os.close(write_fd)
    try:
        assert select.select([read_fd], [], [], 10)[0]
        plan, metadata, locator, rev, state = json.loads(os.read(read_fd, 131072))
        plan, metadata, state = plan.encode(), metadata.encode(), state.encode()
        with pytest.raises(journal.JournalError):
            with journal.Journal(tmp_path).own(plan):
                pass
        os.kill(pid, signal.SIGTERM)
        _, status = os.waitpid(pid, 0)
        pid = None
        assert os.WIFSIGNALED(status)
        store = derived_store.Store(tmp_path / "store")
        try:
            with journal.Journal(tmp_path).own(plan) as new:
                result = new.repair_running_output(
                    metadata, locator, rev, state, store=store, validate_current=provider
                )
                assert result.physical_drain == "UNKNOWN"
                assert new.verified_output(store, metadata) == result.output
        finally:
            store.close()
    finally:
        os.close(read_fd)
        if pid is not None:
            os.kill(pid, signal.SIGTERM)
            os.waitpid(pid, 0)


def test_causal_complete_plan_binding(tmp_path):
    import hashlib
    import sys

    tmp_path.chmod(0o700)
    plan, metadata, locator, store = setup_case(tmp_path)
    changed = json.loads(metadata)
    changed["rows"][0]["source_scope_sha256"] = "d" * 64
    _, vectors = _fixture.fixture(1)
    wrong = wire(changed)
    wrong_locator = batch.publish(store, wrong, vectors.container)
    source = Path(journal.__file__).read_text()
    predicate = (
        "            if metadata[key] != self.plan[key]:\n                raise ValueError\n"
    )
    assert source.count(predicate) == 1
    mutated = source.replace(predicate, "            pass  # causal control: binding omitted\n", 1)
    copy = tmp_path / "control.py"
    copy.write_text(mutated)
    name = "slaif_raggedized_helper._repair_control"
    spec = importlib.util.spec_from_file_location(name, copy)
    control = importlib.util.module_from_spec(spec)
    sys.modules[name] = control
    try:
        spec.loader.exec_module(control)
        for label in ("original", "control", "restored"):
            root = tmp_path / label
            root.mkdir(mode=0o700)
            _, rev, state = running(root, plan)
            module = control if label == "control" else journal
            with module.Journal(root).own(plan) as handle:
                if label == "control":
                    result = handle.repair_running_output(
                        wrong, wrong_locator, rev, state, store=store, validate_current=provider
                    )
                    assert result.output.ref == "sha256:" + wrong_locator
                else:
                    with pytest.raises(journal.JournalError):
                        handle.repair_running_output(
                            wrong, wrong_locator, rev, state, store=store, validate_current=provider
                        )
                    assert handle.read()[1] == rev
                    if label == "restored":
                        result = handle.repair_running_output(
                            metadata, locator, rev, state, store=store, validate_current=provider
                        )
                        assert handle.verified_output(store, metadata) == result.output
        print("original_source_sha256=" + hashlib.sha256(source.encode()).hexdigest())
        print("control_source_sha256=" + hashlib.sha256(mutated.encode()).hexdigest())
        print("omitted_predicate_sha256=" + hashlib.sha256(predicate.encode()).hexdigest())
    finally:
        sys.modules.pop(name, None)
        store.close()


@pytest.mark.parametrize(
    "case", ["stale", "provider", "missing", "corrupt", "interrupt_before", "interrupt_after"]
)
def test_negative_case(tmp_path, case, monkeypatch):
    plan, metadata, locator, store = setup_case(tmp_path)
    try:
        _, rev, state = running(tmp_path, plan)
        with journal.Journal(tmp_path).own(plan) as handle:

            def call(**overrides):
                args = dict(
                    metadata_bytes=metadata,
                    container_id=locator,
                    expected_revision=rev,
                    expected_state_bytes=state,
                    store=store,
                    validate_current=provider,
                )
                args.update(overrides)
                return handle.repair_running_output(**args)

            if case == "stale":
                for changes in (
                    dict(expected_revision="f" * 64),
                    dict(expected_state_bytes=state.replace(b"attempt1", b"attempt2")),
                    dict(expected_state_bytes=state.replace(b"RUNNING", b"CLAIMED")),
                ):
                    with pytest.raises(journal.JournalError):
                        call(**changes)
                assert handle.read()[1] == rev
            elif case == "provider":

                def changing(_plan, stage):
                    return ("e" if stage == "before_repair_validation" else "f") * 64

                with pytest.raises(journal.JournalError):
                    call(validate_current=changing)
                with pytest.raises(journal.JournalError):
                    call(validate_current=lambda *_: (_ for _ in ()).throw(ValueError("private")))
                assert handle.read()[1] == rev
            elif case in ("missing", "corrupt"):
                path = tmp_path / "store" / "derived" / "v1" / "manifests" / locator
                if case == "missing":
                    path.unlink()
                else:
                    path.write_bytes(b"corrupt")
                with pytest.raises(journal.JournalError):
                    call()
                assert handle.read()[1] == rev
            elif case == "interrupt_before":
                interrupt = KeyboardInterrupt("before")

                def interrupted(*_):
                    raise interrupt

                with pytest.raises(KeyboardInterrupt) as caught:
                    call(validate_current=interrupted)
                assert caught.value is interrupt and handle.read()[1] == rev
            else:
                interrupt = KeyboardInterrupt("after")
                original = handle.verified_output

                def interrupted(*_):
                    raise interrupt

                monkeypatch.setattr(handle, "verified_output", interrupted)
                with pytest.raises(KeyboardInterrupt) as caught:
                    call()
                assert caught.value is interrupt
                assert handle.read()[0]["events"][-1]["state"]["status"] == "COMPLETE"
                monkeypatch.setattr(handle, "verified_output", original)
                assert handle.verified_output(store, metadata)
    finally:
        store.close()


def test_supplemental_post_callback_freshness(tmp_path):
    tmp_path.chmod(0o700)
    plan, metadata, locator, store = setup_case(tmp_path)
    try:
        for scenario in ("output", "revision"):
            root = tmp_path / scenario
            root.mkdir(mode=0o700)
            _, revision, state = running(root, plan)
            manifest = tmp_path / "store" / "derived" / "v1" / "manifests" / locator
            original = manifest.read_bytes()
            with journal.Journal(root).own(plan) as handle:
                calls = []

                def mutate(_plan, stage):
                    calls.append(stage)
                    if stage == "before_repair_commit":
                        if scenario == "output":
                            manifest.write_bytes(b"corrupt")
                        else:
                            path = root / "embedding_job_journals" / handle.name
                            obj = json.loads(path.read_bytes())
                            obj["events"][-1]["state"]["updated_ms"] += 1
                            path.write_bytes(wire(obj))
                    return "e" * 64

                try:
                    with pytest.raises(journal.JournalError):
                        handle.repair_running_output(
                            metadata, locator, revision, state, store=store, validate_current=mutate
                        )
                    after, new_revision = handle.read()
                    assert calls == ["before_repair_validation", "before_repair_commit"]
                    assert (
                        len(after["events"]) == 3
                        and after["events"][-1]["state"]["status"] == "RUNNING"
                    )
                    if scenario == "output":
                        assert new_revision == revision
                    else:
                        assert (
                            new_revision != revision
                        )  # callback changed it, repair did not append
                finally:
                    manifest.write_bytes(original)
    finally:
        store.close()


def test_supplemental_state_owner_deadline(tmp_path):
    import time

    tmp_path.chmod(0o700)
    plan, metadata, locator, store = setup_case(tmp_path)
    calls = []

    def provider_count(_plan, stage):
        calls.append(stage)
        return "e" * 64

    def encode_state(obj):
        return job_records.serialize(job_records.admit(job_records.JobState, obj))

    try:
        for kind in (
            "PENDING",
            "CLAIMED",
            "UNKNOWN_COMPLETION",
            "same_owner",
            "closed",
            "deadline",
        ):
            root = tmp_path / kind
            root.mkdir(mode=0o700)
            if kind in ("PENDING", "CLAIMED", "UNKNOWN_COMPLETION", "same_owner"):
                with journal.Journal(root).own(plan) as old:
                    env, rev = old.read()
                    state = env["events"][-1]["state"]
                    if kind != "PENDING":
                        state = dict(state, status="CLAIMED", attempt_id="a", owner_id=old.owner_id)
                        _, rev = old.append(wire(state), None, rev)
                    if kind in ("UNKNOWN_COMPLETION", "same_owner"):
                        state["status"] = "RUNNING"
                        _, rev = old.append(wire(state), None, rev)
                    if kind == "same_owner":
                        calls.clear()
                        with pytest.raises(journal.JournalError):
                            old.repair_running_output(
                                metadata,
                                locator,
                                rev,
                                encode_state(state),
                                store=store,
                                validate_current=provider_count,
                            )
                        assert not calls and old.read()[1] == rev
                        continue
                    if kind == "UNKNOWN_COMPLETION":
                        state = dict(state, status="UNKNOWN_COMPLETION", owner_id=None)
                        attempt = dict(
                            version=1,
                            job_id=state["job_id"],
                            attempt_id="a",
                            request_id=None,
                            outcome="UNKNOWN_COMPLETION",
                            started_ms=state["updated_ms"],
                            ended_ms=state["updated_ms"],
                            input_tokens=None,
                            output_tokens=None,
                            diagnostic_code=None,
                            output=None,
                        )
                        _, rev = old.append(wire(state), wire(attempt), rev)
                with journal.Journal(root).own(plan) as fresh:
                    calls.clear()
                    with pytest.raises(journal.JournalError):
                        fresh.repair_running_output(
                            metadata,
                            locator,
                            rev,
                            encode_state(state),
                            store=store,
                            validate_current=provider_count,
                        )
                    env, after = fresh.read()
                    assert (
                        not calls and after == rev and env["events"][-1]["state"]["status"] == kind
                    )
            else:
                _, rev, state = running(root, plan)
                handle = journal.Journal(root).own(plan)
                with handle:
                    if kind == "deadline":
                        calls.clear()

                        def slow(_plan, stage):
                            calls.append(stage)
                            time.sleep(0.1)
                            return "e" * 64

                        with pytest.raises(journal.JournalError):
                            handle.repair_running_output(
                                metadata,
                                locator,
                                rev,
                                state,
                                store=store,
                                validate_current=slow,
                                deadline_ms=50,
                            )
                        assert calls == ["before_repair_validation"] and handle.read()[1] == rev
                if kind == "closed":
                    calls.clear()
                    with pytest.raises(journal.JournalError):
                        handle.repair_running_output(
                            metadata,
                            locator,
                            rev,
                            state,
                            store=store,
                            validate_current=provider_count,
                        )
                    assert not calls
                    with journal.Journal(root).own(plan) as verify:
                        assert verify.read()[1] == rev
    finally:
        store.close()


@pytest.mark.parametrize("phase", ["commit", "verification"])
def test_postcommit_deadline_preserves_complete(tmp_path, monkeypatch, phase):
    import time

    plan, metadata, locator, store = setup_case(tmp_path)
    try:
        _, revision, state = running(tmp_path, plan)
        with journal.Journal(tmp_path).own(plan) as handle:
            observed = []
            if phase == "commit":
                original = handle._commit

                def delayed(*args):
                    result = original(*args)
                    observed.append("commit_returned")
                    time.sleep(0.1)
                    return result

                monkeypatch.setattr(handle, "_commit", delayed)
            else:
                original = handle.verified_output

                def delayed(*args):
                    result = original(*args)
                    observed.append("verified")
                    time.sleep(0.1)
                    return result

                monkeypatch.setattr(handle, "verified_output", delayed)
            with pytest.raises(journal.JournalError):
                handle.repair_running_output(
                    metadata,
                    locator,
                    revision,
                    state,
                    store=store,
                    validate_current=provider,
                    deadline_ms=50,
                )
            assert observed == (["commit_returned"] if phase == "commit" else ["verified"])
            assert handle.read()[0]["events"][-1]["state"]["status"] == "COMPLETE"
            if phase == "verification":
                monkeypatch.setattr(handle, "verified_output", original)
            assert handle.verified_output(store, metadata)
    finally:
        store.close()
