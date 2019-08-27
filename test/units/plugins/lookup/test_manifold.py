# (c) 2018, Arigato Machine Inc.
# (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat import unittest
from units.compat.mock import patch, call
from ansible.errors import AnsibleError
from ansible.module_utils.urls import ConnectionError, SSLValidationError
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils import six
from ansible.plugins.lookup.manifold import ManifoldApiClient, LookupModule, ApiError
import json


API_FIXTURES = {
    'https://api.marketplace.manifold.co/v1/resources':
        [
            {
                "body": {
                    "label": "resource-1",
                    "name": "Resource 1"
                },
                "id": "rid-1"
            },
            {
                "body": {
                    "label": "resource-2",
                    "name": "Resource 2"
                },
                "id": "rid-2"
            }
        ],
    'https://api.marketplace.manifold.co/v1/resources?label=resource-1':
        [
            {
                "body": {
                    "label": "resource-1",
                    "name": "Resource 1"
                },
                "id": "rid-1"
            }
        ],
    'https://api.marketplace.manifold.co/v1/resources?label=resource-2':
        [
            {
                "body": {
                    "label": "resource-2",
                    "name": "Resource 2"
                },
                "id": "rid-2"
            }
        ],
    'https://api.marketplace.manifold.co/v1/resources?team_id=tid-1':
        [
            {
                "body": {
                    "label": "resource-1",
                    "name": "Resource 1"
                },
                "id": "rid-1"
            }
        ],
    'https://api.marketplace.manifold.co/v1/resources?project_id=pid-1':
        [
            {
                "body": {
                    "label": "resource-2",
                    "name": "Resource 2"
                },
                "id": "rid-2"
            }
        ],
    'https://api.marketplace.manifold.co/v1/resources?project_id=pid-2':
        [
            {
                "body": {
                    "label": "resource-1",
                    "name": "Resource 1"
                },
                "id": "rid-1"
            },
            {
                "body": {
                    "label": "resource-3",
                    "name": "Resource 3"
                },
                "id": "rid-3"
            }
        ],
    'https://api.marketplace.manifold.co/v1/resources?team_id=tid-1&project_id=pid-1':
        [
            {
                "body": {
                    "label": "resource-1",
                    "name": "Resource 1"
                },
                "id": "rid-1"
            }
        ],
    'https://api.marketplace.manifold.co/v1/projects':
        [
            {
                "body": {
                    "label": "project-1",
                    "name": "Project 1",
                },
                "id": "pid-1",
            },
            {
                "body": {
                    "label": "project-2",
                    "name": "Project 2",
                },
                "id": "pid-2",
            }
        ],
    'https://api.marketplace.manifold.co/v1/projects?label=project-2':
        [
            {
                "body": {
                    "label": "project-2",
                    "name": "Project 2",
                },
                "id": "pid-2",
            }
        ],
    'https://api.marketplace.manifold.co/v1/credentials?resource_id=rid-1':
        [
            {
                "body": {
                    "resource_id": "rid-1",
                    "values": {
                        "RESOURCE_TOKEN_1": "token-1",
                        "RESOURCE_TOKEN_2": "token-2"
                    }
                },
                "id": "cid-1",
            }
        ],
    'https://api.marketplace.manifold.co/v1/credentials?resource_id=rid-2':
        [
            {
                "body": {
                    "resource_id": "rid-2",
                    "values": {
                        "RESOURCE_TOKEN_3": "token-3",
                        "RESOURCE_TOKEN_4": "token-4"
                    }
                },
                "id": "cid-2",
            }
        ],
    'https://api.marketplace.manifold.co/v1/credentials?resource_id=rid-3':
        [
            {
                "body": {
                    "resource_id": "rid-3",
                    "values": {
                        "RESOURCE_TOKEN_1": "token-5",
                        "RESOURCE_TOKEN_2": "token-6"
                    }
                },
                "id": "cid-3",
            }
        ],
    'https://api.identity.manifold.co/v1/teams':
        [
            {
                "id": "tid-1",
                "body": {
                    "name": "Team 1",
                    "label": "team-1"
                }
            },
            {
                "id": "tid-2",
                "body": {
                    "name": "Team 2",
                    "label": "team-2"
                }
            }
        ]
}


def mock_fixture(open_url_mock, fixture=None, data=None, headers=None):
    if not headers:
        headers = {}
    if fixture:
        data = json.dumps(API_FIXTURES[fixture])
        if 'content-type' not in headers:
            headers['content-type'] = 'application/json'

    open_url_mock.return_value.read.return_value = data
    open_url_mock.return_value.headers = headers


class TestManifoldApiClient(unittest.TestCase):
    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_sends_default_headers(self, open_url_mock):
        mock_fixture(open_url_mock, data='hello')
        client = ManifoldApiClient('token-123')
        client.request('test', 'endpoint')
        open_url_mock.assert_called_with('https://api.test.manifold.co/v1/endpoint',
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0')

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_decodes_json(self, open_url_mock):
        mock_fixture(open_url_mock, fixture='https://api.marketplace.manifold.co/v1/resources')
        client = ManifoldApiClient('token-123')
        self.assertIsInstance(client.request('marketplace', 'resources'), list)

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_streams_text(self, open_url_mock):
        mock_fixture(open_url_mock, data='hello', headers={'content-type': "text/plain"})
        client = ManifoldApiClient('token-123')
        self.assertEqual('hello', client.request('test', 'endpoint'))

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_processes_parameterized_headers(self, open_url_mock):
        mock_fixture(open_url_mock, data='hello')
        client = ManifoldApiClient('token-123')
        client.request('test', 'endpoint', headers={'X-HEADER': 'MANIFOLD'})
        open_url_mock.assert_called_with('https://api.test.manifold.co/v1/endpoint',
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123',
                                                  'X-HEADER': 'MANIFOLD'},
                                         http_agent='python-manifold-ansible-1.0.0')

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_passes_arbitrary_parameters(self, open_url_mock):
        mock_fixture(open_url_mock, data='hello')
        client = ManifoldApiClient('token-123')
        client.request('test', 'endpoint', use_proxy=False, timeout=5)
        open_url_mock.assert_called_with('https://api.test.manifold.co/v1/endpoint',
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0',
                                         use_proxy=False, timeout=5)

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_raises_on_incorrect_json(self, open_url_mock):
        mock_fixture(open_url_mock, data='noJson', headers={'content-type': "application/json"})
        client = ManifoldApiClient('token-123')
        with self.assertRaises(ApiError) as context:
            client.request('test', 'endpoint')
        self.assertEqual('JSON response can\'t be parsed while requesting https://api.test.manifold.co/v1/endpoint:\n'
                         'noJson',
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_raises_on_status_500(self, open_url_mock):
        open_url_mock.side_effect = HTTPError('https://api.test.manifold.co/v1/endpoint',
                                              500, 'Server error', {}, six.StringIO('ERROR'))
        client = ManifoldApiClient('token-123')
        with self.assertRaises(ApiError) as context:
            client.request('test', 'endpoint')
        self.assertEqual('Server returned: HTTP Error 500: Server error while requesting '
                         'https://api.test.manifold.co/v1/endpoint:\nERROR',
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_raises_on_bad_url(self, open_url_mock):
        open_url_mock.side_effect = URLError('URL is invalid')
        client = ManifoldApiClient('token-123')
        with self.assertRaises(ApiError) as context:
            client.request('test', 'endpoint')
        self.assertEqual('Failed lookup url for https://api.test.manifold.co/v1/endpoint : <url'
                         'open error URL is invalid>',
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_raises_on_ssl_error(self, open_url_mock):
        open_url_mock.side_effect = SSLValidationError('SSL Error')
        client = ManifoldApiClient('token-123')
        with self.assertRaises(ApiError) as context:
            client.request('test', 'endpoint')
        self.assertEqual('Error validating the server\'s certificate for https://api.test.manifold.co/v1/endpoint: '
                         'SSL Error',
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_request_raises_on_connection_error(self, open_url_mock):
        open_url_mock.side_effect = ConnectionError('Unknown connection error')
        client = ManifoldApiClient('token-123')
        with self.assertRaises(ApiError) as context:
            client.request('test', 'endpoint')
        self.assertEqual('Error connecting to https://api.test.manifold.co/v1/endpoint: Unknown connection error',
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_get_resources_get_all(self, open_url_mock):
        url = 'https://api.marketplace.manifold.co/v1/resources'
        mock_fixture(open_url_mock, fixture=url)
        client = ManifoldApiClient('token-123')
        self.assertListEqual(API_FIXTURES[url], client.get_resources())
        open_url_mock.assert_called_with(url,
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0')

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_get_resources_filter_label(self, open_url_mock):
        url = 'https://api.marketplace.manifold.co/v1/resources?label=resource-1'
        mock_fixture(open_url_mock, fixture=url)
        client = ManifoldApiClient('token-123')
        self.assertListEqual(API_FIXTURES[url], client.get_resources(label='resource-1'))
        open_url_mock.assert_called_with(url,
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0')

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_get_resources_filter_team_and_project(self, open_url_mock):
        url = 'https://api.marketplace.manifold.co/v1/resources?team_id=tid-1&project_id=pid-1'
        mock_fixture(open_url_mock, fixture=url)
        client = ManifoldApiClient('token-123')
        self.assertListEqual(API_FIXTURES[url], client.get_resources(team_id='tid-1', project_id='pid-1'))
        args, kwargs = open_url_mock.call_args
        url_called = args[0]
        # Dict order is not guaranteed, so an url may have querystring parameters order randomized
        self.assertIn('team_id=tid-1', url_called)
        self.assertIn('project_id=pid-1', url_called)

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_get_teams_get_all(self, open_url_mock):
        url = 'https://api.identity.manifold.co/v1/teams'
        mock_fixture(open_url_mock, fixture=url)
        client = ManifoldApiClient('token-123')
        self.assertListEqual(API_FIXTURES[url], client.get_teams())
        open_url_mock.assert_called_with(url,
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0')

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_get_teams_filter_label(self, open_url_mock):
        url = 'https://api.identity.manifold.co/v1/teams'
        mock_fixture(open_url_mock, fixture=url)
        client = ManifoldApiClient('token-123')
        self.assertListEqual(API_FIXTURES[url][1:2], client.get_teams(label='team-2'))
        open_url_mock.assert_called_with(url,
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0')

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_get_projects_get_all(self, open_url_mock):
        url = 'https://api.marketplace.manifold.co/v1/projects'
        mock_fixture(open_url_mock, fixture=url)
        client = ManifoldApiClient('token-123')
        self.assertListEqual(API_FIXTURES[url], client.get_projects())
        open_url_mock.assert_called_with(url,
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0')

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_get_projects_filter_label(self, open_url_mock):
        url = 'https://api.marketplace.manifold.co/v1/projects?label=project-2'
        mock_fixture(open_url_mock, fixture=url)
        client = ManifoldApiClient('token-123')
        self.assertListEqual(API_FIXTURES[url], client.get_projects(label='project-2'))
        open_url_mock.assert_called_with(url,
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0')

    @patch('ansible.plugins.lookup.manifold.open_url')
    def test_get_credentials(self, open_url_mock):
        url = 'https://api.marketplace.manifold.co/v1/credentials?resource_id=rid-1'
        mock_fixture(open_url_mock, fixture=url)
        client = ManifoldApiClient('token-123')
        self.assertListEqual(API_FIXTURES[url], client.get_credentials(resource_id='rid-1'))
        open_url_mock.assert_called_with(url,
                                         headers={'Accept': '*/*', 'Authorization': 'Bearer token-123'},
                                         http_agent='python-manifold-ansible-1.0.0')


class TestLookupModule(unittest.TestCase):
    def setUp(self):
        self.lookup = LookupModule()
        self.lookup._load_name = "manifold"

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_get_all(self, client_mock):
        expected_result = [{'RESOURCE_TOKEN_1': 'token-1',
                            'RESOURCE_TOKEN_2': 'token-2',
                            'RESOURCE_TOKEN_3': 'token-3',
                            'RESOURCE_TOKEN_4': 'token-4'
                            }]
        client_mock.return_value.get_resources.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/resources']
        client_mock.return_value.get_credentials.side_effect = lambda x: API_FIXTURES['https://api.marketplace.manifold.co/v1/'
                                                                                      'credentials?resource_id={0}'.format(x)]
        self.assertListEqual(expected_result, self.lookup.run([], api_token='token-123'))
        client_mock.assert_called_with('token-123')
        client_mock.return_value.get_resources.assert_called_with(team_id=None, project_id=None)

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_get_one_resource(self, client_mock):
        expected_result = [{'RESOURCE_TOKEN_3': 'token-3',
                            'RESOURCE_TOKEN_4': 'token-4'
                            }]
        client_mock.return_value.get_resources.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/resources?label=resource-2']
        client_mock.return_value.get_credentials.side_effect = lambda x: API_FIXTURES['https://api.marketplace.manifold.co/v1/'
                                                                                      'credentials?resource_id={0}'.format(x)]
        self.assertListEqual(expected_result, self.lookup.run(['resource-2'], api_token='token-123'))
        client_mock.return_value.get_resources.assert_called_with(team_id=None, project_id=None, label='resource-2')

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_get_two_resources(self, client_mock):
        expected_result = [{'RESOURCE_TOKEN_1': 'token-1',
                            'RESOURCE_TOKEN_2': 'token-2',
                            'RESOURCE_TOKEN_3': 'token-3',
                            'RESOURCE_TOKEN_4': 'token-4'
                            }]
        client_mock.return_value.get_resources.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/resources']
        client_mock.return_value.get_credentials.side_effect = lambda x: API_FIXTURES['https://api.marketplace.manifold.co/v1/'
                                                                                      'credentials?resource_id={0}'.format(x)]
        self.assertListEqual(expected_result, self.lookup.run(['resource-1', 'resource-2'], api_token='token-123'))
        client_mock.assert_called_with('token-123')
        client_mock.return_value.get_resources.assert_called_with(team_id=None, project_id=None)

    @patch('ansible.plugins.lookup.manifold.display')
    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_get_resources_with_same_credential_names(self, client_mock, display_mock):
        expected_result = [{'RESOURCE_TOKEN_1': 'token-5',
                            'RESOURCE_TOKEN_2': 'token-6'
                            }]
        client_mock.return_value.get_resources.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/resources?project_id=pid-2']
        client_mock.return_value.get_projects.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/projects?label=project-2']
        client_mock.return_value.get_credentials.side_effect = lambda x: API_FIXTURES['https://api.marketplace.manifold.co/v1/'
                                                                                      'credentials?resource_id={0}'.format(x)]
        self.assertListEqual(expected_result, self.lookup.run([], api_token='token-123', project='project-2'))
        client_mock.assert_called_with('token-123')
        display_mock.warning.assert_has_calls([
            call("'RESOURCE_TOKEN_1' with label 'resource-1' was replaced by resource data with label 'resource-3'"),
            call("'RESOURCE_TOKEN_2' with label 'resource-1' was replaced by resource data with label 'resource-3'")],
            any_order=True
        )
        client_mock.return_value.get_resources.assert_called_with(team_id=None, project_id='pid-2')

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_filter_by_team(self, client_mock):
        expected_result = [{'RESOURCE_TOKEN_1': 'token-1',
                            'RESOURCE_TOKEN_2': 'token-2'
                            }]
        client_mock.return_value.get_resources.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/resources?team_id=tid-1']
        client_mock.return_value.get_teams.return_value = API_FIXTURES['https://api.identity.manifold.co/v1/teams'][0:1]
        client_mock.return_value.get_credentials.side_effect = lambda x: API_FIXTURES['https://api.marketplace.manifold.co/v1/'
                                                                                      'credentials?resource_id={0}'.format(x)]
        self.assertListEqual(expected_result, self.lookup.run([], api_token='token-123', team='team-1'))
        client_mock.assert_called_with('token-123')
        client_mock.return_value.get_resources.assert_called_with(team_id='tid-1', project_id=None)

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_filter_by_project(self, client_mock):
        expected_result = [{'RESOURCE_TOKEN_3': 'token-3',
                            'RESOURCE_TOKEN_4': 'token-4'
                            }]
        client_mock.return_value.get_resources.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/resources?project_id=pid-1']
        client_mock.return_value.get_projects.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/projects'][0:1]
        client_mock.return_value.get_credentials.side_effect = lambda x: API_FIXTURES['https://api.marketplace.manifold.co/v1/'
                                                                                      'credentials?resource_id={0}'.format(x)]
        self.assertListEqual(expected_result, self.lookup.run([], api_token='token-123', project='project-1'))
        client_mock.assert_called_with('token-123')
        client_mock.return_value.get_resources.assert_called_with(team_id=None, project_id='pid-1')

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_filter_by_team_and_project(self, client_mock):
        expected_result = [{'RESOURCE_TOKEN_1': 'token-1',
                            'RESOURCE_TOKEN_2': 'token-2'
                            }]
        client_mock.return_value.get_resources.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/resources?team_id=tid-1&project_id=pid-1']
        client_mock.return_value.get_teams.return_value = API_FIXTURES['https://api.identity.manifold.co/v1/teams'][0:1]
        client_mock.return_value.get_projects.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/projects'][0:1]
        client_mock.return_value.get_credentials.side_effect = lambda x: API_FIXTURES['https://api.marketplace.manifold.co/v1/'
                                                                                      'credentials?resource_id={0}'.format(x)]
        self.assertListEqual(expected_result, self.lookup.run([], api_token='token-123', project='project-1'))
        client_mock.assert_called_with('token-123')
        client_mock.return_value.get_resources.assert_called_with(team_id=None, project_id='pid-1')

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_raise_team_doesnt_exist(self, client_mock):
        client_mock.return_value.get_teams.return_value = []
        with self.assertRaises(AnsibleError) as context:
            self.lookup.run([], api_token='token-123', team='no-team')
        self.assertEqual("Team 'no-team' does not exist",
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_raise_project_doesnt_exist(self, client_mock):
        client_mock.return_value.get_projects.return_value = []
        with self.assertRaises(AnsibleError) as context:
            self.lookup.run([], api_token='token-123', project='no-project')
        self.assertEqual("Project 'no-project' does not exist",
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_raise_resource_doesnt_exist(self, client_mock):
        client_mock.return_value.get_resources.return_value = API_FIXTURES['https://api.marketplace.manifold.co/v1/resources']
        with self.assertRaises(AnsibleError) as context:
            self.lookup.run(['resource-1', 'no-resource-1', 'no-resource-2'], api_token='token-123')
        self.assertEqual("Resource(s) no-resource-1, no-resource-2 do not exist",
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_catch_api_error(self, client_mock):
        client_mock.side_effect = ApiError('Generic error')
        with self.assertRaises(AnsibleError) as context:
            self.lookup.run([], api_token='token-123')
        self.assertEqual("API Error: Generic error",
                         str(context.exception))

    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_catch_unhandled_exception(self, client_mock):
        client_mock.side_effect = Exception('Unknown error')
        with self.assertRaises(AnsibleError) as context:
            self.lookup.run([], api_token='token-123')
        self.assertTrue('Exception: Unknown error' in str(context.exception))

    @patch('ansible.plugins.lookup.manifold.os.getenv')
    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_falls_back_to_env_var(self, client_mock, getenv_mock):
        getenv_mock.return_value = 'token-321'
        client_mock.return_value.get_resources.return_value = []
        client_mock.return_value.get_credentials.return_value = []
        self.lookup.run([])
        getenv_mock.assert_called_with('MANIFOLD_API_TOKEN')
        client_mock.assert_called_with('token-321')

    @patch('ansible.plugins.lookup.manifold.os.getenv')
    @patch('ansible.plugins.lookup.manifold.ManifoldApiClient')
    def test_falls_raises_on_no_token(self, client_mock, getenv_mock):
        getenv_mock.return_value = None
        client_mock.return_value.get_resources.return_value = []
        client_mock.return_value.get_credentials.return_value = []
        with self.assertRaises(AnsibleError) as context:
            self.lookup.run([])
        self.assertEqual('API token is required. Please set api_token parameter or MANIFOLD_API_TOKEN env var',
                         str(context.exception))
