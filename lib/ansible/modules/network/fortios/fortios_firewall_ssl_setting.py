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
module: fortios_firewall_ssl_setting
short_description: SSL proxy settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall_ssl feature and setting category.
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
    firewall_ssl_setting:
        description:
            - SSL proxy settings.
        default: null
        suboptions:
            abbreviate-handshake:
                description:
                    - Enable/disable use of SSL abbreviated handshake.
                choices:
                    - enable
                    - disable
            cert-cache-capacity:
                description:
                    - Maximum capacity of the host certificate cache (0 - 500, default = 200).
            cert-cache-timeout:
                description:
                    - Time limit to keep certificate cache (1 - 120 min, default = 10).
            kxp-queue-threshold:
                description:
                    - Maximum length of the CP KXP queue. When the queue becomes full, the proxy switches cipher functions to the main CPU (0 - 512, default =
                       16).
            no-matching-cipher-action:
                description:
                    - Bypass or drop the connection when no matching cipher is found.
                choices:
                    - bypass
                    - drop
            proxy-connect-timeout:
                description:
                    - Time limit to make an internal connection to the appropriate proxy process (1 - 60 sec, default = 30).
            session-cache-capacity:
                description:
                    - Capacity of the SSL session cache (--Obsolete--) (1 - 1000, default = 500).
            session-cache-timeout:
                description:
                    - Time limit to keep SSL session state (1 - 60 min, default = 20).
            ssl-dh-bits:
                description:
                    - Bit-size of Diffie-Hellman (DH) prime used in DHE-RSA negotiation (default = 2048).
                choices:
                    - 768
                    - 1024
                    - 1536
                    - 2048
            ssl-queue-threshold:
                description:
                    - Maximum length of the CP SSL queue. When the queue becomes full, the proxy switches cipher functions to the main CPU (0 - 512, default =
                       32).
            ssl-send-empty-frags:
                description:
                    - Enable/disable sending empty fragments to avoid attack on CBC IV (for SSL 3.0 and TLS 1.0 only).
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
  - name: SSL proxy settings.
    fortios_firewall_ssl_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_ssl_setting:
        abbreviate-handshake: "enable"
        cert-cache-capacity: "4"
        cert-cache-timeout: "5"
        kxp-queue-threshold: "6"
        no-matching-cipher-action: "bypass"
        proxy-connect-timeout: "8"
        session-cache-capacity: "9"
        session-cache-timeout: "10"
        ssl-dh-bits: "768"
        ssl-queue-threshold: "12"
        ssl-send-empty-frags: "enable"
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


def filter_firewall_ssl_setting_data(json):
    option_list = ['abbreviate-handshake', 'cert-cache-capacity', 'cert-cache-timeout',
                   'kxp-queue-threshold', 'no-matching-cipher-action', 'proxy-connect-timeout',
                   'session-cache-capacity', 'session-cache-timeout', 'ssl-dh-bits',
                   'ssl-queue-threshold', 'ssl-send-empty-frags']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_ssl_setting(data, fos):
    vdom = data['vdom']
    firewall_ssl_setting_data = data['firewall_ssl_setting']
    filtered_data = filter_firewall_ssl_setting_data(firewall_ssl_setting_data)
    return fos.set('firewall.ssl',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def fortios_firewall_ssl(data, fos):
    login(data)

    methodlist = ['firewall_ssl_setting']
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
        "firewall_ssl_setting": {
            "required": False, "type": "dict",
            "options": {
                "abbreviate-handshake": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "cert-cache-capacity": {"required": False, "type": "int"},
                "cert-cache-timeout": {"required": False, "type": "int"},
                "kxp-queue-threshold": {"required": False, "type": "int"},
                "no-matching-cipher-action": {"required": False, "type": "str",
                                              "choices": ["bypass", "drop"]},
                "proxy-connect-timeout": {"required": False, "type": "int"},
                "session-cache-capacity": {"required": False, "type": "int"},
                "session-cache-timeout": {"required": False, "type": "int"},
                "ssl-dh-bits": {"required": False, "type": "str",
                                "choices": ["768", "1024", "1536",
                                            "2048"]},
                "ssl-queue-threshold": {"required": False, "type": "int"},
                "ssl-send-empty-frags": {"required": False, "type": "str",
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

    is_error, has_changed, result = fortios_firewall_ssl(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
