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
module: fortios_webfilter_urlfilter
short_description: Configure URL filter lists in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify webfilter feature and urlfilter category.
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
    webfilter_urlfilter:
        description:
            - Configure URL filter lists.
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
            comment:
                description:
                    - Optional comments.
                type: str
            entries:
                description:
                    - URL filter entries.
                type: list
                suboptions:
                    action:
                        description:
                            - Action to take for URL filter matches.
                        type: str
                        choices:
                            - exempt
                            - block
                            - allow
                            - monitor
                    dns_address_family:
                        description:
                            - Resolve IPv4 address, IPv6 address, or both from DNS server.
                        type: str
                        choices:
                            - ipv4
                            - ipv6
                            - both
                    exempt:
                        description:
                            - If action is set to exempt, select the security profile operations that exempt URLs skip. Separate multiple options with a space.
                        type: str
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
                        type: int
                    referrer_host:
                        description:
                            - Referrer host name.
                        type: str
                    status:
                        description:
                            - Enable/disable this URL filter.
                        type: str
                        choices:
                            - enable
                            - disable
                    type:
                        description:
                            - Filter type (simple, regex, or wildcard).
                        type: str
                        choices:
                            - simple
                            - regex
                            - wildcard
                    url:
                        description:
                            - URL to be filtered.
                        type: str
                    web_proxy_profile:
                        description:
                            - Web proxy profile. Source web-proxy.profile.name.
                        type: str
            id:
                description:
                    - ID.
                required: true
                type: int
            ip_addr_block:
                description:
                    - Enable/disable blocking URLs when the hostname appears as an IP address.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name of URL filter list.
                type: str
            one_arm_ips_urlfilter:
                description:
                    - Enable/disable DNS resolver for one-arm IPS URL filter operation.
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
  - name: Configure URL filter lists.
    fortios_webfilter_urlfilter:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      webfilter_urlfilter:
        comment: "Optional comments."
        entries:
         -
            action: "exempt"
            dns_address_family: "ipv4"
            exempt: "av"
            id:  "8"
            referrer_host: "myhostname"
            status: "enable"
            type: "simple"
            url: "myurl.com"
            web_proxy_profile: "<your_own_value> (source web-proxy.profile.name)"
        id:  "14"
        ip_addr_block: "enable"
        name: "default_name_16"
        one_arm_ips_urlfilter: "enable"
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


def filter_webfilter_urlfilter_data(json):
    option_list = ['comment', 'entries', 'id',
                   'ip_addr_block', 'name', 'one_arm_ips_urlfilter']
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


def webfilter_urlfilter(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['webfilter_urlfilter'] and data['webfilter_urlfilter']:
        state = data['webfilter_urlfilter']['state']
    else:
        state = True
    webfilter_urlfilter_data = data['webfilter_urlfilter']
    filtered_data = underscore_to_hyphen(filter_webfilter_urlfilter_data(webfilter_urlfilter_data))

    if state == "present":
        return fos.set('webfilter',
                       'urlfilter',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('webfilter',
                          'urlfilter',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_webfilter(data, fos):

    if data['webfilter_urlfilter']:
        resp = webfilter_urlfilter(data, fos)

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
        "webfilter_urlfilter": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "entries": {"required": False, "type": "list",
                            "options": {
                                "action": {"required": False, "type": "str",
                                           "choices": ["exempt", "block", "allow",
                                                       "monitor"]},
                                "dns_address_family": {"required": False, "type": "str",
                                                       "choices": ["ipv4", "ipv6", "both"]},
                                "exempt": {"required": False, "type": "str",
                                           "choices": ["av", "web-content", "activex-java-cookie",
                                                       "dlp", "fortiguard", "range-block",
                                                       "pass", "all"]},
                                "id": {"required": True, "type": "int"},
                                "referrer_host": {"required": False, "type": "str"},
                                "status": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                                "type": {"required": False, "type": "str",
                                         "choices": ["simple", "regex", "wildcard"]},
                                "url": {"required": False, "type": "str"},
                                "web_proxy_profile": {"required": False, "type": "str"}
                            }},
                "id": {"required": True, "type": "int"},
                "ip_addr_block": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "name": {"required": False, "type": "str"},
                "one_arm_ips_urlfilter": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_webfilter(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_webfilter(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
