#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage CheckPoint Firewall (c) 2019
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
module: cp_mgmt_assign_session
short_description: Assign a session ownership to another administrator.
description:
  - Assign a session ownership to another administrator.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  administrator_name:
    description:
      - Assignee administrator name. Specify it to assign a session to another administrator.
    type: str
  disconnect_active_session:
    description:
      - Allows assignment of an active session, currently executed by another administrator.
    type: bool
extends_documentation_fragment: checkpoint_commands
"""

EXAMPLES = """
- name: assign-session
  cp_mgmt_assign_session:
    uid: 41e821a0-3720-11e3-aa6e-0800200c9fde
"""

RETURN = """
cp_mgmt_assign_session:
  description: The checkpoint assign-session output.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_commands, api_command


def main():
    argument_spec = dict(
        administrator_name=dict(type='str'),
        disconnect_active_session=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_commands)

    module = AnsibleModule(argument_spec=argument_spec)

    command = "assign-session"

    result = api_command(module, command)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
