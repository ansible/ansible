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

from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_process_tail
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_process_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_tail
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_novalue
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_value
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_delete
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_BGP_INSTANCE_TAIL
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_BGP_INSTANCE_HEADER
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_GET_BGP_VRF_TAIL
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_GET_BGP_VRF_HEAD
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_CLEAR
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import copy
import re
# import pydevd
import socket
import sys
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_bgp_peerbfd
version_added: "2.6"
short_description: Manages configuration of an BGP instance on HUAWEI netengine switches.
description:
    - Manages configuration of an BGP instance on HUAWEI netengine switches.
author: wangyuanqiang (@netengine-Ansible)
options:
    instanceId:
        description:
            - Set the process ID. If the process ID does not exist, you can create a process. Otherwise, the system fails to create a process.
              The value is an integer ranging from 1 to 4294967295.
        required: true
'''

EXAMPLES = '''
- name: bgp module test
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
  - name: Configure bgp
    ne_bgp_peerBfd:
      instanceId: 1
      description: BGP
      vpnName:__public__
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"instanceId": "1", "description": "BGP", "vpnName":__public__}
proposed:
    description: k/v pairs of proposed configuration
    returned: verbose mode
    type: dict
    sample: {"instanceId": "1", "description": "BGP", "vpnName":__public__}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"instanceId": "1",
             "description": "BGP"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["bgp 1", "description BGP"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class BGP(object):
    """Manages configuration of an ISIS instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.peeraddr = self.module.params['peeraddr']
        self.isbfdblock = self.module.params['isbfdblock']
        self.multiplier = self.module.params['multiplier']
        self.isbfdenable = self.module.params['isbfdenable']
        self.rxinterval = self.module.params['rxinterval']
        self.txinterval = self.module.params['txinterval']
        self.issinglehop = self.module.params['issinglehop']
        self.bfdcompatible = self.module.params['bfdcompatible']
        self.perlinkecho = self.module.params['perlinkecho']

        self.state = self.module.params['state']
        # isis info
        self.isis_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""

        # if self.vrfname:
        #    if len(self.vrfname) > 31 or len(self.vrfname.replace(' ', '')) < 1:
        #        self.module.fail_json(
        #            msg='Error: Vrf name is not in the range from 1 to 31.')
        #
        # if self.peeraddr:
        #    if not check_ip_addr(ipaddr=self.peeraddr):
        #        module.fail_json(
        #            msg='Error: The peer_addr %s is invalid.' % self.peeraddr)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_bgp_dict(self):
        """ get one bgp attributes dict."""

        bfd_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_BGP_VRF_HEAD

        # Body info
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "bgpPeers")
        conf_str = constr_container_head(conf_str, "bgpPeer")

        conf_str = constr_leaf_value(conf_str, "peerAddr", self.peeraddr)
        conf_str = constr_container_head(conf_str, "peerBfd")

        conf_str = constr_leaf_novalue(conf_str, "isBfdBlock")
        conf_str = constr_leaf_novalue(conf_str, "multiplier")
        conf_str = constr_leaf_novalue(conf_str, "isBfdEnable")
        conf_str = constr_leaf_novalue(conf_str, "rxInterval")
        conf_str = constr_leaf_novalue(conf_str, "txInterval")
        conf_str = constr_leaf_novalue(conf_str, "isSingleHop")
        conf_str = constr_leaf_novalue(conf_str, "bfdCompatible")
        conf_str = constr_leaf_novalue(conf_str, "perLinkEcho")

        # Tail info
        conf_str = constr_container_tail(conf_str, "peerBfd")
        conf_str = constr_container_tail(conf_str, "bgpPeer")
        conf_str = constr_container_tail(conf_str, "bgpPeers")
        conf_str += NE_COMMON_XML_GET_BGP_VRF_TAIL

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        xml_str = get_nc_config(self.module, conf_str, True)

        if "<data/>" in xml_str:
            return bfd_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # get process base info

        root = ElementTree.fromstring(xml_str)
        bgpVrf = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf")
        if bgpVrf is not None and len(bgpVrf) != 0:
            for vrf in bgpVrf:
                if vrf.tag in ["vrfName"]:
                    bfd_info[vrf.tag.lower()] = vrf.text

        bgpPeers = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer")
        if bgpPeers is not None and len(bgpPeers) != 0:
            for bgpPeer in bgpPeers:
                if bgpPeer.tag in ["peerAddr"]:
                    bfd_info[bgpPeer.tag.lower()] = bgpPeer.text

        bfds = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd")
        if bfds is not None and len(bfds) != 0:
            for bfd in bfds:
                if bfd.tag in ["isBfdBlock",
                               "multiplier",
                               "isBfdEnable",
                               "rxInterval",
                               "txInterval",
                               "isSingleHop",
                               "bfdCompatible",
                               "perLinkEcho"]:
                    bfd_info[bfd.tag.lower()] = bfd.text

        return bfd_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["peeraddr"] = self.peeraddr
        self.proposed["state"] = self.state

        if self.isbfdblock:
            self.proposed["isbfdblock"] = self.isbfdblock
        if self.multiplier:
            self.proposed["multiplier"] = self.multiplier
        if self.isbfdenable:
            self.proposed["isbfdenable"] = self.isbfdenable
        if self.rxinterval:
            self.proposed["rxinterval"] = self.rxinterval
        if self.txinterval:
            self.proposed["txinterval"] = self.txinterval
        if self.issinglehop:
            self.proposed["issinglehop"] = self.issinglehop
        if self.bfdcompatible:
            self.proposed["bfdcompatible"] = self.bfdcompatible
        if self.perlinkecho:
            self.proposed["perlinkecho"] = self.perlinkecho

    def get_existing(self):
        """get existing info"""
        if not self.bgp_info:
            return

        self.existing = copy.deepcopy(self.bgp_info)

    def get_end_state(self):
        """get end state info"""
        """get end state info"""

        bgp_info = self.get_bgp_dict()
        if not bgp_info:
            return

        self.end_state = copy.deepcopy(bgp_info)

    def common_process(self, operType, operationDesc):
        """Common  isis process"""
        # Head process
        if NE_COMMON_XML_OPERATION_CREATE == operType:
            operType = NE_COMMON_XML_OPERATION_MERGE

        xml_str = NE_BGP_INSTANCE_HEADER % NE_COMMON_XML_OPERATION_MERGE

        # Process vrfname and peeraddr is the key, must input
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_head(xml_str, "bgpPeers")
        xml_str = constr_container_head(xml_str, "bgpPeer")

        xml_str = constr_leaf_value(xml_str, "peerAddr", self.peeraddr)
        if NE_COMMON_XML_OPERATION_DELETE == operType:
            xml_str += "<" + "peerBfd" + " xc:operation=\"" + operType + "\">\r\n"
        else:
            xml_str = constr_container_head(xml_str, "peerBfd")

        # Body process
        if operType == NE_COMMON_XML_OPERATION_CLEAR:
            xml_str = constr_leaf_delete(xml_str, "isBfdBlock", self.isbfdblock)
            xml_str = constr_leaf_delete(xml_str, "multiplier", self.multiplier)
            xml_str = constr_leaf_delete(xml_str, "isBfdEnable", self.isbfdenable)
            xml_str = constr_leaf_delete(xml_str, "rxInterval", self.rxinterval)
            xml_str = constr_leaf_delete(xml_str, "txInterval", self.txinterval)
            xml_str = constr_leaf_delete(xml_str, "isSingleHop", self.issinglehop)
            xml_str = constr_leaf_delete(xml_str, "bfdCompatible", self.bfdcompatible)
            xml_str = constr_leaf_delete(xml_str, "perLinkEcho", self.perlinkecho)
        else:
            xml_str = constr_leaf_value(xml_str, "isBfdBlock", self.isbfdblock)
            xml_str = constr_leaf_value(xml_str, "multiplier", self.multiplier)
            xml_str = constr_leaf_value(xml_str, "isBfdEnable", self.isbfdenable)
            xml_str = constr_leaf_value(xml_str, "rxInterval", self.rxinterval)
            xml_str = constr_leaf_value(xml_str, "txInterval", self.txinterval)
            xml_str = constr_leaf_value(xml_str, "isSingleHop", self.issinglehop)
            xml_str = constr_leaf_value(xml_str, "bfdCompatible", self.bfdcompatible)
            xml_str = constr_leaf_value(xml_str, "perLinkEcho", self.perlinkecho)

        # Tail process
        xml_str += "</" + "peerBfd" + ">\r\n"
        xml_str = constr_container_process_tail(xml_str, "bgpPeer")
        xml_str += NE_BGP_INSTANCE_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

    def create_process(self):
        """Create isis process"""

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge isis process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Merge isis process"""

        self.common_process(NE_COMMON_XML_OPERATION_DELETE, "DELETE_PROCESS")

    def clear_process(self):
        """Merge isis process"""

        self.common_process(NE_COMMON_XML_OPERATION_CLEAR, "MERGE_PROCESS")

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.bgp_info = self.get_bgp_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.bgp_info:
                # create bgp process
                self.create_process()
            else:
                # merge bgp process
                self.merge_process()
        elif self.state == "absent":
            self.delete_process()
        # elif self.state == "query":
            # if not self.bgp_info:
            # self.module.fail_json(msg='Error: bgp peer bfd does not exist')

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        elif self.state == "clear":
            self.clear_process()

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
        vrfname=dict(required=True, type='str'),
        peeraddr=dict(required=True, type='str'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd/isBfdBlock
        isbfdblock=dict(required=False, type='str', choices=['true', 'false']),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd/isBfdEnable
        isbfdenable=dict(
            required=False,
            type='str',
            choices=[
                'true',
                'false']),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd/isSingleHop
        issinglehop=dict(
            required=False,
            type='str',
            choices=[
                'true',
                'false']),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd/multiplier
        multiplier=dict(required=False, type='int'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd/rxInterval
        rxinterval=dict(required=False, type='int'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd/txInterval
        txinterval=dict(required=False, type='int'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd/bfdCompatible
        bfdcompatible=dict(
            required=False,
            type='str',
            choices=[
                'true',
                'false']),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpPeers/bgpPeer/peerBfd/perLinkEcho
        perlinkecho=dict(
            required=False,
            type='str',
            choices=[
                'true',
                'false']),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query', 'clear']))

    argument_spec.update(ne_argument_spec)
    module = BGP(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
