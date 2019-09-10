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
module: fortios_spamfilter_profile
short_description: Configure AntiSpam profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify spamfilter feature and profile category.
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
    spamfilter_profile:
        description:
            - Configure AntiSpam profiles.
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
            external:
                description:
                    - Enable/disable external Email inspection.
                type: str
                choices:
                    - enable
                    - disable
            flow_based:
                description:
                    - Enable/disable flow-based spam filtering.
                type: str
                choices:
                    - enable
                    - disable
            gmail:
                description:
                    - Gmail.
                type: dict
                suboptions:
                    log:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
            imap:
                description:
                    - IMAP.
                type: dict
                suboptions:
                    action:
                        description:
                            - Action for spam email.
                        type: str
                        choices:
                            - pass
                            - tag
                    log:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    tag_msg:
                        description:
                            - Subject text or header added to spam email.
                        type: str
                    tag_type:
                        description:
                            - Tag subject or header for spam email.
                        type: list
                        choices:
                            - subject
                            - header
                            - spaminfo
            mapi:
                description:
                    - MAPI.
                type: dict
                suboptions:
                    action:
                        description:
                            - Action for spam email.
                        type: str
                        choices:
                            - pass
                            - discard
                    log:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
            msn_hotmail:
                description:
                    - MSN Hotmail.
                type: dict
                suboptions:
                    log:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
            name:
                description:
                    - Profile name.
                required: true
                type: str
            options:
                description:
                    - Options.
                type: list
                choices:
                    - bannedword
                    - spambwl
                    - spamfsip
                    - spamfssubmit
                    - spamfschksum
                    - spamfsurl
                    - spamhelodns
                    - spamraddrdns
                    - spamrbl
                    - spamhdrcheck
                    - spamfsphish
            pop3:
                description:
                    - POP3.
                type: dict
                suboptions:
                    action:
                        description:
                            - Action for spam email.
                        type: str
                        choices:
                            - pass
                            - tag
                    log:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    tag_msg:
                        description:
                            - Subject text or header added to spam email.
                        type: str
                    tag_type:
                        description:
                            - Tag subject or header for spam email.
                        type: list
                        choices:
                            - subject
                            - header
                            - spaminfo
            replacemsg_group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
                type: str
            smtp:
                description:
                    - SMTP.
                type: dict
                suboptions:
                    action:
                        description:
                            - Action for spam email.
                        type: str
                        choices:
                            - pass
                            - tag
                            - discard
                    hdrip:
                        description:
                            - Enable/disable SMTP email header IP checks for spamfsip, spamrbl and spambwl filters.
                        type: str
                        choices:
                            - disable
                            - enable
                    local_override:
                        description:
                            - Enable/disable local filter to override SMTP remote check result.
                        type: str
                        choices:
                            - disable
                            - enable
                    log:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    tag_msg:
                        description:
                            - Subject text or header added to spam email.
                        type: str
                    tag_type:
                        description:
                            - Tag subject or header for spam email.
                        type: list
                        choices:
                            - subject
                            - header
                            - spaminfo
            spam_bwl_table:
                description:
                    - Anti-spam black/white list table ID. Source spamfilter.bwl.id.
                type: int
            spam_bword_table:
                description:
                    - Anti-spam banned word table ID. Source spamfilter.bword.id.
                type: int
            spam_bword_threshold:
                description:
                    - Spam banned word threshold.
                type: int
            spam_filtering:
                description:
                    - Enable/disable spam filtering.
                type: str
                choices:
                    - enable
                    - disable
            spam_iptrust_table:
                description:
                    - Anti-spam IP trust table ID. Source spamfilter.iptrust.id.
                type: int
            spam_log:
                description:
                    - Enable/disable spam logging for email filtering.
                type: str
                choices:
                    - disable
                    - enable
            spam_log_fortiguard_response:
                description:
                    - Enable/disable logging FortiGuard spam response.
                type: str
                choices:
                    - disable
                    - enable
            spam_mheader_table:
                description:
                    - Anti-spam MIME header table ID. Source spamfilter.mheader.id.
                type: int
            spam_rbl_table:
                description:
                    - Anti-spam DNSBL table ID. Source spamfilter.dnsbl.id.
                type: int
            yahoo_mail:
                description:
                    - Yahoo! Mail.
                type: dict
                suboptions:
                    log:
                        description:
                            - Enable/disable logging.
                        type: str
                        choices:
                            - enable
                            - disable
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
  - name: Configure AntiSpam profiles.
    fortios_spamfilter_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      spamfilter_profile:
        comment: "Comment."
        external: "enable"
        flow_based: "enable"
        gmail:
            log: "enable"
        imap:
            action: "pass"
            log: "enable"
            tag_msg: "<your_own_value>"
            tag_type: "subject"
        mapi:
            action: "pass"
            log: "enable"
        msn_hotmail:
            log: "enable"
        name: "default_name_18"
        options: "bannedword"
        pop3:
            action: "pass"
            log: "enable"
            tag_msg: "<your_own_value>"
            tag_type: "subject"
        replacemsg_group: "<your_own_value> (source system.replacemsg-group.name)"
        smtp:
            action: "pass"
            hdrip: "disable"
            local_override: "disable"
            log: "enable"
            tag_msg: "<your_own_value>"
            tag_type: "subject"
        spam_bwl_table: "33 (source spamfilter.bwl.id)"
        spam_bword_table: "34 (source spamfilter.bword.id)"
        spam_bword_threshold: "35"
        spam_filtering: "enable"
        spam_iptrust_table: "37 (source spamfilter.iptrust.id)"
        spam_log: "disable"
        spam_log_fortiguard_response: "disable"
        spam_mheader_table: "40 (source spamfilter.mheader.id)"
        spam_rbl_table: "41 (source spamfilter.dnsbl.id)"
        yahoo_mail:
            log: "enable"
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


def filter_spamfilter_profile_data(json):
    option_list = ['comment', 'external', 'flow_based',
                   'gmail', 'imap', 'mapi',
                   'msn_hotmail', 'name', 'options',
                   'pop3', 'replacemsg_group', 'smtp',
                   'spam_bwl_table', 'spam_bword_table', 'spam_bword_threshold',
                   'spam_filtering', 'spam_iptrust_table', 'spam_log',
                   'spam_log_fortiguard_response', 'spam_mheader_table', 'spam_rbl_table',
                   'yahoo_mail']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = [[u'options'], [u'imap', u'tag_type'], [u'pop3', u'tag_type'], [u'smtp', u'tag_type']]

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


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


def spamfilter_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['spamfilter_profile'] and data['spamfilter_profile']:
        state = data['spamfilter_profile']['state']
    else:
        state = True
    spamfilter_profile_data = data['spamfilter_profile']
    spamfilter_profile_data = flatten_multilists_attributes(spamfilter_profile_data)
    filtered_data = underscore_to_hyphen(filter_spamfilter_profile_data(spamfilter_profile_data))

    if state == "present":
        return fos.set('spamfilter',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('spamfilter',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_spamfilter(data, fos):

    if data['spamfilter_profile']:
        resp = spamfilter_profile(data, fos)

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
        "spamfilter_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "external": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "flow_based": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "gmail": {"required": False, "type": "dict",
                          "options": {
                              "log": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]}
                          }},
                "imap": {"required": False, "type": "dict",
                         "options": {
                             "action": {"required": False, "type": "str",
                                        "choices": ["pass", "tag"]},
                             "log": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                             "tag_msg": {"required": False, "type": "str"},
                             "tag_type": {"required": False, "type": "list",
                                          "choices": ["subject", "header", "spaminfo"]}
                         }},
                "mapi": {"required": False, "type": "dict",
                         "options": {
                             "action": {"required": False, "type": "str",
                                        "choices": ["pass", "discard"]},
                             "log": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]}
                         }},
                "msn_hotmail": {"required": False, "type": "dict",
                                "options": {
                                    "log": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]}
                                }},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "list",
                            "choices": ["bannedword", "spambwl", "spamfsip",
                                        "spamfssubmit", "spamfschksum", "spamfsurl",
                                        "spamhelodns", "spamraddrdns", "spamrbl",
                                        "spamhdrcheck", "spamfsphish"]},
                "pop3": {"required": False, "type": "dict",
                         "options": {
                             "action": {"required": False, "type": "str",
                                        "choices": ["pass", "tag"]},
                             "log": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                             "tag_msg": {"required": False, "type": "str"},
                             "tag_type": {"required": False, "type": "list",
                                          "choices": ["subject", "header", "spaminfo"]}
                         }},
                "replacemsg_group": {"required": False, "type": "str"},
                "smtp": {"required": False, "type": "dict",
                         "options": {
                             "action": {"required": False, "type": "str",
                                        "choices": ["pass", "tag", "discard"]},
                             "hdrip": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                             "local_override": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                             "log": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                             "tag_msg": {"required": False, "type": "str"},
                             "tag_type": {"required": False, "type": "list",
                                          "choices": ["subject", "header", "spaminfo"]}
                         }},
                "spam_bwl_table": {"required": False, "type": "int"},
                "spam_bword_table": {"required": False, "type": "int"},
                "spam_bword_threshold": {"required": False, "type": "int"},
                "spam_filtering": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "spam_iptrust_table": {"required": False, "type": "int"},
                "spam_log": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "spam_log_fortiguard_response": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                "spam_mheader_table": {"required": False, "type": "int"},
                "spam_rbl_table": {"required": False, "type": "int"},
                "yahoo_mail": {"required": False, "type": "dict",
                               "options": {
                                   "log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]}
                               }}

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

            is_error, has_changed, result = fortios_spamfilter(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_spamfilter(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
