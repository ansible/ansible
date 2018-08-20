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

version_added: "2.7"

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
          - 10.108.0.0/24
          - 10.109.1.0/29
          - 10.106.0.0/27
        gateway_ip_address: 13.71.1.149
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
state:
    description: The current state of the local network gateway.
    returned: always
    type: dict
    sample: {
        "bgp_settings": null,
        "etag": "W/\"a126580a-5221-1222-ac4d-3c12bc1212111\"",
        "gateway_ip_address": "13.71.1.148",
        "id": "/subscriptions/xyz/resourceGroups/testrg/providers/Microsoft.Network/localNetworkGateways/testlocalgw",
        "local_network_address_space": [
            "10.108.0.0/24",
            "10.109.1.0/29",
            "10.106.0.0/27"
        ],
        "location": "centralindia",
        "name": "testlocalgw",
        "provisioning_state": "Succeeded",
        "tags": {
            "common": "a"
        }
    }
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, CIDR_PATTERN


bgp_spec = dict(
    asn=dict(type='int', required=True),
    bgp_peering_address=dict(),
    peer_weight=dict(type='int', default=0)
)


def bgp_settings_to_dict(bgp_settings):
    return dict(
        asn=long(bgp_settings.get('asn')),
        bgp_peering_address=bgp_settings.get('bgp_peering_address'),
        peer_weight=bgp_settings.get('peer_weight')
    )


def lgw_to_dict(lgw):
    results = dict(
        id=lgw.id,
        name=lgw.name,
        location=lgw.location,
        gateway_ip_address=lgw.gateway_ip_address,
        tags=lgw.tags,
        provisioning_state=lgw.provisioning_state,
        local_network_address_space=lgw.local_network_address_space.address_prefixes,
        bgp_settings=dict(
            asn=long(lgw.bgp_settings.asn),
            bgp_peering_address=lgw.bgp_settings.bgp_peering_address,
            peer_weight=lgw.bgp_settings.peer_weight
        ) if lgw.bgp_settings else None,
        etag=lgw.etag
    )
    return results


class AzureRMLocalNetworkGateway(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            local_address_prefixes=dict(type='list'),
            gateway_ip_address=dict(required=True),
            bgp_settings=dict(type='dict', options=bgp_spec),
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.gateway_ip_address = None
        self.local_address_prefixes = None
        self.bgp_settings = None

        self.results = dict(
            changed=False,
            state=dict()
        )

        super(AzureRMLocalNetworkGateway, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                         supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        changed = False
        results = dict()

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        try:
            lgw = self.network_client.local_network_gateways.get(self.resource_group, self.name)
            self.check_provisioning_state(lgw, self.state)
            results = lgw_to_dict(lgw)
            if self.state == 'present':
                update_tags, results['tags'] = self.update_tags(results['tags'])
                if update_tags:
                    changed = True
                if results['gateway_ip_address'] != self.gateway_ip_address:
                    changed = True
                self.bgp_settings = bgp_settings_to_dict(self.bgp_settings) if self.bgp_settings else None
                if self.bgp_settings != results['bgp_settings']:
                    changed = True
                if sorted(results['local_network_address_space']) != sorted(self.local_address_prefixes):
                    changed = True
            elif self.state == 'absent':
                self.log("CHANGED: local network gateway exists but requested state is 'absent'")
                changed = True
        except CloudError:
            if self.state == 'present':
                self.log("CHANGED: VPN Gateway {0} does not exist but requested state is 'present'".format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if self.check_mode:
            return self.results
        if changed:
            if self.state == 'present':
                if not self.gateway_ip_address:
                    self.fail('Parameter error: gateway_ip_address is required when creating a local network gateway')
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
                self.results['state'] = self.create_or_update_lgw(lgw)
            else:
                self.results['state'] = self.delete_lgw()
        return self.results

    def create_or_update_lgw(self, lgw):
        try:
            poller = self.network_client.local_network_gateways.create_or_update(self.resource_group, self.name, lgw)
            new_lgw = self.get_poller_result(poller)
            return lgw_to_dict(new_lgw)
        except Exception as exc:
            self.fail("Error creating or updating local network gateway {0} - {1}".format(self.name, str(exc)))

    def delete_lgw(self):
        try:
            poller = self.network_client.local_network_gateways.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting local network gateway {0} - {1}".format(self.name, str(exc)))
        return True


def main():
    AzureRMLocalNetworkGateway()


if __name__ == '__main__':
    main()
