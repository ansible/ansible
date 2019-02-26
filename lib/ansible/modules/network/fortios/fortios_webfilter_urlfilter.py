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
module: fortios_webfilter_urlfilter
short_description: Configure URL filter lists in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure webfilter feature and urlfilter category.
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
    webfilter_urlfilter:
        description:
            - Configure URL filter lists.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            comment:
                description:
                    - Optional comments.
            entries:
                description:
                    - URL filter entries.
                suboptions:
                    action:
                        description:
                            - Action to take for URL filter matches.
                        choices:
                            - exempt
                            - block
                            - allow
                            - monitor
                    dns-address-family:
                        description:
                            - Resolve IPv4 address, IPv6 address, or both from DNS server.
                        choices:
                            - ipv4
                            - ipv6
                            - both
                    exempt:
                        description:
                            - If action is set to exempt, select the security profile operations that exempt URLs skip. Separate multiple options with a space.
                        choices:
                            - av
                            - web-content
                            - activex-java-cookie
                            - dlp
                            - fortiguard
                            - range-block
                            - pass
                            - all
                    id:
                        description:
                            - Id.
                        required: true
                    referrer-host:
                        description:
                            - Referrer host name.
                    status:
                        description:
                            - Enable/disable this URL filter.
                        choices:
                            - enable
                            - disable
                    type:
                        description:
                            - Filter type (simple, regex, or wildcard).
                        choices:
                            - simple
                            - regex
                            - wildcard
                    url:
                        description:
                            - URL to be filtered.
                    web-proxy-profile:
                        description:
                            - Web proxy profile. Source web-proxy.profile.name.
            id:
                description:
                    - ID.
                required: true
            ip-addr-block:
                description:
                    - Enable/disable blocking URLs when the hostname appears as an IP address.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name of URL filter list.
            one-arm-ips-urlfilter:
                description:
                    - Enable/disable DNS resolver for one-arm IPS URL filter operation.
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
  - name: Configure URL filter lists.
    fortios_webfilter_urlfilter:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      webfilter_urlfilter:
        state: "present"
        comment: "Optional comments."
        entries:
         -
            action: "exempt"
            dns-address-family: "ipv4"
            exempt: "av"
            id:  "8"
            referrer-host: "myhostname"
            status: "enable"
            type: "simple"
            url: "myurl.com"
            web-proxy-profile: "<your_own_value> (source web-proxy.profile.name)"
        id:  "14"
        ip-addr-block: "enable"
        name: "default_name_16"
        one-arm-ips-urlfilter: "enable"
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


def filter_webfilter_urlfilter_data(json):
    option_list = ['comment', 'entries', 'id',
                   'ip-addr-block', 'name', 'one-arm-ips-urlfilter']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def webfilter_urlfilter(data, fos):
    vdom = data['vdom']
    webfilter_urlfilter_data = data['webfilter_urlfilter']
    filtered_data = filter_webfilter_urlfilter_data(webfilter_urlfilter_data)
    if webfilter_urlfilter_data['state'] == "present":
        return fos.set('webfilter',
                       'urlfilter',
                       data=filtered_data,
                       vdom=vdom)

    elif webfilter_urlfilter_data['state'] == "absent":
        return fos.delete('webfilter',
                          'urlfilter',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def fortios_webfilter(data, fos):
    login(data)

    methodlist = ['webfilter_urlfilter']
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
        "webfilter_urlfilter": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "entries": {"required": False, "type": "list",
                            "options": {
                                "action": {"required": False, "type": "str",
                                           "choices": ["exempt", "block", "allow",
                                                       "monitor"]},
                                "dns-address-family": {"required": False, "type": "str",
                                                       "choices": ["ipv4", "ipv6", "both"]},
                                "exempt": {"required": False, "type": "str",
                                           "choices": ["av", "web-content", "activex-java-cookie",
                                                       "dlp", "fortiguard", "range-block",
                                                       "pass", "all"]},
                                "id": {"required": True, "type": "int"},
                                "referrer-host": {"required": False, "type": "str"},
                                "status": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                                "type": {"required": False, "type": "str",
                                         "choices": ["simple", "regex", "wildcard"]},
                                "url": {"required": False, "type": "str"},
                                "web-proxy-profile": {"required": False, "type": "str"}
                            }},
                "id": {"required": True, "type": "int"},
                "ip-addr-block": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "name": {"required": False, "type": "str"},
                "one-arm-ips-urlfilter": {"required": False, "type": "str",
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

    is_error, has_changed, result = fortios_webfilter(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
