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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'snmp'}

DOCUMENTATION = '''
---
module: snmp_base
version_added: "2.6"
short_description: Manages SNMP switch,version, engineID, acl and MIB View's configuration on HUAWEI router.
description:
    - Manages SNMP switch,version, engineID, acl and MIB View's configuration on HUAWEI router.
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
    engineID:
        description:
            - Engine ID.
        required: false
        default: null
    snmp_acl:
        description:
            - SNMP global acl.
        required: false
        default: null
    view_name:
        description:
            - SNMP mib view's name.
        required: true
        default: null
    view_type:
        description:
            - SNMP mib view's type.
        required: true
        default: null
        choices: ['excluded', 'included']
    subtree:
        description:
            - SNMP mib view's subtree.
        required: true
        default: null
'''

EXAMPLES = '''

- name: snmp base configuration test
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
    snmp_base:
      operation: create
      snmp_enable: true

  - name: "Disable SNMP"
    snmp_base:
      operation: delete
      snmp_enable: true

  - name: "Config SNMP version"
    snmp_base:
      operation: create
      snmp_version: ['v1', 'v2c','v3','all']

  - name: "Cancel config SNMP version"
    snmp_base:
      operation: delete
      snmp_version: ['v1', 'v2c','v3','all']

  - name: "Config SNMP mib view"
    snmp_base:
      operation: create
      view_name: abc
      view_type: included
      subtree:   iso

  - name: "Cancel config SNMP mibview"
    snmp_base:
      operation: delete
      view_name: abc
      subtree:   iso

  - name: "Config SNMP engine id"
    snmp_base:
      operation: create
      engineID:  800007XX0338XXXX2BCA01

  - name: "Cancel config SNMP engine id"
    snmp_base:
      operation: delete
      engineID:  800007XX0338XXXX2BCA01

  - name: "Config SNMP acl"
    snmp_base:
      operation: create
      snmp_acl:  2000

  - name: "Cancel config SNMP acl"
    snmp_base:
      operation: delete
      snmp_acl:  2000
'''

RETURN = '''
response:
    description: check to see config result
    returned: always
    type: result string
    sample: ok
'''


SNMP_ENABLE_CFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <agentCfg>
"""

SNMP_ENABLE_CONF_TAIL = """
        </agentCfg>
    </snmp>
</config>
"""

SNMP_ENGINE_CFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <engine>
"""

SNMP_ENGINE_CONF_TAIL = """
        </engine>
    </snmp>
</config>
"""

SNMP_MIBVIEW_CFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <mibViews>
        <mibView>
"""

SNMP_MIBVIEW_CONF_TAIL = """
            </mibView>
        </mibViews>
    </snmp>
</config>
"""

SNMP_MIBVIEW_DELCFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <mibViews>
        <mibView nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SNMPENALBE = """
      <agentEnable>%s</agentEnable>"""

SNMPENALBE_DEL = """
      <agentEnable nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</agentEnable>"""

SNMPVERSION = """
      <version>%s</version>"""

SNMPVERSION_DEL = """
      <version nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</version>"""

SNMPENGINE_ID = """
      <engineID>%s</engineID>"""

SNMPENGINE_ID_DEL = """
      <engineID nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</engineID>"""

SNMP_VIEW_NAME = """
      <viewName>%s</viewName>"""

SNMP_MIBVIEW_DEL = """
      <viewName nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</viewName>"""

SNMP_VIEW_SUBTREE = """
      <subtree>%s</subtree>"""

SNMP_VIEW_TYPE = """
      <type>%s</type>"""

SNMP_ACL_CFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <systemCfg>
"""

SNMP_ACL_CONF_TAIL = """
        </systemCfg>
    </snmp>
</config>
"""

SNMP_ACL_DEL = """
      <acl nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">%s</acl>"""

SNMP_ACL = """
      <acl>%s</acl>"""

snmp_base_argument_spec = {
    'snmp_enable': dict(choices=['true', 'false']),
    'snmp_version': dict(choices=['v1', 'v2c', 'v3', 'all']),
    'engineID': dict(type='str'),
    'snmp_acl': dict(type='int')
}

snmp_mibView_argument_spec = {
    'view_name': dict(type='str'),
    'view_type': dict(choices=['excluded', 'included']),
    'subtree': dict(type='str')
}


def config_params_func(arg):
    if arg or arg == '':
        return True
    return False


class SnmpEnable(object):
    """
     Manages SNMP enalbe configuration
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=False)
        self.operation = self.module.params['operation']
        self.snmp_enable = self.module.params['snmp_enable']
        self.results = dict()
        self.results['response'] = []

    def snmp_enable_config_str(self):
        snmp_enable_cfg_str = ''
        snmp_enable_cfg_str += SNMP_ENABLE_CFG_HEAD

        if self.operation == 'create':
            if config_params_func(self.snmp_enable):
                snmp_enable_cfg_str += SNMPENALBE % self.snmp_enable

        if self.operation == 'delete':
            if config_params_func(self.snmp_enable):
                snmp_enable_cfg_str += SNMPENALBE_DEL % self.snmp_enable

        snmp_enable_cfg_str += SNMP_ENABLE_CONF_TAIL
        return snmp_enable_cfg_str

    def set_snmp_enable(self):
        if config_params_func(self.snmp_enable):
            recv_xml = set_nc_config(
                self.module, self.snmp_enable_config_str())
            if self.operation == 'delete':
                if "<ok/>" in recv_xml:
                    self.module.exit_json(
                        msg='Info: SNMP agent is not enabled.')
            return recv_xml
        else:
            return "<ok/>"


def snmp_enable_config(argument_spec):
    """ snmp_enable_config """

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    snmp_enable_obj = SnmpEnable(argument_spec)
    if not snmp_enable_obj:
        module.fail_json(msg='Error: Init enable module failed.')

    return snmp_enable_obj.set_snmp_enable()


class SnmpVersion(object):
    """
     Manages SNMP version configuration
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=False)
        self.operation = self.module.params['operation']
        self.snmp_version = self.module.params['snmp_version']
        self.results = dict()
        self.results['response'] = []

    def snmp_version_config_str(self):
        snmp_cfg_str = ''
        snmp_cfg_str += SNMP_ENGINE_CFG_HEAD

        if self.operation == 'create':
            if config_params_func(self.snmp_version):
                snmp_cfg_str += SNMPVERSION % self.snmp_version

        if self.operation == 'delete':
            if config_params_func(self.snmp_version):
                snmp_cfg_str += SNMPVERSION_DEL % self.snmp_version

        snmp_cfg_str += SNMP_ENGINE_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_version(self):
        if config_params_func(self.snmp_version):
            return set_nc_config(self.module, self.snmp_version_config_str())
        else:
            return "<ok/>"


def snmp_version_config(argument_spec):
    """ snmp_version_config """

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    snmp_version_obj = SnmpVersion(argument_spec)

    if not snmp_version_obj:
        module.fail_json(msg='Error: Init version module failed.')

    return snmp_version_obj.set_snmp_version()


class SnmpEngineID(object):
    """
     Manages SnmpEngineID configuration
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=False)
        self.operation = self.module.params['operation']
        self.snmp_engineID = self.module.params['engineID']
        self.results = dict()
        self.results['response'] = []

    def snmp_engineID_config_str(self):
        snmp_cfg_str = ''
        snmp_cfg_str += SNMP_ENGINE_CFG_HEAD

        if self.operation == 'create':
            if config_params_func(self.snmp_engineID):
                snmp_cfg_str += SNMPENGINE_ID % self.snmp_engineID

        if self.operation == 'delete':
            if config_params_func(self.snmp_engineID):
                snmp_cfg_str += SNMPENGINE_ID_DEL % self.snmp_engineID

        snmp_cfg_str += SNMP_ENGINE_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_engineID(self):
        if config_params_func(self.snmp_engineID):
            return set_nc_config(self.module, self.snmp_engineID_config_str())
        else:
            return "<ok/>"


def snmp_engineID_config(argument_spec):
    """ snmp_engineID_config """

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    snmp_engineID_obj = SnmpEngineID(argument_spec)

    if not snmp_engineID_obj:
        module.fail_json(msg='Error: Init engineID module failed.')

    return snmp_engineID_obj.set_snmp_engineID()


class SnmpMibView(object):
    """
     Manages SnmpMibView configuration
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.view_name = self.module.params['view_name']
        self.view_type = self.module.params['view_type']
        self.subtree = self.module.params['subtree']
        self.results = dict()
        self.results['response'] = []

    def snmp_mibview_config_str(self):
        snmp_cfg_str = ''

        if self.operation == 'create':
            snmp_cfg_str += SNMP_MIBVIEW_CFG_HEAD
            if config_params_func(self.view_name):
                snmp_cfg_str += SNMP_VIEW_NAME % self.view_name

            if config_params_func(self.view_type):
                snmp_cfg_str += SNMP_VIEW_TYPE % self.view_type

            if config_params_func(self.subtree):
                snmp_cfg_str += SNMP_VIEW_SUBTREE % self.subtree

        if self.operation == 'delete':
            snmp_cfg_str += SNMP_MIBVIEW_DELCFG_HEAD
            if config_params_func(self.view_name):
                snmp_cfg_str += SNMP_VIEW_NAME % self.view_name

            if config_params_func(self.subtree):
                snmp_cfg_str += SNMP_VIEW_SUBTREE % self.subtree

        snmp_cfg_str += SNMP_MIBVIEW_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_mibview(self):
        if config_params_func(self.view_name):
            if config_params_func(self.subtree):
                return set_nc_config(
                    self.module, self.snmp_mibview_config_str())
            else:
                return "Mib view's config is error"
        else:
            return "<ok/>"


def snmp_mibview_config(argument_spec):
    """ snmp_mibview_config """

    required_together = [("view_name", "view_type", "subtree")]
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        supports_check_mode=True
    )

    snmp_mibview_obj = SnmpMibView(argument_spec)

    if not snmp_mibview_obj:
        module.fail_json(msg='Error: Init mibview module failed.')

    return snmp_mibview_obj.set_snmp_mibview()


class SnmpAcl(object):
    """
     Manages global SNMP Acl configuration
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=False)
        self.operation = self.module.params['operation']
        self.snmp_acl = self.module.params['snmp_acl']
        self.results = dict()
        self.results['response'] = []

    def snmp_acl_config_str(self):
        snmp_cfg_str = ''
        snmp_cfg_str += SNMP_ACL_CFG_HEAD

        if self.operation == 'create':
            if config_params_func(self.snmp_acl):
                snmp_cfg_str += SNMP_ACL % self.snmp_acl

        if self.operation == 'delete':
            if config_params_func(self.snmp_acl):
                snmp_cfg_str += SNMP_ACL_DEL % self.snmp_acl

        snmp_cfg_str += SNMP_ACL_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_acl(self):
        if config_params_func(self.snmp_acl):
            return set_nc_config(self.module, self.snmp_acl_config_str())
        else:
            return "<ok/>"


def snmp_acl_config(argument_spec):
    """ snmp_acl_config """

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    snmp_acl_obj = SnmpAcl(argument_spec)
    if not snmp_acl_obj:
        module.fail_json(msg='Error: Init snmp acl module failed.')

    return snmp_acl_obj.set_snmp_acl()


def main():
    """ main function """

    argument_spec = dict(
        operation=dict(choices=['create', 'delete'], default='create')
    )

    argument_spec.update(ne_argument_spec)
    argument_spec.update(snmp_base_argument_spec)
    argument_spec.update(snmp_mibView_argument_spec)

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

    result = snmp_engineID_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    result = snmp_acl_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    result = snmp_mibview_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    results['response'] = "ok"
    results['changed'] = True
    module.exit_json(**results)


if __name__ == '__main__':
    main()
