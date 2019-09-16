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
module: oneview_logical_interconnect_group_info
short_description: Retrieve information about one or more of the OneView Logical Interconnect Groups
description:
    - Retrieve information about one or more of the Logical Interconnect Groups from OneView
    - This module was called C(oneview_logical_interconnect_group_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(oneview_logical_interconnect_group_info) module no longer returns C(ansible_facts)!
version_added: "2.5"
requirements:
    - hpOneView >= 2.0.1
author:
    - Felipe Bulsoni (@fgbulsoni)
    - Thiago Miotto (@tmiotto)
    - Adriane Cardozo (@adriane-cardozo)
options:
    name:
      description:
        - Logical Interconnect Group name.
extends_documentation_fragment:
    - oneview
    - oneview.factsparams
'''

EXAMPLES = '''
- name: Gather information about all Logical Interconnect Groups
  oneview_logical_interconnect_group_info:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.logical_interconnect_groups }}"

- name: Gather paginated, filtered and sorted information about Logical Interconnect Groups
  oneview_logical_interconnect_group_info:
    params:
      start: 0
      count: 3
      sort: name:descending
      filter: name=LIGName
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.logical_interconnect_groups }}"

- name: Gather information about a Logical Interconnect Group by name
  oneview_logical_interconnect_group_info:
    name: logical interconnect group name
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.logical_interconnect_groups }}"
'''

RETURN = '''
logical_interconnect_groups:
    description: Has all the OneView information about the Logical Interconnect Groups.
    returned: Always, but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class LogicalInterconnectGroupInfoModule(OneViewModuleBase):
    def __init__(self):

        argument_spec = dict(
            name=dict(type='str'),
            params=dict(type='dict'),
        )

        super(LogicalInterconnectGroupInfoModule, self).__init__(additional_arg_spec=argument_spec)
        self.is_old_facts = self.module._name == 'oneview_logical_interconnect_group_facts'
        if self.is_old_facts:
            self.module.deprecate("The 'oneview_logical_interconnect_group_facts' module has been renamed to 'oneview_logical_interconnect_group_info', "
                                  "and the renamed one no longer returns ansible_facts", version='2.13')

    def execute_module(self):
        if self.module.params.get('name'):
            ligs = self.oneview_client.logical_interconnect_groups.get_by('name', self.module.params['name'])
        else:
            ligs = self.oneview_client.logical_interconnect_groups.get_all(**self.facts_params)

        if self.is_old_facts:
            return dict(changed=False, ansible_facts=dict(logical_interconnect_groups=ligs))
        else:
            return dict(changed=False, logical_interconnect_groups=ligs)


def main():
    LogicalInterconnectGroupInfoModule().run()


if __name__ == '__main__':
    main()
