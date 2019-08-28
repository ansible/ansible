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
module: fortios_system_ddns
short_description: Configure DDNS in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and ddns category.
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
    system_ddns:
        description:
            - Configure DDNS.
        default: null
        type: dict
        suboptions:
            bound_ip:
                description:
                    - Bound IP address.
                type: str
            clear_text:
                description:
                    - Enable/disable use of clear text connections.
                type: str
                choices:
                    - disable
                    - enable
            ddns_auth:
                description:
                    - Enable/disable TSIG authentication for your DDNS server.
                type: str
                choices:
                    - disable
                    - tsig
            ddns_domain:
                description:
                    - Your fully qualified domain name (for example, yourname.DDNS.com).
                type: str
            ddns_key:
                description:
                    - DDNS update key (base 64 encoding).
                type: str
            ddns_keyname:
                description:
                    - DDNS update key name.
                type: str
            ddns_password:
                description:
                    - DDNS password.
                type: str
            ddns_server:
                description:
                    - Select a DDNS service provider.
                type: str
                choices:
                    - dyndns.org
                    - dyns.net
                    - tzo.com
                    - vavic.com
                    - dipdns.net
                    - now.net.cn
                    - dhs.org
                    - easydns.com
                    - genericDDNS
                    - FortiGuardDDNS
                    - noip.com
            ddns_server_ip:
                description:
                    - Generic DDNS server IP.
                type: str
            ddns_sn:
                description:
                    - DDNS Serial Number.
                type: str
            ddns_ttl:
                description:
                    - Time-to-live for DDNS packets.
                type: int
            ddns_username:
                description:
                    - DDNS user name.
                type: str
            ddns_zone:
                description:
                    - Zone of your domain name (for example, DDNS.com).
                type: str
            ddnsid:
                description:
                    - DDNS ID.
                required: true
                type: int
            monitor_interface:
                description:
                    - Monitored interface.
                type: list
                suboptions:
                    interface_name:
                        description:
                            - Interface name. Source system.interface.name.
                        type: str
            ssl_certificate:
                description:
                    - Name of local certificate for SSL connections. Source certificate.local.name.
                type: str
            update_interval:
                description:
                    - DDNS update interval (60 - 2592000 sec).
                type: int
            use_public_ip:
                description:
                    - Enable/disable use of public IP address.
                type: str
                choices:
                    - disable
                    - enable
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
  - name: Configure DDNS.
    fortios_system_ddns:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_ddns:
        bound_ip: "<your_own_value>"
        clear_text: "disable"
        ddns_auth: "disable"
        ddns_domain: "<your_own_value>"
        ddns_key: "<your_own_value>"
        ddns_keyname: "<your_own_value>"
        ddns_password: "<your_own_value>"
        ddns_server: "dyndns.org"
        ddns_server_ip: "<your_own_value>"
        ddns_sn: "<your_own_value>"
        ddns_ttl: "13"
        ddns_username: "<your_own_value>"
        ddns_zone: "<your_own_value>"
        ddnsid: "16"
        monitor_interface:
         -
            interface_name: "<your_own_value> (source system.interface.name)"
        ssl_certificate: "<your_own_value> (source certificate.local.name)"
        update_interval: "20"
        use_public_ip: "disable"
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


def filter_system_ddns_data(json):
    option_list = ['bound_ip', 'clear_text', 'ddns_auth',
                   'ddns_domain', 'ddns_key', 'ddns_keyname',
                   'ddns_password', 'ddns_server', 'ddns_server_ip',
                   'ddns_sn', 'ddns_ttl', 'ddns_username',
                   'ddns_zone', 'ddnsid', 'monitor_interface',
                   'ssl_certificate', 'update_interval', 'use_public_ip']
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


def system_ddns(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_ddns_data = data['system_ddns']
    filtered_data = underscore_to_hyphen(filter_system_ddns_data(system_ddns_data))

    if state == "present":
        return fos.set('system',
                       'ddns',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'ddns',
                          mkey=filtered_data['ddnsid'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_ddns']:
        resp = system_ddns(data, fos)

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
        "system_ddns": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "bound_ip": {"required": False, "type": "str"},
                "clear_text": {"required": False, "type": "str",
                               "choices": ["disable", "enable"]},
                "ddns_auth": {"required": False, "type": "str",
                              "choices": ["disable", "tsig"]},
                "ddns_domain": {"required": False, "type": "str"},
                "ddns_key": {"required": False, "type": "str"},
                "ddns_keyname": {"required": False, "type": "str"},
                "ddns_password": {"required": False, "type": "str"},
                "ddns_server": {"required": False, "type": "str",
                                "choices": ["dyndns.org", "dyns.net", "tzo.com",
                                            "vavic.com", "dipdns.net", "now.net.cn",
                                            "dhs.org", "easydns.com", "genericDDNS",
                                            "FortiGuardDDNS", "noip.com"]},
                "ddns_server_ip": {"required": False, "type": "str"},
                "ddns_sn": {"required": False, "type": "str"},
                "ddns_ttl": {"required": False, "type": "int"},
                "ddns_username": {"required": False, "type": "str"},
                "ddns_zone": {"required": False, "type": "str"},
                "ddnsid": {"required": True, "type": "int"},
                "monitor_interface": {"required": False, "type": "list",
                                      "options": {
                                          "interface_name": {"required": False, "type": "str"}
                                      }},
                "ssl_certificate": {"required": False, "type": "str"},
                "update_interval": {"required": False, "type": "int"},
                "use_public_ip": {"required": False, "type": "str",
                                  "choices": ["disable", "enable"]}

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

            is_error, has_changed, result = fortios_system(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
