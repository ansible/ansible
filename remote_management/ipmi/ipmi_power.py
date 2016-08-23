#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
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

try:
    from pyghmi.ipmi import command
except ImportError:
    command = None

from ansible.module_utils.basic import *


DOCUMENTATION = '''
---
module: ipmi_power
short_description: Power management for machine
description:
  - Use this module for power management
version_added: "2.2"
options:
  name:
    description:
      - Hostname or ip address of the BMC.
    required: true
  port:
    description:
      - Remote RMCP port.
    required: false
    type: int
    default: 623
  user:
    description:
      - Username to use to connect to the BMC.
    required: true
  password:
    description:
      - Password to connect to the BMC.
    required: true
    default: null
  state:
    description:
      - Whether to ensure that the machine in desired state.
    required: true
    choices:
        - on -- Request system turn on
        - off -- Request system turn off without waiting for OS to shutdown
        - shutdown -- Have system request OS proper shutdown
        - reset -- Request system reset without waiting for OS
        - boot -- If system is off, then 'on', else 'reset'
  timeout:
    description:
      - Maximum number of seconds before interrupt request.
    required: false
    type: int
    default: 300
requirements:
  - "python >= 2.6"
  - pyghmi
author: "Bulat Gaifullin (gaifullinbf@gmail.com)"
'''

RETURN = '''
powerstate:
    description: The current power state of the machine.
    returned: success
    type: string
    sample: on
'''

EXAMPLES = '''
# Ensure machine is powered on.
- ipmi_power: name="test.testdomain.com" user="admin" password="password" state="on"
'''

# ==================================================


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            port=dict(default=623, type='int'),
            state=dict(required=True, choices=['on', 'off', 'shutdown', 'reset', 'boot']),
            user=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            timeout=dict(default=300, type='int'),
        ),
        supports_check_mode=True,
    )

    if command is None:
        module.fail_json(msg='the python pyghmi module is required')

    name = module.params['name']
    port = module.params['port']
    user = module.params['user']
    password = module.params['password']
    state = module.params['state']
    timeout = module.params['timeout']

    # --- run command ---
    try:
        ipmi_cmd = command.Command(
            bmc=name, userid=user, password=password, port=port
        )
        module.debug('ipmi instantiated - name: "%s"' % name)

        current = ipmi_cmd.get_power()
        if current['powerstate'] != state:
            response = {'powerstate': state} if module.check_mode else ipmi_cmd.set_power(state, wait=timeout)
            changed = True
        else:
            response = current
            changed = False

        if 'error' in response:
            module.fail_json(msg=response['error'])

        module.exit_json(changed=changed, **response)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
