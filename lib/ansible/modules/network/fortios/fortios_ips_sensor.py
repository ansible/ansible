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
module: fortios_ips_sensor
short_description: Configure IPS sensor in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify ips feature and sensor category.
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
    ips_sensor:
        description:
            - Configure IPS sensor.
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
            block_malicious_url:
                description:
                    - Enable/disable malicious URL blocking.
                type: str
                choices:
                    - disable
                    - enable
            comment:
                description:
                    - Comment.
                type: str
            entries:
                description:
                    - IPS sensor filter.
                type: list
                suboptions:
                    action:
                        description:
                            - Action taken with traffic in which signatures are detected.
                        type: str
                        choices:
                            - pass
                            - block
                            - reset
                            - default
                    application:
                        description:
                            - Applications to be protected. set application ? lists available applications. all includes all applications. other includes all
                               unlisted applications.
                        type: str
                    exempt_ip:
                        description:
                            - Traffic from selected source or destination IP addresses is exempt from this signature.
                        type: list
                        suboptions:
                            dst_ip:
                                description:
                                    - Destination IP address and netmask.
                                type: str
                            id:
                                description:
                                    - Exempt IP ID.
                                required: true
                                type: int
                            src_ip:
                                description:
                                    - Source IP address and netmask.
                                type: str
                    id:
                        description:
                            - Rule ID in IPS database (0 - 4294967295).
                        required: true
                        type: int
                    location:
                        description:
                            - Protect client or server traffic.
                        type: str
                    log:
                        description:
                            - Enable/disable logging of signatures included in filter.
                        type: str
                        choices:
                            - disable
                            - enable
                    log_attack_context:
                        description:
                            - "Enable/disable logging of attack context: URL buffer, header buffer, body buffer, packet buffer."
                        type: str
                        choices:
                            - disable
                            - enable
                    log_packet:
                        description:
                            - Enable/disable packet logging. Enable to save the packet that triggers the filter. You can download the packets in pcap format
                               for diagnostic use.
                        type: str
                        choices:
                            - disable
                            - enable
                    os:
                        description:
                            - Operating systems to be protected.  all includes all operating systems. other includes all unlisted operating systems.
                        type: str
                    protocol:
                        description:
                            - Protocols to be examined. set protocol ? lists available protocols. all includes all protocols. other includes all unlisted
                               protocols.
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
                    rule:
                        description:
                            - Identifies the predefined or custom IPS signatures to add to the sensor.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Rule IPS.
                                required: true
                                type: int
                    severity:
                        description:
                            - Relative severity of the signature, from info to critical. Log messages generated by the signature include the severity.
                        type: str
                    status:
                        description:
                            - Status of the signatures included in filter. default enables the filter and only use filters with default status of enable.
                               Filters with default status of disable will not be used.
                        type: str
                        choices:
                            - disable
                            - enable
                            - default
            extended_log:
                description:
                    - Enable/disable extended logging.
                type: str
                choices:
                    - enable
                    - disable
            filter:
                description:
                    - IPS sensor filter.
                type: list
                suboptions:
                    action:
                        description:
                            - Action of selected rules.
                        type: str
                        choices:
                            - pass
                            - block
                            - reset
                            - default
                    application:
                        description:
                            - Vulnerable application filter.
                        type: str
                    location:
                        description:
                            - Vulnerability location filter.
                        type: str
                    log:
                        description:
                            - Enable/disable logging of selected rules.
                        type: str
                        choices:
                            - disable
                            - enable
                    log_packet:
                        description:
                            - Enable/disable packet logging of selected rules.
                        type: str
                        choices:
                            - disable
                            - enable
                    name:
                        description:
                            - Filter name.
                        required: true
                        type: str
                    os:
                        description:
                            - Vulnerable OS filter.
                        type: str
                    protocol:
                        description:
                            - Vulnerable protocol filter.
                        type: str
                    quarantine:
                        description:
                            - Quarantine IP or interface.
                        type: str
                        choices:
                            - none
                            - attacker
                    quarantine_expiry:
                        description:
                            - Duration of quarantine in minute.
                        type: int
                    quarantine_log:
                        description:
                            - Enable/disable logging of selected quarantine.
                        type: str
                        choices:
                            - disable
                            - enable
                    severity:
                        description:
                            - Vulnerability severity filter.
                        type: str
                    status:
                        description:
                            - Selected rules status.
                        type: str
                        choices:
                            - disable
                            - enable
                            - default
            name:
                description:
                    - Sensor name.
                required: true
                type: str
            override:
                description:
                    - IPS override rule.
                type: list
                suboptions:
                    action:
                        description:
                            - Action of override rule.
                        type: str
                        choices:
                            - pass
                            - block
                            - reset
                    exempt_ip:
                        description:
                            - Exempted IP.
                        type: list
                        suboptions:
                            dst_ip:
                                description:
                                    - Destination IP address and netmask.
                                type: str
                            id:
                                description:
                                    - Exempt IP ID.
                                required: true
                                type: int
                            src_ip:
                                description:
                                    - Source IP address and netmask.
                                type: str
                    log:
                        description:
                            - Enable/disable logging.
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
                    quarantine:
                        description:
                            - Quarantine IP or interface.
                        type: str
                        choices:
                            - none
                            - attacker
                    quarantine_expiry:
                        description:
                            - Duration of quarantine in minute.
                        type: int
                    quarantine_log:
                        description:
                            - Enable/disable logging of selected quarantine.
                        type: str
                        choices:
                            - disable
                            - enable
                    rule_id:
                        description:
                            - Override rule ID.
                        type: int
                    status:
                        description:
                            - Enable/disable status of override rule.
                        type: str
                        choices:
                            - disable
                            - enable
            replacemsg_group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
                type: str
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
  - name: Configure IPS sensor.
    fortios_ips_sensor:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      ips_sensor:
        block_malicious_url: "disable"
        comment: "Comment."
        entries:
         -
            action: "pass"
            application: "<your_own_value>"
            exempt_ip:
             -
                dst_ip: "<your_own_value>"
                id:  "10"
                src_ip: "<your_own_value>"
            id:  "12"
            location: "<your_own_value>"
            log: "disable"
            log_attack_context: "disable"
            log_packet: "disable"
            os: "<your_own_value>"
            protocol: "<your_own_value>"
            quarantine: "none"
            quarantine_expiry: "<your_own_value>"
            quarantine_log: "disable"
            rate_count: "22"
            rate_duration: "23"
            rate_mode: "periodical"
            rate_track: "none"
            rule:
             -
                id:  "27"
            severity: "<your_own_value>"
            status: "disable"
        extended_log: "enable"
        filter:
         -
            action: "pass"
            application: "<your_own_value>"
            location: "<your_own_value>"
            log: "disable"
            log_packet: "disable"
            name: "default_name_37"
            os: "<your_own_value>"
            protocol: "<your_own_value>"
            quarantine: "none"
            quarantine_expiry: "41"
            quarantine_log: "disable"
            severity: "<your_own_value>"
            status: "disable"
        name: "default_name_45"
        override:
         -
            action: "pass"
            exempt_ip:
             -
                dst_ip: "<your_own_value>"
                id:  "50"
                src_ip: "<your_own_value>"
            log: "disable"
            log_packet: "disable"
            quarantine: "none"
            quarantine_expiry: "55"
            quarantine_log: "disable"
            rule_id: "57"
            status: "disable"
        replacemsg_group: "<your_own_value> (source system.replacemsg-group.name)"
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


def filter_ips_sensor_data(json):
    option_list = ['block_malicious_url', 'comment', 'entries',
                   'extended_log', 'filter', 'name',
                   'override', 'replacemsg_group']
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


def ips_sensor(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['ips_sensor'] and data['ips_sensor']:
        state = data['ips_sensor']['state']
    else:
        state = True
    ips_sensor_data = data['ips_sensor']
    filtered_data = underscore_to_hyphen(filter_ips_sensor_data(ips_sensor_data))

    if state == "present":
        return fos.set('ips',
                       'sensor',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('ips',
                          'sensor',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_ips(data, fos):

    if data['ips_sensor']:
        resp = ips_sensor(data, fos)

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
        "ips_sensor": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "block_malicious_url": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "comment": {"required": False, "type": "str"},
                "entries": {"required": False, "type": "list",
                            "options": {
                                "action": {"required": False, "type": "str",
                                           "choices": ["pass", "block", "reset",
                                                       "default"]},
                                "application": {"required": False, "type": "str"},
                                "exempt_ip": {"required": False, "type": "list",
                                              "options": {
                                                  "dst_ip": {"required": False, "type": "str"},
                                                  "id": {"required": True, "type": "int"},
                                                  "src_ip": {"required": False, "type": "str"}
                                              }},
                                "id": {"required": True, "type": "int"},
                                "location": {"required": False, "type": "str"},
                                "log": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                                "log_attack_context": {"required": False, "type": "str",
                                                       "choices": ["disable", "enable"]},
                                "log_packet": {"required": False, "type": "str",
                                               "choices": ["disable", "enable"]},
                                "os": {"required": False, "type": "str"},
                                "protocol": {"required": False, "type": "str"},
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
                                "rule": {"required": False, "type": "list",
                                         "options": {
                                             "id": {"required": True, "type": "int"}
                                         }},
                                "severity": {"required": False, "type": "str"},
                                "status": {"required": False, "type": "str",
                                           "choices": ["disable", "enable", "default"]}
                            }},
                "extended_log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "filter": {"required": False, "type": "list",
                           "options": {
                               "action": {"required": False, "type": "str",
                                          "choices": ["pass", "block", "reset",
                                                      "default"]},
                               "application": {"required": False, "type": "str"},
                               "location": {"required": False, "type": "str"},
                               "log": {"required": False, "type": "str",
                                       "choices": ["disable", "enable"]},
                               "log_packet": {"required": False, "type": "str",
                                              "choices": ["disable", "enable"]},
                               "name": {"required": True, "type": "str"},
                               "os": {"required": False, "type": "str"},
                               "protocol": {"required": False, "type": "str"},
                               "quarantine": {"required": False, "type": "str",
                                              "choices": ["none", "attacker"]},
                               "quarantine_expiry": {"required": False, "type": "int"},
                               "quarantine_log": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]},
                               "severity": {"required": False, "type": "str"},
                               "status": {"required": False, "type": "str",
                                          "choices": ["disable", "enable", "default"]}
                           }},
                "name": {"required": True, "type": "str"},
                "override": {"required": False, "type": "list",
                             "options": {
                                 "action": {"required": False, "type": "str",
                                            "choices": ["pass", "block", "reset"]},
                                 "exempt_ip": {"required": False, "type": "list",
                                               "options": {
                                                   "dst_ip": {"required": False, "type": "str"},
                                                   "id": {"required": True, "type": "int"},
                                                   "src_ip": {"required": False, "type": "str"}
                                               }},
                                 "log": {"required": False, "type": "str",
                                         "choices": ["disable", "enable"]},
                                 "log_packet": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                                 "quarantine": {"required": False, "type": "str",
                                                "choices": ["none", "attacker"]},
                                 "quarantine_expiry": {"required": False, "type": "int"},
                                 "quarantine_log": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable"]},
                                 "rule_id": {"required": False, "type": "int"},
                                 "status": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]}
                             }},
                "replacemsg_group": {"required": False, "type": "str"}

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

            is_error, has_changed, result = fortios_ips(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_ips(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
