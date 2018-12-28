#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import copy
import logging
import re
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_brasvas_edsgsupporthwpolicyname_config
version_added: "2.6"
short_description:  Manage brasvas module edsgSupportHwPolicyName config rule configuration.
description:
    -  Manage brasvas module edsgSupportHwPolicyName config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    supportEdsg:
        description:
            -  Configures the HW-Policy-Name attribute to carry the EDSG service policy name. the value is a string of true or false.
        required: false
        default: false
        choices: ['true', 'false']
    operation:
        description:
            -  Manage the state of the resource.If operation is get,the supportEdsg cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default:  merge
        choices: ['merge','get']
'''
EXAMPLES = '''

- name: Manage brasvas module edsgSupportHwPolicyName config rule configuration.
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
      host: "{{inventory_hostname}}"
      port: "{{ansible_ssh_port}}"
      username: "{{ansible_user}}"
      password: "{{ansible_ssh_pass}}"
      transport: cli

  tasks:

  - name:get a brasvas module  edsgSupportHwPolicyName config rule
    ne_brasvas_edsgSupportHwPolicyName_config:
    operation='get'
    provider="{{ cli }}"

  - name:merge a brasvas module  edsgSupportHwPolicyName config rule
    ne_brasvas_edsgSupportHwPolicyName_config:
    supportEdsg='true'
    operation='merge'
    provider="{{ cli }}"

'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "operation": "merge",
        "supportEdsg": "true"

    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
           "supportEdsgs": [
            {
                "supportEdsg": "true"
            }
        ]


    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
         "supportEdsgs": [
            {
                "supportEdsg": "true"
            }
        ]


    }
'''
logging.basicConfig(filename='example.log', level=logging.DEBUG)
EDSGSUPPORTHWPOLICYNAME_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
"""

EDSGSUPPORTHWPOLICYNAME_TAIL = """
        </brasvas>
    </config>
"""

IPV6PREFIXSLIFETIME_GETHEAD = """
    <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <edsgSupportHwPolicyName>
        <supportEdsg/>
"""

IPV6PREFIXSLIFETIME_HEAD_GET = """
    <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <edsgSupportHwPolicyName>
"""

IPV6PREFIXSLIFETIME_TAIL_GET = """
    </edsgSupportHwPolicyName>
    </brasvas>
  </filter>
"""

SUPPORTEDSG_GET = """
    <supportEdsg/>"""

EDSGSUPPORTHWPOLICYNAME_CREATE = """
        <edsgSupportHwPolicyName nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

EDSGSUPPORTHWPOLICYNAME_DELETE = """
        <edsgSupportHwPolicyName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

EDSGSUPPORTHWPOLICYNAME_MERGE = """
        <edsgSupportHwPolicyName nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SUPPORTEDSG = """
      <supportEdsg>%s</supportEdsg>
"""

EDSGSUPPORTHWPOLICYNAMEEND = """
   </edsgSupportHwPolicyName>
"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.supportEdsg = self.module.params['supportEdsg']
        self.operation = self.module.params['operation']

        if self.supportEdsg is None and self.operation != 'get':
            self.supportEdsg = 'false'

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.supportEdsg is not None:
            self.proposed["supportEdsg"] = self.supportEdsg
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def check_params(self):
        if self.poolName:
            if len(self.poolName) > 128 or len(
                    self.poolName.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: poolName is not in the range from 1 to 128.')

    def create_set_delete_process(self):
        cfg_str = ''
        cfg_str += EDSGSUPPORTHWPOLICYNAME_HEAD
        if self.operation == 'create':
            cfg_str += EDSGSUPPORTHWPOLICYNAME_CREATE
        if self.operation == 'delete':
            cfg_str += EDSGSUPPORTHWPOLICYNAME_DELETE
        if self.operation == 'merge':
            cfg_str += EDSGSUPPORTHWPOLICYNAME_MERGE
        if self.supportEdsg:
            cfg_str += SUPPORTEDSG % self.supportEdsg
        cfg_str += EDSGSUPPORTHWPOLICYNAMEEND
        cfg_str += EDSGSUPPORTHWPOLICYNAME_TAIL
        # 第二步: 下发配置报文
        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += IPV6PREFIXSLIFETIME_HEAD_GET
        if self.operation == 'get':
            if self.supportEdsg:
                cfg_str += SUPPORTEDSG % self.supportEdsg
        if self.operation != 'get':
            cfg_str += SUPPORTEDSG_GET
        cfg_str += IPV6PREFIXSLIFETIME_TAIL_GET

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasvas/edsgSupportHwPolicyName")
        attributes_Info["supportEdsgs"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["supportEdsg"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                    attributes_Info["supportEdsgs"].append(
                        service_container_Table)

        if len(attributes_Info["supportEdsgs"]) == 0:
            attributes_Info.clear()
        # 解析5: 返回数据
        return attributes_Info

    def run(self):
        # 第一步: 检测输入

        # 第二步: 下发 get 报文, 查询当前配置
        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        # 第三步: 根据用户输入的操作码下发配置, 查询功能已经在 get_existing 实现
        if self.operation != 'get':
            self.create_set_delete_process()
            # 配置结束, 重新查询下当前状态
            self.end_state = self.get_info_process()
            self.results['end_state'] = self.end_state

        # 第四步: 设置最后状态
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.module.exit_json(**self.results)


def main():
    """ main module """
    logging.debug('This message should go to the log file ******')
    argument_spec = dict(
        supportEdsg=dict(required=False, choices=['true', 'false']),
        operation=dict(
            required=False,
            choices=[
                'merge',
                'get'],
            default='merge'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
