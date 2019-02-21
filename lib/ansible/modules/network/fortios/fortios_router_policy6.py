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
module: fortios_router_policy6
short_description: Configure IPv6 routing policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify router feature and policy6 category.
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
    router_policy6:
        description:
            - Configure IPv6 routing policies.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            comments:
                description:
                    - Optional comments.
            dst:
                description:
                    - Destination IPv6 prefix.
            end-port:
                description:
                    - End destination port number (1 - 65535).
            gateway:
                description:
                    - IPv6 address of the gateway.
            input-device:
                description:
                    - Incoming interface name. Source system.interface.name.
            output-device:
                description:
                    - Outgoing interface name. Source system.interface.name.
            protocol:
                description:
                    - Protocol number (0 - 255).
            seq-num:
                description:
                    - Sequence number.
                required: true
            src:
                description:
                    - Source IPv6 prefix.
            start-port:
                description:
                    - Start destination port number (1 - 65535).
            status:
                description:
                    - Enable/disable this policy route.
                choices:
                    - enable
                    - disable
            tos:
                description:
                    - Type of service bit pattern.
            tos-mask:
                description:
                    - Type of service evaluated bits.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv6 routing policies.
    fortios_router_policy6:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_policy6:
        state: "present"
        comments: "<your_own_value>"
        dst: "<your_own_value>"
        end-port: "5"
        gateway: "<your_own_value>"
        input-device: "<your_own_value> (source system.interface.name)"
        output-device: "<your_own_value> (source system.interface.name)"
        protocol: "9"
        seq-num: "10"
        src: "<your_own_value>"
        start-port: "12"
        status: "enable"
        tos: "<your_own_value>"
        tos-mask: "<your_own_value>"
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


def filter_router_policy6_data(json):
    option_list = ['comments', 'dst', 'end-port',
                   'gateway', 'input-device', 'output-device',
                   'protocol', 'seq-num', 'src',
                   'start-port', 'status', 'tos',
                   'tos-mask']
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


def router_policy6(data, fos):
    vdom = data['vdom']
    router_policy6_data = data['router_policy6']
    flattened_data = flatten_multilists_attributes(router_policy6_data)
    filtered_data = filter_router_policy6_data(flattened_data)
    if router_policy6_data['state'] == "present":
        return fos.set('router',
                       'policy6',
                       data=filtered_data,
                       vdom=vdom)

    elif router_policy6_data['state'] == "absent":
        return fos.delete('router',
                          'policy6',
                          mkey=filtered_data['seq-num'],
                          vdom=vdom)


def fortios_router(data, fos):
    login(data)

    if data['router_policy6']:
        resp = router_policy6(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "router_policy6": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "comments": {"required": False, "type": "str"},
                "dst": {"required": False, "type": "str"},
                "end-port": {"required": False, "type": "int"},
                "gateway": {"required": False, "type": "str"},
                "input-device": {"required": False, "type": "str"},
                "output-device": {"required": False, "type": "str"},
                "protocol": {"required": False, "type": "int"},
                "seq-num": {"required": True, "type": "int"},
                "src": {"required": False, "type": "str"},
                "start-port": {"required": False, "type": "int"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "tos": {"required": False, "type": "str"},
                "tos-mask": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_router(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
