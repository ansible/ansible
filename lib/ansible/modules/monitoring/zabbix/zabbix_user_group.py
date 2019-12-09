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
short_description: Create/update/delete Zabbix user group
description:
    - Create/update/delete Zabbix user group.
version_added: "2.10"
author:
    - Emmanuel Riviere (@emriver)
requirements:
    - "python >= 2.7"
    - "zabbix-api >= 0.5.4"
options:
    name:
        description:
            - Name of the Zabbix user group
        required: true
        type: str
    debug_mode:
        description:
            - Enable or disable debug mode.
        required: false
        type: bool
        default: no
    gui_access:
        description:
            - Frontend authentication method.
        required: false
        type: str
        choices: [default,internal,ldap,disabled]
        default: "default"
    users_status:
        description:
            - Whether the group is enabled of disabled
        required: false
        type: str
        choices: [enabled, disabled]
        default: "enabled"
    rights:
        description:
            - List of permissions associated to the group
            - Each right must contain a host_group and a permission (denied,RO,RW)
        required: false
        type: list
        suboptions:
            host_group:
                description:
                    - Host group name
                type: str
                required: true
            permission:
                description:
                    - Permission associated with that group
                type: str
                required: true
                choices: [denied, RO, RW]
    users:
        description:
            - List of user aliases to add in the group
        required: false
        type: list
    state:
        description:
            - State of the group
            - If C(present), the group will be created or updated if the group configuration is different
            - If C(absent), the group will be deleted
        required: false
        type: str
        choices: [present, absent]
        default: present

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
---
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
'''

import atexit
import traceback

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

try:
    from zabbix_api import ZabbixAPI, ZabbixAPIException
    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False


class UserGroup(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def get_group_id(self, group_name):
        group_id = None
        groups = self._zapi.usergroup.get({'filter': {'name': group_name}})
        if len(groups) == 1:
            group_id = groups[0]['usrgrpid']
        return group_id

    def delete_group(self, group_id):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.usergroup.delete([group_id])

    def dump_group(self, group_id):
        groups = self._zapi.usergroup.get({'output': 'extend', 'usrgrpids': group_id, 'selectRights': 1, 'selectUsers': 1})
        return groups[0]

    def generate_group_config(self, name, debug_mode, gui_access, users_status, rights, users):
        if debug_mode:
            debug_mode = 1
        else:
            debug_mode = 0

        gui_accesses = {'default': '0', 'internal': '1', 'ldap': '2', 'disabled': '3'}
        if LooseVersion(self._zapi.api_version()).version[:2] < LooseVersion('4.0').version:
            gui_accesses = {'default': '0', 'internal': '1', 'disabled': '2'}

        gui_access = gui_accesses[gui_access]

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

            new_rights.append({'id': group_id, 'permission': permission})

        userids = []
        for user in users:
            user_array = self._zapi.user.get({'filter': {'alias': user}})
            if not user_array:
                self._module.fail_json(msg="User with alias %s not found" % user)
            userids.append(user_array[0]['userid'])

        request = {
            'name': name,
            'gui_access': gui_access,
            'debug_mode': debug_mode,
            'users_status': users_status,
            'rights': new_rights
        }

        # Won't push an empty array to avoid removing all users from a group if none provided
        if userids:
            request['userids'] = userids

        return request

    def compare_config(self, generated, current):
        items_to_check = ['gui_access', 'users_status', 'debug_mode']
        for item in items_to_check:
            if str(generated[item]) != str(current[item]):
                return True

        # Users will only be compared if some are provided
        # Otherwise it will remove user already added in the group
        if 'userids' in generated:
            if set(generated['userids']) != set([user['userid'] for user in current['users']]):
                return True

        # Rights check
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
                options=dict(
                    host_group=dict(type='str', required=True),
                    permission=dict(type='str', required=True, choices=['denied', 'RO', 'RW'])
                )
            ),
            users=dict(
                type='list',
                default=[],
                required=False,
                elements='str'
            ),
            state=dict(default="present", choices=['present', 'absent']),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

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

    # Login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password, validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except ZabbixAPIException as error:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % error)

    # Load UserGroup module
    user_group = UserGroup(module, zbx)
    group_id = user_group.get_group_id(name)

    # Delete group
    if state == "absent":
        if not group_id:
            module.exit_json(changed=False, msg="User group not found, no change: %s" % name)
        user_group.delete_group(group_id)
        module.exit_json(changed=True, result="Successfully deleted group %s" % name)

    elif state == "present":
        # Does not exists going to create it
        if not group_id:
            user_group.create_group(name, debug_mode, gui_access, users_status, rights, users)
            module.exit_json(changed=True, result="Successfully created group %s" % name)
        # Else we update it
        else:
            changed = user_group.update_group(group_id, name, debug_mode, gui_access, users_status, rights, users)
            module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
