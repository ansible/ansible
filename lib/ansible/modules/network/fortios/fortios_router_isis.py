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
module: fortios_router_isis
short_description: Configure IS-IS in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify router feature and isis category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.9"
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
    router_isis:
        description:
            - Configure IS-IS.
        default: null
        type: dict
        suboptions:
            adjacency_check:
                description:
                    - Enable/disable adjacency check.
                type: str
                choices:
                    - enable
                    - disable
            adjacency_check6:
                description:
                    - Enable/disable IPv6 adjacency check.
                type: str
                choices:
                    - enable
                    - disable
            adv_passive_only:
                description:
                    - Enable/disable IS-IS advertisement of passive interfaces only.
                type: str
                choices:
                    - enable
                    - disable
            adv_passive_only6:
                description:
                    - Enable/disable IPv6 IS-IS advertisement of passive interfaces only.
                type: str
                choices:
                    - enable
                    - disable
            auth_keychain_l1:
                description:
                    - Authentication key-chain for level 1 PDUs. Source router.key-chain.name.
                type: str
            auth_keychain_l2:
                description:
                    - Authentication key-chain for level 2 PDUs. Source router.key-chain.name.
                type: str
            auth_mode_l1:
                description:
                    - Level 1 authentication mode.
                type: str
                choices:
                    - password
                    - md5
            auth_mode_l2:
                description:
                    - Level 2 authentication mode.
                type: str
                choices:
                    - password
                    - md5
            auth_password_l1:
                description:
                    - Authentication password for level 1 PDUs.
                type: str
            auth_password_l2:
                description:
                    - Authentication password for level 2 PDUs.
                type: str
            auth_sendonly_l1:
                description:
                    - Enable/disable level 1 authentication send-only.
                type: str
                choices:
                    - enable
                    - disable
            auth_sendonly_l2:
                description:
                    - Enable/disable level 2 authentication send-only.
                type: str
                choices:
                    - enable
                    - disable
            default_originate:
                description:
                    - Enable/disable distribution of default route information.
                type: str
                choices:
                    - enable
                    - disable
            default_originate6:
                description:
                    - Enable/disable distribution of default IPv6 route information.
                type: str
                choices:
                    - enable
                    - disable
            dynamic_hostname:
                description:
                    - Enable/disable dynamic hostname.
                type: str
                choices:
                    - enable
                    - disable
            ignore_lsp_errors:
                description:
                    - Enable/disable ignoring of LSP errors with bad checksums.
                type: str
                choices:
                    - enable
                    - disable
            is_type:
                description:
                    - IS type.
                type: str
                choices:
                    - level-1-2
                    - level-1
                    - level-2-only
            isis_interface:
                description:
                    - IS-IS interface configuration.
                type: list
                suboptions:
                    auth_keychain_l1:
                        description:
                            - Authentication key-chain for level 1 PDUs. Source router.key-chain.name.
                        type: str
                    auth_keychain_l2:
                        description:
                            - Authentication key-chain for level 2 PDUs. Source router.key-chain.name.
                        type: str
                    auth_mode_l1:
                        description:
                            - Level 1 authentication mode.
                        type: str
                        choices:
                            - md5
                            - password
                    auth_mode_l2:
                        description:
                            - Level 2 authentication mode.
                        type: str
                        choices:
                            - md5
                            - password
                    auth_password_l1:
                        description:
                            - Authentication password for level 1 PDUs.
                        type: str
                    auth_password_l2:
                        description:
                            - Authentication password for level 2 PDUs.
                        type: str
                    auth_send_only_l1:
                        description:
                            - Enable/disable authentication send-only for level 1 PDUs.
                        type: str
                        choices:
                            - enable
                            - disable
                    auth_send_only_l2:
                        description:
                            - Enable/disable authentication send-only for level 2 PDUs.
                        type: str
                        choices:
                            - enable
                            - disable
                    circuit_type:
                        description:
                            - IS-IS interface's circuit type
                        type: str
                        choices:
                            - level-1-2
                            - level-1
                            - level-2
                    csnp_interval_l1:
                        description:
                            - Level 1 CSNP interval.
                        type: int
                    csnp_interval_l2:
                        description:
                            - Level 2 CSNP interval.
                        type: int
                    hello_interval_l1:
                        description:
                            - Level 1 hello interval.
                        type: int
                    hello_interval_l2:
                        description:
                            - Level 2 hello interval.
                        type: int
                    hello_multiplier_l1:
                        description:
                            - Level 1 multiplier for Hello holding time.
                        type: int
                    hello_multiplier_l2:
                        description:
                            - Level 2 multiplier for Hello holding time.
                        type: int
                    hello_padding:
                        description:
                            - Enable/disable padding to IS-IS hello packets.
                        type: str
                        choices:
                            - enable
                            - disable
                    lsp_interval:
                        description:
                            - LSP transmission interval (milliseconds).
                        type: int
                    lsp_retransmit_interval:
                        description:
                            - LSP retransmission interval (sec).
                        type: int
                    mesh_group:
                        description:
                            - Enable/disable IS-IS mesh group.
                        type: str
                        choices:
                            - enable
                            - disable
                    mesh_group_id:
                        description:
                            - "Mesh group ID <0-4294967295>, 0: mesh-group blocked."
                        type: int
                    metric_l1:
                        description:
                            - Level 1 metric for interface.
                        type: int
                    metric_l2:
                        description:
                            - Level 2 metric for interface.
                        type: int
                    name:
                        description:
                            - IS-IS interface name. Source system.interface.name.
                        required: true
                        type: str
                    network_type:
                        description:
                            - IS-IS interface's network type
                        type: str
                        choices:
                            - broadcast
                            - point-to-point
                            - loopback
                    priority_l1:
                        description:
                            - Level 1 priority.
                        type: int
                    priority_l2:
                        description:
                            - Level 2 priority.
                        type: int
                    status:
                        description:
                            - Enable/disable interface for IS-IS.
                        type: str
                        choices:
                            - enable
                            - disable
                    status6:
                        description:
                            - Enable/disable IPv6 interface for IS-IS.
                        type: str
                        choices:
                            - enable
                            - disable
                    wide_metric_l1:
                        description:
                            - Level 1 wide metric for interface.
                        type: int
                    wide_metric_l2:
                        description:
                            - Level 2 wide metric for interface.
                        type: int
            isis_net:
                description:
                    - IS-IS net configuration.
                type: list
                suboptions:
                    id:
                        description:
                            - isis-net ID.
                        required: true
                        type: int
                    net:
                        description:
                            - IS-IS net xx.xxxx. ... .xxxx.xx.
                        type: str
            lsp_gen_interval_l1:
                description:
                    - Minimum interval for level 1 LSP regenerating.
                type: int
            lsp_gen_interval_l2:
                description:
                    - Minimum interval for level 2 LSP regenerating.
                type: int
            lsp_refresh_interval:
                description:
                    - LSP refresh time in seconds.
                type: int
            max_lsp_lifetime:
                description:
                    - Maximum LSP lifetime in seconds.
                type: int
            metric_style:
                description:
                    - Use old-style (ISO 10589) or new-style packet formats
                type: str
                choices:
                    - narrow
                    - wide
                    - transition
                    - narrow-transition
                    - narrow-transition-l1
                    - narrow-transition-l2
                    - wide-l1
                    - wide-l2
                    - wide-transition
                    - wide-transition-l1
                    - wide-transition-l2
                    - transition-l1
                    - transition-l2
            overload_bit:
                description:
                    - Enable/disable signal other routers not to use us in SPF.
                type: str
                choices:
                    - enable
                    - disable
            overload_bit_on_startup:
                description:
                    - Overload-bit only temporarily after reboot.
                type: int
            overload_bit_suppress:
                description:
                    - Suppress overload-bit for the specific prefixes.
                type: str
                choices:
                    - external
                    - interlevel
            redistribute:
                description:
                    - IS-IS redistribute protocols.
                type: list
                suboptions:
                    level:
                        description:
                            - Level.
                        type: str
                        choices:
                            - level-1-2
                            - level-1
                            - level-2
                    metric:
                        description:
                            - Metric.
                        type: int
                    metric_type:
                        description:
                            - Metric type.
                        type: str
                        choices:
                            - external
                            - internal
                    protocol:
                        description:
                            - Protocol name.
                        required: true
                        type: str
                    routemap:
                        description:
                            - Route map name. Source router.route-map.name.
                        type: str
                    status:
                        description:
                            - Status.
                        type: str
                        choices:
                            - enable
                            - disable
            redistribute_l1:
                description:
                    - Enable/disable redistribution of level 1 routes into level 2.
                type: str
                choices:
                    - enable
                    - disable
            redistribute_l1_list:
                description:
                    - Access-list for route redistribution from l1 to l2. Source router.access-list.name.
                type: str
            redistribute_l2:
                description:
                    - Enable/disable redistribution of level 2 routes into level 1.
                type: str
                choices:
                    - enable
                    - disable
            redistribute_l2_list:
                description:
                    - Access-list for route redistribution from l2 to l1. Source router.access-list.name.
                type: str
            redistribute6:
                description:
                    - IS-IS IPv6 redistribution for routing protocols.
                type: list
                suboptions:
                    level:
                        description:
                            - Level.
                        type: str
                        choices:
                            - level-1-2
                            - level-1
                            - level-2
                    metric:
                        description:
                            - Metric.
                        type: int
                    metric_type:
                        description:
                            - Metric type.
                        type: str
                        choices:
                            - external
                            - internal
                    protocol:
                        description:
                            - Protocol name.
                        required: true
                        type: str
                    routemap:
                        description:
                            - Route map name. Source router.route-map.name.
                        type: str
                    status:
                        description:
                            - Enable/disable redistribution.
                        type: str
                        choices:
                            - enable
                            - disable
            redistribute6_l1:
                description:
                    - Enable/disable redistribution of level 1 IPv6 routes into level 2.
                type: str
                choices:
                    - enable
                    - disable
            redistribute6_l1_list:
                description:
                    - Access-list for IPv6 route redistribution from l1 to l2. Source router.access-list6.name.
                type: str
            redistribute6_l2:
                description:
                    - Enable/disable redistribution of level 2 IPv6 routes into level 1.
                type: str
                choices:
                    - enable
                    - disable
            redistribute6_l2_list:
                description:
                    - Access-list for IPv6 route redistribution from l2 to l1. Source router.access-list6.name.
                type: str
            spf_interval_exp_l1:
                description:
                    - Level 1 SPF calculation delay.
                type: str
            spf_interval_exp_l2:
                description:
                    - Level 2 SPF calculation delay.
                type: str
            summary_address:
                description:
                    - IS-IS summary addresses.
                type: list
                suboptions:
                    id:
                        description:
                            - Summary address entry ID.
                        required: true
                        type: int
                    level:
                        description:
                            - Level.
                        type: str
                        choices:
                            - level-1-2
                            - level-1
                            - level-2
                    prefix:
                        description:
                            - Prefix.
                        type: str
            summary_address6:
                description:
                    - IS-IS IPv6 summary address.
                type: list
                suboptions:
                    id:
                        description:
                            - Prefix entry ID.
                        required: true
                        type: int
                    level:
                        description:
                            - Level.
                        type: str
                        choices:
                            - level-1-2
                            - level-1
                            - level-2
                    prefix6:
                        description:
                            - IPv6 prefix.
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
  - name: Configure IS-IS.
    fortios_router_isis:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_isis:
        adjacency_check: "enable"
        adjacency_check6: "enable"
        adv_passive_only: "enable"
        adv_passive_only6: "enable"
        auth_keychain_l1: "<your_own_value> (source router.key-chain.name)"
        auth_keychain_l2: "<your_own_value> (source router.key-chain.name)"
        auth_mode_l1: "password"
        auth_mode_l2: "password"
        auth_password_l1: "<your_own_value>"
        auth_password_l2: "<your_own_value>"
        auth_sendonly_l1: "enable"
        auth_sendonly_l2: "enable"
        default_originate: "enable"
        default_originate6: "enable"
        dynamic_hostname: "enable"
        ignore_lsp_errors: "enable"
        is_type: "level-1-2"
        isis_interface:
         -
            auth_keychain_l1: "<your_own_value> (source router.key-chain.name)"
            auth_keychain_l2: "<your_own_value> (source router.key-chain.name)"
            auth_mode_l1: "md5"
            auth_mode_l2: "md5"
            auth_password_l1: "<your_own_value>"
            auth_password_l2: "<your_own_value>"
            auth_send_only_l1: "enable"
            auth_send_only_l2: "enable"
            circuit_type: "level-1-2"
            csnp_interval_l1: "30"
            csnp_interval_l2: "31"
            hello_interval_l1: "32"
            hello_interval_l2: "33"
            hello_multiplier_l1: "34"
            hello_multiplier_l2: "35"
            hello_padding: "enable"
            lsp_interval: "37"
            lsp_retransmit_interval: "38"
            mesh_group: "enable"
            mesh_group_id: "40"
            metric_l1: "41"
            metric_l2: "42"
            name: "default_name_43 (source system.interface.name)"
            network_type: "broadcast"
            priority_l1: "45"
            priority_l2: "46"
            status: "enable"
            status6: "enable"
            wide_metric_l1: "49"
            wide_metric_l2: "50"
        isis_net:
         -
            id:  "52"
            net: "<your_own_value>"
        lsp_gen_interval_l1: "54"
        lsp_gen_interval_l2: "55"
        lsp_refresh_interval: "56"
        max_lsp_lifetime: "57"
        metric_style: "narrow"
        overload_bit: "enable"
        overload_bit_on_startup: "60"
        overload_bit_suppress: "external"
        redistribute:
         -
            level: "level-1-2"
            metric: "64"
            metric_type: "external"
            protocol: "<your_own_value>"
            routemap: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        redistribute_l1: "enable"
        redistribute_l1_list: "<your_own_value> (source router.access-list.name)"
        redistribute_l2: "enable"
        redistribute_l2_list: "<your_own_value> (source router.access-list.name)"
        redistribute6:
         -
            level: "level-1-2"
            metric: "75"
            metric_type: "external"
            protocol: "<your_own_value>"
            routemap: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        redistribute6_l1: "enable"
        redistribute6_l1_list: "<your_own_value> (source router.access-list6.name)"
        redistribute6_l2: "enable"
        redistribute6_l2_list: "<your_own_value> (source router.access-list6.name)"
        spf_interval_exp_l1: "<your_own_value>"
        spf_interval_exp_l2: "<your_own_value>"
        summary_address:
         -
            id:  "87"
            level: "level-1-2"
            prefix: "<your_own_value>"
        summary_address6:
         -
            id:  "91"
            level: "level-1-2"
            prefix6: "<your_own_value>"
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


def filter_router_isis_data(json):
    option_list = ['adjacency_check', 'adjacency_check6', 'adv_passive_only',
                   'adv_passive_only6', 'auth_keychain_l1', 'auth_keychain_l2',
                   'auth_mode_l1', 'auth_mode_l2', 'auth_password_l1',
                   'auth_password_l2', 'auth_sendonly_l1', 'auth_sendonly_l2',
                   'default_originate', 'default_originate6', 'dynamic_hostname',
                   'ignore_lsp_errors', 'is_type', 'isis_interface',
                   'isis_net', 'lsp_gen_interval_l1', 'lsp_gen_interval_l2',
                   'lsp_refresh_interval', 'max_lsp_lifetime', 'metric_style',
                   'overload_bit', 'overload_bit_on_startup', 'overload_bit_suppress',
                   'redistribute', 'redistribute_l1', 'redistribute_l1_list',
                   'redistribute_l2', 'redistribute_l2_list', 'redistribute6',
                   'redistribute6_l1', 'redistribute6_l1_list', 'redistribute6_l2',
                   'redistribute6_l2_list', 'spf_interval_exp_l1', 'spf_interval_exp_l2',
                   'summary_address', 'summary_address6']
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


def router_isis(data, fos):
    vdom = data['vdom']
    router_isis_data = data['router_isis']
    filtered_data = underscore_to_hyphen(filter_router_isis_data(router_isis_data))

    return fos.set('router',
                   'isis',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_router(data, fos):

    if data['router_isis']:
        resp = router_isis(data, fos)

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
        "router_isis": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "adjacency_check": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "adjacency_check6": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "adv_passive_only": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "adv_passive_only6": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "auth_keychain_l1": {"required": False, "type": "str"},
                "auth_keychain_l2": {"required": False, "type": "str"},
                "auth_mode_l1": {"required": False, "type": "str",
                                 "choices": ["password", "md5"]},
                "auth_mode_l2": {"required": False, "type": "str",
                                 "choices": ["password", "md5"]},
                "auth_password_l1": {"required": False, "type": "str", "no_log": True},
                "auth_password_l2": {"required": False, "type": "str", "no_log": True},
                "auth_sendonly_l1": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "auth_sendonly_l2": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "default_originate": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "default_originate6": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "dynamic_hostname": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "ignore_lsp_errors": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "is_type": {"required": False, "type": "str",
                            "choices": ["level-1-2", "level-1", "level-2-only"]},
                "isis_interface": {"required": False, "type": "list",
                                   "options": {
                                       "auth_keychain_l1": {"required": False, "type": "str"},
                                       "auth_keychain_l2": {"required": False, "type": "str"},
                                       "auth_mode_l1": {"required": False, "type": "str",
                                                        "choices": ["md5", "password"]},
                                       "auth_mode_l2": {"required": False, "type": "str",
                                                        "choices": ["md5", "password"]},
                                       "auth_password_l1": {"required": False, "type": "str", "no_log": True},
                                       "auth_password_l2": {"required": False, "type": "str", "no_log": True},
                                       "auth_send_only_l1": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                       "auth_send_only_l2": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                       "circuit_type": {"required": False, "type": "str",
                                                        "choices": ["level-1-2", "level-1", "level-2"]},
                                       "csnp_interval_l1": {"required": False, "type": "int"},
                                       "csnp_interval_l2": {"required": False, "type": "int"},
                                       "hello_interval_l1": {"required": False, "type": "int"},
                                       "hello_interval_l2": {"required": False, "type": "int"},
                                       "hello_multiplier_l1": {"required": False, "type": "int"},
                                       "hello_multiplier_l2": {"required": False, "type": "int"},
                                       "hello_padding": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                       "lsp_interval": {"required": False, "type": "int"},
                                       "lsp_retransmit_interval": {"required": False, "type": "int"},
                                       "mesh_group": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                       "mesh_group_id": {"required": False, "type": "int"},
                                       "metric_l1": {"required": False, "type": "int"},
                                       "metric_l2": {"required": False, "type": "int"},
                                       "name": {"required": True, "type": "str"},
                                       "network_type": {"required": False, "type": "str",
                                                        "choices": ["broadcast", "point-to-point", "loopback"]},
                                       "priority_l1": {"required": False, "type": "int"},
                                       "priority_l2": {"required": False, "type": "int"},
                                       "status": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                       "status6": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                       "wide_metric_l1": {"required": False, "type": "int"},
                                       "wide_metric_l2": {"required": False, "type": "int"}
                                   }},
                "isis_net": {"required": False, "type": "list",
                             "options": {
                                 "id": {"required": True, "type": "int"},
                                 "net": {"required": False, "type": "str"}
                             }},
                "lsp_gen_interval_l1": {"required": False, "type": "int"},
                "lsp_gen_interval_l2": {"required": False, "type": "int"},
                "lsp_refresh_interval": {"required": False, "type": "int"},
                "max_lsp_lifetime": {"required": False, "type": "int"},
                "metric_style": {"required": False, "type": "str",
                                 "choices": ["narrow", "wide", "transition",
                                             "narrow-transition", "narrow-transition-l1", "narrow-transition-l2",
                                             "wide-l1", "wide-l2", "wide-transition",
                                             "wide-transition-l1", "wide-transition-l2", "transition-l1",
                                             "transition-l2"]},
                "overload_bit": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "overload_bit_on_startup": {"required": False, "type": "int"},
                "overload_bit_suppress": {"required": False, "type": "str",
                                          "choices": ["external", "interlevel"]},
                "redistribute": {"required": False, "type": "list",
                                 "options": {
                                     "level": {"required": False, "type": "str",
                                               "choices": ["level-1-2", "level-1", "level-2"]},
                                     "metric": {"required": False, "type": "int"},
                                     "metric_type": {"required": False, "type": "str",
                                                     "choices": ["external", "internal"]},
                                     "protocol": {"required": True, "type": "str"},
                                     "routemap": {"required": False, "type": "str"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]}
                                 }},
                "redistribute_l1": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "redistribute_l1_list": {"required": False, "type": "str"},
                "redistribute_l2": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "redistribute_l2_list": {"required": False, "type": "str"},
                "redistribute6": {"required": False, "type": "list",
                                  "options": {
                                      "level": {"required": False, "type": "str",
                                                "choices": ["level-1-2", "level-1", "level-2"]},
                                      "metric": {"required": False, "type": "int"},
                                      "metric_type": {"required": False, "type": "str",
                                                      "choices": ["external", "internal"]},
                                      "protocol": {"required": True, "type": "str"},
                                      "routemap": {"required": False, "type": "str"},
                                      "status": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]}
                                  }},
                "redistribute6_l1": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "redistribute6_l1_list": {"required": False, "type": "str"},
                "redistribute6_l2": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "redistribute6_l2_list": {"required": False, "type": "str"},
                "spf_interval_exp_l1": {"required": False, "type": "str"},
                "spf_interval_exp_l2": {"required": False, "type": "str"},
                "summary_address": {"required": False, "type": "list",
                                    "options": {
                                        "id": {"required": True, "type": "int"},
                                        "level": {"required": False, "type": "str",
                                                  "choices": ["level-1-2", "level-1", "level-2"]},
                                        "prefix": {"required": False, "type": "str"}
                                    }},
                "summary_address6": {"required": False, "type": "list",
                                     "options": {
                                         "id": {"required": True, "type": "int"},
                                         "level": {"required": False, "type": "str",
                                                   "choices": ["level-1-2", "level-1", "level-2"]},
                                         "prefix6": {"required": False, "type": "str"}
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

            is_error, has_changed, result = fortios_router(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_router(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
