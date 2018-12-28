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
module: ne_brasipv6addrmng_ipv6poolbasic_config
version_added: "2.6"
short_description: Manages IPV6 address pool configuration instance rule configuration.
description:
    - Manages IPV6 address pool configuration instance rule configuration.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    poolName:
        description:
            - Specifies the name of an IPv6 address pool. The value can be a string of 1 to 32 characters. The value must start with either
            uppercase letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    poolType:
        description:
            - Specifies the type of an IPv6 address pool.
        required: true
        default: local
        choices: ['local', 'delegation', 'remote', 'relay']
    ruiType:
        description:
            - Indicates a hybrid IP address pool that can be used as both a local address pool and a remote address pool.
        required: true
        default: false
        choices: ['true', 'false']
    prefixName:
        description:
            - The prefix command binds an IPv6 prefix pool to an IPv6 address pool. The value can be a string of 1 to 32 characters.
            The value must start with either uppercase letters A to Z or lowercase letters a to z and be a combination of letters,
            digits, hyphens (-), and underscores (_).
        required: false
    poolNameOperation:
        description:
            - Manage the state of the resource.If poolNameOperation is get,the poolType and ruiType and prefixName cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        choices: ['create', 'merge', 'delete', 'get']
    prefixNameOperation:
        description:
            - Manage the state of the resource.
        required: false
        choices: ['create', 'merge', 'delete']
'''

EXAMPLES = '''

- name: IPV6 address pool configuration instance rule configuration test
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

  - name: Create a IPV6 address pool configuration instance
    ne_brasipv6addrmng_ipv6poolbasic_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      prefixName='cbb777'
      poolNameOperation='create'
      prefixNameOperation='create'
      provider="{{ cli }}"

  - name: Delete a IPV6 address pool configuration instance
    ne_brasipv6addrmng_ipv6poolbasic_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      prefixName='cbb777'
      poolNameOperation='delete'
      provider="{{ cli }}"

  - name: Merge and create a prefixName
    ne_brasipv6addrmng_ipv6poolbasic_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      prefixName='cbb'
      poolNameOperation='merge'
      prefixNameOperation='create'
      provider="{{ cli }}"

  - name: Merge and merge a new prefixName
    ne_brasipv6addrmng_ipv6poolbasic_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      prefixName='cbb1'
      poolNameOperation='merge'
      prefixNameOperation='merge'
      provider="{{ cli }}"

  - name: Merge and delete the prefixName
    ne_brasipv6addrmng_ipv6poolbasic_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      prefixName='cbb1'
      poolNameOperation='merge'
      prefixNameOperation='delete'
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
        "poolNameOperation": "merge",
        "prefixNameOperation": "merge",
        "poolName": "cbb",
        "poolType": "delegation",
        "prefixName": "ipv6test3",
        "ruiType": "true"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "poolNames": [
            {
                "poolName": "cbb",
                "poolType": "delegation",
                "prefixName": "ipv6test",
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
                "poolName": "cbb",
                "poolType": "delegation",
                "prefixName": "ipv6test3",
                "ruiType": "true"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)

IPV6POOL_HEAD = """
    <config>
      <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
        <ipv6Pools>
"""

IPV6POOL_TAIL = """
          </poolBasic>
          </ipv6Pool>
        </ipv6Pools>
      </brasipv6addrmng>
    </config>
"""

IPV6POOL_GET_HEAD = """
    <filter type="subtree">
    <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
      <ipv6Pools>
        <ipv6Pool>
"""

IPV6POOL_GET_TAIL = """
          </poolBasic>
        </ipv6Pool>
      </ipv6Pools>
    </brasipv6addrmng>
  </filter>
"""

POOLTYPE_GET = """
      <poolType/>"""

RUITYPE_GET = """
      <ruiType/>"""

AGENTREMOTEID_GET = """
      <agentRemoteId/>"""

PREFIXNAME_GET = """
      <prefixName/>"""

POOLNAME = """
      <poolName>%s</poolName>
"""

POOLTYPE = """
      <poolType>%s</poolType>
"""

RUITYPE = """
      <ruiType>%s</ruiType>"""

PREFIXNAME = """
      <prefixName>%s</prefixName>"""

IPV6POOL_CREATE = """
     <ipv6Pool nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

IPV6POOL_DELETE = """
      <ipv6Pool nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

IPV6POOL_MERGE = """
      <ipv6Pool nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

POOLBASIC = """
      <poolBasic>"""

POOLBASIC_CREATE = """
      <poolBasic nc:operation="create">"""

POOLBASIC_MERGE = """
      <poolBasic nc:operation="merge">"""

POOLBASIC_PREFIXNAME_DELETE = """
      <prefixName nc:operation="delete">%s</prefixName>"""


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
        self.prefixName = self.module.params['prefixName']
        self.poolNameOperation = self.module.params['poolNameOperation']
        self.prefixNameOperation = self.module.params['prefixNameOperation']

        if self.poolType is None and self.poolNameOperation != 'get':
            self.poolType = 'local'
        if self.ruiType is None and self.poolNameOperation != 'get':
            self.ruiType = 'false'

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.poolName is not None:
            self.proposed["poolName"] = self.poolName
        if self.poolType is not None:
            self.proposed["poolType"] = self.poolType
        if self.ruiType is not None:
            self.proposed["ruiType"] = self.ruiType
        if self.prefixName is not None:
            self.proposed["prefixName"] = self.prefixName
        if self.poolNameOperation is not None:
            self.proposed["poolNameOperation"] = self.poolNameOperation
        if self.prefixNameOperation is not None:
            self.proposed["prefixNameOperation"] = self.prefixNameOperation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        self.changed = True
        cfg_str = ''
        cfg_str += IPV6POOL_HEAD
        if self.poolNameOperation == 'create':
            cfg_str += IPV6POOL_CREATE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            if self.prefixNameOperation == 'create':
                cfg_str += POOLBASIC_CREATE
                if self.prefixName:
                    cfg_str += PREFIXNAME % self.prefixName
            if self.prefixNameOperation == 'merge':
                cfg_str += POOLBASIC_MERGE
                if self.prefixName:
                    cfg_str += PREFIXNAME % self.prefixName
            if self.prefixNameOperation == 'delete':
                cfg_str += POOLBASIC
                cfg_str += POOLBASIC_PREFIXNAME_DELETE % self.prefixName

        if self.poolNameOperation == 'delete':
            cfg_str += IPV6POOL_DELETE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            cfg_str += POOLBASIC
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName

        if self.poolNameOperation == 'merge':
            cfg_str += IPV6POOL_MERGE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            if self.prefixNameOperation == 'create':
                cfg_str += POOLBASIC_CREATE
                if self.prefixName:
                    cfg_str += PREFIXNAME % self.prefixName
            elif self.prefixNameOperation == 'merge':
                cfg_str += POOLBASIC_MERGE
                if self.prefixName:
                    cfg_str += PREFIXNAME % self.prefixName
            elif self.prefixNameOperation == 'delete':
                cfg_str += POOLBASIC
                cfg_str += POOLBASIC_PREFIXNAME_DELETE % self.prefixName
            else:
                cfg_str += POOLBASIC
                if self.prefixName:
                    cfg_str += PREFIXNAME % self.prefixName

        cfg_str += IPV6POOL_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def check_params(self):
        if self.poolName is None:
            if ((self.poolType is not None) or (
                    self.ruiType is not None)) and self.poolNameOperation == 'get':
                self.module.fail_json(msg='Error: This operation is not supported.')

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += IPV6POOL_GET_HEAD
        if self.poolName:
            cfg_str += POOLNAME % self.poolName
        if self.poolNameOperation == 'get':
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            cfg_str += POOLBASIC
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
        if self.poolNameOperation != 'get':
            cfg_str += POOLTYPE_GET
            cfg_str += RUITYPE_GET
            cfg_str += POOLBASIC
            cfg_str += PREFIXNAME_GET
        cfg_str += IPV6POOL_GET_TAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasipv6addrmng/ipv6Pools/ipv6Pool")
        attributes_Info["poolNames"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["poolName", "poolType", "ruiType"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "poolBasic")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["prefixName"]:
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
        poolType=dict(
            required=False,
            choices=[
                'local',
                'delegation',
                'remote',
                'relay']),
        ruiType=dict(required=False, choices=['true', 'false']),
        prefixName=dict(required=False, type='str'),
        poolNameOperation=dict(
            required=False,
            choices=[
                'merge',
                'create',
                'delete',
                'get'],
            default='merge'),
        prefixNameOperation=dict(
            required=False, choices=[
                'merge', 'create', 'delete']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
