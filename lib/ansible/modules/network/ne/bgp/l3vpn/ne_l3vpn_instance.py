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

from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_leaf_process
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_container_process_tail
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_container_process_head
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_container_tail
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_container_head
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_leaf_novalue
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_leaf_value
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPN_TAIL
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPN_HEAD
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_GET_L3VPN_TAIL
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_GET_L3VPN_HEAD
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import copy
import re
import socket
import sys
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_l3vpn_instance
version_added: "2.6"
short_description: Manages configuration of an L3VPN instance on HUAWEI netengine switches.
description:
    - Manages configuration of an L3VPN instance on HUAWEI netengine switches.
author: wangyuanqiang (@netengine-Ansible)
options:
    instanceId:
        description:
            - Set the process ID. If the process ID does not exist, you can create a process. Otherwise, the system fails to create a process.
              The value is an integer ranging from 1 to 4294967295.
        required: true
'''

EXAMPLES = '''
- name: l3vpn module test
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
  - name: Configure a vpn instance named vpna, description is test
    ne_l3vpn_instance:
      vrfname: vpna
      vrfdescription: test
      cfgrouterid: 1.1.1.1
      trafficstatisticenable: true
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"vrfname": "vpna",
             "vrfdescription": "test",
             "cfgRouterid": "1.1.1.1",
             "trafficstatisticenable": "true"
             "state": "present"}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  {"vrfname": "vpna",
              "vrfdescription": "test",
              "cfgRouterid": "1.1.1.1",
              "trafficstatisticenable": "true"
              "present": "present"}
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: ["ip vpn-instance vpna",
             "description test",
             "router id 1.1.1.1",
             "traffic-statistics enable"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class Vrf(object):
    """Manange vpn instance"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # vpn instance info
        self.vrfname = self.module.params['vrfname']
        self.vrfdescription = self.module.params['vrfdescription']
        self.cfgrouterid = self.module.params['cfgrouterid']
        self.trafficstatisticenable = self.module.params['trafficstatisticenable']
        self.state = self.module.params['state']

        # vrf info
        self.vrf_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init_module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_params(self):
        """Check all input params"""

        # check vrf
        # if self.vrfname:
        # if len(self.vrfname) > 31 or len(self.vrfname.replace(' ', '')) < 1:
        # self.module.fail_json(
        # msg='Error: Vpn instance name  is not in the range from 1 to 31.')

        # check isis description 1~242
        # if self.vrfdescription:
        # if len(self.vrfdescription) > 242 or len(self.vrfdescription.replace(' ', '')) < 1:
        # self.module.fail_json(
        # msg='Error: Isis instance description is not in the range from 1 to
        # 242.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_vrf_dict(self):
        """ get one vrf attributes dict."""

        vrf_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_L3VPN_HEAD

        # Body info
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        # conf_str = constr_leaf_novalue(conf_str, "vrfDescription")
        # conf_str = constr_leaf_novalue(conf_str, "cfgRouterId")
        # conf_str = constr_leaf_novalue(conf_str, "trafficStatisticEnable")

        # Tail info
        conf_str += NE_COMMON_XML_GET_L3VPN_TAIL
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return vrf_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn"', "")

        # get process base info
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)

        root = ElementTree.fromstring(xml_str)
        vrfInst = root.find("l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance")
        # if vrfInst is not None:
        if len(vrfInst) != 0:
            for inst in vrfInst:
                if inst.tag in ["vrfName",
                                "vrfDescription",
                                "cfgRouterId",
                                "trafficStatisticEnable"]:
                    vrf_info[inst.tag.lower()] = inst.text

        return vrf_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["vrfname"] = self.vrfname
        self.proposed["state"] = self.state

        if self.vrfdescription:
            self.proposed["vrfdescription"] = self.vrfdescription
        if self.cfgrouterid:
            self.proposed["cfgrouterid"] = self.cfgrouterid
        if self.trafficstatisticenable:
            self.proposed["trafficstatisticenable"] = self.trafficstatisticenable

    def get_existing(self):
        """get existing info"""
        if not self.vrf_info:
            return

        self.existing = copy.deepcopy(self.vrf_info)

    def get_end_state(self):
        """get end state info"""

        vrf_info = self.get_vrf_dict()
        if not vrf_info:
            return

        self.end_state = copy.deepcopy(vrf_info)

    def common_process(self, operationType, operationDesc):
        """Common  l3vpn process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_L3VPN_HEAD % operationType
        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        if self.vrfdescription is not None:
            if len(self.vrfdescription) == 0:
                xml_str = constr_leaf_process(xml_str, "vrfDescription", self.vrfdescription)
            else:
                xml_str = constr_leaf_value(xml_str, "vrfDescription", self.vrfdescription)
        # yang process leaf delete
        if self.cfgrouterid is not None:
            if len(self.cfgrouterid) == 0:
                xml_str = constr_leaf_process(
                    xml_str, "cfgRouterId", self.cfgrouterid)
            else:
                xml_str = constr_leaf_value(
                    xml_str, "cfgRouterId", self.cfgrouterid)

        xml_str = constr_leaf_value(
            xml_str,
            "trafficStatisticEnable",
            self.trafficstatisticenable)

        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_L3VPN_TAIL
        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, operationDesc)
        self.changed = True

        # if self.vrfname:
        #    self.updates_cmd.append("ip vpn-instance %s " % self.vrfname)

        # if self.vrfdescription:
        #    self.updates_cmd.append("description %s " % self.vrfdescription)

        # if self.cfgrouterid:
        #    self.updates_cmd.append("router id %s " % self.cfgrouterid)

        # if self.trafficstatisticenable is not None:
        #    if self.trafficstatisticenable == "true":
        #        self.updates_cmd.append("traffic-statistics enable")
        #    else:
        #        self.updates_cmd.append("undo traffic-statistics enable")

    def create_process(self):
        """Create l3vpn process"""

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge l3vpn process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete l3vpn  process"""
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_L3VPN_HEAD % NE_COMMON_XML_OPERATION_DELETE
        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_L3VPN_TAIL

        recv_xml = set_nc_config(self.module, xml_str, True)
        self.check_response(recv_xml, "DELETE_PROCESS")

        # self.updates_cmd.append("undo ip vpn-instance %s" % self.vrfname)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.vrf_info = self.get_vrf_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.vrf_info:
                # create l3vpn process
                self.create_process()
            else:
                # merge l3vpn process
                self.merge_process()
        elif self.state == "absent":
            # if self.vrf_info:
                # remove l3vpn process
            self.delete_process()
            # else:
            # self.module.fail_json(msg='Error: VRF instance does not exist')
        # elif self.state == "query":
            # if not self.vrf_info:
            # self.module.fail_json(msg='Error: VRF instance does not exist')
            # continue

        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
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
    """main"""

    argument_spec = dict(
        vrfname=dict(required=True, type='str'),
        vrfdescription=dict(required=False, type='str'),
        cfgrouterid=dict(required=False, type='str'),
        trafficstatisticenable=dict(required=False, choices=['true', 'false']),
        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = Vrf(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
