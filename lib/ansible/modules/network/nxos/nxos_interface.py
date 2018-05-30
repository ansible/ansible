#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: nxos_interface
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manages physical attributes of interfaces.
description:
  - Manages physical attributes of interfaces of NX-OS switches.
author:
  - Jason Edelman (@jedelman8)
  - Trishna Guha (@trishnaguha)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - This module is also used to create logical interfaces such as
    svis and loopbacks.
  - Be cautious of platform specific idiosyncrasies. For example,
    when you default a loopback interface, the admin state toggles
    on certain versions of NX-OS.
  - The M(nxos_overlay_global) C(anycast_gateway_mac) attribute must be
    set before setting the C(fabric_forwarding_anycast_gateway) property.
options:
  name:
    description:
      - Full name of interface, i.e. Ethernet1/1, port-channel10.
    required: true
    aliases: [interface]
  interface_type:
    description:
      - Interface type to be unconfigured from the device.
    choices: ['loopback', 'portchannel', 'svi', 'nve']
    version_added: 2.2
  speed:
    description:
      - Interface link speed. Applicable for ethernet interface only.
    version_added: 2.5
  admin_state:
    description:
      - Administrative state of the interface.
    default: up
    choices: ['up','down']
  description:
    description:
      - Interface description.
  mode:
    description:
      - Manage Layer 2 or Layer 3 state of the interface.
        This option is supported for ethernet and portchannel interface.
        Applicable for ethernet and portchannel interface only.
    choices: ['layer2','layer3']
  mtu:
    description:
      - MTU for a specific interface. Must be an even number between 576 and 9216.
        Applicable for ethernet interface only.
    version_added: 2.5
  ip_forward:
    description:
      - Enable/Disable ip forward feature on SVIs.
    choices: ['enable','disable']
    version_added: 2.2
  fabric_forwarding_anycast_gateway:
    description:
      - Associate SVI with anycast gateway under VLAN configuration mode.
        Applicable for SVI interface only.
    type: bool
    version_added: 2.2
  duplex:
    description:
      - Interface link status. Applicable for ethernet interface only.
    default: auto
    choices: ['full', 'half', 'auto']
    version_added: 2.5
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
    version_added: 2.5
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
    version_added: 2.5
  neighbors:
    description:
      - Check the operational state of given interface C(name) for LLDP neighbor.
      - The following suboptions are available. This is state check parameter only.
    suboptions:
        host:
          description:
            - "LLDP neighbor host for given interface C(name)."
        port:
          description:
            - "LLDP neighbor port to which given interface C(name) is connected."
    version_added: 2.5
  aggregate:
    description: List of Interfaces definitions.
    version_added: 2.5
  state:
    description:
      - Specify desired state of the resource.
    default: present
    choices: ['present','absent','default']
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state arguments.
    default: 10
"""

EXAMPLES = """
- name: Ensure an interface is a Layer 3 port and that it has the proper description
  nxos_interface:
    name: Ethernet1/1
    description: 'Configured by Ansible'
    mode: layer3

- name: Admin down an interface
  nxos_interface:
    name: Ethernet2/1
    admin_state: down

- name: Remove all loopback interfaces
  nxos_interface:
    name: loopback
    state: absent

- name: Remove all logical interfaces
  nxos_interface:
    interface_type: "{{ item }} "
    state: absent
  loop:
    - loopback
    - portchannel
    - svi
    - nve

- name: Admin up all loopback interfaces
  nxos_interface:
    name: loopback 0-1023
    admin_state: up

- name: Admin down all loopback interfaces
  nxos_interface:
    name: looback 0-1023
    admin_state: down

- name: Check neighbors intent arguments
  nxos_interface:
    name: Ethernet2/3
    neighbors:
    - port: Ethernet2/3
      host: abc.mycompany.com

- name: Add interface using aggregate
  nxos_interface:
    aggregate:
    - { name: Ethernet0/1, mtu: 256, description: test-interface-1 }
    - { name: Ethernet0/2, mtu: 516, description: test-interface-2 }
    duplex: full
    speed: 100
    state: present

- name: Delete interface using aggregate
  nxos_interface:
    aggregate:
    - name: Loopback9
    - name: Loopback10
    state: absent

- name: Check intent arguments
  nxos_interface:
    name: Ethernet0/2
    state: up
    tx_rate: ge(0)
    rx_rate: le(0)
"""

RETURN = """
commands:
    description: command list sent to the device
    returned: always
    type: list
    sample:
      - interface Ethernet2/3
      - mtu 1500
      - speed 10
"""

import re
import time

from copy import deepcopy

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, normalize_interface
from ansible.module_utils.network.nxos.nxos import get_interface_type
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import conditional, remove_default_spec


def execute_show_command(command, module):
    if 'show run' not in command:
        output = 'json'
    else:
        output = 'text'
    cmds = [{
        'command': command,
        'output': output,
    }]
    body = run_commands(module, cmds, check_rc=False)
    if body and "Invalid" in body[0]:
        return []
    else:
        return body


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def get_interfaces_dict(module):
    """Gets all active interfaces on a given switch
    """
    try:
        body = execute_show_command('show interface', module)[0]
    except IndexError:
        return {}

    interfaces = {
        'ethernet': [],
        'svi': [],
        'loopback': [],
        'management': [],
        'portchannel': [],
        'nve': [],
        'unknown': []
    }

    if body:
        interface_list = body['TABLE_interface']['ROW_interface']
        for index in interface_list:
            intf = index['interface']
            intf_type = get_interface_type(intf)
            interfaces[intf_type].append(intf)

    return interfaces


def get_vlan_interface_attributes(name, intf_type, module):
    """ Returns dictionary that has two k/v pairs:
        admin_state & description if not an svi, returns None
    """
    command = 'show run interface {0} all'.format(name)
    try:
        body = execute_show_command(command, module)[0]
    except (IndexError, TypeError):
        return None
    if body:
        command_list = body.split('\n')
        desc = None
        admin_state = 'down'
        for each in command_list:
            if 'description' in each:
                desc = each.lstrip().split("description")[1].lstrip()
            elif 'no shutdown' in each:
                admin_state = 'up'
        return dict(description=desc, admin_state=admin_state)
    else:
        return None


def get_interface_type_removed_cmds(interfaces):
    commands = []

    for interface in interfaces:
        if interface != 'Vlan1':
            commands.append('no interface {0}'.format(interface))

    return commands


def get_admin_state(admin_state):
    command = ''
    if admin_state == 'up':
        command = 'no shutdown'
    elif admin_state == 'down':
        command = 'shutdown'
    return command


def is_default_interface(name, module):
    """Checks to see if interface exists and if it is a default config
    """
    command = 'show run interface {0}'.format(name)

    try:
        body = execute_show_command(command, module)[0]
    except (IndexError, TypeError) as e:
        body = ''

    if body:
        raw_list = body.split('\n')
        found = False
        for line in raw_list:
            if line.startswith('interface'):
                found = True
            if found and line and not line.startswith('interface'):
                return False
        return True

    else:
        return 'DNE'


def add_command_to_interface(interface, cmd, commands):
    if interface not in commands:
        commands.append(interface)
    commands.append(cmd)


def map_obj_to_commands(updates, module):
    commands = list()
    commands2 = list()
    want, have = updates

    args = ('speed', 'description', 'duplex', 'mtu')
    for w in want:
        name = w['name']
        mode = w['mode']
        ip_forward = w['ip_forward']
        fabric_forwarding_anycast_gateway = w['fabric_forwarding_anycast_gateway']
        admin_state = w['admin_state']
        state = w['state']
        interface_type = w['interface_type']
        del w['state']
        if name:
            w['interface_type'] = None

        if interface_type:
            obj_in_have = {}
            if state in ('present', 'default'):
                module.fail_json(msg='The interface_type param can be used only with state absent.')
        else:
            obj_in_have = search_obj_in_list(name, have)
            is_default = is_default_interface(name, module)

        if name:
            interface = 'interface ' + name

        if state == 'absent':
            if obj_in_have:
                commands.append('no interface {0}'.format(name))
            elif interface_type and not obj_in_have:
                intfs = get_interfaces_dict(module)[interface_type]
                cmds = get_interface_type_removed_cmds(intfs)
                commands.extend(cmds)

        elif state == 'present':
            if obj_in_have:
                # Don't run switchport command for loopback and svi interfaces
                if get_interface_type(name) in ('ethernet', 'portchannel'):
                    if mode == 'layer2' and mode != obj_in_have.get('mode'):
                        add_command_to_interface(interface, 'switchport', commands)
                    elif mode == 'layer3' and mode != obj_in_have.get('mode'):
                        add_command_to_interface(interface, 'no switchport', commands)

                if admin_state == 'up' and admin_state != obj_in_have.get('admin_state'):
                    add_command_to_interface(interface, 'no shutdown', commands)
                elif admin_state == 'down' and admin_state != obj_in_have.get('admin_state'):
                    add_command_to_interface(interface, 'shutdown', commands)

                if ip_forward == 'enable' and ip_forward != obj_in_have.get('ip_forward'):
                    add_command_to_interface(interface, 'ip forward', commands)
                elif ip_forward == 'disable' and ip_forward != obj_in_have.get('ip forward'):
                    add_command_to_interface(interface, 'no ip forward', commands)

                if (fabric_forwarding_anycast_gateway is True and
                        obj_in_have.get('fabric_forwarding_anycast_gateway') is False):
                    add_command_to_interface(interface, 'fabric forwarding mode anycast-gateway', commands)

                elif (fabric_forwarding_anycast_gateway is False and
                        obj_in_have.get('fabric_forwarding_anycast_gateway') is True):
                    add_command_to_interface(interface, 'no fabric forwarding mode anycast-gateway', commands)

                for item in args:
                    candidate = w.get(item)
                    if candidate and candidate != obj_in_have.get(item):
                        cmd = item + ' ' + str(candidate)
                        add_command_to_interface(interface, cmd, commands)

                if name and get_interface_type(name) == 'ethernet':
                    if mode != obj_in_have.get('mode'):
                        admin_state = w.get('admin_state') or obj_in_have.get('admin_state')
                        if admin_state:
                            c1 = 'interface {0}'.format(normalize_interface(w['name']))
                            c2 = get_admin_state(admin_state)
                            commands2.append(c1)
                            commands2.append(c2)

            else:
                commands.append(interface)
                # Don't run switchport command for loopback and svi interfaces
                if get_interface_type(name) in ('ethernet', 'portchannel'):
                    if mode == 'layer2':
                        commands.append('switchport')
                    elif mode == 'layer3':
                        commands.append('no switchport')

                if admin_state == 'up':
                    commands.append('no shutdown')
                elif admin_state == 'down':
                    commands.append('shutdown')

                if ip_forward == 'enable':
                    commands.append('ip forward')
                elif ip_forward == 'disable':
                    commands.append('no ip forward')

                if fabric_forwarding_anycast_gateway is True:
                    commands.append('fabric forwarding mode anycast-gateway')

                elif fabric_forwarding_anycast_gateway is False:
                    commands.append('no fabric forwarding mode anycast-gateway')

                for item in args:
                    candidate = w.get(item)
                    if candidate:
                        commands.append(item + ' ' + str(candidate))

        elif state == 'default':
            if is_default is False:
                commands.append('default interface {0}'.format(name))
            elif is_default == 'DNE':
                module.exit_json(msg='interface you are trying to default does not exist')

    return commands, commands2


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            name = d['name']
            d['name'] = normalize_interface(name)
            obj.append(d)

    else:
        obj.append({
            'name': normalize_interface(module.params['name']),
            'description': module.params['description'],
            'speed': module.params['speed'],
            'mode': module.params['mode'],
            'mtu': module.params['mtu'],
            'duplex': module.params['duplex'],
            'ip_forward': module.params['ip_forward'],
            'fabric_forwarding_anycast_gateway': module.params['fabric_forwarding_anycast_gateway'],
            'admin_state': module.params['admin_state'],
            'state': module.params['state'],
            'interface_type': module.params['interface_type'],
            'tx_rate': module.params['tx_rate'],
            'rx_rate': module.params['rx_rate'],
            'neighbors': module.params['neighbors']
        })

    return obj


def map_config_to_obj(want, module):
    objs = list()

    for w in want:
        obj = dict(name=None, description=None, admin_state=None, speed=None,
                   mtu=None, mode=None, duplex=None, interface_type=None,
                   ip_forward=None, fabric_forwarding_anycast_gateway=None)

        if not w['name']:
            return obj

        command = 'show interface {0}'.format(w['name'])
        try:
            body = execute_show_command(command, module)[0]
        except IndexError:
            return list()
        if body:
            try:
                interface_table = body['TABLE_interface']['ROW_interface']
            except (KeyError, TypeError):
                return list()

            if interface_table:
                if interface_table.get('eth_mode') == 'fex-fabric':
                    module.fail_json(msg='nxos_interface does not support interfaces with mode "fex-fabric"')

                intf_type = get_interface_type(w['name'])

                if intf_type in ['portchannel', 'ethernet']:
                    if not interface_table.get('eth_mode'):
                        obj['mode'] = 'layer3'

                if intf_type == 'ethernet':
                    obj['name'] = normalize_interface(interface_table.get('interface'))
                    obj['admin_state'] = interface_table.get('admin_state')
                    obj['description'] = interface_table.get('desc')
                    obj['mtu'] = interface_table.get('eth_mtu')
                    obj['duplex'] = interface_table.get('eth_duplex')
                    speed = interface_table.get('eth_speed')
                    mode = interface_table.get('eth_mode')
                    if mode in ('access', 'trunk'):
                        obj['mode'] = 'layer2'
                    elif mode in ('routed', 'layer3'):
                        obj['mode'] = 'layer3'

                    command = 'show run interface {0}'.format(obj['name'])
                    body = execute_show_command(command, module)[0]

                    speed_match = re.search(r'speed (\d+)', body)
                    if speed_match is None:
                        obj['speed'] = 'auto'
                    else:
                        obj['speed'] = speed_match.group(1)

                    duplex_match = re.search(r'duplex (\S+)', body)
                    if duplex_match is None:
                        obj['duplex'] = 'auto'
                    else:
                        obj['duplex'] = duplex_match.group(1)

                    if 'ip forward' in body:
                        obj['ip_forward'] = 'enable'
                    else:
                        obj['ip_forward'] = 'disable'

                elif intf_type == 'svi':
                    obj['name'] = normalize_interface(interface_table.get('interface'))
                    attributes = get_vlan_interface_attributes(obj['name'], intf_type, module)
                    obj['admin_state'] = str(attributes.get('admin_state',
                                                            'nxapibug'))
                    obj['description'] = str(attributes.get('description',
                                                            'nxapi_bug'))

                    command = 'show run interface {0}'.format(obj['name'])
                    body = execute_show_command(command, module)[0]
                    if 'ip forward' in body:
                        obj['ip_forward'] = 'enable'
                    else:
                        obj['ip_forward'] = 'disable'
                    if 'fabric forwarding mode anycast-gateway' in body:
                        obj['fabric_forwarding_anycast_gateway'] = True
                    else:
                        obj['fabric_forwarding_anycast_gateway'] = False

                elif intf_type in ('loopback', 'management', 'nve'):
                    obj['name'] = normalize_interface(interface_table.get('interface'))
                    obj['admin_state'] = interface_table.get('admin_state')
                    obj['description'] = interface_table.get('desc')

                elif intf_type == 'portchannel':
                    obj['name'] = normalize_interface(interface_table.get('interface'))
                    obj['admin_state'] = interface_table.get('admin_state')
                    obj['description'] = interface_table.get('desc')
                    obj['mode'] = interface_table.get('eth_mode')

        objs.append(obj)

    return objs


def check_declarative_intent_params(module, want):
    failed_conditions = []
    have_neighbors = None
    for w in want:
        want_tx_rate = w.get('tx_rate')
        want_rx_rate = w.get('rx_rate')
        want_neighbors = w.get('neighbors')

        time.sleep(module.params['delay'])

        if w['interface_type']:
            return

        cmd = [{'command': 'show interface {0}'.format(w['name']), 'output': 'text'}]

        try:
            out = run_commands(module, cmd, check_rc=False)[0]
        except (AttributeError, IndexError, TypeError):
            out = ''

        if want_tx_rate:
            match = re.search(r'output rate (\d+)', out, re.M)
            have_tx_rate = None

            if match:
                have_tx_rate = match.group(1)

            if have_tx_rate is None or not conditional(want_tx_rate, have_tx_rate.strip(), cast=int):
                failed_conditions.append('tx_rate ' + want_tx_rate)

        if want_rx_rate:
            match = re.search(r'input rate (\d+)', out, re.M)
            have_rx_rate = None

            if match:
                have_rx_rate = match.group(1)

            if have_rx_rate is None or not conditional(want_rx_rate, have_rx_rate.strip(), cast=int):
                failed_conditions.append('rx_rate ' + want_rx_rate)

        if want_neighbors:
            have_host = []
            have_port = []
            if have_neighbors is None:
                cmd = [{'command': 'show lldp neighbors interface {0} detail'.format(w['name']), 'output': 'text'}]
                output = run_commands(module, cmd, check_rc=False)
                if output:
                    have_neighbors = output[0]
                else:
                    have_neighbors = ''
                if have_neighbors and 'Total entries displayed: 0' not in have_neighbors:
                    for line in have_neighbors.strip().split('\n'):
                        if line.startswith('Port Description'):
                            have_port.append(line.split(': ')[1])
                        if line.startswith('System Name'):
                            have_host.append(line.split(': ')[1])

            for item in want_neighbors:
                host = item.get('host')
                port = item.get('port')
                if host and host not in have_host:
                    failed_conditions.append('host ' + host)
                if port and port not in have_port:
                    failed_conditions.append('port ' + port)

    return failed_conditions


def main():
    """ main entry point for module execution
    """
    neighbors_spec = dict(
        host=dict(),
        port=dict()
    )

    element_spec = dict(
        name=dict(aliases=['interface']),
        admin_state=dict(default='up', choices=['up', 'down']),
        description=dict(),
        speed=dict(),
        mode=dict(choices=['layer2', 'layer3']),
        mtu=dict(),
        duplex=dict(choices=['full', 'half', 'auto']),
        interface_type=dict(choices=['loopback', 'portchannel', 'svi', 'nve']),
        ip_forward=dict(choices=['enable', 'disable']),
        fabric_forwarding_anycast_gateway=dict(type='bool'),
        tx_rate=dict(),
        rx_rate=dict(),
        neighbors=dict(type='list', elements='dict', options=neighbors_spec),
        delay=dict(default=10, type='int'),
        state=dict(choices=['absent', 'present', 'default'], default='present')
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec,
                       mutually_exclusive=[['name', 'interface_type']])
    )

    argument_spec.update(element_spec)
    argument_spec.update(nxos_argument_spec)

    required_one_of = [['name', 'aggregate', 'interface_type']]
    mutually_exclusive = [['name', 'aggregate'],
                          ['name', 'interface_type']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)
    warnings = list()

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(want, module)

    commands = []
    commands1, commands2 = map_obj_to_commands((want, have), module)
    commands.extend(commands1)

    if commands:
        if not module.check_mode:
            load_config(module, commands)
            result['changed'] = True
            # if the mode changes from L2 to L3, the admin state
            # seems to change after the API call, so adding a second API
            # call to ensure it's in the desired state.
            if commands2:
                load_config(module, commands2)
                commands.extend(commands2)
            commands = [cmd for cmd in commands if cmd != 'configure']
    result['commands'] = commands

    if result['changed']:
        failed_conditions = check_declarative_intent_params(module, want)

        if failed_conditions:
            msg = 'One or more conditional statements have not been satisfied'
            module.fail_json(msg=msg, failed_conditions=failed_conditions)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
