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
module: fortios_router_ospf6
short_description: Configure IPv6 OSPF in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify router feature and ospf6 category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
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
        default: true
    router_ospf6:
        description:
            - Configure IPv6 OSPF.
        default: null
        suboptions:
            abr-type:
                description:
                    - Area border router type.
                choices:
                    - cisco
                    - ibm
                    - standard
            area:
                description:
                    - OSPF6 area configuration.
                suboptions:
                    default-cost:
                        description:
                            - Summary default cost of stub or NSSA area.
                    id:
                        description:
                            - Area entry IP address.
                        required: true
                    nssa-default-information-originate:
                        description:
                            - Enable/disable originate type 7 default into NSSA area.
                        choices:
                            - enable
                            - disable
                    nssa-default-information-originate-metric:
                        description:
                            - OSPFv3 default metric.
                    nssa-default-information-originate-metric-type:
                        description:
                            - OSPFv3 metric type for default routes.
                        choices:
                            - 1
                            - 2
                    nssa-redistribution:
                        description:
                            - Enable/disable redistribute into NSSA area.
                        choices:
                            - enable
                            - disable
                    nssa-translator-role:
                        description:
                            - NSSA translator role type.
                        choices:
                            - candidate
                            - never
                            - always
                    range:
                        description:
                            - OSPF6 area range configuration.
                        suboptions:
                            advertise:
                                description:
                                    - Enable/disable advertise status.
                                choices:
                                    - disable
                                    - enable
                            id:
                                description:
                                    - Range entry ID.
                                required: true
                            prefix6:
                                description:
                                    - IPv6 prefix.
                    stub-type:
                        description:
                            - Stub summary setting.
                        choices:
                            - no-summary
                            - summary
                    type:
                        description:
                            - Area type setting.
                        choices:
                            - regular
                            - nssa
                            - stub
                    virtual-link:
                        description:
                            - OSPF6 virtual link configuration.
                        suboptions:
                            dead-interval:
                                description:
                                    - Dead interval.
                            hello-interval:
                                description:
                                    - Hello interval.
                            name:
                                description:
                                    - Virtual link entry name.
                                required: true
                            peer:
                                description:
                                    - A.B.C.D, peer router ID.
                            retransmit-interval:
                                description:
                                    - Retransmit interval.
                            transmit-delay:
                                description:
                                    - Transmit delay.
            auto-cost-ref-bandwidth:
                description:
                    - Reference bandwidth in terms of megabits per second.
            bfd:
                description:
                    - Enable/disable Bidirectional Forwarding Detection (BFD).
                choices:
                    - enable
                    - disable
            default-information-metric:
                description:
                    - Default information metric.
            default-information-metric-type:
                description:
                    - Default information metric type.
                choices:
                    - 1
                    - 2
            default-information-originate:
                description:
                    - Enable/disable generation of default route.
                choices:
                    - enable
                    - always
                    - disable
            default-information-route-map:
                description:
                    - Default information route map. Source router.route-map.name.
            default-metric:
                description:
                    - Default metric of redistribute routes.
            log-neighbour-changes:
                description:
                    - Enable logging of OSPFv3 neighbour's changes
                choices:
                    - enable
                    - disable
            ospf6-interface:
                description:
                    - OSPF6 interface configuration.
                suboptions:
                    area-id:
                        description:
                            - A.B.C.D, in IPv4 address format.
                    bfd:
                        description:
                            - Enable/disable Bidirectional Forwarding Detection (BFD).
                        choices:
                            - global
                            - enable
                            - disable
                    cost:
                        description:
                            - Cost of the interface, value range from 0 to 65535, 0 means auto-cost.
                    dead-interval:
                        description:
                            - Dead interval.
                    hello-interval:
                        description:
                            - Hello interval.
                    interface:
                        description:
                            - Configuration interface name. Source system.interface.name.
                    name:
                        description:
                            - Interface entry name.
                        required: true
                    neighbor:
                        description:
                            - OSPFv3 neighbors are used when OSPFv3 runs on non-broadcast media
                        suboptions:
                            cost:
                                description:
                                    - Cost of the interface, value range from 0 to 65535, 0 means auto-cost.
                            ip6:
                                description:
                                    - IPv6 link local address of the neighbor.
                                required: true
                            poll-interval:
                                description:
                                    - Poll interval time in seconds.
                            priority:
                                description:
                                    - priority
                    network-type:
                        description:
                            - Network type.
                        choices:
                            - broadcast
                            - point-to-point
                            - non-broadcast
                            - point-to-multipoint
                            - point-to-multipoint-non-broadcast
                    priority:
                        description:
                            - priority
                    retransmit-interval:
                        description:
                            - Retransmit interval.
                    status:
                        description:
                            - Enable/disable OSPF6 routing on this interface.
                        choices:
                            - disable
                            - enable
                    transmit-delay:
                        description:
                            - Transmit delay.
            passive-interface:
                description:
                    - Passive interface configuration.
                suboptions:
                    name:
                        description:
                            - Passive interface name. Source system.interface.name.
                        required: true
            redistribute:
                description:
                    - Redistribute configuration.
                suboptions:
                    metric:
                        description:
                            - Redistribute metric setting.
                    metric-type:
                        description:
                            - Metric type.
                        choices:
                            - 1
                            - 2
                    name:
                        description:
                            - Redistribute name.
                        required: true
                    routemap:
                        description:
                            - Route map name. Source router.route-map.name.
                    status:
                        description:
                            - status
                        choices:
                            - enable
                            - disable
            router-id:
                description:
                    - A.B.C.D, in IPv4 address format.
            spf-timers:
                description:
                    - SPF calculation frequency.
            summary-address:
                description:
                    - IPv6 address summary configuration.
                suboptions:
                    advertise:
                        description:
                            - Enable/disable advertise status.
                        choices:
                            - disable
                            - enable
                    id:
                        description:
                            - Summary address entry ID.
                        required: true
                    prefix6:
                        description:
                            - IPv6 prefix.
                    tag:
                        description:
                            - Tag value.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure IPv6 OSPF.
    fortios_router_ospf6:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_ospf6:
        abr-type: "cisco"
        area:
         -
            default-cost: "5"
            id:  "6"
            nssa-default-information-originate: "enable"
            nssa-default-information-originate-metric: "8"
            nssa-default-information-originate-metric-type: "1"
            nssa-redistribution: "enable"
            nssa-translator-role: "candidate"
            range:
             -
                advertise: "disable"
                id:  "14"
                prefix6: "<your_own_value>"
            stub-type: "no-summary"
            type: "regular"
            virtual-link:
             -
                dead-interval: "19"
                hello-interval: "20"
                name: "default_name_21"
                peer: "<your_own_value>"
                retransmit-interval: "23"
                transmit-delay: "24"
        auto-cost-ref-bandwidth: "25"
        bfd: "enable"
        default-information-metric: "27"
        default-information-metric-type: "1"
        default-information-originate: "enable"
        default-information-route-map: "<your_own_value> (source router.route-map.name)"
        default-metric: "31"
        log-neighbour-changes: "enable"
        ospf6-interface:
         -
            area-id: "<your_own_value>"
            bfd: "global"
            cost: "36"
            dead-interval: "37"
            hello-interval: "38"
            interface: "<your_own_value> (source system.interface.name)"
            name: "default_name_40"
            neighbor:
             -
                cost: "42"
                ip6: "<your_own_value>"
                poll-interval: "44"
                priority: "45"
            network-type: "broadcast"
            priority: "47"
            retransmit-interval: "48"
            status: "disable"
            transmit-delay: "50"
        passive-interface:
         -
            name: "default_name_52 (source system.interface.name)"
        redistribute:
         -
            metric: "54"
            metric-type: "1"
            name: "default_name_56"
            routemap: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        router-id: "<your_own_value>"
        spf-timers: "<your_own_value>"
        summary-address:
         -
            advertise: "disable"
            id:  "63"
            prefix6: "<your_own_value>"
            tag: "65"
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


def filter_router_ospf6_data(json):
    option_list = ['abr-type', 'area', 'auto-cost-ref-bandwidth',
                   'bfd', 'default-information-metric', 'default-information-metric-type',
                   'default-information-originate', 'default-information-route-map', 'default-metric',
                   'log-neighbour-changes', 'ospf6-interface', 'passive-interface',
                   'redistribute', 'router-id', 'spf-timers',
                   'summary-address']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def router_ospf6(data, fos):
    vdom = data['vdom']
    router_ospf6_data = data['router_ospf6']
    flattened_data = flatten_multilists_attributes(router_ospf6_data)
    filtered_data = filter_router_ospf6_data(flattened_data)
    return fos.set('router',
                   'ospf6',
                   data=filtered_data,
                   vdom=vdom)


def fortios_router(data, fos):
    login(data)

    if data['router_ospf6']:
        resp = router_ospf6(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "router_ospf6": {
            "required": False, "type": "dict",
            "options": {
                "abr-type": {"required": False, "type": "str",
                             "choices": ["cisco", "ibm", "standard"]},
                "area": {"required": False, "type": "list",
                         "options": {
                             "default-cost": {"required": False, "type": "int"},
                             "id": {"required": True, "type": "str"},
                             "nssa-default-information-originate": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
                             "nssa-default-information-originate-metric": {"required": False, "type": "int"},
                             "nssa-default-information-originate-metric-type": {"required": False, "type": "str",
                                                                                "choices": ["1", "2"]},
                             "nssa-redistribution": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                             "nssa-translator-role": {"required": False, "type": "str",
                                                      "choices": ["candidate", "never", "always"]},
                             "range": {"required": False, "type": "list",
                                       "options": {
                                           "advertise": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                           "id": {"required": True, "type": "int"},
                                           "prefix6": {"required": False, "type": "str"}
                                       }},
                             "stub-type": {"required": False, "type": "str",
                                           "choices": ["no-summary", "summary"]},
                             "type": {"required": False, "type": "str",
                                      "choices": ["regular", "nssa", "stub"]},
                             "virtual-link": {"required": False, "type": "list",
                                              "options": {
                                                  "dead-interval": {"required": False, "type": "int"},
                                                  "hello-interval": {"required": False, "type": "int"},
                                                  "name": {"required": True, "type": "str"},
                                                  "peer": {"required": False, "type": "str"},
                                                  "retransmit-interval": {"required": False, "type": "int"},
                                                  "transmit-delay": {"required": False, "type": "int"}
                                              }}
                         }},
                "auto-cost-ref-bandwidth": {"required": False, "type": "int"},
                "bfd": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "default-information-metric": {"required": False, "type": "int"},
                "default-information-metric-type": {"required": False, "type": "str",
                                                    "choices": ["1", "2"]},
                "default-information-originate": {"required": False, "type": "str",
                                                  "choices": ["enable", "always", "disable"]},
                "default-information-route-map": {"required": False, "type": "str"},
                "default-metric": {"required": False, "type": "int"},
                "log-neighbour-changes": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "ospf6-interface": {"required": False, "type": "list",
                                    "options": {
                                        "area-id": {"required": False, "type": "str"},
                                        "bfd": {"required": False, "type": "str",
                                                "choices": ["global", "enable", "disable"]},
                                        "cost": {"required": False, "type": "int"},
                                        "dead-interval": {"required": False, "type": "int"},
                                        "hello-interval": {"required": False, "type": "int"},
                                        "interface": {"required": False, "type": "str"},
                                        "name": {"required": True, "type": "str"},
                                        "neighbor": {"required": False, "type": "list",
                                                     "options": {
                                                         "cost": {"required": False, "type": "int"},
                                                         "ip6": {"required": True, "type": "str"},
                                                         "poll-interval": {"required": False, "type": "int"},
                                                         "priority": {"required": False, "type": "int"}
                                                     }},
                                        "network-type": {"required": False, "type": "str",
                                                         "choices": ["broadcast", "point-to-point", "non-broadcast",
                                                                     "point-to-multipoint", "point-to-multipoint-non-broadcast"]},
                                        "priority": {"required": False, "type": "int"},
                                        "retransmit-interval": {"required": False, "type": "int"},
                                        "status": {"required": False, "type": "str",
                                                   "choices": ["disable", "enable"]},
                                        "transmit-delay": {"required": False, "type": "int"}
                                    }},
                "passive-interface": {"required": False, "type": "list",
                                      "options": {
                                          "name": {"required": True, "type": "str"}
                                      }},
                "redistribute": {"required": False, "type": "list",
                                 "options": {
                                     "metric": {"required": False, "type": "int"},
                                     "metric-type": {"required": False, "type": "str",
                                                     "choices": ["1", "2"]},
                                     "name": {"required": True, "type": "str"},
                                     "routemap": {"required": False, "type": "str"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]}
                                 }},
                "router-id": {"required": False, "type": "str"},
                "spf-timers": {"required": False, "type": "str"},
                "summary-address": {"required": False, "type": "list",
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
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_router(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
