#!/usr/bin/python
# coding=utf-8

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
DOCUMENTATION = '''
---
module: ne_acl_configGroup
version_added: "2.6"
short_description: Config configuration of acl groups.
description:
    - Config configuration of acl groups.
author: Chenyang && Shaofei (@netengine-Ansible)
options:
    aclNumOrName:
        description:
            - Config the acl aclNumOrName of a acl Group.
        required: true
        default: null
    aclType:
        description:
            - Config the acl aclType of a acl Group.
        required: false
        default: null
    aclMatchOrder:
        description:
            - Config the acl aclMatchOrder of a acl Group.
        required: false
        default: null
    aclStep:
        description:
            - Config the acl aclStep of a acl Group.
        required: false
        default: null
    aclDescription:
        description:
            - Config the acl aclDescription of a acl Group.
        required: false
        default: null
    operation:
        description:
            - Specifies the action to be performed on the ACL group.
        required: false
        default: all
        choices: ['create', 'delete', 'clear']
'''

EXAMPLES = '''
- name: Config acl Group configuration
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
  - name: Config acl Group configuration
    ne_acl_getGroup:
      aclNumOrName: sf10
      aclType: Advance"
      operation: create
      provider: "{{ cli }}"
'''

RETURN = '''
"response":
    [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
            <rpc-reply xmlns:nc-ext=\"urn:huawei:yang:huawei-ietf-netconf-ext\" nc-ext:flow-id=\"66\">
                <ok/>
            </rpc-reply>"
    ]
'''


ACLGROUP_CFG_HEAD = """
<config>
      <acl xmlns="http://www.huawei.com/netconf/vrp/huawei-acl">
        <aclGroups>
          <aclGroup>
"""

ACLGROUP_CFG_DELETE_HEAD = """
<config>
      <acl xmlns="http://www.huawei.com/netconf/vrp/huawei-acl">
        <aclGroups>
          <aclGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

ACLGROUP_TAIL = """
      </aclGroup>
    </aclGroups>
  </acl>
</config>
"""

ACLNUMORNAME = """
      <aclNumOrName>%s</aclNumOrName>"""

ACLTYPE = """
      <aclType>%s</aclType>"""

ACLMATCHORDER = """
      <aclMatchOrder>%s</aclMatchOrder>"""

ACLSTEP = """
      <aclStep>%s</aclStep>"""

ACLDESCRIPTION = """
      <aclDescription>%s</aclDescription>"""

ACLSTEP_DELETE = """
      <aclStep nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclStep>"""

ACLDESCRIPTION_DELETE = """
      <aclDescription nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</aclDescription>"""


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
        self.aclType = self.module.params['aclType']
        self.aclMatchOrder = self.module.params['aclMatchOrder']
        self.aclStep = self.module.params['aclStep']
        self.aclDescription = self.module.params['aclDescription']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if self.aclStep:
            if int(self.aclStep) < 1 or int(self.aclStep) > 20:
                self.module.fail_json(
                    msg='Error: The aclStep not in the range from 1 to 20.')

        if self.aclNumOrName:
            if self.aclNumOrName.isdigit():
                int_aclNum = int(self.aclNumOrName)
                if int(int_aclNum) < 2000 or int(int_aclNum) > 3999 :
                    self.module.fail_json(
                        msg='Error: The aclNumber not in the range from 2000 to 3999.')

    def config_str(self):
        cfg_str = ''
        if self.operation == 'create':
            cfg_str += ACLGROUP_CFG_HEAD
            cfg_str += ACLNUMORNAME % self.aclNumOrName
            if self.aclType:
                cfg_str += ACLTYPE % self.aclType
            if self.aclMatchOrder:
                cfg_str += ACLMATCHORDER % self.aclMatchOrder
            if self.aclStep:
                cfg_str += ACLSTEP % self.aclStep
            if self.aclDescription:
                cfg_str += ACLDESCRIPTION % self.aclDescription

        if self.operation == 'clear':
            cfg_str += ACLGROUP_CFG_HEAD
            cfg_str += ACLNUMORNAME % self.aclNumOrName
            if self.aclStep:
                cfg_str += ACLSTEP_DELETE % self.aclStep
            if self.aclDescription:
                cfg_str += ACLDESCRIPTION_DELETE % self.aclDescription

        if self.operation == 'delete':
            cfg_str += ACLGROUP_CFG_DELETE_HEAD
            cfg_str += ACLNUMORNAME % self.aclNumOrName

        cfg_str += ACLGROUP_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        aclNumOrName=dict(required=False, type='str'),
        aclType=dict(required=False, choices=['Basic', 'Advance']),
        aclMatchOrder=dict(required=False, choices=['Config', 'Auto']),
        aclStep=dict(required=False, type='int'),
        aclDescription=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'delete',
                'clear'],
            default='create'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
