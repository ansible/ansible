#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, (@zikalino)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_azurefirewall
version_added: '2.9'
short_description: Manage Azure AzureFirewall instance.
description:
  - 'Create, update and delete instance of Azure AzureFirewall.'
options:
  resource_group:
    description:
      - The name of the resource group.
    required: true
  name:
    description:
      - The name of the Azure Firewall.
    required: true
  id:
    description:
      - Resource ID.
  location:
    description:
      - Resource location.
  tags:
    description:
      - Resource tags.
  application_rule_collections:
    description:
      - Collection of application rule collections used by Azure Firewall.
    type: list
    suboptions:
      id:
        description:
          - Resource ID.
      priority:
        description:
          - Priority of the application rule collection resource.
      action:
        description:
          - The action type of a rule collection
        suboptions:
          type:
            description:
              - The type of action.
      rules:
        description:
          - Collection of rules used by a application rule collection.
        type: list
        suboptions:
          name:
            description:
              - Name of the application rule.
          description:
            description:
              - Description of the rule.
          source_addresses:
            description:
              - List of source IP addresses for this rule.
            type: list
          protocols:
            description:
              - Array of ApplicationRuleProtocols.
            type: list
          target_fqdns:
            description:
              - List of FQDNs for this rule.
            type: list
          fqdn_tags:
            description:
              - List of FQDN Tags for this rule.
            type: list
      provisioning_state:
        description:
          - The provisioning state of the resource.
      name:
        description:
          - >-
            Gets name of the resource that is unique within a resource group.
            This name can be used to access the resource.
  nat_rule_collections:
    description:
      - Collection of NAT rule collections used by Azure Firewall.
    type: list
    suboptions:
      id:
        description:
          - Resource ID.
      priority:
        description:
          - Priority of the NAT rule collection resource.
      action:
        description:
          - The action type of a NAT rule collection
        suboptions:
          type:
            description:
              - The type of action.
      rules:
        description:
          - Collection of rules used by a NAT rule collection.
        type: list
        suboptions:
          name:
            description:
              - Name of the NAT rule.
          description:
            description:
              - Description of the rule.
          source_addresses:
            description:
              - List of source IP addresses for this rule.
            type: list
          destination_addresses:
            description:
              - List of destination IP addresses for this rule.
            type: list
          destination_ports:
            description:
              - List of destination ports.
            type: list
          protocols:
            description:
              - >-
                Array of AzureFirewallNetworkRuleProtocols applicable to this
                NAT rule.
            type: list
          translated_address:
            description:
              - The translated address for this NAT rule.
          translated_port:
            description:
              - The translated port for this NAT rule.
      provisioning_state:
        description:
          - The provisioning state of the resource.
      name:
        description:
          - >-
            Gets name of the resource that is unique within a resource group.
            This name can be used to access the resource.
  network_rule_collections:
    description:
      - Collection of network rule collections used by Azure Firewall.
    type: list
    suboptions:
      id:
        description:
          - Resource ID.
      priority:
        description:
          - Priority of the network rule collection resource.
      action:
        description:
          - The action type of a rule collection
        suboptions:
          type:
            description:
              - The type of action.
      rules:
        description:
          - Collection of rules used by a network rule collection.
        type: list
        suboptions:
          name:
            description:
              - Name of the network rule.
          description:
            description:
              - Description of the rule.
          protocols:
            description:
              - Array of AzureFirewallNetworkRuleProtocols.
            type: list
          source_addresses:
            description:
              - List of source IP addresses for this rule.
            type: list
          destination_addresses:
            description:
              - List of destination IP addresses.
            type: list
          destination_ports:
            description:
              - List of destination ports.
            type: list
      provisioning_state:
        description:
          - The provisioning state of the resource.
      name:
        description:
          - >-
            Gets name of the resource that is unique within a resource group.
            This name can be used to access the resource.
  ip_configurations:
    description:
      - IP configuration of the Azure Firewall resource.
    type: list
    suboptions:
      id:
        description:
          - Resource ID.
      subnet:
        description:
          - >-
            Reference of the subnet resource. This resource must be named
            'AzureFirewallSubnet'.
        suboptions:
          id:
            description:
              - Resource ID.
      public_ip_address:
        description:
          - >-
            Reference of the PublicIP resource. This field is a mandatory input
            if subnet is not null.
        suboptions:
          id:
            description:
              - Resource ID.
      provisioning_state:
        description:
          - The provisioning state of the resource.
      name:
        description:
          - >-
            Name of the resource that is unique within a resource group. This
            name can be used to access the resource.
  provisioning_state:
    description:
      - The provisioning state of the resource.
  state:
    description:
      - Assert the state of the AzureFirewall.
      - >-
        Use C(present) to create or update an AzureFirewall and C(absent) to
        delete it.
    default: present
    choices:
      - absent
      - present
extends_documentation_fragment:
  - azure
author:
  - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
- name: Create Azure Firewall
  azure_rm_azurefirewall:
    resource_group: myResourceGroup
    name: myAzureFirewall
    tags:
      key1: value1
    application_rule_collections:
      - priority: '110'
        action: {}
        rules:
          - name: rule1
            description: Deny inbound rule
            source_addresses:
              - 216.58.216.164
              - 10.0.0.0/24
            protocols:
              - protocolType: Https
                port: '443'
            target_fqdns:
              - www.test.com
        name: apprulecoll
    nat_rule_collections:
      - priority: '112'
        action: {}
        rules:
          - name: DNAT-HTTPS-traffic
            description: D-NAT all outbound web traffic for inspection
            source_addresses:
              - '*'
            destination_addresses:
              - 1.2.3.4
            destination_ports:
              - '443'
            protocols:
              - TCP
            translated_address: 1.2.3.5
            translated_port: '8443'
        name: natrulecoll
    network_rule_collections:
      - priority: '112'
        action: {}
        rules:
          - name: L4-traffic
            description: Block traffic based on source IPs and ports
            protocols:
              - TCP
            source_addresses:
              - 192.168.1.1-192.168.1.12
              - 10.1.4.12-10.1.4.255
            destination_addresses:
              - '*'
            destination_ports:
              - 443-444
              - '8443'
        name: netrulecoll
    ip_configurations:
      - subnet:
          id: >-
            /subscriptions/{{ subscription_id }}/resourceGroups/{{
            resource_group }}/providers/Microsoft.Network/virtualNetworks/{{
            virtual_network_name }}/subnets/{{ subnet_name }}
        public_ip_address:
          id: >-
            /subscriptions/{{ subscription_id }}/resourceGroups/{{
            resource_group }}/providers/Microsoft.Network/publicIPAddresses/{{
            public_ip_address_name }}
        name: azureFirewallIpConfiguration
- name: Delete Azure Firewall
  azure_rm_azurefirewall:
    resource_group: myResourceGroup
    name: myAzureFirewall
    state: absent

'''

RETURN = '''
name:
  description:
    - Resource name.
  returned: always
  type: str
  sample: null
type:
  description:
    - Resource type.
  returned: always
  type: str
  sample: null
etag:
  description:
    - >-
      Gets a unique read-only string that changes whenever the resource is
      updated.
  returned: always
  type: str
  sample: null

'''

import time
import json
import re
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from copy import deepcopy
try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network import NetworkManagementClient
    from msrestazure.azure_operation import AzureOperationPoller
    from msrest.polling import LROPoller
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMAzureFirewalls(AzureRMModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                comparison='',
                updatable=False,
                disposition='resource_group_name',
                required=True
            ),
            name=dict(
                type='str',
                comparison='',
                updatable=False,
                disposition='azure_firewall_name',
                required=True
            ),
            id=dict(
                type='str',
                comparison='',
                updatable=False,
                disposition='/'
            ),
            location=dict(
                type='str',
                comparison='',
                updatable=False,
                disposition='/'
            ),
            tags=dict(
                type='unknown[DictionaryType {"$id":"440","$type":"DictionaryType","valueType":{"$id":"441","$type":"PrimaryType","knownPrimaryType":"string","name":{"$id":"442","fixed":false,"raw":"String"},"deprecated":false},"supportsAdditionalProperties":false,"name":{"$id":"443","fixed":false},"deprecated":false}]',
                comparison='',
                updatable=False,
                disposition='/'
            ),
            application_rule_collections=dict(
                type='list',
                comparison='',
                updatable=False,
                disposition='/*',
                options=dict(
                    id=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    priority=dict(
                        type='number',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    action=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
                            type=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*',
                                choices=['Allow',
                                         'Deny']
                            )
                        )
                    ),
                    rules=dict(
                        type='list',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
                            name=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            description=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            source_addresses=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            protocols=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            target_fqdns=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            fqdn_tags=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            )
                        )
                    ),
                    provisioning_state=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        choices=['Succeeded',
                                 'Updating',
                                 'Deleting',
                                 'Failed']
                    ),
                    name=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    )
                )
            ),
            nat_rule_collections=dict(
                type='list',
                comparison='',
                updatable=False,
                disposition='/*',
                options=dict(
                    id=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    priority=dict(
                        type='number',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    action=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
                            type=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*',
                                choices=['Snat',
                                         'Dnat']
                            )
                        )
                    ),
                    rules=dict(
                        type='list',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
                            name=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            description=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            source_addresses=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            destination_addresses=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            destination_ports=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            protocols=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            translated_address=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            translated_port=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            )
                        )
                    ),
                    provisioning_state=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        choices=['Succeeded',
                                 'Updating',
                                 'Deleting',
                                 'Failed']
                    ),
                    name=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    )
                )
            ),
            network_rule_collections=dict(
                type='list',
                comparison='',
                updatable=False,
                disposition='/*',
                options=dict(
                    id=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    priority=dict(
                        type='number',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    action=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
                            type=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*',
                                choices=['Allow',
                                         'Deny']
                            )
                        )
                    ),
                    rules=dict(
                        type='list',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
                            name=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            description=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            protocols=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            source_addresses=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            destination_addresses=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            ),
                            destination_ports=dict(
                                type='list',
                                comparison='',
                                updatable=False,
                                disposition='*'
                            )
                        )
                    ),
                    provisioning_state=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        choices=['Succeeded',
                                 'Updating',
                                 'Deleting',
                                 'Failed']
                    ),
                    name=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    )
                )
            ),
            ip_configurations=dict(
                type='list',
                comparison='',
                updatable=False,
                disposition='/*',
                options=dict(
                    id=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    subnet=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
                            id=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*',
                                pattern='/subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.Network/virtualNetworks/{{ virtual_network_name }}/subnets/{{ name }}'
                            )
                        )
                    ),
                    public_ip_address=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
                            id=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='*',
                                pattern='/subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.Network/publicIPAddresses/{{ name }}'
                            )
                        )
                    ),
                    provisioning_state=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        choices=['Succeeded',
                                 'Updating',
                                 'Deleting',
                                 'Failed']
                    ),
                    name=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    )
                )
            ),
            provisioning_state=dict(
                type='str',
                comparison='',
                updatable=False,
                disposition='/*',
                choices=['Succeeded',
                         'Updating',
                         'Deleting',
                         'Failed']
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.body = {}

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMAzureFirewalls, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                    supports_check_mode=True,
                                                    supports_tags=False)

    def exec_module(self, **kwargs):
        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                self.body[key] = kwargs[key]

        self.inflate_parameters(self.module_arg_spec, self.body, 0)

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(NetworkManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if 'location' not in self.body:
            self.body['location'] = resource_group.location


        old_response = self.get_resource()

        if not old_response:
            if self.state == 'present':
                self.to_do = Actions.Create
        else:
            if self.state == 'absent':
                self.to_do = Actions.Delete
            else:
                modifiers = {}
                self.create_compare_modifiers(self.module_arg_spec, '', modifiers)
                if not self.default_compare(modifiers, self.body, old_response, '', self.results):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.results['changed'] = True
            if self.check_mode:
                return self.results
            response = self.create_update_resource()
            self.results['response'] = response
        elif self.to_do == Actions.Delete:
            self.results['changed'] = True
            if self.check_mode:
                return self.results
            self.delete_resource()
        else:
            self.results['changed'] = False
            response = old_response

        #if response:
        #    self.results["name"] = response["name"]
        #    self.results["type"] = response["type"]
        #    self.results["etag"] = response["etag"]

        return self.results

    def create_update_resource(self):
        try:
            response = self.mgmt_client.azure_firewalls.create_or_update(resource_group_name=self.resource_group,
                                                                         azure_firewall_name=self.name,
                                                                         parameters=self.body)
            if isinstance(response, AzureOperationPoller) or isinstance(response, LROPoller):
               response = self.get_poller_result(response)
        except CloudError as exc:
            self.log('Error attempting to create the AzureFirewall instance.')
            self.fail('Error creating the AzureFirewall instance: {0}'.format(str(exc)))
        return response.as_dict()

    def delete_resource(self):
        # self.log('Deleting the AzureFirewall instance {0}'.format(self.))
        try:
            response = self.mgmt_client.azure_firewalls.delete(resource_group_name=self.resource_group,
                                                               azure_firewall_name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the AzureFirewall instance.')
            self.fail('Error deleting the AzureFirewall instance: {0}'.format(str(e)))

        return True

    def get_resource(self):
        # self.log('Checking if the AzureFirewall instance {0} is present'.format(self.))
        found = False
        try:
            response = self.mgmt_client.azure_firewalls.get(resource_group_name=self.resource_group,
                                                            azure_firewall_name=self.name)
        except CloudError as e:
           return False
        return response.as_dict()

    def inflate_parameters(self, spec, body, level):
        if isinstance(body, list):
            for item in body:
                self.inflate_parameters(spec, item, level)
            return
        for name in spec.keys():
            # first check if option was passed
            param = body.get(name)
            if not param:
                continue
            # check if pattern needs to be used
            pattern = spec[name].get('pattern', None)
            if pattern:
                param = self.normalize_resource_id(param, pattern)
                body[name] = param
            disposition = spec[name].get('disposition', '*')
            if level == 0 and not disposition.startswith('/'):
                continue
            if disposition == '/':
                disposition = '/*'
            parts = disposition.split('/')
            if parts[0] == '':
                # should fail if level is > 0?
                parts.pop(0)
            target_dict = body
            while len(parts) > 1:
                target_dict = target_dict.setdefault(parts.pop(0), {})
            targetName = parts[0] if parts[0] != '*' else name
            target_dict[targetName] = body.pop(name)
            if spec[name].get('options'):
                self.inflate_parameters(spec[name].get('options'), target_dict[targetName], level + 1)

    def normalize_resource_id(self, value, pattern):
        '''
        Return a proper resource id string..

        :param resource_id: It could be a resource name, resource id or dict containing parts from the pattern.
        :param pattern: pattern of resource is, just like in Azure Swagger
        '''
        pattern_parts = pattern.split('/')
        for i in range(len(pattern_parts)):
            x = re.sub('[{} ]+', '', pattern_parts[i], 2)
            if len(x) < len(pattern_parts[i]):
                pattern_parts[i] = '{' + re.sub('([a-z0-9])([A-Z])', r'\1_\2', x).lower() + '}'

        if isinstance(value, str):
            value_parts = value.split('/')
            if len(value_parts) == 1:
                value_dict = {}
                value_dict['name'] = value
            else:
                if len(value_parts) != len(pattern_parts):
                    return None
            value_dict = {}
            for i in range(len(value_parts)):
                if pattern_parts[i].startswith('{'):
                    value_dict[pattern_parts[i][1:-1]] = value_parts[i]
                elif value_parts[i].lower() != pattern_parts[i].lower():
                    return None
        elif isinstance(value, dict):
            value_dict = value
        else:
            return None

        if not value_dict.get('subscription_id'):
            value_dict['subscription_id'] = self.subscription_id
        if not value_dict.get('resource_group'):
            value_dict['resource_group'] = self.resource_group

        for i in range(len(pattern_parts)):
            if pattern_parts[i].startswith('{'):
                value = value_dict.get(pattern_parts[i][1:-1], None)
                if not value:
                    return None
                pattern_parts[i] = value

        return '/'.join(pattern_parts)

    def create_compare_modifiers(self, arg_spec, path, result):
        for k in arg_spec.keys():
            o = arg_spec[k]
            updatable = o.get('updatable', True)
            comparison = o.get('comparison', 'default')
            p = (path +
                 ('/' if len(path) > 0 else '') +
                 o.get('disposition', '*').replace('*', k) +
                 ('/*' if o['type'] == 'list' else ''))
            if comparison != 'default' or not updatable:
                result[p] = { 'updatable': updatable, 'comparison': comparison }
            if o.get('options'):
                self.create_compare_modifiers(o.get('options'), p, result)

    def default_compare(self, modifiers, new, old, path, result):
        if new is None:
            return True
        elif isinstance(new, dict):
            if not isinstance(old, dict):
                result['compare'] = 'changed [' + path + '] old dict is null'
                return False
            for k in new.keys():
                if not self.default_compare(modifiers, new.get(k), old.get(k, None), path + '/' + k, result):
                    return False
            return True
        elif isinstance(new, list):
            if not isinstance(old, list) or len(new) != len(old):
                result['compare'] = 'changed [' + path + '] length is different or null'
                return False
            if isinstance(old[0], dict):
                key = None
                if 'id' in old[0] and 'id' in new[0]:
                    key = 'id'
                elif 'name' in old[0] and 'name' in new[0]:
                    key = 'name'
                else:
                    key = old[0].keys()[0]
                new = sorted(new, key=lambda x: x.get(key, None))
                old = sorted(old, key=lambda x: x.get(key, None))
            else:
                new = sorted(new)
                old = sorted(old)
            for i in range(len(new)):
                if not self.default_compare(modifiers, new[i], old[i], path + '/*', result):
                    return False
            return True
        else:
            updatable = modifiers.get(path, {}).get('updatable', True)
            comparison = modifiers.get(path, {}).get('comparison', 'default')
            if path == '/location' or path.endswith('locationName'):
                new = new.replace(' ', '').lower()
                old = old.replace(' ', '').lower()
            elif path.endswith('adminPassword') or path.endswith('administratorLoginPassword') or path.endswith('createMode'):
                return True
            if str(new) == str(old):
                result['compare'] = result.get('compare', '') + "(" + str(new) + ":" + str(old) + ")"
                return True
            else:
                result['compare'] = 'changed [' + path + '] ' + str(new) + ' != ' + str(old)
                if updatable:
                    return False
                else:
                    # XXX change new value to old
                    self.module.warn("property '" + path + "' cannot be updated (" + str(old) + "->" + str(new) + ")")


def main():
    AzureRMAzureFirewalls()


if __name__ == '__main__':
    main()
