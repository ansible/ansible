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
module: ne_radius_radiusattributeincludevas_config
version_added: "2.6"
short_description: Allows RADIUS packets to carry a specified attribute.
description:
    - Allows RADIUS packets to carry a specified attribute.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    groupName:
        description:
            - RADIUS server group's name. The value can be a string of 1 to 32 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    agentCircuitId:
        description:
            - Indicates the DSL FORUM No. 1 attribute, which represents the agent circuit ID.
        required: false
        default: false
        choices: ['true', 'false']
    agentRemoteId:
        description:
            - Indicates the DSL FORUM No. 2 attribute, which represents the agent remote circuit ID.
        required: false
        default: false
        choices: ['true', 'false']
    groupNameOperation:
        description:
            - Manage the state of the resource.If groupNameOperation is get,the agentCircuitId and agentRemoteId cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: merge
        choices: ['create', 'merge', 'delete', 'get']
    agentCircuitIdOperation:
        description:
            - Manage the state of the resource.
        required: false
        choices: ['merge', 'delete']
    agentRemoteIdOperation:
        description:
            - Manage the state of the resource.
        required: false
        choices: ['merge', 'delete']
'''

EXAMPLES = '''

- name: Config a RADIUS packets to carry a specified attribute test
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

  - name: Create a set of RADIUS group name configuration and RADIUS packets to carry a specified attribute configuration
    ne_radius_radiusattributeincludevas_config:
      groupName='cbb'
      agentCircuitId='true'
      agentRemoteId='true'
      groupNameOperation='create'
      provider="{{ cli }}"

  - name: Merge the set of RADIUS group name configuration and RADIUS packets to carry a specified attribute configuration
    ne_radius_radiusattributeincludevas_config:
      groupName='cbb'
      agentCircuitId='false'
      agentRemoteId='true'
      groupNameOperation='merge'
      provider="{{ cli }}"

  - name: delete the set of RADIUS group name configuration and the RADIUS packets to carry a specified attribute configuration
    ne_radius_radiusattributeincludevas_config:
      groupName='cbb'
      agentCircuitId='false'
      agentRemoteId='true'
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
        "agentCircuitId": "true",
        "agentRemoteId": "false",
        "groupName": "cbb",
        "groupNameOperation": "merge"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "groupNames": [
            {
                "agentCircuitId": "true",
                "agentRemoteId": "true",
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
                "agentCircuitId": "true",
                "agentRemoteId": "false",
                "groupName": "cbb"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
RDSTEMPLATE_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <rdsTemplates>
"""

RDSTEMPLATE_TAIL = """
          </radiusAttributeIncludeVas>
          </rdsTemplate>
        </rdsTemplates>
      </brasvas>
    </config>
"""

RDSTEMPLATE_GET_HEAD = """
    <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <rdsTemplates>
        <rdsTemplate>
"""

RDSTEMPLATE_GET_TAIL = """
          </radiusAttributeIncludeVas>
        </rdsTemplate>
      </rdsTemplates>
    </brasvas>
  </filter>
"""

RADIUSATTRIBUTEINCLUDEVAS_GET = """
      <radiusAttributeIncludeVas>"""

AGENTCIRCUITID_GET = """
      <agentCircuitId/>"""

AGENTREMOTEID_GET = """
      <agentRemoteId/>"""

GROUPNAME = """
      <groupName>%s</groupName>
"""

AGENTCIRCUITID = """
      <agentCircuitId>%s</agentCircuitId>
"""

AGENTREMOTEID = """
      <agentRemoteId>%s</agentRemoteId>"""

RADIUSATTRIBUTEINCLUDEVAS = """
      <radiusAttributeIncludeVas>"""

RDSTEMPLATE_CREATE = """
     <rdsTemplate nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

RDSTEMPLATE_MERGE = """
      <rdsTemplate nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

RDSTEMPLATE_DELETE = """
      <rdsTemplate nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

AGENTCIRCUITID_DELETE = """
<agentCircuitId nc:operation="delete">%s</agentCircuitId>"""

AGENTCIRCUITID_MERGE = """
<agentCircuitId nc:operation="merge">%s</agentCircuitId>"""

AGENTREMOTEID_DELETE = """
<agentRemoteId nc:operation="delete">%s</agentRemoteId>"""

AGENTREMOTEID_MERGE = """
<agentRemoteId nc:operation="merge">%s</agentRemoteId>"""


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
        self.agentCircuitId = self.module.params['agentCircuitId']
        self.agentRemoteId = self.module.params['agentRemoteId']
        self.groupNameOperation = self.module.params['groupNameOperation']
        self.agentCircuitIdOperation = self.module.params['agentCircuitIdOperation']
        self.agentRemoteIdOperation = self.module.params['agentRemoteIdOperation']

        if self.agentCircuitId is None and self.groupNameOperation != 'get':
            self.agentCircuitId = 'false'
        if self.agentRemoteId is None and self.groupNameOperation != 'get':
            self.agentRemoteId = 'false'

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.groupName is not None:
            self.proposed["groupName"] = self.groupName
        if self.agentCircuitId is not None:
            self.proposed["agentCircuitId"] = self.agentCircuitId
        if self.agentRemoteId is not None:
            self.proposed["agentRemoteId"] = self.agentRemoteId
        if self.groupNameOperation is not None:
            self.proposed["groupNameOperation"] = self.groupNameOperation
        if self.agentCircuitIdOperation is not None:
            self.proposed["agentCircuitIdOperation"] = self.agentCircuitIdOperation
        if self.agentRemoteIdOperation is not None:
            self.proposed["agentRemoteIdOperation"] = self.agentRemoteIdOperation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        self.changed = True
        cfg_str = ''
        cfg_str += RDSTEMPLATE_HEAD
        if self.groupNameOperation == 'create':
            cfg_str += RDSTEMPLATE_CREATE
            if self.groupName:
                cfg_str += GROUPNAME % self.groupName
            cfg_str += RADIUSATTRIBUTEINCLUDEVAS
            if self.agentCircuitId:
                cfg_str += AGENTCIRCUITID % self.agentCircuitId
            if self.agentRemoteId:
                cfg_str += AGENTREMOTEID % self.agentRemoteId

        if self.groupNameOperation == 'merge':
            cfg_str += RDSTEMPLATE_MERGE
            if self.groupName:
                cfg_str += GROUPNAME % self.groupName
            cfg_str += RADIUSATTRIBUTEINCLUDEVAS
            if self.agentCircuitIdOperation == 'delete':
                cfg_str += AGENTCIRCUITID_DELETE % self.agentCircuitId
            elif self.agentCircuitIdOperation == 'merge':
                cfg_str += AGENTCIRCUITID_MERGE % self.agentCircuitId
            else:
                if self.agentCircuitId:
                    cfg_str += AGENTCIRCUITID % self.agentCircuitId
            if self.agentRemoteIdOperation == 'delete':
                cfg_str += AGENTREMOTEID_DELETE % self.agentRemoteId
            elif self.agentRemoteIdOperation == 'merge':
                cfg_str += AGENTREMOTEID_MERGE % self.agentRemoteId
            else:
                if self.agentRemoteId:
                    cfg_str += AGENTREMOTEID % self.agentRemoteId

        if self.groupNameOperation == 'delete':
            cfg_str += RDSTEMPLATE_DELETE
            if self.groupName:
                cfg_str += GROUPNAME % self.groupName
            cfg_str += RADIUSATTRIBUTEINCLUDEVAS
            if self.agentCircuitId:
                cfg_str += AGENTCIRCUITID % self.agentCircuitId
            if self.agentRemoteId:
                cfg_str += AGENTREMOTEID % self.agentRemoteId

        cfg_str += RDSTEMPLATE_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += RDSTEMPLATE_GET_HEAD
        if self.groupName:
            cfg_str += GROUPNAME % self.groupName
        cfg_str += RADIUSATTRIBUTEINCLUDEVAS
        if self.groupNameOperation == 'get':
            if self.agentCircuitId:
                cfg_str += AGENTCIRCUITID % self.agentCircuitId
            if self.agentRemoteId:
                cfg_str += AGENTREMOTEID % self.agentRemoteId
        if self.groupNameOperation != 'get':
            cfg_str += AGENTCIRCUITID_GET
            cfg_str += AGENTREMOTEID_GET
        cfg_str += RDSTEMPLATE_GET_TAIL

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
        container_1_attributes_Info = root.findall(
            "brasvas/rdsTemplates/rdsTemplate")
        attributes_Info["groupNames"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["groupName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "radiusAttributeIncludeVas")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in [
                                    "agentCircuitId", "agentRemoteId"]:
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
        agentCircuitId=dict(required=False, choices=['true', 'false']),
        agentRemoteId=dict(required=False, choices=['true', 'false']),
        groupNameOperation=dict(
            required=False,
            choices=[
                'merge',
                'create',
                'delete',
                'get'],
            default='merge'),
        agentCircuitIdOperation=dict(
            required=False, choices=[
                'merge', 'delete']),
        agentRemoteIdOperation=dict(
            required=False, choices=[
                'merge', 'delete']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
