#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ce_is_is_view
version_added: "2.10"
author: xuxiaowei0512 (@CloudEngine-Ansible)
short_description: Manages isis view configuration on HUAWEI CloudEngine devices.
description:
    - Manages isis process id, creates a isis instance id or deletes a process id
      on HUAWEI CloudEngine devices.
options:
  coststyle:
    description:
      - Specifies the cost style.
    type: str
    choices: ['narrow', 'wide', 'transition', 'ntransition', 'wtransition']
  cost_type:
    description:
      - Specifies the cost type.
    type: str
    choices: ['external', 'internal']
  defaultmode:
    description:
      - Specifies the default mode.
    type: str
    choices: ['always', 'matchDefault', 'matchAny']
  export_policytype:
    description:
      - Specifies the default mode.
    type: str
    choices: ['aclNumOrName', 'ipPrefix', 'routePolicy']
  export_protocol:
    description:
      - Specifies the export router protocol.
    type: str
    choices: ['direct', 'ospf', 'isis', 'static', 'rip', 'bgp', 'ospfv3', 'all']
  impotr_leveltype:
    description:
      - Specifies the export router protocol.
    type: str
    choices: ['level_1', 'level_2', 'level_1_2']
  islevel:
    description:
      - Specifies the isis level.
    type: str
    choices: ['level_1', 'level_2', 'level_1_2']
  level_type:
    description:
      - Specifies the isis level type.
    type: str
    choices: ['level_1', 'level_2', 'level_1_2']
  penetration_direct:
    description:
      - Specifies the penetration direct.
    type: str
    choices: ['level2-level1', 'level1-level2']
  protocol:
    description:
      - Specifies the protocol.
    type: str
    choices: ['direct', 'ospf', 'isis', 'static', 'rip', 'bgp', 'ospfv3', 'all']
  aclnum_or_name:
    description:
      - Specifies the acl number or name for isis.
    type: str
  allow_filter:
    description:
      - Specifies the alow filter or not.
    type: bool
  allow_up_down:
    description:
      - Specifies the alow up or down.
    type: bool
  autocostenable:
    description:
      - Specifies the alow auto cost enable.
    type: bool
  autocostenablecompatible:
    description:
      - Specifies the alow auto cost enable compatible.
    type: bool
  avoid_learning:
    description:
      - Specifies the alow avoid learning.
    type: bool
  bfd_min_tx:
    description:
      - Specifies the bfd min sent package.
    type: int
  bfd_min_rx:
    description:
      - Specifies the bfd min received package.
    type: int
  bfd_multiplier_num:
    description:
      - Specifies the bfd multiplier number.
    type: int
  cost:
    description:
      - Specifies the bfd cost.
    type: int
  description:
    description:
      - Specifies description of isis.
    type: str
  enablelevel1tolevel2:
    description:
      - Enable level1 to level2.
    type: bool
  export_aclnumorname:
    description:
      - Specifies export acl number or name.
    type: str
  export_ipprefix:
    description:
      - Specifies export ip prefix.
    type: str
  export_processid:
    description:
      - Specifies export process id.
    type: int
  export_routepolicyname:
    description:
      - Specifies export route policy name.
    type: str
  import_aclnumorname:
    description:
      - Specifies import acl number or name.
    type: str
  import_cost:
    description:
      - Specifies import cost.
    type: int
  import_ipprefix:
    description:
      - Specifies import ip prefix.
    type: str
  import_route_policy:
    description:
      - Specifies import route policy.
    type: str
  import_routepolicy_name:
    description:
      - Specifies import route policy name.
    type: str
  import_routepolicyname:
    description:
      - Specifies import route policy name.
    type: str
  import_tag:
    description:
      - Specifies import tag.
    type: int
  inheritcost:
    description:
      - Enable inherit cost.
    type: bool
  instance_id:
    description:
      - Specifies instance id.
    type: int
  ip_address:
    description:
      - Specifies ip address.
    type: str
  ip_prefix_name:
    description:
      - Specifies ip prefix name.
    type: str
  max_load:
    description:
      - Specifies route max load.
    type: int
  mode_routepolicyname:
    description:
      - Specifies the mode of route polic yname.
    type: str
  mode_tag:
    description:
      - Specifies the tag of mode.
    type: int
  netentity:
    description:
      - Specifies the netentity.
    type: str
  permitibgp:
    description:
      - Specifies the permitibgp.
    type: bool
  processid:
    description:
      - Specifies the process id.
    type: int
  relaxspfLimit:
    description:
      - Specifies enable the relax spf limit.
    type: bool
  route_policy_name:
    description:
      - Specifies the route policy name.
    type: str
  stdbandwidth:
    description:
      - Specifies the std band width.
    type: int
  stdlevel1cost:
    description:
      - Specifies the std level1 cost.
    type: int
  stdlevel2cost:
    description:
      - Specifies the std level2 cost.
    type: int
  tag:
    description:
      - Specifies the isis tag.
    type: int
  weight:
    description:
      - Specifies the isis weight.
    type: int
  preference_value:
    description:
      - Specifies the preference value.
    type: int
  state:
    description:
      - Determines whether the config should be present or not on the device.
    default: present
    type: str
    choices: ['present', 'absent']
notes:
  - This module requires the netconf system service be enabled on the remote device being managed.
  - This module works with connection C(netconf).
"""

EXAMPLES = '''
  - name: Set isis description
    ce_is_is_view:
      instance_id: 3
      description: abcdeggfs
      state: present

  - name: Set isis islevel
    ce_is_is_view:
      instance_id: 3
      islevel: level_1
      state: present
  - name: Set isis coststyle
    ce_is_is_view:
      instance_id: 3
      coststyle: narrow
      state: present

  - name: Set isis stdlevel1cost
    ce_is_is_view:
      instance_id: 3
      stdlevel1cost: 63
      state: present

  - name: set isis stdlevel2cost
    ce_is_is_view:
      instance_id: 3
      stdlevel2cost: 63
      state: present

  - name: set isis stdbandwidth
    ce_is_is_view:
      instance_id: 3
      stdbandwidth: 1
      state: present
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "state": "present"
    }
existing:
    description: k/v pairs of existing configuration
    returned: always
    type: dict
    sample: {
        "session": {}
    }
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {
        "session": {
            "addrType": "IPV4",
            "createType": "SESS_STATIC",
            "destAddr": null,
            "outIfName": "10GE1/0/1",
            "sessName": "bfd_l2link",
            "srcAddr": null,
            "useDefaultIp": "true",
            "vrfName": null
        }
    }
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: [
        "bfd bfd_l2link bind peer-ip default-ip interface 10ge1/0/1"
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

CE_NC_GET_ISIS = """
    <filter type="subtree">
      <isiscomm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
      %s
      </isiscomm>
    </filter>
"""

CE_NC_GET_ISIS_INSTANCE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <description></description>
            <isLevel></isLevel>
            <costStyle></costStyle>
            <relaxSpfLimit></relaxSpfLimit>
            <stdLevel1Cost></stdLevel1Cost>
            <stdLevel2Cost></stdLevel2Cost>
            <stdbandwidth></stdbandwidth>
            <stdAutoCostEnable></stdAutoCostEnable>
            <stdAutoCostEnableCompatible></stdAutoCostEnableCompatible>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_ENTITY = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isNetEntitys>
              <isNetEntity>
                <netEntity></netEntity>
              </isNetEntity>
            </isNetEntitys>
          </isSite>
        </isSites>
"""

CE_NC_CREAT_ISIS_ENTITY = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isNetEntitys>
              <isNetEntity operation="merge">
                <netEntity>%s</netEntity>
              </isNetEntity>
            </isNetEntitys>
          </isSite>
        </isSites>
"""

CE_NC_DELATE_ISIS_ENTITY = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isNetEntitys>
              <isNetEntity operation="delete">
                <netEntity>%s</netEntity>
              </isNetEntity>
            </isNetEntitys>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_PREFERENCE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <isPreferences>
                  <isPreference>
                    <preferenceValue></preferenceValue>
                    <routePolicyName></routePolicyName>
                  </isPreference>
                </isPreferences>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MREGE_ISIS_PREFERENCE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isPreferences>
                  <isPreference operation="merge">
                  %s
                  </isPreference>
                </isPreferences>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_PREFERENCE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isPreferences>
                  <isPreference operation="delete">
                  %s
                  </isPreference>
                </isPreferences>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_MAXLOAD = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <maxLoadBalancing></maxLoadBalancing>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_MAXLOAD = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT operation="merge">
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <maxLoadBalancing>%s</maxLoadBalancing>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_MAXLOAD = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT operation="delete">
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <maxLoadBalancing>32</maxLoadBalancing>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_NEXTHOP = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isNextHopWeights>
                  <isNextHopWeight>
                    <ipAddress></ipAddress>
                    <weight></weight>
                  </isNextHopWeight>
                </isNextHopWeights>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_NEXTHOP = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isNextHopWeights>
                  <isNextHopWeight operation="merge">
                    <ipAddress>%s</ipAddress>
                    <weight>%s</weight>
                  </isNextHopWeight>
                </isNextHopWeights>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_NEXTHOP = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isNextHopWeights>
                  <isNextHopWeight operation="delete">
                    <ipAddress>%s</ipAddress>
                    <weight>1</weight>
                  </isNextHopWeight>
                </isNextHopWeights>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_LEAKROUTELEVEL2 = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isLeakRouteLevel2ToLevel1s>
                  <isLeakRouteLevel2ToLevel1>
                    <tag></tag>
                    <routePolicyName></routePolicyName>
                    <aclNumOrName></aclNumOrName>
                    <ipPrefix></ipPrefix>
                    <allowFilter></allowFilter>
                    <allowUpdown></allowUpdown>
                  </isLeakRouteLevel2ToLevel1>
                </isLeakRouteLevel2ToLevel1s>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_LEAKROUTELEVEL2 = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isLeakRouteLevel2ToLevel1s>
                  <isLeakRouteLevel2ToLevel1 operation="merge">
                   %s
                  </isLeakRouteLevel2ToLevel1>
                </isLeakRouteLevel2ToLevel1s>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_LEAKROUTELEVEL2 = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isLeakRouteLevel2ToLevel1s>
                  <isLeakRouteLevel2ToLevel1 operation="delete">
                    <tag>0</tag>
                    <routePolicyName/>
                    <aclNumOrName/>
                    <ipPrefix/>
                    <allowFilter>false</allowFilter>
                  </isLeakRouteLevel2ToLevel1>
                </isLeakRouteLevel2ToLevel1s>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_LEAKROUTELEVEL1 = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isLeakRouteLevel1ToLevel2s>
                  <isLeakRouteLevel1ToLevel2>
                    <tag></tag>
                    <routePolicyName></routePolicyName>
                    <aclNumOrName></aclNumOrName>
                    <ipPrefix></ipPrefix>
                    <leakEnableFlag></leakEnableFlag>
                    <allowFilter></allowFilter>
                  </isLeakRouteLevel1ToLevel2>
                </isLeakRouteLevel1ToLevel2s>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_LEAKROUTELEVEL1 = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isLeakRouteLevel1ToLevel2s>
                  <isLeakRouteLevel1ToLevel2 operation="merge">
                  %s
                  </isLeakRouteLevel1ToLevel2>
                </isLeakRouteLevel1ToLevel2s>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_LEAKROUTELEVEL1 = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isLeakRouteLevel1ToLevel2s>
                  <isLeakRouteLevel1ToLevel2 operation="delete">
                    <tag>0</tag>
                    <routePolicyName/>
                    <aclNumOrName/>
                    <ipPrefix/>
                    <leakEnableFlag>false</leakEnableFlag>
                    <allowFilter>false</allowFilter>
                  </isLeakRouteLevel1ToLevel2>
                </isLeakRouteLevel1ToLevel2s>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_DEFAULTROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isDefaultRoutes>
                  <isDefaultRoute>
                    <defaultMode></defaultMode>
                    <routePolicyName></routePolicyName>
                    <cost></cost>
                    <tag></tag>
                    <levelType></levelType>
                    <avoidLearning></avoidLearning>
                  </isDefaultRoute>
                </isDefaultRoutes>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_DEFAULTROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isDefaultRoutes>
                  <isDefaultRoute operation="merge">
                   %s
                  </isDefaultRoute>
                </isDefaultRoutes>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_DEFAULTROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isDefaultRoutes>
                  <isDefaultRoute operation="delete">
                    <defaultMode>always</defaultMode>
                    <cost>0</cost>
                    <tag>0</tag>
                    <levelType>level_2</levelType>
                    <avoidLearning>false</avoidLearning>
                  </isDefaultRoute>
                </isDefaultRoutes>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_IMPORTROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isImportRoutes>
                  <isImportRoute>
                    <protocol></protocol>
                    <processId></processId>
                    <costType></costType>
                    <cost></cost>
                    <tag></tag>
                    <policyType></policyType>
                    <routePolicyName></routePolicyName>
                    <levelType></levelType>
                    <inheritCost></inheritCost>
                    <permitIbgp></permitIbgp>
                  </isImportRoute>
                </isImportRoutes>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_IMPORTROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isImportRoutes>
                  <isImportRoute operation="merge">
                   %s
                  </isImportRoute>
                </isImportRoutes>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_EXPORTROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isFilterExports>
                  <isFilterExport>
                    <protocol></protocol>
                    <processId></processId>
                    <policyType></policyType>
                  </isFilterExport>
                </isFilterExports>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_EXPORTROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isFilterExports>
                  <isFilterExport operation="merge">
                  %s
                  </isFilterExport>
                </isFilterExports>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_IMPORTIPROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isFilterImports>
                  <isFilterImport>
                    <aclNumOrName></aclNumOrName>
                    <ipPrefix></ipPrefix>
                    <routePolicyName></routePolicyName>
                    <policyType></policyType>
                  </isFilterImport>
                </isFilterImports>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_IMPORTIPROUTE = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <isFilterImports>
                  <isFilterImport operation="merge">
                   %s
                  </isFilterImport>
                </isFilterImports>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_GET_ISIS_BFDLINK = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT>
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <bfdMinRx></bfdMinRx>
                <bfdMinTx></bfdMinTx>
                <bfdMultNum></bfdMultNum>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_MERGE_ISIS_BFDLINK = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT operation="merge">
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                %s
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""

CE_NC_DELETE_ISIS_BFDLINK = """
        <isSites>
          <isSite>
            <instanceId>%s</instanceId>
            <isSiteMTs>
              <isSiteMT operation="delete">
                <addressFamily>afIpv4</addressFamily>
                <mtId>0</mtId>
                <bfdMinRx>3</bfdMinRx>
                <bfdMinTx>3</bfdMinTx>
                <bfdMultNum>3</bfdMultNum>
              </isSiteMT>
            </isSiteMTs>
          </isSite>
        </isSites>
"""


def is_valid_ip_vpn(vpname):
    """check ip vpn"""

    if not vpname:
        return False

    if vpname == "_public_":
        return False

    if len(vpname) < 1 or len(vpname) > 31:
        return False

    return True


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

    # The value ranges from 224.0.0.107 to 224.0.0.250
    if not check_ip_addr(ipaddr):
        return False

    if ipaddr.count(".") != 3:
        return False

    ips = ipaddr.split(".")
    if ips[0] != "224" or ips[1] != "0" or ips[2] != "0":
        return False

    if not ips[3].isdigit() or int(ips[3]) < 107 or int(ips[3]) > 250:
        return False

    return True


def get_interface_type(interface):
    """get the type of interface, such as 10GE, ETH-TRUNK, VLANIF..."""

    if interface is None:
        return None

    if interface.upper().startswith('GE'):
        iftype = 'ge'
    elif interface.upper().startswith('10GE'):
        iftype = '10ge'
    elif interface.upper().startswith('25GE'):
        iftype = '25ge'
    elif interface.upper().startswith('4X10GE'):
        iftype = '4x10ge'
    elif interface.upper().startswith('40GE'):
        iftype = '40ge'
    elif interface.upper().startswith('100GE'):
        iftype = '100ge'
    elif interface.upper().startswith('VLANIF'):
        iftype = 'vlanif'
    elif interface.upper().startswith('LOOPBACK'):
        iftype = 'loopback'
    elif interface.upper().startswith('METH'):
        iftype = 'meth'
    elif interface.upper().startswith('ETH-TRUNK'):
        iftype = 'eth-trunk'
    elif interface.upper().startswith('VBDIF'):
        iftype = 'vbdif'
    elif interface.upper().startswith('NVE'):
        iftype = 'nve'
    elif interface.upper().startswith('TUNNEL'):
        iftype = 'tunnel'
    elif interface.upper().startswith('ETHERNET'):
        iftype = 'ethernet'
    elif interface.upper().startswith('FCOE-PORT'):
        iftype = 'fcoe-port'
    elif interface.upper().startswith('FABRIC-PORT'):
        iftype = 'fabric-port'
    elif interface.upper().startswith('STACK-PORT'):
        iftype = 'stack-port'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None

    return iftype.lower()


class ISIS_View(object):
    """Manages ISIS Instance"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.instance_id = self.module.params['instance_id']
        self.description = self.module.params['description']
        self.islevel = self.module.params['islevel']
        self.coststyle = self.module.params['coststyle']
        self.relaxspfLimit = self.module.params['relaxspfLimit']
        self.stdlevel1cost = self.module.params['stdlevel1cost']
        self.stdlevel2cost = self.module.params['stdlevel2cost']
        self.stdbandwidth = self.module.params['stdbandwidth']
        self.autocostenable = self.module.params['autocostenable']
        self.autocostenablecompatible = self.module.params['autocostenablecompatible']
        self.netentity = self.module.params['netentity']
        self.preference_value = self.module.params['preference_value']
        self.route_policy_name = self.module.params['route_policy_name']
        self.max_load = self.module.params['max_load']
        self.ip_address = self.module.params['ip_address']
        self.weight = self.module.params['weight']
        self.aclnum_or_name = self.module.params['aclnum_or_name']
        self.ip_prefix_name = self.module.params['ip_prefix_name']
        self.import_routepolicy_name = self.module.params['import_routepolicy_name']
        self.tag = self.module.params['tag']
        self.allow_filter = self.module.params['allow_filter']
        self.allow_up_down = self.module.params['allow_up_down']
        self.penetration_direct = self.module.params['penetration_direct']
        self.enablelevel1tolevel2 = self.module.params['enablelevel1tolevel2']
        self.defaultmode = self.module.params['defaultmode']
        self.mode_routepolicyname = self.module.params['mode_routepolicyname']
        self.cost = self.module.params['cost']
        self.mode_tag = self.module.params['mode_tag']
        self.level_type = self.module.params['level_type']
        self.avoid_learning = self.module.params['avoid_learning']
        self.protocol = self.module.params['protocol']
        self.processid = self.module.params['processid']
        self.cost_type = self.module.params['cost_type']
        self.import_cost = self.module.params['import_cost']
        self.import_tag = self.module.params['import_tag']
        self.impotr_leveltype = self.module.params['impotr_leveltype']
        self.import_route_policy = self.module.params['import_route_policy']
        self.inheritcost = self.module.params['inheritcost']
        self.permitibgp = self.module.params['permitibgp']
        self.avoid_learning = self.module.params['avoid_learning']
        self.export_protocol = self.module.params['export_protocol']
        self.export_policytype = self.module.params['export_policytype']
        self.export_processid = self.module.params['export_processid']
        self.export_aclnumorname = self.module.params['export_aclnumorname']
        self.export_ipprefix = self.module.params['export_ipprefix']
        self.export_routepolicyname = self.module.params['export_routepolicyname']
        self.import_aclnumorname = self.module.params['import_aclnumorname']
        self.import_ipprefix = self.module.params['import_ipprefix']
        self.import_routepolicyname = self.module.params['import_routepolicyname']
        self.bfd_min_rx = self.module.params['bfd_min_rx']
        self.bfd_min_tx = self.module.params['bfd_min_tx']
        self.bfd_multiplier_num = self.module.params['bfd_multiplier_num']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.isis_dict = dict()
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """init module"""

        mutually_exclusive = [["stdlevel1cost", "stdlevel2cost"],
                              ["aclnum_or_name", "ip_prefix_name", "import_routepolicy_name"],
                              ["export_aclnumorname", "import_ipprefix", "import_routepolicyname"]]
        required_together = [('ip_address', 'weight')]
        self.module = AnsibleModule(
            argument_spec=self.spec,
            mutually_exclusive=mutually_exclusive,
            required_together=required_together,
            supports_check_mode=True)

    def get_isis_dict(self):
        """bfd config dict"""

        isis_dict = dict()
        isis_dict["instance"] = dict()
        conf_str = CE_NC_GET_ISIS % (
            (CE_NC_GET_ISIS_INSTANCE % self.instance_id))

        if self.netentity:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_ENTITY % self.instance_id))

        if self.route_policy_name or self.preference_value:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_PREFERENCE % self.instance_id))
        if self.max_load:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_MAXLOAD % self.instance_id))
        if self.ip_address:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_NEXTHOP % self.instance_id))
        if self.penetration_direct and self.penetration_direct == "level2-level1":
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_LEAKROUTELEVEL2 % self.instance_id))
        elif self.penetration_direct and self.penetration_direct == "level1-level2":
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_LEAKROUTELEVEL1 % self.instance_id))
        elif self.defaultmode:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_DEFAULTROUTE % self.instance_id))
        elif self.protocol:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_IMPORTROUTE % self.instance_id))
        elif self.export_protocol:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_EXPORTROUTE % self.instance_id))
        elif self.bfd_min_rx or self.bfd_min_tx or self.bfd_multiplier_num:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_BFDLINK % self.instance_id))
        elif self.import_aclnumorname or self.import_ipprefix or self.import_ipprefix:
            conf_str = CE_NC_GET_ISIS % (
                (CE_NC_GET_ISIS_IMPORTIPROUTE % self.instance_id))
        xml_str = get_nc_config(self.module, conf_str)

        if "<data/>" in xml_str:
            return isis_dict

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)

        # get bfd global info
        if self.netentity:
            glb = root.find("isiscomm/isSites/isSite/isNetEntitys/isNetEntity")
        elif self.route_policy_name or self.preference_value:
            glb = root.find("isiscomm/isSites/isSite//isSiteMTs/isSiteMT/isPreferences/isPreference")
        elif self.max_load:
            glb = root.find("isiscomm/isSites/isSite/isSiteMTs/isSiteMT")
        elif self.ip_address:
            glb = root.find("isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isNextHopWeights/isNextHopWeight")
        elif self.penetration_direct and self.penetration_direct == "level2-level1":
            glb = root.find("isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isLeakRouteLevel2ToLevel1s/isLeakRouteLevel2ToLevel1")
        elif self.penetration_direct and self.penetration_direct == "level1-level2":
            glb = root.find(
                "isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isLeakRouteLevel1ToLevel2s/isLeakRouteLevel1ToLevel2")
        elif self.defaultmode:
            glb = root.find(
                "isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isDefaultRoutes/isDefaultRoute")
        elif self.protocol:
            glb = root.find(
                "isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isImportRoutes/isImportRoute")
        elif self.export_protocol:
            glb = root.find(
                "isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isFilterExports/isFilterExport")
        elif self.bfd_min_rx or self.bfd_min_tx or self.bfd_multiplier_num:
            glb = root.find(
                "isiscomm/isSites/isSite/isSiteMTs/isSiteMT")
        elif self.import_aclnumorname or self.import_ipprefix or self.import_ipprefix:
            glb = root.find(
                "isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isFilterImports/isFilterImport")
        else:
            glb = root.find("isiscomm/isSites/isSite")

        if glb is not None:
            for attr in glb:
                isis_dict["instance"][attr.tag] = attr.text

        return isis_dict

    def config_session(self):
        """configures bfd session"""

        xml_str = ""
        instance = self.isis_dict["instance"]
        if not self.instance_id:
            return xml_str
        xml_str = "<instanceId>%s</instanceId>" % self.instance_id
        self.updates_cmd.append("isis %s" % self.instance_id)
        cmd_list = list()

        if self.state == "present":
            if self.description and self.description != instance.get("description"):
                xml_str += "<description>%s</description>" % self.description
                self.updates_cmd.append("description %s" % self.description)

            if self.islevel and self.islevel != instance.get("isLevel"):
                xml_str += "<isLevel>%s</isLevel>" % self.islevel
                self.updates_cmd.append("is-level %s" % self.islevel)

            if self.coststyle:
                if self.coststyle != instance.get("costStyle"):
                    xml_str += "<costStyle>%s</costStyle>" % self.coststyle
                    self.updates_cmd.append("cost-style %s" % self.coststyle)
                if self.relaxspfLimit and instance.get("relaxSpfLimit", "false") == "false":
                    xml_str += "<relaxSpfLimit>true</relaxSpfLimit>"
                    self.updates_cmd.append("cost-style %s relax-spf-limit" % self.coststyle)
                elif not self.relaxspfLimit and instance.get("relaxSpfLimit", "false") == "true":
                    xml_str += "<relaxSpfLimit>false</relaxSpfLimit>"
                    self.updates_cmd.append("cost-style %s" % self.coststyle)

            if self.stdlevel1cost and str(self.stdlevel1cost) != instance.get("stdLevel1Cost"):
                xml_str += "<stdLevel1Cost>%s</stdLevel1Cost>" % self.stdlevel1cost
                self.updates_cmd.append("circuit-cost %s level-1" % self.stdlevel1cost)

            if self.stdlevel2cost and str(self.stdlevel2cost) != instance.get("stdLevel2Cost"):
                xml_str += "<stdLevel2Cost>%s</stdLevel2Cost>" % self.stdlevel2cost
                self.updates_cmd.append("circuit-cost %s level-2" % self.stdlevel2cost)

            if self.stdbandwidth and str(self.stdbandwidth) != instance.get("stdbandwidth"):
                xml_str += "<stdbandwidth>%s</stdbandwidth>" % self.stdbandwidth
                self.updates_cmd.append("bandwidth-reference %s" % self.stdbandwidth)

            if self.netentity and self.netentity != instance.get("netEntity"):
                xml_str = CE_NC_CREAT_ISIS_ENTITY % (self.instance_id, self.netentity)
                self.updates_cmd.append("network-entity %s" % self.netentity)

            if self.preference_value or self.route_policy_name:
                xml_str = ""
                cmd_session = "preference"
                if self.preference_value and str(self.preference_value) != instance.get("preferenceValue"):
                    xml_str = "<preferenceValue>%s</preferenceValue>" % self.preference_value
                    cmd_session += " %s" % self.preference_value
                if self.route_policy_name and self.route_policy_name != instance.get("routePolicyName"):
                    xml_str += "<routePolicyName>%s</routePolicyName>" % self.route_policy_name
                    cmd_session += " route-policy %s" % self.route_policy_name
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)
                xml_str = CE_NC_MREGE_ISIS_PREFERENCE % (self.instance_id, xml_str)

            if self.max_load and str(self.max_load) != instance.get("maxLoadBalancing"):
                xml_str = CE_NC_MERGE_ISIS_MAXLOAD % (self.instance_id, self.max_load)
                self.updates_cmd.append("maximum load-balancing %s" % self.max_load)

            if self.ip_address:
                xml_str = CE_NC_MERGE_ISIS_NEXTHOP % (self.instance_id, self.ip_address, self.weight)
                self.updates_cmd.append("nexthop %s weight %s" % (self.ip_address, self.weight))

            if self.penetration_direct:
                xml_str = ""
                if self.penetration_direct == "level2-level1":
                    cmd_session = "import-route isis level-2 into level-1"
                elif self.penetration_direct == "level1-level2":
                    cmd_session = "import-route isis level-1 into level-2"
                if self.aclnum_or_name:
                    xml_str = "<aclNumOrName>%s</aclNumOrName>" % self.aclnum_or_name
                    xml_str += "<policyType>aclNumOrName</policyType>"
                    if isinstance(self.aclnum_or_name, int):
                        cmd_session += " filter-policy %s" % self.aclnum_or_name
                    elif isinstance(self.aclnum_or_name, str):
                        cmd_session += " filter-policy acl-name %s" % self.aclnum_or_name
                if self.ip_prefix_name:
                    xml_str = "<ipPrefix>%s</ipPrefix>" % self.ip_prefix_name
                    xml_str += "<policyType>ipPrefix</policyType>"
                    cmd_session += " filter-policy ip-prefix %s" % self.ip_prefix_name
                if self.import_routepolicy_name:
                    xml_str = "<routePolicyName>%s</routePolicyName>" % self.import_routepolicy_name
                    xml_str += "<policyType>routePolicy</policyType>"
                    cmd_session += " filter-policy route-policy %s" % self.import_routepolicy_name
                if self.tag:
                    xml_str += "<tag>%s</tag>" % self.tag
                    cmd_session += " tag %s" % self.tag
                if self.allow_filter or self.allow_up_down:
                    cmd_session += " direct"
                    if self.allow_filter:
                        xml_str += "<allowFilter>true</allowFilter>"
                        cmd_session += " allow-filter-policy"
                    if self.allow_up_down:
                        xml_str += "<allowUpdown>true</allowUpdown>"
                        cmd_session += " allow-up-down-bit"
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)
                if self.enablelevel1tolevel2:
                    xml_str += "<leakEnableFlag>true</leakEnableFlag>"
                    self.updates_cmd.append("undo import-route isis level-1 into level-2 disable")

            if self.defaultmode:
                cmd_session = "default-route-advertise"
                if self.defaultmode == "always":
                    xml_str = "<defaultMode>always</defaultMode>"
                    cmd_session += " always"
                elif self.defaultmode == "matchDefault":
                    xml_str = "<defaultMode>matchDefault</defaultMode>"
                    cmd_session += " match default"
                elif self.defaultmode == "matchAny":
                    xml_str = "<defaultMode>matchAny</defaultMode>"
                    xml_str += "<policyType>routePolicy</policyType>"
                    xml_str += "<routePolicyName>%s</routePolicyName>" % self.mode_routepolicyname
                    cmd_session += " route-policy %s" % self.mode_routepolicyname
                if self.cost is not None:
                    xml_str += "<cost>%s</cost>" % self.cost
                    cmd_session += " cost %s" % self.cost
                if self.mode_tag:
                    xml_str += "<tag>%s</tag>" % self.mode_tag
                    cmd_session += " tag %s" % self.mode_tag
                if self.level_type:
                    if self.level_type == "level_1":
                        xml_str += "<levelType>level_1</levelType>"
                        cmd_session += " level-1"
                    elif self.level_type == "level_2":
                        xml_str += "<levelType>level_2</levelType>"
                        cmd_session += " level-2"
                    elif self.level_type == "level_1_2":
                        xml_str += "<levelType>level_1_2</levelType>"
                        cmd_session += " level-1-2"
                if self.avoid_learning:
                    xml_str += "<avoidLearning>true</avoidLearning>"
                    cmd_session += " avoid-learning"
                elif not self.avoid_learning:
                    xml_str += "<avoidLearning>false</avoidLearning>"
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)

            if self.protocol:
                cmd_session = "import-route"
                if self.protocol == "rip":
                    xml_str = "<protocol>rip</protocol>"
                    cmd_session += " rip"
                elif self.protocol == "isis":
                    xml_str = "<protocol>isis</protocol>"
                    cmd_session += " isis"
                elif self.protocol == "ospf":
                    xml_str = "<protocol>ospf</protocol>"
                    cmd_session += " ospf"
                elif self.protocol == "static":
                    xml_str = "<protocol>static</protocol>"
                    cmd_session += " static"
                elif self.protocol == "direct":
                    xml_str = "<protocol>direct</protocol>"
                    cmd_session += " direct"
                elif self.protocol == "bgp":
                    xml_str = "<protocol>bgp</protocol>"
                    cmd_session += " bgp"
                    if self.permitibgp:
                        xml_str += "<permitIbgp>true</permitIbgp>"
                        cmd_session += " permit-ibgp"
                if self.protocol == "rip" or self.protocol == "isis" or self.protocol == "ospf":
                    xml_str += "<processId>%s</processId>" % self.processid
                    cmd_session += " %s" % self.processid
                if self.inheritcost:
                    xml_str += "<inheritCost>%s</inheritCost>" % self.inheritcost
                    cmd_session += " inherit-cost"
                if self.cost_type:
                    if self.cost_type == "external":
                        xml_str += "<costType>external</costType>"
                        cmd_session += " cost-type external"
                    elif self.cost_type == "internal":
                        xml_str += "<costType>internal</costType>"
                        cmd_session += " cost-type internal"
                if self.import_cost:
                    xml_str += "<cost>%s</cost>" % self.import_cost
                    cmd_session += " cost %s" % self.import_cost
                if self.import_tag:
                    xml_str += "<tag>%s</tag>" % self.import_tag
                    cmd_session += " tag %s" % self.import_tag
                if self.import_route_policy:
                    xml_str += "<policyType>routePolicy</policyType>"
                    xml_str += "<routePolicyName>%s</routePolicyName>" % self.import_route_policy
                    cmd_session += " route-policy %s" % self.import_route_policy
                if self.impotr_leveltype:
                    if self.impotr_leveltype == "level_1":
                        cmd_session += " level-1"
                    elif self.impotr_leveltype == "level_2":
                        cmd_session += " level-2"
                    elif self.impotr_leveltype == "level_1_2":
                        cmd_session += " level-1-2"
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)

            if self.bfd_min_rx or self.bfd_min_tx or self.bfd_multiplier_num:
                xml_str = ""
                self.updates_cmd.append("bfd all-interfaces enable")
                cmd_session = "bfd all-interfaces"
                if self.bfd_min_rx:
                    xml_str += "<bfdMinRx>%s</bfdMinRx>" % self.bfd_min_rx
                    cmd_session += " min-rx-interval %s" % self.bfd_min_rx
                if self.bfd_min_tx:
                    xml_str += "<bfdMinTx>%s</bfdMinTx>" % self.bfd_min_tx
                    cmd_session += " min-tx-interval %s" % self.bfd_min_tx
                if self.bfd_multiplier_num:
                    xml_str += "<bfdMultNum>%s</bfdMultNum>" % self.bfd_multiplier_num
                    cmd_session += " detect-multiplier %s" % self.bfd_multiplier_num
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)

            if self.export_protocol:
                cmd_session = "filter-policy"
                if self.export_aclnumorname:
                    xml_str = "<policyType>aclNumOrName</policyType>"
                    xml_str += "<aclNumOrName>%s</aclNumOrName>" % self.export_aclnumorname
                    if isinstance(self.export_aclnumorname, int):
                        cmd_session += " %s" % self.export_aclnumorname
                    elif isinstance(self.export_aclnumorname, str):
                        cmd_session += " acl-name %s" % self.export_aclnumorname
                if self.export_ipprefix:
                    xml_str = "<policyType>ipPrefix</policyType>"
                    xml_str += "<ipPrefix>%s</ipPrefix>" % self.export_ipprefix
                    cmd_session += " ip-prefix %s" % self.export_ipprefix
                if self.export_routepolicyname:
                    xml_str = "<policyType>routePolicy</policyType>"
                    xml_str += "<routePolicyName>%s</routePolicyName>" % self.export_routepolicyname
                    cmd_session += " route-policy %s" % self.export_routepolicyname
                xml_str += "<protocol>%s</protocol>" % self.export_protocol
                cmd_session += " export %s" % self.export_protocol
                if self.export_processid is not None:
                    xml_str += "<processId>%s</processId>" % self.export_processid
                    cmd_session += " %s" % self.export_processid
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)

            if self.import_ipprefix or self.import_aclnumorname or self.import_routepolicyname:
                cmd_session = "filter-policy"
                if self.import_aclnumorname:
                    xml_str = "<policyType>aclNumOrName</policyType>"
                    xml_str += "<aclNumOrName>%s</aclNumOrName>" % self.import_aclnumorname
                    if isinstance(self.import_aclnumorname, int):
                        cmd_session += " %s" % self.import_aclnumorname
                    elif isinstance(self.import_aclnumorname, str):
                        cmd_session += " acl-name %s" % self.import_aclnumorname
                if self.import_ipprefix:
                    xml_str = "<policyType>ipPrefix</policyType>"
                    xml_str += "<ipPrefix>%s</ipPrefix>" % self.import_ipprefix
                    cmd_session += " ip-prefix %s" % self.import_ipprefix
                if self.import_routepolicyname:
                    xml_str = "<policyType>routePolicy</policyType>"
                    xml_str += "<routePolicyName>%s</routePolicyName>" % self.import_routepolicyname
                    cmd_session += " route-policy %s" % self.import_routepolicyname
                cmd_session += "import"
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)
        else:
            # absent
            if self.description and self.description == instance.get("description"):
                xml_str += "<description>%s</description>" % self.description
                self.updates_cmd.append("undo description")

            if self.islevel and self.islevel == instance.get("isLevel"):
                xml_str += "<isLevel>level_1_2</isLevel>"
                self.updates_cmd.append("undo is-level")

            if self.coststyle and self.coststyle == instance.get("costStyle"):
                xml_str += "<costStyle>%s</costStyle>" % ("narrow")
                xml_str += "<relaxSpfLimit>false</relaxSpfLimit>"
                self.updates_cmd.append("undo cost-style")

            if self.stdlevel1cost and str(self.stdlevel1cost) == instance.get("stdLevel1Cost"):
                xml_str += "<stdLevel1Cost>%s</stdLevel1Cost>" % self.stdlevel1cost
                self.updates_cmd.append("undo circuit-cost %s level-1" % self.stdlevel1cost)

            if self.stdlevel2cost and str(self.stdlevel2cost) == instance.get("stdLevel2Cost"):
                xml_str += "<stdLevel2Cost>%s</stdLevel2Cost>" % self.stdlevel2cost
                self.updates_cmd.append("undo circuit-cost %s level-2" % self.stdlevel2cost)

            if self.stdbandwidth and str(self.stdbandwidth) == instance.get("stdbandwidth"):
                xml_str += "<stdbandwidth>100</stdbandwidth>"
                self.updates_cmd.append("undo bandwidth-reference")

            if self.netentity and self.netentity == instance.get("netEntity"):
                xml_str = CE_NC_DELATE_ISIS_ENTITY % (self.instance_id, self.netentity)
                self.updates_cmd.append("undo network-entity %s" % self.netentity)

            if self.preference_value or self.route_policy_name:
                xml_str = ""
                if self.preference_value and str(self.preference_value) == instance.get("preferenceValue"):
                    xml_str = "<preferenceValue>%s</preferenceValue>" % self.preference_value
                    if self.route_policy_name and self.route_policy_name == instance.get("routePolicyName"):
                        xml_str += "<routePolicyName>%s</routePolicyName>" % self.route_policy_name
                    self.updates_cmd.append("undo preference")
                elif not self.preference_value and self.route_policy_name and self.route_policy_name == instance.get("routePolicyName"):
                    xml_str = "<routePolicyName>%s</routePolicyName>" % self.route_policy_name
                    self.updates_cmd.append("undo preference")
                xml_str = CE_NC_DELETE_ISIS_PREFERENCE % (self.instance_id, xml_str)

            if self.max_load and str(self.max_load) == instance.get("maxLoadBalancing"):
                xml_str = CE_NC_DELETE_ISIS_MAXLOAD % self.instance_id
                self.updates_cmd.append("undo maximum load-balancing")

            if self.ip_address:
                xml_str = CE_NC_DELETE_ISIS_NEXTHOP % (self.instance_id, self.ip_address)
                self.updates_cmd.append("undo nexthop %s" % self.ip_address)

            if self.penetration_direct:
                if self.penetration_direct == "level2-level1":
                    self.updates_cmd.append("undo import-route isis level-2 into level-1")
                elif self.penetration_direct == "level1-level2":
                    self.updates_cmd.append("undo import-route isis level-1 into level-2")
                    self.updates_cmd.append("import-route isis level-1 into level-2 disable")

            if self.bfd_min_rx or self.bfd_min_tx or self.bfd_multiplier_num is not None:
                xml_str = CE_NC_DELETE_ISIS_BFDLINK % self.instance_id
                self.updates_cmd.append("undo bfd all-interfaces enable")
                cmd_session = "undo bfd all-interfaces"
                if self.bfd_min_rx:
                    cmd_session += " min-rx-interval %s" % self.bfd_min_rx
                if self.bfd_min_tx:
                    cmd_session += " min-tx-interval %s" % self.bfd_min_tx
                if self.bfd_multiplier_num:
                    cmd_session += " detect-multiplier %s" % self.bfd_multiplier_num
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)

            if self.defaultmode:
                xml_str = CE_NC_DELETE_ISIS_DEFAULTROUTE % self.instance_id
                self.updates_cmd.append("undo default-route-advertise")

            if self.protocol:
                if self.protocol == "rip" or self.protocol == "isis" or self.protocol == "ospf":
                    self.updates_cmd.append("undo import-route %s %s" % (self.protocol, self.processid))
                else:
                    self.updates_cmd.append("undo import-route %s" % self.protocol)

            if self.export_protocol:
                cmd_session = "undo filter-policy"
                if self.export_aclnumorname:
                    if isinstance(self.export_aclnumorname, int):
                        cmd_session += " %s" % self.export_aclnumorname
                    elif isinstance(self.export_aclnumorname, str):
                        cmd_session += " acl-name %s" % self.export_aclnumorname
                if self.export_ipprefix:
                    cmd_session += " ip-prefix %s" % self.export_ipprefix
                if self.export_routepolicyname:
                    cmd_session += " route-policy %s" % self.export_routepolicyname
                cmd_session += " export %s" % self.export_protocol
                if self.export_processid is not None:
                    cmd_session += " %s" % self.export_processid
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)
            if self.import_ipprefix or self.import_aclnumorname or self.import_routepolicyname:
                cmd_session = "undo filter-policy"
                if self.import_aclnumorname:
                    if isinstance(self.import_aclnumorname, int):
                        cmd_session += " %s" % self.import_aclnumorname
                    elif isinstance(self.import_aclnumorname, str):
                        cmd_session += " acl-name %s" % self.import_aclnumorname
                if self.import_ipprefix:
                    cmd_session += " ip-prefix %s" % self.import_ipprefix
                if self.import_routepolicyname:
                    cmd_session += " route-policy %s" % self.import_routepolicyname
                cmd_session += " import"
                cmd_list.insert(0, cmd_session)
                self.updates_cmd.extend(cmd_list)

        if self.autocostenable and instance.get("stdAutoCostEnable", "false") == "false":
            xml_str += "<stdAutoCostEnable>true</stdAutoCostEnable>"
            self.updates_cmd.append("auto-cost enable")
        elif not self.autocostenable and instance.get("stdAutoCostEnable", "false") == "true":
            xml_str += "<stdAutoCostEnable>false</stdAutoCostEnable>"
            xml_str += "<stdAutoCostEnableCompatible>false</stdAutoCostEnableCompatible>"
            self.updates_cmd.append("undo auto-cost enable")

        if self.autocostenable:
            if self.autocostenablecompatible and instance.get("stdAutoCostEnableCompatible", "false") == "false":
                xml_str += "<stdAutoCostEnableCompatible>true</stdAutoCostEnableCompatible>"
                self.updates_cmd.append("auto-cost enable compatible")
            elif not self.autocostenablecompatible and instance.get("stdAutoCostEnableCompatible", "false") == "true":
                xml_str += "<stdAutoCostEnableCompatible>false</stdAutoCostEnableCompatible>"
                self.updates_cmd.append("auto-cost enable")

        if self.state == "present":
            if self.netentity or self.preference_value or self.route_policy_name or self.max_load or self.ip_address:
                return xml_str
            elif self.penetration_direct:
                if self.penetration_direct == "level2-level1":
                    return CE_NC_MERGE_ISIS_LEAKROUTELEVEL2 % (self.instance_id, xml_str)
                elif self.penetration_direct == "level1-level2":
                    return CE_NC_MERGE_ISIS_LEAKROUTELEVEL1 % (self.instance_id, xml_str)
            elif self.defaultmode:
                return CE_NC_MERGE_ISIS_DEFAULTROUTE % (self.instance_id, xml_str)
            elif self.protocol:
                return CE_NC_MERGE_ISIS_IMPORTROUTE % (self.instance_id, xml_str)
            elif self.export_protocol:
                return CE_NC_MERGE_ISIS_EXPORTROUTE % (self.instance_id, xml_str)
            elif self.import_routepolicyname or self.import_aclnumorname or self.import_ipprefix:
                return CE_NC_MERGE_ISIS_IMPORTIPROUTE % (self.instance_id, xml_str)
            elif self.bfd_min_rx or self.bfd_min_tx or self.bfd_multiplier_num:
                return CE_NC_MERGE_ISIS_BFDLINK % (self.instance_id, xml_str)
            else:
                return '<isSites><isSite operation="merge">' + xml_str + '</isSite></isSites>'
        else:
            if self.netentity or self.preference_value or self.route_policy_name or self.max_load \
                    or self.ip_address or self.defaultmode or self.bfd_min_rx or self.bfd_min_tx or self.bfd_multiplier_num is not None:
                return xml_str
            else:
                return '<isSites><isSite operation="delete">' + xml_str + '</isSite></isSites>'

    def netconf_load_config(self, xml_str):
        """load bfd config by netconf"""

        if not xml_str:
            return
        if xml_str == "<instanceId>%s</instanceId>" % self.instance_id:
            pass
        else:
            xml_cfg = """
                <config>
                <isiscomm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
                %s
                </isiscomm>
                </config>""" % xml_str
            set_nc_config(self.module, xml_cfg)
            self.changed = True

    def check_params(self):
        """Check all input params"""
        levelcost = 16777215
        if not self.instance_id:
            self.module.fail_json(msg="Error: Missing required arguments: instance_id.")

        if self.instance_id:
            if self.instance_id < 1 or self.instance_id > 4294967295:
                self.module.fail_json(msg="Error: Instance id is not ranges from 1 to 4294967295.")

        # check description
        if self.description:
            if len(self.description) < 1 or len(self.description) > 80:
                self.module.fail_json(msg="Error: description is invalid.")

        #
        if self.stdbandwidth:
            if self.stdbandwidth < 1 or self.stdbandwidth > 2147483648:
                self.module.fail_json(msg="Error: stdbandwidth is not ranges from 1 to 2147483648.")

        if self.relaxspfLimit is not None and not self.coststyle:
            self.module.fail_json(msg="Error: relaxspfLimit must set after coststyle.")

        if self.coststyle:
            if self.coststyle != "wide" and self.coststyle != "wtransition":
                levelcost = 63
            else:
                levelcost = 16777215
        if self.stdlevel1cost:
            if self.stdlevel1cost < 1 or self.stdlevel1cost > levelcost:
                self.module.fail_json(msg="Error: stdlevel1cost is not ranges from 1 to %s." % levelcost)

        if self.stdlevel2cost:
            if self.stdlevel2cost < 1 or self.stdlevel2cost > levelcost:
                self.module.fail_json(msg="Error: stdlevel2cost is not ranges from 1 to %s." % levelcost)

        if self.coststyle:
            if self.coststyle != "ntransition" and self.coststyle != "transition":
                if self.relaxspfLimit:
                    self.module.fail_json(msg="Error: relaxspfLimit can not be set while the coststyle is not ntransition or transition")

        if self.autocostenablecompatible:
            if not self.autocostenable:
                self.module.fail_json(msg="Error: you shoule enable the autocostenable first.")

        if self.preference_value:
            if self.preference_value < 1 or self.preference_value > 255:
                self.module.fail_json(msg="Error: preference_value is not ranges from 1 to 255.")

        if self.route_policy_name:
            if len(self.route_policy_name) < 1 or len(self.route_policy_name) > 200:
                self.module.fail_json(msg="Error: route_policy_name is invalid.")

        if self.max_load:
            if self.max_load < 1 or self.max_load > 32:
                self.module.fail_json(msg="Error: max_load is not ranges from 1 to 32.")

        if self.weight:
            if self.weight < 1 or self.weight > 254:
                self.module.fail_json(msg="Error: weight is not ranges from 1 to 254.")

        if self.aclnum_or_name:
            if isinstance(self.aclnum_or_name, int):
                if self.aclnum_or_name < 2000 or self.aclnum_or_name > 2999:
                    self.module.fail_json(msg="Error: acl_num is not ranges from 2000 to 2999.")
            elif isinstance(self.aclnum_or_name, str):
                if len(self.aclnum_or_name) < 1 or len(self.aclnum_or_name) > 32:
                    self.module.fail_json(msg="Error: acl_name is invalid.")
        if self.ip_prefix_name:
            if len(self.ip_prefix_name) < 1 or len(self.ip_prefix_name) > 169:
                self.module.fail_json(msg="Error: ip_prefix_name is invalid.")
        if self.import_routepolicy_name:
            if len(self.import_routepolicy_name) < 1 or len(self.import_routepolicy_name) > 200:
                self.module.fail_json(msg="Error: import_routepolicy_name is invalid.")
        if self.tag:
            if self.tag < 1 or self.tag > 4294967295:
                self.module.fail_json(msg="Error: tag is not ranges from 1 to 4294967295.")

        if self.mode_routepolicyname:
            if len(self.mode_routepolicyname) < 1 or len(self.mode_routepolicyname) > 200:
                self.module.fail_json(msg="Error: mode_routepolicyname is invalid.")
        if self.cost is not None:
            if self.cost < 0 or self.cost > 4261412864:
                self.module.fail_json(msg="Error: cost is not ranges from 0 to 4261412864.")
        if self.mode_tag:
            if self.mode_tag < 1 or self.mode_tag > 4294967295:
                self.module.fail_json(msg="Error: mode_tag is not ranges from 1 to 4294967295.")

        if self.processid is not None:
            if self.processid < 0 or self.processid > 4294967295:
                self.module.fail_json(msg="Error: processid is not ranges from 0 to 4294967295.")

        if self.import_cost is not None:
            if self.import_cost < 0 or self.import_cost > 4261412864:
                self.module.fail_json(msg="Error: import_cost is not ranges from 0 to 4261412864.")

        if self.import_tag:
            if self.import_tag < 1 or self.import_tag > 4294967295:
                self.module.fail_json(msg="Error: import_tag is not ranges from 1 to 4294967295.")

        if self.export_aclnumorname:
            if isinstance(self.export_aclnumorname, int):
                if self.export_aclnumorname < 2000 or self.export_aclnumorname > 2999:
                    self.module.fail_json(msg="Error: acl_num is not ranges from 2000 to 2999.")
            elif isinstance(self.export_aclnumorname, str):
                if len(self.export_aclnumorname) < 1 or len(self.export_aclnumorname) > 32:
                    self.module.fail_json(msg="Error: acl_name is invalid.")

        if self.export_processid:
            if self.export_processid < 1 or self.export_processid > 4294967295:
                self.module.fail_json(msg="Error: export_processid is not ranges from 1 to 4294967295.")

        if self.export_ipprefix:
            if len(self.export_ipprefix) < 1 or len(self.export_ipprefix) > 169:
                self.module.fail_json(msg="Error: export_ipprefix is invalid.")

        if self.export_routepolicyname:
            if len(self.export_routepolicyname) < 1 or len(self.export_routepolicyname) > 200:
                self.module.fail_json(msg="Error: export_routepolicyname is invalid.")

        if self.bfd_min_rx:
            if self.bfd_min_rx < 50 or self.bfd_min_rx > 1000:
                self.module.fail_json(msg="Error: bfd_min_rx is not ranges from 50 to 1000.")

        if self.bfd_min_tx:
            if self.bfd_min_tx < 50 or self.bfd_min_tx > 1000:
                self.module.fail_json(msg="Error: bfd_min_tx is not ranges from 50 to 1000.")

        if self.bfd_multiplier_num:
            if self.bfd_multiplier_num < 3 or self.bfd_multiplier_num > 50:
                self.module.fail_json(msg="Error: bfd_multiplier_num is not ranges from 3 to 50.")

        if self.import_routepolicyname:
            if len(self.import_routepolicyname) < 1 or len(self.import_routepolicyname) > 200:
                self.module.fail_json(msg="Error: import_routepolicyname is invalid.")

        if self.import_aclnumorname:
            if isinstance(self.import_aclnumorname, int):
                if self.import_aclnumorname < 2000 or self.import_aclnumorname > 2999:
                    self.module.fail_json(msg="Error: acl_num is not ranges from 2000 to 2999.")
            elif isinstance(self.import_aclnumorname, str):
                if len(self.import_aclnumorname) < 1 or len(self.import_aclnumorname) > 32:
                    self.module.fail_json(msg="Error: acl_name is invalid.")

    def get_proposed(self):
        """get proposed info"""
        # base config
        self.proposed["instance_id"] = self.instance_id
        self.proposed["description"] = self.description
        self.proposed["islevel"] = self.islevel
        self.proposed["coststyle"] = self.coststyle
        self.proposed["relaxspfLimit"] = self.relaxspfLimit
        self.proposed["stdlevel1cost"] = self.stdlevel1cost
        self.proposed["stdlevel2cost"] = self.stdlevel2cost
        self.proposed["stdbandwidth"] = self.stdbandwidth
        self.proposed["autocostenable"] = self.autocostenable
        self.proposed["autocostenablecompatible"] = self.autocostenablecompatible
        self.proposed["netentity"] = self.netentity
        self.proposed["preference_value"] = self.preference_value
        self.proposed["route_policy_name"] = self.route_policy_name
        self.proposed["max_load"] = self.max_load
        self.proposed["ip_address"] = self.ip_address
        self.proposed["weight"] = self.weight
        self.proposed["penetration_direct"] = self.penetration_direct
        self.proposed["aclnum_or_name"] = self.aclnum_or_name
        self.proposed["ip_prefix_name"] = self.ip_prefix_name
        self.proposed["import_routepolicy_name"] = self.import_routepolicy_name
        self.proposed["tag"] = self.tag
        self.proposed["allow_filter"] = self.allow_filter
        self.proposed["allow_up_down"] = self.allow_up_down
        self.proposed["enablelevel1tolevel2"] = self.enablelevel1tolevel2
        self.proposed["protocol"] = self.protocol
        self.proposed["processid"] = self.processid
        self.proposed["cost_type"] = self.cost_type
        self.proposed["import_cost"] = self.import_cost
        self.proposed["import_tag"] = self.import_tag
        self.proposed["import_route_policy"] = self.import_route_policy
        self.proposed["impotr_leveltype"] = self.impotr_leveltype
        self.proposed["inheritcost"] = self.inheritcost
        self.proposed["permitibgp"] = self.permitibgp
        self.proposed["export_protocol"] = self.export_protocol
        self.proposed["export_policytype"] = self.export_policytype
        self.proposed["export_processid"] = self.export_processid
        self.proposed["export_aclnumorname"] = self.export_aclnumorname
        self.proposed["export_ipprefix"] = self.export_ipprefix
        self.proposed["export_routepolicyname"] = self.export_routepolicyname
        self.proposed["import_aclnumorname"] = self.import_aclnumorname
        self.proposed["import_ipprefix"] = self.import_ipprefix
        self.proposed["import_routepolicyname"] = self.import_routepolicyname
        self.proposed["bfd_min_rx"] = self.bfd_min_rx
        self.proposed["bfd_min_tx"] = self.bfd_min_tx
        self.proposed["bfd_multiplier_num"] = self.bfd_multiplier_num
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if not self.isis_dict:
            self.existing["instance"] = None
        else:
            self.existing["instance"] = self.isis_dict.get("instance")

    def get_end_state(self):
        """get end state info"""

        isis_dict = self.get_isis_dict()
        if not isis_dict:
            self.end_state["instance"] = None
        else:
            self.end_state["instance"] = isis_dict.get("instance")
        if self.end_state == self.existing:
            self.changed = False

    def work(self):
        """worker"""

        self.check_params()
        self.isis_dict = self.get_isis_dict()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        xml_str = ''
        if self.instance_id:
            xml_str += self.config_session()
        # update to device
        if xml_str:
            self.netconf_load_config(xml_str)
            self.changed = True

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()
        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        instance_id=dict(required=True, type='int'),
        description=dict(required=False, type='str'),
        islevel=dict(required=False, type='str', choices=['level_1', 'level_2', 'level_1_2']),
        coststyle=dict(required=False, type='str', choices=['narrow', 'wide', 'transition', 'ntransition', 'wtransition']),
        relaxspfLimit=dict(required=False, type='bool'),
        stdlevel1cost=dict(required=False, type='int'),
        stdlevel2cost=dict(required=False, type='int'),
        stdbandwidth=dict(required=False, type='int'),
        autocostenable=dict(required=False, type='bool'),
        autocostenablecompatible=dict(required=False, type='bool'),
        netentity=dict(required=False, type='str'),
        preference_value=dict(required=False, type='int'),
        route_policy_name=dict(required=False, type='str'),
        max_load=dict(required=False, type='int'),
        ip_address=dict(required=False, type='str'),
        weight=dict(required=False, type='int'),
        penetration_direct=dict(required=False, type='str', choices=['level2-level1', 'level1-level2']),
        aclnum_or_name=dict(required=False, type='str'),
        ip_prefix_name=dict(required=False, type='str'),
        import_routepolicy_name=dict(required=False, type='str'),
        tag=dict(required=False, type='int'),
        allow_filter=dict(required=False, type='bool'),
        allow_up_down=dict(required=False, type='bool'),
        enablelevel1tolevel2=dict(required=False, type='bool'),
        defaultmode=dict(required=False, type='str', choices=['always', 'matchDefault', 'matchAny']),
        mode_routepolicyname=dict(required=False, type='str'),
        cost=dict(required=False, type='int'),
        mode_tag=dict(required=False, type='int'),
        level_type=dict(required=False, type='str', choices=['level_1', 'level_2', 'level_1_2']),
        avoid_learning=dict(required=False, type='bool'),
        protocol=dict(required=False, type='str', choices=['direct', 'ospf', 'isis', 'static', 'rip', 'bgp', 'ospfv3', 'all']),
        processid=dict(required=False, type='int'),
        cost_type=dict(required=False, type='str', choices=['external', 'internal']),
        import_cost=dict(required=False, type='int'),
        import_tag=dict(required=False, type='int'),
        import_route_policy=dict(required=False, type='str'),
        impotr_leveltype=dict(required=False, type='str', choices=['level_1', 'level_2', 'level_1_2']),
        inheritcost=dict(required=False, type='bool'),
        permitibgp=dict(required=False, type='bool'),
        export_protocol=dict(required=False, type='str', choices=['direct', 'ospf', 'isis', 'static', 'rip', 'bgp', 'ospfv3', 'all']),
        export_policytype=dict(required=False, type='str', choices=['aclNumOrName', 'ipPrefix', 'routePolicy']),
        export_processid=dict(required=False, type='int'),
        export_aclnumorname=dict(required=False, type='str'),
        export_ipprefix=dict(required=False, type='str'),
        export_routepolicyname=dict(required=False, type='str'),
        import_aclnumorname=dict(required=False, type='str'),
        import_ipprefix=dict(required=False, type='str'),
        import_routepolicyname=dict(required=False, type='str'),
        bfd_min_rx=dict(required=False, type='int'),
        bfd_min_tx=dict(required=False, type='int'),
        bfd_multiplier_num=dict(required=False, type='int'),
        state=dict(required=False, default='present', choices=['present', 'absent'])
    )

    module = ISIS_View(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
