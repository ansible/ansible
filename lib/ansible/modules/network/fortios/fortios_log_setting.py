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
module: fortios_log_setting
short_description: Configure general log settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify log feature and setting category.
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
    log_setting:
        description:
            - Configure general log settings.
        default: null
        suboptions:
            brief-traffic-format:
                description:
                    - Enable/disable brief format traffic logging.
                choices:
                    - enable
                    - disable
            custom-log-fields:
                description:
                    - Custom fields to append to all log messages.
                suboptions:
                    field-id:
                        description:
                            - Custom log field. Source log.custom-field.id.
                        required: true
            daemon-log:
                description:
                    - Enable/disable daemon logging.
                choices:
                    - enable
                    - disable
            expolicy-implicit-log:
                description:
                    - Enable/disable explicit proxy firewall implicit policy logging.
                choices:
                    - enable
                    - disable
            fwpolicy-implicit-log:
                description:
                    - Enable/disable implicit firewall policy logging.
                choices:
                    - enable
                    - disable
            fwpolicy6-implicit-log:
                description:
                    - Enable/disable implicit firewall policy6 logging.
                choices:
                    - enable
                    - disable
            local-in-allow:
                description:
                    - Enable/disable local-in-allow logging.
                choices:
                    - enable
                    - disable
            local-in-deny-broadcast:
                description:
                    - Enable/disable local-in-deny-broadcast logging.
                choices:
                    - enable
                    - disable
            local-in-deny-unicast:
                description:
                    - Enable/disable local-in-deny-unicast logging.
                choices:
                    - enable
                    - disable
            local-out:
                description:
                    - Enable/disable local-out logging.
                choices:
                    - enable
                    - disable
            log-invalid-packet:
                description:
                    - Enable/disable invalid packet traffic logging.
                choices:
                    - enable
                    - disable
            log-policy-comment:
                description:
                    - Enable/disable inserting policy comments into traffic logs.
                choices:
                    - enable
                    - disable
            log-policy-name:
                description:
                    - Enable/disable inserting policy name into traffic logs.
                choices:
                    - enable
                    - disable
            log-user-in-upper:
                description:
                    - Enable/disable logs with user-in-upper.
                choices:
                    - enable
                    - disable
            neighbor-event:
                description:
                    - Enable/disable neighbor event logging.
                choices:
                    - enable
                    - disable
            resolve-ip:
                description:
                    - Enable/disable adding resolved domain names to traffic logs if possible.
                choices:
                    - enable
                    - disable
            resolve-port:
                description:
                    - Enable/disable adding resolved service names to traffic logs.
                choices:
                    - enable
                    - disable
            user-anonymize:
                description:
                    - Enable/disable anonymizing user names in log messages.
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
  - name: Configure general log settings.
    fortios_log_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      log_setting:
        brief-traffic-format: "enable"
        custom-log-fields:
         -
            field-id: "<your_own_value> (source log.custom-field.id)"
        daemon-log: "enable"
        expolicy-implicit-log: "enable"
        fwpolicy-implicit-log: "enable"
        fwpolicy6-implicit-log: "enable"
        local-in-allow: "enable"
        local-in-deny-broadcast: "enable"
        local-in-deny-unicast: "enable"
        local-out: "enable"
        log-invalid-packet: "enable"
        log-policy-comment: "enable"
        log-policy-name: "enable"
        log-user-in-upper: "enable"
        neighbor-event: "enable"
        resolve-ip: "enable"
        resolve-port: "enable"
        user-anonymize: "enable"
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


def filter_log_setting_data(json):
    option_list = ['brief-traffic-format', 'custom-log-fields', 'daemon-log',
                   'expolicy-implicit-log', 'fwpolicy-implicit-log', 'fwpolicy6-implicit-log',
                   'local-in-allow', 'local-in-deny-broadcast', 'local-in-deny-unicast',
                   'local-out', 'log-invalid-packet', 'log-policy-comment',
                   'log-policy-name', 'log-user-in-upper', 'neighbor-event',
                   'resolve-ip', 'resolve-port', 'user-anonymize']
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


def log_setting(data, fos):
    vdom = data['vdom']
    log_setting_data = data['log_setting']
    flattened_data = flatten_multilists_attributes(log_setting_data)
    filtered_data = filter_log_setting_data(flattened_data)
    return fos.set('log',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def fortios_log(data, fos):
    login(data)

    if data['log_setting']:
        resp = log_setting(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "log_setting": {
            "required": False, "type": "dict",
            "options": {
                "brief-traffic-format": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "custom-log-fields": {"required": False, "type": "list",
                                      "options": {
                                          "field-id": {"required": True, "type": "str"}
                                      }},
                "daemon-log": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "expolicy-implicit-log": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "fwpolicy-implicit-log": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "fwpolicy6-implicit-log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "local-in-allow": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "local-in-deny-broadcast": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "local-in-deny-unicast": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "local-out": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "log-invalid-packet": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "log-policy-comment": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "log-policy-name": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "log-user-in-upper": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "neighbor-event": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "resolve-ip": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "resolve-port": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "user-anonymize": {"required": False, "type": "str",
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

    is_error, has_changed, result = fortios_log(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
