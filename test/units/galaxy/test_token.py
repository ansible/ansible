# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import os
import pytest

from datetime import datetime, timedelta, timezone
from io import StringIO
from unittest.mock import MagicMock

import ansible.constants as C
from ansible.cli.galaxy import GalaxyCLI, SERVER_DEF
from ansible.galaxy.token import GalaxyToken, NoTokenSentinel, KeycloakToken
from ansible.galaxy.token import ISO_8601_FORMAT_STR as time_format
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

    test_server_config = {option[0]: None for option in SERVER_DEF}
    test_server_config.update(
        {
            'url': 'http://my_galaxy_ng:8000/api/automation-hub/',
            'auth_url': 'http://my_keycloak:8080/auth/realms/myco/protocol/openid-connect/token',
            'client_id': 'galaxy-ng',
            'token': 'access_token',
        }
    )

    test_server_default = {option[0]: None for option in SERVER_DEF}
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


def test_keycloak_token_not_expired(monkeypatch):
    expires_in_2_min = int((datetime.now(tz=timezone.utc) + timedelta(minutes=2)).timestamp())
    token_payload = to_text(base64.b64encode(to_bytes(f'{{"exp": {expires_in_2_min}}}')))

    with StringIO(f'{{"access_token": "token", "id_token": "header.{token_payload}.signature"}}') as response:
        mock_open = MagicMock(return_value=response)
        monkeypatch.setattr(token_file, 'open_url', mock_open)
        token = KeycloakToken(access_token='', auth_url='')
        token.get()
        assert token.expired is False


def test_keycloak_token_expired(monkeypatch):
    expired_earlier = int((datetime.now(tz=timezone.utc) - timedelta(minutes=15)).timestamp())
    token_payload = to_text(base64.b64encode(to_bytes(f'{{"exp": {expired_earlier}}}')))
    response1 = f'{{"access_token": "token", "id_token": "header.{token_payload}.signature"}}'

    almost_expired = int((datetime.now(tz=timezone.utc) + timedelta(minutes=1)).timestamp())
    token_payload = to_text(base64.b64encode(to_bytes(f'{{"exp": {almost_expired}}}')))
    response2 = f'{{"access_token": "token", "id_token": "header.{token_payload}.signature"}}'

    with StringIO(response1) as resp1, StringIO(response2) as resp2:
        mock_open = MagicMock(side_effect=[resp1, resp2])
        monkeypatch.setattr(token_file, 'open_url', mock_open)
        token = KeycloakToken(access_token='', auth_url='')
        token.get()
        assert token.expired
        token.get()
        assert token.expired
