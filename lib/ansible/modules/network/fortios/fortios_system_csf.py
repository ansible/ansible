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
module: fortios_system_csf
short_description: Add this FortiGate to a Security Fabric or set up a new Security Fabric on this FortiGate in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and csf category.
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
    system_csf:
        description:
            - Add this FortiGate to a Security Fabric or set up a new Security Fabric on this FortiGate.
        default: null
        type: dict
        suboptions:
            configuration_sync:
                description:
                    - Configuration sync mode.
                type: str
                choices:
                    - default
                    - local
            fabric_device:
                description:
                    - Fabric device configuration.
                type: list
                suboptions:
                    device_ip:
                        description:
                            - Device IP.
                        type: str
                    device_type:
                        description:
                            - Device type.
                        type: str
                        choices:
                            - fortimail
                    login:
                        description:
                            - Device login name.
                        type: str
                    name:
                        description:
                            - Device name.
                        required: true
                        type: str
                    password:
                        description:
                            - Device login password.
                        type: str
            fixed_key:
                description:
                    - Auto-generated fixed key used when this device is the root. (Will automatically be generated if not set.)
                type: str
            group_name:
                description:
                    - Security Fabric group name. All FortiGates in a Security Fabric must have the same group name.
                type: str
            group_password:
                description:
                    - Security Fabric group password. All FortiGates in a Security Fabric must have the same group password.
                type: str
            management_ip:
                description:
                    - Management IP address of this FortiGate. Used to log into this FortiGate from another FortiGate in the Security Fabric.
                type: str
            management_port:
                description:
                    - Overriding port for management connection (Overrides admin port).
                type: int
            status:
                description:
                    - Enable/disable Security Fabric.
                type: str
                choices:
                    - enable
                    - disable
            trusted_list:
                description:
                    - Pre-authorized and blocked security fabric nodes.
                type: list
                suboptions:
                    action:
                        description:
                            - Security fabric authorization action.
                        type: str
                        choices:
                            - accept
                            - deny
                    downstream_authorization:
                        description:
                            - Trust authorizations by this node's administrator.
                        type: str
                        choices:
                            - enable
                            - disable
                    ha_members:
                        description:
                            - HA members.
                        type: str
                    serial:
                        description:
                            - Serial.
                        required: true
                        type: str
            upstream_ip:
                description:
                    - IP address of the FortiGate upstream from this FortiGate in the Security Fabric.
                type: str
            upstream_port:
                description:
                    - The port number to use to communicate with the FortiGate upstream from this FortiGate in the Security Fabric .
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
  - name: Add this FortiGate to a Security Fabric or set up a new Security Fabric on this FortiGate.
    fortios_system_csf:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_csf:
        configuration_sync: "default"
        fabric_device:
         -
            device_ip: "<your_own_value>"
            device_type: "fortimail"
            login: "<your_own_value>"
            name: "default_name_8"
            password: "<your_own_value>"
        fixed_key: "<your_own_value>"
        group_name: "<your_own_value>"
        group_password: "<your_own_value>"
        management_ip: "<your_own_value>"
        management_port: "14"
        status: "enable"
        trusted_list:
         -
            action: "accept"
            downstream_authorization: "enable"
            ha_members: "<your_own_value>"
            serial: "<your_own_value>"
        upstream_ip: "<your_own_value>"
        upstream_port: "22"
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


def filter_system_csf_data(json):
    option_list = ['configuration_sync', 'fabric_device', 'fixed_key',
                   'group_name', 'group_password', 'management_ip',
                   'management_port', 'status', 'trusted_list',
                   'upstream_ip', 'upstream_port']
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


def system_csf(data, fos):
    vdom = data['vdom']
    system_csf_data = data['system_csf']
    filtered_data = underscore_to_hyphen(filter_system_csf_data(system_csf_data))

    return fos.set('system',
                   'csf',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_csf']:
        resp = system_csf(data, fos)

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
        "system_csf": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "configuration_sync": {"required": False, "type": "str",
                                       "choices": ["default", "local"]},
                "fabric_device": {"required": False, "type": "list",
                                  "options": {
                                      "device_ip": {"required": False, "type": "str"},
                                      "device_type": {"required": False, "type": "str",
                                                      "choices": ["fortimail"]},
                                      "login": {"required": False, "type": "str"},
                                      "name": {"required": True, "type": "str"},
                                      "password": {"required": False, "type": "str"}
                                  }},
                "fixed_key": {"required": False, "type": "str"},
                "group_name": {"required": False, "type": "str"},
                "group_password": {"required": False, "type": "str"},
                "management_ip": {"required": False, "type": "str"},
                "management_port": {"required": False, "type": "int"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "trusted_list": {"required": False, "type": "list",
                                 "options": {
                                     "action": {"required": False, "type": "str",
                                                "choices": ["accept", "deny"]},
                                     "downstream_authorization": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                     "ha_members": {"required": False, "type": "str"},
                                     "serial": {"required": True, "type": "str"}
                                 }},
                "upstream_ip": {"required": False, "type": "str"},
                "upstream_port": {"required": False, "type": "int"}

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
