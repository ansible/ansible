#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2019, James Denton <james.denton@outlook.com>
# Portions copyright @ 2013 David Stygstra <david.stygstra@gmail.com>
# Portions copyright @ 2015 VMware, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: openvswitch_bond
version_added: '2.8'
author: "James Denton (@busterswt)"
short_description: Manage Open vSwitch bonds
requirements: [ ovs-vsctl ]
description:
    - Manage Open vSwitch bonds and associated options.
options:
    bridge:
        required: true
        type: str
        description:
            - Name of bridge to manage
    port:
        required: true
        type: str
        description:
            - Name of port to manage on the bridge
    interfaces:
        required: true
        type: list
        description:
            - List of interfaces to add to the bond
    bond_mode:
        choices: [ active-backup, balance-tcp, balance-slb ]
        type: str
        description:
            - Sets the bond mode
    lacp:
        choices: [ 'active', 'passive', 'off' ]
        type: str
        description:
            - Sets LACP mode
    bond_updelay:
        type: int
        description:
            - Number of milliseconds a link must be up to be activated
              to prevent flapping.
    bond_downdelay:
        type: int
        description:
            - Number of milliseconds a link must be down to be deactivated
              to prevent flapping.
    state:
        default: 'present'
        choices: [ 'present', 'absent' ]
        type: str
        description:
            - Whether the port should exist
    timeout:
        default: 5
        type: int
        description:
            - How long to wait for ovs-vswitchd to respond in seconds
    external_ids:
        default: {}
        type: dict
        description:
            - Dictionary of external_ids applied to a port.
    other_config:
        default: {}
        type: dict
        description:
            - Dictionary of other_config applied to a port.
    set:
        type: list
        description:
            - Sets one or more properties on a port.
'''

EXAMPLES = '''
- name: Create an active-backup bond using eth4 and eth5 on bridge br-ex
  openvswitch_bond:
    bridge: br-ex
    port: bond1
    interfaces:
      - eth4
      - eth5
    state: present

- name: Delete the bond from bridge br-ex
  openvswitch_bond:
    bridge: br-ex
    port: bond1
    state: absent

- name: Create an active LACP bond using eth4 and eth5 on bridge br-ex
  openvswitch_bond:
    bridge: br-ex
    port: bond1
    interfaces:
      - eth4
      - eth5
    lacp: active
    state: present

# NOTE: other_config values of integer type must be represented
# as literal strings
- name: Configure bond with miimon link monitoring at 100 millisecond intervals
  openvswitch_bond:
    bridge: br-ex
    port: bond1
    interfaces:
      - eth4
      - eth5
    bond_updelay: 100
    bond_downdelay: 100
    state: present
  args:
    other_config:
      bond-detect-mode: miimon
      bond-miimon-interval: '"100"'

- name: Create an active LACP bond using DPDK interfaces
  openvswitch_bond:
    bridge: br-provider
    port: dpdkbond
    interfaces:
      - "0000:04:00.0"
      - "0000:04:00.1"
    lacp: active
    set:
      - "interface 0000:04:00.0 type=dpdk options:dpdk-devargs=0000:04:00.0"
      - "interface 0000:04:00.1 type=dpdk options:dpdk-devargs=0000:04:00.1"
    state: present
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


def _external_ids_to_dict(text):
    text = text.strip()

    if text == '{}':
        return None
    else:
        d = {}

        for kv in text[1:-1].split(','):
            kv = kv.strip()
            k, v = kv.split('=')
            d[k] = v

        return d


def _other_config_to_dict(text):
    text = text.strip()

    if text == '{}':
        return None
    else:
        d = {}

        for kv in text[1:-1].split(','):
            kv = kv.strip()
            k, v = kv.split('=')
            d[k] = v

        return d


def map_obj_to_commands(want, have, module):
    commands = list()

    if module.params['state'] == 'absent':
        if have:
            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s del-port"
                                   " %(bridge)s %(port)s")
            command = templatized_command % module.params
            commands.append(command)
    else:
        if have:
            if want['other_config'] != have['other_config']:
                for k, v in iteritems(want['other_config']):
                    if (not have['other_config']
                            or k not in have['other_config']
                            or want['other_config'][k] != have['other_config'][k]):
                        if v is None:
                            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                                   " remove port %(port)s"
                                                   " other_config " + k)
                            command = templatized_command % module.params
                            commands.append(command)
                        else:
                            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                                   " set port %(port)s"
                                                   " other_config:")
                            command = templatized_command % module.params
                            command += k + "=" + v
                            commands.append(command)

            if want['external_ids'] != have['external_ids']:
                for k, v in iteritems(want['external_ids']):
                    if (not have['external_ids']
                            or k not in have['external_ids']
                            or want['external_ids'][k] != have['external_ids'][k]):
                        if v is None:
                            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                                   " remove port %(port)s"
                                                   " external_ids " + k)
                            command = templatized_command % module.params
                            commands.append(command)
                        else:
                            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                                   " set port %(port)s"
                                                   " external_ids:")
                            command = templatized_command % module.params
                            command += k + "=" + v
                            commands.append(command)

        else:
            templatized_command = ("%(ovs-vsctl)s -t %(timeout)s add-bond"
                                   " %(bridge)s %(port)s")
            command = templatized_command % module.params

            if want['interfaces']:
                for interface in want['interfaces']:
                    command += " " + interface

            if want['bond_mode']:
                templatized_command = " bond_mode=%(bond_mode)s"
                command += templatized_command % module.params

            if want['lacp']:
                templatized_command = " lacp=%(lacp)s"
                command += templatized_command % module.params

            if want['bond_updelay']:
                templatized_command = " bond_updelay=%(bond_updelay)s"
                command += templatized_command % module.params

            if want['bond_downdelay']:
                templatized_command = " bond_downdelay=%(bond_downdelay)s"
                command += templatized_command % module.params

            if want['set']:
                for set in want['set']:
                    command += " -- set " + set

            commands.append(command)

            if want['other_config']:
                for k, v in iteritems(want['other_config']):
                    templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                           " set port %(port)s other_config:")
                    command = templatized_command % module.params
                    command += k + "=" + v
                    commands.append(command)

            if want['external_ids']:
                for k, v in iteritems(want['external_ids']):
                    templatized_command = ("%(ovs-vsctl)s -t %(timeout)s"
                                           " set port %(port)s external_ids:")
                    command = templatized_command % module.params
                    command += k + "=" + v
                    commands.append(command)

    return commands


def map_config_to_obj(module):
    templatized_command = "%(ovs-vsctl)s -t %(timeout)s list-ports %(bridge)s"
    command = templatized_command % module.params
    rc, out, err = module.run_command(command, check_rc=True)
    if rc != 0:
        module.fail_json(msg=err)

    obj = {}

    if module.params['port'] in out.splitlines():
        obj['bridge'] = module.params['bridge']
        obj['port'] = module.params['port']

        templatized_command = ("%(ovs-vsctl)s -t %(timeout)s get"
                               " Port %(port)s other_config")
        command = templatized_command % module.params
        rc, out, err = module.run_command(command, check_rc=True)
        obj['other_config'] = _other_config_to_dict(out)

        templatized_command = ("%(ovs-vsctl)s -t %(timeout)s get"
                               " Port %(port)s external_ids")
        command = templatized_command % module.params
        rc, out, err = module.run_command(command, check_rc=True)
        obj['external_ids'] = _external_ids_to_dict(out)

    return obj


def map_params_to_obj(module):
    obj = {
        'bridge': module.params['bridge'],
        'port': module.params['port'],
        'interfaces': module.params['interfaces'],
        'bond_mode': module.params['bond_mode'],
        'lacp': module.params['lacp'],
        'bond_updelay': module.params['bond_updelay'],
        'bond_downdelay': module.params['bond_downdelay'],
        'external_ids': module.params['external_ids'],
        'other_config': module.params['other_config'],
        'set': module.params['set']
    }

    return obj


def main():
    """ Entry point. """
    argument_spec = {
        'bridge': {'required': True},
        'port': {'required': True},
        'interfaces': {'type': 'list'},
        'bond_mode': {'default': None,
                      'choices': ['active-backup', 'balance-tcp', 'balance-slb']},
        'lacp': {'default': None, 'choices': ['active', 'passive', 'off']},
        'bond_updelay': {'default': None, 'type': 'int'},
        'bond_downdelay': {'default': None, 'type': 'int'},
        'state': {'default': 'present', 'choices': ['present', 'absent']},
        'timeout': {'default': 5, 'type': 'int'},
        'external_ids': {'default': None, 'type': 'dict'},
        'other_config': {'default': None, 'type': 'dict'},
        'set': {'required': False, 'type': 'list', 'default': None}
    }

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    # We add ovs-vsctl to module_params to later build up templatized commands
    module.params["ovs-vsctl"] = module.get_bin_path("ovs-vsctl", True)

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            for c in commands:
                module.run_command(c, check_rc=True)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
