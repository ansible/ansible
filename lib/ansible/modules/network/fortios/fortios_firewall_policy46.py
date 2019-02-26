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
module: fortios_firewall_policy46
short_description: Configure IPv4 to IPv6 policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and policy46 category.
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
    firewall_policy46:
        description:
            - Configure IPv4 to IPv6 policies.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            action:
                description:
                    - Accept or deny traffic matching the policy.
                choices:
                    - accept
                    - deny
            comments:
                description:
                    - Comment.
            dstaddr:
                description:
                    - Destination address objects.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.vip46.name firewall.vipgrp46.name.
                        required: true
            dstintf:
                description:
                    - Destination interface name. Source system.interface.name system.zone.name.
            fixedport:
                description:
                    - Enable/disable fixed port for this policy.
                choices:
                    - enable
                    - disable
            ippool:
                description:
                    - Enable/disable use of IP Pools for source NAT.
                choices:
                    - enable
                    - disable
            logtraffic:
                description:
                    - Enable/disable traffic logging for this policy.
                choices:
                    - enable
                    - disable
            per-ip-shaper:
                description:
                    - Per IP traffic shaper. Source firewall.shaper.per-ip-shaper.name.
            permit-any-host:
                description:
                    - Enable/disable allowing any host.
                choices:
                    - enable
                    - disable
            policyid:
                description:
                    - Policy ID.
                required: true
            poolname:
                description:
                    - IP Pool names.
                suboptions:
                    name:
                        description:
                            - IP pool name. Source firewall.ippool6.name.
                        required: true
            schedule:
                description:
                    - Schedule name. Source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name.
            service:
                description:
                    - Service name.
                suboptions:
                    name:
                        description:
                            - Service name. Source firewall.service.custom.name firewall.service.group.name.
                        required: true
            srcaddr:
                description:
                    - Source address objects.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            srcintf:
                description:
                    - Source interface name. Source system.zone.name system.interface.name.
            status:
                description:
                    - Enable/disable this policy.
                choices:
                    - enable
                    - disable
            tcp-mss-receiver:
                description:
                    - TCP Maximum Segment Size value of receiver (0 - 65535, default = 0)
            tcp-mss-sender:
                description:
                    - TCP Maximum Segment Size value of sender (0 - 65535, default = 0).
            traffic-shaper:
                description:
                    - Traffic shaper. Source firewall.shaper.traffic-shaper.name.
            traffic-shaper-reverse:
                description:
                    - Reverse traffic shaper. Source firewall.shaper.traffic-shaper.name.
            uuid:
                description:
                    - Universally Unique Identifier (UUID; automatically assigned but can be manually reset).
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv4 to IPv6 policies.
    fortios_firewall_policy46:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_policy46:
        state: "present"
        action: "accept"
        comments: "<your_own_value>"
        dstaddr:
         -
            name: "default_name_6 (source firewall.vip46.name firewall.vipgrp46.name)"
        dstintf: "<your_own_value> (source system.interface.name system.zone.name)"
        fixedport: "enable"
        ippool: "enable"
        logtraffic: "enable"
        per-ip-shaper: "<your_own_value> (source firewall.shaper.per-ip-shaper.name)"
        permit-any-host: "enable"
        policyid: "13"
        poolname:
         -
            name: "default_name_15 (source firewall.ippool6.name)"
        schedule: "<your_own_value> (source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name)"
        service:
         -
            name: "default_name_18 (source firewall.service.custom.name firewall.service.group.name)"
        srcaddr:
         -
            name: "default_name_20 (source firewall.address.name firewall.addrgrp.name)"
        srcintf: "<your_own_value> (source system.zone.name system.interface.name)"
        status: "enable"
        tcp-mss-receiver: "23"
        tcp-mss-sender: "24"
        traffic-shaper: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
        traffic-shaper-reverse: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
        uuid: "<your_own_value>"
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


def filter_firewall_policy46_data(json):
    option_list = ['action', 'comments', 'dstaddr',
                   'dstintf', 'fixedport', 'ippool',
                   'logtraffic', 'per-ip-shaper', 'permit-any-host',
                   'policyid', 'poolname', 'schedule',
                   'service', 'srcaddr', 'srcintf',
                   'status', 'tcp-mss-receiver', 'tcp-mss-sender',
                   'traffic-shaper', 'traffic-shaper-reverse', 'uuid']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_policy46(data, fos):
    vdom = data['vdom']
    firewall_policy46_data = data['firewall_policy46']
    filtered_data = filter_firewall_policy46_data(firewall_policy46_data)
    if firewall_policy46_data['state'] == "present":
        return fos.set('firewall',
                       'policy46',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_policy46_data['state'] == "absent":
        return fos.delete('firewall',
                          'policy46',
                          mkey=filtered_data['policyid'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_policy46']
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
        "firewall_policy46": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "action": {"required": False, "type": "str",
                           "choices": ["accept", "deny"]},
                "comments": {"required": False, "type": "str"},
                "dstaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "dstintf": {"required": False, "type": "str"},
                "fixedport": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "ippool": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "logtraffic": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "per-ip-shaper": {"required": False, "type": "str"},
                "permit-any-host": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "policyid": {"required": True, "type": "int"},
                "poolname": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "schedule": {"required": False, "type": "str"},
                "service": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "srcaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "srcintf": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "tcp-mss-receiver": {"required": False, "type": "int"},
                "tcp-mss-sender": {"required": False, "type": "int"},
                "traffic-shaper": {"required": False, "type": "str"},
                "traffic-shaper-reverse": {"required": False, "type": "str"},
                "uuid": {"required": False, "type": "str"}

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
