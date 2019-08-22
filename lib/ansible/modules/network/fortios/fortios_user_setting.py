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
# along with this program.  If not, see <https://www.gnu.org/licenses/>

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_user_setting
short_description: Configure user authentication setting in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify user feature and setting category.
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
    user_setting:
        description:
            - Configure user authentication setting.
        default: null
        type: dict
        suboptions:
            auth_blackout_time:
                description:
                    - Time in seconds an IP address is denied access after failing to authenticate five times within one minute.
                type: int
            auth_ca_cert:
                description:
                    - HTTPS CA certificate for policy authentication. Source vpn.certificate.local.name.
                type: str
            auth_cert:
                description:
                    - HTTPS server certificate for policy authentication. Source vpn.certificate.local.name.
                type: str
            auth_http_basic:
                description:
                    - Enable/disable use of HTTP basic authentication for identity-based firewall policies.
                type: str
                choices:
                    - enable
                    - disable
            auth_invalid_max:
                description:
                    - Maximum number of failed authentication attempts before the user is blocked.
                type: int
            auth_lockout_duration:
                description:
                    - Lockout period in seconds after too many login failures.
                type: int
            auth_lockout_threshold:
                description:
                    - Maximum number of failed login attempts before login lockout is triggered.
                type: int
            auth_portal_timeout:
                description:
                    - Time in minutes before captive portal user have to re-authenticate (1 - 30 min).
                type: int
            auth_ports:
                description:
                    - Set up non-standard ports for authentication with HTTP, HTTPS, FTP, and TELNET.
                type: list
                suboptions:
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    port:
                        description:
                            - Non-standard port for firewall user authentication.
                        type: int
                    type:
                        description:
                            - Service type.
                        type: str
                        choices:
                            - http
                            - https
                            - ftp
                            - telnet
            auth_secure_http:
                description:
                    - Enable/disable redirecting HTTP user authentication to more secure HTTPS.
                type: str
                choices:
                    - enable
                    - disable
            auth_src_mac:
                description:
                    - Enable/disable source MAC for user identity.
                type: str
                choices:
                    - enable
                    - disable
            auth_ssl_allow_renegotiation:
                description:
                    - Allow/forbid SSL re-negotiation for HTTPS authentication.
                type: str
                choices:
                    - enable
                    - disable
            auth_timeout:
                description:
                    - Time in minutes before the firewall user authentication timeout requires the user to re-authenticate.
                type: int
            auth_timeout_type:
                description:
                    - Control if authenticated users have to login again after a hard timeout, after an idle timeout, or after a session timeout.
                type: str
                choices:
                    - idle-timeout
                    - hard-timeout
                    - new-session
            auth_type:
                description:
                    - Supported firewall policy authentication protocols/methods.
                type: str
                choices:
                    - http
                    - https
                    - ftp
                    - telnet
            radius_ses_timeout_act:
                description:
                    - Set the RADIUS session timeout to a hard timeout or to ignore RADIUS server session timeouts.
                type: str
                choices:
                    - hard-timeout
                    - ignore-timeout
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
  - name: Configure user authentication setting.
    fortios_user_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      user_setting:
        auth_blackout_time: "3"
        auth_ca_cert: "<your_own_value> (source vpn.certificate.local.name)"
        auth_cert: "<your_own_value> (source vpn.certificate.local.name)"
        auth_http_basic: "enable"
        auth_invalid_max: "7"
        auth_lockout_duration: "8"
        auth_lockout_threshold: "9"
        auth_portal_timeout: "10"
        auth_ports:
         -
            id:  "12"
            port: "13"
            type: "http"
        auth_secure_http: "enable"
        auth_src_mac: "enable"
        auth_ssl_allow_renegotiation: "enable"
        auth_timeout: "18"
        auth_timeout_type: "idle-timeout"
        auth_type: "http"
        radius_ses_timeout_act: "hard-timeout"
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


def filter_user_setting_data(json):
    option_list = ['auth_blackout_time', 'auth_ca_cert', 'auth_cert',
                   'auth_http_basic', 'auth_invalid_max', 'auth_lockout_duration',
                   'auth_lockout_threshold', 'auth_portal_timeout', 'auth_ports',
                   'auth_secure_http', 'auth_src_mac', 'auth_ssl_allow_renegotiation',
                   'auth_timeout', 'auth_timeout_type', 'auth_type',
                   'radius_ses_timeout_act']
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


def user_setting(data, fos):
    vdom = data['vdom']
    user_setting_data = data['user_setting']
    filtered_data = underscore_to_hyphen(filter_user_setting_data(user_setting_data))

    return fos.set('user',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_user(data, fos):

    if data['user_setting']:
        resp = user_setting(data, fos)

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
        "user_setting": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "auth_blackout_time": {"required": False, "type": "int"},
                "auth_ca_cert": {"required": False, "type": "str"},
                "auth_cert": {"required": False, "type": "str"},
                "auth_http_basic": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "auth_invalid_max": {"required": False, "type": "int"},
                "auth_lockout_duration": {"required": False, "type": "int"},
                "auth_lockout_threshold": {"required": False, "type": "int"},
                "auth_portal_timeout": {"required": False, "type": "int"},
                "auth_ports": {"required": False, "type": "list",
                               "options": {
                                   "id": {"required": True, "type": "int"},
                                   "port": {"required": False, "type": "int"},
                                   "type": {"required": False, "type": "str",
                                            "choices": ["http", "https", "ftp",
                                                        "telnet"]}
                               }},
                "auth_secure_http": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "auth_src_mac": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "auth_ssl_allow_renegotiation": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "auth_timeout": {"required": False, "type": "int"},
                "auth_timeout_type": {"required": False, "type": "str",
                                      "choices": ["idle-timeout", "hard-timeout", "new-session"]},
                "auth_type": {"required": False, "type": "str",
                              "choices": ["http", "https", "ftp",
                                          "telnet"]},
                "radius_ses_timeout_act": {"required": False, "type": "str",
                                           "choices": ["hard-timeout", "ignore-timeout"]}

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

            is_error, has_changed, result = fortios_user(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_user(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
