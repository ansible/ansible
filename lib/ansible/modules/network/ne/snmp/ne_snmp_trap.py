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
# GNU General Public License for more detai++++++++ls.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from ansible.modules.network.ne.snmp.ne_snmp_base import config_params_func, snmp_base_argument_spec
from ansible.modules.network.ne.snmp.ne_snmp_base import snmp_enable_config, snmp_version_config
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'snmp'}

DOCUMENTATION = '''
---
module: snmp_trap
version_added: "2.6"
short_description: Manages SNMP trap configuration on HUAWEI router.
description:
    - Manages SNMP trap configuration on HUAWEI router.SNMP trap configurations include snmp version, target host and trap switch's configuration.
author:Zhaweiwei(@netengine-Ansible)

options:
    operation:
        description:
            - Ansible operation.
        required: true
        default: null
        choices: ['create', 'delete']
    snmp_enable:
        description:
            - Enable or disable SNMP.
        required: true
        default: null
        choices: ['true', 'false']
    snmp_version:
        description:
            - SNMP version.
        required: true
        default: null
        choices: ['v1', 'v2c','v3','all']
    trap_tgt_name:
        description:
            - Unique name to identify target host entry.
        required: true
        default: null
    trap_tgt_addr:
        description:
            - Network Address.
        required: true
        default: null
    trap_port_number:
        description:
            - UDP Port number used by network management to receive alarm messages.
        required: false
        default: 162
    security_model:
        description:
            - Security Model.
        required: false
        default: v1
        choices: ['v1', 'v2c','v3']
    security_name:
        description:
            - Security Name.
        required: true
        default: null
    security_level:
        description:
            - Security level indicating whether to use authentication and encryption.
        required: yes
        default: noAuthNoPriv
        choices: ['noAuthNoPriv', 'authentication', 'privacy']
    trap_name:
        description:
            - Name of a trap.
        required: true
        default: null
    trap_feature_name:
        description:
            - Module to which a trap belongs.
        required: true
    switch_status:
        description:
            -Configured trap enabling status.
        required: true
        default: null
        choices: ['on', 'off']
    trap_enable_status:
        description:
            -Global trap switch.
        required: false
        default: default
        choices: ['enable', 'disable', 'default']
'''

EXAMPLES = '''

- name: snmp trap test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    yang:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      operation: create or delete

  tasks:

  - name: "Enable SNMP"
    snmp_trap:
      operation: create
      snmp_enable: true

  - name: "Disable SNMP"
    snmp_trap:
      operation: delete
      snmp_enable: true

  - name: "Enalbe SNMP v3 version"
    snmp_trap:
      operation: create
      snmp_version: v3

  - name: "Cancel config SNMP v3 version"
    snmp_trap:
      operation: delete
      snmp_version: v3

  - name: "Config SNMP trap target host"
    snmp_trap:
      operation: create
      trap_tgt_name: abc
      trap_tgt_addr: 1.2.3.6
      security_model: v3
      security_name: test
      security_level: privacy

  - name: "Cancel config SNMP target host"
    snmp_trap:
      operation: delete
      trap_tgt_name: abc
      trap_tgt_addr: 1.2.3.6
      security_model: v3
      security_name: test
      security_level: privacy

  - name: "Config a trap switch"
    snmp_trap:
      operation: create
      trap_name:  hwSystemConfigError
      trap_feature_name: SYSTEM
      switch_status: on

  - name: "Cancel config a trap switch"
    snmp_trap
      operation: delete
      trap_name:  hwSystemConfigError
      trap_feature_name: SYSTEM
      switch_status: on

    - name: "Config SNMP global trap switch"
    snmp_trap:
      operation: create
      trap_enable_status: enable

    - name: "Cancel config SNMP global trap switch"
    snmp_trap:
      operation: delete
      trap_enable_status: enable
'''

RETURN = '''
response:
    description: check to see config result
    returned: always
    type: result string
    sample: ok
'''


SNMP_TRAP_TGTHOST_CFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <targetHosts>
        <targetHost>
"""

SNMP_TRAP_TGTHOST_CONF_TAIL = """
            </targetHost>
        </targetHosts>
    </snmp>
</config>
"""

SNMP_TRAP_TGTHOST_DELCFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <targetHosts>
        <targetHost nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SNMP_TGT_NAME = """
    <nmsName>%s</nmsName>"""

SNMP_DOMAIN_NAME = """
    <domain>%s</domain>"""

SNMP_ADDR_NAME = """
    <address>%s</address>"""

SNMP_NOTIFYTYPE = """
    <notifyType>%s</notifyType>"""

SNMP_PORTNUM = """
    <portNumber>%s</portNumber>"""

SNMP_TGT_SECURITY_MODEL = """
    <securityModel>%s</securityModel>"""

SNMP_TGT_SECURITY_NAME = """
    <securityName>%s</securityName>"""

SNMP_TGT_V3SECURITY_NAME = """
    <securityNameV3>%s</securityNameV3>"""

SNMP_TGT_SECURITY_LEVEL = """
    <securityLevel>%s</securityLevel>"""

SNMP_TRAP_ENABLE_FEATRUE_CFG_HEAD = """
<config>
    <fm xmlns="http://www.huawei.com/netconf/vrp/huawei-fm">
        <trapCfgs>
        <trapCfg>
"""

SNMP_TRAP_ENABLE_FEATRUE_CONF_TAIL = """
    </trapCfg>
    </trapCfgs>
    </fm>
</config>
"""

SNMP_TRAP_ENABLE_FEATRUE_DELCFG_HEAD = """
<config>
    <fm xmlns="http://www.huawei.com/netconf/vrp/huawei-fm">
        <trapCfgs>
        <trapCfg nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SNMP_TRAP_NAME = """
    <trapName>%s</trapName>"""

SNMP_TRAP_FEATURENAME = """
    <featureName>%s</featureName>"""

SNMP_TRAP_CFG_STATUS = """
    <trapCfgStatus>%s</trapCfgStatus>"""

SNMP_TRAP_GOLBAL_SWITCH_CFG_HEAD = """
<config>
    <fm xmlns="http://www.huawei.com/netconf/vrp/huawei-fm">
        <globalParam>
"""

SNMP_TRAP_GOLBAL_SWITCH_CONF_TAIL = """
    </globalParam>
    </fm>
</config>
"""

SNMP_TRAP_ENALBE_DEL = """
      <gblTrapSwitch nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</gblTrapSwitch>"""

SNMP_TRAP_ENALBE = """
      <gblTrapSwitch>%s</gblTrapSwitch>"""

snmp_trap_tgt_argument_spec = {
    'trap_tgt_name': dict(type='str'),
    'trap_tgt_addr': dict(type='str'),
    'trap_port_number': dict(type='int'),
    'security_model': dict(choices=['v1', 'v2c', 'v3']),
    'security_name': dict(type='str'),
    'security_level': dict(choices=['noAuthNoPriv', 'authentication', 'privacy'])
}

snmp_trap_switch_argument_spec = {
    'trap_name': dict(type='str'),
    'trap_feature_name': dict(type='str'),
    'switch_status': dict(choices=['on', 'off'])
}

snmp_trap_enalbe_spec = {
    'trap_enable_status': dict(choices=['enable', 'disable', 'default'])
}


class SnmpTrapTgt(object):
    """
     SnmpTrapTgt
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.trap_tgt_name = self.module.params['trap_tgt_name']
        self.trap_tgt_addr = self.module.params['trap_tgt_addr']
        self.trap_port_number = self.module.params['trap_port_number']
        self.security_model = self.module.params['security_model']
        self.security_name = self.module.params['security_name']
        self.security_level = self.module.params['security_level']
        self.results = dict()
        self.results['response'] = []

    def snmp_trap_config_str(self):
        snmp_cfg_str = ''

        if self.operation == 'create':
            snmp_cfg_str += SNMP_TRAP_TGTHOST_CFG_HEAD
            if config_params_func(self.trap_tgt_name):
                snmp_cfg_str += SNMP_TGT_NAME % self.trap_tgt_name

            if config_params_func(self.trap_tgt_addr):
                snmp_cfg_str += SNMP_ADDR_NAME % self.trap_tgt_addr

            if config_params_func(self.trap_port_number):
                snmp_cfg_str += SNMP_PORTNUM % self.trap_port_number

            if config_params_func(self.security_model):
                snmp_cfg_str += SNMP_TGT_SECURITY_MODEL % self.security_model

            if self.security_model == "v3":
                if config_params_func(self.security_name):
                    snmp_cfg_str += SNMP_TGT_V3SECURITY_NAME % self.security_name

                if config_params_func(self.security_level):
                    snmp_cfg_str += SNMP_TGT_SECURITY_LEVEL % self.security_level

            else:
                if config_params_func(self.security_name):
                    snmp_cfg_str += SNMP_TGT_SECURITY_NAME % self.security_name

            snmp_cfg_str += SNMP_NOTIFYTYPE % "trap"
            snmp_cfg_str += SNMP_DOMAIN_NAME % "snmpUDPDomain"

        if self.operation == 'delete':
            snmp_cfg_str += SNMP_TRAP_TGTHOST_DELCFG_HEAD
            if config_params_func(self.trap_tgt_name):
                snmp_cfg_str += SNMP_TGT_NAME % self.trap_tgt_name

        snmp_cfg_str += SNMP_TRAP_TGTHOST_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_trap_tgt(self):
        if config_params_func(self.trap_tgt_name):
            return set_nc_config(self.module, self.snmp_trap_config_str())
        else:
            return "<ok/>"


def snmp_trap_tgt_config(argument_spec):
    """ snmp_trap_tgt_config """

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    snmp_trap_tgt_obj = SnmpTrapTgt(argument_spec)
    if not snmp_trap_tgt_obj:
        module.fail_json(msg='Error: Init snmp trap target module failed.')

    return snmp_trap_tgt_obj.set_snmp_trap_tgt()


class SnmpTrapEnable(object):
    """
     SnmpTrapEnable
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.trap_enable_status = self.module.params['trap_enable_status']
        self.results = dict()
        self.results['response'] = []

    def snmp_trap_enable_config_str(self):
        snmp_cfg_str = ''

        if self.operation == 'create':
            snmp_cfg_str += SNMP_TRAP_GOLBAL_SWITCH_CFG_HEAD
            if config_params_func(self.trap_enable_status):
                snmp_cfg_str += SNMP_TRAP_ENALBE % self.trap_enable_status

        if self.operation == 'delete':
            snmp_cfg_str += SNMP_TRAP_GOLBAL_SWITCH_CFG_HEAD
            if config_params_func(self.trap_enable_status):
                snmp_cfg_str += SNMP_TRAP_ENALBE_DEL % self.trap_enable_status

        snmp_cfg_str += SNMP_TRAP_GOLBAL_SWITCH_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_trap_enable(self):
        if config_params_func(self.trap_enable_status):
            return set_nc_config(
                self.module, self.snmp_trap_enable_config_str())
        else:
            return "<ok/>"


def snmp_trap_enable_config(argument_spec):
    """ snmp_trap_enable_config """

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    snmp_trap_enable_obj = SnmpTrapEnable(argument_spec)

    if not snmp_trap_enable_obj:
        module.fail_json(msg='Error: Init snmp trap enable module failed.')

    return snmp_trap_enable_obj.set_snmp_trap_enable()


class SnmpTrapSwitch(object):
    """
     SnmpTrapSwitch
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.trap_name = self.module.params['trap_name']
        self.trap_feature_name = self.module.params['trap_feature_name']
        self.switch_status = self.module.params['switch_status']
        self.results = dict()
        self.results['response'] = []

    def snmp_trap_switch_config_str(self):
        snmp_cfg_str = ''

        if self.operation == 'create':
            snmp_cfg_str += SNMP_TRAP_ENABLE_FEATRUE_CFG_HEAD
            if config_params_func(self.trap_name):
                snmp_cfg_str += SNMP_TRAP_NAME % self.trap_name

            if config_params_func(self.trap_feature_name):
                snmp_cfg_str += SNMP_TRAP_FEATURENAME % self.trap_feature_name

            if config_params_func(self.switch_status):
                snmp_cfg_str += SNMP_TRAP_CFG_STATUS % self.switch_status

        if self.operation == 'delete':
            snmp_cfg_str += SNMP_TRAP_ENABLE_FEATRUE_DELCFG_HEAD
            if config_params_func(self.trap_name):
                snmp_cfg_str += SNMP_TRAP_NAME % self.trap_name

            if config_params_func(self.trap_feature_name):
                snmp_cfg_str += SNMP_TRAP_FEATURENAME % self.trap_feature_name

            if config_params_func(self.switch_status):
                snmp_cfg_str += SNMP_TRAP_CFG_STATUS % self.switch_status

        snmp_cfg_str += SNMP_TRAP_ENABLE_FEATRUE_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_trap_switch(self):
        if config_params_func(self.trap_name):
            return set_nc_config(
                self.module, self.snmp_trap_switch_config_str())
        else:
            return "<ok/>"


def snmp_trap_switch_config(argument_spec):
    """ snmp_trap_switch_config """

    required_together = [("trap_name", "trap_feature_name")]
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        supports_check_mode=True
    )

    snmp_trap_switch_obj = SnmpTrapSwitch(argument_spec)

    if not snmp_trap_switch_obj:
        module.fail_json(msg='Error: Init snmp trap switch module failed.')

    return snmp_trap_switch_obj.set_snmp_trap_switch()


def main():
    """ main function """

    argument_spec = dict(
        operation=dict(choices=['create', 'delete'], default='create')
    )

    argument_spec.update(ne_argument_spec)
    argument_spec.update(snmp_base_argument_spec)
    argument_spec.update(snmp_trap_tgt_argument_spec)
    argument_spec.update(snmp_trap_enalbe_spec)
    argument_spec.update(snmp_trap_switch_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    results = dict()
    result = snmp_enable_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    result = snmp_version_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    result = snmp_trap_tgt_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    result = snmp_trap_enable_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    result = snmp_trap_switch_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    results['response'] = "ok"
    results['changed'] = True
    module.exit_json(**results)


if __name__ == '__main__':
    main()
