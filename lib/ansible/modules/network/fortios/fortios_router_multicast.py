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
module: fortios_router_multicast
short_description: Configure router multicast in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify router feature and multicast category.
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
    router_multicast:
        description:
            - Configure router multicast.
        default: null
        suboptions:
            interface:
                description:
                    - PIM interfaces.
                suboptions:
                    bfd:
                        description:
                            - Enable/disable Protocol Independent Multicast (PIM) Bidirectional Forwarding Detection (BFD).
                        choices:
                            - enable
                            - disable
                    cisco-exclude-genid:
                        description:
                            - Exclude GenID from hello packets (compatibility with old Cisco IOS).
                        choices:
                            - enable
                            - disable
                    dr-priority:
                        description:
                            - DR election priority.
                    hello-holdtime:
                        description:
                            - Time before old neighbor information expires (0 - 65535 sec, default = 105).
                    hello-interval:
                        description:
                            - Interval between sending PIM hello messages (0 - 65535 sec, default = 30).
                    igmp:
                        description:
                            - IGMP configuration options.
                        suboptions:
                            access-group:
                                description:
                                    - Groups IGMP hosts are allowed to join. Source router.access-list.name.
                            immediate-leave-group:
                                description:
                                    - Groups to drop membership for immediately after receiving IGMPv2 leave. Source router.access-list.name.
                            last-member-query-count:
                                description:
                                    - Number of group specific queries before removing group (2 - 7, default = 2).
                            last-member-query-interval:
                                description:
                                    - Timeout between IGMPv2 leave and removing group (1 - 65535 msec, default = 1000).
                            query-interval:
                                description:
                                    - Interval between queries to IGMP hosts (1 - 65535 sec, default = 125).
                            query-max-response-time:
                                description:
                                    - Maximum time to wait for a IGMP query response (1 - 25 sec, default = 10).
                            query-timeout:
                                description:
                                    - Timeout between queries before becoming querier for network (60 - 900, default = 255).
                            router-alert-check:
                                description:
                                    - Enable/disable require IGMP packets contain router alert option.
                                choices:
                                    - enable
                                    - disable
                            version:
                                description:
                                    - Maximum version of IGMP to support.
                                choices:
                                    - 3
                                    - 2
                                    - 1
                    join-group:
                        description:
                            - Join multicast groups.
                        suboptions:
                            address:
                                description:
                                    - Multicast group IP address.
                                required: true
                    multicast-flow:
                        description:
                            - Acceptable source for multicast group. Source router.multicast-flow.name.
                    name:
                        description:
                            - Interface name. Source system.interface.name.
                        required: true
                    neighbour-filter:
                        description:
                            - Routers acknowledged as neighbor routers. Source router.access-list.name.
                    passive:
                        description:
                            - Enable/disable listening to IGMP but not participating in PIM.
                        choices:
                            - enable
                            - disable
                    pim-mode:
                        description:
                            - PIM operation mode.
                        choices:
                            - sparse-mode
                            - dense-mode
                    propagation-delay:
                        description:
                            - Delay flooding packets on this interface (100 - 5000 msec, default = 500).
                    rp-candidate:
                        description:
                            - Enable/disable compete to become RP in elections.
                        choices:
                            - enable
                            - disable
                    rp-candidate-group:
                        description:
                            - Multicast groups managed by this RP. Source router.access-list.name.
                    rp-candidate-interval:
                        description:
                            - RP candidate advertisement interval (1 - 16383 sec, default = 60).
                    rp-candidate-priority:
                        description:
                            - Router's priority as RP.
                    state-refresh-interval:
                        description:
                            - Interval between sending state-refresh packets (1 - 100 sec, default = 60).
                    static-group:
                        description:
                            - Statically set multicast groups to forward out. Source router.multicast-flow.name.
                    ttl-threshold:
                        description:
                            - Minimum TTL of multicast packets that will be forwarded (applied only to new multicast routes) (1 - 255, default = 1).
            multicast-routing:
                description:
                    - Enable/disable IP multicast routing.
                choices:
                    - enable
                    - disable
            pim-sm-global:
                description:
                    - PIM sparse-mode global settings.
                suboptions:
                    accept-register-list:
                        description:
                            - Sources allowed to register packets with this Rendezvous Point (RP). Source router.access-list.name.
                    accept-source-list:
                        description:
                            - Sources allowed to send multicast traffic. Source router.access-list.name.
                    bsr-allow-quick-refresh:
                        description:
                            - Enable/disable accept BSR quick refresh packets from neighbors.
                        choices:
                            - enable
                            - disable
                    bsr-candidate:
                        description:
                            - Enable/disable allowing this router to become a bootstrap router (BSR).
                        choices:
                            - enable
                            - disable
                    bsr-hash:
                        description:
                            - BSR hash length (0 - 32, default = 10).
                    bsr-interface:
                        description:
                            - Interface to advertise as candidate BSR. Source system.interface.name.
                    bsr-priority:
                        description:
                            - BSR priority (0 - 255, default = 0).
                    cisco-crp-prefix:
                        description:
                            - Enable/disable making candidate RP compatible with old Cisco IOS.
                        choices:
                            - enable
                            - disable
                    cisco-ignore-rp-set-priority:
                        description:
                            - Use only hash for RP selection (compatibility with old Cisco IOS).
                        choices:
                            - enable
                            - disable
                    cisco-register-checksum:
                        description:
                            - Checksum entire register packet(for old Cisco IOS compatibility).
                        choices:
                            - enable
                            - disable
                    cisco-register-checksum-group:
                        description:
                            - Cisco register checksum only these groups. Source router.access-list.name.
                    join-prune-holdtime:
                        description:
                            - Join/prune holdtime (1 - 65535, default = 210).
                    message-interval:
                        description:
                            - Period of time between sending periodic PIM join/prune messages in seconds (1 - 65535, default = 60).
                    null-register-retries:
                        description:
                            - Maximum retries of null register (1 - 20, default = 1).
                    register-rate-limit:
                        description:
                            - Limit of packets/sec per source registered through this RP (0 - 65535, default = 0 which means unlimited).
                    register-rp-reachability:
                        description:
                            - Enable/disable check RP is reachable before registering packets.
                        choices:
                            - enable
                            - disable
                    register-source:
                        description:
                            - Override source address in register packets.
                        choices:
                            - disable
                            - interface
                            - ip-address
                    register-source-interface:
                        description:
                            - Override with primary interface address. Source system.interface.name.
                    register-source-ip:
                        description:
                            - Override with local IP address.
                    register-supression:
                        description:
                            - Period of time to honor register-stop message (1 - 65535 sec, default = 60).
                    rp-address:
                        description:
                            - Statically configure RP addresses.
                        suboptions:
                            group:
                                description:
                                    - Groups to use this RP. Source router.access-list.name.
                            id:
                                description:
                                    - ID.
                                required: true
                            ip-address:
                                description:
                                    - RP router address.
                    rp-register-keepalive:
                        description:
                            - Timeout for RP receiving data on (S,G) tree (1 - 65535 sec, default = 185).
                    spt-threshold:
                        description:
                            - Enable/disable switching to source specific trees.
                        choices:
                            - enable
                            - disable
                    spt-threshold-group:
                        description:
                            - Groups allowed to switch to source tree. Source router.access-list.name.
                    ssm:
                        description:
                            - Enable/disable source specific multicast.
                        choices:
                            - enable
                            - disable
                    ssm-range:
                        description:
                            - Groups allowed to source specific multicast. Source router.access-list.name.
            route-limit:
                description:
                    - Maximum number of multicast routes.
            route-threshold:
                description:
                    - Generate warnings when the number of multicast routes exceeds this number, must not be greater than route-limit.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure router multicast.
    fortios_router_multicast:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_multicast:
        interface:
         -
            bfd: "enable"
            cisco-exclude-genid: "enable"
            dr-priority: "6"
            hello-holdtime: "7"
            hello-interval: "8"
            igmp:
                access-group: "<your_own_value> (source router.access-list.name)"
                immediate-leave-group: "<your_own_value> (source router.access-list.name)"
                last-member-query-count: "12"
                last-member-query-interval: "13"
                query-interval: "14"
                query-max-response-time: "15"
                query-timeout: "16"
                router-alert-check: "enable"
                version: "3"
            join-group:
             -
                address: "<your_own_value>"
            multicast-flow: "<your_own_value> (source router.multicast-flow.name)"
            name: "default_name_22 (source system.interface.name)"
            neighbour-filter: "<your_own_value> (source router.access-list.name)"
            passive: "enable"
            pim-mode: "sparse-mode"
            propagation-delay: "26"
            rp-candidate: "enable"
            rp-candidate-group: "<your_own_value> (source router.access-list.name)"
            rp-candidate-interval: "29"
            rp-candidate-priority: "30"
            state-refresh-interval: "31"
            static-group: "<your_own_value> (source router.multicast-flow.name)"
            ttl-threshold: "33"
        multicast-routing: "enable"
        pim-sm-global:
            accept-register-list: "<your_own_value> (source router.access-list.name)"
            accept-source-list: "<your_own_value> (source router.access-list.name)"
            bsr-allow-quick-refresh: "enable"
            bsr-candidate: "enable"
            bsr-hash: "40"
            bsr-interface: "<your_own_value> (source system.interface.name)"
            bsr-priority: "42"
            cisco-crp-prefix: "enable"
            cisco-ignore-rp-set-priority: "enable"
            cisco-register-checksum: "enable"
            cisco-register-checksum-group: "<your_own_value> (source router.access-list.name)"
            join-prune-holdtime: "47"
            message-interval: "48"
            null-register-retries: "49"
            register-rate-limit: "50"
            register-rp-reachability: "enable"
            register-source: "disable"
            register-source-interface: "<your_own_value> (source system.interface.name)"
            register-source-ip: "<your_own_value>"
            register-supression: "55"
            rp-address:
             -
                group: "<your_own_value> (source router.access-list.name)"
                id:  "58"
                ip-address: "<your_own_value>"
            rp-register-keepalive: "60"
            spt-threshold: "enable"
            spt-threshold-group: "<your_own_value> (source router.access-list.name)"
            ssm: "enable"
            ssm-range: "<your_own_value> (source router.access-list.name)"
        route-limit: "65"
        route-threshold: "66"
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


def filter_router_multicast_data(json):
    option_list = ['interface', 'multicast-routing', 'pim-sm-global',
                   'route-limit', 'route-threshold']
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


def router_multicast(data, fos):
    vdom = data['vdom']
    router_multicast_data = data['router_multicast']
    flattened_data = flatten_multilists_attributes(router_multicast_data)
    filtered_data = filter_router_multicast_data(flattened_data)
    return fos.set('router',
                   'multicast',
                   data=filtered_data,
                   vdom=vdom)


def fortios_router(data, fos):
    login(data)

    if data['router_multicast']:
        resp = router_multicast(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "router_multicast": {
            "required": False, "type": "dict",
            "options": {
                "interface": {"required": False, "type": "list",
                              "options": {
                                  "bfd": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                  "cisco-exclude-genid": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                  "dr-priority": {"required": False, "type": "int"},
                                  "hello-holdtime": {"required": False, "type": "int"},
                                  "hello-interval": {"required": False, "type": "int"},
                                  "igmp": {"required": False, "type": "dict",
                                           "options": {
                                               "access-group": {"required": False, "type": "str"},
                                               "immediate-leave-group": {"required": False, "type": "str"},
                                               "last-member-query-count": {"required": False, "type": "int"},
                                               "last-member-query-interval": {"required": False, "type": "int"},
                                               "query-interval": {"required": False, "type": "int"},
                                               "query-max-response-time": {"required": False, "type": "int"},
                                               "query-timeout": {"required": False, "type": "int"},
                                               "router-alert-check": {"required": False, "type": "str",
                                                                      "choices": ["enable", "disable"]},
                                               "version": {"required": False, "type": "str",
                                                           "choices": ["3", "2", "1"]}
                                           }},
                                  "join-group": {"required": False, "type": "list",
                                                 "options": {
                                                     "address": {"required": True, "type": "str"}
                                                 }},
                                  "multicast-flow": {"required": False, "type": "str"},
                                  "name": {"required": True, "type": "str"},
                                  "neighbour-filter": {"required": False, "type": "str"},
                                  "passive": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                  "pim-mode": {"required": False, "type": "str",
                                               "choices": ["sparse-mode", "dense-mode"]},
                                  "propagation-delay": {"required": False, "type": "int"},
                                  "rp-candidate": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                  "rp-candidate-group": {"required": False, "type": "str"},
                                  "rp-candidate-interval": {"required": False, "type": "int"},
                                  "rp-candidate-priority": {"required": False, "type": "int"},
                                  "state-refresh-interval": {"required": False, "type": "int"},
                                  "static-group": {"required": False, "type": "str"},
                                  "ttl-threshold": {"required": False, "type": "int"}
                              }},
                "multicast-routing": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "pim-sm-global": {"required": False, "type": "dict",
                                  "options": {
                                      "accept-register-list": {"required": False, "type": "str"},
                                      "accept-source-list": {"required": False, "type": "str"},
                                      "bsr-allow-quick-refresh": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                      "bsr-candidate": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                      "bsr-hash": {"required": False, "type": "int"},
                                      "bsr-interface": {"required": False, "type": "str"},
                                      "bsr-priority": {"required": False, "type": "int"},
                                      "cisco-crp-prefix": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                      "cisco-ignore-rp-set-priority": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                      "cisco-register-checksum": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                      "cisco-register-checksum-group": {"required": False, "type": "str"},
                                      "join-prune-holdtime": {"required": False, "type": "int"},
                                      "message-interval": {"required": False, "type": "int"},
                                      "null-register-retries": {"required": False, "type": "int"},
                                      "register-rate-limit": {"required": False, "type": "int"},
                                      "register-rp-reachability": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                      "register-source": {"required": False, "type": "str",
                                                          "choices": ["disable", "interface", "ip-address"]},
                                      "register-source-interface": {"required": False, "type": "str"},
                                      "register-source-ip": {"required": False, "type": "str"},
                                      "register-supression": {"required": False, "type": "int"},
                                      "rp-address": {"required": False, "type": "list",
                                                     "options": {
                                                         "group": {"required": False, "type": "str"},
                                                         "id": {"required": True, "type": "int"},
                                                         "ip-address": {"required": False, "type": "str"}
                                                     }},
                                      "rp-register-keepalive": {"required": False, "type": "int"},
                                      "spt-threshold": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                      "spt-threshold-group": {"required": False, "type": "str"},
                                      "ssm": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                      "ssm-range": {"required": False, "type": "str"}
                                  }},
                "route-limit": {"required": False, "type": "int"},
                "route-threshold": {"required": False, "type": "int"}

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
