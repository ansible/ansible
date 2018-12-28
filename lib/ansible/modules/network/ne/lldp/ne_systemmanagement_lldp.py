#!/usr/bin/python
# coding=utf-8
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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ne_systemmanagement_lldp
version_added: "2.6"
short_description: Enable the system lldp capability.
description:
    - You can use this command to enable the system lldp capability. When operation is set to delete, the options is only lldpEnable.
author: qinweikun (@netengine-Ansible)
options:
    lldpEnable:
        description:
            - The choice of lldp.
        required: false
        default: enable
        choice: ["enable", "disable"]
'''

EXAMPLES = '''
- name: ne_systemmanagement_lldp test
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
  - name: config lldp
    ne_systemmanagement_lldp:
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"lldpEnable":"lldpenable"}
updates:
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


LLDPSYS_CFG_HEAD = """
<config>
      <lldp xmlns="http://www.huawei.com/netconf/vrp/huawei-lldp">
        <lldpSys>
"""

LLDPSYSPARAMETER_CFG_HEAD = """
<lldpSysParameter>
"""

LLDPSYSPARAMETER_CFG_TAIL = """
</lldpSysParameter>
"""

LLDPSYS_TAIL = """
    </lldpSys>
  </lldp>
</config>
"""

LLDPENABLE = """
      <lldpEnable>%s</lldpEnable>"""

MSGTXINTERVAL = """
      <messageTxInterval>%s</messageTxInterval>"""

MSGTXHOLDMUL = """
      <messageTxHoldMultiplier>%s</messageTxHoldMultiplier>"""

REINITDELAY = """
      <reinitDelay>%s</reinitDelay>"""

TXDELAY = """
      <txDelay>%s</txDelay>"""

NOTIINTERVAL = """
      <notificationInterval>%s</notificationInterval>"""

FASTMESCOUNT = """
      <fastMessageCount>%s</fastMessageCount>"""

CONFIGMACADDR = """
      <configManAddr>%s</configManAddr>"""

LLDPENABLE_DELETE = """
      <lldpEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</lldpEnable>"""

MSGTXINTERVAL_DELETE = """
      <messageTxInterval nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</messageTxInterval>"""

MSGTXHOLDMUL_DELETE = """
      <messageTxHoldMultiplier nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</messageTxHoldMultiplier>"""

REINITDELAY_DELETE = """
      <reinitDelay nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</reinitDelay>"""

TXDELAY_DELETE = """
      <txDelay nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</txDelay>"""

NOTIINTERVAL_DELETE = """
      <notificationInterval nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</notificationInterval>"""

FASTMESCOUNT_DELETE = """
      <fastMessageCount nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</fastMessageCount>"""

CONFIGMACADDR_DELETE = """
      <configManAddr nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</configManAddr>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.lldpEnable = self.module.params['lldpEnable']
        self.messageTxInterval = self.module.params['messageTxInterval']
        self.messageTxHoldMultiplier = self.module.params['messageTxHoldMultiplier']
        self.reinitDelay = self.module.params['reinitDelay']
        self.txDelay = self.module.params['txDelay']
        self.notificationInterval = self.module.params['notificationInterval']
        self.fastMessageCount = self.module.params['fastMessageCount']
        self.configManAddr = self.module.params['configManAddr']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if self.messageTxInterval:
            if int(self.messageTxInterval) < 5 or int(
                    self.messageTxInterval) > 32768:
                self.module.fail_json(
                    msg='Error: The messageTxInterval not in the range from 5 to 32768.')

        if self.messageTxHoldMultiplier:
            if int(self.messageTxHoldMultiplier) < 2 or int(
                    self.messageTxHoldMultiplier) > 10:
                self.module.fail_json(
                    msg='Error: The messageTxHoldMultiplier not in the range from 2 to 10.')

        if self.reinitDelay:
            if int(self.reinitDelay) < 1 or int(self.reinitDelay) > 10:
                self.module.fail_json(
                    msg='Error: The reinitDelay not in the range from 1 to 10.')

        if self.txDelay:
            if int(self.txDelay) < 1 or int(self.txDelay) > 8192:
                self.module.fail_json(
                    msg='Error: The txDelay not in the range from 1 to 8192.')

        if self.notificationInterval:
            if int(self.notificationInterval) < 5 or int(
                    self.notificationInterval) > 3600:
                self.module.fail_json(
                    msg='Error: The notificationInterval not in the range from 5 to 3600.')

        if self.fastMessageCount:
            if int(self.fastMessageCount) < 1 or int(
                    self.fastMessageCount) > 8:
                self.module.fail_json(
                    msg='Error: The fastMessageCount not in the range from 1 to 8.')

    def config_str(self):
        cfg_str = ''
        cfg_str += LLDPSYS_CFG_HEAD
        if self.operation == 'create':
            if self.lldpEnable:
                cfg_str += LLDPENABLE % self.lldpEnable

            if (self.messageTxInterval or self.messageTxHoldMultiplier or self.messageTxHoldMultiplier or self.reinitDelay
                    or self.txDelay or self.notificationInterval or self.fastMessageCount or self.configManAddr):
                cfg_str += LLDPSYSPARAMETER_CFG_HEAD
                if self.messageTxInterval:
                    cfg_str += MSGTXINTERVAL % self.messageTxInterval
                if self.messageTxHoldMultiplier:
                    cfg_str += MSGTXHOLDMUL % self.messageTxHoldMultiplier
                if self.reinitDelay:
                    cfg_str += REINITDELAY % self.reinitDelay
                if self.txDelay:
                    cfg_str += TXDELAY % self.txDelay
                if self.notificationInterval:
                    cfg_str += NOTIINTERVAL % self.notificationInterval
                if self.fastMessageCount:
                    cfg_str += FASTMESCOUNT % self.fastMessageCount
                if self.configManAddr:
                    cfg_str += CONFIGMACADDR % self.configManAddr
                cfg_str += LLDPSYSPARAMETER_CFG_TAIL

        if self.operation == 'delete':
            if self.lldpEnable:
                cfg_str += LLDPENABLE_DELETE % self.lldpEnable

            if self.messageTxInterval or self.messageTxHoldMultiplier or self.messageTxHoldMultiplier or self.reinitDelay or\
                    self.txDelay or self.notificationInterval or self.fastMessageCount or self.configManAddr:
                cfg_str += LLDPSYSPARAMETER_CFG_HEAD
                if self.messageTxInterval:
                    cfg_str += MSGTXINTERVAL_DELETE % self.messageTxInterval
                if self.messageTxHoldMultiplier:
                    cfg_str += MSGTXHOLDMUL_DELETE % self.messageTxHoldMultiplier
                if self.reinitDelay:
                    cfg_str += REINITDELAY_DELETE % self.reinitDelay
                if self.txDelay:
                    cfg_str += TXDELAY_DELETE % self.txDelay
                if self.notificationInterval:
                    cfg_str += NOTIINTERVAL_DELETE % self.notificationInterval
                if self.fastMessageCount:
                    cfg_str += FASTMESCOUNT_DELETE % self.fastMessageCount
                if self.configManAddr:
                    cfg_str += CONFIGMACADDR_DELETE % self.configManAddr
                cfg_str += LLDPSYSPARAMETER_CFG_TAIL

        cfg_str += LLDPSYS_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        lldpEnable=dict(required=False, choices=['enabled', 'disabled']),
        messageTxInterval=dict(required=False, type='int'),
        messageTxHoldMultiplier=dict(required=False, type='int'),
        reinitDelay=dict(required=False, type='int'),
        txDelay=dict(required=False, type='int'),
        notificationInterval=dict(required=False, type='int'),
        fastMessageCount=dict(required=False, type='int'),
        configManAddr=dict(required=False, type='str'),
        operation=dict(
            required=False,
            choices=[
                'create',
                'delete'],
            default='create'),
    )
    argument_spec.update(ne_argument_spec)
    myOperation = MyOperation(argument_spec)
    myOperation.run()


if __name__ == '__main__':
    main()
