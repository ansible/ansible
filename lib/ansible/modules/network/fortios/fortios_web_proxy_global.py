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
module: fortios_web_proxy_global
short_description: Configure Web proxy global settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify web_proxy feature and global category.
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
    web_proxy_global:
        description:
            - Configure Web proxy global settings.
        default: null
        type: dict
        suboptions:
            fast_policy_match:
                description:
                    - Enable/disable fast matching algorithm for explicit and transparent proxy policy.
                type: str
                choices:
                    - enable
                    - disable
            forward_proxy_auth:
                description:
                    - Enable/disable forwarding proxy authentication headers.
                type: str
                choices:
                    - enable
                    - disable
            forward_server_affinity_timeout:
                description:
                    - Period of time before the source IP's traffic is no longer assigned to the forwarding server (6 - 60 min).
                type: int
            learn_client_ip:
                description:
                    - Enable/disable learning the client's IP address from headers.
                type: str
                choices:
                    - enable
                    - disable
            learn_client_ip_from_header:
                description:
                    - Learn client IP address from the specified headers.
                type: str
                choices:
                    - true-client-ip
                    - x-real-ip
                    - x-forwarded-for
            learn_client_ip_srcaddr:
                description:
                    - Source address name (srcaddr or srcaddr6 must be set).
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
                        type: str
            learn_client_ip_srcaddr6:
                description:
                    - IPv6 Source address name (srcaddr or srcaddr6 must be set).
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
                        type: str
            max_message_length:
                description:
                    - Maximum length of HTTP message, not including body (16 - 256 Kbytes).
                type: int
            max_request_length:
                description:
                    - Maximum length of HTTP request line (2 - 64 Kbytes).
                type: int
            max_waf_body_cache_length:
                description:
                    - Maximum length of HTTP messages processed by Web Application Firewall (WAF) (10 - 1024 Kbytes).
                type: int
            proxy_fqdn:
                description:
                    - Fully Qualified Domain Name (FQDN) that clients connect to  to connect to the explicit web proxy.
                type: str
            strict_web_check:
                description:
                    - Enable/disable strict web checking to block web sites that send incorrect headers that don't conform to HTTP 1.1.
                type: str
                choices:
                    - enable
                    - disable
            tunnel_non_http:
                description:
                    - Enable/disable allowing non-HTTP traffic. Allowed non-HTTP traffic is tunneled.
                type: str
                choices:
                    - enable
                    - disable
            unknown_http_version:
                description:
                    - "Action to take when an unknown version of HTTP is encountered: reject, allow (tunnel), or proceed with best-effort."
                type: str
                choices:
                    - reject
                    - tunnel
                    - best-effort
            webproxy_profile:
                description:
                    - Name of the web proxy profile to apply when explicit proxy traffic is allowed by default and traffic is accepted that does not match an
                       explicit proxy policy. Source web-proxy.profile.name.
                type: str
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
  - name: Configure Web proxy global settings.
    fortios_web_proxy_global:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      web_proxy_global:
        fast_policy_match: "enable"
        forward_proxy_auth: "enable"
        forward_server_affinity_timeout: "5"
        learn_client_ip: "enable"
        learn_client_ip_from_header: "true-client-ip"
        learn_client_ip_srcaddr:
         -
            name: "default_name_9 (source firewall.address.name firewall.addrgrp.name)"
        learn_client_ip_srcaddr6:
         -
            name: "default_name_11 (source firewall.address6.name firewall.addrgrp6.name)"
        max_message_length: "12"
        max_request_length: "13"
        max_waf_body_cache_length: "14"
        proxy_fqdn: "<your_own_value>"
        strict_web_check: "enable"
        tunnel_non_http: "enable"
        unknown_http_version: "reject"
        webproxy_profile: "<your_own_value> (source web-proxy.profile.name)"
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


def filter_web_proxy_global_data(json):
    option_list = ['fast_policy_match', 'forward_proxy_auth', 'forward_server_affinity_timeout',
                   'learn_client_ip', 'learn_client_ip_from_header', 'learn_client_ip_srcaddr',
                   'learn_client_ip_srcaddr6', 'max_message_length', 'max_request_length',
                   'max_waf_body_cache_length', 'proxy_fqdn', 'strict_web_check',
                   'tunnel_non_http', 'unknown_http_version', 'webproxy_profile']
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


def web_proxy_global(data, fos):
    vdom = data['vdom']
    web_proxy_global_data = data['web_proxy_global']
    filtered_data = underscore_to_hyphen(filter_web_proxy_global_data(web_proxy_global_data))

    return fos.set('web-proxy',
                   'global',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_web_proxy(data, fos):

    if data['web_proxy_global']:
        resp = web_proxy_global(data, fos)

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
        "web_proxy_global": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "fast_policy_match": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "forward_proxy_auth": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "forward_server_affinity_timeout": {"required": False, "type": "int"},
                "learn_client_ip": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "learn_client_ip_from_header": {"required": False, "type": "str",
                                                "choices": ["true-client-ip", "x-real-ip", "x-forwarded-for"]},
                "learn_client_ip_srcaddr": {"required": False, "type": "list",
                                            "options": {
                                                "name": {"required": True, "type": "str"}
                                            }},
                "learn_client_ip_srcaddr6": {"required": False, "type": "list",
                                             "options": {
                                                 "name": {"required": True, "type": "str"}
                                             }},
                "max_message_length": {"required": False, "type": "int"},
                "max_request_length": {"required": False, "type": "int"},
                "max_waf_body_cache_length": {"required": False, "type": "int"},
                "proxy_fqdn": {"required": False, "type": "str"},
                "strict_web_check": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "tunnel_non_http": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "unknown_http_version": {"required": False, "type": "str",
                                         "choices": ["reject", "tunnel", "best-effort"]},
                "webproxy_profile": {"required": False, "type": "str"}

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
