
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_isis_issite_issitemt
version_added: "2.6"
short_description: Manages configuration of an ISIS instance on HUAWEI netengine switches.
description:
    - Manages configuration of an ISIS instance on HUAWEI netengine switches.
author: Xuenjian (@netengine-Ansible)
options:
    instanceId:
        description:
            - Set the process ID. If the process ID does not exist, you can create a process. Otherwise, the system fails to create a process.
              The value is an integer ranging from 1 to 4294967295.
        required: true
'''

EXAMPLES = '''
- name: isis module test
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
  - name: Configure isis
    ne_isis_isSiteMT:
      instanceId: 1

      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"instanceId": "1", }
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    updates:
    description: commands sent to the device
    returned: always
    type: list
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

# import pydevd

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
# ISIS 模块私有宏定义
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_GET_ISISCOMM_HEAD
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_GET_ISISCOMM_TAIL
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_PROCESS_ISIS_HEAD
from ansible.modules.network.ne.isis.ne_isis_def import NE_COMMON_XML_PROCESS_ISIS_TAIL

# ISIS 模块私有接口公共函数
from ansible.modules.network.ne.isis.ne_isis_def import constr_leaf_value
from ansible.modules.network.ne.isis.ne_isis_def import constr_leaf_novalue
from ansible.modules.network.ne.isis.ne_isis_def import constr_container_head
from ansible.modules.network.ne.isis.ne_isis_def import constr_container_tail
from ansible.modules.network.ne.isis.ne_isis_def import constr_container_process_head
from ansible.modules.network.ne.isis.ne_isis_def import constr_container_process_tail


class ISIS_isSiteMT(object):
    """Manages configuration of an ISIS interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.instanceid = self.module.params['instanceid']
        self.addressfamily = self.module.params['addressfamily']
        self.mtid = self.module.params['mtid']
        self.basetopotype = self.module.params['basetopotype']
        self.topologyname = self.module.params['topologyname']
        self.allcircbfdon = self.module.params['allcircbfdon']
        self.frrbindingflag = self.module.params['frrbindingflag']
        self.bfdminrx = self.module.params['bfdminrx']
        self.bfdmintx = self.module.params['bfdmintx']
        self.bfdmultnum = self.module.params['bfdmultnum']
        self.tosexpvalue = self.module.params['tosexpvalue']
        self.frrenable = self.module.params['frrenable']
        self.policytype = self.module.params['policytype']
        self.routepolicyname = self.module.params['routepolicyname']
        # self.routefilternameentity = self.module.params['routefilternameentity']
        self.lfalevel1enable = self.module.params['lfalevel1enable']
        self.lfalevel2enable = self.module.params['lfalevel2enable']
        self.state = self.module.params['state']
        # isis info
        self.isis_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """

        # required_one_of    = [["instanceId", "ifName", "ipv4Enable", "ipv6Enable", "typeP2pEnable"]]
        # required_one_of=required_one_of,
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # 其他参数待同步增加补充
        # check instanceId
        # self.module.fail_json(msg='Error: The bfdMinRx is not in the range from 50 to 1000.')
        # if self.instanceId:
        #    if not self.instanceId.isdigit():
        #        self.module.fail_json(
        #            msg='Error: Instance Id is not digit.')
        #    if int(self.instanceId) <= 1 or int(self.instanceId) > 4294967295:
        #        self.module.fail_json(
        #            msg='Error: Instance Id is not in the range from 1 to 4294967295.')
        #
        # if self.mtId and self.mtId > 4095:
        #    self.module.fail_json(msg='Error: The mtId is not in the range from 1 to 4095.')
        #
        # if self.topologyName and (len(self.topologyName) > 40):
        #    self.module.fail_json(msg='Error: The len of topologyName is out of [1..40].')
        #
        # if self.routePolicyName and (len(self.routePolicyName) > 31):
        #    self.module.fail_json(msg='Error: The len of routePolicyName is out of [1..31].')
        #
        # if self.bfdMinRx and (self.bfdMinRx > 1000 or self.bfdMinRx < 50):
        #      if self.bfdMinTx and (self.bfdMinTx > 1000 or self.bfdMinTx < 50):
        #    self.module.fail_json(msg='Error: The bfdMinTx is not in the range from 50 to 1000.')
        # if self.bfdMultNum and (self.bfdMultNum > 1000 or self.bfdMultNum < 50):
        #    self.module.fail_json(msg='Error: The bfdMultNum is not in the range from 3 to 50.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_isis_dict(self):
        """ get one isis attributes dict."""

        isis_info = dict()
        # Head info
        conf_str = NE_COMMON_XML_GET_ISISCOMM_HEAD
        conf_str = constr_leaf_value(conf_str, "instanceId", self.instanceid)
        conf_str = constr_leaf_novalue(conf_str, "baseTopoType")
        conf_str = constr_container_head(conf_str, "isSiteMTs")
        conf_str = constr_container_head(conf_str, "isSiteMT")
        # Body info
        conf_str = constr_leaf_value(conf_str, "addressFamily", self.addressfamily)
        conf_str = constr_leaf_value(conf_str, "mtId", self.mtid)
        conf_str = constr_leaf_novalue(conf_str, "topologyName")
        conf_str = constr_leaf_novalue(conf_str, "allCircBfdOn")
        conf_str = constr_leaf_novalue(conf_str, "frrBindingFlag")
        conf_str = constr_leaf_novalue(conf_str, "bfdMinRx")
        conf_str = constr_leaf_novalue(conf_str, "bfdMinTx")
        conf_str = constr_leaf_novalue(conf_str, "bfdMultNum")
        conf_str = constr_leaf_novalue(conf_str, "tosExpValue")

        conf_str = constr_container_head(conf_str, "isFrr")
        conf_str = constr_leaf_novalue(conf_str, "frrEnable")
        conf_str = constr_leaf_novalue(conf_str, "policyType")
        conf_str = constr_leaf_novalue(conf_str, "routePolicyName")
        # conf_str = constr_leaf_novalue(conf_str, "routeFilterNameEntity")
        conf_str = constr_leaf_novalue(conf_str, "lfaLevel1Enable")
        conf_str = constr_leaf_novalue(conf_str, "lfaLevel2Enable")

        # Tail info
        conf_str = constr_container_tail(conf_str, "isFrr")
        conf_str = constr_container_tail(conf_str, "isSiteMT")
        conf_str = constr_container_tail(conf_str, "isSiteMTs")
        conf_str += NE_COMMON_XML_GET_ISISCOMM_TAIL

        # No record return , 没有找到记录直接返回
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return isis_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-isiscomm"', "")
        # get process base info
        root = ElementTree.fromstring(xml_str)
        iSsite = root.find("isiscomm/isSites/isSite")
        if len(iSsite) != 0:
            for site in iSsite:
                if site.tag in ["instanceId", "baseTopoType"]:
                    isis_info[site.tag.lower()] = site.text

        # isSiteMTs 数据， isSiteMTs 是多实例记录
        isis_info["issitemts"] = list()
        isSiteMTs = root.findall("data/isiscomm/isSites/isSite/isSiteMTs/isSiteMT")
        if len(isSiteMTs) != 0:
            for isSiteMT in isSiteMTs:
                isSiteMT_dict = dict()
                for ele in isSiteMT:
                    if ele.tag in ["addressFamily", "mtId", "topologyName", "allCircBfdOn",
                                   "frrBindingFlag", "tosExpValue",
                                   "bfdMultNum", "bfdMinTx", "bfdMinRx"
                                   ]:
                        isSiteMT_dict[ele.tag.lower()] = ele.text
                    if ele.tag == "isFrr":
                        # get isFrr info
                        isSiteMT_dict["isfrr"] = list()
                        isFrr = root.findall("data/isiscomm/isSites/isSite/isSiteMTs/isSiteMT/isFrr")
                        if len(isFrr) != 0:
                            for isFrr_ele in isFrr:
                                isFrr_dict = dict()
                                for ele in isFrr_ele:
                                    if ele.tag in ["frrEnable", "policyType", "routePolicyName",
                                                   "routeFilterNameEntity", "lfaLevel1Enable", "lfaLevel2Enable"]:
                                        isFrr_dict[ele.tag.lower()] = ele.text
                                isSiteMT_dict["isfrr"].append(isFrr_dict)

                isis_info["issitemts"].append(isSiteMT_dict)

        return isis_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["instanceid"] = self.instanceid
        self.proposed['addressfamily'] = self.addressfamily
        self.proposed['mtid'] = self.mtid

        if self.basetopotype is not None:
            self.proposed['basetopotype'] = self.basetopotype
        if self.topologyname is not None:
            self.proposed['topologyname'] = self.topologyname
        if self.allcircbfdon is not None:
            self.proposed['allcircbfdon'] = self.allcircbfdon
        if self.frrbindingflag is not None:
            self.proposed['frrbindingflag'] = self.frrbindingflag
        if self.bfdminrx is not None:
            self.proposed['bfdminrx'] = self.bfdminrx
        if self.bfdmintx is not None:
            self.proposed['bfdmintx'] = self.bfdmintx
        if self.bfdmultnum is not None:
            self.proposed['bfdmultnum'] = self.bfdmultnum
        if self.tosexpvalue is not None:
            self.proposed['tosexpvalue'] = self.tosexpvalue
        if self.frrenable is not None:
            self.proposed['frrenable'] = self.frrenable
        if self.policytype is not None:
            self.proposed['policytype'] = self.policytype
        if self.routepolicyname is not None:
            self.proposed['routepolicyname'] = self.routepolicyname
        # if self.routefilternameentity is not none:
        #    self.proposed['routefilternameentity'] = self.routefilternameentity
        if self.lfalevel1enable is not None:
            self.proposed['lfalevel1enable'] = self.lfalevel1enable
        if self.lfalevel2enable is not None:
            self.proposed['lfalevel2enable'] = self.lfalevel2enable

        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if not self.isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        if self.isis_info["basetopotype"]:
            self.existing["basetopotype"] = self.isis_info["basetopotype"]
        self.existing["issitemts"] = self.isis_info["issitemts"]

    def get_end_state(self):
        """get end state info"""

        isis_info = self.get_isis_dict()
        if not isis_info:
            return

        self.end_state["instanceid"] = isis_info["instanceid"]
        self.end_state["basetopotype"] = isis_info["basetopotype"]
        self.end_state["issitemts"] = isis_info["issitemts"]

    def comm_process(self, operation, operation_Desc):
        """Comm  isis process"""

        # Process schema or yang,  CE_XPATH_ISISCOMM_YANG_OR_SCHEMA
        # Head process
        if NE_COMMON_XML_OPERATION_CREATE == operation:
            xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_MERGE
        else:
            xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % operation

        # Body process
        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_leaf_value(xml_str, "baseTopoType", self.basetopotype)

        xml_str = constr_container_process_head(xml_str, "isSiteMT", operation)
        xml_str = constr_leaf_value(xml_str, "addressFamily", self.addressfamily)
        xml_str = constr_leaf_value(xml_str, "mtId", self.mtid)
        xml_str = constr_leaf_value(xml_str, "topologyName", self.topologyname)
        xml_str = constr_leaf_value(xml_str, "allCircBfdOn", self.allcircbfdon)
        xml_str = constr_leaf_value(xml_str, "frrBindingFlag", self.frrbindingflag)
        xml_str = constr_leaf_value(xml_str, "bfdMinRx", self.bfdminrx)
        xml_str = constr_leaf_value(xml_str, "bfdMinTx", self.bfdmintx)
        xml_str = constr_leaf_value(xml_str, "bfdMultNum", self.bfdmultnum)
        xml_str = constr_leaf_value(xml_str, "tosExpValue", self.tosexpvalue)

        xml_str = constr_container_head(xml_str, "isFrr")
        xml_str = constr_leaf_value(xml_str, "frrEnable", self.frrenable)
        xml_str = constr_leaf_value(xml_str, "policyType", self.policytype)
        xml_str = constr_leaf_value(xml_str, "routePolicyName", self.routepolicyname)
        # xml_str = constr_leaf_value(xml_str, "routeFilterNameEntity", self.routefilternameentity)
        xml_str = constr_leaf_value(xml_str, "lfaLevel1Enable", self.lfalevel1enable)
        xml_str = constr_leaf_value(xml_str, "lfaLevel2Enable", self.lfalevel2enable)
        xml_str = constr_container_tail(xml_str, "isFrr")

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "isSiteMT")
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, operation_Desc)

        # 更新CLI 命令行信息
        self.changed = True

    def create_process(self):
        """Create isis process"""
        self.comm_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """ Merge isis process """
        self.comm_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.isis_info = self.get_isis_dict()
        self.get_proposed()
        self.get_existing()

        # deal present or absent
        if self.state == "present":
            if not self.isis_info:
                # create isis process
                self.create_process()
            else:
                # merge isis process
                self.merge_process()
        elif self.state == "query":
            # 查询输出
            if not self.isis_info:
                self.module.fail_json(msg='Error: Isis instance does not exist')

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        # if self.changed:
        #    self.results['updates'] = self.updates_cmd
        # else:
        #    self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        instanceid=dict(required=True, type='str'),
        addressfamily=dict(required=True, choices=['afIpv4', 'afIpv6']),
        mtid=dict(required=True, type='int'),
        basetopotype=dict(required=False, default='invalid',
                          choices=['standard', 'compatible', 'ipv6', 'cmpt_ipv6spf', 'invalid']),
        topologyname=dict(required=False, type='str'),
        allcircbfdon=dict(required=False, choices=['true', 'false']),
        frrbindingflag=dict(required=False, choices=['true', 'false']),
        bfdminrx=dict(required=False, type='int'),
        bfdmintx=dict(required=False, type='int'),
        bfdmultnum=dict(required=False, type='int'),
        tosexpvalue=dict(required=False, type='int'),
        frrenable=dict(required=False, choices=['true', 'false']),
        policytype=dict(required=False, choices=['noType', 'routePolicy']),
        routepolicyname=dict(required=False, type='str'),
        # NE40e does not support
        # routefilternameentity= dict(required=False, type='str'),
        lfalevel1enable=dict(required=False, choices=['true', 'false']),
        lfalevel2enable=dict(required=False, choices=['true', 'false']),
        state=dict(required=False, default='present', choices=['present', 'query']))

    argument_spec.update(ne_argument_spec)
    module = ISIS_isSiteMT(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
