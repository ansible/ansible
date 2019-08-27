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
module: oneview_fcoe_network_info
short_description: Retrieve the information about one or more of the OneView FCoE Networks
description:
    - Retrieve the information about one or more of the FCoE Networks from OneView.
    - This module was called C(oneview_fcoe_network_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(oneview_fcoe_network_info) module no longer returns C(ansible_facts)!
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
        - FCoE Network name.
extends_documentation_fragment:
    - oneview
    - oneview.factsparams
'''

EXAMPLES = '''
- name: Gather information about all FCoE Networks
  oneview_fcoe_network_info:
    config: /etc/oneview/oneview_config.json
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.fcoe_networks }}"

- name: Gather paginated, filtered and sorted information about FCoE Networks
  oneview_fcoe_network_info:
    config: /etc/oneview/oneview_config.json
    params:
      start: 0
      count: 3
      sort: 'name:descending'
      filter: 'vlanId=2'
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.fcoe_networks }}"

- name: Gather information about a FCoE Network by name
  oneview_fcoe_network_info:
    config: /etc/oneview/oneview_config.json
    name: Test FCoE Network Information
  delegate_to: localhost
  register: result

- debug:
    msg: "{{ result.fcoe_networks }}"
'''

RETURN = '''
fcoe_networks:
    description: Has all the OneView information about the FCoE Networks.
    returned: Always, but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class FcoeNetworkInfoModule(OneViewModuleBase):
    def __init__(self):
        argument_spec = dict(
            name=dict(type='str'),
            params=dict(type='dict'),
        )

        super(FcoeNetworkInfoModule, self).__init__(additional_arg_spec=argument_spec)
        self.is_old_facts = self.module._name == 'oneview_fcoe_network_facts'
        if self.is_old_facts:
            self.module.deprecate("The 'oneview_fcoe_network_facts' module has been renamed to 'oneview_fcoe_network_info', "
                                  "and the renamed one no longer returns ansible_facts", version='2.13')

    def execute_module(self):

        if self.module.params['name']:
            fcoe_networks = self.oneview_client.fcoe_networks.get_by('name', self.module.params['name'])
        else:
            fcoe_networks = self.oneview_client.fcoe_networks.get_all(**self.facts_params)

        if self.is_old_facts:
            return dict(changed=False,
                        ansible_facts=dict(fcoe_networks=fcoe_networks))
        else:
            return dict(changed=False, fcoe_networks=fcoe_networks)


def main():
    FcoeNetworkInfoModule().run()


if __name__ == '__main__':
    main()
