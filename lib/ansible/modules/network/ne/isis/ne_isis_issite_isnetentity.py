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
module: ne_isis_isNetEntity
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
    ne_isis_issite_isnetentity:
      instanceid: 1
      netentity:10.1111.1111.1111.00
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"instanceid": "1", "netentity":10.1111.1111.1111.00}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"instanceid": "1", "netentity":10.1111.1111.1111.00}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"instanceid": "1", "netentity":10.1111.1111.1111.00}

    updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["isis 1", "network-entity 10.1111.1111.1111.00"]
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


class ISIS_netEntity(object):
    """Manages configuration of an ISIS instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.instanceid = self.module.params['instanceid']
        self.netentity = self.module.params['netentity']
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
        required_one_of = [["instanceid", "netentity"]]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
            supports_check_mode=True)

    def is_valid_netEntity(self, netEntity):
        """Check the  netEntiy is  valid"""

        # check isis netEntity 1~83
        # <netEntity>10.0000.0000.0001.00</netEntity>
        # 设置网络实体（Network Entity Title，NET），
        # 格式为X…X.XXXX.XXXX.XXXX.00，前面的“X…X”是区域地址，
        # 中间的12个“X”是路由器的System ID，“X”是16进制字符，不区分大小写，最后的“00”是SEL。
        if len(netEntity) > 83:
            return False

        # 点分格式判断
        if netEntity.find('.') != -1:
            netEntity_list = netEntity.split('.')
            list_num = len(netEntity_list)

            # 点分格式个数 小于5 错误。
            if list_num < 5:
                return False

            # 最后的“00”是SEL
            if "00" != netEntity_list[list_num - 1]:
                return False

            # “X”是16进制字符, 检查是否是数字, 使用int 函数转换
            for each_ID in netEntity_list:
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
        # if self.instanceid:
        #    if not self.instanceid.isdigit():
        #        self.module.fail_json(
        #            msg='error: Instance id is not digit.')
        #    if int(self.instanceid) <= 1 or int(self.instanceid) > 4294967295:
        #        self.module.fail_json(
        #            msg='Error: Instance Id is not in the range from 1 to 4094.')
        #
        # if self.netentity:
        #    if not self.is_valid_netEntity(self.netentity):
        #        self.module.fail_json(
        #            msg='Error: Isis netEntity format as xx.xxxx.xxxx.xxxx.xx')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_isis_dict(self):
        """ get one isis attributes dict."""

        isis_info = dict()
        # use schema xpath
        # CE_XPATH_ISISCOMM_YANG_OR_SCHEMA  OR CE_YANG_XPATH_ISISCOMM
        conf_str = NE_COMMON_XML_GET_ISISCOMM_HEAD
        conf_str = constr_leaf_value(conf_str, "instanceId", self.instanceid)
        conf_str = constr_container_head(conf_str, "isNetEntitys")
        conf_str = constr_container_head(conf_str, "isNetEntity")
        conf_str = constr_leaf_value(conf_str, "netEntity", self.netentity)
        conf_str = constr_container_tail(conf_str, "isNetEntity")
        conf_str = constr_container_tail(conf_str, "isNetEntitys")
        conf_str += NE_COMMON_XML_GET_ISISCOMM_TAIL

        xml_str = get_nc_config(self.module, conf_str)

        # No record return , 没有找到记录直接返回
        if "<data/>" in xml_str:
            return isis_info

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-isiscomm"', "")
        # get process base info
        root = ElementTree.fromstring(xml_str)
        iSsite = root.find("isiscomm/isSites/isSite")
        # if iSsite is not None:
        if len(iSsite) != 0:
            for site in iSsite:
                if site.tag in ["instanceId"]:
                    isis_info[site.tag.lower()] = site.text

        # 获取isNetEntitys 数据， isNetEntity 是多实例记录
        isis_info["isnetentitys"] = list()
        isnetentitys = root.findall(
            "data/isiscomm/isSites/isSite/isNetEntitys/isNetEntity")

        if len(isnetentitys) != 0:
            for isnetentity in isnetentitys:
                isNetEntity_dict = dict()
                for ele in isnetentity:
                    if ele.tag in ["netEntity"]:
                        isNetEntity_dict[ele.tag.lower()] = ele.text

                isis_info["isnetentitys"].append(isNetEntity_dict)

        return isis_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["instanceid"] = self.instanceid
        self.proposed["netentity"] = self.netentity
        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        isis_info = self.get_isis_dict()
        if not isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        self.existing["isnetentitys"] = isis_info["isnetentitys"]

    def get_end_state(self):
        """get end state info"""

        isis_info = self.get_isis_dict()
        if not isis_info:
            return

        self.end_state["instanceid"] = self.instanceid
        self.end_state["isnetentitys"] = isis_info["isnetentitys"]

    def merge_process(self):
        # Process schema or yang,  CE_XPATH_ISISCOMM_YANG_OR_SCHEMA
        xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_MERGE

        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_container_process_head(xml_str, "isNetEntity", NE_COMMON_XML_OPERATION_MERGE)

        xml_str = constr_leaf_value(xml_str, "netEntity", self.netentity)
        xml_str = constr_container_process_tail(xml_str, "isNetEntity")
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "CREATE_PROCESS")
        self.updates_cmd.append("network-entity %s" % self.netentity)
        self.changed = True

    def delete_process(self):
        """Delete isis  process"""
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_MERGE

        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_container_process_head(xml_str, "isNetEntity", NE_COMMON_XML_OPERATION_DELETE)

        xml_str = constr_leaf_value(xml_str, "netEntity", self.netentity)

        xml_str = constr_container_process_tail(xml_str, "isNetEntity")
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.updates_cmd.append("undo network-entity %s" % self.netentity)
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        self.isis_info = self.get_isis_dict()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        if self.state == "present":
            # 创建netEntity 流程统一走 merge流程。不用判断 instanceId 是否存在,不存在创建
            # merge isis process
            if not self.netentity:
                self.module.fail_json(msg='Error: Must input isis netEntity.')
            else:
                self.merge_process()
        elif self.state == "absent":
            if self.isis_info:
                if not self.netentity:
                    self.module.fail_json(msg='Error: Must input isis netEntity.')
                else:
                    # remove isis process
                    self.delete_process()
            else:
                self.module.fail_json(msg='Error: Isis netEntity does not exist')
        elif self.state == "query":
            # 查询输出
            if not self.isis_info:
                self.module.fail_json(msg='Error: Isis netEntity does not exist')

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
        netentity=dict(required=False, type='str'),
        state=dict(required=False, default='present', choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = ISIS_netEntity(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
