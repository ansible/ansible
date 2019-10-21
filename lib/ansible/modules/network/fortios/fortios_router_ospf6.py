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
module: fortios_router_ospf6
short_description: Configure IPv6 OSPF in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify router feature and ospf6 category.
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
    router_ospf6:
        description:
            - Configure IPv6 OSPF.
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
                    - standard
            area:
                description:
                    - OSPF6 area configuration.
                type: list
                suboptions:
                    default_cost:
                        description:
                            - Summary default cost of stub or NSSA area.
                        type: int
                    id:
                        description:
                            - Area entry IP address.
                        required: true
                        type: str
                    nssa_default_information_originate:
                        description:
                            - Enable/disable originate type 7 default into NSSA area.
                        type: str
                        choices:
                            - enable
                            - disable
                    nssa_default_information_originate_metric:
                        description:
                            - OSPFv3 default metric.
                        type: int
                    nssa_default_information_originate_metric_type:
                        description:
                            - OSPFv3 metric type for default routes.
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
                            - OSPF6 area range configuration.
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
                            prefix6:
                                description:
                                    - IPv6 prefix.
                                type: str
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
                            - OSPF6 virtual link configuration.
                        type: list
                        suboptions:
                            dead_interval:
                                description:
                                    - Dead interval.
                                type: int
                            hello_interval:
                                description:
                                    - Hello interval.
                                type: int
                            name:
                                description:
                                    - Virtual link entry name.
                                required: true
                                type: str
                            peer:
                                description:
                                    - A.B.C.D, peer router ID.
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
                    - Enable/disable Bidirectional Forwarding Detection (BFD).
                type: str
                choices:
                    - enable
                    - disable
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
            log_neighbour_changes:
                description:
                    - Enable logging of OSPFv3 neighbour's changes
                type: str
                choices:
                    - enable
                    - disable
            ospf6_interface:
                description:
                    - OSPF6 interface configuration.
                type: list
                suboptions:
                    area_id:
                        description:
                            - A.B.C.D, in IPv4 address format.
                        type: str
                    bfd:
                        description:
                            - Enable/disable Bidirectional Forwarding Detection (BFD).
                        type: str
                        choices:
                            - global
                            - enable
                            - disable
                    cost:
                        description:
                            - Cost of the interface, value range from 0 to 65535, 0 means auto-cost.
                        type: int
                    dead_interval:
                        description:
                            - Dead interval.
                        type: int
                    hello_interval:
                        description:
                            - Hello interval.
                        type: int
                    interface:
                        description:
                            - Configuration interface name. Source system.interface.name.
                        type: str
                    mtu:
                        description:
                            - MTU for OSPFv3 packets.
                        type: int
                    mtu_ignore:
                        description:
                            - Enable/disable ignoring MTU field in DBD packets.
                        type: str
                        choices:
                            - enable
                            - disable
                    name:
                        description:
                            - Interface entry name.
                        required: true
                        type: str
                    neighbor:
                        description:
                            - OSPFv3 neighbors are used when OSPFv3 runs on non-broadcast media
                        type: list
                        suboptions:
                            cost:
                                description:
                                    - Cost of the interface, value range from 0 to 65535, 0 means auto-cost.
                                type: int
                            ip6:
                                description:
                                    - IPv6 link local address of the neighbor.
                                required: true
                                type: str
                            poll_interval:
                                description:
                                    - Poll interval time in seconds.
                                type: int
                            priority:
                                description:
                                    - priority
                                type: int
                    network_type:
                        description:
                            - Network type.
                        type: str
                        choices:
                            - broadcast
                            - point-to-point
                            - non-broadcast
                            - point-to-multipoint
                            - point-to-multipoint-non-broadcast
                    priority:
                        description:
                            - priority
                        type: int
                    retransmit_interval:
                        description:
                            - Retransmit interval.
                        type: int
                    status:
                        description:
                            - Enable/disable OSPF6 routing on this interface.
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
            router_id:
                description:
                    - A.B.C.D, in IPv4 address format.
                type: str
            spf_timers:
                description:
                    - SPF calculation frequency.
                type: str
            summary_address:
                description:
                    - IPv6 address summary configuration.
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
                    prefix6:
                        description:
                            - IPv6 prefix.
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
  - name: Configure IPv6 OSPF.
    fortios_router_ospf6:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_ospf6:
        abr_type: "cisco"
        area:
         -
            default_cost: "5"
            id:  "6"
            nssa_default_information_originate: "enable"
            nssa_default_information_originate_metric: "8"
            nssa_default_information_originate_metric_type: "1"
            nssa_redistribution: "enable"
            nssa_translator_role: "candidate"
            range:
             -
                advertise: "disable"
                id:  "14"
                prefix6: "<your_own_value>"
            stub_type: "no-summary"
            type: "regular"
            virtual_link:
             -
                dead_interval: "19"
                hello_interval: "20"
                name: "default_name_21"
                peer: "<your_own_value>"
                retransmit_interval: "23"
                transmit_delay: "24"
        auto_cost_ref_bandwidth: "25"
        bfd: "enable"
        default_information_metric: "27"
        default_information_metric_type: "1"
        default_information_originate: "enable"
        default_information_route_map: "<your_own_value> (source router.route-map.name)"
        default_metric: "31"
        log_neighbour_changes: "enable"
        ospf6_interface:
         -
            area_id: "<your_own_value>"
            bfd: "global"
            cost: "36"
            dead_interval: "37"
            hello_interval: "38"
            interface: "<your_own_value> (source system.interface.name)"
            mtu: "40"
            mtu_ignore: "enable"
            name: "default_name_42"
            neighbor:
             -
                cost: "44"
                ip6: "<your_own_value>"
                poll_interval: "46"
                priority: "47"
            network_type: "broadcast"
            priority: "49"
            retransmit_interval: "50"
            status: "disable"
            transmit_delay: "52"
        passive_interface:
         -
            name: "default_name_54 (source system.interface.name)"
        redistribute:
         -
            metric: "56"
            metric_type: "1"
            name: "default_name_58"
            routemap: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        router_id: "<your_own_value>"
        spf_timers: "<your_own_value>"
        summary_address:
         -
            advertise: "disable"
            id:  "65"
            prefix6: "<your_own_value>"
            tag: "67"
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


def filter_router_ospf6_data(json):
    option_list = ['abr_type', 'area', 'auto_cost_ref_bandwidth',
                   'bfd', 'default_information_metric', 'default_information_metric_type',
                   'default_information_originate', 'default_information_route_map', 'default_metric',
                   'log_neighbour_changes', 'ospf6_interface', 'passive_interface',
                   'redistribute', 'router_id', 'spf_timers',
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


def router_ospf6(data, fos):
    vdom = data['vdom']
    router_ospf6_data = data['router_ospf6']
    filtered_data = underscore_to_hyphen(filter_router_ospf6_data(router_ospf6_data))

    return fos.set('router',
                   'ospf6',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_router(data, fos):

    if data['router_ospf6']:
        resp = router_ospf6(data, fos)

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
        "router_ospf6": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "abr_type": {"required": False, "type": "str",
                             "choices": ["cisco", "ibm", "standard"]},
                "area": {"required": False, "type": "list",
                         "options": {
                             "default_cost": {"required": False, "type": "int"},
                             "id": {"required": True, "type": "str"},
                             "nssa_default_information_originate": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
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
                                           "prefix6": {"required": False, "type": "str"}
                                       }},
                             "stub_type": {"required": False, "type": "str",
                                           "choices": ["no-summary", "summary"]},
                             "type": {"required": False, "type": "str",
                                      "choices": ["regular", "nssa", "stub"]},
                             "virtual_link": {"required": False, "type": "list",
                                              "options": {
                                                  "dead_interval": {"required": False, "type": "int"},
                                                  "hello_interval": {"required": False, "type": "int"},
                                                  "name": {"required": True, "type": "str"},
                                                  "peer": {"required": False, "type": "str"},
                                                  "retransmit_interval": {"required": False, "type": "int"},
                                                  "transmit_delay": {"required": False, "type": "int"}
                                              }}
                         }},
                "auto_cost_ref_bandwidth": {"required": False, "type": "int"},
                "bfd": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "default_information_metric": {"required": False, "type": "int"},
                "default_information_metric_type": {"required": False, "type": "str",
                                                    "choices": ["1", "2"]},
                "default_information_originate": {"required": False, "type": "str",
                                                  "choices": ["enable", "always", "disable"]},
                "default_information_route_map": {"required": False, "type": "str"},
                "default_metric": {"required": False, "type": "int"},
                "log_neighbour_changes": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "ospf6_interface": {"required": False, "type": "list",
                                    "options": {
                                        "area_id": {"required": False, "type": "str"},
                                        "bfd": {"required": False, "type": "str",
                                                "choices": ["global", "enable", "disable"]},
                                        "cost": {"required": False, "type": "int"},
                                        "dead_interval": {"required": False, "type": "int"},
                                        "hello_interval": {"required": False, "type": "int"},
                                        "interface": {"required": False, "type": "str"},
                                        "mtu": {"required": False, "type": "int"},
                                        "mtu_ignore": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                        "name": {"required": True, "type": "str"},
                                        "neighbor": {"required": False, "type": "list",
                                                     "options": {
                                                         "cost": {"required": False, "type": "int"},
                                                         "ip6": {"required": True, "type": "str"},
                                                         "poll_interval": {"required": False, "type": "int"},
                                                         "priority": {"required": False, "type": "int"}
                                                     }},
                                        "network_type": {"required": False, "type": "str",
                                                         "choices": ["broadcast", "point-to-point", "non-broadcast",
                                                                     "point-to-multipoint", "point-to-multipoint-non-broadcast"]},
                                        "priority": {"required": False, "type": "int"},
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
                                                "choices": ["enable", "disable"]}
                                 }},
                "router_id": {"required": False, "type": "str"},
                "spf_timers": {"required": False, "type": "str"},
                "summary_address": {"required": False, "type": "list",
                                    "options": {
                                        "advertise": {"required": False, "type": "str",
                                                      "choices": ["disable", "enable"]},
                                        "id": {"required": True, "type": "int"},
                                        "prefix6": {"required": False, "type": "str"},
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
