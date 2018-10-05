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
module: oneview_fcoe_network
short_description: Manage OneView FCoE Network resources
description:
    - Provides an interface to manage FCoE Network resources. Can create, update, or delete.
version_added: "2.4"
requirements:
    - "python >= 2.7.9"
    - "hpOneView >= 4.0.0"
author: "Felipe Bulsoni (@fgbulsoni)"
options:
    state:
        description:
            - Indicates the desired state for the FCoE Network resource.
              C(present) will ensure data properties are compliant with OneView.
              C(absent) will remove the resource from OneView, if it exists.
        default: present
        choices: ['present', 'absent']
    data:
        description:
            - List with FCoE Network properties.
        required: true

extends_documentation_fragment:
    - oneview
    - oneview.validateetag
'''

EXAMPLES = '''
- name: Ensure that FCoE Network is present using the default configuration
  oneview_fcoe_network:
    config: '/etc/oneview/oneview_config.json'
    state: present
    data:
      name: Test FCoE Network
      vlanId: 201
  delegate_to: localhost

- name: Update the FCOE network scopes
  oneview_fcoe_network:
    config: '/etc/oneview/oneview_config.json'
    state: present
    data:
      name: New FCoE Network
      scopeUris:
        - '/rest/scopes/00SC123456'
        - '/rest/scopes/01SC123456'
  delegate_to: localhost

- name: Ensure that FCoE Network is absent
  oneview_fcoe_network:
    config: '/etc/oneview/oneview_config.json'
    state: absent
    data:
      name: New FCoE Network
  delegate_to: localhost
'''

RETURN = '''
fcoe_network:
    description: Has the facts about the OneView FCoE Networks.
    returned: On state 'present'. Can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class FcoeNetworkModule(OneViewModuleBase):
    MSG_CREATED = 'FCoE Network created successfully.'
    MSG_UPDATED = 'FCoE Network updated successfully.'
    MSG_DELETED = 'FCoE Network deleted successfully.'
    MSG_ALREADY_PRESENT = 'FCoE Network is already present.'
    MSG_ALREADY_ABSENT = 'FCoE Network is already absent.'
    RESOURCE_FACT_NAME = 'fcoe_network'

    def __init__(self):

        additional_arg_spec = dict(data=dict(required=True, type='dict'),
                                   state=dict(default='present',
                                              choices=['present', 'absent']))

        super(FcoeNetworkModule, self).__init__(additional_arg_spec=additional_arg_spec,
                                                validate_etag_support=True)

        self.resource_client = self.oneview_client.fcoe_networks

    def execute_module(self):
        resource = self.get_by_name(self.data.get('name'))

        if self.state == 'present':
            return self.__present(resource)
        elif self.state == 'absent':
            return self.resource_absent(resource)

    def __present(self, resource):
        scope_uris = self.data.pop('scopeUris', None)
        result = self.resource_present(resource, self.RESOURCE_FACT_NAME)
        if scope_uris is not None:
            result = self.resource_scopes_set(result, 'fcoe_network', scope_uris)
        return result


def main():
    FcoeNetworkModule().run()


if __name__ == '__main__':
    main()
