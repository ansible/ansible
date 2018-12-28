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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_ldp_globalpara
version_added: "2.6"
short_description: Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
description:
    - Manages configuration of MPLS LDP global parameters on HUAWEI netengine switches.
author: Haoliansheng (@netengine-Ansible)
options:
    mtusignalingenable:
        description:
            - Enables the private MTU signaling.
        required: false
        default: null
        choices:['true', 'false']
    mtusignalingapplytlvenable:
        description:
            - Enables the standard MTU signaling.
        required: false
        default: null
        choices:['true', 'false']
    lsptriggermode:
        description:
            - Specifies a triggering mode for establishing LSPs by LDP. The value can be: \
            1. All mode (in which LDP is triggered by all static routes and IGP routes to establish LSPs); \
            2. Host mode (in which LDP is triggered by 32- or 128-bit IP routes to establish LSPs); \
            3. None mode (in which LDP is not triggered to establish LSPs); \
            4. IP-prefix mode (in which LDP is triggered by the IP address prefix list to establish LSPs.
        required: false
        default: null
        choices:['all', 'host', 'none', 'ip-prefix']
    lspipprefixname:
        description:
            - Specifies or clear the IP prefix triggering mode,LDP is triggered to establish or to clear LSPs by IP address prefixes, \
            The IP prefix is a string of 1 to 169 characters, spaces not supported.
        required: false
        default: null
    proxyegrlspdisable:
        description:
            - Disable establish proxy LDP LSP.
        required: false
        default: null
        choices:['true', 'false']
    grenable:
        description:
            - Specifies the LDP GR capability. Enabling or disabling of GR will cause the re-establishment of all LDP sessions.
        required: false
        default: null
        choices:['true', 'false']
    reconnecttime:
        description:
            - Specifies the value of the LDP session reconnection timer in seconds.
        required: false
        default: null

    recoverytime:
        description:
            - Specifies the value of the LSP recovery timer (s).in seconds.
        required: false
        default: null
    peerlivetime:
        description:
            - Specifies the value of the neighbor keeplive timer (s).in seconds.
        required: false
        default: null
    backoffinittime:
        description:
            - Specifies the init value of the exponential backoff timer (s).in seconds.
        required: false
        default: null
    backoffmaxtime:
        description:
            - Specifies the maximum value of the exponential backoff Timer(s).in seconds.
        required: false
        default: null
    bgplabel:
        description:
            - Trigger LDP alloc label for BGP label route.
        required: false
        default: null
        choices:['true', 'false']
    bgpipprefixname:
        description:
            - Trigger policy when LDP alloc label for BGP label route.
        required: false
        default: null
    announcementenable:
        description:
            - Whether dynamic announcement is enabled for LDP.
        required: false
        default: null
    biterrdetectlevel:
        description:
            - Config LDP bit error level.
        required: false
        default: null
    mldpP2mpEnable:
        description:
            - Whether P2MP for mLDP is enabled.
        required: false
        default: null
    mldpmakebeforebreak:
        description:
            - Whether MBB capability is enabled for mLDP.
        required: false
        default: null
        choices:['true', 'false']
    mldprecursivefec:
        description:
            - Whether Recursive FEC is enabled for mLDP.
        required: false
        default: null
        choices:['true', 'false']
    trappubssn:
        description:
            - Config Trap LDP Session
        required: false
        default: null
        choices:['true', 'false']
    grnodelflag:
        description:
            - The modification of GR parameters not affect established sessions, only affect new created sessions.
        required: false
        default: null
        choices:['true', 'false']
    mldpp2mplinkfrrenable:
        description:
            - MLDP P2MP Frr Link Proteciton.
        required: false
        default: null
        choices:['true', 'false']
    mldpmbbswitchdelaytime:
        description:
            - MLDP MBB Switch Delay Time.
        required: false
        default: null
    mldpmbbwaitacktime:
        description:
            - MLDP MBB ACK Notification Wait Time.
        required: false
        default: null
    entropylabelenable:
        description:
            - Delivers LDP entrpy label capability.
        required: false
        default: null
        choices:['true', 'false']
    mldpp2mptoponameall:
        description:
            - Delivers MLDP P2MP Topology Capability.
        required: false
        default: null
    srinterworklsptrigmode:
        description:
            - SR LSP Triggering Mode.
        required: false
        default: null
        choices:['none', 'host']
'''

EXAMPLES = '''
- name: NE device mpls ldp module test
  hosts: mydevice
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli
  connection: netconf
  gather_facts: no

  tasks:

  - name: "Merge mpls ldp Global paras "
    ne_ldp_globalpara: state=present  backoffinittime=16 backoffmaxtime=121 provider="{{ cli }}"
    register: data
    ignore_errors: false

  - name: "Query mpls ldp Global paras "
    ne_ldp_globalpara: state=query  provider="{{ cli }}"
    register: data
    ignore_errors: false

'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample:  {
        "announcementenable": "true",
        "state": "present"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: {
         "announcementenable": "true",
        "backoffinittime": "15",
        "backoffmaxtime": "120",
        "bgplabel": "false",
        "entropylabelenable": "false",
        "grenable": "false",
        "grnodelflag": "false",
        "lsptriggermode": "host",
        "mldpp2mpenable": "false",
        "mtusignalingapplytlvenable": "false",
        "mtusignalingenable": "true",
        "protpacketsuppressdisable": "false",
        "proxyegrlspdisable": "false",
        "srinterworklsptrigmode": "none",
        "trappubssn": "false"
        }

end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: {
        "announcementenable": "false",
        "backoffinittime": "15",
        "backoffmaxtime": "120",
        "bgplabel": "false",
        "entropylabelenable": "false",
        "grenable": "false",
        "grnodelflag": "false",
        "lsptriggermode": "host",
        "mldpp2mpenable": "false",
        "mtusignalingapplytlvenable": "false",
        "mtusignalingenable": "true",
        "protpacketsuppressdisable": "false",
        "proxyegrlspdisable": "false",
        "srinterworklsptrigmode": "none",
        "trappubssn": "false"
    },
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import sys
import copy
import socket

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_TAIL
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_TAIL

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_value
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_novalue
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_tail
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_tail

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module:
version_added: "2.6"
short_description:
description:
    -
author: Haoliansheng (@CloudEngine-Ansible)
notes:
options:
'''

EXAMPLES = '''
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample:
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class MPLS_ldpGlobalPara(object):
    """Manages configuration of a ldpGlobalPara instance.
       Xpath: /mpls/mplsLdp/ldpGlobalPara
    """

    def __init__(self, argument_spec):
        """constructor"""

        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.mtusignalingenable = self.module.params['mtusignalingenable']
        self.mtusignalingapplytlvenable = self.module.params['mtusignalingapplytlvenable']
        self.lsptriggermode = self.module.params['lsptriggermode']
        self.lspipprefixname = self.module.params['lspipprefixname']
        self.proxyegrlspdisable = self.module.params['proxyegrlspdisable']
        self.grnodelflag = self.module.params['grnodelflag']
        self.grenable = self.module.params['grenable']
        self.reconnecttime = self.module.params['reconnecttime']
        self.recoverytime = self.module.params['recoverytime']
        self.peerlivetime = self.module.params['peerlivetime']
        self.backoffinittime = self.module.params['backoffinittime']
        self.backoffmaxtime = self.module.params['backoffmaxtime']
        self.bgplabel = self.module.params['bgplabel']
        self.bgpipprefixname = self.module.params['bgpipprefixname']
        self.announcementenable = self.module.params['announcementenable']
        self.biterrdetectlevel = self.module.params['biterrdetectlevel']
        self.mldpp2mpenable = self.module.params['mldpp2mpenable']
        self.mldpmakebeforebreak = self.module.params['mldpmakebeforebreak']
        self.mldprecursivefec = self.module.params['mldprecursivefec']
        self.mldpp2mplinkfrrenable = self.module.params['mldpp2mplinkfrrenable']
        self.mldpmbbswitchdelaytime = self.module.params['mldpmbbswitchdelaytime']
        self.mldplabelwithdrawdlytime = self.module.params['mldplabelwithdrawdlytime']
        self.mldpmbbwaitacktime = self.module.params['mldpmbbwaitacktime']
        self.entropylabelenable = self.module.params['entropylabelenable']
        self.mldpp2mptoponameall = self.module.params['mldpp2mptoponameall']
        self.protpacketsuppressdisable = self.module.params['protpacketsuppressdisable']
        self.srinterworklsptrigmode = self.module.params['srinterworklsptrigmode']
        self.trappubssn = self.module.params['trappubssn']

        self.state = self.module.params['state']
        # ldpGlobalPara info
        self.ldpGlobalPara_info = dict()

        # state
        self.changed = False
        # self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()
    # FUNC __init__ END

    def init_module(self):
        """init module"""

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
    # FUNC init_module END

    def check_params(self):
        """check all input params"""
    # FUNC check_params END

    def check_response(self, xml_str, xml_name):
        """Check if operation is succeed."""
        if "<ok/>" not in xml_str:
            self.module.fail_json(
                msg='Error: %s failed.' % xml_name)
    # FUNC check_response END

    def get_ldpGlobalPara_dict(self):
        """get a ldpGlobalPara dict"""

        ldpGlobalPara_info = dict()

        conf_str = NE_COMMON_XML_GET_MPLS_HEAD
        conf_str = constr_container_head(conf_str, "mplsLdp")
        conf_str = constr_container_head(conf_str, "ldpGlobalPara")

        conf_str = constr_leaf_novalue(conf_str, "mtuSignalingEnable")
        conf_str = constr_leaf_novalue(conf_str, "mtuSignalingApplyTLVEnable")
        conf_str = constr_leaf_novalue(conf_str, "lspTriggerMode")
        conf_str = constr_leaf_novalue(conf_str, "lspIpPrefixName")
        conf_str = constr_leaf_novalue(conf_str, "proxyEgrLspDisable")
        conf_str = constr_leaf_novalue(conf_str, "grNoDelFlag")
        conf_str = constr_leaf_novalue(conf_str, "grEnable")
        conf_str = constr_leaf_novalue(conf_str, "reconnectTime")
        conf_str = constr_leaf_novalue(conf_str, "recoveryTime")
        conf_str = constr_leaf_novalue(conf_str, "peerLiveTime")
        conf_str = constr_leaf_novalue(conf_str, "backOffInitTime")
        conf_str = constr_leaf_novalue(conf_str, "backOffMaxTime")
        conf_str = constr_leaf_novalue(conf_str, "bgpLabel")
        conf_str = constr_leaf_novalue(conf_str, "bgpIpPrefixName")
        conf_str = constr_leaf_novalue(conf_str, "announcementEnable")
        conf_str = constr_leaf_novalue(conf_str, "bitErrDetectLevel")
        conf_str = constr_leaf_novalue(conf_str, "mldpP2mpEnable")
        conf_str = constr_leaf_novalue(conf_str, "mldpMakeBeforeBreak")
        conf_str = constr_leaf_novalue(conf_str, "mldpRecursiveFec")
        conf_str = constr_leaf_novalue(conf_str, "mldpP2mpLinkFrrEnable")
        conf_str = constr_leaf_novalue(conf_str, "mldpMbbSwitchDelayTime")
        conf_str = constr_leaf_novalue(conf_str, "mldpLabelWithdrawDlyTime")
        conf_str = constr_leaf_novalue(conf_str, "mldpMbbWaitAckTime")
        conf_str = constr_leaf_novalue(conf_str, "entropyLabelEnable")
        conf_str = constr_leaf_novalue(conf_str, "trapPubSsn")
        conf_str = constr_leaf_novalue(conf_str, "mldpP2mpTopoNameAll")
        conf_str = constr_leaf_novalue(conf_str, "srInterworkLspTrigMode")
        conf_str = constr_leaf_novalue(conf_str, "protPacketSuppressDisable")
        conf_str = constr_container_tail(conf_str, "ldpGlobalPara")

        conf_str = constr_container_tail(conf_str, "mplsLdp")
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return ldpGlobalPara_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        root = ElementTree.fromstring(xml_str)
        ldpGlobalPara = root.find("mpls/mplsLdp/ldpGlobalPara")
        if len(ldpGlobalPara) != 0:
            for para in ldpGlobalPara:
                if para.tag in ['announcementEnable', 'backOffInitTime', 'backOffMaxTime', 'bgpIpPrefixName',
                                'bgpLabel', 'bitErrDetectLevel', 'distributedInstIdDeleting', 'distributedInstNum',
                                'entropyLabelEnable', 'grEnable', 'grNoDelFlag', 'loopDetect',
                                'lspIpPrefixName', 'lspTriggerMode', 'mldpLabelWithdrawDlyTime',
                                'mldpMakeBeforeBreak', 'mldpMbbSwitchDelayTime', 'mldpMbbWaitAckTime',
                                'mldpP2mpEnable', 'mldpP2mpLinkFrrEnable', 'mldpP2mpTopoNameAll',
                                'mldpRecursiveFec', 'mtuSignalingApplyTLVEnable', 'mtuSignalingEnable',
                                'pathVectors', 'peerLiveTime', 'protPacketSuppressDisable', 'proxyEgrLspDisable',
                                'reconnectTime', 'recoveryTime', 'srInterworkLspTrigMode', 'trapPubSsn'
                                ]:
                    ldpGlobalPara_info[para.tag.lower()] = para.text

        return ldpGlobalPara_info
    # FUNC get_ldpGlobalPara_dict END

    def get_proposed(self):
        """get proposed info"""

        if self.mtusignalingenable is not None:
            self.proposed["mtusignalingenable"] = self.mtusignalingenable

        if self.mtusignalingapplytlvenable is not None:
            self.proposed["mtusignalingapplytlvenable"] = self.mtusignalingapplytlvenable

        if self.lsptriggermode is not None:
            self.proposed["lsptriggermode"] = self.lsptriggermode

        if self.lspipprefixname is not None:
            self.proposed["lspipprefixname"] = self.lspipprefixname

        if self.proxyegrlspdisable is not None:
            self.proposed["proxyegrlspdisable"] = self.proxyegrlspdisable

        if self.grnodelflag is not None:
            self.proposed["grnodelflag"] = self.grnodelflag

        if self.grenable is not None:
            self.proposed["grenable"] = self.grenable

        if self.reconnecttime is not None:
            self.proposed["reconnecttime"] = self.reconnecttime

        if self.recoverytime is not None:
            self.proposed["recoverytime"] = self.recoverytime

        if self.peerlivetime is not None:
            self.proposed["peerlivetime"] = self.peerlivetime

        if self.backoffinittime is not None:
            self.proposed["backoffinittime"] = self.backoffinittime

        if self.backoffmaxtime is not None:
            self.proposed["backoffmaxtime"] = self.backoffmaxtime

        if self.bgplabel is not None:
            self.proposed["bgplabel"] = self.bgplabel

        if self.bgpipprefixname is not None:
            self.proposed["bgpipprefixname"] = self.bgpipprefixname

        if self.announcementenable is not None:
            self.proposed["announcementenable"] = self.announcementenable

        if self.biterrdetectlevel is not None:
            self.proposed["biterrdetectlevel"] = self.biterrdetectlevel

        if self.mldpp2mpenable is not None:
            self.proposed["mldpp2mpenable"] = self.mldpp2mpenable

        if self.mldpmakebeforebreak is not None:
            self.proposed["mldpmakebeforebreak"] = self.mldpmakebeforebreak

        if self.mldprecursivefec is not None:
            self.proposed["mldprecursivefec"] = self.mldprecursivefec

        if self.mldpp2mplinkfrrenable is not None:
            self.proposed["mldpp2mplinkfrrenable"] = self.mldpp2mplinkfrrenable

        if self.mldpmbbswitchdelaytime is not None:
            self.proposed["mldpmbbswitchdelaytime"] = self.mldpmbbswitchdelaytime

        if self.mldplabelwithdrawdlytime is not None:
            self.proposed["mldplabelwithdrawdlytime"] = self.mldplabelwithdrawdlytime

        if self.mldpmbbwaitacktime is not None:
            self.proposed["mldpmbbwaitacktime"] = self.mldpmbbwaitacktime

        if self.entropylabelenable is not None:
            self.proposed["entropylabelenable"] = self.entropylabelenable

        if self.mldpp2mptoponameall is not None:
            self.proposed["mldpp2mptoponameall"] = self.mldpp2mptoponameall

        if self.protpacketsuppressdisable is not None:
            self.proposed["protpacketsuppressdisable"] = self.protpacketsuppressdisable
        if self.srinterworklsptrigmode is not None:
            self.proposed["srinterworklsptrigmode"] = self.srinterworklsptrigmode
        if self.trappubssn is not None:
            self.proposed["trappubssn"] = self.trappubssn
        self.proposed["state"] = self.state

    # FUNC get_proposed END

    def get_existing(self):
        """get existing info"""
        if not self.ldpGlobalPara_info:
            return

        self.existing = copy.deepcopy(self.ldpGlobalPara_info)
    # FUNC get_existing END

    def get_end_state(self):
        """get end state info"""

        ldpGlobalPara_info = self.get_ldpGlobalPara_dict()
        if not ldpGlobalPara_info:
            return

        self.end_state = copy.deepcopy(ldpGlobalPara_info)
    # FUNC get_end_state END

    def merge_process(self, operation_Desc):
        """Merge  process"""

        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD

        xml_str = constr_container_head(xml_str, "mplsLdp")
        xml_str += "<ldpGlobalPara xc:operation=\"merge\">"

        xml_str = constr_leaf_value(xml_str, "mtuSignalingEnable", self.mtusignalingenable)
        xml_str = constr_leaf_value(xml_str, "mtuSignalingApplyTLVEnable", self.mtusignalingapplytlvenable)
        xml_str = constr_leaf_value(xml_str, "lspTriggerMode", self.lsptriggermode)
        xml_str = constr_leaf_value(xml_str, "lspIpPrefixName", self.lspipprefixname)
        xml_str = constr_leaf_value(xml_str, "proxyEgrLspDisable", self.proxyegrlspdisable)
        xml_str = constr_leaf_value(xml_str, "grNoDelFlag", self.grnodelflag)
        xml_str = constr_leaf_value(xml_str, "grEnable", self.grenable)
        xml_str = constr_leaf_value(xml_str, "reconnectTime", self.reconnecttime)
        xml_str = constr_leaf_value(xml_str, "recoveryTime", self.peerlivetime)
        xml_str = constr_leaf_value(xml_str, "backOffInitTime", self.backoffinittime)
        xml_str = constr_leaf_value(xml_str, "backOffMaxTime", self.backoffmaxtime)
        xml_str = constr_leaf_value(xml_str, "bgpLabel", self.bgplabel)
        xml_str = constr_leaf_value(xml_str, "bgpIpPrefixName", self.bgpipprefixname)
        xml_str = constr_leaf_value(xml_str, "announcementEnable", self.announcementenable)
        xml_str = constr_leaf_value(xml_str, "bitErrDetectLevel", self.biterrdetectlevel)
        xml_str = constr_leaf_value(xml_str, "mldpP2mpEnable", self.mldpp2mpenable)
        xml_str = constr_leaf_value(xml_str, "mldpMakeBeforeBreak", self.mldpmakebeforebreak)
        xml_str = constr_leaf_value(xml_str, "mldpRecursiveFec", self.mldprecursivefec)
        xml_str = constr_leaf_value(xml_str, "mldpP2mpLinkFrrEnable", self.mldpp2mplinkfrrenable)
        xml_str = constr_leaf_value(xml_str, "mldpMbbSwitchDelayTime", self.mldpmbbswitchdelaytime)
        xml_str = constr_leaf_value(xml_str, "mldpLabelWithdrawDlyTime", self.mldplabelwithdrawdlytime)
        xml_str = constr_leaf_value(xml_str, "mldpMbbWaitAckTime", self.mldpmbbwaitacktime)
        xml_str = constr_leaf_value(xml_str, "entropyLabelEnable", self.entropylabelenable)
        xml_str = constr_leaf_value(xml_str, "trapPubSsn", self.trappubssn)
        xml_str = constr_leaf_value(xml_str, "mldpP2mpTopoNameAll", self.mldpp2mptoponameall)
        xml_str = constr_leaf_value(xml_str, "srInterworkLspTrigMode", self.srinterworklsptrigmode)
        xml_str = constr_leaf_value(xml_str, "protPacketSuppressDisable", self.protpacketsuppressdisable)

        xml_str = constr_container_tail(xml_str, "ldpGlobalPara")
        xml_str = constr_container_tail(xml_str, "mplsLdp")
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)

        self.check_response(recv_xml, operation_Desc)

        self.changed = True

    def work(self):
        """worker"""

        self.check_params()

        self.ldpGlobalPara_info = self.get_ldpGlobalPara_dict()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if not self.ldpGlobalPara_info:
                self.module.fail_json(msg='Error ldpGlobalPara instance does not exist.')
            else:
                self.merge_process("MERGE_PROCESS")
        else:
            if not self.ldpGlobalPara_info:
                self.module.fail_json(msg='Error: ldpGlobalPara instance does not exist')

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        # if self.changed:
        #    self.results['updates'] = self.updates_cmd
        # else:
        #    self.results['updates'] = list()

        self.module.exit_json(**self.results)

# CLASS MPLS_ldpGlobalPara END


def main():
    """mian flow"""

    argument_spec = dict(
        announcementenable=dict(required=False, choices=['true', 'false']),
        backoffinittime=dict(required=False, type='int'),
        backoffmaxtime=dict(required=False, type='int'),
        bgpipprefixname=dict(required=False, type='str'),
        bgplabel=dict(required=False, choices=['true', 'false']),
        biterrdetectlevel=dict(required=False, type='int'),
        entropylabelenable=dict(required=False, choices=['true', 'false']),
        grenable=dict(required=False, choices=['true', 'false']),
        grnodelflag=dict(required=False, choices=['true', 'false']),
        lspipprefixname=dict(required=False, type='str'),
        lsptriggermode=dict(required=False, choices=['all', 'host', 'none', 'ip-prefix']),
        mldplabelwithdrawdlytime=dict(required=False, type='int'),
        mldpmakebeforebreak=dict(required=False, choices=['true', 'false']),
        mldpmbbswitchdelaytime=dict(required=False, type='int'),
        mldpmbbwaitacktime=dict(required=False, type='int'),
        mldpp2mpenable=dict(required=False, choices=['true', 'false']),
        mldpp2mplinkfrrenable=dict(required=False, choices=['true', 'false']),
        mldpp2mptoponameall=dict(required=False, type='str'),
        mldprecursivefec=dict(required=False, choices=['true', 'false']),
        mtusignalingapplytlvenable=dict(required=False, choices=['true', 'false']),
        mtusignalingenable=dict(required=False, choices=['true', 'false']),
        peerlivetime=dict(required=False, type='int'),
        protpacketsuppressdisable=dict(required=False, choices=['true', 'false']),
        proxyegrlspdisable=dict(required=False, choices=['true', 'false']),
        reconnecttime=dict(required=False, type='int'),
        recoverytime=dict(required=False, type='int'),
        srinterworklsptrigmode=dict(required=False, choices=['none', 'host']),
        trappubssn=dict(required=False, choices=['true', 'false']),
        state=dict(required=False, default='present', choices=['present', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_ldpGlobalPara(argument_spec)
    module.work()
# FUNC main() END


if __name__ == '__main__':
    main()
