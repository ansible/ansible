# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import socket
import copy
import re


from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_CREATE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_MERGE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_OPERATION_DELETE
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_GET_MPLS_TAIL
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_HEAD
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import NE_COMMON_XML_PROCESS_MPLS_TAIL

from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_value
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_leaf_novalue
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_tail
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_head
from ansible.modules.network.ne.mpls.mplscomm.ne_mpls_def import constr_container_process_tail

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_mpls_interface
version_added: "2.6"
short_description:  Enables the list of interfaces on which MPLS is enabled.
description:
    - Enables the list of interfaces on which MPLS is enabled.
author: Haoliansheng (@CloudEngine-Ansible)
notes:
options:
    interfacename:
        description:
            - Specifies an MPLS interface name.
        required: false
        default: null
    mtuvalue:
        description:
            - Specifies the MTU of an MPLS interface.
        required: false
        default: null
    state:
        description:
            - Specify desired state of the resource.
        required: true
        default: present
        choices: ['present', 'absent', 'query']
'''

EXAMPLES = '''
- name: NE device mpls module test
  hosts: nedevice1
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli
  connection: netconf
  gather_facts: no

  tasks:

  - name: "Create interface Ethernet4/0/0"
    ne_mpls_mplsInterface: interfaceName=Ethernet4/0/0 mtuValue=1201 state=present provider="{{ cli }}"
    register: data
    ignore_errors: false

  - name: "Merge interface Ethernet4/0/0`s mtuValue to 1234"
    ne_mpls_mplsInterface: interfaceName=Ethernet4/0/0 mtuValue=1234 state=present provider="{{ cli }}"
    register: data
    ignore_errors: false

  - name: "Query all interfaces"
    ne_mpls_mplsInterface: state=query provider="{{ cli }}"
    register: data
    ignore_errors: false

  - name: "Delete interface Ethernet4/0/0"
    ne_mpls_mplsInterface: interfaceName=Ethernet4/0/0 state=absent provider="{{ cli }}"
    register: data
    ignore_errors: false

'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: { "interfacename": "Ethernet3/0/1",         "mtuvalue": 1000,         "state": "present"}
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: { "interfacename": "Ethernet3/0/1"}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: { "interfacename": "Ethernet3/0/1",         "mtuvalue": 1000}
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


class MPLS_mplsInterface(object):
    """Manages configuration of an MPLS_mplsInterface instance."""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.interfacename = self.module.params['interfacename']
        self.mtuvalue = self.module.params['mtuvalue']
        # self.ldpenable     = self.module.params['ldpenable']
        # self.mplsteenable  = self.module.params['mplsteenable']
        # self.rsvpteenable  = self.module.params['rsvpteenable']

        self.state = self.module.params['state']
        # mplsInterface info
        self.mplsInterface_info = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init module"""

        # required bulabulabula~~~~~
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        # check interfacename
        if self.interfacename:
            if len(self.interfacename) > 63 or len(self.interfacename.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: interfaceName is not int the range form 1 to 63.')

        # check mtuValue
        if self.mtuvalue:
            if int(self.mtuvalue) < 0 or int(self.mtuvalue) > 50000:
                self.module.fail_json(
                    msg='Error: mtuValue is not in the range from 0 to 50000.')

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_mplsInterface_dict(self):
        """get one mplsInterface attributes dict."""

        mplsInterface_info = dict()

        # Head info
        conf_str = NE_COMMON_XML_GET_MPLS_HEAD

        # Body info
        conf_str = constr_container_head(conf_str, "mplsCommon")
        conf_str = constr_container_head(conf_str, "mplsInterfaces")
        conf_str = constr_container_head(conf_str, "mplsInterface")

        conf_str = constr_leaf_value(conf_str, "interfaceName", self.interfacename)
        conf_str = constr_leaf_novalue(conf_str, "mtuValue")
        # conf_str = constr_leaf_novalue(conf_str, "ldpEnable")
        # conf_str = constr_leaf_novalue(conf_str, "mplsTEEnable")
        # conf_str = constr_leaf_novalue(conf_str, "rsvpTEEnable")

        conf_str = constr_container_tail(conf_str, "mplsInterface")
        conf_str = constr_container_tail(conf_str, "mplsInterfaces")
        conf_str = constr_container_tail(conf_str, "mplsCommon")

        # Tail info
        conf_str += NE_COMMON_XML_GET_MPLS_TAIL

        xml_str = get_nc_config(self.module, conf_str)

        # 如果<rpc-reply>的<data>标签是空的,也就是说是"<data/>"的形式,则返回空的dict()
        if "<data/>" in xml_str:
            return mplsInterface_info

        # 如果<rpc-reply>的<data>标签非空,把查到的数据写到dict()中
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp/huawei-mpls"', "")

        # get process base info
        root = ElementTree.fromstring(xml_str)

        mplsInterfaces = root.findall("data/mpls/mplsCommon/mplsInterfaces/mplsInterface")
        if mplsInterfaces is not None:
            mplsInterface_info['interfaces'] = list()
            for interface in mplsInterfaces:
                interface_dict = dict()
                for ele in interface:
                    if ele.tag in ["interfaceName",
                                   "mtuValue",
                                   "ldpEnable",
                                   "mplsTEEnable",
                                   "rsvpTEEnable"]:
                        interface_dict[ele.tag.lower()] = ele.text
                mplsInterface_info['interfaces'].append(interface_dict)

        return mplsInterface_info

    def get_proposed(self):
        """get proposed info"""

        self.proposed["interfacename"] = self.interfacename
        self.proposed["state"] = self.state

        if self.mtuvalue:
            self.proposed["mtuvalue"] = self.mtuvalue

    def get_existing(self):
        """get existing info"""
        if not self.mplsInterface_info:
            return
        self.existing = copy.deepcopy(self.mplsInterface_info)

    def get_end_state(self):
        """get end state info"""

        mplsInterface_info = self.get_mplsInterface_dict()
        if not mplsInterface_info:
            return

        self.end_state = copy.deepcopy(mplsInterface_info)

    def common_process(self, operationType, operationDesc):
        """common process"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD

        # Body process
        xml_str = constr_container_head(xml_str, "mplsCommon")
        xml_str = constr_container_process_head(xml_str, "mplsInterface", operationType)

        xml_str = constr_leaf_value(xml_str, "interfaceName", self.interfacename)
        xml_str = constr_leaf_value(xml_str, "mtuValue", self.mtuvalue)
        xml_str = constr_container_process_tail(xml_str, "mplsInterface")
        xml_str = constr_container_tail(xml_str, "mplsCommon")

        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL
        recv_xml = set_nc_config(self.module, xml_str)

        self.check_response(recv_xml, operationDesc)
        self.changed = True

    def create_process(self):
        """Create mplsInterface process"""

        self.common_process(NE_COMMON_XML_OPERATION_CREATE, "CREATE_PROCESS")

    def merge_process(self):
        """Merge mplsInterface process"""

        self.common_process(NE_COMMON_XML_OPERATION_MERGE, "MERGE_PROCESS")

    def delete_process(self):
        """Delete mplsInterface process"""

        # Head process
        xml_str = NE_COMMON_XML_PROCESS_MPLS_HEAD

        # Body process
        xml_str = constr_container_head(xml_str, "mplsCommon")
        xml_str = constr_container_process_head(xml_str, "mplsInterface", NE_COMMON_XML_OPERATION_DELETE)

        xml_str = constr_leaf_value(xml_str, "interfaceName", self.interfacename)

        xml_str = constr_container_process_tail(xml_str, "mplsInterface")
        xml_str = constr_container_tail(xml_str, "mplsCommon")

        # Tail process
        xml_str += NE_COMMON_XML_PROCESS_MPLS_TAIL

        recv_xml = set_nc_config(self.module, xml_str)
        self.check_response(recv_xml, "DELETE_PROCESS")

        self.changed = True

    def work(self):
        """worker"""

        # 参数检查
        self.check_params()

        # 查info
        self.mplsInterface_info = self.get_mplsInterface_dict()
        # 取目的态
        self.get_proposed()
        # 查初态
        self.get_existing()

        # 根据state分发给不同的处理函数
        if self.state == "present":
            if not self.mplsInterface_info:
                # create
                self.create_process()
            else:
                # merge
                self.merge_process()

        elif self.state == "absent":
            if self.mplsInterface_info:
                # delete
                self.delete_process()
            else:
                self.module.fail_json(msg='Error: MPLS Interface does not exist ')

        elif self.state == "query":
            # 查询输出
            if not self.mplsInterface_info:
                self.module.fail_json(msg='Error: mplsInterface instance does not exist ')

        # 查终态
        self.get_end_state()

        # 生成结果
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        # if self.changed:
        #    self.results['updates'] = self.updates_cmd
        # else:
        #    self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """Module Main"""

    argument_spec = dict(
        interfacename=dict(required=True, type='str'),
        mtuvalue=dict(required=False, type='int'),
        # Following parameter does not support configure.
        # ldpenable     = dict(required = False, choices = ['true', 'false']),
        # mplsteenable  = dict(required = False, choices = ['true', 'false']),
        # rsvpteenable  = dict(required = False, choices = ['true', 'false']),

        state=dict(required=False, default='present',
                   choices=['present', 'absent', 'query'])
    )

    argument_spec.update(ne_argument_spec)
    module = MPLS_mplsInterface(argument_spec)
    # Just Do It!
    module.work()


if __name__ == '__main__':
    main()
