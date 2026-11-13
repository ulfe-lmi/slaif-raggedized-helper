import pytest

from slaif_raggedized_helper import gpu_embedding_worker as parent
from slaif_raggedized_helper import gpu_worker_launch as launch
from test_gpu_worker_launch import _prepared_fixture


def test_owner_handoff_preserves_existing_arguments(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    try:
        prepared = launch.prepare(**args, preparation_owner=capture)
        try:
            binding, vocab, policy = parent._expected_binding(prepared)
            assert binding and vocab and policy
            argv, descriptors = prepared.launch_arguments()
            assert argv and descriptors and capture.pending
            with pytest.raises(launch.LaunchRefused):
                capture.close()
        finally:
            prepared.close()
        assert not capture.pending
        reservation.assert_owned()
    finally:
        reservation.close()
