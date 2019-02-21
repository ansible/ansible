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
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_router_rip
short_description: Configure RIP in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify router feature and rip category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
version_added: "2.8"
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
            - FortiOS or FortiGate ip address.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: true
    router_rip:
        description:
            - Configure RIP.
        default: null
        suboptions:
            default-information-originate:
                description:
                    - Enable/disable generation of default route.
                choices:
                    - enable
                    - disable
            default-metric:
                description:
                    - Default metric.
            distance:
                description:
                    - distance
                suboptions:
                    access-list:
                        description:
                            - Access list for route destination. Source router.access-list.name.
                    distance:
                        description:
                            - Distance (1 - 255).
                    id:
                        description:
                            - Distance ID.
                        required: true
                    prefix:
                        description:
                            - Distance prefix.
            distribute-list:
                description:
                    - Distribute list.
                suboptions:
                    direction:
                        description:
                            - Distribute list direction.
                        choices:
                            - in
                            - out
                    id:
                        description:
                            - Distribute list ID.
                        required: true
                    interface:
                        description:
                            - Distribute list interface name. Source system.interface.name.
                    listname:
                        description:
                            - Distribute access/prefix list name. Source router.access-list.name router.prefix-list.name.
                    status:
                        description:
                            - status
                        choices:
                            - enable
                            - disable
            garbage-timer:
                description:
                    - Garbage timer in seconds.
            interface:
                description:
                    - RIP interface configuration.
                suboptions:
                    auth-keychain:
                        description:
                            - Authentication key-chain name. Source router.key-chain.name.
                    auth-mode:
                        description:
                            - Authentication mode.
                        choices:
                            - none
                            - text
                            - md5
                    auth-string:
                        description:
                            - Authentication string/password.
                    flags:
                        description:
                            - flags
                    name:
                        description:
                            - Interface name. Source system.interface.name.
                        required: true
                    receive-version:
                        description:
                            - Receive version.
                        choices:
                            - 1
                            - 2
                    send-version:
                        description:
                            - Send version.
                        choices:
                            - 1
                            - 2
                    send-version2-broadcast:
                        description:
                            - Enable/disable broadcast version 1 compatible packets.
                        choices:
                            - disable
                            - enable
                    split-horizon:
                        description:
                            - Enable/disable split horizon.
                        choices:
                            - poisoned
                            - regular
                    split-horizon-status:
                        description:
                            - Enable/disable split horizon.
                        choices:
                            - enable
                            - disable
            max-out-metric:
                description:
                    - Maximum metric allowed to output(0 means 'not set').
            neighbor:
                description:
                    - neighbor
                suboptions:
                    id:
                        description:
                            - Neighbor entry ID.
                        required: true
                    ip:
                        description:
                            - IP address.
            network:
                description:
                    - network
                suboptions:
                    id:
                        description:
                            - Network entry ID.
                        required: true
                    prefix:
                        description:
                            - Network prefix.
            offset-list:
                description:
                    - Offset list.
                suboptions:
                    access-list:
                        description:
                            - Access list name. Source router.access-list.name.
                    direction:
                        description:
                            - Offset list direction.
                        choices:
                            - in
                            - out
                    id:
                        description:
                            - Offset-list ID.
                        required: true
                    interface:
                        description:
                            - Interface name. Source system.interface.name.
                    offset:
                        description:
                            - offset
                    status:
                        description:
                            - status
                        choices:
                            - enable
                            - disable
            passive-interface:
                description:
                    - Passive interface configuration.
                suboptions:
                    name:
                        description:
                            - Passive interface name. Source system.interface.name.
                        required: true
            recv-buffer-size:
                description:
                    - Receiving buffer size.
            redistribute:
                description:
                    - Redistribute configuration.
                suboptions:
                    metric:
                        description:
                            - Redistribute metric setting.
                    name:
                        description:
                            - Redistribute name.
                        required: true
                    routemap:
                        description:
                            - Route map name. Source router.route-map.name.
                    status:
                        description:
                            - status
                        choices:
                            - enable
                            - disable
            timeout-timer:
                description:
                    - Timeout timer in seconds.
            update-timer:
                description:
                    - Update timer in seconds.
            version:
                description:
                    - RIP version.
                choices:
                    - 1
                    - 2
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure RIP.
    fortios_router_rip:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_rip:
        default-information-originate: "enable"
        default-metric: "4"
        distance:
         -
            access-list: "<your_own_value> (source router.access-list.name)"
            distance: "7"
            id:  "8"
            prefix: "<your_own_value>"
        distribute-list:
         -
            direction: "in"
            id:  "12"
            interface: "<your_own_value> (source system.interface.name)"
            listname: "<your_own_value> (source router.access-list.name router.prefix-list.name)"
            status: "enable"
        garbage-timer: "16"
        interface:
         -
            auth-keychain: "<your_own_value> (source router.key-chain.name)"
            auth-mode: "none"
            auth-string: "<your_own_value>"
            flags: "21"
            name: "default_name_22 (source system.interface.name)"
            receive-version: "1"
            send-version: "1"
            send-version2-broadcast: "disable"
            split-horizon: "poisoned"
            split-horizon-status: "enable"
        max-out-metric: "28"
        neighbor:
         -
            id:  "30"
            ip: "<your_own_value>"
        network:
         -
            id:  "33"
            prefix: "<your_own_value>"
        offset-list:
         -
            access-list: "<your_own_value> (source router.access-list.name)"
            direction: "in"
            id:  "38"
            interface: "<your_own_value> (source system.interface.name)"
            offset: "40"
            status: "enable"
        passive-interface:
         -
            name: "default_name_43 (source system.interface.name)"
        recv-buffer-size: "44"
        redistribute:
         -
            metric: "46"
            name: "default_name_47"
            routemap: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        timeout-timer: "50"
        update-timer: "51"
        version: "1"
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

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_router_rip_data(json):
    option_list = ['default-information-originate', 'default-metric', 'distance',
                   'distribute-list', 'garbage-timer', 'interface',
                   'max-out-metric', 'neighbor', 'network',
                   'offset-list', 'passive-interface', 'recv-buffer-size',
                   'redistribute', 'timeout-timer', 'update-timer',
                   'version']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def router_rip(data, fos):
    vdom = data['vdom']
    router_rip_data = data['router_rip']
    flattened_data = flatten_multilists_attributes(router_rip_data)
    filtered_data = filter_router_rip_data(flattened_data)
    return fos.set('router',
                   'rip',
                   data=filtered_data,
                   vdom=vdom)


def fortios_router(data, fos):
    login(data)

    if data['router_rip']:
        resp = router_rip(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "router_rip": {
            "required": False, "type": "dict",
            "options": {
                "default-information-originate": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "default-metric": {"required": False, "type": "int"},
                "distance": {"required": False, "type": "list",
                             "options": {
                                 "access-list": {"required": False, "type": "str"},
                                 "distance": {"required": False, "type": "int"},
                                 "id": {"required": True, "type": "int"},
                                 "prefix": {"required": False, "type": "str"}
                             }},
                "distribute-list": {"required": False, "type": "list",
                                    "options": {
                                        "direction": {"required": False, "type": "str",
                                                      "choices": ["in", "out"]},
                                        "id": {"required": True, "type": "int"},
                                        "interface": {"required": False, "type": "str"},
                                        "listname": {"required": False, "type": "str"},
                                        "status": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]}
                                    }},
                "garbage-timer": {"required": False, "type": "int"},
                "interface": {"required": False, "type": "list",
                              "options": {
                                  "auth-keychain": {"required": False, "type": "str"},
                                  "auth-mode": {"required": False, "type": "str",
                                                "choices": ["none", "text", "md5"]},
                                  "auth-string": {"required": False, "type": "str"},
                                  "flags": {"required": False, "type": "int"},
                                  "name": {"required": True, "type": "str"},
                                  "receive-version": {"required": False, "type": "str",
                                                      "choices": ["1", "2"]},
                                  "send-version": {"required": False, "type": "str",
                                                   "choices": ["1", "2"]},
                                  "send-version2-broadcast": {"required": False, "type": "str",
                                                              "choices": ["disable", "enable"]},
                                  "split-horizon": {"required": False, "type": "str",
                                                    "choices": ["poisoned", "regular"]},
                                  "split-horizon-status": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]}
                              }},
                "max-out-metric": {"required": False, "type": "int"},
                "neighbor": {"required": False, "type": "list",
                             "options": {
                                 "id": {"required": True, "type": "int"},
                                 "ip": {"required": False, "type": "str"}
                             }},
                "network": {"required": False, "type": "list",
                            "options": {
                                "id": {"required": True, "type": "int"},
                                "prefix": {"required": False, "type": "str"}
                            }},
                "offset-list": {"required": False, "type": "list",
                                "options": {
                                    "access-list": {"required": False, "type": "str"},
                                    "direction": {"required": False, "type": "str",
                                                  "choices": ["in", "out"]},
                                    "id": {"required": True, "type": "int"},
                                    "interface": {"required": False, "type": "str"},
                                    "offset": {"required": False, "type": "int"},
                                    "status": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]}
                                }},
                "passive-interface": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "recv-buffer-size": {"required": False, "type": "int"},
                "redistribute": {"required": False, "type": "list",
                                 "options": {
                                     "metric": {"required": False, "type": "int"},
                                     "name": {"required": True, "type": "str"},
                                     "routemap": {"required": False, "type": "str"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]}
                                 }},
                "timeout-timer": {"required": False, "type": "int"},
                "update-timer": {"required": False, "type": "int"},
                "version": {"required": False, "type": "str",
                            "choices": ["1", "2"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_router(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
