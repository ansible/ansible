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
module: nxos_vrf
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manages global VRF configuration.
description:
  - Manages global VRF configuration.
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - Cisco NX-OS creates the default VRF by itself. Therefore,
    you're not allowed to use default as I(vrf) name in this module.
  - C(vrf) name must be shorter than 32 chars.
  - VRF names are not case sensible in NX-OS. Anyway, the name is stored
    just like it's inserted by the user and it'll not be changed again
    unless the VRF is removed and re-created. i.e. C(vrf=NTC) will create
    a VRF named NTC, but running it again with C(vrf=ntc) will not cause
    a configuration change.
options:
  vrf:
    description:
      - Name of VRF to be managed.
    required: true
  admin_state:
    description:
      - Administrative state of the VRF.
    required: false
    default: up
    choices: ['up','down']
  vni:
    description:
      - Specify virtual network identifier. Valid values are Integer
        or keyword 'default'.
    required: false
    default: null
    version_added: "2.2"
  route_distinguisher:
    description:
      - VPN Route Distinguisher (RD). Valid values are a string in
        one of the route-distinguisher formats (ASN2:NN, ASN4:NN, or
        IPV4:NN); the keyword 'auto', or the keyword 'default'.
    required: false
    default: null
    version_added: "2.2"
  state:
    description:
      - Manages desired state of the resource.
    required: false
    default: present
    choices: ['present','absent']
  description:
    description:
      - Description of the VRF.
    required: false
    default: null
'''

EXAMPLES = '''
- name: Ensure ntc VRF exists on switch
  nxos_vrf:
    vrf: ntc
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["vrf context ntc", "shutdown"]
'''
import re

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module):
    if 'show run' not in command:
        output = 'json'
    else:
        output = 'text'
    cmds = [{
        'command': command,
        'output': output,
    }]
    body = run_commands(module, cmds)
    return body


def apply_key_map(key_map, table):
    new_dict = {}
    for key in table:
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = str(table.get(key))
    return new_dict


def get_commands_to_config_vrf(delta, vrf):
    commands = []
    for param, value in delta.items():
        command = ''
        if param == 'description':
            command = 'description {0}'.format(value)
        elif param == 'admin_state':
            if value.lower() == 'up':
                command = 'no shutdown'
            elif value.lower() == 'down':
                command = 'shutdown'
        elif param == 'rd':
            command = 'rd {0}'.format(value)
        elif param == 'vni':
            command = 'vni {0}'.format(value)
        if command:
            commands.append(command)
    if commands:
        commands.insert(0, 'vrf context {0}'.format(vrf))
    return commands


def get_vrf_description(vrf, module):
    command = (r'show run section vrf | begin ^vrf\scontext\s{0} | end ^vrf.*'.format(vrf))

    description = ''
    descr_regex = r".*description\s(?P<descr>[\S+\s]+).*"

    try:
        body = execute_show_command(command, module)[0]
    except IndexError:
        return description

    if body:
        splitted_body = body.split('\n')
        for element in splitted_body:
            if 'description' in element:
                match_description = re.match(descr_regex, element,
                                             re.DOTALL)
                group_description = match_description.groupdict()
                description = group_description["descr"]

    return description


def get_value(arg, config, module):
    extra_arg_regex = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(arg), re.M)
    value = ''
    if arg in config:
        value = extra_arg_regex.search(config).group('value')
    return value


def get_vrf(vrf, module):
    command = 'show vrf {0}'.format(vrf)
    vrf_key = {
        'vrf_name': 'vrf',
        'vrf_state': 'admin_state'
    }

    try:
        body = execute_show_command(command, module)[0]
        vrf_table = body['TABLE_vrf']['ROW_vrf']
    except (TypeError, IndexError):
        return {}

    parsed_vrf = apply_key_map(vrf_key, vrf_table)
    parsed_vrf['admin_state'] = parsed_vrf['admin_state'].lower()

    command = 'show run all | section vrf.context.{0}'.format(vrf)
    body = execute_show_command(command, module)[0]
    extra_params = ['vni', 'rd', 'description']
    for param in extra_params:
        parsed_vrf[param] = get_value(param, body, module)

    return parsed_vrf


def main():
    argument_spec = dict(
        vrf=dict(required=True),
        description=dict(default=None, required=False),
        vni=dict(required=False, type='str'),
        rd=dict(required=False, type='str'),
        admin_state=dict(default='up', choices=['up', 'down'], required=False),
        state=dict(default='present', choices=['present', 'absent'], required=False),
        include_defaults=dict(default=False),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = dict(changed=False, warnings=warnings)

    vrf = module.params['vrf']
    admin_state = module.params['admin_state'].lower()
    description = module.params['description']
    rd = module.params['rd']
    vni = module.params['vni']
    state = module.params['state']

    if vrf == 'default':
        module.fail_json(msg='cannot use default as name of a VRF')
    elif len(vrf) > 32:
        module.fail_json(msg='VRF name exceeded max length of 32', vrf=vrf)

    existing = get_vrf(vrf, module)
    args = dict(vrf=vrf, description=description, vni=vni,
                admin_state=admin_state, rd=rd)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    delta = dict(set(proposed.items()).difference(existing.items()))
    commands = []
    if state == 'absent':
        if existing:
            command = ['no vrf context {0}'.format(vrf)]
            commands.extend(command)

    elif state == 'present':
        if not existing:
            command = get_commands_to_config_vrf(delta, vrf)
            commands.extend(command)
        elif delta:
            command = get_commands_to_config_vrf(delta, vrf)
            commands.extend(command)

    if state == 'present' and commands:
        if proposed.get('vni'):
            if existing.get('vni') and existing.get('vni') != '':
                commands.insert(1, 'no vni {0}'.format(existing['vni']))

    if commands and not module.check_mode:
        load_config(module, commands)
        results['changed'] = True

        if 'configure' in commands:
            commands.pop(0)

    results['commands'] = commands

    module.exit_json(**results)


if __name__ == '__main__':
    main()
