#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Check Point Firewall (c) 2019
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_mgmt_assign_global_assignment
short_description: assign global assignment on Check Point over Web Services API
description:
  - assign global assignment on Check Point over Web Services API
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  dependent_domains:
    description:
      - N/A
    type: list
  global_domains:
    description:
      - N/A
    type: list
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
        representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
extends_documentation_fragment: checkpoint_commands
"""

EXAMPLES = """
- name: assign-global-assignment
  cp_mgmt_assign_global_assignment:
    dependent_domains: domain1
    global_domains: Global2
"""

RETURN = """
cp_mgmt_assign_global_assignment:
  description: The checkpoint assign-global-assignment output.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_commands, api_command


def main():
    argument_spec = dict(
        dependent_domains=dict(type='list'),
        global_domains=dict(type='list'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full'])
    )
    argument_spec.update(checkpoint_argument_spec_for_commands)

    module = AnsibleModule(argument_spec=argument_spec)

    command = "assign-global-assignment"

    result = api_command(module, command)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
