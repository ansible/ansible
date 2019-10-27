#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: jboss_command
short_description: Execute JBoss commands using Management API.
description:
    - Uses DMR Model to send commands over Management API.
author:
  - Jairo Junior (@jairojunior)
version_added: 2.10
options:
    name:
      description: Name of the operation to be executed.
      required: true
      aliases: [operation]
      type: str
    path:
      description: Path in JBoss-CLI syntax to execute the operation.
      required: false
      aliases: [target]
      type: str
    parameters:
      description: Parameters of the operation.
      required: false
      type: dict
    ignore_failed_outcome:
      description: Whether it should ignore non sucessful outcomes.
      required: false
      default: false
      type: bool
extends_documentation_fragment: jboss
'''

EXAMPLES = '''
---
# Read datasource state
- jboss_command:
    username: admin
    password: admin
    operation: read-attribute
    path: "java:jboss/datasources/petshopDSXA"
    parameters:
      name: enable
  register: check_enabled

# Enable if it's not already
- jboss_command:
    username: admin
    password: admin
    operation: enable
    path: "java:jboss/datasources/petshopDSXA"
  when: check_enabled.meta.result == true

# Check server-state
- jboss_command:
    operation: read-attribute
    parameters:
      name: server-state
  changed_when: False
  environment:
    JBOSS_MANAGEMENT_USER: admin
    JBOSS_MANAGEMENT_PASSWORD: admin
  register: server_state

# Get deployment info
- jboss_command:
    username: admin
    password: admin
    path: "/deployment=*"
    operation: query
    parameters:
      select: ["name", "runtime-name", "presistent", "enabled", "status"]
  register: deployment_info

# Reload if necessary
- jboss_command:
    username: admin
    password: admin
    operation: reload
  when: server_state.meta.result == "reload-required"
'''

RETURN = '''
---
meta:
    description: Management API response
    returned: success
    type: dict
    sample: "{'outcome': 'success', 'response-headers': {'process-state': 'reload-required'}}"
'''


from ansible.module_utils.jboss.common import Client
from ansible.module_utils.jboss.common import OperationError
from ansible.module_utils.jboss.common import JBossAnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = JBossAnsibleModule(
        argument_spec=dict(
            name=dict(aliases=['operation'], required=True, type='str'),
            path=dict(aliases=['target'], required=False, type='str'),
            parameters=dict(required=False, type='dict', default=dict()),
            ignore_failed_outcome=dict(required=False, type='bool', default=False),
        ),
        supports_check_mode=False
    )

    client = Client.from_config(module.params)

    try:
        output = client.execute(operation=module.params['name'],
                                parameters=module.params['parameters'],
                                ignore_failed_outcome=module.params['ignore_failed_outcome'],
                                path=module.params['path'])
        module.exit_json(changed=True, meta=output)
    except OperationError as err:
        module.fail_json(msg=to_native(err))


if __name__ == '__main__':
    main()
