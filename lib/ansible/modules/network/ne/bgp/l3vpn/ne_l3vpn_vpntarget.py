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
module: ne_l3vpn_vpntarget
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
    aftype:
        description:
            - VPN instance address family.
        required: false
        choices: ['ipv4uni','ipv6uni']
        default: ipv4uni
    vrfrttype:
        description:
            - VPN instance vpn target type.RT types are as follows:
                export-extcommunity: Specifies the value of the extended community attribute of the route from an outbound interface to the destination VPN.
                import-extcommunity: Receives routes that carry the specified extended community attribute value.
        required: false
        choices: ['export_extcommunity', 'import_extcommunity']
        default: null
    vrfrtvalue:
        description:
            - VPN instance target value. The formats of a VPN target value are as follows:
                (1) 16-bit AS number : 32-bit user-defined number, for example, 1:3. An AS number ranges from 0 to 65535,
                    and a user-defined number ranges from 0 to 4294967295. The AS number and user-defined number cannot be both 0s.
                    This means that the VPN Target value cannot be 0:0.
                (2) 32-bit IP address: 16-bit user-defined number, for example: 192.168.122.15:1.
                    The IP address ranges from 0.0.0.0 to 255.255.255.255, and the user-defined number ranges from 0 to 65535.
                (3) 32-bit AS number :16-bit user-defined number, for example, 10.11:3.
                    An AS number ranges from 0.0 to 65535.65535 or 0 to 4294967295,
                    and a user-defined number ranges from 0 to 65535. The AS number and user-defined number cannot be both 0s.
                    This means that the VPN Target value cannot be 0.0:0.
        required: false
    state:
        description:
            - Manage the state of the vpntarget.
        required: false
        choices: ['present','absent']
        default: present
'''

EXAMPLES = '''
- name: netengine L3VPN vpntarget module test
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

  - name: Config vpna, set address family is ipv4
    ne_l3vpn_vpntarget:
      vrfname: vpna
      aftype: ipv4uni
      state: present
      provider: "{{ cli }}"
  - name: Config vpna, delete address family is ipv4
    ne_l3vpn_vpntarget:
      vrfname: vpna
      aftype: ipv4uni
      state: absent
      provider: "{{ cli }}"
  - name: Config vpna, set address family is ipv4,set vrfrttype=export_extcommunity,vrfrtvalue=2:2,
    ne_l3vpn_vpntarget:
      vrfname: vpna
      aftype: ipv4uni
      vrfrttype: export_extcommunity
      vrfrtvalue: 2:2
      state: present
      provider: "{{ cli }}"
  - name: Config vpna, set address family is ipv4,delete vrfrttype=export_extcommunity,vrfrtvalue=2:2
    ne_l3vpn_vpntarget:
      vrfname: vpna
      aftype: ipv4uni
      vrfrttype: export_extcommunity
      vrfrtvalue: 2:2
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
        "vrfrttype": "export_extcommunity",
        "vrfrtvalue": "10:3"
             }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {
        "vpnInstAF": [
            {
                "aftype": "ipv4uni",
            }
        ],
        "vrfname": "vpna"
    }
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  {
        "vpnInstAF": [
            {
                "aftype": "ipv4uni",
                "vpnTargets": [
                    {
                        "vrfrttype": "export_extcommunity",
                        "vrfrtvalue": "10:3"
                    }
                ],
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
        "ipv4-family",
        "vpn-target 3:3 import_extcommunity"
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


def is_valid_value(vrf_targe_value):
    """check if the vrf target value is valid"""

    each_num = None
    if len(vrf_targe_value) > 21 or len(vrf_targe_value) < 3:
        return False
    if vrf_targe_value.find(':') == -1:
        return False
    elif vrf_targe_value == '0:0':
        return False
    elif vrf_targe_value == '0.0:0':
        return False
    else:
        value_list = vrf_targe_value.split(':')
        if value_list[0].find('.') != -1:
            if not value_list[1].isdigit():
                return False
            if int(value_list[1]) > 65535:
                return False
            value = value_list[0].split('.')
            if len(value) == 4:
                for each_num in value:
                    if not each_num.isdigit():
                        return False
                if int(each_num) > 255:
                    return False
                return True
            elif len(value) == 2:
                for each_num in value:
                    if not each_num.isdigit():
                        return False
                if int(each_num) > 65535:
                    return False
                return True
            else:
                return False
        elif not value_list[0].isdigit():
            return False
        elif not value_list[1].isdigit():
            return False
        elif int(value_list[0]) < 65536 and int(value_list[1]) < 4294967296:
            return True
        elif int(value_list[0]) > 65535 and int(value_list[0]) < 4294967296:
            return bool(int(value_list[1]) < 65536)
        else:
            return False


class VpnTarget(object):
    """manage the vrf address family and export/import target"""

    def __init__(self, argument_spec, ):
        self.spec = argument_spec
        self.module = None
        self.init_module()
        # vpn instance info
        self.vrfname = self.module.params['vrfname']
        self.aftype = self.module.params['aftype']
        self.vrfrttype = self.module.params['vrfrttype']
        self.vrfrtvalue = self.module.params['vrfrtvalue']

        self.state = self.module.params['state']
        # state
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()
        self.vpn_target_changed = False

        self.changed = False
        self.vrf_af_vpntarget_info = dict()

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
            self.updates_cmd.append('ip vpn-instance %s' % (self.vrfname))
            if self.aftype == 'ipv4uni':
                self.updates_cmd.append('ipv4-family')
            elif self.aftype == 'ipv6uni':
                self.updates_cmd.append('ipv6-family')
            if self.vrfrtvalue and self.vrfrttype:
                self.updates_cmd.append(
                    'vpn-target %s %s' % (self.vrfrtvalue, self.vrfrttype))
        else:
            self.updates_cmd.append('ip vpn-instance %s' % (self.vrfname))
            if self.aftype == 'ipv4uni':
                self.updates_cmd.append('undo ipv4-family')
            elif self.aftype == 'ipv6uni':
                self.updates_cmd.append('undo ipv6-family')
            if self.vrfrtvalue and self.vrfrttype:
                self.updates_cmd.append(
                    'vpn-target %s %s' % (self.vrfrtvalue, self.vrfrttype))

    def get_vrf(self):
        """ check if vrf is need to change"""

        getxmlstr = NE_COMMON_XML_GET_L3VPN_HEAD
        getxmlstr = constr_leaf_novalue(getxmlstr, "vrfName")
        getxmlstr += NE_COMMON_XML_GET_L3VPN_TAIL
        xmlstr_new_1 = (self.vrfname)
        xml_str = get_nc_config(self.module, getxmlstr)
        re_find_1 = re.findall(
            r'.*<vrfname>(.*)</vrfname>.*', xml_str.lower())

        if re_find_1 is None:
            return False

        return xmlstr_new_1 in re_find_1

    def get_vrf_af_vpntarget(self):
        """ Get L3VPN VpnTarget informaton to the dictionary."""

        vrf_af_vpntarget_info = dict()
        # Head info
        getxmlstr = NE_COMMON_XML_GET_L3VPN_HEAD
        # vrfname Key
        getxmlstr = constr_leaf_value(getxmlstr, "vrfName", self.vrfname)
        # Body info
        getxmlstr = constr_container_head(getxmlstr, "vpnInstAFs")
        getxmlstr = constr_container_head(getxmlstr, "vpnInstAF")
        # Body info
        # aftype Key
        getxmlstr = constr_leaf_novalue(getxmlstr, "afType")
        # Vpn Targets info
        getxmlstr = constr_container_head(getxmlstr, "vpnTargets")
        getxmlstr = constr_container_head(getxmlstr, "vpnTarget")
        getxmlstr = constr_leaf_novalue(getxmlstr, "vrfRTType")
        getxmlstr = constr_leaf_novalue(getxmlstr, "vrfRTValue")
        getxmlstr = constr_container_tail(getxmlstr, "vpnTarget")
        getxmlstr = constr_container_tail(getxmlstr, "vpnTargets")

        # Tail info
        getxmlstr = constr_container_tail(getxmlstr, "vpnInstAF")
        getxmlstr = constr_container_tail(getxmlstr, "vpnInstAFs")
        getxmlstr += NE_COMMON_XML_GET_L3VPN_TAIL

        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return None
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn"', "")

        root = ElementTree.fromstring(xml_str)

        vpnTargets = root.findall(
            "l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/vpnTargets/vpnTarget")
        if vpnTargets is None or len(vpnTargets) == 0:
            return None

        # VrfName information

        vrfInst = root.find("l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance")
        if vrfInst is None or len(vrfInst) == 0:
            return None

        for vrf in vrfInst:
            if vrf.tag in ["vrfName"]:
                vrf_af_vpntarget_info[vrf.tag.lower()] = vrf.text

        # vpninstaf information
        vpnInstAF = root.find(
            "l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF")
        if vpnInstAF is None or len(vpnInstAF) == 0:
            return None

        for vrfAF in vpnInstAF:
            if vrfAF.tag in ["afType"]:
                vrf_af_vpntarget_info[vrfAF.tag.lower()] = vrfAF.text

        vrf_af_vpntarget_info["vpnTarget"] = list()
        for vpnTarget in vpnTargets:
            vpnTarget_dict = dict()
            for ele in vpnTarget:
                if ele.tag in [
                        "vrfRTValue", "vrfRTType"]:
                    vpnTarget_dict[ele.tag.lower()] = ele.text

            vrf_af_vpntarget_info["vpnTarget"].append(vpnTarget_dict)
        return vrf_af_vpntarget_info

    def check_params(self):
        """Check all input params"""

        # if not self.vpn_target_state:
        #    if self.vrfrtvalue or self.vrfrttype:
        #        self.module.fail_json(
        #                msg='Error: The vpn_target_state should be exist.')
        # if self.vpn_target_state:
        #    if not self.vrfrtvalue or not self.vrfrttype:
        #        self.module.fail_json(
        #                msg='Error: The vrfrtvalue and vrfRTType should be exist.')
        # pass
        # if self.vrfname == '_public_':
        #    self.module.fail_json(
        #        msg='Error: The vrf name _public_ is reserved.')
        # if not self.get_vrf():
        #    self.module.fail_json(
        #        msg='Error: The vrf name do not exist.')
        # if self.state == 'present':
        #    if self.vrfRD:
        #        if not is_valid_value(self.vrfRD):
        #            self.module.fail_json(msg='Error:The vrf route distinguisher length must between 3 ~ 21,'
        #                                 'i.e. X.X.X.X:number<0-65535> or number<0-65535>:number<0-4294967295>'
        #                                  'or number<0-65535>.number<0-65535>:number<0-65535>'
        #                                  'or number<65536-4294967295>:number<0-65535>'
        #                                  ' but not be 0:0 or 0.0:0.')
        #    if self.imPolicyName:
        #        length_ex = len(self.imPolicyName)
        #        if length_ex > 40 or length_ex < 1 or self.imPolicyName.find(" ") >= 0:
        #            self.module.fail_json(msg='Error:The imPolicyName length must between 1 ~ 40, does not support blank space.')

        #    if self.exPolicyName:
        #        length_ex = len(self.exPolicyName)
        #        if length_ex > 40 or length_ex < 1 or self.exPolicyName.find(" ") >= 0:
        #            self.module.fail_json(msg='Error:The exPolicyName length must between 1 ~ 40, does not support blank space.')
        #    if self.vrfLabel and self.vrfLabel > 4294967295:
        #        self.module.fail_json(msg='Error: The vrfLabel is not in the range from 0 to 4294967295.')
        #    if self.tnlPolicyName:
        #        length_tnlPolicyNmae = len(self.tnlPolicyName)
        #        if length_tnlPolicyNmae < 1 or length_tnlPolicyNmae > 39:
        #            self.module.fail_json(msg='Error:The imPolicyName length must between 1 ~ 39.')

        #    if not self.vpn_target_state:
        #        if self.vrfrtvalue or self.vrfrttype:
        #            self.module.fail_json(
        #                msg='Error: The vpn_target_state should be exist.')
        #    if self.vpn_target_state:
        #        if not self.vrfrtvalue or not self.vrfrttype:
        #            self.module.fail_json(
        #                msg='Error: The vrfrtvalue and vrfrttype should be exist.')
        #    if self.vrfrtvalue:
        #        if not is_valid_value(self.vrfrtvalue):
        #            self.module.fail_json(msg='Error:The vrf target value length must between 3 ~ 21,'
        #                                  'i.e. X.X.X.X:number<0-65535> or number<0-65535>:number<0-4294967295>'
        #                                  'or number<0-65535>.number<0-65535>:number<0-65535>'
        #                                  'or number<65536-4294967295>:number<0-65535>'
        #                                  ' but not be 0:0 or 0.0:0.')

    def get_proposed(self):
        """Get proposed info"""

        self.proposed['vrfname'] = self.vrfname
        self.proposed['aftype'] = self.aftype

        if self.vrfrttype is not None:
            self.proposed['vrfrttype'] = self.vrfrttype
        if self.vrfrtvalue is not None:
            self.proposed['vrfrtvalue'] = self.vrfrtvalue

        self.proposed['state'] = self.state

    def get_existing(self):
        """get_existing"""
        if not self.vrf_af_vpntarget_info or len(
                self.vrf_af_vpntarget_info) == 0:
            return

        self.existing["vrfname"] = self.vrfname
        self.existing["aftype"] = self.aftype
        self.existing["vpnTarget"] = self.vrf_af_vpntarget_info["vpnTarget"]

    def get_end_state(self):
        """get_end_state"""
        vrf_af_vpntarget_info = self.get_vrf_af_vpntarget()
        if not vrf_af_vpntarget_info or len(vrf_af_vpntarget_info) == 0:
            return
        self.end_state['vrfname'] = self.vrfname
        self.end_state["aftype"] = self.aftype
        self.end_state['vpnTarget'] = vrf_af_vpntarget_info["vpnTarget"]

    def comm_process(self, operation, operation_Desc):
        """Comm  l3vpn process"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_L3VPN_HEAD_COMMON
        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        xml_str = constr_container_head(xml_str, "vpnInstAFs")
        xml_str = constr_container_head(xml_str, "vpnInstAF")
        xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
        xml_str = constr_container_process_head(
            xml_str, "vpnTarget", operation)
        xml_str = constr_leaf_value(xml_str, "vrfRTType", self.vrfrttype)
        xml_str = constr_leaf_value(xml_str, "vrfRTValue", self.vrfrtvalue)

        #
        # Tail process
        xml_str = constr_container_process_tail(xml_str, "vpnTarget")
        xml_str = constr_container_process_tail(xml_str, "vpnInstAF")
        xml_str += NE_COMMON_XML_PROCESS_L3VPN_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, operation_Desc)

        self.changed = True

    def create_process(self):
        """Create l3vpn process"""
        self.comm_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """ Merge l3vpn process """
        self.comm_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """ Merge l3vpn process """
        self.comm_process(NE_COMMON_XML_OPERATION_DELETE, "DELETE_PROCESS")

    def work(self):
        """worker"""
        self.check_params()
        self.vrf_af_vpntarget_info = self.get_vrf_af_vpntarget()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if not self.vrf_af_vpntarget_info:
                self.create_process()
            else:
                self.merge_process()
        elif self.state == "absent":
            if self.vrf_af_vpntarget_info:
                self.delete_process()
            else:
                self.module.fail_json(
                    msg='Error: L3VPN VrfTarget does not exist')
        elif self.state == "query":
            if not self.vrf_af_vpntarget_info:
                self.module.fail_json(
                    msg='Error: L3VPN VrfTarget does not exist')

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
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/afType
        aftype=dict(required=True, choices=['ipv4uni', 'ipv6uni']),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/vpnTargets/vpnTarget/vrfRTType
        vrfrttype=dict(
            required=True,
            choices=[
                'export_extcommunity',
                'import_extcommunity']),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/vpnTargets/vpnTarget/vrfRTValue
        vrfrtvalue=dict(required=True, type='str'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )
    argument_spec.update(ne_argument_spec)
    interface = VpnTarget(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
