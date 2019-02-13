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
module: fortios_log_fortianalyzer2_setting
short_description: Global FortiAnalyzer settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify log_fortianalyzer2 feature and setting category.
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
    log_fortianalyzer2_setting:
        description:
            - Global FortiAnalyzer settings.
        default: null
        suboptions:
            __change_ip:
                description:
                    - Hidden attribute.
            certificate:
                description:
                    - Certificate used to communicate with FortiAnalyzer. Source certificate.local.name.
            conn-timeout:
                description:
                    - FortiAnalyzer connection time-out in seconds (for status and log buffer).
            enc-algorithm:
                description:
                    - Enable/disable sending FortiAnalyzer log data with SSL encryption.
                choices:
                    - high-medium
                    - high
                    - low
                    - disable
            faz-type:
                description:
                    - Hidden setting index of FortiAnalyzer.
            hmac-algorithm:
                description:
                    - FortiAnalyzer IPsec tunnel HMAC algorithm.
                choices:
                    - sha256
                    - sha1
            ips-archive:
                description:
                    - Enable/disable IPS packet archive logging.
                choices:
                    - enable
                    - disable
            mgmt-name:
                description:
                    - Hidden management name of FortiAnalyzer.
            monitor-failure-retry-period:
                description:
                    - Time between FortiAnalyzer connection retries in seconds (for status and log buffer).
            monitor-keepalive-period:
                description:
                    - Time between OFTP keepalives in seconds (for status and log buffer).
            reliable:
                description:
                    - Enable/disable reliable logging to FortiAnalyzer.
                choices:
                    - enable
                    - disable
            server:
                description:
                    - The remote FortiAnalyzer.
            source-ip:
                description:
                    - Source IPv4 or IPv6 address used to communicate with FortiAnalyzer.
            ssl-min-proto-version:
                description:
                    - Minimum supported protocol version for SSL/TLS connections (default is to follow system global setting).
                choices:
                    - default
                    - SSLv3
                    - TLSv1
                    - TLSv1-1
                    - TLSv1-2
            status:
                description:
                    - Enable/disable logging to FortiAnalyzer.
                choices:
                    - enable
                    - disable
            upload-day:
                description:
                    - Day of week (month) to upload logs.
            upload-interval:
                description:
                    - Frequency to upload log files to FortiAnalyzer.
                choices:
                    - daily
                    - weekly
                    - monthly
            upload-option:
                description:
                    - Enable/disable logging to hard disk and then uploading to FortiAnalyzer.
                choices:
                    - store-and-upload
                    - realtime
                    - 1-minute
                    - 5-minute
            upload-time:
                description:
                    - "Time to upload logs (hh:mm)."
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Global FortiAnalyzer settings.
    fortios_log_fortianalyzer2_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      log_fortianalyzer2_setting:
        __change_ip: "3"
        certificate: "<your_own_value> (source certificate.local.name)"
        conn-timeout: "5"
        enc-algorithm: "high-medium"
        faz-type: "7"
        hmac-algorithm: "sha256"
        ips-archive: "enable"
        mgmt-name: "<your_own_value>"
        monitor-failure-retry-period: "11"
        monitor-keepalive-period: "12"
        reliable: "enable"
        server: "192.168.100.40"
        source-ip: "84.230.14.43"
        ssl-min-proto-version: "default"
        status: "enable"
        upload-day: "<your_own_value>"
        upload-interval: "daily"
        upload-option: "store-and-upload"
        upload-time: "<your_own_value>"
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


def filter_log_fortianalyzer2_setting_data(json):
    option_list = ['__change_ip', 'certificate', 'conn-timeout',
                   'enc-algorithm', 'faz-type', 'hmac-algorithm',
                   'ips-archive', 'mgmt-name', 'monitor-failure-retry-period',
                   'monitor-keepalive-period', 'reliable', 'server',
                   'source-ip', 'ssl-min-proto-version', 'status',
                   'upload-day', 'upload-interval', 'upload-option',
                   'upload-time']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def log_fortianalyzer2_setting(data, fos):
    vdom = data['vdom']
    log_fortianalyzer2_setting_data = data['log_fortianalyzer2_setting']
    filtered_data = filter_log_fortianalyzer2_setting_data(log_fortianalyzer2_setting_data)
    return fos.set('log.fortianalyzer2',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def fortios_log_fortianalyzer2(data, fos):
    login(data)

    methodlist = ['log_fortianalyzer2_setting']
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
        "log_fortianalyzer2_setting": {
            "required": False, "type": "dict",
            "options": {
                "__change_ip": {"required": False, "type": "int"},
                "certificate": {"required": False, "type": "str"},
                "conn-timeout": {"required": False, "type": "int"},
                "enc-algorithm": {"required": False, "type": "str",
                                  "choices": ["high-medium", "high", "low",
                                              "disable"]},
                "faz-type": {"required": False, "type": "int"},
                "hmac-algorithm": {"required": False, "type": "str",
                                   "choices": ["sha256", "sha1"]},
                "ips-archive": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "mgmt-name": {"required": False, "type": "str"},
                "monitor-failure-retry-period": {"required": False, "type": "int"},
                "monitor-keepalive-period": {"required": False, "type": "int"},
                "reliable": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "server": {"required": False, "type": "str"},
                "source-ip": {"required": False, "type": "str"},
                "ssl-min-proto-version": {"required": False, "type": "str",
                                          "choices": ["default", "SSLv3", "TLSv1",
                                                      "TLSv1-1", "TLSv1-2"]},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "upload-day": {"required": False, "type": "str"},
                "upload-interval": {"required": False, "type": "str",
                                    "choices": ["daily", "weekly", "monthly"]},
                "upload-option": {"required": False, "type": "str",
                                  "choices": ["store-and-upload", "realtime", "1-minute",
                                              "5-minute"]},
                "upload-time": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_log_fortianalyzer2(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
