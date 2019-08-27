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
module: fortios_system_firmware_upgrade
short_description: Perform firmware upgrade on FortiGate or FortiOS (FOS) device.
description:
    - This module is able to perform firmware upgrade on FortiGate or FortiOS (FOS) device by specifying
      firmware upgrade source, filename and whether format boot partition before upgrade.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
version_added: "2.9"
author:
    - Don Yao (@fortinetps)
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
        required: false
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
        required: false
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
        required: false
    system_firmware:
        description:
            - Possible parameters to go in the body for the request.
              Specify firmware upgrade source, filename and whether
              format boot partition before upgrade
        default: null
        type: dict
        required: true
        suboptions:
            file_content:
                description:
                    - "Provided when uploading a file: base64 encoded file data. Must not contain whitespace or other invalid base64 characters. Must be
                       included in HTTP body."
                type: str
                required: false
            filename:
                description:
                    - Name and path of the local firmware file.
                type: str
                required: true
            format_partition:
                description:
                    - Set to true to format boot partition before upgrade.
                type: bool
                required: false
            source:
                description:
                    - Firmware file data source [upload|usb|fortiguard].
                type: str
                required: true
                choices:
                    - upload
                    - usb
                    - fortiguard
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
  - name: Perform firmware upgrade with local firmware file.
    fortios_system_firmware:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      ssl_verify: "False"
      system_firmware:
        file_content: "<your_own_value>"
        filename: "<your_own_value>"
        format_partition: "<your_own_value>"
        source: "upload"
    register: fortios_system_firmware_upgrade_result

  - debug:
      var:
        # please check the following status to confirm
        fortios_system_firmware_upgrade_result.meta.results.status

  - name: Perform firmware upgrade with firmware file on USB.
    fortios_system_firmware_upgrade:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      ssl_verify: "False"
      system_firmware:
        filename: "<your_own_value>"
        format_partition: "<your_own_value>"
        source: "usb"
    register: fortios_system_firmware_upgrade_result

  - debug:
      var:
        # please check the following status to confirm
        fortios_system_firmware_upgrade_result.meta.results.status

  - name: Perform firmware upgrade from FortiGuard.
    fortios_system_firmware_upgrade:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      ssl_verify: "False"
      system_firmware:
        filename: "<your_own_value>"
        format_partition: "<your_own_value>"
        source: "fortiguard"
    register: fortios_system_firmware_upgrade_result

  - debug:
      var:
        # please check the following status to confirm
        fortios_system_firmware_upgrade_result.meta.results.status
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
  sample: 'POST'
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "firmware"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "system"
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
import os
import base64


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

    fos.login(host, username, password, timeout=300, verify=ssl_verify)


def filter_system_firmware_data(json):
    option_list = ['file_content', 'filename', 'format_partition',
                   'source']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def system_firmware(data, fos, check_mode=False):
    vdom = data['vdom']

    system_firmware_data = data['system_firmware']

    filtered_data = {}
    filtered_data['source'] = system_firmware_data['source']
    if hasattr(system_firmware_data, 'format_partition'):
        filtered_data['format_partition'] = system_firmware_data['format_partition']
    if filtered_data['source'] == 'upload':
        try:
            filtered_data['file_content'] = base64.b64encode(open(system_firmware_data['filename'], 'rb').read()).decode('utf-8')
        except Exception:
            filtered_data['file_content'] = ''
    else:
        filtered_data['filename'] = system_firmware_data['filename']

    return fos.execute('system',
                       'firmware/upgrade',
                       data=filtered_data,
                       vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_firmware']:
        resp = system_firmware(data, fos)

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
        "system_firmware": {
            "required": True, "type": "dict",
            "options": {
                "file_content": {"required": False, "type": "str"},
                "filename": {"required": True, "type": "str"},
                "format_partition": {"required": False, "type": "bool"},
                "source": {"required": True, "type": "str",
                           "choices": ["upload", "usb", "fortiguard"]}

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
