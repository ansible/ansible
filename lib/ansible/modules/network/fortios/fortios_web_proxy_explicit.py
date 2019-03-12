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
module: fortios_web_proxy_explicit
short_description: Configure explicit Web proxy settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify web_proxy feature and explicit category.
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
    web_proxy_explicit:
        description:
            - Configure explicit Web proxy settings.
        default: null
        suboptions:
            ftp-incoming-port:
                description:
                    - Accept incoming FTP-over-HTTP requests on one or more ports (0 - 65535, default = 0; use the same as HTTP).
            ftp-over-http:
                description:
                    - Enable to proxy FTP-over-HTTP sessions sent from a web browser.
                choices:
                    - enable
                    - disable
            http-incoming-port:
                description:
                    - Accept incoming HTTP requests on one or more ports (0 - 65535, default = 8080).
            https-incoming-port:
                description:
                    - Accept incoming HTTPS requests on one or more ports (0 - 65535, default = 0, use the same as HTTP).
            https-replacement-message:
                description:
                    - Enable/disable sending the client a replacement message for HTTPS requests.
                choices:
                    - enable
                    - disable
            incoming-ip:
                description:
                    - Restrict the explicit HTTP proxy to only accept sessions from this IP address. An interface must have this IP address.
            incoming-ip6:
                description:
                    - Restrict the explicit web proxy to only accept sessions from this IPv6 address. An interface must have this IPv6 address.
            ipv6-status:
                description:
                    - Enable/disable allowing an IPv6 web proxy destination in policies and all IPv6 related entries in this command.
                choices:
                    - enable
                    - disable
            message-upon-server-error:
                description:
                    - Enable/disable displaying a replacement message when a server error is detected.
                choices:
                    - enable
                    - disable
            outgoing-ip:
                description:
                    - Outgoing HTTP requests will have this IP address as their source address. An interface must have this IP address.
            outgoing-ip6:
                description:
                    - Outgoing HTTP requests will leave this IPv6. Multiple interfaces can be specified. Interfaces must have these IPv6 addresses.
            pac-file-data:
                description:
                    - PAC file contents enclosed in quotes (maximum of 256K bytes).
            pac-file-name:
                description:
                    - Pac file name.
            pac-file-server-port:
                description:
                    - Port number that PAC traffic from client web browsers uses to connect to the explicit web proxy (0 - 65535, default = 0; use the same as
                       HTTP).
            pac-file-server-status:
                description:
                    - Enable/disable Proxy Auto-Configuration (PAC) for users of this explicit proxy profile.
                choices:
                    - enable
                    - disable
            pac-file-url:
                description:
                    - PAC file access URL.
            pac-policy:
                description:
                    - PAC policies.
                suboptions:
                    comments:
                        description:
                            - Optional comments.
                    dstaddr:
                        description:
                            - Destination address objects.
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                    pac-file-data:
                        description:
                            - PAC file contents enclosed in quotes (maximum of 256K bytes).
                    pac-file-name:
                        description:
                            - Pac file name.
                    policyid:
                        description:
                            - Policy ID.
                        required: true
                    srcaddr:
                        description:
                            - Source address objects.
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name.
                                required: true
                    srcaddr6:
                        description:
                            - Source address6 objects.
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                                required: true
                    status:
                        description:
                            - Enable/disable policy.
                        choices:
                            - enable
                            - disable
            pref-dns-result:
                description:
                    - Prefer resolving addresses using the configured IPv4 or IPv6 DNS server (default = ipv4).
                choices:
                    - ipv4
                    - ipv6
            realm:
                description:
                    - Authentication realm used to identify the explicit web proxy (maximum of 63 characters).
            sec-default-action:
                description:
                    - Accept or deny explicit web proxy sessions when no web proxy firewall policy exists.
                choices:
                    - accept
                    - deny
            socks:
                description:
                    - Enable/disable the SOCKS proxy.
                choices:
                    - enable
                    - disable
            socks-incoming-port:
                description:
                    - Accept incoming SOCKS proxy requests on one or more ports (0 - 65535, default = 0; use the same as HTTP).
            ssl-algorithm:
                description:
                    - "Relative strength of encryption algorithms accepted in HTTPS deep scan: high, medium, or low."
                choices:
                    - low
            status:
                description:
                    - Enable/disable the explicit Web proxy for HTTP and HTTPS session.
                choices:
                    - enable
                    - disable
            strict-guest:
                description:
                    - Enable/disable strict guest user checking by the explicit web proxy.
                choices:
                    - enable
                    - disable
            trace-auth-no-rsp:
                description:
                    - Enable/disable logging timed-out authentication requests.
                choices:
                    - enable
                    - disable
            unknown-http-version:
                description:
                    - Either reject unknown HTTP traffic as malformed or handle unknown HTTP traffic as best as the proxy server can.
                choices:
                    - reject
                    - best-effort
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure explicit Web proxy settings.
    fortios_web_proxy_explicit:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      web_proxy_explicit:
        ftp-incoming-port: "<your_own_value>"
        ftp-over-http: "enable"
        http-incoming-port: "<your_own_value>"
        https-incoming-port: "<your_own_value>"
        https-replacement-message: "enable"
        incoming-ip: "<your_own_value>"
        incoming-ip6: "<your_own_value>"
        ipv6-status: "enable"
        message-upon-server-error: "enable"
        outgoing-ip: "<your_own_value>"
        outgoing-ip6: "<your_own_value>"
        pac-file-data: "<your_own_value>"
        pac-file-name: "<your_own_value>"
        pac-file-server-port: "<your_own_value>"
        pac-file-server-status: "enable"
        pac-file-url: "<your_own_value>"
        pac-policy:
         -
            comments: "<your_own_value>"
            dstaddr:
             -
                name: "default_name_22 (source firewall.address.name firewall.addrgrp.name)"
            pac-file-data: "<your_own_value>"
            pac-file-name: "<your_own_value>"
            policyid: "25"
            srcaddr:
             -
                name: "default_name_27 (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name)"
            srcaddr6:
             -
                name: "default_name_29 (source firewall.address6.name firewall.addrgrp6.name)"
            status: "enable"
        pref-dns-result: "ipv4"
        realm: "<your_own_value>"
        sec-default-action: "accept"
        socks: "enable"
        socks-incoming-port: "<your_own_value>"
        ssl-algorithm: "low"
        status: "enable"
        strict-guest: "enable"
        trace-auth-no-rsp: "enable"
        unknown-http-version: "reject"
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


def filter_web_proxy_explicit_data(json):
    option_list = ['ftp-incoming-port', 'ftp-over-http', 'http-incoming-port',
                   'https-incoming-port', 'https-replacement-message', 'incoming-ip',
                   'incoming-ip6', 'ipv6-status', 'message-upon-server-error',
                   'outgoing-ip', 'outgoing-ip6', 'pac-file-data',
                   'pac-file-name', 'pac-file-server-port', 'pac-file-server-status',
                   'pac-file-url', 'pac-policy', 'pref-dns-result',
                   'realm', 'sec-default-action', 'socks',
                   'socks-incoming-port', 'ssl-algorithm', 'status',
                   'strict-guest', 'trace-auth-no-rsp', 'unknown-http-version']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def web_proxy_explicit(data, fos):
    vdom = data['vdom']
    web_proxy_explicit_data = data['web_proxy_explicit']
    filtered_data = filter_web_proxy_explicit_data(web_proxy_explicit_data)

    return fos.set('web-proxy',
                   'explicit',
                   data=filtered_data,
                   vdom=vdom)


def fortios_web_proxy(data, fos):
    login(data, fos)

    if data['web_proxy_explicit']:
        resp = web_proxy_explicit(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "web_proxy_explicit": {
            "required": False, "type": "dict",
            "options": {
                "ftp-incoming-port": {"required": False, "type": "str"},
                "ftp-over-http": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "http-incoming-port": {"required": False, "type": "str"},
                "https-incoming-port": {"required": False, "type": "str"},
                "https-replacement-message": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "incoming-ip": {"required": False, "type": "str"},
                "incoming-ip6": {"required": False, "type": "str"},
                "ipv6-status": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "message-upon-server-error": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "outgoing-ip": {"required": False, "type": "str"},
                "outgoing-ip6": {"required": False, "type": "str"},
                "pac-file-data": {"required": False, "type": "str"},
                "pac-file-name": {"required": False, "type": "str"},
                "pac-file-server-port": {"required": False, "type": "str"},
                "pac-file-server-status": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "pac-file-url": {"required": False, "type": "str"},
                "pac-policy": {"required": False, "type": "list",
                               "options": {
                                   "comments": {"required": False, "type": "str"},
                                   "dstaddr": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                                   "pac-file-data": {"required": False, "type": "str"},
                                   "pac-file-name": {"required": False, "type": "str"},
                                   "policyid": {"required": True, "type": "int"},
                                   "srcaddr": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                                   "srcaddr6": {"required": False, "type": "list",
                                                "options": {
                                                    "name": {"required": True, "type": "str"}
                                                }},
                                   "status": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]}
                               }},
                "pref-dns-result": {"required": False, "type": "str",
                                    "choices": ["ipv4", "ipv6"]},
                "realm": {"required": False, "type": "str"},
                "sec-default-action": {"required": False, "type": "str",
                                       "choices": ["accept", "deny"]},
                "socks": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "socks-incoming-port": {"required": False, "type": "str"},
                "ssl-algorithm": {"required": False, "type": "str",
                                  "choices": ["low"]},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "strict-guest": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "trace-auth-no-rsp": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "unknown-http-version": {"required": False, "type": "str",
                                         "choices": ["reject", "best-effort"]}

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
