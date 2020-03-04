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
module: cp_mgmt_run_script
short_description: Executes the script on a given list of targets.
description:
  - Executes the script on a given list of targets.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  script_name:
    description:
      - Script name.
    type: str
  script:
    description:
      - Script body.
    type: str
  targets:
    description:
      - On what targets to execute this command. Targets may be identified by their name, or object unique identifier.
    type: list
  args:
    description:
      - Script arguments.
    type: str
  comments:
    description:
      - Comments string.
    type: str
extends_documentation_fragment: checkpoint_commands
"""

EXAMPLES = """
- name: run-script
  cp_mgmt_run_script:
    script: ls -l /
    script_name: 'Script Example: List files under / dir'
    targets:
    - corporate-gateway
"""

RETURN = """
cp_mgmt_run_script:
  description: The checkpoint run-script output.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_commands, api_command


def main():
    argument_spec = dict(
        script_name=dict(type='str'),
        script=dict(type='str'),
        targets=dict(type='list'),
        args=dict(type='str'),
        comments=dict(type='str')
    )
    argument_spec.update(checkpoint_argument_spec_for_commands)

    module = AnsibleModule(argument_spec=argument_spec)

    command = "run-script"

    result = api_command(module, command)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
