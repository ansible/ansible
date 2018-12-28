#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_telnets_telnetserver_getconfig
version_added: "2.6"
short_description: Gets telnet server configuration.
description:
    - Gets telnet server configuration.
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

  - name: "query telnets telnetServer"
    ne_telnet_server_telnetserver_getconfig:
      provider: "{{ cli }}"
'''

TELNETSERVER_GETCONFIG = """
<filter type="subtree">
  <telnets xmlns="http://www.huawei.com/netconf/vrp/huawei-telnets">
    <telnetServer></telnetServer>
  </telnets>
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
        self.results = dict()
        self.results['response'] = []

    def run(self):
        xml_str = get_nc_config(self.module, TELNETSERVER_GETCONFIG)
        self.results["response"].append(xml_str)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict()
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
