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
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_firewall_proxy_address
short_description: Web proxy address configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and proxy_address category.
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
        default: true
    firewall_proxy_address:
        description:
            - Web proxy address configuration.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            case-sensitivity:
                description:
                    - Enable to make the pattern case sensitive.
                choices:
                    - disable
                    - enable
            category:
                description:
                    - FortiGuard category ID.
                suboptions:
                    id:
                        description:
                            - Fortiguard category id.
                        required: true
            color:
                description:
                    - Integer value to determine the color of the icon in the GUI (1 - 32, default = 0, which sets value to 1).
            comment:
                description:
                    - Optional comments.
            header:
                description:
                    - HTTP header name as a regular expression.
            header-group:
                description:
                    - HTTP header group.
                suboptions:
                    case-sensitivity:
                        description:
                            - Case sensitivity in pattern.
                        choices:
                            - disable
                            - enable
                    header:
                        description:
                            - HTTP header regular expression.
                    header-name:
                        description:
                            - HTTP header.
                    id:
                        description:
                            - ID.
                        required: true
            header-name:
                description:
                    - Name of HTTP header.
            host:
                description:
                    - Address object for the host. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name.
            host-regex:
                description:
                    - Host name as a regular expression.
            method:
                description:
                    - HTTP request methods to be used.
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
            path:
                description:
                    - URL path as a regular expression.
            query:
                description:
                    - Match the query part of the URL as a regular expression.
            referrer:
                description:
                    - Enable/disable use of referrer field in the HTTP header to match the address.
                choices:
                    - enable
                    - disable
            tagging:
                description:
                    - Config object tagging.
                suboptions:
                    category:
                        description:
                            - Tag category. Source system.object-tagging.category.
                    name:
                        description:
                            - Tagging entry name.
                        required: true
                    tags:
                        description:
                            - Tags.
                        suboptions:
                            name:
                                description:
                                    - Tag name. Source system.object-tagging.tags.name.
                                required: true
            type:
                description:
                    - Proxy address type.
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
                choices:
                    - chrome
                    - ms
                    - firefox
                    - safari
                    - other
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
            visibility:
                description:
                    - Enable/disable visibility of the object in the GUI.
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
  - name: Web proxy address configuration.
    fortios_firewall_proxy_address:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_proxy_address:
        state: "present"
        case-sensitivity: "disable"
        category:
         -
            id:  "5"
        color: "6"
        comment: "Optional comments."
        header: "<your_own_value>"
        header-group:
         -
            case-sensitivity: "disable"
            header: "<your_own_value>"
            header-name: "<your_own_value>"
            id:  "13"
        header-name: "<your_own_value>"
        host: "myhostname (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name)"
        host-regex: "myhostname"
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


def filter_firewall_proxy_address_data(json):
    option_list = ['case-sensitivity', 'category', 'color',
                   'comment', 'header', 'header-group',
                   'header-name', 'host', 'host-regex',
                   'method', 'name', 'path',
                   'query', 'referrer', 'tagging',
                   'type', 'ua', 'uuid',
                   'visibility']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_proxy_address(data, fos):
    vdom = data['vdom']
    firewall_proxy_address_data = data['firewall_proxy_address']
    filtered_data = filter_firewall_proxy_address_data(firewall_proxy_address_data)
    if firewall_proxy_address_data['state'] == "present":
        return fos.set('firewall',
                       'proxy-address',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_proxy_address_data['state'] == "absent":
        return fos.delete('firewall',
                          'proxy-address',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_proxy_address']
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
        "https": {"required": False, "type": "bool", "default": True},
        "firewall_proxy_address": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "case-sensitivity": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]},
                "category": {"required": False, "type": "list",
                             "options": {
                                 "id": {"required": True, "type": "int"}
                             }},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "header": {"required": False, "type": "str"},
                "header-group": {"required": False, "type": "list",
                                 "options": {
                                     "case-sensitivity": {"required": False, "type": "str",
                                                          "choices": ["disable", "enable"]},
                                     "header": {"required": False, "type": "str"},
                                     "header-name": {"required": False, "type": "str"},
                                     "id": {"required": True, "type": "int"}
                                 }},
                "header-name": {"required": False, "type": "str"},
                "host": {"required": False, "type": "str"},
                "host-regex": {"required": False, "type": "str"},
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
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
