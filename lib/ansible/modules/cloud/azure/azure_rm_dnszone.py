#!/usr/bin/python
#
# Copyright (c) 2017 Obezimnaka Boms, <t-ozboms@microsoft.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_dnszone

version_added: "2.4"

short_description: Manage Azure DNS zones.

description:
    - Creates and deletes Azure DNS zones.

options:
    resource_group:
        description:
            - name of resource group.
        required: true
    name:
        description:
            - name of the DNS Zone.
        required: true
    state:
        description:
            - Assert the state of the zone. Use C(present) to create or update and
              C(absent) to delete.
        default: present
        choices:
            - absent
            - present
    type:
        description:
            - The type of this DNS zone (public or private)
        choices:
            - public
            - private
        version_added: 2.8
    registration_virtual_networks:
        description:
            - A list of references to virtual networks that register hostnames in this DNS zone.
            - This is a only when I(type) is C(private).
            - Each element can be the name or resource id, or a dict contains C(name), C(resource_group) information of the virtual network.
        version_added: 2.8
        type: list
    resolution_virtual_networks:
        description:
            - A list of references to virtual networks that resolve records in this DNS zone.
            - This is a only when I(type) is C(private).
            - Each element can be the name or resource id, or a dict contains C(name), C(resource_group) information of the virtual network.
        version_added: 2.8
        type: list

extends_documentation_fragment:
    - azure
    - azure_tags

author: "Obezimnaka Boms (@ozboms)"
'''

EXAMPLES = '''

- name: Create a DNS zone
  azure_rm_dnszone:
    resource_group: myResourceGroup
    name: example.com

- name: Delete a DNS zone
  azure_rm_dnszone:
    resource_group: myResourceGroup
    name: example.com
    state: absent

'''

RETURN = '''
state:
    description: Current state of the zone.
    returned: always
    type: dict
    sample: {
        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup",
        "location": "global",
        "name": "Testing",
        "name_servers": [
            "ns1-07.azure-dns.com.",
            "ns2-07.azure-dns.net.",
            "ns3-07.azure-dns.org.",
            "ns4-07.azure-dns.info."
        ],
        "number_of_record_sets": 2,
        "type": "private",
        "resolution_virtual_networks": ["/subscriptions/XXXX/resourceGroup/myResourceGroup/providers/Microsoft.Network/virtualNetworks/foo"]
    }

'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils._text import to_native

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDNSZone(AzureRMModuleBase):

    def __init__(self):

        # define user inputs from playbook
        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
            type=dict(type='str', choices=['private', 'public']),
            registration_virtual_networks=dict(type='list', elements='raw'),
            resolution_virtual_networks=dict(type='list', elements='raw')
        )

        # store the results of the module operation
        self.results = dict(
            changed=False,
            state=dict()
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.tags = None
        self.type = None
        self.registration_virtual_networks = None
        self.resolution_virtual_networks = None

        super(AzureRMDNSZone, self).__init__(self.module_arg_spec,
                                             supports_check_mode=True,
                                             supports_tags=True)

    def exec_module(self, **kwargs):

        # create a new zone variable in case the 'try' doesn't find a zone
        zone = None
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.registration_virtual_networks = self.preprocess_vn_list(self.registration_virtual_networks)
        self.resolution_virtual_networks = self.preprocess_vn_list(self.resolution_virtual_networks)

        self.results['check_mode'] = self.check_mode

        # retrieve resource group to make sure it exists
        self.get_resource_group(self.resource_group)

        changed = False
        results = dict()

        try:
            self.log('Fetching DNS zone {0}'.format(self.name))
            zone = self.dns_client.zones.get(self.resource_group, self.name)

            # serialize object into a dictionary
            results = zone_to_dict(zone)

            # don't change anything if creating an existing zone, but change if deleting it
            if self.state == 'present':
                changed = False

                update_tags, results['tags'] = self.update_tags(results['tags'])
                if update_tags:
                    changed = True
                if self.type and results['type'] != self.type:
                    changed = True
                    results['type'] = self.type
                if self.resolution_virtual_networks:
                    if set(self.resolution_virtual_networks) != set(results['resolution_virtual_networks'] or []):
                        changed = True
                        results['resolution_virtual_networks'] = self.resolution_virtual_networks
                else:
                    # this property should not be changed
                    self.resolution_virtual_networks = results['resolution_virtual_networks']
                if self.registration_virtual_networks:
                    if set(self.registration_virtual_networks) != set(results['registration_virtual_networks'] or []):
                        changed = True
                        results['registration_virtual_networks'] = self.registration_virtual_networks
                else:
                    self.registration_virtual_networks = results['registration_virtual_networks']
            elif self.state == 'absent':
                changed = True

        except CloudError:
            # the zone does not exist so create it
            if self.state == 'present':
                changed = True
            else:
                # you can't delete what is not there
                changed = False

        self.results['changed'] = changed
        self.results['state'] = results

        # return the results if your only gathering information
        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                zone = self.dns_models.Zone(zone_type=str.capitalize(self.type) if self.type else None,
                                            tags=self.tags,
                                            location='global')
                if self.resolution_virtual_networks:
                    zone.resolution_virtual_networks = self.construct_subresource_list(self.resolution_virtual_networks)
                if self.registration_virtual_networks:
                    zone.registration_virtual_networks = self.construct_subresource_list(self.registration_virtual_networks)
                self.results['state'] = self.create_or_update_zone(zone)
            elif self.state == 'absent':
                # delete zone
                self.delete_zone()
                # the delete does not actually return anything. if no exception, then we'll assume
                # it worked.
                self.results['state']['status'] = 'Deleted'

        return self.results

    def create_or_update_zone(self, zone):
        try:
            # create or update the new Zone object we created
            new_zone = self.dns_client.zones.create_or_update(self.resource_group, self.name, zone)
        except Exception as exc:
            self.fail("Error creating or updating zone {0} - {1}".format(self.name, exc.message or str(exc)))
        return zone_to_dict(new_zone)

    def delete_zone(self):
        try:
            # delete the Zone
            poller = self.dns_client.zones.delete(self.resource_group, self.name)
            result = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting zone {0} - {1}".format(self.name, exc.message or str(exc)))
        return result

    def preprocess_vn_list(self, vn_list):
        return [self.parse_vn_id(x) for x in vn_list] if vn_list else None

    def parse_vn_id(self, vn):
        vn_dict = self.parse_resource_to_dict(vn) if not isinstance(vn, dict) else vn
        return format_resource_id(val=vn_dict['name'],
                                  subscription_id=vn_dict.get('subscription') or self.subscription_id,
                                  namespace='Microsoft.Network',
                                  types='virtualNetworks',
                                  resource_group=vn_dict.get('resource_group') or self.resource_group)

    def construct_subresource_list(self, raw):
        return [self.dns_models.SubResource(id=x) for x in raw] if raw else None


def zone_to_dict(zone):
    # turn Zone object into a dictionary (serialization)
    result = dict(
        id=zone.id,
        name=zone.name,
        number_of_record_sets=zone.number_of_record_sets,
        name_servers=zone.name_servers,
        tags=zone.tags,
        type=zone.zone_type.value.lower(),
        registration_virtual_networks=[to_native(x.id) for x in zone.registration_virtual_networks] if zone.registration_virtual_networks else None,
        resolution_virtual_networks=[to_native(x.id) for x in zone.resolution_virtual_networks] if zone.resolution_virtual_networks else None
    )
    return result


def main():
    AzureRMDNSZone()


if __name__ == '__main__':
    main()
