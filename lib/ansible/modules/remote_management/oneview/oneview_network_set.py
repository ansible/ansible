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
module: oneview_network_set
short_description: Manage HPE OneView Network Set resources
description:
    - Provides an interface to manage Network Set resources. Can create, update, or delete.
version_added: "2.4"
requirements:
    - hpOneView >= 4.0.0
author:
    - Felipe Bulsoni (@fgbulsoni)
    - Thiago Miotto (@tmiotto)
    - Adriane Cardozo (@adriane-cardozo)
options:
    state:
      description:
        - Indicates the desired state for the Network Set resource.
            - C(present) will ensure data properties are compliant with OneView.
            - C(absent) will remove the resource from OneView, if it exists.
      default: present
      choices: ['present', 'absent']
    data:
      description:
        - List with the Network Set properties.
      required: true

extends_documentation_fragment:
    - oneview
    - oneview.validateetag
'''

EXAMPLES = '''
- name: Create a Network Set
  oneview_network_set:
    config: /etc/oneview/oneview_config.json
    state: present
    data:
      name: OneViewSDK Test Network Set
      networkUris:
        - Test Ethernet Network_1                                       # can be a name
        - /rest/ethernet-networks/e4360c9d-051d-4931-b2aa-7de846450dd8  # or a URI
  delegate_to: localhost

- name: Update the Network Set name to 'OneViewSDK Test Network Set - Renamed' and change the associated networks
  oneview_network_set:
    config: /etc/oneview/oneview_config.json
    state: present
    data:
      name: OneViewSDK Test Network Set
      newName: OneViewSDK Test Network Set - Renamed
      networkUris:
        - Test Ethernet Network_1
  delegate_to: localhost

- name: Delete the Network Set
  oneview_network_set:
    config: /etc/oneview/oneview_config.json
    state: absent
    data:
        name: OneViewSDK Test Network Set - Renamed
  delegate_to: localhost

- name: Update the Network set with two scopes
  oneview_network_set:
    config: /etc/oneview/oneview_config.json
    state: present
    data:
      name: OneViewSDK Test Network Set
      scopeUris:
        - /rest/scopes/01SC123456
        - /rest/scopes/02SC123456
  delegate_to: localhost
'''

RETURN = '''
network_set:
    description: Has the facts about the Network Set.
    returned: On state 'present', but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase, OneViewModuleResourceNotFound


class NetworkSetModule(OneViewModuleBase):
    MSG_CREATED = 'Network Set created successfully.'
    MSG_UPDATED = 'Network Set updated successfully.'
    MSG_DELETED = 'Network Set deleted successfully.'
    MSG_ALREADY_PRESENT = 'Network Set is already present.'
    MSG_ALREADY_ABSENT = 'Network Set is already absent.'
    MSG_ETHERNET_NETWORK_NOT_FOUND = 'Ethernet Network not found: '
    RESOURCE_FACT_NAME = 'network_set'

    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent']),
        data=dict(required=True, type='dict'))

    def __init__(self):
        super(NetworkSetModule, self).__init__(additional_arg_spec=self.argument_spec,
                                               validate_etag_support=True)
        self.resource_client = self.oneview_client.network_sets

    def execute_module(self):
        resource = self.get_by_name(self.data.get('name'))

        if self.state == 'present':
            return self._present(resource)
        elif self.state == 'absent':
            return self.resource_absent(resource)

    def _present(self, resource):
        scope_uris = self.data.pop('scopeUris', None)
        self._replace_network_name_by_uri(self.data)
        result = self.resource_present(resource, self.RESOURCE_FACT_NAME)
        if scope_uris is not None:
            result = self.resource_scopes_set(result, self.RESOURCE_FACT_NAME, scope_uris)
        return result

    def _get_ethernet_network_by_name(self, name):
        result = self.oneview_client.ethernet_networks.get_by('name', name)
        return result[0] if result else None

    def _get_network_uri(self, network_name_or_uri):
        if network_name_or_uri.startswith('/rest/ethernet-networks'):
            return network_name_or_uri
        else:
            enet_network = self._get_ethernet_network_by_name(network_name_or_uri)
            if enet_network:
                return enet_network['uri']
            else:
                raise OneViewModuleResourceNotFound(self.MSG_ETHERNET_NETWORK_NOT_FOUND + network_name_or_uri)

    def _replace_network_name_by_uri(self, data):
        if 'networkUris' in data:
            data['networkUris'] = [self._get_network_uri(x) for x in data['networkUris']]


def main():
    NetworkSetModule().run()


if __name__ == '__main__':
    main()
