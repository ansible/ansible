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
module: fortios_firewall_service_custom
short_description: Configure custom services in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall_service feature and custom category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
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
        version_added: 2.9
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    firewall_service_custom:
        description:
            - Configure custom services.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            app_category:
                description:
                    - Application category ID.
                type: list
                suboptions:
                    id:
                        description:
                            - Application category id.
                        required: true
                        type: int
            app_service_type:
                description:
                    - Application service type.
                type: str
                choices:
                    - disable
                    - app-id
                    - app-category
            application:
                description:
                    - Application ID.
                type: list
                suboptions:
                    id:
                        description:
                            - Application id.
                        required: true
                        type: int
            category:
                description:
                    - Service category. Source firewall.service.category.name.
                type: str
            check_reset_range:
                description:
                    - Configure the type of ICMP error message verification.
                type: str
                choices:
                    - disable
                    - strict
                    - default
            color:
                description:
                    - Color of icon on the GUI.
                type: int
            comment:
                description:
                    - Comment.
                type: str
            fqdn:
                description:
                    - Fully qualified domain name.
                type: str
            helper:
                description:
                    - Helper name.
                type: str
                choices:
                    - auto
                    - disable
                    - ftp
                    - tftp
                    - ras
                    - h323
                    - tns
                    - mms
                    - sip
                    - pptp
                    - rtsp
                    - dns-udp
                    - dns-tcp
                    - pmap
                    - rsh
                    - dcerpc
                    - mgcp
                    - gtp-c
                    - gtp-u
                    - gtp-b
            icmpcode:
                description:
                    - ICMP code.
                type: int
            icmptype:
                description:
                    - ICMP type.
                type: int
            iprange:
                description:
                    - Start and end of the IP range associated with service.
                type: str
            name:
                description:
                    - Custom service name.
                required: true
                type: str
            protocol:
                description:
                    - Protocol type based on IANA numbers.
                type: str
                choices:
                    - TCP/UDP/SCTP
                    - ICMP
                    - ICMP6
                    - IP
                    - HTTP
                    - FTP
                    - CONNECT
                    - SOCKS-TCP
                    - SOCKS-UDP
                    - ALL
            protocol_number:
                description:
                    - IP protocol number.
                type: int
            proxy:
                description:
                    - Enable/disable web proxy service.
                type: str
                choices:
                    - enable
                    - disable
            sctp_portrange:
                description:
                    - Multiple SCTP port ranges.
                type: str
            session_ttl:
                description:
                    - Session TTL (300 - 604800, 0 = default).
                type: int
            tcp_halfclose_timer:
                description:
                    - Wait time to close a TCP session waiting for an unanswered FIN packet (1 - 86400 sec, 0 = default).
                type: int
            tcp_halfopen_timer:
                description:
                    - Wait time to close a TCP session waiting for an unanswered open session packet (1 - 86400 sec, 0 = default).
                type: int
            tcp_portrange:
                description:
                    - Multiple TCP port ranges.
                type: str
            tcp_timewait_timer:
                description:
                    - Set the length of the TCP TIME-WAIT state in seconds (1 - 300 sec, 0 = default).
                type: int
            udp_idle_timer:
                description:
                    - UDP half close timeout (0 - 86400 sec, 0 = default).
                type: int
            udp_portrange:
                description:
                    - Multiple UDP port ranges.
                type: str
            visibility:
                description:
                    - Enable/disable the visibility of the service on the GUI.
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
  - name: Configure custom services.
    fortios_firewall_service_custom:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_service_custom:
        app_category:
         -
            id:  "4"
        app_service_type: "disable"
        application:
         -
            id:  "7"
        category: "<your_own_value> (source firewall.service.category.name)"
        check_reset_range: "disable"
        color: "10"
        comment: "Comment."
        fqdn: "<your_own_value>"
        helper: "auto"
        icmpcode: "14"
        icmptype: "15"
        iprange: "<your_own_value>"
        name: "default_name_17"
        protocol: "TCP/UDP/SCTP"
        protocol_number: "19"
        proxy: "enable"
        sctp_portrange: "<your_own_value>"
        session_ttl: "22"
        tcp_halfclose_timer: "23"
        tcp_halfopen_timer: "24"
        tcp_portrange: "<your_own_value>"
        tcp_timewait_timer: "26"
        udp_idle_timer: "27"
        udp_portrange: "<your_own_value>"
        visibility: "enable"
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


def filter_firewall_service_custom_data(json):
    option_list = ['app_category', 'app_service_type', 'application',
                   'category', 'check_reset_range', 'color',
                   'comment', 'fqdn', 'helper',
                   'icmpcode', 'icmptype', 'iprange',
                   'name', 'protocol', 'protocol_number',
                   'proxy', 'sctp_portrange', 'session_ttl',
                   'tcp_halfclose_timer', 'tcp_halfopen_timer', 'tcp_portrange',
                   'tcp_timewait_timer', 'udp_idle_timer', 'udp_portrange',
                   'visibility']
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


def firewall_service_custom(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_service_custom'] and data['firewall_service_custom']:
        state = data['firewall_service_custom']['state']
    else:
        state = True
    firewall_service_custom_data = data['firewall_service_custom']
    filtered_data = underscore_to_hyphen(filter_firewall_service_custom_data(firewall_service_custom_data))

    if state == "present":
        return fos.set('firewall.service',
                       'custom',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall.service',
                          'custom',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall_service(data, fos):

    if data['firewall_service_custom']:
        resp = firewall_service_custom(data, fos)

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
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "firewall_service_custom": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "app_category": {"required": False, "type": "list",
                                 "options": {
                                     "id": {"required": True, "type": "int"}
                                 }},
                "app_service_type": {"required": False, "type": "str",
                                     "choices": ["disable", "app-id", "app-category"]},
                "application": {"required": False, "type": "list",
                                "options": {
                                    "id": {"required": True, "type": "int"}
                                }},
                "category": {"required": False, "type": "str"},
                "check_reset_range": {"required": False, "type": "str",
                                      "choices": ["disable", "strict", "default"]},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "fqdn": {"required": False, "type": "str"},
                "helper": {"required": False, "type": "str",
                           "choices": ["auto", "disable", "ftp",
                                       "tftp", "ras", "h323",
                                       "tns", "mms", "sip",
                                       "pptp", "rtsp", "dns-udp",
                                       "dns-tcp", "pmap", "rsh",
                                       "dcerpc", "mgcp", "gtp-c",
                                       "gtp-u", "gtp-b"]},
                "icmpcode": {"required": False, "type": "int"},
                "icmptype": {"required": False, "type": "int"},
                "iprange": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "protocol": {"required": False, "type": "str",
                             "choices": ["TCP/UDP/SCTP", "ICMP", "ICMP6",
                                         "IP", "HTTP", "FTP",
                                         "CONNECT", "SOCKS-TCP", "SOCKS-UDP",
                                         "ALL"]},
                "protocol_number": {"required": False, "type": "int"},
                "proxy": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "sctp_portrange": {"required": False, "type": "str"},
                "session_ttl": {"required": False, "type": "int"},
                "tcp_halfclose_timer": {"required": False, "type": "int"},
                "tcp_halfopen_timer": {"required": False, "type": "int"},
                "tcp_portrange": {"required": False, "type": "str"},
                "tcp_timewait_timer": {"required": False, "type": "int"},
                "udp_idle_timer": {"required": False, "type": "int"},
                "udp_portrange": {"required": False, "type": "str"},
                "visibility": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_firewall_service(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_firewall_service(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
