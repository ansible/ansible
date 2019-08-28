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
module: fortios_firewall_ipv6_eh_filter
short_description: Configure IPv6 extension header filter in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and ipv6_eh_filter category.
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
    firewall_ipv6_eh_filter:
        description:
            - Configure IPv6 extension header filter.
        default: null
        type: dict
        suboptions:
            auth:
                description:
                    - Enable/disable blocking packets with the Authentication header .
                type: str
                choices:
                    - enable
                    - disable
            dest_opt:
                description:
                    - Enable/disable blocking packets with Destination Options headers .
                type: str
                choices:
                    - enable
                    - disable
            fragment:
                description:
                    - Enable/disable blocking packets with the Fragment header .
                type: str
                choices:
                    - enable
                    - disable
            hdopt_type:
                description:
                    - Block specific Hop-by-Hop and/or Destination Option types (max. 7 types, each between 0 and 255).
                type: int
            hop_opt:
                description:
                    - Enable/disable blocking packets with the Hop-by-Hop Options header .
                type: str
                choices:
                    - enable
                    - disable
            no_next:
                description:
                    - Enable/disable blocking packets with the No Next header
                type: str
                choices:
                    - enable
                    - disable
            routing:
                description:
                    - Enable/disable blocking packets with Routing headers .
                type: str
                choices:
                    - enable
                    - disable
            routing_type:
                description:
                    - Block specific Routing header types (max. 7 types, each between 0 and 255).
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
  - name: Configure IPv6 extension header filter.
    fortios_firewall_ipv6_eh_filter:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_ipv6_eh_filter:
        auth: "enable"
        dest_opt: "enable"
        fragment: "enable"
        hdopt_type: "6"
        hop_opt: "enable"
        no_next: "enable"
        routing: "enable"
        routing_type: "10"
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


def filter_firewall_ipv6_eh_filter_data(json):
    option_list = ['auth', 'dest_opt', 'fragment',
                   'hdopt_type', 'hop_opt', 'no_next',
                   'routing', 'routing_type']
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


def firewall_ipv6_eh_filter(data, fos):
    vdom = data['vdom']
    firewall_ipv6_eh_filter_data = data['firewall_ipv6_eh_filter']
    filtered_data = underscore_to_hyphen(filter_firewall_ipv6_eh_filter_data(firewall_ipv6_eh_filter_data))

    return fos.set('firewall',
                   'ipv6-eh-filter',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_ipv6_eh_filter']:
        resp = firewall_ipv6_eh_filter(data, fos)

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
        "firewall_ipv6_eh_filter": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "auth": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "dest_opt": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "fragment": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "hdopt_type": {"required": False, "type": "int"},
                "hop_opt": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "no_next": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "routing": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "routing_type": {"required": False, "type": "int"}

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

            is_error, has_changed, result = fortios_firewall(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_firewall(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
