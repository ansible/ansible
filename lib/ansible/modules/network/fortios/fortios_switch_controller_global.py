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
module: fortios_switch_controller_global
short_description: Configure FortiSwitch global settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify switch_controller feature and global category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
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
            - FortiOS or FortiGate ip address.
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
    switch_controller_global:
        description:
            - Configure FortiSwitch global settings.
        default: null
        suboptions:
            allow-multiple-interfaces:
                description:
                    - Enable/disable multiple FortiLink interfaces for redundant connections between a managed FortiSwitch and FortiGate.
                choices:
                    - enable
                    - disable
            default-virtual-switch-vlan:
                description:
                    - Default VLAN for ports when added to the virtual-switch. Source system.interface.name.
            disable-discovery:
                description:
                    - Prevent this FortiSwitch from discovering.
                suboptions:
                    name:
                        description:
                            - Managed device ID.
                        required: true
            https-image-push:
                description:
                    - Enable/disable image push to FortiSwitch using HTTPS.
                choices:
                    - enable
                    - disable
            log-mac-limit-violations:
                description:
                    - Enable/disable logs for Learning Limit Violations.
                choices:
                    - enable
                    - disable
            mac-aging-interval:
                description:
                    - Time after which an inactive MAC is aged out (10 - 1000000 sec, default = 300, 0 = disable).
            mac-retention-period:
                description:
                    - Time in hours after which an inactive MAC is removed from client DB.
            mac-violation-timer:
                description:
                    - Set timeout for Learning Limit Violations (0 = disabled).
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure FortiSwitch global settings.
    fortios_switch_controller_global:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      switch_controller_global:
        allow-multiple-interfaces: "enable"
        default-virtual-switch-vlan: "<your_own_value> (source system.interface.name)"
        disable-discovery:
         -
            name: "default_name_6"
        https-image-push: "enable"
        log-mac-limit-violations: "enable"
        mac-aging-interval: "9"
        mac-retention-period: "10"
        mac-violation-timer: "11"
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


def filter_switch_controller_global_data(json):
    option_list = ['allow-multiple-interfaces', 'default-virtual-switch-vlan', 'disable-discovery',
                   'https-image-push', 'log-mac-limit-violations', 'mac-aging-interval',
                   'mac-retention-period', 'mac-violation-timer']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def switch_controller_global(data, fos):
    vdom = data['vdom']
    switch_controller_global_data = data['switch_controller_global']
    flattened_data = flatten_multilists_attributes(switch_controller_global_data)
    filtered_data = filter_switch_controller_global_data(flattened_data)
    return fos.set('switch-controller',
                   'global',
                   data=filtered_data,
                   vdom=vdom)


def fortios_switch_controller(data, fos):
    login(data)

    if data['switch_controller_global']:
        resp = switch_controller_global(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "switch_controller_global": {
            "required": False, "type": "dict",
            "options": {
                "allow-multiple-interfaces": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "default-virtual-switch-vlan": {"required": False, "type": "str"},
                "disable-discovery": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "https-image-push": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "log-mac-limit-violations": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "mac-aging-interval": {"required": False, "type": "int"},
                "mac-retention-period": {"required": False, "type": "int"},
                "mac-violation-timer": {"required": False, "type": "int"}

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

    is_error, has_changed, result = fortios_switch_controller(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
