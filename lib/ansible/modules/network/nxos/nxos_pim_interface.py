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
module: nxos_pim_interface
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages PIM interface configuration.
description:
  - Manages PIM interface configuration settings.
author:
  - Jason Edelman (@jedelman8)
notes:
  - When C(state=default), supported params will be reset to a default state.
    These include C(dr_prio), C(hello_auth_key), C(hello_interval), C(jp_policy_out),
    C(jp_policy_in), C(jp_type_in), C(jp_type_out), C(border), C(neighbor_policy),
    C(neighbor_type).
  - The C(hello_auth_key) param is not idempotent.
  - C(hello_auth_key) only supports clear text passwords.
  - When C(state=absent), pim interface configuration will be set to defaults and pim-sm
    will be disabled on the interface.
  - PIM must be enabled on the device to use this module.
  - This module is for Layer 3 interfaces.
options:
  interface:
    description:
      - Full name of the interface such as Ethernet1/33.
    required: true
  sparse:
    description:
      - Enable/disable sparse-mode on the interface.
    required: false
    default: true
    choices: ['true', 'false']
  hello_auth_key:
    description:
      - Authentication for hellos on this interface.
    required: false
    default: null
  hello_interval:
    description:
      - Hello interval in milliseconds for this interface.
    required: false
    default: null
    choices: ['true', 'false']
  jp_policy_out:
    description:
      - Policy for join-prune messages (outbound).
    required: true
    default: null
  jp_policy_in:
    description:
      - Policy for join-prune messages (inbound).
    required: false
    default: null
  jp_type_out:
    description:
      - Type of policy mapped to C(jp_policy_out).
    required: false
    default: null
    choices: ['prefix', 'routemap']
  jp_type_in:
    description:
      - Type of policy mapped to C(jp_policy_in).
    required: false
    default: null
    choices: ['prefix', 'routemap']
  border:
    description:
      - Configures interface to be a boundary of a PIM domain.
    required: false
    default: null
    choices: ['true', 'false']
  neighbor_policy:
    description:
      - Configures a neighbor policy for filtering adjacencies.
    required: false
    default: null
  neighbor_type:
    description:
      - Type of policy mapped to neighbor_policy.
    required: false
    default: null
    choices: ['prefix', 'routemap']
  state:
    description:
      - Manages desired state of the resource.
    required: false
    default: present
    choices: ['present', 'default']
'''
EXAMPLES = '''
# ensure PIM is not running on the interface
- nxos_pim_interface:
    interface: eth1/33
    state: absent

# ensure the interface has pim-sm enabled with the appropriate priority and hello interval
- nxos_pim_interface:
    interface: eth1/33
    dr_prio: 10
    hello_interval: 40
    state: present

# ensure join-prune policies exist
- nxos_pim_interface:
    interface: eth1/33
    jp_policy_in: JPIN
    jp_policy_out: JPOUT
    jp_type_in: routemap
    jp_type_out: routemap

# ensure defaults are in place
- nxos_pim_interface:
    interface: eth1/33
    state: default
'''

RETURN = '''
commands:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface eth1/33", "ip pim neighbor-policy test",
            "ip pim neighbor-policy test"]
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.six import string_types


PARAM_TO_COMMAND_KEYMAP = {
    'interface': '',
    'sparse': 'ip pim sparse-mode',
    'dr_prio': 'ip pim dr-priority {0}',
    'hello_interval': 'ip pim hello-interval {0}',
    'hello_auth_key': 'ip pim hello-authentication ah-md5 {0}',
    'border': 'ip pim border',
    'jp_policy_out': 'ip pim jp-policy prefix-list {0} out',
    'jp_policy_in': 'ip pim jp-policy prefix-list {0} in',
    'jp_type_in': '',
    'jp_type_out': '',
    'neighbor_policy': 'ip pim neighbor-policy prefix-list {0}',
    'neighbor_type': '',
}


def execute_show_command(command, module, text=False):
    if text is False:
        command += ' | json'

    cmds = [command]
    return run_commands(module, cmds)


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def local_existing(gexisting):
    jp_bidir = False
    isauth = False
    if gexisting:
        jp_bidir = gexisting.get('jp_bidir')
        isauth = gexisting.get('isauth')
        if jp_bidir and isauth:
            gexisting.pop('jp_bidir')
            gexisting.pop('isauth')
        gexisting['sparse'] = True

    return gexisting, jp_bidir, isauth


def get_interface_type(interface):
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    else:
        return 'unknown'


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0} | json'.format(interface)
    mode = 'unknown'
    body = run_commands(module, [command])

    try:
        interface_table = body[0]['TABLE_interface']['ROW_interface']
    except (KeyError, AttributeError, IndexError):
        return mode

    if intf_type in ['ethernet', 'portchannel']:
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode in ['access', 'trunk']:
            mode = 'layer2'
        elif mode == 'routed':
            mode = 'layer3'
    elif intf_type in ['loopback', 'svi']:
        mode = 'layer3'
    return mode


def get_pim_interface(module, interface):
    pim_interface = {}
    command = 'show ip pim interface {0}'.format(interface)

    body = execute_show_command(command, module, text=True)

    if body:
        if 'not running' not in body[0]:
            body = execute_show_command(command, module)

    try:
        get_data = body[0]['TABLE_iod']['ROW_iod']

        if isinstance(get_data.get('dr-priority'), string_types):
            pim_interface['dr_prio'] = get_data.get('dr-priority')
        else:
            pim_interface['dr_prio'] = get_data.get('dr-priority')[0]

        hello_interval = get_data.get('hello-interval-sec')
        if hello_interval:
            hello_interval_msec = int(get_data.get('hello-interval-sec')) * 1000
        pim_interface['hello_interval'] = str(hello_interval_msec)
        border = get_data.get('is-border')

        if border == 'true':
            pim_interface['border'] = True
        elif border == 'false':
            pim_interface['border'] = False

        isauth = get_data.get('isauth-config')
        if isauth == 'true':
            pim_interface['isauth'] = True
        elif isauth == 'false':
            pim_interface['isauth'] = False

        pim_interface['neighbor_policy'] = get_data.get('nbr-policy-name')
        if pim_interface['neighbor_policy'] == 'none configured':
            pim_interface['neighbor_policy'] = None

        jp_in_policy = get_data.get('jp-in-policy-name')
        pim_interface['jp_policy_in'] = jp_in_policy
        if jp_in_policy == 'none configured':
            pim_interface['jp_policy_in'] = None

        if isinstance(get_data.get('jp-out-policy-name'), string_types):
            pim_interface['jp_policy_out'] = get_data.get('jp-out-policy-name')
        else:
            pim_interface['jp_policy_out'] = get_data.get(
                'jp-out-policy-name')[0]

        if pim_interface['jp_policy_out'] == 'none configured':
            pim_interface['jp_policy_out'] = None

    except (KeyError, AttributeError, TypeError, IndexError):
        return {}

    body = get_config(module, flags=['interface {0}'.format(interface)])

    jp_configs = []
    neigh = None
    if body:
        all_lines = body[0].splitlines()

        for each in all_lines:
            if 'jp-policy' in each:
                jp_configs.append(str(each.strip()))
            elif 'neighbor-policy' in each:
                neigh = str(each)

    pim_interface['neighbor_type'] = None
    neigh_type = None
    if neigh:
        if 'prefix-list' in neigh:
            neigh_type = 'prefix'
        else:
            neigh_type = 'routemap'
    pim_interface['neighbor_type'] = neigh_type

    len_existing = len(jp_configs)
    list_of_prefix_type = len([x for x in jp_configs if 'prefix-list' in x])
    jp_type_in = None
    jp_type_out = None
    jp_bidir = False
    if len_existing == 1:
        # determine type
        last_word = jp_configs[0].split(' ')[-1]
        if last_word == 'in':
            if list_of_prefix_type:
                jp_type_in = 'prefix'
            else:
                jp_type_in = 'routemap'
        elif last_word == 'out':
            if list_of_prefix_type:
                jp_type_out = 'prefix'
            else:
                jp_type_out = 'routemap'
        else:
            jp_bidir = True
            if list_of_prefix_type:
                jp_type_in = 'prefix'
                jp_type_out = 'routemap'
            else:
                jp_type_in = 'routemap'
                jp_type_out = 'routemap'
    else:
        for each in jp_configs:
            last_word = each.split(' ')[-1]
            if last_word == 'in':
                if 'prefix-list' in each:
                    jp_type_in = 'prefix'
                else:
                    jp_type_in = 'routemap'
            elif last_word == 'out':
                if 'prefix-list' in each:
                    jp_type_out = 'prefix'
                else:
                    jp_type_out = 'routemap'

    pim_interface['jp_type_in'] = jp_type_in
    pim_interface['jp_type_out'] = jp_type_out
    pim_interface['jp_bidir'] = jp_bidir

    return pim_interface


def fix_delta(delta, existing):
    if delta.get('sparse') is False and existing.get('sparse') is None:
        delta.pop('sparse')
    return delta


def config_pim_interface(delta, existing, jp_bidir, isauth):
    command = None
    commands = []

    delta = fix_delta(delta, existing)

    if jp_bidir:
        if delta.get('jp_policy_in') or delta.get('jp_policy_out'):
            if existing.get('jp_type_in') == 'prefix':
                command = 'no ip pim jp-policy prefix-list {0}'.format(existing.get('jp_policy_in'))
            else:
                command = 'no ip pim jp-policy {0}'.format(existing.get('jp_policy_in'))
            if command:
                commands.append(command)

    for k, v in delta.items():
        if k in ['dr_prio', 'hello_interval', 'hello_auth_key', 'border',
                 'sparse']:
            if v:
                command = PARAM_TO_COMMAND_KEYMAP.get(k).format(v)
            elif k == 'hello_auth_key':
                if isauth:
                    command = 'no ip pim hello-authentication ah-md5'
            else:
                command = 'no ' + PARAM_TO_COMMAND_KEYMAP.get(k).format(v)

            if command:
                commands.append(command)
        elif k in ['neighbor_policy', 'jp_policy_in', 'jp_policy_out',
                   'neighbor_type']:
            if k in ['neighbor_policy', 'neighbor_type']:
                temp = delta.get('neighbor_policy') or existing.get(
                    'neighbor_policy')
                if delta.get('neighbor_type') == 'prefix':
                    command = PARAM_TO_COMMAND_KEYMAP.get(k).format(temp)
                elif delta.get('neighbor_type') == 'routemap':
                    command = 'ip pim neighbor-policy {0}'.format(temp)
                elif existing.get('neighbor_type') == 'prefix':
                    command = PARAM_TO_COMMAND_KEYMAP.get(k).format(temp)
                elif existing.get('neighbor_type') == 'routemap':
                    command = 'ip pim neighbor-policy {0}'.format(temp)
            elif k in ['jp_policy_in', 'jp_type_in']:
                temp = delta.get('jp_policy_in') or existing.get(
                    'jp_policy_in')
                if delta.get('jp_type_in') == 'prefix':
                    command = PARAM_TO_COMMAND_KEYMAP.get(k).format(temp)
                elif delta.get('jp_type_in') == 'routemap':
                    command = 'ip pim jp-policy {0} in'.format(temp)
                elif existing.get('jp_type_in') == 'prefix':
                    command = PARAM_TO_COMMAND_KEYMAP.get(k).format(temp)
                elif existing.get('jp_type_in') == 'routemap':
                    command = 'ip pim jp-policy {0} in'.format(temp)
            elif k in ['jp_policy_out', 'jp_type_out']:
                temp = delta.get('jp_policy_out') or existing.get(
                    'jp_policy_out')
                if delta.get('jp_type_out') == 'prefix':
                    command = PARAM_TO_COMMAND_KEYMAP.get(k).format(temp)
                elif delta.get('jp_type_out') == 'routemap':
                    command = 'ip pim jp-policy {0} out'.format(temp)
                elif existing.get('jp_type_out') == 'prefix':
                    command = PARAM_TO_COMMAND_KEYMAP.get(k).format(temp)
                elif existing.get('jp_type_out') == 'routemap':
                    command = 'ip pim jp-policy {0} out'.format(temp)
            if command:
                commands.append(command)
        command = None

    return commands


def get_pim_interface_defaults():
    dr_prio = '1'
    border = False
    hello_interval = '30000'
    hello_auth_key = False

    args = dict(dr_prio=dr_prio, border=border,
                hello_interval=hello_interval,
                hello_auth_key=hello_auth_key)

    default = dict((param, value) for (param, value) in args.items()
                   if value is not None)

    return default


def default_pim_interface_policies(existing, jp_bidir):
    commands = []

    if jp_bidir:
        if existing.get('jp_policy_in') or existing.get('jp_policy_out'):
            if existing.get('jp_type_in') == 'prefix':
                command = 'no ip pim jp-policy prefix-list {0}'.format(existing.get('jp_policy_in'))
        if command:
            commands.append(command)

    elif not jp_bidir:
        command = None
        for k in existing:
            if k == 'jp_policy_in':
                if existing.get('jp_policy_in'):
                    if existing.get('jp_type_in') == 'prefix':
                        command = 'no ip pim jp-policy prefix-list {0} in'.format(
                            existing.get('jp_policy_in')
                        )
                    else:
                        command = 'no ip pim jp-policy {0} in'.format(
                            existing.get('jp_policy_in')
                        )
            elif k == 'jp_policy_out':
                if existing.get('jp_policy_out'):
                    if existing.get('jp_type_out') == 'prefix':
                        command = 'no ip pim jp-policy prefix-list {0} out'.format(
                            existing.get('jp_policy_out')
                        )
                    else:
                        command = 'no ip pim jp-policy {0} out'.format(
                            existing.get('jp_policy_out')
                        )
            if command:
                commands.append(command)
            command = None

    if existing.get('neighbor_policy'):
        command = 'no ip pim neighbor-policy'
        commands.append(command)

    return commands


def config_pim_interface_defaults(existing, jp_bidir, isauth):
    command = []

    # returns a dict
    defaults = get_pim_interface_defaults()
    delta = dict(set(defaults.items()).difference(
        existing.items()))
    if delta:
        # returns a list
        command = config_pim_interface(delta, existing,
                                       jp_bidir, isauth)
    comm = default_pim_interface_policies(existing, jp_bidir)
    if comm:
        for each in comm:
            command.append(each)

    return command


def main():
    argument_spec = dict(
        interface=dict(required=True),
        sparse=dict(type='bool', default=True),
        dr_prio=dict(type='str'),
        hello_auth_key=dict(type='str'),
        hello_interval=dict(type='int'),
        jp_policy_out=dict(type='str'),
        jp_policy_in=dict(type='str'),
        jp_type_out=dict(choices=['prefix', 'routemap']),
        jp_type_in=dict(choices=['prefix', 'routemap']),
        border=dict(type='bool'),
        neighbor_policy=dict(type='str'),
        neighbor_type=dict(choices=['prefix', 'routemap']),
        state=dict(choices=['present', 'absent', 'default'], default='present'),
    )
    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    state = module.params['state']
    interface = module.params['interface']
    jp_type_in = module.params['jp_type_in']
    jp_type_out = module.params['jp_type_out']
    jp_policy_in = module.params['jp_policy_in']
    jp_policy_out = module.params['jp_policy_out']
    neighbor_policy = module.params['neighbor_policy']
    neighbor_type = module.params['neighbor_type']
    hello_interval = module.params['hello_interval']

    intf_type = get_interface_type(interface)
    if get_interface_mode(interface, intf_type, module) == 'layer2':
        module.fail_json(msg='this module only works on Layer 3 interfaces.')

    if jp_policy_in:
        if not jp_type_in:
            module.fail_json(msg='jp_type_in required when using jp_policy_in.')
    if jp_policy_out:
        if not jp_type_out:
            module.fail_json(msg='jp_type_out required when using jp_policy_out.')
    if neighbor_policy:
        if not neighbor_type:
            module.fail_json(msg='neighbor_type required when using neighbor_policy.')

    get_existing = get_pim_interface(module, interface)
    existing, jp_bidir, isauth = local_existing(get_existing)

    args = PARAM_TO_COMMAND_KEYMAP.keys()
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k in args)

    if hello_interval:
        proposed['hello_interval'] = str(proposed['hello_interval'] * 1000)

    delta = dict(set(proposed.items()).difference(existing.items()))

    commands = []
    if state == 'present':
        if delta:
            command = config_pim_interface(delta, existing, jp_bidir, isauth)
            if command:
                commands.append(command)
    elif state == 'default':
        defaults = config_pim_interface_defaults(existing, jp_bidir, isauth)
        if defaults:
            commands.append(defaults)

    elif state == 'absent':
        if existing.get('sparse') is True:
            delta['sparse'] = False
            # defaults is a list of commands
            defaults = config_pim_interface_defaults(existing, jp_bidir, isauth)
            if defaults:
                commands.append(defaults)

            command = config_pim_interface(delta, existing, jp_bidir, isauth)
            commands.append(command)

    if commands:
        commands.insert(0, ['interface {0}'.format(interface)])

    cmds = flatten_list(commands)
    if cmds:
        results['changed'] = True
        if not module.check_mode:
            load_config(module, cmds)
        if 'configure' in cmds:
            cmds.pop(0)

    results['commands'] = cmds

    module.exit_json(**results)


if __name__ == '__main__':
    main()
