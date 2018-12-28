#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec, constr_leaf_value
from ansible.module_utils.basic import AnsibleModule
import collections
import re
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ne_qos_flowqueue
version_added: "2.6"
short_description: HQoS enables the router to perform user-specific queue scheduling.
description:
    - HQoS enables the router to perform user-specific queue scheduling.
    flowQueueName:
        description:
            - Name of a service flow queue.
              The value is a string of characters.
        required: true
        default: null
    prioritymodefq:
        description:
            - Operation type.
        required: true
        default: notpriority
        choices: ['notpriority', 'ispriority', 'is4cos']
    operation:
        description:
            - Operation type.
        required: true
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_flowqueue module test
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

  - name: Config flow-queue template
    ne_qos_flowqueue:
      flowQueueName: test
      prioritymodefq: notpriority
      operation: create
      provider: "{{ cli }}"

  - name: Undo flow-queue template
    ne_qos_flowqueue:
      flowQueueName: test
      operation: delete
      provider: "{{ cli }}"

  - name: Get flow-queue template test configuration
    ne_qos_flowqueue:
      flowQueueName: test
      operation: getconfig
      provider: "{{ cli }}"

  - name: Get all flow-queue template configurations
    ne_qos_flowqueue:
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "flowQueueName": "test2",
        "operation": "create"
        "prioritymodefq": "notpriority",
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "flowQueueName": "test1",
            "prioritymodefq": "notpriority",
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  [
        {
            "flowQueueName": "test1",
            "prioritymodefq": "notpriority",
        }
        {
            "flowQueueName": "test2",
            "prioritymodefq": "notpriority",
        }
    ],
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <hqos>
        <hqosFlowQueues>
            <hqosFlowQueue>
                <flowQueueName>%s</flowQueueName>
"""

MERGE_CLASS_TAIL = """
            </hqosFlowQueue>
        </hqosFlowQueues>
    </hqos>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <hqos>
        <hqosFlowQueues>
            <hqosFlowQueue/>
        </hqosFlowQueues>
    </hqos>
</qos>
</filter>
"""


class QosfqCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosfq config info
        self.flowQueueName = self.module.params['flowQueueName']
        self.prioritymodefq = self.module.params['prioritymodefq']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        self.results = dict()
        self.results["existing"] = []
        self.results["end_state"] = []
        self.results["changed"] = False

    def init_module(self):
        """
        init ansilbe NetworkModule.
        """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        if not self.flowQueueName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes flowQueueName.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % (self.flowQueueName)
        if self.prioritymodefq:
            conf_str = constr_leaf_value(
                conf_str, 'prioritymodefq', self.prioritymodefq)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<hqosFlowQueue>',
                '<hqosFlowQueue xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_fq(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_fq(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return attr
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</hqosFlowQueue>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                attr = dict()
                find_flowQueueName = re.findall(
                    r'.*<flowQueueName>(.*)</flowQueueName>.*\s*', xml_str_split[j])
                find_prioritymodefq = re.findall(
                    r'.*<prioritymodefq>(.*)</prioritymodefq>.*\s*', xml_str_split[j])

                if find_flowQueueName and (
                        find_flowQueueName[0] == self.flowQueueName or not self.flowQueueName or self.operation != "getconfig"):
                    attr['flowQueueName'] = find_flowQueueName[0]
                    if find_prioritymodefq:
                        attr['prioritymodefq'] = find_prioritymodefq[0]
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_fq(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_fq")
        # self.changed = True

    def get_proposed(self):

        if self.flowQueueName:
            self.proposed["flowQueueName"] = self.flowQueueName
        if self.prioritymodefq:
            self.proposed["prioritymodefq"] = self.prioritymodefq
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        fqcfg_attr_exist = self.get_fq()
        if fqcfg_attr_exist:
            self.results["existing"] = fqcfg_attr_exist

        if self.operation == 'create':
            self.merge_fq()

        if self.operation == 'delete':
            self.undo_fq()

        fqcfg_attr_end_state = self.get_fq()
        if fqcfg_attr_end_state:
            self.results["end_state"] = fqcfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        flowQueueName=dict(required=False, type='str'),
        prioritymodefq=dict(
            required=False,
            choices=[
                'notpriority',
                'ispriority',
                'is4cos']),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosfqCfg = QosfqCfg(argument_spec)
    NEWQosfqCfg.work()


if __name__ == '__main__':
    main()
