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
      id:
        description:
          - Resource ID.
      properties:
        description:
          - undefined
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
      properties:
        description:
          - undefined
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
                    Array of AzureFirewallNetworkRuleProtocols applicable to
                    this NAT rule.
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
      properties:
        description:
          - undefined
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
      properties:
        description:
          - undefined
        suboptions:
          subnet:
            description:
              - >-
                Reference of the subnet resource. This resource must be named
                'AzureFirewallSubnet'.
            suboptions:
              id:
                description:
                  - Resource ID.
          public_i_p_address:
            description:
              - >-
                Reference of the PublicIP resource. This field is a mandatory
                input if subnet is not null.
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
      - name: apprulecoll
        properties:
          priority: '110'
          action: Deny
          rules:
            - name: rule1
              description: Deny inbound rule
              protocols:
                - protocolType: Https
                  port: '443'
              targetFqdns:
                - www.test.com
              sourceAddresses:
                - 216.58.216.164
                - 10.0.0.0/24
    nat_rule_collections:
      - name: natrulecoll
        properties:
          priority: '112'
          action: Dnat
          rules:
            - name: DNAT-HTTPS-traffic
              description: D-NAT all outbound web traffic for inspection
              sourceAddresses:
                - '*'
              destinationAddresses:
                - 1.2.3.4
              destinationPorts:
                - '443'
              protocols:
                - TCP
              translatedAddress: 1.2.3.5
              translatedPort: '8443'
    network_rule_collections:
      - name: netrulecoll
        properties:
          priority: '112'
          action: Deny
          rules:
            - name: L4-traffic
              description: Block traffic based on source IPs and ports
              sourceAddresses:
                - 192.168.1.1-192.168.1.12
                - 10.1.4.12-10.1.4.255
              destinationPorts:
                - 443-444
                - '8443'
              destinationAddresses:
                - '*'
              protocols:
                - TCP
    ip_configurations:
      - name: azureFirewallIpConfiguration
        properties:
          subnet:
            id: >-
              /subscriptions/{{ subscription_id }}/resourceGroups/{{
              resource_group }}/providers/Microsoft.Network/virtualNetworks/{{
              virtual_network_name }}/subnets/{{ subnet_name }}
          publicIPAddress:
            id: >-
              /subscriptions/{{ subscription_id }}/resourceGroups/{{
              resource_group }}/providers/Microsoft.Network/publicIPAddresses/{{
              public_ipaddress_name }}
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
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
try:
    from msrestazure.azure_exceptions import CloudError
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
                disposition='resourceGroupName',
                required=True
            ),
            name=dict(
                type='str',
                comparison='',
                updatable=False,
                disposition='azureFirewallName',
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
            application_rule_collections=dict(
                type='list',
                comparison='',
                updatable=False,
                disposition='/properties/applicationRuleCollections',
                options=dict(
                    id=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    properties=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
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
                                        disposition='*'
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
                                        disposition='sourceAddresses'
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
                                        disposition='targetFqdns'
                                    ),
                                    fqdn_tags=dict(
                                        type='list',
                                        comparison='',
                                        updatable=False,
                                        disposition='fqdnTags'
                                    )
                                )
                            ),
                            provisioning_state=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='provisioningState'
                            )
                        )
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
                disposition='/properties/natRuleCollections',
                options=dict(
                    id=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    properties=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
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
                                        disposition='*'
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
                                        disposition='sourceAddresses'
                                    ),
                                    destination_addresses=dict(
                                        type='list',
                                        comparison='',
                                        updatable=False,
                                        disposition='destinationAddresses'
                                    ),
                                    destination_ports=dict(
                                        type='list',
                                        comparison='',
                                        updatable=False,
                                        disposition='destinationPorts'
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
                                        disposition='translatedAddress'
                                    ),
                                    translated_port=dict(
                                        type='str',
                                        comparison='',
                                        updatable=False,
                                        disposition='translatedPort'
                                    )
                                )
                            ),
                            provisioning_state=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='provisioningState'
                            )
                        )
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
                disposition='/properties/networkRuleCollections',
                options=dict(
                    id=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    properties=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
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
                                        disposition='*'
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
                                        disposition='sourceAddresses'
                                    ),
                                    destination_addresses=dict(
                                        type='list',
                                        comparison='',
                                        updatable=False,
                                        disposition='destinationAddresses'
                                    ),
                                    destination_ports=dict(
                                        type='list',
                                        comparison='',
                                        updatable=False,
                                        disposition='destinationPorts'
                                    )
                                )
                            ),
                            provisioning_state=dict(
                                type='str',
                                comparison='',
                                updatable=False,
                                disposition='provisioningState'
                            )
                        )
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
                disposition='/properties/ipConfigurations',
                options=dict(
                    id=dict(
                        type='str',
                        comparison='',
                        updatable=False,
                        disposition='*'
                    ),
                    properties=dict(
                        type='dict',
                        comparison='',
                        updatable=False,
                        disposition='*',
                        options=dict(
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
                                        disposition='*'
                                    )
                                )
                            ),
                            public_i_p_address=dict(
                                type='dict',
                                comparison='',
                                updatable=False,
                                disposition='publicIPAddress',
                                options=dict(
                                    id=dict(
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
                                disposition='provisioningState'
                            )
                        )
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
                disposition='/properties/provisioningState'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200, 201, 202]
        self.to_do = Actions.NoAction

        self.body = {}
        self.query_parameters = {}
        self.query_parameters['api-version'] = '2018-11-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

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

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if 'location' not in self.body:
            self.body['location'] = resource_group.location

        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.Network' +
                    '/azureFirewalls' +
                    '/{{ azure_firewall_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ azure_firewall_name }}', self.name)

        old_response = self.get_resource()

        if not old_response:
            self.log("AzureFirewall instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('AzureFirewall instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log('Need to check if AzureFirewall instance has to be deleted or may be updated')

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the AzureFirewall instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_resource()

            # if not old_response:
            self.results['changed'] = True
            self.results['response'] = response
            # else:
            #     self.results['changed'] = old_response.__ne__(response)
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('AzureFirewall instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_resource()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_resource():
                time.sleep(20)
        else:
            self.log('AzureFirewall instance unchanged')
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["name"] = response["name"]
            self.results["type"] = response["type"]
            self.results["etag"] = response["etag"]

        return self.results

    def create_update_resource(self):
        # self.log('Creating / Updating the AzureFirewall instance {0}'.format(self.))

        try:
            if self.to_do == Actions.Create:
                response = self.mgmt_client.query(self.url,
                                                  'PUT',
                                                  self.query_parameters,
                                                  self.header_parameters,
                                                  self.body,
                                                  self.status_code,
                                                  600,
                                                  30)
            else:
                response = self.mgmt_client.query(self.url,
                                                  'PUT',
                                                  self.query_parameters,
                                                  self.header_parameters,
                                                  self.body,
                                                  self.status_code,
                                                  600,
                                                  30)
        except CloudError as exc:
            self.log('Error attempting to create the AzureFirewall instance.')
            self.fail('Error creating the AzureFirewall instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except Exception:
            response = {'text': response.text}
            pass

        return response

    def delete_resource(self):
        # self.log('Deleting the AzureFirewall instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(self.url,
                                              'DELETE',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
        except CloudError as e:
            self.log('Error attempting to delete the AzureFirewall instance.')
            self.fail('Error deleting the AzureFirewall instance: {0}'.format(str(e)))

        return True

    def get_resource(self):
        # self.log('Checking if the AzureFirewall instance {0} is present'.format(self.))
        found = False
        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            found = True
            self.log("Response : {0}".format(response))
            # self.log("AzureFirewall instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the AzureFirewall instance.')
        if found is True:
            return response

        return False

    def inflate_parameters(self, spec, body, level):
        for name in spec.keys():
            disposition = spec[name].get('disposition', '*')
            # do nothing if disposition is *
            if disposition == '*':
                continue
            if level == 0 and not disposition.startswith('/'):
                continue
            if disposition == '/':
                disposition = '/*'
            # find parameter
            param = body.get(name)
            if not param:
                continue
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


def main():
    AzureRMAzureFirewalls()


if __name__ == '__main__':
    main()
