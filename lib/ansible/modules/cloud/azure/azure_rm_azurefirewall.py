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
  application_rule_collections:
    description:
      - Collection of application rule collections used by Azure Firewall.
    type: list
    suboptions:
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
      subnet:
        description:
          - Resource ID.
      public_ip_address:
        description:
          - Resource ID.
      name:
        description:
          - >-
            Name of the resource that is unique within a resource group. This
            name can be used to access the resource.
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
  - azure_tags
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
        action:
          type: Deny
        rules:
          - name: rule1
            description: Deny inbound rule
            source_addresses:
              - 216.58.216.164
              - 10.0.0.0/24
            protocols:
              - type: https
                port: '443'
            target_fqdns:
              - www.test.com
        name: apprulecoll
    nat_rule_collections:
      - priority: '112'
        action:
          type: Dnat
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
              - tcp
            translated_address: 1.2.3.5
            translated_port: '8443'
        name: natrulecoll
    network_rule_collections:
      - priority: '112'
        action:
          type: Deny
        rules:
          - name: L4-traffic
            description: Block traffic based on source IPs and ports
            protocols:
              - tcp
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
      - subnet: >-
          /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group
          }}/providers/Microsoft.Network/virtualNetworks/{{ virtual_network_name
          }}/subnets/{{ subnet_name }}
        public_ip_address: >-
          /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group
          }}/providers/Microsoft.Network/publicIPAddresses/{{
          public_ip_address_name }}
        name: azureFirewallIpConfiguration
- name: Delete Azure Firewall
  azure_rm_azurefirewall:
    resource_group: myResourceGroup
    name: myAzureFirewall
    state: absent

'''

RETURN = '''
id:
  description:
    - Resource ID.
  returned: always
  type: str
  sample: null

'''

import time
import json
import re
from ansible.module_utils.azure_rm_common_ext import AzureRMModuleBaseExt
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


class AzureRMAzureFirewalls(AzureRMModuleBaseExt):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                disposition='resource_group_name',
                required=True
            ),
            name=dict(
                type='str',
                disposition='azure_firewall_name',
                required=True
            ),
            id=dict(
                type='str',
                disposition='/'
            ),
            location=dict(
                type='str',
                updatable=False,
                disposition='/'
            ),
            application_rule_collections=dict(
                type='list',
                disposition='/',
                options=dict(
                    priority=dict(
                        type='number'
                    ),
                    action=dict(
                        type='dict',
                        options=dict(
                            type=dict(
                                type='str',
                                choices=['allow',
                                         'deny'],
                                comparison='insensitive'
                            )
                        )
                    ),
                    rules=dict(
                        type='list',
                        options=dict(
                            name=dict(
                                type='str'
                            ),
                            description=dict(
                                type='str'
                            ),
                            source_addresses=dict(
                                type='list'
                            ),
                            protocols=dict(
                                type='list',
                                options=dict(
                                    type=dict(
                                        type='str',
                                        disposition='protocolType',
                                        comparison='insensitive'
                                    ),
                                    port=dict(
                                        type='str'
                                    )
                                )
                            ),
                            target_fqdns=dict(
                                type='list'
                            ),
                            fqdn_tags=dict(
                                type='list'
                            )
                        )
                    ),
                    name=dict(
                        type='str'
                    )
                )
            ),
            nat_rule_collections=dict(
                type='list',
                disposition='/',
                options=dict(
                    priority=dict(
                        type='number'
                    ),
                    action=dict(
                        type='dict',
                        options=dict(
                            type=dict(
                                type='str',
                                choices=['snat',
                                         'dnat'],
                                comparison='insensitive'
                            )
                        )
                    ),
                    rules=dict(
                        type='list',
                        options=dict(
                            name=dict(
                                type='str'
                            ),
                            description=dict(
                                type='str'
                            ),
                            source_addresses=dict(
                                type='list'
                            ),
                            destination_addresses=dict(
                                type='list'
                            ),
                            destination_ports=dict(
                                type='list'
                            ),
                            protocols=dict(
                                type='list'
                            ),
                            translated_address=dict(
                                type='str'
                            ),
                            translated_port=dict(
                                type='str'
                            )
                        )
                    ),
                    name=dict(
                        type='str'
                    )
                )
            ),
            network_rule_collections=dict(
                type='list',
                disposition='/',
                options=dict(
                    priority=dict(
                        type='number'
                    ),
                    action=dict(
                        type='dict',
                        options=dict(
                            type=dict(
                                type='str',
                                choices=['allow',
                                         'deny']
                            ),
                            comparison='insensitive'
                        )
                    ),
                    rules=dict(
                        type='list',
                        options=dict(
                            name=dict(
                                type='str'
                            ),
                            description=dict(
                                type='str'
                            ),
                            protocols=dict(
                                type='list'
                            ),
                            source_addresses=dict(
                                type='list'
                            ),
                            destination_addresses=dict(
                                type='list'
                            ),
                            destination_ports=dict(
                                type='list'
                            )
                        )
                    ),
                    name=dict(
                        type='str'
                    )
                )
            ),
            ip_configurations=dict(
                type='list',
                disposition='/',
                options=dict(
                    subnet=dict(
                        type='raw',
                        disposition='subnet/id',
                        pattern=('/subscriptions/{{ subscription_id }}/resourceGroups'
                                 '/{{ resource_group }}/providers/Microsoft.Network'
                                 '/virtualNetworks/{{ virtual_network_name }}/subnets'
                                 '/{{ name }}')
                    ),
                    public_ip_address=dict(
                        type='raw',
                        disposition='public_ip_address/id',
                        pattern=('/subscriptions/{{ subscription_id }}/resourceGroups'
                                 '/{{ resource_group }}/providers/Microsoft.Network'
                                 '/publicIPAddresses/{{ name }}')
                    ),
                    name=dict(
                        type='str'
                    )
                )
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
                                                    supports_tags=True)

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
        elif self.to_do == Actions.Delete:
            self.results['changed'] = True
            if self.check_mode:
                return self.results
            self.delete_resource()
        else:
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

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


def main():
    AzureRMAzureFirewalls()


if __name__ == '__main__':
    main()
