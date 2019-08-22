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
module: fortios_system_vdom_property
short_description: Configure VDOM property in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and vdom_property category.
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
    system_vdom_property:
        description:
            - Configure VDOM property.
        default: null
        type: dict
        suboptions:
            custom_service:
                description:
                    - Maximum guaranteed number of firewall custom services.
                type: str
            description:
                description:
                    - Description.
                type: str
            dialup_tunnel:
                description:
                    - Maximum guaranteed number of dial-up tunnels.
                type: str
            firewall_address:
                description:
                    - Maximum guaranteed number of firewall addresses (IPv4, IPv6, multicast).
                type: str
            firewall_addrgrp:
                description:
                    - Maximum guaranteed number of firewall address groups (IPv4, IPv6).
                type: str
            firewall_policy:
                description:
                    - Maximum guaranteed number of firewall policies (IPv4, IPv6, policy46, policy64, DoS-policy4, DoS-policy6, multicast).
                type: str
            ipsec_phase1:
                description:
                    - Maximum guaranteed number of VPN IPsec phase 1 tunnels.
                type: str
            ipsec_phase1_interface:
                description:
                    - Maximum guaranteed number of VPN IPsec phase1 interface tunnels.
                type: str
            ipsec_phase2:
                description:
                    - Maximum guaranteed number of VPN IPsec phase 2 tunnels.
                type: str
            ipsec_phase2_interface:
                description:
                    - Maximum guaranteed number of VPN IPsec phase2 interface tunnels.
                type: str
            log_disk_quota:
                description:
                    - Log disk quota in MB (range depends on how much disk space is available).
                type: str
            name:
                description:
                    - VDOM name. Source system.vdom.name.
                required: true
                type: str
            onetime_schedule:
                description:
                    - Maximum guaranteed number of firewall one-time schedules.
                type: str
            proxy:
                description:
                    - Maximum guaranteed number of concurrent proxy users.
                type: str
            recurring_schedule:
                description:
                    - Maximum guaranteed number of firewall recurring schedules.
                type: str
            service_group:
                description:
                    - Maximum guaranteed number of firewall service groups.
                type: str
            session:
                description:
                    - Maximum guaranteed number of sessions.
                type: str
            snmp_index:
                description:
                    - Permanent SNMP Index of the virtual domain (0 - 4294967295).
                type: int
            sslvpn:
                description:
                    - Maximum guaranteed number of SSL-VPNs.
                type: str
            user:
                description:
                    - Maximum guaranteed number of local users.
                type: str
            user_group:
                description:
                    - Maximum guaranteed number of user groups.
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
  - name: Configure VDOM property.
    fortios_system_vdom_property:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_vdom_property:
        custom_service: "<your_own_value>"
        description: "<your_own_value>"
        dialup_tunnel: "<your_own_value>"
        firewall_address: "<your_own_value>"
        firewall_addrgrp: "<your_own_value>"
        firewall_policy: "<your_own_value>"
        ipsec_phase1: "<your_own_value>"
        ipsec_phase1_interface: "<your_own_value>"
        ipsec_phase2: "<your_own_value>"
        ipsec_phase2_interface: "<your_own_value>"
        log_disk_quota: "<your_own_value>"
        name: "default_name_14 (source system.vdom.name)"
        onetime_schedule: "<your_own_value>"
        proxy: "<your_own_value>"
        recurring_schedule: "<your_own_value>"
        service_group: "<your_own_value>"
        session: "<your_own_value>"
        snmp_index: "20"
        sslvpn: "<your_own_value>"
        user: "<your_own_value>"
        user_group: "<your_own_value>"
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


def filter_system_vdom_property_data(json):
    option_list = ['custom_service', 'description', 'dialup_tunnel',
                   'firewall_address', 'firewall_addrgrp', 'firewall_policy',
                   'ipsec_phase1', 'ipsec_phase1_interface', 'ipsec_phase2',
                   'ipsec_phase2_interface', 'log_disk_quota', 'name',
                   'onetime_schedule', 'proxy', 'recurring_schedule',
                   'service_group', 'session', 'snmp_index',
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


def system_vdom_property(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_vdom_property_data = data['system_vdom_property']
    filtered_data = underscore_to_hyphen(filter_system_vdom_property_data(system_vdom_property_data))

    if state == "present":
        return fos.set('system',
                       'vdom-property',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'vdom-property',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_vdom_property']:
        resp = system_vdom_property(data, fos)

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
        "system_vdom_property": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "custom_service": {"required": False, "type": "str"},
                "description": {"required": False, "type": "str"},
                "dialup_tunnel": {"required": False, "type": "str"},
                "firewall_address": {"required": False, "type": "str"},
                "firewall_addrgrp": {"required": False, "type": "str"},
                "firewall_policy": {"required": False, "type": "str"},
                "ipsec_phase1": {"required": False, "type": "str"},
                "ipsec_phase1_interface": {"required": False, "type": "str"},
                "ipsec_phase2": {"required": False, "type": "str"},
                "ipsec_phase2_interface": {"required": False, "type": "str"},
                "log_disk_quota": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "onetime_schedule": {"required": False, "type": "str"},
                "proxy": {"required": False, "type": "str"},
                "recurring_schedule": {"required": False, "type": "str"},
                "service_group": {"required": False, "type": "str"},
                "session": {"required": False, "type": "str"},
                "snmp_index": {"required": False, "type": "int"},
                "sslvpn": {"required": False, "type": "str"},
                "user": {"required": False, "type": "str"},
                "user_group": {"required": False, "type": "str"}

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
