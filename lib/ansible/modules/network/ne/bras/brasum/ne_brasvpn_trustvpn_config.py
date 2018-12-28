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
module: ne_brasvpn_trustvpn_config
version_added: "2.6"
short_description: Manage brasvpn module trustvpn config rule configuration.
description:
    - Manage brasvpn module trustvpn config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    domainName:
        description:
            -  Specifies the name of a domain.The value can be a string of 1 to 64 characters.
        required: true
    trustVPNOfTheBASInterface:
        description:
            -  Configures the device to trust the VPN instance bound to the BAS interface through which Layer 2 users go online.
        required: true
        choices: ['true','false']
    trustVPNOfPoolOrPoolGroup:
        description:
            -  Configures a device to trust only the VPN instance bound to the address pool or address pool group that the
            RADIUS server uses to deliver IP addresses to Layer 2 users.
        required: true
        choices: ['true','false']
    trustVpnByFrameIPv6PoolEnable:
        description:
            -  Configures a device to trust the vpn instance that is bound to IPV6 address pool delivered by the RADIUS server.
        required: true
        choices: ['true','false']
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the trustVPNOfTheBASInterface and  trustVPNOfPoolOrPoolGroup and trustVpnByFrameIPv6PoolEnable cannot take
            parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: merge
        choices: ['merge','get']
'''

EXAMPLES = '''

- name: Manage brasvpn module trustvpn config rule configuration.
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

  - name: merge a brasvpn module  trustVPNOfTheBASInterface  config rule
    ne_brasvpn_trustvpn_config:
    domainName='cbb1'
    trustVPNOfTheBASInterface='true'
    operation='merge'
    provider: "{{ cli }}"

  - name: merge a brasvpn module  trustVPNOfPoolOrPoolGroup  config rule
    ne_brasvpn_trustvpn_config:
    domainName='cbb1'
    trustVPNOfPoolOrPoolGroup='true'
    operation='merge'
    provider: "{{ cli }}"

  - name: merge a brasvpn module  trustVpnByFrameIPv6PoolEnable  config rule
    ne_brasvpn_trustvpn_config:
    domainName='cbb1'
    trustVpnByFrameIPv6PoolEnable='true'
    operation='merge'
    provider: "{{ cli }}"

  - name: merge a brasvpn module  trustvpn  config rule
    ne_brasvpn_trustvpn_config:
    domainName='cbb1'
    trustVPNOfTheBASInterface='false'
    trustVPNOfPoolOrPoolGroup='false'
    trustVpnByFrameIPv6PoolEnable='false'
    operation='merge'
    provider: "{{ cli }}"

  - name: get a brasvpn module  trustvpn  config rule
    ne_brasvpn_trustvpn_config:
    domainName='cbb1'
    operation='get'
    provider: "{{ cli }}"

  - name: get a brasvpn module  trustvpn  config rule
    ne_brasvpn_trustvpn_config:
    operation='get'
    provider: "{{ cli }}"
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
        "domainName": "cbb1",
        "operation": "merge",
        "trustVPNOfPoolOrPoolGroup": "false",
        "trustVPNOfTheBASInterface": "false",
        "trustVpnByFrameIPv6PoolEnable": "false"


    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "trustvpns": [
            {
                "domainName": "cbb1",
                "trustVPNOfPoolOrPoolGroup": "true",
                "trustVPNOfTheBASInterface": "true",
                "trustVpnByFrameIPv6PoolEnable": "true"
            }
        ]

    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "trustvpns": [
            {
                "domainName": "cbb1",
                "trustVPNOfPoolOrPoolGroup": "false",
                "trustVPNOfTheBASInterface": "false",
                "trustVpnByFrameIPv6PoolEnable": "false"
            }
        ]

    }
'''


TRASVPN_HEAD = """
    <config>
      <brasvpn xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvpn">
        <domains>
          <domain>
"""

TRASVPN_TAIL = """
           </domain>
        </domains>
      </brasvpn>
    </config>
"""

TRASVPN_GETHEAD = """
    <filter type="subtree">
    <brasvpn xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvpn">
      <domains>
        <domain>
"""

TRASVPN_GETTAIL = """
             <trustVPNThroughWhichLayer2Users>
            <trustVPNOfTheBASInterface/>
            <trustVPNOfPoolOrPoolGroup/>
          </trustVPNThroughWhichLayer2Users>
          <trustVpnByFrameIPv6Pool>
            <trustVpnByFrameIPv6PoolEnable/>
          </trustVpnByFrameIPv6Pool>
        </domain>
      </domains>
    </brasvpn>
  </filter>
"""

TRASVPN_GETTAILGET = """
        </domain>
      </domains>
    </brasvpn>
  </filter>
"""


TRUSTVPNTHROUGHWHICHLAYER2USERSBEG = """
    <trustVPNThroughWhichLayer2Users>
"""
TRUSTVPNBYFRAMEIPV6POOLBEG = """
    <trustVpnByFrameIPv6Pool>
"""

DOMAINNAME = """
      <domainName>%s</domainName>"""


TRUSTVPNOFTHEBASINTERFACE = """
      <trustVPNOfTheBASInterface>%s</trustVPNOfTheBASInterface>"""

TRUSTVPNOFPOOLORPOOLGROUP = """
    <trustVPNOfPoolOrPoolGroup>%s</trustVPNOfPoolOrPoolGroup>
"""

TRUSTVPNBYFRAMEIPV6POOLENABLE = """
    <trustVpnByFrameIPv6PoolEnable>%s</trustVpnByFrameIPv6PoolEnable>
"""

TRUSTVPNTHROUGHWHICHLAYER2USERSEND = """
   </trustVPNThroughWhichLayer2Users>
"""

TRUSTVPNBYFRAMEIPV6POOLEND = """
   </trustVpnByFrameIPv6Pool>
"""

TRUSTVPNTHROUGHWHICHLAYER2USERS_MERGE = """
      <trustVPNThroughWhichLayer2Users nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
 """

TRUSTVPNBYFRAMEIPV6POOL_MERGE = """
       <trustVpnByFrameIPv6Pool nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
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

        # module input info
        self.domainName = self.module.params['domainName']
        self.trustVPNOfTheBASInterface = self.module.params['trustVPNOfTheBASInterface']
        self.trustVPNOfPoolOrPoolGroup = self.module.params['trustVPNOfPoolOrPoolGroup']
        self.trustVpnByFrameIPv6PoolEnable = self.module.params['trustVpnByFrameIPv6PoolEnable']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.trustVPNOfTheBASInterface is not None:
            self.proposed["trustVPNOfTheBASInterface"] = self.trustVPNOfTheBASInterface
        if self.trustVPNOfPoolOrPoolGroup is not None:
            self.proposed["trustVPNOfPoolOrPoolGroup"] = self.trustVPNOfPoolOrPoolGroup
        if self.trustVpnByFrameIPv6PoolEnable is not None:
            self.proposed["trustVpnByFrameIPv6PoolEnable"] = self.trustVpnByFrameIPv6PoolEnable
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        """get config rpc string"""
        # 第一步, 构造配置报文
        cfg_str = ''
        self.changed = True
        cfg_str += TRASVPN_HEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        if self.operation == 'merge':
            cfg_str += TRUSTVPNTHROUGHWHICHLAYER2USERS_MERGE
        if self.trustVPNOfTheBASInterface:
            cfg_str += TRUSTVPNOFTHEBASINTERFACE % self.trustVPNOfTheBASInterface
        if self.trustVPNOfPoolOrPoolGroup:
            cfg_str += TRUSTVPNOFPOOLORPOOLGROUP % self.trustVPNOfPoolOrPoolGroup
        cfg_str += TRUSTVPNTHROUGHWHICHLAYER2USERSEND
        if self.trustVpnByFrameIPv6PoolEnable:
            cfg_str += TRUSTVPNBYFRAMEIPV6POOL_MERGE
            cfg_str += TRUSTVPNBYFRAMEIPV6POOLENABLE % self.trustVpnByFrameIPv6PoolEnable
            cfg_str += TRUSTVPNBYFRAMEIPV6POOLEND
        cfg_str += TRASVPN_TAIL
        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += TRASVPN_GETHEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        if self.operation != 'get':
            cfg_str += TRASVPN_GETTAIL
        if self.operation == 'get':
            cfg_str += TRUSTVPNTHROUGHWHICHLAYER2USERSBEG
            if self.trustVPNOfTheBASInterface:
                cfg_str += TRUSTVPNOFTHEBASINTERFACE % self.trustVPNOfTheBASInterface
            if self.trustVPNOfPoolOrPoolGroup:
                cfg_str += TRUSTVPNOFPOOLORPOOLGROUP % self.trustVPNOfPoolOrPoolGroup
            cfg_str += TRUSTVPNTHROUGHWHICHLAYER2USERSEND
            cfg_str += TRUSTVPNBYFRAMEIPV6POOLBEG
            if self.trustVpnByFrameIPv6PoolEnable:
                cfg_str += TRUSTVPNBYFRAMEIPV6POOLENABLE % self.trustVpnByFrameIPv6PoolEnable
            cfg_str += TRUSTVPNBYFRAMEIPV6POOLEND
            cfg_str += TRASVPN_GETTAILGET

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)

        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvpn"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasvpn/domains/domain")
        attributes_Info["trustvpns"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["domainName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "trustVPNThroughWhichLayer2Users")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "trustVPNOfTheBASInterface", "trustVPNOfPoolOrPoolGroup"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                # attributes_Info["trustvpns"].append(service_container_Table)

                container_combine_Info2 = service_node.findall(
                    "trustVpnByFrameIPv6Pool")
                if len(container_combine_Info2) != 0:
                    for combine_node2 in container_combine_Info2:
                        for leaf_combine_Info2 in combine_node2:
                            if leaf_combine_Info2.tag in [
                                    "trustVpnByFrameIPv6PoolEnable"]:
                                service_container_Table[leaf_combine_Info2.tag] = leaf_combine_Info2.text
                attributes_Info["trustvpns"].append(service_container_Table)

        if len(attributes_Info["trustvpns"]) == 0:
            attributes_Info.clear()

        # 解析5: 返回数据
        return attributes_Info

    def run(self):
        # 第一步: 检测输入
        # self.check_params()

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
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    argument_spec = dict(
        domainName=dict(required=False, type='str'),
        trustVPNOfTheBASInterface=dict(
            required=False, choices=[
                'true', 'false']),
        trustVPNOfPoolOrPoolGroup=dict(
            required=False, choices=[
                'true', 'false']),
        trustVpnByFrameIPv6PoolEnable=dict(
            required=False, choices=['true', 'false']),
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
