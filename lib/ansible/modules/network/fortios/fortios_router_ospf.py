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
module: fortios_router_ospf
short_description: Configure OSPF in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify router feature and ospf category.
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
    router_ospf:
        description:
            - Configure OSPF.
        default: null
        type: dict
        suboptions:
            abr_type:
                description:
                    - Area border router type.
                type: str
                choices:
                    - cisco
                    - ibm
                    - shortcut
                    - standard
            area:
                description:
                    - OSPF area configuration.
                type: list
                suboptions:
                    authentication:
                        description:
                            - Authentication type.
                        type: str
                        choices:
                            - none
                            - text
                            - md5
                    default_cost:
                        description:
                            - Summary default cost of stub or NSSA area.
                        type: int
                    filter_list:
                        description:
                            - OSPF area filter-list configuration.
                        type: list
                        suboptions:
                            direction:
                                description:
                                    - Direction.
                                type: str
                                choices:
                                    - in
                                    - out
                            id:
                                description:
                                    - Filter list entry ID.
                                required: true
                                type: int
                            list:
                                description:
                                    - Access-list or prefix-list name. Source router.access-list.name router.prefix-list.name.
                                type: str
                    id:
                        description:
                            - Area entry IP address.
                        required: true
                        type: str
                    nssa_default_information_originate:
                        description:
                            - Redistribute, advertise, or do not originate Type-7 default route into NSSA area.
                        type: str
                        choices:
                            - enable
                            - always
                            - disable
                    nssa_default_information_originate_metric:
                        description:
                            - OSPF default metric.
                        type: int
                    nssa_default_information_originate_metric_type:
                        description:
                            - OSPF metric type for default routes.
                        type: str
                        choices:
                            - 1
                            - 2
                    nssa_redistribution:
                        description:
                            - Enable/disable redistribute into NSSA area.
                        type: str
                        choices:
                            - enable
                            - disable
                    nssa_translator_role:
                        description:
                            - NSSA translator role type.
                        type: str
                        choices:
                            - candidate
                            - never
                            - always
                    range:
                        description:
                            - OSPF area range configuration.
                        type: list
                        suboptions:
                            advertise:
                                description:
                                    - Enable/disable advertise status.
                                type: str
                                choices:
                                    - disable
                                    - enable
                            id:
                                description:
                                    - Range entry ID.
                                required: true
                                type: int
                            prefix:
                                description:
                                    - Prefix.
                                type: str
                            substitute:
                                description:
                                    - Substitute prefix.
                                type: str
                            substitute_status:
                                description:
                                    - Enable/disable substitute status.
                                type: str
                                choices:
                                    - enable
                                    - disable
                    shortcut:
                        description:
                            - Enable/disable shortcut option.
                        type: str
                        choices:
                            - disable
                            - enable
                            - default
                    stub_type:
                        description:
                            - Stub summary setting.
                        type: str
                        choices:
                            - no-summary
                            - summary
                    type:
                        description:
                            - Area type setting.
                        type: str
                        choices:
                            - regular
                            - nssa
                            - stub
                    virtual_link:
                        description:
                            - OSPF virtual link configuration.
                        type: list
                        suboptions:
                            authentication:
                                description:
                                    - Authentication type.
                                type: str
                                choices:
                                    - none
                                    - text
                                    - md5
                            authentication_key:
                                description:
                                    - Authentication key.
                                type: str
                            dead_interval:
                                description:
                                    - Dead interval.
                                type: int
                            hello_interval:
                                description:
                                    - Hello interval.
                                type: int
                            md5_key:
                                description:
                                    - MD5 key.
                                type: str
                            name:
                                description:
                                    - Virtual link entry name.
                                required: true
                                type: str
                            peer:
                                description:
                                    - Peer IP.
                                type: str
                            retransmit_interval:
                                description:
                                    - Retransmit interval.
                                type: int
                            transmit_delay:
                                description:
                                    - Transmit delay.
                                type: int
            auto_cost_ref_bandwidth:
                description:
                    - Reference bandwidth in terms of megabits per second.
                type: int
            bfd:
                description:
                    - Bidirectional Forwarding Detection (BFD).
                type: str
                choices:
                    - enable
                    - disable
            database_overflow:
                description:
                    - Enable/disable database overflow.
                type: str
                choices:
                    - enable
                    - disable
            database_overflow_max_lsas:
                description:
                    - Database overflow maximum LSAs.
                type: int
            database_overflow_time_to_recover:
                description:
                    - Database overflow time to recover (sec).
                type: int
            default_information_metric:
                description:
                    - Default information metric.
                type: int
            default_information_metric_type:
                description:
                    - Default information metric type.
                type: str
                choices:
                    - 1
                    - 2
            default_information_originate:
                description:
                    - Enable/disable generation of default route.
                type: str
                choices:
                    - enable
                    - always
                    - disable
            default_information_route_map:
                description:
                    - Default information route map. Source router.route-map.name.
                type: str
            default_metric:
                description:
                    - Default metric of redistribute routes.
                type: int
            distance:
                description:
                    - Distance of the route.
                type: int
            distance_external:
                description:
                    - Administrative external distance.
                type: int
            distance_inter_area:
                description:
                    - Administrative inter-area distance.
                type: int
            distance_intra_area:
                description:
                    - Administrative intra-area distance.
                type: int
            distribute_list:
                description:
                    - Distribute list configuration.
                type: list
                suboptions:
                    access_list:
                        description:
                            - Access list name. Source router.access-list.name.
                        type: str
                    id:
                        description:
                            - Distribute list entry ID.
                        required: true
                        type: int
                    protocol:
                        description:
                            - Protocol type.
                        type: str
                        choices:
                            - connected
                            - static
                            - rip
            distribute_list_in:
                description:
                    - Filter incoming routes. Source router.access-list.name router.prefix-list.name.
                type: str
            distribute_route_map_in:
                description:
                    - Filter incoming external routes by route-map. Source router.route-map.name.
                type: str
            log_neighbour_changes:
                description:
                    - Enable logging of OSPF neighbour's changes
                type: str
                choices:
                    - enable
                    - disable
            neighbor:
                description:
                    - OSPF neighbor configuration are used when OSPF runs on non-broadcast media
                type: list
                suboptions:
                    cost:
                        description:
                            - Cost of the interface, value range from 0 to 65535, 0 means auto-cost.
                        type: int
                    id:
                        description:
                            - Neighbor entry ID.
                        required: true
                        type: int
                    ip:
                        description:
                            - Interface IP address of the neighbor.
                        type: str
                    poll_interval:
                        description:
                            - Poll interval time in seconds.
                        type: int
                    priority:
                        description:
                            - Priority.
                        type: int
            network:
                description:
                    - OSPF network configuration.
                type: list
                suboptions:
                    area:
                        description:
                            - Attach the network to area.
                        type: str
                    id:
                        description:
                            - Network entry ID.
                        required: true
                        type: int
                    prefix:
                        description:
                            - Prefix.
                        type: str
            ospf_interface:
                description:
                    - OSPF interface configuration.
                type: list
                suboptions:
                    authentication:
                        description:
                            - Authentication type.
                        type: str
                        choices:
                            - none
                            - text
                            - md5
                    authentication_key:
                        description:
                            - Authentication key.
                        type: str
                    bfd:
                        description:
                            - Bidirectional Forwarding Detection (BFD).
                        type: str
                        choices:
                            - global
                            - enable
                            - disable
                    cost:
                        description:
                            - Cost of the interface, value range from 0 to 65535, 0 means auto-cost.
                        type: int
                    database_filter_out:
                        description:
                            - Enable/disable control of flooding out LSAs.
                        type: str
                        choices:
                            - enable
                            - disable
                    dead_interval:
                        description:
                            - Dead interval.
                        type: int
                    hello_interval:
                        description:
                            - Hello interval.
                        type: int
                    hello_multiplier:
                        description:
                            - Number of hello packets within dead interval.
                        type: int
                    interface:
                        description:
                            - Configuration interface name. Source system.interface.name.
                        type: str
                    ip:
                        description:
                            - IP address.
                        type: str
                    md5_key:
                        description:
                            - MD5 key.
                        type: str
                    mtu:
                        description:
                            - MTU for database description packets.
                        type: int
                    mtu_ignore:
                        description:
                            - Enable/disable ignore MTU.
                        type: str
                        choices:
                            - enable
                            - disable
                    name:
                        description:
                            - Interface entry name.
                        required: true
                        type: str
                    network_type:
                        description:
                            - Network type.
                        type: str
                        choices:
                            - broadcast
                            - non-broadcast
                            - point-to-point
                            - point-to-multipoint
                            - point-to-multipoint-non-broadcast
                    prefix_length:
                        description:
                            - Prefix length.
                        type: int
                    priority:
                        description:
                            - Priority.
                        type: int
                    resync_timeout:
                        description:
                            - Graceful restart neighbor resynchronization timeout.
                        type: int
                    retransmit_interval:
                        description:
                            - Retransmit interval.
                        type: int
                    status:
                        description:
                            - Enable/disable status.
                        type: str
                        choices:
                            - disable
                            - enable
                    transmit_delay:
                        description:
                            - Transmit delay.
                        type: int
            passive_interface:
                description:
                    - Passive interface configuration.
                type: list
                suboptions:
                    name:
                        description:
                            - Passive interface name. Source system.interface.name.
                        required: true
                        type: str
            redistribute:
                description:
                    - Redistribute configuration.
                type: list
                suboptions:
                    metric:
                        description:
                            - Redistribute metric setting.
                        type: int
                    metric_type:
                        description:
                            - Metric type.
                        type: str
                        choices:
                            - 1
                            - 2
                    name:
                        description:
                            - Redistribute name.
                        required: true
                        type: str
                    routemap:
                        description:
                            - Route map name. Source router.route-map.name.
                        type: str
                    status:
                        description:
                            - status
                        type: str
                        choices:
                            - enable
                            - disable
                    tag:
                        description:
                            - Tag value.
                        type: int
            restart_mode:
                description:
                    - OSPF restart mode (graceful or LLS).
                type: str
                choices:
                    - none
                    - lls
                    - graceful-restart
            restart_period:
                description:
                    - Graceful restart period.
                type: int
            rfc1583_compatible:
                description:
                    - Enable/disable RFC1583 compatibility.
                type: str
                choices:
                    - enable
                    - disable
            router_id:
                description:
                    - Router ID.
                type: str
            spf_timers:
                description:
                    - SPF calculation frequency.
                type: str
            summary_address:
                description:
                    - IP address summary configuration.
                type: list
                suboptions:
                    advertise:
                        description:
                            - Enable/disable advertise status.
                        type: str
                        choices:
                            - disable
                            - enable
                    id:
                        description:
                            - Summary address entry ID.
                        required: true
                        type: int
                    prefix:
                        description:
                            - Prefix.
                        type: str
                    tag:
                        description:
                            - Tag value.
                        type: int
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
  - name: Configure OSPF.
    fortios_router_ospf:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_ospf:
        abr_type: "cisco"
        area:
         -
            authentication: "none"
            default_cost: "6"
            filter_list:
             -
                direction: "in"
                id:  "9"
                list: "<your_own_value> (source router.access-list.name router.prefix-list.name)"
            id:  "11"
            nssa_default_information_originate: "enable"
            nssa_default_information_originate_metric: "13"
            nssa_default_information_originate_metric_type: "1"
            nssa_redistribution: "enable"
            nssa_translator_role: "candidate"
            range:
             -
                advertise: "disable"
                id:  "19"
                prefix: "<your_own_value>"
                substitute: "<your_own_value>"
                substitute_status: "enable"
            shortcut: "disable"
            stub_type: "no-summary"
            type: "regular"
            virtual_link:
             -
                authentication: "none"
                authentication_key: "<your_own_value>"
                dead_interval: "29"
                hello_interval: "30"
                md5_key: "<your_own_value>"
                name: "default_name_32"
                peer: "<your_own_value>"
                retransmit_interval: "34"
                transmit_delay: "35"
        auto_cost_ref_bandwidth: "36"
        bfd: "enable"
        database_overflow: "enable"
        database_overflow_max_lsas: "39"
        database_overflow_time_to_recover: "40"
        default_information_metric: "41"
        default_information_metric_type: "1"
        default_information_originate: "enable"
        default_information_route_map: "<your_own_value> (source router.route-map.name)"
        default_metric: "45"
        distance: "46"
        distance_external: "47"
        distance_inter_area: "48"
        distance_intra_area: "49"
        distribute_list:
         -
            access_list: "<your_own_value> (source router.access-list.name)"
            id:  "52"
            protocol: "connected"
        distribute_list_in: "<your_own_value> (source router.access-list.name router.prefix-list.name)"
        distribute_route_map_in: "<your_own_value> (source router.route-map.name)"
        log_neighbour_changes: "enable"
        neighbor:
         -
            cost: "58"
            id:  "59"
            ip: "<your_own_value>"
            poll_interval: "61"
            priority: "62"
        network:
         -
            area: "<your_own_value>"
            id:  "65"
            prefix: "<your_own_value>"
        ospf_interface:
         -
            authentication: "none"
            authentication_key: "<your_own_value>"
            bfd: "global"
            cost: "71"
            database_filter_out: "enable"
            dead_interval: "73"
            hello_interval: "74"
            hello_multiplier: "75"
            interface: "<your_own_value> (source system.interface.name)"
            ip: "<your_own_value>"
            md5_key: "<your_own_value>"
            mtu: "79"
            mtu_ignore: "enable"
            name: "default_name_81"
            network_type: "broadcast"
            prefix_length: "83"
            priority: "84"
            resync_timeout: "85"
            retransmit_interval: "86"
            status: "disable"
            transmit_delay: "88"
        passive_interface:
         -
            name: "default_name_90 (source system.interface.name)"
        redistribute:
         -
            metric: "92"
            metric_type: "1"
            name: "default_name_94"
            routemap: "<your_own_value> (source router.route-map.name)"
            status: "enable"
            tag: "97"
        restart_mode: "none"
        restart_period: "99"
        rfc1583_compatible: "enable"
        router_id: "<your_own_value>"
        spf_timers: "<your_own_value>"
        summary_address:
         -
            advertise: "disable"
            id:  "105"
            prefix: "<your_own_value>"
            tag: "107"
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


def filter_router_ospf_data(json):
    option_list = ['abr_type', 'area', 'auto_cost_ref_bandwidth',
                   'bfd', 'database_overflow', 'database_overflow_max_lsas',
                   'database_overflow_time_to_recover', 'default_information_metric', 'default_information_metric_type',
                   'default_information_originate', 'default_information_route_map', 'default_metric',
                   'distance', 'distance_external', 'distance_inter_area',
                   'distance_intra_area', 'distribute_list', 'distribute_list_in',
                   'distribute_route_map_in', 'log_neighbour_changes', 'neighbor',
                   'network', 'ospf_interface', 'passive_interface',
                   'redistribute', 'restart_mode', 'restart_period',
                   'rfc1583_compatible', 'router_id', 'spf_timers',
                   'summary_address']
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


def router_ospf(data, fos):
    vdom = data['vdom']
    router_ospf_data = data['router_ospf']
    filtered_data = underscore_to_hyphen(filter_router_ospf_data(router_ospf_data))

    return fos.set('router',
                   'ospf',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_router(data, fos):

    if data['router_ospf']:
        resp = router_ospf(data, fos)

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
        "router_ospf": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "abr_type": {"required": False, "type": "str",
                             "choices": ["cisco", "ibm", "shortcut",
                                         "standard"]},
                "area": {"required": False, "type": "list",
                         "options": {
                             "authentication": {"required": False, "type": "str",
                                                "choices": ["none", "text", "md5"]},
                             "default_cost": {"required": False, "type": "int"},
                             "filter_list": {"required": False, "type": "list",
                                             "options": {
                                                 "direction": {"required": False, "type": "str",
                                                               "choices": ["in", "out"]},
                                                 "id": {"required": True, "type": "int"},
                                                 "list": {"required": False, "type": "str"}
                                             }},
                             "id": {"required": True, "type": "str"},
                             "nssa_default_information_originate": {"required": False, "type": "str",
                                                                    "choices": ["enable", "always", "disable"]},
                             "nssa_default_information_originate_metric": {"required": False, "type": "int"},
                             "nssa_default_information_originate_metric_type": {"required": False, "type": "str",
                                                                                "choices": ["1", "2"]},
                             "nssa_redistribution": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                             "nssa_translator_role": {"required": False, "type": "str",
                                                      "choices": ["candidate", "never", "always"]},
                             "range": {"required": False, "type": "list",
                                       "options": {
                                           "advertise": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                           "id": {"required": True, "type": "int"},
                                           "prefix": {"required": False, "type": "str"},
                                           "substitute": {"required": False, "type": "str"},
                                           "substitute_status": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]}
                                       }},
                             "shortcut": {"required": False, "type": "str",
                                          "choices": ["disable", "enable", "default"]},
                             "stub_type": {"required": False, "type": "str",
                                           "choices": ["no-summary", "summary"]},
                             "type": {"required": False, "type": "str",
                                      "choices": ["regular", "nssa", "stub"]},
                             "virtual_link": {"required": False, "type": "list",
                                              "options": {
                                                  "authentication": {"required": False, "type": "str",
                                                                     "choices": ["none", "text", "md5"]},
                                                  "authentication_key": {"required": False, "type": "str", "no_log": True},
                                                  "dead_interval": {"required": False, "type": "int"},
                                                  "hello_interval": {"required": False, "type": "int"},
                                                  "md5_key": {"required": False, "type": "str", "no_log": True},
                                                  "name": {"required": True, "type": "str"},
                                                  "peer": {"required": False, "type": "str"},
                                                  "retransmit_interval": {"required": False, "type": "int"},
                                                  "transmit_delay": {"required": False, "type": "int"}
                                              }}
                         }},
                "auto_cost_ref_bandwidth": {"required": False, "type": "int"},
                "bfd": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "database_overflow": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "database_overflow_max_lsas": {"required": False, "type": "int"},
                "database_overflow_time_to_recover": {"required": False, "type": "int"},
                "default_information_metric": {"required": False, "type": "int"},
                "default_information_metric_type": {"required": False, "type": "str",
                                                    "choices": ["1", "2"]},
                "default_information_originate": {"required": False, "type": "str",
                                                  "choices": ["enable", "always", "disable"]},
                "default_information_route_map": {"required": False, "type": "str"},
                "default_metric": {"required": False, "type": "int"},
                "distance": {"required": False, "type": "int"},
                "distance_external": {"required": False, "type": "int"},
                "distance_inter_area": {"required": False, "type": "int"},
                "distance_intra_area": {"required": False, "type": "int"},
                "distribute_list": {"required": False, "type": "list",
                                    "options": {
                                        "access_list": {"required": False, "type": "str"},
                                        "id": {"required": True, "type": "int"},
                                        "protocol": {"required": False, "type": "str",
                                                     "choices": ["connected", "static", "rip"]}
                                    }},
                "distribute_list_in": {"required": False, "type": "str"},
                "distribute_route_map_in": {"required": False, "type": "str"},
                "log_neighbour_changes": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "neighbor": {"required": False, "type": "list",
                             "options": {
                                 "cost": {"required": False, "type": "int"},
                                 "id": {"required": True, "type": "int"},
                                 "ip": {"required": False, "type": "str"},
                                 "poll_interval": {"required": False, "type": "int"},
                                 "priority": {"required": False, "type": "int"}
                             }},
                "network": {"required": False, "type": "list",
                            "options": {
                                "area": {"required": False, "type": "str"},
                                "id": {"required": True, "type": "int"},
                                "prefix": {"required": False, "type": "str"}
                            }},
                "ospf_interface": {"required": False, "type": "list",
                                   "options": {
                                       "authentication": {"required": False, "type": "str",
                                                          "choices": ["none", "text", "md5"]},
                                       "authentication_key": {"required": False, "type": "str", "no_log": True},
                                       "bfd": {"required": False, "type": "str",
                                               "choices": ["global", "enable", "disable"]},
                                       "cost": {"required": False, "type": "int"},
                                       "database_filter_out": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "dead_interval": {"required": False, "type": "int"},
                                       "hello_interval": {"required": False, "type": "int"},
                                       "hello_multiplier": {"required": False, "type": "int"},
                                       "interface": {"required": False, "type": "str"},
                                       "ip": {"required": False, "type": "str"},
                                       "md5_key": {"required": False, "type": "str", "no_log": True},
                                       "mtu": {"required": False, "type": "int"},
                                       "mtu_ignore": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                       "name": {"required": True, "type": "str"},
                                       "network_type": {"required": False, "type": "str",
                                                        "choices": ["broadcast", "non-broadcast", "point-to-point",
                                                                    "point-to-multipoint", "point-to-multipoint-non-broadcast"]},
                                       "prefix_length": {"required": False, "type": "int"},
                                       "priority": {"required": False, "type": "int"},
                                       "resync_timeout": {"required": False, "type": "int"},
                                       "retransmit_interval": {"required": False, "type": "int"},
                                       "status": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]},
                                       "transmit_delay": {"required": False, "type": "int"}
                                   }},
                "passive_interface": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "redistribute": {"required": False, "type": "list",
                                 "options": {
                                     "metric": {"required": False, "type": "int"},
                                     "metric_type": {"required": False, "type": "str",
                                                     "choices": ["1", "2"]},
                                     "name": {"required": True, "type": "str"},
                                     "routemap": {"required": False, "type": "str"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                                     "tag": {"required": False, "type": "int"}
                                 }},
                "restart_mode": {"required": False, "type": "str",
                                 "choices": ["none", "lls", "graceful-restart"]},
                "restart_period": {"required": False, "type": "int"},
                "rfc1583_compatible": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "router_id": {"required": False, "type": "str"},
                "spf_timers": {"required": False, "type": "str"},
                "summary_address": {"required": False, "type": "list",
                                    "options": {
                                        "advertise": {"required": False, "type": "str",
                                                      "choices": ["disable", "enable"]},
                                        "id": {"required": True, "type": "int"},
                                        "prefix": {"required": False, "type": "str"},
                                        "tag": {"required": False, "type": "int"}
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
