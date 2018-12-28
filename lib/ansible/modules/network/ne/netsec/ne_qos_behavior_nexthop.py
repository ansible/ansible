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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import collections
import re
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ne_qos_behavior_nexthop
version_added: "2.6"
short_description: Manages nextHop action of traffic behavior on HUAWEI NetEngine devices.
description:
    - Manages nextHop action of traffic behavior on HUAWEI NetEngine devices.
author:Pangaoping
options:
    behaviorName:
        description:
            - Name of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    description
        description:
            - Description information of traffic behavior.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    nextHop:
        description:
            - Filtering action.
              If the value is permit, allow the packets that meet the rules to pass through the device.
              If the value is deny, prohibit the packets that meet the rules from passing through the device.
        required: false
        default: null

    operation:
        description:
            - If the value is getconfig, when specify the behaviorName, query the configuration of the behaviorName, otherwise query all behavior.
        required: false
        default: create
        choices: ['create', 'merge', 'delete', 'getconfig']
'''

EXAMPLES = '''
- name: NetEngine ne_behavior_nexthop module test
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

  - name: Create nextHop
    ne_qos_behavior_nexthop:
      behaviorName: "test"
      description: "test"
      nextHop: "1.1.1.1"
      operation: create
      provider: "{{ cli }}"

  - name: Get all traffic behavior configuration
    ne_behavior_nextHop:
      operation: getconfig
      provider: "{{ cli }}"

  - name: Get traffic behavior test configuration
    ne_qos_behavior_fillter:
      behaviorName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
existing:
    description: k/v pairs of existing traffic behavior
    returned: always
    type: dict
    sample: { "behaviorName": "test", "description": "2222", "nextHop": "1.1.1.1" }
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosBehaviors>
            <qosBehavior>
                <behaviorName>%s</behaviorName>
"""
MERGE_DES = """
                <description>%s</description>
"""

MERGE_URPF_HEAD = """
            <qosActRdrNhps>
                <qosActRdrNhp>
                    <rdrType>%s</rdrType>
                    <nextHop>%s</nextHop>

"""
MERGE_URPF_HEAD_OPTION_VPN = """
                    <vpnName>%s</vpnName>
"""
MERGE_URPF_HEAD_OPTION_NQA = """
                    <nqaAdminName>%s</nqaAdminName>
                    <nqaInstance>%s</nqaInstance>
"""
MERGE_URPF_TAIL = """
                    <filterDefault>%s</filterDefault>
                    <filterBlackhole>%s</filterBlackhole>
                    <drop>%s</drop>
                    <hroute>%s</hroute>
                </qosActRdrNhp>
            </qosActRdrNhps>
"""
MERGE_CLASS_TAIL = """
            </qosBehavior>
        </qosBehaviors>
    </qosCbQos>
</qos>
</config>
"""

QOS_IFCAR_CFGGET = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosCbQos>
        <qosBehaviors>
            <qosBehavior>
                <behaviorName>%s</behaviorName>
                <description></description>
                <qosActRdrNhps>
                    <qosActRdrNhp>
                      <rdrType></rdrType>
                      <nextHop></nextHop>
                      <vpnName></vpnName>
                      <nqaAdminName></nqaAdminName>
                      <nqaInstance></nqaInstance>
                      <filterDefault></filterDefault>
                      <filterBlackhole></filterBlackhole>
                      <drop></drop>
                      <hroute></hroute>
                    </qosActRdrNhp>
                </qosActRdrNhps>
            </qosBehavior>
        </qosBehaviors>
    </qosCbQos>
</qos>
</filter>
"""


class QosIfCarCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosifcar config info
        self.behaviorName = self.module.params['behaviorName']
        self.description = self.module.params['description']
        self.rdrType = self.module.params['rdrType']
        self.nextHop = self.module.params['nextHop']
        self.vpnName = self.module.params['vpnName']
        self.nqaAdminName = self.module.params['nqaAdminName']
        self.nqaInstance = self.module.params['nqaInstance']
        self.filterDefault = self.module.params['filterDefault']
        self.filterBlackhole = self.module.params['filterBlackhole']
        # self.routeforward = self.module.params['routeforward']
        self.drop = self.module.params['drop']
        self.hroute = self.module.params['hroute']
        # self.public = self.module.params['public']

        self.operation = self.module.params['operation']
        print('conf_str00000000000000', self.behaviorName)
        # states
        self.changed = False
        self.results = dict()
        self.results["end_state"] = []
        self.proposed = dict()

    def init_module(self):
        """
        init ansilbe NetworkModule.
        """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        if not self.behaviorName and self.operation != 'getconfig':
            self.module.fail_json(
                msg='Error: Please input the necessary element includes behaviorName.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None

        conf_str = MERGE_CLASS_HEALDER % (self.behaviorName)
        if self.description:
            conf_str += MERGE_DES % (self.description)

        if not self.filterDefault:
            self.filterDefault = 'false'
        if not self.filterBlackhole:
            self.filterBlackhole = 'false'
        # if not self.routeforward:
            # self.routeforward = 'false'
        if not self.drop:
            self.drop = 'false'
        if not self.hroute:
            self.hroute = 'false'
        # if not self.public:
            # self.public = 'false'

        if self.rdrType:
            conf_str += MERGE_URPF_HEAD % (self.rdrType, self.nextHop)
            if self.vpnName:
                conf_str += MERGE_URPF_HEAD_OPTION_VPN % (self.vpnName)
            if self.nqaAdminName and self.nqaInstance:
                conf_str += MERGE_URPF_HEAD_OPTION_NQA % (
                    self.nqaAdminName, self.nqaInstance)
            conf_str += MERGE_URPF_TAIL % (self.filterDefault,
                                           self.filterBlackhole, self.drop, self.hroute)

        if self.operation == 'delete':
            if self.nextHop and self.rdrType:
                # global conf_str
                conf_str = conf_str.replace(
                    '<qosActRdrNhp>', '<qosActRdrNhp xc:operation="delete">')
            else:
                conf_str = conf_str.replace(
                    '<qosBehavior>', '<qosBehavior xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('conf_str88888', conf_str)
        return conf_str

    def merge_ifcar(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "MERGE_PROCESS")

        self.changed = True

    def get_ifcar(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        if not self.behaviorName:
            self.behaviorName = ' '
        conf_str = None
        conf_str = QOS_IFCAR_CFGGET % (self.behaviorName)
        print('conf_str11111', conf_str)

        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str11111111111', xml_str)
        # return err,'22222222222222'
        if "<data/>" in xml_str:
            return attr
        else:

            xml_str_split = re.split('</qosBehavior>', xml_str)
            print('get_ifcar66666', xml_str_split)

            for j in range(len(xml_str_split)):
                attr = dict()
                find_behaviorName = re.findall(
                    r'.*<behaviorName>(.*)</behaviorName>.*\s*', xml_str_split[j])

                find_description = re.findall(
                    r'.*<description>(.*)</description>.*\s*', xml_str_split[j])
                find_rdrType = re.findall(
                    r'.*<rdrType>(.*)</rdrType>.*\s*', xml_str_split[j])
                find_nextHop = re.findall(
                    r'.*<nextHop>(.*)</nextHop>.*\s*', xml_str_split[j])
                find_vpnName = re.findall(
                    r'.*<vpnName>(.*)</vpnName>.*\s*', xml_str_split[j])
                find_nqaAdminName = re.findall(
                    r'.*<nqaAdminName>(.*)</nqaAdminName>.*\s*', xml_str_split[j])
                find_nqaInstance = re.findall(
                    r'.*<nqaInstance>(.*)</nqaInstance>.*\s*', xml_str_split[j])
                find_filterDefault = re.findall(
                    r'.*<filterDefault>(.*)</filterDefault>.*\s*', xml_str_split[j])
                find_filterBlackhole = re.findall(
                    r'.*<filterBlackhole>(.*)</filterBlackhole>.*\s*', xml_str_split[j])
                find_drop = re.findall(
                    r'.*<drop>(.*)</drop>.*\s*', xml_str_split[j])
                # find_routeforward =
                # re.findall(r'.*<routeforward>(.*)</routeforward>.*\s*',
                # xml_str_split[j])#meiyou
                find_hroute = re.findall(
                    r'.*<hroute>(.*)</hroute>.*\s*', xml_str_split[j])
                # find_public= re.findall(r'.*<public>(.*)</public>.*\s*', xml_str_split[j])#meiyou
                # print('77777', find_behaviorName[0])

                if find_behaviorName:
                    attr['behaviorName'] = find_behaviorName[0]
                    # print('9999', find_classifierName[0])
                    if find_description:
                        attr['description'] = find_description[0]
                    if find_rdrType:
                        attr['rdrType'] = find_rdrType[0]
                    if find_nextHop:
                        attr['nextHop'] = find_nextHop[0]
                    if find_vpnName:
                        attr['vpnName'] = find_vpnName[0]
                    if find_nqaAdminName:
                        attr['nqaAdminName'] = find_nqaAdminName[0]
                    if find_nqaInstance:
                        attr['nqaInstance'] = find_nqaInstance[0]
                    if find_filterDefault:
                        attr['filterDefault'] = find_filterDefault[0]
                    if find_filterBlackhole:
                        attr['filterBlackhole'] = find_filterBlackhole[0]
                    if find_drop:
                        attr['drop'] = find_drop[0]
                    # if find_routeforward :
                        # attr['routeforward'] = find_routeforward[0]
                    if find_hroute:
                        attr['hroute'] = find_hroute[0]
                    # if find_public :
                        # attr['public'] = find_public[0]
                    output_msg_list.append(attr)

        return output_msg_list

    def undo_ifcar(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        print('recv_xml2222222222222', recv_xml)

        self.check_response(recv_xml, "DELETE_PROCESS")
        self.changed = True

    def get_proposed(self):
        """get proposed info"""

        if self.behaviorName is not None:
            self.proposed["behaviorName"] = self.behaviorName
        if self.description is not None:
            self.proposed["description"] = self.description
        if self.rdrType is not None:
            self.proposed["rdrType"] = self.rdrType
        if self.nextHop is not None:
            self.proposed["nextHop"] = self.nextHop
        if self.vpnName is not None:
            self.proposed["vpnName"] = self.vpnName
        if self.nqaAdminName is not None:
            self.proposed["nqaAdminName"] = self.nqaAdminName
        if self.nqaInstance is not None:
            self.proposed["nqaInstance"] = self.nqaInstance
        if self.filterDefault is not None:
            self.proposed["filterDefault"] = self.filterDefault
        if self.filterBlackhole is not None:
            self.proposed["filterBlackhole"] = self.filterBlackhole
        # if self.routeforward is not None:
            # self.proposed["routeforward"]       =self.routeforward
        if self.drop is not None:
            self.proposed["drop"] = self.drop
        if self.hroute is not None:
            self.proposed["hroute"] = self.hroute
        # if self.public is not None:
            # self.proposed["public"]             =self.public

        self.proposed["operation"] = self.operation

    def work(self):
        """worker"""

        self.check_params()

        self.get_proposed()
        self.results['existing'] = self.get_ifcar()

        if self.operation == 'create' or self.operation == 'merge':
            print('merge_ifcar66666', self.operation)
            self.merge_ifcar()

        if self.operation == 'delete':
            self.undo_ifcar()

        ifcarcfg_attr_exist = self.get_ifcar()
        if ifcarcfg_attr_exist:
            self.results["end_state"].append(ifcarcfg_attr_exist)

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        behaviorName=dict(required=False, type='str'),
        description=dict(required=False, type='str'),
        rdrType=dict(required=False, type='str'),
        nextHop=dict(required=False, type='str'),
        vpnName=dict(required=False, type='str'),
        nqaAdminName=dict(required=False, type='str'),
        nqaInstance=dict(required=False, type='str'),
        filterDefault=dict(required=False, type='str'),
        filterBlackhole=dict(required=False, type='str'),
        drop=dict(required=False, type='str'),
        # routeforward=dict(required=False, type='str'),
        hroute=dict(required=False, type='str'),
        # public=dict(required=False, type='str'),

        operation=dict(
            required=False,
            choices=[
                'create',
                'merge',
                'getconfig',
                'delete'],
            default='merge'),
    )

    argument_spec.update(ne_argument_spec)
    NEWCQosIfCar = QosIfCarCfg(argument_spec)
    NEWCQosIfCar.work()


if __name__ == '__main__':
    main()
