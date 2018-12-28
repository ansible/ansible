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
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import constr_leaf_process
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPN_TAIL
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPN_HEAD
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_GET_L3VPN_TAIL
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_PROCESS_L3VPN_HEAD_COMMON
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_GET_L3VPN_HEAD
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.modules.network.ne.bgp.l3vpn.ne_l3vpn_def import NE_COMMON_XML_OPERATION_CLEAR
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import re
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = '''
---
module: ne_l3vpn_vpninstaf
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
    vrfrd:
        description:
            - VPN instance route distinguisher,the RD used to distinguish same route prefix from different vpn.
              The RD must be setted before setting vrfRTValue.
        required: false
    impolicyname:
        description:
            - Name of a route import policy. The policy is associating the VPN instance with an inbound routing policy.
        required: false
    expolicyname:
        description:
            - Name of a route export policy. The policy is associating the VPN instance with an outbound routing policy.
        required: false
    expolicyaddertfirst:
        description:
            - Advertise routes to vpnv4 add ERT first. The vrfrd and expolicyname must be setted.
        required: false
        choices: ['true','false']
        default: false
    vrflabelmode:
        description:
            - Method of distributing labels to VPN instance routes. The way which assigns the label depends on the paf value.
              If there are a large number of routes in a VPN instance, assign a label for each instance.
              This allows all routes in the instance to use one label.
        required: false
        choices: ['perInstance','perRoute', 'perNextHop']
        default: perRoute
    vrflabel:
        description:
            - Apply static label mode for the VPN instance route.
        required: false
    tnlpolicyname:
        description:
            - Name of a tunnel policy. It is used to associate the VPN instance with the specified tunnel policy.
              If no tunnel policy is configured, the default tunnel policy is used.
              Only LDP LSPs or static LSPs match the default tunnel policy, and load balancing is not performed for LSPs.
        required: false
    transitvpn:
        description:
            - Keep the VPN Instance status up.
        required: false
        choices: ['true','false']
        default: false
    vpnfrr:
        description:
            - Enables the VPN FRR function. By default, VPN FRR is disabled.
        required: false
        choices: ['true','false']
        default: false
    vpn_target_state:
        description:
            - Manage the state of the vpn target.
        required: false
        choices: ['present','absent']
    vrfRTType:
        description:
            - VPN instance vpn target type.RT types are as follows:
                export-extcommunity: Specifies the value of the extended community attribute of the route from an outbound interface to the destination VPN.
                import-extcommunity: Receives routes that carry the specified extended community attribute value.
        required: false
        choices: ['export_extcommunity', 'import_extcommunity']
        default: null
    vrfRTValue:
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
            - Manage the state of the af.
        required: false
        choices: ['present','absent']
        default: present
'''

EXAMPLES = '''
- name: netengine L3VPN vpnInstAF module test
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
    ne_l3vpn_vpninstaf:
      vrfname: vpna
      aftype: ipv4uni
      state: present
      provider: "{{ cli }}"
  - name: Config vpna, delete address family is ipv4
    ne_l3vpn_vpninstaf:
      vrfname: vpna
      aftype: ipv4uni
      state: absent
      provider: "{{ cli }}"
  - name: Config vpna, set address family is ipv4,vrfrd=1:1,set vrfRTType=export_extcommunity,vrfRTValue=2:2,
            set lspoperation=POP, expolicyaddertfirst=false, transitvpn=false, vpnfrr=false vrflabelmode=perInstance, vrflabel=9
    ne_l3vpn_vpninstaf:
      vrfname: vpna
      aftype: ipv4uni
      vrfrd: 1:1
      lspoperation: POP
      expolicyaddertfirst: false
      transitvpn: false
      vpnfrr: false
      vrflabelmode: perInstance
      vrflabel: 9

      state: present
      provider: "{{ cli }}"
  - name: Config vpna, set address family is ipv4,vrfrd=1:1,delete vrfRTType=export_extcommunity,vrfRTValue=2:2
    ne_l3vpn_vpninstaf:
      vrfname: vpna
      aftype: ipv4uni
      vrfrd: 1:1
      state: present
      provider: "{{ cli }}"
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "aftype": "ipv4uni",
        "expolicyaddertfirst": "false",
        "expolicyname": [],
        "impolicyname": [],
        "lspoperation": "POP",
        "tnlpolicyname": [],
        "transitvpn": "false",
        "vpnfrr": "false",
        "vrflabel": "9",
        "vrflabelmode": "perInstance",
        "vrfname": "vpna",
        "vrfrd": [],
             }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {
        "vpnInstAF": [
            {
                "aftype": "ipv4uni",
                "expolicyaddertfirst": "false",
                "lspoperation": "POP",
                "transitvpn": "false",
                "vpnfrr": "false",
                "vrflabelmode": "perRoute",
                "vrfrd": "1:1"
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
                "expolicyaddertfirst": "false",
                "lspoperation": "POP",
                "transitvpn": "false",
                "vpnfrr": "false",
                "vrflabelmode": "perInstance",
                "vrfrd": "10:2"
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


class VrfAf(object):
    """manage the vrf address family and export/import target"""

    def __init__(self, argument_spec, ):
        self.spec = argument_spec
        self.module = None
        self.init_module()
        # vpn instance info
        self.vrfname = self.module.params['vrfname']
        self.aftype = self.module.params['aftype']
        self.vrfrd = self.module.params['vrfrd']
        self.impolicyname = self.module.params['impolicyname']
        self.expolicyname = self.module.params['expolicyname']
        self.expolicyaddertfirst = self.module.params['expolicyaddertfirst']
        self.vrflabelmode = self.module.params['vrflabelmode']
        self.lspoperation = self.module.params['lspoperation']
        self.vrflabel = self.module.params['vrflabel']
        self.tnlpolicyname = self.module.params['tnlpolicyname']
        self.transitvpn = self.module.params['transitvpn']
        self.vpnfrr = self.module.params['vpnfrr']

        self.state = self.module.params['state']
        # state
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()
        self.vpn_target_changed = False

        self.changed = False
        self.vrf_af_info = dict()

    def init_module(self):
        """init_module"""

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def is_vrf_af_exist(self):
        """is vrf address family exist"""

        if not self.vrf_af_info:
            return False

        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            if vrf_af_ele["afType"] == self.aftype:
                return True
            else:
                continue
        return False

    def get_exist_rd(self):
        """get exist route distinguisher """

        if not self.vrf_af_info:
            return None

        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            if vrf_af_ele["afType"] == self.aftype:
                return vrf_af_ele.get("vrfRD")
            else:
                continue
        return None

    def is_vrf_rd_exist(self):
        """is vrf route distinguisher exist"""

        if not self.vrf_af_info:
            return False

        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            if vrf_af_ele["afType"] == self.aftype:
                if vrf_af_ele["vrfRD"] is None:
                    return False
                if self.vrfrd is not None:
                    return bool(vrf_af_ele["vrfRD"] == self.vrfrd)
                else:
                    return False
            else:
                continue
        return False

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
            if self.vrfrd:
                if not self.is_vrf_rd_exist():
                    self.updates_cmd.append(
                        'route-distinguisher %s' % self.vrfrd)
            else:
                if self.get_exist_rd() is not None:
                    self.updates_cmd.append(
                        'undo route-distinguisher %s' % self.get_exist_rd())
        else:
            self.updates_cmd.append('ip vpn-instance %s' % (self.vrfname))
            if self.aftype == 'ipv4uni':
                self.updates_cmd.append('undo ipv4-family')
            elif self.aftype == 'ipv6uni':
                self.updates_cmd.append('undo ipv6-family')

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

    def get_vrf_af(self):
        """ Get L3VPN VrfAf informaton to the dictionary."""

        self.vrf_af_info["vpnInstAF"] = list()
        # Head info
        getxmlstr = NE_COMMON_XML_GET_L3VPN_HEAD
        # vrfName Key
        getxmlstr = constr_leaf_value(getxmlstr, "vrfName", self.vrfname)
        # Body info
        getxmlstr = constr_container_head(getxmlstr, "vpnInstAFs")
        getxmlstr = constr_container_head(getxmlstr, "vpnInstAF")
        # Body info
        # aftype Key
        getxmlstr = constr_leaf_novalue(getxmlstr, "afType")
        getxmlstr = constr_leaf_novalue(getxmlstr, "vrfRD")
        getxmlstr = constr_leaf_novalue(getxmlstr, "imPolicyName")
        getxmlstr = constr_leaf_novalue(getxmlstr, "exPolicyName")
        getxmlstr = constr_leaf_novalue(getxmlstr, "exPolicyAddErtFirst")
        getxmlstr = constr_leaf_novalue(getxmlstr, "vrfLabelMode")
        getxmlstr = constr_leaf_novalue(getxmlstr, "lspOperation")
        getxmlstr = constr_leaf_novalue(getxmlstr, "vrfLabel")
        getxmlstr = constr_leaf_novalue(getxmlstr, "tnlPolicyName")
        getxmlstr = constr_leaf_novalue(getxmlstr, "transitVpn")
        getxmlstr = constr_leaf_novalue(getxmlstr, "vpnFrr")

        # Tail info
        getxmlstr = constr_container_tail(getxmlstr, "vpnInstAF")
        getxmlstr = constr_container_tail(getxmlstr, "vpnInstAFs")
        getxmlstr += NE_COMMON_XML_GET_L3VPN_TAIL

        xml_str = get_nc_config(self.module, getxmlstr)
        if 'data/' in xml_str:
            return
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-l3vpn"', "")

        root = ElementTree.fromstring(xml_str)
        # get the vpn address family and RD text
        vrf_addr_types = root.findall(
            "l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF")
        # findall Returns None or element instances
        if vrf_addr_types:
            for vrf_addr_type in vrf_addr_types:
                vrf_af_info = dict()
                for vrf_addr_type_ele in vrf_addr_type:

                    if vrf_addr_type_ele.tag in ["vrfName", "afType", "vrfRD", "imPolicyName", "exPolicyName",
                                                 "exPolicyAddErtFirst", "vrfLabelMode", "lspOperation", "vrfLabel", "tnlPolicyName", "transitVpn", "vpnFrr"]:

                        vrf_af_info[vrf_addr_type_ele.tag.lower()
                                    ] = vrf_addr_type_ele.text
                # vrf_af_info["vpnInstAF"]中添加vrf_af_info
                self.vrf_af_info["vpnInstAF"].append(vrf_af_info)

    def check_params(self):
        """Check all input params"""

        # if self.vrfname == '_public_':
        #    self.module.fail_json(
        #        msg='Error: The vrf name _public_ is reserved.')
        # if not self.get_vrf():
        #    self.module.fail_json(
        #        msg='Error: The vrf name do not exist.')
        # if self.state == 'present':
        #    if self.vrfrd:
        #        if not is_valid_value(self.vrfrd):
        #            self.module.fail_json(msg='Error:The vrf route distinguisher length must between 3 ~ 21,'
        #                                 'i.e. X.X.X.X:number<0-65535> or number<0-65535>:number<0-4294967295>'
        #                                  'or number<0-65535>.number<0-65535>:number<0-65535>'
        #                                  'or number<65536-4294967295>:number<0-65535>'
        #                                  ' but not be 0:0 or 0.0:0.')
        #    if self.impolicyname:
        #        length_ex = len(self.impolicyname)
        #        if length_ex > 40 or length_ex < 1 or self.impolicyname.find(" ") >= 0:
        #            self.module.fail_json(msg='Error:The impolicyname length must between 1 ~ 40, does not support blank space.')

        #    if self.expolicyname:
        #        length_ex = len(self.expolicyname)
        #        if length_ex > 40 or length_ex < 1 or self.expolicyname.find(" ") >= 0:
        #            self.module.fail_json(msg='Error:The expolicyname length must between 1 ~ 40, does not support blank space.')
        #    if self.vrflabel and self.vrflabel > 4294967295:
        #        self.module.fail_json(msg='Error: The vrflabel is not in the range from 0 to 4294967295.')
        #    if self.tnlpolicyname:
        #        length_tnlPolicyNmae = len(self.tnlpolicyname)
        #        if length_tnlPolicyNmae < 1 or length_tnlPolicyNmae > 39:
        #            self.module.fail_json(msg='Error:The impolicyname length must between 1 ~ 39.')

        #    if not self.vpn_target_state:
        #        if self.vrfRTValue or self.vrfRTType:
        #            self.module.fail_json(
        #                msg='Error: The vpn_target_state should be exist.')
        #    if self.vpn_target_state:
        #        if not self.vrfRTValue or not self.vrfRTType:
        #            self.module.fail_json(
        #                msg='Error: The vrfRTValue and vrfRTType should be exist.')
        #    if self.vrfRTValue:
        #        if not is_valid_value(self.vrfRTValue):
        #            self.module.fail_json(msg='Error:The vrf target value length must between 3 ~ 21,'
        #                                  'i.e. X.X.X.X:number<0-65535> or number<0-65535>:number<0-4294967295>'
        #                                  'or number<0-65535>.number<0-65535>:number<0-65535>'
        #                                  'or number<65536-4294967295>:number<0-65535>'
        #                                  ' but not be 0:0 or 0.0:0.')

    def get_proposed(self):
        """Get proposed info"""

        self.proposed['vrfname'] = self.vrfname
        self.proposed['aftype'] = self.aftype

        if self.vrfrd is not None:
            self.proposed['vrfrd'] = self.vrfrd
        if self.impolicyname is not None:
            self.proposed['impolicyname'] = self.impolicyname
        if self.expolicyname is not None:
            self.proposed['expolicyname'] = self.expolicyname
        if self.expolicyaddertfirst is not None:
            self.proposed['expolicyaddertfirst'] = self.expolicyaddertfirst
        if self.vrflabelmode is not None:
            self.proposed['vrflabelmode'] = self.vrflabelmode
        if self.lspoperation is not None:
            self.proposed['lspoperation'] = self.lspoperation
        if self.vrflabel is not None:
            self.proposed['vrflabel'] = self.vrflabel
        if self.tnlpolicyname is not None:
            self.proposed['tnlpolicyname'] = self.tnlpolicyname
        if self.transitvpn is not None:
            self.proposed['transitvpn'] = self.transitvpn
        if self.vpnfrr is not None:
            self.proposed['vpnfrr'] = self.vpnfrr

        self.proposed['state'] = self.state

    def get_existing(self):
        """get_existing"""

        if self.vrf_af_info["vpnInstAF"] is None:
            return
        self.existing["vrfname"] = self.vrfname
        self.existing["vpnInstAF"] = self.vrf_af_info["vpnInstAF"]

    def get_end_state(self):
        """get_end_state"""
        self.get_vrf_af()
        if self.vrf_af_info["vpnInstAF"] is None:
            return
        self.end_state['vrfname'] = self.vrfname
        self.end_state['vpnInstAF'] = self.vrf_af_info["vpnInstAF"]

    def comm_process(self, operation, operation_Desc):
        """Comm  l3vpn process"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_L3VPN_HEAD_COMMON
        # Body process
        xml_str = constr_leaf_value(xml_str, "vrfName", self.vrfname)
        # xml_str = constr_container_process_head(
        #    xml_str, "vpnInstAF", operation)
        ###
        if operation == NE_COMMON_XML_OPERATION_CLEAR:
            xml_str = constr_container_process_head(xml_str, "vpnInstAF", NE_COMMON_XML_OPERATION_MERGE)
            xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
            xml_str = constr_leaf_process(xml_str, "vrfRD", self.vrfrd)
            xml_str = constr_leaf_process(xml_str, "imPolicyName", self.impolicyname)
            xml_str = constr_leaf_process(xml_str, "exPolicyName", self.expolicyname)
            xml_str = constr_leaf_process(xml_str, "exPolicyAddErtFirst", self.expolicyaddertfirst)
            xml_str = constr_leaf_process(xml_str, "vrfLabelMode", self.vrflabelmode)
            xml_str = constr_leaf_process(xml_str, "lspOperation", self.lspoperation)
            xml_str = constr_leaf_process(xml_str, "vrfLabel", self.vrflabel)
            xml_str = constr_leaf_process(xml_str, "tnlPolicyName", self.tnlpolicyname)
            xml_str = constr_leaf_process(xml_str, "transitVpn", self.transitvpn)
            xml_str = constr_leaf_process(xml_str, "vpnFrr", self.vpnfrr)
        else:
            xml_str = constr_container_process_head(xml_str, "vpnInstAF", operation)
            xml_str = constr_leaf_value(xml_str, "afType", self.aftype)
            xml_str = constr_leaf_value(xml_str, "vrfRD", self.vrfrd)
            xml_str = constr_leaf_value(xml_str, "imPolicyName", self.impolicyname)
            xml_str = constr_leaf_value(xml_str, "exPolicyName", self.expolicyname)
            xml_str = constr_leaf_value(xml_str, "exPolicyAddErtFirst", self.expolicyaddertfirst)
            xml_str = constr_leaf_value(xml_str, "vrfLabelMode", self.vrflabelmode)
            xml_str = constr_leaf_value(xml_str, "lspOperation", self.lspoperation)
            xml_str = constr_leaf_value(xml_str, "vrfLabel", self.vrflabel)
            xml_str = constr_leaf_value(xml_str, "tnlPolicyName", self.tnlpolicyname)
            xml_str = constr_leaf_value(xml_str, "transitVpn", self.transitvpn)
            xml_str = constr_leaf_value(xml_str, "vpnFrr", self.vpnfrr)
        #
        # Tail process
        xml_str = constr_container_process_tail(xml_str, "vpnInstAF")
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

    def clear_process(self):
        """ Merge isis process """
        self.comm_process(NE_COMMON_XML_OPERATION_CLEAR, "MERGE_PROCESS")

    def work(self):
        """worker"""
        self.check_params()
        self.get_vrf_af()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if not self.vrf_af_info:
                self.create_process()
            else:
                self.merge_process()
        elif self.state == "absent":
            # if self.vrf_af_info:
            self.delete_process()
            # else:
            # self.module.fail_json(msg='Error: L3VPN VrfAf does not exist')
        # elif self.state == "query":
            # if not self.vrf_af_info:
            # self.module.fail_json(msg='Error: L3VPN VrfAf does not exist')
        elif self.state == "clear":
            if self.vrf_af_info:
                self.clear_process()

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
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/vrfRD
        vrfrd=dict(required=False, type='str'),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/imPolicyName
        impolicyname=dict(required=False, type='str'),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/exPolicyName
        expolicyname=dict(required=False, type='str'),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/exPolicyAddErtFirst
        expolicyaddertfirst=dict(required=False, choices=['true', 'false']),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/vrfLabelMode
        vrflabelmode=dict(
            required=False,
            choices=[
                'perInstance',
                'perRoute',
                'perNextHop']),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/lspOperation
        lspoperation=dict(required=False, choices=['POPGO', 'POP']),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/vrfLabel
        vrflabel=dict(required=False, type='int'),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/tnlPolicyName
        tnlpolicyname=dict(required=False, type='str'),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/transitVpn
        transitvpn=dict(required=False, choices=['true', 'false']),
        # /l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF/vpnFrr
        vpnfrr=dict(required=False, choices=['true', 'false']),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query', 'clear'])
    )
    argument_spec.update(ne_argument_spec)
    interface = VrfAf(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
