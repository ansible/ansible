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
module: fortios_log_disk_filter
short_description: Configure filters for local disk logging. Use these filters to determine the log messages to record according to severity and type in
   Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify log_disk feature and filter category.
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
    log_disk_filter:
        description:
            - Configure filters for local disk logging. Use these filters to determine the log messages to record according to severity and type.
        default: null
        type: dict
        suboptions:
            admin:
                description:
                    - Enable/disable admin login/logout logging.
                type: str
                choices:
                    - enable
                    - disable
            anomaly:
                description:
                    - Enable/disable anomaly logging.
                type: str
                choices:
                    - enable
                    - disable
            auth:
                description:
                    - Enable/disable firewall authentication logging.
                type: str
                choices:
                    - enable
                    - disable
            cpu_memory_usage:
                description:
                    - Enable/disable CPU & memory usage logging every 5 minutes.
                type: str
                choices:
                    - enable
                    - disable
            dhcp:
                description:
                    - Enable/disable DHCP service messages logging.
                type: str
                choices:
                    - enable
                    - disable
            dlp_archive:
                description:
                    - Enable/disable DLP archive logging.
                type: str
                choices:
                    - enable
                    - disable
            dns:
                description:
                    - Enable/disable detailed DNS event logging.
                type: str
                choices:
                    - enable
                    - disable
            event:
                description:
                    - Enable/disable event logging.
                type: str
                choices:
                    - enable
                    - disable
            filter:
                description:
                    - Disk log filter.
                type: str
            filter_type:
                description:
                    - Include/exclude logs that match the filter.
                type: str
                choices:
                    - include
                    - exclude
            forward_traffic:
                description:
                    - Enable/disable forward traffic logging.
                type: str
                choices:
                    - enable
                    - disable
            gtp:
                description:
                    - Enable/disable GTP messages logging.
                type: str
                choices:
                    - enable
                    - disable
            ha:
                description:
                    - Enable/disable HA logging.
                type: str
                choices:
                    - enable
                    - disable
            ipsec:
                description:
                    - Enable/disable IPsec negotiation messages logging.
                type: str
                choices:
                    - enable
                    - disable
            ldb_monitor:
                description:
                    - Enable/disable VIP real server health monitoring logging.
                type: str
                choices:
                    - enable
                    - disable
            local_traffic:
                description:
                    - Enable/disable local in or out traffic logging.
                type: str
                choices:
                    - enable
                    - disable
            multicast_traffic:
                description:
                    - Enable/disable multicast traffic logging.
                type: str
                choices:
                    - enable
                    - disable
            netscan_discovery:
                description:
                    - Enable/disable netscan discovery event logging.
                type: str
            netscan_vulnerability:
                description:
                    - Enable/disable netscan vulnerability event logging.
                type: str
            pattern:
                description:
                    - Enable/disable pattern update logging.
                type: str
                choices:
                    - enable
                    - disable
            ppp:
                description:
                    - Enable/disable L2TP/PPTP/PPPoE logging.
                type: str
                choices:
                    - enable
                    - disable
            radius:
                description:
                    - Enable/disable RADIUS messages logging.
                type: str
                choices:
                    - enable
                    - disable
            severity:
                description:
                    - Log to disk every message above and including this severity level.
                type: str
                choices:
                    - emergency
                    - alert
                    - critical
                    - error
                    - warning
                    - notification
                    - information
                    - debug
            sniffer_traffic:
                description:
                    - Enable/disable sniffer traffic logging.
                type: str
                choices:
                    - enable
                    - disable
            ssh:
                description:
                    - Enable/disable SSH logging.
                type: str
                choices:
                    - enable
                    - disable
            sslvpn_log_adm:
                description:
                    - Enable/disable SSL administrator login logging.
                type: str
                choices:
                    - enable
                    - disable
            sslvpn_log_auth:
                description:
                    - Enable/disable SSL user authentication logging.
                type: str
                choices:
                    - enable
                    - disable
            sslvpn_log_session:
                description:
                    - Enable/disable SSL session logging.
                type: str
                choices:
                    - enable
                    - disable
            system:
                description:
                    - Enable/disable system activity logging.
                type: str
                choices:
                    - enable
                    - disable
            vip_ssl:
                description:
                    - Enable/disable VIP SSL logging.
                type: str
                choices:
                    - enable
                    - disable
            voip:
                description:
                    - Enable/disable VoIP logging.
                type: str
                choices:
                    - enable
                    - disable
            wan_opt:
                description:
                    - Enable/disable WAN optimization event logging.
                type: str
                choices:
                    - enable
                    - disable
            wireless_activity:
                description:
                    - Enable/disable wireless activity event logging.
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
  - name: Configure filters for local disk logging. Use these filters to determine the log messages to record according to severity and type.
    fortios_log_disk_filter:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      log_disk_filter:
        admin: "enable"
        anomaly: "enable"
        auth: "enable"
        cpu_memory_usage: "enable"
        dhcp: "enable"
        dlp_archive: "enable"
        dns: "enable"
        event: "enable"
        filter: "<your_own_value>"
        filter_type: "include"
        forward_traffic: "enable"
        gtp: "enable"
        ha: "enable"
        ipsec: "enable"
        ldb_monitor: "enable"
        local_traffic: "enable"
        multicast_traffic: "enable"
        netscan_discovery: "<your_own_value>"
        netscan_vulnerability: "<your_own_value>"
        pattern: "enable"
        ppp: "enable"
        radius: "enable"
        severity: "emergency"
        sniffer_traffic: "enable"
        ssh: "enable"
        sslvpn_log_adm: "enable"
        sslvpn_log_auth: "enable"
        sslvpn_log_session: "enable"
        system: "enable"
        vip_ssl: "enable"
        voip: "enable"
        wan_opt: "enable"
        wireless_activity: "enable"
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


def filter_log_disk_filter_data(json):
    option_list = ['admin', 'anomaly', 'auth',
                   'cpu_memory_usage', 'dhcp', 'dlp_archive',
                   'dns', 'event', 'filter',
                   'filter_type', 'forward_traffic', 'gtp',
                   'ha', 'ipsec', 'ldb_monitor',
                   'local_traffic', 'multicast_traffic', 'netscan_discovery',
                   'netscan_vulnerability', 'pattern', 'ppp',
                   'radius', 'severity', 'sniffer_traffic',
                   'ssh', 'sslvpn_log_adm', 'sslvpn_log_auth',
                   'sslvpn_log_session', 'system', 'vip_ssl',
                   'voip', 'wan_opt', 'wireless_activity']
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


def log_disk_filter(data, fos):
    vdom = data['vdom']
    log_disk_filter_data = data['log_disk_filter']
    filtered_data = underscore_to_hyphen(filter_log_disk_filter_data(log_disk_filter_data))

    return fos.set('log.disk',
                   'filter',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_log_disk(data, fos):

    if data['log_disk_filter']:
        resp = log_disk_filter(data, fos)

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
        "log_disk_filter": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "admin": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "anomaly": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "auth": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "cpu_memory_usage": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "dhcp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "dlp_archive": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "dns": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "event": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "filter": {"required": False, "type": "str"},
                "filter_type": {"required": False, "type": "str",
                                "choices": ["include", "exclude"]},
                "forward_traffic": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "gtp": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "ha": {"required": False, "type": "str",
                       "choices": ["enable", "disable"]},
                "ipsec": {"required": False, "type": "str",
                          "choices": ["enable", "disable"]},
                "ldb_monitor": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "local_traffic": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "multicast_traffic": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "netscan_discovery": {"required": False, "type": "str"},
                "netscan_vulnerability": {"required": False, "type": "str"},
                "pattern": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "ppp": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "radius": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "severity": {"required": False, "type": "str",
                             "choices": ["emergency", "alert", "critical",
                                         "error", "warning", "notification",
                                         "information", "debug"]},
                "sniffer_traffic": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "ssh": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "sslvpn_log_adm": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "sslvpn_log_auth": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "sslvpn_log_session": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "system": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "vip_ssl": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "voip": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "wan_opt": {"required": False, "type": "str",
                            "choices": ["enable", "disable"]},
                "wireless_activity": {"required": False, "type": "str",
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

            is_error, has_changed, result = fortios_log_disk(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_log_disk(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
