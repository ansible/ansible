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
module: fortios_router_bgp
short_description: Configure BGP in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify router feature and bgp category.
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
    router_bgp:
        description:
            - Configure BGP.
        default: null
        suboptions:
            admin-distance:
                description:
                    - Administrative distance modifications.
                suboptions:
                    distance:
                        description:
                            - Administrative distance to apply (1 - 255).
                    id:
                        description:
                            - ID.
                        required: true
                    neighbour-prefix:
                        description:
                            - Neighbor address prefix.
                    route-list:
                        description:
                            - Access list of routes to apply new distance to. Source router.access-list.name.
            aggregate-address:
                description:
                    - BGP aggregate address table.
                suboptions:
                    as-set:
                        description:
                            - Enable/disable generate AS set path information.
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - ID.
                        required: true
                    prefix:
                        description:
                            - Aggregate prefix.
                    summary-only:
                        description:
                            - Enable/disable filter more specific routes from updates.
                        choices:
                            - enable
                            - disable
            aggregate-address6:
                description:
                    - BGP IPv6 aggregate address table.
                suboptions:
                    as-set:
                        description:
                            - Enable/disable generate AS set path information.
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - ID.
                        required: true
                    prefix6:
                        description:
                            - Aggregate IPv6 prefix.
                    summary-only:
                        description:
                            - Enable/disable filter more specific routes from updates.
                        choices:
                            - enable
                            - disable
            always-compare-med:
                description:
                    - Enable/disable always compare MED.
                choices:
                    - enable
                    - disable
            as:
                description:
                    - Router AS number, valid from 1 to 4294967295, 0 to disable BGP.
            bestpath-as-path-ignore:
                description:
                    - Enable/disable ignore AS path.
                choices:
                    - enable
                    - disable
            bestpath-cmp-confed-aspath:
                description:
                    - Enable/disable compare federation AS path length.
                choices:
                    - enable
                    - disable
            bestpath-cmp-routerid:
                description:
                    - Enable/disable compare router ID for identical EBGP paths.
                choices:
                    - enable
                    - disable
            bestpath-med-confed:
                description:
                    - Enable/disable compare MED among confederation paths.
                choices:
                    - enable
                    - disable
            bestpath-med-missing-as-worst:
                description:
                    - Enable/disable treat missing MED as least preferred.
                choices:
                    - enable
                    - disable
            client-to-client-reflection:
                description:
                    - Enable/disable client-to-client route reflection.
                choices:
                    - enable
                    - disable
            cluster-id:
                description:
                    - Route reflector cluster ID.
            confederation-identifier:
                description:
                    - Confederation identifier.
            confederation-peers:
                description:
                    - Confederation peers.
                suboptions:
                    peer:
                        description:
                            - Peer ID.
                        required: true
            dampening:
                description:
                    - Enable/disable route-flap dampening.
                choices:
                    - enable
                    - disable
            dampening-max-suppress-time:
                description:
                    - Maximum minutes a route can be suppressed.
            dampening-reachability-half-life:
                description:
                    - Reachability half-life time for penalty (min).
            dampening-reuse:
                description:
                    - Threshold to reuse routes.
            dampening-route-map:
                description:
                    - Criteria for dampening. Source router.route-map.name.
            dampening-suppress:
                description:
                    - Threshold to suppress routes.
            dampening-unreachability-half-life:
                description:
                    - Unreachability half-life time for penalty (min).
            default-local-preference:
                description:
                    - Default local preference.
            deterministic-med:
                description:
                    - Enable/disable enforce deterministic comparison of MED.
                choices:
                    - enable
                    - disable
            distance-external:
                description:
                    - Distance for routes external to the AS.
            distance-internal:
                description:
                    - Distance for routes internal to the AS.
            distance-local:
                description:
                    - Distance for routes local to the AS.
            ebgp-multipath:
                description:
                    - Enable/disable EBGP multi-path.
                choices:
                    - enable
                    - disable
            enforce-first-as:
                description:
                    - Enable/disable enforce first AS for EBGP routes.
                choices:
                    - enable
                    - disable
            fast-external-failover:
                description:
                    - Enable/disable reset peer BGP session if link goes down.
                choices:
                    - enable
                    - disable
            graceful-end-on-timer:
                description:
                    - Enable/disable to exit graceful restart on timer only.
                choices:
                    - enable
                    - disable
            graceful-restart:
                description:
                    - Enable/disable BGP graceful restart capabilities.
                choices:
                    - enable
                    - disable
            graceful-restart-time:
                description:
                    - Time needed for neighbors to restart (sec).
            graceful-stalepath-time:
                description:
                    - Time to hold stale paths of restarting neighbor (sec).
            graceful-update-delay:
                description:
                    - Route advertisement/selection delay after restart (sec).
            holdtime-timer:
                description:
                    - Number of seconds to mark peer as dead.
            ibgp-multipath:
                description:
                    - Enable/disable IBGP multi-path.
                choices:
                    - enable
                    - disable
            ignore-optional-capability:
                description:
                    - Don't send unknown optional capability notification message
                choices:
                    - enable
                    - disable
            keepalive-timer:
                description:
                    - Frequency to send keep alive requests.
            log-neighbour-changes:
                description:
                    - Enable logging of BGP neighbour's changes
                choices:
                    - enable
                    - disable
            neighbor:
                description:
                    - BGP neighbor table.
                suboptions:
                    activate:
                        description:
                            - Enable/disable address family IPv4 for this neighbor.
                        choices:
                            - enable
                            - disable
                    activate6:
                        description:
                            - Enable/disable address family IPv6 for this neighbor.
                        choices:
                            - enable
                            - disable
                    advertisement-interval:
                        description:
                            - Minimum interval (sec) between sending updates.
                    allowas-in:
                        description:
                            - IPv4 The maximum number of occurrence of my AS number allowed.
                    allowas-in-enable:
                        description:
                            - Enable/disable IPv4 Enable to allow my AS in AS path.
                        choices:
                            - enable
                            - disable
                    allowas-in-enable6:
                        description:
                            - Enable/disable IPv6 Enable to allow my AS in AS path.
                        choices:
                            - enable
                            - disable
                    allowas-in6:
                        description:
                            - IPv6 The maximum number of occurrence of my AS number allowed.
                    as-override:
                        description:
                            - Enable/disable replace peer AS with own AS for IPv4.
                        choices:
                            - enable
                            - disable
                    as-override6:
                        description:
                            - Enable/disable replace peer AS with own AS for IPv6.
                        choices:
                            - enable
                            - disable
                    attribute-unchanged:
                        description:
                            - IPv4 List of attributes that should be unchanged.
                        choices:
                            - as-path
                            - med
                            - next-hop
                    attribute-unchanged6:
                        description:
                            - IPv6 List of attributes that should be unchanged.
                        choices:
                            - as-path
                            - med
                            - next-hop
                    bfd:
                        description:
                            - Enable/disable BFD for this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-default-originate:
                        description:
                            - Enable/disable advertise default IPv4 route to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-default-originate6:
                        description:
                            - Enable/disable advertise default IPv6 route to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-dynamic:
                        description:
                            - Enable/disable advertise dynamic capability to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-graceful-restart:
                        description:
                            - Enable/disable advertise IPv4 graceful restart capability to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-graceful-restart6:
                        description:
                            - Enable/disable advertise IPv6 graceful restart capability to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-orf:
                        description:
                            - Accept/Send IPv4 ORF lists to/from this neighbor.
                        choices:
                            - none
                            - receive
                            - send
                            - both
                    capability-orf6:
                        description:
                            - Accept/Send IPv6 ORF lists to/from this neighbor.
                        choices:
                            - none
                            - receive
                            - send
                            - both
                    capability-route-refresh:
                        description:
                            - Enable/disable advertise route refresh capability to this neighbor.
                        choices:
                            - enable
                            - disable
                    conditional-advertise:
                        description:
                            - Conditional advertisement.
                        suboptions:
                            advertise-routemap:
                                description:
                                    - Name of advertising route map. Source router.route-map.name.
                                required: true
                            condition-routemap:
                                description:
                                    - Name of condition route map. Source router.route-map.name.
                            condition-type:
                                description:
                                    - Type of condition.
                                choices:
                                    - exist
                                    - non-exist
                    connect-timer:
                        description:
                            - Interval (sec) for connect timer.
                    default-originate-routemap:
                        description:
                            - Route map to specify criteria to originate IPv4 default. Source router.route-map.name.
                    default-originate-routemap6:
                        description:
                            - Route map to specify criteria to originate IPv6 default. Source router.route-map.name.
                    description:
                        description:
                            - Description.
                    distribute-list-in:
                        description:
                            - Filter for IPv4 updates from this neighbor. Source router.access-list.name.
                    distribute-list-in6:
                        description:
                            - Filter for IPv6 updates from this neighbor. Source router.access-list6.name.
                    distribute-list-out:
                        description:
                            - Filter for IPv4 updates to this neighbor. Source router.access-list.name.
                    distribute-list-out6:
                        description:
                            - Filter for IPv6 updates to this neighbor. Source router.access-list6.name.
                    dont-capability-negotiate:
                        description:
                            - Don't negotiate capabilities with this neighbor
                        choices:
                            - enable
                            - disable
                    ebgp-enforce-multihop:
                        description:
                            - Enable/disable allow multi-hop EBGP neighbors.
                        choices:
                            - enable
                            - disable
                    ebgp-multihop-ttl:
                        description:
                            - EBGP multihop TTL for this peer.
                    filter-list-in:
                        description:
                            - BGP filter for IPv4 inbound routes. Source router.aspath-list.name.
                    filter-list-in6:
                        description:
                            - BGP filter for IPv6 inbound routes. Source router.aspath-list.name.
                    filter-list-out:
                        description:
                            - BGP filter for IPv4 outbound routes. Source router.aspath-list.name.
                    filter-list-out6:
                        description:
                            - BGP filter for IPv6 outbound routes. Source router.aspath-list.name.
                    holdtime-timer:
                        description:
                            - Interval (sec) before peer considered dead.
                    interface:
                        description:
                            - Interface Source system.interface.name.
                    ip:
                        description:
                            - IP/IPv6 address of neighbor.
                        required: true
                    keep-alive-timer:
                        description:
                            - Keep alive timer interval (sec).
                    link-down-failover:
                        description:
                            - Enable/disable failover upon link down.
                        choices:
                            - enable
                            - disable
                    local-as:
                        description:
                            - Local AS number of neighbor.
                    local-as-no-prepend:
                        description:
                            - Do not prepend local-as to incoming updates.
                        choices:
                            - enable
                            - disable
                    local-as-replace-as:
                        description:
                            - Replace real AS with local-as in outgoing updates.
                        choices:
                            - enable
                            - disable
                    maximum-prefix:
                        description:
                            - Maximum number of IPv4 prefixes to accept from this peer.
                    maximum-prefix-threshold:
                        description:
                            - Maximum IPv4 prefix threshold value (1 - 100 percent).
                    maximum-prefix-threshold6:
                        description:
                            - Maximum IPv6 prefix threshold value (1 - 100 percent).
                    maximum-prefix-warning-only:
                        description:
                            - Enable/disable IPv4 Only give warning message when limit is exceeded.
                        choices:
                            - enable
                            - disable
                    maximum-prefix-warning-only6:
                        description:
                            - Enable/disable IPv6 Only give warning message when limit is exceeded.
                        choices:
                            - enable
                            - disable
                    maximum-prefix6:
                        description:
                            - Maximum number of IPv6 prefixes to accept from this peer.
                    next-hop-self:
                        description:
                            - Enable/disable IPv4 next-hop calculation for this neighbor.
                        choices:
                            - enable
                            - disable
                    next-hop-self6:
                        description:
                            - Enable/disable IPv6 next-hop calculation for this neighbor.
                        choices:
                            - enable
                            - disable
                    override-capability:
                        description:
                            - Enable/disable override result of capability negotiation.
                        choices:
                            - enable
                            - disable
                    passive:
                        description:
                            - Enable/disable sending of open messages to this neighbor.
                        choices:
                            - enable
                            - disable
                    password:
                        description:
                            - Password used in MD5 authentication.
                    prefix-list-in:
                        description:
                            - IPv4 Inbound filter for updates from this neighbor. Source router.prefix-list.name.
                    prefix-list-in6:
                        description:
                            - IPv6 Inbound filter for updates from this neighbor. Source router.prefix-list6.name.
                    prefix-list-out:
                        description:
                            - IPv4 Outbound filter for updates to this neighbor. Source router.prefix-list.name.
                    prefix-list-out6:
                        description:
                            - IPv6 Outbound filter for updates to this neighbor. Source router.prefix-list6.name.
                    remote-as:
                        description:
                            - AS number of neighbor.
                    remove-private-as:
                        description:
                            - Enable/disable remove private AS number from IPv4 outbound updates.
                        choices:
                            - enable
                            - disable
                    remove-private-as6:
                        description:
                            - Enable/disable remove private AS number from IPv6 outbound updates.
                        choices:
                            - enable
                            - disable
                    restart-time:
                        description:
                            - Graceful restart delay time (sec, 0 = global default).
                    retain-stale-time:
                        description:
                            - Time to retain stale routes.
                    route-map-in:
                        description:
                            - IPv4 Inbound route map filter. Source router.route-map.name.
                    route-map-in6:
                        description:
                            - IPv6 Inbound route map filter. Source router.route-map.name.
                    route-map-out:
                        description:
                            - IPv4 Outbound route map filter. Source router.route-map.name.
                    route-map-out6:
                        description:
                            - IPv6 Outbound route map filter. Source router.route-map.name.
                    route-reflector-client:
                        description:
                            - Enable/disable IPv4 AS route reflector client.
                        choices:
                            - enable
                            - disable
                    route-reflector-client6:
                        description:
                            - Enable/disable IPv6 AS route reflector client.
                        choices:
                            - enable
                            - disable
                    route-server-client:
                        description:
                            - Enable/disable IPv4 AS route server client.
                        choices:
                            - enable
                            - disable
                    route-server-client6:
                        description:
                            - Enable/disable IPv6 AS route server client.
                        choices:
                            - enable
                            - disable
                    send-community:
                        description:
                            - IPv4 Send community attribute to neighbor.
                        choices:
                            - standard
                            - extended
                            - both
                            - disable
                    send-community6:
                        description:
                            - IPv6 Send community attribute to neighbor.
                        choices:
                            - standard
                            - extended
                            - both
                            - disable
                    shutdown:
                        description:
                            - Enable/disable shutdown this neighbor.
                        choices:
                            - enable
                            - disable
                    soft-reconfiguration:
                        description:
                            - Enable/disable allow IPv4 inbound soft reconfiguration.
                        choices:
                            - enable
                            - disable
                    soft-reconfiguration6:
                        description:
                            - Enable/disable allow IPv6 inbound soft reconfiguration.
                        choices:
                            - enable
                            - disable
                    stale-route:
                        description:
                            - Enable/disable stale route after neighbor down.
                        choices:
                            - enable
                            - disable
                    strict-capability-match:
                        description:
                            - Enable/disable strict capability matching.
                        choices:
                            - enable
                            - disable
                    unsuppress-map:
                        description:
                            - IPv4 Route map to selectively unsuppress suppressed routes. Source router.route-map.name.
                    unsuppress-map6:
                        description:
                            - IPv6 Route map to selectively unsuppress suppressed routes. Source router.route-map.name.
                    update-source:
                        description:
                            - Interface to use as source IP/IPv6 address of TCP connections. Source system.interface.name.
                    weight:
                        description:
                            - Neighbor weight.
            neighbor-group:
                description:
                    - BGP neighbor group table.
                suboptions:
                    activate:
                        description:
                            - Enable/disable address family IPv4 for this neighbor.
                        choices:
                            - enable
                            - disable
                    activate6:
                        description:
                            - Enable/disable address family IPv6 for this neighbor.
                        choices:
                            - enable
                            - disable
                    advertisement-interval:
                        description:
                            - Minimum interval (sec) between sending updates.
                    allowas-in:
                        description:
                            - IPv4 The maximum number of occurrence of my AS number allowed.
                    allowas-in-enable:
                        description:
                            - Enable/disable IPv4 Enable to allow my AS in AS path.
                        choices:
                            - enable
                            - disable
                    allowas-in-enable6:
                        description:
                            - Enable/disable IPv6 Enable to allow my AS in AS path.
                        choices:
                            - enable
                            - disable
                    allowas-in6:
                        description:
                            - IPv6 The maximum number of occurrence of my AS number allowed.
                    as-override:
                        description:
                            - Enable/disable replace peer AS with own AS for IPv4.
                        choices:
                            - enable
                            - disable
                    as-override6:
                        description:
                            - Enable/disable replace peer AS with own AS for IPv6.
                        choices:
                            - enable
                            - disable
                    attribute-unchanged:
                        description:
                            - IPv4 List of attributes that should be unchanged.
                        choices:
                            - as-path
                            - med
                            - next-hop
                    attribute-unchanged6:
                        description:
                            - IPv6 List of attributes that should be unchanged.
                        choices:
                            - as-path
                            - med
                            - next-hop
                    bfd:
                        description:
                            - Enable/disable BFD for this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-default-originate:
                        description:
                            - Enable/disable advertise default IPv4 route to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-default-originate6:
                        description:
                            - Enable/disable advertise default IPv6 route to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-dynamic:
                        description:
                            - Enable/disable advertise dynamic capability to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-graceful-restart:
                        description:
                            - Enable/disable advertise IPv4 graceful restart capability to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-graceful-restart6:
                        description:
                            - Enable/disable advertise IPv6 graceful restart capability to this neighbor.
                        choices:
                            - enable
                            - disable
                    capability-orf:
                        description:
                            - Accept/Send IPv4 ORF lists to/from this neighbor.
                        choices:
                            - none
                            - receive
                            - send
                            - both
                    capability-orf6:
                        description:
                            - Accept/Send IPv6 ORF lists to/from this neighbor.
                        choices:
                            - none
                            - receive
                            - send
                            - both
                    capability-route-refresh:
                        description:
                            - Enable/disable advertise route refresh capability to this neighbor.
                        choices:
                            - enable
                            - disable
                    connect-timer:
                        description:
                            - Interval (sec) for connect timer.
                    default-originate-routemap:
                        description:
                            - Route map to specify criteria to originate IPv4 default. Source router.route-map.name.
                    default-originate-routemap6:
                        description:
                            - Route map to specify criteria to originate IPv6 default. Source router.route-map.name.
                    description:
                        description:
                            - Description.
                    distribute-list-in:
                        description:
                            - Filter for IPv4 updates from this neighbor. Source router.access-list.name.
                    distribute-list-in6:
                        description:
                            - Filter for IPv6 updates from this neighbor. Source router.access-list6.name.
                    distribute-list-out:
                        description:
                            - Filter for IPv4 updates to this neighbor. Source router.access-list.name.
                    distribute-list-out6:
                        description:
                            - Filter for IPv6 updates to this neighbor. Source router.access-list6.name.
                    dont-capability-negotiate:
                        description:
                            - Don't negotiate capabilities with this neighbor
                        choices:
                            - enable
                            - disable
                    ebgp-enforce-multihop:
                        description:
                            - Enable/disable allow multi-hop EBGP neighbors.
                        choices:
                            - enable
                            - disable
                    ebgp-multihop-ttl:
                        description:
                            - EBGP multihop TTL for this peer.
                    filter-list-in:
                        description:
                            - BGP filter for IPv4 inbound routes. Source router.aspath-list.name.
                    filter-list-in6:
                        description:
                            - BGP filter for IPv6 inbound routes. Source router.aspath-list.name.
                    filter-list-out:
                        description:
                            - BGP filter for IPv4 outbound routes. Source router.aspath-list.name.
                    filter-list-out6:
                        description:
                            - BGP filter for IPv6 outbound routes. Source router.aspath-list.name.
                    holdtime-timer:
                        description:
                            - Interval (sec) before peer considered dead.
                    interface:
                        description:
                            - Interface Source system.interface.name.
                    keep-alive-timer:
                        description:
                            - Keep alive timer interval (sec).
                    link-down-failover:
                        description:
                            - Enable/disable failover upon link down.
                        choices:
                            - enable
                            - disable
                    local-as:
                        description:
                            - Local AS number of neighbor.
                    local-as-no-prepend:
                        description:
                            - Do not prepend local-as to incoming updates.
                        choices:
                            - enable
                            - disable
                    local-as-replace-as:
                        description:
                            - Replace real AS with local-as in outgoing updates.
                        choices:
                            - enable
                            - disable
                    maximum-prefix:
                        description:
                            - Maximum number of IPv4 prefixes to accept from this peer.
                    maximum-prefix-threshold:
                        description:
                            - Maximum IPv4 prefix threshold value (1 - 100 percent).
                    maximum-prefix-threshold6:
                        description:
                            - Maximum IPv6 prefix threshold value (1 - 100 percent).
                    maximum-prefix-warning-only:
                        description:
                            - Enable/disable IPv4 Only give warning message when limit is exceeded.
                        choices:
                            - enable
                            - disable
                    maximum-prefix-warning-only6:
                        description:
                            - Enable/disable IPv6 Only give warning message when limit is exceeded.
                        choices:
                            - enable
                            - disable
                    maximum-prefix6:
                        description:
                            - Maximum number of IPv6 prefixes to accept from this peer.
                    name:
                        description:
                            - Neighbor group name.
                        required: true
                    next-hop-self:
                        description:
                            - Enable/disable IPv4 next-hop calculation for this neighbor.
                        choices:
                            - enable
                            - disable
                    next-hop-self6:
                        description:
                            - Enable/disable IPv6 next-hop calculation for this neighbor.
                        choices:
                            - enable
                            - disable
                    override-capability:
                        description:
                            - Enable/disable override result of capability negotiation.
                        choices:
                            - enable
                            - disable
                    passive:
                        description:
                            - Enable/disable sending of open messages to this neighbor.
                        choices:
                            - enable
                            - disable
                    prefix-list-in:
                        description:
                            - IPv4 Inbound filter for updates from this neighbor. Source router.prefix-list.name.
                    prefix-list-in6:
                        description:
                            - IPv6 Inbound filter for updates from this neighbor. Source router.prefix-list6.name.
                    prefix-list-out:
                        description:
                            - IPv4 Outbound filter for updates to this neighbor. Source router.prefix-list.name.
                    prefix-list-out6:
                        description:
                            - IPv6 Outbound filter for updates to this neighbor. Source router.prefix-list6.name.
                    remote-as:
                        description:
                            - AS number of neighbor.
                    remove-private-as:
                        description:
                            - Enable/disable remove private AS number from IPv4 outbound updates.
                        choices:
                            - enable
                            - disable
                    remove-private-as6:
                        description:
                            - Enable/disable remove private AS number from IPv6 outbound updates.
                        choices:
                            - enable
                            - disable
                    restart-time:
                        description:
                            - Graceful restart delay time (sec, 0 = global default).
                    retain-stale-time:
                        description:
                            - Time to retain stale routes.
                    route-map-in:
                        description:
                            - IPv4 Inbound route map filter. Source router.route-map.name.
                    route-map-in6:
                        description:
                            - IPv6 Inbound route map filter. Source router.route-map.name.
                    route-map-out:
                        description:
                            - IPv4 Outbound route map filter. Source router.route-map.name.
                    route-map-out6:
                        description:
                            - IPv6 Outbound route map filter. Source router.route-map.name.
                    route-reflector-client:
                        description:
                            - Enable/disable IPv4 AS route reflector client.
                        choices:
                            - enable
                            - disable
                    route-reflector-client6:
                        description:
                            - Enable/disable IPv6 AS route reflector client.
                        choices:
                            - enable
                            - disable
                    route-server-client:
                        description:
                            - Enable/disable IPv4 AS route server client.
                        choices:
                            - enable
                            - disable
                    route-server-client6:
                        description:
                            - Enable/disable IPv6 AS route server client.
                        choices:
                            - enable
                            - disable
                    send-community:
                        description:
                            - IPv4 Send community attribute to neighbor.
                        choices:
                            - standard
                            - extended
                            - both
                            - disable
                    send-community6:
                        description:
                            - IPv6 Send community attribute to neighbor.
                        choices:
                            - standard
                            - extended
                            - both
                            - disable
                    shutdown:
                        description:
                            - Enable/disable shutdown this neighbor.
                        choices:
                            - enable
                            - disable
                    soft-reconfiguration:
                        description:
                            - Enable/disable allow IPv4 inbound soft reconfiguration.
                        choices:
                            - enable
                            - disable
                    soft-reconfiguration6:
                        description:
                            - Enable/disable allow IPv6 inbound soft reconfiguration.
                        choices:
                            - enable
                            - disable
                    stale-route:
                        description:
                            - Enable/disable stale route after neighbor down.
                        choices:
                            - enable
                            - disable
                    strict-capability-match:
                        description:
                            - Enable/disable strict capability matching.
                        choices:
                            - enable
                            - disable
                    unsuppress-map:
                        description:
                            - IPv4 Route map to selectively unsuppress suppressed routes. Source router.route-map.name.
                    unsuppress-map6:
                        description:
                            - IPv6 Route map to selectively unsuppress suppressed routes. Source router.route-map.name.
                    update-source:
                        description:
                            - Interface to use as source IP/IPv6 address of TCP connections. Source system.interface.name.
                    weight:
                        description:
                            - Neighbor weight.
            neighbor-range:
                description:
                    - BGP neighbor range table.
                suboptions:
                    id:
                        description:
                            - Neighbor range ID.
                        required: true
                    max-neighbor-num:
                        description:
                            - Maximum number of neighbors.
                    neighbor-group:
                        description:
                            - Neighbor group name. Source router.bgp.neighbor-group.name.
                    prefix:
                        description:
                            - Neighbor range prefix.
            network:
                description:
                    - BGP network table.
                suboptions:
                    backdoor:
                        description:
                            - Enable/disable route as backdoor.
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - ID.
                        required: true
                    prefix:
                        description:
                            - Network prefix.
                    route-map:
                        description:
                            - Route map to modify generated route. Source router.route-map.name.
            network-import-check:
                description:
                    - Enable/disable ensure BGP network route exists in IGP.
                choices:
                    - enable
                    - disable
            network6:
                description:
                    - BGP IPv6 network table.
                suboptions:
                    backdoor:
                        description:
                            - Enable/disable route as backdoor.
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - ID.
                        required: true
                    prefix6:
                        description:
                            - Network IPv6 prefix.
                    route-map:
                        description:
                            - Route map to modify generated route. Source router.route-map.name.
            redistribute:
                description:
                    - BGP IPv4 redistribute table.
                suboptions:
                    name:
                        description:
                            - Distribute list entry name.
                        required: true
                    route-map:
                        description:
                            - Route map name. Source router.route-map.name.
                    status:
                        description:
                            - Status
                        choices:
                            - enable
                            - disable
            redistribute6:
                description:
                    - BGP IPv6 redistribute table.
                suboptions:
                    name:
                        description:
                            - Distribute list entry name.
                        required: true
                    route-map:
                        description:
                            - Route map name. Source router.route-map.name.
                    status:
                        description:
                            - Status
                        choices:
                            - enable
                            - disable
            router-id:
                description:
                    - Router ID.
            scan-time:
                description:
                    - Background scanner interval (sec), 0 to disable it.
            synchronization:
                description:
                    - Enable/disable only advertise routes from iBGP if routes present in an IGP.
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
  tasks:
  - name: Configure BGP.
    fortios_router_bgp:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      router_bgp:
        admin-distance:
         -
            distance: "4"
            id:  "5"
            neighbour-prefix: "<your_own_value>"
            route-list: "<your_own_value> (source router.access-list.name)"
        aggregate-address:
         -
            as-set: "enable"
            id:  "10"
            prefix: "<your_own_value>"
            summary-only: "enable"
        aggregate-address6:
         -
            as-set: "enable"
            id:  "15"
            prefix6: "<your_own_value>"
            summary-only: "enable"
        always-compare-med: "enable"
        as: "19"
        bestpath-as-path-ignore: "enable"
        bestpath-cmp-confed-aspath: "enable"
        bestpath-cmp-routerid: "enable"
        bestpath-med-confed: "enable"
        bestpath-med-missing-as-worst: "enable"
        client-to-client-reflection: "enable"
        cluster-id: "<your_own_value>"
        confederation-identifier: "27"
        confederation-peers:
         -
            peer: "<your_own_value>"
        dampening: "enable"
        dampening-max-suppress-time: "31"
        dampening-reachability-half-life: "32"
        dampening-reuse: "33"
        dampening-route-map: "<your_own_value> (source router.route-map.name)"
        dampening-suppress: "35"
        dampening-unreachability-half-life: "36"
        default-local-preference: "37"
        deterministic-med: "enable"
        distance-external: "39"
        distance-internal: "40"
        distance-local: "41"
        ebgp-multipath: "enable"
        enforce-first-as: "enable"
        fast-external-failover: "enable"
        graceful-end-on-timer: "enable"
        graceful-restart: "enable"
        graceful-restart-time: "47"
        graceful-stalepath-time: "48"
        graceful-update-delay: "49"
        holdtime-timer: "50"
        ibgp-multipath: "enable"
        ignore-optional-capability: "enable"
        keepalive-timer: "53"
        log-neighbour-changes: "enable"
        neighbor:
         -
            activate: "enable"
            activate6: "enable"
            advertisement-interval: "58"
            allowas-in: "59"
            allowas-in-enable: "enable"
            allowas-in-enable6: "enable"
            allowas-in6: "62"
            as-override: "enable"
            as-override6: "enable"
            attribute-unchanged: "as-path"
            attribute-unchanged6: "as-path"
            bfd: "enable"
            capability-default-originate: "enable"
            capability-default-originate6: "enable"
            capability-dynamic: "enable"
            capability-graceful-restart: "enable"
            capability-graceful-restart6: "enable"
            capability-orf: "none"
            capability-orf6: "none"
            capability-route-refresh: "enable"
            conditional-advertise:
             -
                advertise-routemap: "<your_own_value> (source router.route-map.name)"
                condition-routemap: "<your_own_value> (source router.route-map.name)"
                condition-type: "exist"
            connect-timer: "80"
            default-originate-routemap: "<your_own_value> (source router.route-map.name)"
            default-originate-routemap6: "<your_own_value> (source router.route-map.name)"
            description: "<your_own_value>"
            distribute-list-in: "<your_own_value> (source router.access-list.name)"
            distribute-list-in6: "<your_own_value> (source router.access-list6.name)"
            distribute-list-out: "<your_own_value> (source router.access-list.name)"
            distribute-list-out6: "<your_own_value> (source router.access-list6.name)"
            dont-capability-negotiate: "enable"
            ebgp-enforce-multihop: "enable"
            ebgp-multihop-ttl: "90"
            filter-list-in: "<your_own_value> (source router.aspath-list.name)"
            filter-list-in6: "<your_own_value> (source router.aspath-list.name)"
            filter-list-out: "<your_own_value> (source router.aspath-list.name)"
            filter-list-out6: "<your_own_value> (source router.aspath-list.name)"
            holdtime-timer: "95"
            interface: "<your_own_value> (source system.interface.name)"
            ip: "<your_own_value>"
            keep-alive-timer: "98"
            link-down-failover: "enable"
            local-as: "100"
            local-as-no-prepend: "enable"
            local-as-replace-as: "enable"
            maximum-prefix: "103"
            maximum-prefix-threshold: "104"
            maximum-prefix-threshold6: "105"
            maximum-prefix-warning-only: "enable"
            maximum-prefix-warning-only6: "enable"
            maximum-prefix6: "108"
            next-hop-self: "enable"
            next-hop-self6: "enable"
            override-capability: "enable"
            passive: "enable"
            password: "<your_own_value>"
            prefix-list-in: "<your_own_value> (source router.prefix-list.name)"
            prefix-list-in6: "<your_own_value> (source router.prefix-list6.name)"
            prefix-list-out: "<your_own_value> (source router.prefix-list.name)"
            prefix-list-out6: "<your_own_value> (source router.prefix-list6.name)"
            remote-as: "118"
            remove-private-as: "enable"
            remove-private-as6: "enable"
            restart-time: "121"
            retain-stale-time: "122"
            route-map-in: "<your_own_value> (source router.route-map.name)"
            route-map-in6: "<your_own_value> (source router.route-map.name)"
            route-map-out: "<your_own_value> (source router.route-map.name)"
            route-map-out6: "<your_own_value> (source router.route-map.name)"
            route-reflector-client: "enable"
            route-reflector-client6: "enable"
            route-server-client: "enable"
            route-server-client6: "enable"
            send-community: "standard"
            send-community6: "standard"
            shutdown: "enable"
            soft-reconfiguration: "enable"
            soft-reconfiguration6: "enable"
            stale-route: "enable"
            strict-capability-match: "enable"
            unsuppress-map: "<your_own_value> (source router.route-map.name)"
            unsuppress-map6: "<your_own_value> (source router.route-map.name)"
            update-source: "<your_own_value> (source system.interface.name)"
            weight: "141"
        neighbor-group:
         -
            activate: "enable"
            activate6: "enable"
            advertisement-interval: "145"
            allowas-in: "146"
            allowas-in-enable: "enable"
            allowas-in-enable6: "enable"
            allowas-in6: "149"
            as-override: "enable"
            as-override6: "enable"
            attribute-unchanged: "as-path"
            attribute-unchanged6: "as-path"
            bfd: "enable"
            capability-default-originate: "enable"
            capability-default-originate6: "enable"
            capability-dynamic: "enable"
            capability-graceful-restart: "enable"
            capability-graceful-restart6: "enable"
            capability-orf: "none"
            capability-orf6: "none"
            capability-route-refresh: "enable"
            connect-timer: "163"
            default-originate-routemap: "<your_own_value> (source router.route-map.name)"
            default-originate-routemap6: "<your_own_value> (source router.route-map.name)"
            description: "<your_own_value>"
            distribute-list-in: "<your_own_value> (source router.access-list.name)"
            distribute-list-in6: "<your_own_value> (source router.access-list6.name)"
            distribute-list-out: "<your_own_value> (source router.access-list.name)"
            distribute-list-out6: "<your_own_value> (source router.access-list6.name)"
            dont-capability-negotiate: "enable"
            ebgp-enforce-multihop: "enable"
            ebgp-multihop-ttl: "173"
            filter-list-in: "<your_own_value> (source router.aspath-list.name)"
            filter-list-in6: "<your_own_value> (source router.aspath-list.name)"
            filter-list-out: "<your_own_value> (source router.aspath-list.name)"
            filter-list-out6: "<your_own_value> (source router.aspath-list.name)"
            holdtime-timer: "178"
            interface: "<your_own_value> (source system.interface.name)"
            keep-alive-timer: "180"
            link-down-failover: "enable"
            local-as: "182"
            local-as-no-prepend: "enable"
            local-as-replace-as: "enable"
            maximum-prefix: "185"
            maximum-prefix-threshold: "186"
            maximum-prefix-threshold6: "187"
            maximum-prefix-warning-only: "enable"
            maximum-prefix-warning-only6: "enable"
            maximum-prefix6: "190"
            name: "default_name_191"
            next-hop-self: "enable"
            next-hop-self6: "enable"
            override-capability: "enable"
            passive: "enable"
            prefix-list-in: "<your_own_value> (source router.prefix-list.name)"
            prefix-list-in6: "<your_own_value> (source router.prefix-list6.name)"
            prefix-list-out: "<your_own_value> (source router.prefix-list.name)"
            prefix-list-out6: "<your_own_value> (source router.prefix-list6.name)"
            remote-as: "200"
            remove-private-as: "enable"
            remove-private-as6: "enable"
            restart-time: "203"
            retain-stale-time: "204"
            route-map-in: "<your_own_value> (source router.route-map.name)"
            route-map-in6: "<your_own_value> (source router.route-map.name)"
            route-map-out: "<your_own_value> (source router.route-map.name)"
            route-map-out6: "<your_own_value> (source router.route-map.name)"
            route-reflector-client: "enable"
            route-reflector-client6: "enable"
            route-server-client: "enable"
            route-server-client6: "enable"
            send-community: "standard"
            send-community6: "standard"
            shutdown: "enable"
            soft-reconfiguration: "enable"
            soft-reconfiguration6: "enable"
            stale-route: "enable"
            strict-capability-match: "enable"
            unsuppress-map: "<your_own_value> (source router.route-map.name)"
            unsuppress-map6: "<your_own_value> (source router.route-map.name)"
            update-source: "<your_own_value> (source system.interface.name)"
            weight: "223"
        neighbor-range:
         -
            id:  "225"
            max-neighbor-num: "226"
            neighbor-group: "<your_own_value> (source router.bgp.neighbor-group.name)"
            prefix: "<your_own_value>"
        network:
         -
            backdoor: "enable"
            id:  "231"
            prefix: "<your_own_value>"
            route-map: "<your_own_value> (source router.route-map.name)"
        network-import-check: "enable"
        network6:
         -
            backdoor: "enable"
            id:  "237"
            prefix6: "<your_own_value>"
            route-map: "<your_own_value> (source router.route-map.name)"
        redistribute:
         -
            name: "default_name_241"
            route-map: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        redistribute6:
         -
            name: "default_name_245"
            route-map: "<your_own_value> (source router.route-map.name)"
            status: "enable"
        router-id: "<your_own_value>"
        scan-time: "249"
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


def filter_router_bgp_data(json):
    option_list = ['admin-distance', 'aggregate-address', 'aggregate-address6',
                   'always-compare-med', 'as', 'bestpath-as-path-ignore',
                   'bestpath-cmp-confed-aspath', 'bestpath-cmp-routerid', 'bestpath-med-confed',
                   'bestpath-med-missing-as-worst', 'client-to-client-reflection', 'cluster-id',
                   'confederation-identifier', 'confederation-peers', 'dampening',
                   'dampening-max-suppress-time', 'dampening-reachability-half-life', 'dampening-reuse',
                   'dampening-route-map', 'dampening-suppress', 'dampening-unreachability-half-life',
                   'default-local-preference', 'deterministic-med', 'distance-external',
                   'distance-internal', 'distance-local', 'ebgp-multipath',
                   'enforce-first-as', 'fast-external-failover', 'graceful-end-on-timer',
                   'graceful-restart', 'graceful-restart-time', 'graceful-stalepath-time',
                   'graceful-update-delay', 'holdtime-timer', 'ibgp-multipath',
                   'ignore-optional-capability', 'keepalive-timer', 'log-neighbour-changes',
                   'neighbor', 'neighbor-group', 'neighbor-range',
                   'network', 'network-import-check', 'network6',
                   'redistribute', 'redistribute6', 'router-id',
                   'scan-time', 'synchronization']
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


def router_bgp(data, fos):
    vdom = data['vdom']
    router_bgp_data = data['router_bgp']
    flattened_data = flatten_multilists_attributes(router_bgp_data)
    filtered_data = filter_router_bgp_data(flattened_data)
    return fos.set('router',
                   'bgp',
                   data=filtered_data,
                   vdom=vdom)


def fortios_router(data, fos):
    login(data)

    if data['router_bgp']:
        resp = router_bgp(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "router_bgp": {
            "required": False, "type": "dict",
            "options": {
                "admin-distance": {"required": False, "type": "list",
                                   "options": {
                                       "distance": {"required": False, "type": "int"},
                                       "id": {"required": True, "type": "int"},
                                       "neighbour-prefix": {"required": False, "type": "str"},
                                       "route-list": {"required": False, "type": "str"}
                                   }},
                "aggregate-address": {"required": False, "type": "list",
                                      "options": {
                                          "as-set": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                          "id": {"required": True, "type": "int"},
                                          "prefix": {"required": False, "type": "str"},
                                          "summary-only": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]}
                                      }},
                "aggregate-address6": {"required": False, "type": "list",
                                       "options": {
                                           "as-set": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                           "id": {"required": True, "type": "int"},
                                           "prefix6": {"required": False, "type": "str"},
                                           "summary-only": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]}
                                       }},
                "always-compare-med": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "as": {"required": False, "type": "int"},
                "bestpath-as-path-ignore": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "bestpath-cmp-confed-aspath": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "bestpath-cmp-routerid": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "bestpath-med-confed": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "bestpath-med-missing-as-worst": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "client-to-client-reflection": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "cluster-id": {"required": False, "type": "str"},
                "confederation-identifier": {"required": False, "type": "int"},
                "confederation-peers": {"required": False, "type": "list",
                                        "options": {
                                            "peer": {"required": True, "type": "str"}
                                        }},
                "dampening": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "dampening-max-suppress-time": {"required": False, "type": "int"},
                "dampening-reachability-half-life": {"required": False, "type": "int"},
                "dampening-reuse": {"required": False, "type": "int"},
                "dampening-route-map": {"required": False, "type": "str"},
                "dampening-suppress": {"required": False, "type": "int"},
                "dampening-unreachability-half-life": {"required": False, "type": "int"},
                "default-local-preference": {"required": False, "type": "int"},
                "deterministic-med": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "distance-external": {"required": False, "type": "int"},
                "distance-internal": {"required": False, "type": "int"},
                "distance-local": {"required": False, "type": "int"},
                "ebgp-multipath": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "enforce-first-as": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "fast-external-failover": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "graceful-end-on-timer": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "graceful-restart": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "graceful-restart-time": {"required": False, "type": "int"},
                "graceful-stalepath-time": {"required": False, "type": "int"},
                "graceful-update-delay": {"required": False, "type": "int"},
                "holdtime-timer": {"required": False, "type": "int"},
                "ibgp-multipath": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "ignore-optional-capability": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "keepalive-timer": {"required": False, "type": "int"},
                "log-neighbour-changes": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "neighbor": {"required": False, "type": "list",
                             "options": {
                                 "activate": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                 "activate6": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                 "advertisement-interval": {"required": False, "type": "int"},
                                 "allowas-in": {"required": False, "type": "int"},
                                 "allowas-in-enable": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                 "allowas-in-enable6": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                 "allowas-in6": {"required": False, "type": "int"},
                                 "as-override": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                 "as-override6": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                 "attribute-unchanged": {"required": False, "type": "str",
                                                         "choices": ["as-path", "med", "next-hop"]},
                                 "attribute-unchanged6": {"required": False, "type": "str",
                                                          "choices": ["as-path", "med", "next-hop"]},
                                 "bfd": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                                 "capability-default-originate": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                 "capability-default-originate6": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                 "capability-dynamic": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                 "capability-graceful-restart": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                 "capability-graceful-restart6": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                 "capability-orf": {"required": False, "type": "str",
                                                    "choices": ["none", "receive", "send",
                                                                "both"]},
                                 "capability-orf6": {"required": False, "type": "str",
                                                     "choices": ["none", "receive", "send",
                                                                 "both"]},
                                 "capability-route-refresh": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                 "conditional-advertise": {"required": False, "type": "list",
                                                           "options": {
                                                               "advertise-routemap": {"required": True, "type": "str"},
                                                               "condition-routemap": {"required": False, "type": "str"},
                                                               "condition-type": {"required": False, "type": "str",
                                                                                  "choices": ["exist", "non-exist"]}
                                                           }},
                                 "connect-timer": {"required": False, "type": "int"},
                                 "default-originate-routemap": {"required": False, "type": "str"},
                                 "default-originate-routemap6": {"required": False, "type": "str"},
                                 "description": {"required": False, "type": "str"},
                                 "distribute-list-in": {"required": False, "type": "str"},
                                 "distribute-list-in6": {"required": False, "type": "str"},
                                 "distribute-list-out": {"required": False, "type": "str"},
                                 "distribute-list-out6": {"required": False, "type": "str"},
                                 "dont-capability-negotiate": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                 "ebgp-enforce-multihop": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                 "ebgp-multihop-ttl": {"required": False, "type": "int"},
                                 "filter-list-in": {"required": False, "type": "str"},
                                 "filter-list-in6": {"required": False, "type": "str"},
                                 "filter-list-out": {"required": False, "type": "str"},
                                 "filter-list-out6": {"required": False, "type": "str"},
                                 "holdtime-timer": {"required": False, "type": "int"},
                                 "interface": {"required": False, "type": "str"},
                                 "ip": {"required": True, "type": "str"},
                                 "keep-alive-timer": {"required": False, "type": "int"},
                                 "link-down-failover": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                 "local-as": {"required": False, "type": "int"},
                                 "local-as-no-prepend": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                 "local-as-replace-as": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                 "maximum-prefix": {"required": False, "type": "int"},
                                 "maximum-prefix-threshold": {"required": False, "type": "int"},
                                 "maximum-prefix-threshold6": {"required": False, "type": "int"},
                                 "maximum-prefix-warning-only": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                 "maximum-prefix-warning-only6": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                 "maximum-prefix6": {"required": False, "type": "int"},
                                 "next-hop-self": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                 "next-hop-self6": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                 "override-capability": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                 "passive": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                                 "password": {"required": False, "type": "str"},
                                 "prefix-list-in": {"required": False, "type": "str"},
                                 "prefix-list-in6": {"required": False, "type": "str"},
                                 "prefix-list-out": {"required": False, "type": "str"},
                                 "prefix-list-out6": {"required": False, "type": "str"},
                                 "remote-as": {"required": False, "type": "int"},
                                 "remove-private-as": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                 "remove-private-as6": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                 "restart-time": {"required": False, "type": "int"},
                                 "retain-stale-time": {"required": False, "type": "int"},
                                 "route-map-in": {"required": False, "type": "str"},
                                 "route-map-in6": {"required": False, "type": "str"},
                                 "route-map-out": {"required": False, "type": "str"},
                                 "route-map-out6": {"required": False, "type": "str"},
                                 "route-reflector-client": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                                 "route-reflector-client6": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                 "route-server-client": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                 "route-server-client6": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                 "send-community": {"required": False, "type": "str",
                                                    "choices": ["standard", "extended", "both",
                                                                "disable"]},
                                 "send-community6": {"required": False, "type": "str",
                                                     "choices": ["standard", "extended", "both",
                                                                 "disable"]},
                                 "shutdown": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                 "soft-reconfiguration": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                 "soft-reconfiguration6": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                 "stale-route": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                 "strict-capability-match": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                 "unsuppress-map": {"required": False, "type": "str"},
                                 "unsuppress-map6": {"required": False, "type": "str"},
                                 "update-source": {"required": False, "type": "str"},
                                 "weight": {"required": False, "type": "int"}
                             }},
                "neighbor-group": {"required": False, "type": "list",
                                   "options": {
                                       "activate": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                       "activate6": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                       "advertisement-interval": {"required": False, "type": "int"},
                                       "allowas-in": {"required": False, "type": "int"},
                                       "allowas-in-enable": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                       "allowas-in-enable6": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                       "allowas-in6": {"required": False, "type": "int"},
                                       "as-override": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                       "as-override6": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                       "attribute-unchanged": {"required": False, "type": "str",
                                                               "choices": ["as-path", "med", "next-hop"]},
                                       "attribute-unchanged6": {"required": False, "type": "str",
                                                                "choices": ["as-path", "med", "next-hop"]},
                                       "bfd": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                       "capability-default-originate": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                       "capability-default-originate6": {"required": False, "type": "str",
                                                                         "choices": ["enable", "disable"]},
                                       "capability-dynamic": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                       "capability-graceful-restart": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                       "capability-graceful-restart6": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                       "capability-orf": {"required": False, "type": "str",
                                                          "choices": ["none", "receive", "send",
                                                                      "both"]},
                                       "capability-orf6": {"required": False, "type": "str",
                                                           "choices": ["none", "receive", "send",
                                                                       "both"]},
                                       "capability-route-refresh": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
                                       "connect-timer": {"required": False, "type": "int"},
                                       "default-originate-routemap": {"required": False, "type": "str"},
                                       "default-originate-routemap6": {"required": False, "type": "str"},
                                       "description": {"required": False, "type": "str"},
                                       "distribute-list-in": {"required": False, "type": "str"},
                                       "distribute-list-in6": {"required": False, "type": "str"},
                                       "distribute-list-out": {"required": False, "type": "str"},
                                       "distribute-list-out6": {"required": False, "type": "str"},
                                       "dont-capability-negotiate": {"required": False, "type": "str",
                                                                     "choices": ["enable", "disable"]},
                                       "ebgp-enforce-multihop": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                       "ebgp-multihop-ttl": {"required": False, "type": "int"},
                                       "filter-list-in": {"required": False, "type": "str"},
                                       "filter-list-in6": {"required": False, "type": "str"},
                                       "filter-list-out": {"required": False, "type": "str"},
                                       "filter-list-out6": {"required": False, "type": "str"},
                                       "holdtime-timer": {"required": False, "type": "int"},
                                       "interface": {"required": False, "type": "str"},
                                       "keep-alive-timer": {"required": False, "type": "int"},
                                       "link-down-failover": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                       "local-as": {"required": False, "type": "int"},
                                       "local-as-no-prepend": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "local-as-replace-as": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "maximum-prefix": {"required": False, "type": "int"},
                                       "maximum-prefix-threshold": {"required": False, "type": "int"},
                                       "maximum-prefix-threshold6": {"required": False, "type": "int"},
                                       "maximum-prefix-warning-only": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                       "maximum-prefix-warning-only6": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                       "maximum-prefix6": {"required": False, "type": "int"},
                                       "name": {"required": True, "type": "str"},
                                       "next-hop-self": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                       "next-hop-self6": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                       "override-capability": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "passive": {"required": False, "type": "str",
                                                   "choices": ["enable", "disable"]},
                                       "prefix-list-in": {"required": False, "type": "str"},
                                       "prefix-list-in6": {"required": False, "type": "str"},
                                       "prefix-list-out": {"required": False, "type": "str"},
                                       "prefix-list-out6": {"required": False, "type": "str"},
                                       "remote-as": {"required": False, "type": "int"},
                                       "remove-private-as": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                       "remove-private-as6": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                       "restart-time": {"required": False, "type": "int"},
                                       "retain-stale-time": {"required": False, "type": "int"},
                                       "route-map-in": {"required": False, "type": "str"},
                                       "route-map-in6": {"required": False, "type": "str"},
                                       "route-map-out": {"required": False, "type": "str"},
                                       "route-map-out6": {"required": False, "type": "str"},
                                       "route-reflector-client": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                       "route-reflector-client6": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                       "route-server-client": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                       "route-server-client6": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                       "send-community": {"required": False, "type": "str",
                                                          "choices": ["standard", "extended", "both",
                                                                      "disable"]},
                                       "send-community6": {"required": False, "type": "str",
                                                           "choices": ["standard", "extended", "both",
                                                                       "disable"]},
                                       "shutdown": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                       "soft-reconfiguration": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                       "soft-reconfiguration6": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                       "stale-route": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]},
                                       "strict-capability-match": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                       "unsuppress-map": {"required": False, "type": "str"},
                                       "unsuppress-map6": {"required": False, "type": "str"},
                                       "update-source": {"required": False, "type": "str"},
                                       "weight": {"required": False, "type": "int"}
                                   }},
                "neighbor-range": {"required": False, "type": "list",
                                   "options": {
                                       "id": {"required": True, "type": "int"},
                                       "max-neighbor-num": {"required": False, "type": "int"},
                                       "neighbor-group": {"required": False, "type": "str"},
                                       "prefix": {"required": False, "type": "str"}
                                   }},
                "network": {"required": False, "type": "list",
                            "options": {
                                "backdoor": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                                "id": {"required": True, "type": "int"},
                                "prefix": {"required": False, "type": "str"},
                                "route-map": {"required": False, "type": "str"}
                            }},
                "network-import-check": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "network6": {"required": False, "type": "list",
                             "options": {
                                 "backdoor": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                                 "id": {"required": True, "type": "int"},
                                 "prefix6": {"required": False, "type": "str"},
                                 "route-map": {"required": False, "type": "str"}
                             }},
                "redistribute": {"required": False, "type": "list",
                                 "options": {
                                     "name": {"required": True, "type": "str"},
                                     "route-map": {"required": False, "type": "str"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]}
                                 }},
                "redistribute6": {"required": False, "type": "list",
                                  "options": {
                                      "name": {"required": True, "type": "str"},
                                      "route-map": {"required": False, "type": "str"},
                                      "status": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]}
                                  }},
                "router-id": {"required": False, "type": "str"},
                "scan-time": {"required": False, "type": "int"},
                "synchronization": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]}

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
