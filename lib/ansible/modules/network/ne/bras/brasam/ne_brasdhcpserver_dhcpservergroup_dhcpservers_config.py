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
module: ne_brasdhcpserver_dhcpservergroup_dhcpservers_config
version_added: "2.6"
short_description: Manage brasdhcpserver module dhcpservers config rule configuration.
description:
    - Manage brasdhcpserver module dhcpservers config rule configuration.
author:
    - liuhong (@CloudEngine-Ansible)
options:
    dhcpServerGroupName:
        description:
            - Specifies the name of the DHCPv4 server group. The value can be a string of 1 to 32 characters. The value must start with either uppercase
            letters A to Z or lowercase letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: true
    serverIp:
        description:
            - Specifies the IP address of the DHCPv4 server in the dotted decimal format. The value can be a string of 1 to 31 characters.
    serverVpnInstance:
        description:
            - Specifies the VPN instance name. The value must start with either uppercase letters A to Z or lowercase
            letters a to z and be a combination of letters, digits, hyphens (-), and underscores (_).
        required: false
        default:"_public_"
    serverWeight:
        description:
            - Specifies the weight of a DHCPv4 server.The value can be a int of 1 to 100 int
        required: true
    groupNameoperation:
        description:
            -  Manage the state of the resource.
               if operation is get,the serverWeight cannot take parameters,otherwise The echo of the command line is'This operation are not supported'.
        required: false
        default: merge
        choices: ['create', 'delete','merge','get']
    dhcpserveroperation:
        description:
            -  Manage the state of the resource.
        required: true
        choices: ['create', 'delete','merge']

'''

EXAMPLES = '''

- name: Manage brasdhcpserver module dhcpservers config rule configuration.
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

  - name:Create a brasdhcpserver module servergroup config rule
    ne_brasdhcpserver_dhcpservergroup_dhcpservers_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    groupNameoperation='create'
    provider="{{ cli }}"

  - name:Delete a brasdhcpserver module servergroup config rule
    ne_brasdhcpserver_dhcpservergroup_dhcpservers_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    groupNameoperation='delete'
    provider="{{ cli }}"

  - name:Merge a brasdhcpserver module servergroupname config rule
    ne_brasdhcpserver_dhcpservergroup_dhcpservers_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    groupNameoperation='merge'
    provider="{{ cli }}"

   - name:Create a brasdhcpserver module serverVpnInstance config rule
    ne_brasdhcpserver_dhcpservergroup_dhcpservers_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    serverIp='138.187.24.10'
    serverVpnInstance='vpntest4'
    serverWeight=30
    groupNameoperation='merge'
    dhcpserveroperation='create'
    provider="{{ cli }}"

  - name:Delete a brasdhcpserver module serverVpnInstance config rule
    ne_brasdhcpserver_dhcpservergroup_dhcpservers_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    serverIp='138.187.24.10'
    serverVpnInstance='vpntest4'
    serverWeight=30
    groupNameoperation='merge'
    dhcpserveroperation='delete'
    provider="{{ cli }}"

  - name:Merge a brasdhcpserver module serverVpnInstance config rule
    ne_brasdhcpserver_dhcpservergroup_dhcpservers_config:
    dhcpServerGroupName='v_grp_dhcp_test1',
    serverIp='138.187.24.10'
    serverVpnInstance='vpntest4'
    serverWeight=30
    groupNameoperation='merge'
    dhcpserveroperation='merge'
    provider="{{ cli }}"


  - name:get a brasdhcpserver module serverVpnInstance config rule
    ne_brasdhcpserver_dhcpservergroup_dhcpservers_config:
    dhcpServerGroupName='v_grp_dhcp_test1'
    groupNameoperation='get'
    provider="{{ cli }}"

  - name:get a brasdhcpserver module serverVpnInstance config rule
    ne_brasdhcpserver_dhcpservergroup_dhcpservers_config:
    groupNameoperation='get'
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
        "dhcpserveroperation": "merge",
        "groupNameoperation": "merge",
        "serverIp": "138.187.24.10",
        "serverVpnInstance": "vpntest4",
        "serverWeight": 61
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
         "dhcpServerGroups": [
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
        "end_state": {
        "dhcpServerGroups": [
            {
                "dhcpServerGroupName": "v_grp_dhcp_test1",
                "serverIp": "138.187.24.10",
                "serverVpnInstance": "vpntest4",
                "serverWeight": "61"
            }
        ]

    }
'''

logging.basicConfig(filename='example.log', level=logging.DEBUG)
DHCPSERGROUPNAME_HEAD = """
    <config>
      <brasdhcpserver xmlns="http://www.huawei.com/netconf/vrp/huawei-brasdhcpserver">
        <dhcpServerGroups>
"""

DHCPSERGROUPNAME_TAIL = """
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

DHCPSERGROUP_CREATE = """
        <dhcpServerGroup nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DHCPSERGROUP_DELETE = """
       <dhcpServerGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DHCPSERGROUP_MERGE = """
       <dhcpServerGroup nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DHCPSERVER_CREATE = """
     <dhcpServer nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DHCPSERVER_DELETE = """
     <dhcpServer nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DHCPSERVER_MERGE = """
     <dhcpServer nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

DHCPSERVERGROUPNAME = """
       <dhcpServerGroupName>%s</dhcpServerGroupName>
"""


SERVERIP = """
   <serverIp>%s</serverIp>
"""

SERVERVPNINSTANCE = """
   <serverVpnInstance>%s</serverVpnInstance>
"""


SERVERWEIGHT = """
   <serverWeight>%d</serverWeight>
"""

DHCPSERVERSBEG = """
    <dhcpServers>
"""

DHCPSERVERSEND = """
    </dhcpServers>
"""

DHCPSERVERBEG = """
    <dhcpServer>
"""

DHCPSERVEREND = """
    </dhcpServer>
"""

DHCPSERVERGROUPEND = """
  </dhcpServerGroup>
"""

SERVERIPSTR = """
    <serverIp/>
"""

SERVERVPNINSTANCESTR = """
    <serverVpnInstance/>
"""

SERVERWEIGHTSTR = """
    <serverWeight/>
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
        self.serverIp = self.module.params['serverIp']
        self.serverVpnInstance = self.module.params['serverVpnInstance']
        self.serverWeight = self.module.params['serverWeight']
        self.groupNameoperation = self.module.params['groupNameoperation']
        self.dhcpserveroperation = self.module.params['dhcpserveroperation']

        if self.groupNameoperation != 'get' and self.serverVpnInstance is None:
            self.serverVpnInstance = '_public_'
        # 解析输入生成 proposed 表
        self.proposed = dict()
        if self.dhcpServerGroupName is not None:
            self.proposed["dhcpServerGroupName"] = self.dhcpServerGroupName
        if self.serverIp is not None:
            self.proposed["serverIp"] = self.serverIp
        if self.serverVpnInstance is not None:
            self.proposed["serverVpnInstance"] = self.serverVpnInstance
        if self.serverWeight is not None:
            self.proposed["serverWeight"] = self.serverWeight
        if self.groupNameoperation is not None:
            self.proposed["groupNameoperation"] = self.groupNameoperation
        if self.dhcpserveroperation is not None:
            self.proposed["dhcpserveroperation"] = self.dhcpserveroperation

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
        if self.groupNameoperation == 'create':
            cfg_str += DHCPSERGROUP_CREATE
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            if self.dhcpserveroperation == 'create':
                cfg_str += DHCPSERVERSBEG
                cfg_str += DHCPSERVER_CREATE
                if self.serverIp:
                    cfg_str += SERVERIP % self.serverIp
                if self.serverVpnInstance:
                    cfg_str += SERVERVPNINSTANCE % self.serverVpnInstance
                if self.serverWeight:
                    cfg_str += SERVERWEIGHT % self.serverWeight
                cfg_str += DHCPSERVEREND
                cfg_str += DHCPSERVERSEND

            if self.dhcpserveroperation == 'merge':
                cfg_str += DHCPSERVERSBEG
                cfg_str += DHCPSERVER_MERGE
                if self.serverIp:
                    cfg_str += SERVERIP % self.serverIp
                if self.serverVpnInstance:
                    cfg_str += SERVERVPNINSTANCE % self.serverVpnInstance
                if self.serverWeight:
                    cfg_str += SERVERWEIGHT % self.serverWeight
                cfg_str += DHCPSERVEREND
                cfg_str += DHCPSERVERSEND

            cfg_str += DHCPSERVERGROUPEND

        if self.groupNameoperation == 'delete':
            cfg_str += DHCPSERGROUP_DELETE
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            cfg_str += DHCPSERVERGROUPEND

        if self.groupNameoperation == 'merge':
            cfg_str += DHCPSERGROUP_MERGE
            if self.dhcpServerGroupName:
                cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
            if self.dhcpserveroperation == 'create':
                cfg_str += DHCPSERVERSBEG
                cfg_str += DHCPSERVER_CREATE
                if self.serverIp:
                    cfg_str += SERVERIP % self.serverIp
                if self.serverVpnInstance:
                    cfg_str += SERVERVPNINSTANCE % self.serverVpnInstance
                if self.serverWeight:
                    cfg_str += SERVERWEIGHT % self.serverWeight
                cfg_str += DHCPSERVEREND
                cfg_str += DHCPSERVERSEND

            if self.dhcpserveroperation == 'delete':
                cfg_str += DHCPSERVERSBEG
                cfg_str += DHCPSERVER_DELETE
                if self.serverIp:
                    cfg_str += SERVERIP % self.serverIp
                if self.serverVpnInstance:
                    cfg_str += SERVERVPNINSTANCE % self.serverVpnInstance
                if self.serverWeight:
                    cfg_str += SERVERWEIGHT % self.serverWeight
                cfg_str += DHCPSERVEREND
                cfg_str += DHCPSERVERSEND

            if self.dhcpserveroperation == 'merge':
                cfg_str += DHCPSERVERSBEG
                cfg_str += DHCPSERVER_MERGE
                if self.serverIp:
                    cfg_str += SERVERIP % self.serverIp
                if self.serverVpnInstance:
                    cfg_str += SERVERVPNINSTANCE % self.serverVpnInstance
                if self.serverWeight:
                    cfg_str += SERVERWEIGHT % self.serverWeight
                cfg_str += DHCPSERVEREND
                cfg_str += DHCPSERVERSEND
            cfg_str += DHCPSERVERGROUPEND

        cfg_str += DHCPSERGROUPNAME_TAIL
        # 第二步: 下发配置报文
        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        # 第一步, 构造查询报文
        cfg_str = ''
        cfg_str += DHCPSERGROUPNAME_GETHEAD
        if self.dhcpServerGroupName:
            cfg_str += DHCPSERVERGROUPNAME % self.dhcpServerGroupName
        cfg_str += DHCPSERVERSBEG
        cfg_str += DHCPSERVERBEG
        if self.groupNameoperation != 'get':
            cfg_str += SERVERIPSTR
            cfg_str += SERVERVPNINSTANCESTR
            cfg_str += SERVERWEIGHTSTR
        if self.groupNameoperation == 'get':
            if self.serverIp:
                cfg_str += SERVERIP % self.serverIp
            if self.serverVpnInstance:
                cfg_str += SERVERVPNINSTANCE % self.serverVpnInstance
            if self.serverWeight:
                cfg_str += SERVERWEIGHT % self.serverWeight
        cfg_str += DHCPSERVEREND
        cfg_str += DHCPSERVERSEND
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
        attributes_Info["dhcpServerGroups"] = list()

        if len(service_container_attributes_Info) != 0:
            for service_node in service_container_attributes_Info:
                service_container_Table = dict()
                for leaf_service_Info in service_node:
                    if leaf_service_Info.tag in ["dhcpServerGroupName"]:
                        service_container_Table[leaf_service_Info.tag] = leaf_service_Info.text

                container_combine_Info = service_node.findall(
                    "dhcpServers/dhcpServer")
                if len(container_combine_Info) != 0:
                    for combine_node in container_combine_Info:
                        container_2_info_Table = copy.deepcopy(
                            service_container_Table)
                        for leaf_combine_Info in combine_node:
                            if leaf_combine_Info.tag in [
                                    "serverIp", "serverVpnInstance", "serverWeight"]:
                                container_2_info_Table[leaf_combine_Info.tag] = leaf_combine_Info.text
                        attributes_Info["dhcpServerGroups"].append(
                            container_2_info_Table)

        # 解析5: 返回数据
        return attributes_Info

    def run(self):
        # 第一步: 检测输入

        # 第二步: 下发 get 报文, 查询当前配置
        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        # 第三步: 根据用户输入的操作码下发配置, 查询功能已经在 get_existing 实现
        if self.groupNameoperation != 'get':
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
        serverIp=dict(required=False, type='str'),
        serverVpnInstance=dict(required=False, type='str', default='_public_'),
        serverWeight=dict(required=False, type='int'),
        groupNameoperation=dict(
            required=False,
            choices=[
                'create',
                'delete',
                'merge',
                'get'],
            default='merge'),
        dhcpserveroperation=dict(
            required=False, choices=[
                'create', 'delete', 'merge']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
