#!/usr/bin/python
# coding=utf-8


from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
DOCUMENTATION = '''
---
module: ne_acl_getGroup
version_added: "2.6"
short_description: Get configuration of acl groups.
description:
    - Get configuration of acl groups.
author: Chenyang && Shaofei (@netengine-Ansible)
options:
    aclNumOrName:
        description:
            - Specify the acl name of a Group.
        required: true
        default: null
    operation:
        description:
            - Returns the specified element of acl group.
        required: false
        default: all
        choices: ['all', 'aclType', 'aclMatchOrder', 'aclStep', 'aclDescription']
'''

EXAMPLES = '''
- name: get acl Group configuration
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
  - name: Get acl Group configuration
    ne_acl_getGroup:
      aclNumOrName: sf10
      operation: all
      provider: "{{ cli }}"
'''

RETURN = '''
"response":
    [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><data>
           <acl xmlns=\"http://www.huawei.com/netconf/vrp/huawei-acl\">
                <aclGroups>
                    <aclGroup>
                        <aclNumOrName>sf10</aclNumOrName>
                        <aclMatchOrder>Config</aclMatchOrder>
                        <aclStep>5</aclStep>
                        <aclType>Advance</aclType>
                    </aclGroup>
                </aclGroups>
            </acl>
        </data>"
    ]
'''


ACLGROUP_GET_HEAD = """
    <filter type="subtree">
      <acl:acl xmlns:acl="http://www.huawei.com/netconf/vrp/huawei-acl">
        <acl:aclGroups>
"""

ACLGROUP_GET_TAIL = """
        </acl:aclGroups>
      </acl:acl>
    </filter>
"""

ACLGROUP_GET_GROUP_BEGIN = """
<acl:aclGroup>"""

ACLGROUP_GET_GROUP = """
<acl:aclNumOrName>%s</acl:aclNumOrName>"""

ACLGROUP_GET_GROUP_END = """
</acl:aclGroup>"""

ACLGROUP_GET_ACLTYPE = """
<acl:aclType/>"""

ACLGROUP_GET_ACLMATCHORDER = """
<acl:aclMatchOrder/>"""

ACLGROUP_GET_ACLSTEP = """
<acl:aclStep/>"""

ACLGROUP_GET_ACLDESCRIPTION = """
<acl:aclDescription/>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.aclNumOrName = self.module.params['aclNumOrName']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def config_str_group(self):
        cfg_str_group = ''
        if self.operation == 'aclType':
            cfg_str_group += ACLGROUP_GET_ACLTYPE
        if self.operation == 'aclMatchOrder':
            cfg_str_group += ACLGROUP_GET_ACLMATCHORDER
        if self.operation == 'aclStep':
            cfg_str_group += ACLGROUP_GET_ACLSTEP
        if self.operation == 'aclDescription':
            cfg_str_group += ACLGROUP_GET_ACLDESCRIPTION
        return cfg_str_group

    def config_str(self):
        cfg_str = ''
        cfg_str += ACLGROUP_GET_HEAD
        cfg_str += ACLGROUP_GET_GROUP_BEGIN
        if self.aclNumOrName:
            cfg_str += ACLGROUP_GET_GROUP % self.aclNumOrName
        cfg_str += self.config_str_group()
        cfg_str += ACLGROUP_GET_GROUP_END
        cfg_str += ACLGROUP_GET_TAIL

        return cfg_str

    def run(self):
        recv_xml = get_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        aclNumOrName=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'all',
                'aclType',
                'aclMatchOrder',
                'aclStep',
                'aclDescription'],
            default='all'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
