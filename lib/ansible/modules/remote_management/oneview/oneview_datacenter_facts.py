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
module: oneview_datacenter_facts
short_description: Retrieve facts about the OneView Data Centers
description:
    - Retrieve facts about the OneView Data Centers.
version_added: "2.5"
requirements:
    - "hpOneView >= 2.0.1"
author:
    - Alex Monteiro (@aalexmonteiro)
    - Madhav Bharadwaj (@madhav-bharadwaj)
    - Priyanka Sood (@soodpr)
    - Ricardo Galeno (@ricardogpsf)
options:
    name:
      description:
        - Data Center name.
    options:
      description:
        - "Retrieve additional facts. Options available: 'visualContent'."

extends_documentation_fragment:
    - oneview
    - oneview.factsparams
'''

EXAMPLES = '''
- name: Gather facts about all Data Centers
  oneview_datacenter_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  delegate_to: localhost
- debug: var=datacenters

- name: Gather paginated, filtered and sorted facts about Data Centers
  oneview_datacenter_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    params:
      start: 0
      count: 3
      sort: 'name:descending'
      filter: 'state=Unmanaged'
- debug: var=datacenters

- name: Gather facts about a Data Center by name
  oneview_datacenter_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    name: "My Data Center"
  delegate_to: localhost
- debug: var=datacenters

- name: Gather facts about the Data Center Visual Content
  oneview_datacenter_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    name: "My Data Center"
    options:
      - visualContent
  delegate_to: localhost
- debug: var=datacenters
- debug: var=datacenter_visual_content
'''

RETURN = '''
datacenters:
    description: Has all the OneView facts about the Data Centers.
    returned: Always, but can be null.
    type: dict

datacenter_visual_content:
    description: Has facts about the Data Center Visual Content.
    returned: When requested, but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class DatacenterFactsModule(OneViewModuleBase):
    argument_spec = dict(
        name=dict(type='str'),
        options=dict(type='list'),
        params=dict(type='dict')
    )

    def __init__(self):
        super(DatacenterFactsModule, self).__init__(additional_arg_spec=self.argument_spec)

    def execute_module(self):

        client = self.oneview_client.datacenters
        ansible_facts = {}

        if self.module.params.get('name'):
            datacenters = client.get_by('name', self.module.params['name'])

            if self.options and 'visualContent' in self.options:
                if datacenters:
                    ansible_facts['datacenter_visual_content'] = client.get_visual_content(datacenters[0]['uri'])
                else:
                    ansible_facts['datacenter_visual_content'] = None

            ansible_facts['datacenters'] = datacenters
        else:
            ansible_facts['datacenters'] = client.get_all(**self.facts_params)

        return dict(changed=False,
                    ansible_facts=ansible_facts)


def main():
    DatacenterFactsModule().run()


if __name__ == '__main__':
    main()
