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
module: fortios_system_wccp
short_description: Configure WCCP in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and wccp category.
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
    state:
        description:
            - Indicates whether to create or remove the object.
        type: str
        required: true
        choices:
            - present
            - absent
    system_wccp:
        description:
            - Configure WCCP.
        default: null
        type: dict
        suboptions:
            assignment_bucket_format:
                description:
                    - Assignment bucket format for the WCCP cache engine.
                type: str
                choices:
                    - wccp-v2
                    - cisco-implementation
            assignment_dstaddr_mask:
                description:
                    - Assignment destination address mask.
                type: str
            assignment_method:
                description:
                    - Hash key assignment preference.
                type: str
                choices:
                    - HASH
                    - MASK
                    - any
            assignment_srcaddr_mask:
                description:
                    - Assignment source address mask.
                type: str
            assignment_weight:
                description:
                    - Assignment of hash weight/ratio for the WCCP cache engine.
                type: int
            authentication:
                description:
                    - Enable/disable MD5 authentication.
                type: str
                choices:
                    - enable
                    - disable
            cache_engine_method:
                description:
                    - Method used to forward traffic to the routers or to return to the cache engine.
                type: str
                choices:
                    - GRE
                    - L2
            cache_id:
                description:
                    - IP address known to all routers. If the addresses are the same, use the default 0.0.0.0.
                type: str
            forward_method:
                description:
                    - Method used to forward traffic to the cache servers.
                type: str
                choices:
                    - GRE
                    - L2
                    - any
            group_address:
                description:
                    - IP multicast address used by the cache routers. For the FortiGate to ignore multicast WCCP traffic, use the default 0.0.0.0.
                type: str
            password:
                description:
                    - Password for MD5 authentication.
                type: str
            ports:
                description:
                    - Service ports.
                type: str
            ports_defined:
                description:
                    - Match method.
                type: str
                choices:
                    - source
                    - destination
            primary_hash:
                description:
                    - Hash method.
                type: str
                choices:
                    - src-ip
                    - dst-ip
                    - src-port
                    - dst-port
            priority:
                description:
                    - Service priority.
                type: int
            protocol:
                description:
                    - Service protocol.
                type: int
            return_method:
                description:
                    -  Method used to decline a redirected packet and return it to the FortiGate.
                type: str
                choices:
                    - GRE
                    - L2
                    - any
            router_id:
                description:
                    - IP address known to all cache engines. If all cache engines connect to the same FortiGate interface, use the default 0.0.0.0.
                type: str
            router_list:
                description:
                    - IP addresses of one or more WCCP routers.
                type: str
            server_list:
                description:
                    - IP addresses and netmasks for up to four cache servers.
                type: str
            server_type:
                description:
                    - Cache server type.
                type: str
                choices:
                    - forward
                    - proxy
            service_id:
                description:
                    - Service ID.
                type: str
            service_type:
                description:
                    - WCCP service type used by the cache server for logical interception and redirection of traffic.
                type: str
                choices:
                    - auto
                    - standard
                    - dynamic
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
  - name: Configure WCCP.
    fortios_system_wccp:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_wccp:
        assignment_bucket_format: "wccp-v2"
        assignment_dstaddr_mask: "<your_own_value>"
        assignment_method: "HASH"
        assignment_srcaddr_mask: "<your_own_value>"
        assignment_weight: "7"
        authentication: "enable"
        cache_engine_method: "GRE"
        cache_id: "<your_own_value>"
        forward_method: "GRE"
        group_address: "<your_own_value>"
        password: "<your_own_value>"
        ports: "<your_own_value>"
        ports_defined: "source"
        primary_hash: "src-ip"
        priority: "17"
        protocol: "18"
        return_method: "GRE"
        router_id: "<your_own_value>"
        router_list: "<your_own_value>"
        server_list: "<your_own_value>"
        server_type: "forward"
        service_id: "<your_own_value>"
        service_type: "auto"
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


def filter_system_wccp_data(json):
    option_list = ['assignment_bucket_format', 'assignment_dstaddr_mask', 'assignment_method',
                   'assignment_srcaddr_mask', 'assignment_weight', 'authentication',
                   'cache_engine_method', 'cache_id', 'forward_method',
                   'group_address', 'password', 'ports',
                   'ports_defined', 'primary_hash', 'priority',
                   'protocol', 'return_method', 'router_id',
                   'router_list', 'server_list', 'server_type',
                   'service_id', 'service_type']
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


def system_wccp(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_wccp_data = data['system_wccp']
    filtered_data = underscore_to_hyphen(filter_system_wccp_data(system_wccp_data))

    if state == "present":
        return fos.set('system',
                       'wccp',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'wccp',
                          mkey=filtered_data['service-id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_wccp']:
        resp = system_wccp(data, fos)

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
        "state": {"required": True, "type": "str",
                  "choices": ["present", "absent"]},
        "system_wccp": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "assignment_bucket_format": {"required": False, "type": "str",
                                             "choices": ["wccp-v2", "cisco-implementation"]},
                "assignment_dstaddr_mask": {"required": False, "type": "str"},
                "assignment_method": {"required": False, "type": "str",
                                      "choices": ["HASH", "MASK", "any"]},
                "assignment_srcaddr_mask": {"required": False, "type": "str"},
                "assignment_weight": {"required": False, "type": "int"},
                "authentication": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "cache_engine_method": {"required": False, "type": "str",
                                        "choices": ["GRE", "L2"]},
                "cache_id": {"required": False, "type": "str"},
                "forward_method": {"required": False, "type": "str",
                                   "choices": ["GRE", "L2", "any"]},
                "group_address": {"required": False, "type": "str"},
                "password": {"required": False, "type": "str"},
                "ports": {"required": False, "type": "str"},
                "ports_defined": {"required": False, "type": "str",
                                  "choices": ["source", "destination"]},
                "primary_hash": {"required": False, "type": "str",
                                 "choices": ["src-ip", "dst-ip", "src-port",
                                             "dst-port"]},
                "priority": {"required": False, "type": "int"},
                "protocol": {"required": False, "type": "int"},
                "return_method": {"required": False, "type": "str",
                                  "choices": ["GRE", "L2", "any"]},
                "router_id": {"required": False, "type": "str"},
                "router_list": {"required": False, "type": "str"},
                "server_list": {"required": False, "type": "str"},
                "server_type": {"required": False, "type": "str",
                                "choices": ["forward", "proxy"]},
                "service_id": {"required": False, "type": "str"},
                "service_type": {"required": False, "type": "str",
                                 "choices": ["auto", "standard", "dynamic"]}

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

            is_error, has_changed, result = fortios_system(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
