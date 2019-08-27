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
module: oneview_datacenter_info
short_description: Retrieve information about the OneView Data Centers
description:
    - Retrieve information about the OneView Data Centers.
    - This module was called C(oneview_datacenter_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(oneview_datacenter_info) module no longer returns C(ansible_facts)!
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
        - "Retrieve additional information. Options available: 'visualContent'."

extends_documentation_fragment:
    - oneview
    - oneview.factsparams
'''

EXAMPLES = '''
- name: Gather information about all Data Centers
  oneview_datacenter_info:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  delegate_to: localhost
  register: result
- debug:
    msg: "{{ result.datacenters }}"

- name: Gather paginated, filtered and sorted information about Data Centers
  oneview_datacenter_info:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    params:
      start: 0
      count: 3
      sort: 'name:descending'
      filter: 'state=Unmanaged'
  register: result
- debug:
    msg: "{{ result.datacenters }}"

- name: Gather information about a Data Center by name
  oneview_datacenter_info:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    name: "My Data Center"
  delegate_to: localhost
  register: result
- debug:
    msg: "{{ result.datacenters }}"

- name: Gather information about the Data Center Visual Content
  oneview_datacenter_info:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    name: "My Data Center"
    options:
      - visualContent
  delegate_to: localhost
  register: result
- debug:
    msg: "{{ result.datacenters }}"
- debug:
    msg: "{{ result.datacenter_visual_content }}"
'''

RETURN = '''
datacenters:
    description: Has all the OneView information about the Data Centers.
    returned: Always, but can be null.
    type: dict

datacenter_visual_content:
    description: Has information about the Data Center Visual Content.
    returned: When requested, but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class DatacenterInfoModule(OneViewModuleBase):
    argument_spec = dict(
        name=dict(type='str'),
        options=dict(type='list'),
        params=dict(type='dict')
    )

    def __init__(self):
        super(DatacenterInfoModule, self).__init__(additional_arg_spec=self.argument_spec)
        self.is_old_facts = self.module._name == 'oneview_datacenter_facts'
        if self.is_old_facts:
            self.module.deprecate("The 'oneview_datacenter_facts' module has been renamed to 'oneview_datacenter_info', "
                                  "and the renamed one no longer returns ansible_facts", version='2.13')

    def execute_module(self):

        client = self.oneview_client.datacenters
        info = {}

        if self.module.params.get('name'):
            datacenters = client.get_by('name', self.module.params['name'])

            if self.options and 'visualContent' in self.options:
                if datacenters:
                    info['datacenter_visual_content'] = client.get_visual_content(datacenters[0]['uri'])
                else:
                    info['datacenter_visual_content'] = None

            info['datacenters'] = datacenters
        else:
            info['datacenters'] = client.get_all(**self.facts_params)

        if self.is_old_facts:
            return dict(changed=False,
                        ansible_facts=info)
        else:
            return dict(changed=False, **info)


def main():
    DatacenterInfoModule().run()


if __name__ == '__main__':
    main()
