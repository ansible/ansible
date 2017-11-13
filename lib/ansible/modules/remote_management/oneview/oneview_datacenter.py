#!/usr/bin/python
# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: oneview_datacenter
short_description: Manage OneView Datacenter resources
description:
    - "Provides an interface to manage Datacenter resources. Can add, update, and remove."
version_added: "2.5"
requirements:
    - "hpOneView >= 3.1.0"
author:
    - Alex Monteiro (@aalexmonteiro)
    - Madhav Bharadwaj (@madhav-bharadwaj)
    - Priyanka Sood (@soodpr)
    - Ricardo Galeno (@ricardogpsf)
options:
    state:
        description:
            - Indicates the desired state for the Datacenter resource.
              C(absent) will remove the resource from OneView, if it exists.
              C(present) will ensure the datacenter resource exists and its properties are compliant with HPE OneView.
        choices: ['present', 'absent']
        default: present
    data:
        description:
            - List with Datacenter properties and its associated states.
        required: true

extends_documentation_fragment:
    - oneview
    - oneview.validateetag
'''

EXAMPLES = '''
- name: Add a Datacenter
  oneview_datacenter:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    state: present
    data:
        contents:
            # You can choose either resourceName or resourceUri to inform the Rack
            - resourceName: '{{ datacenter_content_rack_name }}' # option 1
              resourceUri: ''                                    # option 2
              x: 1000
              y: 1000
        depth: 6000
        name: "MyDatacenter"
        width: 5000
  no_log: true
  delegate_to: localhost

- name: Update the Datacenter with specified properties (no racks)
  oneview_datacenter:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    state: present
    data:
        contents: ~
        coolingCapacity: '5'
        coolingMultiplier: '1.5'
        costPerKilowattHour: '0.10'
        currency: USD
        defaultPowerLineVoltage: '220'
        deratingPercentage: '20.0'
        depth: 5000
        deratingType: NaJp
        name: "MyDatacenter"
        width: 4000
  no_log: true
  delegate_to: localhost

- name: Rename the Datacenter
  oneview_datacenter:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    state: present
    data:
        name: "MyDatacenter"
        newName: "My Datacenter"
  no_log: true
  delegate_to: localhost

- name: Remove the Datacenter
  oneview_datacenter:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    state: absent
    data:
        name: 'My Datacenter'
  no_log: true
  delegate_to: localhost
'''

RETURN = '''
datacenter:
    description: Has the OneView facts about the Datacenter.
    returned: On state 'present'. Can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase, OneViewModuleResourceNotFound


class DatacenterModule(OneViewModuleBase):
    MSG_CREATED = 'Datacenter added successfully.'
    MSG_UPDATED = 'Datacenter updated successfully.'
    MSG_ALREADY_PRESENT = 'Datacenter is already present.'
    MSG_DELETED = 'Datacenter removed successfully.'
    MSG_ALREADY_ABSENT = 'Datacenter is already absent.'
    MSG_RACK_NOT_FOUND = 'Rack was not found.'
    RESOURCE_FACT_NAME = 'datacenter'

    argument_spec = dict(
        state=dict(type='str', default='present', choices=['absent', 'present',]),
        data=dict(type='dict', required=True)
    )

    def __init__(self):
        super(DatacenterModule, self).__init__(additional_arg_spec=self.argument_spec,
                                               validate_etag_support=True)
        self.resource_client = self.oneview_client.datacenters

    def execute_module(self):

        resource = self.get_by_name(self.data['name'])

        if self.state == 'present':
            self.__replace_name_by_uris(self.data)
            return self.resource_present(resource, self.RESOURCE_FACT_NAME, 'add')
        elif self.state == 'absent':
            return self.resource_absent(resource, 'remove')

    def __replace_name_by_uris(self, resource):
        contents = resource.get('contents')

        if contents:
            for content in contents:
                resource_name = content.pop('resourceName', None)
                if resource_name:
                    content['resourceUri'] = self.__get_rack_by_name(resource_name)['uri']

    def __get_rack_by_name(self, name):
        racks = self.oneview_client.racks.get_by('name', name)
        if racks:
            return racks[0]
        else:
            raise OneViewModuleResourceNotFound(self.MSG_RACK_NOT_FOUND)


def main():
    DatacenterModule().run()


if __name__ == '__main__':
    main()
