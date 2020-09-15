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
module: fortios_firewall_ssl_server
short_description: Configure SSL servers in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and ssl_server category.
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
    firewall_ssl_server:
        description:
            - Configure SSL servers.
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
            add_header_x_forwarded_proto:
                description:
                    - Enable/disable adding an X-Forwarded-Proto header to forwarded requests.
                type: str
                choices:
                    - enable
                    - disable
            ip:
                description:
                    - IPv4 address of the SSL server.
                type: str
            mapped_port:
                description:
                    - Mapped server service port (1 - 65535).
                type: int
            name:
                description:
                    - Server name.
                required: true
                type: str
            port:
                description:
                    - Server service port (1 - 65535).
                type: int
            ssl_algorithm:
                description:
                    - Relative strength of encryption algorithms accepted in negotiation.
                type: str
                choices:
                    - high
                    - medium
                    - low
            ssl_cert:
                description:
                    - Name of certificate for SSL connections to this server. Source vpn.certificate.local.name.
                type: str
            ssl_client_renegotiation:
                description:
                    - Allow or block client renegotiation by server.
                type: str
                choices:
                    - allow
                    - deny
                    - secure
            ssl_dh_bits:
                description:
                    - Bit-size of Diffie-Hellman (DH) prime used in DHE-RSA negotiation.
                type: str
                choices:
                    - 768
                    - 1024
                    - 1536
                    - 2048
            ssl_max_version:
                description:
                    - Highest SSL/TLS version to negotiate.
                type: str
                choices:
                    - tls-1.0
                    - tls-1.1
                    - tls-1.2
            ssl_min_version:
                description:
                    - Lowest SSL/TLS version to negotiate.
                type: str
                choices:
                    - tls-1.0
                    - tls-1.1
                    - tls-1.2
            ssl_mode:
                description:
                    - SSL/TLS mode for encryption and decryption of traffic.
                type: str
                choices:
                    - half
                    - full
            ssl_send_empty_frags:
                description:
                    - Enable/disable sending empty fragments to avoid attack on CBC IV.
                type: str
                choices:
                    - enable
                    - disable
            url_rewrite:
                description:
                    - Enable/disable rewriting the URL.
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
  - name: Configure SSL servers.
    fortios_firewall_ssl_server:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_ssl_server:
        add_header_x_forwarded_proto: "enable"
        ip: "<your_own_value>"
        mapped_port: "5"
        name: "default_name_6"
        port: "7"
        ssl_algorithm: "high"
        ssl_cert: "<your_own_value> (source vpn.certificate.local.name)"
        ssl_client_renegotiation: "allow"
        ssl_dh_bits: "768"
        ssl_max_version: "tls-1.0"
        ssl_min_version: "tls-1.0"
        ssl_mode: "half"
        ssl_send_empty_frags: "enable"
        url_rewrite: "enable"
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


def filter_firewall_ssl_server_data(json):
    option_list = ['add_header_x_forwarded_proto', 'ip', 'mapped_port',
                   'name', 'port', 'ssl_algorithm',
                   'ssl_cert', 'ssl_client_renegotiation', 'ssl_dh_bits',
                   'ssl_max_version', 'ssl_min_version', 'ssl_mode',
                   'ssl_send_empty_frags', 'url_rewrite']
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


def firewall_ssl_server(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_ssl_server'] and data['firewall_ssl_server']:
        state = data['firewall_ssl_server']['state']
    else:
        state = True
    firewall_ssl_server_data = data['firewall_ssl_server']
    filtered_data = underscore_to_hyphen(filter_firewall_ssl_server_data(firewall_ssl_server_data))

    if state == "present":
        return fos.set('firewall',
                       'ssl-server',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'ssl-server',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_ssl_server']:
        resp = firewall_ssl_server(data, fos)

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
        "firewall_ssl_server": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "add_header_x_forwarded_proto": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "ip": {"required": False, "type": "str"},
                "mapped_port": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "port": {"required": False, "type": "int"},
                "ssl_algorithm": {"required": False, "type": "str",
                                  "choices": ["high", "medium", "low"]},
                "ssl_cert": {"required": False, "type": "str"},
                "ssl_client_renegotiation": {"required": False, "type": "str",
                                             "choices": ["allow", "deny", "secure"]},
                "ssl_dh_bits": {"required": False, "type": "str",
                                "choices": ["768", "1024", "1536",
                                            "2048"]},
                "ssl_max_version": {"required": False, "type": "str",
                                    "choices": ["tls-1.0", "tls-1.1", "tls-1.2"]},
                "ssl_min_version": {"required": False, "type": "str",
                                    "choices": ["tls-1.0", "tls-1.1", "tls-1.2"]},
                "ssl_mode": {"required": False, "type": "str",
                             "choices": ["half", "full"]},
                "ssl_send_empty_frags": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "url_rewrite": {"required": False, "type": "str",
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
