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
module: ne_radius_radiusaccesslineidlenextend_config
version_added: "2.6"
short_description: Configures the maximum length of the Agent-Circuit-Id or Agent-Remote-Id attribute carried in
RADIUS packets when a device trusts the Option 82 field in user packets as 198 bytes.
description:
    - Configures the maximum length of the Agent-Circuit-Id or Agent-Remote-Id attribute carried in RADIUS
    packets when a device trusts the Option 82 field in user packets as 198 bytes.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    accessLineIdLenExtend:
        description:
            - Configures the maximum length of the Agent-Circuit-Id or Agent-Remote-Id attribute.
        required: false
        default: false
        choices: ['true', 'false']
    operation:
        description:
            - Manage the state of the resource.If operation is get,the accessLineIdLenExtend cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: merge
        choices: ['merge', 'get']
'''

EXAMPLES = '''

- name: Manage the maximum length of the Agent-Circuit-Id or Agent-Remote-Id attribute test
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

  - name: Merge the the maximum length of the Agent-Circuit-Id or Agent-Remote-Id attribute configuration
    ne_radius_radiusaccesslineidlenextend_config:
      accessLineIdLenExtend='true'
      operation='merge'
      provider="{{ cli }}"

  - name: Get the maximum length of the Agent-Circuit-Id or Agent-Remote-Id attribute configuration
    ne_radius_radiusaccesslineidlenextend_config:
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
        "accessLineIdLenExtend": "true",
        "operation": "merge"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "accessLineIdLenExtends": [
            {
                "accessLineIdLenExtend": "false"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "accessLineIdLenExtends": [
            {
                "accessLineIdLenExtend": "true"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
ACCESSLINEIDLENEXTEND_HEAD = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
"""

ACCESSLINEIDLENEXTEND_TAIL = """
        </radiusAccessLineIdLenExtend>
      </radius>
    </config>
"""

RADIUSACCESSLINEIDLENEXTEND_GET_HEAD = """
    <filter type="subtree">
    <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
      <radiusAccessLineIdLenExtend>
"""

RADIUSACCESSLINEIDLENEXTEND_GET_TAIL = """
        </radiusAccessLineIdLenExtend>
    </radius>
  </filter>
"""

ACCESSLINEIDLENEXTEND_GET = """
      <accessLineIdLenExtend/>"""

ACCESSLINEIDLENEXTEND = """
      <accessLineIdLenExtend>%s</accessLineIdLenExtend>
"""

ACCESSLINEIDLENEXTEND_MERGE = """
      <radiusAccessLineIdLenExtend nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
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
        self.accessLineIdLenExtend = self.module.params['accessLineIdLenExtend']
        self.operation = self.module.params['operation']

        if self.accessLineIdLenExtend is None and self.operation != 'get':
            self.accessLineIdLenExtend = 'false'

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.accessLineIdLenExtend is not None:
            self.proposed["accessLineIdLenExtend"] = self.accessLineIdLenExtend
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
        cfg_str += ACCESSLINEIDLENEXTEND_HEAD
        if self.operation == 'merge':
            cfg_str += ACCESSLINEIDLENEXTEND_MERGE
        if self.accessLineIdLenExtend:
            cfg_str += ACCESSLINEIDLENEXTEND % self.accessLineIdLenExtend
        cfg_str += ACCESSLINEIDLENEXTEND_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += RADIUSACCESSLINEIDLENEXTEND_GET_HEAD
        if self.operation == 'get':
            if self.accessLineIdLenExtend:
                cfg_str += ACCESSLINEIDLENEXTEND % self.accessLineIdLenExtend
        if self.operation != 'get':
            cfg_str += ACCESSLINEIDLENEXTEND_GET
        cfg_str += RADIUSACCESSLINEIDLENEXTEND_GET_TAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-radius"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_attributes_Info = root.findall(
            "radius/radiusAccessLineIdLenExtend")
        attributes_Info["accessLineIdLenExtends"] = list()

        if len(container_attributes_Info) != 0:
            for container_node in container_attributes_Info:
                container_Table = dict()
                for leaf_attributes_Info in container_node:
                    if leaf_attributes_Info.tag in ["accessLineIdLenExtend"]:
                        container_Table[leaf_attributes_Info.tag] = leaf_attributes_Info.text
                attributes_Info["accessLineIdLenExtends"].append(
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
        accessLineIdLenExtend=dict(required=False, choices=['true', 'false']),
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
