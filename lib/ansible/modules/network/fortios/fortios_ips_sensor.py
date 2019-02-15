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
module: fortios_ips_sensor
short_description: Configure IPS sensor.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure ips feature and sensor category.
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
    ips_sensor:
        description:
            - Configure IPS sensor.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            block-malicious-url:
                description:
                    - Enable/disable malicious URL blocking.
                choices:
                    - disable
                    - enable
            comment:
                description:
                    - Comment.
            entries:
                description:
                    - IPS sensor filter.
                suboptions:
                    action:
                        description:
                            - Action taken with traffic in which signatures are detected.
                        choices:
                            - pass
                            - block
                            - reset
                            - default
                    application:
                        description:
                            - Applications to be protected. set application ? lists available applications. all includes all applications. other includes all
                               unlisted applications.
                    exempt-ip:
                        description:
                            - Traffic from selected source or destination IP addresses is exempt from this signature.
                        suboptions:
                            dst-ip:
                                description:
                                    - Destination IP address and netmask.
                            id:
                                description:
                                    - Exempt IP ID.
                                required: true
                            src-ip:
                                description:
                                    - Source IP address and netmask.
                    id:
                        description:
                            - Rule ID in IPS database (0 - 4294967295).
                        required: true
                    location:
                        description:
                            - Protect client or server traffic.
                    log:
                        description:
                            - Enable/disable logging of signatures included in filter.
                        choices:
                            - disable
                            - enable
                    log-attack-context:
                        description:
                            - "Enable/disable logging of attack context: URL buffer, header buffer, body buffer, packet buffer."
                        choices:
                            - disable
                            - enable
                    log-packet:
                        description:
                            - Enable/disable packet logging. Enable to save the packet that triggers the filter. You can download the packets in pcap format
                               for diagnostic use.
                        choices:
                            - disable
                            - enable
                    os:
                        description:
                            - Operating systems to be protected.  all includes all operating systems. other includes all unlisted operating systems.
                    protocol:
                        description:
                            - Protocols to be examined. set protocol ? lists available protocols. all includes all protocols. other includes all unlisted
                               protocols.
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
                    rule:
                        description:
                            - Identifies the predefined or custom IPS signatures to add to the sensor.
                        suboptions:
                            id:
                                description:
                                    - Rule IPS.
                                required: true
                    severity:
                        description:
                            - Relative severity of the signature, from info to critical. Log messages generated by the signature include the severity.
                    status:
                        description:
                            - Status of the signatures included in filter. default enables the filter and only use filters with default status of enable.
                               Filters with default status of disable will not be used.
                        choices:
                            - disable
                            - enable
                            - default
            extended-log:
                description:
                    - Enable/disable extended logging.
                choices:
                    - enable
                    - disable
            filter:
                description:
                    - IPS sensor filter.
                suboptions:
                    action:
                        description:
                            - Action of selected rules.
                        choices:
                            - pass
                            - block
                            - reset
                            - default
                    application:
                        description:
                            - Vulnerable application filter.
                    location:
                        description:
                            - Vulnerability location filter.
                    log:
                        description:
                            - Enable/disable logging of selected rules.
                        choices:
                            - disable
                            - enable
                    log-packet:
                        description:
                            - Enable/disable packet logging of selected rules.
                        choices:
                            - disable
                            - enable
                    name:
                        description:
                            - Filter name.
                        required: true
                    os:
                        description:
                            - Vulnerable OS filter.
                    protocol:
                        description:
                            - Vulnerable protocol filter.
                    quarantine:
                        description:
                            - Quarantine IP or interface.
                        choices:
                            - none
                            - attacker
                    quarantine-expiry:
                        description:
                            - Duration of quarantine in minute.
                    quarantine-log:
                        description:
                            - Enable/disable logging of selected quarantine.
                        choices:
                            - disable
                            - enable
                    severity:
                        description:
                            - Vulnerability severity filter.
                    status:
                        description:
                            - Selected rules status.
                        choices:
                            - disable
                            - enable
                            - default
            name:
                description:
                    - Sensor name.
                required: true
            override:
                description:
                    - IPS override rule.
                suboptions:
                    action:
                        description:
                            - Action of override rule.
                        choices:
                            - pass
                            - block
                            - reset
                    exempt-ip:
                        description:
                            - Exempted IP.
                        suboptions:
                            dst-ip:
                                description:
                                    - Destination IP address and netmask.
                            id:
                                description:
                                    - Exempt IP ID.
                                required: true
                            src-ip:
                                description:
                                    - Source IP address and netmask.
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - disable
                            - enable
                    log-packet:
                        description:
                            - Enable/disable packet logging.
                        choices:
                            - disable
                            - enable
                    quarantine:
                        description:
                            - Quarantine IP or interface.
                        choices:
                            - none
                            - attacker
                    quarantine-expiry:
                        description:
                            - Duration of quarantine in minute.
                    quarantine-log:
                        description:
                            - Enable/disable logging of selected quarantine.
                        choices:
                            - disable
                            - enable
                    rule-id:
                        description:
                            - Override rule ID.
                        required: true
                    status:
                        description:
                            - Enable/disable status of override rule.
                        choices:
                            - disable
                            - enable
            replacemsg-group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPS sensor.
    fortios_ips_sensor:
      host:  "{{  host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{  vdom }}"
      ips_sensor:
        state: "present"
        block-malicious-url: "disable"
        comment: "Comment."
        entries:
         -
            action: "pass"
            application: "<your_own_value>"
            exempt-ip:
             -
                dst-ip: "<your_own_value>"
                id:  "10"
                src-ip: "<your_own_value>"
            id:  "12"
            location: "<your_own_value>"
            log: "disable"
            log-attack-context: "disable"
            log-packet: "disable"
            os: "<your_own_value>"
            protocol: "<your_own_value>"
            quarantine: "none"
            quarantine-expiry: "<your_own_value>"
            quarantine-log: "disable"
            rate-count: "22"
            rate-duration: "23"
            rate-mode: "periodical"
            rate-track: "none"
            rule:
             -
                id:  "27"
            severity: "<your_own_value>"
            status: "disable"
        extended-log: "enable"
        filter:
         -
            action: "pass"
            application: "<your_own_value>"
            location: "<your_own_value>"
            log: "disable"
            log-packet: "disable"
            name: "default_name_37"
            os: "<your_own_value>"
            protocol: "<your_own_value>"
            quarantine: "none"
            quarantine-expiry: "41"
            quarantine-log: "disable"
            severity: "<your_own_value>"
            status: "disable"
        name: "default_name_45"
        override:
         -
            action: "pass"
            exempt-ip:
             -
                dst-ip: "<your_own_value>"
                id:  "50"
                src-ip: "<your_own_value>"
            log: "disable"
            log-packet: "disable"
            quarantine: "none"
            quarantine-expiry: "55"
            quarantine-log: "disable"
            rule-id: "57"
            status: "disable"
        replacemsg-group: "<your_own_value> (source system.replacemsg-group.name)"
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


def filter_ips_sensor_data(json):
    option_list = ['block-malicious-url', 'comment', 'entries',
                   'extended-log', 'filter', 'name',
                   'override', 'replacemsg-group']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def ips_sensor(data, fos):
    vdom = data['vdom']
    ips_sensor_data = data['ips_sensor']
    filtered_data = filter_ips_sensor_data(ips_sensor_data)
    if ips_sensor_data['state'] == "present":
        return fos.set('ips',
                       'sensor',
                       data=filtered_data,
                       vdom=vdom)

    elif ips_sensor_data['state'] == "absent":
        return fos.delete('ips',
                          'sensor',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_ips(data, fos):
    login(data)

    methodlist = ['ips_sensor']
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
        "ips_sensor": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "block-malicious-url": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "comment": {"required": False, "type": "str"},
                "entries": {"required": False, "type": "list",
                            "options": {
                                "action": {"required": False, "type": "str",
                                           "choices": ["pass", "block", "reset",
                                                       "default"]},
                                "application": {"required": False, "type": "str"},
                                "exempt-ip": {"required": False, "type": "list",
                                              "options": {
                                                  "dst-ip": {"required": False, "type": "str"},
                                                  "id": {"required": True, "type": "int"},
                                                  "src-ip": {"required": False, "type": "str"}
                                              }},
                                "id": {"required": True, "type": "int"},
                                "location": {"required": False, "type": "str"},
                                "log": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                                "log-attack-context": {"required": False, "type": "str",
                                                       "choices": ["disable", "enable"]},
                                "log-packet": {"required": False, "type": "str",
                                               "choices": ["disable", "enable"]},
                                "os": {"required": False, "type": "str"},
                                "protocol": {"required": False, "type": "str"},
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
                                "rule": {"required": False, "type": "list",
                                         "options": {
                                             "id": {"required": True, "type": "int"}
                                         }},
                                "severity": {"required": False, "type": "str"},
                                "status": {"required": False, "type": "str",
                                           "choices": ["disable", "enable", "default"]}
                            }},
                "extended-log": {"required": False, "type": "str",
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
                               "log-packet": {"required": False, "type": "str",
                                              "choices": ["disable", "enable"]},
                               "name": {"required": True, "type": "str"},
                               "os": {"required": False, "type": "str"},
                               "protocol": {"required": False, "type": "str"},
                               "quarantine": {"required": False, "type": "str",
                                              "choices": ["none", "attacker"]},
                               "quarantine-expiry": {"required": False, "type": "int"},
                               "quarantine-log": {"required": False, "type": "str",
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
                                 "exempt-ip": {"required": False, "type": "list",
                                               "options": {
                                                   "dst-ip": {"required": False, "type": "str"},
                                                   "id": {"required": True, "type": "int"},
                                                   "src-ip": {"required": False, "type": "str"}
                                               }},
                                 "log": {"required": False, "type": "str",
                                         "choices": ["disable", "enable"]},
                                 "log-packet": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                                 "quarantine": {"required": False, "type": "str",
                                                "choices": ["none", "attacker"]},
                                 "quarantine-expiry": {"required": False, "type": "int"},
                                 "quarantine-log": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable"]},
                                 "rule-id": {"required": True, "type": "int"},
                                 "status": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]}
                             }},
                "replacemsg-group": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_ips(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
