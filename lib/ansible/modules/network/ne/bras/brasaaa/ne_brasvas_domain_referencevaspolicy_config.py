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
module: ne_brasvas_domain_referencevaspolicy_config
version_added: "2.6"
short_description: Configures the value-added service policy used by the domain.
description:
    - Configures the value-added service policy used by the domain.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    domainName:
        description:
            - Specifies the name of a domain.
        required: false
    vasPolicyName:
        description:
            - Specifies the name of the service policy used by the domain.
              The policy must be a configured service policy.
        required: false
    operation:
        description:
            - Specifies the operation type.
              if the operation is get,the vasPolicyName cannot take parameters,
              otherwise The echo of the command line is'This operation are not supported'.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_brasvas_domain_referencevaspolicy_config test
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

    - name: "Configures the value-added service policy used by the domain, the operation type is 'create'."
      ne_brasvas_domain_referencevaspolicy_config:
        domainName='nameTest1'
        vasPolicyName='nameTest2'
        operation='create'
        provider: "{{ cli }}"

    - name: "Configures the value-added service policy used by the domain, the operation type is 'delete'."
      ne_brasvas_domain_referencevaspolicy_config:
        domainName='nameTest1'
        vasPolicyName='nameTest2'
        operation='delete'
        provider: "{{ cli }}"

    - name: "Configures the value-added service policy used by the domain, the operation type is 'get'."
      ne_brasvas_domain_referencevaspolicy_config:
        domainName='nameTest1'
        vasPolicyName='nameTest2'
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
        "domainName": "nameTest1",
        "vasPolicyName": "nameTest2",
        "operation": "create"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "referenceVasPolicys": [
            {
                "domainName": "nameTest1",
                "vasPolicyName": "nameTest2"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "referenceVasPolicys": [
            {
                "domainName": "nameTest1",
                "vasPolicyName": "nameTest2"
            }
        ]
    }
'''


DOMAINS_REFERENCEVASPOLICY_CONFIG_HEAD = """
    <config>
      <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
        <domains>
          <domain>
"""

DOMAINS_REFERENCEVASPOLICY_CONFIG_TAIL = """
          </domain>
        </domains>
      </brasvas>
    </config>
"""

REFERENCEVASPOLICY_START = """
              <referenceVasPolicy>"""

DOMAINS_REFERENCEVASPOLICY_CREATE = """
              <referenceVasPolicy nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DOMAINS_REFERENCEVASPOLICY_DELETE = """
              <referenceVasPolicy nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DOMAINS_REFERENCEVASPOLICY_MERGE = """
              <referenceVasPolicy nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

REFERENCEVASPOLICY_END = """
              </referenceVasPolicy>"""

DOMAINS_REFERENCEVASPOLICY_GET_HEAD = """
  <filter type="subtree">
    <brasvas xmlns="http://www.huawei.com/netconf/vrp/huawei-brasvas">
      <domains>
        <domain>"""

DOMAINS_REFERENCEVASPOLICY_GET_TAIL = """
        </domain>
      </domains>
    </brasvas>
  </filter>"""

DOMAINNAME = """
                <domainName>%s</domainName>"""

VASPOLICYNAME = """
                <vasPolicyName>%s</vasPolicyName>"""


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
        self.domainName = self.module.params['domainName']
        self.vasPolicyName = self.module.params['vasPolicyName']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.vasPolicyName is not None:
            self.proposed["vasPolicyName"] = self.vasPolicyName
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
        cfg_str += DOMAINS_REFERENCEVASPOLICY_CONFIG_HEAD
        if self.domainName is not None:
            cfg_str += DOMAINNAME % self.domainName

        if self.operation == 'create':
            cfg_str += DOMAINS_REFERENCEVASPOLICY_CREATE
        if self.operation == 'merge':
            cfg_str += DOMAINS_REFERENCEVASPOLICY_MERGE
        if self.operation == 'delete':
            cfg_str += DOMAINS_REFERENCEVASPOLICY_DELETE

        if self.vasPolicyName is not None:
            cfg_str += VASPOLICYNAME % self.vasPolicyName

        cfg_str += REFERENCEVASPOLICY_END
        cfg_str += DOMAINS_REFERENCEVASPOLICY_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += DOMAINS_REFERENCEVASPOLICY_GET_HEAD

        if self.domainName is not None:
            cfg_str += DOMAINNAME % self.domainName
        cfg_str += REFERENCEVASPOLICY_START
        if self.vasPolicyName is not None:
            cfg_str += VASPOLICYNAME % self.vasPolicyName
        cfg_str += REFERENCEVASPOLICY_END

        cfg_str += DOMAINS_REFERENCEVASPOLICY_GET_TAIL

        if self.operation == 'get':
            if self.vasPolicyName is not None:
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
        container_1_attributes_Info = root.findall("brasvas/domains/domain")
        attributes_Info["referenceVasPolicys"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["domainName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "referenceVasPolicy")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["vasPolicyName"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["referenceVasPolicys"].append(
                            container_2_info_Table)

        if len(attributes_Info["referenceVasPolicys"]) == 0:
            attributes_Info.clear()
        return attributes_Info

    def run(self):
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
        domainName=dict(required=False, type='str'),
        vasPolicyName=dict(required=False, type='str'),
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
