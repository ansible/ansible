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
module: ne_brasbasicaccess_domain_bindippools_config
version_added: "2.6"
short_description: Configures the address pool used by the domain.You can configure up to 1024 address pools for each domain.
description:
    - Configures the address pool used by the domain.You can configure up to 1024 address pools for each domain.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    domainName:
        description:
            - Specifies the name of a domain.
        required: false
    poolName:
        description:
            - Specifies the name of the address pool.
        required: false
    operation:
        description:
            - Specifies the operation type.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_brasbasicaccess_domain_bindippools_config test
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

  - name: "Configures the address pool used by the domain, the operation type is 'create'."
    ne_brasbasicaccess_domain_bindippools_config:
      domainName='domainTest'
      poolName='poolTest'
      operation='create'
      provider: "{{ cli }}"

  - name: "Configures the address pool used by the domain, the operation type is 'delete'."
    ne_brasbasicaccess_domain_bindippools_config:
      domainName='domainTest'
      poolName='poolTest'
      operation='delete'
      provider: "{{ cli }}"

  - name: "Configures the address pool used by the domain, the operation type is 'get'."
    ne_brasbasicaccess_domain_bindippools_config:
      domainName='domainTest'
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
        "domainName": "domainTest",
        "poolName": "poolTest",
        "operation": "create",
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "bindIPPools": [
            {
                "domainName": "domainTest",
                "poolName": "poolTest"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "bindIPPools": [
            {
                "domainName": "domainTest",
                "poolName": "poolTest"
            }
        ]
    }
'''


DOMAINS_BINDIPPOOLS_CONFIG_HEAD = """
    <config>
      <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
        <domains>
          <domain>
"""

DOMAINS_BINDIPPOOLS_CONFIG_TAIL = """
          </domain>
        </domains>
      </brasbasicaccess>
    </config>
"""

BINDIPPOOLS_START = """
            <bindIPPools>"""

BINDIPPOOL_START = """
              <bindIPPool>"""

DOMAINS_BINDIPPOOLS_CREATE = """
              <bindIPPool nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DOMAINS_BINDIPPOOLS_DELETE = """
              <bindIPPool nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DOMAINS_BINDIPPOOLS_MERGE = """
              <bindIPPool nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

BINDIPPOOL_END = """
              </bindIPPool>"""

BINDIPPOOLS_END = """
            </bindIPPools>"""

DOMAINS_BINDIPPOOLS_GET_HEAD = """
  <filter type="subtree">
    <brasbasicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess">
      <domains>
        <domain>"""

DOMAINS_BINDIPPOOLS_GET_TAIL = """
        </domain>
      </domains>
    </brasbasicaccess>
  </filter>"""

DOMAINNAME = """
                <domainName>%s</domainName>"""

POOLNAME = """
                <poolName>%s</poolName>"""


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
        self.poolName = self.module.params['poolName']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.poolName is not None:
            self.proposed["poolName"] = self.poolName
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
        cfg_str += DOMAINS_BINDIPPOOLS_CONFIG_HEAD
        if self.domainName is not None:
            cfg_str += DOMAINNAME % self.domainName

        cfg_str += BINDIPPOOLS_START
        if self.operation == 'create':
            cfg_str += DOMAINS_BINDIPPOOLS_CREATE
        if self.operation == 'merge':
            cfg_str += DOMAINS_BINDIPPOOLS_MERGE
        if self.operation == 'delete':
            cfg_str += DOMAINS_BINDIPPOOLS_DELETE

        if self.poolName is not None:
            cfg_str += POOLNAME % self.poolName

        cfg_str += BINDIPPOOL_END
        cfg_str += BINDIPPOOLS_END
        cfg_str += DOMAINS_BINDIPPOOLS_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += DOMAINS_BINDIPPOOLS_GET_HEAD

        if self.domainName is not None:
            cfg_str += DOMAINNAME % self.domainName
        cfg_str += BINDIPPOOLS_START
        cfg_str += BINDIPPOOL_START
        if self.poolName is not None:
            cfg_str += POOLNAME % self.poolName
        cfg_str += BINDIPPOOL_END
        cfg_str += BINDIPPOOLS_END

        cfg_str += DOMAINS_BINDIPPOOLS_GET_TAIL

        xml_str = get_nc_config(self.module, cfg_str)

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasbasicaccess"', "")

        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasbasicaccess/domains/domain")
        attributes_Info["bindIPPools"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["domainName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "bindIPPools/bindIPPool")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["poolName"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["bindIPPools"].append(
                            container_2_info_Table)

        if len(attributes_Info["bindIPPools"]) == 0:
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
        domainName=dict(required=False, type='str'),
        poolName=dict(required=False, type='str'),
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
