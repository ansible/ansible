#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_vlan
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense vlans
description:
  - Manage pfSense vlans
notes:
options:
  vlan_id:
    description: The vlan tag. Must be between 1 and 4094.
    required: true
    type: int
  interface:
    description: The interface on which to declare the vlan. Friendly name (assignments) can be used.
    required: true
    type: str
  priority:
    description: 802.1Q VLAN Priority code point. Must be between 0 and 7.
    required: false
    type: int
  descr:
    description: The description of the vlan
    default: null
    type: str
  state:
    description: State in which to leave the vlan
    choices: [ "present", "absent" ]
    default: present
    type: str
"""

EXAMPLES = """
- name: Add voice vlan
  pfsense_vlan:
    interface: mvneta0
    vlan_id: 100
    descr: voice
    priority: 5
    state: present

- name: Remove voice vlan
  pfsense_vlan:
    interface: mvneta0
    vlan_id: 100
    state: absent
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: ["create vlan 'mvneta.100', descr='voice', priority='5'", "update vlan 'mvneta.100', set priority='6'", "delete vlan 'mvneta.100'"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.vlan import PFSenseVlanModule, VLAN_ARGUMENT_SPEC


def main():
    module = AnsibleModule(
        argument_spec=VLAN_ARGUMENT_SPEC,
        supports_check_mode=True)

    pfmodule = PFSenseVlanModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
