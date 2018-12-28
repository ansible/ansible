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
module: ne_bgp_bgpvrfaf_peergroupaf_deforiginate
version_added: "2.6"
short_description: Manages configuration of the matching conditions for default route advertisement of a peer group on HUAWEI netengine switches.
description:
    - Manages configuration of the matching conditions for default route advertisement of a peer group on HUAWEI netengine switches.
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
  - name: Configure the matching conditions for default route advertisement of a peer group
    ne_bgp_peerGroupAF_defOriginate:
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


class BGP_peerGroupAF_defOriginate(object):
    """Manages configuration of the matching conditions for default route advertisement of a peer group."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.aftype = self.module.params['aftype']
        self.groupname = self.module.params['groupname']
        self.configvrfname = self.module.params['configvrfname']

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

        conf_str = constr_container_head(conf_str, "peerGroupAFs")
        conf_str = constr_container_head(conf_str, "peerGroupAF")
        conf_str = constr_leaf_value(conf_str, "groupName", self.groupname)

        conf_str = constr_container_head(conf_str, "defOriginates")
        conf_str = constr_container_head(conf_str, "defOriginate")

        # Body info
        conf_str = constr_leaf_novalue(conf_str, "configVrfName")

        # Tail info
        conf_str = constr_container_process_tail(conf_str, "defOriginate")
        conf_str = constr_container_process_tail(conf_str, "peerGroupAF")
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

        defOriginates = root.findall(
            "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerGroupAFs/peerGroupAF/defOriginates/defOriginate")
        if defOriginates is not None and len(defOriginates) != 0:
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

            peerGroupAF = root.find(
                "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerGroupAFs/peerGroupAF")
            if peerGroupAF is not None and len(peerGroupAF) != 0:
                for element in peerGroupAF:
                    if element.tag == "groupName":
                        bgp_info["bgpvrfafs"]["peergroupafs"] = {
                            element.tag.lower(): element.text}

            defOriginate_info = list()
            for defOriginate in defOriginates:
                defOriginate_dict = dict()
                for element in defOriginate:
                    if element.tag == "configVrfName":
                        defOriginate_dict[element.tag.lower()] = element.text
                defOriginate_info.append(defOriginate_dict)
            bgp_info["bgpvrfafs"]["peergroupafs"]["deforiginates"] = defOriginate_info

        return bgp_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["aftype"] = self.aftype
        self.proposed["groupname"] = self.groupname
        self.proposed["configvrfname"] = self.configvrfname

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

        xml_str = constr_container_head(xml_str, "peerGroupAFs")
        xml_str = constr_container_head(xml_str, "peerGroupAF")
        xml_str = constr_leaf_value(xml_str, "groupName", self.groupname)

        xml_str = constr_container_process_head(
            xml_str, "defOriginate", operationType)

        # Body process
        xml_str = constr_leaf_value(
            xml_str, "configVrfName", self.configvrfname)

        # Tail info
        xml_str = constr_container_process_tail(xml_str, "defOriginate")
        xml_str = constr_container_process_tail(xml_str, "peerGroupAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrf")
        xml_str += NE_COMMON_XML_PROCESS_BGP_COMM_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # cmd_str = "peer %s default-originate vpn-instance %s" % (self.groupname,self.configvrfname)
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

        xml_str = constr_container_head(xml_str, "peerGroupAFs")
        xml_str = constr_container_head(xml_str, "peerGroupAF")
        xml_str = constr_leaf_value(xml_str, "groupName", self.groupname)

        xml_str = constr_container_process_head(
            xml_str, "defOriginate", NE_COMMON_XML_OPERATION_DELETE)

        # Body process
        xml_str = constr_leaf_value(
            xml_str, "configVrfName", self.configvrfname)

        # Tail info
        xml_str = constr_container_process_tail(xml_str, "defOriginate")
        xml_str = constr_container_process_tail(xml_str, "peerGroupAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrf")
        xml_str += NE_COMMON_XML_PROCESS_BGP_COMM_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

        # cmd_str = "undo peer %s default-route-advertise" % self.remoteAddress
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
        groupname=dict(required=True, type='str'),

        # CLI: peer g2 default-originate vpn-instance vpna
        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/peerGroupAFs/peerGroupAF/defOriginates/defOriginate/configVrfName
        configvrfname=dict(required=True, type='str'),

        state=dict(required=False, default='present', choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = BGP_peerGroupAF_defOriginate(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
