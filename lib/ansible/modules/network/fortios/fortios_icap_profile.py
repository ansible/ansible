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
module: fortios_icap_profile
short_description: Configure ICAP profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify icap feature and profile category.
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
    icap_profile:
        description:
            - Configure ICAP profiles.
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
            methods:
                description:
                    - The allowed HTTP methods that will be sent to ICAP server for further processing.
                type: str
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
                type: str
            replacemsg_group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
                type: str
            request:
                description:
                    - Enable/disable whether an HTTP request is passed to an ICAP server.
                type: str
                choices:
                    - disable
                    - enable
            request_failure:
                description:
                    - Action to take if the ICAP server cannot be contacted when processing an HTTP request.
                type: str
                choices:
                    - error
                    - bypass
            request_path:
                description:
                    - Path component of the ICAP URI that identifies the HTTP request processing service.
                type: str
            request_server:
                description:
                    - ICAP server to use for an HTTP request. Source icap.server.name.
                type: str
            response:
                description:
                    - Enable/disable whether an HTTP response is passed to an ICAP server.
                type: str
                choices:
                    - disable
                    - enable
            response_failure:
                description:
                    - Action to take if the ICAP server cannot be contacted when processing an HTTP response.
                type: str
                choices:
                    - error
                    - bypass
            response_path:
                description:
                    - Path component of the ICAP URI that identifies the HTTP response processing service.
                type: str
            response_server:
                description:
                    - ICAP server to use for an HTTP response. Source icap.server.name.
                type: str
            streaming_content_bypass:
                description:
                    - Enable/disable bypassing of ICAP server for streaming content.
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
  - name: Configure ICAP profiles.
    fortios_icap_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      icap_profile:
        methods: "delete"
        name: "default_name_4"
        replacemsg_group: "<your_own_value> (source system.replacemsg-group.name)"
        request: "disable"
        request_failure: "error"
        request_path: "<your_own_value>"
        request_server: "<your_own_value> (source icap.server.name)"
        response: "disable"
        response_failure: "error"
        response_path: "<your_own_value>"
        response_server: "<your_own_value> (source icap.server.name)"
        streaming_content_bypass: "disable"
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


def filter_icap_profile_data(json):
    option_list = ['methods', 'name', 'replacemsg_group',
                   'request', 'request_failure', 'request_path',
                   'request_server', 'response', 'response_failure',
                   'response_path', 'response_server', 'streaming_content_bypass']
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


def icap_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['icap_profile'] and data['icap_profile']:
        state = data['icap_profile']['state']
    else:
        state = True
    icap_profile_data = data['icap_profile']
    filtered_data = underscore_to_hyphen(filter_icap_profile_data(icap_profile_data))

    if state == "present":
        return fos.set('icap',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('icap',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_icap(data, fos):

    if data['icap_profile']:
        resp = icap_profile(data, fos)

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
        "icap_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "methods": {"required": False, "type": "str",
                            "choices": ["delete", "get", "head",
                                        "options", "post", "put",
                                        "trace", "other"]},
                "name": {"required": True, "type": "str"},
                "replacemsg_group": {"required": False, "type": "str"},
                "request": {"required": False, "type": "str",
                            "choices": ["disable", "enable"]},
                "request_failure": {"required": False, "type": "str",
                                    "choices": ["error", "bypass"]},
                "request_path": {"required": False, "type": "str"},
                "request_server": {"required": False, "type": "str"},
                "response": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "response_failure": {"required": False, "type": "str",
                                     "choices": ["error", "bypass"]},
                "response_path": {"required": False, "type": "str"},
                "response_server": {"required": False, "type": "str"},
                "streaming_content_bypass": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_icap(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_icap(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
