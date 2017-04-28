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
module: nxos_ospf
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages configuration of an ospf instance.
description:
    - Manages configuration of an ospf instance.
author: Gabriele Gerbino (@GGabriele)
options:
    ospf:
        description:
            - Name of the ospf instance.
        required: true
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- nxos_ospf:
    ospf: 1
    state: present
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"ospf": "1"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"ospf": ["2"]}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"ospf": ["1", "2"]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router ospf 1"]
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
    'ospf': 'router ospf'
}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(config, module):
    splitted_config = config.splitlines()
    value_list = []
    REGEX = '^router ospf\s(?P<ospf>\S+).*'
    for line in splitted_config:
        value = ''
        if 'router ospf' in line:
            try:
                match_ospf = re.match(REGEX, line, re.DOTALL)
                ospf_group = match_ospf.groupdict()
                value = ospf_group['ospf']
            except AttributeError:
                value = ''
            if value:
                value_list.append(value)

    return value_list


def get_existing(module):
    existing = {}
    config = str(get_config(module))

    value = get_value(config, module)
    if value:
        existing['ospf'] = value
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


def state_present(module, proposed, candidate):
    commands = ['router ospf {0}'.format(proposed['ospf'])]
    candidate.add(commands, parents=[])


def state_absent(module, proposed, candidate):
    commands = ['no router ospf {0}'.format(proposed['ospf'])]
    candidate.add(commands, parents=[])


def main():
    argument_spec = dict(
        ospf=dict(required=True, type='str'),
        state=dict(choices=['present', 'absent'], default='present',
                       required=False),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                        supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    state = module.params['state']
    ospf = str(module.params['ospf'])

    existing = invoke('get_existing', module)
    end_state = existing
    proposed = dict(ospf=ospf)

    if not existing:
        existing_list = []
    else:
        existing_list = existing['ospf']

    result = {}
    if (state == 'present' or (state == 'absent' and ospf in existing_list)):
        candidate = CustomNetworkConfig(indent=3)
        invoke('state_%s' % state, module, proposed, candidate)
        response = load_config(module, candidate)
        result.update(response)

    else:
        result['updates'] = []

    if module._verbosity > 0:
        end_state = invoke('get_existing', module)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed

    module.exit_json(**result)


if __name__ == '__main__':
    main()

