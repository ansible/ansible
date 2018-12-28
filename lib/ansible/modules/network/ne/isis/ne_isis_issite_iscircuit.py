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
module: ne_isis_issite_iscircuit
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
    ne_isis_isCircuit:
      instanceId: 1

      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"instanceId": "1", "ifName":LoopBack0}
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


class ISIS_isCircuit(object):
    """Manages configuration of an ISIS interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.instanceid = self.module.params['instanceid']
        self.ifname = self.module.params['ifname']
        self.ipv4enable = self.module.params['ipv4enable']
        self.ipv6enable = self.module.params['ipv6enable']
        self.typep2penable = self.module.params['typep2penable']
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

        required_one_of = [["instanceid", "ifname", "ipv4enable", "ipv6enable", "typep2penable"]]

        self.module = AnsibleModule(
            argument_spec=self.spec,
            required_one_of=required_one_of,
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
        # if self.ifName:
        #    if len(self.ifName) > 63:
        #        self.module.fail_json(
        #             msg='Error: The length of the interface name is not in the range from 1 to 63.')

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
        conf_str = constr_container_head(conf_str, "isCircuits")
        conf_str = constr_container_head(conf_str, "isCircuit")
        # Body info
        conf_str = constr_leaf_value(conf_str, "ifName", self.ifname)
        conf_str = constr_leaf_novalue(conf_str, "ipv4Enable")
        conf_str = constr_leaf_novalue(conf_str, "ipv6Enable")
        conf_str = constr_leaf_novalue(conf_str, "typeP2pEnable")

        # Tail info
        conf_str = constr_container_tail(conf_str, "isCircuit")
        conf_str = constr_container_tail(conf_str, "isCircuits")
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
        # if iSsite is not None:
        if len(iSsite) != 0:
            for site in iSsite:
                if site.tag in ["instanceId"]:
                    isis_info[site.tag.lower()] = site.text

        # isCircuits 数据， isCircuits 是多实例记录
        isis_info["iscircuits"] = list()
        isCircuits = root.findall(
            "data/isiscomm/isSites/isSite/isCircuits/isCircuit")
        if len(isCircuits) != 0:
            for isCircuit in isCircuits:
                isCircuit_dict = dict()
                for ele in isCircuit:
                    if ele.tag in ["ifName", "ipv4Enable", "ipv6Enable", "typeP2pEnable"]:
                        isCircuit_dict[ele.tag.lower()] = ele.text
                isis_info["iscircuits"].append(isCircuit_dict)

        return isis_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["instanceid"] = self.instanceid
        self.proposed["ifname"] = self.ifname
        if self.ifname:
            if self.ipv4enable is not None:
                self.proposed["ipv4enable"] = self.ipv4enable
            if self.ipv6enable is not None:
                self.proposed["ipv6enable"] = self.ipv6enable
            if self.typep2penable is not None:
                self.proposed["typep2penable"] = self.typep2penable

        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if not self.isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        self.existing["iscircuits"] = self.isis_info["iscircuits"]

    def get_end_state(self):
        """get end state info"""

        isis_info = self.get_isis_dict()
        if not isis_info:
            return

        self.end_state["instanceid"] = self.instanceid
        self.end_state["iscircuits"] = isis_info["iscircuits"]

    def create_process(self):
        """Create isis process"""
        self.comm_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

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
        xml_str = constr_container_process_head(xml_str, "isCircuit", operation)

        xml_str = constr_leaf_value(xml_str, "ifName", self.ifname)
        xml_str = constr_leaf_value(xml_str, "ipv4Enable", self.ipv4enable)
        xml_str = constr_leaf_value(xml_str, "ipv6Enable", self.ipv6enable)
        xml_str = constr_leaf_value(xml_str, "typeP2pEnable", self.typep2penable)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "isCircuit")
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, operation_Desc)

        # if self.ipv4enable:
        #    if True == self.ipv4enable:
        #        self.updates_cmd.append("isis enable %s" % self.instanceid)
        #    else:
        #        self.updates_cmd.append("undo isis enable")
        #
        # if self.ipv6enable:
        #    if True == self.ipv6enable:
        #        self.updates_cmd.append("isis ipv6 enable %s" % self.instanceid)
        #    else:
        #        self.updates_cmd.append("undo isis ipv6 enable")
        #
        # if self.typep2penable:
        #    if True == self.typep2penable:
        #        self.updates_cmd.append("isis circuit-type p2p")
        #    else:
        #        self.updates_cmd.append("undo isis circuit-type")

        self.changed = True

    def merge_process(self):
        """ Merge isis process """
        self.comm_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete isis  process"""

        xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_MERGE
        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_container_process_head(xml_str, "isCircuit", NE_COMMON_XML_OPERATION_DELETE)

        xml_str = constr_leaf_value(xml_str, "ifName", self.ifname)

        xml_str = constr_container_process_tail(xml_str, "isCircuit")
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "DELETE_PROCESS")
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
                # create isis process
                self.create_process()
            else:
                # merge isis process
                self.merge_process()
        elif self.state == "absent":
            if self.isis_info:
                # remove isis process
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: Isis instance does not exist')
        elif self.state == "query":
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
        ifname=dict(required=True, type='str'),
        ipv4enable=dict(required=False, choices=['true', 'false']),
        ipv6enable=dict(required=False, choices=['true', 'false']),
        typep2penable=dict(required=False, choices=['true', 'false']),
        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = ISIS_isCircuit(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
