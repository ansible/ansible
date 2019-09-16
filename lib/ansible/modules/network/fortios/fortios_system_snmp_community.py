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
module: fortios_system_snmp_community
short_description: SNMP community configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system_snmp feature and community category.
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
    system_snmp_community:
        description:
            - SNMP community configuration.
        default: null
        type: dict
        suboptions:
            events:
                description:
                    - SNMP trap events.
                type: str
                choices:
                    - cpu-high
                    - mem-low
                    - log-full
                    - intf-ip
                    - vpn-tun-up
                    - vpn-tun-down
                    - ha-switch
                    - ha-hb-failure
                    - ips-signature
                    - ips-anomaly
                    - av-virus
                    - av-oversize
                    - av-pattern
                    - av-fragmented
                    - fm-if-change
                    - fm-conf-change
                    - bgp-established
                    - bgp-backward-transition
                    - ha-member-up
                    - ha-member-down
                    - ent-conf-change
                    - av-conserve
                    - av-bypass
                    - av-oversize-passed
                    - av-oversize-blocked
                    - ips-pkg-update
                    - ips-fail-open
                    - faz-disconnect
                    - wc-ap-up
                    - wc-ap-down
                    - fswctl-session-up
                    - fswctl-session-down
                    - load-balance-real-server-down
                    - device-new
                    - per-cpu-high
            hosts:
                description:
                    - Configure IPv4 SNMP managers (hosts).
                type: list
                suboptions:
                    ha_direct:
                        description:
                            - Enable/disable direct management of HA cluster members.
                        type: str
                        choices:
                            - enable
                            - disable
                    host_type:
                        description:
                            - Control whether the SNMP manager sends SNMP queries, receives SNMP traps, or both.
                        type: str
                        choices:
                            - any
                            - query
                            - trap
                    id:
                        description:
                            - Host entry ID.
                        required: true
                        type: int
                    ip:
                        description:
                            - IPv4 address of the SNMP manager (host).
                        type: str
                    source_ip:
                        description:
                            - Source IPv4 address for SNMP traps.
                        type: str
            hosts6:
                description:
                    - Configure IPv6 SNMP managers.
                type: list
                suboptions:
                    ha_direct:
                        description:
                            - Enable/disable direct management of HA cluster members.
                        type: str
                        choices:
                            - enable
                            - disable
                    host_type:
                        description:
                            - Control whether the SNMP manager sends SNMP queries, receives SNMP traps, or both.
                        type: str
                        choices:
                            - any
                            - query
                            - trap
                    id:
                        description:
                            - Host6 entry ID.
                        required: true
                        type: int
                    ipv6:
                        description:
                            - SNMP manager IPv6 address prefix.
                        type: str
                    source_ipv6:
                        description:
                            - Source IPv6 address for SNMP traps.
                        type: str
            id:
                description:
                    - Community ID.
                required: true
                type: int
            name:
                description:
                    - Community name.
                type: str
            query_v1_port:
                description:
                    - SNMP v1 query port .
                type: int
            query_v1_status:
                description:
                    - Enable/disable SNMP v1 queries.
                type: str
                choices:
                    - enable
                    - disable
            query_v2c_port:
                description:
                    - SNMP v2c query port .
                type: int
            query_v2c_status:
                description:
                    - Enable/disable SNMP v2c queries.
                type: str
                choices:
                    - enable
                    - disable
            status:
                description:
                    - Enable/disable this SNMP community.
                type: str
                choices:
                    - enable
                    - disable
            trap_v1_lport:
                description:
                    - SNMP v1 trap local port .
                type: int
            trap_v1_rport:
                description:
                    - SNMP v1 trap remote port .
                type: int
            trap_v1_status:
                description:
                    - Enable/disable SNMP v1 traps.
                type: str
                choices:
                    - enable
                    - disable
            trap_v2c_lport:
                description:
                    - SNMP v2c trap local port .
                type: int
            trap_v2c_rport:
                description:
                    - SNMP v2c trap remote port .
                type: int
            trap_v2c_status:
                description:
                    - Enable/disable SNMP v2c traps.
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
  - name: SNMP community configuration.
    fortios_system_snmp_community:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_snmp_community:
        events: "cpu-high"
        hosts:
         -
            ha_direct: "enable"
            host_type: "any"
            id:  "7"
            ip: "<your_own_value>"
            source_ip: "84.230.14.43"
        hosts6:
         -
            ha_direct: "enable"
            host_type: "any"
            id:  "13"
            ipv6: "<your_own_value>"
            source_ipv6: "<your_own_value>"
        id:  "16"
        name: "default_name_17"
        query_v1_port: "18"
        query_v1_status: "enable"
        query_v2c_port: "20"
        query_v2c_status: "enable"
        status: "enable"
        trap_v1_lport: "23"
        trap_v1_rport: "24"
        trap_v1_status: "enable"
        trap_v2c_lport: "26"
        trap_v2c_rport: "27"
        trap_v2c_status: "enable"
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


def filter_system_snmp_community_data(json):
    option_list = ['events', 'hosts', 'hosts6',
                   'id', 'name', 'query_v1_port',
                   'query_v1_status', 'query_v2c_port', 'query_v2c_status',
                   'status', 'trap_v1_lport', 'trap_v1_rport',
                   'trap_v1_status', 'trap_v2c_lport', 'trap_v2c_rport',
                   'trap_v2c_status']
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


def system_snmp_community(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_snmp_community_data = data['system_snmp_community']
    filtered_data = underscore_to_hyphen(filter_system_snmp_community_data(system_snmp_community_data))

    if state == "present":
        return fos.set('system.snmp',
                       'community',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system.snmp',
                          'community',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system_snmp(data, fos):

    if data['system_snmp_community']:
        resp = system_snmp_community(data, fos)

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
        "system_snmp_community": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "events": {"required": False, "type": "str",
                           "choices": ["cpu-high", "mem-low", "log-full",
                                       "intf-ip", "vpn-tun-up", "vpn-tun-down",
                                       "ha-switch", "ha-hb-failure", "ips-signature",
                                       "ips-anomaly", "av-virus", "av-oversize",
                                       "av-pattern", "av-fragmented", "fm-if-change",
                                       "fm-conf-change", "bgp-established", "bgp-backward-transition",
                                       "ha-member-up", "ha-member-down", "ent-conf-change",
                                       "av-conserve", "av-bypass", "av-oversize-passed",
                                       "av-oversize-blocked", "ips-pkg-update", "ips-fail-open",
                                       "faz-disconnect", "wc-ap-up", "wc-ap-down",
                                       "fswctl-session-up", "fswctl-session-down", "load-balance-real-server-down",
                                       "device-new", "per-cpu-high"]},
                "hosts": {"required": False, "type": "list",
                          "options": {
                              "ha_direct": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                              "host_type": {"required": False, "type": "str",
                                            "choices": ["any", "query", "trap"]},
                              "id": {"required": True, "type": "int"},
                              "ip": {"required": False, "type": "str"},
                              "source_ip": {"required": False, "type": "str"}
                          }},
                "hosts6": {"required": False, "type": "list",
                           "options": {
                               "ha_direct": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                               "host_type": {"required": False, "type": "str",
                                             "choices": ["any", "query", "trap"]},
                               "id": {"required": True, "type": "int"},
                               "ipv6": {"required": False, "type": "str"},
                               "source_ipv6": {"required": False, "type": "str"}
                           }},
                "id": {"required": True, "type": "int"},
                "name": {"required": False, "type": "str"},
                "query_v1_port": {"required": False, "type": "int"},
                "query_v1_status": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "query_v2c_port": {"required": False, "type": "int"},
                "query_v2c_status": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "trap_v1_lport": {"required": False, "type": "int"},
                "trap_v1_rport": {"required": False, "type": "int"},
                "trap_v1_status": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "trap_v2c_lport": {"required": False, "type": "int"},
                "trap_v2c_rport": {"required": False, "type": "int"},
                "trap_v2c_status": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_system_snmp(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system_snmp(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
