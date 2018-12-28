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
module: ne_brasl2tpaccess_l2tptunnel_config
version_added: "2.6"
short_description: Manage brasl2tpaccess module l2tpTunnel config rule configuration.
description:
    -  Manage brasl2tpaccess module l2tpTunnel config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    groupName:
        description:
            - l2tp group Name. The value can be a string of 1 to 32 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    tunnelName:
        description:
            - tunnelName. The value can be a string of 1 to 253 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    passwordType:
        description:
            - passType. the value is a string of simple or cipher.
        required: true
        choices: ['simple', 'cipher']
    l2tpTunnelpassword:
        description:
            -  password.The value can be a string of 1 to 255 characters. The value must start with either uppercase letters A to Z or lowercase
            letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    groupNameoperation:
        description:
            -  Manage the state of the resource.
            if operation is get,the passwordType and l2tpTunnelpassword and  tunnelName cannot take parameters,otherwise The echo of the
            command line is'This operation are not supported'.
        required: false
        default : merge
        choices: ['create', 'delete','merge','get']
    l2tpTunneloperation:
        description:
            -  Manage the state of the resource.
        required: true
        choices: ['create', 'delete','merge']

'''

EXAMPLES = '''

- name: Manage brasl2tpaccess module l2tpTunnel config rule configuration.
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

  - name:create a brasl2tpaccess module  groupName config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    groupNameoperation='create'
    provider="{{ cli }}"

  - name:delete a brasl2tpaccess module  groupName config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    groupNameoperation='delete'
    provider="{{ cli }}"

  - name:merege a brasl2tpaccess module  groupName config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    groupNameoperation='merge'
    provider="{{ cli }}"

  - name:create a brasl2tpaccess module  tunnelName config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    tunnelName='huawei000'
    l2tpTunneloperation='create'
    provider="{{ cli }}"

  - name:delete a brasl2tpaccess module  tunnelName config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    tunnelName='huawei000'
    l2tpTunneloperation='delete'
    provider="{{ cli }}"

  - name:merge a brasl2tpaccess module  tunnelName config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    tunnelName='huawei000'
    l2tpTunneloperation='merge'
    provider="{{ cli }}"

  - name:create a brasl2tpaccess module  password config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    passwordType='simple'
    l2tpTunnelpassword='###ddd'
    l2tpTunneloperation='create'
    provider="{{ cli }}"

  - name:delete a brasl2tpaccess module  password config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    passwordType='simple'
    l2tpTunnelpassword='###ddd'
    l2tpTunneloperation='delete'
    provider="{{ cli }}"

  - name:merge a brasl2tpaccess module  password config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    passwordType='simple'
    l2tpTunnelpassword='###ddd'
    l2tpTunneloperation='merge'
    provider="{{ cli }}"

  - name:get a brasl2tpaccess module  l2tptunnel config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupName='vtest05251'
    groupNameoperation='get'
    provider="{{ cli }}"

  - name:get a brasl2tpaccess module  l2tptunnel config rule
    ne_brasl2tpaccess_l2tpTunnel_config:
    groupNameoperation='get'
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
        "groupName": "l2tptest1",
        "groupNameoperation": "merge",
        "l2tpTunnelpassword": "dddfff",
        "passwordType": "simple"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "l2tpTunnels": [
            {
                "l2tpGroupName": "l2tptest1",
                "password": "%^%#}nay)sW7BH_kc7~)`~%<n5Rg%IJ5fYZ~$_L69TqV%^%#",
                "passwordType": "cipher",
                "tunnelName": "huawei000"
            }
        ]

    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "l2tpTunnels": [
            {
                "l2tpGroupName": "l2tptest1",
                "password": "%^%#}nay)sW7BH_kc7~)`~%<n5Rg%IJ5fYZ~$_L69TqV%^%#",
                "passwordType": "cipher",
                "tunnelName": "huawei000"
            }
        ]

    }

'''


logging.basicConfig(filename='example.log', level=logging.DEBUG)
L2TPTUNNELGROUPNAME_HEAD = """
    <config>
      <brasl2tpaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasl2tpaccess">
        <l2tpGroups>
"""

L2TPTUNNELGROUPNAME_TAIL = """
              </l2tpGroups>
      </brasl2tpaccess>
    </config>
"""

L2TPTUNNELGROUPNAME_GETHEAD = """
    <filter type="subtree">
      <brasl2tpaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasl2tpaccess">
        <l2tpGroups>
          <l2tpGroup>
"""

L2TPTUNNELGROUPNAME_GETTAIL = """
            </l2tpGroup>
        </l2tpGroups>
     </brasl2tpaccess>
  </filter>
"""
L2TPGROUP_CREATE = """
       <l2tpGroup xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
"""

L2TPGROUP_DELETE = """
       <l2tpGroup xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete">
"""

L2TPGROUP_MERGE = """
       <l2tpGroup xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="merge">
"""

L2TPTUNNEL_CREATE = """
       <l2tpTunnel nc:operation="create">
"""

L2TPTUNNEL_DELETE = """
       <l2tpTunnel nc:operation="delete">
"""

L2TPTUNNEL_MERGE = """
       <l2tpTunnel nc:operation="merge">
"""


L2TPGROUPNAME = """
       <l2tpGroupName>%s</l2tpGroupName>
"""

TUNNELNAME = """
      <tunnelName>%s</tunnelName>
"""

PASSWORDTYPE = """
       <passwordType>%s</passwordType>
"""

PASSWORD = """
       <password>%s</password>
"""

L2TPTUNNELBEG = """
    <l2tpTunnel>
"""

L2TPTUNNELEND = """
    </l2tpTunnel>
"""

TUNNELNAMESTR = """
   <tunnelName/>
"""

PASSWORDTYPESTR = """
    <passwordType/>
"""

PASSWORDSTR = """
    <password/>
"""
L2TPGROUPEND = """
    </l2tpGroup>
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
        self.groupName = self.module.params['groupName']
        self.tunnelName = self.module.params['tunnelName']
        self.passwordType = self.module.params['passwordType']
        self.l2tpTunnelpassword = self.module.params['l2tpTunnelpassword']
        self.groupNameoperation = self.module.params['groupNameoperation']
        self.l2tpTunneloperation = self.module.params['l2tpTunneloperation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.groupName is not None:
            self.proposed["groupName"] = self.groupName
        if self.tunnelName is not None:
            self.proposed["tunnelName"] = self.tunnelName
        if self.passwordType is not None:
            self.proposed["passwordType"] = self.passwordType
        if self.l2tpTunnelpassword is not None:
            self.proposed["l2tpTunnelpassword"] = self.l2tpTunnelpassword
        if self.groupNameoperation is not None:
            self.proposed["groupNameoperation"] = self.groupNameoperation
        if self.l2tpTunneloperation is not None:
            self.proposed["l2tpTunneloperation"] = self.l2tpTunneloperation

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
        cfg_str += L2TPTUNNELGROUPNAME_HEAD
        if self.groupNameoperation == 'create':
            cfg_str += L2TPGROUP_CREATE
        if self.groupNameoperation == 'delete':
            cfg_str += L2TPGROUP_DELETE
        if self.groupNameoperation == 'merge':
            cfg_str += L2TPGROUP_MERGE
        if self.groupName:
            cfg_str += L2TPGROUPNAME % self.groupName
        if self.l2tpTunneloperation == 'create':
            cfg_str += L2TPTUNNEL_CREATE
            if self.tunnelName:
                cfg_str += TUNNELNAME % self.tunnelName
            if self.passwordType:
                cfg_str += PASSWORDTYPE % self.passwordType
            if self.l2tpTunnelpassword:
                cfg_str += PASSWORD % self.l2tpTunnelpassword
            cfg_str += L2TPTUNNELEND
        if self.l2tpTunneloperation == 'delete':
            cfg_str += L2TPTUNNEL_DELETE
            if self.tunnelName:
                cfg_str += TUNNELNAME % self.tunnelName
            if self.passwordType:
                cfg_str += PASSWORDTYPE % self.passwordType
            if self.l2tpTunnelpassword:
                cfg_str += PASSWORD % self.l2tpTunnelpassword
            cfg_str += L2TPTUNNELEND
        if self.l2tpTunneloperation == 'merge':
            cfg_str += L2TPTUNNEL_MERGE
            if self.tunnelName:
                cfg_str += TUNNELNAME % self.tunnelName
            if self.passwordType:
                cfg_str += PASSWORDTYPE % self.passwordType
            if self.l2tpTunnelpassword:
                cfg_str += PASSWORD % self.l2tpTunnelpassword
            cfg_str += L2TPTUNNELEND
        cfg_str += L2TPGROUPEND
        cfg_str += L2TPTUNNELGROUPNAME_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += L2TPTUNNELGROUPNAME_GETHEAD
        if self.groupName:
            cfg_str += L2TPGROUPNAME % self.groupName
        cfg_str += L2TPTUNNELBEG
        if self.groupNameoperation != 'get':
            cfg_str += TUNNELNAMESTR
            cfg_str += PASSWORDTYPESTR
            cfg_str += PASSWORDSTR
        if self.groupNameoperation == 'get':
            if self.tunnelName:
                cfg_str += TUNNELNAME % self.tunnelName
            if self.passwordType:
                cfg_str += PASSWORDTYPE % self.passwordType
            if self.l2tpTunnelpassword:
                cfg_str += PASSWORD % self.l2tpTunnelpassword
        cfg_str += L2TPTUNNELEND
        cfg_str += L2TPTUNNELGROUPNAME_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasl2tpaccess"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasl2tpaccess/l2tpGroups/l2tpGroup")
        attributes_Info["l2tpTunnels"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["l2tpGroupName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall("l2tpTunnel")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "tunnelName", "passwordType", "password"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                    attributes_Info["l2tpTunnels"].append(
                        service_container_Table)

        # if len(attributes_Info["remoteBackupServiceCombines"]) == 0:
            # attributes_Info.clear()
        # 解析5: 返回数据
        return attributes_Info

    def run(self):
        # 第一步: 检测输入

        # 第二步: 下发 get 报文, 查询当前配置
        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        # 第三步: 根据用户输入的操作码下发配置, 查询功能已经在 get_existing 实现
        if self.groupNameoperation != 'get':
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
        groupName=dict(required=False, type='str'),
        tunnelName=dict(required=False, type='str'),
        passwordType=dict(required=False, choices=['simple', 'cipher']),
        l2tpTunnelpassword=dict(required=False, type='str'),
        groupNameoperation=dict(
            required=False,
            choices=[
                'create',
                'delete',
                'merge',
                'get'],
            default='merge'),
        l2tpTunneloperation=dict(
            required=False, choices=[
                'create', 'delete', 'merge']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
