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
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify web_proxy feature and global category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
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
        default: true
    web_proxy_global:
        description:
            - Configure Web proxy global settings.
        default: null
        suboptions:
            fast-policy-match:
                description:
                    - Enable/disable fast matching algorithm for explicit and transparent proxy policy.
                choices:
                    - enable
                    - disable
            forward-proxy-auth:
                description:
                    - Enable/disable forwarding proxy authentication headers.
                choices:
                    - enable
                    - disable
            forward-server-affinity-timeout:
                description:
                    - Period of time before the source IP's traffic is no longer assigned to the forwarding server (6 - 60 min, default = 30).
            learn-client-ip:
                description:
                    - Enable/disable learning the client's IP address from headers.
                choices:
                    - enable
                    - disable
            learn-client-ip-from-header:
                description:
                    - Learn client IP address from the specified headers.
                choices:
                    - true-client-ip
                    - x-real-ip
                    - x-forwarded-for
            learn-client-ip-srcaddr:
                description:
                    - Source address name (srcaddr or srcaddr6 must be set).
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            learn-client-ip-srcaddr6:
                description:
                    - IPv6 Source address name (srcaddr or srcaddr6 must be set).
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            max-message-length:
                description:
                    - Maximum length of HTTP message, not including body (16 - 256 Kbytes, default = 32).
            max-request-length:
                description:
                    - Maximum length of HTTP request line (2 - 64 Kbytes, default = 4).
            max-waf-body-cache-length:
                description:
                    - Maximum length of HTTP messages processed by Web Application Firewall (WAF) (10 - 1024 Kbytes, default = 32).
            proxy-fqdn:
                description:
                    - Fully Qualified Domain Name (FQDN) that clients connect to (default = default.fqdn) to connect to the explicit web proxy.
            strict-web-check:
                description:
                    - Enable/disable strict web checking to block web sites that send incorrect headers that don't conform to HTTP 1.1.
                choices:
                    - enable
                    - disable
            tunnel-non-http:
                description:
                    - Enable/disable allowing non-HTTP traffic. Allowed non-HTTP traffic is tunneled.
                choices:
                    - enable
                    - disable
            unknown-http-version:
                description:
                    - "Action to take when an unknown version of HTTP is encountered: reject, allow (tunnel), or proceed with best-effort."
                choices:
                    - reject
                    - tunnel
                    - best-effort
            webproxy-profile:
                description:
                    - Name of the web proxy profile to apply when explicit proxy traffic is allowed by default and traffic is accepted that does not match an
                       explicit proxy policy. Source web-proxy.profile.name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure Web proxy global settings.
    fortios_web_proxy_global:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      web_proxy_global:
        fast-policy-match: "enable"
        forward-proxy-auth: "enable"
        forward-server-affinity-timeout: "5"
        learn-client-ip: "enable"
        learn-client-ip-from-header: "true-client-ip"
        learn-client-ip-srcaddr:
         -
            name: "default_name_9 (source firewall.address.name firewall.addrgrp.name)"
        learn-client-ip-srcaddr6:
         -
            name: "default_name_11 (source firewall.address6.name firewall.addrgrp6.name)"
        max-message-length: "12"
        max-request-length: "13"
        max-waf-body-cache-length: "14"
        proxy-fqdn: "<your_own_value>"
        strict-web-check: "enable"
        tunnel-non-http: "enable"
        unknown-http-version: "reject"
        webproxy-profile: "<your_own_value> (source web-proxy.profile.name)"
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


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_web_proxy_global_data(json):
    option_list = ['fast-policy-match', 'forward-proxy-auth', 'forward-server-affinity-timeout',
                   'learn-client-ip', 'learn-client-ip-from-header', 'learn-client-ip-srcaddr',
                   'learn-client-ip-srcaddr6', 'max-message-length', 'max-request-length',
                   'max-waf-body-cache-length', 'proxy-fqdn', 'strict-web-check',
                   'tunnel-non-http', 'unknown-http-version', 'webproxy-profile']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def web_proxy_global(data, fos):
    vdom = data['vdom']
    web_proxy_global_data = data['web_proxy_global']
    filtered_data = filter_web_proxy_global_data(web_proxy_global_data)

    return fos.set('web-proxy',
                   'global',
                   data=filtered_data,
                   vdom=vdom)


def fortios_web_proxy(data, fos):
    login(data, fos)

    if data['web_proxy_global']:
        resp = web_proxy_global(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "web_proxy_global": {
            "required": False, "type": "dict",
            "options": {
                "fast-policy-match": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "forward-proxy-auth": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "forward-server-affinity-timeout": {"required": False, "type": "int"},
                "learn-client-ip": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "learn-client-ip-from-header": {"required": False, "type": "str",
                                                "choices": ["true-client-ip", "x-real-ip", "x-forwarded-for"]},
                "learn-client-ip-srcaddr": {"required": False, "type": "list",
                                            "options": {
                                                "name": {"required": True, "type": "str"}
                                            }},
                "learn-client-ip-srcaddr6": {"required": False, "type": "list",
                                             "options": {
                                                 "name": {"required": True, "type": "str"}
                                             }},
                "max-message-length": {"required": False, "type": "int"},
                "max-request-length": {"required": False, "type": "int"},
                "max-waf-body-cache-length": {"required": False, "type": "int"},
                "proxy-fqdn": {"required": False, "type": "str"},
                "strict-web-check": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "tunnel-non-http": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "unknown-http-version": {"required": False, "type": "str",
                                         "choices": ["reject", "tunnel", "best-effort"]},
                "webproxy-profile": {"required": False, "type": "str"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_web_proxy(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
