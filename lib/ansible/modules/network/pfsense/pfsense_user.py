#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_user
version_added: "2.10"
short_description: Manage pfSense users
description:
  >
    Manage pfSense users
author: Orion Poplawski (@opoplawski)
notes:
options:
  name:
    description: The name of the user
    required: true
    type: str
  state:
    description: State in which to leave the user
    default: present
    choices: [ "present", "absent" ]
    type: str
  descr:
    description: Description of the user
    type: str
  scope:
    description: Scope of the user ('user' is a normal user)
    default: user
    choices: [ "user", "system" ]
    type: str
  uid:
    description:
    - UID of the user.
    - Will use next available UID if not specified.
    type: str
  groups:
    description:
    - Groups of the user.
    type: list
  password:
    description:
    - bcrypt encrypted password of the user.
    type: str
  priv:
    description:
    - A list of privileges to assign.
    - Allowed values include page-all, user-shell-access.
    type: list
  authorizedkeys:
    description:
    - Contents of ~/.ssh/authorized_keys.  Can be base64 encoded.
    type: str
"""

EXAMPLES = """
- name: Add operator user
  pfsense_user:
    name: operator
    descr: Operator
    scope: user
    groups: [ 'Operators' ]
    priv: [ 'page-all', 'user-shell-access' ]

- name: Remove user
  pfsense_user:
    name: operator
    state: absent
"""

RETURN = """

"""

import base64
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.pfsense import PFSenseModule

USER_PHP_COMMAND_PREFIX = """
require_once('auth.inc');
init_config_arr(array('system', 'user'));
$a_user = &$config['system']['user'];
$userent = $a_user[{idx}];
"""

USER_PHP_COMMAND_SET = USER_PHP_COMMAND_PREFIX + """
local_user_set($userent);
foreach ({mod_groups} as $groupname) {{
    $group = &$config['system']['group'][$groupindex[$groupname]];
    local_group_set($group);
}}
if (is_dir("/etc/inc/privhooks")) {{
    run_plugins("/etc/inc/privhooks");
}}
"""

USER_PHP_COMMAND_DEL = USER_PHP_COMMAND_PREFIX + """
foreach ({mod_groups} as $groupname) {{
    $group = &$config['system']['group'][$groupindex[$groupname]];
    local_group_set($group);
}}
local_user_del($userent);
"""


class pfSenseUser(object):

    def __init__(self, module):
        self.module = module
        self.pfsense = PFSenseModule(module)
        self.system = self.pfsense.get_element('system')
        self.users = self.system.findall('user')
        self.groups = self.system.findall('group')
        self.diff = {}
        self.change_descr = ''

    def _find_user(self, name):
        found = None
        i = 0
        for user in self.users:
            if user.find('name').text == name:
                found = user
                break
            i += 1
        return (found, i)

    def _find_group(self, name):
        found = None
        i = 0
        for group_elt in self.groups:
            if group_elt.find('name').text == name:
                found = group_elt
                break
            i += 1
        return (found, i)

    def _find_groups_for_uid(self, uid):
        groups = []
        for group_elt in self.groups:
            for member_elt in group_elt.findall('member'):
                if member_elt.text == uid:
                    groups.append(group_elt.find('name').text)
        return groups

    def _find_last_user_idx(self):
        found = False
        i = 0
        for elt in self.system:
            if elt.tag == 'user':
                i += 1
                found = True
            if not found:
                i += 1
        return i

    def _nextuid(self):
        nextuid_elt = self.system.find('nextuid')
        nextuid = nextuid_elt.text
        nextuid_elt.text = str(int(nextuid) + 1)
        return nextuid

    def _format_diff_priv(self, priv):
        if isinstance(priv, str):
            return [priv]
        else:
            return priv

    def _validate_password(self, user):
        if re.match(r'\$2b\$', user['password']):
            user['bcrypt-hash'] = user['password']
        else:
            self.module.fail_json(msg='Password (%s) does not appear to be a bcrypt hash' % user['password'])
        del user['password']

    def add(self, user):
        changed = False
        stdout = None
        stderr = None
        mod_groups = []

        # Allow authorizedkeys to be clear or base64 encoded
        if 'authorizedkeys' in user and 'ssh-' in user['authorizedkeys']:
            user['authorizedkeys'] = base64.b64encode(user['authorizedkeys'])

        user_elt, user_idx = self._find_user(user['name'])
        if user_elt is None:
            changed = True
            self.diff['before'] = {}

            if 'password' in user:
                self._validate_password(user)
            else:
                self.module.fail_json(msg='Password is required when adding a user')
            if 'uid' not in user:
                user['uid'] = self._nextuid()
            self.diff['after'] = user
            user_elt = self.pfsense.new_element('user')
            self.pfsense.copy_dict_to_element(user, user_elt)
            self.system.insert(self._find_last_user_idx(), user_elt)
            self.change_descr = 'ansible pfsense_user added %s' % (user['name'])
        else:
            if 'password' in user:
                self._validate_password(user)
            self.diff['before'] = self.pfsense.element_to_dict(user_elt)
            if 'priv' in self.diff['before']:
                self.diff['before']['priv'] = self._format_diff_priv(self.diff['before']['priv'])
            changed = self.pfsense.copy_dict_to_element(user, user_elt)
            self.diff['after'] = self.pfsense.element_to_dict(user_elt)
            if 'priv' in self.diff['after']:
                self.diff['after']['priv'] = self._format_diff_priv(self.diff['after']['priv'])
            self.change_descr = 'ansible pfsense_user updated "%s"' % (user['name'])

        # Handle group member element - need uid set or retrieved above
        if 'groups' in user:
            uid = user_elt.find('uid').text
            # Get current group membership
            self.diff['before']['groups'] = self._find_groups_for_uid(uid)

            # Add user to groups if needed
            for group in user['groups']:
                group_elt, group_idx = self._find_group(group)
                if group_elt is None:
                    self.module.fail_json(msg='Group (%s) does not exist' % group)
                member_found = False
                for member_elt in group_elt.findall('member'):
                    if member_elt.text == uid:
                        member_found = True
                if not member_found:
                    changed = True
                    mod_groups.append(group)
                    group_elt.append(self.pfsense.new_element('member', uid))

            # Remove user from groups if needed
            for group in self.diff['before']['groups']:
                if group not in user['groups']:
                    group_elt, group_idx = self._find_group(group)
                    if group_elt is None:
                        self.module.fail_json(msg='Group (%s) does not exist' % group)
                    for member_elt in group_elt.findall('member'):
                        if member_elt.text == uid:
                            changed = True
                            mod_groups.append(group)
                            group_elt.remove(member_elt)
                            break

            # Groups are not stored in the user element
            self.diff['after']['groups'] = user.pop('groups')

        # Decode keys for diff
        for k in self.diff:
            if 'authorizedkeys' in self.diff[k]:
                self.diff[k]['authorizedkeys'] = base64.b64decode(self.diff[k]['authorizedkeys'])

        if changed and not self.module.check_mode:
            self.pfsense.write_config(descr=self.change_descr)
            (dummy, stdout, stderr) = self.pfsense.phpshell(
                USER_PHP_COMMAND_SET.format(idx=user_idx, mod_groups=mod_groups))
        self.module.exit_json(changed=changed, diff=self.diff, stdout=stdout, stderr=stderr)

    def remove(self, user):
        user_elt, user_idx = self._find_user(user['name'])
        changed = False
        stdout = None
        stderr = None
        uid = user_elt.find('uid').text
        mod_groups = []
        self.diff['after'] = {}
        if user_elt is not None:
            changed = True
            self.diff['before'] = self.pfsense.element_to_dict(user_elt)

            # Get current group membership
            self.diff['before']['groups'] = self._find_groups_for_uid(uid)

            # Remove user from groups if needed
            for group in self.diff['before']['groups']:
                group_elt, group_idx = self._find_group(group)
                if group_elt is None:
                    self.module.fail_json(msg='Group (%s) does not exist' % group)
                for member_elt in group_elt.findall('member'):
                    if member_elt.text == uid:
                        mod_groups.append(group)
                        group_elt.remove(member_elt)
                        break

            self.system.remove(user_elt)

        if changed and not self.module.check_mode:
            (dummy, stdout, stderr) = self.pfsense.phpshell(
                USER_PHP_COMMAND_DEL.format(cmd='del', idx=user_idx, mod_groups=mod_groups))
            self.pfsense.write_config(descr='ansible pfsense_user removed "%s"' % (user['name']))
        self.module.exit_json(changed=changed, diff=self.diff, stdout=stdout, stderr=stderr)


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {'required': True, 'type': 'str'},
            'state': {
                'type': 'str',
                'default': 'present',
                'choices': ['present', 'absent']
            },
            'descr': {'type': 'str'},
            'scope': {
                'type': 'str',
                'default': 'user',
                'choices': ['user', 'system']
            },
            'uid': {'type': 'str'},
            'password': {'type': 'str', 'no_log': True},
            'groups': {'type': 'list'},
            'priv': {'type': 'list'},
            'authorizedkeys': {'type': 'str'},
        },
        supports_check_mode=True)

    pfuser = pfSenseUser(module)

    user = dict()
    user['name'] = module.params['name']
    state = module.params['state']
    if state == 'absent':
        pfuser.remove(user)
    elif state == 'present':
        for option in ['authorizedkeys', 'descr', 'scope', 'uid', 'password', 'groups', 'priv']:
            if module.params[option] is not None:
                user[option] = module.params[option]
        pfuser.add(user)


if __name__ == '__main__':
    main()
