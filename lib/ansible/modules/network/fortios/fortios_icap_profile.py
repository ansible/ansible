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
module: fortios_icap_profile
short_description: Configure ICAP profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure icap feature and profile category.
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
            - FortiOS or FortiGate ip adress.
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
    icap_profile:
        description:
            - Configure ICAP profiles.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            methods:
                description:
                    - The allowed HTTP methods that will be sent to ICAP server for further processing.
                choices:
                    - delete
                    - get
                    - head
                    - options
                    - post
                    - put
                    - trace
                    - other
            name:
                description:
                    - ICAP profile name.
                required: true
            replacemsg-group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
            request:
                description:
                    - Enable/disable whether an HTTP request is passed to an ICAP server.
                choices:
                    - disable
                    - enable
            request-failure:
                description:
                    - Action to take if the ICAP server cannot be contacted when processing an HTTP request.
                choices:
                    - error
                    - bypass
            request-path:
                description:
                    - Path component of the ICAP URI that identifies the HTTP request processing service.
            request-server:
                description:
                    - ICAP server to use for an HTTP request. Source icap.server.name.
            response:
                description:
                    - Enable/disable whether an HTTP response is passed to an ICAP server.
                choices:
                    - disable
                    - enable
            response-failure:
                description:
                    - Action to take if the ICAP server cannot be contacted when processing an HTTP response.
                choices:
                    - error
                    - bypass
            response-path:
                description:
                    - Path component of the ICAP URI that identifies the HTTP response processing service.
            response-server:
                description:
                    - ICAP server to use for an HTTP response. Source icap.server.name.
            streaming-content-bypass:
                description:
                    - Enable/disable bypassing of ICAP server for streaming content.
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
  tasks:
  - name: Configure ICAP profiles.
    fortios_icap_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      icap_profile:
        state: "present"
        methods: "delete"
        name: "default_name_4"
        replacemsg-group: "<your_own_value> (source system.replacemsg-group.name)"
        request: "disable"
        request-failure: "error"
        request-path: "<your_own_value>"
        request-server: "<your_own_value> (source icap.server.name)"
        response: "disable"
        response-failure: "error"
        response-path: "<your_own_value>"
        response-server: "<your_own_value> (source icap.server.name)"
        streaming-content-bypass: "disable"
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


def filter_icap_profile_data(json):
    option_list = ['methods', 'name', 'replacemsg-group',
                   'request', 'request-failure', 'request-path',
                   'request-server', 'response', 'response-failure',
                   'response-path', 'response-server', 'streaming-content-bypass']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def icap_profile(data, fos):
    vdom = data['vdom']
    icap_profile_data = data['icap_profile']
    filtered_data = filter_icap_profile_data(icap_profile_data)
    if icap_profile_data['state'] == "present":
        return fos.set('icap',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif icap_profile_data['state'] == "absent":
        return fos.delete('icap',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_icap(data, fos):
    login(data)

    methodlist = ['icap_profile']
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
        "icap_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "methods": {"required": False, "type": "str",
                            "choices": ["delete", "get", "head",
                                        "options", "post", "put",
                                        "trace", "other"]},
                "name": {"required": True, "type": "str"},
                "replacemsg-group": {"required": False, "type": "str"},
                "request": {"required": False, "type": "str",
                            "choices": ["disable", "enable"]},
                "request-failure": {"required": False, "type": "str",
                                    "choices": ["error", "bypass"]},
                "request-path": {"required": False, "type": "str"},
                "request-server": {"required": False, "type": "str"},
                "response": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "response-failure": {"required": False, "type": "str",
                                     "choices": ["error", "bypass"]},
                "response-path": {"required": False, "type": "str"},
                "response-server": {"required": False, "type": "str"},
                "streaming-content-bypass": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]}

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

    is_error, has_changed, result = fortios_icap(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
