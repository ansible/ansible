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
module: fortios_ips_rule
short_description: Configure IPS rules in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure ips feature and rule category.
      Examples includes all options and need to be adjusted to datasources before usage.
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
            - FortiOS or FortiGate ip adress.
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
    ips_rule:
        description:
            - Configure IPS rules.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            action:
                description:
                    - Action.
                choices:
                    - pass
                    - block
            application:
                description:
                    - Vulnerable applications.
            date:
                description:
                    - Date.
            group:
                description:
                    - Group.
            location:
                description:
                    - Vulnerable location.
            log:
                description:
                    - Enable/disable logging.
                choices:
                    - disable
                    - enable
            log-packet:
                description:
                    - Enable/disable packet logging.
                choices:
                    - disable
                    - enable
            metadata:
                description:
                    - Meta data.
                suboptions:
                    id:
                        description:
                            - ID.
                        required: true
                    metaid:
                        description:
                            - Meta ID.
                    valueid:
                        description:
                            - Value ID.
            name:
                description:
                    - Rule name.
                required: true
            os:
                description:
                    - Vulnerable operation systems.
            rev:
                description:
                    - Revision.
            rule-id:
                description:
                    - Rule ID.
            service:
                description:
                    - Vulnerable service.
            severity:
                description:
                    - Severity.
            status:
                description:
                    - Enable/disable status.
                choices:
                    - disable
                    - enable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPS rules.
    fortios_ips_rule:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      ips_rule:
        state: "present"
        action: "pass"
        application: "<your_own_value>"
        date: "5"
        group: "<your_own_value>"
        location: "<your_own_value>"
        log: "disable"
        log-packet: "disable"
        metadata:
         -
            id:  "11"
            metaid: "12"
            valueid: "13"
        name: "default_name_14"
        os: "<your_own_value>"
        rev: "16"
        rule-id: "17"
        service: "<your_own_value>"
        severity: "<your_own_value>"
        status: "disable"
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


def filter_ips_rule_data(json):
    option_list = ['action', 'application', 'date',
                   'group', 'location', 'log',
                   'log-packet', 'metadata', 'name',
                   'os', 'rev', 'rule-id',
                   'service', 'severity', 'status']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def ips_rule(data, fos):
    vdom = data['vdom']
    ips_rule_data = data['ips_rule']
    filtered_data = filter_ips_rule_data(ips_rule_data)
    if ips_rule_data['state'] == "present":
        return fos.set('ips',
                       'rule',
                       data=filtered_data,
                       vdom=vdom)

    elif ips_rule_data['state'] == "absent":
        return fos.delete('ips',
                          'rule',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_ips(data, fos):
    login(data)

    methodlist = ['ips_rule']
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
        "ips_rule": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "action": {"required": False, "type": "str",
                           "choices": ["pass", "block"]},
                "application": {"required": False, "type": "str"},
                "date": {"required": False, "type": "int"},
                "group": {"required": False, "type": "str"},
                "location": {"required": False, "type": "str"},
                "log": {"required": False, "type": "str",
                        "choices": ["disable", "enable"]},
                "log-packet": {"required": False, "type": "str",
                               "choices": ["disable", "enable"]},
                "metadata": {"required": False, "type": "list",
                             "options": {
                                 "id": {"required": True, "type": "int"},
                                 "metaid": {"required": False, "type": "int"},
                                 "valueid": {"required": False, "type": "int"}
                             }},
                "name": {"required": True, "type": "str"},
                "os": {"required": False, "type": "str"},
                "rev": {"required": False, "type": "int"},
                "rule-id": {"required": False, "type": "int"},
                "service": {"required": False, "type": "str"},
                "severity": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["disable", "enable"]}

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

    is_error, has_changed, result = fortios_ips(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
