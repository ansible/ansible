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
module: cp_mgmt_run_ips_update
short_description: Runs IPS database update. If "package-path" is not provided server will try to get the latest package from the User Center.
description:
  - Runs IPS database update. If "package-path" is not provided server will try to get the latest package from the User Center.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  package_path:
    description:
      - Offline update package path.
    type: str
extends_documentation_fragment: checkpoint_commands
"""

EXAMPLES = """
- name: run-ips-update
  cp_mgmt_run_ips_update:
"""

RETURN = """
cp_mgmt_run_ips_update:
  description: The checkpoint run-ips-update output.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_commands, api_command


def main():
    argument_spec = dict(
        package_path=dict(type='str')
    )
    argument_spec.update(checkpoint_argument_spec_for_commands)

    module = AnsibleModule(argument_spec=argument_spec)

    command = "run-ips-update"

    result = api_command(module, command)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
