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
module: fortios_log_setting
short_description: Configure general log settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify log feature and setting category.
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
    log_setting:
        description:
            - Configure general log settings.
        default: null
        type: dict
        suboptions:
            brief_traffic_format:
                description:
                    - Enable/disable brief format traffic logging.
                type: str
                choices:
                    - enable
                    - disable
            custom_log_fields:
                description:
                    - Custom fields to append to all log messages.
                type: list
                suboptions:
                    field_id:
                        description:
                            - Custom log field. Source log.custom-field.id.
                        type: str
            daemon_log:
                description:
                    - Enable/disable daemon logging.
                type: str
                choices:
                    - enable
                    - disable
            expolicy_implicit_log:
                description:
                    - Enable/disable explicit proxy firewall implicit policy logging.
                type: str
                choices:
                    - enable
                    - disable
            fwpolicy_implicit_log:
                description:
                    - Enable/disable implicit firewall policy logging.
                type: str
                choices:
                    - enable
                    - disable
            fwpolicy6_implicit_log:
                description:
                    - Enable/disable implicit firewall policy6 logging.
                type: str
                choices:
                    - enable
                    - disable
            local_in_allow:
                description:
                    - Enable/disable local-in-allow logging.
                type: str
                choices:
                    - enable
                    - disable
            local_in_deny_broadcast:
                description:
                    - Enable/disable local-in-deny-broadcast logging.
                type: str
                choices:
                    - enable
                    - disable
            local_in_deny_unicast:
                description:
                    - Enable/disable local-in-deny-unicast logging.
                type: str
                choices:
                    - enable
                    - disable
            local_out:
                description:
                    - Enable/disable local-out logging.
                type: str
                choices:
                    - enable
                    - disable
            log_invalid_packet:
                description:
                    - Enable/disable invalid packet traffic logging.
                type: str
                choices:
                    - enable
                    - disable
            log_policy_comment:
                description:
                    - Enable/disable inserting policy comments into traffic logs.
                type: str
                choices:
                    - enable
                    - disable
            log_policy_name:
                description:
                    - Enable/disable inserting policy name into traffic logs.
                type: str
                choices:
                    - enable
                    - disable
            log_user_in_upper:
                description:
                    - Enable/disable logs with user-in-upper.
                type: str
                choices:
                    - enable
                    - disable
            neighbor_event:
                description:
                    - Enable/disable neighbor event logging.
                type: str
                choices:
                    - enable
                    - disable
            resolve_ip:
                description:
                    - Enable/disable adding resolved domain names to traffic logs if possible.
                type: str
                choices:
                    - enable
                    - disable
            resolve_port:
                description:
                    - Enable/disable adding resolved service names to traffic logs.
                type: str
                choices:
                    - enable
                    - disable
            user_anonymize:
                description:
                    - Enable/disable anonymizing user names in log messages.
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
  - name: Configure general log settings.
    fortios_log_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      log_setting:
        brief_traffic_format: "enable"
        custom_log_fields:
         -
            field_id: "<your_own_value> (source log.custom-field.id)"
        daemon_log: "enable"
        expolicy_implicit_log: "enable"
        fwpolicy_implicit_log: "enable"
        fwpolicy6_implicit_log: "enable"
        local_in_allow: "enable"
        local_in_deny_broadcast: "enable"
        local_in_deny_unicast: "enable"
        local_out: "enable"
        log_invalid_packet: "enable"
        log_policy_comment: "enable"
        log_policy_name: "enable"
        log_user_in_upper: "enable"
        neighbor_event: "enable"
        resolve_ip: "enable"
        resolve_port: "enable"
        user_anonymize: "enable"
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


def filter_log_setting_data(json):
    option_list = ['brief_traffic_format', 'custom_log_fields', 'daemon_log',
                   'expolicy_implicit_log', 'fwpolicy_implicit_log', 'fwpolicy6_implicit_log',
                   'local_in_allow', 'local_in_deny_broadcast', 'local_in_deny_unicast',
                   'local_out', 'log_invalid_packet', 'log_policy_comment',
                   'log_policy_name', 'log_user_in_upper', 'neighbor_event',
                   'resolve_ip', 'resolve_port', 'user_anonymize']
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


def log_setting(data, fos):
    vdom = data['vdom']
    log_setting_data = data['log_setting']
    filtered_data = underscore_to_hyphen(filter_log_setting_data(log_setting_data))

    return fos.set('log',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_log(data, fos):

    if data['log_setting']:
        resp = log_setting(data, fos)

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
        "log_setting": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "brief_traffic_format": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "custom_log_fields": {"required": False, "type": "list",
                                      "options": {
                                          "field_id": {"required": False, "type": "str"}
                                      }},
                "daemon_log": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "expolicy_implicit_log": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "fwpolicy_implicit_log": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "fwpolicy6_implicit_log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "local_in_allow": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "local_in_deny_broadcast": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "local_in_deny_unicast": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "local_out": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "log_invalid_packet": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "log_policy_comment": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "log_policy_name": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "log_user_in_upper": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "neighbor_event": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "resolve_ip": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "resolve_port": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "user_anonymize": {"required": False, "type": "str",
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
