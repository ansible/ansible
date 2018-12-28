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
module: ne_brasipv4addrmng_groupbindpools_config
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
    poolName:
        description:
            - Specifies the name of the address pool. The value can be a string of 1 to 128 characters.
            The value must start with either uppercase letters A to Z or lowercase letters a to z and be a combination of letters,
            digits, hyphens (-), and underscores (_).
    operation:
        description:
            -  Manage the state of the resource.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasipv4addrmng module ip-pool config rule configuration.
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

  - name:Create a brasipv4addrmng module ip-pool config rule
    ne_brasipv4addrmng_groupbindpools_config:
    poolGroupName='v_grp_liuhong10',
    poolName='ippooltest1'
    operation='create'
    provider="{{ cli }}"

  - name:Delete a brasipv4addrmng module ip-pool config rule
    ne_brasipv4addrmng_groupbindpools_config:
    poolGroupName='v_grp_liuhong10',
    poolName='ippooltest1'
    operation='delete'
    provider="{{ cli }}"

  - name:Merge a brasipv4addrmng module ip-pool config rule
    ne_brasipv4addrmng_groupbindpools_config:
    poolGroupName='v_grp_liuhong10',
    poolName='ippooltest1'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasipv4addrmng module ip-pool config rule
    ne_brasipv4addrmng_groupbindpools_config:
    poolGroupName='v_grp_liuhong10',
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
        "operation": "merge",
        "poolGroupName": "v_grp_liuhong10",
        "poolName": "ippooltest1"

    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
          "poolNames": [
            {
                "poolGroupName": "v_grp_liuhong10",
                "poolName": "ippooltest1"
            }
        ]





    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
        "serverAlgorithms": [
            {
                "algorithmType": "poolling",
                "dhcpServerGroupName": "v_grp_dhcp_test1"
            }
        ]


    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
GROUPBINDPOOLS_HEAD = """
    <config>
      <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
        <ipv4PoolGroups>
          <ipv4PoolGroup>
"""

GROUPBINDPOOLS_TAIL = """
            </ipv4PoolGroup>
        </ipv4PoolGroups>
      </brasipv4addrmng>
    </config>
"""

GROUPBINDPOOLS_GETHEAD = """
     <filter type="subtree">
       <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
         <ipv4PoolGroups>
           <ipv4PoolGroup>
"""

GROUPBINDPOOLS_GETTAIL = """
         </ipv4PoolGroup>
       </ipv4PoolGroups>
     </brasipv4addrmng>
  </filter>
"""

GROUPBINDPOOL_CREATE = """
        <groupBindPool nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

GROUPBINDPOOL_DELETE = """
       <groupBindPool nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

GROUPBINDPOOL_MERGE = """
       <groupBindPool nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

POOLGROUPNAME = """
      <poolGroupName>%s</poolGroupName>
"""

POOLNAME = """
      <poolName>%s</poolName>
"""

GROUPBINDPOOLSBEG = """
  <groupBindPools>
"""

GROUPBINDPOOLSEND = """
  </groupBindPools>
"""

GROUPBINDPOOLBEG = """
       <groupBindPool>
"""

GROUPBINDPOOLEND = """
       </groupBindPool>
"""

POOLNAMESTR = """
   <poolName/>
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
        self.poolName = self.module.params['poolName']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.poolGroupName is not None:
            self.proposed["poolGroupName"] = self.poolGroupName
        if self.poolName is not None:
            self.proposed["poolName"] = self.poolName
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
        cfg_str += GROUPBINDPOOLS_HEAD
        if self.operation == 'create':
            if self.poolGroupName:
                cfg_str += POOLGROUPNAME % self.poolGroupName
            cfg_str += GROUPBINDPOOLSBEG
            cfg_str += GROUPBINDPOOL_CREATE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            cfg_str += GROUPBINDPOOLEND
            cfg_str += GROUPBINDPOOLSEND

        if self.operation == 'delete':
            if self.poolGroupName:
                cfg_str += POOLGROUPNAME % self.poolGroupName
            cfg_str += GROUPBINDPOOLSBEG
            cfg_str += GROUPBINDPOOL_DELETE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            cfg_str += GROUPBINDPOOLEND
            cfg_str += GROUPBINDPOOLSEND

        if self.operation == 'merge':
            if self.poolGroupName:
                cfg_str += POOLGROUPNAME % self.poolGroupName
            cfg_str += GROUPBINDPOOLSBEG
            cfg_str += GROUPBINDPOOL_MERGE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            cfg_str += GROUPBINDPOOLEND
            cfg_str += GROUPBINDPOOLSEND

        cfg_str += GROUPBINDPOOLS_TAIL
        # 第二步: 下发配置报文
        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += GROUPBINDPOOLS_GETHEAD
        if self.poolGroupName:
            cfg_str += POOLGROUPNAME % self.poolGroupName
        cfg_str += GROUPBINDPOOLSBEG
        cfg_str += GROUPBINDPOOLBEG
        if self.operation != 'get':
            cfg_str += POOLNAMESTR
        if self.operation == 'get':
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
        cfg_str += GROUPBINDPOOLEND
        cfg_str += GROUPBINDPOOLSEND
        cfg_str += GROUPBINDPOOLS_GETTAIL
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
        attributes_Info["poolNames"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["poolGroupName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "groupBindPools/groupBindPool")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        container_2_info_Table = copy.deepcopy(
                            service_container_Table)
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in ["poolName"]:
                                container_2_info_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["poolNames"].append(
                            container_2_info_Table)

        if len(attributes_Info["poolNames"]) == 0:
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
        poolGroupName=dict(required=False, type='str'),
        poolName=dict(required=False, type='str'),
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
