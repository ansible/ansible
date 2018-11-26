#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
---
module: azure_rm_localnetworkgateway

version_added: "2.8"

short_description: Manage Azure local network gateways.

description:
    - Create, update or delete a local network gateway.

options:
    resource_group:
        description:
            - Name of a resource group where local network Gateway exists or will be created.
        required: true
    name:
        description:
            - Name of local network Gateway.
        required: true
    state:
        description:
            - Assert the state of the local Gateway. Use 'present' to create or update local network gateway and
              'absent' to delete local network gateway.
        default: present
        choices:
            - absent
            - present
        required: false
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        required: false
    local_address_prefixes:
        description:
            - List of local network site address space(on-premise).
    gateway_ip_address:
        description:
            - IP address of local network gateway.
    bgp_settings:
        description:
            - Local network gateway's BGP speaker settings.
        suboptions:
            asn:
                description:
                    - The BGP speaker's ASN.
            bgp_peering_address:
                description:
                    - The BGP peering address and BGP identifier of this BGP speaker.
            peer_weight:
                description:
                    - The weight added to routes learned from this BGP speaker.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Madhura Naniwadekar (@Madhura-CSI)"
'''

EXAMPLES = '''
    - name: Create local network gateway, with BGP settings
      azure_rm_localnetworkgateway:
        resource_group: testrg
        name: testlocalgw
        local_address_prefixes:
          - 10.1.0.0/16
          - 172.100.0.0/16
        gateway_ip_address: 1.2.3.4
        tags:
          common: a
      register: local_network_gateway

    - name: Delete local network gateway
      azure_rm_localnetworkgateway:
        resource_group: testrg
        name: testlocalgw
        state: absent
'''

RETURN = '''
id:
    description: The ID of local network gateway.
    returned: always
    type: str
    sample: /subscriptions/xxxx/resourceGroups/xxx/providers/Microsoft.Network/localNetworkGateways/xx
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, CIDR_PATTERN


bgp_spec = dict(
    asn=dict(type='int'),
    bgp_peering_address=dict(),
    peer_weight=dict(type='int', default=0)
)


class AzureRMLocalNetworkGateway(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            local_address_prefixes=dict(type='list', default=[]),
            gateway_ip_address=dict(),
            bgp_settings=dict(type='dict', options=bgp_spec),
        )

        required_if = [
            ('state', 'present', ['name', 'gateway_ip_address']),
            ('state', 'absent', ['name'])
        ]

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.gateway_ip_address = None
        self.local_address_prefixes = None
        self.bgp_settings = None

        self.results = dict(changed=False)

        super(AzureRMLocalNetworkGateway, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                         supports_check_mode=True,
                                                         required_if=required_if,
                                                         supports_tags=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])
        changed = False
        results = dict()

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        results = self.get_lgw()
        if not results:
            changed = True if self.state == 'present' else False
        else:
            if self.state == 'present':
                update_tags, results['tags'] = self.update_tags(results.get('tags', None))
                if update_tags:
                    changed = True
                if results['gateway_ip_address'] != self.gateway_ip_address:
                    changed = True
                bgp_settings = self.bgp_settings if self.bgp_settings else None
                if bgp_settings != results.get('bgp_settings', None):
                    changed = True
                if sorted(results['local_network_address_space']['address_prefixes']) != sorted(self.local_address_prefixes):
                    changed = True
            else:
                self.log("CHANGED: local network gateway exists but requested state is 'absent'")
                changed = True

        self.results['changed'] = changed
        self.results['id'] = None
        if self.check_mode:
            self.results['changed'] = True
            return self.results

        if changed:
            if self.state == 'present':
                lgw_bgp_settings = self.network_models.BgpSettings(
                    asn=self.bgp_settings.get('asn'),
                    bgp_peering_address=self.bgp_settings.get('bgp_peering_address'),
                    peer_weight=self.bgp_settings.get('peer_weight')
                ) if self.bgp_settings else None
                lgw = self.network_models.LocalNetworkGateway(
                    location=self.location,
                    gateway_ip_address=self.gateway_ip_address,
                    local_network_address_space=self.network_models.AddressSpace(
                        address_prefixes=self.local_address_prefixes
                    ) if self.local_address_prefixes else None,
                    bgp_settings=lgw_bgp_settings
                )
                if self.tags:
                    lgw.tags = self.tags
                lgw = self.create_or_update_lgw(lgw)
                self.results['id'] = lgw.get('id', None)
            else:
                self.delete_lgw()
        return self.results

    def create_or_update_lgw(self, lgw):
        try:
            poller = self.network_client.local_network_gateways.create_or_update(self.resource_group, self.name, lgw)
            new_lgw = self.get_poller_result(poller)
            return new_lgw.as_dict()
        except CloudError as exc:
            self.fail("Error creating or updating local network gateway {0} - {1}".format(self.name, str(exc)))

    def delete_lgw(self):
        try:
            poller = self.network_client.local_network_gateways.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
        except CloudError as exc:
            self.fail("Error deleting local network gateway {0} - {1}".format(self.name, str(exc)))
        return True

    def get_lgw(self):
        lgw = None
        try:
            lgw = self.network_client.local_network_gateways.get(resource_group_name=self.resource_group,
                                                                 local_network_gateway_name=self.name)
        except CloudError as exc:
            if exc.status_code == 404:
                self.log('Local network gateway {0} does not exist.'.format(self.name))
            else:
                self.fail("Error getting local network gateway {0} - {1}".format(self.name, str(exc)))
        if lgw:
            return lgw.as_dict()
        return False


def main():
    AzureRMLocalNetworkGateway()


if __name__ == '__main__':
    main()
