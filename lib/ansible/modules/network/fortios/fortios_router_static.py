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
module: fortios_router_static
short_description: Configure IPv4 static routing tables in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify router feature and static category.
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
    router_static:
        description:
            - Configure IPv4 static routing tables.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            bfd:
                description:
                    - Enable/disable Bidirectional Forwarding Detection (BFD).
                choices:
                    - enable
                    - disable
            blackhole:
                description:
                    - Enable/disable black hole.
                choices:
                    - enable
                    - disable
            comment:
                description:
                    - Optional comments.
            device:
                description:
                    - Gateway out interface or tunnel. Source system.interface.name.
            distance:
                description:
                    - Administrative distance (1 - 255).
            dst:
                description:
                    - Destination IP and mask for this route.
            dstaddr:
                description:
                    - Name of firewall address or address group. Source firewall.address.name firewall.addrgrp.name.
            dynamic-gateway:
                description:
                    - Enable use of dynamic gateway retrieved from a DHCP or PPP server.
                choices:
                    - enable
                    - disable
            gateway:
                description:
                    - Gateway IP for this route.
            internet-service:
                description:
                    - Application ID in the Internet service database. Source firewall.internet-service.id.
            internet-service-custom:
                description:
                    - Application name in the Internet service custom database. Source firewall.internet-service-custom.name.
            link-monitor-exempt:
                description:
                    - Enable/disable withdrawing this route when link monitor or health check is down.
                choices:
                    - enable
                    - disable
            priority:
                description:
                    - Administrative priority (0 - 4294967295).
            seq-num:
                description:
                    - Sequence number.
                required: true
            src:
                description:
                    - Source prefix for this route.
            status:
                description:
                    - Enable/disable this static route.
                choices:
                    - enable
                    - disable
            virtual-wan-link:
                description:
                    - Enable/disable egress through the virtual-wan-link.
                choices:
                    - enable
                    - disable
            vrf:
                description:
                    - Virtual Routing Forwarding ID.
            weight:
                description:
                    - Administrative weight (0 - 255).
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv4 static routing tables.
    fortios_router_static:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_static:
        state: "present"
        bfd: "enable"
        blackhole: "enable"
        comment: "Optional comments."
        device: "<your_own_value> (source system.interface.name)"
        distance: "7"
        dst: "<your_own_value>"
        dstaddr: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
        dynamic-gateway: "enable"
        gateway: "<your_own_value>"
        internet-service: "12 (source firewall.internet-service.id)"
        internet-service-custom: "<your_own_value> (source firewall.internet-service-custom.name)"
        link-monitor-exempt: "enable"
        priority: "15"
        seq-num: "16"
        src: "<your_own_value>"
        status: "enable"
        virtual-wan-link: "enable"
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


def filter_router_static_data(json):
    option_list = ['bfd', 'blackhole', 'comment',
                   'device', 'distance', 'dst',
                   'dstaddr', 'dynamic-gateway', 'gateway',
                   'internet-service', 'internet-service-custom', 'link-monitor-exempt',
                   'priority', 'seq-num', 'src',
                   'status', 'virtual-wan-link', 'vrf',
                   'weight']
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


def router_static(data, fos):
    vdom = data['vdom']
    router_static_data = data['router_static']
    flattened_data = flatten_multilists_attributes(router_static_data)
    filtered_data = filter_router_static_data(flattened_data)
    if router_static_data['state'] == "present":
        return fos.set('router',
                       'static',
                       data=filtered_data,
                       vdom=vdom)

    elif router_static_data['state'] == "absent":
        return fos.delete('router',
                          'static',
                          mkey=filtered_data['seq-num'],
                          vdom=vdom)


def fortios_router(data, fos):
    login(data)

    if data['router_static']:
        resp = router_static(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "router_static": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
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
                "dynamic-gateway": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "gateway": {"required": False, "type": "str"},
                "internet-service": {"required": False, "type": "int"},
                "internet-service-custom": {"required": False, "type": "str"},
                "link-monitor-exempt": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "priority": {"required": False, "type": "int"},
                "seq-num": {"required": True, "type": "int"},
                "src": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "virtual-wan-link": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "vrf": {"required": False, "type": "int"},
                "weight": {"required": False, "type": "int"}

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
