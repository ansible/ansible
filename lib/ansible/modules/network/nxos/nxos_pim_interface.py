#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = r'''
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
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
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
    type: str
    required: true
  sparse:
    description:
      - Enable/disable sparse-mode on the interface.
    type: bool
    default: no
  dr_prio:
    description:
      - Configures priority for PIM DR election on interface.
    type: str
  hello_auth_key:
    description:
      - Authentication for hellos on this interface.
    type: str
  hello_interval:
    description:
      - Hello interval in milliseconds for this interface.
    type: int
  jp_policy_out:
    description:
      - Policy for join-prune messages (outbound).
    type: str
  jp_policy_in:
    description:
      - Policy for join-prune messages (inbound).
    type: str
  jp_type_out:
    description:
      - Type of policy mapped to C(jp_policy_out).
    type: str
    choices: [ prefix, routemap ]
  jp_type_in:
    description:
      - Type of policy mapped to C(jp_policy_in).
    type: str
    choices: [ prefix, routemap ]
  border:
    description:
      - Configures interface to be a boundary of a PIM domain.
    type: bool
    default: no
  neighbor_policy:
    description:
      - Configures a neighbor policy for filtering adjacencies.
    type: str
  neighbor_type:
    description:
      - Type of policy mapped to neighbor_policy.
    type: str
    choices: [ prefix, routemap ]
  state:
    description:
      - Manages desired state of the resource.
    type: str
    choices: [ present, default ]
    default: present
'''
EXAMPLES = r'''
- name: Ensure PIM is not running on the interface
  nxos_pim_interface:
    interface: eth1/33
    state: absent

- name: Ensure the interface has pim-sm enabled with the appropriate priority and hello interval
  nxos_pim_interface:
    interface: eth1/33
    dr_prio: 10
    hello_interval: 40
    state: present

- name: Ensure join-prune policies exist
  nxos_pim_interface:
    interface: eth1/33
    jp_policy_in: JPIN
    jp_policy_out: JPOUT
    jp_type_in: routemap
    jp_type_out: routemap

- name: Ensure defaults are in place
  nxos_pim_interface:
    interface: eth1/33
    state: default
'''

RETURN = r'''
commands:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface eth1/33", "ip pim neighbor-policy test",
            "ip pim neighbor-policy test"]
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.network.nxos.nxos import get_interface_type
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

PARAM_TO_DEFAULT_KEYMAP = {
    'dr_prio': '1',
    'hello_interval': '30000',
    'sparse': False,
    'border': False,
    'hello_auth_key': False,
}


def execute_show_command(command, module, text=False):
    if text:
        cmds = [{
            'command': command,
            'output': 'text'
        }]
    else:
        cmds = [{
            'command': command,
            'output': 'json'
        }]

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

    return gexisting, jp_bidir, isauth


def get_interface_mode(interface, intf_type, module):
    mode = 'unknown'
    command = 'show interface {0}'.format(interface)
    body = execute_show_command(command, module)

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
    body = get_config(module, flags=['interface {0}'.format(interface)])

    pim_interface['neighbor_type'] = None
    pim_interface['neighbor_policy'] = None
    pim_interface['jp_policy_in'] = None
    pim_interface['jp_policy_out'] = None
    pim_interface['jp_type_in'] = None
    pim_interface['jp_type_out'] = None
    pim_interface['jp_bidir'] = False
    pim_interface['isauth'] = False

    if body:
        all_lines = body.splitlines()

        for each in all_lines:
            if 'jp-policy' in each:
                policy_name = \
                    re.search(r'ip pim jp-policy(?: prefix-list)? (\S+)(?: \S+)?', each).group(1)
                if 'prefix-list' in each:
                    ptype = 'prefix'
                else:
                    ptype = 'routemap'
                if 'out' in each:
                    pim_interface['jp_policy_out'] = policy_name
                    pim_interface['jp_type_out'] = ptype
                elif 'in' in each:
                    pim_interface['jp_policy_in'] = policy_name
                    pim_interface['jp_type_in'] = ptype
                else:
                    pim_interface['jp_policy_in'] = policy_name
                    pim_interface['jp_policy_out'] = policy_name
                    pim_interface['jp_bidir'] = True
            elif 'neighbor-policy' in each:
                pim_interface['neighbor_policy'] = \
                    re.search(r'ip pim neighbor-policy(?: prefix-list)? (\S+)', each).group(1)
                if 'prefix-list' in each:
                    pim_interface['neighbor_type'] = 'prefix'
                else:
                    pim_interface['neighbor_type'] = 'routemap'
            elif 'ah-md5' in each:
                pim_interface['isauth'] = True
            elif 'sparse-mode' in each:
                pim_interface['sparse'] = True
            elif 'border' in each:
                pim_interface['border'] = True
            elif 'hello-interval' in each:
                pim_interface['hello_interval'] = \
                    re.search(r'ip pim hello-interval (\d+)', body).group(1)
            elif 'dr-priority' in each:
                pim_interface['dr_prio'] = \
                    re.search(r'ip pim dr-priority (\d+)', body).group(1)

    return pim_interface


def fix_delta(delta, existing):
    for key in list(delta):
        if key in ['dr_prio', 'hello_interval', 'sparse', 'border']:
            if delta.get(key) == PARAM_TO_DEFAULT_KEYMAP.get(key) and existing.get(key) is None:
                delta.pop(key)
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

    args = dict(dr_prio=PARAM_TO_DEFAULT_KEYMAP.get('dr_prio'),
                border=PARAM_TO_DEFAULT_KEYMAP.get('border'),
                sparse=PARAM_TO_DEFAULT_KEYMAP.get('sparse'),
                hello_interval=PARAM_TO_DEFAULT_KEYMAP.get('hello_interval'),
                hello_auth_key=PARAM_TO_DEFAULT_KEYMAP.get('hello_auth_key'))

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
        interface=dict(type='str', required=True),
        sparse=dict(type='bool', default=False),
        dr_prio=dict(type='str'),
        hello_auth_key=dict(type='str', no_log=True),
        hello_interval=dict(type='int'),
        jp_policy_out=dict(type='str'),
        jp_policy_in=dict(type='str'),
        jp_type_out=dict(type='str', choices=['prefix', 'routemap']),
        jp_type_in=dict(type='str', choices=['prefix', 'routemap']),
        border=dict(type='bool', default=False),
        neighbor_policy=dict(type='str'),
        neighbor_type=dict(type='str', choices=['prefix', 'routemap']),
        state=dict(type='str', default='present', choices=['absent', 'default', 'present']),
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
    elif state == 'default' or state == 'absent':
        defaults = config_pim_interface_defaults(existing, jp_bidir, isauth)
        if defaults:
            commands.append(defaults)

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
