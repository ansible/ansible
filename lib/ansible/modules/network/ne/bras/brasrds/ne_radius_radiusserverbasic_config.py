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
module: ne_radius_radiusserverbasic_config
version_added: "2.6"
short_description: A set of RADIUS group configuration.
description:
    - A set of RADIUS group configuration.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    groupName:
        description:
            - RADIUS server group's name. The value can be a string of 1 to 32 characters. The value must start with either uppercase
            letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    sourceInterfaceName:
        description:
            - To configure source interface name at group level.
        required: false
    sharedKey:
        description:
            - To configure shared-key value for a particular group.
        required: false
    groupNameOperation:
        description:
            - Manage the state of the resource.If groupNameOperation is get,the sourceInterfaceName cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        choices: ['create', 'merge', 'delete', 'get']
    sourceInterfaceNameOperation:
        description:
            - Manage the state of the resource.
        required: false
        choices: ['delete']
    sharedKeyOperation:
        description:
            - Manage the shared-key configuration for a particular group.
        required: false
        choices: ['delete']
'''

EXAMPLES = '''

- name: Config a set of RADIUS group name test
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

  - name: Create a set of RADIUS group name configuration
    ne_radius_radiusserverbasic_config:
      groupName='cbb'
      sourceInterfaceName='LoopBack7'
      groupNameOperation='create'
      provider="{{ cli }}"

  - name: Delete the set of RADIUS group name configuration
    ne_radius_radiusserverbasic_config:
      groupName='cbb'
      sourceInterfaceName='LoopBack7'
      groupNameOperation='delete'
      provider="{{ cli }}"

  - name: Merge a new set of RADIUS group name configuration and a new sourceInterfaceName
    ne_radius_radiusserverbasic_config:
      groupName='cbb'
      sourceInterfaceName='LoopBack11'
      groupNameOperation='merge'
      provider="{{ cli }}"

  - name: Merge a new set of RADIUS group name configuration and delete the sourceInterfaceName
    ne_radius_radiusserverbasic_config:
      groupName='cbb'
      sourceInterfaceName='LoopBack11'
      groupNameOperation='merge'
      sourceInterfaceNameOperation='delete'
      provider="{{ cli }}"

  - name: Merge a new set of RADIUS group name configuration and a new sharedKey
    ne_radius_radiusserverbasic_config:
      groupName='cbb'
      sharedKey='huawei'
      groupNameOperation='merge'
      provider="{{ cli }}"

  - name: Merge a new set of RADIUS group name configuration and delete the sharedKey
    ne_radius_radiusserverbasic_config:
      groupName='cbb'
      groupNameOperation='merge'
      sharedKeyOperation='delete'
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
        "groupName": "cbb",
        "groupNameOperation": "merge",
        "sourceInterfaceNameOperation": "delete",
        "sourceInterfaceName": "LoopBack8"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "groupNames": [
            {
                "groupName": "cbb",
                "sourceInterfaceName": "LoopBack8"
                "sharedKey": "%^%#ZA)*VuQN\"SF,(+T&lt;LD#]*N'$fbsV"(kmQS_)&lt;6)%^%#"
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
                "groupName": "cbb"
                "sharedKey": "%^%#ZA)*VuQN\"SF,(+T&lt;LD#]*N'$fbsV"(kmQS_)&lt;6)%^%#"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
RDSTEMPLATE_HEAD = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
        <rdsTemplates>
"""

RDSTEMPLATE_TAIL = """
          </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

RDSTEMPLATE_GET_HEAD = """
    <filter type="subtree">
    <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
      <rdsTemplates>
        <rdsTemplate>
"""

RDSTEMPLATE_GET_TAIL = """
          </rdsTemplate>
      </rdsTemplates>
    </radius>
  </filter>
"""

SOURCEINTERFACENAME_GET = """
      <sourceInterfaceName/>"""

SHAREDKEY_GET = """
      <sharedKey/>"""

GROUPNAME = """
      <groupName>%s</groupName>
"""

SOURCEINTERFACENAME = """
      <sourceInterfaceName>%s</sourceInterfaceName>
"""

SHAREDKEY = """
      <sharedKey>%s</sharedKey>
"""

RDSTEMPLATE_CREATE = """
     <rdsTemplate nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

RDSTEMPLATE_DELETE = """
      <rdsTemplate nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

RDSTEMPLATE_MERGE = """
      <rdsTemplate nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SOURCEINTERFACENAME_DELETE = """
      <sourceInterfaceName nc:operation="delete">%s</sourceInterfaceName>"""

SHAREDKEY_DELETE = """
      <sharedKey nc:operation="delete">%s</sharedKey>"""


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
        self.sourceInterfaceName = self.module.params['sourceInterfaceName']
        self.sharedKey = self.module.params['sharedKey']
        self.groupNameOperation = self.module.params['groupNameOperation']
        self.sourceInterfaceNameOperation = self.module.params['sourceInterfaceNameOperation']
        self.sharedKeyOperation = self.module.params['sharedKeyOperation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.groupName is not None:
            self.proposed["groupName"] = self.groupName
        if self.sourceInterfaceName is not None:
            self.proposed["sourceInterfaceName"] = self.sourceInterfaceName
        if self.sharedKey is not None:
            self.proposed["sharedKey"] = self.sharedKey
        if self.groupNameOperation is not None:
            self.proposed["groupNameOperation"] = self.groupNameOperation
        if self.sourceInterfaceNameOperation is not None:
            self.proposed["sourceInterfaceNameOperation"] = self.sourceInterfaceNameOperation
        if self.sharedKeyOperation is not None:
            self.proposed["sharedKeyOperation"] = self.sharedKeyOperation

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
            if self.sourceInterfaceName:
                cfg_str += SOURCEINTERFACENAME % self.sourceInterfaceName
            if self.sharedKeyOperation == 'delete':
                cfg_str += SHAREDKEY_DELETE % self.sharedKey
            elif self.sharedKey is not None:
                cfg_str += SHAREDKEY % self.sharedKey

        if self.groupNameOperation == 'delete':
            cfg_str += RDSTEMPLATE_DELETE
            if self.groupName:
                cfg_str += GROUPNAME % self.groupName
            if self.sourceInterfaceName:
                cfg_str += SOURCEINTERFACENAME % self.sourceInterfaceName
            if self.sharedKeyOperation == 'delete':
                cfg_str += SHAREDKEY_DELETE % self.sharedKey
            elif self.sharedKey is not None:
                cfg_str += SHAREDKEY % self.sharedKey

        if self.groupNameOperation == 'merge':
            cfg_str += RDSTEMPLATE_MERGE
            if self.groupName:
                cfg_str += GROUPNAME % self.groupName
            if self.sourceInterfaceNameOperation == 'delete':
                cfg_str += SOURCEINTERFACENAME_DELETE % self.sourceInterfaceName
            else:
                if self.sourceInterfaceName:
                    cfg_str += SOURCEINTERFACENAME % self.sourceInterfaceName
            if self.sharedKeyOperation == 'delete':
                cfg_str += SHAREDKEY_DELETE % self.sharedKey
            elif self.sharedKey is not None:
                cfg_str += SHAREDKEY % self.sharedKey

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
        if self.groupNameOperation == 'get':
            if self.sourceInterfaceName:
                cfg_str += SOURCEINTERFACENAME % self.sourceInterfaceName
            if self.sharedKey is not None:
                cfg_str += SHAREDKEY % self.sharedKey
        if self.groupNameOperation != 'get':
            cfg_str += SOURCEINTERFACENAME_GET
            cfg_str += SHAREDKEY_GET
        cfg_str += RDSTEMPLATE_GET_TAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-radius"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_attributes_Info = root.findall(
            "radius/rdsTemplates/rdsTemplate")
        attributes_Info["groupNames"] = list()

        if len(container_attributes_Info) != 0:
            for container_node in container_attributes_Info:
                container_Table = dict()
                for leaf_attributes_Info in container_node:
                    if leaf_attributes_Info.tag in ["groupName",
                                                    "sourceInterfaceName",
                                                    "sharedKey"]:
                        container_Table[leaf_attributes_Info.tag] = leaf_attributes_Info.text
                attributes_Info["groupNames"].append(container_Table)
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
        sourceInterfaceName=dict(required=False, type='str'),
        sharedKey=dict(required=False, type='str'),
        groupNameOperation=dict(
            required=False,
            choices=[
                'merge',
                'create',
                'delete',
                'get'],
            default='merge'),
        sourceInterfaceNameOperation=dict(required=False, choices=['delete']),
        sharedKeyOperation=dict(required=False, choices=['delete']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
