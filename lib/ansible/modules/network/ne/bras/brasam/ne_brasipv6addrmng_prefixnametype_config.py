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
module: ne_brasipv6addrmng_prefixnametype_config
version_added: "2.6"
short_description: Manage brasipv6addrmng module prefixName and prefixType rule configuration.
description:
    - Manage brasipv6addrmng module prefixName and prefixType rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    prefixName:
        description:
            - Specifies the name of the IPv6 prefix pool to be created. The value can be a string of 1 to 64 characters. The value must start with
            either uppercase letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    prefixType:
        description:
            - Specifies the type of the IPv6 prefix pool to be created. The value can be a string of local or delegation or remote or dynamic1.
        required: true
        default: local
        choices: ['local', 'delegation','remote','dynamic']
    operation:
        description:
            -  Manage the state of the resource.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: brasipv6addrmng module prefixName and prefixType rule rule configuration test.
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

  - name:Create a brasipv6addrmng module prefixName and prefixType rule config
    ne_brasipv6addrmng_prefixNameType_config:
    prefixName='v_ffff_2000_52_pool',
    prefixType='delegation'
    operation='create'
    provider="{{ cli }}"

  - name:Delete a brasipv6addrmng module prefixName and prefixType rule config
    ne_brasipv6addrmng_prefixNameType_config:
    prefixName='v_ffff_2000_52_pool',
    prefixType='delegation'
    operation='delete'
    provider="{{ cli }}"

  - name:Merge a brasipv6addrmng module prefixName and prefixType rule config
    ne_brasipv6addrmng_prefixNameType_config:
    prefixName='v_ffff_2000_52_pool',
    prefixType='delegation'
    operation='merge'
    provider="{{ cli }}"

  - name:Merge a brasipv6addrmng module prefixName and prefixType rule config
    ne_brasipv6addrmng_prefixNameType_config:
    prefixName='v_ffff_2000_52_pool',
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
        "operation": "create",
        "prefixName": "v_ffff_2000_53_pool",
        "prefixType": "delegation"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
           "ipv6Prefixs": [
            {
                "prefixName": "liushuai",
                "prefixType": "local"
            },
            {
                "prefixName": "prefix1",
                "prefixType": "local"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
         "ipv6Prefixs": [
            {
                "prefixName": "liushuai",
                "prefixType": "local"
            },
            {
                "prefixName": "prefix1",
                "prefixType": "local"
            }
        ]
    }
'''
logging.basicConfig(filename='example.log', level=logging.DEBUG)
PREFIXNAMETYPE_HEAD = """
    <config>
      <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
        <ipv6Prefixs>
"""

PREFIXNAMETYPE_TAIL = """
           </ipv6Prefixs>
      </brasipv6addrmng>
    </config>
"""

PREFIXNAMETYPE_GETHEAD = """
     <filter type="subtree">
    <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
      <ipv6Prefixs>
        <ipv6Prefix>
          <prefixName/>
          <prefixType/>
        </ipv6Prefix>
      </ipv6Prefixs>
    </brasipv6addrmng>
  </filter>
"""
PREFIXNAMETYPE_GETHEADGET = """
    <filter type="subtree">
    <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
      <ipv6Prefixs>
        <ipv6Prefix>
"""
PREFIXNAMETYPE_GETTAILGET = """
       </ipv6Prefix>
      </ipv6Prefixs>
    </brasipv6addrmng>
  </filter>
"""
REMOTEBACKUPSEVICENAME = """
      <remoteBackupServiceName>%s</remoteBackupServiceName>
"""

PREFIXNAMETYPE_CREATE = """
       <ipv6Prefix nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

PREFIXNAMETYPE_DELETE = """
       <ipv6Prefix nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

PREFIXNAMETYPE_MERGE = """
     <ipv6Prefix nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""
PREFIXNAME = """
      <prefixName>%s</prefixName>
"""

PREFIXTYPE = """
      <prefixType>%s</prefixType>
"""

IPV6PREFIXEND = """
       </ipv6Prefix>
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
        self.prefixName = self.module.params['prefixName']
        self.prefixType = self.module.params['prefixType']
        self.operation = self.module.params['operation']

        if self.operation != 'get' and self.prefixType is None:
            self.prefixType = 'local'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.prefixName is not None:
            self.proposed["prefixName"] = self.prefixName
        if self.prefixType is not None:
            self.proposed["prefixType"] = self.prefixType
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
        self.changed = True
        cfg_str += PREFIXNAMETYPE_HEAD
        if self.operation == 'create':
            cfg_str += PREFIXNAMETYPE_CREATE
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            if self.prefixType:
                cfg_str += PREFIXTYPE % self.prefixType
            cfg_str += IPV6PREFIXEND

        if self.operation == 'delete':
            cfg_str += PREFIXNAMETYPE_DELETE
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            if self.prefixType:
                cfg_str += PREFIXTYPE % self.prefixType
            cfg_str += IPV6PREFIXEND

        if self.operation == 'merge':
            cfg_str += PREFIXNAMETYPE_MERGE
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            if self.prefixType:
                cfg_str += PREFIXTYPE % self.prefixType
            cfg_str += IPV6PREFIXEND

        cfg_str += PREFIXNAMETYPE_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        if self.operation != 'get':
            cfg_str += PREFIXNAMETYPE_GETHEAD
        if self.operation == 'get':
            cfg_str += PREFIXNAMETYPE_GETHEADGET
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            if self.prefixType:
                cfg_str += PREFIXTYPE % self.prefixType
            cfg_str += PREFIXNAMETYPE_GETTAILGET
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
        service_container_attributes_Info = root.findall(
            "brasipv6addrmng/ipv6Prefixs/ipv6Prefix")
        attributes_Info["ipv6Prefixs"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["prefixName", "prefixType"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                attributes_Info["ipv6Prefixs"].append(service_container_Table)

        if len(attributes_Info["ipv6Prefixs"]) == 0:
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
        prefixName=dict(required=False, type='str'),
        prefixType=dict(
            required=False,
            choices=[
                'local',
                'delegation',
                'remote',
                'dynamic']),
        operation=dict(
            required=False,
            choices=[
                'create',
                'delete',
                'merge',
                'get'],
            default='create'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
