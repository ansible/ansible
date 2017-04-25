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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nxos_pim
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages configuration of a PIM instance.
description:
    - Manages configuration of a Protocol Independent Multicast (PIM) instance.
author: Gabriele Gerbino (@GGabriele)
options:
    ssm_range:
        description:
            - Configure group ranges for Source Specific Multicast (SSM).
              Valid values are multicast addresses or the keyword 'none'.
        required: true
'''
EXAMPLES = '''
- nxos_pim:
    ssm_range: "232.0.0.0/8"
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"ssm_range": "232.0.0.0/8"}
existing:
    description: k/v pairs of existing PIM configuration
    returned: verbose mode
    type: dict
    sample: {"ssm_range": none}
end_state:
    description: k/v pairs of BGP configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"ssm_range": "232.0.0.0/8"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["ip pim ssm range 232.0.0.0/8"]
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

import re


PARAM_TO_COMMAND_KEYMAP = {
    'ssm_range': 'ip pim ssm range'
}
PARAM_TO_DEFAULT_KEYMAP = {}
WARNINGS = []


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(arg, config, module):
    REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
    value = ''
    if PARAM_TO_COMMAND_KEYMAP[arg] in config:
        value = REGEX.search(config).group('value')
    return value


def get_existing(module, args):
    existing = {}
    config = str(get_config(module))
    for arg in args:
        existing[arg] = get_value(arg, config, module)
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
        command = '{0} {1}'.format(key, value)
        commands.append(command)

    if commands:
        candidate.add(commands, parents=[])


def main():
    argument_spec = dict(
        ssm_range=dict(required=True, type='str'),
        m_facts=dict(required=False, default=False, type='bool'),
        include_defaults=dict(default=False),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    splitted_ssm_range = module.params['ssm_range'].split('.')
    if len(splitted_ssm_range) != 4 and module.params['ssm_range'] != 'none':
        module.fail_json(msg="Valid ssm_range values are multicast addresses "
                             "or the keyword 'none'.")

    args =  [
        'ssm_range'
    ]

    existing = invoke('get_existing', module, args)
    end_state = existing
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k in args)

    result = {}
    candidate = CustomNetworkConfig(indent=3)
    invoke('get_commands', module, existing, proposed, candidate)
    response = load_config(module, candidate)
    result.update(response)

    if module._verbosity > 0:
        end_state = invoke('get_existing', module, args)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed

    if WARNINGS:
        result['warnings'] = WARNINGS

    module.exit_json(**result)


if __name__ == '__main__':
    main()

