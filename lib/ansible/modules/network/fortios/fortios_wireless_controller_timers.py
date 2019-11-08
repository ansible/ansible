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
module: fortios_wireless_controller_timers
short_description: Configure CAPWAP timers in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wireless_controller feature and timers category.
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
    wireless_controller_timers:
        description:
            - Configure CAPWAP timers.
        default: null
        type: dict
        suboptions:
            ble_scan_report_intv:
                description:
                    - Time between running Bluetooth Low Energy (BLE) reports (10 - 3600 sec).
                type: int
            client_idle_timeout:
                description:
                    - Time after which a client is considered idle and times out (20 - 3600 sec).
                type: int
            darrp_day:
                description:
                    - Weekday on which to run DARRP optimization.
                type: str
                choices:
                    - sunday
                    - monday
                    - tuesday
                    - wednesday
                    - thursday
                    - friday
                    - saturday
            darrp_optimize:
                description:
                    - Time for running Dynamic Automatic Radio Resource Provisioning (DARRP) optimizations (0 - 86400 sec).
                type: int
            darrp_time:
                description:
                    - Time at which DARRP optimizations run (you can add up to 8 times).
                type: list
                suboptions:
                    time:
                        description:
                            - Time.
                        required: true
                        type: str
            discovery_interval:
                description:
                    - Time between discovery requests (2 - 180 sec).
                type: int
            echo_interval:
                description:
                    - Time between echo requests sent by the managed WTP, AP, or FortiAP (1 - 255 sec).
                type: int
            fake_ap_log:
                description:
                    - Time between recording logs about fake APs if periodic fake AP logging is configured (0 - 1440 min).
                type: int
            ipsec_intf_cleanup:
                description:
                    - Time period to keep IPsec VPN interfaces up after WTP sessions are disconnected (30 - 3600 sec).
                type: int
            radio_stats_interval:
                description:
                    - Time between running radio reports (1 - 255 sec).
                type: int
            rogue_ap_log:
                description:
                    - Time between logging rogue AP messages if periodic rogue AP logging is configured (0 - 1440 min).
                type: int
            sta_capability_interval:
                description:
                    - Time between running station capability reports (1 - 255 sec).
                type: int
            sta_locate_timer:
                description:
                    - Time between running client presence flushes to remove clients that are listed but no longer present (0 - 86400 sec).
                type: int
            sta_stats_interval:
                description:
                    - Time between running client (station) reports (1 - 255 sec).
                type: int
            vap_stats_interval:
                description:
                    - Time between running Virtual Access Point (VAP) reports (1 - 255 sec).
                type: int
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
  - name: Configure CAPWAP timers.
    fortios_wireless_controller_timers:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      wireless_controller_timers:
        ble_scan_report_intv: "3"
        client_idle_timeout: "4"
        darrp_day: "sunday"
        darrp_optimize: "6"
        darrp_time:
         -
            time: "<your_own_value>"
        discovery_interval: "9"
        echo_interval: "10"
        fake_ap_log: "11"
        ipsec_intf_cleanup: "12"
        radio_stats_interval: "13"
        rogue_ap_log: "14"
        sta_capability_interval: "15"
        sta_locate_timer: "16"
        sta_stats_interval: "17"
        vap_stats_interval: "18"
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


def filter_wireless_controller_timers_data(json):
    option_list = ['ble_scan_report_intv', 'client_idle_timeout', 'darrp_day',
                   'darrp_optimize', 'darrp_time', 'discovery_interval',
                   'echo_interval', 'fake_ap_log', 'ipsec_intf_cleanup',
                   'radio_stats_interval', 'rogue_ap_log', 'sta_capability_interval',
                   'sta_locate_timer', 'sta_stats_interval', 'vap_stats_interval']
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


def wireless_controller_timers(data, fos):
    vdom = data['vdom']
    wireless_controller_timers_data = data['wireless_controller_timers']
    filtered_data = underscore_to_hyphen(filter_wireless_controller_timers_data(wireless_controller_timers_data))

    return fos.set('wireless-controller',
                   'timers',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wireless_controller(data, fos):

    if data['wireless_controller_timers']:
        resp = wireless_controller_timers(data, fos)

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
        "wireless_controller_timers": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "ble_scan_report_intv": {"required": False, "type": "int"},
                "client_idle_timeout": {"required": False, "type": "int"},
                "darrp_day": {"required": False, "type": "str",
                              "choices": ["sunday", "monday", "tuesday",
                                          "wednesday", "thursday", "friday",
                                          "saturday"]},
                "darrp_optimize": {"required": False, "type": "int"},
                "darrp_time": {"required": False, "type": "list",
                               "options": {
                                   "time": {"required": True, "type": "str"}
                               }},
                "discovery_interval": {"required": False, "type": "int"},
                "echo_interval": {"required": False, "type": "int"},
                "fake_ap_log": {"required": False, "type": "int"},
                "ipsec_intf_cleanup": {"required": False, "type": "int"},
                "radio_stats_interval": {"required": False, "type": "int"},
                "rogue_ap_log": {"required": False, "type": "int"},
                "sta_capability_interval": {"required": False, "type": "int"},
                "sta_locate_timer": {"required": False, "type": "int"},
                "sta_stats_interval": {"required": False, "type": "int"},
                "vap_stats_interval": {"required": False, "type": "int"}

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

            is_error, has_changed, result = fortios_wireless_controller(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_wireless_controller(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
