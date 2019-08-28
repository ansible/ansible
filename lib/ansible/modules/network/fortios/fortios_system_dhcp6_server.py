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
module: fortios_system_dhcp6_server
short_description: Configure DHCPv6 servers in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system_dhcp6 feature and server category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.9"
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
    state:
        description:
            - Indicates whether to create or remove the object.
        type: str
        required: true
        choices:
            - present
            - absent
    system_dhcp6_server:
        description:
            - Configure DHCPv6 servers.
        default: null
        type: dict
        suboptions:
            dns_search_list:
                description:
                    - DNS search list options.
                type: str
                choices:
                    - delegated
                    - specify
            dns_server1:
                description:
                    - DNS server 1.
                type: str
            dns_server2:
                description:
                    - DNS server 2.
                type: str
            dns_server3:
                description:
                    - DNS server 3.
                type: str
            dns_service:
                description:
                    -  Options for assigning DNS servers to DHCPv6 clients.
                type: str
                choices:
                    - delegated
                    - default
                    - specify
            domain:
                description:
                    - Domain name suffix for the IP addresses that the DHCP server assigns to clients.
                type: str
            id:
                description:
                    - ID.
                required: true
                type: int
            interface:
                description:
                    - DHCP server can assign IP configurations to clients connected to this interface. Source system.interface.name.
                type: str
            ip_mode:
                description:
                    - Method used to assign client IP.
                type: str
                choices:
                    - range
                    - delegated
            ip_range:
                description:
                    - DHCP IP range configuration.
                type: list
                suboptions:
                    end_ip:
                        description:
                            - End of IP range.
                        type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    start_ip:
                        description:
                            - Start of IP range.
                        type: str
            lease_time:
                description:
                    - Lease time in seconds, 0 means unlimited.
                type: int
            option1:
                description:
                    - Option 1.
                type: str
            option2:
                description:
                    - Option 2.
                type: str
            option3:
                description:
                    - Option 3.
                type: str
            prefix_range:
                description:
                    - DHCP prefix configuration.
                type: list
                suboptions:
                    end_prefix:
                        description:
                            - End of prefix range.
                        type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    prefix_length:
                        description:
                            - Prefix length.
                        type: int
                    start_prefix:
                        description:
                            - Start of prefix range.
                        type: str
            rapid_commit:
                description:
                    - Enable/disable allow/disallow rapid commit.
                type: str
                choices:
                    - disable
                    - enable
            status:
                description:
                    - Enable/disable this DHCPv6 configuration.
                type: str
                choices:
                    - disable
                    - enable
            subnet:
                description:
                    - Subnet or subnet-id if the IP mode is delegated.
                type: str
            upstream_interface:
                description:
                    - Interface name from where delegated information is provided. Source system.interface.name.
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
  - name: Configure DHCPv6 servers.
    fortios_system_dhcp6_server:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_dhcp6_server:
        dns_search_list: "delegated"
        dns_server1: "<your_own_value>"
        dns_server2: "<your_own_value>"
        dns_server3: "<your_own_value>"
        dns_service: "delegated"
        domain: "<your_own_value>"
        id:  "9"
        interface: "<your_own_value> (source system.interface.name)"
        ip_mode: "range"
        ip_range:
         -
            end_ip: "<your_own_value>"
            id:  "14"
            start_ip: "<your_own_value>"
        lease_time: "16"
        option1: "<your_own_value>"
        option2: "<your_own_value>"
        option3: "<your_own_value>"
        prefix_range:
         -
            end_prefix: "<your_own_value>"
            id:  "22"
            prefix_length: "23"
            start_prefix: "<your_own_value>"
        rapid_commit: "disable"
        status: "disable"
        subnet: "<your_own_value>"
        upstream_interface: "<your_own_value> (source system.interface.name)"
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


def filter_system_dhcp6_server_data(json):
    option_list = ['dns_search_list', 'dns_server1', 'dns_server2',
                   'dns_server3', 'dns_service', 'domain',
                   'id', 'interface', 'ip_mode',
                   'ip_range', 'lease_time', 'option1',
                   'option2', 'option3', 'prefix_range',
                   'rapid_commit', 'status', 'subnet',
                   'upstream_interface']
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


def system_dhcp6_server(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_dhcp6_server_data = data['system_dhcp6_server']
    filtered_data = underscore_to_hyphen(filter_system_dhcp6_server_data(system_dhcp6_server_data))

    if state == "present":
        return fos.set('system.dhcp6',
                       'server',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system.dhcp6',
                          'server',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system_dhcp6(data, fos):

    if data['system_dhcp6_server']:
        resp = system_dhcp6_server(data, fos)

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
        "state": {"required": True, "type": "str",
                  "choices": ["present", "absent"]},
        "system_dhcp6_server": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "dns_search_list": {"required": False, "type": "str",
                                    "choices": ["delegated", "specify"]},
                "dns_server1": {"required": False, "type": "str"},
                "dns_server2": {"required": False, "type": "str"},
                "dns_server3": {"required": False, "type": "str"},
                "dns_service": {"required": False, "type": "str",
                                "choices": ["delegated", "default", "specify"]},
                "domain": {"required": False, "type": "str"},
                "id": {"required": True, "type": "int"},
                "interface": {"required": False, "type": "str"},
                "ip_mode": {"required": False, "type": "str",
                            "choices": ["range", "delegated"]},
                "ip_range": {"required": False, "type": "list",
                             "options": {
                                 "end_ip": {"required": False, "type": "str"},
                                 "id": {"required": True, "type": "int"},
                                 "start_ip": {"required": False, "type": "str"}
                             }},
                "lease_time": {"required": False, "type": "int"},
                "option1": {"required": False, "type": "str"},
                "option2": {"required": False, "type": "str"},
                "option3": {"required": False, "type": "str"},
                "prefix_range": {"required": False, "type": "list",
                                 "options": {
                                     "end_prefix": {"required": False, "type": "str"},
                                     "id": {"required": True, "type": "int"},
                                     "prefix_length": {"required": False, "type": "int"},
                                     "start_prefix": {"required": False, "type": "str"}
                                 }},
                "rapid_commit": {"required": False, "type": "str",
                                 "choices": ["disable", "enable"]},
                "status": {"required": False, "type": "str",
                           "choices": ["disable", "enable"]},
                "subnet": {"required": False, "type": "str"},
                "upstream_interface": {"required": False, "type": "str"}

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

            is_error, has_changed, result = fortios_system_dhcp6(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system_dhcp6(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
