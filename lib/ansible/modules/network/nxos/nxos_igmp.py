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
module: nxos_igmp
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages IGMP global configuration.
description:
    - Manages IGMP global configuration configuration settings.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - When C(state=default), all supported params will be reset to a
      default state.
    - If restart is set to true with other params set, the restart will happen
      last, i.e. after the configuration takes place.
options:
    flush_routes:
        description:
            - Removes routes when the IGMP process is restarted. By default,
              routes are not flushed.
        required: false
        default: null
        choices: ['true', 'false']
    enforce_rtr_alert:
        description:
            - Enables or disables the enforce router alert option check for
              IGMPv2 and IGMPv3 packets.
        required: false
        default: null
        choices: ['true', 'false']
    restart:
        description:
            - Restarts the igmp process (using an exec config command).
        required: false
        default: null
        choices: ['true', 'false']
    state:
        description:
            - Manages desired state of the resource.
        required: false
        default: present
        choices: ['present', 'default']
'''
EXAMPLES = '''
- name: Default igmp global params (all params except restart)
  nxos_igmp:
    state: default
    host: "{{ inventory_hostname }}"

- name: Ensure the following igmp global config exists on the device
  nxos_igmp:
    flush_routes: true
    enforce_rtr_alert: true
    host: "{{ inventory_hostname }}"

- name: Restart the igmp process
  nxos_igmp:
    restart: true
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["ip igmp flush-routes"]
'''
from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def get_current(module):
    output = run_commands(module, {'command': 'show running-config', 'output': 'text'})
    return {
        'flush_routes': 'ip igmp flush-routes' in output[0],
        'enforce_rtr_alert': 'ip igmp enforce-router-alert' in output[0]
    }


def get_desired(module):
    return {
        'flush_routes': module.params['flush_routes'],
        'enforce_rtr_alert': module.params['enforce_rtr_alert']
    }


def main():
    argument_spec = dict(
        flush_routes=dict(type='bool'),
        enforce_rtr_alert=dict(type='bool'),
        restart=dict(type='bool', default=False),

        state=dict(choices=['present', 'default'], default='present'),

        include_defaults=dict(default=False),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    current = get_current(module)
    desired = get_desired(module)

    state = module.params['state']
    restart = module.params['restart']

    commands = list()

    if state == 'default':
        if current['flush_routes']:
            commands.append('no ip igmp flush-routes')
        if current['enforce_rtr_alert']:
            commands.append('no ip igmp enforce-router-alert')

    elif state == 'present':
        if desired['flush_routes'] and not current['flush_routes']:
            commands.append('ip igmp flush-routes')
        if desired['enforce_rtr_alert'] and not current['enforce_rtr_alert']:
            commands.append('ip igmp enforce-router-alert')

    result = {'changed': False, 'updates': commands, 'warnings': warnings}

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    if module.params['restart']:
        run_commands(module, 'restart igmp')

    module.exit_json(**result)


if __name__ == '__main__':
    main()
