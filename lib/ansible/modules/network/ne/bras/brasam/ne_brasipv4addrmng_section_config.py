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
module: ne_brasipv4addrmng_section_config
version_added: "2.6"
short_description: Manage brasipv4addrmng module section config rule configuration.
description:
    -Manage brasipv4addrmng module section config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    poolName:
        description:
            -  Displays the usage of all IPv4 address pools, including the local and remote address pools.the value is a string frong 1 to 128 characters.
        required: true
    poolType:
        description:
            -  Specifies the type of the IP address pool.
        required: false
        default: true
        choices: ['local', 'remote','dynamic']
    ruiType:
        description:
            -  Indicates RUI-slave address pools.
        required: false
        default: false
        choices: ['true','false']
    overlapType:
        description:
            -  Indicates an IP address pool that is used for the vCPE users.
        required: false
        default: false
        choices: ['true','false']
    highIp:
        description:
            -  Specifies the end IP address of the address segment in the dotted decimal format.
        required: true
    sectionIndex:
        description:
            -  Specifies the address segment number.the value is a string frong 0 to 255 int.
        required: true
    lowIp:
        description:
            -  Specifies the start IP address of the address segment in the dotted decimal format.
        required: true
    operation:
        description:
            -  Manage the state of the resource.
               if operation is get,the poolType and ruiType and overlapType cannot take parameters,
                otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create','delete','merge','get']
'''

EXAMPLES = '''

- name: Manage brasipv4addrmng module section config rule configuration.
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

  - name: create a brasipv4addrmng module  section  config rule
    ne_brasbasicaccess_iparptriggerordetect_config:
    poolName='liuhong0619'
    poolType='local'
    ruiType='false'
    overlapType='false'
    sectionIndex=0
    lowIp='1.255.1.2'
    highIp='1.255.1.11'
    operation='create'
    provider: "{{ cli }}"

  - name:delete a brasipv4addrmng module  section  config rule
    ne_brasipv4addrmng_section_config:
    poolName='liuhong0619'
    poolType='local'
    ruiType='false'
    overlapType='false'
    sectionIndex=0
    lowIp='1.255.1.2'
    highIp='1.255.1.11'
    operation='delete'
    provider: "{{ cli }}"

  - name:merge a brasipv4addrmng module  section  config rule
    ne_brasipv4addrmng_section_config:
    poolName='liuhong0619'
    poolType='local'
    ruiType='false'
    overlapType='false'
    sectionIndex=0
    lowIp='1.255.1.2'
    highIp='1.255.1.11'
    operation='merge'
    provider: "{{ cli }}"


  - name: get a brasipv4addrmng module  section  config rule
    ne_brasipv4addrmng_section_config:
    poolName='liuhong0619'
    poolType='local'
    ruiType='false'
    overlapType='false'
    operation='get'
    provider: "{{ cli }}"

  - name: get a brasipv4addrmng module  section  config rule
    ne_brasipv4addrmng_section_config:
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
        "operation": "get",
        "overlapType": "false",
        "poolName": "liuhong0619",
        "poolType": "local",
        "ruiType": "false"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "sections": [
            {
                "highIp": "1.255.1.11",
                "lowIp": "1.255.1.2",
                "overlapType": "false",
                "poolName": "liuhong0619",
                "poolType": "local",
                "ruiType": "false",
                "sectionIndex": "0"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
           "sections": [
            {
                "highIp": "1.255.1.11",
                "lowIp": "1.255.1.2",
                "overlapType": "false",
                "poolName": "liuhong0619",
                "poolType": "local",
                "ruiType": "false",
                "sectionIndex": "0"
            }
        ]
    }
'''


IPV4SECTION_HEAD = """
 <config>
      <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
        <ipv4Pools>
          <ipv4Pool>
"""

IPV4SECTION_TAIL = """
            </ipv4Pool>
        </ipv4Pools>
      </brasipv4addrmng>
    </config>
"""

IPV4SECTION_GETHEAD = """
    <filter type="subtree">
    <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
      <ipv4Pools>
        <ipv4Pool>
"""

IPV4SECTIONT_GETTAIL = """
           <sections>
            <section>
              <sectionIndex/>
              <lowIp/>
              <highIp/>
            </section>
          </sections>
        </ipv4Pool>
      </ipv4Pools>
    </brasipv4addrmng>
  </filter>
"""

IPV4SECTIONT_GETTAILGET = """
        </ipv4Pool>
      </ipv4Pools>
    </brasipv4addrmng>
  </filter>
"""

POOLNAME = """
       <poolName>%s</poolName>"""


POOLTYPE = """
     <poolType>%s</poolType>"""

RUITYPE = """
        <ruiType>%s</ruiType>"""


OVERLAPTYPE = """
      <overlapType>%s</overlapType>"""

SECTIONINDEX = """
      <sectionIndex>%d</sectionIndex>"""

LOWIP = """
      <lowIp>%s</lowIp>"""

HIGHIP = """
      <highIp>%s</highIp>"""

SECTIONSBEG = """
      <sections>
"""

SECTIONSEND = """
       </sections>
"""

SECTIONBEG = """
      <section>
"""

SECTIONEND = """
       </section>
"""

SECTION_CREATE = """
       <section xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="create">"""

SECTION_DELETE = """
       <section xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete">"""

SECTION_MERGE = """
        <section xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="merge">"""


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
        self.poolName = self.module.params['poolName']
        self.poolType = self.module.params['poolType']
        self.ruiType = self.module.params['ruiType']
        self.overlapType = self.module.params['overlapType']
        self.sectionIndex = self.module.params['sectionIndex']
        self.lowIp = self.module.params['lowIp']
        self.highIp = self.module.params['highIp']
        self.operation = self.module.params['operation']
        logging.info("sectionIndex test1")
        logging.info(self.sectionIndex)
        if self.operation != 'get' and self.ruiType is None:
            self.ruiType = 'false'
        if self.operation != 'get' and self.overlapType is None:
            self.overlapType = 'false'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.poolName is not None:
            self.proposed["poolName"] = self.poolName
        if self.poolType is not None:
            self.proposed["poolType"] = self.poolType
        if self.ruiType is not None:
            self.proposed["ruiType"] = self.ruiType
        if self.overlapType is not None:
            self.proposed["overlapType"] = self.overlapType
        if self.sectionIndex is not None:
            self.proposed["sectionIndex"] = self.sectionIndex
        if self.lowIp is not None:
            self.proposed["lowIp"] = self.lowIp
        if self.highIp is not None:
            self.proposed["highIp"] = self.highIp
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
        logging.info('fffffffffffffffffffff2')
        logging.info(self.poolName)
        logging.info(self.poolType)
        logging.info(self.ruiType)
        logging.info(self.overlapType)
        logging.info(self.sectionIndex)
        logging.info(self.lowIp)
        logging.info(self.highIp)
        logging.info(self.operation)
        cfg_str += IPV4SECTION_HEAD
        if self.poolName:
            cfg_str += POOLNAME % self.poolName
        if self.poolType:
            cfg_str += POOLTYPE % self.poolType
        if self.ruiType:
            cfg_str += RUITYPE % self.ruiType
        if self.overlapType:
            cfg_str += OVERLAPTYPE % self.overlapType
        cfg_str += SECTIONSBEG
        if self.operation == 'create':
            cfg_str += SECTION_CREATE
        if self.operation == 'merge':
            cfg_str += SECTION_MERGE
        if self.operation == 'delete':
            cfg_str += SECTION_DELETE
        if self.sectionIndex is not None:
            cfg_str += SECTIONINDEX % self.sectionIndex
        if self.lowIp is not None:
            cfg_str += LOWIP % self.lowIp
        if self.highIp is not None:
            cfg_str += HIGHIP % self.highIp
        cfg_str += SECTIONEND
        cfg_str += SECTIONSEND
        cfg_str += IPV4SECTION_TAIL

        # 第二步: 下发配置报文
        logging.info('fffffffffffffffffffff')
        logging.info(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += IPV4SECTION_GETHEAD
        if self.poolName:
            cfg_str += POOLNAME % self.poolName
        if self.poolType:
            cfg_str += POOLTYPE % self.poolType
        if self.ruiType:
            cfg_str += RUITYPE % self.ruiType
        if self.overlapType:
            cfg_str += OVERLAPTYPE % self.overlapType
        if self.operation != 'get':
            cfg_str += IPV4SECTIONT_GETTAIL
        if self.operation == 'get':
            cfg_str += SECTIONSBEG
            cfg_str += SECTIONBEG
            if self.sectionIndex is not None:
                cfg_str += SECTIONINDEX % self.sectionIndex
            if self.lowIp is not None:
                cfg_str += LOWIP % self.lowIp
            if self.highIp is not None:
                cfg_str += HIGHIP % self.highIp
            cfg_str += SECTIONEND
            cfg_str += SECTIONSEND
            cfg_str += IPV4SECTIONT_GETTAILGET

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
            "brasipv4addrmng/ipv4Pools/ipv4Pool")
        attributes_Info["sections"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in [
                            "poolName", "poolType", "ruiType", "overlapType"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "sections/section")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "sectionIndex", "lowIp", "highIp"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["sections"].append(
                            service_container_Table)

        if len(attributes_Info["sections"]) == 0:
            attributes_Info.clear()

        # 解析5: 返回数据
        return attributes_Info

    def check_params(self):
        if ((self.poolType is not None) or (self.ruiType is not None) or (
                self.overlapType is not None)) and self.operation == 'get':
            self.module.fail_json(
                msg='Error: This operation is not supported.')

    def run(self):
        # 第一步: 检测输入
        self.check_params()
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
        poolName=dict(required=False, type='str'),
        poolType=dict(required=False, choices=['local', 'remote', 'dynamic']),
        ruiType=dict(required=False, choices=['true', 'false']),
        overlapType=dict(required=False, choices=['true', 'false']),
        sectionIndex=dict(required=False, type='int'),
        lowIp=dict(required=False, type='str'),
        highIp=dict(required=False, type='str'),
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
