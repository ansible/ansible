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
module: fortios_firewall_ippool
short_description: Configure IPv4 IP pools in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and ippool category.
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
    firewall_ippool:
        description:
            - Configure IPv4 IP pools.
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
            arp_intf:
                description:
                    - Select an interface from available options that will reply to ARP requests. (If blank, any is selected). Source system.interface.name.
                type: str
            arp_reply:
                description:
                    - Enable/disable replying to ARP requests when an IP Pool is added to a policy .
                type: str
                choices:
                    - disable
                    - enable
            associated_interface:
                description:
                    - Associated interface name. Source system.interface.name.
                type: str
            block_size:
                description:
                    -  Number of addresses in a block (64 to 4096).
                type: int
            comments:
                description:
                    - Comment.
                type: str
            endip:
                description:
                    - "Final IPv4 address (inclusive) in the range for the address pool (format xxx.xxx.xxx.xxx)."
                type: str
            name:
                description:
                    - IP pool name.
                required: true
                type: str
            num_blocks_per_user:
                description:
                    - Number of addresses blocks that can be used by a user (1 to 128).
                type: int
            pba_timeout:
                description:
                    - Port block allocation timeout (seconds).
                type: int
            permit_any_host:
                description:
                    - Enable/disable full cone NAT.
                type: str
                choices:
                    - disable
                    - enable
            source_endip:
                description:
                    - "Final IPv4 address (inclusive) in the range of the source addresses to be translated (format xxx.xxx.xxx.xxx)."
                type: str
            source_startip:
                description:
                    - " First IPv4 address (inclusive) in the range of the source addresses to be translated (format xxx.xxx.xxx.xxx)."
                type: str
            startip:
                description:
                    - "First IPv4 address (inclusive) in the range for the address pool (format xxx.xxx.xxx.xxx)."
                type: str
            type:
                description:
                    - IP pool type (overload, one-to-one, fixed port range, or port block allocation).
                type: str
                choices:
                    - overload
                    - one-to-one
                    - fixed-port-range
                    - port-block-allocation
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
  - name: Configure IPv4 IP pools.
    fortios_firewall_ippool:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_ippool:
        arp_intf: "<your_own_value> (source system.interface.name)"
        arp_reply: "disable"
        associated_interface: "<your_own_value> (source system.interface.name)"
        block_size: "6"
        comments: "<your_own_value>"
        endip: "<your_own_value>"
        name: "default_name_9"
        num_blocks_per_user: "10"
        pba_timeout: "11"
        permit_any_host: "disable"
        source_endip: "<your_own_value>"
        source_startip: "<your_own_value>"
        startip: "<your_own_value>"
        type: "overload"
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


def filter_firewall_ippool_data(json):
    option_list = ['arp_intf', 'arp_reply', 'associated_interface',
                   'block_size', 'comments', 'endip',
                   'name', 'num_blocks_per_user', 'pba_timeout',
                   'permit_any_host', 'source_endip', 'source_startip',
                   'startip', 'type']
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


def firewall_ippool(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_ippool'] and data['firewall_ippool']:
        state = data['firewall_ippool']['state']
    else:
        state = True
    firewall_ippool_data = data['firewall_ippool']
    filtered_data = underscore_to_hyphen(filter_firewall_ippool_data(firewall_ippool_data))

    if state == "present":
        return fos.set('firewall',
                       'ippool',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'ippool',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_ippool']:
        resp = firewall_ippool(data, fos)

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
        "firewall_ippool": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "arp_intf": {"required": False, "type": "str"},
                "arp_reply": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "associated_interface": {"required": False, "type": "str"},
                "block_size": {"required": False, "type": "int"},
                "comments": {"required": False, "type": "str"},
                "endip": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "num_blocks_per_user": {"required": False, "type": "int"},
                "pba_timeout": {"required": False, "type": "int"},
                "permit_any_host": {"required": False, "type": "str",
                                    "choices": ["disable", "enable"]},
                "source_endip": {"required": False, "type": "str"},
                "source_startip": {"required": False, "type": "str"},
                "startip": {"required": False, "type": "str"},
                "type": {"required": False, "type": "str",
                         "choices": ["overload", "one-to-one", "fixed-port-range",
                                     "port-block-allocation"]}

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
