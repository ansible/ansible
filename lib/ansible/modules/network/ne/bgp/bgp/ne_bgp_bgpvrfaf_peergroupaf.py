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
module: ne_bgp_bgpvrfaf_peergroupaf
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
    ne_bgp_bgpVrfAF_peerGroupAF:
      state: present
      vrf_name: js
      peer_addr: 192.168.10.10
      remote_as: 500
      provider: "{{ cli }}"

  - name: "Config bgp route id"
    ne_bgp_bgpVrfAF_peerGroupAF:
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


class BgpVrfAF_peerGroupAF(object):
    """ Manages BGP peer configuration """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.aftype = self.module.params['aftype']
        self.groupname = self.module.params['groupname']
        self.grouptype = self.module.params['grouptype']
        self.addpathmode = self.module.params['addpathmode']
        self.advaddpathnum = self.module.params['advaddpathnum']
        self.advbestexternal = self.module.params['advbestexternal']
        self.advertisecommunity = self.module.params['advertisecommunity']
        self.advertiseextcommunity = self.module.params['advertiseextcommunity']
        # self.advertiseRemoteNexthop = self.module.params['advertiseRemoteNexthop']
        self.allowasloopenable = self.module.params['allowasloopenable']
        self.allowaslooplimit = self.module.params['allowaslooplimit']
        self.labelroutecapability = self.module.params['labelroutecapability']
        self.checktunnelreachable = self.module.params['checktunnelreachable']
        self.checkwithdrawtype = self.module.params['checkwithdrawtype']
        self.defaultrtadvenable = self.module.params['defaultrtadvenable']
        self.defaultrtadvpolicy = self.module.params['defaultrtadvpolicy']
        self.defaultrtmatchmode = self.module.params['defaultrtmatchmode']
        self.discardextcommunity = self.module.params['discardextcommunity']
        self.expmode = self.module.params['expmode']
        self.exportacl6nameornum = self.module.params['exportacl6nameornum']
        self.exportaclnameornum = self.module.params['exportaclnameornum']
        self.exportpref6filtname = self.module.params['exportpref6filtname']
        self.exportpreffiltname = self.module.params['exportpreffiltname']
        self.exportrtpolicyname = self.module.params['exportrtpolicyname']
        # self.ignoreBitError         = self.module.params['ignoreBitError']
        self.importacl6nameornum = self.module.params['importacl6nameornum']
        self.importaclnameornum = self.module.params['importaclnameornum']
        self.importpref6filtname = self.module.params['importpref6filtname']
        self.importpreffiltname = self.module.params['importpreffiltname']
        self.importrtpolicyname = self.module.params['importrtpolicyname']
        self.ipprefixorfenable = self.module.params['ipprefixorfenable']
        self.isnonstdipprefixmod = self.module.params['isnonstdipprefixmod']
        self.orfmode = self.module.params['orfmode']
        self.orftype = self.module.params['orftype']
        self.keepallroutes = self.module.params['keepallroutes']
        self.loadbalancingenable = self.module.params['loadbalancingenable']
        self.loadbalancingignoreas = self.module.params['loadbalancingignoreas']
        self.loadbalancingrelaxas = self.module.params['loadbalancingrelaxas']
        self.nexthopconfigure = self.module.params['nexthopconfigure']
        self.originasvalid = self.module.params['originasvalid']
        self.preferredvalue = self.module.params['preferredvalue']
        self.publicasonly = self.module.params['publicasonly']
        self.publicasonlyforce = self.module.params['publicasonlyforce']
        self.publicasonlylimited = self.module.params['publicasonlylimited']
        self.publicasonlyreplace = self.module.params['publicasonlyreplace']
        self.publicasonlyskippeeras = self.module.params['publicasonlyskippeeras']
        self.reflectclient = self.module.params['reflectclient']
        self.routelimit = self.module.params['routelimit']
        self.routelimitidletimeout = self.module.params['routelimitidletimeout']
        self.routelimitpercent = self.module.params['routelimitpercent']
        self.routelimittype = self.module.params['routelimittype']
        self.acceptprefixenable = self.module.params['acceptprefixenable']
        self.rtupdtinterval = self.module.params['rtupdtinterval']
        self.soostring = self.module.params['soostring']
        self.substituteasenable = self.module.params['substituteasenable']
        # self.upeEnable              = self.module.params['upeEnable']
        self.vplsaddisable = self.module.params['vplsaddisable']
        self.vplsenable = self.module.params['vplsenable']
        self.vpwsenable = self.module.params['vpwsenable']
        self.exportaspathnameornum = self.module.params['exportaspathnameornum']
        self.importaspathnameornum = self.module.params['importaspathnameornum']
        # self.redirectIP             = self.module.params['redirectIP']
        # self.redirectIPVaildation   = self.module.params['redirectIPVaildation']
        self.advertiseirb = self.module.params['advertiseirb']
        self.advertisearp = self.module.params['advertisearp']
        # self.rtpDistributeEnable    = self.module.params['rtpDistributeEnable']
        self.aigp = self.module.params['aigp']
        self.advertiseencaptype = self.module.params['advertiseencaptype']
        self.reoriginatedrtenable = self.module.params['reoriginatedrtenable']
        self.maciprtenable = self.module.params['maciprtenable']
        self.macrtenable = self.module.params['macrtenable']
        self.iprtenable = self.module.params['iprtenable']
        self.vpnv4rtenable = self.module.params['vpnv4rtenable']
        # self.macIpRtEnableDc        = self.module.params['macIpRtEnableDc']
        # self.ipRtEnableDc           = self.module.params['ipRtEnableDc']
        self.allowclustercap = self.module.params['allowclustercap']
        self.allowclusternum = self.module.params['allowclusternum']
        self.advcmulmatnhp = self.module.params['advcmulmatnhp']
        self.esadcompatible = self.module.params['esadcompatible']
        self.splitgroupname = self.module.params['splitgroupname']
        # self.prefixSidEnable        = self.module.params['prefixSidEnable']
        # self.reoriginatedRtEnableDc = self.module.params['reoriginatedRtEnableDc']
        self.updatepktstandardcompatible = self.module.params['updatepktstandardcompatible']

        self.state = self.module.params['state']
        # BGP peer
        self.bgp_VrfAF_GroupAF_info = dict()

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
        self.proposed["groupname"] = self.groupname

        if self.grouptype is not None:
            self.proposed["grouptype"] = self.grouptype
        if self.addpathmode is not None:
            self.proposed["addpathmode"] = self.addpathmode
        if self.advaddpathnum is not None:
            self.proposed["advaddpathnum"] = self.advaddpathnum
        if self.advbestexternal is not None:
            self.proposed["advbestexternal"] = self.advbestexternal
        if self.advertisecommunity is not None:
            self.proposed["advertisecommunity"] = self.advertisecommunity
        if self.advertiseextcommunity is not None:
            self.proposed["advertiseextcommunity"] = self.advertiseextcommunity
        # if self.advertiseRemoteNexthop is not None:
        #    self.proposed["advertiseRemoteNexthop"] = self.advertiseRemoteNexthop
        if self.allowasloopenable is not None:
            self.proposed["allowasloopenable"] = self.allowasloopenable
        if self.allowaslooplimit is not None:
            self.proposed["allowaslooplimit"] = self.allowaslooplimit
        if self.labelroutecapability is not None:
            self.proposed["labelroutecapability"] = self.labelroutecapability
        if self.checktunnelreachable is not None:
            self.proposed["checktunnelreachable"] = self.checktunnelreachable
        if self.checkwithdrawtype is not None:
            self.proposed["checkwithdrawtype"] = self.checkwithdrawtype
        if self.defaultrtadvenable is not None:
            self.proposed["defaultrtadvenable"] = self.defaultrtadvenable
        if self.defaultrtadvpolicy is not None:
            self.proposed["defaultrtadvpolicy"] = self.defaultrtadvpolicy
        if self.defaultrtmatchmode is not None:
            self.proposed["defaultrtmatchmode"] = self.defaultrtmatchmode
        if self.discardextcommunity is not None:
            self.proposed["discardextcommunity"] = self.discardextcommunity
        if self.expmode is not None:
            self.proposed["expmode"] = self.expmode
        if self.exportacl6nameornum is not None:
            self.proposed["exportacl6nameornum"] = self.exportacl6nameornum
        if self.exportaclnameornum is not None:
            self.proposed["exportaclnameornum"] = self.exportaclnameornum
        if self.exportpref6filtname is not None:
            self.proposed["exportpref6filtname"] = self.exportpref6filtname
        if self.exportpreffiltname is not None:
            self.proposed["exportpreffiltname"] = self.exportpreffiltname
        if self.exportrtpolicyname is not None:
            self.proposed["exportrtpolicyname"] = self.exportrtpolicyname
        # if self.ignoreBitError is not None:
        #    self.proposed["ignoreBitError"]         = self.ignoreBitError
        if self.importacl6nameornum is not None:
            self.proposed["importacl6nameornum"] = self.importacl6nameornum
        if self.importaclnameornum is not None:
            self.proposed["importaclnameornum"] = self.importaclnameornum
        if self.importpref6filtname is not None:
            self.proposed["importpref6filtname"] = self.importpref6filtname
        if self.importpreffiltname is not None:
            self.proposed["importpreffiltname"] = self.importpreffiltname
        if self.importrtpolicyname is not None:
            self.proposed["importrtpolicyname"] = self.importrtpolicyname
        if self.ipprefixorfenable is not None:
            self.proposed["ipprefixorfenable"] = self.ipprefixorfenable
        if self.isnonstdipprefixmod is not None:
            self.proposed["isnonstdipprefixmod"] = self.isnonstdipprefixmod
        if self.orfmode is not None:
            self.proposed["orfmode"] = self.orfmode
        if self.orftype is not None:
            self.proposed["orftype"] = self.orftype
        if self.keepallroutes is not None:
            self.proposed["keepallroutes"] = self.keepallroutes
        if self.loadbalancingenable is not None:
            self.proposed["loadbalancingenable"] = self.loadbalancingenable
        if self.loadbalancingignoreas is not None:
            self.proposed["loadbalancingignoreas"] = self.loadbalancingignoreas
        if self.loadbalancingrelaxas is not None:
            self.proposed["loadbalancingrelaxas"] = self.loadbalancingrelaxas
        if self.nexthopconfigure is not None:
            self.proposed["nexthopconfigure"] = self.nexthopconfigure
        if self.originasvalid is not None:
            self.proposed["originasvalid"] = self.originasvalid
        if self.preferredvalue is not None:
            self.proposed["preferredvalue"] = self.preferredvalue
        if self.publicasonly is not None:
            self.proposed["publicasonly"] = self.publicasonly
        if self.publicasonlyforce is not None:
            self.proposed["publicasonlyforce"] = self.publicasonlyforce
        if self.publicasonlylimited is not None:
            self.proposed["publicasonlylimited"] = self.publicasonlylimited
        if self.publicasonlyreplace is not None:
            self.proposed["publicasonlyreplace"] = self.publicasonlyreplace
        if self.publicasonlyskippeeras is not None:
            self.proposed["publicasonlyskippeeras"] = self.publicasonlyskippeeras
        if self.reflectclient is not None:
            self.proposed["reflectclient"] = self.reflectclient
        if self.routelimit is not None:
            self.proposed["routelimit"] = self.routelimit
        if self.routelimitidletimeout is not None:
            self.proposed["routelimitidletimeout"] = self.routelimitidletimeout
        if self.routelimitpercent is not None:
            self.proposed["routelimitpercent"] = self.routelimitpercent
        if self.routelimittype is not None:
            self.proposed["routelimittype"] = self.routelimittype
        if self.acceptprefixenable is not None:
            self.proposed["acceptprefixenable"] = self.acceptprefixenable
        if self.rtupdtinterval is not None:
            self.proposed["rtupdtinterval"] = self.rtupdtinterval
        if self.soostring is not None:
            self.proposed["soostring"] = self.soostring
        if self.substituteasenable is not None:
            self.proposed["substituteasenable"] = self.substituteasenable
        # if self.upeEnable is not None:
        #    self.proposed["upeEnable"]              = self.upeEnable
        if self.vplsaddisable is not None:
            self.proposed["vplsaddisable"] = self.vplsaddisable
        if self.vplsenable is not None:
            self.proposed["vplsenable"] = self.vplsenable
        if self.vpwsenable is not None:
            self.proposed["vpwsenable"] = self.vpwsenable
        if self.exportaspathnameornum is not None:
            self.proposed["exportaspathnameornum"] = self.exportaspathnameornum
        if self.importaspathnameornum is not None:
            self.proposed["importaspathnameornum"] = self.importaspathnameornum
        # if self.redirectIP is not None:
        #    self.proposed["redirectIP"]             = self.redirectIP
        # if self.redirectIPVaildation is not None:
        #    self.proposed["redirectIPVaildation"]   = self.redirectIPVaildation
        if self.advertiseirb is not None:
            self.proposed["advertiseirb"] = self.advertiseirb
        if self.advertisearp is not None:
            self.proposed["advertisearp"] = self.advertisearp
        # if self.rtpDistributeEnable is not None:
        #    self.proposed["rtpDistributeEnable"]    = self.rtpDistributeEnable
        if self.aigp is not None:
            self.proposed["aigp"] = self.aigp
        if self.advertiseencaptype is not None:
            self.proposed["advertiseencaptype"] = self.advertiseencaptype
        if self.reoriginatedrtenable is not None:
            self.proposed["reoriginatedrtenable"] = self.reoriginatedrtenable
        if self.maciprtenable is not None:
            self.proposed["maciprtenable"] = self.maciprtenable
        if self.macrtenable is not None:
            self.proposed["macrtenable"] = self.macrtenable
        if self.iprtenable is not None:
            self.proposed["iprtenable"] = self.iprtenable
        if self.vpnv4rtenable is not None:
            self.proposed["vpnv4rtenable"] = self.vpnv4rtenable
        # if self.macIpRtEnableDc is not None:
        #    self.proposed["macIpRtEnableDc"]        = self.macIpRtEnableDc
        # if self.ipRtEnableDc is not None:
        #    self.proposed["ipRtEnableDc"]           = self.ipRtEnableDc
        if self.allowclustercap is not None:
            self.proposed["allowclustercap"] = self.allowclustercap
        if self.allowclusternum is not None:
            self.proposed["allowclusternum"] = self.allowclusternum
        if self.advcmulmatnhp is not None:
            self.proposed["advcmulmatnhp"] = self.advcmulmatnhp
        if self.esadcompatible is not None:
            self.proposed["esadcompatible"] = self.esadcompatible
        if self.splitgroupname is not None:
            self.proposed["splitgroupname"] = self.splitgroupname
        # if self.prefixSidEnable is not None:
        #    self.proposed["prefixSidEnable"]        = self.prefixSidEnable
        # if self.reoriginatedRtEnableDc is not None:
        #    self.proposed["reoriginatedRtEnableDc"] = self.reoriginatedRtEnableDc
        if self.updatepktstandardcompatible is not None:
            self.proposed["updatepktstandardcompatible"] = self.updatepktstandardcompatible

        self.proposed["state"] = self.state

    def get_existing(self):
        """Get existing info"""

        if not self.bgp_VrfAF_GroupAF_info or len(
                self.bgp_VrfAF_GroupAF_info) == 0:
            return

        self.existing["vrfname"] = self.vrfname
        self.existing["aftype"] = self.aftype
        self.existing["peerGroupAFs"] = self.bgp_VrfAF_GroupAF_info["peerGroupAFs"]

    def get_end_state(self):
        """Get end state info"""

        bgp_VrfAF_GroupAF_info = self.get_bgp_VrfAf_peerGroupAF()
        if not bgp_VrfAF_GroupAF_info or len(bgp_VrfAF_GroupAF_info) == 0:
            return

        self.end_state["vrfname"] = self.vrfname
        self.end_state["aftype"] = self.aftype
        self.end_state["peerGroupAFs"] = bgp_VrfAF_GroupAF_info["peerGroupAFs"]

    def get_bgp_VrfAf_peerGroupAF(self):
        """ Get BGP peer informaton to the dictionary."""

        # Head info
        get_xml_str = NE_COMMON_XML_GET_BGP_VRF_HEAD
        get_xml_str = constr_leaf_value(get_xml_str, "vrfName", self.vrfname)
        get_xml_str = constr_container_head(get_xml_str, "bgpVrfAFs")
        get_xml_str = constr_container_head(get_xml_str, "bgpVrfAF")
        get_xml_str = constr_leaf_value(get_xml_str, "afType", self.aftype)
        get_xml_str = constr_container_head(get_xml_str, "peerGroupAFs")
        get_xml_str = constr_container_head(get_xml_str, "peerGroupAF")

        # Body info
        get_xml_str = constr_leaf_value(
            get_xml_str, "groupName", self.groupname)

        # get_xml_str = constr_leaf_novalue(get_xml_str, "groupType")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "addPathMode")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advAddPathNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advBestExternal")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advertiseCommunity")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advertiseExtCommunity")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advertiseRemoteNexthop")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "allowAsLoopEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "allowAsLoopLimit")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "labelRouteCapability")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "checkTunnelReachable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "checkWithdrawType")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "defaultRtAdvEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "defaultRtAdvPolicy")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "defaultRtMatchMode")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "discardExtCommunity")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "expMode")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "exportAcl6NameOrNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "exportAclNameOrNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "exportPref6FiltName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "exportPrefFiltName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "exportRtPolicyName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ignoreBitError")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "importAcl6NameOrNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "importAclNameOrNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "importPref6FiltName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "importPrefFiltName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "importRtPolicyName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ipprefixOrfEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "isNonstdIpprefixMod")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "orfMode")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "orftype")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "keepAllRoutes")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "loadBalancingEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "loadBalancingIgnoreAs")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "loadBalancingRelaxAs")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "nextHopConfigure")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "originAsValid")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "preferredValue")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "publicAsOnly")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "publicAsOnlyForce")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "publicAsOnlyLimited")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "publicAsOnlyReplace")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "publicAsOnlySkipPeerAs")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "reflectClient")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "routeLimit")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "routeLimitIdleTimeout")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "routeLimitPercent")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "routeLimitType")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "acceptPrefixEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "rtUpdtInterval")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "soostring")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "substituteAsEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "upeEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vplsAdDisable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vplsEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vpwsEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "exportAsPathNameOrNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "importAsPathNameOrNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "redirectIP")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "redirectIPVaildation")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advertiseIrb")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advertiseArp")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "rtpDistributeEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "aigp")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advertiseEncapType")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "reoriginatedRtEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "macIpRtEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "macRtEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ipRtEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "vpnv4RtEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "macIpRtEnableDc")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "ipRtEnableDc")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "allowClusterCap")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "allowClusterNum")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "advCmulMatNhp")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "esadCompatible")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "splitGroupName")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "prefixSidEnable")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "reoriginatedRtEnableDc")
        # get_xml_str = constr_leaf_novalue(get_xml_str, "updatePktStandardCompatible")

        # Tail info
        get_xml_str = constr_container_tail(get_xml_str, "peerGroupAF")
        get_xml_str = constr_container_tail(get_xml_str, "peerGroupAFs")
        get_xml_str = constr_container_tail(get_xml_str, "bgpVrfAF")
        get_xml_str = constr_container_tail(get_xml_str, "bgpVrfAFs")
        get_xml_str += NE_COMMON_XML_GET_BGP_VRF_TAIL

        ret_xml_str = get_nc_config(self.module, get_xml_str)
        if "<data/>" in ret_xml_str:
            return None

        bgp_VrfAF_GroupAF_info = dict()

        ret_xml_str = ret_xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        root = ElementTree.fromstring(ret_xml_str)
        peerGroupAFs = root.findall(
            "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerGroupAFs/peerGroupAF")
        if peerGroupAFs is None or len(peerGroupAFs) == 0:
            return None

        # VrfName information

        bgpVrf = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf")
        if bgpVrf is None or len(bgpVrf) == 0:
            return None

        for vrf in bgpVrf:
            if vrf.tag in ["vrfName"]:
                bgp_VrfAF_GroupAF_info[vrf.tag.lower()] = vrf.text

        # bgp VrfAF information
        bgpVrfAF = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF")
        if bgpVrfAF is None or len(bgpVrfAF) == 0:
            return None

        for vrfAF in bgpVrfAF:
            if vrfAF.tag in ["afType"]:
                bgp_VrfAF_GroupAF_info[vrfAF.tag.lower()] = vrfAF.text

        bgp_VrfAF_GroupAF_info["peerGroupAFs"] = list()
        for peerGroupAF in peerGroupAFs:
            peerGroupAFs_dict = dict()
            for ele in peerGroupAF:
                if ele.tag in [
                    "groupName", "groupType", "addPathMode", "advAddPathNum", "advBestExternal",
                    "advertiseCommunity", "advertiseExtCommunity", "advertiseRemoteNexthop", "allowAsLoopEnable",
                    "allowAsLoopLimit", "labelRouteCapability", "checkTunnelReachable", "checkWithdrawType",
                    "defaultRtAdvEnable", "defaultRtAdvPolicy", "defaultRtMatchMode", "discardExtCommunity",
                    "expMode", "exportAcl6NameOrNum", "exportAclNameOrNum", "exportPref6FiltName",
                    "exportPrefFiltName", "exportRtPolicyName", "ignoreBitError", "importAcl6NameOrNum",
                    "importAclNameOrNum", "importPref6FiltName", "importPrefFiltName", "importRtPolicyName",
                    "ipprefixOrfEnable", "isNonstdIpprefixMod", "orfMode", "orftype", "keepAllRoutes",
                    "loadBalancingEnable", "loadBalancingIgnoreAs", "loadBalancingRelaxAs", "nextHopConfigure",
                    "originAsValid", "peerGroupName", "preferredValue", "publicAsOnly",
                    "publicAsOnlyForce", "publicAsOnlyLimited", "publicAsOnlyReplace", "publicAsOnlySkipPeerAs",
                    "reflectClient", "routeLimit", "routeLimitIdleTimeout", "routeLimitPercent", "routeLimitType",
                    "acceptPrefixEnable", "rtUpdtInterval", "soostring",
                    "substituteAsEnable", "upeEnable", "validationDisable", "vplsAdDisable", "vplsEnable",
                    "vpwsEnable", "exportAsPathNameOrNum", "importAsPathNameOrNum", "redirectIP", "redirectIPVaildation", "advertiseIrb",
                    "advertiseArp", "rtpDistributeEnable", "aigp", "advertiseEncapType", "reoriginatedRtEnable",
                    "macIpRtEnable", "macRtEnable", "ipRtEnable", "vpnv4RtEnable", "macIpRtEnableDc", "ipRtEnableDc",
                    "allowClusterCap", "allowClusterNum", "advCmulMatNhp", "esadCompatible", "splitGroupName", "prefixSidEnable",
                    "staticGrTimerValue", "updatePktStandardCompatible"
                ]:
                    peerGroupAFs_dict[ele.tag.lower()] = ele.text

            bgp_VrfAF_GroupAF_info["peerGroupAFs"].append(peerGroupAFs_dict)
        return bgp_VrfAF_GroupAF_info

    def common_process(self, operType, operDesc):
        """Common process BGP peer."""
        # Head process
        xml_str = NE_BGP_INSTANCE_HEADER % NE_COMMON_XML_OPERATION_MERGE

        # Process vrfname and groupname is the key, must input
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_head(xml_str, "bgpVrfAFs")
        xml_str = constr_container_head(xml_str, "bgpVrfAF")
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
        xml_str = constr_container_process_head(
            xml_str, "peerGroupAF", operType)
        xml_str = constr_leaf_value(xml_str, "groupName", self.groupname)

        # Body process
        xml_str = constr_leaf_value(xml_str, "groupType", self.grouptype)
        xml_str = constr_leaf_value(xml_str, "addPathMode", self.addpathmode)
        xml_str = constr_leaf_value(
            xml_str, "advAddPathNum", self.advaddpathnum)
        xml_str = constr_leaf_value(
            xml_str, "advBestExternal", self.advbestexternal)
        xml_str = constr_leaf_value(
            xml_str,
            "advertiseCommunity",
            self.advertisecommunity)
        xml_str = constr_leaf_value(
            xml_str,
            "advertiseExtCommunity",
            self.advertiseextcommunity)
        # xml_str=constr_leaf_value(xml_str, "advertiseRemoteNexthop", self.advertiseRemoteNexthop)
        xml_str = constr_leaf_value(
            xml_str,
            "allowAsLoopEnable",
            self.allowasloopenable)
        xml_str = constr_leaf_value(
            xml_str, "allowAsLoopLimit", self.allowaslooplimit)
        xml_str = constr_leaf_value(
            xml_str,
            "labelRouteCapability",
            self.labelroutecapability)
        xml_str = constr_leaf_value(
            xml_str,
            "checkTunnelReachable",
            self.checktunnelreachable)
        xml_str = constr_leaf_value(
            xml_str,
            "checkWithdrawType",
            self.checkwithdrawtype)
        xml_str = constr_leaf_value(
            xml_str,
            "defaultRtAdvEnable",
            self.defaultrtadvenable)
        xml_str = constr_leaf_value(
            xml_str,
            "defaultRtAdvPolicy",
            self.defaultrtadvpolicy)
        xml_str = constr_leaf_value(
            xml_str,
            "defaultRtMatchMode",
            self.defaultrtmatchmode)
        xml_str = constr_leaf_value(
            xml_str,
            "discardExtCommunity",
            self.discardextcommunity)
        xml_str = constr_leaf_value(xml_str, "expMode", self.expmode)
        xml_str = constr_leaf_value(
            xml_str,
            "exportAcl6NameOrNum",
            self.exportacl6nameornum)
        xml_str = constr_leaf_value(
            xml_str,
            "exportAclNameOrNum",
            self.exportaclnameornum)
        xml_str = constr_leaf_value(
            xml_str,
            "exportPref6FiltName",
            self.exportpref6filtname)
        xml_str = constr_leaf_value(
            xml_str,
            "exportPrefFiltName",
            self.exportpreffiltname)
        xml_str = constr_leaf_value(
            xml_str,
            "exportRtPolicyName",
            self.exportrtpolicyname)
        # xml_str=constr_leaf_value(xml_str, "ignoreBitError", self.ignoreBitError)
        xml_str = constr_leaf_value(
            xml_str,
            "importAcl6NameOrNum",
            self.importacl6nameornum)
        xml_str = constr_leaf_value(
            xml_str,
            "importAclNameOrNum",
            self.importaclnameornum)
        xml_str = constr_leaf_value(
            xml_str,
            "importPref6FiltName",
            self.importpref6filtname)
        xml_str = constr_leaf_value(
            xml_str,
            "importPrefFiltName",
            self.importpreffiltname)
        xml_str = constr_leaf_value(
            xml_str,
            "importRtPolicyName",
            self.importrtpolicyname)
        xml_str = constr_leaf_value(
            xml_str,
            "ipprefixOrfEnable",
            self.ipprefixorfenable)
        xml_str = constr_leaf_value(
            xml_str,
            "isNonstdIpprefixMod",
            self.isnonstdipprefixmod)
        xml_str = constr_leaf_value(xml_str, "orfMode", self.orfmode)
        xml_str = constr_leaf_value(xml_str, "orftype", self.orftype)
        xml_str = constr_leaf_value(
            xml_str, "keepAllRoutes", self.keepallroutes)
        xml_str = constr_leaf_value(
            xml_str,
            "loadBalancingEnable",
            self.loadbalancingenable)
        xml_str = constr_leaf_value(
            xml_str,
            "loadBalancingIgnoreAs",
            self.loadbalancingignoreas)
        xml_str = constr_leaf_value(
            xml_str,
            "loadBalancingRelaxAs",
            self.loadbalancingrelaxas)
        xml_str = constr_leaf_value(
            xml_str, "nextHopConfigure", self.nexthopconfigure)
        xml_str = constr_leaf_value(
            xml_str, "originAsValid", self.originasvalid)
        xml_str = constr_leaf_value(
            xml_str, "preferredValue", self.preferredvalue)
        xml_str = constr_leaf_value(xml_str, "publicAsOnly", self.publicasonly)
        xml_str = constr_leaf_value(
            xml_str,
            "publicAsOnlyForce",
            self.publicasonlyforce)
        xml_str = constr_leaf_value(
            xml_str,
            "publicAsOnlyLimited",
            self.publicasonlylimited)
        xml_str = constr_leaf_value(
            xml_str,
            "publicAsOnlyReplace",
            self.publicasonlyreplace)
        xml_str = constr_leaf_value(
            xml_str,
            "publicAsOnlySkipPeerAs",
            self.publicasonlyskippeeras)
        xml_str = constr_leaf_value(
            xml_str, "reflectClient", self.reflectclient)
        xml_str = constr_leaf_value(xml_str, "routeLimit", self.routelimit)
        xml_str = constr_leaf_value(
            xml_str,
            "routeLimitIdleTimeout",
            self.routelimitidletimeout)
        xml_str = constr_leaf_value(
            xml_str,
            "routeLimitPercent",
            self.routelimitpercent)
        xml_str = constr_leaf_value(
            xml_str, "routeLimitType", self.routelimittype)
        xml_str = constr_leaf_value(
            xml_str,
            "acceptPrefixEnable",
            self.acceptprefixenable)
        xml_str = constr_leaf_value(
            xml_str, "rtUpdtInterval", self.rtupdtinterval)
        xml_str = constr_leaf_value(xml_str, "soostring", self.soostring)
        xml_str = constr_leaf_value(
            xml_str,
            "substituteAsEnable",
            self.substituteasenable)
        # xml_str=constr_leaf_value(xml_str, "upeEnable", self.upeEnable)
        xml_str = constr_leaf_value(
            xml_str, "vplsAdDisable", self.vplsaddisable)
        xml_str = constr_leaf_value(xml_str, "vplsEnable", self.vplsenable)
        xml_str = constr_leaf_value(xml_str, "vpwsEnable", self.vpwsenable)
        xml_str = constr_leaf_value(
            xml_str,
            "exportAsPathNameOrNum",
            self.exportaspathnameornum)
        xml_str = constr_leaf_value(
            xml_str,
            "importAsPathNameOrNum",
            self.importaspathnameornum)
        # xml_str=constr_leaf_value(xml_str, "redirectIP", self.redirectIP)
        # xml_str=constr_leaf_value(xml_str, "redirectIPVaildation", self.redirectIPVaildation)
        xml_str = constr_leaf_value(xml_str, "advertiseIrb", self.advertiseirb)
        xml_str = constr_leaf_value(xml_str, "advertiseArp", self.advertisearp)
        # xml_str=constr_leaf_value(xml_str, "rtpDistributeEnable", self.rtpDistributeEnable)
        xml_str = constr_leaf_value(xml_str, "aigp", self.aigp)
        xml_str = constr_leaf_value(
            xml_str,
            "advertiseEncapType",
            self.advertiseencaptype)
        xml_str = constr_leaf_value(
            xml_str,
            "reoriginatedRtEnable",
            self.reoriginatedrtenable)
        xml_str = constr_leaf_value(
            xml_str, "macIpRtEnable", self.maciprtenable)
        xml_str = constr_leaf_value(xml_str, "macRtEnable", self.macrtenable)
        xml_str = constr_leaf_value(xml_str, "ipRtEnable", self.iprtenable)
        xml_str = constr_leaf_value(
            xml_str, "vpnv4RtEnable", self.vpnv4rtenable)
        # xml_str=constr_leaf_value(xml_str, "macIpRtEnableDc", self.macIpRtEnableDc)
        # xml_str=constr_leaf_value(xml_str, "ipRtEnableDc", self.ipRtEnableDc)
        xml_str = constr_leaf_value(
            xml_str, "allowClusterCap", self.allowclustercap)
        xml_str = constr_leaf_value(
            xml_str, "allowClusterNum", self.allowclusternum)
        xml_str = constr_leaf_value(
            xml_str, "advCmulMatNhp", self.advcmulmatnhp)
        xml_str = constr_leaf_value(
            xml_str, "esadCompatible", self.esadcompatible)
        xml_str = constr_leaf_value(
            xml_str, "splitGroupName", self.splitgroupname)
        # xml_str=constr_leaf_value(xml_str, "prefixSidEnable", self.prefixSidEnable)
        # xml_str=constr_leaf_value(xml_str, "reoriginatedRtEnableDc", self.reoriginatedRtEnableDc)
        xml_str = constr_leaf_value(
            xml_str,
            "updatePktStandardCompatible",
            self.updatepktstandardcompatible)

        # Tail Process
        xml_str = constr_container_process_tail(xml_str, "peerGroupAF")
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
        """Delete BGP VrfAF peerGroupAF  Process """
        # Head process
        xml_str = NE_BGP_INSTANCE_HEADER % NE_COMMON_XML_OPERATION_MERGE

        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)

        xml_str = constr_container_process_head(
            xml_str, "bgpVrfAF", NE_COMMON_XML_OPERATION_MERGE)
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)

        xml_str = constr_container_process_head(
            xml_str, "peerGroupAF", NE_COMMON_XML_OPERATION_DELETE)
        xml_str = constr_leaf_value(xml_str, "groupName", self.groupname)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "peerGroupAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str += NE_BGP_INSTANCE_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        # self.updates_cmd.append("undo bgp %s" % self.)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

        self.bgp_VrfAF_GroupAF_info = self.get_bgp_VrfAf_peerGroupAF()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.bgp_VrfAF_GroupAF_info:
                # create BGP VrfAf
                self.create_process()
            else:
                # merge BGP VrfAf
                self.merge_process()
        elif self.state == "absent":
            # if self.bgp_VrfAF_GroupAF_info:
                # # remove BGP VrfAf
            self.delete_process()
            # else:
            # self.module.fail_json(msg='Error: BGP VrfAf does not exist')
        # elif self.state == "query":
            # if not self.bgp_VrfAF_GroupAF_info:
            # self.module.fail_json(msg='Error: BGP VrfAf does not exist')

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
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/vrfName
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/afType
        vrfname=dict(required=True, type='str'),
        aftype=dict(required=True,
                    choices=["ipv4uni", "ipv4multi", "ipv4vpn",
                             "ipv6uni", "ipv6vpn", "ipv4flow",
                             "l2vpnad", "mvpn", "vpntarget", "evpn",
                             "ipv4vpnmcast", "ls", "mdt", "ipv6flow",
                             "vpnv4flow", "ipv4labeluni", "mvpnv6"]),
        groupname=dict(required=True, type='str'),

        grouptype=dict(required=False, choices=['ibgp', 'ebgp']),
        addpathmode=dict(
            required=False,
            choices=[
                'null',
                'both',
                'send',
                'receive']),
        advaddpathnum=dict(required=False, type='int'),
        advbestexternal=dict(required=False, choices=['true', 'false']),
        advertisecommunity=dict(required=False, choices=['true', 'false']),
        advertiseextcommunity=dict(required=False, choices=['true', 'false']),
        # advertiseRemoteNexthop = dict(required=False, choices=['true', 'false']),
        allowasloopenable=dict(required=False, choices=['true', 'false']),
        allowaslooplimit=dict(required=False, type='int'),
        labelroutecapability=dict(required=False, choices=['true', 'false']),
        checktunnelreachable=dict(required=False, choices=['true', 'false']),
        checkwithdrawtype=dict(required=False, choices=['true', 'false']),
        defaultrtadvenable=dict(required=False, choices=['true', 'false']),
        defaultrtadvpolicy=dict(required=False, type='str'),
        defaultrtmatchmode=dict(
            required=False, choices=[
                'null', 'matchall', 'matchany']),
        discardextcommunity=dict(required=False, choices=['true', 'false']),
        expmode=dict(required=False, choices=['null', 'pipe', 'uniform']),
        exportacl6nameornum=dict(required=False, type='str'),
        exportaclnameornum=dict(required=False, type='str'),
        exportpref6filtname=dict(required=False, type='str'),
        exportpreffiltname=dict(required=False, type='str'),
        exportrtpolicyname=dict(required=False, type='str'),
        # ignoreBitError         = dict(required=False, choices=['true', 'false']),
        importacl6nameornum=dict(required=False, type='str'),
        importaclnameornum=dict(required=False, type='str'),
        importpref6filtname=dict(required=False, type='str'),
        importpreffiltname=dict(required=False, type='str'),
        importrtpolicyname=dict(required=False, type='str'),
        ipprefixorfenable=dict(required=False, choices=['true', 'false']),
        isnonstdipprefixmod=dict(required=False, choices=['true', 'false']),
        orfmode=dict(
            required=False,
            choices=[
                'null',
                'both',
                'send',
                'receive']),
        orftype=dict(required=False, type='int'),
        keepallroutes=dict(required=False, choices=['true', 'false']),
        loadbalancingenable=dict(required=False, choices=['true', 'false']),
        loadbalancingignoreas=dict(required=False, choices=['true', 'false']),
        loadbalancingrelaxas=dict(required=False, choices=['true', 'false']),
        nexthopconfigure=dict(
            required=False, choices=[
                'null', 'local', 'invariable']),
        originasvalid=dict(required=False, choices=['true', 'false']),
        preferredvalue=dict(required=False, type='int'),
        publicasonly=dict(required=False, choices=['true', 'false']),
        publicasonlyforce=dict(required=False, choices=['true', 'false']),
        publicasonlylimited=dict(required=False, choices=['true', 'false']),
        publicasonlyreplace=dict(required=False, choices=['true', 'false']),
        publicasonlyskippeeras=dict(required=False, choices=['true', 'false']),
        reflectclient=dict(required=False, choices=['true', 'false']),
        routelimit=dict(required=False, type='int'),
        routelimitidletimeout=dict(required=False, type='int'),
        routelimitpercent=dict(required=False, choices=['true', 'false']),
        routelimittype=dict(
            required=False,
            choices=[
                'noparameter',
                'alertOnly',
                'idleForever',
                'idleTimeout']),
        acceptprefixenable=dict(required=False, choices=['true', 'false']),
        rtupdtinterval=dict(required=False, type='int'),
        soostring=dict(required=False, type='str'),
        substituteasenable=dict(required=False, choices=['true', 'false']),
        # upeEnable              = dict(required=False, choices=['true', 'false']),
        vplsaddisable=dict(required=False, choices=['true', 'false']),
        vplsenable=dict(required=False, choices=['true', 'false']),
        vpwsenable=dict(required=False, choices=['true', 'false']),
        exportaspathnameornum=dict(required=False, type='str'),
        importaspathnameornum=dict(required=False, type='str'),
        advertiseirb=dict(required=False, choices=['true', 'false']),
        advertisearp=dict(required=False, choices=['true', 'false']),
        aigp=dict(required=False, choices=['true', 'false']),
        advertiseencaptype=dict(required=False, choices=['vxlan', 'mpls']),
        reoriginatedrtenable=dict(required=False, choices=['true', 'false']),
        maciprtenable=dict(required=False, choices=['true', 'false']),
        macrtenable=dict(required=False, choices=['true', 'false']),
        iprtenable=dict(required=False, choices=['true', 'false']),
        vpnv4rtenable=dict(required=False, choices=['true', 'false']),
        # macIpRtEnableDc        = dict(required=False, choices=['true', 'false']),
        # ipRtEnableDc           = dict(required=False, choices=['true', 'false']),
        allowclustercap=dict(required=False, choices=['true', 'false']),
        allowclusternum=dict(required=False, type='int'),
        advcmulmatnhp=dict(required=False, choices=['true', 'false']),
        esadcompatible=dict(required=False, choices=['true', 'false']),
        splitgroupname=dict(required=False, type='str'),
        # reoriginatedRtEnableDc = dict(required=False, choices=['true', 'false']),
        updatepktstandardcompatible=dict(
            required=False, choices=[
                'true', 'false']),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = BgpVrfAF_peerGroupAF(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
