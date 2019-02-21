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
module: fortios_router_ospf
short_description: Configure OSPF in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify router feature and ospf category.
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
    router_ospf:
        description:
            - Configure OSPF.
        default: null
        suboptions:
            abr-type:
                description:
                    - Area border router type.
                choices:
                    - cisco
                    - ibm
                    - shortcut
                    - standard
            area:
                description:
                    - OSPF area configuration.
                suboptions:
                    authentication:
                        description:
                            - Authentication type.
                        choices:
                            - none
                            - text
                            - md5
                    default-cost:
                        description:
                            - Summary default cost of stub or NSSA area.
                    filter-list:
                        description:
                            - OSPF area filter-list configuration.
                        suboptions:
                            direction:
                                description:
                                    - Direction.
                                choices:
                                    - in
                                    - out
                            id:
                                description:
                                    - Filter list entry ID.
                                required: true
                            list:
                                description:
                                    - Access-list or prefix-list name. Source router.access-list.name router.prefix-list.name.
                    id:
                        description:
                            - Area entry IP address.
                        required: true
                    nssa-default-information-originate:
                        description:
                            - Redistribute, advertise, or do not originate Type-7 default route into NSSA area.
                        choices:
                            - enable
                            - always
                            - disable
                    nssa-default-information-originate-metric:
                        description:
                            - OSPF default metric.
                    nssa-default-information-originate-metric-type:
                        description:
                            - OSPF metric type for default routes.
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
                            - OSPF area range configuration.
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
                            prefix:
                                description:
                                    - Prefix.
                            substitute:
                                description:
                                    - Substitute prefix.
                            substitute-status:
                                description:
                                    - Enable/disable substitute status.
                                choices:
                                    - enable
                                    - disable
                    shortcut:
                        description:
                            - Enable/disable shortcut option.
                        choices:
                            - disable
                            - enable
                            - default
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
                            - OSPF virtual link configuration.
                        suboptions:
                            authentication:
                                description:
                                    - Authentication type.
                                choices:
                                    - none
                                    - text
                                    - md5
                            authentication-key:
                                description:
                                    - Authentication key.
                            dead-interval:
                                description:
                                    - Dead interval.
                            hello-interval:
                                description:
                                    - Hello interval.
                            md5-key:
                                description:
                                    - MD5 key.
                            name:
                                description:
                                    - Virtual link entry name.
                                required: true
                            peer:
                                description:
                                    - Peer IP.
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
                    - Bidirectional Forwarding Detection (BFD).
                choices:
                    - enable
                    - disable
            database-overflow:
                description:
                    - Enable/disable database overflow.
                choices:
                    - enable
                    - disable
            database-overflow-max-lsas:
                description:
                    - Database overflow maximum LSAs.
            database-overflow-time-to-recover:
                description:
                    - Database overflow time to recover (sec).
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
            distance:
                description:
                    - Distance of the route.
            distance-external:
                description:
                    - Administrative external distance.
            distance-inter-area:
                description:
                    - Administrative inter-area distance.
            distance-intra-area:
                description:
                    - Administrative intra-area distance.
            distribute-list:
                description:
                    - Distribute list configuration.
                suboptions:
                    access-list:
                        description:
                            - Access list name. Source router.access-list.name.
                    id:
                        description:
                            - Distribute list entry ID.
                        required: true
                    protocol:
                        description:
                            - Protocol type.
                        choices:
                            - connected
                            - static
                            - rip
            distribute-list-in:
                description:
                    - Filter incoming routes. Source router.access-list.name router.prefix-list.name.
            distribute-route-map-in:
                description:
                    - Filter incoming external routes by route-map. Source router.route-map.name.
            log-neighbour-changes:
                description:
                    - Enable logging of OSPF neighbour's changes
                choices:
                    - enable
                    - disable
            neighbor:
                description:
                    - OSPF neighbor configuration are used when OSPF runs on non-broadcast media
                suboptions:
                    cost:
                        description:
                            - Cost of the interface, value range from 0 to 65535, 0 means auto-cost.
                    id:
                        description:
                            - Neighbor entry ID.
                        required: true
                    ip:
                        description:
                            - Interface IP address of the neighbor.
                    poll-interval:
                        description:
                            - Poll interval time in seconds.
                    priority:
                        description:
                            - Priority.
            network:
                description:
                    - OSPF network configuration.
                suboptions:
                    area:
                        description:
                            - Attach the network to area.
                    id:
                        description:
                            - Network entry ID.
                        required: true
                    prefix:
                        description:
                            - Prefix.
            ospf-interface:
                description:
                    - OSPF interface configuration.
                suboptions:
                    authentication:
                        description:
                            - Authentication type.
                        choices:
                            - none
                            - text
                            - md5
                    authentication-key:
                        description:
                            - Authentication key.
                    bfd:
                        description:
                            - Bidirectional Forwarding Detection (BFD).
                        choices:
                            - global
                            - enable
                            - disable
                    cost:
                        description:
                            - Cost of the interface, value range from 0 to 65535, 0 means auto-cost.
                    database-filter-out:
                        description:
                            - Enable/disable control of flooding out LSAs.
                        choices:
                            - enable
                            - disable
                    dead-interval:
                        description:
                            - Dead interval.
                    hello-interval:
                        description:
                            - Hello interval.
                    hello-multiplier:
                        description:
                            - Number of hello packets within dead interval.
                    interface:
                        description:
                            - Configuration interface name. Source system.interface.name.
                    ip:
                        description:
                            - IP address.
                    md5-key:
                        description:
                            - MD5 key.
                    mtu:
                        description:
                            - MTU for database description packets.
                    mtu-ignore:
                        description:
                            - Enable/disable ignore MTU.
                        choices:
                            - enable
                            - disable
                    name:
                        description:
                            - Interface entry name.
                        required: true
                    network-type:
                        description:
                            - Network type.
                        choices:
                            - broadcast
                            - non-broadcast
                            - point-to-point
                            - point-to-multipoint
                            - point-to-multipoint-non-broadcast
                    prefix-length:
                        description:
                            - Prefix length.
                    priority:
                        description:
                            - Priority.
                    resync-timeout:
                        description:
                            - Graceful restart neighbor resynchronization timeout.
                    retransmit-interval:
                        description:
                            - Retransmit interval.
                    status:
                        description:
                            - Enable/disable status.
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
                    tag:
                        description:
                            - Tag value.
            restart-mode:
                description:
                    - OSPF restart mode (graceful or LLS).
                choices:
                    - none
                    - lls
                    - graceful-restart
            restart-period:
                description:
                    - Graceful restart period.
            rfc1583-compatible:
                description:
                    - Enable/disable RFC1583 compatibility.
                choices:
                    - enable
                    - disable
            router-id:
                description:
                    - Router ID.
            spf-timers:
                description:
                    - SPF calculation frequency.
            summary-address:
                description:
                    - IP address summary configuration.
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
                    prefix:
                        description:
                            - Prefix.
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
  - name: Configure OSPF.
    fortios_router_ospf:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_ospf:
        abr-type: "cisco"
        area:
         -
            authentication: "none"
            default-cost: "6"
            filter-list:
             -
                direction: "in"
                id:  "9"
                list: "<your_own_value> (source router.access-list.name router.prefix-list.name)"
            id:  "11"
            nssa-default-information-originate: "enable"
            nssa-default-information-originate-metric: "13"
            nssa-default-information-originate-metric-type: "1"
            nssa-redistribution: "enable"
            nssa-translator-role: "candidate"
            range:
             -
                advertise: "disable"
                id:  "19"
                prefix: "<your_own_value>"
                substitute: "<your_own_value>"
                substitute-status: "enable"
            shortcut: "disable"
            stub-type: "no-summary"
            type: "regular"
            virtual-link:
             -
                authentication: "none"
                authentication-key: "<your_own_value>"
                dead-interval: "29"
                hello-interval: "30"
                md5-key: "<your_own_value>"
                name: "default_name_32"
                peer: "<your_own_value>"
                retransmit-interval: "34"
                transmit-delay: "35"
        auto-cost-ref-bandwidth: "36"
        bfd: "enable"
        database-overflow: "enable"
        database-overflow-max-lsas: "39"
        database-overflow-time-to-recover: "40"
        default-information-metric: "41"
        default-information-metric-type: "1"
        default-information-originate: "enable"
        default-information-route-map: "<your_own_value> (source router.route-map.name)"
        default-metric: "45"
        distance: "46"
        distance-external: "47"
        distance-inter-area: "48"
        distance-intra-area: "49"
        distribute-list:
         -
            access-list: "<your_own_value> (source router.access-list.name)"
            id:  "52"
            protocol: "connected"
        distribute-list-in: "<your_own_value> (source router.access-list.name router.prefix-list.name)"
        distribute-route-map-in: "<your_own_value> (source router.route-map.name)"
        log-neighbour-changes: "enable"
        neighbor:
         -
            cost: "58"
            id:  "59"
            ip: "<your_own_value>"
            poll-interval: "61"
            priority: "62"
        network:
         -
            area: "<your_own_value>"
            id:  "65"
            prefix: "<your_own_value>"
        ospf-interface:
         -
            authentication: "none"
            authentication-key: "<your_own_value>"
            bfd: "global"
            cost: "71"
            database-filter-out: "enable"
            dead-interval: "73"
            hello-interval: "74"
            hello-multiplier: "75"
            interface: "<your_own_value> (source system.interface.name)"
            ip: "<your_own_value>"
            md5-key: "<your_own_value>"
            mtu: "79"
            mtu-ignore: "enable"
            name: "default_name_81"
            network-type: "broadcast"
            prefix-length: "83"
            priority: "84"
            resync-timeout: "85"
            retransmit-interval: "86"
            status: "disable"
            transmit-delay: "88"
        passive-interface:
         -
            name: "default_name_90 (source system.interface.name)"
        redistribute:
         -
            metric: "92"
            metric-type: "1"
            name: "default_name_94"
            routemap: "<your_own_value> (source router.route-map.name)"
            status: "enable"
            tag: "97"
        restart-mode: "none"
        restart-period: "99"
        rfc1583-compatible: "enable"
        router-id: "<your_own_value>"
        spf-timers: "<your_own_value>"
        summary-address:
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


def filter_router_ospf_data(json):
    option_list = ['abr-type', 'area', 'auto-cost-ref-bandwidth',
                   'bfd', 'database-overflow', 'database-overflow-max-lsas',
                   'database-overflow-time-to-recover', 'default-information-metric', 'default-information-metric-type',
                   'default-information-originate', 'default-information-route-map', 'default-metric',
                   'distance', 'distance-external', 'distance-inter-area',
                   'distance-intra-area', 'distribute-list', 'distribute-list-in',
                   'distribute-route-map-in', 'log-neighbour-changes', 'neighbor',
                   'network', 'ospf-interface', 'passive-interface',
                   'redistribute', 'restart-mode', 'restart-period',
                   'rfc1583-compatible', 'router-id', 'spf-timers',
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


def router_ospf(data, fos):
    vdom = data['vdom']
    router_ospf_data = data['router_ospf']
    flattened_data = flatten_multilists_attributes(router_ospf_data)
    filtered_data = filter_router_ospf_data(flattened_data)
    return fos.set('router',
                   'ospf',
                   data=filtered_data,
                   vdom=vdom)


def fortios_router(data, fos):
    login(data)

    if data['router_ospf']:
        resp = router_ospf(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "router_ospf": {
            "required": False, "type": "dict",
            "options": {
                "abr-type": {"required": False, "type": "str",
                             "choices": ["cisco", "ibm", "shortcut",
                                         "standard"]},
                "area": {"required": False, "type": "list",
                         "options": {
                             "authentication": {"required": False, "type": "str",
                                                "choices": ["none", "text", "md5"]},
                             "default-cost": {"required": False, "type": "int"},
                             "filter-list": {"required": False, "type": "list",
                                             "options": {
                                                 "direction": {"required": False, "type": "str",
                                                               "choices": ["in", "out"]},
                                                 "id": {"required": True, "type": "int"},
                                                 "list": {"required": False, "type": "str"}
                                             }},
                             "id": {"required": True, "type": "str"},
                             "nssa-default-information-originate": {"required": False, "type": "str",
                                                                    "choices": ["enable", "always", "disable"]},
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
                                           "prefix": {"required": False, "type": "str"},
                                           "substitute": {"required": False, "type": "str"},
                                           "substitute-status": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]}
                                       }},
                             "shortcut": {"required": False, "type": "str",
                                          "choices": ["disable", "enable", "default"]},
                             "stub-type": {"required": False, "type": "str",
                                           "choices": ["no-summary", "summary"]},
                             "type": {"required": False, "type": "str",
                                      "choices": ["regular", "nssa", "stub"]},
                             "virtual-link": {"required": False, "type": "list",
                                              "options": {
                                                  "authentication": {"required": False, "type": "str",
                                                                     "choices": ["none", "text", "md5"]},
                                                  "authentication-key": {"required": False, "type": "str"},
                                                  "dead-interval": {"required": False, "type": "int"},
                                                  "hello-interval": {"required": False, "type": "int"},
                                                  "md5-key": {"required": False, "type": "str"},
                                                  "name": {"required": True, "type": "str"},
                                                  "peer": {"required": False, "type": "str"},
                                                  "retransmit-interval": {"required": False, "type": "int"},
                                                  "transmit-delay": {"required": False, "type": "int"}
                                              }}
                         }},
                "auto-cost-ref-bandwidth": {"required": False, "type": "int"},
                "bfd": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "database-overflow": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "database-overflow-max-lsas": {"required": False, "type": "int"},
                "database-overflow-time-to-recover": {"required": False, "type": "int"},
                "default-information-metric": {"required": False, "type": "int"},
                "default-information-metric-type": {"required": False, "type": "str",
                                                    "choices": ["1", "2"]},
                "default-information-originate": {"required": False, "type": "str",
                                                  "choices": ["enable", "always", "disable"]},
                "default-information-route-map": {"required": False, "type": "str"},
                "default-metric": {"required": False, "type": "int"},
                "distance": {"required": False, "type": "int"},
                "distance-external": {"required": False, "type": "int"},
                "distance-inter-area": {"required": False, "type": "int"},
                "distance-intra-area": {"required": False, "type": "int"},
                "distribute-list": {"required": False, "type": "list",
                                    "options": {
                                        "access-list": {"required": False, "type": "str"},
                                        "id": {"required": True, "type": "int"},
                                        "protocol": {"required": False, "type": "str",
                                                     "choices": ["connected", "static", "rip"]}
                                    }},
                "distribute-list-in": {"required": False, "type": "str"},
                "distribute-route-map-in": {"required": False, "type": "str"},
                "log-neighbour-changes": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "neighbor": {"required": False, "type": "list",
                             "options": {
                                 "cost": {"required": False, "type": "int"},
                                 "id": {"required": True, "type": "int"},
                                 "ip": {"required": False, "type": "str"},
                                 "poll-interval": {"required": False, "type": "int"},
                                 "priority": {"required": False, "type": "int"}
                             }},
                "network": {"required": False, "type": "list",
                            "options": {
                                "area": {"required": False, "type": "str"},
                                "id": {"required": True, "type": "int"},
                                "prefix": {"required": False, "type": "str"}
                            }},
                "ospf-interface": {"required": False, "type": "list",
                                   "options": {
                                       "authentication": {"required": False, "type": "str",
                                                          "choices": ["none", "text", "md5"]},
                                       "authentication-key": {"required": False, "type": "str"},
                                       "bfd": {"required": False, "type": "str",
                                               "choices": ["global", "enable", "disable"]},
                                       "cost": {"required": False, "type": "int"},
                                       "database-filter-out": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "dead-interval": {"required": False, "type": "int"},
                                       "hello-interval": {"required": False, "type": "int"},
                                       "hello-multiplier": {"required": False, "type": "int"},
                                       "interface": {"required": False, "type": "str"},
                                       "ip": {"required": False, "type": "str"},
                                       "md5-key": {"required": False, "type": "str"},
                                       "mtu": {"required": False, "type": "int"},
                                       "mtu-ignore": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                       "name": {"required": True, "type": "str"},
                                       "network-type": {"required": False, "type": "str",
                                                        "choices": ["broadcast", "non-broadcast", "point-to-point",
                                                                    "point-to-multipoint", "point-to-multipoint-non-broadcast"]},
                                       "prefix-length": {"required": False, "type": "int"},
                                       "priority": {"required": False, "type": "int"},
                                       "resync-timeout": {"required": False, "type": "int"},
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
                                                "choices": ["enable", "disable"]},
                                     "tag": {"required": False, "type": "int"}
                                 }},
                "restart-mode": {"required": False, "type": "str",
                                 "choices": ["none", "lls", "graceful-restart"]},
                "restart-period": {"required": False, "type": "int"},
                "rfc1583-compatible": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "router-id": {"required": False, "type": "str"},
                "spf-timers": {"required": False, "type": "str"},
                "summary-address": {"required": False, "type": "list",
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
