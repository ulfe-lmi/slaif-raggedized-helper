"""Model-free stable GPU worker prediction tests."""

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import gpu_worker_identity as identity
from slaif_raggedized_helper import gpu_worker_launch as launch
from slaif_raggedized_helper import gpu_worker_protocol as wire
from test_gpu_worker_launch import _prepared_fixture


def test_stable_independent_preparations_and_closed_schema(tmp_path, monkeypatch):
    a = tmp_path / 'a'
    b = tmp_path / 'b'
    a.mkdir()
    b.mkdir()
    args_a, reservation_a = _prepared_fixture(a, monkeypatch)
    args_b, reservation_b = _prepared_fixture(b, monkeypatch)
    first = second = None
    try:
        first = launch.prepare(**args_a)
        second = launch.prepare(**args_b)
        assert first.plan_id != second.plan_id
        assert first.startup != second.startup
        one, two = identity.predict(first), identity.predict(second)
        assert one == two
        assert identity.validate_record(one.record_bytes) == one.fingerprint
        expected = hashlib.sha256(identity._DOMAIN + one.record_bytes).hexdigest()
        assert one.fingerprint == 'sha256:' + expected
        assert one.fingerprint != 'sha256:' + hashlib.sha256(one.record_bytes).hexdigest()
        record = wire.parse(one.record_bytes)
        assert all(node['observed_rdev'] is None for node in record['nodes'])
        assert record['hardware_qualification'] == 'unknown'
        for key in ('plan_id', 'startup_nonce', 'pid', 'fd'):
            assert key not in record
        with pytest.raises(dataclasses.FrozenInstanceError):
            one.fingerprint = 'bad'
        with pytest.raises(identity.IdentityRefused):
            identity.validate_record(one.record_bytes[:-1] + b',"schema":1}')
        for key, bad in [('schema', True), ('contract', 'cpu-worker-v1'),
                         ('resource', {}), ('space_id', 'bad')]:
            changed = dict(record)
            changed[key] = bad
            with pytest.raises(identity.IdentityRefused):
                identity.validate_record(wire.encode(changed))
        changed = dict(record, unknown='x')
        with pytest.raises(identity.IdentityRefused):
            identity.validate_record(wire.encode(changed))
        with pytest.raises(identity.IdentityRefused):
            identity.validate_record(json.dumps(record).encode())
    finally:
        if first is not None:
            first.close()
        if second is not None:
            second.close()
        reservation_a.close()
        reservation_b.close()


def test_prediction_variation_and_mutation_refusal(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    first = second = None
    try:
        first = launch.prepare(**args)
        initial = identity.predict(first)
        args['resource'] = dataclasses.replace(args['resource'], cpu_seconds=29)
        second = launch.prepare(**args)
        assert identity.predict(second).fingerprint != initial.fingerprint
        source = Path(args['source_root']) / 'src/slaif_raggedized_helper/schema.py'
        source.write_bytes(source.read_bytes() + b'\n')
        with pytest.raises(identity.IdentityRefused, match='^identity refused$'):
            identity.predict(first)
        reservation.assert_owned()
    finally:
        if first is not None:
            first.close()
        if second is not None:
            second.close()
        reservation.close()


def test_fake_and_closed_prepared_refuse(tmp_path, monkeypatch):
    with pytest.raises(identity.IdentityRefused):
        identity.predict(object())
    with pytest.raises(identity.IdentityRefused):
        identity.observe(object())
    with pytest.raises(identity.IdentityRefused):
        identity.observe(identity.PlannedWorkerIdentity(b'{}', 'sha256:' + '0' * 64))
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    try:
        prepared.close()
        with pytest.raises(identity.IdentityRefused):
            identity.predict(prepared)
        reservation.assert_owned()
    finally:
        prepared.close()
        reservation.close()


def test_driver_and_wire_policy_change_identity(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    owners = []
    try:
        base = launch.prepare(**args)
        owners.append(base)
        original = identity.predict(base)
        driver_path = tmp_path / 'driver'
        driver_path.write_bytes(b'private synthetic bytes')
        args['drivers'] = (launch.DriverFile(str(driver_path), 'libcuda.so.1',
                                            driver_path.stat().st_size,
                                            hashlib.sha256(driver_path.read_bytes()).hexdigest()),)
        changed = launch.prepare(**args)
        owners.append(changed)
        assert identity.predict(changed).fingerprint != original.fingerprint
        args['drivers'] = ()
        args['wire_policy'] = dataclasses.replace(args['wire_policy'], calls=3)
        changed_policy = launch.prepare(**args)
        owners.append(changed_policy)
        assert identity.predict(changed_policy).fingerprint != original.fingerprint
    finally:
        for owner in reversed(owners):
            owner.close()
        reservation.close()


def test_prediction_starts_no_process_and_preserves_interrupt(tmp_path, monkeypatch):
    import subprocess
    import sys

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    original = prepared.revalidate
    try:
        def forbidden(*args, **kwargs):
            raise AssertionError('process creation is forbidden')

        monkeypatch.setattr(subprocess, 'Popen', forbidden)
        before = set(sys.modules)
        identity.predict(prepared)
        assert not {'torch', 'transformers'} & (set(sys.modules) - before)
        class Stop(BaseException):
            pass
        stop = Stop()
        def interrupt():
            raise stop
        monkeypatch.setattr(prepared, 'revalidate', interrupt)
        with pytest.raises(Stop) as caught:
            identity.predict(prepared)
        assert caught.value is stop
        monkeypatch.setattr(prepared, 'revalidate', original)
    finally:
        prepared.close()
        reservation.close()


@pytest.mark.parametrize('field', ['host', 'device'])
def test_host_and_device_configuration_change_identity(tmp_path, monkeypatch, field):
    from slaif_raggedized_helper import embedding_job_ownership as ownership
    from slaif_raggedized_helper.schema import fingerprint

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    first = second = None
    other_reservation = None
    try:
        first = launch.prepare(**args)
        initial = identity.predict(first)
        changes = {'host_id': 'b' * 64} if field == 'host' else {
            'device_uuid': 'GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}
        device = dataclasses.replace(args['device'], **changes)
        key = fingerprint({'kind': 'gpu-mode-operation-v1', 'host_id': device.host_id,
                           'device_uuid': device.device_uuid})
        directory = tmp_path / 'other-reservation'
        directory.mkdir(mode=0o700)
        other_reservation = ownership.claim(directory, key)
        args['device'], args['reservation'] = device, other_reservation
        second = launch.prepare(**args)
        assert identity.predict(second).fingerprint != initial.fingerprint
        reservation.assert_owned()
        other_reservation.assert_owned()
    finally:
        if first is not None:
            first.close()
        if second is not None:
            second.close()
        if other_reservation is not None:
            other_reservation.close()
        reservation.close()
