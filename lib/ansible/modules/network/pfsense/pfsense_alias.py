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
module: pfsense_alias
version_added: "2.10"
author: Orion Poplawski (@opoplawski), Frederic Bor (@f-bor)
short_description: Manage pfSense aliases
description:
  - Manage pfSense aliases
notes:
options:
  name:
    description: The name of the alias
    required: true
    type: str
  state:
    description: State in which to leave the alias
    choices: [ "present", "absent" ]
    default: present
    type: str
  type:
    description: The type of the alias
    choices: [ "host", "network", "port", "urltable", "urltable_ports" ]
    default: null
    type: str
  address:
    description: The address of the alias. Use a space separator for multiple values
    default: null
    type: str
  descr:
    description: The description of the alias
    default: null
    type: str
  detail:
    description: The descriptions of the items. Use || separator between items
    default: null
    type: str
  updatefreq:
    description: Update frequency in days for urltable
    default: null
    type: int
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
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: ["create alias 'adservers', type='host', address='10.0.0.1 10.0.0.2'", "update alias 'one_host' set address='10.9.8.7'", "delete alias 'one_alias'"]
diff:
    description: a pair of dicts, before and after, with alias settings before and after task run
    returned: always
    type: dict
    sample: {}
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.alias import PFSenseAliasModule, ALIAS_ARGUMENT_SPEC, ALIAS_REQUIRED_IF


def main():
    module = AnsibleModule(
        argument_spec=ALIAS_ARGUMENT_SPEC,
        required_if=ALIAS_REQUIRED_IF,
        supports_check_mode=True)

    pfmodule = PFSenseAliasModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
