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

module: nxos_ntp_options
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages NTP options.
description:
    - Manages NTP options, e.g. authoritative server and logging.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - At least one of C(master) or C(logging) params must be supplied.
    - When C(state=absent), boolean parameters are flipped,
      e.g. C(master=true) will disable the authoritative server.
    - When C(state=absent) and C(master=true), the stratum will be removed as well.
    - When C(state=absent) and C(master=false), the stratum will be configured
      to its default value, 8.
options:
    master:
        description:
            - Sets whether the device is an authoritative NTP server.
        required: false
        default: null
        choices: ['true','false']
    stratum:
        description:
            - If C(master=true), an optional stratum can be supplied (1-15).
              The device default is 8.
        required: false
        default: null
    logging:
        description:
            - Sets whether NTP logging is enabled on the device.
        required: false
        default: null
        choices: ['true','false']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
# Basic NTP options configuration
- nxos_ntp_options:
    master: true
    stratum: 12
    logging: false
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["no ntp logging", "ntp master 11"]
'''
import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def get_current(module):
    cmd = ('show running-config', 'show ntp logging')

    output = run_commands(module, ({'command': cmd[0], 'output': 'text'},
                                   {'command': cmd[1], 'output': 'text'}))

    match = re.search(r"^ntp master(?: (\d+))", output[0], re.M)
    if match:
        master = True
        stratum = match.group(1)
    else:
        master = False
        stratum = None

    logging = 'enabled' in output[1].lower()

    return {'master': master, 'stratum': stratum, 'logging': logging}


def main():
    argument_spec = dict(
        master=dict(required=False, type='bool'),
        stratum=dict(required=False, type='str', default='8'),
        logging=dict(required=False, type='bool'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    master = module.params['master']
    stratum = module.params['stratum']
    logging = module.params['logging']
    state = module.params['state']

    if stratum:
        try:
            stratum_int = int(stratum)
            if stratum_int < 1 or stratum_int > 15:
                raise ValueError
        except ValueError:
            module.fail_json(msg='stratum must be an integer between 1 and 15')

    desired = {'master': master, 'stratum': stratum, 'logging': logging}
    current = get_current(module)

    result = {'changed': False}

    commands = list()

    if state == 'absent':
        if current['master']:
            commands.append('no ntp master')
        if current['logging']:
            commands.append('no ntp logging')

    elif state == 'present':
        if desired['master'] and desired['master'] != current['master']:
            if desired['stratum']:
                commands.append('ntp master %s' % stratum)
            else:
                commands.append('ntp master')
        elif desired['stratum'] and desired['stratum'] != current['stratum']:
            commands.append('ntp master %s' % stratum)

        if desired['logging'] and desired['logging'] != current['logging']:
            if desired['logging']:
                commands.append('ntp logging')
            else:
                commands.append('no ntp logging')

    result['commands'] = commands
    result['updates'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    result['warnings'] = warnings

    module.exit_json(**result)


if __name__ == '__main__':
    main()
