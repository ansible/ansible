#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_telnets_loginfailalarm_config
version_added: "2.6"
short_description: Manages telnet logining fail alarm configuration.
description:
    - Manages telnet logining fail alarm configuration.
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

  - name: "config telnets loginFailAlarm"
    ne_telnet_server_loginfailalarm_config:
      upperLimit: 31
      provider: "{{ cli }}"

  - name: "delete telnets loginFailAlarm"
    ne_telnet_server_loginfailalarm_config:
      upperLimit: 31
      operation: delete
      provider: "{{ cli }}"
'''

LOGINFAILALARM_CONFIG = """
<config>
  <telnets xmlns="http://www.huawei.com/netconf/vrp/huawei-telnets">
    <loginFailAlarm>
      <upperLimit>31</upperLimit>
      <lowerLimit>21</lowerLimit>
      <period>6</period>
    </loginFailAlarm>
  </telnets>
</config>
"""

LOGINFAILALARM_CFG_HEAD = """
<config>
  <telnets xmlns="http://www.huawei.com/netconf/vrp/huawei-telnets">
    <loginFailAlarm>
"""

LOGINFAILALARM_DEL_HEAD = """
<config>
  <telnets xmlns="http://www.huawei.com/netconf/vrp/huawei-telnets">
    <loginFailAlarm operation="delete">
"""

LOGINFAILALARM_TAIL = """
    </loginFailAlarm>
  </telnets>
</config>
"""

UPPERLIMIT = """
      <upperLimit>%s</upperLimit>"""

LOWERLIMIT = """
      <lowerLimit>%s</lowerLimit>"""

PERIOD = """
      <period>%s</period>"""

UPPERLIMIT_DEL = """
      <upperLimit nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</upperLimit>"""

LOWERLIMIT_DEL = """
      <lowerLimit nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</lowerLimit>"""

PERIOD_DEL = """
      <period nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</period>"""

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
        self.upperLimit = self.module.params['upperLimit']
        self.lowerLimit = self.module.params['lowerLimit']
        self.period = self.module.params['period']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if not self.upperLimit and not self.lowerLimit and not self.period and self.upperLimit != '' and self.lowerLimit != '' and self.period != '':
            self.module.fail_json(
                msg='Error: upperLimit and lowerLimit and period at least one provide')

    def config_params_func(self, arg, rpc_str):
        if arg or arg == '':
            return rpc_str % arg
        return ''

    def config_str(self):
        cfg_str = ''
        cfg_str += LOGINFAILALARM_CFG_HEAD
        if self.operation == 'create':
            cfg_str += self.config_params_func(self.upperLimit, UPPERLIMIT)

            cfg_str += self.config_params_func(self.lowerLimit, LOWERLIMIT)

            cfg_str += self.config_params_func(self.period, PERIOD)

        if self.operation == 'delete':
            cfg_str += self.config_params_func(self.upperLimit, UPPERLIMIT_DEL)

            cfg_str += self.config_params_func(self.lowerLimit, LOWERLIMIT_DEL)

            cfg_str += self.config_params_func(self.period, PERIOD_DEL)

        cfg_str += LOGINFAILALARM_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        upperLimit=dict(required=False, type='str'),
        lowerLimit=dict(required=False, type='str'),
        period=dict(required=False, type='str'),
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
