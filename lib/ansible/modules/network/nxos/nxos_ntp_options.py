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
    - When C(state=absent), master and logging will be set to False and
      stratum will be removed as well
options:
    master:
        description:
            - Sets whether the device is an authoritative NTP server.
        type: bool
    stratum:
        description:
            - If C(master=true), an optional stratum can be supplied (1-15).
              The device default is 8.
    logging:
        description:
            - Sets whether NTP logging is enabled on the device.
        type: bool
    state:
        description:
            - Manage the state of the resource.
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
    sample: ["no ntp logging", "ntp master 12"]
'''
import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def get_current(module):
    cmd = ('show running-config | inc ntp')

    master = False
    logging = False
    stratum = None

    output = run_commands(module, ({'command': cmd, 'output': 'text'}))[0]

    if output:
        match = re.search(r"^ntp master(?: (\d+))", output, re.M)
        if match:
            master = True
            stratum = match.group(1)
        logging = 'ntp logging' in output.lower()

    return {'master': master, 'stratum': stratum, 'logging': logging}


def main():
    argument_spec = dict(
        master=dict(required=False, type='bool'),
        stratum=dict(required=False, type='str'),
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

    if stratum and master is False:
        if stratum != 8:
            module.fail_json(msg='master MUST be True when stratum is changed')

    current = get_current(module)

    result = {'changed': False}

    commands = list()

    if state == 'absent':
        if current['master']:
            commands.append('no ntp master')
        if current['logging']:
            commands.append('no ntp logging')

    elif state == 'present':
        if master and not current['master']:
            commands.append('ntp master')
        elif master is False and current['master']:
            commands.append('no ntp master')
        if stratum and stratum != current['stratum']:
            commands.append('ntp master %s' % stratum)

        if logging and not current['logging']:
            commands.append('ntp logging')
        elif logging is False and current['logging']:
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
