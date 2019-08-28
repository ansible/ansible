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
module: fortios_dlp_sensor
short_description: Configure DLP sensors in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify dlp feature and sensor category.
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
    dlp_sensor:
        description:
            - Configure DLP sensors.
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
            comment:
                description:
                    - Comment.
                type: str
            dlp_log:
                description:
                    - Enable/disable DLP logging.
                type: str
                choices:
                    - enable
                    - disable
            extended_log:
                description:
                    - Enable/disable extended logging for data leak prevention.
                type: str
                choices:
                    - enable
                    - disable
            filter:
                description:
                    - Set up DLP filters for this sensor.
                type: list
                suboptions:
                    action:
                        description:
                            - Action to take with content that this DLP sensor matches.
                        type: str
                        choices:
                            - allow
                            - log-only
                            - block
                            - quarantine-ip
                    archive:
                        description:
                            - Enable/disable DLP archiving.
                        type: str
                        choices:
                            - disable
                            - enable
                    company_identifier:
                        description:
                            - Enter a company identifier watermark to match. Only watermarks that your company has placed on the files are matched.
                        type: str
                    expiry:
                        description:
                            - Quarantine duration in days, hours, minutes format (dddhhmm).
                        type: str
                    file_size:
                        description:
                            - Match files this size or larger (0 - 4294967295 kbytes).
                        type: int
                    file_type:
                        description:
                            - Select the number of a DLP file pattern table to match. Source dlp.filepattern.id.
                        type: int
                    filter_by:
                        description:
                            - Select the type of content to match.
                        type: str
                        choices:
                            - credit-card
                            - ssn
                            - regexp
                            - file-type
                            - file-size
                            - fingerprint
                            - watermark
                            - encrypted
                    fp_sensitivity:
                        description:
                            - Select a DLP file pattern sensitivity to match.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Select a DLP sensitivity. Source dlp.fp-sensitivity.name.
                                required: true
                                type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    match_percentage:
                        description:
                            - Percentage of fingerprints in the fingerprint databases designated with the selected fp-sensitivity to match.
                        type: int
                    name:
                        description:
                            - Filter name.
                        type: str
                    proto:
                        description:
                            - Check messages or files over one or more of these protocols.
                        type: str
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
                        type: str
                    severity:
                        description:
                            - Select the severity or threat level that matches this filter.
                        type: str
                        choices:
                            - info
                            - low
                            - medium
                            - high
                            - critical
                    type:
                        description:
                            - Select whether to check the content of messages (an email message) or files (downloaded files or email attachments).
                        type: str
                        choices:
                            - file
                            - message
            flow_based:
                description:
                    - Enable/disable flow-based DLP.
                type: str
                choices:
                    - enable
                    - disable
            full_archive_proto:
                description:
                    - Protocols to always content archive.
                type: str
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
            nac_quar_log:
                description:
                    - Enable/disable NAC quarantine logging.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Name of the DLP sensor.
                required: true
                type: str
            options:
                description:
                    - Configure DLP options.
                type: str
            replacemsg_group:
                description:
                    - Replacement message group used by this DLP sensor. Source system.replacemsg-group.name.
                type: str
            summary_proto:
                description:
                    - Protocols to always log summary.
                type: str
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
   ssl_verify: "False"
  tasks:
  - name: Configure DLP sensors.
    fortios_dlp_sensor:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      dlp_sensor:
        comment: "Comment."
        dlp_log: "enable"
        extended_log: "enable"
        filter:
         -
            action: "allow"
            archive: "disable"
            company_identifier:  "myId_9"
            expiry: "<your_own_value>"
            file_size: "11"
            file_type: "12 (source dlp.filepattern.id)"
            filter_by: "credit-card"
            fp_sensitivity:
             -
                name: "default_name_15 (source dlp.fp-sensitivity.name)"
            id:  "16"
            match_percentage: "17"
            name: "default_name_18"
            proto: "smtp"
            regexp: "<your_own_value>"
            severity: "info"
            type: "file"
        flow_based: "enable"
        full_archive_proto: "smtp"
        nac_quar_log: "enable"
        name: "default_name_26"
        options: "<your_own_value>"
        replacemsg_group: "<your_own_value> (source system.replacemsg-group.name)"
        summary_proto: "smtp"
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


def filter_dlp_sensor_data(json):
    option_list = ['comment', 'dlp_log', 'extended_log',
                   'filter', 'flow_based', 'full_archive_proto',
                   'nac_quar_log', 'name', 'options',
                   'replacemsg_group', 'summary_proto']
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


def dlp_sensor(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['dlp_sensor'] and data['dlp_sensor']:
        state = data['dlp_sensor']['state']
    else:
        state = True
    dlp_sensor_data = data['dlp_sensor']
    filtered_data = underscore_to_hyphen(filter_dlp_sensor_data(dlp_sensor_data))

    if state == "present":
        return fos.set('dlp',
                       'sensor',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('dlp',
                          'sensor',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_dlp(data, fos):

    if data['dlp_sensor']:
        resp = dlp_sensor(data, fos)

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
        "dlp_sensor": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "dlp_log": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "extended_log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "filter": {"required": False, "type": "list",
                           "options": {
                               "action": {"required": False, "type": "str",
                                          "choices": ["allow", "log-only", "block",
                                                      "quarantine-ip"]},
                               "archive": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                               "company_identifier": {"required": False, "type": "str"},
                               "expiry": {"required": False, "type": "str"},
                               "file_size": {"required": False, "type": "int"},
                               "file_type": {"required": False, "type": "int"},
                               "filter_by": {"required": False, "type": "str",
                                             "choices": ["credit-card", "ssn", "regexp",
                                                         "file-type", "file-size", "fingerprint",
                                                         "watermark", "encrypted"]},
                               "fp_sensitivity": {"required": False, "type": "list",
                                                  "options": {
                                                      "name": {"required": True, "type": "str"}
                                                  }},
                               "id": {"required": True, "type": "int"},
                               "match_percentage": {"required": False, "type": "int"},
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
                "flow_based": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "full_archive_proto": {"required": False, "type": "str",
                                       "choices": ["smtp", "pop3", "imap",
                                                   "http-get", "http-post", "ftp",
                                                   "nntp", "mapi", "mm1",
                                                   "mm3", "mm4", "mm7"]},
                "nac_quar_log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str"},
                "replacemsg_group": {"required": False, "type": "str"},
                "summary_proto": {"required": False, "type": "str",
                                  "choices": ["smtp", "pop3", "imap",
                                              "http-get", "http-post", "ftp",
                                              "nntp", "mapi", "mm1",
                                              "mm3", "mm4", "mm7"]}

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
