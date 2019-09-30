# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native, to_text
from ansible.plugins.inventory import (
    BaseInventoryPlugin,
    Constructable,
    Cacheable
)
from ansible.utils.display import Display

try:
    import requests
except ImportError:
    raise AnsibleError(
        'The stackpath_compute dynamic inventory plugin requires requests.'
    )

DOCUMENTATION = '''
    name: stackpath_compute
    plugin_type: inventory
    short_description: StackPath Edge Computing inventory source
    requirements:
        - requests
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    description:
        - Get inventory hosts from StackPath Edge Computing.
        - Uses a YAML configuration file that ends with stackpath_compute.(yml|yaml).
    options:
        plugin:
            description: >
                A token that ensures this is a source file for the 'stackpath_compute' plugin.
            required: True
            choices: ['stackpath_compute']
        client_id:
            description: >
                An OAuth client ID generated from the API Management section of the StackPath customer portal
                U(https://control.stackpath.net/api-management)
            requierd: True
        client_secret:
            description: >
                An OAuth client secret generated from the API Management section of the StackPath customer portal
                U(https://control.stackpath.net/api-management)
            required: True
        stack_ids:
            description: >
                A list of Stack IDs to query instnaces in. If no entry then get instances in all stacks on the account
                U(https://developer.stackpath.com/docs/en/getting-started/#get-your-stack-id)
            required: False
        use_internal_ip:
            description: >
                Whether or not to use internal IP addresses, yes to use internal addresses, no to use external addresses.
                Defaults to external
            requiered: False
            choices: ['yes', 'no']
'''

EXAMPLES = '''

# example using credentials to fetch all workload instances in a stack.
---
plugin: stackpath_compute
client_id: my_client_id
client_secret: my_client_secret
stack_ids:
- my_first_stack_id
- my_other_stack_id
use_internal_ip: no

'''

display = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'stackpath_compute'

    def __init__(self):
        super(InventoryModule, self).__init__()

        # credentials
        self.client_id = None
        self.client_secret = None
        self.stack_id = None
        self.api_host = "https://gateway.stackpath.com"
        self.group_keys = [
            "stackId", "workloadId", "cityCode",
            "countryCode", "continent", "target", "name", "workloadSlug"]

    def _set_credentials(self):
        '''
            :param config_data: contents of the inventory config file
        '''

        self.client_id = self.get_option('client_id')
        self.client_secret = self.get_option('client_secret')

        if not self.client_id or not self.client_secret:
            raise AnsibleError("Insufficient credentials found."
                               "Please provide them in your inventory"
                               " configuration file.")

    def _authenticate(self):
        payload = json.dumps(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
        )
        headers = {
            "Content-Type": "application/json"
        }
        self.auth_token = requests.post(
            self.api_host + '/identity/v1/oauth2/token',
            headers=headers, data=payload).json()["access_token"]

    def _query(self):
        results = []
        self._authenticate()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.auth_token
        }
        for stack_id in self.stack_ids:
            try:
                workloads = requests.get(self.api_host + '/workload/v1/stacks/' +
                                         stack_id + '/workloads',
                                         headers=headers).json()["results"]
            except Exception as e:
                raise AnsibleError("Failed to get workloads from the StackPath API: %s" % to_native(e))
            for workload in workloads:
                try:
                    workload_instances = requests.get(
                        self.api_host + '/workload/v1/stacks/' + stack_id +
                        '/workloads/' + workload["id"] + '/instances',
                        headers=headers).json()["results"]
                except Exception as e:
                    raise AnsibleError("Failed to get workload instances from the StackPath API: %s" % to_native(e))
                for instance in workload_instances:
                    if instance["phase"] == "RUNNING":
                        instance["stackId"] = stack_id
                        instance["workloadId"] = workload["id"]
                        instance["workloadSlug"] = workload["slug"]
                        instance["cityCode"] = instance["location"]["cityCode"]
                        instance["countryCode"] = instance["location"]["countryCode"]
                        instance["continent"] = instance["location"]["continent"]
                        instance["target"] = instance["metadata"]["labels"]["workload.platform.stackpath.net/target-name"]
                        results.append(instance)
        return results

    def _populate(self, instances):
        for instance in instances:
            for group_key in self.group_keys:
                group = group_key + "_" + instance[group_key]
                group = group.lower().replace(" ", "_").replace("-", "_")
                self.inventory.add_group(group)
                self.inventory.add_host(instance[self.hostname_key],
                                        group=group)

    def _get_stack_ids(self):
        self._authenticate()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.auth_token
        }
        stacks = requests.get(self.api_host + '/stack/v1/stacks',
                              headers=headers).json()["results"]
        self.stack_ids = [stack["id"] for stack in stacks]

    def verify_file(self, path):
        '''
            :param loader: an ansible.parsing.dataloader.DataLoader object
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('stackpath_compute.yml', 'stackpath_compute.yaml')):
                return True
        display.debug(
            "stackpath_compute inventory filename must end with \
            'stackpath_compute.yml' or 'stackpath_compute.yaml'"
        )
        return False

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        self._read_config_data(path)

        self._set_credentials()

        # get user specifications
        self.use_internal_ip = self.get_option('use_internal_ip')
        if self.use_internal_ip:
            self.hostname_key = "ipAddress"
        else:
            self.hostname_key = "externalIpAddress"

        self.stack_ids = self.get_option('stack_ids')
        if not self.stack_ids:
            try:
                self._get_stack_ids()
            except Exception as e:
                raise AnsibleError("Failed to get stack IDs from the Stackpath API: %s" % to_native(e))

        cache_key = self.get_cache_key(path)
        # false when refresh_cache or --flush-cache is used
        if cache:
            # get the user-specified directive
            cache = self.get_option('cache')

        # Generate inventory
        cache_needs_update = False
        if cache:
            try:
                results = self._cache[cache_key]
            except KeyError:
                # if cache expires or cache file doesn't exist
                cache_needs_update = True

        if not cache or cache_needs_update:
            results = self._query()

        self._populate(results)

        # If the cache has expired/doesn't exist or
        # if refresh_inventory/flush cache is used
        # when the user is using caching, update the cached inventory
        if cache_needs_update or (not cache and self.get_option('cache')):
            self._cache[cache_key] = results
