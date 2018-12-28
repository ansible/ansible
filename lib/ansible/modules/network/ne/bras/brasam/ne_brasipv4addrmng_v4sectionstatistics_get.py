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
module: ne_brasipv4addrmng_v4sectionstatistics_get
version_added: "2.6"
short_description: The configuration table of IP section.
description:
    - The configuration table of IP section.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    sectionIndex:
        description:
            - Index of address section.
        required: false
    poolIndex:
        description:
            - Index of ip pool.
        required: false
    poolName:
        description:
            - Name of ip pool.
        required: false
    operation:
        description:
            - Specifies the operation type.
        required: true
        choices: ['get']
'''

EXAMPLES = '''

- name: ne_brasipv4addrmng_v4sectionstatistics_get test
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

    - name: "The configuration table of IP section, the operation type is 'get'."
      ne_brasipv4addrmng_v4sectionstatistics_get:
        sectionIndex='1'
        poolIndex='1'
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
        "sectionIndex": 1,
        "poolIndex": 1,
        "poolName": "nameTest",
        "operation": "get"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "v4SectionStatistics": [
            {
                "availableNum": "1",
                "conflict": "0",
                "highIP": "123.1.1.2",
                "invalid": "0",
                "length": "1",
                "lowIP": "123.1.1.2",
                "poolIndex": "0",
                "poolName": "123",
                "reservedNum": "0",
                "sectionIndex": "1",
                "staticBindNum": "0",
                "subnetId": "0",
                "totalNum": "254",
                "usedNum": "0"
            }
        ]
    }
'''


V4SECTIONSTATISTICS_GET_HEAD = """
  <filter type="subtree">
    <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
      <v4SectionStatistics>
        <v4SectionStatistic>"""

V4SECTIONSTATISTICS_GET_TAIL = """
        </v4SectionStatistic>
      </v4SectionStatistics>
    </brasipv4addrmng>
  </filter>"""

SECTIONINDEX = """
                <sectionIndex>%s</sectionIndex>"""

POOLINDEX = """
                <poolIndex>%s</poolIndex>"""

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
        self.sectionIndex = self.module.params['sectionIndex']
        self.poolIndex = self.module.params['poolIndex']
        self.poolName = self.module.params['poolName']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        if self.sectionIndex is not None:
            self.proposed["sectionIndex"] = self.sectionIndex
        if self.poolIndex is not None:
            self.proposed["poolIndex"] = self.poolIndex
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
        if self.sectionIndex is not None:
            cfg_str += SECTIONINDEX % self.sectionIndex
        if self.poolIndex is not None:
            cfg_str += POOLINDEX % self.poolIndex
        if self.poolName is not None:
            cfg_str += POOLNAME % self.poolName
        cfg_str += V4SECTIONSTATISTICS_GET_TAIL

        xml_str = get_nc_config(self.module, cfg_str)

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace(' xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace(' xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace(
            ' xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng"', "")

        attributes_Info = dict()
        if "<data/>" in xml_str:
            return attributes_Info

        root = ElementTree.fromstring(xml_str)
        container_attributes_Info = root.findall(
            "brasipv4addrmng/v4SectionStatistics/v4SectionStatistic")
        attributes_Info["v4SectionStatistics"] = list()

        if len(container_attributes_Info) != 0:
            for container_node in container_attributes_Info:
                container_Table = dict()
                for leaf_attributes_Info in container_node:
                    if leaf_attributes_Info.tag in ["sectionIndex",
                                                    "poolIndex",
                                                    "length",
                                                    "usedNum",
                                                    "conflict",
                                                    "invalid",
                                                    "availableNum",
                                                    "lowIP",
                                                    "highIP",
                                                    "poolName",
                                                    "totalNum",
                                                    "reservedNum",
                                                    "staticBindNum",
                                                    "subnetId"]:
                        container_Table[leaf_attributes_Info.tag] = leaf_attributes_Info.text
                attributes_Info["v4SectionStatistics"].append(container_Table)

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
        sectionIndex=dict(required=False, type='int'),
        poolIndex=dict(required=False, type='int'),
        poolName=dict(required=False, type='str'),
        operation=dict(required=False, choices=['get'], default='get'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
