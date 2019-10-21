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
module: icx_vlan
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Manage VLANs on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of VLANs
    on ICX network devices.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  name:
    description:
      - Name of the VLAN.
    type: str
  vlan_id:
    description:
      - ID of the VLAN. Range 1-4094.
    required: true
    type: int
  interfaces:
    description:
      - List of ethernet ports or LAGS to be added as access(untagged) ports to the vlan.
        To add a range of ports use 'to' keyword. See the example.
    suboptions:
      name:
        description:
          - Name of the interface or lag
        type: list
      purge:
        description:
          - Purge interfaces not defined in the I(name)
        type: bool
    type: dict
  tagged:
    description:
      - List of ethernet ports or LAGS to be added as trunk(tagged) ports to the vlan.
        To add a range of ports use 'to' keyword. See the example.
    suboptions:
      name:
        description:
          - Name of the interface or lag
        type: list
      purge:
        description:
          - Purge interfaces not defined in the I(name)
        type: bool
    type: dict
  ip_dhcp_snooping:
    description:
      - Enables DHCP snooping on a VLAN.
    type: bool
  ip_arp_inspection:
    description:
      - Enables dynamic ARP inspection on a VLAN.
    type: bool
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for given vlan C(name)
        for associated interfaces. If the value in the C(associated_interfaces) does not match with
        the operational state of vlan interfaces on device it will result in failure.
    type: list
  associated_tagged:
    description:
      - This is a intent option and checks the operational state of  given vlan C(name)
        for associated tagged ports and lags. If the value in the C(associated_tagged) does not match with
        the operational state of vlan interfaces on device it will result in failure.
    type: list
  delay:
    description:
      - Delay the play should wait to check for declarative intent params values.
    default: 10
    type: int
  stp:
    description:
      - Enable spanning-tree 802-1w/rstp for this vlan.
    suboptions:
      type:
        description:
          - Specify the type of spanning-tree
        type: str
        default: 802-1w
        choices: ['802-1w','rstp']
      priority:
        description:
          - Configures the priority of the bridge. The value ranges from
            0 through 65535. A lower numerical value means the bridge has
            a higher priority. Thus, the highest priority is 0. The default is 32768.
        type: str
      enabled:
        description:
          - Manage the state(Enable/Disable) of the spanning_tree_802_1w in the current vlan
        type: bool
    type: dict
  aggregate:
    description:
      - List of VLANs definitions.
    type: list
    suboptions:
      name:
        description:
          - Name of the VLAN.
        type: str
      vlan_id:
        description:
          - ID of the VLAN. Range 1-4094.
        required: true
        type: str
      ip_dhcp_snooping:
        description:
          - Enables DHCP snooping on a VLAN.
        type: bool
      ip_arp_inspection:
        description:
          - Enables dynamic ARP inspection on a VLAN.
        type: bool
      tagged:
        description:
          - List of ethernet ports or LAGS to be added as trunk(tagged) ports to the vlan.
            To add a range of ports use 'to' keyword. See the example.
        suboptions:
          name:
            description:
              - Name of the interface or lag
            type: list
          purge:
            description:
              - Purge interfaces not defined in the I(name)
            type: bool
        type: dict
      interfaces:
        description:
          - List of ethernet ports or LAGS to be added as access(untagged) ports to the vlan.
            To add a range of ports use 'to' keyword. See the example.
        suboptions:
          name:
            description:
              - Name of the interface or lag
            type: list
          purge:
            description:
              - Purge interfaces not defined in the I(name)
            type: bool
        type: dict
      delay:
        description:
          - Delay the play should wait to check for declarative intent params values.
        type: int
      stp:
        description:
          - Enable spanning-tree 802-1w/rstp for this vlan.
        suboptions:
          type:
            description:
              - Specify the type of spanning-tree
            type: str
            default: 802-1w
            choices: ['802-1w','rstp']
          priority:
            description:
              - Configures the priority of the bridge. The value ranges from
                0 through 65535. A lower numerical value means the bridge has
                a higher priority. Thus, the highest priority is 0. The default is 32768.
            type: str
          enabled:
            description:
              - Manage the state(Enable/Disable) of the spanning_tree_802_1w in the current vlan
            type: bool
        type: dict
      state:
        description:
          - State of the VLAN configuration.
        type: str
        choices: ['present', 'absent']
      check_running_config:
        description:
          - Check running configuration. This can be set as environment variable.
           Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
        type: bool
      associated_interfaces:
        description:
          - This is a intent option and checks the operational state of the for given vlan C(name)
            for associated interfaces. If the value in the C(associated_interfaces) does not match with
            the operational state of vlan interfaces on device it will result in failure.
        type: list
      associated_tagged:
        description:
          - This is a intent option and checks the operational state of  given vlan C(name)
            for associated tagged ports and lags. If the value in the C(associated_tagged) does not match with
            the operational state of vlan interfaces on device it will result in failure.
        type: list
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
    default: no
    type: bool
  state:
    description:
      - State of the VLAN configuration.
    type: str
    default: present
    choices: ['present', 'absent']
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
       Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
    type: bool
    default: yes
"""

EXAMPLES = """
- name: Add a single ethernet 1/1/48 as access(untagged) port to vlan 20
  icx_vlan:
    name: test-vlan
    vlan_id: 20
    interfaces:
      name:
        - ethernet 1/1/48

- name: Add a single LAG 10 as access(untagged) port to vlan 20
  icx_vlan:
    vlan_id: 20
    interfaces:
      name:
        - lag 10

- name: Add a range of ethernet ports as trunk(tagged) ports to vlan 20 by port
  icx_vlan:
    vlan_id: 20
    tagged:
      name:
        - ethernet 1/1/40 to 1/1/48

- name: Add discontinuous lags, ethernet ports as access(untagged) and trunk(tagged) port to vlan 20.
  icx_vlan:
    vlan_id: 20
    interfaces:
      name:
        - ethernet 1/1/40 to 1/1/48
        - ethernet 2/1/1
        - lag 1
        - lag 3 to 5
    tagged:
      name:
        - ethernet 1/1/20 to 1/1/25
        - lag 1 to 3

- name: Remove an access and range of trunk ports from vlan
  icx_vlan:
    vlan_id: 20
    interfaces:
      name:
        - ethernet 1/1/40
    tagged:
      name:
        - ethernet 1/1/39 to 1/1/70

- name: Enable dhcp snooping, disable arp inspection in vlan
  icx_vlan:
    vlan_id: 20
    ip_dhcp_snooping: present
    ip_arp_inspection: absent

- name: Create vlan 20.  Enable  arp inspection in vlan. Purge all other vlans.
  icx_vlan:
    vlan_id: 20
    ip_arp_inspection: present
    purge: present

- name: Remove vlan 20.
  icx_vlan:
    vlan_id: 20
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - vlan 100
    - name test-vlan
"""

import re
from time import sleep
import itertools
from copy import deepcopy
from time import sleep
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.icx.icx import load_config, get_config
from ansible.module_utils.connection import Connection, ConnectionError, exec_command
from ansible.module_utils.network.common.utils import conditional, remove_default_spec


def search_obj_in_list(vlan_id, lst):
    obj = list()
    for o in lst:
        if str(o['vlan_id']) == vlan_id:
            return o


def parse_vlan_brief(module, vlan_id):
    command = 'show run vlan %s' % vlan_id
    rc, out, err = exec_command(module, command)
    lines = out.split('\n')
    untagged_ports = list()
    untagged_lags = list()
    tagged_ports = list()
    tagged_lags = list()

    for line in lines:
        if 'tagged' in line.split():
            lags = line.split(" lag ")
            ports = lags[0].split(" ethe ")
            del ports[0]
            del lags[0]
            for port in ports:
                if "to" in port:
                    p = port.split(" to ")
                    pr = int(p[1].split('/')[2]) - int(p[0].split('/')[2])
                    for i in range(0, pr + 1):
                        tagged_ports.append((int(p[0].split('/')[2]) + i))
                else:
                    tagged_ports.append(int(port.split('/')[2]))
            for lag in lags:
                if "to" in lag:
                    l = lag.split(" to ")
                    lr = int(l[1]) - int(l[0])
                    for i in range(0, lr + 1):
                        tagged_lags.append((int(l[0]) + i))
                else:
                    tagged_lags.append(int(lag))
        if 'untagged' in line.split():
            lags = line.split(" lag ")
            ports = lags[0].split(" ethe ")
            del ports[0]
            del lags[0]
            for port in ports:
                if "to" in port:
                    p = port.split(" to ")
                    pr = int(p[1].split('/')[2]) - int(p[0].split('/')[2])
                    for i in range(0, pr + 1):
                        untagged_ports.append((int(p[0].split('/')[2]) + i))
                else:
                    untagged_ports.append(int(port.split('/')[2]))
            for lag in lags:
                if "to" in lag:
                    l = lag.split(" to ")
                    lr = int(l[1]) - int(l[0])
                    for i in range(0, lr + 1):
                        untagged_lags.append((int(l[0]) + i))
                else:
                    untagged_lags.append(int(lag))

    return untagged_ports, untagged_lags, tagged_ports, tagged_lags


def extract_list_from_interface(interface):
    if 'ethernet' in interface:
        if 'to' in interface:
            s = re.search(r"\d+\/\d+/(?P<low>\d+)\sto\s+\d+\/\d+/(?P<high>\d+)", interface)
            low = int(s.group('low'))
            high = int(s.group('high'))
        else:
            s = re.search(r"\d+\/\d+/(?P<low>\d+)", interface)
            low = int(s.group('low'))
            high = int(s.group('low'))
    elif 'lag' in interface:
        if 'to' in interface:
            s = re.search(r"(?P<low>\d+)\sto\s(?P<high>\d+)", interface)
            low = int(s.group('low'))
            high = int(s.group('high'))
        else:
            s = re.search(r"(?P<low>\d+)", interface)
            low = int(s.group('low'))
            high = int(s.group('low'))

    return low, high


def parse_vlan_id(module):
    vlans = []
    command = 'show vlan brief'
    rc, out, err = exec_command(module, command)
    lines = out.split('\n')
    for line in lines:
        if 'VLANs Configured :' in line:
            values = line.split(':')[1]
            vlans = [s for s in values.split() if s.isdigit()]
            s = re.findall(r"(?P<low>\d+)\sto\s(?P<high>\d+)", values)
            for ranges in s:
                low = int(ranges[0]) + 1
                high = int(ranges[1])
                while(high > low):
                    vlans.append(str(low))
                    low = low + 1
    return vlans


def spanning_tree(module, stp):
    stp_cmd = list()
    if stp.get('enabled') is False:
        if stp.get('type') == '802-1w':
            stp_cmd.append('no spanning-tree' + ' ' + stp.get('type'))
        stp_cmd.append('no spanning-tree')

    elif stp.get('type'):
        stp_cmd.append('spanning-tree' + ' ' + stp.get('type'))
        if stp.get('priority') and stp.get('type') == 'rstp':
            module.fail_json(msg='spanning-tree 802-1w only can have priority')
        elif stp.get('priority'):
            stp_cmd.append('spanning-tree' + ' ' + stp.get('type') + ' ' + 'priority' + ' ' + stp.get('priority'))

    return stp_cmd


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]
            stp = item.get('stp')
            if stp:
                stp_cmd = spanning_tree(module, stp)
                item.update({'stp': stp_cmd})

            d = item.copy()

            obj.append(d)

    else:
        params = {
            'name': module.params['name'],
            'vlan_id': module.params['vlan_id'],
            'interfaces': module.params['interfaces'],
            'tagged': module.params['tagged'],
            'associated_interfaces': module.params['associated_interfaces'],
            'associated_tagged': module.params['associated_tagged'],
            'delay': module.params['delay'],
            'ip_dhcp_snooping': module.params['ip_dhcp_snooping'],
            'ip_arp_inspection': module.params['ip_arp_inspection'],
            'state': module.params['state'],
        }

        stp = module.params.get('stp')
        if stp:
            stp_cmd = spanning_tree(module, stp)
            params.update({'stp': stp_cmd})

        obj.append(params)

    return obj


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:
        vlan_id = w['vlan_id']
        state = w['state']
        name = w['name']
        interfaces = w.get('interfaces')
        tagged = w.get('tagged')
        dhcp = w.get('ip_dhcp_snooping')
        arp = w.get('ip_arp_inspection')
        stp = w.get('stp')
        obj_in_have = search_obj_in_list(str(vlan_id), have)

        if state == 'absent':
            if have == []:
                commands.append('no vlan {0}'.format(vlan_id))
            if obj_in_have:
                commands.append('no vlan {0}'.format(vlan_id))

        elif state == 'present':
            if not obj_in_have:
                commands.append('vlan {0}'.format(vlan_id))
                if name:
                    commands.append('vlan {0} name {1}'.format(vlan_id, name))

                if interfaces:
                    if interfaces['name']:
                        for item in interfaces['name']:
                            commands.append('untagged {0}'.format(item))

                if tagged:
                    if tagged['name']:
                        for item in tagged['name']:
                            commands.append('tagged {0}'.format(item))

                if dhcp is True:
                    commands.append('ip dhcp snooping vlan {0}'.format(vlan_id))
                elif dhcp is False:
                    commands.append('no ip dhcp snooping vlan {0}'.format(vlan_id))

                if arp is True:
                    commands.append('ip arp inspection vlan {0}'.format(vlan_id))
                elif dhcp is False:
                    commands.append('no ip arp inspection vlan {0}'.format(vlan_id))

                if stp:
                    if w.get('stp'):
                        [commands.append(cmd) for cmd in w['stp']]

            else:
                commands.append('vlan {0}'.format(vlan_id))
                if name:
                    if name != obj_in_have['name']:
                        commands.append('vlan {0} name {1}'.format(vlan_id, name))

                if interfaces:
                    if interfaces['name']:
                        have_interfaces = list()
                        for interface in interfaces['name']:
                            low, high = extract_list_from_interface(interface)

                            while(high >= low):
                                if 'ethernet' in interface:
                                    have_interfaces.append('ethernet 1/1/{0}'.format(low))
                                if 'lag' in interface:
                                    have_interfaces.append('lag {0}'.format(low))
                                low = low + 1

                    if interfaces['purge'] is True:
                        remove_interfaces = list(set(obj_in_have['interfaces']) - set(have_interfaces))
                        for item in remove_interfaces:
                            commands.append('no untagged {0}'.format(item))

                    if interfaces['name']:
                        add_interfaces = list(set(have_interfaces) - set(obj_in_have['interfaces']))
                        for item in add_interfaces:
                            commands.append('untagged {0}'.format(item))

                if tagged:
                    if tagged['name']:
                        have_tagged = list()
                        for tag in tagged['name']:
                            low, high = extract_list_from_interface(tag)

                            while(high >= low):
                                if 'ethernet' in tag:
                                    have_tagged.append('ethernet 1/1/{0}'.format(low))
                                if 'lag' in tag:
                                    have_tagged.append('lag {0}'.format(low))
                                low = low + 1
                    if tagged['purge'] is True:
                        remove_tagged = list(set(obj_in_have['tagged']) - set(have_tagged))
                        for item in remove_tagged:
                            commands.append('no tagged {0}'.format(item))

                    if tagged['name']:
                        add_tagged = list(set(have_tagged) - set(obj_in_have['tagged']))
                        for item in add_tagged:
                            commands.append('tagged {0}'.format(item))

                if dhcp != obj_in_have['ip_dhcp_snooping']:
                    if dhcp is True:
                        commands.append('ip dhcp snooping vlan {0}'.format(vlan_id))
                    elif dhcp is False:
                        commands.append('no ip dhcp snooping vlan {0}'.format(vlan_id))

                if arp != obj_in_have['ip_arp_inspection']:
                    if arp is True:
                        commands.append('ip arp inspection vlan {0}'.format(vlan_id))
                    elif arp is False:
                        commands.append('no ip arp inspection vlan {0}'.format(vlan_id))

                if stp:
                    if w.get('stp'):
                        [commands.append(cmd) for cmd in w['stp']]

            if len(commands) == 1 and 'vlan ' + str(vlan_id) in commands:
                commands = []

    if purge:
        commands = []
        vlans = parse_vlan_id(module)
        for h in vlans:
            obj_in_want = search_obj_in_list(h, want)
            if not obj_in_want and h != '1':
                commands.append('no vlan {0}'.format(h))

    return commands


def parse_name_argument(module, item):
    command = 'show vlan {0}'.format(item)
    rc, out, err = exec_command(module, command)
    match = re.search(r"Name (\S+),", out)
    if match:
        return match.group(1)


def parse_interfaces_argument(module, item, port_type):
    untagged_ports, untagged_lags, tagged_ports, tagged_lags = parse_vlan_brief(module, item)
    ports = list()
    if port_type == "interfaces":
        if untagged_ports:
            for port in untagged_ports:
                ports.append('ethernet 1/1/' + str(port))
        if untagged_lags:
            for port in untagged_lags:
                ports.append('lag ' + str(port))

    elif port_type == "tagged":
        if tagged_ports:
            for port in tagged_ports:
                ports.append('ethernet 1/1/' + str(port))
        if tagged_lags:
            for port in tagged_lags:
                ports.append('lag ' + str(port))

    return ports


def parse_config_argument(config, arg):
    match = re.search(arg, config, re.M)
    if match:
        return True
    else:
        return False


def map_config_to_obj(module):
    config = get_config(module)
    vlans = parse_vlan_id(module)
    instance = list()

    for item in set(vlans):
        obj = {
            'vlan_id': item,
            'name': parse_name_argument(module, item),
            'interfaces': parse_interfaces_argument(module, item, 'interfaces'),
            'tagged': parse_interfaces_argument(module, item, 'tagged'),
            'ip_dhcp_snooping': parse_config_argument(config, 'ip dhcp snooping vlan {0}'.format(item)),
            'ip_arp_inspection': parse_config_argument(config, 'ip arp inspection vlan {0}'.format(item)),
        }
        instance.append(obj)
    return instance


def check_fail(module, output):
    error = [
        re.compile(br"^error", re.I)
    ]
    for x in output:
        for regex in error:
            if regex.search(x):
                module.fail_json(msg=x)


def check_declarative_intent_params(want, module, result):
    def parse_ports(interfaces, ports, lags):
        for interface in interfaces:
            low, high = extract_list_from_interface(interface)

            while(high >= low):
                if 'ethernet' in interface:
                    if not (low in ports):
                        module.fail_json(msg='One or more conditional statements have not been satisfied ' + interface)
                if 'lag' in interface:
                    if not (low in lags):
                        module.fail_json(msg='One or more conditional statements have not been satisfied ' + interface)
                low = low + 1

    is_delay = False
    low = 0
    high = 0
    for w in want:
        if w.get('associated_interfaces') is None and w.get('associated_tagged') is None:
            continue

        if result['changed'] and not is_delay:
            sleep(module.params['delay'])
            is_delay = True

        untagged_ports, untagged_lags, tagged_ports, tagged_lags = parse_vlan_brief(module, w['vlan_id'])

        if w['associated_interfaces']:
            parse_ports(w.get('associated_interfaces'), untagged_ports, untagged_lags)

        if w['associated_tagged']:
            parse_ports(w.get('associated_tagged'), tagged_ports, tagged_lags)


def main():
    """ main entry point for module execution
    """
    stp_spec = dict(
        type=dict(default='802-1w', choices=['802-1w', 'rstp']),
        priority=dict(),
        enabled=dict(type='bool'),
    )
    inter_spec = dict(
        name=dict(type='list'),
        purge=dict(type='bool')
    )
    tagged_spec = dict(
        name=dict(type='list'),
        purge=dict(type='bool')
    )
    element_spec = dict(
        vlan_id=dict(type='int'),
        name=dict(),
        interfaces=dict(type='dict', options=inter_spec),
        tagged=dict(type='dict', options=tagged_spec),
        ip_dhcp_snooping=dict(type='bool'),
        ip_arp_inspection=dict(type='bool'),
        associated_interfaces=dict(type='list'),
        associated_tagged=dict(type='list'),
        delay=dict(default=10, type='int'),
        stp=dict(type='dict', options=stp_spec),
        state=dict(default='present', choices=['present', 'absent']),
        check_running_config=dict(default=True, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG']))
    )
    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['vlan_id'] = dict(required=True)

    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )
    argument_spec.update(element_spec)
    required_one_of = [['vlan_id', 'aggregate']]
    mutually_exclusive = [['vlan_id', 'aggregate']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)
    warnings = list()
    result = {}
    result['changed'] = False
    if warnings:
        result['warnings'] = warnings
    exec_command(module, 'skip')
    want = map_params_to_obj(module)
    if module.params['check_running_config'] is False:
        have = []
    else:
        have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            output = load_config(module, commands)
            if output:
                check_fail(module, output)
            result['output'] = output
        result['changed'] = True

    check_declarative_intent_params(want, module, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
