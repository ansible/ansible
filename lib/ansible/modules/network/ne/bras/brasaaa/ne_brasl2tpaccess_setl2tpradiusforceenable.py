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
module:ne_brasl2tpaccess_setl2tpradiusforceenable
version_added: "2.6"
short_description:  Manage brasl2tpaccess module setl2tpradiusforceenable config rule configuration.
description:
    -  Manage brasl2tpaccess module setl2tpradiusforceenable config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    domainName:
        description:
            -  Specifies the name of a domain.The value can be a string of 1 to 64 characters.
        required: true
    setL2TPRadiusForceEnable:
        description:
            -  Specifies the L2TP attributes delivered by the RADIUS server for the domain users.
        required: true
        default: false
        choices: ['true','false']
    operation:
        description:
            -  Manage the state of the resource.
               if operation is get,the setL2TPRadiusForceEnable cannot take parameters,
                otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: merge
        choices: ['merge','get']
'''
EXAMPLES = '''

- name:  Manage brasl2tpaccess module setL2TPRadiusForceEnable config rule configuration.
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


 -  name:merge a brasl2tpaccess module  setL2TPRadiusForceEnable  config rule
    ne_brasl2tpaccess_setl2tpradiusforceenable:
    domainName='123'
    setL2TPRadiusForceEnable='true'
    operation='merge'
    provider="{{ cli }}"


  - name:get a brasl2tpaccess module  setL2TPRadiusForceEnable  config rule
    ne_brasl2tpaccess_setl2tpradiusforceenable:
    domainName='123'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasvas module  setEDSGAccountingCopyServer config rule
    ne_brasl2tpaccess_setl2tpradiusforceenable:
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
        "operation": "get",
        "setL2TPRadiusForceEnable": "false"


    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
            "setL2TPRadiusForces": [
            {
                "domainName": "123",
                "setL2TPRadiusForceEnable": "true"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
          "setL2TPRadiusForces": [
            {
                "domainName": "123",
                "setL2TPRadiusForceEnable": "true"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
SETL2TPRADIUSFORCEENABLE_HEAD = """
   <config>
      <brasl2tpaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasl2tpaccess">
        <domains>
          <domain>
"""

SETL2TPRADIUSFORCEENABLE_TAIL = """
            </domain>
        </domains>
      </brasl2tpaccess>
    </config>
"""

SETL2TPRADIUSFORCEENABLE_GETHEAD = """
    <filter type="subtree">
     <brasl2tpaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasl2tpaccess">
       <domains>
         <domain>
"""

SETL2TPRADIUSFORCEENABLE_GETTAIL = """
        </domain>
      </domains>
    </brasl2tpaccess>
  </filter>
"""

SETL2TPRADIUSFORCE_MERGE = """
          <setL2TPRadiusForce nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DOMAINNAME = """
    <domainName>%s</domainName>
"""

SETL2TPRADIUSFORCEENABLE = """
     <setL2TPRadiusForceEnable>%s</setL2TPRadiusForceEnable>
"""

SETL2TPRADIUSFORCEBEG = """
    <setL2TPRadiusForce>
"""

SETL2TPRADIUSFORCEEND = """
    </setL2TPRadiusForce>
"""

SETL2TPRADIUSFORCEENABLESTR = """
    <setL2TPRadiusForceEnable/>
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
        self.setL2TPRadiusForceEnable = self.module.params['setL2TPRadiusForceEnable']
        self.operation = self.module.params['operation']

        if self.operation != 'get' and self.setL2TPRadiusForceEnable is None:
            self.setL2TPRadiusForceEnable = 'false'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.setL2TPRadiusForceEnable is not None:
            self.proposed["setL2TPRadiusForceEnable"] = self.setL2TPRadiusForceEnable
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
        cfg_str += SETL2TPRADIUSFORCEENABLE_HEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        if self.operation == 'merge':
            cfg_str += SETL2TPRADIUSFORCE_MERGE
        if self.setL2TPRadiusForceEnable:
            cfg_str += SETL2TPRADIUSFORCEENABLE % self.setL2TPRadiusForceEnable
        cfg_str += SETL2TPRADIUSFORCEEND
        cfg_str += SETL2TPRADIUSFORCEENABLE_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += SETL2TPRADIUSFORCEENABLE_GETHEAD
        if self.domainName:
            cfg_str += DOMAINNAME % self.domainName
        cfg_str += SETL2TPRADIUSFORCEBEG
        if self.operation != 'get':
            cfg_str += SETL2TPRADIUSFORCEENABLESTR
        if self.operation == 'get':
            if self.setL2TPRadiusForceEnable:
                cfg_str += SETL2TPRADIUSFORCEENABLE % self.setL2TPRadiusForceEnable
        cfg_str += SETL2TPRADIUSFORCEEND
        cfg_str += SETL2TPRADIUSFORCEENABLE_GETTAIL

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
            "brasl2tpaccess/domains/domain")
        attributes_Info["setL2TPRadiusForces"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["domainName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "setL2TPRadiusForce")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "setL2TPRadiusForceEnable"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["setL2TPRadiusForces"].append(
                            service_container_Table)
        if len(attributes_Info["setL2TPRadiusForces"]) == 0:
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
        setL2TPRadiusForceEnable=dict(
            required=False, choices=[
                'true', 'false']),
        operation=dict(
            required=False,
            choices=[
                'merge',
                'get'],
            default='merge'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
