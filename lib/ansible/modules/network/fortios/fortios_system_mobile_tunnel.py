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
module: fortios_system_mobile_tunnel
short_description: Configure Mobile tunnels, an implementation of Network Mobility (NEMO) extensions for Mobile IPv4 RFC5177 in Fortinet's FortiOS and
   FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and mobile_tunnel category.
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
    system_mobile_tunnel:
        description:
            - Configure Mobile tunnels, an implementation of Network Mobility (NEMO) extensions for Mobile IPv4 RFC5177.
        default: null
        type: dict
        suboptions:
            hash_algorithm:
                description:
                    - Hash Algorithm (Keyed MD5).
                type: str
                choices:
                    - hmac-md5
            home_address:
                description:
                    - "Home IP address (Format: xxx.xxx.xxx.xxx)."
                type: str
            home_agent:
                description:
                    - "IPv4 address of the NEMO HA (Format: xxx.xxx.xxx.xxx)."
                type: str
            lifetime:
                description:
                    - NMMO HA registration request lifetime (180 - 65535 sec).
                type: int
            n_mhae_key:
                description:
                    - NEMO authentication key.
                type: str
            n_mhae_key_type:
                description:
                    - NEMO authentication key type (ascii or base64).
                type: str
                choices:
                    - ascii
                    - base64
            n_mhae_spi:
                description:
                    - "NEMO authentication SPI ."
                type: int
            name:
                description:
                    - Tunnel name.
                required: true
                type: str
            network:
                description:
                    - NEMO network configuration.
                type: list
                suboptions:
                    id:
                        description:
                            - Network entry ID.
                        required: true
                        type: int
                    interface:
                        description:
                            - Select the associated interface name from available options. Source system.interface.name.
                        type: str
                    prefix:
                        description:
                            - "Class IP and Netmask with correction (Format:xxx.xxx.xxx.xxx xxx.xxx.xxx.xxx or xxx.xxx.xxx.xxx/x)."
                        type: str
            reg_interval:
                description:
                    - NMMO HA registration interval (5 - 300).
                type: int
            reg_retry:
                description:
                    - Maximum number of NMMO HA registration retries (1 to 30).
                type: int
            renew_interval:
                description:
                    - Time before lifetime expiration to send NMMO HA re-registration (5 - 60).
                type: int
            roaming_interface:
                description:
                    - Select the associated interface name from available options. Source system.interface.name.
                type: str
            status:
                description:
                    - Enable/disable this mobile tunnel.
                type: str
                choices:
                    - disable
                    - enable
            tunnel_mode:
                description:
                    - NEMO tunnel mode (GRE tunnel).
                type: str
                choices:
                    - gre
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
  - name: Configure Mobile tunnels, an implementation of Network Mobility (NEMO) extensions for Mobile IPv4 RFC5177.
    fortios_system_mobile_tunnel:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_mobile_tunnel:
        hash_algorithm: "hmac-md5"
        home_address: "<your_own_value>"
        home_agent: "<your_own_value>"
        lifetime: "6"
        n_mhae_key: "<your_own_value>"
        n_mhae_key_type: "ascii"
        n_mhae_spi: "9"
        name: "default_name_10"
        network:
         -
            id:  "12"
            interface: "<your_own_value> (source system.interface.name)"
            prefix: "<your_own_value>"
        reg_interval: "15"
        reg_retry: "16"
        renew_interval: "17"
        roaming_interface: "<your_own_value> (source system.interface.name)"
        status: "disable"
        tunnel_mode: "gre"
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


def filter_system_mobile_tunnel_data(json):
    option_list = ['hash_algorithm', 'home_address', 'home_agent',
                   'lifetime', 'n_mhae_key', 'n_mhae_key_type',
                   'n_mhae_spi', 'name', 'network',
                   'reg_interval', 'reg_retry', 'renew_interval',
                   'roaming_interface', 'status', 'tunnel_mode']
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


def system_mobile_tunnel(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_mobile_tunnel_data = data['system_mobile_tunnel']
    filtered_data = underscore_to_hyphen(filter_system_mobile_tunnel_data(system_mobile_tunnel_data))

    if state == "present":
        return fos.set('system',
                       'mobile-tunnel',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'mobile-tunnel',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_mobile_tunnel']:
        resp = system_mobile_tunnel(data, fos)

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
        "system_mobile_tunnel": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "hash_algorithm": {"required": False, "type": "str",
                                   "choices": ["hmac-md5"]},
                "home_address": {"required": False, "type": "str"},
                "home_agent": {"required": False, "type": "str"},
                "lifetime": {"required": False, "type": "int"},
                "n_mhae_key": {"required": False, "type": "str", "no_log": True},
                "n_mhae_key_type": {"required": False, "type": "str",
                                    "choices": ["ascii", "base64"]},
                "n_mhae_spi": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "network": {"required": False, "type": "list",
                            "options": {
                                "id": {"required": True, "type": "int"},
                                "interface": {"required": False, "type": "str"},
                                "prefix": {"required": False, "type": "str"}
                            }},
                "reg_interval": {"required": False, "type": "int"},
                "reg_retry": {"required": False, "type": "int"},
                "renew_interval": {"required": False, "type": "int"},
                "roaming_interface": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["disable", "enable"]},
                "tunnel_mode": {"required": False, "type": "str",
                                "choices": ["gre"]}

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
