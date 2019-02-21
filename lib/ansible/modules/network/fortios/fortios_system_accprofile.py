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
module: fortios_system_accprofile
short_description: Configure access profiles for system administrators in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify system feature and accprofile category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
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
        default: true
    system_accprofile:
        description:
            - Configure access profiles for system administrators.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            admintimeout:
                description:
                    - Administrator timeout for this access profile (0 - 480 min, default = 10, 0 means never timeout).
            admintimeout-override:
                description:
                    - Enable/disable overriding the global administrator idle timeout.
                choices:
                    - enable
                    - disable
            authgrp:
                description:
                    - Administrator access to Users and Devices.
                choices:
                    - none
                    - read
                    - read-write
            comments:
                description:
                    - Comment.
            ftviewgrp:
                description:
                    - FortiView.
                choices:
                    - none
                    - read
                    - read-write
            fwgrp:
                description:
                    - Administrator access to the Firewall configuration.
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            fwgrp-permission:
                description:
                    - Custom firewall permission.
                suboptions:
                    address:
                        description:
                            - Address Configuration.
                        choices:
                            - none
                            - read
                            - read-write
                    policy:
                        description:
                            - Policy Configuration.
                        choices:
                            - none
                            - read
                            - read-write
                    schedule:
                        description:
                            - Schedule Configuration.
                        choices:
                            - none
                            - read
                            - read-write
                    service:
                        description:
                            - Service Configuration.
                        choices:
                            - none
                            - read
                            - read-write
            loggrp:
                description:
                    - Administrator access to Logging and Reporting including viewing log messages.
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            loggrp-permission:
                description:
                    - Custom Log & Report permission.
                suboptions:
                    config:
                        description:
                            - Log & Report configuration.
                        choices:
                            - none
                            - read
                            - read-write
                    data-access:
                        description:
                            - Log & Report Data Access.
                        choices:
                            - none
                            - read
                            - read-write
                    report-access:
                        description:
                            - Log & Report Report Access.
                        choices:
                            - none
                            - read
                            - read-write
                    threat-weight:
                        description:
                            - Log & Report Threat Weight.
                        choices:
                            - none
                            - read
                            - read-write
            name:
                description:
                    - Profile name.
                required: true
            netgrp:
                description:
                    - Network Configuration.
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            netgrp-permission:
                description:
                    - Custom network permission.
                suboptions:
                    cfg:
                        description:
                            - Network Configuration.
                        choices:
                            - none
                            - read
                            - read-write
                    packet-capture:
                        description:
                            - Packet Capture Configuration.
                        choices:
                            - none
                            - read
                            - read-write
                    route-cfg:
                        description:
                            - Router Configuration.
                        choices:
                            - none
                            - read
                            - read-write
            scope:
                description:
                    - "Scope of admin access: global or specific VDOM(s)."
                choices:
                    - vdom
                    - global
            secfabgrp:
                description:
                    - Security Fabric.
                choices:
                    - none
                    - read
                    - read-write
            sysgrp:
                description:
                    - System Configuration.
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            sysgrp-permission:
                description:
                    - Custom system permission.
                suboptions:
                    admin:
                        description:
                            - Administrator Users.
                        choices:
                            - none
                            - read
                            - read-write
                    cfg:
                        description:
                            - System Configuration.
                        choices:
                            - none
                            - read
                            - read-write
                    mnt:
                        description:
                            - Maintenance.
                        choices:
                            - none
                            - read
                            - read-write
                    upd:
                        description:
                            - FortiGuard Updates.
                        choices:
                            - none
                            - read
                            - read-write
            utmgrp:
                description:
                    - Administrator access to Security Profiles.
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            utmgrp-permission:
                description:
                    - Custom Security Profile permissions.
                suboptions:
                    antivirus:
                        description:
                            - Antivirus profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    application-control:
                        description:
                            - Application Control profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    data-loss-prevention:
                        description:
                            - DLP profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    dnsfilter:
                        description:
                            - DNS Filter profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    endpoint-control:
                        description:
                            - FortiClient Profiles.
                        choices:
                            - none
                            - read
                            - read-write
                    icap:
                        description:
                            - ICAP profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    ips:
                        description:
                            - IPS profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    spamfilter:
                        description:
                            - AntiSpam filter and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    voip:
                        description:
                            - VoIP profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    waf:
                        description:
                            - Web Application Firewall profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
                    webfilter:
                        description:
                            - Web Filter profiles and settings.
                        choices:
                            - none
                            - read
                            - read-write
            vpngrp:
                description:
                    - Administrator access to IPsec, SSL, PPTP, and L2TP VPN.
                choices:
                    - none
                    - read
                    - read-write
            wanoptgrp:
                description:
                    - Administrator access to WAN Opt & Cache.
                choices:
                    - none
                    - read
                    - read-write
            wifi:
                description:
                    - Administrator access to the WiFi controller and Switch controller.
                choices:
                    - none
                    - read
                    - read-write
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure access profiles for system administrators.
    fortios_system_accprofile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_accprofile:
        state: "present"
        admintimeout: "3"
        admintimeout-override: "enable"
        authgrp: "none"
        comments: "<your_own_value>"
        ftviewgrp: "none"
        fwgrp: "none"
        fwgrp-permission:
            address: "none"
            policy: "none"
            schedule: "none"
            service: "none"
        loggrp: "none"
        loggrp-permission:
            config: "none"
            data-access: "none"
            report-access: "none"
            threat-weight: "none"
        name: "default_name_20"
        netgrp: "none"
        netgrp-permission:
            cfg: "none"
            packet-capture: "none"
            route-cfg: "none"
        scope: "vdom"
        secfabgrp: "none"
        sysgrp: "none"
        sysgrp-permission:
            admin: "none"
            cfg: "none"
            mnt: "none"
            upd: "none"
        utmgrp: "none"
        utmgrp-permission:
            antivirus: "none"
            application-control: "none"
            data-loss-prevention: "none"
            dnsfilter: "none"
            endpoint-control: "none"
            icap: "none"
            ips: "none"
            spamfilter: "none"
            voip: "none"
            waf: "none"
            webfilter: "none"
        vpngrp: "none"
        wanoptgrp: "none"
        wifi: "none"
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


def filter_system_accprofile_data(json):
    option_list = ['admintimeout', 'admintimeout-override', 'authgrp',
                   'comments', 'ftviewgrp', 'fwgrp',
                   'fwgrp-permission', 'loggrp', 'loggrp-permission',
                   'name', 'netgrp', 'netgrp-permission',
                   'scope', 'secfabgrp', 'sysgrp',
                   'sysgrp-permission', 'utmgrp', 'utmgrp-permission',
                   'vpngrp', 'wanoptgrp', 'wifi']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def system_accprofile(data, fos):
    vdom = data['vdom']
    system_accprofile_data = data['system_accprofile']
    flattened_data = flatten_multilists_attributes(system_accprofile_data)
    filtered_data = filter_system_accprofile_data(flattened_data)
    if system_accprofile_data['state'] == "present":
        return fos.set('system',
                       'accprofile',
                       data=filtered_data,
                       vdom=vdom)

    elif system_accprofile_data['state'] == "absent":
        return fos.delete('system',
                          'accprofile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_system(data, fos):
    login(data)

    if data['system_accprofile']:
        resp = system_accprofile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "system_accprofile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "admintimeout": {"required": False, "type": "int"},
                "admintimeout-override": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "authgrp": {"required": False, "type": "str",
                            "choices": ["none", "read", "read-write"]},
                "comments": {"required": False, "type": "str"},
                "ftviewgrp": {"required": False, "type": "str",
                              "choices": ["none", "read", "read-write"]},
                "fwgrp": {"required": False, "type": "str",
                          "choices": ["none", "read", "read-write",
                                      "custom"]},
                "fwgrp-permission": {"required": False, "type": "dict",
                                     "options": {
                                         "address": {"required": False, "type": "str",
                                                     "choices": ["none", "read", "read-write"]},
                                         "policy": {"required": False, "type": "str",
                                                    "choices": ["none", "read", "read-write"]},
                                         "schedule": {"required": False, "type": "str",
                                                      "choices": ["none", "read", "read-write"]},
                                         "service": {"required": False, "type": "str",
                                                     "choices": ["none", "read", "read-write"]}
                                     }},
                "loggrp": {"required": False, "type": "str",
                           "choices": ["none", "read", "read-write",
                                       "custom"]},
                "loggrp-permission": {"required": False, "type": "dict",
                                      "options": {
                                          "config": {"required": False, "type": "str",
                                                     "choices": ["none", "read", "read-write"]},
                                          "data-access": {"required": False, "type": "str",
                                                          "choices": ["none", "read", "read-write"]},
                                          "report-access": {"required": False, "type": "str",
                                                            "choices": ["none", "read", "read-write"]},
                                          "threat-weight": {"required": False, "type": "str",
                                                            "choices": ["none", "read", "read-write"]}
                                      }},
                "name": {"required": True, "type": "str"},
                "netgrp": {"required": False, "type": "str",
                           "choices": ["none", "read", "read-write",
                                       "custom"]},
                "netgrp-permission": {"required": False, "type": "dict",
                                      "options": {
                                          "cfg": {"required": False, "type": "str",
                                                  "choices": ["none", "read", "read-write"]},
                                          "packet-capture": {"required": False, "type": "str",
                                                             "choices": ["none", "read", "read-write"]},
                                          "route-cfg": {"required": False, "type": "str",
                                                        "choices": ["none", "read", "read-write"]}
                                      }},
                "scope": {"required": False, "type": "str",
                          "choices": ["vdom", "global"]},
                "secfabgrp": {"required": False, "type": "str",
                              "choices": ["none", "read", "read-write"]},
                "sysgrp": {"required": False, "type": "str",
                           "choices": ["none", "read", "read-write",
                                       "custom"]},
                "sysgrp-permission": {"required": False, "type": "dict",
                                      "options": {
                                          "admin": {"required": False, "type": "str",
                                                    "choices": ["none", "read", "read-write"]},
                                          "cfg": {"required": False, "type": "str",
                                                  "choices": ["none", "read", "read-write"]},
                                          "mnt": {"required": False, "type": "str",
                                                  "choices": ["none", "read", "read-write"]},
                                          "upd": {"required": False, "type": "str",
                                                  "choices": ["none", "read", "read-write"]}
                                      }},
                "utmgrp": {"required": False, "type": "str",
                           "choices": ["none", "read", "read-write",
                                       "custom"]},
                "utmgrp-permission": {"required": False, "type": "dict",
                                      "options": {
                                          "antivirus": {"required": False, "type": "str",
                                                        "choices": ["none", "read", "read-write"]},
                                          "application-control": {"required": False, "type": "str",
                                                                  "choices": ["none", "read", "read-write"]},
                                          "data-loss-prevention": {"required": False, "type": "str",
                                                                   "choices": ["none", "read", "read-write"]},
                                          "dnsfilter": {"required": False, "type": "str",
                                                        "choices": ["none", "read", "read-write"]},
                                          "endpoint-control": {"required": False, "type": "str",
                                                               "choices": ["none", "read", "read-write"]},
                                          "icap": {"required": False, "type": "str",
                                                   "choices": ["none", "read", "read-write"]},
                                          "ips": {"required": False, "type": "str",
                                                  "choices": ["none", "read", "read-write"]},
                                          "spamfilter": {"required": False, "type": "str",
                                                         "choices": ["none", "read", "read-write"]},
                                          "voip": {"required": False, "type": "str",
                                                   "choices": ["none", "read", "read-write"]},
                                          "waf": {"required": False, "type": "str",
                                                  "choices": ["none", "read", "read-write"]},
                                          "webfilter": {"required": False, "type": "str",
                                                        "choices": ["none", "read", "read-write"]}
                                      }},
                "vpngrp": {"required": False, "type": "str",
                           "choices": ["none", "read", "read-write"]},
                "wanoptgrp": {"required": False, "type": "str",
                              "choices": ["none", "read", "read-write"]},
                "wifi": {"required": False, "type": "str",
                         "choices": ["none", "read", "read-write"]}

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
