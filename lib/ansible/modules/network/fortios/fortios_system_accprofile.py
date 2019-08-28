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
module: fortios_system_accprofile
short_description: Configure access profiles for system administrators in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and accprofile category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
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
        version_added: 2.9
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    system_accprofile:
        description:
            - Configure access profiles for system administrators.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            admintimeout:
                description:
                    - Administrator timeout for this access profile (0 - 480 min).
                type: int
            admintimeout_override:
                description:
                    - Enable/disable overriding the global administrator idle timeout.
                type: str
                choices:
                    - enable
                    - disable
            authgrp:
                description:
                    - Administrator access to Users and Devices.
                type: str
                choices:
                    - none
                    - read
                    - read-write
            comments:
                description:
                    - Comment.
                type: str
            ftviewgrp:
                description:
                    - FortiView.
                type: str
                choices:
                    - none
                    - read
                    - read-write
            fwgrp:
                description:
                    - Administrator access to the Firewall configuration.
                type: str
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            fwgrp_permission:
                description:
                    - Custom firewall permission.
                type: dict
                suboptions:
                    address:
                        description:
                            - Address Configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    policy:
                        description:
                            - Policy Configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    schedule:
                        description:
                            - Schedule Configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    service:
                        description:
                            - Service Configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
            loggrp:
                description:
                    - Administrator access to Logging and Reporting including viewing log messages.
                type: str
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            loggrp_permission:
                description:
                    - Custom Log & Report permission.
                type: dict
                suboptions:
                    config:
                        description:
                            - Log & Report configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    data_access:
                        description:
                            - Log & Report Data Access.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    report_access:
                        description:
                            - Log & Report Report Access.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    threat_weight:
                        description:
                            - Log & Report Threat Weight.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
            name:
                description:
                    - Profile name.
                required: true
                type: str
            netgrp:
                description:
                    - Network Configuration.
                type: str
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            netgrp_permission:
                description:
                    - Custom network permission.
                type: dict
                suboptions:
                    cfg:
                        description:
                            - Network Configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    packet_capture:
                        description:
                            - Packet Capture Configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    route_cfg:
                        description:
                            - Router Configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
            scope:
                description:
                    - "Scope of admin access: global or specific VDOM(s)."
                type: str
                choices:
                    - vdom
                    - global
            secfabgrp:
                description:
                    - Security Fabric.
                type: str
                choices:
                    - none
                    - read
                    - read-write
            sysgrp:
                description:
                    - System Configuration.
                type: str
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            sysgrp_permission:
                description:
                    - Custom system permission.
                type: dict
                suboptions:
                    admin:
                        description:
                            - Administrator Users.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    cfg:
                        description:
                            - System Configuration.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    mnt:
                        description:
                            - Maintenance.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    upd:
                        description:
                            - FortiGuard Updates.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
            utmgrp:
                description:
                    - Administrator access to Security Profiles.
                type: str
                choices:
                    - none
                    - read
                    - read-write
                    - custom
            utmgrp_permission:
                description:
                    - Custom Security Profile permissions.
                type: dict
                suboptions:
                    antivirus:
                        description:
                            - Antivirus profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    application_control:
                        description:
                            - Application Control profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    data_loss_prevention:
                        description:
                            - DLP profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    dnsfilter:
                        description:
                            - DNS Filter profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    endpoint_control:
                        description:
                            - FortiClient Profiles.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    icap:
                        description:
                            - ICAP profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    ips:
                        description:
                            - IPS profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    spamfilter:
                        description:
                            - AntiSpam filter and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    voip:
                        description:
                            - VoIP profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    waf:
                        description:
                            - Web Application Firewall profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
                    webfilter:
                        description:
                            - Web Filter profiles and settings.
                        type: str
                        choices:
                            - none
                            - read
                            - read-write
            vpngrp:
                description:
                    - Administrator access to IPsec, SSL, PPTP, and L2TP VPN.
                type: str
                choices:
                    - none
                    - read
                    - read-write
            wanoptgrp:
                description:
                    - Administrator access to WAN Opt & Cache.
                type: str
                choices:
                    - none
                    - read
                    - read-write
            wifi:
                description:
                    - Administrator access to the WiFi controller and Switch controller.
                type: str
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
   ssl_verify: "False"
  tasks:
  - name: Configure access profiles for system administrators.
    fortios_system_accprofile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_accprofile:
        admintimeout: "3"
        admintimeout_override: "enable"
        authgrp: "none"
        comments: "<your_own_value>"
        ftviewgrp: "none"
        fwgrp: "none"
        fwgrp_permission:
            address: "none"
            policy: "none"
            schedule: "none"
            service: "none"
        loggrp: "none"
        loggrp_permission:
            config: "none"
            data_access: "none"
            report_access: "none"
            threat_weight: "none"
        name: "default_name_20"
        netgrp: "none"
        netgrp_permission:
            cfg: "none"
            packet_capture: "none"
            route_cfg: "none"
        scope: "vdom"
        secfabgrp: "none"
        sysgrp: "none"
        sysgrp_permission:
            admin: "none"
            cfg: "none"
            mnt: "none"
            upd: "none"
        utmgrp: "none"
        utmgrp_permission:
            antivirus: "none"
            application_control: "none"
            data_loss_prevention: "none"
            dnsfilter: "none"
            endpoint_control: "none"
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


def filter_system_accprofile_data(json):
    option_list = ['admintimeout', 'admintimeout_override', 'authgrp',
                   'comments', 'ftviewgrp', 'fwgrp',
                   'fwgrp_permission', 'loggrp', 'loggrp_permission',
                   'name', 'netgrp', 'netgrp_permission',
                   'scope', 'secfabgrp', 'sysgrp',
                   'sysgrp_permission', 'utmgrp', 'utmgrp_permission',
                   'vpngrp', 'wanoptgrp', 'wifi']
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


def system_accprofile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['system_accprofile'] and data['system_accprofile']:
        state = data['system_accprofile']['state']
    else:
        state = True
    system_accprofile_data = data['system_accprofile']
    filtered_data = underscore_to_hyphen(filter_system_accprofile_data(system_accprofile_data))

    if state == "present":
        return fos.set('system',
                       'accprofile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'accprofile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_accprofile']:
        resp = system_accprofile(data, fos)

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
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "system_accprofile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "admintimeout": {"required": False, "type": "int"},
                "admintimeout_override": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "authgrp": {"required": False, "type": "str",
                            "choices": ["none", "read", "read-write"]},
                "comments": {"required": False, "type": "str"},
                "ftviewgrp": {"required": False, "type": "str",
                              "choices": ["none", "read", "read-write"]},
                "fwgrp": {"required": False, "type": "str",
                          "choices": ["none", "read", "read-write",
                                      "custom"]},
                "fwgrp_permission": {"required": False, "type": "dict",
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
                "loggrp_permission": {"required": False, "type": "dict",
                                      "options": {
                                          "config": {"required": False, "type": "str",
                                                     "choices": ["none", "read", "read-write"]},
                                          "data_access": {"required": False, "type": "str",
                                                          "choices": ["none", "read", "read-write"]},
                                          "report_access": {"required": False, "type": "str",
                                                            "choices": ["none", "read", "read-write"]},
                                          "threat_weight": {"required": False, "type": "str",
                                                            "choices": ["none", "read", "read-write"]}
                                      }},
                "name": {"required": True, "type": "str"},
                "netgrp": {"required": False, "type": "str",
                           "choices": ["none", "read", "read-write",
                                       "custom"]},
                "netgrp_permission": {"required": False, "type": "dict",
                                      "options": {
                                          "cfg": {"required": False, "type": "str",
                                                  "choices": ["none", "read", "read-write"]},
                                          "packet_capture": {"required": False, "type": "str",
                                                             "choices": ["none", "read", "read-write"]},
                                          "route_cfg": {"required": False, "type": "str",
                                                        "choices": ["none", "read", "read-write"]}
                                      }},
                "scope": {"required": False, "type": "str",
                          "choices": ["vdom", "global"]},
                "secfabgrp": {"required": False, "type": "str",
                              "choices": ["none", "read", "read-write"]},
                "sysgrp": {"required": False, "type": "str",
                           "choices": ["none", "read", "read-write",
                                       "custom"]},
                "sysgrp_permission": {"required": False, "type": "dict",
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
                "utmgrp_permission": {"required": False, "type": "dict",
                                      "options": {
                                          "antivirus": {"required": False, "type": "str",
                                                        "choices": ["none", "read", "read-write"]},
                                          "application_control": {"required": False, "type": "str",
                                                                  "choices": ["none", "read", "read-write"]},
                                          "data_loss_prevention": {"required": False, "type": "str",
                                                                   "choices": ["none", "read", "read-write"]},
                                          "dnsfilter": {"required": False, "type": "str",
                                                        "choices": ["none", "read", "read-write"]},
                                          "endpoint_control": {"required": False, "type": "str",
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
