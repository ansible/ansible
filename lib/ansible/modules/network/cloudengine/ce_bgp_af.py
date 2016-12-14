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

DOCUMENTATION = '''
---

module: ce_bgp_af
version_added: "2.2"
short_description: Manages BGP Address-family configuration.
description:
    - Manages BGP Address-family configurations on cloudengine switches.
extends_documentation_fragment: cloudengine
author:
    - wangdezhuang (@CloudEngine-Ansible)
notes:
    - The server_type parameter is always required.
options:
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']
    vrf_name:
        description:
            - vpn instance name.
        required: true
        default: _public_
    af_type:
        description:
            - address-family type.
        required: true
        default: ipv4uni
        choices: ['ipv4uni','ipv4multi', 'ipv4vpn', 'ipv6uni', 'ipv6vpn', 'evpn']
    max_load_ibgp_num:
        description:
            - max load ibgp num.
        required: false
        default: none
    ibgp_ecmp_nexthop_changed:
        description:
            - ibgp ecmp nexthop changed.
        required: false
        choices: ['true','false']
        default: none
    max_load_ebgp_num:
        description:
            - max load ebgp num.
        required: false
        default: none
    ebgp_ecmp_nexthop_changed:
        description:
            - ebgp ecmp nexthop changed.
        required: false
        choices: ['true','false']
        default: none
    maximum_load_balance:
        description:
            - maximum load balance.
        required: false
        default: none
    ecmp_nexthop_changed:
        description:
            - ecmp nexthop changed.
        required: false
        choices: ['true','false']
        default: none
    default_local_pref:
        description:
            - default local pref.
        required: false
        default: none
    default_med:
        description:
            - default med.
        required: false
        default: none
    default_rt_import_enable:
        description:
            - default rt import enable.
        required: false
        choices: ['true','false']
        default: none
    router_id:
        description:
            - router id.
        required: false
        default: none
    vrf_rid_auto_sel:
        description:
            - vpn instance auto select route id.
        required: false
        choices: ['true','false']
        default: none
    nexthop_third_party:
        description:
            - nexthop third party.
        required: false
        choices: ['true','false']
        default: none
    summary_automatic:
        description:
            - summary automatic.
        required: false
        choices: ['true','false']
        default: none
    auto_frr_enable:
        description:
            - auto frr enable.
        required: false
        choices: ['true','false']
        default: none
    load_balancing_as_path_ignore:
        description:
            - load balancing as path ignore.
        required: false
        choices: ['true','false']
        default: none
    rib_only_enable:
        description:
            - rib only enable.
        required: false
        choices: ['true','false']
        default: none
    rib_only_policy_name:
        description:
            - rib only policy name.
        required: false
        choices: ['true','false']
        default: none
    active_route_advertise:
        description:
            - active route advertise.
        required: false
        choices: ['true','false']
        default: none
    as_path_neglect:
        description:
            - as path neglect.
        required: false
        choices: ['true','false']
        default: none
    med_none_as_maximum:
        description:
            - med none as maximum.
        required: false
        choices: ['true','false']
        default: none
    router_id_neglect:
        description:
            - router id neglect.
        required: false
        choices: ['true','false']
        default: none
    igp_metric_ignore:
        description:
            - igp metric ignore.
        required: false
        choices: ['true','false']
        default: none
    always_compare_med:
        description:
            - always compare med.
        required: false
        choices: ['true','false']
        default: none
    determin_med:
        description:
            - determin med.
        required: false
        choices: ['true','false']
        default: none
    preference_external:
        description:
            - preference external.
        required: false
        default: none
    preference_internal:
        description:
            - preference internal.
        required: false
        default: none
    preference_local:
        description:
            - preference local.
        required: false
        default: none
    prefrence_policy_name:
        description:
            - prefrence policy name.
        required: false
        default: none
    reflect_between_client:
        description:
            - reflect between client.
        required: false
        choices: ['true','false']
        default: none
    reflector_cluster_id:
        description:
            - reflector cluster id.
        required: false
        default: none
    reflector_cluster_ipv4:
        description:
            - reflector cluster ipv4.
        required: false
        default: none
    rr_filter_number:
        description:
            - rr filter number.
        required: false
        default: none
    policy_vpn_target:
        description:
            - policy vpn target.
        required: false
        choices: ['true','false']
        default: none
    next_hop_sel_depend_type:
        description:
            - next hop select depend type.
        required: false
        choices: ['default','dependTunnel', 'dependIp']
        default: default
    nhp_relay_route_policy_name:
        description:
            - nhp relay route policy name.
        required: false
        default: none
    ebgp_if_sensitive:
        description:
            - ebgp if sensitive.
        required: false
        choices: ['true','false']
        default: none
    reflect_chg_path:
        description:
            - reflect chg path.
        required: false
        choices: ['true','false']
        default: none
    add_path_sel_num:
        description:
            - add path sel num.
        required: false
        default: none
    route_sel_delay:
        description:
            - route sel delay.
        required: false
        default: none
    allow_invalid_as:
        description:
            - allow invalid as.
        required: false
        choices: ['true','false']
        default: none
    policy_ext_comm_enable:
        description:
            - policy ext comm enable.
        required: false
        choices: ['true','false']
        default: none
    supernet_uni_adv:
        description:
            - supernet uni adv.
        required: false
        choices: ['true','false']
        default: none
    supernet_label_adv:
        description:
            - supernet label adv.
        required: false
        choices: ['true','false']
        default: none
    ingress_lsp_policy_name:
        description:
            - ingress lsp policy name.
        required: false
        default: none
    originator_prior:
        description:
            - originator prior.
        required: false
        choices: ['true','false']
        default: none
    lowest_priority:
        description:
            - lowest priority.
        required: false
        choices: ['true','false']
        default: none
    relay_delay_enable:
        description:
            - relay delay enable.
        required: false
        choices: ['true','false']
        default: none
    import_protocol:
        description:
            - import protocol.
        required: false
        choices: ['direct', 'ospf', 'isis', 'static', 'rip', 'ospfv3', 'ripng']
        default: none
    import_process_id:
        description:
            - import process id.
        required: false
        default: none
    network_address:
        description:
            - network address.
        required: false
        default: none
    mask_len:
        description:
            - mask len.
        required: false
        default: none
'''

EXAMPLES = '''
# config BGP Address_Family
  - name: "config BGP Address_Family"
    ce_bgp_af:
        state:  present
        vrf_name:  js
        af_type:  ipv4uni
        host:  {{inventory_hostname}}
        username:  {{username}}
        password:  {{password}}
# config import route
  - name: "config import route"
    ce_bgp_af:
        state:  present
        vrf_name:  js
        af_type:  ipv4uni
        import_protocol:  ospf
        import_process_id:  123
        host:  {{inventory_hostname}}
        username:  {{username}}
        password:  {{password}
# config network route
  - name: "config network route"
    ce_bgp_af:
        state:  present
        vrf_name:  js
        af_type:  ipv4uni
        network_address:  1.1.1.1
        mask_len:  24
        host:  {{inventory_hostname}}
        username:  {{username}}
        password:  {{password}
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"af_type": "ipv4uni", "ibgp_ecmp_nexthop_changed": "true",
             "import_process_id": "123", "import_protocol": "ospf",
             "mask_len": "24", "max_load_ibgp_num": "2",
             "med": "123", "network_address": "1.1.1.1",
             "state": "present", "vrf_name": "js"}
existing:
    description:
        - k/v pairs of existing aaa server
    type: dict
    sample: {}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"bgp af": {"af_type": ["ipv4uni"], "vrf_name": "js"},
             "bgp af other": {"ibgp_ecmp_nexthop_changed": ["true"], "max_load_ibgp_num": ["2"], "vrf_name": "js"},
             "bgp import route": {"bgp_import_route": [["ospf", "123"]], "vrf_name": "js"},
execute_time:
    description: the module execute time
    returned: always
    type: string
    sample: "0:00:03.380753"
'''

import re
import datetime
import socket
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


SUCCESS = """success"""
FAILED = """failed"""


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
                  <afType></afType>
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
                <bgpVrfAF operation="create">
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


class ce_bgp_af(object):
    """ Manages BGP Address-family configuration """

    def __init__(self, **kwargs):
        """ __init__ """

        self.netconf = get_netconf(**kwargs)

    def netconf_get_config(self, **kwargs):
        """ netconf_get_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        try:
            con_obj = self.netconf.get_config(filter=conf_str)
        except RPCError as err:
            module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def netconf_set_config(self, **kwargs):
        """ netconf_set_config """

        module = kwargs["module"]
        conf_str = kwargs["conf_str"]

        try:
            con_obj = self.netconf.set_config(config=conf_str)
        except RPCError as err:
            module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def check_ip_addr(self, **kwargs):
        """ check_ip_addr, Supports IPv4 and IPv6"""

        ipaddr = kwargs["ipaddr"]

        if not ipaddr or '\x00' in ipaddr:
            return False

        try:
            res = socket.getaddrinfo(ipaddr, 0, socket.AF_UNSPEC,
                                     socket.SOCK_STREAM,
                                     0, socket.AI_NUMERICHOST)
            return bool(res)
        except socket.gaierror as err:
            if err.args[0] == socket.EAI_NONAME:
                return False
            raise
        return True

    def check_bgp_af_args(self, **kwargs):
        """check_bgp_af_args"""

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']
        if vrf_name:
            if len(vrf_name) > 31 or len(vrf_name) == 0:
                module.fail_json(
                    msg='the len of vrf_name %s is out of [1 - 31].' % vrf_name)

        state = module.params['state']
        af_type = module.params['af_type']

        conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
            CE_GET_BGP_ADDRESS_FAMILY_TAIL
        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        if state == "present":
            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<afType>(.*)</afType>.*', con_obj.xml)

                if re_find:
                    result["af_type"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != af_type:
                        need_cfg = True
                else:
                    need_cfg = True
        else:
            if "<data/>" in con_obj.xml:
                pass
            else:
                re_find = re.findall(
                    r'.*<afType>(.*)</afType>.*', con_obj.xml)

                if re_find:
                    result["af_type"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] == af_type:
                        need_cfg = True

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_af_other_can_del(self, **kwargs):
        """check_bgp_af_other_can_del"""
        module = kwargs["module"]
        result = dict()
        need_cfg = False

        state = module.params['state']
        vrf_name = module.params['vrf_name']

        router_id = module.params['router_id']
        if router_id:
            if len(router_id) > 255:
                module.fail_json(
                    msg='the len of router_id %s is out of [0 - 255].' % router_id)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<routerId></routerId>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<routerId>(.*)</routerId>.*', con_obj.xml)

                    if re_find:
                        if re_find[0] != router_id:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<routerId>(.*)</routerId>.*', con_obj.xml)

                    if re_find:
                        if re_find[0] == router_id:
                            need_cfg = True
                    else:
                        pass

        determin_med = module.params['determin_med']
        if determin_med:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<determinMed></determinMed>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<determinMed>(.*)</determinMed>.*', con_obj.xml)

                    if re_find:
                        if re_find[0] != determin_med:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<determinMed>(.*)</determinMed>.*', con_obj.xml)

                    if re_find:
                        if re_find[0] == determin_med:
                            need_cfg = True
                    else:
                        pass

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<ebgpIfSensitive></ebgpIfSensitive>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', con_obj.xml)

                    if re_find:
                        if re_find[0] != ebgp_if_sensitive:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', con_obj.xml)

                    if re_find:
                        if re_find[0] == ebgp_if_sensitive:
                            need_cfg = True
                    else:
                        pass

        relay_delay_enable = module.params['relay_delay_enable']
        if relay_delay_enable:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<relayDelayEnable></relayDelayEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<relayDelayEnable>(.*)</relayDelayEnable>.*', con_obj.xml)

                    if re_find:
                        if re_find[0] != relay_delay_enable:
                            need_cfg = True
                    else:
                        need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<relayDelayEnable>(.*)</relayDelayEnable>.*', con_obj.xml)

                    if re_find:
                        if re_find[0] == relay_delay_enable:
                            need_cfg = True
                    else:
                        pass

        result["need_cfg"] = need_cfg
        return result

    def check_bgp_af_other_args(self, **kwargs):
        """check_bgp_af_other_args"""

        module = kwargs["module"]
        result = dict()
        need_cfg = False

        vrf_name = module.params['vrf_name']

        max_load_ibgp_num = module.params['max_load_ibgp_num']
        if max_load_ibgp_num:
            if int(max_load_ibgp_num) > 65535 or int(max_load_ibgp_num) < 1:
                module.fail_json(
                    msg='the value of max_load_ibgp_num %s is out of [1 - 65535].' % max_load_ibgp_num)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<maxLoadIbgpNum></maxLoadIbgpNum>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<maxLoadIbgpNum>(.*)</maxLoadIbgpNum>.*', con_obj.xml)

                if re_find:
                    result["max_load_ibgp_num"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != max_load_ibgp_num:
                        need_cfg = True
                else:
                    need_cfg = True

        ibgp_ecmp_nexthop_changed = module.params['ibgp_ecmp_nexthop_changed']
        if ibgp_ecmp_nexthop_changed:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<ibgpEcmpNexthopChanged></ibgpEcmpNexthopChanged>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ibgpEcmpNexthopChanged>(.*)</ibgpEcmpNexthopChanged>.*', con_obj.xml)

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
                    msg='the value of max_load_ebgp_num %s is out of [1 - 65535].' % max_load_ebgp_num)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<maxLoadEbgpNum></maxLoadEbgpNum>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<maxLoadEbgpNum>(.*)</maxLoadEbgpNum>.*', con_obj.xml)

                if re_find:
                    result["max_load_ebgp_num"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != max_load_ebgp_num:
                        need_cfg = True
                else:
                    need_cfg = True

        ebgp_ecmp_nexthop_changed = module.params['ebgp_ecmp_nexthop_changed']
        if ebgp_ecmp_nexthop_changed:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<ebgpEcmpNexthopChanged></ebgpEcmpNexthopChanged>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ebgpEcmpNexthopChanged>(.*)</ebgpEcmpNexthopChanged>.*', con_obj.xml)

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
                    msg='the value of maximum_load_balance %s is out of [1 - 65535].' % maximum_load_balance)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<maximumLoadBalance></maximumLoadBalance>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<maximumLoadBalance>(.*)</maximumLoadBalance>.*', con_obj.xml)

                if re_find:
                    result["maximum_load_balance"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != maximum_load_balance:
                        need_cfg = True
                else:
                    need_cfg = True

        ecmp_nexthop_changed = module.params['ecmp_nexthop_changed']
        if ecmp_nexthop_changed:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<ecmpNexthopChanged></ecmpNexthopChanged>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ecmpNexthopChanged>(.*)</ecmpNexthopChanged>.*', con_obj.xml)

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
                    msg='the value of default_local_pref %s is out of [0 - 4294967295].' % default_local_pref)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<defaultLocalPref></defaultLocalPref>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultLocalPref>(.*)</defaultLocalPref>.*', con_obj.xml)

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
                    msg='the value of default_med %s is out of [0 - 4294967295].' % default_med)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<defaultMed></defaultMed>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultMed>(.*)</defaultMed>.*', con_obj.xml)

                if re_find:
                    result["default_med"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != default_med:
                        need_cfg = True
                else:
                    need_cfg = True

        default_rt_import_enable = module.params['default_rt_import_enable']
        if default_rt_import_enable:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<defaultRtImportEnable></defaultRtImportEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<defaultRtImportEnable>(.*)</defaultRtImportEnable>.*', con_obj.xml)

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
                    msg='the len of router_id %s is out of [0 - 255].' % router_id)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<routerId></routerId>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routerId>(.*)</routerId>.*', con_obj.xml)

                if re_find:
                    result["router_id"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != router_id:
                        need_cfg = True
                else:
                    need_cfg = True

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<vrfRidAutoSel></vrfRidAutoSel>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<vrfRidAutoSel>(.*)</vrfRidAutoSel>.*', con_obj.xml)

                if re_find:
                    result["vrf_rid_auto_sel"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != vrf_rid_auto_sel:
                        need_cfg = True
                else:
                    need_cfg = True

        nexthop_third_party = module.params['nexthop_third_party']
        if nexthop_third_party:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<nexthopThirdParty></nexthopThirdParty>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<nexthopThirdParty>(.*)</nexthopThirdParty>.*', con_obj.xml)

                if re_find:
                    result["nexthop_third_party"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != nexthop_third_party:
                        need_cfg = True
                else:
                    need_cfg = True

        summary_automatic = module.params['summary_automatic']
        if summary_automatic:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<summaryAutomatic></summaryAutomatic>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<summaryAutomatic>(.*)</summaryAutomatic>.*', con_obj.xml)

                if re_find:
                    result["summary_automatic"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != summary_automatic:
                        need_cfg = True
                else:
                    need_cfg = True

        auto_frr_enable = module.params['auto_frr_enable']
        if auto_frr_enable:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<autoFrrEnable></autoFrrEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<autoFrrEnable>(.*)</autoFrrEnable>.*', con_obj.xml)

                if re_find:
                    result["auto_frr_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != auto_frr_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        load_balancing_as_path_ignore = module.params[
            'load_balancing_as_path_ignore']
        if load_balancing_as_path_ignore:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<loadBalancingAsPathIgnore></loadBalancingAsPathIgnore>" + \
                CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<loadBalancingAsPathIgnore>(.*)</loadBalancingAsPathIgnore>.*', con_obj.xml)

                if re_find:
                    result["load_balancing_as_path_ignore"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != load_balancing_as_path_ignore:
                        need_cfg = True
                else:
                    need_cfg = True

        rib_only_enable = module.params['rib_only_enable']
        if rib_only_enable:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<ribOnlyEnable></ribOnlyEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ribOnlyEnable>(.*)</ribOnlyEnable>.*', con_obj.xml)

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
                    msg='the len of rib_only_policy_name %s is out of [1 - 40].' % rib_only_policy_name)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<ribOnlyPolicyName></ribOnlyPolicyName>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ribOnlyPolicyName>(.*)</ribOnlyPolicyName>.*', con_obj.xml)

                if re_find:
                    result["rib_only_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != rib_only_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        active_route_advertise = module.params['active_route_advertise']
        if active_route_advertise:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<activeRouteAdvertise></activeRouteAdvertise>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<activeRouteAdvertise>(.*)</activeRouteAdvertise>.*', con_obj.xml)

                if re_find:
                    result["active_route_advertise"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != active_route_advertise:
                        need_cfg = True
                else:
                    need_cfg = True

        as_path_neglect = module.params['as_path_neglect']
        if as_path_neglect:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<asPathNeglect></asPathNeglect>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<asPathNeglect>(.*)</asPathNeglect>.*', con_obj.xml)

                if re_find:
                    result["as_path_neglect"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != as_path_neglect:
                        need_cfg = True
                else:
                    need_cfg = True

        med_none_as_maximum = module.params['med_none_as_maximum']
        if med_none_as_maximum:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<medNoneAsMaximum></medNoneAsMaximum>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<medNoneAsMaximum>(.*)</medNoneAsMaximum>.*', con_obj.xml)

                if re_find:
                    result["med_none_as_maximum"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != med_none_as_maximum:
                        need_cfg = True
                else:
                    need_cfg = True

        router_id_neglect = module.params['router_id_neglect']
        if router_id_neglect:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<routerIdNeglect></routerIdNeglect>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routerIdNeglect>(.*)</routerIdNeglect>.*', con_obj.xml)

                if re_find:
                    result["router_id_neglect"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != router_id_neglect:
                        need_cfg = True
                else:
                    need_cfg = True

        igp_metric_ignore = module.params['igp_metric_ignore']
        if igp_metric_ignore:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<igpMetricIgnore></igpMetricIgnore>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<igpMetricIgnore>(.*)</igpMetricIgnore>.*', con_obj.xml)

                if re_find:
                    result["igp_metric_ignore"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != igp_metric_ignore:
                        need_cfg = True
                else:
                    need_cfg = True

        always_compare_med = module.params['always_compare_med']
        if always_compare_med:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<alwaysCompareMed></alwaysCompareMed>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<alwaysCompareMed>(.*)</alwaysCompareMed>.*', con_obj.xml)

                if re_find:
                    result["always_compare_med"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != always_compare_med:
                        need_cfg = True
                else:
                    need_cfg = True

        determin_med = module.params['determin_med']
        if determin_med:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<determinMed></determinMed>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<determinMed>(.*)</determinMed>.*', con_obj.xml)

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
                    msg='the value of preference_external %s is out of [1 - 255].' % preference_external)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<preferenceExternal></preferenceExternal>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<preferenceExternal>(.*)</preferenceExternal>.*', con_obj.xml)

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
                    msg='the value of preference_internal %s is out of [1 - 255].' % preference_internal)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<preferenceInternal></preferenceInternal>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<preferenceInternal>(.*)</preferenceInternal>.*', con_obj.xml)

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
                    msg='the value of preference_local %s is out of [1 - 255].' % preference_local)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<preferenceLocal></preferenceLocal>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<preferenceLocal>(.*)</preferenceLocal>.*', con_obj.xml)

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
                    msg='the len of prefrence_policy_name %s is out of [1 - 40].' % prefrence_policy_name)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<prefrencePolicyName></prefrencePolicyName>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<prefrencePolicyName>(.*)</prefrencePolicyName>.*', con_obj.xml)

                if re_find:
                    result["prefrence_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != prefrence_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        reflect_between_client = module.params['reflect_between_client']
        if reflect_between_client:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<reflectBetweenClient></reflectBetweenClient>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectBetweenClient>(.*)</reflectBetweenClient>.*', con_obj.xml)

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
                    msg='the value of reflector_cluster_id %s is out of [1 - 4294967295].' % reflector_cluster_id)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<reflectorClusterId></reflectorClusterId>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectorClusterId>(.*)</reflectorClusterId>.*', con_obj.xml)

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
                    msg='the len of reflector_cluster_ipv4 %s is out of [0 - 255].' % reflector_cluster_ipv4)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<reflectorClusterIpv4></reflectorClusterIpv4>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectorClusterIpv4>(.*)</reflectorClusterIpv4>.*', con_obj.xml)

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
                    msg='the len of rr_filter_number %s is out of [1 - 51].' % rr_filter_number)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<rrFilterNumber></rrFilterNumber>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<rrFilterNumber>(.*)</rrFilterNumber>.*', con_obj.xml)

                if re_find:
                    result["rr_filter_number"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != rr_filter_number:
                        need_cfg = True
                else:
                    need_cfg = True

        policy_vpn_target = module.params['policy_vpn_target']
        if policy_vpn_target:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<policyVpnTarget></policyVpnTarget>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<policyVpnTarget>(.*)</policyVpnTarget>.*', con_obj.xml)

                if re_find:
                    result["policy_vpn_target"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != policy_vpn_target:
                        need_cfg = True
                else:
                    need_cfg = True

        next_hop_sel_depend_type = module.params['next_hop_sel_depend_type']
        if next_hop_sel_depend_type:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<nextHopSelDependType></nextHopSelDependType>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<nextHopSelDependType>(.*)</nextHopSelDependType>.*', con_obj.xml)

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
                    msg='the len of nhp_relay_route_policy_name %s is out of [1 - 40].' % nhp_relay_route_policy_name)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<nhpRelayRoutePolicyName></nhpRelayRoutePolicyName>" + \
                CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<nhpRelayRoutePolicyName>(.*)</nhpRelayRoutePolicyName>.*', con_obj.xml)

                if re_find:
                    result["nhp_relay_route_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != nhp_relay_route_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<ebgpIfSensitive></ebgpIfSensitive>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ebgpIfSensitive>(.*)</ebgpIfSensitive>.*', con_obj.xml)

                if re_find:
                    result["ebgp_if_sensitive"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != ebgp_if_sensitive:
                        need_cfg = True
                else:
                    need_cfg = True

        reflect_chg_path = module.params['reflect_chg_path']
        if reflect_chg_path:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<reflectChgPath></reflectChgPath>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<reflectChgPath>(.*)</reflectChgPath>.*', con_obj.xml)

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
                    msg='the value of add_path_sel_num %s is out of [2 - 64].' % add_path_sel_num)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<addPathSelNum></addPathSelNum>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<addPathSelNum>(.*)</addPathSelNum>.*', con_obj.xml)

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
                    msg='the value of route_sel_delay %s is out of [0 - 3600].' % route_sel_delay)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<routeSelDelay></routeSelDelay>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<routeSelDelay>(.*)</routeSelDelay>.*', con_obj.xml)

                if re_find:
                    result["route_sel_delay"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != route_sel_delay:
                        need_cfg = True
                else:
                    need_cfg = True

        allow_invalid_as = module.params['allow_invalid_as']
        if allow_invalid_as:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<allowInvalidAs></allowInvalidAs>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<allowInvalidAs>(.*)</allowInvalidAs>.*', con_obj.xml)

                if re_find:
                    result["allow_invalid_as"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != allow_invalid_as:
                        need_cfg = True
                else:
                    need_cfg = True

        policy_ext_comm_enable = module.params['policy_ext_comm_enable']
        if policy_ext_comm_enable:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<policyExtCommEnable></policyExtCommEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<policyExtCommEnable>(.*)</policyExtCommEnable>.*', con_obj.xml)

                if re_find:
                    result["policy_ext_comm_enable"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != policy_ext_comm_enable:
                        need_cfg = True
                else:
                    need_cfg = True

        supernet_uni_adv = module.params['supernet_uni_adv']
        if supernet_uni_adv:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<supernetUniAdv></supernetUniAdv>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<supernetUniAdv>(.*)</supernetUniAdv>.*', con_obj.xml)

                if re_find:
                    result["supernet_uni_adv"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != supernet_uni_adv:
                        need_cfg = True
                else:
                    need_cfg = True

        supernet_label_adv = module.params['supernet_label_adv']
        if supernet_label_adv:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<supernetLabelAdv></supernetLabelAdv>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<supernetLabelAdv>(.*)</supernetLabelAdv>.*', con_obj.xml)

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
                    msg='the len of ingress_lsp_policy_name %s is out of [1 - 40].' % ingress_lsp_policy_name)

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<ingressLspPolicyName></ingressLspPolicyName>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<ingressLspPolicyName>(.*)</ingressLspPolicyName>.*', con_obj.xml)

                if re_find:
                    result["ingress_lsp_policy_name"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != ingress_lsp_policy_name:
                        need_cfg = True
                else:
                    need_cfg = True

        originator_prior = module.params['originator_prior']
        if originator_prior:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<originatorPrior></originatorPrior>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<originatorPrior>(.*)</originatorPrior>.*', con_obj.xml)

                if re_find:
                    result["originator_prior"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != originator_prior:
                        need_cfg = True
                else:
                    need_cfg = True

        lowest_priority = module.params['lowest_priority']
        if lowest_priority:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<lowestPriority></lowestPriority>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<lowestPriority>(.*)</lowestPriority>.*', con_obj.xml)

                if re_find:
                    result["lowest_priority"] = re_find
                    result["vrf_name"] = vrf_name
                    if re_find[0] != lowest_priority:
                        need_cfg = True
                else:
                    need_cfg = True

        relay_delay_enable = module.params['relay_delay_enable']
        if relay_delay_enable:

            conf_str = CE_GET_BGP_ADDRESS_FAMILY_HEADER % vrf_name + \
                "<relayDelayEnable></relayDelayEnable>" + CE_GET_BGP_ADDRESS_FAMILY_TAIL
            con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

            if "<data/>" in con_obj.xml:
                need_cfg = True
            else:
                re_find = re.findall(
                    r'.*<relayDelayEnable>(.*)</relayDelayEnable>.*', con_obj.xml)

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
        """check_bgp_import_network_route"""

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
                    msg='please input import_protocol and import_process_id value at the same time.')
            else:
                if int(import_process_id) < 0:
                    module.fail_json(
                        msg='the value of import_process_id %s is out of [0 - 4294967295].' % import_process_id)

        if import_process_id:
            if not import_protocol:
                module.fail_json(
                    msg='please input import_protocol and import_process_id value at the same time.')

        network_address = module.params['network_address']
        mask_len = module.params['mask_len']

        if network_address:
            if not mask_len:
                module.fail_json(
                    msg='please input network_address and mask_len value at the same time.')
        if mask_len:
            if not network_address:
                module.fail_json(
                    msg='please input network_address and mask_len value at the same time.')

        conf_str = CE_GET_BGP_IMPORT_AND_NETWORK_ROUTE % (vrf_name, af_type)
        con_obj = self.netconf_get_config(module=module, conf_str=conf_str)

        if import_protocol:

            if import_protocol == "direct" or import_protocol == "static":
                import_process_id = "0"
            else:
                if not import_process_id or import_process_id == "0":
                    module.fail_json(
                        msg='please input import_process_id not 0 when import_protocol is [ospf, isis, rip, ospfv3, ripng].')

            bgp_import_route_new = (import_protocol, import_process_id)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    import_need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<importProtocol>(.*)</importProtocol>.*\s.*<importProcessId>(.*)</importProcessId>.*', con_obj.xml)

                    if re_find:
                        result["bgp_import_route"] = re_find
                        result["vrf_name"] = vrf_name
                        if bgp_import_route_new not in re_find:
                            import_need_cfg = True
                    else:
                        import_need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<importProtocol>(.*)</importProtocol>.*\s.*<importProcessId>(.*)</importProcessId>.*', con_obj.xml)

                    if re_find:
                        result["bgp_import_route"] = re_find
                        result["vrf_name"] = vrf_name
                        if bgp_import_route_new in re_find:
                            import_need_cfg = True

        if network_address and mask_len:

            bgp_network_route_new = (network_address, mask_len)

            if self.check_ip_addr(ipaddr=network_address) == False:
                module.fail_json(
                    msg='the network_address %s is invalid.' % network_address)

            if len(mask_len) > 128:
                module.fail_json(
                    msg='the len of mask_len %s is out of [0 - 128].' % mask_len)

            if state == "present":
                if "<data/>" in con_obj.xml:
                    network_need_cfg = True
                else:
                    re_find = re.findall(
                        r'.*<networkAddress>(.*)</networkAddress>.*\s.*<maskLen>(.*)</maskLen>.*', con_obj.xml)

                    if re_find:
                        result["bgp_network_route"] = re_find
                        result["vrf_name"] = vrf_name
                        if bgp_network_route_new not in re_find:
                            network_need_cfg = True
                    else:
                        network_need_cfg = True
            else:
                if "<data/>" in con_obj.xml:
                    pass
                else:
                    re_find = re.findall(
                        r'.*<networkAddress>(.*)</networkAddress>.*\s.*<maskLen>(.*)</maskLen>.*', con_obj.xml)

                    if re_find:
                        result["bgp_network_route"] = re_find
                        result["vrf_name"] = vrf_name
                        if bgp_network_route_new in re_find:
                            network_need_cfg = True

        result["import_need_cfg"] = import_need_cfg
        result["network_need_cfg"] = network_need_cfg
        return result

    def merge_bgp_af(self, **kwargs):
        """merge_bgp_af"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']

        conf_str = CE_MERGE_BGP_ADDRESS_FAMILY_HEADER % (
            vrf_name, af_type) + CE_MERGE_BGP_ADDRESS_FAMILY_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp address family failed.')

        return SUCCESS

    def create_bgp_af(self, **kwargs):
        """create_bgp_af"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']

        conf_str = CE_CREATE_BGP_ADDRESS_FAMILY_HEADER % (
            vrf_name, af_type) + CE_CREATE_BGP_ADDRESS_FAMILY_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create bgp address family failed.')

        return SUCCESS

    def delete_bgp_af(self, **kwargs):
        """delete_bgp_af"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']

        conf_str = CE_DELETE_BGP_ADDRESS_FAMILY_HEADER % (
            vrf_name, af_type) + CE_DELETE_BGP_ADDRESS_FAMILY_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete bgp address family failed.')

        return SUCCESS

    def merge_bgp_af_other(self, **kwargs):
        """merge_bgp_af_other"""

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']

        conf_str = CE_MERGE_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type)

        max_load_ibgp_num = module.params['max_load_ibgp_num']
        if max_load_ibgp_num:
            conf_str += "<maxLoadIbgpNum>%s</maxLoadIbgpNum>" % max_load_ibgp_num

        ibgp_ecmp_nexthop_changed = module.params['ibgp_ecmp_nexthop_changed']
        if ibgp_ecmp_nexthop_changed:
            conf_str += "<ibgpEcmpNexthopChanged>%s</ibgpEcmpNexthopChanged>" % ibgp_ecmp_nexthop_changed

        max_load_ebgp_num = module.params['max_load_ebgp_num']
        if max_load_ebgp_num:
            conf_str += "<maxLoadEbgpNum>%s</maxLoadEbgpNum>" % max_load_ebgp_num

        ebgp_ecmp_nexthop_changed = module.params['ebgp_ecmp_nexthop_changed']
        if ebgp_ecmp_nexthop_changed:
            conf_str += "<ebgpEcmpNexthopChanged>%s</ebgpEcmpNexthopChanged>" % ebgp_ecmp_nexthop_changed

        maximum_load_balance = module.params['maximum_load_balance']
        if maximum_load_balance:
            conf_str += "<maximumLoadBalance>%s</maximumLoadBalance>" % maximum_load_balance

        ecmp_nexthop_changed = module.params['ecmp_nexthop_changed']
        if ecmp_nexthop_changed:
            conf_str += "<ecmpNexthopChanged>%s</ecmpNexthopChanged>" % ecmp_nexthop_changed

        default_local_pref = module.params['default_local_pref']
        if default_local_pref:
            conf_str += "<defaultLocalPref>%s</defaultLocalPref>" % default_local_pref

        default_med = module.params['default_med']
        if default_med:
            conf_str += "<defaultMed>%s</defaultMed>" % default_med

        default_rt_import_enable = module.params['default_rt_import_enable']
        if default_rt_import_enable:
            conf_str += "<defaultRtImportEnable>%s</defaultRtImportEnable>" % default_rt_import_enable

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId>%s</routerId>" % router_id

        vrf_rid_auto_sel = module.params['vrf_rid_auto_sel']
        if vrf_rid_auto_sel:
            conf_str += "<vrfRidAutoSel>%s</vrfRidAutoSel>" % vrf_rid_auto_sel

        nexthop_third_party = module.params['nexthop_third_party']
        if nexthop_third_party:
            conf_str += "<nexthopThirdParty>%s</nexthopThirdParty>" % nexthop_third_party

        summary_automatic = module.params['summary_automatic']
        if summary_automatic:
            conf_str += "<summaryAutomatic>%s</summaryAutomatic>" % summary_automatic

        auto_frr_enable = module.params['auto_frr_enable']
        if auto_frr_enable:
            conf_str += "<autoFrrEnable>%s</autoFrrEnable>" % auto_frr_enable

        load_balancing_as_path_ignore = module.params[
            'load_balancing_as_path_ignore']
        if load_balancing_as_path_ignore:
            conf_str += "<loadBalancingAsPathIgnore>%s</loadBalancingAsPathIgnore>" % load_balancing_as_path_ignore

        rib_only_enable = module.params['rib_only_enable']
        if rib_only_enable:
            conf_str += "<ribOnlyEnable>%s</ribOnlyEnable>" % rib_only_enable

        rib_only_policy_name = module.params['rib_only_policy_name']
        if rib_only_policy_name:
            conf_str += "<ribOnlyPolicyName>%s</ribOnlyPolicyName>" % rib_only_policy_name

        active_route_advertise = module.params['active_route_advertise']
        if active_route_advertise:
            conf_str += "<activeRouteAdvertise>%s</activeRouteAdvertise>" % active_route_advertise

        as_path_neglect = module.params['as_path_neglect']
        if as_path_neglect:
            conf_str += "<asPathNeglect>%s</asPathNeglect>" % as_path_neglect

        med_none_as_maximum = module.params['med_none_as_maximum']
        if med_none_as_maximum:
            conf_str += "<medNoneAsMaximum>%s</medNoneAsMaximum>" % med_none_as_maximum

        router_id_neglect = module.params['router_id_neglect']
        if router_id_neglect:
            conf_str += "<routerIdNeglect>%s</routerIdNeglect>" % router_id_neglect

        igp_metric_ignore = module.params['igp_metric_ignore']
        if igp_metric_ignore:
            conf_str += "<igpMetricIgnore>%s</igpMetricIgnore>" % igp_metric_ignore

        always_compare_med = module.params['always_compare_med']
        if always_compare_med:
            conf_str += "<alwaysCompareMed>%s</alwaysCompareMed>" % always_compare_med

        determin_med = module.params['determin_med']
        if determin_med:
            conf_str += "<determinMed>%s</determinMed>" % determin_med

        preference_external = module.params['preference_external']
        if preference_external:
            conf_str += "<preferenceExternal>%s</preferenceExternal>" % preference_external

        preference_internal = module.params['preference_internal']
        if preference_internal:
            conf_str += "<preferenceInternal>%s</preferenceInternal>" % preference_internal

        preference_local = module.params['preference_local']
        if preference_local:
            conf_str += "<preferenceLocal>%s</preferenceLocal>" % preference_local

        prefrence_policy_name = module.params['prefrence_policy_name']
        if prefrence_policy_name:
            conf_str += "<prefrencePolicyName>%s</prefrencePolicyName>" % prefrence_policy_name

        reflect_between_client = module.params['reflect_between_client']
        if reflect_between_client:
            conf_str += "<reflectBetweenClient>%s</reflectBetweenClient>" % reflect_between_client

        reflector_cluster_id = module.params['reflector_cluster_id']
        if reflector_cluster_id:
            conf_str += "<reflectorClusterId>%s</reflectorClusterId>" % reflector_cluster_id

        reflector_cluster_ipv4 = module.params['reflector_cluster_ipv4']
        if reflector_cluster_ipv4:
            conf_str += "<reflectorClusterIpv4>%s</reflectorClusterIpv4>" % reflector_cluster_ipv4

        rr_filter_number = module.params['rr_filter_number']
        if rr_filter_number:
            conf_str += "<rrFilterNumber>%s</rrFilterNumber>" % rr_filter_number

        policy_vpn_target = module.params['policy_vpn_target']
        if policy_vpn_target:
            conf_str += "<policyVpnTarget>%s</policyVpnTarget>" % policy_vpn_target

        next_hop_sel_depend_type = module.params['next_hop_sel_depend_type']
        if next_hop_sel_depend_type:
            conf_str += "<nextHopSelDependType>%s</nextHopSelDependType>" % next_hop_sel_depend_type

        nhp_relay_route_policy_name = module.params[
            'nhp_relay_route_policy_name']
        if nhp_relay_route_policy_name:
            conf_str += "<nhpRelayRoutePolicyName>%s</nhpRelayRoutePolicyName>" % nhp_relay_route_policy_name

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive:
            conf_str += "<ebgpIfSensitive>%s</ebgpIfSensitive>" % ebgp_if_sensitive

        reflect_chg_path = module.params['reflect_chg_path']
        if reflect_chg_path:
            conf_str += "<reflectChgPath>%s</reflectChgPath>" % reflect_chg_path

        add_path_sel_num = module.params['add_path_sel_num']
        if add_path_sel_num:
            conf_str += "<addPathSelNum>%s</addPathSelNum>" % add_path_sel_num

        route_sel_delay = module.params['route_sel_delay']
        if route_sel_delay:
            conf_str += "<routeSelDelay>%s</routeSelDelay>" % route_sel_delay

        allow_invalid_as = module.params['allow_invalid_as']
        if allow_invalid_as:
            conf_str += "<allowInvalidAs>%s</allowInvalidAs>" % allow_invalid_as

        policy_ext_comm_enable = module.params['policy_ext_comm_enable']
        if policy_ext_comm_enable:
            conf_str += "<policyExtCommEnable>%s</policyExtCommEnable>" % policy_ext_comm_enable

        supernet_uni_adv = module.params['supernet_uni_adv']
        if supernet_uni_adv:
            conf_str += "<supernetUniAdv>%s</supernetUniAdv>" % supernet_uni_adv

        supernet_label_adv = module.params['supernet_label_adv']
        if supernet_label_adv:
            conf_str += "<supernetLabelAdv>%s</supernetLabelAdv>" % supernet_label_adv

        ingress_lsp_policy_name = module.params['ingress_lsp_policy_name']
        if ingress_lsp_policy_name:
            conf_str += "<ingressLspPolicyName>%s</ingressLspPolicyName>" % ingress_lsp_policy_name

        originator_prior = module.params['originator_prior']
        if originator_prior:
            conf_str += "<originatorPrior>%s</originatorPrior>" % originator_prior

        lowest_priority = module.params['lowest_priority']
        if lowest_priority:
            conf_str += "<lowestPriority>%s</lowestPriority>" % lowest_priority

        relay_delay_enable = module.params['relay_delay_enable']
        if relay_delay_enable:
            conf_str += "<relayDelayEnable>%s</relayDelayEnable>" % relay_delay_enable

        conf_str += CE_MERGE_BGP_ADDRESS_FAMILY_TAIL
        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(
                msg='merge bgp address family other agrus failed.')

        return SUCCESS

    def delete_bgp_af_other(self, **kwargs):
        """delete_bgp_af_other"""

        module = kwargs["module"]
        vrf_name = module.params['vrf_name']
        af_type = module.params['af_type']

        conf_str = CE_MERGE_BGP_ADDRESS_FAMILY_HEADER % (vrf_name, af_type)

        router_id = module.params['router_id']
        if router_id:
            conf_str += "<routerId></routerId>"

        determin_med = module.params['determin_med']
        if determin_med:
            conf_str += "<determinMed></determinMed>"

        ebgp_if_sensitive = module.params['ebgp_if_sensitive']
        if ebgp_if_sensitive:
            conf_str += "<ebgpIfSensitive></ebgpIfSensitive>"

        relay_delay_enable = module.params['relay_delay_enable']
        if relay_delay_enable:
            conf_str += "<relayDelayEnable></relayDelayEnable>"

        conf_str += CE_MERGE_BGP_ADDRESS_FAMILY_TAIL
        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(
                msg='merge bgp address family other agrus failed.')

        return SUCCESS

    def merge_bgp_import_route(self, **kwargs):
        """merge_bgp_import_route"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        import_protocol = module.params['import_protocol']
        import_process_id = module.params['import_process_id']

        if import_protocol == "direct" or import_protocol == "static":
            import_process_id = "0"

        conf_str = CE_MERGE_BGP_IMPORT_ROUTE_HEADER % (
            vrf_name, af_type, import_protocol, import_process_id) + CE_MERGE_BGP_ADDRESS_FAMILY_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp import route failed.')

        return SUCCESS

    def create_bgp_import_route(self, **kwargs):
        """create_bgp_import_route"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        import_protocol = module.params['import_protocol']
        import_process_id = module.params['import_process_id']

        if import_protocol == "direct" or import_protocol == "static":
            import_process_id = "0"

        conf_str = CE_CREATE_BGP_IMPORT_ROUTE % (
            vrf_name, af_type, import_protocol, import_process_id)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create bgp import route failed.')

        return SUCCESS

    def delete_bgp_import_route(self, **kwargs):
        """delete_bgp_import_route"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        import_protocol = module.params['import_protocol']
        import_process_id = module.params['import_process_id']

        if import_protocol == "direct" or import_protocol == "static":
            import_process_id = "0"

        conf_str = CE_DELETE_BGP_IMPORT_ROUTE % (
            vrf_name, af_type, import_protocol, import_process_id)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete bgp import route failed.')

        return SUCCESS

    def merge_bgp_network_route(self, **kwargs):
        """merge_bgp_network_route"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        network_address = module.params['network_address']
        mask_len = module.params['mask_len']

        conf_str = CE_MERGE_BGP_NETWORK_ROUTE_HEADER % (
            vrf_name, af_type, network_address, mask_len) + CE_MERGE_BGP_NETWORK_ROUTE_TAIL

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='merge bgp network route failed.')

        return SUCCESS

    def create_bgp_network_route(self, **kwargs):
        """create_bgp_network_route"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        network_address = module.params['network_address']
        mask_len = module.params['mask_len']

        conf_str = CE_CREATE_BGP_NETWORK_ROUTE % (
            vrf_name, af_type, network_address, mask_len)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='create bgp network route failed.')

        return SUCCESS

    def delete_bgp_network_route(self, **kwargs):
        """delete_bgp_network_route"""

        module = kwargs["module"]

        vrf_name = module.params['vrf_name']

        af_type = module.params['af_type']
        network_address = module.params['network_address']
        mask_len = module.params['mask_len']

        conf_str = CE_DELETE_BGP_NETWORK_ROUTE % (
            vrf_name, af_type, network_address, mask_len)

        con_obj = self.netconf_set_config(module=module, conf_str=conf_str)

        if "<ok/>" not in con_obj.xml:
            module.fail_json(msg='delete bgp network route failed.')

        return SUCCESS


def main():
    """ main """

    start_time = datetime.datetime.now()

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        host=dict(required=True),
        username=dict(required=True),
        password=dict(required=True),
        vrf_name=dict(type='str', default='_public_'),
        af_type=dict(choices=['ipv4uni', 'ipv4multi', 'ipv4vpn',
                              'ipv6uni', 'ipv6vpn', 'evpn'], required=True),
        max_load_ibgp_num=dict(type='str'),
        ibgp_ecmp_nexthop_changed=dict(choices=['true', 'false']),
        max_load_ebgp_num=dict(type='str'),
        ebgp_ecmp_nexthop_changed=dict(choices=['true', 'false']),
        maximum_load_balance=dict(type='str'),
        ecmp_nexthop_changed=dict(choices=['true', 'false']),
        default_local_pref=dict(type='str'),
        default_med=dict(type='str'),
        default_rt_import_enable=dict(choices=['true', 'false']),
        router_id=dict(type='str'),
        vrf_rid_auto_sel=dict(choices=['true', 'false']),
        nexthop_third_party=dict(choices=['true', 'false']),
        summary_automatic=dict(choices=['true', 'false']),
        auto_frr_enable=dict(choices=['true', 'false']),
        load_balancing_as_path_ignore=dict(choices=['true', 'false']),
        rib_only_enable=dict(choices=['true', 'false']),
        rib_only_policy_name=dict(type='str'),
        active_route_advertise=dict(choices=['true', 'false']),
        as_path_neglect=dict(choices=['true', 'false']),
        med_none_as_maximum=dict(choices=['true', 'false']),
        router_id_neglect=dict(choices=['true', 'false']),
        igp_metric_ignore=dict(choices=['true', 'false']),
        always_compare_med=dict(choices=['true', 'false']),
        determin_med=dict(choices=['true', 'false']),
        preference_external=dict(type='str'),
        preference_internal=dict(type='str'),
        preference_local=dict(type='str'),
        prefrence_policy_name=dict(type='str'),
        reflect_between_client=dict(choices=['true', 'false']),
        reflector_cluster_id=dict(type='str'),
        reflector_cluster_ipv4=dict(type='str'),
        rr_filter_number=dict(type='str'),
        policy_vpn_target=dict(choices=['true', 'false']),
        next_hop_sel_depend_type=dict(
            choices=['default', 'dependTunnel', 'dependIp']),
        nhp_relay_route_policy_name=dict(type='str'),
        ebgp_if_sensitive=dict(choices=['true', 'false']),
        reflect_chg_path=dict(choices=['true', 'false']),
        add_path_sel_num=dict(type='str'),
        route_sel_delay=dict(type='str'),
        allow_invalid_as=dict(choices=['true', 'false']),
        policy_ext_comm_enable=dict(choices=['true', 'false']),
        supernet_uni_adv=dict(choices=['true', 'false']),
        supernet_label_adv=dict(choices=['true', 'false']),
        ingress_lsp_policy_name=dict(type='str'),
        originator_prior=dict(choices=['true', 'false']),
        lowest_priority=dict(choices=['true', 'false']),
        relay_delay_enable=dict(choices=['true', 'false']),
        import_protocol=dict(
            choices=['direct', 'ospf', 'isis', 'static', 'rip', 'ospfv3', 'ripng']),
        import_process_id=dict(type='str'),
        network_address=dict(type='str'),
        mask_len=dict(type='str'))

    if not HAS_NCCLIENT:
        raise Exception("the ncclient library is required")

    module = NetworkModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    state = module.params['state']
    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
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

    ce_bgp_af_obj = ce_bgp_af(
        host=host, port=port, username=username, password=password)

    if not ce_bgp_af_obj:
        module.fail_json(msg='init module failed.')

    bgp_af_rst = ce_bgp_af_obj.check_bgp_af_args(module=module)
    bgp_af_other_rst = ce_bgp_af_obj.check_bgp_af_other_args(module=module)
    bgp_af_other_can_del_rst = ce_bgp_af_obj.check_bgp_af_other_can_del(
        module=module)
    bgp_import_network_route_rst = ce_bgp_af_obj.check_bgp_import_network_route(
        module=module)

    args = dict(state=state,
                vrf_name=vrf_name,
                af_type=af_type,
                max_load_ibgp_num=max_load_ibgp_num,
                ibgp_ecmp_nexthop_changed=ibgp_ecmp_nexthop_changed,
                max_load_ebgp_num=max_load_ebgp_num,
                ebgp_ecmp_nexthop_changed=ebgp_ecmp_nexthop_changed,
                maximum_load_balance=maximum_load_balance,
                ecmp_nexthop_changed=ecmp_nexthop_changed,
                default_local_pref=default_local_pref,
                default_med=default_med,
                default_rt_import_enable=default_rt_import_enable,
                router_id=router_id,
                vrf_rid_auto_sel=vrf_rid_auto_sel,
                nexthop_third_party=nexthop_third_party,
                summary_automatic=summary_automatic,
                auto_frr_enable=auto_frr_enable,
                load_balancing_as_path_ignore=load_balancing_as_path_ignore,
                rib_only_enable=rib_only_enable,
                rib_only_policy_name=rib_only_policy_name,
                active_route_advertise=active_route_advertise,
                as_path_neglect=as_path_neglect,
                med_none_as_maximum=med_none_as_maximum,
                router_id_neglect=router_id_neglect,
                igp_metric_ignore=igp_metric_ignore,
                always_compare_med=always_compare_med,
                determin_med=determin_med,
                preference_external=preference_external,
                preference_internal=preference_internal,
                preference_local=preference_local,
                prefrence_policy_name=prefrence_policy_name,
                reflect_between_client=reflect_between_client,
                reflector_cluster_id=reflector_cluster_id,
                reflector_cluster_ipv4=reflector_cluster_ipv4,
                rr_filter_number=rr_filter_number,
                policy_vpn_target=policy_vpn_target,
                next_hop_sel_depend_type=next_hop_sel_depend_type,
                nhp_relay_route_policy_name=nhp_relay_route_policy_name,
                ebgp_if_sensitive=ebgp_if_sensitive,
                reflect_chg_path=reflect_chg_path,
                add_path_sel_num=add_path_sel_num,
                route_sel_delay=route_sel_delay,
                allow_invalid_as=allow_invalid_as,
                policy_ext_comm_enable=policy_ext_comm_enable,
                supernet_uni_adv=supernet_uni_adv,
                supernet_label_adv=supernet_label_adv,
                ingress_lsp_policy_name=ingress_lsp_policy_name,
                originator_prior=originator_prior,
                lowest_priority=lowest_priority,
                relay_delay_enable=relay_delay_enable,
                import_protocol=import_protocol,
                import_process_id=import_process_id,
                network_address=network_address,
                mask_len=mask_len)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = dict()
    end_state = dict()

    # state exist bgp address family config
    exist_tmp = dict(
        (k, v) for k, v in bgp_af_rst.iteritems() if k is not "need_cfg")
    if exist_tmp:
        existing["bgp af"] = exist_tmp
    # state exist bgp address family other config
    exist_tmp = dict(
        (k, v) for k, v in bgp_af_other_rst.iteritems() if k is not "need_cfg")
    if exist_tmp:
        existing["bgp af other"] = exist_tmp
    # state exist bgp import route config
    exist_tmp = dict(
        (k, v) for k, v in bgp_import_network_route_rst.iteritems() if k is not "import_need_cfg" and k is not "network_need_cfg")
    if exist_tmp:
        existing["bgp import & network route"] = exist_tmp

    if state == "present":
        if bgp_af_rst["need_cfg"] and bgp_import_network_route_rst["import_need_cfg"] and bgp_import_network_route_rst["network_need_cfg"]:
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
            con_obj = ce_bgp_af_obj.netconf_set_config(
                module=module, conf_str=conf_str)

            if "<ok/>" not in con_obj.xml:
                module.fail_json(
                    msg='present bgp af_type import and network route failed.')

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
            con_obj = ce_bgp_af_obj.netconf_set_config(
                module=module, conf_str=conf_str)

            if "<ok/>" not in con_obj.xml:
                module.fail_json(
                    msg='present bgp import and network route failed.')

        else:
            if bgp_af_rst["need_cfg"]:
                if "af_type" in bgp_af_rst.keys():
                    ce_bgp_af_obj.merge_bgp_af(module=module)
                    changed = True
                else:
                    ce_bgp_af_obj.create_bgp_af(module=module)
                    changed = True

            if bgp_af_other_rst["need_cfg"]:
                ce_bgp_af_obj.merge_bgp_af_other(module=module)
                changed = True

            if bgp_import_network_route_rst["import_need_cfg"]:
                if "bgp_import_route" in bgp_import_network_route_rst.keys():
                    ce_bgp_af_obj.merge_bgp_import_route(module=module)
                    changed = True
                else:
                    ce_bgp_af_obj.create_bgp_import_route(module=module)
                    changed = True

            if bgp_import_network_route_rst["network_need_cfg"]:
                if "bgp_network_route" in bgp_import_network_route_rst.keys():
                    ce_bgp_af_obj.merge_bgp_network_route(module=module)
                    changed = True
                else:
                    ce_bgp_af_obj.create_bgp_network_route(module=module)
                    changed = True

    else:
        if bgp_import_network_route_rst["import_need_cfg"] and bgp_import_network_route_rst["network_need_cfg"]:
            changed = True
            conf_str = CE_BGP_IMPORT_NETWORK_ROUTE_HEADER % (vrf_name, af_type)
            conf_str += CE_BGP_DELETE_IMPORT_UNIT % (
                import_protocol, import_process_id)
            conf_str += CE_BGP_DELETE_NETWORK_UNIT % (
                network_address, mask_len)

            conf_str += CE_BGP_IMPORT_NETWORK_ROUTE_TAIL
            con_obj = ce_bgp_af_obj.netconf_set_config(
                module=module, conf_str=conf_str)

            if "<ok/>" not in con_obj.xml:
                module.fail_json(
                    msg='absent bgp import and network route failed.')

        else:
            if bgp_import_network_route_rst["import_need_cfg"]:
                ce_bgp_af_obj.delete_bgp_import_route(module=module)
                changed = True

            if bgp_import_network_route_rst["network_need_cfg"]:
                ce_bgp_af_obj.delete_bgp_network_route(module=module)
                changed = True

        if bgp_af_other_can_del_rst["need_cfg"]:
            ce_bgp_af_obj.delete_bgp_af_other(module=module)
            changed = True

        if bgp_af_rst["need_cfg"] and not bgp_af_other_can_del_rst["need_cfg"]:
            ce_bgp_af_obj.delete_bgp_af(module=module)
            changed = True

        if bgp_af_other_rst["need_cfg"]:
            pass

    # state end bgp address family config
    bgp_af_rst = ce_bgp_af_obj.check_bgp_af_args(module=module)
    end_tmp = dict(
        (k, v) for k, v in bgp_af_rst.iteritems() if k is not "need_cfg")
    if end_tmp:
        end_state["bgp af"] = end_tmp
    # state end bgp address family other config
    bgp_af_other_rst = ce_bgp_af_obj.check_bgp_af_other_args(module=module)
    end_tmp = dict(
        (k, v) for k, v in bgp_af_other_rst.iteritems() if k is not "need_cfg")
    if end_tmp:
        end_state["bgp af other"] = end_tmp
    # state end bgp import route config
    bgp_import_network_route_rst = ce_bgp_af_obj.check_bgp_import_network_route(
        module=module)
    end_tmp = dict(
        (k, v) for k, v in bgp_import_network_route_rst.iteritems() if k is not "import_need_cfg" and k is not "network_need_cfg")
    if end_tmp:
        end_state["bgp import & network route"] = end_tmp

    results = dict()
    results['proposed'] = proposed
    results['existing'] = existing
    results['changed'] = changed
    results['end_state'] = end_state

    end_time = datetime.datetime.now()
    results['execute_time'] = str(end_time - start_time)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
