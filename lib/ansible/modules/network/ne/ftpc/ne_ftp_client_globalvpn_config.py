#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_ftp_client_globalvpn_config
version_added: "2.6"
short_description: Manages FTP global VPN configuration.
description:
    - Manages FTP global VPN configuration.
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
  connection: local
  gather_facts: no


  tasks:

- name: nedevice ftpc module test
  hosts: nedevice
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: "config ftpc globalVpn"
    ne_ftp_client_globalvpn_config:
      vpnName: vpn1
      provider: "{{ cli }}"

  - name: "delete ftpc globalVpn"
    ne_ftp_client_globalvpn_config:
      vpnName: vpn1
      operation: delete
      provider: "{{ cli }}"
'''

FTPCLIENT_CONFIG = """
<config>
  <ftpc xmlns="http://www.huawei.com/netconf/vrp/huawei-ftpc">
    <globalVpn>
      <vpnName></vpnName>
      <ipv6VpnName></ipv6VpnName>
    </globalVpn>
  </ftpc>
</config>
"""

GLOBALVPN_CFG_HEAD = """
<config>
  <ftpc xmlns="http://www.huawei.com/netconf/vrp/huawei-ftpc">
    <globalVpn>
"""

GLOBALVPN_DEL_HEAD = """
<config>
  <ftpc xmlns="http://www.huawei.com/netconf/vrp/huawei-ftpc">
    <globalVpn operation="delete">
"""

GLOBALVPN_TAIL = """
    </globalVpn>
  </ftpc>
</config>
"""

VPNNAME = """
      <vpnName>%s</vpnName>"""

IPV6VPNNAME = """
      <ipv6VpnName>%s</ipv6VpnName>"""

VPNNAME_DEL = """
      <vpnName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</vpnName>"""

IPV6VPNNAME_DEL = """
      <ipv6VpnName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ipv6VpnName>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.vpnName = self.module.params['vpnName']
        self.ipv6VpnName = self.module.params['ipv6VpnName']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if not self.vpnName and not self.ipv6VpnName and self.vpnName != '' and self.ipv6VpnName != '':
            self.module.fail_json(
                msg='Error: vpnName and ipv6VpnName at least one provide')

    def config_params_func(self, arg, rpc_str):
        if arg or arg == '':
            return rpc_str % arg
        return ''

    def config_str(self):
        cfg_str = ''
        cfg_str += GLOBALVPN_CFG_HEAD
        if self.operation == 'create':
            cfg_str += self.config_params_func(self.vpnName, VPNNAME)

            cfg_str += self.config_params_func(self.ipv6VpnName, IPV6VPNNAME)

        if self.operation == 'delete':
            cfg_str += self.config_params_func(self.vpnName, VPNNAME_DEL)

            cfg_str += self.config_params_func(self.ipv6VpnName,
                                               IPV6VPNNAME_DEL)

        cfg_str += GLOBALVPN_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        vpnName=dict(required=False, type='str'),
        ipv6VpnName=dict(required=False, type='str'),
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
