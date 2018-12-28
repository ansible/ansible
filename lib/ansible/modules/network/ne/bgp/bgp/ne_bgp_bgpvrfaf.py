# -*- coding: utf-8 -*-
# !/usr/bin/python
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
# xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">

from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_process_tail
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_process_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_tail
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_novalue
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_value
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_BGP_INSTANCE_TAIL
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_BGP_INSTANCE_HEADER
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_GET_BGP_VRF_TAIL
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_GET_BGP_VRF_HEAD
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import socket
import sys
import re
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_bgp_bgpvrfaf
version_added: "2.6"
short_description: Manages BGP peer configuration on HUAWEI netengine switches.
description:
    - Manages BGP peer configurations on HUAWEI netengine switches.
author:
    - wangyuanqiang  (@netengine-Ansible)
    - Modified by gewuyue for support YANG
options:

'''

EXAMPLES = '''

- name: netengine BGP peer test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli

  tasks:

  - name: "Config bgp peer"
    ne_bgp_bgpVrfAf:
      state: present
      vrf_name: js
      peer_addr: 192.168.10.10
      remote_as: 500
      provider: "{{ cli }}"

  - name: "Config bgp route id"
    ne_bgp_bgpVrfAf:
      state: absent
      vrf_name: js
      peer_addr: 192.168.10.10
      provider: "{{ cli }}"
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
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
updates:
    description: command sent to the device
    returned: always
    type: list
'''

# import pydevd


class BgpVrfAf(object):
    """ Manages BGP peer configuration """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.aftype = self.module.params['aftype']
        self.activerouteadvertise = self.module.params['activerouteadvertise']
        self.addpathselnum = self.module.params['addpathselnum']
        self.policyextcommenable = self.module.params['policyextcommenable']
        self.alwayscomparemed = self.module.params['alwayscomparemed']
        self.applylabelmode = self.module.params['applylabelmode']
        self.popgo = self.module.params['popgo']
        self.autofrrenable = self.module.params['autofrrenable']
        self.bestexternal = self.module.params['bestexternal']
        self.enbestrtbiterrdetection = self.module.params['enbestrtbiterrdetection']
        self.defaultmed = self.module.params['defaultmed']
        self.defaultrtimportenable = self.module.params['defaultrtimportenable']
        self.determinmed = self.module.params['determinmed']
        self.ebgpifsensitive = self.module.params['ebgpifsensitive']
        self.maximumloadbalance = self.module.params['maximumloadbalance']
        self.ecmpnexthopchanged = self.module.params['ecmpnexthopchanged']
        self.labeladvenable = self.module.params['labeladvenable']
        # self.ingressLspProtect = self.module.params['ingressLspProtect']
        self.maxloadibgpnum = self.module.params['maxloadibgpnum']
        self.ibgpecmpnexthopchanged = self.module.params['ibgpecmpnexthopchanged']
        self.ebgpecmpnexthopchanged = self.module.params['ebgpecmpnexthopchanged']
        self.maxloadebgpnum = self.module.params['maxloadebgpnum']
        self.eibgploadbalan = self.module.params['eibgploadbalan']
        self.eibgpecmpnexthopchanged = self.module.params['eibgpecmpnexthopchanged']
        self.loadbalancingigpmetricignore = self.module.params['loadbalancingigpmetricignore']
        self.loadbalancingeibgp = self.module.params['loadbalancingeibgp']
        self.loadbalancingaspathignore = self.module.params['loadbalancingaspathignore']
        self.loadbalancingaspathrelax = self.module.params['loadbalancingaspathrelax']
        self.explicitnull = self.module.params['explicitnull']
        self.ingresslsppolicyname = self.module.params['ingresslsppolicyname']
        self.mednoneasmaximum = self.module.params['mednoneasmaximum']
        self.nexthopdelaytime = self.module.params['nexthopdelaytime']
        self.nocriticalnexthopdelaytime = self.module.params['nocriticalnexthopdelaytime']
        self.nexthopseldependtype = self.module.params['nexthopseldependtype']
        self.nexthopinheritipcost = self.module.params['nexthopinheritipcost']
        # self.nexthopThirdParty = self.module.params['nexthopThirdParty']
        self.nhprelayroutepolicyname = self.module.params['nhprelayroutepolicyname']
        self.originasvalid = self.module.params['originasvalid']
        self.allowinvalidas = self.module.params['allowinvalidas']
        self.originasvalidenable = self.module.params['originasvalidenable']
        self.policyqppbenable = self.module.params['policyqppbenable']
        self.policyvpntarget = self.module.params['policyvpntarget']
        self.aspathneglect = self.module.params['aspathneglect']
        self.preferenceexternal = self.module.params['preferenceexternal']
        self.preferenceinternal = self.module.params['preferenceinternal']
        self.preferencelocal = self.module.params['preferencelocal']
        self.prefrencepolicyname = self.module.params['prefrencepolicyname']
        self.qosid = self.module.params['qosid']
        self.qosidpolicyname = self.module.params['qosidpolicyname']
        self.reflectbetweenclient = self.module.params['reflectbetweenclient']
        self.reflectchgpath = self.module.params['reflectchgpath']
        self.reflectorclusterid = self.module.params['reflectorclusterid']
        self.reflectorclusteripv4 = self.module.params['reflectorclusteripv4']
        self.ribonlyenable = self.module.params['ribonlyenable']
        self.ribonlypolicyname = self.module.params['ribonlypolicyname']
        self.routerid = self.module.params['routerid']
        self.vrfridautosel = self.module.params['vrfridautosel']
        self.routeridneglect = self.module.params['routeridneglect']
        self.routeseldelay = self.module.params['routeseldelay']
        self.rrfilternumber = self.module.params['rrfilternumber']
        self.summaryautomatic = self.module.params['summaryautomatic']
        self.supernetlabeladv = self.module.params['supernetlabeladv']
        self.supernetuniadv = self.module.params['supernetuniadv']
        self.tunnelselectorall = self.module.params['tunnelselectorall']
        self.tunnelselectorname = self.module.params['tunnelselectorname']
        self.vplsaddisable = self.module.params['vplsaddisable']
        self.vplsenable = self.module.params['vplsenable']
        self.vpwsenable = self.module.params['vpwsenable']
        self.originatorprior = self.module.params['originatorprior']
        # self.lowestPriority = self.module.params['lowestPriority']
        self.routematchdestination = self.module.params['routematchdestination']
        self.igpmetricignore = self.module.params['igpmetricignore']
        self.defaultlocalpref = self.module.params['defaultlocalpref']
        self.relaydelayenable = self.module.params['relaydelayenable']
        self.unirtrelaytnl = self.module.params['unirtrelaytnl']
        self.unirttnlselname = self.module.params['unirttnlselname']
        self.activatetag = self.module.params['activatetag']
        self.medplusigp = self.module.params['medplusigp']
        self.medmultiplier = self.module.params['medmultiplier']
        self.igpmultiplier = self.module.params['igpmultiplier']
        self.vrfimportnhpinvariable = self.module.params['vrfimportnhpinvariable']
        self.redirectiprelaytnlenable = self.module.params['redirectiprelaytnlenable']
        self.redirectiprelaytnlselname = self.module.params['redirectiprelaytnlselname']
        self.domainas = self.module.params['domainas']
        self.domainidentifier = self.module.params['domainidentifier']
        self.lspmtu = self.module.params['lspmtu']
        self.slowpeerdet = self.module.params['slowpeerdet']
        self.slowpeerthval = self.module.params['slowpeerthval']
        self.vrfasnum = self.module.params['vrfasnum']
        # self.bwBcNonstd = self.module.params['bwBcNonstd']
        self.timerforeor = self.module.params['timerforeor']
        self.externalpathnum = self.module.params['externalpathnum']
        self.rtfilterdisable = self.module.params['rtfilterdisable']
        self.multihomingnonstdenable = self.module.params['multihomingnonstdenable']
        self.slowpeerabdet = self.module.params['slowpeerabdet']
        self.slowpeerabthval = self.module.params['slowpeerabthval']
        self.flowvalidationmodeas = self.module.params['flowvalidationmodeas']
        # self.ibgpIfSensitive = self.module.params['ibgpIfSensitive']
        self.locatorname = self.module.params['locatorname']
        self.autosid = self.module.params['autosid']
        self.sripv6mode = self.module.params['sripv6mode']
        self.aigp = self.module.params['aigp']
        self.state = self.module.params['state']

        # self.bitErrDetectionEnable = self.module.params['bitErrDetectionEnable']
        # self.bitErrDetectionLocalpref = self.module.params['bitErrDetectionLocalpref']
        # self.bitErrDetectionMed = self.module.params['bitErrDetectionMed']
        # self.bitErrDetectionRtPolicy = self.module.params['bitErrDetectionRtPolicy']

        # BGP peer
        self.bgp_VrfAf_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """
        # mutually_exclusive=mutually_exclusive,
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        pass
        # check vrfname
        # if self.vrfname:
        #    if len(self.vrfname) > 31 or len(self.vrfname.replace(' ', '')) < 1:
        #        self.module.fail_json(
        # msg='Error: VpnInstance name  is not in the range from 1 to 31.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_proposed(self):
        """Get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["aftype"] = self.aftype

        if self.activerouteadvertise is not None:
            self.proposed["activerouteadvertise"] = self.activerouteadvertise
        if self.addpathselnum is not None:
            self.proposed["addpathselnum"] = self.addpathselnum
        if self.policyextcommenable is not None:
            self.proposed["policyextcommenable"] = self.policyextcommenable
        if self.alwayscomparemed is not None:
            self.proposed["alwayscomparemed"] = self.alwayscomparemed
        if self.applylabelmode is not None:
            self.proposed["applylabelmode"] = self.applylabelmode
        if self.popgo is not None:
            self.proposed["popgo"] = self.popgo
        if self.autofrrenable is not None:
            self.proposed["autofrrenable"] = self.autofrrenable
        if self.bestexternal is not None:
            self.proposed["bestexternal"] = self.bestexternal
        # if self.bitErrDetectionEnable is not None:
        #    self.proposed["bitErrDetectionEnable"] = self.bitErrDetectionEnable
        # if self.bitErrDetectionLocalpref is not None:
        #    self.proposed["bitErrDetectionLocalpref"] = self.bitErrDetectionLocalpref
        # if self.bitErrDetectionMed is not None:
        #    self.proposed["bitErrDetectionMed"] = self.bitErrDetectionMed
        # if self.bitErrDetectionRtPolicy is not None:
        #    self.proposed["bitErrDetectionRtPolicy"] = self.bitErrDetectionRtPolicy
        if self.enbestrtbiterrdetection is not None:
            self.proposed["enbestrtbiterrdetection"] = self.enbestrtbiterrdetection
        if self.defaultmed is not None:
            self.proposed["defaultmed"] = self.defaultmed
        if self.defaultrtimportenable is not None:
            self.proposed["defaultrtimportenable"] = self.defaultrtimportenable
        if self.determinmed is not None:
            self.proposed["determinmed"] = self.determinmed
        if self.ebgpifsensitive is not None:
            self.proposed["ebgpifsensitive"] = self.ebgpifsensitive
        if self.maximumloadbalance is not None:
            self.proposed["maximumloadbalance"] = self.maximumloadbalance
        if self.maximumloadbalance is not None:
            self.proposed["ecmpnexthopchanged"] = self.ecmpnexthopchanged
        if self.labeladvenable is not None:
            self.proposed["labeladvenable"] = self.labeladvenable
        # if self.ingressLspProtect is not None:
        #    self.proposed["ingressLspProtect"] = self.ingressLspProtect
        if self.maxloadibgpnum is not None:
            self.proposed["maxloadibgpnum"] = self.maxloadibgpnum
        if self.ibgpecmpnexthopchanged is not None:
            self.proposed["ibgpecmpnexthopchanged"] = self.ibgpecmpnexthopchanged
        if self.ebgpecmpnexthopchanged is not None:
            self.proposed["ebgpecmpnexthopchanged"] = self.ebgpecmpnexthopchanged
        if self.maxloadebgpnum is not None:
            self.proposed["maxloadebgpnum"] = self.maxloadebgpnum
        if self.eibgploadbalan is not None:
            self.proposed["eibgploadbalan"] = self.eibgploadbalan
        if self.eibgpecmpnexthopchanged is not None:
            self.proposed["eibgpecmpnexthopchanged"] = self.eibgpecmpnexthopchanged
        if self.loadbalancingigpmetricignore is not None:
            self.proposed["loadbalancingigpmetricignore"] = self.loadbalancingigpmetricignore
        if self.loadbalancingeibgp is not None:
            self.proposed["loadbalancingeibgp"] = self.loadbalancingeibgp
        if self.loadbalancingaspathignore is not None:
            self.proposed["loadbalancingaspathignore"] = self.loadbalancingaspathignore
        if self.loadbalancingaspathrelax is not None:
            self.proposed["loadbalancingaspathrelax"] = self.loadbalancingaspathrelax
        if self.explicitnull is not None:
            self.proposed["explicitnull"] = self.explicitnull
        if self.ingresslsppolicyname is not None:
            self.proposed["ingresslsppolicyname"] = self.ingresslsppolicyname
        if self.mednoneasmaximum is not None:
            self.proposed["mednoneasmaximum"] = self.mednoneasmaximum
        if self.nexthopdelaytime is not None:
            self.proposed["nexthopdelaytime"] = self.nexthopdelaytime
        if self.nocriticalnexthopdelaytime is not None:
            self.proposed["nocriticalnexthopdelaytime"] = self.nocriticalnexthopdelaytime
        if self.nexthopseldependtype is not None:
            self.proposed["nexthopseldependtype"] = self.nexthopseldependtype
        if self.nexthopinheritipcost is not None:
            self.proposed["nexthopinheritipcost"] = self.nexthopinheritipcost
        # if self.nexthopThirdParty is not None:
        #    self.proposed["nexthopThirdParty"] = self.nexthopThirdParty
        if self.nhprelayroutepolicyname is not None:
            self.proposed["nhprelayroutepolicyname"] = self.nhprelayroutepolicyname
        if self.originasvalid is not None:
            self.proposed["originasvalid"] = self.originasvalid
        if self.allowinvalidas is not None:
            self.proposed["allowinvalidas"] = self.allowinvalidas
        if self.originasvalidenable is not None:
            self.proposed["originasvalidenable"] = self.originasvalidenable
        if self.policyqppbenable is not None:
            self.proposed["policyqppbenable"] = self.policyqppbenable
        if self.policyvpntarget is not None:
            self.proposed["policyvpntarget"] = self.policyvpntarget
        if self.aspathneglect is not None:
            self.proposed["aspathneglect"] = self.aspathneglect
        if self.preferenceexternal is not None:
            self.proposed["preferenceexternal"] = self.preferenceexternal
        if self.preferenceinternal is not None:
            self.proposed["preferenceinternal"] = self.preferenceinternal
        if self.preferencelocal is not None:
            self.proposed["preferencelocal"] = self.preferencelocal
        if self.prefrencepolicyname is not None:
            self.proposed["prefrencepolicyname"] = self.prefrencepolicyname
        if self.qosid is not None:
            self.proposed["qosid"] = self.qosid
        if self.qosidpolicyname is not None:
            self.proposed["qosidpolicyname"] = self.qosidpolicyname
        if self.reflectbetweenclient is not None:
            self.proposed["reflectbetweenclient"] = self.reflectbetweenclient
        if self.reflectchgpath is not None:
            self.proposed["reflectchgpath"] = self.reflectchgpath
        if self.reflectorclusterid is not None:
            self.proposed["reflectorclusterid"] = self.reflectorclusterid
        if self.reflectorclusteripv4 is not None:
            self.proposed["reflectorclusteripv4"] = self.reflectorclusteripv4
        if self.ribonlyenable is not None:
            self.proposed["ribonlyenable"] = self.ribonlyenable
        if self.ribonlypolicyname is not None:
            self.proposed["ribonlypolicyname"] = self.ribonlypolicyname
        if self.routerid is not None:
            self.proposed["routerid"] = self.routerid
        if self.vrfridautosel is not None:
            self.proposed["vrfridautosel"] = self.vrfridautosel
        if self.routeridneglect is not None:
            self.proposed["routeridneglect"] = self.routeridneglect
        if self.routeseldelay is not None:
            self.proposed["routeseldelay"] = self.routeseldelay
        if self.rrfilternumber is not None:
            self.proposed["rrfilternumber"] = self.rrfilternumber
        if self.summaryautomatic is not None:
            self.proposed["summaryautomatic"] = self.summaryautomatic
        if self.supernetlabeladv is not None:
            self.proposed["supernetlabeladv"] = self.supernetlabeladv
        if self.supernetuniadv is not None:
            self.proposed["supernetuniadv"] = self.supernetuniadv
        if self.tunnelselectorall is not None:
            self.proposed["tunnelselectorall"] = self.tunnelselectorall
        if self.tunnelselectorname is not None:
            self.proposed["tunnelselectorname"] = self.tunnelselectorname
        if self.vplsaddisable is not None:
            self.proposed["vplsaddisable"] = self.vplsaddisable
        if self.vplsenable is not None:
            self.proposed["vplsenable"] = self.vplsenable
        if self.vpwsenable is not None:
            self.proposed["vpwsenable"] = self.vpwsenable
        if self.originatorprior is not None:
            self.proposed["originatorprior"] = self.originatorprior
        # if self.lowestPriority is not None:
        #    self.proposed["lowestPriority"] = self.lowestPriority
        if self.routematchdestination is not None:
            self.proposed["routematchdestination"] = self.routematchdestination
        if self.igpmetricignore is not None:
            self.proposed["igpmetricignore"] = self.igpmetricignore
        if self.defaultlocalpref is not None:
            self.proposed["defaultlocalpref"] = self.defaultlocalpref
        if self.relaydelayenable is not None:
            self.proposed["relaydelayenable"] = self.relaydelayenable
        if self.unirtrelaytnl is not None:
            self.proposed["unirtrelaytnl"] = self.unirtrelaytnl
        if self.unirttnlselname is not None:
            self.proposed["unirttnlselname"] = self.unirttnlselname
        if self.activatetag is not None:
            self.proposed["activatetag"] = self.activatetag
        if self.medplusigp is not None:
            self.proposed["medplusigp"] = self.medplusigp
        if self.medmultiplier is not None:
            self.proposed["medmultiplier"] = self.medmultiplier
        if self.igpmultiplier is not None:
            self.proposed["igpmultiplier"] = self.igpmultiplier
        if self.vrfimportnhpinvariable is not None:
            self.proposed["vrfimportnhpinvariable"] = self.vrfimportnhpinvariable
        if self.redirectiprelaytnlenable is not None:
            self.proposed["redirectiprelaytnlenable"] = self.redirectiprelaytnlenable
        if self.redirectiprelaytnlselname is not None:
            self.proposed["redirectiprelaytnlselname"] = self.redirectiprelaytnlselname
        if self.domainas is not None:
            self.proposed["domainas"] = self.domainas
        if self.domainidentifier is not None:
            self.proposed["domainidentifier"] = self.domainidentifier
        if self.lspmtu is not None:
            self.proposed["lspmtu"] = self.lspmtu
        if self.slowpeerdet is not None:
            self.proposed["slowpeerdet"] = self.slowpeerdet
        if self.slowpeerthval is not None:
            self.proposed["slowpeerthval"] = self.slowpeerthval
        if self.vrfasnum is not None:
            self.proposed["vrfasnum"] = self.vrfasnum
        # if self.bwBcNonstd is not None:
        #    self.proposed["bwBcNonstd"] = self.bwBcNonstd
        if self.timerforeor is not None:
            self.proposed["timerforeor"] = self.timerforeor
        if self.externalpathnum is not None:
            self.proposed["externalpathnum"] = self.externalpathnum
        if self.rtfilterdisable is not None:
            self.proposed["rtfilterdisable"] = self.rtfilterdisable
        if self.multihomingnonstdenable is not None:
            self.proposed["multihomingnonstdenable"] = self.multihomingnonstdenable
        if self.slowpeerabdet is not None:
            self.proposed["slowpeerabdet"] = self.slowpeerabdet
        if self.slowpeerabthval is not None:
            self.proposed["slowpeerabthval"] = self.slowpeerabthval
        if self.flowvalidationmodeas is not None:
            self.proposed["flowvalidationmodeas"] = self.flowvalidationmodeas
        # if self.ibgpIfSensitive is not None:
        #    self.proposed["ibgpIfSensitive"] = self.ibgpIfSensitive
        if self.locatorname is not None:
            self.proposed["locatorname"] = self.locatorname
        if self.autosid is not None:
            self.proposed["autosid"] = self.autosid
        if self.sripv6mode is not None:
            self.proposed["sripv6mode"] = self.sripv6mode
        if self.aigp is not None:
            self.proposed["aigp"] = self.aigp

        self.proposed["state"] = self.state

    def get_existing(self):
        """Get existing info"""

        if not self.bgp_VrfAf_info or len(self.bgp_VrfAf_info) == 0:
            return

        self.existing["vrfname"] = self.vrfname
        self.existing["bgpVrfAFs"] = self.bgp_VrfAf_info["bgpVrfAFs"]

    def get_end_state(self):
        """Get end state info"""

        bgp_VrfAf_info = self.get_bgp_VrfAf()
        if not bgp_VrfAf_info or len(bgp_VrfAf_info) == 0:
            return

        self.end_state["vrfname"] = self.vrfname
        self.end_state["bgpVrfAFs"] = bgp_VrfAf_info["bgpVrfAFs"]

    def get_bgp_VrfAf(self):
        """ Get BGP VrfAF informaton to the dictionary."""
        bgp_VrfAf_info = dict()

        # Head info
        get_xml_str = NE_COMMON_XML_GET_BGP_VRF_HEAD
        # vrfname Key
        get_xml_str = constr_leaf_value(get_xml_str, "vrfName", self.vrfname)
        get_xml_str = constr_container_head(get_xml_str, "bgpVrfAFs")
        get_xml_str = constr_container_head(get_xml_str, "bgpVrfAF")

        # Body info
        # aftype  Key
        get_xml_str = constr_leaf_value(get_xml_str, "afType", self.aftype)

        # get_xml_str = constr_leaf_novalue(get_xml_str, "activeRouteAdvertise")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "addPathSelNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "policyExtCommEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "alwaysCompareMed")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "applyLabelMode")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "popGo")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "autoFrrEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "bestExternal")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "bitErrDetectionEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "bitErrDetectionLocalpref")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "bitErrDetectionMed")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "bitErrDetectionRtPolicy")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "enBestRtBitErrDetection")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "defaultMed")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "defaultRtImportEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "determinMed")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ebgpIfSensitive")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "maximumLoadBalance")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ecmpNexthopChanged")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "labelAdvEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ingressLspProtect")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "maxLoadIbgpNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ibgpEcmpNexthopChanged")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ebgpEcmpNexthopChanged")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "maxLoadEbgpNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "eibgpLoadBalan")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "eibgpEcmpNexthopChanged")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "loadBalancingIgpMetricIgnore")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "loadBalancingEibgp")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "loadBalancingAsPathIgnore")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "loadBalancingAsPathRelax")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "explicitNull")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ingressLspPolicyName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "medNoneAsMaximum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "nexthopDelayTime")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "noCriticalNexthopDelayTime")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "nextHopSelDependType")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "nextHopInheritIpcost")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "nexthopThirdParty")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "nhpRelayRoutePolicyName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "originAsValid")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "allowInvalidAs")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "originAsValidEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "policyQPPBEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "policyVpnTarget")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "asPathNeglect")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "preferenceExternal")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "preferenceInternal")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "preferenceLocal")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "prefrencePolicyName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "qosId")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "qosIdPolicyName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "reflectBetweenClient")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "reflectChgPath")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "reflectorClusterId")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "reflectorClusterIpv4")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ribOnlyEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ribOnlyPolicyName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "routerId")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vrfRidAutoSel")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "routerIdNeglect")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "routeSelDelay")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "rrFilterNumber")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "summaryAutomatic")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "supernetLabelAdv")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "supernetUniAdv")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "tunnelSelectorAll")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "tunnelSelectorName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vplsAdDisable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vplsEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vpwsEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "originatorPrior")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "lowestPriority")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "routeMatchDestination")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "igpMetricIgnore")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "defaultLocalPref")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "relayDelayEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "uniRtRelayTnl")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "uniRtTnlSelName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "activateTag")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "medPlusIgp")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "medMultiplier")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "igpMultiplier")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vrfImportnhpinvariable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "redirectIpRelayTnlEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "redirectIpRelayTnlSelName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "domainAs")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "domainIdentifier")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "lspMtu")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "slowPeerDet")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "slowPeerThVal")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vrfAsNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "bwBcNonstd")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "timerForEor")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "externalPathNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "rtFilterDisable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "multiHomingNonStdEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "slowPeerAbDet")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "slowPeerAbThVal")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "flowValidationModeAs")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ibgpIfSensitive")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "locatorName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "autoSid")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "srIpv6Mode")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "aigp")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ingressLspLoadBalancNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "transitLspLoadBalancNum")

        # Tail info
        get_xml_str = constr_container_tail(get_xml_str, "bgpVrfAF")
        get_xml_str = constr_container_tail(get_xml_str, "bgpVrfAFs")
        get_xml_str += NE_COMMON_XML_GET_BGP_VRF_TAIL

        ret_xml_str = get_nc_config(self.module, get_xml_str)
        if "<data/>" in ret_xml_str:
            return bgp_VrfAf_info

        ret_xml_str = ret_xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # VrfName information
        root = ElementTree.fromstring(ret_xml_str)
        bgpVrf = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf")

        if len(bgpVrf) != 0:
            for vrf in bgpVrf:
                if vrf.tag in ["vrfName"]:
                    bgp_VrfAf_info[vrf.tag.lower()] = vrf.text

        # bgp peer information
        bgp_VrfAf_info["bgpVrfAFs"] = list()
        bgpVrfAFs = root.findall(
            "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF")

        if bgpVrfAFs is None or len(bgpVrfAFs) == 0:
            return None

        for bgpVrfAF in bgpVrfAFs:
            bgpVrfAF_dict = dict()
            for ele in bgpVrfAF:
                if ele.tag in ["afType",
                               "activeRouteAdvertise", "addPathSelNum", "policyExtCommEnable", "alwaysCompareMed",
                               "applyLabelMode", "popGo", "autoFrrEnable", "bestExternal", "bitErrDetectionEnable", "bitErrDetectionLocalpref",
                               "bitErrDetectionMed", "bitErrDetectionRtPolicy", "enBestRtBitErrDetection", "defaultMed",
                               "defaultRtImportEnable", "determinMed", "ebgpIfSensitive", "maximumLoadBalance",
                               "ecmpNexthopChanged", "labelAdvEnable", "ingressLspProtect", "maxLoadIbgpNum",
                               "ibgpEcmpNexthopChanged", "ebgpEcmpNexthopChanged", "maxLoadEbgpNum", "eibgpLoadBalan",
                               "eibgpEcmpNexthopChanged", "loadBalancingIgpMetricIgnore", "loadBalancingEibgp", "loadBalancingAsPathIgnore",
                               "loadBalancingAsPathRelax", "explicitNull", "ingressLspPolicyName", "medNoneAsMaximum",
                               "nexthopDelayTime", "noCriticalNexthopDelayTime", "nextHopSelDependType", "nextHopInheritIpcost",
                               "nexthopThirdParty", "nhpRelayRoutePolicyName", "originAsValid", "allowInvalidAs",
                               "originAsValidEnable", "policyQPPBEnable", "policyVpnTarget", "asPathNeglect",
                               "preferenceExternal", "preferenceInternal", "preferenceLocal", "prefrencePolicyName",
                               "qosId", "qosIdPolicyName", "reflectBetweenClient", "reflectChgPath",
                               "reflectorClusterId", "reflectorClusterIpv4", "ribOnlyEnable", "ribOnlyPolicyName",
                               "routerId", "vrfRidAutoSel", "routerIdNeglect", "routeSelDelay", "rrFilterNumber", "summaryAutomatic",
                               "supernetLabelAdv", "supernetUniAdv", "tunnelSelectorAll", "tunnelSelectorName",
                               "vplsAdDisable", "vplsEnable", "vpwsEnable", "originatorPrior", "lowestPriority", "routeMatchDestination",
                               "igpMetricIgnore", "defaultLocalPref", "relayDelayEnable", "uniRtRelayTnl", "uniRtTnlSelName", "activateTag",
                               "medPlusIgp", "medMultiplier", "igpMultiplier", "vrfImportnhpinvariable", "redirectIpRelayTnlEnable",
                               "redirectIpRelayTnlSelName", "domainAs", "domainIdentifier", "lspMtu", "slowPeerDet", "slowPeerThVal", "vrfAsNum",
                               "bwBcNonstd", "timerForEor", "externalPathNum", "rtFilterDisable",
                               "multiHomingNonStdEnable", "slowPeerAbDet", "slowPeerAbThVal", "flowValidationModeAs",
                               "ibgpIfSensitive", "locatorName", "autoSid", "srIpv6Mode", "aigp"
                               ]:
                    bgpVrfAF_dict[ele.tag.lower()] = ele.text
            bgp_VrfAf_info["bgpVrfAFs"].append(bgpVrfAF_dict)

        return bgp_VrfAf_info

    def common_process(self, operType, operDesc):
        """Common process BGP peer."""
        # Head process
        if NE_COMMON_XML_OPERATION_CREATE == operType:
            xml_str = NE_BGP_INSTANCE_HEADER % NE_COMMON_XML_OPERATION_MERGE
        else:
            xml_str = NE_BGP_INSTANCE_HEADER % operType

        # Process vrfname and peerAddr is the key, must input
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "bgpVrfAF", operType)

        # Body process
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
        xml_str = constr_leaf_value(
            xml_str,
            "activeRouteAdvertise",
            self.activerouteadvertise)
        xml_str = constr_leaf_value(
            xml_str, "addPathSelNum", self.addpathselnum)
        xml_str = constr_leaf_value(
            xml_str,
            "policyExtCommEnable",
            self.policyextcommenable)
        xml_str = constr_leaf_value(
            xml_str, "alwaysCompareMed", self.alwayscomparemed)
        xml_str = constr_leaf_value(
            xml_str, "applyLabelMode", self.applylabelmode)
        xml_str = constr_leaf_value(xml_str, "popGo", self.popgo)
        xml_str = constr_leaf_value(
            xml_str, "autoFrrEnable", self.autofrrenable)
        xml_str = constr_leaf_value(xml_str, "bestExternal", self.bestexternal)
        # xml_str = constr_leaf_value(xml_str, "bitErrDetectionEnable",        self.bitErrDetectionEnable)
        # xml_str = constr_leaf_value(xml_str, "bitErrDetectionLocalpref",     self.bitErrDetectionLocalpref)
        # xml_str = constr_leaf_value(xml_str, "bitErrDetectionMed",           self.bitErrDetectionMed)
        # xml_str = constr_leaf_value(xml_str, "bitErrDetectionRtPolicy",      self.bitErrDetectionRtPolicy)
        xml_str = constr_leaf_value(
            xml_str,
            "enBestRtBitErrDetection",
            self.enbestrtbiterrdetection)
        xml_str = constr_leaf_value(xml_str, "defaultMed", self.defaultmed)
        xml_str = constr_leaf_value(
            xml_str,
            "defaultRtImportEnable",
            self.defaultrtimportenable)
        xml_str = constr_leaf_value(xml_str, "determinMed", self.determinmed)
        xml_str = constr_leaf_value(
            xml_str, "ebgpIfSensitive", self.ebgpifsensitive)
        xml_str = constr_leaf_value(
            xml_str,
            "maximumLoadBalance",
            self.maximumloadbalance)
        xml_str = constr_leaf_value(
            xml_str,
            "ecmpNexthopChanged",
            self.ecmpnexthopchanged)
        xml_str = constr_leaf_value(
            xml_str, "labelAdvEnable", self.labeladvenable)
        # xml_str = constr_leaf_value(xml_str, "ingressLspProtect",            self.ingressLspProtect)
        xml_str = constr_leaf_value(
            xml_str, "maxLoadIbgpNum", self.maxloadibgpnum)
        xml_str = constr_leaf_value(
            xml_str,
            "ibgpEcmpNexthopChanged",
            self.ibgpecmpnexthopchanged)
        xml_str = constr_leaf_value(
            xml_str,
            "ebgpEcmpNexthopChanged",
            self.ebgpecmpnexthopchanged)
        xml_str = constr_leaf_value(
            xml_str, "maxLoadEbgpNum", self.maxloadebgpnum)
        xml_str = constr_leaf_value(
            xml_str, "eibgpLoadBalan", self.eibgploadbalan)
        xml_str = constr_leaf_value(
            xml_str,
            "eibgpEcmpNexthopChanged",
            self.eibgpecmpnexthopchanged)
        xml_str = constr_leaf_value(
            xml_str,
            "loadBalancingIgpMetricIgnore",
            self.loadbalancingigpmetricignore)
        xml_str = constr_leaf_value(
            xml_str,
            "loadBalancingEibgp",
            self.loadbalancingeibgp)
        xml_str = constr_leaf_value(
            xml_str,
            "loadBalancingAsPathIgnore",
            self.loadbalancingaspathignore)
        xml_str = constr_leaf_value(
            xml_str,
            "loadBalancingAsPathRelax",
            self.loadbalancingaspathrelax)
        xml_str = constr_leaf_value(xml_str, "explicitNull", self.explicitnull)
        xml_str = constr_leaf_value(
            xml_str,
            "ingressLspPolicyName",
            self.ingresslsppolicyname)
        xml_str = constr_leaf_value(
            xml_str, "medNoneAsMaximum", self.mednoneasmaximum)
        xml_str = constr_leaf_value(
            xml_str, "nexthopDelayTime", self.nexthopdelaytime)
        xml_str = constr_leaf_value(
            xml_str,
            "noCriticalNexthopDelayTime",
            self.nocriticalnexthopdelaytime)
        xml_str = constr_leaf_value(
            xml_str,
            "nextHopSelDependType",
            self.nexthopseldependtype)
        xml_str = constr_leaf_value(
            xml_str,
            "nextHopInheritIpcost",
            self.nexthopinheritipcost)
        # xml_str = constr_leaf_value(xml_str, "nexthopThirdParty",            self.nexthopThirdParty)
        xml_str = constr_leaf_value(
            xml_str,
            "nhpRelayRoutePolicyName",
            self.nhprelayroutepolicyname)
        xml_str = constr_leaf_value(
            xml_str, "originAsValid", self.originasvalid)
        xml_str = constr_leaf_value(
            xml_str, "allowInvalidAs", self.allowinvalidas)
        xml_str = constr_leaf_value(
            xml_str,
            "originAsValidEnable",
            self.originasvalidenable)
        xml_str = constr_leaf_value(
            xml_str, "policyQPPBEnable", self.policyqppbenable)
        xml_str = constr_leaf_value(
            xml_str, "policyVpnTarget", self.policyvpntarget)
        xml_str = constr_leaf_value(
            xml_str, "asPathNeglect", self.aspathneglect)
        xml_str = constr_leaf_value(
            xml_str,
            "preferenceExternal",
            self.preferenceexternal)
        xml_str = constr_leaf_value(
            xml_str,
            "preferenceInternal",
            self.preferenceinternal)
        xml_str = constr_leaf_value(
            xml_str, "preferenceLocal", self.preferencelocal)
        xml_str = constr_leaf_value(
            xml_str,
            "prefrencePolicyName",
            self.prefrencepolicyname)
        xml_str = constr_leaf_value(xml_str, "qosId", self.qosid)
        xml_str = constr_leaf_value(
            xml_str, "qosIdPolicyName", self.qosidpolicyname)
        xml_str = constr_leaf_value(
            xml_str,
            "reflectBetweenClient",
            self.reflectbetweenclient)
        xml_str = constr_leaf_value(
            xml_str, "reflectChgPath", self.reflectchgpath)
        xml_str = constr_leaf_value(
            xml_str,
            "reflectorClusterId",
            self.reflectorclusterid)
        xml_str = constr_leaf_value(
            xml_str,
            "reflectorClusterIpv4",
            self.reflectorclusteripv4)
        xml_str = constr_leaf_value(
            xml_str, "ribOnlyEnable", self.ribonlyenable)
        xml_str = constr_leaf_value(
            xml_str,
            "ribOnlyPolicyName",
            self.ribonlypolicyname)
        xml_str = constr_leaf_value(xml_str, "routerId", self.routerid)
        xml_str = constr_leaf_value(
            xml_str, "vrfRidAutoSel", self.vrfridautosel)
        xml_str = constr_leaf_value(
            xml_str, "routerIdNeglect", self.routeridneglect)
        xml_str = constr_leaf_value(
            xml_str, "routeSelDelay", self.routeseldelay)
        xml_str = constr_leaf_value(
            xml_str, "rrFilterNumber", self.rrfilternumber)
        xml_str = constr_leaf_value(
            xml_str, "summaryAutomatic", self.summaryautomatic)
        xml_str = constr_leaf_value(
            xml_str, "supernetLabelAdv", self.supernetlabeladv)
        xml_str = constr_leaf_value(
            xml_str, "supernetUniAdv", self.supernetuniadv)
        xml_str = constr_leaf_value(
            xml_str,
            "tunnelSelectorAll",
            self.tunnelselectorall)
        xml_str = constr_leaf_value(
            xml_str,
            "tunnelSelectorName",
            self.tunnelselectorname)
        xml_str = constr_leaf_value(
            xml_str, "vplsAdDisable", self.vplsaddisable)
        xml_str = constr_leaf_value(xml_str, "vplsEnable", self.vplsenable)
        xml_str = constr_leaf_value(xml_str, "vpwsEnable", self.vpwsenable)
        xml_str = constr_leaf_value(
            xml_str, "originatorPrior", self.originatorprior)
        # xml_str = constr_leaf_value(xml_str, "lowestPriority",               self.lowestPriority)
        xml_str = constr_leaf_value(
            xml_str,
            "routeMatchDestination",
            self.routematchdestination)
        xml_str = constr_leaf_value(
            xml_str, "igpMetricIgnore", self.igpmetricignore)
        xml_str = constr_leaf_value(
            xml_str, "defaultLocalPref", self.defaultlocalpref)
        xml_str = constr_leaf_value(
            xml_str, "relayDelayEnable", self.relaydelayenable)
        xml_str = constr_leaf_value(
            xml_str, "uniRtRelayTnl", self.unirtrelaytnl)
        xml_str = constr_leaf_value(
            xml_str, "uniRtTnlSelName", self.unirttnlselname)
        xml_str = constr_leaf_value(xml_str, "activateTag", self.activatetag)
        xml_str = constr_leaf_value(xml_str, "medPlusIgp", self.medplusigp)
        xml_str = constr_leaf_value(
            xml_str, "medMultiplier", self.medmultiplier)
        xml_str = constr_leaf_value(
            xml_str, "igpMultiplier", self.igpmultiplier)
        xml_str = constr_leaf_value(
            xml_str,
            "vrfImportnhpinvariable",
            self.vrfimportnhpinvariable)
        xml_str = constr_leaf_value(
            xml_str,
            "redirectIpRelayTnlEnable",
            self.redirectiprelaytnlenable)
        xml_str = constr_leaf_value(
            xml_str,
            "redirectIpRelayTnlSelName",
            self.redirectiprelaytnlselname)
        xml_str = constr_leaf_value(xml_str, "domainAs", self.domainas)
        xml_str = constr_leaf_value(
            xml_str, "domainIdentifier", self.domainidentifier)
        xml_str = constr_leaf_value(xml_str, "lspMtu", self.lspmtu)
        xml_str = constr_leaf_value(xml_str, "slowPeerDet", self.slowpeerdet)
        xml_str = constr_leaf_value(
            xml_str, "slowPeerThVal", self.slowpeerthval)
        xml_str = constr_leaf_value(xml_str, "vrfAsNum", self.vrfasnum)
        # xml_str = constr_leaf_value(xml_str, "bwBcNonstd",                   self.bwBcNonstd)
        xml_str = constr_leaf_value(xml_str, "timerForEor", self.timerforeor)
        xml_str = constr_leaf_value(
            xml_str, "externalPathNum", self.externalpathnum)
        xml_str = constr_leaf_value(
            xml_str, "rtFilterDisable", self.rtfilterdisable)
        xml_str = constr_leaf_value(
            xml_str,
            "multiHomingNonStdEnable",
            self.multihomingnonstdenable)
        xml_str = constr_leaf_value(
            xml_str, "slowPeerAbDet", self.slowpeerabdet)
        xml_str = constr_leaf_value(
            xml_str, "slowPeerAbThVal", self.slowpeerabthval)
        xml_str = constr_leaf_value(
            xml_str,
            "flowValidationModeAs",
            self.flowvalidationmodeas)
        # xml_str = constr_leaf_value(xml_str, "ibgpIfSensitive",              self.ibgpIfSensitive)
        xml_str = constr_leaf_value(xml_str, "locatorName", self.locatorname)
        xml_str = constr_leaf_value(xml_str, "autoSid", self.autosid)
        xml_str = constr_leaf_value(xml_str, "srIpv6Mode", self.sripv6mode)
        xml_str = constr_leaf_value(xml_str, "aigp", self.aigp)

        # Tail Process
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str += NE_BGP_INSTANCE_TAIL

        # Send xml message and process
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operDesc)
        self.changed = True

    def create_process(self):
        """Create BGP peer  process"""
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """ Merge BGP peer process """
        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete BGP peer Process """
        # Head process
        xml_str = NE_BGP_INSTANCE_HEADER % NE_COMMON_XML_OPERATION_MERGE

        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)

        xml_str = constr_container_process_head(
            xml_str, "bgpVrfAF", NE_COMMON_XML_OPERATION_DELETE)
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str += NE_BGP_INSTANCE_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        # self.updates_cmd.append("undo bgp %s" % self.)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

        self.bgp_VrfAf_info = self.get_bgp_VrfAf()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.bgp_VrfAf_info:
                # create BGP VrfAf
                self.create_process()
            else:
                # merge BGP VrfAf
                self.merge_process()
        elif self.state == "absent":
            if self.bgp_VrfAf_info:
                # remove BGP VrfAf
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: BGP VrfAf does not exist')
        elif self.state == "query":
            if not self.bgp_VrfAf_info:
                self.module.fail_json(msg='Error: BGP VrfAf does not exist')

        if self.state != "query":
            self.get_end_state()
            self.results['end_state'] = self.end_state
            self.results['changed'] = self.changed
            self.results['proposed'] = self.proposed

        self.results['existing'] = self.existing

        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/vrfName
        vrfname=dict(required=True, type='str'),
        aftype=dict(required=True,
                    choices=["ipv4uni", "ipv4multi", "ipv4vpn",
                             "ipv6uni", "ipv6vpn", "ipv4flow",
                             "l2vpnad", "mvpn", "vpntarget", "evpn",
                             "ipv4vpnmcast", "ls", "mdt", "ipv6flow",
                             "vpnv4flow", "ipv4labeluni", "mvpnv6"]),

        # 以下为非KEY 参数
        activerouteadvertise=dict(required=False, choices=['true', 'false']),
        addpathselnum=dict(required=False, type='int'),
        policyextcommenable=dict(required=False, choices=['true', 'false']),
        alwayscomparemed=dict(required=False, choices=['true', 'false']),
        applylabelmode=dict(
            required=False, choices=[
                'perRoute', 'perNexthop']),
        popgo=dict(required=False, choices=['true', 'false']),
        autofrrenable=dict(required=False, choices=['true', 'false']),
        bestexternal=dict(required=False, choices=['true', 'false']),
        enbestrtbiterrdetection=dict(
            required=False, choices=[
                'true', 'false']),
        defaultmed=dict(required=False, type='int'),
        defaultrtimportenable=dict(required=False, choices=['true', 'false']),
        determinmed=dict(required=False, choices=['true', 'false']),
        ebgpifsensitive=dict(required=False, choices=['true', 'false']),
        maximumloadbalance=dict(required=False, type='int'),
        ecmpnexthopchanged=dict(required=False, choices=['true', 'false']),
        labeladvenable=dict(required=False, choices=['true', 'false']),
        # ingressLspProtect         = dict(required=False, choices=['null', 'bgpFrr']),
        maxloadibgpnum=dict(required=False, type='int'),
        ibgpecmpnexthopchanged=dict(required=False, choices=['true', 'false']),
        ebgpecmpnexthopchanged=dict(required=False, choices=['true', 'false']),
        maxloadebgpnum=dict(required=False, type='int'),
        eibgploadbalan=dict(required=False, type='int'),
        eibgpecmpnexthopchanged=dict(
            required=False, choices=[
                'true', 'false']),
        loadbalancingigpmetricignore=dict(
            required=False, choices=['true', 'false']),
        loadbalancingeibgp=dict(required=False, choices=['true', 'false']),
        loadbalancingaspathignore=dict(
            required=False, choices=[
                'true', 'false']),
        loadbalancingaspathrelax=dict(
            required=False, choices=[
                'true', 'false']),
        explicitnull=dict(required=False, choices=['true', 'false']),
        ingresslsppolicyname=dict(required=False, type='str'),
        mednoneasmaximum=dict(required=False, choices=['true', 'false']),
        nexthopdelaytime=dict(required=False, type='int'),
        nocriticalnexthopdelaytime=dict(required=False, type='int'),
        nexthopseldependtype=dict(
            required=False,
            choices=[
                'default',
                'dependTunnel',
                'dependIp']),
        nexthopinheritipcost=dict(required=False, choices=['true', 'false']),
        # nexthopThirdParty         = dict(required=False, choices=['true', 'false']),
        nhprelayroutepolicyname=dict(required=False, type='str'),
        originasvalid=dict(required=False, choices=['true', 'false']),
        allowinvalidas=dict(required=False, choices=['true', 'false']),
        originasvalidenable=dict(required=False, choices=['true', 'false']),
        policyqppbenable=dict(required=False, choices=['true', 'false']),
        policyvpntarget=dict(required=False, choices=['true', 'false']),
        aspathneglect=dict(required=False, choices=['true', 'false']),
        preferenceexternal=dict(required=False, type='int'),
        preferenceinternal=dict(required=False, type='int'),
        preferencelocal=dict(required=False, type='int'),
        prefrencepolicyname=dict(required=False, type='str'),
        qosid=dict(required=False, type='int'),
        qosidpolicyname=dict(required=False, type='str'),
        reflectbetweenclient=dict(required=False, choices=['true', 'false']),
        reflectchgpath=dict(required=False, choices=['true', 'false']),
        reflectorclusterid=dict(required=False, type='int'),
        reflectorclusteripv4=dict(required=False, type='str'),
        ribonlyenable=dict(required=False, choices=['true', 'false']),
        ribonlypolicyname=dict(required=False, type='str'),
        routerid=dict(required=False, type='str'),
        vrfridautosel=dict(required=False, choices=['true', 'false']),
        routeridneglect=dict(required=False, choices=['true', 'false']),
        routeseldelay=dict(required=False, type='int'),
        rrfilternumber=dict(required=False, type='str'),
        summaryautomatic=dict(required=False, choices=['true', 'false']),
        supernetlabeladv=dict(required=False, choices=['true', 'false']),
        supernetuniadv=dict(required=False, choices=['true', 'false']),
        tunnelselectorall=dict(required=False, choices=['true', 'false']),
        tunnelselectorname=dict(required=False, type='str'),
        vplsaddisable=dict(required=False, choices=['true', 'false']),
        vplsenable=dict(required=False, choices=['true', 'false']),
        vpwsenable=dict(required=False, choices=['true', 'false']),
        originatorprior=dict(required=False, choices=['true', 'false']),
        # lowestPriority            = dict(required=False, choices=['true', 'false']),
        routematchdestination=dict(required=False, choices=['true', 'false']),
        igpmetricignore=dict(required=False, choices=['true', 'false']),
        defaultlocalpref=dict(required=False, type='int'),
        relaydelayenable=dict(required=False, choices=['true', 'false']),
        unirtrelaytnl=dict(required=False, choices=['true', 'false']),
        unirttnlselname=dict(required=False, type='str'),
        activatetag=dict(required=False, choices=['true', 'false']),
        medplusigp=dict(required=False, choices=['true', 'false']),
        medmultiplier=dict(required=False, type='int'),
        igpmultiplier=dict(required=False, type='int'),
        vrfimportnhpinvariable=dict(required=False, choices=['true', 'false']),
        redirectiprelaytnlenable=dict(
            required=False, choices=[
                'true', 'false']),
        redirectiprelaytnlselname=dict(required=False, type='str'),
        domainas=dict(required=False, type='str'),
        domainidentifier=dict(required=False, type='str'),
        lspmtu=dict(required=False, type='int'),
        slowpeerdet=dict(required=False, choices=['true', 'false']),
        slowpeerthval=dict(required=False, type='int'),
        vrfasnum=dict(required=False, type='str'),
        timerforeor=dict(required=False, type='int'),
        externalpathnum=dict(required=False, type='int'),
        rtfilterdisable=dict(required=False, choices=['true', 'false']),
        multihomingnonstdenable=dict(
            required=False, choices=[
                'true', 'false']),
        slowpeerabdet=dict(required=False, choices=['true', 'false']),
        slowpeerabthval=dict(required=False, type='int'),
        flowvalidationmodeas=dict(required=False, choices=['true', 'false']),
        # ibgpIfSensitive           = dict(required=False, choices=['true', 'false']),
        locatorname=dict(required=False, type='str'),
        autosid=dict(required=False, choices=['true', 'false']),
        sripv6mode=dict(required=False, choices=['null', 'be']),
        aigp=dict(required=False, choices=['true', 'false']),

        # bitErrDetectionEnable     = dict(required=False, choices=['true', 'false']),
        # bitErrDetectionLocalpref  = dict(required=False, type='int'),
        # bitErrDetectionMed        = dict(required=False, type='int'),
        # bitErrDetectionRtPolicy   = dict(required=False, type='str'),
        # bwBcNonstd                = dict(required=False, choices=['true', 'false']),
        # ingressLspLoadBalancNum   = dict(required=False, type='str'),
        # transitLspLoadBalancNum   = dict(required=False, type='str'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = BgpVrfAf(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
