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
module: ne_brasipv6addrmng_v6poolstatusstatistic_get
version_added: "2.6"
short_description: The configuration table of IPv6 address pool's usage.
description:
    - The configuration table of IPv6 address pool's usage.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    poolName:
        description:
            - The name of ipv6 pool.
        required: false
    operation:
        description:
            - Specifies the operation type.
        required: true
        choices: ['get']
'''

EXAMPLES = '''

- name: ne_brasipv6addrmng_v6poolstatusstatistic_get test
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

    - name: "The configuration table of IPv6 address pool's usage, the operation type is 'get'."
      ne_brasipv6addrmng_v6poolstatusstatistic_get:
        poolName='nameTest'
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
        "poolName": "nameTest",
        "operation": "get"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "v6PoolStatusStatistics": [
            {
                "freeAddress": "0",
                "freePrefix": "0",
                "ip6AddrConflict": "0",
                "ip6AddrExclude": "0",
                "ip6AddrFree": "0",
                "ip6AddrTotal": "0",
                "ip6AddrUsed": "0",
                "ip6AddrUsedPerc": "0",
                "ndraPrefConflic": "0",
                "ndraPrefExclude": "0",
                "ndraPrefFree": "0",
                "ndraPrefTotal": "0",
                "ndraPrefUsed": "0",
                "ndraPrefUsedPrc": "0",
                "pdPrefConflict": "0",
                "pdPrefExclude": "0",
                "pdPrefFree": "0",
                "pdPrefTotal": "0",
                "pdPrefUsed": "0",
                "pdPrefUsedPrcnt": "0",
                "poolIndex": "1",
                "poolName": "cbb1",
                "usedAddress": "0",
                "usedPrefix": "0"
            }
        ]
    }
'''


V4SECTIONSTATISTICS_GET_HEAD = """
  <filter type="subtree">
    <brasipv6addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng">
      <v6PoolStatusStatistics>
        <v6PoolStatusStatistic>"""

V4SECTIONSTATISTICS_GET_TAIL = """
        </v6PoolStatusStatistic>
      </v6PoolStatusStatistics>
    </brasipv6addrmng>
  </filter>"""

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
        self.poolName = self.module.params['poolName']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.poolName is not None:
            self.proposed["poolName"] = self.poolName
        if self.operation is not None:
            self.proposed["operation"] = self.operation

        # result state
        self.changed = False
        self.results = dict()
        self.existing = dict()
        self.end_state = dict()

    def get_info_process(self):
        """get one attributes dict."""
        cfg_str = ''
        cfg_str += V4SECTIONSTATISTICS_GET_HEAD
        if self.poolName is not None:
            cfg_str += POOLNAME % self.poolName
        cfg_str += V4SECTIONSTATISTICS_GET_TAIL

        xml_str = get_nc_config(self.module, cfg_str)

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv6addrmng"', "")

        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        root = ElementTree.fromstring(xml_str)
        container_attributes_Info = root.findall(
            "brasipv6addrmng/v6PoolStatusStatistics/v6PoolStatusStatistic")
        attributes_Info["v6PoolStatusStatistics"] = list()

        if len(container_attributes_Info) != 0:
            for container_node in container_attributes_Info:
                container_Table = dict()
                for leaf_attributes_Info in container_node:
                    if leaf_attributes_Info.tag in ["poolName",
                                                    "freeAddress",
                                                    "usedAddress",
                                                    "freePrefix",
                                                    "usedPrefix",
                                                    "ip6AddrTotal",
                                                    "ip6AddrUsed",
                                                    "ip6AddrFree",
                                                    "ip6AddrConflict",
                                                    "ip6AddrExclude",
                                                    "ip6AddrUsedPerc",
                                                    "ndraPrefTotal",
                                                    "ndraPrefUsed",
                                                    "ndraPrefFree",
                                                    "ndraPrefConflic",
                                                    "ndraPrefExclude",
                                                    "ndraPrefUsedPrc",
                                                    "pdPrefTotal",
                                                    "pdPrefUsed",
                                                    "pdPrefFree",
                                                    "pdPrefConflict",
                                                    "pdPrefExclude",
                                                    "pdPrefUsedPrcnt",
                                                    "poolIndex"]:
                        container_Table[leaf_attributes_Info.tag] = leaf_attributes_Info.text
                attributes_Info["v6PoolStatusStatistics"].append(
                    container_Table)

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
        poolName=dict(required=False, type='str'),
        operation=dict(required=False, choices=['get'], default='get'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
