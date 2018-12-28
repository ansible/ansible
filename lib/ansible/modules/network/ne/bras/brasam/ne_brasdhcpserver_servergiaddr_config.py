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
module: ne_brasdhcpserver_servergiaddr_config
version_added: "2.6"
short_description:  Manage brasdhcpserver module serverGiAddr config rule configuration.
description:
    -  Manage brasdhcpserver module serverGiAddr config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    dhcpServerGroupName:
        description:
            -  Specifies the name of the DHCPv4 server group. The value can be a string of 1 to 64 characters. The value must start with either uppercase
            letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    ifName:
        description:
            -  Specifies the interface whose IP address that is used as the GiAddr address of packets sent by the DHCPv4 server group.
            The value can be a string of 1 to 64 characters. The value must start with either uppercase letters A to Z or lowercase
            letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: false
    giaddrIp:
        description:
            -  Specifies the IP address that is used as the GiAddr address of packets sent by the DHCPv4 server group.
            The address is in dotted decimal notation.
        required: true
    vpnInstance:
        description:
            -  Specifies the VPN instance name.
        required: true
    operation:
        description:
            -  Manage the state of the resource.
            if operation is get,the giaddrIp and ifname  and vpnInstance cannot take parameters,
            otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: create
        choices: ['create', 'delete', 'merge','get']
'''
EXAMPLES = '''

- name: Manage brasdhcpserver module serverGiAddr config rule configuration.
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

  - name:Create a brasdhcpserver module  giaddr interface config rule
    ne_brasdhcpserver_serverGiAddr_config:
    dhcpServerGroupName= 'v_grp_dhcp_test1',
    ifName='GigabitEthernet1/0/2'
    operation='create'
    provider="{{ cli }}"

  - name:Delete a brasdhcpserver module giaddr interface config rule
    ne_brasdhcpserver_serverGiAddr_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    ifName='GigabitEthernet1/0/2'
    operation='delete'
    provider="{{ cli }}"

  - name:Merge a brasdhcpserver module giaddr interface config rule
    ne_brasdhcpserver_serverGiAddr_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    ifName='GigabitEthernet1/0/2'
    operation='merge'
    provider="{{ cli }}"

  - name:create a brasdhcpserver module ip-address config rule
    ne_brasdhcpserver_servergiaddr_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    giaddrIp='1.1.1.1'
    vpnInstance='vpntest1'
    operation='create'
    provider="{{ cli }}"

  - name:delete a brasdhcpserver module ip-address config rule
    ne_brasdhcpserver_servergiaddr_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    giaddrIp='1.1.1.1'
    vpnInstance='vpntest1'
    operation='delete'
    provider="{{ cli }}"

  - name:Merge a brasdhcpserver module ip-address config rule
    ne_brasdhcpserver_servergiaddr_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    giaddrIp='1.1.1.1'
    vpnInstance='vpntest1'
    operation='merge'
    provider="{{ cli }}"

  - name:get a brasdhcpserver module serverGiAddr config rule
    ne_brasdhcpserver_servergiaddr_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    operation='get'
    provider="{{ cli }}"

  - name:get a brasdhcpserver module serverGiAddr config rule
    ne_brasdhcpserver_servergiaddr_config:
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
        "dhcpServerGroupName": "v_grp_dhcp_test1",
        "ifName": "GigabitEthernet1/0/2",
        "operation": "merge"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
            "serverGiAddrs": [
            {
                "dhcpServerGroupName": "v_grp_dhcp_test1"
            }
        ]

    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "serverGiAddrs": [
            {
                "dhcpServerGroupName": "v_grp_dhcp_test1"
            }
        ]
    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
DHCPSERGROUPNAME_HEAD = """
    <config>
      <brasdhcpserver xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpserver">
        <dhcpServerGroups>
          <dhcpServerGroup>
"""

DHCPSERGROUPNAME_TAIL = """
              </dhcpServerGroup>
           </dhcpServerGroups>
      </brasdhcpserver>
    </config>
"""

DHCPSERGROUPNAME_GETHEAD = """
    <filter type="subtree">
      <brasdhcpserver xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpserver">
        <dhcpServerGroups>
          <dhcpServerGroup>
"""

DHCPSERGROUPNAME_GETTAIL = """
           </dhcpServerGroup>
      </dhcpServerGroups>
    </brasdhcpserver>
  </filter>
"""

SERVERGIADDR_CREATE = """
        <serverGiAddr nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SERVERGIADDR_DELETE = """
       <serverGiAddr nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SERVERGIADDR_MERGE = """
      <serverGiAddr nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DHCPSERVERGROUPNAME = """
       <dhcpServerGroupName>%s</dhcpServerGroupName>
"""

IFNAME = """
   <ifName>%s</ifName>
"""

GIADDRID = """
   <giaddrIp>%s</giaddrIp>
"""

VPNINSTANCE = """
    <vpnInstance>%s</vpnInstance>
"""

SERVERGIADDRBEG = """
    <serverGiAddr>
"""

SERVERGIADDREND = """
  </serverGiAddr>
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
        self.dhcpServerGroupName = self.module.params['dhcpServerGroupName']
        self.ifName = self.module.params['ifName']
        self.giaddrIp = self.module.params['giaddrIp']
        self.vpnInstance = self.module.params['vpnInstance']
        self.operation = self.module.params['operation']

        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.dhcpServerGroupName is not None:
            self.proposed["dhcpServerGroupName"] = self.dhcpServerGroupName
        if self.ifName is not None:
            self.proposed["ifName"] = self.ifName
        if self.giaddrIp is not None:
            self.proposed["giaddrIp"] = self.giaddrIp
        if self.vpnInstance is not None:
            self.proposed["vpnInstance"] = self.vpnInstance
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
        cfg_str += DHCPSERGROUPNAME_HEAD
        if self.operation == 'create':
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            cfg_str += SERVERGIADDR_CREATE
            if self.ifName:
                cfg_str += IFNAME % self.ifName
            if self.giaddrIp:
                cfg_str += GIADDRID % self.giaddrIp
            if self.vpnInstance:
                cfg_str += VPNINSTANCE % self.vpnInstance
            cfg_str += SERVERGIADDREND

        if self.operation == 'delete':
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            cfg_str += SERVERGIADDR_DELETE
            if self.ifName:
                cfg_str += IFNAME % self.ifName
            if self.giaddrIp:
                cfg_str += GIADDRID % self.giaddrIp
            if self.vpnInstance:
                cfg_str += VPNINSTANCE % self.vpnInstance
            cfg_str += SERVERGIADDREND

        if self.operation == 'merge':
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            cfg_str += SERVERGIADDR_MERGE
            if self.ifName:
                cfg_str += IFNAME % self.ifName
            if self.giaddrIp:
                cfg_str += GIADDRID % self.giaddrIp
            if self.vpnInstance:
                cfg_str += VPNINSTANCE % self.vpnInstance
            cfg_str += SERVERGIADDREND

        cfg_str += DHCPSERGROUPNAME_TAIL
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += DHCPSERGROUPNAME_GETHEAD
        if self.dhcpServerGroupName:
            cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
        if self.operation != 'get':
            cfg_str += SERVERGIADDRBEG
            cfg_str += SERVERGIADDREND
        if self.operation == 'get':
            cfg_str += SERVERGIADDRBEG
            if self.ifName:
                cfg_str += IFNAME % self.ifName
            if self.giaddrIp:
                cfg_str += GIADDRID % self.giaddrIp
            if self.vpnInstance:
                cfg_str += VPNINSTANCE % self.vpnInstance
            cfg_str += SERVERGIADDREND
        cfg_str += DHCPSERGROUPNAME_GETTAIL

        # 第二步: 下发查询报文
        xml_str = get_nc_config(self.module, cfg_str)
        # 第三步: 解析查询报文
        # 解析1: 删除无用字符串, 注意根据业务做替换
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpserver"', "")

        # 解析2: 无数据检测
        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        # 解析3: 提取自己关心的字段(叶子)值
        root = ElementTree.fromstring(xml_str)
        service_container_attributes_Info = root.findall(
            "brasdhcpserver/dhcpServerGroups/dhcpServerGroup")
        attributes_Info["serverGiAddrs"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["dhcpServerGroupName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall("serverGiAddr")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "ifName", "giaddrIp", "vpnInstance"]:
                                service_container_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["serverGiAddrs"].append(
                            service_container_Table)

        if len(attributes_Info["serverGiAddrs"]) == 0:
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
        dhcpServerGroupName=dict(required=False, type='str'),
        ifName=dict(required=False, type='str'),
        giaddrIp=dict(required=False, type='str'),
        vpnInstance=dict(required=False, type='str'),
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
