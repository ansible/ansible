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
module: fortios_user_group
short_description: Configure user groups in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify user feature and group category.
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
    user_group:
        description:
            - Configure user groups.
        default: null
        type: dict
        suboptions:
            auth_concurrent_override:
                description:
                    - Enable/disable overriding the global number of concurrent authentication sessions for this user group.
                type: str
                choices:
                    - enable
                    - disable
            auth_concurrent_value:
                description:
                    - Maximum number of concurrent authenticated connections per user (0 - 100).
                type: int
            authtimeout:
                description:
                    - Authentication timeout in minutes for this user group. 0 to use the global user setting auth-timeout.
                type: int
            company:
                description:
                    - Set the action for the company guest user field.
                type: str
                choices:
                    - optional
                    - mandatory
                    - disabled
            email:
                description:
                    - Enable/disable the guest user email address field.
                type: str
                choices:
                    - disable
                    - enable
            expire:
                description:
                    - Time in seconds before guest user accounts expire. (1 - 31536000 sec)
                type: int
            expire_type:
                description:
                    - Determine when the expiration countdown begins.
                type: str
                choices:
                    - immediately
                    - first-successful-login
            group_type:
                description:
                    - Set the group to be for firewall authentication, FSSO, RSSO, or guest users.
                type: str
                choices:
                    - firewall
                    - fsso-service
                    - rsso
                    - guest
            guest:
                description:
                    - Guest User.
                type: list
                suboptions:
                    comment:
                        description:
                            - Comment.
                        type: str
                    company:
                        description:
                            - Set the action for the company guest user field.
                        type: str
                    email:
                        description:
                            - Email.
                        type: str
                    expiration:
                        description:
                            - Expire time.
                        type: str
                    mobile_phone:
                        description:
                            - Mobile phone.
                        type: str
                    name:
                        description:
                            - Guest name.
                        type: str
                    password:
                        description:
                            - Guest password.
                        type: str
                    sponsor:
                        description:
                            - Set the action for the sponsor guest user field.
                        type: str
                    user_id:
                        description:
                            - Guest ID.
                        type: str
            http_digest_realm:
                description:
                    - Realm attribute for MD5-digest authentication.
                type: str
            id:
                description:
                    - Group ID.
                type: int
            match:
                description:
                    - Group matches.
                type: list
                suboptions:
                    group_name:
                        description:
                            - Name of matching group on remote authentication server.
                        type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    server_name:
                        description:
                            - Name of remote auth server. Source user.radius.name user.ldap.name user.tacacs+.name.
                        type: str
            max_accounts:
                description:
                    - Maximum number of guest accounts that can be created for this group (0 means unlimited).
                type: int
            member:
                description:
                    - Names of users, peers, LDAP servers, or RADIUS servers to add to the user group.
                type: list
                suboptions:
                    name:
                        description:
                            - Group member name. Source user.peer.name user.local.name user.radius.name user.tacacs+.name user.ldap.name user.adgrp.name user
                              .pop3.name.
                        required: true
                        type: str
            mobile_phone:
                description:
                    - Enable/disable the guest user mobile phone number field.
                type: str
                choices:
                    - disable
                    - enable
            multiple_guest_add:
                description:
                    - Enable/disable addition of multiple guests.
                type: str
                choices:
                    - disable
                    - enable
            name:
                description:
                    - Group name.
                required: true
                type: str
            password:
                description:
                    - Guest user password type.
                type: str
                choices:
                    - auto-generate
                    - specify
                    - disable
            sms_custom_server:
                description:
                    - SMS server. Source system.sms-server.name.
                type: str
            sms_server:
                description:
                    - Send SMS through FortiGuard or other external server.
                type: str
                choices:
                    - fortiguard
                    - custom
            sponsor:
                description:
                    - Set the action for the sponsor guest user field.
                type: str
                choices:
                    - optional
                    - mandatory
                    - disabled
            sso_attribute_value:
                description:
                    - Name of the RADIUS user group that this local user group represents.
                type: str
            user_id:
                description:
                    - Guest user ID type.
                type: str
                choices:
                    - email
                    - auto-generate
                    - specify
            user_name:
                description:
                    - Enable/disable the guest user name entry.
                type: str
                choices:
                    - disable
                    - enable
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
  - name: Configure user groups.
    fortios_user_group:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      user_group:
        auth_concurrent_override: "enable"
        auth_concurrent_value: "4"
        authtimeout: "5"
        company: "optional"
        email: "disable"
        expire: "8"
        expire_type: "immediately"
        group_type: "firewall"
        guest:
         -
            comment: "Comment."
            company: "<your_own_value>"
            email: "<your_own_value>"
            expiration: "<your_own_value>"
            mobile_phone: "<your_own_value>"
            name: "default_name_17"
            password: "<your_own_value>"
            sponsor: "<your_own_value>"
            user_id: "<your_own_value>"
        http_digest_realm: "<your_own_value>"
        id:  "22"
        match:
         -
            group_name: "<your_own_value>"
            id:  "25"
            server_name: "<your_own_value> (source user.radius.name user.ldap.name user.tacacs+.name)"
        max_accounts: "27"
        member:
         -
            name: "default_name_29 (source user.peer.name user.local.name user.radius.name user.tacacs+.name user.ldap.name user.adgrp.name user.pop3.name)"
        mobile_phone: "disable"
        multiple_guest_add: "disable"
        name: "default_name_32"
        password: "auto-generate"
        sms_custom_server: "<your_own_value> (source system.sms-server.name)"
        sms_server: "fortiguard"
        sponsor: "optional"
        sso_attribute_value: "<your_own_value>"
        user_id: "email"
        user_name: "disable"
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


def filter_user_group_data(json):
    option_list = ['auth_concurrent_override', 'auth_concurrent_value', 'authtimeout',
                   'company', 'email', 'expire',
                   'expire_type', 'group_type', 'guest',
                   'http_digest_realm', 'id', 'match',
                   'max_accounts', 'member', 'mobile_phone',
                   'multiple_guest_add', 'name', 'password',
                   'sms_custom_server', 'sms_server', 'sponsor',
                   'sso_attribute_value', 'user_id', 'user_name']
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


def user_group(data, fos):
    vdom = data['vdom']
    state = data['state']
    user_group_data = data['user_group']
    filtered_data = underscore_to_hyphen(filter_user_group_data(user_group_data))

    if state == "present":
        return fos.set('user',
                       'group',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('user',
                          'group',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_user(data, fos):

    if data['user_group']:
        resp = user_group(data, fos)

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
        "user_group": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "auth_concurrent_override": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "auth_concurrent_value": {"required": False, "type": "int"},
                "authtimeout": {"required": False, "type": "int"},
                "company": {"required": False, "type": "str",
                            "choices": ["optional", "mandatory", "disabled"]},
                "email": {"required": False, "type": "str",
                          "choices": ["disable", "enable"]},
                "expire": {"required": False, "type": "int"},
                "expire_type": {"required": False, "type": "str",
                                "choices": ["immediately", "first-successful-login"]},
                "group_type": {"required": False, "type": "str",
                               "choices": ["firewall", "fsso-service", "rsso",
                                           "guest"]},
                "guest": {"required": False, "type": "list",
                          "options": {
                              "comment": {"required": False, "type": "str"},
                              "company": {"required": False, "type": "str"},
                              "email": {"required": False, "type": "str"},
                              "expiration": {"required": False, "type": "str"},
                              "mobile_phone": {"required": False, "type": "str"},
                              "name": {"required": False, "type": "str"},
                              "password": {"required": False, "type": "str", "no_log": True},
                              "sponsor": {"required": False, "type": "str"},
                              "user_id": {"required": False, "type": "str"}
                          }},
                "http_digest_realm": {"required": False, "type": "str"},
                "id": {"required": False, "type": "int"},
                "match": {"required": False, "type": "list",
                          "options": {
                              "group_name": {"required": False, "type": "str"},
                              "id": {"required": True, "type": "int"},
                              "server_name": {"required": False, "type": "str"}
                          }},
                "max_accounts": {"required": False, "type": "int"},
                "member": {"required": False, "type": "list",
                           "options": {
                               "name": {"required": True, "type": "str"}
                           }},
                "mobile_phone": {"required": False, "type": "str",
                                 "choices": ["disable", "enable"]},
                "multiple_guest_add": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                "name": {"required": True, "type": "str"},
                "password": {"required": False, "type": "str",
                             "choices": ["auto-generate", "specify", "disable"]},
                "sms_custom_server": {"required": False, "type": "str"},
                "sms_server": {"required": False, "type": "str",
                               "choices": ["fortiguard", "custom"]},
                "sponsor": {"required": False, "type": "str",
                            "choices": ["optional", "mandatory", "disabled"]},
                "sso_attribute_value": {"required": False, "type": "str"},
                "user_id": {"required": False, "type": "str",
                            "choices": ["email", "auto-generate", "specify"]},
                "user_name": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]}

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
