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
module: fortios_application_list
short_description: Configure application control lists.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure application feature and list category.
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
    application_list:
        description:
            - Configure application control lists.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            app-replacemsg:
                description:
                    - Enable/disable replacement messages for blocked applications.
                choices:
                    - disable
                    - enable
            comment:
                description:
                    - comments
            deep-app-inspection:
                description:
                    - Enable/disable deep application inspection.
                choices:
                    - disable
                    - enable
            entries:
                description:
                    - Application list entries.
                suboptions:
                    action:
                        description:
                            - Pass or block traffic, or reset connection for traffic from this application.
                        choices:
                            - pass
                            - block
                            - reset
                    application:
                        description:
                            - ID of allowed applications.
                        suboptions:
                            id:
                                description:
                                    - Application IDs.
                                required: true
                    behavior:
                        description:
                            - Application behavior filter.
                    category:
                        description:
                            - Category ID list.
                        suboptions:
                            id:
                                description:
                                    - Application category ID.
                                required: true
                    id:
                        description:
                            - Entry ID.
                        required: true
                    log:
                        description:
                            - Enable/disable logging for this application list.
                        choices:
                            - disable
                            - enable
                    log-packet:
                        description:
                            - Enable/disable packet logging.
                        choices:
                            - disable
                            - enable
                    parameters:
                        description:
                            - Application parameters.
                        suboptions:
                            id:
                                description:
                                    - Parameter ID.
                                required: true
                            value:
                                description:
                                    - Parameter value.
                    per-ip-shaper:
                        description:
                            - Per-IP traffic shaper. Source firewall.shaper.per-ip-shaper.name.
                    popularity:
                        description:
                            - Application popularity filter (1 - 5, from least to most popular).
                        choices:
                            - 1
                            - 2
                            - 3
                            - 4
                            - 5
                    protocols:
                        description:
                            - Application protocol filter.
                    quarantine:
                        description:
                            - Quarantine method.
                        choices:
                            - none
                            - attacker
                    quarantine-expiry:
                        description:
                            - Duration of quarantine. (Format ###d##h##m, minimum 1m, maximum 364d23h59m, default = 5m). Requires quarantine set to attacker.
                    quarantine-log:
                        description:
                            - Enable/disable quarantine logging.
                        choices:
                            - disable
                            - enable
                    rate-count:
                        description:
                            - Count of the rate.
                    rate-duration:
                        description:
                            - Duration (sec) of the rate.
                    rate-mode:
                        description:
                            - Rate limit mode.
                        choices:
                            - periodical
                            - continuous
                    rate-track:
                        description:
                            - Track the packet protocol field.
                        choices:
                            - none
                            - src-ip
                            - dest-ip
                            - dhcp-client-mac
                            - dns-domain
                    risk:
                        description:
                            - Risk, or impact, of allowing traffic from this application to occur (1 - 5; Low, Elevated, Medium, High, and Critical).
                        suboptions:
                            level:
                                description:
                                    - Risk, or impact, of allowing traffic from this application to occur (1 - 5; Low, Elevated, Medium, High, and Critical).
                                required: true
                    session-ttl:
                        description:
                            - Session TTL (0 = default).
                    shaper:
                        description:
                            - Traffic shaper. Source firewall.shaper.traffic-shaper.name.
                    shaper-reverse:
                        description:
                            - Reverse traffic shaper. Source firewall.shaper.traffic-shaper.name.
                    sub-category:
                        description:
                            - Application Sub-category ID list.
                        suboptions:
                            id:
                                description:
                                    - Application sub-category ID.
                                required: true
                    technology:
                        description:
                            - Application technology filter.
                    vendor:
                        description:
                            - Application vendor filter.
            extended-log:
                description:
                    - Enable/disable extended logging.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - List name.
                required: true
            options:
                description:
                    - Basic application protocol signatures allowed by default.
                choices:
                    - allow-dns
                    - allow-icmp
                    - allow-http
                    - allow-ssl
                    - allow-quic
            other-application-action:
                description:
                    - Action for other applications.
                choices:
                    - pass
                    - block
            other-application-log:
                description:
                    - Enable/disable logging for other applications.
                choices:
                    - disable
                    - enable
            p2p-black-list:
                description:
                    - P2P applications to be black listed.
                choices:
                    - skype
                    - edonkey
                    - bittorrent
            replacemsg-group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
            unknown-application-action:
                description:
                    - Pass or block traffic from unknown applications.
                choices:
                    - pass
                    - block
            unknown-application-log:
                description:
                    - Enable/disable logging for unknown applications.
                choices:
                    - disable
                    - enable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure application control lists.
    fortios_application_list:
      host:  "{{  host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{  vdom }}"
      application_list:
        state: "present"
        app-replacemsg: "disable"
        comment: "comments"
        deep-app-inspection: "disable"
        entries:
         -
            action: "pass"
            application:
             -
                id:  "9"
            behavior: "<your_own_value>"
            category:
             -
                id:  "12"
            id:  "13"
            log: "disable"
            log-packet: "disable"
            parameters:
             -
                id:  "17"
                value: "<your_own_value>"
            per-ip-shaper: "<your_own_value> (source firewall.shaper.per-ip-shaper.name)"
            popularity: "1"
            protocols: "<your_own_value>"
            quarantine: "none"
            quarantine-expiry: "<your_own_value>"
            quarantine-log: "disable"
            rate-count: "25"
            rate-duration: "26"
            rate-mode: "periodical"
            rate-track: "none"
            risk:
             -
                level: "30"
            session-ttl: "31"
            shaper: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
            shaper-reverse: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
            sub-category:
             -
                id:  "35"
            technology: "<your_own_value>"
            vendor: "<your_own_value>"
        extended-log: "enable"
        name: "default_name_39"
        options: "allow-dns"
        other-application-action: "pass"
        other-application-log: "disable"
        p2p-black-list: "skype"
        replacemsg-group: "<your_own_value> (source system.replacemsg-group.name)"
        unknown-application-action: "pass"
        unknown-application-log: "disable"
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
  sample: "key1"
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


def filter_application_list_data(json):
    option_list = ['app-replacemsg', 'comment', 'deep-app-inspection',
                   'entries', 'extended-log', 'name',
                   'options', 'other-application-action', 'other-application-log',
                   'p2p-black-list', 'replacemsg-group', 'unknown-application-action',
                   'unknown-application-log']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def application_list(data, fos):
    vdom = data['vdom']
    application_list_data = data['application_list']
    filtered_data = filter_application_list_data(application_list_data)
    if application_list_data['state'] == "present":
        return fos.set('application',
                       'list',
                       data=filtered_data,
                       vdom=vdom)

    elif application_list_data['state'] == "absent":
        return fos.delete('application',
                          'list',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_application(data, fos):
    login(data)

    methodlist = ['application_list']
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
        "application_list": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "app-replacemsg": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "comment": {"required": False, "type": "str"},
                "deep-app-inspection": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "entries": {"required": False, "type": "list",
                            "options": {
                                "action": {"required": False, "type": "str",
                                           "choices": ["pass", "block", "reset"]},
                                "application": {"required": False, "type": "list",
                                                "options": {
                                                    "id": {"required": True, "type": "int"}
                                                }},
                                "behavior": {"required": False, "type": "str"},
                                "category": {"required": False, "type": "list",
                                             "options": {
                                                 "id": {"required": True, "type": "int"}
                                             }},
                                "id": {"required": True, "type": "int"},
                                "log": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                                "log-packet": {"required": False, "type": "str",
                                               "choices": ["disable", "enable"]},
                                "parameters": {"required": False, "type": "list",
                                               "options": {
                                                   "id": {"required": True, "type": "int"},
                                                   "value": {"required": False, "type": "str"}
                                               }},
                                "per-ip-shaper": {"required": False, "type": "str"},
                                "popularity": {"required": False, "type": "str",
                                               "choices": ["1", "2", "3",
                                                           "4", "5"]},
                                "protocols": {"required": False, "type": "str"},
                                "quarantine": {"required": False, "type": "str",
                                               "choices": ["none", "attacker"]},
                                "quarantine-expiry": {"required": False, "type": "str"},
                                "quarantine-log": {"required": False, "type": "str",
                                                   "choices": ["disable", "enable"]},
                                "rate-count": {"required": False, "type": "int"},
                                "rate-duration": {"required": False, "type": "int"},
                                "rate-mode": {"required": False, "type": "str",
                                              "choices": ["periodical", "continuous"]},
                                "rate-track": {"required": False, "type": "str",
                                               "choices": ["none", "src-ip", "dest-ip",
                                                           "dhcp-client-mac", "dns-domain"]},
                                "risk": {"required": False, "type": "list",
                                         "options": {
                                             "level": {"required": True, "type": "int"}
                                         }},
                                "session-ttl": {"required": False, "type": "int"},
                                "shaper": {"required": False, "type": "str"},
                                "shaper-reverse": {"required": False, "type": "str"},
                                "sub-category": {"required": False, "type": "list",
                                                 "options": {
                                                     "id": {"required": True, "type": "int"}
                                                 }},
                                "technology": {"required": False, "type": "str"},
                                "vendor": {"required": False, "type": "str"}
                            }},
                "extended-log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str",
                            "choices": ["allow-dns", "allow-icmp", "allow-http",
                                        "allow-ssl", "allow-quic"]},
                "other-application-action": {"required": False, "type": "str",
                                             "choices": ["pass", "block"]},
                "other-application-log": {"required": False, "type": "str",
                                          "choices": ["disable", "enable"]},
                "p2p-black-list": {"required": False, "type": "str",
                                   "choices": ["skype", "edonkey", "bittorrent"]},
                "replacemsg-group": {"required": False, "type": "str"},
                "unknown-application-action": {"required": False, "type": "str",
                                               "choices": ["pass", "block"]},
                "unknown-application-log": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]}

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

    is_error, has_changed, result = fortios_application(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
