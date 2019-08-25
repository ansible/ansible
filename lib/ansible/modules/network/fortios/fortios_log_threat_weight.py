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
module: fortios_log_threat_weight
short_description: Configure threat weight settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify log feature and threat_weight category.
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
    log_threat_weight:
        description:
            - Configure threat weight settings.
        default: null
        type: dict
        suboptions:
            application:
                description:
                    - Application-control threat weight settings.
                type: list
                suboptions:
                    category:
                        description:
                            - Application category.
                        type: int
                    id:
                        description:
                            - Entry ID.
                        required: true
                        type: int
                    level:
                        description:
                            - Threat weight score for Application events.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
            blocked_connection:
                description:
                    - Threat weight score for blocked connections.
                type: str
                choices:
                    - disable
                    - low
                    - medium
                    - high
                    - critical
            failed_connection:
                description:
                    - Threat weight score for failed connections.
                type: str
                choices:
                    - disable
                    - low
                    - medium
                    - high
                    - critical
            geolocation:
                description:
                    - Geolocation-based threat weight settings.
                type: list
                suboptions:
                    country:
                        description:
                            - Country code.
                        type: str
                    id:
                        description:
                            - Entry ID.
                        required: true
                        type: int
                    level:
                        description:
                            - Threat weight score for Geolocation-based events.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
            ips:
                description:
                    - IPS threat weight settings.
                type: dict
                suboptions:
                    critical_severity:
                        description:
                            - Threat weight score for IPS critical severity events.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    high_severity:
                        description:
                            - Threat weight score for IPS high severity events.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    info_severity:
                        description:
                            - Threat weight score for IPS info severity events.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    low_severity:
                        description:
                            - Threat weight score for IPS low severity events.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    medium_severity:
                        description:
                            - Threat weight score for IPS medium severity events.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
            level:
                description:
                    - Score mapping for threat weight levels.
                type: dict
                suboptions:
                    critical:
                        description:
                            - Critical level score value (1 - 100).
                        type: int
                    high:
                        description:
                            - High level score value (1 - 100).
                        type: int
                    low:
                        description:
                            - Low level score value (1 - 100).
                        type: int
                    medium:
                        description:
                            - Medium level score value (1 - 100).
                        type: int
            malware:
                description:
                    - Anti-virus malware threat weight settings.
                type: dict
                suboptions:
                    botnet_connection:
                        description:
                            - Threat weight score for detected botnet connections.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    command_blocked:
                        description:
                            - Threat weight score for blocked command detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    content_disarm:
                        description:
                            - Threat weight score for virus (content disarm) detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    mimefragmented:
                        description:
                            - Threat weight score for mimefragmented detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    oversized:
                        description:
                            - Threat weight score for oversized file detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    switch_proto:
                        description:
                            - Threat weight score for switch proto detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus_blocked:
                        description:
                            - Threat weight score for virus (blocked) detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus_file_type_executable:
                        description:
                            - Threat weight score for virus (filetype executable) detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus_infected:
                        description:
                            - Threat weight score for virus (infected) detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus_outbreak_prevention:
                        description:
                            - Threat weight score for virus (outbreak prevention) event.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
                    virus_scan_error:
                        description:
                            - Threat weight score for virus (scan error) detected.
                        type: str
                        choices:
                            - disable
                            - low
                            - medium
                            - high
                            - critical
            status:
                description:
                    - Enable/disable the threat weight feature.
                type: str
                choices:
                    - enable
                    - disable
            url_block_detected:
                description:
                    - Threat weight score for URL blocking.
                type: str
                choices:
                    - disable
                    - low
                    - medium
                    - high
                    - critical
            web:
                description:
                    - Web filtering threat weight settings.
                type: list
                suboptions:
                    category:
                        description:
                            - Threat weight score for web category filtering matches.
                        type: int
                    id:
                        description:
                            - Entry ID.
                        required: true
                        type: int
                    level:
                        description:
                            - Threat weight score for web category filtering matches.
                        type: str
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
   ssl_verify: "False"
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
        blocked_connection: "disable"
        failed_connection: "disable"
        geolocation:
         -
            country: "<your_own_value>"
            id:  "11"
            level: "disable"
        ips:
            critical_severity: "disable"
            high_severity: "disable"
            info_severity: "disable"
            low_severity: "disable"
            medium_severity: "disable"
        level:
            critical: "20"
            high: "21"
            low: "22"
            medium: "23"
        malware:
            botnet_connection: "disable"
            command_blocked: "disable"
            content_disarm: "disable"
            mimefragmented: "disable"
            oversized: "disable"
            switch_proto: "disable"
            virus_blocked: "disable"
            virus_file_type_executable: "disable"
            virus_infected: "disable"
            virus_outbreak_prevention: "disable"
            virus_scan_error: "disable"
        status: "enable"
        url_block_detected: "disable"
        web:
         -
            category: "39"
            id:  "40"
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


def filter_log_threat_weight_data(json):
    option_list = ['application', 'blocked_connection', 'failed_connection',
                   'geolocation', 'ips', 'level',
                   'malware', 'status', 'url_block_detected',
                   'web']
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


def log_threat_weight(data, fos):
    vdom = data['vdom']
    log_threat_weight_data = data['log_threat_weight']
    filtered_data = underscore_to_hyphen(filter_log_threat_weight_data(log_threat_weight_data))

    return fos.set('log',
                   'threat-weight',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_log(data, fos):

    if data['log_threat_weight']:
        resp = log_threat_weight(data, fos)

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
        "log_threat_weight": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "application": {"required": False, "type": "list",
                                "options": {
                                    "category": {"required": False, "type": "int"},
                                    "id": {"required": True, "type": "int"},
                                    "level": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]}
                                }},
                "blocked_connection": {"required": False, "type": "str",
                                       "choices": ["disable", "low", "medium",
                                                   "high", "critical"]},
                "failed_connection": {"required": False, "type": "str",
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
                            "critical_severity": {"required": False, "type": "str",
                                                  "choices": ["disable", "low", "medium",
                                                              "high", "critical"]},
                            "high_severity": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]},
                            "info_severity": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]},
                            "low_severity": {"required": False, "type": "str",
                                             "choices": ["disable", "low", "medium",
                                                         "high", "critical"]},
                            "medium_severity": {"required": False, "type": "str",
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
                                "botnet_connection": {"required": False, "type": "str",
                                                      "choices": ["disable", "low", "medium",
                                                                  "high", "critical"]},
                                "command_blocked": {"required": False, "type": "str",
                                                    "choices": ["disable", "low", "medium",
                                                                "high", "critical"]},
                                "content_disarm": {"required": False, "type": "str",
                                                   "choices": ["disable", "low", "medium",
                                                               "high", "critical"]},
                                "mimefragmented": {"required": False, "type": "str",
                                                   "choices": ["disable", "low", "medium",
                                                               "high", "critical"]},
                                "oversized": {"required": False, "type": "str",
                                              "choices": ["disable", "low", "medium",
                                                          "high", "critical"]},
                                "switch_proto": {"required": False, "type": "str",
                                                 "choices": ["disable", "low", "medium",
                                                             "high", "critical"]},
                                "virus_blocked": {"required": False, "type": "str",
                                                  "choices": ["disable", "low", "medium",
                                                              "high", "critical"]},
                                "virus_file_type_executable": {"required": False, "type": "str",
                                                               "choices": ["disable", "low", "medium",
                                                                           "high", "critical"]},
                                "virus_infected": {"required": False, "type": "str",
                                                   "choices": ["disable", "low", "medium",
                                                               "high", "critical"]},
                                "virus_outbreak_prevention": {"required": False, "type": "str",
                                                              "choices": ["disable", "low", "medium",
                                                                          "high", "critical"]},
                                "virus_scan_error": {"required": False, "type": "str",
                                                     "choices": ["disable", "low", "medium",
                                                                 "high", "critical"]}
                            }},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "url_block_detected": {"required": False, "type": "str",
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

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_log(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_log(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
