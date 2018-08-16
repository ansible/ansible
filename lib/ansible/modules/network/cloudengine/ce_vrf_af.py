#!/usr/bin/python
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
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = '''
---
module: ce_vrf_af
version_added: "2.4"
short_description: Manages VPN instance address family on HUAWEI CloudEngine switches.
description:
    - Manages VPN instance address family of HUAWEI CloudEngine switches.
author: Yang yang (@CloudEngine-Ansible)
notes:
    - If I(state=absent), the vrf will be removed, regardless of the
      non-required parameters.
options:
    vrf:
        description:
            - VPN instance.
        required: true
    vrf_aftype:
        description:
            - VPN instance address family.
        choices: ['v4','v6']
        default: v4
    route_distinguisher:
        description:
            - VPN instance route distinguisher,the RD used to distinguish same route prefix from different vpn.
              The RD must be setted before setting vpn_target_value.
    vpn_target_state:
        description:
            - Manage the state of the vpn target.
        choices: ['present','absent']
    vpn_target_type:
        description:
            - VPN instance vpn target type.
        choices: ['export_extcommunity', 'import_extcommunity']
    vpn_target_value:
        description:
            - VPN instance target value. Such as X.X.X.X:number<0-65535> or number<0-65535>:number<0-4294967295>
              or number<0-65535>.number<0-65535>:number<0-65535> or number<65536-4294967295>:number<0-65535>
              but not support 0:0 and 0.0:0.
    evpn:
        description:
            - Is extend vpn or normal vpn.
        type: bool
        default: 'no'
    state:
        description:
            - Manage the state of the af.
        choices: ['present','absent']
        default: present
'''

EXAMPLES = '''
- name: vrf af module test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: Config vpna, set address family is ipv4
    ce_vrf_af:
      vrf: vpna
      vrf_aftype: v4
      state: present
      provider: "{{ cli }}"
  - name: Config vpna, delete address family is ipv4
    ce_vrf_af:
      vrf: vpna
      vrf_aftype: v4
      state: absent
      provider: "{{ cli }}"
  - name: Config vpna, set address family is ipv4,rd=1:1,set vpn_target_type=export_extcommunity,vpn_target_value=2:2
    ce_vrf_af:
      vrf: vpna
      vrf_aftype: v4
      route_distinguisher: 1:1
      vpn_target_type: export_extcommunity
      vpn_target_value: 2:2
      vpn_target_state: present
      state: present
      provider: "{{ cli }}"
  - name: Config vpna, set address family is ipv4,rd=1:1,delete vpn_target_type=export_extcommunity,vpn_target_value=2:2
    ce_vrf_af:
      vrf: vpna
      vrf_aftype: v4
      route_distinguisher: 1:1
      vpn_target_type: export_extcommunity
      vpn_target_value: 2:2
      vpn_target_state: absent
      state: present
      provider: "{{ cli }}"
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"vrf": "vpna",
             "vrf_aftype": "v4",
             "state": "present",
             "vpn_targe_state":"absent",
             "evpn": "none",
             "vpn_target_type": "none",
             "vpn_target_value": "none"}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  {
        "route_distinguisher": [
            "1:1",
            "2:2"
        ],
        "vpn_target_type": [],
        "vpn_target_value": [],
        "vrf": "vpna",
        "vrf_aftype": [
            "ipv4uni",
            "ipv6uni"
        ]
    }
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  {
        "route_distinguisher": [
            "1:1",
            "2:2"
        ],
        "vpn_target_type": [
            "import_extcommunity",
            "3:3"
        ],
        "vpn_target_value": [],
        "vrf": "vpna",
        "vrf_aftype": [
            "ipv4uni",
            "ipv6uni"
        ]
    }
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: [
        "ip vpn-instance vpna",
        "vpn-target 3:3 import_extcommunity"
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


import re
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec

CE_NC_GET_VRF = """
<filter type="subtree">
      <l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <l3vpncomm>
          <l3vpnInstances>
            <l3vpnInstance>
              <vrfName></vrfName>
              <vrfDescription></vrfDescription>
            </l3vpnInstance>
          </l3vpnInstances>
        </l3vpncomm>
      </l3vpn>
    </filter>
"""

CE_NC_GET_VRF_AF = """
<filter type="subtree">
  <l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <l3vpncomm>
      <l3vpnInstances>
        <l3vpnInstance>
          <vrfName>%s</vrfName>
          <vpnInstAFs>
            <vpnInstAF>
              <afType></afType>
              <vrfRD></vrfRD>%s
            </vpnInstAF>
          </vpnInstAFs>
        </l3vpnInstance>
      </l3vpnInstances>
    </l3vpncomm>
  </l3vpn>
</filter>
"""

CE_NC_DELETE_VRF_AF = """
<l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <l3vpncomm>
    <l3vpnInstances>
      <l3vpnInstance>
        <vrfName>%s</vrfName>
        <vpnInstAFs>
          <vpnInstAF operation="delete">
            <afType>%s</afType>
          </vpnInstAF>
        </vpnInstAFs>
      </l3vpnInstance>
  </l3vpnInstances>
  </l3vpncomm>
</l3vpn>
"""

CE_NC_CREATE_VRF_AF = """
<l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
  <l3vpncomm>
    <l3vpnInstances>
      <l3vpnInstance>
        <vrfName>%s</vrfName>
        <vpnInstAFs>
          <vpnInstAF operation="merge">
            <afType>%s</afType>
            <vrfRD>%s</vrfRD>%s
          </vpnInstAF>
        </vpnInstAFs>
      </l3vpnInstance>
    </l3vpnInstances>
  </l3vpncomm></l3vpn>
"""
CE_NC_CREATE_VRF_TARGET = """
<vpnTargets>
  <vpnTarget operation="merge">
    <vrfRTType>%s</vrfRTType>
    <vrfRTValue>%s</vrfRTValue>
  </vpnTarget>
</vpnTargets>
"""

CE_NC_DELETE_VRF_TARGET = """
<vpnTargets>
  <vpnTarget operation="delete">
    <vrfRTType>%s</vrfRTType>
    <vrfRTValue>%s</vrfRTValue>
  </vpnTarget>
</vpnTargets>
"""

CE_NC_GET_VRF_TARGET = """
<vpnTargets>
  <vpnTarget>
    <vrfRTValue></vrfRTValue>
    <vrfRTType></vrfRTType>
  </vpnTarget>
</vpnTargets>
"""

CE_NC_CREATE_EXTEND_VRF_TARGET = """
<exVpnTargets>
  <exVpnTarget operation="merge">
    <vrfRTType>%s</vrfRTType>
    <vrfRTValue>%s</vrfRTValue>
    <extAddrFamily>evpn</extAddrFamily>
  </exVpnTarget>
</exVpnTargets>
"""

CE_NC_DELETE_EXTEND_VRF_TARGET = """
<exVpnTargets>
  <exVpnTarget operation="delete">
    <vrfRTType>%s</vrfRTType>
    <vrfRTValue>%s</vrfRTValue>
    <extAddrFamily>evpn</extAddrFamily>
  </exVpnTarget>
</exVpnTargets>
"""

CE_NC_GET_EXTEND_VRF_TARGET = """
<exVpnTargets>
  <exVpnTarget>
    <vrfRTType></vrfRTType>
    <vrfRTValue></vrfRTValue>
    <extAddrFamily></extAddrFamily>
  </exVpnTarget>
</exVpnTargets>
"""


def build_config_xml(xmlstr):
    """build_config_xml"""

    return '<config> ' + xmlstr + ' </config>'


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
        self.vrf = self.module.params['vrf']
        self.vrf_aftype = self.module.params['vrf_aftype']
        if self.vrf_aftype == 'v4':
            self.vrf_aftype = 'ipv4uni'
        else:
            self.vrf_aftype = 'ipv6uni'
        self.route_distinguisher = self.module.params['route_distinguisher']
        self.evpn = self.module.params['evpn']
        self.vpn_target_type = self.module.params['vpn_target_type']
        self.vpn_target_value = self.module.params['vpn_target_value']
        self.vpn_target_state = self.module.params['vpn_target_state']
        self.state = self.module.params['state']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

        self.vpn_target_changed = False
        self.vrf_af_type_changed = False
        self.vrf_rd_changed = False
        self.vrf_af_info = dict()

    def init_module(self):
        """init_module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def is_vrf_af_exist(self):
        """is vrf address family exist"""

        if not self.vrf_af_info:
            return False

        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            if vrf_af_ele["afType"] == self.vrf_aftype:
                return True
            else:
                continue
        return False

    def get_exist_rd(self):
        """get exist route distinguisher """

        if not self.vrf_af_info:
            return None

        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            if vrf_af_ele["afType"] == self.vrf_aftype:
                if vrf_af_ele["vrfRD"] is None:
                    return None
                else:
                    return vrf_af_ele["vrfRD"]
            else:
                continue
        return None

    def is_vrf_rd_exist(self):
        """is vrf route distinguisher exist"""

        if not self.vrf_af_info:
            return False

        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            if vrf_af_ele["afType"] == self.vrf_aftype:
                if vrf_af_ele["vrfRD"] is None:
                    return False
                if self.route_distinguisher is not None:
                    return bool(vrf_af_ele["vrfRD"] == self.route_distinguisher)
                else:
                    return True
            else:
                continue
        return False

    def is_vrf_rt_exist(self):
        """is vpn target exist"""

        if not self.vrf_af_info:
            return False

        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            if vrf_af_ele["afType"] == self.vrf_aftype:
                if self.evpn is False:
                    if not vrf_af_ele.get("vpnTargets"):
                        return False
                    for vpn_target in vrf_af_ele.get("vpnTargets"):
                        if vpn_target["vrfRTType"] == self.vpn_target_type \
                                and vpn_target["vrfRTValue"] == self.vpn_target_value:
                            return True
                        else:
                            continue
                else:
                    if not vrf_af_ele.get("evpnTargets"):
                        return False
                    for evpn_target in vrf_af_ele.get("evpnTargets"):
                        if evpn_target["vrfRTType"] == self.vpn_target_type \
                                and evpn_target["vrfRTValue"] == self.vpn_target_value:
                            return True
                        else:
                            continue
            else:
                continue
        return False

    def set_update_cmd(self):
        """ set update command"""
        if not self.changed:
            return
        if self.state == "present":
            self.updates_cmd.append('ip vpn-instance %s' % (self.vrf))
            if self.vrf_aftype == 'ipv4uni':
                self.updates_cmd.append('ipv4-family')
            elif self.vrf_aftype == 'ipv6uni':
                self.updates_cmd.append('ipv6-family')
            if self.route_distinguisher:
                if not self.is_vrf_rd_exist():
                    self.updates_cmd.append(
                        'route-distinguisher %s' % self.route_distinguisher)
            else:
                if self.get_exist_rd() is not None:
                    self.updates_cmd.append(
                        'undo route-distinguisher %s' % self.get_exist_rd())
            if self.vpn_target_state == "present":
                if not self.is_vrf_rt_exist():
                    if self.evpn is False:
                        self.updates_cmd.append(
                            'vpn-target %s %s' % (self.vpn_target_value, self.vpn_target_type))
                    else:
                        self.updates_cmd.append(
                            'vpn-target %s %s evpn' % (self.vpn_target_value, self.vpn_target_type))
            elif self.vpn_target_state == "absent":
                if self.is_vrf_rt_exist():
                    if self.evpn is False:
                        self.updates_cmd.append(
                            'undo vpn-target %s %s' % (self.vpn_target_value, self.vpn_target_type))
                    else:
                        self.updates_cmd.append(
                            'undo vpn-target %s %s evpn' % (self.vpn_target_value, self.vpn_target_type))
        else:
            self.updates_cmd.append('ip vpn-instance %s' % (self.vrf))
            if self.vrf_aftype == 'ipv4uni':
                self.updates_cmd.append('undo ipv4-family')
            elif self.vrf_aftype == 'ipv6uni':
                self.updates_cmd.append('undo ipv6-family')

    def get_vrf(self):
        """ check if vrf is need to change"""

        getxmlstr = CE_NC_GET_VRF
        xmlstr_new_1 = (self.vrf.lower())

        xml_str = get_nc_config(self.module, getxmlstr)
        re_find_1 = re.findall(
            r'.*<vrfname>(.*)</vrfname>.*', xml_str.lower())

        if re_find_1 is None:
            return False

        return xmlstr_new_1 in re_find_1

    def get_vrf_af(self):
        """ check if vrf is need to change"""

        self.vrf_af_info["vpnInstAF"] = list()
        if self.evpn is True:
            getxmlstr = CE_NC_GET_VRF_AF % (
                self.vrf, CE_NC_GET_EXTEND_VRF_TARGET)
        else:
            getxmlstr = CE_NC_GET_VRF_AF % (self.vrf, CE_NC_GET_VRF_TARGET)

        xml_str = get_nc_config(self.module, getxmlstr)

        if 'data/' in xml_str:
            return self.state == 'present'
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        root = ElementTree.fromstring(xml_str)

        # get the vpn address family and RD text
        vrf_addr_types = root.findall(
            "data/l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance/vpnInstAFs/vpnInstAF")
        if vrf_addr_types:
            for vrf_addr_type in vrf_addr_types:
                vrf_af_info = dict()
                for vrf_addr_type_ele in vrf_addr_type:
                    if vrf_addr_type_ele.tag in ["vrfName", "afType", "vrfRD"]:
                        vrf_af_info[vrf_addr_type_ele.tag] = vrf_addr_type_ele.text
                    if vrf_addr_type_ele.tag == 'vpnTargets':
                        vrf_af_info["vpnTargets"] = list()
                        for rtargets in vrf_addr_type_ele:
                            rt_dict = dict()
                            for rtarget in rtargets:
                                if rtarget.tag in ["vrfRTValue", "vrfRTType"]:
                                    rt_dict[rtarget.tag] = rtarget.text
                            vrf_af_info["vpnTargets"].append(rt_dict)
                    if vrf_addr_type_ele.tag == 'exVpnTargets':
                        vrf_af_info["evpnTargets"] = list()
                        for rtargets in vrf_addr_type_ele:
                            rt_dict = dict()
                            for rtarget in rtargets:
                                if rtarget.tag in ["vrfRTValue", "vrfRTType"]:
                                    rt_dict[rtarget.tag] = rtarget.text
                            vrf_af_info["evpnTargets"].append(rt_dict)
                self.vrf_af_info["vpnInstAF"].append(vrf_af_info)

    def check_params(self):
        """Check all input params"""

        # vrf and description check
        if self.vrf == '_public_':
            self.module.fail_json(
                msg='Error: The vrf name _public_ is reserved.')
        if not self.get_vrf():
            self.module.fail_json(
                msg='Error: The vrf name do not exist.')
        if self.state == 'present':
            if self.route_distinguisher:
                if not is_valid_value(self.route_distinguisher):
                    self.module.fail_json(msg='Error:The vrf route distinguisher length must between 3 ~ 21,'
                                          'i.e. X.X.X.X:number<0-65535> or number<0-65535>:number<0-4294967295>'
                                          'or number<0-65535>.number<0-65535>:number<0-65535>'
                                          'or number<65536-4294967295>:number<0-65535>'
                                          ' but not be 0:0 or 0.0:0.')
            if not self.vpn_target_state:
                if self.vpn_target_value or self.vpn_target_type:
                    self.module.fail_json(
                        msg='Error: The vpn target state should be exist.')
            if self.vpn_target_state:
                if not self.vpn_target_value or not self.vpn_target_type:
                    self.module.fail_json(
                        msg='Error: The vpn target value and type should be exist.')
            if self.vpn_target_value:
                if not is_valid_value(self.vpn_target_value):
                    self.module.fail_json(msg='Error:The vrf target value length must between 3 ~ 21,'
                                          'i.e. X.X.X.X:number<0-65535> or number<0-65535>:number<0-4294967295>'
                                          'or number<0-65535>.number<0-65535>:number<0-65535>'
                                          'or number<65536-4294967295>:number<0-65535>'
                                          ' but not be 0:0 or 0.0:0.')

    def operate_vrf_af(self):
        """config/delete vrf"""

        vrf_target_operate = ''
        if self.route_distinguisher is None:
            route_d = ''
        else:
            route_d = self.route_distinguisher

        if self.state == 'present':
            if self.vrf_aftype:
                if self.is_vrf_af_exist():
                    self.vrf_af_type_changed = False
                else:
                    self.vrf_af_type_changed = True
                    configxmlstr = CE_NC_CREATE_VRF_AF % (
                        self.vrf, self.vrf_aftype, route_d, vrf_target_operate)
            else:
                self.vrf_af_type_changed = bool(self.is_vrf_af_exist())

            if self.vpn_target_state == 'present':
                if self.evpn is False and not self.is_vrf_rt_exist():
                    vrf_target_operate = CE_NC_CREATE_VRF_TARGET % (
                        self.vpn_target_type, self.vpn_target_value)
                    configxmlstr = CE_NC_CREATE_VRF_AF % (
                        self.vrf, self.vrf_aftype, route_d, vrf_target_operate)
                    self.vpn_target_changed = True
                if self.evpn is True and not self.is_vrf_rt_exist():
                    vrf_target_operate = CE_NC_CREATE_EXTEND_VRF_TARGET % (
                        self.vpn_target_type, self.vpn_target_value)
                    configxmlstr = CE_NC_CREATE_VRF_AF % (
                        self.vrf, self.vrf_aftype, route_d, vrf_target_operate)
                    self.vpn_target_changed = True
            elif self.vpn_target_state == 'absent':
                if self.evpn is False and self.is_vrf_rt_exist():
                    vrf_target_operate = CE_NC_DELETE_VRF_TARGET % (
                        self.vpn_target_type, self.vpn_target_value)
                    configxmlstr = CE_NC_CREATE_VRF_AF % (
                        self.vrf, self.vrf_aftype, route_d, vrf_target_operate)
                    self.vpn_target_changed = True
                if self.evpn is True and self.is_vrf_rt_exist():
                    vrf_target_operate = CE_NC_DELETE_EXTEND_VRF_TARGET % (
                        self.vpn_target_type, self.vpn_target_value)
                    configxmlstr = CE_NC_CREATE_VRF_AF % (
                        self.vrf, self.vrf_aftype, route_d, vrf_target_operate)
                    self.vpn_target_changed = True
            else:
                if self.route_distinguisher:
                    if not self.is_vrf_rd_exist():
                        configxmlstr = CE_NC_CREATE_VRF_AF % (
                            self.vrf, self.vrf_aftype, route_d, vrf_target_operate)
                        self.vrf_rd_changed = True
                    else:
                        self.vrf_rd_changed = False
                else:
                    if self.is_vrf_rd_exist():
                        configxmlstr = CE_NC_CREATE_VRF_AF % (
                            self.vrf, self.vrf_aftype, route_d, vrf_target_operate)
                        self.vrf_rd_changed = True
                    else:
                        self.vrf_rd_changed = False
            if not self.vrf_rd_changed and not self.vrf_af_type_changed and not self.vpn_target_changed:
                self.changed = False
            else:
                self.changed = True
        else:
            if self.is_vrf_af_exist():
                configxmlstr = CE_NC_DELETE_VRF_AF % (
                    self.vrf, self.vrf_aftype)
                self.changed = True
            else:
                self.changed = False

        if not self.changed:
            return

        conf_str = build_config_xml(configxmlstr)

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "OPERATE_VRF_AF")

    def get_proposed(self):
        """get_proposed"""

        if self.state == 'present':
            self.proposed['vrf'] = self.vrf
            if self.vrf_aftype is None:
                self.proposed['vrf_aftype'] = 'ipv4uni'
            else:
                self.proposed['vrf_aftype'] = self.vrf_aftype
            if self.route_distinguisher is not None:
                self.proposed['route_distinguisher'] = self.route_distinguisher
            else:
                self.proposed['route_distinguisher'] = list()
            if self.vpn_target_state == 'present':
                self.proposed['evpn'] = self.evpn
                self.proposed['vpn_target_type'] = self.vpn_target_type
                self.proposed['vpn_target_value'] = self.vpn_target_value
            else:
                self.proposed['vpn_target_type'] = list()
                self.proposed['vpn_target_value'] = list()
        else:
            self.proposed = dict()
            self.proposed['state'] = self.state
            self.proposed['vrf'] = self.vrf
            self.proposed['vrf_aftype'] = list()
            self.proposed['route_distinguisher'] = list()
            self.proposed['vpn_target_value'] = list()
            self.proposed['vpn_target_type'] = list()

    def get_existing(self):
        """get_existing"""

        self.get_vrf_af()
        self.existing['vrf'] = self.vrf
        self.existing['vrf_aftype'] = list()
        self.existing['route_distinguisher'] = list()
        self.existing['vpn_target_value'] = list()
        self.existing['vpn_target_type'] = list()
        self.existing['evpn_target_value'] = list()
        self.existing['evpn_target_type'] = list()
        if self.vrf_af_info["vpnInstAF"] is None:
            return
        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            self.existing['vrf_aftype'].append(vrf_af_ele["afType"])
            self.existing['route_distinguisher'].append(
                vrf_af_ele["vrfRD"])
            if vrf_af_ele.get("vpnTargets"):
                for vpn_target in vrf_af_ele.get("vpnTargets"):
                    self.existing['vpn_target_type'].append(
                        vpn_target["vrfRTType"])
                    self.existing['vpn_target_value'].append(
                        vpn_target["vrfRTValue"])
            if vrf_af_ele.get("evpnTargets"):
                for evpn_target in vrf_af_ele.get("evpnTargets"):
                    self.existing['evpn_target_type'].append(
                        evpn_target["vrfRTType"])
                    self.existing['evpn_target_value'].append(
                        evpn_target["vrfRTValue"])

    def get_end_state(self):
        """get_end_state"""

        self.get_vrf_af()
        self.end_state['vrf'] = self.vrf
        self.end_state['vrf_aftype'] = list()
        self.end_state['route_distinguisher'] = list()
        self.end_state['vpn_target_value'] = list()
        self.end_state['vpn_target_type'] = list()
        self.end_state['evpn_target_value'] = list()
        self.end_state['evpn_target_type'] = list()
        if self.vrf_af_info["vpnInstAF"] is None:
            return
        for vrf_af_ele in self.vrf_af_info["vpnInstAF"]:
            self.end_state['vrf_aftype'].append(vrf_af_ele["afType"])
            self.end_state['route_distinguisher'].append(vrf_af_ele["vrfRD"])
            if vrf_af_ele.get("vpnTargets"):
                for vpn_target in vrf_af_ele.get("vpnTargets"):
                    self.end_state['vpn_target_type'].append(
                        vpn_target["vrfRTType"])
                    self.end_state['vpn_target_value'].append(
                        vpn_target["vrfRTValue"])
            if vrf_af_ele.get("evpnTargets"):
                for evpn_target in vrf_af_ele.get("evpnTargets"):
                    self.end_state['evpn_target_type'].append(
                        evpn_target["vrfRTType"])
                    self.end_state['evpn_target_value'].append(
                        evpn_target["vrfRTValue"])

    def work(self):
        """worker"""

        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.operate_vrf_af()
        self.set_update_cmd()
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
        vrf=dict(required=True, type='str'),
        vrf_aftype=dict(choices=['v4', 'v6'],
                        default='v4', required=False),
        route_distinguisher=dict(required=False, type='str'),
        evpn=dict(type='bool', default=False),
        vpn_target_type=dict(
            choices=['export_extcommunity', 'import_extcommunity'], required=False),
        vpn_target_value=dict(required=False, type='str'),
        vpn_target_state=dict(choices=['absent', 'present'], required=False),
        state=dict(choices=['absent', 'present'],
                   default='present', required=False),
    )
    argument_spec.update(ce_argument_spec)
    interface = VrfAf(argument_spec)
    interface.work()


if __name__ == '__main__':
    main()
