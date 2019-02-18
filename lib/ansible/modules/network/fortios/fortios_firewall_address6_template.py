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
module: fortios_firewall_address6_template
short_description: Configure IPv6 address templates in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and address6_template category.
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
    firewall_address6_template:
        description:
            - Configure IPv6 address templates.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            ip6:
                description:
                    - IPv6 address prefix.
            name:
                description:
                    - IPv6 address template name.
                required: true
            subnet-segment:
                description:
                    - IPv6 subnet segments.
                suboptions:
                    bits:
                        description:
                            - Number of bits.
                    exclusive:
                        description:
                            - Enable/disable exclusive value.
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - Subnet segment ID.
                        required: true
                    name:
                        description:
                            - Subnet segment name.
                    values:
                        description:
                            - Subnet segment values.
                        suboptions:
                            name:
                                description:
                                    - Subnet segment value name.
                                required: true
                            value:
                                description:
                                    - Subnet segment value.
            subnet-segment-count:
                description:
                    - Number of IPv6 subnet segments.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv6 address templates.
    fortios_firewall_address6_template:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_address6_template:
        state: "present"
        ip6: "<your_own_value>"
        name: "default_name_4"
        subnet-segment:
         -
            bits: "6"
            exclusive: "enable"
            id:  "8"
            name: "default_name_9"
            values:
             -
                name: "default_name_11"
                value: "<your_own_value>"
        subnet-segment-count: "13"
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


def filter_firewall_address6_template_data(json):
    option_list = ['ip6', 'name', 'subnet-segment',
                   'subnet-segment-count']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_address6_template(data, fos):
    vdom = data['vdom']
    firewall_address6_template_data = data['firewall_address6_template']
    filtered_data = filter_firewall_address6_template_data(firewall_address6_template_data)
    if firewall_address6_template_data['state'] == "present":
        return fos.set('firewall',
                       'address6-template',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_address6_template_data['state'] == "absent":
        return fos.delete('firewall',
                          'address6-template',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_address6_template']
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
        "firewall_address6_template": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "ip6": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "subnet-segment": {"required": False, "type": "list",
                                   "options": {
                                       "bits": {"required": False, "type": "int"},
                                       "exclusive": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                       "id": {"required": True, "type": "int"},
                                       "name": {"required": False, "type": "str"},
                                       "values": {"required": False, "type": "list",
                                                  "options": {
                                                      "name": {"required": True, "type": "str"},
                                                      "value": {"required": False, "type": "str"}
                                                  }}
                                   }},
                "subnet-segment-count": {"required": False, "type": "int"}

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
