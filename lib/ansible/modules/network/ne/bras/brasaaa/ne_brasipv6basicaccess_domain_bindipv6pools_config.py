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
module: ne_brasipv6basicaccess_domain_bindipv6pools_config
version_added: "2.6"
short_description: Binds an IPv6 address pool to an AAA domain.
description:
    - Binds an IPv6 address pool to an AAA domain.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    domainName:
        description:
            - Specifies the name of a domain.
        required: false
    setIPv6PoolName:
        description:
            - Specifies the name of an IPv6 address pool.
        required: false
    operation:
        description:
            - Specifies the operation type.
        required: true
        choices: ['create', 'delete', 'merge', 'get']
'''

EXAMPLES = '''

- name: ne_brasipv6basicaccess_domain_bindipv6pools_config test
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

  - name: "Binds an IPv6 address pool to an AAA domain, the operation type is 'create'."
    ne_brasipv6basicaccess_domain_bindipv6pools_config:
      domainName='domainTest'
      setIPv6PoolName='poolTest'
      operation='create'
      provider: "{{ cli }}"

  - name: "Binds an IPv6 address pool to an AAA domain, the operation type is 'delete'."
    ne_brasipv6basicaccess_domain_bindipv6pools_config:
      domainName='domainTest'
      setIPv6PoolName='poolTest'
      operation='delete'
      provider: "{{ cli }}"

  - name: "Binds an IPv6 address pool to an AAA domain, the operation type is 'get'."
    ne_brasipv6basicaccess_domain_bindipv6pools_config:
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
        "setIPv6PoolName": "poolTest",
        "operation": "create",
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "bindIPv6Pools": [
            {
                "domainName": "domainTest",
                "setIPv6PoolName": "poolTest"
            }
        ]
    }
end_state:
    description: k/v pairs of object instance params after module execution
    returned: always
    type: dict
    sample: {
        "bindIPv6Pools": [
            {
                "domainName": "domainTest",
                "setIPv6PoolName": "poolTest"
            }
        ]
    }
'''


DOMAINS_BINDIPV6POOLS_CONFIG_HEAD = """
    <config>
      <brasipv6basicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6basicaccess">
        <domains>
          <domain>
"""

DOMAINS_BINDIPV6POOLS_CONFIG_TAIL = """
          </domain>
        </domains>
      </brasipv6basicaccess>
    </config>
"""

BINDIPV6POOLS_START = """
            <bindIPv6Pools>"""

BINDIPV6POOL_START = """
              <bindIPv6Pool>"""

DOMAINS_BINDIPV6POOLS_CREATE = """
              <bindIPv6Pool nc:operation="create" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DOMAINS_BINDIPV6POOLS_DELETE = """
              <bindIPv6Pool nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

DOMAINS_BINDIPV6POOLS_MERGE = """
              <bindIPv6Pool nc:operation="merge" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">"""

BINDIPV6POOL_END = """
              </bindIPv6Pool>"""

BINDIPV6POOLS_END = """
            </bindIPv6Pools>"""

DOMAINS_BINDIPV6POOLS_GET_HEAD = """
  <filter type="subtree">
    <brasipv6basicaccess xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6basicaccess">
      <domains>
        <domain>"""

DOMAINS_BINDIPV6POOLS_GET_TAIL = """
        </domain>
      </domains>
    </brasipv6basicaccess>
  </filter>"""

DOMAINNAME = """
                <domainName>%s</domainName>"""

SETIPV6POOLNAME = """
                <setIPv6PoolName>%s</setIPv6PoolName>"""


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
        self.setIPv6PoolName = self.module.params['setIPv6PoolName']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.domainName is not None:
            self.proposed["domainName"] = self.domainName
        if self.setIPv6PoolName is not None:
            self.proposed["setIPv6PoolName"] = self.setIPv6PoolName
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
        cfg_str += DOMAINS_BINDIPV6POOLS_CONFIG_HEAD
        if self.domainName is not None:
            cfg_str += DOMAINNAME % self.domainName

        cfg_str += BINDIPV6POOLS_START
        if self.operation == 'create':
            cfg_str += DOMAINS_BINDIPV6POOLS_CREATE
        if self.operation == 'merge':
            cfg_str += DOMAINS_BINDIPV6POOLS_MERGE
        if self.operation == 'delete':
            cfg_str += DOMAINS_BINDIPV6POOLS_DELETE

        if self.setIPv6PoolName is not None:
            cfg_str += SETIPV6POOLNAME % self.setIPv6PoolName

        cfg_str += BINDIPV6POOL_END
        cfg_str += BINDIPV6POOLS_END
        cfg_str += DOMAINS_BINDIPV6POOLS_CONFIG_TAIL

        logging.debug(cfg_str)
        set_nc_config(self.module, cfg_str)

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += DOMAINS_BINDIPV6POOLS_GET_HEAD

        if self.domainName is not None:
            cfg_str += DOMAINNAME % self.domainName
        cfg_str += BINDIPV6POOLS_START
        cfg_str += BINDIPV6POOL_START
        if self.setIPv6PoolName is not None:
            cfg_str += SETIPV6POOLNAME % self.setIPv6PoolName
        cfg_str += BINDIPV6POOL_END
        cfg_str += BINDIPV6POOLS_END

        cfg_str += DOMAINS_BINDIPV6POOLS_GET_TAIL

        xml_str = get_nc_config(self.module, cfg_str)

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6basicaccess"', "")

        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        root = ElementTree.fromstring(xml_str)
        container_1_attributes_Info = root.findall(
            "brasipv6basicaccess/domains/domain")
        attributes_Info["bindIPv6Pools"] = list()

        if len(container_1_attributes_Info) != 0:
            for container_1_node in container_1_attributes_Info:
                container_info_Table = dict()
                for leaf_1_Info in container_1_node:
                    if leaf_1_Info.tag in ["domainName"]:
                        container_info_Table[leaf_1_Info.tag] = leaf_1_Info.text

                container_2_attributes_Info = container_1_node.findall(
                    "bindIPv6Pools/bindIPv6Pool")
                if len(container_2_attributes_Info) != 0:
                    for container_2_node in container_2_attributes_Info:
                        container_2_info_Table = copy.deepcopy(
                            container_info_Table)
                        for leaf_2_Info in container_2_node:
                            if leaf_2_Info.tag in ["setIPv6PoolName"]:
                                container_2_info_Table[leaf_2_Info.tag] = leaf_2_Info.text
                        attributes_Info["bindIPv6Pools"].append(
                            container_2_info_Table)

        if len(attributes_Info["bindIPv6Pools"]) == 0:
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
        setIPv6PoolName=dict(required=False, type='str'),
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
