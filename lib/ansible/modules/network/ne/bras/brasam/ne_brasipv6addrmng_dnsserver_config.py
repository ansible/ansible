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
module: ne_brasipv6addrmng_dnsserver_config
version_added: "2.6"
short_description: Specifies the IPv6 address of a DNS server.
description:
    - Specifies the IPv6 address of a DNS server.
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
    dnsServerAddress:
        description:
            - Specifies the IPv6 address of a DNS server.
        required: false
    dnsServerAddress2:
        description:
            - Specifies the IPv6 address2 of a DNS server.
        required: false
    poolNameOperation:
        description:
            - Manage the state of the resource.If poolNameOperation is get,the poolType and ruiType and dnsServerAddress and dnsServerAddress2
            cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        choices: ['create', 'merge', 'delete', 'get']
    dnsServerAddressOperation:
        description:
            - Manage the state of the resource.
        required: false
        choices: ['create', 'merge', 'delete']
'''

EXAMPLES = '''

- name: Manage the IPv6 address of a DNS server test
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

  - name: Create a IPV6 address pool configuration instance and a dnsServerAddress and a dnsServerAddress2
    ne_brasipv6addrmng_dnsserver_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      dnsServerAddress='2001:918:FFFF:10::56'
      dnsServerAddress2='2001:918:FFFF:10::51'
      poolNameOperation='create'
      dnsServerAddressOperation='create'
      provider="{{ cli }}"

  - name: Merge and delete the DNS server
    ne_brasipv6addrmng_dnsserver_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      dnsServerAddress='2001:918:FFFF:10::56'
      dnsServerAddress2='2001:918:FFFF:10::51'
      poolNameOperation='merge'
      dnsServerAddressOperation='delete'
      provider="{{ cli }}"

  - name: Merge and create a DNS server
    ne_brasipv6addrmng_dnsserver_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      dnsServerAddress='2001:918:FFFF:10::52'
      dnsServerAddress2='2001:918:FFFF:10::51'
      poolNameOperation='merge'
      dnsServerAddressOperation='create'
      provider="{{ cli }}"

  - name: Merge and merge a new DNS server
    ne_brasipv6addrmng_dnsserver_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      dnsServerAddress='2001:918:FFFF:10::53'
      dnsServerAddress2='2001:918:FFFF:10::52'
      poolNameOperation='merge'
      dnsServerAddressOperation='merge'
      provider="{{ cli }}"

  - name: Delete the IPV6 address pool configuration instance and the the IPv6 address of a DNS server
    ne_brasipv6addrmng_dnsserver_config:
      poolName='cbb'
      poolType='local'
      ruiType='true'
      dnsServerAddress='2001:918:FFFF:10::53'
      dnsServerAddress2='2001:918:FFFF:10::52'
      poolNameOperation='delete'
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
        "dnsServerAddress": "2001:918:FFFF:10::57",
        "dnsServerAddress2": "2001:918:FFFF:10::58",
        "poolNameOperation": "merge",
        "dnsServerAddressOperation": "merge",
        "poolName": "cbb",
        "poolType": "delegation",
        "ruiType": "true"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "poolNames": [
            {
                "dnsServerAddress": "2001:918:FFFF:10::54",
                "dnsServerAddress2": "2001:918:FFFF:10::53",
                "poolName": "cbb",
                "poolType": "delegation",
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
                "dnsServerAddress": "2001:918:FFFF:10::57",
                "dnsServerAddress2": "2001:918:FFFF:10::58",
                "poolName": "cbb",
                "poolType": "delegation",
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
          </dnsServer>
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
          </dnsServer>
        </ipv6Pool>
      </ipv6Pools>
    </brasipv6addrmng>
  </filter>
"""

POOLTYPE_GET = """
      <poolType/>"""

RUITYPE_GET = """
      <ruiType/>"""

DNSSERVERADDRESS_GET = """
      <dnsServerAddress/>"""

DNSSERVERADDRESS2_GET = """
      <dnsServerAddress2/>"""

POOLNAME = """
      <poolName>%s</poolName>
"""

POOLTYPE = """
      <poolType>%s</poolType>
"""

RUITYPE = """
      <ruiType>%s</ruiType>"""

DNSSEARCHLIST = """
      <dnsSearchList>%s</dnsSearchList>"""

DNSSERVERADDRESS = """
      <dnsServerAddress>%s</dnsServerAddress>"""

DNSSERVERADDRESS2 = """
      <dnsServerAddress2>%s</dnsServerAddress2>"""

DNSSERVER = """
      <dnsServer>"""

IPV6POOL_CREATE = """
     <ipv6Pool nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

IPV6POOL_DELETE = """
      <ipv6Pool nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

IPV6POOL_MERGE = """
      <ipv6Pool nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DNSSERVER_CREATE = """
      <dnsServer nc:operation="create">"""

DNSSERVER_MERGE = """
      <dnsServer nc:operation="merge">"""

DNSSERVER_DELETE = """
      <dnsServer nc:operation="delete">"""


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
        self.dnsServerAddress = self.module.params['dnsServerAddress']
        self.dnsServerAddress2 = self.module.params['dnsServerAddress2']
        self.poolNameOperation = self.module.params['poolNameOperation']
        self.dnsServerAddressOperation = self.module.params['dnsServerAddressOperation']

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
        if self.dnsServerAddress is not None:
            self.proposed["dnsServerAddress"] = self.dnsServerAddress
        if self.dnsServerAddress2 is not None:
            self.proposed["dnsServerAddress2"] = self.dnsServerAddress2
        if self.poolNameOperation is not None:
            self.proposed["poolNameOperation"] = self.poolNameOperation
        if self.dnsServerAddressOperation is not None:
            self.proposed["dnsServerAddressOperation"] = self.dnsServerAddressOperation

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
            if self.dnsServerAddressOperation == 'create':
                cfg_str += DNSSERVER_CREATE
            if self.dnsServerAddress:
                cfg_str += DNSSERVERADDRESS % self.dnsServerAddress
            if self.dnsServerAddress2:
                cfg_str += DNSSERVERADDRESS2 % self.dnsServerAddress2

        if self.poolNameOperation == 'delete':
            cfg_str += IPV6POOL_DELETE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            cfg_str += DNSSERVER
            if self.dnsServerAddress:
                cfg_str += DNSSERVERADDRESS % self.dnsServerAddress
            if self.dnsServerAddress2:
                cfg_str += DNSSERVERADDRESS2 % self.dnsServerAddress2

        if self.poolNameOperation == 'merge':
            cfg_str += IPV6POOL_MERGE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.poolType:
                cfg_str += POOLTYPE % self.poolType
            if self.ruiType:
                cfg_str += RUITYPE % self.ruiType
            if self.dnsServerAddressOperation == 'create':
                cfg_str += DNSSERVER_CREATE
            elif self.dnsServerAddressOperation == 'merge':
                cfg_str += DNSSERVER_MERGE
            elif self.dnsServerAddressOperation == 'delete':
                cfg_str += DNSSERVER_DELETE
            else:
                cfg_str += DNSSERVER
            if self.dnsServerAddress:
                cfg_str += DNSSERVERADDRESS % self.dnsServerAddress
            if self.dnsServerAddress2:
                cfg_str += DNSSERVERADDRESS2 % self.dnsServerAddress2

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
            cfg_str += DNSSERVER
            if self.dnsServerAddress:
                cfg_str += DNSSERVERADDRESS % self.dnsServerAddress
            if self.dnsServerAddress2:
                cfg_str += DNSSERVERADDRESS2 % self.dnsServerAddress2
        if self.poolNameOperation != 'get':
            cfg_str += POOLTYPE_GET
            cfg_str += RUITYPE_GET
            cfg_str += DNSSERVER
            cfg_str += DNSSERVERADDRESS_GET
            cfg_str += DNSSERVERADDRESS2_GET
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
                    "dnsServer")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in [
                                    "dnsServerAddress", "dnsServerAddress2"]:
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
        dnsServerAddress=dict(required=False, type='str'),
        dnsServerAddress2=dict(required=False, type='str'),
        poolNameOperation=dict(
            required=False,
            choices=[
                'merge',
                'create',
                'delete',
                'get'],
            default='merge'),
        dnsServerAddressOperation=dict(
            required=False, choices=[
                'merge', 'create', 'delete']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
