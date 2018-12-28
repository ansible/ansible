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
module: ne_brasipv4addrmng_groupvpninstance_config
version_added: "2.6"
short_description: Manage brasipv4addrmng module ip-pool config rule configuration.
description:
    - Manage brasipv4addrmng module ip-pool config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    poolGroupName:
        description:
            - Specifies the name of the brasipv4addrmng pool-group to be created. The value can be a string of 1 to 128 characters.
            The value must start with either uppercase letters A to Z or lowercase letters a to z and be a combination of letters,
            digits, hyphens (-), and underscores (_).
        required: true
    vpnInstance:
        description:
            - Specifies the name of the vpnInstance. The value can be a string of 1 to 64 characters.
            The value must start with either uppercase letters A to Z or lowercase letters a to z and be a combination of letters,
            digits, hyphens (-), and underscores (_).
        required: true
    poolGroupNameoperation:
        description:
            -  Manage the state of the resource.
        required: false
        default: merge
        choices: ['create', 'delete','merge','get']
    VpnInstanceoperation:
        description:
            -  Manage the state of the resource.
        required: true
        choices: ['create', 'delete','merge']

'''

EXAMPLES = '''

- name: Manage brasipv4addrmng module VpnInstance and poolGroupName config rule configuration.
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

  - name:Create a brasipv4addrmng module poolGroupName rule
    ne_brasipv4addrmng_groupVpnInstance_config:
    poolGroupName='v_grp_liuhong3',
    poolGroupNameoperation='create'
    operation='create'
    provider="{{ cli }}"

  - name:Delete a brasipv4addrmng module poolGroupName rule
    ne_brasipv4addrmng_groupVpnInstance_config:
    poolGroupName='v_grp_liuhong3',
    poolGroupNameoperation='delete'
    provider="{{ cli }}"

  - name:Merge a brasipv4addrmng module poolGroupName rule
    ne_brasipv4addrmng_groupVpnInstance_config:
    poolGroupName='v_grp_liuhong3',
    poolGroupNameoperation='merge'
    provider="{{ cli }}"

    - name:Create a brasipv4addrmng module VpnInstance  rule
    ne_brasipv4addrmng_groupVpnInstance_config:
    poolGroupName='v_grp_liuhong3',
    vpnInstance='vpntest2'
    poolGroupNameoperation='create'
    VpnInstanceoperation='create'
    provider="{{ cli }}"

  - name:Delete a brasipv4addrmng module VpnInstance  rule
    ne_brasipv4addrmng_groupVpnInstance_config:
    poolGroupName='v_grp_liuhong3',
    vpnInstance='vpntest2'
    poolGroupNameoperation='merge'
    VpnInstanceoperation='delete'
    provider="{{ cli }}"

  - name:Merge a brasipv4addrmng module VpnInstance  rule
    ne_brasipv4addrmng_groupVpnInstance_config:
    poolGroupName='v_grp_liuhong3',
    vpnInstance='vpntest2'
    poolGroupNameoperation='merge'
    VpnInstanceoperation='merge'
    provider="{{ cli }}"

  - name:get a brasipv4addrmng module VpnInstance  rule
    ne_brasipv4addrmng_groupVpnInstance_config:
    poolGroupName='v_grp_liuhong3',
    poolGroupNameoperation='get'
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
        "VpnInstanceoperation": "merge",
        "poolGroupName": "v_grp_liuhong3",
        "poolGroupNameoperation": "merge",
        "vpnInstance": "vpntest2"


    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
          "ipv4PoolGroups": [
            {
                "poolGroupName": "v_grp_liuhong3"
            }
        ]






    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
        "ipv4PoolGroups": [
            {
                "poolGroupName": "v_grp_liuhong3",
                "vpnInstance": "vpntest2"
            }
        ]



    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
GROUPVPNINSTANCE_HEAD = """
    <config>
      <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
        <ipv4PoolGroups>
"""

GROUPVPNINSTANCE_TAIL = """
           </ipv4PoolGroups>
      </brasipv4addrmng>
    </config>
"""

GROUPVPNINSTANCE_GETHEAD = """
    <filter type="subtree">
      <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
        <ipv4PoolGroups>
          <ipv4PoolGroup>
"""

GROUPVPNINSTANCE_GETTAIL = """
      </ipv4PoolGroup>
      </ipv4PoolGroups>
    </brasipv4addrmng>
  </filter>
"""

GROUPVPNINSTANCE_CREATE = """
        <ipv4PoolGroup nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

GROUPVPNINSTANCE_DELETE = """
       <ipv4PoolGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

GROUPVPNINSTANCE_MERGE = """
       <ipv4PoolGroup nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

GROUPVPNINSTANCEVPN_CREATE = """
     <groupVpnInstance nc:operation="create">
"""

GROUPVPNINSTANCEVPN_DELETE = """
     <groupVpnInstance nc:operation="delete">
"""

GROUPVPNINSTANCEVPN_MERGE = """
     <groupVpnInstance nc:operation="merge">
"""

POOLGROUPNAME = """
      <poolGroupName>%s</poolGroupName>
"""

VPNINSTANCE = """
  <vpnInstance>%s</vpnInstance>
"""

GROUPVPNINSTANCEBEG = """
      <groupVpnInstance>
"""

GROUPVPNINSTANCEEND = """
        </groupVpnInstance>
"""

GROUPVPNEND = """
   <groupVpnInstance/>
"""

IPV4POOLGROUPEND = """
       </ipv4PoolGroup>
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
        self.poolGroupName = self.module.params['poolGroupName']
        self.vpnInstance = self.module.params['vpnInstance']
        self.poolGroupNameoperation = self.module.params['poolGroupNameoperation']
        self.VpnInstanceoperation = self.module.params['VpnInstanceoperation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.poolGroupName is not None:
            self.proposed["poolGroupName"] = self.poolGroupName
        if self.vpnInstance is not None:
            self.proposed["vpnInstance"] = self.vpnInstance
        if self.poolGroupNameoperation is not None:
            self.proposed["poolGroupNameoperation"] = self.poolGroupNameoperation
        if self.VpnInstanceoperation is not None:
            self.proposed["VpnInstanceoperation"] = self.VpnInstanceoperation
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
        cfg_str += GROUPVPNINSTANCE_HEAD
        if self.poolGroupNameoperation == 'create':
            cfg_str += GROUPVPNINSTANCE_CREATE
            if self.poolGroupName:
                cfg_str += POOLGROUPNAME % self.poolGroupName
            if self.VpnInstanceoperation == 'create':
                cfg_str += GROUPVPNINSTANCEVPN_CREATE
                if self.vpnInstance:
                    cfg_str += VPNINSTANCE % self.vpnInstance
                cfg_str += GROUPVPNINSTANCEEND
            if self.VpnInstanceoperation == 'delete':
                cfg_str += GROUPVPNINSTANCEVPN_DELETE
                if self.vpnInstance:
                    cfg_str += VPNINSTANCE % self.vpnInstance
                cfg_str += GROUPVPNINSTANCEEND
            if self.VpnInstanceoperation == 'merge':
                cfg_str += GROUPVPNINSTANCEVPN_MERGE
                if self.vpnInstance:
                    cfg_str += VPNINSTANCE % self.vpnInstance
                cfg_str += GROUPVPNINSTANCEEND
            cfg_str += IPV4POOLGROUPEND

        if self.poolGroupNameoperation == 'delete':
            cfg_str += GROUPVPNINSTANCE_DELETE
            if self.poolGroupName:
                cfg_str += POOLGROUPNAME % self.poolGroupName
            cfg_str += IPV4POOLGROUPEND

        if self.poolGroupNameoperation == 'merge':
            cfg_str += GROUPVPNINSTANCE_MERGE
            if self.poolGroupName:
                cfg_str += POOLGROUPNAME % self.poolGroupName
            if self.VpnInstanceoperation == 'create':
                cfg_str += GROUPVPNINSTANCEVPN_CREATE
                if self.vpnInstance:
                    cfg_str += VPNINSTANCE % self.vpnInstance
                cfg_str += GROUPVPNINSTANCEEND
            if self.VpnInstanceoperation == 'delete':
                cfg_str += GROUPVPNINSTANCEVPN_DELETE
                if self.vpnInstance:
                    cfg_str += VPNINSTANCE % self.vpnInstance
                cfg_str += GROUPVPNINSTANCEEND
            if self.VpnInstanceoperation == 'merge':
                cfg_str += GROUPVPNINSTANCEVPN_MERGE
                if self.vpnInstance:
                    cfg_str += VPNINSTANCE % self.vpnInstance
                cfg_str += GROUPVPNINSTANCEEND
            cfg_str += IPV4POOLGROUPEND

        cfg_str += GROUPVPNINSTANCE_TAIL
        # 第二步: 下发配置报文
        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += GROUPVPNINSTANCE_GETHEAD
        if self.poolGroupName:
            cfg_str += POOLGROUPNAME % self.poolGroupName
        if self.poolGroupNameoperation != 'get':
            cfg_str += GROUPVPNEND
        if self.poolGroupNameoperation == 'get':
            cfg_str += GROUPVPNINSTANCEBEG
            if self.vpnInstance:
                cfg_str += VPNINSTANCE % self.vpnInstance
            cfg_str += GROUPVPNINSTANCEEND
        cfg_str += GROUPVPNINSTANCE_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasipv4addrmng/ipv4PoolGroups/ipv4PoolGroup")
        attributes_Info["ipv4PoolGroups"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["poolGroupName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "groupVpnInstance")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in ["vpnInstance"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                attributes_Info["ipv4PoolGroups"].append(
                    service_container_Table)

        # if len(attributes_Info["ipv4PoolGroups"]) == 0:
            # attributes_Info.clear()
        # 解析5: 返回数据
        return attributes_Info

    def run(self):
        # 第一步: 检测输入

        # 第二步: 下发 get 报文, 查询当前配置
        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        # 第三步: 根据用户输入的操作码下发配置, 查询功能已经在 get_existing 实现
        if self.poolGroupNameoperation != 'get':
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
        poolGroupName=dict(required=False, type='str'),
        vpnInstance=dict(required=False, type='str'),
        poolGroupNameoperation=dict(
            required=False,
            choices=[
                'create',
                'delete',
                'merge',
                'get'],
            default='merge'),
        VpnInstanceoperation=dict(
            required=False, choices=[
                'create', 'delete', 'merge']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
