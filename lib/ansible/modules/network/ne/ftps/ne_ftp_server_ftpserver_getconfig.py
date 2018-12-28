#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

DOCUMENTATION = '''
---
module: ne_ftp_server_ftpserver_getconfig
version_added: "2.6"
short_description: Gets FTP server configuration.
description:
    - Gets FTP server configuration.
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

  - name: "query ftps ftpServer"
    ne_ftp_server_ftpserver_getconfig:
      provider: "{{ cli }}"
'''

FTPSERVER_GETCONFIG = """
<filter type="subtree">
  <ftps xmlns="http://www.huawei.com/netconf/vrp/huawei-ftps">
    <ftpServer></ftpServer>
  </ftps>
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
        xml_str = get_nc_config(self.module, FTPSERVER_GETCONFIG)
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
