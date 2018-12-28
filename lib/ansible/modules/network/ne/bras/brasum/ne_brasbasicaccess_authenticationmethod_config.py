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
module: ne_brasbasicaccess_authenticationmethod_config
version_added: "2.6"
short_description: Manage brasbasicaccess module authenticationmethod config rule configuration.
description:
    - Manage brasbasicaccess module authenticationmethod config rule configuration.
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
    bindAuthentication:
        description:
            - Indicates binding authentication. The value can be a string of false or true.
        required: true
        choices: ['true', 'flse']
    webAuthentication:
        description:
            - Indicates web authentication. The value can be a string of false or true.
        required: true
        choices: ['true', 'flse']
    fastAuthentication:
        description:
            - Indicates fast authentication. The value can be a string of false or true.
        required: true
        choices: ['true', 'flse']
    pppAuthentication:
        description:
            - Indicates PPP authentication. The value can be a string of false or true.
        required: true
        default: false
        choices: ['true', 'flse']
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the basEnable and bindAuthentication and webAuthentication and fastAuthentication and pppAuthentication
            cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasbasicaccess module authenticationmethod config rule configuration.
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

  - name:create a brasbasicaccess module bind config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    bindAuthentication='true'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module bind config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    bindAuthentication='true'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module bind config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    bindAuthentication='true'
    operation='merge'
    provider="{{ cli }}"

  - name:create a brasbasicaccess module fast config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    fastAuthentication='true'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module fast config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    fastAuthentication='true'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module fast config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    fastAuthentication='true'
    operation='merge'
    provider="{{ cli }}"

  - name:create a brasbasicaccess module web config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    webAuthentication='true'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module web config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    webAuthentication='true'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module web config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    basEnable='true'
    webAuthentication='true'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module authenticationMethod config rule
    ne_brasbasicaccess_authenticationmethod_config:
    interfaceName='Eth-Trank1.20'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module authenticationMethod config rule
    ne_brasbasicaccess_authenticationmethod_config:
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
         "bindAuthentication": "true",
         "fastAuthentication": "false",
         "interfaceName": "Eth-Trunk1.20",
         "operation": "merge",
         "pppAuthentication": "false",
         "webAuthentication": "false"



    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "authenticationMethods": [
            {
                "bindAuthentication": "false",
                "fastAuthentication": "false",
                "interfaceName": "Eth-Trunk1.20",
                "pppAuthentication": "true",
                "webAuthentication": "false"
            }
        ]




    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "authenticationMethods": [
            {
                "bindAuthentication": "true",
                "fastAuthentication": "false",
                "interfaceName": "Eth-Trunk1.20",
                "pppAuthentication": "false",
                "webAuthentication": "false"
            }
        ]




    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
AUTHENTICATIONMETHOD_HEAD = """
    <config>
      <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
        <basInterfaces>
          <basInterface>
"""

AUTHENTICATIONMETHOD_TAIL = """
                 </basInterface>
        </basInterfaces>
      </brasbasicaccess>
    </config>
"""

AUTHENTICATIONMETHOD_GETHEAD = """
     <filter type="subtree">
       <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
         <basInterfaces>
           <basInterface>
"""

AUTHENTICATIONMETHOD_GETTAIL = """
            </basInterface>
       </basInterfaces>
     </brasbasicaccess>
  </filter>
"""

AUTHENTICATIONMETHOD_CREATE = """
        <authenticationMethod xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
"""

AUTHENTICATIONMETHOD_DELETE = """
         <authenticationMethod xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete">
"""

AUTHENTICATIONMETHOD_MERGE = """
        <authenticationMethod xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="merge">
"""

INTERFACENAME = """
      <interfaceName>%s</interfaceName>
"""

BASENABLE = """
       <basEnable>%s</basEnable>
"""


BINDAUTHENTICATION = """
    <bindAuthentication>%s</bindAuthentication>
"""

PPPAUTHENTICATION = """
   <pppAuthentication>%s</pppAuthentication>
"""

FASTAUTHENTICATION = """
   <fastAuthentication>%s</fastAuthentication>
"""

WEBAUTHENTICATION = """
  <webAuthentication>%s</webAuthentication>
"""

AUTHENTICATIONMETHODBEG = """
  <authenticationMethod>
"""

AUTHENTICATIONMETHODEND = """
  </authenticationMethod>
"""

BINDAUTHENTICATIONSTR = """
    <bindAuthentication/>
"""

PPPAUTHENTICATIONSTR = """
    <pppAuthentication/>
"""

FASTAUTHENTICATIONSTR = """
    <fastAuthentication/>
"""

WEBAUTHENTICATIONSTR = """
    <webAuthentication/>
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
        self.bindAuthentication = self.module.params['bindAuthentication']
        self.pppAuthentication = self.module.params['pppAuthentication']
        self.fastAuthentication = self.module.params['fastAuthentication']
        self.webAuthentication = self.module.params['webAuthentication']
        self.operation = self.module.params['operation']

        if self.operation != 'get' and self.basEnable is None:
            self.basEnable = 'true'
        if self.operation != 'get' and self.pppAuthentication is None:
            self.pppAuthentication = 'false'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.interfaceName is not None:
            self.proposed["interfaceName"] = self.interfaceName
        if self.basEnable is not None:
            self.proposed["basEnable"] = self.basEnable
        if self.bindAuthentication is not None:
            self.proposed["bindAuthentication"] = self.bindAuthentication
        if self.pppAuthentication is not None:
            self.proposed["pppAuthentication"] = self.pppAuthentication
        if self.fastAuthentication is not None:
            self.proposed["fastAuthentication"] = self.fastAuthentication
        if self.webAuthentication is not None:
            self.proposed["webAuthentication"] = self.webAuthentication
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
        cfg_str += AUTHENTICATIONMETHOD_HEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.basEnable:
            cfg_str += BASENABLE % self.basEnable
        if self.operation == 'create':
            cfg_str += AUTHENTICATIONMETHOD_CREATE
        if self.operation == 'delete':
            cfg_str += AUTHENTICATIONMETHOD_DELETE
        if self.operation == 'merge':
            cfg_str += AUTHENTICATIONMETHOD_MERGE
        if self.bindAuthentication:
            cfg_str += BINDAUTHENTICATION % self.bindAuthentication
        if self.pppAuthentication:
            cfg_str += PPPAUTHENTICATION % self.pppAuthentication
        if self.fastAuthentication:
            cfg_str += FASTAUTHENTICATION % self.fastAuthentication
        if self.webAuthentication:
            cfg_str += WEBAUTHENTICATION % self.webAuthentication
        cfg_str += AUTHENTICATIONMETHODEND
        cfg_str += AUTHENTICATIONMETHOD_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += AUTHENTICATIONMETHOD_GETHEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.operation != 'get':
            cfg_str += AUTHENTICATIONMETHODBEG
            cfg_str += BINDAUTHENTICATIONSTR
            cfg_str += PPPAUTHENTICATIONSTR
            cfg_str += FASTAUTHENTICATIONSTR
            cfg_str += WEBAUTHENTICATIONSTR

        if self.operation == 'get':
            if self.basEnable:
                cfg_str += BASENABLE % self.basEnable
            cfg_str += AUTHENTICATIONMETHODBEG
            if self.bindAuthentication:
                cfg_str += BINDAUTHENTICATION % self.bindAuthentication
            if self.pppAuthentication:
                cfg_str += PPPAUTHENTICATION % self.pppAuthentication
            if self.fastAuthentication:
                cfg_str += FASTAUTHENTICATION % self.fastAuthentication
            if self.webAuthentication:
                cfg_str += WEBAUTHENTICATION % self.webAuthentication
        cfg_str += AUTHENTICATIONMETHODEND
        cfg_str += AUTHENTICATIONMETHOD_GETTAIL

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
        attributes_Info["authenticationMethods"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["interfaceName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "authenticationMethod")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "bindAuthentication", "pppAuthentication", "fastAuthentication", "webAuthentication"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["authenticationMethods"].append(
                            service_container_Table)

        if len(attributes_Info["authenticationMethods"]) == 0:
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
        bindAuthentication=dict(required=False, choices=['true', 'false']),
        pppAuthentication=dict(required=False, choices=['true', 'false']),
        fastAuthentication=dict(required=False, choices=['true', 'false']),
        webAuthentication=dict(required=False, choices=['true', 'false']),
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
