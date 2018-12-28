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
module: ne_qos_qosprofile
version_added: "2.6"
short_description: You can configure scheduling parameters, including the CIR, PIR, FQ profile, CAR, and Layer 2 suppression parameters, for queues in a \
QoS profile.
description:
    - You can configure scheduling parameters, including the CIR, PIR, FQ profile, CAR, and Layer 2 suppression parameters, for queues in a QoS profile.
    profileName:
        description:
            - Name of a QoS profile.
              The value is a string of characters.
        required: true
        default: null
    timeRange:
        description:
            - A time range is configured for a QoS profile.
        required: false
        default: notpriority
        choices: ['nottimerange', 'istimerange', 'is4cos']
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_qosprofile module test
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

  - name: Config qos-profile template
    ne_qos_qosprofile:
      flowQtimeRangeueueName: test
      timeRange: nottimerange
      operation: create
      provider: "{{ cli }}"

  - name: Undo qos-profile template
    ne_qos_qosprofile:
      timeRange: test
      operation: delete
      provider: "{{ cli }}"

  - name: Get qos-profile template test configuration
    ne_qos_qosprofile:
      timeRange: test
      operation: getconfig
      provider: "{{ cli }}"

  - name: Get all qos-profile template configurations
    ne_qos_qosprofile:
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "profileName": "test2",
        "operation": "create"
        "timeRange": "nottimerange",
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "profileName": "test1",
            "timeRange": "nottimerange",
        }
        {
            "profileName": "test2",
            "timeRange": "nottimerange",
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  [
        {
            "profileName": "test1",
            "timeRange": "nottimerange",
        }
        {
            "profileName": "test2",
            "timeRange": "nottimerange",
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
        <hqosProfiles>
            <hqosProfile>
                <profileName>%s</profileName>
"""

MERGE_CLASS_TAIL = """
            </hqosProfile>
        </hqosProfiles>
    </hqos>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <hqos>
        <hqosProfiles>
            <hqosProfile/>
        </hqosProfiles>
    </hqos>
</qos>
</filter>
"""


class QosProfileCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosfq config info
        self.profileName = self.module.params['profileName']
        self.timeRange = self.module.params['timeRange']
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
        if not self.profileName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes profileName.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % (self.profileName)
        if self.timeRange:
            conf_str = constr_leaf_value(conf_str, 'timeRange', self.timeRange)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<hqosProfile>', '<hqosProfile xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_qosprof(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_qosprof(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return None
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</hqosProfile>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                attr = dict()
                find_profileName = re.findall(
                    r'.*<profileName>(.*)</profileName>.*\s*', xml_str_split[j])
                find_timeRange = re.findall(
                    r'.*<timeRange>(.*)</timeRange>.*\s*', xml_str_split[j])

                if find_profileName and (
                        find_profileName[0] == self.profileName or not self.profileName or self.operation != "getconfig"):
                    attr['profileName'] = find_profileName[0]
                    if find_timeRange:
                        attr['timeRange'] = find_timeRange[0]
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_qosprof(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_qosprof")
        # self.changed = True

    def get_proposed(self):

        if self.profileName:
            self.proposed["profileName"] = self.profileName
        if self.timeRange:
            self.proposed["timeRange"] = self.timeRange
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        Profilecfg_attr_exist = self.get_qosprof()
        if Profilecfg_attr_exist:
            self.results["existing"] = Profilecfg_attr_exist

        if self.operation == 'create':
            self.merge_qosprof()

        if self.operation == 'delete':
            self.undo_qosprof()

        Profilecfg_attr_end_state = self.get_qosprof()
        if Profilecfg_attr_end_state:
            self.results["end_state"] = Profilecfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        profileName=dict(required=False, type='str'),
        timeRange=dict(
            required=False,
            choices=[
                'nottimerange',
                'istimerange']),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosProfileCfg = QosProfileCfg(argument_spec)
    NEWQosProfileCfg.work()


if __name__ == '__main__':
    main()
