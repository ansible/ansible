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
module: fortios_log_disk_setting
short_description: Settings for local disk logging in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify log_disk feature and setting category.
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
    log_disk_setting:
        description:
            - Settings for local disk logging.
        default: null
        type: dict
        suboptions:
            diskfull:
                description:
                    - Action to take when disk is full. The system can overwrite the oldest log messages or stop logging when the disk is full .
                type: str
                choices:
                    - overwrite
                    - nolog
            dlp_archive_quota:
                description:
                    - DLP archive quota (MB).
                type: int
            full_final_warning_threshold:
                description:
                    - Log full final warning threshold as a percent (3 - 100).
                type: int
            full_first_warning_threshold:
                description:
                    - Log full first warning threshold as a percent (1 - 98).
                type: int
            full_second_warning_threshold:
                description:
                    - Log full second warning threshold as a percent (2 - 99).
                type: int
            ips_archive:
                description:
                    - Enable/disable IPS packet archiving to the local disk.
                type: str
                choices:
                    - enable
                    - disable
            log_quota:
                description:
                    - Disk log quota (MB).
                type: int
            max_log_file_size:
                description:
                    - Maximum log file size before rolling (1 - 100 Mbytes).
                type: int
            max_policy_packet_capture_size:
                description:
                    - Maximum size of policy sniffer in MB (0 means unlimited).
                type: int
            maximum_log_age:
                description:
                    - Delete log files older than (days).
                type: int
            report_quota:
                description:
                    - Report quota (MB).
                type: int
            roll_day:
                description:
                    - Day of week on which to roll log file.
                type: str
                choices:
                    - sunday
                    - monday
                    - tuesday
                    - wednesday
                    - thursday
                    - friday
                    - saturday
            roll_schedule:
                description:
                    - Frequency to check log file for rolling.
                type: str
                choices:
                    - daily
                    - weekly
            roll_time:
                description:
                    - "Time of day to roll the log file (hh:mm)."
                type: str
            source_ip:
                description:
                    - Source IP address to use for uploading disk log files.
                type: str
            status:
                description:
                    - Enable/disable local disk logging.
                type: str
                choices:
                    - enable
                    - disable
            upload:
                description:
                    - Enable/disable uploading log files when they are rolled.
                type: str
                choices:
                    - enable
                    - disable
            upload_delete_files:
                description:
                    - Delete log files after uploading .
                type: str
                choices:
                    - enable
                    - disable
            upload_destination:
                description:
                    - The type of server to upload log files to. Only FTP is currently supported.
                type: str
                choices:
                    - ftp-server
            upload_ssl_conn:
                description:
                    - Enable/disable encrypted FTPS communication to upload log files.
                type: str
                choices:
                    - default
                    - high
                    - low
                    - disable
            uploaddir:
                description:
                    - The remote directory on the FTP server to upload log files to.
                type: str
            uploadip:
                description:
                    - IP address of the FTP server to upload log files to.
                type: str
            uploadpass:
                description:
                    - Password required to log into the FTP server to upload disk log files.
                type: str
            uploadport:
                description:
                    - TCP port to use for communicating with the FTP server .
                type: int
            uploadsched:
                description:
                    - Set the schedule for uploading log files to the FTP server .
                type: str
                choices:
                    - disable
                    - enable
            uploadtime:
                description:
                    - "Time of day at which log files are uploaded if uploadsched is enabled (hh:mm or hh)."
                type: str
            uploadtype:
                description:
                    - Types of log files to upload. Separate multiple entries with a space.
                type: str
                choices:
                    - traffic
                    - event
                    - virus
                    - webfilter
                    - IPS
                    - spamfilter
                    - dlp-archive
                    - anomaly
                    - voip
                    - dlp
                    - app-ctrl
                    - waf
                    - netscan
                    - gtp
                    - dns
            uploaduser:
                description:
                    - Username required to log into the FTP server to upload disk log files.
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
  - name: Settings for local disk logging.
    fortios_log_disk_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      log_disk_setting:
        diskfull: "overwrite"
        dlp_archive_quota: "4"
        full_final_warning_threshold: "5"
        full_first_warning_threshold: "6"
        full_second_warning_threshold: "7"
        ips_archive: "enable"
        log_quota: "9"
        max_log_file_size: "10"
        max_policy_packet_capture_size: "11"
        maximum_log_age: "12"
        report_quota: "13"
        roll_day: "sunday"
        roll_schedule: "daily"
        roll_time: "<your_own_value>"
        source_ip: "84.230.14.43"
        status: "enable"
        upload: "enable"
        upload_delete_files: "enable"
        upload_destination: "ftp-server"
        upload_ssl_conn: "default"
        uploaddir: "<your_own_value>"
        uploadip: "<your_own_value>"
        uploadpass: "<your_own_value>"
        uploadport: "26"
        uploadsched: "disable"
        uploadtime: "<your_own_value>"
        uploadtype: "traffic"
        uploaduser: "<your_own_value>"
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


def filter_log_disk_setting_data(json):
    option_list = ['diskfull', 'dlp_archive_quota', 'full_final_warning_threshold',
                   'full_first_warning_threshold', 'full_second_warning_threshold', 'ips_archive',
                   'log_quota', 'max_log_file_size', 'max_policy_packet_capture_size',
                   'maximum_log_age', 'report_quota', 'roll_day',
                   'roll_schedule', 'roll_time', 'source_ip',
                   'status', 'upload', 'upload_delete_files',
                   'upload_destination', 'upload_ssl_conn', 'uploaddir',
                   'uploadip', 'uploadpass', 'uploadport',
                   'uploadsched', 'uploadtime', 'uploadtype',
                   'uploaduser']
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


def log_disk_setting(data, fos):
    vdom = data['vdom']
    log_disk_setting_data = data['log_disk_setting']
    filtered_data = underscore_to_hyphen(filter_log_disk_setting_data(log_disk_setting_data))

    return fos.set('log.disk',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_log_disk(data, fos):

    if data['log_disk_setting']:
        resp = log_disk_setting(data, fos)

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
        "log_disk_setting": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "diskfull": {"required": False, "type": "str",
                             "choices": ["overwrite", "nolog"]},
                "dlp_archive_quota": {"required": False, "type": "int"},
                "full_final_warning_threshold": {"required": False, "type": "int"},
                "full_first_warning_threshold": {"required": False, "type": "int"},
                "full_second_warning_threshold": {"required": False, "type": "int"},
                "ips_archive": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "log_quota": {"required": False, "type": "int"},
                "max_log_file_size": {"required": False, "type": "int"},
                "max_policy_packet_capture_size": {"required": False, "type": "int"},
                "maximum_log_age": {"required": False, "type": "int"},
                "report_quota": {"required": False, "type": "int"},
                "roll_day": {"required": False, "type": "str",
                             "choices": ["sunday", "monday", "tuesday",
                                         "wednesday", "thursday", "friday",
                                         "saturday"]},
                "roll_schedule": {"required": False, "type": "str",
                                  "choices": ["daily", "weekly"]},
                "roll_time": {"required": False, "type": "str"},
                "source_ip": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "upload": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "upload_delete_files": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "upload_destination": {"required": False, "type": "str",
                                       "choices": ["ftp-server"]},
                "upload_ssl_conn": {"required": False, "type": "str",
                                    "choices": ["default", "high", "low",
                                                "disable"]},
                "uploaddir": {"required": False, "type": "str"},
                "uploadip": {"required": False, "type": "str"},
                "uploadpass": {"required": False, "type": "str"},
                "uploadport": {"required": False, "type": "int"},
                "uploadsched": {"required": False, "type": "str",
                                "choices": ["disable", "enable"]},
                "uploadtime": {"required": False, "type": "str"},
                "uploadtype": {"required": False, "type": "str",
                               "choices": ["traffic", "event", "virus",
                                           "webfilter", "IPS", "spamfilter",
                                           "dlp-archive", "anomaly", "voip",
                                           "dlp", "app-ctrl", "waf",
                                           "netscan", "gtp", "dns"]},
                "uploaduser": {"required": False, "type": "str"}

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

            is_error, has_changed, result = fortios_log_disk(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_log_disk(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
