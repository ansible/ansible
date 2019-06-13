#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, OVH SAS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_user_group
short_description: Create/update/delete/dump Zabbix user group
description:
    - Create/update/delete/dump Zabbix user group.
version_added: "Not official"
author:
    - "Emmanuel Riviere, OVH"
requirements:
    - "python >= 2.7"
    - "zabbix-api >= 0.5.3"
options:
    name:
        description:
            - Name of the Zabbix user group
        required: true
    debug_mode:
        description:
            - Enable or disable debug mode.
        required: false
        choices: [disabled, enabled]
        default: "disabled"
    gui_access:
        description:
            - Frontend authentication method.
        required: false
        choices: [default,internal,ldap,disabled]
        default: "default"
    users_status:
        description:
            - Whether the group is enabled of disabled
        required: false
        choices: [enabled, disabled]
        defaut: "enabled"
    rights:
        description:
            - List of permissions associated to the group
            - Each right must contain a host_group and a permission (denied,RO,RW)
        required: false
    users:
        description:
            -List of users to add in the group
        required: false

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
---
- name: Dump Zabbix user group info
  local_action:
    module: zabbix_user_group
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    name: team1
    state: dump

- name: Create default user groups
  local_action:
    module: zabbix_user_group
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    state: present
    name: Test group
    rights:
        - host_group: Admin VMs
          permission: RW
    users:
        - user1
        - user2
'''

RETURN = '''
---
template_json:
  description: The JSON dump of the group
  returned: when state is dump
  type: str
  sample: {
    "group_json": {
        "debug_mode": "0", 
        "gui_access": "0", 
        "name": "Test group", 
        "rights": [
            {
                "id": "20", 
                "permission": "3"
            }, 
        ], 
        "users": [
            {
                "userid": "6"
            }, 
            {
                "userid": "12"
            }
        ], 
        "users_status": "0", 
        "usrgrpid": "19"
    } 
  }
'''

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import json
import traceback


try:
    from zabbix_api import ZabbixAPI, ZabbixAPIException

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


class UserGroup(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def get_group_id(self, group_name):
        group_id = None
        groups = self._zapi.usergroup.get({'filter':{'name':group_name}})
        if len(groups) == 1:
            group_id = groups[0]['usrgrpid']
        return group_id

    def delete_group(self, group_id):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.usergroup.delete([group_id])

    def dump_group(self, group_id):
        groups = self._zapi.usergroup.get({'output':'extend', 'usrgrpids':group_id, 'selectRights':1, 'selectUsers':1})
        return groups[0]

    def generate_group_config(self, name, debug_mode, gui_access, users_status, rights, users):
        if debug_mode:
            debug_mode = 1
        else:
            debug_mode = 0

        if gui_access == 'default':
            gui_access = 0
        elif gui_access == 'internal':
             gui_access = 1
        elif gui_access == 'ldap':
             gui_access = 2
        elif gui_access == 'disabled':
             gui_access = 3

        if users_status == 'enabled':
            users_status = 0
        else:
            users_status = 1

        new_rights = []
        for right in rights:
            groups = self._zapi.hostgroup.get({'filter': {'name': right['host_group']}})
            if not groups:
                self._module.fail_json(msg="Target host group %s not found" % right['host_group'])
            group_id = groups[0]['groupid']
            permission = "0"
            if right['permission'] == 'RO':
                permission = "2"
            elif right['permission'] == 'RW':
                permission = "3"

            new_rights.append( {'id':group_id, 'permission':permission} )

        userids = []
        for user in users:
            user_array = self._zapi.user.get({'filter': {'name': user}})
            if not user_array:
                self._module.fail_json(msg="User %s not found" % user)
            userids.append(user_array[0]['userid'])

        request = {
            'name': name,
            'gui_access': gui_access,
            'debug_mode': debug_mode,
            'users_status': users_status,
            'rights': new_rights
        }

        #won't push an empty array to avoid removing all users from a group if none provided
        if len(userids):
            request['userids'] = userids

        return request

    def compare_config(self, generated, current):
        items_to_check = ['gui_access','users_status','debug_mode']
        for item in items_to_check:
            if str(generated[item]) != str(current[item]):
                return True

        #Users will only be compared if some are provided
        #Otherwise it will remove user already added in the group
        if 'userids' in generated:
            if set(generated['userids']) != set([user['userid'] for user in current['users']]):
                return True

        #rights check
        new_generated_rights = []
        for rights in generated['rights']:
            new_generated_rights.append(int(rights['permission'] + rights['id']))

        new_current_rights = []
        for rights in current['rights']:
            new_current_rights.append(int(rights['permission'] + rights['id']))

        if set(new_generated_rights) != set(new_current_rights):
            return True

        return False

    def create_group(self, name, debug_mode, gui_access, users_status, rights, users):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.usergroup.create(self.generate_group_config(name, debug_mode, gui_access, users_status, rights, users))

    def update_group(self, group_id, name, debug_mode, gui_access, users_status, rights, users):
        current_config = self.dump_group(group_id)
        generated_config = self.generate_group_config(name, debug_mode, gui_access, users_status, rights, users)

        changed = self.compare_config(generated_config, current_config)

        if self._module.check_mode:
            self._module.exit_json(changed=changed)

        if changed:
            generated_config['usrgrpid'] = group_id
            self._zapi.usergroup.update(generated_config)

        return changed

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            name=dict(type='str', required=True),
            debug_mode=dict(type='bool', default=False, required=False),
            gui_access=dict(default='default', required=False, choices=['default', 'internal', 'ldap', 'disabled']),
            users_status=dict(default='enabled', required=False, choices=['enabled', 'disabled']),
            rights=dict(
                type='list',
                default=[],
                elements='dict',
                required=False,
                opstions=dict(
                    host_group=dict(type='str', required=True),
                    permission=dict(type='str', required=True, choices=['denied','RO','RW'])
                )
            ),
            users=dict(
                type='list',
                default=[],
                required=False,
                elements='str'
            ),
            state=dict(default="present", choices=['present', 'absent','dump']),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module " +
                             "(check docs or install with: " +
                             "pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    name = module.params['name']
    debug_mode = module.params['debug_mode']
    gui_access = module.params['gui_access']
    users_status = module.params['users_status']
    users = module.params['users']
    rights = module.params['rights']
    state = module.params['state']
    timeout = module.params['timeout']

    zbx = None

    #login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password, validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except ZabbixAPIException as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)
    
    #load UserGroup module
    user_group = UserGroup(module, zbx)
    group_id = user_group.get_group_id(name)

    #delete group
    if state == "absent":
        if not group_id:
            module.exit_json(changed=False, msg="User group not found, no change: %s" % name)
        user_group.delete_group(group_id)
        module.exit_json(changed=True, result="Successfully deleted group %s" % name)

    elif state == "dump":
        if not group_id:
            module.fail_json(msg='User group not found: %s' % name)
        module.exit_json(changed=False, group_json=user_group.dump_group(group_id))

    elif state == "present":
        #Does not exists going to create it
        if not group_id:
            user_group.create_group(name, debug_mode, gui_access, users_status, rights, users)
            module.exit_json(changed=True, result="Successfully created group %s" % name)
        #Else we update it
        else:
            changed = user_group.update_group(group_id, name, debug_mode, gui_access, users_status, rights, users)
            module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
