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
module: ne_snmp_v3
version_added: "2.6"
short_description: Manages SNMP v3 configuration on HUAWEI router.
description:
    - Manages SNMP v3 configuration on HUAWEI router.SNMP v3connect configurations include snmp version, mibviews, user and usergroup's configuration.
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
            - SNMP mib view's name.
        required: yes
        default: null
    view_type:
        description:
            - SNMP mib view's type.
        required: yes
        default: null
        choices: ['excluded', 'included']
    subtree:
        description:
            - SNMP mib view's subtree.
        required: yes
        default: null
    group_name:
        description:
            - SNMP v3 group name.
        required: yes
        default: null
    security_level:
        description:
            - Security level indicating whether to use authentication and encryption.
        required: yes
        default: null
        choices: ['noAuthNoPriv', 'authentication', 'privacy']
    read_view_name:
        description:
            - Mib view name for read.
        required: no
        default: ViewDefault
    write_view_name:
        description:
            - Mib view name for write.
        required: no
        default: ViewDefault
    notify_view_name:
        description:
            - Mib view name for notify.
        required: no
        default: ViewDefault
    group_acl_number:
        description:
            - ACL number related by SNMP group.
        required: no
        default: null
    snmp_user_name:
        description:
            - Unique name to identify the USM user.
        required: yes
        default: null
    is_remote_engine_id:
        description:
            - Is remote engine id.
        required: yes
        default: null
        choices: ['true', 'false']
    user_engineID:
        description:
            - Engine ID of the USM user.
        required: yes
        default: null
    user_group_name:
        description:
            -Name of the group where user belongs to.
        required: yes
        default: null
    auth_protocol:
        description:
            -Authentication protocol ( md5 | sha ).
        required: yes
        default: null
        choices: ['md5', 'sha']
    auth_key:
        description:
            -The Authentication Password.
        required: yes
        default: null
    priv_protocol:
        description:
            -Encryption Protocol.
        required: yes
        default: null
        choices: ['3des168', 'aes128', 'aes192', 'aes256', 'des56']
    priv_key:
        description:
            -The Encryption Password.
        required: yes
        default: null
    user_acl_number:
        description:
            -Acl number related by snmp user.
        required: no
        default: null
'''

EXAMPLES = '''

- name: snmp v3 connect test
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
    ne_snmp_v3:
      operation: create
      snmp_enable: true

  - name: "Disable SNMP"
    ne_snmp_v3:
      operation: delete
      snmp_enable: true

 - name: "Config SNMP global acl"
    ne_snmp_base:
      operation: create
      snmp_acl:  2000

  - name: "Cancel config SNMP global acl"
    ne_snmp_base:
      operation: delete
      snmp_acl:  2000

  - name: "Enalbe SNMP v3 version"
    ne_snmp_v3:
      operation: create
      snmp_version: v3

  - name: "Cancel config SNMP v3 version"
    ne_snmp_v3:
      operation: delete
      snmp_version: v3

  - name: "Config SNMP mib view"
    ne_snmp_v3:
      operation: create
      view_name: abc
      view_type: included
      subtree:   iso

  - name: "Cancel config SNMP mibview"
    ne_snmp_v3:
      operation: delete
      view_name: abc
      subtree:   iso

  - name: "Config SNMP v3 group"
    ne_snmp_v3:
      operation: create
      group_name:  test
      security_level: privacy
      read_view_name: abc
      write_view_name: abc
      notify_view_name: abc

  - name: "Cancel config SNMP v3 group"
    ne_snmp_v3:
      operation: delete
      group_name:  test
      security_level: privacy
      read_view_name: abc
      write_view_name: abc
      notify_view_name: abc

    - name: "Config SNMP usm user"
    ne_snmp_v3:
      operation: create
      snmp_user_name:  test
      is_remote_engine_id: false
      user_engineID: 800007XX0338XXXX2BCA01
      user_group_name: test
      auth_protocol: md5
      auth_key: abcd@1236
      priv_protocol: des56
      priv_key: abcd@1256

  - name: "Cancel config SNMP usm user"
    ne_snmp_v3:
      operation: delete
      snmp_user_name:  test
      is_remote_engine_id: false
      user_engineID: 800007XX0338XXXX2BCA01
      user_group_name: test
      auth_protocol: md5
      auth_key: abcd@1236
      priv_protocol: des56
      priv_key: abcd@1256
'''

RETURN = '''
response:
    description: check to see config result
    returned: always
    type: result string
    sample: ok
'''


SNMP_USERGROUP_CFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <snmpv3Groups>
        <snmpv3Group>
"""

SNMP_USERGROUP_CONF_TAIL = """
            </snmpv3Group>
        </snmpv3Groups>
    </snmp>
</config>
"""

SNMP_USERGROUP_DELCFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <snmpv3Groups>
        <snmpv3Group nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SNMP_USERGROUP_NAME = """
    <groupName>%s</groupName>"""

SNMP_SECURITY_LEVEL = """
    <securityLevel>%s</securityLevel>"""

SNMP_USERGROUP_READVIEW_NAME = """
    <readViewName>%s</readViewName>"""

SNMP_USERGROUP_WRITEVIEW_NAME = """
    <writeViewName>%s</writeViewName>"""

SNMP_USERGROUP_NOTIFYVIEW_NAME = """
    <notifyViewName>%s</notifyViewName>"""

SNMP_USERGROUP_ACLNUM = """
    <aclNumber>%s</aclNumber>"""

SNMP_USER_CFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <usmUsers>
        <usmUser>
"""

SNMP_USER_CONF_TAIL = """
            </usmUser>
        </usmUsers>
    </snmp>
</config>
"""

SNMP_USER_DELCFG_HEAD = """
<config>
    <snmp xmlns="http://www.huawei.com/netconf/vrp/huawei-snmp">
        <usmUsers>
        <usmUser nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SNMP_USER_NAME = """
    <userName>%s</userName>"""

SNMP_USER_GROUP_NAME = """
    <groupName>%s</groupName>"""

SNMP_USER_AUTH_PROTOCOL = """
    <authProtocol>%s</authProtocol>"""

SNMP_USER_AUTHKEY = """
    <authKey>%s</authKey>"""

SNMP_USER_PRIV_PROTOCOL = """
    <privProtocol>%s</privProtocol>"""

SNMP_USER_PRIVKEY = """
    <privKey>%s</privKey>"""

SNMP_USER_REMOTE_ENGINEID = """
    <remoteEngineID>%s</remoteEngineID>"""

SNMP_USER_ENGINEID = """
    <engineID>%s</engineID>"""

SNMP_USER_ACLNUM = """
    <aclNumber>%s</aclNumber>"""

snmp_user_group_argument_spec = {
    'group_name': dict(type='str'),
    'security_level': dict(choices=['noAuthNoPriv', 'authentication', 'privacy']),
    'read_view_name': dict(type='str'),
    'write_view_name': dict(type='str'),
    'notify_view_name': dict(type='str'),
    'group_acl_number': dict(type='int')
}

snmp_user_argument_spec = {
    'snmp_user_name': dict(type='str'),
    'is_remote_engine_id': dict(choices=['true', 'false']),
    'user_engineID': dict(type='str'),
    'user_group_name': dict(type='str'),
    'auth_protocol': dict(choices=['md5', 'sha']),
    'auth_key': dict(type='str'),
    'priv_protocol': dict(choices=['3des168', 'aes128', 'aes192', 'aes256', 'des56']),
    'priv_key': dict(type='str'),
    'user_acl_number': dict(type='int')
}


class SnmpV3Group(object):
    """
     SnmpV3Group
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.group_name = self.module.params['group_name']
        self.security_level = self.module.params['security_level']
        self.read_view_name = self.module.params['read_view_name']
        self.write_view_name = self.module.params['write_view_name']
        self.notify_view_name = self.module.params['notify_view_name']
        self.group_acl_number = self.module.params['group_acl_number']
        self.results = dict()
        self.results['response'] = []

    def snmp_v3group_config_str(self):
        snmp_cfg_str = ''

        if self.operation == 'create':
            snmp_cfg_str += SNMP_USERGROUP_CFG_HEAD
            if config_params_func(self.group_name):
                snmp_cfg_str += SNMP_USERGROUP_NAME % self.group_name

            if config_params_func(self.security_level):
                snmp_cfg_str += SNMP_SECURITY_LEVEL % self.security_level

            if config_params_func(self.read_view_name):
                snmp_cfg_str += SNMP_USERGROUP_READVIEW_NAME % self.read_view_name

            if config_params_func(self.write_view_name):
                snmp_cfg_str += SNMP_USERGROUP_WRITEVIEW_NAME % self.write_view_name

            if config_params_func(self.notify_view_name):
                snmp_cfg_str += SNMP_USERGROUP_NOTIFYVIEW_NAME % self.notify_view_name

            if config_params_func(self.group_acl_number):
                snmp_cfg_str += SNMP_USERGROUP_ACLNUM % self.group_acl_number

        if self.operation == 'delete':
            snmp_cfg_str += SNMP_USERGROUP_DELCFG_HEAD
            if config_params_func(self.group_name):
                snmp_cfg_str += SNMP_USERGROUP_NAME % self.group_name

            if config_params_func(self.security_level):
                snmp_cfg_str += SNMP_SECURITY_LEVEL % self.security_level

        snmp_cfg_str += SNMP_USERGROUP_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_user_group(self):
        if config_params_func(self.group_name):
            if config_params_func(self.security_level):
                return set_nc_config(
                    self.module, self.snmp_v3group_config_str())
            else:
                return "Snmp user group's config is error"
        else:
            return "<ok/>"


def snmp_user_group_config(argument_spec):
    """ snmp_user_group_config """

    required_together = [("group_name", "security_level")]
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        supports_check_mode=True
    )

    snmp_usergroup_obj = SnmpV3Group(argument_spec)

    if not snmp_usergroup_obj:
        module.fail_json(msg='Error: Init v3 group module failed.')

    return snmp_usergroup_obj.set_snmp_user_group()


class SnmpV3User(object):
    """
     SnmpV3User
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.snmp_user_name = self.module.params['snmp_user_name']
        self.is_remote_engine_id = self.module.params['is_remote_engine_id']
        self.user_engineID = self.module.params['user_engineID']
        self.user_group_name = self.module.params['user_group_name']
        self.auth_protocol = self.module.params['auth_protocol']
        self.auth_key = self.module.params['auth_key']
        self.priv_protocol = self.module.params['priv_protocol']
        self.priv_key = self.module.params['priv_key']
        self.user_acl_number = self.module.params['user_acl_number']
        self.results = dict()
        self.results['response'] = []

    def snmp_v3user_config_str(self):
        snmp_cfg_str = ''

        if self.operation == 'create':
            snmp_cfg_str += SNMP_USER_CFG_HEAD
            if config_params_func(self.snmp_user_name):
                snmp_cfg_str += SNMP_USER_NAME % self.snmp_user_name

            if config_params_func(self.is_remote_engine_id):
                snmp_cfg_str += SNMP_USER_REMOTE_ENGINEID % self.is_remote_engine_id

            if config_params_func(self.user_engineID):
                snmp_cfg_str += SNMP_USER_ENGINEID % self.user_engineID

            if config_params_func(self.user_group_name):
                snmp_cfg_str += SNMP_USER_GROUP_NAME % self.user_group_name

            if config_params_func(self.auth_protocol):
                snmp_cfg_str += SNMP_USER_AUTH_PROTOCOL % self.auth_protocol

            if config_params_func(self.auth_key):
                snmp_cfg_str += SNMP_USER_AUTHKEY % self.auth_key

            if config_params_func(self.priv_protocol):
                snmp_cfg_str += SNMP_USER_PRIV_PROTOCOL % self.priv_protocol

            if config_params_func(self.priv_key):
                snmp_cfg_str += SNMP_USER_PRIVKEY % self.priv_key

            if config_params_func(self.user_acl_number):
                snmp_cfg_str += SNMP_USER_ACLNUM % self.user_acl_number

        if self.operation == 'delete':
            snmp_cfg_str += SNMP_USER_DELCFG_HEAD
            if config_params_func(self.snmp_user_name):
                snmp_cfg_str += SNMP_USER_NAME % self.snmp_user_name

            if config_params_func(self.is_remote_engine_id):
                snmp_cfg_str += SNMP_USER_REMOTE_ENGINEID % self.is_remote_engine_id

            if config_params_func(self.user_engineID):
                snmp_cfg_str += SNMP_USER_ENGINEID % self.user_engineID

        snmp_cfg_str += SNMP_USER_CONF_TAIL
        return snmp_cfg_str

    def set_snmp_user(self):
        if config_params_func(self.snmp_user_name):
            return set_nc_config(self.module, self.snmp_v3user_config_str())
        else:
            return "<ok/>"


def snmp_user_config(argument_spec):
    """ snmp_user_config """

    required_together = [
        ("snmp_user_name",
         "is_remote_engine_id",
         "user_engineID")]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        supports_check_mode=True
    )

    snmp_user_obj = SnmpV3User(argument_spec)

    if not snmp_user_obj:
        module.fail_json(msg='Error: Init v3 user module failed.')

    return snmp_user_obj.set_snmp_user()


def main():
    """ main function """

    argument_spec = dict(
        operation=dict(choices=['create', 'delete'], default='create')
    )

    argument_spec.update(ne_argument_spec)
    argument_spec.update(snmp_base_argument_spec)
    argument_spec.update(snmp_mibView_argument_spec)
    argument_spec.update(snmp_user_group_argument_spec)
    argument_spec.update(snmp_user_argument_spec)

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

    result = snmp_user_group_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    result = snmp_user_config(argument_spec)
    if "<ok/>" not in result:
        results['response'] = result
        results['changed'] = False
        module.exit_json(**results)

    results['response'] = "ok"
    results['changed'] = True
    module.exit_json(**results)


if __name__ == '__main__':
    main()
