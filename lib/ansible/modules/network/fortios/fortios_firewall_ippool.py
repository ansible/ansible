#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2018 Fortinet, Inc.
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
module: fortios_firewall_ippool
short_description: Configure IPv4 IP pools in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and ippool category.
      Examples includes all options and need to be adjusted to datasources before usage.
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
        default: false
    firewall_ippool:
        description:
            - Configure IPv4 IP pools.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            arp-intf:
                description:
                    - Select an interface from available options that will reply to ARP requests. (If blank, any is selected). Source system.interface.name.
            arp-reply:
                description:
                    - Enable/disable replying to ARP requests when an IP Pool is added to a policy (default = enable).
                choices:
                    - disable
                    - enable
            associated-interface:
                description:
                    - Associated interface name. Source system.interface.name.
            block-size:
                description:
                    -  Number of addresses in a block (64 to 4096, default = 128).
            comments:
                description:
                    - Comment.
            endip:
                description:
                    - "Final IPv4 address (inclusive) in the range for the address pool (format xxx.xxx.xxx.xxx, Default: 0.0.0.0)."
            name:
                description:
                    - IP pool name.
                required: true
            num-blocks-per-user:
                description:
                    - Number of addresses blocks that can be used by a user (1 to 128, default = 8).
            pba-timeout:
                description:
                    - Port block allocation timeout (seconds).
            permit-any-host:
                description:
                    - Enable/disable full cone NAT.
                choices:
                    - disable
                    - enable
            source-endip:
                description:
                    - "Final IPv4 address (inclusive) in the range of the source addresses to be translated (format xxx.xxx.xxx.xxx, Default: 0.0.0.0)."
            source-startip:
                description:
                    - " First IPv4 address (inclusive) in the range of the source addresses to be translated (format xxx.xxx.xxx.xxx, Default: 0.0.0.0)."
            startip:
                description:
                    - "First IPv4 address (inclusive) in the range for the address pool (format xxx.xxx.xxx.xxx, Default: 0.0.0.0)."
            type:
                description:
                    - IP pool type (overload, one-to-one, fixed port range, or port block allocation).
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
  tasks:
  - name: Configure IPv4 IP pools.
    fortios_firewall_ippool:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_ippool:
        state: "present"
        arp-intf: "<your_own_value> (source system.interface.name)"
        arp-reply: "disable"
        associated-interface: "<your_own_value> (source system.interface.name)"
        block-size: "6"
        comments: "<your_own_value>"
        endip: "<your_own_value>"
        name: "default_name_9"
        num-blocks-per-user: "10"
        pba-timeout: "11"
        permit-any-host: "disable"
        source-endip: "<your_own_value>"
        source-startip: "<your_own_value>"
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
  sample: "key1"
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


def filter_firewall_ippool_data(json):
    option_list = ['arp-intf', 'arp-reply', 'associated-interface',
                   'block-size', 'comments', 'endip',
                   'name', 'num-blocks-per-user', 'pba-timeout',
                   'permit-any-host', 'source-endip', 'source-startip',
                   'startip', 'type']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_ippool(data, fos):
    vdom = data['vdom']
    firewall_ippool_data = data['firewall_ippool']
    filtered_data = filter_firewall_ippool_data(firewall_ippool_data)
    if firewall_ippool_data['state'] == "present":
        return fos.set('firewall',
                       'ippool',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_ippool_data['state'] == "absent":
        return fos.delete('firewall',
                          'ippool',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_ippool']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": "False"},
        "firewall_ippool": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "arp-intf": {"required": False, "type": "str"},
                "arp-reply": {"required": False, "type": "str",
                              "choices": ["disable", "enable"]},
                "associated-interface": {"required": False, "type": "str"},
                "block-size": {"required": False, "type": "int"},
                "comments": {"required": False, "type": "str"},
                "endip": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "num-blocks-per-user": {"required": False, "type": "int"},
                "pba-timeout": {"required": False, "type": "int"},
                "permit-any-host": {"required": False, "type": "str",
                                    "choices": ["disable", "enable"]},
                "source-endip": {"required": False, "type": "str"},
                "source-startip": {"required": False, "type": "str"},
                "startip": {"required": False, "type": "str"},
                "type": {"required": False, "type": "str",
                         "choices": ["overload", "one-to-one", "fixed-port-range",
                                     "port-block-allocation"]}

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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
