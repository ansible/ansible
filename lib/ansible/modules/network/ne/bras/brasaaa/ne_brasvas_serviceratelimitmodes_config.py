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
module: ne_brasvas_serviceratelimitmodes_config
version_added: "2.6"
short_description: Configures a rate limit mode for EDSG service traffic.
description:
    - Configures a rate limit mode for EDSG service traffic.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    domainName:
        description:
            - Specifies the name of a domain. The value can be a string of 1 to 64 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    serviceFlowDirection:
        description:
            - Indicates the upstream or the downstream direction.
        required: true
        choices: ['outbound', 'inbound']
    serviceRateLimitType:
        description:
            - Sets a rate limit mode for EDSG service traffic.
        required: false
        default: car
        choices: ['car', 'userQueue']
    operation:
        description:
            - Manage the state of the resource.If operation is get,the serviceRateLimitType cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        choices: ['merge', 'get']
'''

EXAMPLES = '''

- name: Configures a rate limit mode for EDSG service traffic test
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

  - name: Merge a rate limit mode for EDSG service traffic configuration
    ne_brasvas_serviceratelimitmodes_config:
      domainName='v_dom_ispres1'
      serviceFlowDirection='inbound'
      serviceRateLimitType='userQueue'
      operation='merge'
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
        "domainName": "cbb",
        "operation": "merge",
        "serviceFlowDirection": "inbound",
        "serviceRateLimitType": "userQueue"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "domainNames": [
            {
                "domainName": "cbb",
                "serviceFlowDirection": "outbound",
                "serviceRateLimitType": "userQueue"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "domainNames": [
            {
                "domainName": "cbb",
                "serviceFlowDirection": "inbound",
                "serviceRateLimitType": "userQueue"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)

SERVICERATELIMITMODE_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <domains>
          <domain>
"""

SERVICERATELIMITMODE_TAIL = """
              </serviceRateLimitMode>
            </serviceRateLimitModes>
          </domain>
        </domains>
      </brasvas>
    </config>
"""

DOMAINNAME = """
      <domainName>%s</domainName>"""

SERVICERATELIMITMODES = """
      <serviceRateLimitModes>"""

SERVICEFLOWDIRECTION = """
      <serviceFlowDirection>%s</serviceFlowDirection>"""

SERVICERATELIMITTYPE = """
      <serviceRateLimitType>%s</serviceRateLimitType>"""

SERVICERATELIMITMODE_MERGE = """
      <serviceRateLimitMode nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DOMAIN_GET_HEAD = """
      <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <domains>
        <domain>"""

DOMAIN_GET_TAIL = """
          </serviceRateLimitMode>
          </serviceRateLimitModes>
        </domain>
      </domains>
    </brasvas>
  </filter>"""

RATELIMITANDSTATICMODE_GET = """
      <rateLimitAndStaticMode/>"""

SERVICERATELIMITMODE_GET = """
      <serviceRateLimitMode>"""

SERVICEFLOWDIRECTION_GET = """
      <serviceFlowDirection/>"""

SERVICERATELIMITTYPE_GET = """
      <serviceRateLimitType/>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.domainName = self.module.params['domainName']
        self.serviceFlowDirection = self.module.params['serviceFlowDirection']
        self.serviceRateLimitType = self.module.params['serviceRateLimitType']
        self.operation = self.module.params['operation']

        if self.serviceRateLimitType is None and self.operation != 'get':
            self.serviceRateLimitType = 'car'

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.serviceFlowDirection is not None:
            self.proposed["serviceFlowDirection"] = self.serviceFlowDirection
        if self.serviceRateLimitType is not None:
            self.proposed["serviceRateLimitType"] = self.serviceRateLimitType
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        self.changed = True
        cfg_str = ''
        if self.operation == 'merge':
            cfg_str += SERVICERATELIMITMODE_HEAD
            if self.domainName:
                cfg_str += DOMAINNAME % self.domainName
            cfg_str += SERVICERATELIMITMODES
            cfg_str += SERVICERATELIMITMODE_MERGE
            if self.serviceFlowDirection:
                cfg_str += SERVICEFLOWDIRECTION % self.serviceFlowDirection
            if self.serviceRateLimitType:
                cfg_str += SERVICERATELIMITTYPE % self.serviceRateLimitType
            cfg_str += SERVICERATELIMITMODE_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += DOMAIN_GET_HEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        cfg_str += SERVICERATELIMITMODES
        cfg_str += SERVICERATELIMITMODE_GET
        if self.operation == 'get':
            if self.serviceFlowDirection:
                cfg_str += SERVICEFLOWDIRECTION % self.serviceFlowDirection
            if self.serviceRateLimitType:
                cfg_str += SERVICERATELIMITTYPE % self.serviceRateLimitType
        if self.operation != 'get':
            cfg_str += SERVICEFLOWDIRECTION_GET
            cfg_str += SERVICERATELIMITTYPE_GET
        cfg_str += DOMAIN_GET_TAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall("brasvas/domains/domain")
        attributes_Info["domainNames"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["domainName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "serviceRateLimitModes/serviceRateLimitMode")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in [
                                    "serviceFlowDirection", "serviceRateLimitType"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["domainNames"].append(
                            container_2_info_Table)

        if len(attributes_Info["domainNames"]) == 0:
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
    argument_spec = dict(
        domainName=dict(required=False, type='str'),
        serviceFlowDirection=dict(
            required=False, choices=[
                'outbound', 'inbound']),
        serviceRateLimitType=dict(
            required=False, choices=[
                'car', 'userQueue']),
        operation=dict(required=False, choices=['merge', 'get']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
