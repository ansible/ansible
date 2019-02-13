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
module: fortios_firewall_address
short_description: Configure IPv4 addresses.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and address category.
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
    firewall_address:
        description:
            - Configure IPv4 addresses.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            allow-routing:
                description:
                    - Enable/disable use of this address in the static route configuration.
                choices:
                    - enable
                    - disable
            associated-interface:
                description:
                    - Network interface associated with address. Source system.interface.name system.zone.name.
            cache-ttl:
                description:
                    - Defines the minimal TTL of individual IP addresses in FQDN cache measured in seconds.
            color:
                description:
                    - Color of icon on the GUI.
            comment:
                description:
                    - Comment.
            country:
                description:
                    - IP addresses associated to a specific country.
            end-ip:
                description:
                    - Final IP address (inclusive) in the range for the address.
            epg-name:
                description:
                    - Endpoint group name.
            filter:
                description:
                    - Match criteria filter.
            fqdn:
                description:
                    - Fully Qualified Domain Name address.
            list:
                description:
                    - IP address list.
                suboptions:
                    ip:
                        description:
                            - IP.
                        required: true
            name:
                description:
                    - Address name.
                required: true
            obj-id:
                description:
                    - Object ID for NSX.
            organization:
                description:
                    - "Organization domain name (Syntax: organization/domain)."
            policy-group:
                description:
                    - Policy group name.
            sdn:
                description:
                    - SDN.
                choices:
                    - aci
                    - aws
                    - azure
                    - gcp
                    - nsx
                    - nuage
                    - oci
            sdn-tag:
                description:
                    - SDN Tag.
            start-ip:
                description:
                    - First IP address (inclusive) in the range for the address.
            subnet:
                description:
                    - IP address and subnet mask of address.
            subnet-name:
                description:
                    - Subnet name.
            tagging:
                description:
                    - Config object tagging.
                suboptions:
                    category:
                        description:
                            - Tag category. Source system.object-tagging.category.
                    name:
                        description:
                            - Tagging entry name.
                        required: true
                    tags:
                        description:
                            - Tags.
                        suboptions:
                            name:
                                description:
                                    - Tag name. Source system.object-tagging.tags.name.
                                required: true
            tenant:
                description:
                    - Tenant.
            type:
                description:
                    - Type of address.
                choices:
                    - ipmask
                    - iprange
                    - fqdn
                    - geography
                    - wildcard
                    - wildcard-fqdn
                    - dynamic
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
            visibility:
                description:
                    - Enable/disable address visibility in the GUI.
                choices:
                    - enable
                    - disable
            wildcard:
                description:
                    - IP address and wildcard netmask.
            wildcard-fqdn:
                description:
                    - Fully Qualified Domain Name with wildcard characters.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv4 addresses.
    fortios_firewall_address:
      host:  "{{  host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{  vdom }}"
      firewall_address:
        state: "present"
        allow-routing: "enable"
        associated-interface: "<your_own_value> (source system.interface.name system.zone.name)"
        cache-ttl: "5"
        color: "6"
        comment: "Comment."
        country: "<your_own_value>"
        end-ip: "<your_own_value>"
        epg-name: "<your_own_value>"
        filter: "<your_own_value>"
        fqdn: "<your_own_value>"
        list:
         -
            ip: "<your_own_value>"
        name: "default_name_15"
        obj-id: "<your_own_value>"
        organization: "<your_own_value>"
        policy-group: "<your_own_value>"
        sdn: "aci"
        sdn-tag: "<your_own_value>"
        start-ip: "<your_own_value>"
        subnet: "<your_own_value>"
        subnet-name: "<your_own_value>"
        tagging:
         -
            category: "<your_own_value> (source system.object-tagging.category)"
            name: "default_name_26"
            tags:
             -
                name: "default_name_28 (source system.object-tagging.tags.name)"
        tenant: "<your_own_value>"
        type: "ipmask"
        uuid: "<your_own_value>"
        visibility: "enable"
        wildcard: "<your_own_value>"
        wildcard-fqdn: "<your_own_value>"
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


def filter_firewall_address_data(json):
    option_list = ['allow-routing', 'associated-interface', 'cache-ttl',
                   'color', 'comment', 'country',
                   'end-ip', 'epg-name', 'filter',
                   'fqdn', 'list', 'name',
                   'obj-id', 'organization', 'policy-group',
                   'sdn', 'sdn-tag', 'start-ip',
                   'subnet', 'subnet-name', 'tagging',
                   'tenant', 'type', 'uuid',
                   'visibility', 'wildcard', 'wildcard-fqdn']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_address(data, fos):
    vdom = data['vdom']
    firewall_address_data = data['firewall_address']
    filtered_data = filter_firewall_address_data(firewall_address_data)
    if firewall_address_data['state'] == "present":
        return fos.set('firewall',
                       'address',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_address_data['state'] == "absent":
        return fos.delete('firewall',
                          'address',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_address']
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
        "firewall_address": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "allow-routing": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "associated-interface": {"required": False, "type": "str"},
                "cache-ttl": {"required": False, "type": "int"},
                "color": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "country": {"required": False, "type": "str"},
                "end-ip": {"required": False, "type": "str"},
                "epg-name": {"required": False, "type": "str"},
                "filter": {"required": False, "type": "str"},
                "fqdn": {"required": False, "type": "str"},
                "list": {"required": False, "type": "list",
                         "options": {
                             "ip": {"required": True, "type": "str"}
                         }},
                "name": {"required": True, "type": "str"},
                "obj-id": {"required": False, "type": "str"},
                "organization": {"required": False, "type": "str"},
                "policy-group": {"required": False, "type": "str"},
                "sdn": {"required": False, "type": "str",
                        "choices": ["aci", "aws", "azure",
                                    "gcp", "nsx", "nuage",
                                    "oci"]},
                "sdn-tag": {"required": False, "type": "str"},
                "start-ip": {"required": False, "type": "str"},
                "subnet": {"required": False, "type": "str"},
                "subnet-name": {"required": False, "type": "str"},
                "tagging": {"required": False, "type": "list",
                            "options": {
                                "category": {"required": False, "type": "str"},
                                "name": {"required": True, "type": "str"},
                                "tags": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }}
                            }},
                "tenant": {"required": False, "type": "str"},
                "type": {"required": False, "type": "str",
                         "choices": ["ipmask", "iprange", "fqdn",
                                     "geography", "wildcard", "wildcard-fqdn",
                                     "dynamic"]},
                "uuid": {"required": False, "type": "str"},
                "visibility": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "wildcard": {"required": False, "type": "str"},
                "wildcard-fqdn": {"required": False, "type": "str"}

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
