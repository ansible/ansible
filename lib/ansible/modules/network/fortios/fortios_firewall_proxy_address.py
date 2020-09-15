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
module: fortios_firewall_proxy_address
short_description: Web proxy address configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and proxy_address category.
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
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    firewall_proxy_address:
        description:
            - Web proxy address configuration.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            case_sensitivity:
                description:
                    - Enable to make the pattern case sensitive.
                type: str
                choices:
                    - disable
                    - enable
            category:
                description:
                    - FortiGuard category ID.
                type: list
                suboptions:
                    id:
                        description:
                            - Fortiguard category id.
                        required: true
                        type: int
            color:
                description:
                    - Integer value to determine the color of the icon in the GUI (1 - 32).
                type: int
            comment:
                description:
                    - Optional comments.
                type: str
            header:
                description:
                    - HTTP header name as a regular expression.
                type: str
            header_group:
                description:
                    - HTTP header group.
                type: list
                suboptions:
                    case_sensitivity:
                        description:
                            - Case sensitivity in pattern.
                        type: str
                        choices:
                            - disable
                            - enable
                    header:
                        description:
                            - HTTP header regular expression.
                        type: str
                    header_name:
                        description:
                            - HTTP header.
                        type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
            header_name:
                description:
                    - Name of HTTP header.
                type: str
            host:
                description:
                    - Address object for the host. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name.
                type: str
            host_regex:
                description:
                    - Host name as a regular expression.
                type: str
            method:
                description:
                    - HTTP request methods to be used.
                type: str
                choices:
                    - get
                    - post
                    - put
                    - head
                    - connect
                    - trace
                    - options
                    - delete
            name:
                description:
                    - Address name.
                required: true
                type: str
            path:
                description:
                    - URL path as a regular expression.
                type: str
            query:
                description:
                    - Match the query part of the URL as a regular expression.
                type: str
            referrer:
                description:
                    - Enable/disable use of referrer field in the HTTP header to match the address.
                type: str
                choices:
                    - enable
                    - disable
            tagging:
                description:
                    - Config object tagging.
                type: list
                suboptions:
                    category:
                        description:
                            - Tag category. Source system.object-tagging.category.
                        type: str
                    name:
                        description:
                            - Tagging entry name.
                        required: true
                        type: str
                    tags:
                        description:
                            - Tags.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Tag name. Source system.object-tagging.tags.name.
                                required: true
                                type: str
            type:
                description:
                    - Proxy address type.
                type: str
                choices:
                    - host-regex
                    - url
                    - category
                    - method
                    - ua
                    - header
                    - src-advanced
                    - dst-advanced
            ua:
                description:
                    - Names of browsers to be used as user agent.
                type: str
                choices:
                    - chrome
                    - ms
                    - firefox
                    - safari
                    - other
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
                type: str
            visibility:
                description:
                    - Enable/disable visibility of the object in the GUI.
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
  - name: Web proxy address configuration.
    fortios_firewall_proxy_address:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_proxy_address:
        case_sensitivity: "disable"
        category:
         -
            id:  "5"
        color: "6"
        comment: "Optional comments."
        header: "<your_own_value>"
        header_group:
         -
            case_sensitivity: "disable"
            header: "<your_own_value>"
            header_name: "<your_own_value>"
            id:  "13"
        header_name: "<your_own_value>"
        host: "myhostname (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name)"
        host_regex: "myhostname"
        method: "get"
        name: "default_name_18"
        path: "<your_own_value>"
        query: "<your_own_value>"
        referrer: "enable"
        tagging:
         -
            category: "<your_own_value> (source system.object-tagging.category)"
            name: "default_name_24"
            tags:
             -
                name: "default_name_26 (source system.object-tagging.tags.name)"
        type: "host-regex"
        ua: "chrome"
        uuid: "<your_own_value>"
        visibility: "enable"
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


def filter_firewall_proxy_address_data(json):
    option_list = ['case_sensitivity', 'category', 'color',
                   'comment', 'header', 'header_group',
                   'header_name', 'host', 'host_regex',
                   'method', 'name', 'path',
                   'query', 'referrer', 'tagging',
                   'type', 'ua', 'uuid',
                   'visibility']
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


def firewall_proxy_address(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_proxy_address'] and data['firewall_proxy_address']:
        state = data['firewall_proxy_address']['state']
    else:
        state = True
    firewall_proxy_address_data = data['firewall_proxy_address']
    filtered_data = underscore_to_hyphen(filter_firewall_proxy_address_data(firewall_proxy_address_data))

    if state == "present":
        return fos.set('firewall',
                       'proxy-address',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'proxy-address',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_proxy_address']:
        resp = firewall_proxy_address(data, fos)

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
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "firewall_proxy_address": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "case_sensitivity": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]},
                "category": {"required": False, "type": "list",
                             "options": {
                                 "id": {"required": True, "type": "int"}
                             }},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "header": {"required": False, "type": "str"},
                "header_group": {"required": False, "type": "list",
                                 "options": {
                                     "case_sensitivity": {"required": False, "type": "str",
                                                          "choices": ["disable", "enable"]},
                                     "header": {"required": False, "type": "str"},
                                     "header_name": {"required": False, "type": "str"},
                                     "id": {"required": True, "type": "int"}
                                 }},
                "header_name": {"required": False, "type": "str"},
                "host": {"required": False, "type": "str"},
                "host_regex": {"required": False, "type": "str"},
                "method": {"required": False, "type": "str",
                           "choices": ["get", "post", "put",
                                       "head", "connect", "trace",
                                       "options", "delete"]},
                "name": {"required": True, "type": "str"},
                "path": {"required": False, "type": "str"},
                "query": {"required": False, "type": "str"},
                "referrer": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "tagging": {"required": False, "type": "list",
                            "options": {
                                "category": {"required": False, "type": "str"},
                                "name": {"required": True, "type": "str"},
                                "tags": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }}
                            }},
                "type": {"required": False, "type": "str",
                         "choices": ["host-regex", "url", "category",
                                     "method", "ua", "header",
                                     "src-advanced", "dst-advanced"]},
                "ua": {"required": False, "type": "str",
                       "choices": ["chrome", "ms", "firefox",
                                   "safari", "other"]},
                "uuid": {"required": False, "type": "str"},
                "visibility": {"required": False, "type": "str",
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
