#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Nate Coraor <nate@coraor.org>
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
from __future__ import absolute_import
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: zfs_delegate_admin
short_description: Manage ZFS delegated administration (user admin privileges)
description:
  - Manages ZFS file system delegated administration permissions, which allow unprivileged users to perform ZFS
    operations normally restricted to the superuser.
  - See the "zfs allow" section of C(zfs(1M)) for detailed explanations of options. This module attempts to adhere to
    the behavior of the command line tool as much as possible.
requirements:
  - "A ZFS/OpenZFS implementation that supports delegation with `zfs allow`, including: Solaris >= 10, illumos (all
    versions), FreeBSD >= 8.0R, ZFS on Linux >= 0.7.0."
version_added: "2.5"
options:
  name:
    description:
      - File system or volume name e.g. C(rpool/myfs)
    required: true
  state:
    description:
      - Whether to allow (C(present)), or unallow (C(absent)) a permission. When set to C(present), at least one
        "entity" param of I(users), I(groups), or I(everyone) are required. When set to C(absent), removes permissions
        from the specified entities, or removes all permissions if no entity params are specified.
    required: true
    choices: [present, absent]
  users:
    description:
      - List of users to whom permission(s) should be granted
  groups:
    description:
      - List of groups to whom permission(s) should be granted
  everyone:
    description:
      - Apply permissions to everyone.
    default: false
    type: bool
  permissions:
    description:
      - The list of permission(s) to delegate (required if C(state) is C(present))
    choices: ['allow','clone','create','destroy',...]
  local:
    description:
      - Apply permissions to C(name) locally (C(zfs allow -l))
    default: null
    type: bool
  descendents:
    description:
      - Apply permissions to C(name)'s descendents (C(zfs allow -d))
    default: null
    type: bool
  recursive:
    description:
      - Unallow permissions recursively (ignored when C(state) is C(present))
    default: false
    type: bool
author: "Nate Coraor (@natefoo)"
'''

EXAMPLES = '''
# Grant `zfs allow` and `unallow` permission to the `adm` user with the default local+descendents scope
- zfs_delegate_admin: name=rpool/myfs users=adm permissions=allow,unallow

# Grant `zfs send` to everyone, plus the group `backup`
- zfs_delegate_admin: name=rpool/myvol groups=backup everyone=yes permissions=send

# Grant `zfs send,receive` to users `foo` and `bar` with local scope only
- zfs_delegate_admin: name=rpool/myfs users=foo,bar permissions=send,receive local=yes

# Revoke all permissions from everyone (permissions specifically assigned to users and groups remain)
- zfs_delegate_admin: name=rpool/myfs state=absent everyone=yes
'''

# This module does not return anything other than the standard
# changed/state/msg/stdout
RETURN = '''
'''

from itertools import product

from ansible.module_utils.basic import AnsibleModule


class ZfsDelegateAdmin(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params.get('name')
        self.state = module.params.get('state')
        self.users = module.params.get('users')
        self.groups = module.params.get('groups')
        self.everyone = module.params.get('everyone')
        self.perms = module.params.get('permissions')
        self.scope = None
        self.changed = False
        self.initial_perms = None
        self.subcommand = 'allow'
        self.recursive_opt = []
        self.run_method = self.update

        self.setup(module)

    def setup(self, module):
        """ Validate params and set up for run.
        """
        if self.state == 'absent':
            self.subcommand = 'unallow'
            if module.params.get('recursive'):
                self.recursive_opt = ['-r']

        local = module.params.get('local')
        descendents = module.params.get('descendents')
        if (local and descendents) or (not local and not descendents):
            self.scope = 'ld'
        elif local:
            self.scope = 'l'
        elif descendents:
            self.scope = 'd'
        else:
            self.module.fail_json(msg='Impossible value for local and descendents')

        if not (self.users or self.groups or self.everyone):
            if self.state == 'present':
                self.module.fail_json(msg='One of `users`, `groups`, or `everyone` must be set')
            elif self.state == 'absent':
                self.run_method = self.clear
            # ansible ensures the else cannot happen here

        self.zfs_path = module.get_bin_path('zfs', True)

    @property
    def current_perms(self):
        """ Parse the output of `zfs allow <name>` to retrieve current permissions.
        """
        out = self.run_zfs_raw(subcommand='allow')
        perms = {
            'l': {'u': {}, 'g': {}, 'e': []},
            'd': {'u': {}, 'g': {}, 'e': []},
            'ld': {'u': {}, 'g': {}, 'e': []},
        }
        linemap = {
            'Local permissions:': 'l',
            'Descendent permissions:': 'd',
            'Local+Descendent permissions:': 'ld',
        }
        scope = None
        for line in out.splitlines():
            scope = linemap.get(line, scope)
            if not scope:
                continue
            try:
                if line.startswith('\tuser ') or line.startswith('\tgroup '):
                    ent_type, ent, cur_perms = line.split()
                    perms[scope][ent_type[0]][ent] = cur_perms.split(',')
                elif line.startswith('\teveryone '):
                    perms[scope]['e'] = line.split()[1].split(',')
            except ValueError:
                self.module.fail_json(msg="Cannot parse user/group permission output by `zfs allow`: '%s'" % line)
        return perms

    def run_zfs_raw(self, subcommand=None, args=None):
        """ Run a raw zfs command, fail on error.
        """
        cmd = [self.zfs_path, subcommand or self.subcommand] + (args or []) + [self.name]
        rc, out, err = self.module.run_command(cmd)
        if rc:
            self.module.fail_json(msg='Command `%s` failed: %s' % (' '.join(cmd), err))
        return out

    def run_zfs(self, args):
        """ Run zfs allow/unallow with appropriate options as per module arguments.
        """
        args = self.recursive_opt + ['-' + self.scope] + args
        if self.perms:
            args.append(','.join(self.perms))
        return self.run_zfs_raw(args=args)

    def clear(self):
        """ Called by run() to clear all permissions.
        """
        changed = False
        stdout = ''
        for scope, ent_type in product(('ld', 'l', 'd'), ('u', 'g')):
            for ent in self.initial_perms[scope][ent_type].keys():
                stdout += self.run_zfs(['-%s' % ent_type, ent])
                changed = True
        for scope in ('ld', 'l', 'd'):
            if self.initial_perms[scope]['e']:
                stdout += self.run_zfs(['-e'])
                changed = True
        return (changed, stdout)

    def update(self):
        """ Update permissions as per module arguments.
        """
        stdout = ''
        for ent_type, entities in (('u', self.users), ('g', self.groups)):
            if entities:
                stdout += self.run_zfs(['-%s' % ent_type, ','.join(entities)])
        if self.everyone:
            stdout += self.run_zfs(['-e'])
        return (self.initial_perms != self.current_perms, stdout)

    def run(self):
        """ Run an operation, return results for Ansible.
        """
        exit_args = {'state': self.state}
        self.initial_perms = self.current_perms
        exit_args['changed'], stdout = self.run_method()
        if exit_args['changed']:
            exit_args['msg'] = 'ZFS delegated admin permissions updated'
            exit_args['stdout'] = stdout
        self.module.exit_json(**exit_args)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(default='present', choices=['absent', 'present']),
            users=dict(default=[], type='list'),
            groups=dict(default=[], type='list'),
            everyone=dict(default=False, type='bool'),
            permissions=dict(default=[], type='list'),
            local=dict(default=None, type='bool'),
            descendents=dict(default=None, type='bool'),
            recursive=dict(default=False, type='bool')
        ),
        supports_check_mode=False,
        required_if=[('state', 'present', ['permissions'])]
    )
    zfs_delegate_admin = ZfsDelegateAdmin(module)
    zfs_delegate_admin.run()


if __name__ == '__main__':
    main()
