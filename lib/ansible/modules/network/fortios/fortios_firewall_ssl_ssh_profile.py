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
module: fortios_firewall_ssl_ssh_profile
short_description: Configure SSL/SSH protocol options in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and ssl_ssh_profile category.
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
    firewall_ssl_ssh_profile:
        description:
            - Configure SSL/SSH protocol options.
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
            caname:
                description:
                    - CA certificate used by SSL Inspection. Source vpn.certificate.local.name.
                type: str
            comment:
                description:
                    - Optional comments.
                type: str
            ftps:
                description:
                    - Configure FTPS options.
                type: dict
                suboptions:
                    allow_invalid_server_cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        type: str
                        choices:
                            - enable
                            - disable
                    client_cert_request:
                        description:
                            - Action based on client certificate request.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535).
                        type: int
                    status:
                        description:
                            - Configure protocol inspection status.
                        type: str
                        choices:
                            - disable
                            - deep-inspection
                    unsupported_ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted_cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        type: str
                        choices:
                            - allow
                            - block
                            - ignore
            https:
                description:
                    - Configure HTTPS options.
                type: dict
                suboptions:
                    allow_invalid_server_cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        type: str
                        choices:
                            - enable
                            - disable
                    client_cert_request:
                        description:
                            - Action based on client certificate request.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535).
                        type: int
                    status:
                        description:
                            - Configure protocol inspection status.
                        type: str
                        choices:
                            - disable
                            - certificate-inspection
                            - deep-inspection
                    unsupported_ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted_cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        type: str
                        choices:
                            - allow
                            - block
                            - ignore
            imaps:
                description:
                    - Configure IMAPS options.
                type: dict
                suboptions:
                    allow_invalid_server_cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        type: str
                        choices:
                            - enable
                            - disable
                    client_cert_request:
                        description:
                            - Action based on client certificate request.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535).
                        type: int
                    status:
                        description:
                            - Configure protocol inspection status.
                        type: str
                        choices:
                            - disable
                            - deep-inspection
                    unsupported_ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted_cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        type: str
                        choices:
                            - allow
                            - block
                            - ignore
            mapi_over_https:
                description:
                    - Enable/disable inspection of MAPI over HTTPS.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name.
                required: true
                type: str
            pop3s:
                description:
                    - Configure POP3S options.
                type: dict
                suboptions:
                    allow_invalid_server_cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        type: str
                        choices:
                            - enable
                            - disable
                    client_cert_request:
                        description:
                            - Action based on client certificate request.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535).
                        type: int
                    status:
                        description:
                            - Configure protocol inspection status.
                        type: str
                        choices:
                            - disable
                            - deep-inspection
                    unsupported_ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted_cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        type: str
                        choices:
                            - allow
                            - block
                            - ignore
            rpc_over_https:
                description:
                    - Enable/disable inspection of RPC over HTTPS.
                type: str
                choices:
                    - enable
                    - disable
            server_cert:
                description:
                    - Certificate used by SSL Inspection to replace server certificate. Source vpn.certificate.local.name.
                type: str
            server_cert_mode:
                description:
                    - Re-sign or replace the server's certificate.
                type: str
                choices:
                    - re-sign
                    - replace
            smtps:
                description:
                    - Configure SMTPS options.
                type: dict
                suboptions:
                    allow_invalid_server_cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        type: str
                        choices:
                            - enable
                            - disable
                    client_cert_request:
                        description:
                            - Action based on client certificate request.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535).
                        type: int
                    status:
                        description:
                            - Configure protocol inspection status.
                        type: str
                        choices:
                            - disable
                            - deep-inspection
                    unsupported_ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted_cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        type: str
                        choices:
                            - allow
                            - block
                            - ignore
            ssh:
                description:
                    - Configure SSH options.
                type: dict
                suboptions:
                    inspect_all:
                        description:
                            - Level of SSL inspection.
                        type: str
                        choices:
                            - disable
                            - deep-inspection
                    ports:
                        description:
                            - Ports to use for scanning (1 - 65535).
                        type: int
                    ssh_algorithm:
                        description:
                            - Relative strength of encryption algorithms accepted during negotiation.
                        type: str
                        choices:
                            - compatible
                            - high-encryption
                    ssh_policy_check:
                        description:
                            - Enable/disable SSH policy check.
                        type: str
                        choices:
                            - disable
                            - enable
                    ssh_tun_policy_check:
                        description:
                            - Enable/disable SSH tunnel policy check.
                        type: str
                        choices:
                            - disable
                            - enable
                    status:
                        description:
                            - Configure protocol inspection status.
                        type: str
                        choices:
                            - disable
                            - deep-inspection
                    unsupported_version:
                        description:
                            - Action based on SSH version being unsupported.
                        type: str
                        choices:
                            - bypass
                            - block
            ssl:
                description:
                    - Configure SSL options.
                type: dict
                suboptions:
                    allow_invalid_server_cert:
                        description:
                            - When enabled, allows SSL sessions whose server certificate validation failed.
                        type: str
                        choices:
                            - enable
                            - disable
                    client_cert_request:
                        description:
                            - Action based on client certificate request.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    inspect_all:
                        description:
                            - Level of SSL inspection.
                        type: str
                        choices:
                            - disable
                            - certificate-inspection
                            - deep-inspection
                    unsupported_ssl:
                        description:
                            - Action based on the SSL encryption used being unsupported.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    untrusted_cert:
                        description:
                            - Allow, ignore, or block the untrusted SSL session server certificate.
                        type: str
                        choices:
                            - allow
                            - block
                            - ignore
            ssl_anomalies_log:
                description:
                    - Enable/disable logging SSL anomalies.
                type: str
                choices:
                    - disable
                    - enable
            ssl_exempt:
                description:
                    - Servers to exempt from SSL inspection.
                type: list
                suboptions:
                    address:
                        description:
                            - IPv4 address object. Source firewall.address.name firewall.addrgrp.name.
                        type: str
                    address6:
                        description:
                            - IPv6 address object. Source firewall.address6.name firewall.addrgrp6.name.
                        type: str
                    fortiguard_category:
                        description:
                            - FortiGuard category ID.
                        type: int
                    id:
                        description:
                            - ID number.
                        required: true
                        type: int
                    regex:
                        description:
                            - Exempt servers by regular expression.
                        type: str
                    type:
                        description:
                            - Type of address object (IPv4 or IPv6) or FortiGuard category.
                        type: str
                        choices:
                            - fortiguard-category
                            - address
                            - address6
                            - wildcard-fqdn
                            - regex
                    wildcard_fqdn:
                        description:
                            - Exempt servers by wildcard FQDN. Source firewall.wildcard-fqdn.custom.name firewall.wildcard-fqdn.group.name.
                        type: str
            ssl_exemptions_log:
                description:
                    - Enable/disable logging SSL exemptions.
                type: str
                choices:
                    - disable
                    - enable
            ssl_server:
                description:
                    - SSL servers.
                type: list
                suboptions:
                    ftps_client_cert_request:
                        description:
                            - Action based on client certificate request during the FTPS handshake.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    https_client_cert_request:
                        description:
                            - Action based on client certificate request during the HTTPS handshake.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    id:
                        description:
                            - SSL server ID.
                        required: true
                        type: int
                    imaps_client_cert_request:
                        description:
                            - Action based on client certificate request during the IMAPS handshake.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    ip:
                        description:
                            - IPv4 address of the SSL server.
                        type: str
                    pop3s_client_cert_request:
                        description:
                            - Action based on client certificate request during the POP3S handshake.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    smtps_client_cert_request:
                        description:
                            - Action based on client certificate request during the SMTPS handshake.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
                    ssl_other_client_cert_request:
                        description:
                            - Action based on client certificate request during an SSL protocol handshake.
                        type: str
                        choices:
                            - bypass
                            - inspect
                            - block
            untrusted_caname:
                description:
                    - Untrusted CA certificate used by SSL Inspection. Source vpn.certificate.local.name.
                type: str
            use_ssl_server:
                description:
                    - Enable/disable the use of SSL server table for SSL offloading.
                type: str
                choices:
                    - disable
                    - enable
            whitelist:
                description:
                    - Enable/disable exempting servers by FortiGuard whitelist.
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
  - name: Configure SSL/SSH protocol options.
    fortios_firewall_ssl_ssh_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_ssl_ssh_profile:
        caname: "<your_own_value> (source vpn.certificate.local.name)"
        comment: "Optional comments."
        ftps:
            allow_invalid_server_cert: "enable"
            client_cert_request: "bypass"
            ports: "8"
            status: "disable"
            unsupported_ssl: "bypass"
            untrusted_cert: "allow"
        https:
            allow_invalid_server_cert: "enable"
            client_cert_request: "bypass"
            ports: "15"
            status: "disable"
            unsupported_ssl: "bypass"
            untrusted_cert: "allow"
        imaps:
            allow_invalid_server_cert: "enable"
            client_cert_request: "bypass"
            ports: "22"
            status: "disable"
            unsupported_ssl: "bypass"
            untrusted_cert: "allow"
        mapi_over_https: "enable"
        name: "default_name_27"
        pop3s:
            allow_invalid_server_cert: "enable"
            client_cert_request: "bypass"
            ports: "31"
            status: "disable"
            unsupported_ssl: "bypass"
            untrusted_cert: "allow"
        rpc_over_https: "enable"
        server_cert: "<your_own_value> (source vpn.certificate.local.name)"
        server_cert_mode: "re-sign"
        smtps:
            allow_invalid_server_cert: "enable"
            client_cert_request: "bypass"
            ports: "41"
            status: "disable"
            unsupported_ssl: "bypass"
            untrusted_cert: "allow"
        ssh:
            inspect_all: "disable"
            ports: "47"
            ssh_algorithm: "compatible"
            ssh_policy_check: "disable"
            ssh_tun_policy_check: "disable"
            status: "disable"
            unsupported_version: "bypass"
        ssl:
            allow_invalid_server_cert: "enable"
            client_cert_request: "bypass"
            inspect_all: "disable"
            unsupported_ssl: "bypass"
            untrusted_cert: "allow"
        ssl_anomalies_log: "disable"
        ssl_exempt:
         -
            address: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
            address6: "<your_own_value> (source firewall.address6.name firewall.addrgrp6.name)"
            fortiguard_category: "63"
            id:  "64"
            regex: "<your_own_value>"
            type: "fortiguard-category"
            wildcard_fqdn: "<your_own_value> (source firewall.wildcard-fqdn.custom.name firewall.wildcard-fqdn.group.name)"
        ssl_exemptions_log: "disable"
        ssl_server:
         -
            ftps_client_cert_request: "bypass"
            https_client_cert_request: "bypass"
            id:  "72"
            imaps_client_cert_request: "bypass"
            ip: "<your_own_value>"
            pop3s_client_cert_request: "bypass"
            smtps_client_cert_request: "bypass"
            ssl_other_client_cert_request: "bypass"
        untrusted_caname: "<your_own_value> (source vpn.certificate.local.name)"
        use_ssl_server: "disable"
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


def filter_firewall_ssl_ssh_profile_data(json):
    option_list = ['caname', 'comment', 'ftps',
                   'https', 'imaps', 'mapi_over_https',
                   'name', 'pop3s', 'rpc_over_https',
                   'server_cert', 'server_cert_mode', 'smtps',
                   'ssh', 'ssl', 'ssl_anomalies_log',
                   'ssl_exempt', 'ssl_exemptions_log', 'ssl_server',
                   'untrusted_caname', 'use_ssl_server', 'whitelist']
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


def firewall_ssl_ssh_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_ssl_ssh_profile'] and data['firewall_ssl_ssh_profile']:
        state = data['firewall_ssl_ssh_profile']['state']
    else:
        state = True
    firewall_ssl_ssh_profile_data = data['firewall_ssl_ssh_profile']
    filtered_data = underscore_to_hyphen(filter_firewall_ssl_ssh_profile_data(firewall_ssl_ssh_profile_data))

    if state == "present":
        return fos.set('firewall',
                       'ssl-ssh-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'ssl-ssh-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_ssl_ssh_profile']:
        resp = firewall_ssl_ssh_profile(data, fos)

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
        "firewall_ssl_ssh_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "caname": {"required": False, "type": "str"},
                "comment": {"required": False, "type": "str"},
                "ftps": {"required": False, "type": "dict",
                         "options": {
                             "allow_invalid_server_cert": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                             "client_cert_request": {"required": False, "type": "str",
                                                     "choices": ["bypass", "inspect", "block"]},
                             "ports": {"required": False, "type": "int"},
                             "status": {"required": False, "type": "str",
                                        "choices": ["disable", "deep-inspection"]},
                             "unsupported_ssl": {"required": False, "type": "str",
                                                 "choices": ["bypass", "inspect", "block"]},
                             "untrusted_cert": {"required": False, "type": "str",
                                                "choices": ["allow", "block", "ignore"]}
                         }},
                "https": {"required": False, "type": "dict",
                          "options": {
                              "allow_invalid_server_cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "client_cert_request": {"required": False, "type": "str",
                                                      "choices": ["bypass", "inspect", "block"]},
                              "ports": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["disable", "certificate-inspection", "deep-inspection"]},
                              "unsupported_ssl": {"required": False, "type": "str",
                                                  "choices": ["bypass", "inspect", "block"]},
                              "untrusted_cert": {"required": False, "type": "str",
                                                 "choices": ["allow", "block", "ignore"]}
                          }},
                "imaps": {"required": False, "type": "dict",
                          "options": {
                              "allow_invalid_server_cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "client_cert_request": {"required": False, "type": "str",
                                                      "choices": ["bypass", "inspect", "block"]},
                              "ports": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["disable", "deep-inspection"]},
                              "unsupported_ssl": {"required": False, "type": "str",
                                                  "choices": ["bypass", "inspect", "block"]},
                              "untrusted_cert": {"required": False, "type": "str",
                                                 "choices": ["allow", "block", "ignore"]}
                          }},
                "mapi_over_https": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "pop3s": {"required": False, "type": "dict",
                          "options": {
                              "allow_invalid_server_cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "client_cert_request": {"required": False, "type": "str",
                                                      "choices": ["bypass", "inspect", "block"]},
                              "ports": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["disable", "deep-inspection"]},
                              "unsupported_ssl": {"required": False, "type": "str",
                                                  "choices": ["bypass", "inspect", "block"]},
                              "untrusted_cert": {"required": False, "type": "str",
                                                 "choices": ["allow", "block", "ignore"]}
                          }},
                "rpc_over_https": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "server_cert": {"required": False, "type": "str"},
                "server_cert_mode": {"required": False, "type": "str",
                                     "choices": ["re-sign", "replace"]},
                "smtps": {"required": False, "type": "dict",
                          "options": {
                              "allow_invalid_server_cert": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "client_cert_request": {"required": False, "type": "str",
                                                      "choices": ["bypass", "inspect", "block"]},
                              "ports": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["disable", "deep-inspection"]},
                              "unsupported_ssl": {"required": False, "type": "str",
                                                  "choices": ["bypass", "inspect", "block"]},
                              "untrusted_cert": {"required": False, "type": "str",
                                                 "choices": ["allow", "block", "ignore"]}
                          }},
                "ssh": {"required": False, "type": "dict",
                        "options": {
                            "inspect_all": {"required": False, "type": "str",
                                            "choices": ["disable", "deep-inspection"]},
                            "ports": {"required": False, "type": "int"},
                            "ssh_algorithm": {"required": False, "type": "str",
                                              "choices": ["compatible", "high-encryption"]},
                            "ssh_policy_check": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                            "ssh_tun_policy_check": {"required": False, "type": "str",
                                                     "choices": ["disable", "enable"]},
                            "status": {"required": False, "type": "str",
                                       "choices": ["disable", "deep-inspection"]},
                            "unsupported_version": {"required": False, "type": "str",
                                                    "choices": ["bypass", "block"]}
                        }},
                "ssl": {"required": False, "type": "dict",
                        "options": {
                            "allow_invalid_server_cert": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                            "client_cert_request": {"required": False, "type": "str",
                                                    "choices": ["bypass", "inspect", "block"]},
                            "inspect_all": {"required": False, "type": "str",
                                            "choices": ["disable", "certificate-inspection", "deep-inspection"]},
                            "unsupported_ssl": {"required": False, "type": "str",
                                                "choices": ["bypass", "inspect", "block"]},
                            "untrusted_cert": {"required": False, "type": "str",
                                               "choices": ["allow", "block", "ignore"]}
                        }},
                "ssl_anomalies_log": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "ssl_exempt": {"required": False, "type": "list",
                               "options": {
                                   "address": {"required": False, "type": "str"},
                                   "address6": {"required": False, "type": "str"},
                                   "fortiguard_category": {"required": False, "type": "int"},
                                   "id": {"required": True, "type": "int"},
                                   "regex": {"required": False, "type": "str"},
                                   "type": {"required": False, "type": "str",
                                            "choices": ["fortiguard-category", "address", "address6",
                                                        "wildcard-fqdn", "regex"]},
                                   "wildcard_fqdn": {"required": False, "type": "str"}
                               }},
                "ssl_exemptions_log": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                "ssl_server": {"required": False, "type": "list",
                               "options": {
                                   "ftps_client_cert_request": {"required": False, "type": "str",
                                                                "choices": ["bypass", "inspect", "block"]},
                                   "https_client_cert_request": {"required": False, "type": "str",
                                                                 "choices": ["bypass", "inspect", "block"]},
                                   "id": {"required": True, "type": "int"},
                                   "imaps_client_cert_request": {"required": False, "type": "str",
                                                                 "choices": ["bypass", "inspect", "block"]},
                                   "ip": {"required": False, "type": "str"},
                                   "pop3s_client_cert_request": {"required": False, "type": "str",
                                                                 "choices": ["bypass", "inspect", "block"]},
                                   "smtps_client_cert_request": {"required": False, "type": "str",
                                                                 "choices": ["bypass", "inspect", "block"]},
                                   "ssl_other_client_cert_request": {"required": False, "type": "str",
                                                                     "choices": ["bypass", "inspect", "block"]}
                               }},
                "untrusted_caname": {"required": False, "type": "str"},
                "use_ssl_server": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "whitelist": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_firewall(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_firewall(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
