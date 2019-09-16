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
module: fortios_system_link_monitor
short_description: Configure Link Health Monitor in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and link_monitor category.
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
    system_link_monitor:
        description:
            - Configure Link Health Monitor.
        default: null
        type: dict
        suboptions:
            addr_mode:
                description:
                    - Address mode (IPv4 or IPv6).
                type: str
                choices:
                    - ipv4
                    - ipv6
            failtime:
                description:
                    - Number of retry attempts before the server is considered down (1 - 10)
                type: int
            gateway_ip:
                description:
                    - Gateway IP address used to probe the server.
                type: str
            gateway_ip6:
                description:
                    - Gateway IPv6 address used to probe the server.
                type: str
            ha_priority:
                description:
                    - HA election priority (1 - 50).
                type: int
            http_agent:
                description:
                    - String in the http-agent field in the HTTP header.
                type: str
            http_get:
                description:
                    - If you are monitoring an HTML server you can send an HTTP-GET request with a custom string. Use this option to define the string.
                type: str
            http_match:
                description:
                    - String that you expect to see in the HTTP-GET requests of the traffic to be monitored.
                type: str
            interval:
                description:
                    - Detection interval (1 - 3600 sec).
                type: int
            name:
                description:
                    - Link monitor name.
                required: true
                type: str
            packet_size:
                description:
                    - Packet size of a twamp test session,
                type: int
            password:
                description:
                    - Twamp controller password in authentication mode
                type: str
            port:
                description:
                    - Port number of the traffic to be used to monitor the server.
                type: int
            protocol:
                description:
                    - Protocols used to monitor the server.
                type: str
                choices:
                    - ping
                    - tcp-echo
                    - udp-echo
                    - http
                    - twamp
                    - ping6
            recoverytime:
                description:
                    - Number of successful responses received before server is considered recovered (1 - 10).
                type: int
            security_mode:
                description:
                    - Twamp controller security mode.
                type: str
                choices:
                    - none
                    - authentication
            server:
                description:
                    - IP address of the server(s) to be monitored.
                type: list
                suboptions:
                    address:
                        description:
                            - Server address.
                        required: true
                        type: str
            source_ip:
                description:
                    - Source IP address used in packet to the server.
                type: str
            source_ip6:
                description:
                    - Source IPv6 address used in packet to the server.
                type: str
            srcintf:
                description:
                    - Interface that receives the traffic to be monitored. Source system.interface.name.
                type: str
            status:
                description:
                    - Enable/disable this link monitor.
                type: str
                choices:
                    - enable
                    - disable
            update_cascade_interface:
                description:
                    - Enable/disable update cascade interface.
                type: str
                choices:
                    - enable
                    - disable
            update_static_route:
                description:
                    - Enable/disable updating the static route.
                type: str
                choices:
                    - enable
                    - disable
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
  - name: Configure Link Health Monitor.
    fortios_system_link_monitor:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_link_monitor:
        addr_mode: "ipv4"
        failtime: "4"
        gateway_ip: "<your_own_value>"
        gateway_ip6: "<your_own_value>"
        ha_priority: "7"
        http_agent: "<your_own_value>"
        http_get: "<your_own_value>"
        http_match: "<your_own_value>"
        interval: "11"
        name: "default_name_12"
        packet_size: "13"
        password: "<your_own_value>"
        port: "15"
        protocol: "ping"
        recoverytime: "17"
        security_mode: "none"
        server:
         -
            address: "<your_own_value>"
        source_ip: "84.230.14.43"
        source_ip6: "<your_own_value>"
        srcintf: "<your_own_value> (source system.interface.name)"
        status: "enable"
        update_cascade_interface: "enable"
        update_static_route: "enable"
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


def filter_system_link_monitor_data(json):
    option_list = ['addr_mode', 'failtime', 'gateway_ip',
                   'gateway_ip6', 'ha_priority', 'http_agent',
                   'http_get', 'http_match', 'interval',
                   'name', 'packet_size', 'password',
                   'port', 'protocol', 'recoverytime',
                   'security_mode', 'server', 'source_ip',
                   'source_ip6', 'srcintf', 'status',
                   'update_cascade_interface', 'update_static_route']
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


def system_link_monitor(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_link_monitor_data = data['system_link_monitor']
    filtered_data = underscore_to_hyphen(filter_system_link_monitor_data(system_link_monitor_data))

    if state == "present":
        return fos.set('system',
                       'link-monitor',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'link-monitor',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_link_monitor']:
        resp = system_link_monitor(data, fos)

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
        "system_link_monitor": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "addr_mode": {"required": False, "type": "str",
                              "choices": ["ipv4", "ipv6"]},
                "failtime": {"required": False, "type": "int"},
                "gateway_ip": {"required": False, "type": "str"},
                "gateway_ip6": {"required": False, "type": "str"},
                "ha_priority": {"required": False, "type": "int"},
                "http_agent": {"required": False, "type": "str"},
                "http_get": {"required": False, "type": "str"},
                "http_match": {"required": False, "type": "str"},
                "interval": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "packet_size": {"required": False, "type": "int"},
                "password": {"required": False, "type": "str"},
                "port": {"required": False, "type": "int"},
                "protocol": {"required": False, "type": "str",
                             "choices": ["ping", "tcp-echo", "udp-echo",
                                         "http", "twamp", "ping6"]},
                "recoverytime": {"required": False, "type": "int"},
                "security_mode": {"required": False, "type": "str",
                                  "choices": ["none", "authentication"]},
                "server": {"required": False, "type": "list",
                           "options": {
                               "address": {"required": True, "type": "str"}
                           }},
                "source_ip": {"required": False, "type": "str"},
                "source_ip6": {"required": False, "type": "str"},
                "srcintf": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "update_cascade_interface": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "update_static_route": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]}

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
