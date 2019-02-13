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
module: fortios_webfilter_fortiguard
short_description: Configure FortiGuard Web Filter service.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure webfilter feature and fortiguard category.
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
    webfilter_fortiguard:
        description:
            - Configure FortiGuard Web Filter service.
        default: null
        suboptions:
            cache-mem-percent:
                description:
                    - Maximum percentage of available memory allocated to caching (1 - 15%).
            cache-mode:
                description:
                    - Cache entry expiration mode.
                choices:
                    - ttl
                    - db-ver
            cache-prefix-match:
                description:
                    - Enable/disable prefix matching in the cache.
                choices:
                    - enable
                    - disable
            close-ports:
                description:
                    - Close ports used for HTTP/HTTPS override authentication and disable user overrides.
                choices:
                    - enable
                    - disable
            ovrd-auth-https:
                description:
                    - Enable/disable use of HTTPS for override authentication.
                choices:
                    - enable
                    - disable
            ovrd-auth-port:
                description:
                    - Port to use for FortiGuard Web Filter override authentication.
            ovrd-auth-port-http:
                description:
                    - Port to use for FortiGuard Web Filter HTTP override authentication
            ovrd-auth-port-https:
                description:
                    - Port to use for FortiGuard Web Filter HTTPS override authentication.
            ovrd-auth-port-warning:
                description:
                    - Port to use for FortiGuard Web Filter Warning override authentication.
            request-packet-size-limit:
                description:
                    - Limit size of URL request packets sent to FortiGuard server (0 for default).
            warn-auth-https:
                description:
                    - Enable/disable use of HTTPS for warning and authentication.
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
  - name: Configure FortiGuard Web Filter service.
    fortios_webfilter_fortiguard:
      host:  "{{  host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{  vdom }}"
      webfilter_fortiguard:
        cache-mem-percent: "3"
        cache-mode: "ttl"
        cache-prefix-match: "enable"
        close-ports: "enable"
        ovrd-auth-https: "enable"
        ovrd-auth-port: "8"
        ovrd-auth-port-http: "9"
        ovrd-auth-port-https: "10"
        ovrd-auth-port-warning: "11"
        request-packet-size-limit: "12"
        warn-auth-https: "enable"
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
  sample: "key1"
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


def filter_webfilter_fortiguard_data(json):
    option_list = ['cache-mem-percent', 'cache-mode', 'cache-prefix-match',
                   'close-ports', 'ovrd-auth-https', 'ovrd-auth-port',
                   'ovrd-auth-port-http', 'ovrd-auth-port-https', 'ovrd-auth-port-warning',
                   'request-packet-size-limit', 'warn-auth-https']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def webfilter_fortiguard(data, fos):
    vdom = data['vdom']
    webfilter_fortiguard_data = data['webfilter_fortiguard']
    filtered_data = filter_webfilter_fortiguard_data(webfilter_fortiguard_data)
    return fos.set('webfilter',
                   'fortiguard',
                   data=filtered_data,
                   vdom=vdom)


def fortios_webfilter(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    fos.https('off')
    fos.login(host, username, password)

    methodlist = ['webfilter_fortiguard']
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
        "webfilter_fortiguard": {
            "required": False, "type": "dict",
            "options": {
                "cache-mem-percent": {"required": False, "type": "int"},
                "cache-mode": {"required": False, "type": "str",
                               "choices": ["ttl", "db-ver"]},
                "cache-prefix-match": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "close-ports": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "ovrd-auth-https": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "ovrd-auth-port": {"required": False, "type": "int"},
                "ovrd-auth-port-http": {"required": False, "type": "int"},
                "ovrd-auth-port-https": {"required": False, "type": "int"},
                "ovrd-auth-port-warning": {"required": False, "type": "int"},
                "request-packet-size-limit": {"required": False, "type": "int"},
                "warn-auth-https": {"required": False, "type": "str",
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

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_webfilter(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
