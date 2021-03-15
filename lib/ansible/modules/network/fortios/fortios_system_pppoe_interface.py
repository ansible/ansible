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
module: fortios_system_pppoe_interface
short_description: Configure the PPPoE interfaces in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and pppoe_interface category.
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
    system_pppoe_interface:
        description:
            - Configure the PPPoE interfaces.
        default: null
        type: dict
        suboptions:
            ac_name:
                description:
                    - PPPoE AC name.
                type: str
            auth_type:
                description:
                    - PPP authentication type to use.
                type: str
                choices:
                    - auto
                    - pap
                    - chap
                    - mschapv1
                    - mschapv2
            device:
                description:
                    - Name for the physical interface. Source system.interface.name.
                type: str
            dial_on_demand:
                description:
                    - Enable/disable dial on demand to dial the PPPoE interface when packets are routed to the PPPoE interface.
                type: str
                choices:
                    - enable
                    - disable
            disc_retry_timeout:
                description:
                    - PPPoE discovery init timeout value in (0-4294967295 sec).
                type: int
            idle_timeout:
                description:
                    - PPPoE auto disconnect after idle timeout (0-4294967295 sec).
                type: int
            ipunnumbered:
                description:
                    - PPPoE unnumbered IP.
                type: str
            ipv6:
                description:
                    - Enable/disable IPv6 Control Protocol (IPv6CP).
                type: str
                choices:
                    - enable
                    - disable
            lcp_echo_interval:
                description:
                    - PPPoE LCP echo interval in (0-4294967295 sec).
                type: int
            lcp_max_echo_fails:
                description:
                    - Maximum missed LCP echo messages before disconnect (0-4294967295).
                type: int
            name:
                description:
                    - Name of the PPPoE interface.
                required: true
                type: str
            padt_retry_timeout:
                description:
                    - PPPoE terminate timeout value in (0-4294967295 sec).
                type: int
            password:
                description:
                    - Enter the password.
                type: str
            pppoe_unnumbered_negotiate:
                description:
                    - Enable/disable PPPoE unnumbered negotiation.
                type: str
                choices:
                    - enable
                    - disable
            service_name:
                description:
                    - PPPoE service name.
                type: str
            username:
                description:
                    - User name.
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
  - name: Configure the PPPoE interfaces.
    fortios_system_pppoe_interface:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_pppoe_interface:
        ac_name: "<your_own_value>"
        auth_type: "auto"
        device: "<your_own_value> (source system.interface.name)"
        dial_on_demand: "enable"
        disc_retry_timeout: "7"
        idle_timeout: "8"
        ipunnumbered: "<your_own_value>"
        ipv6: "enable"
        lcp_echo_interval: "11"
        lcp_max_echo_fails: "12"
        name: "default_name_13"
        padt_retry_timeout: "14"
        password: "<your_own_value>"
        pppoe_unnumbered_negotiate: "enable"
        service_name: "<your_own_value>"
        username: "<your_own_value>"
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


def filter_system_pppoe_interface_data(json):
    option_list = ['ac_name', 'auth_type', 'device',
                   'dial_on_demand', 'disc_retry_timeout', 'idle_timeout',
                   'ipunnumbered', 'ipv6', 'lcp_echo_interval',
                   'lcp_max_echo_fails', 'name', 'padt_retry_timeout',
                   'password', 'pppoe_unnumbered_negotiate', 'service_name',
                   'username']
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


def system_pppoe_interface(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_pppoe_interface_data = data['system_pppoe_interface']
    filtered_data = underscore_to_hyphen(filter_system_pppoe_interface_data(system_pppoe_interface_data))

    if state == "present":
        return fos.set('system',
                       'pppoe-interface',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'pppoe-interface',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_pppoe_interface']:
        resp = system_pppoe_interface(data, fos)

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
        "system_pppoe_interface": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "ac_name": {"required": False, "type": "str"},
                "auth_type": {"required": False, "type": "str",
                              "choices": ["auto", "pap", "chap",
                                          "mschapv1", "mschapv2"]},
                "device": {"required": False, "type": "str"},
                "dial_on_demand": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "disc_retry_timeout": {"required": False, "type": "int"},
                "idle_timeout": {"required": False, "type": "int"},
                "ipunnumbered": {"required": False, "type": "str"},
                "ipv6": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "lcp_echo_interval": {"required": False, "type": "int"},
                "lcp_max_echo_fails": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "padt_retry_timeout": {"required": False, "type": "int"},
                "password": {"required": False, "type": "str", "no_log": True},
                "pppoe_unnumbered_negotiate": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "service_name": {"required": False, "type": "str"},
                "username": {"required": False, "type": "str"}

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
