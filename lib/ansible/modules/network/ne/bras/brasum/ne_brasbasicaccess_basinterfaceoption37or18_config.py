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
module: ne_brasbasicaccess_basinterfaceoption37or18_config
version_added: "2.6"
short_description: Manage brasbasicaccess module option37 or option18 config rule configuration.
description:
    - Manage brasbasicaccess module option37 or option18 config rule configuration.
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
        default: true
        choices: ['true', 'flse']
    option18Enable:
        description:
            - Enables the server to trust the information in the Option 18 field of DHCPv6 messages sent by the client.
            The value can be a string of false or true.
        required: true
        choices: ['true', 'false']
    option37Enable:
        description:
            - The client-option37 command enables the NE40E to trust the information in the Option 37 field of DHCPv6 messages sent by the client.
            The value can be a string of false or true.
        required: true
        choices: ['true', 'false']
    basinfoInsert:
        description:
            - Encapsulates Option 37 information into a DHCP packet in ft telecom format. The value can be a string of false or true.
        required: true
        choices: ['true', 'false']
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the basEnable and option18Enable and option37Enable and basinfoInsert cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasbasicaccess module option37 or option18 config rule configuration.
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

  - name:create a brasbasicaccess module option60Orvendor config rule
    ne_brasbasicaccess_basinterfaceoption37or18_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    option18Enable='true'
    basinfoInsert='true'
    option37Enable='true'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module option60Orvendor config rule
    ne_brasbasicaccess_basinterfaceoption37or18_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    option18Enable='true'
    basinfoInsert='true'
    option37Enable='true'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module option60Orvendor config rule
    ne_brasbasicaccess_basinterfaceoption37or18_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    option18Enable='true'
    basinfoInsert='true'
    option37Enable='true'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module option60Orvendor config rule
    ne_brasbasicaccess_basinterfaceoption37or18_config:
    interfaceName='Eth-Trank1.20'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module option60Orvendor config rule
    ne_brasbasicaccess_basinterfaceoption37or18_config:
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
         "basEnable": "true",
         "basinfoInsert": "false",
         "interfaceName": "Eth-Trunk1.20",
         "operation": "merge",
         "option18Enable": "false",
         "option37Enable": "false"



    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
          "option18AndOption37s": [
            {
                "basinfoInsert": "false",
                "interfaceName": "Eth-Trunk1.20",
                "option18Enable": "true",
                "option37Enable": "true"
            }
        ]




    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "option18AndOption37s": [
            {
                "interfaceName": "Eth-Trunk1.20",
                "option18Enable": "false"
            }
        ]




    }
'''


logging.basicConfig(filename='example.log', level=logging.DEBUG)

BASINTERFACEOPTION37OR18_HEAD = """
    <config>
      <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
        <basInterfaces>
          <basInterface>
"""

BASINTERFACEOPTION37OR18_TAIL = """
                 </basInterface>
        </basInterfaces>
      </brasbasicaccess>
    </config>
"""

BASINTERFACEOPTION37OR18_GETHEAD = """
    <filter type="subtree">
     <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
       <basInterfaces>
        <basInterface>
"""

BASINTERFACEOPTION37OR18_GETTAIL = """
         </basInterface>
       </basInterfaces>
    </brasbasicaccess>
  </filter>
"""

OPTION18ANDOPTION37_CREATE = """
        <option18AndOption37 nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

OPTION18ANDOPTION37_DELETE = """
         <option18AndOption37 nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

OPTION18ANDOPTION37_MERGE = """
        <option18AndOption37 nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

INTERFACENAME = """
      <interfaceName>%s</interfaceName>
"""

BASENABLE = """
       <basEnable>%s</basEnable>
"""


OPTION18ENABLE = """
    <option18Enable>%s</option18Enable>
"""

BASINFOINSERT = """
   <basinfoInsert>%s</basinfoInsert>
"""

OPTION37ENABLE = """
   <option37Enable>%s</option37Enable>
"""

OPTION18ANDOPTION37BEG = """
   <option18AndOption37>
"""

OPTION18ANDOPTION37END = """
   </option18AndOption37>
"""

OPTION18ENABLESTR = """
     <option18Enable/>
"""

OPTION37ENABLESTR = """
     <option37Enable/>
"""

BASINFOINSERTSTR = """
    <basinfoInsert/>
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
        self.option18Enable = self.module.params['option18Enable']
        self.basinfoInsert = self.module.params['basinfoInsert']
        self.option37Enable = self.module.params['option37Enable']
        self.operation = self.module.params['operation']

        if self.operation != 'get' and self.basEnable is None:
            self.basEnable = 'true'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.interfaceName is not None:
            self.proposed["interfaceName"] = self.interfaceName
        if self.basEnable is not None:
            self.proposed["basEnable"] = self.basEnable
        if self.option18Enable is not None:
            self.proposed["option18Enable"] = self.option18Enable
        if self.basinfoInsert is not None:
            self.proposed["basinfoInsert"] = self.basinfoInsert
        if self.option37Enable is not None:
            self.proposed["option37Enable"] = self.option37Enable
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
        cfg_str += BASINTERFACEOPTION37OR18_HEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.basEnable:
            cfg_str += BASENABLE % self.basEnable
        if self.operation == 'create':
            cfg_str += OPTION18ANDOPTION37_CREATE
        if self.operation == 'delete':
            cfg_str += OPTION18ANDOPTION37_DELETE
        if self.operation == 'merge':
            cfg_str += OPTION18ANDOPTION37_MERGE
        if self.option18Enable:
            cfg_str += OPTION18ENABLE % self.option18Enable
        if self.basinfoInsert:
            cfg_str += BASINFOINSERT % self.basinfoInsert
        if self.option37Enable:
            cfg_str += OPTION37ENABLE % self.option37Enable
        cfg_str += OPTION18ANDOPTION37END
        cfg_str += BASINTERFACEOPTION37OR18_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += BASINTERFACEOPTION37OR18_GETHEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.operation != 'get':
            cfg_str += OPTION18ANDOPTION37BEG
            cfg_str += OPTION18ENABLESTR
            cfg_str += BASINFOINSERTSTR
            cfg_str += OPTION37ENABLESTR
        if self.operation == 'get':
            if self.basEnable:
                cfg_str += BASENABLE % self.basEnable
            cfg_str += OPTION18ANDOPTION37BEG
            if self.option18Enable:
                cfg_str += OPTION18ENABLE % self.option18Enable
            if self.basinfoInsert:
                cfg_str += BASINFOINSERT % self.basinfoInsert
            if self.option37Enable:
                cfg_str += OPTION37ENABLE % self.option37Enable
        cfg_str += OPTION18ANDOPTION37END
        cfg_str += BASINTERFACEOPTION37OR18_GETTAIL

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
        attributes_Info["option18AndOption37s"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["interfaceName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "option18AndOption37")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "option18Enable", "basinfoInsert", "option37Enable"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["option18AndOption37s"].append(
                            service_container_Table)

        if len(attributes_Info["option18AndOption37s"]) == 0:
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
        option18Enable=dict(required=False, choices=['true', 'false']),
        basinfoInsert=dict(required=False, choices=['true', 'false']),
        option37Enable=dict(required=False, choices=['true', 'false']),
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
