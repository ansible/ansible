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
module: ne_brasdhcpv6access_option37decode_config
version_added: "2.6"
short_description: Manages option37 decode rule configuration.
description:
    - Manages option37 decode rule configuration.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    option37DecodeEnable:
        description:
            - Specifies whether parsing arbitrary format option-37 configuration
        required: false
        default: false
        choices: ['true', 'false']
    operation:
        description:
            - Manage the state of the resource.If operation is get,the option37DecodeEnable cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        choices: ['merge', 'get']
'''

EXAMPLES = '''

- name: Option37 decode rule configuration test
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

  - name: Merge a option37 decode rule configuration
    ne_brasdhcpv6access_option37decode_config:
      option37DecodeEnable='true'
      operation='merge'
      provider="{{ cli }}"

  - name: Get a option37 decode rule configuration
    ne_brasdhcpv6access_option37decode_config:
      operation='get'
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
        "option37DecodeEnable": "true"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "option37DecodeEnables": [
            {
                "option37DecodeEnable": "false"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "option37DecodeEnables": [
            {
                "option37DecodeEnable": "true"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
OPTION37DECODEENABLE_HEAD = """
    <config>
      <brasdhcpv6access xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpv6access">
"""

OPTION37DECODEENABLE_TAIL = """
        </option37Decode>
      </brasdhcpv6access>
    </config>
"""

OPTION37DECODE_GET_HEAD = """
    <filter type="subtree">
    <brasdhcpv6access xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpv6access">
      <option37Decode>
"""

OPTION37DECODE_GET_TAIL = """
         </option37Decode>
    </brasdhcpv6access>
  </filter>
"""

OPTION37DECODEENABLE_GET = """
      <option37DecodeEnable/>"""

OPTION37DECODEENABLE = """
      <option37DecodeEnable>%s</option37DecodeEnable>
"""

OPTION37DECODEENABLE_MERGE = """
      <option37Decode nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
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
        self.option37DecodeEnable = self.module.params['option37DecodeEnable']
        self.operation = self.module.params['operation']

        if self.option37DecodeEnable is None and self.operation != 'get':
            self.option37DecodeEnable = 'false'

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.option37DecodeEnable is not None:
            self.proposed["option37DecodeEnable"] = self.option37DecodeEnable
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        self.changed = True
        cfg_str = ''
        cfg_str += OPTION37DECODEENABLE_HEAD
        if self.operation == 'merge':
            cfg_str += OPTION37DECODEENABLE_MERGE
        if self.option37DecodeEnable:
            cfg_str += OPTION37DECODEENABLE % self.option37DecodeEnable
        cfg_str += OPTION37DECODEENABLE_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += OPTION37DECODE_GET_HEAD
        if self.operation == 'get':
            if self.option37DecodeEnable:
                cfg_str += OPTION37DECODEENABLE % self.option37DecodeEnable
        if self.operation != 'get':
            cfg_str += OPTION37DECODEENABLE_GET
        cfg_str += OPTION37DECODE_GET_TAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpv6access"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_attributes_Info = root.findall(
            "brasdhcpv6access/option37Decode")
        attributes_Info["option37DecodeEnables"] = list()

        if len(container_attributes_Info) != 0:
            for container_node in container_attributes_Info:
                container_Table = dict()
                for leaf_attributes_Info in container_node:
                    if leaf_attributes_Info.tag in ["option37DecodeEnable"]:
                        container_Table[leaf_attributes_Info.tag] = leaf_attributes_Info.text
                attributes_Info["option37DecodeEnables"].append(
                    container_Table)

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
    argument_spec = dict(
        option37DecodeEnable=dict(required=False, choices=['true', 'false']),
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
