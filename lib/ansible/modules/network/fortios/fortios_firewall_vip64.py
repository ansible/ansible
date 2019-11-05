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
module: fortios_firewall_vip64
short_description: Configure IPv6 to IPv4 virtual IPs in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and vip64 category.
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
    firewall_vip64:
        description:
            - Configure IPv6 to IPv4 virtual IPs.
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
            arp_reply:
                description:
                    - Enable ARP reply.
                type: str
                choices:
                    - disable
                    - enable
            color:
                description:
                    - Color of icon on the GUI.
                type: int
            comment:
                description:
                    - Comment.
                type: str
            extip:
                description:
                    - Start-external-IP [-end-external-IP].
                type: str
            extport:
                description:
                    - External service port.
                type: str
            id:
                description:
                    - Custom defined id.
                type: int
            ldb_method:
                description:
                    - Load balance method.
                type: str
                choices:
                    - static
                    - round-robin
                    - weighted
                    - least-session
                    - least-rtt
                    - first-alive
            mappedip:
                description:
                    - Start-mapped-IP [-end-mapped-IP].
                type: str
            mappedport:
                description:
                    - Mapped service port.
                type: str
            monitor:
                description:
                    - Health monitors.
                type: list
                suboptions:
                    name:
                        description:
                            - Health monitor name. Source firewall.ldb-monitor.name.
                        required: true
                        type: str
            name:
                description:
                    - VIP64 name.
                required: true
                type: str
            portforward:
                description:
                    - Enable port forwarding.
                type: str
                choices:
                    - disable
                    - enable
            protocol:
                description:
                    - Mapped port protocol.
                type: str
                choices:
                    - tcp
                    - udp
            realservers:
                description:
                    - Real servers.
                type: list
                suboptions:
                    client_ip:
                        description:
                            - Restrict server to a client IP in this range.
                        type: str
                    healthcheck:
                        description:
                            - Per server health check.
                        type: str
                        choices:
                            - disable
                            - enable
                            - vip
                    holddown_interval:
                        description:
                            - Hold down interval.
                        type: int
                    id:
                        description:
                            - Real server ID.
                        required: true
                        type: int
                    ip:
                        description:
                            - Mapped server IP.
                        type: str
                    max_connections:
                        description:
                            - Maximum number of connections allowed to server.
                        type: int
                    monitor:
                        description:
                            - Health monitors. Source firewall.ldb-monitor.name.
                        type: str
                    port:
                        description:
                            - Mapped server port.
                        type: int
                    status:
                        description:
                            - Server administrative status.
                        type: str
                        choices:
                            - active
                            - standby
                            - disable
                    weight:
                        description:
                            - weight
                        type: int
            server_type:
                description:
                    - Server type.
                type: str
                choices:
                    - http
                    - tcp
                    - udp
                    - ip
            src_filter:
                description:
                    - "Source IP6 filter (x:x:x:x:x:x:x:x/x)."
                type: list
                suboptions:
                    range:
                        description:
                            - Src-filter range.
                        required: true
                        type: str
            type:
                description:
                    - "VIP type: static NAT or server load balance."
                type: str
                choices:
                    - static-nat
                    - server-load-balance
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
                type: str
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
  - name: Configure IPv6 to IPv4 virtual IPs.
    fortios_firewall_vip64:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_vip64:
        arp_reply: "disable"
        color: "4"
        comment: "Comment."
        extip: "<your_own_value>"
        extport: "<your_own_value>"
        id:  "8"
        ldb_method: "static"
        mappedip: "<your_own_value>"
        mappedport: "<your_own_value>"
        monitor:
         -
            name: "default_name_13 (source firewall.ldb-monitor.name)"
        name: "default_name_14"
        portforward: "disable"
        protocol: "tcp"
        realservers:
         -
            client_ip: "<your_own_value>"
            healthcheck: "disable"
            holddown_interval: "20"
            id:  "21"
            ip: "<your_own_value>"
            max_connections: "23"
            monitor: "<your_own_value> (source firewall.ldb-monitor.name)"
            port: "25"
            status: "active"
            weight: "27"
        server_type: "http"
        src_filter:
         -
            range: "<your_own_value>"
        type: "static-nat"
        uuid: "<your_own_value>"
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


def filter_firewall_vip64_data(json):
    option_list = ['arp_reply', 'color', 'comment',
                   'extip', 'extport', 'id',
                   'ldb_method', 'mappedip', 'mappedport',
                   'monitor', 'name', 'portforward',
                   'protocol', 'realservers', 'server_type',
                   'src_filter', 'type', 'uuid']
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


def firewall_vip64(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_vip64'] and data['firewall_vip64']:
        state = data['firewall_vip64']['state']
    else:
        state = True
    firewall_vip64_data = data['firewall_vip64']
    filtered_data = underscore_to_hyphen(filter_firewall_vip64_data(firewall_vip64_data))

    if state == "present":
        return fos.set('firewall',
                       'vip64',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'vip64',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_vip64']:
        resp = firewall_vip64(data, fos)

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
        "firewall_vip64": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "arp_reply": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "extip": {"required": False, "type": "str"},
                "extport": {"required": False, "type": "str"},
                "id": {"required": False, "type": "int"},
                "ldb_method": {"required": False, "type": "str",
                               "choices": ["static", "round-robin", "weighted",
                                           "least-session", "least-rtt", "first-alive"]},
                "mappedip": {"required": False, "type": "str"},
                "mappedport": {"required": False, "type": "str"},
                "monitor": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "name": {"required": True, "type": "str"},
                "portforward": {"required": False, "type": "str",
                                "choices": ["disable", "enable"]},
                "protocol": {"required": False, "type": "str",
                             "choices": ["tcp", "udp"]},
                "realservers": {"required": False, "type": "list",
                                "options": {
                                    "client_ip": {"required": False, "type": "str"},
                                    "healthcheck": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable", "vip"]},
                                    "holddown_interval": {"required": False, "type": "int"},
                                    "id": {"required": True, "type": "int"},
                                    "ip": {"required": False, "type": "str"},
                                    "max_connections": {"required": False, "type": "int"},
                                    "monitor": {"required": False, "type": "str"},
                                    "port": {"required": False, "type": "int"},
                                    "status": {"required": False, "type": "str",
                                               "choices": ["active", "standby", "disable"]},
                                    "weight": {"required": False, "type": "int"}
                                }},
                "server_type": {"required": False, "type": "str",
                                "choices": ["http", "tcp", "udp",
                                            "ip"]},
                "src_filter": {"required": False, "type": "list",
                               "options": {
                                   "range": {"required": True, "type": "str"}
                               }},
                "type": {"required": False, "type": "str",
                         "choices": ["static-nat", "server-load-balance"]},
                "uuid": {"required": False, "type": "str"}

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

            is_error, has_changed, result = fortios_firewall(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_firewall(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
