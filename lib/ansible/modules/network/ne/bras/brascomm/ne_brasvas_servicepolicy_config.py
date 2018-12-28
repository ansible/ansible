#!/usr/bin/python
# coding=utf-8
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
from xml.etree import ElementTree
import copy
import logging
import re
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_brasvas_servicepolicy_config
version_added: "2.6"
short_description: Creates a value-added service policy template.
description:
    - Creates a value-added service policy template.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    servicePolicyName:
        description:
            - Specifies the name of a value-added service policy.
        required: false
    servicePolicyType:
        description:
            - Indicates a service policy.
        required: false
        choices: ['edsg', 'portal', 'mirror']
    operation:
        description:
            - Specifies the operation type.
              if the operation is get,the servicePolicyType cannot take parameters,
              otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_brasvas_servicepolicy_config test
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

    - name: "Creates a value-added service policy template, the operation type is 'create'."
      ne_brasvas_servicepolicy_config:
        servicePolicyName='nameTest1'
        servicePolicyType='edsg'
        operation='create'
        provider: "{{ cli }}"

    - name: "Creates a value-added service policy template, the operation type is 'delete'."
      ne_brasvas_servicepolicy_config:
        servicePolicyName='nameTest1'
        servicePolicyType='edsg'
        operation='delete'
        provider: "{{ cli }}"

    - name: "Creates a value-added service policy template, the operation type is 'get'."
      ne_brasvas_servicepolicy_config:
        servicePolicyName='nameTest1'
        servicePolicyType='edsg'
        operation='get'
        provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "servicePolicyName": "nameTest1",
        "servicePolicyType": "edsg",
        "operation": "create"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "servicePolicys": [
            {
                "servicePolicyName": "nameTest1",
                "servicePolicyType": "edsg"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "servicePolicys": [
            {
                "servicePolicyName": "nameTest1",
                "servicePolicyType": "edsg"
            }
        ]
    }
'''


SERVICEPOLICYS_CONFIG_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <servicePolicys>
"""

SERVICEPOLICYS_CONFIG_TAIL = """
        </servicePolicys>
      </brasvas>
    </config>
"""

SERVICEPOLICY_CREATE = """
          <servicePolicy nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICY_DELETE = """
          <servicePolicy nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICY_MERGE = """
          <servicePolicy nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICY_CONFIG_END = """
          </servicePolicy>"""

SERVICEPOLICYS_GET_HEAD = """
  <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <servicePolicys>
        <servicePolicy>"""

SERVICEPOLICYS_GET_TAIL = """
        </servicePolicy>
      </servicePolicys>
    </brasvas>
  </filter>"""

SERVICEPOLICYNAME = """
      <servicePolicyName>%s</servicePolicyName>"""

SERVICEPOLICYTYPE = """
      <servicePolicyType>%s</servicePolicyType>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

        # module input info
        self.servicePolicyName = self.module.params['servicePolicyName']
        self.servicePolicyType = self.module.params['servicePolicyType']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.servicePolicyName is not None:
            self.proposed["servicePolicyName"] = self.servicePolicyName
        if self.servicePolicyType is not None:
            self.proposed["servicePolicyType"] = self.servicePolicyType
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def create_set_delete_process(self):
        """get config rpc string"""
        cfg_str = ''
        self.changed = True
        cfg_str += SERVICEPOLICYS_CONFIG_HEAD
        if self.operation == 'create':
            cfg_str += SERVICEPOLICY_CREATE
        if self.operation == 'merge':
            cfg_str += SERVICEPOLICY_MERGE
        if self.operation == 'delete':
            cfg_str += SERVICEPOLICY_DELETE

        if self.servicePolicyName is not None:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName
        if self.servicePolicyType is not None:
            cfg_str += SERVICEPOLICYTYPE % self.servicePolicyType

        cfg_str += SERVICEPOLICY_CONFIG_END
        cfg_str += SERVICEPOLICYS_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += SERVICEPOLICYS_GET_HEAD

        if self.servicePolicyName is not None:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName

        if self.operation == 'get':
            if self.servicePolicyType is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')

        cfg_str += SERVICEPOLICYS_GET_TAIL

        xml_str = get_nc_config(self.module, cfg_str)

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas"', "")

        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        root = ElementTree.fromstring(xml_str)
        container_attributes_Info = root.findall(
            "brasvas/servicePolicys/servicePolicy")
        attributes_Info["servicePolicys"] = list()

        if len(container_attributes_Info) != 0:
            for container_node in container_attributes_Info:
                container_Table = dict()
                for leaf_attributes_Info in container_node:
                    if leaf_attributes_Info.tag in ["servicePolicyName",
                                                    "servicePolicyType"]:
                        container_Table[leaf_attributes_Info.tag] = leaf_attributes_Info.text
                attributes_Info["servicePolicys"].append(container_Table)

        return attributes_Info

    def run(self):
        # self.check_params()

        self.existing = self.get_info_process()
        self.results['existing'] = self.existing

        if self.operation != 'get':
            self.create_set_delete_process()
            self.end_state = self.get_info_process()
            self.results['end_state'] = self.end_state

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.module.exit_json(**self.results)


def main():
    """ main module """
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    argument_spec = dict(
        servicePolicyName=dict(required=False, type='str'),
        servicePolicyType=dict(
            required=False, choices=[
                'edsg', 'portal', 'mirror']),
        operation=dict(
            required=True,
            choices=[
                'create',
                'delete',
                'merge',
                'get']),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
