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
module: fortios_endpoint_control_forticlient_ems
short_description: Configure FortiClient Enterprise Management Server (EMS) entries in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure endpoint_control feature and forticlient_ems category.
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
        default: false
    endpoint_control_forticlient_ems:
        description:
            - Configure FortiClient Enterprise Management Server (EMS) entries.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            address:
                description:
                    - Firewall address name. Source firewall.address.name.
            admin-password:
                description:
                    - FortiClient EMS admin password.
            admin-type:
                description:
                    - FortiClient EMS admin type.
                choices:
                    - Windows
                    - LDAP
            admin-username:
                description:
                    - FortiClient EMS admin username.
            https-port:
                description:
                    - "FortiClient EMS HTTPS access port number. (1 - 65535, default: 443)."
            listen-port:
                description:
                    - "FortiClient EMS telemetry listen port number. (1 - 65535, default: 8013)."
            name:
                description:
                    - FortiClient Enterprise Management Server (EMS) name.
                required: true
            rest-api-auth:
                description:
                    - FortiClient EMS REST API authentication.
                choices:
                    - disable
                    - userpass
            serial-number:
                description:
                    - FortiClient EMS Serial Number.
            upload-port:
                description:
                    - "FortiClient EMS telemetry upload port number. (1 - 65535, default: 8014)."
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure FortiClient Enterprise Management Server (EMS) entries.
    fortios_endpoint_control_forticlient_ems:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      endpoint_control_forticlient_ems:
        state: "present"
        address: "<your_own_value> (source firewall.address.name)"
        admin-password: "<your_own_value>"
        admin-type: "Windows"
        admin-username: "<your_own_value>"
        https-port: "7"
        listen-port: "8"
        name: "default_name_9"
        rest-api-auth: "disable"
        serial-number: "<your_own_value>"
        upload-port: "12"
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


def filter_endpoint_control_forticlient_ems_data(json):
    option_list = ['address', 'admin-password', 'admin-type',
                   'admin-username', 'https-port', 'listen-port',
                   'name', 'rest-api-auth', 'serial-number',
                   'upload-port']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def endpoint_control_forticlient_ems(data, fos):
    vdom = data['vdom']
    endpoint_control_forticlient_ems_data = data['endpoint_control_forticlient_ems']
    filtered_data = filter_endpoint_control_forticlient_ems_data(endpoint_control_forticlient_ems_data)
    if endpoint_control_forticlient_ems_data['state'] == "present":
        return fos.set('endpoint-control',
                       'forticlient-ems',
                       data=filtered_data,
                       vdom=vdom)

    elif endpoint_control_forticlient_ems_data['state'] == "absent":
        return fos.delete('endpoint-control',
                          'forticlient-ems',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_endpoint_control(data, fos):
    login(data)

    methodlist = ['endpoint_control_forticlient_ems']
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
        "https": {"required": False, "type": "bool", "default": "False"},
        "endpoint_control_forticlient_ems": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "address": {"required": False, "type": "str"},
                "admin-password": {"required": False, "type": "str"},
                "admin-type": {"required": False, "type": "str",
                               "choices": ["Windows", "LDAP"]},
                "admin-username": {"required": False, "type": "str"},
                "https-port": {"required": False, "type": "int"},
                "listen-port": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "rest-api-auth": {"required": False, "type": "str",
                                  "choices": ["disable", "userpass"]},
                "serial-number": {"required": False, "type": "str"},
                "upload-port": {"required": False, "type": "int"}

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

    is_error, has_changed, result = fortios_endpoint_control(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
