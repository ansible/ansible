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
module: fortios_wanopt_content_delivery_network_rule
short_description: Configure WAN optimization content delivery network rules in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wanopt feature and content_delivery_network_rule category.
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
    wanopt_content_delivery_network_rule:
        description:
            - Configure WAN optimization content delivery network rules.
        default: null
        type: dict
        suboptions:
            category:
                description:
                    - Content delivery network rule category.
                type: str
                choices:
                    - vcache
                    - youtube
            comment:
                description:
                    - Comment about this CDN-rule.
                type: str
            host_domain_name_suffix:
                description:
                    - Suffix portion of the fully qualified domain name (eg. fortinet.com in "www.fortinet.com").
                type: list
                suboptions:
                    name:
                        description:
                            - Suffix portion of the fully qualified domain name.
                        required: true
                        type: str
            name:
                description:
                    - Name of table.
                required: true
                type: str
            request_cache_control:
                description:
                    - Enable/disable HTTP request cache control.
                type: str
                choices:
                    - enable
                    - disable
            response_cache_control:
                description:
                    - Enable/disable HTTP response cache control.
                type: str
                choices:
                    - enable
                    - disable
            response_expires:
                description:
                    - Enable/disable HTTP response cache expires.
                type: str
                choices:
                    - enable
                    - disable
            rules:
                description:
                    - WAN optimization content delivery network rule entries.
                type: list
                suboptions:
                    content_id:
                        description:
                            - Content ID settings.
                        type: dict
                        suboptions:
                            end_direction:
                                description:
                                    - Search direction from end-str match.
                                type: str
                                choices:
                                    - forward
                                    - backward
                            end_skip:
                                description:
                                    - Number of characters in URL to skip after end-str has been matched.
                                type: int
                            end_str:
                                description:
                                    - String from which to end search.
                                type: str
                            range_str:
                                description:
                                    - Name of content ID within the start string and end string.
                                type: str
                            start_direction:
                                description:
                                    - Search direction from start-str match.
                                type: str
                                choices:
                                    - forward
                                    - backward
                            start_skip:
                                description:
                                    - Number of characters in URL to skip after start-str has been matched.
                                type: int
                            start_str:
                                description:
                                    - String from which to start search.
                                type: str
                            target:
                                description:
                                    - Option in HTTP header or URL parameter to match.
                                type: str
                                choices:
                                    - path
                                    - parameter
                                    - referrer
                                    - youtube-map
                                    - youtube-id
                                    - youku-id
                                    - hls-manifest
                                    - dash-manifest
                                    - hls-fragment
                                    - dash-fragment
                    match_entries:
                        description:
                            - List of entries to match.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Rule ID.
                                required: true
                                type: int
                            pattern:
                                description:
                                    - Pattern string for matching target (Referrer or URL pattern, eg. "a", "a*c", "*a*", "a*c*e", and "*").
                                type: list
                                suboptions:
                                    string:
                                        description:
                                            - Pattern strings.
                                        required: true
                                        type: str
                            target:
                                description:
                                    - Option in HTTP header or URL parameter to match.
                                type: str
                                choices:
                                    - path
                                    - parameter
                                    - referrer
                                    - youtube-map
                                    - youtube-id
                                    - youku-id
                    match_mode:
                        description:
                            - Match criteria for collecting content ID.
                        type: str
                        choices:
                            - all
                            - any
                    name:
                        description:
                            - WAN optimization content delivery network rule name.
                        required: true
                        type: str
                    skip_entries:
                        description:
                            - List of entries to skip.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Rule ID.
                                required: true
                                type: int
                            pattern:
                                description:
                                    - Pattern string for matching target (Referrer or URL pattern, eg. "a", "a*c", "*a*", "a*c*e", and "*").
                                type: list
                                suboptions:
                                    string:
                                        description:
                                            - Pattern strings.
                                        required: true
                                        type: str
                            target:
                                description:
                                    - Option in HTTP header or URL parameter to match.
                                type: str
                                choices:
                                    - path
                                    - parameter
                                    - referrer
                                    - youtube-map
                                    - youtube-id
                                    - youku-id
                    skip_rule_mode:
                        description:
                            - Skip mode when evaluating skip-rules.
                        type: str
                        choices:
                            - all
                            - any
            status:
                description:
                    - Enable/disable WAN optimization content delivery network rules.
                type: str
                choices:
                    - enable
                    - disable
            text_response_vcache:
                description:
                    - Enable/disable caching of text responses.
                type: str
                choices:
                    - enable
                    - disable
            updateserver:
                description:
                    - Enable/disable update server.
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
  - name: Configure WAN optimization content delivery network rules.
    fortios_wanopt_content_delivery_network_rule:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      wanopt_content_delivery_network_rule:
        category: "vcache"
        comment: "Comment about this CDN-rule."
        host_domain_name_suffix:
         -
            name: "default_name_6"
        name: "default_name_7"
        request_cache_control: "enable"
        response_cache_control: "enable"
        response_expires: "enable"
        rules:
         -
            content_id:
                end_direction: "forward"
                end_skip: "14"
                end_str: "<your_own_value>"
                range_str: "<your_own_value>"
                start_direction: "forward"
                start_skip: "18"
                start_str: "<your_own_value>"
                target: "path"
            match_entries:
             -
                id:  "22"
                pattern:
                 -
                    string: "<your_own_value>"
                target: "path"
            match_mode: "all"
            name: "default_name_27"
            skip_entries:
             -
                id:  "29"
                pattern:
                 -
                    string: "<your_own_value>"
                target: "path"
            skip_rule_mode: "all"
        status: "enable"
        text_response_vcache: "enable"
        updateserver: "enable"
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


def filter_wanopt_content_delivery_network_rule_data(json):
    option_list = ['category', 'comment', 'host_domain_name_suffix',
                   'name', 'request_cache_control', 'response_cache_control',
                   'response_expires', 'rules', 'status',
                   'text_response_vcache', 'updateserver']
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


def wanopt_content_delivery_network_rule(data, fos):
    vdom = data['vdom']
    state = data['state']
    wanopt_content_delivery_network_rule_data = data['wanopt_content_delivery_network_rule']
    filtered_data = underscore_to_hyphen(filter_wanopt_content_delivery_network_rule_data(wanopt_content_delivery_network_rule_data))

    if state == "present":
        return fos.set('wanopt',
                       'content-delivery-network-rule',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('wanopt',
                          'content-delivery-network-rule',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wanopt(data, fos):

    if data['wanopt_content_delivery_network_rule']:
        resp = wanopt_content_delivery_network_rule(data, fos)

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
        "wanopt_content_delivery_network_rule": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "category": {"required": False, "type": "str",
                             "choices": ["vcache", "youtube"]},
                "comment": {"required": False, "type": "str"},
                "host_domain_name_suffix": {"required": False, "type": "list",
                                            "options": {
                                                "name": {"required": True, "type": "str"}
                                            }},
                "name": {"required": True, "type": "str"},
                "request_cache_control": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "response_cache_control": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "response_expires": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "rules": {"required": False, "type": "list",
                          "options": {
                              "content_id": {"required": False, "type": "dict",
                                             "options": {
                                                 "end_direction": {"required": False, "type": "str",
                                                                   "choices": ["forward", "backward"]},
                                                 "end_skip": {"required": False, "type": "int"},
                                                 "end_str": {"required": False, "type": "str"},
                                                 "range_str": {"required": False, "type": "str"},
                                                 "start_direction": {"required": False, "type": "str",
                                                                     "choices": ["forward", "backward"]},
                                                 "start_skip": {"required": False, "type": "int"},
                                                 "start_str": {"required": False, "type": "str"},
                                                 "target": {"required": False, "type": "str",
                                                            "choices": ["path", "parameter", "referrer",
                                                                        "youtube-map", "youtube-id", "youku-id",
                                                                        "hls-manifest", "dash-manifest", "hls-fragment",
                                                                        "dash-fragment"]}
                                             }},
                              "match_entries": {"required": False, "type": "list",
                                                "options": {
                                                    "id": {"required": True, "type": "int"},
                                                    "pattern": {"required": False, "type": "list",
                                                                "options": {
                                                                    "string": {"required": True, "type": "str"}
                                                                }},
                                                    "target": {"required": False, "type": "str",
                                                               "choices": ["path", "parameter", "referrer",
                                                                           "youtube-map", "youtube-id", "youku-id"]}
                                                }},
                              "match_mode": {"required": False, "type": "str",
                                             "choices": ["all", "any"]},
                              "name": {"required": True, "type": "str"},
                              "skip_entries": {"required": False, "type": "list",
                                               "options": {
                                                   "id": {"required": True, "type": "int"},
                                                   "pattern": {"required": False, "type": "list",
                                                               "options": {
                                                                   "string": {"required": True, "type": "str"}
                                                               }},
                                                   "target": {"required": False, "type": "str",
                                                              "choices": ["path", "parameter", "referrer",
                                                                          "youtube-map", "youtube-id", "youku-id"]}
                                               }},
                              "skip_rule_mode": {"required": False, "type": "str",
                                                 "choices": ["all", "any"]}
                          }},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "text_response_vcache": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "updateserver": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_wanopt(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_wanopt(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
