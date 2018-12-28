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
module: ne_brasbasicaccess_domainauthorization
version_added: "2.6"
short_description:  Manage brasbasicaccess module domainAuthorization config rule configuration.
description:
    -  Manage brasbasicaccess module domainAuthorization config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    domainName:
        description:
            -  Specifies the name of a domain.The value can be a string of 1 to 64 characters.
        required: true
    arpDetectRetransmitTime:
        description:
            -  Indicates the number of times for detecting users by sending ARP packets.the value can be a int from 2 to 120.
        required: true
    arpDetectInterval:
        description:
            -  Indicates the interval for detecting users by sending ARP packets.the value can be a int from 0 to 1800.
        required: true
    operation:
        description:
            -  Manage the state of the resource.
               if operation is get,the arpDetectRetransmitTime and arpDetectInterval cannot take parameters,
               otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create','delete','merge','get']
'''
EXAMPLES = '''

- name:  Manage brasbasicaccess module domainAuthorization config rule configuration.
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

  - name:create a brasbasicaccess module  domainAuthorization config rule
    ne_brasbasicaccess_domainauthorization:
    domainName='123'
    arpDetectRetransmitTime=5
    arpDetectInterval=0
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module  domainAuthorization config rule
    ne_brasbasicaccess_domainauthorization:
    domainName='123'
    arpDetectRetransmitTime=5
    arpDetectInterval=0
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module  domainAuthorization config rule
    ne_brasbasicaccess_domainauthorization:
    domainName='123'
    arpDetectRetransmitTime=5
    arpDetectInterval=0
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module  domainAuthorization config rule
    ne_brasbasicaccess_domainauthorization:
    domainName='123'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module  domainAuthorization config rule
    ne_brasbasicaccess_domainauthorization:
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
        "arpDetectInterval": 0,
        "arpDetectRetransmitTime": 5,
        "domainName": "123",
        "operation": "create"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
            "domainAuthorizations": [
            {
                "arpDetectInterval": "0",
                "domainName": "123"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
           "domainAuthorizations": [
            {
                "arpDetectInterval": "0",
                "arpDetectRetransmitTime": "5",
                "domainName": "123"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
DOMAINAUTHORIZATION_HEAD = """
   <config>
      <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
        <domains>
          <domain>
"""

DOMAINAUTHORIZATION_TAIL = """
              </domain>
        </domains>
      </brasbasicaccess>
    </config>
"""

DOMAINAUTHORIZATION_GETHEAD = """
    <filter type="subtree">
    <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
      <domains>
        <domain>
"""

DOMAINAUTHORIZATION_GETTAIL = """
           </domain>
       </domains>
     </brasbasicaccess>
  </filter>
"""

DOMAINAUTHORIZATION_CREATE = """
        <domainAuthorization nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DOMAINAUTHORIZATION_DELETE = """
        <domainAuthorization nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DOMAINAUTHORIZATION_MERGE = """
        <domainAuthorization nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DOMAINNAME = """
    <domainName>%s</domainName>
"""
ARPDETECTRETRANSMITTIME = """
      <arpDetectRetransmitTime>%d</arpDetectRetransmitTime>
"""

ARPDETECTINTERVAL = """
    <arpDetectInterval>%d</arpDetectInterval>
"""

DOMAINAUTHORIZATIONBEG = """
    <domainAuthorization>
"""
DOMAINAUTHORIZATIONEND = """
  </domainAuthorization>
"""

ARPDETECTRETRANSMITTIMESTR = """
    <arpDetectRetransmitTime/>
"""

ARPDETECTINTERVALSTR = """
    <arpDetectInterval/>
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
        self.arpDetectRetransmitTime = self.module.params['arpDetectRetransmitTime']
        self.arpDetectInterval = self.module.params['arpDetectInterval']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.arpDetectRetransmitTime is not None:
            self.proposed["arpDetectRetransmitTime"] = self.arpDetectRetransmitTime
        if self.arpDetectInterval is not None:
            self.proposed["arpDetectInterval"] = self.arpDetectInterval
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
        cfg_str += DOMAINAUTHORIZATION_HEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        if self.operation == 'create':
            cfg_str += DOMAINAUTHORIZATION_CREATE
        if self.operation == 'delete':
            cfg_str += DOMAINAUTHORIZATION_DELETE
        if self.operation == 'merge':
            cfg_str += DOMAINAUTHORIZATION_MERGE
        if self.arpDetectRetransmitTime:
            cfg_str += ARPDETECTRETRANSMITTIME % self.arpDetectRetransmitTime
        if self.arpDetectInterval:
            cfg_str += ARPDETECTINTERVAL % self.arpDetectInterval
        cfg_str += DOMAINAUTHORIZATIONEND
        cfg_str += DOMAINAUTHORIZATION_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += DOMAINAUTHORIZATION_GETHEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        cfg_str += DOMAINAUTHORIZATIONBEG
        if self.operation != 'get':
            cfg_str += ARPDETECTRETRANSMITTIMESTR
            cfg_str += ARPDETECTINTERVALSTR
        if self.operation == 'get':
            if self.arpDetectRetransmitTime:
                cfg_str += ARPDETECTRETRANSMITTIME % self.arpDetectRetransmitTime
            if self.arpDetectInterval:
                cfg_str += ARPDETECTINTERVAL % self.arpDetectInterval
        cfg_str += DOMAINAUTHORIZATIONEND
        cfg_str += DOMAINAUTHORIZATION_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasbasicaccess/domains/domain")
        attributes_Info["domainAuthorizations"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["domainName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "domainAuthorization")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "arpDetectRetransmitTime", "arpDetectInterval"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["domainAuthorizations"].append(
                            service_container_Table)
        if len(attributes_Info["domainAuthorizations"]) == 0:
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
        arpDetectRetransmitTime=dict(required=False, type='int'),
        arpDetectInterval=dict(required=False, type='int'),
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
