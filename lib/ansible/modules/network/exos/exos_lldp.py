#!/usr/bin/python
#
# (c) 2019 Extreme Networks Inc.
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: exos_lldp
version_added: "2.9"
author: "Ruturaj Vyawahare (@ruturajvy)"
short_description: Manage LLDP configuration on Extreme Networks EXOS network devices.
description:
  - This module provides declarative management of LLDP service
    on Extreme EXOS network devices.
notes:
  - Tested against EXOS 30.2.1.8
options:
  interfaces:
    description:
      - The list of interfaces on which the declared LLDP configuration should take effect.
  state:
    description:
      - State of the LLDP configuration. If value is I(present) lldp will be enabled
        else if it is I(absent) it will be disabled.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Enable LLDP service on interfaces 1-10 and interface 15
  exos_lldp:
    interfaces: 1:1-10, 1:1-1:10
    state: present

- name: Enable LLDP service on stacked interfaces 1:1 to 1:10
  exos_lldp:
    interfaces: 1:1-1:10
    state: present

- name: Disable LLDP service on interfaces 15 and 16
  exos_lldp:
    interfaces: 15,16
    state: absent
"""

RETURN = """
requests:
  description: The list of http requests to send to the device.
  returned: always
  type: list
  sample:
    -
"""
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.exos.exos import send_requests
from copy import deepcopy


def get_interface_endpoint(interface):
    end_point = '/rest/restconf/data/openconfig-lldp:lldp/interfaces/interface=' + str(interface) + '/config'
    return end_point


def get_all_interfaces(module):
    interface_json = send_requests(module, requests=[{"path": "/rest/restconf/data/openconfig-interfaces:interfaces?depth=4"}])
    interface_set = set()
    for interface in interface_json[0]["openconfig-interfaces:interfaces"]["interface"]:
        if interface["config"]["type"] == "ethernetCsmacd":
            interface_set.add(interface['name'])
    return interface_set


def validate_interface_params(module, valid_interfaces, interface_list):
    if set(interface_list).difference(valid_interfaces):
        module.fail_json(msg="Invalid interface")


def interfaces_range_to_list(interfaces, valid_interfaces):
    result = []
    if interfaces:
        for part in interfaces.split(','):
            if part == 'none':
                break
            if '-' in part:
                if ':' in part:
                    start, stop = part.split('-')
                    start_l, start_r = start.split(':')
                    stop_l, stop_r = stop.split(':')
                    tuples = [tuple(item.split(':')) for item in valid_interfaces]
                    for root in range(int(start_l), int(stop_l) + 1):
                        max_for_root = int(max([item for item in tuples if int(item[0]) == root], key=lambda x: int(x[1]))[1])
                        if start_l == stop_l:
                            for leaf in range(int(start_r), int(stop_r) + 1):
                                result.append(':'.join([str(root), str(leaf)]))
                        elif root == int(start_l):
                            for leaf in range(int(start_r), max_for_root + 1):
                                result.append(':'.join([str(root), str(leaf)]))
                        elif root == int(stop_l):
                            for leaf in range(1, int(stop_r) + 1):
                                result.append(':'.join([str(root), str(leaf)]))
                        else:
                            for leaf in range(1, max_for_root + 1):
                                result.append(':'.join([str(root), str(leaf)]))

                else:
                    start, stop = (int(i) for i in part.split('-'))
                    result.extend([str(i) for i in range(start, stop + 1)])
            else:
                result.append(part.strip())
    return result


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        interfaces=dict(type=str, required=True),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings
    state = module.params['state']
    requests = []
    valid_interfaces = get_all_interfaces(module)
    interface_list = interfaces_range_to_list(module.params['interfaces'], valid_interfaces)
    validate_interface_params(module, valid_interfaces, interface_list)
    for interface in interface_list:
        interface_endpoint = get_interface_endpoint(interface)
        running = send_requests(module, requests=[{"path": interface_endpoint}])[0]
        if state == 'present':
            if not running["openconfig-lldp:config"]["enabled"]:
                candidate = deepcopy(running)
                candidate["openconfig-lldp:config"]["enabled"] = True
                requests.append({"path": get_interface_endpoint(interface), "method": "PATCH", "data": json.dumps(candidate)})
        else:
            if running["openconfig-lldp:config"]["enabled"]:
                candidate = deepcopy(running)
                candidate["openconfig-lldp:config"]["enabled"] = False
                requests.append({"path": get_interface_endpoint(interface), "method": "PATCH", "data": json.dumps(candidate)})

    result['requests'] = requests

    if requests:
        if not module.check_mode:
            send_requests(module, requests=requests)
        for request in requests:
            request["data"] = json.loads(request["data"])
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
