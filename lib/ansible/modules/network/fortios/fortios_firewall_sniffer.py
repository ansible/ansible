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
module: fortios_firewall_sniffer
short_description: Configure sniffer in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and sniffer category.
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
            - FortiOS or FortiGate ip adress.
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
    firewall_sniffer:
        description:
            - Configure sniffer.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            anomaly:
                description:
                    - Configuration method to edit Denial of Service (DoS) anomaly settings.
                suboptions:
                    action:
                        description:
                            - Action taken when the threshold is reached.
                        choices:
                            - pass
                            - block
                    log:
                        description:
                            - Enable/disable anomaly logging.
                        choices:
                            - enable
                            - disable
                    name:
                        description:
                            - Anomaly name.
                        required: true
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
                    status:
                        description:
                            - Enable/disable this anomaly.
                        choices:
                            - disable
                            - enable
                    threshold:
                        description:
                            - Anomaly threshold. Number of detected instances per minute that triggers the anomaly action.
                    threshold(default):
                        description:
                            - Number of detected instances per minute which triggers action (1 - 2147483647, default = 1000). Note that each anomaly has a
                               different threshold value assigned to it.
            application-list:
                description:
                    - Name of an existing application list. Source application.list.name.
            application-list-status:
                description:
                    - Enable/disable application control profile.
                choices:
                    - enable
                    - disable
            av-profile:
                description:
                    - Name of an existing antivirus profile. Source antivirus.profile.name.
            av-profile-status:
                description:
                    - Enable/disable antivirus profile.
                choices:
                    - enable
                    - disable
            dlp-sensor:
                description:
                    - Name of an existing DLP sensor. Source dlp.sensor.name.
            dlp-sensor-status:
                description:
                    - Enable/disable DLP sensor.
                choices:
                    - enable
                    - disable
            dsri:
                description:
                    - Enable/disable DSRI.
                choices:
                    - enable
                    - disable
            host:
                description:
                    - "Hosts to filter for in sniffer traffic (Format examples: 1.1.1.1, 2.2.2.0/24, 3.3.3.3/255.255.255.0, 4.4.4.0-4.4.4.240)."
            id:
                description:
                    - Sniffer ID.
                required: true
            interface:
                description:
                    - Interface name that traffic sniffing will take place on. Source system.interface.name.
            ips-dos-status:
                description:
                    - Enable/disable IPS DoS anomaly detection.
                choices:
                    - enable
                    - disable
            ips-sensor:
                description:
                    - Name of an existing IPS sensor. Source ips.sensor.name.
            ips-sensor-status:
                description:
                    - Enable/disable IPS sensor.
                choices:
                    - enable
                    - disable
            ipv6:
                description:
                    - Enable/disable sniffing IPv6 packets.
                choices:
                    - enable
                    - disable
            logtraffic:
                description:
                    - Either log all sessions, only sessions that have a security profile applied, or disable all logging for this policy.
                choices:
                    - all
                    - utm
                    - disable
            max-packet-count:
                description:
                    - Maximum packet count (1 - 1000000, default = 10000).
            non-ip:
                description:
                    - Enable/disable sniffing non-IP packets.
                choices:
                    - enable
                    - disable
            port:
                description:
                    - "Ports to sniff (Format examples: 10, :20, 30:40, 50-, 100-200)."
            protocol:
                description:
                    - Integer value for the protocol type as defined by IANA (0 - 255).
            scan-botnet-connections:
                description:
                    - Enable/disable scanning of connections to Botnet servers.
                choices:
                    - disable
                    - block
                    - monitor
            spamfilter-profile:
                description:
                    - Name of an existing spam filter profile. Source spamfilter.profile.name.
            spamfilter-profile-status:
                description:
                    - Enable/disable spam filter.
                choices:
                    - enable
                    - disable
            status:
                description:
                    - Enable/disable the active status of the sniffer.
                choices:
                    - enable
                    - disable
            vlan:
                description:
                    - List of VLANs to sniff.
            webfilter-profile:
                description:
                    - Name of an existing web filter profile. Source webfilter.profile.name.
            webfilter-profile-status:
                description:
                    - Enable/disable web filter profile.
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
  - name: Configure sniffer.
    fortios_firewall_sniffer:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_sniffer:
        state: "present"
        anomaly:
         -
            action: "pass"
            log: "enable"
            name: "default_name_6"
            quarantine: "none"
            quarantine-expiry: "<your_own_value>"
            quarantine-log: "disable"
            status: "disable"
            threshold: "11"
            threshold(default): "12"
        application-list: "<your_own_value> (source application.list.name)"
        application-list-status: "enable"
        av-profile: "<your_own_value> (source antivirus.profile.name)"
        av-profile-status: "enable"
        dlp-sensor: "<your_own_value> (source dlp.sensor.name)"
        dlp-sensor-status: "enable"
        dsri: "enable"
        host: "myhostname"
        id:  "21"
        interface: "<your_own_value> (source system.interface.name)"
        ips-dos-status: "enable"
        ips-sensor: "<your_own_value> (source ips.sensor.name)"
        ips-sensor-status: "enable"
        ipv6: "enable"
        logtraffic: "all"
        max-packet-count: "28"
        non-ip: "enable"
        port: "<your_own_value>"
        protocol: "<your_own_value>"
        scan-botnet-connections: "disable"
        spamfilter-profile: "<your_own_value> (source spamfilter.profile.name)"
        spamfilter-profile-status: "enable"
        status: "enable"
        vlan: "<your_own_value>"
        webfilter-profile: "<your_own_value> (source webfilter.profile.name)"
        webfilter-profile-status: "enable"
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


def filter_firewall_sniffer_data(json):
    option_list = ['anomaly', 'application-list', 'application-list-status',
                   'av-profile', 'av-profile-status', 'dlp-sensor',
                   'dlp-sensor-status', 'dsri', 'host',
                   'id', 'interface', 'ips-dos-status',
                   'ips-sensor', 'ips-sensor-status', 'ipv6',
                   'logtraffic', 'max-packet-count', 'non-ip',
                   'port', 'protocol', 'scan-botnet-connections',
                   'spamfilter-profile', 'spamfilter-profile-status', 'status',
                   'vlan', 'webfilter-profile', 'webfilter-profile-status']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_sniffer(data, fos):
    vdom = data['vdom']
    firewall_sniffer_data = data['firewall_sniffer']
    filtered_data = filter_firewall_sniffer_data(firewall_sniffer_data)
    if firewall_sniffer_data['state'] == "present":
        return fos.set('firewall',
                       'sniffer',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_sniffer_data['state'] == "absent":
        return fos.delete('firewall',
                          'sniffer',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_sniffer']
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
        "https": {"required": False, "type": "bool", "default": True},
        "firewall_sniffer": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "anomaly": {"required": False, "type": "list",
                            "options": {
                                "action": {"required": False, "type": "str",
                                           "choices": ["pass", "block"]},
                                "log": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                                "name": {"required": True, "type": "str"},
                                "quarantine": {"required": False, "type": "str",
                                               "choices": ["none", "attacker"]},
                                "quarantine-expiry": {"required": False, "type": "str"},
                                "quarantine-log": {"required": False, "type": "str",
                                                   "choices": ["disable", "enable"]},
                                "status": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                                "threshold": {"required": False, "type": "int"},
                                "threshold(default)": {"required": False, "type": "int"}
                            }},
                "application-list": {"required": False, "type": "str"},
                "application-list-status": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "av-profile": {"required": False, "type": "str"},
                "av-profile-status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "dlp-sensor": {"required": False, "type": "str"},
                "dlp-sensor-status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "dsri": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "host": {"required": False, "type": "str"},
                "id": {"required": True, "type": "int"},
                "interface": {"required": False, "type": "str"},
                "ips-dos-status": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "ips-sensor": {"required": False, "type": "str"},
                "ips-sensor-status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "ipv6": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "logtraffic": {"required": False, "type": "str",
                               "choices": ["all", "utm", "disable"]},
                "max-packet-count": {"required": False, "type": "int"},
                "non-ip": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "port": {"required": False, "type": "str"},
                "protocol": {"required": False, "type": "str"},
                "scan-botnet-connections": {"required": False, "type": "str",
                                            "choices": ["disable", "block", "monitor"]},
                "spamfilter-profile": {"required": False, "type": "str"},
                "spamfilter-profile-status": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "vlan": {"required": False, "type": "str"},
                "webfilter-profile": {"required": False, "type": "str"},
                "webfilter-profile-status": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]}

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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
