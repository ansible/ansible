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
module: fortios_router_route_map
short_description: Configure route maps in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify router feature and route_map category.
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
    state:
        description:
            - Indicates whether to create or remove the object.
        type: str
        required: true
        choices:
            - present
            - absent
    router_route_map:
        description:
            - Configure route maps.
        default: null
        type: dict
        suboptions:
            comments:
                description:
                    - Optional comments.
                type: str
            name:
                description:
                    - Name.
                required: true
                type: str
            rule:
                description:
                    - Rule.
                type: list
                suboptions:
                    action:
                        description:
                            - Action.
                        type: str
                        choices:
                            - permit
                            - deny
                    id:
                        description:
                            - Rule ID.
                        required: true
                        type: int
                    match_as_path:
                        description:
                            - Match BGP AS path list. Source router.aspath-list.name.
                        type: str
                    match_community:
                        description:
                            - Match BGP community list. Source router.community-list.name.
                        type: str
                    match_community_exact:
                        description:
                            - Enable/disable exact matching of communities.
                        type: str
                        choices:
                            - enable
                            - disable
                    match_flags:
                        description:
                            - BGP flag value to match (0 - 65535)
                        type: int
                    match_interface:
                        description:
                            - Match interface configuration. Source system.interface.name.
                        type: str
                    match_ip_address:
                        description:
                            - Match IP address permitted by access-list or prefix-list. Source router.access-list.name router.prefix-list.name.
                        type: str
                    match_ip_nexthop:
                        description:
                            - Match next hop IP address passed by access-list or prefix-list. Source router.access-list.name router.prefix-list.name.
                        type: str
                    match_ip6_address:
                        description:
                            - Match IPv6 address permitted by access-list6 or prefix-list6. Source router.access-list6.name router.prefix-list6.name.
                        type: str
                    match_ip6_nexthop:
                        description:
                            - Match next hop IPv6 address passed by access-list6 or prefix-list6. Source router.access-list6.name router.prefix-list6.name.
                        type: str
                    match_metric:
                        description:
                            - Match metric for redistribute routes.
                        type: int
                    match_origin:
                        description:
                            - Match BGP origin code.
                        type: str
                        choices:
                            - none
                            - egp
                            - igp
                            - incomplete
                    match_route_type:
                        description:
                            - Match route type.
                        type: str
                        choices:
                            - 1
                            - 2
                            - none
                    match_tag:
                        description:
                            - Match tag.
                        type: int
                    set_aggregator_as:
                        description:
                            - BGP aggregator AS.
                        type: int
                    set_aggregator_ip:
                        description:
                            - BGP aggregator IP.
                        type: str
                    set_aspath:
                        description:
                            - Prepend BGP AS path attribute.
                        type: list
                        suboptions:
                            as:
                                description:
                                    - AS number (0 - 42949672).
                                required: true
                                type: str
                    set_aspath_action:
                        description:
                            - Specify preferred action of set-aspath.
                        type: str
                        choices:
                            - prepend
                            - replace
                    set_atomic_aggregate:
                        description:
                            - Enable/disable BGP atomic aggregate attribute.
                        type: str
                        choices:
                            - enable
                            - disable
                    set_community:
                        description:
                            - BGP community attribute.
                        type: list
                        suboptions:
                            community:
                                description:
                                    - "Attribute: AA|AA:NN|internet|local-AS|no-advertise|no-export."
                                required: true
                                type: str
                    set_community_additive:
                        description:
                            - Enable/disable adding set-community to existing community.
                        type: str
                        choices:
                            - enable
                            - disable
                    set_community_delete:
                        description:
                            - Delete communities matching community list. Source router.community-list.name.
                        type: str
                    set_dampening_max_suppress:
                        description:
                            - Maximum duration to suppress a route (1 - 255 min, 0 = unset).
                        type: int
                    set_dampening_reachability_half_life:
                        description:
                            - Reachability half-life time for the penalty (1 - 45 min, 0 = unset).
                        type: int
                    set_dampening_reuse:
                        description:
                            - Value to start reusing a route (1 - 20000, 0 = unset).
                        type: int
                    set_dampening_suppress:
                        description:
                            - Value to start suppressing a route (1 - 20000, 0 = unset).
                        type: int
                    set_dampening_unreachability_half_life:
                        description:
                            - Unreachability Half-life time for the penalty (1 - 45 min, 0 = unset)
                        type: int
                    set_extcommunity_rt:
                        description:
                            - Route Target extended community.
                        type: list
                        suboptions:
                            community:
                                description:
                                    - Set the target extended community (in decimal notation) of a BGP route.
                                required: true
                                type: str
                    set_extcommunity_soo:
                        description:
                            - Site-of-Origin extended community.
                        type: list
                        suboptions:
                            community:
                                description:
                                    - "AA:NN"
                                required: true
                                type: str
                    set_flags:
                        description:
                            - BGP flags value (0 - 65535)
                        type: int
                    set_ip_nexthop:
                        description:
                            - IP address of next hop.
                        type: str
                    set_ip6_nexthop:
                        description:
                            - IPv6 global address of next hop.
                        type: str
                    set_ip6_nexthop_local:
                        description:
                            - IPv6 local address of next hop.
                        type: str
                    set_local_preference:
                        description:
                            - BGP local preference path attribute.
                        type: int
                    set_metric:
                        description:
                            - Metric value.
                        type: int
                    set_metric_type:
                        description:
                            - Metric type.
                        type: str
                        choices:
                            - 1
                            - 2
                            - none
                    set_origin:
                        description:
                            - BGP origin code.
                        type: str
                        choices:
                            - none
                            - egp
                            - igp
                            - incomplete
                    set_originator_id:
                        description:
                            - BGP originator ID attribute.
                        type: str
                    set_route_tag:
                        description:
                            - Route tag for routing table.
                        type: int
                    set_tag:
                        description:
                            - Tag value.
                        type: int
                    set_weight:
                        description:
                            - BGP weight for routing table.
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
  - name: Configure route maps.
    fortios_router_route_map:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      router_route_map:
        comments: "<your_own_value>"
        name: "default_name_4"
        rule:
         -
            action: "permit"
            id:  "7"
            match_as_path: "<your_own_value> (source router.aspath-list.name)"
            match_community: "<your_own_value> (source router.community-list.name)"
            match_community_exact: "enable"
            match_flags: "11"
            match_interface: "<your_own_value> (source system.interface.name)"
            match_ip_address: "<your_own_value> (source router.access-list.name router.prefix-list.name)"
            match_ip_nexthop: "<your_own_value> (source router.access-list.name router.prefix-list.name)"
            match_ip6_address: "<your_own_value> (source router.access-list6.name router.prefix-list6.name)"
            match_ip6_nexthop: "<your_own_value> (source router.access-list6.name router.prefix-list6.name)"
            match_metric: "17"
            match_origin: "none"
            match_route_type: "1"
            match_tag: "20"
            set_aggregator_as: "21"
            set_aggregator_ip: "<your_own_value>"
            set_aspath:
             -
                as: "<your_own_value>"
            set_aspath_action: "prepend"
            set_atomic_aggregate: "enable"
            set_community:
             -
                community: "<your_own_value>"
            set_community_additive: "enable"
            set_community_delete: "<your_own_value> (source router.community-list.name)"
            set_dampening_max_suppress: "31"
            set_dampening_reachability_half_life: "32"
            set_dampening_reuse: "33"
            set_dampening_suppress: "34"
            set_dampening_unreachability_half_life: "35"
            set_extcommunity_rt:
             -
                community: "<your_own_value>"
            set_extcommunity_soo:
             -
                community: "<your_own_value>"
            set_flags: "40"
            set_ip_nexthop: "<your_own_value>"
            set_ip6_nexthop: "<your_own_value>"
            set_ip6_nexthop_local: "<your_own_value>"
            set_local_preference: "44"
            set_metric: "45"
            set_metric_type: "1"
            set_origin: "none"
            set_originator_id: "<your_own_value>"
            set_route_tag: "49"
            set_tag: "50"
            set_weight: "51"
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


def filter_router_route_map_data(json):
    option_list = ['comments', 'name', 'rule']
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


def router_route_map(data, fos):
    vdom = data['vdom']
    state = data['state']
    router_route_map_data = data['router_route_map']
    filtered_data = underscore_to_hyphen(filter_router_route_map_data(router_route_map_data))

    if state == "present":
        return fos.set('router',
                       'route-map',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('router',
                          'route-map',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_router(data, fos):

    if data['router_route_map']:
        resp = router_route_map(data, fos)

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
        "state": {"required": True, "type": "str",
                  "choices": ["present", "absent"]},
        "router_route_map": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "comments": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "rule": {"required": False, "type": "list",
                         "options": {
                             "action": {"required": False, "type": "str",
                                        "choices": ["permit", "deny"]},
                             "id": {"required": True, "type": "int"},
                             "match_as_path": {"required": False, "type": "str"},
                             "match_community": {"required": False, "type": "str"},
                             "match_community_exact": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                             "match_flags": {"required": False, "type": "int"},
                             "match_interface": {"required": False, "type": "str"},
                             "match_ip_address": {"required": False, "type": "str"},
                             "match_ip_nexthop": {"required": False, "type": "str"},
                             "match_ip6_address": {"required": False, "type": "str"},
                             "match_ip6_nexthop": {"required": False, "type": "str"},
                             "match_metric": {"required": False, "type": "int"},
                             "match_origin": {"required": False, "type": "str",
                                              "choices": ["none", "egp", "igp",
                                                          "incomplete"]},
                             "match_route_type": {"required": False, "type": "str",
                                                  "choices": ["1", "2", "none"]},
                             "match_tag": {"required": False, "type": "int"},
                             "set_aggregator_as": {"required": False, "type": "int"},
                             "set_aggregator_ip": {"required": False, "type": "str"},
                             "set_aspath": {"required": False, "type": "list",
                                            "options": {
                                                "as": {"required": True, "type": "str"}
                                            }},
                             "set_aspath_action": {"required": False, "type": "str",
                                                   "choices": ["prepend", "replace"]},
                             "set_atomic_aggregate": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                             "set_community": {"required": False, "type": "list",
                                               "options": {
                                                   "community": {"required": True, "type": "str"}
                                               }},
                             "set_community_additive": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                             "set_community_delete": {"required": False, "type": "str"},
                             "set_dampening_max_suppress": {"required": False, "type": "int"},
                             "set_dampening_reachability_half_life": {"required": False, "type": "int"},
                             "set_dampening_reuse": {"required": False, "type": "int"},
                             "set_dampening_suppress": {"required": False, "type": "int"},
                             "set_dampening_unreachability_half_life": {"required": False, "type": "int"},
                             "set_extcommunity_rt": {"required": False, "type": "list",
                                                     "options": {
                                                         "community": {"required": True, "type": "str"}
                                                     }},
                             "set_extcommunity_soo": {"required": False, "type": "list",
                                                      "options": {
                                                          "community": {"required": True, "type": "str"}
                                                      }},
                             "set_flags": {"required": False, "type": "int"},
                             "set_ip_nexthop": {"required": False, "type": "str"},
                             "set_ip6_nexthop": {"required": False, "type": "str"},
                             "set_ip6_nexthop_local": {"required": False, "type": "str"},
                             "set_local_preference": {"required": False, "type": "int"},
                             "set_metric": {"required": False, "type": "int"},
                             "set_metric_type": {"required": False, "type": "str",
                                                 "choices": ["1", "2", "none"]},
                             "set_origin": {"required": False, "type": "str",
                                            "choices": ["none", "egp", "igp",
                                                        "incomplete"]},
                             "set_originator_id": {"required": False, "type": "str"},
                             "set_route_tag": {"required": False, "type": "int"},
                             "set_tag": {"required": False, "type": "int"},
                             "set_weight": {"required": False, "type": "int"}
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
