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
module: fortios_log_syslogd2_setting
short_description: Global settings for remote syslog server in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify log_syslogd2 feature and setting category.
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
    log_syslogd2_setting:
        description:
            - Global settings for remote syslog server.
        default: null
        suboptions:
            certificate:
                description:
                    - Certificate used to communicate with Syslog server. Source certificate.local.name.
            custom-field-name:
                description:
                    - Custom field name for CEF format logging.
                suboptions:
                    custom:
                        description:
                            - Field custom name.
                    id:
                        description:
                            - Entry ID.
                        required: true
                    name:
                        description:
                            - Field name.
            enc-algorithm:
                description:
                    - Enable/disable reliable syslogging with TLS encryption.
                choices:
                    - high-medium
                    - high
                    - low
                    - disable
            facility:
                description:
                    - Remote syslog facility.
                choices:
                    - kernel
                    - user
                    - mail
                    - daemon
                    - auth
                    - syslog
                    - lpr
                    - news
                    - uucp
                    - cron
                    - authpriv
                    - ftp
                    - ntp
                    - audit
                    - alert
                    - clock
                    - local0
                    - local1
                    - local2
                    - local3
                    - local4
                    - local5
                    - local6
                    - local7
            format:
                description:
                    - Log format.
                choices:
                    - default
                    - csv
                    - cef
            mode:
                description:
                    - Remote syslog logging over UDP/Reliable TCP.
                choices:
                    - udp
                    - legacy-reliable
                    - reliable
            port:
                description:
                    - Server listen port.
            server:
                description:
                    - Address of remote syslog server.
            source-ip:
                description:
                    - Source IP address of syslog.
            status:
                description:
                    - Enable/disable remote syslog logging.
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
  - name: Global settings for remote syslog server.
    fortios_log_syslogd2_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      log_syslogd2_setting:
        certificate: "<your_own_value> (source certificate.local.name)"
        custom-field-name:
         -
            custom: "<your_own_value>"
            id:  "6"
            name: "default_name_7"
        enc-algorithm: "high-medium"
        facility: "kernel"
        format: "default"
        mode: "udp"
        port: "12"
        server: "192.168.100.40"
        source-ip: "84.230.14.43"
        status: "enable"
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


def filter_log_syslogd2_setting_data(json):
    option_list = ['certificate', 'custom-field-name', 'enc-algorithm',
                   'facility', 'format', 'mode',
                   'port', 'server', 'source-ip',
                   'status']
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


def log_syslogd2_setting(data, fos):
    vdom = data['vdom']
    log_syslogd2_setting_data = data['log_syslogd2_setting']
    flattened_data = flatten_multilists_attributes(log_syslogd2_setting_data)
    filtered_data = filter_log_syslogd2_setting_data(flattened_data)
    return fos.set('log.syslogd2',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def fortios_log_syslogd2(data, fos):
    login(data)

    if data['log_syslogd2_setting']:
        resp = log_syslogd2_setting(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "log_syslogd2_setting": {
            "required": False, "type": "dict",
            "options": {
                "certificate": {"required": False, "type": "str"},
                "custom-field-name": {"required": False, "type": "list",
                                      "options": {
                                          "custom": {"required": False, "type": "str"},
                                          "id": {"required": True, "type": "int"},
                                          "name": {"required": False, "type": "str"}
                                      }},
                "enc-algorithm": {"required": False, "type": "str",
                                  "choices": ["high-medium", "high", "low",
                                              "disable"]},
                "facility": {"required": False, "type": "str",
                             "choices": ["kernel", "user", "mail",
                                         "daemon", "auth", "syslog",
                                         "lpr", "news", "uucp",
                                         "cron", "authpriv", "ftp",
                                         "ntp", "audit", "alert",
                                         "clock", "local0", "local1",
                                         "local2", "local3", "local4",
                                         "local5", "local6", "local7"]},
                "format": {"required": False, "type": "str",
                           "choices": ["default", "csv", "cef"]},
                "mode": {"required": False, "type": "str",
                         "choices": ["udp", "legacy-reliable", "reliable"]},
                "port": {"required": False, "type": "int"},
                "server": {"required": False, "type": "str"},
                "source-ip": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
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

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_log_syslogd2(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
