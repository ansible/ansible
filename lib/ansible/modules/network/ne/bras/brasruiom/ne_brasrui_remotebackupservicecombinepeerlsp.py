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
module: ne_brasrui_remotebackupservicecombinepeerlsp
version_added: "2.6"
short_description: Manage brasrui modulecombinepeerlsp config rule configuration.
description:
    - Manage brasrui modulecombinepeerlsp config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    remoteBackupServiceName:
        description:
            -  Specifies an remoteBackupService name. The value can be a string of 1 to 64 characters. The value must start with either
        uppercase letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    peerIpLsp:
        description:
            -  tunnel peer ip. The value can be a string of 1 to 32 characters.
        required: false
    operation:
        description:
            -  Manage the state of the resource.If operation is get,the peerIpLsp cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasrui module combinepeerlsp config rule configuration.
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

  - name:create a brasrui module combinepeerlsp config rule
    ne_brasrui_remotebackupservicecombinepeerlsp:
    remoteBackupServiceName='liuhong1'
    peerIpLsp='3.4.5.6'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasrui module combinepeerlsp config rule
    ne_brasrui_remotebackupservicecombinepeerlsp:
    remoteBackupServiceName='liuhong1'
    peerIpLsp='3.4.5.6'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasrui module combinepeerlsp config rule
    ne_brasrui_remotebackupservicecombinepeerlsp:
    remoteBackupServiceName='liuhong1'
    peerIpLsp='3.4.5.6'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasrui module combinepeerlsp config rule
    ne_brasrui_remotebackupservicecombinepeerlsp:
    remoteBackupServiceName='liuhong1'
    peerIpLsp='3.4.5.6'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasrui module combinepeerlsp config rule
    ne_brasrui_remotebackupservicecombinepeerlsp:
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
        "peerIpLsp": "3.4.5.6",
        "remoteBackupServiceName": "liuhong1"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
           "remoteBackupServiceCombines": [
            {
                "peerIpLsp": "3.4.5.6",
                "remoteBackupServiceName": "liuhong1"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
         "remoteBackupServiceCombines": [
            {
                "peerIpLsp": "3.4.5.6",
                "remoteBackupServiceName": "liuhong1"
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

REMOTEBACKUPSERVICE_GETHEAD = """
    <filter type="subtree">
    <brasrui xmlns="http://www.huawei.com/netconf/vrp/huawei-brasrui">
      <remoteBackupServices>
        <remoteBackupService>
"""

REMOTEBACKUPSERVICE_GETTAIL = """
         </remoteBackupService>
      </remoteBackupServices>
    </brasrui>
  </filter>
"""

REMOTEBACKUPSEVICENAME = """
      <remoteBackupServiceName>%s</remoteBackupServiceName>
"""

RUIPROTECTTUNNELS = """
      <ruiProtectTunnels>%s</ruiProtectTunnels>
"""

REMOTEBACKUPSERVICECOMBINE_CREATE = """
     <remoteBackupServiceCombine nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

REMOTEBACKUPSERVICECOMBINE_DELETE = """
      <remoteBackupServiceCombine nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

REMOTEBACKUPSERVICECOMBINE_MERGE = """
      <remoteBackupServiceCombine nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""
PEERIPLSP = """
      <peerIpLsp>%s</peerIpLsp>
"""

REMOTEBACKUPSERVICECOMBINEBEG = """
      <remoteBackupServiceCombine>
"""

REMOTEBACKUPSERVICECOMBINEEND = """
      </remoteBackupServiceCombine>
"""


GETPEERIPLSD = """
    <peerIpLsp/>
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
        self.peerIpLsp = self.module.params['peerIpLsp']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.remoteBackupServiceName is not None:
            self.proposed["remoteBackupServiceName"] = self.remoteBackupServiceName
        if self.peerIpLsp is not None:
            self.proposed["peerIpLsp"] = self.peerIpLsp
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
        cfg_getstr = ''
        cfg_str += REMOTEBACKUPSERVICE_HEAD
        cfg_getstr += REMOTEBACKUPSERVICE_GETHEAD
        if self.operation == 'create':
            if self.remoteBackupServiceName:
                cfg_str += REMOTEBACKUPSEVICENAME % self.remoteBackupServiceName
            cfg_str += REMOTEBACKUPSERVICECOMBINE_CREATE
            if self.peerIpLsp:
                cfg_str += PEERIPLSP % self.peerIpLsp
            cfg_str += REMOTEBACKUPSERVICECOMBINEEND

        if self.operation == 'delete':
            if self.remoteBackupServiceName:
                cfg_str += REMOTEBACKUPSEVICENAME % self.remoteBackupServiceName
            cfg_str += REMOTEBACKUPSERVICECOMBINE_DELETE
            if self.peerIpLsp:
                cfg_str += PEERIPLSP % self.peerIpLsp
            cfg_str += REMOTEBACKUPSERVICECOMBINEEND

        if self.operation == 'merge':
            if self.remoteBackupServiceName:
                cfg_str += REMOTEBACKUPSEVICENAME % self.remoteBackupServiceName
            cfg_str += REMOTEBACKUPSERVICECOMBINE_MERGE
            if self.peerIpLsp:
                cfg_str += PEERIPLSP % self.peerIpLsp
            cfg_str += REMOTEBACKUPSERVICECOMBINEEND

        if self.operation == 'get':
            logging.info('self.operation get test 1')
            cfg_getstr += REMOTEBACKUPSERVICE_GETTAIL
            cfg_str = ''
            cfg_str = cfg_getstr
        else:
            cfg_str += REMOTEBACKUPSERVICE_TAIL

        # 第二步: 下发配置报文
        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += REMOTEBACKUPSERVICE_GETHEAD
        if self.remoteBackupServiceName:
            cfg_str += REMOTEBACKUPSEVICENAME % self.remoteBackupServiceName
        cfg_str += REMOTEBACKUPSERVICECOMBINEBEG
        if self.operation == 'get':
            if self.peerIpLsp:
                cfg_str += PEERIPLSP % self.peerIpLsp
        if self.operation != 'get':
            cfg_str += GETPEERIPLSD
        cfg_str += REMOTEBACKUPSERVICECOMBINEEND
        cfg_str += REMOTEBACKUPSERVICE_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        logging.info('1111111111111111112')
        logging.info(xml_str)
        logging.info('1111111111111111112')
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
        service_container_attributes_Info = root.findall(
            "brasrui/remoteBackupServices/remoteBackupService")
        attributes_Info["remoteBackupServiceCombines"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["remoteBackupServiceName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "remoteBackupServiceCombine")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in ["peerIpLsp"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                                attributes_Info["remoteBackupServiceCombines"].append(
                                    service_container_Table)

        if len(attributes_Info["remoteBackupServiceCombines"]) == 0:
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
        remoteBackupServiceName=dict(required=False, type='str'),
        peerIpLsp=dict(required=False, type='str'),
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
