from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import pytest
import tempfile

from docker.constants import DEFAULT_DOCKER_API_VERSION

from units.modules.utils import patch, set_module_args
from ansible.module_utils import basic

from ansible.module_utils.docker.common import AnsibleDockerClient

from ansible.modules.cloud.docker.docker_login import (
    CredentialsNotFound,
    DockerFileStore,
    LoginManager,
    Store,
    StoreError,
)


curr_dir = os.path.dirname(__file__)
test_data_dir = os.path.join(curr_dir, "test_data")

EXAMPLE_REGISTRY = "registry.example.com"
CREDENTIAL_HELPERS = [
    'desktop-config.json',
    'osxkeychain-config.json',
    'secretservice-config.json'
]


@pytest.fixture()
def login_manager():
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

    results = dict(
        changed=False,
        actions=[],
        login_result={}
    )

    return LoginManager(client, results)


@pytest.fixture()
def docker_file_store():
    temp = tempfile.NamedTemporaryFile()
    return DockerFileStore(temp.name)


@pytest.mark.parametrize("config", CREDENTIAL_HELPERS)
def test_docker_credential_helpers(config, login_manager):
    '''
    Verify that LoginManager can return a proper Store
    when asked for a crednetial store that should point to
    a credential helper.
    '''

    try:
        store = login_manager.get_credential_store_instance(
            EXAMPLE_REGISTRY,
            os.path.join(test_data_dir, config)
        )

        assert type(store) == Store
    except StoreError as e:
        pytest.skip("Credential helper not available.")


def test_docker_legacy_crednetials(login_manager):
    '''
    Verify that LoginManager and the associated DockerFileStore
    can read from a previously existing config.json
    '''

    store = login_manager.get_credential_store_instance(
        EXAMPLE_REGISTRY,
        os.path.join(test_data_dir, "none-config.json")
    )

    assert type(store) == DockerFileStore
    assert store.get(EXAMPLE_REGISTRY) == dict(
        Username="abc",
        Secret="123"
    )


def test_dfs_missing(docker_file_store):
    '''
    Verify that we can detect that a registry is not
    configured in the config.json
    '''

    with pytest.raises(CredentialsNotFound):
        missing_auth = docker_file_store.get(EXAMPLE_REGISTRY)


def test_dfs_write(docker_file_store):
    '''
    Verify that DockerFileStore is able to write a sane config.json file.
    '''

    fname = docker_file_store.config_path

    # Test that store works as expected.
    docker_file_store.store(EXAMPLE_REGISTRY, 'abc', '123')

    actual = json.load(open(fname, "r"))
    expected = {
        "auths": {
            EXAMPLE_REGISTRY: {
                "auth": "YWJjOjEyMw=="
            }
        }
    }

    assert actual == expected

    # Test that erase works as expected.
    docker_file_store.erase(EXAMPLE_REGISTRY)

    actual = json.load(open(fname, "r"))
    expected = {
        "auths": dict()
    }

    assert actual == expected
