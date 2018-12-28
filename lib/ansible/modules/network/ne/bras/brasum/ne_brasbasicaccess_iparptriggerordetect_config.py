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
module: ne_brasbasicaccess_iparptriggerordetect_config
version_added: "2.6"
short_description: Manage brasbasicaccess module iparptriggerordetect config rule configuration.
description:
    - Manage brasbasicaccess module iparptriggerordetect config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    interfaceName:
        description:
            -  The command creates a BAS interface and displays the BAS interface view.
        required: true
    ipTriggerEnable:
        description:
            -  Enables IP packet trigger on the BAS interface.
        required: false
        default: false
        choices: ['true','false']
    operation:
        description:
            -  Manage the state of the resource.
               if operation is get,the ipTriggerEnable cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create','delete','merge','get']
'''

EXAMPLES = '''

- name: Manage brasbasicaccess module iparptriggerordetect config rule configuration.
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

  - name: create a brasbasicaccess module  ipTriggerEnable  config rule
    ne_brasbasicaccess_iparptriggerordetect_config:
    interfaceName='Eth-Trunk1.20'
    ipTriggerEnable='true'
    operation='create'
    provider: "{{ cli }}"

  - name: delete a brasbasicaccess module  ipTriggerEnable  config rule
    ne_brasbasicaccess_iparptriggerordetect_config:
    interfaceName='Eth-Trunk1.20'
    ipTriggerEnable='true'
    operation='delete'
    provider: "{{ cli }}"

  - name: merge a brasbasicaccess module  ipTriggerEnable  config rule
    ne_brasbasicaccess_iparptriggerordetect_config:
    interfaceName='Eth-Trunk1.20'
    ipTriggerEnable='true'
    operation='merge'
    provider: "{{ cli }}"

  - name: get a brasbasicaccess module  ipTriggerEnable  config rule
    ne_brasbasicaccess_iparptriggerordetect_config:
    interfaceName='Eth-Trunk1.20'
    operation='get'
    provider: "{{ cli }}"

  - name: get a brasbasicaccess module  ipTriggerEnable  config rule
    ne_brasbasicaccess_iparptriggerordetect_config:
    operation='get'
    provider: "{{ cli }}"
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
        "interfaceName": "Eth-Trunk1.20",
        "ipTriggerEnable": "true",
        "operation": "merge"


    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "ipArpTriggerOrDetects": [
            {
                "interfaceName": "Eth-Trunk1.20",
                "ipTriggerEnable": "false"
            }
        ]



    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
           "ipArpTriggerOrDetects": [
            {
                "interfaceName": "Eth-Trunk1.20",
                "ipTriggerEnable": "true"
            }
        ]

    }
'''


IPARPTRIGGERORDETECT_HEAD = """
 <config>
      <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
        <basInterfaces>
          <basInterface>
"""

IPARPTRIGGERORDETECT_TAIL = """
           </ipArpTriggerOrDetect>
          </basInterface>
        </basInterfaces>
      </brasbasicaccess>
    </config>
"""

IPARPTRIGGERORDETECT_GETHEAD = """
     <filter type="subtree">
    <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
      <basInterfaces>
        <basInterface>
"""

IPARPTRIGGERORDETECT_GETTAIL = """
           <ipArpTriggerOrDetect>
            <ipTriggerEnable/>
          </ipArpTriggerOrDetect>
        </basInterface>
      </basInterfaces>
    </brasbasicaccess>
  </filter>
"""

IPARPTRIGGERORDETECT_GETTAILGET = """
          </ipArpTriggerOrDetect>
        </basInterface>
      </basInterfaces>
    </brasbasicaccess>
  </filter>
"""
IPARPTRIGGERORDETECTBEG = """
    <ipArpTriggerOrDetect>
"""
INTERFACENAME = """
       <interfaceName>%s</interfaceName>"""


IPTRIGGERENABLE = """
      <ipTriggerEnable>%s</ipTriggerEnable>"""

IPARPTRIGGERORDETECT_CREATE = """
       <ipArpTriggerOrDetect nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

IPARPTRIGGERORDETECT_DELETE = """
       <ipArpTriggerOrDetect nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

IPARPTRIGGERORDETECT_MERGE = """
        <ipArpTriggerOrDetect nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

        # module input info
        self.interfaceName = self.module.params['interfaceName']
        self.ipTriggerEnable = self.module.params['ipTriggerEnable']
        self.operation = self.module.params['operation']

        if self.operation != 'get' and self.ipTriggerEnable is None:
            self.ipTriggerEnable = 'false'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.interfaceName is not None:
            self.proposed["interfaceName"] = self.interfaceName
        if self.ipTriggerEnable is not None:
            self.proposed["ipTriggerEnable"] = self.ipTriggerEnable
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        """get config rpc string"""
        # 第一步, 构造配置报文
        cfg_str = ''
        self.changed = True
        cfg_str += IPARPTRIGGERORDETECT_HEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.operation == 'create':
            cfg_str += IPARPTRIGGERORDETECT_CREATE
        if self.operation == 'merge':
            cfg_str += IPARPTRIGGERORDETECT_MERGE
        if self.operation == 'delete':
            cfg_str += IPARPTRIGGERORDETECT_DELETE
        if self.ipTriggerEnable:
            cfg_str += IPTRIGGERENABLE % self.ipTriggerEnable
        cfg_str += IPARPTRIGGERORDETECT_TAIL

        # 第二步: 下发配置报文
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += IPARPTRIGGERORDETECT_GETHEAD
        if self.interfaceName:
            cfg_str += INTERFACENAME % self.interfaceName
        if self.operation != 'get':
            cfg_str += IPARPTRIGGERORDETECT_GETTAIL
        if self.operation == 'get':
            cfg_str += IPARPTRIGGERORDETECTBEG
            if self.ipTriggerEnable:
                cfg_str += IPTRIGGERENABLE % self.ipTriggerEnable
            cfg_str += IPARPTRIGGERORDETECT_GETTAILGET

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
                            if leaf_combine_Info.tag in ["ipTriggerEnable"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["ipArpTriggerOrDetects"].append(
                            service_container_Table)

        if len(attributes_Info["ipArpTriggerOrDetects"]) == 0:
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
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    argument_spec = dict(
        interfaceName=dict(required=False, type='str'),
        ipTriggerEnable=dict(required=False, choices=['true', 'false']),
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
