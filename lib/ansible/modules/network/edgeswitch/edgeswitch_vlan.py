#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: edgeswitch_vlan
version_added: "2.8"
author: "Frederic Bor (@f-bor)"
short_description: Manage VLANs on Ubiquiti Edgeswitch network devices
description:
  - This module provides declarative management of VLANs
    on Ubiquiti Edgeswitch network devices.
notes:
  - Tested against edgeswitch 1.7.4
  - This module use native Ubiquiti vlan syntax and does not support switchport compatibility syntax.
    For clarity, it is strongly advised to not use both syntaxes on the same interface.
  - Edgeswitch does not support deleting or changing name of VLAN 1
  - As auto_tag, auto_untag and auto_exclude are a kind of default setting for all interfaces, they are mutually exclusive

options:
  name:
    description:
      - Name of the VLAN.
  vlan_id:
    description:
      - ID of the VLAN. Range 1-4093.
  tagged_interfaces:
    description:
      - List of interfaces that should accept and transmit tagged frames for the VLAN.
        Accept range of interfaces.
  untagged_interfaces:
    description:
      - List of interfaces that should accept untagged frames and transmit them tagged for the VLAN.
        Accept range of interfaces.
  excluded_interfaces:
    description:
      - List of interfaces that should be excluded of the VLAN.
        Accept range of interfaces.
  auto_tag:
    description:
      - Each of the switch interfaces will be set to accept and transmit
        untagged frames for I(vlan_id) unless defined in I(*_interfaces).
        This is a default setting for all switch interfaces.
    type: bool
  auto_untag:
    description:
      - Each of the switch interfaces will be set to accept untagged frames and
        transmit them tagged for I(vlan_id) unless defined in I(*_interfaces).
        This is a default setting for all switch interfaces.
    type: bool
  auto_exclude:
    description:
      - Each of the switch interfaces will be excluded from I(vlan_id)
        unless defined in I(*_interfaces).
        This is a default setting for all switch interfaces.
    type: bool
  aggregate:
    description: List of VLANs definitions.
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
    default: no
    type: bool
  state:
    description:
      - action on the VLAN configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Create vlan
  edgeswitch_vlan:
    vlan_id: 100
    name: voice
    action: present

- name: Add interfaces to VLAN
  edgeswitch_vlan:
    vlan_id: 100
    tagged_interfaces:
      - 0/1
      - 0/4-0/6

- name: setup three vlans and delete the rest
  edgeswitch_vlan:
    purge: true
    aggregate:
      - { vlan_id: 1, name: default, auto_untag: true, excluded_interfaces: 0/45-0/48 }
      - { vlan_id: 100, name: voice, auto_tag: true }
      - { vlan_id: 200, name: video, auto_exclude: true, untagged_interfaces: 0/45-0/48, tagged_interfaces: 0/49 }

- name: Delete vlan
  edgeswitch_vlan:
    vlan_id: 100
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - vlan database
    - vlan 100
    - vlan name 100 "test vlan"
    - exit
    - interface 0/1
    - vlan pvid 50
    - vlan participation include 50,100
    - vlan tagging 100
    - vlan participation exclude 200
    - no vlan tagging 200
"""

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.edgeswitch.edgeswitch import load_config, run_commands
from ansible.module_utils.network.edgeswitch.edgeswitch import build_aggregate_spec, map_params_to_obj
from ansible.module_utils.network.edgeswitch.edgeswitch_interface import InterfaceConfiguration, merge_interfaces


def search_obj_in_list(vlan_id, lst):
    for o in lst:
        if o['vlan_id'] == vlan_id:
            return o


def map_vlans_to_commands(want, have, module):
    commands = []
    vlans_added = []
    vlans_removed = []
    vlans_names = []

    for w in want:
        vlan_id = w['vlan_id']
        name = w['name']
        state = w['state']

        obj_in_have = search_obj_in_list(vlan_id, have)

        if state == 'absent':
            if obj_in_have:
                vlans_removed.append(vlan_id)

        elif state == 'present':
            if not obj_in_have:
                vlans_added.append(vlan_id)
                if name:
                    vlans_names.append('vlan name {0} "{1}"'.format(vlan_id, name))
            else:
                if name:
                    if name != obj_in_have['name']:
                        vlans_names.append('vlan name {0} "{1}"'.format(vlan_id, name))

    if module.params['purge']:
        for h in have:
            obj_in_want = search_obj_in_list(h['vlan_id'], want)
            # you can't delete vlan 1 on Edgeswitch
            if not obj_in_want and h['vlan_id'] != '1':
                vlans_removed.append(h['vlan_id'])

    if vlans_removed:
        commands.append('no vlan {0}'.format(','.join(vlans_removed)))

    if vlans_added:
        commands.append('vlan {0}'.format(','.join(vlans_added)))

    if vlans_names:
        commands.extend(vlans_names)

    if commands:
        commands.insert(0, 'vlan database')
        commands.append('exit')

    return commands


class VlanInterfaceConfiguration(InterfaceConfiguration):
    """ class holding vlan definitions for a given interface
    """
    def __init__(self):
        InterfaceConfiguration.__init__(self)
        self.tagged = []
        self.untagged = []
        self.excluded = []

    def set_vlan(self, vlan_id, type):
        try:
            self.tagged.remove(vlan_id)
        except ValueError:
            pass

        try:
            self.untagged.remove(vlan_id)
        except ValueError:
            pass

        try:
            self.excluded.remove(vlan_id)
        except ValueError:
            pass

        f = getattr(self, type)
        f.append(vlan_id)

    def gen_commands(self, port, module):
        """ to reduce commands generated by this module
            we group vlans changes to have a max of 5 vlan commands by interface
        """
        exclude = []
        include = []
        tag = []
        untag = []
        pvid = []

        for vlan_id in self.excluded:
            if vlan_id not in port['forbidden_vlans']:
                exclude.append(vlan_id)

            if vlan_id in port['tagged_vlans']:
                untag.append(vlan_id)

        for vlan_id in self.untagged:
            if vlan_id in port['forbidden_vlans'] or vlan_id not in port['untagged_vlans'] and vlan_id not in port['tagged_vlans']:
                include.append(vlan_id)

            if vlan_id in port['tagged_vlans']:
                untag.append(vlan_id)

            if vlan_id != port['pvid_mode']:
                pvid.append(vlan_id)

        for vlan_id in self.tagged:
            if vlan_id not in port['tagged_vlans']:
                tag.append(vlan_id)
                include.append(vlan_id)

        if include:
            self.commands.append('vlan participation include {0}'.format(','.join(include)))

        if pvid:
            if len(pvid) > 1:
                module.fail_json(msg='{0} can\'t have more than one untagged vlan')
                return
            self.commands.append('vlan pvid {0}'.format(pvid[0]))

        if untag:
            self.commands.append('no vlan tagging {0}'.format(','.join(untag)))

        if tag:
            self.commands.append('vlan tagging {0}'.format(','.join(tag)))

        if exclude:
            self.commands.append('vlan participation exclude {0}'.format(','.join(exclude)))


def set_interfaces_vlan(interfaces_param, interfaces, vlan_id, type):
    """ set vlan_id type for each interface in interfaces_param on interfaces
        unrange interfaces_param if needed
    """
    if interfaces_param:
        for i in interfaces_param:
            match = re.search(r'(\d+)\/(\d+)-(\d+)\/(\d+)', i)
            if match:
                group = match.group(1)
                start = int(match.group(2))
                end = int(match.group(4))
                for x in range(start, end + 1):
                    key = '{0}/{1}'.format(group, x)
                    interfaces[key].set_vlan(vlan_id, type)
            else:
                interfaces[i].set_vlan(vlan_id, type)


def map_interfaces_to_commands(want, ports, module):
    commands = list()

    # generate a configuration for each interface
    interfaces = {}
    for key, value in ports.items():
        interfaces[key] = VlanInterfaceConfiguration()

    for w in want:
        state = w['state']
        if state != 'present':
            continue

        auto_tag = w['auto_tag']
        auto_untag = w['auto_untag']
        auto_exclude = w['auto_exclude']
        vlan_id = w['vlan_id']
        tagged_interfaces = w['tagged_interfaces']
        untagged_interfaces = w['untagged_interfaces']
        excluded_interfaces = w['excluded_interfaces']

        # set the default type, if any
        for key, value in ports.items():
            if auto_tag:
                interfaces[key].tagged.append(vlan_id)
            elif auto_exclude:
                interfaces[key].excluded.append(vlan_id)
            elif auto_untag:
                interfaces[key].untagged.append(vlan_id)

        # set explicit definitions
        set_interfaces_vlan(tagged_interfaces, interfaces, vlan_id, 'tagged')
        set_interfaces_vlan(untagged_interfaces, interfaces, vlan_id, 'untagged')
        set_interfaces_vlan(excluded_interfaces, interfaces, vlan_id, 'excluded')

    # generate commands for each interface
    for i, interface in interfaces.items():
        port = ports[i]
        interface.gen_commands(port, module)

    # reduce them using range syntax when possible
    interfaces = merge_interfaces(interfaces)

    # final output
    for i, interface in interfaces.items():
        if len(interface.commands) > 0:
            commands.append('interface {0}'.format(i))
            commands.extend(interface.commands)

    return commands


def parse_vlan_brief(vlan_out):
    have = []
    for line in vlan_out.split('\n'):
        obj = re.match(r'(?P<vlan_id>\d+)\s+(?P<name>[^\s]+)\s+', line)
        if obj:
            have.append(obj.groupdict())
    return have


def unrange(vlans):
    res = []
    for vlan in vlans:
        match = re.match(r'(\d+)-(\d+)', vlan)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            for vlan_id in range(start, end + 1):
                res.append(str(vlan_id))
        else:
            res.append(vlan)
    return res


def parse_interfaces_switchport(cmd_out):
    ports = dict()
    objs = re.findall(
        r'Port: (\d+\/\d+)\n'
        'VLAN Membership Mode:(.*)\n'
        'Access Mode VLAN:(.*)\n'
        'General Mode PVID:(.*)\n'
        'General Mode Ingress Filtering:(.*)\n'
        'General Mode Acceptable Frame Type:(.*)\n'
        'General Mode Dynamically Added VLANs:(.*)\n'
        'General Mode Untagged VLANs:(.*)\n'
        'General Mode Tagged VLANs:(.*)\n'
        'General Mode Forbidden VLANs:(.*)\n', cmd_out)
    for o in objs:
        port = {
            'interface': o[0],
            'pvid_mode': o[3].replace("(default)", "").strip(),
            'untagged_vlans': unrange(o[7].strip().split(',')),
            'tagged_vlans': unrange(o[8].strip().split(',')),
            'forbidden_vlans': unrange(o[9].strip().split(','))
        }
        ports[port['interface']] = port
    return ports


def map_ports_to_obj(module):
    return parse_interfaces_switchport(run_commands(module, ['show interfaces switchport'])[0])


def map_config_to_obj(module):
    return parse_vlan_brief(run_commands(module, ['show vlan brief'])[0])


def check_params(module, want):
    """ Deeper checks on parameters
    """
    def check_parmams_interface(interfaces):
        if interfaces:
            for i in interfaces:
                match = re.search(r'(\d+)\/(\d+)-(\d+)\/(\d+)', i)
                if match:
                    if match.group(1) != match.group(3):
                        module.fail_json(msg="interface range must be within same group: " + i)
                else:
                    match = re.search(r'(\d+)\/(\d+)', i)
                    if not match:
                        module.fail_json(msg="wrong interface format: " + i)

    for w in want:
        auto_tag = w['auto_tag']
        auto_untag = w['auto_untag']
        auto_exclude = w['auto_exclude']

        c = 0
        if auto_tag:
            c = c + 1

        if auto_untag:
            c = c + 1

        if auto_exclude:
            c = c + 1

        if c > 1:
            module.fail_json(msg="parameters are mutually exclusive: auto_tag, auto_untag, auto_exclude")
            return

        check_parmams_interface(w['tagged_interfaces'])
        check_parmams_interface(w['untagged_interfaces'])
        check_parmams_interface(w['excluded_interfaces'])
        w['vlan_id'] = str(w['vlan_id'])


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        vlan_id=dict(type='int'),
        name=dict(),
        tagged_interfaces=dict(type='list'),
        untagged_interfaces=dict(type='list'),
        excluded_interfaces=dict(type='list'),
        auto_tag=dict(type='bool'),
        auto_exclude=dict(type='bool'),
        auto_untag=dict(type='bool'),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    argument_spec = build_aggregate_spec(
        element_spec,
        ['vlan_id'],
        dict(purge=dict(default=False, type='bool'))
    )

    required_one_of = [['vlan_id', 'aggregate']]
    mutually_exclusive = [
        ['vlan_id', 'aggregate'],
        ['auto_tag', 'auto_untag', 'auto_exclude']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)
    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    check_params(module, want)

    # vlans are not created/deleted in configure mode
    commands = map_vlans_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            run_commands(module, commands, check_rc=False)
        result['changed'] = True

    ports = map_ports_to_obj(module)

    # interfaces vlan are set in configure mode
    commands = map_interfaces_to_commands(want, ports, module)
    result['commands'].extend(commands)

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
