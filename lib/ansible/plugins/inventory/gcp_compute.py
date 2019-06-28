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
        - Uses a YAML configuration file that ends with gcp_compute.(yml|yaml) or gcp.(yml|yaml).
    options:
        plugin:
            description: token that ensures this is a source file for the 'gcp_compute' plugin.
            required: True
            choices: ['gcp_compute']
        zones:
          description: A list of regions in which to describe GCE instances.
                       If none provided, it defaults to all zones available to a given project.
          type: list
        projects:
          description: A list of projects in which to describe GCE instances.
          type: list
          required: True
        filters:
          description: >
            A list of filter value pairs. Available filters are listed here
            U(https://cloud.google.com/compute/docs/reference/rest/v1/instances/aggregatedList).
            Each additional filter in the list will act be added as an AND condition
            (filter1 and filter2)
          type: list
        hostnames:
          description: A list of options that describe the ordering for which
              hostnames should be assigned. Currently supported hostnames are
              'public_ip', 'private_ip', or 'name'.
          default: ['public_ip', 'private_ip', 'name']
          type: list
        auth_kind:
            description:
                - The type of credential used.
            required: True
            choices: ['application', 'serviceaccount', 'machineaccount']
            env:
                - name: GCP_AUTH_KIND
                  version_added: "2.8.2"
        scopes:
            description: list of authentication scopes
            type: list
            default: ['https://www.googleapis.com/auth/compute']
            env:
                - name: GCP_SCOPES
                  version_added: "2.8.2"
        service_account_file:
            description:
                - The path of a Service Account JSON file if serviceaccount is selected as type.
            type: path
            env:
                - name: GCP_SERVICE_ACCOUNT_FILE
                  version_added: "2.8.2"
                - name: GCE_CREDENTIALS_FILE_PATH
                  version_added: "2.8"
        service_account_contents:
            description:
                - A string representing the contents of a Service Account JSON file. This should not be passed in as a dictionary,
                  but a string that has the exact contents of a service account json file (valid JSON).
            type: string
            env:
                - name: GCP_SERVICE_ACCOUNT_CONTENTS
            version_added: "2.8.2"
        service_account_email:
            description:
                - An optional service account email address if machineaccount is selected
                  and the user does not wish to use the default email.
            env:
                - name: GCP_SERVICE_ACCOUNT_EMAIL
                  version_added: "2.8.2"
        vars_prefix:
            description: prefix to apply to host variables, does not include facts nor params
            default: ''
        use_contrib_script_compatible_sanitization:
          description:
            - By default this plugin is using a general group name sanitization to create safe and usable group names for use in Ansible.
              This option allows you to override that, in efforts to allow migration from the old inventory script.
            - For this to work you should also turn off the TRANSFORM_INVALID_GROUP_CHARS setting,
              otherwise the core engine will just use the standard sanitization on top.
            - This is not the default as such names break certain functionality as not all characters are valid Python identifiers
              which group names end up being used as.
          type: bool
          default: False
          version_added: '2.8'
        retrieve_image_info:
          description:
            - Populate the C(image) host fact for the instances returned with the GCP image name
            - By default this plugin does not attempt to resolve the boot image of an instance to the image name cataloged in GCP
              because of the performance overhead of the task.
            - Unless this option is enabled, the C(image) host variable will be C(null)
          type: bool
          default: False
          version_added: '2.8'
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
service_account_file: /tmp/service_account.json
auth_kind: serviceaccount
scopes:
 - 'https://www.googleapis.com/auth/cloud-platform'
 - 'https://www.googleapis.com/auth/compute.readonly'
keyed_groups:
  # Create groups from GCE labels
  - prefix: gcp
    key: labels
hostnames:
  # List host by name instead of the default public ip
  - name
compose:
  # Set an inventory parameter to use the Public IP address to connect to the host
  # For Private ip use "networkInterfaces[0].networkIP"
  ansible_host: networkInterfaces[0].accessConfigs[0].natIP
'''

import json

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.gcp_utils import GcpSession, navigate_hash, GcpRequestException, HAS_GOOGLE_LIBRARIES
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable


# Mocking a module to reuse module_utils
class GcpMockModule(object):
    def __init__(self, params):
        self.params = params

    def fail_json(self, *args, **kwargs):
        raise AnsibleError(kwargs['msg'])


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'gcp_compute'

    _instances = r"https://www.googleapis.com/compute/v1/projects/%s/aggregated/instances"

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
            try:
                self.inventory.set_variable(hostname, self.get_option('vars_prefix') + key, item[key])
            except (ValueError, TypeError) as e:
                self.display.warning("Could not set host info hostvar for %s, skipping %s: %s" % (hostname, key, to_text(e)))
        self.inventory.add_child('all', hostname)

    def verify_file(self, path):
        '''
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('gcp.yml', 'gcp.yaml')):
                return True
            elif path.endswith(('gcp_compute.yml', 'gcp_compute.yaml')):
                return True
        return False

    def fetch_list(self, params, link, query):
        '''
            :param params: a dict containing all of the fields relevant to build URL
            :param link: a formatted URL
            :param query: a formatted query string
            :return the JSON response containing a list of instances.
        '''
        response = self.auth_session.get(link, params={'filter': query})
        return self._return_if_object(self.fake_module, response)

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
        if result['kind'] != 'compute#instanceAggregatedList' and result['kind'] != 'compute#zoneList':
            module.fail_json(msg="Incorrect result: {kind}".format(**result))

        return result

    def _format_items(self, items, project_disks):
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
            host['image'] = self._get_image(host, project_disks)
        return items

    def _add_hosts(self, items, config_data, format_items=True, project_disks=None):
        '''
            :param items: A list of hosts
            :param config_data: configuration data
            :param format_items: format items or not
        '''
        if not items:
            return
        if format_items:
            items = self._format_items(items, project_disks)

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

    def _get_image(self, instance, project_disks):
        '''
            :param instance: A instance response from GCP
            :return the image of this instance or None
        '''
        image = None
        if project_disks and 'disks' in instance:
            for disk in instance['disks']:
                if disk.get('boot'):
                    image = project_disks[disk["source"]]
        return image

    def _get_project_disks(self, config_data, query):
        '''
            project space disk images
        '''

        try:
            self._project_disks
        except AttributeError:
            self._project_disks = {}
            request_params = {'maxResults': 500, 'filter': query}

            for project in config_data['projects']:
                session_responses = []
                page_token = True
                while page_token:
                    response = self.auth_session.get(
                        'https://www.googleapis.com/compute/v1/projects/{0}/aggregated/disks'.format(project),
                        params=request_params
                    )
                    response_json = response.json()
                    if 'nextPageToken' in response_json:
                        request_params['pageToken'] = response_json['nextPageToken']
                    elif 'pageToken' in request_params:
                        del request_params['pageToken']

                    if 'items' in response_json:
                        session_responses.append(response_json)
                    page_token = 'pageToken' in request_params

            for response in session_responses:
                if 'items' in response:
                    # example k would be a zone or region name
                    # example v would be { "disks" : [], "otherkey" : "..." }
                    for zone_or_region, aggregate in response['items'].items():
                        if 'zones' in zone_or_region:
                            if 'disks' in aggregate:
                                zone = zone_or_region.replace('zones/', '')
                                for disk in aggregate['disks']:
                                    if 'zones' in config_data and zone in config_data['zones']:
                                        # If zones specified, only store those zones' data
                                        if 'sourceImage' in disk:
                                            self._project_disks[disk['selfLink']] = disk['sourceImage'].split('/')[-1]
                                        else:
                                            self._project_disks[disk['selfLink']] = disk['selfLink'].split('/')[-1]

                                    else:
                                        if 'sourceImage' in disk:
                                            self._project_disks[disk['selfLink']] = disk['sourceImage'].split('/')[-1]
                                        else:
                                            self._project_disks[disk['selfLink']] = disk['selfLink'].split('/')[-1]

        return self._project_disks

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

        if not HAS_GOOGLE_LIBRARIES:
            raise AnsibleParserError('gce inventory plugin cannot start: %s' % missing_required_lib('google-auth'))

        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = {}
        config_data = self._read_config_data(path)

        if self.get_option('use_contrib_script_compatible_sanitization'):
            self._sanitize_group_name = self._legacy_script_compatible_group_sanitization

        # setup parameters as expected by 'fake module class' to reuse module_utils w/o changing the API
        params = {
            'filters': self.get_option('filters'),
            'projects': self.get_option('projects'),
            'scopes': self.get_option('scopes'),
            'zones': self.get_option('zones'),
            'auth_kind': self.get_option('auth_kind'),
            'service_account_file': self.get_option('service_account_file'),
            'service_account_contents': self.get_option('service_account_contents'),
            'service_account_email': self.get_option('service_account_email'),
        }

        self.fake_module = GcpMockModule(params)
        self.auth_session = GcpSession(self.fake_module, 'compute')

        query = self._get_query_options(params['filters'])

        if self.get_option('retrieve_image_info'):
            project_disks = self._get_project_disks(config_data, query)
        else:
            project_disks = None

        # Cache logic
        if cache:
            cache = self.get_option('cache')
            cache_key = self.get_cache_key(path)
        else:
            cache_key = None

        cache_needs_update = False
        if cache:
            try:
                results = self._cache[cache_key]
                for project in results:
                    for zone in results[project]:
                        self._add_hosts(results[project][zone], config_data, False, project_disks=project_disks)
            except KeyError:
                cache_needs_update = True

        if not cache or cache_needs_update:
            cached_data = {}
            for project in params['projects']:
                cached_data[project] = {}
                params['project'] = project
                zones = params['zones']
                # Fetch all instances
                link = self._instances % project
                resp = self.fetch_list(params, link, query)
                for key, value in resp.get('items').items():
                    if 'instances' in value:
                        # Key is in format: "zones/europe-west1-b"
                        zone = key[6:]
                        if not zones or zone in zones:
                            self._add_hosts(value['instances'], config_data, project_disks=project_disks)
                            cached_data[project][zone] = value['instances']

        if cache_needs_update:
            self._cache[cache_key] = cached_data

    @staticmethod
    def _legacy_script_compatible_group_sanitization(name):

        return name
