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
module: ne_qos_domain_profile
version_added: "2.6"
short_description:  qOSProAppDomCfgNode
description:
    - qOSProAppDomCfgNode
options:
    domainName:
        description:
            - domainName.
            The value is a string of 1 to 64 characters.
        required: true
        default: null
    profileName:
        description:
            - profileName
            The value is a string of 1 to 63 characters.
        required: true
        default: null
    direction:
        description:
            - direction
        required: true
        default: null
        choices=['inbound', 'outbound']
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: NetEngine ne_qos_domain_profile module test
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


  - name: Config Domain Qos-Profile operation.
    ne_qos_domain_profile:
      domainName: test
      profileName: q1
      direction: outbound
      operation: create
      provider: "{{ cli }}"

  - name: Undo Domain Qos-Profile operation.
    ne_qos_domain_profile:
      domainName: test
      profileName: q1
      direction: outbound
      provider: "{{ cli }}"

  - name: Get Domain Qos-Profile configuration.
    ne_qos_domain_profile:
      domainName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "domainName": "test",
        "operation": "getconfig"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "direction": "inbound",
            "domainName": "test",
            "profileName": "q1"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample:  [
        {
            "direction": "inbound",
            "domainName": "test",
            "profileName": "q1"
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
<brasqos xmlns="http://www.huawei.com/netconf/vrp/huawei-brasqos">
    <brDomainNodes>
        <brDomainNode>
            <domainName>%s</domainName>
            <qOSProAppDomCfgNodes>
                <qOSProAppDomCfgNode>
"""

MERGE_CLASS_TAIL = """
                </qOSProAppDomCfgNode>
            </qOSProAppDomCfgNodes>
        </brDomainNode>
    </brDomainNodes>
</brasqos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<brasqos xmlns="http://www.huawei.com/netconf/vrp/huawei-brasqos">
    <brDomainNodes>
        <brDomainNode>
            <domainName>%s</domainName>
            <qOSProAppDomCfgNodes>
                <qOSProAppDomCfgNode/>
            </qOSProAppDomCfgNodes>
        </brDomainNode>
    </brDomainNodes>
</brasqos>
</filter>
"""


class QosDomainQOSProfileCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.domainName = self.module.params['domainName']
        self.profileName = self.module.params['profileName']
        self.direction = self.module.params['direction']
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
        msg_para = ""
        if not self.domainName:
            msg_para += " domainName"
        if self.operation != "getconfig":
            if not self.profileName:
                msg_para += " profileName"
            if not self.direction:
                msg_para += " direction"
        if msg_para:
            self.module.fail_json(
                msg='Error: Please input the necessary element includes%s.' % msg_para)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % self.domainName
        conf_str = constr_leaf_value(conf_str, 'profileName', self.profileName)
        conf_str = constr_leaf_value(conf_str, 'direction', self.direction)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qOSProAppDomCfgNode>',
                '<qOSProAppDomCfgNode xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_domainqosprofile(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_domainqosprofile(self):
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS % self.domainName
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return output_msg_list
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</qOSProAppDomCfgNode>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                find_direction = re.findall(
                    r'.*<direction>(.*)</direction>.*\s*', xml_str_split[j])
                find_profileName = re.findall(
                    r'.*<profileName>(.*)</profileName>.*\s*', xml_str_split[j])
                if find_profileName:
                    attr = dict()
                    attr['domainName'] = self.domainName
                    attr['profileName'] = find_profileName[0]
                    attr['direction'] = find_direction[0]

                    output_msg_list.append(attr)

        return output_msg_list

    def undo_domainqosprofile(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.domainName:
            self.proposed["domainName"] = self.domainName
        if self.profileName:
            self.proposed["profileName"] = self.profileName
        if self.direction:
            self.proposed["directione"] = self.direction
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        domainqosprofilecfg_attr_exist = self.get_domainqosprofile()
        if domainqosprofilecfg_attr_exist:
            self.results["existing"] = domainqosprofilecfg_attr_exist

        if self.operation == 'create':
            self.merge_domainqosprofile()

        if self.operation == 'delete':
            self.undo_domainqosprofile()

        domainqosprofilecfg_attr_end_state = self.get_domainqosprofile()
        if domainqosprofilecfg_attr_end_state:
            self.results["end_state"] = domainqosprofilecfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        domainName=dict(required=False, type='str'),
        profileName=dict(required=False, type='str'),
        direction=dict(required=False, choices=['inbound', 'outbound']),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosDomainQOSProfileCfg = QosDomainQOSProfileCfg(argument_spec)
    NEWQosDomainQOSProfileCfg.work()


if __name__ == '__main__':
    main()
