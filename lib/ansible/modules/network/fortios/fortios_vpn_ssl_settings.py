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
module: fortios_vpn_ssl_settings
short_description: Configure SSL VPN in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify vpn_ssl feature and settings category.
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
    vpn_ssl_settings:
        description:
            - Configure SSL VPN.
        default: null
        type: dict
        suboptions:
            auth_timeout:
                description:
                    - SSL-VPN authentication timeout (1 - 259200 sec (3 days), 0 for no timeout).
                type: int
            authentication_rule:
                description:
                    - Authentication rule for SSL VPN.
                type: list
                suboptions:
                    auth:
                        description:
                            - SSL VPN authentication method restriction.
                        type: str
                        choices:
                            - any
                            - local
                            - radius
                            - tacacs+
                            - ldap
                    cipher:
                        description:
                            - SSL VPN cipher strength.
                        type: str
                        choices:
                            - any
                            - high
                            - medium
                    client_cert:
                        description:
                            - Enable/disable SSL VPN client certificate restrictive.
                        type: str
                        choices:
                            - enable
                            - disable
                    groups:
                        description:
                            - User groups.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Group name. Source user.group.name.
                                required: true
                                type: str
                    id:
                        description:
                            - ID (0 - 4294967295).
                        required: true
                        type: int
                    portal:
                        description:
                            - SSL VPN portal. Source vpn.ssl.web.portal.name.
                        type: str
                    realm:
                        description:
                            - SSL VPN realm. Source vpn.ssl.web.realm.url-path.
                        type: str
                    source_address:
                        description:
                            - Source address of incoming traffic.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                                type: str
                    source_address_negate:
                        description:
                            - Enable/disable negated source address match.
                        type: str
                        choices:
                            - enable
                            - disable
                    source_address6:
                        description:
                            - IPv6 source address of incoming traffic.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - IPv6 address name. Source firewall.address6.name firewall.addrgrp6.name.
                                required: true
                                type: str
                    source_address6_negate:
                        description:
                            - Enable/disable negated source IPv6 address match.
                        type: str
                        choices:
                            - enable
                            - disable
                    source_interface:
                        description:
                            - SSL VPN source interface of incoming traffic.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Interface name. Source system.interface.name system.zone.name.
                                required: true
                                type: str
                    users:
                        description:
                            - User name.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - User name. Source user.local.name.
                                required: true
                                type: str
            auto_tunnel_static_route:
                description:
                    - Enable to auto-create static routes for the SSL-VPN tunnel IP addresses.
                type: str
                choices:
                    - enable
                    - disable
            banned_cipher:
                description:
                    - Select one or more cipher technologies that cannot be used in SSL-VPN negotiations.
                type: str
                choices:
                    - RSA
                    - DH
                    - DHE
                    - ECDH
                    - ECDHE
                    - DSS
                    - ECDSA
                    - AES
                    - AESGCM
                    - CAMELLIA
                    - 3DES
                    - SHA1
                    - SHA256
                    - SHA384
                    - STATIC
            check_referer:
                description:
                    - Enable/disable verification of referer field in HTTP request header.
                type: str
                choices:
                    - enable
                    - disable
            default_portal:
                description:
                    - Default SSL VPN portal. Source vpn.ssl.web.portal.name.
                type: str
            deflate_compression_level:
                description:
                    - Compression level (0~9).
                type: int
            deflate_min_data_size:
                description:
                    - Minimum amount of data that triggers compression (200 - 65535 bytes).
                type: int
            dns_server1:
                description:
                    - DNS server 1.
                type: str
            dns_server2:
                description:
                    - DNS server 2.
                type: str
            dns_suffix:
                description:
                    - DNS suffix used for SSL-VPN clients.
                type: str
            dtls_hello_timeout:
                description:
                    - SSLVPN maximum DTLS hello timeout (10 - 60 sec).
                type: int
            dtls_tunnel:
                description:
                    - Enable DTLS to prevent eavesdropping, tampering, or message forgery.
                type: str
                choices:
                    - enable
                    - disable
            force_two_factor_auth:
                description:
                    - Enable to force two-factor authentication for all SSL-VPNs.
                type: str
                choices:
                    - enable
                    - disable
            header_x_forwarded_for:
                description:
                    - Forward the same, add, or remove HTTP header.
                type: str
                choices:
                    - pass
                    - add
                    - remove
            http_compression:
                description:
                    - Enable to allow HTTP compression over SSL-VPN tunnels.
                type: str
                choices:
                    - enable
                    - disable
            http_only_cookie:
                description:
                    - Enable/disable SSL-VPN support for HttpOnly cookies.
                type: str
                choices:
                    - enable
                    - disable
            http_request_body_timeout:
                description:
                    - SSL-VPN session is disconnected if an HTTP request body is not received within this time (1 - 60 sec).
                type: int
            http_request_header_timeout:
                description:
                    - SSL-VPN session is disconnected if an HTTP request header is not received within this time (1 - 60 sec).
                type: int
            https_redirect:
                description:
                    - Enable/disable redirect of port 80 to SSL-VPN port.
                type: str
                choices:
                    - enable
                    - disable
            idle_timeout:
                description:
                    - SSL VPN disconnects if idle for specified time in seconds.
                type: int
            ipv6_dns_server1:
                description:
                    - IPv6 DNS server 1.
                type: str
            ipv6_dns_server2:
                description:
                    - IPv6 DNS server 2.
                type: str
            ipv6_wins_server1:
                description:
                    - IPv6 WINS server 1.
                type: str
            ipv6_wins_server2:
                description:
                    - IPv6 WINS server 2.
                type: str
            login_attempt_limit:
                description:
                    - SSL VPN maximum login attempt times before block (0 - 10).
                type: int
            login_block_time:
                description:
                    - Time for which a user is blocked from logging in after too many failed login attempts (0 - 86400 sec).
                type: int
            login_timeout:
                description:
                    - SSLVPN maximum login timeout (10 - 180 sec).
                type: int
            port:
                description:
                    - SSL-VPN access port (1 - 65535).
                type: int
            port_precedence:
                description:
                    - Enable means that if SSL-VPN connections are allowed on an interface admin GUI connections are blocked on that interface.
                type: str
                choices:
                    - enable
                    - disable
            reqclientcert:
                description:
                    - Enable to require client certificates for all SSL-VPN users.
                type: str
                choices:
                    - enable
                    - disable
            route_source_interface:
                description:
                    - Enable to allow SSL-VPN sessions to bypass routing and bind to the incoming interface.
                type: str
                choices:
                    - enable
                    - disable
            servercert:
                description:
                    - Name of the server certificate to be used for SSL-VPNs. Source vpn.certificate.local.name.
                type: str
            source_address:
                description:
                    - Source address of incoming traffic.
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
                        type: str
            source_address_negate:
                description:
                    - Enable/disable negated source address match.
                type: str
                choices:
                    - enable
                    - disable
            source_address6:
                description:
                    - IPv6 source address of incoming traffic.
                type: list
                suboptions:
                    name:
                        description:
                            - IPv6 address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
                        type: str
            source_address6_negate:
                description:
                    - Enable/disable negated source IPv6 address match.
                type: str
                choices:
                    - enable
                    - disable
            source_interface:
                description:
                    - SSL VPN source interface of incoming traffic.
                type: list
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
                        type: str
            ssl_client_renegotiation:
                description:
                    - Enable to allow client renegotiation by the server if the tunnel goes down.
                type: str
                choices:
                    - disable
                    - enable
            ssl_insert_empty_fragment:
                description:
                    - Enable/disable insertion of empty fragment.
                type: str
                choices:
                    - enable
                    - disable
            tlsv1_0:
                description:
                    - Enable/disable TLSv1.0.
                type: str
                choices:
                    - enable
                    - disable
            tlsv1_1:
                description:
                    - Enable/disable TLSv1.1.
                type: str
                choices:
                    - enable
                    - disable
            tlsv1_2:
                description:
                    - Enable/disable TLSv1.2.
                type: str
                choices:
                    - enable
                    - disable
            tunnel_ip_pools:
                description:
                    - Names of the IPv4 IP Pool firewall objects that define the IP addresses reserved for remote clients.
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
                        type: str
            tunnel_ipv6_pools:
                description:
                    - Names of the IPv6 IP Pool firewall objects that define the IP addresses reserved for remote clients.
                type: list
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
                        type: str
            unsafe_legacy_renegotiation:
                description:
                    - Enable/disable unsafe legacy re-negotiation.
                type: str
                choices:
                    - enable
                    - disable
            url_obscuration:
                description:
                    - Enable to obscure the host name of the URL of the web browser display.
                type: str
                choices:
                    - enable
                    - disable
            wins_server1:
                description:
                    - WINS server 1.
                type: str
            wins_server2:
                description:
                    - WINS server 2.
                type: str
            x_content_type_options:
                description:
                    - Add HTTP X-Content-Type-Options header.
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
  - name: Configure SSL VPN.
    fortios_vpn_ssl_settings:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      vpn_ssl_settings:
        auth_timeout: "3"
        authentication_rule:
         -
            auth: "any"
            cipher: "any"
            client_cert: "enable"
            groups:
             -
                name: "default_name_9 (source user.group.name)"
            id:  "10"
            portal: "<your_own_value> (source vpn.ssl.web.portal.name)"
            realm: "<your_own_value> (source vpn.ssl.web.realm.url-path)"
            source_address:
             -
                name: "default_name_14 (source firewall.address.name firewall.addrgrp.name)"
            source_address_negate: "enable"
            source_address6:
             -
                name: "default_name_17 (source firewall.address6.name firewall.addrgrp6.name)"
            source_address6_negate: "enable"
            source_interface:
             -
                name: "default_name_20 (source system.interface.name system.zone.name)"
            users:
             -
                name: "default_name_22 (source user.local.name)"
        auto_tunnel_static_route: "enable"
        banned_cipher: "RSA"
        check_referer: "enable"
        default_portal: "<your_own_value> (source vpn.ssl.web.portal.name)"
        deflate_compression_level: "27"
        deflate_min_data_size: "28"
        dns_server1: "<your_own_value>"
        dns_server2: "<your_own_value>"
        dns_suffix: "<your_own_value>"
        dtls_hello_timeout: "32"
        dtls_tunnel: "enable"
        force_two_factor_auth: "enable"
        header_x_forwarded_for: "pass"
        http_compression: "enable"
        http_only_cookie: "enable"
        http_request_body_timeout: "38"
        http_request_header_timeout: "39"
        https_redirect: "enable"
        idle_timeout: "41"
        ipv6_dns_server1: "<your_own_value>"
        ipv6_dns_server2: "<your_own_value>"
        ipv6_wins_server1: "<your_own_value>"
        ipv6_wins_server2: "<your_own_value>"
        login_attempt_limit: "46"
        login_block_time: "47"
        login_timeout: "48"
        port: "49"
        port_precedence: "enable"
        reqclientcert: "enable"
        route_source_interface: "enable"
        servercert: "<your_own_value> (source vpn.certificate.local.name)"
        source_address:
         -
            name: "default_name_55 (source firewall.address.name firewall.addrgrp.name)"
        source_address_negate: "enable"
        source_address6:
         -
            name: "default_name_58 (source firewall.address6.name firewall.addrgrp6.name)"
        source_address6_negate: "enable"
        source_interface:
         -
            name: "default_name_61 (source system.interface.name system.zone.name)"
        ssl_client_renegotiation: "disable"
        ssl_insert_empty_fragment: "enable"
        tlsv1_0: "enable"
        tlsv1_1: "enable"
        tlsv1_2: "enable"
        tunnel_ip_pools:
         -
            name: "default_name_68 (source firewall.address.name firewall.addrgrp.name)"
        tunnel_ipv6_pools:
         -
            name: "default_name_70 (source firewall.address6.name firewall.addrgrp6.name)"
        unsafe_legacy_renegotiation: "enable"
        url_obscuration: "enable"
        wins_server1: "<your_own_value>"
        wins_server2: "<your_own_value>"
        x_content_type_options: "enable"
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


def filter_vpn_ssl_settings_data(json):
    option_list = ['auth_timeout', 'authentication_rule', 'auto_tunnel_static_route',
                   'banned_cipher', 'check_referer', 'default_portal',
                   'deflate_compression_level', 'deflate_min_data_size', 'dns_server1',
                   'dns_server2', 'dns_suffix', 'dtls_hello_timeout',
                   'dtls_tunnel', 'force_two_factor_auth', 'header_x_forwarded_for',
                   'http_compression', 'http_only_cookie', 'http_request_body_timeout',
                   'http_request_header_timeout', 'https_redirect', 'idle_timeout',
                   'ipv6_dns_server1', 'ipv6_dns_server2', 'ipv6_wins_server1',
                   'ipv6_wins_server2', 'login_attempt_limit', 'login_block_time',
                   'login_timeout', 'port', 'port_precedence',
                   'reqclientcert', 'route_source_interface', 'servercert',
                   'source_address', 'source_address_negate', 'source_address6',
                   'source_address6_negate', 'source_interface', 'ssl_client_renegotiation',
                   'ssl_insert_empty_fragment', 'tlsv1_0', 'tlsv1_1',
                   'tlsv1_2', 'tunnel_ip_pools', 'tunnel_ipv6_pools',
                   'unsafe_legacy_renegotiation', 'url_obscuration', 'wins_server1',
                   'wins_server2', 'x_content_type_options']
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


def vpn_ssl_settings(data, fos):
    vdom = data['vdom']
    vpn_ssl_settings_data = data['vpn_ssl_settings']
    filtered_data = underscore_to_hyphen(filter_vpn_ssl_settings_data(vpn_ssl_settings_data))

    return fos.set('vpn.ssl',
                   'settings',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_vpn_ssl(data, fos):

    if data['vpn_ssl_settings']:
        resp = vpn_ssl_settings(data, fos)

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
        "vpn_ssl_settings": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "auth_timeout": {"required": False, "type": "int"},
                "authentication_rule": {"required": False, "type": "list",
                                        "options": {
                                            "auth": {"required": False, "type": "str",
                                                     "choices": ["any", "local", "radius",
                                                                 "tacacs+", "ldap"]},
                                            "cipher": {"required": False, "type": "str",
                                                       "choices": ["any", "high", "medium"]},
                                            "client_cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                                            "groups": {"required": False, "type": "list",
                                                       "options": {
                                                           "name": {"required": True, "type": "str"}
                                                       }},
                                            "id": {"required": True, "type": "int"},
                                            "portal": {"required": False, "type": "str"},
                                            "realm": {"required": False, "type": "str"},
                                            "source_address": {"required": False, "type": "list",
                                                               "options": {
                                                                   "name": {"required": True, "type": "str"}
                                                               }},
                                            "source_address_negate": {"required": False, "type": "str",
                                                                      "choices": ["enable", "disable"]},
                                            "source_address6": {"required": False, "type": "list",
                                                                "options": {
                                                                    "name": {"required": True, "type": "str"}
                                                                }},
                                            "source_address6_negate": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                            "source_interface": {"required": False, "type": "list",
                                                                 "options": {
                                                                     "name": {"required": True, "type": "str"}
                                                                 }},
                                            "users": {"required": False, "type": "list",
                                                      "options": {
                                                          "name": {"required": True, "type": "str"}
                                                      }}
                                        }},
                "auto_tunnel_static_route": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "banned_cipher": {"required": False, "type": "str",
                                  "choices": ["RSA", "DH", "DHE",
                                              "ECDH", "ECDHE", "DSS",
                                              "ECDSA", "AES", "AESGCM",
                                              "CAMELLIA", "3DES", "SHA1",
                                              "SHA256", "SHA384", "STATIC"]},
                "check_referer": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "default_portal": {"required": False, "type": "str"},
                "deflate_compression_level": {"required": False, "type": "int"},
                "deflate_min_data_size": {"required": False, "type": "int"},
                "dns_server1": {"required": False, "type": "str"},
                "dns_server2": {"required": False, "type": "str"},
                "dns_suffix": {"required": False, "type": "str"},
                "dtls_hello_timeout": {"required": False, "type": "int"},
                "dtls_tunnel": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "force_two_factor_auth": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "header_x_forwarded_for": {"required": False, "type": "str",
                                           "choices": ["pass", "add", "remove"]},
                "http_compression": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "http_only_cookie": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "http_request_body_timeout": {"required": False, "type": "int"},
                "http_request_header_timeout": {"required": False, "type": "int"},
                "https_redirect": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "idle_timeout": {"required": False, "type": "int"},
                "ipv6_dns_server1": {"required": False, "type": "str"},
                "ipv6_dns_server2": {"required": False, "type": "str"},
                "ipv6_wins_server1": {"required": False, "type": "str"},
                "ipv6_wins_server2": {"required": False, "type": "str"},
                "login_attempt_limit": {"required": False, "type": "int"},
                "login_block_time": {"required": False, "type": "int"},
                "login_timeout": {"required": False, "type": "int"},
                "port": {"required": False, "type": "int"},
                "port_precedence": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "reqclientcert": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "route_source_interface": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "servercert": {"required": False, "type": "str"},
                "source_address": {"required": False, "type": "list",
                                   "options": {
                                       "name": {"required": True, "type": "str"}
                                   }},
                "source_address_negate": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "source_address6": {"required": False, "type": "list",
                                    "options": {
                                        "name": {"required": True, "type": "str"}
                                    }},
                "source_address6_negate": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "source_interface": {"required": False, "type": "list",
                                     "options": {
                                         "name": {"required": True, "type": "str"}
                                     }},
                "ssl_client_renegotiation": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                "ssl_insert_empty_fragment": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "tlsv1_0": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "tlsv1_1": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "tlsv1_2": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "tunnel_ip_pools": {"required": False, "type": "list",
                                    "options": {
                                        "name": {"required": True, "type": "str"}
                                    }},
                "tunnel_ipv6_pools": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "unsafe_legacy_renegotiation": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "url_obscuration": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "wins_server1": {"required": False, "type": "str"},
                "wins_server2": {"required": False, "type": "str"},
                "x_content_type_options": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_vpn_ssl(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_vpn_ssl(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
