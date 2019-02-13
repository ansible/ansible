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
module: fortios_antivirus_quarantine
short_description: Configure quarantine options in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure antivirus feature and quarantine category.
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
    antivirus_quarantine:
        description:
            - Configure quarantine options.
        default: null
        suboptions:
            agelimit:
                description:
                    - Age limit for quarantined files (0 - 479 hours, 0 means forever).
            destination:
                description:
                    - Choose whether to quarantine files to the FortiGate disk or to FortiAnalyzer or to delete them instead of quarantining them.
                choices:
                    - NULL
                    - disk
                    - FortiAnalyzer
            drop-blocked:
                description:
                    - Do not quarantine dropped files found in sessions using the selected protocols. Dropped files are deleted instead of being quarantined.
                choices:
                    - imap
                    - smtp
                    - pop3
                    - http
                    - ftp
                    - nntp
                    - imaps
                    - smtps
                    - pop3s
                    - ftps
                    - mapi
                    - cifs
                    - mm1
                    - mm3
                    - mm4
                    - mm7
            drop-heuristic:
                description:
                    - Do not quarantine files detected by heuristics found in sessions using the selected protocols. Dropped files are deleted instead of
                       being quarantined.
                choices:
                    - imap
                    - smtp
                    - pop3
                    - http
                    - ftp
                    - nntp
                    - imaps
                    - smtps
                    - pop3s
                    - https
                    - ftps
                    - mapi
                    - cifs
                    - mm1
                    - mm3
                    - mm4
                    - mm7
            drop-infected:
                description:
                    - Do not quarantine infected files found in sessions using the selected protocols. Dropped files are deleted instead of being quarantined.
                choices:
                    - imap
                    - smtp
                    - pop3
                    - http
                    - ftp
                    - nntp
                    - imaps
                    - smtps
                    - pop3s
                    - https
                    - ftps
                    - mapi
                    - cifs
                    - mm1
                    - mm3
                    - mm4
                    - mm7
            lowspace:
                description:
                    - Select the method for handling additional files when running low on disk space.
                choices:
                    - drop-new
                    - ovrw-old
            maxfilesize:
                description:
                    - Maximum file size to quarantine (0 - 500 Mbytes, 0 means unlimited).
            quarantine-quota:
                description:
                    - The amount of disk space to reserve for quarantining files (0 - 4294967295 Mbytes, depends on disk space).
            store-blocked:
                description:
                    - Quarantine blocked files found in sessions using the selected protocols.
                choices:
                    - imap
                    - smtp
                    - pop3
                    - http
                    - ftp
                    - nntp
                    - imaps
                    - smtps
                    - pop3s
                    - ftps
                    - mapi
                    - cifs
                    - mm1
                    - mm3
                    - mm4
                    - mm7
            store-heuristic:
                description:
                    - Quarantine files detected by heuristics found in sessions using the selected protocols.
                choices:
                    - imap
                    - smtp
                    - pop3
                    - http
                    - ftp
                    - nntp
                    - imaps
                    - smtps
                    - pop3s
                    - https
                    - ftps
                    - mapi
                    - cifs
                    - mm1
                    - mm3
                    - mm4
                    - mm7
            store-infected:
                description:
                    - Quarantine infected files found in sessions using the selected protocols.
                choices:
                    - imap
                    - smtp
                    - pop3
                    - http
                    - ftp
                    - nntp
                    - imaps
                    - smtps
                    - pop3s
                    - https
                    - ftps
                    - mapi
                    - cifs
                    - mm1
                    - mm3
                    - mm4
                    - mm7
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure quarantine options.
    fortios_antivirus_quarantine:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      antivirus_quarantine:
        agelimit: "3"
        destination: "NULL"
        drop-blocked: "imap"
        drop-heuristic: "imap"
        drop-infected: "imap"
        lowspace: "drop-new"
        maxfilesize: "9"
        quarantine-quota: "10"
        store-blocked: "imap"
        store-heuristic: "imap"
        store-infected: "imap"
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


def filter_antivirus_quarantine_data(json):
    option_list = ['agelimit', 'destination', 'drop-blocked',
                   'drop-heuristic', 'drop-infected', 'lowspace',
                   'maxfilesize', 'quarantine-quota', 'store-blocked',
                   'store-heuristic', 'store-infected']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def antivirus_quarantine(data, fos):
    vdom = data['vdom']
    antivirus_quarantine_data = data['antivirus_quarantine']
    filtered_data = filter_antivirus_quarantine_data(antivirus_quarantine_data)
    return fos.set('antivirus',
                   'quarantine',
                   data=filtered_data,
                   vdom=vdom)


def fortios_antivirus(data, fos):
    login(data)

    methodlist = ['antivirus_quarantine']
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
        "antivirus_quarantine": {
            "required": False, "type": "dict",
            "options": {
                "agelimit": {"required": False, "type": "int"},
                "destination": {"required": False, "type": "str",
                                "choices": ["NULL", "disk", "FortiAnalyzer"]},
                "drop-blocked": {"required": False, "type": "str",
                                 "choices": ["imap", "smtp", "pop3",
                                             "http", "ftp", "nntp",
                                             "imaps", "smtps", "pop3s",
                                             "ftps", "mapi", "cifs",
                                             "mm1", "mm3", "mm4",
                                             "mm7"]},
                "drop-heuristic": {"required": False, "type": "str",
                                   "choices": ["imap", "smtp", "pop3",
                                               "http", "ftp", "nntp",
                                               "imaps", "smtps", "pop3s",
                                               "https", "ftps", "mapi",
                                               "cifs", "mm1", "mm3",
                                               "mm4", "mm7"]},
                "drop-infected": {"required": False, "type": "str",
                                  "choices": ["imap", "smtp", "pop3",
                                              "http", "ftp", "nntp",
                                              "imaps", "smtps", "pop3s",
                                              "https", "ftps", "mapi",
                                              "cifs", "mm1", "mm3",
                                              "mm4", "mm7"]},
                "lowspace": {"required": False, "type": "str",
                             "choices": ["drop-new", "ovrw-old"]},
                "maxfilesize": {"required": False, "type": "int"},
                "quarantine-quota": {"required": False, "type": "int"},
                "store-blocked": {"required": False, "type": "str",
                                  "choices": ["imap", "smtp", "pop3",
                                              "http", "ftp", "nntp",
                                              "imaps", "smtps", "pop3s",
                                              "ftps", "mapi", "cifs",
                                              "mm1", "mm3", "mm4",
                                              "mm7"]},
                "store-heuristic": {"required": False, "type": "str",
                                    "choices": ["imap", "smtp", "pop3",
                                                "http", "ftp", "nntp",
                                                "imaps", "smtps", "pop3s",
                                                "https", "ftps", "mapi",
                                                "cifs", "mm1", "mm3",
                                                "mm4", "mm7"]},
                "store-infected": {"required": False, "type": "str",
                                   "choices": ["imap", "smtp", "pop3",
                                               "http", "ftp", "nntp",
                                               "imaps", "smtps", "pop3s",
                                               "https", "ftps", "mapi",
                                               "cifs", "mm1", "mm3",
                                               "mm4", "mm7"]}

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

    is_error, has_changed, result = fortios_antivirus(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
