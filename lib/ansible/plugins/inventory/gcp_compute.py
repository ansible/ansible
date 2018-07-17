# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: gcp_compute
    plugin_type: inventory
    short_description: Google Cloud Compute Engine inventory source
    requirements:
        - requests >= 2.18.4
        - google-auth >= 1.3.0
    extends_documentation_fragment:
        - constructed
        - inventory_cache
    description:
        - Get inventory hosts from Google Cloud Platform GCE.
        - Uses a <name>.gcp.yaml (or <name>.gcp.yml) YAML configuration file.
    options:
        plugin:
            description: token that ensures this is a source file for the 'gcp_compute' plugin.
            required: True
            choices: ['gcp_compute']
        zones:
          description: A list of regions in which to describe GCE instances.
          default: all zones available to a given project
        projects:
          description: A list of projects in which to describe GCE instances.
        filters:
          description: >
            A list of filter value pairs. Available filters are listed here
            U(https://cloud.google.com/compute/docs/reference/rest/v1/instances/list).
            Each additional filter in the list will act be added as an AND condition
            (filter1 and filter2)
        hostnames:
          description: A list of options that describe the ordering for which
              hostnames should be assigned. Currently supported hostnames are
              'public_ip', 'private_ip', or 'name'.
          default: ['public_ip', 'private_ip', 'name']
        auth_kind:
            description:
                - The type of credential used.
        service_account_file:
            description:
                - The path of a Service Account JSON file if serviceaccount is selected as type.
        service_account_email:
            description:
                - An optional service account email address if machineaccount is selected
                  and the user does not wish to use the default email.
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

    def _populate_host(self, item):
        '''
            :param item: A GCP instance
        '''
        hostname = self._get_hostname(item)
        self.inventory.add_host(hostname)
        for key in item:
            self.inventory.set_variable(hostname, key, item[key])
        self.inventory.add_child('all', hostname)

    def verify_file(self, path):
        '''
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith('.gcp.yml') or path.endswith('.gcp.yaml'):
                return True
            elif path.endswith('.gcp_compute.yml') or path.endswith('.gcp_compute.yaml'):
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

    def _get_zones(self, config_data):
        '''
            :param config_data: dict of info from inventory file
            :return an array of zones that this project has access to
        '''
        link = "https://www.googleapis.com/compute/v1/projects/{project}/zones".format(**config_data)
        zones = []
        zones_response = self.fetch_list(config_data, link, '')
        for item in zones_response['items']:
            zones.append(item['name'])
        return zones

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
        if result['kind'] != 'compute#instanceList' and result['kind'] != 'compute#zoneList':
            module.fail_json(msg="Incorrect result: {kind}".format(**result))

        return result

    def _format_items(self, items):
        '''
            :param items: A list of hosts
        '''
        for host in items:
            if 'zone' in host:
                host['zone_selflink'] = host['zone']
                host['zone'] = host['zone'].split('/')[-1]
            if 'machineType' in host:
                host['machineType_selflink'] = host['machineType']
                host['machineType'] = host['machineType'].split('/')[-1]

            if 'networkInterfaces' in host:
                for network in host['networkInterfaces']:
                    if 'network' in network:
                        network['network'] = self._format_network_info(network['network'])
                    if 'subnetwork' in network:
                        network['subnetwork'] = self._format_network_info(network['subnetwork'])

            host['project'] = host['selfLink'].split('/')[6]
        return items

    def _add_hosts(self, items, config_data, format_items=True):
        '''
            :param items: A list of hosts
            :param config_data: configuration data
            :param format_items: format items or not
        '''
        if not items:
            return
        if format_items:
            items = self._format_items(items)

        for host in items:
            self._populate_host(host)

            hostname = self._get_hostname(host)
            self._set_composite_vars(self.get_option('compose'), host, hostname)
            self._add_host_to_composed_groups(self.get_option('groups'), host, hostname)
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host, hostname)

    def _format_network_info(self, address):
        '''
            :param address: A GCP network address
            :return a dict with network shortname and region
        '''
        split = address.split('/')
        region = ''
        if 'global' in split:
            region = 'global'
        else:
            region = split[8]
        return {
            'region': region,
            'name': split[-1],
            'selfLink': address
        }

    def _get_hostname(self, item):
        '''
            :param item: A host response from GCP
            :return the hostname of this instance
        '''
        hostname_ordering = ['public_ip', 'private_ip', 'name']
        if self.get_option('hostnames'):
            hostname_ordering = self.get_option('hostnames')

        for order in hostname_ordering:
            name = None
            if order == 'public_ip':
                name = self._get_publicip(item)
            elif order == 'private_ip':
                name = self._get_privateip(item)
            elif order == 'name':
                name = item[u'name']
            else:
                raise AnsibleParserError("%s is not a valid hostname precedent" % order)

            if name:
                return name

        raise AnsibleParserError("No valid name found for host")

    def _get_publicip(self, item):
        '''
            :param item: A host response from GCP
            :return the publicIP of this instance or None
        '''
        # Get public IP if exists
        for interface in item['networkInterfaces']:
            if 'accessConfigs' in interface:
                for accessConfig in interface['accessConfigs']:
                    if 'natIP' in accessConfig:
                        return accessConfig[u'natIP']
        return None

    def _get_privateip(self, item):
        '''
            :param item: A host response from GCP
            :return the privateIP of this instance or None
        '''
        # Fallback: Get private IP
        for interface in item[u'networkInterfaces']:
            if 'networkIP' in interface:
                return interface[u'networkIP']

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = {}
        if self.verify_file(path):
            config_data = self._read_config_data(path)

        # get user specifications
        if 'zones' in config_data:
            if not isinstance(config_data['zones'], list):
                raise AnsibleParserError("Zones must be a list in GCP inventory YAML files")

        # get user specifications
        if 'projects' not in config_data:
            raise AnsibleParserError("Projects must be included in inventory YAML file")

        if not isinstance(config_data['projects'], list):
            raise AnsibleParserError("Projects must be a list in GCP inventory YAML files")

        projects = config_data['projects']
        zones = config_data.get('zones')
        config_data['scopes'] = ['https://www.googleapis.com/auth/compute']

        query = self._get_query_options(config_data['filters'])

        # Cache logic
        if cache:
            cache = self.get_option('cache')
            cache_key = self.get_cache_key(path)
        else:
            cache_key = None

        cache_needs_update = False
        if cache:
            try:
                results = self.cache.get(cache_key)
                for project in results:
                    for zone in results[project]:
                        self._add_hosts(results[project][zone], config_data, False)
            except KeyError:
                cache_needs_update = True

        if not cache or cache_needs_update:
            cached_data = {}
            for project in projects:
                cached_data[project] = {}
                config_data['project'] = project
                if not zones:
                    zones = self._get_zones(config_data)
                for zone in zones:
                    config_data['zone'] = zone
                    link = self.self_link(config_data)
                    resp = self.fetch_list(config_data, link, query)
                    self._add_hosts(resp.get('items'), config_data)
                    cached_data[project][zone] = resp.get('items')

        if cache_needs_update:
            self.cache.set(cache_key, cached_data)
