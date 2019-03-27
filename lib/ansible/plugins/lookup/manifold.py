# (c) 2018, Arigato Machine Inc.
# (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    author:
        - Kyrylo Galanov (galanoff@gmail.com)
    lookup: manifold
    version_added: "2.8"
    short_description: get credentials from Manifold.co
    description:
        - Retrieves resources' credentials from Manifold.co
    options:
        _terms:
            description:
                - Optional list of resource labels to lookup on Manifold.co. If no resources are specified, all
                  matched resources will be returned.
            type: list
            elements: string
            required: False
        api_token:
            description:
                - manifold API token
            type: string
            required: True
            env:
              - name: MANIFOLD_API_TOKEN
        project:
            description:
                - The project label you want to get the resource for.
            type: string
            required: False
        team:
            description:
                - The team label you want to get the resource for.
            type: string
            required: False
'''

EXAMPLES = '''
    - name: all available resources
      debug: msg="{{ lookup('manifold', api_token='SecretToken') }}"
    - name: all available resources for a specific project in specific team
      debug: msg="{{ lookup('manifold', api_token='SecretToken', project='poject-1', team='team-2') }}"
    - name: two specific resources
      debug: msg="{{ lookup('manifold', 'resource-1', 'resource-2') }}"
'''

RETURN = '''
    _raw:
        description:
            - dictionary of credentials ready to be consumed as environment variables. If multiple resources define
              the same environment variable(s), the last one returned by the Manifold API will take precedence.
        type: dict
'''
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils import six
from ansible.utils.display import Display
from traceback import format_exception
import json
import sys
import os

display = Display()


class ApiError(Exception):
    pass


class ManifoldApiClient(object):
    base_url = 'https://api.{api}.manifold.co/v1/{endpoint}'
    http_agent = 'python-manifold-ansible-1.0.0'

    def __init__(self, token):
        self._token = token

    def request(self, api, endpoint, *args, **kwargs):
        """
        Send a request to API backend and pre-process a response.
        :param api: API to send a request to
        :type api: str
        :param endpoint: API endpoint to fetch data from
        :type endpoint: str
        :param args: other args for open_url
        :param kwargs: other kwargs for open_url
        :return: server response. JSON response is automatically deserialized.
        :rtype: dict | list | str
        """

        default_headers = {
            'Authorization': "Bearer {0}".format(self._token),
            'Accept': "*/*"  # Otherwise server doesn't set content-type header
        }

        url = self.base_url.format(api=api, endpoint=endpoint)

        headers = default_headers
        arg_headers = kwargs.pop('headers', None)
        if arg_headers:
            headers.update(arg_headers)

        try:
            display.vvvv('manifold lookup connecting to {0}'.format(url))
            response = open_url(url, headers=headers, http_agent=self.http_agent, *args, **kwargs)
            data = response.read()
            if response.headers.get('content-type') == 'application/json':
                data = json.loads(data)
            return data
        except ValueError:
            raise ApiError('JSON response can\'t be parsed while requesting {url}:\n{json}'.format(json=data, url=url))
        except HTTPError as e:
            raise ApiError('Server returned: {err} while requesting {url}:\n{response}'.format(
                err=str(e), url=url, response=e.read()))
        except URLError as e:
            raise ApiError('Failed lookup url for {url} : {err}'.format(url=url, err=str(e)))
        except SSLValidationError as e:
            raise ApiError('Error validating the server\'s certificate for {url}: {err}'.format(url=url, err=str(e)))
        except ConnectionError as e:
            raise ApiError('Error connecting to {url}: {err}'.format(url=url, err=str(e)))

    def get_resources(self, team_id=None, project_id=None, label=None):
        """
        Get resources list
        :param team_id: ID of the Team to filter resources by
        :type team_id: str
        :param project_id: ID of the project to filter resources by
        :type project_id: str
        :param label: filter resources by a label, returns a list with one or zero elements
        :type label: str
        :return: list of resources
        :rtype: list
        """
        api = 'marketplace'
        endpoint = 'resources'
        query_params = {}

        if team_id:
            query_params['team_id'] = team_id
        if project_id:
            query_params['project_id'] = project_id
        if label:
            query_params['label'] = label

        if query_params:
            endpoint += '?' + urlencode(query_params)

        return self.request(api, endpoint)

    def get_teams(self, label=None):
        """
        Get teams list
        :param label: filter teams by a label, returns a list with one or zero elements
        :type label: str
        :return: list of teams
        :rtype: list
        """
        api = 'identity'
        endpoint = 'teams'
        data = self.request(api, endpoint)
        # Label filtering is not supported by API, however this function provides uniform interface
        if label:
            data = list(filter(lambda x: x['body']['label'] == label, data))
        return data

    def get_projects(self, label=None):
        """
        Get projects list
        :param label: filter projects by a label, returns a list with one or zero elements
        :type label: str
        :return: list of projects
        :rtype: list
        """
        api = 'marketplace'
        endpoint = 'projects'
        query_params = {}

        if label:
            query_params['label'] = label

        if query_params:
            endpoint += '?' + urlencode(query_params)

        return self.request(api, endpoint)

    def get_credentials(self, resource_id):
        """
        Get resource credentials
        :param resource_id: ID of the resource to filter credentials by
        :type resource_id: str
        :return:
        """
        api = 'marketplace'
        endpoint = 'credentials?' + urlencode({'resource_id': resource_id})
        return self.request(api, endpoint)


class LookupModule(LookupBase):

    def run(self, terms, variables=None, api_token=None, project=None, team=None):
        """
        :param terms: a list of resources lookups to run.
        :param variables: ansible variables active at the time of the lookup
        :param api_token: API token
        :param project: optional project label
        :param team: optional team label
        :return: a dictionary of resources credentials
        """

        if not api_token:
            api_token = os.getenv('MANIFOLD_API_TOKEN')
        if not api_token:
            raise AnsibleError('API token is required. Please set api_token parameter or MANIFOLD_API_TOKEN env var')

        try:
            labels = terms
            client = ManifoldApiClient(api_token)

            if team:
                team_data = client.get_teams(team)
                if len(team_data) == 0:
                    raise AnsibleError("Team '{0}' does not exist".format(team))
                team_id = team_data[0]['id']
            else:
                team_id = None

            if project:
                project_data = client.get_projects(project)
                if len(project_data) == 0:
                    raise AnsibleError("Project '{0}' does not exist".format(project))
                project_id = project_data[0]['id']
            else:
                project_id = None

            if len(labels) == 1:  # Use server-side filtering if one resource is requested
                resources_data = client.get_resources(team_id=team_id, project_id=project_id, label=labels[0])
            else:  # Get all resources and optionally filter labels
                resources_data = client.get_resources(team_id=team_id, project_id=project_id)
                if labels:
                    resources_data = list(filter(lambda x: x['body']['label'] in labels, resources_data))

            if labels and len(resources_data) < len(labels):
                fetched_labels = [r['body']['label'] for r in resources_data]
                not_found_labels = [label for label in labels if label not in fetched_labels]
                raise AnsibleError("Resource(s) {0} do not exist".format(', '.join(not_found_labels)))

            credentials = {}
            cred_map = {}
            for resource in resources_data:
                resource_credentials = client.get_credentials(resource['id'])
                if len(resource_credentials) and resource_credentials[0]['body']['values']:
                    for cred_key, cred_val in six.iteritems(resource_credentials[0]['body']['values']):
                        label = resource['body']['label']
                        if cred_key in credentials:
                            display.warning("'{cred_key}' with label '{old_label}' was replaced by resource data "
                                            "with label '{new_label}'".format(cred_key=cred_key,
                                                                              old_label=cred_map[cred_key],
                                                                              new_label=label))
                        credentials[cred_key] = cred_val
                        cred_map[cred_key] = label

            ret = [credentials]
            return ret
        except ApiError as e:
            raise AnsibleError('API Error: {0}'.format(str(e)))
        except AnsibleError as e:
            raise e
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            raise AnsibleError(format_exception(exc_type, exc_value, exc_traceback))
