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
module: ne_brasvas_servicepolicy_radiusservergroup_config
version_added: "2.6"
short_description: Sets the RADIUS server group for service policy.The server group must be a configured server group.
description:
    - Sets the RADIUS server group for service policy.The server group must be a configured server group.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    servicePolicyName:
        description:
            - Specifies the name of a value-added service policy.
        required: false
    radiusServerGroupName:
        description:
            - Specifies the name of radius server group.
        required: false
    operation:
        description:
            - Specifies the operation type.
              if the operation is get,the radiusServerGroupName cannot take parameters,
              otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_brasvas_servicepolicy_radiusservergroup_config test
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

    - name: "Sets the RADIUS server group for service policy.The server group must be a configured server group, the operation type is 'create'."
      ne_brasvas_servicepolicy_radiusservergroup_config:
        servicePolicyName='nameTest1'
        radiusServerGroupName='nameTest2'
        operation='create'
        provider: "{{ cli }}"

    - name: "Sets the RADIUS server group for service policy.The server group must be a configured server group, the operation type is 'delete'."
      ne_brasvas_servicepolicy_radiusservergroup_config:
        servicePolicyName='nameTest1'
        radiusServerGroupName='nameTest2'
        operation='delete'
        provider: "{{ cli }}"

    - name: "Sets the RADIUS server group for service policy.The server group must be a configured server group, the operation type is 'get'."
      ne_brasvas_servicepolicy_radiusservergroup_config:
        servicePolicyName='nameTest1'
        radiusServerGroupName='nameTest2'
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
        "radiusServerGroupName": "nameTest2",
        "operation": "create"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "radiusservergroups": [
            {
                "servicePolicyName": "nameTest1",
                "radiusServerGroupName": "nameTest2"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "radiusservergroups": [
            {
                "servicePolicyName": "nameTest1",
                "radiusServerGroupName": "nameTest2"
            }
        ]
    }
'''


SERVICEPOLICYS_RADIUSSERVERGROUP_CONFIG_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <servicePolicys>
          <servicePolicy>
"""

SERVICEPOLICYS_RADIUSSERVERGROUP_CONFIG_TAIL = """
          </servicePolicy>
        </servicePolicys>
      </brasvas>
    </config>
"""

SERVICEPOLICYS_RADIUSSERVERGROUP_CREATE = """
          <refServiceRadiusServerGroup nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICYS_RADIUSSERVERGROUP_DELETE = """
          <refServiceRadiusServerGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICYS_RADIUSSERVERGROUP_MERGE = """
          <refServiceRadiusServerGroup nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

SERVICEPOLICYS_RADIUSSERVERGROUP_CONFIG_END = """
          </refServiceRadiusServerGroup>"""

SERVICEPOLICYS_RADIUSSERVERGROUP_GET_HEAD = """
  <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <servicePolicys>
        <servicePolicy>"""

SERVICEPOLICYS_RADIUSSERVERGROUP_GET_TAIL = """
          <refServiceRadiusServerGroup/>
        </servicePolicy>
      </servicePolicys>
    </brasvas>
  </filter>"""

SERVICEPOLICYNAME = """
      <servicePolicyName>%s</servicePolicyName>"""

RADIUSSERVERGROUPNAME = """
      <radiusServerGroupName>%s</radiusServerGroupName>"""


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
        self.radiusServerGroupName = self.module.params['radiusServerGroupName']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.servicePolicyName is not None:
            self.proposed["servicePolicyName"] = self.servicePolicyName
        if self.radiusServerGroupName is not None:
            self.proposed["radiusServerGroupName"] = self.radiusServerGroupName
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
        cfg_str += SERVICEPOLICYS_RADIUSSERVERGROUP_CONFIG_HEAD
        if self.servicePolicyName is not None:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName

        if self.operation == 'create':
            cfg_str += SERVICEPOLICYS_RADIUSSERVERGROUP_CREATE
        if self.operation == 'merge':
            cfg_str += SERVICEPOLICYS_RADIUSSERVERGROUP_MERGE
        if self.operation == 'delete':
            cfg_str += SERVICEPOLICYS_RADIUSSERVERGROUP_DELETE

        if self.radiusServerGroupName is not None:
            cfg_str += RADIUSSERVERGROUPNAME % self.radiusServerGroupName

        cfg_str += SERVICEPOLICYS_RADIUSSERVERGROUP_CONFIG_END
        cfg_str += SERVICEPOLICYS_RADIUSSERVERGROUP_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += SERVICEPOLICYS_RADIUSSERVERGROUP_GET_HEAD

        if self.servicePolicyName is not None:
            cfg_str += SERVICEPOLICYNAME % self.servicePolicyName

        cfg_str += SERVICEPOLICYS_RADIUSSERVERGROUP_GET_TAIL

        if self.operation == 'get':
            if self.radiusServerGroupName is not None:
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
        attributes_Info["radiusservergroups"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["servicePolicyName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "refServiceRadiusServerGroup")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["radiusServerGroupName"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["radiusservergroups"].append(
                            container_2_info_Table)

        if len(attributes_Info["radiusservergroups"]) == 0:
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
        radiusServerGroupName=dict(required=False, type='str'),
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
