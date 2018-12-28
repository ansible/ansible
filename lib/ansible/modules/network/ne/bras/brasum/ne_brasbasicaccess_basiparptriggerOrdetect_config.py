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
module: ne_brasbasicaccess_basiparptriggerOrdetect_config
version_added: "2.6"
short_description:  Manage brasbasicaccess module ipArpTriggerOrDetect config rule configuration.
description:
    -  Manage brasbasicaccess module ipArpTriggerOrDetect config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    interfaceName:
        description:
            -  Specifies an interface name the value is a string,which lenth from 1 to 31.
        required: true
    detectionNumber:
        description:
            -  Specifies the number of times for detecting users by sending ARP probe packets,the value can be a int from 2 to 120.
        required: true
    detectionTime:
        description:
            -  Specifies the interval for detecting users by sending ARP probe packets.the value can be a int from 0 to 1800.
        required: true
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the detectionNumber and detectionTime cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create','delete','merge','get']
'''
EXAMPLES = '''

- name:  Manage brasbasicaccess module ipArpTriggerOrDetect config rule configuration.
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

  - name:create a brasbasicaccess module  ipArpTriggerOrDetect config rule
    ne_brasbasicaccess_basiparptriggerOrdetect_config:
    interfaceName='GigabitEthernet0/3/1'
    detectionNumber=6
    detectionTime=22
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasbasicaccess module  ipArpTriggerOrDetect config rule
    ne_brasbasicaccess_basiparptriggerOrdetect_config:
    interfaceName='GigabitEthernet0/3/1'
    detectionNumber=6
    detectionTime=22
    operation='delete'
    provider="{{ cli }}"

  - name:merge a brasbasicaccess module  ipArpTriggerOrDetect config rule
    ne_brasbasicaccess_basiparptriggerOrdetect_config:
    interfaceName='GigabitEthernet0/3/1'
    detectionNumber=6
    detectionTime=22
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module  ipArpTriggerOrDetect config rule
    ne_brasbasicaccess_basiparptriggerOrdetect_config:
    interfaceName='GigabitEthernet0/3/1'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasbasicaccess module  ipArpTriggerOrDetect config rule
    ne_brasbasicaccess_basiparptriggerOrdetect_config:
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
        "detectionNumber": 6,
        "detectionTime": 23,
        "interfaceName": "GigabitEthernet1/0/1",
        "operation": "delete"

    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
            "ipArpTriggerOrDetects": [
            {
                "detectionNumber": "6",
                "detectionTime": "23",
                "interfaceName": "GigabitEthernet1/0/1"
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
IPARPTRIGGERORDETECT__HEAD = """
  <config>
      <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
        <basInterfaces>
          <basInterface>
"""

IPARPTRIGGERORDETECT_TAIL = """
            </basInterface>
        </basInterfaces>
      </brasbasicaccess>
    </config>
"""

IPARPTRIGGERORDETECT__GETHEAD = """
   <filter type="subtree">
    <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
      <basInterfaces>
        <basInterface>
"""

IPARPTRIGGERORDETECT_GETTAIL = """
        </basInterface>
      </basInterfaces>
    </brasbasicaccess>
  </filter>
"""

IPARPTRIGGERORDETECT_CREATE = """
       <ipArpTriggerOrDetect nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

IPARPTRIGGERORDETECT_MERGE = """
        <ipArpTriggerOrDetect nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

INTFACENAME = """
    <interfaceName>%s</interfaceName>
"""
DETECTIONNUMBER = """
       <detectionNumber>%d</detectionNumber>
"""

DETECTIONTIME = """
    <detectionTime>%d</detectionTime>
"""

IPARPTRIGGERORDETECTBEG = """
    <ipArpTriggerOrDetect>
"""
IPARPTRIGGERORDETECTEND = """
  </ipArpTriggerOrDetect>
"""

DETECTTIMEGET = """
  <detectionTime/>
"""

DETECTIONNUMBERGET = """
  <detectionNumber/>
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
        self.interfaceName = self.module.params['interfaceName']
        self.detectionNumber = self.module.params['detectionNumber']
        self.detectionTime = self.module.params['detectionTime']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.interfaceName is not None:
            self.proposed["interfaceName"] = self.interfaceName
        if self.detectionNumber is not None:
            self.proposed["detectionNumber"] = self.detectionNumber
        if self.detectionTime is not None:
            self.proposed["detectionTime"] = self.detectionTime
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
        cfg_str += IPARPTRIGGERORDETECT__HEAD
        if self.interfaceName is not None:
            cfg_str += INTFACENAME % self.interfaceName
        if self.operation == 'delete':
            self.detectionNumber = 5
            self.detectionTime = 30
            self.operation = 'merge'
        if self.operation == 'create':
            cfg_str += IPARPTRIGGERORDETECT_CREATE
        if self.operation == 'merge':
            cfg_str += IPARPTRIGGERORDETECT_MERGE
        if self.detectionNumber is not None:
            cfg_str += DETECTIONNUMBER % self.detectionNumber
        if self.detectionTime is not None:
            cfg_str += DETECTIONTIME % self.detectionTime
        cfg_str += IPARPTRIGGERORDETECTEND
        cfg_str += IPARPTRIGGERORDETECT_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += IPARPTRIGGERORDETECT__GETHEAD
        if self.interfaceName is not None:
            cfg_str += INTFACENAME % self.interfaceName
        cfg_str += IPARPTRIGGERORDETECTBEG
        if self.operation != 'get':
            cfg_str += DETECTIONNUMBERGET
            cfg_str += DETECTTIMEGET
        if self.operation == 'get':
            if self.detectionNumber is not None:
                cfg_str += DETECTIONNUMBER % self.detectionNumber
            if self.detectionTime is not None:
                cfg_str += DETECTIONTIME % self.detectionTime
        cfg_str += IPARPTRIGGERORDETECTEND
        cfg_str += IPARPTRIGGERORDETECT_GETTAIL

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
            "brasbasicaccess/basInterfaces/basInterface")
        attributes_Info["ipArpTriggerOrDetects"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["interfaceName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "ipArpTriggerOrDetect")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "detectionNumber", "detectionTime"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["ipArpTriggerOrDetects"].append(
                            service_container_Table)
        if len(attributes_Info["ipArpTriggerOrDetects"]) == 0:
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
        interfaceName=dict(required=False, type='str'),
        detectionNumber=dict(required=False, type='int'),
        detectionTime=dict(required=False, type='int'),
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
