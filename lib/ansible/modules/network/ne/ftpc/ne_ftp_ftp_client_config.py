#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_ftp_ftp_client_config
version_added: "2.6"
short_description: Manages FTP client configuration.
description:
    - Manages FTP client configuration.
author:Zhaweiwei(@netengine-Ansible)
'''

EXAMPLES = '''

- name: nedevice ftpc module test
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

  - name: "delete ftpc ftpClient"
    ne_ftp_client_config:
      ipv4_addr: 1.1.1.1
      operation: delete
      provider: "{{ cli }}"
'''

FTPCLIENT_CONFIG = """
<config>
  <ftpc xmlns="http://www.huawei.com/netconf/vrp/huawei-ftpc">
    <ftpClient>
      <sourceIpv4Address></sourceIpv4Address>
      <sourceInterfaceName></sourceInterfaceName>
    </ftpClient>
  </ftpc>
</config>
"""

FTPCLIENT_CFG_HEAD = """
<config>
  <ftpc xmlns="http://www.huawei.com/netconf/vrp/huawei-ftpc">
    <ftpClient>
"""

FTPCLIENT_DEL_HEAD = """
<config>
  <ftpc xmlns="http://www.huawei.com/netconf/vrp/huawei-ftpc">
    <ftpClient operation="delete">
"""

FTPCLIENT_TAIL = """
    </ftpClient>
  </ftpc>
</config>
"""

IPV4ADDR = """
      <sourceIpv4Address>%s</sourceIpv4Address>"""

INTERFACE = """
      <sourceInterfaceName>%s</sourceInterfaceName>"""

IPV4ADDR_DEL = """
      <sourceIpv4Address nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sourceIpv4Address>"""

INTERFACE_DEL = """
      <sourceInterfaceName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sourceInterfaceName>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.sourceIpv4Address = self.module.params['sourceIpv4Address']
        self.interface_name = self.module.params['interface_name']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if not self.sourceIpv4Address and not self.interface_name and self.sourceIpv4Address != '' and self.interface_name != '':
            self.module.fail_json(
                msg='Error: sourceIpv4Address and interface_name at least one provide')

    def config_params_func(self, arg, rpc_str):
        if arg or arg == '':
            return rpc_str % arg
        return ''

    def config_str(self):
        cfg_str = ''
        cfg_str += FTPCLIENT_CFG_HEAD
        if self.operation == 'create':
            cfg_str += self.config_params_func(
                self.sourceIpv4Address, IPV4ADDR)

            cfg_str += self.config_params_func(self.interface_name, INTERFACE)

        if self.operation == 'delete':
            cfg_str += self.config_params_func(
                self.sourceIpv4Address, IPV4ADDR_DEL)

            cfg_str += self.config_params_func(
                self.interface_name, INTERFACE_DEL)

        cfg_str += FTPCLIENT_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        sourceIpv4Address=dict(required=False, type='str'),
        interface_name=dict(required=False, type='str'),
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
