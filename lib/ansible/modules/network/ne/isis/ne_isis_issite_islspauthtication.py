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
module: ne_isis_issite_islspauthtication
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


class ISIS_isLspAuthtication(object):
    """Manages configuration of an ISIS interface."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.instanceid = self.module.params['instanceid']
        self.cmdtype = self.module.params['cmdtype']
        self.passwordtype = self.module.params['passwordtype']
        self.simplepassword = self.module.params['simplepassword']
        self.md5password = self.module.params['md5password']
        self.servicetype = self.module.params['servicetype']
        self.authenusage = self.module.params['authenusage']
        self.keyid = self.module.params['keyid']
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
        # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

        required_one_of = [["instanceid", "cmdtype"]]
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
        #
        # if self.simplePassword:
        #    if len(self.simplePassword) > 16:
        #        self.module.fail_json(
        #            msg='Error: The simplePassword length is out of rang from 1 to 16.')
        #
        # if self.md5Password:
        #    if len(self.md5Password) > 16:
        #        self.module.fail_json(
        #            msg='Error: The md5Password length is out of rang from 1 to 255.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_isis_dict(self):
        """ get one isis attributes dict."""

        isis_info = dict()
        conf_str = NE_COMMON_XML_GET_ISISCOMM_HEAD
        conf_str = constr_leaf_value(conf_str, "instanceId", self.instanceid)
        conf_str = constr_container_head(conf_str, "isLspAuthtications")
        conf_str = constr_container_head(conf_str, "isLspAuthtication")
        conf_str = constr_leaf_novalue(conf_str, "cmdType")
        conf_str = constr_leaf_novalue(conf_str, "passwordType")
        conf_str = constr_leaf_novalue(conf_str, "simplePassword")
        conf_str = constr_leaf_novalue(conf_str, "md5Password")
        conf_str = constr_leaf_novalue(conf_str, "serviceType")
        conf_str = constr_leaf_novalue(conf_str, "authenUsage")
        conf_str = constr_leaf_novalue(conf_str, "keyId")
        conf_str = constr_container_tail(conf_str, "isLspAuthtication")
        conf_str = constr_container_tail(conf_str, "isLspAuthtications")
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
                if site.tag in ["instanceid"]:
                    isis_info[site.tag.lower()] = site.text

        # isLspAuthtications 数据， isLspAuthtications 是多实例记录
        isis_info["islspauthtications"] = list()
        isLspAuthtications = root.findall(
            "data/isiscomm/isSites/isSite/isLspAuthtications/isLspAuthtication")
        if len(isLspAuthtications) != 0:
            for isLspAuthtication in isLspAuthtications:
                isLspAuthtication_dict = dict()
                for ele in isLspAuthtication:
                    if ele.tag in ["cmdtype", "passwordtype", "simplepassword", "md5password", "servicetype", "authenusage", "keyid"]:
                        isLspAuthtication_dict[ele.tag.lower()] = ele.text

                isis_info["islspauthtications"].append(isLspAuthtication_dict)

        return isis_info

    def get_proposed(self):
        """get proposed info"""

        # key 值必输
        self.proposed["cmdtype"] = self.cmdtype
        self.proposed["passwordtype"] = self.passwordtype
        self.proposed["instanceid"] = self.instanceid
        if self.simplepassword is not None:
            self.proposed['simplepassword'] = self.simplepassword
        if self.md5password is not None:
            self.proposed['md5password'] = self.md5password
        if self.servicetype is not None:
            self.proposed['servicetype'] = self.servicetype
        if self.authenusage is not None:
            self.proposed['authenusage'] = self.authenusage
        if self.authenusage is not None:
            self.proposed['keyid'] = self.keyid

        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""
        if not self.isis_info:
            return

        self.existing["instanceid"] = self.instanceid
        self.existing["islspauthtications"] = self.isis_info["islspauthtications"]

    def get_end_state(self):
        """get end state info"""

        isis_info = self.get_isis_dict()
        if not isis_info:
            return

        self.end_state["instanceid"] = self.instanceid
        self.end_state["islspauthtications"] = isis_info["islspauthtications"]

    def comm_process(self, operation, operation_Desc):
        """Comm  isis process"""

        # Process schema or yang,  CE_XPATH_ISISCOMM_YANG_OR_SCHEMA
        # Head process
        if NE_COMMON_XML_OPERATION_CREATE == operation:
            xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_MERGE
        else:
            xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % operation

        # Head process
        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_container_process_head(xml_str, "isLspAuthtication", operation)

        # Body process
        xml_str = constr_leaf_value(xml_str, "cmdType", self.cmdtype)
        xml_str = constr_leaf_value(xml_str, "passwordType", self.passwordtype)
        xml_str = constr_leaf_value(xml_str, "simplePassword", self.simplepassword)
        xml_str = constr_leaf_value(xml_str, "md5Password", self.md5password)
        xml_str = constr_leaf_value(xml_str, "serviceType", self.servicetype)
        xml_str = constr_leaf_value(xml_str, "authenUsage", self.authenusage)
        xml_str = constr_leaf_value(xml_str, "keyId", self.keyid)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "isLspAuthtication")
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

    def delete_process(self):
        """Delete isis  process"""

        xml_str = NE_COMMON_XML_PROCESS_ISIS_HEAD % NE_COMMON_XML_OPERATION_MERGE

        # Head process
        xml_str = constr_leaf_value(xml_str, "instanceId", self.instanceid)
        xml_str = constr_container_process_head(xml_str, "isLspAuthtication", NE_COMMON_XML_OPERATION_DELETE)

        # Body process
        xml_str = constr_leaf_value(xml_str, "cmdType", self.cmdtype)
        # xml_str = constr_leaf_value(xml_str, "passwordType", self.passwordType)

        # Tail process
        xml_str = constr_container_process_tail(xml_str, "isLspAuthtication")
        xml_str += NE_COMMON_XML_PROCESS_ISIS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

    def work(self):
        """worker"""
        self.check_params()

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
    # pydevd.settrace('10.165.64.94', port=9999, stdoutToServer=True, stderrToServer=True)

    argument_spec = dict(
        instanceid=dict(required=True, type='str'),
        cmdtype=dict(required=True, choices=['area', 'domain']),
        passwordtype=dict(required=False, choices=['simple', 'md5', 'hmac_sha256']),
        simplepassword=dict(required=False, type='str'),
        md5password=dict(required=False, type='str'),
        servicetype=dict(required=False, choices=['ip', 'osi']),
        authenusage=dict(required=False, choices=['usage_default', 'authentication_avoid', 'send_only', 'all_send_only']),
        keyid=dict(required=False, type='int'),

        state=dict(required=False, default='present', choices=['present', 'absent', 'query']))

    argument_spec.update(ne_argument_spec)
    module = ISIS_isLspAuthtication(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
