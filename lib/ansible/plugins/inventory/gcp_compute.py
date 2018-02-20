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
    description:
        - Get inventory hosts from Google Cloud Platform GCE.
        - Uses a <name>.gcp.yaml (or <name>.gcp.yml) YAML configuration file.
    options:
        zones:
          description: A list of regions in which to describe GCE instances.
        filters:
          description: A dictionary of filter value pairs. Available filters are listed here
              U(https://cloud.google.com/compute/docs/reference/rest/v1/instances/list)
'''

EXAMPLES = '''
simple_config_file:

    plugin: gcp_compute
    zones: # populate inventory with instances in these regions
      - us-east1-a
    filters:
      machine-type:
        eq:
          - n1-standard-1
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

    def _validate_config(self, loader, path):
        '''
            :param loader: an ansible.parsing.dataloader.DataLoader object
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith('.gcp.yml') or path.endswith('.gcp.yaml'):
                return self._read_config_data(path)
        raise AnsibleParserError("Not a gce inventory plugin configuration file")

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
        return self.return_if_object(module, response)

    def _get_query_options(self, config_data):
        '''
            :param config_data: contents of the inventory config file
            :return A string
        '''
        queries = []
        for obj_key in config_data['filters']:
            for conditional in config_data['filters'][obj_key]:
                if conditional not in ['ne', 'eq']:
                    raise AnsibleParserError("All conditionals must be eq or ne")
                for item in config_data['filters'][obj_key][conditional]:
                    query = [obj_key, conditional, item]
                    queries.append("(%s)" % ' '.join(query))

        return ' '.join(queries)

    def return_if_object(self, module, response):
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

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = self._validate_config(loader, path)

        # get user specifications
        if 'zones' not in config_data:
            raise AnsibleParserError("Zones must be included in inventory YAML file")

        # get user specifications
        if 'project' not in config_data:
            raise AnsibleParserError("Project must be included in inventory YAML file")

        zones = config_data['zones']
        query = self._get_query_options(config_data)

        for zone in zones:
            config_data['zone'] = zone
            link = self.self_link(config_data)
            resp = self.fetch_list(config_data, link, query)
            self._populate(resp['items'])
