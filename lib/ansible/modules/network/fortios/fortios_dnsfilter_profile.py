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
module: fortios_dnsfilter_profile
short_description: Configure DNS domain filter profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure dnsfilter feature and profile category.
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
    dnsfilter_profile:
        description:
            - Configure DNS domain filter profiles.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            block-action:
                description:
                    - Action to take for blocked domains.
                choices:
                    - block
                    - redirect
            block-botnet:
                description:
                    - Enable/disable blocking botnet C&C DNS lookups.
                choices:
                    - disable
                    - enable
            comment:
                description:
                    - Comment.
            domain-filter:
                description:
                    - Domain filter settings.
                suboptions:
                    domain-filter-table:
                        description:
                            - DNS domain filter table ID. Source dnsfilter.domain-filter.id.
            external-ip-blocklist:
                description:
                    - One or more external IP block lists.
                suboptions:
                    name:
                        description:
                            - External domain block list name. Source system.external-resource.name.
                        required: true
            ftgd-dns:
                description:
                    - FortiGuard DNS Filter settings.
                suboptions:
                    filters:
                        description:
                            - FortiGuard DNS domain filters.
                        suboptions:
                            action:
                                description:
                                    - Action to take for DNS requests matching the category.
                                choices:
                                    - block
                                    - monitor
                            category:
                                description:
                                    - Category number.
                            id:
                                description:
                                    - ID number.
                                required: true
                            log:
                                description:
                                    - Enable/disable DNS filter logging for this DNS profile.
                                choices:
                                    - enable
                                    - disable
                    options:
                        description:
                            - FortiGuard DNS filter options.
                        choices:
                            - error-allow
                            - ftgd-disable
            log-all-domain:
                description:
                    - Enable/disable logging of all domains visited (detailed DNS logging).
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Profile name.
                required: true
            redirect-portal:
                description:
                    - IP address of the SDNS redirect portal.
            safe-search:
                description:
                    - Enable/disable Google, Bing, and YouTube safe search.
                choices:
                    - disable
                    - enable
            sdns-domain-log:
                description:
                    - Enable/disable domain filtering and botnet domain logging.
                choices:
                    - enable
                    - disable
            sdns-ftgd-err-log:
                description:
                    - Enable/disable FortiGuard SDNS rating error logging.
                choices:
                    - enable
                    - disable
            youtube-restrict:
                description:
                    - Set safe search for YouTube restriction level.
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
  tasks:
  - name: Configure DNS domain filter profiles.
    fortios_dnsfilter_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      dnsfilter_profile:
        state: "present"
        block-action: "block"
        block-botnet: "disable"
        comment: "Comment."
        domain-filter:
            domain-filter-table: "7 (source dnsfilter.domain-filter.id)"
        external-ip-blocklist:
         -
            name: "default_name_9 (source system.external-resource.name)"
        ftgd-dns:
            filters:
             -
                action: "block"
                category: "13"
                id:  "14"
                log: "enable"
            options: "error-allow"
        log-all-domain: "enable"
        name: "default_name_18"
        redirect-portal: "<your_own_value>"
        safe-search: "disable"
        sdns-domain-log: "enable"
        sdns-ftgd-err-log: "enable"
        youtube-restrict: "strict"
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


def filter_dnsfilter_profile_data(json):
    option_list = ['block-action', 'block-botnet', 'comment',
                   'domain-filter', 'external-ip-blocklist', 'ftgd-dns',
                   'log-all-domain', 'name', 'redirect-portal',
                   'safe-search', 'sdns-domain-log', 'sdns-ftgd-err-log',
                   'youtube-restrict']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def dnsfilter_profile(data, fos):
    vdom = data['vdom']
    dnsfilter_profile_data = data['dnsfilter_profile']
    filtered_data = filter_dnsfilter_profile_data(dnsfilter_profile_data)
    if dnsfilter_profile_data['state'] == "present":
        return fos.set('dnsfilter',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif dnsfilter_profile_data['state'] == "absent":
        return fos.delete('dnsfilter',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_dnsfilter(data, fos):
    login(data)

    methodlist = ['dnsfilter_profile']
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
        "dnsfilter_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "block-action": {"required": False, "type": "str",
                                 "choices": ["block", "redirect"]},
                "block-botnet": {"required": False, "type": "str",
                                 "choices": ["disable", "enable"]},
                "comment": {"required": False, "type": "str"},
                "domain-filter": {"required": False, "type": "dict",
                                  "options": {
                                      "domain-filter-table": {"required": False, "type": "int"}
                                  }},
                "external-ip-blocklist": {"required": False, "type": "list",
                                          "options": {
                                              "name": {"required": True, "type": "str"}
                                          }},
                "ftgd-dns": {"required": False, "type": "dict",
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
                "log-all-domain": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "redirect-portal": {"required": False, "type": "str"},
                "safe-search": {"required": False, "type": "str",
                                "choices": ["disable", "enable"]},
                "sdns-domain-log": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "sdns-ftgd-err-log": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "youtube-restrict": {"required": False, "type": "str",
                                     "choices": ["strict", "moderate"]}

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

    is_error, has_changed, result = fortios_dnsfilter(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
