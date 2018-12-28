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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, ne_argument_spec
from ansible.module_utils.basic import AnsibleModule
import re
DOCUMENTATION = '''
---
module: netconfc_connection_config
version_added: "2.6"
description:
    - Set the NETCONF connection for remote.
author: Wangqijun (@netengine-Ansible)

options:
    operation:
        description:
            - Ansible operation.
        required: true
        default: null
        choices: ['create', 'delete', 'get']
    groupType:
        description:
            - Type of the authorization.
        required: true
        default: null
        choices: ['taskgroup','usergroup']
    taskGroupName:
        description:
            - Task group name of the authorization.
        required: true
        default: null
    userGroupName:
        description:
            - User group name of the authorization.
        required: true
        default: null
    ruleName:
        description:
            - Name of the rule.
        required: true
        default: null
    ruleType:
        description:
            - Type of the rule.
        required: true
        default: null
        choices: ['operationRule','datanodeRule']
    action:
        description:
            - Action of the rule.
        required: false
        default: null
        choices: ['permit','deny']
    rpcOperName:
        description:
            - Name of the rpc operation.
        required: false
        default: null
        choices: ['get', 'get-config', 'edit-config', 'lock',
                  'unlock', 'kill-session', 'copy-config',
                  'delete-config', 'discard-changes', 'commit',
                  'get-next', 'discard-commit', 'sync-full',
                  'sync-increment', 'execute-action', 'execute-cli',
                  'update', 'create-subscription', 'rpc']
    read:
        description:
            - Access right of the data node.
        required: false
        default: disable
        choices: ['enable','disable']
    write:
        description:
            - Access right of the data node
        required: false
        default: disable
        choices: ['enable','disable']
    execute:
        description:
            - Access right of the data node.
        required: false
        default: disable
        choices: ['enable','disable']
    description:
        description:
            - Description of the rule.
        required: false
        default: null
'''

EXAMPLES = '''

- name: netconf maxsessons timeout capability
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    yang:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      operation: create or delete or get

  tasks:

  - name: "Create usergroup with ruletype operationRule"
    netconf_authorization:
      operation: create
      groupType: 'usergroup'
      userGroupName: 'Netconfusergroup'
      ruleName: 'rulename'
      ruleType: 'operationRule'
      action: 'permit'
      rpcOperName: 'get'
      description: 'Netconfrulename'

  - name: "Create usergroup with ruletype datanodeRule"
    netconf_authorization:
      operation: 'create'
      groupType: 'usergroup'
      userGroupName: 'Netconfusergroup'
      ruleName: 'rulename2'
      ruleType: 'datanodeRule'
      action: 'deny'
      dataNodePath: '/netconf/netconfCapabilitys/netconfCapability'
      description: 'Netconfrulename2'

  - name: "Create usergroup with ruletype datanodeRule and action permit"
    netconf_authorization:
      operation: 'create'
      groupType: 'usergroup'
      userGroupName: 'Netconfusergroup'
      ruleName: 'rulename3'
      ruleType: 'datanodeRule'
      action: 'permit'
      dataNodePath: '/netconf/netconfCapabilitys/netconfCapability'
      read: 'enable'
      write: 'disable'
      execute: 'disable'
      description: 'Netconfrulename3'

  - name: "get usergroup with userGroupName ruleName and ruleType"
    netconf_authorization:
      operation: 'get'
      groupType: 'usergroup'
      userGroupName: 'Netconfusergroup'
      ruleName: 'rulename3'
      ruleType: 'datanodeRule'

  - name: "delete usergroup with userGroupName ruleName and ruleType"
    netconf_authorization:
      operation: 'delete'
      groupType: 'usergroup'
      userGroupName: 'Netconfusergroup'
      ruleName: 'rulename3'
      ruleType: 'datanodeRule'

  - name: "Create taskgroup with ruletype operationRule"
    netconf_authorization:
      operation: create
      groupType: 'taskgroup'
      userGroupName: 'Netconftaskgroup'
      ruleName: 'rulename1'
      ruleType: 'operationRule'
      action: 'permit'
      rpcOperName: 'get'
      description: 'Netconfrulename'

  - name: "Create taskgroup with ruletype datanodeRule and action permit"
    netconf_authorization:
      operation: 'create'
      groupType: 'taskgroup'
      userGroupName: 'Netconftaskgroup'
      ruleName: 'rulename2'
      ruleType: 'datanodeRule'
      action: 'permit'
      dataNodePath: '/netconf/netconfCapabilitys/netconfCapability'
      read: 'enable'
      write: 'disable'
      execute: 'disable'
      description: 'Netconfrulename2'

  - name: "get usergroup with userGroupName ruleName and ruleType"
    netconf_authorization:
      operation: 'get'
      groupType: 'taskgroup'
      userGroupName: 'Netconftaskgroup'
      ruleName: 'rulename1'
      ruleType: 'operationRule'

  - name: "delete usergroup with userGroupName ruleName and ruleType"
    netconf_authorization:
      operation: 'delete'
      groupType: 'taskgroup'
      userGroupName: 'Netconftaskgroup'
      ruleName: 'rulename1'
      ruleType: 'operationRule'
'''


netconf_authorization_spec = {
    'groupType': dict(choices=['taskgroup', 'usergroup']),
    'taskGroupName': dict(type='str'),
    'userGroupName': dict(type='str'),
    'ruleName': dict(type='str'),
    'ruleType': dict(choices=['operationRule', 'datanodeRule']),
    'action': dict(choices=['permit', 'deny']),
    'rpcOperName': dict(choices=['get', 'get-config', 'edit-config', 'lock', 'unlock', 'kill-session',
                                  'copy-config', 'delete-config', 'discard-changes', 'commit', 'get-next', 'discard-commit', 'sync-full',
                                  'sync-increment', 'execute-action', 'execute-cli', 'update', 'create-subscription', 'rpc']),
    'dataNodePath': dict(type='str'),
    'read': dict(choices=['enable', 'disable']),
    'write': dict(choices=['enable', 'disable']),
    'execute': dict(choices=['enable', 'disable']),
    'description': dict(type='str')
}

GET_AUTHORIZATION_USERGROUP_CONFIG_HEAD = """
<filter type="subtree">
  <netconf xmlns="http://www.huawei.com/netconf/vrp/huawei-netconf">
    <authorization>
      <userGroupRules>
        <userGroupRule>
"""

GET_AUTHORIZATION_USERGROUP_CONFIG_TAIL = """
        </userGroupRule>
      </userGroupRules>
    </authorization>
  </netconf>
</filter>
"""

SET_AUTHORIZATION_USERGROUP_CONFIG_HEAD = """
<config>
  <netconf xmlns="http://www.huawei.com/netconf/vrp/huawei-netconf">
    <authorization>
      <userGroupRules>
        <userGroupRule>
"""

SET_AUTHORIZATION_USERGROUP_CONFIG_HEAD_DEL = """
<config>
  <netconf xmlns="http://www.huawei.com/netconf/vrp/huawei-netconf">
    <authorization>
      <userGroupRules>
        <userGroupRule nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SET_AUTHORIZATION_USERGROUP_CONFIG_TAIL = """
        </userGroupRule>
      </userGroupRules>
    </authorization>
  </netconf>
</config>
"""

GET_AUTHORIZATION_TASKGROUP_CONFIG_HEAD = """
<filter type="subtree">
  <netconf xmlns="http://www.huawei.com/netconf/vrp/huawei-netconf">
    <authorization>
      <taskGroupRules>
        <taskGroupRule>
"""

GET_AUTHORIZATION_TASKGROUP_CONFIG_TAIL = """
        </taskGroupRule>
      </taskGroupRules>
    </authorization>
  </netconf>
</filter>
"""

SET_AUTHORIZATION_TASKGROUP_CONFIG_HEAD = """
<config>
  <netconf xmlns="http://www.huawei.com/netconf/vrp/huawei-netconf">
    <authorization>
      <taskGroupRules>
        <taskGroupRule>
"""

SET_AUTHORIZATION_TASKGROUP_CONFIG_HEAD_DEL = """
<config>
  <netconf xmlns="http://www.huawei.com/netconf/vrp/huawei-netconf">
    <authorization>
      <taskGroupRules>
        <taskGroupRule nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
"""

SET_AUTHORIZATION_TASKGROUP_CONFIG_TAIL = """
        </taskGroupRule>
      </taskGroupRules>
    </authorization>
  </netconf>
</config>
"""

USERGROUPNAME = """
        <userGroupName>%s</userGroupName>
"""

TASKGROUPNAME = """
        <taskGroupName>%s</taskGroupName>
"""

RULENAME = """
        <ruleName>%s</ruleName>
"""

RULETYPE = """
        <ruleType>%s</ruleType>
"""

ACTION = """
        <action>%s</action>
"""

RPCOPERNAME = """
        <rpcOperName>%s</rpcOperName>
"""

DATANODEPATH = """
        <dataNodePath>%s</dataNodePath>
"""

READ = """
        <read>%s</read>
"""

WRITE = """
        <write>%s</write>
"""

EXECUTE = """
        <execute>%s</execute>
"""

DESCRIPTION = """
        <description>%s</description>
"""


CREATE_TASKGROUP = """
<config>
  <aaa xmlns="http://www.huawei.com/netconf/vrp/huawei-aaa">
    <taskGroups>
      <taskGroup>
        <taskGroupName>%s</taskGroupName>
      </taskGroup>
    </taskGroups>
  </aaa>
</config>
"""

CREATE_USERGROUP = """
<config>
  <aaa xmlns="http://www.huawei.com/netconf/vrp/huawei-aaa">
    <userGroups>
      <userGroup>
        <userGroupName>%s</userGroupName>
      </userGroup>
    </userGroups>
  </aaa>
</config>
"""

DELETE_USERGROUP = """
<config>
  <aaa xmlns="http://www.huawei.com/netconf/vrp/huawei-aaa">
    <userGroups>
      <userGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <userGroupName>%s</userGroupName>
      </userGroup>
    </userGroups>
  </aaa>
</config>
"""

DELETE_TASKGROUP = """
<config>
  <aaa xmlns="http://www.huawei.com/netconf/vrp/huawei-aaa">
    <taskGroups>
      <taskGroup nc:operation="delete" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <taskGroupName>%s</taskGroupName>
      </taskGroup>
    </taskGroups>
  </aaa>
</config>
"""


class Authorization(object):
    """
     Netconf authorization
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)
        self.operation = self.module.params['operation']
        self.groupType = self.module.params['groupType']
        self.taskGroupName = self.module.params['taskGroupName']
        self.userGroupName = self.module.params['userGroupName']
        self.ruleName = self.module.params['ruleName']
        self.ruleType = self.module.params['ruleType']
        self.action = self.module.params['action']
        self.rpcOperName = self.module.params['rpcOperName']
        self.dataNodePath = self.module.params['dataNodePath']
        self.read = self.module.params['read']
        self.write = self.module.params['write']
        self.execute = self.module.params['execute']
        self.description = self.module.params['description']
        self.results = dict()
        self.results['response'] = []

    def create_taskgroup(self):
        taskgroup_create_xml = ''
        if self.taskGroupName == '' or self.taskGroupName is None:
            self.module.exit_json(
                msg='Error: create taskgroup, but taskGroupName is empty.')
        taskgroup_create_xml += CREATE_TASKGROUP % self.taskGroupName
        recv_xml = set_nc_config(self.module, taskgroup_create_xml)
        if "<ok/>" in recv_xml:
            return 'ok'
        return 'pok'

    def delete_taskgroup(self):
        taskgroup_create_xml = ''
        if self.taskGroupName == '' or self.taskGroupName is None:
            self.module.exit_json(
                msg='Error: create taskgroup, but taskGroupName is empty.')
        taskgroup_create_xml += DELETE_TASKGROUP % self.taskGroupName
        recv_xml = set_nc_config(self.module, taskgroup_create_xml)
        if "<ok/>" in recv_xml:
            return 'ok'
        return 'pok'

    def create_usergroup(self):
        usergroup_create_xml = ''
        if self.userGroupName == '' or self.userGroupName is None:
            self.module.exit_json(
                msg='Error: create usergroup, but userGroupName is empty.')
        usergroup_create_xml += CREATE_USERGROUP % self.userGroupName
        recv_xml = set_nc_config(self.module, usergroup_create_xml)
        if "<ok/>" in recv_xml:
            return 'ok'
        return 'pok'

    def delete_usergroup(self):
        usergroup_create_xml = ''
        if self.userGroupName == '' or self.userGroupName is None:
            self.module.exit_json(
                msg='Error: create usergroup, but userGroupName is empty.')
        usergroup_create_xml += DELETE_USERGROUP % self.userGroupName
        recv_xml = set_nc_config(self.module, usergroup_create_xml)
        if "<ok/>" in recv_xml:
            return 'ok'
        return 'pok'

    def xml_make_get(self):
        get_grouprule_config_xml = ''
        if self.groupType == 'taskgroup':
            if self.taskGroupName == '' or self.taskGroupName is None:
                self.module.exit_json(
                    msg='Error: get authorization, but taskGroupName is empty.')
            if self.ruleName == '' or self.ruleName is None:
                self.module.exit_json(
                    msg='Error: get authorization, but ruleName is empty.')
            if self.ruleType == '' or self.ruleType is None:
                self.module.exit_json(
                    msg='Error: get authorization, but ruleType is empty.')

            get_grouprule_config_xml += GET_AUTHORIZATION_TASKGROUP_CONFIG_HEAD
            get_grouprule_config_xml += TASKGROUPNAME % self.taskGroupName
            get_grouprule_config_xml += RULENAME % self.ruleName
            get_grouprule_config_xml += RULETYPE % self.ruleType
            get_grouprule_config_xml += GET_AUTHORIZATION_TASKGROUP_CONFIG_TAIL

        elif self.groupType == 'usergroup':
            if self.userGroupName == '' or self.userGroupName is None:
                self.module.exit_json(
                    msg='Error: get authorization, but userGroupName is empty.')
            if self.ruleName == '' or self.ruleName is None:
                self.module.exit_json(
                    msg='Error: get authorization, but ruleName is empty.')
            if self.ruleType == '' or self.ruleType is None:
                self.module.exit_json(
                    msg='Error: get authorization, but ruleType is empty.')

            get_grouprule_config_xml += GET_AUTHORIZATION_USERGROUP_CONFIG_HEAD
            get_grouprule_config_xml += USERGROUPNAME % self.userGroupName
            get_grouprule_config_xml += RULENAME % self.ruleName
            get_grouprule_config_xml += RULETYPE % self.ruleType
            get_grouprule_config_xml += GET_AUTHORIZATION_USERGROUP_CONFIG_TAIL
        else:
            self.module.exit_json(
                msg='Error: get authorization, and groupType must be taskgroup or usergroup.')
        return get_grouprule_config_xml

    def xml_make_set_taskgroup(self):
        set_taskgrouprule_config_xml = ''
        if self.taskGroupName == '' or self.taskGroupName is None:
            self.module.exit_json(
                msg='Error: set authorization, but taskGroupName is empty.')
        if self.ruleName == '' or self.ruleName is None:
            self.module.exit_json(
                msg='Error: set authorization, but ruleName is empty.')
        if self.ruleType == '' or self.ruleType is None:
            self.module.exit_json(
                msg='Error: set authorization, but ruleType is empty.')

        if self.operation == 'create':
            set_taskgrouprule_config_xml += SET_AUTHORIZATION_TASKGROUP_CONFIG_HEAD
            set_taskgrouprule_config_xml += TASKGROUPNAME % self.taskGroupName
            set_taskgrouprule_config_xml += RULENAME % self.ruleName
            set_taskgrouprule_config_xml += RULETYPE % self.ruleType
            if self.ruleType == 'operationRule':
                if self.action or self.action == '':
                    set_taskgrouprule_config_xml += ACTION % self.action
                if self.rpcOperName or self.rpcOperName == '':
                    set_taskgrouprule_config_xml += RPCOPERNAME % self.rpcOperName
                if self.description or self.description == '':
                    set_taskgrouprule_config_xml += DESCRIPTION % self.description
            elif self.ruleType == 'datanodeRule':
                if self.action or self.action == '':
                    set_taskgrouprule_config_xml += ACTION % self.action
                if self.dataNodePath or self.dataNodePath == '':
                    set_taskgrouprule_config_xml += DATANODEPATH % self.dataNodePath
                if self.action == 'permit':
                    if self.read or self.read == '':
                        set_taskgrouprule_config_xml += READ % self.read
                    if self.write or self.write == '':
                        set_taskgrouprule_config_xml += WRITE % self.write
                    if self.execute or self.execute == '':
                        set_taskgrouprule_config_xml += EXECUTE % self.execute
                if self.description or self.description == '':
                    set_taskgrouprule_config_xml += DESCRIPTION % self.description

        if self.operation == 'delete':
            set_taskgrouprule_config_xml += SET_AUTHORIZATION_TASKGROUP_CONFIG_HEAD_DEL
            set_taskgrouprule_config_xml += TASKGROUPNAME % self.taskGroupName
            set_taskgrouprule_config_xml += RULENAME % self.ruleName
            set_taskgrouprule_config_xml += RULETYPE % self.ruleType

        set_taskgrouprule_config_xml += SET_AUTHORIZATION_TASKGROUP_CONFIG_TAIL
        return set_taskgrouprule_config_xml

    def xml_make_set_usergroup(self):
        set_usergrouprule_config_xml = ''
        if self.userGroupName == '' or self.userGroupName is None:
            self.module.exit_json(
                msg='Error: set authorization, but userGroupName is empty.')
        if self.ruleName == '' or self.ruleName is None:
            self.module.exit_json(
                msg='Error: set authorization, but ruleName is empty.')
        if self.ruleType == '' or self.ruleType is None:
            self.module.exit_json(
                msg='Error: set authorization, but ruleType is empty.')

        if self.operation == 'create':
            set_usergrouprule_config_xml += SET_AUTHORIZATION_USERGROUP_CONFIG_HEAD
            set_usergrouprule_config_xml += USERGROUPNAME % self.userGroupName
            set_usergrouprule_config_xml += RULENAME % self.ruleName
            set_usergrouprule_config_xml += RULETYPE % self.ruleType
            if self.ruleType == 'operationRule':
                if self.action or self.action == '':
                    set_usergrouprule_config_xml += ACTION % self.action
                if self.rpcOperName or self.rpcOperName == '':
                    set_usergrouprule_config_xml += RPCOPERNAME % self.rpcOperName
                if self.description or self.description == '':
                    set_usergrouprule_config_xml += DESCRIPTION % self.description
            elif self.ruleType == 'datanodeRule':
                if self.action or self.action == '':
                    set_usergrouprule_config_xml += ACTION % self.action
                if self.dataNodePath or self.dataNodePath == '':
                    set_usergrouprule_config_xml += DATANODEPATH % self.dataNodePath
                if self.action == 'permit':
                    if self.read or self.read == '':
                        set_usergrouprule_config_xml += READ % self.read
                    if self.write or self.write == '':
                        set_usergrouprule_config_xml += WRITE % self.write
                    if self.execute or self.execute == '':
                        set_usergrouprule_config_xml += EXECUTE % self.execute
                if self.description or self.description == '':
                    set_usergrouprule_config_xml += DESCRIPTION % self.description

        if self.operation == 'delete':
            set_usergrouprule_config_xml += SET_AUTHORIZATION_USERGROUP_CONFIG_HEAD_DEL
            set_usergrouprule_config_xml += USERGROUPNAME % self.userGroupName
            set_usergrouprule_config_xml += RULENAME % self.ruleName
            set_usergrouprule_config_xml += RULETYPE % self.ruleType

        set_usergrouprule_config_xml += SET_AUTHORIZATION_USERGROUP_CONFIG_TAIL
        return set_usergrouprule_config_xml

    def xml_make_set(self):
        if self.groupType == 'taskgroup':
            if self.operation == 'create':
                result = self.create_taskgroup()
                if result == 'ok':
                    set_grouprule_config_xml = self.xml_make_set_taskgroup()
                else:
                    self.module.exit_json(msg='Error: create taskgroup failed')
            else:
                set_grouprule_config_xml = self.xml_make_set_taskgroup()
        elif self.groupType == 'usergroup':
            if self.operation == 'create':
                result = self.create_usergroup()
                if result == 'ok':
                    set_grouprule_config_xml = self.xml_make_set_usergroup()
                else:
                    self.module.exit_json(msg='Error: create usergroup failed')
            else:
                set_grouprule_config_xml = self.xml_make_set_usergroup()
        else:
            self.module.exit_json(
                msg='Error: set authorization, and groupType must be taskgroup or usergroup.')

        return set_grouprule_config_xml

    def run(self):
        taskgroup_delete_xml = ''
        usergroup_delete_xml = ''
        if self.operation == 'get':
            get_authorization_config_xml = self.xml_make_get()
            recv_xml = get_nc_config(self.module, get_authorization_config_xml)
        else:
            set_authorization_config_xml = self.xml_make_set()
            recv_xml = set_nc_config(self.module, set_authorization_config_xml)

        if self.operation == 'delete' and self.groupType == 'taskgroup':
            taskgroup_delete_xml += DELETE_TASKGROUP % self.taskGroupName
            recv_xml2 = set_nc_config(self.module, taskgroup_delete_xml)
            self.results["response"].append(recv_xml2)

        if self.operation == 'delete' and self.groupType == 'usergroup':
            usergroup_delete_xml += DELETE_USERGROUP % self.userGroupName
            recv_xml2 = set_nc_config(self.module, usergroup_delete_xml)
            self.results["response"].append(recv_xml2)

        self.results["response"].append(recv_xml)
        self.module.exit_json(**self.results)


def main():
    argument_spec = dict(
        operation=dict(choices=['create', 'delete', 'get'])
    )
    argument_spec.update(ne_argument_spec)
    argument_spec.update(netconf_authorization_spec)

    netconf_authorization = Authorization(argument_spec)
    netconf_authorization.run()


if __name__ == '__main__':
    main()
