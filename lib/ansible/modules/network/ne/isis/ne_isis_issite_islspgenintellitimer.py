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
module: ne_isis_issite_islspgenintellitimer
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
    ne_isis_issite_islspgenintellitimer:
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


class ISIS_isLspGenIntelliTimer(object):
    """Manages configuration of an ISIS interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.instanceid = self.module.params['instanceid']
        self.level1lspgenmaxinterval = self.module.params['level1lspgenmaxinterval']
        self.level2lspgenmaxinterval = self.module.params['level2lspgenmaxinterval']
        self.level1lspgeninitinterval = self.module.params['level1lspgeninitinterval']
        self.level2lspgeninitinterval = self.module.params['level2lspgeninitinterval']
        self.level1lspgenincrinterval = self.module.params['level1lspgenincrinterval']
        self.level2lspgenincrinterval = self.module.params['level2lspgenincrinterval']
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
        #    if int(self.level1LspGenMaxInterval) < 1 or int(self.level1LspGenMaxInterval) > 120:
        #        self.module.fail_json(
        #            msg='Error: The level1LspGenMaxInterval is not in the range from 1 to 120.')
        #    if int(self.level2LspGenMaxInterval) < 1 or int(self.level2LspGenMaxInterval) > 120:
        #        self.module.fail_json(
        #            msg='Error: The level2LspGenMaxInterval is not in the range from 1 to 120.')
        #    if int(self.level1LspGenInitInterval) < 0 or int(self.level1LspGenInitInterval) > 60000:
        #        self.module.fail_json(
        #            msg='Error: The level1LspGenInitIntervalis not in the range from 0 to 60000.')
        #    if int(self.level2LspGenInitInterval) < 0 or int(self.level2LspGenInitInterval) > 60000:
        #        self.module.fail_json(
        #            msg='Error: The level2LspGenInitInterval not in the range from 0 to 60000.')
        #    if int(self.level1LspGenIncrInterval) < 0 or int(self.level1LspGenIncrInterval) > 60000:
        #        self.module.fail_json(
        #            msg='Error: The level1LspGenIncrInterval not in the range from 0 to 60000.')
        #    if int(self.level2LspGenIncrInterval) < 0 or int(self.level2LspGenIncrInterval) > 60000:
        #        self.module.fail_json(
        #            msg='Error: The level2LspGenIncrInterval not in the range from 0 to 60000.')

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
        conf_str = constr_container_head(conf_str, "isLspGenIntelliTimer")
        conf_str = constr_leaf_novalue(conf_str, "level1LspGenMaxInterval")
        conf_str = constr_leaf_novalue(conf_str, "level2LspGenMaxInterval")
        conf_str = constr_leaf_novalue(conf_str, "level1LspGenInitInterval")
        conf_str = constr_leaf_novalue(conf_str, "level2LspGenInitInterval")
        conf_str = constr_leaf_novalue(conf_str, "level1LspGenIncrInterval")
        conf_str = constr_leaf_novalue(conf_str, "level2LspGenIncrInterval")
        conf_str = constr_container_tail(conf_str, "isLspGenIntelliTimer")
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
        isis_info["islspgenintellitimer"] = list()
        isLspGenIntelliTimer = root.findall(
            "data/isiscomm/isSites/isSite/isLspGenIntelliTimer")
        if len(isLspGenIntelliTimer) != 0:
            isLspGenIntelliTimer_dict = dict()
            for ele in isLspGenIntelliTimer:
                if ele.tag in ["level1LspGenMaxInterval",
                               "level2LspGenMaxInterval",
                               "level1LspGenInitInterval",
                               "level2LspGenInitInterval",
                               "level1LspGenIncrInterval",
                               "level2LspGenIncrInterval"]:
                    isLspGenIntelliTimer_dict[ele.tag.lower()] = ele.text

            isis_info["islspgenintellitimer"].append(isLspGenIntelliTimer_dict)

        return isis_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["instanceid"] = self.instanceid
        if self.level1lspgenmaxinterval is not None:
            self.proposed['level1lspgenmaxinterval'] = self.level1lspgenmaxinterval
        if self.level2lspgenmaxinterval is not None:
            self.proposed['level2lspgenmaxinterval'] = self.level2lspgenmaxinterval
        if self.level1lspgeninitinterval is not None:
            self.proposed['level1lspgeninitinterval'] = self.level1lspgeninitinterval
        if self.level2lspgeninitinterval is not None:
            self.proposed['level2lspgeninitinterval'] = self.level2lspgeninitinterval
        if self.level1lspgenincrinterval is not None:
            self.proposed['level1lspgenincrinterval'] = self.level1lspgenincrinterval
        if self.level2lspgenincrinterval is not None:
            self.proposed['level2lspgenincrinterval'] = self.level2lspgenincrinterval

        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if not self.isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        self.existing["islspgenintellitimer"] = self.isis_info["islspgenintellitimer"]

    def get_end_state(self):
        """get end state info"""

        isis_info = self.get_isis_dict()
        if not isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        self.existing["islspgenintellitimer"] = isis_info["islspgenintellitimer"]

    def merge_process(self):
        """Comm  isis process"""

        # Process schema or yang,  CE_XPATH_ISISCOMM_YANG_OR_SCHEMA
        # Head process
        xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_MERGE

        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_container_head(xml_str, "isLspGenIntelliTimer")

        # Body process
        xml_str = constr_leaf_value(xml_str, "level1LspGenMaxInterval", self.level1lspgenmaxinterval)
        xml_str = constr_leaf_value(xml_str, "level2LspGenMaxInterval", self.level2lspgenmaxinterval)
        xml_str = constr_leaf_value(xml_str, "level1LspGenInitInterval", self.level1lspgeninitinterval)
        xml_str = constr_leaf_value(xml_str, "level2LspGenInitInterval", self.level2lspgeninitinterval)
        xml_str = constr_leaf_value(xml_str, "level1LspGenIncrInterval", self.level1lspgenincrinterval)
        xml_str = constr_leaf_value(xml_str, "level2LspGenIncrInterval", self.level2lspgenincrinterval)
        # Tail process
        xml_str = constr_container_tail(xml_str, "isLspGenIntelliTimer")
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
        level1lspgenmaxinterval=dict(required=False, type='int'),
        level2lspgenmaxinterval=dict(required=False, type='int'),
        level1lspgeninitinterval=dict(required=False, type='int'),
        level2lspgeninitinterval=dict(required=False, type='int'),
        level1lspgenincrinterval=dict(required=False, type='int'),
        level2lspgenincrinterval=dict(required=False, type='int'),
        state=dict(required=False, default='present', choices=['present', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = ISIS_isLspGenIntelliTimer(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
