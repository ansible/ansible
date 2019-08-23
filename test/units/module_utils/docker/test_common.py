from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest

from docker.constants import DEFAULT_DOCKER_API_VERSION

from units.modules.utils import patch, set_module_args
from ansible.module_utils import basic

from ansible.module_utils.docker.common import (
    Store,
    InitializationError,
    DockerFileStore,
    AnsibleDockerClient,
    compare_dict_allow_more_present,
    compare_generic,
    convert_duration_to_nanosecond,
    parse_healthcheck
)

curr_dir = os.path.dirname(__file__)
test_data_dir = os.path.join(curr_dir, "test_data")

EXAMPLE_REGISTRY = "registry.example.com"
CREDENTIAL_HELPERS = [
    'desktop-config.json',
    'osxkeychain-config.json',
    'secretservice-config.json'
]

DICT_ALLOW_MORE_PRESENT = (
    {
        'av': {},
        'bv': {'a': 1},
        'result': True
    },
    {
        'av': {'a': 1},
        'bv': {'a': 1, 'b': 2},
        'result': True
    },
    {
        'av': {'a': 1},
        'bv': {'b': 2},
        'result': False
    },
    {
        'av': {'a': 1},
        'bv': {'a': None, 'b': 1},
        'result': False
    },
    {
        'av': {'a': None},
        'bv': {'b': 1},
        'result': False
    },
)

COMPARE_GENERIC = [
    ########################################################################################
    # value
    {
        'a': 1,
        'b': 2,
        'method': 'strict',
        'type': 'value',
        'result': False
    },
    {
        'a': 'hello',
        'b': 'hello',
        'method': 'strict',
        'type': 'value',
        'result': True
    },
    {
        'a': None,
        'b': 'hello',
        'method': 'strict',
        'type': 'value',
        'result': False
    },
    {
        'a': None,
        'b': None,
        'method': 'strict',
        'type': 'value',
        'result': True
    },
    {
        'a': 1,
        'b': 2,
        'method': 'ignore',
        'type': 'value',
        'result': True
    },
    {
        'a': None,
        'b': 2,
        'method': 'ignore',
        'type': 'value',
        'result': True
    },
    ########################################################################################
    # list
    {
        'a': [
            'x',
        ],
        'b': [
            'y',
        ],
        'method': 'strict',
        'type': 'list',
        'result': False
    },
    {
        'a': [
            'x',
        ],
        'b': [
            'x',
            'x',
        ],
        'method': 'strict',
        'type': 'list',
        'result': False
    },
    {
        'a': [
            'x',
            'y',
        ],
        'b': [
            'x',
            'y',
        ],
        'method': 'strict',
        'type': 'list',
        'result': True
    },
    {
        'a': [
            'x',
            'y',
        ],
        'b': [
            'y',
            'x',
        ],
        'method': 'strict',
        'type': 'list',
        'result': False
    },
    {
        'a': [
            'x',
            'y',
        ],
        'b': [
            'x',
        ],
        'method': 'allow_more_present',
        'type': 'list',
        'result': False
    },
    {
        'a': [
            'x',
        ],
        'b': [
            'x',
            'y',
        ],
        'method': 'allow_more_present',
        'type': 'list',
        'result': True
    },
    {
        'a': [
            'x',
            'x',
            'y',
        ],
        'b': [
            'x',
            'y',
        ],
        'method': 'allow_more_present',
        'type': 'list',
        'result': False
    },
    {
        'a': [
            'x',
            'z',
        ],
        'b': [
            'x',
            'y',
            'x',
            'z',
        ],
        'method': 'allow_more_present',
        'type': 'list',
        'result': True
    },
    {
        'a': [
            'x',
            'y',
        ],
        'b': [
            'y',
            'x',
        ],
        'method': 'ignore',
        'type': 'list',
        'result': True
    },
    ########################################################################################
    # set
    {
        'a': [
            'x',
        ],
        'b': [
            'y',
        ],
        'method': 'strict',
        'type': 'set',
        'result': False
    },
    {
        'a': [
            'x',
        ],
        'b': [
            'x',
            'x',
        ],
        'method': 'strict',
        'type': 'set',
        'result': True
    },
    {
        'a': [
            'x',
            'y',
        ],
        'b': [
            'x',
            'y',
        ],
        'method': 'strict',
        'type': 'set',
        'result': True
    },
    {
        'a': [
            'x',
            'y',
        ],
        'b': [
            'y',
            'x',
        ],
        'method': 'strict',
        'type': 'set',
        'result': True
    },
    {
        'a': [
            'x',
            'y',
        ],
        'b': [
            'x',
        ],
        'method': 'allow_more_present',
        'type': 'set',
        'result': False
    },
    {
        'a': [
            'x',
        ],
        'b': [
            'x',
            'y',
        ],
        'method': 'allow_more_present',
        'type': 'set',
        'result': True
    },
    {
        'a': [
            'x',
            'x',
            'y',
        ],
        'b': [
            'x',
            'y',
        ],
        'method': 'allow_more_present',
        'type': 'set',
        'result': True
    },
    {
        'a': [
            'x',
            'z',
        ],
        'b': [
            'x',
            'y',
            'x',
            'z',
        ],
        'method': 'allow_more_present',
        'type': 'set',
        'result': True
    },
    {
        'a': [
            'x',
            'a',
        ],
        'b': [
            'y',
            'z',
        ],
        'method': 'ignore',
        'type': 'set',
        'result': True
    },
    ########################################################################################
    # set(dict)
    {
        'a': [
            {'x': 1},
        ],
        'b': [
            {'y': 1},
        ],
        'method': 'strict',
        'type': 'set(dict)',
        'result': False
    },
    {
        'a': [
            {'x': 1},
        ],
        'b': [
            {'x': 1},
        ],
        'method': 'strict',
        'type': 'set(dict)',
        'result': True
    },
    {
        'a': [
            {'x': 1},
        ],
        'b': [
            {'x': 1, 'y': 2},
        ],
        'method': 'strict',
        'type': 'set(dict)',
        'result': True
    },
    {
        'a': [
            {'x': 1},
            {'x': 2, 'y': 3},
        ],
        'b': [
            {'x': 1},
            {'x': 2, 'y': 3},
        ],
        'method': 'strict',
        'type': 'set(dict)',
        'result': True
    },
    {
        'a': [
            {'x': 1},
        ],
        'b': [
            {'x': 1, 'z': 2},
            {'x': 2, 'y': 3},
        ],
        'method': 'allow_more_present',
        'type': 'set(dict)',
        'result': True
    },
    {
        'a': [
            {'x': 1, 'y': 2},
        ],
        'b': [
            {'x': 1},
            {'x': 2, 'y': 3},
        ],
        'method': 'allow_more_present',
        'type': 'set(dict)',
        'result': False
    },
    {
        'a': [
            {'x': 1, 'y': 3},
        ],
        'b': [
            {'x': 1},
            {'x': 1, 'y': 3, 'z': 4},
        ],
        'method': 'allow_more_present',
        'type': 'set(dict)',
        'result': True
    },
    {
        'a': [
            {'x': 1},
            {'x': 2, 'y': 3},
        ],
        'b': [
            {'x': 1},
        ],
        'method': 'ignore',
        'type': 'set(dict)',
        'result': True
    },
    ########################################################################################
    # dict
    {
        'a': {'x': 1},
        'b': {'y': 1},
        'method': 'strict',
        'type': 'dict',
        'result': False
    },
    {
        'a': {'x': 1},
        'b': {'x': 1, 'y': 2},
        'method': 'strict',
        'type': 'dict',
        'result': False
    },
    {
        'a': {'x': 1},
        'b': {'x': 1},
        'method': 'strict',
        'type': 'dict',
        'result': True
    },
    {
        'a': {'x': 1, 'z': 2},
        'b': {'x': 1, 'y': 2},
        'method': 'strict',
        'type': 'dict',
        'result': False
    },
    {
        'a': {'x': 1, 'z': 2},
        'b': {'x': 1, 'y': 2},
        'method': 'ignore',
        'type': 'dict',
        'result': True
    },
] + [{
    'a': entry['av'],
    'b': entry['bv'],
    'method': 'allow_more_present',
    'type': 'dict',
    'result': entry['result']
} for entry in DICT_ALLOW_MORE_PRESENT]


@pytest.mark.parametrize("entry", DICT_ALLOW_MORE_PRESENT)
def test_dict_allow_more_present(entry):
    assert compare_dict_allow_more_present(entry['av'], entry['bv']) == entry['result']


@pytest.mark.parametrize("entry", COMPARE_GENERIC)
def test_compare_generic(entry):
    assert compare_generic(entry['a'], entry['b'], entry['method'], entry['type']) == entry['result']


def test_convert_duration_to_nanosecond():
    nanoseconds = convert_duration_to_nanosecond('5s')
    assert nanoseconds == 5000000000
    nanoseconds = convert_duration_to_nanosecond('1m5s')
    assert nanoseconds == 65000000000
    with pytest.raises(ValueError):
        convert_duration_to_nanosecond([1, 2, 3])
    with pytest.raises(ValueError):
        convert_duration_to_nanosecond('10x')


def test_parse_healthcheck():
    result, disabled = parse_healthcheck({
        'test': 'sleep 1',
        'interval': '1s',
    })
    assert disabled is False
    assert result == {
        'test': ['CMD-SHELL', 'sleep 1'],
        'interval': 1000000000
    }

    result, disabled = parse_healthcheck({
        'test': ['NONE'],
    })
    assert result is None
    assert disabled

    result, disabled = parse_healthcheck({
        'test': 'sleep 1',
        'interval': '1s423ms'
    })
    assert result == {
        'test': ['CMD-SHELL', 'sleep 1'],
        'interval': 1423000000
    }
    assert disabled is False

    result, disabled = parse_healthcheck({
        'test': 'sleep 1',
        'interval': '1h1m2s3ms4us'
    })
    assert result == {
        'test': ['CMD-SHELL', 'sleep 1'],
        'interval': 3662003004000
    }
    assert disabled is False


def get_docker_client():
    '''
    Avoid crash while instantiating AnsibleDockerClient in a test context.
    '''

    set_module_args(dict(
        api_version=DEFAULT_DOCKER_API_VERSION
    ))

    with patch.object(AnsibleDockerClient, 'version') as version:
        version.return_value = dict(
            ApiVersion=DEFAULT_DOCKER_API_VERSION
        )

        client = AnsibleDockerClient()

    return client


@pytest.mark.parametrize("config", CREDENTIAL_HELPERS)
def test_docker_credential_helpers(config):
    client = get_docker_client()

    try:
        store = client.get_credential_store_instance(EXAMPLE_REGISTRY, os.path.join(test_data_dir, config))

        assert type(store) == Store
    except InitializationError as e:
        pytest.skip("Credential helper not available.")


def test_docker_legacy_crednetials():
    client = get_docker_client()

    store = client.get_credential_store_instance(EXAMPLE_REGISTRY, os.path.join(test_data_dir, "none-config.json"))

    assert type(store) == DockerFileStore
    assert store.get(EXAMPLE_REGISTRY) == dict(
        Username="abc",
        Secret="123"
    )
