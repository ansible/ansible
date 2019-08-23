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
module: fortios_log_fortianalyzer_setting
short_description: Global FortiAnalyzer settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify log_fortianalyzer feature and setting category.
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
    log_fortianalyzer_setting:
        description:
            - Global FortiAnalyzer settings.
        default: null
        type: dict
        suboptions:
            __change_ip:
                description:
                    - Hidden attribute.
                type: int
            certificate:
                description:
                    - Certificate used to communicate with FortiAnalyzer. Source certificate.local.name.
                type: str
            conn_timeout:
                description:
                    - FortiAnalyzer connection time-out in seconds (for status and log buffer).
                type: int
            enc_algorithm:
                description:
                    - Enable/disable sending FortiAnalyzer log data with SSL encryption.
                type: str
                choices:
                    - high-medium
                    - high
                    - low
            faz_type:
                description:
                    - Hidden setting index of FortiAnalyzer.
                type: int
            hmac_algorithm:
                description:
                    - FortiAnalyzer IPsec tunnel HMAC algorithm.
                type: str
                choices:
                    - sha256
                    - sha1
            ips_archive:
                description:
                    - Enable/disable IPS packet archive logging.
                type: str
                choices:
                    - enable
                    - disable
            mgmt_name:
                description:
                    - Hidden management name of FortiAnalyzer.
                type: str
            monitor_failure_retry_period:
                description:
                    - Time between FortiAnalyzer connection retries in seconds (for status and log buffer).
                type: int
            monitor_keepalive_period:
                description:
                    - Time between OFTP keepalives in seconds (for status and log buffer).
                type: int
            reliable:
                description:
                    - Enable/disable reliable logging to FortiAnalyzer.
                type: str
                choices:
                    - enable
                    - disable
            server:
                description:
                    - The remote FortiAnalyzer.
                type: str
            source_ip:
                description:
                    - Source IPv4 or IPv6 address used to communicate with FortiAnalyzer.
                type: str
            ssl_min_proto_version:
                description:
                    - Minimum supported protocol version for SSL/TLS connections .
                type: str
                choices:
                    - default
                    - SSLv3
                    - TLSv1
                    - TLSv1-1
                    - TLSv1-2
            status:
                description:
                    - Enable/disable logging to FortiAnalyzer.
                type: str
                choices:
                    - enable
                    - disable
            upload_day:
                description:
                    - Day of week (month) to upload logs.
                type: str
            upload_interval:
                description:
                    - Frequency to upload log files to FortiAnalyzer.
                type: str
                choices:
                    - daily
                    - weekly
                    - monthly
            upload_option:
                description:
                    - Enable/disable logging to hard disk and then uploading to FortiAnalyzer.
                type: str
                choices:
                    - store-and-upload
                    - realtime
                    - 1-minute
                    - 5-minute
            upload_time:
                description:
                    - "Time to upload logs (hh:mm)."
                type: str
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
  - name: Global FortiAnalyzer settings.
    fortios_log_fortianalyzer_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      log_fortianalyzer_setting:
        __change_ip: "3"
        certificate: "<your_own_value> (source certificate.local.name)"
        conn_timeout: "5"
        enc_algorithm: "high-medium"
        faz_type: "7"
        hmac_algorithm: "sha256"
        ips_archive: "enable"
        mgmt_name: "<your_own_value>"
        monitor_failure_retry_period: "11"
        monitor_keepalive_period: "12"
        reliable: "enable"
        server: "192.168.100.40"
        source_ip: "84.230.14.43"
        ssl_min_proto_version: "default"
        status: "enable"
        upload_day: "<your_own_value>"
        upload_interval: "daily"
        upload_option: "store-and-upload"
        upload_time: "<your_own_value>"
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


def filter_log_fortianalyzer_setting_data(json):
    option_list = ['__change_ip', 'certificate', 'conn_timeout',
                   'enc_algorithm', 'faz_type', 'hmac_algorithm',
                   'ips_archive', 'mgmt_name', 'monitor_failure_retry_period',
                   'monitor_keepalive_period', 'reliable', 'server',
                   'source_ip', 'ssl_min_proto_version', 'status',
                   'upload_day', 'upload_interval', 'upload_option',
                   'upload_time']
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


def log_fortianalyzer_setting(data, fos):
    vdom = data['vdom']
    log_fortianalyzer_setting_data = data['log_fortianalyzer_setting']
    filtered_data = underscore_to_hyphen(filter_log_fortianalyzer_setting_data(log_fortianalyzer_setting_data))

    return fos.set('log.fortianalyzer',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_log_fortianalyzer(data, fos):

    if data['log_fortianalyzer_setting']:
        resp = log_fortianalyzer_setting(data, fos)

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
        "log_fortianalyzer_setting": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "__change_ip": {"required": False, "type": "int"},
                "certificate": {"required": False, "type": "str"},
                "conn_timeout": {"required": False, "type": "int"},
                "enc_algorithm": {"required": False, "type": "str",
                                  "choices": ["high-medium", "high", "low"]},
                "faz_type": {"required": False, "type": "int"},
                "hmac_algorithm": {"required": False, "type": "str",
                                   "choices": ["sha256", "sha1"]},
                "ips_archive": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "mgmt_name": {"required": False, "type": "str"},
                "monitor_failure_retry_period": {"required": False, "type": "int"},
                "monitor_keepalive_period": {"required": False, "type": "int"},
                "reliable": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "server": {"required": False, "type": "str"},
                "source_ip": {"required": False, "type": "str"},
                "ssl_min_proto_version": {"required": False, "type": "str",
                                          "choices": ["default", "SSLv3", "TLSv1",
                                                      "TLSv1-1", "TLSv1-2"]},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "upload_day": {"required": False, "type": "str"},
                "upload_interval": {"required": False, "type": "str",
                                    "choices": ["daily", "weekly", "monthly"]},
                "upload_option": {"required": False, "type": "str",
                                  "choices": ["store-and-upload", "realtime", "1-minute",
                                              "5-minute"]},
                "upload_time": {"required": False, "type": "str"}

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

            is_error, has_changed, result = fortios_log_fortianalyzer(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_log_fortianalyzer(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
