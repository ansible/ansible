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
module: ne_bgp_importroute
version_added: "2.6"
short_description: Manages configuration of imported routes on HUAWEI netengine switches.
description:
    - Manages configuration of imported routes on HUAWEI netengine switches.
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
  - name: Configure imported route
    ne_bgp_importRoute:
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


class BGP_importRoute(object):
    """Manages configuration of import route."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.vrfname = self.module.params['vrfname']
        self.aftype = self.module.params['aftype']

        self.importprotocol = self.module.params['importprotocol']
        self.importprocessid = self.module.params['importprocessid']
        self.importroutepolicy = self.module.params['importroutepolicy']
        self.mednew = self.module.params['mednew']
        self.nonrelaytnl = self.module.params['nonrelaytnl']

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

        conf_str = constr_container_head(conf_str, "importRoutes")
        conf_str = constr_container_head(conf_str, "importRoute")

        # Body info
        conf_str = constr_leaf_novalue(conf_str, "importProtocol")
        conf_str = constr_leaf_novalue(conf_str, "importProcessId")

        # Tail info
        conf_str = constr_container_process_tail(conf_str, "importRoute")
        conf_str = constr_container_process_tail(conf_str, "bgpVrfAF")
        conf_str = constr_container_process_tail(conf_str, "bgpVrf")
        conf_str += NE_COMMON_XML_GET_BGP_COMM_TAIL

        bgp_info = dict()
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return bgp_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp"', "")

        # get process base info
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)
        root = ElementTree.fromstring(xml_str)

        importRoutes = root.findall(
            "bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/importRoutes/importRoute")
        if importRoutes is not None and len(importRoutes) != 0:
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

            importRoute_info = list()
            for importRoute in importRoutes:
                importRoute_dict = dict()
                for element in importRoute:
                    if element.tag in ["importProtocol",
                                       "importProcessId",
                                       "importRoutePolicy",
                                       "medNew",
                                       "nonRelayTnl"]:
                        importRoute_dict[element.tag.lower()] = element.text
                importRoute_info.append(importRoute_dict)
            bgp_info["bgpvrfafs"]["importroutes"] = importRoute_info

        return bgp_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["aftype"] = self.aftype

        self.proposed["importprotocol"] = self.importprotocol
        self.proposed["importprocessid"] = self.importprocessid
        if self.importroutepolicy:
            self.proposed["importroutepolicy"] = self.importroutepolicy
        if self.mednew:
            self.proposed["mednew"] = self.mednew
        if self.nonrelaytnl:
            self.proposed["nonrelaytnl"] = self.nonrelaytnl

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
        """Common bgp import route"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_COMM_HEAD

        xml_str = constr_container_head(xml_str, "bgpVrfs")
        xml_str = constr_container_head(xml_str, "bgpVrf")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)

        xml_str = constr_container_head(xml_str, "bgpVrfAFs")
        xml_str = constr_container_head(xml_str, "bgpVrfAF")
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)

        xml_str = constr_container_process_head(
            xml_str, "importRoute", operationType)

        # Body process
        xml_str = constr_leaf_value(
            xml_str, "importProtocol", self.importprotocol)
        xml_str = constr_leaf_value(
            xml_str, "importProcessId", self.importprocessid)
        xml_str = constr_leaf_value(
            xml_str,
            "importRoutePolicy",
            self.importroutepolicy)
        xml_str = constr_leaf_value(xml_str, "medNew", self.mednew)
        xml_str = constr_leaf_value(xml_str, "nonRelayTnl", self.nonrelaytnl)

        # Tail info
        xml_str = constr_container_process_tail(xml_str, "importRoute")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrf")
        xml_str += NE_COMMON_XML_PROCESS_BGP_COMM_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # cmd_str = "import-route %s" % self.importprotocol
        # if self.importprocessid:
        #    cmd_str += " %s" % self.importprocessid
        # if self.importroutepolicy:
        #    cmd_str += " %s" % self.importroutepolicy
        # if self.mednew:
        #    cmd_str += " %s" % self.mednew
        # if self.nonrelaytnl:
        #    cmd_str += " %s" % self.nonrelaytnl
        # self.updates_cmd.append(cmd_str)

    def create_process(self):
        """Create bgp import route"""

        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge bgp import route"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete bgp import route"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_BGP_COMM_HEAD

        xml_str = constr_container_head(xml_str, "bgpVrfs")
        xml_str = constr_container_head(xml_str, "bgpVrf")
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)

        xml_str = constr_container_head(xml_str, "bgpVrfAFs")
        xml_str = constr_container_head(xml_str, "bgpVrfAF")
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)

        xml_str = constr_container_process_head(
            xml_str, "importRoute", NE_COMMON_XML_OPERATION_DELETE)

        # Body process
        xml_str = constr_leaf_value(
            xml_str, "importProtocol", self.importprotocol)
        xml_str = constr_leaf_value(
            xml_str, "importProcessId", self.importprocessid)

        # Tail info
        xml_str = constr_container_process_tail(xml_str, "importRoute")
        xml_str = constr_container_process_tail(xml_str, "bgpVrfAF")
        xml_str = constr_container_process_tail(xml_str, "bgpVrf")
        xml_str += NE_COMMON_XML_PROCESS_BGP_COMM_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

        # cmd_str = "undo import-route %s" % self.importprotocol
        # if self.importprocessid:
        #    cmd_str += " %s" % self.importprocessid
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

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/importRoutes/importRoute/importProtocol
        # CLI: import-route bgp 1
        importprotocol=dict(required=True, choices=['direct', 'ospf', 'isis', 'static', 'rip',
                                                    'ospfv3', 'ripng', 'unr', 'op-route']),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/importRoutes/importRoute/importProcessId
        # CLI: import-route bgp 1
        importprocessid=dict(required=True, type='int'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/importRoutes/importRoute/importRoutePolicy
        # CLI: import-route unr route-policy 22
        importroutepolicy=dict(required=False, type='str'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/importRoutes/importRoute/medNew
        #  CLI: import-route unr med 0
        mednew=dict(required=False, type='int'),

        # /bgp/bgpcomm/bgpVrfs/bgpVrf/bgpVrfAFs/bgpVrfAF/importRoutes/importRoute/nonRelayTnl
        # CLI: import-route ospf 1 non-relay-tunnel xx
        nonrelaytnl=dict(required=False, choices=['true', 'false']),

        state=dict(required=False, default='present', choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = BGP_importRoute(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
