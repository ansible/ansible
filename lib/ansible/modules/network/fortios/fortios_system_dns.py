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
module: fortios_system_dns
short_description: Configure DNS in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and dns category.
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
    system_dns:
        description:
            - Configure DNS.
        default: null
        type: dict
        suboptions:
            cache_notfound_responses:
                description:
                    - Enable/disable response from the DNS server when a record is not in cache.
                type: str
                choices:
                    - disable
                    - enable
            dns_cache_limit:
                description:
                    - Maximum number of records in the DNS cache.
                type: int
            dns_cache_ttl:
                description:
                    - Duration in seconds that the DNS cache retains information.
                type: int
            domain:
                description:
                    - Search suffix list for hostname lookup.
                type: list
                suboptions:
                    domain:
                        description:
                            - DNS search domain list separated by space (maximum 8 domains)
                        required: true
                        type: str
            ip6_primary:
                description:
                    - Primary DNS server IPv6 address.
                type: str
            ip6_secondary:
                description:
                    - Secondary DNS server IPv6 address.
                type: str
            primary:
                description:
                    - Primary DNS server IP address.
                type: str
            retry:
                description:
                    - Number of times to retry (0 - 5).
                type: int
            secondary:
                description:
                    - Secondary DNS server IP address.
                type: str
            source_ip:
                description:
                    - IP address used by the DNS server as its source IP.
                type: str
            timeout:
                description:
                    - DNS query timeout interval in seconds (1 - 10).
                type: int
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
  - name: Configure DNS.
    fortios_system_dns:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_dns:
        cache_notfound_responses: "disable"
        dns_cache_limit: "4"
        dns_cache_ttl: "5"
        domain:
         -
            domain: "<your_own_value>"
        ip6_primary: "<your_own_value>"
        ip6_secondary: "<your_own_value>"
        primary: "<your_own_value>"
        retry: "11"
        secondary: "<your_own_value>"
        source_ip: "84.230.14.43"
        timeout: "14"
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


def filter_system_dns_data(json):
    option_list = ['cache_notfound_responses', 'dns_cache_limit', 'dns_cache_ttl',
                   'domain', 'ip6_primary', 'ip6_secondary',
                   'primary', 'retry', 'secondary',
                   'source_ip', 'timeout']
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


def system_dns(data, fos):
    vdom = data['vdom']
    system_dns_data = data['system_dns']
    filtered_data = underscore_to_hyphen(filter_system_dns_data(system_dns_data))

    return fos.set('system',
                   'dns',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_dns']:
        resp = system_dns(data, fos)

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
        "system_dns": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "cache_notfound_responses": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                "dns_cache_limit": {"required": False, "type": "int"},
                "dns_cache_ttl": {"required": False, "type": "int"},
                "domain": {"required": False, "type": "list",
                           "options": {
                               "domain": {"required": True, "type": "str"}
                           }},
                "ip6_primary": {"required": False, "type": "str"},
                "ip6_secondary": {"required": False, "type": "str"},
                "primary": {"required": False, "type": "str"},
                "retry": {"required": False, "type": "int"},
                "secondary": {"required": False, "type": "str"},
                "source_ip": {"required": False, "type": "str"},
                "timeout": {"required": False, "type": "int"}

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

            is_error, has_changed, result = fortios_system(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
