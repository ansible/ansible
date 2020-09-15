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
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify web_proxy feature and explicit category.
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
    web_proxy_explicit:
        description:
            - Configure explicit Web proxy settings.
        default: null
        type: dict
        suboptions:
            ftp_incoming_port:
                description:
                    - Accept incoming FTP-over-HTTP requests on one or more ports (0 - 65535).
                type: str
            ftp_over_http:
                description:
                    - Enable to proxy FTP-over-HTTP sessions sent from a web browser.
                type: str
                choices:
                    - enable
                    - disable
            http_incoming_port:
                description:
                    - Accept incoming HTTP requests on one or more ports (0 - 65535).
                type: str
            https_incoming_port:
                description:
                    - Accept incoming HTTPS requests on one or more ports (0 - 65535).
                type: str
            https_replacement_message:
                description:
                    - Enable/disable sending the client a replacement message for HTTPS requests.
                type: str
                choices:
                    - enable
                    - disable
            incoming_ip:
                description:
                    - Restrict the explicit HTTP proxy to only accept sessions from this IP address. An interface must have this IP address.
                type: str
            incoming_ip6:
                description:
                    - Restrict the explicit web proxy to only accept sessions from this IPv6 address. An interface must have this IPv6 address.
                type: str
            ipv6_status:
                description:
                    - Enable/disable allowing an IPv6 web proxy destination in policies and all IPv6 related entries in this command.
                type: str
                choices:
                    - enable
                    - disable
            message_upon_server_error:
                description:
                    - Enable/disable displaying a replacement message when a server error is detected.
                type: str
                choices:
                    - enable
                    - disable
            outgoing_ip:
                description:
                    - Outgoing HTTP requests will have this IP address as their source address. An interface must have this IP address.
                type: str
            outgoing_ip6:
                description:
                    - Outgoing HTTP requests will leave this IPv6. Multiple interfaces can be specified. Interfaces must have these IPv6 addresses.
                type: str
            pac_file_data:
                description:
                    - PAC file contents enclosed in quotes (maximum of 256K bytes).
                type: str
            pac_file_name:
                description:
                    - Pac file name.
                type: str
            pac_file_server_port:
                description:
                    - Port number that PAC traffic from client web browsers uses to connect to the explicit web proxy (0 - 65535).
                type: str
            pac_file_server_status:
                description:
                    - Enable/disable Proxy Auto-Configuration (PAC) for users of this explicit proxy profile.
                type: str
                choices:
                    - enable
                    - disable
            pac_file_url:
                description:
                    - PAC file access URL.
                type: str
            pac_policy:
                description:
                    - PAC policies.
                type: list
                suboptions:
                    comments:
                        description:
                            - Optional comments.
                        type: str
                    dstaddr:
                        description:
                            - Destination address objects.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                                type: str
                    pac_file_data:
                        description:
                            - PAC file contents enclosed in quotes (maximum of 256K bytes).
                        type: str
                    pac_file_name:
                        description:
                            - Pac file name.
                        type: str
                    policyid:
                        description:
                            - Policy ID.
                        required: true
                        type: int
                    srcaddr:
                        description:
                            - Source address objects.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name.
                                required: true
                                type: str
                    srcaddr6:
                        description:
                            - Source address6 objects.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                                required: true
                                type: str
                    status:
                        description:
                            - Enable/disable policy.
                        type: str
                        choices:
                            - enable
                            - disable
            pref_dns_result:
                description:
                    - Prefer resolving addresses using the configured IPv4 or IPv6 DNS server .
                type: str
                choices:
                    - ipv4
                    - ipv6
            realm:
                description:
                    - Authentication realm used to identify the explicit web proxy (maximum of 63 characters).
                type: str
            sec_default_action:
                description:
                    - Accept or deny explicit web proxy sessions when no web proxy firewall policy exists.
                type: str
                choices:
                    - accept
                    - deny
            socks:
                description:
                    - Enable/disable the SOCKS proxy.
                type: str
                choices:
                    - enable
                    - disable
            socks_incoming_port:
                description:
                    - Accept incoming SOCKS proxy requests on one or more ports (0 - 65535).
                type: str
            ssl_algorithm:
                description:
                    - "Relative strength of encryption algorithms accepted in HTTPS deep scan: high, medium, or low."
                type: str
                choices:
                    - low
            status:
                description:
                    - Enable/disable the explicit Web proxy for HTTP and HTTPS session.
                type: str
                choices:
                    - enable
                    - disable
            strict_guest:
                description:
                    - Enable/disable strict guest user checking by the explicit web proxy.
                type: str
                choices:
                    - enable
                    - disable
            trace_auth_no_rsp:
                description:
                    - Enable/disable logging timed-out authentication requests.
                type: str
                choices:
                    - enable
                    - disable
            unknown_http_version:
                description:
                    - Either reject unknown HTTP traffic as malformed or handle unknown HTTP traffic as best as the proxy server can.
                type: str
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
   ssl_verify: "False"
  tasks:
  - name: Configure explicit Web proxy settings.
    fortios_web_proxy_explicit:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      web_proxy_explicit:
        ftp_incoming_port: "<your_own_value>"
        ftp_over_http: "enable"
        http_incoming_port: "<your_own_value>"
        https_incoming_port: "<your_own_value>"
        https_replacement_message: "enable"
        incoming_ip: "<your_own_value>"
        incoming_ip6: "<your_own_value>"
        ipv6_status: "enable"
        message_upon_server_error: "enable"
        outgoing_ip: "<your_own_value>"
        outgoing_ip6: "<your_own_value>"
        pac_file_data: "<your_own_value>"
        pac_file_name: "<your_own_value>"
        pac_file_server_port: "<your_own_value>"
        pac_file_server_status: "enable"
        pac_file_url: "<your_own_value>"
        pac_policy:
         -
            comments: "<your_own_value>"
            dstaddr:
             -
                name: "default_name_22 (source firewall.address.name firewall.addrgrp.name)"
            pac_file_data: "<your_own_value>"
            pac_file_name: "<your_own_value>"
            policyid: "25"
            srcaddr:
             -
                name: "default_name_27 (source firewall.address.name firewall.addrgrp.name firewall.proxy-address.name firewall.proxy-addrgrp.name)"
            srcaddr6:
             -
                name: "default_name_29 (source firewall.address6.name firewall.addrgrp6.name)"
            status: "enable"
        pref_dns_result: "ipv4"
        realm: "<your_own_value>"
        sec_default_action: "accept"
        socks: "enable"
        socks_incoming_port: "<your_own_value>"
        ssl_algorithm: "low"
        status: "enable"
        strict_guest: "enable"
        trace_auth_no_rsp: "enable"
        unknown_http_version: "reject"
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


def filter_web_proxy_explicit_data(json):
    option_list = ['ftp_incoming_port', 'ftp_over_http', 'http_incoming_port',
                   'https_incoming_port', 'https_replacement_message', 'incoming_ip',
                   'incoming_ip6', 'ipv6_status', 'message_upon_server_error',
                   'outgoing_ip', 'outgoing_ip6', 'pac_file_data',
                   'pac_file_name', 'pac_file_server_port', 'pac_file_server_status',
                   'pac_file_url', 'pac_policy', 'pref_dns_result',
                   'realm', 'sec_default_action', 'socks',
                   'socks_incoming_port', 'ssl_algorithm', 'status',
                   'strict_guest', 'trace_auth_no_rsp', 'unknown_http_version']
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


def web_proxy_explicit(data, fos):
    vdom = data['vdom']
    web_proxy_explicit_data = data['web_proxy_explicit']
    filtered_data = underscore_to_hyphen(filter_web_proxy_explicit_data(web_proxy_explicit_data))

    return fos.set('web-proxy',
                   'explicit',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_web_proxy(data, fos):

    if data['web_proxy_explicit']:
        resp = web_proxy_explicit(data, fos)

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
        "web_proxy_explicit": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "ftp_incoming_port": {"required": False, "type": "str"},
                "ftp_over_http": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "http_incoming_port": {"required": False, "type": "str"},
                "https_incoming_port": {"required": False, "type": "str"},
                "https_replacement_message": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "incoming_ip": {"required": False, "type": "str"},
                "incoming_ip6": {"required": False, "type": "str"},
                "ipv6_status": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "message_upon_server_error": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "outgoing_ip": {"required": False, "type": "str"},
                "outgoing_ip6": {"required": False, "type": "str"},
                "pac_file_data": {"required": False, "type": "str"},
                "pac_file_name": {"required": False, "type": "str"},
                "pac_file_server_port": {"required": False, "type": "str"},
                "pac_file_server_status": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "pac_file_url": {"required": False, "type": "str"},
                "pac_policy": {"required": False, "type": "list",
                               "options": {
                                   "comments": {"required": False, "type": "str"},
                                   "dstaddr": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                                   "pac_file_data": {"required": False, "type": "str"},
                                   "pac_file_name": {"required": False, "type": "str"},
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
                "pref_dns_result": {"required": False, "type": "str",
                                    "choices": ["ipv4", "ipv6"]},
                "realm": {"required": False, "type": "str"},
                "sec_default_action": {"required": False, "type": "str",
                                       "choices": ["accept", "deny"]},
                "socks": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "socks_incoming_port": {"required": False, "type": "str"},
                "ssl_algorithm": {"required": False, "type": "str",
                                  "choices": ["low"]},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "strict_guest": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "trace_auth_no_rsp": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "unknown_http_version": {"required": False, "type": "str",
                                         "choices": ["reject", "best-effort"]}

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
