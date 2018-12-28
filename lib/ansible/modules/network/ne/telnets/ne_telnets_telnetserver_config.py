#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_telnets_telnetserver_config
version_added: "2.6"
short_description: Manages telnet server configuration.
description:
    - Manages telnet server configuration.
author:Zhaweiwei(@netengine-Ansible)
'''

EXAMPLES = '''

- name: nedevice telnets module test
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

  - name: "delete telnets telnetServer"
    ne_telnet_server_telnetserver_config:
      packetDscp: 45
      operation: delete
      provider: "{{ cli }}"
'''

TELNETSERVER_CONFIG = """
<config>
  <telnets xmlns="http://www.huawei.com/netconf/vrp/huawei-telnets">
    <telnetServer operation="merge">
      <telnetSvrEnable></telnetSvrEnable>
      <portNum></portNum>
      <telIpv6SrvEnble></telIpv6SrvEnble>
      <port6Num></port6Num>
      <srcInterfName></srcInterfName>
      <acl4Name></acl4Name>
      <acl4Num></acl4Num>
      <acl6Name></acl6Name>
      <acl6Num></acl6Num>
      <srcIpv6Addr></srcIpv6Addr>
      <srcIpv6VpnName></srcIpv6VpnName>
      <packetDscp></packetDscp>
    </telnetServer>
  </telnets>
</config>
"""

TELNETSERVER_CFG_HEAD = """
<config>
  <telnets xmlns="http://www.huawei.com/netconf/vrp/huawei-telnets">
    <telnetServer>
"""

TELNETSERVER_DEL_HEAD = """
<config>
  <telnets xmlns="http://www.huawei.com/netconf/vrp/huawei-telnets">
    <telnetServer operation="delete">
"""

TELNETSERVER_TAIL = """
    </telnetServer>
  </telnets>
</config>
"""

TELNETSVRENABLE = """
      <telnetSvrEnable>%s</telnetSvrEnable>"""

PORTNUM = """
      <portNum>%s</portNum>"""

TELIPV6SRVENBLE = """
      <telIpv6SrvEnble>%s</telIpv6SrvEnble>"""

PORT6NUM = """
      <port6Num>%s</port6Num>"""

SRCINTERFNAME = """
      <srcInterfName>%s</srcInterfName>"""

ACL4NAME = """
      <acl4Name>%s</acl4Name>"""

ACL4NUM = """
      <acl4Num>%s</acl4Num>"""

ACL6NAME = """
      <acl6Name>%s</acl6Name>"""

ACL6NUM = """
      <acl6Num>%s</acl6Num>"""

SRCIPV6ADDR = """
      <srcIpv6Addr>%s</srcIpv6Addr>"""

SRCIPV6VPNNAME = """
      <srcIpv6VpnName>%s</srcIpv6VpnName>"""

PACKETDSCP = """
      <packetDscp>%s</packetDscp>"""

TELNETSVRENABLE_DEL = """
      <telnetSvrEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</telnetSvrEnable>"""

PORTNUM_DEL = """
      <portNum nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</portNum>"""

TELIPV6SRVENBLE_DEL = """
      <telIpv6SrvEnble nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</telIpv6SrvEnble>"""

PORT6NUM_DEL = """
      <port6Num nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</port6Num>"""

SRCINTERFNAME_DEL = """
      <srcInterfName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</srcInterfName>"""

ACL4NAME_DEL = """
      <acl4Name nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl4Name>"""

ACL4NUM_DEL = """
      <acl4Num nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl4Num>"""

ACL6NAME_DEL = """
      <acl6Name nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl6Name>"""

ACL6NUM_DEL = """
      <acl6Num nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl6Num>"""

SRCIPV6ADDR_DEL = """
      <srcIpv6Addr nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</srcIpv6Addr>"""

SRCIPV6VPNNAME_DEL = """
      <srcIpv6VpnName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</srcIpv6VpnName>"""

PACKETDSCP_DEL = """
      <packetDscp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</packetDscp>"""

# 增加一行
# LOGINFAILALARM_HEAD += "\nLOGINFAILALARM_HEAD"


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.telnetSvrEnable = self.module.params['telnetSvrEnable']
        self.portNum = self.module.params['portNum']
        self.telIpv6SrvEnble = self.module.params['telIpv6SrvEnble']
        self.port6Num = self.module.params['port6Num']
        self.srcInterfName = self.module.params['srcInterfName']
        self.acl4Name = self.module.params['acl4Name']
        self.acl4Num = self.module.params['acl4Num']
        self.acl6Name = self.module.params['acl6Name']
        self.acl6Num = self.module.params['acl6Num']
        self.srcIpv6Addr = self.module.params['srcIpv6Addr']
        self.srcIpv6VpnName = self.module.params['srcIpv6VpnName']
        self.packetDscp = self.module.params['packetDscp']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params_func(self, arg):
        if not arg and arg != '':
            return True
        return False

    # 最少要输一个参数
    def check_params(self):
        if self.check_params_func(self.telnetSvrEnable) and self.check_params_func(self.portNum) and self.check_params_func(self.telIpv6SrvEnble) \
                and self.check_params_func(self.port6Num) and self.check_params_func(self.srcInterfName) and self.check_params_func(self.acl4Name) \
                and self.check_params_func(self.acl4Num) and self.check_params_func(self.acl6Name) and self.check_params_func(self.acl6Num) \
                and self.check_params_func(self.srcIpv6Addr) and self.check_params_func(self.srcIpv6VpnName) and self.check_params_func(self.packetDscp):
            self.module.fail_json(msg='Error: telnetSvrEnable and portNum and telIpv6SrvEnble and port6Num and srcInterfName and acl4Name and acl4Num\
 and acl6Name and acl6Num and srcIpv6Addr and srcIpv6VpnName and packetDscp at least one provide')

    def config_params_func(self, arg, rpc_str):
        if arg or arg == '':
            return rpc_str % arg
        return ''

    def config_str(self):
        cfg_str = ''
        cfg_str += TELNETSERVER_CFG_HEAD
        if self.operation == 'create':
            cfg_str += self.config_params_func(
                self.telnetSvrEnable, TELNETSVRENABLE)

            cfg_str += self.config_params_func(self.portNum, PORTNUM)

            cfg_str += self.config_params_func(
                self.telIpv6SrvEnble, TELIPV6SRVENBLE)

            cfg_str += self.config_params_func(self.port6Num, PORT6NUM)

            cfg_str += self.config_params_func(
                self.srcInterfName, SRCINTERFNAME)

            cfg_str += self.config_params_func(self.acl4Name, ACL4NAME)

            cfg_str += self.config_params_func(self.acl4Num, ACL4NUM)

            cfg_str += self.config_params_func(self.acl6Name, ACL6NAME)

            cfg_str += self.config_params_func(self.acl6Num, ACL6NUM)

            cfg_str += self.config_params_func(self.srcIpv6Addr, SRCIPV6ADDR)

            cfg_str += self.config_params_func(
                self.srcIpv6VpnName, SRCIPV6VPNNAME)

            cfg_str += self.config_params_func(self.packetDscp, PACKETDSCP)

        if self.operation == 'delete':
            cfg_str += self.config_params_func(
                self.telnetSvrEnable, TELNETSVRENABLE_DEL)

            cfg_str += self.config_params_func(self.portNum, PORTNUM_DEL)

            cfg_str += self.config_params_func(
                self.telIpv6SrvEnble, TELIPV6SRVENBLE_DEL)

            cfg_str += self.config_params_func(self.port6Num, PORT6NUM_DEL)

            cfg_str += self.config_params_func(
                self.srcInterfName, SRCINTERFNAME_DEL)

            cfg_str += self.config_params_func(self.acl4Name, ACL4NAME_DEL)

            cfg_str += self.config_params_func(self.acl4Num, ACL4NUM_DEL)

            cfg_str += self.config_params_func(self.acl6Name, ACL6NAME_DEL)

            cfg_str += self.config_params_func(self.acl6Num, ACL6NUM_DEL)

            cfg_str += self.config_params_func(self.srcIpv6Addr,
                                               SRCIPV6ADDR_DEL)

            cfg_str += self.config_params_func(
                self.srcIpv6VpnName, SRCIPV6VPNNAME_DEL)

            cfg_str += self.config_params_func(self.packetDscp, PACKETDSCP_DEL)

        cfg_str += TELNETSERVER_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        telnetSvrEnable=dict(required=False, type='str'),
        portNum=dict(required=False, type='str'),
        telIpv6SrvEnble=dict(required=False, type='str'),
        port6Num=dict(required=False, type='str'),
        srcInterfName=dict(required=False, type='str'),
        acl4Name=dict(required=False, type='str'),
        acl4Num=dict(required=False, type='str'),
        acl6Name=dict(required=False, type='str'),
        acl6Num=dict(required=False, type='str'),
        srcIpv6Addr=dict(required=False, type='str'),
        srcIpv6VpnName=dict(required=False, type='str'),
        packetDscp=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'delete'],
            default='create'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
