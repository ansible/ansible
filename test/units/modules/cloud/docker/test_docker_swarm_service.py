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
        side_effect=APIErrorMock(message='', response=None, explanation='some error')
    )
    manager = docker_swarm_service.DockerServiceManager(client=None)
    manager.run = run_mock
    with pytest.raises(APIErrorMock):
        manager.run_safe()
    assert run_mock.call_count == 1


def test_get_docker_environment(mocker, docker_swarm_service):
    env_file_result = {'TEST1': 'A', 'TEST2': 'B', 'TEST3': 'C'}
    env_dict = {'TEST3': 'CC', 'TEST4': 'D'}
    env_string = "TEST3=CC,TEST4=D"

    env_list = ['TEST3=CC', 'TEST4=D']
    expected_result = sorted(['TEST1=A', 'TEST2=B', 'TEST3=CC', 'TEST4=D'])
    mocker.patch.object(
        docker_swarm_service, 'parse_env_file', return_value=env_file_result
    )
    mocker.patch.object(
        docker_swarm_service,
        'format_environment',
        side_effect=lambda d: ['{0}={1}'.format(key, value) for key, value in d.items()],
    )
    # Test with env dict and file
    result = docker_swarm_service.get_docker_environment(
        env_dict, env_files=['dummypath']
    )
    assert result == expected_result
    # Test with env list and file
    result = docker_swarm_service.get_docker_environment(
        env_list,
        env_files=['dummypath']
    )
    assert result == expected_result
    # Test with env string and file
    result = docker_swarm_service.get_docker_environment(
        env_string, env_files=['dummypath']
    )
    assert result == expected_result

    assert result == expected_result
    # Test with empty env
    result = docker_swarm_service.get_docker_environment(
        [], env_files=None
    )
    assert result == []
    # Test with empty env_files
    result = docker_swarm_service.get_docker_environment(
        None, env_files=[]
    )
    assert result == []


def test_get_nanoseconds_from_raw_option(docker_swarm_service):
    value = docker_swarm_service.get_nanoseconds_from_raw_option('test', None)
    assert value is None

    value = docker_swarm_service.get_nanoseconds_from_raw_option('test', '1m30s535ms')
    assert value == 90535000000

    value = docker_swarm_service.get_nanoseconds_from_raw_option('test', 10000000000)
    assert value == 10000000000

    with pytest.raises(ValueError):
        docker_swarm_service.get_nanoseconds_from_raw_option('test', [])


def test_has_dict_changed(docker_swarm_service):
    assert not docker_swarm_service.has_dict_changed(
        {"a": 1},
        {"a": 1},
    )
    assert not docker_swarm_service.has_dict_changed(
        {"a": 1},
        {"a": 1, "b": 2}
    )
    assert docker_swarm_service.has_dict_changed(
        {"a": 1},
        {"a": 2, "b": 2}
    )
    assert docker_swarm_service.has_dict_changed(
        {"a": 1, "b": 1},
        {"a": 1}
    )
    assert not docker_swarm_service.has_dict_changed(
        None,
        {"a": 2, "b": 2}
    )
    assert docker_swarm_service.has_dict_changed(
        {},
        {"a": 2, "b": 2}
    )
    assert docker_swarm_service.has_dict_changed(
        {"a": 1},
        {}
    )
    assert docker_swarm_service.has_dict_changed(
        {"a": 1},
        None
    )
    assert not docker_swarm_service.has_dict_changed(
        {},
        {}
    )
    assert not docker_swarm_service.has_dict_changed(
        None,
        None
    )
    assert not docker_swarm_service.has_dict_changed(
        {},
        None
    )
    assert not docker_swarm_service.has_dict_changed(
        None,
        {}
    )


def test_has_list_of_dicts_changed(docker_swarm_service):
    assert docker_swarm_service.has_list_of_dicts_changed(
        [
            {"a": 1},
            {"b": 1}
        ],
        [
            {"a": 1}
        ]
    )
    assert docker_swarm_service.has_list_of_dicts_changed(
        [
            {"a": 1},
        ],
        [
            {"a": 1},
            {"b": 1},
        ]
    )
    assert not docker_swarm_service.has_list_of_dicts_changed(
        [
            {"a": 1},
            {"b": 1},
        ],
        [
            {"a": 1},
            {"b": 1}
        ]
    )
    assert not docker_swarm_service.has_list_of_dicts_changed(
        None,
        [
            {"b": 1},
            {"a": 1}
        ]
    )
    assert docker_swarm_service.has_list_of_dicts_changed(
        [],
        [
            {"b": 1},
            {"a": 1}
        ]
    )
    assert not docker_swarm_service.has_list_of_dicts_changed(
        None,
        None
    )
    assert not docker_swarm_service.has_list_of_dicts_changed(
        [],
        None
    )
    assert not docker_swarm_service.has_list_of_dicts_changed(
        None,
        []
    )
    assert not docker_swarm_service.has_list_of_dicts_changed(
        [
            {"src": 1, "dst": 2},
            {"src": 1, "dst": 2, "protocol": "udp"},
        ],
        [
            {"src": 1, "dst": 2, "protocol": "tcp"},
            {"src": 1, "dst": 2, "protocol": "udp"},
        ]
    )
    assert not docker_swarm_service.has_list_of_dicts_changed(
        [
            {"src": 1, "dst": 2, "protocol": "udp"},
            {"src": 1, "dst": 3, "protocol": "tcp"},
        ],
        [
            {"src": 1, "dst": 2, "protocol": "udp"},
            {"src": 1, "dst": 3, "protocol": "tcp"},
        ]
    )
    assert docker_swarm_service.has_list_of_dicts_changed(
        [
            {"src": 1, "dst": 2, "protocol": "udp"},
            {"src": 1, "dst": 2},
            {"src": 3, "dst": 4},
        ],
        [
            {"src": 1, "dst": 3, "protocol": "udp"},
            {"src": 1, "dst": 2, "protocol": "tcp"},
            {"src": 3, "dst": 4, "protocol": "tcp"},
        ]
    )
    assert docker_swarm_service.has_list_of_dicts_changed(
        [
            {"src": 1, "dst": 3, "protocol": "tcp"},
            {"src": 1, "dst": 2, "protocol": "udp"},
        ],
        [
            {"src": 1, "dst": 2, "protocol": "tcp"},
            {"src": 1, "dst": 2, "protocol": "udp"},
        ]
    )
    assert docker_swarm_service.has_list_of_dicts_changed(
        [
            {"src": 1, "dst": 2, "protocol": "udp"},
            {"src": 1, "dst": 2, "protocol": "tcp", "extra": {"test": "foo"}},
        ],
        [
            {"src": 1, "dst": 2, "protocol": "udp"},
            {"src": 1, "dst": 2, "protocol": "tcp"},
        ]
    )
