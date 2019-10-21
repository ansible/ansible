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
module: fortios_web_proxy_profile
short_description: Configure web proxy profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify web_proxy feature and profile category.
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
    web_proxy_profile:
        description:
            - Configure web proxy profiles.
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
            header_client_ip:
                description:
                    - "Action to take on the HTTP client-IP header in forwarded requests: forwards (pass), adds, or removes the HTTP header."
                type: str
                choices:
                    - pass
                    - add
                    - remove
            header_front_end_https:
                description:
                    - "Action to take on the HTTP front-end-HTTPS header in forwarded requests: forwards (pass), adds, or removes the HTTP header."
                type: str
                choices:
                    - pass
                    - add
                    - remove
            header_via_request:
                description:
                    - "Action to take on the HTTP via header in forwarded requests: forwards (pass), adds, or removes the HTTP header."
                type: str
                choices:
                    - pass
                    - add
                    - remove
            header_via_response:
                description:
                    - "Action to take on the HTTP via header in forwarded responses: forwards (pass), adds, or removes the HTTP header."
                type: str
                choices:
                    - pass
                    - add
                    - remove
            header_x_authenticated_groups:
                description:
                    - "Action to take on the HTTP x-authenticated-groups header in forwarded requests: forwards (pass), adds, or removes the HTTP header."
                type: str
                choices:
                    - pass
                    - add
                    - remove
            header_x_authenticated_user:
                description:
                    - "Action to take on the HTTP x-authenticated-user header in forwarded requests: forwards (pass), adds, or removes the HTTP header."
                type: str
                choices:
                    - pass
                    - add
                    - remove
            header_x_forwarded_for:
                description:
                    - "Action to take on the HTTP x-forwarded-for header in forwarded requests: forwards (pass), adds, or removes the HTTP header."
                type: str
                choices:
                    - pass
                    - add
                    - remove
            headers:
                description:
                    - Configure HTTP forwarded requests headers.
                type: list
                suboptions:
                    action:
                        description:
                            - Action when HTTP the header forwarded.
                        type: str
                        choices:
                            - add-to-request
                            - add-to-response
                            - remove-from-request
                            - remove-from-response
                    content:
                        description:
                            - HTTP header's content.
                        type: str
                    id:
                        description:
                            - HTTP forwarded header id.
                        required: true
                        type: int
                    name:
                        description:
                            - HTTP forwarded header name.
                        type: str
            log_header_change:
                description:
                    - Enable/disable logging HTTP header changes.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Profile name.
                required: true
                type: str
            strip_encoding:
                description:
                    - Enable/disable stripping unsupported encoding from the request header.
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
  - name: Configure web proxy profiles.
    fortios_web_proxy_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      web_proxy_profile:
        header_client_ip: "pass"
        header_front_end_https: "pass"
        header_via_request: "pass"
        header_via_response: "pass"
        header_x_authenticated_groups: "pass"
        header_x_authenticated_user: "pass"
        header_x_forwarded_for: "pass"
        headers:
         -
            action: "add-to-request"
            content: "<your_own_value>"
            id:  "13"
            name: "default_name_14"
        log_header_change: "enable"
        name: "default_name_16"
        strip_encoding: "enable"
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


def filter_web_proxy_profile_data(json):
    option_list = ['header_client_ip', 'header_front_end_https', 'header_via_request',
                   'header_via_response', 'header_x_authenticated_groups', 'header_x_authenticated_user',
                   'header_x_forwarded_for', 'headers', 'log_header_change',
                   'name', 'strip_encoding']
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


def web_proxy_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['web_proxy_profile'] and data['web_proxy_profile']:
        state = data['web_proxy_profile']['state']
    else:
        state = True
    web_proxy_profile_data = data['web_proxy_profile']
    filtered_data = underscore_to_hyphen(filter_web_proxy_profile_data(web_proxy_profile_data))

    if state == "present":
        return fos.set('web-proxy',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('web-proxy',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_web_proxy(data, fos):

    if data['web_proxy_profile']:
        resp = web_proxy_profile(data, fos)

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
        "web_proxy_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "header_client_ip": {"required": False, "type": "str",
                                     "choices": ["pass", "add", "remove"]},
                "header_front_end_https": {"required": False, "type": "str",
                                           "choices": ["pass", "add", "remove"]},
                "header_via_request": {"required": False, "type": "str",
                                       "choices": ["pass", "add", "remove"]},
                "header_via_response": {"required": False, "type": "str",
                                        "choices": ["pass", "add", "remove"]},
                "header_x_authenticated_groups": {"required": False, "type": "str",
                                                  "choices": ["pass", "add", "remove"]},
                "header_x_authenticated_user": {"required": False, "type": "str",
                                                "choices": ["pass", "add", "remove"]},
                "header_x_forwarded_for": {"required": False, "type": "str",
                                           "choices": ["pass", "add", "remove"]},
                "headers": {"required": False, "type": "list",
                            "options": {
                                "action": {"required": False, "type": "str",
                                           "choices": ["add-to-request", "add-to-response", "remove-from-request",
                                                       "remove-from-response"]},
                                "content": {"required": False, "type": "str"},
                                "id": {"required": True, "type": "int"},
                                "name": {"required": False, "type": "str"}
                            }},
                "log_header_change": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "strip_encoding": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_web_proxy(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_web_proxy(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
