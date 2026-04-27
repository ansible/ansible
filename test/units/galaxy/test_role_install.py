# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import json
import os
import functools
import pytest
import tempfile

from io import StringIO
from ansible import context
from ansible.cli.galaxy import GalaxyCLI
from ansible.galaxy import api, role, Galaxy
from ansible.module_utils.common.text.converters import to_text
from ansible.utils import context_objects as co


def call_galaxy_cli(args):
    orig = co.GlobalCLIArgs._Singleton__instance
    co.GlobalCLIArgs._Singleton__instance = None
    try:
        return GalaxyCLI(args=['ansible-galaxy', 'role'] + args).run()
    finally:
        co.GlobalCLIArgs._Singleton__instance = orig


@pytest.fixture(autouse=True)
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


@pytest.fixture(autouse=True)
def galaxy_server():
    context.CLIARGS._store = {'ignore_certs': False}
    galaxy_api = api.GalaxyAPI(None, 'test_server', 'https://galaxy.ansible.com')
    return galaxy_api


@pytest.fixture(autouse=True)
def init_role_dir(tmp_path_factory):
    test_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Roles Input'))
    namespace = 'ansible_namespace'
    role = 'role'
    skeleton_path = os.path.join(os.path.dirname(os.path.split(__file__)[0]), 'cli', 'test_data', 'role_skeleton')
    call_galaxy_cli(['init', '%s.%s' % (namespace, role), '-c', '--init-path', test_dir, '--role-skeleton', skeleton_path])


def mock_NamedTemporaryFile(mocker, **args):
    mock_ntf = mocker.MagicMock()
    mock_ntf.write = mocker.MagicMock()
    mock_ntf.close = mocker.MagicMock()
    mock_ntf.name = None
    return mock_ntf


@pytest.fixture
def init_mock_temp_file(mocker, monkeypatch):
    monkeypatch.setattr(tempfile, 'NamedTemporaryFile', functools.partial(mock_NamedTemporaryFile, mocker))


@pytest.fixture(autouse=True)
def mock_role_download_api(mocker, monkeypatch):
    mock_role_api = mocker.MagicMock()
    mock_role_api.side_effect = [
        StringIO(u''),
    ]
    monkeypatch.setattr(role, 'open_url', mock_role_api)
    return mock_role_api


def test_role_download_github(init_mock_temp_file, mocker, galaxy_server, mock_role_download_api, monkeypatch):
    mock_api = mocker.MagicMock()
    mock_api.side_effect = [
        StringIO(u'{"available_versions":{"v1":"v1/"}}'),
        StringIO(u'{"results":[{"id":"123","github_user":"test_owner","github_repo": "test_role"}]}'),
        StringIO(u'{"results":[{"name": "0.0.1"},{"name": "0.0.2"}]}'),
    ]
    monkeypatch.setattr(api, 'open_url', mock_api)

    role.GalaxyRole(Galaxy(), galaxy_server, 'test_owner.test_role', version="0.0.1").install()

    assert mock_role_download_api.call_count == 1
    assert mock_role_download_api.mock_calls[0][1][0] == 'https://github.com/test_owner/test_role/archive/0.0.1.tar.gz'


def test_role_download_github_default_version(init_mock_temp_file, mocker, galaxy_server, mock_role_download_api, monkeypatch):
    mock_api = mocker.MagicMock()
    mock_api.side_effect = [
        StringIO(u'{"available_versions":{"v1":"v1/"}}'),
        StringIO(u'{"results":[{"id":"123","github_user":"test_owner","github_repo": "test_role"}]}'),
        StringIO(u'{"results":[{"name": "0.0.1"},{"name": "0.0.2"}]}'),
    ]
    monkeypatch.setattr(api, 'open_url', mock_api)

    role.GalaxyRole(Galaxy(), galaxy_server, 'test_owner.test_role').install()

    assert mock_role_download_api.call_count == 1
    assert mock_role_download_api.mock_calls[0][1][0] == 'https://github.com/test_owner/test_role/archive/0.0.2.tar.gz'


def test_role_download_github_no_download_url_for_version(init_mock_temp_file, mocker, galaxy_server, mock_role_download_api, monkeypatch):
    mock_api = mocker.MagicMock()
    mock_api.side_effect = [
        StringIO(u'{"available_versions":{"v1":"v1/"}}'),
        StringIO(u'{"results":[{"id":"123","github_user":"test_owner","github_repo": "test_role"}]}'),
        StringIO(u'{"results":[{"name": "0.0.1"},{"name": "0.0.2","download_url":"http://localhost:8080/test_owner/test_role/0.0.2.tar.gz"}]}'),
    ]
    monkeypatch.setattr(api, 'open_url', mock_api)

    role.GalaxyRole(Galaxy(), galaxy_server, 'test_owner.test_role', version="0.0.1").install()

    assert mock_role_download_api.call_count == 1
    assert mock_role_download_api.mock_calls[0][1][0] == 'https://github.com/test_owner/test_role/archive/0.0.1.tar.gz'


@pytest.mark.parametrize(
    'state,rc',
    [('SUCCESS', 0), ('FAILED', 1),]
)
def test_role_import(state, rc, mocker, galaxy_server, monkeypatch):
    responses = [
        {"available_versions": {"v1": "v1/"}},
        {"results": [{'id': 12345, 'github_user': 'user', 'github_repo': 'role', 'github_reference': None, 'summary_fields': {'role': {'name': 'role'}}}]},
        {"results": [{'state': 'WAITING', 'id': 12345, 'summary_fields': {'task_messages': []}}]},
        {"results": [{'state': state, 'id': 12345, 'summary_fields': {'task_messages': []}}]},
    ]
    mock_api = mocker.MagicMock(side_effect=[StringIO(json.dumps(rsp)) for rsp in responses])
    monkeypatch.setattr(api, 'open_url', mock_api)
    monkeypatch.setattr(GalaxyCLI, '_task_check_delay_sec', 0.1)
    assert call_galaxy_cli(['import', 'user', 'role']) == rc


def test_role_download_url(init_mock_temp_file, mocker, galaxy_server, mock_role_download_api, monkeypatch):
    mock_api = mocker.MagicMock()
    mock_api.side_effect = [
        StringIO(u'{"available_versions":{"v1":"v1/"}}'),
        StringIO(u'{"results":[{"id":"123","github_user":"test_owner","github_repo": "test_role"}]}'),
        StringIO(u'{"results":[{"name": "0.0.1","download_url":"http://localhost:8080/test_owner/test_role/0.0.1.tar.gz"},'
                 u'{"name": "0.0.2","download_url":"http://localhost:8080/test_owner/test_role/0.0.2.tar.gz"}]}'),
    ]
    monkeypatch.setattr(api, 'open_url', mock_api)

    role.GalaxyRole(Galaxy(), galaxy_server, 'test_owner.test_role', version="0.0.1").install()

    assert mock_role_download_api.call_count == 1
    assert mock_role_download_api.mock_calls[0][1][0] == 'http://localhost:8080/test_owner/test_role/0.0.1.tar.gz'


def test_role_download_url_default_version(init_mock_temp_file, mocker, galaxy_server, mock_role_download_api, monkeypatch):
    mock_api = mocker.MagicMock()
    mock_api.side_effect = [
        StringIO(u'{"available_versions":{"v1":"v1/"}}'),
        StringIO(u'{"results":[{"id":"123","github_user":"test_owner","github_repo": "test_role"}]}'),
        StringIO(u'{"results":[{"name": "0.0.1","download_url":"http://localhost:8080/test_owner/test_role/0.0.1.tar.gz"},'
                 u'{"name": "0.0.2","download_url":"http://localhost:8080/test_owner/test_role/0.0.2.tar.gz"}]}'),
    ]
    monkeypatch.setattr(api, 'open_url', mock_api)

    role.GalaxyRole(Galaxy(), galaxy_server, 'test_owner.test_role').install()

    assert mock_role_download_api.call_count == 1
    assert mock_role_download_api.mock_calls[0][1][0] == 'http://localhost:8080/test_owner/test_role/0.0.2.tar.gz'
