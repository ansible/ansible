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

from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_container_process_tail
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_container_process_head
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_container_tail
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_container_head
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_leaf_novalue
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_leaf_value
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPN_TAIL
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPN_HEAD
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_GET_L3VPN_TAIL
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPN_HEAD_COMMON
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_GET_L3VPN_HEAD
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import re
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = '''
---
module: ne_l3vpn_l3vpnif
version_added: "2.6"
short_description: Manages VPN instance address family on HUAWEI CloudEngine switches.
description:
    - Manages VPN instance address family of HUAWEI CloudEngine switches.
author: wangyuanqiang (@netengine-Ansible)
notes:
    - If I(state=absent), the vrf will be removed, regardless of the
      non-required parameters.
options:
    vrfname:
        description:
            - VPN instance.
        required: true
        default: null
    ifname:
        description:
            - Interface name.
        required: true
        default: null
    ipv4addr:
        description:
            - Interface IP address. It is in dotted decimal notation, for example: 100.1.1.1.
        required: false
    subnetmask:
        description:
            - Mask of an interface address. It is in dotted decimal notation, for example: 255.255.0.0.
        required: false
    state:
        description:
            - Manage the state of the l3vpnif.
        required: false
        choices: ['present','absent']
        default: present
'''

EXAMPLES = '''
- name: netengine L3VPN l3vpnIf module test
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

  - name: Config vpna
    ne_l3vpn_l3vpnif:
      vrfname: vpna
      state: present
      provider: "{{ cli }}"
  - name: delete vpna
    ne_l3vpn_l3vpnif:
      vrfname: vpna
      state: absent
      provider: "{{ cli }}"
  - name: Config vpna, set ifname=LoopBack1 ipv4addr=100.1.1.1 subnetmask=255.255.0.0
    ne_l3vpn_l3vpnif:
      vrfname: vpna
      ifname: LoopBack1
      ipv4addr: 100.1.1.1
      subnetmask: 255.255.0.0

      state: present
      provider: "{{ cli }}"
  - name: Config vpna, delete l3vpnIf
    ne_l3vpn_l3vpnif:
      vrfname: vpna
      ifname: LoopBack1
      state: absent
      provider: "{{ cli }}"
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "ifname": "LoopBack1",
        "ipv4addr": "100.1.1.1",
        "subnetmask": "255.255.0.0",
        "vrfname": "vpna",
             }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {
        "l3vpnIf": [
            {
               "ifname": "LoopBack1",
               "ipv4addr": "100.1.1.1",
               "subnetmask": "255.255.0.0",
            }
        ],
        "vrfname": "vpna"
    }
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  {
        "l3vpnIf": [
            {
                "ifname": "LoopBack1",
                "ipv4addr": "100.1.1.1",
                "subnetmask": "255.255.0.0",
            }
        ],
        "vrfname": "vpna"
    }
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: [
        "ip vpn-instance vpna",
        "ip binding vpn-instance  vrf1 ",
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class VpnIf(object):
    """manage the vrf address family and export/import target"""

    def __init__(self, argument_spec, ):
        self.spec = argument_spec
        self.module = None
        self.init_module()
        # vpn instance info
        self.vrfname = self.module.params['vrfname']
        self.ifname = self.module.params['ifname']
        self.ipv4addr = self.module.params['ipv4addr']
        self.subnetmask = self.module.params['subnetmask']
        self.state = self.module.params['state']
        # state
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()
        self.vpn_target_changed = False

        self.changed = False
        self.vpn_if_info = dict()

    def init_module(self):
        """init_module"""

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_vpn_if(self):
        """Get L3VPN VpnIf information to the dictionary."""

        vpn_if_info = dict()
        # Head info
        getxmlstr = NE_COMMON_XML_GET_L3VPN_HEAD
        # vrfName Key
        getxmlstr = constr_leaf_value(getxmlstr, "vrfName", self.vrfname)
        # Body info
        getxmlstr = constr_container_head(getxmlstr, "l3vpnIfs")
        getxmlstr = constr_container_head(getxmlstr, "l3vpnIf")
        # Body info
        # ifName Key
        getxmlstr = constr_leaf_novalue(getxmlstr, "ifName")
        getxmlstr = constr_leaf_novalue(getxmlstr, "ipv4Addr")
        getxmlstr = constr_leaf_novalue(getxmlstr, "subnetMask")

        # Tail info
        getxmlstr = constr_container_tail(getxmlstr, "l3vpnIf")
        getxmlstr = constr_container_tail(getxmlstr, "l3vpnIfs")
        getxmlstr += NE_COMMON_XML_GET_L3VPN_TAIL

        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return None
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn"', "")

        root = ElementTree.fromstring(xml_str)
        # get the l3vpnIf
        vpnIfs = root.findall(
            "l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/l3vpnIfs/l3vpnIf")
        if vpnIfs is None or len(vpnIfs) == 0:
            return None

        # VrfName information
        vrfInst = root.find("l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance")
        if vrfInst is None or len(vrfInst) == 0:
            return None

        for vrf in vrfInst:
            if vrf.tag in ["vrfName"]:
                vpn_if_info[vrf.tag.lower()] = vrf.text

        # findall Returns None or element instances
        vpn_if_info["vpnIf"] = list()
        for vpnIf in vpnIfs:
            vpnIf_dict = dict()
            for ele in vpnIf:
                if ele.tag in [
                        "ifName", "ipv4Addr", "subnetMask"]:
                    vpnIf_dict[ele.tag.lower()] = ele.text

            vpn_if_info["vpnIf"].append(vpnIf_dict)
        return vpn_if_info

    def check_params(self):
        """Check all input params"""

    def get_proposed(self):
        """Get proposed info"""

        self.proposed['vrfname'] = self.vrfname
        self.proposed['ifname'] = self.ifname

        if self.ipv4addr is not None:
            self.proposed['ipv4addr'] = self.ipv4addr
        if self.subnetmask is not None:
            self.proposed['subnetmask'] = self.subnetmask

        self.proposed['state'] = self.state

    def get_existing(self):
        """get_existing"""
        if not self.vpn_if_info or len(self.vpn_if_info) == 0:
            return

        self.existing["vrfname"] = self.vrfname
        self.existing["vpnIf"] = self.vpn_if_info["vpnIf"]

    def get_end_state(self):
        """get_end_state"""
        vpn_if_info = self.get_vpn_if()
        if not vpn_if_info or len(vpn_if_info) == 0:
            return
        self.end_state['vrfname'] = self.vrfname
        self.end_state['vpnIf'] = vpn_if_info["vpnIf"]

    def comm_process(self, operation, operation_Desc):
        """Comm  l3vpn process"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_L3VPN_HEAD_COMMON
        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_process_head(xml_str, "l3vpnIf", operation)

        xml_str = constr_leaf_value(xml_str, "ifName", self.ifname)
        xml_str = constr_leaf_value(xml_str, "ipv4Addr", self.ipv4addr)
        xml_str = constr_leaf_value(xml_str, "subnetMask", self.subnetmask)

        #
        # Tail process
        xml_str = constr_container_process_tail(xml_str, "l3vpnIf")
        xml_str += NE_COMMON_XML_PROCESS_L3VPN_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, operation_Desc)

        self.changed = True

    def create_process(self):
        """Create isis process"""
        self.comm_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """ Merge isis process """
        self.comm_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """ Merge isis process """
        self.comm_process(NE_COMMON_XML_OPERATION_DELETE, "DELETE_PROCESS")

    def work(self):
        """worker"""
        self.check_params()
        self.vpn_if_info = self.get_vpn_if()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if not self.vpn_if_info:
                self.create_process()
            else:
                self.merge_process()
        elif self.state == "absent":
            if self.vpn_if_info:
                self.delete_process()
            else:
                self.module.fail_json(
                    msg='Error: L3VPN interface does not exist')
        elif self.state == "query":
            if not self.vpn_if_info:
                self.module.fail_json(
                    msg='Error: L3VPN interface does not exist')

        if self.state != "query":
            self.get_end_state()
            self.results['changed'] = self.changed
            self.results['end_state'] = self.end_state
            self.results['proposed'] = self.proposed

        self.results['existing'] = self.existing

        if self.changed:
            # self.set_update_cmd()
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """main"""

    argument_spec = dict(
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vrfName
        vrfname=dict(required=True, type='str'),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/l3vpnIfs/l3vpnIf/ifName
        ifname=dict(required=True, type='str'),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/l3vpnIfs/l3vpnIf/ipv4Addr
        ipv4addr=dict(required=False, type='str'),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/l3vpnIfs/l3vpnIf/subnetMask
        subnetmask=dict(required=False, type='str'),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = VpnIf(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
