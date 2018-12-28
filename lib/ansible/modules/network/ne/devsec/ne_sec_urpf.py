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
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action_yang, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import collections
import re
DOCUMENTATION = '''
---
module: ne_sec_urpf
version_added: "2.6"
short_description: Interface URPF plug-in for supporting NETCONF or YANG
description:
    - Interface URPF plug-in for supporting NETCONF or YANG
          on Huawei NetEngine switches.
    - Each exposed node relies on Yang.If Yang was modified, and the plugin
          should be modified.
    - ifName support abbreviation.
author: chenzhixiang
extends_documentation_fragment: NetEngine
options:
    ifName:
        description:
            - Specify the interface
        required: false
        default: null
    secProtoFamily:
        description:
            - Protocol Family
        required: false
        default: null
        choices: ['ipv4','ipv6']
    secUrpfLoose:
        description:
            - URPF performs loose check
        required: false
        default: strict
        choices: ['strict','loose']
    secUrfpDefault:
        description:
            - The packets matching only the default route are discarded.
        required: false
        default: disallow for router, allow for atn
        choices: ['disallow', 'allow']
    secUrpfStatisticsEn:
        description:
            - Interface URPF discard statistics enable.
        required: false
        default: disable
        choices: ['enable', 'disable']
    secV4DiscardPkts:
        description:
            - Number of IPV4 packets discarded by URPF on LPUs.
        required: false
        default: null
    secV6DiscardPkts:
        description:
            - Number of IPV6 packets discarded by URPF on LPUs.
        required: false
        default: null
    secSlotId:
        description:
            - Slot number of the installed LPU.
        required: false
        default: null
    secDiscardPkts:
        description:
            - Number of packets discarded by URPF on LPUs.
              Must be an integer less than or equal to 18446744073709551615.
        required: false
        default: null

'''
EXAMPLES = '''

- name: "securpf"
  hosts: ne_test
  connection: netconf
  gather_facts: no
  ignore_errors: yes
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
  tasks:

  - name: "create"
    test: operation=create secProtoFamily=ipv6 ifName=GigabitEthernet1/1/1.8 provider={{ cli }}
'''

RETURN = '''
    "existing": [
        [
            {
                "ifName": "GigabitEthernet1/1/1.8",
                "secProtoFamily": "ipv6",
                "secUrfpDefault": "disallow",
                "secUrpfStatisticsEn": "disable",
                "secUrpfLoose": "strict"
            }
        ]
    ]
'''

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}


PRODUCT_SYSTERM = """
<filter type="subtree">
<system xmlns="http://www.huawei.com/netconf/vrp/huawei-system"></system>
</filter>
"""

SEC_URPF_CFG = """
<config>
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <ifName>%s</ifName>
        <secProtoFamily>%s</secProtoFamily>
        <secUrpfLoose>%s</secUrpfLoose>
        <secUrfpDefault>%s</secUrfpDefault>
        <secUrpfStatisticsEn>%s</secUrpfStatisticsEn>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</config>
"""

SEC_URPF_MERGE = """
<config>
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <ifName>%s</ifName>
        <secProtoFamily>%s</secProtoFamily>
        <secUrpfLoose>%s</secUrpfLoose>
        <secUrfpDefault>%s</secUrfpDefault>
        <secUrpfStatisticsEn>%s</secUrpfStatisticsEn>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</config>
"""

SEC_URPF_CFGGET = """
<filter type="subtree">
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf>
        <ifName/>
        <secProtoFamily/>
        <secUrpfLoose/>
        <secUrfpDefault/>
        <secUrpfStatisticsEn/>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</filter>
"""
SEC_URPF_CFGGETFIL = """
<filter type="subtree">
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf>
        <ifName>%s</ifName>
        <secProtoFamily>%s</secProtoFamily>
        <secUrpfLoose/>
        <secUrfpDefault/>
        <secUrpfStatisticsEn/>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</filter>
"""
SEC_URPF_CFGUNDO = """
<config>
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <ifName>%s</ifName>
        <secProtoFamily>%s</secProtoFamily>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</config>
"""
SEC_INTURPF_QUERY = """
<filter type="subtree">
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secdispintfurpfstats>
      <secdispintfurpfstat>
        <ifName/>
        <secV4DiscardPkts/>
        <secV6DiscardPkts/>
      </secdispintfurpfstat>
    </secdispintfurpfstats>
  </cpudefend>
</filter>
"""

SEC_INTURPF_RESET = """
  <cpudefend:secResetUrpf xmlns:cpudefend="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
      <cpudefend:ifName>%s</cpudefend:ifName>
  </cpudefend:secResetUrpf>
"""

SEC_URPF_QUERY = """
<filter type="subtree">
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secipurpfstats>
      <secipurpfstat>
        <secSlotId>%s</secSlotId>
        <secProtoFamily>%s</secProtoFamily>
        <secDiscardPkts/>
      </secipurpfstat>
    </secipurpfstats>
  </cpudefend>
</filter>
"""

SEC_URPF_RESET = """
  <cpudefend:secresetipurpf xmlns:cpudefend="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
      <cpudefend:secSlotId>%s</cpudefend:secSlotId>
      <cpudefend:secProtoFamily>%s</cpudefend:secProtoFamily>
  </cpudefend:secresetipurpf>
"""
SEC_URPF_CFGATN = """
<config>
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <ifName>%s</ifName>
        <secProtoFamily>%s</secProtoFamily>
        <secUrpfLoose>%s</secUrpfLoose>
        <secUrfpDefault>%s</secUrfpDefault>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</config>
"""
SEC_URPF_MERGEATN = """
<config>
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <ifName>%s</ifName>
        <secProtoFamily>%s</secProtoFamily>
        <secUrpfLoose>%s</secUrpfLoose>
        <secUrfpDefault>%s</secUrfpDefault>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</config>
"""

SEC_URPF_CFGGETATN = """
<filter type="subtree">
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf>
        <ifName/>
        <secProtoFamily/>
        <secUrpfLoose/>
        <secUrfpDefault/>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</filter>
"""
SEC_URPF_CFGGETFILATN = """
<filter type="subtree">
  <cpudefend xmlns="http://www.huawei.com/netconf/vrp/huawei-cpudefend">
    <secintfurpfs>
      <secintfurpf>
        <ifName>%s</ifName>
        <secProtoFamily>%s</secProtoFamily>
        <secUrpfLoose/>
        <secUrfpDefault/>
      </secintfurpf>
    </secintfurpfs>
  </cpudefend>
</filter>
"""


class SecUrpf(object):
    """
     Manages SecUrpf resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()
        self.ifName = self.module.params['ifName']
        self.secProtoFamily = self.module.params['secProtoFamily']
        self.secUrpfLoose = self.module.params['secUrpfLoose']
        self.secUrfpDefault = self.module.params['secUrfpDefault']
        self.secUrpfStatisticsEn = self.module.params['secUrpfStatisticsEn']
        self.ifName = self.module.params['ifName']
        self.secV4DiscardPkts = self.module.params['secV4DiscardPkts']
        self.secV6DiscardPkts = self.module.params['secV6DiscardPkts']
        self.secSlotId = self.module.params['secSlotId']
        self.secDiscardPkts = self.module.params['secDiscardPkts']
        self.operation = self.module.params['operation']
        self.changed = False
        self.existing = dict()
        self.proposed = dict()
        self.results = dict()
        self.urpfcfg_exist = False
        self.urpfcfg_attr_exist = None
        # self.results["start_stat"] = []
        self.results["existing"] = []
        # self.results["end_stat"] = []
        self.results["changed"] = False

    def init_module(self):
        """
        init ansilbe AnsibleModule.
        """
        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        product_name = self.get_product_name()
        if (product_name == 'ATN 910B') or (product_name == 'ATN 950B') or (product_name == 'ATN 980B') or (product_name == 'ATN 910C')\
                or (product_name == 'ATN 950C') or (product_name == 'ATN NE05E') or (product_name == 'ATN NE08E'):
            if self.operation == 'get':
                if not self.secUrpfLoose and not self.secUrfpDefault:
                    self.secUrpfLoose = ''
                    self.secUrfpDefault = ''
                else:
                    self.module.fail_json(
                        msg='Error:This operation is not supported.')
        else:
            if self.operation == 'get':
                if not self.secUrpfLoose and not self.secUrfpDefault and not self.secUrpfStatisticsEn:
                    self.secUrpfLoose = ''
                    self.secUrfpDefault = ''
                    self.secUrpfStatisticsEn = ''
                else:
                    self.module.fail_json(
                        msg='Error:This operation is not supported.')
        if self.operation == 'create' or self.operation == 'merge' or self.operation == 'delete':
            if not self.ifName or not self.secProtoFamily:
                self.module.fail_json(
                    msg='Error:Please input the necessary element include ifName/secProtoFamily.')
        # check the length of ifName
        if self.ifName:
            if len(self.ifName) > 32:
                self.module.fail_json(
                    msg='Error: The length of the interface name is not in the range from 1 to 32.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def transformatn(self, ifName, secProtoFamily):
        attr_input_ifName = ifName
        if not self.secProtoFamily:
            secProtoFamily = ''
        conf_str = None
        conf_str = SEC_URPF_CFGGETFILATN % (ifName, secProtoFamily)
        xml_str = get_nc_config(self.module, conf_str)
        re_find = re.findall(r'.*<ifName>(.*)</ifName>.*\s*', xml_str)
        if re_find:
            attr_input_ifName = re_find[0]
        return attr_input_ifName

    def transform(self, ifName, secProtoFamily):
        attr_input_ifName = ifName
        if not self.secProtoFamily:
            secProtoFamily = ''
        conf_str = None
        conf_str = SEC_URPF_CFGGETFIL % (ifName, secProtoFamily)
        xml_str = get_nc_config(self.module, conf_str)
        re_find = re.findall(r'.*<ifName>(.*)</ifName>.*\s*', xml_str)
        if re_find:
            attr_input_ifName = re_find[0]
        return attr_input_ifName

    def create_urpf(self, ifName, secProtoFamily,
                    secUrpfLoose, secUrfpDefault,
                    secUrpfStatisticsEn):
        if not self.secUrpfLoose:
            secUrpfLoose = 'strict'
        if not self.secUrfpDefault:
            secUrfpDefault = 'disallow'
        if not self.secUrpfStatisticsEn:
            secUrpfStatisticsEn = 'disable'
        conf_str = None
        conf_str = SEC_URPF_CFG % (ifName, secProtoFamily,
                                   secUrpfLoose, secUrfpDefault,
                                   secUrpfStatisticsEn)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_URPF")
        self.changed = True

    def create_urpfatn(self, ifName, secProtoFamily,
                       secUrpfLoose, secUrfpDefault):
        if not self.secUrpfLoose:
            secUrpfLoose = 'strict'
        if not self.secUrfpDefault:
            secUrfpDefault = 'allow'
        conf_str = None
        conf_str = SEC_URPF_CFGATN % (ifName, secProtoFamily,
                                      secUrpfLoose, secUrfpDefault)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_URPF")
        self.changed = True

    def merge_urpf(self, ifName, secProtoFamily,
                   secUrpfLoose, secUrfpDefault,
                   secUrpfStatisticsEn):
        attr_get = dict()
        attr_get = self.get_urpf(ifName, secProtoFamily)
        if attr_get:
            conf_str = None
            attr_get = dict()
            conf_str = SEC_URPF_CFGGETFIL % (ifName, secProtoFamily)
            xml_str = get_nc_config(self.module, conf_str)
            re_find = re.findall(r'.*<secUrpfLoose>(.*)</secUrpfLoose>.*\s*',
                                 xml_str)
            if re_find:
                attr_get['secUrpfLoose'] = re_find[0]
            re_find = re.findall(r'.*<secUrfpDefault>(.*)</secUrfpDefault>.*\s*',
                                 xml_str)
            if re_find:
                attr_get['secUrfpDefault'] = re_find[0]
            re_find = re.findall(
                r'.*<secUrpfStatisticsEn>(.*)</secUrpfStatisticsEn>.*\s*', xml_str)
            if re_find:
                attr_get['secUrpfStatisticsEn'] = re_find[0]
            if not self.secUrpfLoose:
                secUrpfLoose = attr_get['secUrpfLoose']
            if not self.secUrfpDefault:
                secUrfpDefault = attr_get['secUrfpDefault']
            if not self.secUrpfStatisticsEn:
                secUrpfStatisticsEn = attr_get['secUrpfStatisticsEn']
            conf_str = None
            conf_str = SEC_URPF_MERGE % (ifName, secProtoFamily,
                                         secUrpfLoose, secUrfpDefault,
                                         secUrpfStatisticsEn)
            recv_xml = set_nc_config(self.module, conf_str)
            self.check_response(recv_xml, "MEG_URPF")
            self.changed = False
        else:
            if not self.secUrpfLoose:
                secUrpfLoose = 'strict'
            if not self.secUrfpDefault:
                secUrfpDefault = 'disallow'
            if not self.secUrpfStatisticsEn:
                secUrpfStatisticsEn = 'disable'
            conf_str = None
            conf_str = SEC_URPF_MERGE % (ifName, secProtoFamily,
                                         secUrpfLoose, secUrfpDefault,
                                         secUrpfStatisticsEn)
            recv_xml = set_nc_config(self.module, conf_str)
            self.check_response(recv_xml, "MEG_URPF")
            self.changed = True

    def merge_urpfatn(self, ifName, secProtoFamily,
                      secUrpfLoose, secUrfpDefault):
        attr_get = dict()
        attr_get = self.get_urpfatn(ifName, secProtoFamily)
        if attr_get:
            conf_str = None
            attr_get = dict()
            conf_str = SEC_URPF_CFGGETFILATN % (ifName, secProtoFamily)
            xml_str = get_nc_config(self.module, conf_str)
            re_find = re.findall(r'.*<secUrpfLoose>(.*)</secUrpfLoose>.*\s*',
                                 xml_str)
            if re_find:
                attr_get['secUrpfLoose'] = re_find[0]
            re_find = re.findall(
                r'.*<secUrfpDefault>(.*)</secUrfpDefault>.*\s*', xml_str)
            if re_find:
                attr_get['secUrfpDefault'] = re_find[0]
            if not self.secUrpfLoose:
                secUrpfLoose = attr_get['secUrpfLoose']
            if not self.secUrfpDefault:
                secUrfpDefault = attr_get['secUrfpDefault']
            conf_str = None
            conf_str = SEC_URPF_MERGEATN % (ifName, secProtoFamily,
                                            secUrpfLoose, secUrfpDefault)
            recv_xml = set_nc_config(self.module, conf_str)
            self.check_response(recv_xml, "MEG_URPF")
            self.changed = False
        else:
            if not self.secUrpfLoose:
                secUrpfLoose = 'strict'
            if not self.secUrfpDefault:
                secUrfpDefault = 'allow'
            conf_str = None
            conf_str = SEC_URPF_MERGEATN % (ifName, secProtoFamily,
                                            secUrpfLoose, secUrfpDefault)
            recv_xml = set_nc_config(self.module, conf_str)
            self.check_response(recv_xml, "MEG_URPF")
            self.changed = True

    def get_data(self, ifName, secProtoFamily, xml_str):
        attr_get = dict()
        attr_input = dict()
        attr_output = dict()
        re_find = re.findall(r'.*<ifName>(.*)</ifName>.*\s*', xml_str)
        if re_find:
            attr_get['ifName'] = re_find[0]
        re_find = re.findall(r'.*<secProtoFamily>(.*)</secProtoFamily>.*\s*',
                             xml_str)
        if re_find:
            attr_get['secProtoFamily'] = re_find[0]
        re_find = re.findall(r'.*<secUrpfLoose>(.*)</secUrpfLoose>.*\s*',
                             xml_str)
        if re_find:
            attr_get['secUrpfLoose'] = re_find[0]
        re_find = re.findall(r'.*<secUrfpDefault>(.*)</secUrfpDefault>.*\s*',
                             xml_str)
        if re_find:
            attr_get['secUrfpDefault'] = re_find[0]
        re_find = re.findall(
            r'.*<secUrpfStatisticsEn>(.*)</secUrpfStatisticsEn>.*\s*',
            xml_str)
        if re_find:
            attr_get['secUrpfStatisticsEn'] = re_find[0]
        if not self.ifName and not self.secProtoFamily:
            attr_output = attr_get
        elif not self.ifName:
            attr_input['secProtoFamily'] = secProtoFamily
            if attr_get['secProtoFamily'] == attr_input['secProtoFamily']:
                attr_output = attr_get
        elif not self.secProtoFamily:
            attr_input['ifName'] = ifName
            if attr_get['ifName'] == attr_input['ifName']:
                attr_output = attr_get
        else:
            attr_input['ifName'] = ifName
            attr_input['secProtoFamily'] = secProtoFamily
            if attr_get['ifName'] == attr_input['ifName'] and attr_get['secProtoFamily'] == attr_input['secProtoFamily']:
                attr_output = attr_get
        return attr_output

    def get_dataatn(self, ifName, secProtoFamily, xml_str):
        attr_get = dict()
        attr_input = dict()
        attr_output = dict()
        re_find = re.findall(r'.*<ifName>(.*)</ifName>.*\s*', xml_str)
        re_find = re.findall(r'.*<ifName>(.*)</ifName>.*\s*', xml_str)
        if re_find:
            attr_get['ifName'] = re_find[0]
        re_find = re.findall(r'.*<secProtoFamily>(.*)</secProtoFamily>.*\s*',
                             xml_str)
        if re_find:
            attr_get['secProtoFamily'] = re_find[0]
        re_find = re.findall(r'.*<secUrpfLoose>(.*)</secUrpfLoose>.*\s*',
                             xml_str)
        if re_find:
            attr_get['secUrpfLoose'] = re_find[0]
        re_find = re.findall(r'.*<secUrfpDefault>(.*)</secUrfpDefault>.*\s*',
                             xml_str)
        if re_find:
            attr_get['secUrfpDefault'] = re_find[0]

        if not self.ifName and not self.secProtoFamily:
            attr_output = attr_get
        elif not self.ifName:
            attr_input['secProtoFamily'] = secProtoFamily
            if attr_get['secProtoFamily'] == attr_input['secProtoFamily']:
                attr_output = attr_get
        elif not self.secProtoFamily:
            attr_input['ifName'] = ifName
            if attr_get['ifName'] == attr_input['ifName']:
                attr_output = attr_get
        else:
            attr_input['ifName'] = ifName
            attr_input['secProtoFamily'] = secProtoFamily
            if attr_get['ifName'] == attr_input['ifName'] and attr_get['secProtoFamily'] == attr_input['secProtoFamily']:
                attr_output = attr_get
        return attr_output

    def get_urpf(self, ifName, secProtoFamily):
        conf_str = None
        conf_str = SEC_URPF_CFGGET
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        attr = dict()
        attr_input = dict()
        attrfil = dict()
        if "<data/>" in xml_str:
            return attr
        else:
            attr_total = list()
            re_find_ifName = re.findall(r'.*<ifName>(.*)</ifName>.*\s*',
                                        xml_str)
            re_find_secProtoFamily = re.findall(
                r'.*<secProtoFamily>(.*)</secProtoFamily>.*\s*', xml_str)
            re_find = re.split('</secintfurpf>', xml_str)
            if not self.ifName:
                for i in range(len(re_find_secProtoFamily)):
                    attr = self.get_data(ifName, secProtoFamily, re_find[i])
                    if attr == attrfil:
                        attr = dict()
                    else:
                        attr_total.append(attr)
                        attr = dict()
                return attr_total
            else:
                attr_input['ifName'] = self.transform(ifName, secProtoFamily)
                for i in range(len(re_find_secProtoFamily)):
                    attr = self.get_data(attr_input['ifName'], secProtoFamily,
                                         re_find[i])
                    if attr == attrfil:
                        attr = dict()
                    else:
                        attr_total.append(attr)
                        attr = dict()
                return attr_total

    def get_urpfatn(self, ifName, secProtoFamily):
        conf_str = None
        conf_str = SEC_URPF_CFGGETATN
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        attr = dict()
        attr_input = dict()
        attrfil = dict()
        if "<data/>" in xml_str:
            return attr
        else:
            attr_total = list()
            re_find_ifName = re.findall(r'.*<ifName>(.*)</ifName>.*\s*',
                                        xml_str)
            re_find_secProtoFamily = re.findall(
                r'.*<secProtoFamily>(.*)</secProtoFamily>.*\s*', xml_str)
            re_find = re.split('</secintfurpf>', xml_str)
            if not self.ifName:
                for i in range(len(re_find_secProtoFamily)):
                    attr = self.get_dataatn(ifName, secProtoFamily, re_find[i])
                    if attr == attrfil:
                        attr = dict()
                    else:
                        attr_total.append(attr)
                        attr = dict()
                return attr_total
            else:
                attr_input['ifName'] = self.transformatn(ifName,
                                                         secProtoFamily)
                for i in range(len(re_find_secProtoFamily)):
                    attr = self.get_dataatn(attr_input['ifName'],
                                            secProtoFamily, re_find[i])
                    if attr == attrfil:
                        attr = dict()
                    else:
                        attr_total.append(attr)
                        attr = dict()
                return attr_total

    def undo_urpf(self, ifName, secProtoFamily):
        conf_str = None
        conf_str = SEC_URPF_CFGUNDO % (ifName, secProtoFamily)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "DEL_URPF")
        self.changed = True

    def query_urpf(self, secSlotId, secProtoFamily):
        if not self.secSlotId:
            secSlotId = ''
        if not self.secProtoFamily:
            secProtoFamily = ''
        conf_str = None
        conf_str = SEC_URPF_QUERY % (secSlotId, secProtoFamily)
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        attr = collections.OrderedDict()
        output_msg_list = list()
        output_msg = list()
        if "<data/>" in xml_str:
            return output_msg
        else:
            output_msg.append('secSlotId %s' % secSlotId)
            output_msg.append('secProtoFamily %s' % secProtoFamily)
            re_find = re.findall(r'.*<secSlotId>(.*)</secSlotId>.*\s*'
                                 r'<secProtoFamily>(.*)</secProtoFamily>.*\s*'
                                 r'<secDiscardPkts>(.*)</secDiscardPkts>.*\s*',
                                 xml_str)
            print('re_find', re_find)
            if re_find:
                for i in range(len(re_find)):
                    attr = collections.OrderedDict()
                    attr['secSlotId'] = secSlotId
                    attr['secProtoFamily'] = secProtoFamily
                    attr['secSlotId'] = re_find[i][0]
                    attr['secProtoFamily'] = re_find[i][1]
                    attr['secDiscardPkts'] = re_find[i][2]
                    output_msg_list.append(attr)
            else:
                output_msg_list = {}
        return output_msg_list

    def reset_urpf(self, secSlotId, secProtoFamily):
        product_name = self.get_product_name()
        if not self.secProtoFamily:
            self.module.fail_json(
                msg='Error:Please input the necessary element include secProtoFamily.')
        if (product_name == 'ATN 910B') or (product_name == 'ATN 950B') or (product_name == 'ATN 980B') or (product_name == 'ATN 910C')\
                or (product_name == 'ATN 950C') or (product_name == 'ATN NE05E') or (product_name == 'ATN NE08E'):
            conf_str = None
        else:
            if not self.secSlotId:
                secSlotId = ''
            conf_str = None
        conf_str = SEC_URPF_RESET % (secSlotId, secProtoFamily)
        recv_xml = execute_nc_action_yang(self.module, conf_str)
        self.check_response(recv_xml, "RST_URPF")

    def query_inturpf(self, ifName):
        conf_str = None
        conf_str = SEC_INTURPF_QUERY
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        attr = collections.OrderedDict()
        attr_input = dict()
        attr_get = dict()
        output_msg_list = list()
        output_msg = list()
        if "<data/>" in xml_str:
            return output_msg
        else:
            output_msg.append('ifName %s' % ifName)
            re_find = re.findall(r'.*<ifName>(.*)</ifName>.*\s*'
                                 r'<secV4DiscardPkts>(.*)</secV4DiscardPkts>.*\s*'
                                 r'<secV6DiscardPkts>(.*)</secV6DiscardPkts>.*\s*',
                                 xml_str)

            print('re_find', re_find)
            if re_find:
                attr_input['ifName'] = self.transform(ifName, '')
                for i in range(len(re_find)):
                    attr = collections.OrderedDict()
                    attr_get['ifName'] = re_find[i][0]
                    if attr_get['ifName'] == attr_input['ifName']:
                        attr['ifName'] = re_find[i][0]
                        attr['secV4DiscardPkts'] = re_find[i][1]
                        attr['secV6DiscardPkts'] = re_find[i][2]
                        output_msg_list.append(attr)
            else:
                output_msg_list = {}
        return output_msg_list

    def reset_inturpf(self, ifName):
        conf_str = None
        conf_str = SEC_INTURPF_RESET % (ifName)
        recv_xml = execute_nc_action_yang(self.module, conf_str)
        self.check_response(recv_xml, "RST_INTURPF")

    def get_product_name(self):
        conf_str = None
        conf_str = PRODUCT_SYSTERM
        xml_str = get_nc_config(self.module, conf_str)
        attr = dict()
        if "<data/>" in xml_str:
            return attr
        else:
            attr_total = list()
            re_find_product_name = re.findall(
                r'.*<productName>(.*)</productName>.*\s*', xml_str)
        return re_find_product_name[0]

    def get_proposed(self):
        if self.ifName:
            self.proposed["ifName"] = self.ifName
        if self.secV4DiscardPkts:
            self.proposed["secV4DiscardPkts"] = self.secV4DiscardPkts
        if self.secV6DiscardPkts:
            self.proposed["secV6DiscardPkts"] = self.secV6DiscardPkts
        if self.secSlotId:
            self.proposed["secSlotId"] = self.secSlotId
        if self.secDiscardPkts:
            self.proposed["secDiscardPkts"] = self.secDiscardPkts
        if self.operation:
            self.proposed["operation"] = self.operation
        if self.secProtoFamily:
            self.proposed["secProtoFamily"] = self.secProtoFamily
        if self.secUrpfLoose:
            self.proposed["secUrpfLoose"] = self.secUrpfLoose
        if self.secUrfpDefault:
            self.proposed["secUrfpDefault"] = self.secUrfpDefault
        if self.secUrpfStatisticsEn:
            self.proposed["secUrpfStatisticsEn"] = self.secUrpfStatisticsEn

    def work(self):
        """
        worker.
        """
        # check param
        self.check_params()
        self.get_proposed()
        product_name = self.get_product_name()
        if (product_name == 'ATN 910B') or (product_name == 'ATN 950B') or (product_name == 'ATN 980B') or (product_name == 'ATN 910C')\
                or (product_name == 'ATN 950C') or (product_name == 'ATN NE05E') or (product_name == 'ATN NE08E'):
            # urpfcfg_attr_start_stat = self.get_urpfatn(self.ifName,self.secProtoFamily)
            # if urpfcfg_attr_start_stat:
            # self.results["start_stat"] = urpfcfg_attr_start_stat
            if self.operation == 'create':
                self.create_urpfatn(self.ifName, self.secProtoFamily,
                                    self.secUrpfLoose, self.secUrfpDefault)
                self.results['changed'] = self.changed
            elif self.operation == 'merge':
                self.merge_urpfatn(self.ifName, self.secProtoFamily,
                                   self.secUrpfLoose, self.secUrfpDefault)
                self.results['changed'] = self.changed
            elif self.operation == 'delete':
                self.undo_urpf(self.ifName, self.secProtoFamily)
                self.results['changed'] = self.changed

            if self.operation == 'create' or self.operation == 'merge'or self.operation == 'get' or self.operation == 'delete':
                urpfcfg_attr_exist = self.get_urpfatn(self.ifName,
                                                      self.secProtoFamily)
                if urpfcfg_attr_exist:
                    self.uprfcfg_exist = True
                self.results["existing"].append(urpfcfg_attr_exist)

            if self.operation == 'query':
                urpfcfg_attr_exist = self.query_urpf(self.secSlotId,
                                                     self.secProtoFamily)
                if urpfcfg_attr_exist:
                    self.uprfcfg_exist = True
                self.results["existing"].append(urpfcfg_attr_exist)
            elif self.operation == 'reset':
                self.reset_urpf(self.secSlotId, self.secProtoFamily)
                self.results['changed'] = self.changed
                # urpfcfg_attr_end_stat = self.get_urpfatn(self.ifName,self.secProtoFamily)
                # if urpfcfg_attr_end_stat:
                # self.results["end_stat"] = urpfcfg_attr_end_stat
        else:
            # urpfcfg_attr_start_stat = self.get_urpf(self.ifName,self.secProtoFamily)
            # if urpfcfg_attr_start_stat:
                # self.results["start_stat"] = urpfcfg_attr_start_stat
            if self.operation == 'create':
                self.create_urpf(self.ifName, self.secProtoFamily,
                                 self.secUrpfLoose, self.secUrfpDefault,
                                 self.secUrpfStatisticsEn)
                self.results['changed'] = self.changed
            elif self.operation == 'merge':
                self.merge_urpf(self.ifName,
                                self.secProtoFamily, self.secUrpfLoose,
                                self.secUrfpDefault, self.secUrpfStatisticsEn)
                self.results['changed'] = self.changed
            elif self.operation == 'delete':
                self.undo_urpf(self.ifName, self.secProtoFamily)
                self.results['changed'] = self.changed

            if self.operation == 'create' or self.operation == 'merge' or self.operation == 'get' or self.operation == 'delete':
                urpfcfg_attr_exist = self.get_urpf(self.ifName,
                                                   self.secProtoFamily)
                if urpfcfg_attr_exist:
                    self.uprfcfg_exist = True
                self.results["existing"].append(urpfcfg_attr_exist)

            if self.operation == 'query':
                if not self.ifName:
                    urpfcfg_attr_exist = self.query_urpf(self.secSlotId,
                                                         self.secProtoFamily)
                else:
                    urpfcfg_attr_exist = self.query_inturpf(self.ifName)
                if urpfcfg_attr_exist:
                    self.uprfcfg_exist = True
                self.results["existing"].append(urpfcfg_attr_exist)
            elif self.operation == 'reset':
                if not self.ifName:
                    self.reset_urpf(self.secSlotId, self.secProtoFamily)
                else:
                    self.reset_inturpf(self.ifName)
                self.results['changed'] = self.changed
                # urpfcfg_attr_end_stat = self.get_urpf(self.ifName,self.secProtoFamily)
                # if urpfcfg_attr_end_stat:
                # self.results["end_stat"] = urpfcfg_attr_end_stat

        if self.operation != 'get' and self.operation != 'query':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """
    argument_spec = dict(
        ifName=dict(required=False, type='str'),
        secProtoFamily=dict(choices=['ipv4', 'ipv6'],
                            required=False),
        secUrpfLoose=dict(choices=['strict', 'loose'],
                          required=False),
        secUrfpDefault=dict(choices=['disallow', 'allow'],
                            required=False),
        secUrpfStatisticsEn=dict(choices=['enable', 'disable'],
                                 required=False),
        secV4DiscardPkts=dict(required=False, type='str'),
        secV6DiscardPkts=dict(required=False, type='str'),
        secSlotId=dict(required=False, type='str'),
        secDiscardPkts=dict(required=False, type='str'),
        operation=dict(required=False, choices=['create', 'merge', 'get',
                                                'delete', 'query', 'reset'], default='merge'),
    )
    argument_spec.update(ne_argument_spec)
    urpfcfg = SecUrpf(argument_spec)
    urpfcfg.work()


if __name__ == '__main__':
    main()
