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
module: exos_vlan
version_added: "2.8"
author: "Ruturaj Vyawahare (@ruturajvy)"
short_description: Manage VLANs on Extreme Networks EXOS VLAN configuration.
description:
  - This module provides declarative management of VLANs on Extreme EXOS network devices
notes:
  - Tested against EXOS 30.1.1.4
options:
  name:
    description:
      - Name of the VLAN.
  vlan_id:
    description:
      - ID of the VLAN. Range 1-4094.
    required: true
  interfaces:
    description:
      - List of interfaces that should be associated to the VLAN.
    required: true
  delay:
    description:
      - Delay the play should wait to check for declarative intent params values with default of 10 ms
    default: 10
  aggregate:
    description: List of VLANs definitions to be configured
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
    type: bool
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Create vlan
  exos_vlan:
    vlan_id: 100
    name: test-vlan
    state: present

- name: Add interfaces to VLAN
  exos_vlan:
    vlan_id: 100
    interfaces:
      - 1
      - 2

- name: Delete vlan
  exos_vlan:
    vlan_id: 100
    state: absent

- name: Create a VLAN configuration using aggregate
  exos_vlan:
    aggregate:
      - { vlan_id: 300, name: test_vlan_1 }
      - { vlan_id: 400, name: test_vlan_2 }
    state: present
"""

RETURN = """
requests:
  description: Configuration difference in terms of POST, PATCH and DELETE requests
  returned: always
  type: list
  sample: |
    [
      {
        "data": {
          "openconfig-vlan:vlan": [
            {
              "config": {
                "name": "ansible_100",
                "status": "ACTIVE",
                "tpid": "oc-vlan-types:TPID_0x8100",
                "vlan-id": 100
              }
            }
          ]
        },
        "method": "POST",
        "path": "/rest/restconf/data/openconfig-vlan:vlans/"
      },
      {
        "data": {
          "openconfig-vlan:vlan": [
            {
              "config": {
                "name": "ansible_200",
                "status": "ACTIVE",
                "tpid": "oc-vlan-types:TPID_0x8100",
                "vlan-id": 200
              }
            }
          ]
        },
        "method": "POST",
        "path": "/rest/restconf/data/openconfig-vlan:vlans/"
      }
    ]
"""
import time
import json
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.exos.exos import send_requests


# Base path for the RESTconf API endpoint
def get_vlan_path():
    vlan_path = "/rest/restconf/data/openconfig-vlan:vlans/"
    return vlan_path


def get_interface_path(interface):
    if_base = '/rest/restconf/data/openconfig-interfaces:interfaces/interface='
    if_end = '/openconfig--if-ethernet:ethernet/openconfig-vlan:switched-vlan/'
    interface_path = if_base + str(interface) + if_end
    return interface_path


# Returns a JSON formatted body for POST and PATCH requests for vlan configuration
def make_vlan_body(vlan_id, name):
    vlan_body = {
        "openconfig-vlan:vlan": [{
            "config": {
                "vlan-id": None,
                "status": "ACTIVE",
                "tpid": "oc-vlan-types:TPID_0x8100",
                "name": None
            }
        }]
    }
    vlan_config = vlan_body["openconfig-vlan:vlan"][0]['config']
    vlan_config['vlan-id'] = vlan_id
    vlan_config['name'] = name
    return json.dumps(vlan_body)


def make_interface_body(vlan_id):
    vlan_body = {
        "openconfig-vlan:switched-vlan": {
            "config": {
                "access-vlan": vlan_id,
                "interface-mode": "ACCESS"
            }
        }
    }
    return json.dumps(vlan_body)


# Maps current config to a list of dicts each containing vlan_id, name and interfaces(list)
def map_config_to_list(module):
    path = get_vlan_path()
    requests = [{"path": path}]
    resp = send_requests(module, requests=requests)
    old_config_list = list()
    for vlan_json in resp:
        for vlan in vlan_json['openconfig-vlan:vlans']['vlan']:
            interfaces = []
            if 'members' in vlan:
                for member in vlan['members']['member']:
                    interfaces.append(member['interface-ref']['state']['interface'])

            old_config_list.append({"name": vlan['config']['name'],
                                    "vlan_id": vlan['config']['vlan-id'],
                                    "interfaces": interfaces})
    return old_config_list


# Maps module params to a list of dicts each containing vlan_id, name and interfaces(list)
def map_params_to_list(module):
    params = module.params
    new_config_list = list()
    aggregate = params['aggregate']
    if aggregate:
        # Completes each dictionary with the common parameters in the element spec
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]
            d = item.copy()
            d['vlan_id'] = int(d['vlan_id'])
            validate_vlan_id(module, d['vlan_id'])
            new_config_list.append(d)
    else:
        validate_vlan_id(module, int(params['vlan_id']))
        new_config_list.append({"vlan_id": int(params['vlan_id']),
                                "name": params['name'],
                                "interfaces": params['interfaces'],
                                "state": params['state']})
    return new_config_list


# Returns the vlan object from the list if the vlan_id is present in it
def search_vlan_in_list(vlan_id, lst):
    for o in lst:
        if o['vlan_id'] == vlan_id:
            return o
    return None


# Returns a list requests after comparing old and new config
def map_diff_to_requests(module, old_config_list, new_config_list):
    requests = list()
    purge = module.params['purge']
    for new_config in new_config_list:
        vlan_id = new_config['vlan_id']
        name = new_config['name']
        interfaces = None
        if new_config['interfaces']:
            interfaces = [str(item) for item in new_config['interfaces']]
        state = new_config['state']
        if name:
            for old_vlan in old_config_list:
                if name == old_vlan['name'] and vlan_id != old_vlan['vlan_id']:
                    module.fail_json(msg="VLAN %s is already configured with the name %s."
                                     % (old_vlan['vlan_id'], name))
        # Check if the VLAN is already configured
        old_vlan_dict = search_vlan_in_list(vlan_id, old_config_list)
        if state == 'absent':
            if old_vlan_dict:
                path = get_vlan_path() + "vlan=" + str(vlan_id)
                requests.append({"path": path,
                                 "method": "DELETE"})
        elif state == 'present':
            if not old_vlan_dict:
                if name:
                    path = get_vlan_path()
                    body = make_vlan_body(vlan_id, name)
                    requests.append({"path": path,
                                     "method": "POST",
                                     "data": body})
                if interfaces:
                    for interface in interfaces:
                        path = get_interface_path(interface)
                        body = make_interface_body(vlan_id)
                        requests.append({"path": path,
                                         "method": "PATCH",
                                         "data": body})
            else:
                if name:
                    if name != old_vlan_dict['name']:
                        path = get_vlan_path() + 'vlan=' + str(vlan_id)
                        body = make_vlan_body(vlan_id, name)
                        requests.append({"path": path,
                                         "method": "PATCH",
                                         "data": body})
                if interfaces:
                    if not old_vlan_dict['interfaces']:
                        for interface in interfaces:
                            path = get_interface_path(interface)
                            body = make_interface_body(vlan_id)
                            requests.append({"path": path,
                                             "method": "PATCH",
                                             "data": body})

                    elif set(interfaces) != set(old_vlan_dict['interfaces']):
                        missing_interfaces = list(set(interfaces) - set(old_vlan_dict['interfaces']))
                        for interface in missing_interfaces:
                            path = get_interface_path(interface)
                            body = make_interface_body(vlan_id)
                            requests.append({"path": path,
                                             "method": "PATCH",
                                             "data": body})

                        superfluous_interfaces = list(set(old_vlan_dict['interfaces']) - set(interfaces))
                        for interface in superfluous_interfaces:
                            path = get_interface_path("1")
                            body = make_interface_body(1)
                            requests.append({"path": path,
                                             "method": "PATCH",
                                             "data": body})
    if purge:
        for old_config in old_config_list:
            new_vlan_dict = search_vlan_in_list(old_config['vlan_id'], new_config_list)
            if new_vlan_dict is None and old_config['name'] != 'Default':
                path = get_vlan_path() + "vlan=" + str(old_config['vlan_id'])
                requests.append({"path": path,
                                 "method": "DELETE"})

    return requests


# Sends the HTTP requests to the switch API endpoints
def change_configuration(module, requests):
    send_requests(module, requests=requests)


# Sanity check for the VLAN ID
def validate_vlan_id(module, vlan):
    if vlan and not 1 <= int(vlan) <= 4094:
        module.fail_json(msg='vlan_id must be between 1 and 4094')


# To check after a delay that the interfaces are in the VLAN
def check_declarative_intent_params(new_config_list, module):
    if module.params['interfaces']:
        time.sleep(module.params['delay'])

        old_config_list = map_config_to_list(module)
        for newconfs in new_config_list:
            for i in newconfs['interfaces']:
                vlan_dict = search_vlan_in_list(newconfs['vlan_id'], old_config_list)
                if vlan_dict and 'interfaces' in vlan_dict and str(i) not in vlan_dict['interfaces']:
                    module.fail_json(msg="Interface %s not configured on vlan %s" % (i, newconfs['vlan_id']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        vlan_id=dict(type='int'),
        name=dict(),
        interfaces=dict(type='list'),
        delay=dict(default=10, type='int'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['vlan_id'] = dict(type='int', required=True)

    # Removes default values from aggregate spec
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
    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    old_config_list = map_config_to_list(module)
    new_config_list = map_params_to_list(module)

    requests = map_diff_to_requests(module, old_config_list, new_config_list)
    result['requests'] = requests

    if requests:
        if not module.check_mode:
            change_configuration(module, requests)
        for request in requests:
            if 'data' in request:
                if request['data']:
                    request['data'] = json.loads(request['data'])
        result['changed'] = True

    if result['changed']:
        check_declarative_intent_params(new_config_list, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
