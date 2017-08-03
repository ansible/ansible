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
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"enforce_rtr_alert": true, "flush_routes": true}
existing:
    description: k/v pairs of existing IGMP configuration
    returned: verbose mode
    type: dict
    sample: {"enforce_rtr_alert": true, "flush_routes": false}
end_state:
    description: k/v pairs of IGMP configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"enforce_rtr_alert": true, "flush_routes": true}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["ip igmp flush-routes"]
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
    'flush_routes': 'ip igmp flush-routes',
    'enforce_rtr_alert': 'ip igmp enforce-router-alert'
}


def get_value(arg, config):
    REGEX = re.compile(r'{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
    value = False
    try:
        if REGEX.search(config):
            value = True
    except TypeError:
        value = False
    return value


def get_existing(module, args):
    existing = {}
    config = str(get_config(module))

    for arg in args:
        existing[arg] = get_value(arg, config)
    return existing


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_commands(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)
    if module.params['state'] == 'default':
        for key, value in proposed_commands.items():
            if existing_commands.get(key):
                commands.append('no {0}'.format(key))
    else:
        for key, value in proposed_commands.items():
            if value is True:
                commands.append(key)
            else:
                if existing_commands.get(key):
                    commands.append('no {0}'.format(key))

    if module.params['restart']:
        commands.append('restart igmp')

    if commands:
        parents = []
        candidate.add(commands, parents=parents)


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


    state = module.params['state']
    restart = module.params['restart']

    if (state == 'default' and (module.params['flush_routes'] is not None or
            module.params['enforce_rtr_alert'] is not None)):
        module.fail_json(msg='When state=default other params have no effect.')

    args =  [
        "flush_routes",
        "enforce_rtr_alert",
    ]

    existing = invoke('get_existing', module, args)
    end_state = existing

    proposed = dict((k, v) for k, v in module.params.items()
                if v is not None and k in args)

    proposed_args = proposed.copy()
    if state == 'default':
        proposed_args = dict((k, False) for k in args)

    result = {}
    if (state == 'present' or (state == 'default' and
            True in existing.values()) or restart):
        candidate = CustomNetworkConfig(indent=3)
        invoke('get_commands', module, existing, proposed_args, candidate)
        response = load_config(module, candidate)
        result.update(response)

    else:
        result['updates'] = []

    if restart:
        proposed['restart'] = restart
    result['connected'] = module.connected
    if module._verbosity > 0:
        end_state = invoke('get_existing', module, args)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed

    result['warnings'] = warnings

    module.exit_json(**result)


if __name__ == '__main__':
    main()

