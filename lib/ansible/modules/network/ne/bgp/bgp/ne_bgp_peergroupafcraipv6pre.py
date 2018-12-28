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
module: ne_bgp_peergroupafcraipv6pre
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
    ne_bgp_peerGroupAFCraIPv6Pre:
      instanceId: 1

      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"instanceId": "1", "ifName":LoopBack0}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    updates:
    description: commands sent to the device
    returned: always
    type: list
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''
# import pydevd


class BGP_peerGroupAFCraIPv6Pre(object):
    """Manages configuration of an BGP interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.aftype = self.module.params['aftype']
        self.groupname = self.module.params['groupname']
        self.dertipv6addr = self.module.params['dertipv6addr']
        self.dertipv6mask = self.module.params['dertipv6mask']
        self.state = self.module.params['state']
        # bgp info
        self.bgp_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """

        # required_one_of    = [["vrfName", "aftype", "groupname", "dertipv6addr", "dertipv6mask"]]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            # required_one_of=required_one_of,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # check vrfName
        # if self.vrfName:
        #    if len(self.vrfName) > 63:
        #        self.module.fail_json(
        #             msg='Error: The length of the instance name is not in the range from 1 to 63.')
        #
        # check aftype
        # if self.aftype:
        #    if self.aftype not in self.spec["aftype"]["choices"]:
        #        self.module.fail_json(
        #            msg='Error: aftype is not in the range.')
        #
        # check groupname
        # if self.groupname:
        #    if len(self.groupname) > 63:
        #        self.module.fail_json(
        #             msg='Error: The length of the group Name is not in the range from 1 to 63.')
        #

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_bgp_dict(self):
        """ get one bgp attributes dict."""

        bgp_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_BGP_VRF_HEAD
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "bgpVrfAFs")
        conf_str = constr_container_head(conf_str, "bgpVrfAF")
        conf_str = constr_leaf_value(conf_str, "afType", self.aftype)
        conf_str = constr_container_head(conf_str, "peerGroupAFs")
        conf_str = constr_container_head(conf_str, "peerGroupAF")
        conf_str = constr_leaf_value(conf_str, "groupName", self.groupname)
        conf_str = constr_container_head(conf_str, "peerGroupAFCraIPv6Pres")
        conf_str = constr_container_head(conf_str, "peerGroupAFCraIPv6Pre")

        # Body info
        conf_str = constr_leaf_novalue(conf_str, "deRtIpv6Addr")
        conf_str = constr_leaf_novalue(conf_str, "deRtIPv6Mask")

        # Tail info
        conf_str = constr_container_tail(conf_str, "peerGroupAFCraIPv6Pre")
        conf_str = constr_container_tail(conf_str, "peerGroupAFCraIPv6Pres")
        conf_str = constr_container_tail(conf_str, "peerGroupAF")
        conf_str = constr_container_tail(conf_str, "peerGroupAFs")
        conf_str = constr_container_tail(conf_str, "bgpVrfAF")
        conf_str = constr_container_tail(conf_str, "bgpVrfAFs")
        conf_str += NE_COMMON_XML_GET_BGP_VRF_TAIL

        xml_str = get_nc_config(self.module, conf_str, True)
        # print xml_str
        if "<data/>" in xml_str:
            return bgp_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # get process base info
        root = ElementTree.fromstring(xml_str)
        peerGroupAFCraIPv6Pres = root.findall(
            "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerGroupAFs/peerGroupAF/peerGroupAFCraIPv6Pres/peerGroupAFCraIPv6Pre")
        if peerGroupAFCraIPv6Pres is not None and len(
                peerGroupAFCraIPv6Pres) != 0:

            bgpVrf = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf")
            # if bgpVrf is not None:
            if bgpVrf is not None and len(bgpVrf) != 0:
                for element in bgpVrf:
                    if element.tag in ["vrfName"]:
                        bgp_info[element.tag.lower()] = element.text

            bgpVrfAF = root.find(
                "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF")
            # if bgpVrfAF is not None:
            if bgpVrfAF is not None and len(bgpVrfAF) != 0:
                for element in bgpVrfAF:
                    if element.tag in ["afType"]:
                        bgp_info["bgpvrfafs"] = {
                            element.tag.lower(): element.text}

            peerGroupAF = root.find(
                "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerGroupAFs/peerGroupAF")
            if peerGroupAF is not None and len(peerGroupAF) != 0:
                for element in peerGroupAF:
                    if element.tag == "groupName":
                        bgp_info["bgpvrfafs"]["peergroupafs"] = {
                            element.tag.lower(): element.text}

            peerGroupAFCraIPv6Pre_info = list()
            for peerGroupAFCraIPv6Pre in peerGroupAFCraIPv6Pres:
                peerGroupAFCraIPv6Pre_dict = dict()
                for element in peerGroupAFCraIPv6Pre:
                    if element.tag in ["deRtIpv6Addr",
                                       "deRtIPv6Mask"]:
                        peerGroupAFCraIPv6Pre_dict[element.tag.lower(
                        )] = element.text
                peerGroupAFCraIPv6Pre_info.append(peerGroupAFCraIPv6Pre_dict)
            bgp_info["bgpvrfafs"]["peergroupafs"]["peergroupafcraipv6pres"] = peerGroupAFCraIPv6Pre_info

        return bgp_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["aftype"] = self.aftype
        self.proposed["groupname"] = self.groupname
        self.proposed["state"] = self.state
        self.proposed["dertipv6addr"] = self.dertipv6addr
        self.proposed["dertipv6mask"] = self.dertipv6mask

    def get_existing(self):
        """get existing info"""
        if not self.bgp_info:
            return

        self.existing = self.bgp_info

    def get_end_state(self):
        """get end state info"""

        bgp_info = self.get_bgp_dict()
        if not bgp_info:
            return
        self.end_state = bgp_info

    def create_process(self):
        """Create bgp process"""
        self.comm_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def comm_process(self, operation, operation_Desc):
        """Comm  bgp process"""

        # Head process
        xml_str = NE_BGP_INSTANCE_HEADER % NE_COMMON_XML_OPERATION_MERGE

        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_head(xml_str, "bgpVrfAFs")
        xml_str = constr_container_head(xml_str, "bgpVrfAF")
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
        xml_str = constr_container_head(xml_str, "peerGroupAFs")
        xml_str = constr_container_head(xml_str, "peerGroupAF")
        xml_str = constr_leaf_value(xml_str, "groupName", self.groupname)
        xml_str = constr_container_process_head(
            xml_str, "peerGroupAFCraIPv6Pre", operation)

        # Body process
        xml_str = constr_leaf_value(xml_str, "deRtIpv6Addr", self.dertipv6addr)
        xml_str = constr_leaf_value(xml_str, "deRtIPv6Mask", self.dertipv6mask)

        # Tail process
        xml_str = constr_container_process_tail(
            xml_str, "peerGroupAFCraIPv6Pre")
        xml_str = constr_container_process_tail(xml_str, "peerGroupAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str += NE_BGP_INSTANCE_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, operation_Desc)

        self.changed = True

    def merge_process(self):
        """ Merge bgp process """
        self.comm_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete bgp  process"""
        # Common Head process
        xml_str = NE_BGP_INSTANCE_HEADER % (NE_COMMON_XML_OPERATION_MERGE)
        # Head process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_head(xml_str, "bgpVrfAFs")
        xml_str = constr_container_head(xml_str, "bgpVrfAF")
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
        xml_str = constr_container_head(xml_str, "peerGroupAFs")
        xml_str = constr_container_head(xml_str, "peerGroupAF")
        xml_str = constr_leaf_value(xml_str, "groupName", self.groupname)
        xml_str = constr_container_process_head(
            xml_str, "peerGroupAFCraIPv6Pre", NE_COMMON_XML_OPERATION_DELETE)

        # Body process
        xml_str = constr_leaf_value(xml_str, "deRtIpv6Addr", self.dertipv6addr)
        xml_str = constr_leaf_value(xml_str, "deRtIPv6Mask", self.dertipv6mask)

        # Tail process
        xml_str = constr_container_process_tail(
            xml_str, "peerGroupAFCraIPv6Pre")
        xml_str = constr_container_process_tail(xml_str, "peerGroupAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str += NE_BGP_INSTANCE_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

    def work(self):
        """worker"""
        # self.check_params()

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
            # if self.bgp_info:
                # # remove bgp process
            self.delete_process()
            # else:
                # self.module.fail_json(msg='Error: Bgp instance does not exist')
        # elif self.state == "query":
            # if not self.bgp_info:
                # self.module.fail_json(msg='Error: Bgp instance does not exist')

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
        aftype=dict(required=True, choices=['ipv4uni', 'ipv4multi', 'ipv4vpn', 'ipv6uni',
                                            'ipv6vpn', 'ipv4flow', 'l2vpnad', 'mvpn', 'vpntarget',
                                            'evpn', 'ipv4vpnmcast', 'ls', 'mdt', 'ipv6flow', 'vpnv4flow',
                                            'ipv4labeluni', 'mvpnv6']),
        groupname=dict(required=True, type='str'),
        dertipv6addr=dict(required=True, type='str'),
        dertipv6mask=dict(required=True, type='int'),


        state=dict(required=False, default='present', choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = BGP_peerGroupAFCraIPv6Pre(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
