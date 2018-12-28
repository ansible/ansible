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
module: ne_brasipv6addrmng_ipv6prefixs_lifetime_config
version_added: "2.6"
short_description: Manage brasipv6addrmng module lifetime config rule configuration.
description:
    - Manage brasipv6addrmng module lifetime config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    prefixName:
        description:
            - Specifies the name of the IPv6 prefix pool to be created. The value can be a string of 1 to 64 characters.
            The value must start with either uppercase letters A to Z or lowercase letters a to z and be a combination of letters,
            digits, hyphens (-), and underscores (_).
        required: true
    preferDay:
        description:
            - prefer day. The value can be a  integer of 0 to 999.
        required: true
    preferHour:
        description:
            - prefer Hour. The value can be a  integer of 0 to 23.
        required: true
    preferMinute:
        description:
            - prefer minute. The value can be a  integer of 0 to 59.
        required: true
    validDay:
        description:
            - valid day. The value can be a  integer of 0 to 999.
        required: true
    validHour:
        description:
            - valid hour. The value can be a  integer of 0 to 23.
        required: true
    validMinute:
        description:
            - valid minute. The value can be a  integer of 0 to 59.
        required: true
    preferInfiniteEnable:
        description:
            - prefer infinite enable. The value can be a string of true or false.
            Preferinfiniteenable and Validinfinteenable must both configure true or False, and when True is configured,
            preferday/preferhour/preferminute/validday/ Validhour/validminute parameters are not configurable.
        required: false
        default: false
        choices: ['true','false']
    validInfinteEnable:
        description:
            - valid infinite enable. The value can be a string of true or false.
            Preferinfiniteenable and Validinfinteenable must both configure true or False, and when True is configured,
            preferday/preferhour/preferminute/validday/ Validhour/validminute parameters are not configurable.
        required: false
        default: false
        choices: ['true','false']
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the preferDay and  preferHour and  preferMinute and  validDay and validHour and validMinute and preferInfiniteEnable
            and validInfinteEnable  cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasipv6addrmng module ipv6 lifetime rule configuration.
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

  - name:Create a brasipv6addrmng module lifetime rule
    ne_brasipv6addrmng_ipv6prefixs_lifetime_config:
    prefixName='prefixlhtest',
    preferDay=5
    preferHour=6
    preferMinute=7
    validDay=7
    validHour=8
    validMinute=9
    preferInfiniteEnable='false'
    validInfinteEnable='false'
    operation='create'
    provider="{{ cli }}"

  - name:Delete a brasipv6addrmng module lifetime rule
    ne_brasipv6addrmng_ipv6prefixs_lifetime_config:
    prefixName='prefixlhtest',
    preferDay=5
    preferHour=6
    preferMinute=7
    validDay=7
    validHour=8
    validMinute=9
    preferInfiniteEnable='false'
    validInfinteEnable='false'
    operation='delete'
    provider="{{ cli }}"

  - name:Merge a brasipv6addrmng module lifetime rule
    ne_brasipv6addrmng_ipv6prefixs_lifetime_config:
    prefixName='prefixlhtest',
    preferDay=5
    preferHour=6
    preferMinute=7
    validDay=7
    validHour=8
    validMinute=9
    preferInfiniteEnable='false'
    validInfinteEnable='false'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasipv6addrmng module lifetime rule
    ne_brasipv6addrmng_ipv6prefixs_lifetime_config:
    prefixName='prefixlhtest',
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
        "preferDay": 5,
        "preferHour": 6,
        "preferInfiniteEnable": "false",
        "preferMinute": 7,
        "prefixName": "prefixlhtest",
        "validDay": 7,
        "validHour": 8,
        "validInfinteEnable": "false",
        "validMinute": 9



    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
          "lifttimes": [
            {
                "preferDay": "2",
                "preferHour": "0",
                "preferInfiniteEnable": "false",
                "preferMinute": "0",
                "prefixName": "prefixlhtest",
                "validDay": "3",
                "validHour": "0",
                "validInfinteEnable": "false",
                "validMinute": "0"
            }
        ]







    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "end_state": {
         "lifttimes": [
            {
                "preferDay": "5",
                "preferHour": "6",
                "preferInfiniteEnable": "false",
                "preferMinute": "7",
                "prefixName": "prefixlhtest",
                "validDay": "7",
                "validHour": "8",
                "validInfinteEnable": "false",
                "validMinute": "9"
            }
        ]
    }
'''


logging.basicConfig(filename='example.log', level=logging.DEBUG)
IPV6PREFIXSLIFETIME_HEAD = """
    <config>
      <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
        <ipv6Prefixs>
          <ipv6Prefix>
"""

IPV6PREFIXSLIFETIME_TAIL = """
           </ipv6Prefix>
        </ipv6Prefixs>
      </brasipv6addrmng>
    </config>
"""

IPV6PREFIXSLIFETIME_GETHEAD = """
   <filter type="subtree">
      <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
        <ipv6Prefixs>
          <ipv6Prefix>
"""

IPV6PREFIXSLIFETIME_GETTAIL = """
          </ipv6Prefix>
        </ipv6Prefixs>
      </brasipv6addrmng>
    </filter>
"""

LIFETIME_CREATE = """
        <lifeTime nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

LIFETIME_DELETE = """
       <lifeTime nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

LIFETIME_MERGE = """
    <lifeTime nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

PREFIXNAME = """
      <prefixName>%s</prefixName>
"""

PREFERDAY = """
      <preferDay>%d</preferDay>
"""

PREFERHOUR = """
      <preferHour>%d</preferHour>
"""

PREFERMINUTE = """
      <preferMinute>%d</preferMinute>
"""

VALIDDAY = """
      <validDay>%d</validDay>
"""

VALIDHOUR = """
       <validHour>%d</validHour>
"""

VALIDMINUTE = """
       <validMinute>%d</validMinute>
"""

PREFERINFINITEENABLE = """
      <preferInfiniteEnable>%s</preferInfiniteEnable>
"""

VALIDINFINTENABLE = """
      <validInfinteEnable>%s</validInfinteEnable>
"""

LIFETIME = """
    <lifeTime/>
"""

LIFETIMEBEG = """
       <lifeTime>
"""

LIFETIMEEND = """
       </lifeTime>
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
        self.prefixName = self.module.params['prefixName']
        self.preferDay = self.module.params['preferDay']
        self.preferHour = self.module.params['preferHour']
        self.preferMinute = self.module.params['preferMinute']
        self.validDay = self.module.params['validDay']
        self.validHour = self.module.params['validHour']
        self.validMinute = self.module.params['validMinute']
        self.preferInfiniteEnable = self.module.params['preferInfiniteEnable']
        self.validInfinteEnable = self.module.params['validInfinteEnable']
        self.operation = self.module.params['operation']
        if self.operation != 'delete':
            if self.operation != 'get' and self.preferInfiniteEnable is None:
                self.preferInfiniteEnable = 'false'
            if self.operation != 'get' and self.validInfinteEnable is None:
                self.validInfinteEnable = 'false'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.prefixName is not None:
            self.proposed["prefixName"] = self.prefixName
        if self.preferDay is not None:
            self.proposed["preferDay"] = self.preferDay
        if self.preferHour is not None:
            self.proposed["preferHour"] = self.preferHour
        if self.preferMinute is not None:
            self.proposed["preferMinute"] = self.preferMinute
        if self.validDay is not None:
            self.proposed["validDay"] = self.validDay
        if self.validHour is not None:
            self.proposed["validHour"] = self.validHour
        if self.validMinute is not None:
            self.proposed["validMinute"] = self.validMinute
        if self.preferInfiniteEnable is not None:
            self.proposed["preferInfiniteEnable"] = self.preferInfiniteEnable
        if self.validInfinteEnable is not None:
            self.proposed["validInfinteEnable"] = self.validInfinteEnable
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
        cfg_str += IPV6PREFIXSLIFETIME_HEAD
        if self.operation == 'create':
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            cfg_str += LIFETIME_CREATE
            if self.preferDay is not None:
                cfg_str += PREFERDAY % self.preferDay
            if self.preferHour is not None:
                cfg_str += PREFERHOUR % self.preferHour
            if self.preferMinute is not None:
                cfg_str += PREFERMINUTE % self.preferMinute
            if self.validDay is not None:
                cfg_str += VALIDDAY % self.validDay
            if self.validHour is not None:
                cfg_str += VALIDHOUR % self.validHour
            if self.validMinute is not None:
                cfg_str += VALIDMINUTE % self.validMinute
            if self.preferInfiniteEnable is not None:
                cfg_str += PREFERINFINITEENABLE % self.preferInfiniteEnable
            if self.validInfinteEnable is not None:
                cfg_str += VALIDINFINTENABLE % self.validInfinteEnable
            cfg_str += LIFETIMEEND

        if self.operation == 'delete':
            if self.prefixName:
                cfg_str += PREFIXNAME % self.prefixName
            cfg_str += LIFETIME_DELETE
            if self.preferDay is not None:
                cfg_str += PREFERDAY % self.preferDay
            if self.preferHour is not None:
                cfg_str += PREFERHOUR % self.preferHour
            if self.preferMinute is not None:
                cfg_str += PREFERMINUTE % self.preferMinute
            if self.validDay is not None:
                cfg_str += VALIDDAY % self.validDay
            if self.validHour is not None:
                cfg_str += VALIDHOUR % self.validHour
            if self.validMinute is not None:
                cfg_str += VALIDMINUTE % self.validMinute
            if self.preferInfiniteEnable is not None:
                cfg_str += PREFERINFINITEENABLE % self.preferInfiniteEnable
            if self.validInfinteEnable is not None:
                cfg_str += VALIDINFINTENABLE % self.validInfinteEnable
            cfg_str += LIFETIMEEND

        if self.operation == 'merge':
            if self.prefixName is not None:
                cfg_str += PREFIXNAME % self.prefixName
            cfg_str += LIFETIME_MERGE
            if self.preferDay is not None:
                cfg_str += PREFERDAY % self.preferDay
            if self.preferHour is not None:
                cfg_str += PREFERHOUR % self.preferHour
            if self.preferMinute is not None:
                cfg_str += PREFERMINUTE % self.preferMinute
            if self.validDay is not None:
                cfg_str += VALIDDAY % self.validDay
            if self.validHour is not None:
                cfg_str += VALIDHOUR % self.validHour
            if self.validMinute is not None:
                cfg_str += VALIDMINUTE % self.validMinute
            if self.preferInfiniteEnable is not None:
                cfg_str += PREFERINFINITEENABLE % self.preferInfiniteEnable
            if self.validInfinteEnable is not None:
                cfg_str += VALIDINFINTENABLE % self.validInfinteEnable
            cfg_str += LIFETIMEEND

        if self.operation == 'get':
            logging.info('self.operation get test 1')
            cfg_str = ''
            cfg_str = IPV6PREFIXSLIFETIME_GETHEAD
        else:
            cfg_str += IPV6PREFIXSLIFETIME_TAIL
        # 第二步: 下发配置报文
        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += IPV6PREFIXSLIFETIME_GETHEAD
        if self.prefixName is not None:
            cfg_str += PREFIXNAME % self.prefixName
        if self.operation != 'get':
            cfg_str += LIFETIME
        if self.operation == 'get':
            cfg_str += LIFETIMEBEG
            if self.preferDay is not None:
                cfg_str += PREFERDAY % self.preferDay
            if self.preferHour is not None:
                cfg_str += PREFERHOUR % self.preferHour
            if self.preferMinute is not None:
                cfg_str += PREFERMINUTE % self.preferMinute
            if self.validDay is not None:
                cfg_str += VALIDDAY % self.validDay
            if self.validHour is not None:
                cfg_str += VALIDHOUR % self.validHour
            if self.validMinute is not None:
                cfg_str += VALIDMINUTE % self.validMinute
            if self.preferInfiniteEnable is not None:
                cfg_str += PREFERINFINITEENABLE % self.preferInfiniteEnable
            if self.validInfinteEnable is not None:
                cfg_str += VALIDINFINTENABLE % self.validInfinteEnable
            cfg_str += LIFETIMEEND
        cfg_str += IPV6PREFIXSLIFETIME_GETTAIL
        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasipv6addrmng/ipv6Prefixs/ipv6Prefix")
        attributes_Info["lifttimes"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["prefixName"]:
                        logging.info("@!!!!@1")
                        logging.info(leaf_service_Info.text)
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall("lifeTime")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in ["preferDay", "preferHour", "preferMinute", "validDay",
                                                         "validHour", "validMinute", "preferInfiniteEnable", "validInfinteEnable"]:
                                logging.info("@!!!!@2")
                                logging.info(leaf_combine_Info.tag)
                                logging.info(leaf_combine_Info.text)
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["lifttimes"].append(
                            service_container_Table)

        if len(attributes_Info["lifttimes"]) == 0:
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
        prefixName=dict(required=False, type='str'),
        preferDay=dict(required=False, type='int'),
        preferHour=dict(required=False, type='int'),
        preferMinute=dict(required=False, type='int'),
        validDay=dict(required=False, type='int'),
        validHour=dict(required=False, type='int'),
        validMinute=dict(required=False, type='int'),
        preferInfiniteEnable=dict(required=False, choices=['false', 'true']),
        validInfinteEnable=dict(required=False, choices=['false', 'true']),
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
