import pytest


class APIErrorMock(Exception):

    def __init__(self, message, response=None, explanation=None):
        self.message = message
        self.response = response
        self.explanation = explanation


@pytest.fixture(autouse=True)
def docker_module_mock(mocker):
    docker_module_mock = mocker.MagicMock()
    docker_utils_module_mock = mocker.MagicMock()
    docker_errors_module_mock = mocker.MagicMock()
    docker_errors_module_mock.APIError = APIErrorMock
    mock_modules = {
        'docker': docker_module_mock,
        'docker.utils': docker_utils_module_mock,
        'docker.errors': docker_errors_module_mock,
    }
    return mocker.patch.dict('sys.modules', **mock_modules)


@pytest.fixture(autouse=True)
def docker_swarm_service():
    from ansible.modules.cloud.docker import docker_swarm_service
    return docker_swarm_service


def test_retry_on_out_of_sequence_error(mocker, docker_swarm_service):
    run_mock = mocker.MagicMock(
        side_effect=APIErrorMock(
            message='',
            response=None,
            explanation='rpc error: code = Unknown desc = update out of sequence',
        )
    )
    manager = docker_swarm_service.DockerServiceManager(client=None)
    manager.run = run_mock
    with pytest.raises(APIErrorMock):
        manager.run_safe()
    assert run_mock.call_count == 3


def test_no_retry_on_general_api_error(mocker, docker_swarm_service):
    run_mock = mocker.MagicMock(
        side_effect=APIErrorMock(
            message='',
            response=None,
            explanation='some error',
        )
    )
    manager = docker_swarm_service.DockerServiceManager(client=None)
    manager.run = run_mock
    with pytest.raises(APIErrorMock):
        manager.run_safe()
    assert run_mock.call_count == 1
