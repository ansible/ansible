# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: azure_rm
    plugin_type: inventory
    short_description: Azure Resource Manager inventory plugin
    extends_documentation_fragment:
      - azure
    description:
        - Query VM details from Azure Resource Manager
        - Requires a YAML configuration file whose name ends with 'azure_rm.(yml|yaml)'
        - By default, sets C(ansible_host) to the first public IP address found (preferring the primary NIC). If no
          public IPs are found, the first private IP (also preferring the primary NIC). The default may be overridden
          via C(hostvar_expressions); see examples.
    options:
        plugin:
            description: marks this as an instance of the 'azure_rm' plugin
            required: true
            choices: ['azure_rm']
        include_vm_resource_groups:
            description: A list of resource group names to search for virtual machines. '\*' will include all resource
                groups in the subscription.
            default: ['*']
        include_vmss_resource_groups:
            description: A list of resource group names to search for virtual machine scale sets (VMSSs). '\*' will
                include all resource groups in the subscription.
            default: []
        fail_on_template_errors:
            description: When false, template failures during group and filter processing are silently ignored (eg,
                if a filter or group expression refers to an undefined host variable)
            choices: [True, False]
            default: True
        keyed_groups:
            description: Creates groups based on the value of a host variable. Requires a list of dictionaries,
                defining C(key) (the source dictionary-typed variable), C(prefix) (the prefix to use for the new group
                name), and optionally C(separator) (which defaults to C(_))
        conditional_groups:
            description: A mapping of group names to Jinja2 expressions. When the mapped expression is true, the host
                is added to the named group.
        hostvar_expressions:
            description: A mapping of hostvar names to Jinja2 expressions. The value for each host is the result of the
                Jinja2 expression (which may refer to any of the host's existing variables at the time this inventory
                plugin runs).
        exclude_host_filters:
            description: Excludes hosts from the inventory with a list of Jinja2 conditional expressions. Each
                expression in the list is evaluated for each host; when the expression is true, the host is excluded
                from the inventory.
            default: []
        batch_fetch:
            description: To improve performance, results are fetched using an unsupported batch API. Disabling
                C(batch_fetch) uses a much slower serial fetch, resulting in many more round-trips. Generally only
                useful for troubleshooting.
            default: true
        default_host_filters:
            description: A default set of filters that is applied in addition to the conditions in
                C(exclude_host_filters) to exclude powered-off and not-fully-provisioned hosts. Set this to a different
                value or empty list if you need to include hosts in these states.
            default: ['powerstate != "running"', 'provisioning_state != "succeeded"']
        use_contrib_script_compatible_sanitization:
          description:
            - By default this plugin is using a general group name sanitization to create safe and usable group names for use in Ansible.
              This option allows you to override that, in efforts to allow migration from the old inventory script and
              matches the sanitization of groups when the script's ``replace_dash_in_groups`` option is set to ``False``.
              To replicate behavior of ``replace_dash_in_groups = True`` with constructed groups,
              you will need to replace hyphens with underscores via the regex_replace filter for those entries.
            - For this to work you should also turn off the TRANSFORM_INVALID_GROUP_CHARS setting,
              otherwise the core engine will just use the standard sanitization on top.
            - This is not the default as such names break certain functionality as not all characters are valid Python identifiers
              which group names end up being used as.
          type: bool
          default: False
          version_added: '2.8'
        plain_host_names:
          description:
            - By default this plugin will use globally unique host names.
              This option allows you to override that, and use the name that matches the old inventory script naming.
            - This is not the default, as these names are not truly unique, and can conflict with other hosts.
              The default behavior will add extra hashing to the end of the hostname to prevent such conflicts.
          type: bool
          default: False
          version_added: '2.8'
'''

EXAMPLES = '''
# The following host variables are always available:
# public_ipv4_addresses: all public IP addresses, with the primary IP config from the primary NIC first
# public_dns_hostnames: all public DNS hostnames, with the primary IP config from the primary NIC first
# private_ipv4_addresses: all private IP addressses, with the primary IP config from the primary NIC first
# id: the VM's Azure resource ID, eg /subscriptions/00000000-0000-0000-1111-1111aaaabb/resourceGroups/my_rg/providers/Microsoft.Compute/virtualMachines/my_vm
# location: the VM's Azure location, eg 'westus', 'eastus'
# name: the VM's resource name, eg 'myvm'
# powerstate: the VM's current power state, eg: 'running', 'stopped', 'deallocated'
# provisioning_state: the VM's current provisioning state, eg: 'succeeded'
# tags: dictionary of the VM's defined tag values
# resource_type: the VM's resource type, eg: 'Microsoft.Compute/virtualMachine', 'Microsoft.Compute/virtualMachineScaleSets/virtualMachines'
# vmid: the VM's internal SMBIOS ID, eg: '36bca69d-c365-4584-8c06-a62f4a1dc5d2'
# vmss: if the VM is a member of a scaleset (vmss), a dictionary including the id and name of the parent scaleset


# sample 'myazuresub.azure_rm.yaml'

# required for all azure_rm inventory plugin configs
plugin: azure_rm

# forces this plugin to use a CLI auth session instead of the automatic auth source selection (eg, prevents the
# presence of 'ANSIBLE_AZURE_RM_X' environment variables from overriding CLI auth)
auth_source: cli

# fetches VMs from an explicit list of resource groups instead of default all (- '*')
include_vm_resource_groups:
- myrg1
- myrg2

# fetches VMs from VMSSs in all resource groups (defaults to no VMSS fetch)
include_vmss_resource_groups:
- '*'

# places a host in the named group if the associated condition evaluates to true
conditional_groups:
  # since this will be true for every host, every host sourced from this inventory plugin config will be in the
  # group 'all_the_hosts'
  all_the_hosts: true
  # if the VM's "name" variable contains "dbserver", it will be placed in the 'db_hosts' group
  db_hosts: "'dbserver' in name"

# adds variables to each host found by this inventory plugin, whose values are the result of the associated expression
hostvar_expressions:
  my_host_var:
  # A statically-valued expression has to be both single and double-quoted, or use escaped quotes, since the outer
  # layer of quotes will be consumed by YAML. Without the second set of quotes, it interprets 'staticvalue' as a
  # variable instead of a string literal.
  some_statically_valued_var: "'staticvalue'"
  # overrides the default ansible_host value with a custom Jinja2 expression, in this case, the first DNS hostname, or
  # if none are found, the first public IP address.
  ansible_host: (public_dns_hostnames + public_ipv4_addresses) | first

# places hosts in dynamically-created groups based on a variable value.
keyed_groups:
# places each host in a group named 'tag_(tag name)_(tag value)' for each tag on a VM.
- prefix: tag
  key: tags
# places each host in a group named 'azure_loc_(location name)', depending on the VM's location
- prefix: azure_loc
  key: location
# places host in a group named 'some_tag_X' using the value of the 'sometag' tag on a VM as X, and defaulting to the
# value 'none' (eg, the group 'some_tag_none') if the 'sometag' tag is not defined for a VM.
- prefix: some_tag
  key: tags.sometag | default('none')

# excludes a host from the inventory when any of these expressions is true, can refer to any vars defined on the host
exclude_host_filters:
# excludes hosts in the eastus region
- location in ['eastus']
# excludes hosts that are powered off
- powerstate != 'running'
'''

# FUTURE: do we need a set of sane default filters, separate from the user-defineable ones?
# eg, powerstate==running, provisioning_state==succeeded


import hashlib
import json
import re
import uuid

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

from collections import namedtuple
from ansible import release
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.module_utils.six import iteritems
from ansible.module_utils.azure_rm_common import AzureRMAuth
from ansible.errors import AnsibleParserError, AnsibleError
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils._text import to_native, to_bytes
from itertools import chain
from msrest import ServiceClient, Serializer, Deserializer
from msrestazure import AzureConfiguration
from msrestazure.polling.arm_polling import ARMPolling
from msrestazure.tools import parse_resource_id


class AzureRMRestConfiguration(AzureConfiguration):
    def __init__(self, credentials, subscription_id, base_url=None):

        if credentials is None:
            raise ValueError("Parameter 'credentials' must not be None.")
        if subscription_id is None:
            raise ValueError("Parameter 'subscription_id' must not be None.")
        if not base_url:
            base_url = 'https://management.azure.com'

        super(AzureRMRestConfiguration, self).__init__(base_url)

        self.add_user_agent('ansible-dynamic-inventory/{0}'.format(release.__version__))

        self.credentials = credentials
        self.subscription_id = subscription_id


UrlAction = namedtuple('UrlAction', ['url', 'api_version', 'handler', 'handler_args'])


# FUTURE: add Cacheable support once we have a sane serialization format
class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'azure_rm'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self._serializer = Serializer()
        self._deserializer = Deserializer()
        self._hosts = []
        self._filters = None

        # FUTURE: use API profiles with defaults
        self._compute_api_version = '2017-03-30'
        self._network_api_version = '2015-06-15'

        self._default_header_parameters = {'Content-Type': 'application/json; charset=utf-8'}

        self._request_queue = Queue()

        self.azure_auth = None

        self._batch_fetch = False

    def verify_file(self, path):
        '''
            :param loader: an ansible.parsing.dataloader.DataLoader object
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if re.match(r'.{0,}azure_rm\.y(a)?ml$', path):
                return True
        # display.debug("azure_rm inventory filename must end with 'azure_rm.yml' or 'azure_rm.yaml'")
        return False

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        self._read_config_data(path)

        if self.get_option('use_contrib_script_compatible_sanitization'):
            self._sanitize_group_name = self._legacy_script_compatible_group_sanitization

        self._batch_fetch = self.get_option('batch_fetch')

        self._legacy_hostnames = self.get_option('plain_host_names')

        self._filters = self.get_option('exclude_host_filters') + self.get_option('default_host_filters')

        try:
            self._credential_setup()
            self._get_hosts()
        except Exception:
            raise

    def _credential_setup(self):
        auth_options = dict(
            auth_source=self.get_option('auth_source'),
            profile=self.get_option('profile'),
            subscription_id=self.get_option('subscription_id'),
            client_id=self.get_option('client_id'),
            secret=self.get_option('secret'),
            tenant=self.get_option('tenant'),
            ad_user=self.get_option('ad_user'),
            password=self.get_option('password'),
            cloud_environment=self.get_option('cloud_environment'),
            cert_validation_mode=self.get_option('cert_validation_mode'),
            api_profile=self.get_option('api_profile'),
            adfs_authority_url=self.get_option('adfs_authority_url')
        )

        self.azure_auth = AzureRMAuth(**auth_options)

        self._clientconfig = AzureRMRestConfiguration(self.azure_auth.azure_credentials, self.azure_auth.subscription_id,
                                                      self.azure_auth._cloud_environment.endpoints.resource_manager)
        self._client = ServiceClient(self._clientconfig.credentials, self._clientconfig)

    def _enqueue_get(self, url, api_version, handler, handler_args=None):
        if not handler_args:
            handler_args = {}
        self._request_queue.put_nowait(UrlAction(url=url, api_version=api_version, handler=handler, handler_args=handler_args))

    def _enqueue_vm_list(self, rg='*'):
        if not rg or rg == '*':
            url = '/subscriptions/{subscriptionId}/providers/Microsoft.Compute/virtualMachines'
        else:
            url = '/subscriptions/{subscriptionId}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines'

        url = url.format(subscriptionId=self._clientconfig.subscription_id, rg=rg)
        self._enqueue_get(url=url, api_version=self._compute_api_version, handler=self._on_vm_page_response)

    def _enqueue_vmss_list(self, rg=None):
        if not rg or rg == '*':
            url = '/subscriptions/{subscriptionId}/providers/Microsoft.Compute/virtualMachineScaleSets'
        else:
            url = '/subscriptions/{subscriptionId}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachineScaleSets'

        url = url.format(subscriptionId=self._clientconfig.subscription_id, rg=rg)
        self._enqueue_get(url=url, api_version=self._compute_api_version, handler=self._on_vmss_page_response)

    def _get_hosts(self):
        for vm_rg in self.get_option('include_vm_resource_groups'):
            self._enqueue_vm_list(vm_rg)

        for vmss_rg in self.get_option('include_vmss_resource_groups'):
            self._enqueue_vmss_list(vmss_rg)

        if self._batch_fetch:
            self._process_queue_batch()
        else:
            self._process_queue_serial()

        constructable_config_strict = boolean(self.get_option('fail_on_template_errors'))
        constructable_config_compose = self.get_option('hostvar_expressions')
        constructable_config_groups = self.get_option('conditional_groups')
        constructable_config_keyed_groups = self.get_option('keyed_groups')

        for h in self._hosts:
            inventory_hostname = self._get_hostname(h)
            if self._filter_host(inventory_hostname, h.hostvars):
                continue
            self.inventory.add_host(inventory_hostname)
            # FUTURE: configurable default IP list? can already do this via hostvar_expressions
            self.inventory.set_variable(inventory_hostname, "ansible_host",
                                        next(chain(h.hostvars['public_ipv4_addresses'], h.hostvars['private_ipv4_addresses']), None))
            for k, v in iteritems(h.hostvars):
                # FUTURE: configurable hostvar prefix? Makes docs harder...
                self.inventory.set_variable(inventory_hostname, k, v)

            # constructable delegation
            self._set_composite_vars(constructable_config_compose, h.hostvars, inventory_hostname, strict=constructable_config_strict)
            self._add_host_to_composed_groups(constructable_config_groups, h.hostvars, inventory_hostname, strict=constructable_config_strict)
            self._add_host_to_keyed_groups(constructable_config_keyed_groups, h.hostvars, inventory_hostname, strict=constructable_config_strict)

    # FUTURE: fix underlying inventory stuff to allow us to quickly access known groupvars from reconciled host
    def _filter_host(self, inventory_hostname, hostvars):
        self.templar.set_available_variables(hostvars)

        for condition in self._filters:
            # FUTURE: should warn/fail if conditional doesn't return True or False
            conditional = "{{% if {0} %}} True {{% else %}} False {{% endif %}}".format(condition)
            try:
                if boolean(self.templar.template(conditional)):
                    return True
            except Exception as e:
                if boolean(self.get_option('fail_on_template_errors')):
                    raise AnsibleParserError("Error evaluating filter condition '{0}' for host {1}: {2}".format(condition, inventory_hostname, to_native(e)))
                continue

        return False

    def _get_hostname(self, host):
        # FUTURE: configurable hostname sources
        return host.default_inventory_hostname

    def _process_queue_serial(self):
        try:
            while True:
                item = self._request_queue.get_nowait()
                resp = self.send_request(item.url, item.api_version)
                item.handler(resp, **item.handler_args)
        except Empty:
            pass

    def _on_vm_page_response(self, response, vmss=None):
        next_link = response.get('nextLink')

        if next_link:
            self._enqueue_get(url=next_link, api_version=self._compute_api_version, handler=self._on_vm_page_response)

        if 'value' in response:
            for h in response['value']:
                # FUTURE: add direct VM filtering by tag here (performance optimization)?
                self._hosts.append(AzureHost(h, self, vmss=vmss, legacy_name=self._legacy_hostnames))

    def _on_vmss_page_response(self, response):
        next_link = response.get('nextLink')

        if next_link:
            self._enqueue_get(url=next_link, api_version=self._compute_api_version, handler=self._on_vmss_page_response)

        # FUTURE: add direct VMSS filtering by tag here (performance optimization)?
        for vmss in response['value']:
            url = '{0}/virtualMachines'.format(vmss['id'])
            # VMSS instances look close enough to regular VMs that we can share the handler impl...
            self._enqueue_get(url=url, api_version=self._compute_api_version, handler=self._on_vm_page_response, handler_args=dict(vmss=vmss))

    # use the undocumented /batch endpoint to bulk-send up to 500 requests in a single round-trip
    #
    def _process_queue_batch(self):
        while True:
            batch_requests = []
            batch_item_index = 0
            batch_response_handlers = dict()
            try:
                while batch_item_index < 100:
                    item = self._request_queue.get_nowait()

                    name = str(uuid.uuid4())
                    query_parameters = {'api-version': item.api_version}
                    req = self._client.get(item.url, query_parameters)
                    batch_requests.append(dict(httpMethod="GET", url=req.url, name=name))
                    batch_response_handlers[name] = item
                    batch_item_index += 1
            except Empty:
                pass

            if not batch_requests:
                break

            batch_resp = self._send_batch(batch_requests)

            key_name = None
            if 'responses' in batch_resp:
                key_name = 'responses'
            elif 'value' in batch_resp:
                key_name = 'value'
            else:
                raise AnsibleError("didn't find expected key responses/value in batch response")

            for idx, r in enumerate(batch_resp[key_name]):
                status_code = r.get('httpStatusCode')
                returned_name = r['name']
                result = batch_response_handlers[returned_name]
                if status_code != 200:
                    # FUTURE: error-tolerant operation mode (eg, permissions)
                    raise AnsibleError("a batched request failed with status code {0}, url {1}".format(status_code, result.url))
                # FUTURE: store/handle errors from individual handlers
                result.handler(r['content'], **result.handler_args)

    def _send_batch(self, batched_requests):
        url = '/batch'
        query_parameters = {'api-version': '2015-11-01'}

        body_obj = dict(requests=batched_requests)

        body_content = self._serializer.body(body_obj, 'object')

        header = {'x-ms-client-request-id': str(uuid.uuid4())}
        header.update(self._default_header_parameters)

        request = self._client.post(url, query_parameters)
        initial_response = self._client.send(request, header, body_content)

        # FUTURE: configurable timeout?
        poller = ARMPolling(timeout=2)
        poller.initialize(client=self._client,
                          initial_response=initial_response,
                          deserialization_callback=lambda r: self._deserializer('object', r))

        poller.run()

        return poller.resource()

    def send_request(self, url, api_version):
        query_parameters = {'api-version': api_version}
        req = self._client.get(url, query_parameters)
        resp = self._client.send(req, self._default_header_parameters, stream=False)

        resp.raise_for_status()
        content = resp.content

        return json.loads(content)

    @staticmethod
    def _legacy_script_compatible_group_sanitization(name):

        # note that while this mirrors what the script used to do, it has many issues with unicode and usability in python
        regex = re.compile(r"[^A-Za-z0-9\_\-]")

        return regex.sub('_', name)

# VM list (all, N resource groups): VM -> InstanceView, N NICs, N PublicIPAddress)
# VMSS VMs (all SS, N specific SS, N resource groups?): SS -> VM -> InstanceView, N NICs, N PublicIPAddress)


class AzureHost(object):
    _powerstate_regex = re.compile('^PowerState/(?P<powerstate>.+)$')

    def __init__(self, vm_model, inventory_client, vmss=None, legacy_name=False):
        self._inventory_client = inventory_client
        self._vm_model = vm_model
        self._vmss = vmss

        self._instanceview = None

        self._powerstate = "unknown"
        self.nics = []

        if legacy_name:
            self.default_inventory_hostname = vm_model['name']
        else:
            # Azure often doesn't provide a globally-unique filename, so use resource name + a chunk of ID hash
            self.default_inventory_hostname = '{0}_{1}'.format(vm_model['name'], hashlib.sha1(to_bytes(vm_model['id'])).hexdigest()[0:4])

        self._hostvars = {}

        inventory_client._enqueue_get(url="{0}/instanceView".format(vm_model['id']),
                                      api_version=self._inventory_client._compute_api_version,
                                      handler=self._on_instanceview_response)

        nic_refs = vm_model['properties']['networkProfile']['networkInterfaces']
        for nic in nic_refs:
            # single-nic instances don't set primary, so figure it out...
            is_primary = nic.get('properties', {}).get('primary', len(nic_refs) == 1)
            inventory_client._enqueue_get(url=nic['id'], api_version=self._inventory_client._network_api_version,
                                          handler=self._on_nic_response,
                                          handler_args=dict(is_primary=is_primary))

    @property
    def hostvars(self):
        if self._hostvars != {}:
            return self._hostvars

        new_hostvars = dict(
            public_ipv4_addresses=[],
            public_dns_hostnames=[],
            private_ipv4_addresses=[],
            id=self._vm_model['id'],
            location=self._vm_model['location'],
            name=self._vm_model['name'],
            powerstate=self._powerstate,
            provisioning_state=self._vm_model['properties']['provisioningState'].lower(),
            tags=self._vm_model.get('tags', {}),
            resource_type=self._vm_model.get('type', "unknown"),
            vmid=self._vm_model['properties']['vmId'],
            vmss=dict(
                id=self._vmss['id'],
                name=self._vmss['name'],
            ) if self._vmss else {},
            virtual_machine_size=self._vm_model['properties']['hardwareProfile']['vmSize'] if self._vm_model['properties'].get('hardwareProfile') else None,
            plan=self._vm_model['properties']['plan']['name'] if self._vm_model['properties'].get('plan') else None,
            resource_group=parse_resource_id(self._vm_model['id']).get('resource_group').lower()
        )

        # set nic-related values from the primary NIC first
        for nic in sorted(self.nics, key=lambda n: n.is_primary, reverse=True):
            # and from the primary IP config per NIC first
            for ipc in sorted(nic._nic_model['properties']['ipConfigurations'], key=lambda i: i['properties']['primary'], reverse=True):
                private_ip = ipc['properties'].get('privateIPAddress')
                if private_ip:
                    new_hostvars['private_ipv4_addresses'].append(private_ip)
                pip_id = ipc['properties'].get('publicIPAddress', {}).get('id')
                if pip_id:
                    new_hostvars['public_ip_id'] = pip_id

                    pip = nic.public_ips[pip_id]
                    new_hostvars['public_ip_name'] = pip._pip_model['name']
                    new_hostvars['public_ipv4_addresses'].append(pip._pip_model['properties'].get('ipAddress', None))
                    pip_fqdn = pip._pip_model['properties'].get('dnsSettings', {}).get('fqdn')
                    if pip_fqdn:
                        new_hostvars['public_dns_hostnames'].append(pip_fqdn)

            new_hostvars['mac_address'] = nic._nic_model['properties'].get('macAddress')
            new_hostvars['network_interface'] = nic._nic_model['name']
            new_hostvars['network_interface_id'] = nic._nic_model['id']
            new_hostvars['security_group_id'] = nic._nic_model['properties']['networkSecurityGroup']['id'] \
                if nic._nic_model['properties'].get('networkSecurityGroup') else None
            new_hostvars['security_group'] = parse_resource_id(new_hostvars['security_group_id'])['resource_name'] \
                if nic._nic_model['properties'].get('networkSecurityGroup') else None

        # set image and os_disk
        new_hostvars['image'] = {}
        new_hostvars['os_disk'] = {}
        storageProfile = self._vm_model['properties'].get('storageProfile')
        if storageProfile:
            imageReference = storageProfile.get('imageReference')
            if imageReference:
                if imageReference.get('publisher'):
                    new_hostvars['image'] = dict(
                        sku=imageReference.get('sku'),
                        publisher=imageReference.get('publisher'),
                        version=imageReference.get('version'),
                        offer=imageReference.get('offer')
                    )
                elif imageReference.get('id'):
                    new_hostvars['image'] = dict(
                        id=imageReference.get('id')
                    )

            osDisk = storageProfile.get('osDisk')
            new_hostvars['os_disk'] = dict(
                name=osDisk.get('name'),
                operating_system_type=osDisk.get('osType').lower() if osDisk.get('osType') else None
            )

        self._hostvars = new_hostvars

        return self._hostvars

    def _on_instanceview_response(self, vm_instanceview_model):
        self._instanceview = vm_instanceview_model
        self._powerstate = next((self._powerstate_regex.match(s.get('code', '')).group('powerstate')
                                 for s in vm_instanceview_model.get('statuses', []) if self._powerstate_regex.match(s.get('code', ''))), 'unknown')

    def _on_nic_response(self, nic_model, is_primary=False):
        nic = AzureNic(nic_model=nic_model, inventory_client=self._inventory_client, is_primary=is_primary)
        self.nics.append(nic)


class AzureNic(object):
    def __init__(self, nic_model, inventory_client, is_primary=False):
        self._nic_model = nic_model
        self.is_primary = is_primary
        self._inventory_client = inventory_client

        self.public_ips = {}

        if nic_model.get('properties', {}).get('ipConfigurations'):
            for ipc in nic_model['properties']['ipConfigurations']:
                pip = ipc['properties'].get('publicIPAddress')
                if pip:
                    self._inventory_client._enqueue_get(url=pip['id'], api_version=self._inventory_client._network_api_version, handler=self._on_pip_response)

    def _on_pip_response(self, pip_model):
        self.public_ips[pip_model['id']] = AzurePip(pip_model)


class AzurePip(object):
    def __init__(self, pip_model):
        self._pip_model = pip_model
