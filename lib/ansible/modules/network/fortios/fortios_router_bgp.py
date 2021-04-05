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
module: fortios_router_bgp
short_description: Configure BGP in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify router feature and bgp category.
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
    router_bgp:
        description:
            - Configure BGP.
        default: null
        type: dict
        suboptions:
            admin_distance:
                description:
                    - Administrative distance modifications.
                type: list
                suboptions:
                    distance:
                        description:
                            - Administrative distance to apply (1 - 255).
                        type: int
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    neighbour_prefix:
                        description:
                            - Neighbor address prefix.
                        type: str
                    route_list:
                        description:
                            - Access list of routes to apply new distance to. Source router.access-list.name.
                        type: str
            aggregate_address:
                description:
                    - BGP aggregate address table.
                type: list
                suboptions:
                    as_set:
                        description:
                            - Enable/disable generate AS set path information.
                        type: str
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    prefix:
                        description:
                            - Aggregate prefix.
                        type: str
                    summary_only:
                        description:
                            - Enable/disable filter more specific routes from updates.
                        type: str
                        choices:
                            - enable
                            - disable
            aggregate_address6:
                description:
                    - BGP IPv6 aggregate address table.
                type: list
                suboptions:
                    as_set:
                        description:
                            - Enable/disable generate AS set path information.
                        type: str
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    prefix6:
                        description:
                            - Aggregate IPv6 prefix.
                        type: str
                    summary_only:
                        description:
                            - Enable/disable filter more specific routes from updates.
                        type: str
                        choices:
                            - enable
                            - disable
            always_compare_med:
                description:
                    - Enable/disable always compare MED.
                type: str
                choices:
                    - enable
                    - disable
            as:
                description:
                    - Router AS number, valid from 1 to 4294967295, 0 to disable BGP.
                type: int
            bestpath_as_path_ignore:
                description:
                    - Enable/disable ignore AS path.
                type: str
                choices:
                    - enable
                    - disable
            bestpath_cmp_confed_aspath:
                description:
                    - Enable/disable compare federation AS path length.
                type: str
                choices:
                    - enable
                    - disable
            bestpath_cmp_routerid:
                description:
                    - Enable/disable compare router ID for identical EBGP paths.
                type: str
                choices:
                    - enable
                    - disable
            bestpath_med_confed:
                description:
                    - Enable/disable compare MED among confederation paths.
                type: str
                choices:
                    - enable
                    - disable
            bestpath_med_missing_as_worst:
                description:
                    - Enable/disable treat missing MED as least preferred.
                type: str
                choices:
                    - enable
                    - disable
            client_to_client_reflection:
                description:
                    - Enable/disable client-to-client route reflection.
                type: str
                choices:
                    - enable
                    - disable
            cluster_id:
                description:
                    - Route reflector cluster ID.
                type: str
            confederation_identifier:
                description:
                    - Confederation identifier.
                type: int
            confederation_peers:
                description:
                    - Confederation peers.
                type: list
                suboptions:
                    peer:
                        description:
                            - Peer ID.
                        required: true
                        type: str
            dampening:
                description:
                    - Enable/disable route-flap dampening.
                type: str
                choices:
                    - enable
                    - disable
            dampening_max_suppress_time:
                description:
                    - Maximum minutes a route can be suppressed.
                type: int
            dampening_reachability_half_life:
                description:
                    - Reachability half-life time for penalty (min).
                type: int
            dampening_reuse:
                description:
                    - Threshold to reuse routes.
                type: int
            dampening_route_map:
                description:
                    - Criteria for dampening. Source router.route-map.name.
                type: str
            dampening_suppress:
                description:
                    - Threshold to suppress routes.
                type: int
            dampening_unreachability_half_life:
                description:
                    - Unreachability half-life time for penalty (min).
                type: int
            default_local_preference:
                description:
                    - Default local preference.
                type: int
            deterministic_med:
                description:
                    - Enable/disable enforce deterministic comparison of MED.
                type: str
                choices:
                    - enable
                    - disable
            distance_external:
                description:
                    - Distance for routes external to the AS.
                type: int
            distance_internal:
                description:
                    - Distance for routes internal to the AS.
                type: int
            distance_local:
                description:
                    - Distance for routes local to the AS.
                type: int
            ebgp_multipath:
                description:
                    - Enable/disable EBGP multi-path.
                type: str
                choices:
                    - enable
                    - disable
            enforce_first_as:
                description:
                    - Enable/disable enforce first AS for EBGP routes.
                type: str
                choices:
                    - enable
                    - disable
            fast_external_failover:
                description:
                    - Enable/disable reset peer BGP session if link goes down.
                type: str
                choices:
                    - enable
                    - disable
            graceful_end_on_timer:
                description:
                    - Enable/disable to exit graceful restart on timer only.
                type: str
                choices:
                    - enable
                    - disable
            graceful_restart:
                description:
                    - Enable/disable BGP graceful restart capabilities.
                type: str
                choices:
                    - enable
                    - disable
            graceful_restart_time:
                description:
                    - Time needed for neighbors to restart (sec).
                type: int
            graceful_stalepath_time:
                description:
                    - Time to hold stale paths of restarting neighbor (sec).
                type: int
            graceful_update_delay:
                description:
                    - Route advertisement/selection delay after restart (sec).
                type: int
            holdtime_timer:
                description:
                    - Number of seconds to mark peer as dead.
                type: int
            ibgp_multipath:
                description:
                    - Enable/disable IBGP multi-path.
                type: str
                choices:
                    - enable
                    - disable
            ignore_optional_capability:
                description:
                    - Don't send unknown optional capability notification message
                type: str
                choices:
                    - enable
                    - disable
            keepalive_timer:
                description:
                    - Frequency to send keep alive requests.
                type: int
            log_neighbour_changes:
                description:
                    - Enable logging of BGP neighbour's changes
                type: str
                choices:
                    - enable
                    - disable
            neighbor:
                description:
                    - BGP neighbor table.
                type: list
                suboptions:
                    activate:
                        description:
                            - Enable/disable address family IPv4 for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    activate6:
                        description:
                            - Enable/disable address family IPv6 for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    advertisement_interval:
                        description:
                            - Minimum interval (sec) between sending updates.
                        type: int
                    allowas_in:
                        description:
                            - IPv4 The maximum number of occurrence of my AS number allowed.
                        type: int
                    allowas_in_enable:
                        description:
                            - Enable/disable IPv4 Enable to allow my AS in AS path.
                        type: str
                        choices:
                            - enable
                            - disable
                    allowas_in_enable6:
                        description:
                            - Enable/disable IPv6 Enable to allow my AS in AS path.
                        type: str
                        choices:
                            - enable
                            - disable
                    allowas_in6:
                        description:
                            - IPv6 The maximum number of occurrence of my AS number allowed.
                        type: int
                    as_override:
                        description:
                            - Enable/disable replace peer AS with own AS for IPv4.
                        type: str
                        choices:
                            - enable
                            - disable
                    as_override6:
                        description:
                            - Enable/disable replace peer AS with own AS for IPv6.
                        type: str
                        choices:
                            - enable
                            - disable
                    attribute_unchanged:
                        description:
                            - IPv4 List of attributes that should be unchanged.
                        type: str
                        choices:
                            - as-path
                            - med
                            - next-hop
                    attribute_unchanged6:
                        description:
                            - IPv6 List of attributes that should be unchanged.
                        type: str
                        choices:
                            - as-path
                            - med
                            - next-hop
                    bfd:
                        description:
                            - Enable/disable BFD for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_default_originate:
                        description:
                            - Enable/disable advertise default IPv4 route to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_default_originate6:
                        description:
                            - Enable/disable advertise default IPv6 route to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_dynamic:
                        description:
                            - Enable/disable advertise dynamic capability to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_graceful_restart:
                        description:
                            - Enable/disable advertise IPv4 graceful restart capability to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_graceful_restart6:
                        description:
                            - Enable/disable advertise IPv6 graceful restart capability to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_orf:
                        description:
                            - Accept/Send IPv4 ORF lists to/from this neighbor.
                        type: str
                        choices:
                            - none
                            - receive
                            - send
                            - both
                    capability_orf6:
                        description:
                            - Accept/Send IPv6 ORF lists to/from this neighbor.
                        type: str
                        choices:
                            - none
                            - receive
                            - send
                            - both
                    capability_route_refresh:
                        description:
                            - Enable/disable advertise route refresh capability to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    conditional_advertise:
                        description:
                            - Conditional advertisement.
                        type: list
                        suboptions:
                            advertise_routemap:
                                description:
                                    - Name of advertising route map. Source router.route-map.name.
                                type: str
                            condition_routemap:
                                description:
                                    - Name of condition route map. Source router.route-map.name.
                                type: str
                            condition_type:
                                description:
                                    - Type of condition.
                                type: str
                                choices:
                                    - exist
                                    - non-exist
                    connect_timer:
                        description:
                            - Interval (sec) for connect timer.
                        type: int
                    default_originate_routemap:
                        description:
                            - Route map to specify criteria to originate IPv4 default. Source router.route-map.name.
                        type: str
                    default_originate_routemap6:
                        description:
                            - Route map to specify criteria to originate IPv6 default. Source router.route-map.name.
                        type: str
                    description:
                        description:
                            - Description.
                        type: str
                    distribute_list_in:
                        description:
                            - Filter for IPv4 updates from this neighbor. Source router.access-list.name.
                        type: str
                    distribute_list_in6:
                        description:
                            - Filter for IPv6 updates from this neighbor. Source router.access-list6.name.
                        type: str
                    distribute_list_out:
                        description:
                            - Filter for IPv4 updates to this neighbor. Source router.access-list.name.
                        type: str
                    distribute_list_out6:
                        description:
                            - Filter for IPv6 updates to this neighbor. Source router.access-list6.name.
                        type: str
                    dont_capability_negotiate:
                        description:
                            - Don't negotiate capabilities with this neighbor
                        type: str
                        choices:
                            - enable
                            - disable
                    ebgp_enforce_multihop:
                        description:
                            - Enable/disable allow multi-hop EBGP neighbors.
                        type: str
                        choices:
                            - enable
                            - disable
                    ebgp_multihop_ttl:
                        description:
                            - EBGP multihop TTL for this peer.
                        type: int
                    filter_list_in:
                        description:
                            - BGP filter for IPv4 inbound routes. Source router.aspath-list.name.
                        type: str
                    filter_list_in6:
                        description:
                            - BGP filter for IPv6 inbound routes. Source router.aspath-list.name.
                        type: str
                    filter_list_out:
                        description:
                            - BGP filter for IPv4 outbound routes. Source router.aspath-list.name.
                        type: str
                    filter_list_out6:
                        description:
                            - BGP filter for IPv6 outbound routes. Source router.aspath-list.name.
                        type: str
                    holdtime_timer:
                        description:
                            - Interval (sec) before peer considered dead.
                        type: int
                    interface:
                        description:
                            - Interface Source system.interface.name.
                        type: str
                    ip:
                        description:
                            - IP/IPv6 address of neighbor.
                        required: true
                        type: str
                    keep_alive_timer:
                        description:
                            - Keep alive timer interval (sec).
                        type: int
                    link_down_failover:
                        description:
                            - Enable/disable failover upon link down.
                        type: str
                        choices:
                            - enable
                            - disable
                    local_as:
                        description:
                            - Local AS number of neighbor.
                        type: int
                    local_as_no_prepend:
                        description:
                            - Do not prepend local-as to incoming updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    local_as_replace_as:
                        description:
                            - Replace real AS with local-as in outgoing updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    maximum_prefix:
                        description:
                            - Maximum number of IPv4 prefixes to accept from this peer.
                        type: int
                    maximum_prefix_threshold:
                        description:
                            - Maximum IPv4 prefix threshold value (1 - 100 percent).
                        type: int
                    maximum_prefix_threshold6:
                        description:
                            - Maximum IPv6 prefix threshold value (1 - 100 percent).
                        type: int
                    maximum_prefix_warning_only:
                        description:
                            - Enable/disable IPv4 Only give warning message when limit is exceeded.
                        type: str
                        choices:
                            - enable
                            - disable
                    maximum_prefix_warning_only6:
                        description:
                            - Enable/disable IPv6 Only give warning message when limit is exceeded.
                        type: str
                        choices:
                            - enable
                            - disable
                    maximum_prefix6:
                        description:
                            - Maximum number of IPv6 prefixes to accept from this peer.
                        type: int
                    next_hop_self:
                        description:
                            - Enable/disable IPv4 next-hop calculation for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    next_hop_self6:
                        description:
                            - Enable/disable IPv6 next-hop calculation for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_capability:
                        description:
                            - Enable/disable override result of capability negotiation.
                        type: str
                        choices:
                            - enable
                            - disable
                    passive:
                        description:
                            - Enable/disable sending of open messages to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    password:
                        description:
                            - Password used in MD5 authentication.
                        type: str
                    prefix_list_in:
                        description:
                            - IPv4 Inbound filter for updates from this neighbor. Source router.prefix-list.name.
                        type: str
                    prefix_list_in6:
                        description:
                            - IPv6 Inbound filter for updates from this neighbor. Source router.prefix-list6.name.
                        type: str
                    prefix_list_out:
                        description:
                            - IPv4 Outbound filter for updates to this neighbor. Source router.prefix-list.name.
                        type: str
                    prefix_list_out6:
                        description:
                            - IPv6 Outbound filter for updates to this neighbor. Source router.prefix-list6.name.
                        type: str
                    remote_as:
                        description:
                            - AS number of neighbor.
                        type: int
                    remove_private_as:
                        description:
                            - Enable/disable remove private AS number from IPv4 outbound updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    remove_private_as6:
                        description:
                            - Enable/disable remove private AS number from IPv6 outbound updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    restart_time:
                        description:
                            - Graceful restart delay time (sec, 0 = global default).
                        type: int
                    retain_stale_time:
                        description:
                            - Time to retain stale routes.
                        type: int
                    route_map_in:
                        description:
                            - IPv4 Inbound route map filter. Source router.route-map.name.
                        type: str
                    route_map_in6:
                        description:
                            - IPv6 Inbound route map filter. Source router.route-map.name.
                        type: str
                    route_map_out:
                        description:
                            - IPv4 Outbound route map filter. Source router.route-map.name.
                        type: str
                    route_map_out6:
                        description:
                            - IPv6 Outbound route map filter. Source router.route-map.name.
                        type: str
                    route_reflector_client:
                        description:
                            - Enable/disable IPv4 AS route reflector client.
                        type: str
                        choices:
                            - enable
                            - disable
                    route_reflector_client6:
                        description:
                            - Enable/disable IPv6 AS route reflector client.
                        type: str
                        choices:
                            - enable
                            - disable
                    route_server_client:
                        description:
                            - Enable/disable IPv4 AS route server client.
                        type: str
                        choices:
                            - enable
                            - disable
                    route_server_client6:
                        description:
                            - Enable/disable IPv6 AS route server client.
                        type: str
                        choices:
                            - enable
                            - disable
                    send_community:
                        description:
                            - IPv4 Send community attribute to neighbor.
                        type: str
                        choices:
                            - standard
                            - extended
                            - both
                            - disable
                    send_community6:
                        description:
                            - IPv6 Send community attribute to neighbor.
                        type: str
                        choices:
                            - standard
                            - extended
                            - both
                            - disable
                    shutdown:
                        description:
                            - Enable/disable shutdown this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    soft_reconfiguration:
                        description:
                            - Enable/disable allow IPv4 inbound soft reconfiguration.
                        type: str
                        choices:
                            - enable
                            - disable
                    soft_reconfiguration6:
                        description:
                            - Enable/disable allow IPv6 inbound soft reconfiguration.
                        type: str
                        choices:
                            - enable
                            - disable
                    stale_route:
                        description:
                            - Enable/disable stale route after neighbor down.
                        type: str
                        choices:
                            - enable
                            - disable
                    strict_capability_match:
                        description:
                            - Enable/disable strict capability matching.
                        type: str
                        choices:
                            - enable
                            - disable
                    unsuppress_map:
                        description:
                            - IPv4 Route map to selectively unsuppress suppressed routes. Source router.route-map.name.
                        type: str
                    unsuppress_map6:
                        description:
                            - IPv6 Route map to selectively unsuppress suppressed routes. Source router.route-map.name.
                        type: str
                    update_source:
                        description:
                            - Interface to use as source IP/IPv6 address of TCP connections. Source system.interface.name.
                        type: str
                    weight:
                        description:
                            - Neighbor weight.
                        type: int
            neighbor_group:
                description:
                    - BGP neighbor group table.
                type: list
                suboptions:
                    activate:
                        description:
                            - Enable/disable address family IPv4 for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    activate6:
                        description:
                            - Enable/disable address family IPv6 for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    advertisement_interval:
                        description:
                            - Minimum interval (sec) between sending updates.
                        type: int
                    allowas_in:
                        description:
                            - IPv4 The maximum number of occurrence of my AS number allowed.
                        type: int
                    allowas_in_enable:
                        description:
                            - Enable/disable IPv4 Enable to allow my AS in AS path.
                        type: str
                        choices:
                            - enable
                            - disable
                    allowas_in_enable6:
                        description:
                            - Enable/disable IPv6 Enable to allow my AS in AS path.
                        type: str
                        choices:
                            - enable
                            - disable
                    allowas_in6:
                        description:
                            - IPv6 The maximum number of occurrence of my AS number allowed.
                        type: int
                    as_override:
                        description:
                            - Enable/disable replace peer AS with own AS for IPv4.
                        type: str
                        choices:
                            - enable
                            - disable
                    as_override6:
                        description:
                            - Enable/disable replace peer AS with own AS for IPv6.
                        type: str
                        choices:
                            - enable
                            - disable
                    attribute_unchanged:
                        description:
                            - IPv4 List of attributes that should be unchanged.
                        type: str
                        choices:
                            - as-path
                            - med
                            - next-hop
                    attribute_unchanged6:
                        description:
                            - IPv6 List of attributes that should be unchanged.
                        type: str
                        choices:
                            - as-path
                            - med
                            - next-hop
                    bfd:
                        description:
                            - Enable/disable BFD for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_default_originate:
                        description:
                            - Enable/disable advertise default IPv4 route to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_default_originate6:
                        description:
                            - Enable/disable advertise default IPv6 route to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_dynamic:
                        description:
                            - Enable/disable advertise dynamic capability to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_graceful_restart:
                        description:
                            - Enable/disable advertise IPv4 graceful restart capability to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_graceful_restart6:
                        description:
                            - Enable/disable advertise IPv6 graceful restart capability to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    capability_orf:
                        description:
                            - Accept/Send IPv4 ORF lists to/from this neighbor.
                        type: str
                        choices:
                            - none
                            - receive
                            - send
                            - both
                    capability_orf6:
                        description:
                            - Accept/Send IPv6 ORF lists to/from this neighbor.
                        type: str
                        choices:
                            - none
                            - receive
                            - send
                            - both
                    capability_route_refresh:
                        description:
                            - Enable/disable advertise route refresh capability to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    connect_timer:
                        description:
                            - Interval (sec) for connect timer.
                        type: int
                    default_originate_routemap:
                        description:
                            - Route map to specify criteria to originate IPv4 default. Source router.route-map.name.
                        type: str
                    default_originate_routemap6:
                        description:
                            - Route map to specify criteria to originate IPv6 default. Source router.route-map.name.
                        type: str
                    description:
                        description:
                            - Description.
                        type: str
                    distribute_list_in:
                        description:
                            - Filter for IPv4 updates from this neighbor. Source router.access-list.name.
                        type: str
                    distribute_list_in6:
                        description:
                            - Filter for IPv6 updates from this neighbor. Source router.access-list6.name.
                        type: str
                    distribute_list_out:
                        description:
                            - Filter for IPv4 updates to this neighbor. Source router.access-list.name.
                        type: str
                    distribute_list_out6:
                        description:
                            - Filter for IPv6 updates to this neighbor. Source router.access-list6.name.
                        type: str
                    dont_capability_negotiate:
                        description:
                            - Don't negotiate capabilities with this neighbor
                        type: str
                        choices:
                            - enable
                            - disable
                    ebgp_enforce_multihop:
                        description:
                            - Enable/disable allow multi-hop EBGP neighbors.
                        type: str
                        choices:
                            - enable
                            - disable
                    ebgp_multihop_ttl:
                        description:
                            - EBGP multihop TTL for this peer.
                        type: int
                    filter_list_in:
                        description:
                            - BGP filter for IPv4 inbound routes. Source router.aspath-list.name.
                        type: str
                    filter_list_in6:
                        description:
                            - BGP filter for IPv6 inbound routes. Source router.aspath-list.name.
                        type: str
                    filter_list_out:
                        description:
                            - BGP filter for IPv4 outbound routes. Source router.aspath-list.name.
                        type: str
                    filter_list_out6:
                        description:
                            - BGP filter for IPv6 outbound routes. Source router.aspath-list.name.
                        type: str
                    holdtime_timer:
                        description:
                            - Interval (sec) before peer considered dead.
                        type: int
                    interface:
                        description:
                            - Interface Source system.interface.name.
                        type: str
                    keep_alive_timer:
                        description:
                            - Keep alive timer interval (sec).
                        type: int
                    link_down_failover:
                        description:
                            - Enable/disable failover upon link down.
                        type: str
                        choices:
                            - enable
                            - disable
                    local_as:
                        description:
                            - Local AS number of neighbor.
                        type: int
                    local_as_no_prepend:
                        description:
                            - Do not prepend local-as to incoming updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    local_as_replace_as:
                        description:
                            - Replace real AS with local-as in outgoing updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    maximum_prefix:
                        description:
                            - Maximum number of IPv4 prefixes to accept from this peer.
                        type: int
                    maximum_prefix_threshold:
                        description:
                            - Maximum IPv4 prefix threshold value (1 - 100 percent).
                        type: int
                    maximum_prefix_threshold6:
                        description:
                            - Maximum IPv6 prefix threshold value (1 - 100 percent).
                        type: int
                    maximum_prefix_warning_only:
                        description:
                            - Enable/disable IPv4 Only give warning message when limit is exceeded.
                        type: str
                        choices:
                            - enable
                            - disable
                    maximum_prefix_warning_only6:
                        description:
                            - Enable/disable IPv6 Only give warning message when limit is exceeded.
                        type: str
                        choices:
                            - enable
                            - disable
                    maximum_prefix6:
                        description:
                            - Maximum number of IPv6 prefixes to accept from this peer.
                        type: int
                    name:
                        description:
                            - Neighbor group name.
                        required: true
                        type: str
                    next_hop_self:
                        description:
                            - Enable/disable IPv4 next-hop calculation for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    next_hop_self6:
                        description:
                            - Enable/disable IPv6 next-hop calculation for this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_capability:
                        description:
                            - Enable/disable override result of capability negotiation.
                        type: str
                        choices:
                            - enable
                            - disable
                    passive:
                        description:
                            - Enable/disable sending of open messages to this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    prefix_list_in:
                        description:
                            - IPv4 Inbound filter for updates from this neighbor. Source router.prefix-list.name.
                        type: str
                    prefix_list_in6:
                        description:
                            - IPv6 Inbound filter for updates from this neighbor. Source router.prefix-list6.name.
                        type: str
                    prefix_list_out:
                        description:
                            - IPv4 Outbound filter for updates to this neighbor. Source router.prefix-list.name.
                        type: str
                    prefix_list_out6:
                        description:
                            - IPv6 Outbound filter for updates to this neighbor. Source router.prefix-list6.name.
                        type: str
                    remote_as:
                        description:
                            - AS number of neighbor.
                        type: int
                    remove_private_as:
                        description:
                            - Enable/disable remove private AS number from IPv4 outbound updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    remove_private_as6:
                        description:
                            - Enable/disable remove private AS number from IPv6 outbound updates.
                        type: str
                        choices:
                            - enable
                            - disable
                    restart_time:
                        description:
                            - Graceful restart delay time (sec, 0 = global default).
                        type: int
                    retain_stale_time:
                        description:
                            - Time to retain stale routes.
                        type: int
                    route_map_in:
                        description:
                            - IPv4 Inbound route map filter. Source router.route-map.name.
                        type: str
                    route_map_in6:
                        description:
                            - IPv6 Inbound route map filter. Source router.route-map.name.
                        type: str
                    route_map_out:
                        description:
                            - IPv4 Outbound route map filter. Source router.route-map.name.
                        type: str
                    route_map_out6:
                        description:
                            - IPv6 Outbound route map filter. Source router.route-map.name.
                        type: str
                    route_reflector_client:
                        description:
                            - Enable/disable IPv4 AS route reflector client.
                        type: str
                        choices:
                            - enable
                            - disable
                    route_reflector_client6:
                        description:
                            - Enable/disable IPv6 AS route reflector client.
                        type: str
                        choices:
                            - enable
                            - disable
                    route_server_client:
                        description:
                            - Enable/disable IPv4 AS route server client.
                        type: str
                        choices:
                            - enable
                            - disable
                    route_server_client6:
                        description:
                            - Enable/disable IPv6 AS route server client.
                        type: str
                        choices:
                            - enable
                            - disable
                    send_community:
                        description:
                            - IPv4 Send community attribute to neighbor.
                        type: str
                        choices:
                            - standard
                            - extended
                            - both
                            - disable
                    send_community6:
                        description:
                            - IPv6 Send community attribute to neighbor.
                        type: str
                        choices:
                            - standard
                            - extended
                            - both
                            - disable
                    shutdown:
                        description:
                            - Enable/disable shutdown this neighbor.
                        type: str
                        choices:
                            - enable
                            - disable
                    soft_reconfiguration:
                        description:
                            - Enable/disable allow IPv4 inbound soft reconfiguration.
                        type: str
                        choices:
                            - enable
                            - disable
                    soft_reconfiguration6:
                        description:
                            - Enable/disable allow IPv6 inbound soft reconfiguration.
                        type: str
                        choices:
                            - enable
                            - disable
                    stale_route:
                        description:
                            - Enable/disable stale route after neighbor down.
                        type: str
                        choices:
                            - enable
                            - disable
                    strict_capability_match:
                        description:
                            - Enable/disable strict capability matching.
                        type: str
                        choices:
                            - enable
                            - disable
                    unsuppress_map:
                        description:
                            - IPv4 Route map to selectively unsuppress suppressed routes. Source router.route-map.name.
                        type: str
                    unsuppress_map6:
                        description:
                            - IPv6 Route map to selectively unsuppress suppressed routes. Source router.route-map.name.
                        type: str
                    update_source:
                        description:
                            - Interface to use as source IP/IPv6 address of TCP connections. Source system.interface.name.
                        type: str
                    weight:
                        description:
                            - Neighbor weight.
                        type: int
            neighbor_range:
                description:
                    - BGP neighbor range table.
                type: list
                suboptions:
                    id:
                        description:
                            - Neighbor range ID.
                        required: true
                        type: int
                    max_neighbor_num:
                        description:
                            - Maximum number of neighbors.
                        type: int
                    neighbor_group:
                        description:
                            - Neighbor group name. Source router.bgp.neighbor-group.name.
                        type: str
                    prefix:
                        description:
                            - Neighbor range prefix.
                        type: str
            neighbor_range6:
                description:
                    - BGP IPv6 neighbor range table.
                type: list
                suboptions:
                    id:
                        description:
                            - IPv6 neighbor range ID.
                        required: true
                        type: int
                    max_neighbor_num:
                        description:
                            - Maximum number of neighbors.
                        type: int
                    neighbor_group:
                        description:
                            - Neighbor group name. Source router.bgp.neighbor-group.name.
                        type: str
                    prefix6:
                        description:
                            - IPv6 prefix.
                        type: str
            network:
                description:
                    - BGP network table.
                type: list
                suboptions:
                    backdoor:
                        description:
                            - Enable/disable route as backdoor.
                        type: str
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    prefix:
                        description:
                            - Network prefix.
                        type: str
                    route_map:
                        description:
                            - Route map to modify generated route. Source router.route-map.name.
                        type: str
            network_import_check:
                description:
                    - Enable/disable ensure BGP network route exists in IGP.
                type: str
                choices:
                    - enable
                    - disable
            network6:
                description:
                    - BGP IPv6 network table.
                type: list
                suboptions:
                    backdoor:
                        description:
                            - Enable/disable route as backdoor.
                        type: str
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    prefix6:
                        description:
                            - Network IPv6 prefix.
                        type: str
                    route_map:
                        description:
                            - Route map to modify generated route. Source router.route-map.name.
                        type: str
            redistribute:
                description:
                    - BGP IPv4 redistribute table.
                type: list
                suboptions:
                    name:
                        description:
                            - Distribute list entry name.
                        required: true
                        type: str
                    route_map:
                        description:
                            - Route map name. Source router.route-map.name.
                        type: str
                    status:
                        description:
                            - Status
                        type: str
                        choices:
                            - enable
                            - disable
            redistribute6:
                description:
                    - BGP IPv6 redistribute table.
                type: list
                suboptions:
                    name:
                        description:
                            - Distribute list entry name.
                        required: true
                        type: str
                    route_map:
                        description:
                            - Route map name. Source router.route-map.name.
                        type: str
                    status:
                        description:
                            - Status
                        type: str
                        choices:
                            - enable
                            - disable
            router_id:
                description:
                    - Router ID.
                type: str
            scan_time:
                description:
                    - Background scanner interval (sec), 0 to disable it.
                type: int
            synchronization:
                description:
                    - Enable/disable only advertise routes from iBGP if routes present in an IGP.
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
  - name: Configure BGP.
    fortios_router_bgp:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_bgp:
        admin_distance:
         -
            distance: "4"
            id:  "5"
            neighbour_prefix: "<your_own_value>"
            route_list: "<your_own_value> (source router.access-list.name)"
        aggregate_address:
         -
            as_set: "enable"
            id:  "10"
            prefix: "<your_own_value>"
            summary_only: "enable"
        aggregate_address6:
         -
            as_set: "enable"
            id:  "15"
            prefix6: "<your_own_value>"
            summary_only: "enable"
        always_compare_med: "enable"
        as: "19"
        bestpath_as_path_ignore: "enable"
        bestpath_cmp_confed_aspath: "enable"
        bestpath_cmp_routerid: "enable"
        bestpath_med_confed: "enable"
        bestpath_med_missing_as_worst: "enable"
        client_to_client_reflection: "enable"
        cluster_id: "<your_own_value>"
        confederation_identifier: "27"
        confederation_peers:
         -
            peer: "<your_own_value>"
        dampening: "enable"
        dampening_max_suppress_time: "31"
        dampening_reachability_half_life: "32"
        dampening_reuse: "33"
        dampening_route_map: "<your_own_value> (source router.route-map.name)"
        dampening_suppress: "35"
        dampening_unreachability_half_life: "36"
        default_local_preference: "37"
        deterministic_med: "enable"
        distance_external: "39"
        distance_internal: "40"
        distance_local: "41"
        ebgp_multipath: "enable"
        enforce_first_as: "enable"
        fast_external_failover: "enable"
        graceful_end_on_timer: "enable"
        graceful_restart: "enable"
        graceful_restart_time: "47"
        graceful_stalepath_time: "48"
        graceful_update_delay: "49"
        holdtime_timer: "50"
        ibgp_multipath: "enable"
        ignore_optional_capability: "enable"
        keepalive_timer: "53"
        log_neighbour_changes: "enable"
        neighbor:
         -
            activate: "enable"
            activate6: "enable"
            advertisement_interval: "58"
            allowas_in: "59"
            allowas_in_enable: "enable"
            allowas_in_enable6: "enable"
            allowas_in6: "62"
            as_override: "enable"
            as_override6: "enable"
            attribute_unchanged: "as-path"
            attribute_unchanged6: "as-path"
            bfd: "enable"
            capability_default_originate: "enable"
            capability_default_originate6: "enable"
            capability_dynamic: "enable"
            capability_graceful_restart: "enable"
            capability_graceful_restart6: "enable"
            capability_orf: "none"
            capability_orf6: "none"
            capability_route_refresh: "enable"
            conditional_advertise:
             -
                advertise_routemap: "<your_own_value> (source router.route-map.name)"
                condition_routemap: "<your_own_value> (source router.route-map.name)"
                condition_type: "exist"
            connect_timer: "80"
            default_originate_routemap: "<your_own_value> (source router.route-map.name)"
            default_originate_routemap6: "<your_own_value> (source router.route-map.name)"
            description: "<your_own_value>"
            distribute_list_in: "<your_own_value> (source router.access-list.name)"
            distribute_list_in6: "<your_own_value> (source router.access-list6.name)"
            distribute_list_out: "<your_own_value> (source router.access-list.name)"
            distribute_list_out6: "<your_own_value> (source router.access-list6.name)"
            dont_capability_negotiate: "enable"
            ebgp_enforce_multihop: "enable"
            ebgp_multihop_ttl: "90"
            filter_list_in: "<your_own_value> (source router.aspath-list.name)"
            filter_list_in6: "<your_own_value> (source router.aspath-list.name)"
            filter_list_out: "<your_own_value> (source router.aspath-list.name)"
            filter_list_out6: "<your_own_value> (source router.aspath-list.name)"
            holdtime_timer: "95"
            interface: "<your_own_value> (source system.interface.name)"
            ip: "<your_own_value>"
            keep_alive_timer: "98"
            link_down_failover: "enable"
            local_as: "100"
            local_as_no_prepend: "enable"
            local_as_replace_as: "enable"
            maximum_prefix: "103"
            maximum_prefix_threshold: "104"
            maximum_prefix_threshold6: "105"
            maximum_prefix_warning_only: "enable"
            maximum_prefix_warning_only6: "enable"
            maximum_prefix6: "108"
            next_hop_self: "enable"
            next_hop_self6: "enable"
            override_capability: "enable"
            passive: "enable"
            password: "<your_own_value>"
            prefix_list_in: "<your_own_value> (source router.prefix-list.name)"
            prefix_list_in6: "<your_own_value> (source router.prefix-list6.name)"
            prefix_list_out: "<your_own_value> (source router.prefix-list.name)"
            prefix_list_out6: "<your_own_value> (source router.prefix-list6.name)"
            remote_as: "118"
            remove_private_as: "enable"
            remove_private_as6: "enable"
            restart_time: "121"
            retain_stale_time: "122"
            route_map_in: "<your_own_value> (source router.route-map.name)"
            route_map_in6: "<your_own_value> (source router.route-map.name)"
            route_map_out: "<your_own_value> (source router.route-map.name)"
            route_map_out6: "<your_own_value> (source router.route-map.name)"
            route_reflector_client: "enable"
            route_reflector_client6: "enable"
            route_server_client: "enable"
            route_server_client6: "enable"
            send_community: "standard"
            send_community6: "standard"
            shutdown: "enable"
            soft_reconfiguration: "enable"
            soft_reconfiguration6: "enable"
            stale_route: "enable"
            strict_capability_match: "enable"
            unsuppress_map: "<your_own_value> (source router.route-map.name)"
            unsuppress_map6: "<your_own_value> (source router.route-map.name)"
            update_source: "<your_own_value> (source system.interface.name)"
            weight: "141"
        neighbor_group:
         -
            activate: "enable"
            activate6: "enable"
            advertisement_interval: "145"
            allowas_in: "146"
            allowas_in_enable: "enable"
            allowas_in_enable6: "enable"
            allowas_in6: "149"
            as_override: "enable"
            as_override6: "enable"
            attribute_unchanged: "as-path"
            attribute_unchanged6: "as-path"
            bfd: "enable"
            capability_default_originate: "enable"
            capability_default_originate6: "enable"
            capability_dynamic: "enable"
            capability_graceful_restart: "enable"
            capability_graceful_restart6: "enable"
            capability_orf: "none"
            capability_orf6: "none"
            capability_route_refresh: "enable"
            connect_timer: "163"
            default_originate_routemap: "<your_own_value> (source router.route-map.name)"
            default_originate_routemap6: "<your_own_value> (source router.route-map.name)"
            description: "<your_own_value>"
            distribute_list_in: "<your_own_value> (source router.access-list.name)"
            distribute_list_in6: "<your_own_value> (source router.access-list6.name)"
            distribute_list_out: "<your_own_value> (source router.access-list.name)"
            distribute_list_out6: "<your_own_value> (source router.access-list6.name)"
            dont_capability_negotiate: "enable"
            ebgp_enforce_multihop: "enable"
            ebgp_multihop_ttl: "173"
            filter_list_in: "<your_own_value> (source router.aspath-list.name)"
            filter_list_in6: "<your_own_value> (source router.aspath-list.name)"
            filter_list_out: "<your_own_value> (source router.aspath-list.name)"
            filter_list_out6: "<your_own_value> (source router.aspath-list.name)"
            holdtime_timer: "178"
            interface: "<your_own_value> (source system.interface.name)"
            keep_alive_timer: "180"
            link_down_failover: "enable"
            local_as: "182"
            local_as_no_prepend: "enable"
            local_as_replace_as: "enable"
            maximum_prefix: "185"
            maximum_prefix_threshold: "186"
            maximum_prefix_threshold6: "187"
            maximum_prefix_warning_only: "enable"
            maximum_prefix_warning_only6: "enable"
            maximum_prefix6: "190"
            name: "default_name_191"
            next_hop_self: "enable"
            next_hop_self6: "enable"
            override_capability: "enable"
            passive: "enable"
            prefix_list_in: "<your_own_value> (source router.prefix-list.name)"
            prefix_list_in6: "<your_own_value> (source router.prefix-list6.name)"
            prefix_list_out: "<your_own_value> (source router.prefix-list.name)"
            prefix_list_out6: "<your_own_value> (source router.prefix-list6.name)"
            remote_as: "200"
            remove_private_as: "enable"
            remove_private_as6: "enable"
            restart_time: "203"
            retain_stale_time: "204"
            route_map_in: "<your_own_value> (source router.route-map.name)"
            route_map_in6: "<your_own_value> (source router.route-map.name)"
            route_map_out: "<your_own_value> (source router.route-map.name)"
            route_map_out6: "<your_own_value> (source router.route-map.name)"
            route_reflector_client: "enable"
            route_reflector_client6: "enable"
            route_server_client: "enable"
            route_server_client6: "enable"
            send_community: "standard"
            send_community6: "standard"
            shutdown: "enable"
            soft_reconfiguration: "enable"
            soft_reconfiguration6: "enable"
            stale_route: "enable"
            strict_capability_match: "enable"
            unsuppress_map: "<your_own_value> (source router.route-map.name)"
            unsuppress_map6: "<your_own_value> (source router.route-map.name)"
            update_source: "<your_own_value> (source system.interface.name)"
            weight: "223"
        neighbor_range:
         -
            id:  "225"
            max_neighbor_num: "226"
            neighbor_group: "<your_own_value> (source router.bgp.neighbor-group.name)"
            prefix: "<your_own_value>"
        neighbor_range6:
         -
            id:  "230"
            max_neighbor_num: "231"
            neighbor_group: "<your_own_value> (source router.bgp.neighbor-group.name)"
            prefix6: "<your_own_value>"
        network:
         -
            backdoor: "enable"
            id:  "236"
            prefix: "<your_own_value>"
            route_map: "<your_own_value> (source router.route-map.name)"
        network_import_check: "enable"
        network6:
         -
            backdoor: "enable"
            id:  "242"
            prefix6: "<your_own_value>"
            route_map: "<your_own_value> (source router.route-map.name)"
        redistribute:
         -
            name: "default_name_246"
            route_map: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        redistribute6:
         -
            name: "default_name_250"
            route_map: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        router_id: "<your_own_value>"
        scan_time: "254"
        synchronization: "enable"
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


def filter_router_bgp_data(json):
    option_list = ['admin_distance', 'aggregate_address', 'aggregate_address6',
                   'always_compare_med', 'as', 'bestpath_as_path_ignore',
                   'bestpath_cmp_confed_aspath', 'bestpath_cmp_routerid', 'bestpath_med_confed',
                   'bestpath_med_missing_as_worst', 'client_to_client_reflection', 'cluster_id',
                   'confederation_identifier', 'confederation_peers', 'dampening',
                   'dampening_max_suppress_time', 'dampening_reachability_half_life', 'dampening_reuse',
                   'dampening_route_map', 'dampening_suppress', 'dampening_unreachability_half_life',
                   'default_local_preference', 'deterministic_med', 'distance_external',
                   'distance_internal', 'distance_local', 'ebgp_multipath',
                   'enforce_first_as', 'fast_external_failover', 'graceful_end_on_timer',
                   'graceful_restart', 'graceful_restart_time', 'graceful_stalepath_time',
                   'graceful_update_delay', 'holdtime_timer', 'ibgp_multipath',
                   'ignore_optional_capability', 'keepalive_timer', 'log_neighbour_changes',
                   'neighbor', 'neighbor_group', 'neighbor_range',
                   'neighbor_range6', 'network', 'network_import_check',
                   'network6', 'redistribute', 'redistribute6',
                   'router_id', 'scan_time', 'synchronization']
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


def router_bgp(data, fos):
    vdom = data['vdom']
    router_bgp_data = data['router_bgp']
    filtered_data = underscore_to_hyphen(filter_router_bgp_data(router_bgp_data))

    return fos.set('router',
                   'bgp',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_router(data, fos):

    if data['router_bgp']:
        resp = router_bgp(data, fos)

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
        "router_bgp": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "admin_distance": {"required": False, "type": "list",
                                   "options": {
                                       "distance": {"required": False, "type": "int"},
                                       "id": {"required": True, "type": "int"},
                                       "neighbour_prefix": {"required": False, "type": "str"},
                                       "route_list": {"required": False, "type": "str"}
                                   }},
                "aggregate_address": {"required": False, "type": "list",
                                      "options": {
                                          "as_set": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                          "id": {"required": True, "type": "int"},
                                          "prefix": {"required": False, "type": "str"},
                                          "summary_only": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]}
                                      }},
                "aggregate_address6": {"required": False, "type": "list",
                                       "options": {
                                           "as_set": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                           "id": {"required": True, "type": "int"},
                                           "prefix6": {"required": False, "type": "str"},
                                           "summary_only": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]}
                                       }},
                "always_compare_med": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "as": {"required": False, "type": "int"},
                "bestpath_as_path_ignore": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "bestpath_cmp_confed_aspath": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "bestpath_cmp_routerid": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "bestpath_med_confed": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "bestpath_med_missing_as_worst": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "client_to_client_reflection": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "cluster_id": {"required": False, "type": "str"},
                "confederation_identifier": {"required": False, "type": "int"},
                "confederation_peers": {"required": False, "type": "list",
                                        "options": {
                                            "peer": {"required": True, "type": "str"}
                                        }},
                "dampening": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "dampening_max_suppress_time": {"required": False, "type": "int"},
                "dampening_reachability_half_life": {"required": False, "type": "int"},
                "dampening_reuse": {"required": False, "type": "int"},
                "dampening_route_map": {"required": False, "type": "str"},
                "dampening_suppress": {"required": False, "type": "int"},
                "dampening_unreachability_half_life": {"required": False, "type": "int"},
                "default_local_preference": {"required": False, "type": "int"},
                "deterministic_med": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "distance_external": {"required": False, "type": "int"},
                "distance_internal": {"required": False, "type": "int"},
                "distance_local": {"required": False, "type": "int"},
                "ebgp_multipath": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "enforce_first_as": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "fast_external_failover": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "graceful_end_on_timer": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "graceful_restart": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "graceful_restart_time": {"required": False, "type": "int"},
                "graceful_stalepath_time": {"required": False, "type": "int"},
                "graceful_update_delay": {"required": False, "type": "int"},
                "holdtime_timer": {"required": False, "type": "int"},
                "ibgp_multipath": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "ignore_optional_capability": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "keepalive_timer": {"required": False, "type": "int"},
                "log_neighbour_changes": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "neighbor": {"required": False, "type": "list",
                             "options": {
                                 "activate": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                 "activate6": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                 "advertisement_interval": {"required": False, "type": "int"},
                                 "allowas_in": {"required": False, "type": "int"},
                                 "allowas_in_enable": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                 "allowas_in_enable6": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                 "allowas_in6": {"required": False, "type": "int"},
                                 "as_override": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                 "as_override6": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                 "attribute_unchanged": {"required": False, "type": "str",
                                                         "choices": ["as-path", "med", "next-hop"]},
                                 "attribute_unchanged6": {"required": False, "type": "str",
                                                          "choices": ["as-path", "med", "next-hop"]},
                                 "bfd": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                                 "capability_default_originate": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                 "capability_default_originate6": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                 "capability_dynamic": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                 "capability_graceful_restart": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                 "capability_graceful_restart6": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                 "capability_orf": {"required": False, "type": "str",
                                                    "choices": ["none", "receive", "send",
                                                                "both"]},
                                 "capability_orf6": {"required": False, "type": "str",
                                                     "choices": ["none", "receive", "send",
                                                                 "both"]},
                                 "capability_route_refresh": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                 "conditional_advertise": {"required": False, "type": "list",
                                                           "options": {
                                                               "advertise_routemap": {"required": False, "type": "str"},
                                                               "condition_routemap": {"required": False, "type": "str"},
                                                               "condition_type": {"required": False, "type": "str",
                                                                                  "choices": ["exist", "non-exist"]}
                                                           }},
                                 "connect_timer": {"required": False, "type": "int"},
                                 "default_originate_routemap": {"required": False, "type": "str"},
                                 "default_originate_routemap6": {"required": False, "type": "str"},
                                 "description": {"required": False, "type": "str"},
                                 "distribute_list_in": {"required": False, "type": "str"},
                                 "distribute_list_in6": {"required": False, "type": "str"},
                                 "distribute_list_out": {"required": False, "type": "str"},
                                 "distribute_list_out6": {"required": False, "type": "str"},
                                 "dont_capability_negotiate": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                 "ebgp_enforce_multihop": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                 "ebgp_multihop_ttl": {"required": False, "type": "int"},
                                 "filter_list_in": {"required": False, "type": "str"},
                                 "filter_list_in6": {"required": False, "type": "str"},
                                 "filter_list_out": {"required": False, "type": "str"},
                                 "filter_list_out6": {"required": False, "type": "str"},
                                 "holdtime_timer": {"required": False, "type": "int"},
                                 "interface": {"required": False, "type": "str"},
                                 "ip": {"required": True, "type": "str"},
                                 "keep_alive_timer": {"required": False, "type": "int"},
                                 "link_down_failover": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                 "local_as": {"required": False, "type": "int"},
                                 "local_as_no_prepend": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                 "local_as_replace_as": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                 "maximum_prefix": {"required": False, "type": "int"},
                                 "maximum_prefix_threshold": {"required": False, "type": "int"},
                                 "maximum_prefix_threshold6": {"required": False, "type": "int"},
                                 "maximum_prefix_warning_only": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                 "maximum_prefix_warning_only6": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                 "maximum_prefix6": {"required": False, "type": "int"},
                                 "next_hop_self": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                 "next_hop_self6": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                 "override_capability": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                 "passive": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                                 "password": {"required": False, "type": "str", "no_log": True},
                                 "prefix_list_in": {"required": False, "type": "str"},
                                 "prefix_list_in6": {"required": False, "type": "str"},
                                 "prefix_list_out": {"required": False, "type": "str"},
                                 "prefix_list_out6": {"required": False, "type": "str"},
                                 "remote_as": {"required": False, "type": "int"},
                                 "remove_private_as": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                 "remove_private_as6": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                 "restart_time": {"required": False, "type": "int"},
                                 "retain_stale_time": {"required": False, "type": "int"},
                                 "route_map_in": {"required": False, "type": "str"},
                                 "route_map_in6": {"required": False, "type": "str"},
                                 "route_map_out": {"required": False, "type": "str"},
                                 "route_map_out6": {"required": False, "type": "str"},
                                 "route_reflector_client": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                                 "route_reflector_client6": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                 "route_server_client": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                 "route_server_client6": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                 "send_community": {"required": False, "type": "str",
                                                    "choices": ["standard", "extended", "both",
                                                                "disable"]},
                                 "send_community6": {"required": False, "type": "str",
                                                     "choices": ["standard", "extended", "both",
                                                                 "disable"]},
                                 "shutdown": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                 "soft_reconfiguration": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                 "soft_reconfiguration6": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                 "stale_route": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                 "strict_capability_match": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                 "unsuppress_map": {"required": False, "type": "str"},
                                 "unsuppress_map6": {"required": False, "type": "str"},
                                 "update_source": {"required": False, "type": "str"},
                                 "weight": {"required": False, "type": "int"}
                             }},
                "neighbor_group": {"required": False, "type": "list",
                                   "options": {
                                       "activate": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                       "activate6": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                       "advertisement_interval": {"required": False, "type": "int"},
                                       "allowas_in": {"required": False, "type": "int"},
                                       "allowas_in_enable": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                       "allowas_in_enable6": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                       "allowas_in6": {"required": False, "type": "int"},
                                       "as_override": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                       "as_override6": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                       "attribute_unchanged": {"required": False, "type": "str",
                                                               "choices": ["as-path", "med", "next-hop"]},
                                       "attribute_unchanged6": {"required": False, "type": "str",
                                                                "choices": ["as-path", "med", "next-hop"]},
                                       "bfd": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                       "capability_default_originate": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                       "capability_default_originate6": {"required": False, "type": "str",
                                                                         "choices": ["enable", "disable"]},
                                       "capability_dynamic": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                       "capability_graceful_restart": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                       "capability_graceful_restart6": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                       "capability_orf": {"required": False, "type": "str",
                                                          "choices": ["none", "receive", "send",
                                                                      "both"]},
                                       "capability_orf6": {"required": False, "type": "str",
                                                           "choices": ["none", "receive", "send",
                                                                       "both"]},
                                       "capability_route_refresh": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
                                       "connect_timer": {"required": False, "type": "int"},
                                       "default_originate_routemap": {"required": False, "type": "str"},
                                       "default_originate_routemap6": {"required": False, "type": "str"},
                                       "description": {"required": False, "type": "str"},
                                       "distribute_list_in": {"required": False, "type": "str"},
                                       "distribute_list_in6": {"required": False, "type": "str"},
                                       "distribute_list_out": {"required": False, "type": "str"},
                                       "distribute_list_out6": {"required": False, "type": "str"},
                                       "dont_capability_negotiate": {"required": False, "type": "str",
                                                                     "choices": ["enable", "disable"]},
                                       "ebgp_enforce_multihop": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                       "ebgp_multihop_ttl": {"required": False, "type": "int"},
                                       "filter_list_in": {"required": False, "type": "str"},
                                       "filter_list_in6": {"required": False, "type": "str"},
                                       "filter_list_out": {"required": False, "type": "str"},
                                       "filter_list_out6": {"required": False, "type": "str"},
                                       "holdtime_timer": {"required": False, "type": "int"},
                                       "interface": {"required": False, "type": "str"},
                                       "keep_alive_timer": {"required": False, "type": "int"},
                                       "link_down_failover": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                       "local_as": {"required": False, "type": "int"},
                                       "local_as_no_prepend": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "local_as_replace_as": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "maximum_prefix": {"required": False, "type": "int"},
                                       "maximum_prefix_threshold": {"required": False, "type": "int"},
                                       "maximum_prefix_threshold6": {"required": False, "type": "int"},
                                       "maximum_prefix_warning_only": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                       "maximum_prefix_warning_only6": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                       "maximum_prefix6": {"required": False, "type": "int"},
                                       "name": {"required": True, "type": "str"},
                                       "next_hop_self": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                       "next_hop_self6": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                       "override_capability": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "passive": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                       "prefix_list_in": {"required": False, "type": "str"},
                                       "prefix_list_in6": {"required": False, "type": "str"},
                                       "prefix_list_out": {"required": False, "type": "str"},
                                       "prefix_list_out6": {"required": False, "type": "str"},
                                       "remote_as": {"required": False, "type": "int"},
                                       "remove_private_as": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                       "remove_private_as6": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                       "restart_time": {"required": False, "type": "int"},
                                       "retain_stale_time": {"required": False, "type": "int"},
                                       "route_map_in": {"required": False, "type": "str"},
                                       "route_map_in6": {"required": False, "type": "str"},
                                       "route_map_out": {"required": False, "type": "str"},
                                       "route_map_out6": {"required": False, "type": "str"},
                                       "route_reflector_client": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                       "route_reflector_client6": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                       "route_server_client": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "route_server_client6": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                       "send_community": {"required": False, "type": "str",
                                                          "choices": ["standard", "extended", "both",
                                                                      "disable"]},
                                       "send_community6": {"required": False, "type": "str",
                                                           "choices": ["standard", "extended", "both",
                                                                       "disable"]},
                                       "shutdown": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                       "soft_reconfiguration": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                       "soft_reconfiguration6": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                       "stale_route": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                       "strict_capability_match": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                       "unsuppress_map": {"required": False, "type": "str"},
                                       "unsuppress_map6": {"required": False, "type": "str"},
                                       "update_source": {"required": False, "type": "str"},
                                       "weight": {"required": False, "type": "int"}
                                   }},
                "neighbor_range": {"required": False, "type": "list",
                                   "options": {
                                       "id": {"required": True, "type": "int"},
                                       "max_neighbor_num": {"required": False, "type": "int"},
                                       "neighbor_group": {"required": False, "type": "str"},
                                       "prefix": {"required": False, "type": "str"}
                                   }},
                "neighbor_range6": {"required": False, "type": "list",
                                    "options": {
                                        "id": {"required": True, "type": "int"},
                                        "max_neighbor_num": {"required": False, "type": "int"},
                                        "neighbor_group": {"required": False, "type": "str"},
                                        "prefix6": {"required": False, "type": "str"}
                                    }},
                "network": {"required": False, "type": "list",
                            "options": {
                                "backdoor": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                                "id": {"required": True, "type": "int"},
                                "prefix": {"required": False, "type": "str"},
                                "route_map": {"required": False, "type": "str"}
                            }},
                "network_import_check": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "network6": {"required": False, "type": "list",
                             "options": {
                                 "backdoor": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                 "id": {"required": True, "type": "int"},
                                 "prefix6": {"required": False, "type": "str"},
                                 "route_map": {"required": False, "type": "str"}
                             }},
                "redistribute": {"required": False, "type": "list",
                                 "options": {
                                     "name": {"required": True, "type": "str"},
                                     "route_map": {"required": False, "type": "str"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]}
                                 }},
                "redistribute6": {"required": False, "type": "list",
                                  "options": {
                                      "name": {"required": True, "type": "str"},
                                      "route_map": {"required": False, "type": "str"},
                                      "status": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]}
                                  }},
                "router_id": {"required": False, "type": "str"},
                "scan_time": {"required": False, "type": "int"},
                "synchronization": {"required": False, "type": "str",
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
