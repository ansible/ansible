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
module: oneview_san_manager_info
short_description: Retrieve information about one or more of the OneView SAN Managers
description:
    - Retrieve information about one or more of the SAN Managers from OneView
    - This module was called C(oneview_san_manager_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(oneview_san_manager_info) module no longer returns C(ansible_facts)!
version_added: "2.5"
requirements:
    - hpOneView >= 2.0.1
author:
    - Felipe Bulsoni (@fgbulsoni)
    - Thiago Miotto (@tmiotto)
    - Adriane Cardozo (@adriane-cardozo)
options:
    provider_display_name:
      description:
        - Provider Display Name.
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           - C(start): The first item to return, using 0-based indexing.
           - C(count): The number of resources to return.
           - C(query): A general query string to narrow the list of resources returned.
           - C(sort): The sort order of the returned data set."
extends_documentation_fragment:
    - oneview
'''

EXAMPLES = '''
- name: Gather information about all SAN Managers
  oneview_san_manager_info:
    config: /etc/oneview/oneview_config.json
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.san_managers }}"

- name: Gather paginated, filtered and sorted information about SAN Managers
  oneview_san_manager_info:
    config: /etc/oneview/oneview_config.json
    params:
      start: 0
      count: 3
      sort: name:ascending
      query: isInternal eq false
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.san_managers }}"

- name: Gather information about a SAN Manager by provider display name
  oneview_san_manager_info:
    config: /etc/oneview/oneview_config.json
    provider_display_name: Brocade Network Advisor
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.san_managers }}"
'''

RETURN = '''
san_managers:
    description: Has all the OneView information about the SAN Managers.
    returned: Always, but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class SanManagerInfoModule(OneViewModuleBase):
    argument_spec = dict(
        provider_display_name=dict(type='str'),
        params=dict(type='dict')
    )

    def __init__(self):
        super(SanManagerInfoModule, self).__init__(additional_arg_spec=self.argument_spec)
        self.resource_client = self.oneview_client.san_managers
        self.is_old_facts = self.module._name == 'oneview_san_manager_facts'
        if self.is_old_facts:
            self.module.deprecate("The 'oneview_san_manager_facts' module has been renamed to 'oneview_san_manager_info', "
                                  "and the renamed one no longer returns ansible_facts", version='2.13')

    def execute_module(self):
        if self.module.params.get('provider_display_name'):
            provider_display_name = self.module.params['provider_display_name']
            san_manager = self.oneview_client.san_managers.get_by_provider_display_name(provider_display_name)
            if san_manager:
                resources = [san_manager]
            else:
                resources = []
        else:
            resources = self.oneview_client.san_managers.get_all(**self.facts_params)

        if self.is_old_facts:
            return dict(changed=False, ansible_facts=dict(san_managers=resources))
        else:
            return dict(changed=False, san_managers=resources)


def main():
    SanManagerInfoModule().run()


if __name__ == '__main__':
    main()
