#!/usr/bin/python
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_multicast_pim_view
version_added: "2.10"
short_description: Manages multicast pim configuration on HUAWEI CloudEngine switches.
description:
  - Manages the multicast pim on HUAWEI CloudEngine switches.
author: xuxiawei0512 (@CloudEngine-Ansible)
notes:
  - If no vrf is supplied, vrf is set to default.
    If I(state=absent), the route will be removed, regardless of the
    non-required parameters.
options:
  aftype:
    description:
      - Destination ip address family type of static route.
    type: str
    choices: ['v4','v6']
  vrf:
    description:
      - VPN instance of destination ip address.
    type: str
  addr:
    description:
      - Indicates the static RP address.
    type: str
  local_addr:
    description:
      - Specify Anycast RP local address.
    type: str
  ifname:
    description:
      - Candidate BSR interface name. PIM-SM must be enabled
        on the corresponding interface before the candidate BSR can take effect (range 1-63).
    type: str
  pri:
    description:
      - The priority of this global domain candidate BSR,priority is from 0 to 255.
    type: int
    default: 0
  hashlen:
    description:
      - The hash mask length of this global domain candidate BSR (range 0-32).
    type: int
    default: 30
  features:
    description:
      - Used to distinguish neconf xml functionality.
    type: str
    choices: ['c_bsr','auto_rp','c_rp','pim','bid','static_rp','anycast_rp']
  method:
    description:
      - Used to distinguish cmd functionality.
    type: str
    choices: ['lifetime','hello_interval','hello_holdtime','hello_option',
              'join_prune','join_prune_holdtime','hello_over_interval','hello_lan_delay','assert']
  bid:
    description:
      - Indicates whether the RP has bidirectional PIM capability.Or static RP is only bidirectional PIM service.
    type: bool
  frag:
    description:
      - Enable BSR packet fragmentation. By default,BSR packet fragmentation is disabled by default.
    type: bool
  pre:
    description:
      - Static RP first.
    type: bool
  trigcache:
    description:
      - Configure the real-time triggered Join/prune
        packet encapsulation function.By default, the real-time triggered
        Join/prune packet encapsulation function is enabled.
    type: bool
  bid_enable:
    description:
      - Is bidirectional PIM enabled.
    type: bool
  name:
    description:
      - acl name (range 1-32) or basic acl number (range 2000-2999) or advance number (range 3000-3999).
    type: str
  src_name:
    description:
      - acl name (range 1-32) or basic acl number (range 2000-2999) or advance number (range 2000-3999).
    type: str
  interval:
    description:
      - The BSR waits to receive the timeout period for the C-RP to send
        Advertisement announcement messages. Unit is second (range 1-65535).
    type: int
  adinterval:
    description:
      - The C-RP waits to receive the timeout period for the C-RP to send
        Advertisement announcement messages. Unit is second (range 1-65535).
    type: int
    default: 60
  state:
    description:
      - Specify desired state of the resource.
    type: str
    choices: ['present','absent']
    default: present
'''

EXAMPLES = '''
  - name: new pim anycast_rp local_addr 2.2.2.2
    ce_multicast_pim_view:
      features: 'anycast_rp'
      aftype: v4
      addr: 1.1.1.1
      local_addr: 2.2.2.2

  - name: modify pim anycast_rp local_addr 126.255.255.254
    ce_multicast_pim_view:
      features: 'anycast_rp'
      aftype: v4
      addr: 1.1.1.1
      local_addr: 126.255.255.254

  - name: delete pim anycast_rp local_addr
    ce_multicast_pim_view:
      features: 'anycast_rp'
      aftype: v4
      addr: 1.1.1.1
      state: absent

  - name: delete pim anycast_rp
    ce_multicast_pim_view:
      features: 'anycast_rp'
      aftype: v4
      addr: 126.255.255.255
      state: absent

  - name: config c_rp bid enable
    ce_multicast_pim_view:
      features: 'c_rp'
      aftype: v4
      ifname: 10GE2/0/2
      bid: true
      state: present

  - name: config c_rp bid disable
    ce_multicast_pim_view:
      features: 'c_rp'
      aftype: v4
      ifname: 10GE2/0/2
      bid: false
      state: present

  - name: config c_rp all
    ce_multicast_pim_view:
      features: 'c_rp'
      aftype: v4
      ifname: 10GE2/0/2
      bid: true
      pri: 5
      interval: 6
      adinterval: 7
      name: 2001
      state: present
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"addressFamily": "ipv4unicast","cRpAdvInterval": 7,"cRpBidir": "Bidir",
    "cRpGrpPlyName": "2001","cRpHoldTime": 6,"cRpIfName": "10GE2/0/2","cRpPriority": 5,
    "features": "c_rp","state": "present","vrfName": "_public_"}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: {}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  {"cRpAdvInterval": "7","cRpBidir": "Bidir","cRpGrpPlyName": "2001","cRpHoldTime": "6",
                "cRpIfName": "10GE2/0/2","cRpPriority": "5","vrfName": "_public_"}
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: [
        "c-rp 10GE2/0/2 ",
        " group-policy 2001 ",
        " priority 5 ",
        " holdtime 6 ",
        " advertisement-interval 7 ",
        " bidir"
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import sys
import socket
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config

# xml2
CE_NC_GET_MULTICAST_PIM_AUTO_RP = """
<filter type="subtree">
    <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bsrafspro>
          <bsrAfsAutoRpCfgs>
            <bsrAfsAutoRpCfg>
              <vrfName>%s</vrfName>
              <addressFamily>%s</addressFamily>
            </bsrAfsAutoRpCfg>
          </bsrAfsAutoRpCfgs>
        </bsrafspro>
    </pim>
</filter>
"""
CE_NC_MERGE_MULTICAST_PIM_AUTO_RP = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <bsrafspro>
      <bsrAfsAutoRpCfgs>
        <bsrAfsAutoRpCfg operation="merge">
          <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>
        </bsrAfsAutoRpCfg>
      </bsrAfsAutoRpCfgs>
    </bsrafspro>
</pim>
"""
CE_NC_DELETE_MULTICAST_PIM_AUTO_RP = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <bsrafspro>
      <bsrAfsAutoRpCfgs>
        <bsrAfsAutoRpCfg operation="delete">
          <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>
        </bsrAfsAutoRpCfg>
      </bsrAfsAutoRpCfgs>
    </bsrafspro>
</pim>
"""
# xml1
CE_NC_GET_MULTICAST_PIM_C_BSR = """
<filter type="subtree">
    <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bsrafspro>
          <bsrAfsSiteCfgs>
            <bsrAfsSiteCfg>
              <vrfName>%s</vrfName>
              <addressFamily>%s</addressFamily>
              <cBsrIfName></cBsrIfName>
              <cBsrHashLen></cBsrHashLen>
              <cBsrPriority></cBsrPriority>
              <isFragable></isFragable>
            </bsrAfsSiteCfg>
          </bsrAfsSiteCfgs>
        </bsrafspro>
    </pim>
</filter>
"""
CE_NC_MERGE_MULTICAST_PIM_C_BSR = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <bsrafspro>
      <bsrAfsSiteCfgs>
        <bsrAfsSiteCfg operation="merge">
         <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>%s%s%s%s
        </bsrAfsSiteCfg>
      </bsrAfsSiteCfgs>
    </bsrafspro>
</pim>
"""
CE_NC_MERGE_MULTICAST_PIM_C_BSR_IFNAME = """
    <cBsrIfName>%s</cBsrIfName>
"""
CE_NC_MERGE_MULTICAST_PIM_C_BSR_LEN = """
    <cBsrHashLen>%s</cBsrHashLen>
"""
CE_NC_MERGE_MULTICAST_PIM_C_BSR_PRI = """
    <cBsrPriority>%s</cBsrPriority>
"""
CE_NC_MERGE_MULTICAST_PIM_C_BSR_FRAG = """
    <isFragable>%s</isFragable>
"""
CE_NC_DELETE_MULTICAST_PIM_C_BSR = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <bsrafspro>
      <bsrAfsSiteCfgs>
        <bsrAfsSiteCfg operation="delete">
         <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>
        </bsrAfsSiteCfg>
      </bsrAfsSiteCfgs>
    </bsrafspro>
</pim>
"""
# xml4
CE_NC_GET_MULTICAST_PIM_C_RP = """
<filter type="subtree">
    <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
      <bsrafspro>
        <bsrAf4CrpCfgs>
          <bsrAf4CrpCfg>
            <vrfName>%s</vrfName>
            <cRpIfName>%s</cRpIfName>
            <cRpGrpPlyName></cRpGrpPlyName>
            <cRpPriority></cRpPriority>
            <cRpHoldTime></cRpHoldTime>
            <cRpAdvInterval></cRpAdvInterval>
            <cRpBidir></cRpBidir>
          </bsrAf4CrpCfg>
        </bsrAf4CrpCfgs>
      </bsrafspro>
    </pim>
</filter>
"""
CE_NC_MERGE_MULTICAST_PIM_C_RP = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <bsrafspro>
    <bsrAf4CrpCfgs>
      <bsrAf4CrpCfg operation="merge">
        <vrfName>%s</vrfName>
        <cRpIfName>%s</cRpIfName>%s%s%s%s%s
      </bsrAf4CrpCfg>
    </bsrAf4CrpCfgs>
  </bsrafspro>
</pim>
"""
CE_NC_MERGE_MULTICAST_PIM_C_RP_PRI = """
    <cRpPriority>%s</cRpPriority>
"""
CE_NC_MERGE_MULTICAST_PIM_C_RP_INTERVAL = """
    <cRpHoldTime>%s</cRpHoldTime>
"""
CE_NC_MERGE_MULTICAST_PIM_C_RP_ADINTERVAL = """
    <cRpAdvInterval>%s</cRpAdvInterval>
"""
CE_NC_MERGE_MULTICAST_PIM_C_RP_NAME = """
    <cRpGrpPlyName>%s</cRpGrpPlyName>
"""
CE_NC_MERGE_MULTICAST_PIM_C_RP_BID = """
    <cRpBidir>%s</cRpBidir>
"""
CE_NC_DELETE_MULTICAST_PIM_C_RP = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <bsrafspro>
    <bsrAf4CrpCfgs>
      <bsrAf4CrpCfg operation="delete">
        <vrfName>%s</vrfName>
        <cRpIfName>%s</cRpIfName>
      </bsrAf4CrpCfg>
    </bsrAf4CrpCfgs>
  </bsrafspro>
</pim>
"""
# xml3
CE_NC_GET_MULTICAST_PIM_INFO = """
<filter type="subtree">
    <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <pimafspro>
          <pimAfsSiteCfgs>
            <pimAfsSiteCfg>
              <vrfName>%s</vrfName>
              <addressFamily>%s</addressFamily>
              <sourceLifeTime></sourceLifeTime>
              <srcPlyName></srcPlyName>
              <helloInterval></helloInterval>
              <helloHoldtime></helloHoldtime>
              <drPriority></drPriority>
              <jpTimerInterval></jpTimerInterval>
              <jpTrigCacheDisable></jpTrigCacheDisable>
              <helloOverride></helloOverride>
              <helloLandelay></helloLandelay>
              <assertHoldTime></assertHoldTime>
              <jpHoldTime></jpHoldTime>
            </pimAfsSiteCfg>
          </pimAfsSiteCfgs>
        </pimafspro>
    </pim>
</filter>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <pimafspro>
      <pimAfsSiteCfgs>
        <pimAfsSiteCfg operation="merge">
          <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>%s%s%s%s
        </pimAfsSiteCfg>
      </pimAfsSiteCfgs>
    </pimafspro>
</pim>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_LIFETIME = """
<sourceLifeTime>%s</sourceLifeTime>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_SRCNAME = """
<srcPlyName>%s</srcPlyName>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_HELLOTIME = """
<helloInterval>%s</helloInterval>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_HELLOHOLDTIME = """
<helloHoldtime>%s</helloHoldtime>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_DRPRI = """
<drPriority>%s</drPriority>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_PRUNE = """
<jpTimerInterval>%s</jpTimerInterval>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_PRUNEHOLDTIME = """
<jpHoldTime>%s</jpHoldTime>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_CACHE = """
<jpTrigCacheDisable>%s</jpTrigCacheDisable>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_OVERTIME = """
<helloOverride>%s</helloOverride>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_DELAYTIME = """
<helloLandelay>%s</helloLandelay>
"""
CE_NC_MERGE_MULTICAST_PIM_INFO_ASSRETTIME = """
<assertHoldTime>%s</assertHoldTime>
"""
CE_NC_DELETE_MULTICAST_PIM_INFO = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <pimafspro>
      <pimAfsSiteCfgs>
        <pimAfsSiteCfg operation="delete">
          <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>
        </pimAfsSiteCfg>
      </pimAfsSiteCfgs>
    </pimafspro>
</pim>
"""
# xml3.3
CE_NC_GET_MULTICAST_PIM_BID = """
<filter type="subtree">
    <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <pimafspro>
          <pimAfsSiteCfgs>
            <pimAfsSiteCfg>
              <vrfName>%s</vrfName>
              <addressFamily>%s</addressFamily>
              <pimAfsBidirCfg>
                <bidirPimEnable></bidirPimEnable>
              </pimAfsBidirCfg>
            </pimAfsSiteCfg>
          </pimAfsSiteCfgs>
        </pimafspro>
    </pim>
</filter>
"""
CE_NC_MERGE_MULTICAST_PIM_BID = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <pimafspro>
    <pimAfsSiteCfgs>
      <pimAfsSiteCfg>
        <vrfName>%s</vrfName>
        <addressFamily>%s</addressFamily>
        <pimAfsBidirCfg operation="merge">
          <bidirPimEnable>%s</bidirPimEnable>
        </pimAfsBidirCfg>
      </pimAfsSiteCfg>
    </pimAfsSiteCfgs>
  </pimafspro>
</pim>
"""
# xml3.1
CE_NC_GET_MULTICAST_PIM_STATIC_RP = """
<filter type="subtree">
     <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <pimafspro>
          <pimAfsSiteCfgs>
            <pimAfsSiteCfg>
              <vrfName>%s</vrfName>
              <addressFamily>%s</addressFamily>
              <pimAfsStaticRps>
                <pimAfsStaticRp>
                  <staticRpAddr>%s</staticRpAddr>
                  <staticRpPlyName></staticRpPlyName>
                  <preference></preference>
                  <bidirEnable></bidirEnable>
                </pimAfsStaticRp>
              </pimAfsStaticRps>
            </pimAfsSiteCfg>
          </pimAfsSiteCfgs>
        </pimafspro>
     </pim>
</filter>
"""
CE_NC_MERGE_MULTICAST_PIM_STATIC_RP = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <pimafspro>
      <pimAfsSiteCfgs>
        <pimAfsSiteCfg>
          <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>
          <pimAfsStaticRps>
            <pimAfsStaticRp operation="merge">
              <staticRpAddr>%s</staticRpAddr>%s%s%s
            </pimAfsStaticRp>
          </pimAfsStaticRps>
        </pimAfsSiteCfg>
      </pimAfsSiteCfgs>
    </pimafspro>
</pim>
"""
CE_NC_MERGE_MULTICAST_PIM_STATIC_RP_NAME = """
    <staticRpPlyName>%s</staticRpPlyName>
"""
CE_NC_MERGE_MULTICAST_PIM_STATIC_RP_PRE = """
    <preference>%s</preference>
"""
CE_NC_MERGE_MULTICAST_PIM_STATIC_RP_BID = """
    <bidirEnable>%s</bidirEnable>
"""
CE_NC_DELETE_MULTICAST_PIM_STATIC_RP = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <pimafspro>
      <pimAfsSiteCfgs>
        <pimAfsSiteCfg>
          <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>
          <pimAfsStaticRps>
            <pimAfsStaticRp operation="delete">
              <staticRpAddr>%s</staticRpAddr>
            </pimAfsStaticRp>
          </pimAfsStaticRps>
        </pimAfsSiteCfg>
      </pimAfsSiteCfgs>
    </pimafspro>
</pim>
"""
# xml3.2
CE_NC_GET_MULTICAST_PIM_ANYCAST_RP = """
<filter type="subtree">
     <pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <pimafspro>
          <pimAfsSiteCfgs>
            <pimAfsSiteCfg>
              <vrfName>%s</vrfName>
              <addressFamily>%s</addressFamily>
              <pimAfsAnyRps>
                <pimAfsAnyRp>
                  <rpAddress>%s</rpAddress>
                  <localAddress></localAddress>
                </pimAfsAnyRp>
              </pimAfsAnyRps>
            </pimAfsSiteCfg>
          </pimAfsSiteCfgs>
        </pimafspro>
     </pim>
</filter>
"""
CE_NC_MERGE_MULTICAST_PIM_ANYCAST_RP = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <pimafspro>
      <pimAfsSiteCfgs>
        <pimAfsSiteCfg>
          <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>
          <pimAfsAnyRps>
            <pimAfsAnyRp operation="merge">
              <rpAddress>%s</rpAddress>%s
            </pimAfsAnyRp>
          </pimAfsAnyRps>
        </pimAfsSiteCfg>
      </pimAfsSiteCfgs>
    </pimafspro>
</pim>
"""
CE_NC_MERGE_MULTICAST_PIM_ANYCAST_RP_LOCALADDR = """
    <localAddress>%s</localAddress>
"""
CE_NC_DELETE_MULTICAST_PIM_ANYCAST_RP = """
<pim xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <pimafspro>
      <pimAfsSiteCfgs>
        <pimAfsSiteCfg>
          <vrfName>%s</vrfName>
          <addressFamily>%s</addressFamily>
          <pimAfsAnyRps>
            <pimAfsAnyRp operation="delete">
              <rpAddress>%s</rpAddress>
            </pimAfsAnyRp>
          </pimAfsAnyRps>
        </pimAfsSiteCfg>
      </pimAfsSiteCfgs>
    </pimafspro>
</pim>
"""


def get_xml(xml, value):
    """operate xml"""
    tempxml = xml % value
    return tempxml


def build_config_xml(xmlstr):
    """build config xml"""
    return '<config> ' + xmlstr + ' </config>'


def set_default_interval(obj, features, value):
    """set default interval"""
    if obj.features == features:
        if obj.interval is None:
            obj.interval = value


def validate_interval(obj, features, minv, maxv):
    """validate interval"""
    if obj.interval:
        if obj.features == features:
            if obj.interval < minv or obj.interval > maxv:
                obj.module.fail_json(
                    msg='Error: interval is not in the range '
                        'from %s to %s.' % (minv, maxv))


def check_ip_addr(ipaddr):
    """check ip address, Supports IPv4 and IPv6"""
    if not ipaddr or '\x00' in ipaddr:
        return False
    try:
        res = socket.getaddrinfo(ipaddr, 0, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM,
                                 0, socket.AI_NUMERICHOST)
        return bool(res)
    except socket.gaierror:
        err = sys.exc_info()[1]
        if err.args[0] == socket.EAI_NONAME:
            return False
        raise
    return True


def check_default_ip(ipaddr):
    """check the default multicast IP address"""

    # The value ranges from 1.0.0.0-126.255.255.255 or 128.0.0.0 - 223.255.255.255
    if not check_ip_addr(ipaddr):
        return False
    if ipaddr.count(".") != 3:
        return False
    ips = ipaddr.split(".")
    if not ips[0].isdigit() or int(ips[0]) < 1 \
            or int(ips[0]) == 127 or int(ips[0]) > 223:
        return False
    if not ips[1].isdigit() or int(ips[1]) < 0 or int(ips[3]) > 255:
        return False
    if not ips[2].isdigit() or int(ips[2]) < 0 or int(ips[3]) > 255:
        return False
    if not ips[3].isdigit() or int(ips[3]) < 0 or int(ips[3]) > 255:
        return False
    return True


class MulticastPim(object):
    """multicast pim module"""

    def __init__(self, argument_spec):
        """multicast pim info"""

        self.spec = argument_spec
        self.module = None
        self._initmodule_()

        self.aftype = self.module.params['aftype']
        self.state = self.module.params['state']
        self.features = self.module.params['features']
        if self.aftype == "v4":
            self.version = "ipv4unicast"
        else:
            self.version = "ipv6unicast"
        # vpn instance info
        self.vrf = self.module.params['vrf']
        if self.vrf is None:
            self.vrf = "_public_"
        self.ifname = self.module.params['ifname']
        self.hashlen = self.module.params['hashlen']
        self.frag = self.module.params['frag']
        self.interval = self.module.params['interval']
        self.method = self.module.params['method']
        tempvalue = 210
        if self.method == 'hello_interval':
            tempvalue = 30
        if self.method == 'hello_holdtime':
            tempvalue = 105
        if self.method == 'join_prune':
            tempvalue = 60
        if self.method == 'hello_over_interval':
            tempvalue = 2500
        if self.method == 'hello_lan_delay':
            tempvalue = 500
        if self.method == 'assert':
            tempvalue = 180
        set_default_interval(self, 'c_rp', 150)
        set_default_interval(self, 'pim', tempvalue)
        self.adinterval = self.module.params['adinterval']
        self.name = self.module.params['name']
        self.bid = self.module.params['bid']
        self.addr = self.module.params['addr']
        self.local_addr = self.module.params['local_addr']
        self.pre = self.module.params['pre']
        self.trigcache = self.module.params['trigcache']
        self.bid_enable = self.module.params['bid_enable']
        self.src_name = self.module.params['src_name']

        if self.bid.lower() == 'true':
            self.bid = 'Bidir'
        else:
            self.bid = 'NotBidir'

        if self.pre.lower() == 'true':
            self.pre = 'Prefer'
        else:
            self.pre = 'NotPrefer'

        self.pri = self.module.params['pri']
        if self.method == 'hello_option':
            if self.pri is None:
                self.pri = 1
        else:
            if self.pri is None:
                self.pri = 0
        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

        self.pim_data = dict()
        self.pim_data["pim_info"] = list()

    def _initmodule_(self):
        """init module"""
        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=False)

    def _checkresponse_(self, xml_str, xml_name):
        """check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def set_change_state(self):
        """set change state"""
        state = self.state
        change = False
        features = self.features
        if features == 'auto_rp':
            self.get_multicast_auto_rp()
            # new or edit
            if state == 'present':
                if not self.pim_data["pim"]:
                    # self.pim_data["pim"] has not value
                    change = True
            else:
                # delete
                if self.pim_data["pim"]:
                    # self.pim_data["pim"] has value
                    change = True
        elif features == 'c_bsr':
            self._getcbsr_()
            change = self._comparecbsr_()
        elif features == 'c_rp':
            self._getcrp_()
            change = self._comparecrp_()
        elif features == 'pim':
            self._getpim_()
            change = self._comparepim_()
        elif features == 'bid':
            self._getbid_()
            change = self._comparebid_()
        elif features == 'static_rp':
            self._getstaticrp_()
            change = self._comparestaticrp_()
        elif features == 'anycast_rp':
            self._getanycastrp_()
            change = self._compareanycastrp_()
        self.changed = change

    def _getanycastrp_(self):
        """get anycast_rp one data"""
        self.pim_data["pim"] = list()
        self.pim_data["pim_info"] = list()
        getxmlstr = CE_NC_GET_MULTICAST_PIM_ANYCAST_RP % (
            self.vrf, self.version, self.addr)
        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return
        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        anycast_rp_data = root.findall(
            "pim/pimafspro/pimAfsSiteCfgs/pimAfsSiteCfg/pimAfsAnyRps/pimAfsAnyRp")
        self._findpim_(root)
        if anycast_rp_data:
            for anycast_rp_value in anycast_rp_data:
                # anycast_rp_value = {rpAddress:x.x.x.x,localAddress:x.x.x.x}
                data_info = dict()
                for ele in anycast_rp_value:
                    if ele.tag in ["rpAddress", "localAddress"]:
                        data_info[ele.tag] = ele.text
                self.pim_data["pim"].append(data_info)

    def _getstaticrp_(self):
        """get static_rp one data"""
        self.pim_data["pim"] = list()
        self.pim_data["pim_info"] = list()
        getxmlstr = CE_NC_GET_MULTICAST_PIM_STATIC_RP % (
            self.vrf, self.version, self.addr)
        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return
        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        static_rp_data = root.findall(
            "pim/pimafspro/pimAfsSiteCfgs/pimAfsSiteCfg/pimAfsStaticRps/pimAfsStaticRp")
        self._findpim_(root)
        if static_rp_data:
            for static_rp_value in static_rp_data:
                # static_rp_value = {preference:11,staticRpAddr:x.x.x.x,bidirEnable:XX,staticRpPlyName:xx}
                data_info = dict()
                for ele in static_rp_value:
                    if ele.tag in ["staticRpAddr", "preference", "bidirEnable",
                                   "staticRpPlyName"]:
                        data_info[ele.tag] = ele.text
                self.pim_data["pim"].append(data_info)

    def _getcrp_(self):
        """get c_rp one data"""
        self.pim_data["pim"] = list()
        getxmlstr = CE_NC_GET_MULTICAST_PIM_C_RP % (
            self.vrf, self.ifname)
        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return
        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        c_rp_data = root.findall(
            "pim/bsrafspro/bsrAf4CrpCfgs/bsrAf4CrpCfg")
        if c_rp_data:
            # c_rp_data = [{vrfName:11,addressFamily:'xx'},{vrfName:22,addressFamily:'xx'}...]
            for c_rp_value in c_rp_data:
                # c_rp_value = {vrfName:11,addressFamily:'xx'}
                data_info = dict()
                for ele in c_rp_value:
                    if ele.tag in ["vrfName", "cRpIfName", "cRpGrpPlyName",
                                   "cRpPriority", "cRpHoldTime", "cRpAdvInterval", "cRpBidir"]:
                        data_info[ele.tag] = ele.text
                self.pim_data["pim"].append(data_info)

    def _getpim_(self):
        """get pim one data"""
        self.pim_data["pim"] = list()
        getxmlstr = CE_NC_GET_MULTICAST_PIM_INFO % (
            self.vrf, self.version)
        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return
        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        pim_info_data = root.findall(
            "pim/pimafspro/pimAfsSiteCfgs/pimAfsSiteCfg")
        if pim_info_data:
            # pim_info_data = [{vrfName:11,addressFamily:'xx'},{vrfName:22,addressFamily:'xx'}...]
            for pim_value in pim_info_data:
                # pim_value = {vrfName:11,addressFamily:'xx'}
                data_info = dict()
                for ele in pim_value:
                    if ele.tag in ["vrfName", "addressFamily", "sourceLifeTime",
                                   "srcPlyName", "helloInterval", "helloHoldtime", "drPriority",
                                   "jpTimerInterval", "jpHoldTime", "helloOverride", "helloLandelay",
                                   "assertHoldTime", "jpTrigCacheDisable"]:
                        data_info[ele.tag] = ele.text
                self.pim_data["pim"].append(data_info)

    def _findpim_(self, root):
        """get pim of vrfName and addressFamily"""
        pim_info_data = root.findall(
            "pim/pimafspro/pimAfsSiteCfgs/pimAfsSiteCfg")
        if pim_info_data:
            # pim_info_data = [{vrfName:11,addressFamily:'xx'},{vrfName:22,addressFamily:'xx'}...]
            for pim_value in pim_info_data:
                # pim_value = {vrfName:11,addressFamily:'xx'}
                data_info = dict()
                for ele in pim_value:
                    if ele.tag in ["vrfName", "addressFamily"]:
                        data_info[ele.tag] = ele.text
                self.pim_data["pim_info"].append(data_info)

    def _getbid_(self):
        """get bidir-pim one data"""
        self.pim_data["pim"] = list()
        self.pim_data["pim_info"] = list()
        getxmlstr = CE_NC_GET_MULTICAST_PIM_BID % (
            self.vrf, self.version)
        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return
        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        bidir_data = root.findall(
            "pim/pimafspro/pimAfsSiteCfgs/pimAfsSiteCfg/pimAfsBidirCfg")
        self._findpim_(root)
        if bidir_data:
            # bidir_data = [{bidirPimEnable:true}]
            for bidir_value in bidir_data:
                # bidir_value = {bidirPimEnable:true}
                data_info = dict()
                for ele in bidir_value:
                    if ele.tag in ["bidirPimEnable"]:
                        data_info[ele.tag] = ele.text
                self.pim_data["pim"].append(data_info)

    def _getcbsr_(self):
        """get c_bsr one data"""
        self.pim_data["pim"] = list()
        getxmlstr = CE_NC_GET_MULTICAST_PIM_C_BSR % (
            self.vrf, self.version)
        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return
        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        c_bsr_data = root.findall('pim/bsrafspro/bsrAfsSiteCfgs/bsrAfsSiteCfg')
        if c_bsr_data:
            # c_bsr_data = [{vrfName:11,addressFamily:'xx'},{vrfName:22,addressFamily:'xx'}...]
            for c_bsr_value in c_bsr_data:
                # c_bsr_value = {vrfName:11,addressFamily:'xx'}
                data_info = dict()
                for ele in c_bsr_value:
                    if ele.tag in ["vrfName", "addressFamily", "cBsrIfName",
                                   "cBsrHashLen", "cBsrPriority", "isFragable"]:
                        data_info[ele.tag] = ele.text
                self.pim_data["pim"].append(data_info)

    def _comparepim_(self):
        """compare pim data"""
        method = self.method
        state = self.state
        change = False
        # new or edit
        if state == 'present':
            # edit
            if self.pim_data["pim"]:
                for data in self.pim_data["pim"]:
                    if self.version == data["addressFamily"] and self.vrf == data["vrfName"]:
                        if self.src_name:
                            if self.src_name != data["srcPlyName"]:
                                change = True
                        else:
                            if data["srcPlyName"]:
                                change = True
                        if method == 'hello_option':
                            if str(self.pri) != data["drPriority"]:
                                change = True
                        if method == 'lifetime':
                            if str(self.interval) != data["sourceLifeTime"]:
                                change = True
                        if method == 'hello_interval':
                            if str(self.interval) != data["helloInterval"]:
                                change = True
                        if method == 'hello_holdtime':
                            if str(self.interval) != data["helloHoldtime"]:
                                change = True
                        if method == 'join_prune':
                            if str(self.interval) != data["jpTimerInterval"]:
                                change = True
                        if method == 'join_prune_holdtime':
                            if str(self.interval) != data["jpHoldTime"]:
                                change = True
                        if method == 'hello_over_interval':
                            if str(self.interval) != data["helloOverride"]:
                                change = True
                        if method == 'hello_lan_delay':
                            if str(self.interval) != data["helloLandelay"]:
                                change = True
                        if method == 'assert':
                            if str(self.interval) != data["assertHoldTime"]:
                                change = True
                        if self.trigcache.lower() != data["jpTrigCacheDisable"].lower():
                            change = True
            # new
            else:
                change = True
        else:
            # delete
            if self.pim_data["pim"]:
                change = True
        return change

    def _comparebid_(self):
        """compare bidir-pim data"""
        change = False
        pim_info = self.pim_data["pim_info"]
        if self.pim_data["pim"] and pim_info:
            for data in self.pim_data["pim"]:
                if self.version == pim_info[0]["addressFamily"] and self.vrf == pim_info[0]["vrfName"]:
                    if self.bid_enable.lower() != data["bidirPimEnable"].lower():
                        change = True
        else:
            change = True
        return change

    def _compareanycastrp_(self):
        """compare anycast_rp data"""
        state = self.state
        change = False
        pim_info = self.pim_data["pim_info"]
        # new or edit
        if state == 'present':
            # edit
            if self.pim_data["pim"] and pim_info:
                for data in self.pim_data["pim"]:
                    if self.version == pim_info[0]["addressFamily"] and self.vrf == pim_info[0]["vrfName"]:
                        if self.local_addr:
                            if self.local_addr != data["localAddress"]:
                                change = True
                        else:
                            if data["localAddress"]:
                                change = True
                        if self.addr != data["rpAddress"]:
                            change = True

            # new
            else:
                change = True
        else:
            # delete
            if self.pim_data["pim"] and pim_info:
                change = True
        return change

    def _comparestaticrp_(self):
        """compare static_rp data"""
        state = self.state
        change = False
        pim_info = self.pim_data["pim_info"]
        # new or edit
        if state == 'present':
            # edit
            if self.pim_data["pim"] and pim_info:
                for data in self.pim_data["pim"]:
                    if self.version == pim_info[0]["addressFamily"] and self.vrf == pim_info[0]["vrfName"]:
                        if self.name:
                            if self.name != data["staticRpPlyName"]:
                                change = True
                        else:
                            if data["staticRpPlyName"]:
                                change = True
                        if self.addr != data["staticRpAddr"]:
                            change = True
                        if self.bid.lower() != data["bidirEnable"].lower():
                            change = True
                        if self.pre.lower() != data["preference"].lower():
                            change = True
            # new
            else:
                change = True
        else:
            # delete
            if self.pim_data["pim"] and pim_info:
                change = True
        return change

    def _comparecrp_(self):
        """compare c_rp data"""
        state = self.state
        change = False
        # new or edit
        if state == 'present':
            # edit
            if self.pim_data["pim"]:
                for data in self.pim_data["pim"]:
                    if self.ifname == data["cRpIfName"] and self.vrf == data["vrfName"]:
                        if self.name:
                            if self.name != data["cRpGrpPlyName"]:
                                change = True
                        else:
                            if data["cRpGrpPlyName"]:
                                change = True
                        if str(self.pri) != data["cRpPriority"]:
                            change = True
                        if str(self.interval) != data["cRpHoldTime"]:
                            change = True
                        if str(self.adinterval) != data["cRpAdvInterval"]:
                            change = True
                        if self.bid.lower() != data["cRpBidir"].lower():
                            change = True
            # new
            else:
                change = True
        else:
            # delete
            if self.pim_data["pim"]:
                change = True
        return change

    def _comparecbsr_(self):
        """compare c_bsr data"""
        state = self.state
        change = False
        # new or edit
        if state == 'present':
            # edit
            if self.pim_data["pim"]:
                for data in self.pim_data["pim"]:
                    if self.version == data["addressFamily"] and self.vrf == data["vrfName"]:
                        if self.ifname:
                            if self.ifname != data["cBsrIfName"]:
                                change = True
                        if str(self.hashlen) != data["cBsrHashLen"]:
                            change = True
                        if str(self.pri) != data["cBsrPriority"]:
                            change = True
                        if self.frag:
                            if self.frag.lower() != data["isFragable"].lower():
                                change = True
            # new
            else:
                change = True
        else:
            # delete
            if self.pim_data["pim"]:
                change = True
        return change

    def get_multicast_auto_rp(self):
        """get auto_rp one data"""
        self.pim_data["pim"] = list()
        getxmlstr = CE_NC_GET_MULTICAST_PIM_AUTO_RP % (
            self.vrf, self.version)
        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return
        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        auto_rp_data = root.findall('pim/bsrafspro/bsrAfsAutoRpCfgs/bsrAfsAutoRpCfg')
        if auto_rp_data:
            # auto_rp_data = [{vrfName:11,addressFamily:'xx'},{vrfName:22,addressFamily:'xx'}...]
            for auto_rp_value in auto_rp_data:
                # auto_rp_value = {vrfName:11,addressFamily:'xx'}
                data_info = dict()
                for ele in auto_rp_value:
                    if ele.tag in ["vrfName", "addressFamily"]:
                        data_info[ele.tag] = ele.text
                self.pim_data["pim"].append(data_info)

    def set_auto_rp(self, state, version):
        """set auto-rp"""
        if state == "present":
            configxmlstr = CE_NC_MERGE_MULTICAST_PIM_AUTO_RP % (self.vrf, version)
        else:
            configxmlstr = CE_NC_DELETE_MULTICAST_PIM_AUTO_RP % (self.vrf, version)

        conf_str = build_config_xml(configxmlstr)
        recv_xml = set_nc_config(self.module, conf_str)
        self._checkresponse_(recv_xml, "SET_AUTO_RP")

    def _setpim_(self, state):
        """set pim netconf"""
        src_name_xml = """\n"""
        trigcache_xml = """\n"""
        interval_xml = """\n"""
        pri_xml = """\n"""
        method = self.method
        if state == "present":
            if self.src_name:
                src_name_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_SRCNAME, self.src_name)
            else:
                src_name_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_SRCNAME, '')
            if method == 'lifetime':
                interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_LIFETIME, self.interval)
            if method == 'hello_interval':
                interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_HELLOTIME, self.interval)
            if method == 'hello_holdtime':
                interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_HELLOHOLDTIME, self.interval)
            if method == 'join_prune':
                interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_PRUNE, self.interval)
            if method == 'join_prune_holdtime':
                interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_PRUNEHOLDTIME, self.interval)
            if method == 'hello_over_interval':
                interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_OVERTIME, self.interval)
            if method == 'hello_lan_delay':
                interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_DELAYTIME, self.interval)
            if method == 'assert':
                interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_ASSRETTIME, self.interval)
            if method == 'hello_option':
                pri_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_DRPRI, self.pri)
            trigcache_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_INFO_CACHE, self.trigcache.lower())
            configxmlstr = CE_NC_MERGE_MULTICAST_PIM_INFO % (
                self.vrf, self.version, src_name_xml, interval_xml, pri_xml, trigcache_xml)
        else:
            configxmlstr = CE_NC_DELETE_MULTICAST_PIM_INFO % (self.vrf, self.version)

        conf_str = build_config_xml(configxmlstr)
        recv_xml = set_nc_config(self.module, conf_str)
        self._checkresponse_(recv_xml, "SET_PIM")

    def _setbid_(self):
        """set bidir-pim netconf"""
        configxmlstr = CE_NC_MERGE_MULTICAST_PIM_BID % (self.vrf, self.version, self.bid_enable)
        conf_str = build_config_xml(configxmlstr)
        recv_xml = set_nc_config(self.module, conf_str)
        self._checkresponse_(recv_xml, "SET_BID")

    def _setanycastrp_(self, state):
        """set anycast-rp netconf"""
        local_xml = """\n"""
        if state == "present":
            if self.local_addr:
                local_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_ANYCAST_RP_LOCALADDR, self.local_addr)
            else:
                local_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_ANYCAST_RP_LOCALADDR, '')
            configxmlstr = CE_NC_MERGE_MULTICAST_PIM_ANYCAST_RP % (
                self.vrf, self.version, self.addr, local_xml)
        else:
            configxmlstr = CE_NC_DELETE_MULTICAST_PIM_ANYCAST_RP % (
                self.vrf, self.version, self.addr)
        conf_str = build_config_xml(configxmlstr)
        recv_xml = set_nc_config(self.module, conf_str)
        self._checkresponse_(recv_xml, "SET_ANYCAST_RP")

    def _setstaticrp_(self, state):
        """set static-rp netconf"""
        name_xml = """\n"""
        pre_xml = """\n"""
        bid_xml = """\n"""
        if state == "present":
            if self.name:
                name_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_STATIC_RP_NAME, self.name)
            else:
                name_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_STATIC_RP_NAME, '')
            pre_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_STATIC_RP_PRE, self.pre)
            bid_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_STATIC_RP_BID, self.bid)
            configxmlstr = CE_NC_MERGE_MULTICAST_PIM_STATIC_RP % (
                self.vrf, self.version, self.addr, name_xml, pre_xml, bid_xml)
        else:
            configxmlstr = CE_NC_DELETE_MULTICAST_PIM_STATIC_RP % (
                self.vrf, self.version, self.addr)

        conf_str = build_config_xml(configxmlstr)
        recv_xml = set_nc_config(self.module, conf_str)
        self._checkresponse_(recv_xml, "SET_STATIC_RP")

    def _setcrp_(self, state):
        """set c-rp netconf"""
        name_xml = """\n"""
        pri_xml = """\n"""
        interval_xml = """\n"""
        adinterval_xml = """\n"""
        bid_xml = """\n"""
        if state == "present":
            if self.name:
                name_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_RP_NAME, self.name)
            else:
                name_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_RP_NAME, '')
            pri_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_RP_PRI, self.pri)
            interval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_RP_INTERVAL, self.interval)
            adinterval_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_RP_ADINTERVAL, self.adinterval)
            bid_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_RP_BID, self.bid)
            configxmlstr = CE_NC_MERGE_MULTICAST_PIM_C_RP % (
                self.vrf, self.ifname, pri_xml, interval_xml,
                adinterval_xml, bid_xml, name_xml)
        else:
            configxmlstr = CE_NC_DELETE_MULTICAST_PIM_C_RP % (self.vrf, self.ifname)

        conf_str = build_config_xml(configxmlstr)
        recv_xml = set_nc_config(self.module, conf_str)
        self._checkresponse_(recv_xml, "SET_C_RP")

    def _setcbsrnc_(self, state, version):
        """set c-bsr netconf"""
        ifname_xml = """\n"""
        hashlen_xml = """\n"""
        pri_xml = """\n"""
        frag_xml = """\n"""
        if state == "present":
            if self.ifname:
                ifname_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_BSR_IFNAME, self.ifname)
            hashlen_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_BSR_LEN, self.hashlen)
            pri_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_BSR_PRI, self.pri)
            frag_xml = get_xml(CE_NC_MERGE_MULTICAST_PIM_C_BSR_FRAG, self.frag.lower())
            configxmlstr = CE_NC_MERGE_MULTICAST_PIM_C_BSR % (
                self.vrf, version, ifname_xml, hashlen_xml, pri_xml, frag_xml)
        else:
            configxmlstr = CE_NC_DELETE_MULTICAST_PIM_C_BSR % (self.vrf, version)

        conf_str = build_config_xml(configxmlstr)
        recv_xml = set_nc_config(self.module, conf_str)
        self._checkresponse_(recv_xml, "SET_C_BSR")

    def _setbidcmd_(self):
        """set bidir-pim cmd"""
        if self.bid_enable.lower() != 'true':
            self.updates_cmd.append('undo bidir-pim')
        else:
            self.updates_cmd.append('bidir-pim')

    def _setcbsrcmd_(self):
        """set c-bsr cmd"""
        if self.state == "present":
            if self.frag.lower() != 'true':
                self.updates_cmd.append('undo bsm semantic fragmentation')
            else:
                self.updates_cmd.append('bsm semantic fragmentation')
            self.updates_cmd.append('c-bsr ')
            if self.ifname:
                self.updates_cmd.append('%s ' % self.ifname)
            if self.hashlen != 30:
                self.updates_cmd.append('%s ' % self.hashlen)
            if self.pri != 0:
                self.updates_cmd.append('%s' % self.pri)
        else:
            self.updates_cmd.append('undo c-bsr')

    def _setpimcmd_(self):
        """set pim cmd"""
        if self.state == "present":
            if self.src_name:
                if self.src_name.isdigit():
                    self.updates_cmd.append(' source-policy  %s ' % self.src_name)
                else:
                    self.updates_cmd.append(' source-policy acl-name %s ' % self.src_name)
            else:
                self.updates_cmd.append(' undo source-policy ')
            if self.method == 'lifetime':
                if self.interval != 210:
                    self.updates_cmd.append(' source-lifetime %s ' % self.interval)
                else:
                    self.updates_cmd.append(' undo source-lifetime ')
            if self.method == 'hello_interval':
                if self.interval != 30:
                    self.updates_cmd.append(' timer hello %s ' % self.interval)
                else:
                    self.updates_cmd.append(' undo timer hello ')
            if self.method == 'hello_holdtime':
                if self.interval != 105:
                    self.updates_cmd.append(' hello-option holdtime %s ' % self.interval)
                else:
                    self.updates_cmd.append(' undo hello-option holdtime ')
            if self.method == 'join_prune':
                if self.interval != 60:
                    self.updates_cmd.append(' timer join-prune %s ' % self.interval)
                else:
                    self.updates_cmd.append(' undo timer join-prune ')
            if self.method == 'join_prune_holdtime':
                if self.interval != 210:
                    self.updates_cmd.append(' holdtime join-prune %s ' % self.interval)
                else:
                    self.updates_cmd.append(' undo holdtime join-prune ')
            if self.method == 'hello_over_interval':
                if self.interval != 2500:
                    self.updates_cmd.append(' hello-option override-interval %s ' % self.interval)
                else:
                    self.updates_cmd.append(' undo hello-option override-interval ')

            if self.method == 'hello_lan_delay':
                if self.interval != 500:
                    self.updates_cmd.append(' hello-option lan-delay %s ' % self.interval)
                else:
                    self.updates_cmd.append(' undo hello-option lan-delay ')
            if self.method == 'assert':
                if self.interval != 180:
                    self.updates_cmd.append(' holdtime assert %s ' % self.interval)
                else:
                    self.updates_cmd.append(' undo holdtime assert ')

            if self.method == 'hello_option':
                if self.pri != 1:
                    self.updates_cmd.append(' hello-option dr-priority %s ' % self.pri)
                else:
                    self.updates_cmd.append(' undo hello-option dr-priority ')
            if self.trigcache.lower() == 'true':
                self.updates_cmd.append(' join-prune triggered-message-cache disable ')
            else:
                self.updates_cmd.append(' undo join-prune triggered-message-cache disable ')
        else:
            self.updates_cmd.append('undo source-lifetime ')
            self.updates_cmd.append(' undo source-policy ')
            self.updates_cmd.append(' undo timer hello ')
            self.updates_cmd.append(' undo hello-option holdtime ')
            self.updates_cmd.append(' undo hello-option dr-priority ')
            self.updates_cmd.append(' undo timer join-prune ')
            self.updates_cmd.append(' undo holdtime join-prune ')
            self.updates_cmd.append(' undo hello-option override-interval ')
            self.updates_cmd.append(' undo join-prune triggered-message-cache disable ')
            self.updates_cmd.append(' undo hello-option lan-delay ')
            self.updates_cmd.append(' undo holdtime assert ')

    def _setanycastrpcmd_(self):
        """set anycast-rp cmd"""
        if self.state == "present":
            self.updates_cmd.append('anycast-rp %s ' % self.addr)
            if self.local_addr:
                self.updates_cmd.append(' local-address %s ' % self.local_addr)
            else:
                self.updates_cmd.append(' undo local-address ')
        else:
            self.updates_cmd.append('undo anycast-rp %s ' % self.addr)
            self.updates_cmd.append('undo local-address ')

    def _setstaticrpcmd_(self):
        """set static-rp cmd"""
        if self.state == "present":
            self.updates_cmd.append('static-rp %s ' % self.addr)
            if self.name:
                if self.name.isdigit():
                    self.updates_cmd.append(' %s ' % self.name)
                else:
                    self.updates_cmd.append(' acl-name %s ' % self.name)
            if self.pre.lower() != 'notprefer':
                self.updates_cmd.append(' preferred ')
            if self.bid.lower() != 'notbidir':
                self.updates_cmd.append(' bidir')
        else:
            self.updates_cmd.append('undo static-rp %s ' % self.addr)

    def _setcrpcmd_(self):
        """set c-rp cmd"""
        if self.state == "present":
            self.updates_cmd.append('c-rp %s ' % self.ifname)
            if self.name:
                if self.name.isdigit():
                    self.updates_cmd.append(' group-policy %s ' % self.name)
                else:
                    self.updates_cmd.append(' group-policy acl-name %s ' % self.name)
            if self.pri != 0:
                self.updates_cmd.append(' priority %s ' % self.pri)
            if self.interval != 150:
                self.updates_cmd.append(' holdtime %s ' % self.interval)
            if self.adinterval != 60:
                self.updates_cmd.append(' advertisement-interval %s ' % self.adinterval)
            if self.bid.lower() != 'notbidir':
                self.updates_cmd.append(' bidir')
        else:
            self.updates_cmd.append('undo c-rp %s ' % self.ifname)

    def _checkparams_(self):
        """check all input params"""
        # check ifname
        if self.features == 'c_rp':
            if not self.ifname:
                self.module.fail_json(msg='Error: missing required arguments: ifname.')
        if self.ifname:
            if len(self.ifname) <= 0 or len(self.ifname) > 63:
                self.module.fail_json(
                    msg='Error: ifname is not in the range from 1 to 63.')
        # check  hashlen
        if self.hashlen:
            if self.hashlen < 0 or self.hashlen > 32:
                self.module.fail_json(
                    msg='Error: hashlen is not in the range from 0 to 32.')
        # check pri
        minpri = 0
        maxpri = 255
        if self.features == 'pim':
            if self.method == 'hello_option':
                minpri = 0
                maxpri = 4294967295
        if self.pri:
            if self.pri < minpri or self.pri > maxpri:
                self.module.fail_json(
                    msg='Error: pri is not in the range from %s to %s.' % (minpri, maxpri))
        # check interval
        validate_interval(self, 'c_rp', 1, 65535)
        minv = 60
        maxv = 65535
        if self.method == 'hello_interval' or self.method == 'join_prune':
            minv = 1
            maxv = 18000
        if self.method == 'hello_holdtime' or \
                self.method == 'join_prune_holdtime' or self.method == 'hello_over_interval':
            minv = 1
            maxv = 65535
        if self.method == 'hello_lan_delay':
            minv = 1
            maxv = 32767
        if self.method == 'assert':
            minv = 7
            maxv = 65535
        validate_interval(self, 'pim', minv, maxv)
        # check adinterval
        if self.adinterval:
            if self.adinterval < 1 or self.adinterval > 65535:
                self.module.fail_json(
                    msg='Error: adinterval is not in the range from 1 to 65535.')
        # check name
        if self.name:
            if self.name.isdigit():
                if int(self.name) < 2000 or int(self.name) > 2999:
                    self.module.fail_json(
                        msg='Error: name is not in the range from 2000 to 2999.')
            else:
                if len(self.name) < 1 or len(self.name) > 32:
                    self.module.fail_json(
                        msg='Error: name is not in the range from 1 to 32.')
        # check src_name
        if self.src_name:
            if self.src_name.isdigit():
                if int(self.src_name) < 2000 or int(self.src_name) > 3999:
                    self.module.fail_json(
                        msg='Error: src_name is not in the range from 2000 to 3999.')
            else:
                if len(self.src_name) < 1 or len(self.src_name) > 32:
                    self.module.fail_json(
                        msg='Error: src_name is not in the range from 1 to 32.')
        # check addr
        if self.features == 'static_rp' or self.features == 'anycast_rp':
            if not self.addr:
                self.module.fail_json(msg='Error: missing required arguments: addr.')
            if not check_default_ip(self.addr):
                self.module.fail_json(msg='Error: addr ipaddress is invalid')
        # check local_addr
        if self.features == 'anycast_rp':
            if self.local_addr:
                if not check_default_ip(self.addr):
                    self.module.fail_json(msg='Error: local_addr ipaddress is invalid')

    def get_existing(self):
        """get existing information"""
        self.set_change_state()
        self.existing["pim"] = self.pim_data["pim"]
        self.existing["pim_info"] = self.pim_data["pim_info"]

    def get_proposed(self):
        """get proposed information"""
        self.proposed['features'] = self.features
        self.proposed['addressFamily'] = self.version
        self.proposed['state'] = self.state
        self.proposed['vrfName'] = self.vrf
        if self.features == 'c_bsr':
            if self.ifname:
                self.proposed['cBsrIfName'] = self.ifname
            self.proposed['cBsrHashLen'] = self.hashlen
            self.proposed['cBsrPriority'] = self.pri
            self.proposed['isFragable'] = self.frag
        if self.features == 'c_rp':
            self.proposed['cRpIfName'] = self.ifname
            self.proposed['cRpPriority'] = self.pri
            self.proposed['cRpHoldTime'] = self.interval
            self.proposed['cRpAdvInterval'] = self.adinterval
            if self.name:
                self.proposed['cRpGrpPlyName'] = self.name
            self.proposed['cRpBidir'] = self.bid
        if self.features == 'pim':
            self.proposed['method'] = self.method
            if self.src_name:
                self.proposed['srcPlyName'] = self.src_name
            if self.method == 'lifetime':
                self.proposed['sourceLifeTime'] = self.interval
            if self.method == 'hello_interval':
                self.proposed['helloInterval'] = self.interval
            if self.method == 'hello_holdtime':
                self.proposed['helloHoldtime'] = self.interval
            if self.method == 'join_prune':
                self.proposed['jpTimerInterval'] = self.interval
            if self.method == 'join_prune_holdtime':
                self.proposed['jpHoldTime'] = self.interval
            if self.method == 'hello_over_interval':
                self.proposed['helloOverride'] = self.interval
            if self.method == 'hello_lan_delay':
                self.proposed['helloLandelay'] = self.interval
            if self.method == 'assert':
                self.proposed['assertHoldTime'] = self.interval
            if self.method == 'hello_option':
                self.proposed['drPriority'] = self.pri
            self.proposed['jpTrigCacheDisable'] = self.trigcache
        if self.features == 'bid':
            self.proposed['bidirPimEnable'] = self.bid_enable
        if self.features == 'static_rp':
            self.proposed['staticRpAddr'] = self.addr
            self.proposed['preference'] = self.pre
            self.proposed['bidirEnable'] = self.bid
            if self.name:
                self.proposed['staticRpPlyName'] = self.name
        if self.features == 'anycast_rp':
            self.proposed['rpAddress'] = self.addr
            self.proposed['localAddress'] = self.local_addr

    def set_pim_netconf(self):
        """get pim netconf"""
        if not self.changed:
            return
        if self.features == 'auto_rp':
            self.set_auto_rp(self.state, self.version)
        elif self.features == 'c_bsr':
            self._setcbsrnc_(self.state, self.version)
        elif self.features == 'c_rp':
            self._setcrp_(self.state)
        elif self.features == 'pim':
            self._setpim_(self.state)
        elif self.features == 'bid':
            self._setbid_()
        elif self.features == 'static_rp':
            self._setstaticrp_(self.state)
        elif self.features == 'anycast_rp':
            self._setanycastrp_(self.state)

    def set_update_cmd(self):
        """set update command"""
        if not self.changed:
            return
        if self.features == 'auto_rp':
            if self.state == "present":
                self.updates_cmd.append('auto-rp listening enable')
            else:
                self.updates_cmd.append('undo auto-rp listening enable')
        elif self.features == 'c_bsr':
            self._setcbsrcmd_()
        elif self.features == 'c_rp':
            self._setcrpcmd_()
        elif self.features == 'pim':
            self._setpimcmd_()
        elif self.features == 'bid':
            self._setbidcmd_()
        elif self.features == 'static_rp':
            self._setstaticrpcmd_()
        elif self.features == 'anycast_rp':
            self._setanycastrpcmd_()

    def get_end_state(self):
        """get end state information"""
        if self.features == 'auto_rp':
            self.get_multicast_auto_rp()
        elif self.features == 'c_bsr':
            self._getcbsr_()
        elif self.features == 'c_rp':
            self._getcrp_()
        elif self.features == 'pim':
            self._getpim_()
        elif self.features == 'bid':
            self._getbid_()
        elif self.features == 'static_rp':
            self._getstaticrp_()
        elif self.features == 'anycast_rp':
            self._getanycastrp_()
        self.end_state["pim"] = self.pim_data["pim"]

    def work(self):
        """worker"""
        self._checkparams_()
        self.get_existing()
        self.get_proposed()
        self.set_pim_netconf()
        self.set_update_cmd()
        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['existing'] = self.existing
        self.results['proposed'] = self.proposed
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()
        self.module.exit_json(**self.results)


def main():
    """main"""

    argument_spec = dict(
        features=dict(choices=['c_bsr', 'auto_rp', 'c_rp',
                               'pim', 'bid', 'static_rp', 'anycast_rp'], required=True, type='str'),
        method=dict(choices=['lifetime', 'hello_interval', 'hello_holdtime',
                             'hello_option', 'join_prune', 'join_prune_holdtime',
                             'hello_over_interval', 'hello_lan_delay', 'assert'], required=False, type='str'),
        aftype=dict(choices=['v4', 'v6'], required=True),
        vrf=dict(required=False, type='str'),
        ifname=dict(required=False, type='str'),
        hashlen=dict(required=False, type='int', default=30),
        pri=dict(required=False, type='int'),
        interval=dict(required=False, type='int'),
        adinterval=dict(required=False, type='int', default=60),
        name=dict(required=False, type='str'),
        src_name=dict(required=False, type='str'),
        frag=dict(type='bool'),
        bid=dict(type='bool'),
        bid_enable=dict(type='bool'),
        trigcache=dict(type='bool'),
        pre=dict(type='bool'),
        addr=dict(type='str'),
        local_addr=dict(type='str'),
        state=dict(choices=['absent', 'present'],
                   default='present', required=False),
    )
    interface = MulticastPim(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
