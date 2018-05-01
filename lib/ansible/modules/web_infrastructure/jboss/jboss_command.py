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
author: "Jairo Junior (@jairojunior)"
version_added: 2.6
options:
    name:
      description: Name of the operation to be executed.
      required: true
      aliases: [operation]
    path:
      description: Path in JBoss-CLI syntax to execute the operation.
      required: false
      aliases: [target]
    parameters:
      description: Parameters of the operation.
      required: false
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
    operation: read-attribute
    path: "java:jboss/datasources/petshopDSXA"
    parameters:
        name: enable
  register: check_enabled

# Enable if it's not already
- jboss_command:
    operation: enable
    path: "java:jboss/datasources/petshopDSXA"
  when: check_enabled.meta.result == true

# Check server-state
- jboss_command:
    operation: read-attribute
    parameters:
    name: server-state
  changed_when: False
  register: server_state

# Reload if necessary
- jboss_cli:
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

try:
    from jboss.client import Client
    from jboss.exceptions import AuthError
    from jboss.exceptions import OperationError
    HAS_JBOSS_PY = True
except ImportError:
    HAS_JBOSS_PY = False

from ansible.module_utils.jboss import JBossAnsibleModule


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

    if not HAS_JBOSS_PY:
        module.fail_json(msg='jboss-py required for this module')

    client = Client.from_config(module.params)

    try:
        output = client.execute(operation=module.params['name'],
                                parameters=module.params['parameters'],
                                ignore_failed_outcome=module.params['ignore_failed_outcome'],
                                path=module.params['path'])

        module.exit_json(changed=True, meta=output)
    except (AuthError, OperationError) as err:
        module.fail_json(msg=str(err))


if __name__ == '__main__':
    main()
