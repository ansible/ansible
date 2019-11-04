#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_bgp_af
version_added: "2.4"
short_description: Manages BGP Address-family configuration on HUAWEI CloudEngine switches.
description:
    - Manages BGP Address-family configurations on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@QijunPan)
notes:
  - This module requires the netconf system service be enabled on the remote device being managed.
  - Recommended connection is C(netconf).
  - This module also works with C(local) connections for legacy playbooks.
options:
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present','absent']
    vrf_name:
        description:
            - Name of a BGP instance. The name is a case-sensitive string of characters.
              The BGP instance can be used only after the corresponding VPN instance is created.
              The value is a string of 1 to 31 case-sensitive characters.
        required: true
    af_type:
        description:
            - Address family type of a BGP instance.
        required: true
        choices: ['ipv4uni','ipv4multi', 'ipv4vpn', 'ipv6uni', 'ipv6vpn', 'evpn']
    max_load_ibgp_num:
        description:
            - Specify the maximum number of equal-cost IBGP routes.
              The value is an integer ranging from 1 to 65535.
    ibgp_ecmp_nexthop_changed:
        description:
            - If the value is true, the next hop of an advertised route is changed to the advertiser itself in IBGP
              load-balancing scenarios.
              If the value is false, the next hop of an advertised route is not changed to the advertiser itself in
              IBGP load-balancing scenarios.
        choices: ['no_use','true','false']
        default: no_use
    max_load_ebgp_num:
        description:
            - Specify the maximum number of equal-cost EBGP routes.
              The value is an integer ranging from 1 to 65535.
    ebgp_ecmp_nexthop_changed:
        description:
            - If the value is true, the next hop of an advertised route is changed to the advertiser itself in EBGP
              load-balancing scenarios.
              If the value is false, the next hop of an advertised route is not changed to the advertiser itself in
              EBGP load-balancing scenarios.
        choices: ['no_use','true','false']
        default: no_use
    maximum_load_balance:
        description:
            - Specify the maximum number of equal-cost routes in the BGP routing table.
              The value is an integer ranging from 1 to 65535.
    ecmp_nexthop_changed:
        description:
            - If the value is true, the next hop of an advertised route is changed to the advertiser itself in BGP
              load-balancing scenarios.
              If the value is false, the next hop of an advertised route is not changed to the advertiser itself
              in BGP load-balancing scenarios.
        choices: ['no_use','true','false']
        default: no_use
    default_local_pref:
        description:
            - Set the Local-Preference attribute. The value is an integer.
              The value is an integer ranging from 0 to 4294967295.
    default_med:
        description:
            - Specify the Multi-Exit-Discriminator (MED) of BGP routes.
              The value is an integer ranging from 0 to 4294967295.
    default_rt_import_enable:
        description:
            - If the value is true, importing default routes to the BGP routing table is allowed.
              If the value is false, importing default routes to the BGP routing table is not allowed.
        choices: ['no_use','true','false']
        default: no_use
    router_id:
        description:
            - ID of a router that is in IPv4 address format.
              The value is a string of 0 to 255 characters.
              The value is in dotted decimal notation.
    vrf_rid_auto_sel:
        description:
            - If the value is true, VPN BGP instances are enabled to automatically select router IDs.
              If the value is false, VPN BGP instances are disabled from automatically selecting router IDs.
        choices: ['no_use','true','false']
        default: no_use
    nexthop_third_party:
        description:
            - If the value is true, the third-party next hop function is enabled.
              If the value is false, the third-party next hop function is disabled.
        choices: ['no_use','true','false']
        default: no_use
    summary_automatic:
        description:
            - If the value is true, automatic aggregation is enabled for locally imported routes.
              If the value is false, automatic aggregation is disabled for locally imported routes.
        choices: ['no_use','true','false']
        default: no_use
    auto_frr_enable:
        description:
            - If the value is true, BGP auto FRR is enabled.
              If the value is false, BGP auto FRR is disabled.
        choices: ['no_use','true','false']
        default: no_use
    load_balancing_as_path_ignore:
        description:
            - Load balancing as path ignore.
        choices: ['no_use','true','false']
        default: no_use
    rib_only_enable:
        description:
            - If the value is true, BGP routes cannot be advertised to the IP routing table.
              If the value is false, Routes preferred by BGP are advertised to the IP routing table.
        choices: ['no_use','true','false']
        default: no_use
    rib_only_policy_name:
        description:
            - Specify the name of a routing policy.
              The value is a string of 1 to 40 characters.
    active_route_advertise:
        description:
            - If the value is true, BGP is enabled to advertise only optimal routes in the RM to peers.
              If the value is false, BGP is not enabled to advertise only optimal routes in the RM to peers.
        choices: ['no_use','true','false']
        default: no_use
    as_path_neglect:
        description:
            - If the value is true, the AS path attribute is ignored when BGP selects an optimal route.
              If the value is false, the AS path attribute is not ignored when BGP selects an optimal route.
              An AS path with a smaller length has a higher priority.
        choices: ['no_use','true','false']
        default: no_use
    med_none_as_maximum:
        description:
            - If the value is true, when BGP selects an optimal route, the system uses 4294967295 as the
              MED value of a route if the route's attribute does not carry a MED value.
              If the value is false, the system uses 0 as the MED value of a route if the route's attribute
              does not carry a MED value.
        choices: ['no_use','true','false']
        default: no_use
    router_id_neglect:
        description:
            - If the value is true, the router ID attribute is ignored when BGP selects the optimal route.
              If the value is false, the router ID attribute is not ignored when BGP selects the optimal route.
        choices: ['no_use','true','false']
        default: no_use
    igp_metric_ignore:
        description:
            - If the value is true, the metrics of next-hop IGP routes are not compared when BGP selects
              an optimal route.
              If the value is false, the metrics of next-hop IGP routes are not compared when BGP selects
              an optimal route.
              A route with a smaller metric has a higher priority.
        choices: ['no_use','true','false']
        default: no_use
    always_compare_med:
        description:
            - If the value is true, the MEDs of routes learned from peers in different autonomous systems
              are compared when BGP selects an optimal route.
              If the value is false, the MEDs of routes learned from peers in different autonomous systems
              are not compared when BGP selects an optimal route.
        choices: ['no_use','true','false']
        default: no_use
    determin_med:
        description:
            - If the value is true, BGP deterministic-MED is enabled.
              If the value is false, BGP deterministic-MED is disabled.
        choices: ['no_use','true','false']
        default: no_use
    preference_external:
        description:
            - Set the protocol priority of EBGP routes.
              The value is an integer ranging from 1 to 255.
    preference_internal:
        description:
            - Set the protocol priority of IBGP routes.
              The value is an integer ranging from 1 to 255.
    preference_local:
        description:
            - Set the protocol priority of a local BGP route.
              The value is an integer ranging from 1 to 255.
    prefrence_policy_name:
        description:
            - Set a routing policy to filter routes so that a configured priority is applied to
              the routes that match the specified policy.
              The value is a string of 1 to 40 characters.
    reflect_between_client:
        description:
            - If the value is true, route reflection is enabled between clients.
              If the value is false, route reflection is disabled between clients.
        choices: ['no_use','true','false']
        default: no_use
    reflector_cluster_id:
        description:
            - Set a cluster ID. Configuring multiple RRs in a cluster can enhance the stability of the network.
              The value is an integer ranging from 1 to 4294967295.
    reflector_cluster_ipv4:
        description:
            - Set a cluster ipv4 address. The value is expressed in the format of an IPv4 address.
    rr_filter_number:
        description:
            - Set the number of the extended community filter supported by an RR group.
              The value is a string of 1 to 51 characters.
    policy_vpn_target:
        description:
            - If the value is true, VPN-Target filtering function is performed for received VPN routes.
              If the value is false, VPN-Target filtering function is not performed for received VPN routes.
        choices: ['no_use','true','false']
        default: no_use
    next_hop_sel_depend_type:
        description:
            - Next hop select depend type.
        choices: ['default','dependTunnel', 'dependIp']
        default: default
    nhp_relay_route_policy_name:
        description:
            - Specify the name of a route-policy for route iteration.
              The value is a string of 1 to 40 characters.
    ebgp_if_sensitive:
        description:
            - If the value is true, after the fast EBGP interface awareness function is enabled,
              EBGP sessions on an interface are deleted immediately when the interface goes Down.
              If the value is false, after the fast EBGP interface awareness function is enabled,
              EBGP sessions on an interface are not deleted immediately when the interface goes Down.
        choices: ['no_use','true','false']
        default: no_use
    reflect_chg_path:
        description:
            - If the value is true, the route reflector is enabled to modify route path attributes
              based on an export policy.
              If the value is false, the route reflector is disabled from modifying route path attributes
              based on an export policy.
        choices: ['no_use','true','false']
        default: no_use
    add_path_sel_num:
        description:
            - Number of Add-Path routes.
              The value is an integer ranging from 2 to 64.
    route_sel_delay:
        description:
            - Route selection delay.
              The value is an integer ranging from 0 to 3600.
    allow_invalid_as:
        description:
            - Allow routes with BGP origin AS validation result Invalid to be selected.
              If the value is true, invalid routes can participate in route selection.
              If the value is false, invalid routes cannot participate in route selection.
        choices: ['no_use','true','false']
        default: no_use
    policy_ext_comm_enable:
        description:
            - If the value is true, modifying extended community attributes is allowed.
              If the value is false, modifying extended community attributes is not allowed.
        choices: ['no_use','true','false']
        default: no_use
    supernet_uni_adv:
        description:
            - If the value is true, the function to advertise supernetwork unicast routes is enabled.
              If the value is false, the function to advertise supernetwork unicast routes is disabled.
        choices: ['no_use','true','false']
        default: no_use
    supernet_label_adv:
        description:
            - If the value is true, the function to advertise supernetwork label is enabled.
              If the value is false, the function to advertise supernetwork label is disabled.
        choices: ['no_use','true','false']
        default: no_use
    ingress_lsp_policy_name:
        description:
            - Ingress lsp policy name.
    originator_prior:
        description:
            - Originator prior.
        choices: ['no_use','true','false']
        default: no_use
    lowest_priority:
        description:
            - If the value is true, enable reduce priority to advertise route.
              If the value is false, disable reduce priority to advertise route.
        choices: ['no_use','true','false']
        default: no_use
    relay_delay_enable:
        description:
            - If the value is true, relay delay enable.
              If the value is false, relay delay disable.
        choices: ['no_use','true','false']
        default: no_use
    import_protocol:
        description:
            - Routing protocol from which routes can be imported.
        choices: ['direct', 'ospf', 'isis', 'static', 'rip', 'ospfv3', 'ripng']
    import_process_id:
        description:
            - Process ID of an imported routing protocol.
              The value is an integer ranging from 0 to 4294967295.
    network_address:
        description:
            - Specify the IP address advertised by BGP.
              The value is a string of 0 to 255 characters.
    mask_len:
        description:
            - Specify the mask length of an IP address.
              The value is an integer ranging from 0 to 128.
'''

EXAMPLES = '''
- name: CloudEngine BGP address family test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli
  tasks:
  - name: "Config BGP Address_Family"
    ce_bgp_af:
      state: present
      vrf_name: js
      af_type: ipv4uni
      provider: "{{ cli }}"
  - name: "Undo BGP Address_Family"
    ce_bgp_af:
      state: absent
      vrf_name: js
      af_type: ipv4uni
      provider: "{{ cli }}"
  - name: "Config import route"
    ce_bgp_af:
      state: present
      vrf_name: js
      af_type: ipv4uni
      import_protocol: ospf
      import_process_id: 123
      provider: "{{ cli }}"
  - name: "Undo import route"
    ce_bgp_af:
      state: absent
      vrf_name: js
      af_type: ipv4uni
      import_protocol: ospf
      import_process_id: 123
      provider: "{{ cli }}"
  - name: "Config network route"
    ce_bgp_af:
      state: present
      vrf_name: js
      af_type: ipv4uni
      network_address: 1.1.1.1
      mask_len: 24
      provider: "{{ cli }}"
  - name: "Undo network route"
    ce_bgp_af:
      state: absent
      vrf_name: js
      af_type: ipv4uni
      network_address: 1.1.1.1
      mask_len: 24
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"af_type": "ipv4uni",
             "state": "present", "vrf_name": "js"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"af_type": "ipv4uni", "vrf_name": "js"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["ipv4-family vpn-instance js"]
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec, check_ip_addr

# get bgp address family
CE_GET_BGP_ADDRESS_FAMILY_HEADER = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
"""
CE_GET_BGP_ADDRESS_FAMILY_TAIL = """
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </filter>
"""

# merge bgp address family
CE_MERGE_BGP_ADDRESS_FAMILY_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF operation="merge">
                  <afType>%s</afType>
"""
CE_MERGE_BGP_ADDRESS_FAMILY_TAIL = """
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# create bgp address family
CE_CREATE_BGP_ADDRESS_FAMILY_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF operation="merge">
                  <afType>%s</afType>
"""
CE_CREATE_BGP_ADDRESS_FAMILY_TAIL = """
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# delete bgp address family
CE_DELETE_BGP_ADDRESS_FAMILY_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF operation="delete">
                  <afType>%s</afType>
"""
CE_DELETE_BGP_ADDRESS_FAMILY_TAIL = """
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# get bgp import route
CE_GET_BGP_IMPORT_AND_NETWORK_ROUTE = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <importRoutes>
                    <importRoute>
                      <importProtocol></importProtocol>
                      <importProcessId></importProcessId>
                    </importRoute>
                  </importRoutes>
                  <networkRoutes>
                    <networkRoute>
                      <networkAddress></networkAddress>
                      <maskLen></maskLen>
                    </networkRoute>
                  </networkRoutes>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </filter>
"""

# merge bgp import route
CE_MERGE_BGP_IMPORT_ROUTE_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <importRoutes>
                    <importRoute operation="merge">
                      <importProtocol>%s</importProtocol>
                      <importProcessId>%s</importProcessId>
"""
CE_MERGE_BGP_IMPORT_ROUTE_TAIL = """
                    </importRoute>
                  </importRoutes>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# create bgp import route
CE_CREATE_BGP_IMPORT_ROUTE = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <importRoutes>
                    <importRoute operation="create">
                      <importProtocol>%s</importProtocol>
                      <importProcessId>%s</importProcessId>
                    </importRoute>
                  </importRoutes>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# delete bgp import route
CE_DELETE_BGP_IMPORT_ROUTE = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <importRoutes>
                    <importRoute operation="delete">
                      <importProtocol>%s</importProtocol>
                      <importProcessId>%s</importProcessId>
                    </importRoute>
                  </importRoutes>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# get bgp network route
CE_GET_BGP_NETWORK_ROUTE_HEADER = """
    <filter type="subtree">
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <networkRoutes>
                    <networkRoute>
                      <networkAddress></networkAddress>
                      <maskLen></maskLen>
"""
CE_GET_BGP_NETWORK_ROUTE_TAIL = """
                    </networkRoute>
                  </networkRoutes>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </filter>
"""

# merge bgp network route
CE_MERGE_BGP_NETWORK_ROUTE_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <networkRoutes>
                    <networkRoute operation="merge">
                      <networkAddress>%s</networkAddress>
                      <maskLen>%s</maskLen>
"""
CE_MERGE_BGP_NETWORK_ROUTE_TAIL = """
                    </networkRoute>
                  </networkRoutes>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# create bgp network route
CE_CREATE_BGP_NETWORK_ROUTE = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <networkRoutes>
                    <networkRoute operation="create">
                      <networkAddress>%s</networkAddress>
                      <maskLen>%s</maskLen>
                    </networkRoute>
                  </networkRoutes>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# delete bgp network route
CE_DELETE_BGP_NETWORK_ROUTE = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
                  <networkRoutes>
                    <networkRoute operation="delete">
                      <networkAddress>%s</networkAddress>
                      <maskLen>%s</maskLen>
                    </networkRoute>
                  </networkRoutes>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""

# bgp import and network route header
CE_BGP_IMPORT_NETWORK_ROUTE_HEADER = """
    <config>
      <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>%s</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType>%s</afType>
"""
CE_BGP_IMPORT_NETWORK_ROUTE_TAIL = """
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
    </config>
"""
CE_BGP_MERGE_IMPORT_UNIT = """
                  <importRoutes>
                    <importRoute operation="merge">
                      <importProtocol>%s</importProtocol>
                      <importProcessId>%s</importProcessId>
                    </importRoute>
                  </importRoutes>
"""
CE_BGP_CREATE_IMPORT_UNIT = """
                  <importRoutes>
                    <importRoute operation="create">
                      <importProtocol>%s</importProtocol>
                      <importProcessId>%s</importProcessId>
                    </importRoute>
                  </importRoutes>
"""
CE_BGP_DELETE_IMPORT_UNIT = """
                  <importRoutes>
                    <importRoute operation="delete">
                      <importProtocol>%s</importProtocol>
                      <importProcessId>%s</importProcessId>
                    </importRoute>
                  </importRoutes>
"""
CE_BGP_MERGE_NETWORK_UNIT = """
                  <networkRoutes>
                    <networkRoute operation="merge">
                      <networkAddress>%s</networkAddress>
                      <maskLen>%s</maskLen>
                    </networkRoute>
                  </networkRoutes>
"""
CE_BGP_CREATE_NETWORK_UNIT = """
                  <networkRoutes>
                    <networkRoute operation="create">
                      <networkAddress>%s</networkAddress>
                      <maskLen>%s</maskLen>
                    </networkRoute>
                  </networkRoutes>
"""
CE_BGP_DELETE_NETWORK_UNIT = """
                  <networkRoutes>
                    <networkRoute operation="delete">
                      <networkAddress>%s</networkAddress>
                      <maskLen>%s</maskLen>
                    </networkRoute>
                  </networkRoutes>
"""


class BgpAf(object):
    """ Manages BGP Address-family configuration """

    def netconf_get_config(self, **kwargs):
        """ netconf_get_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = get_nc_config(module, conf_str)

        return xml_str

    def netconf_set_config(self, **kwargs):
        """ netconf_set_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        xml_str = set_nc_config(module, conf_str)

        return xml_str

    def check_bgp_af_args(self, **kwargs):
        """ check_bgp_af_args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='Error: The len of vrf_name %s is out of [1 - 31].' % vrf_name)
        else:
            module.fail_json(msg='Error: Please input vrf_name.')

        state = module.params['state']
        af_type = module.params['af_type']

        conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
            CE_GET_BGP_ADDRESS_FAMILY_TAIL
        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if state == "present":
            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<afType>(.*)</afType>.*', recv_xml)

                if re_find:
                    result["af_type"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != af_type:
                        need_cfg = True
                else:
                    need_cfg = True
        else:
            if "<data/>" in recv_xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<afType>(.*)</afType>.*', recv_xml)

                if re_find:
                    result["af_type"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] == af_type:
                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_af_other_can_del(self, **kwargs):
        """ check_bgp_af_other_can_del """
        module = kwargs["module"]
        result = dict()
        need_cfg = False

        state = module.params['state']
        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']

        router_id = module.params['router_id']
        if router_id:
            if len(router_id) > 255:
                module.fail_json(
                    msg='Error: The len of router_id %s is out of [0 - 255].' % router_id)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<routerId></routerId>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<routerId>(.*)</routerId>.*', recv_xml)

                    if re_find:
                        if re_find[0] != router_id:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<routerId>(.*)</routerId>.*', recv_xml)

                    if re_find:
                        if re_find[0] == router_id:
                            need_cfg = True
                    else:
                        pass

        determin_med = module.params['determin_med']
        if determin_med != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<determinMed></determinMed>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<determinMed>(.*)</determinMed>.*', recv_xml)

                    if re_find:
                        if re_find[0] != determin_med:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<determinMed>(.*)</determinMed>.*', recv_xml)

                    if re_find:
                        if re_find[0] == determin_med:
                            need_cfg = True
                    else:
                        pass

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<ebgpIfSensitive></ebgpIfSensitive>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', recv_xml)

                    if re_find:
                        if re_find[0] != ebgp_if_sensitive:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', recv_xml)

                    if re_find:
                        if re_find[0] == ebgp_if_sensitive:
                            need_cfg = True
                    else:
                        pass

        relay_delay_enable = module.params['relay_delay_enable']
        if relay_delay_enable != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<relayDelayEnable></relayDelayEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in recv_xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<relayDelayEnable>(.*)</relayDelayEnable>.*', recv_xml)

                    if re_find:
                        if re_find[0] != relay_delay_enable:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<relayDelayEnable>(.*)</relayDelayEnable>.*', recv_xml)

                    if re_find:
                        if re_find[0] == relay_delay_enable:
                            need_cfg = True
                    else:
                        pass

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_af_other_args(self, **kwargs):
        """ check_bgp_af_other_args """

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']

        max_load_ibgp_num = module.params['max_load_ibgp_num']
        if max_load_ibgp_num:
            if int(max_load_ibgp_num) > 65535 or int(max_load_ibgp_num) < 1:
                module.fail_json(
                    msg='Error: The value of max_load_ibgp_num %s is out of [1 - 65535].' % max_load_ibgp_num)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<maxLoadIbgpNum></maxLoadIbgpNum>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<maxLoadIbgpNum>(.*)</maxLoadIbgpNum>.*', recv_xml)

                if re_find:
                    result["max_load_ibgp_num"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != max_load_ibgp_num:
                        need_cfg = True
                else:
                    need_cfg = True

        ibgp_ecmp_nexthop_changed = module.params['ibgp_ecmp_nexthop_changed']
        if ibgp_ecmp_nexthop_changed != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<ibgpEcmpNexthopChanged></ibgpEcmpNexthopChanged>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ibgpEcmpNexthopChanged>(.*)</ibgpEcmpNexthopChanged>.*', recv_xml)

                if re_find:
                    result["ibgp_ecmp_nexthop_changed"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != ibgp_ecmp_nexthop_changed:
                        need_cfg = True
                else:
                    need_cfg = True

        max_load_ebgp_num = module.params['max_load_ebgp_num']
        if max_load_ebgp_num:
            if int(max_load_ebgp_num) > 65535 or int(max_load_ebgp_num) < 1:
                module.fail_json(
                    msg='Error: The value of max_load_ebgp_num %s is out of [1 - 65535].' % max_load_ebgp_num)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<maxLoadEbgpNum></maxLoadEbgpNum>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<maxLoadEbgpNum>(.*)</maxLoadEbgpNum>.*', recv_xml)

                if re_find:
                    result["max_load_ebgp_num"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != max_load_ebgp_num:
                        need_cfg = True
                else:
                    need_cfg = True

        ebgp_ecmp_nexthop_changed = module.params['ebgp_ecmp_nexthop_changed']
        if ebgp_ecmp_nexthop_changed != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<ebgpEcmpNexthopChanged></ebgpEcmpNexthopChanged>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ebgpEcmpNexthopChanged>(.*)</ebgpEcmpNexthopChanged>.*', recv_xml)

                if re_find:
                    result["ebgp_ecmp_nexthop_changed"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != ebgp_ecmp_nexthop_changed:
                        need_cfg = True
                else:
                    need_cfg = True

        maximum_load_balance = module.params['maximum_load_balance']
        if maximum_load_balance:
            if int(maximum_load_balance) > 65535 or int(maximum_load_balance) < 1:
                module.fail_json(
                    msg='Error: The value of maximum_load_balance %s is out of [1 - 65535].' % maximum_load_balance)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<maximumLoadBalance></maximumLoadBalance>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<maximumLoadBalance>(.*)</maximumLoadBalance>.*', recv_xml)

                if re_find:
                    result["maximum_load_balance"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != maximum_load_balance:
                        need_cfg = True
                else:
                    need_cfg = True

        ecmp_nexthop_changed = module.params['ecmp_nexthop_changed']
        if ecmp_nexthop_changed != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<ecmpNexthopChanged></ecmpNexthopChanged>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ecmpNexthopChanged>(.*)</ecmpNexthopChanged>.*', recv_xml)

                if re_find:
                    result["ecmp_nexthop_changed"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != ecmp_nexthop_changed:
                        need_cfg = True
                else:
                    need_cfg = True

        default_local_pref = module.params['default_local_pref']
        if default_local_pref:
            if int(default_local_pref) < 0:
                module.fail_json(
                    msg='Error: The value of default_local_pref %s is out of [0 - 4294967295].' % default_local_pref)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<defaultLocalPref></defaultLocalPref>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultLocalPref>(.*)</defaultLocalPref>.*', recv_xml)

                if re_find:
                    result["default_local_pref"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != default_local_pref:
                        need_cfg = True
                else:
                    need_cfg = True

        default_med = module.params['default_med']
        if default_med:
            if int(default_med) < 0:
                module.fail_json(
                    msg='Error: The value of default_med %s is out of [0 - 4294967295].' % default_med)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<defaultMed></defaultMed>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultMed>(.*)</defaultMed>.*', recv_xml)

                if re_find:
                    result["default_med"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != default_med:
                        need_cfg = True
                else:
                    need_cfg = True

        default_rt_import_enable = module.params['default_rt_import_enable']
        if default_rt_import_enable != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<defaultRtImportEnable></defaultRtImportEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultRtImportEnable>(.*)</defaultRtImportEnable>.*', recv_xml)

                if re_find:
                    result["default_rt_import_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != default_rt_import_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        router_id = module.params['router_id']
        if router_id:
            if len(router_id) > 255:
                module.fail_json(
                    msg='Error: The len of router_id %s is out of [0 - 255].' % router_id)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<routerId></routerId>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routerId>(.*)</routerId>.*', recv_xml)

                if re_find:
                    result["router_id"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != router_id:
                        need_cfg = True
                else:
                    need_cfg = True

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<vrfRidAutoSel></vrfRidAutoSel>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<vrfRidAutoSel>(.*)</vrfRidAutoSel>.*', recv_xml)

                if re_find:
                    result["vrf_rid_auto_sel"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != vrf_rid_auto_sel:
                        need_cfg = True
                else:
                    need_cfg = True

        nexthop_third_party = module.params['nexthop_third_party']
        if nexthop_third_party != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<nexthopThirdParty></nexthopThirdParty>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<nexthopThirdParty>(.*)</nexthopThirdParty>.*', recv_xml)

                if re_find:
                    result["nexthop_third_party"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != nexthop_third_party:
                        need_cfg = True
                else:
                    need_cfg = True

        summary_automatic = module.params['summary_automatic']
        if summary_automatic != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<summaryAutomatic></summaryAutomatic>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<summaryAutomatic>(.*)</summaryAutomatic>.*', recv_xml)

                if re_find:
                    result["summary_automatic"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != summary_automatic:
                        need_cfg = True
                else:
                    need_cfg = True

        auto_frr_enable = module.params['auto_frr_enable']
        if auto_frr_enable != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<autoFrrEnable></autoFrrEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<autoFrrEnable>(.*)</autoFrrEnable>.*', recv_xml)

                if re_find:
                    result["auto_frr_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != auto_frr_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        load_balancing_as_path_ignore = module.params['load_balancing_as_path_ignore']
        if load_balancing_as_path_ignore != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<loadBalancingAsPathIgnore></loadBalancingAsPathIgnore>" + \
                CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<loadBalancingAsPathIgnore>(.*)</loadBalancingAsPathIgnore>.*', recv_xml)

                if re_find:
                    result["load_balancing_as_path_ignore"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != load_balancing_as_path_ignore:
                        need_cfg = True
                else:
                    need_cfg = True

        rib_only_enable = module.params['rib_only_enable']
        if rib_only_enable != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<ribOnlyEnable></ribOnlyEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ribOnlyEnable>(.*)</ribOnlyEnable>.*', recv_xml)

                if re_find:
                    result["rib_only_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != rib_only_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        rib_only_policy_name = module.params['rib_only_policy_name']
        if rib_only_policy_name:
            if len(rib_only_policy_name) > 40 or len(rib_only_policy_name) < 1:
                module.fail_json(
                    msg='Error: The len of rib_only_policy_name %s is out of [1 - 40].' % rib_only_policy_name)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<ribOnlyPolicyName></ribOnlyPolicyName>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ribOnlyPolicyName>(.*)</ribOnlyPolicyName>.*', recv_xml)

                if re_find:
                    result["rib_only_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != rib_only_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        active_route_advertise = module.params['active_route_advertise']
        if active_route_advertise != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<activeRouteAdvertise></activeRouteAdvertise>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<activeRouteAdvertise>(.*)</activeRouteAdvertise>.*', recv_xml)

                if re_find:
                    result["active_route_advertise"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != active_route_advertise:
                        need_cfg = True
                else:
                    need_cfg = True

        as_path_neglect = module.params['as_path_neglect']
        if as_path_neglect != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<asPathNeglect></asPathNeglect>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<asPathNeglect>(.*)</asPathNeglect>.*', recv_xml)

                if re_find:
                    result["as_path_neglect"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != as_path_neglect:
                        need_cfg = True
                else:
                    need_cfg = True

        med_none_as_maximum = module.params['med_none_as_maximum']
        if med_none_as_maximum != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<medNoneAsMaximum></medNoneAsMaximum>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<medNoneAsMaximum>(.*)</medNoneAsMaximum>.*', recv_xml)

                if re_find:
                    result["med_none_as_maximum"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != med_none_as_maximum:
                        need_cfg = True
                else:
                    need_cfg = True

        router_id_neglect = module.params['router_id_neglect']
        if router_id_neglect != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<routerIdNeglect></routerIdNeglect>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routerIdNeglect>(.*)</routerIdNeglect>.*', recv_xml)

                if re_find:
                    result["router_id_neglect"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != router_id_neglect:
                        need_cfg = True
                else:
                    need_cfg = True

        igp_metric_ignore = module.params['igp_metric_ignore']
        if igp_metric_ignore != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<igpMetricIgnore></igpMetricIgnore>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<igpMetricIgnore>(.*)</igpMetricIgnore>.*', recv_xml)

                if re_find:
                    result["igp_metric_ignore"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != igp_metric_ignore:
                        need_cfg = True
                else:
                    need_cfg = True

        always_compare_med = module.params['always_compare_med']
        if always_compare_med != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<alwaysCompareMed></alwaysCompareMed>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<alwaysCompareMed>(.*)</alwaysCompareMed>.*', recv_xml)

                if re_find:
                    result["always_compare_med"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != always_compare_med:
                        need_cfg = True
                else:
                    need_cfg = True

        determin_med = module.params['determin_med']
        if determin_med != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<determinMed></determinMed>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<determinMed>(.*)</determinMed>.*', recv_xml)

                if re_find:
                    result["determin_med"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != determin_med:
                        need_cfg = True
                else:
                    need_cfg = True

        preference_external = module.params['preference_external']
        if preference_external:
            if int(preference_external) > 255 or int(preference_external) < 1:
                module.fail_json(
                    msg='Error: The value of preference_external %s is out of [1 - 255].' % preference_external)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<preferenceExternal></preferenceExternal>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<preferenceExternal>(.*)</preferenceExternal>.*', recv_xml)

                if re_find:
                    result["preference_external"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != preference_external:
                        need_cfg = True
                else:
                    need_cfg = True

        preference_internal = module.params['preference_internal']
        if preference_internal:
            if int(preference_internal) > 255 or int(preference_internal) < 1:
                module.fail_json(
                    msg='Error: The value of preference_internal %s is out of [1 - 255].' % preference_internal)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<preferenceInternal></preferenceInternal>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<preferenceInternal>(.*)</preferenceInternal>.*', recv_xml)

                if re_find:
                    result["preference_internal"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != preference_internal:
                        need_cfg = True
                else:
                    need_cfg = True

        preference_local = module.params['preference_local']
        if preference_local:
            if int(preference_local) > 255 or int(preference_local) < 1:
                module.fail_json(
                    msg='Error: The value of preference_local %s is out of [1 - 255].' % preference_local)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<preferenceLocal></preferenceLocal>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<preferenceLocal>(.*)</preferenceLocal>.*', recv_xml)

                if re_find:
                    result["preference_local"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != preference_local:
                        need_cfg = True
                else:
                    need_cfg = True

        prefrence_policy_name = module.params['prefrence_policy_name']
        if prefrence_policy_name:
            if len(prefrence_policy_name) > 40 or len(prefrence_policy_name) < 1:
                module.fail_json(
                    msg='Error: The len of prefrence_policy_name %s is out of [1 - 40].' % prefrence_policy_name)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<prefrencePolicyName></prefrencePolicyName>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<prefrencePolicyName>(.*)</prefrencePolicyName>.*', recv_xml)

                if re_find:
                    result["prefrence_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != prefrence_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        reflect_between_client = module.params['reflect_between_client']
        if reflect_between_client != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<reflectBetweenClient></reflectBetweenClient>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectBetweenClient>(.*)</reflectBetweenClient>.*', recv_xml)

                if re_find:
                    result["reflect_between_client"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != reflect_between_client:
                        need_cfg = True
                else:
                    need_cfg = True

        reflector_cluster_id = module.params['reflector_cluster_id']
        if reflector_cluster_id:
            if int(reflector_cluster_id) < 0:
                module.fail_json(
                    msg='Error: The value of reflector_cluster_id %s is out of '
                        '[1 - 4294967295].' % reflector_cluster_id)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<reflectorClusterId></reflectorClusterId>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectorClusterId>(.*)</reflectorClusterId>.*', recv_xml)

                if re_find:
                    result["reflector_cluster_id"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != reflector_cluster_id:
                        need_cfg = True
                else:
                    need_cfg = True

        reflector_cluster_ipv4 = module.params['reflector_cluster_ipv4']
        if reflector_cluster_ipv4:
            if len(reflector_cluster_ipv4) > 255:
                module.fail_json(
                    msg='Error: The len of reflector_cluster_ipv4 %s is out of [0 - 255].' % reflector_cluster_ipv4)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<reflectorClusterIpv4></reflectorClusterIpv4>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectorClusterIpv4>(.*)</reflectorClusterIpv4>.*', recv_xml)

                if re_find:
                    result["reflector_cluster_ipv4"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != reflector_cluster_ipv4:
                        need_cfg = True
                else:
                    need_cfg = True

        rr_filter_number = module.params['rr_filter_number']
        if rr_filter_number:
            if len(rr_filter_number) > 51 or len(rr_filter_number) < 1:
                module.fail_json(
                    msg='Error: The len of rr_filter_number %s is out of [1 - 51].' % rr_filter_number)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<rrFilterNumber></rrFilterNumber>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<rrFilterNumber>(.*)</rrFilterNumber>.*', recv_xml)

                if re_find:
                    result["rr_filter_number"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != rr_filter_number:
                        need_cfg = True
                else:
                    need_cfg = True

        policy_vpn_target = module.params['policy_vpn_target']
        if policy_vpn_target != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<policyVpnTarget></policyVpnTarget>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<policyVpnTarget>(.*)</policyVpnTarget>.*', recv_xml)

                if re_find:
                    result["policy_vpn_target"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != policy_vpn_target:
                        need_cfg = True
                else:
                    need_cfg = True

        next_hop_sel_depend_type = module.params['next_hop_sel_depend_type']
        if next_hop_sel_depend_type:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<nextHopSelDependType></nextHopSelDependType>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<nextHopSelDependType>(.*)</nextHopSelDependType>.*', recv_xml)

                if re_find:
                    result["next_hop_sel_depend_type"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != next_hop_sel_depend_type:
                        need_cfg = True
                else:
                    need_cfg = True

        nhp_relay_route_policy_name = module.params[
            'nhp_relay_route_policy_name']
        if nhp_relay_route_policy_name:
            if len(nhp_relay_route_policy_name) > 40 or len(nhp_relay_route_policy_name) < 1:
                module.fail_json(
                    msg='Error: The len of nhp_relay_route_policy_name %s is '
                        'out of [1 - 40].' % nhp_relay_route_policy_name)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<nhpRelayRoutePolicyName></nhpRelayRoutePolicyName>" + \
                CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<nhpRelayRoutePolicyName>(.*)</nhpRelayRoutePolicyName>.*', recv_xml)

                if re_find:
                    result["nhp_relay_route_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != nhp_relay_route_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<ebgpIfSensitive></ebgpIfSensitive>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', recv_xml)

                if re_find:
                    result["ebgp_if_sensitive"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != ebgp_if_sensitive:
                        need_cfg = True
                else:
                    need_cfg = True

        reflect_chg_path = module.params['reflect_chg_path']
        if reflect_chg_path != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<reflectChgPath></reflectChgPath>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectChgPath>(.*)</reflectChgPath>.*', recv_xml)

                if re_find:
                    result["reflect_chg_path"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != reflect_chg_path:
                        need_cfg = True
                else:
                    need_cfg = True

        add_path_sel_num = module.params['add_path_sel_num']
        if add_path_sel_num:
            if int(add_path_sel_num) > 64 or int(add_path_sel_num) < 2:
                module.fail_json(
                    msg='Error: The value of add_path_sel_num %s is out of [2 - 64].' % add_path_sel_num)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<addPathSelNum></addPathSelNum>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<addPathSelNum>(.*)</addPathSelNum>.*', recv_xml)

                if re_find:
                    result["add_path_sel_num"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != add_path_sel_num:
                        need_cfg = True
                else:
                    need_cfg = True

        route_sel_delay = module.params['route_sel_delay']
        if route_sel_delay:
            if int(route_sel_delay) > 3600 or int(route_sel_delay) < 0:
                module.fail_json(
                    msg='Error: The value of route_sel_delay %s is out of [0 - 3600].' % route_sel_delay)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<routeSelDelay></routeSelDelay>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeSelDelay>(.*)</routeSelDelay>.*', recv_xml)

                if re_find:
                    result["route_sel_delay"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != route_sel_delay:
                        need_cfg = True
                else:
                    need_cfg = True

        allow_invalid_as = module.params['allow_invalid_as']
        if allow_invalid_as != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<allowInvalidAs></allowInvalidAs>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<allowInvalidAs>(.*)</allowInvalidAs>.*', recv_xml)

                if re_find:
                    result["allow_invalid_as"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != allow_invalid_as:
                        need_cfg = True
                else:
                    need_cfg = True

        policy_ext_comm_enable = module.params['policy_ext_comm_enable']
        if policy_ext_comm_enable != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<policyExtCommEnable></policyExtCommEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<policyExtCommEnable>(.*)</policyExtCommEnable>.*', recv_xml)

                if re_find:
                    result["policy_ext_comm_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != policy_ext_comm_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        supernet_uni_adv = module.params['supernet_uni_adv']
        if supernet_uni_adv != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<supernetUniAdv></supernetUniAdv>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<supernetUniAdv>(.*)</supernetUniAdv>.*', recv_xml)

                if re_find:
                    result["supernet_uni_adv"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != supernet_uni_adv:
                        need_cfg = True
                else:
                    need_cfg = True

        supernet_label_adv = module.params['supernet_label_adv']
        if supernet_label_adv != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<supernetLabelAdv></supernetLabelAdv>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<supernetLabelAdv>(.*)</supernetLabelAdv>.*', recv_xml)

                if re_find:
                    result["supernet_label_adv"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != supernet_label_adv:
                        need_cfg = True
                else:
                    need_cfg = True

        ingress_lsp_policy_name = module.params['ingress_lsp_policy_name']
        if ingress_lsp_policy_name:
            if len(ingress_lsp_policy_name) > 40 or len(ingress_lsp_policy_name) < 1:
                module.fail_json(
                    msg='Error: The len of ingress_lsp_policy_name %s is out of [1 - 40].' % ingress_lsp_policy_name)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<ingressLspPolicyName></ingressLspPolicyName>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ingressLspPolicyName>(.*)</ingressLspPolicyName>.*', recv_xml)

                if re_find:
                    result["ingress_lsp_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != ingress_lsp_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        originator_prior = module.params['originator_prior']
        if originator_prior != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<originatorPrior></originatorPrior>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<originatorPrior>(.*)</originatorPrior>.*', recv_xml)

                if re_find:
                    result["originator_prior"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != originator_prior:
                        need_cfg = True
                else:
                    need_cfg = True

        lowest_priority = module.params['lowest_priority']
        if lowest_priority != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<lowestPriority></lowestPriority>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<lowestPriority>(.*)</lowestPriority>.*', recv_xml)

                if re_find:
                    result["lowest_priority"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != lowest_priority:
                        need_cfg = True
                else:
                    need_cfg = True

        relay_delay_enable = module.params['relay_delay_enable']
        if relay_delay_enable != 'no_use':

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type) + \
                "<relayDelayEnable></relayDelayEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in recv_xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<relayDelayEnable>(.*)</relayDelayEnable>.*', recv_xml)

                if re_find:
                    result["relay_delay_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != relay_delay_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_import_network_route(self, **kwargs):
        """ check_bgp_import_network_route """

        module = kwargs["module"]
        result = dict()
        import_need_cfg = False
        network_need_cfg = False

        vrf_name = module.params['vrf_name']

        state = module.params['state']
        af_type = module.params['af_type']
        import_protocol = module.params['import_protocol']
        import_process_id = module.params['import_process_id']

        if import_protocol and (import_protocol != "direct" and import_protocol != "static"):
            if not import_process_id:
                module.fail_json(
                    msg='Error: Please input import_protocol and import_process_id value at the same time.')
            else:
                if int(import_process_id) < 0:
                    module.fail_json(
                        msg='Error: The value of import_process_id %s is out of [0 - 4294967295].' % import_process_id)

        if import_process_id:
            if not import_protocol:
                module.fail_json(
                    msg='Error: Please input import_protocol and import_process_id value at the same time.')

        network_address = module.params['network_address']
        mask_len = module.params['mask_len']

        if network_address:
            if not mask_len:
                module.fail_json(
                    msg='Error: Please input network_address and mask_len value at the same time.')
        if mask_len:
            if not network_address:
                module.fail_json(
                    msg='Error: Please input network_address and mask_len value at the same time.')

        conf_str = CE_GET_BGP_IMPORT_AND_NETWORK_ROUTE % (vrf_name, af_type)
        recv_xml = self.netconf_get_config(module=module, conf_str=conf_str)

        if import_protocol:

            if import_protocol == "direct" or import_protocol == "static":
                import_process_id = "0"
            else:
                if not import_process_id or import_process_id == "0":
                    module.fail_json(
                        msg='Error: Please input import_process_id not 0 when import_protocol is '
                            '[ospf, isis, rip, ospfv3, ripng].')

            bgp_import_route_new = (import_protocol, import_process_id)

            if state == "present":
                if "<data/>" in recv_xml:
                    import_need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<importProtocol>(.*)</importProtocol>.*\s.*<importProcessId>(.*)</importProcessId>.*',
                        recv_xml)

                    if re_find:
                        result["bgp_import_route"] = re_find
                        result["vrf_name"] = vrf_name
                        if bgp_import_route_new not in re_find:
                            import_need_cfg = True
                    else:
                        import_need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<importProtocol>(.*)</importProtocol>.*\s.*<importProcessId>(.*)</importProcessId>.*',
                        recv_xml)

                    if re_find:
                        result["bgp_import_route"] = re_find
                        result["vrf_name"] = vrf_name
                        if bgp_import_route_new in re_find:
                            import_need_cfg = True

        if network_address and mask_len:

            bgp_network_route_new = (network_address, mask_len)

            if not check_ip_addr(ipaddr=network_address):
                module.fail_json(
                    msg='Error: The network_address %s is invalid.' % network_address)

            if len(mask_len) > 128:
                module.fail_json(
                    msg='Error: The len of mask_len %s is out of [0 - 128].' % mask_len)

            if state == "present":
                if "<data/>" in recv_xml:
                    network_need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<networkAddress>(.*)</networkAddress>.*\s.*<maskLen>(.*)</maskLen>.*', recv_xml)

                    if re_find:
                        result["bgp_network_route"] = re_find
                        result["vrf_name"] = vrf_name
                        if bgp_network_route_new not in re_find:
                            network_need_cfg = True
                    else:
                        network_need_cfg = True
            else:
                if "<data/>" in recv_xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<networkAddress>(.*)</networkAddress>.*\s.*<maskLen>(.*)</maskLen>.*', recv_xml)

                    if re_find:
                        result["bgp_network_route"] = re_find
                        result["vrf_name"] = vrf_name
                        if bgp_network_route_new in re_find:
                            network_need_cfg = True

        result["import_need_cfg"] = import_need_cfg
        result["network_need_cfg"] = network_need_cfg
        return result

    def merge_bgp_af(self, **kwargs):
        """ merge_bgp_af """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']

        conf_str = CE_MERGE_BGP_ADDRESS_FAMILY_HEADER % (
            vrf_name, af_type) + CE_MERGE_BGP_ADDRESS_FAMILY_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp address family failed.')

        cmds = []

        cmd = "ipv4-family vpn-instance %s" % vrf_name

        if af_type == "ipv4multi":
            cmd = "ipv4-family multicast"
        elif af_type == "ipv4vpn":
            cmd = "ipv4-family vpnv4"
        elif af_type == "ipv6uni":
            cmd = "ipv6-family vpn-instance %s" % vrf_name
            if vrf_name == "_public_":
                cmd = "ipv6-family unicast"
        elif af_type == "ipv6vpn":
            cmd = "ipv6-family vpnv6"
        elif af_type == "evpn":
            cmd = "l2vpn-family evpn"
        cmds.append(cmd)

        return cmds

    def create_bgp_af(self, **kwargs):
        """ create_bgp_af """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']

        conf_str = CE_CREATE_BGP_ADDRESS_FAMILY_HEADER % (
            vrf_name, af_type) + CE_CREATE_BGP_ADDRESS_FAMILY_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create bgp address family failed.')

        cmds = []

        cmd = "ipv4-family vpn-instance %s" % vrf_name

        if af_type == "ipv4multi":
            cmd = "ipv4-family multicast"
        elif af_type == "ipv4vpn":
            cmd = "ipv4-family vpnv4"
        elif af_type == "ipv6uni":
            cmd = "ipv6-family vpn-instance %s" % vrf_name
            if vrf_name == "_public_":
                cmd = "ipv6-family unicast"
        elif af_type == "ipv6vpn":
            cmd = "ipv6-family vpnv6"
        elif af_type == "evpn":
            cmd = "l2vpn-family evpn"
        cmds.append(cmd)

        return cmds

    def delete_bgp_af(self, **kwargs):
        """ delete_bgp_af """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']

        conf_str = CE_DELETE_BGP_ADDRESS_FAMILY_HEADER % (
            vrf_name, af_type) + CE_DELETE_BGP_ADDRESS_FAMILY_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete bgp address family failed.')

        cmds = []

        cmd = "undo ipv4-family vpn-instance %s" % vrf_name

        if af_type == "ipv4multi":
            cmd = "undo ipv4-family multicast"
        elif af_type == "ipv4vpn":
            cmd = "undo ipv4-family vpnv4"
        elif af_type == "ipv6uni":
            cmd = "undo ipv6-family vpn-instance %s" % vrf_name
            if vrf_name == "_public_":
                cmd = "undo ipv6-family unicast"
        elif af_type == "ipv6vpn":
            cmd = "undo ipv6-family vpnv6"
        elif af_type == "evpn":
            cmd = "l2vpn-family evpn"
        cmds.append(cmd)

        return cmds

    def merge_bgp_af_other(self, **kwargs):
        """ merge_bgp_af_other """

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']

        conf_str = CE_MERGE_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type)

        cmds = []

        max_load_ibgp_num = module.params['max_load_ibgp_num']
        if max_load_ibgp_num:
            conf_str += "<maxLoadIbgpNum>%s</maxLoadIbgpNum>" % max_load_ibgp_num

            cmd = "maximum load-balancing ibgp %s" % max_load_ibgp_num
            cmds.append(cmd)

        ibgp_ecmp_nexthop_changed = module.params['ibgp_ecmp_nexthop_changed']
        if ibgp_ecmp_nexthop_changed != 'no_use':
            conf_str += "<ibgpEcmpNexthopChanged>%s</ibgpEcmpNexthopChanged>" % ibgp_ecmp_nexthop_changed

            if ibgp_ecmp_nexthop_changed == "true":
                cmd = "maximum load-balancing ibgp %s ecmp-nexthop-changed" % max_load_ibgp_num
                cmds.append(cmd)
            else:
                cmd = "undo maximum load-balancing ibgp %s ecmp-nexthop-changed" % max_load_ibgp_num
                cmds.append(cmd)
        max_load_ebgp_num = module.params['max_load_ebgp_num']
        if max_load_ebgp_num:
            conf_str += "<maxLoadEbgpNum>%s</maxLoadEbgpNum>" % max_load_ebgp_num

            cmd = "maximum load-balancing ebgp %s" % max_load_ebgp_num
            cmds.append(cmd)

        ebgp_ecmp_nexthop_changed = module.params['ebgp_ecmp_nexthop_changed']
        if ebgp_ecmp_nexthop_changed != 'no_use':
            conf_str += "<ebgpEcmpNexthopChanged>%s</ebgpEcmpNexthopChanged>" % ebgp_ecmp_nexthop_changed

            if ebgp_ecmp_nexthop_changed == "true":
                cmd = "maximum load-balancing ebgp %s ecmp-nexthop-changed" % max_load_ebgp_num
            else:
                cmd = "undo maximum load-balancing ebgp %s ecmp-nexthop-changed" % max_load_ebgp_num
            cmds.append(cmd)

        maximum_load_balance = module.params['maximum_load_balance']
        if maximum_load_balance:
            conf_str += "<maximumLoadBalance>%s</maximumLoadBalance>" % maximum_load_balance

            cmd = "maximum load-balancing %s" % maximum_load_balance
            cmds.append(cmd)

        ecmp_nexthop_changed = module.params['ecmp_nexthop_changed']
        if ecmp_nexthop_changed != 'no_use':
            conf_str += "<ecmpNexthopChanged>%s</ecmpNexthopChanged>" % ecmp_nexthop_changed

            if ecmp_nexthop_changed == "true":
                cmd = "maximum load-balancing %s ecmp-nexthop-changed" % maximum_load_balance
            else:
                cmd = "undo maximum load-balancing %s ecmp-nexthop-changed" % maximum_load_balance
            cmds.append(cmd)

        default_local_pref = module.params['default_local_pref']
        if default_local_pref:
            conf_str += "<defaultLocalPref>%s</defaultLocalPref>" % default_local_pref

            cmd = "default local-preference %s" % default_local_pref
            cmds.append(cmd)

        default_med = module.params['default_med']
        if default_med:
            conf_str += "<defaultMed>%s</defaultMed>" % default_med

            cmd = "default med %s" % default_med
            cmds.append(cmd)

        default_rt_import_enable = module.params['default_rt_import_enable']
        if default_rt_import_enable != 'no_use':
            conf_str += "<defaultRtImportEnable>%s</defaultRtImportEnable>" % default_rt_import_enable

            if default_rt_import_enable == "true":
                cmd = "default-route imported"
            else:
                cmd = "undo default-route imported"
            cmds.append(cmd)

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId>%s</routerId>" % router_id

            cmd = "router-id %s" % router_id
            cmds.append(cmd)

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel != 'no_use':
            conf_str += "<vrfRidAutoSel>%s</vrfRidAutoSel>" % vrf_rid_auto_sel
            family = "ipv4-family"
            if af_type == "ipv6uni":
                family = "ipv6-family"
            if vrf_rid_auto_sel == "true":
                cmd = "%s vpn-instance %s" % (family, vrf_name)
                cmds.append(cmd)
                cmd = "router-id auto-select"
                cmds.append(cmd)
            else:
                cmd = "%s vpn-instance %s" % (family, vrf_name)
                cmds.append(cmd)
                cmd = "undo router-id auto-select"
                cmds.append(cmd)

        nexthop_third_party = module.params['nexthop_third_party']
        if nexthop_third_party != 'no_use':
            conf_str += "<nexthopThirdParty>%s</nexthopThirdParty>" % nexthop_third_party

            if nexthop_third_party == "true":
                cmd = "nexthop third-party"
            else:
                cmd = "undo nexthop third-party"
            cmds.append(cmd)

        summary_automatic = module.params['summary_automatic']
        if summary_automatic != 'no_use':
            conf_str += "<summaryAutomatic>%s</summaryAutomatic>" % summary_automatic

            if summary_automatic == "true":
                cmd = "summary automatic"
            else:
                cmd = "undo summary automatic"
            cmds.append(cmd)

        auto_frr_enable = module.params['auto_frr_enable']
        if auto_frr_enable != 'no_use':
            conf_str += "<autoFrrEnable>%s</autoFrrEnable>" % auto_frr_enable

            if auto_frr_enable == "true":
                cmd = "auto-frr"
            else:
                cmd = "undo auto-frr"
            cmds.append(cmd)

        load_balancing_as_path_ignore = module.params[
            'load_balancing_as_path_ignore']
        if load_balancing_as_path_ignore != 'no_use':
            conf_str += "<loadBalancingAsPathIgnore>%s</loadBalancingAsPathIgnore>" % load_balancing_as_path_ignore

            if load_balancing_as_path_ignore == "true":
                cmd = "load-balancing as-path-ignore"
            else:
                cmd = "undo load-balancing as-path-ignore"
            cmds.append(cmd)

        rib_only_enable = module.params['rib_only_enable']
        if rib_only_enable != 'no_use':
            conf_str += "<ribOnlyEnable>%s</ribOnlyEnable>" % rib_only_enable

            if rib_only_enable == "true":
                cmd = "routing-table rib-only"
            else:
                cmd = "undo routing-table rib-only"
            cmds.append(cmd)

        rib_only_policy_name = module.params['rib_only_policy_name']
        if rib_only_policy_name and rib_only_enable == "true":
            conf_str += "<ribOnlyPolicyName>%s</ribOnlyPolicyName>" % rib_only_policy_name

            cmd = "routing-table rib-only route-policy %s" % rib_only_policy_name
            cmds.append(cmd)

        active_route_advertise = module.params['active_route_advertise']
        if active_route_advertise != 'no_use':
            conf_str += "<activeRouteAdvertise>%s</activeRouteAdvertise>" % active_route_advertise

            if active_route_advertise == "true":
                cmd = "active-route-advertise"
            else:
                cmd = "undo active-route-advertise"
            cmds.append(cmd)

        as_path_neglect = module.params['as_path_neglect']
        if as_path_neglect != 'no_use':
            conf_str += "<asPathNeglect>%s</asPathNeglect>" % as_path_neglect

            if as_path_neglect == "true":
                cmd = "bestroute as-path-ignore"
            else:
                cmd = "undo bestroute as-path-ignore"
            cmds.append(cmd)

        med_none_as_maximum = module.params['med_none_as_maximum']
        if med_none_as_maximum != 'no_use':
            conf_str += "<medNoneAsMaximum>%s</medNoneAsMaximum>" % med_none_as_maximum

            if med_none_as_maximum == "true":
                cmd = "bestroute med-none-as-maximum"
            else:
                cmd = "undo bestroute med-none-as-maximum"
            cmds.append(cmd)

        router_id_neglect = module.params['router_id_neglect']
        if router_id_neglect != 'no_use':
            conf_str += "<routerIdNeglect>%s</routerIdNeglect>" % router_id_neglect

            if router_id_neglect == "true":
                cmd = "bestroute router-id-ignore"
            else:
                cmd = "undo bestroute router-id-ignore"
            cmds.append(cmd)

        igp_metric_ignore = module.params['igp_metric_ignore']
        if igp_metric_ignore != 'no_use':
            conf_str += "<igpMetricIgnore>%s</igpMetricIgnore>" % igp_metric_ignore

            if igp_metric_ignore == "true":
                cmd = "bestroute igp-metric-ignore"
                cmds.append(cmd)
            else:
                cmd = "undo bestroute igp-metric-ignore"
                cmds.append(cmd)
        always_compare_med = module.params['always_compare_med']
        if always_compare_med != 'no_use':
            conf_str += "<alwaysCompareMed>%s</alwaysCompareMed>" % always_compare_med

            if always_compare_med == "true":
                cmd = "compare-different-as-med"
                cmds.append(cmd)
            else:
                cmd = "undo compare-different-as-med"
                cmds.append(cmd)
        determin_med = module.params['determin_med']
        if determin_med != 'no_use':
            conf_str += "<determinMed>%s</determinMed>" % determin_med

            if determin_med == "true":
                cmd = "deterministic-med"
                cmds.append(cmd)
            else:
                cmd = "undo deterministic-med"
                cmds.append(cmd)

        preference_external = module.params['preference_external']
        preference_internal = module.params['preference_internal']
        preference_local = module.params['preference_local']
        if any([preference_external, preference_internal, preference_local]):
            preference_external = preference_external or "255"
            preference_internal = preference_internal or "255"
            preference_local = preference_local or "255"

            conf_str += "<preferenceExternal>%s</preferenceExternal>" % preference_external
            conf_str += "<preferenceInternal>%s</preferenceInternal>" % preference_internal
            conf_str += "<preferenceLocal>%s</preferenceLocal>" % preference_local

            cmd = "preference %s %s %s" % (
                preference_external, preference_internal, preference_local)
            cmds.append(cmd)

        prefrence_policy_name = module.params['prefrence_policy_name']
        if prefrence_policy_name:
            conf_str += "<prefrencePolicyName>%s</prefrencePolicyName>" % prefrence_policy_name

            cmd = "preference route-policy %s" % prefrence_policy_name
            cmds.append(cmd)

        reflect_between_client = module.params['reflect_between_client']
        if reflect_between_client != 'no_use':
            conf_str += "<reflectBetweenClient>%s</reflectBetweenClient>" % reflect_between_client

            if reflect_between_client == "true":
                cmd = "reflect between-clients"
            else:
                cmd = "undo reflect between-clients"
            cmds.append(cmd)

        reflector_cluster_id = module.params['reflector_cluster_id']
        if reflector_cluster_id:
            conf_str += "<reflectorClusterId>%s</reflectorClusterId>" % reflector_cluster_id

            cmd = "reflector cluster-id %s" % reflector_cluster_id
            cmds.append(cmd)

        reflector_cluster_ipv4 = module.params['reflector_cluster_ipv4']
        if reflector_cluster_ipv4:
            conf_str += "<reflectorClusterIpv4>%s</reflectorClusterIpv4>" % reflector_cluster_ipv4

            cmd = "reflector cluster-id %s" % reflector_cluster_ipv4
            cmds.append(cmd)

        rr_filter_number = module.params['rr_filter_number']
        if rr_filter_number:
            conf_str += "<rrFilterNumber>%s</rrFilterNumber>" % rr_filter_number
            cmd = 'rr-filter %s' % rr_filter_number
            cmds.append(cmd)

        policy_vpn_target = module.params['policy_vpn_target']
        if policy_vpn_target != 'no_use':
            conf_str += "<policyVpnTarget>%s</policyVpnTarget>" % policy_vpn_target
            if policy_vpn_target == 'true':
                cmd = 'policy vpn-target'
            else:
                cmd = 'undo policy vpn-target'
            cmds.append(cmd)

        next_hop_sel_depend_type = module.params['next_hop_sel_depend_type']
        if next_hop_sel_depend_type:
            conf_str += "<nextHopSelDependType>%s</nextHopSelDependType>" % next_hop_sel_depend_type

        nhp_relay_route_policy_name = module.params[
            'nhp_relay_route_policy_name']
        if nhp_relay_route_policy_name:
            conf_str += "<nhpRelayRoutePolicyName>%s</nhpRelayRoutePolicyName>" % nhp_relay_route_policy_name

            cmd = "nexthop recursive-lookup route-policy %s" % nhp_relay_route_policy_name
            cmds.append(cmd)

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive != 'no_use':
            conf_str += "<ebgpIfSensitive>%s</ebgpIfSensitive>" % ebgp_if_sensitive

            if ebgp_if_sensitive == "true":
                cmd = "ebgp-interface-sensitive"
            else:
                cmd = "undo ebgp-interface-sensitive"
            cmds.append(cmd)

        reflect_chg_path = module.params['reflect_chg_path']
        if reflect_chg_path != 'no_use':
            conf_str += "<reflectChgPath>%s</reflectChgPath>" % reflect_chg_path

            if reflect_chg_path == "true":
                cmd = "reflect change-path-attribute"
            else:
                cmd = "undo reflect change-path-attribute"
            cmds.append(cmd)

        add_path_sel_num = module.params['add_path_sel_num']
        if add_path_sel_num:
            conf_str += "<addPathSelNum>%s</addPathSelNum>" % add_path_sel_num

            cmd = "bestroute add-path path-number %s" % add_path_sel_num
            cmds.append(cmd)

        route_sel_delay = module.params['route_sel_delay']
        if route_sel_delay:
            conf_str += "<routeSelDelay>%s</routeSelDelay>" % route_sel_delay

            cmd = "route-select delay %s" % route_sel_delay
            cmds.append(cmd)

        allow_invalid_as = module.params['allow_invalid_as']
        if allow_invalid_as != 'no_use':
            conf_str += "<allowInvalidAs>%s</allowInvalidAs>" % allow_invalid_as

        policy_ext_comm_enable = module.params['policy_ext_comm_enable']
        if policy_ext_comm_enable != 'no_use':
            conf_str += "<policyExtCommEnable>%s</policyExtCommEnable>" % policy_ext_comm_enable

            if policy_ext_comm_enable == "true":
                cmd = "ext-community-change enable"
            else:
                cmd = "undo ext-community-change enable"
            cmds.append(cmd)

        supernet_uni_adv = module.params['supernet_uni_adv']
        if supernet_uni_adv != 'no_use':
            conf_str += "<supernetUniAdv>%s</supernetUniAdv>" % supernet_uni_adv

            if supernet_uni_adv == "true":
                cmd = "supernet unicast advertise enable"
            else:
                cmd = "undo supernet unicast advertise enable"
            cmds.append(cmd)

        supernet_label_adv = module.params['supernet_label_adv']
        if supernet_label_adv != 'no_use':
            conf_str += "<supernetLabelAdv>%s</supernetLabelAdv>" % supernet_label_adv

            if supernet_label_adv == "true":
                cmd = "supernet label-route advertise enable"
            else:
                cmd = "undo supernet label-route advertise enable"
            cmds.append(cmd)

        ingress_lsp_policy_name = module.params['ingress_lsp_policy_name']
        if ingress_lsp_policy_name:
            conf_str += "<ingressLspPolicyName>%s</ingressLspPolicyName>" % ingress_lsp_policy_name
            cmd = "ingress-lsp trigger route-policy %s" % ingress_lsp_policy_name
            cmds.append(cmd)

        originator_prior = module.params['originator_prior']
        if originator_prior != 'no_use':
            conf_str += "<originatorPrior>%s</originatorPrior>" % originator_prior
            if originator_prior == "true":
                cmd = "bestroute routerid-prior-clusterlist"
            else:
                cmd = "undo bestroute routerid-prior-clusterlist"
            cmds.append(cmd)

        lowest_priority = module.params['lowest_priority']
        if lowest_priority != 'no_use':
            conf_str += "<lowestPriority>%s</lowestPriority>" % lowest_priority

            if lowest_priority == "true":
                cmd = "advertise lowest-priority on-startup"
            else:
                cmd = "undo advertise lowest-priority on-startup"
            cmds.append(cmd)

        relay_delay_enable = module.params['relay_delay_enable']
        if relay_delay_enable != 'no_use':
            conf_str += "<relayDelayEnable>%s</relayDelayEnable>" % relay_delay_enable

            if relay_delay_enable == "true":
                cmd = "nexthop recursive-lookup restrain enable"
            else:
                cmd = "nexthop recursive-lookup restrain disable"
            cmds.append(cmd)
        conf_str += CE_MERGE_BGP_ADDRESS_FAMILY_TAIL
        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Merge bgp address family other agrus failed.')

        return cmds

    def delete_bgp_af_other(self, **kwargs):
        """ delete_bgp_af_other """

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']

        conf_str = CE_MERGE_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type)

        cmds = []

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId></routerId>"

            cmd = "undo router-id %s" % router_id
            cmds.append(cmd)

        determin_med = module.params['determin_med']
        if determin_med != 'no_use':
            conf_str += "<determinMed></determinMed>"

            cmd = "undo deterministic-med"
            cmds.append(cmd)

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive != 'no_use':
            conf_str += "<ebgpIfSensitive></ebgpIfSensitive>"

            cmd = "undo ebgp-interface-sensitive"
            cmds.append(cmd)

        relay_delay_enable = module.params['relay_delay_enable']
        if relay_delay_enable != 'no_use':
            conf_str += "<relayDelayEnable></relayDelayEnable>"

        conf_str += CE_MERGE_BGP_ADDRESS_FAMILY_TAIL
        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(
                msg='Error: Merge bgp address family other agrus failed.')

        return cmds

    def merge_bgp_import_route(self, **kwargs):
        """ merge_bgp_import_route """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        import_protocol = module.params['import_protocol']
        import_process_id = module.params['import_process_id']

        if import_protocol == "direct" or import_protocol == "static":
            import_process_id = "0"

        conf_str = CE_MERGE_BGP_IMPORT_ROUTE_HEADER % (
            vrf_name, af_type, import_protocol, import_process_id) + CE_MERGE_BGP_IMPORT_ROUTE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp import route failed.')

        cmds = []
        cmd = "import-route %s %s" % (import_protocol, import_process_id)
        if import_protocol == "direct" or import_protocol == "static":
            cmd = "import-route %s" % import_protocol
        cmds.append(cmd)

        return cmds

    def create_bgp_import_route(self, **kwargs):
        """ create_bgp_import_route """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        import_protocol = module.params['import_protocol']
        import_process_id = module.params['import_process_id']

        if import_protocol == "direct" or import_protocol == "static":
            import_process_id = "0"

        conf_str = CE_CREATE_BGP_IMPORT_ROUTE % (
            vrf_name, af_type, import_protocol, import_process_id)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create bgp import route failed.')

        cmds = []
        cmd = "import-route %s %s" % (import_protocol, import_process_id)
        if import_protocol == "direct" or import_protocol == "static":
            cmd = "import-route %s" % import_protocol
        cmds.append(cmd)

        return cmds

    def delete_bgp_import_route(self, **kwargs):
        """ delete_bgp_import_route """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        import_protocol = module.params['import_protocol']
        import_process_id = module.params['import_process_id']

        if import_protocol == "direct" or import_protocol == "static":
            import_process_id = "0"

        conf_str = CE_DELETE_BGP_IMPORT_ROUTE % (
            vrf_name, af_type, import_protocol, import_process_id)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete bgp import route failed.')

        cmds = []
        cmd = "undo import-route %s %s" % (import_protocol, import_process_id)
        if import_protocol == "direct" or import_protocol == "static":
            cmd = "undo import-route %s" % import_protocol
        cmds.append(cmd)

        return cmds

    def merge_bgp_network_route(self, **kwargs):
        """ merge_bgp_network_route """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        network_address = module.params['network_address']
        mask_len = module.params['mask_len']

        conf_str = CE_MERGE_BGP_NETWORK_ROUTE_HEADER % (
            vrf_name, af_type, network_address, mask_len) + CE_MERGE_BGP_NETWORK_ROUTE_TAIL

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Merge bgp network route failed.')

        cmds = []
        cmd = "network %s %s" % (network_address, mask_len)
        cmds.append(cmd)

        return cmds

    def create_bgp_network_route(self, **kwargs):
        """ create_bgp_network_route """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        network_address = module.params['network_address']
        mask_len = module.params['mask_len']

        conf_str = CE_CREATE_BGP_NETWORK_ROUTE % (
            vrf_name, af_type, network_address, mask_len)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Create bgp network route failed.')

        cmds = []
        cmd = "network %s %s" % (network_address, mask_len)
        cmds.append(cmd)

        return cmds

    def delete_bgp_network_route(self, **kwargs):
        """ delete_bgp_network_route """

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        network_address = module.params['network_address']
        mask_len = module.params['mask_len']

        conf_str = CE_DELETE_BGP_NETWORK_ROUTE % (
            vrf_name, af_type, network_address, mask_len)

        recv_xml = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            module.fail_json(msg='Error: Delete bgp network route failed.')

        cmds = []
        cmd = "undo network %s %s" % (network_address, mask_len)
        cmds.append(cmd)

        return cmds


def main():
    """ main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        vrf_name=dict(type='str', required=True),
        af_type=dict(choices=['ipv4uni', 'ipv4multi', 'ipv4vpn',
                              'ipv6uni', 'ipv6vpn', 'evpn'], required=True),
        max_load_ibgp_num=dict(type='str'),
        ibgp_ecmp_nexthop_changed=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        max_load_ebgp_num=dict(type='str'),
        ebgp_ecmp_nexthop_changed=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        maximum_load_balance=dict(type='str'),
        ecmp_nexthop_changed=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        default_local_pref=dict(type='str'),
        default_med=dict(type='str'),
        default_rt_import_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        router_id=dict(type='str'),
        vrf_rid_auto_sel=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        nexthop_third_party=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        summary_automatic=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        auto_frr_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        load_balancing_as_path_ignore=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        rib_only_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        rib_only_policy_name=dict(type='str'),
        active_route_advertise=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        as_path_neglect=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        med_none_as_maximum=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        router_id_neglect=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        igp_metric_ignore=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        always_compare_med=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        determin_med=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        preference_external=dict(type='str'),
        preference_internal=dict(type='str'),
        preference_local=dict(type='str'),
        prefrence_policy_name=dict(type='str'),
        reflect_between_client=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        reflector_cluster_id=dict(type='str'),
        reflector_cluster_ipv4=dict(type='str'),
        rr_filter_number=dict(type='str'),
        policy_vpn_target=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        next_hop_sel_depend_type=dict(
            choices=['default', 'dependTunnel', 'dependIp']),
        nhp_relay_route_policy_name=dict(type='str'),
        ebgp_if_sensitive=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        reflect_chg_path=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        add_path_sel_num=dict(type='str'),
        route_sel_delay=dict(type='str'),
        allow_invalid_as=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        policy_ext_comm_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        supernet_uni_adv=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        supernet_label_adv=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        ingress_lsp_policy_name=dict(type='str'),
        originator_prior=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        lowest_priority=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        relay_delay_enable=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        import_protocol=dict(
            choices=['direct', 'ospf', 'isis', 'static', 'rip', 'ospfv3', 'ripng']),
        import_process_id=dict(type='str'),
        network_address=dict(type='str'),
        mask_len=dict(type='str'))

    argument_spec.update(ce_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    changed = False
    proposed = dict()
    existing = dict()
    end_state = dict()
    updates = []

    state = module.params['state']
    vrf_name = module.params['vrf_name']
    af_type = module.params['af_type']
    max_load_ibgp_num = module.params['max_load_ibgp_num']
    ibgp_ecmp_nexthop_changed = module.params['ibgp_ecmp_nexthop_changed']
    max_load_ebgp_num = module.params['max_load_ebgp_num']
    ebgp_ecmp_nexthop_changed = module.params['ebgp_ecmp_nexthop_changed']
    maximum_load_balance = module.params['maximum_load_balance']
    ecmp_nexthop_changed = module.params['ecmp_nexthop_changed']
    default_local_pref = module.params['default_local_pref']
    default_med = module.params['default_med']
    default_rt_import_enable = module.params['default_rt_import_enable']
    router_id = module.params['router_id']
    vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
    nexthop_third_party = module.params['nexthop_third_party']
    summary_automatic = module.params['summary_automatic']
    auto_frr_enable = module.params['auto_frr_enable']
    load_balancing_as_path_ignore = module.params[
        'load_balancing_as_path_ignore']
    rib_only_enable = module.params['rib_only_enable']
    rib_only_policy_name = module.params['rib_only_policy_name']
    active_route_advertise = module.params['active_route_advertise']
    as_path_neglect = module.params['as_path_neglect']
    med_none_as_maximum = module.params['med_none_as_maximum']
    router_id_neglect = module.params['router_id_neglect']
    igp_metric_ignore = module.params['igp_metric_ignore']
    always_compare_med = module.params['always_compare_med']
    determin_med = module.params['determin_med']
    preference_external = module.params['preference_external']
    preference_internal = module.params['preference_internal']
    preference_local = module.params['preference_local']
    prefrence_policy_name = module.params['prefrence_policy_name']
    reflect_between_client = module.params['reflect_between_client']
    reflector_cluster_id = module.params['reflector_cluster_id']
    reflector_cluster_ipv4 = module.params['reflector_cluster_ipv4']
    rr_filter_number = module.params['rr_filter_number']
    policy_vpn_target = module.params['policy_vpn_target']
    next_hop_sel_depend_type = module.params['next_hop_sel_depend_type']
    nhp_relay_route_policy_name = module.params['nhp_relay_route_policy_name']
    ebgp_if_sensitive = module.params['ebgp_if_sensitive']
    reflect_chg_path = module.params['reflect_chg_path']
    add_path_sel_num = module.params['add_path_sel_num']
    route_sel_delay = module.params['route_sel_delay']
    allow_invalid_as = module.params['allow_invalid_as']
    policy_ext_comm_enable = module.params['policy_ext_comm_enable']
    supernet_uni_adv = module.params['supernet_uni_adv']
    supernet_label_adv = module.params['supernet_label_adv']
    ingress_lsp_policy_name = module.params['ingress_lsp_policy_name']
    originator_prior = module.params['originator_prior']
    lowest_priority = module.params['lowest_priority']
    relay_delay_enable = module.params['relay_delay_enable']
    import_protocol = module.params['import_protocol']
    import_process_id = module.params['import_process_id']
    network_address = module.params['network_address']
    mask_len = module.params['mask_len']

    ce_bgp_af_obj = BgpAf()

    if not ce_bgp_af_obj:
        module.fail_json(msg='Error: Init module failed.')

    # get proposed
    proposed["state"] = state
    if vrf_name:
        proposed["vrf_name"] = vrf_name
    if af_type:
        proposed["af_type"] = af_type
    if max_load_ibgp_num:
        proposed["max_load_ibgp_num"] = max_load_ibgp_num
    if ibgp_ecmp_nexthop_changed != 'no_use':
        proposed["ibgp_ecmp_nexthop_changed"] = ibgp_ecmp_nexthop_changed
    if max_load_ebgp_num:
        proposed["max_load_ebgp_num"] = max_load_ebgp_num
    if ebgp_ecmp_nexthop_changed != 'no_use':
        proposed["ebgp_ecmp_nexthop_changed"] = ebgp_ecmp_nexthop_changed
    if maximum_load_balance:
        proposed["maximum_load_balance"] = maximum_load_balance
    if ecmp_nexthop_changed != 'no_use':
        proposed["ecmp_nexthop_changed"] = ecmp_nexthop_changed
    if default_local_pref:
        proposed["default_local_pref"] = default_local_pref
    if default_med:
        proposed["default_med"] = default_med
    if default_rt_import_enable != 'no_use':
        proposed["default_rt_import_enable"] = default_rt_import_enable
    if router_id:
        proposed["router_id"] = router_id
    if vrf_rid_auto_sel != 'no_use':
        proposed["vrf_rid_auto_sel"] = vrf_rid_auto_sel
    if nexthop_third_party != 'no_use':
        proposed["nexthop_third_party"] = nexthop_third_party
    if summary_automatic != 'no_use':
        proposed["summary_automatic"] = summary_automatic
    if auto_frr_enable != 'no_use':
        proposed["auto_frr_enable"] = auto_frr_enable
    if load_balancing_as_path_ignore != 'no_use':
        proposed["load_balancing_as_path_ignore"] = load_balancing_as_path_ignore
    if rib_only_enable != 'no_use':
        proposed["rib_only_enable"] = rib_only_enable
    if rib_only_policy_name:
        proposed["rib_only_policy_name"] = rib_only_policy_name
    if active_route_advertise != 'no_use':
        proposed["active_route_advertise"] = active_route_advertise
    if as_path_neglect != 'no_use':
        proposed["as_path_neglect"] = as_path_neglect
    if med_none_as_maximum != 'no_use':
        proposed["med_none_as_maximum"] = med_none_as_maximum
    if router_id_neglect != 'no_use':
        proposed["router_id_neglect"] = router_id_neglect
    if igp_metric_ignore != 'no_use':
        proposed["igp_metric_ignore"] = igp_metric_ignore
    if always_compare_med != 'no_use':
        proposed["always_compare_med"] = always_compare_med
    if determin_med != 'no_use':
        proposed["determin_med"] = determin_med
    if preference_external:
        proposed["preference_external"] = preference_external
    if preference_internal:
        proposed["preference_internal"] = preference_internal
    if preference_local:
        proposed["preference_local"] = preference_local
    if prefrence_policy_name:
        proposed["prefrence_policy_name"] = prefrence_policy_name
    if reflect_between_client != 'no_use':
        proposed["reflect_between_client"] = reflect_between_client
    if reflector_cluster_id:
        proposed["reflector_cluster_id"] = reflector_cluster_id
    if reflector_cluster_ipv4:
        proposed["reflector_cluster_ipv4"] = reflector_cluster_ipv4
    if rr_filter_number:
        proposed["rr_filter_number"] = rr_filter_number
    if policy_vpn_target != 'no_use':
        proposed["policy_vpn_target"] = policy_vpn_target
    if next_hop_sel_depend_type:
        proposed["next_hop_sel_depend_type"] = next_hop_sel_depend_type
    if nhp_relay_route_policy_name:
        proposed["nhp_relay_route_policy_name"] = nhp_relay_route_policy_name
    if ebgp_if_sensitive != 'no_use':
        proposed["ebgp_if_sensitive"] = ebgp_if_sensitive
    if reflect_chg_path != 'no_use':
        proposed["reflect_chg_path"] = reflect_chg_path
    if add_path_sel_num:
        proposed["add_path_sel_num"] = add_path_sel_num
    if route_sel_delay:
        proposed["route_sel_delay"] = route_sel_delay
    if allow_invalid_as != 'no_use':
        proposed["allow_invalid_as"] = allow_invalid_as
    if policy_ext_comm_enable != 'no_use':
        proposed["policy_ext_comm_enable"] = policy_ext_comm_enable
    if supernet_uni_adv != 'no_use':
        proposed["supernet_uni_adv"] = supernet_uni_adv
    if supernet_label_adv != 'no_use':
        proposed["supernet_label_adv"] = supernet_label_adv
    if ingress_lsp_policy_name:
        proposed["ingress_lsp_policy_name"] = ingress_lsp_policy_name
    if originator_prior != 'no_use':
        proposed["originator_prior"] = originator_prior
    if lowest_priority != 'no_use':
        proposed["lowest_priority"] = lowest_priority
    if relay_delay_enable != 'no_use':
        proposed["relay_delay_enable"] = relay_delay_enable
    if import_protocol:
        proposed["import_protocol"] = import_protocol
    if import_process_id:
        proposed["import_process_id"] = import_process_id
    if network_address:
        proposed["network_address"] = network_address
    if mask_len:
        proposed["mask_len"] = mask_len

    bgp_af_rst = ce_bgp_af_obj.check_bgp_af_args(module=module)
    bgp_af_other_rst = ce_bgp_af_obj.check_bgp_af_other_args(module=module)
    bgp_af_other_can_del_rst = ce_bgp_af_obj.check_bgp_af_other_can_del(
        module=module)
    bgp_import_network_route_rst = ce_bgp_af_obj.check_bgp_import_network_route(
        module=module)

    # state exist bgp address family config
    exist_tmp = dict()
    for item in bgp_af_rst:
        if item != "need_cfg":
            exist_tmp[item] = bgp_af_rst[item]

    if exist_tmp:
        existing["bgp af"] = exist_tmp
    # state exist bgp address family other config
    exist_tmp = dict()
    for item in bgp_af_other_rst:
        if item != "need_cfg":
            exist_tmp[item] = bgp_af_other_rst[item]
    if exist_tmp:
        existing["bgp af other"] = exist_tmp
    # state exist bgp import route config
    exist_tmp = dict()
    for item in bgp_import_network_route_rst:
        if item != "need_cfg":
            exist_tmp[item] = bgp_import_network_route_rst[item]

    if exist_tmp:
        existing["bgp import & network route"] = exist_tmp

    if state == "present":
        if bgp_af_rst["need_cfg"] and bgp_import_network_route_rst["import_need_cfg"] and \
                bgp_import_network_route_rst["network_need_cfg"]:
            changed = True
            if "af_type" in bgp_af_rst.keys():
                conf_str = CE_MERGE_BGP_ADDRESS_FAMILY_HEADER % (
                    vrf_name, af_type)
            else:
                conf_str = CE_CREATE_BGP_ADDRESS_FAMILY_HEADER % (
                    vrf_name, af_type)

            if "bgp_import_route" in bgp_import_network_route_rst.keys():
                conf_str += CE_BGP_MERGE_IMPORT_UNIT % (
                    import_protocol, import_process_id)
            else:
                conf_str += CE_BGP_CREATE_IMPORT_UNIT % (
                    import_protocol, import_process_id)

            if "bgp_network_route" in bgp_import_network_route_rst.keys():
                conf_str += CE_BGP_MERGE_NETWORK_UNIT % (
                    network_address, mask_len)
            else:
                conf_str += CE_BGP_CREATE_NETWORK_UNIT % (
                    network_address, mask_len)

            conf_str += CE_MERGE_BGP_ADDRESS_FAMILY_TAIL
            recv_xml = ce_bgp_af_obj.netconf_set_config(
                module=module, conf_str=conf_str)

            if "<ok/>" not in recv_xml:
                module.fail_json(
                    msg='Error: Present bgp af_type import and network route failed.')

            cmd = "import-route %s %s" % (import_protocol, import_process_id)
            updates.append(cmd)
            cmd = "network %s %s" % (network_address, mask_len)
            updates.append(cmd)

        elif bgp_import_network_route_rst["import_need_cfg"] and bgp_import_network_route_rst["network_need_cfg"]:
            changed = True
            conf_str = CE_BGP_IMPORT_NETWORK_ROUTE_HEADER % (vrf_name, af_type)

            if "bgp_import_route" in bgp_import_network_route_rst.keys():
                conf_str += CE_BGP_MERGE_IMPORT_UNIT % (
                    import_protocol, import_process_id)
            else:
                conf_str += CE_BGP_CREATE_IMPORT_UNIT % (
                    import_protocol, import_process_id)

            if "bgp_network_route" in bgp_import_network_route_rst.keys():
                conf_str += CE_BGP_MERGE_NETWORK_UNIT % (
                    network_address, mask_len)
            else:
                conf_str += CE_BGP_CREATE_NETWORK_UNIT % (
                    network_address, mask_len)

            conf_str += CE_BGP_IMPORT_NETWORK_ROUTE_TAIL
            recv_xml = ce_bgp_af_obj.netconf_set_config(
                module=module, conf_str=conf_str)

            if "<ok/>" not in recv_xml:
                module.fail_json(
                    msg='Error: Present bgp import and network route failed.')

            cmd = "import-route %s %s" % (import_protocol, import_process_id)
            updates.append(cmd)
            cmd = "network %s %s" % (network_address, mask_len)
            updates.append(cmd)

        else:
            if bgp_af_rst["need_cfg"]:
                if "af_type" in bgp_af_rst.keys():
                    cmd = ce_bgp_af_obj.merge_bgp_af(module=module)
                    changed = True
                    for item in cmd:
                        updates.append(item)
                else:
                    cmd = ce_bgp_af_obj.create_bgp_af(module=module)
                    changed = True
                    for item in cmd:
                        updates.append(item)

            if bgp_af_other_rst["need_cfg"]:
                cmd = ce_bgp_af_obj.merge_bgp_af_other(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

            if bgp_import_network_route_rst["import_need_cfg"]:
                if "bgp_import_route" in bgp_import_network_route_rst.keys():
                    cmd = ce_bgp_af_obj.merge_bgp_import_route(module=module)
                    changed = True
                    for item in cmd:
                        updates.append(item)
                else:
                    cmd = ce_bgp_af_obj.create_bgp_import_route(module=module)
                    changed = True
                    for item in cmd:
                        updates.append(item)

            if bgp_import_network_route_rst["network_need_cfg"]:
                if "bgp_network_route" in bgp_import_network_route_rst.keys():
                    cmd = ce_bgp_af_obj.merge_bgp_network_route(module=module)
                    changed = True
                    for item in cmd:
                        updates.append(item)
                else:
                    cmd = ce_bgp_af_obj.create_bgp_network_route(module=module)
                    changed = True
                    for item in cmd:
                        updates.append(item)

    else:
        if bgp_import_network_route_rst["import_need_cfg"] and bgp_import_network_route_rst["network_need_cfg"]:
            changed = True
            conf_str = CE_BGP_IMPORT_NETWORK_ROUTE_HEADER % (vrf_name, af_type)
            conf_str += CE_BGP_DELETE_IMPORT_UNIT % (
                import_protocol, import_process_id)
            conf_str += CE_BGP_DELETE_NETWORK_UNIT % (
                network_address, mask_len)

            conf_str += CE_BGP_IMPORT_NETWORK_ROUTE_TAIL
            recv_xml = ce_bgp_af_obj.netconf_set_config(
                module=module, conf_str=conf_str)

            if "<ok/>" not in recv_xml:
                module.fail_json(
                    msg='Error: Absent bgp import and network route failed.')

            cmd = "undo import-route %s %s" % (import_protocol,
                                               import_process_id)
            updates.append(cmd)
            cmd = "undo network %s %s" % (network_address, mask_len)
            updates.append(cmd)

        else:
            if bgp_import_network_route_rst["import_need_cfg"]:
                cmd = ce_bgp_af_obj.delete_bgp_import_route(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

            if bgp_import_network_route_rst["network_need_cfg"]:
                cmd = ce_bgp_af_obj.delete_bgp_network_route(module=module)
                changed = True
                for item in cmd:
                    updates.append(item)

        if bgp_af_other_can_del_rst["need_cfg"]:
            cmd = ce_bgp_af_obj.delete_bgp_af_other(module=module)
            changed = True
            for item in cmd:
                updates.append(item)

        if bgp_af_rst["need_cfg"] and not bgp_af_other_can_del_rst["need_cfg"]:
            cmd = ce_bgp_af_obj.delete_bgp_af(module=module)
            changed = True
            for item in cmd:
                updates.append(item)

        if bgp_af_other_rst["need_cfg"]:
            pass

    # state end bgp address family config
    bgp_af_rst = ce_bgp_af_obj.check_bgp_af_args(module=module)
    end_tmp = dict()
    for item in bgp_af_rst:
        if item != "need_cfg":
            end_tmp[item] = bgp_af_rst[item]
    if end_tmp:
        end_state["bgp af"] = end_tmp
    # state end bgp address family other config
    bgp_af_other_rst = ce_bgp_af_obj.check_bgp_af_other_args(module=module)
    end_tmp = dict()
    for item in bgp_af_other_rst:
        if item != "need_cfg":
            end_tmp[item] = bgp_af_other_rst[item]
    if end_tmp:
        end_state["bgp af other"] = end_tmp
    # state end bgp import route config
    bgp_import_network_route_rst = ce_bgp_af_obj.check_bgp_import_network_route(
        module=module)
    end_tmp = dict()
    for item in bgp_import_network_route_rst:
        if item != "need_cfg":
            end_tmp[item] = bgp_import_network_route_rst[item]
    if end_tmp:
        end_state["bgp import & network route"] = end_tmp
    if end_state == existing:
        changed = False
        updates = list()

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state
    results['updates'] = updates

    module.exit_json(**results)


if __name__ == '__main__':
    main()
