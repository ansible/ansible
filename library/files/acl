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
    default: None
    description:
      - The full path of the file or object.
    aliases: ['path']
  entry:
    required: false
    default: None
    description:
      - The acl to set or remove.  This must always be quoted in the form of '<type>:<qualifier>:<perms>'.  The qualifier may be empty for some types, but the type and perms are always requried. '-' can be used as placeholder when you do not care about permissions.

  state:
    required: false
    default: query
    choices: [ 'query', 'present', 'absent' ]
    description:
      - defines whether the ACL should be present or not.  The C(query) state gets the current acl C(present) without changing it, for use in 'register' operations.
  follow:
    required: false
    default: yes
    choices: [ 'yes', 'no' ]
    description:
      - whether to follow symlinks on the path if a symlink is encountered.
author: Brian Coca
notes:
    - The "acl" module requires that acls are enabled on the target filesystem and that the setfacl and getfacl binaries are installed.
'''

EXAMPLES = '''
# Grant user Joe read access to a file
- acl: name=/etc/foo.conf entry="user:joe:r" state=present

# Removes the acl for Joe on a specific file
- acl: name=/etc/foo.conf entry="user:joe:-" state=absent

# Obtain the acl for a specific file
- acl: name=/etc/foo.conf
  register: acl_info
'''

def get_acl(module,path,entry,follow):

    cmd = [ module.get_bin_path('getfacl', True) ]
    if not follow:
        cmd.append('-h')
    # prevents absolute path warnings and removes headers
    cmd.append('--omit-header')
    cmd.append('--absolute-names')
    cmd.append(path)

    return _run_acl(module,cmd)

def set_acl(module,path,entry,follow):

    cmd = [ module.get_bin_path('setfacl', True) ]
    if not follow:
        cmd.append('-h')
    cmd.append('-m "%s"' % entry)
    cmd.append(path)

    return _run_acl(module,cmd)

def rm_acl(module,path,entry,follow):

    cmd = [ module.get_bin_path('setfacl', True) ]
    if not follow:
        cmd.append('-h')
    entry = entry[0:entry.rfind(':')]
    cmd.append('-x "%s"' % entry)
    cmd.append(path)

    return _run_acl(module,cmd,False)

def _run_acl(module,cmd,check_rc=True):

    try:
        (rc, out, err) = module.run_command(' '.join(cmd), check_rc=check_rc)
    except Exception, e:
        module.fail_json(msg=e.strerror)

    return out.splitlines()

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True,aliases=['path']),
            entry = dict(required=False, default=None),
            state = dict(required=False, default='query', choices=[ 'query', 'present', 'absent' ], type='str'),
            follow = dict(required=False, type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    path = module.params.get('name')
    entry = module.params.get('entry')
    state = module.params.get('state')
    follow = module.params.get('follow')

    if not os.path.exists(path):
        module.fail_json(msg="path not found or not accessible!")

    if entry is None:
        if state in ['present','absent']:
            module.fail_json(msg="%s needs entry to be set" % state)
    else:
        if entry.count(":") != 2:
            module.fail_json(msg="Invalid entry: '%s', it requires 3 sections divided by ':'" % entry)

    changed=False
    changes=0
    msg = ""
    currentacl = get_acl(module,path,entry,follow)


    if (state == 'present'):
        newe = entry.split(':')
        matched = False
        for oldentry in currentacl:
            diff = False
            olde = oldentry.split(':')
            if olde[0] == newe[0]:
                if newe[0] in ['user', 'group']:
                    if olde[1] == newe[1]:
                        matched = True
                        if not olde[2] == newe[2]:
                            diff = True
                else:
                    matched = True
                    if not olde[2] == newe[2]:
                        diff = True
            if diff:
                changes=changes+1
                if not module.check_mode:
                    set_acl(module,path,entry,follow)
            if matched:
                break
        if not matched:
            changes=changes+1
            if not module.check_mode:
                set_acl(module,path,entry,follow)
        msg="%s is present" % (entry)
    elif state == 'absent':
        rme = entry.split(':')
        for oldentry in currentacl:
            olde = oldentry.split(':')
            if olde[0] == rme[0]:
                if rme[0] in ['user', 'group']:
                    if olde[1] == rme[1]:
                        changes=changes+1
                        if not module.check_mode:
                            rm_acl(module,path,entry,follow)
                        break
                else:
                    changes=changes+1
                    if not module.check_mode:
                        rm_acl(module,path,entry,follow)
                    break
        msg="%s is absent" % (entry)
    else:
        msg="current acl"

    if changes > 0:
        changed=True
        currentacl = get_acl(module,path,entry,follow)

    msg="%s. %d entries changed" % (msg,changes)
    module.exit_json(changed=changed, msg=msg, acl=currentacl)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
