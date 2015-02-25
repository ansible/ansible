#!/usr/bin/python
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

author: Brian Coca
notes:
    - The "acl" module requires that acls are enabled on the target filesystem and that the setfacl and getfacl binaries are installed.
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

def normalize_permissions(p):
    perms = ['-','-','-']
    for char in p:
        if char == 'r':
            perms[0] = 'r'
        if char == 'w':
            perms[1] = 'w'
        if char == 'x':
            perms[2] = 'x'
        if char == 'X':
            if perms[2] != 'x':  # 'x' is more permissive
              perms[2] = 'X'
    return ''.join(perms)

def split_entry(entry):
    ''' splits entry and ensures normalized return'''

    a = entry.split(':')
    a.reverse()
    if len(a) == 3:
        a.append(False)
    try:
        p,e,t,d = a
    except ValueError, e:
        print "wtf?? %s => %s" % (entry,a)
        raise e

    if d:
        d = True

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

    p = normalize_permissions(p)

    return [d,t,e,p]

def get_acls(module,path,follow):

    cmd = [ module.get_bin_path('getfacl', True) ]
    if not follow:
        cmd.append('-h')
    # prevents absolute path warnings and removes headers
    cmd.append('--omit-header')
    cmd.append('--absolute-names')
    cmd.append(path)

    return _run_acl(module,cmd)

def set_acl(module,path,entry,follow,default):

    cmd = [ module.get_bin_path('setfacl', True) ]
    if not follow:
        cmd.append('-h')
    if default:
        cmd.append('-d')
    cmd.append('-m "%s"' % entry)
    cmd.append(path)

    return _run_acl(module,cmd)

def rm_acl(module,path,entry,follow,default):

    cmd = [ module.get_bin_path('setfacl', True) ]
    if not follow:
        cmd.append('-h')
    if default:
        cmd.append('-k')
    entry = entry[0:entry.rfind(':')]
    cmd.append('-x "%s"' % entry)
    cmd.append(path)

    return _run_acl(module,cmd,False)

def _run_acl(module,cmd,check_rc=True):

    try:
        (rc, out, err) = module.run_command(' '.join(cmd), check_rc=check_rc)
    except Exception, e:
        module.fail_json(msg=e.strerror)

    # trim last line as it is always empty
    ret = out.splitlines()
    return ret[0:len(ret)-1]

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True,aliases=['path'], type='str'),
            entry = dict(required=False, etype='str'),
            entity = dict(required=False, type='str', default=''),
            etype = dict(required=False, choices=['other', 'user', 'group', 'mask'], type='str'),
            permissions = dict(required=False, type='str'),
            state = dict(required=False, default='query', choices=[ 'query', 'present', 'absent' ], type='str'),
            follow = dict(required=False, type='bool', default=True),
            default= dict(required=False, type='bool', default=False),
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

    if permissions:
        permissions = normalize_permissions(permissions)

    if not os.path.exists(path):
        module.fail_json(msg="path not found or not accessible!")

    if state in ['present','absent']:
        if  not entry and not etype:
            module.fail_json(msg="%s requires either etype and permissions or just entry be set" % state)

    if entry:
        if etype or entity or permissions:
            module.fail_json(msg="entry and another incompatible field (entity, etype or permissions) are also set")
        if entry.count(":") not in [2,3]:
            module.fail_json(msg="Invalid entry: '%s', it requires 3 or 4 sections divided by ':'" % entry)

        default, etype, entity, permissions = split_entry(entry)

    changed=False
    msg = ""
    currentacls = get_acls(module,path,follow)

    if (state == 'present'):
        matched = False
        for oldentry in currentacls:
            if oldentry.count(":") == 0:
                continue
            old_default, old_type, old_entity, old_permissions = split_entry(oldentry)
            if old_default == default:
                if old_type == etype:
                    if etype in ['user', 'group']:
                        if old_entity == entity:
                            matched = True
                            if not old_permissions == permissions:
                                changed = True
                            break
                    else:
                        matched = True
                        if not old_permissions == permissions:
                            changed = True
                        break
        if not matched:
            changed=True

        if changed and not module.check_mode:
            set_acl(module,path,':'.join([etype, str(entity), permissions]),follow,default)
        msg="%s is present" % ':'.join([etype, str(entity), permissions])

    elif state == 'absent':
        for oldentry in currentacls:
            if oldentry.count(":") == 0:
                continue
            old_default, old_type, old_entity, old_permissions = split_entry(oldentry)
            if old_default == default:
                if old_type == etype:
                    if etype in ['user', 'group']:
                        if old_entity == entity:
                            changed=True
                            break
                    else:
                        changed=True
                        break
        if changed and not module.check_mode:
            rm_acl(module,path,':'.join([etype, entity, '---']),follow,default)
        msg="%s is absent" % ':'.join([etype, entity, '---'])
    else:
        msg="current acl"

    if changed:
        currentacls = get_acls(module,path,follow)

    module.exit_json(changed=changed, msg=msg, acl=currentacls)

# import module snippets
from ansible.module_utils.basic import *

main()
