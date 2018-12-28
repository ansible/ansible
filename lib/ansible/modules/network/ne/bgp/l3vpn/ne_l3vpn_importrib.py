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
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPNCOMM_TAIL
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPNCOMM_HEAD
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_GET_L3VPNCOMM_TAIL
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_GET_L3VPNCOMM_HEAD
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
module: ne_l3vpn_importrib
version_added: "2.6"
short_description: Configures the list of imported routes by public. on HUAWEI CloudEngine switches.
description:
    - Configures the list of imported routes by public. Manages VPN instance of HUAWEI CloudEngine switches.
author: wangyuanqiang (@netengine-Ansible)
notes:
    - If I(state=absent), the imported routes will be removed, regardless of the
      non-required parameters.
options:
    aftype:
        description:
            - VPN instance address family.
        required: true
        choices: ['ipv4uni','ipv6uni']
        default: ipv4uni
    srcvrfname:
        description:
            - VPN instance name. It uniquely identifies a VPN instance. The name is a string of case-sensitive characters.
        required: true
    protocol:
        description:
            - Specifies a routing protocol from which routes can be imported.
        required: true
        choices: ['ALL', 'Direct', 'OSPF', 'ISIS', 'Static',
                  'RIP', 'BGP', 'OSPFV3', 'RIPNG', 'Total',
                  'NetStream', 'VlinkDirect', 'INVALID']
        default: null
    processid:
        description:
            - Specifies the process ID of an imported routing protocol.
              The process ID must be specified if the imported routing protocol is RIP, OSPF, RIPng, or OSPFv3.
        required: true
        default: null
    policyname:
        description:
            - When routes are imported from other routing protocols,
              the Route-Policy filter specified by the parameter can be used to filter the routes and change the route attributes.
        required: false
    validrtenable:
        description:
            - Imported all valid route.When condition:protocol='BGP'
        required: false
        choices: ['true', 'false']
        default: false
    validrouteenable:
        description:
            - Imported Valid Route.
        required: false
        choices: ['true','false']
        default: false
'''

EXAMPLES = '''
- name: netengine L3VPN importRib module test
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

  - name: Config vpn instanc vpna
    ne_l3vpn_l3vpnInstance:
      vrfName: vpna
      vrfDescription: test
      state: present
      provider: "{{ cli }}"
  - name: Create importRib, set address family is ipv4, set srcvrfname=vpna,
            set protocol=ISIS, processid=1, validrouteenable=false, state=present
    ne_l3vpn_importrib:
      aftype: ipv4uni
      srcvrfname: vpna
      protocol: ISIS
      processid: 1
      validrouteenable: false
      state: present
      provider: "{{ cli }}"
  - name: Config importRib, set address family is ipv4, set srcvrfname=vpna,
            set protocol=Direct, processid=0, validrouteenable=false, state=present
    ne_l3vpn_importrib:
      aftype: ipv4uni
      srcvrfname: vpna
      protocol: Direct
      processid: 0
      validrouteenable: false
      state: present
      provider: "{{ cli }}"
  - name: Delete importRib, which address family is ipv4, srcvrfname=vpna,
            protocol=Direct, processid=0
    ne_l3vpn_vpnInstAF:
      aftype: ipv4uni
      srcvrfname: vpna
      protocol: Direct
      processid: 0
      state: absent
      provider: "{{ cli }}"
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
            "aftype": "ipv4uni",
            "processid": 1,
            "protocol": "ISIS",
            "srcvrfname": "l3vpn_test",
            "state": "present",
            "validrouteenable": "false"
             }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {
       "importRibs": [
            {
                "aftype": "ipv4uni",
                "processid": "1",
                "protocol": "OSPF",
                "srcvrfname": "l3vpn_test",
                "validrouteenable": "false"
            },
            {
                "aftype": "ipv4uni",
                "processid": "0",
                "protocol": "Direct",
                "srcvrfname": "l3vpn_test",
                "validrouteenable": "false"
            }
        ]
    }
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  {
        "importRibs": [
            {
                "aftype": "ipv4uni",
                "processid": "1",
                "protocol": "ISIS",
                "srcvrfname": "l3vpn_test",
                "validrouteenable": "false"
            },
            {
                "aftype": "ipv4uni",
                "processid": "1",
                "protocol": "OSPF",
                "srcvrfname": "l3vpn_test",
                "validrouteenable": "false"
            },
            {
                "aftype": "ipv4uni",
                "processid": "0",
                "protocol": "Direct",
                "srcvrfname": "l3vpn_test",
                "validrouteenable": "false"
            }
        ]
    }
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: [
        "ip vpn-instance vpna",
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class l3vpn_importRib(object):
    """manage the vrf address family and export/import target"""

    def __init__(self, argument_spec, ):
        self.spec = argument_spec
        self.module = None
        self.init_module()
        # module input info
        self.aftype = self.module.params['aftype']
        self.srcvrfname = self.module.params['srcvrfname']
        self.protocol = self.module.params['protocol']
        self.processid = self.module.params['processid']
        self.policyname = self.module.params['policyname']
        self.validrtenable = self.module.params['validrtenable']
        self.validrouteenable = self.module.params['validrouteenable']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

        # vrfaf info
        self.importRibs_info = dict()

    def init_module(self):
        """init_module"""

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def set_update_cmd(self):
        """ set update command"""
        if not self.changed:
            return
        if self.state == "present":
            # self.updates_cmd.append('ip vpn-instance %s' % (self.vrfName))
            if self.aftype == 'ipv4uni':
                self.updates_cmd.append('ipv4-family')
            elif self.aftype == 'ipv6uni':
                self.updates_cmd.append('ipv6-family')
        else:
            # self.updates_cmd.append('ip vpn-instance %s' % (self.vrfName))
            if self.aftype == 'ipv4uni':
                self.updates_cmd.append('undo ipv4-family')
            elif self.aftype == 'ipv6uni':
                self.updates_cmd.append('undo ipv6-family')

    def get_l3vpn_info(self, flag):
        """ Get L3VPN VrfAf informaton to the dictionary."""

        importRibs_info = dict()
        # Head info
        getxmlstr = NE_COMMON_XML_GET_L3VPNCOMM_HEAD
        getxmlstr = constr_container_head(getxmlstr, "importRibs")
        getxmlstr = constr_container_head(getxmlstr, "importRib")

        # Body info
        getxmlstr = constr_leaf_value(getxmlstr, "afType", self.aftype)
        getxmlstr = constr_leaf_value(getxmlstr, "srcVrfName", self.srcvrfname)
        getxmlstr = constr_leaf_value(getxmlstr, "protocol", self.protocol)
        getxmlstr = constr_leaf_value(getxmlstr, "processId", self.processid)
        if flag == 0:
            getxmlstr = constr_leaf_value(getxmlstr, "validRouteEnable", self.validrouteenable)

        # Tail info
        getxmlstr = constr_container_tail(getxmlstr, "importRib")
        getxmlstr = constr_container_tail(getxmlstr, "importRibs")
        getxmlstr += NE_COMMON_XML_GET_L3VPNCOMM_TAIL

        xml_str = get_nc_config(self.module, getxmlstr)
        # No record return
        if 'data/' in xml_str:
            return

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn"', "")

        root = ElementTree.fromstring(xml_str)

        importRibs = root.findall(
            "l3vpn/l3vpncomm/importRibs/importRib")
        # findall Returns None or element instances
        if importRibs is not None and len(importRibs) != 0:
            # get importRibs
            importRib_info = list()
            for importRib in importRibs:
                importRib_dict = dict()
                for element in importRib:
                    if element.tag in ["afType", "srcVrfName", "protocol", "processId",
                                       "policyName", "validRtEnable", "validRouteEnable"]:
                        importRib_dict[element.tag.lower()] = element.text
                # end of for
                importRib_info.append(importRib_dict)
            importRibs_info["importRibs"] = importRib_info
            self.importRibs_info = importRibs_info

    def check_params(self):
        """Check all input params"""
        pass
        # check afType
        # if self.aftype:
        #    if self.aftype not in self.spec["afType"]["choices"]:
        #        self.module.fail_json(
        #            msg='Error: AfType is not in the range.')

        # check srcVrfName
        # if self.srcVrfName:
        #    if len(self.srcVrfName) > 63:
        #        self.module.fail_json(
        # msg='Error: The length of the srcVrf Name is not in the range from 1
        # to 63.')

        # check protocol
        # if self.protocol:
        #    if self.protocol not in self.spec["protocol"]["choices"]:
        #        self.module.fail_json(
        #            msg='Error: protocol is not in the range.')

    def get_proposed(self):
        """Get proposed info"""

        self.proposed['aftype'] = self.aftype
        self.proposed['srcvrfname'] = self.srcvrfname
        self.proposed['protocol'] = self.protocol
        self.proposed['processid'] = self.processid

        if self.policyname:
            self.proposed['policyname'] = self.policyname
        if self.validrtenable:
            self.proposed['validrtenable'] = self.validrtenable
        if self.validrouteenable:
            self.proposed['validrouteenable'] = self.validrouteenable

        self.proposed['state'] = self.state

    def get_existing(self):
        """get_existing"""

        if not self.importRibs_info:
            return
        self.existing = self.importRibs_info

    def get_end_state(self):
        """get_end_state"""
        self.get_l3vpn_info(1)
        if not self.importRibs_info:
            return
        self.end_state = self.importRibs_info

    def comm_process(self, operation, operation_Desc):
        """Comm  l3vpn process"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_L3VPNCOMM_HEAD

        # Body process
        # create means merge
        if NE_COMMON_XML_OPERATION_CREATE == operation:
            xml_str = constr_container_process_head(
                xml_str, "importRib", NE_COMMON_XML_OPERATION_MERGE)
        else:
            xml_str = constr_container_process_head(
                xml_str, "importRib", operation)
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
        xml_str = constr_leaf_value(xml_str, "srcVrfName", self.srcvrfname)
        xml_str = constr_leaf_value(xml_str, "protocol", self.protocol)
        xml_str = constr_leaf_value(xml_str, "processId", self.processid)
        xml_str = constr_leaf_value(xml_str, "policyName", self.policyname)
        xml_str = constr_leaf_value(
            xml_str, "validRtEnable", self.validrtenable)
        xml_str = constr_leaf_value(
            xml_str, "validRouteEnable", self.validrouteenable)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "importRib")
        xml_str += NE_COMMON_XML_PROCESS_L3VPNCOMM_TAIL

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
        # self.check_params()
        # self.get_l3vpn_info()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if not self.importRibs_info:
                self.create_process()
            else:
                self.merge_process()
        elif self.state == "absent":
            # if self.importRibs_info:
            self.delete_process()
            # else:
            # self.module.fail_json(msg='Error: importRib does not exist')
        elif self.state == "query":
            # if not self.importRibs_info:
                # self.module.fail_json(msg='Error: importRib does not exist')
            self.get_l3vpn_info(0)
        self.get_end_state()
        if self.state != "query":
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
    """Module main"""

    argument_spec = dict(
        # /l3vpn/l3vpncomm/importRibs/importRib
        aftype=dict(required=True, choices=['ipv4uni', 'ipv6uni']),
        # /l3vpn/l3vpncomm/importRibs/importRib/srcVrfName
        srcvrfname=dict(required=True, type='str'),
        # /l3vpn/l3vpncomm/importRibs/importRib/protocol
        protocol=dict(required=True, choices=['ALL', 'Direct', 'OSPF', 'ISIS', 'Static',
                                              'RIP', 'BGP', 'OSPFV3', 'RIPNG', 'Total',
                                              'NetStream', 'VlinkDirect', 'INVALID']),
        # /l3vpn/l3vpncomm/importRibs/importRib/processId
        processid=dict(required=True, type='int'),
        # /l3vpn/l3vpncomm/importRibs/importRib/policyName
        policyname=dict(required=False, type='str'),
        # /l3vpn/l3vpncomm/importRibs/importRib/validRtEnable
        validrtenable=dict(required=False, choices=['true', 'false']),
        # /l3vpn/l3vpncomm/importRibs/importRib/validRouteEnable
        validrouteenable=dict(required=False, choices=['true', 'false']),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    module = l3vpn_importRib(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
