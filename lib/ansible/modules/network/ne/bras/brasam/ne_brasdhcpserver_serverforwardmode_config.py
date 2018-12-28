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
module: ne_brasdhcpserver_serverforwardmode_config
version_added: "2.6"
short_description: The dhcp rebind forward-mode all command configures the NE40E to forward DHCP Rebind packets to all DHCPv4 servers in a DHCPv4 server group.
description:
    - The dhcp rebind forward-mode all command configures the NE40E to forward DHCP Rebind packets to all DHCPv4 servers in a DHCPv4 server group.
author:
    - cuibaobao (@CloudEngine-Ansible)
options:
    dhcpServerGroupName:
        description:
            - Specifies the name of the DHCPv4 server group. The value can be a string of 1 to 32 characters. The value must start with either
            uppercase letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    rebindAllEnable:
        description:
            - enable the NE40E to forward DHCP Rebind packets to all DHCPv4 servers in a DHCPv4 server group.
        required: false
        choices: ['true', 'false']
    dhcpServerGroupNameOperation:
        description:
            - Manage the state of the dhcpServerGroupName.If dhcpServerGroupNameOperation is get,the rebindAllEnable cannot take parameters,otherwise
            The echo of the command line is'This operation are not supported'.
        required: false
        default: merge
        choices: ['create', 'merge', 'delete', 'get']
    rebindAllEnableOperation:
        description:
            - Manage the state of the rebindAllEnable.
        required: false
        choices: ['create', 'merge', 'delete']
'''

EXAMPLES = '''

- name: Configures a dhcp rebind forward-mode all command configures the NE40E to forward DHCP Rebind
  packets to all DHCPv4 servers in a DHCPv4 server group test
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

  - name: Create a DHCPv4 server group configuration
    ne_brasdhcpserver_serverforwardmode_config:
      dhcpServerGroupName='cbb123456'
      dhcpServerGroupNameOperation='create'
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
        "dhcpServerGroupName": "cbb123456",
        "dhcpServerGroupNameOperation": "merge",
        "rebindAllEnable": "true",
        "rebindAllEnableOperation": "create"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "dhcpServerGroupNames": [
            {
                "dhcpServerGroupName": "cbb123456",
                "rebindAllEnable": "false"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "dhcpServerGroupNames": [
            {
                "dhcpServerGroupName": "cbb123456",
                "rebindAllEnable": "true"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)

DHCPSERVERGROUP_HEAD = """
    <config>
      <brasdhcpserver xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpserver">
        <dhcpServerGroups>
"""

DHCPSERVERGROUP_TAIL = """
              </serverForwardMode>
          </dhcpServerGroup>
        </dhcpServerGroups>
      </brasdhcpserver>
    </config>
"""

DHCPSERVERGROUPNAME = """
      <dhcpServerGroupName>%s</dhcpServerGroupName>"""

SERVERFORWARDMODE = """
      <serverForwardMode>"""

REBINDALLENABLE = """
      <rebindAllEnable>%s</rebindAllEnable>"""

DHCPSERVERGROUP_CREATE = """
      <dhcpServerGroup nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DHCPSERVERGROUP_MERGE = """
      <dhcpServerGroup nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DHCPSERVERGROUP_DELETE = """
      <dhcpServerGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVERFORWARDMODE_CREATE = """
      <serverForwardMode nc:operation="create">"""

SERVERFORWARDMODE_MERGE = """
      <serverForwardMode nc:operation="merge">"""

SERVERFORWARDMODE_DELETE = """
      <serverForwardMode nc:operation="delete">"""

DHCPSERVERGROUP_GET_HEAD = """
      <filter type="subtree">
    <brasdhcpserver xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpserver">
      <dhcpServerGroups>
        <dhcpServerGroup>"""

DHCPSERVERGROUP_GET_TAIL = """
          </serverForwardMode>
        </dhcpServerGroup>
      </dhcpServerGroups>
    </brasdhcpserver>
  </filter>"""

REBINDALLENABLE_GET = """
      <rebindAllEnable/>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.dhcpServerGroupName = self.module.params['dhcpServerGroupName']
        self.rebindAllEnable = self.module.params['rebindAllEnable']
        self.dhcpServerGroupNameOperation = self.module.params['dhcpServerGroupNameOperation']
        self.rebindAllEnableOperation = self.module.params['rebindAllEnableOperation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.dhcpServerGroupName is not None:
            self.proposed["dhcpServerGroupName"] = self.dhcpServerGroupName
        if self.rebindAllEnable is not None:
            self.proposed["rebindAllEnable"] = self.rebindAllEnable
        if self.dhcpServerGroupNameOperation is not None:
            self.proposed["dhcpServerGroupNameOperation"] = self.dhcpServerGroupNameOperation
        if self.rebindAllEnableOperation is not None:
            self.proposed["rebindAllEnableOperation"] = self.rebindAllEnableOperation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        self.changed = True
        cfg_str = ''
        cfg_str += DHCPSERVERGROUP_HEAD
        if self.dhcpServerGroupNameOperation == 'create':
            cfg_str += DHCPSERVERGROUP_CREATE
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            cfg_str += SERVERFORWARDMODE

        if self.dhcpServerGroupNameOperation == 'merge':
            cfg_str += DHCPSERVERGROUP_MERGE
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            if self.rebindAllEnableOperation == 'create':
                cfg_str += SERVERFORWARDMODE_CREATE
            elif self.rebindAllEnableOperation == 'merge':
                cfg_str += SERVERFORWARDMODE_MERGE
            elif self.rebindAllEnableOperation == 'delete':
                cfg_str += SERVERFORWARDMODE_DELETE
            else:
                cfg_str += SERVERFORWARDMODE
            if self.rebindAllEnable:
                cfg_str += REBINDALLENABLE % self.rebindAllEnable

        if self.dhcpServerGroupNameOperation == 'delete':
            cfg_str += DHCPSERVERGROUP_DELETE
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            cfg_str += SERVERFORWARDMODE
            if self.rebindAllEnable:
                cfg_str += REBINDALLENABLE % self.rebindAllEnable

        cfg_str += DHCPSERVERGROUP_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    # def check_params(self):
        # if self.dhcpServerGroupName is None:
        # if self.rebindAllEnable is not None and self.dhcpServerGroupNameOperation == 'get':
        # self.module.fail_json(msg='Error: This operation is not supported.')

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += DHCPSERVERGROUP_GET_HEAD
        if self.dhcpServerGroupName:
            cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
        cfg_str += SERVERFORWARDMODE
        if self.dhcpServerGroupNameOperation == 'get':
            if self.rebindAllEnable:
                cfg_str += REBINDALLENABLE % self.rebindAllEnable
        if self.dhcpServerGroupNameOperation != 'get':
            cfg_str += REBINDALLENABLE_GET
        cfg_str += DHCPSERVERGROUP_GET_TAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpserver"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasdhcpserver/dhcpServerGroups/dhcpServerGroup")
        attributes_Info["dhcpServerGroupNames"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["dhcpServerGroupName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "serverForwardMode")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["rebindAllEnable"]:
                                container_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                attributes_Info["dhcpServerGroupNames"].append(
                    container_info_Table)

        if len(attributes_Info["dhcpServerGroupNames"]) == 0:
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
        if self.dhcpServerGroupNameOperation != 'get':
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
        dhcpServerGroupName=dict(required=False, type='str'),
        rebindAllEnable=dict(required=False, choices=['true', 'false']),
        dhcpServerGroupNameOperation=dict(
            required=False,
            choices=[
                'merge',
                'create',
                'delete',
                'get'],
            default='merge'),
        rebindAllEnableOperation=dict(
            required=False, choices=[
                'merge', 'create', 'delete']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
