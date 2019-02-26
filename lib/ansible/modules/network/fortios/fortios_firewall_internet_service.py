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
module: fortios_firewall_internet_service
short_description: Show Internet Service application in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and internet_service category.
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
    firewall_internet_service:
        description:
            - Show Internet Service application.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            database:
                description:
                    - Database name this Internet Service belongs to.
                choices:
                    - isdb
                    - irdb
            direction:
                description:
                    - How this service may be used in a firewall policy (source, destination or both).
                choices:
                    - src
                    - dst
                    - both
            entry:
                description:
                    - Entries in the Internet Service database.
                suboptions:
                    id:
                        description:
                            - Entry ID.
                        required: true
                    ip-number:
                        description:
                            - Total number of IP addresses.
                    ip-range-number:
                        description:
                            - Total number of IP ranges.
                    port:
                        description:
                            - Integer value for the TCP/IP port (0 - 65535).
                    protocol:
                        description:
                            - Integer value for the protocol type as defined by IANA (0 - 255).
            icon-id:
                description:
                    - Icon ID of Internet Service.
            id:
                description:
                    - Internet Service ID.
                required: true
            name:
                description:
                    - Internet Service name.
            offset:
                description:
                    - Offset of Internet Service ID.
            reputation:
                description:
                    - Reputation level of the Internet Service.
            sld-id:
                description:
                    - Second Level Domain.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Show Internet Service application.
    fortios_firewall_internet_service:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_internet_service:
        state: "present"
        database: "isdb"
        direction: "src"
        entry:
         -
            id:  "6"
            ip-number: "7"
            ip-range-number: "8"
            port: "9"
            protocol: "10"
        icon-id: "11"
        id:  "12"
        name: "default_name_13"
        offset: "14"
        reputation: "15"
        sld-id: "16"
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


def filter_firewall_internet_service_data(json):
    option_list = ['database', 'direction', 'entry',
                   'icon-id', 'id', 'name',
                   'offset', 'reputation', 'sld-id']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_internet_service(data, fos):
    vdom = data['vdom']
    firewall_internet_service_data = data['firewall_internet_service']
    filtered_data = filter_firewall_internet_service_data(firewall_internet_service_data)
    if firewall_internet_service_data['state'] == "present":
        return fos.set('firewall',
                       'internet-service',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_internet_service_data['state'] == "absent":
        return fos.delete('firewall',
                          'internet-service',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_internet_service']
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
        "firewall_internet_service": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "database": {"required": False, "type": "str",
                             "choices": ["isdb", "irdb"]},
                "direction": {"required": False, "type": "str",
                              "choices": ["src", "dst", "both"]},
                "entry": {"required": False, "type": "list",
                          "options": {
                              "id": {"required": True, "type": "int"},
                              "ip-number": {"required": False, "type": "int"},
                              "ip-range-number": {"required": False, "type": "int"},
                              "port": {"required": False, "type": "int"},
                              "protocol": {"required": False, "type": "int"}
                          }},
                "icon-id": {"required": False, "type": "int"},
                "id": {"required": True, "type": "int"},
                "name": {"required": False, "type": "str"},
                "offset": {"required": False, "type": "int"},
                "reputation": {"required": False, "type": "int"},
                "sld-id": {"required": False, "type": "int"}

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
