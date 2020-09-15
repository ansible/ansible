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
module: fortios_vpn_certificate_setting
short_description: VPN certificate setting in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify vpn_certificate feature and setting category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.9"
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
    vpn_certificate_setting:
        description:
            - VPN certificate setting.
        default: null
        type: dict
        suboptions:
            certname_dsa1024:
                description:
                    - 1024 bit DSA key certificate for re-signing server certificates for SSL inspection. Source vpn.certificate.local.name.
                type: str
            certname_dsa2048:
                description:
                    - 2048 bit DSA key certificate for re-signing server certificates for SSL inspection. Source vpn.certificate.local.name.
                type: str
            certname_ecdsa256:
                description:
                    - 256 bit ECDSA key certificate for re-signing server certificates for SSL inspection. Source vpn.certificate.local.name.
                type: str
            certname_ecdsa384:
                description:
                    - 384 bit ECDSA key certificate for re-signing server certificates for SSL inspection. Source vpn.certificate.local.name.
                type: str
            certname_rsa1024:
                description:
                    - 1024 bit RSA key certificate for re-signing server certificates for SSL inspection. Source vpn.certificate.local.name.
                type: str
            certname_rsa2048:
                description:
                    - 2048 bit RSA key certificate for re-signing server certificates for SSL inspection. Source vpn.certificate.local.name.
                type: str
            check_ca_cert:
                description:
                    - Enable/disable verification of the user certificate and pass authentication if any CA in the chain is trusted .
                type: str
                choices:
                    - enable
                    - disable
            check_ca_chain:
                description:
                    - Enable/disable verification of the entire certificate chain and pass authentication only if the chain is complete and all of the CAs in
                       the chain are trusted .
                type: str
                choices:
                    - enable
                    - disable
            cmp_save_extra_certs:
                description:
                    - Enable/disable saving extra certificates in CMP mode.
                type: str
                choices:
                    - enable
                    - disable
            cn_match:
                description:
                    - When searching for a matching certificate, control how to find matches in the cn attribute of the certificate subject name.
                type: str
                choices:
                    - substring
                    - value
            ocsp_default_server:
                description:
                    - Default OCSP server. Source vpn.certificate.ocsp-server.name.
                type: str
            ocsp_status:
                description:
                    - Enable/disable receiving certificates using the OCSP.
                type: str
                choices:
                    - enable
                    - disable
            ssl_min_proto_version:
                description:
                    - Minimum supported protocol version for SSL/TLS connections .
                type: str
                choices:
                    - default
                    - SSLv3
                    - TLSv1
                    - TLSv1-1
                    - TLSv1-2
            ssl_ocsp_option:
                description:
                    - Specify whether the OCSP URL is from the certificate or the default OCSP server.
                type: str
                choices:
                    - certificate
                    - server
            ssl_ocsp_status:
                description:
                    - Enable/disable SSL OCSP.
                type: str
                choices:
                    - enable
                    - disable
            strict_crl_check:
                description:
                    - Enable/disable strict mode CRL checking.
                type: str
                choices:
                    - enable
                    - disable
            strict_ocsp_check:
                description:
                    - Enable/disable strict mode OCSP checking.
                type: str
                choices:
                    - enable
                    - disable
            subject_match:
                description:
                    - When searching for a matching certificate, control how to find matches in the certificate subject name.
                type: str
                choices:
                    - substring
                    - value
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
  - name: VPN certificate setting.
    fortios_vpn_certificate_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      vpn_certificate_setting:
        certname_dsa1024: "<your_own_value> (source vpn.certificate.local.name)"
        certname_dsa2048: "<your_own_value> (source vpn.certificate.local.name)"
        certname_ecdsa256: "<your_own_value> (source vpn.certificate.local.name)"
        certname_ecdsa384: "<your_own_value> (source vpn.certificate.local.name)"
        certname_rsa1024: "<your_own_value> (source vpn.certificate.local.name)"
        certname_rsa2048: "<your_own_value> (source vpn.certificate.local.name)"
        check_ca_cert: "enable"
        check_ca_chain: "enable"
        cmp_save_extra_certs: "enable"
        cn_match: "substring"
        ocsp_default_server: "<your_own_value> (source vpn.certificate.ocsp-server.name)"
        ocsp_status: "enable"
        ssl_min_proto_version: "default"
        ssl_ocsp_option: "certificate"
        ssl_ocsp_status: "enable"
        strict_crl_check: "enable"
        strict_ocsp_check: "enable"
        subject_match: "substring"
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


def filter_vpn_certificate_setting_data(json):
    option_list = ['certname_dsa1024', 'certname_dsa2048', 'certname_ecdsa256',
                   'certname_ecdsa384', 'certname_rsa1024', 'certname_rsa2048',
                   'check_ca_cert', 'check_ca_chain', 'cmp_save_extra_certs',
                   'cn_match', 'ocsp_default_server', 'ocsp_status',
                   'ssl_min_proto_version', 'ssl_ocsp_option', 'ssl_ocsp_status',
                   'strict_crl_check', 'strict_ocsp_check', 'subject_match']
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


def vpn_certificate_setting(data, fos):
    vdom = data['vdom']
    vpn_certificate_setting_data = data['vpn_certificate_setting']
    filtered_data = underscore_to_hyphen(filter_vpn_certificate_setting_data(vpn_certificate_setting_data))

    return fos.set('vpn.certificate',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_vpn_certificate(data, fos):

    if data['vpn_certificate_setting']:
        resp = vpn_certificate_setting(data, fos)

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
        "vpn_certificate_setting": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "certname_dsa1024": {"required": False, "type": "str"},
                "certname_dsa2048": {"required": False, "type": "str"},
                "certname_ecdsa256": {"required": False, "type": "str"},
                "certname_ecdsa384": {"required": False, "type": "str"},
                "certname_rsa1024": {"required": False, "type": "str"},
                "certname_rsa2048": {"required": False, "type": "str"},
                "check_ca_cert": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "check_ca_chain": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "cmp_save_extra_certs": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "cn_match": {"required": False, "type": "str",
                             "choices": ["substring", "value"]},
                "ocsp_default_server": {"required": False, "type": "str"},
                "ocsp_status": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "ssl_min_proto_version": {"required": False, "type": "str",
                                          "choices": ["default", "SSLv3", "TLSv1",
                                                      "TLSv1-1", "TLSv1-2"]},
                "ssl_ocsp_option": {"required": False, "type": "str",
                                    "choices": ["certificate", "server"]},
                "ssl_ocsp_status": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "strict_crl_check": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "strict_ocsp_check": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "subject_match": {"required": False, "type": "str",
                                  "choices": ["substring", "value"]}

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

            is_error, has_changed, result = fortios_vpn_certificate(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_vpn_certificate(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
