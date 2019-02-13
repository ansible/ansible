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
module: fortios_dlp_sensor
short_description: Configure DLP sensors in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure dlp feature and sensor category.
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
    dlp_sensor:
        description:
            - Configure DLP sensors.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            comment:
                description:
                    - Comment.
            dlp-log:
                description:
                    - Enable/disable DLP logging.
                choices:
                    - enable
                    - disable
            extended-log:
                description:
                    - Enable/disable extended logging for data leak prevention.
                choices:
                    - enable
                    - disable
            filter:
                description:
                    - Set up DLP filters for this sensor.
                suboptions:
                    action:
                        description:
                            - Action to take with content that this DLP sensor matches.
                        choices:
                            - allow
                            - log-only
                            - block
                            - quarantine-ip
                    archive:
                        description:
                            - Enable/disable DLP archiving.
                        choices:
                            - disable
                            - enable
                    company-identifier:
                        description:
                            - Enter a company identifier watermark to match. Only watermarks that your company has placed on the files are matched.
                    expiry:
                        description:
                            - Quarantine duration in days, hours, minutes format (dddhhmm).
                    file-size:
                        description:
                            - Match files this size or larger (0 - 4294967295 kbytes).
                    file-type:
                        description:
                            - Select the number of a DLP file pattern table to match. Source dlp.filepattern.id.
                    filter-by:
                        description:
                            - Select the type of content to match.
                        choices:
                            - credit-card
                            - ssn
                            - regexp
                            - file-type
                            - file-size
                            - fingerprint
                            - watermark
                            - encrypted
                    fp-sensitivity:
                        description:
                            - Select a DLP file pattern sensitivity to match.
                        suboptions:
                            name:
                                description:
                                    - Select a DLP sensitivity. Source dlp.fp-sensitivity.name.
                                required: true
                    id:
                        description:
                            - ID.
                        required: true
                    match-percentage:
                        description:
                            - Percentage of fingerprints in the fingerprint databases designated with the selected fp-sensitivity to match.
                    name:
                        description:
                            - Filter name.
                    proto:
                        description:
                            - Check messages or files over one or more of these protocols.
                        choices:
                            - smtp
                            - pop3
                            - imap
                            - http-get
                            - http-post
                            - ftp
                            - nntp
                            - mapi
                            - mm1
                            - mm3
                            - mm4
                            - mm7
                    regexp:
                        description:
                            - Enter a regular expression to match (max. 255 characters).
                    severity:
                        description:
                            - Select the severity or threat level that matches this filter.
                        choices:
                            - info
                            - low
                            - medium
                            - high
                            - critical
                    type:
                        description:
                            - Select whether to check the content of messages (an email message) or files (downloaded files or email attachments).
                        choices:
                            - file
                            - message
            flow-based:
                description:
                    - Enable/disable flow-based DLP.
                choices:
                    - enable
                    - disable
            full-archive-proto:
                description:
                    - Protocols to always content archive.
                choices:
                    - smtp
                    - pop3
                    - imap
                    - http-get
                    - http-post
                    - ftp
                    - nntp
                    - mapi
                    - mm1
                    - mm3
                    - mm4
                    - mm7
            nac-quar-log:
                description:
                    - Enable/disable NAC quarantine logging.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name of the DLP sensor.
                required: true
            options:
                description:
                    - Configure DLP options.
            replacemsg-group:
                description:
                    - Replacement message group used by this DLP sensor. Source system.replacemsg-group.name.
            summary-proto:
                description:
                    - Protocols to always log summary.
                choices:
                    - smtp
                    - pop3
                    - imap
                    - http-get
                    - http-post
                    - ftp
                    - nntp
                    - mapi
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
  - name: Configure DLP sensors.
    fortios_dlp_sensor:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      dlp_sensor:
        state: "present"
        comment: "Comment."
        dlp-log: "enable"
        extended-log: "enable"
        filter:
         -
            action: "allow"
            archive: "disable"
            company-identifier:  "myId_9"
            expiry: "<your_own_value>"
            file-size: "11"
            file-type: "12 (source dlp.filepattern.id)"
            filter-by: "credit-card"
            fp-sensitivity:
             -
                name: "default_name_15 (source dlp.fp-sensitivity.name)"
            id:  "16"
            match-percentage: "17"
            name: "default_name_18"
            proto: "smtp"
            regexp: "<your_own_value>"
            severity: "info"
            type: "file"
        flow-based: "enable"
        full-archive-proto: "smtp"
        nac-quar-log: "enable"
        name: "default_name_26"
        options: "<your_own_value>"
        replacemsg-group: "<your_own_value> (source system.replacemsg-group.name)"
        summary-proto: "smtp"
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


def filter_dlp_sensor_data(json):
    option_list = ['comment', 'dlp-log', 'extended-log',
                   'filter', 'flow-based', 'full-archive-proto',
                   'nac-quar-log', 'name', 'options',
                   'replacemsg-group', 'summary-proto']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def dlp_sensor(data, fos):
    vdom = data['vdom']
    dlp_sensor_data = data['dlp_sensor']
    filtered_data = filter_dlp_sensor_data(dlp_sensor_data)
    if dlp_sensor_data['state'] == "present":
        return fos.set('dlp',
                       'sensor',
                       data=filtered_data,
                       vdom=vdom)

    elif dlp_sensor_data['state'] == "absent":
        return fos.delete('dlp',
                          'sensor',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_dlp(data, fos):
    login(data)

    methodlist = ['dlp_sensor']
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
        "dlp_sensor": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "dlp-log": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "extended-log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "filter": {"required": False, "type": "list",
                           "options": {
                               "action": {"required": False, "type": "str",
                                          "choices": ["allow", "log-only", "block",
                                                      "quarantine-ip"]},
                               "archive": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                               "company-identifier": {"required": False, "type": "str"},
                               "expiry": {"required": False, "type": "str"},
                               "file-size": {"required": False, "type": "int"},
                               "file-type": {"required": False, "type": "int"},
                               "filter-by": {"required": False, "type": "str",
                                             "choices": ["credit-card", "ssn", "regexp",
                                                         "file-type", "file-size", "fingerprint",
                                                         "watermark", "encrypted"]},
                               "fp-sensitivity": {"required": False, "type": "list",
                                                  "options": {
                                                      "name": {"required": True, "type": "str"}
                                                  }},
                               "id": {"required": True, "type": "int"},
                               "match-percentage": {"required": False, "type": "int"},
                               "name": {"required": False, "type": "str"},
                               "proto": {"required": False, "type": "str",
                                         "choices": ["smtp", "pop3", "imap",
                                                     "http-get", "http-post", "ftp",
                                                     "nntp", "mapi", "mm1",
                                                     "mm3", "mm4", "mm7"]},
                               "regexp": {"required": False, "type": "str"},
                               "severity": {"required": False, "type": "str",
                                            "choices": ["info", "low", "medium",
                                                        "high", "critical"]},
                               "type": {"required": False, "type": "str",
                                        "choices": ["file", "message"]}
                           }},
                "flow-based": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "full-archive-proto": {"required": False, "type": "str",
                                       "choices": ["smtp", "pop3", "imap",
                                                   "http-get", "http-post", "ftp",
                                                   "nntp", "mapi", "mm1",
                                                   "mm3", "mm4", "mm7"]},
                "nac-quar-log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str",
                            "choices": []},
                "replacemsg-group": {"required": False, "type": "str"},
                "summary-proto": {"required": False, "type": "str",
                                  "choices": ["smtp", "pop3", "imap",
                                              "http-get", "http-post", "ftp",
                                              "nntp", "mapi", "mm1",
                                              "mm3", "mm4", "mm7"]}

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
