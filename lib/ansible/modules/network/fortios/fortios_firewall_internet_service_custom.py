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
module: fortios_firewall_internet_service_custom
short_description: Configure custom Internet Services in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and internet_service_custom category.
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
    firewall_internet_service_custom:
        description:
            - Configure custom Internet Services.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            comment:
                description:
                    - Comment.
            disable-entry:
                description:
                    - Disable entries in the Internet Service database.
                suboptions:
                    id:
                        description:
                            - Disable entry ID.
                        required: true
                    ip-range:
                        description:
                            - IP ranges in the disable entry.
                        suboptions:
                            end-ip:
                                description:
                                    - End IP address.
                            id:
                                description:
                                    - Disable entry range ID.
                                required: true
                            start-ip:
                                description:
                                    - Start IP address.
                    port:
                        description:
                            - Integer value for the TCP/IP port (0 - 65535).
                    protocol:
                        description:
                            - Integer value for the protocol type as defined by IANA (0 - 255).
            entry:
                description:
                    - Entries added to the Internet Service database and custom database.
                suboptions:
                    dst:
                        description:
                            - Destination address or address group name.
                        suboptions:
                            name:
                                description:
                                    - Select the destination address or address group object from available options. Source firewall.address.name firewall
                                      .addrgrp.name.
                                required: true
                    id:
                        description:
                            - Entry ID(1-255).
                        required: true
                    port-range:
                        description:
                            - Port ranges in the custom entry.
                        suboptions:
                            end-port:
                                description:
                                    - Integer value for ending TCP/UDP/SCTP destination port in range (1 to 65535).
                            id:
                                description:
                                    - Custom entry port range ID.
                                required: true
                            start-port:
                                description:
                                    - Integer value for starting TCP/UDP/SCTP destination port in range (1 to 65535).
                    protocol:
                        description:
                            - Integer value for the protocol type as defined by IANA (0 - 255).
            master-service-id:
                description:
                    - Internet Service ID in the Internet Service database. Source firewall.internet-service.id.
            name:
                description:
                    - Internet Service name.
                required: true
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure custom Internet Services.
    fortios_firewall_internet_service_custom:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_internet_service_custom:
        state: "present"
        comment: "Comment."
        disable-entry:
         -
            id:  "5"
            ip-range:
             -
                end-ip: "<your_own_value>"
                id:  "8"
                start-ip: "<your_own_value>"
            port: "10"
            protocol: "11"
        entry:
         -
            dst:
             -
                name: "default_name_14 (source firewall.address.name firewall.addrgrp.name)"
            id:  "15"
            port-range:
             -
                end-port: "17"
                id:  "18"
                start-port: "19"
            protocol: "20"
        master-service-id: "21 (source firewall.internet-service.id)"
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


def filter_firewall_internet_service_custom_data(json):
    option_list = ['comment', 'disable-entry', 'entry',
                   'master-service-id', 'name']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_internet_service_custom(data, fos):
    vdom = data['vdom']
    firewall_internet_service_custom_data = data['firewall_internet_service_custom']
    filtered_data = filter_firewall_internet_service_custom_data(firewall_internet_service_custom_data)
    if firewall_internet_service_custom_data['state'] == "present":
        return fos.set('firewall',
                       'internet-service-custom',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_internet_service_custom_data['state'] == "absent":
        return fos.delete('firewall',
                          'internet-service-custom',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_internet_service_custom']
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
        "firewall_internet_service_custom": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "disable-entry": {"required": False, "type": "list",
                                  "options": {
                                      "id": {"required": True, "type": "int"},
                                      "ip-range": {"required": False, "type": "list",
                                                   "options": {
                                                       "end-ip": {"required": False, "type": "str"},
                                                       "id": {"required": True, "type": "int"},
                                                       "start-ip": {"required": False, "type": "str"}
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
                              "port-range": {"required": False, "type": "list",
                                             "options": {
                                                 "end-port": {"required": False, "type": "int"},
                                                 "id": {"required": True, "type": "int"},
                                                 "start-port": {"required": False, "type": "int"}
                                             }},
                              "protocol": {"required": False, "type": "int"}
                          }},
                "master-service-id": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"}

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
