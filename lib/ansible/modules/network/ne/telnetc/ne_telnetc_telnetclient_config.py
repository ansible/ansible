#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_telnetc_telnetclient_config
version_added: "2.6"
short_description: Manages telnet client configuration.
description:
    - Manages telnet client configuration.
author:Zhaweiwei(@netengine-Ansible)
'''

EXAMPLES = '''

- name: nedevice telnetc module test
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

  - name: "config telnetc telnetclient"
    ne_telnet_client_telnetclient_config:
      ipv4_addr: 1.1.1.1
      provider: "{{ cli }}"

  - name: "delete telnetc telnetclient"
    ne_telnet_client_telnetclient_config:
      ipv4_addr: 1.1.1.1
      operation: delete
      provider: "{{ cli }}"
'''

FTPCLIENT_CONFIG = """
<config>
  <telnetc xmlns="http://www.huawei.com/netconf/vrp/huawei-telnetc">
    <telnetClient>
      <telnetSrcIpv4Addr></telnetSrcIpv4Addr>
      <telnetSrcInterface></telnetSrcInterface>
      <packetDscp></packetDscp>
    </telnetClient>
  </telnetc>
</config>
"""

TELNETCLIENT_CFG_HEAD = """
<config>
  <telnetc xmlns="http://www.huawei.com/netconf/vrp/huawei-telnetc">
    <telnetClient>
"""

TELNETCLIENT_DEL_HEAD = """
<config>
  <telnetc xmlns="http://www.huawei.com/netconf/vrp/huawei-telnetc">
    <telnetClient operation="delete">
"""

TELNETCLIENT_TAIL = """
    </telnetClient>
  </telnetc>
</config>
"""

IPV4ADDR = """
      <telnetSrcIpv4Addr>%s</telnetSrcIpv4Addr>"""

INTERFACE = """
      <telnetSrcInterface>%s</telnetSrcInterface>"""

PACKETDSCP = """
      <packetDscp>%s</packetDscp>"""

IPV4ADDR_DEL = """
      <telnetSrcIpv4Addr nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</telnetSrcIpv4Addr>"""

INTERFACE_DEL = """
      <telnetSrcInterface nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</telnetSrcInterface>"""

PACKETDSCP_DEL = """
      <packetDscp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</packetDscp>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.ipv4_addr = self.module.params['ipv4_addr']
        self.interface_name = self.module.params['interface_name']
        self.packetDscp = self.module.params['packetDscp']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if not self.ipv4_addr and self.ipv4_addr != '' and not self.interface_name \
           and self.interface_name != '' and not self.packetDscp and self.packetDscp != '':
            self.module.fail_json(
                msg='Error: ipv4_addr and interface_name and packetDscp at least one provide')

    def config_params_func(self, arg, rpc_str):
        if arg or arg == '':
            return rpc_str % arg
        return ''

    def config_str(self):
        cfg_str = ''
        cfg_str += TELNETCLIENT_CFG_HEAD
        if self.operation == 'create':
            cfg_str += self.config_params_func(self.ipv4_addr, IPV4ADDR)

            cfg_str += self.config_params_func(self.interface_name, INTERFACE)

            cfg_str += self.config_params_func(self.packetDscp, PACKETDSCP)

        if self.operation == 'delete':
            cfg_str += self.config_params_func(self.ipv4_addr, IPV4ADDR_DEL)

            cfg_str += self.config_params_func(
                self.interface_name, INTERFACE_DEL)

            cfg_str += self.config_params_func(self.packetDscp, PACKETDSCP_DEL)

        cfg_str += TELNETCLIENT_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        ipv4_addr=dict(required=False, type='str'),
        interface_name=dict(required=False, type='str'),
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
