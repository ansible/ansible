#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_ftp_server_ftpipblockcfg_config
version_added: "2.6"
short_description: Manages FTP IP block configuration.
description:
    - Manages FTP IP block configuration.
author:Zhaweiwei(@netengine-Ansible)
'''

EXAMPLES = '''
---
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

  - name: "config ftps ftpIpBlockCfg"
    ne_ftp_server_ftpipblockcfg_config:
      ipBlockEnable: false
      provider: "{{ cli }}"

  - name: "delete ftps ftpIpBlockCfg"
    ne_ftp_server_ftpipblockcfg_config:
      ipBlockEnable: false
      operation: delete
      provider: "{{ cli }}"
'''

IPBLOCK_CONFIG = """
<config>
  <ftps xmlns="http://www.huawei.com/netconf/vrp/huawei-ftps">
    <ftpIpBlockCfg>
      <ipBlockEnable></ipBlockEnable>
      <ipBlockFailedTimes></ipBlockFailedTimes>
      <ipBlockPeriod></ipBlockPeriod>
      <ipBlockReactPeriod></ipBlockReactPeriod>
    </ftpIpBlockCfg>
  </ftps>
</config>
"""

IPBLOCK_CFG_HEAD = """
<config>
  <ftps xmlns="http://www.huawei.com/netconf/vrp/huawei-ftps">
    <ftpIpBlockCfg>
"""

IPBLOCK_DEL_HEAD = """
<config>
  <ftps xmlns="http://www.huawei.com/netconf/vrp/huawei-ftps">
    <ftpIpBlockCfg operation="delete">
"""

IPBLOCK_TAIL = """
    </ftpIpBlockCfg>
  </ftps>
</config>
"""

IPBLOCKENABLE = """
      <ipBlockEnable>%s</ipBlockEnable>"""

FAILEDTIMES = """
      <ipBlockFailedTimes>%s</ipBlockFailedTimes>"""

PERIOD = """
      <ipBlockPeriod>%s</ipBlockPeriod>"""

REACTPERIOD = """
      <ipBlockReactPeriod>%s</ipBlockReactPeriod>"""

IPBLOCKENABLE_DEL = """
      <ipBlockEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ipBlockEnable>"""

FAILEDTIMES_DEL = """
      <ipBlockFailedTimes nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ipBlockFailedTimes>"""

PERIOD_DEL = """
      <ipBlockPeriod nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ipBlockPeriod>"""

REACTPERIOD_DEL = """
      <ipBlockReactPeriod nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ipBlockReactPeriod>"""

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
        self.ipBlockEnable = self.module.params['ipBlockEnable']
        self.ipBlockFailedTimes = self.module.params['ipBlockFailedTimes']
        self.ipBlockPeriod = self.module.params['ipBlockPeriod']
        self.ReactPeriod = self.module.params['ReactPeriod']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if not self.ipBlockEnable and self.ipBlockEnable != '' and not self.ipBlockFailedTimes and self.ipBlockFailedTimes != '' \
                and not self.ipBlockPeriod and self.ipBlockPeriod != '' and not self.ReactPeriod and self.ReactPeriod != '':
            self.module.fail_json(
                msg='Error: ipBlockEnable and ipBlockFailedTimes and ipBlockPeriod and ReactPeriod at least one provide')

    def config_params_func(self, arg, rpc_str):
        if arg or arg == '':
            return rpc_str % arg
        return ''

    def config_str(self):
        cfg_str = ''
        cfg_str += IPBLOCK_CFG_HEAD
        if self.operation == 'create':
            cfg_str += self.config_params_func(
                self.ipBlockEnable, IPBLOCKENABLE)

            cfg_str += self.config_params_func(
                self.ipBlockFailedTimes, FAILEDTIMES)

            cfg_str += self.config_params_func(self.ipBlockPeriod, PERIOD)

            cfg_str += self.config_params_func(self.ReactPeriod, REACTPERIOD)

        if self.operation == 'delete':
            cfg_str += self.config_params_func(
                self.ipBlockEnable, IPBLOCKENABLE_DEL)

            cfg_str += self.config_params_func(
                self.ipBlockFailedTimes, FAILEDTIMES_DEL)

            cfg_str += self.config_params_func(self.ipBlockPeriod, PERIOD_DEL)

            cfg_str += self.config_params_func(self.ReactPeriod,
                                               REACTPERIOD_DEL)

        cfg_str += IPBLOCK_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        ipBlockEnable=dict(required=False, type='str'),
        ipBlockFailedTimes=dict(required=False, type='str'),
        ipBlockPeriod=dict(required=False, type='str'),
        ReactPeriod=dict(required=False, type='str'),
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
