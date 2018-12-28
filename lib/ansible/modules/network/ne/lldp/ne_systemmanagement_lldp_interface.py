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
module: ne_systemmanagement_lldp_interface
version_added: "2.6"
short_description: Enable the interface lldp capability.
description:
    - You can use this command to enable the interface lldp capability.
author: qinweikun (@netengine-Ansible)
options:
    lldpEnable:
        description:
            - The choice of lldp.
        required: false
        default: enable
        choice: ["enable", "disable"]
    ifname:
        description:
            - The choice of interface.
        required: true
        default:
        choice: [""gigabitethernet", "eth-trunk", "ip-trunk", "pos", "tunnel", "null", "loopback", "vlanif",
                 "100ge", "40ge", "mtunnel", "cpos", "e1", "serial", "vritual-ethernet", "ima-group", "vbridge",
                 "atm-bundle", "lmpif", "t1", "t3", "global-ve", "vbdif", "e3", "pos-trunk", "trunk-serial",
                 "global-ima-group", "global-mp-group", "wdm", "nve", "virtual-template", "atm", "xgigabitethernet",
                 "flexe", "50|100ge", "50ge", "pw-ve", "virtual-serial", "400ge""]
'''

EXAMPLES = '''
- name: ne_systemmanagement_lldp_interface test
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
  - name: config the interface lldp
    ne_systemmanagement_lldp:
      name: GigabitEthernet2/0/0
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"ifname":"GigabitEthernet2/0/0"}
updates:
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


LLDPIF_CFG_HEAD = """
<config>
      <lldp xmlns="http://www.huawei.com/netconf/vrp/huawei-lldp">
        <lldpInterfaces>
          <lldpInterface>
"""

LLDPIFSUB_CFG_HEAD = """
<tlvTxEnable>
"""

LLDPIFSUB_CFG_TAIL = """
</tlvTxEnable>
"""

LLDPIF_CFG_TAIL = """
          </lldpInterface>
        </lldpInterfaces>
</lldp>
</config>
"""

LLDPIFNAME = """
      <ifName>%s</ifName>"""

LLDPIF_ADMINSTATUS = """
      <lldpAdminStatus>%s</lldpAdminStatus>"""

LLDPIF_MANADDRTXENABLE = """
      <manAddrTxEnable>%s</manAddrTxEnable>"""

LLDPIF_MANADDRTXENABLE_DELETE = """
      <manAddrTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</manAddrTxEnable>"""

LLDPIF_PORTDESCTXENABLE = """
      <portDescTxEnable>%s</portDescTxEnable>"""

LLDPIF_PORTDESCTXENABLE_DELETE = """
      <portDescTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</portDescTxEnable>"""

LLDPIF_SYSCAPTXENABLE = """
      <sysCapTxEnable>%s</sysCapTxEnable>"""

LLDPIF_SYSCAPTXENABLE_DELETE = """
      <sysCapTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sysCapTxEnable>"""

LLDPIF_SYSDESCTXENABLE = """
      <sysDescTxEnable>%s</sysDescTxEnable>"""

LLDPIF_SYSDESCTXENABLE_DELETE = """
      <sysDescTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sysDescTxEnable>"""

LLDPIF_SYSNAMETXENABLE = """
      <sysNameTxEnable>%s</sysNameTxEnable>"""

LLDPIF_SYSNAMETXENABLE_DELETE = """
      <sysNameTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</sysNameTxEnable>"""

LLDPIF_PORTVLANTXENABLE = """
      <portVlanTxEnable>%s</portVlanTxEnable>"""

LLDPIF_PORTVLANTXENABLE_DELETE = """
      <portVlanTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</portVlanTxEnable>"""

LLDPIF_POROTOVLANTXENABLE = """
      <protoVlanTxEnable>%s</protoVlanTxEnable>"""

LLDPIF_POROTOVLANTXENABLE_DELETE = """
      <protoVlanTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</protoVlanTxEnable>"""

LLDPIF_TXPROTOCOLVLANID = """
      <txProtocolVlanId>%s</txProtocolVlanId>"""

LLDPIF_TXPROTOCOLVLANID_DELETE = """
      <txProtocolVlanId nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</txProtocolVlanId>"""

LLDPIF_VLANNAMETXENABLE = """
      <vlanNameTxEnable>%s</vlanNameTxEnable>"""

LLDPIF_VLANNAMETXENABLE_DELETE = """
      <vlanNameTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</vlanNameTxEnable>"""

LLDPIF_TXVLANNAMEID = """
      <txVlanNameId>%s</txVlanNameId>"""

LLDPIF_TXVLANNAMEID_DELETE = """
      <txVlanNameId nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</txVlanNameId>"""

LLDPIF_PROTOIDTXENABLE = """
      <protoIdTxEnable>%s</protoIdTxEnable>"""

LLDPIF_PROTOIDTXENABLE_DELETE = """
      <protoIdTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</protoIdTxEnable>"""

LLDPIF_MACPHYTXENABLE = """
      <macPhyTxEnable>%s</macPhyTxEnable>"""

LLDPIF_MACPHYTXENABLE_DELETE = """
      <macPhyTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</macPhyTxEnable>"""

LLDPIF_LINKAGGRETXENABLE = """
      <linkAggreTxEnable>%s</linkAggreTxEnable>"""

LLDPIF_LINKAGGRETXENABLE_DELETE = """
      <linkAggreTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</linkAggreTxEnable>"""

LLDPIF_MAXFRAMETXENABLE = """
      <maxFrameTxEnable>%s</maxFrameTxEnable>"""

LLDPIF_MAXFRAMETXENABLE_DELETE = """
      <maxFrameTxEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</maxFrameTxEnable>"""

LLDPIF_DDP = """
      <ddp>%s</ddp>"""

LLDPIF_DDP_DELETE = """
      <ddp nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</ddp>"""


class MyOperation(object):
    """
     My Operation Concrete Realization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.ifName = self.module.params['ifName']
        self.lldpAdminStatus = self.module.params['lldpAdminStatus']
        self.manAddrTxEnable = self.module.params['manAddrTxEnable']
        self.portDescTxEnable = self.module.params['portDescTxEnable']
        self.sysCapTxEnable = self.module.params['sysCapTxEnable']
        self.sysDescTxEnable = self.module.params['sysDescTxEnable']
        self.sysNameTxEnable = self.module.params['sysNameTxEnable']
        self.portVlanTxEnable = self.module.params['portVlanTxEnable']
        self.protoVlanTxEnable = self.module.params['protoVlanTxEnable']
        self.txProtocolVlanId = self.module.params['txProtocolVlanId']
        self.vlanNameTxEnable = self.module.params['vlanNameTxEnable']
        self.txVlanNameId = self.module.params['txVlanNameId']
        self.protoIdTxEnable = self.module.params['protoIdTxEnable']
        self.macPhyTxEnable = self.module.params['macPhyTxEnable']
        self.linkAggreTxEnable = self.module.params['linkAggreTxEnable']
        self.maxFrameTxEnable = self.module.params['maxFrameTxEnable']
        self.ddp = self.module.params['ddp']
        self.operation = self.module.params['operation']
        self.results = dict()
        self.results['response'] = []

    def check_params(self):
        if self.txProtocolVlanId:
            if int(self.txProtocolVlanId) < 1 or int(
                    self.txProtocolVlanId) > 4094:
                self.module.fail_json(
                    msg='Error: The txProtocolVlanId not in the range from 1 to 4094.')

        if self.txVlanNameId:
            if int(self.txVlanNameId) < 1 or int(self.txVlanNameId) > 4094:
                self.module.fail_json(
                    msg='Error: The txVlanNameId not in the range from 1 to 4094.')

        if self.lldpAdminStatus and self.operation == 'delete':
            self.module.fail_json(
                msg='Error: The lldpAdminStatus cannot be deleted.')

    def config_str_tlvTxEnable_create(self):
        cfg_str_subcreate = ''
        cfg_str_subcreate += LLDPIFSUB_CFG_HEAD
        if self.manAddrTxEnable:
            cfg_str_subcreate += LLDPIF_MANADDRTXENABLE % self.manAddrTxEnable

        if self.portDescTxEnable:
            cfg_str_subcreate += LLDPIF_PORTDESCTXENABLE % self.portDescTxEnable

        if self.sysCapTxEnable:
            cfg_str_subcreate += LLDPIF_SYSCAPTXENABLE % self.sysCapTxEnable

        if self.sysDescTxEnable:
            cfg_str_subcreate += LLDPIF_SYSDESCTXENABLE % self.sysDescTxEnable

        if self.sysNameTxEnable:
            cfg_str_subcreate += LLDPIF_SYSNAMETXENABLE % self.sysNameTxEnable

        if self.portVlanTxEnable:
            cfg_str_subcreate += LLDPIF_PORTVLANTXENABLE % self.portVlanTxEnable

        if self.protoVlanTxEnable:
            cfg_str_subcreate += LLDPIF_POROTOVLANTXENABLE % self.protoVlanTxEnable

        if self.txProtocolVlanId:
            cfg_str_subcreate += LLDPIF_TXPROTOCOLVLANID % self.txProtocolVlanId

        if self.vlanNameTxEnable:
            cfg_str_subcreate += LLDPIF_VLANNAMETXENABLE % self.vlanNameTxEnable

        if self.txVlanNameId:
            cfg_str_subcreate += LLDPIF_TXVLANNAMEID % self.txVlanNameId

        if self.protoIdTxEnable:
            cfg_str_subcreate += LLDPIF_PROTOIDTXENABLE % self.protoIdTxEnable

        if self.macPhyTxEnable:
            cfg_str_subcreate += LLDPIF_MACPHYTXENABLE % self.macPhyTxEnable

        if self.linkAggreTxEnable:
            cfg_str_subcreate += LLDPIF_LINKAGGRETXENABLE % self.linkAggreTxEnable

        if self.maxFrameTxEnable:
            cfg_str_subcreate += LLDPIF_MAXFRAMETXENABLE % self.maxFrameTxEnable

        if self.ddp:
            cfg_str_subcreate += LLDPIF_DDP % self.ddp

        cfg_str_subcreate += LLDPIFSUB_CFG_TAIL

        return cfg_str_subcreate

    def config_str_tlvTxEnable_delete(self):
        cfg_str_subdelete = ''
        cfg_str_subdelete += LLDPIFSUB_CFG_HEAD
        if self.manAddrTxEnable:
            cfg_str_subdelete += LLDPIF_MANADDRTXENABLE_DELETE % self.manAddrTxEnable

        if self.portDescTxEnable:
            cfg_str_subdelete += LLDPIF_PORTDESCTXENABLE_DELETE % self.portDescTxEnable

        if self.sysCapTxEnable:
            cfg_str_subdelete += LLDPIF_SYSCAPTXENABLE_DELETE % self.sysCapTxEnable

        if self.sysDescTxEnable:
            cfg_str_subdelete += LLDPIF_SYSDESCTXENABLE_DELETE % self.sysDescTxEnable

        if self.sysNameTxEnable:
            cfg_str_subdelete += LLDPIF_SYSNAMETXENABLE_DELETE % self.sysNameTxEnable

        if self.portVlanTxEnable:
            cfg_str_subdelete += LLDPIF_PORTVLANTXENABLE_DELETE % self.portVlanTxEnable

        if self.protoVlanTxEnable:
            cfg_str_subdelete += LLDPIF_POROTOVLANTXENABLE_DELETE % self.protoVlanTxEnable

        if self.txProtocolVlanId:
            cfg_str_subdelete += LLDPIF_TXPROTOCOLVLANID_DELETE % self.txProtocolVlanId

        if self.vlanNameTxEnable:
            cfg_str_subdelete += LLDPIF_VLANNAMETXENABLE_DELETE % self.vlanNameTxEnable

        if self.txVlanNameId:
            cfg_str_subdelete += LLDPIF_TXVLANNAMEID_DELETE % self.txVlanNameId

        if self.protoIdTxEnable:
            cfg_str_subdelete += LLDPIF_PROTOIDTXENABLE_DELETE % self.protoIdTxEnable

        if self.macPhyTxEnable:
            cfg_str_subdelete += LLDPIF_MACPHYTXENABLE_DELETE % self.macPhyTxEnable

        if self.linkAggreTxEnable:
            cfg_str_subdelete += LLDPIF_LINKAGGRETXENABLE_DELETE % self.linkAggreTxEnable

        if self.maxFrameTxEnable:
            cfg_str_subdelete += LLDPIF_MAXFRAMETXENABLE_DELETE % self.maxFrameTxEnable

        if self.ddp:
            cfg_str_subdelete += LLDPIF_DDP_DELETE % self.ddp

        cfg_str_subdelete += LLDPIFSUB_CFG_TAIL

        return cfg_str_subdelete

    def config_str(self):
        cfg_str = ''
        cfg_str += LLDPIF_CFG_HEAD
        cfg_str += LLDPIFNAME % self.ifName
        if self.operation == 'create':
            if self.lldpAdminStatus:
                cfg_str += LLDPIF_ADMINSTATUS % self.lldpAdminStatus

            if (self.manAddrTxEnable or self.portDescTxEnable or self.sysCapTxEnable
                or self.sysDescTxEnable or self.sysNameTxEnable or self.portVlanTxEnable
                or self.protoVlanTxEnable or self.txProtocolVlanId or self.vlanNameTxEnable
                or self.txVlanNameId or self.protoIdTxEnable or self.macPhyTxEnable
                    or self.linkAggreTxEnable or self.maxFrameTxEnable or self.ddp):

                cfg_str += self.config_str_tlvTxEnable_create()

        if self.operation == 'delete':
            if (self.manAddrTxEnable or self.portDescTxEnable or self.sysCapTxEnable
                or self.sysDescTxEnable or self.sysNameTxEnable or self.portVlanTxEnable
                or self.protoVlanTxEnable or self.txProtocolVlanId or self.vlanNameTxEnable
                or self.txVlanNameId or self.protoIdTxEnable or self.macPhyTxEnable
                    or self.linkAggreTxEnable or self.maxFrameTxEnable or self.ddp):

                cfg_str += self.config_str_tlvTxEnable_delete()

        cfg_str += LLDPIF_CFG_TAIL

        return cfg_str

    def run(self):
        self.check_params()
        recv_xml = set_nc_config(self.module, self.config_str())
        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    """ main module """
    argument_spec = dict(
        ifName=dict(required=True, type='str'),
        lldpAdminStatus=dict(
            required=False,
            choices=[
                'txOnly',
                'rxOnly',
                'txAndRx',
                'disabled']),
        manAddrTxEnable=dict(required=False, choices=['true', 'false']),
        portDescTxEnable=dict(required=False, choices=['true', 'false']),
        sysCapTxEnable=dict(required=False, choices=['true', 'false']),
        sysDescTxEnable=dict(required=False, choices=['true', 'false']),
        sysNameTxEnable=dict(required=False, choices=['true', 'false']),
        portVlanTxEnable=dict(required=False, choices=['true', 'false']),
        protoVlanTxEnable=dict(required=False, choices=['true', 'false']),
        txProtocolVlanId=dict(required=False, type='int'),
        vlanNameTxEnable=dict(required=False, choices=['true', 'false']),
        txVlanNameId=dict(required=False, type='int'),
        protoIdTxEnable=dict(required=False, choices=['true', 'false']),
        macPhyTxEnable=dict(required=False, choices=['true', 'false']),
        linkAggreTxEnable=dict(required=False, choices=['true', 'false']),
        maxFrameTxEnable=dict(required=False, choices=['true', 'false']),
        ddp=dict(required=False, choices=['true', 'false']),
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
