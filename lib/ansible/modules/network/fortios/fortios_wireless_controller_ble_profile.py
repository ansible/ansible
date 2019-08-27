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
module: fortios_wireless_controller_ble_profile
short_description: Configure Bluetooth Low Energy profile in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wireless_controller feature and ble_profile category.
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
    wireless_controller_ble_profile:
        description:
            - Configure Bluetooth Low Energy profile.
        default: null
        type: dict
        suboptions:
            advertising:
                description:
                    - Advertising type.
                type: str
                choices:
                    - ibeacon
                    - eddystone-uid
                    - eddystone-url
            beacon_interval:
                description:
                    - Beacon interval .
                type: int
            ble_scanning:
                description:
                    - Enable/disable Bluetooth Low Energy (BLE) scanning.
                type: str
                choices:
                    - enable
                    - disable
            comment:
                description:
                    - Comment.
                type: str
            eddystone_instance:
                description:
                    - Eddystone instance ID.
                type: str
            eddystone_namespace:
                description:
                    - Eddystone namespace ID.
                type: str
            eddystone_url:
                description:
                    - Eddystone URL.
                type: str
            eddystone_url_encode_hex:
                description:
                    - Eddystone encoded URL hexadecimal string
                type: str
            ibeacon_uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
                type: str
            major_id:
                description:
                    - Major ID.
                type: int
            minor_id:
                description:
                    - Minor ID.
                type: int
            name:
                description:
                    - Bluetooth Low Energy profile name.
                required: true
                type: str
            txpower:
                description:
                    - Transmit power level .
                type: str
                choices:
                    - 0
                    - 1
                    - 2
                    - 3
                    - 4
                    - 5
                    - 6
                    - 7
                    - 8
                    - 9
                    - 10
                    - 11
                    - 12
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
  - name: Configure Bluetooth Low Energy profile.
    fortios_wireless_controller_ble_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      wireless_controller_ble_profile:
        advertising: "ibeacon"
        beacon_interval: "4"
        ble_scanning: "enable"
        comment: "Comment."
        eddystone_instance: "<your_own_value>"
        eddystone_namespace: "<your_own_value>"
        eddystone_url: "<your_own_value>"
        eddystone_url_encode_hex: "<your_own_value>"
        ibeacon_uuid: "<your_own_value>"
        major_id: "12"
        minor_id: "13"
        name: "default_name_14"
        txpower: "0"
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


def filter_wireless_controller_ble_profile_data(json):
    option_list = ['advertising', 'beacon_interval', 'ble_scanning',
                   'comment', 'eddystone_instance', 'eddystone_namespace',
                   'eddystone_url', 'eddystone_url_encode_hex', 'ibeacon_uuid',
                   'major_id', 'minor_id', 'name',
                   'txpower']
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


def wireless_controller_ble_profile(data, fos):
    vdom = data['vdom']
    state = data['state']
    wireless_controller_ble_profile_data = data['wireless_controller_ble_profile']
    filtered_data = underscore_to_hyphen(filter_wireless_controller_ble_profile_data(wireless_controller_ble_profile_data))

    if state == "present":
        return fos.set('wireless-controller',
                       'ble-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('wireless-controller',
                          'ble-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wireless_controller(data, fos):

    if data['wireless_controller_ble_profile']:
        resp = wireless_controller_ble_profile(data, fos)

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
        "wireless_controller_ble_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "advertising": {"required": False, "type": "str",
                                "choices": ["ibeacon", "eddystone-uid", "eddystone-url"]},
                "beacon_interval": {"required": False, "type": "int"},
                "ble_scanning": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "comment": {"required": False, "type": "str"},
                "eddystone_instance": {"required": False, "type": "str"},
                "eddystone_namespace": {"required": False, "type": "str"},
                "eddystone_url": {"required": False, "type": "str"},
                "eddystone_url_encode_hex": {"required": False, "type": "str"},
                "ibeacon_uuid": {"required": False, "type": "str"},
                "major_id": {"required": False, "type": "int"},
                "minor_id": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "txpower": {"required": False, "type": "str",
                            "choices": ["0", "1", "2",
                                        "3", "4", "5",
                                        "6", "7", "8",
                                        "9", "10", "11",
                                        "12"]}

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

            is_error, has_changed, result = fortios_wireless_controller(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_wireless_controller(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
