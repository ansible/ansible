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
module: fortios_switch_controller_global
short_description: Configure FortiSwitch global settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify switch_controller feature and global category.
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
    switch_controller_global:
        description:
            - Configure FortiSwitch global settings.
        default: null
        type: dict
        suboptions:
            allow_multiple_interfaces:
                description:
                    - Enable/disable multiple FortiLink interfaces for redundant connections between a managed FortiSwitch and FortiGate.
                type: str
                choices:
                    - enable
                    - disable
            default_virtual_switch_vlan:
                description:
                    - Default VLAN for ports when added to the virtual-switch. Source system.interface.name.
                type: str
            disable_discovery:
                description:
                    - Prevent this FortiSwitch from discovering.
                type: list
                suboptions:
                    name:
                        description:
                            - Managed device ID.
                        required: true
                        type: str
            https_image_push:
                description:
                    - Enable/disable image push to FortiSwitch using HTTPS.
                type: str
                choices:
                    - enable
                    - disable
            log_mac_limit_violations:
                description:
                    - Enable/disable logs for Learning Limit Violations.
                type: str
                choices:
                    - enable
                    - disable
            mac_aging_interval:
                description:
                    - Time after which an inactive MAC is aged out (10 - 1000000 sec).
                type: int
            mac_retention_period:
                description:
                    - Time in hours after which an inactive MAC is removed from client DB.
                type: int
            mac_violation_timer:
                description:
                    - Set timeout for Learning Limit Violations (0 = disabled).
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
  - name: Configure FortiSwitch global settings.
    fortios_switch_controller_global:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      switch_controller_global:
        allow_multiple_interfaces: "enable"
        default_virtual_switch_vlan: "<your_own_value> (source system.interface.name)"
        disable_discovery:
         -
            name: "default_name_6"
        https_image_push: "enable"
        log_mac_limit_violations: "enable"
        mac_aging_interval: "9"
        mac_retention_period: "10"
        mac_violation_timer: "11"
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


def filter_switch_controller_global_data(json):
    option_list = ['allow_multiple_interfaces', 'default_virtual_switch_vlan', 'disable_discovery',
                   'https_image_push', 'log_mac_limit_violations', 'mac_aging_interval',
                   'mac_retention_period', 'mac_violation_timer']
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


def switch_controller_global(data, fos):
    vdom = data['vdom']
    switch_controller_global_data = data['switch_controller_global']
    filtered_data = underscore_to_hyphen(filter_switch_controller_global_data(switch_controller_global_data))

    return fos.set('switch-controller',
                   'global',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_switch_controller(data, fos):

    if data['switch_controller_global']:
        resp = switch_controller_global(data, fos)

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
        "switch_controller_global": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "allow_multiple_interfaces": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "default_virtual_switch_vlan": {"required": False, "type": "str"},
                "disable_discovery": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "https_image_push": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "log_mac_limit_violations": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "mac_aging_interval": {"required": False, "type": "int"},
                "mac_retention_period": {"required": False, "type": "int"},
                "mac_violation_timer": {"required": False, "type": "int"}

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

            is_error, has_changed, result = fortios_switch_controller(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_switch_controller(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
