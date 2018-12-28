#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_vty_acl_config
version_added: "2.6"
short_description: Manages the access control list for user terminal interface VTY configuration.
description:
    - Manages the access control list for user terminal interface VTY configuration.
author:Zhaweiwei(@netengine-Ansible)
'''

EXAMPLES = '''

- name: nedevice vty module test
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

  - name: "config vty acl"
    ne_vty_acl_config:
      lineIndex: 45
      acl4InNum: 2000
      provider: "{{ cli }}"

  - name: "delete vty acl"
    ne_vty_acl_config:
      lineIndex: 45
      acl4InNum: 2000
      operation: delete
      provider: "{{ cli }}"
'''

VTY_ACL_CONFIG = """
<config>
  <vty xmlns="http://www.huawei.com/netconf/vrp/huawei-vty">
    <lineCfg>
    </lineCfg>
  </vty>
</config>
"""

VTY_ACL_CFG_HEAD = """
<config>
  <vty xmlns="http://www.huawei.com/netconf/vrp/huawei-vty">
    <lineCfgs>
      <lineCfg>
"""

VTY_ACL_DEL_HEAD = """
<config>
  <vty xmlns="http://www.huawei.com/netconf/vrp/huawei-vty">
    <lineCfgs>
      <lineCfg operation="delete">
"""

VTY_ACL_TAIL = """
      </lineCfg>
    </lineCfgs>
  </vty>
</config>
"""

LINEINDEX = """
        <lineIndex>%s</lineIndex>"""

ACL4INBOUND = """
        <acl4InBound>%s</acl4InBound>"""

ACL4OUTBOUND = """
        <acl4OutBound>%s</acl4OutBound>"""

ACL4INNUM = """
        <acl4InNum>%s</acl4InNum>"""

ACL6INBOUND = """
        <acl6InBound>%s</acl6InBound>"""

ACL6OUTBOUND = """
        <acl6OutBound>%s</acl6OutBound>"""

ACL4OUTNUM = """
        <acl4OutNum>%s</acl4OutNum>"""

ACL6INNUM = """
        <acl6InNum>%s</acl6InNum>"""

ACL6OUTNUM = """
        <acl6OutNum>%s</acl6OutNum>"""

LINEINDEX_DEL = """
        <lineIndex nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</lineIndex>"""

ACL4INBOUND_DEL = """
        <acl4InBound nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl4InBound>"""

ACL4OUTBOUND_DEL = """
        <acl4OutBound nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl4OutBound>"""

ACL4INNUM_DEL = """
        <acl4InNum nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl4InNum>"""

ACL6INBOUND_DEL = """
        <acl6InBound nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl6InBound>"""

ACL6OUTBOUND_DEL = """
        <acl6OutBound nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl6OutBound>"""

ACL4OUTNUM_DEL = """
        <acl4OutNum nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl4OutNum>"""

ACL6INNUM_DEL = """
        <acl6InNum nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl6InNum>"""

ACL6OUTNUM_DEL = """
        <acl6OutNum nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl6OutNum>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.lineIndex = self.module.params['lineIndex']
        self.acl4InBound = self.module.params['acl4InBound']
        self.acl4OutBound = self.module.params['acl4OutBound']
        self.acl4InNum = self.module.params['acl4InNum']
        self.acl6InBound = self.module.params['acl6InBound']
        self.acl6OutBound = self.module.params['acl6InBound']
        self.acl4OutNum = self.module.params['acl4OutNum']
        self.acl6InNum = self.module.params['acl6InNum']
        self.acl6OutNum = self.module.params['acl6OutNum']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params_func(self, arg):
        if not arg and arg != '':
            return True
        return False

    def check_params(self):
        if self.check_params_func(self.acl4InBound) and self.check_params_func(self.acl4OutBound) \
                and self.check_params_func(self.acl4InNum) and self.check_params_func(self.acl6InBound) and self.check_params_func(self.acl6OutBound) \
                and self.check_params_func(self.acl4OutNum) and self.check_params_func(self.acl6InNum) and self.check_params_func(self.acl6OutNum):
            self.module.fail_json(msg='Error: acl4InBound and acl4OutBound and acl4InNum and acl6InBound \
 and acl6OutBound and acl4OutNum and acl6InNum and acl6OutNum at least one provide')

    def config_params_func(self, arg, rpc_str):
        if arg or arg == '':
            return rpc_str % arg
        return ''

    def config_str(self):
        cfg_str = ''
        cfg_str += VTY_ACL_CFG_HEAD
        cfg_str += self.config_params_func(self.lineIndex, LINEINDEX)

        if self.operation == 'create':
            cfg_str += self.config_params_func(self.acl4InBound, ACL4INBOUND)

            cfg_str += self.config_params_func(self.acl4OutBound, ACL4OUTBOUND)

            cfg_str += self.config_params_func(self.acl4InNum, ACL4INNUM)

            cfg_str += self.config_params_func(self.acl6InBound, ACL6INBOUND)

            cfg_str += self.config_params_func(self.acl6OutBound, ACL6OUTBOUND)

            cfg_str += self.config_params_func(self.acl4OutNum, ACL4OUTNUM)

            cfg_str += self.config_params_func(self.acl6InNum, ACL6INNUM)

            cfg_str += self.config_params_func(self.acl6OutNum, ACL6OUTNUM)

        if self.operation == 'delete':
            cfg_str += self.config_params_func(self.acl4InBound,
                                               ACL4INBOUND_DEL)

            cfg_str += self.config_params_func(
                self.acl4OutBound, ACL4OUTBOUND_DEL)

            cfg_str += self.config_params_func(self.acl4InNum, ACL4INNUM_DEL)

            cfg_str += self.config_params_func(self.acl6InBound,
                                               ACL6INBOUND_DEL)

            cfg_str += self.config_params_func(
                self.acl6OutBound, ACL6OUTBOUND_DEL)

            cfg_str += self.config_params_func(self.acl4OutNum, ACL4OUTNUM_DEL)

            cfg_str += self.config_params_func(self.acl6InNum, ACL6INNUM_DEL)

            cfg_str += self.config_params_func(self.acl6OutNum, ACL6OUTNUM_DEL)

        cfg_str += VTY_ACL_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        lineIndex=dict(required=True, type='str'),
        acl4InBound=dict(required=False, type='str'),
        acl4OutBound=dict(required=False, type='str'),
        acl4InNum=dict(required=False, type='str'),
        acl6InBound=dict(required=False, type='str'),
        acl6OutBound=dict(required=False, type='str'),
        acl4OutNum=dict(required=False, type='str'),
        acl6InNum=dict(required=False, type='str'),
        acl6OutNum=dict(required=False, type='str'),
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
