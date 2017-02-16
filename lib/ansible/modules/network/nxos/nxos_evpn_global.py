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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: nxos_evpn_global
version_added: "2.2"
short_description: Handles the EVPN control plane for VXLAN.
description:
    - Handles the EVPN control plane for VXLAN.
author: Gabriele Gerbino (@GGabriele)
options:
    nv_overlay_evpn:
        description:
            - EVPN control plane.
        required: true
        choices: ['true', 'false']
'''
EXAMPLES = '''
- nxos_evpn_global:
    nv_overlay_evpn: true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"nv_overlay_evpn": true}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"nv_overlay_evpn": false}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"nv_overlay_evpn": true}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["nv overlay evpn"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


import re
from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import CustomNetworkConfig

PARAM_TO_COMMAND_KEYMAP = {
    'nv_overlay_evpn': 'nv overlay evpn',
}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(arg, config, module):
    REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
    value = False
    if REGEX.search(config):
        value = True
    return value


def get_existing(module):
    existing = {}
    config = str(get_config(module))

    existing['nv_overlay_evpn'] = get_value('nv_overlay_evpn', config, module)
    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = value
            else:
                new_dict[new_key] = value
    return new_dict


def get_commands(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.items():
        if value is True:
            commands.append(key)
        elif value is False:
            commands.append('no {0}'.format(key))

    if commands:
        candidate.add(commands, parents=[])


def main():
    argument_spec = dict(
        nv_overlay_evpn=dict(required=True, type='bool'),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    existing = invoke('get_existing', module)
    end_state = existing
    proposed = dict(nv_overlay_evpn=module.params['nv_overlay_evpn'])

    result = {}
    candidate = CustomNetworkConfig(indent=3)
    invoke('get_commands', module, existing, proposed, candidate)

    if proposed != existing:
        try:
            response = load_config(module, candidate)
            result.update(response)
        except ShellError:
            exc = get_exception()
            module.fail_json(msg=str(exc))
    else:
        result['updates'] = []

    result['connected'] = module.connected
    if module._verbosity > 0:
        end_state = invoke('get_existing', module)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed

    result['warnings'] = warnings

    module.exit_json(**result)


if __name__ == '__main__':
    main()

