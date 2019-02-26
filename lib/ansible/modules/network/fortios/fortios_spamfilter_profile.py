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
module: fortios_spamfilter_profile
short_description: Configure AntiSpam profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify spamfilter feature and profile category.
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
    spamfilter_profile:
        description:
            - Configure AntiSpam profiles.
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
            external:
                description:
                    - Enable/disable external Email inspection.
                choices:
                    - enable
                    - disable
            flow-based:
                description:
                    - Enable/disable flow-based spam filtering.
                choices:
                    - enable
                    - disable
            gmail:
                description:
                    - Gmail.
                suboptions:
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
            imap:
                description:
                    - IMAP.
                suboptions:
                    action:
                        description:
                            - Action for spam email.
                        choices:
                            - pass
                            - tag
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    tag-msg:
                        description:
                            - Subject text or header added to spam email.
                    tag-type:
                        description:
                            - Tag subject or header for spam email.
                        choices:
                            - subject
                            - header
                            - spaminfo
            mapi:
                description:
                    - MAPI.
                suboptions:
                    action:
                        description:
                            - Action for spam email.
                        choices:
                            - pass
                            - discard
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
            msn-hotmail:
                description:
                    - MSN Hotmail.
                suboptions:
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
            name:
                description:
                    - Profile name.
                required: true
            options:
                description:
                    - Options.
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
                suboptions:
                    action:
                        description:
                            - Action for spam email.
                        choices:
                            - pass
                            - tag
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    tag-msg:
                        description:
                            - Subject text or header added to spam email.
                    tag-type:
                        description:
                            - Tag subject or header for spam email.
                        choices:
                            - subject
                            - header
                            - spaminfo
            replacemsg-group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
            smtp:
                description:
                    - SMTP.
                suboptions:
                    action:
                        description:
                            - Action for spam email.
                        choices:
                            - pass
                            - tag
                            - discard
                    hdrip:
                        description:
                            - Enable/disable SMTP email header IP checks for spamfsip, spamrbl and spambwl filters.
                        choices:
                            - disable
                            - enable
                    local-override:
                        description:
                            - Enable/disable local filter to override SMTP remote check result.
                        choices:
                            - disable
                            - enable
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    tag-msg:
                        description:
                            - Subject text or header added to spam email.
                    tag-type:
                        description:
                            - Tag subject or header for spam email.
                        choices:
                            - subject
                            - header
                            - spaminfo
            spam-bwl-table:
                description:
                    - Anti-spam black/white list table ID. Source spamfilter.bwl.id.
            spam-bword-table:
                description:
                    - Anti-spam banned word table ID. Source spamfilter.bword.id.
            spam-bword-threshold:
                description:
                    - Spam banned word threshold.
            spam-filtering:
                description:
                    - Enable/disable spam filtering.
                choices:
                    - enable
                    - disable
            spam-iptrust-table:
                description:
                    - Anti-spam IP trust table ID. Source spamfilter.iptrust.id.
            spam-log:
                description:
                    - Enable/disable spam logging for email filtering.
                choices:
                    - disable
                    - enable
            spam-log-fortiguard-response:
                description:
                    - Enable/disable logging FortiGuard spam response.
                choices:
                    - disable
                    - enable
            spam-mheader-table:
                description:
                    - Anti-spam MIME header table ID. Source spamfilter.mheader.id.
            spam-rbl-table:
                description:
                    - Anti-spam DNSBL table ID. Source spamfilter.dnsbl.id.
            yahoo-mail:
                description:
                    - Yahoo! Mail.
                suboptions:
                    log:
                        description:
                            - Enable/disable logging.
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
  tasks:
  - name: Configure AntiSpam profiles.
    fortios_spamfilter_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      spamfilter_profile:
        state: "present"
        comment: "Comment."
        external: "enable"
        flow-based: "enable"
        gmail:
            log: "enable"
        imap:
            action: "pass"
            log: "enable"
            tag-msg: "<your_own_value>"
            tag-type: "subject"
        mapi:
            action: "pass"
            log: "enable"
        msn-hotmail:
            log: "enable"
        name: "default_name_18"
        options: "bannedword"
        pop3:
            action: "pass"
            log: "enable"
            tag-msg: "<your_own_value>"
            tag-type: "subject"
        replacemsg-group: "<your_own_value> (source system.replacemsg-group.name)"
        smtp:
            action: "pass"
            hdrip: "disable"
            local-override: "disable"
            log: "enable"
            tag-msg: "<your_own_value>"
            tag-type: "subject"
        spam-bwl-table: "33 (source spamfilter.bwl.id)"
        spam-bword-table: "34 (source spamfilter.bword.id)"
        spam-bword-threshold: "35"
        spam-filtering: "enable"
        spam-iptrust-table: "37 (source spamfilter.iptrust.id)"
        spam-log: "disable"
        spam-log-fortiguard-response: "disable"
        spam-mheader-table: "40 (source spamfilter.mheader.id)"
        spam-rbl-table: "41 (source spamfilter.dnsbl.id)"
        yahoo-mail:
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


def filter_spamfilter_profile_data(json):
    option_list = ['comment', 'external', 'flow-based',
                   'gmail', 'imap', 'mapi',
                   'msn-hotmail', 'name', 'options',
                   'pop3', 'replacemsg-group', 'smtp',
                   'spam-bwl-table', 'spam-bword-table', 'spam-bword-threshold',
                   'spam-filtering', 'spam-iptrust-table', 'spam-log',
                   'spam-log-fortiguard-response', 'spam-mheader-table', 'spam-rbl-table',
                   'yahoo-mail']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = [[u'options'], [u'imap', u'tag-type'], [u'pop3', u'tag-type'], [u'smtp', u'tag-type']]

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def spamfilter_profile(data, fos):
    vdom = data['vdom']
    spamfilter_profile_data = data['spamfilter_profile']
    flattened_data = flatten_multilists_attributes(spamfilter_profile_data)
    filtered_data = filter_spamfilter_profile_data(flattened_data)
    if spamfilter_profile_data['state'] == "present":
        return fos.set('spamfilter',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif spamfilter_profile_data['state'] == "absent":
        return fos.delete('spamfilter',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_spamfilter(data, fos):
    login(data)

    if data['spamfilter_profile']:
        resp = spamfilter_profile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "spamfilter_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "external": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "flow-based": {"required": False, "type": "str",
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
                             "tag-msg": {"required": False, "type": "str"},
                             "tag-type": {"required": False, "type": "list",
                                          "choices": ["subject", "header", "spaminfo"]}
                         }},
                "mapi": {"required": False, "type": "dict",
                         "options": {
                             "action": {"required": False, "type": "str",
                                        "choices": ["pass", "discard"]},
                             "log": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]}
                         }},
                "msn-hotmail": {"required": False, "type": "dict",
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
                             "tag-msg": {"required": False, "type": "str"},
                             "tag-type": {"required": False, "type": "list",
                                          "choices": ["subject", "header", "spaminfo"]}
                         }},
                "replacemsg-group": {"required": False, "type": "str"},
                "smtp": {"required": False, "type": "dict",
                         "options": {
                             "action": {"required": False, "type": "str",
                                        "choices": ["pass", "tag", "discard"]},
                             "hdrip": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                             "local-override": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                             "log": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                             "tag-msg": {"required": False, "type": "str"},
                             "tag-type": {"required": False, "type": "list",
                                          "choices": ["subject", "header", "spaminfo"]}
                         }},
                "spam-bwl-table": {"required": False, "type": "int"},
                "spam-bword-table": {"required": False, "type": "int"},
                "spam-bword-threshold": {"required": False, "type": "int"},
                "spam-filtering": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "spam-iptrust-table": {"required": False, "type": "int"},
                "spam-log": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "spam-log-fortiguard-response": {"required": False, "type": "str",
                                                 "choices": ["disable", "enable"]},
                "spam-mheader-table": {"required": False, "type": "int"},
                "spam-rbl-table": {"required": False, "type": "int"},
                "yahoo-mail": {"required": False, "type": "dict",
                               "options": {
                                   "log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]}
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

    is_error, has_changed, result = fortios_spamfilter(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
