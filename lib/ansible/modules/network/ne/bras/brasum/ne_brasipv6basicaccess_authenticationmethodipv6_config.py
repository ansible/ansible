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
module: ne_brasipv6basicaccess_authenticationmethodipv6_config
version_added: "2.6"
short_description: Manage brasbasicaccess module authenticationmethodipv6 config rule configuration.
description:
    - Manage brasbasicaccess module authenticationmethodipv6 config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    interfaceName:
        description:
            - Specifies an interface name. The value can be a string of 1 to 64 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    ipv6BindAuthentication:
        description:
            - Indicates binding authentication. The value can be a string of false or true.
        required: false
        choices: ['true', 'flse']
    ipv6PppAuthentication:
        description:
            - Indicates PPP authentication. The value can be a string of false or true.
        required: false
        default: false
        choices: ['true', 'flse']
    ipv6Dot1xAuthentication:
        description:
            - Indicates Dot1x authentication. The value can be a string of false or true.
        required: false
        default: false
        choices: ['true', 'flse']
    ipv6FastAuthentication:
        description:
            -  Indicates fast authentication. The value can be a string of false or true.
        required: false
        choices: ['true', 'false']
    ipv6WebAuthentication:
        description:
            -  Indicates web authentication. The value can be a string of false or true..
        required: false
        choices: ['true', 'false']
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the ipv6BindAuthentication and ipv6PppAuthentication and ipv6Dot1xAuthentication and ipv6FastAuthentication and
            ipv6WebAuthentication cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: merge
        choices: ['merge','get']

'''

EXAMPLES = '''

- name: Manage brasbasicaccess module authenticationmethodipv6 config rule configuration.
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

  - name:merge a brasbasicaccess module ipv6bind config rule
    ne_brasipv6basicaccess_authenticationmethodipv6_config:
    interfaceName='Eth-Trank1.20'
    ipv6BindAuthentication='true'
    operation='merge'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module ipv6fast config rule
    ne_brasipv6basicaccess_authenticationmethodipv6_config:
    interfaceName='Eth-Trank1.20'
    ipv6FastAuthentication='true'
    operation='merge'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module ipv6web config rule
    ne_brasipv6basicaccess_authenticationmethodipv6_config:
    interfaceName='Eth-Trank1.20'
    ipv6WebAuthentication='true'
    operation='merge'
    provider="{{ cli }}"
  - name:get a brasbasicaccess module authenticationMethodIpv6 config rule
    ne_brasipv6basicaccess_authenticationmethodipv6_config:
    interfaceName='Eth-Trank1.20'
    operation='get'
    provider="{{ cli }}"
  - name:get a brasbasicaccess module authenticationMethodIpv6 config rule
    ne_brasipv6basicaccess_authenticationmethodipv6_config:
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
          "interfaceName": "Eth-Trunk1.20",
        "ipv6BindAuthentication": "false",
        "ipv6Dot1xAuthentication": "false",
        "ipv6FastAuthentication": "false",
        "ipv6PppAuthentication": "false",
        "ipv6WebAuthentication": "false",
        "operation": "get"



    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "authenticationMethodIpv6s": [
            {
                "interfaceName": "Eth-Trunk1.20",
                "ipv6BindAuthentication": "false",
                "ipv6FastAuthentication": "false",
                "ipv6PppAuthentication": "true",
                "ipv6WebAuthentication": "false"
            }
        ]

        ]



    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "authenticationMethodIpv6s": [
            {
                "interfaceName": "Eth-Trunk1.20",
                "ipv6BindAuthentication": "false",
                "ipv6FastAuthentication": "true",
                "ipv6PppAuthentication": "true",
                "ipv6WebAuthentication": "false"
            }
        ]




    }
'''


logging.basicConfig(filename='example.log', level=logging.DEBUG)
AUTHENTICATIONMETHODIPV6_HEAD = """
    <config>
      <brasipv6basicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6basicaccess">
        <interfaceNetconfs>
          <interfaceNetconf>
"""

AUTHENTICATIONMETHODIPV6_TAIL = """
                 </interfaceNetconf>
        </interfaceNetconfs>
      </brasipv6basicaccess>
    </config>
"""

AUTHENTICATIONMETHODIPV6_GETHEAD = """
     <filter type="subtree">
      <brasipv6basicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6basicaccess">
       <interfaceNetconfs>
         <interfaceNetconf>
"""

AUTHENTICATIONMETHODIPV6_GETTAIL = """
            </interfaceNetconf>
       </interfaceNetconfs>
     </brasipv6basicaccess>
  </filter>
"""
AUTHENTICATIONMETHODIPV6_CREATE = """
        <authenticationMethodIpv6 nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

AUTHENTICATIONMETHODIPV6_DELETE = """
        <authenticationMethodIpv6 nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

AUTHENTICATIONMETHODIPV6_MERGE = """
        <authenticationMethodIpv6 nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

INTERFACENAME = """
      <interfaceName>%s</interfaceName>
"""

IPV6PPPAUTHENTICATION = """
        <ipv6PppAuthentication>%s</ipv6PppAuthentication>
"""


IPV6WEBAUTHENTICATION = """
    <ipv6WebAuthentication>%s</ipv6WebAuthentication>
"""

IPV6DOT1XAUTHENTICATION = """
   <ipv6Dot1xAuthentication>%s</ipv6Dot1xAuthentication>
"""

IPV6BINDAUTHENTICATION = """
   <ipv6BindAuthentication>%s</ipv6BindAuthentication>
"""

IPV6FASTAUTHENTICATION = """
  <ipv6FastAuthentication>%s</ipv6FastAuthentication>
"""

AUTHENTICATIONMETHODIPV6BEG = """
  <authenticationMethodIpv6>
"""

AUTHENTICATIONMETHODIPV6END = """
  </authenticationMethodIpv6>
"""

IPV6PPPAUTHENTICATIONSTR = """
    <ipv6PppAuthentication/>
"""

IPV6WEBAUTHENTICATIONSTR = """
    <ipv6WebAuthentication/>
"""

IPV6FASTAUTHENTICATIONSTR = """
    <ipv6FastAuthentication/>
"""

IPV6BINDAUTHENTICATIONSTR = """
    <ipv6BindAuthentication/>
"""

IPV6DOT1XAUTHENTICATIONSTR = """
    <ipv6Dot1xAuthentication/>
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
        self.ipv6PppAuthentication = self.module.params['ipv6PppAuthentication']
        self.ipv6WebAuthentication = self.module.params['ipv6WebAuthentication']
        self.ipv6Dot1xAuthentication = self.module.params['ipv6Dot1xAuthentication']
        self.ipv6BindAuthentication = self.module.params['ipv6BindAuthentication']
        self.ipv6FastAuthentication = self.module.params['ipv6FastAuthentication']
        self.operation = self.module.params['operation']

        if self.operation != 'get' and self.ipv6PppAuthentication is None:
            self.ipv6PppAuthentication = 'false'
        if self.operation != 'get' and self.ipv6Dot1xAuthentication is None:
            self.ipv6Dot1xAuthentication = 'false'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.interfaceName is not None:
            self.proposed["interfaceName"] = self.interfaceName
        if self.ipv6PppAuthentication is not None:
            self.proposed["ipv6PppAuthentication"] = self.ipv6PppAuthentication
        if self.ipv6WebAuthentication is not None:
            self.proposed["ipv6WebAuthentication"] = self.ipv6WebAuthentication
        if self.ipv6Dot1xAuthentication is not None:
            self.proposed["ipv6Dot1xAuthentication"] = self.ipv6Dot1xAuthentication
        if self.ipv6BindAuthentication is not None:
            self.proposed["ipv6BindAuthentication"] = self.ipv6BindAuthentication
        if self.ipv6FastAuthentication is not None:
            self.proposed["ipv6FastAuthentication"] = self.ipv6FastAuthentication
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
        cfg_str += AUTHENTICATIONMETHODIPV6_HEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.operation == 'create':
            cfg_str += AUTHENTICATIONMETHODIPV6_CREATE
        if self.operation == 'delete':
            cfg_str += AUTHENTICATIONMETHODIPV6_DELETE
        if self.operation == 'merge':
            cfg_str += AUTHENTICATIONMETHODIPV6_MERGE
        if self.ipv6PppAuthentication:
            cfg_str += IPV6PPPAUTHENTICATION % self.ipv6PppAuthentication
        if self.ipv6WebAuthentication:
            cfg_str += IPV6WEBAUTHENTICATION % self.ipv6WebAuthentication
        if self.ipv6Dot1xAuthentication:
            cfg_str += IPV6DOT1XAUTHENTICATION % self.ipv6Dot1xAuthentication
        if self.ipv6BindAuthentication:
            cfg_str += IPV6BINDAUTHENTICATION % self.ipv6BindAuthentication
        if self.ipv6FastAuthentication:
            cfg_str += IPV6FASTAUTHENTICATION % self.ipv6FastAuthentication
        cfg_str += AUTHENTICATIONMETHODIPV6END
        cfg_str += AUTHENTICATIONMETHODIPV6_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += AUTHENTICATIONMETHODIPV6_GETHEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        cfg_str += AUTHENTICATIONMETHODIPV6BEG
        if self.operation != 'get':
            cfg_str += IPV6PPPAUTHENTICATIONSTR
            cfg_str += IPV6WEBAUTHENTICATIONSTR
            cfg_str += IPV6FASTAUTHENTICATIONSTR
            cfg_str += IPV6BINDAUTHENTICATIONSTR
            cfg_str += IPV6DOT1XAUTHENTICATIONSTR
        if self.operation == 'get':
            if self.ipv6PppAuthentication:
                cfg_str += IPV6PPPAUTHENTICATION % self.ipv6PppAuthentication
            if self.ipv6WebAuthentication:
                cfg_str += IPV6WEBAUTHENTICATION % self.ipv6WebAuthentication
            if self.ipv6Dot1xAuthentication:
                cfg_str += IPV6DOT1XAUTHENTICATION % self.ipv6Dot1xAuthentication
            if self.ipv6BindAuthentication:
                cfg_str += IPV6BINDAUTHENTICATION % self.ipv6BindAuthentication
            if self.ipv6FastAuthentication:
                cfg_str += IPV6FASTAUTHENTICATION % self.ipv6FastAuthentication
        cfg_str += AUTHENTICATIONMETHODIPV6END
        cfg_str += AUTHENTICATIONMETHODIPV6_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6basicaccess"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasipv6basicaccess/interfaceNetconfs/interfaceNetconf")
        attributes_Info["authenticationMethodIpv6s"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["interfaceName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "authenticationMethodIpv6")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "ipv6PppAuthentication", "ipv6WebAuthentication", "ipv6BindAuthentication", "ipv6FastAuthentication"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["authenticationMethodIpv6s"].append(
                            service_container_Table)

        if len(attributes_Info["authenticationMethodIpv6s"]) == 0:
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
        ipv6PppAuthentication=dict(required=False, choices=['true', 'false']),
        ipv6WebAuthentication=dict(required=False, choices=['true', 'false']),
        ipv6Dot1xAuthentication=dict(
            required=False, choices=[
                'true', 'false']),
        ipv6BindAuthentication=dict(required=False, choices=['true', 'false']),
        ipv6FastAuthentication=dict(required=False, choices=['true', 'false']),
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
