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
module: fortios_firewall_shaping_policy
short_description: Configure shaping policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and shaping_policy category.
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
            - FortiOS or FortiGate ip adress.
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
    firewall_shaping_policy:
        description:
            - Configure shaping policies.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            app-category:
                description:
                    - IDs of one or more application categories that this shaper applies application control traffic shaping to.
                suboptions:
                    id:
                        description:
                            - Category IDs.
                        required: true
            application:
                description:
                    - IDs of one or more applications that this shaper applies application control traffic shaping to.
                suboptions:
                    id:
                        description:
                            - Application IDs.
                        required: true
            class-id:
                description:
                    - Traffic class ID.
            comment:
                description:
                    - Comments.
            dstaddr:
                description:
                    - IPv4 destination address and address group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            dstaddr6:
                description:
                    - IPv6 destination address and address group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            dstintf:
                description:
                    - One or more outgoing (egress) interfaces.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            groups:
                description:
                    - Apply this traffic shaping policy to user groups that have authenticated with the FortiGate.
                suboptions:
                    name:
                        description:
                            - Group name. Source user.group.name.
                        required: true
            id:
                description:
                    - Shaping policy ID.
                required: true
            internet-service:
                description:
                    - Enable/disable use of Internet Services for this policy. If enabled, destination address and service are not used.
                choices:
                    - enable
                    - disable
            internet-service-custom:
                description:
                    - Custom Internet Service name.
                suboptions:
                    name:
                        description:
                            - Custom Internet Service name. Source firewall.internet-service-custom.name.
                        required: true
            internet-service-id:
                description:
                    - Internet Service ID.
                suboptions:
                    id:
                        description:
                            - Internet Service ID. Source firewall.internet-service.id.
                        required: true
            internet-service-src:
                description:
                    - Enable/disable use of Internet Services in source for this policy. If enabled, source address is not used.
                choices:
                    - enable
                    - disable
            internet-service-src-custom:
                description:
                    - Custom Internet Service source name.
                suboptions:
                    name:
                        description:
                            - Custom Internet Service name. Source firewall.internet-service-custom.name.
                        required: true
            internet-service-src-id:
                description:
                    - Internet Service source ID.
                suboptions:
                    id:
                        description:
                            - Internet Service ID. Source firewall.internet-service.id.
                        required: true
            ip-version:
                description:
                    - Apply this traffic shaping policy to IPv4 or IPv6 traffic.
                choices:
                    - 4
                    - 6
            per-ip-shaper:
                description:
                    - Per-IP traffic shaper to apply with this policy. Source firewall.shaper.per-ip-shaper.name.
            schedule:
                description:
                    - Schedule name. Source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name.
            service:
                description:
                    - Service and service group names.
                suboptions:
                    name:
                        description:
                            - Service name. Source firewall.service.custom.name firewall.service.group.name.
                        required: true
            srcaddr:
                description:
                    - IPv4 source address and address group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            srcaddr6:
                description:
                    - IPv6 source address and address group names.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address6.name firewall.addrgrp6.name.
                        required: true
            status:
                description:
                    - Enable/disable this traffic shaping policy.
                choices:
                    - enable
                    - disable
            traffic-shaper:
                description:
                    - Traffic shaper to apply to traffic forwarded by the firewall policy. Source firewall.shaper.traffic-shaper.name.
            traffic-shaper-reverse:
                description:
                    - Traffic shaper to apply to response traffic received by the firewall policy. Source firewall.shaper.traffic-shaper.name.
            url-category:
                description:
                    - IDs of one or more FortiGuard Web Filtering categories that this shaper applies traffic shaping to.
                suboptions:
                    id:
                        description:
                            - URL category ID.
                        required: true
            users:
                description:
                    - Apply this traffic shaping policy to individual users that have authenticated with the FortiGate.
                suboptions:
                    name:
                        description:
                            - User name. Source user.local.name.
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
  - name: Configure shaping policies.
    fortios_firewall_shaping_policy:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_shaping_policy:
        state: "present"
        app-category:
         -
            id:  "4"
        application:
         -
            id:  "6"
        class-id: "7"
        comment: "Comments."
        dstaddr:
         -
            name: "default_name_10 (source firewall.address.name firewall.addrgrp.name)"
        dstaddr6:
         -
            name: "default_name_12 (source firewall.address6.name firewall.addrgrp6.name)"
        dstintf:
         -
            name: "default_name_14 (source system.interface.name system.zone.name)"
        groups:
         -
            name: "default_name_16 (source user.group.name)"
        id:  "17"
        internet-service: "enable"
        internet-service-custom:
         -
            name: "default_name_20 (source firewall.internet-service-custom.name)"
        internet-service-id:
         -
            id:  "22 (source firewall.internet-service.id)"
        internet-service-src: "enable"
        internet-service-src-custom:
         -
            name: "default_name_25 (source firewall.internet-service-custom.name)"
        internet-service-src-id:
         -
            id:  "27 (source firewall.internet-service.id)"
        ip-version: "4"
        per-ip-shaper: "<your_own_value> (source firewall.shaper.per-ip-shaper.name)"
        schedule: "<your_own_value> (source firewall.schedule.onetime.name firewall.schedule.recurring.name firewall.schedule.group.name)"
        service:
         -
            name: "default_name_32 (source firewall.service.custom.name firewall.service.group.name)"
        srcaddr:
         -
            name: "default_name_34 (source firewall.address.name firewall.addrgrp.name)"
        srcaddr6:
         -
            name: "default_name_36 (source firewall.address6.name firewall.addrgrp6.name)"
        status: "enable"
        traffic-shaper: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
        traffic-shaper-reverse: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
        url-category:
         -
            id:  "41"
        users:
         -
            name: "default_name_43 (source user.local.name)"
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


def filter_firewall_shaping_policy_data(json):
    option_list = ['app-category', 'application', 'class-id',
                   'comment', 'dstaddr', 'dstaddr6',
                   'dstintf', 'groups', 'id',
                   'internet-service', 'internet-service-custom', 'internet-service-id',
                   'internet-service-src', 'internet-service-src-custom', 'internet-service-src-id',
                   'ip-version', 'per-ip-shaper', 'schedule',
                   'service', 'srcaddr', 'srcaddr6',
                   'status', 'traffic-shaper', 'traffic-shaper-reverse',
                   'url-category', 'users']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_shaping_policy(data, fos):
    vdom = data['vdom']
    firewall_shaping_policy_data = data['firewall_shaping_policy']
    filtered_data = filter_firewall_shaping_policy_data(firewall_shaping_policy_data)
    if firewall_shaping_policy_data['state'] == "present":
        return fos.set('firewall',
                       'shaping-policy',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_shaping_policy_data['state'] == "absent":
        return fos.delete('firewall',
                          'shaping-policy',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_shaping_policy']
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
        "https": {"required": False, "type": "bool", "default": True},
        "firewall_shaping_policy": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "app-category": {"required": False, "type": "list",
                                 "options": {
                                     "id": {"required": True, "type": "int"}
                                 }},
                "application": {"required": False, "type": "list",
                                "options": {
                                    "id": {"required": True, "type": "int"}
                                }},
                "class-id": {"required": False, "type": "int"},
                "comment": {"required": False, "type": "str"},
                "dstaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "dstaddr6": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "dstintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "groups": {"required": False, "type": "list",
                           "options": {
                               "name": {"required": True, "type": "str"}
                           }},
                "id": {"required": True, "type": "int"},
                "internet-service": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "internet-service-custom": {"required": False, "type": "list",
                                            "options": {
                                                "name": {"required": True, "type": "str"}
                                            }},
                "internet-service-id": {"required": False, "type": "list",
                                        "options": {
                                            "id": {"required": True, "type": "int"}
                                        }},
                "internet-service-src": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "internet-service-src-custom": {"required": False, "type": "list",
                                                "options": {
                                                    "name": {"required": True, "type": "str"}
                                                }},
                "internet-service-src-id": {"required": False, "type": "list",
                                            "options": {
                                                "id": {"required": True, "type": "int"}
                                            }},
                "ip-version": {"required": False, "type": "str",
                               "choices": ["4", "6"]},
                "per-ip-shaper": {"required": False, "type": "str"},
                "schedule": {"required": False, "type": "str"},
                "service": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "srcaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "srcaddr6": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "traffic-shaper": {"required": False, "type": "str"},
                "traffic-shaper-reverse": {"required": False, "type": "str"},
                "url-category": {"required": False, "type": "list",
                                 "options": {
                                     "id": {"required": True, "type": "int"}
                                 }},
                "users": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }}

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
