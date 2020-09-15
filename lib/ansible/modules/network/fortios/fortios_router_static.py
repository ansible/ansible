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
module: fortios_router_static
short_description: Configure IPv4 static routing tables in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify router feature and static category.
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
    router_static:
        description:
            - Configure IPv4 static routing tables.
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
            bfd:
                description:
                    - Enable/disable Bidirectional Forwarding Detection (BFD).
                type: str
                choices:
                    - enable
                    - disable
            blackhole:
                description:
                    - Enable/disable black hole.
                type: str
                choices:
                    - enable
                    - disable
            comment:
                description:
                    - Optional comments.
                type: str
            device:
                description:
                    - Gateway out interface or tunnel. Source system.interface.name.
                type: str
            distance:
                description:
                    - Administrative distance (1 - 255).
                type: int
            dst:
                description:
                    - Destination IP and mask for this route.
                type: str
            dstaddr:
                description:
                    - Name of firewall address or address group. Source firewall.address.name firewall.addrgrp.name.
                type: str
            dynamic_gateway:
                description:
                    - Enable use of dynamic gateway retrieved from a DHCP or PPP server.
                type: str
                choices:
                    - enable
                    - disable
            gateway:
                description:
                    - Gateway IP for this route.
                type: str
            internet_service:
                description:
                    - Application ID in the Internet service database. Source firewall.internet-service.id.
                type: int
            internet_service_custom:
                description:
                    - Application name in the Internet service custom database. Source firewall.internet-service-custom.name.
                type: str
            link_monitor_exempt:
                description:
                    - Enable/disable withdrawing this route when link monitor or health check is down.
                type: str
                choices:
                    - enable
                    - disable
            priority:
                description:
                    - Administrative priority (0 - 4294967295).
                type: int
            seq_num:
                description:
                    - Sequence number.
                type: int
            src:
                description:
                    - Source prefix for this route.
                type: str
            status:
                description:
                    - Enable/disable this static route.
                type: str
                choices:
                    - enable
                    - disable
            virtual_wan_link:
                description:
                    - Enable/disable egress through the virtual-wan-link.
                type: str
                choices:
                    - enable
                    - disable
            vrf:
                description:
                    - Virtual Routing Forwarding ID.
                type: int
            weight:
                description:
                    - Administrative weight (0 - 255).
                type: int
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
  - name: Configure IPv4 static routing tables.
    fortios_router_static:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      router_static:
        bfd: "enable"
        blackhole: "enable"
        comment: "Optional comments."
        device: "<your_own_value> (source system.interface.name)"
        distance: "7"
        dst: "<your_own_value>"
        dstaddr: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
        dynamic_gateway: "enable"
        gateway: "<your_own_value>"
        internet_service: "12 (source firewall.internet-service.id)"
        internet_service_custom: "<your_own_value> (source firewall.internet-service-custom.name)"
        link_monitor_exempt: "enable"
        priority: "15"
        seq_num: "16"
        src: "<your_own_value>"
        status: "enable"
        virtual_wan_link: "enable"
        vrf: "20"
        weight: "21"
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


def filter_router_static_data(json):
    option_list = ['bfd', 'blackhole', 'comment',
                   'device', 'distance', 'dst',
                   'dstaddr', 'dynamic_gateway', 'gateway',
                   'internet_service', 'internet_service_custom', 'link_monitor_exempt',
                   'priority', 'seq_num', 'src',
                   'status', 'virtual_wan_link', 'vrf',
                   'weight']
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


def router_static(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['router_static'] and data['router_static']:
        state = data['router_static']['state']
    else:
        state = True
    router_static_data = data['router_static']
    filtered_data = underscore_to_hyphen(filter_router_static_data(router_static_data))

    if state == "present":
        return fos.set('router',
                       'static',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('router',
                          'static',
                          mkey=filtered_data['seq-num'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_router(data, fos):

    if data['router_static']:
        resp = router_static(data, fos)

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
        "router_static": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "bfd": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "blackhole": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "comment": {"required": False, "type": "str"},
                "device": {"required": False, "type": "str"},
                "distance": {"required": False, "type": "int"},
                "dst": {"required": False, "type": "str"},
                "dstaddr": {"required": False, "type": "str"},
                "dynamic_gateway": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "gateway": {"required": False, "type": "str"},
                "internet_service": {"required": False, "type": "int"},
                "internet_service_custom": {"required": False, "type": "str"},
                "link_monitor_exempt": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "priority": {"required": False, "type": "int"},
                "seq_num": {"required": False, "type": "int"},
                "src": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "virtual_wan_link": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "vrf": {"required": False, "type": "int"},
                "weight": {"required": False, "type": "int"}

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

            is_error, has_changed, result = fortios_router(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_router(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
