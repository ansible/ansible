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
module: ne_radius_qosprofilecasesensitive_config
version_added: "2.6"
short_description: Allows a RADIUS server to support case-sensitive RADIUS qos profile attribute.
description:
    - Allows a RADIUS server to support case-sensitive RADIUS qos profile attribute.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    groupName:
        description:
            - RADIUS server group's name. The value can be a string of 1 to 32 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    caseSensitive:
        description:
            - Config a RADIUS server to support case-sensitive RADIUS qos profile attribute.
        required: false
    groupNameOperation:
        description:
            - Manage the state of the resource.If groupNameOperation is get,the caseSensitive cannot take parameters,otherwise The echo of the command
            line is'This operation are not supported'.
        required: false
        choices: ['create', 'merge', 'delete', 'get']
    caseSensitiveOperation:
        description:
            - Manage the state of the resource.
        required: false
        choices: ['create', 'merge', 'delete']
'''

EXAMPLES = '''

- name: Config a RADIUS server to support case-sensitive RADIUS qos profile attribute test
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

  - name: Create a set of RADIUS group name configuration and case-sensitive RADIUS qos profile attribute
    ne_radius_qosprofilecasesensitive_config:
      groupName='cbb'
      caseSensitive='true'
      groupNameOperation='create'
      provider="{{ cli }}"

  - name: Merge the set of RADIUS group name configuration and delete the case-sensitive RADIUS qos profile attribute
    ne_radius_qosprofilecasesensitive_config:
      groupName='cbb'
      sourceInterfaceName='true'
      groupNameOperation='merge'
      caseSensitiveOperation='delete'
      provider="{{ cli }}"

  - name: Merge the set of RADIUS group name configuration and create a new case-sensitive RADIUS qos profile attribute
    ne_radius_qosprofilecasesensitive_config:
      groupName='cbb'
      sourceInterfaceName='true'
      groupNameOperation='merge'
      caseSensitiveOperation='create'
      provider="{{ cli }}"

  - name: Merge the set of RADIUS group name configuration and merge a new case-sensitive RADIUS qos profile attribute
    ne_radius_qosprofilecasesensitive_config:
      groupName='cbb'
      sourceInterfaceName='false'
      groupNameOperation='merge'
      caseSensitiveOperation='merge'
      provider="{{ cli }}"

  - name: Merge the set of RADIUS group name configuration and merge a new case-sensitive RADIUS qos profile attribute
    ne_radius_qosprofilecasesensitive_config:
      groupName='cbb'
      sourceInterfaceName='true'
      groupNameOperation='merge'
      caseSensitiveOperation='merge'
      provider="{{ cli }}"

  - name: delete the set of RADIUS group name configuration and the case-sensitive RADIUS qos profile attribute
    ne_radius_qosprofilecasesensitive_config:
      groupName='cbb'
      sourceInterfaceName='true'
      groupNameOperation='delete'
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
        "caseSensitive": "true",
        "groupName": "cbb",
        "groupNameOperation": "merge",
        "caseSensitiveOperation": "delete"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "groupNames": [
            {
                "caseSensitive": "true",
                "groupName": "cbb"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "groupNames": [
            {
                "caseSensitive": "false",
                "groupName": "cbb"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
RADIUSTEMPLATE_HEAD = """
    <config>
      <brasqos xmlns="http://www.huawei.com/netconf/vrp/huawei-brasqos">
        <radiusTemplates>
"""

RADIUSTEMPLATE_TAIL = """
            </qosProfileCaseSensitive>
          </radiusTemplate>
        </radiusTemplates>
      </brasqos>
    </config>
"""

RADIUSTEMPLATE_GET_HEAD = """
    <filter type="subtree">
    <brasqos xmlns="http://www.huawei.com/netconf/vrp/huawei-brasqos">
      <radiusTemplates>
        <radiusTemplate>
"""

RADIUSTEMPLATE_GET_TAIL = """
          </qosProfileCaseSensitive>
        </radiusTemplate>
      </radiusTemplates>
    </brasqos>
  </filter>
"""

CASESENSITIVE_GET = """
      <caseSensitive/>"""

GROUPNAME = """
      <groupName>%s</groupName>
"""

CASESENSITIVE = """
      <caseSensitive>%s</caseSensitive>
"""

QOSPROFILECASESENSITIVE = """
      <qosProfileCaseSensitive>"""

RADIUSTEMPLATE_CREATE = """
     <radiusTemplate nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

RADIUSTEMPLATE_DELETE = """
      <radiusTemplate nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

RADIUSTEMPLATE_MERGE = """
      <radiusTemplate nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

QOSPROFILECASESENSITIVE_CREATE = """
      <qosProfileCaseSensitive nc:operation="create">"""

QOSPROFILECASESENSITIVE_MERGE = """
      <qosProfileCaseSensitive nc:operation="merge">"""

QOSPROFILECASESENSITIVE_DELETE = """
      <qosProfileCaseSensitive nc:operation="delete">"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.groupName = self.module.params['groupName']
        self.caseSensitive = self.module.params['caseSensitive']
        self.groupNameOperation = self.module.params['groupNameOperation']
        self.caseSensitiveOperation = self.module.params['caseSensitiveOperation']

        if self.caseSensitive is None and self.groupNameOperation != 'get':
            self.caseSensitive = 'false'

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.groupName is not None:
            self.proposed["groupName"] = self.groupName
        if self.caseSensitive is not None:
            self.proposed["caseSensitive"] = self.caseSensitive
        if self.groupNameOperation is not None:
            self.proposed["groupNameOperation"] = self.groupNameOperation
        if self.caseSensitiveOperation is not None:
            self.proposed["caseSensitiveOperation"] = self.caseSensitiveOperation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        self.changed = True
        cfg_str = ''
        cfg_str += RADIUSTEMPLATE_HEAD
        if self.groupNameOperation == 'create':
            cfg_str += RADIUSTEMPLATE_CREATE
            if self.groupName:
                cfg_str += GROUPNAME % self.groupName
            cfg_str += QOSPROFILECASESENSITIVE
            if self.caseSensitive:
                cfg_str += CASESENSITIVE % self.caseSensitive

        if self.groupNameOperation == 'delete':
            cfg_str += RADIUSTEMPLATE_DELETE
            if self.groupName:
                cfg_str += GROUPNAME % self.groupName
            cfg_str += QOSPROFILECASESENSITIVE
            if self.caseSensitive:
                cfg_str += CASESENSITIVE % self.caseSensitive

        if self.groupNameOperation == 'merge':
            cfg_str += RADIUSTEMPLATE_MERGE
            if self.groupName:
                cfg_str += GROUPNAME % self.groupName
            if self.caseSensitiveOperation == 'create':
                cfg_str += QOSPROFILECASESENSITIVE_CREATE
            elif self.caseSensitiveOperation == 'merge':
                cfg_str += QOSPROFILECASESENSITIVE_MERGE
            elif self.caseSensitiveOperation == 'delete':
                cfg_str += QOSPROFILECASESENSITIVE_DELETE
            else:
                cfg_str += QOSPROFILECASESENSITIVE
            if self.caseSensitive:
                cfg_str += CASESENSITIVE % self.caseSensitive

        cfg_str += RADIUSTEMPLATE_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += RADIUSTEMPLATE_GET_HEAD
        if self.groupName:
            cfg_str += GROUPNAME % self.groupName
        cfg_str += QOSPROFILECASESENSITIVE
        if self.groupNameOperation == 'get':
            if self.caseSensitive:
                cfg_str += CASESENSITIVE % self.caseSensitive
        if self.groupNameOperation != 'get':
            cfg_str += CASESENSITIVE_GET
        cfg_str += RADIUSTEMPLATE_GET_TAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasqos"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasqos/radiusTemplates/radiusTemplate")
        attributes_Info["groupNames"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["groupName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "qosProfileCaseSensitive")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["caseSensitive"]:
                                container_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                    attributes_Info["groupNames"].append(container_info_Table)

        if len(attributes_Info["groupNames"]) == 0:
            attributes_Info.clear()
        # 解析5: 返回数据
        return attributes_Info

    def run(self):
        # 第一步: 检测输入

        # 第二步: 下发 get 报文, 查询当前配置
        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        # 第三步: 根据用户输入的操作码下发配置, 查询功能已经在 get_existing 实现
        if self.groupNameOperation != 'get':
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
        groupName=dict(required=False, type='str'),
        caseSensitive=dict(required=False, choices=['true', 'false']),
        groupNameOperation=dict(
            required=False,
            choices=[
                'merge',
                'create',
                'delete',
                'get'],
            default='merge'),
        caseSensitiveOperation=dict(
            required=False, choices=[
                'merge', 'create', 'delete']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
