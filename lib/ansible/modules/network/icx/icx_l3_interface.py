#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: icx_l3_interface
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Manage Layer-3 interfaces on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of Layer-3 interfaces
    on ICX network devices.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  name:
    description:
      - Name of the Layer-3 interface to be configured eg. GigabitEthernet0/2, ve 10, ethernet 1/1/1
    type: str
  ipv4:
    description:
      - IPv4 address to be set for the Layer-3 interface mentioned in I(name) option.
        The address format is <ipv4 address>/<mask>, the mask is number
        in range 0-32 eg. 192.168.0.1/24
    type: str
  ipv6:
    description:
      - IPv6 address to be set for the Layer-3 interface mentioned in I(name) option.
        The address format is <ipv6 address>/<mask>, the mask is number
        in range 0-128 eg. fd5d:12c9:2201:1::1/64.
    type: str
  mode:
    description:
      - Specifies if ipv4 address should be dynamic/advertise to ospf/not advertise to ospf.
        This should be specified only if ipv4 address is configured and if it is not secondary IP address.
    choices: ['dynamic', 'ospf-ignore', 'ospf-passive']
    type: str
  replace:
    description:
      - Replaces the configured primary IP address on the interface.
    choices: ['yes', 'no']
    type: str
  secondary:
    description:
      - Specifies that the configured address is a secondary IP address.
        If this keyword is omitted, the configured address is the primary IP address.
    choices: ['yes', 'no']
    type: str
  aggregate:
    description:
      - List of Layer-3 interfaces definitions. Each of the entry in aggregate list should
        define name of interface C(name) and a optional C(ipv4) or C(ipv6) address.
    type: list
    suboptions:
      name:
        description:
          - Name of the Layer-3 interface to be configured eg. GigabitEthernet0/2, ve 10, ethernet 1/1/1
        type: str
      ipv4:
        description:
          - IPv4 address to be set for the Layer-3 interface mentioned in I(name) option.
            The address format is <ipv4 address>/<mask>, the mask is number
            in range 0-32 eg. 192.168.0.1/24
        type: str
      ipv6:
        description:
          - IPv6 address to be set for the Layer-3 interface mentioned in I(name) option.
            The address format is <ipv6 address>/<mask>, the mask is number
            in range 0-128 eg. fd5d:12c9:2201:1::1/64.
        type: str
      mode:
        description:
          - Specifies if ipv4 address should be dynamic/advertise to ospf/not advertise to ospf.
            This should be specified only if ipv4 address is configured and if it is not secondary IP address.
        choices: ['dynamic', 'ospf-ignore', 'ospf-passive']
        type: str
      replace:
        description:
          - Replaces the configured primary IP address on the interface.
        choices: ['yes', 'no']
        type: str
      secondary:
        description:
          - Specifies that the configured address is a secondary IP address.
            If this keyword is omitted, the configured address is the primary IP address.
        choices: ['yes', 'no']
        type: str
      state:
        description:
          - State of the Layer-3 interface configuration. It indicates if the configuration should
            be present or absent on remote device.
        choices: ['present', 'absent']
        type: str
      check_running_config:
        description:
          - Check running configuration. This can be set as environment variable.
           Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
        type: bool
  state:
    description:
      - State of the Layer-3 interface configuration. It indicates if the configuration should
        be present or absent on remote device.
    default: present
    choices: ['present', 'absent']
    type: str
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
       Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
    type: bool
    default: yes
"""

EXAMPLES = """
- name: Remove ethernet 1/1/1 IPv4 and IPv6 address
  icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
    ipv6: "fd5d:12c9:2201:1::1/64"
    state: absent

- name: Replace ethernet 1/1/1 primary IPv4 address
  icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
    replace: yes
    state: absent

- name: Replace ethernet 1/1/1 dynamic IPv4 address
  icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
    mode: dynamic
    state: absent

- name: Set ethernet 1/1/1 secondary IPv4 address
  icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
    secondary: yes
    state: absent

- name: Set ethernet 1/1/1 IPv4 address
  icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24

- name: Set ethernet 1/1/1 IPv6 address
  icx_l3_interface:
    name: ethernet 1/1/1
    ipv6: "fd5d:12c9:2201:1::1/64"

- name: Set IP addresses on aggregate
  icx_l3_interface:
    aggregate:
      - { name: GigabitEthernet0/3, ipv4: 192.168.2.10/24 }
      - { name: GigabitEthernet0/3, ipv4: 192.168.3.10/24, ipv6: "fd5d:12c9:2201:1::1/64" }

- name: Remove IP addresses on aggregate
  icx_l3_interface:
    aggregate:
      - { name: GigabitEthernet0/3, ipv4: 192.168.2.10/24 }
      - { name: GigabitEthernet0/3, ipv4: 192.168.3.10/24, ipv6: "fd5d:12c9:2201:1::1/64" }
    state: absent


- name: Set the ipv4 and ipv6 of a virtual ethernet(ve)
  icx_l3_interface:
    name: ve 100
    ipv4: 192.168.0.1
    ipv6: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - interface ethernet 1/1/1
    - ip address 192.168.0.1 255.255.255.0
    - ipv6 address fd5d:12c9:2201:1::1/64
"""


import re
from copy import deepcopy
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.icx.icx import get_config, load_config
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.common.utils import is_netmask, is_masklen, to_netmask, to_masklen


def validate_ipv4(value, module):
    if value:
        address = value.split('/')
        if len(address) != 2:
            module.fail_json(msg='address format is <ipv4 address>/<mask>, got invalid format %s' % value)
        else:
            if not is_masklen(address[1]):
                module.fail_json(msg='invalid value for mask: %s, mask should be in range 0-32' % address[1])


def validate_ipv6(value, module):
    if value:
        address = value.split('/')
        if len(address) != 2:
            module.fail_json(msg='address format is <ipv6 address>/<mask>, got invalid format %s' % value)
        else:
            if not 0 <= int(address[1]) <= 128:
                module.fail_json(msg='invalid value for mask: %s, mask should be in range 0-128' % address[1])


def validate_param_values(module, obj, param=None):
    if param is None:
        param = module.params
    for key in obj:
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(param.get(key), module)


def map_params_to_obj(module):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            validate_param_values(module, item, item)
            obj.append(item.copy())
    else:
        obj.append({
            'name': module.params['name'],
            'ipv4': module.params['ipv4'],
            'ipv6': module.params['ipv6'],
            'state': module.params['state'],
            'replace': module.params['replace'],
            'mode': module.params['mode'],
            'secondary': module.params['secondary'],
        })

        validate_param_values(module, obj)

    return obj


def parse_config_argument(configobj, name, arg=None):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)

    values = []
    matches = re.finditer(r'%s (.+)$' % arg, cfg, re.M)
    for match in matches:
        match_str = match.group(1).strip()
        if arg == 'ipv6 address':
            values.append(match_str)
        else:
            values = match_str
            break

    return values or None


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def map_config_to_obj(module):
    compare = module.params['check_running_config']
    config = get_config(module, flags=['| begin interface'], compare=compare)
    configobj = NetworkConfig(indent=1, contents=config)

    match = re.findall(r'^interface (\S+ \S+)', config, re.M)
    if not match:
        return list()

    instances = list()

    for item in set(match):
        ipv4 = parse_config_argument(configobj, item, 'ip address')
        if ipv4:
            address = ipv4.strip().split(' ')
            if len(address) == 2 and is_netmask(address[1]):
                ipv4 = '{0}/{1}'.format(address[0], to_text(to_masklen(address[1])))
        obj = {
            'name': item,
            'ipv4': ipv4,
            'ipv6': parse_config_argument(configobj, item, 'ipv6 address'),
            'state': 'present'
        }
        instances.append(obj)

    return instances


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    for w in want:
        name = w['name']
        ipv4 = w['ipv4']
        ipv6 = w['ipv6']
        state = w['state']
        if 'replace' in w:
            replace = w['replace'] == 'yes'
        else:
            replace = False
        if w['mode'] is not None:
            mode = ' ' + w['mode']
        else:
            mode = ''
        if w['secondary'] is not None:
            secondary = w['secondary'] == 'yes'
        else:
            secondary = False

        interface = 'interface ' + name
        commands.append(interface)

        obj_in_have = search_obj_in_list(name, have)
        if state == 'absent' and have == []:
            if ipv4:
                address = ipv4.split('/')
                if len(address) == 2:
                    ipv4 = '{addr} {mask}'.format(addr=address[0], mask=to_netmask(address[1]))
                commands.append('no ip address {ip}'.format(ip=ipv4))
            if ipv6:
                commands.append('no ipv6 address {ip}'.format(ip=ipv6))

        elif state == 'absent' and obj_in_have:
            if obj_in_have['ipv4']:
                if ipv4:
                    address = ipv4.split('/')
                    if len(address) == 2:
                        ipv4 = '{addr} {mask}'.format(addr=address[0], mask=to_netmask(address[1]))
                    commands.append('no ip address {ip}'.format(ip=ipv4))
            if obj_in_have['ipv6']:
                if ipv6:
                    commands.append('no ipv6 address {ip}'.format(ip=ipv6))

        elif state == 'present':
            if ipv4:
                if obj_in_have is None or obj_in_have.get('ipv4') is None or ipv4 != obj_in_have['ipv4']:
                    address = ipv4.split('/')
                    if len(address) == 2:
                        ipv4 = '{0} {1}'.format(address[0], to_netmask(address[1]))
                    commands.append('ip address %s%s%s%s' % (format(ipv4), mode, ' replace' if (replace) else '', ' secondary' if (secondary) else ''))

            if ipv6:
                if obj_in_have is None or obj_in_have.get('ipv6') is None or ipv6.lower() not in [addr.lower() for addr in obj_in_have['ipv6']]:
                    commands.append('ipv6 address {ip}'.format(ip=ipv6))

        if commands[-1] == interface:
            commands.pop(-1)
        else:
            commands.append("exit")

    return commands


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        ipv4=dict(),
        ipv6=dict(),
        replace=dict(choices=['yes', 'no']),
        mode=dict(choices=['dynamic', 'ospf-ignore', 'ospf-passive']),
        secondary=dict(choices=['yes', 'no']),
        check_running_config=dict(default=True, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG'])),
        state=dict(default='present',
                   choices=['present', 'absent']),
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec)
    )

    argument_spec.update(element_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate'], ['secondary', 'replace'], ['secondary', 'mode']]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}
    exec_command(module, 'skip')
    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)

    if commands:
        if not module.check_mode:
            resp = load_config(module, commands)
            warnings.extend((out for out in resp if out))

        result['changed'] = True

    if warnings:
        result['warnings'] = warnings

    result['commands'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
