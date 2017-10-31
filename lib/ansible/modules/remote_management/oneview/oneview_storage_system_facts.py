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
module: oneview_storage_system_facts
short_description: Retrieve facts about the OneView Storage Systems
description:
    - Retrieve facts about the Storage Systems from OneView.
version_added: "2.5"
requirements:
    - hpOneView >= 4.0.0
author:
    - Priyanka Sood (@soodpr)
    - Madhav Bharadwaj (@madhav-bharadwaj)
    - Ricardo Galeno (@ricardogpsf)
    - Alex Monteiro (@aalexmonteiro)
options:
    storage_hostname:
      description:
        - Storage System IP or hostname.
    name:
      description:
        - Storage System name.
    options:
      description:
        - "List with options to gather additional facts about a Storage System and related resources.
          Options allowed:
          C(hostTypes) gets the list of supported host types.
          C(storagePools) gets a list of storage pools belonging to the specified storage system.
          C(reachablePorts) gets a list of storage system reachable ports. Accepts C(params).
            An additional C(networks) list param can be used to restrict the search for only these ones.
          C(templates) gets a list of storage templates belonging to the storage system."
        - "To gather facts about C(storagePools), C(reachablePorts), and C(templates) it is required to inform
            either the argument C(name), or C(storage_hostname). Otherwise, this option will be ignored."
extends_documentation_fragment:
    - oneview
    - oneview.factsparams
'''

EXAMPLES = '''
- name: Gather facts about all Storage Systems
  oneview_storage_system_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost

- debug: var=storage_systems

- name: Gather paginated, filtered and sorted facts about Storage Systems
  oneview_storage_system_facts:
    params:
      start: 0
      count: 3
      sort: 'name:descending'
      filter: managedDomain=TestDomain
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true

- debug: var=storage_systems

- name: Gather facts about a Storage System by IP
  oneview_storage_system_facts:
    storage_hostname: "172.18.11.12"
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost

- debug: var=storage_systems

- name: Gather facts about a Storage System by hostname
  oneview_storage_system_facts:
    storage_hostname: "172.18.11.12"
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost

- debug: var=storage_systems


- name: Gather facts about a Storage System by name
  oneview_storage_system_facts:
    name: "ThreePAR7200-4555"
    storage_hostname: "172.18.11.12"
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost

- debug: var=storage_systems

- name: Gather facts about a Storage System and all options
  oneview_storage_system_facts:
    name: "ThreePAR7200-4555"
    options:
        - hostTypes
        - storagePools
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost

- debug: var=storage_systems
- debug: var=storage_system_host_types
- debug: var=storage_system_pools

- name: Gather queried facts about Storage System reachable ports
  oneview_storage_system_facts:
    storage_hostname: "172.18.11.12"
    options:
        - reachablePorts
    params:
      networks:
        - /rest/fc-networks/01FC123456
        - /rest/fc-networks/02FC123456
      sort: 'name:descending'
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true

- debug: var=storage_system_reachable_ports

- name: Gather facts about Storage System storage templates
  oneview_storage_system_facts:
    storage_hostname: "172.18.11.12"
    options:
      - templates
    params:
      sort: 'name:descending'
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true

- debug: var=storage_system_templates
'''

RETURN = '''
storage_systems:
    description: Has all the OneView facts about the Storage Systems.
    returned: Always, but can be null.
    type: dict

storage_system_host_types:
    description: Has all the OneView facts about the supported host types.
    returned: When requested, but can be null.
    type: dict

storage_system_pools:
    description: Has all the OneView facts about the Storage Systems - Storage Pools.
    returned: When requested, but can be null.
    type: dict

storage_system_reachable_ports:
    description: Has all the OneView facts about the Storage Systems reachable ports.
    returned: When requested, but can be null.
    type: dict

storage_system_templates:
    description: Has all the OneView facts about the Storage Systems - Storage Templates.
    returned: When requested, but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class StorageSystemFactsModule(OneViewModuleBase):
    def __init__(self):
        argument_spec = dict(
            name=dict(type='str'),
            options=dict(type='list'),
            params=dict(type='dict'),
            storage_hostname=dict(type='str')
        )

        super(StorageSystemFactsModule, self).__init__(additional_arg_spec=argument_spec)
        self.resource_client = self.oneview_client.storage_systems

    def execute_module(self):
        facts = {}
        is_specific_storage_system = True
        # This allows using both "ip_hostname" and "hostname" regardless api_version
        if self.oneview_client.api_version >= 500:
            get_method = self.oneview_client.storage_systems.get_by_hostname
        else:
            get_method = self.oneview_client.storage_systems.get_by_ip_hostname

        if self.module.params.get('storage_hostname'):
            storage_systems = get_method(self.module.params['storage_hostname'])
        elif self.module.params.get('name'):
            storage_systems = self.oneview_client.storage_systems.get_by_name(self.module.params['name'])
        else:
            storage_systems = self.oneview_client.storage_systems.get_all(**self.facts_params)
            is_specific_storage_system = False

        self.__get_options(facts, storage_systems, is_specific_storage_system)

        facts['storage_systems'] = storage_systems

        return dict(changed=False, ansible_facts=facts)

    def __get_options(self, facts, storage_system, is_specific_storage_system):

        if self.options:
            if self.options.get('hostTypes'):
                facts['storage_system_host_types'] = self.oneview_client.storage_systems.get_host_types()

            if storage_system and is_specific_storage_system:
                storage_uri = storage_system['uri']
                query_params = self.module.params.get('params', {})
                if self.options.get('storagePools'):
                    facts['storage_system_pools'] = self.oneview_client.storage_systems.get_storage_pools(storage_uri)
                if self.options.get('reachablePorts'):
                    facts['storage_system_reachable_ports'] = \
                        self.oneview_client.storage_systems.get_reachable_ports(storage_uri, **query_params)
                if self.options.get('templates'):
                    facts['storage_system_templates'] = \
                        self.oneview_client.storage_systems.get_templates(storage_uri, **query_params)


def main():
    StorageSystemFactsModule().run()


if __name__ == '__main__':
    main()
