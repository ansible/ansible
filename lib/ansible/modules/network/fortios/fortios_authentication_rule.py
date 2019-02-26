#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2018 Fortinet, Inc.
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
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_authentication_rule
short_description: Configure Authentication Rules in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure authentication feature and rule category.
      Examples includes all options and need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
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
            - FortiOS or FortiGate ip address.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: false
    authentication_rule:
        description:
            - Configure Authentication Rules.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            active-auth-method:
                description:
                    - Select an active authentication method. Source authentication.scheme.name.
            comments:
                description:
                    - Comment.
            ip-based:
                description:
                    - Enable/disable IP-based authentication. Once a user authenticates all traffic from the IP address the user authenticated from is allowed.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Authentication rule name.
                required: true
            protocol:
                description:
                    - Select the protocol to use for authentication (default = http). Users connect to the FortiGate using this protocol and are asked to
                       authenticate.
                choices:
                    - http
                    - ftp
                    - socks
                    - ssh
            srcaddr:
                description:
                    - Select an IPv4 source address from available options. Required for web proxy authentication.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name.
                        required: true
            srcaddr6:
                description:
                    - Select an IPv6 source address. Required for web proxy authentication.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            sso-auth-method:
                description:
                    - Select a single-sign on (SSO) authentication method. Source authentication.scheme.name.
            status:
                description:
                    - Enable/disable this authentication rule.
                choices:
                    - enable
                    - disable
            transaction-based:
                description:
                    - Enable/disable transaction based authentication (default = disable).
                choices:
                    - enable
                    - disable
            web-auth-cookie:
                description:
                    - Enable/disable Web authentication cookies (default = disable).
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
  tasks:
  - name: Configure Authentication Rules.
    fortios_authentication_rule:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      authentication_rule:
        state: "present"
        active-auth-method: "<your_own_value> (source authentication.scheme.name)"
        comments: "<your_own_value>"
        ip-based: "enable"
        name: "default_name_6"
        protocol: "http"
        srcaddr:
         -
            name: "default_name_9 (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name)"
        srcaddr6:
         -
            name: "default_name_11 (source firewall.address6.name firewall.addrgrp6.name)"
        sso-auth-method: "<your_own_value> (source authentication.scheme.name)"
        status: "enable"
        transaction-based: "enable"
        web-auth-cookie: "enable"
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

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_authentication_rule_data(json):
    option_list = ['active-auth-method', 'comments', 'ip-based',
                   'name', 'protocol', 'srcaddr',
                   'srcaddr6', 'sso-auth-method', 'status',
                   'transaction-based', 'web-auth-cookie']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def authentication_rule(data, fos):
    vdom = data['vdom']
    authentication_rule_data = data['authentication_rule']
    filtered_data = filter_authentication_rule_data(authentication_rule_data)
    if authentication_rule_data['state'] == "present":
        return fos.set('authentication',
                       'rule',
                       data=filtered_data,
                       vdom=vdom)

    elif authentication_rule_data['state'] == "absent":
        return fos.delete('authentication',
                          'rule',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_authentication(data, fos):
    login(data)

    methodlist = ['authentication_rule']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": "False"},
        "authentication_rule": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "active-auth-method": {"required": False, "type": "str"},
                "comments": {"required": False, "type": "str"},
                "ip-based": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "protocol": {"required": False, "type": "str",
                             "choices": ["http", "ftp", "socks",
                                         "ssh"]},
                "srcaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "srcaddr6": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "sso-auth-method": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "transaction-based": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "web-auth-cookie": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_authentication(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
