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
module: ne_brasipv4addrmng_v4poolstatistics_get
version_added: "2.6"
short_description: The Statistics of ip pool.
description:
    - The Statistics of ip pool.
author:
    - liushuai (@CloudEngine-Ansible)
options:
    operation:
        description:
            - Specifies the operation type.
        required: true
        choices: ['get']
'''

EXAMPLES = '''

- name: ne_brasipv4addrmng_v4poolstatistics_get test
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

    - name: "The Statistics of ip pool, the operation type is 'get'."
      ne_brasipv4addrmng_v4poolstatistics_get:
        operation='get'
        provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: false
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "operation": "get"
    }
existing:
    description: k/v pairs of existing object instance
    returned: always
    type: dict
    sample: {
        "v4PoolStatistics": [
            {
                "conflictNum": "0",
                "excludeNum": "0",
                "idleTotalNum": "206610",
                "poolNum": "23",
                "totaoNum": "206612",
                "usedPercent": "0",
                "usedTotalNum": "1"
            }
        ]
    }
'''


V4POOLSTATISTICS_GET_HEAD = """
  <filter type="subtree">
    <brasipv4addrmng xmlns="http://www.huawei.com/netconf/vrp/huawei-brasipv4addrmng">
      <v4PoolStatistics>
        <v4PoolStatistic>"""

V4POOLSTATISTICS_GET_TAIL = """
        </v4PoolStatistic>
      </v4PoolStatistics>
    </brasipv4addrmng>
  </filter>"""


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
        self.operation = self.module.params['operation']

        self.proposed = dict()
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
        cfg_str += V4POOLSTATISTICS_GET_HEAD
        cfg_str += V4POOLSTATISTICS_GET_TAIL

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
            "brasipv4addrmng/v4PoolStatistics/v4PoolStatistic")
        attributes_Info["v4PoolStatistics"] = list()

        if len(container_attributes_Info) != 0:
            for container_node in container_attributes_Info:
                container_Table = dict()
                for leaf_attributes_Info in container_node:
                    if leaf_attributes_Info.tag in ["poolNum",
                                                    "idleTotalNum",
                                                    "usedTotalNum",
                                                    "conflictNum",
                                                    "excludeNum",
                                                    "totaoNum",
                                                    "usedPercent"]:
                        container_Table[leaf_attributes_Info.tag] = leaf_attributes_Info.text
                attributes_Info["v4PoolStatistics"].append(container_Table)

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
        operation=dict(required=False, choices=['get'], default='get'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
