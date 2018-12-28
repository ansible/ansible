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
module: ne_brasbasicaccess_basInterfaceBasic_config
version_added: "2.6"
short_description: Manage brasbasicaccess module basinterfacebasic config rule configuration.
description:
    - Manage brasbasicaccess module basinterfacebasic config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    interfaceName:
        description:
            - Specifies an interface name. The value can be a string of 1 to 64 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    basEnable:
        description:
            - Create a BAS interface or displays the BAS interface view. The value can be a string of true or false.
        required: false
        default: false
        choices: ['true', 'flse']
    accessType:
        description:
            - accessType. The value can be a string of none or layer2-subscriber or layer3-subscriber or layer2-leased-line or layer3-leased-line.
        required: true
        choices: ['none', 'layer2-subscriber','layer3-subscriber','layer2-leased-line','layer3-leased-line']
    defaultDomainName:
        description:
            -  defDomainName. The value can be a string of 1 to 64 characters. The value must start with either uppercase letters A to Z or lowercase
            letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    basInterfaceName:
        description:
            - basIntfName. The value can be a string of 1 to 32 characters. The value must start with either uppercase letters A to Z or lowercase
            letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    radiusServerName:
        description:
            - rdName. The value can be a string of 1 to 32 characters. The value must start with either uppercase letters A to Z or lowercase
            letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    preDomainName:
        description:
            - preDomainName. The value can be a string of 1 to 64 characters. The value must start with either uppercase letters A to Z or lowercase
            letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    defaultDomainType:
        description:
            - defaultDomainType. The value can be a string of none or force or replace.
        required: true
        choices: ['none', 'force','replace']
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the basEnable and accessType and defaultDomainName and basInterfaceName and radiusServerName and preDomainName and
            defaultDomainType cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasbasicaccess module basinterfacebasic config rule configuration.
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

  - name:create a brasbasicaccess module radius-server config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    radiusServerName='radius-server1'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module radius-server config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    radiusServerName='radius-server1'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module radius-server config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    radiusServerName='radius-server1'
    operation='merge'
    provider="{{ cli }}"

  - name:create a brasbasicaccess module bas-interface-name config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    basInterfaceName='huawei123'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module bas-interface-name config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    basInterfaceName='huawei123'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module bas-interface-name config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    basInterfaceName='huawei123'
    operation='merge'
    provider="{{ cli }}"

  - name:create a brasbasicaccess module default-domain pre-authentication config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    preDomainName='abc'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module default-domain pre-authentication config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    preDomainName='abc'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module default-domain pre-authentication config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    preDomainName='abc'
    operation='merge'
    provider="{{ cli }}"

  - name:create a brasbasicaccess module default-domain defaultDomainType config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    defaultDomainType='force'
    defaultDomainName='abc'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module default-domain defaultDomainType config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    defaultDomainType='force'
    defaultDomainName='abc'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module default-domain defaultDomainType config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    accessType='layer2-subscriber'
    defaultDomainType='force'
    defaultDomainName='abc'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module basinterfacebasic config rule
    ne_brasbasicaccess_basinterfacebasic_config:
    interfaceName='Eth-Trank1.20'
    operation='get'
    provider="{{ cli }}"
  - name:get a brasbasicaccess module basinterfacebasic config rule
    ne_brasbasicaccess_basinterfacebasic_config:
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
         "accessType": "layer2-subscriber",
         "basEnable": "true",
         "defaultDomainName": "abc",
         "defaultDomainType": "force",
         "interfaceName": "Eth-Trunk1.20",
         "operation": "merge"


    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "basBasicAccesss": [
            {
                "accessType": "none",
                "interfaceName": "Eth-Trunk1.20"
            }
        ]


    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "basBasicAccesss": [
            {
                "accessType": "layer2-subscriber",
                "defaultDomainName": "abc",
                "defaultDomainType": "force",
                "interfaceName": "Eth-Trunk1.20"
            }
        ]


    }
'''


logging.basicConfig(filename='example.log', level=logging.DEBUG)
BASINTERFACEBASIC_HEAD = """
    <config>
      <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
        <basInterfaces>
          <basInterface>
"""

BASINTERFACEBASIC_TAIL = """
                 </basInterface>
        </basInterfaces>
      </brasbasicaccess>
    </config>
"""

BASINTERFACEBASIC_GETHEAD = """
    <filter type="subtree">
      <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
        <basInterfaces>
          <basInterface>
"""

BASINTERFACEBASIC_GETTAIL = """
         </basInterface>
      </basInterfaces>
    </brasbasicaccess>
  </filter>
"""

BASBASICACCESS_CREATE = """
       <basBasicAccess nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

BASBASICACCESS_DELETE = """
       <basBasicAccess nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

BASBASICACCESS_MERGE = """
      <basBasicAccess nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

INTERFACENAME = """
      <interfaceName>%s</interfaceName>
"""

BASENABLE = """
       <basEnable>%s</basEnable>
"""


ACCESSTYPE = """
    <accessType>%s</accessType>
"""

DEFAULTDOMAINNAME = """
     <defaultDomainName>%s</defaultDomainName>
"""

BASINTERFACENAME = """
    <basInterfaceName>%s</basInterfaceName>
"""

RADIUSSERVERNAME = """
    <radiusServerName>%s</radiusServerName>
"""

PREDOMAINNAME = """
    <preDomainName>%s</preDomainName>
"""

DEFAULTDOMAINTYPE = """
    <defaultDomainType>%s</defaultDomainType>
"""

BASBASICACCESSBEG = """
    <basBasicAccess>
"""

BASBASICACCESSEND = """
    </basBasicAccess>
"""

ACCESSTYPESTR = """
    <accessType/>
"""

DEFAULTDOMAINNAMESTR = """
    <defaultDomainName/>
"""

BASINTERFACENAMESTR = """
    <basInterfaceName/>
"""

RADIUSSERVERNAMESTR = """
    <radiusServerName/>
"""

DEFAULTDOMAINTYPESTR = """
    <defaultDomainType/>
"""

PREDOMAINNAMESTR = """
    <preDomainName/>
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
        self.interfaceName = self.module.params['interfaceName']
        self.basEnable = self.module.params['basEnable']
        self.accessType = self.module.params['accessType']
        self.defaultDomainName = self.module.params['defaultDomainName']
        self.basInterfaceName = self.module.params['basInterfaceName']
        self.radiusServerName = self.module.params['radiusServerName']
        self.preDomainName = self.module.params['preDomainName']
        self.defaultDomainType = self.module.params['defaultDomainType']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.interfaceName is not None:
            self.proposed["interfaceName"] = self.interfaceName
        if self.basEnable is not None:
            self.proposed["basEnable"] = self.basEnable
        if self.accessType is not None:
            self.proposed["accessType"] = self.accessType
        if self.defaultDomainName is not None:
            self.proposed["defaultDomainName"] = self.defaultDomainName
        if self.basInterfaceName is not None:
            self.proposed["basInterfaceName"] = self.basInterfaceName
        if self.radiusServerName is not None:
            self.proposed["radiusServerName"] = self.radiusServerName
        if self.preDomainName is not None:
            self.proposed["preDomainName"] = self.preDomainName
        if self.defaultDomainType is not None:
            self.proposed["defaultDomainType"] = self.defaultDomainType
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
        self.changed = True
        cfg_str = ''
        cfg_str += BASINTERFACEBASIC_HEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.basEnable:
            cfg_str += BASENABLE % self.basEnable
        if self.operation == 'create':
            cfg_str += BASBASICACCESS_CREATE
        if self.operation == 'delete':
            cfg_str += BASBASICACCESS_DELETE
        if self.operation == 'merge':
            cfg_str += BASBASICACCESS_MERGE
        if self.accessType:
            cfg_str += ACCESSTYPE % self.accessType
        if self.defaultDomainName:
            cfg_str += DEFAULTDOMAINNAME % self.defaultDomainName
        if self.basInterfaceName:
            cfg_str += BASINTERFACENAME % self.basInterfaceName
        if self.radiusServerName:
            cfg_str += RADIUSSERVERNAME % self.radiusServerName
        if self.preDomainName:
            cfg_str += PREDOMAINNAME % self.preDomainName
        if self.defaultDomainType:
            cfg_str += DEFAULTDOMAINTYPE % self.defaultDomainType
        cfg_str += BASBASICACCESSEND
        cfg_str += BASINTERFACEBASIC_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += BASINTERFACEBASIC_GETHEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.operation != 'get':
            cfg_str += BASBASICACCESSBEG
            cfg_str += ACCESSTYPESTR
            cfg_str += DEFAULTDOMAINNAMESTR
            cfg_str += BASINTERFACENAMESTR
            cfg_str += RADIUSSERVERNAMESTR
            cfg_str += PREDOMAINNAMESTR
            cfg_str += DEFAULTDOMAINTYPESTR
            cfg_str += BASBASICACCESSEND
        if self.operation == 'get':
            if self.basEnable:
                cfg_str += BASENABLE % self.basEnable
            cfg_str += BASBASICACCESSBEG
            if self.accessType:
                cfg_str += ACCESSTYPE % self.accessType
            if self.defaultDomainName:
                cfg_str += DEFAULTDOMAINNAME % self.defaultDomainName
            if self.basInterfaceName:
                cfg_str += BASINTERFACENAME % self.basInterfaceName
            if self.radiusServerName:
                cfg_str += RADIUSSERVERNAME % self.radiusServerName
            if self.preDomainName:
                cfg_str += PREDOMAINNAME % self.preDomainName
            if self.defaultDomainType:
                cfg_str += DEFAULTDOMAINTYPE % self.defaultDomainType
            cfg_str += BASBASICACCESSEND
        cfg_str += BASINTERFACEBASIC_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasbasicaccess/basInterfaces/basInterface")
        attributes_Info["basBasicAccesss"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["interfaceName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall("basBasicAccess")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "accessType", "defaultDomainName", "basInterfaceName", "radiusServerName", "preDomainName", "defaultDomainType"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["basBasicAccesss"].append(
                            service_container_Table)

        if len(attributes_Info["basBasicAccesss"]) == 0:
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
        interfaceName=dict(required=False, type='str'),
        basEnable=dict(required=False, choices=['true', 'false']),
        accessType=dict(
            required=False,
            choices=[
                'none',
                'layer2-subscriber',
                'layer3-subscriber',
                'layer2-leased-line',
                'layer3-leased-line']),
        defaultDomainName=dict(required=False, type='str'),
        basInterfaceName=dict(required=False, type='str'),
        radiusServerName=dict(required=False, type='str'),
        preDomainName=dict(required=False, type='str'),
        defaultDomainType=dict(
            required=False, choices=[
                'none', 'force', 'replace']),
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
