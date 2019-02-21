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
module: fortios_system_api_user
short_description: Configure API users in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify system feature and api_user category.
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
    system_api_user:
        description:
            - Configure API users.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            accprofile:
                description:
                    - Admin user access profile. Source system.accprofile.name.
            api-key:
                description:
                    - Admin user password.
            comments:
                description:
                    - Comment.
            cors-allow-origin:
                description:
                    - Value for Access-Control-Allow-Origin on API responses. Avoid using '*' if possible.
            name:
                description:
                    - User name.
                required: true
            peer-auth:
                description:
                    - Enable/disable peer authentication.
                choices:
                    - enable
                    - disable
            peer-group:
                description:
                    - Peer group name.
            schedule:
                description:
                    - Schedule name.
            trusthost:
                description:
                    - Trusthost.
                suboptions:
                    id:
                        description:
                            - Table ID.
                        required: true
                    ipv4-trusthost:
                        description:
                            - IPv4 trusted host address.
                    ipv6-trusthost:
                        description:
                            - IPv6 trusted host address.
                    type:
                        description:
                            - Trusthost type.
                        choices:
                            - ipv4-trusthost
                            - ipv6-trusthost
            vdom:
                description:
                    - Virtual domains.
                suboptions:
                    name:
                        description:
                            - Virtual domain name. Source system.vdom.name.
                        required: true
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure API users.
    fortios_system_api_user:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_api_user:
        state: "present"
        accprofile: "<your_own_value> (source system.accprofile.name)"
        api-key: "<your_own_value>"
        comments: "<your_own_value>"
        cors-allow-origin: "<your_own_value>"
        name: "default_name_7"
        peer-auth: "enable"
        peer-group: "<your_own_value>"
        schedule: "<your_own_value>"
        trusthost:
         -
            id:  "12"
            ipv4-trusthost: "<your_own_value>"
            ipv6-trusthost: "<your_own_value>"
            type: "ipv4-trusthost"
        vdom:
         -
            name: "default_name_17 (source system.vdom.name)"
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


def filter_system_api_user_data(json):
    option_list = ['accprofile', 'api-key', 'comments',
                   'cors-allow-origin', 'name', 'peer-auth',
                   'peer-group', 'schedule', 'trusthost',
                   'vdom']
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


def system_api_user(data, fos):
    vdom = data['vdom']
    system_api_user_data = data['system_api_user']
    flattened_data = flatten_multilists_attributes(system_api_user_data)
    filtered_data = filter_system_api_user_data(flattened_data)
    if system_api_user_data['state'] == "present":
        return fos.set('system',
                       'api-user',
                       data=filtered_data,
                       vdom=vdom)

    elif system_api_user_data['state'] == "absent":
        return fos.delete('system',
                          'api-user',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_system(data, fos):
    login(data)

    if data['system_api_user']:
        resp = system_api_user(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "system_api_user": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "accprofile": {"required": False, "type": "str"},
                "api-key": {"required": False, "type": "str"},
                "comments": {"required": False, "type": "str"},
                "cors-allow-origin": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "peer-auth": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "peer-group": {"required": False, "type": "str"},
                "schedule": {"required": False, "type": "str"},
                "trusthost": {"required": False, "type": "list",
                              "options": {
                                  "id": {"required": True, "type": "int"},
                                  "ipv4-trusthost": {"required": False, "type": "str"},
                                  "ipv6-trusthost": {"required": False, "type": "str"},
                                  "type": {"required": False, "type": "str",
                                           "choices": ["ipv4-trusthost", "ipv6-trusthost"]}
                              }},
                "vdom": {"required": False, "type": "list",
                         "options": {
                             "name": {"required": True, "type": "str"}
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

    is_error, has_changed, result = fortios_system(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
