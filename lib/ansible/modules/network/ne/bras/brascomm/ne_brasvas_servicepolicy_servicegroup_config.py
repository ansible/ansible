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
module: ne_brasvas_servicepolicy_servicegroup_config
version_added: "2.6"
short_description: Specifies a service group for a service policy.
description:
    - Specifies a service group for a service policy.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    servicePolicyName:
        description:
            - Specifies the name of a value-added service policy.
        required: false
    serviceGroupName:
        description:
            - Specifies the name of a service group.
        required: false
    serviceGroupDirection:
        description:
            - Indicates the direction for a service group..
        required: false
        choices: ['inbound', 'outbound', 'both']
    serviceGroupPriority:
        description:
            - Specifies a priority value that a service matches,The value is an integer ranging from 0 to 1000.
        required: false
    operation:
        description:
            - Specifies the operation type.
              if the operation is get,the serviceGroupName and serviceGroupDirection and serviceGroupPriority cannot take parameters,
              otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_brasvas_servicepolicy_servicegroup_config test
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

    - name: "Specifies a service group for a service policy, the operation type is 'create'."
      ne_brasvas_servicepolicy_servicegroup_config:
        servicePolicyName='nameTest1'
        serviceGroupName='nameTest2'
        serviceGroupDirection='inbound'
        serviceGroupPriority='1'
        operation='create'
        provider: "{{ cli }}"

    - name: "Specifies a service group for a service policy, the operation type is 'delete'."
      ne_brasvas_servicepolicy_servicegroup_config:
        servicePolicyName='nameTest1'
        serviceGroupName='nameTest2'
        serviceGroupDirection='inbound'
        serviceGroupPriority='1'
        operation='create'
        provider: "{{ cli }}"

    - name: "Specifies a service group for a service policy, the operation type is 'get'."
      ne_brasvas_servicepolicy_servicegroup_config:
        servicePolicyName='nameTest1'
        serviceGroupName='nameTest2'
        serviceGroupDirection='inbound'
        serviceGroupPriority='1'
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
        "serviceGroupName": "nameTest2",
        "serviceGroupDirection": "inbound",
        "serviceGroupPriority": 1,
        "operation": "create"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "serviceGroups": [
            {
                "servicePolicyName": "nameTest1",
                "serviceGroupName": "nameTest2",
                "serviceGroupDirection": "inbound",
                "serviceGroupPriority": 1
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "serviceGroups": [
            {
                "servicePolicyName": "nameTest1",
                "serviceGroupName": "nameTest2",
                "serviceGroupDirection": "inbound",
                "serviceGroupPriority": 1
            }
        ]
    }
'''


SERVICEPOLICYS_SERVICEGROUP_CONFIG_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <servicePolicys>
          <servicePolicy>
"""

SERVICEPOLICYS_SERVICEGROUP_CONFIG_TAIL = """
          </servicePolicy>
        </servicePolicys>
      </brasvas>
    </config>
"""

SERVICEPOLICYS_SERVICEGROUP_CREATE = """
          <refServiceGroup nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICYS_SERVICEGROUP_DELETE = """
          <refServiceGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICYS_SERVICEGROUP_MERGE = """
          <refServiceGroup nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICYS_SERVICEGROUP_CONFIG_END = """
          </refServiceGroup>"""

SERVICEPOLICYS_SERVICEGROUP_GET_HEAD = """
  <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <servicePolicys>
        <servicePolicy>"""

SERVICEPOLICYS_SERVICEGROUP_GET_TAIL = """
          <refServiceGroup/>
        </servicePolicy>
      </servicePolicys>
    </brasvas>
  </filter>"""

SERVICEPOLICYNAME = """
      <servicePolicyName>%s</servicePolicyName>"""

SERVICEGROUPNAME = """
      <serviceGroupName>%s</serviceGroupName>"""

SERVICEGROUPDIRECTION = """
      <serviceGroupDirection>%s</serviceGroupDirection>"""

SERVICEGROUPPRIORITY = """
      <serviceGroupPriority>%s</serviceGroupPriority>"""


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
        self.serviceGroupName = self.module.params['serviceGroupName']
        self.serviceGroupDirection = self.module.params['serviceGroupDirection']
        self.serviceGroupPriority = self.module.params['serviceGroupPriority']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.servicePolicyName is not None:
            self.proposed["servicePolicyName"] = self.servicePolicyName
        if self.serviceGroupName is not None:
            self.proposed["serviceGroupName"] = self.serviceGroupName
        if self.serviceGroupDirection is not None:
            self.proposed["serviceGroupDirection"] = self.serviceGroupDirection
        if self.serviceGroupPriority is not None:
            self.proposed["serviceGroupPriority"] = self.serviceGroupPriority
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
        cfg_str += SERVICEPOLICYS_SERVICEGROUP_CONFIG_HEAD
        if self.servicePolicyName is not None:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName

        if self.operation == 'create':
            cfg_str += SERVICEPOLICYS_SERVICEGROUP_CREATE
        if self.operation == 'merge':
            cfg_str += SERVICEPOLICYS_SERVICEGROUP_MERGE
        if self.operation == 'delete':
            cfg_str += SERVICEPOLICYS_SERVICEGROUP_DELETE

        if self.serviceGroupName is not None:
            cfg_str += SERVICEGROUPNAME % self.serviceGroupName
        if self.serviceGroupDirection is not None:
            cfg_str += SERVICEGROUPDIRECTION % self.serviceGroupDirection
        if self.serviceGroupPriority is not None:
            cfg_str += SERVICEGROUPPRIORITY % self.serviceGroupPriority

        cfg_str += SERVICEPOLICYS_SERVICEGROUP_CONFIG_END
        cfg_str += SERVICEPOLICYS_SERVICEGROUP_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += SERVICEPOLICYS_SERVICEGROUP_GET_HEAD

        if self.servicePolicyName:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName

        cfg_str += SERVICEPOLICYS_SERVICEGROUP_GET_TAIL

        if self.operation == 'get':
            if self.serviceGroupName is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.serviceGroupDirection is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')
            if self.serviceGroupPriority is not None:
                self.module.fail_json(
                    msg='Error: This operation is not supported.')

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
        container_1_attributes_Info = root.findall(
            "brasvas/servicePolicys/servicePolicy")
        attributes_Info["serviceGroups"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["servicePolicyName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "refServiceGroup")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["serviceGroupName",
                                                   "serviceGroupDirection",
                                                   "serviceGroupPriority"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["serviceGroups"].append(
                            container_2_info_Table)

        if len(attributes_Info["serviceGroups"]) == 0:
            attributes_Info.clear()
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
        serviceGroupName=dict(required=False, type='str'),
        serviceGroupDirection=dict(
            required=False, choices=[
                'inbound', 'outbound', 'both']),
        serviceGroupPriority=dict(required=False, type='int'),
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
