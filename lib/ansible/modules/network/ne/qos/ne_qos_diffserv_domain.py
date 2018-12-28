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
module: ne_qos_diffserv_domain
version_added: "2.6"
short_description: Manages the diffServ domain on Huawei NetEngine devices.
description:
    - Manages the diffServ domain. on Huawei NetEngine devices.
options:
    dsName:
        description:
            - Name of a DiffServ domain.
              The value is a string of 1 to 48 characters.
        required: true
        default: null
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_diffserv_domain module test
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

  - name: Config DiffServ domain
    ne_qos_diffserv_domain:
      dsName: test
      operation: create
      provider: "{{ cli }}"

  - name: Undo DiffServ domain
    ne_behavior_policy:
      dsName: test
      operation: delete
      provider: "{{ cli }}"

  - name: Get DiffServ domain test configuration
    ne_behavior_policy:
      behaviorName: test
      operation: getconfig
      provider: "{{ cli }}"

  - name: Get all DiffServ domain configurations
    ne_behavior_policy:
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "dsName": "test",
        "operation": "getconfig"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "dsId": "7",
            "dsName": "test"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  [
        {
            "dsId": "7",
            "dsName": "test"
        }
    ],
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: false
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosDss>
        <qosDs>
            <dsName>%s</dsName>
"""

MERGE_CLASS_TAIL = """
        </qosDs>
    </qosDss>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosDss>
        <qosDs>
            <dsName></dsName>
            <dsId></dsId>
        </qosDs>
    </qosDss>
</qos>
</filter>
"""


class QosDsCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.dsName = self.module.params['dsName']
        self.dsId = self.module.params['dsId']
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
        if not self.dsName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes dsName.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % (self.dsName)
        if self.dsId:
            conf_str = constr_leaf_value(conf_str, 'dsId', self.dsId)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qosDs>', '<qosDs xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_ds(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_ds(self):
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
            xml_str_split = re.split('</qosDs>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                attr = dict()
                find_dsName = re.findall(
                    r'.*<dsName>(.*)</dsName>.*\s*', xml_str_split[j])
                find_dsId = re.findall(
                    r'.*<dsId>(.*)</dsId>.*\s*', xml_str_split[j])

                if find_dsName and (
                        find_dsName[0] == self.dsName or not self.dsName or self.operation != "getconfig"):
                    attr['dsName'] = find_dsName[0]
                    attr['dsId'] = find_dsId[0]
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_ds(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.dsName:
            self.proposed["dsName"] = self.dsName
        if self.dsId:
            self.proposed["dsId"] = self.dsId
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        dscfg_attr_exist = self.get_ds()
        if dscfg_attr_exist:
            self.results["existing"] = dscfg_attr_exist

        if self.operation == 'create':
            self.merge_ds()

        if self.operation == 'delete':
            self.undo_ds()

        dscfg_attr_end_state = self.get_ds()
        if dscfg_attr_end_state:
            self.results["end_state"] = dscfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        dsName=dict(required=False, type='str'),
        dsId=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosDsCfg = QosDsCfg(argument_spec)
    NEWQosDsCfg.work()


if __name__ == '__main__':
    main()
