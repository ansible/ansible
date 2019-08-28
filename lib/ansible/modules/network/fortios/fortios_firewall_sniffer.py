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
module: fortios_firewall_sniffer
short_description: Configure sniffer in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and sniffer category.
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
    firewall_sniffer:
        description:
            - Configure sniffer.
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
            anomaly:
                description:
                    - Configuration method to edit Denial of Service (DoS) anomaly settings.
                type: list
                suboptions:
                    action:
                        description:
                            - Action taken when the threshold is reached.
                        type: str
                        choices:
                            - pass
                            - block
                    log:
                        description:
                            - Enable/disable anomaly logging.
                        type: str
                        choices:
                            - enable
                            - disable
                    name:
                        description:
                            - Anomaly name.
                        required: true
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
                    status:
                        description:
                            - Enable/disable this anomaly.
                        type: str
                        choices:
                            - disable
                            - enable
                    threshold:
                        description:
                            - Anomaly threshold. Number of detected instances per minute that triggers the anomaly action.
                        type: int
                    threshold(default):
                        description:
                            - Number of detected instances per minute which triggers action (1 - 2147483647). Note that each anomaly has a different threshold
                               value assigned to it.
                        type: int
            application_list:
                description:
                    - Name of an existing application list. Source application.list.name.
                type: str
            application_list_status:
                description:
                    - Enable/disable application control profile.
                type: str
                choices:
                    - enable
                    - disable
            av_profile:
                description:
                    - Name of an existing antivirus profile. Source antivirus.profile.name.
                type: str
            av_profile_status:
                description:
                    - Enable/disable antivirus profile.
                type: str
                choices:
                    - enable
                    - disable
            dlp_sensor:
                description:
                    - Name of an existing DLP sensor. Source dlp.sensor.name.
                type: str
            dlp_sensor_status:
                description:
                    - Enable/disable DLP sensor.
                type: str
                choices:
                    - enable
                    - disable
            dsri:
                description:
                    - Enable/disable DSRI.
                type: str
                choices:
                    - enable
                    - disable
            host:
                description:
                    - "Hosts to filter for in sniffer traffic (Format examples: 1.1.1.1, 2.2.2.0/24, 3.3.3.3/255.255.255.0, 4.4.4.0-4.4.4.240)."
                type: str
            id:
                description:
                    - Sniffer ID.
                required: true
                type: int
            interface:
                description:
                    - Interface name that traffic sniffing will take place on. Source system.interface.name.
                type: str
            ips_dos_status:
                description:
                    - Enable/disable IPS DoS anomaly detection.
                type: str
                choices:
                    - enable
                    - disable
            ips_sensor:
                description:
                    - Name of an existing IPS sensor. Source ips.sensor.name.
                type: str
            ips_sensor_status:
                description:
                    - Enable/disable IPS sensor.
                type: str
                choices:
                    - enable
                    - disable
            ipv6:
                description:
                    - Enable/disable sniffing IPv6 packets.
                type: str
                choices:
                    - enable
                    - disable
            logtraffic:
                description:
                    - Either log all sessions, only sessions that have a security profile applied, or disable all logging for this policy.
                type: str
                choices:
                    - all
                    - utm
                    - disable
            max_packet_count:
                description:
                    - Maximum packet count (1 - 1000000).
                type: int
            non_ip:
                description:
                    - Enable/disable sniffing non-IP packets.
                type: str
                choices:
                    - enable
                    - disable
            port:
                description:
                    - "Ports to sniff (Format examples: 10, :20, 30:40, 50-, 100-200)."
                type: str
            protocol:
                description:
                    - Integer value for the protocol type as defined by IANA (0 - 255).
                type: str
            scan_botnet_connections:
                description:
                    - Enable/disable scanning of connections to Botnet servers.
                type: str
                choices:
                    - disable
                    - block
                    - monitor
            spamfilter_profile:
                description:
                    - Name of an existing spam filter profile. Source spamfilter.profile.name.
                type: str
            spamfilter_profile_status:
                description:
                    - Enable/disable spam filter.
                type: str
                choices:
                    - enable
                    - disable
            status:
                description:
                    - Enable/disable the active status of the sniffer.
                type: str
                choices:
                    - enable
                    - disable
            vlan:
                description:
                    - List of VLANs to sniff.
                type: str
            webfilter_profile:
                description:
                    - Name of an existing web filter profile. Source webfilter.profile.name.
                type: str
            webfilter_profile_status:
                description:
                    - Enable/disable web filter profile.
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
  - name: Configure sniffer.
    fortios_firewall_sniffer:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_sniffer:
        anomaly:
         -
            action: "pass"
            log: "enable"
            name: "default_name_6"
            quarantine: "none"
            quarantine_expiry: "<your_own_value>"
            quarantine_log: "disable"
            status: "disable"
            threshold: "11"
            threshold(default): "12"
        application_list: "<your_own_value> (source application.list.name)"
        application_list_status: "enable"
        av_profile: "<your_own_value> (source antivirus.profile.name)"
        av_profile_status: "enable"
        dlp_sensor: "<your_own_value> (source dlp.sensor.name)"
        dlp_sensor_status: "enable"
        dsri: "enable"
        host: "myhostname"
        id:  "21"
        interface: "<your_own_value> (source system.interface.name)"
        ips_dos_status: "enable"
        ips_sensor: "<your_own_value> (source ips.sensor.name)"
        ips_sensor_status: "enable"
        ipv6: "enable"
        logtraffic: "all"
        max_packet_count: "28"
        non_ip: "enable"
        port: "<your_own_value>"
        protocol: "<your_own_value>"
        scan_botnet_connections: "disable"
        spamfilter_profile: "<your_own_value> (source spamfilter.profile.name)"
        spamfilter_profile_status: "enable"
        status: "enable"
        vlan: "<your_own_value>"
        webfilter_profile: "<your_own_value> (source webfilter.profile.name)"
        webfilter_profile_status: "enable"
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


def filter_firewall_sniffer_data(json):
    option_list = ['anomaly', 'application_list', 'application_list_status',
                   'av_profile', 'av_profile_status', 'dlp_sensor',
                   'dlp_sensor_status', 'dsri', 'host',
                   'id', 'interface', 'ips_dos_status',
                   'ips_sensor', 'ips_sensor_status', 'ipv6',
                   'logtraffic', 'max_packet_count', 'non_ip',
                   'port', 'protocol', 'scan_botnet_connections',
                   'spamfilter_profile', 'spamfilter_profile_status', 'status',
                   'vlan', 'webfilter_profile', 'webfilter_profile_status']
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


def firewall_sniffer(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_sniffer'] and data['firewall_sniffer']:
        state = data['firewall_sniffer']['state']
    else:
        state = True
    firewall_sniffer_data = data['firewall_sniffer']
    filtered_data = underscore_to_hyphen(filter_firewall_sniffer_data(firewall_sniffer_data))

    if state == "present":
        return fos.set('firewall',
                       'sniffer',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'sniffer',
                          mkey=filtered_data['id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_sniffer']:
        resp = firewall_sniffer(data, fos)

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
        "firewall_sniffer": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
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
                                "quarantine_expiry": {"required": False, "type": "str"},
                                "quarantine_log": {"required": False, "type": "str",
                                                   "choices": ["disable", "enable"]},
                                "status": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                                "threshold": {"required": False, "type": "int"},
                                "threshold(default)": {"required": False, "type": "int"}
                            }},
                "application_list": {"required": False, "type": "str"},
                "application_list_status": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "av_profile": {"required": False, "type": "str"},
                "av_profile_status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "dlp_sensor": {"required": False, "type": "str"},
                "dlp_sensor_status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "dsri": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "host": {"required": False, "type": "str"},
                "id": {"required": True, "type": "int"},
                "interface": {"required": False, "type": "str"},
                "ips_dos_status": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "ips_sensor": {"required": False, "type": "str"},
                "ips_sensor_status": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "ipv6": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "logtraffic": {"required": False, "type": "str",
                               "choices": ["all", "utm", "disable"]},
                "max_packet_count": {"required": False, "type": "int"},
                "non_ip": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "port": {"required": False, "type": "str"},
                "protocol": {"required": False, "type": "str"},
                "scan_botnet_connections": {"required": False, "type": "str",
                                            "choices": ["disable", "block", "monitor"]},
                "spamfilter_profile": {"required": False, "type": "str"},
                "spamfilter_profile_status": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "vlan": {"required": False, "type": "str"},
                "webfilter_profile": {"required": False, "type": "str"},
                "webfilter_profile_status": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]}

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

            is_error, has_changed, result = fortios_firewall(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_firewall(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
