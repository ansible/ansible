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
module: fortios_system_snmp_user
short_description: SNMP user configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system_snmp feature and user category.
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
    system_snmp_user:
        description:
            - SNMP user configuration.
        default: null
        type: dict
        suboptions:
            auth_proto:
                description:
                    - Authentication protocol.
                type: str
                choices:
                    - md5
                    - sha
            auth_pwd:
                description:
                    - Password for authentication protocol.
                type: str
            events:
                description:
                    - SNMP notifications (traps) to send.
                type: list
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
            ha_direct:
                description:
                    - Enable/disable direct management of HA cluster members.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - SNMP user name.
                required: true
                type: str
            notify_hosts:
                description:
                    - SNMP managers to send notifications (traps) to.
                type: list
            notify_hosts6:
                description:
                    - IPv6 SNMP managers to send notifications (traps) to.
                type: list
            priv_proto:
                description:
                    - Privacy (encryption) protocol.
                type: str
                choices:
                    - aes
                    - des
                    - aes256
                    - aes256cisco
            priv_pwd:
                description:
                    - Password for privacy (encryption) protocol.
                type: str
            queries:
                description:
                    - Enable/disable SNMP queries for this user.
                type: str
                choices:
                    - enable
                    - disable
            query_port:
                description:
                    - SNMPv3 query port .
                type: int
            security_level:
                description:
                    - Security level for message authentication and encryption.
                type: str
                choices:
                    - no-auth-no-priv
                    - auth-no-priv
                    - auth-priv
            source_ip:
                description:
                    - Source IP for SNMP trap.
                type: str
            source_ipv6:
                description:
                    - Source IPv6 for SNMP trap.
                type: str
            status:
                description:
                    - Enable/disable this SNMP user.
                type: str
                choices:
                    - enable
                    - disable
            trap_lport:
                description:
                    - SNMPv3 local trap port .
                type: int
            trap_rport:
                description:
                    - SNMPv3 trap remote port .
                type: int
            trap_status:
                description:
                    - Enable/disable traps for this SNMP user.
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
  - name: SNMP user configuration.
    fortios_system_snmp_user:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_snmp_user:
        auth_proto: "md5"
        auth_pwd: "<your_own_value>"
        events: "cpu-high"
        ha_direct: "enable"
        name: "default_name_7"
        notify_hosts: "<your_own_value>"
        notify_hosts6: "<your_own_value>"
        priv_proto: "aes"
        priv_pwd: "<your_own_value>"
        queries: "enable"
        query_port: "13"
        security_level: "no-auth-no-priv"
        source_ip: "84.230.14.43"
        source_ipv6: "<your_own_value>"
        status: "enable"
        trap_lport: "18"
        trap_rport: "19"
        trap_status: "enable"
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


def filter_system_snmp_user_data(json):
    option_list = ['auth_proto', 'auth_pwd', 'events',
                   'ha_direct', 'name', 'notify_hosts',
                   'notify_hosts6', 'priv_proto', 'priv_pwd',
                   'queries', 'query_port', 'security_level',
                   'source_ip', 'source_ipv6', 'status',
                   'trap_lport', 'trap_rport', 'trap_status']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = [[u'events'], [u'notify_hosts'], [u'notify_hosts6']]

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


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


def system_snmp_user(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_snmp_user_data = data['system_snmp_user']
    system_snmp_user_data = flatten_multilists_attributes(system_snmp_user_data)
    filtered_data = underscore_to_hyphen(filter_system_snmp_user_data(system_snmp_user_data))

    if state == "present":
        return fos.set('system.snmp',
                       'user',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system.snmp',
                          'user',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system_snmp(data, fos):

    if data['system_snmp_user']:
        resp = system_snmp_user(data, fos)

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
        "system_snmp_user": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "auth_proto": {"required": False, "type": "str",
                               "choices": ["md5", "sha"]},
                "auth_pwd": {"required": False, "type": "str"},
                "events": {"required": False, "type": "list",
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
                "ha_direct": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "notify_hosts": {"required": False, "type": "list"},
                "notify_hosts6": {"required": False, "type": "list"},
                "priv_proto": {"required": False, "type": "str",
                               "choices": ["aes", "des", "aes256",
                                           "aes256cisco"]},
                "priv_pwd": {"required": False, "type": "str"},
                "queries": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "query_port": {"required": False, "type": "int"},
                "security_level": {"required": False, "type": "str",
                                   "choices": ["no-auth-no-priv", "auth-no-priv", "auth-priv"]},
                "source_ip": {"required": False, "type": "str"},
                "source_ipv6": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "trap_lport": {"required": False, "type": "int"},
                "trap_rport": {"required": False, "type": "int"},
                "trap_status": {"required": False, "type": "str",
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
