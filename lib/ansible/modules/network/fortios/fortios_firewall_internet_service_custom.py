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
module: fortios_firewall_internet_service_custom
short_description: Configure custom Internet Services in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and internet_service_custom category.
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
    firewall_internet_service_custom:
        description:
            - Configure custom Internet Services.
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
            comment:
                description:
                    - Comment.
                type: str
            disable_entry:
                description:
                    - Disable entries in the Internet Service database.
                type: list
                suboptions:
                    id:
                        description:
                            - Disable entry ID.
                        required: true
                        type: int
                    ip_range:
                        description:
                            - IP ranges in the disable entry.
                        type: list
                        suboptions:
                            end_ip:
                                description:
                                    - End IP address.
                                type: str
                            id:
                                description:
                                    - Disable entry range ID.
                                required: true
                                type: int
                            start_ip:
                                description:
                                    - Start IP address.
                                type: str
                    port:
                        description:
                            - Integer value for the TCP/IP port (0 - 65535).
                        type: int
                    protocol:
                        description:
                            - Integer value for the protocol type as defined by IANA (0 - 255).
                        type: int
            entry:
                description:
                    - Entries added to the Internet Service database and custom database.
                type: list
                suboptions:
                    dst:
                        description:
                            - Destination address or address group name.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Select the destination address or address group object from available options. Source firewall.address.name firewall
                                      .addrgrp.name.
                                required: true
                                type: str
                    id:
                        description:
                            - Entry ID(1-255).
                        required: true
                        type: int
                    port_range:
                        description:
                            - Port ranges in the custom entry.
                        type: list
                        suboptions:
                            end_port:
                                description:
                                    - Integer value for ending TCP/UDP/SCTP destination port in range (1 to 65535).
                                type: int
                            id:
                                description:
                                    - Custom entry port range ID.
                                required: true
                                type: int
                            start_port:
                                description:
                                    - Integer value for starting TCP/UDP/SCTP destination port in range (1 to 65535).
                                type: int
                    protocol:
                        description:
                            - Integer value for the protocol type as defined by IANA (0 - 255).
                        type: int
            master_service_id:
                description:
                    - Internet Service ID in the Internet Service database. Source firewall.internet-service.id.
                type: int
            name:
                description:
                    - Internet Service name.
                required: true
                type: str
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
  - name: Configure custom Internet Services.
    fortios_firewall_internet_service_custom:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_internet_service_custom:
        comment: "Comment."
        disable_entry:
         -
            id:  "5"
            ip_range:
             -
                end_ip: "<your_own_value>"
                id:  "8"
                start_ip: "<your_own_value>"
            port: "10"
            protocol: "11"
        entry:
         -
            dst:
             -
                name: "default_name_14 (source firewall.address.name firewall.addrgrp.name)"
            id:  "15"
            port_range:
             -
                end_port: "17"
                id:  "18"
                start_port: "19"
            protocol: "20"
        master_service_id: "21 (source firewall.internet-service.id)"
        name: "default_name_22"
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


def filter_firewall_internet_service_custom_data(json):
    option_list = ['comment', 'disable_entry', 'entry',
                   'master_service_id', 'name']
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


def firewall_internet_service_custom(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_internet_service_custom'] and data['firewall_internet_service_custom']:
        state = data['firewall_internet_service_custom']['state']
    else:
        state = True
    firewall_internet_service_custom_data = data['firewall_internet_service_custom']
    filtered_data = underscore_to_hyphen(filter_firewall_internet_service_custom_data(firewall_internet_service_custom_data))

    if state == "present":
        return fos.set('firewall',
                       'internet-service-custom',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'internet-service-custom',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_internet_service_custom']:
        resp = firewall_internet_service_custom(data, fos)

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
        "firewall_internet_service_custom": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "disable_entry": {"required": False, "type": "list",
                                  "options": {
                                      "id": {"required": True, "type": "int"},
                                      "ip_range": {"required": False, "type": "list",
                                                   "options": {
                                                       "end_ip": {"required": False, "type": "str"},
                                                       "id": {"required": True, "type": "int"},
                                                       "start_ip": {"required": False, "type": "str"}
                                                   }},
                                      "port": {"required": False, "type": "int"},
                                      "protocol": {"required": False, "type": "int"}
                                  }},
                "entry": {"required": False, "type": "list",
                          "options": {
                              "dst": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                              "id": {"required": True, "type": "int"},
                              "port_range": {"required": False, "type": "list",
                                             "options": {
                                                 "end_port": {"required": False, "type": "int"},
                                                 "id": {"required": True, "type": "int"},
                                                 "start_port": {"required": False, "type": "int"}
                                             }},
                              "protocol": {"required": False, "type": "int"}
                          }},
                "master_service_id": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"}

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
