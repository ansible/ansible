#!/usr/bin/python
# Copyright: (c) 2018, Manuel Maestinger <manuel.maestinger@inf.ethz.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: member
short_description: Manage local group memberships
version_added: "2.6"
description:
    - Define which users are or are not members of a specific group.
options:
    group:
        description:
            - Name of the group to define the members of.
        required: true
    users:
        description:
            - List of the group members.
        type: list
        required: true
    state:
        description:
            - Whether the users should be member of the group or not.
        choices: [ exactly, absent, present ]
        default: exactly
requirements:
    - gpasswd
author: Manuel Maestinger (@manumeter)
'''

EXAMPLES = '''
- name: Ensure only "someuser" is member of "sudoers"
  member:
    group: sudoers
    users:
      - someuser

- name: Remove "otheruser" from "othergroup"
  member:
    group: othergroup
    users:
      - otheruser
    state: absent

- name: Add "thirduser" to "othergroup"
  member:
    group: othergroup
    users:
      - thirduser
    state: present
'''

RETURN = '''
group:
    description: The group we operated on
    returned: always
    type: str
users_added:
    description: Users effectively added to the group
    returned: always
    type: list
users_removed:
    description: Users effectively removed from the group
    returned: always
    type: list
'''


from ansible.module_utils.basic import AnsibleModule, load_platform_subclass
import grp

#
# Group manipulation classes
#

class GroupError(Exception):
    def __init__(self, rc, out, err):
        super(GroupError, self).__init__(err)
        self.rc = rc
        self.out = out
        self.err = err

class Group(object):
    '''
    This is a generic Group membership manipulation class that is subclassed
    based on platform.

    All subclasses MUST define platform and distribution (which may be None).
    '''

    platform = 'Generic'
    distribution = None
    
    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(Group, args, kwargs)

    def __init__(self, module, name):
        self._module = module
        self._name = name
        self._grp = self._get_grp(name)

    def _get_grp(self, name):
        try:
            return grp.getgrnam(name)
        except KeyError:
            return False

    def _run(self, cmd, expected_rc = 0):
        (rc, out, err) = self._module.run_command(cmd)
        if rc != expected_rc:
            raise GroupError(rc, out, err)

    def exists(self):
        return bool(self._grp)

    def get_members(self):
        return self._grp.gr_mem if self._grp else []

    def remove_members(self, members):
        cmd = [self._module.get_bin_path('gpasswd', True), self._name, '--delete']
        for member in members:
            self._run(cmd + [member])

    def add_members(self, members):
        cmd = [self._module.get_bin_path('gpasswd', True), self._name, '--add']
        for member in members:
            self._run(cmd + [member])

#
# Module logic
#

def main():
    module = AnsibleModule(
        argument_spec={
            'group': {'type': 'str', 'required': True},
            'users': {'type': 'list', 'required': True},
            'state': {'type': 'str', 'default': 'exactly', 'choices': ['exactly', 'absent', 'present']},
        },
        supports_check_mode=True
    )
    
    result = {
        'changed': False,
        'state': module.params['state'],
        'group': module.params['group'],
        'users_added': [],
        'users_removed': []
    }

    group = Group(module, result['group'])

    if not group.exists():
        module.fail_json(msg='Group %s does not exist' % result['group'], **result)
        return

    users = set(module.params['users'])
    members = set(group.get_members())
        
    if result['state'] == 'absent':
        result['users_removed'] = list(users.intersection(members))
    elif result['state'] == 'present':
        result['users_added']   = list(users.difference(members))
    else:
        result['users_added']   = list(users.difference(members))
        result['users_removed'] = list(members.difference(users))

    if len(result['users_removed']) > 0 or \
       len(result['users_added'])   > 0:
        result['changed'] = True

    if not result['changed']:
        module.exit_json(**result)
        return
    elif module.check_mode:
        return result
    
    try:
        group.remove_members(result['users_removed'])
        group.add_members(result['users_added'])
    except GroupError as e:
        module.fail_json(msg=e.message, **result)
        return

    module.exit_json(**result)
    return

#
# Run
#

if __name__ == '__main__':
    main()
