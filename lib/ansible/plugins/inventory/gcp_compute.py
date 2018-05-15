# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: gcp_compute
    plugin_type: inventory
    short_description: Google Cloud Compute Engine inventory source
    extends_documentation_fragment:
        - gcp
        - constructed
        - inventory_cache
    description:
        - Get inventory hosts from Google Cloud Platform GCE.
        - Uses a <name>.gcp.yaml (or <name>.gcp.yml) YAML configuration file.
    options:
        zones:
          description: A list of regions in which to describe GCE instances.
        projects:
          description: A list of projects in which to describe GCE instances.
        filters:
          description: A dictionary of filter value pairs. Available filters are listed here
              U(https://cloud.google.com/compute/docs/reference/rest/v1/instances/list)
'''

EXAMPLES = '''
plugin: gcp_compute
zones: # populate inventory with instances in these regions
  - us-east1-a
projects:
  - gcp-prod-gke-100
  - gcp-cicd-101
filters:
  - machineType = n1-standard-1
  - scheduling.automaticRestart = true AND machineType = n1-standard-1

scopes:
  - https://www.googleapis.com/auth/compute
service_account_file: /tmp/service_account.json
auth_kind: serviceaccount
'''

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six import string_types
from ansible.module_utils.gcp_utils import GcpSession, navigate_hash, GcpRequestException
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable, to_safe_group_name
import json


# The mappings give an array of keys to get from the filter name to the value
# returned by boto3's GCE describe_instances method.
class GcpMockModule(object):
    def __init__(self, params):
        self.params = params

    def fail_json(self, *args, **kwargs):
        raise AnsibleError(kwargs['msg'])


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'gcp_compute'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.group_prefix = 'gcp_'

    def _populate(self, resp):
        '''
            :param resp: A JSON response
        '''
        for item in resp:
            hostname = item['name']
            self.inventory.add_host(hostname)
            for key in item:
                self.inventory.set_variable(hostname, key, item[key])
            self.inventory.add_child('all', hostname)

    def _validate_file(self, path):
        '''
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith('.gcp.yml') or path.endswith('.gcp.yaml'):
                return True
        return False

    def self_link(self, params):
        '''
            :param params: a dict containing all of the fields relevant to build URL
            :return the formatted URL as a string.
        '''
        return "https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances".format(**params)

    def fetch_list(self, params, link, query):
        '''
            :param params: a dict containing all of the fields relevant to build URL
            :param link: a formatted URL
            :param query: a formatted query string
            :return the JSON response containing a list of instances.
        '''
        module = GcpMockModule(params)
        auth = GcpSession(module, 'compute')
        response = auth.get(link, params={'filter': query})
        return self._return_if_object(module, response)

    def _get_query_options(self, filters):
        '''
            :param config_data: contents of the inventory config file
            :return A fully built query string
        '''
        if not filters:
            return ''

        if len(filters) == 1:
            return filters[0]
        else:
            queries = []
            for f in filters:
                # For multiple queries, all queries should have ()
                if f[0] != '(' and f[-1] != ')':
                    queries.append("(%s)" % ''.join(f))
                else:
                    queries.append(f)

            return ' '.join(queries)

    def _return_if_object(self, module, response):
        '''
            :param module: A GcpModule
            :param response: A Requests response object
            :return JSON response
        '''
        # If not found, return nothing.
        if response.status_code == 404:
            return None

        # If no content, return nothing.
        if response.status_code == 204:
            return None

        try:
            response.raise_for_status
            result = response.json()
        except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
            module.fail_json(msg="Invalid JSON response with error: %s" % inst)
        except GcpRequestException as inst:
            module.fail_json(msg="Network error: %s" % inst)

        if navigate_hash(result, ['error', 'errors']):
            module.fail_json(msg=navigate_hash(result, ['error', 'errors']))
        if result['kind'] != 'compute#instanceList':
            module.fail_json(msg="Incorrect result: {kind}".format(**result))

        return result

    def _add_hosts(self, items, config_data):
        '''
            :param items: A list of hosts
            :param config_data: configuration data
            :param hostnames: a list of hostnames
        '''
        if not items:
            return

        self._populate(items)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = {}
        if self._validate_file(path):
            config_data = self._read_config_data(path)

        # get user specifications
        if 'zones' not in config_data:
            raise AnsibleParserError("Zones must be included in inventory YAML file")

        if not isinstance(config_data['zones'], list):
            raise AnsibleParserError("Zones must be a list in GCP inventory YAML files")

        # get user specifications
        if 'projects' not in config_data:
            raise AnsibleParserError("Projects must be included in inventory YAML file")

        if not isinstance(config_data['projects'], list):
            raise AnsibleParserError("Projects must be a list in GCP inventory YAML files")

        zones = config_data['zones']
        projects = config_data['projects']
        config_data['scopes'] = ['https://www.googleapis.com/auth/compute']

        query = self._get_query_options(config_data['filters'])

        # Cache logic
        if cache:
            cache = self._options.get('cache')
            cache_key = self.get_cache_key(path)
        else:
            cache_key = None

        cache_needs_update = False
        if cache:
            try:
                results = self.cache.get(cache_key)
            except KeyError:
                cache_needs_update = True

        if not cache or cache_needs_update:
            for project in projects:
                for zone in zones:
                    config_data['zone'] = zone
                    config_data['project'] = project
                    link = self.self_link(config_data)
                    resp = self.fetch_list(config_data, link, query)
                    self._add_hosts(resp.get('items'), config_data)
                    if cache_needs_update:
                        self.cache.set(cache_key, resp.get('items'))
