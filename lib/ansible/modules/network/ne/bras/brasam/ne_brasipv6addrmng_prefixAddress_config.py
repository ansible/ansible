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
module: ne_brasipv6addrmng_prefixAddress_config
version_added: "2.6"
short_description: Manage brasipv6addrmng prefixAddress config rule configuration.
description:
    - Manage brasipv6addrmng prefixAddress config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    prefixName:
        description:
            - Specifies the name of the IPv6 prefix pool to be created. The value can be a string of 1 to 64 characters. The value must start with either
            uppercase letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    prefix:
        description:
            - Specifies the address and length of an IPv6 prefix. The value can be a string of 0 to 255 characters. The value must start with either
            uppercase letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    delegationPrefixLength:
        description:
            - Specifies the length of the IPv6 prefix assigned by the delegating router to the requesting router. The value can be a integer of 1 to 128.
        required: true
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the prefix and delegationPrefixLength  cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasipv6addrmng prefixAddress config rule configuration..
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

  - name:create a brasipv6addrmng module prefixAddress config rule
    ne_brasipv6addrmng_prefixAddress_config:
    prefixName='ipv6test3'
    prefix='2002:917:FFFF:2000::/53'
    delegationPrefixLength=62
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasipv6addrmng module prefixAddress config rule
    ne_brasipv6addrmng_prefixAddress_config:
    prefixName='ipv6test3'
    prefix='2002:917:FFFF:2000::/53'
    delegationPrefixLength=62
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasipv6addrmng module prefixAddress config rule
    ne_brasipv6addrmng_prefixAddress_config:
    prefixName='ipv6test3'
    prefix='2002:917:FFFF:2000::/53'
    delegationPrefixLength=62
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasipv6addrmng module prefixAddress config rule
    ne_brasipv6addrmng_prefixAddress_config:
    prefixName='ipv6test3'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasipv6addrmng module prefixAddress config rule
    ne_brasipv6addrmng_prefixAddress_config:
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
        "delegationPrefixLength": 62,
        "operation": "merge",
        "prefix": "2002:917:FFFF:2000::/53",
        "prefixName": "ipv6test3"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
           "ipv6Prefixs": [
            {
                "delegationPrefixLength": "62",
                "prefix": "2002:917:FFFF:2000::/53",
                "prefixName": "ipv6test3"
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
                "delegationPrefixLength": "62",
                "prefix": "2002:917:FFFF:2000::/53",
                "prefixName": "ipv6test3"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
PREFIXADDRESS_HEAD = """
    <config>
      <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
        <ipv6Prefixs>
          <ipv6Prefix xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

PREFIXADDRESS_TAIL = """
            </ipv6Prefix>
        </ipv6Prefixs>
      </brasipv6addrmng>
    </config>
"""

PREFIXADDRESS_GETHEAD = """
     <filter type="subtree">
       <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
         <ipv6Prefixs>
           <ipv6Prefix>
"""

PREFIXADDRESS_GETTAIL = """
         </ipv6Prefix>
      </ipv6Prefixs>
    </brasipv6addrmng>
  </filter>
"""
PREFIXADDRESS_CREATE = """
       <prefixAddress nc:operation="create">
"""

PREFIXADDRESS_DELETE = """
       <prefixAddress nc:operation="delete">
"""

PREFIXADDRESS_MERGE = """
     <prefixAddress nc:operation="merge">
"""

PREFIXNAME = """
      <prefixName>%s</prefixName>
"""

PREFIX = """
      <prefix>%s</prefix>
"""

DELEGATIONPREFIXLENGTH = """
     <delegationPrefixLength>%d</delegationPrefixLength>
"""

PREFIXADDRESSBEG = """
       <prefixAddress>
"""
PREFIXADDRESSEND = """
       </prefixAddress>
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
        self.prefix = self.module.params['prefix']
        self.delegationPrefixLength = self.module.params['delegationPrefixLength']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.prefixName is not None:
            self.proposed["prefixName"] = self.prefixName
        if self.prefix is not None:
            self.proposed["prefix"] = self.prefix
        if self.delegationPrefixLength is not None:
            self.proposed["delegationPrefixLength"] = self.delegationPrefixLength
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
        cfg_str += PREFIXADDRESS_HEAD
        if self.operation == 'create':
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            cfg_str += PREFIXADDRESS_CREATE
            if self.prefix:
                cfg_str += PREFIX % self.prefix
            if self.delegationPrefixLength:
                cfg_str += DELEGATIONPREFIXLENGTH % self.delegationPrefixLength
            cfg_str += PREFIXADDRESSEND

        if self.operation == 'delete':
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            cfg_str += PREFIXADDRESS_DELETE
            if self.prefix:
                cfg_str += PREFIX % self.prefix
            if self.delegationPrefixLength:
                cfg_str += DELEGATIONPREFIXLENGTH % self.delegationPrefixLength
            cfg_str += PREFIXADDRESSEND

        if self.operation == 'merge':
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            cfg_str += PREFIXADDRESS_MERGE
            if self.prefix:
                cfg_str += PREFIX % self.prefix
            if self.delegationPrefixLength:
                cfg_str += DELEGATIONPREFIXLENGTH % self.delegationPrefixLength
            cfg_str += PREFIXADDRESSEND

        if self.operation == 'get':
            logging.info('self.operation get test 1')
            cfg_str = ''
            cfg_str = PREFIXADDRESS_GETHEAD
        else:
            cfg_str += PREFIXADDRESS_TAIL

        # 第二步: 下发配置报文
        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += PREFIXADDRESS_GETHEAD
        if self.prefixName:
            cfg_str += PREFIXNAME % self.prefixName
        if self.operation != 'get':
            cfg_str += PREFIXADDRESSBEG
            cfg_str += PREFIXADDRESSEND
        if self.operation == 'get':
            cfg_str += PREFIXADDRESSBEG
            if self.prefix:
                cfg_str += PREFIX % self.prefix
            if self.delegationPrefixLength:
                cfg_str += DELEGATIONPREFIXLENGTH % self.delegationPrefixLength
            cfg_str += PREFIXADDRESSEND
        cfg_str += PREFIXADDRESS_GETTAIL
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
                    if leaf_service_Info.tag in ["prefixName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall("prefixAddress")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "prefix", "delegationPrefixLength"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["ipv6Prefixs"].append(
                            service_container_Table)

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
        prefix=dict(required=False, type='str'),
        delegationPrefixLength=dict(required=False, type='int'),
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
