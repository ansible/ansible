#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Victor Hahn Castell <info@victor-hahn.de>
# Copyright (c) 2018 Nexinto GmbH and contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This module is derived from the acl module which deals with POSIX ACLs and
# tries to provide a compatible interface as much as possible.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: acl_nfs4
version_added: "2.6"
short_description: Sets and retrieves ACL permissions on NFSv4 volumes
description:
    - Sets and retrieves file ACL information.
options:
  path:
    description:
      - The full path of the file or object.
    aliases: [ name ]
    required: true

  state:
    description:
      - defines whether the ACL should be present or not.  The C(query) state gets the current acl without changing it, for use in 'register' operations.
    choices: [ absent, present, query ]
    default: query

  follow:
    description:
      - whether to follow symlinks on the path if a symlink is encountered.
    type: bool
    default: 'yes'

  default:
    description:
      - if the target is a directory, setting this to yes will make it the default acl for entities created inside the directory. Has no effect on files.
    type: bool
    default: 'no'

  entity:
    description:
      - actual user or group that the ACL applies to when matching entity types user or group are selected.

  etype:
    description:
      - is entity a group or a user?
    choices: [ group, user ]
    default: 'user'

  permissions:
    description:
      - Permissions to apply/remove. For most common use cases, use any combination of R (read), W (write) and X (execute) (caps!). Note the caps! See the nfs4_acl manpage for additional options. You must specify this event if removing and ACL entry.

  recursive:
    description:
      - Recursively sets the specified ACL (added in Ansible 2.0). Incompatible with C(state=query).
    type: bool
    default: 'no'

  ace_type:
    description:
      - Is this ACL entry granting (A, default) or denying (D) permissions? See nfs4_acl manpage for details and less often used options.
    type: str
    choices: [ A, D, U, L ]
    default: 'A'

#  TODO!! inheritance:
#    description:
#      - For directories: whether this ACL should apply to newly created files and directories, too.

  transmission_format:
    description:
      - Sometimes NFS servers require you to talk about entities in a specific format, e.g represent users as IDs, names or qualified names (name@domain). We can convert those formats for you.
      - Only supported for user entities for now
    type: str
    choices: [ name, namedomain, id ]
author:
    - Victor Hahn Castell
notes:
    - The "acl_nfs4" module requires the nfs4_getfacl, nfs4_setfacl, id and nfsidmap binaries.
    - This module only supports Linux distributions.
'''

EXAMPLES = '''
- name: Grant user Joe read access to a file
  acl_nfs4:
    path: /etc/foo.conf
    entity: joe
    etype: user
    permissions: R
    state: present

- name: Removes the acl for Joe on a specific file
  acl_nfs4:
    path: /etc/foo.conf
    entity: joe
    etype: user
    state: absent

- name: Sets default acl for joe on foo.d
  acl_nfs4:
    path: /etc/foo.d
    entity: joe
    etype: user
    permissions: RW
    default: yes
    state: present

- name: Same as previous but using entry shorthand
  acl_nfs4:
    path: /etc/foo.d
    entry: "default:user:joe:rw-"
    state: present

- name: Obtain the acl for a specific file
  acl_nfs4:
    path: /etc/foo.conf
  register: acl_info
'''

RETURN = '''
acl:
    description: Current acl on provided path (after changes, if any)
    returned: success
    type: list
    sample: [ "A::OWNER@:rwaDxtTnNcCy", "A:g:GROUP@:rxtncy" ]
'''

import os

from ansible.module_utils.basic import AnsibleModule, get_platform
from ansible.module_utils._text import to_native


def build_entry(ace_type, etype, entity, permissions, default, path_isdir):
    '''Builds and returns an entry string.'''
    flags = set()
    if path_isdir and default:
        flags.add('d')
        flags.add('f')
    flagstr = ''.join(flags)

    if etype == 'group':
        flags.add('g')

    return ':'.join([ace_type, flagstr, entity, permissions])


def build_command(module, mode, path, follow, recursive, entry=None):
    '''Builds and returns a getfacl/setfacl command.'''

    if mode == 'set':
        cmd = [module.get_bin_path('nfs4_setfacl', True)]
        cmd.append('-a "%s"' % entry)
    elif mode == 'rm':
        cmd = [module.get_bin_path('nfs4_setfacl', True)]
        cmd.append('-x "%s"' % entry)
    else:  # mode == 'get'
        cmd = [module.get_bin_path('nfs4_getfacl', True)]

    if recursive:
        cmd.append('--recursive')

    if not follow:
        cmd.append('--physical')

    cmd.append(path)
    return cmd


def run_acl(module, cmd, check_rc=True):
    try:
        (rc, out, err) = module.run_command(' '.join(cmd), check_rc=check_rc)
    except Exception as e:
        module.fail_json(msg=to_native(e))

    lines = []
    for l in out.splitlines():
        if not l.startswith('#'):
            lines.append(l.strip())

    if lines and not lines[-1].split():
        # trim last line only when it is empty
        return lines[:-1]

    return lines


def convert_entity(module, transmission_format, entity, etype):
    ret = ""

    if etype == 'group':
        module.fail_json(msg="transmission_format conversion is currently only supported for users")

    if transmission_format == 'id':
        flag = "-u"
    else:
        flag = "-un"

    cmd = module.get_bin_path('id', True)
    (rc, out, err) = module.run_command(' '.join([cmd, flag, entity]))
    converted = out.strip(' \n')
    if converted:
        ret += converted
    else:
        module.fail_json(msg="Cannot convert " + entity + ". Check if it's properly set up.")

    if transmission_format == 'namedomain':
        cmd = [module.get_bin_path('nfsidmap', True)]
        flag = "-d"
        (rc, out, err) = module.run_command(' '.join([cmd, flag]))
        ret += "@" + out.strip(' \n')
    return ret

def acl_contains(lines, entry):
    for line in lines:
        if entry_equal(line, entry):
            return True
    return False

def expand_permission_shorthand(path_isdir, perms):
    perms = perms.replace("R", "rntcy")
    perms = perms.replace("X", "xtcy")

    if path_isdir:
        perms = perms.replace("W", "watTNcCyD")
    else:
        perms = perms.replace("W", "watTNcCy")

    return perms

def entry_equal(t1, t2):
    fields = zip(t1.split(':'), t2.split(':'))

    # Each entry has four fields:
    type = fields[0]
    flags = fields[1]
    entity = fields[2]  # the NFS people normally call this one principal
    permissions = fields[3]

    if type[0] != type[1]:
        return False

    # flag order doesn't matter
    if set(flags[0]) != set(flags[1]):
        return False

    if entity[0] != entity[1]:
        return False

    # Permissions:
    # Expand RWX shorthand. Try for both the directory and regular file expansion.
    # Permission order doesn't matter.
    p0_file = expand_permission_shorthand(False, permissions[0])
    p0_dir = expand_permission_shorthand(True, permissions[0])
    p1_file = expand_permission_shorthand(False, permissions[1])
    p1_dir = expand_permission_shorthand(True, permissions[1])

    if set(p0_file) != set(p1_file) and set(p0_dir) != set(p1_dir):
        return False

    return True  # no diversions found


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, aliases=['name'], type='path'),
            entry=dict(required=False, type='str'),
            entity=dict(required=False, type='str', default=''),
            etype=dict(
                required=False,
                choices=['user', 'group'],
                type='str',
                default='user'
            ),
            permissions=dict(required=True, type='str'),
            state=dict(
                required=False,
                default='query',
                choices=['query', 'present', 'absent'],
                type='str'
            ),
            follow=dict(required=False, type='bool', default=True),
            default=dict(required=False, type='bool', default=False),
            recursive=dict(required=False, type='bool', default=False),
            ace_type=dict(
                required=False,
                choices=['A', 'D', 'U', 'L'],
                default='A',
                type='str'),
            transmission_format=dict(
                required=False,
                type='str',
                default=None,
                choices=['name', 'namedomain', 'id'])
        ),
        supports_check_mode=True,
    )

    if get_platform().lower() not in ['linux', 'freebsd']:
        module.fail_json(msg="The acl module is not available on this system.")

    path = module.params.get('path')
    entry = module.params.get('entry')
    entity = module.params.get('entity')
    etype = module.params.get('etype')
    permissions = module.params.get('permissions')
    state = module.params.get('state')
    follow = module.params.get('follow')
    default = module.params.get('default')
    recursive = module.params.get('recursive')
    ace_type = module.params.get('ace_type')
    transmission_format = module.params.get('transmission_format')

    # Plausibility checks:

    if not os.path.exists(path):
        module.fail_json(msg="Path not found or not accessible.")
    path_isdir = os.path.isdir(path)  # is this for a directory?

    if state == 'query' and recursive:
        module.fail_json(msg="'recursive' MUST NOT be set when 'state=query'.")

    # TODO!
    # if state == 'absent' and permissions:
    #     module.fail_json(msg="'permissions' MUST NOT be set when 'state=absent'.")

    if state in ['present', 'absent'] and not entity:
        module.fail_json(msg="'entity' MUST be set when 'state=absent'.")

    if transmission_format:
        entity = convert_entity(module, transmission_format, entity, etype)

    changed = False
    msg = ""

    get_command = build_command(module, 'get', path, follow, recursive)

    if state == 'present':
        entry = build_entry(ace_type, etype, entity, permissions, default, path_isdir)
        get_lines = run_acl(module, get_command)
        changed = False

        if not acl_contains(get_lines, entry):  # don't duplicate entries
            changed = True
            if not module.check_mode:
                set_command = build_command(
                    module, 'set', path, follow, recursive, entry
                )
                run_acl(module, set_command)

        msg = "%s is present" % entry

    elif state == 'absent':
        entry = build_entry(ace_type, etype, entity, permissions, default, path_isdir)

        set_command = build_command(
            module, 'rm', path, follow, recursive, entry
        )
        changed = False

        while True:  # NFSv4 ACL entries may have duplicates
            get_lines = run_acl(module, get_command)
            if acl_contains(get_lines, entry):
                changed = True
                if not module.check_mode:  # perform change except in check mode
                    run_acl(module, set_command)
                else:                       # just report changed in check mode
                    break
            else:
                break

        msg = "%s is absent" % entry

    elif state == 'query':
        msg = "current acl"

    acl = run_acl(module, get_command)

    module.exit_json(changed=changed, msg=msg, acl=acl)


if __name__ == '__main__':
    main()
