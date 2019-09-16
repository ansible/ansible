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
module: fortios_system_dns_database
short_description: Configure DNS databases in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and dns_database category.
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
    system_dns_database:
        description:
            - Configure DNS databases.
        default: null
        type: dict
        suboptions:
            allow_transfer:
                description:
                    - DNS zone transfer IP address list.
                type: str
            authoritative:
                description:
                    - Enable/disable authoritative zone.
                type: str
                choices:
                    - enable
                    - disable
            contact:
                description:
                    - Email address of the administrator for this zone.
                      You can specify only the username (e.g. admin) or full email address (e.g. admin@test.com)
                      When using a simple username, the domain of the email will be this zone.
                type: str
            dns_entry:
                description:
                    - DNS entry.
                type: list
                suboptions:
                    canonical_name:
                        description:
                            - Canonical name of the host.
                        type: str
                    hostname:
                        description:
                            - Name of the host.
                        type: str
                    id:
                        description:
                            - DNS entry ID.
                        required: true
                        type: int
                    ip:
                        description:
                            - IPv4 address of the host.
                        type: str
                    ipv6:
                        description:
                            - IPv6 address of the host.
                        type: str
                    preference:
                        description:
                            - DNS entry preference, 0 is the highest preference (0 - 65535)
                        type: int
                    status:
                        description:
                            - Enable/disable resource record status.
                        type: str
                        choices:
                            - enable
                            - disable
                    ttl:
                        description:
                            - Time-to-live for this entry (0 to 2147483647 sec).
                        type: int
                    type:
                        description:
                            - Resource record type.
                        type: str
                        choices:
                            - A
                            - NS
                            - CNAME
                            - MX
                            - AAAA
                            - PTR
                            - PTR_V6
            domain:
                description:
                    - Domain name.
                type: str
            forwarder:
                description:
                    - DNS zone forwarder IP address list.
                type: str
            ip_master:
                description:
                    - IP address of master DNS server. Entries in this master DNS server and imported into the DNS zone.
                type: str
            name:
                description:
                    - Zone name.
                required: true
                type: str
            primary_name:
                description:
                    - Domain name of the default DNS server for this zone.
                type: str
            source_ip:
                description:
                    - Source IP for forwarding to DNS server.
                type: str
            status:
                description:
                    - Enable/disable this DNS zone.
                type: str
                choices:
                    - enable
                    - disable
            ttl:
                description:
                    - Default time-to-live value for the entries of this DNS zone (0 - 2147483647 sec).
                type: int
            type:
                description:
                    - Zone type (master to manage entries directly, slave to import entries from other zones).
                type: str
                choices:
                    - master
                    - slave
            view:
                description:
                    - Zone view (public to serve public clients, shadow to serve internal clients).
                type: str
                choices:
                    - shadow
                    - public
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
  - name: Configure DNS databases.
    fortios_system_dns_database:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_dns_database:
        allow_transfer: "<your_own_value>"
        authoritative: "enable"
        contact: "<your_own_value>"
        dns_entry:
         -
            canonical_name: "<your_own_value>"
            hostname: "myhostname"
            id:  "9"
            ip: "<your_own_value>"
            ipv6: "<your_own_value>"
            preference: "12"
            status: "enable"
            ttl: "14"
            type: "A"
        domain: "<your_own_value>"
        forwarder: "<your_own_value>"
        ip_master: "<your_own_value>"
        name: "default_name_19"
        primary_name: "<your_own_value>"
        source_ip: "84.230.14.43"
        status: "enable"
        ttl: "23"
        type: "master"
        view: "shadow"
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


def filter_system_dns_database_data(json):
    option_list = ['allow_transfer', 'authoritative', 'contact',
                   'dns_entry', 'domain', 'forwarder',
                   'ip_master', 'name', 'primary_name',
                   'source_ip', 'status', 'ttl',
                   'type', 'view']
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


def system_dns_database(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_dns_database_data = data['system_dns_database']
    filtered_data = underscore_to_hyphen(filter_system_dns_database_data(system_dns_database_data))

    if state == "present":
        return fos.set('system',
                       'dns-database',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'dns-database',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_dns_database']:
        resp = system_dns_database(data, fos)

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
        "system_dns_database": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "allow_transfer": {"required": False, "type": "str"},
                "authoritative": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "contact": {"required": False, "type": "str"},
                "dns_entry": {"required": False, "type": "list",
                              "options": {
                                  "canonical_name": {"required": False, "type": "str"},
                                  "hostname": {"required": False, "type": "str"},
                                  "id": {"required": True, "type": "int"},
                                  "ip": {"required": False, "type": "str"},
                                  "ipv6": {"required": False, "type": "str"},
                                  "preference": {"required": False, "type": "int"},
                                  "status": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                                  "ttl": {"required": False, "type": "int"},
                                  "type": {"required": False, "type": "str",
                                           "choices": ["A", "NS", "CNAME",
                                                       "MX", "AAAA", "PTR",
                                                       "PTR_V6"]}
                              }},
                "domain": {"required": False, "type": "str"},
                "forwarder": {"required": False, "type": "str"},
                "ip_master": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "primary_name": {"required": False, "type": "str"},
                "source_ip": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "ttl": {"required": False, "type": "int"},
                "type": {"required": False, "type": "str",
                         "choices": ["master", "slave"]},
                "view": {"required": False, "type": "str",
                         "choices": ["shadow", "public"]}

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

            is_error, has_changed, result = fortios_system(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
