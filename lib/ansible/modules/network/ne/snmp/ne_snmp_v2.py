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

from ansible.modules.network.ne.snmp.ne_snmp_base import config_params_func, snmp_base_argument_spec, snmp_mibView_argument_spec
from ansible.modules.network.ne.snmp.ne_snmp_base import snmp_enable_config, snmp_version_config, snmp_engineID_config, snmp_acl_config, snmp_mibview_config
from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'snmp'}

DOCUMENTATION = '''
---
module: ne_snmp_v2
version_added: "2.6"
short_description: Manages SNMP v2c configuration on HUAWEI router.
description:
    - Manages SNMP v2c configuration on HUAWEI router.SNMP v2c connect configurations include snmp version, acl, mibviews and communitys configuration.
author:Zhaweiwei(@netengine-Ansible)

options:
    operation:
        description:
            - Ansible operation.
        required: yes
        default: null
        choices: ['create', 'delete']
    snmp_enable:
        description:
            - Enable or disable SNMP.
        required: yes
        default: null
        choices: ['true', 'false']
    snmp_version:
        description:
            - SNMP version.
        required: yes
        default: null
        choices: ['v1', 'v2c','v3','all']
    engineID:
        description:
            - Engine ID.
        required: no
        default: null
    snmp_acl:
        description:
            - SNMP global acl.
        required: no
        default: null
    view_name:
        description:
            - SNMP mib view name.
        required: yes
        default: null
    view_type:
        description:
            - SNMP mib view type.
        required: yes
        default: null
        choices: ['excluded', 'included']
    subtree:
        description:
            - SNMP mib view subtree.
        required: yes
        default: null
    community_name:
        description:
            - SNMP community name.
        required: yes
        default: null
    access_right:
        description:
            - SNMP community access right.
        required: yes
        default: null
        choices: ['read', 'write']
   community_mib_view:
        description:
            - SNMP community mib view name.
        required: default
        default: null
   acl_number:
        description:
            - ACL number related by SNMP community.
        required: no
        default: null
'''

EXAMPLES = '''

- name: snmp v2 connect test
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
    ne_snmp_v2:
      operation: create
      snmp_enable: true

  - name: "Disable SNMP"
    ne_snmp_v2:
      operation: delete
      snmp_enable: true

  - name: "Enalbe SNMP v2c version"
    ne_snmp_v2:
      operation: create
      snmp_version: v2c

  - name: "Cancel config SNMP v2c version"
    ne_snmp_v2:
      operation: delete
      snmp_version: v2c

  - name: "Config SNMP global acl"
    ne_snmp_base:
      operation: create
      snmp_acl:  2000

  - name: "Cancel config SNMP global acl"
    ne_ne_snmp_base:
      operation: delete
      snmp_acl:  2000

  - name: "Config SNMP mib view"
    ne_snmp_v2:
      operation: create
      view_name: abc
      view_type: included
      subtree:   iso

  - name: "Cancel config SNMP mibview"
    ne_snmp_v2:
      operation: delete
      view_name: abc
      subtree:   iso

  - name: "Config SNMP community"
    ne_snmp_v2:
      operation: create
      community_name:  abcd@1236
      access_right: read
      community_mib_view: abc

  - name: "Cancel config SNMP community"
    ne_snmp_v2:
      operation: delete
      community_name:  abcd@1236
      access_right: read
      community_mib_view: abc
'''


RETURN = '''
response:
    description: check to see config result
    returned: always
    type: result string
    sample: ok
'''


SNMP_COMMUNITY_CFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <communitys>
        <community>
"""

SNMP_COMMUNITY_CONF_TAIL = """
            </community>
        </communitys>
    </snmp>
</config>
"""

SNMP_COMMUNITY_DELCFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <communitys>
        <community nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SNMP_COMMUNITY_NAME = """
    <communityName>%s</communityName>"""

SNMP_COMMUNITY_ACCESS_RIGHT = """
    <accessRight>%s</accessRight>"""

SNMP_COMMUNITY_VIEW_NAME = """
    <mibViewName>%s</mibViewName>"""

SNMP_COMMUNITY_ACL_NUMBER = """
    <aclNumber>%s</aclNumber>"""

snmp_community_argument_spec = {
    'community_name': dict(type='str'),
    'access_right': dict(choices=['read', 'write']),
    'community_mib_view': dict(type='str'),
    'acl_number': dict(type='int')
}


class SnmpCommunity(object):
    """
     SnmpCommunity
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.community_name = self.module.params['community_name']
        self.access_right = self.module.params['access_right']
        self.community_mib_view = self.module.params['community_mib_view']
        self.acl_number = self.module.params['acl_number']
        self.results = dict()
        self.results['response'] = []

    def snmp_community_config_str(self):
        snmp_cfg_str = ''

        if self.operation == 'create':
            snmp_cfg_str += SNMP_COMMUNITY_CFG_HEAD
            if config_params_func(self.community_name):
                snmp_cfg_str += SNMP_COMMUNITY_NAME % self.community_name

            if config_params_func(self.access_right):
                snmp_cfg_str += SNMP_COMMUNITY_ACCESS_RIGHT % self.access_right

            if config_params_func(self.community_mib_view):
                snmp_cfg_str += SNMP_COMMUNITY_VIEW_NAME % self.community_mib_view

            if config_params_func(self.acl_number):
                snmp_cfg_str += SNMP_COMMUNITY_ACL_NUMBER % self.acl_number

        if self.operation == 'delete':
            snmp_cfg_str += SNMP_COMMUNITY_DELCFG_HEAD
            if config_params_func(self.community_name):
                snmp_cfg_str += SNMP_COMMUNITY_NAME % self.community_name

            if config_params_func(self.access_right):
                snmp_cfg_str += SNMP_COMMUNITY_ACCESS_RIGHT % self.access_right

        snmp_cfg_str += SNMP_COMMUNITY_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_community(self):
        if config_params_func(self.community_name):
            if config_params_func(self.access_right):
                return set_nc_config(
                    self.module, self.snmp_community_config_str())
            else:
                return "Snmp community's config is error"
        else:
            return "<ok/>"


def snmp_community_config(argument_spec):
    """ snmp_community_config """

    required_together = [("community_name", "access_right")]
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        supports_check_mode=True
    )

    snmp_community_obj = SnmpCommunity(argument_spec)

    if not snmp_community_obj:
        module.fail_json(msg='Error: Init community module failed.')

    return snmp_community_obj.set_snmp_community()


def main():
    """ main function """

    argument_spec = dict(
        operation=dict(choices=['create', 'delete'], default='create')
    )

    argument_spec.update(ne_argument_spec)
    argument_spec.update(snmp_base_argument_spec)
    argument_spec.update(snmp_mibView_argument_spec)
    argument_spec.update(snmp_community_argument_spec)

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

    result = snmp_community_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    results['response'] = "ok"
    results['changed'] = True
    module.exit_json(**results)


if __name__ == '__main__':
    main()
