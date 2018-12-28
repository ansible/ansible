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
module: ne_isis_issite_isoverloadset
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
    ne_isis_issite_isoverloadset:
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


class ISIS_isOverloadSet(object):
    """Manages configuration of an ISIS interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.instanceid = self.module.params['instanceid']
        self.stdoverloadtype = self.module.params['stdoverloadtype']
        self.stdoverloadwaittype = self.module.params['stdoverloadwaittype']
        self.stdoverloadnbrsysid = self.module.params['stdoverloadnbrsysid']
        self.stdoverloadtimeout1 = self.module.params['stdoverloadtimeout1']
        self.stdoverloadtimeout2 = self.module.params['stdoverloadtimeout2']
        self.stdoverloadinterlevel = self.module.params['stdoverloadinterlevel']
        self.stdoverloadexternal = self.module.params['stdoverloadexternal']
        self.stdoverloadsendsabit = self.module.params['stdoverloadsendsabit']
        self.stdoverloadsabittime = self.module.params['stdoverloadsabittime']
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

        # required_one_of=required_one_of,
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def is_valid_stdOverloadNbrSysId(self, stdOverloadNbrSysId):
        """Check the  netEntiy is  valid"""

        # check isis stdOverloadNbrSysId 15
        # 设置邻居系统ID，会根据该系统ID指定的邻居的状态，配置系统保持过载标志位时长。
        # 格式是XXXX.XXXX.XXXX，“X”是16进制字符，不区分大小写。
        if len(stdOverloadNbrSysId) > 15:
            return False

        # 点分格式判断
        if stdOverloadNbrSysId.find('.') != -1:
            stdOverloadNbrSysId_list = stdOverloadNbrSysId.split('.')
            list_num = len(stdOverloadNbrSysId_list)

            # 点分格式个数 不等于3错误。
            if list_num == 3:
                return False

            # “X”是16进制字符, 检查是否是数字, 使用int 函数转换
            for each_ID in stdOverloadNbrSysId_list:
                try:
                    eachID = int(each_ID, 16)
                except ValueError:
                    return False

            # 正确返回True
            return True
        # 找不到 . 返回False
        return False

    def check_params(self):
        """Check all input params"""
        # 其他参数待同步增加补充
        # check instanceId
        # if self.instanceId:
        #    if not self.instanceId.isdigit():
        #        self.module.fail_json(
        #            msg='Error: Instance Id is not digit.')
        #    if int(self.instanceId) <= 1 or int(self.instanceId) > 4294967295:
        #        self.module.fail_json(
        #            msg='Error: Instance Id is not in the range from 1 to 4294967295.')
        #
        # if self.stdOverloadTimeout1:
        #    if int(self.stdOverloadTimeout1) < 5 or int(self.stdOverloadTimeout1) > 86400:
        #        self.module.fail_json(
        #            msg='Error: The stdOverloadTimeout1 not in the range from 5 to 86400.')
        # if self.stdOverloadTimeout2:
        #    if int(self.stdOverloadTimeout2) < 5 or int(self.stdOverloadTimeout2) > 86400:
        #        self.module.fail_json(
        #            msg='Error: The stdOverloadTimeout2 not in the range from 5 to 86400.')
        #
        # if self.stdOverloadSaBitTime:
        #    if int(self.stdOverloadSaBitTime) < 5 or int(self.stdOverloadSaBitTime) > 120:
        #        self.module.fail_json(
        #            msg='Error: The stdOverloadSaBitTime not in the range from 5 to 120.')
        #
        # if self.stdOverloadNbrSysId:
        #    if not(self.is_valid_stdOverloadNbrSysId(self.stdOverloadNbrSysId)):
        #        self.module.fail_json(
        #            msg='Error: The stdOverloadNbrSysId must be as format :XXXX.XXXX.XXXX. X is HEXadecimal')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_isis_dict(self):
        """ get one isis attributes dict."""

        isis_info = dict()
        # use schema xpath
        # CE_XPATH_ISISCOMM_YANG_OR_SCHEMA
        conf_str = NE_COMMON_XML_GET_ISISCOMM_HEAD
        conf_str = constr_leaf_value(conf_str, "instanceId", self.instanceid)
        conf_str = constr_container_head(conf_str, "isOverloadSet")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadType")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadWaitType")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadNbrSysId")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadTimeout1")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadTimeout2")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadInterlevel")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadExternal")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadSendSaBit")
        conf_str = constr_leaf_novalue(conf_str, "stdOverloadSaBitTime")
        conf_str = constr_container_tail(conf_str, "isOverloadSet")
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
                if site.tag in ["instanceId"]:
                    isis_info[site.tag.lower()] = site.text

        # isLspGenIntelliTimer 数据， isLspGenIntelliTimer 单实例记录
        isis_info["isoverloadset"] = list()
        isOverloadSet = root.findall(
            "data/isiscomm/isSites/isSite/isOverloadSet")
        if len(isOverloadSet) != 0:
            isOverloadSet_dict = dict()
            for ele in isOverloadSet:
                if ele.tag in ["stdOverloadType",
                               "stdOverloadWaitType",
                               "stdOverloadNbrSysId",
                               "stdOverloadTimeout1",
                               "stdOverloadTimeout2",
                               "stdOverloadInterlevel",
                               "stdOverloadExternal",
                               "stdOverloadSendSaBit",
                               "stdOverloadSaBitTime"]:
                    isOverloadSet_dict[ele.tag.lower()] = ele.text

            isis_info["isoverloadset"].append(isOverloadSet_dict)

        return isis_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["instanceid"] = self.instanceid
        if self.stdoverloadtype is not None:
            self.proposed['stdoverloadtype'] = self.stdoverloadtype
        if self.stdoverloadwaittype is not None:
            self.proposed['stdoverloadwaittype'] = self.stdoverloadwaittype
        if self.stdoverloadnbrsysid is not None:
            self.proposed['stdoverloadnbrsysid'] = self.stdoverloadnbrsysid
        if self.stdoverloadtimeout1 is not None:
            self.proposed['stdoverloadtimeout1'] = self.stdoverloadtimeout1
        if self.stdoverloadtimeout2 is not None:
            self.proposed['stdoverloadtimeout2'] = self.stdoverloadtimeout2
        if self.stdoverloadinterlevel is not None:
            self.proposed['stdoverloadinterlevel'] = self.stdoverloadinterlevel
        if self.stdoverloadexternal is not None:
            self.proposed['stdoverloadexternal'] = self.stdoverloadexternal
        if self.stdoverloadsendsabit is not None:
            self.proposed['stdoverloadsendsabit'] = self.stdoverloadsendsabit
        if self.stdoverloadsabittime is not None:
            self.proposed['stdoverloadsabittime'] = self.stdoverloadsabittime

        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if not self.isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        self.existing["isoverloadset"] = self.isis_info["isoverloadset"]

    def get_end_state(self):
        """get end state info"""

        isis_info = self.get_isis_dict()
        if not isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        self.existing["isoverloadset"] = isis_info["isoverloadset"]

    def merge_process(self):
        """Comm  isis process"""

        # Process schema or yang,  CE_XPATH_ISISCOMM_YANG_OR_SCHEMA
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_MERGE

        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_container_head(xml_str, "isOverloadSet")

        # Body process
        xml_str = constr_leaf_value(xml_str, "stdOverloadType", self.stdoverloadtype)
        xml_str = constr_leaf_value(xml_str, "stdOverloadWaitType", self.stdoverloadwaittype)
        xml_str = constr_leaf_value(xml_str, "stdOverloadNbrSysId", self.stdoverloadnbrsysid)
        xml_str = constr_leaf_value(xml_str, "stdOverloadTimeout1", self.stdoverloadtimeout1)
        xml_str = constr_leaf_value(xml_str, "stdOverloadTimeout2", self.stdoverloadtimeout2)
        xml_str = constr_leaf_value(xml_str, "stdOverloadInterlevel", self.stdoverloadinterlevel)
        xml_str = constr_leaf_value(xml_str, "stdOverloadExternal", self.stdoverloadexternal)
        xml_str = constr_leaf_value(xml_str, "stdOverloadSendSaBit", self.stdoverloadsendsabit)
        xml_str = constr_leaf_value(xml_str, "stdOverloadSaBitTime", self.stdoverloadsabittime)
        # Tail process
        xml_str = constr_container_tail(xml_str, "isOverloadSet")
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "MERGE_OPERATION")

        # 更新CLI 命令行信息
        self.changed = True

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
                self.module.fail_json(msg='Error: Isis instance does not exist')
            else:
                # merge isis process
                self.merge_process()
        else:
            # 查询输出
            if not self.isis_info:
                self.module.fail_json(msg='Error: Isis instance does not exist')

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
        instanceid=dict(required=True, type='str'),
        stdoverloadtype=dict(required=False, choices=['no_set', 'on_startup', 'maunal']),
        stdoverloadwaittype=dict(required=False, choices=['no_wait', 'wait_for_bgp', 'start_from_nbr']),
        stdoverloadnbrsysid=dict(required=False, type='str'),
        stdoverloadtimeout1=dict(required=False, type='int'),
        stdoverloadtimeout2=dict(required=False, type='int'),
        stdoverloadinterlevel=dict(required=False, choices=['true', 'false']),
        stdoverloadexternal=dict(required=False, choices=['true', 'false']),
        stdoverloadsendsabit=dict(required=False, choices=['true', 'false']),
        stdoverloadsabittime=dict(required=False, type='int'),
        state=dict(required=False, default='present', choices=['present', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = ISIS_isOverloadSet(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
