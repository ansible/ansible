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
module: ne_brasl2tpaccess_l2tpstartips_config
version_added: "2.6"
short_description: Manage brasl2tpaccess module l2tpstartips config rule configuration.
description:
    - Manage brasl2tpaccess module l2tpstartips config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    l2tpGroupName:
        description:
            - l2tpgroup Name. The value can be a string of 1 to 32 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    identifierName:
        description:
            - identifierName. The value can be a string of 1 to 4 characters. The value must start with either uppercase letters A to Z or
            lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    ipAddress:
        description:
            - ipAddres.
        required: true
    weight:
        description:
            -  weight. The value can be a integer of 1 to 10.
        required: true
    preference:
        description:
            - preference. The value can be a integer of 1 to 255.
        required: true
    remoteName:
        description:
            - remoteName. The value can be a string of 1 to 253 characters. The value must start with either uppercase letters A to Z or lowercase
            letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the ipAddress and weight and  preference and  remoteName cannot take parameters,otherwise The echo of the command
            line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']

'''

EXAMPLES = '''

- name: Manage brasl2tpaccess module l2tpstartips config rule configuration.
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

  - name:create a brasl2tpaccess module l2tpstartips config rule
    ne_brasl2tpaccess_l2tpstartips_config:
    l2tpGroupName='vtest05251'
    identifierName='ID1'
    ipAddress='10.192.12.162'
    weight=9
    preference=2
    remoteName='huawei000'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasl2tpaccess module l2tpstartips config rule
    ne_brasl2tpaccess_l2tpstartips_config:
    l2tpGroupName='vtest05251'
    identifierName='ID1'
    ipAddress='10.192.12.162'
    weight=9
    preference=2
    remoteName='huawei000'
    operation='delete'
    provider="{{ cli }}"

  - name:get a brasl2tpaccess module l2tpstartips config rule
    ne_brasl2tpaccess_l2tpstartips_config:
    l2tpGroupName='vtest05251'
    operation='get'
    provider="{{ cli }}"

  - name:get a brasl2tpaccess module l2tpstartips config rule
    ne_brasl2tpaccess_l2tpstartips_config:
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
        "identifierName": "ID1",
        "ipAddress": "10.192.12.163",
        "l2tpGroupName": "vtest05251",
        "operation": "create",
        "remoteName": "huawei000",
        "weight": 8

    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "l2tpStartIPs": [
            {
                "identifierName": "ID1",
                "ipAddress": "10.192.12.163",
                "l2tpGroupName": "vtest05251",
                "preference": "1",
                "remoteName": "huawei000",
                "weight": "8"
            }
        ]

    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "l2tpStartIPs": [
            {
                "identifierName": "ID1",
                "ipAddress": "10.192.12.163",
                "l2tpGroupName": "vtest05251",
                "preference": "1",
                "remoteName": "huawei000",
                "weight": "8"
            }
        ]

    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
L2TPTUNNELGROUPNAME_HEAD = """
    <config>
      <brasl2tpaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasl2tpaccess">
        <l2tpGroups>
          <l2tpGroup>
"""

L2TPTUNNELGROUPNAME_TAIL = """
                 </l2tpGroup>
              </l2tpGroups>
      </brasl2tpaccess>
    </config>
"""

L2TPTUNNELGROUPNAME_GETHEAD = """
    <filter type="subtree">
     <brasl2tpaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasl2tpaccess">
       <l2tpGroups>
         <l2tpGroup>
"""

L2TPTUNNELGROUPNAME_GETTAIL = """
        </l2tpGroup>
      </l2tpGroups>
    </brasl2tpaccess>
  </filter>
"""

L2TPSTARTIP_CREATE = """
       <l2tpStartIP nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

L2TPSTARTIP_DELETE = """
       <l2tpStartIP nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

L2TPSTARTIP_MERGE = """
      <l2tpStartIP nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""


L2TPGROUPNAME = """
       <l2tpGroupName>%s</l2tpGroupName>
"""

IDENTIFIERNAME = """
      <identifierName>%s</identifierName>
"""

IPADDRESS = """
        <ipAddress>%s</ipAddress>
"""

WEIGHE = """
        <weight>%d</weight>
"""

PREFERENCE = """
       <preference>%d</preference>
"""

REMOTENAME = """
       <remoteName>%s</remoteName>
"""

L2TPSTARTIPSBEG = """
    <l2tpStartIPs>
"""

L2TPSTARTIPSEND = """
   </l2tpStartIPs>
"""

L2TPSTARTIPBEG = """
   <l2tpStartIP>
"""

L2TPSTARTIPEND = """
   </l2tpStartIP>
"""


IDENTIFIERNAMESTR = """
    <identifierName/>
"""

IPADDRESSSTR = """
    <ipAddress/>
"""

WEIGHESTR = """
    <weight/>
"""

PREFERENCESTR = """
    <preference/>
"""

REMOTENAMESTR = """
    <remoteName/>
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
        self.l2tpGroupName = self.module.params['l2tpGroupName']
        self.identifierName = self.module.params['identifierName']
        self.ipAddress = self.module.params['ipAddress']
        self.weight = self.module.params['weight']
        self.preference = self.module.params['preference']
        self.remoteName = self.module.params['remoteName']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.l2tpGroupName is not None:
            self.proposed["l2tpGroupName"] = self.l2tpGroupName
        if self.identifierName is not None:
            self.proposed["identifierName"] = self.identifierName
        if self.ipAddress is not None:
            self.proposed["ipAddress"] = self.ipAddress
        if self.weight is not None:
            self.proposed["weight"] = self.weight
        if self.preference is not None:
            self.proposed["preference"] = self.preference
        if self.remoteName is not None:
            self.proposed["remoteName"] = self.remoteName
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
        cfg_str += L2TPTUNNELGROUPNAME_HEAD
        if self.l2tpGroupName:
            cfg_str += L2TPGROUPNAME % self.l2tpGroupName
        cfg_str += L2TPSTARTIPSBEG
        if self.operation == 'create':
            cfg_str += L2TPSTARTIP_CREATE
        if self.operation == 'delete':
            cfg_str += L2TPSTARTIP_DELETE
        if self.operation == 'merge':
            cfg_str += L2TPSTARTIP_MERGE
        if self.identifierName:
            cfg_str += IDENTIFIERNAME % self.identifierName
        if self.ipAddress:
            cfg_str += IPADDRESS % self.ipAddress
        if self.weight:
            cfg_str += WEIGHE % self.weight
        if self.preference:
            cfg_str += PREFERENCE % self.preference
        if self.remoteName:
            cfg_str += REMOTENAME % self.remoteName
        cfg_str += L2TPSTARTIPEND
        cfg_str += L2TPSTARTIPSEND
        cfg_str += L2TPTUNNELGROUPNAME_TAIL

        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += L2TPTUNNELGROUPNAME_GETHEAD
        if self.l2tpGroupName:
            cfg_str += L2TPGROUPNAME % self.l2tpGroupName
        cfg_str += L2TPSTARTIPSBEG
        cfg_str += L2TPSTARTIPBEG
        if self.operation != 'get':
            cfg_str += IDENTIFIERNAMESTR
            cfg_str += IPADDRESSSTR
            cfg_str += WEIGHESTR
            cfg_str += PREFERENCESTR
            cfg_str += REMOTENAMESTR
        if self.operation == 'get':
            if self.identifierName:
                cfg_str += IDENTIFIERNAME % self.identifierName
            if self.ipAddress:
                cfg_str += IPADDRESS % self.ipAddress
            if self.weight:
                cfg_str += WEIGHE % self.weight
            if self.preference:
                cfg_str += PREFERENCE % self.preference
            if self.remoteName:
                cfg_str += REMOTENAME % self.remoteName
        cfg_str += L2TPSTARTIPEND
        cfg_str += L2TPSTARTIPSEND
        cfg_str += L2TPTUNNELGROUPNAME_GETTAIL

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
            "brasl2tpaccess/l2tpGroups/l2tpGroup")
        attributes_Info["l2tpStartIPs"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["l2tpGroupName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "l2tpStartIPs/l2tpStartIP")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        container_2_info_Table = copy.deepcopy(
                            service_container_Table)
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "identifierName", "ipAddress", "weight", "preference", "remoteName"]:
                                container_2_info_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["l2tpStartIPs"].append(
                            container_2_info_Table)

        if len(attributes_Info["l2tpStartIPs"]) == 0:
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
        l2tpGroupName=dict(required=False, type='str'),
        identifierName=dict(required=False, type='str'),
        ipAddress=dict(required=False, type='str'),
        weight=dict(required=False, type='int'),
        preference=dict(required=False, type='int'),
        remoteName=dict(required=False, type='str'),
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
