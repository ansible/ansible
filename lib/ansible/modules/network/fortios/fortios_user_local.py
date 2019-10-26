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
module: fortios_user_local
short_description: Configure local users in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify user feature and local category.
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
    user_local:
        description:
            - Configure local users.
        default: null
        type: dict
        suboptions:
            auth_concurrent_override:
                description:
                    - Enable/disable overriding the policy-auth-concurrent under config system global.
                type: str
                choices:
                    - enable
                    - disable
            auth_concurrent_value:
                description:
                    - Maximum number of concurrent logins permitted from the same user.
                type: int
            authtimeout:
                description:
                    - Time in minutes before the authentication timeout for a user is reached.
                type: int
            email_to:
                description:
                    - Two-factor recipient's email address.
                type: str
            fortitoken:
                description:
                    - Two-factor recipient's FortiToken serial number. Source user.fortitoken.serial-number.
                type: str
            id:
                description:
                    - User ID.
                type: int
            ldap_server:
                description:
                    - Name of LDAP server with which the user must authenticate. Source user.ldap.name.
                type: str
            name:
                description:
                    - User name.
                required: true
                type: str
            passwd:
                description:
                    - User's password.
                type: str
            passwd_policy:
                description:
                    - Password policy to apply to this user, as defined in config user password-policy. Source user.password-policy.name.
                type: str
            passwd_time:
                description:
                    - Time of the last password update.
                type: str
            ppk_identity:
                description:
                    - IKEv2 Postquantum Preshared Key Identity.
                type: str
            ppk_secret:
                description:
                    - IKEv2 Postquantum Preshared Key (ASCII string or hexadecimal encoded with a leading 0x).
                type: str
            radius_server:
                description:
                    - Name of RADIUS server with which the user must authenticate. Source user.radius.name.
                type: str
            sms_custom_server:
                description:
                    - Two-factor recipient's SMS server. Source system.sms-server.name.
                type: str
            sms_phone:
                description:
                    - Two-factor recipient's mobile phone number.
                type: str
            sms_server:
                description:
                    - Send SMS through FortiGuard or other external server.
                type: str
                choices:
                    - fortiguard
                    - custom
            status:
                description:
                    - Enable/disable allowing the local user to authenticate with the FortiGate unit.
                type: str
                choices:
                    - enable
                    - disable
            two_factor:
                description:
                    - Enable/disable two-factor authentication.
                type: str
                choices:
                    - disable
                    - fortitoken
                    - email
                    - sms
            type:
                description:
                    - Authentication method.
                type: str
                choices:
                    - password
                    - radius
                    - tacacs+
                    - ldap
            workstation:
                description:
                    - Name of the remote user workstation, if you want to limit the user to authenticate only from a particular workstation.
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
  - name: Configure local users.
    fortios_user_local:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      user_local:
        auth_concurrent_override: "enable"
        auth_concurrent_value: "4"
        authtimeout: "5"
        email_to: "<your_own_value>"
        fortitoken: "<your_own_value> (source user.fortitoken.serial-number)"
        id:  "8"
        ldap_server: "<your_own_value> (source user.ldap.name)"
        name: "default_name_10"
        passwd: "<your_own_value>"
        passwd_policy: "<your_own_value> (source user.password-policy.name)"
        passwd_time: "<your_own_value>"
        ppk_identity: "<your_own_value>"
        ppk_secret: "<your_own_value>"
        radius_server: "<your_own_value> (source user.radius.name)"
        sms_custom_server: "<your_own_value> (source system.sms-server.name)"
        sms_phone: "<your_own_value>"
        sms_server: "fortiguard"
        status: "enable"
        two_factor: "disable"
        type: "password"
        workstation: "<your_own_value>"
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


def filter_user_local_data(json):
    option_list = ['auth_concurrent_override', 'auth_concurrent_value', 'authtimeout',
                   'email_to', 'fortitoken', 'id',
                   'ldap_server', 'name', 'passwd',
                   'passwd_policy', 'passwd_time', 'ppk_identity',
                   'ppk_secret', 'radius_server', 'sms_custom_server',
                   'sms_phone', 'sms_server', 'status',
                   'two_factor', 'type',
                   'workstation']
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


def user_local(data, fos):
    vdom = data['vdom']
    state = data['state']
    user_local_data = data['user_local']
    filtered_data = underscore_to_hyphen(filter_user_local_data(user_local_data))

    if state == "present":
        return fos.set('user',
                       'local',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('user',
                          'local',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_user(data, fos):

    if data['user_local']:
        resp = user_local(data, fos)

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
        "user_local": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "auth_concurrent_override": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "auth_concurrent_value": {"required": False, "type": "int"},
                "authtimeout": {"required": False, "type": "int"},
                "email_to": {"required": False, "type": "str"},
                "fortitoken": {"required": False, "type": "str"},
                "id": {"required": False, "type": "int"},
                "ldap_server": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "passwd": {"required": False, "type": "str"},
                "passwd_policy": {"required": False, "type": "str"},
                "passwd_time": {"required": False, "type": "str"},
                "ppk_identity": {"required": False, "type": "str"},
                "ppk_secret": {"required": False, "type": "str"},
                "radius_server": {"required": False, "type": "str"},
                "sms_custom_server": {"required": False, "type": "str"},
                "sms_phone": {"required": False, "type": "str"},
                "sms_server": {"required": False, "type": "str",
                               "choices": ["fortiguard", "custom"]},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "two_factor": {"required": False, "type": "str",
                               "choices": ["disable", "fortitoken", "email",
                                           "sms"]},
                "type": {"required": False, "type": "str",
                         "choices": ["password", "radius", "tacacs+",
                                     "ldap"]},
                "workstation": {"required": False, "type": "str"}

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
