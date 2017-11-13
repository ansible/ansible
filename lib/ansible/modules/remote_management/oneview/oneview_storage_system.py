#!/usr/bin/python

# Copyright: (c) 2016-2017, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: oneview_storage_system
short_description: Manage OneView Storage System resources
description:
    - Provides an interface to manage Storage System resources. Can add, update and remove.
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
            - Indicates the desired state for the Storage System resource.
                - C(present) will ensure data properties are compliant with OneView.
                - C(absent) will remove the resource from OneView, if it exists.
        choices: ['present', 'absent']
        default: present
    data:
        description:
            - List with Storage System properties and its associated states.
        required: true
extends_documentation_fragment:
    - oneview
    - oneview.validateetag
'''

EXAMPLES = '''
- name: Add a Storage System with one managed pool (before API500)
  oneview_storage_system:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 300
    state: present
    data:
        credentials:
            ip_hostname: 172.18.11.12
            username: username
            password: password
        managedDomain: TestDomain
        managedPools:
          - domain: TestDomain
            type: StoragePoolV2
            name: CPG_FC-AO
            deviceType: FC

  no_log: true
  delegate_to: localhost

- name: Add a StoreServ Storage System with one managed pool (API500 onwards)
  oneview_storage_system:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    state: present
    data:
      credentials:
          username: username
          password: password
      hostname: 172.18.11.12
      family: StoreServ
      deviceSpecificAttributes:
          managedDomain: TestDomain
          managedPools:
              - domain: TestDomain
                name: CPG_FC-AO
                deviceType: FC

  no_log: true
  delegate_to: localhost

- name: Remove the storage system by its IP (before API500)
  oneview_storage_system:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 300
    state: absent
    data:
        credentials:
            ip_hostname: 172.18.11.12

  no_log: true
  delegate_to: localhost

- name: Remove the storage system by its IP (API500 onwards)
  oneview_storage_system:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    state: absent
    data:
        credentials:
            hostname: 172.18.11.12

  no_log: true
  delegate_to: localhost
'''

RETURN = '''
storage_system:
    description: Has the OneView facts about the Storage System.
    returned: On state 'present'. Can be null.
    type: dict
'''

from ansible.module_utils.six.moves import filter
from ansible.module_utils.oneview import OneViewModuleBase, OneViewModuleValueError


class StorageSystemModule(OneViewModuleBase):
    MSG_ADDED = 'Storage System added successfully.'
    MSG_UPDATED = 'Storage System updated successfully.'
    MSG_ALREADY_PRESENT = 'Storage System is already present.'
    MSG_DELETED = 'Storage System deleted successfully.'
    MSG_ALREADY_ABSENT = 'Storage System is already absent.'
    MSG_MANDATORY_FIELDS_MISSING = "At least one mandatory field must be provided: name or credentials.hostname" \
                                   "(credentials.ip_hostname if API version lower than 500 )."
    MSG_CREDENTIALS_MANDATORY = "The attribute 'credentials' is mandatory for Storage System creation."

    argument_spec = dict(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        data=dict(type='dict', required=True)
    )

    def __init__(self):
        super(StorageSystemModule, self).__init__(additional_arg_spec=self.argument_spec, validate_etag_support=True)

        self.resource_client = self.oneview_client.storage_systems

    def execute_module(self):
        if self.oneview_client.api_version < 500:
            resource = self.__get_resource_hostname('ip_hostname', 'newIp_hostname')
        else:
            resource = self.__get_resource_hostname('hostname', 'newHostname')

        if self.state == 'present':
            return self.__present(resource)
        elif self.state == 'absent':
            return self.resource_absent(resource, 'remove')

    def __present(self, resource):
        changed = False
        msg = ''

        if not resource:
            if 'credentials' not in self.data:
                raise OneViewModuleValueError(self.MSG_CREDENTIALS_MANDATORY)
            if self.oneview_client.api_version < 500:
                resource = self.oneview_client.storage_systems.add(self.data['credentials'])
            else:
                options = self.data['credentials'].copy()
                options['family'] = self.data.get('family', None)
                options['hostname'] = self.data.get('hostname', None)
                resource = self.oneview_client.storage_systems.add(options)

            changed = True
            msg = self.MSG_ADDED

        merged_data = resource.copy()
        merged_data.update(self.data)

        # remove password, it cannot be used in comparison
        if 'credentials' in merged_data and 'password' in merged_data['credentials']:
            del merged_data['credentials']['password']

        # sets the uuid to all the storage pools that are in the 'managedPools' list
        if self.oneview_client.api_version >= 500:
            for pool in merged_data['deviceSpecificAttributes'].get('managedPools', []):
                discovered_pools = resource.get('deviceSpecificAttributes', {}).get('discoveredPools', [])
                pools_by_name = list(filter(lambda item: item.get('name') == pool.get('name') and item.get('domain') == pool.get('domain'), discovered_pools))
                if pools_by_name:
                    'uuid' in pool or pool.setdefault('uuid', pools_by_name[0].get('uuid'))

        if not self.compare(resource, merged_data):
            # update the resource
            resource = self.oneview_client.storage_systems.update(merged_data)
            if not changed:
                changed = True
                msg = self.MSG_UPDATED
        else:
            msg = self.MSG_ALREADY_PRESENT

        return dict(changed=changed,
                    msg=msg,
                    ansible_facts=dict(storage_system=resource))

    def __get_resource_hostname(self, hostname_key, new_hostname_key):
        hostname = self.data.get(hostname_key, None)
        if 'credentials' in self.data and hostname is None:
            hostname = self.data['credentials'].get(hostname_key, None)
        if hostname:
            get_method = getattr(self.oneview_client.storage_systems, "get_by_{0}".format(hostname_key))
            resource = get_method(hostname)
            if self.data['credentials'].get(new_hostname_key):
                self.data['credentials'][hostname_key] = self.data['credentials'].pop(new_hostname_key)
            elif self.data.get(new_hostname_key):
                self.data[hostname_key] = self.data.pop(new_hostname_key)
            return resource
        elif self.data.get('name'):
            return self.oneview_client.storage_systems.get_by_name(self.data['name'])
        else:
            raise OneViewModuleValueError(self.MSG_MANDATORY_FIELDS_MISSING)


def main():
    StorageSystemModule().run()


if __name__ == '__main__':
    main()
