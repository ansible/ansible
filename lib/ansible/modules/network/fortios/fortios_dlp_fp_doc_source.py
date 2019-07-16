#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2018 Fortinet, Inc.
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
module: fortios_dlp_fp_doc_source
short_description: Create a DLP fingerprint database by allowing the FortiGate to access a file server containing files from which to create fingerprints in
   Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure dlp feature and fp_doc_source category.
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
    dlp_fp_doc_source:
        description:
            - Create a DLP fingerprint database by allowing the FortiGate to access a file server containing files from which to create fingerprints.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            date:
                description:
                    - Day of the month on which to scan the server (1 - 31).
            file-path:
                description:
                    - Path on the server to the fingerprint files (max 119 characters).
            file-pattern:
                description:
                    - Files matching this pattern on the server are fingerprinted. Optionally use the * and ? wildcards.
            keep-modified:
                description:
                    - Enable so that when a file is changed on the server the FortiGate keeps the old fingerprint and adds a new fingerprint to the database.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name of the DLP fingerprint database.
                required: true
            password:
                description:
                    - Password required to log into the file server.
            period:
                description:
                    - Frequency for which the FortiGate checks the server for new or changed files.
                choices:
                    - none
                    - daily
                    - weekly
                    - monthly
            remove-deleted:
                description:
                    - Enable to keep the fingerprint database up to date when a file is deleted from the server.
                choices:
                    - enable
                    - disable
            scan-on-creation:
                description:
                    - Enable to keep the fingerprint database up to date when a file is added or changed on the server.
                choices:
                    - enable
                    - disable
            scan-subdirectories:
                description:
                    - Enable/disable scanning subdirectories to find files to create fingerprints from.
                choices:
                    - enable
                    - disable
            sensitivity:
                description:
                    - Select a sensitivity or threat level for matches with this fingerprint database. Add sensitivities using fp-sensitivity. Source dlp
                      .fp-sensitivity.name.
            server:
                description:
                    - IPv4 or IPv6 address of the server.
            server-type:
                description:
                    - Protocol used to communicate with the file server. Currently only Samba (SMB) servers are supported.
                choices:
                    - samba
            tod-hour:
                description:
                    - Hour of the day on which to scan the server (0 - 23, default = 1).
            tod-min:
                description:
                    - Minute of the hour on which to scan the server (0 - 59).
            username:
                description:
                    - User name required to log into the file server.
            vdom:
                description:
                    - Select the VDOM that can communicate with the file server.
                choices:
                    - mgmt
                    - current
            weekday:
                description:
                    - Day of the week on which to scan the server.
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
  tasks:
  - name: Create a DLP fingerprint database by allowing the FortiGate to access a file server containing files from which to create fingerprints.
    fortios_dlp_fp_doc_source:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      dlp_fp_doc_source:
        state: "present"
        date: "3"
        file-path: "<your_own_value>"
        file-pattern: "<your_own_value>"
        keep-modified: "enable"
        name: "default_name_7"
        password: "<your_own_value>"
        period: "none"
        remove-deleted: "enable"
        scan-on-creation: "enable"
        scan-subdirectories: "enable"
        sensitivity: "<your_own_value> (source dlp.fp-sensitivity.name)"
        server: "192.168.100.40"
        server-type: "samba"
        tod-hour: "16"
        tod-min: "17"
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


def filter_dlp_fp_doc_source_data(json):
    option_list = ['date', 'file-path', 'file-pattern',
                   'keep-modified', 'name', 'password',
                   'period', 'remove-deleted', 'scan-on-creation',
                   'scan-subdirectories', 'sensitivity', 'server',
                   'server-type', 'tod-hour', 'tod-min',
                   'username', 'vdom', 'weekday']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def dlp_fp_doc_source(data, fos):
    vdom = data['vdom']
    dlp_fp_doc_source_data = data['dlp_fp_doc_source']
    filtered_data = filter_dlp_fp_doc_source_data(dlp_fp_doc_source_data)
    if dlp_fp_doc_source_data['state'] == "present":
        return fos.set('dlp',
                       'fp-doc-source',
                       data=filtered_data,
                       vdom=vdom)

    elif dlp_fp_doc_source_data['state'] == "absent":
        return fos.delete('dlp',
                          'fp-doc-source',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_dlp(data, fos):
    login(data)

    methodlist = ['dlp_fp_doc_source']
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
        "dlp_fp_doc_source": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "date": {"required": False, "type": "int"},
                "file-path": {"required": False, "type": "str"},
                "file-pattern": {"required": False, "type": "str"},
                "keep-modified": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "password": {"required": False, "type": "str"},
                "period": {"required": False, "type": "str",
                           "choices": ["none", "daily", "weekly",
                                       "monthly"]},
                "remove-deleted": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "scan-on-creation": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "scan-subdirectories": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "sensitivity": {"required": False, "type": "str"},
                "server": {"required": False, "type": "str"},
                "server-type": {"required": False, "type": "str",
                                "choices": ["samba"]},
                "tod-hour": {"required": False, "type": "int"},
                "tod-min": {"required": False, "type": "int"},
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
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_dlp(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
