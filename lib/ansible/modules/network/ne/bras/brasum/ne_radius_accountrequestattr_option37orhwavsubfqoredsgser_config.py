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
module: ne_radius_accountrequestattr_option37orhwavsubfqoredsgser_config
version_added: "2.6"
short_description: Manage radius module option37 hwAvSubFq edsgSer config rule configuration.
description:
    - Manage radius module option37 hwAvSubFq edsgSer config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    groupName:
        description:
            - RADIUS server group's name,Range Supported [a-z][A-Z][0-9] and [.,_,-],the value can be a string,which length from 1 to 64.
        required: true
    edsgServiceName:
        description:
            - Indicates the EDSG service name. If the command is configured, it indicates the Huawei proprietary No.95 attribute.
            If the command is not configured, it indicates the Huawei proprietary No.185 attribute..
        required: true
        choices: ['true', 'flse']
    hwDhcpv6Option37:
        description:
            - Indicates the Huawei proprietary No.150 attribute, which is used to encapsulate the client MAC.
        required: true
        choices: ['true', 'flse']
    hwAvpairSubscriberFq:
        description:
            - HW-Avpair.Indicates that the hw-avpair attribute in Accounting-request packets is used for sending effective Flow-queue parameters.
        required: true
        choices: ['true', 'flse']
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the edsgServiceName and hwDhcpv6Option37 and hwAvpairSubscriberFq cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete','merge','get']


'''

EXAMPLES = '''

- name: Manage radius module option37 hwAvSubFq edsgSer config rule configuration.
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

  - name:create a radius module option37 config rule
    ne_radius_accountrequestattr_option37orhwavsubfqoredsgser_config:
    groupName='liuhong'
    edsgServiceName='true'
    operation='create'
    provider="{{ cli }}"

  - name:delete a radius module option37 config rule
    ne_radius_accountrequestattr_option37orhwavsubfqoredsgser_config:
    groupName='liuhong'
    edsgServiceName='true'
    operation='delete'
    provider="{{ cli }}"

  - name:merge a radius module option37 config rule
    ne_radius_accountrequestattr_option37orhwavsubfqoredsgser_config:
    groupName='liuhong'
    edsgServiceName='true'
    operation='merge'
    provider="{{ cli }}"

  - name:get a radius module accountrequestattr config rule
    ne_radius_accountRequestAttr_option37orhwAvSubFqoredsgSer_config:
    groupName='liuhong'
    operation='get'
    provider="{{ cli }}"

  - name:get a radius module accountrequestattr config rule
    ne_radius_accountrequestattr_option37orhwavsubfqoredsgser_config:
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
        "edsgServiceName": "true",
        "groupName": "liuhong",
        "operation": "merge"

    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "accountRequestAttributes": [
            {
                "edsgServiceName": "false",
                "groupName": "liuhong",
                "hwAvpairSubscriberFq": "true",
                "hwDhcpv6Option37": "true"
            }
        ]





    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "clientOption60s": [
            {
                "interfaceName": "Eth-Trunk1.20",
                "option60OrVendorClass": "none"
            }
        ]




    }
'''


logging.basicConfig(filename='example.log', level=logging.DEBUG)
RADIUS_HEAD = """
    <config>
      <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
        <rdsTemplates>
          <rdsTemplate>
"""

RADIUS_TAIL = """
            </rdsTemplate>
        </rdsTemplates>
      </radius>
    </config>
"""

RADIUS_GETHEAD = """
     <filter type="subtree">
      <radius xmlns="http://www.huawei.com/netconf/vrp/huawei-radius">
      <rdsTemplates>
        <rdsTemplate>
"""

RADIUS_GETTAIL = """
        </rdsTemplate>
      </rdsTemplates>
    </radius>
  </filter>
"""

ACCOUNTREQUESTATTR_CREATE = """
          <accountRequestAttribute nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

ACCOUNTREQUESTATTR_DELETE = """
          <accountRequestAttribute nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

ACCOUNTREQUESTATTR_MERGE = """
        <accountRequestAttribute nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

GROUPNAME = """
      <groupName>%s</groupName>
"""

EDSGSERVICENAME = """
       <edsgServiceName>%s</edsgServiceName>
"""


HWDPCPV6OPTION37 = """
    <hwDhcpv6Option37>%s</hwDhcpv6Option37>
"""

HWAVPAIRSUBSCRIBERFQ = """
    <hwAvpairSubscriberFq>%s</hwAvpairSubscriberFq>
"""


ACCOUNTREQUESTATTREND = """
   </accountRequestAttribute>
"""

ACCOUNTREQUESTATTRBEG = """
   <accountRequestAttribute>
"""

EDSGSERVICENAMEGET = """
    <edsgServiceName/>
"""

HWDPCPV6OPTION37GET = """
    <hwDhcpv6Option37/>
"""

HWAVPAIRSUBSCRIBERFQGET = """
    <hwAvpairSubscriberFq/>
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
        self.groupName = self.module.params['groupName']
        self.edsgServiceName = self.module.params['edsgServiceName']
        self.hwDhcpv6Option37 = self.module.params['hwDhcpv6Option37']
        self.hwAvpairSubscriberFq = self.module.params['hwAvpairSubscriberFq']
        self.operation = self.module.params['operation']
        if self.operation == 'delete':
            if self.edsgServiceName is None and self.hwDhcpv6Option37 is None and self.hwAvpairSubscriberFq is None:
                self.edsgServiceName = 'false'
                self.hwDhcpv6Option37 = 'false'
                self.hwAvpairSubscriberFq = 'false'
                self.operation = 'merge'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.groupName is not None:
            self.proposed["groupName"] = self.groupName
        if self.edsgServiceName is not None:
            self.proposed["edsgServiceName"] = self.edsgServiceName
        if self.hwDhcpv6Option37 is not None:
            self.proposed["hwDhcpv6Option37"] = self.hwDhcpv6Option37
        if self.hwAvpairSubscriberFq is not None:
            self.proposed["hwAvpairSubscriberFq"] = self.hwAvpairSubscriberFq
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
        cfg_str += RADIUS_HEAD
        if self.groupName is not None:
            cfg_str += GROUPNAME % self.groupName
        if self.operation == 'create':
            cfg_str += ACCOUNTREQUESTATTR_CREATE
        if self.operation == 'delete':
            cfg_str += ACCOUNTREQUESTATTR_DELETE
        if self.operation == 'merge':
            cfg_str += ACCOUNTREQUESTATTR_MERGE
        if self.edsgServiceName is not None:
            cfg_str += EDSGSERVICENAME % self.edsgServiceName
        if self.hwDhcpv6Option37 is not None:
            cfg_str += HWDPCPV6OPTION37 % self.hwDhcpv6Option37
        if self.hwAvpairSubscriberFq is not None:
            cfg_str += HWAVPAIRSUBSCRIBERFQ % self.hwAvpairSubscriberFq
        cfg_str += ACCOUNTREQUESTATTREND
        cfg_str += RADIUS_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += RADIUS_GETHEAD
        if self.groupName is not None:
            cfg_str += GROUPNAME % self.groupName
        cfg_str += ACCOUNTREQUESTATTRBEG
        if self.operation != 'get':
            cfg_str += EDSGSERVICENAMEGET
            cfg_str += HWDPCPV6OPTION37GET
            cfg_str += HWAVPAIRSUBSCRIBERFQGET
        if self.operation == 'get':
            if self.edsgServiceName is not None:
                cfg_str += EDSGSERVICENAME % self.edsgServiceName
            if self.hwDhcpv6Option37 is not None:
                cfg_str += HWDPCPV6OPTION37 % self.hwDhcpv6Option37
            if self.hwAvpairSubscriberFq is not None:
                cfg_str += HWAVPAIRSUBSCRIBERFQ % self.hwAvpairSubscriberFq
        cfg_str += ACCOUNTREQUESTATTREND
        cfg_str += RADIUS_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        logging.info("*******service_node1xml_str*****")
        logging.info(xml_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-radius"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "radius/rdsTemplates/rdsTemplate")
        attributes_Info["accountRequestAttributes"] = list()
        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["groupName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "accountRequestAttribute")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "edsgServiceName", "hwDhcpv6Option37", "hwAvpairSubscriberFq"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                    attributes_Info["accountRequestAttributes"].append(
                        service_container_Table)
        if len(attributes_Info["accountRequestAttributes"]) == 0:
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
        groupName=dict(required=False, type='str'),
        edsgServiceName=dict(required=False, choices=['true', 'false']),
        hwDhcpv6Option37=dict(required=False, choices=['true', 'false']),
        hwAvpairSubscriberFq=dict(required=False, choices=['true', 'false']),
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
