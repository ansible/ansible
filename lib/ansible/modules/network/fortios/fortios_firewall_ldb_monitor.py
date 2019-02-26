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
module: fortios_firewall_ldb_monitor
short_description: Configure server load balancing health monitors in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and ldb_monitor category.
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
    firewall_ldb_monitor:
        description:
            - Configure server load balancing health monitors.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            http-get:
                description:
                    - URL used to send a GET request to check the health of an HTTP server.
            http-match:
                description:
                    - String to match the value expected in response to an HTTP-GET request.
            http-max-redirects:
                description:
                    - The maximum number of HTTP redirects to be allowed (0 - 5, default = 0).
            interval:
                description:
                    - Time between health checks (5 - 65635 sec, default = 10).
            name:
                description:
                    - Monitor name.
                required: true
            port:
                description:
                    - Service port used to perform the health check. If 0, health check monitor inherits port configured for the server (0 - 65635, default =
                       0).
            retry:
                description:
                    - Number health check attempts before the server is considered down (1 - 255, default = 3).
            timeout:
                description:
                    - Time to wait to receive response to a health check from a server. Reaching the timeout means the health check failed (1 - 255 sec,
                       default = 2).
            type:
                description:
                    - Select the Monitor type used by the health check monitor to check the health of the server (PING | TCP | HTTP).
                choices:
                    - ping
                    - tcp
                    - http
                    - passive-sip
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure server load balancing health monitors.
    fortios_firewall_ldb_monitor:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_ldb_monitor:
        state: "present"
        http-get: "<your_own_value>"
        http-match: "<your_own_value>"
        http-max-redirects: "5"
        interval: "6"
        name: "default_name_7"
        port: "8"
        retry: "9"
        timeout: "10"
        type: "ping"
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


def filter_firewall_ldb_monitor_data(json):
    option_list = ['http-get', 'http-match', 'http-max-redirects',
                   'interval', 'name', 'port',
                   'retry', 'timeout', 'type']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_ldb_monitor(data, fos):
    vdom = data['vdom']
    firewall_ldb_monitor_data = data['firewall_ldb_monitor']
    filtered_data = filter_firewall_ldb_monitor_data(firewall_ldb_monitor_data)
    if firewall_ldb_monitor_data['state'] == "present":
        return fos.set('firewall',
                       'ldb-monitor',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_ldb_monitor_data['state'] == "absent":
        return fos.delete('firewall',
                          'ldb-monitor',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_ldb_monitor']
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
        "firewall_ldb_monitor": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "http-get": {"required": False, "type": "str"},
                "http-match": {"required": False, "type": "str"},
                "http-max-redirects": {"required": False, "type": "int"},
                "interval": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "port": {"required": False, "type": "int"},
                "retry": {"required": False, "type": "int"},
                "timeout": {"required": False, "type": "int"},
                "type": {"required": False, "type": "str",
                         "choices": ["ping", "tcp", "http",
                                     "passive-sip"]}

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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
