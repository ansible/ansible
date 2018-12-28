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
module: ne_brasvas_edsgtrafficmode_config
version_added: "2.6"
short_description: Configures EDSG service rate limiting mode.
description:
    - Configures EDSG service rate limiting mode.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    domainName:
        description:
            - Specifies the name of a domain. The value can be a string of 1 to 64 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    rateLimitAndStaticMode:
        description:
            - Configures EDSG service rate limiting mode.
        required: false
        choices: ['defaultMode', 'separate', 'together']
    operation:
        description:
            - Manage the state of the resource.If operation is get,the rateLimitAndStaticMode cannot take parameters,otherwise
            The echo of the command line is'This operation are not supported'.
        required: false
        choices: ['merge', 'get']
'''

EXAMPLES = '''

- name: Configures EDSG service rate limiting mode test
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

  - name: Merge a EDSG service rate limiting mode configuration with separate
    ne_brasvas_edsgtrafficmode_config:
      domainName='cbb'
      rateLimitAndStaticMode='separate'
      operation='merge'
      provider="{{ cli }}"

  - name: Merge a EDSG service rate limiting mode configuration with together
    ne_brasvas_edsgtrafficmode_config:
      domainName='cbb'
      rateLimitAndStaticMode='together'
      operation='merge'
      provider="{{ cli }}"

  - name: Merge a EDSG service rate limiting mode configuration with defaultMode
    ne_brasvas_edsgtrafficmode_config:
      domainName='cbb'
      rateLimitAndStaticMode='defaultMode'
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
        "domainName": "cbb",
        "operation": "merge",
        "rateLimitAndStaticMode": "together"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "domainNames": [
            {
                "domainName": "cbb",
                "rateLimitAndStaticMode": "separate"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "domainNames": [
            {
                "domainName": "cbb",
                "rateLimitAndStaticMode": "together"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)

DOMAIN_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <domains>
"""

DOMAIN_TAIL = """
            </edsgTrafficMode>
          </domain>
        </domains>
      </brasvas>
    </config>
"""

DOMAINNAME = """
      <domainName>%s</domainName>"""

RATELIMITANDSTATICMODE = """
      <rateLimitAndStaticMode>%s</rateLimitAndStaticMode>"""

EDSGTRAFFICMODE = """
      <edsgTrafficMode>"""

DOMAIN_MERGE = """
      <domain nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DOMAIN_GET_HEAD = """
      <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <domains>
        <domain>"""

DOMAIN_GET_TAIL = """
          </edsgTrafficMode>
        </domain>
      </domains>
    </brasvas>
  </filter>"""

RATELIMITANDSTATICMODE_GET = """
      <rateLimitAndStaticMode/>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.domainName = self.module.params['domainName']
        self.rateLimitAndStaticMode = self.module.params['rateLimitAndStaticMode']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.rateLimitAndStaticMode is not None:
            self.proposed["rateLimitAndStaticMode"] = self.rateLimitAndStaticMode
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
        cfg_str += DOMAIN_HEAD
        if self.operation == 'merge':
            cfg_str += DOMAIN_MERGE
            if self.domainName:
                cfg_str += DOMAINNAME % self.domainName
            cfg_str += EDSGTRAFFICMODE
            if self.rateLimitAndStaticMode:
                cfg_str += RATELIMITANDSTATICMODE % self.rateLimitAndStaticMode

        cfg_str += DOMAIN_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += DOMAIN_GET_HEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        cfg_str += EDSGTRAFFICMODE
        if self.operation == 'get':
            if self.rateLimitAndStaticMode:
                cfg_str += RATELIMITANDSTATICMODE % self.rateLimitAndStaticMode
        if self.operation != 'get':
            cfg_str += RATELIMITANDSTATICMODE_GET
        cfg_str += DOMAIN_GET_TAIL

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
        container_1_attributes_Info = root.findall("brasvas/domains/domain")
        attributes_Info["domainNames"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["domainName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "edsgTrafficMode")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["rateLimitAndStaticMode"]:
                                container_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                attributes_Info["domainNames"].append(container_info_Table)

        if len(attributes_Info["domainNames"]) == 0:
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
    argument_spec = dict(
        domainName=dict(required=False, type='str'),
        rateLimitAndStaticMode=dict(
            required=False, choices=[
                'defaultMode', 'separate', 'together']),
        operation=dict(required=False, choices=['merge', 'get']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
