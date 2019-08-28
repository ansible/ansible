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
module: fortios_system_password_policy
short_description: Configure password policy for locally defined administrator passwords and IPsec VPN pre-shared keys in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and password_policy category.
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
    system_password_policy:
        description:
            - Configure password policy for locally defined administrator passwords and IPsec VPN pre-shared keys.
        default: null
        type: dict
        suboptions:
            apply_to:
                description:
                    - Apply password policy to administrator passwords or IPsec pre-shared keys or both. Separate entries with a space.
                type: str
                choices:
                    - admin-password
                    - ipsec-preshared-key
            change_4_characters:
                description:
                    - Enable/disable changing at least 4 characters for a new password (This attribute overrides reuse-password if both are enabled).
                type: str
                choices:
                    - enable
                    - disable
            expire_day:
                description:
                    - Number of days after which passwords expire (1 - 999 days).
                type: int
            expire_status:
                description:
                    - Enable/disable password expiration.
                type: str
                choices:
                    - enable
                    - disable
            min_lower_case_letter:
                description:
                    - Minimum number of lowercase characters in password (0 - 128).
                type: int
            min_non_alphanumeric:
                description:
                    - Minimum number of non-alphanumeric characters in password (0 - 128).
                type: int
            min_number:
                description:
                    - Minimum number of numeric characters in password (0 - 128).
                type: int
            min_upper_case_letter:
                description:
                    - Minimum number of uppercase characters in password (0 - 128).
                type: int
            minimum_length:
                description:
                    - Minimum password length (8 - 128).
                type: int
            reuse_password:
                description:
                    - Enable/disable reusing of password (if both reuse-password and change-4-characters are enabled, change-4-characters overrides).
                type: str
                choices:
                    - enable
                    - disable
            status:
                description:
                    - Enable/disable setting a password policy for locally defined administrator passwords and IPsec VPN pre-shared keys.
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
  - name: Configure password policy for locally defined administrator passwords and IPsec VPN pre-shared keys.
    fortios_system_password_policy:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_password_policy:
        apply_to: "admin-password"
        change_4_characters: "enable"
        expire_day: "5"
        expire_status: "enable"
        min_lower_case_letter: "7"
        min_non_alphanumeric: "8"
        min_number: "9"
        min_upper_case_letter: "10"
        minimum_length: "11"
        reuse_password: "enable"
        status: "enable"
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


def filter_system_password_policy_data(json):
    option_list = ['apply_to', 'change_4_characters', 'expire_day',
                   'expire_status', 'min_lower_case_letter', 'min_non_alphanumeric',
                   'min_number', 'min_upper_case_letter', 'minimum_length',
                   'reuse_password', 'status']
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


def system_password_policy(data, fos):
    vdom = data['vdom']
    system_password_policy_data = data['system_password_policy']
    filtered_data = underscore_to_hyphen(filter_system_password_policy_data(system_password_policy_data))

    return fos.set('system',
                   'password-policy',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_password_policy']:
        resp = system_password_policy(data, fos)

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
        "system_password_policy": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "apply_to": {"required": False, "type": "str",
                             "choices": ["admin-password", "ipsec-preshared-key"]},
                "change_4_characters": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "expire_day": {"required": False, "type": "int"},
                "expire_status": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "min_lower_case_letter": {"required": False, "type": "int"},
                "min_non_alphanumeric": {"required": False, "type": "int"},
                "min_number": {"required": False, "type": "int"},
                "min_upper_case_letter": {"required": False, "type": "int"},
                "minimum_length": {"required": False, "type": "int"},
                "reuse_password": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "status": {"required": False, "type": "str",
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
