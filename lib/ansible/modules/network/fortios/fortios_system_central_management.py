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
module: fortios_system_central_management
short_description: Configure central management.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure system feature and central_management category.
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
    system_central_management:
        description:
            - Configure central management.
        default: null
        suboptions:
            allow-monitor:
                description:
                    - Enable/disable allowing the central management server to remotely monitor this FortiGate
                choices:
                    - enable
                    - disable
            allow-push-configuration:
                description:
                    - Enable/disable allowing the central management server to push configuration changes to this FortiGate.
                choices:
                    - enable
                    - disable
            allow-push-firmware:
                description:
                    - Enable/disable allowing the central management server to push firmware updates to this FortiGate.
                choices:
                    - enable
                    - disable
            allow-remote-firmware-upgrade:
                description:
                    - Enable/disable remotely upgrading the firmware on this FortiGate from the central management server.
                choices:
                    - enable
                    - disable
            enc-algorithm:
                description:
                    - Encryption strength for communications between the FortiGate and central management.
                choices:
                    - default
                    - high
                    - low
            fmg:
                description:
                    - IP address or FQDN of the FortiManager.
            fmg-source-ip:
                description:
                    - IPv4 source address that this FortiGate uses when communicating with FortiManager.
            fmg-source-ip6:
                description:
                    - IPv6 source address that this FortiGate uses when communicating with FortiManager.
            include-default-servers:
                description:
                    - Enable/disable inclusion of public FortiGuard servers in the override server list.
                choices:
                    - enable
                    - disable
            mode:
                description:
                    - Central management mode.
                choices:
                    - normal
                    - backup
            schedule-config-restore:
                description:
                    - Enable/disable allowing the central management server to restore the configuration of this FortiGate.
                choices:
                    - enable
                    - disable
            schedule-script-restore:
                description:
                    - Enable/disable allowing the central management server to restore the scripts stored on this FortiGate.
                choices:
                    - enable
                    - disable
            serial-number:
                description:
                    - Serial number.
            server-list:
                description:
                    - Additional servers that the FortiGate can use for updates (for AV, IPS, updates) and ratings (for web filter and antispam ratings)
                      servers.
                suboptions:
                    addr-type:
                        description:
                            - Indicate whether the FortiGate communicates with the override server using an IPv4 address, an IPv6 address or a FQDN.
                        choices:
                            - ipv4
                            - ipv6
                            - fqdn
                    fqdn:
                        description:
                            - FQDN address of override server.
                    id:
                        description:
                            - ID.
                        required: true
                    server-address:
                        description:
                            - IPv4 address of override server.
                    server-address6:
                        description:
                            - IPv6 address of override server.
                    server-type:
                        description:
                            - FortiGuard service type.
                        choices:
                            - update
                            - rating
            type:
                description:
                    - Central management type.
                choices:
                    - fortimanager
                    - fortiguard
                    - none
            vdom:
                description:
                    - Virtual domain (VDOM) name to use when communicating with FortiManager. Source system.vdom.name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure central management.
    fortios_system_central_management:
      host:  "{{  host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{  vdom }}"
      system_central_management:
        allow-monitor: "enable"
        allow-push-configuration: "enable"
        allow-push-firmware: "enable"
        allow-remote-firmware-upgrade: "enable"
        enc-algorithm: "default"
        fmg: "<your_own_value>"
        fmg-source-ip: "<your_own_value>"
        fmg-source-ip6: "<your_own_value>"
        include-default-servers: "enable"
        mode: "normal"
        schedule-config-restore: "enable"
        schedule-script-restore: "enable"
        serial-number: "<your_own_value>"
        server-list:
         -
            addr-type: "ipv4"
            fqdn: "<your_own_value>"
            id:  "19"
            server-address: "<your_own_value>"
            server-address6: "<your_own_value>"
            server-type: "update"
        type: "fortimanager"
        vdom: "<your_own_value> (source system.vdom.name)"
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


def filter_system_central_management_data(json):
    option_list = ['allow-monitor', 'allow-push-configuration', 'allow-push-firmware',
                   'allow-remote-firmware-upgrade', 'enc-algorithm', 'fmg',
                   'fmg-source-ip', 'fmg-source-ip6', 'include-default-servers',
                   'mode', 'schedule-config-restore', 'schedule-script-restore',
                   'serial-number', 'server-list', 'type',
                   'vdom']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def system_central_management(data, fos):
    vdom = data['vdom']
    system_central_management_data = data['system_central_management']
    filtered_data = filter_system_central_management_data(
        system_central_management_data)
    return fos.set('system',
                   'central-management',
                   data=filtered_data,
                   vdom=vdom)


def fortios_system(data, fos):
    login(data)

    methodlist = ['system_central_management']
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
        "system_central_management": {
            "required": False, "type": "dict",
            "options": {
                "allow-monitor": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "allow-push-configuration": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "allow-push-firmware": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "allow-remote-firmware-upgrade": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "enc-algorithm": {"required": False, "type": "str",
                                  "choices": ["default", "high", "low"]},
                "fmg": {"required": False, "type": "str"},
                "fmg-source-ip": {"required": False, "type": "str"},
                "fmg-source-ip6": {"required": False, "type": "str"},
                "include-default-servers": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "mode": {"required": False, "type": "str",
                         "choices": ["normal", "backup"]},
                "schedule-config-restore": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "schedule-script-restore": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "serial-number": {"required": False, "type": "str"},
                "server-list": {"required": False, "type": "list",
                                "options": {
                                    "addr-type": {"required": False, "type": "str",
                                                  "choices": ["ipv4", "ipv6", "fqdn"]},
                                    "fqdn": {"required": False, "type": "str"},
                                    "id": {"required": True, "type": "int"},
                                    "server-address": {"required": False, "type": "str"},
                                    "server-address6": {"required": False, "type": "str"},
                                    "server-type": {"required": False, "type": "str",
                                                    "choices": ["update", "rating"]}
                                }},
                "type": {"required": False, "type": "str",
                         "choices": ["fortimanager", "fortiguard", "none"]},
                "vdom": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_system(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
