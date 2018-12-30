#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_alias
version_added: "2.8"
author: Orion Poplawski (@opoplawski)
short_description: Manage pfSense aliases
description:
  - Manage pfSense aliases
notes:
options:
  name:
    description: The name the alias
    required: true
    default: null
  type:
    description: The type of the alias
    required: true
    default: host
    choices: [ "host", "network", "port", "urltable" ]
  state:
    description: State in which to leave the alias
    choices: [ "present", "absent" ]
  address:
    description: The address of the alias
    required: true
    default: null
  descr:
    description: Description
    default: null
  detail:
    description: Details for items
    default: ""
  updatefreq:
    description: Update frequency in days for urltable
"""

EXAMPLES = """
- name: Add adservers alias
  pfsense_alias:
    name: adservers
    address: 10.0.0.1 10.0.0.2
    state: present

- name: Remove adservers alias
  pfsense_alias:
    name: adservers
    state: absent
"""

RETURN = """
added:
    description: aliases that were added
    returned: always
    type: list
    sample: []
deleted:
    description: aliases that were removed
    returned: always
    type: list
    sample: []
modified:
    description: aliases that were modified
    returned: always
    type: list
    sample: []
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pfsense.pfsense_alias import PFSenseAliasModule, ALIASES_ARGUMENT_SPEC, ALIASES_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=ALIASES_ARGUMENT_SPEC,
        required_if=ALIASES_REQUIRED_IF,
        supports_check_mode=True)

    pfalias = PFSenseAliasModule(module)

    pfalias.run(module.params)

    pfalias.commit_changes()


if __name__ == '__main__':
    main()
