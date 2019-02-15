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
module: fortios_log_threat_weight
short_description: Configure threat weight settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify log feature and threat_weight category.
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
    log_threat_weight:
        description:
            - Configure threat weight settings.
        default: null
        suboptions:
            application:
                description:
                    - Application-control threat weight settings.
                suboptions:
                    category:
                        description:
                            - Application category.
                    id:
                        description:
                            - Entry ID.
                        required: true
                    level:
                        description:
                            - Threat weight score for Application events.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
            blocked-connection:
                description:
                    - Threat weight score for blocked connections.
                choices:
                    - disable
                    - low
                    - medium
                    - high
                    - critical
            failed-connection:
                description:
                    - Threat weight score for failed connections.
                choices:
                    - disable
                    - low
                    - medium
                    - high
                    - critical
            geolocation:
                description:
                    - Geolocation-based threat weight settings.
                suboptions:
                    country:
                        description:
                            - Country code.
                    id:
                        description:
                            - Entry ID.
                        required: true
                    level:
                        description:
                            - Threat weight score for Geolocation-based events.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
            ips:
                description:
                    - IPS threat weight settings.
                suboptions:
                    critical-severity:
                        description:
                            - Threat weight score for IPS critical severity events.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    high-severity:
                        description:
                            - Threat weight score for IPS high severity events.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    info-severity:
                        description:
                            - Threat weight score for IPS info severity events.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    low-severity:
                        description:
                            - Threat weight score for IPS low severity events.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    medium-severity:
                        description:
                            - Threat weight score for IPS medium severity events.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
            level:
                description:
                    - Score mapping for threat weight levels.
                suboptions:
                    critical:
                        description:
                            - Critical level score value (1 - 100).
                    high:
                        description:
                            - High level score value (1 - 100).
                    low:
                        description:
                            - Low level score value (1 - 100).
                    medium:
                        description:
                            - Medium level score value (1 - 100).
            malware:
                description:
                    - Anti-virus malware threat weight settings.
                suboptions:
                    botnet-connection:
                        description:
                            - Threat weight score for detected botnet connections.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    command-blocked:
                        description:
                            - Threat weight score for blocked command detected.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    mimefragmented:
                        description:
                            - Threat weight score for mimefragmented detected.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    oversized:
                        description:
                            - Threat weight score for oversized file detected.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    switch-proto:
                        description:
                            - Threat weight score for switch proto detected.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus-blocked:
                        description:
                            - Threat weight score for virus (blocked) detected.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus-file-type-executable:
                        description:
                            - Threat weight score for virus (filetype executable) detected.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus-infected:
                        description:
                            - Threat weight score for virus (infected) detected.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus-outbreak-prevention:
                        description:
                            - Threat weight score for virus (outbreak prevention) event.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus-scan-error:
                        description:
                            - Threat weight score for virus (scan error) detected.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
            status:
                description:
                    - Enable/disable the threat weight feature.
                choices:
                    - enable
                    - disable
            url-block-detected:
                description:
                    - Threat weight score for URL blocking.
                choices:
                    - disable
                    - low
                    - medium
                    - high
                    - critical
            web:
                description:
                    - Web filtering threat weight settings.
                suboptions:
                    category:
                        description:
                            - Threat weight score for web category filtering matches.
                    id:
                        description:
                            - Entry ID.
                        required: true
                    level:
                        description:
                            - Threat weight score for web category filtering matches.
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure threat weight settings.
    fortios_log_threat_weight:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      log_threat_weight:
        application:
         -
            category: "4"
            id:  "5"
            level: "disable"
        blocked-connection: "disable"
        failed-connection: "disable"
        geolocation:
         -
            country: "<your_own_value>"
            id:  "11"
            level: "disable"
        ips:
            critical-severity: "disable"
            high-severity: "disable"
            info-severity: "disable"
            low-severity: "disable"
            medium-severity: "disable"
        level:
            critical: "20"
            high: "21"
            low: "22"
            medium: "23"
        malware:
            botnet-connection: "disable"
            command-blocked: "disable"
            mimefragmented: "disable"
            oversized: "disable"
            switch-proto: "disable"
            virus-blocked: "disable"
            virus-file-type-executable: "disable"
            virus-infected: "disable"
            virus-outbreak-prevention: "disable"
            virus-scan-error: "disable"
        status: "enable"
        url-block-detected: "disable"
        web:
         -
            category: "38"
            id:  "39"
            level: "disable"
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


def filter_log_threat_weight_data(json):
    option_list = ['application', 'blocked-connection', 'failed-connection',
                   'geolocation', 'ips', 'level',
                   'malware', 'status', 'url-block-detected',
                   'web']
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


def log_threat_weight(data, fos):
    vdom = data['vdom']
    log_threat_weight_data = data['log_threat_weight']
    flattened_data = flatten_multilists_attributes(log_threat_weight_data)
    filtered_data = filter_log_threat_weight_data(flattened_data)
    return fos.set('log',
                   'threat-weight',
                   data=filtered_data,
                   vdom=vdom)


def fortios_log(data, fos):
    login(data)

    if data['log_threat_weight']:
        resp = log_threat_weight(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "log_threat_weight": {
            "required": False, "type": "dict",
            "options": {
                "application": {"required": False, "type": "list",
                                "options": {
                                    "category": {"required": False, "type": "int"},
                                    "id": {"required": True, "type": "int"},
                                    "level": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]}
                                }},
                "blocked-connection": {"required": False, "type": "str",
                                       "choices": ["disable", "low", "medium",
                                                   "high", "critical"]},
                "failed-connection": {"required": False, "type": "str",
                                      "choices": ["disable", "low", "medium",
                                                  "high", "critical"]},
                "geolocation": {"required": False, "type": "list",
                                "options": {
                                    "country": {"required": False, "type": "str"},
                                    "id": {"required": True, "type": "int"},
                                    "level": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]}
                                }},
                "ips": {"required": False, "type": "dict",
                        "options": {
                            "critical-severity": {"required": False, "type": "str",
                                                  "choices": ["disable", "low", "medium",
                                                              "high", "critical"]},
                            "high-severity": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]},
                            "info-severity": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]},
                            "low-severity": {"required": False, "type": "str",
                                             "choices": ["disable", "low", "medium",
                                                         "high", "critical"]},
                            "medium-severity": {"required": False, "type": "str",
                                                "choices": ["disable", "low", "medium",
                                                            "high", "critical"]}
                        }},
                "level": {"required": False, "type": "dict",
                          "options": {
                              "critical": {"required": False, "type": "int"},
                              "high": {"required": False, "type": "int"},
                              "low": {"required": False, "type": "int"},
                              "medium": {"required": False, "type": "int"}
                          }},
                "malware": {"required": False, "type": "dict",
                            "options": {
                                "botnet-connection": {"required": False, "type": "str",
                                                      "choices": ["disable", "low", "medium",
                                                                  "high", "critical"]},
                                "command-blocked": {"required": False, "type": "str",
                                                    "choices": ["disable", "low", "medium",
                                                                "high", "critical"]},
                                "mimefragmented": {"required": False, "type": "str",
                                                   "choices": ["disable", "low", "medium",
                                                               "high", "critical"]},
                                "oversized": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]},
                                "switch-proto": {"required": False, "type": "str",
                                                 "choices": ["disable", "low", "medium",
                                                             "high", "critical"]},
                                "virus-blocked": {"required": False, "type": "str",
                                                  "choices": ["disable", "low", "medium",
                                                              "high", "critical"]},
                                "virus-file-type-executable": {"required": False, "type": "str",
                                                               "choices": ["disable", "low", "medium",
                                                                           "high", "critical"]},
                                "virus-infected": {"required": False, "type": "str",
                                                   "choices": ["disable", "low", "medium",
                                                               "high", "critical"]},
                                "virus-outbreak-prevention": {"required": False, "type": "str",
                                                              "choices": ["disable", "low", "medium",
                                                                          "high", "critical"]},
                                "virus-scan-error": {"required": False, "type": "str",
                                                     "choices": ["disable", "low", "medium",
                                                                 "high", "critical"]}
                            }},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "url-block-detected": {"required": False, "type": "str",
                                       "choices": ["disable", "low", "medium",
                                                   "high", "critical"]},
                "web": {"required": False, "type": "list",
                        "options": {
                            "category": {"required": False, "type": "int"},
                            "id": {"required": True, "type": "int"},
                            "level": {"required": False, "type": "str",
                                      "choices": ["disable", "low", "medium",
                                                  "high", "critical"]}
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

    is_error, has_changed, result = fortios_log(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
