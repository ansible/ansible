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
module: fortios_wireless_controller_wids_profile
short_description: Configure wireless intrusion detection system (WIDS) profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wireless_controller feature and wids_profile category.
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
    wireless_controller_wids_profile:
        description:
            - Configure wireless intrusion detection system (WIDS) profiles.
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
            ap_auto_suppress:
                description:
                    - Enable/disable on-wire rogue AP auto-suppression .
                type: str
                choices:
                    - enable
                    - disable
            ap_bgscan_disable_day:
                description:
                    - Optionally turn off scanning for one or more days of the week. Separate the days with a space. By default, no days are set.
                type: str
                choices:
                    - sunday
                    - monday
                    - tuesday
                    - wednesday
                    - thursday
                    - friday
                    - saturday
            ap_bgscan_disable_end:
                description:
                    - "End time, using a 24-hour clock in the format of hh:mm, for disabling background scanning ."
                type: str
            ap_bgscan_disable_start:
                description:
                    - "Start time, using a 24-hour clock in the format of hh:mm, for disabling background scanning ."
                type: str
            ap_bgscan_duration:
                description:
                    - Listening time on a scanning channel (10 - 1000 msec).
                type: int
            ap_bgscan_idle:
                description:
                    - Waiting time for channel inactivity before scanning this channel (0 - 1000 msec).
                type: int
            ap_bgscan_intv:
                description:
                    - Period of time between scanning two channels (1 - 600 sec).
                type: int
            ap_bgscan_period:
                description:
                    - Period of time between background scans (60 - 3600 sec).
                type: int
            ap_bgscan_report_intv:
                description:
                    - Period of time between background scan reports (15 - 600 sec).
                type: int
            ap_fgscan_report_intv:
                description:
                    - Period of time between foreground scan reports (15 - 600 sec).
                type: int
            ap_scan:
                description:
                    - Enable/disable rogue AP detection.
                type: str
                choices:
                    - disable
                    - enable
            ap_scan_passive:
                description:
                    - Enable/disable passive scanning. Enable means do not send probe request on any channels .
                type: str
                choices:
                    - enable
                    - disable
            asleap_attack:
                description:
                    - Enable/disable asleap attack detection .
                type: str
                choices:
                    - enable
                    - disable
            assoc_flood_thresh:
                description:
                    - The threshold value for association frame flooding.
                type: int
            assoc_flood_time:
                description:
                    - Number of seconds after which a station is considered not connected.
                type: int
            assoc_frame_flood:
                description:
                    - Enable/disable association frame flooding detection .
                type: str
                choices:
                    - enable
                    - disable
            auth_flood_thresh:
                description:
                    - The threshold value for authentication frame flooding.
                type: int
            auth_flood_time:
                description:
                    - Number of seconds after which a station is considered not connected.
                type: int
            auth_frame_flood:
                description:
                    - Enable/disable authentication frame flooding detection .
                type: str
                choices:
                    - enable
                    - disable
            comment:
                description:
                    - Comment.
                type: str
            deauth_broadcast:
                description:
                    - Enable/disable broadcasting de-authentication detection .
                type: str
                choices:
                    - enable
                    - disable
            deauth_unknown_src_thresh:
                description:
                    - "Threshold value per second to deauth unknown src for DoS attack (0: no limit)."
                type: int
            eapol_fail_flood:
                description:
                    - Enable/disable EAPOL-Failure flooding (to AP) detection .
                type: str
                choices:
                    - enable
                    - disable
            eapol_fail_intv:
                description:
                    - The detection interval for EAPOL-Failure flooding (1 - 3600 sec).
                type: int
            eapol_fail_thresh:
                description:
                    - The threshold value for EAPOL-Failure flooding in specified interval.
                type: int
            eapol_logoff_flood:
                description:
                    - Enable/disable EAPOL-Logoff flooding (to AP) detection .
                type: str
                choices:
                    - enable
                    - disable
            eapol_logoff_intv:
                description:
                    - The detection interval for EAPOL-Logoff flooding (1 - 3600 sec).
                type: int
            eapol_logoff_thresh:
                description:
                    - The threshold value for EAPOL-Logoff flooding in specified interval.
                type: int
            eapol_pre_fail_flood:
                description:
                    - Enable/disable premature EAPOL-Failure flooding (to STA) detection .
                type: str
                choices:
                    - enable
                    - disable
            eapol_pre_fail_intv:
                description:
                    - The detection interval for premature EAPOL-Failure flooding (1 - 3600 sec).
                type: int
            eapol_pre_fail_thresh:
                description:
                    - The threshold value for premature EAPOL-Failure flooding in specified interval.
                type: int
            eapol_pre_succ_flood:
                description:
                    - Enable/disable premature EAPOL-Success flooding (to STA) detection .
                type: str
                choices:
                    - enable
                    - disable
            eapol_pre_succ_intv:
                description:
                    - The detection interval for premature EAPOL-Success flooding (1 - 3600 sec).
                type: int
            eapol_pre_succ_thresh:
                description:
                    - The threshold value for premature EAPOL-Success flooding in specified interval.
                type: int
            eapol_start_flood:
                description:
                    - Enable/disable EAPOL-Start flooding (to AP) detection .
                type: str
                choices:
                    - enable
                    - disable
            eapol_start_intv:
                description:
                    - The detection interval for EAPOL-Start flooding (1 - 3600 sec).
                type: int
            eapol_start_thresh:
                description:
                    - The threshold value for EAPOL-Start flooding in specified interval.
                type: int
            eapol_succ_flood:
                description:
                    - Enable/disable EAPOL-Success flooding (to AP) detection .
                type: str
                choices:
                    - enable
                    - disable
            eapol_succ_intv:
                description:
                    - The detection interval for EAPOL-Success flooding (1 - 3600 sec).
                type: int
            eapol_succ_thresh:
                description:
                    - The threshold value for EAPOL-Success flooding in specified interval.
                type: int
            invalid_mac_oui:
                description:
                    - Enable/disable invalid MAC OUI detection.
                type: str
                choices:
                    - enable
                    - disable
            long_duration_attack:
                description:
                    - Enable/disable long duration attack detection based on user configured threshold .
                type: str
                choices:
                    - enable
                    - disable
            long_duration_thresh:
                description:
                    - Threshold value for long duration attack detection (1000 - 32767 usec).
                type: int
            name:
                description:
                    - WIDS profile name.
                required: true
                type: str
            null_ssid_probe_resp:
                description:
                    - Enable/disable null SSID probe response detection .
                type: str
                choices:
                    - enable
                    - disable
            sensor_mode:
                description:
                    - Scan WiFi nearby stations .
                type: str
                choices:
                    - disable
                    - foreign
                    - both
            spoofed_deauth:
                description:
                    - Enable/disable spoofed de-authentication attack detection .
                type: str
                choices:
                    - enable
                    - disable
            weak_wep_iv:
                description:
                    - Enable/disable weak WEP IV (Initialization Vector) detection .
                type: str
                choices:
                    - enable
                    - disable
            wireless_bridge:
                description:
                    - Enable/disable wireless bridge detection .
                type: str
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
   ssl_verify: "False"
  tasks:
  - name: Configure wireless intrusion detection system (WIDS) profiles.
    fortios_wireless_controller_wids_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      wireless_controller_wids_profile:
        ap_auto_suppress: "enable"
        ap_bgscan_disable_day: "sunday"
        ap_bgscan_disable_end: "<your_own_value>"
        ap_bgscan_disable_start: "<your_own_value>"
        ap_bgscan_duration: "7"
        ap_bgscan_idle: "8"
        ap_bgscan_intv: "9"
        ap_bgscan_period: "10"
        ap_bgscan_report_intv: "11"
        ap_fgscan_report_intv: "12"
        ap_scan: "disable"
        ap_scan_passive: "enable"
        asleap_attack: "enable"
        assoc_flood_thresh: "16"
        assoc_flood_time: "17"
        assoc_frame_flood: "enable"
        auth_flood_thresh: "19"
        auth_flood_time: "20"
        auth_frame_flood: "enable"
        comment: "Comment."
        deauth_broadcast: "enable"
        deauth_unknown_src_thresh: "24"
        eapol_fail_flood: "enable"
        eapol_fail_intv: "26"
        eapol_fail_thresh: "27"
        eapol_logoff_flood: "enable"
        eapol_logoff_intv: "29"
        eapol_logoff_thresh: "30"
        eapol_pre_fail_flood: "enable"
        eapol_pre_fail_intv: "32"
        eapol_pre_fail_thresh: "33"
        eapol_pre_succ_flood: "enable"
        eapol_pre_succ_intv: "35"
        eapol_pre_succ_thresh: "36"
        eapol_start_flood: "enable"
        eapol_start_intv: "38"
        eapol_start_thresh: "39"
        eapol_succ_flood: "enable"
        eapol_succ_intv: "41"
        eapol_succ_thresh: "42"
        invalid_mac_oui: "enable"
        long_duration_attack: "enable"
        long_duration_thresh: "45"
        name: "default_name_46"
        null_ssid_probe_resp: "enable"
        sensor_mode: "disable"
        spoofed_deauth: "enable"
        weak_wep_iv: "enable"
        wireless_bridge: "enable"
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


def filter_wireless_controller_wids_profile_data(json):
    option_list = ['ap_auto_suppress', 'ap_bgscan_disable_day', 'ap_bgscan_disable_end',
                   'ap_bgscan_disable_start', 'ap_bgscan_duration', 'ap_bgscan_idle',
                   'ap_bgscan_intv', 'ap_bgscan_period', 'ap_bgscan_report_intv',
                   'ap_fgscan_report_intv', 'ap_scan', 'ap_scan_passive',
                   'asleap_attack', 'assoc_flood_thresh', 'assoc_flood_time',
                   'assoc_frame_flood', 'auth_flood_thresh', 'auth_flood_time',
                   'auth_frame_flood', 'comment', 'deauth_broadcast',
                   'deauth_unknown_src_thresh', 'eapol_fail_flood', 'eapol_fail_intv',
                   'eapol_fail_thresh', 'eapol_logoff_flood', 'eapol_logoff_intv',
                   'eapol_logoff_thresh', 'eapol_pre_fail_flood', 'eapol_pre_fail_intv',
                   'eapol_pre_fail_thresh', 'eapol_pre_succ_flood', 'eapol_pre_succ_intv',
                   'eapol_pre_succ_thresh', 'eapol_start_flood', 'eapol_start_intv',
                   'eapol_start_thresh', 'eapol_succ_flood', 'eapol_succ_intv',
                   'eapol_succ_thresh', 'invalid_mac_oui', 'long_duration_attack',
                   'long_duration_thresh', 'name', 'null_ssid_probe_resp',
                   'sensor_mode', 'spoofed_deauth', 'weak_wep_iv',
                   'wireless_bridge']
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


def wireless_controller_wids_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['wireless_controller_wids_profile'] and data['wireless_controller_wids_profile']:
        state = data['wireless_controller_wids_profile']['state']
    else:
        state = True
    wireless_controller_wids_profile_data = data['wireless_controller_wids_profile']
    filtered_data = underscore_to_hyphen(filter_wireless_controller_wids_profile_data(wireless_controller_wids_profile_data))

    if state == "present":
        return fos.set('wireless-controller',
                       'wids-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('wireless-controller',
                          'wids-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wireless_controller(data, fos):

    if data['wireless_controller_wids_profile']:
        resp = wireless_controller_wids_profile(data, fos)

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
        "wireless_controller_wids_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "ap_auto_suppress": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "ap_bgscan_disable_day": {"required": False, "type": "str",
                                          "choices": ["sunday", "monday", "tuesday",
                                                      "wednesday", "thursday", "friday",
                                                      "saturday"]},
                "ap_bgscan_disable_end": {"required": False, "type": "str"},
                "ap_bgscan_disable_start": {"required": False, "type": "str"},
                "ap_bgscan_duration": {"required": False, "type": "int"},
                "ap_bgscan_idle": {"required": False, "type": "int"},
                "ap_bgscan_intv": {"required": False, "type": "int"},
                "ap_bgscan_period": {"required": False, "type": "int"},
                "ap_bgscan_report_intv": {"required": False, "type": "int"},
                "ap_fgscan_report_intv": {"required": False, "type": "int"},
                "ap_scan": {"required": False, "type": "str",
                            "choices": ["disable", "enable"]},
                "ap_scan_passive": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "asleap_attack": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "assoc_flood_thresh": {"required": False, "type": "int"},
                "assoc_flood_time": {"required": False, "type": "int"},
                "assoc_frame_flood": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "auth_flood_thresh": {"required": False, "type": "int"},
                "auth_flood_time": {"required": False, "type": "int"},
                "auth_frame_flood": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "comment": {"required": False, "type": "str"},
                "deauth_broadcast": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "deauth_unknown_src_thresh": {"required": False, "type": "int"},
                "eapol_fail_flood": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "eapol_fail_intv": {"required": False, "type": "int"},
                "eapol_fail_thresh": {"required": False, "type": "int"},
                "eapol_logoff_flood": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "eapol_logoff_intv": {"required": False, "type": "int"},
                "eapol_logoff_thresh": {"required": False, "type": "int"},
                "eapol_pre_fail_flood": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "eapol_pre_fail_intv": {"required": False, "type": "int"},
                "eapol_pre_fail_thresh": {"required": False, "type": "int"},
                "eapol_pre_succ_flood": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "eapol_pre_succ_intv": {"required": False, "type": "int"},
                "eapol_pre_succ_thresh": {"required": False, "type": "int"},
                "eapol_start_flood": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "eapol_start_intv": {"required": False, "type": "int"},
                "eapol_start_thresh": {"required": False, "type": "int"},
                "eapol_succ_flood": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "eapol_succ_intv": {"required": False, "type": "int"},
                "eapol_succ_thresh": {"required": False, "type": "int"},
                "invalid_mac_oui": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "long_duration_attack": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "long_duration_thresh": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "null_ssid_probe_resp": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "sensor_mode": {"required": False, "type": "str",
                                "choices": ["disable", "foreign", "both"]},
                "spoofed_deauth": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "weak_wep_iv": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "wireless_bridge": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]}

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
