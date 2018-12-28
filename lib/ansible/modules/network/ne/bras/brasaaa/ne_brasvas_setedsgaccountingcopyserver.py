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
module:ne_brasvas_setedsgaccountingcopyserver
version_added: "2.6"
short_description:  Manage brasvas module setEDSGAccountingCopyServer config rule configuration.
description:
    -  Manage brasvas module setEDSGAccountingCopyServer config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    domainName:
        description:
            -  Specifies the name of a domain.The value can be a string of 1 to 64 characters.
        required: true
    radiusServerName:
        description:
            -  Enables EDSG service accounting copy and configures a RADIUS copy server group.The value can be a string of 1 to 32 characters.
        required: true
    operation:
        description:
            -  Manage the state of the resource.
               if operation is get,the radiusServerName cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create','delete','merge','get']
'''
EXAMPLES = '''

- name:  Manage brasvas module setEDSGAccountingCopyServer config rule configuration.
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

  - name:create a brasvas module  setEDSGAccountingCopyServer config rule
    ne_brasvas_setedsgaccountingcopyserver:
    domainName='123'
    radiusServerName='cbb1'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasvas module  setEDSGAccountingCopyServer config rule
    ne_brasvas_setedsgaccountingcopyserver:
    domainName='123'
    radiusServerName='cbb1'
    operation='delete'
    provider="{{ cli }}"

 -  name:merge a brasvas module  setEDSGAccountingCopyServer config rule
    ne_brasvas_setedsgaccountingcopyserver:
    domainName='123'
    radiusServerName='cbb1'
    operation='merge'
    provider="{{ cli }}"


  - name:get a brasvas module  setEDSGAccountingCopyServer config rule
    ne_brasvas_setedsgaccountingcopyserver:
    domainName='123'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasvas module  setEDSGAccountingCopyServer config rule
    ne_brasvas_setedsgaccountingcopyserver:
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
          "domainName": "123",
          "operation": "get"


    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
            "setEDSGAccountingCopyServers": [
            {
                "domainName": "123",
                "radiusServerName": "cbb"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
          "setEDSGAccountingCopyServers": [
            {
                "domainName": "123",
                "radiusServerName": "cbb"
            }
        ]

    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
SETEDSGACCOUNTINGCOPYSERVER_HEAD = """
   <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <domains>
          <domain>
"""

SETEDSGACCOUNTINGCOPYSERVER_TAIL = """
            </domain>
        </domains>
      </brasvas>
    </config>
"""

SETEDSGACCOUNTINGCOPYSERVER_GETHEAD = """
     <filter type="subtree">
     <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <domains>
        <domain>
"""

SETEDSGACCOUNTINGCOPYSERVER_GETTAIL = """
        </domain>
      </domains>
    </brasvas>
  </filter>
"""

SETEDSGACCOUNTINGCOPYSERVER_CREATE = """
         <setEDSGAccountingCopyServer nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SETEDSGACCOUNTINGCOPYSERVER_DELETE = """
         <setEDSGAccountingCopyServer nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SETEDSGACCOUNTINGCOPYSERVER_MERGE = """
         <setEDSGAccountingCopyServer nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DOMAINNAME = """
    <domainName>%s</domainName>
"""

RADIUSSERVERNAME = """
     <radiusServerName>%s</radiusServerName>
"""

SETEDSGACCOUNTINGCOPYSERVERBEG = """
    <setEDSGAccountingCopyServer>
"""

SETEDSGACCOUNTINGCOPYSERVEREND = """
    </setEDSGAccountingCopyServer>
"""

RADIUSSERVERNAMESTR = """
    <radiusServerName/>
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
        self.domainName = self.module.params['domainName']
        self.radiusServerName = self.module.params['radiusServerName']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.radiusServerName is not None:
            self.proposed["radiusServerName"] = self.radiusServerName
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
        cfg_str += SETEDSGACCOUNTINGCOPYSERVER_HEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        if self.operation == 'create':
            cfg_str += SETEDSGACCOUNTINGCOPYSERVER_CREATE
        if self.operation == 'delete':
            cfg_str += SETEDSGACCOUNTINGCOPYSERVER_DELETE
        if self.operation == 'merge':
            cfg_str += SETEDSGACCOUNTINGCOPYSERVER_MERGE
        if self.radiusServerName:
            cfg_str += RADIUSSERVERNAME % self.radiusServerName
        cfg_str += SETEDSGACCOUNTINGCOPYSERVEREND
        cfg_str += SETEDSGACCOUNTINGCOPYSERVER_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += SETEDSGACCOUNTINGCOPYSERVER_GETHEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        cfg_str += SETEDSGACCOUNTINGCOPYSERVERBEG
        if self.operation != 'get':
            cfg_str += RADIUSSERVERNAMESTR
        if self.operation == 'get':
            if self.radiusServerName:
                cfg_str += RADIUSSERVERNAME % self.radiusServerName
        cfg_str += SETEDSGACCOUNTINGCOPYSERVEREND
        cfg_str += SETEDSGACCOUNTINGCOPYSERVER_GETTAIL

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
        service_container_attributes_Info = root.findall(
            "brasvas/domains/domain")
        attributes_Info["setEDSGAccountingCopyServers"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["domainName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "setEDSGAccountingCopyServer")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in ["radiusServerName"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["setEDSGAccountingCopyServers"].append(
                            service_container_Table)
        if len(attributes_Info["setEDSGAccountingCopyServers"]) == 0:
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
        domainName=dict(required=False, type='str'),
        radiusServerName=dict(required=False, type='str'),
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
