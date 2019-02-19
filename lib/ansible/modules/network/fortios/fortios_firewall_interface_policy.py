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
module: fortios_firewall_interface_policy
short_description: Configure IPv4 interface policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and interface_policy category.
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
    firewall_interface_policy:
        description:
            - Configure IPv4 interface policies.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            address-type:
                description:
                    - Policy address type (IPv4 or IPv6).
                choices:
                    - ipv4
                    - ipv6
            application-list:
                description:
                    - Application list name. Source application.list.name.
            application-list-status:
                description:
                    - Enable/disable application control.
                choices:
                    - enable
                    - disable
            av-profile:
                description:
                    - Antivirus profile. Source antivirus.profile.name.
            av-profile-status:
                description:
                    - Enable/disable antivirus.
                choices:
                    - enable
                    - disable
            comments:
                description:
                    - Comments.
            dlp-sensor:
                description:
                    - DLP sensor name. Source dlp.sensor.name.
            dlp-sensor-status:
                description:
                    - Enable/disable DLP.
                choices:
                    - enable
                    - disable
            dsri:
                description:
                    - Enable/disable DSRI.
                choices:
                    - enable
                    - disable
            dstaddr:
                description:
                    - Address object to limit traffic monitoring to network traffic sent to the specified address or range.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            interface:
                description:
                    - Monitored interface name from available interfaces. Source system.zone.name system.interface.name.
            ips-sensor:
                description:
                    - IPS sensor name. Source ips.sensor.name.
            ips-sensor-status:
                description:
                    - Enable/disable IPS.
                choices:
                    - enable
                    - disable
            label:
                description:
                    - Label.
            logtraffic:
                description:
                    - "Logging type to be used in this policy (Options: all | utm | disable, Default: utm)."
                choices:
                    - all
                    - utm
                    - disable
            policyid:
                description:
                    - Policy ID.
                required: true
            scan-botnet-connections:
                description:
                    - Enable/disable scanning for connections to Botnet servers.
                choices:
                    - disable
                    - block
                    - monitor
            service:
                description:
                    - Service object from available options.
                suboptions:
                    name:
                        description:
                            - Service name. Source firewall.service.custom.name firewall.service.group.name.
                        required: true
            spamfilter-profile:
                description:
                    - Antispam profile. Source spamfilter.profile.name.
            spamfilter-profile-status:
                description:
                    - Enable/disable antispam.
                choices:
                    - enable
                    - disable
            srcaddr:
                description:
                    - Address object to limit traffic monitoring to network traffic sent from the specified address or range.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            status:
                description:
                    - Enable/disable this policy.
                choices:
                    - enable
                    - disable
            webfilter-profile:
                description:
                    - Web filter profile. Source webfilter.profile.name.
            webfilter-profile-status:
                description:
                    - Enable/disable web filtering.
                choices:
                    - enable
                    - disable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv4 interface policies.
    fortios_firewall_interface_policy:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_interface_policy:
        state: "present"
        address-type: "ipv4"
        application-list: "<your_own_value> (source application.list.name)"
        application-list-status: "enable"
        av-profile: "<your_own_value> (source antivirus.profile.name)"
        av-profile-status: "enable"
        comments: "<your_own_value>"
        dlp-sensor: "<your_own_value> (source dlp.sensor.name)"
        dlp-sensor-status: "enable"
        dsri: "enable"
        dstaddr:
         -
            name: "default_name_13 (source firewall.address.name firewall.addrgrp.name)"
        interface: "<your_own_value> (source system.zone.name system.interface.name)"
        ips-sensor: "<your_own_value> (source ips.sensor.name)"
        ips-sensor-status: "enable"
        label: "<your_own_value>"
        logtraffic: "all"
        policyid: "19"
        scan-botnet-connections: "disable"
        service:
         -
            name: "default_name_22 (source firewall.service.custom.name firewall.service.group.name)"
        spamfilter-profile: "<your_own_value> (source spamfilter.profile.name)"
        spamfilter-profile-status: "enable"
        srcaddr:
         -
            name: "default_name_26 (source firewall.address.name firewall.addrgrp.name)"
        status: "enable"
        webfilter-profile: "<your_own_value> (source webfilter.profile.name)"
        webfilter-profile-status: "enable"
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


def filter_firewall_interface_policy_data(json):
    option_list = ['address-type', 'application-list', 'application-list-status',
                   'av-profile', 'av-profile-status', 'comments',
                   'dlp-sensor', 'dlp-sensor-status', 'dsri',
                   'dstaddr', 'interface', 'ips-sensor',
                   'ips-sensor-status', 'label', 'logtraffic',
                   'policyid', 'scan-botnet-connections', 'service',
                   'spamfilter-profile', 'spamfilter-profile-status', 'srcaddr',
                   'status', 'webfilter-profile', 'webfilter-profile-status']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_interface_policy(data, fos):
    vdom = data['vdom']
    firewall_interface_policy_data = data['firewall_interface_policy']
    filtered_data = filter_firewall_interface_policy_data(firewall_interface_policy_data)
    if firewall_interface_policy_data['state'] == "present":
        return fos.set('firewall',
                       'interface-policy',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_interface_policy_data['state'] == "absent":
        return fos.delete('firewall',
                          'interface-policy',
                          mkey=filtered_data['policyid'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_interface_policy']
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
        "firewall_interface_policy": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "address-type": {"required": False, "type": "str",
                                 "choices": ["ipv4", "ipv6"]},
                "application-list": {"required": False, "type": "str"},
                "application-list-status": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "av-profile": {"required": False, "type": "str"},
                "av-profile-status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "comments": {"required": False, "type": "str"},
                "dlp-sensor": {"required": False, "type": "str"},
                "dlp-sensor-status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "dsri": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "dstaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "interface": {"required": False, "type": "str"},
                "ips-sensor": {"required": False, "type": "str"},
                "ips-sensor-status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "label": {"required": False, "type": "str"},
                "logtraffic": {"required": False, "type": "str",
                               "choices": ["all", "utm", "disable"]},
                "policyid": {"required": True, "type": "int"},
                "scan-botnet-connections": {"required": False, "type": "str",
                                            "choices": ["disable", "block", "monitor"]},
                "service": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "spamfilter-profile": {"required": False, "type": "str"},
                "spamfilter-profile-status": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "srcaddr": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "webfilter-profile": {"required": False, "type": "str"},
                "webfilter-profile-status": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]}

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
