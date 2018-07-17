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
module: nxos_vlan
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manages VLAN resources and attributes.
description:
  - Manages VLAN configurations on NX-OS switches.
author: Jason Edelman (@jedelman8)
options:
  vlan_id:
    description:
      - Single VLAN ID.
  vlan_range:
    description:
      - Range of VLANs such as 2-10 or 2,5,10-15, etc.
  name:
    description:
      - Name of VLAN or keyword 'default'.
  interfaces:
    description:
      - List of interfaces that should be associated to the VLAN or keyword 'default'.
    version_added: "2.5"
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for given vlan C(name)
        for associated interfaces. If the value in the C(associated_interfaces) does not match with
        the operational state of vlan interfaces on device it will result in failure.
    version_added: "2.5"
  vlan_state:
    description:
      - Manage the vlan operational state of the VLAN
    default: active
    choices: ['active','suspend']
  admin_state:
    description:
      - Manage the VLAN administrative state of the VLAN equivalent
        to shut/no shut in VLAN config mode.
    default: up
    choices: ['up','down']
  mapped_vni:
    description:
      - The Virtual Network Identifier (VNI) ID that is mapped to the
        VLAN. Valid values are integer and keyword 'default'. Range 4096-16773119.
    version_added: "2.2"
  state:
    description:
      - Manage the state of the resource.
    default: present
    choices: ['present','absent']
  mode:
    description:
      - Set VLAN mode to classical ethernet or fabricpath.
        This is a valid option for Nexus 5000 and 7000 series.
    default: ce
    choices: ['ce','fabricpath']
    version_added: "2.4"
  aggregate:
    description: List of VLANs definitions.
    version_added: "2.5"
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
        This parameter can be used without aggregate as well.
    type: bool
    default: 'no'
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state arguments.
    default: 10
'''

EXAMPLES = '''
- name: Ensure a range of VLANs are not present on the switch
  nxos_vlan:
    vlan_range: "2-10,20,50,55-60,100-150"
    state: absent

- name: Ensure VLAN 50 exists with the name WEB and is in the shutdown state
  nxos_vlan:
    vlan_id: 50
    admin_state: down
    name: WEB

- name: Ensure VLAN is NOT on the device
  nxos_vlan:
    vlan_id: 50
    state: absent

- name: Add interfaces to VLAN and check intent (config + intent)
  nxos_vlan:
    vlan_id: 100
    interfaces:
      - Ethernet2/1
      - Ethernet2/5
    associated_interfaces:
      - Ethernet2/1
      - Ethernet2/5

- name: Check interfaces assigned to VLAN
  nxos_vlan:
    vlan_id: 100
    associated_interfaces:
      - Ethernet2/1
      - Ethernet2/5

- name: Create aggregate of vlans
  nxos_vlan:
    aggregate:
      - { vlan_id: 4000, mode: ce }
      - { vlan_id: 4001, name: vlan-4001 }

- name: purge vlans - removes all other vlans except the ones mentioned in aggregate)
  nxos_vlan:
    aggregate:
      - vlan_id: 1
      - vlan_id: 4001
    purge: yes

'''

RETURN = '''
commands:
    description: Set of command strings to send to the remote device
    returned: always
    type: list
    sample: ["vlan 20", "vlan 55", "vn-segment 5000"]
'''

import re
import time

from copy import deepcopy

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec


def search_obj_in_list(vlan_id, lst):
    for o in lst:
        if o['vlan_id'] == vlan_id:
            return o


def get_diff(w, obj):
    c = deepcopy(w)
    entries = ('interfaces', 'associated_interfaces', 'delay', 'vlan_range')
    for key in entries:
        if key in c:
            del c[key]

    o = deepcopy(obj)
    del o['interfaces']
    if o['vlan_id'] == w['vlan_id']:
        diff_dict = dict(set(c.items()) - set(o.items()))
        return diff_dict


def is_default_name(obj, vlan_id):
    cname = obj['name']
    if ('VLAN' in cname):
        vid = int(cname[4:])
        if vid == int(vlan_id):
            return True

    return False


def map_obj_to_commands(updates, module, os_platform):
    commands = list()
    purge = module.params['purge']
    want, have = updates

    for w in want:
        vlan_id = w['vlan_id']
        name = w['name']
        interfaces = w.get('interfaces') or []
        mapped_vni = w['mapped_vni']
        vlan_state = w['vlan_state']
        admin_state = w['admin_state']
        state = w['state']
        del w['state']
        if any(i in os_platform for i in ['5K', '7K']):
            mode = w['mode']
        else:
            w['mode'] = None
            mode = w['mode']

        obj_in_have = search_obj_in_list(vlan_id, have)

        if state == 'absent':
            if obj_in_have:
                if obj_in_have['mapped_vni'] != 'None':
                    commands.append('vlan {0}'.format(vlan_id))
                    commands.append('no vn-segment')
                    commands.append('exit')
                commands.append('no vlan {0}'.format(vlan_id))

        elif state == 'present':
            if not obj_in_have:
                commands.append('vlan {0}'.format(vlan_id))

                if name and name != 'default':
                    commands.append('name {0}'.format(name))
                if mode:
                    commands.append('mode {0}'.format(mode))
                if vlan_state:
                    commands.append('state {0}'.format(vlan_state))
                if mapped_vni != 'None' and mapped_vni != 'default':
                    commands.append('vn-segment {0}'.format(mapped_vni))
                if admin_state == 'up':
                    commands.append('no shutdown')
                if admin_state == 'down':
                    commands.append('shutdown')
                commands.append('exit')

                if interfaces and interfaces[0] != 'default':
                    for i in interfaces:
                        commands.append('interface {0}'.format(i))
                        commands.append('switchport')
                        commands.append('switchport mode access')
                        commands.append('switchport access vlan {0}'.format(vlan_id))

            else:
                diff = get_diff(w, obj_in_have)
                if diff:
                    commands.append('vlan {0}'.format(vlan_id))
                    for key, value in diff.items():
                        if key == 'name':
                            if name != 'default':
                                if name is not None:
                                    commands.append('name {0}'.format(value))
                            else:
                                if not is_default_name(obj_in_have, vlan_id):
                                    commands.append('no name')
                        if key == 'vlan_state':
                            commands.append('state {0}'.format(value))
                        if key == 'mapped_vni':
                            if value == 'default':
                                if obj_in_have['mapped_vni'] != 'None':
                                    commands.append('no vn-segment')
                            elif value != 'None':
                                commands.append('vn-segment {0}'.format(value))
                        if key == 'admin_state':
                            if value == 'up':
                                commands.append('no shutdown')
                            elif value == 'down':
                                commands.append('shutdown')
                        if key == 'mode':
                            commands.append('mode {0}'.format(value))
                    if len(commands) > 1:
                        commands.append('exit')
                    else:
                        del commands[:]

                if interfaces and interfaces[0] != 'default':
                    if not obj_in_have['interfaces']:
                        for i in interfaces:
                            commands.append('vlan {0}'.format(vlan_id))
                            commands.append('exit')
                            commands.append('interface {0}'.format(i))
                            commands.append('switchport')
                            commands.append('switchport mode access')
                            commands.append('switchport access vlan {0}'.format(vlan_id))

                    elif set(interfaces) != set(obj_in_have['interfaces']):
                        missing_interfaces = list(set(interfaces) - set(obj_in_have['interfaces']))
                        for i in missing_interfaces:
                            commands.append('vlan {0}'.format(vlan_id))
                            commands.append('exit')
                            commands.append('interface {0}'.format(i))
                            commands.append('switchport')
                            commands.append('switchport mode access')
                            commands.append('switchport access vlan {0}'.format(vlan_id))

                        superfluous_interfaces = list(set(obj_in_have['interfaces']) - set(interfaces))
                        for i in superfluous_interfaces:
                            commands.append('vlan {0}'.format(vlan_id))
                            commands.append('exit')
                            commands.append('interface {0}'.format(i))
                            commands.append('switchport')
                            commands.append('switchport mode access')
                            commands.append('no switchport access vlan {0}'.format(vlan_id))

                elif interfaces and interfaces[0] == 'default':
                    if obj_in_have['interfaces']:
                        for i in obj_in_have['interfaces']:
                            commands.append('vlan {0}'.format(vlan_id))
                            commands.append('exit')
                            commands.append('interface {0}'.format(i))
                            commands.append('switchport')
                            commands.append('switchport mode access')
                            commands.append('no switchport access vlan {0}'.format(vlan_id))

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['vlan_id'], want)
            if not obj_in_want:
                commands.append('no vlan {0}'.format(h['vlan_id']))

    return commands


def want_vlan_list(module):
    result = []
    vlan_range = module.params['vlan_range']
    for part in vlan_range.split(','):
        if part == 'none':
            break
        if '-' in part:
            start, end = part.split('-')
            start, end = int(start), int(end)
            result.extend([str(i) for i in range(start, end + 1)])
        else:
            result.append(part)
    return result


def have_vlan_list(have):
    result = []
    if have:
        for h in have:
            result.append(str(h.get('vlan_id')))
    return result


def vlan_range_commands(module, have):
    commands = list()
    proposed_vlans_list = want_vlan_list(module)
    existing_vlans_list = have_vlan_list(have)

    if module.params['state'] == 'absent':
        vlans = set(proposed_vlans_list).intersection(existing_vlans_list)
        for vlan in vlans:
            commands.append('no vlan {0}'.format(vlan))

    elif module.params['state'] == 'present':
        vlans = set(proposed_vlans_list).difference(existing_vlans_list)
        for vlan in vlans:
            commands.append('vlan {0}'.format(vlan))

    return commands


def map_params_to_obj(module):
    obj = []
    if module.params['vlan_range']:
        return []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            d['vlan_id'] = str(d['vlan_id'])
            d['mapped_vni'] = str(d['mapped_vni'])

            obj.append(d)
    else:
        obj.append({
            'vlan_id': str(module.params['vlan_id']),
            'name': module.params['name'],
            'interfaces': module.params['interfaces'],
            'vlan_state': module.params['vlan_state'],
            'mapped_vni': str(module.params['mapped_vni']),
            'state': module.params['state'],
            'admin_state': module.params['admin_state'],
            'mode': module.params['mode'],
            'associated_interfaces': module.params['associated_interfaces']
        })

    return obj


def parse_admin_state(vlan):
    shutstate = vlan.get('vlanshowbr-shutstate')
    if shutstate == 'noshutdown':
        return 'up'
    elif shutstate == 'shutdown':
        return 'down'


def parse_mode(os_platform, output, vlan_id):
    if not any(i in os_platform for i in ['5K', '7K']):
        return None

    try:
        mtus = output['TABLE_mtuinfo']['ROW_mtuinfo']
    except KeyError:
        return None

    if mtus:
        if isinstance(mtus, list):
            for mtu in mtus:
                if mtu['vlanshowinfo-vlanid'] == vlan_id:
                    mode = mtu.get('vlanshowinfo-vlanmode')
                    if mode == 'ce-vlan':
                        return 'ce'
                    elif mode == 'fabricpath-vlan':
                        return 'fabricpath'
            return None

        elif isinstance(mtus, dict):
            if mtus['vlanshowinfo-vlanid'] == vlan_id:
                    mode = mtus.get('vlanshowinfo-vlanmode')
                    if mode == 'ce-vlan':
                        return 'ce'
                    elif mode == 'fabricpath-vlan':
                        return 'fabricpath'
            return None

        else:
            return None
    else:
        return None


def parse_vni(module, vlan_id):
    vni = None
    flags = ['| section vlan.{0}'.format(vlan_id)]
    cfg = get_config(module, flags=flags)

    match = re.search(r'vn-segment (\S+)', cfg, re.M)
    if match:
        vni = match.group(1)
    return str(vni)


def get_vlan_int(interfaces):
    vlan_int = []
    for i in interfaces.split(','):
        if 'eth' in i.lower() and '-' in i:
            int_range = i.split('-')
            stop = int((int_range)[1])
            start = int(int_range[0].split('/')[1])
            eth = int_range[0].split('/')[0]
            for r in range(start, stop + 1):
                vlan_int.append(eth + '/' + str(r))
        else:
            vlan_int.append(i)
    return vlan_int


def parse_interfaces(module, vlan):
    vlan_int = []
    interfaces = vlan.get('vlanshowplist-ifidx')
    if interfaces:
        if isinstance(interfaces, list):
            interfaces_list = [i.strip() for i in interfaces]
            interfaces_str = ','.join(interfaces_list)
            vlan_int = get_vlan_int(interfaces_str)
        else:
            vlan_int = get_vlan_int(interfaces)
    return vlan_int


def parse_vlan_options(module, os_platform, output, vlan):
    obj = {}
    vlan_id = vlan['vlanshowbr-vlanid-utf']
    obj['vlan_id'] = str(vlan_id)
    obj['name'] = vlan.get('vlanshowbr-vlanname')
    obj['vlan_state'] = vlan.get('vlanshowbr-vlanstate')
    obj['admin_state'] = parse_admin_state(vlan)
    obj['mode'] = parse_mode(os_platform, output, vlan_id)
    obj['mapped_vni'] = parse_vni(module, vlan_id)
    obj['interfaces'] = parse_interfaces(module, vlan)
    return obj


def map_config_to_obj(module, os_platform):
    objs = list()
    output = run_commands(module, ['show vlan | json'])[0]
    try:
        vlans = output['TABLE_vlanbrief']['ROW_vlanbrief']
    except KeyError:
        return objs

    if vlans:
        if isinstance(vlans, list):
            for vlan in vlans:
                obj = parse_vlan_options(module, os_platform, output, vlan)
                objs.append(obj)

        elif isinstance(vlans, dict):
            obj = parse_vlan_options(module, os_platform, output, vlans)
            objs.append(obj)

    return objs


def check_declarative_intent_params(want, module, os_platform, result):

    have = None
    is_delay = False

    for w in want:
        if w.get('associated_interfaces') is None:
            continue

        if result['changed'] and not is_delay:
            time.sleep(module.params['delay'])
            is_delay = True

        if have is None:
            have = map_config_to_obj(module, os_platform)

        for i in w['associated_interfaces']:
            obj_in_have = search_obj_in_list(w['vlan_id'], have)
            if obj_in_have and 'interfaces' in obj_in_have and i not in obj_in_have['interfaces']:
                module.fail_json(msg="Interface %s not configured on vlan %s" % (i, w['vlan_id']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        vlan_id=dict(required=False, type='int'),
        vlan_range=dict(required=False),
        name=dict(required=False),
        interfaces=dict(type='list'),
        associated_interfaces=dict(type='list'),
        vlan_state=dict(choices=['active', 'suspend'], required=False, default='active'),
        mapped_vni=dict(required=False),
        delay=dict(default=10, type='int'),
        state=dict(choices=['present', 'absent'], default='present', required=False),
        admin_state=dict(choices=['up', 'down'], required=False, default='up'),
        mode=dict(choices=['ce', 'fabricpath'], required=False, default='ce'),
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['vlan_id'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(nxos_argument_spec)

    required_one_of = [['vlan_id', 'aggregate', 'vlan_range']]
    mutually_exclusive = [['vlan_id', 'aggregate'],
                          ['vlan_range', 'name'],
                          ['vlan_id', 'vlan_range']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    info = get_capabilities(module).get('device_info', {})
    os_platform = info.get('network_os_platform', '')

    warnings = list()
    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    have = map_config_to_obj(module, os_platform)
    want = map_params_to_obj(module)

    if module.params['vlan_range']:
        commands = vlan_range_commands(module, have)
        result['commands'] = commands
    else:
        commands = map_obj_to_commands((want, have), module, os_platform)
        result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    if want:
        check_declarative_intent_params(want, module, os_platform, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
