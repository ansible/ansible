#!/usr/bin/python
# -*- coding: utf-8 -*-
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

DOCUMENTATION = '''
---
module: acl
version_added: "1.4"
short_description: Sets and retrieves file ACL information.
description:
    - Sets and retrieves file ACL information.
options:
  name:
    required: true
    default: null
    description:
      - The full path of the file or object.
    aliases: ['path']

  state:
    required: false
    default: query
    choices: [ 'query', 'present', 'absent' ]
    description:
      - defines whether the ACL should be present or not.  The C(query) state gets the current acl without changing it, for use in 'register' operations.

  follow:
    required: false
    default: yes
    choices: [ 'yes', 'no' ]
    description:
      - whether to follow symlinks on the path if a symlink is encountered.

  default:
    version_added: "1.5"
    required: false
    default: no
    choices: [ 'yes', 'no' ]
    description:
      - if the target is a directory, setting this to yes will make it the default acl for entities created inside the directory. It causes an error if name is a file.

  entity:
    version_added: "1.5"
    required: false
    description:
      - actual user or group that the ACL applies to when matching entity types user or group are selected.

  etype:
    version_added: "1.5"
    required: false
    default: null
    choices: [ 'user', 'group', 'mask', 'other' ]
    description:
      - the entity type of the ACL to apply, see setfacl documentation for more info.


  permissions:
    version_added: "1.5"
    required: false
    default: null
    description:
      - Permissions to apply/remove can be any combination of r, w and  x (read, write and execute respectively)

  entry:
    required: false
    default: null
    description:
      - DEPRECATED. The acl to set or remove.  This must always be quoted in the form of '<etype>:<qualifier>:<perms>'.  The qualifier may be empty for some types, but the type and perms are always requried. '-' can be used as placeholder when you do not care about permissions. This is now superseded by entity, type and permissions fields.

  recursive:
    version_added: "2.0"
    required: false
    default: no
    choices: [ 'yes', 'no' ]
    description:
      - Recursively sets the specified ACL (added in Ansible 2.0). Incompatible with C(state=query).
author:
    - "Brian Coca (@bcoca)"
    - "Jérémie Astori (@astorije)"
notes:
    - The "acl" module requires that acls are enabled on the target filesystem and that the setfacl and getfacl binaries are installed.
    - As of Ansible 2.0, this module only supports Linux distributions.
'''

EXAMPLES = '''
# Grant user Joe read access to a file
- acl: name=/etc/foo.conf entity=joe etype=user permissions="r" state=present

# Removes the acl for Joe on a specific file
- acl: name=/etc/foo.conf entity=joe etype=user state=absent

# Sets default acl for joe on foo.d
- acl: name=/etc/foo.d entity=joe etype=user permissions=rw default=yes state=present

# Same as previous but using entry shorthand
- acl: name=/etc/foo.d entry="default:user:joe:rw-" state=present

# Obtain the acl for a specific file
- acl: name=/etc/foo.conf
  register: acl_info
'''

RETURN = '''
acl:
    description: Current acl on provided path (after changes, if any)
    returned: success
    type: list
    sample: [ "user::rwx", "group::rwx", "other::rwx" ]
'''


def split_entry(entry):
    ''' splits entry and ensures normalized return'''

    a = entry.split(':')

    d = None
    if entry.lower().startswith("d"):
        d = True
        a.pop(0)

    if len(a) == 2:
        a.append(None)

    t, e, p = a
    t = t.lower()

    if t.startswith("u"):
        t = "user"
    elif t.startswith("g"):
        t = "group"
    elif t.startswith("m"):
        t = "mask"
    elif t.startswith("o"):
        t = "other"
    else:
        t = None

    return [d, t, e, p]


def build_entry(etype, entity, permissions=None):
    '''Builds and returns an entry string. Does not include the permissions bit if they are not provided.'''
    if permissions:
        return etype + ':' + entity + ':' + permissions
    else:
        return etype + ':' + entity


def build_command(module, mode, path, follow, default, recursive, entry=''):
    '''Builds and returns a getfacl/setfacl command.'''
    if mode == 'set':
        cmd = [module.get_bin_path('setfacl', True)]
        cmd.append('-m "%s"' % entry)
    elif mode == 'rm':
        cmd = [module.get_bin_path('setfacl', True)]
        cmd.append('-x "%s"' % entry)
    else:  # mode == 'get'
        cmd = [module.get_bin_path('getfacl', True)]
        # prevents absolute path warnings and removes headers
        cmd.append('--omit-header')
        cmd.append('--absolute-names')

    if recursive:
        cmd.append('--recursive')

    if not follow:
        cmd.append('--physical')

    if default:
        if(mode == 'rm'):
            cmd.insert(1, '-k')
        else:  # mode == 'set' or mode == 'get'
            cmd.insert(1, '-d')

    cmd.append(path)
    return cmd


def acl_changed(module, cmd):
    '''Returns true if the provided command affects the existing ACLs, false otherwise.'''
    cmd = cmd[:]  # lists are mutables so cmd would be overriden without this
    cmd.insert(1, '--test')
    lines = run_acl(module, cmd)

    for line in lines:
        if not line.endswith('*,*'):
            return True
    return False


def run_acl(module, cmd, check_rc=True):

    try:
        (rc, out, err) = module.run_command(' '.join(cmd), check_rc=check_rc)
    except Exception, e:
        module.fail_json(msg=e.strerror)

    lines = out.splitlines()
    if lines and not lines[-1].split():
        # trim last line only when it is empty
        return lines[:-1]
    else:
        return lines


def main():
    if get_platform().lower() != 'linux':
        module.fail_json(msg="The acl module is only available for Linux distributions.")

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, aliases=['path'], type='str'),
            entry=dict(required=False, type='str'),
            entity=dict(required=False, type='str', default=''),
            etype=dict(
                required=False,
                choices=['other', 'user', 'group', 'mask'],
                type='str'
            ),
            permissions=dict(required=False, type='str'),
            state=dict(
                required=False,
                default='query',
                choices=['query', 'present', 'absent'],
                type='str'
            ),
            follow=dict(required=False, type='bool', default=True),
            default=dict(required=False, type='bool', default=False),
            recursive=dict(required=False, type='bool', default=False),
        ),
        supports_check_mode=True,
    )

    path = os.path.expanduser(module.params.get('name'))
    entry = module.params.get('entry')
    entity = module.params.get('entity')
    etype = module.params.get('etype')
    permissions = module.params.get('permissions')
    state = module.params.get('state')
    follow = module.params.get('follow')
    default = module.params.get('default')
    recursive = module.params.get('recursive')

    if not os.path.exists(path):
        module.fail_json(msg="Path not found or not accessible.")

    if state == 'query' and recursive:
        module.fail_json(msg="'recursive' MUST NOT be set when 'state=query'.")

    if not entry:
        if state == 'absent' and permissions:
            module.fail_json(msg="'permissions' MUST NOT be set when 'state=absent'.")

        if state == 'absent' and not entity:
            module.fail_json(msg="'entity' MUST be set when 'state=absent'.")

        if state in ['present', 'absent'] and not etype:
            module.fail_json(msg="'etype' MUST be set when 'state=%s'." % state)

    if entry:
        if etype or entity or permissions:
            module.fail_json(msg="'entry' MUST NOT be set when 'entity', 'etype' or 'permissions' are set.")

        if state == 'present' and not entry.count(":") in [2, 3]:
            module.fail_json(msg="'entry' MUST have 3 or 4 sections divided by ':' when 'state=present'.")

        if state == 'absent' and not entry.count(":") in [1, 2]:
            module.fail_json(msg="'entry' MUST have 2 or 3 sections divided by ':' when 'state=absent'.")

        if state == 'query':
            module.fail_json(msg="'entry' MUST NOT be set when 'state=query'.")

        default_flag, etype, entity, permissions = split_entry(entry)
        if default_flag != None:
            default = default_flag

    changed = False
    msg = ""

    if state == 'present':
        entry = build_entry(etype, entity, permissions)
        command = build_command(
            module, 'set', path, follow,
            default, recursive, entry
        )
        changed = acl_changed(module, command)

        if changed and not module.check_mode:
            run_acl(module, command)
        msg = "%s is present" % entry

    elif state == 'absent':
        entry = build_entry(etype, entity)
        command = build_command(
            module, 'rm', path, follow,
            default, recursive, entry
        )
        changed = acl_changed(module, command)

        if changed and not module.check_mode:
            run_acl(module, command, False)
        msg = "%s is absent" % entry

    elif state == 'query':
        msg = "current acl"

    acl = run_acl(
        module,
        build_command(module, 'get', path, follow, default, recursive)
    )

    module.exit_json(changed=changed, msg=msg, acl=acl)

# import module snippets
from ansible.module_utils.basic import *

main()
