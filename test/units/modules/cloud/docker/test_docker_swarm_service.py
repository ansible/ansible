import pytest
from units.compat.mock import MagicMock

from ansible.modules.cloud.docker.docker_swarm_service import DockerServiceManager
from docker.errors import APIError


def test_retry_on_out_of_sequence_error():
    run_mock = MagicMock(
        side_effect=APIError(
            message='',
            response=None,
            explanation='rpc error: code = Unknown desc = update out of sequence',
        )
    )
    manager = DockerServiceManager(client=None)
    manager.run = run_mock
    with pytest.raises(APIError):
        manager.run_safe()
    assert run_mock.call_count == 3

def test_no_retry_on_general_api_error():
    run_mock = MagicMock(
        side_effect=APIError(
            message='',
            response=None,
            explanation='some error',
        )
    )
    manager = DockerServiceManager(client=None)
    manager.run = run_mock
    with pytest.raises(APIError):
        manager.run_safe()
    assert run_mock.call_count == 1

