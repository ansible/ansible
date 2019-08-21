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
module: cp_mgmt_run_threat_emulation_file_types_offline_update
short_description: Update Threat Emulation file types offline.
description:
  - Update Threat Emulation file types offline.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  file_path:
    description:
      - File path for offline update of Threat Emulation file types, the file path should be on the management machine.
    type: str
  file_raw_data:
    description:
      - The contents of a file containing the Threat Emulation file types.
    type: str
extends_documentation_fragment: checkpoint_commands
"""

EXAMPLES = """
- name: run-threat-emulation-file-types-offline-update
  cp_mgmt_run_threat_emulation_file_types_offline_update:
    file_path: /tmp/FileTypeUpdate.xml
"""

RETURN = """
cp_mgmt_run_threat_emulation_file_types_offline_update:
  description: The checkpoint run-threat-emulation-file-types-offline-update output.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_commands, api_command


def main():
    argument_spec = dict(
        file_path=dict(type='str'),
        file_raw_data=dict(type='str')
    )
    argument_spec.update(checkpoint_argument_spec_for_commands)

    module = AnsibleModule(argument_spec=argument_spec)

    command = "run-threat-emulation-file-types-offline-update"

    result = api_command(module, command)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
