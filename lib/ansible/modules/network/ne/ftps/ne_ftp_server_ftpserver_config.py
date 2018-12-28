#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_ftp_server_ftpserver_config
version_added: "2.6"
short_description: Manages FTP server configuration.
description:
    - Manages FTP server configuration.
author:Zhaweiwei(@netengine-Ansible)
'''

EXAMPLES = '''

- name: nedevice ftps module test
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

  - name: "config ftps ftpServer"
    ne_ftp_server_ftpserver_config:
      ftpServerEnable: true
      provider: "{{ cli }}"

  - name: "delete ftps ftpServer"
    ne_ftp_server_ftpserver_config:
      ftpServerEnable: true
      operation: delete
      provider: "{{ cli }}"
'''

FTPSERVER_CONFIG = """
<config>
  <ftps xmlns="http://www.huawei.com/netconf/vrp/huawei-ftps">
    <ftpServer>
      <sourceIpv4Address />
      <ftpServerEnable></ftpServerEnable>
      <ftpIpv6SvrEnble></ftpIpv6SvrEnble>
      <idleTimeout></idleTimeout>
      <aclNumber />
      <listenPortNumber></listenPortNumber>
      <Ipv6listenPortNumber></Ipv6listenPortNumber>
      <aclname4 />
      <defaultDir />
      <sourceInterfaceName />
      <ipv6IdleTimeout></ipv6IdleTimeout>
      <aclname6 />
      <acl6Number />
      <srcIpv6Addr />
      <srcIpv6VpnName />
    </ftpServer>
  </ftps>
</config>
"""

FTPSERVER_CFG_HEAD = """
<config>
  <ftps xmlns="http://www.huawei.com/netconf/vrp/huawei-ftps">
    <ftpServer>
"""

FTPSERVER_DEL_HEAD = """
<config>
  <ftps xmlns="http://www.huawei.com/netconf/vrp/huawei-ftps">
    <ftpServer operation="delete">
"""

FTPSERVER_TAIL = """
    </ftpServer>
  </ftps>
</config>
"""

SOURCEIPV4ADDR = """
      <sourceIpv4Address>%s</sourceIpv4Address>"""

FTPSERVERENABLE = """
      <ftpServerEnable>%s</ftpServerEnable>"""

FTPIPV6SVRENBLE = """
      <ftpIpv6SvrEnble>%s</ftpIpv6SvrEnble>"""

IDLETIMEOUT = """
      <idleTimeout>%s</idleTimeout>"""

ACL4NUMBER = """
      <aclNumber>%s</aclNumber>"""

LISTENPORTNUM = """
      <listenPortNumber>%s</listenPortNumber>"""

IPV6LISTENPORTNUM = """
      <Ipv6listenPortNumber>%s</Ipv6listenPortNumber>"""

ACL4NAME = """
      <aclname4>%s</aclname4>"""

DEFAULTDIR = """
      <defaultDir>%s</defaultDir>"""

SOURCEINTERFACENAME = """
      <sourceInterfaceName>%s</sourceInterfaceName>"""

IPV6IDLETIMEOUT = """
      <ipv6IdleTimeout>%s</ipv6IdleTimeout>"""

ACL6NAME = """
      <aclname6>%s</aclname6>"""

ACL6NUMBER = """
      <acl6Number>%s</acl6Number>"""

SRCIPV6ADDR = """
      <srcIpv6Addr>%s</srcIpv6Addr>"""

SRCIPV6VPNNAME = """
      <srcIpv6VpnName>%s</srcIpv6VpnName>"""

SOURCEIPV4ADDR_DEL = """
      <sourceIpv4Address nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sourceIpv4Address>"""

FTPSERVERENABLE_DEL = """
      <ftpServerEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ftpServerEnable>"""

FTPIPV6SVRENBLE_DEL = """
      <ftpIpv6SvrEnble nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ftpIpv6SvrEnble>"""

IDLETIMEOUT_DEL = """
      <idleTimeout nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</idleTimeout>"""

ACL4NUMBER_DEL = """
      <aclNumber nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclNumber>"""

LISTENPORTNUM_DEL = """
      <listenPortNumber nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</listenPortNumber>"""

IPV6LISTENPORTNUM_DEL = """
      <Ipv6listenPortNumber nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</Ipv6listenPortNumber>"""

ACL4NAME_DEL = """
      <aclname4 nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclname4>"""

DEFAULTDIR_DEL = """
      <defaultDir nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</defaultDir>"""

SOURCEINTERFACENAME_DEL = """
      <sourceInterfaceName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sourceInterfaceName>"""

IPV6IDLETIMEOUT_DEL = """
      <ipv6IdleTimeout nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ipv6IdleTimeout>"""

ACL6NAME_DEL = """
      <aclname6 nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclname6>"""

ACL6NUMBER_DEL = """
      <acl6Number nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl6Number>"""

SRCIPV6ADDR_DEL = """
      <srcIpv6Addr nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</srcIpv6Addr>"""

SRCIPV6VPNNAME_DEL = """
      <srcIpv6VpnName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</srcIpv6VpnName>"""

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
        self.ftpServerEnable = self.module.params['ftpServerEnable']
        self.ftpIpv6SvrEnble = self.module.params['ftpIpv6SvrEnble']
        self.sourceIpv4Addr = self.module.params['sourceIpv4Addr']
        self.sourceInterfaceName = self.module.params['sourceInterfaceName']
        self.listenPortNum = self.module.params['listenPortNum']
        self.idleTimeout = self.module.params['idleTimeout']
        self.acl4Number = self.module.params['acl4Number']
        self.acl4name = self.module.params['acl4name']
        self.defaultDir = self.module.params['defaultDir']
        self.Ipv6listenPortNum = self.module.params['Ipv6listenPortNum']
        self.ipv6IdleTimeout = self.module.params['ipv6IdleTimeout']
        self.acl6name = self.module.params['acl6name']
        self.acl6Number = self.module.params['acl6Number']
        self.srcIpv6Addr = self.module.params['srcIpv6Addr']
        self.srcIpv6VpnName = self.module.params['srcIpv6VpnName']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params_func(self, arg):
        if not arg and arg != '':
            return True
        return False

    # 最少要输一个参数
    def check_params(self):
        if self.check_params_func(self.ftpServerEnable) and self.check_params_func(self.ftpIpv6SvrEnble) \
                and self.check_params_func(self.sourceIpv4Addr) and self.check_params_func(self.sourceInterfaceName) \
                and self.check_params_func(self.listenPortNum) and self.check_params_func(self.idleTimeout) \
                and self.check_params_func(self.acl4Number) and self.check_params_func(self.acl4name) and self.check_params_func(self.defaultDir) \
                and self.check_params_func(self.Ipv6listenPortNum) and self.check_params_func(self.ipv6IdleTimeout) and self.check_params_func(self.acl6name) \
                and self.check_params_func(self.acl6Number) and self.check_params_func(self.srcIpv6Addr) and self.check_params_func(self.srcIpv6VpnName):
            self.module.fail_json(msg='Error: ftpServerEnable and ftpIpv6SvrEnble and sourceIpv4Addr and sourceInterfaceName and listenPortNum \
 and idleTimeout and acl4Number and acl4name and defaultDir and Ipv6listenPortNum and ipv6IdleTimeout and acl6name and acl6Number \
 and srcIpv6Addr and srcIpv6VpnName at least one provide')

    def config_params_func(self, arg, rpc_str):
        if arg or arg == '':
            return rpc_str % arg
        return ''

    def config_str(self):
        cfg_str = ''
        cfg_str += FTPSERVER_CFG_HEAD
        if self.operation == 'create':
            cfg_str += self.config_params_func(
                self.ftpServerEnable, FTPSERVERENABLE)

            cfg_str += self.config_params_func(
                self.ftpIpv6SvrEnble, FTPIPV6SVRENBLE)

            cfg_str += self.config_params_func(
                self.sourceIpv4Addr, SOURCEIPV4ADDR)

            cfg_str += self.config_params_func(
                self.sourceInterfaceName, SOURCEINTERFACENAME)

            cfg_str += self.config_params_func(
                self.listenPortNum, LISTENPORTNUM)

            cfg_str += self.config_params_func(self.idleTimeout, IDLETIMEOUT)

            cfg_str += self.config_params_func(self.acl4Number, ACL4NUMBER)

            cfg_str += self.config_params_func(self.acl4name, ACL4NAME)

            cfg_str += self.config_params_func(self.defaultDir, DEFAULTDIR)

            cfg_str += self.config_params_func(
                self.Ipv6listenPortNum, IPV6LISTENPORTNUM)

            cfg_str += self.config_params_func(
                self.ipv6IdleTimeout, IPV6IDLETIMEOUT)

            cfg_str += self.config_params_func(self.acl6name, ACL6NAME)

            cfg_str += self.config_params_func(self.acl6Number, ACL6NUMBER)

            cfg_str += self.config_params_func(self.srcIpv6Addr, SRCIPV6ADDR)

            cfg_str += self.config_params_func(
                self.srcIpv6VpnName, SRCIPV6VPNNAME)

        if self.operation == 'delete':
            cfg_str += self.config_params_func(
                self.ftpServerEnable, FTPSERVERENABLE_DEL)

            cfg_str += self.config_params_func(
                self.ftpIpv6SvrEnble, FTPIPV6SVRENBLE_DEL)

            cfg_str += self.config_params_func(
                self.sourceIpv4Addr, SOURCEIPV4ADDR_DEL)

            cfg_str += self.config_params_func(
                self.sourceInterfaceName, SOURCEINTERFACENAME_DEL)

            cfg_str += self.config_params_func(
                self.listenPortNum, LISTENPORTNUM_DEL)

            cfg_str += self.config_params_func(self.idleTimeout,
                                               IDLETIMEOUT_DEL)

            cfg_str += self.config_params_func(self.acl4Number, ACL4NUMBER_DEL)

            cfg_str += self.config_params_func(self.acl4name, ACL4NAME_DEL)

            cfg_str += self.config_params_func(self.defaultDir, DEFAULTDIR_DEL)

            cfg_str += self.config_params_func(
                self.Ipv6listenPortNum, IPV6LISTENPORTNUM_DEL)

            cfg_str += self.config_params_func(
                self.ipv6IdleTimeout, IPV6IDLETIMEOUT_DEL)

            cfg_str += self.config_params_func(self.acl6name, ACL6NAME_DEL)

            cfg_str += self.config_params_func(self.acl6Number, ACL6NUMBER_DEL)

            cfg_str += self.config_params_func(self.srcIpv6Addr,
                                               SRCIPV6ADDR_DEL)

            cfg_str += self.config_params_func(
                self.srcIpv6VpnName, SRCIPV6VPNNAME_DEL)

        cfg_str += FTPSERVER_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        ftpServerEnable=dict(required=False, type='str'),
        ftpIpv6SvrEnble=dict(required=False, type='str'),
        sourceIpv4Addr=dict(required=False, type='str'),
        sourceInterfaceName=dict(required=False, type='str'),
        listenPortNum=dict(required=False, type='str'),
        idleTimeout=dict(required=False, type='str'),
        acl4Number=dict(required=False, type='str'),
        acl4name=dict(required=False, type='str'),
        defaultDir=dict(required=False, type='str'),
        Ipv6listenPortNum=dict(required=False, type='str'),
        ipv6IdleTimeout=dict(required=False, type='str'),
        acl6name=dict(required=False, type='str'),
        acl6Number=dict(required=False, type='str'),
        srcIpv6Addr=dict(required=False, type='str'),
        srcIpv6VpnName=dict(required=False, type='str'),
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
