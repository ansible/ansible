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
module: fortios_dnsfilter_profile
short_description: Configure DNS domain filter profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify dnsfilter feature and profile category.
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
    dnsfilter_profile:
        description:
            - Configure DNS domain filter profiles.
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
            block_action:
                description:
                    - Action to take for blocked domains.
                type: str
                choices:
                    - block
                    - redirect
            block_botnet:
                description:
                    - Enable/disable blocking botnet C&C DNS lookups.
                type: str
                choices:
                    - disable
                    - enable
            comment:
                description:
                    - Comment.
                type: str
            domain_filter:
                description:
                    - Domain filter settings.
                type: dict
                suboptions:
                    domain_filter_table:
                        description:
                            - DNS domain filter table ID. Source dnsfilter.domain-filter.id.
                        type: int
            external_ip_blocklist:
                description:
                    - One or more external IP block lists.
                type: list
                suboptions:
                    name:
                        description:
                            - External domain block list name. Source system.external-resource.name.
                        required: true
                        type: str
            ftgd_dns:
                description:
                    - FortiGuard DNS Filter settings.
                type: dict
                suboptions:
                    filters:
                        description:
                            - FortiGuard DNS domain filters.
                        type: list
                        suboptions:
                            action:
                                description:
                                    - Action to take for DNS requests matching the category.
                                type: str
                                choices:
                                    - block
                                    - monitor
                            category:
                                description:
                                    - Category number.
                                type: int
                            id:
                                description:
                                    - ID number.
                                required: true
                                type: int
                            log:
                                description:
                                    - Enable/disable DNS filter logging for this DNS profile.
                                type: str
                                choices:
                                    - enable
                                    - disable
                    options:
                        description:
                            - FortiGuard DNS filter options.
                        type: str
                        choices:
                            - error-allow
                            - ftgd-disable
            log_all_domain:
                description:
                    - Enable/disable logging of all domains visited (detailed DNS logging).
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Profile name.
                required: true
                type: str
            redirect_portal:
                description:
                    - IP address of the SDNS redirect portal.
                type: str
            safe_search:
                description:
                    - Enable/disable Google, Bing, and YouTube safe search.
                type: str
                choices:
                    - disable
                    - enable
            sdns_domain_log:
                description:
                    - Enable/disable domain filtering and botnet domain logging.
                type: str
                choices:
                    - enable
                    - disable
            sdns_ftgd_err_log:
                description:
                    - Enable/disable FortiGuard SDNS rating error logging.
                type: str
                choices:
                    - enable
                    - disable
            youtube_restrict:
                description:
                    - Set safe search for YouTube restriction level.
                type: str
                choices:
                    - strict
                    - moderate
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
  - name: Configure DNS domain filter profiles.
    fortios_dnsfilter_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      dnsfilter_profile:
        block_action: "block"
        block_botnet: "disable"
        comment: "Comment."
        domain_filter:
            domain_filter_table: "7 (source dnsfilter.domain-filter.id)"
        external_ip_blocklist:
         -
            name: "default_name_9 (source system.external-resource.name)"
        ftgd_dns:
            filters:
             -
                action: "block"
                category: "13"
                id:  "14"
                log: "enable"
            options: "error-allow"
        log_all_domain: "enable"
        name: "default_name_18"
        redirect_portal: "<your_own_value>"
        safe_search: "disable"
        sdns_domain_log: "enable"
        sdns_ftgd_err_log: "enable"
        youtube_restrict: "strict"
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


def filter_dnsfilter_profile_data(json):
    option_list = ['block_action', 'block_botnet', 'comment',
                   'domain_filter', 'external_ip_blocklist', 'ftgd_dns',
                   'log_all_domain', 'name', 'redirect_portal',
                   'safe_search', 'sdns_domain_log', 'sdns_ftgd_err_log',
                   'youtube_restrict']
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


def dnsfilter_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['dnsfilter_profile'] and data['dnsfilter_profile']:
        state = data['dnsfilter_profile']['state']
    else:
        state = True
    dnsfilter_profile_data = data['dnsfilter_profile']
    filtered_data = underscore_to_hyphen(filter_dnsfilter_profile_data(dnsfilter_profile_data))

    if state == "present":
        return fos.set('dnsfilter',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('dnsfilter',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_dnsfilter(data, fos):

    if data['dnsfilter_profile']:
        resp = dnsfilter_profile(data, fos)

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
        "dnsfilter_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "block_action": {"required": False, "type": "str",
                                 "choices": ["block", "redirect"]},
                "block_botnet": {"required": False, "type": "str",
                                 "choices": ["disable", "enable"]},
                "comment": {"required": False, "type": "str"},
                "domain_filter": {"required": False, "type": "dict",
                                  "options": {
                                      "domain_filter_table": {"required": False, "type": "int"}
                                  }},
                "external_ip_blocklist": {"required": False, "type": "list",
                                          "options": {
                                              "name": {"required": True, "type": "str"}
                                          }},
                "ftgd_dns": {"required": False, "type": "dict",
                             "options": {
                                 "filters": {"required": False, "type": "list",
                                             "options": {
                                                 "action": {"required": False, "type": "str",
                                                            "choices": ["block", "monitor"]},
                                                 "category": {"required": False, "type": "int"},
                                                 "id": {"required": True, "type": "int"},
                                                 "log": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]}
                                             }},
                                 "options": {"required": False, "type": "str",
                                             "choices": ["error-allow", "ftgd-disable"]}
                             }},
                "log_all_domain": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "redirect_portal": {"required": False, "type": "str"},
                "safe_search": {"required": False, "type": "str",
                                "choices": ["disable", "enable"]},
                "sdns_domain_log": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "sdns_ftgd_err_log": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "youtube_restrict": {"required": False, "type": "str",
                                     "choices": ["strict", "moderate"]}

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

            is_error, has_changed, result = fortios_dnsfilter(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_dnsfilter(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
