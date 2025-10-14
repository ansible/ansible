# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import os
import re
import pytest
import stat
import tarfile
import tempfile
import time

from io import BytesIO, StringIO
from unittest.mock import MagicMock

import ansible.constants as C
from ansible import context
from ansible.errors import AnsibleError
from ansible.galaxy import api as galaxy_api
from ansible.galaxy.api import CollectionVersionMetadata, GalaxyAPI, GalaxyError
from ansible.galaxy.token import BasicAuthToken, GalaxyToken, KeycloakToken
from ansible.module_utils.common.file import S_IRWU_RG_RO
from ansible.module_utils.common.text.converters import to_native, to_text
import urllib.error
from ansible.utils import context_objects as co
from ansible.utils.display import Display


@pytest.fixture(autouse=True)
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    # Required to initialise the GalaxyAPI object
    context.CLIARGS._store = {'ignore_certs': False}
    yield
    co.GlobalCLIArgs._Singleton__instance = None


@pytest.fixture()
def collection_artifact(tmp_path_factory):
    """ Creates a collection artifact tarball that is ready to be published """
    output_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Output'))

    tar_path = os.path.join(output_dir, 'namespace-collection-v1.0.0.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tfile:
        b_io = BytesIO(b"\x00\x01\x02\x03")
        tar_info = tarfile.TarInfo('test')
        tar_info.size = 4
        tar_info.mode = S_IRWU_RG_RO
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    yield tar_path


@pytest.fixture()
def cache_dir(tmp_path_factory, monkeypatch):
    cache_dir = to_text(tmp_path_factory.mktemp('Test ÅÑŚÌβŁÈ Galaxy Cache'))
    monkeypatch.setattr(C, 'GALAXY_CACHE_DIR', cache_dir)

    yield cache_dir


def get_test_galaxy_api(url, version, token_ins=None, token_value=None, no_cache=True):
    token_value = token_value or "my token"
    token_ins = token_ins or GalaxyToken(token_value)
    api = GalaxyAPI(None, "test", url, no_cache=no_cache)
    # Warning, this doesn't test g_connect() because _available_api_versions is set here.  That means
    # that urls for v2 servers have to append '/api/' themselves in the input data.
    api._available_api_versions = {version: '%s' % version}
    api.token = token_ins

    return api


def get_v3_collection_versions(namespace='namespace', name='collection'):
    pagination_path = f"/api/galaxy/content/community/v3/plugin/{namespace}/content/community/collections/index/{namespace}/{name}/versions"
    page_versions = (('1.0.0', '1.0.1',), ('1.0.2', '1.0.3',), ('1.0.4', '1.0.5'),)
    responses = [
        {},  # TODO: initial response
    ]

    first = f"{pagination_path}/?limit=100"
    last = f"{pagination_path}/?limit=100&offset=200"
    page_versions = [
        {
            "versions": ('1.0.0', '1.0.1',),
            "url": first,
        },
        {
            "versions": ('1.0.2', '1.0.3',),
            "url": f"{pagination_path}/?limit=100&offset=100",
        },
        {
            "versions": ('1.0.4', '1.0.5'),
            "url": last,
        },
    ]

    previous = None
    for page in range(0, len(page_versions)):
        data = []

        if page_versions[page]["url"] == last:
            next_page = None
        else:
            next_page = page_versions[page + 1]["url"]
        links = {"first": first, "last": last, "next": next_page, "previous": previous}

        for version in page_versions[page]["versions"]:
            data.append(
                {
                    "version": f"{version}",
                    "href": f"{pagination_path}/{version}/",
                    "created_at": "2022-05-13T15:55:58.913107Z",
                    "updated_at": "2022-05-13T15:55:58.913121Z",
                    "requires_ansible": ">=2.9.10"
                }
            )

        responses.append({"meta": {"count": 6}, "links": links, "data": data})

        previous = page_versions[page]["url"]
    return responses


def get_collection_versions(namespace='namespace', name='collection'):
    base_url = f'/api/v3/plugin/ansible/content/published/collections/index/{namespace}/{name}/'
    versions_url = f'{base_url}versions/'

    # Response for collection info
    responses = [
        {
            "href": base_url,
            "name": name,
            "namespace": namespace,
            "highest_version": {
                "href": f"{versions_url}1.0.5",
                "version": "1.0.5",
            },
            "versions_url": versions_url,
            "deprecated": False,
            "created_at": "2021-02-09T16:55:42.749915-05:00",
            "updated_at": "2021-02-09T16:55:42.749915-05:00",
        }
    ]

    # Paginated responses for versions
    page_versions = (('1.0.0', '1.0.1',), ('1.0.2', '1.0.3',), ('1.0.4', '1.0.5'),)
    prev_page = None
    for page in range(1, len(page_versions) + 1):
        if page < len(page_versions):
            next_page = f'{versions_url}?limit=2&offset={page + 1}'
        else:
            next_page = None

        version_results = []
        for version in page_versions[int(page - 1)]:
            version_results.append(
                {'version': version, 'href': versions_url + '{0}/'.format(version)}
            )

        responses.append(
            {
                'meta': {
                    'count': 6,
                },
                'links': {
                    'first': f'{versions_url}?limit=2&offset=0',
                    'next': next_page,
                    'previous': prev_page,
                    'last': f'{versions_url}?limit=2&offset={len(page_versions)}',
                },
                'data': version_results,
            }
        )
        prev_page = page

    return responses


def test_api_no_auth():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/")
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {}


def test_api_no_auth_but_required():
    expected = "No access token or username set. A token can be set with --api-key or at "
    with pytest.raises(AnsibleError, match=expected):
        GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/")._add_auth_token({}, "", required=True)


def test_api_token_auth():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=token)
    actual = {}
    api._add_auth_token(actual, "", required=True)
    assert actual == {'Authorization': 'Token my_token'}


def test_api_token_auth_with_token_type(monkeypatch):
    token = KeycloakToken(auth_url='https://api.test/')
    mock_token_get = MagicMock()
    mock_token_get.return_value = 'my_token'
    monkeypatch.setattr(token, 'get', mock_token_get)
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=token)
    actual = {}
    api._add_auth_token(actual, "", token_type="Bearer", required=True)
    assert actual == {'Authorization': 'Bearer my_token'}


def test_api_token_auth_with_v3_url(monkeypatch):
    token = KeycloakToken(auth_url='https://api.test/')
    mock_token_get = MagicMock()
    mock_token_get.return_value = 'my_token'
    monkeypatch.setattr(token, 'get', mock_token_get)
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=token)
    actual = {}
    api._add_auth_token(actual, "https://galaxy.ansible.com/api/v3/resource/name", required=True)
    assert actual == {'Authorization': 'Bearer my_token'}


def test_api_token_auth_with_v2_url():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=token)
    actual = {}
    # Add v3 to random part of URL but response should only see the v2 as the full URI path segment.
    api._add_auth_token(actual, "https://galaxy.ansible.com/api/v2/resourcev3/name", required=True)
    assert actual == {'Authorization': 'Token my_token'}


def test_api_basic_auth_password():
    token = BasicAuthToken(username=u"user", password=u"pass")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=token)
    actual = {}
    api._add_auth_token(actual, "", required=True)
    assert actual == {'Authorization': 'Basic dXNlcjpwYXNz'}


def test_api_basic_auth_no_password():
    token = BasicAuthToken(username=u"user")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=token)
    actual = {}
    api._add_auth_token(actual, "", required=True)
    assert actual == {'Authorization': 'Basic dXNlcjo='}


def test_api_dont_override_auth_header():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/")
    actual = {'Authorization': 'Custom token'}
    api._add_auth_token(actual, "", required=True)
    assert actual == {'Authorization': 'Custom token'}


def test_initialise_galaxy(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(u'{"available_versions":{"v1":"v1/"}}'),
        StringIO(u'{"token":"my token"}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/")
    actual = api.authenticate("github_token")

    assert len(api.available_api_versions) == 1
    assert api.available_api_versions['v1'] == u'v1/'
    assert actual == {u'token': u'my token'}
    assert mock_open.call_count == 2
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api/'
    assert 'ansible-galaxy' in mock_open.mock_calls[0][2]['http_agent']
    assert mock_open.mock_calls[1][1][0] == 'https://galaxy.ansible.com/api/v1/tokens/'
    assert 'ansible-galaxy' in mock_open.mock_calls[1][2]['http_agent']
    assert mock_open.mock_calls[1][2]['data'] == 'github_token=github_token'


def test_initialise_galaxy_with_auth(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(u'{"available_versions":{"v1":"v1/"}}'),
        StringIO(u'{"token":"my token"}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=GalaxyToken(token='my_token'))
    actual = api.authenticate("github_token")

    assert len(api.available_api_versions) == 1
    assert api.available_api_versions['v1'] == u'v1/'
    assert actual == {u'token': u'my token'}
    assert mock_open.call_count == 2
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api/'
    assert 'ansible-galaxy' in mock_open.mock_calls[0][2]['http_agent']
    assert mock_open.mock_calls[1][1][0] == 'https://galaxy.ansible.com/api/v1/tokens/'
    assert 'ansible-galaxy' in mock_open.mock_calls[1][2]['http_agent']
    assert mock_open.mock_calls[1][2]['data'] == 'github_token=github_token'


def test_initialise_automation_hub(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(u'{"available_versions":{"v3":"v3/"}}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)
    token = KeycloakToken(auth_url='https://api.test/')
    mock_token_get = MagicMock()
    mock_token_get.return_value = 'my_token'
    monkeypatch.setattr(token, 'get', mock_token_get)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=token)

    assert len(api.available_api_versions) == 1
    assert api.available_api_versions['v3'] == u'v3/'

    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api/'
    assert 'ansible-galaxy' in mock_open.mock_calls[0][2]['http_agent']
    assert mock_open.mock_calls[0][2]['headers'] == {'Authorization': 'Bearer my_token'}


def test_initialise_unknown(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        urllib.error.HTTPError('https://galaxy.ansible.com/api/', 500, 'msg', {}, StringIO(u'{"msg":"raw error"}')),
        urllib.error.HTTPError('https://galaxy.ansible.com/api/api/', 500, 'msg', {}, StringIO(u'{"msg":"raw error"}')),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/", token=GalaxyToken(token='my_token'))

    expected = "Error when finding available api versions from test (%s) (HTTP Code: 500, Message: msg)" \
        % api.api_server
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        api.authenticate("github_token")


def test_get_available_api_versions(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(u'{"available_versions":{"v1":"v1/","v3":"v3/"}}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/")
    actual = api.available_api_versions
    assert len(actual) == 2
    assert actual['v1'] == u'v1/'
    assert actual['v3'] == u'v3/'

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api/'
    assert 'ansible-galaxy' in mock_open.mock_calls[0][2]['http_agent']


def test_publish_collection_missing_file():
    fake_path = u'/fake/ÅÑŚÌβŁÈ/path'
    expected = to_native("The collection path specified '%s' does not exist." % fake_path)

    api = get_test_galaxy_api("https://galaxy.ansible.com/api/", "v3")
    with pytest.raises(AnsibleError, match=expected):
        api.publish_collection(fake_path)


def test_publish_collection_not_a_tarball():
    expected = "The collection path specified '{0}' is not a tarball, use 'ansible-galaxy collection build' to " \
               "create a proper release artifact."

    api = get_test_galaxy_api("https://galaxy.ansible.com/api/", "v3")
    with tempfile.NamedTemporaryFile(prefix=u'ÅÑŚÌβŁÈ') as temp_file:
        temp_file.write(b"\x00")
        temp_file.flush()
        with pytest.raises(AnsibleError, match=expected.format(to_native(temp_file.name))):
            api.publish_collection(temp_file.name)


def test_publish_collection_unsupported_version():
    expected = "Galaxy action publish_collection requires API versions 'v3' but only 'v1' are available on test " \
               "https://galaxy.ansible.com/api/"

    api = get_test_galaxy_api("https://galaxy.ansible.com/api/", "v1")
    with pytest.raises(AnsibleError, match=expected):
        api.publish_collection("path")


@pytest.mark.parametrize('api_version, collection_url', [
    ('v3', 'artifacts/collections'),
])
def test_publish_collection(api_version, collection_url, collection_artifact, monkeypatch):
    api = get_test_galaxy_api("https://galaxy.ansible.com/api/", api_version)

    mock_call = MagicMock()
    mock_call.return_value = {'task': 'http://task.url/'}
    monkeypatch.setattr(api, '_call_galaxy', mock_call)

    actual = api.publish_collection(collection_artifact)
    assert actual == 'http://task.url/'
    assert mock_call.call_count == 1
    assert mock_call.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api/%s/%s/' % (api_version, collection_url)
    assert mock_call.mock_calls[0][2]['headers']['Content-length'] == len(mock_call.mock_calls[0][2]['args'])
    assert mock_call.mock_calls[0][2]['headers']['Content-type'].startswith(
        'multipart/form-data; boundary=')
    assert mock_call.mock_calls[0][2]['args'].startswith(b'--')
    assert mock_call.mock_calls[0][2]['method'] == 'POST'
    assert mock_call.mock_calls[0][2]['auth_required'] is True


@pytest.mark.parametrize('api_version, collection_url, response, expected', [
    ('v3', 'artifact/collections', {},
     'Error when publishing collection to test (%s) (HTTP Code: 500, Message: msg Code: Unknown)'),
    ('v3', 'artifact/collections', {
        'errors': [
            {
                'code': 'conflict.collection_exists',
                'detail': 'Collection "mynamespace-mycollection-4.1.1" already exists.',
                'title': 'Conflict.',
                'status': '400',
            },
            {
                'code': 'quantum_improbability',
                'title': u'Rändom(?) quantum improbability.',
                'source': {'parameter': 'the_arrow_of_time'},
                'meta': {'remediation': 'Try again before'},
            },
        ],
    }, u'Error when publishing collection to test (%s) (HTTP Code: 500, Message: Collection '
       u'"mynamespace-mycollection-4.1.1" already exists. Code: conflict.collection_exists), (HTTP Code: 500, '
       u'Message: Rändom(?) quantum improbability. Code: quantum_improbability)')
])
def test_publish_failure(api_version, collection_url, response, expected, collection_artifact, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com/api/', api_version)

    expected_url = '%s/api/%s/%s' % (api.api_server, api_version, collection_url)

    mock_open = MagicMock()
    mock_open.side_effect = urllib.error.HTTPError(expected_url, 500, 'msg', {},
                                                   StringIO(to_text(json.dumps(response))))
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    with pytest.raises(GalaxyError, match=re.escape(to_native(expected % api.api_server))):
        api.publish_collection(collection_artifact)


@pytest.mark.parametrize('server_url, api_version, token_type, token_ins, full_import_uri', [
    ('https://galaxy.server.com/api/automation-hub/', 'v3', 'Bearer', KeycloakToken(auth_url='https://api.test/'),
     'https://galaxy.server.com/api/automation-hub/v3/imports/collections/1234/'),
])
def test_wait_import_task(server_url, api_version, token_type, token_ins, full_import_uri, monkeypatch):
    api = get_test_galaxy_api(server_url, api_version, token_ins=token_ins)

    mock_token_get = MagicMock()
    mock_token_get.return_value = 'my token'
    monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.return_value = StringIO(u'{"state":"success","finished_at":"time"}')
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    api.wait_import_task(full_import_uri)

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == full_import_uri
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == 'Waiting until Galaxy import task %s has completed' % full_import_uri


@pytest.mark.parametrize('server_url, api_version, token_type, token_ins, full_import_uri', [
    ('https://galaxy.server.com/api/automation-hub', 'v3', 'Bearer', KeycloakToken(auth_url='https://api.test/'),
     'https://galaxy.server.com/api/automation-hub/v3/imports/collections/1234/'),
])
def test_wait_import_task_multiple_requests(server_url, api_version, token_type, token_ins, full_import_uri, monkeypatch):
    api = get_test_galaxy_api(server_url, api_version, token_ins=token_ins)

    mock_token_get = MagicMock()
    mock_token_get.return_value = 'my token'
    monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(u'{"state":"test"}'),
        StringIO(u'{"state":"success","finished_at":"time"}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_vvv = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_vvv)

    monkeypatch.setattr(time, 'sleep', MagicMock())

    api.wait_import_task(full_import_uri)

    assert mock_open.call_count == 2
    assert mock_open.mock_calls[0][1][0] == full_import_uri
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type
    assert mock_open.mock_calls[1][1][0] == full_import_uri
    assert mock_open.mock_calls[1][2]['headers']['Authorization'] == '%s my token' % token_type

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == 'Waiting until Galaxy import task %s has completed' % full_import_uri

    assert mock_vvv.call_count == 1
    assert mock_vvv.mock_calls[0][1][0] == \
        'Galaxy import process has a status of test, wait 2 seconds before trying again'


@pytest.mark.parametrize('server_url, api_version, token_type, token_ins, full_import_uri,', [
    ('https://galaxy.server.com/api/automation-hub/', 'v3', 'Bearer', KeycloakToken(auth_url='https://api.test/'),
     'https://galaxy.server.com/api/automation-hub/v3/imports/collections/1234/'),
])
def test_wait_import_task_with_failure(server_url, api_version, token_type, token_ins, full_import_uri, monkeypatch):
    api = get_test_galaxy_api(server_url, api_version, token_ins=token_ins)

    mock_token_get = MagicMock()
    mock_token_get.return_value = 'my token'
    monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(to_text(json.dumps({
            'finished_at': 'some_time',
            'state': 'failed',
            'error': {
                'code': 'GW001',
                'description': u'Becäuse I said so!',

            },
            'messages': [
                {
                    'level': 'ERrOR',
                    'message': u'Somé error',
                },
                {
                    'level': 'WARNiNG',
                    'message': u'Some wärning',
                },
                {
                    'level': 'INFO',
                    'message': u'Somé info',
                },
            ],
        }))),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_vvv = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_vvv)

    mock_warn = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_warn)

    mock_err = MagicMock()
    monkeypatch.setattr(Display, 'error', mock_err)

    expected = to_native(u'Galaxy import process failed: Becäuse I said so! (Code: GW001)')
    with pytest.raises(AnsibleError, match=re.escape(expected)):
        api.wait_import_task(full_import_uri)

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == full_import_uri
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == 'Waiting until Galaxy import task %s has completed' % full_import_uri

    assert mock_vvv.call_count == 1
    assert mock_vvv.mock_calls[0][1][0] == u'Galaxy import message: INFO - Somé info'

    assert mock_warn.call_count == 1
    assert mock_warn.mock_calls[0][1][0] == u'Galaxy import warning message: Some wärning'

    assert mock_err.call_count == 1
    assert mock_err.mock_calls[0][1][0] == u'Galaxy import error message: Somé error'


@pytest.mark.parametrize('server_url, api_version, token_type, token_ins, full_import_uri', [
    ('https://galaxy.server.com/api/automation-hub/', 'v3', 'Bearer', KeycloakToken(auth_url='https://api.test/'),
     'https://galaxy.server.com/api/automation-hub/v3/imports/collections/1234/'),
])
def test_wait_import_task_with_failure_no_error(server_url, api_version, token_type, token_ins, full_import_uri, monkeypatch):
    api = get_test_galaxy_api(server_url, api_version, token_ins=token_ins)

    mock_token_get = MagicMock()
    mock_token_get.return_value = 'my token'
    monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(to_text(json.dumps({
            'finished_at': 'some_time',
            'state': 'failed',
            'error': {},
            'messages': [
                {
                    'level': 'ERROR',
                    'message': u'Somé error',
                },
                {
                    'level': 'WARNING',
                    'message': u'Some wärning',
                },
                {
                    'level': 'INFO',
                    'message': u'Somé info',
                },
            ],
        }))),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_vvv = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_vvv)

    mock_warn = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_warn)

    mock_err = MagicMock()
    monkeypatch.setattr(Display, 'error', mock_err)

    expected = 'Galaxy import process failed: Unknown error, see %s for more details \\(Code: UNKNOWN\\)' % full_import_uri
    with pytest.raises(AnsibleError, match=expected):
        api.wait_import_task(full_import_uri)

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == full_import_uri
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == 'Waiting until Galaxy import task %s has completed' % full_import_uri

    assert mock_vvv.call_count == 1
    assert mock_vvv.mock_calls[0][1][0] == u'Galaxy import message: INFO - Somé info'

    assert mock_warn.call_count == 1
    assert mock_warn.mock_calls[0][1][0] == u'Galaxy import warning message: Some wärning'

    assert mock_err.call_count == 1
    assert mock_err.mock_calls[0][1][0] == u'Galaxy import error message: Somé error'


@pytest.mark.parametrize('server_url, api_version, token_type, token_ins, full_import_uri', [
    ('https://galaxy.server.com/api/automation-hub', 'v3', 'Bearer', KeycloakToken(auth_url='https://api.test/'),
     'https://galaxy.server.com/api/automation-hub/v3/imports/collections/1234/'),
])
def test_wait_import_task_timeout(server_url, api_version, token_type, token_ins, full_import_uri, monkeypatch):
    api = get_test_galaxy_api(server_url, api_version, token_ins=token_ins)

    mock_token_get = MagicMock()
    mock_token_get.return_value = 'my token'
    monkeypatch.setattr(token_ins, 'get', mock_token_get)

    def return_response(*args, **kwargs):
        return StringIO(u'{"state":"waiting"}')

    mock_open = MagicMock()
    mock_open.side_effect = return_response
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    mock_vvv = MagicMock()
    monkeypatch.setattr(Display, 'vvv', mock_vvv)

    monkeypatch.setattr(time, 'sleep', MagicMock())

    expected = "Timeout while waiting for the Galaxy import process to finish, check progress at '%s'" % full_import_uri
    with pytest.raises(AnsibleError, match=expected):
        api.wait_import_task(full_import_uri, 1)

    assert mock_open.call_count > 1
    assert mock_open.mock_calls[0][1][0] == full_import_uri
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type
    assert mock_open.mock_calls[1][1][0] == full_import_uri
    assert mock_open.mock_calls[1][2]['headers']['Authorization'] == '%s my token' % token_type

    assert mock_display.call_count == 1
    assert mock_display.mock_calls[0][1][0] == 'Waiting until Galaxy import task %s has completed' % full_import_uri

    # expected_wait_msg = 'Galaxy import process has a status of waiting, wait {0} seconds before trying again'
    assert mock_vvv.call_count > 9  # 1st is opening Galaxy token file.

    # FIXME:
    # assert mock_vvv.mock_calls[1][1][0] == expected_wait_msg.format(2)
    # assert mock_vvv.mock_calls[2][1][0] == expected_wait_msg.format(3)
    # assert mock_vvv.mock_calls[3][1][0] == expected_wait_msg.format(4)
    # assert mock_vvv.mock_calls[4][1][0] == expected_wait_msg.format(6)
    # assert mock_vvv.mock_calls[5][1][0] == expected_wait_msg.format(10)
    # assert mock_vvv.mock_calls[6][1][0] == expected_wait_msg.format(15)
    # assert mock_vvv.mock_calls[7][1][0] == expected_wait_msg.format(22)
    # assert mock_vvv.mock_calls[8][1][0] == expected_wait_msg.format(30)


@pytest.mark.parametrize('api_version, token_type, version, token_ins', [
    ('v3', 'Bearer', 'v1.0.0', KeycloakToken(auth_url='https://api.test/api/automation-hub/')),
])
def test_get_collection_version_metadata_no_version(api_version, token_type, version, token_ins, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com/api/', api_version, token_ins=token_ins)

    if token_ins:
        mock_token_get = MagicMock()
        mock_token_get.return_value = 'my token'
        monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(to_text(json.dumps({
            'href': 'https://galaxy.server.com/api/{api}/namespace/name/versions/{version}/'.format(api=api_version, version=version),
            'download_url': 'https://downloadme.com',
            'artifact': {
                'sha256': 'ac47b6fac117d7c171812750dacda655b04533cf56b31080b82d1c0db3c9d80f',
            },
            'namespace': {
                'name': 'namespace',
            },
            'collection': {
                'name': 'collection',
            },
            'version': version,
            'metadata': {
                'dependencies': {},
            }
        }))),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_version_metadata('namespace', 'collection', version)

    assert isinstance(actual, CollectionVersionMetadata)
    assert actual.namespace == u'namespace'
    assert actual.name == u'collection'
    assert actual.download_url == u'https://downloadme.com'
    assert actual.artifact_sha256 == u'ac47b6fac117d7c171812750dacda655b04533cf56b31080b82d1c0db3c9d80f'
    assert actual.version == version
    assert actual.dependencies == {}

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == '%s%s/collections/namespace/collection/versions/%s/' \
        % (api.api_server, api_version, version)

    # v2 calls dont need auth, so no authz header or token_type
    if token_type:
        assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type


@pytest.mark.parametrize('api_version, token_type, token_ins', [
    ('v3', None, None),
    ('v3', 'Bearer', KeycloakToken(auth_url='https://api.test/api/automation-hub/')),
])
def test_get_collection_signatures_backwards_compat(api_version, token_type, token_ins, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com/api/', api_version, token_ins=token_ins)

    if token_ins:
        mock_token_get = MagicMock()
        mock_token_get.return_value = 'my token'
        monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO("{}")
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_signatures('namespace', 'collection', '1.0.0')
    assert actual == []

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == '%s%s/collections/namespace/collection/versions/1.0.0/' \
        % (api.api_server, api_version)

    # v3 calls dont need auth, so no authz header or token_type
    if token_type:
        assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type


@pytest.mark.parametrize('api_version, token_type, token_ins', [
    ('v3', None, None),
    ('v3', 'Bearer', KeycloakToken(auth_url='https://api.test/api/automation-hub/')),
])
def test_get_collection_signatures(api_version, token_type, token_ins, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com/api/', api_version, token_ins=token_ins)

    if token_ins:
        mock_token_get = MagicMock()
        mock_token_get.return_value = 'my token'
        monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(to_text(json.dumps({
            'signatures': [
                {
                    "signature": "-----BEGIN PGP SIGNATURE-----\nSIGNATURE1\n-----END PGP SIGNATURE-----\n",
                    "pubkey_fingerprint": "FINGERPRINT",
                    "signing_service": "ansible-default",
                    "pulp_created": "2022-01-14T14:05:53.835605Z",
                },
                {
                    "signature": "-----BEGIN PGP SIGNATURE-----\nSIGNATURE2\n-----END PGP SIGNATURE-----\n",
                    "pubkey_fingerprint": "FINGERPRINT",
                    "signing_service": "ansible-default",
                    "pulp_created": "2022-01-14T14:05:53.835605Z",
                },
            ],
        }))),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_signatures('namespace', 'collection', '1.0.0')

    assert actual == [
        "-----BEGIN PGP SIGNATURE-----\nSIGNATURE1\n-----END PGP SIGNATURE-----\n",
        "-----BEGIN PGP SIGNATURE-----\nSIGNATURE2\n-----END PGP SIGNATURE-----\n"
    ]

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == '%s%s/collections/namespace/collection/versions/1.0.0/' \
        % (api.api_server, api_version)

    # v3 calls dont need auth, so no authz header or token_type
    if token_type:
        assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type


@pytest.mark.parametrize('api_version, token_type, token_ins', [
    ('v3', None, None),
    ('v3', 'Bearer', KeycloakToken(auth_url='https://ah.test/'))
])
def test_get_collection_versions(api_version, token_type, token_ins, monkeypatch):
    response = {
        'meta': {
            'count': 2
        },
        'links': {
            'first': '/api/v3/plugin/ansible/content/published/collections/index/ns/col/versions/?limit=100&offset=0',
            'previous': None,
            'next': None,
            'last': '/api/v3/plugin/ansible/content/published/collections/index/ns/col/versions/?limit=100&offset=0'
        },
        'data': [
            {
                'version': '1.0.0',
                'href': '/api/v3/plugin/ansible/content/published/collections/index/ns/col/versions/1.0.0/',
            },
            {
                'version': '1.0.1',
                'href': '/api/v3/plugin/ansible/content/pubished/collections/index/ns/col/versions/1.0.1/',
            },
        ],
    }

    api = get_test_galaxy_api('https://galaxy.server.com/api/', api_version, token_ins=token_ins)

    if token_ins:
        mock_token_get = MagicMock()
        mock_token_get.return_value = 'my token'
        monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(to_text(json.dumps(response))),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_versions('namespace', 'collection')
    assert actual == [u'1.0.0', u'1.0.1']

    page_query = '?limit=100'
    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/%s' % (api_version, page_query)
    if token_ins:
        assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type


@pytest.mark.parametrize('api_version, token_type, token_ins, responses', [
    ('v3', 'Bearer', KeycloakToken(auth_url='https://api.test/'), [
        {
            'count': 6,
            'links': {
                # v3 links are relative and the limit is included during pagination
                'next': '/api/v3/collections/namespace/collection/versions/?limit=100&offset=100',
                'previous': None,
            },
            'data': [
                {
                    'version': '1.0.0',
                    'href': '/api/v3/collections/namespace/collection/versions/1.0.0',
                },
                {
                    'version': '1.0.1',
                    'href': '/api/v3/collections/namespace/collection/versions/1.0.1',
                },
            ],
        },
        {
            'count': 6,
            'links': {
                'next': '/api/v3/collections/namespace/collection/versions/?limit=100&offset=200',
                'previous': '/api/v3/collections/namespace/collection/versions',
            },
            'data': [
                {
                    'version': '1.0.2',
                    'href': '/api/v3/collections/namespace/collection/versions/1.0.2',
                },
                {
                    'version': '1.0.3',
                    'href': '/api/v3/collections/namespace/collection/versions/1.0.3',
                },
            ],
        },
        {
            'count': 6,
            'links': {
                'next': None,
                'previous': '/api/v3/collections/namespace/collection/versions/?limit=100&offset=100',
            },
            'data': [
                {
                    'version': '1.0.4',
                    'href': '/api/v3/collections/namespace/collection/versions/1.0.4',
                },
                {
                    'version': '1.0.5',
                    'href': '/api/v3/collections/namespace/collection/versions/1.0.5',
                },
            ],
        },
    ]),
])
def test_get_collection_versions_pagination(api_version, token_type, token_ins, responses, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com/api/', api_version, token_ins=token_ins)

    if token_ins:
        mock_token_get = MagicMock()
        mock_token_get.return_value = 'my token'
        monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [StringIO(to_text(json.dumps(r))) for r in responses]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_versions('namespace', 'collection')
    assert actual == [u'1.0.0', u'1.0.1', u'1.0.2', u'1.0.3', u'1.0.4', u'1.0.5']

    assert mock_open.call_count == 3

    query_1 = 'limit=100'
    query_2 = 'limit=100&offset=100'
    query_3 = 'limit=100&offset=200'

    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/?%s' % (api_version, query_1)
    assert mock_open.mock_calls[1][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/?%s' % (api_version, query_2)
    assert mock_open.mock_calls[2][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/?%s' % (api_version, query_3)

    if token_type:
        assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type
        assert mock_open.mock_calls[1][2]['headers']['Authorization'] == '%s my token' % token_type
        assert mock_open.mock_calls[2][2]['headers']['Authorization'] == '%s my token' % token_type


@pytest.mark.parametrize('responses', [
    [
        {
            'count': 2,
            'results': [{'name': '3.5.1', }, {'name': '3.5.2'}],
            'next_link': None,
            'next': None,
            'previous_link': None,
            'previous': None
        },
    ],
    [
        {
            'count': 2,
            'results': [{'name': '3.5.1'}],
            'next_link': '/api/v1/roles/432/versions/?page=2&page_size=50',
            'next': '/roles/432/versions/?page=2&page_size=50',
            'previous_link': None,
            'previous': None
        },
        {
            'count': 2,
            'results': [{'name': '3.5.2'}],
            'next_link': None,
            'next': None,
            'previous_link': '/api/v1/roles/432/versions/?&page_size=50',
            'previous': '/roles/432/versions/?page_size=50',
        },
    ]
])
def test_get_role_versions_pagination(monkeypatch, responses):
    api = get_test_galaxy_api('https://galaxy.com/api/', 'v1')

    mock_open = MagicMock()
    mock_open.side_effect = [StringIO(to_text(json.dumps(r))) for r in responses]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.fetch_role_related('versions', 432)
    assert actual == [{'name': '3.5.1'}, {'name': '3.5.2'}]

    assert mock_open.call_count == len(responses)

    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.com/api/v1/roles/432/versions/?page_size=50'
    if len(responses) == 2:
        assert mock_open.mock_calls[1][1][0] == 'https://galaxy.com/api/v1/roles/432/versions/?page=2&page_size=50'


def test_missing_cache_dir(cache_dir):
    os.rmdir(cache_dir)
    GalaxyAPI(None, "test", 'https://galaxy.ansible.com/', no_cache=False)

    assert os.path.isdir(cache_dir)
    assert stat.S_IMODE(os.stat(cache_dir).st_mode) == 0o700

    cache_file = os.path.join(cache_dir, 'api.json')
    with open(cache_file) as fd:
        actual_cache = fd.read()
    assert actual_cache == '{"version": 1}'
    assert stat.S_IMODE(os.stat(cache_file).st_mode) == 0o600


def test_existing_cache(cache_dir):
    cache_file = os.path.join(cache_dir, 'api.json')
    cache_file_contents = '{"version": 1, "test": "json"}'
    with open(cache_file, mode='w') as fd:
        fd.write(cache_file_contents)
        os.chmod(cache_file, 0o655)

    GalaxyAPI(None, "test", 'https://galaxy.ansible.com/', no_cache=False)

    assert os.path.isdir(cache_dir)
    with open(cache_file) as fd:
        actual_cache = fd.read()
    assert actual_cache == cache_file_contents
    assert stat.S_IMODE(os.stat(cache_file).st_mode) == 0o655


@pytest.mark.parametrize('content', [
    '',
    'value',
    '{"de" "finit" "ely" [\'invalid"]}',
    '[]',
    '{"version": 2, "test": "json"}',
    '{"version": 2, "key": "ÅÑŚÌβŁÈ"}',
])
def test_cache_invalid_cache_content(content, cache_dir):
    cache_file = os.path.join(cache_dir, 'api.json')
    with open(cache_file, mode='w') as fd:
        fd.write(content)
        os.chmod(cache_file, 0o664)

    GalaxyAPI(None, "test", 'https://galaxy.ansible.com/', no_cache=False)

    with open(cache_file) as fd:
        actual_cache = fd.read()
    assert actual_cache == '{"version": 1}'
    assert stat.S_IMODE(os.stat(cache_file).st_mode) == 0o664


def test_cache_complete_pagination(cache_dir, monkeypatch):

    responses = get_collection_versions()
    cache_file = os.path.join(cache_dir, 'api.json')

    api = get_test_galaxy_api('https://galaxy.server.com/api/', 'v3', no_cache=False)

    mock_open = MagicMock(
        side_effect=[
            StringIO(to_text(json.dumps(r)))
            for r in responses
        ]
    )
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual_versions = api.get_collection_versions('namespace', 'collection')
    assert actual_versions == [u'1.0.0', u'1.0.1', u'1.0.2', u'1.0.3', u'1.0.4', u'1.0.5']

    with open(cache_file) as fd:
        final_cache = json.loads(fd.read())

    cached_server = final_cache['galaxy.server.com:']
    cached_collection = cached_server['/api/v3/collections/namespace/collection/versions/']
    cached_versions = [r['version'] for r in cached_collection['results']]

    assert final_cache == api._cache
    assert cached_versions == actual_versions


def test_cache_complete_pagination_v3(cache_dir, monkeypatch):

    responses = get_v3_collection_versions()
    cache_file = os.path.join(cache_dir, 'api.json')

    api = get_test_galaxy_api('https://galaxy.server.com/api/', 'v3', no_cache=False)

    mock_open = MagicMock(
        side_effect=[
            StringIO(to_text(json.dumps(r)))
            for r in responses
        ]
    )
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual_versions = api.get_collection_versions('namespace', 'collection')
    assert actual_versions == [u'1.0.0', u'1.0.1', u'1.0.2', u'1.0.3', u'1.0.4', u'1.0.5']

    with open(cache_file) as fd:
        final_cache = json.loads(fd.read())

    cached_server = final_cache['galaxy.server.com:']
    cached_collection = cached_server['/api/v3/collections/namespace/collection/versions/']
    cached_versions = [r['version'] for r in cached_collection['results']]

    assert final_cache == api._cache
    assert cached_versions == actual_versions


def test_cache_flaky_pagination(cache_dir, monkeypatch):

    responses = get_collection_versions()
    cache_file = os.path.join(cache_dir, 'api.json')

    api = get_test_galaxy_api('https://galaxy.server.com/api/', 'v3', no_cache=False)

    # First attempt, fail midway through
    mock_open = MagicMock(
        side_effect=[
            StringIO(to_text(json.dumps(responses[0]))),
            StringIO(to_text(json.dumps(responses[1]))),
            urllib.error.HTTPError(responses[1]['links']['next'], 500, 'Error', {}, StringIO()),
            StringIO(to_text(json.dumps(responses[3]))),
        ]
    )
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    expected = (
        r'Error when getting available collection versions for namespace\.collection '
        r'from test \(https://galaxy\.server\.com/api/\) '
        r'\(HTTP Code: 500, Message: Error Code: Unknown\)'
    )
    with pytest.raises(GalaxyError, match=expected):
        api.get_collection_versions('namespace', 'collection')

    with open(cache_file) as fd:
        final_cache = json.loads(fd.read())

    assert final_cache == {
        'version': 1,
        'galaxy.server.com:': {
            'modified': {
                'namespace.collection': responses[0]['updated_at']
            }
        }
    }

    # Reset API
    api = get_test_galaxy_api('https://galaxy.server.com/api/', 'v3', no_cache=False)

    # Second attempt is successful so cache should be populated
    mock_open = MagicMock(
        side_effect=[
            StringIO(to_text(json.dumps(r)))
            for r in responses
        ]
    )
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual_versions = api.get_collection_versions('namespace', 'collection')
    assert actual_versions == [u'1.0.0', u'1.0.1', u'1.0.2', u'1.0.3', u'1.0.4', u'1.0.5']

    with open(cache_file) as fd:
        final_cache = json.loads(fd.read())

    cached_server = final_cache['galaxy.server.com:']
    cached_collection = cached_server['/api/v3/collections/namespace/collection/versions/']
    cached_versions = [r['version'] for r in cached_collection['results']]

    assert cached_versions == actual_versions


def test_world_writable_cache(cache_dir, monkeypatch):
    mock_warning = MagicMock()
    monkeypatch.setattr(Display, 'warning', mock_warning)

    cache_file = os.path.join(cache_dir, 'api.json')
    with open(cache_file, mode='w') as fd:
        fd.write('{"version": 2}')
        os.chmod(cache_file, 0o666)

    api = GalaxyAPI(None, "test", 'https://galaxy.ansible.com/', no_cache=False)
    assert api._cache is None

    with open(cache_file) as fd:
        actual_cache = fd.read()
    assert actual_cache == '{"version": 2}'
    assert stat.S_IMODE(os.stat(cache_file).st_mode) == 0o666

    assert mock_warning.call_count == 1
    assert mock_warning.call_args[0][0] == \
        'Galaxy cache has world writable access (%s), ignoring it as a cache source.' % cache_file


def test_no_cache(cache_dir):
    cache_file = os.path.join(cache_dir, 'api.json')
    with open(cache_file, mode='w') as fd:
        fd.write('random')

    api = GalaxyAPI(None, "test", 'https://galaxy.ansible.com/')
    assert api._cache is None

    with open(cache_file) as fd:
        actual_cache = fd.read()
    assert actual_cache == 'random'


def test_clear_cache_with_no_cache(cache_dir):
    cache_file = os.path.join(cache_dir, 'api.json')
    with open(cache_file, mode='w') as fd:
        fd.write('{"version": 1, "key": "value"}')

    GalaxyAPI(None, "test", 'https://galaxy.ansible.com/', clear_response_cache=True)
    assert not os.path.exists(cache_file)


def test_clear_cache(cache_dir):
    cache_file = os.path.join(cache_dir, 'api.json')
    with open(cache_file, mode='w') as fd:
        fd.write('{"version": 1, "key": "value"}')

    GalaxyAPI(None, "test", 'https://galaxy.ansible.com/', clear_response_cache=True, no_cache=False)

    with open(cache_file) as fd:
        actual_cache = fd.read()
    assert actual_cache == '{"version": 1}'
    assert stat.S_IMODE(os.stat(cache_file).st_mode) == 0o600


@pytest.mark.parametrize(['url', 'expected'], [
    ('http://hostname/path', 'hostname:'),
    ('http://hostname:80/path', 'hostname:80'),
    ('https://testing.com:invalid', 'testing.com:'),
    ('https://testing.com:1234', 'testing.com:1234'),
    ('https://username:password@testing.com/path', 'testing.com:'),
    ('https://username:password@testing.com:443/path', 'testing.com:443'),
])
def test_cache_id(url, expected):
    actual = galaxy_api.get_cache_id(url)
    assert actual == expected


def test_cache_missing_results_raises_descriptive_error(mocker):
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com/api/")

    mock_cache_entry = {
        'expires': '2023-01-02T12:00:00Z',
        'paginated': False
    }

    api._cache = {'galaxy.ansible.com': {'/api/v1/roles/': mock_cache_entry}}

    mocker.patch('ansible.galaxy.api.urlparse')
    mocker.patch('ansible.galaxy.api.parse_qs', return_value={})
    mocker.patch('ansible.galaxy.api.get_cache_id',
                 return_value='galaxy.ansible.com')

    mock_datetime = mocker.patch('ansible.galaxy.api.datetime')

    mock_comparison = mocker.Mock()
    mock_comparison.__bool__ = mocker.Mock(return_value=True)

    mock_now = mocker.Mock()
    mock_expires = mocker.Mock()
    mock_now.__lt__ = mocker.Mock(return_value=True)
    mock_datetime.datetime.now.return_value = mock_now
    mock_datetime.datetime.strptime.return_value = mock_expires

    with pytest.raises(AnsibleError, match="Missing expected 'results' in ansible-galaxy cache"):
        api._call_galaxy(
            url='https://galaxy.ansible.com/api/v1/roles/',
            cache=True,
            cache_key='/api/v1/roles/'
        )
