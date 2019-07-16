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
module: fortios_firewall_ssl_ssh_profile
short_description: Configure SSL/SSH protocol options in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and ssl_ssh_profile category.
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
            - FortiOS or FortiGate ip adress.
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
    firewall_ssl_ssh_profile:
        description:
            - Configure SSL/SSH protocol options.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            caname:
                description:
                    - CA certificate used by SSL Inspection. Source vpn.certificate.local.name.
            comment:
                description:
                    - Optional comments.
            ftps:
                description:
                    - Configure FTPS options.
                suboptions:
                    allow-invalid-server-cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        choices:
                            - enable
                            - disable
                    client-cert-request:
                        description:
                            - Action based on client certificate request.
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535, default = 443).
                    status:
                        description:
                            - Configure protocol inspection status.
                        choices:
                            - disable
                            - deep-inspection
                    unsupported-ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted-cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        choices:
                            - allow
                            - block
                            - ignore
            https:
                description:
                    - Configure HTTPS options.
                suboptions:
                    allow-invalid-server-cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        choices:
                            - enable
                            - disable
                    client-cert-request:
                        description:
                            - Action based on client certificate request.
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535, default = 443).
                    status:
                        description:
                            - Configure protocol inspection status.
                        choices:
                            - disable
                            - certificate-inspection
                            - deep-inspection
                    unsupported-ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted-cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        choices:
                            - allow
                            - block
                            - ignore
            imaps:
                description:
                    - Configure IMAPS options.
                suboptions:
                    allow-invalid-server-cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        choices:
                            - enable
                            - disable
                    client-cert-request:
                        description:
                            - Action based on client certificate request.
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535, default = 443).
                    status:
                        description:
                            - Configure protocol inspection status.
                        choices:
                            - disable
                            - deep-inspection
                    unsupported-ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted-cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        choices:
                            - allow
                            - block
                            - ignore
            mapi-over-https:
                description:
                    - Enable/disable inspection of MAPI over HTTPS.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name.
                required: true
            pop3s:
                description:
                    - Configure POP3S options.
                suboptions:
                    allow-invalid-server-cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        choices:
                            - enable
                            - disable
                    client-cert-request:
                        description:
                            - Action based on client certificate request.
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535, default = 443).
                    status:
                        description:
                            - Configure protocol inspection status.
                        choices:
                            - disable
                            - deep-inspection
                    unsupported-ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted-cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        choices:
                            - allow
                            - block
                            - ignore
            rpc-over-https:
                description:
                    - Enable/disable inspection of RPC over HTTPS.
                choices:
                    - enable
                    - disable
            server-cert:
                description:
                    - Certificate used by SSL Inspection to replace server certificate. Source vpn.certificate.local.name.
            server-cert-mode:
                description:
                    - Re-sign or replace the server's certificate.
                choices:
                    - re-sign
                    - replace
            smtps:
                description:
                    - Configure SMTPS options.
                suboptions:
                    allow-invalid-server-cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        choices:
                            - enable
                            - disable
                    client-cert-request:
                        description:
                            - Action based on client certificate request.
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535, default = 443).
                    status:
                        description:
                            - Configure protocol inspection status.
                        choices:
                            - disable
                            - deep-inspection
                    unsupported-ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted-cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        choices:
                            - allow
                            - block
                            - ignore
            ssh:
                description:
                    - Configure SSH options.
                suboptions:
                    inspect-all:
                        description:
                            - Level of SSL inspection.
                        choices:
                            - disable
                            - deep-inspection
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535, default = 443).
                    ssh-algorithm:
                        description:
                            - Relative strength of encryption algorithms accepted during negotiation.
                        choices:
                            - compatible
                            - high-encryption
                    ssh-policy-check:
                        description:
                            - Enable/disable SSH policy check.
                        choices:
                            - disable
                            - enable
                    ssh-tun-policy-check:
                        description:
                            - Enable/disable SSH tunnel policy check.
                        choices:
                            - disable
                            - enable
                    status:
                        description:
                            - Configure protocol inspection status.
                        choices:
                            - disable
                            - deep-inspection
                    unsupported-version:
                        description:
                            - Action based on SSH version being unsupported.
                        choices:
                            - bypass
                            - block
            ssl:
                description:
                    - Configure SSL options.
                suboptions:
                    allow-invalid-server-cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        choices:
                            - enable
                            - disable
                    client-cert-request:
                        description:
                            - Action based on client certificate request.
                        choices:
                            - bypass
                            - inspect
                            - block
                    inspect-all:
                        description:
                            - Level of SSL inspection.
                        choices:
                            - disable
                            - certificate-inspection
                            - deep-inspection
                    unsupported-ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted-cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        choices:
                            - allow
                            - block
                            - ignore
            ssl-anomalies-log:
                description:
                    - Enable/disable logging SSL anomalies.
                choices:
                    - disable
                    - enable
            ssl-exempt:
                description:
                    - Servers to exempt from SSL inspection.
                suboptions:
                    address:
                        description:
                            - IPv4 address object. Source firewall.address.name firewall.addrgrp.name.
                    address6:
                        description:
                            - IPv6 address object. Source firewall.address6.name firewall.addrgrp6.name.
                    fortiguard-category:
                        description:
                            - FortiGuard category ID.
                    id:
                        description:
                            - ID number.
                        required: true
                    regex:
                        description:
                            - Exempt servers by regular expression.
                    type:
                        description:
                            - Type of address object (IPv4 or IPv6) or FortiGuard category.
                        choices:
                            - fortiguard-category
                            - address
                            - address6
                            - wildcard-fqdn
                            - regex
                    wildcard-fqdn:
                        description:
                            - Exempt servers by wildcard FQDN. Source firewall.wildcard-fqdn.custom.name firewall.wildcard-fqdn.group.name.
            ssl-exemptions-log:
                description:
                    - Enable/disable logging SSL exemptions.
                choices:
                    - disable
                    - enable
            ssl-server:
                description:
                    - SSL servers.
                suboptions:
                    ftps-client-cert-request:
                        description:
                            - Action based on client certificate request during the FTPS handshake.
                        choices:
                            - bypass
                            - inspect
                            - block
                    https-client-cert-request:
                        description:
                            - Action based on client certificate request during the HTTPS handshake.
                        choices:
                            - bypass
                            - inspect
                            - block
                    id:
                        description:
                            - SSL server ID.
                        required: true
                    imaps-client-cert-request:
                        description:
                            - Action based on client certificate request during the IMAPS handshake.
                        choices:
                            - bypass
                            - inspect
                            - block
                    ip:
                        description:
                            - IPv4 address of the SSL server.
                    pop3s-client-cert-request:
                        description:
                            - Action based on client certificate request during the POP3S handshake.
                        choices:
                            - bypass
                            - inspect
                            - block
                    smtps-client-cert-request:
                        description:
                            - Action based on client certificate request during the SMTPS handshake.
                        choices:
                            - bypass
                            - inspect
                            - block
                    ssl-other-client-cert-request:
                        description:
                            - Action based on client certificate request during an SSL protocol handshake.
                        choices:
                            - bypass
                            - inspect
                            - block
            untrusted-caname:
                description:
                    - Untrusted CA certificate used by SSL Inspection. Source vpn.certificate.local.name.
            use-ssl-server:
                description:
                    - Enable/disable the use of SSL server table for SSL offloading.
                choices:
                    - disable
                    - enable
            whitelist:
                description:
                    - Enable/disable exempting servers by FortiGuard whitelist.
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
  - name: Configure SSL/SSH protocol options.
    fortios_firewall_ssl_ssh_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_ssl_ssh_profile:
        state: "present"
        caname: "<your_own_value> (source vpn.certificate.local.name)"
        comment: "Optional comments."
        ftps:
            allow-invalid-server-cert: "enable"
            client-cert-request: "bypass"
            ports: "8"
            status: "disable"
            unsupported-ssl: "bypass"
            untrusted-cert: "allow"
        https:
            allow-invalid-server-cert: "enable"
            client-cert-request: "bypass"
            ports: "15"
            status: "disable"
            unsupported-ssl: "bypass"
            untrusted-cert: "allow"
        imaps:
            allow-invalid-server-cert: "enable"
            client-cert-request: "bypass"
            ports: "22"
            status: "disable"
            unsupported-ssl: "bypass"
            untrusted-cert: "allow"
        mapi-over-https: "enable"
        name: "default_name_27"
        pop3s:
            allow-invalid-server-cert: "enable"
            client-cert-request: "bypass"
            ports: "31"
            status: "disable"
            unsupported-ssl: "bypass"
            untrusted-cert: "allow"
        rpc-over-https: "enable"
        server-cert: "<your_own_value> (source vpn.certificate.local.name)"
        server-cert-mode: "re-sign"
        smtps:
            allow-invalid-server-cert: "enable"
            client-cert-request: "bypass"
            ports: "41"
            status: "disable"
            unsupported-ssl: "bypass"
            untrusted-cert: "allow"
        ssh:
            inspect-all: "disable"
            ports: "47"
            ssh-algorithm: "compatible"
            ssh-policy-check: "disable"
            ssh-tun-policy-check: "disable"
            status: "disable"
            unsupported-version: "bypass"
        ssl:
            allow-invalid-server-cert: "enable"
            client-cert-request: "bypass"
            inspect-all: "disable"
            unsupported-ssl: "bypass"
            untrusted-cert: "allow"
        ssl-anomalies-log: "disable"
        ssl-exempt:
         -
            address: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
            address6: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
            fortiguard-category: "63"
            id:  "64"
            regex: "<your_own_value>"
            type: "fortiguard-category"
            wildcard-fqdn: "<your_own_value> (source firewall.wildcard-fqdn.custom.name firewall.wildcard-fqdn.group.name)"
        ssl-exemptions-log: "disable"
        ssl-server:
         -
            ftps-client-cert-request: "bypass"
            https-client-cert-request: "bypass"
            id:  "72"
            imaps-client-cert-request: "bypass"
            ip: "<your_own_value>"
            pop3s-client-cert-request: "bypass"
            smtps-client-cert-request: "bypass"
            ssl-other-client-cert-request: "bypass"
        untrusted-caname: "<your_own_value> (source vpn.certificate.local.name)"
        use-ssl-server: "disable"
        whitelist: "enable"
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


def filter_firewall_ssl_ssh_profile_data(json):
    option_list = ['caname', 'comment', 'ftps',
                   'https', 'imaps', 'mapi-over-https',
                   'name', 'pop3s', 'rpc-over-https',
                   'server-cert', 'server-cert-mode', 'smtps',
                   'ssh', 'ssl', 'ssl-anomalies-log',
                   'ssl-exempt', 'ssl-exemptions-log', 'ssl-server',
                   'untrusted-caname', 'use-ssl-server', 'whitelist']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_ssl_ssh_profile(data, fos):
    vdom = data['vdom']
    firewall_ssl_ssh_profile_data = data['firewall_ssl_ssh_profile']
    filtered_data = filter_firewall_ssl_ssh_profile_data(firewall_ssl_ssh_profile_data)
    if firewall_ssl_ssh_profile_data['state'] == "present":
        return fos.set('firewall',
                       'ssl-ssh-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_ssl_ssh_profile_data['state'] == "absent":
        return fos.delete('firewall',
                          'ssl-ssh-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_ssl_ssh_profile']
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
        "https": {"required": False, "type": "bool", "default": True},
        "firewall_ssl_ssh_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "caname": {"required": False, "type": "str"},
                "comment": {"required": False, "type": "str"},
                "ftps": {"required": False, "type": "dict",
                         "options": {
                             "allow-invalid-server-cert": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                             "client-cert-request": {"required": False, "type": "str",
                                                     "choices": ["bypass", "inspect", "block"]},
                             "ports": {"required": False, "type": "int"},
                             "status": {"required": False, "type": "str",
                                        "choices": ["disable", "deep-inspection"]},
                             "unsupported-ssl": {"required": False, "type": "str",
                                                 "choices": ["bypass", "inspect", "block"]},
                             "untrusted-cert": {"required": False, "type": "str",
                                                "choices": ["allow", "block", "ignore"]}
                         }},
                "https": {"required": False, "type": "dict",
                          "options": {
                              "allow-invalid-server-cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "client-cert-request": {"required": False, "type": "str",
                                                      "choices": ["bypass", "inspect", "block"]},
                              "ports": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["disable", "certificate-inspection", "deep-inspection"]},
                              "unsupported-ssl": {"required": False, "type": "str",
                                                  "choices": ["bypass", "inspect", "block"]},
                              "untrusted-cert": {"required": False, "type": "str",
                                                 "choices": ["allow", "block", "ignore"]}
                          }},
                "imaps": {"required": False, "type": "dict",
                          "options": {
                              "allow-invalid-server-cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "client-cert-request": {"required": False, "type": "str",
                                                      "choices": ["bypass", "inspect", "block"]},
                              "ports": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["disable", "deep-inspection"]},
                              "unsupported-ssl": {"required": False, "type": "str",
                                                  "choices": ["bypass", "inspect", "block"]},
                              "untrusted-cert": {"required": False, "type": "str",
                                                 "choices": ["allow", "block", "ignore"]}
                          }},
                "mapi-over-https": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "pop3s": {"required": False, "type": "dict",
                          "options": {
                              "allow-invalid-server-cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "client-cert-request": {"required": False, "type": "str",
                                                      "choices": ["bypass", "inspect", "block"]},
                              "ports": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["disable", "deep-inspection"]},
                              "unsupported-ssl": {"required": False, "type": "str",
                                                  "choices": ["bypass", "inspect", "block"]},
                              "untrusted-cert": {"required": False, "type": "str",
                                                 "choices": ["allow", "block", "ignore"]}
                          }},
                "rpc-over-https": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "server-cert": {"required": False, "type": "str"},
                "server-cert-mode": {"required": False, "type": "str",
                                     "choices": ["re-sign", "replace"]},
                "smtps": {"required": False, "type": "dict",
                          "options": {
                              "allow-invalid-server-cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "client-cert-request": {"required": False, "type": "str",
                                                      "choices": ["bypass", "inspect", "block"]},
                              "ports": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["disable", "deep-inspection"]},
                              "unsupported-ssl": {"required": False, "type": "str",
                                                  "choices": ["bypass", "inspect", "block"]},
                              "untrusted-cert": {"required": False, "type": "str",
                                                 "choices": ["allow", "block", "ignore"]}
                          }},
                "ssh": {"required": False, "type": "dict",
                        "options": {
                            "inspect-all": {"required": False, "type": "str",
                                            "choices": ["disable", "deep-inspection"]},
                            "ports": {"required": False, "type": "int"},
                            "ssh-algorithm": {"required": False, "type": "str",
                                              "choices": ["compatible", "high-encryption"]},
                            "ssh-policy-check": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                            "ssh-tun-policy-check": {"required": False, "type": "str",
                                                     "choices": ["disable", "enable"]},
                            "status": {"required": False, "type": "str",
                                       "choices": ["disable", "deep-inspection"]},
                            "unsupported-version": {"required": False, "type": "str",
                                                    "choices": ["bypass", "block"]}
                        }},
                "ssl": {"required": False, "type": "dict",
                        "options": {
                            "allow-invalid-server-cert": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                            "client-cert-request": {"required": False, "type": "str",
                                                    "choices": ["bypass", "inspect", "block"]},
                            "inspect-all": {"required": False, "type": "str",
                                            "choices": ["disable", "certificate-inspection", "deep-inspection"]},
                            "unsupported-ssl": {"required": False, "type": "str",
                                                "choices": ["bypass", "inspect", "block"]},
                            "untrusted-cert": {"required": False, "type": "str",
                                               "choices": ["allow", "block", "ignore"]}
                        }},
                "ssl-anomalies-log": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "ssl-exempt": {"required": False, "type": "list",
                               "options": {
                                   "address": {"required": False, "type": "str"},
                                   "address6": {"required": False, "type": "str"},
                                   "fortiguard-category": {"required": False, "type": "int"},
                                   "id": {"required": True, "type": "int"},
                                   "regex": {"required": False, "type": "str"},
                                   "type": {"required": False, "type": "str",
                                            "choices": ["fortiguard-category", "address", "address6",
                                                        "wildcard-fqdn", "regex"]},
                                   "wildcard-fqdn": {"required": False, "type": "str"}
                               }},
                "ssl-exemptions-log": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                "ssl-server": {"required": False, "type": "list",
                               "options": {
                                   "ftps-client-cert-request": {"required": False, "type": "str",
                                                                "choices": ["bypass", "inspect", "block"]},
                                   "https-client-cert-request": {"required": False, "type": "str",
                                                                 "choices": ["bypass", "inspect", "block"]},
                                   "id": {"required": True, "type": "int"},
                                   "imaps-client-cert-request": {"required": False, "type": "str",
                                                                 "choices": ["bypass", "inspect", "block"]},
                                   "ip": {"required": False, "type": "str"},
                                   "pop3s-client-cert-request": {"required": False, "type": "str",
                                                                 "choices": ["bypass", "inspect", "block"]},
                                   "smtps-client-cert-request": {"required": False, "type": "str",
                                                                 "choices": ["bypass", "inspect", "block"]},
                                   "ssl-other-client-cert-request": {"required": False, "type": "str",
                                                                     "choices": ["bypass", "inspect", "block"]}
                               }},
                "untrusted-caname": {"required": False, "type": "str"},
                "use-ssl-server": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "whitelist": {"required": False, "type": "str",
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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
