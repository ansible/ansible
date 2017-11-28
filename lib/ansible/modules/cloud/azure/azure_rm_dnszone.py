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
            - Assert the state of the zone. Use 'present' to create or update and
              'absent' to delete.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author: "Obezimnaka Boms (@ozboms)"
'''

EXAMPLES = '''

- name: Create a DNS zone
  azure_rm_dnszone:
    resource_group: Testing
    name: example.com
    state: present

- name: Delete a DNS zone
  azure_rm_dnszone:
    resource_group: Testing
    name: example.com
    state: absent

'''

RETURN = '''
state:
    description: Current state of the zone.
    returned: always
    type: dict
    sample: {
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing",
        "location": "global",
        "name": "Testing",
        "name_servers": [
            "ns1-07.azure-dns.com.",
            "ns2-07.azure-dns.net.",
            "ns3-07.azure-dns.org.",
            "ns4-07.azure-dns.info."
        ],
        "number_of_record_sets": 2
    }

'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.dns.models import Zone
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDNSZone(AzureRMModuleBase):

    def __init__(self):

        # define user inputs from playbook
        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present', type='str')
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

        super(AzureRMDNSZone, self).__init__(self.module_arg_spec,
                                             supports_check_mode=True,
                                             supports_tags=True)

    def exec_module(self, **kwargs):

        # create a new zone variable in case the 'try' doesn't find a zone
        zone = None
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

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
                if not zone:
                    # create new zone
                    self.log('Creating zone {0}'.format(self.name))
                    zone = Zone(location='global', tags=self.tags)
                else:
                    # update zone
                    zone = Zone(
                        location='global',
                        tags=results['tags']
                    )
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
            self.fail("Error creating or updating zone {0} - {1}".format(self.name, str(exc)))
        return zone_to_dict(new_zone)

    def delete_zone(self):
        try:
            # delete the Zone
            poller = self.dns_client.zones.delete(self.resource_group, self.name)
            result = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting zone {0} - {1}".format(self.name, str(exc)))
        return result


def zone_to_dict(zone):
    # turn Zone object into a dictionary (serialization)
    result = dict(
        id=zone.id,
        name=zone.name,
        number_of_record_sets=zone.number_of_record_sets,
        name_servers=zone.name_servers,
        tags=zone.tags
    )
    return result


def main():
    AzureRMDNSZone()

if __name__ == '__main__':
    main()
