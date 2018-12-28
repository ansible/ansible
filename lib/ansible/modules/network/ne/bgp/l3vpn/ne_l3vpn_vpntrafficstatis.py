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
module: ne_l3vpn_vpntrafficstatis
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
  - name: Display vpntrafficstatis
    ne_l3vpn_vpntrafficstatis:
      vrfname: vpna
      vrfdescription: test
      cfgRouterid: 1.1.1.1
      trafficstatisticenable: true
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  {}
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: []
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class VpnTrafficStatis(object):
    """Manange vpn instance"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # vpn instance info
        self.vrfname = self.module.params['vrfname']
        self.state = self.module.params['state']

        # traffic statistics info
        self.traffic_statistics_info = dict()

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

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_traffic_statistics_dict(self):
        """ get one vrf attributes dict."""

        traffic_statistics_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_L3VPN_HEAD

        # Body info
        conf_str = constr_leaf_value(conf_str, "vrfName", self.vrfname)
        conf_str = constr_container_head(conf_str, "vpnTrafficStatis")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatInTrafficRate")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatOutTrafficRate")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatInPacketsRate")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatOutPacketsRate")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatInBytes")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatOutBytes")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatInPackets")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatOutPackets")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatInUnicastPackets")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatOutUnicastPackets")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatInMulticastPackets")
        conf_str = constr_leaf_novalue(
            conf_str, "l3vpnStatOutMulticastPackets")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatInBroadcastPackets")
        conf_str = constr_leaf_novalue(
            conf_str, "l3vpnStatOutBroadcastPackets")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatResetTime")
        conf_str = constr_leaf_novalue(conf_str, "l3vpnStatResetStatistics")

        conf_str = constr_container_tail(conf_str, "vpnTrafficStatis")
        # Tail info
        conf_str += NE_COMMON_XML_GET_L3VPN_TAIL
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)
        xml_str = get_nc_config(self.module, conf_str, True)
        if "<data/>" in xml_str:
            return traffic_statistics_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn"', "")

        # get process base info
        # re_find = re.findall(
        #    r'.*<instanceId>(.*)</instanceId>.*', xml_str)

        root = ElementTree.fromstring(xml_str)
        # get the l3vpnIf
        vpnTrafficStatistics = root.findall(
            "l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/l3vpnIfs/l3vpnIf")
        if vpnTrafficStatistics is None or len(vpnTrafficStatistics) == 0:
            return None

        # VrfName information
        vrfInst = root.find("l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance")
        if vrfInst is None or len(vrfInst) == 0:
            return None

        for vrf in vrfInst:
            if vrf.tag in ["vrfName"]:
                traffic_statistics_info[vrf.tag.lower()] = vrf.text

        # findall Returns None or element instances
        traffic_statistics_info["vpnTrafficStatistic"] = list()
        for vpnTrafficStatistic in vpnTrafficStatistics:
            vpnTrafficStatistic_dict = dict()
            for ele in vpnTrafficStatistic:
                if ele.tag in ["l3vpnStatInTrafficRate",
                               "l3vpnStatOutTrafficRate",
                               "l3vpnStatInPacketsRate",
                               "l3vpnStatOutPacketsRate",
                               "l3vpnStatInBytes",
                               "l3vpnStatOutBytes",
                               "l3vpnStatInPackets",
                               "l3vpnStatOutPackets",
                               "l3vpnStatInUnicastPackets",
                               "l3vpnStatOutUnicastPackets",
                               "l3vpnStatInMulticastPackets",
                               "l3vpnStatOutMulticastPackets",
                               "l3vpnStatInBroadcastPackets",
                               "l3vpnStatOutBroadcastPackets",
                               "l3vpnStatResetTime",
                               "l3vpnStatResetStatistics"]:
                    vpnTrafficStatistic_dict[ele.tag.lower()] = ele.text

            traffic_statistics_info["vpnTrafficStatistic"].append(
                vpnTrafficStatistic_dict)
        return traffic_statistics_info

    def get_proposed(self):
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if not self.traffic_statistics_info:
            return

        self.existing = copy.deepcopy(self.traffic_statistics_info)

    def get_end_state(self):
        """get end state info"""

        traffic_statistics_info = self.get_traffic_statistics_dict()
        if not traffic_statistics_info:
            return

        self.end_state = copy.deepcopy(traffic_statistics_info)

    def common_process(self, operationType, operationDesc):
        """common process"""

    def create_process(self):
        """Create  process"""
        # not support

    def merge_process(self):
        """Merge l3vpn process"""

        # not support

    def delete_process(self):
        """Delete l3vpn  process"""
        # not support

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.traffic_statistics_info = self.get_traffic_statistics_dict()
        self.get_proposed()
        self.get_existing()

        if self.state != "query":
            self.module.fail_json(msg='Error: Operation not supported')

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
        vrfname=dict(required=False, type='str'),

        cfgRouterid=dict(required=False, type='str'),
        trafficstatisticenable=dict(required=False, choices=['true', 'false']),
        state=dict(required=False, default='query',
                   choices=['query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = VpnTrafficStatis(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
