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

DOCUMENTATION = '''
---
module: zfs_permissions
short_description: Manage zfs administrative permissions
description:
  - Manages ZFS file system administrative permissions on Solaris and FreeBSD. See zfs(1M) for more information about the properties.
version_added: "1.10"
options:
  name:
    description:
      - File system or volume name e.g. C(rpool/myfs)
    required: true
  state:
    description:
      - Whether to allow (C(present)), or unallow (C(absent)) a permission.
    required: true
    choices: [present, absent]
  users:
    description:
      - Users to whom permission(s) should be granted, separated by commas.
    required: false
  groups:
    description:
      - Groups to whom permission(s) should be granted, separated by commas.
    required: false
  everyone:
    description:
      - Apply permissions to everyone.
    required: false
    default: false
    choices: ['on','off']
  permissions:
    description:
      - The permission(s) to delegate, separated by commas (required if C(state) is C(present))
    required: false
    choices: ['allow','clone','create','destroy',...]
  local:
    description:
      - Apply permissions to C(name) "locally" (C(zfs allow -l))
    required: false
    default: null
    choices: ['on','off']
  descendents:
    description:
      - Apply permissions to C(name)'s descendents (C(zfs allow -d))
    required: false
    default: null
    choices: ['on','off']
  recursive:
    description:
      - Unallow permissions recursively (ignored when C(state) is C(present))
    required: false
    default: false
    choices: ['on','off']
author: "Nate Coraor (@natefoo)"
'''

EXAMPLES = '''
# Grant `zfs allow` and `unallow` permission to the `adm` user with local+descendents scope
- zfs_permissions: name=rpool/myfs users=adm permissions=allow,unallow

# Grant `zfs send` to everyone, plus the group `backup`
- zfs_permissions: name=rpool/myvol groups=backup everyone=yes permissions=send

# Grant `zfs send,receive` to users `foo` and `bar` with local scope only
- zfs_permissions: name=rpool/myfs users=foo,bar permissions=send,receive local=yes

# Revoke all permissions from everyone (permissions specifically assigned to users and groups remain)
- zfs_permissions: name=rpool/myfs state=absent everyone=yes
'''


import sys


class ZfsPermissions(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params.get('name')
        self.state = module.params.get('state')
        self.users = module.params.get('users') or []
        self.groups = module.params.get('groups') or []
        self.everyone = module.boolean(module.params.get('everyone'))
        self.perms = module.params.get('permissions') or []
        self.recursive = module.boolean(module.params.get('recursive'))
        self.scope = None
        self.changed = False
        self.__current_perms = None

        if self.state == 'present' and not self.perms:
            self.module.fail_json(msg='The `permissions` option is required for state=present')

        if self.state == 'present' and not (self.users or self.groups or self.everyone):
            self.module.fail_json(msg='One of `users`, `groups`, or `everyone` must be set')

        for splittable in ('users', 'groups', 'perms'):
            if getattr(self, splittable):
                setattr(self, splittable, getattr(self, splittable).split(','))

        local = module.boolean(module.params.get('local'))
        descendents = module.boolean(module.params.get('descendents'))
        if (local and descendents) or (not local and not descendents):
            self.scope = 'ld'
        elif local:
            self.scope = 'l'
        elif descendents:
            self.scope = 'd'
        else:
            self.module.fail_json(msg='Impossible value for local and descendents')

        self.subcommand = 'allow'
        self.recursive_opt = []
        if self.state == 'absent':
            self.subcommand = 'unallow'
            if self.recursive:
                self.recursive_opt = ['-r']
            else:
                self.recursive_opt = []

        self.run()

    @property
    def current_perms(self):
        if self.__current_perms is None:
            rc, out, err = self.run_command(['zfs', 'allow', self.name])
            if rc:
                self.module.fail_json(msg='Getting permissions for %s failed: %s' % (self.name, err))
            perms = dict(l  = dict(u=dict(), g=dict(), e=[]),
                         d  = dict(u=dict(), g=dict(), e=[]),
                         ld = dict(u=dict(), g=dict(), e=[]))
            reading = None
            for line in out.splitlines():
                if line == 'Local permissions:':
                    reading = 'l'
                elif line == 'Descendent permissions:':
                    reading = 'd'
                elif line == 'Local+Descendent permissions:':
                    reading = 'ld'
                elif line.startswith('\tuser '):
                    user, cur_perms = line.split()[1:3]
                    perms[reading]['u'][user] = cur_perms.split(',')
                elif line.startswith('\tgroup '):
                    group, cur_perms = line.split()[1:3]
                    perms[reading]['g'][group] = cur_perms.split(',')
                elif line.startswith('\teveryone '):
                    perms[reading]['e'] = line.split()[1].split(',')
            self.__current_perms = perms
        return self.__current_perms

    def run_command(self, cmd):
        progname = cmd[0]
        cmd[0] = self.module.get_bin_path(progname, True)
        return self.module.run_command(cmd)

    def change_required(self, ent_type):
        # zfs allow/unallow are idempotent, so we only need to do this for Ansible's changed flag
        rval = []
        if ent_type == 'u':
            entities = self.users
        elif ent_type == 'g':
            entities = self.groups
        for ent in entities:
            ent_perms = self.current_perms[self.scope][ent_type].get(ent, None)
            if self.state == 'present' and ent_perms is None:
                rval.append(ent)
            elif self.state == 'absent' and ent_perms is not None:
                rval.append(ent)
            elif ent_perms is not None:
                for perm in self.perms:
                    if ((self.state == 'present' and perm not in ent_perms) or
                        (self.state == 'absent' and perm in ent_perms)):
                        # at least one desired permission is absent, or
                        # at least one undesired permission is present
                        rval.append(ent)
                        break
        return rval

    def run(self):
        def run_cmd(args):
            cmd = ['zfs', self.subcommand] + self.recursive_opt + ['-%s' % self.scope] + args
            if self.perms:
                cmd = cmd + [','.join(self.perms)]
            cmd = cmd + [self.name]
            if self.module.check_mode:
                return 'Check mode skipped execution of: %s' % ' '.join(cmd)
            rc, out, err = self.run_command(cmd)
            if rc:
                msg = 'Changing permissions with `%s` failed: %s' % (' '.join(cmd), err)
                self.module.fail_json(msg=msg)
            return out
        stdout = ''
        for ent_type in ('u', 'g'):
            change = self.change_required(ent_type)
            if change:
                args = ['-%s' % ent_type, ','.join(change)]
                stdout += run_cmd(args)
                self.changed = True
        if self.everyone:
            everyone_perms = self.current_perms[self.scope]['e']
            if self.state == 'absent' and not self.perms and everyone_perms:
                args = ['-e']
                stdout += run_cmd(args)
                self.changed = True
            for perm in self.perms:
                if ((self.state == 'present' and perm not in everyone_perms) or
                    (self.state == 'absent' and perm in everyone_perms)):
                    #
                    args = ['-e']
                    stdout += run_cmd(args)
                    self.changed = True
                    break

        exit_args = dict(changed=self.changed, state=self.state)
        if self.changed:
            exit_args.update(msg='ZFS permissions updated', stdout=stdout)

        self.module.exit_json(**exit_args)


def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            state = dict(default="present", choices=["absent", "present"]),
            users = dict(default=None),
            groups = dict(default=None),
            everyone = dict(default=False, choices=BOOLEANS),
            permissions = dict(default=None),
            local = dict(default=None, choices=BOOLEANS),
            descendents = dict(default=None, choices=BOOLEANS),
            recursive = dict(default=False, choices=BOOLEANS)
        ),
        supports_check_mode = True
    )


    zfs_permissions = ZfsPermissions(module)

    sys.exit(0)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
