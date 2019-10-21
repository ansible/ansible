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
module: fortios_system_resource_limits
short_description: Configure resource limits in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and resource_limits category.
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
    system_resource_limits:
        description:
            - Configure resource limits.
        default: null
        type: dict
        suboptions:
            custom_service:
                description:
                    - Maximum number of firewall custom services.
                type: int
            dialup_tunnel:
                description:
                    - Maximum number of dial-up tunnels.
                type: int
            firewall_address:
                description:
                    - Maximum number of firewall addresses (IPv4, IPv6, multicast).
                type: int
            firewall_addrgrp:
                description:
                    - Maximum number of firewall address groups (IPv4, IPv6).
                type: int
            firewall_policy:
                description:
                    - Maximum number of firewall policies (IPv4, IPv6, policy46, policy64, DoS-policy4, DoS-policy6, multicast).
                type: int
            ipsec_phase1:
                description:
                    - Maximum number of VPN IPsec phase1 tunnels.
                type: int
            ipsec_phase1_interface:
                description:
                    - Maximum number of VPN IPsec phase1 interface tunnels.
                type: int
            ipsec_phase2:
                description:
                    - Maximum number of VPN IPsec phase2 tunnels.
                type: int
            ipsec_phase2_interface:
                description:
                    - Maximum number of VPN IPsec phase2 interface tunnels.
                type: int
            log_disk_quota:
                description:
                    - Log disk quota in MB.
                type: int
            onetime_schedule:
                description:
                    - Maximum number of firewall one-time schedules.
                type: int
            proxy:
                description:
                    - Maximum number of concurrent proxy users.
                type: int
            recurring_schedule:
                description:
                    - Maximum number of firewall recurring schedules.
                type: int
            service_group:
                description:
                    - Maximum number of firewall service groups.
                type: int
            session:
                description:
                    - Maximum number of sessions.
                type: int
            sslvpn:
                description:
                    - Maximum number of SSL-VPN.
                type: int
            user:
                description:
                    - Maximum number of local users.
                type: int
            user_group:
                description:
                    - Maximum number of user groups.
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
  - name: Configure resource limits.
    fortios_system_resource_limits:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_resource_limits:
        custom_service: "3"
        dialup_tunnel: "4"
        firewall_address: "5"
        firewall_addrgrp: "6"
        firewall_policy: "7"
        ipsec_phase1: "8"
        ipsec_phase1_interface: "9"
        ipsec_phase2: "10"
        ipsec_phase2_interface: "11"
        log_disk_quota: "12"
        onetime_schedule: "13"
        proxy: "14"
        recurring_schedule: "15"
        service_group: "16"
        session: "17"
        sslvpn: "18"
        user: "19"
        user_group: "20"
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


def filter_system_resource_limits_data(json):
    option_list = ['custom_service', 'dialup_tunnel', 'firewall_address',
                   'firewall_addrgrp', 'firewall_policy', 'ipsec_phase1',
                   'ipsec_phase1_interface', 'ipsec_phase2', 'ipsec_phase2_interface',
                   'log_disk_quota', 'onetime_schedule', 'proxy',
                   'recurring_schedule', 'service_group', 'session',
                   'sslvpn', 'user', 'user_group']
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


def system_resource_limits(data, fos):
    vdom = data['vdom']
    system_resource_limits_data = data['system_resource_limits']
    filtered_data = underscore_to_hyphen(filter_system_resource_limits_data(system_resource_limits_data))

    return fos.set('system',
                   'resource-limits',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_resource_limits']:
        resp = system_resource_limits(data, fos)

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
        "system_resource_limits": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "custom_service": {"required": False, "type": "int"},
                "dialup_tunnel": {"required": False, "type": "int"},
                "firewall_address": {"required": False, "type": "int"},
                "firewall_addrgrp": {"required": False, "type": "int"},
                "firewall_policy": {"required": False, "type": "int"},
                "ipsec_phase1": {"required": False, "type": "int"},
                "ipsec_phase1_interface": {"required": False, "type": "int"},
                "ipsec_phase2": {"required": False, "type": "int"},
                "ipsec_phase2_interface": {"required": False, "type": "int"},
                "log_disk_quota": {"required": False, "type": "int"},
                "onetime_schedule": {"required": False, "type": "int"},
                "proxy": {"required": False, "type": "int"},
                "recurring_schedule": {"required": False, "type": "int"},
                "service_group": {"required": False, "type": "int"},
                "session": {"required": False, "type": "int"},
                "sslvpn": {"required": False, "type": "int"},
                "user": {"required": False, "type": "int"},
                "user_group": {"required": False, "type": "int"}

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
