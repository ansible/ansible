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
module: fortios_log_disk_setting
short_description: Settings for local disk logging in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify log_disk feature and setting category.
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
    log_disk_setting:
        description:
            - Settings for local disk logging.
        default: null
        suboptions:
            diskfull:
                description:
                    - Action to take when disk is full. The system can overwrite the oldest log messages or stop logging when the disk is full (default =
                       overwrite).
                choices:
                    - overwrite
                    - nolog
            dlp-archive-quota:
                description:
                    - DLP archive quota (MB).
            full-final-warning-threshold:
                description:
                    - Log full final warning threshold as a percent (3 - 100, default = 95).
            full-first-warning-threshold:
                description:
                    - Log full first warning threshold as a percent (1 - 98, default = 75).
            full-second-warning-threshold:
                description:
                    - Log full second warning threshold as a percent (2 - 99, default = 90).
            ips-archive:
                description:
                    - Enable/disable IPS packet archiving to the local disk.
                choices:
                    - enable
                    - disable
            log-quota:
                description:
                    - Disk log quota (MB).
            max-log-file-size:
                description:
                    - Maximum log file size before rolling (1 - 100 Mbytes).
            max-policy-packet-capture-size:
                description:
                    - Maximum size of policy sniffer in MB (0 means unlimited).
            maximum-log-age:
                description:
                    - Delete log files older than (days).
            report-quota:
                description:
                    - Report quota (MB).
            roll-day:
                description:
                    - Day of week on which to roll log file.
                choices:
                    - sunday
                    - monday
                    - tuesday
                    - wednesday
                    - thursday
                    - friday
                    - saturday
            roll-schedule:
                description:
                    - Frequency to check log file for rolling.
                choices:
                    - daily
                    - weekly
            roll-time:
                description:
                    - "Time of day to roll the log file (hh:mm)."
            source-ip:
                description:
                    - Source IP address to use for uploading disk log files.
            status:
                description:
                    - Enable/disable local disk logging.
                choices:
                    - enable
                    - disable
            upload:
                description:
                    - Enable/disable uploading log files when they are rolled.
                choices:
                    - enable
                    - disable
            upload-delete-files:
                description:
                    - Delete log files after uploading (default = enable).
                choices:
                    - enable
                    - disable
            upload-destination:
                description:
                    - The type of server to upload log files to. Only FTP is currently supported.
                choices:
                    - ftp-server
            upload-ssl-conn:
                description:
                    - Enable/disable encrypted FTPS communication to upload log files.
                choices:
                    - default
                    - high
                    - low
                    - disable
            uploaddir:
                description:
                    - The remote directory on the FTP server to upload log files to.
            uploadip:
                description:
                    - IP address of the FTP server to upload log files to.
            uploadpass:
                description:
                    - Password required to log into the FTP server to upload disk log files.
            uploadport:
                description:
                    - TCP port to use for communicating with the FTP server (default = 21).
            uploadsched:
                description:
                    - Set the schedule for uploading log files to the FTP server (default = disable = upload when rolling).
                choices:
                    - disable
                    - enable
            uploadtime:
                description:
                    - "Time of day at which log files are uploaded if uploadsched is enabled (hh:mm or hh)."
            uploadtype:
                description:
                    - Types of log files to upload. Separate multiple entries with a space.
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
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
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
        dlp-archive-quota: "4"
        full-final-warning-threshold: "5"
        full-first-warning-threshold: "6"
        full-second-warning-threshold: "7"
        ips-archive: "enable"
        log-quota: "9"
        max-log-file-size: "10"
        max-policy-packet-capture-size: "11"
        maximum-log-age: "12"
        report-quota: "13"
        roll-day: "sunday"
        roll-schedule: "daily"
        roll-time: "<your_own_value>"
        source-ip: "84.230.14.43"
        status: "enable"
        upload: "enable"
        upload-delete-files: "enable"
        upload-destination: "ftp-server"
        upload-ssl-conn: "default"
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


def filter_log_disk_setting_data(json):
    option_list = ['diskfull', 'dlp-archive-quota', 'full-final-warning-threshold',
                   'full-first-warning-threshold', 'full-second-warning-threshold', 'ips-archive',
                   'log-quota', 'max-log-file-size', 'max-policy-packet-capture-size',
                   'maximum-log-age', 'report-quota', 'roll-day',
                   'roll-schedule', 'roll-time', 'source-ip',
                   'status', 'upload', 'upload-delete-files',
                   'upload-destination', 'upload-ssl-conn', 'uploaddir',
                   'uploadip', 'uploadpass', 'uploadport',
                   'uploadsched', 'uploadtime', 'uploadtype',
                   'uploaduser']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def log_disk_setting(data, fos):
    vdom = data['vdom']
    log_disk_setting_data = data['log_disk_setting']
    filtered_data = filter_log_disk_setting_data(log_disk_setting_data)
    return fos.set('log.disk',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def fortios_log_disk(data, fos):
    login(data)

    methodlist = ['log_disk_setting']
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
        "log_disk_setting": {
            "required": False, "type": "dict",
            "options": {
                "diskfull": {"required": False, "type": "str",
                             "choices": ["overwrite", "nolog"]},
                "dlp-archive-quota": {"required": False, "type": "int"},
                "full-final-warning-threshold": {"required": False, "type": "int"},
                "full-first-warning-threshold": {"required": False, "type": "int"},
                "full-second-warning-threshold": {"required": False, "type": "int"},
                "ips-archive": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "log-quota": {"required": False, "type": "int"},
                "max-log-file-size": {"required": False, "type": "int"},
                "max-policy-packet-capture-size": {"required": False, "type": "int"},
                "maximum-log-age": {"required": False, "type": "int"},
                "report-quota": {"required": False, "type": "int"},
                "roll-day": {"required": False, "type": "str",
                             "choices": ["sunday", "monday", "tuesday",
                                         "wednesday", "thursday", "friday",
                                         "saturday"]},
                "roll-schedule": {"required": False, "type": "str",
                                  "choices": ["daily", "weekly"]},
                "roll-time": {"required": False, "type": "str"},
                "source-ip": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "upload": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "upload-delete-files": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "upload-destination": {"required": False, "type": "str",
                                       "choices": ["ftp-server"]},
                "upload-ssl-conn": {"required": False, "type": "str",
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
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_log_disk(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
