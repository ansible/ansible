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
module: ne_bgp_bgppeer
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

- name: netengine BGP peer group  test
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

  - name: "Config bgp peer group "
    ne_bgp_bgpPeerGroup:
      state: present
      vrf_name: js
      peer_addr: 192.168.10.10
      remote_as: 500
      provider: "{{ cli }}"

  - name: "Config bgp route id"
    ne_bgp_bgpPeerGroup:
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


class BgpPeerGroup(object):
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
        self.groupas = self.module.params['groupas']
        self.conventional = self.module.params['conventional']
        self.description = self.module.params['description']
        self.dualas = self.module.params['dualas']
        self.prependfakeas = self.module.params['prependfakeas']
        self.fakeas = self.module.params['fakeas']
        self.prependglobalas = self.module.params['prependglobalas']
        self.connretrytime = self.module.params['connretrytime']
        self.checkfirstas = self.module.params['checkfirstas']
        self.connectmode = self.module.params['connectmode']
        self.holdtime = self.module.params['holdtime']
        self.keepalivetime = self.module.params['keepalivetime']
        self.minholdtime = self.module.params['minholdtime']
        self.isignore = self.module.params['isignore']
        self.keychainname = self.module.params['keychainname']
        self.localifaddress = self.module.params['localifaddress']
        self.localifname = self.module.params['localifname']
        self.mplslocalifnetdisable = self.module.params['mplslocalifnetdisable']
        self.ebgpmaxhop = self.module.params['ebgpmaxhop']
        self.fourbyteas = self.module.params['fourbyteas']
        self.pswdtype = self.module.params['pswdtype']
        self.pswdciphertext = self.module.params['pswdciphertext']
        self.routerefresh = self.module.params['routerefresh']
        self.tcpmss = self.module.params['tcpmss']
        self.trackdelaytime = self.module.params['trackdelaytime']
        self.trackingenable = self.module.params['trackingenable']
        self.validttlhops = self.module.params['validttlhops']
        self.islogchange = self.module.params['islogchange']
        self.state = self.module.params['state']

        # BGP peerGroup
        self.bgp_peerGroup_info = dict()

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

        self.proposed['vrfname'] = self.vrfname
        self.proposed['aftype'] = self.aftype
        self.proposed['groupname'] = self.groupname
        self.proposed['grouptype'] = self.grouptype

        if self.groupas is not None:
            self.proposed['groupas'] = self.groupas
        if self.conventional is not None:
            self.proposed['conventional'] = self.conventional
        if self.description is not None:
            self.proposed['description'] = self.description
        if self.dualas is not None:
            self.proposed['dualas'] = self.dualas
        if self.prependfakeas is not None:
            self.proposed['prependfakeas'] = self.prependfakeas
        if self.fakeas is not None:
            self.proposed['fakeas'] = self.fakeas
        if self.prependglobalas is not None:
            self.proposed['prependglobalas'] = self.prependglobalas
        if self.connretrytime is not None:
            self.proposed['connretrytime'] = self.connretrytime
        if self.checkfirstas is not None:
            self.proposed['checkfirstas'] = self.checkfirstas
        if self.connectmode is not None:
            self.proposed['connectmode'] = self.connectmode
        if self.holdtime is not None:
            self.proposed['holdtime'] = self.holdtime
        if self.keepalivetime is not None:
            self.proposed['keepalivetime'] = self.keepalivetime
        if self.minholdtime is not None:
            self.proposed['minholdtime'] = self.minholdtime
        if self.isignore is not None:
            self.proposed['isignore'] = self.isignore
        if self.keychainname is not None:
            self.proposed['keychainname'] = self.keychainname
        if self.localifaddress is not None:
            self.proposed['localifaddress'] = self.localifaddress
        if self.localifname is not None:
            self.proposed['localifname'] = self.localifname
        if self.mplslocalifnetdisable is not None:
            self.proposed['mplslocalifnetdisable'] = self.mplslocalifnetdisable
        if self.ebgpmaxhop is not None:
            self.proposed['ebgpmaxhop'] = self.ebgpmaxhop
        if self.fourbyteas is not None:
            self.proposed['fourbyteas'] = self.fourbyteas
        if self.pswdtype is not None:
            self.proposed['pswdtype'] = self.pswdtype
        if self.pswdciphertext is not None:
            self.proposed['pswdciphertext'] = self.pswdciphertext
        if self.routerefresh is not None:
            self.proposed['routerefresh'] = self.routerefresh
        if self.tcpmss is not None:
            self.proposed['tcpmss'] = self.tcpmss
        if self.trackdelaytime is not None:
            self.proposed['trackdelaytime'] = self.trackdelaytime
        if self.trackingenable is not None:
            self.proposed['trackingenable'] = self.trackingenable
        if self.validttlhops is not None:
            self.proposed['validttlhops'] = self.validttlhops
        if self.islogchange is not None:
            self.proposed['islogchange'] = self.islogchange

        self.proposed['state'] = self.state

    def get_existing(self):
        """Get existing info"""

        if not self.bgp_peerGroup_info or len(self.bgp_peerGroup_info) == 0:
            return

        self.existing["vrfname"] = self.vrfname
        self.existing["bgpPeerGroups"] = self.bgp_peerGroup_info["bgpPeerGroups"]

    def get_end_state(self):
        """Get end state info"""

        bgp_peerGroup_info = self.get_bgp_peerGroup()
        if not bgp_peerGroup_info or len(bgp_peerGroup_info) == 0:
            return

        self.end_state["vrfname"] = self.vrfname
        self.end_state["bgpPeerGroups"] = bgp_peerGroup_info["bgpPeerGroups"]

    def get_bgp_peerGroup(self):
        """ Get BGP peer group informaton to the dictionary."""
        bgp_peer_Group_info = dict()

        # Head info
        get_xml_str = NE_COMMON_XML_GET_BGP_VRF_HEAD
        get_xml_str = constr_leaf_value(get_xml_str, "vrfName", self.vrfname)
        get_xml_str = constr_container_head(get_xml_str, "bgpPeerGroups")
        get_xml_str = constr_container_head(get_xml_str, "bgpPeerGroup")

        # Body info
        get_xml_str = constr_leaf_value(get_xml_str, "afType", self.aftype)
        get_xml_str = constr_leaf_value(
            get_xml_str, "groupName", self.groupname)
        get_xml_str = constr_leaf_novalue(get_xml_str, "groupType")
        get_xml_str = constr_leaf_novalue(get_xml_str, "groupAs")
        get_xml_str = constr_leaf_novalue(get_xml_str, "conventional")
        get_xml_str = constr_leaf_novalue(get_xml_str, "description")
        get_xml_str = constr_leaf_novalue(get_xml_str, "dualAs")
        get_xml_str = constr_leaf_novalue(get_xml_str, "prependFakeAs")
        get_xml_str = constr_leaf_novalue(get_xml_str, "fakeAs")
        get_xml_str = constr_leaf_novalue(get_xml_str, "prependGlobalAs")
        get_xml_str = constr_leaf_novalue(get_xml_str, "connRetryTime")
        get_xml_str = constr_leaf_novalue(get_xml_str, "checkFirstAs")
        get_xml_str = constr_leaf_novalue(get_xml_str, "connectMode")
        get_xml_str = constr_leaf_novalue(get_xml_str, "holdTime")
        get_xml_str = constr_leaf_novalue(get_xml_str, "keepAliveTime")
        get_xml_str = constr_leaf_novalue(get_xml_str, "minHoldTime")
        get_xml_str = constr_leaf_novalue(get_xml_str, "isIgnore")
        get_xml_str = constr_leaf_novalue(get_xml_str, "keyChainName")
        get_xml_str = constr_leaf_novalue(get_xml_str, "localIfAddress")
        get_xml_str = constr_leaf_novalue(get_xml_str, "localIfName")
        get_xml_str = constr_leaf_novalue(get_xml_str, "mplsLocalIfnetDisable")
        get_xml_str = constr_leaf_novalue(get_xml_str, "ebgpMaxHop")
        get_xml_str = constr_leaf_novalue(get_xml_str, "fourByteAs")
        get_xml_str = constr_leaf_novalue(get_xml_str, "pswdType")
        get_xml_str = constr_leaf_novalue(get_xml_str, "pswdCipherText")
        get_xml_str = constr_leaf_novalue(get_xml_str, "routeRefresh")
        get_xml_str = constr_leaf_novalue(get_xml_str, "tcpMSS")
        get_xml_str = constr_leaf_novalue(get_xml_str, "trackDelayTime")
        get_xml_str = constr_leaf_novalue(get_xml_str, "trackingEnable")
        get_xml_str = constr_leaf_novalue(get_xml_str, "validTtlHops")
        get_xml_str = constr_leaf_novalue(get_xml_str, "isLogChange")

        # Tail info
        get_xml_str = constr_container_tail(get_xml_str, "bgpPeerGroup")
        get_xml_str = constr_container_tail(get_xml_str, "bgpPeerGroups")
        get_xml_str += NE_COMMON_XML_GET_BGP_VRF_TAIL

        # No record return , 没有找到记录直接返回
        ret_xml_str = get_nc_config(self.module, get_xml_str)
        if "<data/>" in ret_xml_str:
            return bgp_peer_Group_info

        # 替换整理返回报文
        ret_xml_str = ret_xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # 处理获取具体数据输出
        # VrfName information
        root = ElementTree.fromstring(ret_xml_str)
        bgpVrf = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf")

        if len(bgpVrf) != 0 and bgpVrf is not None:
            for vrf in bgpVrf:
                if vrf.tag in ["vrfName"]:
                    bgp_peer_Group_info[vrf.tag.lower()] = vrf.text

        # bgp peer information
        bgp_peer_Group_info["bgpPeerGroups"] = list()
        bgpPeerGroups = root.findall(
            "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup")

        if len(bgpPeerGroups) != 0 and bgpPeerGroups is not None:
            for bgpPeerGroup in bgpPeerGroups:
                bgpPeerGroup_dict = dict()
                for ele in bgpPeerGroup:
                    if ele.tag in [
                        "afType", "groupName", "groupType", "groupAs", "conventional",
                        "description", "dualAs", "prependFakeAs", "fakeAs", "prependGlobalAs",
                        "connRetryTime", "checkFirstAs", "connectMode", "holdTime", "keepAliveTime",
                        "minHoldTime", "isIgnore", "keyChainName", "localIfAddress", "localIfName",
                        "mplsLocalIfnetDisable" "ebgpMaxHop", "fourByteAs", "pswdType", "pswdCipherText",
                        "routeRefresh", "tcpMSS", "trackDelayTime", "trackingEnable", "validTtlHops", "isLogChange"
                    ]:
                        bgpPeerGroup_dict[ele.tag.lower()] = ele.text
                bgp_peer_Group_info["bgpPeerGroups"].append(bgpPeerGroup_dict)

        return bgp_peer_Group_info

    def common_process(self, operType, operDesc):
        """Common process BGP peer."""
        # Head process
        xml_str = NE_BGP_INSTANCE_HEADER % NE_COMMON_XML_OPERATION_MERGE

        # Process vrfname and aftype, groupname is the key, must input
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)

        xml_str = constr_container_process_head(
            xml_str, "bgpPeerGroup", operType)
        # Body process
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
        xml_str = constr_leaf_value(xml_str, "groupName", self.groupname)
        xml_str = constr_leaf_value(xml_str, "groupType", self.grouptype)
        xml_str = constr_leaf_value(xml_str, "groupAs", self.groupas)
        xml_str = constr_leaf_value(xml_str, "conventional", self.conventional)
        xml_str = constr_leaf_value(xml_str, "description", self.description)
        xml_str = constr_leaf_value(xml_str, "dualAs", self.dualas)
        xml_str = constr_leaf_value(
            xml_str, "prependFakeAs", self.prependfakeas)
        xml_str = constr_leaf_value(xml_str, "fakeAs", self.fakeas)
        xml_str = constr_leaf_value(
            xml_str, "prependGlobalAs", self.prependglobalas)
        xml_str = constr_leaf_value(
            xml_str, "connRetryTime", self.connretrytime)
        xml_str = constr_leaf_value(xml_str, "checkFirstAs", self.checkfirstas)
        xml_str = constr_leaf_value(xml_str, "connectMode", self.connectmode)
        xml_str = constr_leaf_value(xml_str, "holdTime", self.holdtime)
        xml_str = constr_leaf_value(
            xml_str, "keepAliveTime", self.keepalivetime)
        xml_str = constr_leaf_value(xml_str, "minHoldTime", self.minholdtime)
        xml_str = constr_leaf_value(xml_str, "isIgnore", self.isignore)
        xml_str = constr_leaf_value(xml_str, "keyChainName", self.keychainname)
        xml_str = constr_leaf_value(
            xml_str, "localIfAddress", self.localifaddress)
        xml_str = constr_leaf_value(xml_str, "localIfName", self.localifname)
        xml_str = constr_leaf_value(
            xml_str,
            "mplsLocalIfnetDisable",
            self.mplslocalifnetdisable)
        xml_str = constr_leaf_value(xml_str, "ebgpMaxHop", self.ebgpmaxhop)
        xml_str = constr_leaf_value(xml_str, "fourByteAs", self.fourbyteas)
        xml_str = constr_leaf_value(xml_str, "pswdType", self.pswdtype)
        xml_str = constr_leaf_value(
            xml_str, "pswdCipherText", self.pswdciphertext)
        xml_str = constr_leaf_value(xml_str, "routeRefresh", self.routerefresh)
        xml_str = constr_leaf_value(xml_str, "tcpMSS", self.tcpmss)
        xml_str = constr_leaf_value(
            xml_str, "trackDelayTime", self.trackdelaytime)
        xml_str = constr_leaf_value(
            xml_str, "trackingEnable", self.trackingenable)
        xml_str = constr_leaf_value(xml_str, "validTtlHops", self.validttlhops)
        xml_str = constr_leaf_value(xml_str, "isLogChange", self.islogchange)
        # Tail Process
        xml_str = constr_container_process_tail(xml_str, "bgpPeerGroup")
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
            xml_str, "bgpPeerGroup", NE_COMMON_XML_OPERATION_DELETE)
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
        xml_str = constr_leaf_value(xml_str, "groupName", self.groupname)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "bgpPeerGroup")
        xml_str += NE_BGP_INSTANCE_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        # self.updates_cmd.append("undo bgp %s" % self.)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

        self.bgp_peerGroup_info = self.get_bgp_peerGroup()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.bgp_peerGroup_info:
                # create BGP peer
                self.create_process()
            else:
                # merge BGP peer
                self.merge_process()
        elif self.state == "absent":
            # if self.bgp_peerGroup_info:
                # # remove BGP peer
            self.delete_process()
            # else:
            # self.module.fail_json(
            # msg='Error: BGP peer group does not exist')
        # elif self.state == "query":
            # # 查询输出
            # if not self.bgp_peerGroup_info:
            # self.module.fail_json(
            # msg='Error: BGP peer group does not exist')

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
    # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

    argument_spec = dict(
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/vrfName
        vrfname=dict(required=True, type='str'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/afType
        aftype=dict(required=True, choices=['public', 'ipv4uni', 'ipv6uni']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/groupName
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/groupType
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/groupAs
        groupname=dict(required=True, type='str'),
        grouptype=dict(required=False, choices=['ebgp', 'ibgp']),
        groupas=dict(required=False, type='str'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/conventional
        conventional=dict(required=False, choices=['true', 'false']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/description
        description=dict(required=False, type='str'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/dualAs
        dualas=dict(required=False, choices=['true', 'false']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/prependFakeAs
        prependfakeas=dict(required=False, choices=['true', 'false']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/fakeAs
        fakeas=dict(required=False, type='str'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/prependGlobalAs
        prependglobalas=dict(required=False, choices=['true', 'false']),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/connRetryTime
        connretrytime=dict(required=False, type='int'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/checkFirstAs
        checkfirstas=dict(
            required=False,
            choices=[
                'default',
                'disable',
                'enable']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/connectMode
        connectmode=dict(
            required=False,
            choices=[
                'listenOnly',
                'connectOnly',
                'null']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/holdTime
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/keepAliveTime
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/minHoldTime
        holdtime=dict(required=False, type='int'),
        keepalivetime=dict(required=False, type='int'),
        minholdtime=dict(required=False, type='int'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/isIgnore
        isignore=dict(required=False, choices=['true', 'false']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/keyChainName
        keychainname=dict(required=False, type='str'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/localIfAddress
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/localIfName
        localifaddress=dict(required=False, type='str'),
        localifname=dict(required=False, type='str'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/mplsLocalIfnetDisable
        mplslocalifnetdisable=dict(required=False, choices=['true', 'false']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/ebgpMaxHop
        ebgpmaxhop=dict(required=False, type='int'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/fourByteAs
        fourbyteas=dict(required=False, choices=['true', 'false']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/pswdCipherText
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/pswdType
        pswdtype=dict(required=False, choices=['simple', 'cipher', 'null']),
        pswdciphertext=dict(required=False, type='str'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/routeRefresh
        routerefresh=dict(required=False, choices=['true', 'false']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/tcpMSS
        tcpmss=dict(required=False, type='int'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/trackDelayTime
        trackdelaytime=dict(required=False, type='int'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/trackingEnable
        trackingenable=dict(required=False, choices=['true', 'false']),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/validTtlHops
        validttlhops=dict(required=False, type='int'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeerGroups/bgpPeerGroup/isLogChange
        islogchange=dict(required=False, choices=['true', 'false']),
        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = BgpPeerGroup(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
