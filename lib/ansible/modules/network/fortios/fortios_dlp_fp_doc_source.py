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
module: fortios_dlp_fp_doc_source
short_description: Create a DLP fingerprint database by allowing the FortiGate to access a file server containing files from which to create fingerprints in
   Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify dlp feature and fp_doc_source category.
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
    dlp_fp_doc_source:
        description:
            - Create a DLP fingerprint database by allowing the FortiGate to access a file server containing files from which to create fingerprints.
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
            date:
                description:
                    - Day of the month on which to scan the server (1 - 31).
                type: int
            file_path:
                description:
                    - Path on the server to the fingerprint files (max 119 characters).
                type: str
            file_pattern:
                description:
                    - Files matching this pattern on the server are fingerprinted. Optionally use the * and ? wildcards.
                type: str
            keep_modified:
                description:
                    - Enable so that when a file is changed on the server the FortiGate keeps the old fingerprint and adds a new fingerprint to the database.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name of the DLP fingerprint database.
                required: true
                type: str
            password:
                description:
                    - Password required to log into the file server.
                type: str
            period:
                description:
                    - Frequency for which the FortiGate checks the server for new or changed files.
                type: str
                choices:
                    - none
                    - daily
                    - weekly
                    - monthly
            remove_deleted:
                description:
                    - Enable to keep the fingerprint database up to date when a file is deleted from the server.
                type: str
                choices:
                    - enable
                    - disable
            scan_on_creation:
                description:
                    - Enable to keep the fingerprint database up to date when a file is added or changed on the server.
                type: str
                choices:
                    - enable
                    - disable
            scan_subdirectories:
                description:
                    - Enable/disable scanning subdirectories to find files to create fingerprints from.
                type: str
                choices:
                    - enable
                    - disable
            sensitivity:
                description:
                    - Select a sensitivity or threat level for matches with this fingerprint database. Add sensitivities using fp-sensitivity. Source dlp
                      .fp-sensitivity.name.
                type: str
            server:
                description:
                    - IPv4 or IPv6 address of the server.
                type: str
            server_type:
                description:
                    - Protocol used to communicate with the file server. Currently only Samba (SMB) servers are supported.
                type: str
                choices:
                    - samba
            tod_hour:
                description:
                    - Hour of the day on which to scan the server (0 - 23).
                type: int
            tod_min:
                description:
                    - Minute of the hour on which to scan the server (0 - 59).
                type: int
            username:
                description:
                    - User name required to log into the file server.
                type: str
            vdom:
                description:
                    - Select the VDOM that can communicate with the file server.
                type: str
                choices:
                    - mgmt
                    - current
            weekday:
                description:
                    - Day of the week on which to scan the server.
                type: str
                choices:
                    - sunday
                    - monday
                    - tuesday
                    - wednesday
                    - thursday
                    - friday
                    - saturday
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
  - name: Create a DLP fingerprint database by allowing the FortiGate to access a file server containing files from which to create fingerprints.
    fortios_dlp_fp_doc_source:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      dlp_fp_doc_source:
        date: "3"
        file_path: "<your_own_value>"
        file_pattern: "<your_own_value>"
        keep_modified: "enable"
        name: "default_name_7"
        password: "<your_own_value>"
        period: "none"
        remove_deleted: "enable"
        scan_on_creation: "enable"
        scan_subdirectories: "enable"
        sensitivity: "<your_own_value> (source dlp.fp-sensitivity.name)"
        server: "192.168.100.40"
        server_type: "samba"
        tod_hour: "16"
        tod_min: "17"
        username: "<your_own_value>"
        vdom: "mgmt"
        weekday: "sunday"
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


def filter_dlp_fp_doc_source_data(json):
    option_list = ['date', 'file_path', 'file_pattern',
                   'keep_modified', 'name', 'password',
                   'period', 'remove_deleted', 'scan_on_creation',
                   'scan_subdirectories', 'sensitivity', 'server',
                   'server_type', 'tod_hour', 'tod_min',
                   'username', 'vdom', 'weekday']
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


def dlp_fp_doc_source(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['dlp_fp_doc_source'] and data['dlp_fp_doc_source']:
        state = data['dlp_fp_doc_source']['state']
    else:
        state = True
    dlp_fp_doc_source_data = data['dlp_fp_doc_source']
    filtered_data = underscore_to_hyphen(filter_dlp_fp_doc_source_data(dlp_fp_doc_source_data))

    if state == "present":
        return fos.set('dlp',
                       'fp-doc-source',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('dlp',
                          'fp-doc-source',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_dlp(data, fos):

    if data['dlp_fp_doc_source']:
        resp = dlp_fp_doc_source(data, fos)

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
        "dlp_fp_doc_source": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "date": {"required": False, "type": "int"},
                "file_path": {"required": False, "type": "str"},
                "file_pattern": {"required": False, "type": "str"},
                "keep_modified": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "password": {"required": False, "type": "str", "no_log": True},
                "period": {"required": False, "type": "str",
                           "choices": ["none", "daily", "weekly",
                                       "monthly"]},
                "remove_deleted": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "scan_on_creation": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "scan_subdirectories": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "sensitivity": {"required": False, "type": "str"},
                "server": {"required": False, "type": "str"},
                "server_type": {"required": False, "type": "str",
                                "choices": ["samba"]},
                "tod_hour": {"required": False, "type": "int"},
                "tod_min": {"required": False, "type": "int"},
                "username": {"required": False, "type": "str"},
                "vdom": {"required": False, "type": "str",
                         "choices": ["mgmt", "current"]},
                "weekday": {"required": False, "type": "str",
                            "choices": ["sunday", "monday", "tuesday",
                                        "wednesday", "thursday", "friday",
                                        "saturday"]}

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

            is_error, has_changed, result = fortios_dlp(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_dlp(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
