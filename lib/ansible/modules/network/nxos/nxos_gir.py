#!/usr/bin/python
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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_gir
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Trigger a graceful removal or insertion (GIR) of the switch.
description:
    - Trigger a graceful removal or insertion (GIR) of the switch.
author:
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - C(state) has effect only in combination with
      C(system_mode_maintenance_timeout) or
      C(system_mode_maintenance_on_reload_reset_reason).
    - Using C(system_mode_maintenance) and
      C(system_mode_maintenance_dont_generate_profile) would make the module
      fail, but the system mode will be triggered anyway.
options:
    system_mode_maintenance:
        description:
            - When C(system_mode_maintenance=true) it puts all enabled
              protocols in maintenance mode (using the isolate command).
              When C(system_mode_maintenance=false) it puts all enabled
              protocols in normal mode (using the no isolate command).
        type: bool
    system_mode_maintenance_dont_generate_profile:
        description:
            - When C(system_mode_maintenance_dont_generate_profile=true) it
              prevents the dynamic searching of enabled protocols and executes
              commands configured in a maintenance-mode profile.
              Use this option if you want the system to use a maintenance-mode
              profile that you have created.
              When C(system_mode_maintenance_dont_generate_profile=false) it
              prevents the dynamic searching of enabled protocols and executes
              commands configured in a normal-mode profile. Use this option if
              you want the system to use a normal-mode profile that
              you have created.
        type: bool
    system_mode_maintenance_timeout:
        description:
            - Keeps the switch in maintenance mode for a specified
              number of minutes. Range is 5-65535.
    system_mode_maintenance_shutdown:
        description:
            - Shuts down all protocols, vPC domains, and interfaces except
              the management interface (using the shutdown command).
              This option is disruptive while C(system_mode_maintenance)
              (which uses the isolate command) is not.
        type: bool
    system_mode_maintenance_on_reload_reset_reason:
        description:
            - Boots the switch into maintenance mode automatically in the
              event of a specified system crash. Note that not all reset
              reasons are applicable for all platforms. Also if reset
              reason is set to match_any, it is not idempotent as it turns
              on all reset reasons. If reset reason is match_any and state
              is absent, it turns off all the reset reasons.
        choices: ['hw_error','svc_failure','kern_failure','wdog_timeout',
                  'fatal_error','lc_failure','match_any','manual_reload',
                  'any_other', 'maintenance']
    state:
        description:
            - Specify desired state of the resource.
        required: true
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Trigger system maintenance mode
- nxos_gir:
    system_mode_maintenance: true
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Trigger system normal mode
- nxos_gir:
    system_mode_maintenance: false
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Configure on-reload reset-reason for maintenance mode
- nxos_gir:
    system_mode_maintenance_on_reload_reset_reason: manual_reload
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Add on-reload reset-reason for maintenance mode
- nxos_gir:
    system_mode_maintenance_on_reload_reset_reason: hw_error
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Remove on-reload reset-reason for maintenance mode
- nxos_gir:
    system_mode_maintenance_on_reload_reset_reason: manual_reload
    state: absent
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Set timeout for maintenance mode
- nxos_gir:
    system_mode_maintenance_timeout: 30
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Remove timeout for maintenance mode
- nxos_gir:
    system_mode_maintenance_timeout: 30
    state: absent
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
final_system_mode:
    description: describe the last system mode
    returned: verbose mode
    type: str
    sample: normal
updates:
    description: commands sent to the device
    returned: verbose mode
    type: list
    sample: ["terminal dont-ask", "system mode maintenance timeout 10"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re
from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule


def get_system_mode(module):
    command = {'command': 'show system mode', 'output': 'text'}
    body = run_commands(module, [command])[0]
    if body and 'normal' in body.lower():
        mode = 'normal'
    else:
        mode = 'maintenance'
    return mode


def get_maintenance_timeout(module):
    command = {'command': 'show maintenance timeout', 'output': 'text'}
    body = run_commands(module, [command])[0]
    timeout = body.split()[4]
    return timeout


def get_reset_reasons(module):
    command = {'command': 'show maintenance on-reload reset-reasons', 'output': 'text'}
    body = run_commands(module, [command])[0]
    return body


def get_commands(module, state, mode):
    commands = list()
    system_mode = ''
    if module.params['system_mode_maintenance'] is True and mode == 'normal':
        commands.append('system mode maintenance')
    elif (module.params['system_mode_maintenance'] is False and
          mode == 'maintenance'):
        commands.append('no system mode maintenance')

    elif (module.params[
        'system_mode_maintenance_dont_generate_profile'] is True and
            mode == 'normal'):
        commands.append('system mode maintenance dont-generate-profile')
    elif (module.params[
          'system_mode_maintenance_dont_generate_profile'] is False and
          mode == 'maintenance'):
        commands.append('no system mode maintenance dont-generate-profile')

    elif module.params['system_mode_maintenance_timeout']:
        timeout = get_maintenance_timeout(module)
        if (state == 'present' and
                timeout != module.params['system_mode_maintenance_timeout']):
            commands.append('system mode maintenance timeout {0}'.format(
                            module.params['system_mode_maintenance_timeout']))
        elif (state == 'absent' and
                timeout == module.params['system_mode_maintenance_timeout']):
            commands.append('no system mode maintenance timeout {0}'.format(
                            module.params['system_mode_maintenance_timeout']))

    elif (module.params['system_mode_maintenance_shutdown'] and
            mode == 'normal'):
        commands.append('system mode maintenance shutdown')
    elif (module.params[
          'system_mode_maintenance_shutdown'] is False and
          mode == 'maintenance'):
        commands.append('no system mode maintenance')

    elif module.params['system_mode_maintenance_on_reload_reset_reason']:
        reset_reasons = get_reset_reasons(module)
        if (state == 'present' and
                module.params['system_mode_maintenance_on_reload_reset_reason'].lower() not in reset_reasons.lower()):
            commands.append('system mode maintenance on-reload '
                            'reset-reason {0}'.format(
                                module.params[
                                    'system_mode_maintenance_on_reload_reset_reason']))
        elif (state == 'absent' and
              module.params[
                  'system_mode_maintenance_on_reload_reset_reason'].lower() in
              reset_reasons.lower()):
            commands.append('no system mode maintenance on-reload '
                            'reset-reason {0}'.format(
                                module.params[
                                    'system_mode_maintenance_on_reload_reset_reason']))

    if commands:
        commands.insert(0, 'terminal dont-ask')
    return commands


def main():
    argument_spec = dict(
        system_mode_maintenance=dict(required=False, type='bool'),
        system_mode_maintenance_dont_generate_profile=dict(required=False,
                                                           type='bool'),
        system_mode_maintenance_timeout=dict(required=False, type='str'),
        system_mode_maintenance_shutdown=dict(required=False, type='bool'),
        system_mode_maintenance_on_reload_reset_reason=dict(required=False,
                                                            choices=['hw_error', 'svc_failure', 'kern_failure',
                                                                     'wdog_timeout', 'fatal_error', 'lc_failure',
                                                                     'match_any', 'manual_reload', 'any_other',
                                                                     'maintenance']),
        state=dict(choices=['absent', 'present', 'default'],
                   default='present', required=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[[
                               'system_mode_maintenance',
                               'system_mode_maintenance_dont_generate_profile',
                               'system_mode_maintenance_timeout',
                               'system_mode_maintenance_shutdown',
                               'system_mode_maintenance_on_reload_reset_reason'
                           ]],
                           required_one_of=[[
                               'system_mode_maintenance',
                               'system_mode_maintenance_dont_generate_profile',
                               'system_mode_maintenance_timeout',
                               'system_mode_maintenance_shutdown',
                               'system_mode_maintenance_on_reload_reset_reason'
                           ]],
                           supports_check_mode=True)

    warnings = list()

    state = module.params['state']
    mode = get_system_mode(module)
    commands = get_commands(module, state, mode)
    changed = False
    if commands:
        if module.check_mode:
            module.exit_json(changed=True, commands=commands)
        else:
            load_config(module, commands)
            changed = True

    result = {}
    result['changed'] = changed
    if module._verbosity > 0:
        final_system_mode = get_system_mode(module)
        result['final_system_mode'] = final_system_mode
        result['updates'] = commands

    result['warnings'] = warnings

    module.exit_json(**result)


if __name__ == '__main__':
    main()
