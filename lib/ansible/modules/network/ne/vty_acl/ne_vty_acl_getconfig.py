#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_vty_acl_getconfig
version_added: "2.6"
short_description: Gets the access control list for user terminal interface VTY configuration.
description:
    - Gets the access control list for user terminal interface VTY configuration.
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

  - name: "query vty acl"
    ne_vty_acl_getconfig:
      provider: "{{ cli }}"
'''

VTY_ACL_GETCONFIG = """
<filter type="subtree">
  <vty xmlns="http://www.huawei.com/netconf/vrp/huawei-vty">
    <lineCfgs>
      <lineCfg></lineCfg>
    </lineCfgs>
  </vty>
</filter>
"""

VTY_ACL_HEAD = """
<filter type="subtree">
  <vty xmlns="http://www.huawei.com/netconf/vrp/huawei-vty">
    <lineCfgs>
      <lineCfg>
"""

VTY_ACL_LINEINDEX = """
        <lineIndex>%s</lineIndex>"""

VTY_ACL_TAIL = """
        <acl4InBound></acl4InBound>
        <acl4OutBound></acl4OutBound>
        <acl4InNum></acl4InNum>
        <acl6InBound></acl6InBound>
        <acl6OutBound></acl6OutBound>
        <acl4OutNum></acl4OutNum>
        <acl6InNum></acl6InNum>
        <acl6OutNum></acl6OutNum>
      </lineCfg>
    </lineCfgs>
  </vty>
</filter>
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
        self.lineIndex = self.module.params['lineIndex']
        self.results = dict()
        self.results['response'] = []

    def get_config_str(self):
        cfg_str = ''
        cfg_str += VTY_ACL_HEAD

        if self.lineIndex:
            cfg_str += VTY_ACL_LINEINDEX % self.lineIndex
        else:
            cfg_str += '        <lineIndex></lineIndex>'

        cfg_str += VTY_ACL_TAIL

        return cfg_str

    def run(self):
        xml_str = get_nc_config(self.module, self.get_config_str())
        self.results["response"].append(xml_str)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        lineIndex=dict(required=False, type='str'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
