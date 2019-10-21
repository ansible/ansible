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
module: fortios_ssh_filter_profile
short_description: SSH filter profile in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify ssh_filter feature and profile category.
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
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    ssh_filter_profile:
        description:
            - SSH filter profile.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            block:
                description:
                    - SSH blocking options.
                type: str
                choices:
                    - x11
                    - shell
                    - exec
                    - port-forward
                    - tun-forward
                    - sftp
                    - unknown
            default_command_log:
                description:
                    - Enable/disable logging unmatched shell commands.
                type: str
                choices:
                    - enable
                    - disable
            log:
                description:
                    - SSH logging options.
                type: str
                choices:
                    - x11
                    - shell
                    - exec
                    - port-forward
                    - tun-forward
                    - sftp
                    - unknown
            name:
                description:
                    - SSH filter profile name.
                required: true
                type: str
            shell_commands:
                description:
                    - SSH command filter.
                type: list
                suboptions:
                    action:
                        description:
                            - Action to take for URL filter matches.
                        type: str
                        choices:
                            - block
                            - allow
                    alert:
                        description:
                            - Enable/disable alert.
                        type: str
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - Id.
                        required: true
                        type: int
                    log:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    pattern:
                        description:
                            - SSH shell command pattern.
                        type: str
                    severity:
                        description:
                            - Log severity.
                        type: str
                        choices:
                            - low
                            - medium
                            - high
                            - critical
                    type:
                        description:
                            - Matching type.
                        type: str
                        choices:
                            - simple
                            - regex
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
  - name: SSH filter profile.
    fortios_ssh_filter_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      ssh_filter_profile:
        block: "x11"
        default_command_log: "enable"
        log: "x11"
        name: "default_name_6"
        shell_commands:
         -
            action: "block"
            alert: "enable"
            id:  "10"
            log: "enable"
            pattern: "<your_own_value>"
            severity: "low"
            type: "simple"
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


def filter_ssh_filter_profile_data(json):
    option_list = ['block', 'default_command_log', 'log',
                   'name', 'shell_commands']
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


def ssh_filter_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['ssh_filter_profile'] and data['ssh_filter_profile']:
        state = data['ssh_filter_profile']['state']
    else:
        state = True
    ssh_filter_profile_data = data['ssh_filter_profile']
    filtered_data = underscore_to_hyphen(filter_ssh_filter_profile_data(ssh_filter_profile_data))

    if state == "present":
        return fos.set('ssh-filter',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('ssh-filter',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_ssh_filter(data, fos):

    if data['ssh_filter_profile']:
        resp = ssh_filter_profile(data, fos)

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
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "ssh_filter_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "block": {"required": False, "type": "str",
                          "choices": ["x11", "shell", "exec",
                                      "port-forward", "tun-forward", "sftp",
                                      "unknown"]},
                "default_command_log": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "log": {"required": False, "type": "str",
                        "choices": ["x11", "shell", "exec",
                                    "port-forward", "tun-forward", "sftp",
                                    "unknown"]},
                "name": {"required": True, "type": "str"},
                "shell_commands": {"required": False, "type": "list",
                                   "options": {
                                       "action": {"required": False, "type": "str",
                                                  "choices": ["block", "allow"]},
                                       "alert": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                       "id": {"required": True, "type": "int"},
                                       "log": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                       "pattern": {"required": False, "type": "str"},
                                       "severity": {"required": False, "type": "str",
                                                    "choices": ["low", "medium", "high",
                                                                "critical"]},
                                       "type": {"required": False, "type": "str",
                                                "choices": ["simple", "regex"]}
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

            is_error, has_changed, result = fortios_ssh_filter(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_ssh_filter(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
