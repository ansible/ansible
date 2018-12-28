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
module: ne_brasrui_ruiippools_config
version_added: "2.6"
short_description:  Manage Brasrui module ip-pool rule configuration.
description:
    -  Manage Brasrui module ip-pool rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    remoteBackupServiceName:
        description:
            -  Specifies an remoteBackupService name. The value can be a string of 1 to 64 characters. The value must start with either
            uppercase letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    poolName:
        description:
            -  Specifies the name or ID of the ip-pool group. The value can be a string of 1 to 64 characters. The value must start with
            either uppercase letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    metric:
        description:
            -  Cost of ip pool network route. The value can be a integer number.
        required: false
    operation:
        description:
            -  Manage the state of the resource.If operation is get,the metric cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Brasrui module ip-pool rule configuration test.
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

  - name:Create a Brasrui module ip-pool rule
    ne_brasrui_ruiippools_config:
    remoteBackupServiceName='liuhong2',
    poolName='liuhong1'
    metric=40
    operation='create'
    provider="{{ cli }}"

  - name:Delete a Brasrui module ip-pool rule
    ne_brasrui_ruiippools_config:
    remoteBackupServiceName='liuhong2',
    poolName='liuhong1'
    metric=40
    operation='delete'
    provider="{{ cli }}"

  - name:Merge a Brasrui module ip-pool rule
    ne_brasrui_ruiippools_config:
    remoteBackupServiceName='liuhong2',
    poolName='liuhong1'
    metric=40
    operation='merge'
    provider="{{ cli }}"

 - name:get a Brasrui module ip-pool rule
    ne_brasrui_ruiippools_config:
    remoteBackupServiceName='liuhong2',
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
        "metric": 40,
        "operation": "create",
        "poolName": "liuhong1",
        "remoteBackupServiceName": "liuhong2"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
           "ruiIPPools": [
            {
                "metric": "40",
                "poolName": "liuhong1",
                "remoteBackupServiceName": "liuhong2"
            }
        ]

    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
         "ruiIPPools": [
            {
                "metric": "40",
                "poolName": "liuhong1",
                "remoteBackupServiceName": "liuhong2"
            }
        ]

    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
REMOTEBACKUPSERVICE_HEAD = """
    <config>
      <brasrui xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui">
        <remoteBackupServices>
          <remoteBackupService>
"""

REMOTEBACKUPSERVICE_TAIL = """
          </remoteBackupService>
        </remoteBackupServices>
      </brasrui>
    </config>
"""

RUIIPOOL_GETHEAD = """
    <filter type="subtree">
      <brasrui xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui">
        <remoteBackupServices>
          <remoteBackupService>
"""

RUIIPOOL_GETTAIL = """
           </remoteBackupService>
        </remoteBackupServices>
      </brasrui>
    </filter>
"""
REMOTEBACKUPSEVICENAME = """
      <remoteBackupServiceName>%s</remoteBackupServiceName>
"""

RUIIPPOOL_CREATE = """
      <ruiIPPool xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">
"""

RUIIPOOL_DELETE = """
      <ruiIPPool xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete">
"""

RUIIPOOL_MERGE = """
     <ruiIPPool xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="merge">
"""
POOLNAME = """
      <poolName>%s</poolName>
"""

METRIC = """
      <metric>%d</metric>
"""

RUIIPPOOLSBEG = """
      <ruiIPPools>
"""

RUIIPOOLSEND = """
      </ruiIPPools>
"""

RUIIPOOLBEG = """
      <ruiIPPool>
"""
RUIIPOOLEND = """
      </ruiIPPool>
"""

POOLNAMEEND = """
    <poolName/>
"""

METRICEND = """
    <metric/>
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
        self.remoteBackupServiceName = self.module.params['remoteBackupServiceName']
        self.poolName = self.module.params['poolName']
        self.metric = self.module.params['metric']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.remoteBackupServiceName is not None:
            self.proposed["remoteBackupServiceName"] = self.remoteBackupServiceName
        if self.poolName is not None:
            self.proposed["poolName"] = self.poolName
        if self.metric is not None:
            self.proposed["metric"] = self.metric
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
        self.changed = True
        cfg_str = ''
        cfg_str += REMOTEBACKUPSERVICE_HEAD
        if self.operation == 'create':
            if self.remoteBackupServiceName:
                cfg_str += REMOTEBACKUPSEVICENAME % self.remoteBackupServiceName
            cfg_str += RUIIPPOOLSBEG
            cfg_str += RUIIPPOOL_CREATE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.metric is not None:
                cfg_str += METRIC % self.metric
            cfg_str += RUIIPOOLEND
            cfg_str += RUIIPOOLSEND

        if self.operation == 'delete':
            if self.remoteBackupServiceName:
                cfg_str += REMOTEBACKUPSEVICENAME % self.remoteBackupServiceName
            cfg_str += RUIIPPOOLSBEG
            cfg_str += RUIIPOOL_DELETE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.metric:
                cfg_str += METRIC % self.metric
            cfg_str += RUIIPOOLEND
            cfg_str += RUIIPOOLSEND

        if self.operation == 'merge':
            if self.remoteBackupServiceName:
                cfg_str += REMOTEBACKUPSEVICENAME % self.remoteBackupServiceName
            cfg_str += RUIIPPOOLSBEG
            cfg_str += RUIIPOOL_MERGE
            if self.poolName:
                cfg_str += POOLNAME % self.poolName
            if self.metric:
                cfg_str += METRIC % self.metric
            cfg_str += RUIIPOOLEND
            cfg_str += RUIIPOOLSEND

        cfg_str += REMOTEBACKUPSERVICE_TAIL
        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += RUIIPOOL_GETHEAD
        if self.remoteBackupServiceName:
            cfg_str += REMOTEBACKUPSEVICENAME % self.remoteBackupServiceName
        cfg_str += RUIIPPOOLSBEG
        cfg_str += RUIIPOOLBEG
        if self.poolName:
            cfg_str += POOLNAME % self.poolName
        if self.operation == 'get':
            if self.metric:
                cfg_str += METRIC % self.metric
        if self.operation != 'get':
            cfg_str += METRICEND
        cfg_str += RUIIPOOLEND
        cfg_str += RUIIPOOLSEND
        cfg_str += RUIIPOOL_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasrui/remoteBackupServices/remoteBackupService")
        attributes_Info["ruiIPPools"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["remoteBackupServiceName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "ruiIPPools/ruiIPPool")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["poolName",
                                                   "metric"]:
                                container_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["ruiIPPools"].append(
                            container_info_Table)

        # 解析5: 返回数据
        if len(attributes_Info["ruiIPPools"]) == 0:
            attributes_Info.clear()
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
        remoteBackupServiceName=dict(required=False, type='str'),
        poolName=dict(required=False, type='str'),
        metric=dict(required=False, type='int'),
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
