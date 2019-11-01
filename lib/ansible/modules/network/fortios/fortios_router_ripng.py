#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_router_ripng
short_description: Configure RIPng in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify router feature and ripng category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.9"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
        description:
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
    router_ripng:
        description:
            - Configure RIPng.
        default: null
        type: dict
        suboptions:
            aggregate_address:
                description:
                    - Aggregate address.
                type: list
                suboptions:
                    id:
                        description:
                            - Aggregate address entry ID.
                        required: true
                        type: int
                    prefix6:
                        description:
                            - Aggregate address prefix.
                        type: str
            default_information_originate:
                description:
                    - Enable/disable generation of default route.
                type: str
                choices:
                    - enable
                    - disable
            default_metric:
                description:
                    - Metric that the FortiGate unit advertises to adjacent routers.
                type: int
            distance:
                description:
                    - Administrative distance
                type: list
                suboptions:
                    access_list6:
                        description:
                            - Access list for route destination. Source router.access-list6.name.
                        type: str
                    distance:
                        description:
                            - Distance (1 - 255).
                        type: int
                    id:
                        description:
                            - Distance ID.
                        required: true
                        type: int
                    prefix6:
                        description:
                            - Distance prefix6.
                        type: str
            distribute_list:
                description:
                    - Use this to filter incoming or outgoing updates using an access list or a prefix list.
                type: list
                suboptions:
                    direction:
                        description:
                            - Distribute list direction.
                        type: str
                        choices:
                            - in
                            - out
                    id:
                        description:
                            - Distribute list ID.
                        required: true
                        type: int
                    interface:
                        description:
                            - Distribute list interface name. Source system.interface.name.
                        type: str
                    listname:
                        description:
                            - Distribute access/prefix list name. Source router.access-list6.name router.prefix-list6.name.
                        type: str
                    status:
                        description:
                            - Use this to activate or deactivate
                        type: str
                        choices:
                            - enable
                            - disable
            garbage_timer:
                description:
                    - Time in seconds that must elapse after the timeout interval for a route expires,.
                type: int
            interface:
                description:
                    - RIPng interface configuration.
                type: list
                suboptions:
                    flags:
                        description:
                            - Configuration flags of the interface.
                        type: int
                    name:
                        description:
                            - Interface name. Source system.interface.name.
                        required: true
                        type: str
                    split_horizon:
                        description:
                            - Configure RIP to use either regular or poisoned split horizon on this interface.
                        type: str
                        choices:
                            - poisoned
                            - regular
                    split_horizon_status:
                        description:
                            - Enable/disable split horizon.
                        type: str
                        choices:
                            - enable
                            - disable
            max_out_metric:
                description:
                    - Maximum metric allowed to output(0 means 'not set').
                type: int
            neighbor:
                description:
                    - List of neighbors.
                type: list
                suboptions:
                    id:
                        description:
                            - Neighbor entry ID.
                        required: true
                        type: int
                    interface:
                        description:
                            - Interface name. Source system.interface.name.
                        type: str
                    ip6:
                        description:
                            - IPv6 link-local address.
                        type: str
            network:
                description:
                    - list of networks connected.
                type: list
                suboptions:
                    id:
                        description:
                            - Network entry ID.
                        required: true
                        type: int
                    prefix:
                        description:
                            - Network IPv6 link-local prefix.
                        type: str
            offset_list:
                description:
                    - Adds the specified offset to the metric (hop count) of a route.
                type: list
                suboptions:
                    access_list6:
                        description:
                            - IPv6 access list name. Source router.access-list6.name.
                        type: str
                    direction:
                        description:
                            - Offset list direction.
                        type: str
                        choices:
                            - in
                            - out
                    id:
                        description:
                            - Offset-list ID.
                        required: true
                        type: int
                    interface:
                        description:
                            - Interface name. Source system.interface.name.
                        type: str
                    offset:
                        description:
                            - Offset range
                        type: int
                    status:
                        description:
                            - Indicates if the offset is active or not
                        type: str
                        choices:
                            - enable
                            - disable
            passive_interface:
                description:
                    - Passive interface configuration.
                type: list
                suboptions:
                    name:
                        description:
                            - Passive interface name. Source system.interface.name.
                        required: true
                        type: str
            redistribute:
                description:
                    - Redistribute configuration.
                type: list
                suboptions:
                    metric:
                        description:
                            - Redistribute metric setting.
                        type: int
                    name:
                        description:
                            - Redistribute name.
                        required: true
                        type: str
                    routemap:
                        description:
                            - Route map name. Source router.route-map.name.
                        type: str
                    status:
                        description:
                            - Indicates if the redistribute is active or not
                        type: str
                        choices:
                            - enable
                            - disable
            timeout_timer:
                description:
                    - Time interval in seconds after which a route is declared unreachable.
                type: int
            update_timer:
                description:
                    - The time interval in seconds between RIP updates.
                type: int
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
   ssl_verify: "False"
  tasks:
  - name: Configure RIPng.
    fortios_router_ripng:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_ripng:
        aggregate_address:
         -
            id:  "4"
            prefix6: "<your_own_value>"
        default_information_originate: "enable"
        default_metric: "7"
        distance:
         -
            access_list6: "<your_own_value> (source router.access-list6.name)"
            distance: "10"
            id:  "11"
            prefix6: "<your_own_value>"
        distribute_list:
         -
            direction: "in"
            id:  "15"
            interface: "<your_own_value> (source system.interface.name)"
            listname: "<your_own_value> (source router.access-list6.name router.prefix-list6.name)"
            status: "enable"
        garbage_timer: "19"
        interface:
         -
            flags: "21"
            name: "default_name_22 (source system.interface.name)"
            split_horizon: "poisoned"
            split_horizon_status: "enable"
        max_out_metric: "25"
        neighbor:
         -
            id:  "27"
            interface: "<your_own_value> (source system.interface.name)"
            ip6: "<your_own_value>"
        network:
         -
            id:  "31"
            prefix: "<your_own_value>"
        offset_list:
         -
            access_list6: "<your_own_value> (source router.access-list6.name)"
            direction: "in"
            id:  "36"
            interface: "<your_own_value> (source system.interface.name)"
            offset: "38"
            status: "enable"
        passive_interface:
         -
            name: "default_name_41 (source system.interface.name)"
        redistribute:
         -
            metric: "43"
            name: "default_name_44"
            routemap: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        timeout_timer: "47"
        update_timer: "48"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_router_ripng_data(json):
    option_list = ['aggregate_address', 'default_information_originate', 'default_metric',
                   'distance', 'distribute_list', 'garbage_timer',
                   'interface', 'max_out_metric', 'neighbor',
                   'network', 'offset_list', 'passive_interface',
                   'redistribute', 'timeout_timer', 'update_timer']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def router_ripng(data, fos):
    vdom = data['vdom']
    router_ripng_data = data['router_ripng']
    filtered_data = underscore_to_hyphen(filter_router_ripng_data(router_ripng_data))

    return fos.set('router',
                   'ripng',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_router(data, fos):

    if data['router_ripng']:
        resp = router_ripng(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "router_ripng": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "aggregate_address": {"required": False, "type": "list",
                                      "options": {
                                          "id": {"required": True, "type": "int"},
                                          "prefix6": {"required": False, "type": "str"}
                                      }},
                "default_information_originate": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "default_metric": {"required": False, "type": "int"},
                "distance": {"required": False, "type": "list",
                             "options": {
                                 "access_list6": {"required": False, "type": "str"},
                                 "distance": {"required": False, "type": "int"},
                                 "id": {"required": True, "type": "int"},
                                 "prefix6": {"required": False, "type": "str"}
                             }},
                "distribute_list": {"required": False, "type": "list",
                                    "options": {
                                        "direction": {"required": False, "type": "str",
                                                      "choices": ["in", "out"]},
                                        "id": {"required": True, "type": "int"},
                                        "interface": {"required": False, "type": "str"},
                                        "listname": {"required": False, "type": "str"},
                                        "status": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]}
                                    }},
                "garbage_timer": {"required": False, "type": "int"},
                "interface": {"required": False, "type": "list",
                              "options": {
                                  "flags": {"required": False, "type": "int"},
                                  "name": {"required": True, "type": "str"},
                                  "split_horizon": {"required": False, "type": "str",
                                                    "choices": ["poisoned", "regular"]},
                                  "split_horizon_status": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]}
                              }},
                "max_out_metric": {"required": False, "type": "int"},
                "neighbor": {"required": False, "type": "list",
                             "options": {
                                 "id": {"required": True, "type": "int"},
                                 "interface": {"required": False, "type": "str"},
                                 "ip6": {"required": False, "type": "str"}
                             }},
                "network": {"required": False, "type": "list",
                            "options": {
                                "id": {"required": True, "type": "int"},
                                "prefix": {"required": False, "type": "str"}
                            }},
                "offset_list": {"required": False, "type": "list",
                                "options": {
                                    "access_list6": {"required": False, "type": "str"},
                                    "direction": {"required": False, "type": "str",
                                                  "choices": ["in", "out"]},
                                    "id": {"required": True, "type": "int"},
                                    "interface": {"required": False, "type": "str"},
                                    "offset": {"required": False, "type": "int"},
                                    "status": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]}
                                }},
                "passive_interface": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "redistribute": {"required": False, "type": "list",
                                 "options": {
                                     "metric": {"required": False, "type": "int"},
                                     "name": {"required": True, "type": "str"},
                                     "routemap": {"required": False, "type": "str"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]}
                                 }},
                "timeout_timer": {"required": False, "type": "int"},
                "update_timer": {"required": False, "type": "int"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_router(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_router(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
