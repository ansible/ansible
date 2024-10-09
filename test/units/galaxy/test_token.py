# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock

import ansible.constants as C
from ansible.cli.galaxy import GalaxyCLI
from ansible.config import manager
from ansible.galaxy.token import GalaxyToken, NoTokenSentinel
from ansible.module_utils.common.text.converters import to_bytes, to_text


@pytest.fixture()
def b_token_file(request, tmp_path_factory):
    b_test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Token'))
    b_token_path = os.path.join(b_test_dir, b"token.yml")

    token = getattr(request, 'param', None)
    if token:
        with open(b_token_path, 'wb') as token_fd:
            token_fd.write(b"token: %s" % to_bytes(token))

    orig_token_path = C.GALAXY_TOKEN_PATH
    C.GALAXY_TOKEN_PATH = to_text(b_token_path)
    try:
        yield b_token_path
    finally:
        C.GALAXY_TOKEN_PATH = orig_token_path


def test_client_id(monkeypatch):
    monkeypatch.setattr(C, 'GALAXY_SERVER_LIST', ['server1', 'server2'])

    test_server_config = {option[0]: None for option in manager.GALAXY_SERVER_DEF}
    test_server_config.update(
        {
            'url': 'http://my_galaxy_ng:8000/api/automation-hub/',
            'auth_url': 'http://my_keycloak:8080/auth/realms/myco/protocol/openid-connect/token',
            'client_id': 'galaxy-ng',
            'token': 'access_token',
        }
    )

    test_server_default = {option[0]: None for option in manager.GALAXY_SERVER_DEF}
    test_server_default.update(
        {
            'url': 'https://cloud.redhat.com/api/automation-hub/',
            'auth_url': 'https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token',
            'token': 'access_token',
        }
    )

    get_plugin_options = MagicMock(side_effect=[test_server_config, test_server_default])
    monkeypatch.setattr(C.config, 'get_plugin_options', get_plugin_options)

    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
    galaxy_cli.run()

    assert galaxy_cli.api_servers[0].token.client_id == 'galaxy-ng'
    assert galaxy_cli.api_servers[1].token.client_id == 'cloud-services'


def test_token_explicit(b_token_file):
    assert GalaxyToken(token="explicit").get() == "explicit"


@pytest.mark.parametrize('b_token_file', ['file'], indirect=True)
def test_token_explicit_override_file(b_token_file):
    assert GalaxyToken(token="explicit").get() == "explicit"


@pytest.mark.parametrize('b_token_file', ['file'], indirect=True)
def test_token_from_file(b_token_file):
    assert GalaxyToken().get() == "file"


def test_token_from_file_missing(b_token_file):
    assert GalaxyToken().get() is None


@pytest.mark.parametrize('b_token_file', ['file'], indirect=True)
def test_token_none(b_token_file):
    assert GalaxyToken(token=NoTokenSentinel).get() is None
