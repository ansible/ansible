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
module: ne_brasusermng_basserviceidentifypolicy_config
version_added: "2.6"
short_description: Manage brasusermng module basserviceidentifypolicy config rule configuration.
description:
    - Manage brasusermng module basserviceidentifypolicy config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    interfaceName:
        description:
            - Specifies an interface name. The value can be a string of 1 to 64 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    servicePolicyName:
        description:
            - servicePolicyName. The value can be a string of 1 to 32 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    operation:
        description:
            -  Manage the state of the resource.
               if operation is get,the servicePolicyName cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasusermng module basserviceidentifypolicy config rule configuration.
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

  - name:create a brasusermng module basserviceidentifypolicy config rule
    ne_brasusermng_basserviceidentifypolicy_config:
    interfaceName='Eth-Trank1.20'
    servicePolicyName='test'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasusermng module basserviceidentifypolicy config rule
    ne_brasusermng_basserviceidentifypolicy_config:
    interfaceName='Eth-Trank1.20'
    servicePolicyName='test'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasusermng module basserviceidentifypolicy config rule
    ne_brasusermng_basserviceidentifypolicy_config:
    interfaceName='Eth-Trank1.20'
    servicePolicyName='test'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasusermng module basserviceidentifypolicy config rule
    ne_brasusermng_basserviceidentifypolicy_config:
    interfaceName='Eth-Trank1.20'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasusermng module basserviceidentifypolicy config rule
    ne_brasusermng_basserviceidentifypolicy_config:
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
          "operation": "merge",
          "servicePolicyName": "test"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "basServiceIdentifyPolicys": [
            {
                "interfaceName": "Eth-Trunk1.20",
                "servicePolicyName": "test"
            }
        ]

    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "basServiceIdentifyPolicys": [
            {
                "interfaceName": "Eth-Trunk1.20",
                "servicePolicyName": "test"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
BASSERVICEIDENTIFYPOLICY_HEAD = """
    <config>
      <brasusermng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasusermng">
        <interfaceNetconfs>
          <interfaceNetconf>
"""

BASSERVICEIDENTIFYPOLICY_TAIL = """
                      </interfaceNetconf>
        </interfaceNetconfs>
      </brasusermng>
    </config>
"""

BASSERVICEIDENTIFYPOLICY_GETHEAD = """
    <filter type="subtree">
     <brasusermng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasusermng">
       <interfaceNetconfs>
         <interfaceNetconf>
"""
BASSERVICEIDENTIFYPOLICY_GETTAIL = """
            </interfaceNetconf>
        </interfaceNetconfs>
    </brasusermng>
  </filter>
"""

BASSERVICEIDENTIFYPOLICY_CREATE = """
        <basServiceIdentifyPolicy nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

BASSERVICEIDENTIFYPOLICY_DELETE = """
        <basServiceIdentifyPolicy nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

BASSERVICEIDENTIFYPOLICY_MERGE = """
        <basServiceIdentifyPolicy nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

INTERFACENAME = """
      <interfaceName>%s</interfaceName>
"""

SERVICEPOLICYNAME = """
        <servicePolicyName>%s</servicePolicyName>
"""

BASSERVICEIDENTIFYPOLICYBEG = """
  <basServiceIdentifyPolicy>
"""

BASSERVICEIDENTIFYPOLICYEND = """
  </basServiceIdentifyPolicy>
"""


SERVICEPOLICYNAMESTR = """
    <servicePolicyName/>
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
        self.servicePolicyName = self.module.params['servicePolicyName']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.interfaceName is not None:
            self.proposed["interfaceName"] = self.interfaceName
        if self.servicePolicyName is not None:
            self.proposed["servicePolicyName"] = self.servicePolicyName
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
        cfg_str += BASSERVICEIDENTIFYPOLICY_HEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.operation == 'create':
            cfg_str += BASSERVICEIDENTIFYPOLICY_CREATE
        if self.operation == 'delete':
            cfg_str += BASSERVICEIDENTIFYPOLICY_DELETE
        if self.operation == 'merge':
            cfg_str += BASSERVICEIDENTIFYPOLICY_MERGE
        if self.servicePolicyName:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName
        cfg_str += BASSERVICEIDENTIFYPOLICYEND
        cfg_str += BASSERVICEIDENTIFYPOLICY_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += BASSERVICEIDENTIFYPOLICY_GETHEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        cfg_str += BASSERVICEIDENTIFYPOLICYBEG
        if self.operation != 'get':
            cfg_str += SERVICEPOLICYNAMESTR
        if self.operation == 'get':
            if self.servicePolicyName:
                cfg_str += SERVICEPOLICYNAME % self.servicePolicyName
        cfg_str += BASSERVICEIDENTIFYPOLICYEND
        cfg_str += BASSERVICEIDENTIFYPOLICY_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasusermng"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasusermng/interfaceNetconfs/interfaceNetconf")
        attributes_Info["basServiceIdentifyPolicys"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["interfaceName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "basServiceIdentifyPolicy")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in ["servicePolicyName"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["basServiceIdentifyPolicys"].append(
                            service_container_Table)

        if len(attributes_Info["basServiceIdentifyPolicys"]) == 0:
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
        servicePolicyName=dict(required=False, type='str'),
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
