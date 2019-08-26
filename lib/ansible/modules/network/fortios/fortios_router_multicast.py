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
module: fortios_router_multicast
short_description: Configure router multicast in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify router feature and multicast category.
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
    router_multicast:
        description:
            - Configure router multicast.
        default: null
        type: dict
        suboptions:
            interface:
                description:
                    - PIM interfaces.
                type: list
                suboptions:
                    bfd:
                        description:
                            - Enable/disable Protocol Independent Multicast (PIM) Bidirectional Forwarding Detection (BFD).
                        type: str
                        choices:
                            - enable
                            - disable
                    cisco_exclude_genid:
                        description:
                            - Exclude GenID from hello packets (compatibility with old Cisco IOS).
                        type: str
                        choices:
                            - enable
                            - disable
                    dr_priority:
                        description:
                            - DR election priority.
                        type: int
                    hello_holdtime:
                        description:
                            - Time before old neighbor information expires (0 - 65535 sec).
                        type: int
                    hello_interval:
                        description:
                            - Interval between sending PIM hello messages (0 - 65535 sec).
                        type: int
                    igmp:
                        description:
                            - IGMP configuration options.
                        type: dict
                        suboptions:
                            access_group:
                                description:
                                    - Groups IGMP hosts are allowed to join. Source router.access-list.name.
                                type: str
                            immediate_leave_group:
                                description:
                                    - Groups to drop membership for immediately after receiving IGMPv2 leave. Source router.access-list.name.
                                type: str
                            last_member_query_count:
                                description:
                                    - Number of group specific queries before removing group (2 - 7).
                                type: int
                            last_member_query_interval:
                                description:
                                    - Timeout between IGMPv2 leave and removing group (1 - 65535 msec).
                                type: int
                            query_interval:
                                description:
                                    - Interval between queries to IGMP hosts (1 - 65535 sec).
                                type: int
                            query_max_response_time:
                                description:
                                    - Maximum time to wait for a IGMP query response (1 - 25 sec).
                                type: int
                            query_timeout:
                                description:
                                    - Timeout between queries before becoming querier for network (60 - 900).
                                type: int
                            router_alert_check:
                                description:
                                    - Enable/disable require IGMP packets contain router alert option.
                                type: str
                                choices:
                                    - enable
                                    - disable
                            version:
                                description:
                                    - Maximum version of IGMP to support.
                                type: str
                                choices:
                                    - 3
                                    - 2
                                    - 1
                    join_group:
                        description:
                            - Join multicast groups.
                        type: list
                        suboptions:
                            address:
                                description:
                                    - Multicast group IP address.
                                required: true
                                type: str
                    multicast_flow:
                        description:
                            - Acceptable source for multicast group. Source router.multicast-flow.name.
                        type: str
                    name:
                        description:
                            - Interface name. Source system.interface.name.
                        required: true
                        type: str
                    neighbour_filter:
                        description:
                            - Routers acknowledged as neighbor routers. Source router.access-list.name.
                        type: str
                    passive:
                        description:
                            - Enable/disable listening to IGMP but not participating in PIM.
                        type: str
                        choices:
                            - enable
                            - disable
                    pim_mode:
                        description:
                            - PIM operation mode.
                        type: str
                        choices:
                            - sparse-mode
                            - dense-mode
                    propagation_delay:
                        description:
                            - Delay flooding packets on this interface (100 - 5000 msec).
                        type: int
                    rp_candidate:
                        description:
                            - Enable/disable compete to become RP in elections.
                        type: str
                        choices:
                            - enable
                            - disable
                    rp_candidate_group:
                        description:
                            - Multicast groups managed by this RP. Source router.access-list.name.
                        type: str
                    rp_candidate_interval:
                        description:
                            - RP candidate advertisement interval (1 - 16383 sec).
                        type: int
                    rp_candidate_priority:
                        description:
                            - Router's priority as RP.
                        type: int
                    state_refresh_interval:
                        description:
                            - Interval between sending state-refresh packets (1 - 100 sec).
                        type: int
                    static_group:
                        description:
                            - Statically set multicast groups to forward out. Source router.multicast-flow.name.
                        type: str
                    ttl_threshold:
                        description:
                            - Minimum TTL of multicast packets that will be forwarded (applied only to new multicast routes) (1 - 255).
                        type: int
            multicast_routing:
                description:
                    - Enable/disable IP multicast routing.
                type: str
                choices:
                    - enable
                    - disable
            pim_sm_global:
                description:
                    - PIM sparse-mode global settings.
                type: dict
                suboptions:
                    accept_register_list:
                        description:
                            - Sources allowed to register packets with this Rendezvous Point (RP). Source router.access-list.name.
                        type: str
                    accept_source_list:
                        description:
                            - Sources allowed to send multicast traffic. Source router.access-list.name.
                        type: str
                    bsr_allow_quick_refresh:
                        description:
                            - Enable/disable accept BSR quick refresh packets from neighbors.
                        type: str
                        choices:
                            - enable
                            - disable
                    bsr_candidate:
                        description:
                            - Enable/disable allowing this router to become a bootstrap router (BSR).
                        type: str
                        choices:
                            - enable
                            - disable
                    bsr_hash:
                        description:
                            - BSR hash length (0 - 32).
                        type: int
                    bsr_interface:
                        description:
                            - Interface to advertise as candidate BSR. Source system.interface.name.
                        type: str
                    bsr_priority:
                        description:
                            - BSR priority (0 - 255).
                        type: int
                    cisco_crp_prefix:
                        description:
                            - Enable/disable making candidate RP compatible with old Cisco IOS.
                        type: str
                        choices:
                            - enable
                            - disable
                    cisco_ignore_rp_set_priority:
                        description:
                            - Use only hash for RP selection (compatibility with old Cisco IOS).
                        type: str
                        choices:
                            - enable
                            - disable
                    cisco_register_checksum:
                        description:
                            - Checksum entire register packet(for old Cisco IOS compatibility).
                        type: str
                        choices:
                            - enable
                            - disable
                    cisco_register_checksum_group:
                        description:
                            - Cisco register checksum only these groups. Source router.access-list.name.
                        type: str
                    join_prune_holdtime:
                        description:
                            - Join/prune holdtime (1 - 65535).
                        type: int
                    message_interval:
                        description:
                            - Period of time between sending periodic PIM join/prune messages in seconds (1 - 65535).
                        type: int
                    null_register_retries:
                        description:
                            - Maximum retries of null register (1 - 20).
                        type: int
                    register_rate_limit:
                        description:
                            - Limit of packets/sec per source registered through this RP (0 - 65535).
                        type: int
                    register_rp_reachability:
                        description:
                            - Enable/disable check RP is reachable before registering packets.
                        type: str
                        choices:
                            - enable
                            - disable
                    register_source:
                        description:
                            - Override source address in register packets.
                        type: str
                        choices:
                            - disable
                            - interface
                            - ip-address
                    register_source_interface:
                        description:
                            - Override with primary interface address. Source system.interface.name.
                        type: str
                    register_source_ip:
                        description:
                            - Override with local IP address.
                        type: str
                    register_supression:
                        description:
                            - Period of time to honor register-stop message (1 - 65535 sec).
                        type: int
                    rp_address:
                        description:
                            - Statically configure RP addresses.
                        type: list
                        suboptions:
                            group:
                                description:
                                    - Groups to use this RP. Source router.access-list.name.
                                type: str
                            id:
                                description:
                                    - ID.
                                required: true
                                type: int
                            ip_address:
                                description:
                                    - RP router address.
                                type: str
                    rp_register_keepalive:
                        description:
                            - Timeout for RP receiving data on (S,G) tree (1 - 65535 sec).
                        type: int
                    spt_threshold:
                        description:
                            - Enable/disable switching to source specific trees.
                        type: str
                        choices:
                            - enable
                            - disable
                    spt_threshold_group:
                        description:
                            - Groups allowed to switch to source tree. Source router.access-list.name.
                        type: str
                    ssm:
                        description:
                            - Enable/disable source specific multicast.
                        type: str
                        choices:
                            - enable
                            - disable
                    ssm_range:
                        description:
                            - Groups allowed to source specific multicast. Source router.access-list.name.
                        type: str
            route_limit:
                description:
                    - Maximum number of multicast routes.
                type: int
            route_threshold:
                description:
                    - Generate warnings when the number of multicast routes exceeds this number, must not be greater than route-limit.
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
            cisco_exclude_genid: "enable"
            dr_priority: "6"
            hello_holdtime: "7"
            hello_interval: "8"
            igmp:
                access_group: "<your_own_value> (source router.access-list.name)"
                immediate_leave_group: "<your_own_value> (source router.access-list.name)"
                last_member_query_count: "12"
                last_member_query_interval: "13"
                query_interval: "14"
                query_max_response_time: "15"
                query_timeout: "16"
                router_alert_check: "enable"
                version: "3"
            join_group:
             -
                address: "<your_own_value>"
            multicast_flow: "<your_own_value> (source router.multicast-flow.name)"
            name: "default_name_22 (source system.interface.name)"
            neighbour_filter: "<your_own_value> (source router.access-list.name)"
            passive: "enable"
            pim_mode: "sparse-mode"
            propagation_delay: "26"
            rp_candidate: "enable"
            rp_candidate_group: "<your_own_value> (source router.access-list.name)"
            rp_candidate_interval: "29"
            rp_candidate_priority: "30"
            state_refresh_interval: "31"
            static_group: "<your_own_value> (source router.multicast-flow.name)"
            ttl_threshold: "33"
        multicast_routing: "enable"
        pim_sm_global:
            accept_register_list: "<your_own_value> (source router.access-list.name)"
            accept_source_list: "<your_own_value> (source router.access-list.name)"
            bsr_allow_quick_refresh: "enable"
            bsr_candidate: "enable"
            bsr_hash: "40"
            bsr_interface: "<your_own_value> (source system.interface.name)"
            bsr_priority: "42"
            cisco_crp_prefix: "enable"
            cisco_ignore_rp_set_priority: "enable"
            cisco_register_checksum: "enable"
            cisco_register_checksum_group: "<your_own_value> (source router.access-list.name)"
            join_prune_holdtime: "47"
            message_interval: "48"
            null_register_retries: "49"
            register_rate_limit: "50"
            register_rp_reachability: "enable"
            register_source: "disable"
            register_source_interface: "<your_own_value> (source system.interface.name)"
            register_source_ip: "<your_own_value>"
            register_supression: "55"
            rp_address:
             -
                group: "<your_own_value> (source router.access-list.name)"
                id:  "58"
                ip_address: "<your_own_value>"
            rp_register_keepalive: "60"
            spt_threshold: "enable"
            spt_threshold_group: "<your_own_value> (source router.access-list.name)"
            ssm: "enable"
            ssm_range: "<your_own_value> (source router.access-list.name)"
        route_limit: "65"
        route_threshold: "66"
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


def filter_router_multicast_data(json):
    option_list = ['interface', 'multicast_routing', 'pim_sm_global',
                   'route_limit', 'route_threshold']
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


def router_multicast(data, fos):
    vdom = data['vdom']
    router_multicast_data = data['router_multicast']
    filtered_data = underscore_to_hyphen(filter_router_multicast_data(router_multicast_data))

    return fos.set('router',
                   'multicast',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_router(data, fos):

    if data['router_multicast']:
        resp = router_multicast(data, fos)

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
        "router_multicast": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "interface": {"required": False, "type": "list",
                              "options": {
                                  "bfd": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                                  "cisco_exclude_genid": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                  "dr_priority": {"required": False, "type": "int"},
                                  "hello_holdtime": {"required": False, "type": "int"},
                                  "hello_interval": {"required": False, "type": "int"},
                                  "igmp": {"required": False, "type": "dict",
                                           "options": {
                                               "access_group": {"required": False, "type": "str"},
                                               "immediate_leave_group": {"required": False, "type": "str"},
                                               "last_member_query_count": {"required": False, "type": "int"},
                                               "last_member_query_interval": {"required": False, "type": "int"},
                                               "query_interval": {"required": False, "type": "int"},
                                               "query_max_response_time": {"required": False, "type": "int"},
                                               "query_timeout": {"required": False, "type": "int"},
                                               "router_alert_check": {"required": False, "type": "str",
                                                                      "choices": ["enable", "disable"]},
                                               "version": {"required": False, "type": "str",
                                                           "choices": ["3", "2", "1"]}
                                           }},
                                  "join_group": {"required": False, "type": "list",
                                                 "options": {
                                                     "address": {"required": True, "type": "str"}
                                                 }},
                                  "multicast_flow": {"required": False, "type": "str"},
                                  "name": {"required": True, "type": "str"},
                                  "neighbour_filter": {"required": False, "type": "str"},
                                  "passive": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                  "pim_mode": {"required": False, "type": "str",
                                               "choices": ["sparse-mode", "dense-mode"]},
                                  "propagation_delay": {"required": False, "type": "int"},
                                  "rp_candidate": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                  "rp_candidate_group": {"required": False, "type": "str"},
                                  "rp_candidate_interval": {"required": False, "type": "int"},
                                  "rp_candidate_priority": {"required": False, "type": "int"},
                                  "state_refresh_interval": {"required": False, "type": "int"},
                                  "static_group": {"required": False, "type": "str"},
                                  "ttl_threshold": {"required": False, "type": "int"}
                              }},
                "multicast_routing": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "pim_sm_global": {"required": False, "type": "dict",
                                  "options": {
                                      "accept_register_list": {"required": False, "type": "str"},
                                      "accept_source_list": {"required": False, "type": "str"},
                                      "bsr_allow_quick_refresh": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                      "bsr_candidate": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                      "bsr_hash": {"required": False, "type": "int"},
                                      "bsr_interface": {"required": False, "type": "str"},
                                      "bsr_priority": {"required": False, "type": "int"},
                                      "cisco_crp_prefix": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                      "cisco_ignore_rp_set_priority": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                      "cisco_register_checksum": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                      "cisco_register_checksum_group": {"required": False, "type": "str"},
                                      "join_prune_holdtime": {"required": False, "type": "int"},
                                      "message_interval": {"required": False, "type": "int"},
                                      "null_register_retries": {"required": False, "type": "int"},
                                      "register_rate_limit": {"required": False, "type": "int"},
                                      "register_rp_reachability": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                      "register_source": {"required": False, "type": "str",
                                                          "choices": ["disable", "interface", "ip-address"]},
                                      "register_source_interface": {"required": False, "type": "str"},
                                      "register_source_ip": {"required": False, "type": "str"},
                                      "register_supression": {"required": False, "type": "int"},
                                      "rp_address": {"required": False, "type": "list",
                                                     "options": {
                                                         "group": {"required": False, "type": "str"},
                                                         "id": {"required": True, "type": "int"},
                                                         "ip_address": {"required": False, "type": "str"}
                                                     }},
                                      "rp_register_keepalive": {"required": False, "type": "int"},
                                      "spt_threshold": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                      "spt_threshold_group": {"required": False, "type": "str"},
                                      "ssm": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                      "ssm_range": {"required": False, "type": "str"}
                                  }},
                "route_limit": {"required": False, "type": "int"},
                "route_threshold": {"required": False, "type": "int"}

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
