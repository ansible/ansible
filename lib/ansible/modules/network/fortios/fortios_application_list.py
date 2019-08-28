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
module: fortios_application_list
short_description: Configure application control lists in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify application feature and list category.
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
    application_list:
        description:
            - Configure application control lists.
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
            app_replacemsg:
                description:
                    - Enable/disable replacement messages for blocked applications.
                type: str
                choices:
                    - disable
                    - enable
            comment:
                description:
                    - comments
                type: str
            deep_app_inspection:
                description:
                    - Enable/disable deep application inspection.
                type: str
                choices:
                    - disable
                    - enable
            entries:
                description:
                    - Application list entries.
                type: list
                suboptions:
                    action:
                        description:
                            - Pass or block traffic, or reset connection for traffic from this application.
                        type: str
                        choices:
                            - pass
                            - block
                            - reset
                    application:
                        description:
                            - ID of allowed applications.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Application IDs.
                                required: true
                                type: int
                    behavior:
                        description:
                            - Application behavior filter.
                        type: str
                    category:
                        description:
                            - Category ID list.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Application category ID.
                                required: true
                                type: int
                    id:
                        description:
                            - Entry ID.
                        required: true
                        type: int
                    log:
                        description:
                            - Enable/disable logging for this application list.
                        type: str
                        choices:
                            - disable
                            - enable
                    log_packet:
                        description:
                            - Enable/disable packet logging.
                        type: str
                        choices:
                            - disable
                            - enable
                    parameters:
                        description:
                            - Application parameters.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Parameter ID.
                                required: true
                                type: int
                            value:
                                description:
                                    - Parameter value.
                                type: str
                    per_ip_shaper:
                        description:
                            - Per-IP traffic shaper. Source firewall.shaper.per-ip-shaper.name.
                        type: str
                    popularity:
                        description:
                            - Application popularity filter (1 - 5, from least to most popular).
                        type: str
                        choices:
                            - 1
                            - 2
                            - 3
                            - 4
                            - 5
                    protocols:
                        description:
                            - Application protocol filter.
                        type: str
                    quarantine:
                        description:
                            - Quarantine method.
                        type: str
                        choices:
                            - none
                            - attacker
                    quarantine_expiry:
                        description:
                            - Duration of quarantine. (Format ###d##h##m, minimum 1m, maximum 364d23h59m). Requires quarantine set to attacker.
                        type: str
                    quarantine_log:
                        description:
                            - Enable/disable quarantine logging.
                        type: str
                        choices:
                            - disable
                            - enable
                    rate_count:
                        description:
                            - Count of the rate.
                        type: int
                    rate_duration:
                        description:
                            - Duration (sec) of the rate.
                        type: int
                    rate_mode:
                        description:
                            - Rate limit mode.
                        type: str
                        choices:
                            - periodical
                            - continuous
                    rate_track:
                        description:
                            - Track the packet protocol field.
                        type: str
                        choices:
                            - none
                            - src-ip
                            - dest-ip
                            - dhcp-client-mac
                            - dns-domain
                    risk:
                        description:
                            - Risk, or impact, of allowing traffic from this application to occur (1 - 5; Low, Elevated, Medium, High, and Critical).
                        type: list
                        suboptions:
                            level:
                                description:
                                    - Risk, or impact, of allowing traffic from this application to occur (1 - 5; Low, Elevated, Medium, High, and Critical).
                                required: true
                                type: int
                    session_ttl:
                        description:
                            - Session TTL (0 = default).
                        type: int
                    shaper:
                        description:
                            - Traffic shaper. Source firewall.shaper.traffic-shaper.name.
                        type: str
                    shaper_reverse:
                        description:
                            - Reverse traffic shaper. Source firewall.shaper.traffic-shaper.name.
                        type: str
                    sub_category:
                        description:
                            - Application Sub-category ID list.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Application sub-category ID.
                                required: true
                                type: int
                    technology:
                        description:
                            - Application technology filter.
                        type: str
                    vendor:
                        description:
                            - Application vendor filter.
                        type: str
            extended_log:
                description:
                    - Enable/disable extended logging.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - List name.
                required: true
                type: str
            options:
                description:
                    - Basic application protocol signatures allowed by default.
                type: str
                choices:
                    - allow-dns
                    - allow-icmp
                    - allow-http
                    - allow-ssl
                    - allow-quic
            other_application_action:
                description:
                    - Action for other applications.
                type: str
                choices:
                    - pass
                    - block
            other_application_log:
                description:
                    - Enable/disable logging for other applications.
                type: str
                choices:
                    - disable
                    - enable
            p2p_black_list:
                description:
                    - P2P applications to be black listed.
                type: str
                choices:
                    - skype
                    - edonkey
                    - bittorrent
            replacemsg_group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
                type: str
            unknown_application_action:
                description:
                    - Pass or block traffic from unknown applications.
                type: str
                choices:
                    - pass
                    - block
            unknown_application_log:
                description:
                    - Enable/disable logging for unknown applications.
                type: str
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
   ssl_verify: "False"
  tasks:
  - name: Configure application control lists.
    fortios_application_list:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      application_list:
        app_replacemsg: "disable"
        comment: "comments"
        deep_app_inspection: "disable"
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
            log_packet: "disable"
            parameters:
             -
                id:  "17"
                value: "<your_own_value>"
            per_ip_shaper: "<your_own_value> (source firewall.shaper.per-ip-shaper.name)"
            popularity: "1"
            protocols: "<your_own_value>"
            quarantine: "none"
            quarantine_expiry: "<your_own_value>"
            quarantine_log: "disable"
            rate_count: "25"
            rate_duration: "26"
            rate_mode: "periodical"
            rate_track: "none"
            risk:
             -
                level: "30"
            session_ttl: "31"
            shaper: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
            shaper_reverse: "<your_own_value> (source firewall.shaper.traffic-shaper.name)"
            sub_category:
             -
                id:  "35"
            technology: "<your_own_value>"
            vendor: "<your_own_value>"
        extended_log: "enable"
        name: "default_name_39"
        options: "allow-dns"
        other_application_action: "pass"
        other_application_log: "disable"
        p2p_black_list: "skype"
        replacemsg_group: "<your_own_value> (source system.replacemsg-group.name)"
        unknown_application_action: "pass"
        unknown_application_log: "disable"
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


def filter_application_list_data(json):
    option_list = ['app_replacemsg', 'comment', 'deep_app_inspection',
                   'entries', 'extended_log', 'name',
                   'options', 'other_application_action', 'other_application_log',
                   'p2p_black_list', 'replacemsg_group', 'unknown_application_action',
                   'unknown_application_log']
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


def application_list(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['application_list'] and data['application_list']:
        state = data['application_list']['state']
    else:
        state = True
    application_list_data = data['application_list']
    filtered_data = underscore_to_hyphen(filter_application_list_data(application_list_data))

    if state == "present":
        return fos.set('application',
                       'list',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('application',
                          'list',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_application(data, fos):

    if data['application_list']:
        resp = application_list(data, fos)

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
        "application_list": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "app_replacemsg": {"required": False, "type": "str",
                                   "choices": ["disable", "enable"]},
                "comment": {"required": False, "type": "str"},
                "deep_app_inspection": {"required": False, "type": "str",
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
                                "log_packet": {"required": False, "type": "str",
                                               "choices": ["disable", "enable"]},
                                "parameters": {"required": False, "type": "list",
                                               "options": {
                                                   "id": {"required": True, "type": "int"},
                                                   "value": {"required": False, "type": "str"}
                                               }},
                                "per_ip_shaper": {"required": False, "type": "str"},
                                "popularity": {"required": False, "type": "str",
                                               "choices": ["1", "2", "3",
                                                           "4", "5"]},
                                "protocols": {"required": False, "type": "str"},
                                "quarantine": {"required": False, "type": "str",
                                               "choices": ["none", "attacker"]},
                                "quarantine_expiry": {"required": False, "type": "str"},
                                "quarantine_log": {"required": False, "type": "str",
                                                   "choices": ["disable", "enable"]},
                                "rate_count": {"required": False, "type": "int"},
                                "rate_duration": {"required": False, "type": "int"},
                                "rate_mode": {"required": False, "type": "str",
                                              "choices": ["periodical", "continuous"]},
                                "rate_track": {"required": False, "type": "str",
                                               "choices": ["none", "src-ip", "dest-ip",
                                                           "dhcp-client-mac", "dns-domain"]},
                                "risk": {"required": False, "type": "list",
                                         "options": {
                                             "level": {"required": True, "type": "int"}
                                         }},
                                "session_ttl": {"required": False, "type": "int"},
                                "shaper": {"required": False, "type": "str"},
                                "shaper_reverse": {"required": False, "type": "str"},
                                "sub_category": {"required": False, "type": "list",
                                                 "options": {
                                                     "id": {"required": True, "type": "int"}
                                                 }},
                                "technology": {"required": False, "type": "str"},
                                "vendor": {"required": False, "type": "str"}
                            }},
                "extended_log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str",
                            "choices": ["allow-dns", "allow-icmp", "allow-http",
                                        "allow-ssl", "allow-quic"]},
                "other_application_action": {"required": False, "type": "str",
                                             "choices": ["pass", "block"]},
                "other_application_log": {"required": False, "type": "str",
                                          "choices": ["disable", "enable"]},
                "p2p_black_list": {"required": False, "type": "str",
                                   "choices": ["skype", "edonkey", "bittorrent"]},
                "replacemsg_group": {"required": False, "type": "str"},
                "unknown_application_action": {"required": False, "type": "str",
                                               "choices": ["pass", "block"]},
                "unknown_application_log": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]}

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

            is_error, has_changed, result = fortios_application(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_application(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
