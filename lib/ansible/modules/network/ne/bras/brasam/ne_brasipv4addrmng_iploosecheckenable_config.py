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
module: ne_brasipv4addrmng_iploosecheckenable_config
version_added: "2.6"
short_description: Enables check server to assign ip whether in the network segment of the remote address pool gateway
description:
    - Enables check server to assign ip whether in the network segment of the remote address pool gateway
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    poolName:
        description:
            - Specifies the name of the IP address pool. The value can be a string of 1 to 128 characters. The value must start with either uppercase
            letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    poolType:
        description:
            - Specifies the type of the IP address pool.
        required: true
        choices: ['remote']
    ruiType:
        description:
            - Indicates RUI-slave address pools.
        required: true
        choices: ['true', 'false']
    overlapType:
        description:
            - Indicates an IP address pool that is used for the vCPE users.
        required: true
        choices: ['false']
    ipLooseCheckEnable:
        description:
            - Check-remote-ip Loose, 0 :disable, 1: enable.
        required: false
        choices: ['true', 'false']
    poolNameOperation:
        description:
            - Manage the state of the poolName.If poolNameOperation is get,the poolType and ruiType and overlapType and ipLooseCheckEnable
            cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: merge
        choices: ['create', 'merge', 'delete', 'get']
    ipLooseCheckEnableOperation:
        description:
            - Manage the state of the ipLooseCheckEnable.
        required: false
        choices: ['create', 'merge', 'delete']
'''

EXAMPLES = '''

- name: Enables check server to assign ip whether in the network segment of the remote address pool gateway test
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

  - name: Create and delete to assign ip whether in the network segment of the remote address pool gateway configuration test
    ne_brasdhcpserver_serverforwardmode_config:
      poolName='cbb'
      poolType='remote'
      ruiType='false'
      ipLooseCheckEnable='true'
      overlapType='false'
      poolNameOperation='create'
      ipLooseCheckEnableOperation='delete'
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
        "ipLooseCheckEnable": "true",
        "ipLooseCheckEnableOperation": "delete",
        "overlapType": "false",
        "poolName": "cbb",
        "poolNameOperation": "create",
        "poolType": "remote",
        "ruiType": "false"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "poolNames": [
            {
                "ipLooseCheckEnable": "false",
                "overlapType": "false",
                "poolName": "cbb",
                "poolType": "remote",
                "ruiType": "true"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "poolNames": [
            {
                "ipLooseCheckEnable": "false",
                "overlapType": "false",
                "poolName": "cbb",
                "poolType": "remote",
                "ruiType": "false"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)

IPV4POOL_HEAD = """
    <config>
      <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
        <ipv4Pools>
"""

IPV4POOL_TAIL = """
              </ipLooseCheckEnable>
          </ipv4Pool>
        </ipv4Pools>
      </brasipv4addrmng>
    </config>
"""

POOLNAME = """
      <poolName>%s</poolName>"""

POOLTYPE = """
      <poolType>%s</poolType>"""

RUITYPE = """
      <ruiType>%s</ruiType>"""

OVERLAPTYPE = """
      <overlapType>%s</overlapType>"""

IPLOOSECHECKENABLE = """
      <ipLooseCheckEnable>"""

IPLOOSECHECKENABLES = """
      <ipLooseCheckEnable>%s</ipLooseCheckEnable>"""

IPV4POOL_CREATE = """
      <ipv4Pool nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

IPV4POOL_MERGE = """
      <ipv4Pool nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

IPV4POOL_DELETE = """
      <ipv4Pool nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

IPLOOSECHECKENABLE_CREATE = """
      <ipLooseCheckEnable nc:operation="create">"""

IPLOOSECHECKENABLE_MERGE = """
      <ipLooseCheckEnable nc:operation="merge">"""

IPLOOSECHECKENABLE_DELETE = """
      <ipLooseCheckEnable nc:operation="delete">"""

IPV4POOL_GET_HEAD = """
      <filter type="subtree">
    <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
      <ipv4Pools>
        <ipv4Pool>"""

IPV4POOL_GET_TAIL = """
          </ipLooseCheckEnable>
        </ipv4Pool>
      </ipv4Pools>
    </brasipv4addrmng>
  </filter>"""

POOLTYPE_GET = """
      <poolType/>"""

RUITYPE_GET = """
      <ruiType/>"""

OVERLAPTYPE_GET = """
      <overlapType/>"""

IPLOOSECHECKENABLE_GET = """
      <ipLooseCheckEnable/>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.poolName = self.module.params['poolName']
        self.poolType = self.module.params['poolType']
        self.ruiType = self.module.params['ruiType']
        self.overlapType = self.module.params['overlapType']
        self.ipLooseCheckEnable = self.module.params['ipLooseCheckEnable']
        self.poolNameOperation = self.module.params['poolNameOperation']
        self.ipLooseCheckEnableOperation = self.module.params['ipLooseCheckEnableOperation']

        if self.poolType is None and self.poolNameOperation != 'get':
            self.poolType = 'remote'
        if self.overlapType is None and self.poolNameOperation != 'get':
            self.overlapType = 'false'

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.poolName is not None:
            self.proposed["poolName"] = self.poolName
        if self.poolType is not None:
            self.proposed["poolType"] = self.poolType
        if self.ruiType is not None:
            self.proposed["ruiType"] = self.ruiType
        if self.overlapType is not None:
            self.proposed["overlapType"] = self.overlapType
        if self.ipLooseCheckEnable is not None:
            self.proposed["ipLooseCheckEnable"] = self.ipLooseCheckEnable
        if self.poolNameOperation is not None:
            self.proposed["poolNameOperation"] = self.poolNameOperation
        if self.ipLooseCheckEnableOperation is not None:
            self.proposed["ipLooseCheckEnableOperation"] = self.ipLooseCheckEnableOperation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        self.changed = True
        cfg_str = ''
        cfg_str += IPV4POOL_HEAD
        if self.poolNameOperation == 'create':
            cfg_str += IPV4POOL_CREATE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            if self.overlapType:
                cfg_str += OVERLAPTYPE % self.overlapType
            if self.ipLooseCheckEnableOperation == 'create':
                cfg_str += IPLOOSECHECKENABLE_CREATE
                if self.ipLooseCheckEnable:
                    cfg_str += IPLOOSECHECKENABLES % self.ipLooseCheckEnable
            elif self.ipLooseCheckEnableOperation == 'merge':
                cfg_str += IPLOOSECHECKENABLE_MERGE
                if self.ipLooseCheckEnable:
                    cfg_str += IPLOOSECHECKENABLES % self.ipLooseCheckEnable
            elif self.ipLooseCheckEnableOperation == 'delete':
                cfg_str += IPLOOSECHECKENABLE_DELETE
                if self.ipLooseCheckEnable:
                    cfg_str += IPLOOSECHECKENABLES % self.ipLooseCheckEnable
            else:
                cfg_str += IPLOOSECHECKENABLE

        if self.poolNameOperation == 'merge':
            cfg_str += IPV4POOL_MERGE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            if self.overlapType:
                cfg_str += OVERLAPTYPE % self.overlapType
            if self.ipLooseCheckEnableOperation == 'create':
                cfg_str += IPLOOSECHECKENABLE_CREATE
            elif self.ipLooseCheckEnableOperation == 'merge':
                cfg_str += IPLOOSECHECKENABLE_MERGE
            elif self.ipLooseCheckEnableOperation == 'delete':
                cfg_str += IPLOOSECHECKENABLE_DELETE
            else:
                cfg_str += IPLOOSECHECKENABLE
            if self.ipLooseCheckEnable:
                cfg_str += IPLOOSECHECKENABLES % self.ipLooseCheckEnable

        if self.poolNameOperation == 'delete':
            cfg_str += IPV4POOL_DELETE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            if self.overlapType:
                cfg_str += OVERLAPTYPE % self.overlapType
            cfg_str += IPLOOSECHECKENABLE
            if self.ipLooseCheckEnable:
                cfg_str += IPLOOSECHECKENABLES % self.ipLooseCheckEnable

        cfg_str += IPV4POOL_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def check_params(self):
        if self.poolName is None:
            if ((self.poolType is not None) or (self.ruiType is not None) or (
                    self.overlapType is not None)) and self.poolNameOperation == 'get':
                self.module.fail_json(
                    msg='Error: This operation is not supported.')

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += IPV4POOL_GET_HEAD
        if self.poolName:
            cfg_str += POOLNAME % self.poolName
        if self.poolNameOperation == 'get':
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            if self.overlapType:
                cfg_str += OVERLAPTYPE % self.overlapType
            cfg_str += IPLOOSECHECKENABLE
            if self.ipLooseCheckEnable:
                cfg_str += IPLOOSECHECKENABLES % self.ipLooseCheckEnable
        if self.poolNameOperation != 'get':
            cfg_str += POOLTYPE_GET
            cfg_str += RUITYPE_GET
            cfg_str += OVERLAPTYPE_GET
            cfg_str += IPLOOSECHECKENABLE
            cfg_str += IPLOOSECHECKENABLE_GET
        cfg_str += IPV4POOL_GET_TAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasipv4addrmng/ipv4Pools/ipv4Pool")
        attributes_Info["poolNames"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in [
                            "poolName", "poolType", "ruiType", "overlapType"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "ipLooseCheckEnable")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["ipLooseCheckEnable"]:
                                container_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                attributes_Info["poolNames"].append(container_info_Table)

        if len(attributes_Info["poolNames"]) == 0:
            attributes_Info.clear()
        # 解析5: 返回数据
        return attributes_Info

    def run(self):
        # 第一步: 检测输入
        self.check_params()

        # 第二步: 下发 get 报文, 查询当前配置
        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        # 第三步: 根据用户输入的操作码下发配置, 查询功能已经在 get_existing 实现
        if self.poolNameOperation != 'get':
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
        poolName=dict(required=False, type='str'),
        poolType=dict(required=False, choices=['remote']),
        ruiType=dict(required=False, choices=['true', 'false']),
        overlapType=dict(required=False, choices=['false']),
        ipLooseCheckEnable=dict(required=False, choices=['true', 'false']),
        poolNameOperation=dict(
            required=False,
            choices=[
                'merge',
                'create',
                'delete',
                'get'],
            default='merge'),
        ipLooseCheckEnableOperation=dict(
            required=False, choices=[
                'merge', 'create', 'delete']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
