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
module: fortios_vpn_ssl_settings
short_description: Configure SSL VPN in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify vpn_ssl feature and settings category.
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
    vpn_ssl_settings:
        description:
            - Configure SSL VPN.
        default: null
        suboptions:
            auth-timeout:
                description:
                    - SSL-VPN authentication timeout (1 - 259200 sec (3 days), 0 for no timeout).
            authentication-rule:
                description:
                    - Authentication rule for SSL VPN.
                suboptions:
                    auth:
                        description:
                            - SSL VPN authentication method restriction.
                        choices:
                            - any
                            - local
                            - radius
                            - tacacs+
                            - ldap
                    cipher:
                        description:
                            - SSL VPN cipher strength.
                        choices:
                            - any
                            - high
                            - medium
                    client-cert:
                        description:
                            - Enable/disable SSL VPN client certificate restrictive.
                        choices:
                            - enable
                            - disable
                    groups:
                        description:
                            - User groups.
                        suboptions:
                            name:
                                description:
                                    - Group name. Source user.group.name.
                                required: true
                    id:
                        description:
                            - ID (0 - 4294967295).
                        required: true
                    portal:
                        description:
                            - SSL VPN portal. Source vpn.ssl.web.portal.name.
                    realm:
                        description:
                            - SSL VPN realm. Source vpn.ssl.web.realm.url-path.
                    source-address:
                        description:
                            - Source address of incoming traffic.
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                    source-address-negate:
                        description:
                            - Enable/disable negated source address match.
                        choices:
                            - enable
                            - disable
                    source-address6:
                        description:
                            - IPv6 source address of incoming traffic.
                        suboptions:
                            name:
                                description:
                                    - IPv6 address name. Source firewall.address6.name firewall.addrgrp6.name.
                                required: true
                    source-address6-negate:
                        description:
                            - Enable/disable negated source IPv6 address match.
                        choices:
                            - enable
                            - disable
                    source-interface:
                        description:
                            - SSL VPN source interface of incoming traffic.
                        suboptions:
                            name:
                                description:
                                    - Interface name. Source system.interface.name system.zone.name.
                                required: true
                    users:
                        description:
                            - User name.
                        suboptions:
                            name:
                                description:
                                    - User name. Source user.local.name.
                                required: true
            auto-tunnel-static-route:
                description:
                    - Enable to auto-create static routes for the SSL-VPN tunnel IP addresses.
                choices:
                    - enable
                    - disable
            banned-cipher:
                description:
                    - Select one or more cipher technologies that cannot be used in SSL-VPN negotiations.
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
            check-referer:
                description:
                    - Enable/disable verification of referer field in HTTP request header.
                choices:
                    - enable
                    - disable
            default-portal:
                description:
                    - Default SSL VPN portal. Source vpn.ssl.web.portal.name.
            deflate-compression-level:
                description:
                    - Compression level (0~9).
            deflate-min-data-size:
                description:
                    - Minimum amount of data that triggers compression (200 - 65535 bytes).
            dns-server1:
                description:
                    - DNS server 1.
            dns-server2:
                description:
                    - DNS server 2.
            dns-suffix:
                description:
                    - DNS suffix used for SSL-VPN clients.
            dtls-hello-timeout:
                description:
                    - SSLVPN maximum DTLS hello timeout (10 - 60 sec, default = 10).
            dtls-tunnel:
                description:
                    - Enable DTLS to prevent eavesdropping, tampering, or message forgery.
                choices:
                    - enable
                    - disable
            force-two-factor-auth:
                description:
                    - Enable to force two-factor authentication for all SSL-VPNs.
                choices:
                    - enable
                    - disable
            header-x-forwarded-for:
                description:
                    - Forward the same, add, or remove HTTP header.
                choices:
                    - pass
                    - add
                    - remove
            http-compression:
                description:
                    - Enable to allow HTTP compression over SSL-VPN tunnels.
                choices:
                    - enable
                    - disable
            http-only-cookie:
                description:
                    - Enable/disable SSL-VPN support for HttpOnly cookies.
                choices:
                    - enable
                    - disable
            http-request-body-timeout:
                description:
                    - SSL-VPN session is disconnected if an HTTP request body is not received within this time (1 - 60 sec, default = 20).
            http-request-header-timeout:
                description:
                    - SSL-VPN session is disconnected if an HTTP request header is not received within this time (1 - 60 sec, default = 20).
            https-redirect:
                description:
                    - Enable/disable redirect of port 80 to SSL-VPN port.
                choices:
                    - enable
                    - disable
            idle-timeout:
                description:
                    - SSL VPN disconnects if idle for specified time in seconds.
            ipv6-dns-server1:
                description:
                    - IPv6 DNS server 1.
            ipv6-dns-server2:
                description:
                    - IPv6 DNS server 2.
            ipv6-wins-server1:
                description:
                    - IPv6 WINS server 1.
            ipv6-wins-server2:
                description:
                    - IPv6 WINS server 2.
            login-attempt-limit:
                description:
                    - SSL VPN maximum login attempt times before block (0 - 10, default = 2, 0 = no limit).
            login-block-time:
                description:
                    - Time for which a user is blocked from logging in after too many failed login attempts (0 - 86400 sec, default = 60).
            login-timeout:
                description:
                    - SSLVPN maximum login timeout (10 - 180 sec, default = 30).
            port:
                description:
                    - SSL-VPN access port (1 - 65535).
            port-precedence:
                description:
                    - Enable means that if SSL-VPN connections are allowed on an interface admin GUI connections are blocked on that interface.
                choices:
                    - enable
                    - disable
            reqclientcert:
                description:
                    - Enable to require client certificates for all SSL-VPN users.
                choices:
                    - enable
                    - disable
            route-source-interface:
                description:
                    - Enable to allow SSL-VPN sessions to bypass routing and bind to the incoming interface.
                choices:
                    - enable
                    - disable
            servercert:
                description:
                    - Name of the server certificate to be used for SSL-VPNs. Source vpn.certificate.local.name.
            source-address:
                description:
                    - Source address of incoming traffic.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            source-address-negate:
                description:
                    - Enable/disable negated source address match.
                choices:
                    - enable
                    - disable
            source-address6:
                description:
                    - IPv6 source address of incoming traffic.
                suboptions:
                    name:
                        description:
                            - IPv6 address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            source-address6-negate:
                description:
                    - Enable/disable negated source IPv6 address match.
                choices:
                    - enable
                    - disable
            source-interface:
                description:
                    - SSL VPN source interface of incoming traffic.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            ssl-client-renegotiation:
                description:
                    - Enable to allow client renegotiation by the server if the tunnel goes down.
                choices:
                    - disable
                    - enable
            ssl-insert-empty-fragment:
                description:
                    - Enable/disable insertion of empty fragment.
                choices:
                    - enable
                    - disable
            tlsv1-0:
                description:
                    - Enable/disable TLSv1.0.
                choices:
                    - enable
                    - disable
            tlsv1-1:
                description:
                    - Enable/disable TLSv1.1.
                choices:
                    - enable
                    - disable
            tlsv1-2:
                description:
                    - Enable/disable TLSv1.2.
                choices:
                    - enable
                    - disable
            tunnel-ip-pools:
                description:
                    - Names of the IPv4 IP Pool firewall objects that define the IP addresses reserved for remote clients.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            tunnel-ipv6-pools:
                description:
                    - Names of the IPv6 IP Pool firewall objects that define the IP addresses reserved for remote clients.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            unsafe-legacy-renegotiation:
                description:
                    - Enable/disable unsafe legacy re-negotiation.
                choices:
                    - enable
                    - disable
            url-obscuration:
                description:
                    - Enable to obscure the host name of the URL of the web browser display.
                choices:
                    - enable
                    - disable
            wins-server1:
                description:
                    - WINS server 1.
            wins-server2:
                description:
                    - WINS server 2.
            x-content-type-options:
                description:
                    - Add HTTP X-Content-Type-Options header.
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
  - name: Configure SSL VPN.
    fortios_vpn_ssl_settings:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      vpn_ssl_settings:
        auth-timeout: "3"
        authentication-rule:
         -
            auth: "any"
            cipher: "any"
            client-cert: "enable"
            groups:
             -
                name: "default_name_9 (source user.group.name)"
            id:  "10"
            portal: "<your_own_value> (source vpn.ssl.web.portal.name)"
            realm: "<your_own_value> (source vpn.ssl.web.realm.url-path)"
            source-address:
             -
                name: "default_name_14 (source firewall.address.name firewall.addrgrp.name)"
            source-address-negate: "enable"
            source-address6:
             -
                name: "default_name_17 (source firewall.address6.name firewall.addrgrp6.name)"
            source-address6-negate: "enable"
            source-interface:
             -
                name: "default_name_20 (source system.interface.name system.zone.name)"
            users:
             -
                name: "default_name_22 (source user.local.name)"
        auto-tunnel-static-route: "enable"
        banned-cipher: "RSA"
        check-referer: "enable"
        default-portal: "<your_own_value> (source vpn.ssl.web.portal.name)"
        deflate-compression-level: "27"
        deflate-min-data-size: "28"
        dns-server1: "<your_own_value>"
        dns-server2: "<your_own_value>"
        dns-suffix: "<your_own_value>"
        dtls-hello-timeout: "32"
        dtls-tunnel: "enable"
        force-two-factor-auth: "enable"
        header-x-forwarded-for: "pass"
        http-compression: "enable"
        http-only-cookie: "enable"
        http-request-body-timeout: "38"
        http-request-header-timeout: "39"
        https-redirect: "enable"
        idle-timeout: "41"
        ipv6-dns-server1: "<your_own_value>"
        ipv6-dns-server2: "<your_own_value>"
        ipv6-wins-server1: "<your_own_value>"
        ipv6-wins-server2: "<your_own_value>"
        login-attempt-limit: "46"
        login-block-time: "47"
        login-timeout: "48"
        port: "49"
        port-precedence: "enable"
        reqclientcert: "enable"
        route-source-interface: "enable"
        servercert: "<your_own_value> (source vpn.certificate.local.name)"
        source-address:
         -
            name: "default_name_55 (source firewall.address.name firewall.addrgrp.name)"
        source-address-negate: "enable"
        source-address6:
         -
            name: "default_name_58 (source firewall.address6.name firewall.addrgrp6.name)"
        source-address6-negate: "enable"
        source-interface:
         -
            name: "default_name_61 (source system.interface.name system.zone.name)"
        ssl-client-renegotiation: "disable"
        ssl-insert-empty-fragment: "enable"
        tlsv1-0: "enable"
        tlsv1-1: "enable"
        tlsv1-2: "enable"
        tunnel-ip-pools:
         -
            name: "default_name_68 (source firewall.address.name firewall.addrgrp.name)"
        tunnel-ipv6-pools:
         -
            name: "default_name_70 (source firewall.address6.name firewall.addrgrp6.name)"
        unsafe-legacy-renegotiation: "enable"
        url-obscuration: "enable"
        wins-server1: "<your_own_value>"
        wins-server2: "<your_own_value>"
        x-content-type-options: "enable"
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


def filter_vpn_ssl_settings_data(json):
    option_list = ['auth-timeout', 'authentication-rule', 'auto-tunnel-static-route',
                   'banned-cipher', 'check-referer', 'default-portal',
                   'deflate-compression-level', 'deflate-min-data-size', 'dns-server1',
                   'dns-server2', 'dns-suffix', 'dtls-hello-timeout',
                   'dtls-tunnel', 'force-two-factor-auth', 'header-x-forwarded-for',
                   'http-compression', 'http-only-cookie', 'http-request-body-timeout',
                   'http-request-header-timeout', 'https-redirect', 'idle-timeout',
                   'ipv6-dns-server1', 'ipv6-dns-server2', 'ipv6-wins-server1',
                   'ipv6-wins-server2', 'login-attempt-limit', 'login-block-time',
                   'login-timeout', 'port', 'port-precedence',
                   'reqclientcert', 'route-source-interface', 'servercert',
                   'source-address', 'source-address-negate', 'source-address6',
                   'source-address6-negate', 'source-interface', 'ssl-client-renegotiation',
                   'ssl-insert-empty-fragment', 'tlsv1-0', 'tlsv1-1',
                   'tlsv1-2', 'tunnel-ip-pools', 'tunnel-ipv6-pools',
                   'unsafe-legacy-renegotiation', 'url-obscuration', 'wins-server1',
                   'wins-server2', 'x-content-type-options']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def vpn_ssl_settings(data, fos):
    vdom = data['vdom']
    vpn_ssl_settings_data = data['vpn_ssl_settings']
    flattened_data = flatten_multilists_attributes(vpn_ssl_settings_data)
    filtered_data = filter_vpn_ssl_settings_data(flattened_data)
    return fos.set('vpn.ssl',
                   'settings',
                   data=filtered_data,
                   vdom=vdom)


def fortios_vpn_ssl(data, fos):
    login(data)

    if data['vpn_ssl_settings']:
        resp = vpn_ssl_settings(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "vpn_ssl_settings": {
            "required": False, "type": "dict",
            "options": {
                "auth-timeout": {"required": False, "type": "int"},
                "authentication-rule": {"required": False, "type": "list",
                                        "options": {
                                            "auth": {"required": False, "type": "str",
                                                     "choices": ["any", "local", "radius",
                                                                 "tacacs+", "ldap"]},
                                            "cipher": {"required": False, "type": "str",
                                                       "choices": ["any", "high", "medium"]},
                                            "client-cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                                            "groups": {"required": False, "type": "list",
                                                       "options": {
                                                           "name": {"required": True, "type": "str"}
                                                       }},
                                            "id": {"required": True, "type": "int"},
                                            "portal": {"required": False, "type": "str"},
                                            "realm": {"required": False, "type": "str"},
                                            "source-address": {"required": False, "type": "list",
                                                               "options": {
                                                                   "name": {"required": True, "type": "str"}
                                                               }},
                                            "source-address-negate": {"required": False, "type": "str",
                                                                      "choices": ["enable", "disable"]},
                                            "source-address6": {"required": False, "type": "list",
                                                                "options": {
                                                                    "name": {"required": True, "type": "str"}
                                                                }},
                                            "source-address6-negate": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                            "source-interface": {"required": False, "type": "list",
                                                                 "options": {
                                                                     "name": {"required": True, "type": "str"}
                                                                 }},
                                            "users": {"required": False, "type": "list",
                                                      "options": {
                                                          "name": {"required": True, "type": "str"}
                                                      }}
                                        }},
                "auto-tunnel-static-route": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "banned-cipher": {"required": False, "type": "str",
                                  "choices": ["RSA", "DH", "DHE",
                                              "ECDH", "ECDHE", "DSS",
                                              "ECDSA", "AES", "AESGCM",
                                              "CAMELLIA", "3DES", "SHA1",
                                              "SHA256", "SHA384", "STATIC"]},
                "check-referer": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "default-portal": {"required": False, "type": "str"},
                "deflate-compression-level": {"required": False, "type": "int"},
                "deflate-min-data-size": {"required": False, "type": "int"},
                "dns-server1": {"required": False, "type": "str"},
                "dns-server2": {"required": False, "type": "str"},
                "dns-suffix": {"required": False, "type": "str"},
                "dtls-hello-timeout": {"required": False, "type": "int"},
                "dtls-tunnel": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "force-two-factor-auth": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "header-x-forwarded-for": {"required": False, "type": "str",
                                           "choices": ["pass", "add", "remove"]},
                "http-compression": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "http-only-cookie": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "http-request-body-timeout": {"required": False, "type": "int"},
                "http-request-header-timeout": {"required": False, "type": "int"},
                "https-redirect": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "idle-timeout": {"required": False, "type": "int"},
                "ipv6-dns-server1": {"required": False, "type": "str"},
                "ipv6-dns-server2": {"required": False, "type": "str"},
                "ipv6-wins-server1": {"required": False, "type": "str"},
                "ipv6-wins-server2": {"required": False, "type": "str"},
                "login-attempt-limit": {"required": False, "type": "int"},
                "login-block-time": {"required": False, "type": "int"},
                "login-timeout": {"required": False, "type": "int"},
                "port": {"required": False, "type": "int"},
                "port-precedence": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "reqclientcert": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "route-source-interface": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "servercert": {"required": False, "type": "str"},
                "source-address": {"required": False, "type": "list",
                                   "options": {
                                       "name": {"required": True, "type": "str"}
                                   }},
                "source-address-negate": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "source-address6": {"required": False, "type": "list",
                                    "options": {
                                        "name": {"required": True, "type": "str"}
                                    }},
                "source-address6-negate": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "source-interface": {"required": False, "type": "list",
                                     "options": {
                                         "name": {"required": True, "type": "str"}
                                     }},
                "ssl-client-renegotiation": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                "ssl-insert-empty-fragment": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "tlsv1-0": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "tlsv1-1": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "tlsv1-2": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "tunnel-ip-pools": {"required": False, "type": "list",
                                    "options": {
                                        "name": {"required": True, "type": "str"}
                                    }},
                "tunnel-ipv6-pools": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "unsafe-legacy-renegotiation": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "url-obscuration": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "wins-server1": {"required": False, "type": "str"},
                "wins-server2": {"required": False, "type": "str"},
                "x-content-type-options": {"required": False, "type": "str",
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

    is_error, has_changed, result = fortios_vpn_ssl(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
