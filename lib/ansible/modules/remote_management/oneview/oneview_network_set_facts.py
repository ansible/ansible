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
module: oneview_network_set_facts
short_description: Retrieve facts about the OneView Network Sets
description:
    - Retrieve facts about the Network Sets from OneView.
version_added: "2.4"
requirements:
    - hpOneView >= 2.0.1
author:
    - Felipe Bulsoni (@fgbulsoni)
    - Thiago Miotto (@tmiotto)
    - Adriane Cardozo (@adriane-cardozo)
options:
    name:
      description:
        - Network Set name.

    options:
      description:
        - "List with options to gather facts about Network Set.
          Option allowed: C(withoutEthernet).
          The option C(withoutEthernet) retrieves the list of network_sets excluding Ethernet networks."

extends_documentation_fragment:
    - oneview
    - oneview.factsparams
'''

EXAMPLES = '''
- name: Gather facts about all Network Sets
  oneview_network_set_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost

- debug: var=network_sets

- name: Gather paginated, filtered, and sorted facts about Network Sets
  oneview_network_set_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    params:
      start: 0
      count: 3
      sort: 'name:descending'
      filter: name='netset001'
  no_log: true
  delegate_to: localhost

- debug: var=network_sets

- name: Gather facts about all Network Sets, excluding Ethernet networks
  oneview_network_set_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    options:
        - withoutEthernet
  no_log: true
  delegate_to: localhost

- debug: var=network_sets


- name: Gather facts about a Network Set by name
  oneview_network_set_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    name: Name of the Network Set
  no_log: true
  delegate_to: localhost

- debug: var=network_sets


- name: Gather facts about a Network Set by name, excluding Ethernet networks
  oneview_network_set_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    name: Name of the Network Set
    options:
        - withoutEthernet
  no_log: true
  delegate_to: localhost

- debug: var=network_sets
'''

RETURN = '''
network_sets:
    description: Has all the OneView facts about the Network Sets.
    returned: Always, but can be empty.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class NetworkSetFactsModule(OneViewModuleBase):
    argument_spec = dict(
        name=dict(type='str'),
        options=dict(type='list'),
        params=dict(type='dict'),
    )

    def __init__(self):
        super(NetworkSetFactsModule, self).__init__(additional_arg_spec=self.argument_spec)

    def execute_module(self):

        name = self.module.params.get('name')

        if 'withoutEthernet' in self.options:
            filter_by_name = ("\"'name'='%s'\"" % name) if name else ''
            network_sets = self.oneview_client.network_sets.get_all_without_ethernet(filter=filter_by_name)
        elif name:
            network_sets = self.oneview_client.network_sets.get_by('name', name)
        else:
            network_sets = self.oneview_client.network_sets.get_all(**self.facts_params)

        return dict(changed=False,
                    ansible_facts=dict(network_sets=network_sets))


def main():
    NetworkSetFactsModule().run()


if __name__ == '__main__':
    main()
