# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import re
import pytest
import tarfile
import tempfile

from io import BytesIO, StringIO
from units.compat.mock import MagicMock

from ansible import context
from ansible.errors import AnsibleError
from ansible.galaxy import api as galaxy_api
from ansible.galaxy.api import GalaxyAPI, GalaxyError
from ansible.galaxy.token import GalaxyToken
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six.moves.urllib import error as urllib_error
from ansible.utils import context_objects as co


@pytest.fixture(autouse='function')
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    # Required to initialise the GalaxyAPI object
    context.CLIARGS._store = {'ignore_certs': False}
    yield
    co.GlobalCLIArgs._Singleton__instance = None


@pytest.fixture()
def collection_artifact(tmp_path_factory):
    ''' Creates a collection artifact tarball that is ready to be published '''
    output_dir = to_text(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Output'))

    tar_path = os.path.join(output_dir, 'namespace-collection-v1.0.0.tar.gz')
    with tarfile.open(tar_path, 'w:gz') as tfile:
        b_io = BytesIO(b"\x00\x01\x02\x03")
        tar_info = tarfile.TarInfo('test')
        tar_info.size = 4
        tar_info.mode = 0o0644
        tfile.addfile(tarinfo=tar_info, fileobj=b_io)

    yield tar_path


def get_test_galaxy_api(url, version):
    api = GalaxyAPI(None, "test", url)
    api.initialized = True
    api.available_api_versions = {version: '/api/%s' % version}
    api.token = GalaxyToken(token="my token")

    return api



def test_api_no_auth():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com")
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {}


def test_api_no_auth_but_required():
    expected = "No access token or username set. A token can be set with --api-key, with 'ansible-galaxy login', " \
               "or set in ansible.cfg."
    with pytest.raises(AnsibleError, match=expected):
        GalaxyAPI(None, "test", "https://galaxy.ansible.com")._add_auth_token({}, "", required=True)


def test_api_token_auth():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {'Authorization': 'Token my_token'}


def test_api_token_auth_with_token_type():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = {}
    api._add_auth_token(actual, "", token_type="Bearer")
    assert actual == {'Authorization': 'Bearer my_token'}


def test_api_token_auth_with_v3_url():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = {}
    api._add_auth_token(actual, "https://galaxy.ansible.com/api/v3/resource/name")
    assert actual == {'Authorization': 'Bearer my_token'}


def test_api_token_auth_with_v2_url():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = {}
    # Add v3 to random part of URL but response should only see the v2 as the full URI path segment.
    api._add_auth_token(actual, "https://galaxy.ansible.com/api/v2/resourcev3/name")
    assert actual == {'Authorization': 'Token my_token'}


def test_api_basic_auth_password():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", username=u"user", password=u"pass")
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {'Authorization': 'Basic dXNlcjpwYXNz'}


def test_api_basic_auth_no_password():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", username=u"user",)
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {'Authorization': 'Basic dXNlcjo='}


def test_api_dont_override_auth_header():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com")
    actual = {'Authorization': 'Custom token'}
    api._add_auth_token(actual, "")
    assert actual == {'Authorization': 'Custom token'}


def test_initialise_galaxy(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(u'{"available_versions":{"v1":"/api/v1"}}'),
        StringIO(u'{"token":"my token"}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com")
    actual = api.authenticate("github_token")

    assert len(api.available_api_versions) == 2
    assert api.available_api_versions['v1'] == u'/api/v1'
    assert api.available_api_versions['v2'] == u'/api/v2'
    assert actual == {u'token': u'my token'}
    assert mock_open.call_count == 2
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api'
    assert mock_open.mock_calls[1][1][0] == 'https://galaxy.ansible.com/api/v1/tokens'
    assert mock_open.mock_calls[1][2]['data'] == 'github_token=github_token'


def test_initialise_galaxy_with_auth(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(u'{"available_versions":{"v1":"/api/v1"}}'),
        StringIO(u'{"token":"my token"}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=GalaxyToken(token='my_token'))
    actual = api.authenticate("github_token")

    assert len(api.available_api_versions) == 2
    assert api.available_api_versions['v1'] == u'/api/v1'
    assert api.available_api_versions['v2'] == u'/api/v2'
    assert actual == {u'token': u'my token'}
    assert mock_open.call_count == 2
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api'
    assert mock_open.mock_calls[0][2]['headers'] == {'Authorization': 'Token my_token'}
    assert mock_open.mock_calls[1][1][0] == 'https://galaxy.ansible.com/api/v1/tokens'
    assert mock_open.mock_calls[1][2]['data'] == 'github_token=github_token'


def test_initialise_automation_hub(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        urllib_error.HTTPError('https://galaxy.ansible.com/api', 401, 'msg', {}, StringIO()),
        # AH won't return v1 but we do for authenticate() to work.
        StringIO(u'{"available_versions":{"v1":"/api/v1","v3":"/api/v3"}}'),
        StringIO(u'{"token":"my token"}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=GalaxyToken(token='my_token'))
    actual = api.authenticate("github_token")

    assert len(api.available_api_versions) == 2
    assert api.available_api_versions['v1'] == u'/api/v1'
    assert api.available_api_versions['v3'] == u'/api/v3'
    assert actual == {u'token': u'my token'}
    assert mock_open.call_count == 3
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api'
    assert mock_open.mock_calls[0][2]['headers'] == {'Authorization': 'Token my_token'}
    assert mock_open.mock_calls[1][1][0] == 'https://galaxy.ansible.com/api'
    assert mock_open.mock_calls[1][2]['headers'] == {'Authorization': 'Bearer my_token'}
    assert mock_open.mock_calls[2][1][0] == 'https://galaxy.ansible.com/api/v1/tokens'
    assert mock_open.mock_calls[2][2]['data'] == 'github_token=github_token'


def test_initialise_unknown(monkeypatch):
    mock_open = MagicMock()
    mock_open.side_effect = [
        urllib_error.HTTPError('https://galaxy.ansible.com/api', 500, 'msg', {}, StringIO(u'{"msg":"raw error"}')),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=GalaxyToken(token='my_token'))

    expected = "Error when finding available api versions from test (%s/api) (HTTP Code: 500, Message: Unknown " \
               "error returned by Galaxy server.)" % api.api_server
    with pytest.raises(GalaxyError, match=re.escape(expected)):
        api.authenticate("github_token")


def test_publish_collection_missing_file():
    fake_path = u'/fake/ÅÑŚÌβŁÈ/path'
    expected = to_native("The collection path specified '%s' does not exist." % fake_path)

    api = get_test_galaxy_api("https://galaxy.ansible.com", "v2")
    with pytest.raises(AnsibleError, match=expected):
        api.publish_collection(fake_path)


def test_publish_collection_not_a_tarball():
    expected = "The collection path specified '{0}' is not a tarball, use 'ansible-galaxy collection build' to " \
               "create a proper release artifact."

    api = get_test_galaxy_api("https://galaxy.ansible.com", "v2")
    with tempfile.NamedTemporaryFile(prefix=u'ÅÑŚÌβŁÈ') as temp_file:
        temp_file.write(b"\x00")
        temp_file.flush()
        with pytest.raises(AnsibleError, match=expected.format(to_native(temp_file.name))):
            api.publish_collection(temp_file.name)


def test_publish_collection_unsupported_version():
    expected = "Galaxy action publish_collection requires API versions 'v2, v3' but only 'v1' are available on test " \
               "https://galaxy.ansible.com"

    api = get_test_galaxy_api("https://galaxy.ansible.com", "v1")
    with pytest.raises(AnsibleError, match=expected):
        api.publish_collection("path")


@pytest.mark.parametrize('api_version, collection_url', [
    ('v2', 'collections'),
    ('v3', 'artifacts/collections'),
])
def test_publish_collection(api_version, collection_url, collection_artifact, monkeypatch):
    api = get_test_galaxy_api("https://galaxy.ansible.com", api_version)

    mock_call = MagicMock()
    mock_call.return_value = {'task': 'http://task.url/'}
    monkeypatch.setattr(api, '_call_galaxy', mock_call)

    actual = api.publish_collection(collection_artifact)
    assert actual == 'http://task.url/'
    assert mock_call.call_count == 1
    assert mock_call.mock_calls[0][1][0] == 'https://galaxy.ansible.com/api/%s/%s' % (api_version, collection_url)
    assert mock_call.mock_calls[0][2]['headers']['Content-length'] == len(mock_call.mock_calls[0][2]['args'])
    assert mock_call.mock_calls[0][2]['headers']['Content-type'].startswith(
        'multipart/form-data; boundary=--------------------------')
    assert mock_call.mock_calls[0][2]['args'].startswith(b'--------------------------')
    assert mock_call.mock_calls[0][2]['method'] == 'POST'
    assert mock_call.mock_calls[0][2]['auth_required'] is True


@pytest.mark.parametrize('api_version, collection_url, response, expected', [
    ('v2', 'collections', {},
     'Error when publishing collection to test (%s) (HTTP Code: 500, Message: Unknown error returned by Galaxy '
     'server. Code: Unknown)'),
    ('v2', 'collections', {
        'message': u'Galaxy error messäge',
        'code': 'GWE002',
    }, u'Error when publishing collection to test (%s) (HTTP Code: 500, Message: Galaxy error messäge Code: GWE002)'),
    ('v3', 'artifact/collections', {},
     'Error when publishing collection to test (%s) (HTTP Code: 500, Message: Unknown error returned by Galaxy '
     'server. Code: Unknown)'),
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
    api = get_test_galaxy_api('https://galaxy.server.com', api_version)

    expected_url = '%s/api/%s/%s' % (api.api_server, api_version, collection_url)

    mock_open = MagicMock()
    mock_open.side_effect = urllib_error.HTTPError(expected_url, 500, 'msg', {},
                                                   StringIO(to_text(json.dumps(response))))
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    with pytest.raises(GalaxyError, match=re.escape(to_native(expected % api.api_server))):
        api.publish_collection(collection_artifact)


@pytest.mark.parametrize('api_version, token_type, version, expected', [
    ('v2', 'Token', None, 'collection'),
    ('v2', 'Token', 'v2.1.13', 'collection/versions/v2.1.13'),
    ('v3', 'Bearer', None, 'collection'),
    ('v3', 'Bearer', 'v1.0.0', 'collection/versions/v1.0.0'),
])
def test_get_collection_information_no_version(api_version, token_type, version, expected, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com', api_version)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(u'{"data": "value"}'),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_information('namespace', 'collection', version=version)

    assert actual == {u'data': u'value'}
    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == '%s/api/%s/collections/namespace/%s' \
        % (api.api_server, api_version, expected)
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type


@pytest.mark.parametrize('api_version, token_type, response', [
    ('v2', 'Token', {
        'count': 2,
        'next': None,
        'previous': None,
        'results': [
            {
                'version': '1.0.0',
                'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.0',
            },
            {
                'version': '1.0.1',
                'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.1',
            },
        ],
    }),
    # TODO: Verify this once Automation Hub is actually out
    ('v3', 'Bearer', {
        'count': 2,
        'next': None,
        'previous': None,
        'data': [
            {
                'version': '1.0.0',
                'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.0',
            },
            {
                'version': '1.0.1',
                'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.1',
            },
        ],
    }),
])
def test_get_collection_versions(api_version, token_type, response, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com', api_version)

    mock_open = MagicMock()
    mock_open.side_effect = [
        StringIO(to_text(json.dumps(response))),
    ]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_versions('namespace', 'collection')
    assert actual == [u'1.0.0', u'1.0.1']

    assert mock_open.call_count == 1
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions' % api_version
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type


@pytest.mark.parametrize('api_version, token_type, responses', [
    ('v2', 'Token', [
        {
            'count': 6,
            'next': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/?page=2',
            'previous': None,
            'results': [
                {
                    'version': '1.0.0',
                    'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.0',
                },
                {
                    'version': '1.0.1',
                    'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.1',
                },
            ],
        },
        {
            'count': 6,
            'next': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/?page=3',
            'previous': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions',
            'results': [
                {
                    'version': '1.0.2',
                    'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.2',
                },
                {
                    'version': '1.0.3',
                    'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.3',
                },
            ],
        },
        {
            'count': 6,
            'next': None,
            'previous': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/?page=2',
            'results': [
                {
                    'version': '1.0.4',
                    'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.4',
                },
                {
                    'version': '1.0.5',
                    'href': 'https://galaxy.server.com/api/v2/collections/namespace/collection/versions/1.0.5',
                },
            ],
        },
    ]),
    ('v3', 'Bearer', [
        {
            'count': 6,
            'links': {
                'next': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/?page=2',
                'previous': None,
            },
            'data': [
                {
                    'version': '1.0.0',
                    'href': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/1.0.0',
                },
                {
                    'version': '1.0.1',
                    'href': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/1.0.1',
                },
            ],
        },
        {
            'count': 6,
            'links': {
                'next': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/?page=3',
                'previous': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions',
            },
            'data': [
                {
                    'version': '1.0.2',
                    'href': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/1.0.2',
                },
                {
                    'version': '1.0.3',
                    'href': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/1.0.3',
                },
            ],
        },
        {
            'count': 6,
            'links': {
                'next': None,
                'previous': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/?page=2',
            },
            'data': [
                {
                    'version': '1.0.4',
                    'href': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/1.0.4',
                },
                {
                    'version': '1.0.5',
                    'href': 'https://galaxy.server.com/api/v3/collections/namespace/collection/versions/1.0.5',
                },
            ],
        },
    ]),
])
def test_get_collection_versions_pagination(api_version, token_type, responses, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com', api_version)

    mock_open = MagicMock()
    mock_open.side_effect = [StringIO(to_text(json.dumps(r))) for r in responses]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_versions('namespace', 'collection')
    a = ''
    assert actual == [u'1.0.0', u'1.0.1', u'1.0.2', u'1.0.3', u'1.0.4', u'1.0.5']

    assert mock_open.call_count == 3
    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions' % api_version
    assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type
    assert mock_open.mock_calls[1][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/?page=2' % api_version
    assert mock_open.mock_calls[1][2]['headers']['Authorization'] == '%s my token' % token_type
    assert mock_open.mock_calls[2][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/?page=3' % api_version
    assert mock_open.mock_calls[2][2]['headers']['Authorization'] == '%s my token' % token_type
