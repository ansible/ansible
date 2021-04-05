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
module: fortios_vpn_certificate_crl
short_description: Certificate Revocation List as a PEM file in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify vpn_certificate feature and crl category.
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
    state:
        description:
            - Indicates whether to create or remove the object.
        type: str
        required: true
        choices:
            - present
            - absent
    vpn_certificate_crl:
        description:
            - Certificate Revocation List as a PEM file.
        default: null
        type: dict
        suboptions:
            crl:
                description:
                    - Certificate Revocation List as a PEM file.
                type: str
            http_url:
                description:
                    - HTTP server URL for CRL auto-update.
                type: str
            last_updated:
                description:
                    - Time at which CRL was last updated.
                type: int
            ldap_password:
                description:
                    - LDAP server user password.
                type: str
            ldap_server:
                description:
                    - LDAP server name for CRL auto-update.
                type: str
            ldap_username:
                description:
                    - LDAP server user name.
                type: str
            name:
                description:
                    - Name.
                required: true
                type: str
            range:
                description:
                    - Either global or VDOM IP address range for the certificate.
                type: str
                choices:
                    - global
                    - vdom
            scep_cert:
                description:
                    - Local certificate for SCEP communication for CRL auto-update. Source vpn.certificate.local.name.
                type: str
            scep_url:
                description:
                    - SCEP server URL for CRL auto-update.
                type: str
            source:
                description:
                    - Certificate source type.
                type: str
                choices:
                    - factory
                    - user
                    - bundle
            source_ip:
                description:
                    - Source IP address for communications to a HTTP or SCEP CA server.
                type: str
            update_interval:
                description:
                    - Time in seconds before the FortiGate checks for an updated CRL. Set to 0 to update only when it expires.
                type: int
            update_vdom:
                description:
                    - VDOM for CRL update. Source system.vdom.name.
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
  - name: Certificate Revocation List as a PEM file.
    fortios_vpn_certificate_crl:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      vpn_certificate_crl:
        crl: "<your_own_value>"
        http_url: "<your_own_value>"
        last_updated: "5"
        ldap_password: "<your_own_value>"
        ldap_server: "<your_own_value>"
        ldap_username: "<your_own_value>"
        name: "default_name_9"
        range: "global"
        scep_cert: "<your_own_value> (source vpn.certificate.local.name)"
        scep_url: "<your_own_value>"
        source: "factory"
        source_ip: "84.230.14.43"
        update_interval: "15"
        update_vdom: "<your_own_value> (source system.vdom.name)"
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


def filter_vpn_certificate_crl_data(json):
    option_list = ['crl', 'http_url', 'last_updated',
                   'ldap_password', 'ldap_server', 'ldap_username',
                   'name', 'range', 'scep_cert',
                   'scep_url', 'source', 'source_ip',
                   'update_interval', 'update_vdom']
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


def vpn_certificate_crl(data, fos):
    vdom = data['vdom']
    state = data['state']
    vpn_certificate_crl_data = data['vpn_certificate_crl']
    filtered_data = underscore_to_hyphen(filter_vpn_certificate_crl_data(vpn_certificate_crl_data))

    if state == "present":
        return fos.set('vpn.certificate',
                       'crl',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('vpn.certificate',
                          'crl',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_vpn_certificate(data, fos):

    if data['vpn_certificate_crl']:
        resp = vpn_certificate_crl(data, fos)

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
        "state": {"required": True, "type": "str",
                  "choices": ["present", "absent"]},
        "vpn_certificate_crl": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "crl": {"required": False, "type": "str"},
                "http_url": {"required": False, "type": "str"},
                "last_updated": {"required": False, "type": "int"},
                "ldap_password": {"required": False, "type": "str", "no_log": True},
                "ldap_server": {"required": False, "type": "str"},
                "ldap_username": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "range": {"required": False, "type": "str",
                          "choices": ["global", "vdom"]},
                "scep_cert": {"required": False, "type": "str"},
                "scep_url": {"required": False, "type": "str"},
                "source": {"required": False, "type": "str",
                           "choices": ["factory", "user", "bundle"]},
                "source_ip": {"required": False, "type": "str"},
                "update_interval": {"required": False, "type": "int"},
                "update_vdom": {"required": False, "type": "str"}

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
