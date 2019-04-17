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
module: fortios_firewall_ssl_server
short_description: Configure SSL servers in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and ssl_server category.
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
    firewall_ssl_server:
        description:
            - Configure SSL servers.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            add-header-x-forwarded-proto:
                description:
                    - Enable/disable adding an X-Forwarded-Proto header to forwarded requests.
                choices:
                    - enable
                    - disable
            ip:
                description:
                    - IPv4 address of the SSL server.
            mapped-port:
                description:
                    - Mapped server service port (1 - 65535, default = 80).
            name:
                description:
                    - Server name.
                required: true
            port:
                description:
                    - Server service port (1 - 65535, default = 443).
            ssl-algorithm:
                description:
                    - Relative strength of encryption algorithms accepted in negotiation.
                choices:
                    - high
                    - medium
                    - low
            ssl-cert:
                description:
                    - Name of certificate for SSL connections to this server (default = "Fortinet_CA_SSL"). Source vpn.certificate.local.name.
            ssl-client-renegotiation:
                description:
                    - Allow or block client renegotiation by server.
                choices:
                    - allow
                    - deny
                    - secure
            ssl-dh-bits:
                description:
                    - Bit-size of Diffie-Hellman (DH) prime used in DHE-RSA negotiation (default = 2048).
                choices:
                    - 768
                    - 1024
                    - 1536
                    - 2048
            ssl-max-version:
                description:
                    - Highest SSL/TLS version to negotiate.
                choices:
                    - tls-1.0
                    - tls-1.1
                    - tls-1.2
            ssl-min-version:
                description:
                    - Lowest SSL/TLS version to negotiate.
                choices:
                    - tls-1.0
                    - tls-1.1
                    - tls-1.2
            ssl-mode:
                description:
                    - SSL/TLS mode for encryption and decryption of traffic.
                choices:
                    - half
                    - full
            ssl-send-empty-frags:
                description:
                    - Enable/disable sending empty fragments to avoid attack on CBC IV.
                choices:
                    - enable
                    - disable
            url-rewrite:
                description:
                    - Enable/disable rewriting the URL.
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
  - name: Configure SSL servers.
    fortios_firewall_ssl_server:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_ssl_server:
        state: "present"
        add-header-x-forwarded-proto: "enable"
        ip: "<your_own_value>"
        mapped-port: "5"
        name: "default_name_6"
        port: "7"
        ssl-algorithm: "high"
        ssl-cert: "<your_own_value> (source vpn.certificate.local.name)"
        ssl-client-renegotiation: "allow"
        ssl-dh-bits: "768"
        ssl-max-version: "tls-1.0"
        ssl-min-version: "tls-1.0"
        ssl-mode: "half"
        ssl-send-empty-frags: "enable"
        url-rewrite: "enable"
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


def filter_firewall_ssl_server_data(json):
    option_list = ['add-header-x-forwarded-proto', 'ip', 'mapped-port',
                   'name', 'port', 'ssl-algorithm',
                   'ssl-cert', 'ssl-client-renegotiation', 'ssl-dh-bits',
                   'ssl-max-version', 'ssl-min-version', 'ssl-mode',
                   'ssl-send-empty-frags', 'url-rewrite']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_ssl_server(data, fos):
    vdom = data['vdom']
    firewall_ssl_server_data = data['firewall_ssl_server']
    filtered_data = filter_firewall_ssl_server_data(firewall_ssl_server_data)
    if firewall_ssl_server_data['state'] == "present":
        return fos.set('firewall',
                       'ssl-server',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_ssl_server_data['state'] == "absent":
        return fos.delete('firewall',
                          'ssl-server',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_ssl_server']
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
        "firewall_ssl_server": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "add-header-x-forwarded-proto": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "ip": {"required": False, "type": "str"},
                "mapped-port": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "port": {"required": False, "type": "int"},
                "ssl-algorithm": {"required": False, "type": "str",
                                  "choices": ["high", "medium", "low"]},
                "ssl-cert": {"required": False, "type": "str"},
                "ssl-client-renegotiation": {"required": False, "type": "str",
                                             "choices": ["allow", "deny", "secure"]},
                "ssl-dh-bits": {"required": False, "type": "str",
                                "choices": ["768", "1024", "1536",
                                            "2048"]},
                "ssl-max-version": {"required": False, "type": "str",
                                    "choices": ["tls-1.0", "tls-1.1", "tls-1.2"]},
                "ssl-min-version": {"required": False, "type": "str",
                                    "choices": ["tls-1.0", "tls-1.1", "tls-1.2"]},
                "ssl-mode": {"required": False, "type": "str",
                             "choices": ["half", "full"]},
                "ssl-send-empty-frags": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "url-rewrite": {"required": False, "type": "str",
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
