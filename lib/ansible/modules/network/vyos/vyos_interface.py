#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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


DOCUMENTATION = """
---
module: vyos_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Interface on VyOS network devices
description:
  - This module provides declarative management of Interfaces
    on VyOS network devices.
notes:
  - Tested against VYOS 1.1.7
options:
  name:
    description:
      - Name of the Interface.
    required: true
  description:
    description:
      - Description of Interface.
  enabled:
    description:
      - Interface link status.
  speed:
    description:
      - Interface link speed.
  mtu:
    description:
      - Maximum size of transmit packet.
  duplex:
    description:
      - Interface link status.
    default: auto
    choices: ['full', 'half', 'auto']
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state argument which are
        I(state) with values C(up)/C(down) and I(neighbors).
    default: 10
  neighbors:
    description:
      - Check the operational state of given interface C(name) for LLDP neighbor.
      - The following suboptions are available.
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
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    choices: ['present', 'absent', 'up', 'down']
extends_documentation_fragment: vyos
"""

EXAMPLES = """
- name: configure interface
  vyos_interface:
    name: eth0
    description: test-interface

- name: remove interface
  vyos_interface:
    name: eth0
    state: absent

- name: make interface down
  vyos_interface:
    name: eth0
    enabled: False

- name: make interface up
  vyos_interface:
    name: eth0
    enabled: True

- name: Configure interface speed, mtu, duplex
  vyos_interface:
    name: eth5
    state: present
    speed: 100
    mtu: 256
    duplex: full

- name: Set interface using aggregate
  vyos_interface:
    aggregate:
      - { name: eth1, description: test-interface-1,  speed: 100, duplex: half, mtu: 512}
      - { name: eth2, description: test-interface-2,  speed: 1000, duplex: full, mtu: 256}

- name: Disable interface on aggregate
  net_interface:
    aggregate:
      - name: eth1
      - name: eth2
    enabled: False

- name: Delete interface using aggregate
  net_interface:
    aggregate:
      - name: eth1
      - name: eth2
    state: absent

- name: Check lldp neighbors intent arguments
  vyos_interface:
    name: eth0
    neighbors:
    - port: eth0
      host: netdev

- name: Config + intent
  vyos_interface:
    name: eth1
    enabled: False
    state: down
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - set interfaces ethernet eth0 description "test-interface"
    - set interfaces ethernet eth0 speed 100
    - set interfaces ethernet eth0 mtu 256
    - set interfaces ethernet eth0 duplex full
"""
import re

from copy import deepcopy
from time import sleep

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.common.utils import conditional, remove_default_spec
from ansible.module_utils.network.vyos.vyos import load_config, get_config
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def map_obj_to_commands(updates):
    commands = list()
    want, have = updates

    params = ('speed', 'description', 'duplex', 'mtu')
    for w in want:
        name = w['name']
        disable = w['disable']
        state = w['state']

        obj_in_have = search_obj_in_list(name, have)
        set_interface = 'set interfaces ethernet ' + name
        delete_interface = 'delete interfaces ethernet ' + name

        if state == 'absent' and obj_in_have:
            commands.append(delete_interface)
        elif state in ('present', 'up', 'down'):
            if obj_in_have:
                for item in params:
                    value = w.get(item)

                    if value and value != obj_in_have.get(item):
                        commands.append(set_interface + ' ' + item + ' ' + str(value))

                if disable and not obj_in_have.get('disable', False):
                    commands.append(set_interface + ' disable')
                elif not disable and obj_in_have.get('disable', False):
                    commands.append(delete_interface + ' disable')
            else:
                commands.append(set_interface)
                for item in params:
                    value = w.get(item)
                    if value:
                        commands.append(set_interface + ' ' + item + ' ' + str(value))

                if disable:
                    commands.append(set_interface + ' disable')
    return commands


def map_config_to_obj(module):
    data = get_config(module)
    obj = []
    for line in data.split('\n'):
        if line.startswith('set interfaces ethernet'):
            match = re.search(r'set interfaces ethernet (\S+)', line, re.M)
            name = match.group(1)
            if name:
                interface = {}
                for item in obj:
                    if item['name'] == name:
                        interface = item
                        break

                if not interface:
                    interface = {'name': name}
                    obj.append(interface)

                match = re.search(r'%s (\S+)' % name, line, re.M)
                if match:
                    param = match.group(1)
                    if param == 'description':
                        match = re.search(r'description (\S+)', line, re.M)
                        description = match.group(1).strip("'")
                        interface['description'] = description
                    elif param == 'speed':
                        match = re.search(r'speed (\S+)', line, re.M)
                        speed = match.group(1).strip("'")
                        interface['speed'] = speed
                    elif param == 'mtu':
                        match = re.search(r'mtu (\S+)', line, re.M)
                        mtu = match.group(1).strip("'")
                        interface['mtu'] = int(mtu)
                    elif param == 'duplex':
                        match = re.search(r'duplex (\S+)', line, re.M)
                        duplex = match.group(1).strip("'")
                        interface['duplex'] = duplex
                    elif param.strip("'") == 'disable':
                        interface['disable'] = True

    return obj


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            if d['enabled']:
                d['disable'] = False
            else:
                d['disable'] = True

            obj.append(d)
    else:
        params = {
            'name': module.params['name'],
            'description': module.params['description'],
            'speed': module.params['speed'],
            'mtu': module.params['mtu'],
            'duplex': module.params['duplex'],
            'delay': module.params['delay'],
            'state': module.params['state'],
            'neighbors': module.params['neighbors']
        }

        if module.params['enabled']:
            params.update({'disable': False})
        else:
            params.update({'disable': True})

        obj.append(params)
    return obj


def check_declarative_intent_params(module, want, result):
    failed_conditions = []
    have_neighbors = None
    for w in want:
        want_state = w.get('state')
        want_neighbors = w.get('neighbors')

        if want_state not in ('up', 'down') and not want_neighbors:
            continue

        if result['changed']:
            sleep(w['delay'])

        command = 'show interfaces ethernet %s' % w['name']
        rc, out, err = exec_command(module, command)
        if rc != 0:
            module.fail_json(msg=to_text(err, errors='surrogate_then_replace'), command=command, rc=rc)

        if want_state in ('up', 'down'):
            match = re.search(r'%s (\w+)' % 'state', out, re.M)
            have_state = None
            if match:
                have_state = match.group(1)
            if have_state is None or not conditional(want_state, have_state.strip().lower()):
                failed_conditions.append('state ' + 'eq(%s)' % want_state)

        if want_neighbors:
            have_host = []
            have_port = []
            if have_neighbors is None:
                rc, have_neighbors, err = exec_command(module, 'show lldp neighbors detail')
                if rc != 0:
                    module.fail_json(msg=to_text(err, errors='surrogate_then_replace'), command=command, rc=rc)

            if have_neighbors:
                lines = have_neighbors.strip().split('Interface: ')
                for line in lines:
                    field = line.split('\n')
                    if field[0].split(',')[0].strip() == w['name']:
                        for item in field:
                            if item.strip().startswith('SysName:'):
                                have_host.append(item.split(':')[1].strip())
                            if item.strip().startswith('PortDescr:'):
                                have_port.append(item.split(':')[1].strip())
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
        name=dict(),
        description=dict(),
        speed=dict(),
        mtu=dict(type='int'),
        duplex=dict(choices=['full', 'half', 'auto']),
        enabled=dict(default=True, type='bool'),
        neighbors=dict(type='list', elements='dict', options=neighbors_spec),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(vyos_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]

    required_together = (['speed', 'duplex'])
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           required_together=required_together,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have))
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        diff = load_config(module, commands, commit=commit)
        if diff:
            if module._diff:
                result['diff'] = {'prepared': diff}
        result['changed'] = True

    failed_conditions = check_declarative_intent_params(module, want, result)

    if failed_conditions:
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)
    module.exit_json(**result)

if __name__ == '__main__':
    main()
