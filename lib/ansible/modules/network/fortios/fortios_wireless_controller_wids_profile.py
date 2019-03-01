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
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify wireless_controller feature and wids_profile category.
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
    wireless_controller_wids_profile:
        description:
            - Configure wireless intrusion detection system (WIDS) profiles.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            ap-auto-suppress:
                description:
                    - Enable/disable on-wire rogue AP auto-suppression (default = disable).
                choices:
                    - enable
                    - disable
            ap-bgscan-disable-day:
                description:
                    - Optionally turn off scanning for one or more days of the week. Separate the days with a space. By default, no days are set.
                choices:
                    - sunday
                    - monday
                    - tuesday
                    - wednesday
                    - thursday
                    - friday
                    - saturday
            ap-bgscan-disable-end:
                description:
                    - "End time, using a 24-hour clock in the format of hh:mm, for disabling background scanning (default = 00:00)."
            ap-bgscan-disable-start:
                description:
                    - "Start time, using a 24-hour clock in the format of hh:mm, for disabling background scanning (default = 00:00)."
            ap-bgscan-duration:
                description:
                    - Listening time on a scanning channel (10 - 1000 msec, default = 20).
            ap-bgscan-idle:
                description:
                    - Waiting time for channel inactivity before scanning this channel (0 - 1000 msec, default = 0).
            ap-bgscan-intv:
                description:
                    - Period of time between scanning two channels (1 - 600 sec, default = 1).
            ap-bgscan-period:
                description:
                    - Period of time between background scans (60 - 3600 sec, default = 600).
            ap-bgscan-report-intv:
                description:
                    - Period of time between background scan reports (15 - 600 sec, default = 30).
            ap-fgscan-report-intv:
                description:
                    - Period of time between foreground scan reports (15 - 600 sec, default = 15).
            ap-scan:
                description:
                    - Enable/disable rogue AP detection.
                choices:
                    - disable
                    - enable
            ap-scan-passive:
                description:
                    - Enable/disable passive scanning. Enable means do not send probe request on any channels (default = disable).
                choices:
                    - enable
                    - disable
            asleap-attack:
                description:
                    - Enable/disable asleap attack detection (default = disable).
                choices:
                    - enable
                    - disable
            assoc-flood-thresh:
                description:
                    - The threshold value for association frame flooding.
            assoc-flood-time:
                description:
                    - Number of seconds after which a station is considered not connected.
            assoc-frame-flood:
                description:
                    - Enable/disable association frame flooding detection (default = disable).
                choices:
                    - enable
                    - disable
            auth-flood-thresh:
                description:
                    - The threshold value for authentication frame flooding.
            auth-flood-time:
                description:
                    - Number of seconds after which a station is considered not connected.
            auth-frame-flood:
                description:
                    - Enable/disable authentication frame flooding detection (default = disable).
                choices:
                    - enable
                    - disable
            comment:
                description:
                    - Comment.
            deauth-broadcast:
                description:
                    - Enable/disable broadcasting de-authentication detection (default = disable).
                choices:
                    - enable
                    - disable
            deauth-unknown-src-thresh:
                description:
                    - "Threshold value per second to deauth unknown src for DoS attack (0: no limit)."
            eapol-fail-flood:
                description:
                    - Enable/disable EAPOL-Failure flooding (to AP) detection (default = disable).
                choices:
                    - enable
                    - disable
            eapol-fail-intv:
                description:
                    - The detection interval for EAPOL-Failure flooding (1 - 3600 sec).
            eapol-fail-thresh:
                description:
                    - The threshold value for EAPOL-Failure flooding in specified interval.
            eapol-logoff-flood:
                description:
                    - Enable/disable EAPOL-Logoff flooding (to AP) detection (default = disable).
                choices:
                    - enable
                    - disable
            eapol-logoff-intv:
                description:
                    - The detection interval for EAPOL-Logoff flooding (1 - 3600 sec).
            eapol-logoff-thresh:
                description:
                    - The threshold value for EAPOL-Logoff flooding in specified interval.
            eapol-pre-fail-flood:
                description:
                    - Enable/disable premature EAPOL-Failure flooding (to STA) detection (default = disable).
                choices:
                    - enable
                    - disable
            eapol-pre-fail-intv:
                description:
                    - The detection interval for premature EAPOL-Failure flooding (1 - 3600 sec).
            eapol-pre-fail-thresh:
                description:
                    - The threshold value for premature EAPOL-Failure flooding in specified interval.
            eapol-pre-succ-flood:
                description:
                    - Enable/disable premature EAPOL-Success flooding (to STA) detection (default = disable).
                choices:
                    - enable
                    - disable
            eapol-pre-succ-intv:
                description:
                    - The detection interval for premature EAPOL-Success flooding (1 - 3600 sec).
            eapol-pre-succ-thresh:
                description:
                    - The threshold value for premature EAPOL-Success flooding in specified interval.
            eapol-start-flood:
                description:
                    - Enable/disable EAPOL-Start flooding (to AP) detection (default = disable).
                choices:
                    - enable
                    - disable
            eapol-start-intv:
                description:
                    - The detection interval for EAPOL-Start flooding (1 - 3600 sec).
            eapol-start-thresh:
                description:
                    - The threshold value for EAPOL-Start flooding in specified interval.
            eapol-succ-flood:
                description:
                    - Enable/disable EAPOL-Success flooding (to AP) detection (default = disable).
                choices:
                    - enable
                    - disable
            eapol-succ-intv:
                description:
                    - The detection interval for EAPOL-Success flooding (1 - 3600 sec).
            eapol-succ-thresh:
                description:
                    - The threshold value for EAPOL-Success flooding in specified interval.
            invalid-mac-oui:
                description:
                    - Enable/disable invalid MAC OUI detection.
                choices:
                    - enable
                    - disable
            long-duration-attack:
                description:
                    - Enable/disable long duration attack detection based on user configured threshold (default = disable).
                choices:
                    - enable
                    - disable
            long-duration-thresh:
                description:
                    - Threshold value for long duration attack detection (1000 - 32767 usec, default = 8200).
            name:
                description:
                    - WIDS profile name.
                required: true
            null-ssid-probe-resp:
                description:
                    - Enable/disable null SSID probe response detection (default = disable).
                choices:
                    - enable
                    - disable
            sensor-mode:
                description:
                    - Scan WiFi nearby stations (default = disable).
                choices:
                    - disable
                    - foreign
                    - both
            spoofed-deauth:
                description:
                    - Enable/disable spoofed de-authentication attack detection (default = disable).
                choices:
                    - enable
                    - disable
            weak-wep-iv:
                description:
                    - Enable/disable weak WEP IV (Initialization Vector) detection (default = disable).
                choices:
                    - enable
                    - disable
            wireless-bridge:
                description:
                    - Enable/disable wireless bridge detection (default = disable).
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
  - name: Configure wireless intrusion detection system (WIDS) profiles.
    fortios_wireless_controller_wids_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      wireless_controller_wids_profile:
        state: "present"
        ap-auto-suppress: "enable"
        ap-bgscan-disable-day: "sunday"
        ap-bgscan-disable-end: "<your_own_value>"
        ap-bgscan-disable-start: "<your_own_value>"
        ap-bgscan-duration: "7"
        ap-bgscan-idle: "8"
        ap-bgscan-intv: "9"
        ap-bgscan-period: "10"
        ap-bgscan-report-intv: "11"
        ap-fgscan-report-intv: "12"
        ap-scan: "disable"
        ap-scan-passive: "enable"
        asleap-attack: "enable"
        assoc-flood-thresh: "16"
        assoc-flood-time: "17"
        assoc-frame-flood: "enable"
        auth-flood-thresh: "19"
        auth-flood-time: "20"
        auth-frame-flood: "enable"
        comment: "Comment."
        deauth-broadcast: "enable"
        deauth-unknown-src-thresh: "24"
        eapol-fail-flood: "enable"
        eapol-fail-intv: "26"
        eapol-fail-thresh: "27"
        eapol-logoff-flood: "enable"
        eapol-logoff-intv: "29"
        eapol-logoff-thresh: "30"
        eapol-pre-fail-flood: "enable"
        eapol-pre-fail-intv: "32"
        eapol-pre-fail-thresh: "33"
        eapol-pre-succ-flood: "enable"
        eapol-pre-succ-intv: "35"
        eapol-pre-succ-thresh: "36"
        eapol-start-flood: "enable"
        eapol-start-intv: "38"
        eapol-start-thresh: "39"
        eapol-succ-flood: "enable"
        eapol-succ-intv: "41"
        eapol-succ-thresh: "42"
        invalid-mac-oui: "enable"
        long-duration-attack: "enable"
        long-duration-thresh: "45"
        name: "default_name_46"
        null-ssid-probe-resp: "enable"
        sensor-mode: "disable"
        spoofed-deauth: "enable"
        weak-wep-iv: "enable"
        wireless-bridge: "enable"
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


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_wireless_controller_wids_profile_data(json):
    option_list = ['ap-auto-suppress', 'ap-bgscan-disable-day', 'ap-bgscan-disable-end',
                   'ap-bgscan-disable-start', 'ap-bgscan-duration', 'ap-bgscan-idle',
                   'ap-bgscan-intv', 'ap-bgscan-period', 'ap-bgscan-report-intv',
                   'ap-fgscan-report-intv', 'ap-scan', 'ap-scan-passive',
                   'asleap-attack', 'assoc-flood-thresh', 'assoc-flood-time',
                   'assoc-frame-flood', 'auth-flood-thresh', 'auth-flood-time',
                   'auth-frame-flood', 'comment', 'deauth-broadcast',
                   'deauth-unknown-src-thresh', 'eapol-fail-flood', 'eapol-fail-intv',
                   'eapol-fail-thresh', 'eapol-logoff-flood', 'eapol-logoff-intv',
                   'eapol-logoff-thresh', 'eapol-pre-fail-flood', 'eapol-pre-fail-intv',
                   'eapol-pre-fail-thresh', 'eapol-pre-succ-flood', 'eapol-pre-succ-intv',
                   'eapol-pre-succ-thresh', 'eapol-start-flood', 'eapol-start-intv',
                   'eapol-start-thresh', 'eapol-succ-flood', 'eapol-succ-intv',
                   'eapol-succ-thresh', 'invalid-mac-oui', 'long-duration-attack',
                   'long-duration-thresh', 'name', 'null-ssid-probe-resp',
                   'sensor-mode', 'spoofed-deauth', 'weak-wep-iv',
                   'wireless-bridge']
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


def wireless_controller_wids_profile(data, fos):
    vdom = data['vdom']
    wireless_controller_wids_profile_data = data['wireless_controller_wids_profile']
    flattened_data = flatten_multilists_attributes(wireless_controller_wids_profile_data)
    filtered_data = filter_wireless_controller_wids_profile_data(flattened_data)
    if wireless_controller_wids_profile_data['state'] == "present":
        return fos.set('wireless-controller',
                       'wids-profile',
                       data=filtered_data,
                       vdom=vdom)

    elif wireless_controller_wids_profile_data['state'] == "absent":
        return fos.delete('wireless-controller',
                          'wids-profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_wireless_controller(data, fos):
    login(data, fos)

    if data['wireless_controller_wids_profile']:
        resp = wireless_controller_wids_profile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "wireless_controller_wids_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "ap-auto-suppress": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "ap-bgscan-disable-day": {"required": False, "type": "str",
                                          "choices": ["sunday", "monday", "tuesday",
                                                      "wednesday", "thursday", "friday",
                                                      "saturday"]},
                "ap-bgscan-disable-end": {"required": False, "type": "str"},
                "ap-bgscan-disable-start": {"required": False, "type": "str"},
                "ap-bgscan-duration": {"required": False, "type": "int"},
                "ap-bgscan-idle": {"required": False, "type": "int"},
                "ap-bgscan-intv": {"required": False, "type": "int"},
                "ap-bgscan-period": {"required": False, "type": "int"},
                "ap-bgscan-report-intv": {"required": False, "type": "int"},
                "ap-fgscan-report-intv": {"required": False, "type": "int"},
                "ap-scan": {"required": False, "type": "str",
                            "choices": ["disable", "enable"]},
                "ap-scan-passive": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "asleap-attack": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "assoc-flood-thresh": {"required": False, "type": "int"},
                "assoc-flood-time": {"required": False, "type": "int"},
                "assoc-frame-flood": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "auth-flood-thresh": {"required": False, "type": "int"},
                "auth-flood-time": {"required": False, "type": "int"},
                "auth-frame-flood": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "comment": {"required": False, "type": "str"},
                "deauth-broadcast": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "deauth-unknown-src-thresh": {"required": False, "type": "int"},
                "eapol-fail-flood": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "eapol-fail-intv": {"required": False, "type": "int"},
                "eapol-fail-thresh": {"required": False, "type": "int"},
                "eapol-logoff-flood": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "eapol-logoff-intv": {"required": False, "type": "int"},
                "eapol-logoff-thresh": {"required": False, "type": "int"},
                "eapol-pre-fail-flood": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "eapol-pre-fail-intv": {"required": False, "type": "int"},
                "eapol-pre-fail-thresh": {"required": False, "type": "int"},
                "eapol-pre-succ-flood": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "eapol-pre-succ-intv": {"required": False, "type": "int"},
                "eapol-pre-succ-thresh": {"required": False, "type": "int"},
                "eapol-start-flood": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "eapol-start-intv": {"required": False, "type": "int"},
                "eapol-start-thresh": {"required": False, "type": "int"},
                "eapol-succ-flood": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "eapol-succ-intv": {"required": False, "type": "int"},
                "eapol-succ-thresh": {"required": False, "type": "int"},
                "invalid-mac-oui": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "long-duration-attack": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "long-duration-thresh": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "null-ssid-probe-resp": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "sensor-mode": {"required": False, "type": "str",
                                "choices": ["disable", "foreign", "both"]},
                "spoofed-deauth": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "weak-wep-iv": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "wireless-bridge": {"required": False, "type": "str",
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

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_wireless_controller(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
