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
module: fortios_ssh_filter_profile
short_description: SSH filter profile in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify ssh_filter feature and profile category.
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
    ssh_filter_profile:
        description:
            - SSH filter profile.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            block:
                description:
                    - SSH blocking options.
                choices:
                    - x11
                    - shell
                    - exec
                    - port-forward
                    - tun-forward
                    - sftp
                    - unknown
            default-command-log:
                description:
                    - Enable/disable logging unmatched shell commands.
                choices:
                    - enable
                    - disable
            log:
                description:
                    - SSH logging options.
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
            shell-commands:
                description:
                    - SSH command filter.
                suboptions:
                    action:
                        description:
                            - Action to take for URL filter matches.
                        choices:
                            - block
                            - allow
                    alert:
                        description:
                            - Enable/disable alert.
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - Id.
                        required: true
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    pattern:
                        description:
                            - SSH shell command pattern.
                    severity:
                        description:
                            - Log severity.
                        choices:
                            - low
                            - medium
                            - high
                            - critical
                    type:
                        description:
                            - Matching type.
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
  tasks:
  - name: SSH filter profile.
    fortios_ssh_filter_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      ssh_filter_profile:
        state: "present"
        block: "x11"
        default-command-log: "enable"
        log: "x11"
        name: "default_name_6"
        shell-commands:
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


def filter_ssh_filter_profile_data(json):
    option_list = ['block', 'default-command-log', 'log',
                   'name', 'shell-commands']
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


def ssh_filter_profile(data, fos):
    vdom = data['vdom']
    ssh_filter_profile_data = data['ssh_filter_profile']
    flattened_data = flatten_multilists_attributes(ssh_filter_profile_data)
    filtered_data = filter_ssh_filter_profile_data(flattened_data)
    if ssh_filter_profile_data['state'] == "present":
        return fos.set('ssh-filter',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif ssh_filter_profile_data['state'] == "absent":
        return fos.delete('ssh-filter',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_ssh_filter(data, fos):
    login(data)

    if data['ssh_filter_profile']:
        resp = ssh_filter_profile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssh_filter_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "block": {"required": False, "type": "str",
                          "choices": ["x11", "shell", "exec",
                                      "port-forward", "tun-forward", "sftp",
                                      "unknown"]},
                "default-command-log": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "log": {"required": False, "type": "str",
                        "choices": ["x11", "shell", "exec",
                                    "port-forward", "tun-forward", "sftp",
                                    "unknown"]},
                "name": {"required": True, "type": "str"},
                "shell-commands": {"required": False, "type": "list",
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
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_ssh_filter(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
