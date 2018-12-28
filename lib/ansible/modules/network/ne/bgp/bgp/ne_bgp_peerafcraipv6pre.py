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
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_container_head
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_novalue
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import constr_leaf_value
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_PROCESS_BGP_COMM_TAIL
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_PROCESS_BGP_COMM_HEAD
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_GET_BGP_COMM_TAIL
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_GET_BGP_COMM_HEAD
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.bgp.bgp.ne_bgp_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import re
import socket
import sys
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_bgp_peerafcraipv6pre
version_added: "2.6"
short_description: Manages configuration of the matching conditions for default route advertisement of a peer on HUAWEI netengine switches.
description:
    - Manages configuration of the matching conditions for default route advertisement of a peer on HUAWEI netengine switches.
author: wangyuanqiang (@netengine-Ansible)
options:

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
  - name: Configure bgp peer AFCraIPv6Pre
    ne_bgp_peerAFCraIPv6Pre:
      vrfname:__public__
      state: present
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


class BGP_peerAFCraIPv6Pre(object):
    """Manages configuration of the matching conditions for default route advertisement of a peer."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.aftype = self.module.params['aftype']
        self.remoteaddress = self.module.params['remoteaddress']
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

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""

        # check vrf name.
        # if self.vrfname:
        #    if len(self.vrfname) > 31 or len(self.vrfname.replace(' ', '')) < 1:
        #        self.module.fail_json(
        # msg='Error: The length of vrfname is not in the range from 1 to 31.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_bgp_dict(self):
        """ get one bgp attributes dict."""

        # Head info
        conf_str = NE_COMMON_XML_GET_BGP_COMM_HEAD

        conf_str = constr_container_head(conf_str, "bgpVrfs")
        conf_str = constr_container_head(conf_str, "bgpVrf")
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)

        conf_str = constr_container_head(conf_str, "bgpVrfAFs")
        conf_str = constr_container_head(conf_str, "bgpVrfAF")
        conf_str = constr_leaf_value(conf_str, "afType", self.aftype)

        conf_str = constr_container_head(conf_str, "peerAFs")
        conf_str = constr_container_head(conf_str, "peerAF")
        conf_str = constr_leaf_value(
            conf_str, "remoteAddress", self.remoteaddress)

        conf_str = constr_container_head(conf_str, "peerAFCraIPv6Pres")
        conf_str = constr_container_head(conf_str, "peerAFCraIPv6Pre")

        # Body info
        conf_str = constr_leaf_novalue(conf_str, "deRtIpv6Addr")
        conf_str = constr_leaf_novalue(conf_str, "deRtIPv6Mask")

        # Tail info
        conf_str = constr_container_process_tail(conf_str, "peerAFCraIPv6Pre")
        conf_str = constr_container_process_tail(conf_str, "peerAF")
        conf_str = constr_container_process_tail(conf_str, "bgpVrfAF")
        conf_str = constr_container_process_tail(conf_str, "bgpVrf")
        conf_str += NE_COMMON_XML_GET_BGP_COMM_TAIL

        bgp_info = {}
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return bgp_info

        xml_str = xml_str.replace('\r', '').replace('\n', ''). \
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp"', ""). \
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # get process base info
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)
        root = ElementTree.fromstring(xml_str)

        peerAFCraPres = root.findall(
            "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerAFs/peerAF/peerAFCraIPv6Pres/peerAFCraIPv6Pre")
        if peerAFCraPres is not None and len(peerAFCraPres) != 0:
            bgpVrf = root.find("bgp/bgpcomm/bgpVrfs/bgpVrf")
            if bgpVrf is not None and len(bgpVrf) != 0:
                for element in bgpVrf:
                    if element.tag == "vrfName":
                        bgp_info[element.tag.lower()] = element.text

            bgpVrfAF = root.find(
                "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF")
            if bgpVrfAF is not None and len(bgpVrfAF) != 0:
                for element in bgpVrfAF:
                    if element.tag == "afType":
                        bgp_info["bgpvrfafs"] = {
                            element.tag.lower(): element.text}

            peerAF = root.find(
                "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerAFs/peerAF")
            if peerAF is not None and len(peerAF) != 0:
                bgp_info["bgpvrfafs"]["peerafs"] = {}
                for element in peerAF:
                    if element.tag == "remoteAddress":
                        bgp_info["bgpvrfafs"]["peerafs"][element.tag.lower()
                                                         ] = element.text

            peerAFCraIPv6Pre_info = list()
            for peerAFCraPre in peerAFCraPres:
                peerAFCraPre_dict = dict()
                for element in peerAFCraPre:
                    if element.tag in ["deRtIpv6Addr",
                                       "deRtIPv6Mask"]:
                        peerAFCraPre_dict[element.tag.lower()] = element.text
                peerAFCraIPv6Pre_info.append(peerAFCraPre_dict)
            bgp_info["bgpvrfafs"]["peerafs"]["peerafcraipv6pres"] = peerAFCraIPv6Pre_info

        return bgp_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["aftype"] = self.aftype
        self.proposed["remoteaddress"] = self.remoteaddress
        self.proposed["dertipv6addr"] = self.dertipv6addr
        self.proposed["dertipv6mask"] = self.dertipv6mask

        self.proposed["state"] = self.state

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

    def common_process(self, operationType, operationDesc):
        """Common the matching conditions for default route advertisement of a peer"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_COMM_HEAD

        xml_str = constr_container_head(xml_str, "bgpVrfs")
        xml_str = constr_container_head(xml_str, "bgpVrf")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)

        xml_str = constr_container_head(xml_str, "bgpVrfAFs")
        xml_str = constr_container_head(xml_str, "bgpVrfAF")
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)

        xml_str = constr_container_head(xml_str, "peerAFs")
        xml_str = constr_container_head(xml_str, "peerAF")
        xml_str = constr_leaf_value(
            xml_str, "remoteAddress", self.remoteaddress)

        xml_str = constr_container_process_head(
            xml_str, "peerAFCraIPv6Pre", operationType)

        # Body process
        xml_str = constr_leaf_value(xml_str, "deRtIpv6Addr", self.dertipv6addr)
        xml_str = constr_leaf_value(xml_str, "deRtIPv6Mask", self.dertipv6mask)

        # Tail info
        xml_str = constr_container_process_tail(xml_str, "peerAFCraIPv6Pre")
        xml_str = constr_container_process_tail(xml_str, "peerAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrf")
        xml_str += NE_COMMON_XML_PROCESS_BGP_COMM_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # cmd_str = "peer %s default-route-advertise conditional-route-match-all %s %s" % (self.remoteaddress,self.dertipv6addr,self.dertipv6mask)
        # self.updates_cmd.append(cmd_str)

    def create_process(self):
        """Create the matching conditions for default route advertisement of a peer"""

        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge the matching conditions for default route advertisement of a peer"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete the matching conditions for default route advertisement of a peer"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_COMM_HEAD

        xml_str = constr_container_head(xml_str, "bgpVrfs")
        xml_str = constr_container_head(xml_str, "bgpVrf")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)

        xml_str = constr_container_head(xml_str, "bgpVrfAFs")
        xml_str = constr_container_head(xml_str, "bgpVrfAF")
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)

        xml_str = constr_container_head(xml_str, "peerAFs")
        xml_str = constr_container_head(xml_str, "peerAF")
        xml_str = constr_leaf_value(
            xml_str, "remoteAddress", self.remoteaddress)

        xml_str = constr_container_process_head(
            xml_str, "peerAFCraIPv6Pre", NE_COMMON_XML_OPERATION_DELETE)

        # Body process
        xml_str = constr_leaf_value(xml_str, "deRtIpv6Addr", self.dertipv6addr)
        xml_str = constr_leaf_value(xml_str, "deRtIPv6Mask", self.dertipv6mask)

        # Tail info
        xml_str = constr_container_process_tail(xml_str, "peerAFCraIPv6Pre")
        xml_str = constr_container_process_tail(xml_str, "peerAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrf")
        xml_str += NE_COMMON_XML_PROCESS_BGP_COMM_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

        # cmd_str = "undo peer %s default-route-advertise" % self.remoteaddress
        # self.updates_cmd.append(cmd_str)

    def work(self):
        """worker"""

        self.check_params()
        self.bgp_info = self.get_bgp_dict()
        self.get_proposed()
        self.get_existing()

        # deal present, absent or query
        if self.state == "present":
            if not self.bgp_info:
                # create bgp process
                self.create_process()
            else:
                # merge bgp process
                self.merge_process()
        elif self.state == "absent":
            if self.bgp_info:
                # remove bgp process
                self.delete_process()
            else:
                self.module.fail_json(
                    msg='Error: The specified configuration does not exist.')
        elif self.state == "query":
            if not self.bgp_info:
                self.module.fail_json(
                    msg='Error: The specified configuration does not exist.')

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
        aftype=dict(required=True, choices=['ipv4uni', 'ipv4multi', 'ipv4vpn', 'ipv6uni', 'ipv6vpn', 'ipv4flow',
                                            'l2vpnad', 'mvpn', 'vpntarget', 'evpn', 'ipv4vpnmcast', 'ls', 'mdt',
                                            'ipv6flow', 'vpnv4flow', 'ipv4labeluni', 'mvpnv6']),
        remoteaddress=dict(required=True, type='str'),

        # CLI: peer 11::22 default-route-advertise conditional-route-match-all 11:: 64
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerAFs/peerAF/peerAFCraIPv6Pres/peerAFCraIPv6Pre/deRtIpv6Addr
        dertipv6addr=dict(required=True, type='str'),
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerAFs/peerAF/peerAFCraIPv6Pres/peerAFCraIPv6Pre/deRtIPv6Mask
        dertipv6mask=dict(required=True, type='int'),

        state=dict(required=False, default='present', choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = BGP_peerAFCraIPv6Pre(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
